import pytest
from unittest.mock import MagicMock, patch

from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.net_link_data import NetLinkId
from ehubx.data.net_tech_data import (
    ExceptionKey as NetTechExcKey,
    NetTechId,
    NetworkTechs,
)
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.unit import (
    CurrencyUnit,
    DimlessUnit,
    LengthUnit,
    MassUnit,
    TimeUnit,
    Unit,
)
from ehubx.data.value import Value
from ehubx.data import exceptions as data_exceptions
from ehubx.parser import exceptions, net_link_parser, net_tech_parser, yaml_parser


# ==========================================================================
# Fixtures
# ==========================================================================


@pytest.fixture
def stages():
    mock_stages = MagicMock(spec=Stages)
    mock_stages.ids = [StageId("S1"), StageId("S2")]
    return mock_stages


@pytest.fixture
def ecs():
    mock_ecs = MagicMock(spec=Ecs)
    mock_ecs.get_unit.return_value = Unit.from_str("MWh")
    return mock_ecs


@pytest.fixture
def energy_system():
    mock_energy_system = MagicMock(spec=EnergySystem)
    mock_energy_system.trl_threshold = Value(5, DimlessUnit())
    mock_energy_system.interest_rate_def = Value(0.03, DimlessUnit())
    return mock_energy_system


# ==========================================================================
# Tests for parse_primary()
# ==========================================================================


def test_parse_primary_returns_empty_when_yaml_none(stages, ecs, energy_system):
    with patch("ehubx.parser.net_tech_parser.yaml_parser.parse", return_value=None):
        net_techs = net_tech_parser.parse_primary(
            "/tmp/model", energy_system, stages, ecs
        )

    assert isinstance(net_techs, NetworkTechs)
    assert len(net_techs.ids) == 0


def test_parse_primary_returns_empty_when_no_net_techs(stages, ecs, energy_system):
    root = MagicMock(spec=yaml_parser.YamlDictNode)
    root.__getitem__.return_value = None

    with patch("ehubx.parser.net_tech_parser.yaml_parser.parse", return_value=root), patch(
        "ehubx.parser.net_tech_parser.yaml_parser.check_node_type"
    ):
        net_techs = net_tech_parser.parse_primary(
            "/tmp/model", energy_system, stages, ecs
        )

    assert isinstance(net_techs, NetworkTechs)
    assert len(net_techs.ids) == 0


# ==========================================================================
# Tests for _parse_net_tech_primary()
# ==========================================================================


def test_parse_net_tech_primary_sets_fields_and_allows_all_stages(
    stages, ecs, energy_system
):
    net_tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
    net_techs = NetworkTechs()

    with patch(
        "ehubx.parser.net_tech_parser.yaml_parser.parse_mandatory_str_from_dict_node",
        side_effect=["NT1", "E1"],
    ), patch(
        "ehubx.parser.net_tech_parser.yaml_parser.parse_mandatory_value_from_dict_node",
        return_value=Value(20, TimeUnit.A),
    ), patch(
        "ehubx.parser.net_tech_parser.yaml_parser.parse_optional_yeardep_value_from_dict_node",
        side_effect=[None, None, None],
    ), patch("ehubx.parser.net_tech_parser._parse_costs") as mock_costs, patch(
        "ehubx.parser.net_tech_parser._parse_emissions"
    ) as mock_emissions:
        net_tech_parser._parse_net_tech_primary(
            net_tech_node, energy_system, stages, ecs, net_techs
        )

    net_tech_id = NetTechId("NT1")
    assert net_techs.get_ec(net_tech_id) == EcId("E1")
    assert net_techs.get_lifetime(net_tech_id).to_float(TimeUnit.A) == 20
    assert net_techs.get_allowed_stages(net_tech_id) == set(stages.ids)
    mock_costs.assert_called_once()
    mock_emissions.assert_called_once()


