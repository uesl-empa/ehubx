from typing import Optional

from ehubx.core import logging
from ehubx.data.ates_data import AtesData, AtesScheduleId
from ehubx.data.ates_tech_data import AtesTechs, WellPairAreaCalcMethod
from ehubx.data.ec_data import EcId
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import Stages
from ehubx.data.tech_data import TechId
from ehubx.data.time_data import TimeId
from ehubx.parser import hub_parser, tech_parser, yaml_parser


# YAML keys
YAMLKEY_ATESPARAMS = "ates_params"
YAMLKEY_ECS = "ecs"
YAMLKEY_ELEC = "elec"
YAMLKEY_HEAT = "heat"
YAMLKEY_COOL = "cool"
YAMLKEY_DENSITIYFLUID = "density_fluid"
YAMLKEY_SPECHEATCAPFLUID = "specific_heat_capacity_fluid"
YAMLKEY_WELLRADIUS = "well_radius"
YAMLKEY_WELLPAIRAREACALCMETHOD = "well pair area calculation method"
YAMLKEY_ELECPERENERGYHEAT = "elec_per_energy_heat"
YAMLKEY_ELECPERENERGYCOOL = "elec_per_energy_cool"
YAMLKEY_ELECPERFLOWHEAT = "elec_per_flow_heat"
YAMLKEY_ELECPERFLOWCOOL = "elec_per_flow_cool"
YAMLKEY_MAXHEATOVERCOOL = "max_heat_over_cool"
YAMLKEY_MAXCOOLOVERHEAT = "max_cool_over_heat"
YAMLKEY_SCHEDULEPARAMS = "schedule_params"
YAMLKEY_SCHEDULEID = "schedule_id"
YAMLKEY_MAXPUMPWARM = "max_pump_rate_per_warm_well"
YAMLKEY_MAXPUMPCOLD = "max_pump_rate_per_cold_well"
YAMLKEY_THERMRADWARM = "thermal_radius_per_warm_well"
YAMLKEY_THERMRADCOLD = "thermal_radius_per_cold_well"
YAMLKEY_GROUNDVELO = "groundwater_velocity"
YAMLKEY_SPECHEATCAPAQ = "specific_heat_capacity_aquifer"
YAMLKEY_THICKNESSAQ = "thickness_aquifer"
YAMLKEY_HYDCONDAQ = "hydraulic_conductivity_aquifer"
YAMLKEY_STORATIVITYAQ = "storativity_aquifer"
YAMLKEY_MAXDRAWDOWN = "max_drawdown"
YAMLKEY_MAXDTWARM = "max_temperature_spread_warm"
YAMLKEY_MAXDTCOLD = "max_temperature_spread_cold"
YAMLKEY_AVAILABLEAREA = "available_area"
YAMLKEY_SCHEDULES = "schedules"
YAMLKEY_PHASEW2CSTART = "phase_w2c_start_id"
YAMLKEY_PHASEW2CEND = "phase_w2c_end_id"
YAMLKEY_PHASEC2WSTART = "phase_c2w_start_id"
YAMLKEY_PHASEC2WEND = "phase_c2w_end_id"
YAMLKEY_CAPEXPERWELLPAIR = "capex_per_well_pair"
YAMLKEY_OPEXPERWELLPAIR = "opex_per_well_pair"
YAMLKEY_CO2PERWELLPAIR = "co2_per_well_pair"

# Literals
LOG_MODULE_STR: str = "pars/ates_tech"


def parse_primary(
    tech_root_node: Optional[yaml_parser.YamlNode], stages: Stages
) -> AtesTechs:
    ates_techs = AtesTechs()
    if tech_root_node is None:
        return ates_techs
    techs_node = tech_root_node[tech_parser.YAMLKEY_TECHS]
    if techs_node is None:
        return ates_techs
    for tech_node in techs_node:
        _parse_ates_tech_primary(tech_node, stages, ates_techs)
    # [TODO]: Logging
    return ates_techs


