import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId
from ehubx.data.net_link_data import (
    NetLinkDirection,
    NetLinkId,
    NetworkLinks,
    ExceptionKey as NetLinkExcKey,
)
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.time_data import TimeId
from ehubx.data.unit import DimlessUnit, LengthUnit, TimeUnit, Unit
from ehubx.data.value import Value
from ehubx.data import exceptions as data_exceptions
from ehubx.parser import csv_parser, exceptions, net_link_parser, yaml_parser


# ==========================================================================
# Fixtures
# ==========================================================================


@pytest.fixture
def stages():
    mock_stages = MagicMock(spec=Stages)
    mock_stages.ids = [StageId("S1")]
    return mock_stages


@pytest.fixture
def ecs():
    mock_ecs = MagicMock(spec=Ecs)
    mock_ecs.get_unit.return_value = Unit.from_str("MWh")
    return mock_ecs


@pytest.fixture
def stage_id():
    return StageId("S1")


@pytest.fixture
def link_id():
    return NetLinkId("L1")


@pytest.fixture
def ec_id():
    return EcId("E1")


@pytest.fixture
def hub_start():
    return HubId("H1")


@pytest.fixture
def hub_end():
    return HubId("H2")


# ==========================================================================
# Tests for parse()
# ==========================================================================


def test_parse_returns_empty_when_yaml_none(stages, ecs):
    with patch("ehubx.parser.net_link_parser.yaml_parser.parse", return_value=None):
        net_links, root = net_link_parser.parse("/tmp/model", stages, ecs)

    assert isinstance(net_links, NetworkLinks)
    assert len(net_links.ids) == 0
    assert root is None


def test_parse_returns_empty_when_no_start_hubs(stages, ecs):
    root = MagicMock(spec=yaml_parser.YamlDictNode)
    root.__getitem__.return_value = None

    with patch("ehubx.parser.net_link_parser.yaml_parser.parse", return_value=root), patch(
        "ehubx.parser.net_link_parser.yaml_parser.check_node_type"
    ):
        net_links, root_node = net_link_parser.parse("/tmp/model", stages, ecs)

    assert isinstance(net_links, NetworkLinks)
    assert len(net_links.ids) == 0
    assert root_node is root


def test_parse_skips_missing_end_hubs_and_links(stages, ecs):
    root = MagicMock(spec=yaml_parser.YamlDictNode)
    start_hubs_node = MagicMock(spec=yaml_parser.YamlListNode)
    start_hub_node_1 = MagicMock(spec=yaml_parser.YamlDictNode)
    start_hub_node_2 = MagicMock(spec=yaml_parser.YamlDictNode)
    end_hubs_node = MagicMock(spec=yaml_parser.YamlListNode)
    end_hub_node = MagicMock(spec=yaml_parser.YamlDictNode)

    start_hubs_node.__iter__.return_value = iter([start_hub_node_1, start_hub_node_2])
    start_hubs_node.set_id = MagicMock()

    end_hubs_node.__iter__.return_value = iter([end_hub_node])
    end_hubs_node.set_id = MagicMock()

    def root_getitem(key):
        if key == net_link_parser.YAMLKEY_STARTHUBS:
            return start_hubs_node
        return None

    def start_1_getitem(key):
        if key == net_link_parser.YAMLKEY_ENDHUBS:
            return None
        return None

    def start_2_getitem(key):
        if key == net_link_parser.YAMLKEY_ENDHUBS:
            return end_hubs_node
        return None

    def end_getitem(key):
        if key == net_link_parser.YAMLKEY_NETLINKS:
            return None
        return None

    root.__getitem__.side_effect = root_getitem
    start_hub_node_1.__getitem__.side_effect = start_1_getitem
    start_hub_node_2.__getitem__.side_effect = start_2_getitem
    end_hub_node.__getitem__.side_effect = end_getitem

    with patch("ehubx.parser.net_link_parser.yaml_parser.parse", return_value=root), patch(
        "ehubx.parser.net_link_parser.yaml_parser.check_node_type"
    ), patch(
        "ehubx.parser.net_link_parser.yaml_parser.parse_mandatory_str_from_dict_node",
        side_effect=["H1", "H2", "H3"],
    ), patch("ehubx.parser.net_link_parser._parse_link_primary") as mock_parse_link:
        net_links, _ = net_link_parser.parse("/tmp/model", stages, ecs)

    assert isinstance(net_links, NetworkLinks)
    assert len(net_links.ids) == 0
    mock_parse_link.assert_not_called()


# ==========================================================================
# Tests for _parse_link_primary()
# ==========================================================================


