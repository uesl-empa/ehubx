"""Load shifting writer module. Writes out information from the load shifting
submodule to files"""
import os
from typing import Dict, List, Optional, Tuple
import pandas as pd
from pyomo.core import Model, value
from ehubx.core.common import TimeSeriesKind
from ehubx.core import exceptions
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.stage_data import StageId
from ehubx.data.hub_data import HubId
from ehubx.data.ec_data import EcId
from ehubx.data.load_shifting_data import LoadShifting, LoadShiftId
from ehubx.data.time_data import Times
from ehubx.data.time_series import TimeSeries
from ehubx.parser.load_shifting_parser import YAMLKEY_MAXABOVEABS, \
    YAMLKEY_MAXABOVEREL, YAMLKEY_MAXBELOWABS, YAMLKEY_MAXBELOWREL, \
    YAMLKEY_ENERGYCOSTABOVE, YAMLKEY_ENERGYCOSTBELOW, YAMLKEY_FIXCOST
from ehubx.parser.csv_parser import HeaderId
from ehubx.model import load_shifting_model
from ehubx.writer.common_writer import create_dir, add_to_df_st, \
    add_to_df_ts_cl

# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "writ/load_shift"
"""String identifying the load shifting writer module for logging purposes"""

FILENAME_TIMESERIES_LOADSHIFTING: str = "load_shifting.csv"
"""Filename for load shifting time series"""

SOURCE: str = "load shifting"
"""Display name for the load shifting module in result files"""

ENTRY_INTERVALLENGTH: str = "Interval length (interval_length)"
"""Entry name for load shifting parameter 'interval_length' in result files"""

ENTRY_INTERVALCAP: str = "Interval capacity (interval_cap)"
"""Entry name for load shifting parameter 'interval_cap' in result files"""

ENTRY_MAXABOVEABS: str = "Maximal absolute above-shifting (max_above_abs)"
"""Entry name for load shifting parameter 'max_above_abs' in result files"""

ENTRY_MAXABOVEREL: str = "Maximal relative above-shifting (max_above_rel)"
"""Entry name for load shifting parameter 'max_above_rel' in result files"""

ENTRY_MAXBELOWABS: str = "Maximal absolute below-shifting (max_below_abs)"
"""Entry name for load shifting parameter 'max_below_abs' in result files"""

ENTRY_MAXBELOWREL: str = "Maximal relative below-shifting (max_below_rel)"
"""Entry name for load shifting parameter 'max_below_rel' in result files"""

ENTRY_PEAKCOSTABOVE: str = "Peak cost for above-shifting (peak_cost_above)"
"""Entry name for load shifting parameter 'peak_cost_above' in result files"""

ENTRY_PEAKCOSTBELOW: str = "Peak cost for below-shifting (peak_cost_below)"
"""Entry name for load shifting parameter 'peak_cost_below' in result files"""

ENTRY_ENERGYCOSTABOVE: str = \
    "Energy cost for above-shifting (energy_cost_above)"
"""Entry name for load shifting parameter 'energy_cost_above' in result
files"""

ENTRY_ENERGYCOSTBELOW: str = \
    "Energy cost for below-shifting (energy_cost_below)"
"""Entry name for load shifting parameter 'energy_cost_below' in result
files"""

ENTRY_FIXCOST: str = "Fix cost for load shifting (fix_cost)"
"""Entry name for load shifting parameter 'fix_cost' in result files"""

ENTRY_LOADSHIFTING: str = \
    f"Load shifting ({load_shifting_model.VAR_LOADSHIFTING})"
"""Entry name for load shifting variable in result files"""

ENTRY_LOADSHIFTINGABOVEPEAK: str = \
    ("Load shifting above-peak "
     f"({load_shifting_model.VAR_LOADSHIFTINGABOVEPEAK})")
"""Entry name for load shifting above-peak variable in result files"""

ENTRY_LOADSHIFTINGBELOWPEAK: str = \
    ("Load shifting below-peak "
     f"({load_shifting_model.VAR_LOADSHIFTINGBELOWPEAK})")
"""Entry name for load shifting above-peak variable in result files"""

