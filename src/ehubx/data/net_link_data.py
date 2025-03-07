"""
Network link data module
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


class NetLinkId(Index):
    """
    Network link index
    """

    def __init__(self, key: str) -> None:
        super().__init__(IndexKind.NETLINK, key)


class NetLinkDirection(Enum):
    """
    Link direction (forward or backward)
    """

    FORWARD = "LinkForward"
    BACKWARD = "LinkBackward"


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the network link data module
    """

    ID_ADD = "adding to 'ids' of NetworkLinks"
    ID_REMOVE = "removing from 'ids' of NetworkLinks"
    ECS_ADD = "adding to 'ecs' of NetworkLinks"
    ECS_GET = "getting 'ecs' from NetworkLinks"
    ECS_VAL = "validating 'ecs' of NetworkLinks"
    HUBSTART_SET = "setting 'hub_start' of NetworkLinks"
    HUBSTART_GET = "getting 'hub_start' from NetworkLinks"
    HUBSTART_VAL = "validating 'hub_start' of NetworkLinks"
    HUBEND_SET = "setting 'hub_end' of NetworkLinks"
    HUBEND_GET = "getting 'hub_end' from NetworkLinks"
    HUBEND_VAL = "validating 'hub_end' of NetworkLinks"
    HUBSTARTEND_SAME = "hub_start and hub_end are identical"
    LENGTH_SET = "setting 'length' of NetworkLinks"
    LENGTH_GET = "getting 'length' from NetworkLinks"
    LENGTH_VAL = "validating 'length' of NetworkLinks"
    BIDIRECTIONAL_SET = "setting 'bidirectional' of NetworkLinks"
    BIDIRECTIONAL_GET = "getting 'bidirectional' from NetworkLinks"
    CAPMIN_SET = "setting 'cap_min' of NetworkLinks"
    CAPMIN_GET = "getting 'cap_min' from NetworkLinks"
    CAPMIN_VAL = "validating 'cap_min' of NetworkLinks"
    CAPMAX_SET = "setting 'cap_max' of NetworkLinks"
    CAPMAX_GET = "getting 'cap_max' from NetworkLinks"
    CAPMAX_VAL = "validating 'cap_max' of NetworkLinks"
    CAPMINMAX_VAL = "validating 'cap_min' against 'cap_max' of NetworkLinks"
    AVAILABILITY_SET = "setting 'availability' of NetworkLinks"
    AVAILABILITY_DEFSET = "setting default 'availability' of NetworkLinks"
    AVAILABILITY_GET = "getting 'availability' from NetworkLinks"
    AVAILABILITY_VAL = "validating 'availability' of NetworkLinks"
    AVAILABILITY_BI = "bidirectional 'availability' for unidirectional link"
    SUMMIN_SET = "setting 'sum_min' of NetworkLinks"
    SUMMIN_GET = "getting 'sum_min' from NetworkLinks"
    SUMMIN_BI = "bidirectional 'sum_min' for unidirectional link"
    SUMMIN_VAL = "validating 'sum_min' of NetworkLinks"
    SUMMAX_SET = "setting 'sum_max' of NetworkLinks"
    SUMMAX_GET = "getting 'sum_max' from NetworkLinks"
    SUMMAX_BI = "bidirectional 'sum_max' for unidirectional link"
    SUMMAX_VAL = "validating 'sum_max' of NetworkLinks"
    SUMMINMAX_VAL = "validating 'sum_min' against 'sum_max' of NetworkLinks"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/link"
"""String identifying the network link module for logging purposes"""

DEF_BIDIRECTIONAL: bool = False
"""Default value for parameter 'bidirectional' in the network link data
module"""

DEF_CAPMIN: float = 0
"""Default value for parameter 'cap_min' in the network link data module"""

DEF_CAPMAX: float = float("inf")
"""Default value for parameter 'cap_max' in the network link data module"""

DEF_AVAILABILITY: float = 1
"""Default value for parameter 'availability' in the network link data
module"""

DEF_SUMMIN: float = 0
"""Default value for parameter 'sum_min' in the network link data module"""

DEF_SUMMAX: float = float("inf")
"""Default value for parameter 'sum_max' in the network link data module"""


