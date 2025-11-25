import itertools
import os
from typing import Optional, Set, Tuple

import pandas as pd

import ehubx.data.exceptions as data_exceptions
from ehubx.core import logging
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId
from ehubx.data.load_shedding_data import LoadShedding
from ehubx.data.stage_data import StageId
from ehubx.data.time_data import TimeId
from ehubx.data.unit import CurrencyUnit, DimlessUnit, TimeUnit, Unit
from ehubx.data.value import Value
from ehubx.parser import csv_parser, exceptions, yaml_parser


# YAML keys
YAMLKEY_LOADSHHEDDING = "load_shedding"
YAMLKEY_PRESET = "preset"
YAMLKEY_MANUAL = "manual"
YAMLKEY_STAGES = "stages"
YAMLKEY_HUBS = "hubs"
YAMLKEY_EC = "ec"
YAMLKEY_ENABLED = "enabled"
YAMLKEY_MAXABS = "max_abs"
YAMLKEY_MAXREL = "max_rel"
YAMLKEY_ENERGYCOST = "energy_cost"
YAMLKEY_PROFILEPATH = "profile_path"

# Literals
LOG_MODULE_STR: str = "pars/load_shed"
FILETYPE_LOADSHEDDINGPROFILE = "load_shedding profile"
DEF_ENABLED: bool = True


def parse(demand_root_node: Optional[yaml_parser.YamlNode], ecs: Ecs) -> LoadShedding:
    # Initialize data model
    load_shedding = LoadShedding()
    if demand_root_node is None:
        return load_shedding
    load_shedding_node = demand_root_node[YAMLKEY_LOADSHHEDDING]
    if load_shedding_node is None:
        return load_shedding
    yaml_parser.check_node_type(load_shedding_node, yaml_parser.YamlNodeKind.LIST)
    previous_tuples: Set[Tuple[StageId, HubId, EcId]] = set()
    for node in load_shedding_node:
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
        # Stage-hub tuples
        stage_hub_tuples = set(itertools.product(stage_ids, hub_ids))
        dupe_tuples = previous_tuples.intersection(
            {(stage_id, hub_id, ec_id) for (stage_id, hub_id) in stage_hub_tuples}
        )
        if len(dupe_tuples) > 0:
            raise exceptions.ParsingException(
                node.file_path,
                "Overlap detected in load shedding module: The (stage, hub, ec) "
                f"tuples {dupe_tuples} occur in more than one load shedding entry",
                module=LOG_MODULE_STR,
            )
        _parse_node(node, stage_hub_tuples, ec_id, ecs.get_unit(ec_id), load_shedding)
        # Remember encountered tuples
        previous_tuples = previous_tuples.union(
            {(stage_id, hub_id, ec_id) for (stage_id, hub_id) in stage_hub_tuples}
        )
    # Logging
    _log(load_shedding)
    # Return
    return load_shedding


def _parse_node(
    node: yaml_parser.YamlDictNode,
    stage_hub_tuples: Set[Tuple[StageId, HubId]],
    ec_id: EcId,
    ec_unit: Unit,
    load_shedding: LoadShedding,
) -> None:
    # enabled
    enabled = yaml_parser.parse_optional_bool_from_dict_node(node, YAMLKEY_ENABLED)
    # max_abs
    max_abs = yaml_parser.parse_optional_value_from_dict_node(
        node, YAMLKEY_MAXABS, expected_unit=(ec_unit / TimeUnit.H)
    )
    # max_rel
    max_rel = yaml_parser.parse_optional_value_from_dict_node(
        node, YAMLKEY_MAXREL, expected_unit=DimlessUnit()
    )
    # energy_cost
    energy_cost = yaml_parser.parse_optional_value_from_dict_node(
        node,
        YAMLKEY_ENERGYCOST,
        expected_unit=(CurrencyUnit.CHF / ec_unit),
    )

    # Write def values to data model
    for stage_id, hub_id in stage_hub_tuples:
        load_shedding.add_tuple(stage_id, hub_id, ec_id, ec_unit)
        if enabled is not None:
            load_shedding.set_enabled(stage_id, hub_id, ec_id, enabled)
        if max_abs is not None:
            load_shedding.set_max_abs_def(stage_id, hub_id, ec_id, max_abs)
        if max_rel is not None:
            load_shedding.set_max_rel_def(stage_id, hub_id, ec_id, max_rel)
        if energy_cost is not None:
            load_shedding.set_energy_cost_def(stage_id, hub_id, ec_id, energy_cost)

    # profiles
    profile_path = yaml_parser.parse_optional_str_from_dict_node(
        node, YAMLKEY_PROFILEPATH
    )
    if profile_path is not None:
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
        for stage_id, hub_id in stage_hub_tuples:
            _parse_profiles(
                df_profiles,
                profile_path,
                stage_id,
                hub_id,
                ec_id,
                ec_unit,
                load_shedding,
            )


def _parse_profiles(
    df_profiles: pd.DataFrame,
    profile_path: str,
    stage_id: StageId,
    hub_id: HubId,
    ec_id: EcId,
    ec_unit: Unit,
    load_shedding: LoadShedding,
) -> None:
    for s, h, e, key in df_profiles.columns:
        if s != stage_id.key:
            continue
        if h != hub_id.key:
            continue
        if e != ec_id.key:
            continue
        try:
            unit = Unit.from_str(df_profiles.attrs[csv_parser.ATTR_UNIT][s, h, e, key])
        except data_exceptions.UnitException as ex:
            raise exceptions.ParsingException(
                profile_path,
                f"Invalid unit '{ex.unit}' for load shedding profile key '{key}' "
                f"for (stage, hub, ec) tuple ({s}, {h}, {e})",
                module=LOG_MODULE_STR,
            ) from ex

        expected_unit: Unit
        check_unit: bool = True
        if key == YAMLKEY_MAXABS:
            expected_unit = ec_unit / TimeUnit.H
        elif key == YAMLKEY_MAXREL:
            expected_unit = DimlessUnit()
        elif key == YAMLKEY_ENERGYCOST:
            expected_unit = CurrencyUnit.CHF / ec_unit
        else:
            check_unit = False

        if check_unit and not unit.same_type_as(expected_unit):
            raise exceptions.ParsingException(
                profile_path,
                f"Invalid unit '{unit}' for load shedding profile key '{key}' "
                f"for (stage, hub, ec) tuple ({s}, {h}, {e}). Expected a unit "
                f"like '{expected_unit}'.",
                module=LOG_MODULE_STR,
            )

        # Write profile values to data model
        if key == YAMLKEY_MAXABS:
            for t, val in df_profiles[s, h, e, key].items():
                load_shedding.set_max_abs(
                    stage_id, hub_id, ec_id, TimeId(t), Value(val, unit)
                )
        if key == YAMLKEY_MAXREL:
            for t, val in df_profiles[s, h, e, key].items():
                load_shedding.set_max_rel(
                    stage_id, hub_id, ec_id, TimeId(t), Value(val, unit)
                )
        if key == YAMLKEY_ENERGYCOST:
            for t, val in df_profiles[s, h, e, key].items():
                load_shedding.set_energy_cost(
                    stage_id, hub_id, ec_id, TimeId(t), Value(val, unit)
                )


def _log(load_shedding: LoadShedding) -> None:
    msg = "Load shedding tuples: "
    logging.log_file(msg, module=LOG_MODULE_STR)
    for s, h, e in load_shedding.tuples:
        msg = f"  Load shedding tuple ({s}, {h}, {e}): " + (
            "Enabled" if load_shedding.is_enabled(s, h, e) else "Disabled"
        )
        logging.log_file(msg, print_time=False)
