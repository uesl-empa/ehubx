"""
Data exceptions module
"""

from typing import List

from ehubx.core.exceptions import EhubXException
from ehubx.data.index import Index


class DataException(EhubXException):
    """
    General exception that inherits from the main ehubX exception and can be
    thrown from the data module. In addition to its EhubXException properties,
    it contains a key string which can be used to identify its origin, and a
    list of indices for which the exception was thrown.
    """

    def __init__(self, key: str, indices: List[Index], msg: str, module: str = ""):
        self.indices = indices
        self.key = key
        super().__init__(msg, module=module)


class DuplicateIdException(DataException):
    """
    Data exception that arises when a duplicate index occurs for a type of
    model element (e.g.; stages). This class inherits from DataException and
    may contain only a single index (which is duplicate)
    """

    @property
    def index(self) -> Index:
        return self.indices[0]

    def __init__(self, key: str, index: Index, module: str = "") -> None:
        message = (
            f"Duplicate {index.kind_as_str} index {index.key} "
            + f"detected while {key}"
        )
        super().__init__(key, [index], message, module=module)


class UnknownIdException(DataException):
    """
    Data exception that arises when trying to set or get a parameter in a data
    class for an unknown index, i.e.; an index that is not known to the class
    object even though that class manages all known indices of that type. This
    class inherits from DataException and may only contain a single index
    (which is unknown)
    """

    @property
    def index(self) -> Index:
        return self.indices[0]

    def __init__(self, key: str, index: Index, module: str = ""):
        message = (
            f"Unkown {index.kind_as_str} id {index.key} " + f"detected while {key}"
        )
        super().__init__(key, [index], message, module=module)


class MissingIdsException(DataException):
    """
    Data exception that arises when trying to set or get a parameter in a data
    class for an unknown tuple of indices, i.e.; an index tuple that is not
    known to the class object even though that class manages all known tuples
    of that type. This class inherits from DataException
    """

    def __init__(self, key: str, indices: List[Index], module: str = ""):
        kinds_as_str = "(" + ",".join([index.kind_as_str for index in indices]) + ")"
        keys_as_str = "(" + ",".join([index.key for index in indices]) + ")"
        message = (
            f"Missing {kinds_as_str} index tuple {keys_as_str} "
            + f"detected while {key}"
        )
        super().__init__(key, indices, message, module=module)


class MissingValueException(DataException):
    """
    Data exception that arises when trying to get a mandatory parameter from a
    data object which has not been defined. This class inherits from
    DataException but may not contain any indices
    """

    def __init__(self, key: str, module: str = ""):
        message = f"Missing value detected while {key}"
        super().__init__(key, [], message, module=module)


class MissingIdException(DataException):
    """
    Data exception that arises when trying to get a mandatory parameter from a
    data object which has not been defined for a certain index. This class
    inherits from DataException but may contain only a single index
    """

    @property
    def index(self) -> Index:
        return self.indices[0]

    def __init__(self, key: str, index: Index, module: str = ""):
        message = (
            f"Missing {index.kind_as_str} index {index.key} " + f"detected while {key}"
        )
        super().__init__(key, [index], message, module=module)
