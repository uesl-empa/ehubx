from unittest.mock import MagicMock, patch

import pytest

from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId
from ehubx.data.solar_tech_data import ExceptionKey as SolarTechExcKey, SolarTechs
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.time_data import TimeId
from ehubx.data.unit import DimlessUnit, LengthUnit, Unit
from ehubx.data.value import Value
from ehubx.parser import exceptions, solar_parser, tech_parser
from ehubx.data import exceptions as data_exceptions


# ==========================================================================
# Helpers
# ==========================================================================


def _write_csv(tmp_path, name, lines):
    path = tmp_path / name
    path.write_text("\n".join(lines))
    return str(path)


# ==========================================================================
# Fixtures
# ==========================================================================


@pytest.fixture
def stages():
    return MagicMock(spec=Stages)


@pytest.fixture
def techs():
    return MagicMock(spec=Techs)


@pytest.fixture
def ecs():
    mock_ecs = MagicMock(spec=Ecs)
    mock_ecs.get_unit.return_value = Unit.from_str("MWh")
    return mock_ecs


# ==========================================================================
# Tests for parse_techs()
# ==========================================================================


def test_parse_techs_returns_empty_on_none_root(stages, techs):
    solar_techs = solar_parser.parse_techs(None, stages, techs)

    assert isinstance(solar_techs, SolarTechs)
    assert len(solar_techs.ids) == 0


def test_parse_techs_returns_empty_on_none_techs_node(stages, techs):
    root = MagicMock()
    root.__getitem__.return_value = None

    solar_techs = solar_parser.parse_techs(root, stages, techs)

    assert isinstance(solar_techs, SolarTechs)
    assert len(solar_techs.ids) == 0


def test_parse_techs_calls_parse_for_each_node(stages, techs):
    root = MagicMock()
    tech_node = MagicMock()
    techs_node = MagicMock()
    techs_node.__iter__ = MagicMock(return_value=iter([tech_node]))
    root.__getitem__.return_value = techs_node

    with patch("ehubx.parser.solar_parser._parse_tech") as mock_parse:
        solar_techs = solar_parser.parse_techs(root, stages, techs)

    assert isinstance(solar_techs, SolarTechs)
    mock_parse.assert_called_once_with(tech_node, stages, techs, solar_techs)


# ==========================================================================
# Tests for _parse_tech()
# ==========================================================================


def test_parse_tech_skips_non_solar_type(stages, techs):
    tech_node = MagicMock()
    solar_techs = SolarTechs()

    with patch(
        "ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node",
        return_value="t1",
    ), patch(
        "ehubx.parser.yaml_parser.parse_optional_str_from_dict_node",
        return_value="conversion",
    ):
        solar_parser._parse_tech(tech_node, stages, techs, solar_techs)

    assert TechId("t1") not in solar_techs.ids
    techs.set_cap_unit.assert_not_called()


def test_parse_tech_solar_without_params_adds_id(stages, techs):
    tech_node = MagicMock()
    tech_node.__getitem__.return_value = None
    solar_techs = SolarTechs()

    with patch(
        "ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node",
        return_value="solar1",
    ), patch(
        "ehubx.parser.yaml_parser.parse_optional_str_from_dict_node",
        return_value=tech_parser.TechType.SOLAR.value,
    ):
        solar_parser._parse_tech(tech_node, stages, techs, solar_techs)

    assert TechId("solar1") in solar_techs.ids
    techs.set_cap_unit.assert_called_once_with(TechId("solar1"), LengthUnit.M**2)


def test_parse_tech_sets_curtail_max_rel(stages, techs):
    tech_node = MagicMock()
    solar_params_node = MagicMock()
    tech_node.__getitem__.return_value = solar_params_node
    solar_techs = SolarTechs()
    stage_id = StageId("S1")

    with patch(
        "ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node",
        return_value="solar2",
    ), patch(
        "ehubx.parser.yaml_parser.parse_optional_str_from_dict_node",
        return_value=tech_parser.TechType.SOLAR.value,
    ), patch(
        "ehubx.parser.yaml_parser.check_node_type"
    ), patch(
        "ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node",
        return_value={stage_id: Value(0.4, DimlessUnit())},
    ):
        solar_parser._parse_tech(tech_node, stages, techs, solar_techs)

    value = solar_techs.get_curtail_max_rel(stage_id, TechId("solar2"))
    assert value.to_float(DimlessUnit()) == pytest.approx(0.4)


