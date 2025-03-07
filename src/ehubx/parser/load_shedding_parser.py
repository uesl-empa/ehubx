import itertools
import os
from typing import Optional, Set, Tuple

from ehubx.core import logging
from ehubx.data.ec_data import EcId
from ehubx.data.hub_data import HubId
from ehubx.data.load_shedding_data import LoadShedding
from ehubx.data.stage_data import StageId
from ehubx.data.time_data import TimeId
from ehubx.parser import csv_parser, exceptions, yaml_parser


# YAML keys
YAMLKEY_LOADSHHEDDING = "load_shedding"
YAMLKEY_PRESET = "preset"
YAMLKEY_MANUAL = "manual"
YAMLKEY_STAGES = "stages"
YAMLKEY_HUBS = "hubs"
YAMLKEY_ECS = "ecs"
YAMLKEY_ENABLED = "enabled"
YAMLKEY_MAXABS = "max_abs"
YAMLKEY_MAXREL = "max_rel"
YAMLKEY_ENERGYCOST = "energy_cost"
YAMLKEY_PROFILEPATH = "profile_path"

# Literals
LOG_MODULE_STR: str = "pars/load_shed"
FILETYPE_LOADSHEDDINGPROFILE = "load_shedding profile"
DEF_ENABLED: bool = True


def parse(demand_root_node: Optional[yaml_parser.YamlNode]) -> LoadShedding:
    # Initialize data model
    load_shedding = LoadShedding()
    if demand_root_node is None:
        return load_shedding
    load_shedding_node = demand_root_node[YAMLKEY_LOADSHHEDDING]
    if load_shedding_node is None:
        return load_shedding
    yaml_parser.check_node_type(load_shedding_node, yaml_parser.YamlNodeKind.DICT)
    # Preset
    preset_node = load_shedding_node[YAMLKEY_PRESET]
    if preset_node is not None:
        yaml_parser.check_node_type(preset_node, yaml_parser.YamlNodeKind.DICT)
        _parse_preset(preset_node, load_shedding)
    # Manual
    manual_node = load_shedding_node[YAMLKEY_MANUAL]
    if manual_node is not None:
        yaml_parser.check_node_type(manual_node, yaml_parser.YamlNodeKind.LIST)
        _parse_manual(manual_node, load_shedding)
    # Logging
    _log(load_shedding)
    # Return
    return load_shedding


def _parse_preset(
    preset_node: yaml_parser.YamlDictNode, load_shedding: LoadShedding
) -> None:
    # enabled
    enabled = yaml_parser.parse_optional_bool_value_from_dict_node(
        preset_node, YAMLKEY_ENABLED
    )
    if enabled is not None:
        load_shedding.enabled_preset = enabled
    # max_abs
    max_abs = yaml_parser.parse_optional_float_value_from_dict_node(
        preset_node, YAMLKEY_MAXABS
    )
    if max_abs is not None:
        load_shedding.set_max_abs_preset(max_abs)
    # max_rel
    max_rel = yaml_parser.parse_optional_float_value_from_dict_node(
        preset_node, YAMLKEY_MAXREL
    )
    if max_rel is not None:
        load_shedding.set_max_rel_preset(max_rel)
    # energy_cost
    energy_cost = yaml_parser.parse_optional_float_value_from_dict_node(
        preset_node, YAMLKEY_ENERGYCOST
    )
    if energy_cost is not None:
        load_shedding.set_energy_cost_preset(energy_cost)


def _parse_manual(
    manual_node: yaml_parser.YamlListNode, load_shedding: LoadShedding
) -> None:
    previous_tuples: Set[Tuple[StageId, HubId, EcId]] = set()
    for node in manual_node:
        yaml_parser.check_node_type(node, yaml_parser.YamlNodeKind.DICT)
        # stages
        stages_str = yaml_parser.parse_str_list_from_dict_node(
            node, YAMLKEY_STAGES, optional=False
        )
        stages = {StageId(stage_str) for stage_str in stages_str}
        # hubs
        hubs_str = yaml_parser.parse_str_list_from_dict_node(
            node, YAMLKEY_HUBS, optional=False
        )
        hubs = {HubId(hub_str) for hub_str in hubs_str}
        # ecs
        ecs_str = yaml_parser.parse_str_list_from_dict_node(
            node, YAMLKEY_ECS, optional=False
        )
        ecs = {EcId(ec_str) for ec_str in ecs_str}
        # Id tuples
        id_tuples = set(itertools.product(stages, hubs, ecs))
        dupe_tuples = previous_tuples.intersection(id_tuples)
        if len(dupe_tuples) > 0:
            msg = (
                "Overlap detected in load shedding module: "
                + f"The (stage, hub, ec) tuples {dupe_tuples} occur in more "
                + "than one manual load shedding entry"
            )
            raise exceptions.ParsingException(
                manual_node.file_path, msg, module=LOG_MODULE_STR
            )
        # Defaults
        _parse_manual_defaults(node, id_tuples, load_shedding)
        # Profile values
        _parse_manual_profiles(node, id_tuples, load_shedding)
        # Remember encountered tuples
        previous_tuples = previous_tuples.union(id_tuples)


