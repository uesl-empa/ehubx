import os
from typing import Set, Tuple
import itertools
from ehubx.core import logging
from ehubx.data.stage_data import StageId
from ehubx.data.hub_data import HubId
from ehubx.data.ec_data import EcId
from ehubx.data.import_data import Imports
from ehubx.data.export_data import Exports
from ehubx.data.time_data import TimeId
from ehubx.parser import csv_parser
from ehubx.parser import yaml_parser
from ehubx.parser import exceptions

# YAML keys
YAMLKEY_STAGES = "stages"
YAMLKEY_STAGEID = "stage_id"
YAMLKEY_HUBS = "hubs"
YAMLKEY_HUBID = "hub_id"
YAMLKEY_ECS = "ecs"
YAMLKEY_ECID = "ec_id"
YAMLKEY_PRICE = "price"
YAMLKEY_CO2 = "co2"
YAMLKEY_MIN = "min"
YAMLKEY_MAX = "max"
YAMLKEY_SUMMIN = "sum_min"
YAMLKEY_SUMMAX = "sum_max"
YAMLKEY_PROFILEPATH = "profile_path"

# Literals
LOG_MODULE_STR: str = "pars/imp_exp"
FILE_IMPORTS = "imports.yaml"
FILE_EXPORTS = "exports.yaml"
FILETYPE_IMPEXPPROFILE = "import/export profile"


def parse_imports(basic_subpath: str) -> Imports:
    imports = Imports()
    import_file_path = os.path.join(basic_subpath, FILE_IMPORTS)
    if not os.path.isfile(import_file_path):
        return imports
    import_root_node = yaml_parser.parse(import_file_path)
    if import_root_node is None:
        return imports
    yaml_parser.check_node_type(import_root_node,
                                yaml_parser.YamlNodeKind.LIST)
    # Iterate over list
    previous_tuples: Set[Tuple[StageId, HubId, EcId]] = set()
    for import_node in import_root_node:
        yaml_parser.check_node_type(import_node, yaml_parser.YamlNodeKind.DICT)
        # stages
        stages_str = yaml_parser.parse_str_list_from_dict_node(
            import_node, YAMLKEY_STAGES, optional=False)
        stages = {StageId(stage_str) for stage_str in stages_str}
        # hubs
        hubs_str = yaml_parser.parse_str_list_from_dict_node(
            import_node, YAMLKEY_HUBS, optional=False)
        hubs = {HubId(hub_str) for hub_str in hubs_str}
        # ecs
        ecs_str = yaml_parser.parse_str_list_from_dict_node(
            import_node, YAMLKEY_ECS, optional=False)
        ecs = {EcId(ec_str) for ec_str in ecs_str}
        # Id tuples
        id_tuples = set(itertools.product(stages, hubs, ecs))
        dupe_tuples = previous_tuples.intersection(id_tuples)
        if len(dupe_tuples) > 0:
            msg = "Overlap detected in import module: " + \
                f"The (stage, hub, ec) tuples {dupe_tuples} occur in more " + \
                "than one import entry"
            raise exceptions.ParsingException(import_node.file_path, msg,
                                              module=LOG_MODULE_STR)
        for (stage_id, hub_id, ec_id) in id_tuples:
            _parse_import_tuple(stage_id, hub_id, ec_id, import_node, imports)

    # Logging
    _log_imports(imports)
    # Return
    return imports


