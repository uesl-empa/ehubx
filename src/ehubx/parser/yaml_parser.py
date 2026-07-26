import os
from enum import Enum
from typing import Any, Dict, List, Optional, Self, Set, Union

import yaml

import ehubx.data.exceptions as data_exceptions
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.unit import Unit
from ehubx.data.value import Value
from ehubx.parser import exceptions


class YamlNodeKind(Enum):
    DICT = "dict"
    LIST = "list"
    VALUE = "value"


class ParamType(Enum):
    STR = str
    INT = int
    FLOAT = float


class ExceptionKey(Enum):
    YEARDEP_ENTRYNOTALIST = "entry is not a list node"
    YEARDEP_ENTRYNOTLENGTHTWO = "entry does not have length 2"
    YEARDEP_ENTRYPARTISNOTAVALUE = "entry is not a value node"
    YEARDEP_YEARSNOTINCREASING = "entry years are not strictly increasing"


# Literals
LOG_MODULE_STR: str = "pars/yaml"


class YamlNode:
    @property
    def node_kind(self) -> YamlNodeKind:
        return self._node_kind

    def __init__(
        self, node_kind: YamlNodeKind, file_path: Optional[str] = None
    ) -> None:
        if file_path is None:
            file_path = ""
        self._node_kind = node_kind
        self._parent: Optional[YamlNode] = None
        self._file_path: str = file_path
        self._node_path: List[str] = []

    def copy(self):
        raise NotImplementedError()

    def set_parent(self, parent: Self) -> None:
        self._parent = parent

    def clear_parent(self) -> None:
        self._parent = None

    @property
    def node_path(self) -> List[str]:
        return self._node_path

    @property
    def node_path_as_str(self) -> str:
        return "|".join(self._node_path)

    def set_node_path(self, node_path: List[str]) -> None:
        raise NotImplementedError()

    def update_node_path(self) -> None:
        if self.node_path is None:
            msg = "Tried to update a node's path which does not exist yet"
            raise exceptions.ParsingException(
                self.file_path, msg, module=LOG_MODULE_STR
            )
        self.set_node_path(self.node_path)

    @property
    def file_path(self) -> str:
        return self._file_path

    # ---------------- #
    # Abstract methods #
    # ---------------- #
    @property
    def value(self) -> Any:
        raise NotImplementedError(
            (f".value not implemented for YamlNode of type {type(self)}")
        )

    def add_dict_child(self, child_key: str, child: Any) -> None:
        raise NotImplementedError(
            (f"add_dict_child not implemented for YamlNode of type {type(self)}")
        )

    def add_list_child(self, child: Any) -> None:
        raise NotImplementedError(
            (f"add_list_child not implemented for YamlNode of type {type(self)}")
        )

    def remove_dict_child(self, child_key: str) -> None:
        raise NotImplementedError(
            (f"remove_dict_child not implemented for YamlNode of type {type(self)}")
        )

    def remove_list_child(self, child: Any) -> None:
        raise NotImplementedError(
            (f"remove_list_child not implemented for YamlNode of type {type(self)}")
        )

    def __getitem__(self, key: Any) -> Optional[Any]:
        raise NotImplementedError(
            (f"__get__item not implemented for YamlNode of type {type(self)}")
        )

    def __len__(self) -> int:
        raise NotImplementedError(
            (f"__len__ not implemented for YamlNode of type {type(self)}")
        )

    def __iter__(self):
        raise NotImplementedError(
            (f"__iter__ not implemented for YamlNode of type {type(self)}")
        )

    def set_id(self, id_key: str) -> None:
        raise NotImplementedError(
            (f"set_id not implemented for YamlNode of type {type(self)}")
        )


class YamlDictNode(YamlNode):
    def __init__(self, file_path: Optional[str] = None) -> None:
        super().__init__(YamlNodeKind.DICT, file_path)
        self._children: Dict[str, YamlNode] = {}

    def copy(self):
        new = YamlDictNode(self.file_path)
        for child_key, child in self._children.items():
            new.add_dict_child(child_key, child.copy())
        return new

    def add_dict_child(self, child_key: str, child: YamlNode) -> None:
        if child_key in self._children:
            msg = (
                "Tried to add child to YamlDictNode with key "
                + f"{child_key} that already exists"
            )
            raise exceptions.ParsingException(
                self.file_path, msg, module=LOG_MODULE_STR
            )
        self._children[child_key] = child
        child.set_parent(self)

    def add_child_value(self, value_key: str, value: Any) -> None:
        new_value_node = YamlValueNode(self.file_path)
        new_value_node.set_value(value)
        self.add_dict_child(value_key, new_value_node)

    def remove_dict_child(self, child_key: str) -> None:
        if child_key not in self._children:
            msg = (
                "Tried to remove child of YamlDictNode with key "
                + f"{child_key} that does not exist"
            )
            raise exceptions.ParsingException(
                self.file_path, msg, module=LOG_MODULE_STR
            )
        self._children[child_key].clear_parent()
        self._children.pop(child_key)

    def set_node_path(self, node_path: List[str]) -> None:
        self._node_path = node_path
        for child_key, child in self._children.items():
            child_node_path = node_path + [child_key]
            child.set_node_path(child_node_path)

    def populate(self, node_raw: Dict[str, Any]) -> None:
        self._children.clear()
        for child_key, subnode_raw in node_raw.items():
            # Keys may not contain square brackets
            if ("[" in child_key) or ("]" in child_key):
                msg = (
                    "Tried to populate a YamlDictNode with key "
                    + f"{child_key} that contains square brackets []"
                )
                raise exceptions.ParsingException(
                    self.file_path, msg, module=LOG_MODULE_STR
                )
            child = create_node(subnode_raw, self.file_path)
            child.set_parent(self)
            self._children[child_key] = child

    def __getitem__(self, key: str) -> Optional[YamlNode]:
        return self._children.get(key, None)

    def __contains__(self, item: Any) -> bool:
        return item in self._children

    def __repr__(self) -> str:
        return f"<YamlDictNode at {self.node_path_as_str}>"


