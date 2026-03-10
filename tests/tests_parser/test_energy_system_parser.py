import pytest

from ehubx.data import exceptions as data_exceptions
from ehubx.data.energy_system_data import EnergySystem, ExceptionKey as EnergySystemKey
from ehubx.data.unit import CurrencyUnit, DimlessUnit, LengthUnit, MassUnit, PowerUnit
from ehubx.data.value import Value
from ehubx.parser import energy_system_parser, exceptions, yaml_parser


def _make_stage_root_node():
    raw = {
        "system_params": {
            "interest_rate_def": "0.05",
            "trl_threshold": "1.0",
            "num_times_horizon": 4,
            "currency_unit": "EUR",
            "length_unit": "km",
            "mass_unit": "t",
            "power_unit": "MW",
        }
    }
    node = yaml_parser.create_node(raw, "system.yaml")
    node.set_node_path([])
    return node


def test_parse_calls_subparsers(monkeypatch):
    energy_system = EnergySystem()
    calls = {"parse_self": 0, "parse_modules": 0}

    def fake_parse_self(_):
        calls["parse_self"] += 1
        return energy_system

    def fake_parse_modules(_, energy_system_arg):
        assert energy_system_arg is energy_system
        calls["parse_modules"] += 1

    monkeypatch.setattr(energy_system_parser, "_parse_self", fake_parse_self)
    monkeypatch.setattr(energy_system_parser, "_parse_modules", fake_parse_modules)
    monkeypatch.setattr(energy_system_parser.logging, "log", lambda *_, **__: None)

    result = energy_system_parser.parse("/tmp/input")

    assert result is energy_system
    assert calls == {"parse_self": 1, "parse_modules": 1}


def test_parse_self_success(monkeypatch):
    root_node = _make_stage_root_node()

    monkeypatch.setattr(yaml_parser, "check_file_exists", lambda *_: None)
    monkeypatch.setattr(yaml_parser, "parse", lambda *_: root_node)
    monkeypatch.setattr(energy_system_parser.logging, "log_file", lambda *_, **__: None)

    energy_system = energy_system_parser._parse_self("/tmp/input")

    assert energy_system.interest_rate_def.to_float(DimlessUnit()) == 0.05
    assert energy_system.trl_threshold.to_float(DimlessUnit()) == 1.0
    assert energy_system.num_times_horizon == 4
    assert energy_system.currency_unit == CurrencyUnit.EUR
    assert energy_system.length_unit == LengthUnit.KM
    assert energy_system.mass_unit == MassUnit.T
    assert energy_system.power_unit == PowerUnit.MW


def test_parse_self_missing_stage_file(monkeypatch, tmp_path):
    def raise_missing(file_path, file_type):
        raise exceptions.MissingFileException(file_path, file_type)

    monkeypatch.setattr(yaml_parser, "check_file_exists", raise_missing)

    with pytest.raises(exceptions.MissingFileException) as exc_info:
        energy_system_parser._parse_self(str(tmp_path))

    assert exc_info.value._file_type == energy_system_parser.stage_parser.FILETYPE_STAGES


def test_parse_self_missing_root_node(monkeypatch):
    monkeypatch.setattr(yaml_parser, "check_file_exists", lambda *_: None)
    monkeypatch.setattr(yaml_parser, "parse", lambda *_: None)

    with pytest.raises(exceptions.MissingRootNodeException):
        energy_system_parser._parse_self("/tmp/input")


def test_parse_self_invalid_root_type(monkeypatch):
    root_node = yaml_parser.create_node([1, 2], "system.yaml")
    root_node.set_node_path([])

    monkeypatch.setattr(yaml_parser, "check_file_exists", lambda *_: None)
    monkeypatch.setattr(yaml_parser, "parse", lambda *_: root_node)

    with pytest.raises(exceptions.InvalidNodeTypeException):
        energy_system_parser._parse_self("/tmp/input")


