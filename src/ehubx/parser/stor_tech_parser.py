from typing import Optional
from ehubx.core import logging
from ehubx.data.stage_data import Stages
from ehubx.data.hub_data import HubId
from ehubx.data.tech_data import TechId
from ehubx.data.stor_tech_data import StorageTechs
from ehubx.data.ec_data import EcId
import ehubx.parser.hub_parser as hub_parser
import ehubx.parser.tech_parser as tech_parser
from ehubx.parser import yaml_parser


# YAML keys
YAMLKEY_STORAGEPARAMS = "storage_params"
YAMLKEY_EC = "ec"
YAMLKEY_INEFF = "in_eff"
YAMLKEY_OUTEFF = "out_eff"
YAMLKEY_CHARGEMAX = "charge_max"
YAMLKEY_DISCHARGEMAX = "discharge_max"
YAMLKEY_STANDBYLOSS = "standby_loss"
YAMLKEY_SOCMIN = "soc_min"
YAMLKEY_SOCMAX = "soc_max"
YAMLKEY_SOCINIT = "soc_init"

# Literals
LOG_MODULE_STR: str = "pars/stor_techs"


def parse_primary(tech_root_node: Optional[yaml_parser.YamlNode],
                  stages: Stages) -> StorageTechs:
    # Create storage techs
    stor_techs = StorageTechs()
    # File does not exist or is empty:
    if tech_root_node is None:
        return stor_techs
    # Level 0: techs
    techs_node = tech_root_node[tech_parser.YAMLKEY_TECHS]
    if techs_node is None:
        return stor_techs
    for tech_node in techs_node:
        _parse_stor_tech_primary(tech_node, stages, stor_techs)
    # Logging
    _log(stor_techs)
    # Return
    return stor_techs


def _parse_stor_tech_primary(tech_node: yaml_parser.YamlDictNode,
                             stages: Stages, stor_techs: StorageTechs) -> None:
    # tech_id
    tech_id_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        tech_node, tech_parser.YAMLKEY_TECHID)
    tech_id = TechId(tech_id_str)
    # type
    tech_type = yaml_parser.parse_optional_str_value_from_dict_node(
        tech_node, tech_parser.YAMLKEY_TYPE)
    if tech_type != tech_parser.TechType.STORAGE.value:
        return
    # add id
    stor_techs.add_id(tech_id)
    # storage_params
    storage_params_node = yaml_parser.get_mandatory_subnode_from_dict_node(
        tech_node, YAMLKEY_STORAGEPARAMS)
    yaml_parser.check_node_type(storage_params_node,
                                yaml_parser.YamlNodeKind.DICT)
    # ec
    ec_id_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        storage_params_node, YAMLKEY_EC)
    ec_id = EcId(ec_id_str)
    stor_techs.set_ec(tech_id, ec_id)
    # in_eff
    in_eff = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        storage_params_node, YAMLKEY_INEFF, stages)
    if in_eff is not None:
        for stage_id, value in in_eff.items():
            stor_techs.set_in_eff(stage_id, tech_id, value)
    # out_eff
    out_eff = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        storage_params_node, YAMLKEY_OUTEFF, stages)
    if out_eff is not None:
        for stage_id, value in out_eff.items():
            stor_techs.set_out_eff(stage_id, tech_id, value)
    # charge_max
    charge_max = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        storage_params_node, YAMLKEY_CHARGEMAX, stages)
    if charge_max is not None:
        for stage_id, value in charge_max.items():
            stor_techs.set_charge_max(stage_id, tech_id, value)
    # discharge_max
    discharge_max = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        storage_params_node, YAMLKEY_DISCHARGEMAX, stages)
    if discharge_max is not None:
        for stage_id, value in discharge_max.items():
            stor_techs.set_discharge_max(stage_id, tech_id, value)
    # standby_loss
    standby_loss = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        storage_params_node, YAMLKEY_STANDBYLOSS, stages)
    if standby_loss is not None:
        for stage_id, value in standby_loss.items():
            stor_techs.set_standby_loss(stage_id, tech_id, value)
    # soc_min
    soc_min = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        storage_params_node, YAMLKEY_SOCMIN, stages)
    if soc_min is not None:
        for stage_id, value in soc_min.items():
            stor_techs.set_soc_min(stage_id, tech_id, value)
    # soc_max
    soc_max = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        storage_params_node, YAMLKEY_SOCMAX, stages)
    if soc_max is not None:
        for stage_id, value in soc_max.items():
            stor_techs.set_soc_max(stage_id, tech_id, value)


def parse_secondary(hub_root_node: Optional[yaml_parser.YamlNode],
                    stor_techs: StorageTechs) -> None:
    if hub_root_node is None:
        return
    hubs_node = hub_root_node[hub_parser.YAMLKEY_HUBS]
    if hubs_node is None:
        return
    for hub_node in hubs_node:
        _parse_hub_secondary(hub_node, stor_techs)


def _parse_hub_secondary(hub_node: yaml_parser.YamlDictNode,
                         stor_techs: StorageTechs) -> None:
    # id
    hub_id_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        hub_node, hub_parser.YAMLKEY_HUBID)
    hub_id = HubId(hub_id_str)
    techs_node = hub_node[tech_parser.YAMLKEY_TECHS]
    if techs_node is None:
        return
    for tech_id in stor_techs.ids:
        tech_node = techs_node[tech_id.key]
        if tech_node is None:
            continue
        _parse_tech_secondary(tech_node, hub_id, tech_id, stor_techs)


def _parse_tech_secondary(tech_node: yaml_parser.YamlDictNode, hub_id: HubId,
                          tech_id: TechId, stor_techs: StorageTechs) -> None:
    # storage_params
    storage_params_node = tech_node[YAMLKEY_STORAGEPARAMS]
    if storage_params_node is None:
        return
    yaml_parser.check_node_type(storage_params_node,
                                yaml_parser.YamlNodeKind.DICT)
    # soc_init
    soc_init = yaml_parser.parse_optional_float_value_from_dict_node(
        storage_params_node, YAMLKEY_SOCINIT)
    if soc_init is not None:
        stor_techs.set_soc_init(hub_id, tech_id, soc_init)


def _log(stor_techs: StorageTechs) -> None:
    logging.log_file(f"Parsed {len(stor_techs.ids)} storage tech(s)",
                     module=LOG_MODULE_STR)
    for x in stor_techs.ids:
        logging.log_file(f"  StorTech {x}: ec {stor_techs.get_ec(x)}",
                         print_time=False)
