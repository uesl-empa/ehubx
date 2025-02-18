"""Heatpump technology writer module. Writes out information from the heatpump
technology submodule to files"""
import os
from typing import Dict, List, Optional, Tuple
import pandas as pd
from pyomo.core import Model, value
from ehubx.core.common import TimeSeriesKind
from ehubx.core import exceptions
from ehubx.parser.hp_tech_parser import YAMLKEY_COP, YAMLKEY_TEMPHEATIN, \
    YAMLKEY_TEMPHEATOUT
from ehubx.parser.csv_parser import HeaderId
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.tech_data import TechId
from ehubx.data.hp_tech_data import HeatpumpTechs
from ehubx.data.time_data import Times
from ehubx.data.time_series import TimeSeries
from ehubx.model import hp_tech_model
from ehubx.writer.common_writer import create_dir, add_to_df_st, \
    add_to_df_ts_cl

# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "writ/hp_tech"
"""String identifying the heat pump technology writer module for logging
purposes"""

FILENAME_TIMESERIES_HPTECHS: str = "hp_techs.csv"
"""Filename for heatpump technology time series"""

SOURCE: str = "hp_tech"
"""Display name for the heat pump tech module in result files"""

ENTRY_ECEL: str = "Electricity ec (ec_el)"
"""Entry name for electricity ec in result files"""

ENTRY_ECHTIN: str = "Input heating ec, evaporator (ec_ht_in)"
"""Entry name for input heating ec (evaporator side) in result files"""

ENTRY_ECHTOUT: str = "Output heating ec, condenser (ec_ht_out)"
"""Entry name for output heating ec (condenser side) in result files"""

ENTRY_ECCOIN: str = "Input cooling ec, condenser (ec_co_in)"
"""Entry name for input cooling ec (condenser side) in result files"""

ENTRY_ECCOOUT: str = "Output cooling ec, evaporator (ec_co_out)"
"""Entry name for output cooling ec (evaporator side) in result files"""

ENTRY_TEMPHTIN: str = "Input heating temperature, evaporator (temp_ht_in)"
"""Entry name for input heating temperature (evaporator side) in result
files"""

ENTRY_TEMPHTOUT: str = "Output heating temperature, condenser (temp_ht_out)"
"""Entry name for output heating temperature (condenser side) in result
files"""

ENTRY_COPFACTOR: str = "COP calculation factor (cop_factor)"
"""Entry name for COP calculation factor (to Carnot efficiency) in result
files"""

ENTRY_COP: str = "Coefficient of Performance (cop)"
"""Entry name for coefficient of Performance in result files"""

ENTRY_HPTECHIN: str = f"HP tech input ({hp_tech_model.VAR_HPTECHIN})"
"""Entry name for heat pump tech input variable in result files"""

ENTRY_HPTECHOUT: str = f"HP tech output ({hp_tech_model.VAR_HPTECHOUT})"
"""Entry name for heat pump tech output variable in result files"""

ENTRY_HPTECHELECHT: str = ("HP tech electricity consumption in heating mode "
                           f"({hp_tech_model.VAR_HPTECHELECHT})")
"""Entry name for heat pump tech electricity consumption variable in heating
mode in result files"""

ENTRY_HPTECHELECCO: str = ("HP tech electricity consumption in cooling mode "
                           f"({hp_tech_model.VAR_HPTECHELECCO})")
"""Entry name for heat pump tech electricity consumption variable in cooling
mode in result files"""


def format_all(energy_system: EnergySystem, model: Model, df_st: pd.DataFrame,
               df_ts_hor: pd.DataFrame, df_ts_cl: Optional[pd.DataFrame]
               ) -> None:
    # Tech-specific properties
    for tech_id in energy_system.hp_techs.ids_in_order:
        _format_tech(energy_system, model, tech_id, df_st, df_ts_hor, df_ts_cl)