def test_parse_self_missing_system_params(monkeypatch):
    root = yaml_parser.create_node({"other": 1}, "system.yaml")
    root.set_node_path([])

    monkeypatch.setattr(yaml_parser, "check_file_exists", lambda *_: None)
    monkeypatch.setattr(yaml_parser, "parse", lambda *_: root)

    with pytest.raises(exceptions.MissingNodeException):
        energy_system_parser._parse_self("/tmp/input")


def test_parse_self_raises_on_interest_rate_unit_mismatch(monkeypatch):
    root = _make_stage_root_node()

    monkeypatch.setattr(yaml_parser, "check_file_exists", lambda *_: None)
    monkeypatch.setattr(yaml_parser, "parse", lambda *_: root)
    monkeypatch.setattr(
        yaml_parser,
        "parse_mandatory_value_from_dict_node",
        lambda *_args, **_kwargs: Value(1, PowerUnit.KW),
    )
    monkeypatch.setattr(
        yaml_parser,
        "parse_optional_value_from_dict_node",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        yaml_parser,
        "parse_mandatory_int_from_dict_node",
        lambda *_args, **_kwargs: 2,
    )
    monkeypatch.setattr(
        yaml_parser,
        "parse_optional_unit_from_dict_node",
        lambda *_args, **_kwargs: None,
    )

    with pytest.raises(data_exceptions.DataException) as exc_info:
        energy_system_parser._parse_self("/tmp/input")

    assert exc_info.value.key == EnergySystemKey.INTERESTRATEDEF_VAL.value


def test_parse_self_raises_on_trl_threshold_unit_mismatch(monkeypatch):
    root = _make_stage_root_node()

    monkeypatch.setattr(yaml_parser, "check_file_exists", lambda *_: None)
    monkeypatch.setattr(yaml_parser, "parse", lambda *_: root)
    monkeypatch.setattr(
        yaml_parser,
        "parse_mandatory_value_from_dict_node",
        lambda *_args, **_kwargs: Value(0.1),
    )
    monkeypatch.setattr(
        yaml_parser,
        "parse_optional_value_from_dict_node",
        lambda *_args, **_kwargs: Value(1, PowerUnit.KW),
    )
    monkeypatch.setattr(
        yaml_parser,
        "parse_mandatory_int_from_dict_node",
        lambda *_args, **_kwargs: 2,
    )
    monkeypatch.setattr(
        yaml_parser,
        "parse_optional_unit_from_dict_node",
        lambda *_args, **_kwargs: None,
    )

    with pytest.raises(data_exceptions.DataException) as exc_info:
        energy_system_parser._parse_self("/tmp/input")

    assert exc_info.value.key == EnergySystemKey.TRLTHRESHOLD_SET.value


