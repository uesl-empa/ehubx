import pytest
from unittest.mock import MagicMock, patch

from ehubx.data import exceptions as data_exceptions
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId
from ehubx.data.tech_data import ExceptionKey as TechExcKey, TechId, Techs
from ehubx.data.unit import CurrencyUnit, DimlessUnit, MassUnit, TimeUnit
from ehubx.data.value import Value
from ehubx.parser import exceptions, tech_parser, yaml_parser


# ==========================================================================
# Helpers
# ==========================================================================


def _make_tech_node(file_path: str, tech_id: str) -> yaml_parser.YamlDictNode:
    node = yaml_parser.YamlDictNode(file_path)
    node.add_child_value(tech_parser.YAMLKEY_TECHID, tech_id)
    return node


def _make_coupled_node(
    file_path: str,
    tech_id: str,
    main_tech_id: str,
    with_tech_params: bool = False,
) -> yaml_parser.YamlDictNode:
    node = _make_tech_node(file_path, tech_id)
    coupling = yaml_parser.YamlDictNode(file_path)
    coupling.add_child_value(tech_parser.YAMLKEY_MAINTECHID, main_tech_id)
    node.add_dict_child(tech_parser.YAMLKEY_COUPLINGPARAMS, coupling)
    if with_tech_params:
        node.add_dict_child(tech_parser.YAMLKEY_TECHPARAMS, yaml_parser.YamlDictNode(file_path))
    return node


# ==========================================================================
# parse_initial
# ==========================================================================


def test_parse_initial_returns_empty_when_file_missing():
    with patch("ehubx.parser.yaml_parser.parse", return_value=None):
        techs, root = tech_parser.parse_initial("/tmp")

    assert isinstance(techs, Techs)
    assert len(techs.ids) == 0
    assert root is None


def test_parse_initial_skips_missing_techs_node():
    root = MagicMock()
    root.__getitem__.return_value = None

    with patch("ehubx.parser.yaml_parser.parse", return_value=root), patch(
        "ehubx.parser.yaml_parser.check_node_type"
    ):
        techs, root_out = tech_parser.parse_initial("/tmp")

    assert isinstance(techs, Techs)
    assert root_out is root
    assert len(techs.ids) == 0


def test_parse_initial_calls_preprocess_and_parse_initial():
    root = MagicMock()
    tech_node = MagicMock()
    techs_node = MagicMock(__iter__=lambda self: iter([tech_node]))
    techs_node.set_id = MagicMock()
    root.__getitem__.return_value = techs_node

    with patch("ehubx.parser.yaml_parser.parse", return_value=root), patch(
        "ehubx.parser.yaml_parser.check_node_type"
    ), patch(
        "ehubx.parser.tech_parser._preprocess_coupled_techs_primary"
    ) as mock_pre, patch(
        "ehubx.parser.tech_parser._parse_tech_initial"
    ) as mock_parse_initial:
        techs, _ = tech_parser.parse_initial("/tmp")

    assert isinstance(techs, Techs)
    mock_pre.assert_called_once_with(techs_node)
    mock_parse_initial.assert_called_once_with(tech_node, techs)


# ==========================================================================
# _preprocess_coupled_techs_primary
# ==========================================================================


def test_preprocess_coupled_techs_primary_self_reference_raises():
    file_path = "techs.yaml"
    techs_node = yaml_parser.YamlListNode(file_path)
    techs_node.add_list_child(_make_coupled_node(file_path, "t1", "t1"))
    techs_node.set_id(tech_parser.YAMLKEY_TECHID)
    techs_node.set_node_path([tech_parser.YAMLKEY_TECHS])

    with pytest.raises(exceptions.InvalidValueException):
        tech_parser._preprocess_coupled_techs_primary(techs_node)


def test_preprocess_coupled_techs_primary_missing_main_raises():
    file_path = "techs.yaml"
    techs_node = yaml_parser.YamlListNode(file_path)
    sub_node = _make_coupled_node(file_path, "t_sub", "t_main")
    coupling_node = sub_node[tech_parser.YAMLKEY_COUPLINGPARAMS]
    coupling_node.node_path_str = "techs['t_sub']|coupling_params"
    techs_node.add_list_child(sub_node)
    techs_node.set_id(tech_parser.YAMLKEY_TECHID)
    techs_node.set_node_path([tech_parser.YAMLKEY_TECHS])

    with pytest.raises(exceptions.InvalidValueException):
        tech_parser._preprocess_coupled_techs_primary(techs_node)


