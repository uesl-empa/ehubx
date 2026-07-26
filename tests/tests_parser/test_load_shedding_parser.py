"""
Tests for load_shedding_parser module
"""

from typing import List
from unittest.mock import patch

import pytest

from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId
from ehubx.data.load_shedding_data import LoadShedding
from ehubx.data.stage_data import StageId
from ehubx.data.time_data import TimeId
from ehubx.data.unit import CurrencyUnit, DimlessUnit, PowerUnit, TimeUnit
from ehubx.parser import exceptions, load_shedding_parser, yaml_parser


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


def test_parse_missing_node_returns_empty_load_shedding():
    """Test that parse returns empty LoadShedding when load_shedding node is None"""
    ecs = _create_test_ecs()
    root_node = None

    load_shedding = load_shedding_parser.parse(root_node, ecs)

    assert isinstance(load_shedding, LoadShedding)
    assert len(load_shedding.tuples) == 0


def test_parse_empty_yaml_returns_empty_load_shedding(tmp_path):
    """Test parsing empty YAML returns empty LoadShedding"""
    ecs = _create_test_ecs()
    _write_yaml(tmp_path, "load_shedding.yaml", "")

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))
    load_shedding = load_shedding_parser.parse(root_node, ecs)

    assert isinstance(load_shedding, LoadShedding)
    assert len(load_shedding.tuples) == 0


def test_parse_with_no_load_shedding_key_returns_empty(tmp_path):
    """Test parsing YAML without load_shedding key returns empty LoadShedding"""
    ecs = _create_test_ecs()
    yaml_content = """
some_other_key:
  - value
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))
    load_shedding = load_shedding_parser.parse(root_node, ecs)

    assert isinstance(load_shedding, LoadShedding)
    assert len(load_shedding.tuples) == 0


def test_parse_single_basic_load_shedding_entry(tmp_path):
    """Test parsing a single basic load shedding entry"""
    ecs = _create_test_ecs()

    yaml_content = """load_shedding:
  - stages: [S1]
    hubs: [H1]
    ec: E0
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))
    load_shedding = load_shedding_parser.parse(root_node, ecs)

    assert len(load_shedding.tuples) == 1
    assert (StageId("S1"), HubId("H1"), EcId("E0")) in load_shedding.tuples


def test_parse_multiple_stages_and_hubs(tmp_path):
    """Test parsing with multiple stages and hubs creates cartesian product"""
    ecs = _create_test_ecs()

    yaml_content = """load_shedding:
  - stages: [S1, S2]
    hubs: [H1, H2]
    ec: E0
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))
    load_shedding = load_shedding_parser.parse(root_node, ecs)

    # 2 stages * 2 hubs = 4 tuples
    assert len(load_shedding.tuples) == 4
    assert (StageId("S1"), HubId("H1"), EcId("E0")) in load_shedding.tuples
    assert (StageId("S1"), HubId("H2"), EcId("E0")) in load_shedding.tuples
    assert (StageId("S2"), HubId("H1"), EcId("E0")) in load_shedding.tuples
    assert (StageId("S2"), HubId("H2"), EcId("E0")) in load_shedding.tuples


def test_parse_multiple_load_shedding_entries(tmp_path):
    """Test parsing multiple load shedding entries"""
    ecs = _create_test_ecs()

    yaml_content = """load_shedding:
  - stages: [S1]
    hubs: [H1]
    ec: E0
  - stages: [S2]
    hubs: [H2]
    ec: E1
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))
    load_shedding = load_shedding_parser.parse(root_node, ecs)

    assert len(load_shedding.tuples) == 2
    assert (StageId("S1"), HubId("H1"), EcId("E0")) in load_shedding.tuples
    assert (StageId("S2"), HubId("H2"), EcId("E1")) in load_shedding.tuples


def test_parse_with_enabled_parameter(tmp_path):
    """Test parsing with enabled parameter"""
    ecs = _create_test_ecs()

    yaml_content = """load_shedding:
  - stages: [S1]
    hubs: [H1]
    ec: E0
    enabled: false
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))
    load_shedding = load_shedding_parser.parse(root_node, ecs)

    assert len(load_shedding.tuples) == 1
    assert not load_shedding.is_enabled(StageId("S1"), HubId("H1"), EcId("E0"))


def test_parse_with_enabled_true(tmp_path):
    """Test parsing with enabled=true"""
    ecs = _create_test_ecs()

    yaml_content = """load_shedding:
  - stages: [S1]
    hubs: [H1]
    ec: E0
    enabled: true
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))
    load_shedding = load_shedding_parser.parse(root_node, ecs)

    assert load_shedding.is_enabled(StageId("S1"), HubId("H1"), EcId("E0"))


