import pytest
from unittest.mock import MagicMock, patch
from typing import Callable

from ehubx.parser import conv_tech_parser, yaml_parser, exceptions
from ehubx.data.conv_tech_data import ConversionTechs
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.unit import PowerUnit, DimlessUnit
from ehubx.data.value import Value


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _setup_conv_tech_in(conversion_params_node, tech_id, stages, ecs, conv_techs):
    """Helper to set up tech input in conv_techs"""
    conv_techs.add_in_ec(tech_id, EcId("in_test"), PowerUnit.KW)
    conv_techs.set_in_ec_main(tech_id, EcId("in_test"))


def _setup_conv_tech_out(conversion_params_node, tech_id, stages, ecs, conv_techs):
    """Helper to set up tech output in conv_techs"""
    conv_techs.add_out_ec(tech_id, EcId("out_test"), PowerUnit.KW)
    conv_techs.set_out_ec_main(tech_id, EcId("out_test"))


def _mock_conv_tech_prep(conv_techs, tech_id):
    """Prepare conv_techs with basic tech setup"""
    conv_techs.add_id(tech_id)
    conv_techs.add_in_ec(tech_id, EcId("electricity"), PowerUnit.KW)
    conv_techs.set_in_ec_main(tech_id, EcId("electricity"))
    conv_techs.add_out_ec(tech_id, EcId("heat"), PowerUnit.KW)
    conv_techs.set_out_ec_main(tech_id, EcId("heat"))


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
    mock_ecs.get_unit.return_value = PowerUnit.KW
    return mock_ecs


@pytest.fixture
def techs():
    """Mock Techs object"""
    return MagicMock(spec=Techs)


@pytest.fixture
def conv_techs():
    """ConversionTechs instance"""
    return ConversionTechs()


@pytest.fixture
def hub_id():
    """Sample hub ID"""
    return HubId("hub_test")


@pytest.fixture
def tech_id():
    """Sample tech ID"""
    return TechId("conv_tech_test")


@pytest.fixture
def ec_id_in():
    """Sample input EC ID"""
    return EcId("electricity")


@pytest.fixture
def ec_id_out():
    """Sample output EC ID"""
    return EcId("heat")


@pytest.fixture
def stage_id():
    """Sample stage ID"""
    return StageId("2025")


# ============================================================================
# TEST: preprocess_in_ec_groups
# ============================================================================


class TestPreprocessInEcGroups:
    """Tests for preprocess_in_ec_groups function"""

    def test_none_ec_root_node(self, techs):
        """Should return early if ec_root_node is None"""
        conv_tech_parser.preprocess_in_ec_groups(None, None, techs)
        techs.assert_not_called()
        # Should not raise and not modify techs

    def test_none_tech_root_node(self, techs):
        """Should return early if tech_root_node is None"""
        ec_root = MagicMock()
        ec_root.__getitem__.return_value = None

        conv_tech_parser.preprocess_in_ec_groups(None, ec_root, techs)
        techs.assert_not_called()
        # Should not raise

    def test_no_in_ec_groups(self, techs):
        """Should handle case where no in_ec_groups exist"""
        ec_root = MagicMock()
        ec_root.__getitem__.return_value = None
        tech_root = MagicMock()
        techs_node = MagicMock()
        techs_node.__iter__ = MagicMock(return_value=iter([]))
        techs_node.update_node_path = MagicMock()
        tech_root.__getitem__.return_value = techs_node

        conv_tech_parser.preprocess_in_ec_groups(tech_root, ec_root, techs)
        techs.assert_not_called()
        # Should not raise

    @patch("ehubx.parser.conv_tech_parser._parse_in_ec_groups")
    def test_with_valid_in_ec_groups(self, mock_parse_groups, techs):
        """Should parse and extend conversion techs based on ec groups"""
        mock_parse_groups.return_value = {"group1": {EcId("ec1"), EcId("ec2")}}

        # Create mock YAML nodes
        ec_root = MagicMock()
        ec_root.__getitem__.return_value = None

        tech_root = MagicMock()
        techs_node = MagicMock()
        tech_root.__getitem__.return_value = techs_node
        techs_node.__iter__ = MagicMock(return_value=iter([]))

        conv_tech_parser.preprocess_in_ec_groups(tech_root, ec_root, techs)
        mock_parse_groups.assert_called_once()


