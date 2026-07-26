"""Demand writer module. Writes out information from the demands submodule to
files"""

import os
from typing import Dict, List, Optional, Tuple

import pandas as pd
from pyomo.core import Model, value

from ehubx.core import exceptions
from ehubx.core.common import TimeSeriesKind
from ehubx.data.ec_data import EcId
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId
from ehubx.data.time_series import TimeSeries
from ehubx.data.unit import TimeUnit
from ehubx.data.value import Value
from ehubx.model import demand_model, ec_model
from ehubx.parser.csv_parser import HeaderId
from ehubx.parser.demand_parser import YAMLKEY_DEMANDPROFILES
from ehubx.writer import load_shedding_writer, load_shifting_writer
from ehubx.writer.common_writer import (
    DfStBuilder,
    DfStColumn,
    FileGranularity,
    add_to_df_ts_cl,
    create_dir,
    init_df_ts_cl,
    init_df_ts_hor,
)


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "writ/demand"
"""String identifying the demand writer module for logging purposes"""

FILENAME_TIMESERIES_DEMANDS: str = "demands.csv"
"""Filename for conversion tech time series"""

FILENAME_LOADS: str = "loads"
"""Filename for all load-related data (demands, load shedding, load
shifting)"""

SOURCE: str = "demands"
"""Display name for the demands module in result files"""

ENTRY_DEMANDPROFILE: str = "Demand-profile"
"""Entry name for demand parameter 'demand_profile' in result files"""

ENTRY_DEMANDSUM: str = "Demand-sum"
"""Entry name for demand parameter 'demand_sum' in result files"""

ENTRY_DEMANDSUPPLY: str = f"Demand supply ({demand_model.VAR_DEMANDSUPPLY})"
"""Entry name for demand supply variable in result files"""


def format_all(
    energy_system: EnergySystem,
    model: Model,
    dir_path: str,
    file_granularity: FileGranularity = FileGranularity.DEFAULT,
) -> List[Tuple[pd.DataFrame, str]]:
    # Initialize dataframes
    df_st_builder = DfStBuilder()
    df_ts_hor = init_df_ts_hor(energy_system.times)
    df_ts_cl: Optional[pd.DataFrame] = None
    if energy_system.times.is_clustered:
        df_ts_cl = init_df_ts_cl(energy_system.times)

    # Tuple-specific values
    for s, h, e in energy_system.demands.tuples:
        _format_tuple(energy_system, model, s, h, e, df_ts_hor, df_ts_cl)
    for s, h, e in energy_system.demands.profile_tuples:
        _format_profile_tuple(
            energy_system, s, h, e, df_st_builder, df_ts_hor, df_ts_cl
        )
    for s, h, e in energy_system.demands.sum_tuples:
        _format_sum_tuple(energy_system, s, h, e, df_st_builder)

    # Child modules
    load_shedding_writer.format_all(
        energy_system, model, df_st_builder, df_ts_hor, df_ts_cl
    )
    load_shifting_writer.format_all(
        energy_system, model, df_st_builder, df_ts_hor, df_ts_cl
    )

    # Remove unused columns
    cols_to_drop_st = {
        DfStColumn.TECH,
        DfStColumn.NET_LINK,
        DfStColumn.NET_LINK_DIR,
        DfStColumn.NET_TECH,
    }
    cols_to_drop_ts = [
        DfStColumn.TECH.value,
        DfStColumn.NET_LINK.value,
        DfStColumn.NET_TECH.value,
    ]
    df_ts_hor.columns = df_ts_hor.columns.droplevel(cols_to_drop_ts)
    if df_ts_cl is not None:
        df_ts_cl.columns = df_ts_cl.columns.droplevel(cols_to_drop_ts)

    # Create all-in-one dataframes
    df_st = df_st_builder.build(drop_columns=cols_to_drop_st)

    # Format for file granularity
    dfs = _format_file_granularity(
        df_st, df_ts_hor, df_ts_cl, dir_path, file_granularity
    )

    # Return
    return dfs


