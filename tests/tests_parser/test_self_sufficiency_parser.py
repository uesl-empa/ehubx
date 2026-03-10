"""
Tests for self_sufficiency_parser module
"""

import pytest

from ehubx.data.self_sufficiency_data import SelfSufficiencyCalculationMethod
from ehubx.data.unit import DimlessUnit
from ehubx.parser import exceptions, self_sufficiency_parser, yaml_parser


def _write_yaml(tmp_path, name: str, content: str):
    path = tmp_path / name
    path.write_text(content)
    return path


# =============================================================================
# Tests for parse()
# =============================================================================


def test_parse_none_returns_defaults():
    self_sufficiency = self_sufficiency_parser.parse(None)

    assert (
        self_sufficiency.calculation_method
        == SelfSufficiencyCalculationMethod.NONE
    )
    assert self_sufficiency.self_sufficiency_min.to_float(DimlessUnit()) == 0
    assert self_sufficiency.self_sufficiency_max.to_float(DimlessUnit()) == 1


@pytest.mark.parametrize(
    ("method_str", "expected"),
    [
        ("linearized", SelfSufficiencyCalculationMethod.LINEARIZED),
        ("quadratic", SelfSufficiencyCalculationMethod.QUADRATIC),
        ("none", SelfSufficiencyCalculationMethod.NONE),
    ],
)
def test_parse_sets_calculation_method(tmp_path, method_str, expected):
    yaml_content = f"""system_params:
  self_sufficiency_calculation_method: {method_str}
"""
    _write_yaml(tmp_path, "stage.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "stage.yaml"))
    self_sufficiency = self_sufficiency_parser.parse(root_node)

    assert self_sufficiency.calculation_method == expected


def test_parse_sets_min_max_values(tmp_path):
    yaml_content = """system_params:
  self_sufficiency_min: 0.25
  self_sufficiency_max: 0.75
"""
    _write_yaml(tmp_path, "stage.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "stage.yaml"))
    self_sufficiency = self_sufficiency_parser.parse(root_node)

    assert self_sufficiency.self_sufficiency_min.to_float(DimlessUnit()) == 0.25
    assert self_sufficiency.self_sufficiency_max.to_float(DimlessUnit()) == 0.75
    assert (
        self_sufficiency.calculation_method
        == SelfSufficiencyCalculationMethod.NONE
    )


def test_parse_missing_system_params_raises_exception(tmp_path):
    yaml_content = """other:
  value: 1
"""
    _write_yaml(tmp_path, "stage.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "stage.yaml"))

    with pytest.raises(exceptions.MissingNodeException):
        self_sufficiency_parser.parse(root_node)


def test_parse_invalid_calc_method_raises_exception(tmp_path):
    yaml_content = """system_params:
  self_sufficiency_calculation_method: invalid
"""
    _write_yaml(tmp_path, "stage.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "stage.yaml"))

    with pytest.raises(exceptions.InvalidValueException) as excinfo:
        self_sufficiency_parser.parse(root_node)

    assert "calculation method" in str(excinfo.value)


def test_parse_min_unit_mismatch_raises_exception(tmp_path):
    yaml_content = """system_params:
  self_sufficiency_min: 1 kW
"""
    _write_yaml(tmp_path, "stage.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "stage.yaml"))

    with pytest.raises(exceptions.InvalidValueException) as excinfo:
        self_sufficiency_parser.parse(root_node)

    assert "Unit mismatch" in str(excinfo.value)


def test_parse_invalid_min_value_raises_exception(tmp_path):
    yaml_content = """system_params:
  self_sufficiency_min: not_a_number
"""
    _write_yaml(tmp_path, "stage.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "stage.yaml"))

    with pytest.raises(exceptions.InvalidValueException) as excinfo:
        self_sufficiency_parser.parse(root_node)

    assert "Invalid value" in str(excinfo.value)