def test_preprocess_coupled_techs_primary_sub_has_params_raises():
    file_path = "techs.yaml"
    techs_node = yaml_parser.YamlListNode(file_path)
    main_node = _make_tech_node(file_path, "t_main")
    main_node.add_dict_child(tech_parser.YAMLKEY_TECHPARAMS, yaml_parser.YamlDictNode(file_path))
    techs_node.add_list_child(main_node)
    techs_node.add_list_child(
        _make_coupled_node(file_path, "t_sub", "t_main", with_tech_params=True)
    )
    techs_node.set_id(tech_parser.YAMLKEY_TECHID)
    techs_node.set_node_path([tech_parser.YAMLKEY_TECHS])

    with pytest.raises(exceptions.InvalidValueException):
        tech_parser._preprocess_coupled_techs_primary(techs_node)


def test_preprocess_coupled_techs_primary_copies_main_params():
    file_path = "techs.yaml"
    techs_node = yaml_parser.YamlListNode(file_path)
    main_node = _make_tech_node(file_path, "t_main")
    main_params = yaml_parser.YamlDictNode(file_path)
    main_params.add_child_value("foo", 1)
    main_node.add_dict_child(tech_parser.YAMLKEY_TECHPARAMS, main_params)
    sub_node = _make_coupled_node(file_path, "t_sub", "t_main")
    techs_node.add_list_child(main_node)
    techs_node.add_list_child(sub_node)
    techs_node.set_id(tech_parser.YAMLKEY_TECHID)
    techs_node.set_node_path([tech_parser.YAMLKEY_TECHS])

    tech_parser._preprocess_coupled_techs_primary(techs_node)

    copied_params = sub_node[tech_parser.YAMLKEY_TECHPARAMS]
    assert copied_params is not None
    assert copied_params["foo"].value == main_params["foo"].value
    assert copied_params is not main_params


# ==========================================================================
# _parse_tech_initial
# ==========================================================================


def test_parse_tech_initial_duplicate_id_exception_key():
    techs = Techs()
    techs.add_id(TechId("t1"))
    tech_node = MagicMock(spec=yaml_parser.YamlDictNode)

    with patch(
        "ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node",
        return_value="t1",
    ):
        with pytest.raises(data_exceptions.DuplicateIdException) as excinfo:
            tech_parser._parse_tech_initial(tech_node, techs)

    assert excinfo.value.key == TechExcKey.ID_ADD.value


# ==========================================================================
# _parse_tech_params_primary
# ==========================================================================


def test_parse_tech_params_primary_trl_none_allows_all_stages():
    techs = Techs()
    tech_id = TechId("t1")
    techs.add_id(tech_id)
    techs.set_cap_unit(tech_id, DimlessUnit())

    stages = MagicMock()
    stages.ids = {StageId("S1"), StageId("S2")}
    energy_system = MagicMock()
    energy_system.trl_threshold = 5

    tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
    tech_params_node = MagicMock(spec=yaml_parser.YamlDictNode)

    with patch(
        "ehubx.parser.yaml_parser.get_mandatory_subnode_from_dict_node",
        return_value=tech_params_node,
    ), patch("ehubx.parser.yaml_parser.check_node_type"), patch(
        "ehubx.parser.yaml_parser.parse_mandatory_value_from_dict_node",
        return_value=Value(20, TimeUnit.A),
    ), patch(
        "ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node",
        side_effect=[None, None],
    ):
        tech_parser._parse_tech_params_primary(
            tech_node, tech_id, energy_system, stages, techs
        )

    assert techs.get_allowed_stages(tech_id) == stages.ids


