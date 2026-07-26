from unittest.mock import MagicMock, patch
import pytest
import pandas as pd
from ehubx.data.time_data import TimeId
from ehubx.parser import hp_tech_parser, exceptions, csv_parser
from ehubx.data.hp_tech_data import HeatpumpTechs
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.unit import PowerUnit, DimlessUnit, TemperatureUnit
from ehubx.data.value import Value
from ehubx.data import exceptions as data_exceptions


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def stages():
    """Mock Stages object"""
    return MagicMock(spec=Stages)


@pytest.fixture
def ecs():
    """Mock Ecs object with sensible defaults"""
    from ehubx.data.unit import TimeUnit
    mock_ecs = MagicMock(spec=Ecs)
    mock_ecs.get_unit.return_value = PowerUnit.KW * TimeUnit.H
    return mock_ecs


@pytest.fixture
def techs():
    """Mock Techs object"""
    return MagicMock(spec=Techs)


@pytest.fixture
def hp_techs():
    """HeatpumpTechs instance"""
    return HeatpumpTechs()


@pytest.fixture
def hub_id():
    """Sample hub ID"""
    return HubId("hub_test")


@pytest.fixture
def tech_id():
    """Sample tech ID"""
    return TechId("hp_tech_test")


@pytest.fixture
def stage_id():
    """Sample stage ID"""
    return StageId("2025")


@pytest.fixture
def hp_techs_with_ecs(hp_techs, tech_id):
    """HeatpumpTechs instance with a tech that has ECs configured"""
    from ehubx.data.unit import TimeUnit
    hp_techs.add_id(tech_id)
    energy_unit = PowerUnit.KW * TimeUnit.H
    hp_techs.set_ec_el(tech_id, EcId("electricity"), energy_unit)
    hp_techs.set_ec_ht_in(tech_id, EcId("heat_in"), energy_unit)
    hp_techs.set_ec_ht_out(tech_id, EcId("heat_out"), energy_unit)
    hp_techs.set_ec_co_in(tech_id, EcId("cool_in"), energy_unit)
    hp_techs.set_ec_co_out(tech_id, EcId("cool_out"), energy_unit)
    return hp_techs


# ============================================================================
# TEST: parse_primary
# ============================================================================


class TestParsePrimary:
    """Tests for parse_primary function"""

    def test_none_root_node(self, stages, ecs, techs):
        """Should return empty HeatpumpTechs when root_node is None"""
        result = hp_tech_parser.parse_primary(None, stages, ecs, techs)

        assert isinstance(result, HeatpumpTechs)
        assert len(result.ids) == 0

    def test_none_techs_node(self, stages, ecs, techs):
        """Should return empty HeatpumpTechs when techs_node is None"""
        root = MagicMock()
        root.__getitem__.return_value = None

        result = hp_tech_parser.parse_primary(root, stages, ecs, techs)

        assert isinstance(result, HeatpumpTechs)
        assert len(result.ids) == 0

    @patch("ehubx.parser.hp_tech_parser._parse_hp_tech_primary")
    @patch("ehubx.parser.hp_tech_parser._log")
    def test_with_hp_techs(
        self, mock_log, mock_parse_tech, stages, ecs, techs
    ):
        """Should parse heat pump techs correctly"""
        root = MagicMock()
        tech_node = MagicMock()
        techs_node = MagicMock()
        techs_node.__iter__ = MagicMock(return_value=iter([tech_node]))
        root.__getitem__.return_value = techs_node

        result = hp_tech_parser.parse_primary(root, stages, ecs, techs)

        assert isinstance(result, HeatpumpTechs)
        mock_parse_tech.assert_called_once_with(tech_node, stages, ecs, techs, result)
        mock_log.assert_called_once_with(result)


# ============================================================================
# TEST: _parse_hp_tech_primary
# ============================================================================