def _parse_manual_defaults(
    node: yaml_parser.YamlDictNode,
    id_tuples: Set[Tuple[StageId, HubId, EcId]],
    load_shedding: LoadShedding,
) -> None:
    # enabled
    enabled: bool = DEF_ENABLED
    enabled_parsed = yaml_parser.parse_optional_bool_value_from_dict_node(
        node, YAMLKEY_ENABLED
    )
    if enabled_parsed is not None:
        enabled = enabled_parsed
    # max_abs
    max_abs = yaml_parser.parse_optional_float_value_from_dict_node(
        node, YAMLKEY_MAXABS
    )
    # max_rel
    max_rel = yaml_parser.parse_optional_float_value_from_dict_node(
        node, YAMLKEY_MAXREL
    )
    # energy_cost
    energy_cost = yaml_parser.parse_optional_float_value_from_dict_node(
        node, YAMLKEY_ENERGYCOST
    )
    # Write def values to data model
    for stage_id, hub_id, ec_id in id_tuples:
        load_shedding.set_enabled(stage_id, hub_id, ec_id, enabled)
        if max_abs is not None:
            load_shedding.set_max_abs_def(stage_id, hub_id, ec_id, max_abs)
        if max_rel is not None:
            load_shedding.set_max_rel_def(stage_id, hub_id, ec_id, max_rel)
        if energy_cost is not None:
            load_shedding.set_energy_cost_def(stage_id, hub_id, ec_id, energy_cost)


def _parse_manual_profiles(
    node: yaml_parser.YamlDictNode,
    id_tuples: Set[Tuple[StageId, HubId, EcId]],
    load_shedding: LoadShedding,
) -> None:
    # profile_path
    profile_path = yaml_parser.parse_optional_str_value_from_dict_node(
        node, YAMLKEY_PROFILEPATH
    )
    if profile_path is None:
        return
    profile_path = os.path.abspath(
        os.path.join(node.file_path, os.pardir, profile_path)
    )
    yaml_parser.check_file_exists(profile_path, FILETYPE_LOADSHEDDINGPROFILE)
    df_profiles = csv_parser.parse(
        profile_path,
        header_ids=[
            csv_parser.HeaderId.STAGEID,
            csv_parser.HeaderId.HUBID,
            csv_parser.HeaderId.ECID,
            csv_parser.HeaderId.PROFILEKEY,
        ],
    )
    # Write profile values to data model
    for s, h, e, profile_key in df_profiles.columns:
        stage_id = StageId(s)
        hub_id = HubId(h)
        ec_id = EcId(e)
        if (stage_id, hub_id, ec_id) not in id_tuples:
            continue
        # max_abs
        if profile_key == YAMLKEY_MAXABS:
            for t in df_profiles.index:
                load_shedding.set_max_abs(
                    stage_id,
                    hub_id,
                    ec_id,
                    TimeId(t),
                    df_profiles[s, h, e, profile_key][t],
                )
        # max_rel
        if profile_key == YAMLKEY_MAXREL:
            for t in df_profiles.index:
                load_shedding.set_max_rel(
                    stage_id,
                    hub_id,
                    ec_id,
                    TimeId(t),
                    df_profiles[s, h, e, profile_key][t],
                )
        # energy_cost
        if profile_key == YAMLKEY_ENERGYCOST:
            for t in df_profiles.index:
                load_shedding.set_energy_cost(
                    stage_id,
                    hub_id,
                    ec_id,
                    TimeId(t),
                    df_profiles[s, h, e, profile_key][t],
                )


def _log(load_shedding: LoadShedding) -> None:
    msg = "Load shedding "
    if load_shedding.enabled_preset:
        msg += (
            f"enabled as preset (max_abs={load_shedding.max_abs_preset}, "
            f"max_rel={load_shedding.max_rel_preset}, "
            f"energy_cost={load_shedding.energy_cost_preset})"
        )
    if not load_shedding.enabled_preset:
        msg += "disabled as preset"
    if load_shedding.manual_tuples:
        msg += ". Manual tuples: "
    logging.log_file(msg, module=LOG_MODULE_STR)
    for s, h, e in load_shedding.manual_tuples:
        msg = f"  Load shedding tuple ({s}, {h}, {e}): " + (
            "Enabled" if load_shedding.is_enabled(s, h, e) else "Disabled"
        )
        logging.log_file(msg, print_time=False)
