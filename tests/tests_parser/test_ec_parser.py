"""
Tests for ec_parser module
"""

import pytest

from ehubx.data.ec_data import EcId, Ecs, ImpExpType
from ehubx.data.unit import MassUnit, PowerUnit, TimeUnit
from ehubx.parser import ec_parser, exceptions, yaml_parser


def _write_yaml(tmp_path, name, content: str):
    """Helper to write YAML file"""
    path = tmp_path / name
    path.write_text(content)
    return path


# ============================================================================
# Tests for parse() function - main entry point
# ============================================================================


def test_parse_missing_file_returns_empty_ecs(tmp_path):
    """Test that missing ecs.yaml file returns empty Ecs object and None"""
    ecs, root_node = ec_parser.parse(str(tmp_path))

    assert isinstance(ecs, Ecs)
    assert len(ecs.ids) == 0
    assert root_node is None


def test_parse_file_with_single_ec(tmp_path):
    """Test parsing file with a single energy carrier"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kWh
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, root_node = ec_parser.parse(str(tmp_path))

    assert root_node is not None
    assert len(ecs.ids) == 1
    assert EcId("E0") in ecs.ids
    assert ecs.get_unit(EcId("E0")) == PowerUnit.KW * TimeUnit.H


def test_parse_file_with_multiple_ecs(tmp_path):
    """Test parsing file with multiple energy carriers"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kWh
  - ec_id: E1
    unit: kg
  - ec_id: E2
    unit: MWh
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, root_node = ec_parser.parse(str(tmp_path))

    assert len(ecs.ids) == 3
    assert EcId("E0") in ecs.ids
    assert EcId("E1") in ecs.ids
    assert EcId("E2") in ecs.ids
    assert ecs.get_unit(EcId("E0")) == PowerUnit.KW * TimeUnit.H
    assert ecs.get_unit(EcId("E1")) == MassUnit.KG
    assert ecs.get_unit(EcId("E2")) == PowerUnit.MW * TimeUnit.H


def test_parse_empty_yaml_file(tmp_path):
    """Test parsing empty YAML file"""
    _write_yaml(tmp_path, "ecs.yaml", "")

    ecs, root_node = ec_parser.parse(str(tmp_path))

    # Empty file returns None from yaml_parser.parse, so we get empty ecs
    assert isinstance(ecs, Ecs)
    assert len(ecs.ids) == 0
    assert root_node is None


def test_parse_yaml_with_no_ecs_key(tmp_path):
    """Test parsing YAML with no 'ecs' key"""
    yaml_content = """some_other_key:
  - value1
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, root_node = ec_parser.parse(str(tmp_path))

    # Should return empty ecs and the root node
    assert isinstance(ecs, Ecs)
    assert len(ecs.ids) == 0
    assert root_node is not None


def test_parse_empty_ecs_list(tmp_path):
    """Test parsing with empty ecs list"""
    yaml_content = """ecs: []
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    assert len(ecs.ids) == 0


def test_parse_returns_root_node(tmp_path):
    """Test that parse returns the root YAML node"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kWh
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, root_node = ec_parser.parse(str(tmp_path))

    assert root_node is not None
    assert root_node.node_kind == yaml_parser.YamlNodeKind.DICT


# ============================================================================
# Tests for _parse_ec() function - individual EC parsing
# ============================================================================


def test_parse_ec_with_mandatory_fields_only(tmp_path):
    """Test parsing EC with only mandatory fields (ec_id and unit)"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kWh
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    ec_id = EcId("E0")
    assert ec_id in ecs.ids
    assert ecs.get_unit(ec_id) == PowerUnit.KW * TimeUnit.H
    assert ecs.is_energy(ec_id) is True  # Default value
    assert ecs.get_imp_exp_type(ec_id) == ImpExpType.NONE  # Default value


def test_parse_ec_with_mass_unit(tmp_path):
    """Test parsing EC with mass unit"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kg
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    ec_id = EcId("E0")
    assert ecs.get_unit(ec_id) == MassUnit.KG


def test_parse_ec_with_energy_unit(tmp_path):
    """Test parsing EC with various energy units"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kWh
  - ec_id: E1
    unit: MWh
  - ec_id: E2
    unit: kW*h
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    assert ecs.get_unit(EcId("E0")) == PowerUnit.KW * TimeUnit.H
    assert ecs.get_unit(EcId("E1")) == PowerUnit.MW * TimeUnit.H
    assert ecs.get_unit(EcId("E2")) == PowerUnit.KW * TimeUnit.H


def test_parse_ec_with_invalid_unit_raises_exception(tmp_path):
    """Test that invalid unit raises InvalidValueException"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: m  # Invalid - not mass or energy
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    with pytest.raises(exceptions.InvalidValueException) as exc_info:
        ec_parser.parse(str(tmp_path))

    assert "Invalid unit" in str(exc_info.value)
    assert "Only mass units or energy units are allowed" in str(exc_info.value)


def test_parse_ec_with_is_energy_true(tmp_path):
    """Test parsing EC with is_energy set to true"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kWh
    is_energy: true
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    assert ecs.is_energy(EcId("E0")) is True


