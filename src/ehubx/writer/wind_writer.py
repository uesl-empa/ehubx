"""Wind writer module. Writes out information from the wind submodule to
files"""

import os
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from pyomo.core import Model, value

from ehubx.core import exceptions
from ehubx.core.common import TimeSeriesKind
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.tech_data import TechId
from ehubx.data.time_series import TimeSeries
from ehubx.data.unit import DimlessUnit, LengthUnit, TimeUnit, Unit
from ehubx.data.value import Value
from ehubx.model import ec_model, wind_tech_model
from ehubx.parser.csv_parser import HeaderId
from ehubx.writer.common_writer import DfStBuilder, add_to_df_ts_cl, create_dir


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "writ/wind"
"""String identifying the wind writer module for logging purposes"""

FILENAME_TIMESERIES_WINDDATA: str = "wind_data.csv"
"""Filename for wind time series"""

PROFILEKEY_WINDSPEED: str = "wind_speed"
"""Key for the wind speed time series to be used in CSV files"""

PROFILEKEY_WINDTURBINT: str = "wind_turbulence_intensity_profile"
"""Key for the wind turbulence intensity profile to be used in CSV files"""

SOURCE: str = "wind_tech"
"""Display name for the wind tech module in result files"""

ENTRY_WINDSPEED: str = "Wind speed"
"""Entry name for wind speed in result files"""

ENTRY_EC: str = "Wind output ec"
"""Entry name for wind output ec in result files"""

ENTRY_WINDTECHOUT: str = "Wind tech output"
"""Entry name for wind tech output in result files"""


def format_all(
    energy_system: EnergySystem,
    model: Model,
    df_st_builder: DfStBuilder,
    df_ts_hor: pd.DataFrame,
    df_ts_cl: Optional[pd.DataFrame],
) -> None:
    # Wind speed (per stage, wind_group â€” reference height is terrain-specific)
    for (s, w), wind_speed in energy_system.wind_data._speed.items():
        wind_speed_unit = LengthUnit.M / TimeUnit.S
        if wind_speed.has_values:
            add_to_df_ts_cl(
                df_ts_hor,
                df_ts_cl,
                energy_system.times,
                ENTRY_WINDSPEED,
                wind_speed,
                unit=wind_speed_unit,
                stage=s.key,
                wind_group=w.key,
                source=SOURCE,
                in_res="input",
            )
        if not wind_speed.has_values:
            wind_speed_def = wind_speed.def_value
            assert wind_speed_def is not None
            df_st_builder.add_row(
                ENTRY_WINDSPEED,
                wind_speed_def,
                unit=wind_speed_unit,
                stage=s.key,
                wind_group=w.key,
                source=SOURCE,
                in_res="input",
            )
    # Tech-specific values
    for tech_id in energy_system.wind_techs.ids_in_order:
        _format_tech(energy_system, model, tech_id, df_st_builder, df_ts_hor, df_ts_cl)


