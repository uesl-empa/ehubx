import os
from typing import Dict, List, Optional, Set, Tuple

import ehubx.data.exceptions as data_exceptions
from ehubx.core import logging
from ehubx.data.conv_tech_data import ConversionTechs
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.time_data import TimeId
from ehubx.data.unit import CurrencyUnit, DimlessUnit, TimeUnit, Unit
from ehubx.data.value import Value
from ehubx.parser import csv_parser, exceptions, hub_parser, tech_parser, yaml_parser


# YAML keys
YAMLKEY_CONVERSIONPARAMS = "conversion_params"
YAMLKEY_INECS = "in_ecs"
YAMLKEY_INID = "in_id"
YAMLKEY_INPART = "in_part"
YAMLKEY_MAININEC = "main_in_ec"
YAMLKEY_OUTECS = "out_ecs"
YAMLKEY_ECID = "ec_id"
YAMLKEY_OUTEFF = "out_eff"
YAMLKEY_MAINOUTEC = "main_out_ec"
YAMLKEY_OPEXPERENERGY = "opex_per_energy"
YAMLKEY_INECGROUPS = "in_ec_groups"
YAMLKEY_ECGROUPID = "ec_group_id"
YAMLKEY_ECS = "ecs"
YAMLKEY_OUTSUMMIN = "out_sum_min"
YAMLKEY_OUTSUMMAX = "out_sum_max"
YAMLKEY_AVAILABILITY = "availability"
YAMLKEY_PROFILEPATH = "profile_path"

# Literals
LOG_MODULE_STR: str = "pars/conv_tech"
FILETYPE_CONVERSIONEFFICIENCYPROFILE = "conversion efficiency profile"
FILETYPE_CONVERSIONPROFILE = "conversion profiles"


def preprocess_in_ec_groups(
    tech_root_node: Optional[yaml_parser.YamlNode],
    ec_root_node: Optional[yaml_parser.YamlNode],
    techs: Techs,
) -> None:
    if ec_root_node is None:
        return
    in_ec_groups = _parse_in_ec_groups(ec_root_node)
    if tech_root_node is None:
        return
    techs_node = tech_root_node[tech_parser.YAMLKEY_TECHS]
    if techs_node is None:
        return
    # Prepare buffers for nodes which are to be added or removed
    tech_nodes_to_remove: Set[yaml_parser.YamlDictNode] = set()
    tech_ids_to_remove: Set[TechId] = set()
    tech_nodes_to_add: Set[yaml_parser.YamlDictNode] = set()
    extensions_log: Dict[str, Set[str]] = {}
    for tech_node in techs_node:
        # tech_id
        tech_id_str = yaml_parser.parse_mandatory_str_from_dict_node(
            tech_node, tech_parser.YAMLKEY_TECHID
        )
        # type
        tech_type = yaml_parser.parse_optional_str_from_dict_node(
            tech_node, tech_parser.YAMLKEY_TYPE
        )
        if tech_type not in [
            tech_parser.TechType.CONVERSION.value,
            tech_parser.TechType.SOLAR.value,
        ]:
            continue
        # conversion_params
        conversion_params_node = yaml_parser.get_mandatory_subnode_from_dict_node(
            tech_node, YAMLKEY_CONVERSIONPARAMS
        )
        yaml_parser.check_node_type(
            conversion_params_node, yaml_parser.YamlNodeKind.DICT
        )
        # in_ecs
        in_ecs_node = yaml_parser.get_mandatory_subnode_from_dict_node(
            conversion_params_node, YAMLKEY_INECS
        )
        yaml_parser.check_node_type(in_ecs_node, yaml_parser.YamlNodeKind.LIST)
        in_ecs_node.set_id(YAMLKEY_INID)
        # in_ecs = yaml_parser.parse_mandatory_str2float_dict_from_dict_node(
        #     conversion_params_node, YAMLKEY_INECS)
        # Extend the in_ecs by in_ec_groups
        extensions = _extend_in_ecs(in_ecs_node, in_ec_groups)
        # Extensions may result in multiple new technologies, go over these
        for new_in_ecs_node, suffixes in extensions:
            # If no suffixes exist, no extension has occured
            if len(suffixes) == 0:
                continue
            # Mark tech for later removaL
            tech_nodes_to_remove.add(tech_node)
            tech_ids_to_remove.add(TechId(tech_id_str))
            # Make new tech node for YAML tech tree and new tech
            new_tech_node = tech_node.copy()
            # Update tech_id for new node
            new_tech_id_node = yaml_parser.YamlValueNode(tech_node.file_path)
            new_tech_id_str = tech_id_str + "_" + "_".join(suffixes)
            if tech_id_str not in extensions_log:
                extensions_log[tech_id_str] = set()
            extensions_log[tech_id_str].add(new_tech_id_str)
            new_tech_id_node.set_value(new_tech_id_str)
            new_tech_node.remove_dict_child(tech_parser.YAMLKEY_TECHID)
            new_tech_node.add_dict_child(tech_parser.YAMLKEY_TECHID, new_tech_id_node)
            # Replace in_ecs for new tech node
            new_tech_node[YAMLKEY_CONVERSIONPARAMS].remove_dict_child(YAMLKEY_INECS)
            new_tech_node[YAMLKEY_CONVERSIONPARAMS].add_dict_child(
                YAMLKEY_INECS, new_in_ecs_node
            )
            # Schedule new node for later addition
            tech_nodes_to_add.add(new_tech_node)
            # Copy tech in techs data model
            techs.add_id(TechId(new_tech_id_str))
    # Remove old nodes (conversion techs)
    for tech_node in tech_nodes_to_remove:
        techs_node.remove_list_child(tech_node)
    # Remove old techs from techs data model
    for tech_id in tech_ids_to_remove:
        techs.remove_tech(tech_id)
    # Add new nodes from buffer
    for tech_node_to_add in tech_nodes_to_add:
        techs_node.add_list_child(tech_node_to_add)
    # Recalculate the node paths for the changed part of the tree
    techs_node.update_node_path()
    # Log the procedure
    if extensions_log:
        logging.log(
            f"Performed {len(extensions_log)} extension(s) of "
            "conversion techs based in input ec groups",
            module=LOG_MODULE_STR,
        )
        for x_old, x_new in extensions_log.items():
            logging.log(f"  Extension {x_old} -> {x_new}", print_time=False)