def _format_tuple(
    energy_system: EnergySystem,
    model: Model,
    s: StageId,
    h: HubId,
    e: EcId,
    df_ts_hor: pd.DataFrame,
    df_ts_cl: Optional[pd.DataFrame],
) -> None:
    # Demand supply
    var = getattr(model, demand_model.VAR_DEMANDSUPPLY)
    supply = TimeSeries()
    supply_unit = (
        ec_model.get_ec_model_unit(
            energy_system.ecs.get_unit(e),
            energy_system.mass_unit,
            energy_system.power_unit,
        )
        / TimeUnit.H
    )
    for t in energy_system.times.ids:
        supply_fl = value(var[s.key, h.key, e.key, t.key_as_int], exception=False)
        if supply_fl is not None:
            supply.set_value(t, Value(supply_fl, supply_unit))
    add_to_df_ts_cl(
        df_ts_hor,
        df_ts_cl,
        energy_system.times,
        ENTRY_DEMANDSUPPLY,
        supply,
        unit=supply_unit,
        stage=s.key,
        hub=h.key,
        ec=e.key,
        source=SOURCE,
        in_res="result",
    )


def _format_profile_tuple(
    energy_system: EnergySystem,
    s: StageId,
    h: HubId,
    e: EcId,
    df_st_builder: DfStBuilder,
    df_ts_hor: pd.DataFrame,
    df_ts_cl: Optional[pd.DataFrame],
) -> None:
    # demand_profile
    demand_profile = energy_system.demands.get_demand_profile(s, h, e)
    demand_unit = (
        ec_model.get_ec_model_unit(
            energy_system.ecs.get_unit(e),
            energy_system.mass_unit,
            energy_system.power_unit,
        )
        / TimeUnit.H
    )
    if demand_profile.has_values:
        add_to_df_ts_cl(
            df_ts_hor,
            df_ts_cl,
            energy_system.times,
            ENTRY_DEMANDPROFILE,
            demand_profile,
            demand_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )
    if not demand_profile.has_values:
        demand_def = demand_profile.def_value
        assert demand_def is not None
        df_st_builder.add_row(
            ENTRY_DEMANDPROFILE,
            demand_def,
            unit=demand_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )


def _format_sum_tuple(
    energy_system: EnergySystem,
    s: StageId,
    h: HubId,
    e: EcId,
    df_st_builder: DfStBuilder,
) -> None:
    # demand
    demand_sum = energy_system.demands.get_demand_sum(s, h, e)
    demand_sum_unit = ec_model.get_ec_model_unit(
        energy_system.ecs.get_unit(e), energy_system.mass_unit, energy_system.power_unit
    )
    df_st_builder.add_row(
        ENTRY_DEMANDSUM,
        demand_sum,
        unit=demand_sum_unit,
        stage=s.key,
        hub=h.key,
        ec=e.key,
        source=SOURCE,
        in_res="input",
    )


