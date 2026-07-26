"""
Tests for demand_parser module
"""

import os
from typing import List

import pytest

from ehubx.data.demand_data import Demands
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId
from ehubx.data.time_data import TimeId
from ehubx.data.unit import PowerUnit, TimeUnit
from ehubx.parser import demand_parser, exceptions, yaml_parser


def _write_yaml(tmp_path, name, content: str):
    """Helper to write YAML file"""
    path = tmp_path / name
    path.write_text(content)
    return path


def _write_csv(tmp_path, name, lines: List[str]):
    """Helper to write CSV file"""
    path = tmp_path / name
    # Ensure parent directories exist
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))
    return path


def _create_test_ecs():
    """Create Ecs object for testing"""
    ecs = Ecs()
    e0 = EcId("E0")
    e1 = EcId("E1")
    ecs.add_id(e0)
    ecs.add_id(e1)
    # Set units (kWh is energy unit)
    ecs.set_unit(e0, PowerUnit.KW * TimeUnit.H)
    ecs.set_unit(e1, PowerUnit.MW * TimeUnit.H)
    return ecs


# ============================================================================
# Tests for parse() function - main entry point
# ============================================================================


def test_parse_missing_file_returns_empty_demands(tmp_path):
    """Test that missing demands.yaml file returns empty Demands object and None"""
    ecs = _create_test_ecs()
    demands, root_node = demand_parser.parse(str(tmp_path), ecs)

    assert isinstance(demands, Demands)
    assert len(demands.tuples) == 0
    assert root_node is None


def test_parse_file_with_only_demand_profiles(tmp_path):
    """Test parsing file with demand profiles only"""
    ecs = _create_test_ecs()

    # Create demand profile CSV
    csv_lines = [
        "ec_id,E0,E0",
        "stage_id,S1,S1",
        "hub_id,H1,H2",
        "unit,kW,kW",
        "1,10,20",
        "2,15,25",
    ]
    csv_path = _write_csv(tmp_path, "profiles/demands.csv", csv_lines)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    # Create demands.yaml
    yaml_content = """demand_profiles:
    - profiles/demands.csv"""
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    demands, root_node = demand_parser.parse(str(tmp_path), ecs)

    assert root_node is not None
    assert len(demands.profile_tuples) == 2
    assert (StageId("S1"), HubId("H1"), EcId("E0")) in demands.profile_tuples
    assert (StageId("S1"), HubId("H2"), EcId("E0")) in demands.profile_tuples


def test_parse_file_with_only_demand_sums(tmp_path):
    """Test parsing file with demand sums only"""
    ecs = _create_test_ecs()

    yaml_content = """demand_sums:
  - stages: [S1]
    hubs: [H1, H2]
    ec: E0
    demand_sum: 30 kWh
  - stages: [S1, S2]
    hubs: [H3]
    ec: E1
    demand_sum: 50 MWh
"""
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    demands, root_node = demand_parser.parse(str(tmp_path), ecs)

    # 2 hubs for E0 (S1,H1), (S1,H2) and 2 stages for E1 with H3: total 4
    assert len(demands.sum_tuples) == 4
    assert (StageId("S1"), HubId("H1"), EcId("E0")) in demands.sum_tuples
    assert (StageId("S1"), HubId("H2"), EcId("E0")) in demands.sum_tuples
    assert (StageId("S1"), HubId("H3"), EcId("E1")) in demands.sum_tuples
    assert (StageId("S2"), HubId("H3"), EcId("E1")) in demands.sum_tuples


def test_parse_file_with_both_profiles_and_sums(tmp_path):
    """Test parsing file with both profiles and sums"""
    ecs = _create_test_ecs()

    # Create demand profile CSV
    csv_lines = [
        "ec_id,E0",
        "stage_id,S1",
        "hub_id,H1",
        "unit,kW",
        "1,10",
    ]
    csv_path = _write_csv(tmp_path, "profiles/demands.csv", csv_lines)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    yaml_content = """demand_profiles:
  - profiles/demands.csv
demand_sums:
  - stages: [S1]
    hubs: [H2]
    ec: E1
    demand_sum: 50 MWh
"""
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    demands, root_node = demand_parser.parse(str(tmp_path), ecs)

    assert len(demands.profile_tuples) == 1
    assert len(demands.sum_tuples) == 1
    assert (StageId("S1"), HubId("H1"), EcId("E0")) in demands.profile_tuples
    assert (StageId("S1"), HubId("H2"), EcId("E1")) in demands.sum_tuples