class TestParseHpTechPrimary:
    """Tests for _parse_hp_tech_primary function"""

    @pytest.mark.parametrize("tech_type", ["storage", "conversion"])
    def test_non_hp_tech_types(self, tech_type, stages, ecs, techs, hp_techs):
        """Should skip non-heatpump tech types"""
        tech_node = MagicMock()

        with patch(
            "ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node",
            return_value="test_tech",
        ), patch(
            "ehubx.parser.yaml_parser.parse_optional_str_from_dict_node",
            return_value=tech_type,
        ):
            hp_tech_parser._parse_hp_tech_primary(
                tech_node, stages, ecs, techs, hp_techs
            )

            assert TechId("test_tech") not in hp_techs.ids

    @patch("ehubx.parser.hp_tech_parser._parse_ecs")
    @patch("ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node")
    @patch("ehubx.parser.yaml_parser.get_mandatory_subnode_from_dict_node")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    @patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    def test_hp_tech_parsing_success(
        self,
        mock_optional_str,
        mock_mandatory_str,
        mock_check_type,
        mock_get_subnode,
        mock_optional_yeardep,
        mock_parse_ecs,
        stages,
        ecs,
        techs,
        hp_techs,
    ):
        """Should parse heat pump tech correctly"""
        mock_optional_str.return_value = "heatpump"
        mock_mandatory_str.return_value = "test_hp"
        mock_optional_yeardep.return_value = None

        tech_node = MagicMock()
        hp_params_node = MagicMock()
        mock_get_subnode.return_value = hp_params_node

        hp_tech_parser._parse_hp_tech_primary(
            tech_node, stages, ecs, techs, hp_techs
        )

        assert TechId("test_hp") in hp_techs.ids
        techs.set_cap_unit.assert_called_once_with(TechId("test_hp"), PowerUnit.KW)
        mock_parse_ecs.assert_called_once()

    @patch("ehubx.parser.hp_tech_parser._parse_ecs")
    @patch("ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node")
    @patch("ehubx.parser.yaml_parser.get_mandatory_subnode_from_dict_node")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    @patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    def test_hp_tech_with_cop_factor(
        self,
        mock_optional_str,
        mock_mandatory_str,
        mock_check_type,
        mock_get_subnode,
        mock_optional_yeardep,
        mock_parse_ecs,
        stages,
        ecs,
        techs,
        hp_techs,
        stage_id,
    ):
        """Should parse heat pump tech with cop_factor"""
        mock_optional_str.return_value = "heatpump"
        mock_mandatory_str.return_value = "test_hp"
        mock_optional_yeardep.return_value = {
            stage_id: Value(0.5, DimlessUnit())
        }

        tech_node = MagicMock()
        hp_params_node = MagicMock()
        mock_get_subnode.return_value = hp_params_node

        hp_tech_parser._parse_hp_tech_primary(
            tech_node, stages, ecs, techs, hp_techs
        )

        assert TechId("test_hp") in hp_techs.ids
        # cop_factor should be set
        mock_optional_yeardep.assert_called_once()


# ============================================================================
# TEST: _parse_ecs
# ============================================================================


class TestParseEcs:
    """Tests for _parse_ecs function"""

    @patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
    @patch("ehubx.parser.yaml_parser.get_mandatory_subnode_from_dict_node")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    def test_parse_all_ecs(
        self,
        mock_check_type,
        mock_get_subnode,
        mock_mandatory_str,
        tech_id,
        ecs,
        hp_techs,
    ):
        """Should parse all energy carriers for heat pump"""
        from ehubx.data.unit import TimeUnit
        # Add tech_id before setting ECs
        hp_techs.add_id(tech_id)

        # Mock ecs.get_unit to return energy unit
        ecs.get_unit.return_value = PowerUnit.KW * TimeUnit.H

        mock_mandatory_str.side_effect = [
            "electricity",  # ec_el
            "heat_in",  # ec_ht_in
            "heat_out",  # ec_ht_out
            "cool_in",  # ec_co_in
            "cool_out",  # ec_co_out
        ]

        hp_params_node = MagicMock()
        ecs_node = MagicMock()
        mock_get_subnode.return_value = ecs_node

        hp_tech_parser._parse_ecs(hp_params_node, tech_id, ecs, hp_techs)

        assert hp_techs.get_ec_el(tech_id) == EcId("electricity")
        assert hp_techs.get_ec_ht_in(tech_id) == EcId("heat_in")
        assert hp_techs.get_ec_ht_out(tech_id) == EcId("heat_out")
        assert hp_techs.get_ec_co_in(tech_id) == EcId("cool_in")
        assert hp_techs.get_ec_co_out(tech_id) == EcId("cool_out")
        assert mock_mandatory_str.call_count == 5