def _format_tech(
    energy_system: EnergySystem,
    model: Model,
    x: TechId,
    df_st_builder: DfStBuilder,
    df_ts_hor: pd.DataFrame,
    df_ts_cl: Optional[pd.DataFrame],
) -> None:
    # ec
    ec = energy_system.wind_techs.get_ec(x)
    hub_height_m = energy_system.wind_techs.get_hub_height(x).to_float(LengthUnit.M)
    hub_height_str = f"{hub_height_m}m"
    df_st_builder.add_row(ENTRY_EC, ec.key, tech=x.key, source=SOURCE, in_res="input")

    # Wind output
    """
    Total wind output per (stage, hub, tech) combination, summed over all wind groups
    and terrain types.
    Hourly time series, unit = ec/h.
    Reads VAR_WINDTECHOUT from model.
    """
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, wind_tech_model.VAR_WINDTECHOUT)
            wind_out = TimeSeries()
            ec = energy_system.wind_techs.get_ec(x)
            ec_unit = ec_model.get_ec_model_unit(
                energy_system.ecs.get_unit(ec),
                energy_system.mass_unit,
                energy_system.power_unit,
                energy_system.length_unit,
                energy_system.passenger_unit,
                energy_system.freight_unit,
            )
            wind_out_unit = ec_unit / TimeUnit.H
            for t in energy_system.times.ids:
                wind_out_fl = value(
                    var[s.key, h.key, x.key, t.key_as_int], exception=False
                )
                if wind_out_fl is not None:
                    wind_out.set_value(t, Value(wind_out_fl, unit=wind_out_unit))
            add_to_df_ts_cl(
                df_ts_hor,
                df_ts_cl,
                energy_system.times,
                ENTRY_WINDTECHOUT,
                wind_out,
                unit=wind_out_unit,
                stage=s.key,
                hub=h.key,
                tech=x.key,
                ec=ec.key,
                wind_height=hub_height_str,
                source=SOURCE,
                in_res="result",
            )

    # Wind output per (wind_group, terrain) sub-group
    """
    Reads VAR_WINDTECHOUTINGROUP from model.
    Result: wind_group and terrain are exported in separate columns.
    """
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            for w in energy_system.wind_data.get_wind_groups():
                terrain_fracs = energy_system.wind_data.get_terrain_fracs_for_group(w)
                # When no terrain areas are defined the sub-group uses terrain == w
                # Falls back to the wind group itself when no terrain areas
                # are defined; terrain_key below handles both id types.
                subgroup_terrains: List[Any] = (
                    list(terrain_fracs) if terrain_fracs else [w]
                )
                for terrain in subgroup_terrains:
                    terrain_key = (
                        terrain.key if hasattr(terrain, "key") else str(terrain)
                    )
                    var = getattr(model, wind_tech_model.VAR_WINDTECHOUTINGROUP)
                    wind_out = TimeSeries()
                    ec = energy_system.wind_techs.get_ec(x)
                    ec_unit = ec_model.get_ec_model_unit(
                        energy_system.ecs.get_unit(ec),
                        energy_system.mass_unit,
                        energy_system.power_unit,
                        energy_system.length_unit,
                        energy_system.passenger_unit,
                        energy_system.freight_unit,
                    )
                    wind_out_unit = ec_unit / TimeUnit.H
                    for t in energy_system.times.ids:
                        wind_out_fl = value(
                            var[s.key, h.key, x.key, w.key, terrain_key, t.key_as_int],
                            exception=False,
                        )
                        if wind_out_fl is not None:
                            wind_out.set_value(
                                t, Value(wind_out_fl, unit=wind_out_unit)
                            )
                    add_to_df_ts_cl(
                        df_ts_hor,
                        df_ts_cl,
                        energy_system.times,
                        ENTRY_WINDTECHOUT,
                        wind_out,
                        unit=wind_out_unit,
                        stage=s.key,
                        hub=h.key,
                        tech=x.key,
                        ec=ec.key,
                        wind_group=w.key,
                        terrain=terrain_key,
                        wind_height=hub_height_str,
                        source=SOURCE,
                        in_res="result",
                    )

                    var_curt = getattr(model, wind_tech_model.VAR_WINDTECHCURT)
                    wind_curt = TimeSeries()
                    for t in energy_system.times.ids:
                        wind_curt_fl = value(
                            var_curt[
                                s.key, h.key, x.key, w.key, terrain_key, t.key_as_int
                            ],
                            exception=False,
                        )
                        if wind_curt_fl is not None:
                            wind_curt.set_value(
                                t, Value(wind_curt_fl, unit=wind_out_unit)
                            )
                    add_to_df_ts_cl(
                        df_ts_hor,
                        df_ts_cl,
                        energy_system.times,
                        f"Wind curtailment ({wind_tech_model.VAR_WINDTECHCURT})",
                        wind_curt,
                        unit=wind_out_unit,
                        stage=s.key,
                        hub=h.key,
                        tech=x.key,
                        ec=ec.key,
                        wind_group=w.key,
                        terrain=terrain_key,
                        wind_height=hub_height_str,
                        source=SOURCE,
                        in_res="result",
                    )

    # Capacity and installed capacity per (wind_group, terrain) sub-group
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            for w in energy_system.wind_data.get_wind_groups():
                terrain_fracs = energy_system.wind_data.get_terrain_fracs_for_group(w)
                # Falls back to the wind group itself when no terrain areas
                # are defined; terrain_key below handles both id types.
                subgroup_terrains = list(terrain_fracs) if terrain_fracs else [w]
                for terrain in subgroup_terrains:
                    terrain_key = (
                        terrain.key if hasattr(terrain, "key") else str(terrain)
                    )
                    if not energy_system.wind_techs.is_subgroup_allowed(
                        x, w.key, terrain_key
                    ):
                        continue
                    ec = energy_system.wind_techs.get_ec(x)
                    cap_unit = ec_model.get_ec_model_unit(
                        energy_system.ecs.get_unit(ec),
                        energy_system.mass_unit,
                        energy_system.power_unit,
                        energy_system.length_unit,
                        energy_system.passenger_unit,
                        energy_system.freight_unit,
                    )
                    var_cap = getattr(model, wind_tech_model.VAR_WINDTECHCAPINGROUP)
                    cap_fl = value(
                        var_cap[s.key, h.key, x.key, w.key, terrain_key],
                        exception=False,
                    )
                    if cap_fl is not None:
                        df_st_builder.add_row(
                            "Wind sub-group capacity "
                            f"({wind_tech_model.VAR_WINDTECHCAPINGROUP})",
                            Value(cap_fl, unit=cap_unit),
                            unit=cap_unit,
                            stage=s.key,
                            hub=h.key,
                            tech=x.key,
                            wind_group=w.key,
                            terrain=terrain_key,
                            source=SOURCE,
                            in_res="result",
                        )

                    var_instl = getattr(
                        model, wind_tech_model.VAR_WINDTECHCAPINSTLGROUP
                    )
                    instl_fl = value(
                        var_instl[s.key, h.key, x.key, w.key, terrain_key],
                        exception=False,
                    )
                    if instl_fl is not None:
                        df_st_builder.add_row(
                            "Wind sub-group installed capacity "
                            f"({wind_tech_model.VAR_WINDTECHCAPINSTLGROUP})",
                            Value(instl_fl, unit=cap_unit),
                            unit=cap_unit,
                            stage=s.key,
                            hub=h.key,
                            tech=x.key,
                            wind_group=w.key,
                            terrain=terrain_key,
                            source=SOURCE,
                            in_res="result",
                        )

                    var_y_instl = getattr(
                        model, wind_tech_model.VAR_YWINDTECHCAPINSTLGROUP
                    )
                    y_instl_fl = value(
                        var_y_instl[s.key, h.key, x.key, w.key, terrain_key],
                        exception=False,
                    )
                    if y_instl_fl is not None:
                        df_st_builder.add_row(
                            "Wind sub-group install binary "
                            f"({wind_tech_model.VAR_YWINDTECHCAPINSTLGROUP})",
                            bool(round(y_instl_fl)),
                            stage=s.key,
                            hub=h.key,
                            tech=x.key,
                            wind_group=w.key,
                            terrain=terrain_key,
                            source=SOURCE,
                            in_res="result",
                        )

                    var_y_used = getattr(model, wind_tech_model.VAR_YWINDTECHUSEDGROUP)
                    y_used_fl = value(
                        var_y_used[s.key, h.key, x.key, w.key, terrain_key],
                        exception=False,
                    )
                    if y_used_fl is not None:
                        df_st_builder.add_row(
                            "Wind sub-group used binary "
                            f"({wind_tech_model.VAR_YWINDTECHUSEDGROUP})",
                            bool(round(y_used_fl)),
                            stage=s.key,
                            hub=h.key,
                            tech=x.key,
                            wind_group=w.key,
                            terrain=terrain_key,
                            source=SOURCE,
                            in_res="result",
                        )


