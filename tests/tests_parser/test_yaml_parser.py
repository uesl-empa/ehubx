import pytest
import yaml

from ehubx.data.stage_data import StageId, Stages
from ehubx.data.unit import CurrencyUnit, PowerUnit
from ehubx.data.value import Value
from ehubx.parser import exceptions, yaml_parser
from ehubx.parser.yaml_parser import ExceptionKey, YamlDictNode, YamlListNode, YamlNodeKind


def _make_dict_node(raw, file_path="file.yaml") -> YamlDictNode:
    node = yaml_parser.create_node(raw, file_path)
    assert isinstance(node, YamlDictNode)
    node.set_node_path([])
    return node


def _make_stages() -> Stages:
    stages = Stages()
    for key, year in [("s0", 2010), ("s1", 2020), ("s2", 2035)]:
        sid = StageId(key)
        stages.add_id(sid)
        stages.set_start_year(sid, year)
    return stages


def test_create_node_paths_and_copy():
    raw = {"a": 1, "b": ["x", "y"], "c": {"d": 2}}
    root = yaml_parser.create_node(raw, "input.yaml")
    assert isinstance(root, YamlDictNode)
    root.set_node_path([])

    assert root["a"].node_path_as_str == "a"
    assert root["b"].node_path_as_str == "b"
    assert root["c"].node_path_as_str == "c"
    assert root["c"]["d"].node_path_as_str == "c|d"

    copied = root.copy()
    assert isinstance(copied, YamlDictNode)
    assert copied["c"]["d"].value == 2


def test_yaml_dict_node_rejects_bracket_keys():
    node = YamlDictNode("input.yaml")
    with pytest.raises(exceptions.ParsingException):
        node.populate({"bad[key]": 1})


def test_yaml_list_node_set_id_and_duplicates():
    list_node = yaml_parser.create_node(
        [{"id": "a"}, {"id": "b"}], "input.yaml"
    )
    assert isinstance(list_node, YamlListNode)
    list_node.set_node_path(["root"])
    list_node.set_id("id")

    assert list_node.ids == {"a", "b"}
    assert list_node["a"].node_path_as_str == 'root["a"]'
    assert list_node[0].node_path_as_str == 'root["a"]'

    dup_list = yaml_parser.create_node(
        [{"id": "a"}, {"id": "a"}], "input.yaml"
    )
    assert isinstance(dup_list, YamlListNode)
    dup_list.set_node_path(["root"])
    with pytest.raises(exceptions.DuplicateIdInYamlBlockListException):
        dup_list.set_id("id")

    with pytest.raises(exceptions.ParsingException):
        list_node.set_id("id[")


def test_parse_and_check_file_exists(tmp_path):
    yaml_path = tmp_path / "simple.yaml"
    yaml_path.write_text("a: 1\n")
    root = yaml_parser.parse(str(yaml_path))
    assert isinstance(root, YamlDictNode)
    assert root["a"].value == 1

    missing_path = tmp_path / "missing.yaml"
    assert yaml_parser.parse(str(missing_path)) is None

    with pytest.raises(exceptions.MissingFileException):
        yaml_parser.check_file_exists(str(missing_path), "yaml")


def test_get_mandatory_subnode_missing():
    node = _make_dict_node({"a": 1})
    with pytest.raises(exceptions.MissingNodeException):
        yaml_parser.get_mandatory_subnode_from_dict_node(node, "b")


def test_check_node_type_mismatch():
    node = _make_dict_node({"a": 1})
    with pytest.raises(exceptions.InvalidNodeTypeException):
        yaml_parser.check_node_type(node["a"], YamlNodeKind.DICT)


def test_parse_optional_and_mandatory_primitives():
    node = _make_dict_node(
        {"b": 0, "i": "2", "f": "2.5", "s": "hello", "none": None}
    )

    assert yaml_parser.parse_optional_bool_from_dict_node(node, "b") is False
    assert yaml_parser.parse_mandatory_bool_from_dict_node(node, "b") is False
    assert yaml_parser.parse_optional_int_from_dict_node(node, "i") == 2
    assert yaml_parser.parse_mandatory_int_from_dict_node(node, "i") == 2
    assert yaml_parser.parse_optional_float_from_dict_node(node, "f") == 2.5
    assert yaml_parser.parse_mandatory_float_from_dict_node(node, "f") == 2.5
    assert yaml_parser.parse_optional_str_from_dict_node(node, "s") == "hello"
    assert yaml_parser.parse_mandatory_str_from_dict_node(node, "s") == "hello"
    assert yaml_parser.parse_optional_str_from_dict_node(node, "missing") is None
    assert yaml_parser.parse_optional_str_from_dict_node(node, "none") is None

    with pytest.raises(exceptions.MissingValueException):
        yaml_parser.parse_mandatory_str_from_dict_node(node, "none")

    bad_node = _make_dict_node({"i": "bad", "f": "bad"})
    with pytest.raises(exceptions.InvalidParamTypeException):
        yaml_parser.parse_mandatory_int_from_dict_node(bad_node, "i")
    with pytest.raises(exceptions.InvalidParamTypeException):
        yaml_parser.parse_mandatory_float_from_dict_node(bad_node, "f")