def test_parse_with_max_abs_parameter(tmp_path):
    """Test parsing with max_abs parameter"""
    ecs = _create_test_ecs()

    yaml_content = """load_shedding:
  - stages: [S1]
    hubs: [H1]
    ec: E0
    max_abs: 100 kW
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))
    load_shedding = load_shedding_parser.parse(root_node, ecs)

    ts = load_shedding.get_max_abs(StageId("S1"), HubId("H1"), EcId("E0"))
    assert ts.def_value.to_float(PowerUnit.KW) == 100


def test_parse_with_max_rel_parameter(tmp_path):
    """Test parsing with max_rel parameter"""
    ecs = _create_test_ecs()

    yaml_content = """load_shedding:
  - stages: [S1]
    hubs: [H1]
    ec: E0
    max_rel: 0.5
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))
    load_shedding = load_shedding_parser.parse(root_node, ecs)

    ts = load_shedding.get_max_rel(StageId("S1"), HubId("H1"), EcId("E0"))
    assert ts.def_value.to_float(DimlessUnit()) == 0.5


def test_parse_with_energy_cost_parameter(tmp_path):
    """Test parsing with energy_cost parameter"""
    ecs = _create_test_ecs()

    yaml_content = """load_shedding:
  - stages: [S1]
    hubs: [H1]
    ec: E0
    energy_cost: 1000 CHF/kWh
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))
    load_shedding = load_shedding_parser.parse(root_node, ecs)

    ts = load_shedding.get_energy_cost(StageId("S1"), HubId("H1"), EcId("E0"))
    assert ts.def_value.to_float(CurrencyUnit.CHF / (PowerUnit.KW * TimeUnit.H)) == 1000


def test_parse_with_all_parameters(tmp_path):
    """Test parsing with all parameters specified"""
    ecs = _create_test_ecs()

    yaml_content = """load_shedding:
  - stages: [S1]
    hubs: [H1]
    ec: E0
    enabled: true
    max_abs: 100 kW
    max_rel: 0.75
    energy_cost: 500 CHF/kWh
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))
    load_shedding = load_shedding_parser.parse(root_node, ecs)

    s, h, e = StageId("S1"), HubId("H1"), EcId("E0")
    assert load_shedding.is_enabled(s, h, e)
    assert load_shedding.get_max_abs(s, h, e).def_value.to_float(PowerUnit.KW) == 100
    assert load_shedding.get_max_rel(s, h, e).def_value.to_float(DimlessUnit()) == 0.75
    assert (
        load_shedding.get_energy_cost(s, h, e).def_value.to_float(
            CurrencyUnit.CHF / (PowerUnit.KW * TimeUnit.H)
        )
        == 500
    )


def test_parse_with_profile_csv(tmp_path):
    """Test parsing with load shedding profile CSV"""
    ecs = _create_test_ecs()

    csv_lines = [
        "stage_id,S1,S1",
        "hub_id,H1,H1",
        "ec_id,E0,E0",
        "profile_key,max_abs,max_rel",
        "unit,kW,1",
        "1,10,0.5",
        "2,15,0.6",
    ]
    _write_csv(tmp_path, "profiles/load_shedding.csv", csv_lines)

    yaml_content = """load_shedding:
  - stages: [S1]
    hubs: [H1]
    ec: E0
    profile_path: profiles/load_shedding.csv
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))
    load_shedding = load_shedding_parser.parse(root_node, ecs)

    s, h, e = StageId("S1"), HubId("H1"), EcId("E0")
    assert len(load_shedding.tuples) == 1
    # Check that profile values are set
    ts = load_shedding.get_max_abs(s, h, e)
    assert ts.get_value(TimeId("1")).to_float(PowerUnit.KW) == 10
    ts_rel = load_shedding.get_max_rel(s, h, e)
    assert ts_rel.get_value(TimeId("1")).to_float(DimlessUnit()) == 0.5


def test_parse_with_profile_multiple_keys(tmp_path):
    """Test parsing profile with multiple keys (max_abs, max_rel, energy_cost)"""
    ecs = _create_test_ecs()

    csv_lines = [
        "stage_id,S1,S1,S1",
        "hub_id,H1,H1,H1",
        "ec_id,E0,E0,E0",
        "profile_key,max_abs,max_rel,energy_cost",
        "unit,kW,1,CHF/kWh",
        "1,50,0.5,1000",
        "2,75,0.8,1200",
    ]
    _write_csv(tmp_path, "profiles/load_shedding.csv", csv_lines)

    yaml_content = """load_shedding:
  - stages: [S1]
    hubs: [H1]
    ec: E0
    profile_path: profiles/load_shedding.csv
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))
    load_shedding = load_shedding_parser.parse(root_node, ecs)

    s, h, e = StageId("S1"), HubId("H1"), EcId("E0")

    # Check max_abs
    max_abs_ts = load_shedding.get_max_abs(s, h, e)
    assert max_abs_ts.get_value(TimeId("1")).to_float(PowerUnit.KW) == 50

    # Check max_rel
    max_rel_ts = load_shedding.get_max_rel(s, h, e)
    assert max_rel_ts.get_value(TimeId("1")).to_float(DimlessUnit()) == 0.5

    # Check energy_cost
    energy_cost_ts = load_shedding.get_energy_cost(s, h, e)
    assert (
        energy_cost_ts.get_value(TimeId("1")).to_float(
            CurrencyUnit.CHF / (PowerUnit.KW * TimeUnit.H)
        )
        == 1000
    )