def test_parse_ec_with_is_energy_false(tmp_path):
    """Test parsing EC with is_energy set to false"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kg
    is_energy: false
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    assert ecs.is_energy(EcId("E0")) is False


def test_parse_ec_with_imp_exp_type_cross(tmp_path):
    """Test parsing EC with imp_exp_type set to 'cross'"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kWh
    imp_exp_type: cross
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    assert ecs.get_imp_exp_type(EcId("E0")) == ImpExpType.CROSS


def test_parse_ec_with_imp_exp_type_internal(tmp_path):
    """Test parsing EC with imp_exp_type set to 'internal'"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kWh
    imp_exp_type: internal
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    assert ecs.get_imp_exp_type(EcId("E0")) == ImpExpType.INTERNAL


def test_parse_ec_with_imp_exp_type_none(tmp_path):
    """Test parsing EC with imp_exp_type set to 'none'"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kWh
    imp_exp_type: none
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    assert ecs.get_imp_exp_type(EcId("E0")) == ImpExpType.NONE


def test_parse_ec_with_invalid_imp_exp_type_raises_exception(tmp_path):
    """Test that invalid imp_exp_type raises InvalidValueException"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kWh
    imp_exp_type: invalid_type
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    with pytest.raises(exceptions.InvalidValueException) as exc_info:
        ec_parser.parse(str(tmp_path))

    assert "is not a known import-export-type" in str(exc_info.value)


def test_parse_ec_with_heur_max_energy_unit(tmp_path):
    """Test parsing EC with heur_max parameter"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kWh
    heur_max: 100 kW
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    ec_id = EcId("E0")
    heur_max = ecs.get_heuristic_max(ec_id)
    assert heur_max.to_float(PowerUnit.KW) == 100


def test_parse_ec_with_heur_max_mass_unit(tmp_path):
    """Test parsing EC with heur_max parameter for mass unit"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kg
    heur_max: 50 kg/h
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    ec_id = EcId("E0")
    heur_max = ecs.get_heuristic_max(ec_id)
    assert heur_max.to_float(MassUnit.KG / TimeUnit.H) == 50


def test_parse_ec_with_heur_sum_max(tmp_path):
    """Test parsing EC with heur_sum_max parameter"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kWh
    heur_sum_max: 1000 kWh
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    ec_id = EcId("E0")
    heur_sum_max = ecs.get_heuristic_sum_max(ec_id)
    assert heur_sum_max.to_float(PowerUnit.KW * TimeUnit.H) == 1000


def test_parse_ec_with_heur_sum_max_mass_unit(tmp_path):
    """Test parsing EC with heur_sum_max parameter for mass unit"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kg
    heur_sum_max: 5000 kg
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    ec_id = EcId("E0")
    heur_sum_max = ecs.get_heuristic_sum_max(ec_id)
    assert heur_sum_max.to_float(MassUnit.KG) == 5000


def test_parse_ec_with_all_optional_fields(tmp_path):
    """Test parsing EC with all optional fields"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kWh
    is_energy: true
    imp_exp_type: cross
    heur_max: 100 kW
    heur_sum_max: 1000 kWh
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    ec_id = EcId("E0")
    assert ecs.is_energy(ec_id) is True
    assert ecs.get_imp_exp_type(ec_id) == ImpExpType.CROSS
    assert ecs.get_heuristic_max(ec_id).to_float(PowerUnit.KW) == 100
    assert ecs.get_heuristic_sum_max(ec_id).to_float(PowerUnit.KW * TimeUnit.H) == 1000


def test_parse_ec_with_underscore_in_id_logs_warning(tmp_path):
    """Test that EC ID with underscore logs a warning"""
    yaml_content = """ecs:
  - ec_id: E_0
    unit: kWh
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    # Parse should succeed but log warning
    ecs, _ = ec_parser.parse(str(tmp_path))

    assert EcId("E_0") in ecs.ids


def test_parse_ec_missing_mandatory_unit_raises_exception(tmp_path):
    """Test that missing mandatory unit raises exception"""
    yaml_content = """ecs:
  - ec_id: E0
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    with pytest.raises(exceptions.MissingNodeException):
        ec_parser.parse(str(tmp_path))


def test_parse_ec_missing_mandatory_ec_id_raises_exception(tmp_path):
    """Test that missing mandatory ec_id raises exception"""
    yaml_content = """ecs:
  - unit: kWh
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    with pytest.raises(exceptions.MissingNodeException):
        ec_parser.parse(str(tmp_path))


def test_parse_ecs_list_not_dict_raises_exception(tmp_path):
    """Test that ecs_node not being a list raises exception"""
    yaml_content = """ecs:
  ec_id: E0
  unit: kWh
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    with pytest.raises(exceptions.InvalidNodeTypeException):
        ec_parser.parse(str(tmp_path))


# ============================================================================
# Tests for complex scenarios and edge cases
# ============================================================================


