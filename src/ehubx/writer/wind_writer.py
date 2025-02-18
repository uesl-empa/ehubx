"""Wind writer module. Writes out information from the wind submodule to
files"""
import os
from typing import Dict, List, Optional, Tuple
import pandas as pd
from pyomo.core import Model, value
from ehubx.core.common import TimeSeriesKind
from ehubx.core import exceptions
from ehubx.parser.csv_parser import HeaderId
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.tech_data import TechId
from ehubx.data.wind_data import WindData
from ehubx.data.time_data import Times
from ehubx.data.time_series import TimeSeries
from ehubx.model import wind_tech_model
from ehubx.writer.common_writer import create_dir, add_to_df_st, \
    add_to_df_ts_cl

# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "writ/wind"
"""String identifying the wind writer module for logging purposes"""

FILENAME_TIMESERIES_WIND: str = "wind_data.csv"
"""Filename for wind time series"""

PROFILEKEY_VELOCITY: str = "velocity"
"""Key for the velocity time series to be used in CSV files"""

SOURCE: str = "wind_tech"
"""Display name for the wind tech module in result files"""

ENTRY_VELOCITY: str = "Wind velocity"
"""Entry name for wind velocity in result files"""

ENTRY_AREA: str = "Windpark area"
"""Entry name for windpark area in result files"""

ENTRY_TURBINEFOOTPRINT: str = "Turbine footprint"
"""Entry name for turbine footprint of wind techs in result files"""

ENTRY_ROTORAREA: str = "Rotor area"
"""Entry name for rotor area of wind techs in result files"""

ENTRY_VELOCUTIN: str = "Cut-in velocity"
"""Entry name for cut-in velocity of wind techs in result files"""

ENTRY_VELONOMINAL: str = "Nominal velocity"
"""Entry name for nominal velocity of wind techs in result files"""

ENTRY_VELOCUTOFF: str = "Cut-off velocity"
"""Entry name for cut-off velocity of wind techs in result files"""

ENTRY_CURTAILMAXREL: str = "Cut-in velocity"
"""Entry name for maximal relative curtailment of wind techs in result files"""

ENTRY_WINDTECHINCIDENT: str = ("Wind tech incident "
                               f"({wind_tech_model.VAR_WINDTECHINCIDENT})")
"""Entry name for wind tech incident in result files"""

ENTRY_WINDTECHCURTAILMENT: str = \
    f"Wind tech curtailment ({wind_tech_model.VAR_WINDTECHCURTAILMENT})"
"""Entry name for wind tech curtailment in result files"""


def format_all(energy_system: EnergySystem, model: Model, df_st: pd.DataFrame,
               df_ts_hor: pd.DataFrame, df_ts_cl: Optional[pd.DataFrame]
               ) -> None:
    # Wind velocity
    for s in energy_system.stages.ids_in_order:
        for e in energy_system.ecs.ids_in_order:
            if e not in energy_system.wind_data.ecs:
                continue
            velocity = energy_system.wind_data.get_velocity(s, e)
            if velocity.has_values:
                add_to_df_ts_cl(df_ts_hor, df_ts_cl,
                    energy_system.times, ENTRY_VELOCITY, velocity,
                    unit="m/s", stage=s.key, ec=e.key, source=SOURCE,
                    in_res="input")
            if not velocity.has_values:
                velocity_def = velocity.def_value
                assert velocity_def is not None
                add_to_df_st(df_st, ENTRY_VELOCITY, velocity_def, unit="m/s",
                             stage=s.key, ec=e.key, source=SOURCE,
                             in_res="input")

    # Area
    for s in energy_system.stages.ids_in_order:
        for h in energy_system.hubs.ids_in_order:
            for wp in energy_system.wind_data.windpark_ids:
                windpark_area = energy_system.wind_data.get_windpark_area(
                    s, h, wp)
                add_to_df_st(df_st, ENTRY_AREA, windpark_area, unit="m^2",
                             stage=s.key, hub=h.key, windpark=wp.key,
                             source=SOURCE, in_res="input")

    # Tech-specific values
    for tech_id in energy_system.wind_techs.ids:
        _format_tech(energy_system, model, tech_id, df_st, df_ts_hor, df_ts_cl)


