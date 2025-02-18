"""Export writer module. Writes out information from the imports submodule to
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
from ehubx.data.export_data import Exports
from ehubx.data.time_data import Times
from ehubx.data.time_series import TimeSeries
from ehubx.parser.import_export_parser import YAMLKEY_PRICE, YAMLKEY_MIN, \
    YAMLKEY_MAX, YAMLKEY_CO2
from ehubx.model import export_model
from ehubx.writer.common_writer import create_dir, add_to_df_st, \
    add_to_df_ts_cl

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

ENTRY_EXPPROFITTOTAL: str = \
    f"Total export profit ({export_model.VAR_EXPPROFITTOTAL})"
"""Entry name for total export cost variable in result files"""

ENTRY_EXPCO2: str = f"Embodied CO2 in exports ({export_model.VAR_EXPCO2})"
"""Entry name for export CO2 variable in result files"""

ENTRY_EXPCO2TOTAL: str = \
    f"Total embodied CO2 in exports ({export_model.VAR_EXPCO2TOTAL})"
"""Entry name for total export CO2 variable in result files"""


def format_all(energy_system: EnergySystem, model: Model, df_st: pd.DataFrame,
               df_ts_hor: pd.DataFrame, df_ts_cl: Optional[pd.DataFrame]
               ) -> None:
    # Total export profit
    var = getattr(model, export_model.VAR_EXPPROFITTOTAL)
    exp_profit_total = value(var, exception=False)
    add_to_df_st(df_st, ENTRY_EXPPROFITTOTAL, exp_profit_total, unit="CHF",
                 source=SOURCE, in_res="result")

    # Total export CO2
    for s in energy_system.stages.ids_in_order:
        var = getattr(model, export_model.VAR_EXPCO2TOTAL)
        exp_co2_total = value(var[s.key], exception=False)
        add_to_df_st(df_st, ENTRY_EXPCO2TOTAL, exp_co2_total, unit="kg",
                     stage=s.key, source=SOURCE, in_res="result")

    # Tuple-specific values
    for (s, h, e) in energy_system.exports.tuples:
        _format_tuple(energy_system, model, s, h, e, df_st, df_ts_hor,
                      df_ts_cl)


def _format_tuple(energy_system: EnergySystem, model: Model, s: StageId,
                  h: HubId, e: EcId, df_st: pd.DataFrame,
                  df_ts_hor: pd.DataFrame, df_ts_cl: Optional[pd.DataFrame]
                  ) -> None:

    # price
    price = energy_system.exports.get_price(s, h, e)
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
    co2 = energy_system.exports.get_co2(s, h, e)
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
    exp_min = energy_system.exports.get_min(s, h, e)
    if exp_min.has_values:
        add_to_df_ts_cl(df_ts_hor, df_ts_cl,
            energy_system.times, ENTRY_MIN, exp_min, unit="kW",
            stage=s.key, hub=h.key, ec=e.key, source=SOURCE, in_res="input")
    if not exp_min.has_values:
        exp_min_def = exp_min.def_value
        assert exp_min_def is not None
        add_to_df_st(df_st, ENTRY_MIN, exp_min_def, unit="kW", stage=s.key,
                     hub=h.key, ec=e.key, source=SOURCE, in_res="input")

    # max
    exp_max = energy_system.exports.get_max(s, h, e)
    if exp_max.has_values:
        add_to_df_ts_cl(df_ts_hor, df_ts_cl,
            energy_system.times, ENTRY_MAX, exp_max, unit="kW",
            stage=s.key, hub=h.key, ec=e.key, source=SOURCE, in_res="input")
    if not exp_max.has_values:
        exp_max_def = exp_max.def_value
        assert exp_max_def is not None
        add_to_df_st(df_st, ENTRY_MAX, exp_max_def, unit="kW", stage=s.key,
                     hub=h.key, ec=e.key, source=SOURCE, in_res="input")

    # sum_min
    sum_min = energy_system.exports.get_sum_min(s, h, e)
    add_to_df_st(df_st, ENTRY_SUMMIN, sum_min, unit="kWh", stage=s.key,
                 hub=h.key, ec=e.key, source=SOURCE, in_res="input")

    # sum_max
    sum_max = energy_system.exports.get_sum_max(s, h, e)
    add_to_df_st(df_st, ENTRY_SUMMAX, sum_max, unit="kWh", stage=s.key,
                 hub=h.key, ec=e.key, source=SOURCE, in_res="input")

    # Exports
    var = getattr(model, export_model.VAR_EXP)
    exp = TimeSeries()
    for t in energy_system.times.ids:
        exp.set_value(t, value(var[s.key, h.key, e.key, t.key_as_int],
                               exception=False))
    add_to_df_ts_cl(df_ts_hor, df_ts_cl, energy_system.times,
        ENTRY_EXP, exp, unit="kW", stage=s.key, hub=h.key, ec=e.key,
        source=SOURCE, in_res="result")

    # Export profit
    var = getattr(model, export_model.VAR_EXPPROFIT)
    exp_profit = value(var[s.key, h.key, e.key], exception=False)
    add_to_df_st(df_st, ENTRY_EXPPROFIT, exp_profit, unit="CHF", stage=s.key,
                 hub=h.key, ec=e.key, source=SOURCE, in_res="result")

    # Export CO2
    var = getattr(model, export_model.VAR_EXPCO2)
    exp_co2 = value(var[s.key, h.key, e.key], exception=False)
    add_to_df_st(df_st, ENTRY_EXPCO2, exp_co2, unit="kg", stage=s.key,
                 hub=h.key, ec=e.key, source=SOURCE, in_res="result")


def write_data_time_series(exports: Exports, times: Times,
                           dir_path: str) -> None:
    """
    Writes all time series with actual data (def_value is not enough) in an
    Exports data object to a dedicated csv file in a directory

    :param exports: The Exports data object whose time series are to be written
    :type exports: Exports
    :param times: Times data object
    :type times: Times
    :param dir_path: Path where the csv file will be placed
    :type dir_path: str
    """
    # Create directory if it does not exist
    if not os.path.isdir(dir_path):
        if not create_dir(dir_path):
            raise exceptions.EhubXException(
                "Could not write export time series data because "
                "the directory could not be created", module=LOG_MODULE_STR)

    # Gather time series
    data: Dict[Tuple[str, str, str, str], List[float]] = {}
    for (kind, stage, ids, series) in exports.time_series:
        # Skip series without values
        if not series.has_values:
            continue
        if kind == TimeSeriesKind.EXPORTPRICE:
            data[stage.key, ids[0], ids[1], YAMLKEY_PRICE] = [
                series.get_value(t) for t in times.ids_in_order]
        if kind == TimeSeriesKind.EXPORTMIN:
            data[stage.key, ids[0], ids[1], YAMLKEY_MIN] = [
                series.get_value(t) for t in times.ids_in_order]
        if kind == TimeSeriesKind.EXPORTMAX:
            data[stage.key, ids[0], ids[1], YAMLKEY_MAX] = [
                series.get_value(t) for t in times.ids_in_order]
        if kind == TimeSeriesKind.EXPORTCO2:
            data[stage.key, ids[0], ids[1], YAMLKEY_CO2] = [
                series.get_value(t) for t in times.ids_in_order]

    # Write demands file
    if data:
        df = pd.DataFrame(data)
        df.columns.names = [HeaderId.STAGEID.value, HeaderId.HUBID.value,
                            HeaderId.ECID.value, HeaderId.PROFILEKEY.value]
        df.index += 1
        df.to_csv(os.path.join(dir_path, FILENAME_TIMESERIES_EXPORTS))
