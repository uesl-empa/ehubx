import pytest
from unittest.mock import MagicMock, patch
import pandas as pd

from ehubx.parser import ebm_tech_parser, csv_parser, exceptions
from ehubx.data.ebm_tech_data import EbmTechs
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.unit import PowerUnit, DimlessUnit, TimeUnit
from ehubx.data.value import Value


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
    mock_ecs = MagicMock(spec=Ecs)
    mock_ecs.get_unit.return_value = PowerUnit.KW * TimeUnit.H
    return mock_ecs


@pytest.fixture
def techs():
    """Mock Techs object"""
    return MagicMock(spec=Techs)


@pytest.fixture
def ebm_techs():
    """EbmTechs instance"""
    return EbmTechs()


@pytest.fixture
def tech_id():
    """Sample tech ID"""
    return TechId("ebm_test")


@pytest.fixture
def hub_id():
    """Sample hub ID"""
    return HubId("hub1")


@pytest.fixture
def stage_id():
    """Sample stage ID"""
    return StageId("2025")


@pytest.fixture
def ec_id():
    """Sample EC ID"""
    return EcId("electricity")


@pytest.fixture
def ebm_techs_with_id(ebm_techs, tech_id, ec_id, ecs):
    """EbmTechs with a pre-added tech"""
    ebm_techs.add_id(tech_id)
    ebm_techs.set_ec(tech_id, ec_id, ecs.get_unit(ec_id))
    return ebm_techs


# ============================================================================
# TEST: parse_primary
# ============================================================================


class TestParsePrimary:
    """Tests for parse_primary function"""

    def test_none_root_node(self, stages, ecs, techs):
        """Should return empty EbmTechs when root node is None"""
        result = ebm_tech_parser.parse_primary(None, stages, ecs, techs)
        assert isinstance(result, EbmTechs)
        assert len(result.ids) == 0

    def test_none_techs_node(self, stages, ecs, techs):
        """Should return empty EbmTechs when techs node is None"""
        root = MagicMock()
        root.__getitem__.return_value = None
        result = ebm_tech_parser.parse_primary(root, stages, ecs, techs)
        assert isinstance(result, EbmTechs)
        assert len(result.ids) == 0

    @patch("ehubx.parser.ebm_tech_parser._parse_ebm_tech_primary")
    def test_with_valid_techs(self, mock_parse_tech, stages, ecs, techs):
        """Should parse techs when valid nodes exist"""
        tech_node = MagicMock()
        techs_node = MagicMock()
        techs_node.__iter__ = MagicMock(return_value=iter([tech_node]))
        root = MagicMock()
        root.__getitem__.return_value = techs_node

        result = ebm_tech_parser.parse_primary(root, stages, ecs, techs)

        assert isinstance(result, EbmTechs)
        mock_parse_tech.assert_called_once()


# ============================================================================
# TEST: _parse_ebm_tech_primary
# ============================================================================