def test_parse_empty_yaml_file(tmp_path):
    """Test parsing empty YAML file"""
    ecs = _create_test_ecs()
    _write_yaml(tmp_path, "demands.yaml", "")

    demands, root_node = demand_parser.parse(str(tmp_path), ecs)

    # Empty file returns None from yaml_parser.parse, so we get empty demands
    assert isinstance(demands, Demands)
    assert len(demands.tuples) == 0


# ============================================================================
# Tests for _parse_demand_profiles() function
# ============================================================================


def test_parse_demand_profiles_with_none_node(tmp_path):
    """Test that None demand_profiles_node is handled gracefully"""
    ecs = _create_test_ecs()
    demands = Demands()

    # Should not raise, just return
    demand_parser._parse_demand_profiles(None, ecs, demands)

    assert len(demands.profile_tuples) == 0


def test_parse_demand_profiles_multiple_files(tmp_path):
    """Test parsing multiple demand profile files"""
    ecs = _create_test_ecs()

    # Create first demand profile CSV
    csv_lines1 = [
        "ec_id,E0",
        "stage_id,S1",
        "hub_id,H1",
        "unit,kW",
        "1,10",
        "2,20",
    ]
    _write_csv(tmp_path, "profiles/demands1.csv", csv_lines1)

    # Create second demand profile CSV
    csv_lines2 = [
        "ec_id,E0",
        "stage_id,S1",
        "hub_id,H1",
        "unit,kW",
        "1,5",
        "2,10",
    ]
    _write_csv(tmp_path, "profiles/demands2.csv", csv_lines2)

    yaml_content = """demand_profiles:
  - profiles/demands1.csv
  - profiles/demands2.csv
"""
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    demands, _ = demand_parser.parse(str(tmp_path), ecs)

    # Current implementation overwrites earlier profile values with later files
    assert len(demands.profile_tuples) == 1
    profile = demands.get_demand_profile(StageId("S1"), HubId("H1"), EcId("E0"))
    # Expect value from second file: 5 at t=1
    val_at_t1 = profile.get_value(TimeId("1"))
    assert val_at_t1.to_float(PowerUnit.KW) == 15


def test_parse_demand_profiles_invalid_unit_raises_exception(tmp_path):
    """Test that invalid unit in demand profile raises exception"""
    ecs = _create_test_ecs()

    # Create demand profile with wrong unit (should be power/time, e.g., kW not kWh)
    csv_lines = [
        "ec_id,E0",
        "stage_id,S1",
        "hub_id,H1",
        "unit,kWh",  # Wrong unit - should be kW (or similar power)
        "1,10",
    ]
    csv_path = _write_csv(tmp_path, "profiles/demands.csv", csv_lines)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    yaml_content = """demand_profiles:
  - profiles/demands.csv
"""
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    with pytest.raises(exceptions.ParsingException) as exc_info:
        demand_parser.parse(str(tmp_path), ecs)

    assert "Invalid unit" in str(exc_info.value)
    assert "Expected a unit like" in str(exc_info.value)


def test_parse_demand_profiles_empty_list(tmp_path):
    """Test parsing with empty demand_profiles list"""
    ecs = _create_test_ecs()

    yaml_content = """demand_profiles: []
"""
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    demands, _ = demand_parser.parse(str(tmp_path), ecs)

    assert len(demands.profile_tuples) == 0


# ============================================================================
# Tests for _parse_demand_profile() function
# ============================================================================


def test_parse_demand_profile_missing_file_raises_exception(tmp_path):
    """Test that missing profile file raises MissingFileException"""
    ecs = _create_test_ecs()

    yaml_content = """demand_profiles:
  - nonexistent.csv
"""
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    with pytest.raises(exceptions.MissingFileException):
        demand_parser.parse(str(tmp_path), ecs)


# ============================================================================
# Tests for _parse_demand_sums() function
# ============================================================================


def test_parse_demand_sums_with_none_node(tmp_path):
    """Test that None demand_sums_node is handled gracefully"""
    ecs = _create_test_ecs()
    demands = Demands()

    # Should not raise, just return
    demand_parser._parse_demand_sums(None, ecs, demands)

    assert len(demands.sum_tuples) == 0


