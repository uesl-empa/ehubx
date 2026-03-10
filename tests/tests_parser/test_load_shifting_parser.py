"""
Tests for load_shifting_parser module
"""

from typing import List
from unittest.mock import patch

import pytest

from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId
from ehubx.data.load_shifting_data import LoadShiftId, LoadShifting
from ehubx.data.stage_data import StageId
from ehubx.data.time_data import TimeId
from ehubx.data.unit import CurrencyUnit, DimlessUnit, PowerUnit, TimeUnit
from ehubx.parser import exceptions, load_shifting_parser, yaml_parser


def _write_yaml(tmp_path, name, content: str):
    """Helper to write YAML file"""
    path = tmp_path / name
    path.write_text(content)
    return path


def _write_csv(tmp_path, name, lines: List[str]):
    """Helper to write CSV file"""
    path = tmp_path / name
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
    ecs.set_unit(e0, PowerUnit.KW * TimeUnit.H)
    ecs.set_unit(e1, PowerUnit.MW * TimeUnit.H)
    return ecs


def _parse_load_shifting(tmp_path, yaml_content: str):
    """Helper to write YAML and parse load shifting"""
    _write_yaml(tmp_path, "load_shifting.yaml", yaml_content)
    root_node = yaml_parser.parse(str(tmp_path / "load_shifting.yaml"))
    return load_shifting_parser.parse(root_node, _create_test_ecs())


# ============================================================================
# Tests for parse() function - main entry point
# ============================================================================


def test_parse_missing_node_returns_empty_load_shifting():
    """Test that parse returns empty LoadShifting when root node is None"""
    ecs = _create_test_ecs()
    root_node = None

    load_shifting = load_shifting_parser.parse(root_node, ecs)

    assert isinstance(load_shifting, LoadShifting)
    assert len(load_shifting.ids) == 0


def test_parse_empty_yaml_returns_empty_load_shifting(tmp_path):
    """Test parsing empty YAML returns empty LoadShifting"""
    load_shifting = _parse_load_shifting(tmp_path, "")
    assert isinstance(load_shifting, LoadShifting)
    assert len(load_shifting.ids) == 0


def test_parse_with_no_load_shifting_key_returns_empty(tmp_path):
    """Test parsing YAML without load_shifting key returns empty LoadShifting"""
    load_shifting = _parse_load_shifting(tmp_path, "some_other_key:\n  - value")
    assert isinstance(load_shifting, LoadShifting)
    assert len(load_shifting.ids) == 0


def test_parse_single_basic_load_shifting_entry(tmp_path):
    """Test parsing a single basic load shifting entry with required fields only"""
    yaml_content = """load_shifting:
  - load_shift_id: LS1
    stages: [S1]
    hubs: [H1]
    ec: E0
    interval_length: 4 h
"""
    load_shifting = _parse_load_shifting(tmp_path, yaml_content)

    assert len(load_shifting.ids) == 1
    assert LoadShiftId("LS1") in load_shifting.ids
    assert (StageId("S1"), HubId("H1")) in load_shifting.get_stage_hub_tuples(LoadShiftId("LS1"))
    assert load_shifting.get_interval_length(LoadShiftId("LS1")).to_float(TimeUnit.H) == 4


def test_parse_multiple_stages_and_hubs(tmp_path):
    """Test parsing with multiple stages and hubs creates cartesian product"""
    yaml_content = """load_shifting:
  - load_shift_id: LS1
    stages: [S1, S2]
    hubs: [H1, H2]
    ec: E0
    interval_length: 2 h
"""
    load_shifting = _parse_load_shifting(tmp_path, yaml_content)
    stage_hub_tuples = load_shifting.get_stage_hub_tuples(LoadShiftId("LS1"))

    assert len(stage_hub_tuples) == 4
    assert (StageId("S1"), HubId("H1")) in stage_hub_tuples
    assert (StageId("S1"), HubId("H2")) in stage_hub_tuples
    assert (StageId("S2"), HubId("H1")) in stage_hub_tuples
    assert (StageId("S2"), HubId("H2")) in stage_hub_tuples


def test_parse_multiple_load_shifting_entries(tmp_path):
    """Test parsing multiple load shifting entries"""
    yaml_content = """load_shifting:
  - load_shift_id: LS1
    stages: [S1]
    hubs: [H1]
    ec: E0
    interval_length: 3 h
  - load_shift_id: LS2
    stages: [S2]
    hubs: [H2]
    ec: E1
    interval_length: 6 h
"""
    load_shifting = _parse_load_shifting(tmp_path, yaml_content)

    assert len(load_shifting.ids) == 2
    assert LoadShiftId("LS1") in load_shifting.ids
    assert LoadShiftId("LS2") in load_shifting.ids


