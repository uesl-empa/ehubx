import itertools
import os
from typing import List, Optional, Set, Tuple

import pandas as pd

import ehubx.data.exceptions as data_exceptions
from ehubx.core import logging
from ehubx.data.demand_data import Demands
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId
from ehubx.data.time_data import TimeId
from ehubx.data.unit import CurrencyUnit, TimeUnit, Unit
from ehubx.data.value import Value
from ehubx.parser import csv_parser, exceptions, yaml_parser


# YAML keys
YAMLKEY_DEMANDPROFILES = "demand_profiles"
YAMLKEY_DEMANDSUMS = "demand_sums"
YAMLKEY_DEMANDSUM = "demand_sum"
YAMLKEY_STAGES = "stages"
YAMLKEY_HUBS = "hubs"
YAMLKEY_EC = "ec"
YAMLKEY_DEMANDUNMETPENALTIES = "demand_unmet_penalties"
YAMLKEY_DEMANDUNMETPENALTY = "demand_unmet_penalty"

# Literals
LOG_MODULE_STR: str = "pars/demand"
FILE_DEMANDS = "demands.yaml"
FILETYPE_DEMANDPROFILE = "demand profile"


def parse(
    basic_subpath: str, ecs: Ecs
) -> Tuple[Demands, Optional[yaml_parser.YamlNode]]:
    # Initialize data model
    demands = Demands()
    # Read file
    demand_file_path = os.path.join(basic_subpath, FILE_DEMANDS)
    if not os.path.isfile(demand_file_path):
        return demands, None
    demand_root_node = yaml_parser.parse(demand_file_path)
    if demand_root_node is None:
        return demands, None
    yaml_parser.check_node_type(demand_root_node, yaml_parser.YamlNodeKind.DICT)
    # Demand-profiles
    demand_profiles_node = demand_root_node[YAMLKEY_DEMANDPROFILES]
    _parse_demand_profiles(demand_profiles_node, ecs, demands)
    # Demand-sums
    demand_sums_node = demand_root_node[YAMLKEY_DEMANDSUMS]
    _parse_demand_sums(demand_sums_node, ecs, demands)
    # Unmet-penalties
    unmet_penalties_node = demand_root_node[YAMLKEY_DEMANDUNMETPENALTIES]
    _parse_unmet_penalties(unmet_penalties_node, ecs, demands)
    # Logging
    _log(demands)
    # Return
    return demands, demand_root_node


def _parse_demand_profiles(
    demand_profiles_node: Optional[yaml_parser.YamlNode], ecs: Ecs, demands: Demands
) -> None:
    if demand_profiles_node is None:
        return
    yaml_parser.check_node_type(demand_profiles_node, yaml_parser.YamlNodeKind.LIST)
    # Save demand dataframes per entry to list
    dfs: List[pd.DataFrame] = []
    for demand_profile_node in demand_profiles_node:
        yaml_parser.check_node_type(demand_profile_node, yaml_parser.YamlNodeKind.VALUE)
        _parse_demand_profile(demand_profile_node, dfs)
    if not dfs:
        return
    # Concatenate and sum up profiles
    for df_sub in dfs:
        for s, h, e in df_sub.columns:
            # Check
            try:
                unit = Unit.from_str(df_sub.attrs[csv_parser.ATTR_UNIT][s, h, e])
            except data_exceptions.UnitException as ex:
                raise exceptions.ParsingException(
                    "(one of the demands files)",
                    f"Invalid unit '{ex.unit}' for (stage, hub, ec) tuple "
                    f"({s}, {h}, {e})",
                    module=LOG_MODULE_STR,
                ) from ex

            e_unit = ecs.get_unit(EcId(e))
            dem_unit = e_unit / TimeUnit.H
            if not unit.same_type_as(dem_unit):
                raise exceptions.ParsingException(
                    "(one of the demands files)",
                    f"Invalid unit '{unit}' for demand profile at (stage, hub, ec) "
                    f"tuple ({s}, {h}, {e}). Expected a unit like '{dem_unit}'",
                    module=LOG_MODULE_STR,
                )
            if (StageId(s), HubId(h), EcId(e)) not in demands.profile_tuples:
                demands.add_profile_tuple(StageId(s), HubId(h), EcId(e), e_unit)
                for t, val in df_sub[s, h, e].items():
                    demands.set_demand_in_profile(
                        StageId(s), HubId(h), EcId(e), TimeId(t), Value(val, unit)
                    )
            else:
                demand_cur = demands.get_demand_profile(StageId(s), HubId(h), EcId(e))
                for t, val in df_sub[s, h, e].items():
                    demands.set_demand_in_profile(
                        StageId(s),
                        HubId(h),
                        EcId(e),
                        TimeId(t),
                        demand_cur.get_value(t) + Value(val, unit),
                    )


def _parse_demand_profile(
    demand_profile_node: yaml_parser.YamlValueNode, dfs: List[pd.DataFrame]
) -> None:
    # profile_path
    profile_path = demand_profile_node.value
    profile_path = os.path.abspath(
        os.path.join(demand_profile_node.file_path, os.pardir, profile_path)
    )
    # Parse profile
    yaml_parser.check_file_exists(profile_path, FILETYPE_DEMANDPROFILE)
    df = csv_parser.parse(
        profile_path,
        header_ids=[
            csv_parser.HeaderId.STAGEID,
            csv_parser.HeaderId.HUBID,
            csv_parser.HeaderId.ECID,
        ],
    )
    dfs.append(df)