class YamlListNode(YamlNode):
    def __init__(self, file_path: Optional[str] = None) -> None:
        super().__init__(YamlNodeKind.LIST, file_path)
        self._children: List[YamlNode] = []
        self._iter_cnt: int = -1
        self._id_key: Optional[str] = None

    def copy(self):
        new = YamlListNode(self.file_path)
        for child in self._children:
            new.add_list_child(child.copy())
        if self._id_key is not None:
            new.set_id(self._id_key)
        return new

    def add_list_child(self, child: YamlNode) -> None:
        if child in self._children:
            msg = (
                "Tried to add child to YamlListNode that already "
                + "contains this child"
            )
            raise exceptions.ParsingException(
                self.file_path, msg, module=LOG_MODULE_STR
            )
        self._children.append(child)
        child.set_parent(self)

    def remove_list_child(self, child: YamlNode) -> None:
        if child not in self._children:
            msg = (
                "Tried to remove child from YamlListNode that does not "
                + "contain this child"
            )
            raise exceptions.ParsingException(
                self.file_path, msg, module=LOG_MODULE_STR
            )
        child.clear_parent()
        self._children.remove(child)

    def set_node_path(self, node_path: List[str]) -> None:
        if len(node_path) == 0:
            node_path = ["_root_"]
        self._node_path = node_path
        if self._id_key is None:  # node|path[0], node|path[1], ...
            for child_pos, child in enumerate(self._children):
                child_node_path = node_path.copy()
                child_node_path[-1] += f"[{child_pos}]"
                child.set_node_path(child_node_path)
        if self._id_key is not None:  # node|path["id1"], node|path["id2"]
            for child in self._children:
                child_node_path = node_path.copy()
                child_id_node = child[self._id_key]
                assert isinstance(child_id_node, YamlValueNode)
                child_node_path[-1] += f'["{child_id_node.value}"]'
                child.set_node_path(child_node_path)

    def populate(self, node_raw: List[Any]):
        self._children.clear()
        for subnode_raw in node_raw:
            child = create_node(subnode_raw, self.file_path)
            self.add_list_child(child)

    def set_id(self, id_key: str) -> None:
        # Id key may not contain square brackets
        if ("[" in id_key) or ("]" in id_key):
            msg = (
                "Tried to set id of YamlListNode with id_key "
                + f"{id_key} that contains square brackets []"
            )
            raise exceptions.ParsingException(
                self.file_path, msg, module=LOG_MODULE_STR
            )
        child_ids = []
        for child in self._children:
            child_id = parse_mandatory_str_from_dict_node(child, id_key)
            child_ids.append(child_id)
        for child_id in child_ids:
            id_positions = [
                position
                for position, child_id_ in enumerate(child_ids)
                if child_id_ == child_id
            ]
            if len(id_positions) > 1:
                raise exceptions.DuplicateIdInYamlBlockListException(
                    self.file_path,
                    self.node_path_as_str,
                    child_id,
                    id_positions,
                    module=LOG_MODULE_STR,
                )
        self._id_key = id_key
        # Update child node paths from node|path[0] to node|path["id"]
        self.update_node_path()

    @property
    def ids(self) -> Set[str]:
        if self._id_key is None:
            msg = (
                "Tried to get ids of YamlListNode whose ids have not "
                + "been set be the set_id method"
            )
            raise exceptions.ParsingException(
                self.file_path, msg, module=LOG_MODULE_STR
            )
        ids = set()
        for child in self._children:
            child_id_node = child[self._id_key]
            assert isinstance(child_id_node, YamlValueNode)
            ids.add(child_id_node.value)
        return ids

    def __getitem__(self, key: Union[str, int]) -> Optional[YamlNode]:
        if isinstance(key, int):
            return self._children[key]
        if isinstance(key, str):
            if self._id_key is None:
                msg = (
                    "Tried to get a child node by id from a YamlListNode "
                    "whose ids have not been set be the set_id method"
                )
                raise exceptions.ParsingException(
                    self.file_path, msg, module=LOG_MODULE_STR
                )
            for child in self._children:
                child_id_node = child[self._id_key]
                assert isinstance(child_id_node, YamlValueNode)
                if child_id_node.value == key:
                    return child
            return None
        msg = (
            "YamlListNode does not contain a child with an id_key of "
            + f"{self._id_key}={key}"
        )
        raise exceptions.ParsingException(self.file_path, msg, module=LOG_MODULE_STR)

    def __iter__(self):
        self._iter_cnt = -1
        return self

    def __next__(self) -> YamlNode:
        self._iter_cnt += 1
        if self._iter_cnt >= len(self._children):
            raise StopIteration
        return self._children[self._iter_cnt]

    def __len__(self) -> int:
        return len(self._children)

    def __repr__(self) -> str:
        return f"<YamlListNode at {self.node_path_as_str}>"