# ============================================================================
# TEST: parse_secondary
# ============================================================================


class TestParseSecondary:
    """Tests for parse_secondary function"""

    @patch("ehubx.parser.hp_tech_parser._parse_hub_secondary")
    def test_none_root_node(self, mock_parse_hub, stages, hp_techs):
        """Should return early when root_node is None"""
        hp_tech_parser.parse_secondary(None, stages, hp_techs)
        # Should not raise
        mock_parse_hub.assert_not_called()

    @patch("ehubx.parser.hp_tech_parser._parse_hub_secondary")
    def test_none_hubs_node(self, mock_parse_hub, stages, hp_techs):
        """Should return early when hubs_node is None"""
        root = MagicMock()
        root.__getitem__.return_value = None

        hp_tech_parser.parse_secondary(root, stages, hp_techs)
        # Should not raise
        mock_parse_hub.assert_not_called()

    @patch("ehubx.parser.hp_tech_parser._parse_hub_secondary")
    def test_with_hubs(self, mock_parse_hub, stages, hp_techs):
        """Should parse hubs correctly"""
        root = MagicMock()
        hub_node = MagicMock()
        hubs_node = MagicMock()
        hubs_node.__iter__ = MagicMock(return_value=iter([hub_node]))
        root.__getitem__.return_value = hubs_node

        hp_tech_parser.parse_secondary(root, stages, hp_techs)

        mock_parse_hub.assert_called_once_with(hub_node, stages, hp_techs)


# ============================================================================
# TEST: _parse_hub_secondary
# ============================================================================


class TestParseHubSecondary:
    """Tests for _parse_hub_secondary function"""

    @patch("ehubx.parser.hp_tech_parser._parse_tech_secondary")
    @patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
    def test_none_techs_node(self, mock_str, mock_parse_tech, stages, hp_techs):
        """Should return early when techs node is None"""
        mock_str.return_value = "hub1"
        hub_node = MagicMock()
        hub_node.__getitem__.return_value = None

        hp_tech_parser._parse_hub_secondary(hub_node, stages, hp_techs)
        # Should not raise
        mock_parse_tech.assert_not_called()

    @patch("ehubx.parser.hp_tech_parser._parse_tech_secondary")
    @patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
    def test_with_tech(self, mock_str, mock_parse_tech, stages, tech_id, hp_techs_with_ecs):
        """Should parse tech secondary when tech node exists"""
        mock_str.return_value = "hub1"

        hub_node = MagicMock()
        techs_node = MagicMock()
        tech_node = MagicMock()
        techs_node.__getitem__.return_value = tech_node
        hub_node.__getitem__.return_value = techs_node

        hp_tech_parser._parse_hub_secondary(hub_node, stages, hp_techs_with_ecs)

        mock_parse_tech.assert_called_once()

    @patch("ehubx.parser.hp_tech_parser._parse_tech_secondary")
    @patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
    def test_tech_node_none(self, mock_str, mock_parse_tech, stages, tech_id, hp_techs_with_ecs):
        """Should skip tech when tech node is None"""
        mock_str.return_value = "hub1"

        hub_node = MagicMock()
        techs_node = MagicMock()
        techs_node.__getitem__.return_value = None
        hub_node.__getitem__.return_value = techs_node

        hp_tech_parser._parse_hub_secondary(hub_node, stages, hp_techs_with_ecs)
        # Should not raise
        mock_parse_tech.assert_not_called()

# ============================================================================
# TEST: _parse_tech_secondary
# ============================================================================


