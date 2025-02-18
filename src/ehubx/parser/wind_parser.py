import os
from typing import Optional
from ehubx.core import logging
from ehubx.data.stage_data import Stages, StageId
from ehubx.data.hub_data import HubId
from ehubx.data.tech_data import TechId
from ehubx.data.wind_tech_data import WindTechs
from ehubx.data.ec_data import EcId
from ehubx.data.wind_data import WindData, WindparkId
from ehubx.data.time_data import TimeId
from ehubx.parser import tech_parser
from ehubx.parser import csv_parser
from ehubx.parser import yaml_parser
from ehubx.parser import exceptions

# YAML keys
YAMLKEY_WINDPARAMS = "wind_params"
YAMLKEY_TURBINEFOOTPRINT = "turbine_footprint"
YAMLKEY_ROTORAREA = "rotor_area"
YAMLKEY_VELONOMINAL = "velo_nominal"
YAMLKEY_VELOCUTIN = "velo_cut_in"
YAMLKEY_VELOCUTOFF = "velo_cut_off"
YAMLKEY_CURTAILMAXREL = "curtail_max_rel"
YAMLKEY_WINDPARKS = "windparks"
YAMLKEY_WINDPARKID = "windpark_id"
YAMLKEY_ECS = "ecs"

# Literals
LOG_MODULE_STR: str = "pars/wind_tech"
FILENAME_WINDAREAS = "wind_areas.csv"
FILENAME_WINDVELOCITY = "wind_velocity.csv"


def parse_techs(tech_root_node: Optional[yaml_parser.YamlNode],
                stages: Stages) -> WindTechs:
    # Create wind techs
    wind_techs = WindTechs()
    if tech_root_node is None:
        return wind_techs
    techs_node = tech_root_node[tech_parser.YAMLKEY_TECHS]
    if techs_node is None:
        return wind_techs
    for tech_node in techs_node:
        _parse_tech(tech_node, stages, wind_techs)
    # Logging
    _log_wind_techs(wind_techs)
    # Return
    return wind_techs


def _parse_tech(tech_node: yaml_parser.YamlDictNode, stages: Stages,
                wind_techs: WindTechs) -> None:
    # tech_id
    tech_id_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        tech_node, tech_parser.YAMLKEY_TECHID)
    tech_id = TechId(tech_id_str)
    # type
    tech_type = yaml_parser.parse_optional_str_value_from_dict_node(
        tech_node, tech_parser.YAMLKEY_TYPE)
    if tech_type != tech_parser.TechType.WIND.value:
        return
    # Add id
    wind_techs.add_id(tech_id)
    # wind_params
    wind_params_node = yaml_parser.get_mandatory_subnode_from_dict_node(
        tech_node, YAMLKEY_WINDPARAMS)
    yaml_parser.check_node_type(wind_params_node,
                                yaml_parser.YamlNodeKind.DICT)
    # turbine_footprint
    turbine_footprint = \
        yaml_parser.parse_mandatory_yeardep_float_from_dict_node(
            wind_params_node, YAMLKEY_TURBINEFOOTPRINT, stages)
    for stage_id, value in turbine_footprint.items():
        wind_techs.set_turbine_footprint(stage_id, tech_id, value)
    # rotor_area
    rotor_area = yaml_parser.parse_mandatory_yeardep_float_from_dict_node(
        wind_params_node, YAMLKEY_ROTORAREA, stages)
    for stage_id, value in rotor_area.items():
        wind_techs.set_rotor_area(stage_id, tech_id, value)
    # velo_nominal
    velo_nominal = yaml_parser.parse_mandatory_yeardep_float_from_dict_node(
        wind_params_node, YAMLKEY_VELONOMINAL, stages)
    for stage_id, value in velo_nominal.items():
        wind_techs.set_velo_nominal(stage_id, tech_id, value)
    # velo_cut_in
    velo_cut_in = yaml_parser.parse_mandatory_yeardep_float_from_dict_node(
        wind_params_node, YAMLKEY_VELOCUTIN, stages)
    for stage_id, value in velo_cut_in.items():
        wind_techs.set_velo_cut_in(stage_id, tech_id, value)
    # velo_cut_in
    velo_cut_off = yaml_parser.parse_mandatory_yeardep_float_from_dict_node(
        wind_params_node, YAMLKEY_VELOCUTOFF, stages)
    for stage_id, value in velo_cut_off.items():
        wind_techs.set_velo_cut_off(stage_id, tech_id, value)
    # curtail_max_rel
    curtail_max_rel = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        wind_params_node, YAMLKEY_CURTAILMAXREL, stages)
    if curtail_max_rel is not None:
        for stage_id, value in curtail_max_rel.items():
            wind_techs.set_curtail_max_rel(stage_id, tech_id, value)