def test_parse_tech_params_primary_trl_threshold_filters():
    techs = Techs()
    tech_id = TechId("t1")
    techs.add_id(tech_id)
    techs.set_cap_unit(tech_id, DimlessUnit())

    stage_low = StageId("S1")
    stage_high = StageId("S2")
    stages = MagicMock()
    stages.ids = {stage_low, stage_high}
    energy_system = MagicMock()
    energy_system.trl_threshold = Value(4, DimlessUnit())

    trl_dict = {
        stage_low: Value(3, DimlessUnit()),
        stage_high: Value(5, DimlessUnit()),
    }

    tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
    tech_params_node = MagicMock(spec=yaml_parser.YamlDictNode)

    with patch(
        "ehubx.parser.yaml_parser.get_mandatory_subnode_from_dict_node",
        return_value=tech_params_node,
    ), patch("ehubx.parser.yaml_parser.check_node_type"), patch(
        "ehubx.parser.yaml_parser.parse_mandatory_value_from_dict_node",
        return_value=Value(20, TimeUnit.A),
    ), patch(
        "ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node",
        side_effect=[trl_dict, None],
    ):
        tech_parser._parse_tech_params_primary(
            tech_node, tech_id, energy_system, stages, techs
        )

    assert techs.get_allowed_stages(tech_id) == {stage_high}


# ==========================================================================
# _parse_costs / _parse_emissions
# ==========================================================================


def test_parse_costs_default_interest_rate_when_missing():
    techs = Techs()
    tech_id = TechId("t1")
    techs.add_id(tech_id)
    techs.set_cap_unit(tech_id, DimlessUnit())

    energy_system = MagicMock()
    energy_system.interest_rate_def = Value(0.03, DimlessUnit())

    tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
    tech_node.__getitem__.return_value = None

    tech_parser._parse_costs(tech_node, tech_id, energy_system, MagicMock(), techs)

    assert techs.get_interest_rate(tech_id) == energy_system.interest_rate_def


def test_parse_costs_sets_values():
    techs = Techs()
    tech_id = TechId("t1")
    techs.add_id(tech_id)
    techs.set_cap_unit(tech_id, DimlessUnit())

    stages = MagicMock()
    stage_id = StageId("S1")

    costs_node = MagicMock(spec=yaml_parser.YamlDictNode)
    tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
    tech_node.__getitem__.return_value = costs_node

    with patch("ehubx.parser.yaml_parser.check_node_type"), patch(
        "ehubx.parser.yaml_parser.parse_optional_value_from_dict_node",
        return_value=Value(0.04, DimlessUnit()),
    ), patch(
        "ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node",
        side_effect=[
            {stage_id: Value(100, CurrencyUnit.CHF)},
            {stage_id: Value(2, CurrencyUnit.CHF / DimlessUnit())},
            {stage_id: Value(10, CurrencyUnit.CHF)},
            {stage_id: Value(1, CurrencyUnit.CHF / DimlessUnit())},
        ],
    ):
        tech_parser._parse_costs(tech_node, tech_id, MagicMock(), stages, techs)

    assert techs.get_one_time_capex(stage_id, tech_id).to_float(CurrencyUnit.CHF) == pytest.approx(100)
    assert techs.get_capex_per_cap(stage_id, tech_id).to_float(CurrencyUnit.CHF / DimlessUnit()) == pytest.approx(2)
    assert techs.get_one_time_opex(stage_id, tech_id).to_float(CurrencyUnit.CHF) == pytest.approx(10)
    assert techs.get_opex_per_cap(stage_id, tech_id).to_float(CurrencyUnit.CHF / DimlessUnit()) == pytest.approx(1)


def test_parse_emissions_sets_co2_per_cap():
    techs = Techs()
    tech_id = TechId("t1")
    techs.add_id(tech_id)
    techs.set_cap_unit(tech_id, DimlessUnit())

    stage_id = StageId("S1")
    emissions_node = MagicMock(spec=yaml_parser.YamlDictNode)
    tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
    tech_node.__getitem__.return_value = emissions_node

    with patch("ehubx.parser.yaml_parser.check_node_type"), patch(
        "ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node",
        return_value={stage_id: Value(4, MassUnit.KG / DimlessUnit())},
    ):
        tech_parser._parse_emissions(tech_node, tech_id, MagicMock(), techs)

    assert techs.get_co2_per_cap(stage_id, tech_id).to_float(MassUnit.KG / DimlessUnit()) == pytest.approx(4)