class YamlValueNode(YamlNode):
    def __init__(self, file_path: Optional[str] = None) -> None:
        super().__init__(YamlNodeKind.VALUE, file_path)
        self._value: Any = None

    def copy(self):
        new = YamlValueNode(self.file_path)
        new.populate(self._value)
        return new

    def set_node_path(self, node_path: List[str]) -> None:
        self._node_path = node_path

    def populate(self, node_raw: Any) -> None:
        self._value = node_raw

    def __repr__(self) -> str:
        return f"<YamlValueNode at {self.node_path_as_str}>: {self._value}"

    @property
    def value(self) -> Any:
        return self._value

    def set_value(self, value: Any) -> None:
        self._value = value


NODE_KIND_TO_TYPE: Dict[YamlNodeKind, type] = {
    YamlNodeKind.DICT: YamlDictNode,
    YamlNodeKind.LIST: YamlListNode,
    YamlNodeKind.VALUE: YamlValueNode,
}


def create_node(node_raw: Any, file_path: Optional[str] = None) -> YamlNode:
    if isinstance(node_raw, dict):
        dict_node = YamlDictNode(file_path)
        dict_node.populate(node_raw)
        return dict_node
    if isinstance(node_raw, list):
        list_node = YamlListNode(file_path)
        list_node.populate(node_raw)
        return list_node
    if node_raw is None or isinstance(node_raw, (int, float, str)):
        value_node = YamlValueNode(file_path)
        value_node.populate(node_raw)
        return value_node
    if file_path is None:
        file_path = "[unknown_file_path]"
    msg = f"Cannot create a node from raw data of type {type(node_raw)}"
    raise exceptions.ParsingException(file_path, msg, module=LOG_MODULE_STR)


def parse(file_path: str) -> Optional[YamlNode]:
    if not os.path.isfile(file_path):
        return None
    with open(file_path, "r", encoding="utf-8") as file_reader:
        root_raw = yaml.safe_load(file_reader)
    if root_raw is None:
        return None
    root = create_node(root_raw, file_path)
    root.set_node_path([])
    return root


def check_node_type(node: YamlNode, expected_node_kind: YamlNodeKind) -> None:
    expected_node_type = NODE_KIND_TO_TYPE[expected_node_kind]
    if not isinstance(node, expected_node_type):
        actual_node_type: str = f"{type(node)}"
        expected_node_type_str: str = f"{expected_node_type}"
        raise exceptions.InvalidNodeTypeException(
            node.file_path,
            node.node_path_as_str,
            expected_node_type_str,
            actual_node_type,
            module=LOG_MODULE_STR,
        )


def check_file_exists(file_path: str, file_type: str) -> None:
    if not os.path.isfile(file_path):
        raise exceptions.MissingFileException(
            file_path, file_type, module=LOG_MODULE_STR
        )


def get_mandatory_subnode_from_dict_node(
    parent_node: YamlNode, subnode_key: str
) -> YamlNode:
    check_node_type(parent_node, YamlNodeKind.DICT)
    node = parent_node[subnode_key]
    if node is None:
        presumed_node_path_str = parent_node.node_path_as_str + f"|{subnode_key}"
        raise exceptions.MissingNodeException(
            parent_node.file_path, presumed_node_path_str, module=LOG_MODULE_STR
        )
    return node


def parse_optional_bool_from_dict_node(
    parent_node: YamlNode, value_key: str
) -> Optional[bool]:
    check_node_type(parent_node, YamlNodeKind.DICT)
    value_node = parent_node[value_key]
    # Value node does not exist
    if value_node is None:
        return None
    # Value node exists but value is empty
    check_node_type(value_node, YamlNodeKind.VALUE)
    if value_node.value is None:
        return None
    # Transform to requested type
    value_as_bool = parse_bool_from_value_node(value_node)
    # Return
    return value_as_bool


def parse_mandatory_bool_from_dict_node(parent_node: YamlNode, value_key: str) -> int:
    check_node_type(parent_node, YamlNodeKind.DICT)
    value_node = get_mandatory_subnode_from_dict_node(parent_node, value_key)
    check_node_type(value_node, YamlNodeKind.VALUE)
    # Value node has to exist
    if value_node.value is None:
        raise exceptions.MissingValueException(
            parent_node.file_path, value_node.node_path_as_str, module=LOG_MODULE_STR
        )
    # Transform to requested type
    value_as_bool = parse_bool_from_value_node(value_node)
    # Return
    return value_as_bool