# ============================================================================
# TEST: _parse_in_ec_groups
# ============================================================================


class TestParseInEcGroups:
    """Tests for _parse_in_ec_groups function"""

    def test_no_in_ec_groups_node(self):
        """Should return empty dict when in_ec_groups node is None"""
        root = MagicMock()
        root.__getitem__.return_value = None

        result = conv_tech_parser._parse_in_ec_groups(root)

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_empty_in_ec_groups(self):
        """Should return empty dict for empty in_ec_groups"""
        root = MagicMock(spec=yaml_parser.YamlNode)
        root.file_path = "test.yaml"
        groups_node = MagicMock(spec=yaml_parser.YamlListNode)
        groups_node.__len__ = MagicMock(return_value=0)
        groups_node.__iter__ = MagicMock(return_value=iter([]))
        root.__getitem__.return_value = groups_node

        result = conv_tech_parser._parse_in_ec_groups(root)

        assert isinstance(result, dict)
        assert len(result) == 0

    @patch("ehubx.parser.yaml_parser.parse_str_list_from_dict_node")
    @patch("ehubx.parser.yaml_parser.get_mandatory_subnode_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    def test_parse_single_group(
        self, mock_check_type, mock_parse_str, mock_get_subnode, mock_parse_list
    ):
        """Should parse a single in_ec_group correctly"""
        root = MagicMock(spec=yaml_parser.YamlNode)
        root.file_path = "test.yaml"
        groups_node = MagicMock(spec=yaml_parser.YamlListNode)

        group_node = MagicMock(spec=yaml_parser.YamlDictNode)
        ecs_node = MagicMock(spec=yaml_parser.YamlListNode)
        ecs_node.__len__ = MagicMock(return_value=1)  # Not empty!

        groups_node.__len__ = MagicMock(return_value=1)
        groups_node.__iter__ = MagicMock(return_value=iter([group_node]))
        root.__getitem__.return_value = groups_node

        mock_parse_str.return_value = "group_id_1"
        mock_get_subnode.return_value = ecs_node
        mock_parse_list.return_value = ["ec1", "ec2"]

        result = conv_tech_parser._parse_in_ec_groups(root)

        assert "group_id_1" in result
        assert EcId("ec1") in result["group_id_1"]
        assert EcId("ec2") in result["group_id_1"]

    @patch("ehubx.parser.yaml_parser.get_mandatory_subnode_from_dict_node")
    def test_raises_on_empty_ecs_list(self, mock_get_subnode):
        """Should raise EmptyListNodeException for empty ecs list"""
        root = MagicMock(spec=yaml_parser.YamlNode)
        root.file_path = "test.yaml"
        groups_node = MagicMock(spec=yaml_parser.YamlListNode)

        group_node = MagicMock(spec=yaml_parser.YamlDictNode)
        ecs_node = MagicMock(spec=yaml_parser.YamlListNode)
        ecs_node.node_path_as_str = "in_ec_groups[0].ecs"
        ecs_node.__len__ = MagicMock(return_value=0)  # Empty!

        groups_node.__len__ = MagicMock(return_value=1)
        groups_node.__iter__ = MagicMock(return_value=iter([group_node]))
        root.__getitem__.return_value = groups_node

        with patch(
            "ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node",
            return_value="group1",
        ):
            with patch("ehubx.parser.yaml_parser.check_node_type"):
                mock_get_subnode.return_value = ecs_node

                with pytest.raises(exceptions.EmptyListNodeException):
                    conv_tech_parser._parse_in_ec_groups(root)


# ============================================================================
# TEST: _extend_in_ecs
# ============================================================================