def _parse_ates_tech_primary(
    tech_node: yaml_parser.YamlDictNode, stages: Stages, ates_techs: AtesTechs
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
    if tech_type != tech_parser.TechType.ATES.value:
        return
    # Add id
    ates_techs.add_id(tech_id)
    # ates_params
    _parse_ates_tech_params_primary(tech_node, tech_id, stages, ates_techs)
    # costs
    _parse_costs(tech_node, tech_id, stages, ates_techs)
    # emissions
    _parse_emissions(tech_node, tech_id, stages, ates_techs)


def _parse_ates_tech_params_primary(
    tech_node: yaml_parser.YamlDictNode,
    tech_id: TechId,
    stages: Stages,
    ates_techs: AtesTechs,
) -> None:
    ates_params_node = yaml_parser.get_mandatory_subnode_from_dict_node(
        tech_node, YAMLKEY_ATESPARAMS
    )
    yaml_parser.check_node_type(ates_params_node, yaml_parser.YamlNodeKind.DICT)
    # ecs
    ecs_node = yaml_parser.get_mandatory_subnode_from_dict_node(
        ates_params_node, YAMLKEY_ECS
    )
    # ec_elec
    ec_elec_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        ecs_node, YAMLKEY_ELEC
    )
    ec_elec_id = EcId(ec_elec_str)
    ates_techs.set_ec_el(tech_id, ec_elec_id)
    # ec_heat
    ec_heat_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        ecs_node, YAMLKEY_HEAT
    )
    ec_heat_id = EcId(ec_heat_str)
    ates_techs.set_ec_ht(tech_id, ec_heat_id)
    # ec_cool
    ec_cool_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        ecs_node, YAMLKEY_COOL
    )
    ec_cool_id = EcId(ec_cool_str)
    ates_techs.set_ec_co(tech_id, ec_cool_id)
    # density_fluid
    dens_fl = yaml_parser.parse_mandatory_float_value_from_dict_node(
        ates_params_node, YAMLKEY_DENSITIYFLUID
    )
    ates_techs.set_density_fluid(tech_id, dens_fl)
    # specific_heat_capacity_fluid
    spec_heat_cap_fl = yaml_parser.parse_mandatory_float_value_from_dict_node(
        ates_params_node, YAMLKEY_SPECHEATCAPFLUID
    )
    ates_techs.set_specific_heat_capacity_fluid(tech_id, spec_heat_cap_fl)
    # well_radius
    well_radius = yaml_parser.parse_optional_float_value_from_dict_node(
        ates_params_node, YAMLKEY_WELLRADIUS
    )
    if well_radius is not None:
        ates_techs.set_well_radius(tech_id, well_radius)
    # well_pair_area_calc_method
    area_calc_method_str = yaml_parser.parse_optional_str_value_from_dict_node(
        ates_params_node, YAMLKEY_WELLPAIRAREACALCMETHOD
    )
    if area_calc_method_str is not None:
        method_found: bool = False
        for area_calc_method in WellPairAreaCalcMethod:
            if area_calc_method_str == area_calc_method.value:
                ates_techs.set_well_pair_area_calc_method(tech_id, area_calc_method)
                method_found = True
            break
        if not method_found:
            logging.log_warning(
                "Encountered unknown well pair area calculation method '"
                f"{area_calc_method_str} for ATES technology {tech_id}. "
                "Using default method instead. ",
                module=LOG_MODULE_STR,
            )
    # elec_per_flow_heat
    elec_per_flow_heat = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        ates_params_node, YAMLKEY_ELECPERFLOWHEAT, stages
    )
    if elec_per_flow_heat is not None:
        for stage_id, value in elec_per_flow_heat.items():
            ates_techs.set_elec_per_flow_heat(stage_id, tech_id, value)
    # elec_per_flow_cool
    elec_per_flow_cool = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        ates_params_node, YAMLKEY_ELECPERFLOWCOOL, stages
    )
    if elec_per_flow_cool is not None:
        for stage_id, value in elec_per_flow_cool.items():
            ates_techs.set_elec_per_flow_cool(stage_id, tech_id, value)