def parse_optional_int_from_dict_node(
    parent_node: YamlNode, value_key: str
) -> Optional[int]:
    check_node_type(parent_node, YamlNodeKind.DICT)
    value_node = parent_node[value_key]
    # Value node does not exist
    if value_node is None:
        return None
    # Value node exists but value is empty
    check_node_type(value_node, YamlNodeKind.VALUE)
    if value_node.value is None:
        return None
    # Transform to requested type
    value_as_int = parse_int_from_value_node(value_node)
    # Return
    return value_as_int


def parse_mandatory_int_from_dict_node(parent_node: YamlNode, value_key: str) -> int:
    check_node_type(parent_node, YamlNodeKind.DICT)
    value_node = get_mandatory_subnode_from_dict_node(parent_node, value_key)
    check_node_type(value_node, YamlNodeKind.VALUE)
    # Value node has to exist
    if value_node.value is None:
        raise exceptions.MissingValueException(
            parent_node.file_path, value_node.node_path_as_str, module=LOG_MODULE_STR
        )
    # Transform to requested type
    value_as_int = parse_int_from_value_node(value_node)
    # Return
    return value_as_int


def parse_optional_float_from_dict_node(
    parent_node: YamlNode, value_key: str
) -> Optional[float]:
    check_node_type(parent_node, YamlNodeKind.DICT)
    value_node = parent_node[value_key]
    # Value node does not exist
    if value_node is None:
        return None
    # Value node exists but value is empty
    check_node_type(value_node, YamlNodeKind.VALUE)
    if value_node.value is None:
        return None
    # Transform to requested type
    value_as_float = parse_float_from_value_node(value_node)
    # Return
    return value_as_float


def parse_mandatory_float_from_dict_node(
    parent_node: YamlNode, value_key: str
) -> float:
    check_node_type(parent_node, YamlNodeKind.DICT)
    value_node = get_mandatory_subnode_from_dict_node(parent_node, value_key)
    check_node_type(value_node, YamlNodeKind.VALUE)
    # Value node has to exist
    if value_node.value is None:
        raise exceptions.MissingValueException(
            parent_node.file_path, value_node.node_path_as_str, module=LOG_MODULE_STR
        )
    # Transform to requested type
    value_as_float = parse_float_from_value_node(value_node)
    # Return
    return value_as_float


def parse_optional_str_from_dict_node(
    parent_node: YamlNode, value_key: str
) -> Optional[str]:
    check_node_type(parent_node, YamlNodeKind.DICT)
    value_node = parent_node[value_key]
    # Value node does not exist
    if value_node is None:
        return None
    # Value node exists but value is empty
    check_node_type(value_node, YamlNodeKind.VALUE)
    if value_node.value is None:
        return None
    # Transform to requested type
    value_as_str = parse_str_from_value_node(value_node)
    # Return
    return value_as_str


def parse_mandatory_str_from_dict_node(parent_node: YamlNode, value_key: str) -> str:
    check_node_type(parent_node, YamlNodeKind.DICT)
    value_node = get_mandatory_subnode_from_dict_node(parent_node, value_key)
    check_node_type(value_node, YamlNodeKind.VALUE)
    # Value node has to exist
    if value_node.value is None:
        raise exceptions.MissingValueException(
            parent_node.file_path, value_node.node_path_as_str, module=LOG_MODULE_STR
        )
    # Transform to requested type
    value_as_str = parse_str_from_value_node(value_node)
    # Return
    return value_as_str


def parse_mandatory_unit_from_dict_node(
    parent_node: YamlNode, value_key: str, expected_unit: Optional[Unit] = None
) -> Unit:
    unit_str = parse_mandatory_str_from_dict_node(parent_node, value_key)
    try:
        unit = Unit.from_str(unit_str)
    except data_exceptions.UnitException as ex:
        raise exceptions.InvalidValueException(
            parent_node.file_path,
            parent_node.node_path_as_str + f"|{value_key}",
            invalidity_reason=f"Invalid unit {unit_str} detected.",
            module=LOG_MODULE_STR,
        ) from ex
    if expected_unit is not None and not unit.same_type_as(expected_unit):
        raise exceptions.InvalidValueException(
            parent_node.file_path,
            parent_node.node_path_as_str + f"|{value_key}",
            invalidity_reason=f"Unit mismatch: expected {expected_unit}, got {unit}.",
            module=LOG_MODULE_STR,
        )
    return unit


def parse_optional_unit_from_dict_node(
    parent_node: YamlNode, value_key: str, expected_unit: Optional[Unit] = None
) -> Optional[Unit]:
    unit_str = parse_optional_str_from_dict_node(parent_node, value_key)
    if unit_str is None:
        return None
    try:
        unit = Unit.from_str(unit_str)
    except data_exceptions.UnitException as ex:
        raise exceptions.InvalidValueException(
            parent_node.file_path,
            parent_node.node_path_as_str + f"|{value_key}",
            invalidity_reason=f"Invalid unit {unit_str} detected.",
            module=LOG_MODULE_STR,
        ) from ex
    if expected_unit is not None and not unit.same_type_as(expected_unit):
        raise exceptions.InvalidValueException(
            parent_node.file_path,
            parent_node.node_path_as_str + f"|{value_key}",
            invalidity_reason=f"Unit mismatch: expected {expected_unit}, got {unit}.",
            module=LOG_MODULE_STR,
        )
    return unit


