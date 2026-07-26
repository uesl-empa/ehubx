import os
from datetime import datetime

from ehubx.core import logging
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.unit import CurrencyUnit, DimlessUnit, LengthUnit, MassUnit, PowerUnit
from ehubx.parser import (
    ates_parser,
    conv_tech_parser,
    demand_parser,
    ebm_tech_parser,
    ec_parser,
    exceptions,
    hp_tech_parser,
    hub_parser,
    import_export_parser,
    load_shedding_parser,
    load_shifting_parser,
    net_link_parser,
    net_tech_parser,
    self_sufficiency_parser,
    solar_parser,
    stage_parser,
    stor_tech_parser,
    tech_parser,
    time_parser,
    yaml_parser,
)


# YAML keys
YAMLKEY_SYSTEMPARAMS = "system_params"
YAMLKEY_INTERESTRATEDEF = "interest_rate_def"
YAMLKEY_TRLTHRESHOLD = "trl_threshold"
YAMLKEY_NUMTIMESHORIZON = "num_times_horizon"
YAMLKEY_CURRENCYUNIT = "currency_unit"
YAMLKEY_LENGTHUNIT = "length_unit"
YAMLKEY_MASSUNIT = "mass_unit"
YAMLKEY_POWERUNIT = "power_unit"

# Literals
LOG_MODULE_STR: str = "pars/system"
FILENAME_SYSTEM = "system.yaml"
FILETYPE_SYSTEM = "system"
DIR_BASIC = "basic"
DIR_NETWORK = "network"
DIR_RENEWABLES = "renewables"


def parse(input_path: str) -> EnergySystem:
    start_time = datetime.now()
    logging.log(
        f"Starting parsing from input files at {input_path} ...", module=LOG_MODULE_STR
    )
    energy_system = _parse_self(input_path)
    _parse_modules(input_path, energy_system)
    elapsed = datetime.now() - start_time
    logging.log(
        (f"Finished parsing. Elapsed time: {int(elapsed.total_seconds())}s"),
        module=LOG_MODULE_STR,
    )
    return energy_system


def _parse_self(input_path: str) -> EnergySystem:
    energy_system = EnergySystem()
    stage_file_path = os.path.join(input_path, DIR_BASIC, stage_parser.FILENAME_STAGES)
    yaml_parser.check_file_exists(stage_file_path, stage_parser.FILETYPE_STAGES)
    stage_root_node = yaml_parser.parse(stage_file_path)
    # Empty stage file
    if stage_root_node is None:
        raise exceptions.MissingRootNodeException(
            stage_file_path, module=LOG_MODULE_STR
        )
    yaml_parser.check_node_type(stage_root_node, yaml_parser.YamlNodeKind.DICT)
    # system_params node
    system_params_node = yaml_parser.get_mandatory_subnode_from_dict_node(
        stage_root_node, YAMLKEY_SYSTEMPARAMS
    )
    # Default interest rate
    interest_rate_def = yaml_parser.parse_mandatory_value_from_dict_node(
        system_params_node, YAMLKEY_INTERESTRATEDEF, expected_unit=DimlessUnit()
    )
    energy_system.interest_rate_def = interest_rate_def
    # TRL threshold
    trl_threshold = yaml_parser.parse_optional_value_from_dict_node(
        system_params_node, YAMLKEY_TRLTHRESHOLD, expected_unit=DimlessUnit()
    )
    if trl_threshold is not None:
        energy_system.trl_threshold = trl_threshold
    # num_times_horizon
    num_times_horizon = yaml_parser.parse_mandatory_int_from_dict_node(
        system_params_node, YAMLKEY_NUMTIMESHORIZON
    )
    energy_system.num_times_horizon = num_times_horizon
    # currency_unit
    currency_unit = yaml_parser.parse_optional_unit_from_dict_node(
        system_params_node, YAMLKEY_CURRENCYUNIT, expected_unit=CurrencyUnit.CHF
    )
    if currency_unit is not None:
        assert isinstance(currency_unit, CurrencyUnit)
        energy_system.currency_unit = currency_unit
    # length_unit
    length_unit = yaml_parser.parse_optional_unit_from_dict_node(
        system_params_node, YAMLKEY_LENGTHUNIT, expected_unit=LengthUnit.M
    )
    if length_unit is not None:
        assert isinstance(length_unit, LengthUnit)
        energy_system.length_unit = length_unit
    # mass_unit
    mass_unit = yaml_parser.parse_optional_unit_from_dict_node(
        system_params_node, YAMLKEY_MASSUNIT, expected_unit=MassUnit.KG
    )
    if mass_unit is not None:
        assert isinstance(mass_unit, MassUnit)
        energy_system.mass_unit = mass_unit
    # power_unit
    power_unit = yaml_parser.parse_optional_unit_from_dict_node(
        system_params_node, YAMLKEY_POWERUNIT, expected_unit=PowerUnit.KW
    )
    if power_unit is not None:
        assert isinstance(power_unit, PowerUnit)
        energy_system.power_unit = power_unit
    # Log
    _log(energy_system)
    # Return
    return energy_system


