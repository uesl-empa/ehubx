import os
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from ehubx.core import logging
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import Stages
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.unit import CurrencyUnit, DimlessUnit, MassUnit, TimeUnit
from ehubx.parser import exceptions, hub_parser, yaml_parser


# YAML keys
YAMLKEY_TECHS = "techs"
YAMLKEY_TECHID = "tech_id"
YAMLKEY_TYPE = "type"
YAMLKEY_TECHPARAMS = "tech_params"
YAMLKEY_LIFETIME = "lifetime"
YAMLKEY_UNITCAPMIN = "unit_cap_min"
YAMLKEY_TRL = "trl"
YAMLKEY_COSTS = "costs"
YAMLKEY_INTERESTRATE = "interest_rate"
YAMLKEY_ONETIMECAPEX = "one_time_capex"
YAMLKEY_CAPEXPERCAP = "capex_per_cap"
YAMLKEY_ONETIMEOPEX = "one_time_opex"
YAMLKEY_OPEXPERCAP = "opex_per_cap"
YAMLKEY_EMISSIONS = "emissions"
YAMLKEY_CO2PERCAP = "co2_per_cap"
YAMLKEY_TECHLISTS = "tech_lists"
YAMLKEY_TECHLISTID = "tech_list_id"
YAMLKEY_ALLOWEDTECHLISTS = "allowed_tech_lists"
YAMLKEY_LASTINSTYEAR = "last_inst_year"
YAMLKEY_CAPINIT = "cap_init"
YAMLKEY_CAPMIN = "cap_min"
YAMLKEY_CAPMAX = "cap_max"
YAMLKEY_AGEINIT = "age_init"
YAMLKEY_COUPLINGPARAMS = "coupling_params"
YAMLKEY_MAINTECHID = "main_tech_id"
YAMLKEY_CAPFACTOR = "cap_factor"

# Literals
LOG_MODULE_STR: str = "pars/tech"
FILENAME_TECHS = "techs.yaml"


# Tech types
class TechType(Enum):
    STORAGE = "storage"
    CONVERSION = "conversion"
    SOLAR = "solar"
    EBM = "ebm"
    HP = "heatpump"
    ATES = "ates"


def parse_initial(basic_subpath: str) -> Tuple[Techs, Optional[yaml_parser.YamlNode]]:
    # Create techs
    techs = Techs()
    # Parse file
    tech_file_path = os.path.join(basic_subpath, FILENAME_TECHS)
    tech_root_node = yaml_parser.parse(tech_file_path)
    # File does not exist or is empty
    if tech_root_node is None:
        return techs, tech_root_node
    yaml_parser.check_node_type(tech_root_node, yaml_parser.YamlNodeKind.DICT)
    # Level 0: techs
    techs_node = tech_root_node[YAMLKEY_TECHS]
    if techs_node is None:
        return techs, tech_root_node
    yaml_parser.check_node_type(techs_node, yaml_parser.YamlNodeKind.LIST)
    techs_node.set_id(YAMLKEY_TECHID)
    _preprocess_coupled_techs_primary(techs_node)
    for tech_node in techs_node:
        _parse_tech_initial(tech_node, techs)
    # Return
    return techs, tech_root_node


def parse_primary(
    tech_root_node: Optional[yaml_parser.YamlNode],
    techs: Techs,
    energy_system: EnergySystem,
    stages: Stages,
) -> None:
    # File does not exist or is empty
    if tech_root_node is None:
        return
    # Level 0: techs
    techs_node = tech_root_node[YAMLKEY_TECHS]
    if techs_node is None:
        return
    # Parsing
    for tech_node in techs_node:
        _parse_tech_primary(tech_node, energy_system, stages, techs)
    for tech_node in techs_node:
        _parse_coupled_techs(tech_node, techs)
    # Logging
    _log(techs)


