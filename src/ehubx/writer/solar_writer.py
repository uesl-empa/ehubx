"""Solar writer module. Writes out information from the solar submodule to
files"""

import os
from typing import Dict, List, Optional, Tuple

import pandas as pd
from pyomo.core import Model, value

from ehubx.core import exceptions
from ehubx.core.common import TimeSeriesKind
from ehubx.data.ec_data import EcId
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.tech_data import TechId
from ehubx.data.time_series import TimeSeries
from ehubx.data.unit import DimlessUnit, TimeUnit
from ehubx.data.value import Value
from ehubx.model import ec_model, solar_tech_model
from ehubx.parser.csv_parser import HeaderId
from ehubx.writer.common_writer import DfStBuilder, add_to_df_ts_cl, create_dir


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

ENTRY_SOLARTECHINCIDENT: str = (
    f"Solar tech incident ({solar_tech_model.VAR_SOLARTECHINCIDENT})"
)
"""Entry name for solar tech incident in result files"""


def format_all(
    energy_system: EnergySystem,
    model: Model,
    df_st_builder: DfStBuilder,
    df_ts_hor: pd.DataFrame,
    df_ts_cl: Optional[pd.DataFrame],
) -> None:
    # Solar irradiation
    for s in energy_system.stages.ids_in_order:
        for e in energy_system.ecs.ids_in_order:
            if e not in energy_system.solar_data.ecs:
                continue
            ec_unit = ec_model.get_ec_model_unit(
                energy_system.ecs.get_unit(e),
                energy_system.mass_unit,
                energy_system.power_unit,
            )
            irradiation = energy_system.solar_data.get_irradiation(s, e)
            irradiation_unit = ec_unit / (TimeUnit.H * (energy_system.length_unit**2))
            if irradiation.has_values:
                add_to_df_ts_cl(
                    df_ts_hor,
                    df_ts_cl,
                    energy_system.times,
                    ENTRY_IRRADIATION,
                    irradiation,
                    unit=irradiation_unit,
                    stage=s.key,
                    ec=e.key,
                    source=SOURCE,
                    in_res="input",
                )
            if not irradiation.has_values:
                irradiation_def = irradiation.def_value
                assert irradiation_def is not None
                df_st_builder.add_row(
                    ENTRY_IRRADIATION,
                    irradiation_def,
                    unit=irradiation_unit,
                    stage=s.key,
                    ec=e.key,
                    source=SOURCE,
                    in_res="input",
                )

    # Area
    for s in energy_system.stages.ids_in_order:
        for h in energy_system.hubs.ids_in_order:
            for e in energy_system.ecs.ids_in_order:
                if e not in energy_system.solar_data.ecs:
                    continue
                solar_area = energy_system.solar_data.get_area(s, h, e)
                df_st_builder.add_row(
                    ENTRY_AREA,
                    solar_area,
                    unit=(energy_system.length_unit**2),
                    stage=s.key,
                    hub=h.key,
                    ec=e.key,
                    source=SOURCE,
                    in_res="input",
                )

    # Tech-specific values
    for tech_id in energy_system.solar_techs.ids_in_order:
        _format_tech(energy_system, model, tech_id, df_st_builder, df_ts_hor, df_ts_cl)


def _format_tech(
    energy_system: EnergySystem,
    model: Model,
    x: TechId,
    df_st_builder: DfStBuilder,
    df_ts_hor: pd.DataFrame,
    df_ts_cl: Optional[pd.DataFrame],
) -> None:
    # curtail_max_rel
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        curtail_max_rel = energy_system.solar_techs.get_curtail_max_rel(s, x)
        df_st_builder.add_row(
            ENTRY_CURTAILMAXREL,
            curtail_max_rel,
            unit=DimlessUnit(),
            stage=s.key,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # Solar incident
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, solar_tech_model.VAR_SOLARTECHINCIDENT)
            incident = TimeSeries()
            e_solar = energy_system.conv_techs.get_in_ec_main(x)
            ec_unit = ec_model.get_ec_model_unit(
                energy_system.ecs.get_unit(e_solar),
                energy_system.mass_unit,
                energy_system.power_unit,
            )
            incident_unit = ec_unit / TimeUnit.H
            for t in energy_system.times.ids:
                incident_fl = value(
                    var[s.key, h.key, x.key, t.key_as_int], exception=False
                )
                if incident_fl is not None:
                    incident.set_value(t, Value(incident_fl, unit=incident_unit))
            add_to_df_ts_cl(
                df_ts_hor,
                df_ts_cl,
                energy_system.times,
                ENTRY_SOLARTECHINCIDENT,
                incident,
                unit=incident_unit,
                stage=s.key,
                hub=h.key,
                tech=x.key,
                source=SOURCE,
                in_res="result",
            )


def write_data_time_series(energy_system: EnergySystem, dir_path: str) -> None:
    """
    Writes all time series with actual data (def_value is not enough) in a
    solar data object to a dedicated csv file in a directory

    :param energy_system: Energy system data object
    :type energy_system: EnergySystem1
    :param dir_path: Path where the csv file will be placed
    :type dir_path: str
    """
    # Create directory if it does not exist
    if not os.path.isdir(dir_path):
        if not create_dir(dir_path):
            raise exceptions.EhubXException(
                "Could not write solar time series data because "
                "the directory could not be created",
                module=LOG_MODULE_STR,
            )

    # Gather time series
    data: Dict[Tuple[str, str, str, str], List[float]] = {}
    for kind, stage, ids, series in energy_system.solar_data.time_series:
        # Skip series without values
        if not series.has_values:
            continue
        ec_unit = ec_model.get_ec_model_unit(
            energy_system.ecs.get_unit(EcId(ids[0])),
            energy_system.mass_unit,
            energy_system.power_unit,
        )
        if kind == TimeSeriesKind.SOLARIRRAD:
            unit = ec_unit / (TimeUnit.H * (energy_system.length_unit**2))
            data[stage.key, ids[0], PROFILEKEY_IRRADIATION, str(unit)] = [
                series.get_value(t).to_float(unit=unit)
                for t in energy_system.times.ids_in_order
            ]

    # Write demands file
    if data:
        df = pd.DataFrame(data)
        df.columns.names = [
            HeaderId.STAGEID.value,
            HeaderId.ECID.value,
            HeaderId.PROFILEKEY.value,
            HeaderId.UNIT.value,
        ]
        df.index += 1
        df.to_csv(os.path.join(dir_path, FILENAME_TIMESERIES_SOLARDATA))
