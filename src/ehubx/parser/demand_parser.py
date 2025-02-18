
import os
from typing import List, Optional, Tuple
import pandas as pd
from ehubx.core import logging
from ehubx.data.stage_data import StageId
from ehubx.data.hub_data import HubId
from ehubx.data.ec_data import EcId
from ehubx.data.time_data import TimeId
from ehubx.data.demand_data import Demands
from ehubx.parser import csv_parser
from ehubx.parser import yaml_parser

# YAML keys
YAMLKEY_DEMANDS = "demands"
YAMLKEY_DEMANDID = "demand_id"
YAMLKEY_PROFILEPATH = "profile_path"

# Literals
LOG_MODULE_STR: str = "pars/demand"
FILE_DEMANDS = "demands.yaml"
FILETYPE_DEMANDPROFILE = "demand profile"


def parse(basic_subpath: str
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
    yaml_parser.check_node_type(demand_root_node,
                                yaml_parser.YamlNodeKind.DICT)
    # Level 0: demands
    demands_node = demand_root_node[YAMLKEY_DEMANDS]
    if demands_node is None:
        return demands, demand_root_node
    yaml_parser.check_node_type(demands_node, yaml_parser.YamlNodeKind.LIST)
    demands_node.set_id(YAMLKEY_DEMANDID)
    # Save demand dataframes per entry to list
    dfs: List[pd.DataFrame] = []
    for demand_node in demands_node:
        _parse_demand(demand_node, dfs)
    if not dfs:
        return demands, demand_root_node
    # Concatenate and sum up profiles
    df = pd.concat(dfs, axis=1)
    df = df.T.groupby(level=[0, 1, 2]).sum().T
    # Write to demands data model
    for (s, h, e) in df.columns:
        demands.add_tuple(StageId(s), HubId(h), EcId(e))
        for t in df.index:
            demands.set_demand(StageId(s), HubId(h), EcId(e), TimeId(t),
                               df[(s, h, e)][t])
    # Logging
    _log(demands)
    # Return
    return demands, demand_root_node


def _parse_demand(demand_node: yaml_parser.YamlDictNode,
                  dfs: List[pd.DataFrame]) -> None:
    # profile_path
    profile_path = yaml_parser.parse_mandatory_str_value_from_dict_node(
        demand_node, YAMLKEY_PROFILEPATH)
    profile_path = os.path.abspath(os.path.join(
        demand_node.file_path, os.pardir, profile_path))
    # Parse profile
    yaml_parser.check_file_exists(profile_path, FILETYPE_DEMANDPROFILE)
    df = csv_parser.parse(profile_path,
        header_ids=[csv_parser.HeaderId.STAGEID, csv_parser.HeaderId.HUBID,
                    csv_parser.HeaderId.ECID])
    dfs.append(df)


def _log(demands: Demands) -> None:
    logging.log_file(
        f"Parsed {len(demands.tuples)} demand (stage, hub, ec) tuples",
        module=LOG_MODULE_STR)
    for (s, h, e) in demands.tuples:
        logging.log_file(f"  Demand tuple ({s}, {h}, {e})", print_time=False)
