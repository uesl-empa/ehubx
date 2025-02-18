"""EBM technology writer module. Writes out information from the EBM technology
submodule to files"""
import os
from typing import Dict, List, Optional, Tuple
import pandas as pd
from pyomo.core import Model, value
from ehubx.core.common import TimeSeriesKind
from ehubx.core import exceptions
from ehubx.parser.ebm_tech_parser import YAMLKEY_AVAILABILITY, \
    YAMLKEY_DEMANDNOMINAL
from ehubx.parser.csv_parser import HeaderId
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.tech_data import TechId
from ehubx.data.ebm_tech_data import EbmTechs
from ehubx.data.time_data import Times
from ehubx.data.time_series import TimeSeries
from ehubx.model import ebm_tech_model
from ehubx.writer.common_writer import create_dir, add_to_df_st, \
    add_to_df_ts_cl, add_to_df_ts_hor

# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "writ/ebm_tech"
"""String identifying the EBM technology writer module for logging purposes"""

FILENAME_TIMESERIES_EBMTECHS: str = "ebm_techs.csv"
"""Filename for EBM technology time series"""

SOURCE: str = "ebm_tech"
"""Display name for the EBM tech module in result files"""

ENTRY_EC: str = "EBM ec"
"""Entry name for EBM ec in result files"""

ENTRY_NUMVEHICLES: str = "Number of EBM vehicles"
"""Entry name for number of EBM vehicles in result files"""

ENTRY_INEFF: str = "EBM charging efficiency (in_eff)"
"""Entry name for EBM charging efficiency in result files"""

ENTRY_OUTEFF: str = "EBM discharging efficiency (out_eff)"
"""Entry name for EBM discharging efficiency in result files"""

ENTRY_STANDBYLOSS: str = "EBM standby loss (standby_loss)"
"""Entry name for EBM standby loss in result files"""

ENTRY_STORAGECAP: str = "EBM storage capacity per vehicle (storage_cap)"
"""Entry name for EBM storage capacity per vehicle in result files"""

ENTRY_SOCMIN: str = "Minimal EBM SOC (soc_min)"
"""Entry name for EBM input parameter 'soc_min' in result files"""

ENTRY_SOCMAX: str = "Maximal EBM SOC (soc_max)"
"""Entry name for EBM input parameter 'soc_max' in result files"""

ENTRY_SOCINIT: str = "Initial EBM SOC (soc_init)"
"""Entry name for EBM input parameter 'soc_init' in result files"""

ENTRY_CHARGEMAX: str = "Maximal EBM charging speed per vehicle (charge_max)"
"""Entry name for EBM input parameter 'charge_max' in result files"""

ENTRY_DISCHARGEMAX: str = \
    "Maximal EBM discharging speed per vehicle (discharge_max)"
"""Entry name for EBM input parameter 'discharge_max' in result files"""

ENTRY_DISCHARGECONTROL: str = \
    "EBM discharge controllability (discharge_control)"
"""Entry name for EBM input parameter 'discharge_control' in result files"""

ENTRY_DEMANDMODIFIER: str = "EBM demand modifier (demand_modifier)"
"""Entry name for EBM input parameter 'demand_modifier' in result files"""

ENTRY_DEMANDNOMINAL: str = "EBM nominal demand (demand_nominal)"
"""Entry name for EBM input parameter 'demand_nominal' in result files"""

ENTRY_AVAILABILITY: str = "EBM availability (availability)"
"""Entry name for EBM input parameter 'availability' in result files"""

ENTRY_CONSUMPTION: str = "EBM fleet consumption"
"""Entry name for EBM fleet consumption in result files"""

ENTRY_INFLOW: str = f"EBM tech inflow ({ebm_tech_model.VAR_EBMTECHINFLOW})"
"""Entry name for EBM inflow (grid to vehicle) variable in result files"""

ENTRY_OUTFLOW: str = f"EBM tech outflow ({ebm_tech_model.VAR_EBMTECHOUTFLOW})"
"""Entry name for EBM outflow (vehicle to grid) variable in result files"""

ENTRY_ENERGY: str = f"EBM tech energy ({ebm_tech_model.VAR_EBMTECHENERGY})"
"""Entry name for EBM outflow (vehicle to grid) variable in result files"""


def format_all(energy_system: EnergySystem, model: Model, df_st: pd.DataFrame,
               df_ts_hor: pd.DataFrame, df_ts_cl: Optional[pd.DataFrame]
               ) -> None:
    # Tech-specific properties
    for tech_id in energy_system.ebm_techs.ids_in_order:
        _format_tech(energy_system, model, tech_id, df_st, df_ts_hor, df_ts_cl)


