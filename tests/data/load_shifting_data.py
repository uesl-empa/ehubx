"""
Load shifting data module
"""

import itertools
from enum import Enum
from typing import Dict, List, Set, Tuple

from ehubx.core import logging
from ehubx.core.common import EPS_ZEROCHECK, TimeSeriesKind
from ehubx.data import exceptions
from ehubx.data.demand_data import Demands
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.index import Index, IndexKind
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.time_data import TimeId, Times
from ehubx.data.time_series import TimeSeries
from ehubx.data.unit import CurrencyUnit, DimlessUnit, TimeUnit, Unit
from ehubx.data.value import Value


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
    EC_GET = "getting 'ec' from LoadShifting"
    EC_SET = "setting 'ec' of LoadShifting"
    EC_VAL = "validating 'ec' of LoadShifting"
    TUPLES_GET = "getting 'tuples' from LoadShifting"
    TUPLES_VAL = "validating 'tuples' from LoadShifting"
    INTERVALLENGTH_SET = "setting 'interval_length' of LoadShifting"
    INTERVALLENGTH_GET = "getting 'interval_length' from LoadShifting"
    INTERVALLENGTH_VAL = "validating 'interval_length' of LoadShifting"
    CAPEXPERCAP_SET = "setting 'capex_per_cap' of LoadShifting"
    CAPEXPERCAP_GET = "getting 'capex_per_cap' from LoadShifting"
    CAPEXPERCAP_VAL = "validating 'capex_per_cap' of LoadShifting"
    CAPMIN_SET = "setting 'cap_min' of LoadShifting"
    CAPMIN_GET = "getting 'cap_min' from LoadShifting"
    CAPMIN_VAL = "validating 'cap_min' of LoadShifting"
    CAPMAX_SET = "setting 'cap_max' of LoadShifting"
    CAPMAX_GET = "getting 'cap_max' from LoadShifting"
    CAPMAX_VAL = "validating 'cap_max' of LoadShifting"
    CAPMINMAXINIT_VAL = "validating 'cap_min' against 'cap_max' of LoadShifting"
    CAPINIT_SET = "setting 'cap_init' of LoadShifting"
    CAPINIT_GET = "getting 'cap_init' from LoadShifting"
    CAPINIT_VAL = "validating 'cap_init' of LoadShifting"
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
    ENERGYCOSTABOVE_DEFSET = "setting default 'energy_cost_above' of " + "LoadShifting"
    ENERGYCOSTABOVE_GET = "getting 'energy_cost_above' from LoadShifting"
    ENERGYCOSTABOVE_VAL = "validating 'energy_cost_above' of LoadShifting"
    ENERGYCOSTBELOW_SET = "setting 'energy_cost_below' of LoadShifting"
    ENERGYCOSTBELOW_DEFSET = "setting default 'energy_cost_below' of " + "LoadShifting"
    ENERGYCOSTBELOW_GET = "getting 'energy_cost_below' from LoadShifting"
    ENERGYCOSTBELOW_VAL = "validating 'energy_cost_below' of LoadShifting"
    ENERGYCOSTABOVEBELOWNONZERO_VAL = (
        "valdating that not both 'energy_cost_above' and 'energy_cost_below' are zero"
    )
    FIXCOST_SET = "setting 'fix_cost' of LoadShifting"
    FIXCOST_DEFSET = "setting default 'fix_cost' of LoadShifting"
    FIXCOST_GET = "getting 'fix_cost' from LoadShifting"
    FIXCOST_VAL = "validating 'fix_cost' of LoadShifting"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/load_shift"
"""String identifying the load shifting data module for logging purposes"""

DEF_CAPEXPERCAP: float = 0
"""Default value for parameter 'capex_per_cap' in the load shifting data module"""

DEF_CAPMIN: float = 0
"""Default value for parameter 'cap_min' in the load shifting data module"""

DEF_CAPMAX: float = float("inf")
"""Default value for parameter 'cap_max' in the load shifting data module"""

DEF_CAPINIT: float = 0
"""Default value for parameter 'cap_init' in the load shifting data module"""

DEF_MAXABOVEABS: float = float("inf")
"""Default value for parameter 'max_above_abs' in the load shifting data module"""

DEF_MAXABOVEREL: float = float("inf")
"""Default value for parameter 'max_above_rel' in the load shifting data module"""

DEF_MAXBELOWABS: float = float("inf")
"""Default value for parameter 'max_below_abs' in the load shifting data module"""

DEF_MAXBELOWREL: float = 1
"""Default value for parameter 'max_below_rel' in the load shifting data module"""

DEF_PEAKCOSTABOVE: float = 0
"""Default value for parameter 'peak_cost_above' in the load shifting data module"""

DEF_PEAKCOSTBELOW: float = 0
"""Default value for parameter 'peak_cost_below' in the load shifting data module"""

DEF_ENERGYCOSTABOVE: float = 0
"""Default value for parameter 'energy_cost_above' in the load shifting data module"""

DEF_ENERGYCOSTBELOW: float = 0
"""Default value for parameter 'energy_cost_below' in the load shifting data module"""