# ============================================================================
# Exception tests - duplicate tuples
# ============================================================================


def test_parse_duplicate_tuples_raises_exception(tmp_path):
    """Test that duplicate (stage, hub, ec) tuples raise ParsingException"""
    ecs = _create_test_ecs()

    yaml_content = """load_shedding:
  - stages: [S1]
    hubs: [H1]
    ec: E0
  - stages: [S1]
    hubs: [H1]
    ec: E0
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))

    with pytest.raises(exceptions.ParsingException) as exc_info:
        load_shedding_parser.parse(root_node, ecs)

    error_msg = str(exc_info.value)
    assert "Overlap detected in load shedding module" in error_msg
    assert "(stage, hub, ec)" in error_msg


def test_parse_partial_overlap_tuples_raises_exception(tmp_path):
    """Test that partial overlaps in (stage, hub, ec) tuples raise exception"""
    ecs = _create_test_ecs()

    yaml_content = """load_shedding:
  - stages: [S1, S2]
    hubs: [H1]
    ec: E0
  - stages: [S1]
    hubs: [H1]
    ec: E0
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))

    with pytest.raises(exceptions.ParsingException) as exc_info:
        load_shedding_parser.parse(root_node, ecs)

    assert "Overlap detected in load shedding module" in str(exc_info.value)


def test_parse_different_ec_no_conflict(tmp_path):
    """Test that same (stage, hub) with different EC is allowed"""
    ecs = _create_test_ecs()

    yaml_content = """load_shedding:
  - stages: [S1]
    hubs: [H1]
    ec: E0
  - stages: [S1]
    hubs: [H1]
    ec: E1
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))
    load_shedding = load_shedding_parser.parse(root_node, ecs)

    assert len(load_shedding.tuples) == 2
    assert (StageId("S1"), HubId("H1"), EcId("E0")) in load_shedding.tuples
    assert (StageId("S1"), HubId("H1"), EcId("E1")) in load_shedding.tuples


# ============================================================================
# Exception tests - invalid units
# ============================================================================


def test_parse_invalid_max_abs_unit_raises_exception(tmp_path):
    """Test that invalid unit for max_abs raises exception"""
    ecs = _create_test_ecs()

    yaml_content = """load_shedding:
  - stages: [S1]
    hubs: [H1]
    ec: E0
    max_abs: 100 kWh
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))

    with pytest.raises(exceptions.ParsingException) as exc_info:
        load_shedding_parser.parse(root_node, ecs)

    assert "Unit mismatch" in str(exc_info.value)


def test_parse_invalid_max_rel_unit_raises_exception(tmp_path):
    """Test that invalid unit for max_rel raises exception"""
    ecs = _create_test_ecs()

    yaml_content = """load_shedding:
  - stages: [S1]
    hubs: [H1]
    ec: E0
    max_rel: 0.5 kW
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))

    with pytest.raises(exceptions.ParsingException) as exc_info:
        load_shedding_parser.parse(root_node, ecs)

    assert "Unit mismatch" in str(exc_info.value)


def test_parse_invalid_energy_cost_unit_raises_exception(tmp_path):
    """Test that invalid unit for energy_cost raises exception"""
    ecs = _create_test_ecs()

    yaml_content = """load_shedding:
  - stages: [S1]
    hubs: [H1]
    ec: E0
    energy_cost: 1000 kW
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))

    with pytest.raises(exceptions.ParsingException) as exc_info:
        load_shedding_parser.parse(root_node, ecs)

    assert "Unit mismatch" in str(exc_info.value)


