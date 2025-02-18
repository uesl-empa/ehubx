import os
from typing import Optional
from ehubx.core import logging
from ehubx.data.stage_data import Stages, StageId
from ehubx.data.hub_data import HubId
from ehubx.data.tech_data import TechId
from ehubx.data.solar_tech_data import SolarTechs
from ehubx.data.ec_data import EcId
from ehubx.data.solar_data import SolarData
from ehubx.data.time_data import TimeId
from ehubx.parser import tech_parser
from ehubx.parser import csv_parser
from ehubx.parser import yaml_parser

# YAML keys
YAMLKEY_SOLARPARAMS = "solar_params"
YAMLKEY_CURTAILMAXREL = "curtail_max_rel"

# Literals
LOG_MODULE_STR: str = "pars/solar_tech"
FILENAME_SOLARAREAS = "solar_areas.csv"
FILENAME_SOLARIRRADIATION = "solar_irradiation.csv"


def parse_techs(tech_root_node: Optional[yaml_parser.YamlNode],
                stages: Stages) -> SolarTechs:
    solar_techs = SolarTechs()
    if tech_root_node is None:
        return solar_techs
    techs_node = tech_root_node[tech_parser.YAMLKEY_TECHS]
    if techs_node is None:
        return solar_techs
    for tech_node in techs_node:
        _parse_tech(tech_node, stages, solar_techs)
    # Return
    return solar_techs


def parse_data(renewables_subpath: str) -> SolarData:
    solar_data = SolarData()
    # Solar areas
    areas_file_path = os.path.join(renewables_subpath, FILENAME_SOLARAREAS)
    if os.path.isfile(areas_file_path):
        df_area = csv_parser.parse(areas_file_path,
            header_ids=[csv_parser.HeaderId.STAGEID,
                        csv_parser.HeaderId.HUBID])
        for (s, h) in df_area.columns:
            for e in df_area.index:
                area = df_area[(s, h)][e]
                solar_data.set_area(StageId(s), HubId(h), EcId(e), area)
    # Solar irradiation
    irradiation_file_path = os.path.join(renewables_subpath,
                                         FILENAME_SOLARIRRADIATION)
    if os.path.isfile(irradiation_file_path):
        df_irradiation = csv_parser.parse(irradiation_file_path,
            header_ids=[csv_parser.HeaderId.STAGEID, csv_parser.HeaderId.ECID])
        for (s, e) in df_irradiation.columns:
            for t in df_irradiation.index:
                irradiation = df_irradiation[(s, e)][t]
                solar_data.set_irradiation(StageId(s), EcId(e), TimeId(t),
                                           irradiation)
    # Logging
    _log_solar_data(solar_data)
    # Return
    return solar_data


def _parse_tech(tech_node: yaml_parser.YamlDictNode,
                stages: Stages, solar_techs: SolarTechs) -> None:
    # tech_id
    tech_id_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        tech_node, tech_parser.YAMLKEY_TECHID)
    tech_id = TechId(tech_id_str)
    # type
    tech_type = yaml_parser.parse_optional_str_value_from_dict_node(
        tech_node, tech_parser.YAMLKEY_TYPE)
    if tech_type != tech_parser.TechType.SOLAR.value:
        return
    # Add id
    solar_techs.add_id(tech_id)
    # solar_params
    solar_params_node = tech_node[YAMLKEY_SOLARPARAMS]
    if solar_params_node is None:
        return
    yaml_parser.check_node_type(solar_params_node,
                                yaml_parser.YamlNodeKind.DICT)
    # curtail_max_rel
    curtail_max_rel = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        solar_params_node, YAMLKEY_CURTAILMAXREL, stages)
    if curtail_max_rel is not None:
        for stage_id, value in curtail_max_rel.items():
            solar_techs.set_curtail_max_rel(stage_id, tech_id, value)
    # Logging
    _log_solar_techs(solar_techs)


def _log_solar_techs(solar_techs: SolarTechs) -> None:
    logging.log_file(f"Parsed {len(solar_techs.ids)} solar tech(s)",
                     module=LOG_MODULE_STR)
    for x in solar_techs.ids:
        logging.log_file(f"  SolarTech {x}", print_time=False)


def _log_solar_data(solar_data: SolarData) -> None:
    logging.log_file(f"Parsed solar data: Solar ecs = {solar_data.ecs}",
                     module=LOG_MODULE_STR)
