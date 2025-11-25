"""
Index module
"""

from enum import Enum
from typing import Any


class IndexKind(Enum):
    STAGE = "stage"
    HUB = "hub"
    NETLINK = "net_link"
    TECH = "tech"
    NETTECH = "net tech"
    EC = "ec"
    LOADSHIFT = "load shift"
    TIME = "time"
    PARETOPOINT = "pareto_point"
    ATESSCHEDULE = "ates_schedule"


# Main index class
class Index:
    """
    Index class. Indices are used to identify model elements such as stages,
    hubs, technologies and many more. An index object knows which kind of index
    it is and holds a key string which marks its value. Two index objects are
    considered equal if they are of the same kind and hold the same key.
    """

    @property
    def kind(self) -> IndexKind:
        """Index kind (e.g.; stage, hub, ...)"""
        return self._kind

    @property
    def kind_as_str(self) -> str:
        """The index kind, as a string"""
        return self._kind.value

    @property
    def key(self) -> str:
        """Index key (unique identifier)"""
        return self._key

    def __init__(self, index_kind: IndexKind, key: str) -> None:
        self._kind = index_kind
        self._key = key

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Index):
            return (self.kind == other.kind) and (self.key == other.key)
        return False

    def __hash__(self) -> int:
        return hash((self.kind, self.key))

    def __repr__(self) -> str:
        return self.key