def _parse_costs(
    tech_node: yaml_parser.YamlDictNode,
    tech_id: TechId,
    stages: Stages,
    ates_techs: AtesTechs,
) -> None:
    costs_node = tech_node[tech_parser.YAMLKEY_COSTS]
    if costs_node is None:
        return
    yaml_parser.check_node_type(costs_node, yaml_parser.YamlNodeKind.DICT)
    # capex_per_well_pair
    capex_per_well_pair = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        costs_node, YAMLKEY_CAPEXPERWELLPAIR, stages
    )
    if capex_per_well_pair is not None:
        for stage_id, value in capex_per_well_pair.items():
            ates_techs.set_capex_per_well_pair(stage_id, tech_id, value)
    # opex_per_well_pair
    opex_per_well_pair = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        costs_node, YAMLKEY_OPEXPERWELLPAIR, stages
    )
    if opex_per_well_pair is not None:
        for stage_id, value in opex_per_well_pair.items():
            ates_techs.set_opex_per_well_pair(stage_id, tech_id, value)


def _parse_emissions(
    tech_node: yaml_parser.YamlDictNode,
    tech_id: TechId,
    stages: Stages,
    ates_techs: AtesTechs,
) -> None:
    emissions_node = tech_node[tech_parser.YAMLKEY_EMISSIONS]
    if emissions_node is None:
        return
    yaml_parser.check_node_type(emissions_node, yaml_parser.YamlNodeKind.DICT)
    # co2_per_well_pair
    co2_per_well_pair = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        emissions_node, YAMLKEY_CO2PERWELLPAIR, stages
    )
    if co2_per_well_pair is not None:
        for stage_id, value in co2_per_well_pair.items():
            ates_techs.set_co2_per_well_pair(stage_id, tech_id, value)


def parse_secondary(
    hub_root_node: Optional[yaml_parser.YamlNode], stages: Stages, ates_techs: AtesTechs
) -> None:
    if hub_root_node is None:
        return
    hubs_node = hub_root_node[hub_parser.YAMLKEY_HUBS]
    if hubs_node is None:
        return
    for hub_node in hubs_node:
        _parse_hub_techs_secondary(hub_node, stages, ates_techs)


def _parse_hub_techs_secondary(
    hub_node: yaml_parser.YamlDictNode, stages: Stages, ates_techs: AtesTechs
) -> None:
    # id
    hub_id_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        hub_node, hub_parser.YAMLKEY_HUBID
    )
    hub_id = HubId(hub_id_str)
    techs_node = hub_node[tech_parser.YAMLKEY_TECHS]
    if techs_node is None:
        return
    for tech_id in ates_techs.ids:
        tech_node = techs_node[tech_id.key]
        if tech_node is None:
            continue
        _parse_tech_secondary(tech_node, hub_id, tech_id, stages, ates_techs)


