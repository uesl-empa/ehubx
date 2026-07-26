import pytest
from unittest.mock import MagicMock, patch
from ehubx.parser import ates_parser, csv_parser
from ehubx.data.ates_tech_data import AtesTechs
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.ec_data import Ecs
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.ates_data import AtesScheduleId, AtesData
from ehubx.data.unit import LengthUnit, PowerUnit, MassUnit, TimeUnit, TemperatureUnit, CurrencyUnit, DimlessUnit
from ehubx.data.value import Value


# Fixtures
@pytest.fixture
def stages():
    return MagicMock(spec=Stages)


@pytest.fixture
def ecs():
    mock_ecs = MagicMock(spec=Ecs)
    mock_ecs.get_unit.return_value = PowerUnit.KW * TimeUnit.H
    return mock_ecs


@pytest.fixture
def techs():
    return MagicMock(spec=Techs)


@pytest.fixture
def ates_techs():
    return AtesTechs()


@pytest.fixture
def tech_id():
    return TechId("test_tech")


@pytest.fixture
def hub_id():
    return HubId("hub1")


@pytest.fixture
def schedule_id():
    return AtesScheduleId("schedule1")


@pytest.fixture
def ates_techs_with_id(ates_techs, tech_id):
    ates_techs.add_id(tech_id)
    return ates_techs


# Test Primary Parsing Functions
@pytest.mark.parametrize("root_node,expected_count", [
    (None, 0),
    (MagicMock(__getitem__=lambda self, k: None), 0),
])
def test_parse_primary_empty_cases(root_node, expected_count, stages, ecs, techs):
    """Test parse_primary with None or empty nodes"""
    result = ates_parser.parse_primary(root_node, stages, ecs, techs)
    assert isinstance(result, AtesTechs)
    assert len(result.ids) == expected_count


@patch("ehubx.parser.ates_parser._parse_ates_tech_primary")
def test_parse_primary_with_techs(mock_parse_tech, stages, ecs, techs):
    """Test parse_primary with valid techs"""
    root = MagicMock(__getitem__=lambda self, k: [MagicMock()])
    result = ates_parser.parse_primary(root, stages, ecs, techs)
    assert isinstance(result, AtesTechs)
    mock_parse_tech.assert_called_once()


@pytest.mark.parametrize("tech_type,should_add", [
    ("conversion", False),
    ("ates", True),
])
@patch("ehubx.parser.ates_parser._parse_emissions")
@patch("ehubx.parser.ates_parser._parse_costs")
@patch("ehubx.parser.ates_parser._parse_ates_tech_params_primary")
@patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
@patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
def test_parse_ates_tech_primary_type_handling(
    mock_mandatory, mock_optional, mock_params, mock_costs, mock_emissions,
    tech_type, should_add, stages, ecs, techs, ates_techs
):
    """Test _parse_ates_tech_primary with different tech types"""
    mock_mandatory.return_value = "test_ates"
    mock_optional.return_value = tech_type

    ates_parser._parse_ates_tech_primary(MagicMock(), stages, ecs, techs, ates_techs)

    assert (TechId("test_ates") in ates_techs.ids) == should_add
    if should_add:
        mock_params.assert_called_once()
        mock_costs.assert_called_once()
        mock_emissions.assert_called_once()


# Test Cost and Emissions Parsing
@pytest.mark.parametrize("parse_func", [ates_parser._parse_costs, ates_parser._parse_emissions])
def test_parse_costs_emissions_none_node(parse_func, stages, tech_id, ates_techs_with_id):
    """Test parsing functions with None node"""
    node = MagicMock(__getitem__=lambda self, k: None)
    parse_func(node, tech_id, stages, ates_techs_with_id)  # Should not raise


