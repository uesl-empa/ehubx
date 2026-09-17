import os
from typing import Optional

import ehubx.data.exceptions as data_exceptions
from ehubx.core import logging
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.time_data import TimeId
from ehubx.data.unit import DimlessUnit, LengthUnit, PowerUnit, TimeUnit, Unit
from ehubx.data.value import Value
from ehubx.data.wind_data import (
    TERRAIN_COST_COMPONENTS,
    TerrainId,
    WindData,
    WindGroupId,
)
from ehubx.data.wind_tech_data import WindTechs
from ehubx.parser import csv_parser, exceptions, hub_parser, tech_parser, yaml_parser


# YAML keys
YAMLKEY_WINDPARAMS = "wind_params"
YAMLKEY_EC = "ec"
YAMLKEY_RATED_POWER = "rated_power"

YAMLKEY_CUT_IN_SPEED = "cut_in_speed"
YAMLKEY_CUT_OUT_SPEED = "cut_out_speed"
YAMLKEY_RATED_SPEED = "rated_speed"
YAMLKEY_CURTAILMAXREL = "curtail_max_rel"
YAMLKEY_CURTAILMINREL = "curtail_min_rel"
YAMLKEY_AREA_PER_TURBINE = "area_per_turbine"
YAMLKEY_POWER_COEFFICIENT = "power_coefficient"
YAMLKEY_ROTOR_DIAMETER = "rotor_diameter"
YAMLKEY_HUB_HEIGHT = "hub_height"
YAMLKEY_ALLOWED_TERRAINS = "allowed_terrains"


# Literals
LOG_MODULE_STR: str = "pars/wind_tech"
FILENAME_WINDSPEED = "wind_speed.csv"
FILENAME_WINDTURBINT_PROFILE = "wind_turbulence_intensity_profile.csv"
FILENAME_WINDTURBINT_FIXED = "wind_turbulence_intensity_fixed.csv"
FILENAME_WINDAREAS = "wind_areas.csv"
FILENAME_WINDGROUP = "wind_groups.csv"
FILENAME_WINDTERRAIN = "wind_terrains.csv"
FILENAME_TERRAIN_AREAS = "wind_terrain_areas.csv"
FILENAME_TERRAIN_MULT = "wind_terrain_multipliers.csv"


def parse_techs_primary(
    tech_root_node: Optional[yaml_parser.YamlNode],
    techs: Techs,
    ecs: Ecs,
) -> WindTechs:
    wind_techs = WindTechs()
    if tech_root_node is None:
        return wind_techs
    techs_node = tech_root_node[tech_parser.YAMLKEY_TECHS]
    if techs_node is None:
        return wind_techs
    for tech_node in techs_node:
        _parse_tech_primary(tech_node, techs, ecs, wind_techs)
    # Return
    return wind_techs


def parse_techs_secondary(
    hub_root_node: Optional[yaml_parser.YamlNode], stages: Stages, wind_techs: WindTechs
) -> None:
    if hub_root_node is None:
        return
    hubs_node = hub_root_node[hub_parser.YAMLKEY_HUBS]
    if hubs_node is None:
        return
    for hub_node in hubs_node:
        _parse_hub_techs_secondary(hub_node, stages, wind_techs)


