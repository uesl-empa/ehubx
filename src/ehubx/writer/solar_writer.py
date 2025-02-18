"""Solar writer module. Writes out information from the solar submodule to
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
from ehubx.data.solar_data import SolarData
from ehubx.data.time_data import Times
from ehubx.data.time_series import TimeSeries
from ehubx.model import solar_tech_model
from ehubx.writer.common_writer import create_dir, add_to_df_st, \
    add_to_df_ts_cl

# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "writ/solar"
"""String identifying the solar writer module for logging purposes"""

FILENAME_TIMESERIES_SOLARDATA: str = "solar_data.csv"
"""Filename for solar time series"""

PROFILEKEY_IRRADIATION: str = "irradiation"
"""Key for the irradiation time series to be used in CSV files"""

SOURCE: str = "solar_tech"
"""Display name for the solar tech module in result files"""

ENTRY_IRRADIATION: str = "Solar irradiation"
"""Entry name for solar irradiation in result files"""

ENTRY_AREA: str = "Solar area"
"""Entry name for solar area in result files"""

ENTRY_CURTAILMAXREL: str = "Maximal relative curtailment"
"""Entry name for maximal relative curtailment of solar techs in result
files"""

ENTRY_SOLARTECHINCIDENT: str = ("Solar tech incident "
                                f"({solar_tech_model.VAR_SOLARTECHINCIDENT})")
"""Entry name for solar tech incident in result files"""


def format_all(energy_system: EnergySystem, model: Model, df_st: pd.DataFrame,
               df_ts_hor: pd.DataFrame, df_ts_cl: Optional[pd.DataFrame]
               ) -> None:
    # Solar irradiation
    for s in energy_system.stages.ids_in_order:
        for e in energy_system.ecs.ids_in_order:
            if e not in energy_system.solar_data.ecs:
                continue
            irradiation = energy_system.solar_data.get_irradiation(s, e)
            if irradiation.has_values:
                add_to_df_ts_cl(df_ts_hor, df_ts_cl,
                    energy_system.times, ENTRY_IRRADIATION, irradiation,
                    unit="kW/m^2", stage=s.key, ec=e.key, source=SOURCE,
                    in_res="input")
            if not irradiation.has_values:
                irradiation_def = irradiation.def_value
                assert irradiation_def is not None
                add_to_df_st(df_st, ENTRY_IRRADIATION, irradiation_def,
                             unit="kW/m^2", stage=s.key, ec=e.key,
                             source=SOURCE, in_res="input")

    # Area
    for s in energy_system.stages.ids_in_order:
        for h in energy_system.hubs.ids_in_order:
            for e in energy_system.ecs.ids_in_order:
                if e not in energy_system.solar_data.ecs:
                    continue
                solar_area = energy_system.solar_data.get_area(s, h, e)
                add_to_df_st(df_st, ENTRY_AREA, solar_area, unit="m^2",
                             stage=s.key, hub=h.key, ec=e.key,
                             source=SOURCE, in_res="input")

    # Tech-specific values
    for tech_id in energy_system.solar_techs.ids_in_order:
        _format_tech(energy_system, model, tech_id, df_st, df_ts_hor, df_ts_cl)


def _format_tech(energy_system: EnergySystem, model: Model, x: TechId,
                 df_st: pd.DataFrame, df_ts_hor: pd.DataFrame,
                 df_ts_cl: Optional[pd.DataFrame]) -> None:
    # curtail_max_rel
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        curtail_max_rel = energy_system.solar_techs.get_curtail_max_rel(s, x)
        add_to_df_st(df_st, ENTRY_CURTAILMAXREL, curtail_max_rel, unit="1",
                     stage=s.key, tech=x.key, source=SOURCE, in_res="input")

    # Solar incident
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, solar_tech_model.VAR_SOLARTECHINCIDENT)
            incident = TimeSeries()
            for t in energy_system.times.ids:
                incident.set_value(t, value(var[s.key, h.key, x.key,
                                                t.key_as_int],
                                            exception=False))
            add_to_df_ts_cl(df_ts_hor, df_ts_cl, energy_system.times,
                            ENTRY_SOLARTECHINCIDENT, incident, unit="kW",
                            stage=s.key, hub=h.key, tech=x.key, source=SOURCE,
                            in_res="result")


def write_data_time_series(solar_data: SolarData, times: Times,
                           dir_path: str) -> None:
    """
    Writes all time series with actual data (def_value is not enough) in a
    solar data object to a dedicated csv file in a directory

    :param solar_data: The solar data object whose time series are to be
        written
    :type solar_data: SolarData
    :param times: Times data object
    :type times: Times
    :param dir_path: Path where the csv file will be placed
    :type dir_path: str
    """
    # Create directory if it does not exist
    if not os.path.isdir(dir_path):
        if not create_dir(dir_path):
            raise exceptions.EhubXException(
                "Could not write solar time series data because "
                "the directory could not be created", module=LOG_MODULE_STR)

    # Gather time series
    data: Dict[Tuple[str, str, str], List[float]] = {}
    for (kind, stage, ids, series) in solar_data.time_series:
        # Skip series without values
        if not series.has_values:
            continue
        if kind == TimeSeriesKind.SOLARIRRAD:
            data[stage.key, ids[0], PROFILEKEY_IRRADIATION] = [
                series.get_value(t) for t in times.ids_in_order]

    # Write demands file
    if data:
        df = pd.DataFrame(data)
        df.columns.names = [HeaderId.STAGEID.value, HeaderId.ECID.value,
                            HeaderId.PROFILEKEY.value]
        df.index += 1
        df.to_csv(os.path.join(dir_path, FILENAME_TIMESERIES_SOLARDATA))