@patch("ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node")
@patch("ehubx.parser.yaml_parser.check_node_type")
@pytest.mark.parametrize("values,expected_calls", [
    ({StageId("2025"): Value(1000.0, CurrencyUnit.CHF)}, 2),  # capex set
    ([None, {StageId("2025"): Value(500.0, CurrencyUnit.CHF)}], 2),  # opex set
])
def test_parse_costs_with_values(mock_check, mock_parse, values, expected_calls, stages, tech_id, ates_techs_with_id):
    """Test _parse_costs with capex/opex values"""
    node = MagicMock(__getitem__=lambda self, k: MagicMock())
    mock_parse.side_effect = values if isinstance(values, list) else [values, None]
    ates_parser._parse_costs(node, tech_id, stages, ates_techs_with_id)
    assert mock_parse.call_count == expected_calls


@patch("ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node")
@patch("ehubx.parser.yaml_parser.check_node_type")
def test_parse_emissions_with_co2(mock_check, mock_parse, stages, tech_id, ates_techs_with_id):
    """Test _parse_emissions with CO2 values"""
    node = MagicMock(__getitem__=lambda self, k: MagicMock())
    mock_parse.return_value = {StageId("2025"): Value(100.0, MassUnit.KG)}
    ates_parser._parse_emissions(node, tech_id, stages, ates_techs_with_id)
    mock_parse.assert_called_once()


# Test Secondary Parsing
@pytest.mark.parametrize("root_node", [None, MagicMock(__getitem__=lambda self, k: None)])
def test_parse_secondary_empty_cases(root_node, stages, ates_techs):
    """Test parse_secondary with None or empty nodes"""
    ates_parser.parse_secondary(root_node, stages, ates_techs)  # Should not raise


@patch("ehubx.parser.ates_parser._parse_hub_techs_secondary")
def test_parse_secondary_with_hubs(mock_parse_hub, stages, ates_techs):
    """Test parse_secondary with valid hubs"""
    root = MagicMock(__getitem__=lambda self, k: [MagicMock()])
    ates_parser.parse_secondary(root, stages, ates_techs)
    mock_parse_hub.assert_called_once()


@patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
def test_parse_hub_techs_secondary_none_techs_node(mock_str, stages, ates_techs):
    """Test _parse_hub_techs_secondary when techs node is None"""
    mock_str.return_value = "hub1"
    node = MagicMock(__getitem__=lambda self, k: None)
    ates_parser._parse_hub_techs_secondary(node, stages, ates_techs)  # Should not raise


@patch("ehubx.parser.ates_parser._parse_tech_secondary")
@patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
def test_parse_hub_techs_secondary_with_tech(mock_str, mock_parse, stages):
    """Test _parse_hub_techs_secondary with valid tech"""
    ates_techs = AtesTechs()
    tech_id = TechId("ates1")
    ates_techs.add_id(tech_id)
    mock_str.return_value = "hub1"

    hub_node = MagicMock()
    techs_node = MagicMock(__getitem__=lambda self, k: MagicMock())
    hub_node.__getitem__.return_value = techs_node

    ates_parser._parse_hub_techs_secondary(hub_node, stages, ates_techs)
    mock_parse.assert_called_once()


@patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
def test_parse_hub_techs_secondary_tech_node_none(mock_str, stages):
    """Test _parse_hub_techs_secondary when specific tech node is None"""
    ates_techs = AtesTechs()
    ates_techs.add_id(TechId("ates1"))
    mock_str.return_value = "hub1"

    hub_node = MagicMock()
    techs_node = MagicMock(__getitem__=lambda self, k: None)
    hub_node.__getitem__.return_value = techs_node

    ates_parser._parse_hub_techs_secondary(hub_node, stages, ates_techs)  # Should not raise