def _parse_in_ec_groups(ec_root_node: yaml_parser.YamlNode) -> Dict[str, Set[EcId]]:
    in_ec_groups: Dict[str, Set[EcId]] = {}
    in_ec_groups_node = ec_root_node[YAMLKEY_INECGROUPS]
    if in_ec_groups_node is None:
        return in_ec_groups
    yaml_parser.check_node_type(in_ec_groups_node, yaml_parser.YamlNodeKind.LIST)
    in_ec_groups_node.set_id(YAMLKEY_ECGROUPID)
    for in_ec_group_node in in_ec_groups_node:
        # ec_group_id
        ec_group_id = yaml_parser.parse_mandatory_str_from_dict_node(
            in_ec_group_node, YAMLKEY_ECGROUPID
        )
        # ecs
        ecs_node = yaml_parser.get_mandatory_subnode_from_dict_node(
            in_ec_group_node, YAMLKEY_ECS
        )
        yaml_parser.check_node_type(ecs_node, yaml_parser.YamlNodeKind.LIST)
        if len(ecs_node) == 0:
            raise exceptions.EmptyListNodeException(
                ec_root_node.file_path, ecs_node.node_path_as_str, module=LOG_MODULE_STR
            )
        ecs_str = yaml_parser.parse_str_list_from_dict_node(
            in_ec_group_node, YAMLKEY_ECS
        )
        ecs = {EcId(ec_id) for ec_id in ecs_str}
        in_ec_groups[ec_group_id] = ecs
    # Logging
    if len(in_ec_groups) > 0:
        logging.log(
            f"Detected {len(in_ec_groups)} input ec group(s):", module=LOG_MODULE_STR
        )
        for name, ecs in in_ec_groups.items():
            logging.log(f"  Group {name}: ecs {ecs}", print_time=False)
    return in_ec_groups