class TestParseEbmTechPrimary:
    """Tests for _parse_ebm_tech_primary function"""

    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
    def test_non_ebm_tech_type(
        self, mock_mandatory, mock_optional, stages, ecs, techs, ebm_techs
    ):
        """Should return early if tech type is not EBM"""
        mock_mandatory.return_value = "test_tech"
        mock_optional.return_value = "conversion"  # Not EBM

        tech_node = MagicMock()
        ebm_tech_parser._parse_ebm_tech_primary(
            tech_node, stages, ecs, techs, ebm_techs
        )

        assert len(ebm_techs.ids) == 0

    @patch("ehubx.parser.yaml_parser.parse_mandatory_yeardep_value_from_dict_node")
    @patch("ehubx.parser.yaml_parser.get_mandatory_subnode_from_dict_node")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    @patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    def test_ebm_tech_basic_params(
        self,
        mock_optional_str,
        mock_mandatory_str,
        mock_check_type,
        mock_get_subnode,
        mock_mandatory_yeardep,
        stages,
        ecs,
        techs,
        ebm_techs,
        stage_id,
    ):
        """Should parse basic EBM tech parameters"""
        mock_optional_str.return_value = "ebm"
        mock_mandatory_str.side_effect = ["test_ebm", "electricity"]
        mock_mandatory_yeardep.return_value = {
            stage_id: Value(100.0, PowerUnit.KW * TimeUnit.H)
        }

        tech_node = MagicMock()
        ebm_params_node = MagicMock()
        mock_get_subnode.return_value = ebm_params_node
        ebm_params_node.__getitem__.return_value = None

        ebm_tech_parser._parse_ebm_tech_primary(
            tech_node, stages, ecs, techs, ebm_techs
        )

        assert TechId("test_ebm") in ebm_techs.ids
        techs.set_cap_unit.assert_called_once()

    @patch("ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_mandatory_yeardep_value_from_dict_node")
    @patch("ehubx.parser.yaml_parser.get_mandatory_subnode_from_dict_node")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    @patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    def test_ebm_tech_optional_params(
        self,
        mock_optional_str,
        mock_mandatory_str,
        mock_check_type,
        mock_get_subnode,
        mock_mandatory_yeardep,
        mock_optional_yeardep,
        stages,
        ecs,
        techs,
        ebm_techs,
        stage_id,
    ):
        """Should parse optional EBM tech parameters"""
        mock_optional_str.return_value = "ebm"
        mock_mandatory_str.side_effect = ["test_ebm", "electricity"]
        mock_mandatory_yeardep.return_value = {
            stage_id: Value(100.0, PowerUnit.KW * TimeUnit.H)
        }
        # Return correct unit types for each optional parameter
        mock_optional_yeardep.side_effect = [
            {stage_id: Value(0.9, DimlessUnit())},  # in_eff
            {stage_id: Value(0.9, DimlessUnit())},  # out_eff
            {stage_id: Value(0.01, DimlessUnit() / TimeUnit.H)},  # standby_loss
            {stage_id: Value(0.2, DimlessUnit())},  # soc_min
            {stage_id: Value(0.9, DimlessUnit())},  # soc_max
            {stage_id: Value(50.0, PowerUnit.KW)},  # charge_max
            {stage_id: Value(40.0, PowerUnit.KW)},  # discharge_max
            {stage_id: Value(1.0, DimlessUnit())},  # discharge_control
        ]

        tech_node = MagicMock()
        ebm_params_node = MagicMock()
        mock_get_subnode.return_value = ebm_params_node
        ebm_params_node.__getitem__.return_value = None

        ebm_tech_parser._parse_ebm_tech_primary(
            tech_node, stages, ecs, techs, ebm_techs
        )

        assert TechId("test_ebm") in ebm_techs.ids
        # Should be called for: in_eff, out_eff, standby_loss, soc_min, soc_max,
        # charge_max, discharge_max, discharge_control
        assert mock_optional_yeardep.call_count >= 8

    @patch("ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_mandatory_yeardep_value_from_dict_node")
    @patch("ehubx.parser.yaml_parser.get_mandatory_subnode_from_dict_node")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    @patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    def test_ebm_tech_all_optional_params_none(
        self,
        mock_optional_str,
        mock_mandatory_str,
        mock_check_type,
        mock_get_subnode,
        mock_mandatory_yeardep,
        mock_optional_yeardep,
        stages,
        ecs,
        techs,
        ebm_techs,
        stage_id,
    ):
        """Should handle all optional parameters being None"""
        mock_optional_str.return_value = "ebm"
        mock_mandatory_str.side_effect = ["test_ebm", "electricity"]
        mock_mandatory_yeardep.return_value = {
            stage_id: Value(100.0, PowerUnit.KW * TimeUnit.H)
        }
        mock_optional_yeardep.return_value = None

        tech_node = MagicMock()
        ebm_params_node = MagicMock()
        mock_get_subnode.return_value = ebm_params_node
        ebm_params_node.__getitem__.return_value = None

        ebm_tech_parser._parse_ebm_tech_primary(
            tech_node, stages, ecs, techs, ebm_techs
        )

        assert TechId("test_ebm") in ebm_techs.ids


# ============================================================================
# TEST: parse_secondary
# ============================================================================