# ============================================================================
# Tests for optional parameters
# ============================================================================


@pytest.mark.parametrize("param_name,param_value,getter_method,unit,expected", [
    ("max_above_abs", "50 kW", "get_max_above_abs", PowerUnit.KW, 50),
    ("max_below_abs", "30 kW", "get_max_below_abs", PowerUnit.KW, 30),
    ("max_above_rel", "0.5", "get_max_above_rel", DimlessUnit(), 0.5),
    ("max_below_rel", "0.3", "get_max_below_rel", DimlessUnit(), 0.3),
    ("capex_per_cap", "100 CHF/kWh", "get_capex_per_cap", CurrencyUnit.CHF / (PowerUnit.KW * TimeUnit.H), 100),
    ("cap_min", "10 kWh", "get_cap_min", PowerUnit.KW * TimeUnit.H, 10),
    ("cap_max", "500 kWh", "get_cap_max", PowerUnit.KW * TimeUnit.H, 500),
    ("cap_init", "50 kWh", "get_cap_init", PowerUnit.KW * TimeUnit.H, 50),
    ("energy_cost_above", "200 CHF/kWh", "get_energy_cost_above", CurrencyUnit.CHF / (PowerUnit.KW * TimeUnit.H), 200),
    ("energy_cost_below", "150 CHF/kWh", "get_energy_cost_below", CurrencyUnit.CHF / (PowerUnit.KW * TimeUnit.H), 150),
    ("peak_cost_above", "1000 CHF/kW", "get_peak_cost_above", CurrencyUnit.CHF / PowerUnit.KW, 1000),
    ("peak_cost_below", "800 CHF/kW", "get_peak_cost_below", CurrencyUnit.CHF / PowerUnit.KW, 800),
    ("fix_cost", "50 CHF/h", "get_fix_cost", CurrencyUnit.CHF / TimeUnit.H, 50),
])
def test_parse_optional_parameters(tmp_path, param_name, param_value, getter_method, unit, expected):
    """Test parsing various optional parameters"""
    yaml_content = f"""load_shifting:
  - load_shift_id: LS1
    stages: [S1]
    hubs: [H1]
    ec: E0
    interval_length: 1 h
    {param_name}: {param_value}
"""
    load_shifting = _parse_load_shifting(tmp_path, yaml_content)
    result = getattr(load_shifting, getter_method)(LoadShiftId("LS1"))

    # Handle both Value and TimeSeries return types
    value_to_check = result.def_value if hasattr(result, 'def_value') else result
    assert value_to_check.to_float(unit) == expected


def test_parse_with_all_optional_parameters(tmp_path):
    """Test parsing with all optional parameters specified"""
    yaml_content = """load_shifting:
  - load_shift_id: LS1
    stages: [S1]
    hubs: [H1]
    ec: E0
    interval_length: 2 h
    max_above_abs: 100 kW
    max_below_abs: 80 kW
    max_above_rel: 0.6
    max_below_rel: 0.4
    capex_per_cap: 200 CHF/kWh
    cap_min: 20 kWh
    cap_max: 600 kWh
    cap_init: 100 kWh
    energy_cost_above: 300 CHF/kWh
    energy_cost_below: 250 CHF/kWh
    peak_cost_above: 2000 CHF/kW
    peak_cost_below: 1500 CHF/kW
    fix_cost: 100 CHF/h
"""
    load_shifting = _parse_load_shifting(tmp_path, yaml_content)
    ls_id = LoadShiftId("LS1")

    assert load_shifting.get_interval_length(ls_id).to_float(TimeUnit.H) == 2
    assert load_shifting.get_max_above_abs(ls_id).def_value.to_float(PowerUnit.KW) == 100
    assert load_shifting.get_max_below_abs(ls_id).def_value.to_float(PowerUnit.KW) == 80
    assert load_shifting.get_max_above_rel(ls_id).def_value.to_float(DimlessUnit()) == 0.6
    assert load_shifting.get_max_below_rel(ls_id).def_value.to_float(DimlessUnit()) == 0.4
    assert load_shifting.get_capex_per_cap(ls_id).to_float(CurrencyUnit.CHF / (PowerUnit.KW * TimeUnit.H)) == 200
    assert load_shifting.get_cap_min(ls_id).to_float(PowerUnit.KW * TimeUnit.H) == 20
    assert load_shifting.get_cap_max(ls_id).to_float(PowerUnit.KW * TimeUnit.H) == 600
    assert load_shifting.get_cap_init(ls_id).to_float(PowerUnit.KW * TimeUnit.H) == 100


