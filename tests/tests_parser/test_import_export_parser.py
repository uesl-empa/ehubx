"""
Tests for import_export_parser module
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.export_data import Exports
from ehubx.data.hub_data import HubId
from ehubx.data.import_data import Imports
from ehubx.data.stage_data import StageId
from ehubx.data.time_data import TimeId
from ehubx.data.unit import CurrencyUnit, MassUnit, TimeUnit, Unit
from ehubx.data.value import Value
from ehubx.parser import import_export_parser, exceptions


# ============================================================================
# Tests for parse_imports() function
# ============================================================================


class TestParseImports:
    """Tests for parse_imports function"""

    def test_parse_imports_file_not_found_returns_empty(self):
        """Test that missing imports.yaml file returns empty Imports object"""
        ecs = Mock(spec=Ecs)
        result = import_export_parser.parse_imports("/nonexistent/path", ecs)

        assert isinstance(result, Imports)
        assert len(result.tuples) == 0

    @patch("ehubx.parser.yaml_parser.parse")
    @patch("os.path.isfile")
    def test_parse_imports_yaml_returns_none(self, mock_isfile, mock_parse):
        """Test that yaml returning None returns empty Imports object"""
        mock_isfile.return_value = True
        mock_parse.return_value = None
        ecs = Mock(spec=Ecs)

        result = import_export_parser.parse_imports("/test/path", ecs)

        assert isinstance(result, Imports)
        assert len(result.tuples) == 0

    @patch("ehubx.parser.import_export_parser._parse_import_node")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    @patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_str_list_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse")
    @patch("os.path.isfile")
    def test_parse_imports_with_single_entry(
        self, mock_isfile, mock_parse, mock_str_list, mock_mandatory_str,
        mock_check_type, mock_parse_node
    ):
        """Test parsing imports with single valid entry"""
        mock_isfile.return_value = True

        mock_import_node = Mock()
        mock_import_node.file_path = "/test/imports.yaml"

        mock_root_node = Mock()
        mock_root_node.file_path = "/test/imports.yaml"
        mock_root_node.__iter__ = Mock(return_value=iter([mock_import_node]))
        mock_parse.return_value = mock_root_node

        mock_str_list.side_effect = [["stage1"], ["hub1"]]
        mock_mandatory_str.return_value = "ec1"

        mock_ecs = Mock(spec=Ecs)
        mock_ecs.get_unit.return_value = Unit.from_str("MWh")

        result = import_export_parser.parse_imports("/test/path", mock_ecs)

        assert isinstance(result, Imports)
        mock_parse_node.assert_called_once()

    @patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_str_list_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse")
    @patch("os.path.isfile")
    def test_parse_imports_duplicate_tuples_raises_exception(
        self, mock_isfile, mock_parse, mock_str_list, mock_mandatory_str
    ):
        """Test that duplicate (stage, hub, ec) tuples raise ParsingException"""
        from ehubx.parser.yaml_parser import YamlListNode, YamlDictNode

        mock_isfile.return_value = True

        mock_node1 = Mock(spec=YamlDictNode)
        mock_node1.file_path = "/test/imports.yaml"
        mock_node2 = Mock(spec=YamlDictNode)
        mock_node2.file_path = "/test/imports.yaml"

        mock_root_node = Mock(spec=YamlListNode)
        mock_root_node.file_path = "/test/imports.yaml"
        mock_root_node.__iter__ = Mock(return_value=iter([mock_node1, mock_node2]))
        mock_parse.return_value = mock_root_node

        # Both nodes parse to same tuple
        mock_str_list.side_effect = [["stage1"], ["hub1"], ["stage1"], ["hub1"]]
        mock_mandatory_str.side_effect = ["ec1", "ec1"]

        mock_ecs = Mock(spec=Ecs)
        mock_ecs.get_unit.return_value = Unit.from_str("MWh")

        with patch("ehubx.parser.import_export_parser._parse_import_node"):
            with pytest.raises(exceptions.ParsingException) as exc_info:
                import_export_parser.parse_imports("/test/path", mock_ecs)

            # Verify exception message contains "Overlap"
            assert "overlap" in str(exc_info.value).lower()

    @patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_str_list_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse")
    @patch("os.path.isfile")
    def test_parse_imports_cartesian_product_of_stages_and_hubs(
        self, mock_isfile, mock_parse, mock_str_list, mock_mandatory_str
    ):
        """Test that multiple stages and hubs create cartesian product"""
        from ehubx.parser.yaml_parser import YamlListNode, YamlDictNode

        mock_isfile.return_value = True

        mock_node = Mock(spec=YamlDictNode)
        mock_node.file_path = "/test/imports.yaml"

        mock_root_node = Mock(spec=YamlListNode)
        mock_root_node.file_path = "/test/imports.yaml"
        mock_root_node.__iter__ = Mock(return_value=iter([mock_node]))
        mock_parse.return_value = mock_root_node

        # Two stages and two hubs should create 4 tuples
        mock_str_list.side_effect = [["stage1", "stage2"], ["hub1", "hub2"]]
        mock_mandatory_str.return_value = "ec1"

        mock_ecs = Mock(spec=Ecs)
        mock_ecs.get_unit.return_value = Unit.from_str("MWh")

        with patch("ehubx.parser.import_export_parser._parse_import_node") as mock_parse_node:
            result = import_export_parser.parse_imports("/test/path", mock_ecs)

            # Check that _parse_import_node was called with 4 tuples (2x2)
            call_args = mock_parse_node.call_args
            stage_hub_tuples = call_args[0][1]
            assert len(stage_hub_tuples) == 4


# ============================================================================
# Tests for parse_exports() function
# ============================================================================


class TestParseExports:
    """Tests for parse_exports function"""

    def test_parse_exports_file_not_found_returns_empty(self):
        """Test that missing exports.yaml file returns empty Exports object"""
        ecs = Mock(spec=Ecs)
        result = import_export_parser.parse_exports("/nonexistent/path", ecs)

        assert isinstance(result, Exports)
        assert len(result.tuples) == 0

    @patch("ehubx.parser.yaml_parser.parse")
    @patch("os.path.isfile")
    def test_parse_exports_yaml_returns_none(self, mock_isfile, mock_parse):
        """Test that yaml returning None returns empty Exports object"""
        mock_isfile.return_value = True
        mock_parse.return_value = None
        ecs = Mock(spec=Ecs)

        result = import_export_parser.parse_exports("/test/path", ecs)

        assert isinstance(result, Exports)
        assert len(result.tuples) == 0

    @patch("ehubx.parser.import_export_parser._parse_export_node")
    @patch("ehubx.parser.yaml_parser.check_node_type")
    @patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_str_list_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse")
    @patch("os.path.isfile")
    def test_parse_exports_with_single_entry(
        self, mock_isfile, mock_parse, mock_str_list, mock_mandatory_str,
        mock_check_type, mock_parse_node
    ):
        """Test parsing exports with single valid entry"""
        mock_isfile.return_value = True

        mock_export_node = Mock()
        mock_export_node.file_path = "/test/exports.yaml"

        mock_root_node = Mock()
        mock_root_node.file_path = "/test/exports.yaml"
        mock_root_node.__iter__ = Mock(return_value=iter([mock_export_node]))
        mock_parse.return_value = mock_root_node

        mock_str_list.side_effect = [["stage1"], ["hub1"]]
        mock_mandatory_str.return_value = "ec1"

        mock_ecs = Mock(spec=Ecs)
        mock_ecs.get_unit.return_value = Unit.from_str("MWh")

        result = import_export_parser.parse_exports("/test/path", mock_ecs)

        assert isinstance(result, Exports)
        mock_parse_node.assert_called_once()

    @patch("ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_str_list_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse")
    @patch("os.path.isfile")
    def test_parse_exports_duplicate_tuples_raises_exception(
        self, mock_isfile, mock_parse, mock_str_list, mock_mandatory_str
    ):
        """Test that duplicate (stage, hub, ec) tuples raise ParsingException"""
        from ehubx.parser.yaml_parser import YamlListNode, YamlDictNode

        mock_isfile.return_value = True

        mock_node1 = Mock(spec=YamlDictNode)
        mock_node1.file_path = "/test/exports.yaml"
        mock_node2 = Mock(spec=YamlDictNode)
        mock_node2.file_path = "/test/exports.yaml"

        mock_root_node = Mock(spec=YamlListNode)
        mock_root_node.file_path = "/test/exports.yaml"
        mock_root_node.__iter__ = Mock(return_value=iter([mock_node1, mock_node2]))
        mock_parse.return_value = mock_root_node

        # Both nodes parse to same tuple
        mock_str_list.side_effect = [["stage1"], ["hub1"], ["stage1"], ["hub1"]]
        mock_mandatory_str.side_effect = ["ec1", "ec1"]

        mock_ecs = Mock(spec=Ecs)
        mock_ecs.get_unit.return_value = Unit.from_str("MWh")

        with patch("ehubx.parser.import_export_parser._parse_export_node"):
            with pytest.raises(exceptions.ParsingException) as exc_info:
                import_export_parser.parse_exports("/test/path", mock_ecs)

            # Verify exception message contains "Overlap"
            assert "overlap" in str(exc_info.value).lower()


# ============================================================================
# Tests for _parse_import_node() function
# ============================================================================


class TestParseImportNode:
    """Tests for _parse_import_node function"""

    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_optional_value_from_dict_node")
    def test_parse_import_node_with_no_optional_params(self, mock_value, mock_str):
        """Test parsing import node without optional parameters"""
        mock_value.return_value = None
        mock_str.return_value = None

        node = Mock()
        stage_hub_tuples = {(StageId("s1"), HubId("h1"))}
        ec_id = EcId("ec1")
        ec_unit = Unit.from_str("MWh")
        imports = Imports()

        import_export_parser._parse_import_node(
            node, stage_hub_tuples, ec_id, ec_unit, imports
        )

        assert (StageId("s1"), HubId("h1"), EcId("ec1")) in imports.tuples

    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_optional_value_from_dict_node")
    def test_parse_import_node_with_all_optional_params(self, mock_value, mock_str):
        """Test parsing import node with all optional parameters"""
        ec_unit = Unit.from_str("MWh")

        # Mock return values for price, co2, min, max, sum_min, sum_max in order
        mock_value.side_effect = [
            Value(0.15, CurrencyUnit.CHF / ec_unit),  # price
            Value(0.5, MassUnit.KG / ec_unit),  # co2
            Value(10, ec_unit / TimeUnit.H),  # min
            Value(100, ec_unit / TimeUnit.H),  # max
            Value(50, ec_unit),  # sum_min
            Value(500, ec_unit),  # sum_max
        ]
        mock_str.return_value = None

        node = Mock()
        stage_hub_tuples = {(StageId("s1"), HubId("h1"))}
        ec_id = EcId("ec1")
        imports = Imports()

        import_export_parser._parse_import_node(
            node, stage_hub_tuples, ec_id, ec_unit, imports
        )

        # Verify tuple was added
        assert (StageId("s1"), HubId("h1"), EcId("ec1")) in imports.tuples

        # Verify optional parameters were set
        ecs = Ecs()
        ecs.add_id(EcId("ec1"))
        ecs.set_unit(EcId("ec1"), ec_unit)

        price_ts = imports.get_price(StageId("s1"), HubId("h1"), EcId("ec1"))
        assert price_ts.def_value.to_float(CurrencyUnit.CHF / ec_unit) == pytest.approx(0.15)
        assert imports.get_co2(StageId("s1"), HubId("h1"), EcId("ec1")).def_value.to_float(MassUnit.KG / ec_unit) == pytest.approx(0.5)

    @patch("ehubx.parser.import_export_parser._parse_import_profiles")
    @patch("ehubx.parser.csv_parser.parse")
    @patch("ehubx.parser.yaml_parser.check_file_exists")
    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_optional_value_from_dict_node")
    def test_parse_import_node_with_profile_path(
        self, mock_value, mock_str, mock_check_file, mock_csv_parse, mock_parse_profiles
    ):
        """Test parsing import node with profile_path specified"""
        mock_value.return_value = None
        mock_str.return_value = "profiles/import.csv"
        mock_check_file.return_value = None

        mock_df = MagicMock()
        mock_csv_parse.return_value = mock_df

        node = Mock()
        node.file_path = "/test/basic/imports.yaml"
        stage_hub_tuples = {(StageId("s1"), HubId("h1"))}
        ec_id = EcId("ec1")
        ec_unit = Unit.from_str("MWh")
        imports = Imports()

        import_export_parser._parse_import_node(
            node, stage_hub_tuples, ec_id, ec_unit, imports
        )

        # Verify csv parser was called
        mock_csv_parse.assert_called_once()
        # Verify profile parser was called
        mock_parse_profiles.assert_called_once()


# ============================================================================
# Tests for _parse_export_node() function
# ============================================================================


class TestParseExportNode:
    """Tests for _parse_export_node function"""

    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_optional_value_from_dict_node")
    def test_parse_export_node_with_no_optional_params(self, mock_value, mock_str):
        """Test parsing export node without optional parameters"""
        mock_value.return_value = None
        mock_str.return_value = None

        node = Mock()
        stage_hub_tuples = {(StageId("s1"), HubId("h1"))}
        ec_id = EcId("ec1")
        ec_unit = Unit.from_str("MWh")
        exports = Exports()

        import_export_parser._parse_export_node(
            node, stage_hub_tuples, ec_id, ec_unit, exports
        )

        assert (StageId("s1"), HubId("h1"), EcId("ec1")) in exports.tuples

    @patch("ehubx.parser.yaml_parser.parse_optional_str_from_dict_node")
    @patch("ehubx.parser.yaml_parser.parse_optional_value_from_dict_node")
    def test_parse_export_node_with_all_optional_params(self, mock_value, mock_str):
        """Test parsing export node with all optional parameters"""
        ec_unit = Unit.from_str("MWh")

        # Mock return values for price, co2, min, max, sum_min, sum_max in order
        mock_value.side_effect = [
            Value(0.10, CurrencyUnit.CHF / ec_unit),  # price
            Value(0.3, MassUnit.KG / ec_unit),  # co2
            Value(5, ec_unit / TimeUnit.H),  # min
            Value(50, ec_unit / TimeUnit.H),  # max
            Value(25, ec_unit),  # sum_min
            Value(250, ec_unit),  # sum_max
        ]
        mock_str.return_value = None

        node = Mock()
        stage_hub_tuples = {(StageId("s1"), HubId("h1"))}
        ec_id = EcId("ec1")
        exports = Exports()

        import_export_parser._parse_export_node(
            node, stage_hub_tuples, ec_id, ec_unit, exports
        )

        # Verify tuple was added
        assert (StageId("s1"), HubId("h1"), EcId("ec1")) in exports.tuples
        assert exports.get_price(StageId("s1"), HubId("h1"), EcId("ec1")).def_value.to_float(CurrencyUnit.CHF / ec_unit) == pytest.approx(0.10)
        assert exports.get_co2(StageId("s1"), HubId("h1"), EcId("ec1")).def_value.to_float(MassUnit.KG / ec_unit) == pytest.approx(0.3)


# ============================================================================
# Tests for _parse_import_profiles() function
# ============================================================================


class TestParseImportProfiles:
    """Tests for _parse_import_profiles function"""

    def test_parse_import_profiles_empty_dataframe(self):
        """Test parsing with empty dataframe (no matching columns)"""
        df = MagicMock()
        df.columns = []

        imports = Imports()
        imports.add_tuple(StageId("s1"), HubId("h1"), EcId("ec1"), Unit.from_str("MWh"))

        # Should not raise exception
        import_export_parser._parse_import_profiles(
            df, "/test/profile.csv", StageId("s1"), HubId("h1"),
            EcId("ec1"), Unit.from_str("MWh"), imports
        )

    @patch("ehubx.data.import_data.Imports.set_price")
    def test_parse_import_profiles_non_matching_stage(self, mock_set_price):
        """Test that profiles for different stage are filtered out"""
        df = MagicMock()
        df.columns = [("s2", "h1", "ec1", "price")]

        imports = Imports()
        imports.add_tuple(StageId("s1"), HubId("h1"), EcId("ec1"), Unit.from_str("MWh"))

        # Should not raise exception, just skip non-matching column
        import_export_parser._parse_import_profiles(
            df, "/test/profile.csv", StageId("s1"), HubId("h1"),
            EcId("ec1"), Unit.from_str("MWh"), imports
        )
        mock_set_price.assert_not_called()

    @patch("ehubx.data.import_data.Imports.set_price")
    def test_parse_import_profiles_non_matching_hub(self, mock_set_price):
        """Test that profiles for different hub are filtered out"""
        df = MagicMock()
        df.columns = [("s1", "h2", "ec1", "price")]

        imports = Imports()
        imports.add_tuple(StageId("s1"), HubId("h1"), EcId("ec1"), Unit.from_str("MWh"))

        # Should not raise exception, just skip non-matching column
        import_export_parser._parse_import_profiles(
            df, "/test/profile.csv", StageId("s1"), HubId("h1"),
            EcId("ec1"), Unit.from_str("MWh"), imports
        )
        mock_set_price.assert_not_called()

    @patch("ehubx.data.import_data.Imports.set_price")
    def test_parse_import_profiles_non_matching_ec(self, mock_set_price):
        """Test that profiles for different ec are filtered out"""
        df = MagicMock()
        df.columns = [("s1", "h1", "ec2", "price")]

        imports = Imports()
        imports.add_tuple(StageId("s1"), HubId("h1"), EcId("ec1"), Unit.from_str("MWh"))

        # Should not raise exception, just skip non-matching column
        import_export_parser._parse_import_profiles(
            df, "/test/profile.csv", StageId("s1"), HubId("h1"),
            EcId("ec1"), Unit.from_str("MWh"), imports
        )
        mock_set_price.assert_not_called()

    def test_parse_import_profiles_invalid_unit_raises_exception(self):
        """Test that invalid unit in profile raises ParsingException"""
        ec_unit = Unit.from_str("MWh")

        df = MagicMock()
        df.columns = [("s1", "h1", "ec1", "price")]
        df.attrs = {
            "unit": {("s1", "h1", "ec1", "price"): "INVALID_UNIT"}
        }

        imports = Imports()
        imports.add_tuple(StageId("s1"), HubId("h1"), EcId("ec1"), ec_unit)

        with pytest.raises(exceptions.ParsingException) as exc_info:
            import_export_parser._parse_import_profiles(
                df, "/test/profile.csv", StageId("s1"), HubId("h1"),
                EcId("ec1"), ec_unit, imports
            )

        # Verify exception message mentions invalid unit
        assert "invalid unit" in str(exc_info.value).lower()

    def test_parse_import_profiles_wrong_unit_type_raises_exception(self):
        """Test that wrong unit type for key raises ParsingException"""
        ec_unit = Unit.from_str("MWh")

        df = MagicMock()
        df.columns = [("s1", "h1", "ec1", "price")]
        # Price should be CHF/MWh, but we provide kg (mass unit)
        df.attrs = {
            "unit": {("s1", "h1", "ec1", "price"): "kg"}
        }

        imports = Imports()
        imports.add_tuple(StageId("s1"), HubId("h1"), EcId("ec1"), ec_unit)

        with pytest.raises(exceptions.ParsingException) as exc_info:
            import_export_parser._parse_import_profiles(
                df, "/test/profile.csv", StageId("s1"), HubId("h1"),
                EcId("ec1"), ec_unit, imports
            )

        # Verify exception message mentions unit or expected
        error_msg = str(exc_info.value).lower()
        assert "unit" in error_msg or "expected" in error_msg

    def test_parse_import_profiles_unknown_key_is_ignored(self):
        """Test that unknown profile key is ignored without error"""
        ec_unit = Unit.from_str("MWh")

        df = MagicMock()
        df.columns = [("s1", "h1", "ec1", "unknown_key")]
        df.attrs = {
            "unit": {("s1", "h1", "ec1", "unknown_key"): "MWh"}
        }

        imports = Imports()
        imports.add_tuple(StageId("s1"), HubId("h1"), EcId("ec1"), ec_unit)

        # Should not raise exception for unknown key
        import_export_parser._parse_import_profiles(
            df, "/test/profile.csv", StageId("s1"), HubId("h1"),
            EcId("ec1"), ec_unit, imports
        )

    def test_parse_import_profiles_price_key(self):
        """Test parsing profile with price key"""
        ec_unit = Unit.from_str("MWh")

        df = MagicMock()
        df.columns = [("s1", "h1", "ec1", "price")]
        df.attrs = {
            "unit": {("s1", "h1", "ec1", "price"): "CHF/MWh"}
        }
        df.__getitem__ = Mock(return_value=pd.Series({
            "t1": 0.10,
            "t2": 0.15
        }))

        imports = Imports()
        imports.add_tuple(StageId("s1"), HubId("h1"), EcId("ec1"), ec_unit)

        import_export_parser._parse_import_profiles(
            df, "/test/profile.csv", StageId("s1"), HubId("h1"),
            EcId("ec1"), ec_unit, imports
        )

        # Verify price was set
        price_ts = imports.get_price(StageId("s1"), HubId("h1"), EcId("ec1"))
        assert price_ts.get_value(TimeId("t1")).to_float(CurrencyUnit.CHF / ec_unit) == pytest.approx(0.10)

    def test_parse_import_profiles_co2_key(self):
        """Test parsing profile with co2 key"""
        ec_unit = Unit.from_str("MWh")

        df = MagicMock()
        df.columns = [("s1", "h1", "ec1", "co2")]
        df.attrs = {
            "unit": {("s1", "h1", "ec1", "co2"): "kg/MWh"}
        }
        df.__getitem__ = Mock(return_value=pd.Series({
            "t1": 0.5
        }))

        imports = Imports()
        imports.add_tuple(StageId("s1"), HubId("h1"), EcId("ec1"), ec_unit)

        import_export_parser._parse_import_profiles(
            df, "/test/profile.csv", StageId("s1"), HubId("h1"),
            EcId("ec1"), ec_unit, imports
        )

        # Verify co2 was set
        co2_ts = imports.get_co2(StageId("s1"), HubId("h1"), EcId("ec1"))
        assert co2_ts.get_value(TimeId("t1")).to_float(MassUnit.KG / ec_unit) == pytest.approx(0.5)

    def test_parse_import_profiles_min_key(self):
        """Test parsing profile with min key"""
        ec_unit = Unit.from_str("MWh")

        df = MagicMock()
        df.columns = [("s1", "h1", "ec1", "min")]
        df.attrs = {
            "unit": {("s1", "h1", "ec1", "min"): "MWh/h"}
        }
        df.__getitem__ = Mock(return_value=pd.Series({
            "t1": 10.0
        }))

        imports = Imports()
        imports.add_tuple(StageId("s1"), HubId("h1"), EcId("ec1"), ec_unit)

        import_export_parser._parse_import_profiles(
            df, "/test/profile.csv", StageId("s1"), HubId("h1"),
            EcId("ec1"), ec_unit, imports
        )

        # Verify min was set
        min_ts = imports.get_min(StageId("s1"), HubId("h1"), EcId("ec1"))
        assert min_ts.get_value(TimeId("t1")).to_float(ec_unit / TimeUnit.H) == pytest.approx(10.0)

    def test_parse_import_profiles_max_key(self):
        """Test parsing profile with max key"""
        ec_unit = Unit.from_str("MWh")

        df = MagicMock()
        df.columns = [("s1", "h1", "ec1", "max")]
        df.attrs = {
            "unit": {("s1", "h1", "ec1", "max"): "MWh/h"}
        }
        df.__getitem__ = Mock(return_value=pd.Series({
            "t1": 100.0
        }))

        imports = Imports()
        imports.add_tuple(StageId("s1"), HubId("h1"), EcId("ec1"), ec_unit)

        import_export_parser._parse_import_profiles(
            df, "/test/profile.csv", StageId("s1"), HubId("h1"),
            EcId("ec1"), ec_unit, imports
        )

        # Verify max was set
        max_ts = imports.get_max(StageId("s1"), HubId("h1"), EcId("ec1"))
        assert max_ts.get_value(TimeId("t1")).to_float(ec_unit / TimeUnit.H) == pytest.approx(100.0)


# ============================================================================
# Tests for _parse_export_profiles() function
# ============================================================================


class TestParseExportProfiles:
    """Tests for _parse_export_profiles function"""

    def test_parse_export_profiles_empty_dataframe(self):
        """Test parsing with empty dataframe (no matching columns)"""
        df = MagicMock()
        df.columns = []

        exports = Exports()
        exports.add_tuple(StageId("s1"), HubId("h1"), EcId("ec1"), Unit.from_str("MWh"))

        # Should not raise exception
        import_export_parser._parse_export_profiles(
            df, "/test/profile.csv", StageId("s1"), HubId("h1"),
            EcId("ec1"), Unit.from_str("MWh"), exports
        )

    def test_parse_export_profiles_invalid_unit_raises_exception(self):
        """Test that invalid unit in profile raises ParsingException"""
        ec_unit = Unit.from_str("MWh")

        df = MagicMock()
        df.columns = [("s1", "h1", "ec1", "price")]
        df.attrs = {
            "unit": {("s1", "h1", "ec1", "price"): "INVALID_UNIT"}
        }

        exports = Exports()
        exports.add_tuple(StageId("s1"), HubId("h1"), EcId("ec1"), ec_unit)

        with pytest.raises(exceptions.ParsingException) as exc_info:
            import_export_parser._parse_export_profiles(
                df, "/test/profile.csv", StageId("s1"), HubId("h1"),
                EcId("ec1"), ec_unit, exports
            )

        # Verify exception message mentions invalid unit
        assert "invalid unit" in str(exc_info.value).lower()

    def test_parse_export_profiles_price_key(self):
        """Test parsing profile with price key"""
        ec_unit = Unit.from_str("MWh")

        df = MagicMock()
        df.columns = [("s1", "h1", "ec1", "price")]
        df.attrs = {
            "unit": {("s1", "h1", "ec1", "price"): "CHF/MWh"}
        }
        df.__getitem__ = Mock(return_value=pd.Series({
            "t1": 0.08
        }))

        exports = Exports()
        exports.add_tuple(StageId("s1"), HubId("h1"), EcId("ec1"), ec_unit)

        import_export_parser._parse_export_profiles(
            df, "/test/profile.csv", StageId("s1"), HubId("h1"),
            EcId("ec1"), ec_unit, exports
        )

        # Verify price was set
        price_ts = exports.get_price(StageId("s1"), HubId("h1"), EcId("ec1"))
        assert price_ts.get_value(TimeId("t1")).to_float(CurrencyUnit.CHF / ec_unit) == pytest.approx(0.08)


# ============================================================================
# Tests for logging functions
# ============================================================================


class TestLogging:
    """Tests for logging functions"""

    @patch("ehubx.core.logging.log_file")
    def test_log_imports(self, mock_log):
        """Test that _log_imports logs correctly"""
        imports = Imports()
        imports.add_tuple(StageId("s1"), HubId("h1"), EcId("ec1"), Unit.from_str("MWh"))
        imports.add_tuple(StageId("s2"), HubId("h2"), EcId("ec2"), Unit.from_str("MWh"))

        import_export_parser._log_imports(imports)

        # Should log at least twice (summary + tuples)
        assert mock_log.call_count >= 2

        # First call should mention count
        first_call = str(mock_log.call_args_list[0])
        assert "2" in first_call or "import" in first_call.lower()

    @patch("ehubx.core.logging.log_file")
    def test_log_exports(self, mock_log):
        """Test that _log_exports logs correctly"""
        exports = Exports()
        exports.add_tuple(StageId("s1"), HubId("h1"), EcId("ec1"), Unit.from_str("MWh"))

        import_export_parser._log_exports(exports)

        # Should log at least twice (summary + tuple)
        assert mock_log.call_count >= 2


# ============================================================================
# Tests for constants
# ============================================================================


class TestConstants:
    """Tests for module constants"""

    def test_yaml_keys(self):
        """Test that YAML key constants are defined correctly"""
        assert import_export_parser.YAMLKEY_STAGES == "stages"
        assert import_export_parser.YAMLKEY_HUBS == "hubs"
        assert import_export_parser.YAMLKEY_EC == "ec"
        assert import_export_parser.YAMLKEY_PRICE == "price"
        assert import_export_parser.YAMLKEY_CO2 == "co2"
        assert import_export_parser.YAMLKEY_MIN == "min"
        assert import_export_parser.YAMLKEY_MAX == "max"
        assert import_export_parser.YAMLKEY_SUMMIN == "sum_min"
        assert import_export_parser.YAMLKEY_SUMMAX == "sum_max"
        assert import_export_parser.YAMLKEY_PROFILEPATH == "profile_path"

    def test_file_constants(self):
        """Test that file name constants are defined correctly"""
        assert import_export_parser.FILE_IMPORTS == "imports.yaml"
        assert import_export_parser.FILE_EXPORTS == "exports.yaml"
        assert import_export_parser.FILETYPE_IMPEXPPROFILE == "import/export profile"

    def test_log_module_string(self):
        """Test that log module string is defined correctly"""
        assert import_export_parser.LOG_MODULE_STR == "pars/imp_exp"