class TestParseTechSecondary:
    """Tests for _parse_tech_secondary function"""

    @patch("ehubx.parser.yaml_parser.check_node_type")
    def test_none_hp_params_node(self, mock_check_type, hub_id, tech_id, stages, hp_techs_with_ecs):
        """Should return early when hp_params node is None"""
        tech_node = MagicMock()
        tech_node.__getitem__.return_value = None

        hp_tech_parser._parse_tech_secondary(
            tech_node, hub_id, tech_id, stages, hp_techs_with_ecs
        )
        # Should not raise
        mock_check_type.assert_not_called()

    @patch("ehubx.parser.hp_tech_parser._parse_tech_secondary_profiles")
    @patch("ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    def test_with_cop(
        self,
        mock_check_type,
        mock_optional_yeardep,
        mock_parse_profiles,
        hub_id,
        tech_id,
        stage_id,
        stages,
        hp_techs_with_ecs,
    ):
        """Should parse cop parameter"""
        mock_optional_yeardep.side_effect = [
            {stage_id: Value(3.5, DimlessUnit())},  # cop
            None,  # temp_ht_in
            None,  # temp_ht_out
            None,  # availability
        ]

        tech_node = MagicMock()
        hp_params_node = MagicMock()
        tech_node.__getitem__.return_value = hp_params_node

        hp_tech_parser._parse_tech_secondary(
            tech_node, hub_id, tech_id, stages, hp_techs_with_ecs
        )

        # cop should be set
        assert mock_optional_yeardep.call_count >= 1
        assert hp_techs_with_ecs.get_cop(stage_id, hub_id, tech_id, MagicMock()).def_value == Value(3.5, DimlessUnit())

    @patch("ehubx.parser.hp_tech_parser._parse_tech_secondary_profiles")
    @patch("ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    def test_with_temperatures(
        self,
        mock_check_type,
        mock_optional_yeardep,
        mock_parse_profiles,
        hub_id,
        tech_id,
        stage_id,
        stages,
        hp_techs_with_ecs,
    ):
        """Should parse temperature parameters"""
        mock_optional_yeardep.side_effect = [
            None,  # cop
            {stage_id: Value(273.15, TemperatureUnit.K)},  # temp_ht_in
            {stage_id: Value(323.15, TemperatureUnit.K)},  # temp_ht_out
            None,  # availability
        ]

        tech_node = MagicMock()
        hp_params_node = MagicMock()
        tech_node.__getitem__.return_value = hp_params_node

        hp_tech_parser._parse_tech_secondary(
            tech_node, hub_id, tech_id, stages, hp_techs_with_ecs
        )

        assert mock_optional_yeardep.call_count >= 2
        assert hp_techs_with_ecs.get_temp_ht_in(stage_id, hub_id, tech_id).def_value == Value(273.15, TemperatureUnit.K)
        assert hp_techs_with_ecs.get_temp_ht_out(stage_id, hub_id, tech_id).def_value == Value(323.15, TemperatureUnit.K)

    @patch("ehubx.parser.hp_tech_parser._parse_tech_secondary_profiles")
    @patch("ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    def test_with_availability(
        self,
        mock_check_type,
        mock_optional_yeardep,
        mock_parse_profiles,
        hub_id,
        tech_id,
        stage_id,
        stages,
        hp_techs_with_ecs,
    ):
        """Should parse availability parameter"""
        mock_optional_yeardep.side_effect = [
            None,  # cop
            None,  # temp_ht_in
            None,  # temp_ht_out
            {stage_id: Value(0.95, DimlessUnit())},  # availability
        ]

        tech_node = MagicMock()
        hp_params_node = MagicMock()
        tech_node.__getitem__.return_value = hp_params_node

        hp_tech_parser._parse_tech_secondary(
            tech_node, hub_id, tech_id, stages, hp_techs_with_ecs
        )

        assert mock_optional_yeardep.call_count >=3
        mock_parse_profiles.assert_called_once()
        assert hp_techs_with_ecs.get_availability(stage_id, hub_id, tech_id).def_value == Value(0.95, DimlessUnit())

    @patch("ehubx.parser.hp_tech_parser._parse_tech_secondary_profiles")
    @patch("ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    def test_with_all_params_none(
        self,
        mock_check_type,
        mock_optional_yeardep,
        mock_parse_profiles,
        hub_id,
        tech_id,
        stages,
        hp_techs_with_ecs,
    ):
        """Should handle all optional parameters being None"""
        mock_optional_yeardep.return_value = None

        tech_node = MagicMock()
        hp_params_node = MagicMock()
        tech_node.__getitem__.return_value = hp_params_node

        hp_tech_parser._parse_tech_secondary(
            tech_node, hub_id, tech_id, stages, hp_techs_with_ecs
        )

        assert mock_optional_yeardep.call_count == 4
        mock_parse_profiles.assert_called_once()


# ============================================================================
# TEST: _parse_tech_secondary_profiles
# ============================================================================