ENTRY_LOADSHIFTINGCOSTENERGY: str = \
    ("Load shifting energy cost "
     f"({load_shifting_model.VAR_LOADHSHIFTINGCOSTENERGY})")
"""Entry name for load shifting energy cost variable in result files"""

ENTRY_LOADSHIFTINGCOSTPEAK: str = \
    ("Load shifting peak cost "
     f"({load_shifting_model.VAR_LOADHSHIFTINGCOSTPEAK})")
"""Entry name for load shifting peak cost variable in result files"""

ENTRY_LOADSHIFTINGCOSTFIX: str = \
    ("Load shifting fix cost "
     f"({load_shifting_model.VAR_LOADHSHIFTINGCOSTFIX})")
"""Entry name for load shifting fixed cost variable in result files"""

ENTRY_LOADSHIFTINGCOSTTOTAL: str = \
    ("Load shifting total cost "
     f"({load_shifting_model.VAR_LOADHSHIFTINGCOSTTOTAL})")
"""Entry name for load shifting total cost variable in result files"""

ENTRY_YLOADSHIFTING: str = \
    f"Any load shifting? ({load_shifting_model.VAR_YLOADHSHIFTING})"
"""Entry name for binary load shifting monitoring variable in result files"""


def format_all(energy_system: EnergySystem, model: Model, df_st: pd.DataFrame,
               df_ts_hor: pd.DataFrame, df_ts_cl: Optional[pd.DataFrame]
               ) -> None:
    # Total cost
    var = getattr(model, load_shifting_model.VAR_LOADHSHIFTINGCOSTTOTAL)
    total_cost = value(var, exception=False)
    add_to_df_st(df_st, ENTRY_LOADSHIFTINGCOSTTOTAL, total_cost,
                 unit="CHF", source=SOURCE, in_res="result")

    # Id-and-tuple-specific values
    for ls in energy_system.load_shifting.ids:
        for (s, h, e) in energy_system.load_shifting.get_tuples(ls):
            _format_ls_and_tuple(energy_system, ls, s, h, e, df_st, df_ts_hor,
                                 df_ts_cl)

    # Tuple-specific values
    for (s_, h_, e_) in getattr(model,
                                load_shifting_model.SET_LOADSHIFTINGTUPLE):
        _format_tuple(energy_system, model, StageId(s_), HubId(h_), EcId(e_),
                      df_st, df_ts_hor, df_ts_cl)


