"""
Tests for hub_parser module
"""

import pytest
from unittest.mock import patch, call
from yaml import YAMLError

from ehubx.data.hub_data import HubId, Hubs
from ehubx.parser import hub_parser, exceptions, yaml_parser


def _write_yaml(tmp_path, name, content: str):
    """Helper to write YAML file"""
    path = tmp_path / name
    path.write_text(content)
    return path


# ============================================================================
# Tests for parse_primary() function
# ============================================================================


def test_parse_primary_missing_file_returns_empty_hubs(tmp_path):
    """Test that missing hubs.yaml file returns empty Hubs object and None"""
    hubs, root_node = hub_parser.parse_primary(str(tmp_path))

    assert isinstance(hubs, Hubs)
    assert len(hubs.ids) == 0
    assert root_node is None


def test_parse_primary_single_hub(tmp_path):
    """Test parsing a single hub"""
    yaml_content = """hubs:
  - hub_id: hub1
"""
    _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    hubs, root_node = hub_parser.parse_primary(str(tmp_path))

    assert isinstance(hubs, Hubs)
    assert len(hubs.ids) == 1
    hub_id = HubId("hub1")
    assert hub_id in hubs.ids
    assert root_node is not None


def test_parse_primary_multiple_hubs(tmp_path):
    """Test parsing multiple hubs"""
    yaml_content = """hubs:
  - hub_id: hub1
  - hub_id: hub2
  - hub_id: hub3
"""
    _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    hubs, root_node = hub_parser.parse_primary(str(tmp_path))

    assert isinstance(hubs, Hubs)
    assert len(hubs.ids) == 3
    assert HubId("hub1") in hubs.ids
    assert HubId("hub2") in hubs.ids
    assert HubId("hub3") in hubs.ids
    assert root_node is not None


def test_parse_primary_hubs_with_ids_in_order(tmp_path):
    """Test that hubs are added to the Hubs object"""
    yaml_content = """hubs:
  - hub_id: z_hub
  - hub_id: a_hub
  - hub_id: m_hub
"""
    _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    hubs, root_node = hub_parser.parse_primary(str(tmp_path))

    assert len(hubs.ids_in_order) == 3
    # ids_in_order should be alphabetically sorted
    hub_ids_sorted = [h.key for h in hubs.ids_in_order]
    assert hub_ids_sorted == ["a_hub", "m_hub", "z_hub"]


def test_parse_primary_duplicate_hub_id_raises_duplicateidexception(tmp_path):
    """Test that duplicate hub IDs raise DuplicateIdInYamlBlockListException"""
    yaml_content = """hubs:
  - hub_id: hub1
  - hub_id: hub1
"""
    _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    with pytest.raises(exceptions.DuplicateIdInYamlBlockListException) as exc_info:
        hub_parser.parse_primary(str(tmp_path))

    # The exception should mention the duplicate ID or hub
    error_msg = str(exc_info.value).lower()
    assert "duplicate" in error_msg or "hub1" in error_msg


def test_parse_primary_with_invalid_yaml_raises_exception(tmp_path):
    """Test that invalid YAML raises an exception"""
    # Create malformed YAML
    yaml_content = """hubs:
  - hub_id: hub1
    invalid: [unclosed"""
    _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    with pytest.raises(YAMLError):
        hub_parser.parse_primary(str(tmp_path))


def test_parse_primary_missing_hubs_key_returns_empty_hubs(tmp_path):
    """Test that YAML without 'hubs' key returns empty Hubs"""
    yaml_content = """other_key: value"""
    _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    hubs, root_node = hub_parser.parse_primary(str(tmp_path))

    assert isinstance(hubs, Hubs)
    assert len(hubs.ids) == 0
    assert root_node is not None


def test_parse_primary_empty_hubs_list(tmp_path):
    """Test parsing with empty hubs list"""
    yaml_content = """hubs: []
"""
    _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    hubs, root_node = hub_parser.parse_primary(str(tmp_path))

    assert isinstance(hubs, Hubs)
    assert len(hubs.ids) == 0
    assert root_node is not None


def test_parse_primary_hubs_not_list_raises_exception(tmp_path):
    """Test that non-list 'hubs' value raises InvalidNodeTypeException"""
    yaml_content = """hubs:
  hub_id: hub1
"""
    _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    with pytest.raises(exceptions.InvalidNodeTypeException) as exc_info:
        hub_parser.parse_primary(str(tmp_path))

    assert "hubs" in str(exc_info.value).lower() or "list" in str(exc_info.value).lower()