def _extend_in_ecs(
    in_ecs_node: yaml_parser.YamlNode, in_ec_groups: Dict[str, Set[EcId]]
) -> List[Tuple[yaml_parser.YamlListNode, List[str]]]:
    # Exit: empty list
    if len(in_ecs_node) == 0:
        return []
    # Grab random child node, remove it and go one level deeper
    pruned_in_ecs_node = in_ecs_node.copy()
    first_in_ecs_node = in_ecs_node[0]
    assert first_in_ecs_node is not None
    removed_in_id = first_in_ecs_node[YAMLKEY_INID].value
    removed_in_ec_node = pruned_in_ecs_node[removed_in_id]
    pruned_in_ecs_node.remove_list_child(removed_in_ec_node)
    extensions = _extend_in_ecs(pruned_in_ecs_node, in_ec_groups)
    # This level: Either we extend (removed_in_id is id of in_ec_group)
    # or not (removed_in_id is ec_id)
    if removed_in_id in in_ec_groups:
        new_ec_ids = [new_ec_id.key for new_ec_id in in_ec_groups[removed_in_id]]
        was_extended = True
    else:
        new_ec_ids = [removed_in_id]
        was_extended = False
    # Combine this level and sub-level: One new branch for each combination of
    # (extension branch, new_ec_id)
    extensions_new = []
    for in_ecs_node, suffixes in extensions:
        for new_ec_id in new_ec_ids:
            new_in_ecs_node = in_ecs_node.copy()
            if new_ec_id in new_in_ecs_node.ids:
                msg = "Something went wrong in the recursive in_ec preprocessing method"
                raise exceptions.ParsingException(
                    in_ecs_node.file_path, msg, module=LOG_MODULE_STR
                )
            new_suffixes = suffixes.copy()
            if was_extended:
                new_suffixes.append(new_ec_id)
            new_in_ec_node = removed_in_ec_node.copy()
            new_in_ec_node[YAMLKEY_INID].set_value(new_ec_id)
            new_in_ecs_node.add_list_child(new_in_ec_node)
            extensions_new.append((new_in_ecs_node, new_suffixes))
    # Case where sub-level returned empty list so we need to create it here
    if len(extensions_new) == 0:
        for new_ec_id in new_ec_ids:
            suffix = []
            if was_extended:
                suffix = [new_ec_id]
            new_in_ecs_node = pruned_in_ecs_node.copy()
            new_in_ec_node = removed_in_ec_node.copy()
            new_in_ec_node[YAMLKEY_INID].set_value(new_ec_id)
            new_in_ecs_node.add_list_child(new_in_ec_node)
            extensions_new.append((new_in_ecs_node, suffix))
    return extensions_new


def parse_primary(
    tech_root_node: Optional[yaml_parser.YamlNode],
    stages: Stages,
    ecs: Ecs,
    techs: Techs,
) -> ConversionTechs:
    # Create conversion techs
    conv_techs = ConversionTechs()
    # File does not exist or is empty:
    if tech_root_node is None:
        return conv_techs
    techs_node = tech_root_node[tech_parser.YAMLKEY_TECHS]
    if techs_node is None:
        return conv_techs
    for tech_node in techs_node:
        _parse_conv_tech_primary(tech_node, stages, ecs, techs, conv_techs)
    # Logging
    _log(conv_techs)
    return conv_techs