# ============================================================================
# Exception tests - profile CSV issues
# ============================================================================


def test_parse_profile_invalid_unit_raises_exception(tmp_path):
    """Test that invalid unit in profile CSV raises exception"""
    ecs = _create_test_ecs()

    csv_lines = [
        "stage_id,S1",
        "hub_id,H1",
        "ec_id,E0",
        "profile_key,max_abs",
        "unit,kWh",  # Wrong unit - should be power/time
        "1,100",
    ]
    _write_csv(tmp_path, "profiles/load_shedding.csv", csv_lines)

    yaml_content = """load_shedding:
  - stages: [S1]
    hubs: [H1]
    ec: E0
    profile_path: profiles/load_shedding.csv
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))

    with pytest.raises(exceptions.ParsingException) as exc_info:
        load_shedding_parser.parse(root_node, ecs)

    error_msg = str(exc_info.value)
    assert "Invalid unit" in error_msg


def test_parse_profile_missing_file_raises_exception(tmp_path):
    """Test that missing profile file raises exception"""
    ecs = _create_test_ecs()

    yaml_content = """load_shedding:
  - stages: [S1]
    hubs: [H1]
    ec: E0
    profile_path: profiles/nonexistent.csv
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))

    with pytest.raises(exceptions.ParsingException):
        load_shedding_parser.parse(root_node, ecs)

def test_parse_profile_no_matching_tuple_ignores_profile(tmp_path):
    """Test that profile for non-matching (stage, hub, ec) tuple is ignored"""
    ecs = _create_test_ecs()

    csv_lines = [
        "stage_id,S2",
        "hub_id,H2",
        "ec_id,E0",
        "profile_key,max_abs",
        "unit,kW",
        "1,100",
    ]
    _write_csv(tmp_path, "profiles/load_shedding.csv", csv_lines)

    yaml_content = """load_shedding:
  - stages: [S1]
    hubs: [H1]
    ec: E0
    profile_path: profiles/load_shedding.csv
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    with patch("ehubx.data.load_shedding_data.LoadShedding.set_max_abs") as mock_set_max_abs:
        root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))
        load_shedding = load_shedding_parser.parse(root_node, ecs)

        # Should not raise, just not set any profile values
        s, h, e = StageId("S1"), HubId("H1"), EcId("E0")
        assert len(load_shedding.tuples) == 1
        mock_set_max_abs.assert_not_called()



def test_parse_profile_with_multiple_columns_same_tuple(tmp_path):
    """Test parsing profile with multiple data columns for different profile keys"""
    ecs = _create_test_ecs()

    csv_lines = [
        "stage_id,S1,S1,S1",
        "hub_id,H1,H1,H1",
        "ec_id,E0,E0,E0",
        "profile_key,max_abs,max_rel,energy_cost",
        "unit,kW,1,CHF/kWh",
        "1,50,0.5,500",
        "2,60,0.6,600",
    ]
    _write_csv(tmp_path, "profiles/load_shedding.csv", csv_lines)

    yaml_content = """load_shedding:
  - stages: [S1]
    hubs: [H1]
    ec: E0
    profile_path: profiles/load_shedding.csv
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))
    load_shedding = load_shedding_parser.parse(root_node, ecs)

    s, h, e = StageId("S1"), HubId("H1"), EcId("E0")
    ts = load_shedding.get_max_abs(s, h, e)
    # Check the values for both time steps
    assert ts.get_value(TimeId("1")).to_float(PowerUnit.KW) == 50
    assert ts.get_value(TimeId("2")).to_float(PowerUnit.KW) == 60


# ============================================================================
# Edge cases and comprehensive scenarios
# ============================================================================