def test_parse_primary_missing_hub_id_raises_exception(tmp_path):
    """Test that missing hub_id field raises exception"""
    yaml_content = """hubs:
  - other_field: value
"""
    _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    with pytest.raises(exceptions.MissingNodeException):
        hub_parser.parse_primary(str(tmp_path))


def test_parse_primary_hub_id_is_none_raises_exception(tmp_path):
    """Test that null hub_id value raises MissingValueException"""
    yaml_content = """hubs:
  - hub_id:
"""
    _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    with pytest.raises(exceptions.MissingValueException) as exc_info:
        hub_parser.parse_primary(str(tmp_path))

    assert "hub_id" in str(exc_info.value).lower() or "value" in str(exc_info.value).lower()


def test_parse_primary_root_node_parse_fails_returns_empty_and_none(tmp_path):
    """Test that if YAML parsing fails to produce root node, returns empty hubs and None"""
    yaml_content = ""
    _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    hubs, root_node = hub_parser.parse_primary(str(tmp_path))

    assert isinstance(hubs, Hubs)
    # Empty file should parse to None, but shouldn't crash
    assert len(hubs.ids) == 0
    assert root_node is None


def test_parse_primary_hub_with_extra_fields_ignored(tmp_path):
    """Test that extra fields in hub definition are ignored"""
    yaml_content = """hubs:
  - hub_id: hub1
    extra_field: extra_value
    another_field: another_value
"""
    _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    hubs, root_node = hub_parser.parse_primary(str(tmp_path))

    # Should only process hub_id
    assert len(hubs.ids) == 1
    assert HubId("hub1") in hubs.ids


def test_parse_primary_hub_id_with_special_characters(tmp_path):
    """Test parsing hub IDs with special characters"""
    yaml_content = """hubs:
  - hub_id: hub-1_test.123
"""
    _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    hubs, root_node = hub_parser.parse_primary(str(tmp_path))

    assert len(hubs.ids) == 1
    assert HubId("hub-1_test.123") in hubs.ids


def test_parse_primary_large_number_of_hubs(tmp_path):
    """Test parsing a large number of hubs"""
    yaml_lines = ["hubs:"]
    num_hubs = 100
    for i in range(num_hubs):
        yaml_lines.append(f"  - hub_id: hub_{i:03d}")

    yaml_content = "\n".join(yaml_lines)
    _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    hubs, root_node = hub_parser.parse_primary(str(tmp_path))

    assert len(hubs.ids) == num_hubs
    for i in range(num_hubs):
        assert HubId(f"hub_{i:03d}") in hubs.ids


def test_parse_primary_whitespace_in_hub_id(tmp_path):
    """Test that hub IDs with whitespace are accepted"""
    yaml_content = """hubs:
  - hub_id: "hub with spaces"
"""
    _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    hubs, root_node = hub_parser.parse_primary(str(tmp_path))

    assert len(hubs.ids) == 1
    assert HubId("hub with spaces") in hubs.ids


def test_parse_primary_exception_includes_file_path(tmp_path):
    """Test that exceptions include the file path"""
    yaml_content = """hubs:
  hub_id: hub1
"""
    yaml_path = _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    with pytest.raises(Exception) as exc_info:
        hub_parser.parse_primary(str(tmp_path))

    # File path should be in the exception
    error_msg = str(exc_info.value)
    assert str(yaml_path) in error_msg or "hubs.yaml" in error_msg


def test_parse_primary_returns_tuple(tmp_path):
    """Test that parse_primary returns a tuple of (Hubs, Optional[YamlNode])"""
    yaml_content = """hubs:
  - hub_id: hub1
"""
    _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    result = hub_parser.parse_primary(str(tmp_path))

    assert isinstance(result, tuple)
    assert len(result) == 2
    hubs, root_node = result
    assert isinstance(hubs, Hubs)
    assert root_node is None or isinstance(root_node, yaml_parser.YamlNode)


def test_parse_primary_logging_called_on_success(tmp_path):
    """Test that logging is called after successful parsing"""
    yaml_content = """hubs:
  - hub_id: hub1
  - hub_id: hub2
"""
    _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    # Mock the logging.log_file function to verify it's called
    with patch("ehubx.core.logging.log_file") as mock_log:
        hubs, root_node = hub_parser.parse_primary(str(tmp_path))

    assert len(hubs.ids) == 2
    # Verify that logging.log_file was called
    assert mock_log.called, "logging.log_file should have been called"
    # Verify the logged message contains information about parsed hubs
    call_args = mock_log.call_args[0][0]  # Get the first positional argument
    assert "Parsed" in call_args and "2" in call_args and "hub" in call_args.lower()


