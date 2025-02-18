import os
from typing import Dict, List, Optional, Set
from ehubx.core import logging
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.stage_data import Stages
from ehubx.data.net_link_data import NetLinkId
from ehubx.data.net_tech_data import NetworkTechs, NetTechId
from ehubx.data.ec_data import EcId
from ehubx.parser import net_link_parser
from ehubx.parser import yaml_parser
from ehubx.parser import exceptions

# YAML keys
YAMLKEY_ALLOWEDNETTECHLISTS = "allowed_net_tech_lists"
YAMLKEY_NETTECHS = "net_techs"
YAMLKEY_NETTECHID = "net_tech_id"
YAMLKEY_NETTECHLISTID = "net_tech_list_id"
YAMLKEY_NETTECHLISTS = "net_tech_lists"
YAMLKEY_NETTECHS = "net_techs"
YAMLKEY_EC = "ec"
YAMLKEY_LIFETIME = "lifetime"
YAMLKEY_TRL = "trl"
YAMLKEY_TRANSLOSS = "trans_loss"
YAMLKEY_UNITCAPMIN = "unit_cap_min"
YAMLKEY_COSTS = "costs"
YAMLKEY_INTERESTRATE = "interest_rate"
YAMLKEY_ONETIMECAPEX = "one_time_capex"
YAMLKEY_CAPEXPERCAP = "capex_per_cap"
YAMLKEY_ONETIMEOPEX = "one_time_opex"
YAMLKEY_OPEXPERCAP = "opex_per_cap"
YAMLKEY_OPEXPERENERGY = "opex_per_energy"
YAMLKEY_EMISSIONS = "emissions"
YAMLKEY_CO2PERCAP = "co2_per_cap"
YAMLKEY_CO2PERENERGY = "co2_per_energy"
YAMLKEY_NETTECHPARAMS = "net_tech_params"
YAMLKEY_CAPINIT = "cap_init"
YAMLKEY_AGEINIT = "age_init"

# Literals
LOG_MODULE_STR: str = "pars/net_tech"
FILENAME_NETTECHS = "network_techs.yaml"
FILETYPE_NETTECHS = "network_techs"


def parse_primary(network_subpath: str, energy_system: EnergySystem,
                  stages: Stages) -> NetworkTechs:
    # Create network techs
    net_techs = NetworkTechs()
    # Parse file
    net_tech_file_path = os.path.join(network_subpath, FILENAME_NETTECHS)
    root_node = yaml_parser.parse(net_tech_file_path)
    # File does not exist or is empty
    if root_node is None:
        return net_techs
    yaml_parser.check_node_type(root_node, yaml_parser.YamlNodeKind.DICT)
    # Level 0: net_techs
    net_techs_node = root_node[YAMLKEY_NETTECHS]
    if net_techs_node is None:
        return net_techs
    yaml_parser.check_node_type(net_techs_node, yaml_parser.YamlNodeKind.LIST)
    net_techs_node.set_id(YAMLKEY_NETTECHID)
    for net_tech_node in net_techs_node:
        _parse_net_tech_primary(net_tech_node, energy_system, stages,
                                net_techs)
    # Logging
    _log(net_techs)
    # Return
    return net_techs


def _parse_net_tech_primary(net_tech_node: yaml_parser.YamlDictNode,
                            energy_system: EnergySystem, stages: Stages,
                            net_techs: NetworkTechs) -> None:
    # net_tech_id
    net_tech_id_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        net_tech_node, YAMLKEY_NETTECHID)
    net_tech_id = NetTechId(net_tech_id_str)
    net_techs.add_id(net_tech_id)
    # ec
    ec = EcId(yaml_parser.parse_mandatory_str_value_from_dict_node(
        net_tech_node, YAMLKEY_EC))
    net_techs.set_ec(net_tech_id, ec)
    # lifetime
    lifetime = yaml_parser.parse_mandatory_int_value_from_dict_node(
        net_tech_node, YAMLKEY_LIFETIME)
    net_techs.set_lifetime(net_tech_id, lifetime)
    # trl -> add allowed stages
    trl_dict = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        net_tech_node, YAMLKEY_TRL, stages)
    if trl_dict is None:
        for stage_id in stages.ids:
            net_techs.add_allowed_stage(stage_id, net_tech_id)
    if trl_dict is not None:
        for stage_id, trl in trl_dict.items():
            if trl < energy_system.trl_threshold:
                continue
            net_techs.add_allowed_stage(stage_id, net_tech_id)
    # trans_loss
    trans_loss = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        net_tech_node, YAMLKEY_TRANSLOSS, stages)
    if trans_loss is not None:
        for stage_id, value in trans_loss.items():
            net_techs.set_trans_loss(stage_id, net_tech_id, value)
    # unit_cap_min
    unit_cap_min = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        net_tech_node, YAMLKEY_UNITCAPMIN, stages)
    if unit_cap_min is not None:
        for stage_id, value in unit_cap_min.items():
            net_techs.set_unit_cap_min(stage_id, net_tech_id, value)
    # costs
    _parse_costs(net_tech_node, net_tech_id, energy_system, stages, net_techs)
    # emissions
    _parse_emissions(net_tech_node, net_tech_id, stages, net_techs)