@pytest.mark.parametrize("has_ates_params,has_schedule_params", [
    (False, False),
    (True, False),
])
@patch("ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node")
@patch("ehubx.parser.yaml_parser.check_node_type")
def test_parse_tech_secondary_empty_cases(
    mock_check, mock_parse, has_ates_params, has_schedule_params, stages, hub_id, tech_id, ates_techs
):
    """Test _parse_tech_secondary with missing nodes"""
    mock_parse.return_value = None
    node = MagicMock()

    if not has_ates_params:
        node.__getitem__.return_value = None
    else:
        ates_params = MagicMock(__getitem__=lambda self, k: None)
        node.__getitem__.return_value = ates_params

    ates_parser._parse_tech_secondary(node, hub_id, tech_id, stages, ates_techs)  # Should not raise


# Test Data Parsing
@pytest.mark.parametrize("root_node", [None, MagicMock(__getitem__=lambda self, k: None)])
def test_parse_data_empty_cases(root_node, stages):
    """Test parse_data with None or empty nodes"""
    result = ates_parser.parse_data(root_node, stages)
    assert isinstance(result, AtesData)


@patch("ehubx.parser.ates_parser._parse_hub_data_secondary")
def test_parse_data_with_hubs(mock_parse, stages):
    """Test parse_data with valid hubs"""
    root = MagicMock(__getitem__=lambda self, k: [MagicMock()])
    result = ates_parser.parse_data(root, stages)
    assert isinstance(result, AtesData)
    mock_parse.assert_called_once()


@patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
def test_parse_hub_data_secondary_none_ates_params(mock_str, stages):
    """Test _parse_hub_data_secondary when ates_params is None"""
    mock_str.return_value = "hub1"
    node = MagicMock(__getitem__=lambda self, k: None)
    ates_parser._parse_hub_data_secondary(node, stages, AtesData())  # Should not raise


@patch("ehubx.parser.ates_parser._parse_schedule_data")
@patch("ehubx.parser.yaml_parser.check_node_type")
@patch("ehubx.parser.yaml_parser.get_mandatory_subnode_from_dict_node")
@patch("ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node")
@patch("ehubx.parser.yaml_parser.parse_optional_value_from_dict_node")
@patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
def test_parse_hub_data_secondary_with_all_params(
    mock_str, mock_opt_val, mock_opt_yeardep, mock_get_mandatory, mock_check, mock_schedule, stages
):
    """Test _parse_hub_data_secondary with all optional parameters"""
    mock_str.return_value = "hub1"
    mock_opt_val.return_value = None
    mock_opt_yeardep.return_value = None
    mock_get_mandatory.return_value = MagicMock(__iter__=lambda self: iter([MagicMock()]))

    hub_node = MagicMock(__getitem__=lambda self, k: MagicMock())
    ates_parser._parse_hub_data_secondary(hub_node, stages, AtesData())
    assert mock_opt_val.call_count > 0


@patch("ehubx.parser.yaml_parser.parse_mandatory_int_from_dict_node")
@patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
@patch("ehubx.parser.yaml_parser.check_node_type")
def test_parse_schedule_data(mock_check, mock_str, mock_int, hub_id):
    """Test _parse_schedule_data"""
    mock_str.return_value = "schedule1"
    mock_int.return_value = 1
    ates_parser._parse_schedule_data(MagicMock(), hub_id, AtesData())
    assert mock_str.call_count == 1
    assert mock_int.call_count == 4


# Test Profile Parsing
@patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
def test_parse_tech_secondary_profiles_none_path(mock_str, hub_id, tech_id, schedule_id, ates_techs):
    """Test _parse_tech_secondary_profiles when profile_path is None"""
    mock_str.return_value = None
    ates_parser._parse_tech_secondary_profiles(MagicMock(), hub_id, tech_id, schedule_id, ates_techs)


@patch("ehubx.parser.csv_parser.parse")
@patch("ehubx.parser.yaml_parser.check_file_exists")
@patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
@patch("os.path.abspath")
def test_parse_tech_secondary_profiles_with_path(
    mock_abspath, mock_str, mock_check, mock_csv, hub_id, tech_id, schedule_id, ates_techs
):
    """Test _parse_tech_secondary_profiles with valid profile path"""
    node = MagicMock(file_path="/test/path")
    mock_str.return_value = "profile.csv"
    mock_abspath.return_value = "/test/profile.csv"
    mock_csv.return_value = MagicMock(columns=[])

    ates_parser._parse_tech_secondary_profiles(node, hub_id, tech_id, schedule_id, ates_techs)
    mock_check.assert_called_once()
    mock_csv.assert_called_once()


