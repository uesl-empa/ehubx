from unittest.mock import MagicMock, patch

import pytest

from ehubx.data import exceptions as data_exceptions
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.stor_tech_data import ExceptionKey as StorTechExcKey, StorageTechs
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.unit import DimlessUnit, TimeUnit
from ehubx.data.value import Value
from ehubx.parser import stor_tech_parser, tech_parser, yaml_parser


# ==========================================================================
# Fixtures
# ==========================================================================


@pytest.fixture
def stages():
    return MagicMock(spec=Stages)


@pytest.fixture
def ecs():
    mock_ecs = MagicMock(spec=Ecs)
    mock_ecs.get_unit.return_value = DimlessUnit()
    return mock_ecs


@pytest.fixture
def techs():
    return MagicMock(spec=Techs)


# ==========================================================================
# Tests for parse_primary()
# ==========================================================================


@pytest.mark.parametrize("root_node", [None, MagicMock(__getitem__=lambda self, k: None)])
def test_parse_primary_empty_cases(root_node, stages, ecs, techs):
    stor_techs = stor_tech_parser.parse_primary(root_node, stages, ecs, techs)

    assert isinstance(stor_techs, StorageTechs)
    assert len(stor_techs.ids) == 0


def test_parse_primary_calls_parse_for_each_node(stages, ecs, techs):
    root = MagicMock()
    tech_node = MagicMock()
    techs_node = MagicMock(__iter__=lambda self: iter([tech_node]))
    root.__getitem__.return_value = techs_node

    with patch("ehubx.parser.stor_tech_parser._parse_stor_tech_primary") as mock_parse:
        stor_techs = stor_tech_parser.parse_primary(root, stages, ecs, techs)

    assert isinstance(stor_techs, StorageTechs)
    mock_parse.assert_called_once_with(tech_node, stages, ecs, techs, stor_techs)


# ==========================================================================
# Tests for _parse_stor_tech_primary()
# ==========================================================================


def test_parse_stor_tech_primary_skips_non_storage_type(stages, ecs, techs):
    tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
    stor_techs = StorageTechs()

    with patch(
        "ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node",
        return_value="stor1",
    ), patch(
        "ehubx.parser.yaml_parser.parse_optional_str_from_dict_node",
        return_value="conversion",
    ):
        stor_tech_parser._parse_stor_tech_primary(tech_node, stages, ecs, techs, stor_techs)

    assert TechId("stor1") not in stor_techs.ids
    techs.set_cap_unit.assert_not_called()


def test_parse_stor_tech_primary_sets_params(stages, ecs, techs):
    tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
    storage_params_node = MagicMock(spec=yaml_parser.YamlDictNode)
    stor_techs = StorageTechs()
    stage_id = StageId("S1")

    in_eff = {stage_id: Value(0.9, DimlessUnit())}
    out_eff = {stage_id: Value(0.8, DimlessUnit())}
    charge_max = {stage_id: Value(0.2, DimlessUnit() / TimeUnit.H)}
    discharge_max = {stage_id: Value(0.3, DimlessUnit() / TimeUnit.H)}
    standby_loss = {stage_id: Value(0.01, DimlessUnit() / TimeUnit.H)}
    soc_min = {stage_id: Value(0.1, DimlessUnit())}
    soc_max = {stage_id: Value(0.95, DimlessUnit())}

    with patch(
        "ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node",
        side_effect=["stor1", "EC1"],
    ), patch(
        "ehubx.parser.yaml_parser.parse_optional_str_from_dict_node",
        return_value=tech_parser.TechType.STORAGE.value,
    ), patch(
        "ehubx.parser.yaml_parser.get_mandatory_subnode_from_dict_node",
        return_value=storage_params_node,
    ), patch(
        "ehubx.parser.yaml_parser.check_node_type"
    ), patch(
        "ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node",
        side_effect=[
            in_eff,
            out_eff,
            charge_max,
            discharge_max,
            standby_loss,
            soc_min,
            soc_max,
        ],
    ):
        stor_tech_parser._parse_stor_tech_primary(tech_node, stages, ecs, techs, stor_techs)

    tech_id = TechId("stor1")
    assert tech_id in stor_techs.ids
    assert stor_techs.get_ec(tech_id) == EcId("EC1")
    techs.set_cap_unit.assert_called_once_with(tech_id, ecs.get_unit(EcId("EC1")))

    assert stor_techs.get_in_eff(stage_id, tech_id).to_float(DimlessUnit()) == pytest.approx(0.9)
    assert stor_techs.get_out_eff(stage_id, tech_id).to_float(DimlessUnit()) == pytest.approx(0.8)
    assert (
        stor_techs.get_charge_max(stage_id, tech_id).to_float(DimlessUnit() / TimeUnit.H)
        == pytest.approx(0.2)
    )
    assert (
        stor_techs.get_discharge_max(stage_id, tech_id).to_float(DimlessUnit() / TimeUnit.H)
        == pytest.approx(0.3)
    )
    assert (
        stor_techs.get_standby_loss(stage_id, tech_id).to_float(DimlessUnit() / TimeUnit.H)
        == pytest.approx(0.01)
    )
    assert stor_techs.get_soc_min(stage_id, tech_id).to_float(DimlessUnit()) == pytest.approx(0.1)
    assert stor_techs.get_soc_max(stage_id, tech_id).to_float(DimlessUnit()) == pytest.approx(0.95)


