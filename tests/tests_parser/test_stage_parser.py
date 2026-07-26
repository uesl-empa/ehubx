"""
Tests for stage_parser module
"""

import pytest
from yaml import YAMLError

from ehubx.data.stage_data import (
    ExceptionKey as StageExceptionKey,
    StageId,
    Stages,
    DEF_CO2_MIN,
    DEF_CO2_MAX,
)
from ehubx.data.unit import CurrencyUnit, MassUnit
from ehubx.data.value import Value
from ehubx.data import exceptions as data_exceptions
from ehubx.parser import stage_parser, exceptions, yaml_parser


def _write_yaml(tmp_path, name, content: str):
    """Helper to write YAML file"""
    path = tmp_path / name
    path.write_text(content)
    return path


# ============================================================================
# Tests for parse() function - main entry point
# ============================================================================


def test_parse_missing_file_returns_empty_stages(tmp_path):
    stages, root_node = stage_parser.parse(str(tmp_path))

    assert isinstance(stages, Stages)
    assert len(stages.ids) == 0
    assert root_node is None


def test_parse_empty_file_returns_empty_stages(tmp_path):
    _write_yaml(tmp_path, "stages.yaml", "")

    stages, root_node = stage_parser.parse(str(tmp_path))

    assert isinstance(stages, Stages)
    assert len(stages.ids) == 0
    assert root_node is None


def test_parse_missing_stages_key_returns_empty(tmp_path):
    _write_yaml(tmp_path, "stages.yaml", "other_key: value")

    stages, root_node = stage_parser.parse(str(tmp_path))

    assert isinstance(stages, Stages)
    assert len(stages.ids) == 0
    assert root_node is not None


def test_parse_stages_not_list_raises_exception(tmp_path):
    _write_yaml(
        tmp_path,
        "stages.yaml",
        """stages:
  stage_id: s1
  start_year: 2020
""",
    )

    with pytest.raises(exceptions.InvalidNodeTypeException):
        stage_parser.parse(str(tmp_path))


def test_parse_missing_stage_id_raises_exception(tmp_path):
    _write_yaml(
        tmp_path,
        "stages.yaml",
        """stages:
  - start_year: 2020
""",
    )

    with pytest.raises(exceptions.MissingNodeException):
        stage_parser.parse(str(tmp_path))


def test_parse_stage_id_null_raises_exception(tmp_path):
    _write_yaml(
        tmp_path,
        "stages.yaml",
        """stages:
  - stage_id:
    start_year: 2020
""",
    )

    with pytest.raises(exceptions.MissingValueException):
        stage_parser.parse(str(tmp_path))


def test_parse_missing_start_year_raises_exception(tmp_path):
    _write_yaml(
        tmp_path,
        "stages.yaml",
        """stages:
  - stage_id: s1
""",
    )

    with pytest.raises(exceptions.MissingNodeException):
        stage_parser.parse(str(tmp_path))


def test_parse_start_year_null_raises_exception(tmp_path):
    _write_yaml(
        tmp_path,
        "stages.yaml",
        """stages:
  - stage_id: s1
    start_year:
""",
    )

    with pytest.raises(exceptions.MissingValueException):
        stage_parser.parse(str(tmp_path))


def test_parse_duplicate_stage_id_raises_exception(tmp_path):
    _write_yaml(
        tmp_path,
        "stages.yaml",
        """stages:
  - stage_id: s1
    start_year: 2020
  - stage_id: s1
    start_year: 2030
""",
    )

    with pytest.raises(exceptions.DuplicateIdInYamlBlockListException):
        stage_parser.parse(str(tmp_path))


def test_parse_invalid_yaml_raises_yamLError(tmp_path):
    _write_yaml(
        tmp_path,
        "stages.yaml",
        """stages:
  - stage_id: s1
    start_year: 2020
    co2_price: [unterminated
""",
    )

    with pytest.raises(YAMLError):
        stage_parser.parse(str(tmp_path))


def test_parse_basic_stage_with_optional_fields(tmp_path):
    _write_yaml(
        tmp_path,
        "stages.yaml",
        """stages:
  - stage_id: s2
    start_year: 2030
    co2_price: 10 CHF/kg
    co2_min: 5 kg
    co2_max: 20 kg
  - stage_id: s1
    start_year: 2020
    co2_price: 0 CHF/kg
""",
    )

    stages, root_node = stage_parser.parse(str(tmp_path))

    assert root_node is not None
    assert len(stages.ids) == 2
    assert StageId("s1") in stages.ids
    assert StageId("s2") in stages.ids

    # ids_in_order sorted by start_year
    ids_in_order = [s.key for s in stages.ids_in_order]
    assert ids_in_order == ["s1", "s2"]

    # Check parsed values
    assert stages.get_start_year(StageId("s1")) == 2020
    assert stages.get_start_year(StageId("s2")) == 2030
    assert stages.get_co2_price(StageId("s2")) == Value(
        10, CurrencyUnit.CHF / MassUnit.KG
    )
    assert stages.get_co2_min(StageId("s2")) == Value(5, MassUnit.KG)
    assert stages.get_co2_max(StageId("s2")) == Value(20, MassUnit.KG)


def test_parse_optional_fields_default_when_blank(tmp_path):
    _write_yaml(
        tmp_path,
        "stages.yaml",
        """stages:
  - stage_id: s1
    start_year: 2020
    co2_min:
    co2_max:
""",
    )

    stages, _ = stage_parser.parse(str(tmp_path))

    s1 = StageId("s1")
    assert stages.get_co2_price(s1) == Value(0, CurrencyUnit.CHF / MassUnit.KG)
    assert stages.get_co2_min(s1) == Value(DEF_CO2_MIN, MassUnit.KG)
    assert stages.get_co2_max(s1) == Value(DEF_CO2_MAX, MassUnit.KG)


def test_parse_invalid_co2_price_unit_raises_exception(tmp_path):
    _write_yaml(
        tmp_path,
        "stages.yaml",
        """stages:
  - stage_id: s1
    start_year: 2020
    co2_price: 10 kg
""",
    )

    with pytest.raises(exceptions.InvalidValueException):
        stage_parser.parse(str(tmp_path))


# ============================================================================
# Tests for _parse_stage() helper
# ============================================================================


def test_parse_stage_duplicate_id_raises_data_exception_key(tmp_path):
    _write_yaml(
        tmp_path,
        "stages.yaml",
        """stages:
  - stage_id: s1
    start_year: 2020
""",
    )

    root = yaml_parser.parse(str(tmp_path / "stages.yaml"))
    stages_node = root[stage_parser.YAMLKEY_STAGES]
    stage_node = next(iter(stages_node))

    stages = Stages()
    stage_parser._parse_stage(stage_node, stages)

    with pytest.raises(data_exceptions.DuplicateIdException) as exc_info:
        stage_parser._parse_stage(stage_node, stages)

    assert exc_info.value.key == StageExceptionKey.ID_ADD.value