@patch("ehubx.data.unit.Unit.from_str")
@patch("ehubx.parser.csv_parser.parse")
@patch("ehubx.parser.yaml_parser.check_file_exists")
@patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
@patch("os.path.abspath")
def test_parse_tech_secondary_profiles_with_matching_data(
    mock_abspath, mock_str, mock_check, mock_csv, mock_unit, hub_id, tech_id, schedule_id
):
    """Test _parse_tech_secondary_profiles with matching hub/tech/schedule data"""
    ates_techs = AtesTechs()
    ates_techs.add_id(tech_id)

    node = MagicMock(file_path="/test/path")
    mock_str.return_value = "profile.csv"
    mock_abspath.return_value = "/test/profile.csv"
    mock_unit.return_value = DimlessUnit()

    mock_series = MagicMock(items=lambda: [(1, 0.95), (2, 0.90)])
    mock_df = MagicMock(
        columns=[("2025", hub_id.key, tech_id.key, schedule_id.key, "availability")],
        attrs={csv_parser.ATTR_UNIT: {("2025", hub_id.key, tech_id.key, schedule_id.key, "availability"): "-"}},
        __getitem__=lambda self, k: mock_series
    )
    mock_csv.return_value = mock_df

    ates_parser._parse_tech_secondary_profiles(node, hub_id, tech_id, schedule_id, ates_techs)
    mock_check.assert_called_once()


@patch("ehubx.parser.csv_parser.parse")
@patch("ehubx.parser.yaml_parser.check_file_exists")
@patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
@patch("os.path.abspath")
def test_parse_tech_secondary_profiles_skip_non_matching(
    mock_abspath, mock_str, mock_check, mock_csv, hub_id, tech_id, schedule_id, ates_techs
):
    """Test _parse_tech_secondary_profiles skips non-matching hub/tech/schedule"""
    node = MagicMock(file_path="/test/path")
    mock_str.return_value = "profile.csv"
    mock_abspath.return_value = "/test/profile.csv"
    mock_csv.return_value = MagicMock(columns=[
        ("2025", "other_hub", tech_id.key, schedule_id.key, "availability"),
        ("2025", hub_id.key, "other_tech", schedule_id.key, "availability"),
    ])
    ates_parser._parse_tech_secondary_profiles(node, hub_id, tech_id, schedule_id, ates_techs)


# Test Tech Params with Optional Values
@patch("ehubx.data.ates_tech_data.AtesTechs.set_well_radius")
@patch("ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node")
@patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
@patch("ehubx.parser.yaml_parser.parse_optional_value_from_dict_node")
@patch("ehubx.parser.yaml_parser.parse_mandatory_value_from_dict_node")
@patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
@patch("ehubx.parser.yaml_parser.get_mandatory_subnode_from_dict_node")
@patch("ehubx.parser.yaml_parser.check_node_type")
def test_parse_tech_params_with_optional_well_radius(
    mock_check, mock_get, mock_str, mock_val, mock_opt_val, mock_opt_str,
    mock_opt_yeardep, mock_set, stages, ecs, tech_id, ates_techs_with_id
):
    """Test _parse_ates_tech_params_primary with well_radius set"""
    mock_get.return_value = MagicMock()
    mock_str.side_effect = ["elec", "heat", "cool"]
    mock_val.side_effect = [
        Value(1000.0, MassUnit.KG / (LengthUnit.M**3)),
        Value(4.18, (PowerUnit.KW * TimeUnit.H) / (MassUnit.KG * TemperatureUnit.K)),
    ]
    mock_opt_val.return_value = Value(0.1, LengthUnit.M)
    mock_opt_str.return_value = None
    mock_opt_yeardep.return_value = None

    ates_parser._parse_ates_tech_params_primary(MagicMock(), tech_id, stages, ecs, ates_techs_with_id)
    mock_set.assert_called_once()