def _parse_demand_sums(
    demand_sums_node: Optional[yaml_parser.YamlNode], ecs: Ecs, demands: Demands
) -> None:
    if demand_sums_node is None:
        return
    yaml_parser.check_node_type(demand_sums_node, yaml_parser.YamlNodeKind.LIST)
    # Iterate over list
    previous_tuples: Set[Tuple[StageId, HubId, EcId]] = set()
    for demand_sum_node in demand_sums_node:
        yaml_parser.check_node_type(demand_sum_node, yaml_parser.YamlNodeKind.DICT)
        # stages
        stages_str = yaml_parser.parse_str_list_from_dict_node(
            demand_sum_node, YAMLKEY_STAGES, optional=False
        )
        stage_ids = {StageId(stage_str) for stage_str in stages_str}
        # hubs
        hubs_str = yaml_parser.parse_str_list_from_dict_node(
            demand_sum_node, YAMLKEY_HUBS, optional=False
        )
        hub_ids = {HubId(hub_str) for hub_str in hubs_str}
        # ec
        ec_str = yaml_parser.parse_mandatory_str_from_dict_node(
            demand_sum_node, YAMLKEY_EC
        )
        ec_id = EcId(ec_str)
        # Id tuples
        stage_hub_tuples = set(itertools.product(stage_ids, hub_ids))
        dupe_tuples = previous_tuples.intersection(
            {(stage_id, hub_id, ec_id) for (stage_id, hub_id) in stage_hub_tuples}
        )
        if len(dupe_tuples) > 0:
            raise exceptions.ParsingException(
                demand_sum_node.file_path,
                "Overlap detected in demand module: The (stage, hub, ec) tuples "
                f"{dupe_tuples} occur in more than one demand_sums entry",
                module=LOG_MODULE_STR,
            )
        _parse_demand_sum(
            demand_sum_node, stage_hub_tuples, ec_id, ecs.get_unit(ec_id), demands
        )
        # Remember encountered tuples
        previous_tuples = previous_tuples.union(
            {(stage_id, hub_id, ec_id) for (stage_id, hub_id) in stage_hub_tuples}
        )


def _parse_demand_sum(
    node: yaml_parser.YamlDictNode,
    stage_hub_tuples: Set[Tuple[StageId, HubId]],
    ec_id: EcId,
    ec_unit: Unit,
    demands: Demands,
) -> None:
    # demand_sum
    demand_sum = yaml_parser.parse_mandatory_value_from_dict_node(
        node, YAMLKEY_DEMANDSUM, expected_unit=ec_unit
    )
    for stage_id, hub_id in stage_hub_tuples:
        demands.set_demand_sum(stage_id, hub_id, ec_id, demand_sum)


def _parse_unmet_penalties(
    unmet_penalties_node: Optional[yaml_parser.YamlNode], ecs: Ecs, demands: Demands
) -> None:
    if unmet_penalties_node is None:
        return
    yaml_parser.check_node_type(unmet_penalties_node, yaml_parser.YamlNodeKind.LIST)
    previous_tuples: Set[Tuple[StageId, HubId, EcId]] = set()
    for penalty_node in unmet_penalties_node:
        yaml_parser.check_node_type(penalty_node, yaml_parser.YamlNodeKind.DICT)
        # stages
        stages_str = yaml_parser.parse_str_list_from_dict_node(
            penalty_node, YAMLKEY_STAGES, optional=False
        )
        stage_ids = {StageId(stage_str) for stage_str in stages_str}
        # hubs
        hubs_str = yaml_parser.parse_str_list_from_dict_node(
            penalty_node, YAMLKEY_HUBS, optional=False
        )
        hub_ids = {HubId(hub_str) for hub_str in hubs_str}
        # ec
        ec_str = yaml_parser.parse_mandatory_str_from_dict_node(
            penalty_node, YAMLKEY_EC
        )
        ec_id = EcId(ec_str)
        # Expected unit: currency per energy (e.g. CHF/kWh)
        expected_unit = CurrencyUnit.CHF / ecs.get_unit(ec_id)
        unmet_penalty = yaml_parser.parse_mandatory_value_from_dict_node(
            penalty_node, YAMLKEY_DEMANDUNMETPENALTY, expected_unit=expected_unit
        )
        # Id tuples + duplicate check
        stage_hub_tuples = set(itertools.product(stage_ids, hub_ids))
        dupe_tuples = previous_tuples.intersection(
            {(stage_id, hub_id, ec_id) for (stage_id, hub_id) in stage_hub_tuples}
        )
        if len(dupe_tuples) > 0:
            raise exceptions.ParsingException(
                penalty_node.file_path,
                "Overlap detected in demand module: The (stage, hub, ec) tuples "
                f"{dupe_tuples} occur in more than one unmet_penalties entry",
                module=LOG_MODULE_STR,
            )
        for stage_id, hub_id in stage_hub_tuples:
            demands.set_demand_unmet_penalty(stage_id, hub_id, ec_id, unmet_penalty)
        previous_tuples = previous_tuples.union(
            {(stage_id, hub_id, ec_id) for (stage_id, hub_id) in stage_hub_tuples}
        )


def _log(demands: Demands) -> None:
    logging.log_file(
        f"Parsed {len(demands.tuples)} demand (stage, hub, ec) tuples",
        module=LOG_MODULE_STR,
    )
    for s, h, e in demands.profile_tuples:
        logging.log_file(f"  Demand-profile tuple ({s}, {h}, {e})", print_time=False)
    for s, h, e in demands.sum_tuples:
        logging.log_file(f"  Demand-sum tuple ({s}, {h}, {e})", print_time=False)
