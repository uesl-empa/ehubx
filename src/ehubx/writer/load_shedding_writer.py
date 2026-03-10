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
from ehubx.data.stage_data import StageId
from ehubx.data.time_series import TimeSeries
from ehubx.data.unit import DimlessUnit, TimeUnit
from ehubx.data.value import Value
from ehubx.model import ec_model, load_shedding_model
from ehubx.parser.csv_parser import HeaderId
from ehubx.parser.load_shedding_parser import (
    YAMLKEY_ENERGYCOST,
    YAMLKEY_MAXABS,
    YAMLKEY_MAXREL,
)
from ehubx.writer.common_writer import DfStBuilder, add_to_df_ts_cl, create_dir


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
    df_st_builder: DfStBuilder,
    df_ts_hor: pd.DataFrame,
    df_ts_cl: Optional[pd.DataFrame],
) -> None:
    # Total load shedding cost
    var = getattr(model, load_shedding_model.VAR_LOADHSHEDDINGCOSTTOTAL)
    total_load_shedding_cost_fl = value(var, exception=False)
    if total_load_shedding_cost_fl is not None:
        total_load_shedding_cost = Value(
            total_load_shedding_cost_fl, unit=energy_system.currency_unit
        )
        df_st_builder.add_row(
            ENTRY_LOADSHEDDINGCOSTTOTAL,
            total_load_shedding_cost,
            unit=energy_system.currency_unit,
            source=SOURCE,
            in_res="result",
        )

    # Tuple-specific values
    for s, h, e in energy_system.load_shedding.get_enabled_tuples():
        _format_tuple(energy_system, model, s, h, e, df_st_builder, df_ts_hor, df_ts_cl)


def _format_tuple(
    energy_system: EnergySystem,
    model: Model,
    s: StageId,
    h: HubId,
    e: EcId,
    df_st_builder: DfStBuilder,
    df_ts_hor: pd.DataFrame,
    df_ts_cl: Optional[pd.DataFrame],
) -> None:
    # ec_unit
    ec_unit = ec_model.get_ec_model_unit(
        energy_system.ecs.get_unit(e),
        energy_system.mass_unit,
        energy_system.power_unit,
    )
    # max_abs
    max_abs = energy_system.load_shedding.get_max_abs(s, h, e)
    max_abs_unit = ec_unit / TimeUnit.H
    if max_abs.has_values:
        add_to_df_ts_cl(
            df_ts_hor,
            df_ts_cl,
            energy_system.times,
            ENTRY_MAXABS,
            max_abs,
            max_abs_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )
    if not max_abs.has_values:
        max_abs_def = max_abs.def_value
        assert max_abs_def is not None
        df_st_builder.add_row(
            ENTRY_MAXABS,
            max_abs_def,
            unit=max_abs_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )

    # max_rel
    max_rel = energy_system.load_shedding.get_max_rel(s, h, e)
    max_rel_unit = DimlessUnit()
    if max_rel.has_values:
        add_to_df_ts_cl(
            df_ts_hor,
            df_ts_cl,
            energy_system.times,
            ENTRY_MAXREL,
            max_rel,
            max_rel_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )
    if not max_rel.has_values:
        max_rel_def = max_rel.def_value
        assert max_rel_def is not None
        df_st_builder.add_row(
            ENTRY_MAXREL,
            max_rel_def,
            unit=max_rel_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )

    # energy_cost
    energy_cost = energy_system.load_shedding.get_energy_cost(s, h, e)
    energy_cost_unit = energy_system.currency_unit / ec_unit
    if energy_cost.has_values:
        add_to_df_ts_cl(
            df_ts_hor,
            df_ts_cl,
            energy_system.times,
            ENTRY_ENERGYCOST,
            energy_cost,
            energy_cost_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )
    if not energy_cost.has_values:
        energy_cost_def = energy_cost.def_value
        assert energy_cost_def is not None
        df_st_builder.add_row(
            ENTRY_ENERGYCOST,
            energy_cost_def,
            unit=energy_cost_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )

    # Load shedding
    var = getattr(model, load_shedding_model.VAR_LOADSHEDDING)
    shed = TimeSeries()
    shed_unit = ec_unit / TimeUnit.H
    for t in energy_system.times.ids:
        shed_fl = value(var[s.key, h.key, e.key, t.key_as_int], exception=False)
        if shed_fl is not None:
            shed.set_value(t, Value(shed_fl, unit=shed_unit))
    add_to_df_ts_cl(
        df_ts_hor,
        df_ts_cl,
        energy_system.times,
        ENTRY_LOADSHEDDING,
        shed,
        unit=shed_unit,
        stage=s.key,
        hub=h.key,
        ec=e.key,
        source=SOURCE,
        in_res="result",
    )

    # Load shedding cost
    var = getattr(model, load_shedding_model.VAR_LOADHSHEDDINGCOST)
    shed_cost_fl = value(var[s.key, h.key, e.key], exception=False)
    if shed_cost_fl is not None:
        shed_cost = Value(shed_cost_fl, unit=energy_system.currency_unit)
        df_st_builder.add_row(
            ENTRY_LOADSHEDDINGCOST,
            shed_cost,
            unit=energy_system.currency_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="result",
        )


def write_data_time_series(energy_system: EnergySystem, dir_path: str) -> None:
    """
    Writes all time series with actual data (def_value is not enough) in a
    load shedding data object to a dedicated csv file in a directory

    :param energy_system: Energy system data object
    :type energy_system: EnergySystem
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
    data: Dict[Tuple[str, str, str, str, str], List[float]] = {}
    for kind, stage, ids, series in energy_system.load_shedding.time_series:
        # Skip series without values
        if not series.has_values:
            continue
        ec_unit = ec_model.get_ec_model_unit(
            energy_system.ecs.get_unit(EcId(ids[1])),
            energy_system.mass_unit,
            energy_system.power_unit,
        )
        if kind == TimeSeriesKind.LOADSHEDMAXABS:
            unit = ec_unit / TimeUnit.H
            data[stage.key, ids[0], ids[1], YAMLKEY_MAXABS, str(unit)] = [
                series.get_value(t).to_float(unit=unit)
                for t in energy_system.times.ids_in_order
            ]
        if kind == TimeSeriesKind.LOADSHEDMAXREL:
            unit = DimlessUnit()
            data[stage.key, ids[0], ids[1], YAMLKEY_MAXREL, str(unit)] = [
                series.get_value(t).to_float(unit=unit)
                for t in energy_system.times.ids_in_order
            ]
        if kind == TimeSeriesKind.LOADSHEDENERGYCOST:
            unit = energy_system.currency_unit / ec_unit
            data[stage.key, ids[0], ids[1], YAMLKEY_ENERGYCOST, str(unit)] = [
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
        df.to_csv(os.path.join(dir_path, FILENAME_TIMESERIES_LOADSHEDDING))