def test_parse_modules_assigns_parsed_data(monkeypatch):
    energy_system = EnergySystem()
    energy_system.num_times_horizon = 3

    stages = object()
    stage_root = object()
    hubs = object()
    hub_root = object()
    ecs = object()
    ec_root = object()
    net_links = object()
    net_link_root = object()
    imports = object()
    exports = object()
    demands = object()
    demand_root = object()
    load_shedding = object()
    load_shifting = object()
    techs = object()
    tech_root = object()
    stor_techs = object()
    conv_techs = object()
    solar_techs = object()
    hp_techs = object()
    ates_techs = object()
    ebm_techs = object()
    net_techs = object()
    ates_data = object()
    solar_data = object()
    self_sufficiency = object()
    times = object()

    monkeypatch.setattr(energy_system_parser.stage_parser, "parse", lambda *_: (stages, stage_root))
    monkeypatch.setattr(energy_system_parser.hub_parser, "parse_primary", lambda *_: (hubs, hub_root))
    monkeypatch.setattr(energy_system_parser.ec_parser, "parse", lambda *_: (ecs, ec_root))
    monkeypatch.setattr(
        energy_system_parser.net_link_parser,
        "parse",
        lambda *_: (net_links, net_link_root),
    )
    monkeypatch.setattr(energy_system_parser.import_export_parser, "parse_imports", lambda *_: imports)
    monkeypatch.setattr(energy_system_parser.import_export_parser, "parse_exports", lambda *_: exports)
    monkeypatch.setattr(energy_system_parser.demand_parser, "parse", lambda *_: (demands, demand_root))
    monkeypatch.setattr(energy_system_parser.load_shedding_parser, "parse", lambda *_: load_shedding)
    monkeypatch.setattr(energy_system_parser.load_shifting_parser, "parse", lambda *_: load_shifting)
    monkeypatch.setattr(energy_system_parser.tech_parser, "parse_initial", lambda *_: (techs, tech_root))
    monkeypatch.setattr(energy_system_parser.conv_tech_parser, "preprocess_in_ec_groups", lambda *_: None)
    monkeypatch.setattr(energy_system_parser.stor_tech_parser, "parse_primary", lambda *_: stor_techs)
    monkeypatch.setattr(energy_system_parser.conv_tech_parser, "parse_primary", lambda *_: conv_techs)
    monkeypatch.setattr(energy_system_parser.solar_parser, "parse_techs", lambda *_: solar_techs)
    monkeypatch.setattr(energy_system_parser.hp_tech_parser, "parse_primary", lambda *_: hp_techs)
    monkeypatch.setattr(energy_system_parser.ates_parser, "parse_primary", lambda *_: ates_techs)
    monkeypatch.setattr(energy_system_parser.ebm_tech_parser, "parse_primary", lambda *_: ebm_techs)
    monkeypatch.setattr(energy_system_parser.tech_parser, "parse_primary", lambda *_: None)
    monkeypatch.setattr(energy_system_parser.net_tech_parser, "parse_primary", lambda *_: net_techs)
    monkeypatch.setattr(energy_system_parser.ates_parser, "parse_data", lambda *_: ates_data)
    monkeypatch.setattr(energy_system_parser.solar_parser, "parse_data", lambda *_: solar_data)
    monkeypatch.setattr(energy_system_parser.self_sufficiency_parser, "parse", lambda *_: self_sufficiency)

    monkeypatch.setattr(energy_system_parser.tech_parser, "parse_secondary", lambda *_: None)
    monkeypatch.setattr(energy_system_parser.net_tech_parser, "parse_secondary", lambda *_: None)
    monkeypatch.setattr(energy_system_parser.conv_tech_parser, "parse_secondary", lambda *_: None)
    monkeypatch.setattr(energy_system_parser.hp_tech_parser, "parse_secondary", lambda *_: None)
    monkeypatch.setattr(energy_system_parser.ates_parser, "parse_secondary", lambda *_: None)
    monkeypatch.setattr(energy_system_parser.stor_tech_parser, "parse_secondary", lambda *_: None)
    monkeypatch.setattr(energy_system_parser.ebm_tech_parser, "parse_secondary", lambda *_: None)
    monkeypatch.setattr(energy_system_parser.time_parser, "parse", lambda *_: times)

    energy_system_parser._parse_modules("/tmp/input", energy_system)

    assert energy_system.stages is stages
    assert energy_system.hubs is hubs
    assert energy_system.net_links is net_links
    assert energy_system.techs is techs
    assert energy_system.conv_techs is conv_techs
    assert energy_system.solar_techs is solar_techs
    assert energy_system.hp_techs is hp_techs
    assert energy_system.ates_techs is ates_techs
    assert energy_system.stor_techs is stor_techs
    assert energy_system.ebm_techs is ebm_techs
    assert energy_system.net_techs is net_techs
    assert energy_system.ecs is ecs
    assert energy_system.imports is imports
    assert energy_system.exports is exports
    assert energy_system.demands is demands
    assert energy_system.load_shedding is load_shedding
    assert energy_system.load_shifting is load_shifting
    assert energy_system.ates_data is ates_data
    assert energy_system.solar_data is solar_data
    assert energy_system.self_sufficiency is self_sufficiency
    assert energy_system.times is times