# ==========================================================================
# _parse_coupled_techs
# ==========================================================================


def test_parse_coupled_techs_sets_main_and_cap_factor():
    techs = Techs()
    main_id = TechId("main")
    sub_id = TechId("sub")
    techs.add_id(main_id)
    techs.add_id(sub_id)
    techs.set_cap_unit(main_id, DimlessUnit())
    techs.set_cap_unit(sub_id, DimlessUnit())

    tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
    coupling_node = MagicMock(spec=yaml_parser.YamlDictNode)
    tech_node.__getitem__.return_value = coupling_node

    with patch(
        "ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node",
        side_effect=["sub", "main"],
    ), patch(
        "ehubx.parser.yaml_parser.parse_mandatory_value_from_dict_node",
        return_value=Value(0.5, DimlessUnit()),
    ):
        tech_parser._parse_coupled_techs(tech_node, techs)

    assert techs.get_coupled_main_tech(sub_id) == main_id
    assert techs.get_coupled_cap_factor(sub_id).to_float(DimlessUnit()) == pytest.approx(0.5)


def test_parse_coupled_techs_missing_sub_id_exception_key():
    techs = Techs()
    main_id = TechId("main")
    techs.add_id(main_id)
    techs.set_cap_unit(main_id, DimlessUnit())

    tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
    coupling_node = MagicMock(spec=yaml_parser.YamlDictNode)
    tech_node.__getitem__.return_value = coupling_node

    with patch(
        "ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node",
        side_effect=["sub", "main"],
    ):
        with pytest.raises(data_exceptions.UnknownIdException) as excinfo:
            tech_parser._parse_coupled_techs(tech_node, techs)

    assert excinfo.value.key == TechExcKey.COUPLEDMAINTECH_SET.value


# ==========================================================================
# parse_primary
# ==========================================================================


def test_parse_primary_calls_parse_and_log():
    root = MagicMock()
    tech_node = MagicMock()
    techs_node = MagicMock(__iter__=lambda self: iter([tech_node]))
    root.__getitem__.return_value = techs_node

    with patch("ehubx.parser.tech_parser._parse_tech_primary") as mock_parse, patch(
        "ehubx.parser.tech_parser._parse_coupled_techs"
    ) as mock_coupled, patch("ehubx.parser.tech_parser._log") as mock_log:
        tech_parser.parse_primary(root, Techs(), MagicMock(), MagicMock())

    mock_parse.assert_called_once()
    mock_coupled.assert_called_once()
    mock_log.assert_called_once()


# ==========================================================================
# parse_secondary / _parse_allowed_techs
# ==========================================================================


def test_parse_secondary_empty_cases():
    with patch("ehubx.parser.tech_parser._parse_hub_secondary") as mock_parse:
        tech_parser.parse_secondary(None, MagicMock(), Techs())
        mock_parse.assert_not_called()

    root = MagicMock()
    root.__getitem__.return_value = None
    with patch("ehubx.parser.tech_parser._parse_hub_secondary") as mock_parse:
        tech_parser.parse_secondary(root, MagicMock(), Techs())
        mock_parse.assert_not_called()


def test_parse_secondary_calls_parse_hub_secondary():
    root = MagicMock()
    hub_node = MagicMock()
    hubs_node = MagicMock(__iter__=lambda self: iter([hub_node]))
    root.__getitem__.return_value = hubs_node

    with patch("ehubx.parser.tech_parser._parse_hub_secondary") as mock_parse, patch(
        "ehubx.parser.tech_parser._parse_tech_lists", return_value={}
    ):
        tech_parser.parse_secondary(root, MagicMock(), Techs())

    mock_parse.assert_called_once()


def test_parse_allowed_techs_invalid_list_raises():
    hub_node = MagicMock()
    hub_node.node_path_as_str = "hubs[0]"
    hub_node.file_path = "hubs.yaml"

    with patch(
        "ehubx.parser.yaml_parser.parse_str_list_from_dict_node",
        return_value=["missing_list"],
    ):
        with pytest.raises(exceptions.InvalidValueException):
            tech_parser._parse_allowed_techs(hub_node, {}, HubId("H1"), Techs())