def test_parse_demand_sums_single_stage_single_hub(tmp_path):
    """Test parsing single demand sum with one stage and hub"""
    ecs = _create_test_ecs()

    yaml_content = """demand_sums:
  - stages: [S1]
    hubs: [H1]
    ec: E0
    demand_sum: 30 kWh
"""
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    demands, _ = demand_parser.parse(str(tmp_path), ecs)

    assert len(demands.sum_tuples) == 1
    assert (StageId("S1"), HubId("H1"), EcId("E0")) in demands.sum_tuples


def test_parse_demand_sums_multiple_stages_and_hubs(tmp_path):
    """Test parsing demand sum with multiple stages and hubs"""
    ecs = _create_test_ecs()

    yaml_content = """demand_sums:
  - stages: [S1, S2, S3]
    hubs: [H1, H2]
    ec: E0
    demand_sum: 50 kWh
"""
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    demands, _ = demand_parser.parse(str(tmp_path), ecs)

    # Should have 3 stages * 2 hubs = 6 tuples
    assert len(demands.sum_tuples) == 6
    assert (StageId("S1"), HubId("H1"), EcId("E0")) in demands.sum_tuples
    assert (StageId("S2"), HubId("H2"), EcId("E0")) in demands.sum_tuples
    assert (StageId("S3"), HubId("H1"), EcId("E0")) in demands.sum_tuples


def test_parse_demand_sums_multiple_entries(tmp_path):
    """Test parsing multiple demand sum entries"""
    ecs = _create_test_ecs()

    yaml_content = """demand_sums:
  - stages: [S1]
    hubs: [H1]
    ec: E0
    demand_sum: 30 kWh
  - stages: [S2]
    hubs: [H2]
    ec: E1
    demand_sum: 50 MWh
  - stages: [S3]
    hubs: [H3, H4]
    ec: E0
    demand_sum: 100 kWh
"""
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    demands, _ = demand_parser.parse(str(tmp_path), ecs)

    assert len(demands.sum_tuples) == 4
    assert (StageId("S1"), HubId("H1"), EcId("E0")) in demands.sum_tuples
    assert (StageId("S2"), HubId("H2"), EcId("E1")) in demands.sum_tuples
    assert (StageId("S3"), HubId("H3"), EcId("E0")) in demands.sum_tuples
    assert (StageId("S3"), HubId("H4"), EcId("E0")) in demands.sum_tuples


def test_parse_demand_sums_detects_duplicate_tuples(tmp_path):
    """Test that duplicate (stage, hub, ec) tuples raise exception"""
    ecs = _create_test_ecs()

    yaml_content = """demand_sums:
  - stages: [S1]
    hubs: [H1]
    ec: E0
    demand_sum: 30 kWh
  - stages: [S1]
    hubs: [H1]
    ec: E0
    demand_sum: 50 kWh
"""
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    with pytest.raises(exceptions.ParsingException) as exc_info:
        demand_parser.parse(str(tmp_path), ecs)

    assert "Overlap detected" in str(exc_info.value)
    assert "demand module" in str(exc_info.value)


def test_parse_demand_sums_empty_list(tmp_path):
    """Test parsing with empty demand_sums list"""
    ecs = _create_test_ecs()

    yaml_content = """demand_sums: []
"""
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    demands, _ = demand_parser.parse(str(tmp_path), ecs)

    assert len(demands.sum_tuples) == 0


# ============================================================================
# Tests for _parse_demand_sum() function
# ============================================================================


def test_parse_demand_sum_sets_correct_value(tmp_path):
    """Test that demand_sum value is correctly stored"""
    ecs = _create_test_ecs()

    yaml_content = """demand_sums:
  - stages: [S1]
    hubs: [H1]
    ec: E0
    demand_sum: 42 kWh
"""
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    demands, _ = demand_parser.parse(str(tmp_path), ecs)

    # Get the demand sum for the tuple
    sum_val = demands.get_demand_sum(StageId("S1"), HubId("H1"), EcId("E0"))
    assert sum_val.to_float(PowerUnit.KW * TimeUnit.H) == 42


def test_parse_demand_sum_with_different_units(tmp_path):
    """Test demand sums with different units"""
    ecs = _create_test_ecs()

    yaml_content = """demand_sums:
  - stages: [S1]
    hubs: [H1]
    ec: E0
    demand_sum: 100 kWh
  - stages: [S1]
    hubs: [H2]
    ec: E1
    demand_sum: 200 MWh
"""
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    demands, _ = demand_parser.parse(str(tmp_path), ecs)

    sum1 = demands.get_demand_sum(StageId("S1"), HubId("H1"), EcId("E0"))
    sum2 = demands.get_demand_sum(StageId("S1"), HubId("H2"), EcId("E1"))

    assert sum1.to_float(PowerUnit.KW * TimeUnit.H) == 100
    assert sum2.to_float(PowerUnit.MW * TimeUnit.H) == 200