def _parse_conv_tech_primary(
    tech_node: yaml_parser.YamlDictNode,
    stages: Stages,
    ecs: Ecs,
    techs: Techs,
    conv_techs: ConversionTechs,
) -> None:
    # tech_id
    tech_id_str = yaml_parser.parse_mandatory_str_from_dict_node(
        tech_node, tech_parser.YAMLKEY_TECHID
    )
    tech_id = TechId(tech_id_str)
    # type
    tech_type = yaml_parser.parse_optional_str_from_dict_node(
        tech_node, tech_parser.YAMLKEY_TYPE
    )
    if tech_type not in {
        tech_parser.TechType.CONVERSION.value,
        tech_parser.TechType.SOLAR.value,
    }:
        return
    # Add id
    conv_techs.add_id(tech_id)
    # conversion_params
    conversion_params_node = yaml_parser.get_mandatory_subnode_from_dict_node(
        tech_node, YAMLKEY_CONVERSIONPARAMS
    )
    yaml_parser.check_node_type(conversion_params_node, yaml_parser.YamlNodeKind.DICT)
    # in_ecs and out_ecs
    _parse_in_ecs(conversion_params_node, tech_id, stages, ecs, conv_techs)
    _parse_out_ecs(conversion_params_node, tech_id, stages, ecs, conv_techs)
    # cap_unit
    out_ec_main = conv_techs.get_out_ec_main(tech_id)
    if tech_type == tech_parser.TechType.CONVERSION.value:
        cap_unit = ecs.get_unit(out_ec_main) / TimeUnit.H
        techs.set_cap_unit(tech_id, cap_unit)
    # costs
    costs_node = tech_node[tech_parser.YAMLKEY_COSTS]
    # opex_per_energy
    if costs_node is not None:
        opex_per_energy = yaml_parser.parse_optional_yeardep_value_from_dict_node(
            costs_node,
            YAMLKEY_OPEXPERENERGY,
            stages,
            expected_unit=(CurrencyUnit.CHF / ecs.get_unit(out_ec_main)),
        )
        if opex_per_energy is not None:
            for stage_id, value in opex_per_energy.items():
                conv_techs.set_opex_per_energy(stage_id, tech_id, value)


def _parse_in_ecs(
    conversion_params_node: yaml_parser.YamlNode,
    tech_id: TechId,
    stages: Stages,
    ecs: Ecs,
    conv_techs: ConversionTechs,
) -> None:
    in_ecs_node = yaml_parser.get_mandatory_subnode_from_dict_node(
        conversion_params_node, YAMLKEY_INECS
    )
    yaml_parser.check_node_type(in_ecs_node, yaml_parser.YamlNodeKind.LIST)
    in_ecs_node.set_id(YAMLKEY_INID)
    for in_ec_node in in_ecs_node:
        # in_id
        in_id_str = yaml_parser.parse_mandatory_str_from_dict_node(
            in_ec_node, YAMLKEY_INID
        )
        in_id = EcId(in_id_str)
        conv_techs.add_in_ec(tech_id, in_id, ecs.get_unit(in_id))
        # in_part:
        in_part_dict = yaml_parser.parse_mandatory_yeardep_value_from_dict_node(
            in_ec_node, YAMLKEY_INPART, stages, expected_unit=ecs.get_unit(in_id)
        )
        for stage_id, val in in_part_dict.items():
            conv_techs.set_in_part(stage_id, tech_id, in_id, val)
    # main_in_ec
    main_in_ec_str = yaml_parser.parse_optional_str_from_dict_node(
        conversion_params_node, YAMLKEY_MAININEC
    )
    if main_in_ec_str is not None:
        main_in_ec = EcId(main_in_ec_str)
        conv_techs.set_in_ec_main(tech_id, main_in_ec)


def _parse_out_ecs(
    conversion_params_node: yaml_parser.YamlNode,
    tech_id: TechId,
    stages: Stages,
    ecs: Ecs,
    conv_techs: ConversionTechs,
) -> None:
    # out_ecs
    out_ecs_node = yaml_parser.get_mandatory_subnode_from_dict_node(
        conversion_params_node, YAMLKEY_OUTECS
    )
    yaml_parser.check_node_type(out_ecs_node, yaml_parser.YamlNodeKind.LIST)
    out_ecs_node.set_id(YAMLKEY_ECID)
    for out_ec_node in out_ecs_node:
        # ec_id
        ec_id_str = yaml_parser.parse_mandatory_str_from_dict_node(
            out_ec_node, YAMLKEY_ECID
        )
        ec_id = EcId(ec_id_str)
        conv_techs.add_out_ec(tech_id, ec_id, ecs.get_unit(ec_id))
        # out_eff
        _parse_out_eff(out_ec_node, tech_id, ec_id, stages, ecs, conv_techs)
    # main_out_ec
    main_out_ec_str = yaml_parser.parse_optional_str_from_dict_node(
        conversion_params_node, YAMLKEY_MAINOUTEC
    )
    if main_out_ec_str is not None:
        main_out_ec = EcId(main_out_ec_str)
        conv_techs.set_out_ec_main(tech_id, main_out_ec)


