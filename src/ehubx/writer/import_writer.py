"""Import writer module. Writes out information from the imports submodule to
files"""
import os
from typing import Dict, List, Optional, Tuple
import pandas as pd
from pyomo.core import Model, value
from ehubx.core.common import TimeSeriesKind
from ehubx.core import exceptions
from ehubx.parser.csv_parser import HeaderId
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.stage_data import StageId
from ehubx.data.hub_data import HubId
from ehubx.data.ec_data import EcId
from ehubx.data.import_data import Imports
from ehubx.data.time_data import Times
from ehubx.data.time_series import TimeSeries
from ehubx.parser.import_export_parser import YAMLKEY_PRICE, YAMLKEY_MIN, \
    YAMLKEY_MAX, YAMLKEY_CO2
from ehubx.model import import_model
from ehubx.writer.common_writer import create_dir, FileGranularity, \
    init_df_st, init_df_ts_cl, init_df_ts_hor, add_to_df_st, add_to_df_ts_cl, \
    COL_STAGE, COL_HUB, COL_EC, COL_TECH, COL_NETLINK, COL_NETLINKDIR, \
    COL_NETTECH, COL_WINDPARK, COL_LOADSHIFT, COL_SOURCE
from ehubx.writer import export_writer

# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "writ/import"
"""String identifying the import writer module for logging purposes"""

FILENAME_IMPEXP: str = "import_export"
"""Filename for import and export data"""

FILENAME_TIMESERIES_IMPORTS: str = "imports.csv"
"""Filename for import time series"""

SOURCE: str = "imports"
"""Display name for the imports module in result files"""

ENTRY_PRICE: str = "Import price"
"""Entry name for import parameter 'price' in result files"""

ENTRY_CO2: str = "Import CO2"
"""Entry name for import parameter 'co2' in result files"""

ENTRY_MIN: str = "Min import"
"""Entry name for import parameter 'min' in result files"""

ENTRY_MAX: str = "Max import"
"""Entry name for import parameter 'max' in result files"""

ENTRY_SUMMIN: str = "Min summed-up import"
"""Entry name for import parameter 'sum_min' in result files"""

ENTRY_SUMMAX: str = "Max summed-up import"
"""Entry name for import parameter 'sum_max' in result files"""

ENTRY_IMP: str = f"Import ({import_model.VAR_IMP})"
"""Entry name for import variable in result files"""

ENTRY_IMPCOST: str = f"Import cost ({import_model.VAR_IMPCOST})"
"""Entry name for import cost variable in result files"""

ENTRY_IMPCOSTTOTAL: str = \
    f"Total import cost ({import_model.VAR_IMPCOSTTOTAL})"
"""Entry name for total import cost variable in result files"""

ENTRY_IMPCO2: str = f"Embodied CO2 in imports ({import_model.VAR_IMPCO2})"
"""Entry name for import CO2 variable in result files"""

ENTRY_IMPCO2TOTAL: str = \
    f"Total embodied CO2 in imports ({import_model.VAR_IMPCO2TOTAL})"
"""Entry name for total import CO2 variable in result files"""


def format_all(energy_system: EnergySystem, model: Model, dir_path: str,
               file_granularity: FileGranularity = FileGranularity.DEFAULT
               ) -> List[Tuple[pd.DataFrame, str]]:
    # Initialize dataframes
    df_st = init_df_st()
    df_ts_hor = init_df_ts_hor(energy_system.times)
    df_ts_cl: Optional[pd.DataFrame] = None
    if energy_system.times.is_clustered:
        df_ts_cl = init_df_ts_cl(energy_system.times)

    # Total import cost
    var = getattr(model, import_model.VAR_IMPCOSTTOTAL)
    imp_cost_total = value(var, exception=False)
    add_to_df_st(df_st, ENTRY_IMPCOSTTOTAL, imp_cost_total, unit="CHF",
                 source=SOURCE, in_res="result")

    # Total import CO2
    for s in energy_system.stages.ids_in_order:
        var = getattr(model, import_model.VAR_IMPCO2TOTAL)
        imp_co2_total = value(var[s.key], exception=False)
        add_to_df_st(df_st, ENTRY_IMPCO2TOTAL, imp_co2_total, unit="kg",
                     stage=s.key, source=SOURCE, in_res="result")

    # Tuple-specific values
    for (s, h, e) in energy_system.imports.tuples:
        _format_tuple(energy_system, model, s, h, e, df_st, df_ts_hor,
                      df_ts_cl)

    # Export module
    export_writer.format_all(energy_system, model, df_st, df_ts_hor, df_ts_cl)

    # Remove unused columns
    cols_to_drop_st = [COL_TECH, COL_NETLINK, COL_NETLINKDIR, COL_NETTECH,
                       COL_WINDPARK, COL_LOADSHIFT]
    cols_to_drop_ts = [COL_TECH, COL_NETLINK, COL_NETTECH, COL_LOADSHIFT]
    df_st.drop(columns=(cols_to_drop_st), inplace=True)
    df_ts_hor.columns = df_ts_hor.columns.droplevel(cols_to_drop_ts)
    if df_ts_cl is not None:
        df_ts_cl.columns = df_ts_cl.columns.droplevel(cols_to_drop_ts)

    # Format for file granularity
    dfs = _format_file_granularity(df_st, df_ts_hor, df_ts_cl, dir_path,
                                   file_granularity)

    # Return
    return dfs