class TestExtendInEcs:
    """Tests for _extend_in_ecs function"""

    def test_empty_in_ecs_list(self):
        """Should return empty list for empty in_ecs"""
        in_ecs_node = MagicMock()
        in_ecs_node.__len__ = MagicMock(return_value=0)
        in_ec_groups = {}

        result = conv_tech_parser._extend_in_ecs(in_ecs_node, in_ec_groups)

        assert result == []

    @patch("ehubx.parser.conv_tech_parser._extend_in_ecs", wraps=conv_tech_parser._extend_in_ecs)
    def test_no_extension_needed(self, mock_extend):
        """Should return unchanged structure when no extension needed"""
        # Create a properly structured mock for in_ecs with 1 item (minimal case)
        in_ec_node = MagicMock(spec=yaml_parser.YamlDictNode)
        in_id_node = MagicMock(spec=yaml_parser.YamlValueNode)
        in_id_node.value = "ec_id_1"  # Not a group
        in_ec_node.__getitem__ = MagicMock(return_value=in_id_node)

        in_ecs_node = MagicMock(spec=yaml_parser.YamlListNode)
        in_ecs_node.__len__ = MagicMock(return_value=1)
        in_ecs_node.__getitem__ = MagicMock(return_value=in_ec_node)
        in_ecs_node.ids = set()
        in_ecs_node.copy = MagicMock(return_value=MagicMock(spec=yaml_parser.YamlListNode))
        in_ecs_node.remove_list_child = MagicMock()
        in_ecs_node.add_list_child = MagicMock()
        in_ec_node.copy = MagicMock(return_value=in_ec_node)
        in_id_node.set_value = MagicMock()

        in_ec_groups = {}

        result = conv_tech_parser._extend_in_ecs(in_ecs_node, in_ec_groups)

        # Result should contain extensions, each is tuple of (node, suffixes)
        assert isinstance(result, list)
        assert all(isinstance(item, tuple) and len(item) == 2 for item in result)


# ============================================================================
# TEST: parse_primary
# ============================================================================


class TestParsePrimary:
    """Tests for parse_primary function"""

    def test_none_root_node(self, stages, ecs, techs):
        """Should return empty ConversionTechs when root_node is None"""
        result = conv_tech_parser.parse_primary(None, stages, ecs, techs)

        assert isinstance(result, ConversionTechs)
        assert len(result.ids) == 0

    def test_none_techs_node(self, stages, ecs, techs):
        """Should return empty ConversionTechs when techs_node is None"""
        root = MagicMock()
        root.__getitem__.return_value = None

        result = conv_tech_parser.parse_primary(root, stages, ecs, techs)

        assert isinstance(result, ConversionTechs)
        assert len(result.ids) == 0

    @patch("ehubx.parser.conv_tech_parser._parse_conv_tech_primary")
    @patch("ehubx.parser.conv_tech_parser._log")
    def test_with_conversion_techs(
        self, mock_log, mock_parse_tech, stages, ecs, techs
    ):
        """Should parse conversion techs correctly"""
        root = MagicMock()
        tech_node = MagicMock()
        techs_node = MagicMock()
        techs_node.__iter__ = MagicMock(return_value=iter([tech_node]))
        root.__getitem__.return_value = techs_node

        result = conv_tech_parser.parse_primary(root, stages, ecs, techs)

        assert isinstance(result, ConversionTechs)
        mock_parse_tech.assert_called_once_with(tech_node, stages, ecs, techs, result)
        mock_log.assert_called_once_with(result)


# ============================================================================
# TEST: _parse_conv_tech_primary
# ============================================================================