def test_parse_net_tech_primary_trl_filters_stages(stages, ecs, energy_system):
    net_tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
    net_techs = NetworkTechs()
    trl_values = {
        stages.ids[0]: Value(4, DimlessUnit()),
        stages.ids[1]: Value(6, DimlessUnit()),
    }

    with patch(
        "ehubx.parser.net_tech_parser.yaml_parser.parse_mandatory_str_from_dict_node",
        side_effect=["NT1", "E1"],
    ), patch(
        "ehubx.parser.net_tech_parser.yaml_parser.parse_mandatory_value_from_dict_node",
        return_value=Value(15, TimeUnit.A),
    ), patch(
        "ehubx.parser.net_tech_parser.yaml_parser.parse_optional_yeardep_value_from_dict_node",
        side_effect=[trl_values, None, None],
    ), patch("ehubx.parser.net_tech_parser._parse_costs"), patch(
        "ehubx.parser.net_tech_parser._parse_emissions"
    ):
        net_tech_parser._parse_net_tech_primary(
            net_tech_node, energy_system, stages, ecs, net_techs
        )

    net_tech_id = NetTechId("NT1")
    assert net_techs.get_allowed_stages(net_tech_id) == {stages.ids[1]}


def test_parse_net_tech_primary_duplicate_id_raises_exception_key(
    stages, ecs, energy_system
):
    net_tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
    net_techs = NetworkTechs()
    net_techs.add_id(NetTechId("NT1"))

    with patch(
        "ehubx.parser.net_tech_parser.yaml_parser.parse_mandatory_str_from_dict_node",
        side_effect=["NT1", "E1"],
    ):
        with pytest.raises(data_exceptions.DuplicateIdException) as excinfo:
            net_tech_parser._parse_net_tech_primary(
                net_tech_node, energy_system, stages, ecs, net_techs
            )

    assert excinfo.value.key == NetTechExcKey.ID_ADD.value


# ==========================================================================
# Tests for _parse_costs()
# ==========================================================================


def test_parse_costs_sets_default_interest_rate_and_values(
    stages, ecs, energy_system
):
    net_tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
    costs_node = MagicMock(spec=yaml_parser.YamlDictNode)
    net_tech_node.__getitem__.return_value = costs_node

    net_techs = NetworkTechs()
    net_tech_id = NetTechId("NT1")
    net_techs.add_id(net_tech_id)
    net_techs.set_ec(net_tech_id, EcId("E1"), ecs.get_unit(EcId("E1")))

    stage_id = stages.ids[0]
    ec_unit = ecs.get_unit(EcId("E1"))
    one_time_capex = Value(10, CurrencyUnit.CHF / LengthUnit.M)
    capex_per_cap = Value(
        20, CurrencyUnit.CHF / ((ec_unit / TimeUnit.H) * LengthUnit.M)
    )
    one_time_opex = Value(30, CurrencyUnit.CHF / LengthUnit.M)
    opex_per_cap = Value(
        40, CurrencyUnit.CHF / ((ec_unit / TimeUnit.H) * LengthUnit.M)
    )
    opex_per_energy = Value(50, CurrencyUnit.CHF / (ec_unit * LengthUnit.M))

    with patch("ehubx.parser.net_tech_parser.yaml_parser.check_node_type"), patch(
        "ehubx.parser.net_tech_parser.yaml_parser.parse_optional_value_from_dict_node",
        return_value=None,
    ), patch(
        "ehubx.parser.net_tech_parser.yaml_parser.parse_optional_yeardep_value_from_dict_node",
        side_effect=[
            {stage_id: one_time_capex},
            {stage_id: capex_per_cap},
            {stage_id: one_time_opex},
            {stage_id: opex_per_cap},
            {stage_id: opex_per_energy},
        ],
    ):
        net_tech_parser._parse_costs(
            net_tech_node, net_tech_id, energy_system, stages, ecs, net_techs
        )

    assert net_techs.get_interest_rate(net_tech_id) == energy_system.interest_rate_def
    assert net_techs.get_one_time_capex(stage_id, net_tech_id) == one_time_capex
    assert net_techs.get_capex_per_cap(stage_id, net_tech_id) == capex_per_cap
    assert net_techs.get_one_time_opex(stage_id, net_tech_id) == one_time_opex
    assert net_techs.get_opex_per_cap(stage_id, net_tech_id) == opex_per_cap
    assert net_techs.get_opex_per_energy(stage_id, net_tech_id) == opex_per_energy