def test_parse_link_primary_basic_fields(stages, ecs, hub_start, hub_end):
    link_node = MagicMock(spec=yaml_parser.YamlDictNode)
    ecs_node = MagicMock(spec=yaml_parser.YamlListNode)
    ec_node = MagicMock(spec=yaml_parser.YamlValueNode)

    ecs_node.__len__.return_value = 1
    ecs_node.__iter__.return_value = iter([ec_node])
    link_node.__getitem__.return_value = None

    net_links = NetworkLinks()

    with patch(
        "ehubx.parser.net_link_parser.yaml_parser.parse_mandatory_str_from_dict_node",
        return_value="L1",
    ), patch(
        "ehubx.parser.net_link_parser.yaml_parser.get_mandatory_subnode_from_dict_node",
        return_value=ecs_node,
    ), patch(
        "ehubx.parser.net_link_parser.yaml_parser.parse_str_from_value_node",
        return_value="E1",
    ), patch(
        "ehubx.parser.net_link_parser.yaml_parser.parse_mandatory_value_from_dict_node",
        return_value=Value(10, unit=LengthUnit.M),
    ), patch(
        "ehubx.parser.net_link_parser.yaml_parser.parse_optional_bool_from_dict_node",
        return_value=True,
    ), patch("ehubx.parser.net_link_parser.yaml_parser.check_node_type"):
        net_link_parser._parse_link_primary(
            link_node, hub_start, hub_end, stages, ecs, net_links
        )

    link_id = NetLinkId("L1")
    ec_id = EcId("E1")
    assert link_id in net_links.ids
    assert net_links.get_hub_start(link_id) == hub_start
    assert net_links.get_hub_end(link_id) == hub_end
    assert net_links.is_bidirectional(link_id) is True
    assert ec_id in net_links.get_ecs(link_id)
    assert net_links.get_length(link_id).to_float(LengthUnit.M) == 10


def test_parse_link_primary_empty_ecs_raises(stages, ecs, hub_start, hub_end):
    link_node = MagicMock(spec=yaml_parser.YamlDictNode)
    ecs_node = MagicMock(spec=yaml_parser.YamlListNode)

    ecs_node.__len__.return_value = 0
    ecs_node.__iter__.return_value = iter([])

    with patch(
        "ehubx.parser.net_link_parser.yaml_parser.parse_mandatory_str_from_dict_node",
        return_value="L1",
    ), patch(
        "ehubx.parser.net_link_parser.yaml_parser.get_mandatory_subnode_from_dict_node",
        return_value=ecs_node,
    ), patch("ehubx.parser.net_link_parser.yaml_parser.check_node_type"):
        with pytest.raises(exceptions.EmptyListNodeException):
            net_link_parser._parse_link_primary(
                link_node, hub_start, hub_end, stages, ecs, NetworkLinks()
            )


def test_parse_link_primary_calls_ec_params(stages, ecs, hub_start, hub_end):
    link_node = MagicMock(spec=yaml_parser.YamlDictNode)
    ecs_node = MagicMock(spec=yaml_parser.YamlListNode)
    ec_node = MagicMock(spec=yaml_parser.YamlValueNode)
    ec_params_node = MagicMock(spec=yaml_parser.YamlListNode)
    ec_params_child = MagicMock(spec=yaml_parser.YamlDictNode)

    ecs_node.__len__.return_value = 1
    ecs_node.__iter__.return_value = iter([ec_node])
    ec_params_node.__iter__.return_value = iter([ec_params_child])
    ec_params_node.set_id = MagicMock()

    def link_getitem(key):
        if key == net_link_parser.YAMLKEY_ECPARAMS:
            return ec_params_node
        return None

    link_node.__getitem__.side_effect = link_getitem

    net_links = NetworkLinks()

    with patch(
        "ehubx.parser.net_link_parser.yaml_parser.parse_mandatory_str_from_dict_node",
        return_value="L1",
    ), patch(
        "ehubx.parser.net_link_parser.yaml_parser.get_mandatory_subnode_from_dict_node",
        return_value=ecs_node,
    ), patch(
        "ehubx.parser.net_link_parser.yaml_parser.parse_str_from_value_node",
        return_value="E1",
    ), patch(
        "ehubx.parser.net_link_parser.yaml_parser.parse_mandatory_value_from_dict_node",
        return_value=Value(1, unit=LengthUnit.M),
    ), patch(
        "ehubx.parser.net_link_parser.yaml_parser.parse_optional_bool_from_dict_node",
        return_value=None,
    ), patch(
        "ehubx.parser.net_link_parser.yaml_parser.check_node_type"
    ), patch("ehubx.parser.net_link_parser._parse_ec_params") as mock_parse_ec:
        net_link_parser._parse_link_primary(
            link_node, hub_start, hub_end, stages, ecs, net_links
        )

    mock_parse_ec.assert_called_once_with(
        ec_params_child, NetLinkId("L1"), stages, ecs, net_links
    )


