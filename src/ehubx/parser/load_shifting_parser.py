import os
from typing import Optional
import itertools
from ehubx.core import logging
from ehubx.data.stage_data import StageId
from ehubx.data.hub_data import HubId
from ehubx.data.ec_data import EcId
from ehubx.data.load_shifting_data import LoadShifting, LoadShiftId
from ehubx.data.time_data import TimeId
from ehubx.parser import csv_parser
from ehubx.parser import yaml_parser
from ehubx.parser import exceptions

# YAML keys
YAMLKEY_LOADHSHIFTING = "load_shifting"
YAMLKEY_LOADSHIFTID = "load_shift_id"
YAMLKEY_STAGES = "stages"
YAMLKEY_HUBS = "hubs"
YAMLKEY_ECS = "ecs"
YAMLKEY_INTERVALLENGTH = "interval_length"
YAMLKEY_INTERVALCAP = "interval_cap"
YAMLKEY_MAXABOVEABS = "max_above_abs"
YAMLKEY_MAXBELOWABS = "max_below_abs"
YAMLKEY_MAXABOVEREL = "max_above_rel"
YAMLKEY_MAXBELOWREL = "max_below_rel"
YAMLKEY_ENERGYCOSTABOVE = "energy_cost_above"
YAMLKEY_ENERGYCOSTBELOW = "energy_cost_below"
YAMLKEY_PEAKCOSTABOVE = "peak_cost_above"
YAMLKEY_PEAKCOSTBELOW = "peak_cost_below"
YAMLKEY_FIXCOST = "fix_cost"
YAMLKEY_PROFILEPATH = "profile_path"

# Literals
LOG_MODULE_STR: str = "pars/load_shift"
FILETYPE_LOADSHIFTPROFILE = "loadshift profile"


def parse(demand_root_node: Optional[yaml_parser.YamlNode]) -> LoadShifting:
    # Initialize data model
    load_shifting = LoadShifting()
    if demand_root_node is None:
        return load_shifting
    load_shifts_node = demand_root_node[YAMLKEY_LOADHSHIFTING]
    if load_shifts_node is None:
        return load_shifting
    yaml_parser.check_node_type(load_shifts_node,
                                yaml_parser.YamlNodeKind.LIST)
    load_shifts_node.set_id(YAMLKEY_LOADSHIFTID)
    for load_shift_node in load_shifts_node:
        yaml_parser.check_node_type(load_shift_node,
                                    yaml_parser.YamlNodeKind.DICT)
        _parse_load_shift(load_shift_node, load_shifting)

    # Logging
    _log(load_shifting)
    # Return
    return load_shifting


def _parse_load_shift(load_shift_node: yaml_parser.YamlDictNode,
                      load_shifting: LoadShifting) -> None:
    # load_shift_id
    load_shift_id_str = yaml_parser.parse_mandatory_str_value_from_dict_node(
        load_shift_node, YAMLKEY_LOADSHIFTID)
    load_shift_id = LoadShiftId(load_shift_id_str)
    load_shifting.add_id(load_shift_id)
    # Literals
    _parse_defaults(load_shift_node, load_shift_id, load_shifting)
    # Profile values
    _parse_profiles(load_shift_node, load_shift_id, load_shifting)


