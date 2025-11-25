"""
Load shedding data module
"""

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from ehubx.core import logging
from ehubx.core.common import TimeSeriesKind
from ehubx.data import exceptions
from ehubx.data.demand_data import Demands
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.time_data import TimeId, Times
from ehubx.data.time_series import TimeSeries
from ehubx.data.unit import CurrencyUnit, DimlessUnit, TimeUnit, Unit
from ehubx.data.value import Value


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the load shedding data
    module
    """

    TUPLES_ADD = "adding to 'tuples' of LoadShedding"
    TUPLES_REMOVE = "removing from 'tuples' of LoadShedding"
    TUPLES_VAL = "adding to 'tuples' of LoadShedding"
    ENABLED_GET = "getting 'enabled' from LoadShedding"
    ENABLED_SET = "setting 'enabled' of LoadShedding"
    MAXABS_GET = "getting 'max_abs' from LoadShedding"
    MAXABS_DEFSET = "setting default 'max_abs' of LoadShedding"
    MAXABS_SET = "setting 'max_abs' of LoadShedding"
    MAXABS_VAL = "validating 'max_abs' of LoadShedding"
    MAXREL_GET = "getting 'max_rel' from LoadShedding"
    MAXREL_SET = "setting 'max_rel' of LoadShedding"
    MAXREL_DEFSET = "setting default 'max_rel' of LoadShedding"
    MAXREL_VAL = "validating 'max_rel' of LoadShedding"
    ENERGYCOST_GET = "getting 'energy_cost' from LoadShedding"
    ENERGYCOST_DEFSET = "setting default 'energy_cost' of LoadShedding"
    ENERGYCOST_SET = "setting 'energy_cost' of LoadShedding"
    ENERGYCOST_VAL = "validating 'energy_cost' of LoadShedding"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/load_shed"
"""String identifying the load shedding data module for logging purposes"""

DEF_ENABLED: bool = True
"""Default value for parameter 'enabled' in the load shedding data module"""

DEF_MAXABS: float = float("inf")
"""Default value for parameter 'max_abs' in the load shedding data module"""

DEF_MAXREL: float = 1
"""Default value for parameter 'max_rel' in the load shedding data module"""

DEF_ENERGYCOST: float = 1e6
"""Default value for parameter 'energy_cost' in the load shedding data
module"""


class LoadShedding:
    """
    Class for load shedding data. Manages load shedding tuples, contains
    getters and setters for load shedding parameters and validation methods
    to control data integrity
    """

    # ----------------------- #
    # Property: manual_tuples #
    # ----------------------- #
    @property
    def tuples(self) -> Set[Tuple[StageId, HubId, EcId]]:
        """
        Set of (stage, hub, ec) tuples for which load shedding options can be set
        """
        return self._tuples

    def add_tuple(self, s: StageId, h: HubId, e: EcId, ec_unit: Unit) -> None:
        """
        Add a new load shedding (stage, hub, ec) tuple

        :param s: Stage index of the tuple to be added
        :type s: StageId
        :param h: Hub index of the tuple to be added
        :type h: HubId
        :param e: ec index of the tuple to be added
        :type e: EcId
        :param ec_unit: Unit of the ec
        :type ec_unit: Unit
        """
        self._tuples.add((s, h, e))
        self._enabled[s, h, e] = DEF_ENABLED
        self._max_abs[s, h, e] = TimeSeries()
        self._max_rel[s, h, e] = TimeSeries()
        self._energy_cost[s, h, e] = TimeSeries()
        self._max_abs[s, h, e].def_value = Value(DEF_MAXABS, ec_unit / TimeUnit.H)
        self._max_rel[s, h, e].def_value = Value(DEF_MAXREL, DimlessUnit())
        self._energy_cost[s, h, e].def_value = Value(
            DEF_ENERGYCOST, unit=(CurrencyUnit.CHF / ec_unit)
        )

    # ----------------------------------- #
    # Properties: enabled, enabled_preset #
    # ----------------------------------- #
    def is_enabled(self, s: StageId, h: HubId, e: EcId) -> bool:
        """
        Get the parameter 'enabled' for a load shedding (stage, hub,
        ec) tuple which indicates whether load shedding is enabled or not. This
        is an optional parameter with a defaut value of True.

        :param s: Stage in tuple
        :type s: StageId
        :param h: Hub in tuple
        :type h: HubId
        :param e: ec in tuple
        :type e: EcId
        :return: Whether load shedding is enabled on the tuple
        :rtype: bool
        """
        self._check_ids(s, h, e, ExceptionKey.ENABLED_GET)
        return self._enabled.get((s, h, e), DEF_ENABLED)

    def set_enabled(self, s: StageId, h: HubId, e: EcId, enabled: bool) -> None:
        """
        Set the parameter 'enabled' for a load shedding (stage, hub,
        ec) tuple which indicates whether load shedding is enabled or not. This
        is an optional parameter, with a default value of True.

        :param s: Stage in tuple
        :type s: StageId
        :param h: Hub in tuple
        :type h: HubId
        :param e: ec in tuple
        :type e: EcId
        :param enabled: Whether load shedding is enabled on the tuple
        :type enabled: bool
        """
        self._check_ids(s, h, e, ExceptionKey.ENABLED_SET)
        self._enabled[s, h, e] = enabled

    # ------------------- #
    # Properties: max_abs #
    # ------------------- #
    def get_max_abs(self, s: StageId, h: HubId, e: EcId) -> TimeSeries:
        """
        Get the parameter 'max_abs' for a load shedding tuple which denotes the
        maximal amount of demand power that can be shed. This is an optional
        parameter, with a default value of inifinity.

        :param s: Stage in manual tuple
        :type s: StageId
        :param h: Hub in manual tuple
        :type h: HubId
        :param e: ec in manual tuple
        :type e: EcId
        :return: Maximal sheddable demand power amounts
        :rtype: TimeSeries
        """
        self._check_ids(s, h, e, ExceptionKey.MAXABS_GET)
        return self._max_abs[s, h, e]

    def set_max_abs(
        self, s: StageId, h: HubId, e: EcId, t: TimeId, max_abs: Value
    ) -> None:
        """
        At a specific time, set the parameter 'max_abs' for a load shedding tuple
        which denotes the maximal amount of demand power that can be shed. This
        is an optional parameter with a default value of infinity.

        :param s: Stage in manual tuple
        :type s: StageId
        :param h: Hub in manual tuple
        :type h: HubId
        :param e: ec in manual tuple
        :type e: EcId
        :param t: Time
        :type t: TimeId
        :param max_abs: Maximal sheddable demand power
        :type max_abs: Value
        """
        self._check_ids(s, h, e, ExceptionKey.MAXABS_SET)
        self._max_abs[s, h, e].set_value(t, max_abs)

    def set_max_abs_def(
        self, s: StageId, h: HubId, e: EcId, max_abs_def: Value
    ) -> None:
        """
        Set the default (with respect to time) value for the parameter
        'max_abs' for a load shedding tuple which denotes the maximal amount of demand
        power that can be shed. This is an optional parameter with a default value
        of infinity.

        :param s: Stage in manual tuple
        :type s: StageId
        :param h: Hub in manual tuple
        :type h: HubId
        :param e: ec in manual tuple
        :type e: EcId
        :param max_abs_def: Default maximal sheddable demand power
        :type max_abs_def: Value
        """
        self._check_ids(s, h, e, ExceptionKey.MAXABS_DEFSET)
        self._max_abs[s, h, e].def_value = max_abs_def

    # ------------------- #
    # Properties: max_rel #
    # ------------------- #
    def get_max_rel(self, s: StageId, h: HubId, e: EcId) -> TimeSeries:
        """
        Get the parameter 'max_rel' for a load shedding tuple which denotes the
        maximal fraction of demand power that can be shed. This is an optional
        parameter with a default value of 1.

        :param s: Stage in load shedding tuple
        :type s: StageId
        :param h: Hub in load shedding tuple
        :type h: HubId
        :param e: ec in load shedding tuple
        :type e: EcId
        :return: Maximal sheddable demand fractions
        :rtype: TimeSeries
        """
        self._check_ids(s, h, e, ExceptionKey.MAXREL_GET)
        return self._max_rel[s, h, e]

    def set_max_rel(
        self, s: StageId, h: HubId, e: EcId, t: TimeId, max_rel: Value
    ) -> None:
        """
        At a specific time, set the parameter 'max_rel' for a load shedding tuple
        which denotes the maximal fraction of demand power that can be shed.
        This is an optional parameter with a default value of 1.

        :param s: Stage in load shedding tuple
        :type s: StageId
        :param h: Hub in load shedding tuple
        :type h: HubId
        :param e: ec in load shedding tuple
        :type e: EcId
        :param t: Time
        :type t: TimeId
        :param max_abs: Maximal sheddable demand fraction
        :type max_abs: Value
        """
        self._check_ids(s, h, e, ExceptionKey.MAXREL_SET)
        if not isinstance(max_rel.unit, DimlessUnit):
            raise exceptions.DataException(
                ExceptionKey.MAXREL_SET.value,
                [s, h, e],
                f"max_rel must be a dimensionless value, but has unit '{max_rel.unit}'",
                module=LOG_MODULE_STR,
            )
        self._max_rel[s, h, e].set_value(t, max_rel)

    def set_max_rel_def(
        self, s: StageId, h: HubId, e: EcId, max_rel_def: Value
    ) -> None:
        """
        Set the default (with respect to time) value for the parameter
        'max_rel' for a load shedding tuple which denotes the maximal fraction of
        demand power that can be shed. This is an optional parameter with a default
        value of 1.

        :param s: Stage in load shedding tuple
        :type s: StageId
        :param h: Hub in load shedding tuple
        :type h: HubId
        :param e: ec in load shedding tuple
        :type e: EcId
        :param max_rel_def: Default maximal sheddable demand fraction
        :type max_rel_def: Value
        """
        self._check_ids(s, h, e, ExceptionKey.MAXREL_DEFSET)
        if not isinstance(max_rel_def.unit, DimlessUnit):
            msg = (
                "max_rel_def must be a dimensionless value, but has unit "
                f"'{max_rel_def.unit}'"
            )
            raise exceptions.DataException(
                ExceptionKey.MAXREL_DEFSET.value, [s, h, e], msg, module=LOG_MODULE_STR
            )
        self._max_rel[s, h, e].def_value = max_rel_def

    # ----------------------- #
    # Properties: energy_cost #
    # ----------------------- #
    def get_energy_cost(self, s: StageId, h: HubId, e: EcId) -> TimeSeries:
        """
        Get the parameter 'energy_cost' for a load shedding tuple which denotes the
        penalization cost for each ec unit that is shed. This is an
        optional parameter, with the default being the object's
        energy_cost_preset value.

        :param s: Stage in load shedding tuple
        :type s: StageId
        :param h: Hub in load shedding tuple
        :type h: HubId
        :param e: ec in load shedding tuple
        :type e: EcId
        :return: Energy costs per amount of shed energy
        :rtype: TimeSeries
        """
        self._check_ids(s, h, e, ExceptionKey.ENERGYCOST_GET)
        return self._energy_cost[s, h, e]

    def set_energy_cost(
        self, s: StageId, h: HubId, e: EcId, t: TimeId, energy_cost: Value
    ) -> None:
        """
        At a specific time, set the parameter 'energy_cost' for a load shedding tuple
        which denotes the penalization cost for each energy unit that is shed.
        This is an optional parameter, with the default being the object's
        energy_cost_preset value.

        :param s: Stage in load shedding tuple
        :type s: StageId
        :param h: Hub in load shedding tuple
        :type h: HubId
        :param e: ec in load shedding tuple
        :type e: EcId
        :param t: Time
        :type t: TimeId
        :param energy_cost: Energy cost per amount of shed energy
        :type energy_cost: Value
        """
        self._check_ids(s, h, e, ExceptionKey.ENERGYCOST_SET)
        self._energy_cost[s, h, e].set_value(t, energy_cost)

    def set_energy_cost_def(
        self, s: StageId, h: HubId, e: EcId, energy_cost_def: Value
    ) -> None:
        """
        Set the default (with respect to time) value for the parameter
        'energy_cost' for a load shedding tuple which denotes the penalization cost
        for each energy unit that is shed. This is an optional parameter, with
        the default being the object's energy_cost_preset value.

        :param s: Stage in load shedding tuple
        :type s: StageId
        :param h: Hub in load shedding tuple
        :type h: HubId
        :param e: ec in load shedding tuple
        :type e: EcId
        :param energy_cost_def: Default energy cost per amount of shed energy
        :type energy_cost_def: Value
        """
        self._check_ids(s, h, e, ExceptionKey.ENERGYCOST_DEFSET)
        self._energy_cost[s, h, e].def_value = energy_cost_def

    # ------------------ #
    # Get enabled tuples #
    # ------------------ #
    def get_enabled_tuples(self) -> Set[Tuple[StageId, HubId, EcId]]:
        """
        Get all (stage, hub, ec) tuples in which load shedding is enabled.

        :param demands: Demands
        :type demands: Demands
        :return: Set of all enabled tuples
        :rtype: Set[Tuple[StageId, HubId, EcId]]
        """
        tuples = set()
        for s, h, e in self._tuples:
            if self.is_enabled(s, h, e):
                tuples.add((s, h, e))
        return tuples

    # ------------------------------- #
    # Secondary property: time_series #
    # ------------------------------- #
    @property
    def time_series(
        self,
    ) -> List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...], TimeSeries]]:
        """
        Time series profiles in the load shedding module. This is a list of
        tuples. Each list element has the following list entries: 1)
        ProfileKind of the profile. 2) Stage. 3) Tuple of string identifiers
        specific to the ProfileKind. 4) The TimeSeries itself

        :return: All time series of the load shedding module
        :rtype: List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...],
            TimeSeries]]
        """
        all_series: List[
            Tuple[TimeSeriesKind, StageId, Tuple[str, ...], TimeSeries]
        ] = []
        # max_abs
        for (s, h, e), series in self._max_abs.items():
            if series.has_values:
                all_series.append(
                    (TimeSeriesKind.LOADSHEDMAXABS, s, (h.key, e.key), series)
                )
        # max_rel
        for (s, h, e), series in self._max_rel.items():
            if series.has_values:
                all_series.append(
                    (TimeSeriesKind.LOADSHEDMAXREL, s, (h.key, e.key), series)
                )
        # energy_cost
        for (s, h, e), series in self._energy_cost.items():
            if series.has_values:
                all_series.append(
                    (TimeSeriesKind.LOADSHEDENERGYCOST, s, (h.key, e.key), series)
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
        Set the value for a time series in the load shedding data class. The
        time series should be uniquely identified by the time series kind, the
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
        unit: Optional[Unit]
        if kind == TimeSeriesKind.LOADSHEDMAXABS:
            h = HubId(ids[0])
            e = EcId(ids[1])
            unit = self._max_abs[s, h, e].unit
            assert unit is not None
            self.set_max_abs(s, h, e, t, Value(value, unit=Unit.get_def_unit(unit)))
        if kind == TimeSeriesKind.LOADSHEDMAXREL:
            h = HubId(ids[0])
            e = EcId(ids[1])
            unit = DimlessUnit()
            self.set_max_rel(s, h, e, t, Value(value, unit=unit))
        if kind == TimeSeriesKind.LOADSHEDENERGYCOST:
            h = HubId(ids[0])
            e = EcId(ids[1])
            unit = self._energy_cost[s, h, e].unit
            assert unit is not None
            self.set_energy_cost(s, h, e, t, Value(value, unit=Unit.get_def_unit(unit)))

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._tuples: Set[Tuple[StageId, HubId, EcId]] = set()
        self._enabled: Dict[Tuple[StageId, HubId, EcId], bool] = {}
        self._max_abs: Dict[Tuple[StageId, HubId, EcId], TimeSeries] = {}
        self._max_rel: Dict[Tuple[StageId, HubId, EcId], TimeSeries] = {}
        self._energy_cost: Dict[Tuple[StageId, HubId, EcId], TimeSeries] = {}

    # ---------- #
    # Validation #
    # ---------- #
    def validate(
        self, stages: Stages, hubs: Hubs, ecs: Ecs, demands: Demands, times: Times
    ) -> None:
        """
        Validate all load shedding data in this object. Apart from sense-
        checking parameter in terms of quantity, this includes checking whether
        the ids from other data classes used here are known there as well.

        :param stages: Stages data class
        :type stages: Stages
        :param hubs: Hubs data class
        :type hubs: Hubs
        :param ecs: ecs data class
        :type ecs: Ecs
        :param demands: Demands data class
        :type demands: Demands
        :param times: Times data class
        :type times: Times
        """
        self._validate_tuples(stages, hubs, ecs, demands)
        self._validate_max_abs(ecs, times)
        self._validate_max_rel(times)
        self._validate_energy_cost(ecs, times)

    def _validate_tuples(
        self, stages: Stages, hubs: Hubs, ecs: Ecs, demands: Demands
    ) -> None:
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
            # Not a demand tuple
            if (s, h, e) not in demands.profile_tuples:
                msg = (
                    f"({s}, {h}, {e}) is a load shedding tuple but not a "
                    f"demand profile tuple"
                )
                raise exceptions.DataException(
                    exc_key, [s, h, e], msg, module=LOG_MODULE_STR
                )

    def _validate_max_abs(self, ecs: Ecs, times: Times) -> None:
        exc_key = ExceptionKey.MAXABS_VAL.value
        for (s, h, e), max_abs in self._max_abs.items():
            if not self.is_enabled(s, h, e):
                continue
            # Unit
            assert max_abs.unit is not None
            expected_unit = ecs.get_unit(e) / TimeUnit.H
            if not max_abs.unit.same_type_as(expected_unit):
                msg = (
                    f"Unit {max_abs.unit} of max_abs[{s}, {h}, {e}] "
                    f"does not match expected unit {expected_unit}"
                )
                raise exceptions.DataException(
                    exc_key, [s, h, e], msg, module=LOG_MODULE_STR
                )
            # Unknown time ids
            max_abs.validate(times, exc_key, module=LOG_MODULE_STR)
            # max_abs must be nonnegative (time values)
            if max_abs.has_values:
                for t in times.ids:
                    if max_abs.get_value(t).is_negative:
                        msg = (
                            f"{max_abs.get_value(t)} = max_abs[{s}, {h}, {e}][{t}] < 0"
                        )
                        raise exceptions.DataException(
                            exc_key, [s, h, e, t], msg, module=LOG_MODULE_STR
                        )
            # max_abs must be nonnegative (default values)
            if not max_abs.has_values:
                max_abs_def = max_abs.def_value
                assert max_abs_def is not None
                if max_abs_def.is_negative:
                    msg = f"{max_abs_def} = max_abs[{s}, {h}, {e}] < 0"
                    raise exceptions.DataException(
                        exc_key, [s, h, e], msg, module=LOG_MODULE_STR
                    )

    def _validate_max_rel(self, times: Times) -> None:
        exc_key = ExceptionKey.MAXREL_VAL.value
        for (s, h, e), max_rel in self._max_rel.items():
            if not self.is_enabled(s, h, e):
                continue
            # Unknown time ids
            max_rel.validate(times, exc_key, module=LOG_MODULE_STR)
            # Time values
            if max_rel.has_values:
                # max_rel must be nonnegative (time values)
                for t in times.ids:
                    if max_rel.get_value(t).is_negative:
                        msg = (
                            f"{max_rel.get_value(t)} = max_rel[{s}, {h}, {e}][{t}] < 0"
                        )
                        raise exceptions.DataException(
                            exc_key, [s, h, e, t], msg, module=LOG_MODULE_STR
                        )
                # max_rel usually not larger than one (time values)
                for t in times.ids:
                    if max_rel.get_value(t) > Value(1):
                        msg = (
                            f"{max_rel.get_value(t)} = max_rel[{s}, {h}, {e}][{t}] > 1"
                        )
                        logging.log_warning(msg, module=LOG_MODULE_STR)
                        break
            # Default value
            if not max_rel.has_values:
                max_rel_def = max_rel.def_value
                assert max_rel_def is not None
                # max_abs must be nonnegative (default value)
                if max_rel_def.is_negative:
                    msg = f"{max_rel_def} = max_abs[{s}, {h}, {e}] < 0"
                    raise exceptions.DataException(
                        exc_key, [s, h, e], msg, module=LOG_MODULE_STR
                    )
                # max_abs usually not larger than one (default value)
                if max_rel_def > Value(1):
                    msg = f"{max_rel_def} = max_abs[{s}, {h}, {e}] > 1"
                    logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_energy_cost(self, ecs: Ecs, times: Times) -> None:
        exc_key = ExceptionKey.ENERGYCOST_VAL.value
        for (s, h, e), energy_cost in self._energy_cost.items():
            if not self.is_enabled(s, h, e):
                continue
            # Unit
            assert energy_cost.unit is not None
            expected_unit = CurrencyUnit.CHF / ecs.get_unit(e)
            if not energy_cost.unit.same_type_as(expected_unit):
                msg = (
                    f"Unit {energy_cost.unit} of energy_cost[{s}, {h}, {e}] "
                    f"does not match expected unit {expected_unit}"
                )
                raise exceptions.DataException(
                    exc_key, [s, h, e], msg, module=LOG_MODULE_STR
                )
            # Unknown time ids
            energy_cost.validate(times, exc_key, module=LOG_MODULE_STR)
            # energy_cost usually nonnegative (time values)
            if energy_cost.has_values:
                for t in times.ids:
                    if energy_cost.get_value(t).is_negative:
                        msg = (
                            f"{energy_cost.get_value(t)} = energy_cost"
                            f"[{s}, {h}, {e}][{t}] < 0"
                        )
                        logging.log_warning(msg, module=LOG_MODULE_STR)
                        break
            # energy_cost usually nonnegative (default value)
            if not energy_cost.has_values:
                energy_cost_def = energy_cost.def_value
                assert energy_cost_def is not None
                if energy_cost_def.is_negative:
                    msg = f"{energy_cost_def} = energy_cost[{s}, {h}, {e}] < 0"
                    logging.log_warning(msg, module=LOG_MODULE_STR)

    # ---------- #
    # Id checker #
    # ---------- #
    def _check_ids(self, s: StageId, h: HubId, e: EcId, where: ExceptionKey) -> None:
        if (s, h, e) not in self._tuples:
            msg = (
                f"Encountered tuple ({s}, {h}, {e}) which is not a load shedding "
                f"tuple. This happened while {where.value}"
            )
            raise exceptions.DataException(
                where.value, [s, h, e], msg, module=LOG_MODULE_STR
            )