def write_data_time_series(energy_system: EnergySystem, dir_path: str) -> None:
    """
    Writes all time series with actual data (def_value is not enough) in a
    wind data object to a dedicated csv file in a directory

    :param energy_system: Energy system data object
    :type energy_system: EnergySystem
    :param dir_path: Path where the csv file will be placed
    :type dir_path: str
    """
    # Create directory if it does not exist
    if not os.path.isdir(dir_path):
        if not create_dir(dir_path):
            raise exceptions.EhubXException(
                "Could not write wind time series data because "
                "the directory could not be created",
                module=LOG_MODULE_STR,
            )

    # Gather time series
    # Keys: (stage, wind_group, terrain_or_empty, profile_key, unit)
    data: Dict[Tuple[str, str, str, str, str], List[float]] = {}
    for kind, stage, ids, series in energy_system.wind_data.time_series:
        # Skip series without values
        if not series.has_values:
            continue
        if kind == TimeSeriesKind.WINDSPEED:
            unit = Unit.get_def_unit(LengthUnit.M / TimeUnit.S)
            data[stage.key, ids[0], "", PROFILEKEY_WINDSPEED, str(unit)] = [
                series.get_value(t).to_float(unit=unit)
                for t in energy_system.times.ids_in_order
            ]
        if kind == TimeSeriesKind.WINDTURBULENCEINTENSITY:
            unit = Unit.get_def_unit(DimlessUnit())
            data[stage.key, ids[0], "", PROFILEKEY_WINDTURBINT, str(unit)] = [
                series.get_value(t).to_float(unit=unit)
                for t in energy_system.times.ids_in_order
            ]

    # Write wind file
    if data:
        df = pd.DataFrame(data)
        df.columns.names = [
            HeaderId.STAGEID.value,
            HeaderId.WINDGROUPID.value,
            HeaderId.TERRAINID.value,
            HeaderId.PROFILEKEY.value,
            HeaderId.UNIT.value,
        ]
        df.index += 1
        df.to_csv(os.path.join(dir_path, FILENAME_TIMESERIES_WINDDATA))
