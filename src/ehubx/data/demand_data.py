"""
Demand data module
"""

from enum import Enum
from typing import Dict, List, Set, Tuple

from ehubx.core import logging
from ehubx.core.common import TimeSeriesKind
from ehubx.data import exceptions
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.time_data import TimeId, Times
from ehubx.data.time_series import TimeSeries


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the demand data module
    """

    TUPLES_ADD = "adding to 'tuples' of Demands"
    TUPLES_REMOVE = "removing from 'tuples' of Demands"
    TUPLES_VAL = "validating 'tuples' of Demands"
    DEMAND_SET = "setting 'demand' of Demands"
    DEMAND_GET = "getting 'demand' from Demands"
    DEMAND_VAL = "validating 'demand' of Demands"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/demand"
"""String identifying the demand data module for logging purposes"""

DEF_DEMAND: float = 0
"""Default value for parameter 'demand' in the demand data module"""


class Demands:
    """
    Class to hold demand data. Manages demand tuples, contains getters and
    setters for demand parameters and validation methods to control data
    integrity
    """

    # ---------------- #
    # Property: tuples #
    # ---------------- #
    @property
    def tuples(self) -> Set[Tuple[StageId, HubId, EcId]]:
        """
        Set of known demand (stgae, hub, ec) tuples
        """
        return self._tuples

    def add_tuple(self, s: StageId, h: HubId, e: EcId) -> None:
        """
        Add a new demand (stage, hub, ec) tuple

        :param s: Stage index of the tuple to be added
        :type s: StageId
        :param h: Hub index of the tuple to be added
        :type h: HubId
        :param e: ec index of the tuple to be added
        :type e: EcId
        """
        if (s, h, e) in self._tuples:
            exc_key = ExceptionKey.TUPLES_ADD.value
            msg = f"Trying to add already existing tuple ({s}, {h}, {e})."
            raise exceptions.DataException(
                exc_key, [s, h, e], msg, module=LOG_MODULE_STR
            )
        self._tuples.add((s, h, e))
        self._demand[s, h, e] = TimeSeries()
        self._demand[s, h, e].def_value = DEF_DEMAND

    def remove_tuple(self, s: StageId, h: HubId, e: EcId) -> None:
        """
        Remove a demand (stage, hub, ec) tuple

        :param s: Stage index of the tuple to be removed
        :type s: StageId
        :param h: Hub index of the tuple to be removed
        :type h: HubId
        :param e: ec index of the tuple to be removed
        :type e: EcId
        """
        if (s, h, e) not in self._tuples:
            raise exceptions.MissingIdsException(
                ExceptionKey.TUPLES_REMOVE.value, [s, h, e], module=LOG_MODULE_STR
            )
        self._tuples.remove((s, h, e))
        if (s, h, e) in self._demand:
            self._demand.pop((s, h, e))

    # ---------------- #
    # Property: demand #
    # ---------------- #
    def get_demand(self, s: StageId, h: HubId, e: EcId) -> TimeSeries:
        """
        Get the parameter 'demand' which denotes the amount of power that is
        scheduled to be consumed by the system. This is an optional parameter
        with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: ec
        :type e: EcId
        :return: Demands [kW]
        :rtype: TimeSeries
        """
        self._check_ids(s, h, e, ExceptionKey.DEMAND_GET)
        return self._demand[s, h, e]

    def set_demand(
        self, s: StageId, h: HubId, e: EcId, t: TimeId, demand: float
    ) -> None:
        """
        At a specific time, set the parameter 'demand' which denotes the
        amount of power that is scheduled to be consumed by the system. This is
        an optional parameter with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: ec
        :type e: EcId
        :param t: Time
        :type t: TimeId
        :param demand: Demand [kW]
        :type demand: float
        """
        self._check_ids(s, h, e, ExceptionKey.DEMAND_SET)
        self._demand[s, h, e].set_value(t, demand)

    def set_demand_def(self, s: StageId, h: HubId, e: EcId, demand_def: float) -> None:
        """
        Set the default (with respect to time) value for the parameter 'demand'
        which denotes the amount of power that is scheduled to be consumed by
        the system. This is an optional parameter with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: ec
        :type e: EcId
        :param demand_def: Default demand [kW]
        :type demand_def: float
        """
        self._check_ids(s, h, e, ExceptionKey.DEMAND_SET)
        self._demand[s, h, e].def_value = demand_def

    # ------------------------------- #
    # Secondary property: time_series #
    # ------------------------------- #
    @property
    def time_series(
        self,
    ) -> List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...], TimeSeries]]:
        """
        Time series profiles in the demands module. This is a list of tuples.
        Each list element has the following list entries: 1) ProfileKind of the
        profile. 2) Stage. 3) Tuple of string identifiers specific to the
        ProfileKind. 4) The TimeSeries itself

        :return: All time series of the demand module
        :rtype: List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...],
            TimeSeries]]
        """
        all_series: List[
            Tuple[TimeSeriesKind, StageId, Tuple[str, ...], TimeSeries]
        ] = []
        for (s, h, e), series in self._demand.items():
            if series.has_values:
                all_series.append((TimeSeriesKind.DEMAND, s, (h.key, e.key), series))
        return all_series

    def set_time_series_val(
        self,
        kind: TimeSeriesKind,
        s: StageId,
        ids: Tuple[str, ...],
        t: TimeId,
        value: float,
    ) -> None:
        """
        Set the value for a time series in the demand data class. The time
        series should be uniquely identified by the time series kind, the
        stage id and the remaining tuples.

        :param kind: Kind of time series
        :type kind: TimeSeriesKind
        :param s: Stage
        :type s: StageId
        :param ids: Remaining ids, other than stage and time
        :type ids: Tuple[str, ...]
        :param t: Time id
        :type t: TimeId
        :param value: Value to set
        :type value: float
        """
        if kind == TimeSeriesKind.DEMAND:
            h = HubId(ids[0])
            e = EcId(ids[1])
            self.set_demand(s, h, e, t, value)

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._tuples: Set[Tuple[StageId, HubId, EcId]] = set()
        self._demand: Dict[Tuple[StageId, HubId, EcId], TimeSeries] = {}

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self, stages: Stages, hubs: Hubs, ecs: Ecs, times: Times) -> None:
        """
        Validate all demand data in this object. Apart from sense-checking
        parameter in terms of quantity, this includes checking whether the ids
        from other data classes used here are known there as well.

        :param stages: Stages data class
        :type stages: Stages
        :param hubs: Hubs data class
        :type hubs: Hubs
        :param ecs: ecs data class
        :type ecs: Ecs
        :param times: Times data class
        :type times: Times
        """
        self._validate_tuples(stages, hubs, ecs)
        self._validate_demand(times)

    def _validate_tuples(self, stages: Stages, hubs: Hubs, ecs: Ecs) -> None:
        exc_key = ExceptionKey.TUPLES_VAL.value
        for s, h, e in self._tuples:
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in tuple ({s}, {h}, {e})"
                raise exceptions.DataException(exc_key, [s], msg, module=LOG_MODULE_STR)
            # Unknown hub
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in tuple ({s}, {h}, {e})"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)
            # Unknown ec
            if e not in ecs.ids:
                msg = f"Unknown ec {e} in tuple ({s}, {h}, {e})"
                raise exceptions.DataException(exc_key, [e], msg, module=LOG_MODULE_STR)

    def _validate_demand(self, times: Times) -> None:
        exc_key = ExceptionKey.DEMAND_VAL.value
        for (s, h, e), demand in self._demand.items():
            # Unknown time ids
            demand.validate(times, exc_key, module=LOG_MODULE_STR)
            # Price values usually nonnegative (time values)
            if demand.has_values:
                for t in times.ids:
                    if demand.get_value(t) < 0:
                        msg = f"{demand.get_value(t)} = demand[{s}, {h}, {e}][{t}] < 0"
                        logging.log_warning(msg, module=LOG_MODULE_STR)
                        break
            # Price values usually nonnegative (default values)
            if not demand.has_values:
                demand_def = demand.def_value
                assert demand_def is not None
                if demand_def < 0:
                    msg = f"{demand_def} = demand[{s}, {h}, {e}] < 0"
                    logging.log_warning(msg, module=LOG_MODULE_STR)

    # ---------- #
    # Id checker #
    # ---------- #
    def _check_ids(self, s: StageId, h: HubId, e: EcId, where: ExceptionKey) -> None:
        if (s, h, e) not in self._tuples:
            msg = (
                f"Encountered tuple ({s}, {h}, {e}) which is not a demand "
                f"tuple. This happened while {where.value}"
            )
            raise exceptions.DataException(
                where.value, [s, h, e], msg, module=LOG_MODULE_STR
            )
