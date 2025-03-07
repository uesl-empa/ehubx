import os
from typing import Optional

from ehubx.data.ebm_tech_data import EbmTechs
from ehubx.data.ec_data import EcId
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.tech_data import TechId
from ehubx.data.time_data import TimeId
from ehubx.parser import csv_parser, hub_parser, tech_parser, yaml_parser


# YAML keys
YAMLKEY_EBMPARAMS = "ebm_params"
YAMLKEY_EC = "ec"
YAMLKEY_INEFF = "in_eff"
YAMLKEY_OUTEFF = "out_eff"
YAMLKEY_STANDBYLOSS = "standby_loss"
YAMLKEY_SOCMIN = "soc_min"
YAMLKEY_SOCMAX = "soc_max"
YAMLKEY_SOCINIT = "soc_init"
YAMLKEY_STORAGECAP = "storage_cap"
YAMLKEY_NUMVEHICLES = "num_vehicles"
YAMLKEY_CHARGEMAX = "charge_max"
YAMLKEY_DISCHARGEMAX = "discharge_max"
YAMLKEY_DISCHARGECONTROL = "discharge_controllability"
YAMLKEY_DEMANDMODIFIER = "demand_modifier"
YAMLKEY_DEMANDNOMINAL = "demand_nominal"
YAMLKEY_AVAILABILITY = "availability"
YAMLKEY_PROFILEPATH = "profile_path"

# Literals
FILETYPE_EBMPROFILE = "EBM profile"


def parse_primary(
    tech_root_node: Optional[yaml_parser.YamlNode], stages: Stages
) -> EbmTechs:
    ebm_techs = EbmTechs()
    if tech_root_node is None:
        return ebm_techs
    techs_node = tech_root_node[tech_parser.YAMLKEY_TECHS]
    if techs_node is None:
        return ebm_techs
    for tech_node in techs_node:
        _parse_ebm_tech_primary(tech_node, stages, ebm_techs)
    return ebm_techs


def _parse_ebm_tech_primary(
    tech_node: yaml_parser.YamlDictNode, stages: Stages, ebm_techs: EbmTechs
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
    if tech_type != tech_parser.TechType.EBM.value:
        return
    # Add id
    ebm_techs.add_id(tech_id)
    # ebm_params
    ebm_params_node = yaml_parser.get_mandatory_subnode_from_dict_node(
        tech_node, YAMLKEY_EBMPARAMS
    )
    yaml_parser.check_node_type(ebm_params_node, yaml_parser.YamlNodeKind.DICT)
    # ec_id
    ec_id_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        ebm_params_node, YAMLKEY_EC
    )
    ec_id = EcId(ec_id_str)
    ebm_techs.set_ec(tech_id, ec_id)
    # in_eff
    in_eff = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        ebm_params_node, YAMLKEY_INEFF, stages
    )
    if in_eff is not None:
        for stage_id, value in in_eff.items():
            ebm_techs.set_in_eff(stage_id, tech_id, value)
    # out_eff
    out_eff = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        ebm_params_node, YAMLKEY_OUTEFF, stages
    )
    if out_eff is not None:
        for stage_id, value in out_eff.items():
            ebm_techs.set_out_eff(stage_id, tech_id, value)
    # standby_loss
    standby_loss = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        ebm_params_node, YAMLKEY_STANDBYLOSS, stages
    )
    if standby_loss is not None:
        for stage_id, value in standby_loss.items():
            ebm_techs.set_standby_loss(stage_id, tech_id, value)
    # soc_min
    soc_min = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        ebm_params_node, YAMLKEY_SOCMIN, stages
    )
    if soc_min is not None:
        for stage_id, value in soc_min.items():
            ebm_techs.set_soc_min(stage_id, tech_id, value)
    # soc_max
    soc_max = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        ebm_params_node, YAMLKEY_SOCMAX, stages
    )
    if soc_max is not None:
        for stage_id, value in soc_max.items():
            ebm_techs.set_soc_max(stage_id, tech_id, value)
    # storage_cap
    storage_cap = yaml_parser.parse_mandatory_yeardep_float_from_dict_node(
        ebm_params_node, YAMLKEY_STORAGECAP, stages
    )
    for stage_id, value in storage_cap.items():
        ebm_techs.set_storage_cap(stage_id, tech_id, value)
    # charge_max
    charge_max = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        ebm_params_node, YAMLKEY_CHARGEMAX, stages
    )
    if charge_max is not None:
        for stage_id, value in charge_max.items():
            ebm_techs.set_charge_max(stage_id, tech_id, value)
    # discharge_max
    discharge_max = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        ebm_params_node, YAMLKEY_DISCHARGEMAX, stages
    )
    if discharge_max is not None:
        for stage_id, value in discharge_max.items():
            ebm_techs.set_discharge_max(stage_id, tech_id, value)
    # discharge_control
    discharge_control = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        ebm_params_node, YAMLKEY_DISCHARGECONTROL, stages
    )
    if discharge_control is not None:
        for stage_id, value in discharge_control.items():
            ebm_techs.set_discharge_control(stage_id, tech_id, value)