def _parse_tech_primary(
    tech_node: yaml_parser.YamlDictNode,
    techs: Techs,
    ecs: Ecs,
    wind_techs: WindTechs,
) -> None:
    # tech_id
    tech_id_str = yaml_parser.parse_mandatory_str_from_dict_node(
        tech_node, tech_parser.YAMLKEY_TECHID
    )
    tech_id = TechId(tech_id_str)
    # type
    tech_type = yaml_parser.parse_optional_str_from_dict_node(
        tech_node, tech_parser.YAMLKEY_TYPE
    )
    if tech_type != tech_parser.TechType.WIND.value:
        return
    # cap_unit - currently set up for"number of turbines" (dimless) -> change to kW
    techs.set_cap_unit(tech_id, PowerUnit.KW)

    # Add id
    wind_techs.add_id(tech_id)

    # wind_params
    wind_params_node = tech_node[YAMLKEY_WINDPARAMS]
    if wind_params_node is None:
        raise exceptions.ParsingException(
            "techs.yaml",
            f"Missing '{YAMLKEY_WINDPARAMS}' for wind tech '{tech_id.key}'",
            module=LOG_MODULE_STR,
        )
    yaml_parser.check_node_type(wind_params_node, yaml_parser.YamlNodeKind.DICT)

    # ec
    ec_id_str = yaml_parser.parse_mandatory_str_from_dict_node(
        wind_params_node, YAMLKEY_EC
    )
    ec_id = EcId(ec_id_str)
    wind_techs.set_ec(tech_id, ec_id, ecs.get_unit(ec_id))

    # rated power
    rated_power = yaml_parser.parse_mandatory_value_from_dict_node(
        wind_params_node, YAMLKEY_RATED_POWER, expected_unit=PowerUnit.KW
    )
    wind_techs.set_rated_power(tech_id, rated_power)

    # cut in wind speed (cut_in_speed)
    cut_in_speed = yaml_parser.parse_mandatory_value_from_dict_node(
        wind_params_node, YAMLKEY_CUT_IN_SPEED, expected_unit=LengthUnit.M / TimeUnit.S
    )
    wind_techs.set_cut_in_speed(tech_id, cut_in_speed)

    # rated wind speed (rated_speed)
    rated_speed = yaml_parser.parse_mandatory_value_from_dict_node(
        wind_params_node, YAMLKEY_RATED_SPEED, expected_unit=LengthUnit.M / TimeUnit.S
    )
    wind_techs.set_rated_speed(tech_id, rated_speed)

    # cut out wind speed (cut_out_speed)
    cut_out_speed = yaml_parser.parse_mandatory_value_from_dict_node(
        wind_params_node, YAMLKEY_CUT_OUT_SPEED, expected_unit=LengthUnit.M / TimeUnit.S
    )
    wind_techs.set_cut_out_speed(tech_id, cut_out_speed)

    # rotor_diameter_m (mandatory)
    rotor_diameter = yaml_parser.parse_mandatory_value_from_dict_node(
        wind_params_node, YAMLKEY_ROTOR_DIAMETER, expected_unit=LengthUnit.M
    )
    wind_techs.set_rotor_diameter(tech_id, rotor_diameter)

    # hub_height_m (mandatory)
    hub_height = yaml_parser.parse_mandatory_value_from_dict_node(
        wind_params_node, YAMLKEY_HUB_HEIGHT, expected_unit=LengthUnit.M
    )
    wind_techs.set_hub_height(tech_id, hub_height)

    # power_coefficient (mandatory)
    power_coefficient = yaml_parser.parse_mandatory_value_from_dict_node(
        wind_params_node, YAMLKEY_POWER_COEFFICIENT, expected_unit=DimlessUnit()
    )
    wind_techs.set_power_coefficient(tech_id, power_coefficient)

    # area per turbine
    area_per_turbine = yaml_parser.parse_mandatory_value_from_dict_node(
        wind_params_node, YAMLKEY_AREA_PER_TURBINE, expected_unit=LengthUnit.M**2
    )
    wind_techs.set_area_per_turbine(tech_id, area_per_turbine)

    # optional curtailment bounds (tech-level)
    curtail_max_rel = yaml_parser.parse_optional_value_from_dict_node(
        wind_params_node, YAMLKEY_CURTAILMAXREL, expected_unit=DimlessUnit()
    )
    curtail_min_rel = yaml_parser.parse_optional_value_from_dict_node(
        wind_params_node, YAMLKEY_CURTAILMINREL, expected_unit=DimlessUnit()
    )
    if curtail_max_rel is not None:
        wind_techs.set_curtail_max_rel(tech_id, curtail_max_rel)
    if curtail_min_rel is not None:
        wind_techs.set_curtail_min_rel(tech_id, curtail_min_rel)

    # optional terrain allow-list per wind tech
    has_allowed_terrains = wind_params_node[YAMLKEY_ALLOWED_TERRAINS] is not None
    if has_allowed_terrains:
        allowed_terrains = yaml_parser.parse_str_list_from_dict_node(
            wind_params_node, YAMLKEY_ALLOWED_TERRAINS, optional=False
        )
        wind_techs.set_allowed_terrains(tech_id, set(allowed_terrains))

    # Logging
    _log_wind_techs(wind_techs)


"""
One long function with 6 independent blocks, each wrapped in if os.path.isfile(...).
Reads csv input files for new wind module, incl. terrain specific data.
Every file is optional: if it's missing, that feature just doesn't get used.
e.g. no wind_terrain_multipliers.csv -> no terrain cost penalty
"""