def _parse_out_eff(
    out_ec_node: yaml_parser.YamlDictNode,
    tech_id: TechId,
    ec_id: EcId,
    stages: Stages,
    ecs: Ecs,
    conv_techs: ConversionTechs,
) -> None:
    out_eff_node = yaml_parser.get_mandatory_subnode_from_dict_node(
        out_ec_node, YAMLKEY_OUTEFF
    )
    # Unit
    expected_unit = ecs.get_unit(ec_id) / ecs.get_unit(
        conv_techs.get_in_ec_main(tech_id)
    )
    # eff_out as profile parameter
    if (
        isinstance(out_eff_node, yaml_parser.YamlValueNode)
        and isinstance(out_eff_node.value, str)
        and out_eff_node.value.endswith(".csv")
    ):
        file_path = os.path.abspath(
            os.path.join(out_ec_node.file_path, os.pardir, out_eff_node.value)
        )
        yaml_parser.check_file_exists(file_path, FILETYPE_CONVERSIONEFFICIENCYPROFILE)
        df = csv_parser.parse(
            file_path,
            header_ids=[
                csv_parser.HeaderId.STAGEID,
                csv_parser.HeaderId.TECHID,
                csv_parser.HeaderId.ECID,
            ],
        )
        for s, x, e in df.columns:
            if x != tech_id.key:
                continue
            if e != ec_id.key:
                continue
            try:
                unit = Unit.from_str(df.attrs[csv_parser.ATTR_UNIT][s, x, e])
            except data_exceptions.UnitException as ex:
                raise exceptions.ParsingException(
                    file_path,
                    f"Invalid unit '{ex.unit}' for output efficiency profile "
                    f"at (stage, tech, ec) tuple ({s}, {x}, {e})",
                    module=LOG_MODULE_STR,
                ) from ex
            if not unit.same_type_as(expected_unit):
                raise exceptions.ParsingException(
                    file_path,
                    f"Invalid unit '{unit}' for output efficiency profile "
                    f"at (stage, tech, ec) tuple ({s}, {x}, {e}): "
                    f"Expected a unit like '{expected_unit}'",
                    module=LOG_MODULE_STR,
                )
            for t in df.index:
                out_eff = df[(s, x, e)][t]
                conv_techs.set_out_eff(
                    StageId(s), tech_id, ec_id, TimeId(t), Value(out_eff, unit)
                )
        return
    # out_eff as a year-dependent value
    out_eff = yaml_parser.parse_mandatory_yeardep_value_from_dict_node(
        out_ec_node, YAMLKEY_OUTEFF, stages, expected_unit=expected_unit
    )
    for stage_id, value in out_eff.items():
        conv_techs.set_out_eff_def(stage_id, tech_id, ec_id, value)


def parse_secondary(
    hub_root_node: Optional[yaml_parser.YamlNode],
    stages: Stages,
    ecs: Ecs,
    conv_techs: ConversionTechs,
) -> None:
    if hub_root_node is None:
        return
    hubs_node = hub_root_node[hub_parser.YAMLKEY_HUBS]
    if hubs_node is None:
        return
    for hub_node in hubs_node:
        _parse_hub_secondary(hub_node, stages, ecs, conv_techs)


def _parse_hub_secondary(
    hub_node: yaml_parser.YamlNode,
    stages: Stages,
    ecs: Ecs,
    conv_techs: ConversionTechs,
) -> None:
    # id
    hub_id_str = yaml_parser.parse_mandatory_str_from_dict_node(
        hub_node, hub_parser.YAMLKEY_HUBID
    )
    hub_id = HubId(hub_id_str)
    techs_node = hub_node[tech_parser.YAMLKEY_TECHS]
    if techs_node is None:
        return
    for tech_id in conv_techs.ids:
        tech_node = techs_node[tech_id.key]
        if tech_node is None:
            continue
        _parse_tech_secondary(tech_node, hub_id, tech_id, stages, ecs, conv_techs)


