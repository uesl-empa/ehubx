import os
from typing import Optional, Tuple
from ehubx.core import logging
from ehubx.data.ec_data import Ecs, EcId, ImpExpType
from ehubx.parser import yaml_parser
from ehubx.parser import exceptions

# YAML keys
YAMLKEY_ECS = "ecs"
YAMLKEY_ECID = "ec_id"
YAMLKEY_ISENERGY = "is_energy"
YAMLKEY_IMPEXPTYPE = "imp_exp_type"
YAMLKEY_IMPEXPTYPE_CROSS = "cross"
YAMLKEY_IMPEXPTYPE_INTERNAL = "internal"
YAMLKEY_IMPEXPTYPE_NONE = "none"

# Literals
LOG_MODULE_STR: str = "pars/ec"
FILENAME_ECS = "ecs.yaml"
FILETYPE_ECS = "ecs"


def parse(basic_subpath: str
          ) -> Tuple[Ecs, Optional[yaml_parser.YamlNode]]:
    ecs = Ecs()
    ec_file_path = os.path.join(basic_subpath, FILENAME_ECS)
    if not os.path.isfile(ec_file_path):
        return ecs, None
    ec_root_node = yaml_parser.parse(ec_file_path)
    if ec_root_node is None:
        return ecs, None
    ecs_node = ec_root_node[YAMLKEY_ECS]
    if ecs_node is None:
        return ecs, ec_root_node
    yaml_parser.check_node_type(ecs_node, yaml_parser.YamlNodeKind.LIST)
    ecs_node.set_id(YAMLKEY_ECID)
    for ec_node in ecs_node:
        _parse_ec(ec_node, ecs)
    # Logging
    _log(ecs)
    return ecs, ec_root_node


def _parse_ec(ec_node: yaml_parser.YamlDictNode, ecs: Ecs) -> None:
    # id
    ec_id_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        ec_node, YAMLKEY_ECID)
    if "_" in ec_id_str:
        ec_id_node = yaml_parser.get_mandatory_subnode_from_dict_node(
            ec_node, YAMLKEY_ECID)
        logging.log_warning(
            (f"Warning in file {ec_node.file_path}: Deteted underscore in ec "
             f"id {ec_id_str} at node {ec_id_node.node_path_as_str}"),
            module=LOG_MODULE_STR)
    ec_id = EcId(ec_id_str)
    ecs.add_id(ec_id)
    # is_energy
    is_energy = yaml_parser.parse_optional_bool_value_from_dict_node(
        ec_node, YAMLKEY_ISENERGY)
    if is_energy is not None:
        ecs.set_is_energy(ec_id, is_energy)
    # imp_exp_type
    imp_exp_type = yaml_parser.parse_optional_str_value_from_dict_node(
        ec_node, YAMLKEY_IMPEXPTYPE)
    if imp_exp_type is not None:
        if imp_exp_type == YAMLKEY_IMPEXPTYPE_CROSS:
            ecs.set_imp_exp_type(ec_id, ImpExpType.CROSS)
        elif imp_exp_type == YAMLKEY_IMPEXPTYPE_INTERNAL:
            ecs.set_imp_exp_type(ec_id, ImpExpType.INTERNAL)
        elif imp_exp_type == YAMLKEY_IMPEXPTYPE_NONE:
            ecs.set_imp_exp_type(ec_id, ImpExpType.NONE)
        else:
            node_path_str = f"{ec_node.node_path_as_str}|{YAMLKEY_IMPEXPTYPE}"
            invalidity_reason = (f"{imp_exp_type} is not a known "
                                 "import-export-type")
            raise exceptions.InvalidValueException(
                ec_node.file_path, node_path_str, invalidity_reason,
                module=LOG_MODULE_STR)


def _log(ecs: Ecs) -> None:
    logging.log_file(f"Parsed {len(ecs.ids)} ec(s)", module=LOG_MODULE_STR)
