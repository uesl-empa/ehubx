"""Load shedding writer module. Writes out information from the load shedding
submodule to files"""

import os
from typing import Dict, List, Optional, Tuple

import pandas as pd
from pyomo.core import Model, value

from ehubx.core import exceptions
from ehubx.core.common import TimeSeriesKind
from ehubx.data.ec_data import EcId
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.hub_data import HubId
from ehubx.data.load_shedding_data import LoadShedding
from ehubx.data.stage_data import StageId
from ehubx.data.time_data import Times
from ehubx.data.time_series import TimeSeries
from ehubx.model import load_shedding_model
from ehubx.parser.csv_parser import HeaderId
from ehubx.parser.load_shedding_parser import (
    YAMLKEY_ENERGYCOST,
    YAMLKEY_MAXABS,
    YAMLKEY_MAXREL,
)
from ehubx.writer.common_writer import add_to_df_st, add_to_df_ts_cl, create_dir


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "writ/load_shed"
"""String identifying the load shedding writer module for logging purposes"""

FILENAME_TIMESERIES_LOADSHEDDING: str = "load_shedding.csv"
"""Filename for load shedding time series"""

SOURCE: str = "load shedding"
"""Display name for the load shedding module in result files"""

ENTRY_MAXABS: str = "Maximal absolute load shedding (max_abs)"
"""Entry name for load shedding parameter 'max_abs' in result files"""

ENTRY_MAXREL: str = "Maximal relative load shedding (max_rel)"
"""Entry name for load shedding parameter 'max_rel' in result files"""

ENTRY_ENERGYCOST: str = "Load shedding energy cost (energy_cost)"
"""Entry name for load shedding parameter 'energy_cost' in result files"""

ENTRY_LOADSHEDDING: str = f"Load shedding ({load_shedding_model.VAR_LOADSHEDDING})"
"""Entry name for load shedding variable in result files"""

ENTRY_LOADSHEDDINGCOST: str = (
    f"Load shedding cost ({load_shedding_model.VAR_LOADHSHEDDINGCOST})"
)
"""Entry name for load shedding cost variable in result files"""

ENTRY_LOADSHEDDINGCOSTTOTAL: str = (
    f"Total load shedding cost ({load_shedding_model.VAR_LOADHSHEDDINGCOSTTOTAL})"
)
"""Entry name for total load shedding cost variable in result files"""


def format_all(
    energy_system: EnergySystem,
    model: Model,
    df_st: pd.DataFrame,
    df_ts_hor: pd.DataFrame,
    df_ts_cl: Optional[pd.DataFrame],
) -> None:
    # Total load shedding cost
    var = getattr(model, load_shedding_model.VAR_LOADHSHEDDINGCOSTTOTAL)
    total_load_shedding_cost = value(var, exception=False)
    add_to_df_st(
        df_st,
        ENTRY_LOADSHEDDINGCOSTTOTAL,
        total_load_shedding_cost,
        unit="CHF",
        source=SOURCE,
        in_res="result",
    )

    # Tuple-specific values
    for s, h, e in energy_system.load_shedding.get_enabled_tuples(
        energy_system.stages,
        energy_system.hubs,
        energy_system.ecs,
        energy_system.demands,
    ):
        _format_tuple(energy_system, model, s, h, e, df_st, df_ts_hor, df_ts_cl)


