"""
Hub data module
"""

from enum import Enum
from typing import List, Set

from ehubx.data import exceptions
from ehubx.data.index import Index, IndexKind


class HubId(Index):
    """
    Hub index
    """

    def __init__(self, key: str):
        super().__init__(IndexKind.HUB, key)


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the hub data module
    """

    ID_ADD = "adding to 'ids' of EnergyCarriers"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/hub"
"""String identifying the hub data module for logging purposes"""


class Hubs:
    """
    Class for hub data. It only manages hub ids and does not hold any
    additional data.
    """

    # ------------- #
    # Property: ids #
    # ------------- #
    @property
    def ids(self) -> Set[HubId]:
        """
        Set of known hub ids
        """
        return self._ids

    @property
    def ids_in_order(self) -> List[HubId]:
        """
        List of known hub ids in alphabetical order
        """
        ids = list(self.ids)
        ids.sort(key=lambda h: h.key)
        return ids

    def add_id(self, h: HubId) -> None:
        """
        Add a new hub id

        :param h: Id to be added
        :type h: HubId
        """
        if h in self._ids:
            raise exceptions.DuplicateIdException(
                ExceptionKey.ID_ADD.value, h, module=LOG_MODULE_STR
            )
        self._ids.add(h)

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._ids: Set[HubId] = set()

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self) -> None:
        """
        Validate all hub data in this object.
        """

    # ---------- #
    # Id checker #
    # ---------- #
    def _check_id(self, h: HubId, where: ExceptionKey) -> None:
        if h not in self._ids:
            raise exceptions.UnknownIdException(where.value, h, module=LOG_MODULE_STR)