# ============================================================================
# Tests for error handling and edge cases
# ============================================================================


def test_parse_demand_profiles_with_multiple_stages_hubs_ecs(tmp_path):
    """Test parsing profiles with complex stage/hub/ec combinations"""
    ecs = _create_test_ecs()

    csv_lines = [
        "ec_id,E0,E0,E1,E1",
        "stage_id,S1,S2,S1,S2",
        "hub_id,H1,H2,H1,H2",
        "unit,kW,kW,MW,MW",
        "1,10,20,30,40",
        "2,15,25,35,45",
    ]
    csv_path = _write_csv(tmp_path, "profiles/demands.csv", csv_lines)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    yaml_content = """demand_profiles:
  - profiles/demands.csv
"""
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    demands, _ = demand_parser.parse(str(tmp_path), ecs)

    assert len(demands.profile_tuples) == 4
    assert (StageId("S1"), HubId("H1"), EcId("E0")) in demands.profile_tuples
    assert (StageId("S2"), HubId("H2"), EcId("E1")) in demands.profile_tuples


def test_parse_demand_profiles_mixed_unit_error(tmp_path):
    """Test that mixed incompatible units in single profile cause error"""
    ecs = _create_test_ecs()

    # E0 is in kWh but we're providing kWh/h which doesn't match kW (power)
    csv_lines = [
        "ec_id,E0",
        "stage_id,S1",
        "hub_id,H1",
        "unit,MJ/h",  # Energy/time, but wrong energy unit
        "1,10",
    ]
    csv_path = _write_csv(tmp_path, "profiles/demands.csv", csv_lines)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    yaml_content = """demand_profiles:
  - profiles/demands.csv
"""
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    with pytest.raises(exceptions.ParsingException) as exc_info:
        demand_parser.parse(str(tmp_path), ecs)

    assert "Invalid unit" in str(exc_info.value)


def test_parse_with_invalid_yaml_structure(tmp_path):
    """Test parsing with invalid YAML structure (wrong dict type)"""
    ecs = _create_test_ecs()

    # Create a valid YAML but with list instead of dict at root
    yaml_content = "- item1\n- item2"
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    # This should raise because root should be a dict
    with pytest.raises(exceptions.InvalidNodeTypeException):
        demand_parser.parse(str(tmp_path), ecs)


def test_parse_demand_sum_single_stage_string(tmp_path):
    """Test that single stage as string (not list) works"""
    ecs = _create_test_ecs()

    yaml_content = """demand_sums:
  - stages: S1
    hubs: [H1]
    ec: E0
    demand_sum: 30 kWh
"""
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    # Should work - yaml_parser handles conversion
    demands, _ = demand_parser.parse(str(tmp_path), ecs)

    assert len(demands.sum_tuples) == 1


def test_parse_profile_tuples_property(tmp_path):
    """Test that profile_tuples property returns correct set"""
    ecs = _create_test_ecs()

    csv_lines = [
        "ec_id,E0,E0",
        "stage_id,S1,S2",
        "hub_id,H1,H2",
        "unit,kW,kW",
        "1,10,20",
    ]
    csv_path = _write_csv(tmp_path, "profiles/demands.csv", csv_lines)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    yaml_content = """demand_profiles:
  - profiles/demands.csv
"""
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    demands, _ = demand_parser.parse(str(tmp_path), ecs)

    # Verify the property
    profile_tuples = demands.profile_tuples
    assert len(profile_tuples) == 2
    assert isinstance(profile_tuples, set)


def test_parse_sum_tuples_property(tmp_path):
    """Test that sum_tuples property returns correct set"""
    ecs = _create_test_ecs()

    yaml_content = """demand_sums:
  - stages: [S1, S2]
    hubs: [H1]
    ec: E0
    demand_sum: 30 kWh
"""
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    demands, _ = demand_parser.parse(str(tmp_path), ecs)

    # Verify the property
    sum_tuples = demands.sum_tuples
    assert len(sum_tuples) == 2
    assert isinstance(sum_tuples, set)