# ==========================================================================
# Tests for _parse_ec_params()
# ==========================================================================


def test_parse_ec_params_sets_values(stages, ecs, link_id, ec_id, stage_id):
    ec_node = MagicMock(spec=yaml_parser.YamlDictNode)
    net_links = NetworkLinks()
    net_links.add_id(link_id)
    net_links.add_ec(link_id, ec_id, ecs.get_unit(ec_id))

    ec_unit = ecs.get_unit(ec_id)

    cap_min = {stage_id: Value(1, unit=(ec_unit / TimeUnit.H))}
    cap_max = {stage_id: Value(2, unit=(ec_unit / TimeUnit.H))}
    sum_min_forward = {stage_id: Value(3, unit=ec_unit)}
    sum_min_backward = {stage_id: Value(4, unit=ec_unit)}
    sum_max_forward = {stage_id: Value(5, unit=ec_unit)}
    sum_max_backward = {stage_id: Value(6, unit=ec_unit)}
    availability = {stage_id: Value(0.9, unit=DimlessUnit())}

    with patch(
        "ehubx.parser.net_link_parser.yaml_parser.parse_mandatory_str_from_dict_node",
        return_value=ec_id.key,
    ), patch(
        "ehubx.parser.net_link_parser.yaml_parser.parse_optional_yeardep_value_from_dict_node",
        side_effect=[
            cap_min,
            cap_max,
            sum_min_forward,
            sum_min_backward,
            sum_max_forward,
            sum_max_backward,
            availability,
        ],
    ), patch("ehubx.parser.net_link_parser._parse_net_link_ec_profiles"):
        net_link_parser._parse_ec_params(ec_node, link_id, stages, ecs, net_links)

    assert (
        net_links.get_cap_min(stage_id, link_id, ec_id)
        .to_float(ec_unit / TimeUnit.H)
        == 1
    )
    assert (
        net_links.get_cap_max(stage_id, link_id, ec_id)
        .to_float(ec_unit / TimeUnit.H)
        == 2
    )
    assert (
        net_links.get_sum_min(stage_id, link_id, ec_id, NetLinkDirection.FORWARD)
        .to_float(ec_unit)
        == 3
    )
    assert (
        net_links.get_sum_min(stage_id, link_id, ec_id, NetLinkDirection.BACKWARD)
        .to_float(ec_unit)
        == 4
    )
    assert (
        net_links.get_sum_max(stage_id, link_id, ec_id, NetLinkDirection.FORWARD)
        .to_float(ec_unit)
        == 5
    )
    assert (
        net_links.get_sum_max(stage_id, link_id, ec_id, NetLinkDirection.BACKWARD)
        .to_float(ec_unit)
        == 6
    )
    assert (
        net_links.get_availability(stage_id, link_id, ec_id)
        .def_value.to_float(DimlessUnit())
        == 0.9
    )


def test_parse_ec_params_invalid_unit_raises_data_exception_key(
    stages, ecs, link_id, ec_id, stage_id
):
    ec_node = MagicMock(spec=yaml_parser.YamlDictNode)
    net_links = NetworkLinks()
    net_links.add_id(link_id)
    net_links.add_ec(link_id, ec_id, ecs.get_unit(ec_id))

    cap_min = {stage_id: Value(1, unit=LengthUnit.M)}

    with patch(
        "ehubx.parser.net_link_parser.yaml_parser.parse_mandatory_str_from_dict_node",
        return_value=ec_id.key,
    ), patch(
        "ehubx.parser.net_link_parser.yaml_parser.parse_optional_yeardep_value_from_dict_node",
        return_value=cap_min,
    ), patch("ehubx.parser.net_link_parser._parse_net_link_ec_profiles"):
        with pytest.raises(data_exceptions.DataException) as excinfo:
            net_link_parser._parse_ec_params(ec_node, link_id, stages, ecs, net_links)

    assert excinfo.value.key == NetLinkExcKey.CAPMIN_SET.value


# ==========================================================================
# Tests for _parse_net_link_ec_profiles()
# ==========================================================================