class TestParseConvTechPrimary:
    """Tests for _parse_conv_tech_primary function"""

    @pytest.mark.parametrize("tech_type", ["storage", "demand"])
    def test_non_conversion_tech_types(self, tech_type, stages, ecs, techs, conv_techs):
        """Should skip non-conversion/non-solar tech types"""
        tech_node = MagicMock()

        with patch(
            "ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node",
            return_value="tech_test",
        ):
            with patch(
                "ehubx.parser.yaml_parser.parse_optional_str_from_dict_node",
                return_value=tech_type,
            ):
                conv_tech_parser._parse_conv_tech_primary(
                    tech_node, stages, ecs, techs, conv_techs
                )

        assert TechId("tech_test") not in conv_techs.ids

    @patch("ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node")
    @patch("ehubx.parser.conv_tech_parser._parse_out_ecs")
    @patch("ehubx.parser.conv_tech_parser._parse_in_ecs")
    @patch("ehubx.parser.yaml_parser.get_mandatory_subnode_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node", return_value="conversion")
    @patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node", return_value="conv_tech_1")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    def test_conversion_tech_primary(
        self, mock_check, mock_tech_id, mock_type, mock_get_subnode, mock_parse_in, mock_parse_out, mock_parse_opt, stages, ecs, techs, conv_techs
    ):
        """Should parse conversion tech with conversion type"""
        tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
        tech_node.file_path = "test.yaml"
        conversion_params_node = MagicMock(spec=yaml_parser.YamlDictNode)
        tech_node.__getitem__ = MagicMock(return_value=None)

        ecs.get_unit.return_value = PowerUnit.KW
        mock_get_subnode.return_value = conversion_params_node
        mock_parse_opt.return_value = None  # No opex_per_energy

        mock_parse_in.side_effect = _setup_conv_tech_in
        mock_parse_out.side_effect = _setup_conv_tech_out

        conv_tech_parser._parse_conv_tech_primary(
            tech_node, stages, ecs, techs, conv_techs
        )

        assert TechId("conv_tech_1") in conv_techs.ids
        mock_parse_in.assert_called_once()
        mock_parse_out.assert_called_once()

    @patch("ehubx.parser.conv_tech_parser._parse_out_ecs")
    @patch("ehubx.parser.conv_tech_parser._parse_in_ecs")
    @patch("ehubx.parser.yaml_parser.get_mandatory_subnode_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node", return_value="solar")
    @patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node", return_value="solar_1")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    def test_solar_tech_primary(
        self, mock_check, mock_tech_id, mock_type, mock_get_subnode, mock_parse_in, mock_parse_out, stages, ecs, techs, conv_techs
    ):
        """Should parse solar tech with solar type"""
        tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
        tech_node.file_path = "test.yaml"
        conversion_params_node = MagicMock(spec=yaml_parser.YamlDictNode)
        tech_node.__getitem__ = MagicMock(return_value=None)

        mock_get_subnode.return_value = conversion_params_node
        ecs.get_unit.return_value = PowerUnit.KW

        mock_parse_in.side_effect = _setup_conv_tech_in
        mock_parse_out.side_effect = _setup_conv_tech_out

        conv_tech_parser._parse_conv_tech_primary(
            tech_node, stages, ecs, techs, conv_techs
        )

        assert TechId("solar_1") in conv_techs.ids


# ============================================================================
# TEST: _parse_in_ecs
# ============================================================================


class TestParseInEcs:
    """Tests for _parse_in_ecs function"""

    @patch("ehubx.parser.yaml_parser.get_mandatory_subnode_from_dict_node")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    def test_empty_in_ecs(
        self, mock_check, mock_get, stages, conv_techs, tech_id
    ):
        """Should handle empty in_ecs list"""
        mock_ecs = MagicMock(spec=Ecs)
        conversion_params_node = MagicMock(spec=yaml_parser.YamlDictNode)
        in_ecs_node = MagicMock(spec=yaml_parser.YamlListNode)
        in_ecs_node.__len__ = MagicMock(return_value=0)
        in_ecs_node.__iter__ = MagicMock(return_value=iter([]))
        in_ecs_node.set_id = MagicMock()

        mock_get.return_value = in_ecs_node

        # Parse with optional main_in_ec that returns None
        with patch(
            "ehubx.parser.yaml_parser.parse_optional_str_from_dict_node",
            return_value=None,
        ):
            conv_tech_parser._parse_in_ecs(
                conversion_params_node, tech_id, stages, mock_ecs, conv_techs
            )

        # Should complete without raising

    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_mandatory_yeardep_value_from_dict_node")
    @patch("ehubx.parser.yaml_parser.get_mandatory_subnode_from_dict_node")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    def test_parse_in_ecs_with_values(
        self, mock_check, mock_get, mock_parse_val, mock_parse_opt, stages, conv_techs, tech_id, ec_id_in, stage_id
    ):
        """Should parse in_ecs with values correctly"""
        mock_ecs = MagicMock(spec=Ecs)
        mock_ecs.get_unit.return_value = PowerUnit.KW

        conversion_params_node = MagicMock()
        in_ecs_node = MagicMock()
        in_ec_node = MagicMock()

        in_ec_node.__getitem__ = MagicMock()
        mock_val_node = MagicMock()
        mock_val_node.value = "electricity"
        in_ec_node.__getitem__.return_value = mock_val_node

        in_ecs_node.__len__ = MagicMock(return_value=1)
        in_ecs_node.__iter__ = MagicMock(return_value=iter([in_ec_node]))

        mock_get.return_value = in_ecs_node
        mock_parse_val.return_value = {stage_id: Value(0.5, PowerUnit.KW)}
        mock_parse_opt.return_value = None

        with patch(
            "ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node",
            return_value="electricity",
        ):
            conv_techs.add_id(tech_id)
            conv_tech_parser._parse_in_ecs(
                conversion_params_node, tech_id, stages, mock_ecs, conv_techs
            )

        assert mock_parse_val.called


