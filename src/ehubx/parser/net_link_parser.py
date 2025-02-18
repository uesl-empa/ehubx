import os
from typing import Optional, Tuple
from ehubx.core import logging
from ehubx.data.stage_data import Stages, StageId
from ehubx.data.ec_data import EcId
from ehubx.data.hub_data import HubId
from ehubx.data.net_link_data import NetworkLinks, NetLinkId, NetLinkDirection
from ehubx.data.time_data import TimeId
from ehubx.parser import csv_parser
from ehubx.parser import yaml_parser
from ehubx.parser import exceptions

# YAML keys
YAMLKEY_AVAILABILITY = "availability"
YAMLKEY_BIDIRECTIONAL = "bidirectional"
YAMLKEY_CAPMAX = "cap_max"
YAMLKEY_CAPMIN = "cap_min"
YAMLKEY_ECPARAMS = "ec_params"
YAMLKEY_ECID = "ec_id"
YAMLKEY_ECS = "ecs"
YAMLKEY_ENDHUBS = "end_hubs"
YAMLKEY_ENDHUBID = "end_hub_id"
YAMLKEY_LENGTH = "length"
YAMLKEY_NETLINKID = "net_link_id"
YAMLKEY_NETLINKS = "net_links"
YAMLKEY_PROFILEPATH = "profile_path"
YAMLKEY_STARTHUBS = "start_hubs"
YAMLKEY_STARTHUBID = "start_hub_id"
YAMLKEY_SUMMAXBACKWARD = "sum_max_backward"
YAMLKEY_SUMMAXFORWARD = "sum_max_forward"
YAMLKEY_SUMMINBACKWARD = "sum_min_backward"
YAMLKEY_SUMMINFORWARD = "sum_min_forward"

# Literals
LOG_MODULE_STR: str = "pars/net_link"
FILENAME_NETLINKS = "network_links.yaml"
FILETYPE_NETLINKS = "network_links"
FILETYPE_NETLINKPROFILE = "network link profile"


def parse(network_subpath: str, stages: Stages
          ) -> Tuple[NetworkLinks, Optional[yaml_parser.YamlNode]]:
    # Create links
    net_links = NetworkLinks()
    # Parse file
    net_link_file_path = os.path.join(network_subpath, FILENAME_NETLINKS)
    net_link_root_node = yaml_parser.parse(net_link_file_path)
    # File does not exist or is empty
    if net_link_root_node is None:
        return net_links, net_link_root_node
    yaml_parser.check_node_type(net_link_root_node,
                                yaml_parser.YamlNodeKind.DICT)
    # Level 0: start_hubs
    start_hubs_node = net_link_root_node[YAMLKEY_STARTHUBS]
    if start_hubs_node is None:
        return net_links, net_link_root_node
    yaml_parser.check_node_type(start_hubs_node, yaml_parser.YamlNodeKind.LIST)
    start_hubs_node.set_id(YAMLKEY_STARTHUBID)
    for start_hub_node in start_hubs_node:
        start_hub_id_str = \
            yaml_parser.parse_mandatory_str_value_from_dict_node(
                start_hub_node, YAMLKEY_STARTHUBID)
        start_hub_id = HubId(start_hub_id_str)
        # Level 1: end_hubs
        end_hubs_node = start_hub_node[YAMLKEY_ENDHUBS]
        if end_hubs_node is None:
            continue
        yaml_parser.check_node_type(end_hubs_node,
                                    yaml_parser.YamlNodeKind.LIST)
        end_hubs_node.set_id(YAMLKEY_ENDHUBID)
        for end_hub_node in end_hubs_node:
            end_hub_id_str = \
                yaml_parser.parse_mandatory_str_value_from_dict_node(
                    end_hub_node, YAMLKEY_ENDHUBID)
            end_hub_id = HubId(end_hub_id_str)
            # Level 2: net_links
            links_node = end_hub_node[YAMLKEY_NETLINKS]
            if links_node is None:
                continue
            yaml_parser.check_node_type(links_node,
                                        yaml_parser.YamlNodeKind.LIST)
            links_node.set_id(YAMLKEY_NETLINKID)
            for link_node in links_node:
                _parse_link_primary(link_node, start_hub_id, end_hub_id,
                                    net_links, stages)
    # Logging
    _log(net_links)
    # Return
    return net_links, net_link_root_node


def _parse_link_primary(link_node: yaml_parser.YamlDictNode,
                        start_hub_id: HubId, end_hub_id: HubId,
                        net_links: NetworkLinks, stages: Stages) -> None:
    # id
    link_id_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        link_node, YAMLKEY_NETLINKID)
    link_id = NetLinkId(link_id_str)
    net_links.add_id(link_id)
    # start_hub and end_hub
    net_links.set_hub_start(link_id, start_hub_id)
    net_links.set_hub_end(link_id, end_hub_id)
    # ecs
    ecs_node = yaml_parser.get_mandatory_subnode_from_dict_node(link_node,
        YAMLKEY_ECS)
    yaml_parser.check_node_type(ecs_node, yaml_parser.YamlNodeKind.LIST)
    if len(ecs_node) == 0:
        raise exceptions.EmptyListNodeException(link_node.file_path,
                                                ecs_node.node_path_as_str,
                                                module=LOG_MODULE_STR)
    for ec_node in ecs_node:
        yaml_parser.check_node_type(ec_node, yaml_parser.YamlNodeKind.VALUE)
        ec_id = EcId(yaml_parser.parse_str_from_value_node(ec_node))
        net_links.add_ec(link_id, ec_id)
    # length
    length = yaml_parser.parse_mandatory_float_value_from_dict_node(
        link_node, YAMLKEY_LENGTH)
    net_links.set_length(link_id, length)
    # bidirectional
    bidirectional = yaml_parser.parse_optional_bool_value_from_dict_node(
        link_node, YAMLKEY_BIDIRECTIONAL)
    if bidirectional is not None:
        net_links.set_bidirectional(link_id, bidirectional)
    # ec_params
    ec_params_node = link_node[YAMLKEY_ECPARAMS]
    if ec_params_node is not None:
        yaml_parser.check_node_type(ec_params_node,
                                    yaml_parser.YamlNodeKind.LIST)
        ec_params_node.set_id(YAMLKEY_ECID)
        for ec_node in ec_params_node:
            _parse_ec_params(ec_node, link_id, net_links, stages)