def test_parse_costs_missing_node_sets_interest_rate_default(
    stages, ecs, energy_system
):
    net_tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
    net_tech_node.__getitem__.return_value = None

    net_techs = NetworkTechs()
    net_tech_id = NetTechId("NT1")
    net_techs.add_id(net_tech_id)

    net_tech_parser._parse_costs(
        net_tech_node, net_tech_id, energy_system, stages, ecs, net_techs
    )

    assert net_techs.get_interest_rate(net_tech_id) == energy_system.interest_rate_def


# ==========================================================================
# Tests for _parse_emissions()
# ==========================================================================


def test_parse_emissions_sets_values(stages, ecs):
    net_tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
    emissions_node = MagicMock(spec=yaml_parser.YamlDictNode)
    net_tech_node.__getitem__.return_value = emissions_node

    net_techs = NetworkTechs()
    net_tech_id = NetTechId("NT1")
    net_techs.add_id(net_tech_id)
    net_techs.set_ec(net_tech_id, EcId("E1"), ecs.get_unit(EcId("E1")))

    stage_id = stages.ids[0]
    ec_unit = ecs.get_unit(EcId("E1"))
    co2_per_cap = Value(
        1, MassUnit.KG / ((ec_unit / TimeUnit.H) * LengthUnit.M)
    )
    co2_per_energy = Value(2, MassUnit.KG / (ec_unit * LengthUnit.M))

    with patch("ehubx.parser.net_tech_parser.yaml_parser.check_node_type"), patch(
        "ehubx.parser.net_tech_parser.yaml_parser.parse_optional_yeardep_value_from_dict_node",
        side_effect=[{stage_id: co2_per_cap}, {stage_id: co2_per_energy}],
    ):
        net_tech_parser._parse_emissions(
            net_tech_node, net_tech_id, stages, ecs, net_techs
        )

    assert net_techs.get_co2_per_cap(stage_id, net_tech_id) == co2_per_cap
    assert net_techs.get_co2_per_energy(stage_id, net_tech_id) == co2_per_energy


# ==========================================================================
# Tests for parse_secondary()
# ==========================================================================


def test_parse_secondary_calls_link_secondary(stages, ecs):
    link_root_node = MagicMock(spec=yaml_parser.YamlDictNode)
    start_hubs_node = MagicMock(spec=yaml_parser.YamlListNode)
    start_hub_node = MagicMock(spec=yaml_parser.YamlDictNode)
    end_hubs_node = MagicMock(spec=yaml_parser.YamlListNode)
    end_hub_node = MagicMock(spec=yaml_parser.YamlDictNode)
    links_node = MagicMock(spec=yaml_parser.YamlListNode)
    link_node = MagicMock(spec=yaml_parser.YamlDictNode)

    start_hubs_node.__iter__.return_value = iter([start_hub_node])
    end_hubs_node.__iter__.return_value = iter([end_hub_node])
    links_node.__iter__.return_value = iter([link_node])

    def root_getitem(key):
        if key == net_link_parser.YAMLKEY_STARTHUBS:
            return start_hubs_node
        return None

    def start_getitem(key):
        if key == net_link_parser.YAMLKEY_ENDHUBS:
            return end_hubs_node
        return None

    def end_getitem(key):
        if key == net_link_parser.YAMLKEY_NETLINKS:
            return links_node
        return None

    link_root_node.__getitem__.side_effect = root_getitem
    start_hub_node.__getitem__.side_effect = start_getitem
    end_hub_node.__getitem__.side_effect = end_getitem

    net_techs = NetworkTechs()

    with patch(
        "ehubx.parser.net_tech_parser._parse_net_tech_lists",
        return_value={"list1": [NetTechId("NT1")]},
    ), patch("ehubx.parser.net_tech_parser._parse_link_secondary") as mock_link:
        net_tech_parser.parse_secondary(link_root_node, ecs, net_techs)

    mock_link.assert_called_once()