def test_parse_primary_numeric_hub_id(tmp_path):
    """Test parsing numeric hub IDs"""
    yaml_content = """hubs:
  - hub_id: "123"
  - hub_id: "456"
"""
    _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    hubs, root_node = hub_parser.parse_primary(str(tmp_path))

    assert len(hubs.ids) == 2
    assert HubId("123") in hubs.ids
    assert HubId("456") in hubs.ids


# ============================================================================
# Edge cases and error conditions
# ============================================================================

def test_parse_primary_hub_id_empty_string(tmp_path):
    """Test parsing with empty string hub ID"""
    yaml_content = """hubs:
  - hub_id: ""
"""
    _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    hubs, root_node = hub_parser.parse_primary(str(tmp_path))

    # Empty string should be a valid hub ID
    assert len(hubs.ids) == 1
    assert HubId("") in hubs.ids


def test_parse_primary_hubs_yaml_in_subdirectory(tmp_path):
    """Test that only hubs.yaml in the specified directory is used"""
    # Create hubs.yaml in a subdirectory
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    yaml_content = """hubs:
  - hub_id: hub_in_subdir
"""
    _write_yaml(subdir, "hubs.yaml", yaml_content)

    # Parse from the main directory (no file there)
    hubs, root_node = hub_parser.parse_primary(str(tmp_path))

    # Should return empty since hubs.yaml is not in tmp_path
    assert len(hubs.ids) == 0
    assert root_node is None

    # Parse from subdirectory should find the file
    hubs_sub, root_node_sub = hub_parser.parse_primary(str(subdir))
    assert len(hubs_sub.ids) == 1
    assert HubId("hub_in_subdir") in hubs_sub.ids


def test_parse_primary_duplicate_then_unique_ids(tmp_path):
    """Test that duplicate detection works even with subsequent unique IDs"""
    yaml_content = """hubs:
  - hub_id: hub1
  - hub_id: hub2
  - hub_id: hub1
  - hub_id: hub3
"""
    _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    with pytest.raises(exceptions.DuplicateIdInYamlBlockListException) as exc_info:
        hub_parser.parse_primary(str(tmp_path))

    error_msg = str(exc_info.value).lower()
    assert "duplicate" in error_msg or "hub1" in error_msg


# ============================================================================
# Additional branch coverage tests
# ============================================================================

def test_parse_primary_single_hub_ids_in_order(tmp_path):
    """Test ids_in_order with single hub"""
    yaml_content = """hubs:
  - hub_id: single_hub
"""
    _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    hubs, root_node = hub_parser.parse_primary(str(tmp_path))

    ids_ordered = hubs.ids_in_order
    assert len(ids_ordered) == 1
    assert ids_ordered[0].key == "single_hub"


def test_parse_primary_hub_id_case_sensitive(tmp_path):
    """Test that hub IDs are case-sensitive"""
    yaml_content = """hubs:
  - hub_id: HUB1
  - hub_id: hub1
  - hub_id: Hub1
"""
    _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    hubs, root_node = hub_parser.parse_primary(str(tmp_path))

    # All three should be treated as different hubs
    assert len(hubs.ids) == 3
    assert HubId("HUB1") in hubs.ids
    assert HubId("hub1") in hubs.ids
    assert HubId("Hub1") in hubs.ids


def test_parse_primary_returns_same_hubs_object_reference(tmp_path):
    """Test that returned Hubs object contains the correct data"""
    yaml_content = """hubs:
  - hub_id: test_hub
"""
    _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    hubs1, _ = hub_parser.parse_primary(str(tmp_path))
    hubs2, _ = hub_parser.parse_primary(str(tmp_path))

    # Two separate calls should return different Hubs objects
    assert hubs1 is not hubs2
    # But they should have the same content
    assert len(hubs1.ids) == len(hubs2.ids)
    assert HubId("test_hub") in hubs1.ids
    assert HubId("test_hub") in hubs2.ids


def test_parse_primary_complex_hub_id_underscore_dash_dot(tmp_path):
    """Test hub IDs with complex naming using underscores, dashes, and dots"""
    yaml_content = """hubs:
  - hub_id: hub_name-01.v2
  - hub_id: _hub._test.data-01
  - hub_id: ...
  - hub_id: ___---...
"""
    _write_yaml(tmp_path, "hubs.yaml", yaml_content)

    hubs, root_node = hub_parser.parse_primary(str(tmp_path))

    assert len(hubs.ids) == 4
    assert HubId("hub_name-01.v2") in hubs.ids
    assert HubId("_hub._test.data-01") in hubs.ids
    assert HubId("...") in hubs.ids
    assert HubId("___---...") in hubs.ids