def _parse_tech_secondary(
    tech_node: yaml_parser.YamlDictNode,
    hub_id: HubId,
    tech_id: TechId,
    stages: Stages,
    ates_techs: AtesTechs,
) -> None:
    # ates_params
    ates_params_node = tech_node[YAMLKEY_ATESPARAMS]
    if ates_params_node is None:
        return
    yaml_parser.check_node_type(ates_params_node, yaml_parser.YamlNodeKind.DICT)
    # elec_per_energy_heat
    elec_per_energy_heat = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        ates_params_node, YAMLKEY_ELECPERENERGYHEAT, stages
    )
    if elec_per_energy_heat is not None:
        for stage_id, value in elec_per_energy_heat.items():
            ates_techs.set_elec_per_energy_heat(stage_id, hub_id, tech_id, value)
    # elec_per_energy_cool
    elec_per_energy_cool = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        ates_params_node, YAMLKEY_ELECPERENERGYCOOL, stages
    )
    if elec_per_energy_cool is not None:
        for stage_id, value in elec_per_energy_cool.items():
            ates_techs.set_elec_per_energy_cool(stage_id, hub_id, tech_id, value)
    # schedule_params
    schedule_params_node = ates_params_node[YAMLKEY_SCHEDULEPARAMS]
    if schedule_params_node is None:
        return
    yaml_parser.check_node_type(schedule_params_node, yaml_parser.YamlNodeKind.LIST)
    schedule_params_node.set_id(YAMLKEY_SCHEDULEID)
    for schedule_node in schedule_params_node:
        # schedule_id
        schedule_id_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
            schedule_node, YAMLKEY_SCHEDULEID
        )
        schedule_id = AtesScheduleId(schedule_id_str)
        # max_pump_rate_per_warm_well
        max_pump_warm = yaml_parser.parse_optional_yeardep_float_from_dict_node(
            schedule_node, YAMLKEY_MAXPUMPWARM, stages
        )
        if max_pump_warm is not None:
            for stage_id, value in max_pump_warm.items():
                ates_techs.set_max_pump_rate_per_warm_well(
                    stage_id, hub_id, tech_id, schedule_id, value
                )
        # max_pump_rate_per_cold_well
        max_pump_cold = yaml_parser.parse_optional_yeardep_float_from_dict_node(
            schedule_node, YAMLKEY_MAXPUMPCOLD, stages
        )
        if max_pump_cold is not None:
            for stage_id, value in max_pump_cold.items():
                ates_techs.set_max_pump_rate_per_cold_well(
                    stage_id, hub_id, tech_id, schedule_id, value
                )
        # thermal_radius_per_warm_well
        therm_rad_warm = yaml_parser.parse_optional_yeardep_float_from_dict_node(
            schedule_node, YAMLKEY_THERMRADWARM, stages
        )
        if therm_rad_warm is not None:
            for stage_id, value in therm_rad_warm.items():
                ates_techs.set_thermal_radius_per_warm_well(
                    stage_id, hub_id, tech_id, schedule_id, value
                )
        # thermal_radius_per_cold_well
        therm_rad_cold = yaml_parser.parse_optional_yeardep_float_from_dict_node(
            schedule_node, YAMLKEY_THERMRADCOLD, stages
        )
        if therm_rad_cold is not None:
            for stage_id, value in therm_rad_cold.items():
                ates_techs.set_thermal_radius_per_cold_well(
                    stage_id, hub_id, tech_id, schedule_id, value
                )
        # max_heat_over_cool
        max_heat_over_cool = yaml_parser.parse_optional_yeardep_float_from_dict_node(
            schedule_node, YAMLKEY_MAXHEATOVERCOOL, stages
        )
        if max_heat_over_cool is not None:
            for stage_id, value in max_heat_over_cool.items():
                ates_techs.set_max_heat_over_cool(
                    stage_id, hub_id, tech_id, schedule_id, value
                )
        # max_cool_over_heat
        max_cool_over_heat = yaml_parser.parse_optional_yeardep_float_from_dict_node(
            schedule_node, YAMLKEY_MAXCOOLOVERHEAT, stages
        )
        if max_cool_over_heat is not None:
            for stage_id, value in max_cool_over_heat.items():
                ates_techs.set_max_cool_over_heat(
                    stage_id, hub_id, tech_id, schedule_id, value
                )


def parse_data(
    hub_root_node: Optional[yaml_parser.YamlNode], stages: Stages
) -> AtesData:
    ates_data = AtesData()
    if hub_root_node is None:
        return ates_data
    hubs_node = hub_root_node[hub_parser.YAMLKEY_HUBS]
    if hubs_node is None:
        return ates_data
    for hub_node in hubs_node:
        _parse_hub_data_secondary(hub_node, stages, ates_data)
    return ates_data