def parse_mandatory_value_from_dict_node(
    parent_node: YamlNode, value_key: str, expected_unit: Optional[Unit] = None
) -> Value:
    value_str = parse_mandatory_str_from_dict_node(parent_node, value_key)
    try:
        value = Value.from_str(value_str)
    except data_exceptions.ValueException as ex:
        raise exceptions.InvalidValueException(
            parent_node.file_path,
            parent_node.node_path_as_str + f"|{value_key}",
            invalidity_reason=(
                f"Invalid value '{value_str}' detected. "
                f"Reason for this: {ex.reason}"
            ),
            module=LOG_MODULE_STR,
        ) from ex
    if expected_unit is not None and not value.unit.same_type_as(expected_unit):
        raise exceptions.InvalidValueException(
            parent_node.file_path,
            parent_node.node_path_as_str + f"|{value_key}",
            invalidity_reason=(
                f"Unit mismatch: expected {expected_unit}, " f"got {value.unit}."
            ),
            module=LOG_MODULE_STR,
        )
    return value


def parse_optional_value_from_dict_node(
    parent_node: YamlNode, value_key: str, expected_unit: Optional[Unit] = None
) -> Optional[Value]:
    value_str = parse_optional_str_from_dict_node(parent_node, value_key)
    if value_str is None:
        return None
    try:
        value = Value.from_str(value_str)
    except data_exceptions.ValueException as ex:
        raise exceptions.InvalidValueException(
            parent_node.file_path,
            parent_node.node_path_as_str + f"|{value_key}",
            invalidity_reason=(
                f"Invalid value '{value_str}' detected. "
                f"Reason for this: {ex.reason}"
            ),
            module=LOG_MODULE_STR,
        ) from ex
    if expected_unit is not None and not value.unit.same_type_as(expected_unit):
        raise exceptions.InvalidValueException(
            parent_node.file_path,
            parent_node.node_path_as_str + f"|{value_key}",
            invalidity_reason=(
                f"Unit mismatch: expected {expected_unit}, " f"got {value.unit}."
            ),
            module=LOG_MODULE_STR,
        )
    return value


def parse_str_list_from_dict_node(
    parent_node: YamlNode, value_key: str, optional: bool = True
) -> List[str]:
    list_node = parent_node[value_key]
    if list_node is None:
        if optional:
            return []
        raise exceptions.MissingValueException(
            parent_node.file_path,
            parent_node.node_path_as_str + f"|{value_key}",
            module=LOG_MODULE_STR,
        )
    if isinstance(list_node, YamlValueNode):
        if list_node.value is None:
            if optional:
                return []
            raise exceptions.MissingValueException(
                parent_node.file_path,
                parent_node.node_path_as_str + f"|{value_key}",
                module=LOG_MODULE_STR,
            )
        return [list_node.value]
    if isinstance(list_node, YamlListNode):
        values: List[str] = []
        for child_node in list_node:
            check_node_type(child_node, YamlNodeKind.VALUE)
            if child_node.value is None:
                raise exceptions.MissingValueException(
                    parent_node.file_path,
                    child_node.node_path_as_str,
                    module=LOG_MODULE_STR,
                )
            value_as_str = parse_str_from_value_node(child_node)
            values.append(value_as_str)
        return values
    expected_type = f"{YamlNodeKind.VALUE} or {YamlNodeKind.LIST}"
    actual_type = f"{type(list_node)}"
    raise exceptions.InvalidNodeTypeException(
        parent_node.file_path,
        list_node.node_path_as_str,
        expected_type,
        actual_type,
        module=LOG_MODULE_STR,
    )


def parse_optional_yeardep_float_from_dict_node(
    parent_node: YamlNode, value_key: str, stages: Stages
) -> Optional[Dict[StageId, float]]:
    check_node_type(parent_node, YamlNodeKind.DICT)
    node = parent_node[value_key]
    if node is None:
        return None
    if isinstance(node, YamlValueNode):
        if node.value is None:
            return None
        value = parse_float_from_value_node(node)
        return {s: value for s in stages.ids}
    if isinstance(node, YamlListNode):
        year_to_value_dict: Dict[int, float] = {}
        previous_year = -float("inf")
        for doublet_node in node:
            if not isinstance(doublet_node, YamlListNode):
                raise exceptions.YearDepFormatException(
                    parent_node.file_path,
                    doublet_node.node_path_as_str,
                    ExceptionKey.YEARDEP_ENTRYNOTALIST.value,
                    module=LOG_MODULE_STR,
                )
            if not len(doublet_node) == 2:
                raise exceptions.YearDepFormatException(
                    parent_node.file_path,
                    doublet_node.node_path_as_str,
                    ExceptionKey.YEARDEP_ENTRYNOTLENGTHTWO.value,
                    module=LOG_MODULE_STR,
                )
            year: int = 0
            year_value: float = 0
            for i in range(2):
                doublet_node_i = doublet_node[i]
                assert doublet_node_i is not None
                if not isinstance(doublet_node_i, YamlValueNode):
                    raise exceptions.YearDepFormatException(
                        parent_node.file_path,
                        doublet_node_i.node_path_as_str,
                        ExceptionKey.YEARDEP_ENTRYPARTISNOTAVALUE.value,
                        module=LOG_MODULE_STR,
                    )
                if i == 0:
                    year = parse_int_from_value_node(doublet_node_i)
                if i == 1:
                    year_value = parse_float_from_value_node(doublet_node_i)
            if not year > previous_year:
                raise exceptions.YearDepFormatException(
                    parent_node.file_path,
                    doublet_node.node_path_as_str,
                    ExceptionKey.YEARDEP_YEARSNOTINCREASING.value,
                    module=LOG_MODULE_STR,
                )
            previous_year = year
            year_to_value_dict[year] = year_value
        stage_to_value_dict = _transform_yeartofloat_to_stagetofloat(
            year_to_value_dict, stages
        )
        return stage_to_value_dict
    # Wrong yaml node kind
    expected_type = f"{YamlNodeKind.VALUE} or {YamlNodeKind.DICT}"
    actual_type = f"{type(node)}"
    raise exceptions.InvalidNodeTypeException(
        parent_node.file_path,
        node.node_path_as_str,
        expected_type,
        actual_type,
        module=LOG_MODULE_STR,
    )


