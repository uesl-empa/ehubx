import os
from typing import Optional, Set

import pandas as pd

import ehubx.data.exceptions as data_exceptions
from ehubx.core import logging
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId
from ehubx.data.load_shifting_data import LoadShiftId, LoadShifting
from ehubx.data.stage_data import StageId
from ehubx.data.time_data import TimeId
from ehubx.data.unit import CurrencyUnit, DimlessUnit, TimeUnit, Unit
from ehubx.data.value import Value
from ehubx.parser import csv_parser, exceptions, yaml_parser


# YAML keys
YAMLKEY_LOADHSHIFTING = "load_shifting"
YAMLKEY_LOADSHIFTID = "load_shift_id"
YAMLKEY_STAGES = "stages"
YAMLKEY_HUBS = "hubs"
YAMLKEY_EC = "ec"
YAMLKEY_INTERVALLENGTH = "interval_length"
YAMLKEY_CAPEXPERCAP = "capex_per_cap"
YAMLKEY_CAPMIN = "cap_min"
YAMLKEY_CAPMAX = "cap_max"
YAMLKEY_CAPINIT = "cap_init"
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


def parse(demand_root_node: Optional[yaml_parser.YamlNode], ecs: Ecs) -> LoadShifting:
    # Initialize data model
    load_shifting = LoadShifting()
    if demand_root_node is None:
        return load_shifting
    load_shifts_node = demand_root_node[YAMLKEY_LOADHSHIFTING]
    if load_shifts_node is None:
        return load_shifting
    yaml_parser.check_node_type(load_shifts_node, yaml_parser.YamlNodeKind.LIST)
    load_shifts_node.set_id(YAMLKEY_LOADSHIFTID)
    for node in load_shifts_node:
        yaml_parser.check_node_type(node, yaml_parser.YamlNodeKind.DICT)
        # stages
        stages_str = yaml_parser.parse_str_list_from_dict_node(
            node, YAMLKEY_STAGES, optional=False
        )
        stage_ids = {StageId(stage_str) for stage_str in stages_str}
        # hubs
        hubs_str = yaml_parser.parse_str_list_from_dict_node(
            node, YAMLKEY_HUBS, optional=False
        )
        hub_ids = {HubId(hub_str) for hub_str in hubs_str}
        # ec
        ec_str = yaml_parser.parse_mandatory_str_from_dict_node(node, YAMLKEY_EC)
        ec_id = EcId(ec_str)
        _parse_node(node, stage_ids, hub_ids, ec_id, ecs.get_unit(ec_id), load_shifting)

    # Logging
    _log(load_shifting)
    # Return
    return load_shifting