# ==========================================================================
# Tests for _parse_net_tech_lists()
# ==========================================================================


def test_parse_net_tech_lists_parses_ids():
    link_root_node = MagicMock(spec=yaml_parser.YamlDictNode)
    net_tech_lists_node = MagicMock(spec=yaml_parser.YamlListNode)
    net_tech_list_node_1 = MagicMock(spec=yaml_parser.YamlDictNode)
    net_tech_list_node_2 = MagicMock(spec=yaml_parser.YamlDictNode)

    net_tech_lists_node.__iter__.return_value = iter(
        [net_tech_list_node_1, net_tech_list_node_2]
    )
    net_tech_lists_node.set_id = MagicMock()

    link_root_node.__getitem__.return_value = net_tech_lists_node

    with patch("ehubx.parser.net_tech_parser.yaml_parser.check_node_type"), patch(
        "ehubx.parser.net_tech_parser.yaml_parser.parse_mandatory_str_from_dict_node",
        side_effect=["L1", "L2"],
    ), patch(
        "ehubx.parser.net_tech_parser.yaml_parser.parse_str_list_from_dict_node",
        side_effect=[["NT1"], ["NT2", "NT3"]],
    ):
        net_tech_lists = net_tech_parser._parse_net_tech_lists(link_root_node)

    assert net_tech_lists == {
        "L1": [NetTechId("NT1")],
        "L2": [NetTechId("NT2"), NetTechId("NT3")],
    }


# ==========================================================================
# Tests for _parse_allowed_net_techs()
# ==========================================================================


def test_parse_allowed_net_techs_unknown_list_raises():
    link_node = MagicMock(spec=yaml_parser.YamlDictNode)
    link_node.file_path = "/tmp/link.yaml"
    link_node.node_path_as_str = "root"

    with patch(
        "ehubx.parser.net_tech_parser.yaml_parser.parse_str_list_from_dict_node",
        return_value=["unknown"],
    ):
        with pytest.raises(exceptions.InvalidValueException):
            net_tech_parser._parse_allowed_net_techs(
                link_node, {}, NetLinkId("L1"), NetworkTechs()
            )


def test_parse_allowed_net_techs_adds_allowed_links():
    link_node = MagicMock(spec=yaml_parser.YamlDictNode)
    net_tech_lists = {"list1": [NetTechId("NT1"), NetTechId("NT2")]}
    net_techs = NetworkTechs()
    net_techs.add_id(NetTechId("NT1"))
    net_techs.add_id(NetTechId("NT2"))
    link_id = NetLinkId("L1")

    with patch(
        "ehubx.parser.net_tech_parser.yaml_parser.parse_str_list_from_dict_node",
        return_value=["list1"],
    ):
        allowed = net_tech_parser._parse_allowed_net_techs(
            link_node, net_tech_lists, link_id, net_techs
        )

    assert allowed == {NetTechId("NT1"), NetTechId("NT2")}
    assert link_id in net_techs.get_allowed_net_links(NetTechId("NT1"))
    assert link_id in net_techs.get_allowed_net_links(NetTechId("NT2"))


# ==========================================================================
# Tests for _parse_link_secondary() / _parse_net_tech_secondary()
# ==========================================================================


