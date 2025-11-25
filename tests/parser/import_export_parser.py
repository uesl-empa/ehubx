import itertools
import os
from typing import Set, Tuple

import pandas as pd

import ehubx.data.exceptions as data_exceptions
from ehubx.core import logging
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.export_data import Exports
from ehubx.data.hub_data import HubId
from ehubx.data.import_data import Imports
from ehubx.data.stage_data import StageId
from ehubx.data.time_data import TimeId
from ehubx.data.unit import CurrencyUnit, MassUnit, TimeUnit, Unit
from ehubx.data.value import Value
from ehubx.parser import csv_parser, exceptions, yaml_parser


# YAML keys
YAMLKEY_STAGES = "stages"
YAMLKEY_HUBS = "hubs"
YAMLKEY_EC = "ec"
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


def parse_imports(basic_subpath: str, ecs: Ecs) -> Imports:
    imports = Imports()
    import_file_path = os.path.join(basic_subpath, FILE_IMPORTS)
    if not os.path.isfile(import_file_path):
        return imports
    import_root_node = yaml_parser.parse(import_file_path)
    if import_root_node is None:
        return imports
    yaml_parser.check_node_type(import_root_node, yaml_parser.YamlNodeKind.LIST)
    # Iterate over list
    previous_tuples: Set[Tuple[StageId, HubId, EcId]] = set()
    for import_node in import_root_node:
        yaml_parser.check_node_type(import_node, yaml_parser.YamlNodeKind.DICT)
        # stages
        stages_str = yaml_parser.parse_str_list_from_dict_node(
            import_node, YAMLKEY_STAGES, optional=False
        )
        stage_ids = {StageId(stage_str) for stage_str in stages_str}
        # hubs
        hubs_str = yaml_parser.parse_str_list_from_dict_node(
            import_node, YAMLKEY_HUBS, optional=False
        )
        hub_ids = {HubId(hub_str) for hub_str in hubs_str}
        # ec
        ec_str = yaml_parser.parse_mandatory_str_from_dict_node(import_node, YAMLKEY_EC)
        ec_id = EcId(ec_str)
        # Id tuples
        stage_hub_tuples = set(itertools.product(stage_ids, hub_ids))
        dupe_tuples = previous_tuples.intersection(
            {(stage_id, hub_id, ec_id) for (stage_id, hub_id) in stage_hub_tuples}
        )
        if len(dupe_tuples) > 0:
            raise exceptions.ParsingException(
                import_node.file_path,
                "Overlap detected in import module: The (stage, hub, ec) tuples "
                f"{dupe_tuples} occur in more than one import entry",
                module=LOG_MODULE_STR,
            )
        _parse_import_node(
            import_node, stage_hub_tuples, ec_id, ecs.get_unit(ec_id), imports
        )
        # Remember encountered tuples
        previous_tuples = previous_tuples.union(
            {(stage_id, hub_id, ec_id) for (stage_id, hub_id) in stage_hub_tuples}
        )

    # Logging
    _log_imports(imports)
    # Return
    return imports


