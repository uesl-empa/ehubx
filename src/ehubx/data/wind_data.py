"""
Wind data module
"""

from enum import Enum
from typing import Dict, List, Set, Tuple

from ehubx.core import logging
from ehubx.core.common import EPS_ZEROCHECK, TimeSeriesKind
from ehubx.data import exceptions
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.index import Index, IndexKind
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.time_data import TimeId, Times
from ehubx.data.time_series import TimeSeries


class WindparkId(Index):
    """
    Windpark index
    """

    def __init__(self, key: str) -> None:
        super().__init__(IndexKind.WINDPARK, key)


# Exception keys
class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the wind data module
    """

    WINDPARKID_ADD = "adding to 'windpark_ids' of WindData"
    VELOCITY_SET = "setting 'velocity' of WindData"
    VELOCITY_VAL = "validating 'velocity' of WindData"
    WINDPARKAREA_SET = "setting 'windpark_area' of WindData"
    WINDPARKAREA_GET = "getting 'windpark_area' from WindData"
    WINDPARKAREA_VAL = "setting 'windpark_area' of WindData"
    WINDPARKECS_ADD = "adding to 'windpark_es' of WindData"
    WINDPARKECS_GET = "getting 'windpark_ecs' from WindData"
    WINDPARKECS_VAL = "adding to 'windpark_es' of WindData"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/wind"
"""String identifying the wind data module for logging purposes"""

DEF_VELOCITY: float = 0
"""Default value for parameter 'velocity' in the wind data module"""

DEF_WINDPARKAREA: float = 0
"""Default value for parameter 'windpark_area' in the wind data module"""


class WindData:
    """
    Class for wind data. Manages windpark ids, contains
    getters and setters for wind technology parameters and validation methods
    to control data integrity
    """

    # ---------------------- #
    # Property: windpark_ids #
    # ---------------------- #
    @property
    def windpark_ids(self) -> Set[WindparkId]:
        """
        Set of known windpark ids
        """
        return self._windpark_ids

    def add_windpark_id(self, w: WindparkId) -> None:
        """
        Add a new windpark id

        :param w: Id to be added
        :type w: WindparkId
        """
        if w in self._windpark_ids:
            raise exceptions.DuplicateIdException(
                ExceptionKey.WINDPARKID_ADD.value, w, module=LOG_MODULE_STR
            )
        self._windpark_ids.add(w)
        self._windpark_ecs[w] = set()

    # ---------------------- #
    # Property: windpark_ecs #
    # ---------------------- #
    def get_windpark_ecs(self, wp: WindparkId) -> Set[EcId]:
        """
        Get all ecs that are included in a windpark

        :param wp: Windpark id
        :type wp: WindparkId
        :return: Set of all windpark ecs
        :rtype: Set[EcId]
        """
        self._check_id(wp, ExceptionKey.WINDPARKECS_GET)
        return self._windpark_ecs[wp]

    def add_windpark_ec(self, wp: WindparkId, e: EcId) -> None:
        """
        Add an ec to a windpark

        :param wp: Windpark id
        :type wp: WindparkId
        :param e: ec id
        :type e: EcId
        """
        self._check_id(wp, ExceptionKey.WINDPARKECS_ADD)
        self._windpark_ecs[wp].add(e)

    # ------------- #
    # Property: ecs #
    # ------------- #
    @property
    def ecs(self) -> Set[EcId]:
        """
        All ecs that belong to a windpark

        :return: Set of ecs that belong to a windpark
        :rtype: Set[EcId]
        """
        return set(e for wp in self.windpark_ids for e in self._windpark_ecs[wp])

    # ----------------------- #
    # Property: windpark_area #
    # ----------------------- #
    def get_windpark_area(self, s: StageId, h: HubId, wp: WindparkId) -> float:
        """
        Returns the amount of available area in a windpark and hub. This value
        may change over time so it is stage-dependent

        :param s: Stage id
        :type s: StageId
        :param h: Hub id
        :type h: HubId
        :param wp: Windpark id
        :type wp: WindparkId
        :return: Available area [m^2]
        :rtype: float
        """
        self._check_id(wp, ExceptionKey.WINDPARKAREA_GET)
        return self._windpark_area.get((s, h, wp), DEF_WINDPARKAREA)

    def set_windpark_area(
        self, s: StageId, h: HubId, wp: WindparkId, windpark_area: float
    ) -> None:
        """
        Set the amount of available area in a windpark and hub. This value
        may change over time so it is stage-dependent

        :param s: Stage id
        :type s: StageId
        :param h: Hub id
        :type h: HubId
        :param wp: Windpark id
        :type wp: WindparkId
        :param windpark_area: Available area [m^2]
        :type windpark_area: float
        """
        self._check_id(wp, ExceptionKey.WINDPARKAREA_SET)
        self._windpark_area[s, h, wp] = windpark_area

    # ------------------ #
    # Property: velocity #
    # ------------------ #
    def get_velocity(self, s: StageId, e: EcId) -> TimeSeries:
        """
        Get the wind velocity profile for a wind ec

        :param s: Stage id
        :type s: StageId
        :param e: Wind ec
        :type e: EcId
        :return: Wind velocity profile
        :rtype: TimeSeries
        """
        if (s, e) not in self._velocity:
            series = TimeSeries()
            series.def_value = DEF_VELOCITY
            return series
        return self._velocity[s, e]

    def set_velocity(self, s: StageId, e: EcId, t: TimeId, velocity: float) -> None:
        """
        Set the wind velocity for a wind ec at a specific time

        :param s: Stage id
        :type s: StageId
        :param e: Wind ec
        :type e: EcId
        :param t: Time id
        :type t: TimeId
        :param velocity: Wind velocity
        :type velocity: float
        """
        if (s, e) not in self._velocity:
            self._velocity[s, e] = TimeSeries()
            self._velocity[s, e].def_value = DEF_VELOCITY
        self._velocity[s, e].set_value(t, velocity)

    def set_velocity_def(self, s: StageId, e: EcId, velocity_def: float) -> None:
        """
        Set the default (with respect to time) wind velocity for a wind ec

        :param s: Stage id
        :type s: StageId
        :param e: ec id
        :type e: EcId
        :param velocity_def: Default wind velocity
        :type velocity_def: float
        """
        if (s, e) not in self._velocity:
            self._velocity[s, e] = TimeSeries()
        self._velocity[s, e].def_value = velocity_def

    def clear_velocity(self) -> None:
        """
        Remove all data for the parameter 'velocity' from wind data
        """
        for s, e in self._velocity:
            self._velocity[s, e].clear()

    # ------------------------------- #
    # Secondary property: time_series #
    # ------------------------------- #
    @property
    def time_series(
        self,
    ) -> List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...], TimeSeries]]:
        """
        Time series profiles in the solar module. This is a list of tuples.
        Each list element has the following list entries: 1) ProfileKind of
        the profile. 2) Stage. 3) Tuple of string identifiers specific to the
        ProfileKind. 4) The TimeSeries of the profile

        :return: All time series of the solar module
        :rtype: List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...],
            TimeSeries]]
        """
        all_series: List[
            Tuple[TimeSeriesKind, StageId, Tuple[str, ...], TimeSeries]
        ] = []
        # velocity
        for (s, e), series in self._velocity.items():
            if series.has_values:
                all_series.append((TimeSeriesKind.WINDVELOCITY, s, (e.key,), series))
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
        Set the value for a time series in the wind data class. The time
        series should be uniquely identified by the time series kind, the
        stage  id and the remaining tuples.

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
        if kind == TimeSeriesKind.WINDVELOCITY:
            e = EcId(ids[0])
            self.set_velocity(s, e, t, value)

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._windpark_ids: Set[WindparkId] = set()
        self._windpark_ecs: Dict[WindparkId, Set[EcId]] = {}
        self._windpark_area: Dict[Tuple[StageId, HubId, WindparkId], float] = {}
        self._velocity: Dict[Tuple[StageId, EcId], TimeSeries] = {}

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self, stages: Stages, hubs: Hubs, ecs: Ecs, times: Times) -> None:
        """
        Validate all wind data in this object. Apart from sense-checking
        parameter in terms of quantity, this includes checking whether
        the ids from other data classes used here are known there as well.

        :param stages: Stages data class
        :type stages: Stages
        :param hubs: Hubs data class
        :type hubs: Hubs
        :param ecs: ec data class
        :type ecs: Ecs
        :param times: Times data class
        :type times: Times
        """
        self._validate_windpark_ecs(ecs)
        self._validate_windpark_area(stages, hubs)
        self._validate_velocity(stages, ecs, times)

    def _validate_windpark_ecs(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.WINDPARKECS_VAL.value
        for wp, windpark_ecs in self._windpark_ecs.items():
            # windpark_ecs usually not empty
            if not windpark_ecs:
                msg = f"Empty windpark_ecs[{wp}]"
                logging.log_warning(msg, module=LOG_MODULE_STR)
            for e in windpark_ecs:
                # Unknown windpark_ec
                if e not in ecs.ids:
                    msg = f"Unknown ec {e} in windpark_ecs[{wp}]"
                    raise exceptions.DataException(
                        exc_key, [wp, e], msg, module=LOG_MODULE_STR
                    )

    def _validate_windpark_area(self, stages: Stages, hubs: Hubs) -> None:
        exc_key = ExceptionKey.WINDPARKAREA_VAL.value
        for (s, h, wp), area in self._windpark_area.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in windpark_area[{s}, {h}, {wp}]"
                raise exceptions.DataException(
                    exc_key, [s, h, wp], msg, module=LOG_MODULE_STR
                )
            # Unknown hub
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in windpark_area[{s}, {h}, {wp}]"
                raise exceptions.DataException(
                    exc_key, [s, h, wp], msg, module=LOG_MODULE_STR
                )
            # area must not not be negative
            if area < 0:
                msg = f"{area} = windpark_area[{s}, {h}, {wp}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, h, wp], msg, module=LOG_MODULE_STR
                )

    def _validate_velocity(self, stages: Stages, ecs: Ecs, times: Times) -> None:
        exc_key = ExceptionKey.VELOCITY_VAL.value
        for (s, e), velocity in self._velocity.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in velocity[{s}, {e}]"
                raise exceptions.DataException(
                    exc_key, [s, e], msg, module=LOG_MODULE_STR
                )
            # Not a wind ec
            if e not in self.ecs:
                msg = f"ec {e} in velocity[{s}, {e}] is not a wind ec"
                raise exceptions.DataException(
                    exc_key, [s, e], msg, module=LOG_MODULE_STR
                )
            # Time values
            if velocity.has_values:
                # Unknown time ids
                velocity.validate(times, exc_key)
                # velocity must not be negative
                for t in times.ids:
                    if velocity.get_value(t) < 0:
                        msg = f"{velocity.get_value(t)} = velocity[{s}, {e}][{t}] < 0"
                        raise exceptions.DataException(
                            exc_key, [s, e, t], msg, module=LOG_MODULE_STR
                        )
            # Default value
            if not velocity.has_values:
                velocity_def = velocity.def_value
                assert velocity_def is not None
                # velocity must not be negative
                if velocity_def < 0:
                    msg = f"{velocity_def} = velocity_def[{s}, {e}] < 0"
                    raise exceptions.DataException(
                        exc_key, [s, e], msg, module=LOG_MODULE_STR
                    )
                # velocity usually not all-zero
                if velocity_def < EPS_ZEROCHECK:
                    msg = f"{velocity_def} = velocity[{s}, {e}] ~ 0"
                    logging.log_warning(msg, module=LOG_MODULE_STR)

    # ------------------- #
    # Windpark id checker #
    # ------------------- #
    def _check_id(self, wp: WindparkId, where: ExceptionKey) -> None:
        if wp not in self._windpark_ids:
            raise exceptions.UnknownIdException(where.value, wp, module=LOG_MODULE_STR)