def _parse_costs(net_tech_node: yaml_parser.YamlDictNode,
                 net_tech_id: NetTechId, energy_system: EnergySystem,
                 stages: Stages, net_techs: NetworkTechs) -> None:
    costs_node = net_tech_node[YAMLKEY_COSTS]
    if costs_node is None:
        net_techs.set_interest_rate(net_tech_id,
                                    energy_system.interest_rate_def)
        return
    yaml_parser.check_node_type(costs_node, yaml_parser.YamlNodeKind.DICT)
    # interest_rate
    interest_rate = yaml_parser.parse_optional_float_value_from_dict_node(
        costs_node, YAMLKEY_INTERESTRATE)
    if interest_rate is None:
        interest_rate = energy_system.interest_rate_def
    net_techs.set_interest_rate(net_tech_id, interest_rate)
    # one_time_capex
    one_time_capex = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        costs_node, YAMLKEY_ONETIMECAPEX, stages)
    if one_time_capex is not None:
        for stage_id, value in one_time_capex.items():
            net_techs.set_one_time_capex(stage_id, net_tech_id, value)
    # capex_per_cap
    capex_per_cap = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        costs_node, YAMLKEY_CAPEXPERCAP, stages)
    if capex_per_cap is not None:
        for stage_id, value in capex_per_cap.items():
            net_techs.set_capex_per_cap(stage_id, net_tech_id, value)
    # one_time_opex
    one_time_opex = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        costs_node, YAMLKEY_ONETIMEOPEX, stages)
    if one_time_opex is not None:
        for stage_id, value in one_time_opex.items():
            net_techs.set_one_time_opex(stage_id, net_tech_id, value)
    # opex_per_cap
    opex_per_cap = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        costs_node, YAMLKEY_OPEXPERCAP, stages)
    if opex_per_cap is not None:
        for stage_id, value in opex_per_cap.items():
            net_techs.set_opex_per_cap(stage_id, net_tech_id, value)
    # opex_per_energy
    opex_per_energy = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        costs_node, YAMLKEY_OPEXPERENERGY, stages)
    if opex_per_energy is not None:
        for stage_id, value in opex_per_energy.items():
            net_techs.set_opex_per_energy(stage_id, net_tech_id, value)


def _parse_emissions(net_tech_node: yaml_parser.YamlDictNode,
                     net_tech_id: NetTechId, stages: Stages,
                     net_techs: NetworkTechs) -> None:
    emissions_node = net_tech_node[YAMLKEY_EMISSIONS]
    if emissions_node is None:
        return
    yaml_parser.check_node_type(emissions_node, yaml_parser.YamlNodeKind.DICT)
    # co2_per_cap
    co2_per_cap = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        emissions_node, YAMLKEY_CO2PERCAP, stages)
    if co2_per_cap is not None:
        for stage_id, value in co2_per_cap.items():
            net_techs.set_co2_per_cap(stage_id, net_tech_id, value)
    # co2_per_energy
    co2_per_energy = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        emissions_node, YAMLKEY_CO2PERENERGY, stages)
    if co2_per_energy is not None:
        for stage_id, value in co2_per_energy.items():
            net_techs.set_co2_per_energy(stage_id, net_tech_id, value)


def parse_secondary(link_root_node: Optional[yaml_parser.YamlNode],
                    net_techs: NetworkTechs) -> None:
    if link_root_node is None:
        return
    # net_tech_lists:
    net_tech_lists = _parse_net_tech_lists(link_root_node)
    # start_hubs
    start_hubs_node = link_root_node[net_link_parser.YAMLKEY_STARTHUBS]
    if start_hubs_node is None:
        return
    for start_hub_node in start_hubs_node:
        # end_hubs
        end_hubs_node = start_hub_node[net_link_parser.YAMLKEY_ENDHUBS]
        if end_hubs_node is None:
            continue
        for end_hub_node in end_hubs_node:
            # links
            links_node = end_hub_node[net_link_parser.YAMLKEY_NETLINKS]
            if links_node is None:
                continue
            for link_node in links_node:
                _parse_link_secondary(link_node, net_tech_lists, net_techs)


