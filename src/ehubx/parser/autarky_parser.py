from typing import Optional
from ehubx.data.autarky_data import Autarky, AutarkyCalculationMethod
from ehubx.parser import yaml_parser
from ehubx.parser import exceptions

# YAML keys
YAMLKEY_SYSTEMPARAMS = "system_params"
YAMLKEY_AUTCALCMETHOD = "autarky_calculation_method"
YAMLKEY_AUTCALCMETHOD_LIN = "linearized"
YAMLKEY_AUTCALCMETHOD_QUAD = "quadratic"
YAMLKEY_AUTCALCMETHOD_NONE = "none"
YAMLKEY_AUTARKYMIN = "autarky_min"
YAMLKEY_AUTARKYMAX = "autarky_max"

# Literals
LOG_MODULE_STR: str = "pars/autarky"


def parse(stage_root_node: Optional[yaml_parser.YamlNode]) -> Autarky:
    autarky = Autarky()
    if stage_root_node is None:
        return autarky
    system_params_node = yaml_parser.get_mandatory_subnode_from_dict_node(
        stage_root_node, YAMLKEY_SYSTEMPARAMS)
    # autarky_calculation_method
    aut_calc_method = yaml_parser.parse_optional_str_value_from_dict_node(
        system_params_node, YAMLKEY_AUTCALCMETHOD)
    if aut_calc_method is not None:
        if aut_calc_method == YAMLKEY_AUTCALCMETHOD_LIN:
            autarky.calculation_method = AutarkyCalculationMethod.LINEARIZED
        elif aut_calc_method == YAMLKEY_AUTCALCMETHOD_QUAD:
            autarky.calculation_method = AutarkyCalculationMethod.QUADRATIC
        elif aut_calc_method == YAMLKEY_AUTCALCMETHOD_NONE:
            autarky.calculation_method = AutarkyCalculationMethod.NONE
        else:
            node_path_str = (system_params_node.node_path_as_str
                             + "|" + YAMLKEY_AUTCALCMETHOD)
            invalidity_reason = (f"{aut_calc_method} is not a known autarky "
                                 "calculation method")
            raise exceptions.InvalidValueException(
                stage_root_node.file_path, node_path_str, invalidity_reason,
                module=LOG_MODULE_STR)
    # autarky_min
    autarky_min = yaml_parser.parse_optional_float_value_from_dict_node(
        system_params_node, YAMLKEY_AUTARKYMIN)
    if autarky_min is not None:
        autarky.autarky_min = autarky_min
    # autarky_max
    autarky_max = yaml_parser.parse_optional_float_value_from_dict_node(
        system_params_node, YAMLKEY_AUTARKYMAX)
    if autarky_max is not None:
        autarky.autarky_max = autarky_max
    # Return
    return autarky