def _parse_modules(input_path: str, energy_system: EnergySystem) -> None:
    # Construct input directory subpaths
    basic_subpath = os.path.join(input_path, DIR_BASIC)
    network_subpath = os.path.join(input_path, DIR_NETWORK)
    renewables_subpath = os.path.join(input_path, DIR_RENEWABLES)
    # Primary parsing calls
    stages, stage_root_node = stage_parser.parse(basic_subpath)
    hubs, hub_root_node = hub_parser.parse_primary(basic_subpath)
    ecs, ec_root_node = ec_parser.parse(basic_subpath)
    net_links, net_link_root_node = net_link_parser.parse(network_subpath, stages, ecs)
    imports = import_export_parser.parse_imports(basic_subpath, ecs)
    exports = import_export_parser.parse_exports(basic_subpath, ecs)
    demands, demand_root_node = demand_parser.parse(basic_subpath, ecs)
    load_shedding = load_shedding_parser.parse(demand_root_node, ecs)
    load_shifting = load_shifting_parser.parse(demand_root_node, ecs)
    techs, tech_root_node = tech_parser.parse_initial(basic_subpath)
    conv_tech_parser.preprocess_in_ec_groups(tech_root_node, ec_root_node, techs)
    stor_techs = stor_tech_parser.parse_primary(tech_root_node, stages, ecs, techs)
    conv_techs = conv_tech_parser.parse_primary(tech_root_node, stages, ecs, techs)
    solar_techs = solar_parser.parse_techs(tech_root_node, stages, techs)
    hp_techs = hp_tech_parser.parse_primary(tech_root_node, stages, ecs, techs)
    ates_techs = ates_parser.parse_primary(tech_root_node, stages, ecs, techs)
    ebm_techs = ebm_tech_parser.parse_primary(tech_root_node, stages, ecs, techs)
    tech_parser.parse_primary(tech_root_node, techs, energy_system, stages)
    net_techs = net_tech_parser.parse_primary(
        network_subpath, energy_system, stages, ecs
    )
    ates_data = ates_parser.parse_data(hub_root_node, stages)
    solar_data = solar_parser.parse_data(renewables_subpath, ecs)
    self_sufficiency = self_sufficiency_parser.parse(stage_root_node)

    # Secondary module parsing (interdependent module parsing)
    tech_parser.parse_secondary(hub_root_node, stages, techs)
    net_tech_parser.parse_secondary(net_link_root_node, ecs, net_techs)
    conv_tech_parser.parse_secondary(hub_root_node, stages, ecs, conv_techs)
    hp_tech_parser.parse_secondary(hub_root_node, stages, hp_techs)
    ates_parser.parse_secondary(hub_root_node, stages, ates_techs)
    stor_tech_parser.parse_secondary(hub_root_node, stor_techs)
    ebm_tech_parser.parse_secondary(hub_root_node, stages, ecs, ebm_techs)
    times = time_parser.parse(energy_system.num_times_horizon)

    # Pass data classes
    energy_system.stages = stages
    energy_system.hubs = hubs
    energy_system.net_links = net_links
    energy_system.techs = techs
    energy_system.conv_techs = conv_techs
    energy_system.solar_techs = solar_techs
    energy_system.hp_techs = hp_techs
    energy_system.ates_techs = ates_techs
    energy_system.stor_techs = stor_techs
    energy_system.ebm_techs = ebm_techs
    energy_system.net_techs = net_techs
    energy_system.ecs = ecs
    energy_system.imports = imports
    energy_system.exports = exports
    energy_system.demands = demands
    energy_system.load_shedding = load_shedding
    energy_system.load_shifting = load_shifting
    energy_system.ates_data = ates_data
    energy_system.solar_data = solar_data
    energy_system.self_sufficiency = self_sufficiency
    energy_system.times = times


def _log(energy_system: EnergySystem) -> None:
    logging.log_file(
        (
            f"Parsed system settings: "
            f"TRL threshold = {energy_system.trl_threshold}, "
            f"Time horizon length = {energy_system.num_times_horizon}"
        ),
        module=LOG_MODULE_STR,
    )