def parse_exports(basic_subpath: str) -> Exports:
    exports = Exports()
    export_file_path = os.path.join(basic_subpath, FILE_EXPORTS)
    if not os.path.isfile(export_file_path):
        return exports
    export_root_node = yaml_parser.parse(export_file_path)
    if export_root_node is None:
        return exports
    yaml_parser.check_node_type(export_root_node,
                                yaml_parser.YamlNodeKind.LIST)
    # Iterate over list
    previous_tuples: Set[Tuple[StageId, HubId, EcId]] = set()
    for export_node in export_root_node:
        yaml_parser.check_node_type(export_node, yaml_parser.YamlNodeKind.DICT)
        # stages
        stages_str = yaml_parser.parse_str_list_from_dict_node(
            export_node, YAMLKEY_STAGES, optional=False)
        stages = {StageId(stage_str) for stage_str in stages_str}
        # hubs
        hubs_str = yaml_parser.parse_str_list_from_dict_node(
            export_node, YAMLKEY_HUBS, optional=False)
        hubs = {HubId(hub_str) for hub_str in hubs_str}
        # ecs
        ecs_str = yaml_parser.parse_str_list_from_dict_node(
            export_node, YAMLKEY_ECS, optional=False)
        ecs = {EcId(ec_str) for ec_str in ecs_str}
        # Id tuples
        id_tuples = set(itertools.product(stages, hubs, ecs))
        dupe_tuples = previous_tuples.intersection(id_tuples)
        if len(dupe_tuples) > 0:
            msg = "Overlap detected in export module: " + \
                f"The (stage, hub, ec) tuples {dupe_tuples} occur in more " + \
                "than one export entry"
            raise exceptions.ParsingException(export_node.file_path, msg,
                                              module=LOG_MODULE_STR)
        for (stage_id, hub_id, ec_id) in id_tuples:
            _parse_export_tuple(stage_id, hub_id, ec_id, export_node, exports)

    # Logging
    _log_exports(exports)
    # Return
    return exports


def _parse_import_tuple(s: StageId, h: HubId, e: EcId,
                        node: yaml_parser.YamlNode, imports: Imports
                        ) -> None:
    # tuple
    imports.add_tuple(s, h, e)
    # price
    price = yaml_parser.parse_optional_float_value_from_dict_node(
        node, YAMLKEY_PRICE)
    if price is not None:
        imports.set_price_def(s, h, e, price)
    # co2
    co2 = yaml_parser.parse_optional_float_value_from_dict_node(
        node, YAMLKEY_CO2)
    if co2 is not None:
        imports.set_co2_def(s, h, e, co2)
    # min
    imp_min = yaml_parser.parse_optional_float_value_from_dict_node(
        node, YAMLKEY_MIN)
    if imp_min is not None:
        imports.set_min_def(s, h, e, imp_min)
    # max
    imp_max = yaml_parser.parse_optional_float_value_from_dict_node(
        node, YAMLKEY_MAX)
    if imp_max is not None:
        imports.set_max_def(s, h, e, imp_max)
    # sum_min
    sum_min = yaml_parser.parse_optional_float_value_from_dict_node(
        node, YAMLKEY_SUMMIN)
    if sum_min is not None:
        imports.set_sum_min(s, h, e, sum_min)
    # sum_max
    sum_max = yaml_parser.parse_optional_float_value_from_dict_node(
        node, YAMLKEY_SUMMAX)
    if sum_max is not None:
        imports.set_sum_max(s, h, e, sum_max)
    # profiles
    profile_path = yaml_parser.parse_optional_str_value_from_dict_node(
        node, YAMLKEY_PROFILEPATH)
    if profile_path is not None:
        profile_path = os.path.abspath(os.path.join(
            node.file_path, os.pardir, profile_path))
        _parse_import_profiles(profile_path, s, h, e, imports)


def _parse_export_tuple(s: StageId, h: HubId, e: EcId,
                        node: yaml_parser.YamlNode, exports: Exports
                        ) -> None:
    # tuple
    exports.add_tuple(s, h, e)
    # price
    price = yaml_parser.parse_optional_float_value_from_dict_node(
        node, YAMLKEY_PRICE)
    if price is not None:
        exports.set_price_def(s, h, e, price)
    # co2
    co2 = yaml_parser.parse_optional_float_value_from_dict_node(
        node, YAMLKEY_CO2)
    if co2 is not None:
        exports.set_co2_def(s, h, e, co2)
    # min
    exp_min = yaml_parser.parse_optional_float_value_from_dict_node(
        node, YAMLKEY_MIN)
    if exp_min is not None:
        exports.set_min_def(s, h, e, exp_min)
    # max
    exp_max = yaml_parser.parse_optional_float_value_from_dict_node(
        node, YAMLKEY_MAX)
    if exp_max is not None:
        exports.set_max_def(s, h, e, exp_max)
    # sum_min
    sum_min = yaml_parser.parse_optional_float_value_from_dict_node(
        node, YAMLKEY_SUMMIN)
    if sum_min is not None:
        exports.set_sum_min(s, h, e, sum_min)
    # sum_max
    sum_max = yaml_parser.parse_optional_float_value_from_dict_node(
        node, YAMLKEY_SUMMAX)
    if sum_max is not None:
        exports.set_sum_max(s, h, e, sum_max)
    # profiles
    profile_path = yaml_parser.parse_optional_str_value_from_dict_node(
        node, YAMLKEY_PROFILEPATH)
    if profile_path is not None:
        profile_path = os.path.abspath(os.path.join(
            node.file_path, os.pardir, profile_path))
        _parse_export_profiles(profile_path, s, h, e, exports)