def _parse_defaults(load_shift_node: yaml_parser.YamlDictNode,
                    load_shift_id: LoadShiftId,
                    load_shifting: LoadShifting) -> None:
    # stages, hubs, ecs
    stages_str = yaml_parser.parse_str_list_from_dict_node(load_shift_node,
                                                           YAMLKEY_STAGES)
    hubs_str = yaml_parser.parse_str_list_from_dict_node(load_shift_node,
                                                         YAMLKEY_HUBS)
    ecs_str = yaml_parser.parse_str_list_from_dict_node(load_shift_node,
                                                        YAMLKEY_ECS)
    stages = {StageId(stage_str) for stage_str in stages_str}
    hubs = {HubId(hub_str) for hub_str in hubs_str}
    ecs = {EcId(ec_str) for ec_str in ecs_str}
    for (stage_id, hub_id, ec_id) in itertools.product(stages, hubs, ecs):
        for other_load_shift_id in load_shifting.ids:
            if other_load_shift_id == load_shift_id:
                continue
            if ((stage_id, hub_id, ec_id)
                    in load_shifting.get_tuples(other_load_shift_id)):
                msg = ("Duplicate (stage, hub, ec) tuple detected for the "
                       f"load shifting module: {(stage_id, hub_id, ec_id)} "
                       f"occurs in load shift ids {other_load_shift_id} and "
                       f"{load_shift_id}")
                raise exceptions.ParsingException(load_shift_node.file_path,
                                                  msg, module=LOG_MODULE_STR)
    for stage_id in stages:
        load_shifting.add_stage(load_shift_id, stage_id)
    for hub_id in hubs:
        load_shifting.add_hub(load_shift_id, hub_id)
    for ec_id in ecs:
        load_shifting.add_ec(load_shift_id, ec_id)
    # interval_length
    interval_length = yaml_parser.parse_mandatory_int_value_from_dict_node(
        load_shift_node, YAMLKEY_INTERVALLENGTH)
    load_shifting.set_interval_length(load_shift_id, interval_length)
    # max_above_abs
    max_above_abs = yaml_parser.parse_optional_float_value_from_dict_node(
        load_shift_node, YAMLKEY_MAXABOVEABS)
    if max_above_abs is not None:
        load_shifting.set_max_above_abs_def(load_shift_id, max_above_abs)
    # max_below_abs
    max_below_abs = yaml_parser.parse_optional_float_value_from_dict_node(
        load_shift_node, YAMLKEY_MAXBELOWABS)
    if max_below_abs is not None:
        load_shifting.set_max_below_abs_def(load_shift_id, max_below_abs)
    # max_above_rel
    max_above_rel = yaml_parser.parse_optional_float_value_from_dict_node(
        load_shift_node, YAMLKEY_MAXABOVEREL)
    if max_above_rel is not None:
        load_shifting.set_max_above_rel_def(load_shift_id, max_above_rel)
    # max_below_rel
    max_below_rel = yaml_parser.parse_optional_float_value_from_dict_node(
        load_shift_node, YAMLKEY_MAXBELOWREL)
    if max_below_rel is not None:
        load_shifting.set_max_below_rel_def(load_shift_id, max_below_rel)
    # interval_cap
    interval_cap = yaml_parser.parse_optional_float_value_from_dict_node(
        load_shift_node, YAMLKEY_INTERVALCAP)
    if interval_cap is not None:
        load_shifting.set_interval_cap(load_shift_id, interval_cap)
    # energy_cost_above
    energy_cost_above = yaml_parser.parse_optional_float_value_from_dict_node(
        load_shift_node, YAMLKEY_ENERGYCOSTABOVE)
    if energy_cost_above is not None:
        load_shifting.set_energy_cost_above_def(load_shift_id,
                                                energy_cost_above)
    # energy_cost_below
    energy_cost_below = yaml_parser.parse_optional_float_value_from_dict_node(
        load_shift_node, YAMLKEY_ENERGYCOSTBELOW)
    if energy_cost_below is not None:
        load_shifting.set_energy_cost_below_def(load_shift_id,
                                                energy_cost_below)
    # peak_cost_above
    peak_cost_above = yaml_parser.parse_optional_float_value_from_dict_node(
        load_shift_node, YAMLKEY_PEAKCOSTABOVE)
    if peak_cost_above is not None:
        load_shifting.set_peak_cost_above(load_shift_id, peak_cost_above)
    # peak_cost_below
    peak_cost_below = yaml_parser.parse_optional_float_value_from_dict_node(
        load_shift_node, YAMLKEY_PEAKCOSTBELOW)
    if peak_cost_below is not None:
        load_shifting.set_peak_cost_below(load_shift_id, peak_cost_below)
    # fix_cost
    fix_cost = yaml_parser.parse_optional_float_value_from_dict_node(
        load_shift_node, YAMLKEY_FIXCOST)
    if fix_cost is not None:
        load_shifting.set_fix_cost_def(load_shift_id, fix_cost)


def _parse_profiles(load_shift_node: yaml_parser.YamlDictNode,
                    load_shift_id: LoadShiftId,
                    load_shifting: LoadShifting) -> None:
    # profile_path
    profile_path = yaml_parser.parse_optional_str_value_from_dict_node(
        load_shift_node, YAMLKEY_PROFILEPATH)
    if profile_path is None:
        return
    profile_path = os.path.abspath(os.path.join(
        load_shift_node.file_path, os.pardir, profile_path))
    yaml_parser.check_file_exists(profile_path, FILETYPE_LOADSHIFTPROFILE)
    df_profiles = csv_parser.parse(profile_path,
                                   header_ids=[csv_parser.HeaderId.LOADSHIFTID,
                                               csv_parser.HeaderId.PROFILEKEY])
    # Write profile values to data model
    for (ls, profile_key) in df_profiles.columns:
        if ls != load_shift_id.key:
            continue
        # max_above_abs
        if profile_key == YAMLKEY_MAXABOVEABS:
            for t in df_profiles.index:
                load_shifting.set_max_above_abs(load_shift_id, TimeId(t),
                    df_profiles[ls, profile_key][t])
        # max_below_abs
        if profile_key == YAMLKEY_MAXBELOWABS:
            for t in df_profiles.index:
                load_shifting.set_max_below_abs(load_shift_id, TimeId(t),
                    df_profiles[ls, profile_key][t])
        # max_above_rel
        if profile_key == YAMLKEY_MAXABOVEREL:
            for t in df_profiles.index:
                load_shifting.set_max_above_rel(load_shift_id, TimeId(t),
                    df_profiles[ls, profile_key][t])
        # max_below_rel
        if profile_key == YAMLKEY_MAXBELOWREL:
            for t in df_profiles.index:
                load_shifting.set_max_below_rel(load_shift_id, TimeId(t),
                    df_profiles[ls, profile_key][t])
        # energy_cost_above
        if profile_key == YAMLKEY_ENERGYCOSTABOVE:
            for t in df_profiles.index:
                load_shifting.set_energy_cost_above(load_shift_id, TimeId(t),
                    df_profiles[ls, profile_key][t])
        # energy_cost_below
        if profile_key == YAMLKEY_ENERGYCOSTBELOW:
            for t in df_profiles.index:
                load_shifting.set_energy_cost_below(load_shift_id, TimeId(t),
                    df_profiles[ls, profile_key][t])
        # fix_cost
        if profile_key == YAMLKEY_FIXCOST:
            for t in df_profiles.index:
                load_shifting.set_fix_cost(load_shift_id, TimeId(t),
                    df_profiles[ls, profile_key][t])


def _log(load_shifting: LoadShifting) -> None:
    logging.log_file(f"Parsed {len(load_shifting.ids)} load shift id(s)",
                     module=LOG_MODULE_STR)
    for ls in load_shifting.ids:
        logging.log_file(
            (f"  Load shift {ls}: Tuples {load_shifting.get_tuples(ls)}, "
             f"interval_length = {load_shifting.get_interval_length(ls)}"),
            print_time=False)
