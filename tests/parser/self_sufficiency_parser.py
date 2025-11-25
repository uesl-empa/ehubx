from typing import Optional

from ehubx.data.self_sufficiency_data import (
    SelfSufficiency,
    SelfSufficiencyCalculationMethod,
)
from ehubx.data.unit import DimlessUnit
from ehubx.parser import exceptions, yaml_parser


# YAML keys
YAMLKEY_SYSTEMPARAMS = "system_params"
YAMLKEY_SELFSUFFCALCMETHOD = "self_sufficiency_calculation_method"
YAMLKEY_SELFSUFFCALCMETHOD_LIN = "linearized"
YAMLKEY_SELFSUFFCALCMETHOD_QUAD = "quadratic"
YAMLKEY_SELFSUFFCALCMETHOD_NONE = "none"
YAMLKEY_SELFSUFFMIN = "self_sufficiency_min"
YAMLKEY_SELFSUFFMAX = "self_sufficiency_max"

# Literals
LOG_MODULE_STR: str = "pars/self_suff"


def parse(stage_root_node: Optional[yaml_parser.YamlNode]) -> SelfSufficiency:
    self_sufficiency = SelfSufficiency()
    if stage_root_node is None:
        return self_sufficiency
    system_params_node = yaml_parser.get_mandatory_subnode_from_dict_node(
        stage_root_node, YAMLKEY_SYSTEMPARAMS
    )
    # self_sufficiency_calculation_method
    self_suff_calc_method = yaml_parser.parse_optional_str_from_dict_node(
        system_params_node, YAMLKEY_SELFSUFFCALCMETHOD
    )
    if self_suff_calc_method is not None:
        if self_suff_calc_method == YAMLKEY_SELFSUFFCALCMETHOD_LIN:
            self_sufficiency.calculation_method = (
                SelfSufficiencyCalculationMethod.LINEARIZED
            )
        elif self_suff_calc_method == YAMLKEY_SELFSUFFCALCMETHOD_QUAD:
            self_sufficiency.calculation_method = (
                SelfSufficiencyCalculationMethod.QUADRATIC
            )
        elif self_suff_calc_method == YAMLKEY_SELFSUFFCALCMETHOD_NONE:
            self_sufficiency.calculation_method = SelfSufficiencyCalculationMethod.NONE
        else:
            node_path_str = (
                system_params_node.node_path_as_str + "|" + YAMLKEY_SELFSUFFCALCMETHOD
            )
            invalidity_reason = (
                f"{self_suff_calc_method} is not a known self-sufficiency "
                "calculation method"
            )
            raise exceptions.InvalidValueException(
                stage_root_node.file_path,
                node_path_str,
                invalidity_reason,
                module=LOG_MODULE_STR,
            )
    # self_sufficiency_min
    self_sufficiency_min = yaml_parser.parse_optional_value_from_dict_node(
        system_params_node, YAMLKEY_SELFSUFFMIN, expected_unit=DimlessUnit()
    )
    if self_sufficiency_min is not None:
        self_sufficiency.self_sufficiency_min = self_sufficiency_min
    # self_sufficiency_max
    self_sufficiency_max = yaml_parser.parse_optional_value_from_dict_node(
        system_params_node, YAMLKEY_SELFSUFFMAX, expected_unit=DimlessUnit()
    )
    if self_sufficiency_max is not None:
        self_sufficiency.self_sufficiency_max = self_sufficiency_max
    # Return
    return self_sufficiency