# ============================================================================
# TEST: _parse_out_ecs
# ============================================================================


class TestParseOutEcs:
    """Tests for _parse_out_ecs function"""

    @patch("ehubx.parser.conv_tech_parser._parse_out_eff")
    @patch("ehubx.parser.yaml_parser.get_mandatory_subnode_from_dict_node")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    def test_parse_single_out_ec(
        self, mock_check, mock_get, mock_parse_eff, stages, conv_techs, tech_id, ec_id_out, stage_id
    ):
        """Should parse output EC correctly"""
        mock_ecs = MagicMock(spec=Ecs)
        mock_ecs.get_unit.return_value = PowerUnit.KW

        conversion_params_node = MagicMock()
        out_ecs_node = MagicMock()
        out_ec_node = MagicMock()

        out_ecs_node.__len__ = MagicMock(return_value=1)
        out_ecs_node.__iter__ = MagicMock(return_value=iter([out_ec_node]))
        mock_get.return_value = out_ecs_node

        with patch(
            "ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node",
            return_value="heat",
        ):
            with patch(
                "ehubx.parser.yaml_parser.parse_optional_str_from_dict_node",
                return_value=None,
            ):
                conv_techs.add_id(tech_id)
                conv_techs.add_in_ec(tech_id, EcId("electricity"), PowerUnit.KW)
                conv_techs.set_in_ec_main(tech_id, EcId("electricity"))

                conv_tech_parser._parse_out_ecs(
                    conversion_params_node, tech_id, stages, mock_ecs, conv_techs
                )

        assert mock_parse_eff.called


# ============================================================================
# TEST: _parse_out_eff
# ============================================================================


class TestParseOutEff:
    """Tests for _parse_out_eff function"""

    @patch("ehubx.parser.yaml_parser.parse_mandatory_yeardep_value_from_dict_node")
    def test_out_eff_as_year_dependent_value(
        self, mock_parse, stages, conv_techs, tech_id, ec_id_in, ec_id_out, stage_id
    ):
        """Should parse out_eff as year-dependent value"""
        mock_ecs = MagicMock(spec=Ecs)
        mock_ecs.get_unit.side_effect = lambda ec_id: PowerUnit.KW

        out_ec_node = MagicMock(spec=yaml_parser.YamlDictNode)
        out_ec_node.file_path = "test.yaml"
        out_eff_node = MagicMock(spec=yaml_parser.YamlValueNode)
        out_eff_node.value = 0.9  # Not a CSV path (doesn't end with .csv)

        out_ec_node.__getitem__ = MagicMock(return_value=out_eff_node)

        mock_parse.return_value = {stage_id: Value(0.9, DimlessUnit())}

        conv_techs.add_id(tech_id)
        conv_techs.add_in_ec(tech_id, ec_id_in, PowerUnit.KW)
        conv_techs.set_in_ec_main(tech_id, ec_id_in)
        conv_techs.add_out_ec(tech_id, ec_id_out, PowerUnit.KW)

        conv_tech_parser._parse_out_eff(
            out_ec_node, tech_id, ec_id_out, stages, mock_ecs, conv_techs
        )

        mock_parse.assert_called_once()

    @patch("ehubx.parser.csv_parser.parse")
    @patch("ehubx.parser.yaml_parser.check_file_exists")
    def test_out_eff_as_csv_profile(
        self, mock_check_file, mock_csv_parse, stages, conv_techs, tech_id, ec_id_in, ec_id_out
    ):
        """Should parse out_eff from CSV file when path ends with .csv"""
        mock_ecs = MagicMock(spec=Ecs)
        mock_ecs.get_unit.side_effect = lambda ec_id: PowerUnit.KW

        out_ec_node = MagicMock(spec=yaml_parser.YamlDictNode)
        out_ec_node.file_path = "/test/path/file.yaml"
        out_eff_node = MagicMock(spec=yaml_parser.YamlValueNode)
        out_eff_node.value = "profile.csv"

        out_ec_node.__getitem__ = MagicMock(return_value=out_eff_node)

        # Mock CSV parsing - return empty dataframe to avoid processing
        mock_df = MagicMock()
        mock_df.columns = []
        mock_df.attrs = {}
        mock_csv_parse.return_value = mock_df

        conv_techs.add_id(tech_id)
        conv_techs.add_in_ec(tech_id, ec_id_in, PowerUnit.KW)
        conv_techs.set_in_ec_main(tech_id, ec_id_in)
        conv_techs.add_out_ec(tech_id, ec_id_out, PowerUnit.KW)

        conv_tech_parser._parse_out_eff(
            out_ec_node, tech_id, ec_id_out, stages, mock_ecs, conv_techs
        )

        mock_check_file.assert_called_once()
        mock_csv_parse.assert_called_once()