# ============================================================================
# Tests for profile parsing
# ============================================================================


@pytest.mark.parametrize("profile_key,unit_str,values,getter_method,unit", [
    ("max_above_abs", "kW", [100, 150], "get_max_above_abs", PowerUnit.KW),
    ("max_below_abs", "kW", [50, 60], "get_max_below_abs", PowerUnit.KW),
    ("max_above_rel", "1", [0.7, 0.8], "get_max_above_rel", DimlessUnit()),
    ("max_below_rel", "1", [0.3, 0.4], "get_max_below_rel", DimlessUnit()),
    ("energy_cost_above", "CHF/kWh", [100, 120], "get_energy_cost_above", CurrencyUnit.CHF / (PowerUnit.KW * TimeUnit.H)),
    ("energy_cost_below", "CHF/kWh", [80, 90], "get_energy_cost_below", CurrencyUnit.CHF / (PowerUnit.KW * TimeUnit.H)),
    ("fix_cost", "CHF/h", [40, 45], "get_fix_cost", CurrencyUnit.CHF / TimeUnit.H),
])
def test_parse_with_profile(tmp_path, profile_key, unit_str, values, getter_method, unit):
    """Test parsing time-dependent profiles"""
    csv_lines = [
        "loadshift_id,LS1",
        f"profile_key,{profile_key}",
        f"unit,{unit_str}",
        f"1,{values[0]}",
        f"2,{values[1]}",
    ]
    _write_csv(tmp_path, "profiles/load_shifting.csv", csv_lines)

    yaml_content = """load_shifting:
  - load_shift_id: LS1
    stages: [S1]
    hubs: [H1]
    ec: E0
    interval_length: 1 h
    profile_path: profiles/load_shifting.csv
"""
    load_shifting = _parse_load_shifting(tmp_path, yaml_content)
    result = getattr(load_shifting, getter_method)(LoadShiftId("LS1"))

    assert result.get_value(TimeId("1")).to_float(unit) == values[0]
    assert result.get_value(TimeId("2")).to_float(unit) == values[1]


def test_parse_with_profile_multiple_keys(tmp_path):
    """Test parsing with multiple profile keys in single CSV"""
    csv_lines = [
        "loadshift_id,LS1,LS1,LS1",
        "profile_key,max_above_abs,max_below_abs,max_above_rel",
        "unit,kW,kW,1",
        "1,100,50,0.6",
        "2,120,60,0.7",
    ]
    _write_csv(tmp_path, "profiles/load_shifting.csv", csv_lines)

    yaml_content = """load_shifting:
  - load_shift_id: LS1
    stages: [S1]
    hubs: [H1]
    ec: E0
    interval_length: 1 h
    profile_path: profiles/load_shifting.csv
"""
    load_shifting = _parse_load_shifting(tmp_path, yaml_content)
    ls_id = LoadShiftId("LS1")

    assert load_shifting.get_max_above_abs(ls_id).get_value(TimeId("1")).to_float(PowerUnit.KW) == 100
    assert load_shifting.get_max_above_abs(ls_id).get_value(TimeId("2")).to_float(PowerUnit.KW) == 120
    assert load_shifting.get_max_below_abs(ls_id).get_value(TimeId("1")).to_float(PowerUnit.KW) == 50
    assert load_shifting.get_max_below_abs(ls_id).get_value(TimeId("2")).to_float(PowerUnit.KW) == 60
    assert load_shifting.get_max_above_rel(ls_id).get_value(TimeId("1")).to_float(DimlessUnit()) == 0.6
    assert load_shifting.get_max_above_rel(ls_id).get_value(TimeId("2")).to_float(DimlessUnit()) == 0.7


def test_parse_profile_ignores_other_load_shift_ids(tmp_path):
    """Test that profile parsing only reads data for the correct load_shift_id"""
    csv_lines = [
        "loadshift_id,LS1,LS2",
        "profile_key,max_above_abs,max_above_abs",
        "unit,kW,kW",
        "1,100,999",
        "2,150,888",
    ]
    _write_csv(tmp_path, "profiles/load_shifting.csv", csv_lines)

    yaml_content = """load_shifting:
  - load_shift_id: LS1
    stages: [S1]
    hubs: [H1]
    ec: E0
    interval_length: 1 h
    profile_path: profiles/load_shifting.csv
"""
    load_shifting = _parse_load_shifting(tmp_path, yaml_content)
    max_above = load_shifting.get_max_above_abs(LoadShiftId("LS1"))

    # Should only read LS1 column values
    assert max_above.get_value(TimeId("1")).to_float(PowerUnit.KW) == 100
    assert max_above.get_value(TimeId("2")).to_float(PowerUnit.KW) == 150