def _format_file_granularity(
    df_st: pd.DataFrame,
    df_ts_hor: pd.DataFrame,
    df_ts_cl: Optional[pd.DataFrame],
    dir_path,
    file_granularity: FileGranularity,
) -> List[Tuple[pd.DataFrame, str]]:
    # Prepare dataframe list
    dfs: List[Tuple[pd.DataFrame, str]] = []

    # Format for minimal file granularity (One csv file "loads" for static,
    # horizon time and clustered time df each)
    if file_granularity == FileGranularity.MIN:
        # Filenames
        filename_st = os.path.join(dir_path, f"{FILENAME_LOADS}.csv")
        filename_ts_hor = os.path.join(dir_path, f"{FILENAME_LOADS}-TS.csv")
        filename_ts_cl = os.path.join(dir_path, f"{FILENAME_LOADS}-TSCL.csv")
        # Append dfs
        dfs.append((df_st, filename_st))
        dfs.append((df_ts_hor, filename_ts_hor))
        if df_ts_cl is not None:
            dfs.append((df_ts_cl, filename_ts_cl))

    # Format for default file granularity (split by tuples but keep demands,
    # load shedding and load shifting together)
    if file_granularity == FileGranularity.DEFAULT:
        # Static files (tuples)
        ids_st = df_st[
            [DfStColumn.STAGE.value, DfStColumn.HUB.value, DfStColumn.EC.value]
        ].drop_duplicates()
        for s, h, e in ids_st.itertuples(index=False, name=None):
            if not h:
                continue
            filename_st = f"{FILENAME_LOADS}_{s}_{h}_{e}"
            filename_st = os.path.join(dir_path, f"{filename_st}.csv")
            df_st_cur = df_st[
                (df_st[DfStColumn.STAGE.value] == s)
                & (df_st[DfStColumn.HUB.value] == h)
                & (df_st[DfStColumn.EC.value] == e)
            ]
            if len(df_st_cur) > 0:
                dfs.append((df_st_cur, filename_st))
        # Static files (nontuple)
        df_st_0 = df_st[df_st[DfStColumn.HUB.value] == ""]
        filename_st = os.path.join(dir_path, f"{FILENAME_LOADS}.csv")
        dfs.append((df_st_0, filename_st))

        # Horizon time files
        ids_ts_hor = df_ts_hor.columns.to_frame(index=False)[
            [DfStColumn.STAGE.value, DfStColumn.HUB.value, DfStColumn.EC.value]
        ]
        for s, h, e in ids_ts_hor.itertuples(index=False, name=None):
            filename_ts_hor = f"{FILENAME_LOADS}-TS"
            if s:
                filename_ts_hor = f"{FILENAME_LOADS}_{s}_{h}_{e}-TS"
            filename_ts_hor = os.path.join(dir_path, f"{filename_ts_hor}.csv")
            df_ts_hor_cur = df_ts_hor.xs(
                (s, h, e),
                axis=1,
                level=(
                    DfStColumn.STAGE.value,
                    DfStColumn.HUB.value,
                    DfStColumn.EC.value,
                ),
                drop_level=False,
            )
            if len(df_ts_hor_cur) > 0:
                dfs.append((df_ts_hor_cur, filename_ts_hor))

        # Clustered time files
        if df_ts_cl is not None:
            ids_ts_cl = df_ts_cl.columns.to_frame(index=False)[
                [DfStColumn.STAGE.value, DfStColumn.HUB.value, DfStColumn.EC.value]
            ]
            for s, h, e in ids_ts_cl.itertuples(index=False, name=None):
                filename_ts_cl = f"{FILENAME_LOADS}-TSCL"
                if s:
                    filename_ts_cl = f"{FILENAME_LOADS}_{s}_{h}_{e}-TSCL"
                filename_ts_cl = os.path.join(dir_path, f"{filename_ts_cl}.csv")
                df_ts_cl_cur = df_ts_cl.xs(
                    (s, h, e),
                    axis=1,
                    level=(
                        DfStColumn.STAGE.value,
                        DfStColumn.HUB.value,
                        DfStColumn.EC.value,
                    ),
                    drop_level=False,
                )
                if len(df_ts_cl_cur) > 0:
                    dfs.append((df_ts_cl_cur, filename_ts_cl))

    # Format for maximal file granularity (split by tuples and make separate
    # csvs for demands, load shedding and load shifting)
    if file_granularity == FileGranularity.MAX:
        # Static files (tuples)
        ids_st = df_st[
            [DfStColumn.STAGE, DfStColumn.HUB, DfStColumn.EC, DfStColumn.SOURCE]
        ].drop_duplicates()
        for s, h, e, source in ids_st.itertuples(index=False, name=None):
            if not h:
                continue
            filename_st = f"{source}_{s}_{h}_{e}"
            filename_st = os.path.join(dir_path, f"{filename_st}.csv")
            df_st_cur = df_st[
                (df_st[DfStColumn.STAGE.value] == s)
                & (df_st[DfStColumn.HUB.value] == h)
                & (df_st[DfStColumn.EC.value] == e)
                & (df_st[DfStColumn.SOURCE.value] == source)
            ]
            if len(df_st_cur) > 0:
                dfs.append((df_st_cur, filename_st))
        # Static files (nontuple)
        df_st_0 = df_st[df_st[DfStColumn.HUB.value] == ""]
        for source in df_st_0[DfStColumn.SOURCE.value].unique():
            filename_st = source
            filename_st = os.path.join(dir_path, f"{filename_st}.csv")
            df_st_cur = df_st_0[df_st_0[DfStColumn.SOURCE.value] == source]
            if len(df_st_cur) > 0:
                dfs.append((df_st_cur, filename_st))

        # Horizon time files
        ids_ts_hor = df_ts_hor.columns.to_frame(index=False)[
            [
                DfStColumn.STAGE.value,
                DfStColumn.HUB.value,
                DfStColumn.EC.value,
                DfStColumn.SOURCE.value,
            ]
        ]
        for s, h, e, source in ids_ts_hor.itertuples(index=False, name=None):
            filename_ts_hor = f"{source}TS"
            if s:
                filename_ts_hor = f"{source}_{s}_{h}_{e}-TS"
            filename_ts_hor = os.path.join(dir_path, f"{filename_ts_hor}.csv")
            df_ts_hor_cur = df_ts_hor.xs(
                (s, h, e, source),
                axis=1,
                level=(
                    DfStColumn.STAGE.value,
                    DfStColumn.HUB.value,
                    DfStColumn.EC.value,
                    DfStColumn.SOURCE.value,
                ),
                drop_level=False,
            )
            if len(df_ts_hor_cur) > 0:
                dfs.append((df_ts_hor_cur, filename_ts_hor))

        # Clustered time files
        if df_ts_cl is not None:
            ids_ts_cl = df_ts_cl.columns.to_frame(index=False)[
                [
                    DfStColumn.STAGE.value,
                    DfStColumn.HUB.value,
                    DfStColumn.EC.value,
                    DfStColumn.SOURCE.value,
                ]
            ]
            for s, h, e, source in ids_ts_cl.itertuples(index=False, name=None):
                filename_ts_cl = f"{source}-TSCL"
                if s:
                    filename_ts_cl = f"{source}_{s}_{h}_{e}-TSCL"
                filename_ts_cl = os.path.join(dir_path, f"{filename_ts_cl}.csv")
                df_ts_cl_cur = df_ts_cl.xs(
                    (s, h, e, source),
                    axis=1,
                    level=(
                        DfStColumn.STAGE.value,
                        DfStColumn.HUB.value,
                        DfStColumn.EC.value,
                        DfStColumn.SOURCE.value,
                    ),
                    drop_level=False,
                )
                if len(df_ts_cl_cur) > 0:
                    dfs.append((df_ts_cl_cur, filename_ts_cl))

    return dfs