def _parse_ec_params(ec_node: yaml_parser.YamlDictNode,
                     link_id: NetLinkId, net_links: NetworkLinks,
                     stages: Stages) -> None:
    # ec_id
    ec_id_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        ec_node, YAMLKEY_ECID)
    ec_id = EcId(ec_id_str)
    # cap_min
    cap_min = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        ec_node, YAMLKEY_CAPMIN, stages)
    if cap_min is not None:
        for stage_id, value in cap_min.items():
            net_links.set_cap_min(stage_id, link_id, ec_id, value)
    # cap_max
    cap_max = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        ec_node, YAMLKEY_CAPMAX, stages)
    if cap_max is not None:
        for stage_id, value in cap_max.items():
            net_links.set_cap_max(stage_id, link_id, ec_id, value)
    # sum_min_forward
    sum_min_forward = \
        yaml_parser.parse_optional_yeardep_float_from_dict_node(
            ec_node, YAMLKEY_SUMMINFORWARD, stages)
    if sum_min_forward is not None:
        for stage_id, value in sum_min_forward.items():
            net_links.set_sum_min(stage_id, link_id, ec_id,
                                  NetLinkDirection.FORWARD, value)
    # sum_min_backward
    sum_min_backward = \
        yaml_parser.parse_optional_yeardep_float_from_dict_node(
            ec_node, YAMLKEY_SUMMINBACKWARD, stages)
    if sum_min_backward is not None:
        for stage_id, value in sum_min_backward.items():
            net_links.set_sum_min(stage_id, link_id, ec_id,
                                  NetLinkDirection.BACKWARD, value)
    # availability
    availability = \
        yaml_parser.parse_optional_yeardep_float_from_dict_node(
            ec_node, YAMLKEY_AVAILABILITY, stages)
    if availability is not None:
        for stage_id, value in availability.items():
            net_links.set_availability_def(stage_id, link_id, ec_id, value)
    # sum_max_forward
    sum_max_forward = \
        yaml_parser.parse_optional_yeardep_float_from_dict_node(
            ec_node, YAMLKEY_SUMMAXFORWARD, stages)
    if sum_max_forward is not None:
        for stage_id, value in sum_max_forward.items():
            net_links.set_sum_max(stage_id, link_id, ec_id,
                                  NetLinkDirection.FORWARD, value)
    # sum_max_backward
    sum_max_backward = \
        yaml_parser.parse_optional_yeardep_float_from_dict_node(
            ec_node, YAMLKEY_SUMMAXBACKWARD, stages)
    if sum_max_backward is not None:
        for stage_id, value in sum_max_backward.items():
            net_links.set_sum_max(stage_id, link_id, ec_id,
                                  NetLinkDirection.BACKWARD, value)
    # profiles
    _parse_net_link_ec_profiles(ec_node, link_id, ec_id, net_links)


def _parse_net_link_ec_profiles(ec_node: yaml_parser.YamlNode,
                                link_id: NetLinkId, ec_id: EcId,
                                net_links: NetworkLinks) -> None:
    profile_path = yaml_parser.parse_optional_str_value_from_dict_node(
        ec_node, YAMLKEY_PROFILEPATH)
    if profile_path is not None:
        profile_path = os.path.abspath(os.path.join(
            ec_node.file_path, os.pardir, profile_path))
        yaml_parser.check_file_exists(profile_path, FILETYPE_NETLINKPROFILE)
        df = csv_parser.parse(profile_path,
                              header_ids=[csv_parser.HeaderId.STAGEID,
                                          csv_parser.HeaderId.NETLINKID,
                                          csv_parser.HeaderId.ECID,
                                          csv_parser.HeaderId.PROFILEKEY])
        for (s, li, e, profile_key) in df.columns:
            if li != link_id.key:
                continue
            if e != ec_id.key:
                continue
            stage_id = StageId(s)
            if profile_key == YAMLKEY_AVAILABILITY:
                for t in df.index:
                    net_links.set_availability(stage_id, link_id, ec_id,
                        TimeId(t), df[s, li, e, profile_key][t])


def _log(net_links: NetworkLinks) -> None:
    logging.log_file(f"Parsed {len(net_links.ids)} link(s)",
                     module=LOG_MODULE_STR)
    for li in net_links.ids:
        connecting_symbol = "<->" if net_links.is_bidirectional(li) else "-->"
        link_hub_str = (f"  Link {li}: {net_links.get_hub_start(li)} "
                        f"{connecting_symbol} {net_links.get_hub_end(li)}, "
                        f"ecs = {net_links.get_ecs(li)}, "
                        f"length = {net_links.get_length(li)}")
        logging.log_file(link_hub_str, print_time=False)