def parse_data(renewables_subpath: str) -> WindData:
    wind_data = WindData()
    tuples_in_speed: set[tuple[StageId, WindGroupId]] = set()
    tuples_in_turb_int: set[tuple[StageId, WindGroupId]] = set()
    tuples_in_area: set[tuple[StageId, HubId, WindGroupId]] = set()
    tuples_in_height: set[WindGroupId] = set()
    tuples_in_roughness: set[TerrainId] = set()
    terrains_in_area: set[TerrainId] = set()

    # Reference height of each wind-group speed profile
    wg_file_path = os.path.join(renewables_subpath, FILENAME_WINDGROUP)
    if os.path.isfile(wg_file_path):
        df_windgroup = csv_parser.parse(
            wg_file_path,
            header_ids=[csv_parser.HeaderId.WINDGROUPID],
        )

        for wind_group_key in df_windgroup.columns:
            wind_group = WindGroupId(wind_group_key)

            try:
                unit_wg = Unit.from_str(
                    df_windgroup.attrs[csv_parser.ATTR_UNIT].get(wind_group_key, "")
                )
            except data_exceptions.UnitException as ex:
                raise exceptions.ParsingException(
                    wg_file_path,
                    f"Invalid unit '{ex.unit}' for wind group '{wind_group_key}'",
                    module=LOG_MODULE_STR,
                ) from ex

            expected_unit_len = LengthUnit.M
            if not unit_wg.same_type_as(expected_unit_len):
                raise exceptions.ParsingException(
                    wg_file_path,
                    f"Invalid unit '{unit_wg}' for wind group '{wind_group_key}'. "
                    f"Expected a length unit like '{expected_unit_len}'.",
                    module=LOG_MODULE_STR,
                )

            if wind_group not in wind_data.get_wind_groups():
                wind_data.add_wind_group(wind_group)
            height_val = df_windgroup[wind_group_key].get("height")
            if height_val is not None:
                wind_data.set_wind_group_height(wind_group, Value(height_val, unit_wg))
                tuples_in_height.add(wind_group)
    # Surface roughness of each terrain
    terrain_file_path = os.path.join(renewables_subpath, FILENAME_WINDTERRAIN)
    if os.path.isfile(terrain_file_path):
        df_terrain = csv_parser.parse(
            terrain_file_path,
            header_ids=[csv_parser.HeaderId.TERRAINID],
        )
        for terrain_key in df_terrain.columns:
            terrain = TerrainId(terrain_key)
            try:
                unit = Unit.from_str(
                    df_terrain.attrs[csv_parser.ATTR_UNIT].get(terrain_key, "")
                )
            except data_exceptions.UnitException as ex:
                raise exceptions.ParsingException(
                    terrain_file_path,
                    f"Invalid unit '{ex.unit}' for terrain '{terrain_key}'",
                    module=LOG_MODULE_STR,
                ) from ex
            if not unit.same_type_as(LengthUnit.M):
                raise exceptions.ParsingException(
                    terrain_file_path,
                    f"Invalid unit '{unit}' for terrain '{terrain_key}'. "
                    "Expected a length unit.",
                    module=LOG_MODULE_STR,
                )
            roughness_val = df_terrain[terrain_key].get("roughness")
            if roughness_val is not None:
                wind_data.set_terrain_roughness(terrain, Value(roughness_val, unit))
                tuples_in_roughness.add(terrain)

    # Wind speed (per stage, wind_group - no terrain dimension)
    speed_file_path = os.path.join(renewables_subpath, FILENAME_WINDSPEED)
    if os.path.isfile(speed_file_path):
        df_speed = csv_parser.parse(
            speed_file_path,
            header_ids=[csv_parser.HeaderId.STAGEID, csv_parser.HeaderId.WINDGROUPID],
        )

        for s, w in df_speed.columns:
            expected_unit = LengthUnit.M / TimeUnit.S
            try:
                unit = Unit.from_str(df_speed.attrs[csv_parser.ATTR_UNIT][s, w])
            except data_exceptions.UnitException as ex:
                raise exceptions.ParsingException(
                    speed_file_path,
                    f"Invalid unit '{ex.unit}' for wind speed "
                    f"at (stage, wind_group) tuple ({s}, {w})",
                    module=LOG_MODULE_STR,
                ) from ex
            if not unit.same_type_as(expected_unit):
                raise exceptions.ParsingException(
                    speed_file_path,
                    f"Invalid unit '{unit}' for wind speed "
                    f"at (stage, wind_group) tuple ({s}, {w}). "
                    f"Expected a unit like '{expected_unit}'.",
                    module=LOG_MODULE_STR,
                )
            tuples_in_speed.add((StageId(s), WindGroupId(w)))
            if WindGroupId(w) not in wind_data.get_wind_groups():
                wind_data.add_wind_group(WindGroupId(w))
            for t, val in df_speed[s, w].items():
                wind_data.set_speed_in_profile(
                    StageId(s), WindGroupId(w), TimeId(t), Value(val, unit)
                )

    # Fixed wind turbulence intensity (per stage, wind_group - no time dimension)
    turb_int_fixed_file_path = os.path.join(
        renewables_subpath, FILENAME_WINDTURBINT_FIXED
    )
    if os.path.isfile(turb_int_fixed_file_path):
        df_turb_int_fixed = csv_parser.parse(
            turb_int_fixed_file_path,
            header_ids=[csv_parser.HeaderId.STAGEID, csv_parser.HeaderId.WINDGROUPID],
        )

        for s, w in df_turb_int_fixed.columns:
            expected_unit = DimlessUnit()
            try:
                unit = Unit.from_str(
                    df_turb_int_fixed.attrs[csv_parser.ATTR_UNIT][s, w]
                )
            except data_exceptions.UnitException as ex:
                raise exceptions.ParsingException(
                    turb_int_fixed_file_path,
                    f"Invalid unit '{ex.unit}' for fixed wind turbulence intensity "
                    f"at (stage, wind_group) tuple ({s}, {w})",
                    module=LOG_MODULE_STR,
                ) from ex
            if not unit.same_type_as(expected_unit):
                raise exceptions.ParsingException(
                    turb_int_fixed_file_path,
                    f"Invalid unit '{unit}' for fixed wind turbulence intensity "
                    f"at (stage, wind_group) tuple ({s}, {w}). "
                    f"Expected a unit like '{expected_unit}'.",
                    module=LOG_MODULE_STR,
                )
            if WindGroupId(w) not in wind_data.get_wind_groups():
                wind_data.add_wind_group(WindGroupId(w))
            val = df_turb_int_fixed[s, w].get("turbulence_intensity")
            if val is not None:
                wind_data.set_fixed_turbulence_intensity(
                    StageId(s), WindGroupId(w), Value(float(val), unit)
                )

    # Wind turbulence intensity profile (per stage, wind_group, time)
    turb_int_file_path = os.path.join(renewables_subpath, FILENAME_WINDTURBINT_PROFILE)
    if not os.path.isfile(turb_int_file_path):
        legacy_turb_int_file_path = os.path.join(
            renewables_subpath, "wind_turbulence_intensity.csv"
        )
        if os.path.isfile(legacy_turb_int_file_path):
            turb_int_file_path = legacy_turb_int_file_path
    if os.path.isfile(turb_int_file_path):
        df_turb_int = csv_parser.parse(
            turb_int_file_path,
            header_ids=[csv_parser.HeaderId.STAGEID, csv_parser.HeaderId.WINDGROUPID],
        )

        for s, w in df_turb_int.columns:
            expected_unit = DimlessUnit()
            try:
                unit = Unit.from_str(df_turb_int.attrs[csv_parser.ATTR_UNIT][s, w])
            except data_exceptions.UnitException as ex:
                raise exceptions.ParsingException(
                    turb_int_file_path,
                    f"Invalid unit '{ex.unit}' for wind turbulence intensity "
                    f"at (stage, wind_group) tuple ({s}, {w})",
                    module=LOG_MODULE_STR,
                ) from ex
            if not unit.same_type_as(expected_unit):
                raise exceptions.ParsingException(
                    turb_int_file_path,
                    f"Invalid unit '{unit}' for wind turbulence intensity "
                    f"at (stage, wind_group) tuple ({s}, {w}). "
                    f"Expected a unit like '{expected_unit}'.",
                    module=LOG_MODULE_STR,
                )
            tuples_in_turb_int.add((StageId(s), WindGroupId(w)))
            if WindGroupId(w) not in wind_data.get_wind_groups():
                wind_data.add_wind_group(WindGroupId(w))
            for t, val in df_turb_int[s, w].items():
                wind_data.set_turbulence_intensity_in_profile(
                    StageId(s), WindGroupId(w), TimeId(t), Value(val, unit)
                )

    # Wind areas (static, per stage/hub)
    area_file_path = os.path.join(renewables_subpath, FILENAME_WINDAREAS)
    if os.path.isfile(area_file_path):
        df_area = csv_parser.parse(
            area_file_path,
            header_ids=[
                csv_parser.HeaderId.STAGEID,
                csv_parser.HeaderId.HUBID,
            ],
        )

        for s, h in df_area.columns:
            expected_unit = LengthUnit.M * LengthUnit.M
            try:
                unit = Unit.from_str(df_area.attrs[csv_parser.ATTR_UNIT][s, h])
            except data_exceptions.UnitException as ex:
                raise exceptions.ParsingException(
                    area_file_path,
                    f"Invalid unit '{ex.unit}' for wind area at "
                    f"(stage, hub) tuple ({s}, {h})",
                    module=LOG_MODULE_STR,
                ) from ex
            if not unit.same_type_as(expected_unit):
                raise exceptions.ParsingException(
                    area_file_path,
                    f"Invalid unit '{unit}' for wind area at "
                    f"(stage, hub) tuple ({s}, {h}). "
                    f"Expected an area unit like '{expected_unit}'.",
                    module=LOG_MODULE_STR,
                )

            for w in df_area.index:
                if WindGroupId(w) not in wind_data.get_wind_groups():
                    raise exceptions.ParsingException(
                        area_file_path,
                        f"Wind group {w} in wind area file {area_file_path} "
                        "is not defined in wind group file "
                        f"{wg_file_path}. Please add an entry for wind group "
                        f"{w} in the wind group file.",
                        module=LOG_MODULE_STR,
                    )
                area = df_area[(s, h)][w]
                wind_data.set_area(
                    StageId(s), HubId(h), WindGroupId(w), Value(area, unit)
                )
                tuples_in_area.add((StageId(s), HubId(h), WindGroupId(w)))

    # Terrain area fractions (wind_terrain_areas.csv)
    # Rows = terrain types, columns = wind groups, values = fractions summing to 1.
    terrain_areas_file_path = os.path.join(renewables_subpath, FILENAME_TERRAIN_AREAS)
    if os.path.isfile(terrain_areas_file_path):
        df_terrain_areas = csv_parser.parse(
            terrain_areas_file_path,
            header_ids=[csv_parser.HeaderId.WINDGROUPID],
        )
        for w_key in df_terrain_areas.columns:
            wind_group = WindGroupId(w_key)
            if wind_group not in wind_data.get_wind_groups():
                raise exceptions.ParsingException(
                    terrain_areas_file_path,
                    f"Unknown wind group '{w_key}' in terrain area file.",
                    module=LOG_MODULE_STR,
                )
            for terrain_key in df_terrain_areas.index:
                terrain = TerrainId(str(terrain_key))
                frac = df_terrain_areas[w_key].get(terrain_key)
                if frac is not None:
                    wind_data.set_terrain_area_frac(wind_group, terrain, float(frac))
                    terrains_in_area.add(terrain)
        wind_data.set_terrain_areas_loaded()
        logging.log_file(
            f"Parsed terrain area fractions for {len(df_terrain_areas.index)} "
            "terrain(s)",
            module=LOG_MODULE_STR,
        )

    # Terrain cost multipliers (optional - if file absent, standard costs apply).
    # CSV format: two header rows (wind_group_id, terrain_id), data rows are cost
    # components. Effective per-group multiplier = area-fraction-weighted average.
    terrain_file_path = os.path.join(renewables_subpath, FILENAME_TERRAIN_MULT)
    if os.path.isfile(terrain_file_path):
        df_terrain = csv_parser.parse(
            terrain_file_path,
            header_ids=[
                csv_parser.HeaderId.WINDGROUPID,
                csv_parser.HeaderId.TERRAINID,
            ],
        )
        for w, terrain_key in df_terrain.columns:
            if WindGroupId(w) not in wind_data.get_wind_groups():
                raise exceptions.ParsingException(
                    terrain_file_path,
                    f"Wind group '{w}' in terrain multipliers file is not defined in "
                    f"{wg_file_path}. Add an entry for '{w}' in wind_groups.csv.",
                    module=LOG_MODULE_STR,
                )
            for component in TERRAIN_COST_COMPONENTS:
                val = df_terrain[w, terrain_key].get(component)
                if val is None:
                    raise exceptions.ParsingException(
                        terrain_file_path,
                        f"Missing row '{component}' for (wind_group='{w}', "
                        f"terrain='{terrain_key}') in {terrain_file_path}.",
                        module=LOG_MODULE_STR,
                    )
                wind_data.set_terrain_multiplier(
                    WindGroupId(w), TerrainId(terrain_key), component, float(val)
                )
        wind_data.set_terrain_multipliers_loaded()
        n_combos = len(df_terrain.columns)
        logging.log_file(
            f"Parsed terrain cost multipliers for {n_combos} (wind_group, terrain) "
            "combination(s)",
            module=LOG_MODULE_STR,
        )

    # Validate
    _validate_tuples_in_data_files(
        tuples_in_speed,
        tuples_in_turb_int,
        tuples_in_area,
        tuples_in_height,
        tuples_in_roughness,
        terrains_in_area,
        speed_file_path,
        area_file_path,
    )

    # Logging
    _log_wind_data(wind_data)
    # Return
    return wind_data