def write_input_time_series(energy_system: EnergySystem, dir_path: str) -> None:
    """
    Writes all time series with actual data (def_value is not enough) in a
    Demands data object to a dedicated csv file in a directory

    :param energy_system: Energy system data object
    :type energy_system: EnergySystem
    :param dir_path: Path where the csv file will be placed
    :type dir_path: str
    """
    # Create directory if it does not exist
    if not os.path.isdir(dir_path):
        if not create_dir(dir_path):
            raise exceptions.EhubXException(
                "Could not write demand time series data because "
                "the directory could not be created",
                module=LOG_MODULE_STR,
            )

    # Gather time series
    data: Dict[Tuple[str, str, str, str, str], List[float]] = {}
    for kind, stage, ids, series in energy_system.demands.time_series:
        # Skip series without values
        if not series.has_values:
            continue
        if kind == TimeSeriesKind.DEMAND:
            ec_unit = ec_model.get_ec_model_unit(
                energy_system.ecs.get_unit(EcId(ids[1])),
                energy_system.mass_unit,
                energy_system.power_unit,
            )
            unit = ec_unit / TimeUnit.H
            data[stage.key, ids[0], ids[1], YAMLKEY_DEMANDPROFILES, str(unit)] = [
                series.get_value(t).to_float(unit=unit)
                for t in energy_system.times.ids_in_order
            ]

    # Write demands file
    if data:
        df = pd.DataFrame(data)
        df.columns.names = [
            HeaderId.STAGEID.value,
            HeaderId.HUBID.value,
            HeaderId.ECID.value,
            HeaderId.PROFILEKEY.value,
            HeaderId.UNIT.value,
        ]
        df.index += 1
        df.to_csv(os.path.join(dir_path, FILENAME_TIMESERIES_DEMANDS))