class NetworkLinks:
    """
    Class for network link data. Manages network link ids, contains
    getters and setters for network link parameters and validation methods
    to control data integrity
    """

    # ------------- #
    # Property: ids #
    # ------------- #
    @property
    def ids(self) -> Set[NetLinkId]:
        """
        Set of known network link ids
        """
        return self._ids

    @property
    def ids_in_order(self) -> List[NetLinkId]:
        """
        List of known network link ids in alphabetical order
        """
        ids = list(self.ids)
        ids.sort(key=lambda li: li.key)
        return ids

    def add_id(self, li: NetLinkId) -> None:
        """
        Add a new network link id

        :param li: Id to be added
        :type li: NetLinkId
        """
        if li in self._ids:
            raise exceptions.DuplicateIdException(
                ExceptionKey.ID_ADD.value, li, module=LOG_MODULE_STR
            )
        self._ids.add(li)

    # ------------- #
    # Property: ecs #
    # ------------- #
    def get_ecs(self, li: NetLinkId) -> Set[EcId]:
        """
        Get all ecs that can be transported on a network link

        :param li: Network link
        :type li: NetLinkId
        :return: Set of transportable ecs
        :rtype: Set[EcId]
        """
        self._check_id(li, ExceptionKey.ECS_GET)
        return self._ecs.get(li, set())

    def add_ec(self, li: NetLinkId, e: EcId) -> None:
        """
        Add an ec to the transportable ecs of a network link

        :param li: Network link
        :type li: NetLinkId
        :param e: ec
        :type e: EcId
        """
        self._check_id(li, ExceptionKey.ECS_ADD)
        if li not in self._ecs:
            self._ecs[li] = set()
        self._ecs[li].add(e)

    # ------------------- #
    # Property: hub_start #
    # ------------------- #
    def get_hub_start(self, li: NetLinkId) -> HubId:
        """
        Get the start hub of a network link. For a unidirectional link, ecs
        can be transported from the start hub to the end hub. For bidirectional
        links, the other direction is possible as well.

        :param li: Network link
        :type li: NetLinkId
        :return: Start hub
        :rtype: HubId
        """
        self._check_id(li, ExceptionKey.HUBSTART_GET)
        if li not in self._hub_start:
            raise exceptions.MissingIdException(
                ExceptionKey.HUBSTART_GET.value, li, module=LOG_MODULE_STR
            )
        return self._hub_start[li]

    def set_hub_start(self, li: NetLinkId, h: HubId) -> None:
        """
        Set the start hub of a network link. For a unidirectional link, ecs
        can be transported from the start hub to the end hub. For bidirectional
        links, the other direction is possible as well.

        :param li: Network link
        :type li: NetLinkId
        :param h: Start hub
        :type h: HubId
        """
        self._check_id(li, ExceptionKey.HUBSTART_SET)
        self._hub_start[li] = h

    # ----------------- #
    # Property: hub_end #
    # ----------------- #
    def get_hub_end(self, li: NetLinkId) -> HubId:
        """
        Set the end hub of a network link. For a unidirectional link, ecs
        can be transported from the start hub to the end hub. For bidirectional
        links, the other direction is possible as well.

        :param li: Network link
        :type li: NetLinkId
        :return: End hub
        :rtype: HubId
        """
        self._check_id(li, ExceptionKey.HUBEND_GET)
        if li not in self._hub_end:
            raise exceptions.MissingIdException(
                ExceptionKey.HUBEND_GET.value, li, module=LOG_MODULE_STR
            )
        return self._hub_end[li]

    def set_hub_end(self, li: NetLinkId, h: HubId) -> None:
        """
        Set the end hub of a network link. For a unidirectional link, ecs
        can be transported from the start hub to the end hub. For bidirectional
        links, the other direction is possible as well.

        :param li: Network link
        :type li: NetLinkId
        :param h: End hub
        :type h: HubId
        """
        self._check_id(li, ExceptionKey.HUBEND_SET)
        self._hub_end[li] = h

    # ---------------- #
    # Property: length #
    # ---------------- #
    def get_length(self, li: NetLinkId) -> float:
        """
        Get the parameter 'length' which denotes the physical length of a
        network link. This is a mandatory parameter.

        :param li: Network link
        :type li: NetLinkId
        :return: Length [m]
        :rtype: float
        """
        self._check_id(li, ExceptionKey.LENGTH_GET)
        if li not in self._length:
            raise exceptions.MissingIdException(
                ExceptionKey.LENGTH_GET.value, li, module=LOG_MODULE_STR
            )
        return self._length[li]

    def set_length(self, li: NetLinkId, length: float) -> None:
        """
        Set the parameter 'length' which denotes the physical length of a
        network link. This is a mandatory parameter.

        :param li: Network link
        :type li: NetLinkId
        :param length: Length [m]
        :type length: float
        """
        self._check_id(li, ExceptionKey.LENGTH_SET)
        self._length[li] = length

    # ----------------------- #
    # Property: bidirectional #
    # ----------------------- #
    def is_bidirectional(self, li: NetLinkId) -> bool:
        """
        Get the parameter 'bidirectional' which denotes whether a network link
        is bidirectional.

        :param li: Network link
        :type li: NetLinkId
        :return: Whether the link is bidirectional
        :rtype: bool
        """
        self._check_id(li, ExceptionKey.BIDIRECTIONAL_GET)
        return self._bidirectional.get(li, DEF_BIDIRECTIONAL)

    def set_bidirectional(self, li: NetLinkId, bidirectional: bool) -> None:
        """
        Set the parameter 'bidirectional' which denotes whether a network link
        is bidirectional.

        :param li: Network link
        :type li: NetLinkId
        :param bidirectional: Whether the link is bidirectional
        :type bidirectional: bool
        """
        self._check_id(li, ExceptionKey.BIDIRECTIONAL_SET)
        self._bidirectional[li] = bidirectional

    # ----------------- #
    # Property: cap_min #
    # ----------------- #
    def get_cap_min(self, s: StageId, li: NetLinkId, e: EcId) -> float:
        """
        Get the parameter 'cap_min' which denotes the minimal amount of network
        technology capacity that has to be achieved on a network link for an
        ec through a combination of installation and remaining initial
        capacity. This is an optional parameter with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param li: Network link
        :type li: NetLinkId
        :param e: ec
        :type e: EcId
        :return: Minimal capacity [kW]
        :rtype: float
        """
        self._check_id(li, ExceptionKey.CAPMIN_GET)
        return self._cap_min.get((s, li, e), DEF_CAPMIN)

    def set_cap_min(self, s: StageId, li: NetLinkId, e: EcId, cap_min: float) -> None:
        """
        Set the parameter 'cap_min' which denotes the minimal amount of network
        technology capacity that has to be achieved on a network link for an
        ec through a combination of installation and remaining initial
        capacity. This is an optional parameter with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param li: Network link
        :type li: NetLinkId
        :param e: ec
        :type e: EcId
        :param cap_min: Minimal capacity [kW]
        :type cap_min: float
        """
        self._check_id(li, ExceptionKey.CAPMIN_SET)
        self._cap_min[s, li, e] = cap_min

    # ----------------- #
    # Property: cap_max #
    # ----------------- #
    def get_cap_max(self, s: StageId, li: NetLinkId, e: EcId) -> float:
        """
        Get the parameter 'cap_max' which denotes the maximal amount of network
        technology capacity that is permitted on a network link for an
        ec through a combination of installation and remaining initial
        capacity. This is an optional parameter with a default value of
        infinity.

        :param s: Stage
        :type s: StageId
        :param li: Network link
        :type li: NetLinkId
        :param e: ec
        :type e: EcId
        :return: Maximal capacity [kW]
        :rtype: float
        """
        self._check_id(li, ExceptionKey.CAPMAX_GET)
        return self._cap_max.get((s, li, e), DEF_CAPMAX)

    def set_cap_max(self, s: StageId, li: NetLinkId, e: EcId, cap_max: float) -> None:
        """
        Set the parameter 'cap_max' which denotes the maximal amount of network
        technology capacity that is permitted on a network link for an
        ec through a combination of installation and remaining initial
        capacity. This is an optional parameter with a default value of
        infinity.

        :param s: Stage
        :type s: StageId
        :param li: Network link
        :type li: NetLinkId
        :param e: ec
        :type e: EcId
        :param cap_max: Maximal capacity [kW]
        :type cap_max: float
        """
        self._check_id(li, ExceptionKey.CAPMAX_SET)
        self._cap_max[s, li, e] = cap_max

    # ---------------------- #
    # Property: availability #
    # ---------------------- #
    def get_availability(self, s: StageId, li: NetLinkId, e: EcId) -> TimeSeries:
        """
        Get the parameter 'availability' for a network link in a direction.
        availability is a relative value that scales the amount of available
        capacity on that link, thereby limiting the operational possibilities
        of the network technologies on that link. An availability value of
        e.g.; 0.5 means that only half of the installed technology is available
        at that time. This is an optional parameter with a default value of 1.

        :param s: Stage
        :type s: StageId
        :param li: Network link
        :type li: NetLinkId
        :param e: Ec
        :type e: EcId
        :return: Time series for availability [1]
        :rtype: TimeSeries
        """
        self._check_id(li, ExceptionKey.AVAILABILITY_GET)
        if (s, li, e) not in self._availability:
            availability = TimeSeries()
            availability.def_value = DEF_AVAILABILITY
            return availability
        return self._availability[s, li, e]

    def set_availability(
        self, s: StageId, li: NetLinkId, e: EcId, t: TimeId, availability: float
    ) -> None:
        """
        Get the parameter 'availability' for a network link in a direction at
        a specific time step. availability is a relative value that scales the
        amount of available capacity on that link, thereby limiting the
        operational possibilities of the network technologies on that link. An
        availability value of e.g.; 0.5 means that only half of the installed
        technology is available at that time. This is an optional parameter
        with a default value of 1.

        :param s: Stage
        :type s: StageId
        :param li: Network link
        :type li: NetLinkId
        :param e: Ec
        :type e: EcId
        :param t: Time
        :type t: TimeId
        :param availability: Availability [1]
        :type availability: float
        """
        self._check_id(li, ExceptionKey.AVAILABILITY_SET)
        if (s, li, e) not in self._availability:
            self._availability[s, li, e] = TimeSeries()
            self._availability[s, li, e].def_value = DEF_AVAILABILITY
        self._availability[s, li, e].set_value(t, availability)

    def set_availability_def(
        self, s: StageId, li: NetLinkId, e: EcId, availability_def: float
    ) -> None:
        """
        Get the default (with respect to time) parameter 'availability' for a
        network link in a direction. availability is a relative value that
        scales the amount of available capacity on that link, thereby limiting
        the operational possibilities of the network technologies on that link.
        An availability value of e.g.; 0.5 means that only half of the
        installed technology is available at that time. This is an optional
        parameter with a default value of 1.

        :param s: Stage
        :type s: StageId
        :param li: Network link
        :type li: NetLinkId
        :param e: Ec
        :type e: EcId
        :param availability_def: Default availability [1]
        :type availability_def: float
        """
        self._check_id(li, ExceptionKey.AVAILABILITY_DEFSET)
        if (s, li, e) not in self._availability:
            self._availability[s, li, e] = TimeSeries()
        self._availability[s, li, e].def_value = availability_def

    # ----------------- #
    # Property: sum_min #
    # ----------------- #
    def get_sum_min(
        self, s: StageId, li: NetLinkId, e: EcId, d: NetLinkDirection
    ) -> float:
        """
        Get the parameter 'sum_min' (specified as 'sum_min_forward' and
        'sum_min_backward' in the input files) which denotes the minimal amount
        of an ec's energy that has to be transported along a network link in a
        certain direction throughout a stage.

        :param s: Stage
        :type s: StageId
        :param li: Network link
        :type li: NetLinkId
        :param e: ec
        :type e: EcId
        :param d: Direction (forward or backward)
        :type d: NetLinkDirection
        :return: Minimal energy that has to be transported throughout the
            stage [kWh]
        :rtype: float
        """
        self._check_id(li, ExceptionKey.SUMMIN_GET)
        return self._sum_min.get((s, li, e, d), DEF_SUMMIN)

    def set_sum_min(
        self, s: StageId, li: NetLinkId, e: EcId, d: NetLinkDirection, sum_min: float
    ) -> None:
        """
        Set the parameter 'sum_min' (specified as 'sum_min_forward' and
        'sum_min_backward' in the input files) which denotes the minimal amount
        of an ec's energy that has to be transported along a network link in a
        certain direction throughout a stage.

        :param s: Stage
        :type s: StageId
        :param li: Network link
        :type li: NetLinkId
        :param e: ec
        :type e: EcId
        :param d: Direction (forward or backward)
        :type d: NetLinkDirection
        :param sum_min: Minimal energy that has to be transported throughout
            the stage [kWh]
        :type sum_min: float
        """
        self._check_id(li, ExceptionKey.SUMMIN_SET)
        self._sum_min[s, li, e, d] = sum_min

    # ----------------- #
    # Property: sum_max #
    # ----------------- #
    def get_sum_max(
        self, s: StageId, li: NetLinkId, e: EcId, d: NetLinkDirection
    ) -> float:
        """
        Get the parameter 'sum_max' (specified as 'sum_max_forward' and
        'sum_max_backward' in the input files) which denotes the maximal amount
        of an ec's energy that may be transported along a network link in a
        certain direction throughout a stage.

        :param s: Stage
        :type s: StageId
        :param li: Network link
        :type li: NetLinkId
        :param e: ec
        :type e: EcId
        :param d: Direction (forward or backward)
        :type d: NetLinkDirection
        :return: Maximal energy that may be transported throughout the stage
            [kWh]
        :rtype: float
        """
        self._check_id(li, ExceptionKey.SUMMAX_GET)
        return self._sum_max.get((s, li, e, d), DEF_SUMMAX)

    def set_sum_max(
        self, s: StageId, li: NetLinkId, e: EcId, d: NetLinkDirection, sum_max: float
    ) -> None:
        """
        Set the parameter 'sum_max' (specified as 'sum_max_forward' and
        'sum_max_backward' in the input files) which denotes the maximal amount
        of an ec's energy that may be transported along a network link in a
        certain direction throughout a stage.

        :param s: Stage
        :type s: StageId
        :param li: Network link
        :type li: NetLinkId
        :param e: ec
        :type e: EcId
        :param d: Direction (forward or backward)
        :type d: NetLinkDirection
        :param sum_max: Maximal energy that may be transported throughout the
            stage [kWh]
        :type sum_max: float
        """
        self._check_id(li, ExceptionKey.SUMMAX_SET)
        self._sum_max[s, li, e, d] = sum_max

    # ------------------------------- #
    # Secondary property: time_series #
    # ------------------------------- #
    @property
    def time_series(
        self,
    ) -> List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...], TimeSeries]]:
        """
        Time series profiles in the network link module. This is a list of
        tuples. Each list element has the following list entries: 1)
        ProfileKind of the profile. 2) Stage. 3) Tuple of string identifiers
        specific to the ProfileKind. 4) The TimeSeries of the profile

        :return: All time series of the network link module
        :rtype: List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...],
            TimeSeries]]
        """
        all_series: List[
            Tuple[TimeSeriesKind, StageId, Tuple[str, ...], TimeSeries]
        ] = []
        # availability
        for (s, li, e), series in self._availability.items():
            if series.has_values:
                all_series.append(
                    (TimeSeriesKind.NETLINKAVAIL, s, (li.key, e.key), series)
                )
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
        Set the value for a time series in the network link data class. The
        time series should be uniquely identified by the time series kind, the
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
        if kind == TimeSeriesKind.NETLINKAVAIL:
            li = NetLinkId(ids[0])
            e = EcId(ids[1])
            self.set_availability(s, li, e, t, value)

    # -------------------- #
    # Construction methods #
    # -------------------- #
    def __init__(self) -> None:
        self._ids: Set[NetLinkId] = set()
        self._ecs: Dict[NetLinkId, Set[EcId]] = {}
        self._hub_start: Dict[NetLinkId, HubId] = {}
        self._hub_end: Dict[NetLinkId, HubId] = {}
        self._length: Dict[NetLinkId, float] = {}
        self._bidirectional: Dict[NetLinkId, bool] = {}
        self._cap_min: Dict[Tuple[StageId, NetLinkId, EcId], float] = {}
        self._cap_max: Dict[Tuple[StageId, NetLinkId, EcId], float] = {}
        self._availability: Dict[Tuple[StageId, NetLinkId, EcId], TimeSeries] = {}
        self._sum_min: Dict[
            Tuple[StageId, NetLinkId, EcId, NetLinkDirection], float
        ] = {}
        self._sum_max: Dict[
            Tuple[StageId, NetLinkId, EcId, NetLinkDirection], float
        ] = {}

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self, stages: Stages, hubs: Hubs, ecs: Ecs, times: Times) -> None:
        """
        Validate all network link data in this object. Apart from sense-
        checking parameter in terms of quantity, this includes checking whether
        the ids from other data classes used here are known there as well.

        :param stages: Stages data class
        :type stages: Stages
        :param hubs: Hubs data class
        :type hubs: Hubs
        :param ecs: ecs data class
        :type ecs: Ecs
        :param times: Times data class
        :type times: Times
        """
        self._validate_ecs(ecs)
        self._validate_hub_start(hubs)
        self._validate_hub_end(hubs)
        self._validate_hub_start_end()
        self._validate_length()
        self._validate_cap_min(stages, ecs)
        self._validate_cap_max(stages, ecs)
        self._validate_cap_minmax()
        self._validate_availability(stages, ecs, times)
        self._validate_sum_min(stages, ecs)
        self._validate_sum_max(stages, ecs)
        self._validate_sum_minmax()

    def _validate_ecs(self, ecs: Ecs) -> None:
        for li, link_ecs in self._ecs.items():
            for e in link_ecs:
                if e not in ecs.ids:
                    msg = f"Unknown ec {e} in ecs[{li}]"
                    raise exceptions.DataException(
                        ExceptionKey.ECS_VAL.value, [e], msg, module=LOG_MODULE_STR
                    )

    def _validate_hub_start(self, hubs: Hubs) -> None:
        for li, h in self._hub_start.items():
            if h not in hubs.ids:
                msg = f"Unknown hub in hub_start[{li}] = {h}"
                raise exceptions.DataException(
                    ExceptionKey.HUBSTART_VAL.value, [li, h], msg, module=LOG_MODULE_STR
                )

    def _validate_hub_end(self, hubs: Hubs) -> None:
        for li, h in self._hub_end.items():
            if h not in hubs.ids:
                msg = f"Unknown hub in hub_end[{li}] = {h}"
                raise exceptions.DataException(
                    ExceptionKey.ECS_VAL.value, [li, h], msg, module=LOG_MODULE_STR
                )

    def _validate_hub_start_end(self) -> None:
        for li, hub_start in self._hub_start.items():
            hub_end = self._hub_end.get(li, None)
            if hub_start == hub_end:
                msg = f"Identical start_hub[{li}] = end_hub[{li}] = {hub_start}"
                raise exceptions.DataException(
                    ExceptionKey.HUBSTARTEND_SAME.value,
                    [li, hub_start, hub_end],
                    msg,
                    module=LOG_MODULE_STR,
                )

    def _validate_length(self) -> None:
        for li, length in self._length.items():
            if length < 0:
                msg = f"{length} = length[{li}] < 0"
                raise exceptions.DataException(
                    ExceptionKey.LENGTH_VAL.value, [li], msg, module=LOG_MODULE_STR
                )
            if length < EPS_ZEROCHECK:
                msg = f"{length} = length[{li}] ~ 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_cap_min(self, stages: Stages, ecs: Ecs) -> None:
        for (s, li, e), cap_min in self._cap_min.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in cap_min[{s}, {li}, {e}]"
                raise exceptions.DataException(
                    ExceptionKey.CAPMIN_VAL.value, [s], msg, module=LOG_MODULE_STR
                )
            # Unknown ec
            if e not in ecs.ids:
                msg = f"Unknown ec {e} in cap_min[{s}, {li}, {e}]"
                raise exceptions.DataException(
                    ExceptionKey.CAPMIN_VAL.value, [e], msg, module=LOG_MODULE_STR
                )
            # EC not assigned to link
            if e not in self.get_ecs(li):
                msg = (
                    f"Encountered ec {e} in cap_min[{s}, {li}, {e}] "
                    f"which is not in ecs[{li}] = {self.get_ecs(li)}"
                )
                logging.log_warning(msg, module=LOG_MODULE_STR)
            # cap_min usually nonnegative
            if cap_min < 0:
                msg = f"cap_min[{s}, {li}, {e}] = {cap_min} < 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_cap_max(self, stages: Stages, ecs: Ecs) -> None:
        for (s, li, e), cap_max in self._cap_max.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in cap_max[{s}, {li}, {e}]"
                raise exceptions.DataException(
                    ExceptionKey.CAPMIN_VAL.value, [s], msg, module=LOG_MODULE_STR
                )
            # Unknown ec
            if e not in ecs.ids:
                msg = f"Unknown ec {e} in cap_max[{s}, {li}, {e}]"
                raise exceptions.DataException(
                    ExceptionKey.CAPMIN_VAL.value, [e], msg, module=LOG_MODULE_STR
                )
            # ec not assigned to link
            if e not in self.get_ecs(li):
                msg = (
                    f"Encountered ec {e} in cap_min[{s}, {li}, {e}] "
                    f"which is not in ecs[{li}] = {self.get_ecs(li)}"
                )
                logging.log_warning(msg, module=LOG_MODULE_STR)
            # cap_max must be nonnegative
            if cap_max < 0:
                msg = f"cap_max[{s}, {li}, {e}] = {cap_max} < 0"
                raise exceptions.DataException(
                    ExceptionKey.CAPMAX_VAL.value,
                    [s, li, e],
                    msg,
                    module=LOG_MODULE_STR,
                )

    def _validate_cap_minmax(self) -> None:
        all_keys = set(self._cap_min.keys()).union(set(self._cap_max.keys()))
        for s, h, e in all_keys:
            cap_min = self.get_cap_min(s, h, e)
            cap_max = self.get_cap_max(s, h, e)
            if cap_min > cap_max:
                msg = (
                    f"{cap_min} = cap_min[{s}, {h}, {e}] > "
                    f"cap_max[{s}, {h}, {e}] = {cap_max}"
                )
                raise exceptions.DataException(
                    ExceptionKey.CAPMINMAX_VAL.value,
                    [s, h, e],
                    msg,
                    module=LOG_MODULE_STR,
                )

    def _validate_availability(self, stages: Stages, ecs: Ecs, times: Times) -> None:
        exc_key = ExceptionKey.AVAILABILITY_VAL.value
        for (s, li, e), availability in self._availability.items():
            # Unknown stage id
            if s not in stages.ids:
                msg = f"Unknown stage {s} in availability[{s}, {li}, {e}]"
                raise exceptions.DataException(
                    exc_key, [s, li, e], msg, module=LOG_MODULE_STR
                )
            # Unknown ec id
            if e not in ecs.ids:
                msg = f"Unknown ec {e} in availability[{s}, {li}, {e}]"
                raise exceptions.DataException(
                    exc_key, [s, li, e], msg, module=LOG_MODULE_STR
                )
            # Time values
            if availability.has_values:
                # Unknown time ids
                availability.validate(times, exc_key, module=LOG_MODULE_STR)
                # Availability values must be nonnegative (time values)
                for t in times.ids:
                    if availability.get_value(t) < 0:
                        msg = (
                            f"{availability.get_value(t)} = availability["
                            f"{s}, {li}, {e}][{t}] < 0"
                        )
                        raise exceptions.DataException(
                            exc_key, [s, li, e, t], msg, module=LOG_MODULE_STR
                        )
                # Availability values should be smaller than 1 (time values)
                for t in times.ids:
                    if availability.get_value(t) > 1:
                        msg = (
                            f"{availability.get_value(t)} = availability["
                            f"{s}, {li}, {e}][{t}] > 1"
                        )
                        logging.log_warning(msg, module=LOG_MODULE_STR)
                        break
            # Default values
            if not availability.has_values:
                availability_def = availability.def_value
                assert availability_def is not None
                # Availability values must be nonnegative (default value)
                if availability_def < 0:
                    msg = f"{availability_def} = availability_def[{s}, {li}, {e}] < 0"
                    raise exceptions.DataException(
                        exc_key, [s, li, e], msg, module=LOG_MODULE_STR
                    )
                # Constant availability usually not zero (default value)
                if availability_def < EPS_ZEROCHECK:
                    msg = f"{availability_def} = availability_def[{s}, {li}, {e}] ~ 0"
                    logging.log_warning(msg, module=LOG_MODULE_STR)
                # Availability values usually smaller than 1 (default value)
                if availability_def > 1:
                    msg = f"{availability_def} = availability[{s}, {li}, {e}] > 1"
                    logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_sum_min(self, stages: Stages, ecs: Ecs) -> None:
        exc_key = ExceptionKey.SUMMIN_VAL.value
        for (s, li, e, d), sum_min in self._sum_min.items():
            # Unknown stage id
            if s not in stages.ids:
                msg = f"Unknown stage {s} in sum_min[{s}, {li}, {e}, {d.value}]"
                raise exceptions.DataException(exc_key, [s], msg, module=LOG_MODULE_STR)
            # Unknown ec id
            if e not in ecs.ids:
                msg = f"Unknown ec {e} in sum_min[{s}, {li}, {e}, {d.value}]"
                raise exceptions.DataException(exc_key, [e], msg, module=LOG_MODULE_STR)
            # EC not assigned to link
            if e not in self.get_ecs(li):
                msg = (
                    f"Encountered ec {e} in sum_min[{s}, {li}, {e}, "
                    f"{d.value}] which is not in ecs[{li}] = "
                    f"{self.get_ecs(li)}"
                )
                logging.log_warning(msg, module=LOG_MODULE_STR)
            # Backward data for unidirectional link
            if d == NetLinkDirection.BACKWARD and not self.is_bidirectional(li):
                msg = (
                    f"sum_min[{s}, {li}, {e}, {d.value}] exists but "
                    f"{li} is not bidirectional"
                )
                logging.log_warning(msg, module=LOG_MODULE_STR)
            # sum_min usually nonnegative
            if sum_min < 0:
                msg = f"{sum_min} = sum_min[{s}, {li}, {e}, {d.value}] < 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_sum_max(self, stages: Stages, ecs: Ecs) -> None:
        exc_key = ExceptionKey.SUMMAX_VAL.value
        for (s, li, e, d), sum_max in self._sum_max.items():
            # Unknown stage id
            if s not in stages.ids:
                msg = f"Unknown stage {s} in sum_max[{s}, {li}, {e}, {d.value}]"
                raise exceptions.DataException(exc_key, [s], msg, module=LOG_MODULE_STR)
            # Unknown ec id
            if e not in ecs.ids:
                msg = f"Unknown ec {e} in sum_max[{s}, {li}, {e}, {d.value}]"
                raise exceptions.DataException(exc_key, [e], msg, module=LOG_MODULE_STR)
            # EC not assigned to link
            if e not in self.get_ecs(li):
                msg = (
                    f"Encountered ec {e} in sum_max[{s}, {li}, {e}, "
                    f"{d.value}] which is not in ecs[{li}] = "
                    f"{self.get_ecs(li)}"
                )
                logging.log_warning(msg, module=LOG_MODULE_STR)
            # Backward data for unidirectional link
            if d == NetLinkDirection.BACKWARD and not self.is_bidirectional(li):
                msg = (
                    f"sum_max[{s}, {li}, {e}, {d.value}] exists but "
                    f"{li} is not bidirectional"
                )
                logging.log_warning(msg, module=LOG_MODULE_STR)
            # sum_max must be nonnegative
            if sum_max < 0:
                msg = f"{sum_max} = sum_max[{s}, {li}, {e}, {d.value}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, li, e], msg, module=LOG_MODULE_STR
                )

    def _validate_sum_minmax(self) -> None:
        all_keys = set(self._sum_min.keys()).union(set(self._sum_max.keys()))
        for s, li, e, d in all_keys:
            sum_min = self.get_sum_min(s, li, e, d)
            sum_max = self.get_sum_max(s, li, e, d)
            if sum_min > sum_max:
                msg = (
                    f"{sum_min} = sum_min[{s}, {li}, {e}, "
                    f"{d.value}] > sum_max[{s}, {li}, {e}, "
                    f"{d.value}] = {sum_max}"
                )
                raise exceptions.DataException(
                    ExceptionKey.SUMMINMAX_VAL.value,
                    [s, li, e],
                    msg,
                    module=LOG_MODULE_STR,
                )

    # ---------- #
    # Id checker #
    # ---------- #
    def _check_id(self, li: NetLinkId, where: ExceptionKey) -> None:
        if li not in self._ids:
            raise exceptions.UnknownIdException(where.value, li, module=LOG_MODULE_STR)