def test_parse_with_e1_ec_unit(tmp_path):
    """Test parsing with E1 EC which has different unit (MW*h)"""
    ecs = _create_test_ecs()

    yaml_content = """load_shedding:
  - stages: [S1]
    hubs: [H1]
    ec: E1
    max_abs: 50 MW
    max_rel: 0.3
    energy_cost: 2000 CHF/MWh
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))
    load_shedding = load_shedding_parser.parse(root_node, ecs)

    s, h, e = StageId("S1"), HubId("H1"), EcId("E1")
    assert (
        load_shedding.get_max_abs(s, h, e).def_value.to_float(PowerUnit.MW) == 50
    )


def test_parse_large_number_of_tuples(tmp_path):
    """Test parsing with large cartesian product of stages and hubs"""
    ecs = _create_test_ecs()

    stages = ["S1", "S2", "S3", "S4"]
    hubs = ["H1", "H2", "H3", "H4", "H5"]

    yaml_content = f"""load_shedding:
  - stages: {stages}
    hubs: {hubs}
    ec: E0
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))
    load_shedding = load_shedding_parser.parse(root_node, ecs)

    # 4 stages * 5 hubs = 20 tuples
    assert len(load_shedding.tuples) == 20


def test_parse_default_enabled_is_true(tmp_path):
    """Test that when enabled is not specified, it defaults to True"""
    ecs = _create_test_ecs()

    yaml_content = """load_shedding:
  - stages: [S1]
    hubs: [H1]
    ec: E0
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))
    load_shedding = load_shedding_parser.parse(root_node, ecs)

    s, h, e = StageId("S1"), HubId("H1"), EcId("E0")
    assert load_shedding.is_enabled(s, h, e) is True


def test_parse_complex_scenario_with_mixed_parameters(tmp_path):
    """Test complex scenario with multiple entries and mixed parameters"""
    ecs = _create_test_ecs()

    csv_lines = [
        "stage_id,S2,S2",
        "hub_id,H2,H2",
        "ec_id,E0,E0",
        "profile_key,max_abs,max_rel",
        "unit,kW,1",
        "1,200,0.6",
        "2,250,0.7",
    ]
    _write_csv(tmp_path, "profiles/load_shedding.csv", csv_lines)

    yaml_content = """load_shedding:
  - stages: [S1]
    hubs: [H1]
    ec: E0
    enabled: false
    max_abs: 100 kW
  - stages: [S2]
    hubs: [H2]
    ec: E0
    enabled: true
    profile_path: profiles/load_shedding.csv
  - stages: [S1]
    hubs: [H1]
    ec: E1
    energy_cost: 5000 CHF/MWh
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))
    load_shedding = load_shedding_parser.parse(root_node, ecs)

    # Check total tuples
    assert len(load_shedding.tuples) == 3

    # Check S1-H1-E0
    s1h1e0 = (StageId("S1"), HubId("H1"), EcId("E0"))
    assert s1h1e0 in load_shedding.tuples
    assert not load_shedding.is_enabled(*s1h1e0)

    # Check S2-H2-E0
    s2h2e0 = (StageId("S2"), HubId("H2"), EcId("E0"))
    assert s2h2e0 in load_shedding.tuples
    assert load_shedding.is_enabled(*s2h2e0)
    assert load_shedding.get_max_abs(*s2h2e0).get_value(TimeId("1")).to_float(PowerUnit.KW) == 200

    # Check S1-H1-E1
    s1h1e1 = (StageId("S1"), HubId("H1"), EcId("E1"))
    assert s1h1e1 in load_shedding.tuples
    assert load_shedding.get_energy_cost(*s1h1e1).def_value.to_float(
        CurrencyUnit.CHF / (PowerUnit.MW * TimeUnit.H)
    ) == 5000


def test_parse_profile_with_string_key_not_recognized(tmp_path):
    """Test that unrecognized profile keys are silently ignored"""
    ecs = _create_test_ecs()

    csv_lines = [
        "stage_id,S1",
        "hub_id,H1",
        "ec_id,E0",
        "profile_key,unknown_key",
        "unit,1",
        "1,999",
    ]
    _write_csv(tmp_path, "profiles/load_shedding.csv", csv_lines)

    yaml_content = """load_shedding:
  - stages: [S1]
    hubs: [H1]
    ec: E0
    profile_path: profiles/load_shedding.csv
"""
    _write_yaml(tmp_path, "load_shedding.yaml", yaml_content)

    root_node = yaml_parser.parse(str(tmp_path / "load_shedding.yaml"))
    load_shedding = load_shedding_parser.parse(root_node, ecs)

    # Should not raise, unrecognized keys are ignored
    assert len(load_shedding.tuples) == 1