def test_parse_net_link_ec_profiles_sets_availability(ecs, link_id, ec_id):
    ec_node = MagicMock(spec=yaml_parser.YamlDictNode)
    ec_node.file_path = "/tmp/inputs/network_links.yaml"

    net_links = NetworkLinks()
    net_links.add_id(link_id)
    net_links.add_ec(link_id, ec_id, ecs.get_unit(ec_id))

    columns = pd.MultiIndex.from_tuples(
        [
            ("S1", link_id.key, ec_id.key, net_link_parser.YAMLKEY_AVAILABILITY),
            ("S1", "OTHER", ec_id.key, net_link_parser.YAMLKEY_AVAILABILITY),
        ]
    )
    df = pd.DataFrame(
        {
            ("S1", link_id.key, ec_id.key, net_link_parser.YAMLKEY_AVAILABILITY): [
                0.8,
                0.9,
            ],
            ("S1", "OTHER", ec_id.key, net_link_parser.YAMLKEY_AVAILABILITY): [
                0.1,
                0.2,
            ],
        },
        columns=columns,
        index=["t1", "t2"],
    )
    df.attrs = {
        csv_parser.ATTR_UNIT: {
            ("S1", link_id.key, ec_id.key, net_link_parser.YAMLKEY_AVAILABILITY): "1",
            ("S1", "OTHER", ec_id.key, net_link_parser.YAMLKEY_AVAILABILITY): "1",
        }
    }

    with patch(
        "ehubx.parser.net_link_parser.yaml_parser.parse_optional_str_from_dict_node",
        return_value="profiles.csv",
    ), patch(
        "ehubx.parser.net_link_parser.yaml_parser.check_file_exists"
    ), patch("ehubx.parser.net_link_parser.csv_parser.parse", return_value=df):
        net_link_parser._parse_net_link_ec_profiles(ec_node, link_id, ec_id, net_links)

    availability = net_links.get_availability(StageId("S1"), link_id, ec_id)
    assert availability.get_value(TimeId("t1")).to_float(DimlessUnit()) == 0.8
    assert availability.get_value(TimeId("t2")).to_float(DimlessUnit()) == 0.9


def test_parse_net_link_ec_profiles_invalid_unit_raises_parsing_exception(
    ecs, link_id, ec_id
):
    ec_node = MagicMock(spec=yaml_parser.YamlDictNode)
    ec_node.file_path = "/tmp/inputs/network_links.yaml"

    net_links = NetworkLinks()
    net_links.add_id(link_id)
    net_links.add_ec(link_id, ec_id, ecs.get_unit(ec_id))

    columns = pd.MultiIndex.from_tuples(
        [("S1", link_id.key, ec_id.key, net_link_parser.YAMLKEY_AVAILABILITY)]
    )
    df = pd.DataFrame(
        {
            ("S1", link_id.key, ec_id.key, net_link_parser.YAMLKEY_AVAILABILITY): [
                0.8
            ]
        },
        columns=columns,
        index=["t1"],
    )
    df.attrs = {
        csv_parser.ATTR_UNIT: {
            ("S1", link_id.key, ec_id.key, net_link_parser.YAMLKEY_AVAILABILITY): "??"
        }
    }

    with patch(
        "ehubx.parser.net_link_parser.yaml_parser.parse_optional_str_from_dict_node",
        return_value="profiles.csv",
    ), patch(
        "ehubx.parser.net_link_parser.yaml_parser.check_file_exists"
    ), patch("ehubx.parser.net_link_parser.csv_parser.parse", return_value=df):
        with pytest.raises(exceptions.ParsingException) as excinfo:
            net_link_parser._parse_net_link_ec_profiles(ec_node, link_id, ec_id, net_links)

    assert "Invalid unit" in str(excinfo.value)


def test_parse_net_link_ec_profiles_wrong_unit_type_raises_parsing_exception(
    ecs, link_id, ec_id
):
    ec_node = MagicMock(spec=yaml_parser.YamlDictNode)
    ec_node.file_path = "/tmp/inputs/network_links.yaml"

    net_links = NetworkLinks()
    net_links.add_id(link_id)
    net_links.add_ec(link_id, ec_id, ecs.get_unit(ec_id))

    columns = pd.MultiIndex.from_tuples(
        [("S1", link_id.key, ec_id.key, net_link_parser.YAMLKEY_AVAILABILITY)]
    )
    df = pd.DataFrame(
        {
            ("S1", link_id.key, ec_id.key, net_link_parser.YAMLKEY_AVAILABILITY): [
                0.8
            ]
        },
        columns=columns,
        index=["t1"],
    )
    df.attrs = {
        csv_parser.ATTR_UNIT: {
            ("S1", link_id.key, ec_id.key, net_link_parser.YAMLKEY_AVAILABILITY): "kWh"
        }
    }

    with patch(
        "ehubx.parser.net_link_parser.yaml_parser.parse_optional_str_from_dict_node",
        return_value="profiles.csv",
    ), patch(
        "ehubx.parser.net_link_parser.yaml_parser.check_file_exists"
    ), patch("ehubx.parser.net_link_parser.csv_parser.parse", return_value=df):
        with pytest.raises(exceptions.ParsingException) as excinfo:
            net_link_parser._parse_net_link_ec_profiles(ec_node, link_id, ec_id, net_links)

    assert "Invalid unit" in str(excinfo.value)