@patch("ehubx.data.ates_tech_data.AtesTechs.set_elec_per_flow_cool")
@patch("ehubx.data.ates_tech_data.AtesTechs.set_elec_per_flow_heat")
@patch("ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node")
@patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
@patch("ehubx.parser.yaml_parser.parse_optional_value_from_dict_node")
@patch("ehubx.parser.yaml_parser.parse_mandatory_value_from_dict_node")
@patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
@patch("ehubx.parser.yaml_parser.get_mandatory_subnode_from_dict_node")
@patch("ehubx.parser.yaml_parser.check_node_type")
def test_parse_tech_params_with_elec_per_flow(
    mock_check, mock_get, mock_str, mock_val, mock_opt_val, mock_opt_str,
    mock_opt_yeardep, mock_heat, mock_cool, stages, ecs, tech_id, ates_techs_with_id
):
    """Test _parse_ates_tech_params_primary with elec_per_flow_heat and elec_per_flow_cool"""
    mock_get.return_value = MagicMock()
    mock_str.side_effect = ["elec", "heat", "cool"]
    mock_val.side_effect = [
        Value(1000.0, MassUnit.KG / (LengthUnit.M**3)),
        Value(4.18, (PowerUnit.KW * TimeUnit.H) / (MassUnit.KG * TemperatureUnit.K)),
    ]
    mock_opt_val.return_value = None
    mock_opt_str.return_value = None

    stage_id = StageId("2025")
    mock_opt_yeardep.side_effect = [
        {stage_id: Value(0.5, (PowerUnit.KW * TimeUnit.H) / (LengthUnit.M**3))},
        {stage_id: Value(0.3, (PowerUnit.KW * TimeUnit.H) / (LengthUnit.M**3))},
    ]

    ates_parser._parse_ates_tech_params_primary(MagicMock(), tech_id, stages, ecs, ates_techs_with_id)
    mock_heat.assert_called_once()
    mock_cool.assert_called_once()


@patch("ehubx.parser.ates_parser._parse_tech_secondary_profiles")
@patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
@patch("ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node")
@patch("ehubx.parser.yaml_parser.check_node_type")
def test_parse_tech_secondary_with_optional_params(
    mock_check, mock_yeardep, mock_str, mock_profiles, stages, hub_id, tech_id
):
    """Test _parse_tech_secondary with optional parameters set"""
    ates_techs = AtesTechs()
    ates_techs.add_id(tech_id)

    mock_str.return_value = "schedule1"
    stage_id = StageId("2025")
    mock_yeardep.side_effect = [
        {stage_id: Value(0.1, DimlessUnit())},
        {stage_id: Value(0.05, DimlessUnit())},
        {stage_id: Value(100.0, LengthUnit.M)},
        {stage_id: Value(1.0, DimlessUnit())},
        {stage_id: Value(10.0, DimlessUnit())},
        {stage_id: Value(50.0, (LengthUnit.M**3) / TimeUnit.H)},
        {stage_id: Value(50.0, (LengthUnit.M**3) / TimeUnit.H)},
        {stage_id: Value(30.0, LengthUnit.M)},
        {stage_id: Value(30.0, LengthUnit.M)},
        {stage_id: Value(1.2, DimlessUnit())},
        {stage_id: Value(0.8, DimlessUnit())},
        {stage_id: Value(0.95, DimlessUnit())},
    ]

    node = MagicMock()
    ates_params = MagicMock()
    schedule_params = MagicMock(__iter__=lambda self: iter([MagicMock()]))
    node.__getitem__.return_value = ates_params
    ates_params.__getitem__.return_value = schedule_params

    ates_parser._parse_tech_secondary(node, hub_id, tech_id, stages, ates_techs)
    assert mock_yeardep.call_count > 0