def _preprocess_coupled_techs_primary(techs_node: yaml_parser.YamlListNode) -> None:
    for tech_node in techs_node:
        # Existence of coupling_params subnode determines whether tech is sub
        coupling_params_node = tech_node[YAMLKEY_COUPLINGPARAMS]
        if coupling_params_node is None:
            continue
        tech_id = yaml_parser.parse_mandatory_str_from_dict_node(
            tech_node, YAMLKEY_TECHID
        )
        yaml_parser.check_node_type(coupling_params_node, yaml_parser.YamlNodeKind.DICT)
        # Get main node
        main_tech_id = yaml_parser.parse_mandatory_str_from_dict_node(
            coupling_params_node, YAMLKEY_MAINTECHID
        )
        if tech_id == main_tech_id:
            main_tech_id_path_str = coupling_params_node[
                YAMLKEY_MAINTECHID
            ].node_path_as_str
            msg = f"Coupled tech {tech_id} references itself as main_tech_id"
            raise exceptions.InvalidValueException(
                techs_node.file_path, main_tech_id_path_str, msg, module=LOG_MODULE_STR
            )
        main_tech_node = techs_node[main_tech_id]
        if main_tech_node is None:
            node_path_str = (
                coupling_params_node.node_path_str + "|" + f"{YAMLKEY_MAINTECHID}"
            )
            invalidity_reason = (
                f"Tech id {main_tech_id} was not found " + "in techs list"
            )
            raise exceptions.InvalidValueException(
                techs_node.file_path,
                node_path_str,
                invalidity_reason,
                module=LOG_MODULE_STR,
            )
        # Get tech id
        tech_id = yaml_parser.parse_mandatory_str_from_dict_node(
            tech_node, YAMLKEY_TECHID
        )
        # Coupled sub techs must not have tech_params but take all from main
        if tech_node[YAMLKEY_TECHPARAMS] is not None:
            node_path_str = tech_node.node_path_as_str + "|" + YAMLKEY_TECHPARAMS
            invalidity_reason = (
                f"Tech {tech_id} qualifies as a coupled "
                + f"sub tech, so it must not have a {YAMLKEY_TECHPARAMS} node"
            )
            raise exceptions.InvalidValueException(
                techs_node.file_path,
                node_path_str,
                invalidity_reason,
                module=LOG_MODULE_STR,
            )
        tech_params_node = yaml_parser.get_mandatory_subnode_from_dict_node(
            main_tech_node, YAMLKEY_TECHPARAMS
        )
        yaml_parser.check_node_type(tech_params_node, yaml_parser.YamlNodeKind.DICT)
        tech_node.add_dict_child(YAMLKEY_TECHPARAMS, tech_params_node.copy())


def _parse_tech_initial(
    tech_node: yaml_parser.YamlDictNode,
    techs: Techs,
) -> None:
    # tech_id
    tech_id_str = yaml_parser.parse_mandatory_str_from_dict_node(
        tech_node, YAMLKEY_TECHID
    )
    tech_id = TechId(tech_id_str)
    techs.add_id(tech_id)


def _parse_tech_primary(
    tech_node: yaml_parser.YamlDictNode,
    energy_system: EnergySystem,
    stages: Stages,
    techs: Techs,
) -> None:
    # tech_id
    tech_id_str = yaml_parser.parse_mandatory_str_from_dict_node(
        tech_node, YAMLKEY_TECHID
    )
    tech_id = TechId(tech_id_str)
    # tech_params
    _parse_tech_params_primary(tech_node, tech_id, energy_system, stages, techs)
    # costs
    _parse_costs(tech_node, tech_id, energy_system, stages, techs)
    # emissions
    _parse_emissions(tech_node, tech_id, stages, techs)


