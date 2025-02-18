import os
from typing import Optional, Tuple
from ehubx.core import logging
from ehubx.data.hub_data import Hubs, HubId
from ehubx.parser import yaml_parser


# YAML keys
YAMLKEY_HUBS = "hubs"
YAMLKEY_HUBID = "hub_id"
YAMLKEY_TECHLISTS = "tech_lists"
YAMLKEY_TECHLISTID = "tech_list_id"

# Literals
LOG_MODULE_STR: str = "parse/hub"
FILENAME_HUBS = "hubs.yaml"
FILETYPE_HUBS = "hubs"


def parse_primary(basic_subpath: str
                  ) -> Tuple[Hubs, Optional[yaml_parser.YamlNode]]:
    hubs = Hubs()
    hubs_file_path = os.path.join(basic_subpath, FILENAME_HUBS)
    if not os.path.isfile(hubs_file_path):
        return hubs, None
    hub_root_node = yaml_parser.parse(hubs_file_path)
    if hub_root_node is None:
        return hubs, hub_root_node
    hubs_node = hub_root_node[YAMLKEY_HUBS]
    if hubs_node is None:
        return hubs, hub_root_node
    yaml_parser.check_node_type(hubs_node, yaml_parser.YamlNodeKind.LIST)
    hubs_node.set_id(YAMLKEY_HUBID)
    for hub_node in hubs_node:
        _parse_hub(hub_node, hubs)
    _log(hubs)
    return hubs, hub_root_node


def _parse_hub(hub_node: yaml_parser.YamlDictNode, hubs: Hubs) -> None:
    # id
    hub_id_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        hub_node, YAMLKEY_HUBID)
    hub_id = HubId(hub_id_str)
    hubs.add_id(hub_id)


def _log(hubs: Hubs) -> None:
    logging.log_file(f"Parsed {len(hubs.ids)} hub(s): {hubs.ids}",
                     module=LOG_MODULE_STR)
