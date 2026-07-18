import os
from typing import Optional, Tuple

from ehubx.core import logging
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.unit import CurrencyUnit, MassUnit
from ehubx.parser import yaml_parser


# YAML keys
YAMLKEY_STAGES = "stages"
YAMLKEY_STAGEID = "stage_id"
YAMLKEY_STARTYEAR = "start_year"
YAMLKEY_CO2PRICE = "co2_price"
YAMLKEY_CO2MIN = "co2_min"
YAMLKEY_CO2MAX = "co2_max"
YAMLKEY_AUTALLOWUNMETDEMAND = "autonomy_allow_unmet_demand"

# Literals
LOG_MODULE_STR: str = "parse/stage"
FILENAME_STAGES = "stages.yaml"
FILETYPE_STAGES = "stages"


def parse(basic_subpath: str) -> Tuple[Stages, Optional[yaml_parser.YamlNode]]:
    stages = Stages()
    stage_file_path = os.path.join(basic_subpath, FILENAME_STAGES)
    if not os.path.isfile(stage_file_path):
        return stages, None
    stage_root_node = yaml_parser.parse(stage_file_path)
    if stage_root_node is None:  # Empty stages file
        return stages, stage_root_node
    stages_node = stage_root_node[YAMLKEY_STAGES]
    if stages_node is None:
        return stages, stage_root_node
    yaml_parser.check_node_type(stages_node, yaml_parser.YamlNodeKind.LIST)
    stages_node.set_id(YAMLKEY_STAGEID)
    for stage_node in stages_node:
        _parse_stage(stage_node, stages)
    # Logging
    _log(stages)
    return stages, stage_root_node


def _parse_stage(stage_node: yaml_parser.YamlDictNode, stages: Stages) -> None:
    # id
    stage_id_str = yaml_parser.parse_mandatory_str_from_dict_node(
        stage_node, YAMLKEY_STAGEID
    )
    stage_id = StageId(stage_id_str)
    stages.add_id(stage_id)
    # start_year
    start_year = yaml_parser.parse_mandatory_float_from_dict_node(
        stage_node, YAMLKEY_STARTYEAR
    )
    stages.set_start_year(stage_id, start_year)
    # co2_price
    co2_price = yaml_parser.parse_optional_value_from_dict_node(
        stage_node, YAMLKEY_CO2PRICE, expected_unit=(CurrencyUnit.CHF / MassUnit.KG)
    )
    if co2_price is not None:
        stages.set_co2_price(stage_id, co2_price)
    # co2_min
    co2_min = yaml_parser.parse_optional_value_from_dict_node(
        stage_node, YAMLKEY_CO2MIN, expected_unit=MassUnit.KG
    )
    if co2_min is not None:
        stages.set_co2_min(stage_id, co2_min)
    # co2_max
    co2_max = yaml_parser.parse_optional_value_from_dict_node(
        stage_node, YAMLKEY_CO2MAX, expected_unit=MassUnit.KG
    )
    if co2_max is not None:
        stages.set_co2_max(stage_id, co2_max)

    # autonomy unmet demand
    autonomy_allow_unmet_demand = yaml_parser.parse_optional_bool_from_dict_node(
        stage_node, YAMLKEY_AUTALLOWUNMETDEMAND
    )
    if autonomy_allow_unmet_demand is not None:
        stages.set_allow_unmet_demand(stage_id, autonomy_allow_unmet_demand)


def _log(stages: Stages) -> None:
    logging.log_file(f"Parsed {len(stages.ids)} stage(s)", module=LOG_MODULE_STR)
    for s in stages.ids_in_order:
        logging.log_file(
            f"  Stage {s}: Start year = {stages.get_start_year(s)}", print_time=False
        )