def _parse_tech_params_primary(
    tech_node: yaml_parser.YamlDictNode,
    tech_id: TechId,
    energy_system: EnergySystem,
    stages: Stages,
    techs: Techs,
) -> None:
    # tech_params node
    tech_params_node = yaml_parser.get_mandatory_subnode_from_dict_node(
        tech_node, YAMLKEY_TECHPARAMS
    )
    yaml_parser.check_node_type(tech_params_node, yaml_parser.YamlNodeKind.DICT)
    # lifetime
    lifetime = yaml_parser.parse_mandatory_value_from_dict_node(
        tech_params_node, YAMLKEY_LIFETIME, expected_unit=TimeUnit.A
    )
    techs.set_lifetime(tech_id, lifetime)
    # trl -> add allowed stages
    trl_dict = yaml_parser.parse_optional_yeardep_value_from_dict_node(
        tech_params_node, YAMLKEY_TRL, stages, expected_unit=DimlessUnit()
    )
    if trl_dict is None:
        for stage_id in stages.ids:
            techs.add_allowed_stage(stage_id, tech_id)
    if trl_dict is not None:
        for stage_id, trl in trl_dict.items():
            if trl < energy_system.trl_threshold:
                continue
            techs.add_allowed_stage(stage_id, tech_id)
    # unit_cap_min
    unit_cap_min = yaml_parser.parse_optional_yeardep_value_from_dict_node(
        tech_params_node,
        YAMLKEY_UNITCAPMIN,
        stages,
        expected_unit=techs.get_cap_unit(tech_id),
    )
    if unit_cap_min is not None:
        for stage_id, value in unit_cap_min.items():
            techs.set_unit_cap_min(stage_id, tech_id, value)


def _parse_costs(
    tech_node: yaml_parser.YamlDictNode,
    tech_id: TechId,
    energy_system: EnergySystem,
    stages: Stages,
    techs: Techs,
) -> None:
    costs_node = tech_node[YAMLKEY_COSTS]
    if costs_node is None:
        techs.set_interest_rate(tech_id, energy_system.interest_rate_def)
        return
    yaml_parser.check_node_type(costs_node, yaml_parser.YamlNodeKind.DICT)
    # interest_rate
    interest_rate = yaml_parser.parse_optional_value_from_dict_node(
        costs_node, YAMLKEY_INTERESTRATE, expected_unit=DimlessUnit()
    )
    if interest_rate is None:
        interest_rate = energy_system.interest_rate_def
    techs.set_interest_rate(tech_id, interest_rate)
    # one_time_capex
    one_time_capex = yaml_parser.parse_optional_yeardep_value_from_dict_node(
        costs_node, YAMLKEY_ONETIMECAPEX, stages, expected_unit=CurrencyUnit.CHF
    )
    if one_time_capex is not None:
        for stage_id, value in one_time_capex.items():
            techs.set_one_time_capex(stage_id, tech_id, value)
    # capex_per_cap
    capex_per_cap = yaml_parser.parse_optional_yeardep_value_from_dict_node(
        costs_node,
        YAMLKEY_CAPEXPERCAP,
        stages,
        expected_unit=(CurrencyUnit.CHF / techs.get_cap_unit(tech_id)),
    )
    if capex_per_cap is not None:
        for stage_id, value in capex_per_cap.items():
            techs.set_capex_per_cap(stage_id, tech_id, value)
    # one_time_opex
    one_time_opex = yaml_parser.parse_optional_yeardep_value_from_dict_node(
        costs_node, YAMLKEY_ONETIMEOPEX, stages, expected_unit=CurrencyUnit.CHF
    )
    if one_time_opex is not None:
        for stage_id, value in one_time_opex.items():
            techs.set_one_time_opex(stage_id, tech_id, value)
    # opex_per_cap
    opex_per_cap = yaml_parser.parse_optional_yeardep_value_from_dict_node(
        costs_node,
        YAMLKEY_OPEXPERCAP,
        stages,
        expected_unit=(CurrencyUnit.CHF / techs.get_cap_unit(tech_id)),
    )
    if opex_per_cap is not None:
        for stage_id, value in opex_per_cap.items():
            techs.set_opex_per_cap(stage_id, tech_id, value)


def _parse_emissions(
    tech_node: yaml_parser.YamlDictNode,
    tech_id: TechId,
    stages: Stages,
    techs: Techs,
) -> None:
    """Parse embodied and operational technology emission parameters."""

    emissions_node = tech_node[YAMLKEY_EMISSIONS]

    if emissions_node is None:
        return

    yaml_parser.check_node_type(
        emissions_node,
        yaml_parser.YamlNodeKind.DICT,
    )

    # ---------------------- #
    # Embodied CO2 per cap   #
    # ---------------------- #
    co2_per_cap = yaml_parser.parse_optional_yeardep_value_from_dict_node(
        emissions_node,
        YAMLKEY_CO2PERCAP,
        stages,
        expected_unit=MassUnit.KG / techs.get_cap_unit(tech_id),
    )

    if co2_per_cap is not None:
        for stage_id, value in co2_per_cap.items():
            techs.set_co2_per_cap(
                stage_id,
                tech_id,
                value,
            )