def _format_tuple(energy_system: EnergySystem, model: Model, s: StageId,
                  h: HubId, e: EcId, df_st: pd.DataFrame,
                  df_ts_hor: pd.DataFrame, df_ts_cl: Optional[pd.DataFrame]
                  ) -> None:

    # price
    price = energy_system.imports.get_price(s, h, e)
    if price.has_values:
        add_to_df_ts_cl(df_ts_hor, df_ts_cl,
            energy_system.times, ENTRY_PRICE, price, unit="CHF/kW",
            stage=s.key, hub=h.key, ec=e.key, source=SOURCE, in_res="input")
    if not price.has_values:
        price_def = price.def_value
        assert price_def is not None
        add_to_df_st(df_st, ENTRY_PRICE, price_def, unit="CHF/kW", stage=s.key,
                     hub=h.key, ec=e.key, source=SOURCE, in_res="input")

    # co2
    co2 = energy_system.imports.get_co2(s, h, e)
    if co2.has_values:
        add_to_df_ts_cl(df_ts_hor, df_ts_cl,
            energy_system.times, ENTRY_CO2, co2, unit="kg/kW",
            stage=s.key, hub=h.key, ec=e.key, source=SOURCE, in_res="input")
    if not co2.has_values:
        co2_def = co2.def_value
        assert co2_def is not None
        add_to_df_st(df_st, ENTRY_CO2, co2_def, unit="kg/kW", stage=s.key,
                     hub=h.key, ec=e.key, source=SOURCE, in_res="input")

    # min
    imp_min = energy_system.imports.get_min(s, h, e)
    if imp_min.has_values:
        add_to_df_ts_cl(df_ts_hor, df_ts_cl,
            energy_system.times, ENTRY_MIN, imp_min, unit="kW",
            stage=s.key, hub=h.key, ec=e.key, source=SOURCE, in_res="input")
    if not imp_min.has_values:
        imp_min_def = imp_min.def_value
        assert imp_min_def is not None
        add_to_df_st(df_st, ENTRY_MIN, imp_min_def, unit="kW", stage=s.key,
                     hub=h.key, ec=e.key, source=SOURCE, in_res="input")

    # max
    imp_max = energy_system.imports.get_max(s, h, e)
    if imp_max.has_values:
        add_to_df_ts_cl(df_ts_hor, df_ts_cl,
            energy_system.times, ENTRY_MAX, imp_max, unit="kW",
            stage=s.key, hub=h.key, ec=e.key, source=SOURCE, in_res="input")
    if not imp_max.has_values:
        imp_max_def = imp_max.def_value
        assert imp_max_def is not None
        add_to_df_st(df_st, ENTRY_MAX, imp_max_def, unit="kW", stage=s.key,
                     hub=h.key, ec=e.key, source=SOURCE, in_res="input")

    # sum_min
    sum_min = energy_system.imports.get_sum_min(s, h, e)
    add_to_df_st(df_st, ENTRY_SUMMIN, sum_min, unit="kWh", stage=s.key,
                 hub=h.key, ec=e.key, source=SOURCE, in_res="input")

    # sum_max
    sum_max = energy_system.imports.get_sum_max(s, h, e)
    add_to_df_st(df_st, ENTRY_SUMMAX, sum_max, unit="kWh", stage=s.key,
                 hub=h.key, ec=e.key, source=SOURCE, in_res="input")

    # Imports
    var = getattr(model, import_model.VAR_IMP)
    imp = TimeSeries()
    for t in energy_system.times.ids:
        imp.set_value(t, value(var[s.key, h.key, e.key, t.key_as_int],
                               exception=False))
    add_to_df_ts_cl(df_ts_hor, df_ts_cl, energy_system.times,
        ENTRY_IMP, imp, unit="kW", stage=s.key, hub=h.key, ec=e.key,
        source=SOURCE, in_res="result")

    # Import cost
    var = getattr(model, import_model.VAR_IMPCOST)
    imp_cost = value(var[s.key, h.key, e.key], exception=False)
    add_to_df_st(df_st, ENTRY_IMPCOST, imp_cost, unit="CHF", stage=s.key,
                 hub=h.key, ec=e.key, source=SOURCE, in_res="result")

    # Import CO2
    var = getattr(model, import_model.VAR_IMPCO2)
    imp_co2 = value(var[s.key, h.key, e.key], exception=False)
    add_to_df_st(df_st, ENTRY_IMPCO2, imp_co2, unit="kg", stage=s.key,
                 hub=h.key, ec=e.key, source=SOURCE, in_res="result")