def _parse_hub_data_secondary(
    hub_node: yaml_parser.YamlDictNode, stages: Stages, ates_data: AtesData
) -> None:
    # id
    hub_id_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        hub_node, hub_parser.YAMLKEY_HUBID
    )
    hub_id = HubId(hub_id_str)
    # ates_params node
    ates_params_node = hub_node[YAMLKEY_ATESPARAMS]
    if ates_params_node is None:
        return
    # groundwater_velocity
    ground_velo = yaml_parser.parse_optional_float_value_from_dict_node(
        ates_params_node, YAMLKEY_GROUNDVELO
    )
    if ground_velo is not None:
        ates_data.set_groundwater_velocity(hub_id, ground_velo)
    # specific_heat_capacity_aquifer
    spec_heat_cap_aq = yaml_parser.parse_optional_float_value_from_dict_node(
        ates_params_node, YAMLKEY_SPECHEATCAPAQ
    )
    if spec_heat_cap_aq is not None:
        ates_data.set_specific_heat_capacity_aquifer(hub_id, spec_heat_cap_aq)
    # thickness_aquifer
    thickness_aq = yaml_parser.parse_optional_float_value_from_dict_node(
        ates_params_node, YAMLKEY_THICKNESSAQ
    )
    if thickness_aq is not None:
        ates_data.set_thickness_aquifer(hub_id, thickness_aq)
    # hydraulic_conductivity_aquifer
    hyd_cond_aq = yaml_parser.parse_optional_float_value_from_dict_node(
        ates_params_node, YAMLKEY_HYDCONDAQ
    )
    if hyd_cond_aq is not None:
        ates_data.set_hydraulic_conductivity_aquifer(hub_id, hyd_cond_aq)
    # storativity_aquifer
    storativity_aq = yaml_parser.parse_optional_float_value_from_dict_node(
        ates_params_node, YAMLKEY_STORATIVITYAQ
    )
    if storativity_aq is not None:
        ates_data.set_storativity_aquifer(hub_id, storativity_aq)
    # max_drawdown
    max_drawdown = yaml_parser.parse_optional_float_value_from_dict_node(
        ates_params_node, YAMLKEY_MAXDRAWDOWN
    )
    if max_drawdown is not None:
        ates_data.set_max_drawdown(hub_id, max_drawdown)
    # max_temperature_spread_warm
    max_dt_warm = yaml_parser.parse_optional_float_value_from_dict_node(
        ates_params_node, YAMLKEY_MAXDTWARM
    )
    if max_dt_warm is not None:
        ates_data.set_max_temperature_spread_warm(hub_id, max_dt_warm)
    # max_temperature_spread_cold
    max_dt_cold = yaml_parser.parse_optional_float_value_from_dict_node(
        ates_params_node, YAMLKEY_MAXDTCOLD
    )
    if max_dt_cold is not None:
        ates_data.set_max_temperature_spread_cold(hub_id, max_dt_cold)
    # available_area
    available_area = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        ates_params_node, YAMLKEY_AVAILABLEAREA, stages
    )
    if available_area is not None:
        for stage_id, value in available_area.items():
            ates_data.set_available_area(stage_id, hub_id, value)
    # schedules
    schedules_node = yaml_parser.get_mandatory_subnode_from_dict_node(
        ates_params_node, YAMLKEY_SCHEDULES
    )
    yaml_parser.check_node_type(schedules_node, yaml_parser.YamlNodeKind.LIST)
    schedules_node.set_id(YAMLKEY_SCHEDULEID)
    for schedule_node in schedules_node:
        _parse_schedule_data(schedule_node, hub_id, ates_data)


def _parse_schedule_data(
    schedule_node: yaml_parser.YamlNode, hub_id: HubId, ates_data: AtesData
) -> None:
    yaml_parser.check_node_type(schedule_node, yaml_parser.YamlNodeKind.DICT)
    # id
    schedule_id_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        schedule_node, YAMLKEY_SCHEDULEID
    )
    schedule_id = AtesScheduleId(schedule_id_str)
    ates_data.add_schedule_id(hub_id, schedule_id)
    # phase_w2c_start_id
    phase_w2c_start_str = yaml_parser.parse_mandatory_int_value_from_dict_node(
        schedule_node, YAMLKEY_PHASEW2CSTART
    )
    phase_w2c_start_id = TimeId(phase_w2c_start_str)
    ates_data.set_phase_w2c_start(hub_id, schedule_id, phase_w2c_start_id)
    # phase_w2c_end_id
    phase_w2c_end_str = yaml_parser.parse_mandatory_int_value_from_dict_node(
        schedule_node, YAMLKEY_PHASEW2CEND
    )
    phase_w2c_end_id = TimeId(phase_w2c_end_str)
    ates_data.set_phase_w2c_end(hub_id, schedule_id, phase_w2c_end_id)
    # phase_c2w_start_id
    phase_c2w_start_str = yaml_parser.parse_mandatory_int_value_from_dict_node(
        schedule_node, YAMLKEY_PHASEC2WSTART
    )
    phase_c2w_start_id = TimeId(phase_c2w_start_str)
    ates_data.set_phase_c2w_start(hub_id, schedule_id, phase_c2w_start_id)
    # phase_c2w_end_id
    phase_c2w_end_str = yaml_parser.parse_mandatory_int_value_from_dict_node(
        schedule_node, YAMLKEY_PHASEC2WEND
    )
    phase_c2w_end_id = TimeId(phase_c2w_end_str)
    ates_data.set_phase_c2w_end(hub_id, schedule_id, phase_c2w_end_id)
