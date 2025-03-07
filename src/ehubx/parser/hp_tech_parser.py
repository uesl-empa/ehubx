import os
from typing import Optional

from ehubx.core import logging
from ehubx.data.ec_data import EcId
from ehubx.data.hp_tech_data import HeatpumpTechs
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.tech_data import TechId
from ehubx.data.time_data import TimeId
from ehubx.parser import csv_parser, hub_parser, tech_parser, yaml_parser


# YAML keys
YAMLKEY_HEATPUMPPARAMS = "heatpump_params"
YAMLKEY_ECS = "ecs"
YAMLKEY_EC_ELEC = "elec"
YAMLKEY_EC_HEATIN = "heat_in"
YAMLKEY_EC_HEATOUT = "heat_out"
YAMLKEY_EC_COOLIN = "cool_in"
YAMLKEY_EC_COOLOUT = "cool_out"
YAMLKEY_COP = "cop"
YAMLKEY_COPFACTOR = "cop_factor"
YAMLKEY_TEMPHEATIN = "temp_heat_in"
YAMLKEY_TEMPHEATOUT = "temp_heat_out"
YAMLKEY_PROFILEPATH = "profile_path"

# Literals
LOG_MODULE_STR: str = "pars/hp_tech"
FILETYPE_HEATPUMPPROFILE = "heat pump profile"


def parse_primary(
    tech_root_node: Optional[yaml_parser.YamlNode], stages: Stages
) -> HeatpumpTechs:
    # Create heat pump techs
    hp_techs = HeatpumpTechs()
    # File does not exist or is empty:
    if tech_root_node is None:
        return hp_techs
    techs_node = tech_root_node[tech_parser.YAMLKEY_TECHS]
    if techs_node is None:
        return hp_techs
    for tech_node in techs_node:
        _parse_hp_tech_primary(tech_node, stages, hp_techs)
    # Logging
    _log(hp_techs)
    return hp_techs


def _parse_hp_tech_primary(
    tech_node: yaml_parser.YamlDictNode, stages: Stages, hp_techs: HeatpumpTechs
) -> None:
    # tech_id
    tech_id_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        tech_node, tech_parser.YAMLKEY_TECHID
    )
    tech_id = TechId(tech_id_str)
    # type
    tech_type = yaml_parser.parse_optional_str_value_from_dict_node(
        tech_node, tech_parser.YAMLKEY_TYPE
    )
    if tech_type != tech_parser.TechType.HP.value:
        return
    # Add id
    hp_techs.add_id(tech_id)
    # heatpump_params
    hp_params_node = yaml_parser.get_mandatory_subnode_from_dict_node(
        tech_node, YAMLKEY_HEATPUMPPARAMS
    )
    yaml_parser.check_node_type(hp_params_node, yaml_parser.YamlNodeKind.DICT)
    # ecs
    _parse_ecs(hp_params_node, tech_id, hp_techs)
    # cop_factor
    cop_factor = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        hp_params_node, YAMLKEY_COPFACTOR, stages
    )
    if cop_factor:
        for stage_id, value in cop_factor.items():
            hp_techs.set_cop_factor(stage_id, tech_id, value)


def _parse_ecs(
    hp_params_node: yaml_parser.YamlNode, tech_id: TechId, hp_techs: HeatpumpTechs
) -> None:
    ecs_node = yaml_parser.get_mandatory_subnode_from_dict_node(
        hp_params_node, YAMLKEY_ECS
    )
    yaml_parser.check_node_type(ecs_node, yaml_parser.YamlNodeKind.DICT)
    # ec_el
    ec_el_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        ecs_node, YAMLKEY_EC_ELEC
    )
    ec_el = EcId(ec_el_str)
    hp_techs.set_ec_el(tech_id, ec_el)
    # ec_ht_in
    ec_ht_in_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        ecs_node, YAMLKEY_EC_HEATIN
    )
    ec_ht_in = EcId(ec_ht_in_str)
    hp_techs.set_ec_ht_in(tech_id, ec_ht_in)
    # ec_ht_out
    ec_ht_out_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        ecs_node, YAMLKEY_EC_HEATOUT
    )
    ec_ht_out = EcId(ec_ht_out_str)
    hp_techs.set_ec_ht_out(tech_id, ec_ht_out)
    # ec_co_in
    ec_co_in_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        ecs_node, YAMLKEY_EC_COOLIN
    )
    ec_co_in = EcId(ec_co_in_str)
    hp_techs.set_ec_co_in(tech_id, ec_co_in)
    # ec_co_out
    ec_co_out_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        ecs_node, YAMLKEY_EC_COOLOUT
    )
    ec_co_out = EcId(ec_co_out_str)
    hp_techs.set_ec_co_out(tech_id, ec_co_out)


