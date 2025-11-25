"""
Time data module
"""

from enum import Enum
from typing import Dict, List, Set, Tuple

from ehubx.core import common, logging
from ehubx.data import exceptions
from ehubx.data.index import Index, IndexKind
from ehubx.data.stage_data import StageId, Stages


# Time index
class TimeId(Index):
    """
    Time index
    """

    @property
    def key_as_int(self) -> int:
        """
        Integer value of the time index's key
        """
        return self._key_int

    def __init__(self, key_int: int):
        self._key_int = key_int
        super().__init__(IndexKind.TIME, str(key_int))


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the time data module
    """

    ID_ADD = "adding to 'ids' of Times"
    HORIZONID_ADD = "adding to 'ids' of Times"
    WEIGHT_SET = "setting 'weight' of Times"
    WEIGHT_GET = "getting 'weight' from Times"
    WEIGHT_VAL = "validating 'weight' of Times"
    CLUSTERTS_SET = "setting 'cluster_ts' of Times"
    CLUSTERTS_GET = "getting 'cluster_ts' from Times"
    CLUSTERTS_VAL = "validating 'cluster_ts' of Times"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/times"
"""String identifying the time data module for logging purposes"""

DEF_WEIGHT: float = 1
"""Default value for parameter 'weight' in the time data module"""


class Times:
    """
    Class for time data which manages time ids and time-associated data.
    Contains getters and setters as well as validation methods to control data
    integrity
    """

    # ------------- #
    # Property: ids #
    # ------------- #
    @property
    def ids(self) -> Set[TimeId]:
        """
        Set of time ids. These may differ from the horizon time ids if
        clustering is performed.
        """
        return self._ids

    @property
    def ids_in_order(self) -> List[TimeId]:
        """
        List of known time ids in order of their integer key
        """
        ids = list(self.ids)
        ids.sort(key=lambda t: t.key_as_int)
        return ids

    def add_id(self, t: TimeId) -> None:
        """
        Add a time id.

        :param t: Id to be added
        :type t: TimeId
        """
        if t in self._ids:
            raise exceptions.DuplicateIdException(
                ExceptionKey.ID_ADD.value, t, module=LOG_MODULE_STR
            )
        self._ids.add(t)
        self._ids_horizon.add(t)

    def clear_ids(self) -> None:
        """
        Remove all time ids from the data class
        """
        self._ids.clear()

    @property
    def num_ts(self) -> int:
        """
        Number of time steps in the data class. This may differ from the
        number of horizon time ids if clustering is performed.
        """
        return len(self._ids)

    # --------------------- #
    # Property: ids_horizon #
    # --------------------- #
    @property
    def ids_horizon(self) -> Set[TimeId]:
        """
        Set of horizon time ids. These are the original time ids before
        potential clustering is performed.
        """
        return self._ids_horizon

    @property
    def ids_horizon_in_order(self) -> List[TimeId]:
        """
        List of known horizon time ids in order of their integer key
        """
        ids = list(self.ids_horizon)
        ids.sort(key=lambda t: t.key_as_int)
        return ids

    def add_horizon_id(self, t: TimeId) -> None:
        """
        Add a horizon time id.

        :param t: Horizon time id to be added
        :type t: TimeId
        """
        self._ids_horizon.add(t)

    def clear_horizon_ids(self) -> None:
        """
        Clear all horizon time ids from the data class
        """
        self._ids_horizon.clear()
        self._ids.clear()

    @property
    def num_horizon_ts(self) -> int:
        """
        Number of horizon time ids in the data class. This is the original
        number of time ids before any potential clustering is performed

        :return: _description_
        :rtype: int
        """
        return len(self.ids_horizon)

    # ---------------------- #
    # Property: is_clustered #
    # ---------------------- #
    @property
    def is_clustered(self) -> bool:
        """
        Whether the time data has been clustered
        """
        return self.num_horizon_ts > self.num_ts

    # -------------------------- #
    # Property: first_horizon_id #
    # -------------------------- #
    @property
    def first_horizon_id(self) -> TimeId:
        ids_horizon = sorted(list(self.ids_horizon), key=lambda t: t.key_as_int)
        return ids_horizon[0]

    # ------------------------- #
    # Property: last_horizon_id #
    # ------------------------- #
    @property
    def last_horizon_id(self) -> TimeId:
        ids_horizon = sorted(list(self.ids_horizon), key=lambda t: t.key_as_int)
        return ids_horizon[-1]

    # ---------------- #
    # Property: weight #
    # ---------------- #
    def get_weight(self, s: StageId, t: TimeId) -> float:
        """
        Get the clustering weight of a time id. This coincides with the number
        of horizon time ids that are part of the input time id's cluster.

        :param s: Stage id
        :type s: StageId
        :param t: Time id
        :type t: TimeId
        :return: Clustering weight of the time id
        :rtype: float
        """
        self._check_id(t, ExceptionKey.WEIGHT_GET)
        return self._weight.get((s, t), DEF_WEIGHT)

    def set_weight(self, s: StageId, t: TimeId, weight: float) -> None:
        """
        Set the clustering weight of a time id. This coincides with the number
        of horizon time ids that are part of the input time id's cluster.

        :param s: Stage id
        :type s: StageId
        :param t: Time id
        :type t: TimeId
        :param weight: Clustering weight of the time id
        :type weight: float
        """
        self._check_id(t, ExceptionKey.WEIGHT_SET)
        self._weight[s, t] = weight

    # -------------------- #
    # Property: cluster_ts #
    # -------------------- #
    def get_cluster_ts(self, s: StageId, t_hor: TimeId) -> TimeId:
        """
        Get the time id of a horizon time id's cluster.

        :param s: Stage id
        :type s: StageId
        :param t_hor: Horizon time id
        :type t_hor: TimeId
        :return: Cluster time id
        :rtype: TimeId
        """
        self._check_horizon_id(t_hor, ExceptionKey.CLUSTERTS_GET)
        if not self.is_clustered:
            return t_hor
        if (s, t_hor) not in self._cluster_ts:
            msg = (
                "Tried to obtain a clustering timestep which does not "
                f"exist for the horizon time step {t_hor}"
            )
            raise exceptions.DataException(
                ExceptionKey.CLUSTERTS_GET.value, [t_hor], msg, module=LOG_MODULE_STR
            )
        return self._cluster_ts[s, t_hor]

    def set_cluster_ts(self, s: StageId, t: TimeId, t_hor: TimeId) -> None:
        """
        Set the time id of a horizon time id's cluster.

        :param s: Stage id
        :type s: StageId
        :param t: Cluster time id
        :type t: TimeId
        :param t_hor: Horizon time id
        :type t_hor: TimeId
        """
        self._check_id(t, ExceptionKey.CLUSTERTS_SET)
        self._check_horizon_id(t_hor, ExceptionKey.CLUSTERTS_SET)
        self._cluster_ts[s, t_hor] = t

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._ids: Set[TimeId] = set()
        self._ids_horizon: Set[TimeId] = set()
        self._weight: Dict[Tuple[StageId, TimeId], float] = {}
        self._cluster_ts: Dict[Tuple[StageId, TimeId], TimeId] = {}

    # --------- #
    # Validation #
    # ---------- #
    def validate(self, stages: Stages) -> None:
        """
        Validate all time data in this object. Apart from sense-checking
        parameter in terms of quantity, this includes checking whether
        the ids from other data classes used here are known there as well.

        :param stages: Stages data class
        :type stages: Stages
        """
        self._validate_weight(stages)
        self._validate_cluster_ts(stages)

    def _validate_weight(self, stages: Stages) -> None:
        for (s, t), weight in self._weight.items():
            if s not in stages.ids:
                msg = f"Unknown stage {s} in weight[{s}, {t}]"
                raise exceptions.DataException(
                    ExceptionKey.WEIGHT_VAL.value, [s, t], msg, module=LOG_MODULE_STR
                )
            if weight < 0:
                msg = f"Negative weight[{s}, {t}] = {weight}"
                raise exceptions.DataException(
                    ExceptionKey.WEIGHT_VAL.value, [s, t], msg, module=LOG_MODULE_STR
                )
            if weight < common.EPS_ZEROCHECK:
                msg = f"Quasi-zero weight[{s}, {t}] = {weight}"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_cluster_ts(self, stages: Stages) -> None:
        for s, t in self._cluster_ts:
            if s not in stages.ids:
                msg = f"Unknown stage {s} in cluster_ts[{s}, {t}]"
                raise exceptions.DataException(
                    ExceptionKey.CLUSTERTS_VAL.value, [s, t], msg, module=LOG_MODULE_STR
                )

    # ----------- #
    # Id checkers #
    # ----------- #
    def _check_id(self, t: TimeId, exc_key: ExceptionKey) -> None:
        if t not in self._ids:
            raise exceptions.UnknownIdException(exc_key.value, t, module=LOG_MODULE_STR)

    def _check_horizon_id(self, t: TimeId, where: ExceptionKey) -> None:
        if t not in self._ids_horizon:
            raise exceptions.UnknownIdException(where.value, t, module=LOG_MODULE_STR)