def _format_ls_and_tuple(energy_system: EnergySystem, ls: LoadShiftId,
                         s: StageId, h: HubId, e: EcId, df_st: pd.DataFrame,
                         df_ts_hor: pd.DataFrame,
                         df_ts_cl: Optional[pd.DataFrame]) -> None:
    # interval_length
    interval_length = energy_system.load_shifting.get_interval_length(ls)
    add_to_df_st(df_st, ENTRY_INTERVALLENGTH, interval_length, unit="h",
                 load_shift=ls.key, stage=s.key, hub=h.key, ec=e.key,
                 source=SOURCE, in_res="input")

    # interval_cap
    interval_cap = energy_system.load_shifting.get_interval_cap(ls)
    add_to_df_st(df_st, ENTRY_INTERVALCAP, interval_cap, unit="kWh",
                 load_shift=ls.key, stage=s.key, hub=h.key, ec=e.key,
                 source=SOURCE, in_res="input")

    # max_above_abs
    max_above_abs = energy_system.load_shifting.get_max_above_abs(ls)
    if max_above_abs.has_values:
        add_to_df_ts_cl(df_ts_hor, df_ts_cl,
            energy_system.times, ENTRY_MAXABOVEABS, max_above_abs, unit="kW",
            load_shift=ls.key, stage=s.key, hub=h.key, ec=e.key,
            source=SOURCE, in_res="input")
    if not max_above_abs.has_values:
        max_above_abs_def = max_above_abs.def_value
        assert max_above_abs_def is not None
        add_to_df_st(df_st, ENTRY_MAXABOVEABS, max_above_abs_def, unit="kW",
                     load_shift=ls.key, stage=s.key, hub=h.key, ec=e.key,
                     source=SOURCE, in_res="input")

    # max_above_rel
    max_above_rel = energy_system.load_shifting.get_max_above_rel(ls)
    if max_above_rel.has_values:
        add_to_df_ts_cl(df_ts_hor, df_ts_cl,
            energy_system.times, ENTRY_MAXABOVEREL, max_above_rel, unit="1",
            load_shift=ls.key, stage=s.key, hub=h.key, ec=e.key,
            source=SOURCE, in_res="input")
    if not max_above_rel.has_values:
        max_above_rel_def = max_above_rel.def_value
        assert max_above_rel_def is not None
        add_to_df_st(df_st, ENTRY_MAXABOVEREL, max_above_rel_def, unit="1",
                     load_shift=ls.key, stage=s.key, hub=h.key, ec=e.key,
                     source=SOURCE, in_res="input")

    # max_below_abs
    max_below_abs = energy_system.load_shifting.get_max_below_abs(ls)
    if max_below_abs.has_values:
        add_to_df_ts_cl(df_ts_hor, df_ts_cl, energy_system.times,
                        ENTRY_MAXBELOWABS, max_below_abs, unit="kW",
                        load_shift=ls.key, stage=s.key, hub=h.key, ec=e.key,
                        source=SOURCE, in_res="input")
    if not max_below_abs.has_values:
        max_below_abs_def = max_below_abs.def_value
        assert max_below_abs_def is not None
        add_to_df_st(df_st, ENTRY_MAXBELOWABS, max_below_abs_def,
                     unit="kW", load_shift=ls.key, stage=s.key, hub=h.key,
                     ec=e.key, source=SOURCE, in_res="input")

    # max_below_rel
    max_below_rel = energy_system.load_shifting.get_max_below_rel(ls)
    if max_below_rel.has_values:
        add_to_df_ts_cl(df_ts_hor, df_ts_cl,
            energy_system.times, ENTRY_MAXBELOWREL, max_below_rel, unit="1",
            load_shift=ls.key, stage=s.key, hub=h.key, ec=e.key,
            source=SOURCE, in_res="input")
    if not max_below_rel.has_values:
        max_below_rel_def = max_below_rel.def_value
        assert max_below_rel_def is not None
        add_to_df_st(df_st, ENTRY_MAXBELOWREL, max_below_rel_def, unit="1",
                     load_shift=ls.key, stage=s.key, hub=h.key, ec=e.key,
                     source=SOURCE, in_res="input")

    # peak_cost_above
    peak_cost_above = energy_system.load_shifting.get_peak_cost_above(ls)
    add_to_df_st(df_st, ENTRY_PEAKCOSTABOVE, peak_cost_above, unit="CHF/kW",
                 load_shift=ls.key, stage=s.key, hub=h.key,
                 ec=e.key, source=SOURCE, in_res="input")

    # peak_cost_below
    peak_cost_below = energy_system.load_shifting.get_peak_cost_below(ls)
    add_to_df_st(df_st, ENTRY_PEAKCOSTBELOW, peak_cost_below, unit="CHF/kW",
                 load_shift=ls.key, stage=s.key, hub=h.key, ec=e.key,
                 source=SOURCE, in_res="input")

    # energy_cost_above
    energy_cost_above = energy_system.load_shifting.get_energy_cost_above(ls)
    if energy_cost_above.has_values:
        add_to_df_ts_cl(df_ts_hor, df_ts_cl,
            energy_system.times, ENTRY_ENERGYCOSTABOVE, energy_cost_above,
            unit="CHF/kWh", load_shift=ls.key, stage=s.key, hub=h.key,
            ec=e.key, source=SOURCE, in_res="input")
    if not energy_cost_above.has_values:
        energy_cost_above_def = energy_cost_above.def_value
        assert energy_cost_above_def is not None
        add_to_df_st(df_st, ENTRY_ENERGYCOSTABOVE, energy_cost_above_def,
                     unit="CHF/kWh", load_shift=ls.key, stage=s.key,
                     hub=h.key, ec=e.key, source=SOURCE, in_res="input")

    # energy_cost_below
    energy_cost_below = energy_system.load_shifting.get_energy_cost_below(ls)
    if energy_cost_below.has_values:
        add_to_df_ts_cl(df_ts_hor, df_ts_cl, energy_system.times,
                        ENTRY_ENERGYCOSTBELOW, energy_cost_below,
                        unit="CHF/kWh", load_shift=ls.key, stage=s.key,
                        hub=h.key, ec=e.key, source=SOURCE, in_res="input")
    if not energy_cost_below.has_values:
        energy_cost_below_def = energy_cost_below.def_value
        assert energy_cost_below_def is not None
        add_to_df_st(df_st, ENTRY_ENERGYCOSTBELOW, energy_cost_below_def,
                     unit="CHF/kWh", load_shift=ls.key, stage=s.key,
                     hub=h.key, ec=e.key, source=SOURCE, in_res="input")

    # fix_cost
    fix_cost = energy_system.load_shifting.get_fix_cost(ls)
    if fix_cost.has_values:
        add_to_df_ts_cl(df_ts_hor, df_ts_cl,
            energy_system.times, ENTRY_FIXCOST, fix_cost, unit="CHF/h",
            load_shift=ls.key, stage=s.key, hub=h.key, ec=e.key,
            source=SOURCE, in_res="input")
    if not fix_cost.has_values:
        fix_cost_def = fix_cost.def_value
        assert fix_cost_def is not None
        add_to_df_st(df_st, ENTRY_FIXCOST, fix_cost_def, unit="CHF/h",
                     load_shift=ls.key, stage=s.key, hub=h.key, ec=e.key,
                     source=SOURCE, in_res="input")