# ============================================================================
# Tests for different energy carrier units
# ============================================================================


def test_parse_with_e1_ec_unit(tmp_path):
    """Test parsing with E1 EC which has different unit (MW*h)"""
    yaml_content = """load_shifting:
  - load_shift_id: LS1
    stages: [S1]
    hubs: [H1]
    ec: E1
    interval_length: 3 h
    max_above_abs: 25 MW
    capex_per_cap: 50 CHF/MWh
"""
    load_shifting = _parse_load_shifting(tmp_path, yaml_content)
    ls_id = LoadShiftId("LS1")

    assert load_shifting.get_max_above_abs(ls_id).def_value.to_float(PowerUnit.MW) == 25
    assert load_shifting.get_capex_per_cap(ls_id).to_float(CurrencyUnit.CHF / (PowerUnit.MW * TimeUnit.H)) == 50


# ============================================================================
# Tests for exception cases
# ============================================================================


def test_parse_profile_with_missing_file(tmp_path):
    """Test that referencing non-existent profile file raises exception"""
    yaml_content = """load_shifting:
  - load_shift_id: LS1
    stages: [S1]
    hubs: [H1]
    ec: E0
    interval_length: 1 h
    profile_path: profiles/nonexistent.csv
"""
    _write_yaml(tmp_path, "load_shifting.yaml", yaml_content)
    root_node = yaml_parser.parse(str(tmp_path / "load_shifting.yaml"))

    with pytest.raises(exceptions.MissingFileException):
        load_shifting_parser.parse(root_node, _create_test_ecs())


@pytest.mark.parametrize("profile_key,invalid_unit,expected_msg", [
    ("max_above_abs", "CHF", "max_above_abs"),
    ("max_below_abs", "1", "max_below_abs"),
    ("max_above_rel", "kW", "max_above_rel"),
    ("max_below_rel", "CHF", "max_below_rel"),
    ("energy_cost_above", "kW", "energy_cost_above"),
    ("energy_cost_below", "1", "energy_cost_below"),
    ("fix_cost", "kW", "fix_cost"),
])
def test_parse_profile_with_invalid_units(tmp_path, profile_key, invalid_unit, expected_msg):
    """Test that profiles with invalid units raise ParsingException"""
    csv_lines = [
        "loadshift_id,LS1",
        f"profile_key,{profile_key}",
        f"unit,{invalid_unit}",
        "1,100",
    ]
    _write_csv(tmp_path, "profiles/load_shifting.csv", csv_lines)

    yaml_content = """load_shifting:
  - load_shift_id: LS1
    stages: [S1]
    hubs: [H1]
    ec: E0
    interval_length: 1 h
    profile_path: profiles/load_shifting.csv
"""
    _write_yaml(tmp_path, "load_shifting.yaml", yaml_content)
    root_node = yaml_parser.parse(str(tmp_path / "load_shifting.yaml"))

    with pytest.raises(exceptions.ParsingException) as exc_info:
        load_shifting_parser.parse(root_node, _create_test_ecs())

    assert "Invalid unit" in str(exc_info.value)
    assert expected_msg in str(exc_info.value)


def test_parse_profile_with_unparseable_unit(tmp_path):
    """Test that profile with unparseable unit string raises exception"""
    csv_lines = [
        "loadshift_id,LS1",
        "profile_key,max_above_abs",
        "unit,invalid_unit_xyz",
        "1,100",
    ]
    _write_csv(tmp_path, "profiles/load_shifting.csv", csv_lines)

    yaml_content = """load_shifting:
  - load_shift_id: LS1
    stages: [S1]
    hubs: [H1]
    ec: E0
    interval_length: 1 h
    profile_path: profiles/load_shifting.csv
"""
    _write_yaml(tmp_path, "load_shifting.yaml", yaml_content)
    root_node = yaml_parser.parse(str(tmp_path / "load_shifting.yaml"))

    with pytest.raises(exceptions.ParsingException) as exc_info:
        load_shifting_parser.parse(root_node, _create_test_ecs())

    assert "Invalid unit 'invalid_unit_xyz'" in str(exc_info.value)


