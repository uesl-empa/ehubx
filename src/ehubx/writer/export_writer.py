"""Export writer module. Writes out information from the imports submodule to
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
from ehubx.model import ec_model, export_model
from ehubx.parser.csv_parser import HeaderId
from ehubx.parser.import_export_parser import (
    YAMLKEY_CO2,
    YAMLKEY_MAX,
    YAMLKEY_MIN,
    YAMLKEY_PRICE,
)
from ehubx.writer.common_writer import DfStBuilder, add_to_df_ts_cl, create_dir


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "writ/export"
"""String identifying the export writer module for logging purposes"""

FILENAME_TIMESERIES_EXPORTS: str = "exports.csv"
"""Filename for export time series"""

SOURCE: str = "exports"
"""Display name for the exports module in result files"""

ENTRY_PRICE: str = "Import price"
"""Entry name for export parameter 'price' in result files"""

ENTRY_CO2: str = "Import CO2"
"""Entry name for export parameter 'co2' in result files"""

ENTRY_MIN: str = "Min export"
"""Entry name for export parameter 'min' in result files"""

ENTRY_MAX: str = "Max export"
"""Entry name for export parameter 'max' in result files"""

ENTRY_SUMMIN: str = "Min summed-up export"
"""Entry name for export parameter 'sum_min' in result files"""

ENTRY_SUMMAX: str = "Max summed-up export"
"""Entry name for export parameter 'sum_max' in result files"""

ENTRY_EXP: str = f"Export ({export_model.VAR_EXP})"
"""Entry name for export variable in result files"""

ENTRY_EXPPROFIT: str = f"Export cost ({export_model.VAR_EXPPROFIT})"
"""Entry name for export profit variable in result files"""

ENTRY_EXPPROFITTOTAL: str = f"Total export profit ({export_model.VAR_EXPPROFITTOTAL})"
"""Entry name for total export cost variable in result files"""

ENTRY_EXPCO2: str = f"Embodied CO2 in exports ({export_model.VAR_EXPCO2})"
"""Entry name for export CO2 variable in result files"""

ENTRY_EXPCO2TOTAL: str = (
    f"Total embodied CO2 in exports ({export_model.VAR_EXPCO2TOTAL})"
)
"""Entry name for total export CO2 variable in result files"""


def format_all(
    energy_system: EnergySystem,
    model: Model,
    df_st_builder: DfStBuilder,
    df_ts_hor: pd.DataFrame,
    df_ts_cl: Optional[pd.DataFrame],
) -> None:
    # Total export profit
    var = getattr(model, export_model.VAR_EXPPROFITTOTAL)
    exp_profit_total_fl = value(var, exception=False)
    if exp_profit_total_fl is not None:
        exp_profit_total = Value(exp_profit_total_fl, unit=energy_system.currency_unit)
        df_st_builder.add_row(
            ENTRY_EXPPROFITTOTAL,
            exp_profit_total,
            unit=energy_system.currency_unit,
            source=SOURCE,
            in_res="result",
        )

    # Total export CO2
    for s in energy_system.stages.ids_in_order:
        var = getattr(model, export_model.VAR_EXPCO2TOTAL)
        exp_co2_total_fl = value(var[s.key], exception=False)
        if exp_co2_total_fl is not None:
            exp_co2_total = Value(exp_co2_total_fl, unit=energy_system.mass_unit)
            df_st_builder.add_row(
                ENTRY_EXPCO2TOTAL,
                exp_co2_total,
                unit=energy_system.mass_unit,
                stage=s.key,
                source=SOURCE,
                in_res="result",
            )

    # Tuple-specific values
    for s, h, e in energy_system.exports.tuples:
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
    # price
    price = energy_system.exports.get_price(s, h, e)
    price_unit = energy_system.currency_unit / ec_unit
    if price.has_values:
        add_to_df_ts_cl(
            df_ts_hor,
            df_ts_cl,
            energy_system.times,
            ENTRY_PRICE,
            price,
            price_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )
    if not price.has_values:
        price_def = price.def_value
        assert price_def is not None
        df_st_builder.add_row(
            ENTRY_PRICE,
            price_def,
            unit=price_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )

    # co2
    co2 = energy_system.exports.get_co2(s, h, e)
    co2_unit = energy_system.mass_unit / ec_unit
    if co2.has_values:
        add_to_df_ts_cl(
            df_ts_hor,
            df_ts_cl,
            energy_system.times,
            ENTRY_CO2,
            co2,
            unit=co2_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )
    if not co2.has_values:
        co2_def = co2.def_value
        assert co2_def is not None
        df_st_builder.add_row(
            ENTRY_CO2,
            co2_def,
            unit=co2_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )

    # min
    exp_min = energy_system.exports.get_min(s, h, e)
    exp_min_unit = ec_unit / TimeUnit.H
    if exp_min.has_values:
        add_to_df_ts_cl(
            df_ts_hor,
            df_ts_cl,
            energy_system.times,
            ENTRY_MIN,
            exp_min,
            unit=exp_min_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )
    if not exp_min.has_values:
        exp_min_def = exp_min.def_value
        assert exp_min_def is not None
        df_st_builder.add_row(
            ENTRY_MIN,
            exp_min_def,
            unit=exp_min_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )

    # max
    exp_max = energy_system.exports.get_max(s, h, e)
    exp_max_unit = ec_unit / TimeUnit.H
    if exp_max.has_values:
        add_to_df_ts_cl(
            df_ts_hor,
            df_ts_cl,
            energy_system.times,
            ENTRY_MAX,
            exp_max,
            unit=exp_max_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )
    if not exp_max.has_values:
        exp_max_def = exp_max.def_value
        assert exp_max_def is not None
        df_st_builder.add_row(
            ENTRY_MAX,
            exp_max_def,
            unit=exp_max_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )

    # sum_min
    sum_min = energy_system.exports.get_sum_min(s, h, e, energy_system.ecs)
    df_st_builder.add_row(
        ENTRY_SUMMIN,
        sum_min,
        unit=ec_unit,
        stage=s.key,
        hub=h.key,
        ec=e.key,
        source=SOURCE,
        in_res="input",
    )

    # sum_max
    sum_max = energy_system.exports.get_sum_max(s, h, e, energy_system.ecs)
    df_st_builder.add_row(
        ENTRY_SUMMAX,
        sum_max,
        unit=ec_unit,
        stage=s.key,
        hub=h.key,
        ec=e.key,
        source=SOURCE,
        in_res="input",
    )

    # Exports
    var = getattr(model, export_model.VAR_EXP)
    exp = TimeSeries()
    exp_unit = ec_unit / TimeUnit.H
    for t in energy_system.times.ids:
        exp_fl = value(var[s.key, h.key, e.key, t.key_as_int], exception=False)
        if exp_fl is not None:
            exp.set_value(t, Value(exp_fl, unit=exp_unit))
    add_to_df_ts_cl(
        df_ts_hor,
        df_ts_cl,
        energy_system.times,
        ENTRY_EXP,
        exp,
        unit=exp_unit,
        stage=s.key,
        hub=h.key,
        ec=e.key,
        source=SOURCE,
        in_res="result",
    )

    # Export profit
    var = getattr(model, export_model.VAR_EXPPROFIT)
    exp_profit_fl = value(var[s.key, h.key, e.key], exception=False)
    if exp_profit_fl is not None:
        exp_profit = Value(exp_profit_fl, unit=energy_system.currency_unit)
        df_st_builder.add_row(
            ENTRY_EXPPROFIT,
            exp_profit,
            unit=energy_system.currency_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="result",
        )

    # Export CO2
    var = getattr(model, export_model.VAR_EXPCO2)
    exp_co2_fl = value(var[s.key, h.key, e.key], exception=False)
    if exp_co2_fl is not None:
        exp_co2 = Value(exp_co2_fl, unit=energy_system.mass_unit)
        df_st_builder.add_row(
            ENTRY_EXPCO2,
            exp_co2,
            unit=energy_system.mass_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="result",
        )


def write_data_time_series(energy_system: EnergySystem, dir_path: str) -> None:
    """
    Writes all time series with actual data (def_value is not enough) in an
    Exports data object to a dedicated csv file in a directory

    :param energy_system: Energy system data object
    :type energy_system: EnergySystem
    :param dir_path: Path where the csv file will be placed
    :type dir_path: str
    """
    # Create directory if it does not exist
    if not os.path.isdir(dir_path):
        if not create_dir(dir_path):
            raise exceptions.EhubXException(
                "Could not write export time series data because "
                "the directory could not be created",
                module=LOG_MODULE_STR,
            )

    # Gather time series
    data: Dict[Tuple[str, str, str, str, str], List[float]] = {}
    for kind, stage, ids, series in energy_system.exports.time_series:
        # Skip series without values
        if not series.has_values:
            continue
        ec_unit = ec_model.get_ec_model_unit(
            energy_system.ecs.get_unit(EcId(ids[1])),
            energy_system.mass_unit,
            energy_system.power_unit,
        )
        if kind == TimeSeriesKind.EXPORTPRICE:
            unit = energy_system.currency_unit / ec_unit
            data[stage.key, ids[0], ids[1], YAMLKEY_PRICE, str(unit)] = [
                series.get_value(t).to_float(unit=unit)
                for t in energy_system.times.ids_in_order
            ]
        if kind == TimeSeriesKind.EXPORTMIN:
            unit = ec_unit / TimeUnit.H
            data[stage.key, ids[0], ids[1], YAMLKEY_MIN, str(unit)] = [
                series.get_value(t).to_float(unit=unit)
                for t in energy_system.times.ids_in_order
            ]
        if kind == TimeSeriesKind.EXPORTMAX:
            unit = ec_unit / TimeUnit.H
            data[stage.key, ids[0], ids[1], YAMLKEY_MAX, str(unit)] = [
                series.get_value(t).to_float(unit=unit)
                for t in energy_system.times.ids_in_order
            ]
        if kind == TimeSeriesKind.EXPORTCO2:
            unit = energy_system.mass_unit / ec_unit
            data[stage.key, ids[0], ids[1], YAMLKEY_CO2, str(unit)] = [
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
        df.to_csv(os.path.join(dir_path, FILENAME_TIMESERIES_EXPORTS))