def _parse_node(
    node: yaml_parser.YamlDictNode,
    stage_ids: Set[StageId],
    hub_ids: Set[HubId],
    ec_id: EcId,
    ec_unit: Unit,
    load_shifting: LoadShifting,
) -> None:
    yaml_parser.check_node_type(node, yaml_parser.YamlNodeKind.DICT)
    # load_shift_id and ec
    load_shift_id_str = yaml_parser.parse_mandatory_str_from_dict_node(
        node, YAMLKEY_LOADSHIFTID
    )
    load_shift_id = LoadShiftId(load_shift_id_str)
    load_shifting.add_id(load_shift_id, ec_id, ec_unit)
    # stages
    for stage_id in stage_ids:
        load_shifting.add_stage(load_shift_id, stage_id)
    # hubs
    for hub_id in hub_ids:
        load_shifting.add_hub(load_shift_id, hub_id)
    # interval_length
    interval_length = yaml_parser.parse_mandatory_value_from_dict_node(
        node, YAMLKEY_INTERVALLENGTH, expected_unit=TimeUnit.H
    )
    load_shifting.set_interval_length(load_shift_id, interval_length)
    # max_above_abs
    max_above_abs = yaml_parser.parse_optional_value_from_dict_node(
        node, YAMLKEY_MAXABOVEABS, expected_unit=(ec_unit / TimeUnit.H)
    )
    if max_above_abs is not None:
        load_shifting.set_max_above_abs_def(load_shift_id, max_above_abs)
    # max_below_abs
    max_below_abs = yaml_parser.parse_optional_value_from_dict_node(
        node, YAMLKEY_MAXBELOWABS, expected_unit=(ec_unit / TimeUnit.H)
    )
    if max_below_abs is not None:
        load_shifting.set_max_below_abs_def(load_shift_id, max_below_abs)
    # max_above_rel
    max_above_rel = yaml_parser.parse_optional_value_from_dict_node(
        node,
        YAMLKEY_MAXABOVEREL,
        expected_unit=DimlessUnit(),
    )
    if max_above_rel is not None:
        load_shifting.set_max_above_rel_def(load_shift_id, max_above_rel)
    # max_below_rel
    max_below_rel = yaml_parser.parse_optional_value_from_dict_node(
        node,
        YAMLKEY_MAXBELOWREL,
        expected_unit=DimlessUnit(),
    )
    if max_below_rel is not None:
        load_shifting.set_max_below_rel_def(load_shift_id, max_below_rel)
    # capex_per_cap
    capex_per_cap = yaml_parser.parse_optional_value_from_dict_node(
        node, YAMLKEY_CAPEXPERCAP, expected_unit=(CurrencyUnit.CHF / ec_unit)
    )
    if capex_per_cap is not None:
        load_shifting.set_capex_per_cap(load_shift_id, capex_per_cap)
    # cap_min
    cap_min = yaml_parser.parse_optional_value_from_dict_node(
        node, YAMLKEY_CAPMIN, expected_unit=ec_unit
    )
    if cap_min is not None:
        load_shifting.set_cap_min(load_shift_id, cap_min)
    # cap_max
    cap_max = yaml_parser.parse_optional_value_from_dict_node(
        node, YAMLKEY_CAPMAX, expected_unit=ec_unit
    )
    if cap_max is not None:
        load_shifting.set_cap_max(load_shift_id, cap_max)
    # cap_init
    cap_init = yaml_parser.parse_optional_value_from_dict_node(
        node, YAMLKEY_CAPINIT, expected_unit=ec_unit
    )
    if cap_init is not None:
        load_shifting.set_cap_init(load_shift_id, cap_init)
    # energy_cost_above
    energy_cost_above = yaml_parser.parse_optional_value_from_dict_node(
        node,
        YAMLKEY_ENERGYCOSTABOVE,
        expected_unit=(CurrencyUnit.CHF / ec_unit),
    )
    if energy_cost_above is not None:
        load_shifting.set_energy_cost_above_def(load_shift_id, energy_cost_above)
    # energy_cost_below
    energy_cost_below = yaml_parser.parse_optional_value_from_dict_node(
        node,
        YAMLKEY_ENERGYCOSTBELOW,
        expected_unit=(CurrencyUnit.CHF / ec_unit),
    )
    if energy_cost_below is not None:
        load_shifting.set_energy_cost_below_def(load_shift_id, energy_cost_below)
    # peak_cost_above
    peak_cost_above = yaml_parser.parse_optional_value_from_dict_node(
        node,
        YAMLKEY_PEAKCOSTABOVE,
        expected_unit=(CurrencyUnit.CHF / (ec_unit / TimeUnit.H)),
    )
    if peak_cost_above is not None:
        load_shifting.set_peak_cost_above(load_shift_id, peak_cost_above)
    # peak_cost_below
    peak_cost_below = yaml_parser.parse_optional_value_from_dict_node(
        node,
        YAMLKEY_PEAKCOSTBELOW,
        expected_unit=(CurrencyUnit.CHF / (ec_unit / TimeUnit.H)),
    )
    if peak_cost_below is not None:
        load_shifting.set_peak_cost_below(load_shift_id, peak_cost_below)
    # fix_cost
    fix_cost = yaml_parser.parse_optional_value_from_dict_node(
        node, YAMLKEY_FIXCOST, expected_unit=(CurrencyUnit.CHF / TimeUnit.H)
    )
    if fix_cost is not None:
        load_shifting.set_fix_cost_def(load_shift_id, fix_cost)

    # Profiles
    profile_path = yaml_parser.parse_optional_str_from_dict_node(
        node, YAMLKEY_PROFILEPATH
    )
    if profile_path is not None:
        profile_path = os.path.abspath(
            os.path.join(node.file_path, os.pardir, profile_path)
        )
        yaml_parser.check_file_exists(profile_path, FILETYPE_LOADSHIFTPROFILE)
        df_profiles = csv_parser.parse(
            profile_path,
            header_ids=[
                csv_parser.HeaderId.LOADSHIFTID,
                csv_parser.HeaderId.PROFILEKEY,
            ],
        )
        _parse_profiles(
            df_profiles,
            profile_path,
            load_shift_id,
            ec_unit,
            load_shifting,
        )