def _parse_coupled_techs(tech_node: yaml_parser.YamlDictNode, techs: Techs) -> None:
    # Tech id
    tech_id_str = yaml_parser.parse_mandatory_str_from_dict_node(
        tech_node, YAMLKEY_TECHID
    )
    tech_id = TechId(tech_id_str)
    # coupling_params node
    coupling_params_node = tech_node[YAMLKEY_COUPLINGPARAMS]
    if coupling_params_node is None:
        return
    yaml_parser.check_node_type(coupling_params_node, yaml_parser.YamlNodeKind.DICT)
    # main_tech_id
    main_tech_id_str = yaml_parser.parse_mandatory_str_from_dict_node(
        coupling_params_node, YAMLKEY_MAINTECHID
    )
    main_tech_id = TechId(main_tech_id_str)
    techs.set_coupled_main_tech(tech_id, main_tech_id)
    # cap_factor
    cap_unit = techs.get_cap_unit(tech_id)
    cap_unit_main = techs.get_cap_unit(main_tech_id)
    cap_factor = yaml_parser.parse_mandatory_value_from_dict_node(
        coupling_params_node,
        YAMLKEY_CAPFACTOR,
        expected_unit=(cap_unit / cap_unit_main),
    )
    techs.set_coupled_cap_factor(tech_id, cap_factor)


def parse_secondary(
    hub_root_node: Optional[yaml_parser.YamlNode], stages: Stages, techs: Techs
) -> None:
    if hub_root_node is None:
        return
    hubs_node = hub_root_node[hub_parser.YAMLKEY_HUBS]
    if hubs_node is None:
        return
    tech_lists = _parse_tech_lists(hub_root_node, techs)
    for hub_node in hubs_node:
        _parse_hub_secondary(hub_node, tech_lists, stages, techs)


def _parse_hub_secondary(
    hub_node: yaml_parser.YamlNode,
    tech_lists: Dict[str, List[TechId]],
    stages: Stages,
    techs: Techs,
) -> None:
    # hub id
    hub_id_str = yaml_parser.parse_mandatory_str_from_dict_node(
        hub_node, hub_parser.YAMLKEY_HUBID
    )
    hub_id = HubId(hub_id_str)
    # allowed_tech_lists
    allowed_techs = _parse_allowed_techs(hub_node, tech_lists, hub_id, techs)
    techs_node = hub_node[YAMLKEY_TECHS]
    if techs_node is None:
        return
    yaml_parser.check_node_type(techs_node, yaml_parser.YamlNodeKind.LIST)
    techs_node.set_id(YAMLKEY_TECHID)
    _preprocess_coupled_techs_secondary(techs_node, techs)
    for tech_node in techs_node:
        _parse_tech_secondary(tech_node, hub_id, stages, techs, allowed_techs)


def _parse_allowed_techs(
    hub_node: yaml_parser.YamlNode,
    tech_lists: Dict[str, List[TechId]],
    hub_id: HubId,
    techs: Techs,
) -> Set[TechId]:
    # Get allowed techs for this hub
    allowed_tech_lists = yaml_parser.parse_str_list_from_dict_node(
        hub_node, YAMLKEY_ALLOWEDTECHLISTS
    )
    allowed_techs: Set[TechId] = set()
    for tech_list_id in allowed_tech_lists:
        if tech_list_id not in tech_lists:
            node_path_str = hub_node.node_path_as_str + "|" + YAMLKEY_ALLOWEDTECHLISTS
            invalidity_reason = (
                f"{tech_list_id} is not a known " + f"{YAMLKEY_TECHLISTID}"
            )
            raise exceptions.InvalidValueException(
                hub_node.file_path,
                node_path_str,
                invalidity_reason,
                module=LOG_MODULE_STR,
            )
        for tech_id in tech_lists[tech_list_id]:
            allowed_techs.add(tech_id)

    # Allow coupled sub techs if their main tech is allowed
    sub_techs_to_add = set()
    for main_tech_id in allowed_techs.intersection(techs.coupled_main_techs):
        sub_techs = techs.get_coupled_sub_techs(main_tech_id)
        for sub_tech_id in sub_techs:
            if sub_tech_id not in allowed_techs:
                msg = (
                    f"Added coupled sub tech {sub_tech_id} to allowed techs"
                    f" of hub {hub_id} because its main tech {main_tech_id}"
                    "is allowed there"
                )
                logging.log(msg, module=LOG_MODULE_STR)
                sub_techs_to_add.add(sub_tech_id)
    allowed_techs = allowed_techs.union(sub_techs_to_add)
    # Add allowed hubs
    for tech_id in allowed_techs:
        techs.add_allowed_hub(hub_id, tech_id)
    # Return allowed techs
    return allowed_techs