# Raw YAML text of a bool value, as a user would write it in an input file,
# and the bool it has to be parsed to
_BOOL_YAML_ACCEPTED = [
    # Converted to bool by PyYAML already
    ("true", True),
    ("True", True),
    ("TRUE", True),
    ("yes", True),
    ("Yes", True),
    ("on", True),
    ("false", False),
    ("False", False),
    ("FALSE", False),
    ("no", False),
    ("No", False),
    ("off", False),
    # Integers
    ("1", True),
    ("0", False),
    # Strings, case-insensitive and stripped
    ('"true"', True),
    ("'True'", True),
    ("TrUe", True),
    ('"TrUe"', True),
    ('"yes"', True),
    ('"1"', True),
    ('" true "', True),
    ('"false"', False),
    ("'False'", False),
    ("fAlSe", False),
    ('"fAlSe"', False),
    ('"no"', False),
    ('"0"', False),
]

_BOOL_YAML_REJECTED = [
    "2",
    "-1",
    "1.0",
    "0.0",
    "abc",
    "y",
    "n",
    '"on"',
    '"off"',
    '""',
]


def _make_bool_node(yaml_text: str) -> YamlDictNode:
    return _make_dict_node(yaml.safe_load(f"b: {yaml_text}"))


@pytest.mark.parametrize("yaml_text, expected", _BOOL_YAML_ACCEPTED)
def test_parse_bool_accepted_values(yaml_text, expected):
    node = _make_bool_node(yaml_text)
    assert yaml_parser.parse_optional_bool_from_dict_node(node, "b") is expected
    assert yaml_parser.parse_mandatory_bool_from_dict_node(node, "b") is expected


@pytest.mark.parametrize("yaml_text", _BOOL_YAML_REJECTED)
def test_parse_bool_rejected_values(yaml_text):
    node = _make_bool_node(yaml_text)
    with pytest.raises(exceptions.InvalidParamTypeException):
        yaml_parser.parse_optional_bool_from_dict_node(node, "b")
    with pytest.raises(exceptions.InvalidParamTypeException):
        yaml_parser.parse_mandatory_bool_from_dict_node(node, "b")


def test_parse_bool_missing_or_empty_value():
    node = _make_dict_node({"empty": None})
    assert yaml_parser.parse_optional_bool_from_dict_node(node, "missing") is None
    assert yaml_parser.parse_optional_bool_from_dict_node(node, "empty") is None
    with pytest.raises(exceptions.MissingNodeException):
        yaml_parser.parse_mandatory_bool_from_dict_node(node, "missing")
    with pytest.raises(exceptions.MissingValueException):
        yaml_parser.parse_mandatory_bool_from_dict_node(node, "empty")


def test_parse_units_and_values_with_mismatches():
    node = _make_dict_node(
        {"unit": "kW", "bad_unit": "nope", "val": "3 kW", "bad": "x"}
    )

    unit = yaml_parser.parse_optional_unit_from_dict_node(node, "unit")
    assert unit.same_type_as(PowerUnit.KW)

    with pytest.raises(exceptions.InvalidValueException):
        yaml_parser.parse_optional_unit_from_dict_node(
            node, "bad_unit", expected_unit=PowerUnit.KW
        )

    value = yaml_parser.parse_mandatory_value_from_dict_node(node, "val")
    assert isinstance(value, Value)

    with pytest.raises(exceptions.InvalidValueException):
        yaml_parser.parse_mandatory_value_from_dict_node(
            node, "val", expected_unit=CurrencyUnit.CHF
        )

    with pytest.raises(exceptions.InvalidValueException):
        yaml_parser.parse_optional_value_from_dict_node(node, "bad")


def test_parse_str_list_from_dict_node_variants():
    node = _make_dict_node({"list": ["a", "b"], "single": "x", "none": None})

    assert yaml_parser.parse_str_list_from_dict_node(node, "list") == ["a", "b"]
    assert yaml_parser.parse_str_list_from_dict_node(node, "single") == ["x"]
    assert yaml_parser.parse_str_list_from_dict_node(node, "missing") == []

    with pytest.raises(exceptions.MissingValueException):
        yaml_parser.parse_str_list_from_dict_node(node, "missing", optional=False)

    with pytest.raises(exceptions.MissingValueException):
        yaml_parser.parse_str_list_from_dict_node(node, "none", optional=False)

    bad_node = _make_dict_node({"bad": {"x": 1}})
    with pytest.raises(exceptions.InvalidNodeTypeException):
        yaml_parser.parse_str_list_from_dict_node(bad_node, "bad")