def parse_mandatory_yeardep_float_from_dict_node(
    parent_node: YamlNode, value_key: str, stages: Stages
) -> Dict[StageId, float]:
    check_node_type(parent_node, YamlNodeKind.DICT)
    node = get_mandatory_subnode_from_dict_node(parent_node, value_key)
    if isinstance(node, YamlValueNode):
        value = parse_mandatory_float_from_dict_node(parent_node, value_key)
        return {s: value for s in stages.ids}
    if isinstance(node, YamlListNode):
        year_to_value_dict: Dict[int, float] = {}
        if len(node) == 0:
            raise exceptions.EmptyListNodeException(
                parent_node.file_path, node.node_path_as_str, module=LOG_MODULE_STR
            )
        previous_year = -float("inf")
        for doublet_node in node:
            if not isinstance(doublet_node, YamlListNode):
                raise exceptions.YearDepFormatException(
                    parent_node.file_path,
                    doublet_node.node_path_as_str,
                    ExceptionKey.YEARDEP_ENTRYNOTALIST.value,
                    module=LOG_MODULE_STR,
                )
            if not len(doublet_node) == 2:
                raise exceptions.YearDepFormatException(
                    parent_node.file_path,
                    doublet_node.node_path_as_str,
                    ExceptionKey.YEARDEP_ENTRYNOTLENGTHTWO.value,
                    module=LOG_MODULE_STR,
                )
            year: int = 0
            year_value: float = 0
            for i in range(2):
                doublet_node_i = doublet_node[i]
                assert doublet_node_i is not None
                if not isinstance(doublet_node[i], YamlValueNode):
                    raise exceptions.YearDepFormatException(
                        parent_node.file_path,
                        doublet_node_i.node_path_as_str,
                        ExceptionKey.YEARDEP_ENTRYPARTISNOTAVALUE.value,
                        module=LOG_MODULE_STR,
                    )
                if i == 0:
                    year = parse_int_from_value_node(doublet_node_i)
                if i == 1:
                    year_value = parse_float_from_value_node(doublet_node_i)
            if not year > previous_year:
                raise exceptions.YearDepFormatException(
                    parent_node.file_path,
                    doublet_node.node_path_as_str,
                    ExceptionKey.YEARDEP_YEARSNOTINCREASING.value,
                    module=LOG_MODULE_STR,
                )
            previous_year = year
            year_to_value_dict[year] = year_value
        stage_to_value_dict = _transform_yeartofloat_to_stagetofloat(
            year_to_value_dict, stages
        )
        return stage_to_value_dict
    # Wrong yaml node kind
    expected_type = f"{YamlNodeKind.VALUE} or {YamlNodeKind.LIST}"
    actual_type = f"{type(node)}"
    raise exceptions.InvalidNodeTypeException(
        parent_node.file_path,
        node.node_path_as_str,
        expected_type,
        actual_type,
        module=LOG_MODULE_STR,
    )