def _parse_profiles(
    df_profiles: pd.DataFrame,
    profile_path: str,
    load_shift_id: LoadShiftId,
    ec_unit: Unit,
    load_shifting: LoadShifting,
) -> None:
    for ls, key in df_profiles.columns:
        if ls != load_shift_id.key:
            continue
        try:
            unit = Unit.from_str(df_profiles.attrs[csv_parser.ATTR_UNIT][ls, key])
        except data_exceptions.UnitException as ex:
            raise exceptions.ParsingException(
                profile_path,
                f"Invalid unit '{ex.unit}' for load shifting profile key '{key}' "
                f"for load shift id {ls}",
                module=LOG_MODULE_STR,
            ) from ex

        expected_unit: Unit
        check_unit: bool = True
        if key in {YAMLKEY_MAXABOVEABS, YAMLKEY_MAXBELOWABS}:
            expected_unit = ec_unit / TimeUnit.H
        elif key in {YAMLKEY_MAXABOVEREL, YAMLKEY_MAXBELOWREL}:
            expected_unit = DimlessUnit()
        elif key in {YAMLKEY_ENERGYCOSTABOVE, YAMLKEY_ENERGYCOSTBELOW}:
            expected_unit = CurrencyUnit.CHF / ec_unit
        elif key == YAMLKEY_FIXCOST:
            expected_unit = CurrencyUnit.CHF / TimeUnit.H
        else:
            check_unit = False

        if check_unit and not unit.same_type_as(expected_unit):
            raise exceptions.ParsingException(
                profile_path,
                f"Invalid unit '{unit}' for load shifting profile key '{key}' "
                f"for load shift id {ls}. Expected a unit like '{expected_unit}'.",
                module=LOG_MODULE_STR,
            )

        # max_above_abs
        if key == YAMLKEY_MAXABOVEABS:
            for t, val in df_profiles[ls, key].items():
                load_shifting.set_max_above_abs(
                    load_shift_id, TimeId(t), Value(val, unit)
                )
        # max_below_abs
        if key == YAMLKEY_MAXBELOWABS:
            for t, val in df_profiles[ls, key].items():
                load_shifting.set_max_below_abs(
                    load_shift_id, TimeId(t), Value(val, unit)
                )
        # max_above_rel
        if key == YAMLKEY_MAXABOVEREL:
            for t, val in df_profiles[ls, key].items():
                load_shifting.set_max_above_rel(
                    load_shift_id, TimeId(t), Value(val, unit)
                )
        # max_below_rel
        if key == YAMLKEY_MAXBELOWREL:
            for t, val in df_profiles[ls, key].items():
                load_shifting.set_max_below_rel(
                    load_shift_id, TimeId(t), Value(val, unit)
                )
        # energy_cost_above
        if key == YAMLKEY_ENERGYCOSTABOVE:
            for t, val in df_profiles[ls, key].items():
                load_shifting.set_energy_cost_above(
                    load_shift_id, TimeId(t), Value(val, unit)
                )
        # energy_cost_below
        if key == YAMLKEY_ENERGYCOSTBELOW:
            for t, val in df_profiles[ls, key].items():
                load_shifting.set_energy_cost_below(
                    load_shift_id, TimeId(t), Value(val, unit)
                )
        # fix_cost
        if key == YAMLKEY_FIXCOST:
            for t, val in df_profiles[ls, key].items():
                load_shifting.set_fix_cost(load_shift_id, TimeId(t), Value(val, unit))


def _log(load_shifting: LoadShifting) -> None:
    logging.log_file(
        f"Parsed {len(load_shifting.ids)} load shift id(s)", module=LOG_MODULE_STR
    )
    for ls in load_shifting.ids:
        logging.log_file(
            (
                f"  Load shift {ls}: Tuples {load_shifting.get_stage_hub_tuples(ls)}, "
                f"interval_length = {load_shifting.get_interval_length(ls)}"
            ),
            print_time=False,
        )