def parse_data(renewables_subpath: str,
               ec_root_node: Optional[yaml_parser.YamlNode]) -> WindData:
    wind_data = WindData()
    _parse_windparks(ec_root_node, wind_data)
    # wind_areas
    areas_file_path = os.path.join(renewables_subpath, FILENAME_WINDAREAS)
    if os.path.isfile(areas_file_path):
        df_area = csv_parser.parse(areas_file_path,
            header_ids=[csv_parser.HeaderId.STAGEID,
                        csv_parser.HeaderId.HUBID])
        for (s, h) in df_area.columns:
            for wp in df_area.index:
                area = df_area[(s, h)][wp]
                wind_data.set_windpark_area(StageId(s), HubId(h),
                                            WindparkId(wp), area)
    # wind_velocity
    velocity_file_path = os.path.join(renewables_subpath,
                                      FILENAME_WINDVELOCITY)
    if os.path.isfile(velocity_file_path):
        df_velocity = csv_parser.parse(velocity_file_path,
            header_ids=[csv_parser.HeaderId.STAGEID, csv_parser.HeaderId.ECID])
        for (s, e) in df_velocity.columns:
            for t in df_velocity.index:
                velocity = df_velocity[(s, e)][t]
                wind_data.set_velocity(StageId(s), EcId(e), TimeId(t),
                                       velocity)
    # Logging
    _log_wind_data(wind_data)
    # Return
    return wind_data


def _parse_windparks(ec_root_node: Optional[yaml_parser.YamlNode],
                     wind_data: WindData) -> None:
    if ec_root_node is None:
        return
    windparks_node = ec_root_node[YAMLKEY_WINDPARKS]
    if windparks_node is None:
        return
    yaml_parser.check_node_type(windparks_node, yaml_parser.YamlNodeKind.LIST)
    windparks_node.set_id(YAMLKEY_WINDPARKID)
    for windpark_node in windparks_node:
        _parse_windpark(windpark_node, wind_data)


def _parse_windpark(windpark_node: yaml_parser.YamlDictNode,
                    wind_data: WindData) -> None:
    # windpark_id
    windpark_id_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        windpark_node, YAMLKEY_WINDPARKID)
    windpark_id = WindparkId(windpark_id_str)
    wind_data.add_windpark_id(windpark_id)
    # ecs
    ecs_node = yaml_parser.get_mandatory_subnode_from_dict_node(windpark_node,
                                                                YAMLKEY_ECS)
    yaml_parser.check_node_type(ecs_node, yaml_parser.YamlNodeKind.LIST)
    if len(ecs_node) == 0:
        raise exceptions.EmptyListNodeException(windpark_node.file_path,
                                                windpark_node.node_path_as_str,
                                                module=LOG_MODULE_STR)
    ecs = yaml_parser.parse_str_list_from_dict_node(windpark_node, YAMLKEY_ECS)
    for ec_id in ecs:
        wind_data.add_windpark_ec(windpark_id, EcId(ec_id))


def _log_wind_techs(wind_techs: WindTechs) -> None:
    logging.log_file(f"Parsed {len(wind_techs.ids)} wind tech(s)",
                     module=LOG_MODULE_STR)
    for x in wind_techs.ids:
        logging.log_file(f"  WindTech {x}", print_time=False)


def _log_wind_data(wind_data: WindData) -> None:
    logging.log_file((f"Parsed wind data: Wind ecs = {wind_data.ecs}, "
                      f"{len(wind_data.windpark_ids)} windpark id(s)"),
                     module=LOG_MODULE_STR)
    for wp in wind_data.windpark_ids:
        logging.log_file(
            f"  Windpark {wp}: ecs {wind_data.get_windpark_ecs(wp)}",
            print_time=False)