class TestParseTechSecondaryProfiles:
    """Tests for _parse_tech_secondary_profiles function"""

    @patch("ehubx.parser.yaml_parser.check_file_exists")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node", return_value=None,)
    def test_none_profile_path(self, mock_parse_str, mock_check_file, hub_id, tech_id, hp_techs_with_ecs):
        """Should return early when profile_path is None"""
        hp_params_node = MagicMock()

        hp_tech_parser._parse_tech_secondary_profiles(
            hp_params_node, hub_id, tech_id, hp_techs_with_ecs
        )
        # Should not raise
        mock_check_file.assert_not_called()

    @patch("ehubx.data.hp_tech_data.HeatpumpTechs.set_cop")
    @patch("ehubx.parser.csv_parser.parse")
    @patch("ehubx.parser.yaml_parser.check_file_exists")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    def test_with_valid_profile_cop(
        self,
        mock_parse_str,
        mock_check_file,
        mock_csv_parse,
        mock_set_cop,
        hub_id,
        tech_id,
        stage_id,
        hp_techs_with_ecs,
    ):
        """Should parse cop profile correctly"""
        mock_parse_str.return_value = "profiles/hp_profile.csv"

        hp_params_node = MagicMock()
        hp_params_node.file_path = "/path/to/file.yaml"

        # Create mock DataFrame with cop profile
        df = pd.DataFrame(
            {
                (stage_id.key, hub_id.key, tech_id.key, "cop"): {
                    "t1": 3.5,
                    "t2": 3.7,
                }
            }
        )
        df.attrs = {
            csv_parser.ATTR_UNIT: {
                (stage_id.key, hub_id.key, tech_id.key, "cop"): ""
            }
        }
        mock_csv_parse.return_value = df

        hp_tech_parser._parse_tech_secondary_profiles(
            hp_params_node, hub_id, tech_id, hp_techs_with_ecs
        )

        mock_check_file.assert_called_once()
        mock_csv_parse.assert_called_once()
        mock_set_cop.assert_any_call(stage_id, hub_id, tech_id, TimeId("t1"), Value(3.5, DimlessUnit()))
        mock_set_cop.assert_any_call(stage_id, hub_id, tech_id, TimeId("t2"), Value(3.7, DimlessUnit()))

    @patch("ehubx.data.hp_tech_data.HeatpumpTechs.set_temp_ht_out")
    @patch("ehubx.data.hp_tech_data.HeatpumpTechs.set_temp_ht_in")
    @patch("ehubx.parser.csv_parser.parse")
    @patch("ehubx.parser.yaml_parser.check_file_exists")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    def test_with_valid_profile_temperatures(
        self,
        mock_parse_str,
        mock_check_file,
        mock_csv_parse,
        mock_set_temp_ht_in,
        mock_set_temp_ht_out,
        hub_id,
        tech_id,
        stage_id,
        hp_techs_with_ecs,
    ):
        """Should parse temperature profiles correctly"""
        mock_parse_str.return_value = "profiles/hp_profile.csv"

        hp_params_node = MagicMock()
        hp_params_node.file_path = "/path/to/file.yaml"

        # Create mock DataFrame with temperature profiles
        df = pd.DataFrame(
            {
                (stage_id.key, hub_id.key, tech_id.key, "temp_heat_in"): {
                    "t1": 273.15,
                    "t2": 278.15,
                },
                (stage_id.key, hub_id.key, tech_id.key, "temp_heat_out"): {
                    "t1": 323.15,
                    "t2": 328.15,
                },
            }
        )
        df.attrs = {
            csv_parser.ATTR_UNIT: {
                (stage_id.key, hub_id.key, tech_id.key, "temp_heat_in"): "K",
                (stage_id.key, hub_id.key, tech_id.key, "temp_heat_out"): "K",
            }
        }
        mock_csv_parse.return_value = df

        hp_tech_parser._parse_tech_secondary_profiles(
            hp_params_node, hub_id, tech_id, hp_techs_with_ecs
        )

        mock_check_file.assert_called_once()
        mock_csv_parse.assert_called_once()
        mock_set_temp_ht_in.assert_any_call(stage_id, hub_id, tech_id, TimeId("t1"), Value(273.15, TemperatureUnit.K))
        mock_set_temp_ht_in.assert_any_call(stage_id, hub_id, tech_id, TimeId("t2"), Value(278.15, TemperatureUnit.K))
        mock_set_temp_ht_out.assert_any_call(stage_id, hub_id, tech_id, TimeId("t1"), Value(323.15, TemperatureUnit.K))
        mock_set_temp_ht_out.assert_any_call(stage_id, hub_id, tech_id, TimeId("t2"), Value(328.15, TemperatureUnit.K))

    @patch("ehubx.data.hp_tech_data.HeatpumpTechs.set_availability")
    @patch("ehubx.parser.csv_parser.parse")
    @patch("ehubx.parser.yaml_parser.check_file_exists")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    def test_with_valid_profile_availability(
        self,
        mock_parse_str,
        mock_check_file,
        mock_csv_parse,
        mock_set_availability,
        hub_id,
        tech_id,
        stage_id,
        hp_techs_with_ecs,
    ):
        """Should parse availability profile correctly"""
        mock_parse_str.return_value = "profiles/hp_profile.csv"

        hp_params_node = MagicMock()
        hp_params_node.file_path = "/path/to/file.yaml"

        # Create mock DataFrame with availability profile
        df = pd.DataFrame(
            {
                (stage_id.key, hub_id.key, tech_id.key, "availability"): {
                    "t1": 1.0,
                    "t2": 0.95,
                }
            }
        )
        df.attrs = {
            csv_parser.ATTR_UNIT: {
                (stage_id.key, hub_id.key, tech_id.key, "availability"): ""
            }
        }
        mock_csv_parse.return_value = df

        hp_tech_parser._parse_tech_secondary_profiles(
            hp_params_node, hub_id, tech_id, hp_techs_with_ecs
        )

        mock_check_file.assert_called_once()
        mock_csv_parse.assert_called_once()
        mock_set_availability.assert_any_call(stage_id, hub_id, tech_id, TimeId("t1"), Value(1.0, DimlessUnit()))
        mock_set_availability.assert_any_call(stage_id, hub_id, tech_id, TimeId("t2"), Value(0.95, DimlessUnit()))

    @patch("ehubx.data.hp_tech_data.HeatpumpTechs.set_cop")
    @patch("ehubx.parser.csv_parser.parse")
    @patch("ehubx.parser.yaml_parser.check_file_exists")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    def test_profile_wrong_hub_id(
        self,
        mock_parse_str,
        mock_check_file,
        mock_csv_parse,
        mock_set_cop,
        hub_id,
        tech_id,
        stage_id,
        hp_techs_with_ecs,
    ):
        """Should skip profiles with non-matching hub_id"""
        mock_parse_str.return_value = "profiles/hp_profile.csv"

        hp_params_node = MagicMock()
        hp_params_node.file_path = "/path/to/file.yaml"

        # Create mock DataFrame with different hub_id
        df = pd.DataFrame(
            {
                (stage_id.key, "different_hub", tech_id.key, "cop"): {
                    "t1": 3.5,
                }
            }
        )
        df.attrs = {
            csv_parser.ATTR_UNIT: {
                (stage_id.key, "different_hub", tech_id.key, "cop"): "-"
            }
        }
        mock_csv_parse.return_value = df

        hp_tech_parser._parse_tech_secondary_profiles(
            hp_params_node, hub_id, tech_id, hp_techs_with_ecs
        )

        mock_check_file.assert_called_once()
        mock_csv_parse.assert_called_once()
        # Should not set any values but should not raise
        mock_set_cop.assert_not_called()

    @patch("ehubx.data.hp_tech_data.HeatpumpTechs.set_cop")
    @patch("ehubx.parser.csv_parser.parse")
    @patch("ehubx.parser.yaml_parser.check_file_exists")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    def test_profile_wrong_tech_id(
        self,
        mock_parse_str,
        mock_check_file,
        mock_csv_parse,
        mock_set_cop,
        hub_id,
        tech_id,
        stage_id,
        hp_techs_with_ecs,
    ):
        """Should skip profiles with non-matching tech_id"""
        mock_parse_str.return_value = "profiles/hp_profile.csv"

        hp_params_node = MagicMock()
        hp_params_node.file_path = "/path/to/file.yaml"

        # Create mock DataFrame with different tech_id
        df = pd.DataFrame(
            {
                (stage_id.key, hub_id.key, "different_tech", "cop"): {
                    "t1": 3.5,
                }
            }
        )
        df.attrs = {
            csv_parser.ATTR_UNIT: {
                (stage_id.key, hub_id.key, "different_tech", "cop"): "-"
            }
        }
        mock_csv_parse.return_value = df

        hp_tech_parser._parse_tech_secondary_profiles(
            hp_params_node, hub_id, tech_id, hp_techs_with_ecs
        )

        mock_check_file.assert_called_once()
        mock_csv_parse.assert_called_once()
        # Should not set any values but should not raise
        mock_set_cop.assert_not_called()