def test_parse_stor_tech_primary_duplicate_id_raises_exception_key(stages, ecs, techs):
    tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
    stor_techs = StorageTechs()
    stor_techs.add_id(TechId("stor1"))

    with patch(
        "ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node",
        return_value="stor1",
    ), patch(
        "ehubx.parser.yaml_parser.parse_optional_str_from_dict_node",
        return_value=tech_parser.TechType.STORAGE.value,
    ):
        with pytest.raises(data_exceptions.DuplicateIdException) as excinfo:
            stor_tech_parser._parse_stor_tech_primary(
                tech_node, stages, ecs, techs, stor_techs
            )

    assert excinfo.value.key == StorTechExcKey.ID_ADD.value


# ==========================================================================
# Tests for parse_secondary()
# ==========================================================================


@pytest.mark.parametrize("root_node", [None, MagicMock(__getitem__=lambda self, k: None)])
def test_parse_secondary_empty_cases(root_node):
    with patch("ehubx.parser.stor_tech_parser._parse_hub_secondary") as mock_parse:
        stor_tech_parser.parse_secondary(root_node, StorageTechs())  # should not raise
    mock_parse.assert_not_called()


def test_parse_secondary_calls_parse_hub(stages):
    root = MagicMock()
    hub_node = MagicMock()
    hubs_node = MagicMock(__iter__=lambda self: iter([hub_node]))
    root.__getitem__.return_value = hubs_node

    with patch("ehubx.parser.stor_tech_parser._parse_hub_secondary") as mock_parse:
        stor_tech_parser.parse_secondary(root, StorageTechs())

    mock_parse.assert_called_once()
    args = mock_parse.call_args[0]
    assert args[0] == hub_node
    assert isinstance(args[1], StorageTechs)


# ==========================================================================
# Tests for _parse_hub_secondary()
# ==========================================================================


def test_parse_hub_secondary_returns_when_no_techs_node():
    hub_node = MagicMock(spec=yaml_parser.YamlDictNode)
    hub_node.__getitem__.return_value = None

    with patch(
        "ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node",
        return_value="hub1",
    ), patch("ehubx.parser.stor_tech_parser._parse_tech_secondary") as mock_parse:
        stor_tech_parser._parse_hub_secondary(hub_node, StorageTechs())
    mock_parse.assert_not_called()


def test_parse_hub_secondary_calls_parse_tech_secondary():
    hub_node = MagicMock(spec=yaml_parser.YamlDictNode)
    techs_node = MagicMock()
    techs_node.__getitem__.return_value = MagicMock()
    hub_node.__getitem__.return_value = techs_node
    stor_techs = StorageTechs()
    stor_techs.add_id(TechId("stor1"))

    with patch(
        "ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node",
        return_value="hub1",
    ), patch("ehubx.parser.stor_tech_parser._parse_tech_secondary") as mock_parse:
        stor_tech_parser._parse_hub_secondary(hub_node, stor_techs)

    mock_parse.assert_called_once()


def test_parse_hub_secondary_skips_missing_tech_node():
    hub_node = MagicMock(spec=yaml_parser.YamlDictNode)
    techs_node = MagicMock(__getitem__=lambda self, k: None)
    hub_node.__getitem__.return_value = techs_node
    stor_techs = StorageTechs()
    stor_techs.add_id(TechId("stor1"))

    with patch(
        "ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node",
        return_value="hub1",
    ), patch("ehubx.parser.stor_tech_parser._parse_tech_secondary") as mock_parse:
        stor_tech_parser._parse_hub_secondary(hub_node, stor_techs)
    mock_parse.assert_not_called()


# ==========================================================================
# Tests for _parse_tech_secondary()
# ==========================================================================


def test_parse_tech_secondary_returns_when_no_storage_params():
    tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
    tech_node.__getitem__.return_value = None
    with patch("ehubx.data.stor_tech_data.StorageTechs.set_soc_init") as mock_set_soc_init:
        stor_tech_parser._parse_tech_secondary(
            tech_node, HubId("H1"), TechId("stor1"), StorageTechs()
        )
    mock_set_soc_init.assert_not_called()


def test_parse_tech_secondary_sets_soc_init():
    tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
    storage_params_node = MagicMock(spec=yaml_parser.YamlDictNode)
    tech_node.__getitem__.return_value = storage_params_node

    stor_techs = StorageTechs()
    tech_id = TechId("stor1")
    hub_id = HubId("H1")
    stor_techs.add_id(tech_id)

    soc_init = Value(0.4, DimlessUnit())

    with patch("ehubx.parser.yaml_parser.check_node_type"), patch(
        "ehubx.parser.yaml_parser.parse_optional_value_from_dict_node",
        return_value=soc_init,
    ):
        stor_tech_parser._parse_tech_secondary(tech_node, hub_id, tech_id, stor_techs)

    assert stor_techs.get_soc_init(hub_id, tech_id).to_float(DimlessUnit()) == pytest.approx(0.4)


def test_parse_tech_secondary_invalid_soc_init_unit_raises_exception_key():
    tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
    storage_params_node = MagicMock(spec=yaml_parser.YamlDictNode)
    tech_node.__getitem__.return_value = storage_params_node

    stor_techs = StorageTechs()
    tech_id = TechId("stor1")
    hub_id = HubId("H1")
    stor_techs.add_id(tech_id)

    bad_soc_init = Value(1.0, TimeUnit.H)

    with patch("ehubx.parser.yaml_parser.check_node_type"), patch(
        "ehubx.parser.yaml_parser.parse_optional_value_from_dict_node",
        return_value=bad_soc_init,
    ):
        with pytest.raises(data_exceptions.DataException) as excinfo:
            stor_tech_parser._parse_tech_secondary(
                tech_node, hub_id, tech_id, stor_techs
            )

    assert excinfo.value.key == StorTechExcKey.SOCINIT_SET.value