def _format_tech(energy_system: EnergySystem, model: Model, x: TechId,
                 df_st: pd.DataFrame, df_ts_hor: pd.DataFrame,
                 df_ts_cl: Optional[pd.DataFrame]) -> None:
    # ec
    ec = energy_system.ebm_techs.get_ec(x)
    add_to_df_st(df_st, ENTRY_EC, ec.key, tech=x.key, source=SOURCE,
                 in_res="input")

    # num_vehicles
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            num_vehicles = energy_system.ebm_techs.get_num_vehicles(s, h, x)
            add_to_df_st(df_st, ENTRY_NUMVEHICLES, num_vehicles, unit="1",
                         stage=s.key, hub=h.key, tech=x.key, source=SOURCE,
                         in_res="input")

    # in_eff
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        in_eff = energy_system.ebm_techs.get_in_eff(s, x)
        add_to_df_st(df_st, ENTRY_INEFF, in_eff, unit="1", stage=s.key,
                     tech=x.key, source=SOURCE, in_res="input")

    # out_eff
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        out_eff = energy_system.ebm_techs.get_out_eff(s, x)
        add_to_df_st(df_st, ENTRY_OUTEFF, out_eff, unit="1", stage=s.key,
                     tech=x.key, source=SOURCE, in_res="input")

    # standby_loss
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        standby_loss = energy_system.ebm_techs.get_standby_loss(s, x)
        add_to_df_st(df_st, ENTRY_STANDBYLOSS, standby_loss, unit="1",
                     stage=s.key, tech=x.key, source=SOURCE, in_res="input")

    # storage_cap
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        storage_cap = energy_system.ebm_techs.get_storage_cap(s, x)
        add_to_df_st(df_st, ENTRY_STORAGECAP, storage_cap, unit="kWh",
                     stage=s.key, tech=x.key, source=SOURCE, in_res="input")

    # soc_min
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        soc_min = energy_system.ebm_techs.get_soc_min(s, x)
        add_to_df_st(df_st, ENTRY_SOCMIN, soc_min, unit="1", stage=s.key,
                     tech=x.key, source=SOURCE, in_res="input")

    # soc_max
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        soc_max = energy_system.ebm_techs.get_soc_max(s, x)
        add_to_df_st(df_st, ENTRY_SOCMAX, soc_max, unit="1", stage=s.key,
                     tech=x.key, source=SOURCE, in_res="input")

    # soc_init
    for h in energy_system.hubs.ids_in_order:
        if h not in energy_system.techs.get_allowed_hubs(x):
            continue
        soc_init = energy_system.ebm_techs.get_soc_init(h, x)
        add_to_df_st(df_st, ENTRY_SOCMAX, soc_init, unit="1", hub=h.key,
                     tech=x.key, source=SOURCE, in_res="input")

    # charge_max
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        charge_max = energy_system.ebm_techs.get_charge_max(s, x)
        add_to_df_st(df_st, ENTRY_CHARGEMAX, charge_max, unit="kW",
                     stage=s.key, tech=x.key, source=SOURCE, in_res="input")

    # discharge_max
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        discharge_max = energy_system.ebm_techs.get_discharge_max(s, x)
        add_to_df_st(df_st, ENTRY_DISCHARGEMAX, discharge_max, unit="kW",
                     stage=s.key, tech=x.key, source=SOURCE, in_res="input")

    # discharge_control
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        discharge_control = energy_system.ebm_techs.get_discharge_control(s, x)
        add_to_df_st(df_st, ENTRY_DISCHARGECONTROL, discharge_control,
                     unit="1", stage=s.key, tech=x.key, source=SOURCE,
                     in_res="input")

    # demand_modifier
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            demand_mod = energy_system.ebm_techs.get_demand_modifier(s, h, x)
            add_to_df_st(df_st, ENTRY_DEMANDMODIFIER, demand_mod, unit="1",
                         stage=s.key, hub=h.key, tech=x.key, source=SOURCE,
                         in_res="input")

    # demand_nominal
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            demand_nom = energy_system.ebm_techs.get_demand_nominal(s, h, x)
            if demand_nom.has_values:
                add_to_df_ts_cl(df_ts_hor, df_ts_cl,
                    energy_system.times, ENTRY_DEMANDNOMINAL, demand_nom,
                    unit="kW", stage=s.key, hub=h.key, tech=x.key,
                    source=SOURCE, in_res="input")
            if not demand_nom.has_values:
                demand_nom_def = demand_nom.def_value
                assert demand_nom_def is not None
                add_to_df_st(df_st, ENTRY_DEMANDNOMINAL, demand_nom_def,
                             unit="kW", stage=s.key, hub=h.key, tech=x.key,
                             source=SOURCE, in_res="input")

    # consumption
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            consumption = energy_system.ebm_techs.get_consumption(s, h, x,
                energy_system.times)
            if consumption.has_values:
                add_to_df_ts_cl(df_ts_hor, df_ts_cl,
                    energy_system.times, ENTRY_CONSUMPTION, consumption,
                    unit="kW", stage=s.key, hub=h.key, tech=x.key,
                    source=SOURCE, in_res="input")
            if not consumption.has_values:
                consumption_def = consumption.def_value
                assert consumption_def is not None
                add_to_df_st(df_st, ENTRY_CONSUMPTION, consumption_def,
                             unit="kW", stage=s.key, hub=h.key, tech=x.key,
                             source=SOURCE, in_res="input")

    # availability
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            availability = energy_system.ebm_techs.get_availability(s, h, x)
            if availability.has_values:
                add_to_df_ts_cl(df_ts_hor, df_ts_cl,
                    energy_system.times, ENTRY_AVAILABILITY, availability,
                    unit="1", stage=s.key, hub=h.key, tech=x.key,
                    source=SOURCE, in_res="input")
            if not availability.has_values:
                availability_def = availability.def_value
                assert availability_def is not None
                add_to_df_st(df_st, ENTRY_AVAILABILITY, availability_def,
                             unit="1", stage=s.key, hub=h.key, tech=x.key,
                             source=SOURCE, in_res="input")

    # EBM inflow
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, ebm_tech_model.VAR_EBMTECHINFLOW)
            inflow = TimeSeries()
            for t in energy_system.times.ids:
                inflow.set_value(t, value(var[s.key, h.key, x.key,
                                              t.key_as_int],
                                          exception=False))
            add_to_df_ts_cl(df_ts_hor, df_ts_cl,
                energy_system.times, ENTRY_INFLOW, inflow, unit="kW",
                stage=s.key, hub=h.key, tech=x.key, source=SOURCE,
                in_res="result")

    # EBM outflow
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, ebm_tech_model.VAR_EBMTECHOUTFLOW)
            outflow = TimeSeries()
            for t in energy_system.times.ids:
                outflow.set_value(t, value(var[s.key, h.key, x.key,
                                               t.key_as_int],
                                           exception=False))
            add_to_df_ts_cl(df_ts_hor, df_ts_cl,
                energy_system.times, ENTRY_OUTFLOW, outflow, unit="kW",
                stage=s.key, hub=h.key, tech=x.key, source=SOURCE,
                in_res="result")

    # EBM energy
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, ebm_tech_model.VAR_EBMTECHENERGY)
            energy = TimeSeries()
            for t in energy_system.times.ids_horizon:
                energy.set_value(t, value(var[s.key, h.key, x.key,
                                              t.key_as_int],
                                          exception=False))
            add_to_df_ts_hor(df_ts_hor, energy_system.times,
                ENTRY_ENERGY, energy, unit="kWh", stage=s.key, hub=h.key,
                tech=x.key, source=SOURCE, in_res="result")