def test_parse_allowed_techs_adds_coupled_sub_techs_and_hubs():
    techs = Techs()
    main_id = TechId("main")
    sub_id = TechId("sub")
    techs.add_id(main_id)
    techs.add_id(sub_id)
    techs.set_coupled_main_tech(sub_id, main_id)
    techs.set_coupled_cap_factor(sub_id, Value(1, DimlessUnit()))

    hub_id = HubId("H1")

    hub_node = MagicMock()
    hub_node.node_path_as_str = "hubs[0]"
    hub_node.file_path = "hubs.yaml"

    tech_lists = {"list1": [main_id]}

    with patch(
        "ehubx.parser.yaml_parser.parse_str_list_from_dict_node",
        return_value=["list1"],
    ):
        allowed = tech_parser._parse_allowed_techs(hub_node, tech_lists, hub_id, techs)

    assert main_id in allowed
    assert sub_id in allowed
    assert hub_id in techs.get_allowed_hubs(main_id)
    assert hub_id in techs.get_allowed_hubs(sub_id)


# ==========================================================================
# _preprocess_coupled_techs_secondary
# ==========================================================================


def test_preprocess_coupled_techs_secondary_creates_sub_tech_node():
    techs = Techs()
    main_id = TechId("main")
    sub_id = TechId("sub")
    techs.add_id(main_id)
    techs.add_id(sub_id)
    techs.set_cap_unit(main_id, DimlessUnit())
    techs.set_cap_unit(sub_id, DimlessUnit())
    techs.set_coupled_main_tech(sub_id, main_id)
    techs.set_coupled_cap_factor(sub_id, Value(0.5, DimlessUnit()))

    file_path = "techs.yaml"
    techs_node = yaml_parser.YamlListNode(file_path)
    main_node = _make_tech_node(file_path, "main")
    main_params = yaml_parser.YamlDictNode(file_path)
    main_node.add_dict_child(tech_parser.YAMLKEY_TECHPARAMS, main_params)
    techs_node.add_list_child(main_node)
    techs_node.set_id(tech_parser.YAMLKEY_TECHID)
    techs_node.set_node_path([tech_parser.YAMLKEY_TECHS])

    with patch(
        "ehubx.parser.yaml_parser.parse_optional_value_from_dict_node",
        side_effect=[
            Value(10, DimlessUnit()),
            Value(1, TimeUnit.A),
            Value(2030, DimlessUnit()),
        ],
    ):
        tech_parser._preprocess_coupled_techs_secondary(techs_node, techs)

    sub_node = techs_node[sub_id.key]
    assert sub_node is not None
    params_node = sub_node[tech_parser.YAMLKEY_TECHPARAMS]
    assert params_node is not None


def test_preprocess_coupled_techs_secondary_raises_on_existing_params():
    techs = Techs()
    main_id = TechId("main")
    sub_id = TechId("sub")
    techs.add_id(main_id)
    techs.add_id(sub_id)
    techs.set_coupled_main_tech(sub_id, main_id)

    file_path = "techs.yaml"
    techs_node = yaml_parser.YamlListNode(file_path)
    main_node = _make_tech_node(file_path, "main")
    main_node.add_dict_child(tech_parser.YAMLKEY_TECHPARAMS, yaml_parser.YamlDictNode(file_path))
    sub_node = _make_tech_node(file_path, "sub")
    sub_node.add_dict_child(tech_parser.YAMLKEY_TECHPARAMS, yaml_parser.YamlDictNode(file_path))
    techs_node.add_list_child(main_node)
    techs_node.add_list_child(sub_node)
    techs_node.set_id(tech_parser.YAMLKEY_TECHID)
    techs_node.set_node_path([tech_parser.YAMLKEY_TECHS])

    with pytest.raises(exceptions.InvalidValueException):
        tech_parser._preprocess_coupled_techs_secondary(techs_node, techs)


# ==========================================================================
# _parse_tech_secondary
# ==========================================================================