def _format_file_granularity(df_st: pd.DataFrame, df_ts_hor: pd.DataFrame,
                             df_ts_cl: Optional[pd.DataFrame],
                             dir_path, file_granularity: FileGranularity
                             ) -> List[Tuple[pd.DataFrame, str]]:
    # Initialize dataframe list
    dfs: List[Tuple[pd.DataFrame, str]] = []

    # Format for minimal file granularity (One csv file "import_export" for
    # static, horizon time and clustered time df each)
    if file_granularity == FileGranularity.MIN:
        # Filenames
        filename_st = os.path.join(dir_path, f"{FILENAME_IMPEXP}.csv")
        filename_ts_hor = os.path.join(dir_path,
                                       f"{FILENAME_IMPEXP}-TS.csv")
        filename_ts_cl = os.path.join(dir_path,
                                      f"{FILENAME_IMPEXP}-TSCL.csv")
        # Append dfs
        dfs.append((df_st, filename_st))
        dfs.append((df_ts_hor, filename_ts_hor))
        if df_ts_cl is not None:
            dfs.append((df_ts_cl, filename_ts_cl))

    # Format for default file granularity (split by tuples but keep imports
    # and exports together)
    if file_granularity == FileGranularity.DEFAULT:

        # Static files (tuples)
        ids_st = df_st[[COL_STAGE, COL_HUB, COL_EC]].drop_duplicates()
        for (s, h, e) in ids_st.itertuples(index=False, name=None):
            if not h:
                continue
            filename_st = f"{FILENAME_IMPEXP}_{s}_{h}_{e}"
            filename_st = os.path.join(dir_path, f"{filename_st}.csv")
            df_st_cur = df_st[(df_st[COL_STAGE] == s)
                              & (df_st[COL_HUB] == h)
                              & (df_st[COL_EC] == e)]
            if len(df_st_cur) > 0:
                dfs.append((df_st_cur, filename_st))
        # Static files (nontuple)
        df_st_0 = df_st[df_st[COL_HUB] == ""]
        filename_st = os.path.join(dir_path, f"{FILENAME_IMPEXP}.csv")
        dfs.append((df_st_0, filename_st))

        # Horizon time files
        ids_ts_hor = df_ts_hor.columns.to_frame(index=False)[
            [COL_STAGE, COL_HUB, COL_EC]]
        for (s, h, e) in ids_ts_hor.itertuples(index=False, name=None):
            filename_ts_hor = f"{FILENAME_IMPEXP}TS"
            if s:
                filename_ts_hor = f"{FILENAME_IMPEXP}_{s}_{h}_{e}-TS"
            filename_ts_hor = os.path.join(dir_path, f"{filename_ts_hor}.csv")
            df_ts_hor_cur = df_ts_hor.xs((s, h, e), axis=1,
                                         level=(COL_STAGE, COL_HUB, COL_EC),
                                         drop_level=False)
            if len(df_ts_hor_cur) > 0:
                dfs.append((df_ts_hor_cur, filename_ts_hor))

        # Clustered time files
        if df_ts_cl is not None:
            ids_ts_cl = df_ts_cl.columns.to_frame(index=False)[
                [COL_STAGE, COL_HUB, COL_EC]]
            for (s, h, e) in ids_ts_cl.itertuples(index=False, name=None):
                filename_ts_cl = f"{FILENAME_IMPEXP}-TSCL"
                if s:
                    filename_ts_cl = f"{FILENAME_IMPEXP}_{s}_{h}_{e}-TSCL"
                filename_ts_cl = os.path.join(dir_path,
                                              f"{filename_ts_cl}.csv")
                df_ts_cl_cur = df_ts_cl.xs((s, h, e), axis=1,
                                           level=(COL_STAGE, COL_HUB, COL_EC),
                                           drop_level=False)
                if len(df_ts_cl_cur) > 0:
                    dfs.append((df_ts_cl_cur, filename_ts_cl))

    # Format for maximal file granularity (split by tuples and make separate
    # csvs for import and export)
    if file_granularity == FileGranularity.MAX:

        # Static files (tuples)
        ids_st = df_st[[COL_STAGE, COL_HUB, COL_EC, COL_SOURCE]
                       ].drop_duplicates()
        for (s, h, e, source) in ids_st.itertuples(index=False, name=None):
            if not h:
                continue
            filename_st = f"{source}_{s}_{h}_{e}"
            filename_st = os.path.join(dir_path, f"{filename_st}.csv")
            df_st_cur = df_st[(df_st[COL_STAGE] == s)
                              & (df_st[COL_HUB] == h)
                              & (df_st[COL_EC] == e)
                              & (df_st[COL_SOURCE] == source)]
            if len(df_st_cur) > 0:
                dfs.append((df_st_cur, filename_st))
        # Static files (nontuple)
        df_st_0 = df_st[df_st[COL_HUB] == ""]
        for source in df_st_0[COL_SOURCE].unique():
            filename_st = source
            filename_st = os.path.join(dir_path, f"{filename_st}.csv")
            df_st_cur = df_st_0[df_st_0[COL_SOURCE] == source]
            if len(df_st_cur) > 0:
                dfs.append((df_st_cur, filename_st))

        # Horizon time files
        ids_ts_hor = df_ts_hor.columns.to_frame(index=False)[
            [COL_STAGE, COL_HUB, COL_EC, COL_SOURCE]]
        for (s, h, e, source) in ids_ts_hor.itertuples(index=False, name=None):
            filename_ts_hor = f"{source}TS"
            if s:
                filename_ts_hor = f"{source}_{s}_{h}_{e}-TS"
            filename_ts_hor = os.path.join(dir_path, f"{filename_ts_hor}.csv")
            df_ts_hor_cur = df_ts_hor.xs((s, h, e, source), axis=1,
                                         level=(COL_STAGE, COL_HUB, COL_EC,
                                                COL_SOURCE),
                                         drop_level=False)
            if len(df_ts_hor_cur) > 0:
                dfs.append((df_ts_hor_cur, filename_ts_hor))

        # Clustered time files
        if df_ts_cl is not None:
            ids_ts_cl = df_ts_cl.columns.to_frame(index=False)[
                [COL_STAGE, COL_HUB, COL_EC, COL_SOURCE]]
            for (s, h, e, source) in ids_ts_cl.itertuples(index=False,
                                                          name=None):
                filename_ts_cl = f"{source}-TSCL"
                if s:
                    filename_ts_cl = f"{source}_{s}_{h}_{e}-TSCL"
                filename_ts_cl = os.path.join(dir_path,
                                              f"{filename_ts_cl}.csv")
                df_ts_cl_cur = df_ts_cl.xs((s, h, e, source), axis=1,
                                           level=(COL_STAGE, COL_HUB, COL_EC,
                                                  COL_SOURCE),
                                           drop_level=False)
                if len(df_ts_cl_cur) > 0:
                    dfs.append((df_ts_cl_cur, filename_ts_cl))

    # Return
    return dfs