# ============================================================================
# TEST: parse_secondary
# ============================================================================


class TestParseSecondary:
    """Tests for parse_secondary function"""

    def test_none_root_node(self, stages, conv_techs):
        """Should return early if root_node is None"""
        conv_tech_parser.parse_secondary(None, stages, MagicMock(), conv_techs)
        stages.assert_not_called()
        # Should not raise

    def test_none_hubs_node(self, stages, conv_techs):
        """Should return early if hubs_node is None"""
        root = MagicMock()
        root.__getitem__.return_value = None

        conv_tech_parser.parse_secondary(root, stages, MagicMock(), conv_techs)
        stages.assert_not_called()
        # Should not raise

    @patch("ehubx.parser.conv_tech_parser._parse_hub_secondary")
    def test_with_hubs(self, mock_parse_hub, stages, conv_techs):
        """Should parse secondary parameters for hubs"""
        root = MagicMock(spec=yaml_parser.YamlNode)
        hub_node = MagicMock(spec=yaml_parser.YamlDictNode)
        hubs_node = MagicMock(spec=yaml_parser.YamlListNode)
        hubs_node.__iter__ = MagicMock(return_value=iter([hub_node]))
        root.__getitem__.return_value = hubs_node

        mock_ecs = MagicMock(spec=Ecs)

        conv_tech_parser.parse_secondary(root, stages, mock_ecs, conv_techs)

        # Check that _parse_hub_secondary was called with the right arguments
        assert mock_parse_hub.called
        call_args = mock_parse_hub.call_args
        assert call_args[0][0] == hub_node  # hub_node
        assert call_args[0][1] == stages  # stages
        assert call_args[0][3] == conv_techs  # conv_techs


# ============================================================================
# TEST: _parse_hub_secondary
# ============================================================================


class TestParseHubSecondary:
    """Tests for _parse_hub_secondary function"""

    def test_none_techs_node(self, stages, conv_techs, hub_id, tech_id):
        """Should return early if techs_node is None"""
        hub_node = MagicMock()
        hub_node.__getitem__.return_value = None

        with patch(
            "ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node",
            return_value=hub_id.key,
        ):
            conv_techs.add_id(tech_id)
            conv_tech_parser._parse_hub_secondary(
                hub_node, stages, MagicMock(), conv_techs
            )
        stages.assert_not_called()
        # Should not raise

    @patch("ehubx.parser.conv_tech_parser._parse_tech_secondary")
    def test_with_techs(self, mock_parse_tech, stages, conv_techs, hub_id, tech_id):
        """Should parse secondary for techs in hub"""
        hub_node = MagicMock()
        techs_node = MagicMock()
        tech_node = MagicMock()
        techs_node.__getitem__ = MagicMock(return_value=tech_node)
        hub_node.__getitem__.return_value = techs_node

        conv_techs.add_id(tech_id)

        with patch(
            "ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node",
            return_value=hub_id.key,
        ):
            conv_tech_parser._parse_hub_secondary(
                hub_node, stages, MagicMock(), conv_techs
            )

        mock_parse_tech.assert_called_once()


# ============================================================================
# TEST: _parse_tech_secondary
# ============================================================================