def parse_secondary(
    hub_root_node: Optional[yaml_parser.YamlNode],
    stages: Stages,
    hp_techs: HeatpumpTechs,
) -> None:
    if hub_root_node is None:
        return
    hubs_node = hub_root_node[hub_parser.YAMLKEY_HUBS]
    if hubs_node is None:
        return
    for hub_node in hubs_node:
        _parse_hub_secondary(hub_node, stages, hp_techs)


def _parse_hub_secondary(
    hub_node: yaml_parser.YamlNode, stages: Stages, hp_techs: HeatpumpTechs
) -> None:
    # id
    hub_id_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        hub_node, hub_parser.YAMLKEY_HUBID
    )
    hub_id = HubId(hub_id_str)
    techs_node = hub_node[tech_parser.YAMLKEY_TECHS]
    if techs_node is None:
        return
    for tech_id in hp_techs.ids:
        tech_node = techs_node[tech_id.key]
        if tech_node is None:
            continue
        _parse_tech_secondary(tech_node, hub_id, tech_id, stages, hp_techs)


def _parse_tech_secondary(
    tech_node: yaml_parser.YamlDictNode,
    hub_id: HubId,
    tech_id: TechId,
    stages: Stages,
    hp_techs: HeatpumpTechs,
) -> None:
    # heatpump_params
    hp_params_node = tech_node[YAMLKEY_HEATPUMPPARAMS]
    if hp_params_node is None:
        return
    yaml_parser.check_node_type(hp_params_node, yaml_parser.YamlNodeKind.DICT)
    # cop (default)
    cop = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        hp_params_node, YAMLKEY_COP, stages
    )
    if cop is not None:
        for stage_id, value in cop.items():
            hp_techs.set_cop_def(stage_id, hub_id, tech_id, value)
    # temperatures
    temp_ht_in = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        hp_params_node, YAMLKEY_TEMPHEATIN, stages
    )
    if temp_ht_in is not None:
        for stage_id, value in temp_ht_in.items():
            hp_techs.set_temp_ht_in_def(stage_id, hub_id, tech_id, value)
    temp_ht_out = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        hp_params_node, YAMLKEY_TEMPHEATOUT, stages
    )
    if temp_ht_out is not None:
        for stage_id, value in temp_ht_out.items():
            hp_techs.set_temp_ht_out_def(stage_id, hub_id, tech_id, value)
    # profiles
    _parse_tech_secondary_profiles(hp_params_node, hub_id, tech_id, hp_techs)


def _parse_tech_secondary_profiles(
    hp_params_node: yaml_parser.YamlNode,
    hub_id: HubId,
    tech_id: TechId,
    hp_techs: HeatpumpTechs,
) -> None:
    profile_path = yaml_parser.parse_optional_str_value_from_dict_node(
        hp_params_node, YAMLKEY_PROFILEPATH
    )
    if profile_path is not None:
        profile_path = os.path.abspath(
            os.path.join(hp_params_node.file_path, os.pardir, profile_path)
        )
        yaml_parser.check_file_exists(profile_path, FILETYPE_HEATPUMPPROFILE)
        df = csv_parser.parse(
            profile_path,
            header_ids=[
                csv_parser.HeaderId.STAGEID,
                csv_parser.HeaderId.HUBID,
                csv_parser.HeaderId.TECHID,
                csv_parser.HeaderId.PROFILEKEY,
            ],
        )
        for s, h, x, profile_key in df.columns:
            if h != hub_id.key:
                continue
            if x != tech_id.key:
                continue
            stage_id = StageId(s)
            # temperatures
            if profile_key == YAMLKEY_TEMPHEATIN:
                for t in df.index:
                    hp_techs.set_temp_ht_in(
                        stage_id,
                        hub_id,
                        tech_id,
                        TimeId(t),
                        df[s, h, x, profile_key][t],
                    )
            if profile_key == YAMLKEY_TEMPHEATOUT:
                for t in df.index:
                    hp_techs.set_temp_ht_out(
                        stage_id,
                        hub_id,
                        tech_id,
                        TimeId(t),
                        df[s, h, x, profile_key][t],
                    )
            # cop
            if profile_key == YAMLKEY_COP:
                for t in df.index:
                    hp_techs.set_cop(
                        stage_id,
                        hub_id,
                        tech_id,
                        TimeId(t),
                        df[s, h, x, profile_key][t],
                    )


def _log(hp_techs: HeatpumpTechs) -> None:
    logging.log_file(
        f"Parsed {len(hp_techs.ids)} heat pump tech(s)", module=LOG_MODULE_STR
    )
    for x in hp_techs.ids:
        logging.log_file(
            f"  HpTech {x}: ec_el={hp_techs.get_ec_el(x)}, "
            f"ec_ht_in={hp_techs.get_ec_ht_in(x)}, "
            f"ec_ht_out={hp_techs.get_ec_ht_out(x)}, "
            f"ec_co_in={hp_techs.get_ec_co_in(x)}, "
            f"ec_co_out={hp_techs.get_ec_co_out(x)}",
            print_time=False,
        )