def parse_exports(basic_subpath: str, ecs: Ecs) -> Exports:
    exports = Exports()
    export_file_path = os.path.join(basic_subpath, FILE_EXPORTS)
    if not os.path.isfile(export_file_path):
        return exports
    export_root_node = yaml_parser.parse(export_file_path)
    if export_root_node is None:
        return exports
    yaml_parser.check_node_type(export_root_node, yaml_parser.YamlNodeKind.LIST)
    # Iterate over list
    previous_tuples: Set[Tuple[StageId, HubId, EcId]] = set()
    for export_node in export_root_node:
        yaml_parser.check_node_type(export_node, yaml_parser.YamlNodeKind.DICT)
        # stages
        stages_str = yaml_parser.parse_str_list_from_dict_node(
            export_node, YAMLKEY_STAGES, optional=False
        )
        stage_ids = {StageId(stage_str) for stage_str in stages_str}
        # hubs
        hubs_str = yaml_parser.parse_str_list_from_dict_node(
            export_node, YAMLKEY_HUBS, optional=False
        )
        hub_ids = {HubId(hub_str) for hub_str in hubs_str}
        # ec
        ec_str = yaml_parser.parse_mandatory_str_from_dict_node(export_node, YAMLKEY_EC)
        ec_id = EcId(ec_str)
        # Id tuples
        stage_hub_tuples = set(itertools.product(stage_ids, hub_ids))
        dupe_tuples = previous_tuples.intersection(
            {(stage_id, hub_id, ec_id) for (stage_id, hub_id) in stage_hub_tuples}
        )
        if len(dupe_tuples) > 0:
            raise exceptions.ParsingException(
                export_node.file_path,
                "Overlap detected in export module: The (stage, hub, ec) tuples "
                f"{dupe_tuples} occur in more than one export entry",
                module=LOG_MODULE_STR,
            )
        _parse_export_node(
            export_node, stage_hub_tuples, ec_id, ecs.get_unit(ec_id), exports
        )
        # Remember encountered tuples
        previous_tuples = previous_tuples.union(
            {(stage_id, hub_id, ec_id) for (stage_id, hub_id) in stage_hub_tuples}
        )

    # Logging
    _log_exports(exports)
    # Return
    return exports


def _parse_import_node(
    node: yaml_parser.YamlDictNode,
    stage_hub_tuples: Set[Tuple[StageId, HubId]],
    ec_id: EcId,
    ec_unit: Unit,
    imports: Imports,
) -> None:
    # price
    price = yaml_parser.parse_optional_value_from_dict_node(
        node, YAMLKEY_PRICE, expected_unit=(CurrencyUnit.CHF / ec_unit)
    )
    # co2
    co2 = yaml_parser.parse_optional_value_from_dict_node(
        node, YAMLKEY_CO2, expected_unit=(MassUnit.KG / ec_unit)
    )
    # min
    imp_min = yaml_parser.parse_optional_value_from_dict_node(
        node, YAMLKEY_MIN, expected_unit=(ec_unit / TimeUnit.H)
    )
    # max
    imp_max = yaml_parser.parse_optional_value_from_dict_node(
        node, YAMLKEY_MAX, expected_unit=(ec_unit / TimeUnit.H)
    )
    # sum_min
    sum_min = yaml_parser.parse_optional_value_from_dict_node(
        node, YAMLKEY_SUMMIN, expected_unit=ec_unit
    )
    # sum_max
    sum_max = yaml_parser.parse_optional_value_from_dict_node(
        node, YAMLKEY_SUMMAX, expected_unit=ec_unit
    )

    # Write def values to data model
    for stage_id, hub_id in stage_hub_tuples:
        imports.add_tuple(stage_id, hub_id, ec_id, ec_unit)
        if price is not None:
            imports.set_price_def(stage_id, hub_id, ec_id, price)
        if co2 is not None:
            imports.set_co2_def(stage_id, hub_id, ec_id, co2)
        if imp_min is not None:
            imports.set_min_def(stage_id, hub_id, ec_id, imp_min)
        if imp_max is not None:
            imports.set_max_def(stage_id, hub_id, ec_id, imp_max)
        if sum_min is not None:
            imports.set_sum_min(stage_id, hub_id, ec_id, sum_min)
        if sum_max is not None:
            imports.set_sum_max(stage_id, hub_id, ec_id, sum_max)

    # profiles
    profile_path = yaml_parser.parse_optional_str_from_dict_node(
        node, YAMLKEY_PROFILEPATH
    )
    if profile_path is not None:
        profile_path = os.path.abspath(
            os.path.join(node.file_path, os.pardir, profile_path)
        )
        yaml_parser.check_file_exists(profile_path, FILETYPE_IMPEXPPROFILE)
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
            _parse_import_profiles(
                df_profiles, profile_path, stage_id, hub_id, ec_id, ec_unit, imports
            )