def test_parse_yeardep_float_and_value_success():
    stages = _make_stages()
    node = _make_dict_node({"param": [[2020, 1.0], [2030, 2.0]]})

    float_map = yaml_parser.parse_optional_yeardep_float_from_dict_node(
        node, "param", stages
    )
    assert float_map is not None
    assert float_map[next(s for s in stages.ids if s.key == "s0")] == 1.0
    assert float_map[next(s for s in stages.ids if s.key == "s1")] == 1.0
    assert float_map[next(s for s in stages.ids if s.key == "s2")] == 2.0

    value_node = _make_dict_node({"param": [[2020, "1 kW"], [2030, "2 kW"]]})
    value_map = yaml_parser.parse_optional_yeardep_value_from_dict_node(
        value_node, "param", stages, expected_unit=PowerUnit.KW
    )
    assert value_map is not None
    assert value_map[next(s for s in stages.ids if s.key == "s0")].to_float(
        PowerUnit.KW
    ) == 1.0


def test_parse_yeardep_float_errors_with_exception_keys():
    stages = _make_stages()

    node = _make_dict_node({"param": ["not-a-list"]})
    with pytest.raises(exceptions.YearDepFormatException) as exc_info:
        yaml_parser.parse_optional_yeardep_float_from_dict_node(node, "param", stages)
    assert ExceptionKey.YEARDEP_ENTRYNOTALIST.value in str(exc_info.value)

    node = _make_dict_node({"param": [[2020]]})
    with pytest.raises(exceptions.YearDepFormatException) as exc_info:
        yaml_parser.parse_optional_yeardep_float_from_dict_node(node, "param", stages)
    assert ExceptionKey.YEARDEP_ENTRYNOTLENGTHTWO.value in str(exc_info.value)

    node = _make_dict_node({"param": [[{"x": 1}, 2.0]]})
    with pytest.raises(exceptions.YearDepFormatException) as exc_info:
        yaml_parser.parse_optional_yeardep_float_from_dict_node(node, "param", stages)
    assert ExceptionKey.YEARDEP_ENTRYPARTISNOTAVALUE.value in str(exc_info.value)


def test_parse_yeardep_value_and_mandatory_errors():
    stages = _make_stages()

    node = _make_dict_node({"param": []})
    with pytest.raises(exceptions.EmptyListNodeException):
        yaml_parser.parse_mandatory_yeardep_float_from_dict_node(node, "param", stages)

    bad_kind = _make_dict_node({"param": {"x": 1}})
    with pytest.raises(exceptions.InvalidNodeTypeException):
        yaml_parser.parse_optional_yeardep_float_from_dict_node(bad_kind, "param", stages)

    with pytest.raises(exceptions.InvalidNodeTypeException):
        yaml_parser.parse_mandatory_yeardep_value_from_dict_node(bad_kind, "param", stages)

    bad_unit = _make_dict_node({"param": [[2020, "1 kW"], [2030, "2 CHF"]]})
    with pytest.raises(exceptions.InvalidValueException):
        yaml_parser.parse_optional_yeardep_value_from_dict_node(
            bad_unit, "param", stages, expected_unit=PowerUnit.KW
        )

def test_parse_yeardep_years_not_increasing_raises():
    stages = _make_stages()
    node = _make_dict_node({"param": [[2020, 1.0], [2015, 2.0]]})

    with pytest.raises(exceptions.YearDepFormatException) as exc_info:
        yaml_parser.parse_mandatory_yeardep_float_from_dict_node(node, "param", stages)
    assert ExceptionKey.YEARDEP_YEARSNOTINCREASING.value in str(exc_info.value)

    with pytest.raises(exceptions.YearDepFormatException) as exc_info:
        yaml_parser.parse_optional_yeardep_float_from_dict_node(node, "param", stages)
    assert ExceptionKey.YEARDEP_YEARSNOTINCREASING.value in str(exc_info.value)

    with pytest.raises(exceptions.YearDepFormatException) as exc_info:
        yaml_parser.parse_mandatory_yeardep_value_from_dict_node(node, "param", stages)
    assert ExceptionKey.YEARDEP_YEARSNOTINCREASING.value in str(exc_info.value)

    with pytest.raises(exceptions.YearDepFormatException) as exc_info:
        yaml_parser.parse_optional_yeardep_value_from_dict_node(node, "param", stages)
    assert ExceptionKey.YEARDEP_YEARSNOTINCREASING.value in str(exc_info.value)
