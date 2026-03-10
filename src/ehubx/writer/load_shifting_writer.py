"""Load shifting writer module. Writes out information from the load shifting
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
from ehubx.data.load_shifting_data import LoadShiftId
from ehubx.data.stage_data import StageId
from ehubx.data.time_series import TimeSeries
from ehubx.data.unit import CurrencyUnit, DimlessUnit, TimeUnit
from ehubx.data.value import Value
from ehubx.model import ec_model, load_shifting_model
from ehubx.parser.csv_parser import HeaderId
from ehubx.parser.load_shifting_parser import (
    YAMLKEY_ENERGYCOSTABOVE,
    YAMLKEY_ENERGYCOSTBELOW,
    YAMLKEY_FIXCOST,
    YAMLKEY_MAXABOVEABS,
    YAMLKEY_MAXABOVEREL,
    YAMLKEY_MAXBELOWABS,
    YAMLKEY_MAXBELOWREL,
)
from ehubx.writer.common_writer import DfStBuilder, add_to_df_ts_cl, create_dir


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

ENTRY_CAPMIN: str = "Minimal load shifting capacity (cap_min)"
"""Entry name for load shifting parameter 'cap_min' in result files"""

ENTRY_CAPMAX: str = "Maximal load shifting capacity (cap_max)"
"""Entry name for load shifting parameter 'cap_max' in result files"""

ENTRY_CAPINIT: str = "Initial load shifting capacity (cap_init)"
"""Entry name for load shifting parameter 'cap_init' in result files"""

ENTRY_MAXABOVEABS: str = "Maximal absolute above-shifting (max_above_abs)"
"""Entry name for load shifting parameter 'max_above_abs' in result files"""

ENTRY_MAXABOVEREL: str = "Maximal relative above-shifting (max_above_rel)"
"""Entry name for load shifting parameter 'max_above_rel' in result files"""

ENTRY_MAXBELOWABS: str = "Maximal absolute below-shifting (max_below_abs)"
"""Entry name for load shifting parameter 'max_below_abs' in result files"""

ENTRY_MAXBELOWREL: str = "Maximal relative below-shifting (max_below_rel)"
"""Entry name for load shifting parameter 'max_below_rel' in result files"""

ENTRY_CAPEXPERCAP: str = "CAPEX cost for capacity installation (capex_per_cap)"
"""Entry name for load shifting parameter 'capex_per_cap' in result files"""

ENTRY_PEAKCOSTABOVE: str = "Peak cost for above-shifting (peak_cost_above)"
"""Entry name for load shifting parameter 'peak_cost_above' in result files"""

ENTRY_PEAKCOSTBELOW: str = "Peak cost for below-shifting (peak_cost_below)"
"""Entry name for load shifting parameter 'peak_cost_below' in result files"""

ENTRY_ENERGYCOSTABOVE: str = "Energy cost for above-shifting (energy_cost_above)"
"""Entry name for load shifting parameter 'energy_cost_above' in result
files"""

ENTRY_ENERGYCOSTBELOW: str = "Energy cost for below-shifting (energy_cost_below)"
"""Entry name for load shifting parameter 'energy_cost_below' in result
files"""

ENTRY_FIXCOST: str = "Fix cost for load shifting (fix_cost)"
"""Entry name for load shifting parameter 'fix_cost' in result files"""

ENTRY_LOADSHIFTINGCAP: str = (
    f"Load shifting capacity ({load_shifting_model.VAR_LOADSHIFTINGCAP})"
)
"""Entry name for load shifting capacity variable in result files"""

ENTRY_LOADSHIFTINGCAPINSTL: str = (
    "Load shifting capacity installation "
    f"({load_shifting_model.VAR_LOADSHIFTINGCAPINSTL})"
)
"""Entry name for load shifting capacity installation variable in result files"""

ENTRY_LOADSHIFTING: str = f"Load shifting ({load_shifting_model.VAR_LOADSHIFTING})"
"""Entry name for load shifting variable in result files"""

ENTRY_LOADSHIFTINGABOVEPEAK: str = (
    f"Load shifting above-peak ({load_shifting_model.VAR_LOADSHIFTINGABOVEPEAK})"
)
"""Entry name for load shifting above-peak variable in result files"""

ENTRY_LOADSHIFTINGBELOWPEAK: str = (
    f"Load shifting below-peak ({load_shifting_model.VAR_LOADSHIFTINGBELOWPEAK})"
)
"""Entry name for load shifting above-peak variable in result files"""

ENTRY_LOADSHIFTINGCOSTCAPEX: str = (
    f"Load shifting CAPEX cost ({load_shifting_model.VAR_LOADSHIFTINGCOSTCAPEX})"
)
"""Entry name for load shifting CAPEX cost variable in result files"""

ENTRY_LOADSHIFTINGCOSTENERGY: str = (
    f"Load shifting energy cost ({load_shifting_model.VAR_LOADSHIFTINGCOSTENERGY})"
)
"""Entry name for load shifting energy cost variable in result files"""

ENTRY_LOADSHIFTINGCOSTPEAK: str = (
    f"Load shifting peak cost ({load_shifting_model.VAR_LOADSHIFTINGCOSTPEAK})"
)
"""Entry name for load shifting peak cost variable in result files"""

ENTRY_LOADSHIFTINGCOSTFIX: str = (
    f"Load shifting fix cost ({load_shifting_model.VAR_LOADSHIFTINGCOSTFIX})"
)
"""Entry name for load shifting fixed cost variable in result files"""

ENTRY_LOADSHIFTINGCOSTTOTAL: str = (
    f"Load shifting total cost ({load_shifting_model.VAR_LOADSHIFTINGCOSTTOTAL})"
)
"""Entry name for load shifting total cost variable in result files"""

ENTRY_YLOADSHIFTING: str = (
    f"Any load shifting? ({load_shifting_model.VAR_YLOADSHIFTING})"
)
"""Entry name for binary load shifting monitoring variable in result files"""


def format_all(
    energy_system: EnergySystem,
    model: Model,
    df_st_builder: DfStBuilder,
    df_ts_hor: pd.DataFrame,
    df_ts_cl: Optional[pd.DataFrame],
) -> None:
    # Total cost
    var = getattr(model, load_shifting_model.VAR_LOADSHIFTINGCOSTTOTAL)
    total_cost_fl = value(var, exception=False)
    if total_cost_fl is not None:
        total_cost = Value(total_cost_fl, unit=energy_system.currency_unit)
        df_st_builder.add_row(
            ENTRY_LOADSHIFTINGCOSTTOTAL,
            total_cost,
            unit=energy_system.currency_unit,
            source=SOURCE,
            in_res="result",
        )

    # Id-and-tuple-specific values
    for ls in energy_system.load_shifting.ids:
        e = energy_system.load_shifting.get_ec(ls)
        for s, h in energy_system.load_shifting.get_stage_hub_tuples(ls):
            _format_ls_and_tuple(
                energy_system, model, ls, s, h, e, df_st_builder, df_ts_hor, df_ts_cl
            )

    # Tuple-specific values
    for s_, h_, e_ in getattr(model, load_shifting_model.SET_LOADSHIFTINGTUPLES):
        _format_tuple(
            energy_system,
            model,
            StageId(s_),
            HubId(h_),
            EcId(e_),
            df_ts_hor,
            df_ts_cl,
        )


def _format_ls_and_tuple(
    energy_system: EnergySystem,
    model: Model,
    ls: LoadShiftId,
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
    # interval_length
    interval_length = energy_system.load_shifting.get_interval_length(ls)
    interval_length_unit = TimeUnit.H
    df_st_builder.add_row(
        ENTRY_INTERVALLENGTH,
        interval_length,
        unit=interval_length_unit,
        load_shift=ls.key,
        stage=s.key,
        hub=h.key,
        ec=e.key,
        source=SOURCE,
        in_res="input",
    )

    # cap_min
    cap_min = energy_system.load_shifting.get_cap_min(ls)
    df_st_builder.add_row(
        ENTRY_CAPMIN,
        cap_min,
        unit=ec_unit,
        load_shift=ls.key,
        stage=s.key,
        hub=h.key,
        ec=e.key,
        source=SOURCE,
        in_res="input",
    )

    # cap_max
    cap_max = energy_system.load_shifting.get_cap_max(ls)
    df_st_builder.add_row(
        ENTRY_CAPMAX,
        cap_max,
        unit=ec_unit,
        load_shift=ls.key,
        stage=s.key,
        hub=h.key,
        ec=e.key,
        source=SOURCE,
        in_res="input",
    )

    # cap_init
    cap_init = energy_system.load_shifting.get_cap_init(ls)
    df_st_builder.add_row(
        ENTRY_CAPINIT,
        cap_init,
        unit=ec_unit,
        load_shift=ls.key,
        stage=s.key,
        hub=h.key,
        ec=e.key,
        source=SOURCE,
        in_res="input",
    )

    # max_above_abs
    max_above_abs = energy_system.load_shifting.get_max_above_abs(ls)
    max_abs_unit = ec_unit / TimeUnit.H
    if max_above_abs.has_values:
        add_to_df_ts_cl(
            df_ts_hor,
            df_ts_cl,
            energy_system.times,
            ENTRY_MAXABOVEABS,
            max_above_abs,
            max_abs_unit,
            load_shift=ls.key,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )
    if not max_above_abs.has_values:
        max_above_abs_def = max_above_abs.def_value
        assert max_above_abs_def is not None
        df_st_builder.add_row(
            ENTRY_MAXABOVEABS,
            max_above_abs_def,
            unit=max_abs_unit,
            load_shift=ls.key,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )

    # max_above_rel
    max_above_rel = energy_system.load_shifting.get_max_above_rel(ls)
    max_abovebelow_rel_unit = DimlessUnit()
    if max_above_rel.has_values:
        add_to_df_ts_cl(
            df_ts_hor,
            df_ts_cl,
            energy_system.times,
            ENTRY_MAXABOVEREL,
            max_above_rel,
            max_abovebelow_rel_unit,
            load_shift=ls.key,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )
    if not max_above_rel.has_values:
        max_above_rel_def = max_above_rel.def_value
        assert max_above_rel_def is not None
        df_st_builder.add_row(
            ENTRY_MAXABOVEREL,
            max_above_rel_def,
            unit=max_abovebelow_rel_unit,
            load_shift=ls.key,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )

    # max_below_abs
    max_below_abs = energy_system.load_shifting.get_max_below_abs(ls)
    if max_below_abs.has_values:
        add_to_df_ts_cl(
            df_ts_hor,
            df_ts_cl,
            energy_system.times,
            ENTRY_MAXBELOWABS,
            max_below_abs,
            max_abs_unit,
            load_shift=ls.key,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )
    if not max_below_abs.has_values:
        max_below_abs_def = max_below_abs.def_value
        assert max_below_abs_def is not None
        df_st_builder.add_row(
            ENTRY_MAXBELOWABS,
            max_below_abs_def,
            unit=max_abs_unit,
            load_shift=ls.key,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )

    # max_below_rel
    max_below_rel = energy_system.load_shifting.get_max_below_rel(ls)
    if max_below_rel.has_values:
        add_to_df_ts_cl(
            df_ts_hor,
            df_ts_cl,
            energy_system.times,
            ENTRY_MAXBELOWREL,
            max_below_rel,
            max_abovebelow_rel_unit,
            load_shift=ls.key,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )
    if not max_below_rel.has_values:
        max_below_rel_def = max_below_rel.def_value
        assert max_below_rel_def is not None
        df_st_builder.add_row(
            ENTRY_MAXBELOWREL,
            max_below_rel_def,
            unit=max_abovebelow_rel_unit,
            load_shift=ls.key,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )

    # capex_per_cap
    capex_per_cap = energy_system.load_shifting.get_capex_per_cap(ls)
    capex_per_cap_unit = CurrencyUnit.CHF / ec_unit
    df_st_builder.add_row(
        ENTRY_CAPEXPERCAP,
        capex_per_cap,
        unit=capex_per_cap_unit,
        load_shift=ls.key,
        stage=s.key,
        hub=h.key,
        ec=e.key,
        source=SOURCE,
        in_res="input",
    )

    # peak_cost_above
    peak_cost_above = energy_system.load_shifting.get_peak_cost_above(ls)
    peak_cost_unit = energy_system.currency_unit / (ec_unit / TimeUnit.H)
    df_st_builder.add_row(
        ENTRY_PEAKCOSTABOVE,
        peak_cost_above,
        unit=peak_cost_unit,
        load_shift=ls.key,
        stage=s.key,
        hub=h.key,
        ec=e.key,
        source=SOURCE,
        in_res="input",
    )

    # peak_cost_below
    peak_cost_below = energy_system.load_shifting.get_peak_cost_below(ls)
    df_st_builder.add_row(
        ENTRY_PEAKCOSTBELOW,
        peak_cost_below,
        unit=peak_cost_unit,
        load_shift=ls.key,
        stage=s.key,
        hub=h.key,
        ec=e.key,
        source=SOURCE,
        in_res="input",
    )

    # energy_cost_above
    energy_cost_above = energy_system.load_shifting.get_energy_cost_above(ls)
    energy_cost_unit = energy_system.currency_unit / ec_unit
    if energy_cost_above.has_values:
        add_to_df_ts_cl(
            df_ts_hor,
            df_ts_cl,
            energy_system.times,
            ENTRY_ENERGYCOSTABOVE,
            energy_cost_above,
            energy_cost_unit,
            load_shift=ls.key,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )
    if not energy_cost_above.has_values:
        energy_cost_above_def = energy_cost_above.def_value
        assert energy_cost_above_def is not None
        df_st_builder.add_row(
            ENTRY_ENERGYCOSTABOVE,
            energy_cost_above_def,
            unit=energy_cost_unit,
            load_shift=ls.key,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )

    # energy_cost_below
    energy_cost_below = energy_system.load_shifting.get_energy_cost_below(ls)
    if energy_cost_below.has_values:
        add_to_df_ts_cl(
            df_ts_hor,
            df_ts_cl,
            energy_system.times,
            ENTRY_ENERGYCOSTBELOW,
            energy_cost_below,
            energy_cost_unit,
            load_shift=ls.key,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )
    if not energy_cost_below.has_values:
        energy_cost_below_def = energy_cost_below.def_value
        assert energy_cost_below_def is not None
        df_st_builder.add_row(
            ENTRY_ENERGYCOSTBELOW,
            energy_cost_below_def,
            unit=energy_cost_unit,
            load_shift=ls.key,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )

    # fix_cost
    fix_cost = energy_system.load_shifting.get_fix_cost(ls)
    fix_cost_unit = energy_system.currency_unit / TimeUnit.H
    if fix_cost.has_values:
        add_to_df_ts_cl(
            df_ts_hor,
            df_ts_cl,
            energy_system.times,
            ENTRY_FIXCOST,
            fix_cost,
            fix_cost_unit,
            load_shift=ls.key,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )
    if not fix_cost.has_values:
        fix_cost_def = fix_cost.def_value
        assert fix_cost_def is not None
        df_st_builder.add_row(
            ENTRY_FIXCOST,
            fix_cost_def,
            unit=fix_cost_unit,
            load_shift=ls.key,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            source=SOURCE,
            in_res="input",
        )

    # Capacity
    var = getattr(model, load_shifting_model.VAR_LOADSHIFTINGCAP)
    cap_fl = value(var[ls.key, s.key, h.key, e.key], exception=False)
    if cap_fl is not None:
        cap = Value(cap_fl, unit=ec_unit)
        df_st_builder.add_row(
            ENTRY_LOADSHIFTINGCAP,
            cap,
            unit=ec_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            load_shift=ls.key,
            source=SOURCE,
            in_res="result",
        )

    # Installed capacity
    var = getattr(model, load_shifting_model.VAR_LOADSHIFTINGCAPINSTL)
    cap_instl_fl = value(var[ls.key, s.key, h.key, e.key], exception=False)
    if cap_instl_fl is not None:
        cap_instl = Value(cap_instl_fl, unit=ec_unit)
        df_st_builder.add_row(
            ENTRY_LOADSHIFTINGCAPINSTL,
            cap_instl,
            unit=ec_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            load_shift=ls.key,
            source=SOURCE,
            in_res="result",
        )

    # Load shifting
    var = getattr(model, load_shifting_model.VAR_LOADSHIFTING)
    load_shifting = TimeSeries()
    shift_unit = ec_unit / TimeUnit.H
    for t in energy_system.times.ids:
        shift_fl = value(
            var[ls.key, s.key, h.key, e.key, t.key_as_int], exception=False
        )
        if shift_fl is not None:
            load_shifting.set_value(t, Value(shift_fl, shift_unit))
    add_to_df_ts_cl(
        df_ts_hor,
        df_ts_cl,
        energy_system.times,
        ENTRY_LOADSHIFTING,
        load_shifting,
        unit=shift_unit,
        stage=s.key,
        hub=h.key,
        ec=e.key,
        load_shift=ls.key,
        source=SOURCE,
        in_res="result",
    )

    # Above-peak
    var = getattr(model, load_shifting_model.VAR_LOADSHIFTINGABOVEPEAK)
    peak_unit = ec_unit / TimeUnit.H
    above_peak_fl = value(var[ls.key, s.key, h.key, e.key], exception=False)
    if above_peak_fl is not None:
        above_peak = Value(above_peak_fl, unit=peak_unit)
        df_st_builder.add_row(
            ENTRY_LOADSHIFTINGABOVEPEAK,
            above_peak,
            unit=peak_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            load_shift=ls.key,
            source=SOURCE,
            in_res="result",
        )

    # Below-peak
    var = getattr(model, load_shifting_model.VAR_LOADSHIFTINGBELOWPEAK)
    below_peak_fl = value(var[ls.key, s.key, h.key, e.key], exception=False)
    if below_peak_fl is not None:
        below_peak = Value(below_peak_fl, unit=peak_unit)
        df_st_builder.add_row(
            ENTRY_LOADSHIFTINGBELOWPEAK,
            below_peak,
            unit=peak_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            load_shift=ls.key,
            source=SOURCE,
            in_res="result",
        )

    # YLoadShifting
    if (ls.key, s.key, h.key, e.key) in getattr(
        model, load_shifting_model.SET_LOADSHIFTINGWITHTUPLESFIX
    ):
        var = getattr(model, load_shifting_model.VAR_YLOADSHIFTING)
        y_load_shifting = TimeSeries()
        for t in energy_system.times.ids:
            y_load_shift_fl = value(
                var[ls.key, s.key, h.key, e.key, t.key_as_int], exception=False
            )
            if y_load_shift_fl is not None:
                y_load_shifting.set_value(t, Value(y_load_shift_fl, DimlessUnit()))
        add_to_df_ts_cl(
            df_ts_hor,
            df_ts_cl,
            energy_system.times,
            ENTRY_YLOADSHIFTING,
            y_load_shifting,
            unit=DimlessUnit(),
            stage=s.key,
            hub=h.key,
            ec=e.key,
            load_shift=ls.key,
            source=SOURCE,
            in_res="result",
        )

    # CAPEX cost
    var = getattr(model, load_shifting_model.VAR_LOADSHIFTINGCOSTCAPEX)
    capex_cost_fl = value(var[ls.key, s.key, h.key, e.key], exception=False)
    if capex_cost_fl is not None:
        capex = Value(capex_cost_fl, energy_system.currency_unit)
        df_st_builder.add_row(
            ENTRY_LOADSHIFTINGCOSTCAPEX,
            capex,
            unit=energy_system.currency_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            load_shift=ls.key,
            source=SOURCE,
            in_res="result",
        )

    # Energy cost
    var = getattr(model, load_shifting_model.VAR_LOADSHIFTINGCOSTENERGY)
    energy_cost_fl = value(var[ls.key, s.key, h.key, e.key], exception=False)
    if energy_cost_fl is not None:
        energy_cost = Value(energy_cost_fl, unit=energy_system.currency_unit)
        df_st_builder.add_row(
            ENTRY_LOADSHIFTINGCOSTENERGY,
            energy_cost,
            unit=energy_system.currency_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            load_shift=ls.key,
            source=SOURCE,
            in_res="result",
        )

    # Peak cost
    var = getattr(model, load_shifting_model.VAR_LOADSHIFTINGCOSTPEAK)
    peak_cost_fl = value(var[ls.key, s.key, h.key, e.key], exception=False)
    if peak_cost_fl is not None:
        peak_cost = Value(peak_cost_fl, unit=energy_system.currency_unit)
        df_st_builder.add_row(
            ENTRY_LOADSHIFTINGCOSTPEAK,
            peak_cost,
            unit=energy_system.currency_unit,
            stage=s.key,
            hub=h.key,
            ec=e.key,
            load_shift=ls.key,
            source=SOURCE,
            in_res="result",
        )

    # Fix cost
    if (ls.key, s.key, h.key, e.key) in getattr(
        model, load_shifting_model.SET_LOADSHIFTINGWITHTUPLESFIX
    ):
        var = getattr(model, load_shifting_model.VAR_LOADSHIFTINGCOSTFIX)
        fix_cost_fl = value(var[ls.key, s.key, h.key, e.key], exception=False)
        if fix_cost_fl is not None:
            fix_cost_pr = Value(fix_cost_fl, unit=energy_system.currency_unit)
            df_st_builder.add_row(
                ENTRY_LOADSHIFTINGCOSTFIX,
                fix_cost_pr,
                unit=energy_system.currency_unit,
                stage=s.key,
                hub=h.key,
                ec=e.key,
                load_shift=ls.key,
                source=SOURCE,
                in_res="result",
            )


def _format_tuple(
    energy_system: EnergySystem,
    model: Model,
    s: StageId,
    h: HubId,
    e: EcId,
    df_ts_hor: pd.DataFrame,
    df_ts_cl: Optional[pd.DataFrame],
) -> None:
    # ec_unit
    ec_unit = ec_model.get_ec_model_unit(
        energy_system.ecs.get_unit(e),
        energy_system.mass_unit,
        energy_system.power_unit,
    )
    # Load shifting total
    var = getattr(model, load_shifting_model.VAR_LOADSHIFTINGTOTAL)
    load_shifting_total = TimeSeries()
    shift_unit = ec_unit / TimeUnit.H
    for t in energy_system.times.ids:
        shift_fl = value(var[s.key, h.key, e.key, t.key_as_int], exception=False)
        if shift_fl is not None:
            load_shifting_total.set_value(t, Value(shift_fl, shift_unit))
    add_to_df_ts_cl(
        df_ts_hor,
        df_ts_cl,
        energy_system.times,
        ENTRY_LOADSHIFTING,
        load_shifting_total,
        unit=shift_unit,
        stage=s.key,
        hub=h.key,
        ec=e.key,
        source=SOURCE,
        in_res="result",
    )


def write_data_time_series(energy_system: EnergySystem, dir_path: str) -> None:
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
                "Could not write load shifting time series data because "
                "the directory could not be created",
                module=LOG_MODULE_STR,
            )

    # Gather time series
    data: Dict[Tuple[str, str, str, str, str, str], List[float]] = {}
    for kind, stage, ids, series in energy_system.load_shifting.time_series:
        # Skip series without values
        if not series.has_values:
            continue
        ec_unit = ec_model.get_ec_model_unit(
            energy_system.ecs.get_unit(EcId(ids[1])),
            energy_system.mass_unit,
            energy_system.power_unit,
        )
        if kind == TimeSeriesKind.LOADSHIFTMAXABOVEABS:
            unit = ec_unit / TimeUnit.H
            data[stage.key, ids[0], ids[1], ids[2], YAMLKEY_MAXABOVEABS, str(unit)] = [
                series.get_value(t).to_float(unit=unit)
                for t in energy_system.times.ids_in_order
            ]
        if kind == TimeSeriesKind.LOADSHIFTMAXABOVEREL:
            unit = DimlessUnit()
            data[stage.key, ids[0], ids[1], ids[2], YAMLKEY_MAXABOVEREL, str(unit)] = [
                series.get_value(t).to_float(unit=unit)
                for t in energy_system.times.ids_in_order
            ]
        if kind == TimeSeriesKind.LOADSHIFTMAXBELOWABS:
            unit = ec_unit / TimeUnit.H
            data[stage.key, ids[0], ids[1], ids[2], YAMLKEY_MAXBELOWABS, str(unit)] = [
                series.get_value(t).to_float(unit=unit)
                for t in energy_system.times.ids_in_order
            ]
        if kind == TimeSeriesKind.LOADSHIFTMAXBELOWREL:
            unit = DimlessUnit()
            data[stage.key, ids[0], ids[1], ids[2], YAMLKEY_MAXBELOWREL, str(unit)] = [
                series.get_value(t).to_float(unit=unit)
                for t in energy_system.times.ids_in_order
            ]
        if kind == TimeSeriesKind.LOADSHIFTENERGYCOSTABOVE:
            unit = energy_system.currency_unit / ec_unit
            data[
                stage.key, ids[0], ids[1], ids[2], YAMLKEY_ENERGYCOSTABOVE, str(unit)
            ] = [
                series.get_value(t).to_float(unit=unit)
                for t in energy_system.times.ids_in_order
            ]
        if kind == TimeSeriesKind.LOADSHIFTENERGYCOSTBELOW:
            unit = energy_system.currency_unit / ec_unit
            data[
                stage.key, ids[0], ids[1], ids[2], YAMLKEY_ENERGYCOSTBELOW, str(unit)
            ] = [
                series.get_value(t).to_float(unit=unit)
                for t in energy_system.times.ids_in_order
            ]
        if kind == TimeSeriesKind.LOADSHIFTFIXCOST:
            unit = energy_system.currency_unit / TimeUnit.H
            data[stage.key, ids[0], ids[1], ids[2], YAMLKEY_FIXCOST, str(unit)] = [
                series.get_value(t).to_float(unit=unit)
                for t in energy_system.times.ids_in_order
            ]

    # Write file
    if data:
        df = pd.DataFrame(data)
        df.columns.names = [
            HeaderId.STAGEID.value,
            HeaderId.HUBID.value,
            HeaderId.ECID.value,
            HeaderId.LOADSHIFTID.value,
            HeaderId.PROFILEKEY.value,
            HeaderId.UNIT.value,
        ]
        df.index += 1
        df.to_csv(os.path.join(dir_path, FILENAME_TIMESERIES_LOADSHIFTING))