def _format_tuple(energy_system: EnergySystem, model: Model, s: StageId,
                  h: HubId, e: EcId, df_st: pd.DataFrame,
                  df_ts_hor: pd.DataFrame, df_ts_cl: Optional[pd.DataFrame]
                  ) -> None:
    # Load shifting
    var = getattr(model, load_shifting_model.VAR_LOADSHIFTING)
    load_shifting = TimeSeries()
    for t in energy_system.times.ids:
        load_shifting.set_value(t, value(var[s.key, h.key, e.key,
                                             t.key_as_int],
                                         exception=False))
    add_to_df_ts_cl(df_ts_hor, df_ts_cl, energy_system.times,
        ENTRY_LOADSHIFTING, load_shifting, unit="kW", stage=s.key, hub=h.key,
        ec=e.key, source=SOURCE, in_res="result")

    # Above-peak
    var = getattr(model, load_shifting_model.VAR_LOADSHIFTINGABOVEPEAK)
    above_peak = value(var[s.key, h.key, e.key], exception=False)
    add_to_df_st(df_st, ENTRY_LOADSHIFTINGABOVEPEAK, above_peak,
                 unit="kW", stage=s.key, hub=h.key, ec=e.key,
                 source=SOURCE, in_res="result")

    # Below-peak
    var = getattr(model, load_shifting_model.VAR_LOADSHIFTINGBELOWPEAK)
    below_peak = value(var[s.key, h.key, e.key], exception=False)
    add_to_df_st(df_st, ENTRY_LOADSHIFTINGBELOWPEAK, below_peak, unit="kW",
                 stage=s.key, hub=h.key, ec=e.key, source=SOURCE,
                 in_res="result")

    # YLoadShifting
    if (s.key, h.key, e.key) in getattr(model,
            load_shifting_model.SET_LOADSHIFTINGTUPLEFIX):
        var = getattr(model, load_shifting_model.VAR_YLOADHSHIFTING)
        y_load_shifting = TimeSeries()
        for t in energy_system.times.ids:
            y_load_shifting.set_value(t, value(var[s.key, h.key, e.key,
                                                t.key_as_int],
                                            exception=False))
        add_to_df_ts_cl(df_ts_hor, df_ts_cl, energy_system.times,
                        ENTRY_YLOADSHIFTING, y_load_shifting, stage=s.key,
                        hub=h.key, ec=e.key, source=SOURCE, in_res="result")

    # Energy cost
    var = getattr(model, load_shifting_model.VAR_LOADHSHIFTINGCOSTENERGY)
    energy_cost = value(var[s.key, h.key, e.key], exception=False)
    add_to_df_st(df_st, ENTRY_LOADSHIFTINGCOSTENERGY, energy_cost,
                 unit="CHF", stage=s.key, hub=h.key, ec=e.key,
                 source=SOURCE, in_res="result")

    # Peak cost
    var = getattr(model, load_shifting_model.VAR_LOADHSHIFTINGCOSTPEAK)
    peak_cost = value(var[s.key, h.key, e.key], exception=False)
    add_to_df_st(df_st, ENTRY_LOADSHIFTINGCOSTPEAK, peak_cost, unit="CHF",
                 stage=s.key, hub=h.key, ec=e.key, source=SOURCE,
                 in_res="result")

    # Fix cost
    if (s.key, h.key, e.key) in getattr(model,
            load_shifting_model.SET_LOADSHIFTINGTUPLEFIX):
        var = getattr(model, load_shifting_model.VAR_LOADHSHIFTINGCOSTFIX)
        fix_cost = value(var[s.key, h.key, e.key], exception=False)
        add_to_df_st(df_st, ENTRY_LOADSHIFTINGCOSTFIX, fix_cost, unit="CHF",
                     stage=s.key, hub=h.key, ec=e.key, source=SOURCE,
                     in_res="result")