def parse_optional_yeardep_value_from_dict_node(
    parent_node: YamlNode,
    value_key: str,
    stages: Stages,
    expected_unit: Optional[Unit] = None,
) -> Optional[Dict[StageId, Value]]:
    check_node_type(parent_node, YamlNodeKind.DICT)
    node = parent_node[value_key]
    if node is None:
        return None
    if isinstance(node, YamlValueNode):
        value = parse_optional_value_from_dict_node(
            parent_node, value_key, expected_unit=expected_unit
        )
        if value is None:
            return None
        return {s: value for s in stages.ids}
    if isinstance(node, YamlListNode):
        year_to_value_dict: Dict[int, Value] = {}
        previous_year = -float("inf")
        first_unit: Optional[Unit] = None
        for doublet_node in node:
            if not isinstance(doublet_node, YamlListNode):
                raise exceptions.YearDepFormatException(
                    parent_node.file_path,
                    doublet_node.node_path_as_str,
                    ExceptionKey.YEARDEP_ENTRYNOTALIST.value,
                    module=LOG_MODULE_STR,
                )
            if not len(doublet_node) == 2:
                raise exceptions.YearDepFormatException(
                    parent_node.file_path,
                    doublet_node.node_path_as_str,
                    ExceptionKey.YEARDEP_ENTRYNOTLENGTHTWO.value,
                    module=LOG_MODULE_STR,
                )
            year: int = 0
            year_value: Value = Value(0)
            for i in range(2):
                doublet_node_i = doublet_node[i]
                assert doublet_node_i is not None
                if not isinstance(doublet_node_i, YamlValueNode):
                    raise exceptions.YearDepFormatException(
                        parent_node.file_path,
                        doublet_node_i.node_path_as_str,
                        ExceptionKey.YEARDEP_ENTRYPARTISNOTAVALUE.value,
                        module=LOG_MODULE_STR,
                    )
                if i == 0:
                    year = parse_int_from_value_node(doublet_node_i)
                if i == 1:
                    year_value_str = parse_str_from_value_node(doublet_node_i)
                    year_value = Value.from_str(year_value_str)
                    if first_unit is not None:
                        if not year_value.unit.same_type_as(first_unit):
                            raise exceptions.InvalidValueException(
                                parent_node.file_path,
                                doublet_node.node_path_as_str,
                                invalidity_reason=(
                                    "Unit mismatch: First unit in dict "
                                    f"was {first_unit}, this is "
                                    f"{year_value.unit}."
                                ),
                                module=LOG_MODULE_STR,
                            )
                    if first_unit is None:
                        first_unit = year_value.unit
                        if (
                            expected_unit is not None
                            and not year_value.unit.same_type_as(expected_unit)
                        ):
                            raise exceptions.InvalidValueException(
                                parent_node.file_path,
                                doublet_node.node_path_as_str,
                                invalidity_reason=(
                                    "Unit mismatch: expected "
                                    f"{expected_unit}, got "
                                    f"{year_value.unit}."
                                ),
                                module=LOG_MODULE_STR,
                            )
            if not year > previous_year:
                raise exceptions.YearDepFormatException(
                    parent_node.file_path,
                    doublet_node.node_path_as_str,
                    ExceptionKey.YEARDEP_YEARSNOTINCREASING.value,
                    module=LOG_MODULE_STR,
                )
            previous_year = year
            year_to_value_dict[year] = year_value
        stage_to_value_dict = _transform_yeartovalue_to_stagetovalue(
            year_to_value_dict, stages
        )
        return stage_to_value_dict
    # Wrong yaml node kind
    expected_type = f"{YamlNodeKind.VALUE} or {YamlNodeKind.DICT}"
    actual_type = f"{type(node)}"
    raise exceptions.InvalidNodeTypeException(
        parent_node.file_path,
        node.node_path_as_str,
        expected_type,
        actual_type,
        module=LOG_MODULE_STR,
    )


def parse_mandatory_yeardep_value_from_dict_node(
    parent_node: YamlNode,
    value_key: str,
    stages: Stages,
    expected_unit: Optional[Unit] = None,
) -> Dict[StageId, Value]:
    check_node_type(parent_node, YamlNodeKind.DICT)
    node = get_mandatory_subnode_from_dict_node(parent_node, value_key)
    if isinstance(node, YamlValueNode):
        value = parse_mandatory_value_from_dict_node(
            parent_node, value_key, expected_unit=expected_unit
        )
        return {s: value for s in stages.ids}
    if isinstance(node, YamlListNode):
        year_to_value_dict: Dict[int, Value] = {}
        previous_year = -float("inf")
        first_unit: Optional[Unit] = None
        for doublet_node in node:
            if not isinstance(doublet_node, YamlListNode):
                raise exceptions.YearDepFormatException(
                    parent_node.file_path,
                    doublet_node.node_path_as_str,
                    ExceptionKey.YEARDEP_ENTRYNOTALIST.value,
                    module=LOG_MODULE_STR,
                )
            if not len(doublet_node) == 2:
                raise exceptions.YearDepFormatException(
                    parent_node.file_path,
                    doublet_node.node_path_as_str,
                    ExceptionKey.YEARDEP_ENTRYNOTLENGTHTWO.value,
                    module=LOG_MODULE_STR,
                )
            year: int = 0
            year_value: Value = Value(0)
            for i in range(2):
                doublet_node_i = doublet_node[i]
                assert doublet_node_i is not None
                if not isinstance(doublet_node_i, YamlValueNode):
                    raise exceptions.YearDepFormatException(
                        parent_node.file_path,
                        doublet_node_i.node_path_as_str,
                        ExceptionKey.YEARDEP_ENTRYPARTISNOTAVALUE.value,
                        module=LOG_MODULE_STR,
                    )
                if i == 0:
                    year = parse_int_from_value_node(doublet_node_i)
                if i == 1:
                    year_value_str = parse_str_from_value_node(doublet_node_i)
                    year_value = Value.from_str(year_value_str)
                    if first_unit is not None:
                        if not year_value.unit.same_type_as(first_unit):
                            raise exceptions.InvalidValueException(
                                parent_node.file_path,
                                doublet_node.node_path_as_str,
                                invalidity_reason=(
                                    "Unit mismatch: First unit in dict "
                                    f"was {first_unit}, this is "
                                    f"{year_value.unit}."
                                ),
                                module=LOG_MODULE_STR,
                            )
                    if first_unit is None:
                        first_unit = year_value.unit
                        if (
                            expected_unit is not None
                            and not year_value.unit.same_type_as(expected_unit)
                        ):
                            raise exceptions.InvalidValueException(
                                parent_node.file_path,
                                doublet_node.node_path_as_str,
                                invalidity_reason=(
                                    "Unit mismatch: expected "
                                    f"{expected_unit}, got "
                                    f"{year_value.unit}."
                                ),
                                module=LOG_MODULE_STR,
                            )
            if not year > previous_year:
                raise exceptions.YearDepFormatException(
                    parent_node.file_path,
                    doublet_node.node_path_as_str,
                    ExceptionKey.YEARDEP_YEARSNOTINCREASING.value,
                    module=LOG_MODULE_STR,
                )
            previous_year = year
            year_to_value_dict[year] = year_value
        stage_to_value_dict = _transform_yeartovalue_to_stagetovalue(
            year_to_value_dict, stages
        )
        return stage_to_value_dict
    # Wrong yaml node kind
    expected_type = f"{YamlNodeKind.VALUE} or {YamlNodeKind.DICT}"
    actual_type = f"{type(node)}"
    raise exceptions.InvalidNodeTypeException(
        parent_node.file_path,
        node.node_path_as_str,
        expected_type,
        actual_type,
        module=LOG_MODULE_STR,
    )