class TestParseSecondary:
    """Tests for parse_secondary function"""

    @patch("ehubx.parser.ebm_tech_parser._parse_hub_secondary")
    def test_none_root_node(self, mock_parse_hub, stages, ecs, ebm_techs):
        """Should return early when root node is None"""
        ebm_tech_parser.parse_secondary(None, stages, ecs, ebm_techs)

        mock_parse_hub.assert_not_called()
        # Should not raise

    @patch("ehubx.parser.ebm_tech_parser._parse_hub_secondary")
    def test_none_hubs_node(self, mock_parse_hub, stages, ecs, ebm_techs):
        """Should return early when hubs node is None"""
        root = MagicMock()
        root.__getitem__.return_value = None
        ebm_tech_parser.parse_secondary(root, stages, ecs, ebm_techs)

        mock_parse_hub.assert_not_called()
        # Should not raise

    @patch("ehubx.parser.ebm_tech_parser._parse_hub_secondary")
    def test_with_valid_hubs(self, mock_parse_hub, stages, ecs, ebm_techs):
        """Should parse hubs when valid nodes exist"""
        hub_node = MagicMock()
        hubs_node = MagicMock()
        hubs_node.__iter__ = MagicMock(return_value=iter([hub_node]))
        root = MagicMock()
        root.__getitem__.return_value = hubs_node

        ebm_tech_parser.parse_secondary(root, stages, ecs, ebm_techs)

        mock_parse_hub.assert_called_once()


# ============================================================================
# TEST: _parse_hub_secondary
# ============================================================================


class TestParseHubSecondary:
    """Tests for _parse_hub_secondary function"""

    @patch("ehubx.parser.ebm_tech_parser._parse_tech_secondary")
    @patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
    def test_none_techs_node(self, mock_mandatory, mock_parse_tech, stages, ecs, ebm_techs):
        """Should return early when techs node is None"""
        mock_mandatory.return_value = "hub1"
        hub_node = MagicMock()
        hub_node.__getitem__.return_value = None

        ebm_tech_parser._parse_hub_secondary(hub_node, stages, ecs, ebm_techs)
        # Should not raise
        mock_parse_tech.assert_not_called()

    @patch("ehubx.parser.ebm_tech_parser._parse_tech_secondary")
    @patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
    def test_with_valid_tech(
        self, mock_mandatory, mock_parse_tech, stages, ecs, ebm_techs_with_id, tech_id
    ):
        """Should parse tech when valid nodes exist"""
        mock_mandatory.return_value = "hub1"

        tech_node = MagicMock()
        techs_node = MagicMock()
        techs_node.__getitem__.return_value = tech_node

        hub_node = MagicMock()
        hub_node.__getitem__.return_value = techs_node

        ebm_tech_parser._parse_hub_secondary(hub_node, stages, ecs, ebm_techs_with_id)

        mock_parse_tech.assert_called_once()

    @patch("ehubx.parser.ebm_tech_parser._parse_tech_secondary")
    @patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
    def test_tech_not_in_ebm_techs(self, mock_mandatory, mock_parse_tech, stages, ecs, ebm_techs):
        """Should skip techs not in ebm_techs.ids"""
        mock_mandatory.return_value = "hub1"

        tech_node = MagicMock()
        techs_node = MagicMock()
        techs_node.__getitem__.return_value = None

        hub_node = MagicMock()
        hub_node.__getitem__.return_value = techs_node

        ebm_tech_parser._parse_hub_secondary(hub_node, stages, ecs, ebm_techs)
        # Should not raise
        mock_parse_tech.assert_not_called()


# ============================================================================
# TEST: _parse_tech_secondary
# ============================================================================