def _parse_net_tech_lists(
        link_root_node: yaml_parser.YamlNode) -> Dict[str, List[NetTechId]]:
    net_tech_lists: Dict[str, List[NetTechId]] = {}
    net_tech_lists_node = link_root_node[YAMLKEY_NETTECHLISTS]
    if net_tech_lists_node is None:
        return net_tech_lists
    yaml_parser.check_node_type(net_tech_lists_node,
                                yaml_parser.YamlNodeKind.LIST)
    net_tech_lists_node.set_id(YAMLKEY_NETTECHLISTID)
    for net_tech_list_node in net_tech_lists_node:
        net_tech_list_id = \
            yaml_parser.parse_mandatory_str_value_from_dict_node(
                net_tech_list_node, YAMLKEY_NETTECHLISTID)
        net_techs = yaml_parser.parse_str_list_from_dict_node(
            net_tech_list_node, YAMLKEY_NETTECHS)
        net_tech_lists[net_tech_list_id] = [NetTechId(net_tech)
                                            for net_tech in net_techs]
    return net_tech_lists


def _parse_link_secondary(link_node: yaml_parser.YamlDictNode,
                          net_tech_lists: Dict[str, List[NetTechId]],
                          net_techs: NetworkTechs) -> None:
    # link id
    link_id_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        link_node, net_link_parser.YAMLKEY_NETLINKID)
    link_id = NetLinkId(link_id_str)
    # allowed_net_tech_lists
    allowed_net_techs = _parse_allowed_net_techs(link_node, net_tech_lists,
                                                 link_id, net_techs)
    # net_tech_params
    net_tech_params_node = link_node[YAMLKEY_NETTECHPARAMS]
    if net_tech_params_node is not None:
        yaml_parser.check_node_type(net_tech_params_node,
                                    yaml_parser.YamlNodeKind.LIST)
        net_tech_params_node.set_id(YAMLKEY_NETTECHID)
        for net_tech_node in net_tech_params_node:
            _parse_net_tech_secondary(net_tech_node, link_id, net_techs,
                                      allowed_net_techs)


def _parse_net_tech_secondary(net_tech_node: yaml_parser.YamlDictNode,
                              link_id: NetLinkId, net_techs: NetworkTechs,
                              allowed_net_techs: Set[NetTechId]) -> None:
    # net_tech_id
    net_tech_id_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        net_tech_node, YAMLKEY_NETTECHID)
    net_tech_id = NetTechId(net_tech_id_str)
    # Warning: Specifying net_tech params if net_tech is not allowed
    if net_tech_id not in allowed_net_techs:
        msg = (f"Parsing irregularity in file {net_tech_node.file_path}: "
               "Encountered net_tech parameter block for net_tech "
               f"{net_tech_id} in net_link {link_id} (node path "
               f"{net_tech_node.node_path_as_str}) even though the net_tech "
               "is not allowed on this net_link")
        logging.log_warning(msg, module=LOG_MODULE_STR)
    # cap_init
    cap_init = yaml_parser.parse_optional_float_value_from_dict_node(
        net_tech_node, YAMLKEY_CAPINIT)
    if cap_init is not None:
        net_techs.set_cap_init(link_id, net_tech_id, cap_init)
    # age_init
    age_init = yaml_parser.parse_optional_float_value_from_dict_node(
        net_tech_node, YAMLKEY_AGEINIT)
    if age_init is not None:
        net_techs.set_age_init(link_id, net_tech_id, age_init)


def _parse_allowed_net_techs(
        link_node: yaml_parser.YamlDictNode,
        net_tech_lists: Dict[str, List[NetTechId]], link_id: NetLinkId,
        net_techs: NetworkTechs) -> Set[NetTechId]:
    # Get allowed net_techs for this link
    allowed_net_tech_lists = yaml_parser.parse_str_list_from_dict_node(
        link_node, YAMLKEY_ALLOWEDNETTECHLISTS)
    allowed_net_techs: Set[NetTechId] = set()
    for net_tech_list_id in allowed_net_tech_lists:
        if net_tech_list_id not in net_tech_lists:
            node_path_str = link_node.node_path_as_str + "|" + \
                YAMLKEY_ALLOWEDNETTECHLISTS
            invalidity_reason = f"{net_tech_list_id} is not a known " + \
                f"{YAMLKEY_NETTECHLISTID}"
            raise exceptions.InvalidValueException(link_node.file_path,
                node_path_str, invalidity_reason, module=LOG_MODULE_STR)
        for net_tech_id in net_tech_lists[net_tech_list_id]:
            allowed_net_techs.add(net_tech_id)
    # Add allowed net_links
    for net_tech_id in allowed_net_techs:
        net_techs.add_allowed_net_link(link_id, net_tech_id)
    # Return allowed net_techs
    return allowed_net_techs


def _log(net_techs: NetworkTechs) -> None:
    logging.log_file(f"Parsed {len(net_techs.ids)} network tech(s)",
                     module=LOG_MODULE_STR)
    for n in net_techs.ids:
        logging.log_file((f"  NetTech {n}: ec = {net_techs.get_ec(n)}, "
                          f"lifetime = {net_techs.get_lifetime(n)}"),
                         print_time=False)