def write_data_time_series(ebm_techs: EbmTechs, times: Times,
                           dir_path: str) -> None:
    """
    Writes all time series with actual data (def_value is not enough) in an
    EBM technology data object to a dedicated csv file in a directory

    :param ebm_techs: The EBM technology data object whose time series are to
        be written
    :type ebm_techs: Demands
    :param times: Times data object
    :type times: Times
    :param dir_path: Path where the csv file will be placed
    :type dir_path: str
    """
    # Create directory if it does not exist
    if not os.path.isdir(dir_path):
        if not create_dir(dir_path):
            raise exceptions.EhubXException(
                "Could not write EBM tech time series data because "
                "the directory could not be created", module=LOG_MODULE_STR)

    # Gather time series
    data: Dict[Tuple[str, str, str, str], List[float]] = {}
    for (kind, stage, ids, series) in ebm_techs.time_series:
        # Skip series without values
        if not series.has_values:
            continue
        if kind == TimeSeriesKind.EBMTECHAVAIL:
            data[stage.key, ids[0], ids[1], YAMLKEY_AVAILABILITY] = [
                series.get_value(t) for t in times.ids_in_order]
        if kind == TimeSeriesKind.EBMTECHDEMANDNOM:
            data[stage.key, ids[0], ids[1], YAMLKEY_DEMANDNOMINAL] = [
                series.get_value(t) for t in times.ids_in_order]

    # Write demands file
    if data:
        df = pd.DataFrame(data)
        df.columns.names = [HeaderId.STAGEID.value, HeaderId.HUBID.value,
                            HeaderId.TECHID.value, HeaderId.PROFILEKEY.value]
        df.index += 1
        df.to_csv(os.path.join(dir_path, FILENAME_TIMESERIES_EBMTECHS))