def _validate_tuples_in_data_files(
    tuples_in_speed: set[tuple[StageId, WindGroupId]],
    tuples_in_turb_int: set[tuple[StageId, WindGroupId]],
    tuples_in_area: set[tuple[StageId, HubId, WindGroupId]],
    tuples_in_height: set[WindGroupId],
    tuples_in_roughness: set[TerrainId],
    terrains_in_area: set[TerrainId],
    speed_file_path: str,
    area_file_path: str,
) -> None:
    for s, w in tuples_in_speed:
        if not any(s == ss and w == ww for (ss, _, ww) in tuples_in_area):
            logging.log_warning(
                f"Stage-Windgroup tuple ({s}, {w}) occurs in speed file "
                f"{speed_file_path} but not in wind area file {area_file_path}",
                module=LOG_MODULE_STR,
            )
    for s, _, w in tuples_in_area:
        if (s, w) not in tuples_in_speed:
            logging.log_warning(
                f"Stage-Windgroup tuple ({s}, {w}) occurs in wind area file "
                f"{area_file_path} but not in speed file {speed_file_path}",
                module=LOG_MODULE_STR,
            )
    for _, w in tuples_in_speed:
        if w not in tuples_in_height:
            logging.log_warning(
                f"Wind group {w} has speed data but no reference height data.",
                module=LOG_MODULE_STR,
            )
    for s, w in tuples_in_turb_int:
        if (s, w) not in tuples_in_speed:
            logging.log_warning(
                f"Stage-Windgroup tuple ({s}, {w}) occurs in wind turbulence "
                f"intensity file but not in speed file {speed_file_path}",
                module=LOG_MODULE_STR,
            )
    for terrain in terrains_in_area:
        if terrain not in tuples_in_roughness:
            logging.log_warning(
                f"Terrain {terrain} has area data but no roughness data.",
                module=LOG_MODULE_STR,
            )