def test_parse_multiple_ecs_with_mixed_configurations(tmp_path):
    """Test parsing multiple ECs with different configurations"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kWh
    is_energy: true
    imp_exp_type: cross
  - ec_id: E1
    unit: kg
    is_energy: false
    imp_exp_type: internal
  - ec_id: E2
    unit: MWh
    imp_exp_type: none
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    assert len(ecs.ids) == 3
    assert ecs.is_energy(EcId("E0")) is True
    assert ecs.get_imp_exp_type(EcId("E0")) == ImpExpType.CROSS
    assert ecs.is_energy(EcId("E1")) is False
    assert ecs.get_imp_exp_type(EcId("E1")) == ImpExpType.INTERNAL
    assert ecs.get_imp_exp_type(EcId("E2")) == ImpExpType.NONE


def test_parse_ecs_ids_order_preserved(tmp_path):
    """Test that order of EC IDs is sorted alphabetically in ids_in_order"""
    yaml_content = """ecs:
  - ec_id: Z0
    unit: kWh
  - ec_id: A0
    unit: kg
  - ec_id: M0
    unit: MWh
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    # ids_in_order returns them sorted alphabetically
    ids_in_order = list(ecs.ids_in_order)
    assert ids_in_order[0] == EcId("A0")
    assert ids_in_order[1] == EcId("M0")
    assert ids_in_order[2] == EcId("Z0")


def test_parse_with_yaml_root_not_dict_raises_exception(tmp_path):
    """Test that non-dict YAML root raises exception"""
    yaml_content = """- E0
- E1
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    with pytest.raises(exceptions.ParsingException):
        ec_parser.parse(str(tmp_path))


def test_parse_ec_with_zero_heur_max(tmp_path):
    """Test parsing EC with heur_max set to 0"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kWh
    heur_max: 0 kW
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    assert ecs.get_heuristic_max(EcId("E0")).to_float(PowerUnit.KW) == 0


def test_parse_ec_with_zero_heur_sum_max(tmp_path):
    """Test parsing EC with heur_sum_max set to 0"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kWh
    heur_sum_max: 0 kWh
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    assert ecs.get_heuristic_sum_max(EcId("E0")).to_float(PowerUnit.KW * TimeUnit.H) == 0


def test_parse_ec_with_large_heur_values(tmp_path):
    """Test parsing EC with large heuristic values"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kWh
    heur_max: 999999 kW
    heur_sum_max: 999999999 kWh
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    ec_id = EcId("E0")
    assert ecs.get_heuristic_max(ec_id).to_float(PowerUnit.KW) == 999999
    assert ecs.get_heuristic_sum_max(ec_id).to_float(PowerUnit.KW * TimeUnit.H) == 999999999


def test_parse_ec_with_fractional_heur_values(tmp_path):
    """Test parsing EC with fractional heuristic values"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kWh
    heur_max: 10.5 kW
    heur_sum_max: 100.25 kWh
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    ec_id = EcId("E0")
    assert ecs.get_heuristic_max(ec_id).to_float(PowerUnit.KW) == 10.5
    assert ecs.get_heuristic_sum_max(ec_id).to_float(PowerUnit.KW * TimeUnit.H) == 100.25


def test_parse_ec_unit_conversion(tmp_path):
    """Test that different unit representations are correctly parsed"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kW*h
  - ec_id: E1
    unit: MW*h
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    # Both should be energy units
    unit0 = ecs.get_unit(EcId("E0"))
    unit1 = ecs.get_unit(EcId("E1"))
    assert unit0.same_type_as(PowerUnit.KW * TimeUnit.H)
    assert unit1.same_type_as(PowerUnit.MW * TimeUnit.H)


# ============================================================================
# Tests for optional field combinations
# ============================================================================


def test_parse_ec_optional_field_only_is_energy(tmp_path):
    """Test parsing EC with only is_energy optional field"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kWh
    is_energy: false
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    ec_id = EcId("E0")
    assert ecs.is_energy(ec_id) is False
    assert ecs.get_imp_exp_type(ec_id) == ImpExpType.NONE  # Default


def test_parse_ec_optional_field_only_imp_exp_type(tmp_path):
    """Test parsing EC with only imp_exp_type optional field"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kWh
    imp_exp_type: internal
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    ec_id = EcId("E0")
    assert ecs.is_energy(ec_id) is True  # Default
    assert ecs.get_imp_exp_type(ec_id) == ImpExpType.INTERNAL


def test_parse_ec_optional_field_only_heur_max(tmp_path):
    """Test parsing EC with only heur_max optional field"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kWh
    heur_max: 50 kW
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    ec_id = EcId("E0")
    assert ecs.get_heuristic_max(ec_id).to_float(PowerUnit.KW) == 50


def test_parse_ec_optional_field_only_heur_sum_max(tmp_path):
    """Test parsing EC with only heur_sum_max optional field"""
    yaml_content = """ecs:
  - ec_id: E0
    unit: kWh
    heur_sum_max: 500 kWh
"""
    _write_yaml(tmp_path, "ecs.yaml", yaml_content)

    ecs, _ = ec_parser.parse(str(tmp_path))

    ec_id = EcId("E0")
    assert ecs.get_heuristic_sum_max(ec_id).to_float(PowerUnit.KW * TimeUnit.H) == 500
