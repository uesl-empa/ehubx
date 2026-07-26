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
from ehubx.data.unit import CurrencyUnit, TimeUnit, Unit
from ehubx.data.value import Optional, Value


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the demand data module
    """

    PROFILETUPLES_ADD = "adding to 'profile_tuples' of Demands"
    PROFILETUPLES_REMOVE = "removing from 'profile_tuples' of Demands"
    PROFILETUPLES_VAL = "validating 'profile_tuples' of Demands"
    SUMTUPLES_ADD = "adding to 'sum_tuples' of Demands"
    SUMTUPLES_REMOVE = "removing from 'sum_tuples' of Demands"
    SUMTUPLES_VAL = "validating 'sum_tuples' of Demands"
    DEMANDPROFILE_SET = "setting 'demand_profile' of Demands"
    DEMANDPROFILE_DEFSET = "setting default 'demand_profile' of Demands"
    DEMANDPROFILE_GET = "getting 'demand_profile' from Demands"
    DEMANDPROFILE_VAL = "validating 'demand_profile' of Demands"
    DEMANDSUM_SET = "setting 'demand_sum' of Demands"
    DEMANDSUM_GET = "getting 'demand_sum' from Demands"
    DEMANDSUM_VAL = "validating 'demand_sum' of Demands"
    DEMANDUNMETPENALTY_SET = "setting 'demand_unmet_penalty' of Demands"
    DEMANTUNMETPENALTY_GET = "getting 'demand_unmet_penalty' from Demands"
    DEMANTUNMETPENALTY_VAL = "validating 'demand_unmet_penalty' of Demands"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/demand"
"""String identifying the demand data module for logging purposes"""

DEF_DEMAND: float = 0
"""Default value for parameter 'demand' in the demand data module"""

DEF_DEMANDUNMETPENALTY: float = 0
"""Default value for the unmet-demand penalty (currency per energy)"""


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
        Set of known demand (stage, hub, ec) tuples
        """
        return self._profile_tuples.union(self._sum_tuples)

    @property
    def profile_tuples(self) -> Set[Tuple[StageId, HubId, EcId]]:
        """
        Set of known demand (stage, hub, ec) tuples with a time-dependent load profile.
        """
        return self._profile_tuples

    @property
    def sum_tuples(self) -> Set[Tuple[StageId, HubId, EcId]]:
        """
        Set of known demand (stage, hub, ec) tuples with a sum-load.
        """
        return self._sum_tuples

    def add_profile_tuple(self, s: StageId, h: HubId, e: EcId, ec_unit: Unit) -> None:
        """
        Add a new demand (stage, hub, ec) tuple with a time-dependent load profile.

        :param s: Stage index of the tuple to be added
        :type s: StageId
        :param h: Hub index of the tuple to be added
        :type h: HubId
        :param e: ec index of the tuple to be added
        :type e: EcId
        :param ec_unit: Unit of the ec
        :type ec_unit: Unit
        """
        if (s, h, e) in self._profile_tuples:
            exc_key = ExceptionKey.PROFILETUPLES_ADD.value
            msg = (
                f"Trying to add already existing demand-profile tuple ({s}, {h}, {e})."
            )
            raise exceptions.DataException(
                exc_key, [s, h, e], msg, module=LOG_MODULE_STR
            )
        if (s, h, e) in self._sum_tuples:
            exc_key = ExceptionKey.PROFILETUPLES_ADD.value
            msg = (
                f"Trying to add demand-profile tuple ({s}, {h}, {e}) "
                "which is already a demand-sum tuple."
            )
            raise exceptions.DataException(
                exc_key, [s, h, e], msg, module=LOG_MODULE_STR
            )
        self._profile_tuples.add((s, h, e))
        self._demand_profile[s, h, e] = TimeSeries()
        self._demand_profile[s, h, e].def_value = Value(
            DEF_DEMAND, ec_unit / TimeUnit.H
        )

    # ------------------------ #
    # Property: demand_profile #
    # ------------------------ #
    def get_demand_profile(self, s: StageId, h: HubId, e: EcId) -> TimeSeries:
        """
        Get the parameter 'demand_profile' which denotes the amount of power that is
        scheduled to be consumed by the system. This is an optional parameter
        with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: ec
        :type e: EcId
        :return: Demands
        :rtype: TimeSeries
        """
        self._check_profile_tuple(s, h, e, ExceptionKey.DEMANDPROFILE_GET)
        return self._demand_profile[s, h, e]

    def set_demand_in_profile(
        self, s: StageId, h: HubId, e: EcId, t: TimeId, demand: Value
    ) -> None:
        """
        At a specific time, set the parameter 'demand_profile' which denotes the
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
        :param demand: Demand
        :type demand: Value
        """
        self._check_profile_tuple(s, h, e, ExceptionKey.DEMANDPROFILE_SET)
        self._demand_profile[s, h, e].set_value(t, demand)

    def set_demand_profile_def(
        self, s: StageId, h: HubId, e: EcId, demand_def: Value
    ) -> None:
        """
        Set the default (with respect to time) value for the parameter 'demand_profile'
        which denotes the amount of power that is scheduled to be consumed by
        the system. This is an optional parameter with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: ec
        :type e: EcId
        :param demand_def: Default demand
        :type demand_def: Value
        """
        self._check_profile_tuple(s, h, e, ExceptionKey.DEMANDPROFILE_DEFSET)
        self._demand_profile[s, h, e].def_value = demand_def

    # -------------------- #
    # Property: demand_sum #
    # -------------------- #
    def get_demand_sum(self, s: StageId, h: HubId, e: EcId) -> Value:
        """
        Get the parameter 'demand_sum' which denotes the total amount of power
        that is scheduled to be consumed by the system. This is an optional
        parameter with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: ec
        :type e: EcId
        :return: Demand sum
        :rtype: Value
        """
        self._check_sum_tuple(s, h, e, ExceptionKey.DEMANDSUM_GET)
        return self._demand_sum[s, h, e]

    def set_demand_sum(self, s: StageId, h: HubId, e: EcId, demand_sum: Value) -> None:
        """
        Set the parameter 'demand_sum' which denotes the total amount of demand
        that is scheduled to be consumed by the system over the entire time horizon.

        :param s: Stage index of the tuple with the demand-sum
        :type s: StageId
        :param h: Hub index of the tuple with the demand-sum
        :type h: HubId
        :param e: ec index of the tuple with the demand-sum
        :type e: EcId
        :param demand-sum: Value of the demand-sum
        :type demand-sum: Value
        """
        if (s, h, e) in self._profile_tuples:
            exc_key = ExceptionKey.SUMTUPLES_ADD.value
            msg = (
                f"Trying to set demand-sum at tuple ({s}, {h}, {e}) "
                "which is already a demand-profile tuple."
            )
            raise exceptions.DataException(
                exc_key, [s, h, e], msg, module=LOG_MODULE_STR
            )
        if (s, h, e) not in self._sum_tuples:
            self._sum_tuples.add((s, h, e))
        self._demand_sum[s, h, e] = demand_sum

    # ----------------------- #
    # Property: demand_unmet_penalty #
    # ----------------------- #
    def get_demand_unmet_penalty(
        self,
        s: StageId,
        h: HubId,
        e: EcId,
    ) -> Optional[Value]:
        """
        Get the parameter 'demand_unmet_penalty' which denotes the cost per unit
        of unmet demand energy for a (stage, hub, ec) tuple. This is an optional
        parameter; None if not set, treated as zero in the model.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: ec
        :type e: EcId
        :return: Unmet-demand penalty (currency per energy), None if not set
        :rtype: Optional[Value]
        """
        return self._demand_unmet_penalty.get((s, h, e))

    def set_demand_unmet_penalty(
        self, s: StageId, h: HubId, e: EcId, demand_unmet_penalty: Value
    ) -> None:
        """
        Set the parameter 'demand_unmet_penalty' which denotes the cost per unit of
        unmet demand energy for a (stage, hub, ec) tuple.

        :param s: Stage index of the tuple
        :type s: StageId
        :param h: Hub index of the tuple
        :type h: HubId
        :param e: ec index of the tuple
        :type e: EcId
        :param demand_unmet_penalty: Penalty cost per unit of unmet demand energy
        :type demand_unmet_penalty: Value
        """
        self._demand_unmet_penalty[s, h, e] = demand_unmet_penalty

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
        for (s, h, e), series in self._demand_profile.items():
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
        :param value: Value to set in the respective default unit
        :type value: float
        """
        if kind == TimeSeriesKind.DEMAND:
            h = HubId(ids[0])
            e = EcId(ids[1])
            unit = self._demand_profile[s, h, e].unit
            assert unit is not None
            self.set_demand_in_profile(
                s, h, e, t, Value(value, unit=Unit.get_def_unit(unit))
            )

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._profile_tuples: Set[Tuple[StageId, HubId, EcId]] = set()
        self._sum_tuples: Set[Tuple[StageId, HubId, EcId]] = set()
        self._demand_profile: Dict[Tuple[StageId, HubId, EcId], TimeSeries] = {}
        self._demand_sum: Dict[Tuple[StageId, HubId, EcId], Value] = {}
        self._demand_unmet_penalty: Dict[Tuple[StageId, HubId, EcId], Value] = {}

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
        self._validate_profile_tuples(stages, hubs, ecs)
        self._validate_sum_tuples(stages, hubs, ecs)
        self._validate_demand_profiles(ecs, times)
        self._validate_demand_sum(ecs)
        self._validate_demand_unmet_penalty(ecs)

    def _validate_profile_tuples(self, stages: Stages, hubs: Hubs, ecs: Ecs) -> None:
        exc_key = ExceptionKey.PROFILETUPLES_VAL.value
        for s, h, e in self._profile_tuples:
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in profile_tuple ({s}, {h}, {e})"
                raise exceptions.DataException(exc_key, [s], msg, module=LOG_MODULE_STR)
            # Unknown hub
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in profile_tuple ({s}, {h}, {e})"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)
            # Unknown ec
            if e not in ecs.ids:
                msg = f"Unknown ec {e} in profile_tuple ({s}, {h}, {e})"
                raise exceptions.DataException(exc_key, [e], msg, module=LOG_MODULE_STR)

    def _validate_sum_tuples(self, stages: Stages, hubs: Hubs, ecs: Ecs) -> None:
        exc_key = ExceptionKey.SUMTUPLES_VAL.value
        for s, h, e in self._sum_tuples:
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in sum_tuple ({s}, {h}, {e})"
                raise exceptions.DataException(exc_key, [s], msg, module=LOG_MODULE_STR)
            # Unknown hub
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in sum_tuple ({s}, {h}, {e})"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)
            # Unknown ec
            if e not in ecs.ids:
                msg = f"Unknown ec {e} in sum_tuple ({s}, {h}, {e})"
                raise exceptions.DataException(exc_key, [e], msg, module=LOG_MODULE_STR)

    def _validate_demand_profiles(self, ecs: Ecs, times: Times) -> None:
        exc_key = ExceptionKey.DEMANDPROFILE_VAL.value
        for (s, h, e), demand_profile in self._demand_profile.items():
            # Unit
            assert demand_profile.unit is not None
            expected_unit = ecs.get_unit(e) / TimeUnit.H
            if not demand_profile.unit.same_type_as(expected_unit):
                msg = (
                    f"Unit {demand_profile.unit} of demand_profile[{s}, {h}, {e}] "
                    f"does not match expected unit {ecs.get_unit(e) / TimeUnit.H}"
                )
                raise exceptions.DataException(
                    exc_key, [s, h, e], msg, module=LOG_MODULE_STR
                )

            # Unknown time ids
            demand_profile.validate(times, exc_key, module=LOG_MODULE_STR)
            # Demand values usually nonnegative (time values)
            if demand_profile.has_values:
                for t in times.ids:
                    if demand_profile.get_value(t).is_negative:
                        msg = (
                            f"{demand_profile.get_value(t)} = demand_profile"
                            f"[{s}, {h}, {e}][{t}] < 0"
                        )
                        logging.log_warning(msg, module=LOG_MODULE_STR)
                        break
            # Demand values usually nonnegative (default values)
            if not demand_profile.has_values:
                demand_def = demand_profile.def_value
                assert demand_def is not None
                if demand_def.is_negative:
                    msg = f"{demand_def} = demand_profile[{s}, {h}, {e}] < 0"
                    logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_demand_sum(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.DEMANDSUM_VAL.value
        for (s, h, e), demand_sum in self._demand_sum.items():
            # Unit
            expected_unit = ecs.get_unit(e)
            if not demand_sum.unit.same_type_as(expected_unit):
                msg = (
                    f"Unit of demand_sum[{s}, {h}, {e}] = {demand_sum}"
                    f"does not match expected unit {ecs.get_unit(e)}"
                )
                raise exceptions.DataException(
                    exc_key, [s, h, e], msg, module=LOG_MODULE_STR
                )
            # Demand sum must be nonnegative
            if demand_sum.is_negative:
                msg = f"{demand_sum} = demand_sum[{s}, {h}, {e}] < 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_demand_unmet_penalty(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.DEMANTUNMETPENALTY_VAL.value
        for (s, h, e), penalty in self._demand_unmet_penalty.items():
            expected_unit = CurrencyUnit.CHF / ecs.get_unit(e)
            if not penalty.unit.same_type_as(expected_unit):
                msg = (
                    f"Unit of demand_unmet_penalty[{s}, {h}, {e}] = {penalty} "
                    f"does not match expected unit {expected_unit}"
                )
                raise exceptions.DataException(
                    exc_key, [s, h, e], msg, module=LOG_MODULE_STR
                )
            if penalty.is_negative:
                msg = f"{penalty} = demand_unmet_penalty[{s}, {h}, {e}] < 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    # ---------- #
    # Id checker #
    # ---------- #
    def _check_profile_tuple(
        self, s: StageId, h: HubId, e: EcId, where: ExceptionKey
    ) -> None:
        if (s, h, e) not in self._profile_tuples:
            msg = (
                f"Encountered tuple ({s}, {h}, {e}) which is not a demand "
                f"profile tuple. This happened while {where.value}"
            )
            raise exceptions.DataException(
                where.value, [s, h, e], msg, module=LOG_MODULE_STR
            )

    def _check_sum_tuple(
        self, s: StageId, h: HubId, e: EcId, where: ExceptionKey
    ) -> None:
        if (s, h, e) not in self._sum_tuples:
            msg = (
                f"Encountered tuple ({s}, {h}, {e}) which is not a demand "
                f"sum tuple. This happened while {where.value}"
            )
            raise exceptions.DataException(
                where.value, [s, h, e], msg, module=LOG_MODULE_STR
            )