def _parse_import_profiles(profile_path: str, stage_id: StageId, hub_id: HubId,
                           ec_id: EcId, imports: Imports) -> None:
    yaml_parser.check_file_exists(profile_path, FILETYPE_IMPEXPPROFILE)
    df_profiles = csv_parser.parse(profile_path,
        header_ids=[csv_parser.HeaderId.STAGEID, csv_parser.HeaderId.HUBID,
                    csv_parser.HeaderId.ECID, csv_parser.HeaderId.PROFILEKEY])
    for (s, h, e, key) in df_profiles.columns:
        if s != stage_id.key:
            continue
        if h != hub_id.key:
            continue
        if e != ec_id.key:
            continue
        if key == YAMLKEY_PRICE:
            for t in df_profiles.index:
                imports.set_price(stage_id, hub_id, ec_id, TimeId(t),
                                  df_profiles[s, h, e, key][t])
        if key == YAMLKEY_CO2:
            for t in df_profiles.index:
                imports.set_co2(stage_id, hub_id, ec_id, TimeId(t),
                                df_profiles[s, h, e, key][t])
        if key == YAMLKEY_MIN:
            for t in df_profiles.index:
                imports.set_min(stage_id, hub_id, ec_id, TimeId(t),
                                df_profiles[s, h, e, key][t])
        if key == YAMLKEY_MAX:
            for t in df_profiles.index:
                imports.set_max(stage_id, hub_id, ec_id, TimeId(t),
                                df_profiles[s, h, e, key][t])


def _parse_export_profiles(profile_path: str, stage_id: StageId, hub_id: HubId,
                           ec_id: EcId, exports: Exports) -> None:
    yaml_parser.check_file_exists(profile_path, FILETYPE_IMPEXPPROFILE)
    df_profiles = csv_parser.parse(profile_path,
        header_ids=[csv_parser.HeaderId.STAGEID, csv_parser.HeaderId.HUBID,
                    csv_parser.HeaderId.ECID, csv_parser.HeaderId.PROFILEKEY])
    for (s, h, e, key) in df_profiles.columns:
        if s != stage_id.key:
            continue
        if h != hub_id.key:
            continue
        if e != ec_id.key:
            continue
        if key == YAMLKEY_PRICE:
            for t in df_profiles.index:
                exports.set_price(stage_id, hub_id, ec_id, TimeId(t),
                                  df_profiles[s, h, e, key][t])
        if key == YAMLKEY_CO2:
            for t in df_profiles.index:
                exports.set_co2(stage_id, hub_id, ec_id, TimeId(t),
                                df_profiles[s, h, e, key][t])
        if key == YAMLKEY_MIN:
            for t in df_profiles.index:
                exports.set_min(stage_id, hub_id, ec_id, TimeId(t),
                                df_profiles[s, h, e, key][t])
        if key == YAMLKEY_MAX:
            for t in df_profiles.index:
                exports.set_max(stage_id, hub_id, ec_id, TimeId(t),
                                df_profiles[s, h, e, key][t])


def _log_imports(imports: Imports) -> None:
    logging.log_file((f"Parsed {len(imports.tuples)} import (stage, hub, ec) "
                      "tuples"), module=LOG_MODULE_STR)
    for (s, h, e) in imports.tuples:
        logging.log_file(f"  Import tuple ({s}, {h}, {e})", print_time=False)


def _log_exports(exports: Exports) -> None:
    logging.log_file((f"Parsed {len(exports.tuples)} export (stage, hub, ec) "
                      "tuples"), module=LOG_MODULE_STR)
    for (s, h, e) in exports.tuples:
        logging.log_file(f"  Export tuple ({s}, {h}, {e})", print_time=False)