def test_parse_tech_secondary_sets_params():
    techs = Techs()
    tech_id = TechId("t1")
    hub_id = HubId("H1")
    stage_id = StageId("S1")
    techs.add_id(tech_id)
    techs.set_cap_unit(tech_id, DimlessUnit())

    tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
    tech_params_node = MagicMock(spec=yaml_parser.YamlDictNode)
    tech_node.__getitem__.return_value = tech_params_node

    with patch(
        "ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node",
        return_value="t1",
    ), patch("ehubx.parser.yaml_parser.check_node_type"), patch(
        "ehubx.parser.yaml_parser.parse_optional_float_from_dict_node",
        return_value=2030.0,
    ), patch(
        "ehubx.parser.yaml_parser.parse_optional_value_from_dict_node",
        side_effect=[Value(5, DimlessUnit()), Value(2, TimeUnit.A)],
    ), patch(
        "ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node",
        side_effect=[
            {stage_id: Value(1, DimlessUnit())},
            {stage_id: Value(3, DimlessUnit())},
        ],
    ):
        tech_parser._parse_tech_secondary(
            tech_node, hub_id, MagicMock(), techs, {tech_id}
        )

    assert techs.get_last_inst_year(hub_id, tech_id) == 2030.0
    assert techs.get_cap_init(hub_id, tech_id).to_float(DimlessUnit()) == pytest.approx(5)
    assert techs.get_age_init(hub_id, tech_id).to_float(TimeUnit.A) == pytest.approx(2)
    assert techs.get_cap_min(stage_id, hub_id, tech_id).to_float(DimlessUnit()) == pytest.approx(1)
    assert techs.get_cap_max(stage_id, hub_id, tech_id).to_float(DimlessUnit()) == pytest.approx(3)


def test_parse_tech_secondary_warns_for_disallowed_tech():
    techs = Techs()
    tech_id = TechId("t1")
    techs.add_id(tech_id)

    tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
    tech_params_node = MagicMock(spec=yaml_parser.YamlDictNode)
    tech_node.__getitem__.return_value = tech_params_node

    with patch("ehubx.core.logging.log_warning") as mock_log, patch(
        "ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node",
        return_value="t1",
    ), patch(
        "ehubx.parser.yaml_parser.check_node_type"
    ), patch(
        "ehubx.parser.yaml_parser.parse_optional_float_from_dict_node",
        return_value=None,
    ), patch(
        "ehubx.parser.yaml_parser.parse_optional_value_from_dict_node",
        return_value=None,
    ), patch(
        "ehubx.parser.yaml_parser.parse_optional_yeardep_value_from_dict_node",
        return_value=None,
    ):
        tech_parser._parse_tech_secondary(
            tech_node, HubId("H1"), MagicMock(), techs, set()
        )

    mock_log.assert_called_once()


# ==========================================================================
# _parse_tech_lists / _log
# ==========================================================================


def test_parse_tech_lists_warns_unknown_tech():
    techs = Techs()
    techs.add_id(TechId("known"))

    hub_root = MagicMock()
    tech_lists_node = MagicMock(__iter__=lambda self: iter([MagicMock()]))
    tech_lists_node.set_id = MagicMock()
    hub_root.__getitem__.return_value = tech_lists_node

    with patch("ehubx.parser.yaml_parser.check_node_type"), patch(
        "ehubx.parser.yaml_parser.parse_mandatory_str_from_dict_node",
        return_value="list1",
    ), patch(
        "ehubx.parser.yaml_parser.parse_str_list_from_dict_node",
        return_value=["known", "unknown"],
    ), patch("ehubx.core.logging.log_warning") as mock_log:
        tech_lists = tech_parser._parse_tech_lists(hub_root, techs)

    assert "list1" in tech_lists
    assert TechId("known") in tech_lists["list1"]
    assert TechId("unknown") in tech_lists["list1"]
    mock_log.assert_called_once()


def test_log_outputs_techs():
    techs = Techs()
    tech_id = TechId("t1")
    techs.add_id(tech_id)
    techs.set_lifetime(tech_id, Value(10, TimeUnit.A))

    with patch("ehubx.core.logging.log_file") as mock_log:
        tech_parser._log(techs)

    assert mock_log.call_count == 2