def test_parse_tuples_property_combines_both(tmp_path):
    """Test that tuples property combines profile and sum tuples"""
    ecs = _create_test_ecs()

    csv_lines = [
        "ec_id,E0",
        "stage_id,S1",
        "hub_id,H1",
        "unit,kW",
        "1,10",
    ]
    csv_path = _write_csv(tmp_path, "profiles/demands.csv", csv_lines)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    yaml_content = """demand_profiles:
  - profiles/demands.csv
demand_sums:
  - stages: [S2]
    hubs: [H2]
    ec: E0
    demand_sum: 30 kWh
"""
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    demands, _ = demand_parser.parse(str(tmp_path), ecs)

    # Verify the combined property
    tuples = demands.tuples
    assert len(tuples) == 2
    assert (StageId("S1"), HubId("H1"), EcId("E0")) in tuples
    assert (StageId("S2"), HubId("H2"), EcId("E0")) in tuples


def test_parse_demand_sums_preserves_order_for_duplicate_check(tmp_path):
    """Test that demand sums with overlapping ranges are detected"""
    ecs = _create_test_ecs()

    yaml_content = """demand_sums:
  - stages: [S1, S2]
    hubs: [H1]
    ec: E0
    demand_sum: 30 kWh
  - stages: [S1]
    hubs: [H1, H2]
    ec: E0
    demand_sum: 50 kWh
"""
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    with pytest.raises(exceptions.ParsingException) as exc_info:
        demand_parser.parse(str(tmp_path), ecs)

    assert "Overlap detected" in str(exc_info.value)


def test_parse_returns_root_node(tmp_path):
    """Test that parse returns the root YAML node"""
    ecs = _create_test_ecs()

    yaml_content = """demand_sums:
  - stages: [S1]
    hubs: [H1]
    ec: E0
    demand_sum: 30 kWh
"""
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    demands, root_node = demand_parser.parse(str(tmp_path), ecs)

    assert root_node is not None
    assert root_node.node_kind == yaml_parser.YamlNodeKind.DICT


def test_parse_demand_profile_with_relative_path(tmp_path):
    """Test that relative paths in demand_profiles are resolved correctly"""
    ecs = _create_test_ecs()

    # Create demands.yaml in subdirectory
    subdir = tmp_path / "basic"
    subdir.mkdir()

    csv_lines = [
        "ec_id,E0",
        "stage_id,S1",
        "hub_id,H1",
        "unit,kW",
        "1,10",
    ]
    csv_path = _write_csv(subdir, "profiles/demands.csv", csv_lines)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    yaml_content = """demand_profiles:
  - profiles/demands.csv
"""
    _write_yaml(subdir, "demands.yaml", yaml_content)

    demands, _ = demand_parser.parse(str(subdir), ecs)

    assert len(demands.profile_tuples) == 1


# ============================================================================
# Tests for data consistency and validation
# ============================================================================


def test_parse_demand_profile_time_series_access(tmp_path):
    """Test accessing demand profile values from time series"""
    ecs = _create_test_ecs()

    csv_lines = [
        "ec_id,E0",
        "stage_id,S1",
        "hub_id,H1",
        "unit,kW",
        "1,10",
        "2,20",
        "3,30",
    ]
    csv_path = _write_csv(tmp_path, "profiles/demands.csv", csv_lines)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    yaml_content = """demand_profiles:
  - profiles/demands.csv
"""
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    demands, _ = demand_parser.parse(str(tmp_path), ecs)

    profile = demands.get_demand_profile(StageId("S1"), HubId("H1"), EcId("E0"))

    # Access values at different times
    assert profile.get_value(TimeId("1")).to_float(PowerUnit.KW) == 10
    assert profile.get_value(TimeId("2")).to_float(PowerUnit.KW) == 20
    assert profile.get_value(TimeId("3")).to_float(PowerUnit.KW) == 30


def test_parse_demand_sum_access(tmp_path):
    """Test accessing demand sum values"""
    ecs = _create_test_ecs()

    yaml_content = """demand_sums:
  - stages: [S1, S2]
    hubs: [H1, H2]
    ec: E0
    demand_sum: 123 kWh
"""
    _write_yaml(tmp_path, "demands.yaml", yaml_content)

    demands, _ = demand_parser.parse(str(tmp_path), ecs)

    # All tuples should have the same demand_sum value
    for stage_str in ["S1", "S2"]:
        for hub_str in ["H1", "H2"]:
            sum_val = demands.get_demand_sum(
                StageId(stage_str), HubId(hub_str), EcId("E0")
            )
            assert sum_val.to_float(PowerUnit.KW * TimeUnit.H) == 123