def write_time_series(load_shifting: LoadShifting, times: Times,
                      dir_path: str) -> None:
    """
    Writes all time series with actual data (def_value is not enough) in a
    Demands data object to a dedicated csv file in a directory

    :param load_shifting: The load shifting data object whose time series are
        to be written
    :type load_shifting: LoadShifting
    :param times: Times data object
    :type times: Times
    :param dir_path: Path where the csv file will be placed
    :type dir_path: str
    """
    # Create directory if it does not exist
    if not os.path.isdir(dir_path):
        if not create_dir(dir_path):
            raise exceptions.EhubXException(
                "Could not write load shifting time series data because "
                "the directory could not be created", module=LOG_MODULE_STR)

    # Gather time series
    data: Dict[Tuple[str, str], List[float]] = {}
    for (kind, stage, _, series) in load_shifting.time_series:
        # Skip series without values
        if not series.has_values:
            continue
        if kind == TimeSeriesKind.LOADSHIFTMAXABOVEABS:
            data[stage.key, YAMLKEY_MAXABOVEABS] = [
                series.get_value(t) for t in times.ids_in_order]
        if kind == TimeSeriesKind.LOADSHIFTMAXABOVEREL:
            data[stage.key, YAMLKEY_MAXABOVEREL] = [
                series.get_value(t) for t in times.ids_in_order]
        if kind == TimeSeriesKind.LOADSHIFTMAXBELOWABS:
            data[stage.key, YAMLKEY_MAXBELOWABS] = [
                series.get_value(t) for t in times.ids_in_order]
        if kind == TimeSeriesKind.LOADSHIFTMAXBELOWREL:
            data[stage.key, YAMLKEY_MAXBELOWREL] = [
                series.get_value(t) for t in times.ids_in_order]
        if kind == TimeSeriesKind.LOADSHIFTENERGYCOSTABOVE:
            data[stage.key, YAMLKEY_ENERGYCOSTABOVE] = [
                series.get_value(t) for t in times.ids_in_order]
        if kind == TimeSeriesKind.LOADSHIFTENERGYCOSTBELOW:
            data[stage.key, YAMLKEY_ENERGYCOSTBELOW] = [
                series.get_value(t) for t in times.ids_in_order]
        if kind == TimeSeriesKind.LOADSHIFTFIXCOST:
            data[stage.key, YAMLKEY_FIXCOST] = [
                series.get_value(t) for t in times.ids_in_order]

    # Write demands file
    if data:
        df = pd.DataFrame(data)
        df.columns.names = [HeaderId.LOADSHIFTID.value,
                            HeaderId.PROFILEKEY.value]
        df.index += 1
        df.to_csv(os.path.join(dir_path, FILENAME_TIMESERIES_LOADSHIFTING))