def _format_tech(energy_system: EnergySystem, model: Model, x: TechId,
                 df_st: pd.DataFrame, df_ts_hor: pd.DataFrame,
                 df_ts_cl: Optional[pd.DataFrame]) -> None:
    # Turbine footprint
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        footprint = energy_system.wind_techs.get_turbine_footprint(s, x)
        add_to_df_st(df_st, ENTRY_TURBINEFOOTPRINT, footprint, unit="m^2",
                     stage=s.key, tech=x.key, source=SOURCE, in_res="input")

    # Rotor area
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        rotor_area = energy_system.wind_techs.get_rotor_area(s, x)
        add_to_df_st(df_st, ENTRY_ROTORAREA, rotor_area, unit="m^2",
                     stage=s.key, tech=x.key, source=SOURCE, in_res="input")

    # Cut-in velocity
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        velo_cut_in = energy_system.wind_techs.get_velo_cut_in(s, x)
        add_to_df_st(df_st, ENTRY_VELOCUTIN, velo_cut_in, unit="m/s",
                     stage=s.key, tech=x.key, source=SOURCE, in_res="input")

    # Nominal velocity
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        velo_nominal = energy_system.wind_techs.get_velo_nominal(s, x)
        add_to_df_st(df_st, ENTRY_VELONOMINAL, velo_nominal, unit="m/s",
                     stage=s.key, tech=x.key, source=SOURCE, in_res="input")

    # Cut-off velocity
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        velo_cut_off = energy_system.wind_techs.get_velo_cut_off(s, x)
        add_to_df_st(df_st, ENTRY_VELOCUTOFF, velo_cut_off, unit="m/s",
                     stage=s.key, tech=x.key, source=SOURCE, in_res="input")

    # Maximal relative curtailment
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        curtail_max_rel = energy_system.wind_techs.get_curtail_max_rel(s, x)
        add_to_df_st(df_st, ENTRY_CURTAILMAXREL, curtail_max_rel, unit="1",
                     stage=s.key, tech=x.key, source=SOURCE, in_res="input")

    # Wind tech incident
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, wind_tech_model.VAR_WINDTECHINCIDENT)
            incident = TimeSeries()
            for t in energy_system.times.ids:
                incident.set_value(t, value(var[s.key, h.key, x.key,
                                                t.key_as_int],
                                            exception=False))
            add_to_df_ts_cl(df_ts_hor, df_ts_cl,
                energy_system.times, ENTRY_WINDTECHINCIDENT,
                incident, unit="kW", stage=s.key, hub=h.key,
                tech=x.key, source=SOURCE, in_res="result")

    # Wind tech curtailment
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, wind_tech_model.VAR_WINDTECHCURTAILMENT)
            curtailment = TimeSeries()
            for t in energy_system.times.ids:
                curtailment.set_value(t, value(var[s.key, h.key, x.key,
                                                   t.key_as_int],
                                               exception=False))
            add_to_df_ts_cl(df_ts_hor, df_ts_cl,
                energy_system.times, ENTRY_WINDTECHCURTAILMENT,
                curtailment, unit="kW", stage=s.key, hub=h.key,
                tech=x.key, source=SOURCE, in_res="result")


def write_time_series(wind_data: WindData, times: Times, dir_path: str
                      ) -> None:
    """
    Writes all time series with actual data (def_value is not enough) in a
    wind data object to a dedicated csv file in a directory

    :param wind_data: The wind data object whose time series are to be written
    :type wind_data: WindData
    :param times: Times data object
    :type times: Times
    :param dir_path: Path where the csv file will be placed
    :type dir_path: str
    """
    # Create directory if it does not exist
    if not os.path.isdir(dir_path):
        if not create_dir(dir_path):
            raise exceptions.EhubXException(
                "Could not write wind time series data because "
                "the directory could not be created", module=LOG_MODULE_STR)

    # Gather time series
    data_demands: Dict[Tuple[str, str, str], List[float]] = {}
    for (kind, stage, ids, series) in wind_data.time_series:
        # Skip series without values
        if not series.has_values:
            continue
        if kind == TimeSeriesKind.WINDVELOCITY:
            data_demands[stage.key, ids[0], PROFILEKEY_VELOCITY] = [
                series.get_value(t) for t in times.ids_in_order]

    # Write demands file
    if data_demands:
        df = pd.DataFrame(data_demands)
        df.columns.names = [HeaderId.STAGEID.value, HeaderId.ECID.value,
                            HeaderId.PROFILEKEY.value]
        df.index += 1
        df.to_csv(os.path.join(dir_path, FILENAME_TIMESERIES_WIND))
