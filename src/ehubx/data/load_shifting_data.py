"""
Load shifting data module
"""
from typing import Dict, List, Set, Tuple
from enum import Enum
import itertools
from ehubx.core.common import TimeSeriesKind, EPS_ZEROCHECK
from ehubx.core import logging
from ehubx.data.index import Index, IndexKind
from ehubx.data.stage_data import Stages, StageId
from ehubx.data.hub_data import Hubs, HubId
from ehubx.data.ec_data import Ecs, EcId
from ehubx.data.demand_data import Demands
from ehubx.data.time_data import Times, TimeId
from ehubx.data.time_series import TimeSeries
from ehubx.data import exceptions


class LoadShiftId(Index):
    """
    Load shift index
    """
    def __init__(self, key: str) -> None:
        super().__init__(IndexKind.LOADSHIFT, key)


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the load shifting data
    module
    """
    ID_ADD = "adding to 'ids' of LoadShifting"
    ID_REMOVE = "adding from 'ids' of LoadShifting"
    STAGE_ADD = "setting 'stage' of LoadShifting"
    STAGE_VAL = "validating 'stage' of LoadShifting"
    HUB_ADD = "setting 'hub' of LoadShifting"
    HUB_VAL = "validating 'hub' of LoadShifting"
    EC_ADD = "setting 'ec' of LoadShifting"
    EC_VAL = "validating 'ec' of LoadShifting"
    TUPLES_GET = "getting 'tuples' from LoadShifting"
    TUPLES_VAL = "validating 'tuples' from LoadShifting"
    INTERVALLENGTH_SET = "setting 'interval_length' of LoadShifting"
    INTERVALLENGTH_GET = "getting 'interval_length' from LoadShifting"
    INTERVALLENGTH_VAL = "validating 'interval_length' of LoadShifting"
    INTERVALCAP_SET = "setting 'interval_cap' of LoadShifting"
    INTERVALCAP_GET = "getting 'interval_cap' from LoadShifting"
    INTERVALCAP_VAL = "validating 'interval_cap' of LoadShifting"
    MAXABOVEABS_SET = "setting 'max_above_abs' of LoadShifting"
    MAXABOVEABS_DEFSET = "setting default 'max_above_abs' of LoadShifting"
    MAXABOVEABS_GET = "getting 'max_above_abs' from LoadShifting"
    MAXABOVEABS_VAL = "validating 'max_above_abs' of LoadShifting"
    MAXABOVEREL_SET = "setting 'max_above_rel' of LoadShifting"
    MAXABOVEREL_DEFSET = "setting default 'max_above_rel' of LoadShifting"
    MAXABOVEREL_GET = "getting 'max_above_rel' from LoadShifting"
    MAXABOVEREL_VAL = "validating 'max_above_rel' of LoadShifting"
    MAXBELOWABS_SET = "setting 'max_below_abs' of LoadShifting"
    MAXBELOWABS_DEFSET = "setting default 'max_below_abs' of LoadShifting"
    MAXBELOWABS_GET = "getting 'max_below_abs' from LoadShifting"
    MAXBELOWABS_VAL = "validating 'max_below_abs' of LoadShifting"
    MAXBELOWREL_SET = "setting 'max_below_rel' of LoadShifting"
    MAXBELOWREL_DEFSET = "setting default 'max_below_rel' of LoadShifting"
    MAXBELOWREL_GET = "getting 'max_below_rel' from LoadShifting"
    MAXBELOWREL_VAL = "validating 'max_below_rel' of LoadShifting"
    PEAKCOSTABOVE_SET = "setting 'peak_cost_above' of LoadShifting"
    PEAKCOSTABOVE_GET = "getting 'peak_cost_above' from LoadShifting"
    PEAKCOSTABOVE_VAL = "validating 'peak_cost_above' of LoadShifting"
    PEAKCOSTBELOW_SET = "setting 'peak_cost_below' of LoadShifting"
    PEAKCOSTBELOW_GET = "getting 'peak_cost_below' from LoadShifting"
    PEAKCOSTBELOW_VAL = "validating 'peak_cost_below' of LoadShifting"
    ENERGYCOSTABOVE_SET = "setting 'energy_cost_above' of LoadShifting"
    ENERGYCOSTABOVE_DEFSET = "setting default 'energy_cost_above' of " + \
        "LoadShifting"
    ENERGYCOSTABOVE_GET = "getting 'energy_cost_above' from LoadShifting"
    ENERGYCOSTABOVE_VAL = "validating 'energy_cost_above' of LoadShifting"
    ENERGYCOSTBELOW_SET = "setting 'energy_cost_below' of LoadShifting"
    ENERGYCOSTBELOW_DEFSET = "setting default 'energy_cost_below' of " + \
        "LoadShifting"
    ENERGYCOSTBELOW_GET = "getting 'energy_cost_below' from LoadShifting"
    ENERGYCOSTBELOW_VAL = "validating 'energy_cost_below' of LoadShifting"
    ENERGYCOSTABOVEBELOWNONZERO_VAL = (
        "valdating that not both 'energy_cost_above' and 'energy_cost_below' "
        "are zero")
    FIXCOST_SET = "setting 'fix_cost' of LoadShifting"
    FIXCOST_DEFSET = "setting default 'fix_cost' of LoadShifting"
    FIXCOST_GET = "getting 'fix_cost' from LoadShifting"
    FIXCOST_VAL = "validating 'fix_cost' of LoadShifting"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/load_shift"
"""String identifying the load shifting data module for logging purposes"""

DEF_INTERVALCAP: float = float("inf")
"""Default value for parameter 'interval_cap' in the load shifting data
module"""

DEF_MAXABOVEABS: float = float("inf")
"""Default value for parameter 'max_above_abs' in the load shifting data
module"""

DEF_MAXABOVEREL: float = float("inf")
"""Default value for parameter 'max_above_rel' in the load shifting data
module"""

DEF_MAXBELOWABS: float = float("inf")
"""Default value for parameter 'max_below_abs' in the load shifting data
module"""

DEF_MAXBELOWREL: float = 1
"""Default value for parameter 'max_below_rel' in the load shifting data
module"""

DEF_PEAKCOSTABOVE: float = 0
"""Default value for parameter 'peak_cost_above' in the load shifting data
module"""

DEF_PEAKCOSTBELOW: float = 0
"""Default value for parameter 'peak_cost_below' in the load shifting data
module"""

DEF_ENERGYCOSTABOVE: float = 0
"""Default value for parameter 'energy_cost_above' in the load shifting data
module"""

DEF_ENERGYCOSTBELOW: float = 0
"""Default value for parameter 'energy_cost_below' in the load shifting data
module"""

DEF_FIXCOST: float = 0
"""Default value for parameter 'fix_cost' in the load shifting data
module"""


class LoadShifting:
    """
    Class for load shifting data. Manages load shifting ids, contains
    getters and setters for load shifting parameters and validation methods
    to control data integrity
    """

    # ------------- #
    # Property: ids #
    # ------------- #
    @property
    def ids(self) -> Set[LoadShiftId]:
        """
        Set of known load shifting ids
        """
        return self._ids

    def add_id(self, ls: LoadShiftId) -> None:
        """
        Add a new load shifting id

        :param ls: Id to be added
        :type ls: LoadShiftTechId
        """
        if ls in self._ids:
            raise exceptions.DuplicateIdException(ExceptionKey.ID_ADD.value,
                                                  ls, module=LOG_MODULE_STR)
        self._ids.add(ls)

    # ----------------------------- #
    # Properties: stages, sets, ecs #
    # ----------------------------- #
    def get_tuples(self, ls: LoadShiftId) -> Set[Tuple[StageId, HubId, EcId]]:
        """
        Get all tuples of (stage, hub, ec) that are encompassed for a specific
        load shifting id

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :return: Set of (stage, hub, ec) tuples
        :rtype: Set[Tuple[StageId, HubId, EcId]]
        """
        self._check_id(ls, ExceptionKey.TUPLES_GET)
        stages = self._stages.get(ls, set())
        hubs = self._hubs.get(ls, set())
        ecs = self._ecs.get(ls, set())
        return set(itertools.product(stages, hubs, ecs))

    def add_stage(self, ls: LoadShiftId, s: StageId) -> None:
        """
        Add a stage to a load shifting index

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param s: Stage
        :type s: StageId
        """
        self._check_id(ls, ExceptionKey.STAGE_ADD)
        if ls not in self._stages:
            self._stages[ls] = set()
        self._stages[ls].add(s)

    def add_hub(self, ls: LoadShiftId, h: HubId) -> None:
        """
        Add a hub to a load shifting index

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param h: Hub
        :type h: HubId
        """
        self._check_id(ls, ExceptionKey.HUB_ADD)
        if ls not in self._hubs:
            self._hubs[ls] = set()
        self._hubs[ls].add(h)

    def add_ec(self, ls: LoadShiftId, e: EcId) -> None:
        """
        Add an ec to a load shifting index

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param e: ec
        :type e: EcId
        """
        self._check_id(ls, ExceptionKey.EC_ADD)
        if ls not in self._ecs:
            self._ecs[ls] = set()
        self._ecs[ls].add(e)

    # ------------------------- #
    # Property: interval_length #
    # ------------------------- #
    def get_interval_length(self, ls: LoadShiftId) -> int:
        """
        Get the parameter 'interval_length' which denotes number of time steps
        that are included on each load shifting interval. This is a mandatory
        parameter.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :return: Number of time steps in each load shifting interval [1]
        :rtype: int
        """
        self._check_id(ls, ExceptionKey.INTERVALLENGTH_GET)
        if ls not in self._interval_length:
            raise exceptions.MissingIdException(
                ExceptionKey.INTERVALLENGTH_GET.value, ls,
                module=LOG_MODULE_STR)
        return self._interval_length[ls]

    def set_interval_length(self, ls: LoadShiftId,
                            interval_length: int) -> None:
        """
        Set the parameter 'interval_length' which denotes number of time steps
        that are included on each load shifting interval. This is a mandatory
        parameter.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param interval_length: Number of time steps in each load shifting
            interval [1]
        :type interval_length: int
        """
        self._check_id(ls, ExceptionKey.INTERVALLENGTH_SET)
        self._interval_length[ls] = interval_length

    # ----------------------- #
    # Property: max_above_abs #
    # ----------------------- #
    def get_max_above_abs(self, ls: LoadShiftId) -> TimeSeries:
        """
        Get the parameter 'max_above_abs' which denotes the maximal amount of
        load shifting that can occur above the demand curve. This is an
        optional parameter with a default value of infinity.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :return: Maximal absolute above-shifts [kW]
        :rtype: TimeSeries
        """
        self._check_id(ls, ExceptionKey.MAXABOVEABS_GET)
        if ls not in self._max_above_abs:
            max_above_abs = TimeSeries()
            max_above_abs.def_value = DEF_MAXABOVEABS
            return max_above_abs
        return self._max_above_abs[ls]

    def set_max_above_abs(self, ls: LoadShiftId, t: TimeId,
                          max_above_abs: float) -> None:
        """
        Set the parameter 'max_above_abs' at a specific time which denotes the
        maximal amount of load shifting that can occur above the demand curve.
        This is an optional parameter with a default value of infinity.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param t: Time
        :type t: TimeId
        :param max_above_abs: Maximal absolute above-shift [kW]
        :type max_above_abs: float
        """
        self._check_id(ls, ExceptionKey.MAXABOVEABS_SET)
        if ls not in self._max_above_abs:
            self._max_above_abs[ls] = TimeSeries()
            self._max_above_abs[ls].def_value = DEF_MAXABOVEABS
        self._max_above_abs[ls].set_value(t, max_above_abs)

    def set_max_above_abs_def(self, ls: LoadShiftId,
                              max_above_abs_def: float) -> None:
        """
        Set the default (with respect to time) value of the parameter
        'max_above_abs' at a specific time which denotes the maximal amount of
        load shifting that can occur above the demand curve. This is an
        optional parameter with a default value of infinity.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param max_above_abs_def: Default maximal absolute above-shift [kW]
        :type max_above_abs_def: float
        """
        self._check_id(ls, ExceptionKey.MAXABOVEABS_DEFSET)
        if ls not in self._max_above_abs:
            self._max_above_abs[ls] = TimeSeries()
        self._max_above_abs[ls].def_value = max_above_abs_def

    # ----------------------- #
    # Property: max_above_rel #
    # ----------------------- #
    def get_max_above_rel(self, ls: LoadShiftId) -> TimeSeries:
        """
        Get the parameter 'max_above_rel' which denotes the maximal amount of
        load shifting that can occur above the demand curve, relative to the
        demand curve itself. This is an optional parameter with a default value
        of infinity.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :return: Maximal relative above-shifts [1]
        :rtype: TimeSeries
        """
        self._check_id(ls, ExceptionKey.MAXABOVEREL_GET)
        if ls not in self._max_above_rel:
            max_above_rel = TimeSeries()
            max_above_rel.def_value = DEF_MAXABOVEREL
            return max_above_rel
        return self._max_above_rel[ls]

    def set_max_above_rel(self, ls: LoadShiftId, t: TimeId,
                          max_above_rel: float) -> None:
        """
        Set the parameter 'max_above_rel' at a specific time which denotes the
        maximal amount of load shifting that can occur above the demand curve,
        relative to the demand curve itself. This is an optional parameter with
        a default value of infinity.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param t: Time
        :type t: TimeId
        :param max_above_rel: Maximal relative above-shift [1]
        :type max_above_rel: float
        """
        self._check_id(ls, ExceptionKey.MAXABOVEREL_SET)
        if ls not in self._max_above_rel:
            self._max_above_rel[ls] = TimeSeries()
            self._max_above_rel[ls].def_value = DEF_MAXABOVEREL
        self._max_above_rel[ls].set_value(t, max_above_rel)

    def set_max_above_rel_def(self, ls: LoadShiftId,
                              max_above_rel_def: float) -> None:
        """
        Set a default (with respect to time) for the parameter 'max_above_rel'
        at a specific time which denotes the maximal amount of load shifting
        that can occur above the demand curve, relative to the demand curve
        itself. This is an optional parameter with a default value of infinity.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param max_above_rel_def: Default maximal relative above-shift [1]
        :type max_above_rel_def: float
        """
        self._check_id(ls, ExceptionKey.MAXABOVEREL_DEFSET)
        if ls not in self._max_above_rel:
            self._max_above_rel[ls] = TimeSeries()
        self._max_above_rel[ls].def_value = max_above_rel_def

    # ----------------------- #
    # Property: max_below_abs #
    # ----------------------- #
    def get_max_below_abs(self, ls: LoadShiftId) -> TimeSeries:
        """
        Get the parameter 'max_below_abs' which denotes the maximal amount of
        load shifting that can occur below the demand curve. This is an
        optional parameter with a default value of infinity.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :return: Maximal absolute below-shifts [kW]
        :rtype: TimeSeries
        """
        self._check_id(ls, ExceptionKey.MAXBELOWABS_GET)
        if ls not in self._max_below_abs:
            max_below_abs = TimeSeries()
            max_below_abs.def_value = DEF_MAXBELOWABS
            return max_below_abs
        return self._max_below_abs[ls]

    def set_max_below_abs(self, ls: LoadShiftId, t: TimeId,
                          max_below_abs: float) -> None:
        """
        Set the parameter 'max_below_abs' at a specific time which denotes the
        maximal amount of load shifting that can occur below the demand curve.
        This is an optional parameter with a default value of infinity.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param t: Time
        :type t: TimeId
        :param max_below_abs: Maximal absolute below-shift [kW]
        :type max_below_abs: float
        """
        self._check_id(ls, ExceptionKey.MAXBELOWABS_SET)
        if ls not in self._max_below_abs:
            self._max_below_abs[ls] = TimeSeries()
            self._max_below_abs[ls].def_value = DEF_MAXBELOWABS
        self._max_below_abs[ls].set_value(t, max_below_abs)

    def set_max_below_abs_def(self, ls: LoadShiftId,
                              max_below_abs_def: float) -> None:
        """
        Set the default (with respect to time) value of the parameter
        'max_below_abs' at a specific time which denotes the maximal amount of
        load shifting that can occur below the demand curve. This is an
        optional parameter with a default value of infinity.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param max_below_abs_def: Default maximal absolute below-shift [kW]
        :type max_below_abs_def: float
        """
        self._check_id(ls, ExceptionKey.MAXBELOWABS_DEFSET)
        if ls not in self._max_below_abs:
            self._max_below_abs[ls] = TimeSeries()
        self._max_below_abs[ls].def_value = max_below_abs_def

    # ----------------------- #
    # Property: max_below_rel #
    # ----------------------- #
    def get_max_below_rel(self, ls: LoadShiftId) -> TimeSeries:
        """
        Get the parameter 'max_below_rel' which denotes the maximal amount of
        load shifting that can occur below the demand curve, relative to the
        demand curve itself. This is an optional parameter with a default value
        of 1.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :return: Maximal relative below-shifts [1]
        :rtype: TimeSeries
        """
        self._check_id(ls, ExceptionKey.MAXBELOWREL_GET)
        if ls not in self._max_below_rel:
            max_below_rel = TimeSeries()
            max_below_rel.def_value = DEF_MAXBELOWREL
            return max_below_rel
        return self._max_below_rel[ls]

    def set_max_below_rel(self, ls: LoadShiftId, t: TimeId,
                          max_below_rel: float) -> None:
        """
        Set the parameter 'max_below_rel' at a specific time which denotes the
        maximal amount of load shifting that can occur below the demand curve,
        relative to the demand curve itself. This is an optional parameter with
        a default value of 1.


        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param t: Time
        :type t: TimeId
        :param max_below_rel: Maximal relative below-shift [1]
        :type max_below_rel: float
        """
        self._check_id(ls, ExceptionKey.MAXBELOWREL_SET)
        if ls not in self._max_below_rel:
            self._max_below_rel[ls] = TimeSeries()
            self._max_below_rel[ls].def_value = DEF_MAXBELOWREL
        self._max_below_rel[ls].set_value(t, max_below_rel)

    def set_max_below_rel_def(self, ls: LoadShiftId,
                              max_below_rel_def: float) -> None:
        """
        Set a default (with respect to time) for the parameter 'max_below_rel'
        at a specific time which denotes the maximal amount of load shifting
        that can occur below the demand curve, relative to the demand curve
        itself. This is an optional parameter with a default value of 1.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param max_below_rel_def: Default maximal relative below-shift [1]
        :type max_below_rel_def: float
        """
        self._check_id(ls, ExceptionKey.MAXBELOWREL_DEFSET)
        if ls not in self._max_below_rel:
            self._max_below_rel[ls] = TimeSeries()
        self._max_below_rel[ls].def_value = max_below_rel_def

    # ---------------------- #
    # Property: interval_cap #
    # ---------------------- #
    def get_interval_cap(self, ls: LoadShiftId) -> float:
        """
        Get the parameter 'interval_cap' which denotes the amount of installed
        load shifting capacity, i.e.; the amount of energy that can be used for
        load shifting purposes in above or below direction on each load shift
        interval. This is an optional parameter with a default value of
        infinity.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :return: Load shifting interval capacity [kWh]
        :rtype: float
        """
        self._check_id(ls, ExceptionKey.INTERVALCAP_GET)
        return self._interval_cap.get(ls, DEF_INTERVALCAP)

    def set_interval_cap(self, ls: LoadShiftId, interval_cap: float) -> None:
        """
        Set the parameter 'interval_cap' which denotes the amount of installed
        load shifting capacity, i.e.; the amount of energy that can be used for
        load shifting purposes in above or below direction on each load shift
        interval. This is an optional parameter with a default value of
        infinity.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param interval_cap: Load shifting interval capacity [kWh]
        :type interval_cap: float
        """
        self._check_id(ls, ExceptionKey.INTERVALCAP_SET)
        self._interval_cap[ls] = interval_cap

    # ------------------------- #
    # Property: peak_cost_above #
    # ------------------------- #
    def get_peak_cost_above(self, ls: LoadShiftId) -> float:
        """
        Get the parameter 'peak_cost_above' which denotes the cost for the
        largest amount of above-shifts on the entire time horizon.
        This is an optional parameter with a default value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :return: Peak cost above the demand curve [CHF/kW]
        :rtype: float
        """
        self._check_id(ls, ExceptionKey.PEAKCOSTABOVE_GET)
        return self._peak_cost_above.get(ls, DEF_PEAKCOSTABOVE)

    def set_peak_cost_above(self, ls: LoadShiftId,
                            peak_cost_above: float) -> None:
        """
        Set the parameter 'peak_cost_above' which denotes the cost for the
        largest amount of above-shifts on the entire time horizon.
        This is an optional parameter with a default value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param peak_cost_above: Peak cost above the demand curve [CHF/kW]
        :type peak_cost_above: float
        """
        self._check_id(ls, ExceptionKey.PEAKCOSTABOVE_SET)
        self._peak_cost_above[ls] = peak_cost_above

    # ------------------------- #
    # Property: peak_cost_below #
    # ------------------------- #
    def get_peak_cost_below(self, ls: LoadShiftId) -> float:
        """
        Get the parameter 'peak_cost_below' which denotes the cost for the
        largest amount of below-shifts on the entire time horizon.
        This is an optional parameter with a default value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :return: Peak cost below the demand curve [CHF/kW]
        :rtype: float
        """
        self._check_id(ls, ExceptionKey.PEAKCOSTBELOW_GET)
        return self._peak_cost_below.get(ls, DEF_PEAKCOSTBELOW)

    def set_peak_cost_below(self, ls: LoadShiftId,
                            peak_cost_below: float) -> None:
        """
        Set the parameter 'peak_cost_below' which denotes the cost for the
        largest amount of below-shifts on the entire time horizon.
        This is an optional parameter with a default value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param peak_cost_below: Peak cost below the demand curve [CHF/kW]
        :type peak_cost_below: float
        """
        self._check_id(ls, ExceptionKey.PEAKCOSTBELOW_SET)
        self._peak_cost_below[ls] = peak_cost_below

    # --------------------------- #
    # Property: energy_cost_above #
    # --------------------------- #
    def get_energy_cost_above(self, ls: LoadShiftId) -> TimeSeries:
        """
        Get the parameter 'energy_cost_above' which denotes the penalization
        cost for each energy unit of above-shifting. This is an optional
        parameter with a default value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :return: Energy costs above the demand curve [CHF/kWh]
        :rtype: TimeSeries
        """
        self._check_id(ls, ExceptionKey.ENERGYCOSTABOVE_GET)
        if ls not in self._energy_cost_above:
            energy_cost_above = TimeSeries()
            energy_cost_above.def_value = DEF_ENERGYCOSTABOVE
            return energy_cost_above
        return self._energy_cost_above[ls]

    def set_energy_cost_above(self, ls: LoadShiftId, t: TimeId,
                              energy_cost_above: float) -> None:
        """
        At a specific time, set the parameter 'energy_cost_above' which denotes
        the penalization cost for each energy unit of above-shifting. This is
        an optional parameter with a default value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param t: Time
        :type t: TimeId
        :param energy_cost_above: Energy cost above the demand curve [CHF/kWh]
        :type energy_cost_above: float
        """
        self._check_id(ls, ExceptionKey.ENERGYCOSTABOVE_SET)
        if ls not in self._energy_cost_above:
            self._energy_cost_above[ls] = TimeSeries()
            self._energy_cost_above[ls].def_value = DEF_ENERGYCOSTABOVE
        self._energy_cost_above[ls].set_value(t, energy_cost_above)

    def set_energy_cost_above_def(self, ls: LoadShiftId,
                                  energy_cost_above_def: float) -> None:
        """
        Set the default (with respect to time) value of the parameter
        'energy_cost_above' which denotes the penalization cost for each energy
        unit of above-shifting. This is an optional parameter with a default
        value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param energy_cost_above_def: Default energy cost above the demand
            curve [CHF/kWh]
        :type energy_cost_above_def: float
        """
        self._check_id(ls, ExceptionKey.ENERGYCOSTABOVE_DEFSET)
        if ls not in self._energy_cost_above:
            self._energy_cost_above[ls] = TimeSeries()
        self._energy_cost_above[ls].def_value = energy_cost_above_def

    # --------------------------- #
    # Property: energy_cost_below #
    # --------------------------- #
    def get_energy_cost_below(self, ls: LoadShiftId) -> TimeSeries:
        """
        Get the parameter 'energy_cost_below' which denotes the penalization
        cost for each energy unit of below-shifting. This is an optional
        parameter with a default value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :return: Energy costs below the demand curve [CHF/kWh]
        :rtype: TimeSeries
        """
        self._check_id(ls, ExceptionKey.ENERGYCOSTBELOW_GET)
        if ls not in self._energy_cost_below:
            energy_cost_below = TimeSeries()
            energy_cost_below.def_value = DEF_ENERGYCOSTBELOW
            return energy_cost_below
        return self._energy_cost_below[ls]

    def set_energy_cost_below(self, ls: LoadShiftId, t: TimeId,
                              energy_cost_below: float) -> None:
        """
        At a specific time, set the parameter 'energy_cost_below' which denotes
        the penalization cost for each energy unit of below-shifting. This is
        an optional parameter with a default value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param t: Time
        :type t: TimeId
        :param energy_cost_below: Energy cost below the demand curve [CHF/kWh]
        :type energy_cost_below: float
        """
        self._check_id(ls, ExceptionKey.ENERGYCOSTBELOW_SET)
        if ls not in self._energy_cost_below:
            self._energy_cost_below[ls] = TimeSeries()
            self._energy_cost_below[ls].def_value = DEF_ENERGYCOSTBELOW
        self._energy_cost_below[ls].set_value(t, energy_cost_below)

    def set_energy_cost_below_def(self, ls: LoadShiftId,
                                  energy_cost_below_def: float) -> None:
        """
        Set the default (with respect to time) value of the parameter
        'energy_cost_below' which denotes the penalization cost for each energy
        unit of below-shifting. This is an optional parameter with a default
        value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param energy_cost_below_def: Default energy cost below the demand
            curve [CHF/kWh]
        :type energy_cost_below_def: float
        """
        self._check_id(ls, ExceptionKey.ENERGYCOSTBELOW_DEFSET)
        if ls not in self._energy_cost_below:
            self._energy_cost_below[ls] = TimeSeries()
        self._energy_cost_below[ls].def_value = energy_cost_below_def

    # ------------------ #
    # Property: fix_cost #
    # ------------------ #
    def get_fix_cost(self, ls: LoadShiftId) -> TimeSeries:
        """
        Get the parameter 'fix_cost' which denotes fixed costs that arise per
        timestep when any amount of load shifting occurs at all. Be aware that
        whenever this parameter is set to a nonzero value, binary variables
        will be added to the MILP model for each time step. This will
        drastically increase the complexity and solving speed of the model,
        and should only be used for comparably small systems. This is an
        optional parameter with a default value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :return: Fixed costs [CHF/h]
        :rtype: TimeSeries
        """
        self._check_id(ls, ExceptionKey.FIXCOST_GET)
        if ls not in self._fix_cost:
            fix_cost = TimeSeries()
            fix_cost.def_value = DEF_FIXCOST
            return fix_cost
        return self._fix_cost[ls]

    def set_fix_cost(self, ls: LoadShiftId, t: TimeId, fix_cost: float
                     ) -> None:
        """
        At a specific time step, set the parameter 'fix_cost' which denotes
        fixed costs that arise per timestep when any amount of load shifting
        occurs at all. Be aware that whenever this parameter is set to a
        nonzero value, binary variables will be added to the MILP model for
        each time step. This will drastically increase the complexity and
        solving speed of the model, and should only be used for comparably
        small systems. This is an optional parameter with a default value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param t: Time
        :type t: TimeId
        :param fix_cost: Fixed cost [CHF/h]
        :type fix_cost: float
        """
        self._check_id(ls, ExceptionKey.FIXCOST_SET)
        if ls not in self._fix_cost:
            self._fix_cost[ls] = TimeSeries()
            self._fix_cost[ls].def_value = DEF_FIXCOST
        self._fix_cost[ls].set_value(t, fix_cost)

    def set_fix_cost_def(self, ls: LoadShiftId, fix_cost_def: float) -> None:
        """
        Set the default (with respect to time) value for the parameter
        'fix_cost' which denotes fixed costs that arise per timestep when any
        amount of load shifting occurs at all. Be aware that whenever this
        parameter is set to a nonzero value, binary variables will be added to
        the MILP model for each time step. This will drastically increase the
        complexity and solving speed of the model, and should only be used for
        comparably small systems. This is an optional parameter with a default
        value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param fix_cost_def: Default fix cost [CHF/h]
        :type fix_cost_def: float
        """
        self._check_id(ls, ExceptionKey.FIXCOST_DEFSET)
        if ls not in self._fix_cost:
            self._fix_cost[ls] = TimeSeries()
        self._fix_cost[ls].def_value = fix_cost_def

    # ------------------------------- #
    # Secondary property: time_series #
    # ------------------------------- #
    @property
    def time_series(self) -> List[Tuple[TimeSeriesKind, StageId,
                                        Tuple[str, ...], TimeSeries]]:
        """
        Time series profiles in the load shifting module. This is a list of
        tuples. Each list element has the following list entries: 1)
        ProfileKind of the profile. 2) Stage. 3) Tuple of string identifiers
        specific to the ProfileKind. 3) The TimeSerie itself. This function
        does currently not work because no unique stage can be assigned to the
        load shifting index. This is the reason why clustering does not work
        if load shifting has time-dependent data.

        :return: All time series of the load shifting module
        :rtype: List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...],
            TimeSeries]]
        """
        all_series: List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...],
                               TimeSeries]] = []
        # # max_above_abs
        # for ls, series in self._max_above_abs.items():
        #     if series.has_values:
        #         all_series.append((TimeSeriesKind.LOADSHIFTMAXABOVEABS,
        #                            (ls.key,), series))
        # # max_above_rel
        # for ls, series in self._max_above_rel.items():
        #     if series.has_values:
        #         all_series.append((TimeSeriesKind.LOADSHIFTMAXABOVEREL,
        #                            (ls.key,), series))
        # # max_below_abs
        # for ls, series in self._max_below_abs.items():
        #     if series.has_values:
        #         all_series.append((TimeSeriesKind.LOADSHIFTMAXBELOWABS,
        #                            (ls.key,), series))
        # # max_below_rel
        # for ls, series in self._max_below_rel.items():
        #     if series.has_values:
        #         all_series.append((TimeSeriesKind.LOADSHIFTMAXBELOWREL,
        #                            (ls.key,), series))
        # # energy_cost_above
        # for ls, series in self._energy_cost_above.items():
        #     if series.has_values:
        #         all_series.append((TimeSeriesKind.LOADSHIFTENERGYCOSTABOVE,
        #                            (ls.key,), series))
        # # energy_cost_below
        # for ls, series in self._energy_cost_below.items():
        #     if series.has_values:
        #         all_series.append((TimeSeriesKind.LOADSHIFTENERGYCOSTBELOW,
        #                            (ls.key,), series))
        # # fix_cost
        # for ls, series in self._fix_cost.items():
        #     if series.has_values:
        #         all_series.append((TimeSeriesKind.LOADSHIFTFIXCOST,
        #                            (ls.key,), series))
        return all_series

    def set_time_series_val(self, kind: TimeSeriesKind, s: StageId,
                            ids: Tuple[str, ...], t: TimeId, value: float
                            ) -> None:
        """
        Set the value for a time series in the load shifting data class. The
        time series should be uniquely identified by the time series kind, the
        stage id and the remaining tuples. This function does currently not
        work because no unique stage can be assigned to the load shifting
        index. This is the reason why clustering does not work if load
        shifting has time-dependent data.

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

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._ids: Set[LoadShiftId] = set()
        self._stages: Dict[LoadShiftId, Set[StageId]] = {}
        self._hubs: Dict[LoadShiftId, Set[HubId]] = {}
        self._ecs: Dict[LoadShiftId, Set[EcId]] = {}
        self._interval_length: Dict[LoadShiftId, int] = {}
        self._interval_cap: Dict[LoadShiftId, float] = {}
        self._max_above_abs: Dict[LoadShiftId, TimeSeries] = {}
        self._max_above_rel: Dict[LoadShiftId, TimeSeries] = {}
        self._max_below_abs: Dict[LoadShiftId, TimeSeries] = {}
        self._max_below_rel: Dict[LoadShiftId, TimeSeries] = {}
        self._peak_cost_above: Dict[LoadShiftId, float] = {}
        self._peak_cost_below: Dict[LoadShiftId, float] = {}
        self._energy_cost_above: Dict[LoadShiftId, TimeSeries] = {}
        self._energy_cost_below: Dict[LoadShiftId, TimeSeries] = {}
        self._fix_cost: Dict[LoadShiftId, TimeSeries] = {}

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self, stages: Stages, hubs: Hubs, ecs: Ecs, demands: Demands,
                 times: Times) -> None:
        """
        Validate all load shifting data in this object. Apart from sense-
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
        self._validate_stage(stages)
        self._validate_hub(hubs)
        self._validate_ec(ecs)
        self._validate_tuples(demands)
        self._validate_interval_length(times)
        self._validate_interval_cap()
        self._validate_max_above_abs(times)
        self._validate_max_above_rel(times)
        self._validate_max_below_abs(times)
        self._validate_max_below_rel(times)
        self._validate_peak_cost_above()
        self._validate_peak_cost_below()
        self._validate_energy_cost_above(times)
        self._validate_energy_cost_below(times)
        self._validate_energy_cost_abovebelow_nonzero()
        self._validate_fix_cost(times)

    def _validate_stage(self, stages: Stages) -> None:
        for ls, stage_set in self._stages.items():
            for s in stage_set:
                if s not in stages.ids:
                    msg = f"Unknown stage {s} in stages[{ls}]"
                    raise exceptions.DataException(
                        ExceptionKey.STAGE_VAL.value, [s], msg,
                        module=LOG_MODULE_STR)

    def _validate_hub(self, hubs: Hubs) -> None:
        for ls, hub_set in self._hubs.items():
            for h in hub_set:
                if h not in hubs.ids:
                    msg = f"Unknown hub {h} in hubs[{ls}]"
                    raise exceptions.DataException(ExceptionKey.HUB_VAL.value,
                        [h], msg, module=LOG_MODULE_STR)

    def _validate_ec(self, ecs: Ecs) -> None:
        for ls, ec_set in self._ecs.items():
            for e in ec_set:
                if e not in ecs.ids:
                    msg = f"Unknown ec {e} in ecs[{ls}]"
                    raise exceptions.DataException(ExceptionKey.HUB_VAL.value,
                        [e], msg, module=LOG_MODULE_STR)

    def _validate_tuples(self, demands: Demands) -> None:
        for ls in self.ids:
            for (s, h, e) in self.get_tuples(ls):
                if (s, h, e) not in demands.tuples:
                    msg = (f"{ls} contains tuple ({s}, {h}, {e}) which is not "
                           "a demand tuple")
                    raise exceptions.DataException(
                        ExceptionKey.TUPLES_GET.value, [s, h, e], msg,
                        module=LOG_MODULE_STR)

    def _validate_interval_length(self, times: Times) -> None:
        for ls, interval_length in self._interval_length.items():
            if interval_length <= 0:
                msg = f"{interval_length} = interval_length[{ls}] <= 0"
                raise exceptions.DataException(
                    ExceptionKey.INTERVALLENGTH_VAL.value, [ls], msg,
                    module=LOG_MODULE_STR)
            if interval_length > times.num_horizon_ts:
                msg = (f"interval_length[{ls}] = {interval_length} but time "
                       f"horizon only has length {times.num_horizon_ts}")
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_interval_cap(self) -> None:
        for ls, interval_cap in self._interval_cap.items():
            if interval_cap < 0:
                msg = f"{interval_cap} = interval_cap[{ls}] < 0"
                raise exceptions.DataException(
                    ExceptionKey.INTERVALCAP_VAL.value, [ls], msg,
                    module=LOG_MODULE_STR)
            if interval_cap < EPS_ZEROCHECK:
                msg = f"{interval_cap} = interval_cap[{ls}] ~ 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_max_above_abs(self, times: Times) -> None:
        exc_key = ExceptionKey.MAXABOVEABS_VAL.value
        for ls, max_above_abs in self._max_above_abs.items():
            # Unknown time ids
            max_above_abs.validate(times, exc_key, module=LOG_MODULE_STR)
            # max_above_abs must be nonnegative (time values)
            if max_above_abs.has_values:
                for t in times.ids:
                    if max_above_abs.get_value(t) < 0:
                        msg = (f"{max_above_abs.get_value(t)} = max_above_abs"
                               f"[{ls}][{t}] < 0")
                        raise exceptions.DataException(exc_key, [ls, t],
                            msg, module=LOG_MODULE_STR)
            # max_above_abs must be nonnegative (default values)
            if not max_above_abs.has_values:
                max_above_abs_def = max_above_abs.def_value
                assert max_above_abs_def is not None
                if max_above_abs_def < 0:
                    msg = f"{max_above_abs_def} = max_above_abs[{ls}] < 0"
                    raise exceptions.DataException(exc_key, [ls],
                                                   msg, module=LOG_MODULE_STR)

    def _validate_max_above_rel(self, times: Times) -> None:
        exc_key = ExceptionKey.MAXABOVEREL_VAL.value
        for ls, max_above_rel in self._max_above_rel.items():
            # Unknown time ids
            max_above_rel.validate(times, exc_key, module=LOG_MODULE_STR)
            # max_above_rel must be nonnegative (time values)
            if max_above_rel.has_values:
                for t in times.ids:
                    if max_above_rel.get_value(t) < 0:
                        msg = (f"{max_above_rel.get_value(t)} = max_above_rel"
                               f"[{ls}][{t}] < 0")
                        raise exceptions.DataException(exc_key, [ls, t],
                            msg, module=LOG_MODULE_STR)
            # max_above_rel must be nonnegative (default values)
            if not max_above_rel.has_values:
                max_above_rel_def = max_above_rel.def_value
                assert max_above_rel_def is not None
                if max_above_rel_def < 0:
                    msg = f"{max_above_rel_def} = max_above_rel[{ls}] < 0"
                    raise exceptions.DataException(exc_key, [ls],
                                                   msg, module=LOG_MODULE_STR)

    def _validate_max_below_abs(self, times: Times) -> None:
        exc_key = ExceptionKey.MAXBELOWABS_VAL.value
        for ls, max_below_abs in self._max_below_abs.items():
            # Unknown time ids
            max_below_abs.validate(times, exc_key, module=LOG_MODULE_STR)
            # max_below_abs must be nonnegative (time values)
            if max_below_abs.has_values:
                for t in times.ids:
                    if max_below_abs.get_value(t) < 0:
                        msg = (f"{max_below_abs.get_value(t)} = max_below_abs"
                               f"[{ls}][{t}] < 0")
                        raise exceptions.DataException(exc_key, [ls, t],
                            msg, module=LOG_MODULE_STR)
            # max_below_abs must be nonnegative (default values)
            if not max_below_abs.has_values:
                max_below_abs_def = max_below_abs.def_value
                assert max_below_abs_def is not None
                if max_below_abs_def < 0:
                    msg = f"{max_below_abs_def} = max_below_abs[{ls}] < 0"
                    raise exceptions.DataException(exc_key, [ls],
                                                   msg, module=LOG_MODULE_STR)

    def _validate_max_below_rel(self, times: Times) -> None:
        # self.set_max_below_rel(LoadShiftId("ls1"), TimeId(2), 1.5)
        exc_key = ExceptionKey.MAXBELOWREL_VAL.value
        for ls, max_below_rel in self._max_below_rel.items():
            # Unknown time ids
            max_below_rel.validate(times, exc_key, module=LOG_MODULE_STR)
            # Time values
            if max_below_rel.has_values:
                # max_below_rel must be nonnegative (time values)
                for t in times.ids:
                    if max_below_rel.get_value(t) < 0:
                        msg = (f"{max_below_rel.get_value(t)} = max_below_rel"
                               f"[{ls}][{t}] < 0")
                        raise exceptions.DataException(exc_key, [ls, t],
                            msg, module=LOG_MODULE_STR)
                # max_below_rel usually not larger than one (time values)
                for t in times.ids:
                    if max_below_rel.get_value(t) > 1:
                        msg = (f"{max_below_rel.get_value(t)} = max_below_rel"
                               f"[{ls}][{t}] > 1")
                        logging.log_warning(msg, LOG_MODULE_STR)
                        break
            # Default values
            if not max_below_rel.has_values:
                # max_below_rel must be nonnegative (default values)
                max_below_rel_def = max_below_rel.def_value
                assert max_below_rel_def is not None
                if max_below_rel_def < 0:
                    msg = f"{max_below_rel_def} = max_below_rel[{ls}] < 0"
                    raise exceptions.DataException(exc_key, [ls],
                                                   msg, module=LOG_MODULE_STR)
                # max_below_rel usually not larger than one (default values)
                if max_below_rel_def > 1:
                    msg = f"{max_below_rel_def} = max_below_rel[{ls}] > 1"
                    logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_peak_cost_above(self) -> None:
        # peak_cost_above usually nonnegative
        for ls, peak_cost_above in self._peak_cost_above.items():
            if peak_cost_above < 0:
                msg = f"{peak_cost_above} = peak_cost_above[{ls}] < 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_peak_cost_below(self) -> None:
        # peak_cost_below usually nonnegative
        for ls, peak_cost_below in self._peak_cost_below.items():
            if peak_cost_below < 0:
                msg = f"{peak_cost_below} = peak_cost_below[{ls}] < 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_energy_cost_above(self, times: Times) -> None:
        # self.set_energy_cost_above(LoadShiftId("ls1"), TimeId(2), -1)
        exc_key = ExceptionKey.ENERGYCOSTABOVE_VAL.value
        for ls, energy_cost_above in self._energy_cost_above.items():
            # Unknown time ids
            energy_cost_above.validate(times, exc_key, module=LOG_MODULE_STR)
            # energy_cost_above usually nonnegative (time values)
            if energy_cost_above.has_values:
                for t in times.ids:
                    if energy_cost_above.get_value(t) < 0:
                        msg = (f"{energy_cost_above.get_value(t)} = "
                               f"energy_cost_above[{ls}][{t}] < 0")
                        logging.log_warning(msg, module=LOG_MODULE_STR)
                        break
            # energy_cost_above usually nonnegative (default values)
            if not energy_cost_above.has_values:
                energy_cost_above_def = energy_cost_above.def_value
                assert energy_cost_above_def is not None
                if energy_cost_above_def < 0:
                    msg = (f"{energy_cost_above_def} = "
                           f"energy_cost_above[{ls}] < 0")
                    logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_energy_cost_below(self, times: Times) -> None:
        exc_key = ExceptionKey.ENERGYCOSTBELOW_VAL.value
        for ls, energy_cost_below in self._energy_cost_below.items():
            # Unknown time ids
            energy_cost_below.validate(times, exc_key, module=LOG_MODULE_STR)
            # energy_cost_below usually nonnegative (time values)
            if energy_cost_below.has_values:
                for t in times.ids:
                    if energy_cost_below.get_value(t) < 0:
                        msg = (f"{energy_cost_below.get_value(t)} = "
                               f"energy_cost_below[{ls}][{t}] < 0")
                        logging.log_warning(msg, module=LOG_MODULE_STR)
                        break
            # energy_cost_below usually nonnegative (default values)
            if not energy_cost_below.has_values:
                energy_cost_below_def = energy_cost_below.def_value
                assert energy_cost_below_def is not None
                if energy_cost_below_def < 0:
                    msg = (f"{energy_cost_below_def} = "
                           f"energy_cost_below[{ls}] < 0")
                    logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_energy_cost_abovebelow_nonzero(self) -> None:
        for ls in self.ids:
            energy_cost_above = self.get_energy_cost_above(ls)
            energy_cost_below = self.get_energy_cost_below(ls)
            if (not energy_cost_above.has_values
                    and not energy_cost_below.has_values):
                energy_cost_above_def = energy_cost_above.def_value
                energy_cost_below_def = energy_cost_below.def_value
                assert energy_cost_above_def is not None
                assert energy_cost_below_def is not None
                if (abs(energy_cost_above_def) < EPS_ZEROCHECK
                        and abs(energy_cost_below_def) < EPS_ZEROCHECK):
                    msg = (f"{abs(energy_cost_above_def)} = "
                           f"|energy_cost_above[{ls}]| ~ 0 and "
                           f"{abs(energy_cost_below_def)} = "
                           f"|energy_cost_below[{ls}]| ~ 0. This might lead "
                           "to non-unique solutions in V_LoadShiftAbove and "
                           "V_LoadShiftBelow")
                    logging.log_file_warning(msg, module=LOG_MODULE_STR)

    def _validate_fix_cost(self, times: Times) -> None:
        exc_key = ExceptionKey.FIXCOST_VAL.value
        for ls, fix_cost in self._fix_cost.items():
            # Unknown time ids
            fix_cost.validate(times, exc_key, module=LOG_MODULE_STR)
            # fix_cost usually nonnegative (time values)
            if fix_cost.has_values:
                for t in times.ids:
                    if fix_cost.get_value(t) < 0:
                        msg = (f"{fix_cost.get_value(t)} = "
                               f"fix_cost[{ls}][{t}] < 0")
                        logging.log_warning(msg, module=LOG_MODULE_STR)
                        break
            # fix_cost usually nonnegative (default values)
            if not fix_cost.has_values:
                fix_cost_def = fix_cost.has_values
                assert fix_cost_def is not None
                if fix_cost_def < 0:
                    msg = f"{fix_cost_def} = fix_cost[{ls}] < 0"
                    logging.log_warning(msg, module=LOG_MODULE_STR)

    # ---------- #
    # Id checker #
    # ---------- #
    def _check_id(self, ls: LoadShiftId, where: ExceptionKey) -> None:
        if ls not in self._ids:
            raise exceptions.UnknownIdException(where.value, ls,
                                                module=LOG_MODULE_STR)