def _parse_tech_secondary(
    tech_node: yaml_parser.YamlDictNode,
    hub_id: HubId,
    tech_id: TechId,
    stages: Stages,
    ecs: Ecs,
    conv_techs: ConversionTechs,
) -> None:
    # conversion_params
    conversion_params_node = tech_node[YAMLKEY_CONVERSIONPARAMS]
    if conversion_params_node is None:
        return
    yaml_parser.check_node_type(conversion_params_node, yaml_parser.YamlNodeKind.DICT)
    # out_sum_min
    main_out_ec_unit = ecs.get_unit(conv_techs.get_out_ec_main(tech_id))
    out_sum_min = yaml_parser.parse_optional_yeardep_value_from_dict_node(
        conversion_params_node,
        YAMLKEY_OUTSUMMIN,
        stages,
        expected_unit=main_out_ec_unit,
    )
    if out_sum_min is not None:
        for stage_id, value in out_sum_min.items():
            conv_techs.set_out_sum_min(stage_id, hub_id, tech_id, value)
    # out_sum_max
    out_sum_max = yaml_parser.parse_optional_yeardep_value_from_dict_node(
        conversion_params_node,
        YAMLKEY_OUTSUMMAX,
        stages,
        expected_unit=main_out_ec_unit,
    )
    if out_sum_max is not None:
        for stage_id, value in out_sum_max.items():
            conv_techs.set_out_sum_max(stage_id, hub_id, tech_id, value)
    # availability
    availability = yaml_parser.parse_optional_yeardep_value_from_dict_node(
        conversion_params_node,
        YAMLKEY_AVAILABILITY,
        stages,
        expected_unit=DimlessUnit(),
    )
    if availability is not None:
        for stage_id, value in availability.items():
            conv_techs.set_availability_def(stage_id, hub_id, tech_id, value)
    # profiles
    _parse_tech_secondary_profiles(conversion_params_node, hub_id, tech_id, conv_techs)


def _parse_tech_secondary_profiles(
    conversion_params_node: yaml_parser.YamlNode,
    hub_id: HubId,
    tech_id: TechId,
    conv_techs: ConversionTechs,
) -> None:
    profile_path = yaml_parser.parse_optional_str_from_dict_node(
        conversion_params_node, YAMLKEY_PROFILEPATH
    )
    if profile_path is not None:
        profile_path = os.path.abspath(
            os.path.join(conversion_params_node.file_path, os.pardir, profile_path)
        )
        yaml_parser.check_file_exists(profile_path, FILETYPE_CONVERSIONPROFILE)
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
            if profile_key == YAMLKEY_AVAILABILITY:
                try:
                    unit = Unit.from_str(
                        df.attrs[csv_parser.ATTR_UNIT][s, h, x, profile_key]
                    )
                except data_exceptions.UnitException as ex:
                    raise exceptions.ParsingException(
                        profile_path,
                        f"Invalid unit '{ex.unit}' for availability profile "
                        f"at (stage, hub, tech) tuple ({s}, {h}, {x})",
                        module=LOG_MODULE_STR,
                    ) from ex
                expected_unit = DimlessUnit()
                if not unit.same_type_as(expected_unit):
                    raise exceptions.ParsingException(
                        profile_path,
                        f"Invalid unit '{unit}' for availability profile "
                        f"at (stage, hub, tech) tuple ({s}, {h}, {x}): "
                        f"Expected a unit like '{expected_unit}'",
                        module=LOG_MODULE_STR,
                    )
                for t, val in df[s, h, x, profile_key].items():
                    conv_techs.set_availability(
                        stage_id, hub_id, tech_id, TimeId(t), Value(val)
                    )


def _log(conv_techs: ConversionTechs) -> None:
    logging.log_file(
        f"Parsed {len(conv_techs.ids)} conversion tech(s)", module=LOG_MODULE_STR
    )
    for x in conv_techs.ids:
        logging.log_file(
            f"  ConvTech {x}: ecs {conv_techs.get_in_ecs(x)} --> "
            f"{conv_techs.get_out_ecs(x)}",
            print_time=False,
        )