class TestParseTechSecondary:
    """Tests for _parse_tech_secondary function"""

    @patch("ehubx.parser.yaml_parser.check_node_type")
    def test_none_ebm_params_node(
        self, mock_check_type, hub_id, tech_id, stages, ecs, ebm_techs_with_id
    ):
        """Should return early when ebm_params node is None"""
        tech_node = MagicMock()
        tech_node.__getitem__.return_value = None

        ebm_tech_parser._parse_tech_secondary(
            tech_node, hub_id, tech_id, stages, ecs, ebm_techs_with_id
        )
        # Should not raise
        mock_check_type.assert_not_called()

    @patch("ehubx.parser.ebm_tech_parser._parse_tech_secondary_profiles")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    def test_with_ebm_params(
        self,
        mock_check_type,
        mock_parse_profiles,
        hub_id,
        tech_id,
        stages,
        ecs,
        ebm_techs_with_id,
    ):
        """Should parse ebm_params when present"""
        ebm_params_node = MagicMock()
        ebm_params_node.__getitem__.return_value = None

        tech_node = MagicMock()
        tech_node.__getitem__.return_value = ebm_params_node

        ebm_tech_parser._parse_tech_secondary(
            tech_node, hub_id, tech_id, stages, ecs, ebm_techs_with_id
        )

        # check_node_type is called multiple times during parsing
        assert mock_check_type.call_count >= 1
        mock_parse_profiles.assert_called_once()

    @patch("ehubx.parser.ebm_tech_parser._parse_tech_secondary_profiles")
    @patch("ehubx.parser.yaml_parser.parse_optional_yeardep_float_from_dict_node")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    def test_with_num_vehicles(
        self,
        mock_check_type,
        mock_optional_float,
        mock_parse_profiles,
        hub_id,
        tech_id,
        stages,
        ecs,
        ebm_techs_with_id,
        stage_id,
    ):
        """Should parse num_vehicles when present and set it in ebm_techs"""
        mock_optional_float.return_value = {stage_id: 5.0}

        ebm_params_node = MagicMock()
        ebm_params_node.__getitem__.return_value = None

        tech_node = MagicMock()
        tech_node.__getitem__.return_value = ebm_params_node

        # Should not raise an exception
        ebm_tech_parser._parse_tech_secondary(
            tech_node, hub_id, tech_id, stages, ecs, ebm_techs_with_id
        )

        # Verify the data was actually set
        assert ebm_techs_with_id.get_num_vehicles(stage_id, hub_id, tech_id) == 5.0

    @patch("ehubx.parser.ebm_tech_parser._parse_tech_secondary_profiles")
    @patch("ehubx.parser.yaml_parser.parse_optional_value_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_optional_yeardep_float_from_dict_node")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    def test_with_soc_init(
        self,
        mock_check_type,
        mock_optional_float,
        mock_optional_value,
        mock_parse_profiles,
        hub_id,
        tech_id,
        stages,
        ecs,
        ebm_techs_with_id,
    ):
        """Should parse soc_init when present and set it in ebm_techs"""
        mock_optional_float.return_value = None
        expected_soc_init = Value(0.5, DimlessUnit())
        mock_optional_value.return_value = expected_soc_init

        ebm_params_node = MagicMock()
        ebm_params_node.__getitem__.return_value = None

        tech_node = MagicMock()
        tech_node.__getitem__.return_value = ebm_params_node

        # Should not raise an exception
        ebm_tech_parser._parse_tech_secondary(
            tech_node, hub_id, tech_id, stages, ecs, ebm_techs_with_id
        )

        # Verify the data was actually set
        assert ebm_techs_with_id.get_soc_init(hub_id, tech_id) == expected_soc_init

    @patch("ehubx.parser.ebm_tech_parser._parse_tech_secondary_profiles")
    @patch("ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_optional_value_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_optional_yeardep_float_from_dict_node")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    def test_with_demand_modifier(
        self,
        mock_check_type,
        mock_optional_float,
        mock_optional_value,
        mock_optional_yeardep_value,
        mock_parse_profiles,
        hub_id,
        tech_id,
        stages,
        ecs,
        ebm_techs_with_id,
        stage_id,
    ):
        """Should parse demand_modifier when present and set it in ebm_techs"""
        mock_optional_float.return_value = None
        mock_optional_value.return_value = None
        expected_modifier = Value(1.1, DimlessUnit())
        mock_optional_yeardep_value.side_effect = [
            {stage_id: expected_modifier},  # demand_modifier
            None,  # demand_nominal
            None,  # availability
        ]

        ebm_params_node = MagicMock()
        ebm_params_node.__getitem__.return_value = None

        tech_node = MagicMock()
        tech_node.__getitem__.return_value = ebm_params_node

        # Should not raise an exception
        ebm_tech_parser._parse_tech_secondary(
            tech_node, hub_id, tech_id, stages, ecs, ebm_techs_with_id
        )

        # Verify the data was actually set
        assert ebm_techs_with_id.get_demand_modifier(stage_id, hub_id, tech_id) == expected_modifier

    @patch("ehubx.parser.ebm_tech_parser._parse_tech_secondary_profiles")
    @patch("ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_optional_value_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_optional_yeardep_float_from_dict_node")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    def test_with_demand_nominal_and_availability(
        self,
        mock_check_type,
        mock_optional_float,
        mock_optional_value,
        mock_optional_yeardep_value,
        mock_parse_profiles,
        hub_id,
        tech_id,
        stages,
        ecs,
        ebm_techs_with_id,
        stage_id,
    ):
        """Should parse demand_nominal and availability when present and set them in ebm_techs"""
        mock_optional_float.return_value = None
        mock_optional_value.return_value = None

        expected_demand_nominal = Value(50.0, PowerUnit.KW)
        expected_availability = Value(0.8, DimlessUnit())

        def yeardep_value_side_effect(node, key, stages, expected_unit):
            if key == ebm_tech_parser.YAMLKEY_DEMANDNOMINAL:
                return {stage_id: expected_demand_nominal}
            elif key == ebm_tech_parser.YAMLKEY_AVAILABILITY:
                return {stage_id: expected_availability}
            return None

        mock_optional_yeardep_value.side_effect = yeardep_value_side_effect

        ebm_params_node = MagicMock()
        ebm_params_node.__getitem__.return_value = None

        tech_node = MagicMock()
        tech_node.__getitem__.return_value = ebm_params_node

        # Should not raise an exception
        ebm_tech_parser._parse_tech_secondary(
            tech_node, hub_id, tech_id, stages, ecs, ebm_techs_with_id
        )

        # Verify the data was actually set (using def_value since no time-dependent profiles)
        assert ebm_techs_with_id.get_demand_nominal(stage_id, hub_id, tech_id).def_value == expected_demand_nominal
        assert ebm_techs_with_id.get_availability(stage_id, hub_id, tech_id).def_value == expected_availability


