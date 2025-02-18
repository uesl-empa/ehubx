"""
Load shedding data module
"""
from enum import Enum
from typing import Dict, List, Set, Tuple
import itertools
from ehubx.core.common import TimeSeriesKind
from ehubx.core import logging
from ehubx.data.stage_data import Stages, StageId
from ehubx.data.hub_data import Hubs, HubId
from ehubx.data.ec_data import Ecs, EcId
from ehubx.data.demand_data import Demands
from ehubx.data.time_data import Times, TimeId
from ehubx.data.time_series import TimeSeries
from ehubx.data import exceptions


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the load shedding data
    module
    """
    MANUALTUPLES_ADD = "adding to 'manual_tuples' of LoadShedding"
    MANUALTUPLES_REMOVE = "removing from 'manual_tuples' of LoadShedding"
    MANUALTUPLES_VAL = "adding to 'manual_tuples' of LoadShedding"
    MAXABS_SET = "setting 'max_abs' of LoadShedding"
    MAXABS_VAL = "validating 'max_abs' of LoadShedding"
    MAXREL_SET = "setting 'max_rel' of LoadShedding"
    MAXREL_VAL = "validating 'max_rel' of LoadShedding"
    ENERGYCOST_SET = "setting 'energy_cost' of LoadShedding"
    ENERGYCOST_VAL = "validating 'energy_cost' of LoadShedding"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/load_shed"
"""String identifying the load shedding data module for logging purposes"""

DEF_ENABLED: bool = False
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
    def manual_tuples(self) -> Set[Tuple[StageId, HubId, EcId]]:
        """
        Set of (stage, hub, ec) tuples for which manual load shedding options
        can be set
        """
        return self._manual_tuples

    def add_manual_tuple(self, s: StageId, h: HubId, e: EcId) -> None:
        """
        Add a new manual (stage, hub, ec) tuple

        :param s: Stage index of the tuple to be added
        :type s: StageId
        :param h: Hub index of the tuple to be added
        :type h: HubId
        :param e: ec index of the tuple to be added
        :type e: EcId
        """
        self._manual_tuples.add((s, h, e))
        self._max_abs[s, h, e] = TimeSeries()
        self._max_rel[s, h, e] = TimeSeries()
        self._energy_cost[s, h, e] = TimeSeries()
        self._max_abs[s, h, e].def_value = self.max_abs_preset
        self._max_rel[s, h, e].def_value = self.max_rel_preset
        self._energy_cost[s, h, e].def_value = self.energy_cost_preset

    # ----------------------------------- #
    # Properties: enabled, enabled_preset #
    # ----------------------------------- #
    @property
    def enabled_preset(self) -> bool:
        """Whether load shedding is enabled as preset (i.e.; outside of manual
        tuples). This is an optional setting which is False by default"""
        return self._enabled_preset

    @enabled_preset.setter
    def enabled_preset(self, enabled_preset: bool) -> None:
        self._enabled_preset = enabled_preset

    def is_enabled(self, s: StageId, h: HubId, e: EcId) -> bool:
        """
        Get the parameter 'enabled' for a manual load shedding (stage, hub,
        ec) tuple which indicates whether load shedding is enabled or not. This
        is an optional parameter, with the default being the object's
        enabled_preset property.

        :param s: Stage in manual tuple
        :type s: StageId
        :param h: Hub in manual tuple
        :type h: HubId
        :param e: ec in manual tuple
        :type e: EcId
        :return: Whether load shedding is enabled on the manual tuple
        :rtype: bool
        """
        return self._enabled.get((s, h, e), self._enabled_preset)

    def set_enabled(self, s: StageId, h: HubId, e: EcId, enabled: bool
                    ) -> None:
        """
        Set the parameter 'enabled' for a manual load shedding (stage, hub,
        ec) tuple which indicates whether load shedding is enabled or not. This
        is an optional parameter, with the default being the object's
        enabled_preset property.

        :param s: Stage in manual tuple
        :type s: StageId
        :param h: Hub in manual tuple
        :type h: HubId
        :param e: ec in manual tuple
        :type e: EcId
        :param enabled: Whether load shedding is enabled on the manual tuple
        :type enabled: bool
        """
        if (s, h, e) not in self._manual_tuples:
            self.add_manual_tuple(s, h, e)
        self._enabled[s, h, e] = enabled

    # ----------------------------------- #
    # Properties: max_abs, max_abs_preset #
    # ----------------------------------- #
    @property
    def max_abs_preset(self) -> float:
        """Preset (i.e.; outside of manual tuples) value for the parameter
        max_abs which denotes the maximal amount of demand power that can be
        shed. This is an optional parameter with a default value of infinity"""
        return self._max_abs_preset

    def set_max_abs_preset(self, max_abs_preset: float,
                           overwrite_manual_defs: bool = False) -> None:
        """
        Set the preset (i.e.; outside of manual tuples) value for the parameter
        'max_abs' which denotes the maximal amount of demand power that can be
        shed. This is an optional parameter with a default value of
        infinity.

        :param max_abs_preset: Preset amount of maximal sheddable demand power
            [kW]
        :type max_abs_preset: float
        :param overwrite_manual_defs: Whether to overwrite the value max_abs
            for all manual tuples as well, defaults to False
        :type overwrite_manual_defs: bool, optional
        """
        self._max_abs_preset = max_abs_preset
        if overwrite_manual_defs:
            for (s, h, e) in self._manual_tuples:
                self._max_abs[s, h, e].def_value = max_abs_preset

    def get_max_abs(self, s: StageId, h: HubId, e: EcId) -> TimeSeries:
        """
        Get the parameter 'max_abs' for a manual tuple which denotes the
        maximal amount of demand power that can be shed. This is an optional
        parameter, with the default being the object's max_abs_preset value.

        :param s: Stage in manual tuple
        :type s: StageId
        :param h: Hub in manual tuple
        :type h: HubId
        :param e: ec in manual tuple
        :type e: EcId
        :return: Maximal sheddable demand power amounts [kW]
        :rtype: TimeSeries
        """
        if (s, h, e) not in self._manual_tuples:
            max_abs = TimeSeries()
            max_abs.def_value = self._max_abs_preset
            return max_abs
        return self._max_abs[s, h, e]

    def set_max_abs(self, s: StageId, h: HubId, e: EcId, t: TimeId,
                    max_abs: float) -> None:
        """
        At a specific time, set the parameter 'max_abs' for a manual tuple
        which denotes the maximal amount of demand power that can be shed. This
        is an optional parameter, with the default being the object's
        max_abs_preset value.

        :param s: Stage in manual tuple
        :type s: StageId
        :param h: Hub in manual tuple
        :type h: HubId
        :param e: ec in manual tuple
        :type e: EcId
        :param t: Time
        :type t: TimeId
        :param max_abs: Maximal sheddable demand power [kW]
        :type max_abs: float
        """
        if (s, h, e) not in self._manual_tuples:
            self.add_manual_tuple(s, h, e)
        self._max_abs[s, h, e].set_value(t, max_abs)

    def set_max_abs_def(self, s: StageId, h: HubId, e: EcId,
                        max_abs_def: float) -> None:
        """
        Set the default (with respect to time) value for the parameter
        'max_abs' for a manual tuple which denotes the maximal amount of demand
        power that can be shed. This is an optional parameter, with the default
        being the object's max_abs_preset value.

        :param s: Stage in manual tuple
        :type s: StageId
        :param h: Hub in manual tuple
        :type h: HubId
        :param e: ec in manual tuple
        :type e: EcId
        :param max_abs_def: Default maximal sheddable demand power [kW]
        :type max_abs_def: float
        """
        if (s, h, e) not in self._manual_tuples:
            self.add_manual_tuple(s, h, e)
        self._max_abs[s, h, e].def_value = max_abs_def

    # ----------------------------------- #
    # Properties: max_rel, max_rel_preset #
    # ----------------------------------- #
    @property
    def max_rel_preset(self) -> float:
        """Preset (i.e.; outside of manual tuples) value for the parameter
        max_rel which denotes the maximal fraction of demand power that can be
        shed. This is an optional parameter with a default value of 1"""
        return self._max_rel_preset

    def set_max_rel_preset(self, max_rel_preset: float,
                           overwrite_manual_defs: bool = False) -> None:
        """
        Set the preset (i.e.; outside of manual tuples) value for the parameter
        'max_rel' which denotes the maximal fraction of demand power that can
        be shed. This is an optional parameter with a default value of
        infinity.

        :param max_rel_preset: Preset fraction of maximal sheddable demand
            power [1]
        :type max_rel_preset: float
        :param overwrite_manual_defs: Whether to overwrite the value max_rel
            for all manual tuples as well, defaults to False
        :type overwrite_manual_defs: bool, optional
        """
        self._max_rel_preset = max_rel_preset
        if overwrite_manual_defs:
            for (s, h, e) in self._manual_tuples:
                self._max_rel[s, h, e].def_value = max_rel_preset

    def get_max_rel(self, s: StageId, h: HubId, e: EcId) -> TimeSeries:
        """
        Get the parameter 'max_rel' for a manual tuple which denotes the
        maximal fraction of demand power that can be shed. This is an optional
        parameter, with the default being the object's max_rel_preset value.

        :param s: Stage in manual tuple
        :type s: StageId
        :param h: Hub in manual tuple
        :type h: HubId
        :param e: ec in manual tuple
        :type e: EcId
        :return: Maximal sheddable demand fractions [1]
        :rtype: TimeSeries
        """
        if (s, h, e) not in self._manual_tuples:
            max_rel = TimeSeries()
            max_rel.def_value = self._max_rel_preset
            return max_rel
        return self._max_rel[s, h, e]

    def set_max_rel(self, s: StageId, h: HubId, e: EcId, t: TimeId,
                    max_rel: float) -> None:
        """
        At a specific time, set the parameter 'max_rel' for a manual tuple
        which denotes the maximal fraction of demand power that can be shed.
        This is an optional parameter, with the default being the object's
        max_rel_preset value.

        :param s: Stage in manual tuple
        :type s: StageId
        :param h: Hub in manual tuple
        :type h: HubId
        :param e: ec in manual tuple
        :type e: EcId
        :param t: Time
        :type t: TimeId
        :param max_abs: Maximal sheddable demand fraction [1]
        :type max_abs: float
        """
        if (s, h, e) not in self._manual_tuples:
            self.add_manual_tuple(s, h, e)
        self._max_rel[s, h, e].set_value(t, max_rel)

    def set_max_rel_def(self, s: StageId, h: HubId, e: EcId,
                        max_rel_def: float) -> None:
        """
        Set the default (with respect to time) value for the parameter
        'max_rel' for a manual tuple which denotes the maximal fraction of
        demand power that can be shed. This is an optional parameter, with the
        default being the object's max_rel_preset value.

        :param s: Stage in manual tuple
        :type s: StageId
        :param h: Hub in manual tuple
        :type h: HubId
        :param e: ec in manual tuple
        :type e: EcId
        :param max_rel_def: Default maximal sheddable demand fraction [1]
        :type max_rel_def: float
        """
        if (s, h, e) not in self._manual_tuples:
            self.add_manual_tuple(s, h, e)
        self._max_rel[s, h, e].def_value = max_rel_def

    # ------------------------------------------- #
    # Properties: energy_cost, energy_cost_preset #
    # ------------------------------------------- #
    @property
    def energy_cost_preset(self) -> float:
        """Preset (i.e.; outside of manual tuples) value for the parameter
        energy_cost which denotes the penalization cost for eacah energy unit
        that is shed. This is an optional parameter with a default value of
        0."""
        return self._energy_cost_preset

    def set_energy_cost_preset(self, energy_cost_preset: float,
                               overwrite_manual_defs: bool = False) -> None:
        """
        Set the preset (i.e.; outside of manual tuples) value for the parameter
        'energy_cost' which denotes the penalization cost for eacah energy unit
        that is shed. This is an optional parameter with a default value of 0.

        :param energy_cost_preset: Energy cost per amount of shed energy
            [CHF/kWh]
        :type energy_cost_preset: float
        :param overwrite_manual_defs: Whether to overwrite the value
            energy_cost for all manual tuples as well, defaults to False
        :type overwrite_manual_defs: bool, optional
        """
        self._energy_cost_preset = energy_cost_preset
        if overwrite_manual_defs:
            for (s, h, e) in self._manual_tuples:
                self._energy_cost[s, h, e].def_value = energy_cost_preset

    def get_energy_cost(self, s: StageId, h: HubId, e: EcId) -> TimeSeries:
        """
        Get the parameter 'energy_cost' for a manual tuple which denotes the
        penalization cost for each energy unit that is shed. This is an
        optional parameter, with the default being the object's
        energy_cost_preset value.

        :param s: Stage in manual tuple
        :type s: StageId
        :param h: Hub in manual tuple
        :type h: HubId
        :param e: ec in manual tuple
        :type e: EcId
        :return: Energy costs per amount of shed energy [CHF/kWh]
        :rtype: TimeSeries
        """
        if (s, h, e) not in self._manual_tuples:
            energy_cost = TimeSeries()
            energy_cost.def_value = self._energy_cost_preset
            return energy_cost
        return self._energy_cost[s, h, e]

    def set_energy_cost(self, s: StageId, h: HubId, e: EcId, t: TimeId,
                        energy_cost: float) -> None:
        """
        At a specific time, set the parameter 'energy_cost' for a manual tuple
        which denotes the penalization cost for each energy unit that is shed.
        This is an optional parameter, with the default being the object's
        energy_cost_preset value.

        :param s: Stage in manual tuple
        :type s: StageId
        :param h: Hub in manual tuple
        :type h: HubId
        :param e: ec in manual tuple
        :type e: EcId
        :param t: Time
        :type t: TimeId
        :param energy_cost: Energy cost per amount of shed energy [CHF/kWh]
        :type energy_cost: float
        """
        if (s, h, e) not in self._manual_tuples:
            self.add_manual_tuple(s, h, e)
        self._energy_cost[s, h, e].set_value(t, energy_cost)

    def set_energy_cost_def(self, s: StageId, h: HubId, e: EcId,
                            energy_cost_def: float) -> None:
        """
        Set the default (with respect to time) value for the parameter
        'energy_cost' for a manual tuple which denotes the penalization cost
        for each energy unit that is shed. This is an optional parameter, with
        the default being the object's energy_cost_preset value.

        :param s: Stage in manual tuple
        :type s: StageId
        :param h: Hub in manual tuple
        :type h: HubId
        :param e: ec in manual tuple
        :type e: EcId
        :param energy_cost_def: Default energy cost per amount of shed energy
            [CHF/kWh]
        :type energy_cost_def: float
        """
        if (s, h, e) not in self._manual_tuples:
            self.add_manual_tuple(s, h, e)
        self._energy_cost[s, h, e].def_value = energy_cost_def

    # ------------------ #
    # Get enabled tuples #
    # ------------------ #
    def get_enabled_tuples(self, stages: Stages, hubs: Hubs,
                           ecs: Ecs, demands: Demands
                           ) -> Set[Tuple[StageId, HubId, EcId]]:
        """
        Get all (stage, hub, ec) tuples in which load shedding is enabled (by
        default or manual)

        :param stages: Stages
        :type stages: Stages
        :param hubs: Hubs
        :type hubs: Hubs
        :param ecs: ecs
        :type ecs: Ecs
        :param demands: Demands
        :type demands: Demands
        :return: Set of all enabled tuples
        :rtype: Set[Tuple[StageId, HubId, EcId]]
        """
        # All (s, h, e) tuples are enabled as preset
        if self.enabled_preset:
            tuples = set(itertools.product(stages.ids, hubs.ids, ecs.ids))
            tuples = tuples.intersection(demands.tuples)
            for (s, h, e) in self._manual_tuples:
                if not self.is_enabled(s, h, e):
                    tuples.remove((s, h, e))
            return tuples

        # All (s, h, e) tuples are disabled as preset
        tuples = set()
        for (s, h, e) in self._manual_tuples:
            if self.is_enabled(s, h, e):
                tuples.add((s, h, e))
        return tuples

    # ------------------------------- #
    # Secondary property: time_series #
    # ------------------------------- #
    @property
    def time_series(self) -> List[Tuple[TimeSeriesKind, StageId,
                                        Tuple[str, ...], TimeSeries]]:
        """
        Time series profiles in the load shedding module. This is a list of
        tuples. Each list element has the following list entries: 1)
        ProfileKind of the profile. 2) Stage. 3) Tuple of string identifiers
        specific to the ProfileKind. 4) The TimeSeries itself

        :return: All time series of the load shedding module
        :rtype: List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...],
            TimeSeries]]
        """
        all_series: List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...],
                               TimeSeries]] = []
        # max_abs
        for (s, h, e), series in self._max_abs.items():
            if series.has_values:
                all_series.append((TimeSeriesKind.LOADSHEDMAXABS, s,
                                   (h.key, e.key), series))
        # max_rel
        for (s, h, e), series in self._max_rel.items():
            if series.has_values:
                all_series.append((TimeSeriesKind.LOADSHEDMAXREL, s,
                                   (h.key, e.key), series))
        # energy_cost
        for (s, h, e), series in self._energy_cost.items():
            if series.has_values:
                all_series.append((TimeSeriesKind.LOADSHEDENERGYCOST, s,
                                   (h.key, e.key), series))
        return all_series

    def set_time_series_val(self, kind: TimeSeriesKind, s: StageId,
                            ids: Tuple[str, ...], t: TimeId, value: float
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
        :param value: Value to set
        :type value: float
        """
        if kind == TimeSeriesKind.LOADSHEDMAXABS:
            h = HubId(ids[0])
            e = EcId(ids[1])
            self.set_max_abs(s, h, e, t, value)
        if kind == TimeSeriesKind.LOADSHEDMAXREL:
            h = HubId(ids[0])
            e = EcId(ids[1])
            self.set_max_rel(s, h, e, t, value)
        if kind == TimeSeriesKind.LOADSHEDENERGYCOST:
            h = HubId(ids[0])
            e = EcId(ids[1])
            self.set_energy_cost(s, h, e, t, value)

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._manual_tuples: Set[Tuple[StageId, HubId, EcId]] = set()
        self._enabled: Dict[Tuple[StageId, HubId, EcId], bool] = {}
        self.enabled_preset = DEF_ENABLED
        self._max_abs: Dict[Tuple[StageId, HubId, EcId], TimeSeries] = {}
        self._max_abs_preset = DEF_MAXABS
        self._max_rel: Dict[Tuple[StageId, HubId, EcId], TimeSeries] = {}
        self._max_rel_preset = DEF_MAXREL
        self._energy_cost: Dict[Tuple[StageId, HubId, EcId], TimeSeries] = {}
        self._energy_cost_preset = DEF_ENERGYCOST

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self, stages: Stages, hubs: Hubs, ecs: Ecs, demands: Demands,
                 times: Times) -> None:
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
        self._validate_max_abs(times)
        self._validate_max_rel(times)
        self._validate_energy_cost(times)

    def _validate_tuples(self, stages: Stages, hubs: Hubs, ecs: Ecs,
                         demands: Demands) -> None:
        exc_key = ExceptionKey.MANUALTUPLES_VAL.value
        for (s, h, e) in self._manual_tuples:
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in tuple ({s}, {h}, {e})"
                raise exceptions.DataException(exc_key, [s], msg,
                                               module=LOG_MODULE_STR)
            # Unknown hub
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in tuple ({s}, {h}, {e})"
                raise exceptions.DataException(exc_key, [h], msg,
                                               module=LOG_MODULE_STR)
            # Unknown ec
            if e not in ecs.ids:
                msg = f"Unknown ec {e} in tuple ({s}, {h}, {e})"
                raise exceptions.DataException(exc_key, [e], msg,
                                               module=LOG_MODULE_STR)
            # Not a demand tuple
            if (s, h, e) not in demands.tuples:
                msg = (f"({s}, {h}, {e}) is a load shedding tuple but not a "
                       "demand tuple")
                raise exceptions.DataException(exc_key, [s, h, e], msg,
                                               module=LOG_MODULE_STR)

    def _validate_max_abs(self, times: Times) -> None:
        exc_key = ExceptionKey.MAXABS_VAL.value
        # Preset value
        if self.max_abs_preset < 0:
            msg = f"{self.max_abs_preset} = max_abs_preset < 0"
            raise exceptions.DataException(exc_key, [], msg,
                                           module=LOG_MODULE_STR)
        # Manual entries
        for (s, h, e), max_abs in self._max_abs.items():
            if not self.is_enabled(s, h, e):
                continue
            # Unknown time ids
            max_abs.validate(times, exc_key, module=LOG_MODULE_STR)
            # max_abs must be nonnegative (time values)
            if max_abs.has_values:
                for t in times.ids:
                    if max_abs.get_value(t) < 0:
                        msg = (f"{max_abs.get_value(t)} = max_abs"
                            f"[{s}, {h}, {e}][{t}] < 0")
                        raise exceptions.DataException(exc_key, [s, h, e, t],
                            msg, module=LOG_MODULE_STR)
            # max_abs must be nonnegative (default values)
            if not max_abs.has_values:
                max_abs_def = max_abs.def_value
                assert max_abs_def is not None
                if max_abs_def < 0:
                    msg = f"{max_abs_def} = max_abs[{s}, {h}, {e}] < 0"
                    raise exceptions.DataException(exc_key, [s, h, e],
                                                   msg, module=LOG_MODULE_STR)

    def _validate_max_rel(self, times: Times) -> None:
        exc_key = ExceptionKey.MAXREL_VAL.value
        # Preset value negative
        if self.max_rel_preset < 0:
            msg = f"{self.max_rel_preset} = max_rel_preset < 0"
            raise exceptions.DataException(exc_key, [], msg,
                                           module=LOG_MODULE_STR)
        # Preset value larger than one
        if self.max_rel_preset > 1:
            msg = f"{self.max_rel_preset} = max_rel_preset > 1"
            logging.log_warning(msg, module=LOG_MODULE_STR)
        # Manual entries
        for (s, h, e), max_rel in self._max_rel.items():
            if not self.is_enabled(s, h, e):
                continue
            # Unknown time ids
            max_rel.validate(times, exc_key, module=LOG_MODULE_STR)
            # Time values
            if max_rel.has_values:
                # max_rel must be nonnegative (time values)
                for t in times.ids:
                    if max_rel.get_value(t) < 0:
                        msg = (f"{max_rel.get_value(t)} = max_rel"
                            f"[{s}, {h}, {e}][{t}] < 0")
                        raise exceptions.DataException(exc_key, [s, h, e, t],
                            msg, module=LOG_MODULE_STR)
                # max_rel usually not larger than one (time values)
                for t in times.ids:
                    if max_rel.get_value(t) > 1:
                        msg = (f"{max_rel.get_value(t)} = max_rel"
                            f"[{s}, {h}, {e}][{t}] > 1")
                        logging.log_warning(msg, module=LOG_MODULE_STR)
                        break
            # Default value
            if not max_rel.has_values:
                max_rel_def = max_rel.def_value
                assert max_rel_def is not None
                # max_abs must be nonnegative (default value)
                if max_rel_def < 0:
                    msg = f"{max_rel_def} = max_abs[{s}, {h}, {e}] < 0"
                    raise exceptions.DataException(exc_key, [s, h, e],
                                                   msg, module=LOG_MODULE_STR)
                # max_abs usually not larger than one (default value)
                if max_rel_def > 1:
                    msg = f"{max_rel_def} = max_abs[{s}, {h}, {e}] > 1"
                    logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_energy_cost(self, times: Times) -> None:
        exc_key = ExceptionKey.ENERGYCOST_VAL.value
        # Preset value
        if self.energy_cost_preset < 0:
            msg = f"{self.energy_cost_preset} = energy_cost_preset < 0"
            logging.log_warning(msg, module=LOG_MODULE_STR)
        # Manual entries
        for (s, h, e), energy_cost in self._energy_cost.items():
            if not self.is_enabled(s, h, e):
                continue
            # Unknown time ids
            energy_cost.validate(times, exc_key, module=LOG_MODULE_STR)
            # energy_cost usually nonnegative (time values)
            if energy_cost.has_values:
                for t in times.ids:
                    if energy_cost.get_value(t) < 0:
                        msg = (f"{energy_cost.get_value(t)} = energy_cost"
                            f"[{s}, {h}, {e}][{t}] < 0")
                        logging.log_warning(msg, module=LOG_MODULE_STR)
                        break
            # energy_cost usually nonnegative (default value)
            if not energy_cost.has_values:
                energy_cost_def = energy_cost.def_value
                assert energy_cost_def is not None
                if energy_cost_def < 0:
                    msg = (f"{energy_cost_def} = energy_cost"
                           f"[{s}, {h}, {e}] < 0")
                    logging.log_warning(msg, module=LOG_MODULE_STR)