def parse_secondary(
    hub_root_node: Optional[yaml_parser.YamlNode], stages: Stages, ebm_techs: EbmTechs
) -> None:
    if hub_root_node is None:
        return
    hubs_node = hub_root_node[hub_parser.YAMLKEY_HUBS]
    if hubs_node is None:
        return
    for hub_node in hubs_node:
        _parse_hub_secondary(hub_node, stages, ebm_techs)


def _parse_hub_secondary(
    hub_node: yaml_parser.YamlDictNode, stages: Stages, ebm_techs: EbmTechs
) -> None:
    # id
    hub_id_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        hub_node, hub_parser.YAMLKEY_HUBID
    )
    hub_id = HubId(hub_id_str)
    techs_node = hub_node[tech_parser.YAMLKEY_TECHS]
    if techs_node is None:
        return
    for tech_id in ebm_techs.ids:
        tech_node = techs_node[tech_id.key]
        if tech_node is None:
            continue
        _parse_tech_secondary(tech_node, hub_id, tech_id, stages, ebm_techs)


def _parse_tech_secondary(
    tech_node: yaml_parser.YamlDictNode,
    hub_id: HubId,
    tech_id: TechId,
    stages: Stages,
    ebm_techs: EbmTechs,
) -> None:
    # ebm_params
    ebm_params_node = tech_node[YAMLKEY_EBMPARAMS]
    if ebm_params_node is None:
        return
    yaml_parser.check_node_type(ebm_params_node, yaml_parser.YamlNodeKind.DICT)
    # num_vehicles
    num_vehicles = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        ebm_params_node, YAMLKEY_NUMVEHICLES, stages
    )
    if num_vehicles is not None:
        for stage_id, value in num_vehicles.items():
            ebm_techs.set_num_vehicles(stage_id, hub_id, tech_id, value)
    # soc_init
    soc_init = yaml_parser.parse_optional_float_value_from_dict_node(
        ebm_params_node, YAMLKEY_SOCINIT
    )
    if soc_init is not None:
        ebm_techs.set_soc_init(hub_id, tech_id, soc_init)
    # demand_modifier
    demand_modifier = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        ebm_params_node, YAMLKEY_DEMANDMODIFIER, stages
    )
    if demand_modifier is not None:
        for stage_id, value in demand_modifier.items():
            ebm_techs.set_demand_modifier(stage_id, hub_id, tech_id, value)
    # demand_nominal
    demand_nominal = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        ebm_params_node, YAMLKEY_DEMANDNOMINAL, stages
    )
    if demand_nominal is not None:
        for stage_id, value in demand_nominal.items():
            ebm_techs.set_demand_nominal_def(stage_id, hub_id, tech_id, value)
    # availability
    availability = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        ebm_params_node, YAMLKEY_AVAILABILITY, stages
    )
    if availability is not None:
        for stage_id, value in availability.items():
            ebm_techs.set_availability_def(stage_id, hub_id, tech_id, value)
    # profiles
    _parse_tech_secondary_profiles(ebm_params_node, hub_id, tech_id, ebm_techs)


def _parse_tech_secondary_profiles(
    ebm_params_node: yaml_parser.YamlNode,
    hub_id: HubId,
    tech_id: TechId,
    ebm_techs: EbmTechs,
) -> None:
    profile_path = yaml_parser.parse_optional_str_value_from_dict_node(
        ebm_params_node, YAMLKEY_PROFILEPATH
    )
    if profile_path is not None:
        profile_path = os.path.abspath(
            os.path.join(ebm_params_node.file_path, os.pardir, profile_path)
        )
        yaml_parser.check_file_exists(profile_path, FILETYPE_EBMPROFILE)
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
            if profile_key == YAMLKEY_DEMANDNOMINAL:
                for t in df.index:
                    ebm_techs.set_demand_nominal(
                        stage_id,
                        hub_id,
                        tech_id,
                        TimeId(t),
                        df[s, h, x, profile_key][t],
                    )
            if profile_key == YAMLKEY_AVAILABILITY:
                for t in df.index:
                    ebm_techs.set_availability(
                        stage_id,
                        hub_id,
                        tech_id,
                        TimeId(t),
                        df[s, h, x, profile_key][t],
                    )