# ============================================================================
# TEST: _parse_tech_secondary_profiles
# ============================================================================


class TestParseTechSecondaryProfiles:
    """Tests for _parse_tech_secondary_profiles function"""
    @patch("ehubx.parser.yaml_parser.check_file_exists")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node", return_value=None)
    def test_none_profile_path(self, mock_parse_str, mock_check_file, hub_id, tech_id, ecs, ebm_techs_with_id, ec_id):
        """Should return early when profile_path is None"""
        ebm_params_node = MagicMock()
        ebm_params_node.__getitem__.return_value = None

        ebm_tech_parser._parse_tech_secondary_profiles(
            ebm_params_node, hub_id, tech_id, ecs.get_unit(ec_id), ebm_techs_with_id
        )
        # Should not raise
        mock_check_file.assert_not_called()

    @patch("ehubx.data.ebm_tech_data.EbmTechs.set_demand_nominal")
    @patch("ehubx.parser.csv_parser.parse")
    @patch("ehubx.parser.yaml_parser.check_file_exists")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    def test_with_valid_profile_demand_nominal(
        self,
        mock_parse_str,
        mock_check_file,
        mock_csv_parse,
        mock_set_demand_nominal,
        hub_id,
        tech_id,
        ec_id,
        ebm_techs_with_id,
        stage_id,
    ):
        """Should parse demand_nominal profile correctly"""
        mock_parse_str.return_value = "profiles.csv"

        ebm_params_node = MagicMock()
        ebm_params_node.file_path = "/test/path/config.yaml"

        # Create mock DataFrame
        columns = pd.MultiIndex.from_tuples(
            [(stage_id.key, hub_id.key, tech_id.key, "demand_nominal")]
        )
        data = {(stage_id.key, hub_id.key, tech_id.key, "demand_nominal"): [10.0, 20.0]}
        df = pd.DataFrame(data, columns=columns, index=["t1", "t2"])
        df.attrs = {
            csv_parser.ATTR_UNIT: {
                (stage_id.key, hub_id.key, tech_id.key, "demand_nominal"): "kWh/h"
            }
        }
        mock_csv_parse.return_value = df

        ebm_tech_parser._parse_tech_secondary_profiles(
            ebm_params_node, hub_id, tech_id, PowerUnit.KW * TimeUnit.H, ebm_techs_with_id
        )

        mock_check_file.assert_called_once()
        mock_csv_parse.assert_called_once()
        assert mock_set_demand_nominal.call_count == 2

    @patch("ehubx.data.ebm_tech_data.EbmTechs.set_availability")
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
        ec_id,
        ebm_techs_with_id,
        stage_id,
    ):
        """Should parse availability profile correctly"""
        mock_parse_str.return_value = "profiles.csv"

        ebm_params_node = MagicMock()
        ebm_params_node.file_path = "/test/path/config.yaml"

        # Create mock DataFrame with empty string for dimensionless unit
        columns = pd.MultiIndex.from_tuples(
            [(stage_id.key, hub_id.key, tech_id.key, "availability")]
        )
        data = {(stage_id.key, hub_id.key, tech_id.key, "availability"): [0.8, 0.9]}
        df = pd.DataFrame(data, columns=columns, index=["t1", "t2"])
        df.attrs = {
            csv_parser.ATTR_UNIT: {
                (stage_id.key, hub_id.key, tech_id.key, "availability"): ""
            }
        }
        mock_csv_parse.return_value = df

        ebm_tech_parser._parse_tech_secondary_profiles(
            ebm_params_node, hub_id, tech_id, PowerUnit.KW * TimeUnit.H, ebm_techs_with_id
        )

        mock_check_file.assert_called_once()
        mock_csv_parse.assert_called_once()
        assert mock_set_availability.call_count == 2

    @patch("ehubx.data.ebm_tech_data.EbmTechs.set_demand_nominal")
    @patch("ehubx.parser.csv_parser.parse")
    @patch("ehubx.parser.yaml_parser.check_file_exists")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    def test_profile_skips_different_hub(
        self,
        mock_parse_str,
        mock_check_file,
        mock_csv_parse,
        mock_set_demand_nominal,
        hub_id,
        tech_id,
        ec_id,
        ebm_techs_with_id,
        stage_id,
    ):
        """Should skip profiles for different hub"""
        mock_parse_str.return_value = "profiles.csv"

        ebm_params_node = MagicMock()
        ebm_params_node.file_path = "/test/path/config.yaml"

        # Create mock DataFrame with different hub
        columns = pd.MultiIndex.from_tuples(
            [(stage_id.key, "different_hub", tech_id.key, "demand_nominal")]
        )
        data = {
            (stage_id.key, "different_hub", tech_id.key, "demand_nominal"): [10.0, 20.0]
        }
        df = pd.DataFrame(data, columns=columns, index=["t1", "t2"])
        df.attrs = {
            csv_parser.ATTR_UNIT: {
                (stage_id.key, "different_hub", tech_id.key, "demand_nominal"): "kW"
            }
        }
        mock_csv_parse.return_value = df

        ebm_tech_parser._parse_tech_secondary_profiles(
            ebm_params_node, hub_id, tech_id, PowerUnit.KW * TimeUnit.H, ebm_techs_with_id
        )

        # Should not raise - just skip this profile
        mock_check_file.assert_called_once()
        mock_set_demand_nominal.assert_not_called()

    @patch("ehubx.data.ebm_tech_data.EbmTechs.set_demand_nominal")
    @patch("ehubx.parser.csv_parser.parse")
    @patch("ehubx.parser.yaml_parser.check_file_exists")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    def test_profile_skips_different_tech(
        self,
        mock_parse_str,
        mock_check_file,
        mock_csv_parse,
        mock_set_demand_nominal,
        hub_id,
        tech_id,
        ec_id,
        ebm_techs_with_id,
        stage_id,
    ):
        """Should skip profiles for different tech"""
        mock_parse_str.return_value = "profiles.csv"

        ebm_params_node = MagicMock()
        ebm_params_node.file_path = "/test/path/config.yaml"

        # Create mock DataFrame with different tech
        columns = pd.MultiIndex.from_tuples(
            [(stage_id.key, hub_id.key, "different_tech", "demand_nominal")]
        )
        data = {
            (stage_id.key, hub_id.key, "different_tech", "demand_nominal"): [10.0, 20.0]
        }
        df = pd.DataFrame(data, columns=columns, index=["t1", "t2"])
        df.attrs = {
            csv_parser.ATTR_UNIT: {
                (stage_id.key, hub_id.key, "different_tech", "demand_nominal"): "kW"
            }
        }
        mock_csv_parse.return_value = df

        ebm_tech_parser._parse_tech_secondary_profiles(
            ebm_params_node, hub_id, tech_id, PowerUnit.KW * TimeUnit.H, ebm_techs_with_id
        )

        # Should not raise - just skip this profile
        mock_check_file.assert_called_once()
        mock_set_demand_nominal.assert_not_called()

    @patch("ehubx.data.ebm_tech_data.EbmTechs.set_demand_nominal")
    @patch("ehubx.data.ebm_tech_data.EbmTechs.set_availability")
    @patch("ehubx.parser.csv_parser.parse")
    @patch("ehubx.parser.yaml_parser.check_file_exists")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    def test_profile_unknown_key_ignored(
        self,
        mock_parse_str,
        mock_check_file,
        mock_csv_parse,
        mock_set_availability,
        mock_set_demand_nominal,
        hub_id,
        tech_id,
        ec_id,
        ebm_techs_with_id,
        stage_id,
    ):
        """Should ignore profiles with unknown keys"""
        mock_parse_str.return_value = "profiles.csv"

        ebm_params_node = MagicMock()
        ebm_params_node.file_path = "/test/path/config.yaml"

        # Create mock DataFrame with unknown key
        columns = pd.MultiIndex.from_tuples(
            [(stage_id.key, hub_id.key, tech_id.key, "unknown_key")]
        )
        data = {(stage_id.key, hub_id.key, tech_id.key, "unknown_key"): [10.0, 20.0]}
        df = pd.DataFrame(data, columns=columns, index=["t1", "t2"])
        df.attrs = {
            csv_parser.ATTR_UNIT: {
                (stage_id.key, hub_id.key, tech_id.key, "unknown_key"): "kWh/h"
            }
        }
        mock_csv_parse.return_value = df

        # Should not raise
        ebm_tech_parser._parse_tech_secondary_profiles(
            ebm_params_node, hub_id, tech_id, PowerUnit.KW * TimeUnit.H, ebm_techs_with_id
        )
        mock_set_demand_nominal.assert_not_called()
        mock_set_availability.assert_not_called()