def _preprocess_coupled_techs_secondary(
    techs_node: yaml_parser.YamlNode, techs: Techs
) -> None:
    yaml_parser.check_node_type(techs_node, yaml_parser.YamlNodeKind.LIST)
    for tech_id in techs.coupled_sub_techs:
        main_tech_id = techs.get_coupled_main_tech(tech_id)
        tech_node = techs_node[tech_id.key]
        # Main tech node
        main_tech_node = techs_node[main_tech_id.key]
        if main_tech_node is None:
            continue
        main_tech_params_node = main_tech_node[YAMLKEY_TECHPARAMS]
        if main_tech_params_node is None:
            continue
        if tech_node is None:
            tech_node = yaml_parser.YamlDictNode(techs_node.file_path)
            tech_node_path = techs_node.node_path.copy()
            tech_node_path.append(tech_id.key)
            tech_node.set_node_path(tech_node_path)
            tech_node.add_child_value(YAMLKEY_TECHID, tech_id.key)
            techs_node.add_list_child(tech_node)
        # Coupled sub techs must not have tech_params but take all from main
        if tech_node[YAMLKEY_TECHPARAMS] is not None:
            node_path_str = tech_node.node_path_as_str + "|" + YAMLKEY_TECHPARAMS
            invalidity_reason = (
                f"Tech {tech_id} qualifies as a coupled "
                + f"sub tech, so it must not have a {YAMLKEY_TECHPARAMS} node"
            )
            raise exceptions.InvalidValueException(
                techs_node.file_path,
                node_path_str,
                invalidity_reason,
                module=LOG_MODULE_STR,
            )
        # Construct tech_params node based on main tech entries
        new_tech_params_node = yaml_parser.YamlDictNode(techs_node.file_path)
        # cap_init
        cap_init_main = yaml_parser.parse_optional_value_from_dict_node(
            main_tech_params_node,
            YAMLKEY_CAPINIT,
            expected_unit=techs.get_cap_unit(main_tech_id),
        )
        if cap_init_main is not None:
            cap_init = techs.get_coupled_cap_factor(tech_id) * cap_init_main
            new_tech_params_node.add_child_value(YAMLKEY_CAPINIT, str(cap_init))
        # age_init
        age_init_main = yaml_parser.parse_optional_value_from_dict_node(
            main_tech_params_node, YAMLKEY_AGEINIT, expected_unit=TimeUnit.A
        )
        if age_init_main is not None:
            age_init = age_init_main
            new_tech_params_node.add_child_value(YAMLKEY_AGEINIT, str(age_init))
        # last_inst_year
        last_inst_year_main = yaml_parser.parse_optional_value_from_dict_node(
            main_tech_params_node, YAMLKEY_LASTINSTYEAR, expected_unit=DimlessUnit()
        )
        if last_inst_year_main is not None:
            last_inst_year = last_inst_year_main
            new_tech_params_node.add_child_value(YAMLKEY_LASTINSTYEAR, last_inst_year)
        # cap_min & cap_max are not set for coupled techs
        # Add tech node to techs_node
        tech_node.add_dict_child(YAMLKEY_TECHPARAMS, new_tech_params_node)
        tech_node.update_node_path()