def _format_tech(energy_system: EnergySystem, model: Model, x: TechId,
                 df_st: pd.DataFrame, df_ts_hor: pd.DataFrame,
                 df_ts_cl: Optional[pd.DataFrame]) -> None:
    # ec_el
    ec_el = energy_system.hp_techs.get_ec_el(x)
    add_to_df_st(df_st, ENTRY_ECEL, ec_el.key, tech=x.key, source=SOURCE,
                 in_res="input")

    # ec_ht_in
    ec_ht_in = energy_system.hp_techs.get_ec_ht_in(x)
    add_to_df_st(df_st, ENTRY_ECHTIN, ec_ht_in.key, tech=x.key, source=SOURCE,
                 in_res="input")

    # ec_ht_out
    ec_ht_out = energy_system.hp_techs.get_ec_ht_out(x)
    add_to_df_st(df_st, ENTRY_ECHTOUT, ec_ht_out.key, tech=x.key,
                 source=SOURCE, in_res="input")

    # ec_co_in
    ec_co_in = energy_system.hp_techs.get_ec_co_in(x)
    add_to_df_st(df_st, ENTRY_ECCOIN, ec_co_in.key, tech=x.key, source=SOURCE,
                 in_res="input")

    # ec_co_out
    ec_co_out = energy_system.hp_techs.get_ec_co_out(x)
    add_to_df_st(df_st, ENTRY_ECCOOUT, ec_co_out.key, tech=x.key,
                 source=SOURCE, in_res="input")

    # temp_ht_in
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            if not energy_system.hp_techs.has_temp_ht_in(s, h, x):
                continue
            temp_ht_in = energy_system.hp_techs.get_temp_ht_in(s, h, x)
            if temp_ht_in.has_values:
                add_to_df_ts_cl(df_ts_hor, df_ts_cl,
                    energy_system.times, ENTRY_TEMPHTIN, temp_ht_in,
                    unit="°C", stage=s.key, hub=h.key, tech=x.key,
                    source=SOURCE, in_res="input")
            if not temp_ht_in.has_values:
                temp_ht_in_def = temp_ht_in.def_value
                assert temp_ht_in_def is not None
                add_to_df_st(df_st, ENTRY_TEMPHTIN, temp_ht_in_def, unit="°C",
                             stage=s.key, hub=h.key, tech=x.key,
                             source=SOURCE, in_res="input")

    # temp_ht_out
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            if not energy_system.hp_techs.has_temp_ht_out(s, h, x):
                continue
            temp_ht_out = energy_system.hp_techs.get_temp_ht_out(s, h, x)
            if temp_ht_out.has_values:
                add_to_df_ts_cl(df_ts_hor, df_ts_cl,
                    energy_system.times, ENTRY_TEMPHTOUT, temp_ht_out,
                    unit="°C", stage=s.key, hub=h.key, tech=x.key,
                    source=SOURCE, in_res="input")
            if not temp_ht_out.has_values:
                temp_ht_out_def = temp_ht_out.def_value
                assert temp_ht_out_def is not None
                add_to_df_st(df_st, ENTRY_TEMPHTOUT, temp_ht_out_def,
                             unit="°C", stage=s.key, hub=h.key, tech=x.key,
                             source=SOURCE, in_res="input")

    # cop_factor
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        if not energy_system.hp_techs.has_cop_factor(s, x):
            continue
        cop_factor = energy_system.hp_techs.get_cop_factor(s, x)
        add_to_df_st(df_st, ENTRY_COPFACTOR, cop_factor, unit="1", stage=s.key,
                     hub=h.key, tech=x.key, source=SOURCE, in_res="input")

    # cop
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            cop = energy_system.hp_techs.get_cop(s, h, x, energy_system.times)
            if cop.has_values:
                add_to_df_ts_cl(df_ts_hor, df_ts_cl,
                    energy_system.times, ENTRY_COP, cop, unit="1", stage=s.key,
                    hub=h.key, tech=x.key, source=SOURCE, in_res="input")
            if not cop.has_values:
                cop_def = cop.def_value
                assert cop_def is not None
                add_to_df_st(df_st, ENTRY_COP, cop_def, unit="1", stage=s.key,
                             hub=h.key, tech=x.key, source=SOURCE,
                             in_res="input")

    # HP input
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            for e in (energy_system.hp_techs.get_ec_el(x),
                      energy_system.hp_techs.get_ec_ht_in(x),
                      energy_system.hp_techs.get_ec_co_in(x)):
                var = getattr(model, hp_tech_model.VAR_HPTECHIN)
                hp_in = TimeSeries()
                for t in energy_system.times.ids:
                    hp_in.set_value(t, value(var[s.key, h.key, x.key, e.key,
                                                 t.key_as_int],
                                             exception=False))
                add_to_df_ts_cl(df_ts_hor, df_ts_cl,
                    energy_system.times, ENTRY_HPTECHIN, hp_in, unit="kW",
                    stage=s.key, hub=h.key, tech=x.key, ec=e.key,
                    source=SOURCE, in_res="result")

    # HP output
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            for e in (energy_system.hp_techs.get_ec_ht_out(x),
                      energy_system.hp_techs.get_ec_co_out(x)):
                var = getattr(model, hp_tech_model.VAR_HPTECHOUT)
                hp_out = TimeSeries()
                for t in energy_system.times.ids:
                    hp_out.set_value(t, value(var[s.key, h.key, x.key, e.key,
                                                  t.key_as_int],
                                              exception=False))
                add_to_df_ts_cl(df_ts_hor, df_ts_cl,
                    energy_system.times, ENTRY_HPTECHOUT, hp_out, unit="kW",
                    stage=s.key, hub=h.key, tech=x.key, ec=e.key,
                    source=SOURCE, in_res="result")

    # HP electricity consumption in heating mode
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, hp_tech_model.VAR_HPTECHELECHT)
            hp_elec_ht = TimeSeries()
            for t in energy_system.times.ids:
                hp_elec_ht.set_value(t, value(var[s.key, h.key, x.key,
                                                  t.key_as_int],
                                              exception=False))
            add_to_df_ts_cl(df_ts_hor, df_ts_cl,
                energy_system.times, ENTRY_HPTECHELECHT, hp_elec_ht, unit="kW",
                stage=s.key, hub=h.key, tech=x.key, source=SOURCE,
                in_res="result")

    # HP electricity consumption in cooling mode
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, hp_tech_model.VAR_HPTECHELECCO)
            hp_elec_co = TimeSeries()
            for t in energy_system.times.ids:
                hp_elec_co.set_value(t, value(var[s.key, h.key, x.key,
                                                  t.key_as_int],
                                              exception=False))
            add_to_df_ts_cl(df_ts_hor, df_ts_cl,
                energy_system.times, ENTRY_HPTECHELECCO, hp_elec_co, unit="kW",
                stage=s.key, hub=h.key, tech=x.key, source=SOURCE,
                in_res="result")