def _transform_yeartofloat_to_stagetofloat(
    year_to_value_dict: Dict[int, float], stages: Stages
) -> Dict[StageId, float]:
    stage_ids = stages.ids_in_order
    dict_years = list(year_to_value_dict.keys())
    cur_dict_year_pos = 0
    cur_dict_year = dict_years[cur_dict_year_pos]
    stage_to_value_dict: Dict[StageId, float] = {}
    for s in stage_ids:
        stage_year = stages.get_start_year(s)
        if stage_year < cur_dict_year:
            stage_to_value_dict[s] = year_to_value_dict[cur_dict_year]
            continue
        while True:
            if cur_dict_year_pos == len(dict_years) - 1:
                break
            if stage_year < dict_years[cur_dict_year_pos + 1]:
                break
            cur_dict_year_pos += 1
            cur_dict_year = dict_years[cur_dict_year_pos]
        stage_to_value_dict[s] = year_to_value_dict[cur_dict_year]
    return stage_to_value_dict


def _transform_yeartovalue_to_stagetovalue(
    year_to_value_dict: Dict[int, Value], stages: Stages
) -> Dict[StageId, Value]:
    stage_ids = stages.ids_in_order
    dict_years = list(year_to_value_dict.keys())
    cur_dict_year_pos = 0
    cur_dict_year = dict_years[cur_dict_year_pos]
    stage_to_value_dict: Dict[StageId, Value] = {}
    for s in stage_ids:
        stage_year = stages.get_start_year(s)
        if stage_year < cur_dict_year:
            stage_to_value_dict[s] = year_to_value_dict[cur_dict_year]
            continue
        while True:
            if cur_dict_year_pos == len(dict_years) - 1:
                break
            if stage_year < dict_years[cur_dict_year_pos + 1]:
                break
            cur_dict_year_pos += 1
            cur_dict_year = dict_years[cur_dict_year_pos]
        stage_to_value_dict[s] = year_to_value_dict[cur_dict_year]
    return stage_to_value_dict


def parse_bool_from_value_node(value_node: YamlNode) -> bool:
    check_node_type(value_node, YamlNodeKind.VALUE)
    value = value_node.value
    try:
        value_as_bool = bool(value)
    except ValueError as exc:
        raise exceptions.InvalidParamTypeException(
            value_node.file_path,
            value_node.node_path_as_str,
            bool,
            type(value),
            module=LOG_MODULE_STR,
        ) from exc
    return value_as_bool


def parse_int_from_value_node(value_node: YamlNode) -> int:
    check_node_type(value_node, YamlNodeKind.VALUE)
    value = value_node.value
    try:
        value_as_int = int(value)
    except ValueError as exc:
        raise exceptions.InvalidParamTypeException(
            value_node.file_path,
            value_node.node_path_as_str,
            int,
            type(value),
            module=LOG_MODULE_STR,
        ) from exc
    return value_as_int


def parse_float_from_value_node(value_node: YamlNode) -> float:
    check_node_type(value_node, YamlNodeKind.VALUE)
    value = value_node.value
    if isinstance(value, Value):
        return value.to_float()
    try:
        value_as_float = float(value)
    except ValueError as exc:
        raise exceptions.InvalidParamTypeException(
            value_node.file_path,
            value_node.node_path_as_str,
            float,
            type(value),
            module=LOG_MODULE_STR,
        ) from exc
    return value_as_float


def parse_str_from_value_node(value_node: YamlNode) -> str:
    check_node_type(value_node, YamlNodeKind.VALUE)
    value = value_node.value
    try:
        value_as_str = str(value)
    except ValueError as exc:
        raise exceptions.InvalidParamTypeException(
            value_node.file_path,
            value_node.node_path_as_str,
            str,
            type(value),
            module=LOG_MODULE_STR,
        ) from exc
    return value_as_str