def test_parse_profile_with_unrecognized_key_is_ignored(tmp_path):
    """Test that unrecognized profile keys are silently ignored"""
    csv_lines = [
        "loadshift_id,LS1,LS1",
        "profile_key,max_above_abs,unrecognized_key",
        "unit,kW,kW",
        "1,100,999",
        "2,150,888",
    ]
    _write_csv(tmp_path, "profiles/load_shifting.csv", csv_lines)

    yaml_content = """load_shifting:
  - load_shift_id: LS1
    stages: [S1]
    hubs: [H1]
    ec: E0
    interval_length: 1 h
    profile_path: profiles/load_shifting.csv
"""
    load_shifting = _parse_load_shifting(tmp_path, yaml_content)

    # Should successfully parse, ignoring unrecognized key
    max_above = load_shifting.get_max_above_abs(LoadShiftId("LS1"))
    assert max_above.get_value(TimeId("1")).to_float(PowerUnit.KW) == 100


# ============================================================================
# Edge cases and comprehensive scenarios
# ============================================================================


def test_parse_large_number_of_tuples(tmp_path):
    """Test parsing with large cartesian product of stages and hubs"""
    stages = ["S1", "S2", "S3", "S4"]
    hubs = ["H1", "H2", "H3", "H4", "H5"]

    yaml_content = f"""load_shifting:
  - load_shift_id: LS1
    stages: {stages}
    hubs: {hubs}
    ec: E0
    interval_length: 2 h
"""
    load_shifting = _parse_load_shifting(tmp_path, yaml_content)

    # 4 stages * 5 hubs = 20 tuples
    assert len(load_shifting.get_stage_hub_tuples(LoadShiftId("LS1"))) == 20


def test_parse_complex_scenario_with_mixed_parameters(tmp_path):
    """Test complex scenario with multiple entries and mixed parameters"""
    csv_lines = [
        "loadshift_id,LS2,LS2",
        "profile_key,max_above_abs,max_below_abs",
        "unit,kW,kW",
        "1,200,100",
        "2,250,120",
    ]
    _write_csv(tmp_path, "profiles/load_shifting.csv", csv_lines)

    yaml_content = """load_shifting:
  - load_shift_id: LS1
    stages: [S1]
    hubs: [H1]
    ec: E0
    interval_length: 1 h
    max_above_abs: 100 kW
    capex_per_cap: 150 CHF/kWh
  - load_shift_id: LS2
    stages: [S2]
    hubs: [H2]
    ec: E0
    interval_length: 2 h
    profile_path: profiles/load_shifting.csv
  - load_shift_id: LS3
    stages: [S1]
    hubs: [H1]
    ec: E1
    interval_length: 4 h
    energy_cost_above: 5000 CHF/MWh
"""
    load_shifting = _parse_load_shifting(tmp_path, yaml_content)

    assert len(load_shifting.ids) == 3

    # Check LS1
    ls1 = LoadShiftId("LS1")
    assert (StageId("S1"), HubId("H1")) in load_shifting.get_stage_hub_tuples(ls1)
    assert load_shifting.get_max_above_abs(ls1).def_value.to_float(PowerUnit.KW) == 100

    # Check LS2
    ls2 = LoadShiftId("LS2")
    assert (StageId("S2"), HubId("H2")) in load_shifting.get_stage_hub_tuples(ls2)
    assert load_shifting.get_max_above_abs(ls2).get_value(TimeId("1")).to_float(PowerUnit.KW) == 200
    assert load_shifting.get_max_below_abs(ls2).get_value(TimeId("2")).to_float(PowerUnit.KW) == 120

    # Check LS3
    ls3 = LoadShiftId("LS3")
    assert load_shifting.get_interval_length(ls3).to_float(TimeUnit.H) == 4
    assert load_shifting.get_energy_cost_above(ls3).def_value.to_float(
        CurrencyUnit.CHF / (PowerUnit.MW * TimeUnit.H)
    ) == 5000


def test_parse_with_logging_disabled(tmp_path):
    """Test that parsing works when logging is mocked"""
    yaml_content = """load_shifting:
  - load_shift_id: LS1
    stages: [S1]
    hubs: [H1]
    ec: E0
    interval_length: 1 h
"""
    _write_yaml(tmp_path, "load_shifting.yaml", yaml_content)
    root_node = yaml_parser.parse(str(tmp_path / "load_shifting.yaml"))

    with patch('ehubx.core.logging.log_file') as mock_log_file:
        load_shifting = load_shifting_parser.parse(root_node, _create_test_ecs())

    assert len(load_shifting.ids) == 1
    mock_log_file.assert_called()


def test_parse_empty_load_shifting_list(tmp_path):
    """Test parsing with empty load_shifting list"""
    load_shifting = _parse_load_shifting(tmp_path, "load_shifting: []")

    assert isinstance(load_shifting, LoadShifting)
    assert len(load_shifting.ids) == 0