# ============================================================================
# TEST: Exception Handling
# ============================================================================


class TestExceptionHandling:
    """Tests for exception handling in ebm_tech_parser"""

    @patch("ehubx.parser.csv_parser.parse")
    @patch("ehubx.parser.yaml_parser.check_file_exists")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    def test_invalid_unit_in_profile(
        self,
        mock_parse_str,
        mock_check_file,
        mock_csv_parse,
        hub_id,
        tech_id,
        ec_id,
        ebm_techs_with_id,
        stage_id,
    ):
        """Should raise ParsingException for invalid unit in profile"""
        mock_parse_str.return_value = "profiles.csv"

        ebm_params_node = MagicMock()
        ebm_params_node.file_path = "/test/path/config.yaml"

        # Create mock DataFrame with invalid unit
        columns = pd.MultiIndex.from_tuples(
            [(stage_id.key, hub_id.key, tech_id.key, "demand_nominal")]
        )
        data = {(stage_id.key, hub_id.key, tech_id.key, "demand_nominal"): [10.0, 20.0]}
        df = pd.DataFrame(data, columns=columns, index=["t1", "t2"])
        df.attrs = {
            csv_parser.ATTR_UNIT: {
                (stage_id.key, hub_id.key, tech_id.key, "demand_nominal"): "invalid_unit"
            }
        }
        mock_csv_parse.return_value = df

        with pytest.raises(exceptions.ParsingException) as exc_info:
            ebm_tech_parser._parse_tech_secondary_profiles(
                ebm_params_node, hub_id, tech_id, PowerUnit.KW * TimeUnit.H, ebm_techs_with_id
            )

        assert "Invalid unit" in str(exc_info.value)
        assert "demand_nominal" in str(exc_info.value)

    @patch("ehubx.parser.csv_parser.parse")
    @patch("ehubx.parser.yaml_parser.check_file_exists")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    def test_unit_type_mismatch_demand_nominal(
        self,
        mock_parse_str,
        mock_check_file,
        mock_csv_parse,
        hub_id,
        tech_id,
        ec_id,
        ebm_techs_with_id,
        stage_id,
    ):
        """Should raise ParsingException for unit type mismatch in demand_nominal"""
        mock_parse_str.return_value = "profiles.csv"

        ebm_params_node = MagicMock()
        ebm_params_node.file_path = "/test/path/config.yaml"

        # Create mock DataFrame with wrong unit type (should be energy/time, not energy)
        columns = pd.MultiIndex.from_tuples(
            [(stage_id.key, hub_id.key, tech_id.key, "demand_nominal")]
        )
        data = {(stage_id.key, hub_id.key, tech_id.key, "demand_nominal"): [10.0, 20.0]}
        df = pd.DataFrame(data, columns=columns, index=["t1", "t2"])
        df.attrs = {
            csv_parser.ATTR_UNIT: {
                (stage_id.key, hub_id.key, tech_id.key, "demand_nominal"): "kWh"  # Wrong! Should be kWh/h
            }
        }
        mock_csv_parse.return_value = df

        with pytest.raises(exceptions.ParsingException) as exc_info:
            ebm_tech_parser._parse_tech_secondary_profiles(
                ebm_params_node, hub_id, tech_id, PowerUnit.KW * TimeUnit.H, ebm_techs_with_id
            )

        assert "Invalid unit" in str(exc_info.value)
        assert "demand_nominal" in str(exc_info.value)

    @patch("ehubx.parser.csv_parser.parse")
    @patch("ehubx.parser.yaml_parser.check_file_exists")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    def test_unit_type_mismatch_availability(
        self,
        mock_parse_str,
        mock_check_file,
        mock_csv_parse,
        hub_id,
        tech_id,
        ec_id,
        ebm_techs_with_id,
        stage_id,
    ):
        """Should raise ParsingException for unit type mismatch in availability"""
        mock_parse_str.return_value = "profiles.csv"

        ebm_params_node = MagicMock()
        ebm_params_node.file_path = "/test/path/config.yaml"

        # Create mock DataFrame with wrong unit type (should be dimensionless)
        columns = pd.MultiIndex.from_tuples(
            [(stage_id.key, hub_id.key, tech_id.key, "availability")]
        )
        data = {(stage_id.key, hub_id.key, tech_id.key, "availability"): [0.8, 0.9]}
        df = pd.DataFrame(data, columns=columns, index=["t1", "t2"])
        df.attrs = {
            csv_parser.ATTR_UNIT: {
                (stage_id.key, hub_id.key, tech_id.key, "availability"): "kWh"  # Wrong! Should be dimensionless
            }
        }
        mock_csv_parse.return_value = df

        with pytest.raises(exceptions.ParsingException) as exc_info:
            ebm_tech_parser._parse_tech_secondary_profiles(
                ebm_params_node, hub_id, tech_id, PowerUnit.KW * TimeUnit.H, ebm_techs_with_id
            )

        assert "Invalid unit" in str(exc_info.value)
        assert "availability" in str(exc_info.value)