# ============================================================================
# TEST: Exception Handling
# ============================================================================


class TestExceptionHandling:
    """Tests for exception handling in hp_tech_parser"""

    @patch("ehubx.parser.csv_parser.parse")
    @patch("ehubx.parser.yaml_parser.check_file_exists")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    def test_invalid_unit_exception(
        self,
        mock_parse_str,
        mock_check_file,
        mock_csv_parse,
        hub_id,
        tech_id,
        stage_id,
        hp_techs_with_ecs,
    ):
        """Should raise ParsingException when unit is invalid"""
        mock_parse_str.return_value = "profiles/hp_profile.csv"

        hp_params_node = MagicMock()
        hp_params_node.file_path = "/path/to/file.yaml"

        # Create mock DataFrame with invalid unit
        df = pd.DataFrame(
            {
                (stage_id.key, hub_id.key, tech_id.key, "cop"): {
                    "t1": 3.5,
                }
            }
        )
        df.attrs = {
            csv_parser.ATTR_UNIT: {
                (stage_id.key, hub_id.key, tech_id.key, "cop"): "invalid_unit"
            }
        }
        mock_csv_parse.return_value = df

        # Mock Unit.from_str to raise UnitException
        with patch(
            "ehubx.data.unit.Unit.from_str",
            side_effect=data_exceptions.UnitException("invalid_unit", "Test error message"),
        ):
            with pytest.raises(exceptions.ParsingException) as exc_info:
                hp_tech_parser._parse_tech_secondary_profiles(
                    hp_params_node, hub_id, tech_id, hp_techs_with_ecs
                )

            assert "Invalid unit 'invalid_unit'" in str(exc_info.value)
            assert "cop" in str(exc_info.value)

    @patch("ehubx.parser.csv_parser.parse")
    @patch("ehubx.parser.yaml_parser.check_file_exists")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    def test_wrong_unit_type_for_cop(
        self,
        mock_parse_str,
        mock_check_file,
        mock_csv_parse,
        hub_id,
        tech_id,
        stage_id,
        hp_techs_with_ecs,
    ):
        """Should raise ParsingException when unit type is wrong for cop"""
        mock_parse_str.return_value = "profiles/hp_profile.csv"

        hp_params_node = MagicMock()
        hp_params_node.file_path = "/path/to/file.yaml"

        # Create mock DataFrame with wrong unit type for cop
        df = pd.DataFrame(
            {
                (stage_id.key, hub_id.key, tech_id.key, "cop"): {
                    "t1": 3.5,
                }
            }
        )
        df.attrs = {
            csv_parser.ATTR_UNIT: {
                (stage_id.key, hub_id.key, tech_id.key, "cop"): "kW"  # Wrong unit type
            }
        }
        mock_csv_parse.return_value = df

        with pytest.raises(exceptions.ParsingException) as exc_info:
            hp_tech_parser._parse_tech_secondary_profiles(
                hp_params_node, hub_id, tech_id, hp_techs_with_ecs
            )

        assert "Invalid unit" in str(exc_info.value)
        assert "cop" in str(exc_info.value)

    @patch("ehubx.parser.csv_parser.parse")
    @patch("ehubx.parser.yaml_parser.check_file_exists")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    def test_wrong_unit_type_for_temperature(
        self,
        mock_parse_str,
        mock_check_file,
        mock_csv_parse,
        hub_id,
        tech_id,
        stage_id,
        hp_techs_with_ecs,
    ):
        """Should raise ParsingException when unit type is wrong for temperature"""
        mock_parse_str.return_value = "profiles/hp_profile.csv"

        hp_params_node = MagicMock()
        hp_params_node.file_path = "/path/to/file.yaml"

        # Create mock DataFrame with wrong unit type for temperature
        df = pd.DataFrame(
            {
                (stage_id.key, hub_id.key, tech_id.key, "temp_heat_in"): {
                    "t1": 273.15,
                }
            }
        )
        df.attrs = {
            csv_parser.ATTR_UNIT: {
                (stage_id.key, hub_id.key, tech_id.key, "temp_heat_in"): "-"  # Wrong unit
            }
        }
        mock_csv_parse.return_value = df

        with pytest.raises(exceptions.ParsingException) as exc_info:
            hp_tech_parser._parse_tech_secondary_profiles(
                hp_params_node, hub_id, tech_id, hp_techs_with_ecs
            )

        assert "Invalid unit" in str(exc_info.value)
        assert "temp_heat_in" in str(exc_info.value)

    @patch("ehubx.parser.csv_parser.parse")
    @patch("ehubx.parser.yaml_parser.check_file_exists")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    def test_wrong_unit_type_for_availability(
        self,
        mock_parse_str,
        mock_check_file,
        mock_csv_parse,
        hub_id,
        tech_id,
        stage_id,
        hp_techs_with_ecs,
    ):
        """Should raise ParsingException when unit type is wrong for availability"""
        mock_parse_str.return_value = "profiles/hp_profile.csv"

        hp_params_node = MagicMock()
        hp_params_node.file_path = "/path/to/file.yaml"

        # Create mock DataFrame with wrong unit type for availability
        df = pd.DataFrame(
            {
                (stage_id.key, hub_id.key, tech_id.key, "availability"): {
                    "t1": 1.0,
                }
            }
        )
        df.attrs = {
            csv_parser.ATTR_UNIT: {
                (stage_id.key, hub_id.key, tech_id.key, "availability"): "K"  # Wrong unit
            }
        }
        mock_csv_parse.return_value = df

        with pytest.raises(exceptions.ParsingException) as exc_info:
            hp_tech_parser._parse_tech_secondary_profiles(
                hp_params_node, hub_id, tech_id, hp_techs_with_ecs
            )

        assert "Invalid unit" in str(exc_info.value)
        assert "availability" in str(exc_info.value)

    @patch("ehubx.parser.csv_parser.parse")
    @patch("ehubx.parser.yaml_parser.check_file_exists")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    def test_unknown_profile_key(
        self,
        mock_parse_str,
        mock_check_file,
        mock_csv_parse,
        hub_id,
        tech_id,
        stage_id,
        hp_techs_with_ecs,
    ):
        """Should handle unknown profile keys gracefully"""
        mock_parse_str.return_value = "profiles/hp_profile.csv"

        hp_params_node = MagicMock()
        hp_params_node.file_path = "/path/to/file.yaml"

        # Create mock DataFrame with unknown key
        df = pd.DataFrame(
            {
                (stage_id.key, hub_id.key, tech_id.key, "unknown_key"): {
                    "t1": 1.0,
                }
            }
        )
        df.attrs = {
            csv_parser.ATTR_UNIT: {
                (stage_id.key, hub_id.key, tech_id.key, "unknown_key"): ""
            }
        }
        mock_csv_parse.return_value = df

        # Should not raise for unknown keys with valid units, just skip them
        hp_tech_parser._parse_tech_secondary_profiles(
            hp_params_node, hub_id, tech_id, hp_techs_with_ecs
        )

        mock_check_file.assert_called_once()
        mock_csv_parse.assert_called_once()


# ============================================================================
# TEST: Logging
# ============================================================================


class TestLogging:
    """Tests for _log function"""

    @patch("ehubx.core.logging.log_file")
    def test_log_empty_hp_techs(self, mock_log_file):
        """Should log correctly for empty HeatpumpTechs"""
        hp_techs = HeatpumpTechs()

        hp_tech_parser._log(hp_techs)

        mock_log_file.assert_called()
        # Should log "Parsed 0 heat pump tech(s)"

    @patch("ehubx.core.logging.log_file")
    def test_log_with_hp_techs(self, mock_log_file, tech_id, hp_techs_with_ecs):
        """Should log correctly for HeatpumpTechs with techs"""
        hp_tech_parser._log(hp_techs_with_ecs)

        # Should be called at least twice (header + tech details)
        assert mock_log_file.call_count >= 2
