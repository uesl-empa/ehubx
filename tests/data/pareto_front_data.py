"""
Pareto front data module
"""

from enum import Enum
from typing import Dict, List, Tuple

from ehubx.data import exceptions
from ehubx.data.index import Index, IndexKind


class ParetoId(Index):
    """
    Pareto point index
    """

    def __init__(self, pos: int):
        super().__init__(IndexKind.PARETOPOINT, str(pos))
        self.pos: int = pos


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the Pareto front data module
    """

    POINT_GET = "getting 'point' from ParetoFront"
    POINT_SET = "setting 'point' of ParetoFront"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/pareto"
"""String identifying the Pareto front data module for logging purposes"""


class ParetoFront:
    """
    Class for Pareto front data. Contains getters and setters for Pareto
    points
    """

    # Constructor
    def __init__(self) -> None:
        self.obj_key_1: str = ""
        self.obj_key_2: str = ""
        self._points: Dict[ParetoId, Tuple[float, float]] = {}

    # ------------- #
    # Property: ids #
    # ------------- #
    @property
    def ids(self) -> List[ParetoId]:
        """
        Set of Pareto point indices in the Pareto front
        """
        ids = list(self._points.keys())
        ids.sort(key=lambda p: p.pos)
        return ids

    # ---------------- #
    # Property: points #
    # ---------------- #
    def get_point(self, pareto_id: ParetoId) -> Tuple[float, float]:
        """
        Get the two-dimensional objective coordinates of a point in the Pareto
        front

        :param pareto_id: Pareto point
        :type pareto_id: ParetoId
        :return: Objective coordinates
        :rtype: Tuple[float, float]
        """
        if pareto_id not in self.ids:
            raise exceptions.MissingIdException(
                ExceptionKey.POINT_GET.value, pareto_id, module=LOG_MODULE_STR
            )
        return self._points[pareto_id]

    def set_point(
        self, pareto_id: ParetoId, obj_val_1: float, obj_val_2: float
    ) -> None:
        """
        Set the two-dimensional objective coordinates of a point in the Pareto
        front

        :param pareto_id: Pareto point
        :type pareto_id: ParetoId
        :param obj_val_1: Coordinate in first objective dimension
        :type obj_val_1: float
        :param obj_val_2: Coordinate in second objective dimension
        :type obj_val_2: float
        """
        self._points[pareto_id] = (obj_val_1, obj_val_2)