def _parse_export_node(
    node: yaml_parser.YamlDictNode,
    stage_hub_tuples: Set[Tuple[StageId, HubId]],
    ec_id: EcId,
    ec_unit: Unit,
    exports: Exports,
) -> None:
    # price
    price = yaml_parser.parse_optional_value_from_dict_node(
        node, YAMLKEY_PRICE, expected_unit=(CurrencyUnit.CHF / ec_unit)
    )
    # co2
    co2 = yaml_parser.parse_optional_value_from_dict_node(
        node, YAMLKEY_CO2, expected_unit=(MassUnit.KG / ec_unit)
    )
    # min
    exp_min = yaml_parser.parse_optional_value_from_dict_node(
        node, YAMLKEY_MIN, expected_unit=(ec_unit / TimeUnit.H)
    )
    # max
    exp_max = yaml_parser.parse_optional_value_from_dict_node(
        node, YAMLKEY_MAX, expected_unit=(ec_unit / TimeUnit.H)
    )
    # sum_min
    sum_min = yaml_parser.parse_optional_value_from_dict_node(
        node, YAMLKEY_SUMMIN, expected_unit=ec_unit
    )
    # sum_max
    sum_max = yaml_parser.parse_optional_value_from_dict_node(
        node, YAMLKEY_SUMMAX, expected_unit=ec_unit
    )

    # Write def values to data model
    for stage_id, hub_id in stage_hub_tuples:
        exports.add_tuple(stage_id, hub_id, ec_id, ec_unit)
        if price is not None:
            exports.set_price_def(stage_id, hub_id, ec_id, price)
        if co2 is not None:
            exports.set_co2_def(stage_id, hub_id, ec_id, co2)
        if exp_min is not None:
            exports.set_min_def(stage_id, hub_id, ec_id, exp_min)
        if exp_max is not None:
            exports.set_max_def(stage_id, hub_id, ec_id, exp_max)
        if sum_min is not None:
            exports.set_sum_min(stage_id, hub_id, ec_id, sum_min)
        if sum_max is not None:
            exports.set_sum_max(stage_id, hub_id, ec_id, sum_max)

    # profiles
    profile_path = yaml_parser.parse_optional_str_from_dict_node(
        node, YAMLKEY_PROFILEPATH
    )
    if profile_path is not None:
        profile_path = os.path.abspath(
            os.path.join(node.file_path, os.pardir, profile_path)
        )
        yaml_parser.check_file_exists(profile_path, FILETYPE_IMPEXPPROFILE)
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
            _parse_export_profiles(
                df_profiles, profile_path, stage_id, hub_id, ec_id, ec_unit, exports
            )


def _parse_import_profiles(
    df_profiles: pd.DataFrame,
    profile_path: str,
    stage_id: StageId,
    hub_id: HubId,
    ec_id: EcId,
    ec_unit: Unit,
    imports: Imports,
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
                f"Invalid unit '{ex.unit}' for import profile key '{key}' "
                f"for (stage, hub, ec) tuple ({s}, {h}, {e})",
                module=LOG_MODULE_STR,
            ) from ex

        expected_unit: Unit
        check_unit: bool = True
        if key == YAMLKEY_PRICE:
            expected_unit = CurrencyUnit.CHF / ec_unit
        elif key == YAMLKEY_CO2:
            expected_unit = MassUnit.KG / ec_unit
        elif key in (YAMLKEY_MIN, YAMLKEY_MAX):
            expected_unit = ec_unit / TimeUnit.H
        elif key in (YAMLKEY_SUMMIN, YAMLKEY_SUMMAX):
            expected_unit = ec_unit
        else:
            check_unit = False

        if check_unit and not unit.same_type_as(expected_unit):
            raise exceptions.ParsingException(
                profile_path,
                f"Invalid unit '{unit}' for import profile key '{key}' "
                f"for (stage, hub, ec) tuple ({s}, {h}, {e}). Expected a unit "
                f"like '{expected_unit}'.",
                module=LOG_MODULE_STR,
            )

        if key == YAMLKEY_PRICE:
            for t, val in df_profiles[s, h, e, key].items():
                imports.set_price(stage_id, hub_id, ec_id, TimeId(t), Value(val, unit))
        if key == YAMLKEY_CO2:
            for t, val in df_profiles[s, h, e, key].items():
                imports.set_co2(stage_id, hub_id, ec_id, TimeId(t), Value(val, unit))
        if key == YAMLKEY_MIN:
            for t, val in df_profiles[s, h, e, key].items():
                imports.set_min(stage_id, hub_id, ec_id, TimeId(t), Value(val, unit))
        if key == YAMLKEY_MAX:
            for t, val in df_profiles[s, h, e, key].items():
                imports.set_max(stage_id, hub_id, ec_id, TimeId(t), Value(val, unit))