def test_parse_tech_duplicate_id_raises_exception_key(stages, techs):
    tech_node = MagicMock()
    tech_node.__getitem__.return_value = None
    solar_techs = SolarTechs()
    solar_techs.add_id(TechId("solar1"))

    with patch(
        "ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node",
        return_value="solar1",
    ), patch(
        "ehubx.parser.yaml_parser.parse_optional_str_from_dict_node",
        return_value=tech_parser.TechType.SOLAR.value,
    ):
        with pytest.raises(data_exceptions.DuplicateIdException) as excinfo:
            solar_parser._parse_tech(tech_node, stages, techs, solar_techs)

    assert excinfo.value.key == SolarTechExcKey.ID_ADD.value


# ==========================================================================
# Tests for parse_data()
# ==========================================================================


def test_parse_data_returns_empty_when_files_missing(tmp_path, ecs):
    solar_data = solar_parser.parse_data(str(tmp_path), ecs)

    assert len(solar_data.ecs) == 0


def test_parse_data_reads_area_and_irradiation(tmp_path, ecs):
    _write_csv(
        tmp_path,
        solar_parser.FILENAME_SOLARAREAS,
        [
            "stage_id,S1",
            "hub_id,H1",
            "unit,km^2",
            "E1,0.1",
        ],
    )
    _write_csv(
        tmp_path,
        solar_parser.FILENAME_SOLARIRRADIATION,
        [
            "stage_id,S1",
            "ec_id,E1",
            "unit,kW/m^2",
            "1,2",
            "2,3",
        ],
    )

    solar_data = solar_parser.parse_data(str(tmp_path), ecs)

    assert EcId("E1") in solar_data.ecs
    area = solar_data.get_area(StageId("S1"), HubId("H1"), EcId("E1"))
    assert area.to_float(LengthUnit.M**2) == pytest.approx(100000)

    series = solar_data.get_irradiation(StageId("S1"), EcId("E1"))
    value_t1 = series.get_value(TimeId("1"))
    assert value_t1.to_float(Unit.from_str("kW/m^2")) == pytest.approx(2)


def test_parse_data_invalid_area_unit_string_raises(tmp_path, ecs):
    _write_csv(
        tmp_path,
        solar_parser.FILENAME_SOLARAREAS,
        [
            "stage_id,S1",
            "hub_id,H1",
            "unit,invalid_unit",
            "E1,1",
        ],
    )

    with pytest.raises(exceptions.ParsingException) as excinfo:
        solar_parser.parse_data(str(tmp_path), ecs)

    assert "Invalid unit" in str(excinfo.value)


def test_parse_data_invalid_area_unit_type_raises(tmp_path, ecs):
    _write_csv(
        tmp_path,
        solar_parser.FILENAME_SOLARAREAS,
        [
            "stage_id,S1",
            "hub_id,H1",
            "unit,kW",
            "E1,1",
        ],
    )

    with pytest.raises(exceptions.ParsingException) as excinfo:
        solar_parser.parse_data(str(tmp_path), ecs)

    assert "Expected a unit like" in str(excinfo.value)


def test_parse_data_invalid_irradiation_unit_type_raises(tmp_path, ecs):
    _write_csv(
        tmp_path,
        solar_parser.FILENAME_SOLARIRRADIATION,
        [
            "stage_id,S1",
            "ec_id,E1",
            "unit,m^2",
            "1,2",
        ],
    )

    with pytest.raises(exceptions.ParsingException) as excinfo:
        solar_parser.parse_data(str(tmp_path), ecs)

    assert "Expected a unit like" in str(excinfo.value)
