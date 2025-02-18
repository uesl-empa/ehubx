"""Storage technology writer module. Writes out information from the
storage technology submodule to files"""
from typing import Optional
import pandas as pd
from pyomo.core import Model, value
from ehubx.data.tech_data import TechId
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.time_series import TimeSeries
from ehubx.model import stor_tech_model
from ehubx.writer.common_writer import add_to_df_st, \
    add_to_df_ts_cl, add_to_df_ts_hor

# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "writ/stor_tech"
"""String identifying the storage technology writer module for logging
purposes"""

SOURCE: str = "stor_tech"
"""Display name for the storage tech module in result files"""

ENTRY_EC: str = "Stored ec"
"""Entry name for storage ec in result files"""

ENTRY_INEFF: str = "Input efficiency (in_eff)"
"""Entry name for storage input parameter 'in_eff' in result files"""

ENTRY_OUTEFF: str = "Output efficiency (out_eff)"
"""Entry name for storage input parameter 'out_eff' in result files"""

ENTRY_CHARGEMAX: str = "Maximal charging speed (charge_max)"
"""Entry name for storage input parameter 'charge_max' in result files"""

ENTRY_DISCHARGEMAX: str = "Maximal discharging speed (discharge_max)"
"""Entry name for storage input parameter 'discharge_max' in result files"""

ENTRY_STANDBYLOSS: str = "Standby loss (standy_loss)"
"""Entry name for storage input parameter 'standby_loss' in result files"""

ENTRY_SOCMIN: str = "Minimal SOC (soc_min)"
"""Entry name for storage input parameter 'soc_min' in result files"""

ENTRY_SOCMAX: str = "Maximal SOC (soc_max)"
"""Entry name for storage input parameter 'soc_max' in result files"""

ENTRY_SOCINIT: str = "Initial SOC (soc_init)"
"""Entry name for storage input parameter 'soc_init' in result files"""

ENTRY_INFLOW: str = \
    f"Storage inflow ({stor_tech_model.VAR_STORTECHINFLOW})"
"""Entry name for storage inflow variable in result files"""

ENTRY_OUTFLOW: str = \
    f"Storage outflow ({stor_tech_model.VAR_STORTECHOUTFLOW})"
"""Entry name for storage outflow variable in result files"""

ENTRY_ENERGY: str = \
    f"Storage energy ({stor_tech_model.VAR_STORTECHENERGY})"
"""Entry name for storage energy variable in result files"""


def format_all(energy_system: EnergySystem, model: Model, df_st: pd.DataFrame,
               df_ts_hor: pd.DataFrame, df_ts_cl: Optional[pd.DataFrame]
               ) -> None:
    # Tech-specific properties
    for tech_id in energy_system.stor_techs.ids_in_order:
        _format_tech(energy_system, model, tech_id, df_st, df_ts_hor, df_ts_cl)


def _format_tech(energy_system: EnergySystem, model: Model, x: TechId,
                 df_st: pd.DataFrame, df_ts_hor: pd.DataFrame,
                 df_ts_cl: Optional[pd.DataFrame]) -> None:
    # ec
    ec = energy_system.stor_techs.get_ec(x)
    add_to_df_st(df_st, ENTRY_EC, ec.key, tech=x.key, source=SOURCE,
                 in_res="input")

    # in_eff
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        in_eff = energy_system.stor_techs.get_in_eff(s, x)
        add_to_df_st(df_st, ENTRY_INEFF, in_eff, unit="1", stage=s.key,
                     tech=x.key, source=SOURCE, in_res="input")

    # out_eff
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        out_eff = energy_system.stor_techs.get_out_eff(s, x)
        add_to_df_st(df_st, ENTRY_OUTEFF, out_eff, unit="1", stage=s.key,
                     tech=x.key, source=SOURCE, in_res="input")

    # charge_max
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        charge_max = energy_system.stor_techs.get_charge_max(s, x)
        add_to_df_st(df_st, ENTRY_CHARGEMAX, charge_max, unit="kW",
                     stage=s.key, tech=x.key, source=SOURCE, in_res="input")

    # discharge_max
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        discharge_max = energy_system.stor_techs.get_discharge_max(s, x)
        add_to_df_st(df_st, ENTRY_DISCHARGEMAX, discharge_max, unit="kW",
                     stage=s.key, tech=x.key, source=SOURCE, in_res="input")

    # standby_loss
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        standby_loss = energy_system.stor_techs.get_standby_loss(s, x)
        add_to_df_st(df_st, ENTRY_STANDBYLOSS, standby_loss, unit="1",
                     stage=s.key, tech=x.key, source=SOURCE, in_res="input")

    # soc_min
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        soc_min = energy_system.stor_techs.get_soc_min(s, x)
        add_to_df_st(df_st, ENTRY_SOCMIN, soc_min, unit="1", stage=s.key,
                     tech=x.key, source=SOURCE, in_res="input")

    # soc_max
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        soc_max = energy_system.stor_techs.get_soc_max(s, x)
        add_to_df_st(df_st, ENTRY_SOCMAX, soc_max, unit="1", stage=s.key,
                     tech=x.key, source=SOURCE, in_res="input")

    # soc_init
    for h in energy_system.hubs.ids_in_order:
        if h not in energy_system.techs.get_allowed_hubs(x):
            continue
        soc_init = energy_system.stor_techs.get_soc_init(h, x)
        add_to_df_st(df_st, ENTRY_SOCMAX, soc_init, unit="1", hub=h.key,
                     tech=x.key, source=SOURCE, in_res="input")

    # Storage inflow
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, stor_tech_model.VAR_STORTECHINFLOW)
            inflow = TimeSeries()
            for t in energy_system.times.ids:
                inflow.set_value(t, value(var[s.key, h.key, x.key,
                                              t.key_as_int],
                                          exception=False))
            add_to_df_ts_cl(df_ts_hor, df_ts_cl,
                energy_system.times, ENTRY_INFLOW, inflow, unit="kW",
                stage=s.key, hub=h.key, tech=x.key, source=SOURCE,
                in_res="result")

    # Storage outflow
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, stor_tech_model.VAR_STORTECHOUTFLOW)
            outflow = TimeSeries()
            for t in energy_system.times.ids:
                outflow.set_value(t, value(var[s.key, h.key, x.key,
                                               t.key_as_int],
                                           exception=False))
            add_to_df_ts_cl(df_ts_hor, df_ts_cl,
                energy_system.times, ENTRY_OUTFLOW, outflow, unit="kW",
                stage=s.key, hub=h.key, tech=x.key, source=SOURCE,
                in_res="result")

    # Storage energy
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, stor_tech_model.VAR_STORTECHENERGY)
            energy = TimeSeries()
            for t in energy_system.times.ids_horizon:
                energy.set_value(t, value(var[s.key, h.key, x.key,
                                              t.key_as_int],
                                          exception=False))
            add_to_df_ts_hor(df_ts_hor, energy_system.times,
                ENTRY_ENERGY, energy, unit="kWh", stage=s.key, hub=h.key,
                tech=x.key, source=SOURCE, in_res="result")