def write_data_time_series(hp_techs: HeatpumpTechs, times: Times,
                           dir_path: str) -> None:
    """
    Writes all time series with actual data (def_value is not enough) in a
    heatpump technology data object to a dedicated csv file in a directory

    :param hp_techs: The heatpump technology  data object whose time series are
        to be written
    :type hp_techs: Demands
    :param times: Times data object
    :type times: Times
    :param dir_path: Path where the csv file will be placed
    :type dir_path: str
    """
    # Create directory if it does not exist
    if not os.path.isdir(dir_path):
        if not create_dir(dir_path):
            raise exceptions.EhubXException(
                "Could not write heatpump tech time series data because "
                "the directory could not be created", module=LOG_MODULE_STR)

    # Gather time series
    data: Dict[Tuple[str, str, str, str], List[float]] = {}
    for (kind, stage, ids, series) in hp_techs.time_series:
        # Skip series without values
        if not series.has_values:
            continue
        if kind == TimeSeriesKind.HPTECHCOP:
            data[stage.key, ids[0], ids[1], YAMLKEY_COP] = [
                series.get_value(t) for t in times.ids_in_order]
        if kind == TimeSeriesKind.HPTECHTEMPHTIN:
            data[stage.key, ids[0], ids[1], YAMLKEY_TEMPHEATIN] = [
                series.get_value(t) for t in times.ids_in_order]
        if kind == TimeSeriesKind.HPTECHTEMPHTOUT:
            data[stage.key, ids[0], ids[1], YAMLKEY_TEMPHEATOUT] = [
                series.get_value(t) for t in times.ids_in_order]

    # Write demands file
    if data:
        df = pd.DataFrame(data)
        df.columns.names = [HeaderId.STAGEID.value, HeaderId.HUBID.value,
                            HeaderId.TECHID.value, HeaderId.PROFILEKEY.value]
        df.index += 1
        df.to_csv(os.path.join(dir_path, FILENAME_TIMESERIES_HPTECHS))