# ============================================================================
# TEST: Integration Tests
# ============================================================================


class TestIntegration:
    """Integration tests for complete parsing flow"""

    @patch("ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_mandatory_yeardep_value_from_dict_node")
    @patch("ehubx.parser.yaml_parser.get_mandatory_subnode_from_dict_node")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    @patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    def test_complete_ebm_tech_parsing(
        self,
        mock_optional_str,
        mock_mandatory_str,
        mock_check_type,
        mock_get_subnode,
        mock_mandatory_yeardep,
        mock_optional_yeardep,
        stages,
        ecs,
        techs,
        stage_id,
    ):
        """Test complete parsing flow with all parameters"""
        mock_optional_str.return_value = "ebm"
        mock_mandatory_str.side_effect = ["ebm_complete", "electricity"]
        mock_mandatory_yeardep.return_value = {
            stage_id: Value(200.0, PowerUnit.KW * TimeUnit.H)
        }

        # Set up optional parameters
        optional_returns = [
            {stage_id: Value(0.95, DimlessUnit())},  # in_eff
            {stage_id: Value(0.90, DimlessUnit())},  # out_eff
            {stage_id: Value(0.01, DimlessUnit() / TimeUnit.H)},  # standby_loss
            {stage_id: Value(0.2, DimlessUnit())},  # soc_min
            {stage_id: Value(0.9, DimlessUnit())},  # soc_max
            {stage_id: Value(50.0, PowerUnit.KW)},  # charge_max
            {stage_id: Value(40.0, PowerUnit.KW)},  # discharge_max
            {stage_id: Value(1.0, DimlessUnit())},  # discharge_control
        ]
        mock_optional_yeardep.side_effect = optional_returns

        tech_node = MagicMock()
        ebm_params_node = MagicMock()
        mock_get_subnode.return_value = ebm_params_node
        ebm_params_node.__getitem__.return_value = None

        ebm_techs = EbmTechs()
        ebm_tech_parser._parse_ebm_tech_primary(
            tech_node, stages, ecs, techs, ebm_techs
        )

        tech_id = TechId("ebm_complete")
        assert tech_id in ebm_techs.ids
        # Verify that optional parameters were parsed (8 calls expected)
        assert mock_optional_yeardep.call_count == 8
