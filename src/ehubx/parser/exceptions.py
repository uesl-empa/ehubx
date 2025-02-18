from typing import List
from ehubx.core import logging


class ParsingException(Exception):
    def __init__(self, file_path: str, msg: str, module: str = ""):
        msg = f"Parsing exception in file {file_path}: {msg}"
        logging.log_error(msg, module=module)
        super().__init__(msg)
        self._file_path = file_path


class DuplicateIdInYamlBlockListException(ParsingException):
    def __init__(self, file_path: str, node_path_str: str,
                 dupe_id: str, id_positions: List[int], module: str = ""):
        msg = f"Encountered duplicate id {dupe_id} at positions " + \
            f"{id_positions} in yaml block list {node_path_str}."
        self._node_path_str = node_path_str
        self._dupe_id = dupe_id
        self._id_positions = id_positions
        super().__init__(file_path, msg, module=module)


class MissingFileException(ParsingException):
    def __init__(self, file_path: str, file_type: str, module: str = ""):
        msg = f"{file_type} file does not exist"
        super().__init__(file_path, msg, module=module)
        self._file_type = file_type


class MissingNodeException(ParsingException):
    def __init__(self, file_path: str, node_path_str: str,
                 module: str = "") -> None:
        msg = f"Missing mandatory node '{node_path_str}' detected"
        super().__init__(file_path, msg, module=module)
        self._node_path_str = node_path_str


class MissingRootNodeException(MissingNodeException):
    def __init__(self, file_path: str, module: str = "") -> None:
        node_path_str: str = "[root]"
        super().__init__(file_path, node_path_str, module=module)


class MissingValueException(ParsingException):
    def __init__(self, file_path: str, node_path_str: str,
                 module: str = "") -> None:
        msg = "Missing mandatory value detected at node " + \
            f"'{node_path_str}'"
        super().__init__(file_path, msg, module=module)
        self._node_path_str: str = node_path_str


class InvalidValueException(ParsingException):
    def __init__(self, file_path: str, node_path_str: str,
                 invalidity_reason: str, module: str = "") -> None:
        msg = f"Invalid value detected at node {node_path_str}. " + \
            f"Reason: {invalidity_reason}"
        super().__init__(file_path, msg, module=module)
        self._node_path_str: str = node_path_str


class InvalidParamTypeException(ParsingException):
    def __init__(self, file_path: str, node_path_str: str,
                 expected_type: type, actual_type: type,
                 module: str = "") -> None:
        msg = f"Invalid type of parameter '{node_path_str}' " + \
            f"detected. Expected {expected_type} but got {actual_type}"
        super().__init__(file_path, msg, module=module)
        self._node_path_str: str = node_path_str
        self._expected_type: type = expected_type
        self._actual_type: type = actual_type


class InvalidNodeTypeException(ParsingException):
    def __init__(self, file_path: str, node_path_str: str,
                 expected_type: str, actual_type: str,
                 module: str = "") -> None:
        msg = f"Invalid type of node '{node_path_str}' " + \
            f"detected. Expected {expected_type} but got {actual_type}"
        super().__init__(file_path, msg, module=module)
        self._node_path_str: str = node_path_str
        self._expected_type: str = expected_type
        self._actual_type: str = actual_type


class EmptyListNodeException(ParsingException):
    def __init__(self, file_path: str, node_path_str: str,
                 module: str = "") -> None:
        msg = f"Empty list detected at node path {node_path_str}"
        super().__init__(file_path, msg, module=module)
        self._node_path_str: str = node_path_str


class YearDepFormatException(ParsingException):
    def __init__(self, file_path: str, node_path_str: str,
                 invalidity_reason: str, module: str = ""):
        msg = "Invalid format of year-dependent parameter node " + \
            f"{node_path_str}. Reason: {invalidity_reason}"
        super().__init__(file_path, msg, module=module)
        self._node_path_str: str = node_path_str