class TestParseTechSecondary:
    """Tests for _parse_tech_secondary function"""

    def test_none_conversion_params_node(self, stages, conv_techs, hub_id, tech_id):
        """Should return early if conversion_params_node is None"""
        tech_node = MagicMock()
        tech_node.__getitem__.return_value = None

        _mock_conv_tech_prep(conv_techs, tech_id)

        conv_tech_parser._parse_tech_secondary(
            tech_node, hub_id, tech_id, stages, MagicMock(), conv_techs
        )
        stages.assert_not_called()
        # Should not raise

    @patch("ehubx.parser.conv_tech_parser._parse_tech_secondary_profiles")
    @patch("ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    def test_with_availability_and_out_sum(
        self, mock_check, mock_parse_val, mock_parse_profiles, stages, conv_techs, hub_id, tech_id, stage_id
    ):
        """Should parse out_sum_min, out_sum_max, and availability"""
        tech_node = MagicMock()
        conversion_params_node = MagicMock()
        tech_node.__getitem__.return_value = conversion_params_node

        mock_ecs = MagicMock(spec=Ecs)
        mock_ecs.get_unit.return_value = PowerUnit.KW

        mock_parse_val.side_effect = [
            {stage_id: Value(100.0, PowerUnit.KW)},  # out_sum_min
            {stage_id: Value(200.0, PowerUnit.KW)},  # out_sum_max
            {stage_id: Value(0.95, DimlessUnit())},  # availability
        ]

        conv_techs.add_id(tech_id)
        conv_techs.add_in_ec(tech_id, EcId("electricity"), PowerUnit.KW)
        conv_techs.set_in_ec_main(tech_id, EcId("electricity"))
        conv_techs.add_out_ec(tech_id, EcId("heat"), PowerUnit.KW)
        conv_techs.set_out_ec_main(tech_id, EcId("heat"))

        conv_tech_parser._parse_tech_secondary(
            tech_node, hub_id, tech_id, stages, mock_ecs, conv_techs
        )

        assert mock_parse_val.call_count >= 1


# ============================================================================
# TEST: _parse_tech_secondary_profiles
# ============================================================================


class TestParseTechSecondaryProfiles:
    """Tests for _parse_tech_secondary_profiles function"""

    def test_no_profile_path(self, conv_techs, hub_id, tech_id):
        """Should return early if no profile_path specified"""
        conversion_params_node = MagicMock()

        with patch(
            "ehubx.parser.yaml_parser.parse_optional_str_from_dict_node",
            return_value=None,
        ):
            conv_tech_parser._parse_tech_secondary_profiles(
                conversion_params_node, hub_id, tech_id, conv_techs
            )
        conversion_params_node.assert_not_called()
        # Should not raise

    @patch("ehubx.parser.csv_parser.parse")
    @patch("ehubx.parser.yaml_parser.check_file_exists")
    def test_with_availability_profile(
        self, mock_check_file, mock_csv_parse, conv_techs, hub_id, tech_id
    ):
        """Should parse availability profile from CSV"""
        conversion_params_node = MagicMock()
        conversion_params_node.file_path = "/test/path/file.yaml"

        # Mock CSV parsing
        mock_df = MagicMock()
        mock_df.columns = []
        mock_df.attrs = {"unit": {}}
        mock_csv_parse.return_value = mock_df

        conv_techs.add_id(tech_id)

        with patch(
            "ehubx.parser.yaml_parser.parse_optional_str_from_dict_node",
            return_value="profiles.csv",
        ):
            conv_tech_parser._parse_tech_secondary_profiles(
                conversion_params_node, hub_id, tech_id, conv_techs
            )

        mock_check_file.assert_called_once()
        mock_csv_parse.assert_called_once()


# ============================================================================
# TEST: EXCEPTION HANDLING
# ============================================================================