def test_parse_link_secondary_calls_net_tech_secondary(stages, ecs):
    link_node = MagicMock(spec=yaml_parser.YamlDictNode)
    net_tech_params_node = MagicMock(spec=yaml_parser.YamlListNode)
    net_tech_param = MagicMock(spec=yaml_parser.YamlDictNode)

    net_tech_params_node.__iter__.return_value = iter([net_tech_param])
    net_tech_params_node.set_id = MagicMock()

    def link_getitem(key):
        if key == net_link_parser.YAMLKEY_NETLINKID:
            return None
        if key == net_tech_parser.YAMLKEY_NETTECHPARAMS:
            return net_tech_params_node
        return None

    link_node.__getitem__.side_effect = link_getitem

    net_techs = NetworkTechs()

    with patch(
        "ehubx.parser.net_tech_parser.yaml_parser.parse_mandatory_str_from_dict_node",
        return_value="L1",
    ), patch(
        "ehubx.parser.net_tech_parser._parse_allowed_net_techs",
        return_value={NetTechId("NT1")},
    ), patch(
        "ehubx.parser.net_tech_parser._parse_net_tech_secondary"
    ) as mock_secondary:
        net_tech_parser._parse_link_secondary(link_node, {}, ecs, net_techs)

    mock_secondary.assert_called_once()


def test_parse_net_tech_secondary_sets_cap_init_and_age_init(ecs):
    net_tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
    net_techs = NetworkTechs()
    net_tech_id = NetTechId("NT1")
    net_techs.add_id(net_tech_id)
    net_techs.set_ec(net_tech_id, EcId("E1"), ecs.get_unit(EcId("E1")))

    link_id = NetLinkId("L1")
    cap_init = Value(2, ecs.get_unit(EcId("E1")) / TimeUnit.H)
    age_init = Value(3, TimeUnit.A)

    with patch(
        "ehubx.parser.net_tech_parser.yaml_parser.parse_mandatory_str_from_dict_node",
        return_value="NT1",
    ), patch(
        "ehubx.parser.net_tech_parser.yaml_parser.parse_optional_value_from_dict_node",
        side_effect=[cap_init, age_init],
    ):
        net_tech_parser._parse_net_tech_secondary(
            net_tech_node, link_id, ecs, net_techs, {net_tech_id}
        )

    assert net_techs.get_cap_init(link_id, net_tech_id) == cap_init
    assert net_techs.get_age_init(link_id, net_tech_id) == age_init


def test_parse_net_tech_secondary_warns_when_not_allowed(ecs):
    net_tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
    net_tech_node.file_path = "/tmp/link.yaml"
    net_tech_node.node_path_as_str = "root"

    net_techs = NetworkTechs()
    net_tech_id = NetTechId("NT1")
    net_techs.add_id(net_tech_id)
    net_techs.set_ec(net_tech_id, EcId("E1"), ecs.get_unit(EcId("E1")))

    with patch(
        "ehubx.parser.net_tech_parser.yaml_parser.parse_mandatory_str_from_dict_node",
        return_value="NT1",
    ), patch(
        "ehubx.parser.net_tech_parser.yaml_parser.parse_optional_value_from_dict_node",
        return_value=None,
    ), patch("ehubx.parser.net_tech_parser.logging.log_warning") as mock_warn:
        net_tech_parser._parse_net_tech_secondary(
            net_tech_node, NetLinkId("L1"), ecs, net_techs, set()
        )

    mock_warn.assert_called_once()


def test_parse_net_tech_secondary_unknown_id_raises_exception_key(ecs):
    net_tech_node = MagicMock(spec=yaml_parser.YamlDictNode)
    net_techs = NetworkTechs()

    with patch(
        "ehubx.parser.net_tech_parser.yaml_parser.parse_mandatory_str_from_dict_node",
        return_value="NT1",
    ):
        with pytest.raises(data_exceptions.UnknownIdException) as excinfo:
            net_tech_parser._parse_net_tech_secondary(
                net_tech_node, NetLinkId("L1"), ecs, net_techs, set()
            )

    assert excinfo.value.key == NetTechExcKey.EC_GET.value