# Test Exception Handling
@patch("ehubx.core.logging.log_error")
@patch("ehubx.data.unit.Unit.from_str")
@patch("ehubx.parser.csv_parser.parse")
@patch("ehubx.parser.yaml_parser.check_file_exists")
@patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
@patch("os.path.abspath")
def test_parse_tech_secondary_profiles_invalid_unit_exception(
    mock_abspath, mock_str, mock_check, mock_csv, mock_unit, mock_log, hub_id, tech_id, schedule_id
):
    """Test _parse_tech_secondary_profiles raises ParsingException on invalid unit"""
    from ehubx.data.exceptions import UnitException
    from ehubx.parser.exceptions import ParsingException

    ates_techs = AtesTechs()
    ates_techs.add_id(tech_id)

    node = MagicMock(file_path="/test/path")
    mock_str.return_value = "profile.csv"
    mock_abspath.return_value = "/test/profile.csv"
    mock_unit.side_effect = UnitException("invalid_unit", "Unit not recognized")

    mock_series = MagicMock(items=lambda: [(1, 0.95)])
    mock_df = MagicMock(
        columns=[("2025", hub_id.key, tech_id.key, schedule_id.key, "availability")],
        attrs={csv_parser.ATTR_UNIT: {("2025", hub_id.key, tech_id.key, schedule_id.key, "availability"): "invalid"}},
        __getitem__=lambda self, k: mock_series
    )
    mock_csv.return_value = mock_df

    with pytest.raises(ParsingException) as exc_info:
        ates_parser._parse_tech_secondary_profiles(node, hub_id, tech_id, schedule_id, ates_techs)

    # Verify exception contains expected message
    assert "Invalid unit" in str(exc_info.value)
    assert "availability profile" in str(exc_info.value)
    # Verify file path is stored in exception
    assert exc_info.value._file_path == "/test/profile.csv"


@patch("ehubx.core.logging.log_error")
@patch("ehubx.data.unit.Unit.from_str")
@patch("ehubx.parser.csv_parser.parse")
@patch("ehubx.parser.yaml_parser.check_file_exists")
@patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
@patch("os.path.abspath")
def test_parse_tech_secondary_profiles_unit_type_mismatch_exception(
    mock_abspath, mock_str, mock_check, mock_csv, mock_unit, mock_log, hub_id, tech_id, schedule_id
):
    """Test _parse_tech_secondary_profiles raises ParsingException on unit type mismatch"""
    from ehubx.parser.exceptions import ParsingException

    ates_techs = AtesTechs()
    ates_techs.add_id(tech_id)

    node = MagicMock(file_path="/test/path")
    mock_str.return_value = "profile.csv"
    mock_abspath.return_value = "/test/profile.csv"
    # Return a unit with wrong type (not dimensionless)
    mock_unit.return_value = PowerUnit.KW

    mock_series = MagicMock(items=lambda: [(1, 0.95)])
    mock_df = MagicMock(
        columns=[("2025", hub_id.key, tech_id.key, schedule_id.key, "availability")],
        attrs={csv_parser.ATTR_UNIT: {("2025", hub_id.key, tech_id.key, schedule_id.key, "availability"): "kW"}},
        __getitem__=lambda self, k: mock_series
    )
    mock_csv.return_value = mock_df

    with pytest.raises(ParsingException) as exc_info:
        ates_parser._parse_tech_secondary_profiles(node, hub_id, tech_id, schedule_id, ates_techs)

    # Verify exception contains expected message about unit mismatch
    assert "Invalid unit" in str(exc_info.value)
    assert "Expected a unit like" in str(exc_info.value)
    # Verify file path is stored in exception
    assert exc_info.value._file_path == "/test/profile.csv"