def _parse_export_profiles(
    df_profiles: pd.DataFrame,
    profile_path: str,
    stage_id: StageId,
    hub_id: HubId,
    ec_id: EcId,
    ec_unit: Unit,
    exports: Exports,
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
                f"Invalid unit '{ex.unit}' for export profile key '{key}' "
                f"for (stage, hub, ec) tuple ({s}, {h}, {e})",
                module=LOG_MODULE_STR,
            ) from ex

        expected_unit: Unit
        check_unit: bool = True
        if key == YAMLKEY_PRICE:
            expected_unit = CurrencyUnit.CHF / ec_unit
        elif key == YAMLKEY_CO2:
            expected_unit = MassUnit.KG / ec_unit
        elif key in (YAMLKEY_MIN, YAMLKEY_MAX):
            expected_unit = ec_unit / TimeUnit.H
        elif key in (YAMLKEY_SUMMIN, YAMLKEY_SUMMAX):
            expected_unit = ec_unit
        else:
            check_unit = False

        if check_unit and not unit.same_type_as(expected_unit):
            raise exceptions.ParsingException(
                profile_path,
                f"Invalid unit '{unit}' for export profile key '{key}' "
                f"for (stage, hub, ec) tuple ({s}, {h}, {e}). Expected a unit "
                f"like '{expected_unit}'.",
                module=LOG_MODULE_STR,
            )

        if key == YAMLKEY_PRICE:
            for t, val in df_profiles[s, h, e, key].items():
                exports.set_price(stage_id, hub_id, ec_id, TimeId(t), Value(val, unit))
        if key == YAMLKEY_CO2:
            for t, val in df_profiles[s, h, e, key].items():
                exports.set_co2(stage_id, hub_id, ec_id, TimeId(t), Value(val, unit))
        if key == YAMLKEY_MIN:
            for t, val in df_profiles[s, h, e, key].items():
                exports.set_min(stage_id, hub_id, ec_id, TimeId(t), Value(val, unit))
        if key == YAMLKEY_MAX:
            for t, val in df_profiles[s, h, e, key].items():
                exports.set_max(stage_id, hub_id, ec_id, TimeId(t), Value(val, unit))


def _log_imports(imports: Imports) -> None:
    logging.log_file(
        (f"Parsed {len(imports.tuples)} import (stage, hub, ec) tuples"),
        module=LOG_MODULE_STR,
    )
    for s, h, e in imports.tuples:
        logging.log_file(f"  Import tuple ({s}, {h}, {e})", print_time=False)


def _log_exports(exports: Exports) -> None:
    logging.log_file(
        (f"Parsed {len(exports.tuples)} export (stage, hub, ec) tuples"),
        module=LOG_MODULE_STR,
    )
    for s, h, e in exports.tuples:
        logging.log_file(f"  Export tuple ({s}, {h}, {e})", print_time=False)