def _format_tuple(
    energy_system: EnergySystem,
    model: Model,
    s: StageId,
    h: HubId,
    e: EcId,
    df_st: pd.DataFrame,
    df_ts_hor: pd.DataFrame,
    df_ts_cl: Optional[pd.DataFrame],
) -> None:
    # max_abs
    max_abs = energy_system.load_shedding.get_max_abs(s, h, e)
    if max_abs.has_values:
        add_to_df_ts_cl(
            df_ts_hor,
            df_ts_cl,
            energy_system.times,
            ENTRY_MAXABS,
            max_abs,
            unit="kW",
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )
    if not max_abs.has_values:
        max_abs_def = max_abs.def_value
        assert max_abs_def is not None
        add_to_df_st(
            df_st,
            ENTRY_MAXABS,
            max_abs_def,
            unit="kW",
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )

    # max_rel
    max_rel = energy_system.load_shedding.get_max_rel(s, h, e)
    if max_rel.has_values:
        add_to_df_ts_cl(
            df_ts_hor,
            df_ts_cl,
            energy_system.times,
            ENTRY_MAXREL,
            max_rel,
            unit="1",
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )
    if not max_rel.has_values:
        max_rel_def = max_rel.def_value
        assert max_rel_def is not None
        add_to_df_st(
            df_st,
            ENTRY_MAXREL,
            max_rel_def,
            unit="1",
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )

    # energy_cost
    energy_cost = energy_system.load_shedding.get_energy_cost(s, h, e)
    if energy_cost.has_values:
        add_to_df_ts_cl(
            df_ts_hor,
            df_ts_cl,
            energy_system.times,
            ENTRY_ENERGYCOST,
            energy_cost,
            unit="CHF/kW",
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )
    if not energy_cost.has_values:
        energy_cost_def = energy_cost.def_value
        assert energy_cost_def is not None
        add_to_df_st(
            df_st,
            ENTRY_ENERGYCOST,
            energy_cost_def,
            unit="CHF/kW",
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )

    # Load shedding
    var = getattr(model, load_shedding_model.VAR_LOADSHEDDING)
    load_shedding = TimeSeries()
    for t in energy_system.times.ids:
        load_shedding.set_value(
            t, value(var[s.key, h.key, e.key, t.key_as_int], exception=False)
        )
    add_to_df_ts_cl(
        df_ts_hor,
        df_ts_cl,
        energy_system.times,
        ENTRY_LOADSHEDDING,
        load_shedding,
        unit="kW",
        stage=s.key,
        hub=h.key,
        ec=e.key,
        source=SOURCE,
        in_res="result",
    )

    # Load shedding cost
    var = getattr(model, load_shedding_model.VAR_LOADHSHEDDINGCOST)
    load_shedding_cost = value(var[s.key, h.key, e.key], exception=False)
    add_to_df_st(
        df_st,
        ENTRY_LOADSHEDDINGCOST,
        load_shedding_cost,
        unit="CHF",
        stage=s.key,
        hub=h.key,
        ec=e.key,
        source=SOURCE,
        in_res="result",
    )


def write_data_time_series(
    load_shedding: LoadShedding, times: Times, dir_path: str
) -> None:
    """
    Writes all time series with actual data (def_value is not enough) in a
    load shedding data object to a dedicated csv file in a directory

    :param load_shedding: The load shedding data object whose time series are
        to be written
    :type load_shedding: LoadShedding
    :param times: Times data object
    :type times: Times
    :param dir_path: Path where the csv file will be placed
    :type dir_path: str
    """
    # Create directory if it does not exist
    if not os.path.isdir(dir_path):
        if not create_dir(dir_path):
            raise exceptions.EhubXException(
                "Could not write load shedding time series data because "
                "the directory could not be created",
                module=LOG_MODULE_STR,
            )

    # Gather time series
    data: Dict[Tuple[str, str, str, str], List[float]] = {}
    for kind, stage, ids, series in load_shedding.time_series:
        # Skip series without values
        if not series.has_values:
            continue
        if kind == TimeSeriesKind.LOADSHEDMAXABS:
            data[stage.key, ids[0], ids[1], YAMLKEY_MAXABS] = [
                series.get_value(t) for t in times.ids_in_order
            ]
        if kind == TimeSeriesKind.LOADSHEDMAXREL:
            data[stage.key, ids[0], ids[1], YAMLKEY_MAXREL] = [
                series.get_value(t) for t in times.ids_in_order
            ]
        if kind == TimeSeriesKind.LOADSHEDENERGYCOST:
            data[stage.key, ids[0], ids[1], YAMLKEY_ENERGYCOST] = [
                series.get_value(t) for t in times.ids_in_order
            ]

    # Write demands file
    if data:
        df = pd.DataFrame(data)
        df.columns.names = [
            HeaderId.STAGEID.value,
            HeaderId.HUBID.value,
            HeaderId.ECID.value,
            HeaderId.PROFILEKEY.value,
        ]
        df.index += 1
        df.to_csv(os.path.join(dir_path, FILENAME_TIMESERIES_LOADSHEDDING))