DEF_FIXCOST: float = 0
"""Default value for parameter 'fix_cost' in the load shifting data module"""


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

    def add_id(self, ls: LoadShiftId, e: EcId, ec_unit: Unit) -> None:
        """
        Add a new load shifting id

        :param ls: Id to be added
        :type ls: LoadShiftTechId
        """
        if ls in self._ids:
            raise exceptions.DuplicateIdException(
                ExceptionKey.ID_ADD.value, ls, module=LOG_MODULE_STR
            )
        self._ids.add(ls)
        self._ec[ls] = e
        self._stages[ls] = set()
        self._hubs[ls] = set()
        self._max_above_abs[ls] = TimeSeries()
        self._max_above_rel[ls] = TimeSeries()
        self._energy_cost_above[ls] = TimeSeries()
        self._max_below_abs[ls] = TimeSeries()
        self._max_below_rel[ls] = TimeSeries()
        self._energy_cost_below[ls] = TimeSeries()
        self._fix_cost[ls] = TimeSeries()
        self._max_above_abs[ls].def_value = Value(
            DEF_MAXABOVEABS, unit=(ec_unit / TimeUnit.H)
        )
        self._max_above_rel[ls].def_value = Value(DEF_MAXABOVEREL, unit=DimlessUnit())
        self._energy_cost_above[ls].def_value = Value(
            DEF_ENERGYCOSTABOVE, unit=(CurrencyUnit.CHF / ec_unit)
        )
        self._max_below_abs[ls].def_value = Value(
            DEF_MAXBELOWABS, unit=(ec_unit / TimeUnit.H)
        )
        self._max_below_rel[ls].def_value = Value(DEF_MAXBELOWREL, unit=DimlessUnit())
        self._energy_cost_below[ls].def_value = Value(
            DEF_ENERGYCOSTBELOW, unit=(CurrencyUnit.CHF / ec_unit)
        )
        self._fix_cost[ls].def_value = Value(
            DEF_FIXCOST, unit=(CurrencyUnit.CHF / TimeUnit.H)
        )
        self._capex_per_cap[ls] = Value(
            DEF_CAPEXPERCAP, unit=(CurrencyUnit.CHF / ec_unit)
        )
        self._cap_min[ls] = Value(DEF_CAPMIN, unit=ec_unit)
        self._cap_max[ls] = Value(DEF_CAPMAX, unit=ec_unit)
        self._cap_init[ls] = Value(DEF_CAPINIT, unit=ec_unit)
        self._peak_cost_above[ls] = Value(
            DEF_PEAKCOSTABOVE, unit=(CurrencyUnit.CHF / (ec_unit / TimeUnit.H))
        )
        self._peak_cost_below[ls] = Value(
            DEF_PEAKCOSTBELOW, unit=(CurrencyUnit.CHF / (ec_unit / TimeUnit.H))
        )

    # ----------------------------- #
    # Properties: stages, sets, ecs #
    # ----------------------------- #
    def get_stage_hub_tuples(self, ls: LoadShiftId) -> Set[Tuple[StageId, HubId]]:
        """
        Get all tuples of (stage, hub) that are encompassed in a specific
        load shifting id

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :return: Set of (stage, hub) tuples
        :rtype: Set[Tuple[StageId, HubId]]
        """
        self._check_id(ls, ExceptionKey.TUPLES_GET)
        stages = self._stages.get(ls, set())
        hubs = self._hubs.get(ls, set())
        return set(itertools.product(stages, hubs))

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

    def get_ec(self, ls: LoadShiftId) -> EcId:
        """
        Get the ec for a load shifting index

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :return: Ec
        :rtype: EcId
        """
        self._check_id(ls, ExceptionKey.EC_GET)
        return self._ec[ls]

    # ------------------------- #
    # Property: interval_length #
    # ------------------------- #
    def get_interval_length(self, ls: LoadShiftId) -> Value:
        """
        Get the parameter 'interval_length' which denotes length (in
        time) of a shifting interval. This is a mandatory
        parameter.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :return: Length of load shifting interval
        :rtype: Value
        """
        self._check_id(ls, ExceptionKey.INTERVALLENGTH_GET)
        if ls not in self._interval_length:
            raise exceptions.MissingIdException(
                ExceptionKey.INTERVALLENGTH_GET.value, ls, module=LOG_MODULE_STR
            )
        return self._interval_length[ls]

    def set_interval_length(self, ls: LoadShiftId, interval_length: Value) -> None:
        """
        Set the parameter 'interval_length' which denotes length (in
        time) of a shifting interval. This is a mandatory
        parameter.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param interval_length: Length of load shifting inteval
        :type interval_length: Value
        """
        self._check_id(ls, ExceptionKey.INTERVALLENGTH_SET)
        if not interval_length.unit.same_type_as(TimeUnit.H):
            raise exceptions.DataException(
                ExceptionKey.INTERVALLENGTH_SET.value,
                [ls],
                "interval_length must be a time value, but has unit "
                f"'{interval_length.unit}'",
                module=LOG_MODULE_STR,
            )
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
        :return: Maximal absolute above-shifts
        :rtype: TimeSeries
        """
        self._check_id(ls, ExceptionKey.MAXABOVEABS_GET)
        return self._max_above_abs[ls]

    def set_max_above_abs(
        self, ls: LoadShiftId, t: TimeId, max_above_abs: Value
    ) -> None:
        """
        Set the parameter 'max_above_abs' at a specific time which denotes the
        maximal amount of load shifting that can occur above the demand curve.
        This is an optional parameter with a default value of infinity.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param t: Time
        :type t: TimeId
        :param max_above_abs: Maximal absolute above-shift
        :type max_above_abs: Value
        """
        self._check_id(ls, ExceptionKey.MAXABOVEABS_SET)
        self._max_above_abs[ls].set_value(t, max_above_abs)

    def set_max_above_abs_def(self, ls: LoadShiftId, max_above_abs_def: Value) -> None:
        """
        Set the default (with respect to time) value of the parameter
        'max_above_abs' at a specific time which denotes the maximal amount of
        load shifting that can occur above the demand curve. This is an
        optional parameter with a default value of infinity.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param max_above_abs_def: Default maximal absolute above-shift
        :type max_above_abs_def: Value
        """
        self._check_id(ls, ExceptionKey.MAXABOVEABS_DEFSET)
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
        :return: Maximal relative above-shifts
        :rtype: TimeSeries
        """
        self._check_id(ls, ExceptionKey.MAXABOVEREL_GET)
        return self._max_above_rel[ls]

    def set_max_above_rel(
        self, ls: LoadShiftId, t: TimeId, max_above_rel: Value
    ) -> None:
        """
        Set the parameter 'max_above_rel' at a specific time which denotes the
        maximal amount of load shifting that can occur above the demand curve,
        relative to the demand curve itself. This is an optional parameter with
        a default value of infinity.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param t: Time
        :type t: TimeId
        :param max_above_rel: Maximal relative above-shift
        :type max_above_rel: Value
        """
        self._check_id(ls, ExceptionKey.MAXABOVEREL_SET)
        expected_unit = DimlessUnit()
        if not max_above_rel.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.MAXBELOWREL_SET.value,
                [ls, t],
                f"Unit {max_above_rel.unit} of max_above_rel[{ls}][{t}] "
                f"does not match expected unit '{expected_unit}'",
                module=LOG_MODULE_STR,
            )
        self._max_above_rel[ls].set_value(t, max_above_rel)

    def set_max_above_rel_def(self, ls: LoadShiftId, max_above_rel_def: Value) -> None:
        """
        Set a default (with respect to time) for the parameter 'max_above_rel'
        at a specific time which denotes the maximal amount of load shifting
        that can occur above the demand curve, relative to the demand curve
        itself. This is an optional parameter with a default value of infinity.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param max_above_rel_def: Default maximal relative above-shift
        :type max_above_rel_def: Value
        """
        self._check_id(ls, ExceptionKey.MAXABOVEREL_DEFSET)
        expected_unit = DimlessUnit()
        if not max_above_rel_def.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.MAXBELOWREL_SET.value,
                [ls],
                f"Unit {max_above_rel_def.unit} of max_above_rel[{ls}] "
                f"does not match expected unit '{expected_unit}'",
                module=LOG_MODULE_STR,
            )
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
        :return: Maximal absolute below-shifts
        :rtype: TimeSeries
        """
        self._check_id(ls, ExceptionKey.MAXBELOWABS_GET)
        return self._max_below_abs[ls]

    def set_max_below_abs(
        self, ls: LoadShiftId, t: TimeId, max_below_abs: Value
    ) -> None:
        """
        Set the parameter 'max_below_abs' at a specific time which denotes the
        maximal amount of load shifting that can occur below the demand curve.
        This is an optional parameter with a default value of infinity.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param t: Time
        :type t: TimeId
        :param max_below_abs: Maximal absolute below-shift
        :type max_below_abs: Value
        """
        self._check_id(ls, ExceptionKey.MAXBELOWABS_SET)
        self._max_below_abs[ls].set_value(t, max_below_abs)

    def set_max_below_abs_def(self, ls: LoadShiftId, max_below_abs_def: Value) -> None:
        """
        Set the default (with respect to time) value of the parameter
        'max_below_abs' at a specific time which denotes the maximal amount of
        load shifting that can occur below the demand curve. This is an
        optional parameter with a default value of infinity.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param max_below_abs_def: Default maximal absolute below-shift
        :type max_below_abs_def: Value
        """
        self._check_id(ls, ExceptionKey.MAXBELOWABS_DEFSET)
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
        :return: Maximal relative below-shifts
        :rtype: TimeSeries
        """
        self._check_id(ls, ExceptionKey.MAXBELOWREL_GET)
        return self._max_below_rel[ls]

    def set_max_below_rel(
        self, ls: LoadShiftId, t: TimeId, max_below_rel: Value
    ) -> None:
        """
        Set the parameter 'max_below_rel' at a specific time which denotes the
        maximal amount of load shifting that can occur below the demand curve,
        relative to the demand curve itself. This is an optional parameter with
        a default value of 1.


        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param t: Time
        :type t: TimeId
        :param max_below_rel: Maximal relative below-shift
        :type max_below_rel: Value
        """
        self._check_id(ls, ExceptionKey.MAXBELOWREL_SET)
        expected_unit = DimlessUnit()
        if not max_below_rel.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.MAXBELOWREL_SET.value,
                [ls, t],
                f"Unit {max_below_rel.unit} of max_below_rel[{ls}][{t}] "
                f"does not match expected unit '{expected_unit}'",
                module=LOG_MODULE_STR,
            )
        self._max_below_rel[ls].set_value(t, max_below_rel)

    def set_max_below_rel_def(self, ls: LoadShiftId, max_below_rel_def: Value) -> None:
        """
        Set a default (with respect to time) for the parameter 'max_below_rel'
        at a specific time which denotes the maximal amount of load shifting
        that can occur below the demand curve, relative to the demand curve
        itself. This is an optional parameter with a default value of 1.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param max_below_rel_def: Default maximal relative below-shift
        :type max_below_rel_def: Value
        """
        self._check_id(ls, ExceptionKey.MAXBELOWREL_DEFSET)
        expected_unit = DimlessUnit()
        if not max_below_rel_def.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.MAXBELOWREL_SET.value,
                [ls],
                f"Unit {max_below_rel_def.unit} of max_below_rel[{ls}] "
                f"does not match expected unit '{expected_unit}'",
                module=LOG_MODULE_STR,
            )
        self._max_below_rel[ls].def_value = max_below_rel_def

    # ----------------------- #
    # Property: capex_per_cap #
    # ----------------------- #
    def get_capex_per_cap(self, ls: LoadShiftId) -> Value:
        """
        Get the parameter 'capex_per_cap' which denotes the amount of CAPEX cost for
        the installation  of one unit of capacity used for load shifting. This is an
        optional parameter with a default value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :return: CAPEX cost per unit of load shifting capacity
        :rtype: Value
        """
        self._check_id(ls, ExceptionKey.CAPEXPERCAP_GET)
        return self._capex_per_cap[ls]

    def set_capex_per_cap(self, ls: LoadShiftId, capex_per_cap: Value) -> None:
        """
        Set the parameter 'capex_per_cap' which denotes the amount of CAPEX cost for
        the installation  of one unit of capacity used for load shifting. This is an
        optional parameter with a default value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param capex_per_cap: CAPEX cost per unit of load shifting capacity
        :type capex_per_cap: Value
        """
        self._check_id(ls, ExceptionKey.CAPEXPERCAP_SET)
        self._capex_per_cap[ls] = capex_per_cap

    # ----------------- #
    # Property: cap_min #
    # ----------------- #
    def get_cap_min(self, ls: LoadShiftId) -> Value:
        """
        Get the parameter 'cap_min' which denotes the minimum amount of installed
        load shifting capacity, i.e.; the amount of energy that can be used for
        load shifting purposes in above or below direction on each load shift
        interval. This is an optional parameter with a default value of 0.
        """
        self._check_id(ls, ExceptionKey.CAPMIN_GET)
        return self._cap_min[ls]

    def set_cap_min(self, ls: LoadShiftId, cap_min: Value) -> None:
        """
        Set the parameter 'cap_min' which denotes the minimum amount of installed
        load shifting capacity, i.e.; the amount of energy that can be used for
        load shifting purposes in above or below direction on each load shift
        interval. This is an optional parameter with a default value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param cap_min: Minimum load shifting capacity
        :type cap_min: Value
        """
        self._check_id(ls, ExceptionKey.CAPMIN_SET)
        self._cap_min[ls] = cap_min

    # ----------------- #
    # Property: cap_max #
    # ----------------- #
    def get_cap_max(self, ls: LoadShiftId) -> Value:
        """
        Get the parameter 'cap_max' which denotes the maximum amount of installed
        load shifting capacity, i.e.; the amount of energy that can be used for
        load shifting purposes in above or below direction on each load shift
        interval. This is an optional parameter with a default value of infinity.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :return: Maximum load shifting capacity
        :rtype: Value
        """
        self._check_id(ls, ExceptionKey.CAPMAX_GET)
        return self._cap_max[ls]

    def set_cap_max(self, ls: LoadShiftId, cap_max: Value) -> None:
        """
        Set the parameter 'cap_max' which denotes the maximum amount of installed
        load shifting capacity, i.e.; the amount of energy that can be used for
        load shifting purposes in above or below direction on each load shift
        interval. This is an optional parameter with a default value of infinity.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param cap_max: Maximum load shifting capacity
        :type cap_max: Value
        """
        self._check_id(ls, ExceptionKey.CAPMAX_SET)
        self._cap_max[ls] = cap_max

    # ------------------ #
    # Property: cap_init #
    # ------------------ #
    def get_cap_init(self, ls: LoadShiftId) -> Value:
        """
        Get the parameter 'cap_init' which denotes the initial amount of installed
        load shifting capacity, i.e.; the amount of energy that can be used for
        load shifting purposes in above or below direction on the first load shift
        interval. This is an optional parameter with a default value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :return: Initial load shifting capacity
        :rtype: Value
        """
        self._check_id(ls, ExceptionKey.CAPINIT_GET)
        return self._cap_init[ls]

    def set_cap_init(self, ls: LoadShiftId, cap_init: Value) -> None:
        """
        Set the parameter 'cap_init' which denotes the initial amount of installed
        load shifting capacity, i.e.; the amount of energy that can be used for
        load shifting purposes in above or below direction on the first load shift
        interval. This is an optional parameter with a default value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param cap_init: Initial load shifting capacity
        :type cap_init: Value
        """
        self._check_id(ls, ExceptionKey.CAPINIT_SET)
        self._cap_init[ls] = cap_init

    # ------------------------- #
    # Property: peak_cost_above #
    # ------------------------- #
    def get_peak_cost_above(self, ls: LoadShiftId) -> Value:
        """
        Get the parameter 'peak_cost_above' which denotes the cost for the
        largest amount of above-shifts on the entire time horizon.
        This is an optional parameter with a default value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :return: Peak cost above the demand curve
        :rtype: Value
        """
        self._check_id(ls, ExceptionKey.PEAKCOSTABOVE_GET)
        return self._peak_cost_above[ls]

    def set_peak_cost_above(self, ls: LoadShiftId, peak_cost_above: Value) -> None:
        """
        Set the parameter 'peak_cost_above' which denotes the cost for the
        largest amount of above-shifts on the entire time horizon.
        This is an optional parameter with a default value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param peak_cost_above: Peak cost above the demand curve
        :type peak_cost_above: Value
        """
        self._check_id(ls, ExceptionKey.PEAKCOSTABOVE_SET)
        self._peak_cost_above[ls] = peak_cost_above

    # ------------------------- #
    # Property: peak_cost_below #
    # ------------------------- #
    def get_peak_cost_below(self, ls: LoadShiftId) -> Value:
        """
        Get the parameter 'peak_cost_below' which denotes the cost for the
        largest amount of below-shifts on the entire time horizon.
        This is an optional parameter with a default value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :return: Peak cost below the demand curve
        :rtype: Value
        """
        self._check_id(ls, ExceptionKey.PEAKCOSTBELOW_GET)
        return self._peak_cost_below[ls]

    def set_peak_cost_below(self, ls: LoadShiftId, peak_cost_below: Value) -> None:
        """
        Set the parameter 'peak_cost_below' which denotes the cost for the
        largest amount of below-shifts on the entire time horizon.
        This is an optional parameter with a default value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param peak_cost_below: Peak cost below the demand curve
        :type peak_cost_below: Value
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
        :return: Energy costs above the demand curve
        :rtype: TimeSeries
        """
        self._check_id(ls, ExceptionKey.ENERGYCOSTABOVE_GET)
        return self._energy_cost_above[ls]

    def set_energy_cost_above(
        self, ls: LoadShiftId, t: TimeId, energy_cost_above: Value
    ) -> None:
        """
        At a specific time, set the parameter 'energy_cost_above' which denotes
        the penalization cost for each energy unit of above-shifting. This is
        an optional parameter with a default value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param t: Time
        :type t: TimeId
        :param energy_cost_above: Energy cost above the demand curve
        :type energy_cost_above: Value
        """
        self._check_id(ls, ExceptionKey.ENERGYCOSTABOVE_SET)
        self._energy_cost_above[ls].set_value(t, energy_cost_above)

    def set_energy_cost_above_def(
        self, ls: LoadShiftId, energy_cost_above_def: Value
    ) -> None:
        """
        Set the default (with respect to time) value of the parameter
        'energy_cost_above' which denotes the penalization cost for each energy
        unit of above-shifting. This is an optional parameter with a default
        value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param energy_cost_above_def: Default energy cost above the demand curve
        :type energy_cost_above_def: Value
        """
        self._check_id(ls, ExceptionKey.ENERGYCOSTABOVE_DEFSET)
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
        :return: Energy costs below the demand curve
        :rtype: TimeSeries
        """
        self._check_id(ls, ExceptionKey.ENERGYCOSTBELOW_GET)
        return self._energy_cost_below[ls]

    def set_energy_cost_below(
        self, ls: LoadShiftId, t: TimeId, energy_cost_below: Value
    ) -> None:
        """
        At a specific time, set the parameter 'energy_cost_below' which denotes
        the penalization cost for each energy unit of below-shifting. This is
        an optional parameter with a default value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param t: Time
        :type t: TimeId
        :param energy_cost_below: Energy cost below the demand curve
        :type energy_cost_below: Value
        """
        self._check_id(ls, ExceptionKey.ENERGYCOSTBELOW_SET)
        self._energy_cost_below[ls].set_value(t, energy_cost_below)

    def set_energy_cost_below_def(
        self, ls: LoadShiftId, energy_cost_below_def: Value
    ) -> None:
        """
        Set the default (with respect to time) value of the parameter
        'energy_cost_below' which denotes the penalization cost for each energy
        unit of below-shifting. This is an optional parameter with a default
        value of 0.

        :param ls: Load shifting id
        :type ls: LoadShiftId
        :param energy_cost_below_def: Default energy cost below the demand curve
        :type energy_cost_below_def: Value
        """
        self._check_id(ls, ExceptionKey.ENERGYCOSTBELOW_DEFSET)
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
        :return: Fixed costs
        :rtype: TimeSeries
        """
        self._check_id(ls, ExceptionKey.FIXCOST_GET)
        return self._fix_cost[ls]

    def set_fix_cost(self, ls: LoadShiftId, t: TimeId, fix_cost: Value) -> None:
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
        :param fix_cost: Fixed cost
        :type fix_cost: float
        """
        self._check_id(ls, ExceptionKey.FIXCOST_SET)
        expected_unit = CurrencyUnit.CHF / TimeUnit.H
        if not fix_cost.unit.same_type_as(expected_unit):
            f"Unit {fix_cost.unit} of fix_cost[{ls}] "
            f"does not match expected unit '{expected_unit}'"
        self._fix_cost[ls].set_value(t, fix_cost)

    def set_fix_cost_def(self, ls: LoadShiftId, fix_cost_def: Value) -> None:
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
        :param fix_cost_def: Default fix cost
        :type fix_cost_def: Value
        """
        self._check_id(ls, ExceptionKey.FIXCOST_DEFSET)
        expected_unit = CurrencyUnit.CHF / TimeUnit.H
        if not fix_cost_def.unit.same_type_as(expected_unit):
            f"Unit {fix_cost_def.unit} of default value for fix_cost[{ls}] "
            f"does not match expected unit '{expected_unit}'"
        self._fix_cost[ls].def_value = fix_cost_def

    # ------------------------------- #
    # Secondary property: time_series #
    # ------------------------------- #
    @property
    def time_series(
        self,
    ) -> List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...], TimeSeries]]:
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
        all_series: List[
            Tuple[TimeSeriesKind, StageId, Tuple[str, ...], TimeSeries]
        ] = []
        # max_above_abs
        for ls, series in self._max_above_abs.items():
            if series.has_values:
                e = self._ec[ls]
                for s in self._stages[ls]:
                    for h in self._hubs[ls]:
                        all_series.append(
                            (
                                TimeSeriesKind.LOADSHIFTMAXABOVEABS,
                                s,
                                (h.key, e.key, ls.key),
                                series,
                            )
                        )
        # max_above_rel
        for ls, series in self._max_above_rel.items():
            if series.has_values:
                e = self._ec[ls]
                for s in self._stages[ls]:
                    for h in self._hubs[ls]:
                        all_series.append(
                            (
                                TimeSeriesKind.LOADSHIFTMAXABOVEREL,
                                s,
                                (h.key, e.key, ls.key),
                                series,
                            )
                        )
        # max_below_abs
        for ls, series in self._max_below_abs.items():
            if series.has_values:
                e = self._ec[ls]
                for s in self._stages[ls]:
                    for h in self._hubs[ls]:
                        all_series.append(
                            (
                                TimeSeriesKind.LOADSHIFTMAXBELOWABS,
                                s,
                                (h.key, e.key, ls.key),
                                series,
                            )
                        )
        # max_below_rel
        for ls, series in self._max_below_rel.items():
            if series.has_values:
                e = self._ec[ls]
                for s in self._stages[ls]:
                    for h in self._hubs[ls]:
                        all_series.append(
                            (
                                TimeSeriesKind.LOADSHIFTMAXBELOWREL,
                                s,
                                (h.key, e.key, ls.key),
                                series,
                            )
                        )
        # energy_cost_above
        for ls, series in self._energy_cost_above.items():
            if series.has_values:
                e = self._ec[ls]
                for s in self._stages[ls]:
                    for h in self._hubs[ls]:
                        all_series.append(
                            (
                                TimeSeriesKind.LOADSHIFTENERGYCOSTABOVE,
                                s,
                                (h.key, e.key, ls.key),
                                series,
                            )
                        )
        # energy_cost_below
        for ls, series in self._energy_cost_below.items():
            if series.has_values:
                e = self._ec[ls]
                for s in self._stages[ls]:
                    for h in self._hubs[ls]:
                        all_series.append(
                            (
                                TimeSeriesKind.LOADSHIFTENERGYCOSTBELOW,
                                s,
                                (h.key, e.key, ls.key),
                                series,
                            )
                        )
        # fix_cost
        for ls, series in self._fix_cost.items():
            if series.has_values:
                e = self._ec[ls]
                for s in self._stages[ls]:
                    for h in self._hubs[ls]:
                        all_series.append(
                            (
                                TimeSeriesKind.LOADSHIFTFIXCOST,
                                s,
                                (h.key, e.key, ls.key),
                                series,
                            )
                        )
        return all_series

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._ids: Set[LoadShiftId] = set()
        self._stages: Dict[LoadShiftId, Set[StageId]] = {}
        self._hubs: Dict[LoadShiftId, Set[HubId]] = {}
        self._ec: Dict[LoadShiftId, EcId] = {}
        self._interval_length: Dict[LoadShiftId, Value] = {}
        self._capex_per_cap: Dict[LoadShiftId, Value] = {}
        self._cap_min: Dict[LoadShiftId, Value] = {}
        self._cap_max: Dict[LoadShiftId, Value] = {}
        self._cap_init: Dict[LoadShiftId, Value] = {}
        self._max_above_abs: Dict[LoadShiftId, TimeSeries] = {}
        self._max_above_rel: Dict[LoadShiftId, TimeSeries] = {}
        self._max_below_abs: Dict[LoadShiftId, TimeSeries] = {}
        self._max_below_rel: Dict[LoadShiftId, TimeSeries] = {}
        self._peak_cost_above: Dict[LoadShiftId, Value] = {}
        self._peak_cost_below: Dict[LoadShiftId, Value] = {}
        self._energy_cost_above: Dict[LoadShiftId, TimeSeries] = {}
        self._energy_cost_below: Dict[LoadShiftId, TimeSeries] = {}
        self._fix_cost: Dict[LoadShiftId, TimeSeries] = {}

    # ---------- #
    # Validation #
    # ---------- #
    def validate(
        self, stages: Stages, hubs: Hubs, ecs: Ecs, demands: Demands, times: Times
    ) -> None:
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
        self._validate_capex_per_cap(ecs)
        self._validate_cap_min(ecs)
        self._validate_cap_max(ecs)
        self._validate_cap_init(ecs)
        self._validate_max_above_abs(ecs, times)
        self._validate_max_above_rel(times)
        self._validate_max_below_abs(ecs, times)
        self._validate_max_below_rel(times)
        self._validate_peak_cost_above(ecs)
        self._validate_peak_cost_below(ecs)
        self._validate_energy_cost_above(ecs, times)
        self._validate_energy_cost_below(ecs, times)
        self._validate_energy_cost_abovebelow_nonzero()
        self._validate_fix_cost(times)

    def _validate_stage(self, stages: Stages) -> None:
        for ls, stage_set in self._stages.items():
            for s in stage_set:
                if s not in stages.ids:
                    msg = f"Unknown stage {s} in stages[{ls}]"
                    raise exceptions.DataException(
                        ExceptionKey.STAGE_VAL.value, [s], msg, module=LOG_MODULE_STR
                    )

    def _validate_hub(self, hubs: Hubs) -> None:
        for ls, hub_set in self._hubs.items():
            for h in hub_set:
                if h not in hubs.ids:
                    msg = f"Unknown hub {h} in hubs[{ls}]"
                    raise exceptions.DataException(
                        ExceptionKey.HUB_VAL.value, [h], msg, module=LOG_MODULE_STR
                    )

    def _validate_ec(self, ecs: Ecs) -> None:
        for ls, e in self._ec.items():
            if e not in ecs.ids:
                msg = f"Unknown ec {e} = ecs[{ls}]"
                raise exceptions.DataException(
                    ExceptionKey.EC_VAL.value, [e], msg, module=LOG_MODULE_STR
                )

    def _validate_tuples(self, demands: Demands) -> None:
        for ls in self.ids:
            e = self._ec[ls]
            for s, h in self.get_stage_hub_tuples(ls):
                if (s, h, e) not in demands.profile_tuples:
                    msg = (
                        f"{ls} contains tuple ({s}, {h}, {e}) which is not "
                        "a demand profile tuple"
                    )
                    raise exceptions.DataException(
                        ExceptionKey.TUPLES_GET.value,
                        [s, h, e],
                        msg,
                        module=LOG_MODULE_STR,
                    )

    def _validate_interval_length(self, times: Times) -> None:
        for ls, interval_length in self._interval_length.items():
            if interval_length <= Value(0, TimeUnit.H):
                msg = f"{interval_length} = interval_length[{ls}] <= 0"
                raise exceptions.DataException(
                    ExceptionKey.INTERVALLENGTH_VAL.value,
                    [ls],
                    msg,
                    module=LOG_MODULE_STR,
                )
            if interval_length > Value(times.num_horizon_ts, TimeUnit.H):
                msg = (
                    f"interval_length[{ls}] = {interval_length} but time "
                    f"horizon only has length {Value(times.num_horizon_ts, TimeUnit.H)}"
                )
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_capex_per_cap(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.CAPEXPERCAP_VAL.value
        for ls, capex_per_cap in self._capex_per_cap.items():
            expected_unit = CurrencyUnit.CHF / ecs.get_unit(self._ec[ls])
            # Wrong unit
            if not capex_per_cap.unit.same_type_as(expected_unit):
                msg = (
                    f"Unit {capex_per_cap.unit} of capex_per_cap[{ls}] "
                    f"does not match expected unit {expected_unit}"
                )
                raise exceptions.DataException(
                    exc_key, [ls], msg, module=LOG_MODULE_STR
                )
            # capex_per_cap usually nonnegative
            if capex_per_cap.is_negative:
                logging.log_warning(
                    f"{capex_per_cap} = capex_per_cap[{ls}] < 0", module=LOG_MODULE_STR
                )

    def _validate_cap_min(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.CAPMIN_VAL.value
        for ls, cap_min in self._cap_min.items():
            # Wrong unit
            expected_unit = ecs.get_unit(self._ec[ls])
            if not cap_min.unit.same_type_as(expected_unit):
                msg = (
                    f"Unit {cap_min.unit} of cap_min[{ls}] "
                    f"does not match expected unit {expected_unit}"
                )
                raise exceptions.DataException(
                    exc_key, [ls], msg, module=LOG_MODULE_STR
                )
            # cap_min usually nonnegative
            if cap_min.is_negative:
                msg = f"{cap_min} = cap_min[{ls}] < 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_cap_max(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.CAPMAX_VAL.value
        for ls, cap_max in self._cap_max.items():
            # Wrong unit
            expected_unit = ecs.get_unit(self._ec[ls])
            if not cap_max.unit.same_type_as(expected_unit):
                msg = (
                    f"Unit {cap_max.unit} of cap_max[{ls}] "
                    f"does not match expected unit {expected_unit}"
                )
                raise exceptions.DataException(
                    exc_key, [ls], msg, module=LOG_MODULE_STR
                )
            # cap_max must be nonnegative
            if cap_max.is_negative:
                msg = f"{cap_max} = cap_max[{ls}] < 0"
                raise exceptions.DataException(
                    exc_key, [ls], msg, module=LOG_MODULE_STR
                )

    def _validate_cap_init(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.CAPINIT_VAL.value
        for ls, cap_init in self._cap_init.items():
            # Wrong unit
            expected_unit = ecs.get_unit(self._ec[ls])
            if not cap_init.unit.same_type_as(expected_unit):
                msg = (
                    f"Unit {cap_init.unit} of cap_init[{ls}] "
                    f"does not match expected unit {expected_unit}"
                )
                raise exceptions.DataException(
                    exc_key, [ls], msg, module=LOG_MODULE_STR
                )
            # cap_init must be nonnegative
            if cap_init.is_negative:
                msg = f"{cap_init} = cap_init[{ls}] < 0"
                raise exceptions.DataException(
                    exc_key, [ls], msg, module=LOG_MODULE_STR
                )

    def _validate_cap_minmaxinit(self) -> None:
        all_keys = set(self._cap_min.keys()).union(set(self._cap_max.keys()))
        for ls in all_keys:
            cap_min = self.get_cap_min(ls)
            cap_max = self.get_cap_max(ls)
            cap_init = self.get_cap_init(ls)
            # cap_min must not be larger than cap_max
            if cap_min > cap_max:
                msg = f"{cap_min} = cap_min[{ls}] > cap_max[{ls}] = {cap_max}"
                raise exceptions.DataException(
                    ExceptionKey.CAPMINMAXINIT_VAL.value,
                    [ls],
                    msg,
                    module=LOG_MODULE_STR,
                )
            # cap_init must not be smaller than cap_min
            if cap_init < cap_min:
                msg = f"{cap_init} = cap_init[{ls}] < cap_min[{ls}] = {cap_min}"
                raise exceptions.DataException(
                    ExceptionKey.CAPMINMAXINIT_VAL.value,
                    [ls],
                    msg,
                    module=LOG_MODULE_STR,
                )
            # cap_init must not be larger than cap_max
            if cap_init > cap_max:
                msg = f"{cap_init} = cap_init[{ls}] > cap_max[{ls}] = {cap_max}"
                raise exceptions.DataException(
                    ExceptionKey.CAPMINMAXINIT_VAL.value,
                    [ls],
                    msg,
                    module=LOG_MODULE_STR,
                )

    def _validate_max_above_abs(self, ecs: Ecs, times: Times) -> None:
        exc_key = ExceptionKey.MAXABOVEABS_VAL.value
        for ls, max_above_abs in self._max_above_abs.items():
            # Unit
            expected_unit = ecs.get_unit(self._ec[ls]) / TimeUnit.H
            assert max_above_abs.unit is not None
            if not max_above_abs.unit.same_type_as(expected_unit):
                msg = (
                    f"Unit {max_above_abs.unit} of max_above_abs[{ls}] "
                    f"does not match expected unit {expected_unit}"
                )
                raise exceptions.DataException(
                    exc_key, [ls], msg, module=LOG_MODULE_STR
                )
            # Unknown time ids
            max_above_abs.validate(times, exc_key, module=LOG_MODULE_STR)
            # max_above_abs must be nonnegative (time values)
            if max_above_abs.has_values:
                for t in times.ids:
                    if max_above_abs.get_value(t).is_negative:
                        msg = (
                            f"{max_above_abs.get_value(t)} = max_above_abs"
                            f"[{ls}][{t}] < 0"
                        )
                        raise exceptions.DataException(
                            exc_key, [ls, t], msg, module=LOG_MODULE_STR
                        )
            # max_above_abs must be nonnegative (default values)
            if not max_above_abs.has_values:
                max_above_abs_def = max_above_abs.def_value
                assert max_above_abs_def is not None
                if max_above_abs_def.is_negative:
                    msg = f"{max_above_abs_def} = max_above_abs[{ls}] < 0"
                    raise exceptions.DataException(
                        exc_key, [ls], msg, module=LOG_MODULE_STR
                    )

    def _validate_max_above_rel(self, times: Times) -> None:
        exc_key = ExceptionKey.MAXABOVEREL_VAL.value
        for ls, max_above_rel in self._max_above_rel.items():
            # Unknown time ids
            max_above_rel.validate(times, exc_key, module=LOG_MODULE_STR)
            # max_above_rel must be nonnegative (time values)
            if max_above_rel.has_values:
                for t in times.ids:
                    if max_above_rel.get_value(t).is_negative:
                        msg = (
                            f"{max_above_rel.get_value(t)} = max_above_rel"
                            f"[{ls}][{t}] < 0"
                        )
                        raise exceptions.DataException(
                            exc_key, [ls, t], msg, module=LOG_MODULE_STR
                        )
            # max_above_rel must be nonnegative (default values)
            if not max_above_rel.has_values:
                max_above_rel_def = max_above_rel.def_value
                assert max_above_rel_def is not None
                if max_above_rel_def.is_negative:
                    msg = f"{max_above_rel_def} = max_above_rel[{ls}] < 0"
                    raise exceptions.DataException(
                        exc_key, [ls], msg, module=LOG_MODULE_STR
                    )

    def _validate_max_below_abs(self, ecs: Ecs, times: Times) -> None:
        exc_key = ExceptionKey.MAXBELOWABS_VAL.value
        for ls, max_below_abs in self._max_below_abs.items():
            # Unit
            expected_unit = ecs.get_unit(self._ec[ls]) / TimeUnit.H
            assert max_below_abs.unit is not None
            if not max_below_abs.unit.same_type_as(expected_unit):
                msg = (
                    f"Unit {max_below_abs.unit} of max_below_abs[{ls}] "
                    f"does not match expected unit {expected_unit}"
                )
                raise exceptions.DataException(
                    exc_key, [ls], msg, module=LOG_MODULE_STR
                )
            # Unknown time ids
            max_below_abs.validate(times, exc_key, module=LOG_MODULE_STR)
            # max_below_abs must be nonnegative (time values)
            if max_below_abs.has_values:
                for t in times.ids:
                    if max_below_abs.get_value(t).is_negative:
                        msg = (
                            f"{max_below_abs.get_value(t)} = max_below_abs"
                            f"[{ls}][{t}] < 0"
                        )
                        raise exceptions.DataException(
                            exc_key, [ls, t], msg, module=LOG_MODULE_STR
                        )
            # max_below_abs must be nonnegative (default values)
            if not max_below_abs.has_values:
                max_below_abs_def = max_below_abs.def_value
                assert max_below_abs_def is not None
                if max_below_abs_def.is_negative:
                    msg = f"{max_below_abs_def} = max_below_abs[{ls}] < 0"
                    raise exceptions.DataException(
                        exc_key, [ls], msg, module=LOG_MODULE_STR
                    )

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
                    if max_below_rel.get_value(t).is_negative:
                        msg = (
                            f"{max_below_rel.get_value(t)} = max_below_rel"
                            f"[{ls}][{t}] < 0"
                        )
                        raise exceptions.DataException(
                            exc_key, [ls, t], msg, module=LOG_MODULE_STR
                        )
                # max_below_rel usually not larger than one (time values)
                for t in times.ids:
                    if max_below_rel.get_value(t) > Value(1):
                        msg = (
                            f"{max_below_rel.get_value(t)} = max_below_rel"
                            f"[{ls}][{t}] > 1"
                        )
                        logging.log_warning(msg, LOG_MODULE_STR)
                        break
            # Default values
            if not max_below_rel.has_values:
                # max_below_rel must be nonnegative (default values)
                max_below_rel_def = max_below_rel.def_value
                assert max_below_rel_def is not None
                if max_below_rel_def.is_negative:
                    msg = f"{max_below_rel_def} = max_below_rel[{ls}] < 0"
                    raise exceptions.DataException(
                        exc_key, [ls], msg, module=LOG_MODULE_STR
                    )
                # max_below_rel usually not larger than one (default values)
                if max_below_rel_def > Value(1):
                    msg = f"{max_below_rel_def} = max_below_rel[{ls}] > 1"
                    logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_peak_cost_above(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.PEAKCOSTABOVE_VAL.value
        for ls, peak_cost_above in self._peak_cost_above.items():
            # Unit
            expected_unit = CurrencyUnit.CHF / (ecs.get_unit(self._ec[ls]) / TimeUnit.H)
            if not peak_cost_above.unit.same_type_as(expected_unit):
                msg = (
                    f"Unit {peak_cost_above.unit} of peak_cost_above[{ls}] "
                    f"does not match expected unit {expected_unit}"
                )
                raise exceptions.DataException(
                    exc_key, [ls], msg, module=LOG_MODULE_STR
                )
            # peak_cost_above usually nonnegative
            if peak_cost_above.is_negative:
                msg = f"{peak_cost_above} = peak_cost_above[{ls}] < 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_peak_cost_below(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.PEAKCOSTBELOW_VAL.value
        for ls, peak_cost_below in self._peak_cost_below.items():
            # Unit
            expected_unit = CurrencyUnit.CHF / (ecs.get_unit(self._ec[ls]) / TimeUnit.H)
            if not peak_cost_below.unit.same_type_as(expected_unit):
                msg = (
                    f"Unit {peak_cost_below.unit} of peak_cost_below[{ls}] "
                    f"does not match expected unit {expected_unit}"
                )
                raise exceptions.DataException(
                    exc_key, [ls], msg, module=LOG_MODULE_STR
                )
            # peak_cost_below usually nonnegative
            if peak_cost_below.is_negative:
                msg = f"{peak_cost_below} = peak_cost_below[{ls}] < 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_energy_cost_above(self, ecs: Ecs, times: Times) -> None:
        # self.set_energy_cost_above(LoadShiftId("ls1"), TimeId(2), -1)
        exc_key = ExceptionKey.ENERGYCOSTABOVE_VAL.value
        for ls, energy_cost_above in self._energy_cost_above.items():
            # Unit
            expected_unit = CurrencyUnit.CHF / ecs.get_unit(self._ec[ls])
            assert energy_cost_above.unit is not None
            if not energy_cost_above.unit.same_type_as(expected_unit):
                msg = (
                    f"Unit {energy_cost_above.unit} of energy_cost_above[{ls}] "
                    f"does not match expected unit {expected_unit}"
                )
                raise exceptions.DataException(
                    exc_key, [ls], msg, module=LOG_MODULE_STR
                )
            # Unknown time ids
            energy_cost_above.validate(times, exc_key, module=LOG_MODULE_STR)
            # energy_cost_above usually nonnegative (time values)
            if energy_cost_above.has_values:
                for t in times.ids:
                    if energy_cost_above.get_value(t).is_negative:
                        msg = (
                            f"{energy_cost_above.get_value(t)} = "
                            f"energy_cost_above[{ls}][{t}] < 0"
                        )
                        logging.log_warning(msg, module=LOG_MODULE_STR)
                        break
            # energy_cost_above usually nonnegative (default values)
            if not energy_cost_above.has_values:
                energy_cost_above_def = energy_cost_above.def_value
                assert energy_cost_above_def is not None
                if energy_cost_above_def.is_negative:
                    msg = f"{energy_cost_above_def} = energy_cost_above[{ls}] < 0"
                    logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_energy_cost_below(self, ecs: Ecs, times: Times) -> None:
        exc_key = ExceptionKey.ENERGYCOSTBELOW_VAL.value
        for ls, energy_cost_below in self._energy_cost_below.items():
            # Unit
            expected_unit = CurrencyUnit.CHF / ecs.get_unit(self._ec[ls])
            assert energy_cost_below.unit is not None
            if not energy_cost_below.unit.same_type_as(expected_unit):
                msg = (
                    f"Unit {energy_cost_below.unit} of energy_cost_below[{ls}] "
                    f"does not match expected unit {expected_unit}"
                )
                raise exceptions.DataException(
                    exc_key, [ls], msg, module=LOG_MODULE_STR
                )
            # Unknown time ids
            energy_cost_below.validate(times, exc_key, module=LOG_MODULE_STR)
            # energy_cost_below usually nonnegative (time values)
            if energy_cost_below.has_values:
                for t in times.ids:
                    if energy_cost_below.get_value(t).is_negative:
                        msg = (
                            f"{energy_cost_below.get_value(t)} = "
                            f"energy_cost_below[{ls}][{t}] < 0"
                        )
                        logging.log_warning(msg, module=LOG_MODULE_STR)
                        break
            # energy_cost_below usually nonnegative (default values)
            if not energy_cost_below.has_values:
                energy_cost_below_def = energy_cost_below.def_value
                assert energy_cost_below_def is not None
                if energy_cost_below_def.is_negative:
                    msg = f"{energy_cost_below_def} = energy_cost_below[{ls}] < 0"
                    logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_energy_cost_abovebelow_nonzero(self) -> None:
        for ls in self.ids:
            energy_cost_above = self.get_energy_cost_above(ls)
            energy_cost_below = self.get_energy_cost_below(ls)
            if not energy_cost_above.has_values and not energy_cost_below.has_values:
                energy_cost_above_def = energy_cost_above.def_value
                energy_cost_below_def = energy_cost_below.def_value
                assert energy_cost_above_def is not None
                assert energy_cost_below_def is not None
                pos_tol = Value(EPS_ZEROCHECK, energy_cost_above_def.unit)
                neg_tol = Value(-EPS_ZEROCHECK, energy_cost_above_def.unit)
                if (
                    energy_cost_above_def < pos_tol
                    and energy_cost_below_def > neg_tol
                    and energy_cost_below_def < pos_tol
                    and energy_cost_above_def > neg_tol
                ):
                    msg = (
                        f"{energy_cost_above_def} = "
                        f"energy_cost_above[{ls}] ~ 0 and "
                        f"{energy_cost_below_def} = "
                        f"energy_cost_below[{ls}] ~ 0. This might lead "
                        "to non-unique solutions in V_LoadShiftAbove and "
                        "V_LoadShiftBelow"
                    )
                    logging.log_file_warning(msg, module=LOG_MODULE_STR)

    def _validate_fix_cost(self, times: Times) -> None:
        exc_key = ExceptionKey.FIXCOST_VAL.value
        for ls, fix_cost in self._fix_cost.items():
            # Unknown time ids
            fix_cost.validate(times, exc_key, module=LOG_MODULE_STR)
            # fix_cost usually nonnegative (time values)
            if fix_cost.has_values:
                for t in times.ids:
                    if fix_cost.get_value(t).is_negative:
                        msg = f"{fix_cost.get_value(t)} = fix_cost[{ls}][{t}] < 0"
                        logging.log_warning(msg, module=LOG_MODULE_STR)
                        break
            # fix_cost usually nonnegative (default values)
            if not fix_cost.has_values:
                fix_cost_def = fix_cost.def_value
                assert fix_cost_def is not None
                if fix_cost_def.is_negative:
                    msg = f"{fix_cost_def} = fix_cost[{ls}] < 0"
                    logging.log_warning(msg, module=LOG_MODULE_STR)

    # ---------- #
    # Id checker #
    # ---------- #
    def _check_id(self, ls: LoadShiftId, where: ExceptionKey) -> None:
        if ls not in self._ids:
            raise exceptions.UnknownIdException(where.value, ls, module=LOG_MODULE_STR)