class TestExceptionHandling:
    """Tests for exception handling and error conditions"""

    def test_parsing_exception_creation(self):
        """Should create ParsingException with correct attributes"""
        exc = exceptions.ParsingException("/test.yaml", "Test error message")

        assert "/test.yaml" in str(exc)
        assert "Test error message" in str(exc)

    @patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
    def test_missing_mandatory_node_in_parsing(self, mock_parse_str):
        """Should propagate MissingNodeException from YAML parsing"""
        mock_parse_str.side_effect = exceptions.MissingNodeException(
            "/test.yaml", "conversion_params", module="test"
        )

        with pytest.raises(exceptions.MissingNodeException):
            root = MagicMock(spec=yaml_parser.YamlNode)
            root.__getitem__.return_value = [MagicMock()]
            conv_tech_parser.parse_primary(root, MagicMock(), MagicMock(), MagicMock())

    def test_invalid_unit_in_efficiency_profile(self):
        """Should raise ParsingException for invalid unit in profile"""
        # This tests the CSV profile parsing error handling
        with patch("ehubx.parser.csv_parser.parse") as mock_csv:
            with patch("ehubx.parser.yaml_parser.check_file_exists"):
                mock_df = MagicMock()
                mock_df.columns = [("2025", "tech1", "heat")]
                mock_df.attrs = {"unit": {("2025", "tech1", "heat"): "invalid_unit"}}
                mock_csv.return_value = mock_df

                conv_techs = ConversionTechs()
                conv_techs.add_id(TechId("tech1"))
                conv_techs.add_in_ec(TechId("tech1"), EcId("elec"), PowerUnit.KW)
                conv_techs.set_in_ec_main(TechId("tech1"), EcId("elec"))
                conv_techs.add_out_ec(TechId("tech1"), EcId("heat"), PowerUnit.KW)

                # Create mock out_ec_node pointing to the CSV profile
                out_ec_node = MagicMock(spec=yaml_parser.YamlDictNode)
                out_ec_node.file_path = "/test/path/file.yaml"
                out_eff_node = MagicMock(spec=yaml_parser.YamlValueNode)
                out_eff_node.value = "profile.csv"
                out_ec_node.__getitem__ = MagicMock(return_value=out_eff_node)

                mock_ecs = MagicMock(spec=Ecs)
                mock_ecs.get_unit.return_value = PowerUnit.KW

                # Should raise an exception when trying to parse the invalid unit
                with pytest.raises(exceptions.ParsingException):
                    conv_tech_parser._parse_out_eff(
                        out_ec_node,
                        TechId("tech1"),
                        EcId("heat"),
                        MagicMock(),
                        mock_ecs,
                        conv_techs,
                    )

    def test_missing_file_exception_for_csv_profile(self):
        """Should raise exception when CSV profile file doesn't exist"""
        out_ec_node = MagicMock(spec=yaml_parser.YamlDictNode)
        out_ec_node.file_path = "/test/path/file.yaml"
        out_eff_node = MagicMock(spec=yaml_parser.YamlValueNode)
        out_eff_node.value = "nonexistent.csv"
        out_ec_node.__getitem__ = MagicMock(return_value=out_eff_node)

        mock_ecs = MagicMock(spec=Ecs)
        mock_ecs.get_unit.return_value = PowerUnit.KW

        conv_techs = ConversionTechs()
        tech_id = TechId("test_tech")
        ec_id_in = EcId("electricity")
        ec_id_out = EcId("heat")

        _mock_conv_tech_prep(conv_techs, tech_id)

        with patch(
            "ehubx.parser.yaml_parser.check_file_exists",
            side_effect=exceptions.MissingFileException(
                "/test/path/nonexistent.csv", "CSV profile", module="test"
            ),
        ):
            with pytest.raises(exceptions.MissingFileException):
                conv_tech_parser._parse_out_eff(
                    out_ec_node, tech_id, ec_id_out, MagicMock(), mock_ecs, conv_techs
                )


# ============================================================================
# TEST: INTEGRATION TESTS
# ============================================================================


class TestIntegration:
    """Integration tests combining multiple functions"""

    @patch("ehubx.parser.conv_tech_parser._parse_conv_tech_primary")
    def test_parse_primary_integration(self, mock_parse_tech, stages, ecs, techs):
        """Should successfully parse a complete primary structure"""
        root = MagicMock()
        tech_node1 = MagicMock()
        tech_node2 = MagicMock()
        techs_node = MagicMock()
        techs_node.__iter__ = MagicMock(
            return_value=iter([tech_node1, tech_node2])
        )
        root.__getitem__.return_value = techs_node

        result = conv_tech_parser.parse_primary(root, stages, ecs, techs)

        assert isinstance(result, ConversionTechs)
        assert mock_parse_tech.call_count == 2

    @patch("ehubx.parser.conv_tech_parser._parse_hub_secondary")
    def test_parse_secondary_integration(self, mock_parse_hub, stages):
        """Should successfully parse secondary structure with multiple hubs"""
        root = MagicMock()
        hub_node1 = MagicMock()
        hub_node2 = MagicMock()
        hubs_node = MagicMock()
        hubs_node.__iter__ = MagicMock(
            return_value=iter([hub_node1, hub_node2])
        )
        root.__getitem__.return_value = hubs_node

        conv_techs = ConversionTechs()

        conv_tech_parser.parse_secondary(root, stages, MagicMock(), conv_techs)

        assert mock_parse_hub.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