def write_data_time_series(imports: Imports, times: Times, dir_path: str
                           ) -> None:
    """
    Writes all time series with actual data (def_value is not enough) in an
    Imports data object to a dedicated csv file in a directory

    :param imports: The Imports data object whose time series are to be written
    :type imports: Demands
    :param times: Times data object
    :type times: Times
    :param dir_path: Path where the csv file will be placed
    :type dir_path: str
    """
    # Create directory if it does not exist
    if not os.path.isdir(dir_path):
        if not create_dir(dir_path):
            raise exceptions.EhubXException(
                "Could not write import time series data because "
                "the directory could not be created", module=LOG_MODULE_STR)

    # Gather time series
    data: Dict[Tuple[str, str, str, str], List[float]] = {}
    for (kind, stage, ids, series) in imports.time_series:
        # Skip series without values
        if not series.has_values:
            continue
        if kind == TimeSeriesKind.IMPORTPRICE:
            data[stage.key, ids[0], ids[1], YAMLKEY_PRICE] = [
                series.get_value(t) for t in times.ids_in_order]
        if kind == TimeSeriesKind.IMPORTMIN:
            data[stage.key, ids[0], ids[1], YAMLKEY_MIN] = [
                series.get_value(t) for t in times.ids_in_order]
        if kind == TimeSeriesKind.IMPORTMAX:
            data[stage.key, ids[0], ids[1], YAMLKEY_MAX] = [
                series.get_value(t) for t in times.ids_in_order]
        if kind == TimeSeriesKind.IMPORTCO2:
            data[stage.key, ids[0], ids[1], YAMLKEY_CO2] = [
                series.get_value(t) for t in times.ids_in_order]

    # Write demands file
    if data:
        df = pd.DataFrame(data)
        df.columns.names = [HeaderId.STAGEID.value, HeaderId.HUBID.value,
                            HeaderId.ECID.value, HeaderId.PROFILEKEY.value]
        df.index += 1
        df.to_csv(os.path.join(dir_path, FILENAME_TIMESERIES_IMPORTS))