def _parse_hub_techs_secondary(
    hub_node: yaml_parser.YamlDictNode, stages: Stages, wind_techs: WindTechs
) -> None:
    hub_id_str = yaml_parser.parse_mandatory_str_from_dict_node(
        hub_node, hub_parser.YAMLKEY_HUBID
    )
    hub_id = HubId(hub_id_str)

    # wind_params at hub level - applies to all wind techs at this hub
    wind_params_node = hub_node[YAMLKEY_WINDPARAMS]
    if wind_params_node is None:
        return
    yaml_parser.check_node_type(wind_params_node, yaml_parser.YamlNodeKind.DICT)

    curtail_max_rel = yaml_parser.parse_optional_value_from_dict_node(
        wind_params_node, YAMLKEY_CURTAILMAXREL, expected_unit=DimlessUnit()
    )
    curtail_min_rel = yaml_parser.parse_optional_value_from_dict_node(
        wind_params_node, YAMLKEY_CURTAILMINREL, expected_unit=DimlessUnit()
    )
    if curtail_max_rel is not None:
        wind_techs.set_curtail_max_rel_hub(hub_id, curtail_max_rel)
    if curtail_min_rel is not None:
        wind_techs.set_curtail_min_rel_hub(hub_id, curtail_min_rel)


def _log_wind_techs(wind_techs: WindTechs) -> None:
    logging.log_file(
        f"Parsed {len(wind_techs.ids)} wind tech(s)", module=LOG_MODULE_STR
    )
    for x in wind_techs.ids:
        logging.log_file(f"  WindTech {x}", print_time=False)


def _log_wind_data(wind_data: WindData) -> None:
    logging.log_file("Parsed wind data", module=LOG_MODULE_STR)