def _parse_tech_secondary(
    tech_node: yaml_parser.YamlDictNode,
    hub_id: HubId,
    stages: Stages,
    techs: Techs,
    allowed_techs: Set[TechId],
) -> None:
    # tech_id
    tech_id_str = yaml_parser.parse_mandatory_str_from_dict_node(
        tech_node, YAMLKEY_TECHID
    )
    tech_id = TechId(tech_id_str)
    # Warning: Specifying tech params if tech is not allowed
    if tech_id not in allowed_techs:
        msg = (
            f"Parsing irregularity in file {tech_node.file_path}: "
            f"Encountered tech parameter block for tech {tech_id} in "
            f"hub {hub_id} (node path {tech_node.node_path_as_str}) "
            f"even though the tech is not allowed in this hub"
        )
        logging.log_warning(msg, module=LOG_MODULE_STR)
    # tech_params
    tech_params_node = tech_node[YAMLKEY_TECHPARAMS]
    if tech_params_node is None:
        return
    yaml_parser.check_node_type(tech_params_node, yaml_parser.YamlNodeKind.DICT)
    # last_inst_year
    last_inst_year = yaml_parser.parse_optional_float_from_dict_node(
        tech_params_node, YAMLKEY_LASTINSTYEAR
    )
    if last_inst_year is not None:
        techs.set_last_inst_year(hub_id, tech_id, last_inst_year)
    # cap_init
    cap_init = yaml_parser.parse_optional_value_from_dict_node(
        tech_params_node, YAMLKEY_CAPINIT, expected_unit=techs.get_cap_unit(tech_id)
    )
    if cap_init is not None:
        techs.set_cap_init(hub_id, tech_id, cap_init)
    # age_init
    age_init = yaml_parser.parse_optional_value_from_dict_node(
        tech_params_node, YAMLKEY_AGEINIT, expected_unit=TimeUnit.A
    )
    if age_init is not None:
        techs.set_age_init(hub_id, tech_id, age_init)
    # cap_min
    cap_min = yaml_parser.parse_optional_yeardep_value_from_dict_node(
        tech_params_node,
        YAMLKEY_CAPMIN,
        stages,
        expected_unit=techs.get_cap_unit(tech_id),
    )
    if cap_min is not None:
        for stage_id, value in cap_min.items():
            techs.set_cap_min(stage_id, hub_id, tech_id, value)
    # cap_max
    cap_max = yaml_parser.parse_optional_yeardep_value_from_dict_node(
        tech_params_node,
        YAMLKEY_CAPMAX,
        stages,
        expected_unit=techs.get_cap_unit(tech_id),
    )
    if cap_max is not None:
        for stage_id, value in cap_max.items():
            techs.set_cap_max(stage_id, hub_id, tech_id, value)


def _parse_tech_lists(
    hub_root_node: yaml_parser.YamlNode, techs: Techs
) -> Dict[str, List[TechId]]:
    tech_lists: Dict[str, List[TechId]] = {}
    tech_lists_node = hub_root_node[YAMLKEY_TECHLISTS]
    if tech_lists_node is None:
        return tech_lists
    yaml_parser.check_node_type(tech_lists_node, yaml_parser.YamlNodeKind.LIST)
    tech_lists_node.set_id(YAMLKEY_TECHLISTID)
    for tech_list_node in tech_lists_node:
        tech_list_id = yaml_parser.parse_mandatory_str_from_dict_node(
            tech_list_node, YAMLKEY_TECHLISTID
        )
        techs_in_list = yaml_parser.parse_str_list_from_dict_node(
            tech_list_node, YAMLKEY_TECHS
        )
        for tech_id_str in techs_in_list:
            tech_id = TechId(tech_id_str)
            if tech_id not in techs.ids:
                logging.log_warning(
                    f"Unknown tech {tech_id} at "
                    f"{tech_list_node.node_path_as_str} in file "
                    f"{tech_list_node.file_path}",
                    module=LOG_MODULE_STR,
                )

        tech_lists[tech_list_id] = [TechId(tech) for tech in techs_in_list]
    return tech_lists


def _log(techs: Techs) -> None:
    logging.log_file(f"Parsed {len(techs.ids)} tech(s)", module=LOG_MODULE_STR)
    for x in techs.ids:
        logging.log_file(
            f"  Tech {x}: Lifetime = {techs.get_lifetime(x)}", print_time=False
        )
