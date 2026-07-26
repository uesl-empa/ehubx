"""
Stage data module
"""

import collections
from enum import Enum
from typing import Dict, List, Optional, Set

from ehubx.core import logging
from ehubx.data import exceptions
from ehubx.data.index import Index, IndexKind
from ehubx.data.unit import CurrencyUnit, MassUnit
from ehubx.data.value import Value


class StageId(Index):
    """
    Stage index
    """

    def __init__(self, key: str):
        super().__init__(IndexKind.STAGE, key)


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the stage data module
    """

    ID_ADD = "adding to 'ids' of Stages"
    STARTYEAR_SET = "setting 'start_year' of Stages"
    STARTYEAR_GET = "getting 'start_year' from Stages"
    STARTYEAR_VAL = "validating 'start_year' of Stages"
    CO2PRICE_SET = "setting 'co2_price' of Stages"
    CO2PRICE_GET = "getting 'co2_price' from Stages"
    CO2PRICE_VAL = "validating 'co2_price' of Stages"
    CO2MIN_SET = "setting 'co2_min' of Stages"
    CO2MIN_GET = "getting 'co2_min' from Stages"
    CO2MAX_SET = "setting 'co2_max' of Stages"
    CO2MAX_GET = "getting 'co2_max' from Stages"
    CO2MINMAX_VAL = "validating 'co2_min' against 'co2_max' of Stages"
    AUTALLOWUNMETDEMAND_GET = "getting autonomy_allow_demand from Stages"
    AUTALLOWUNMETDEMAND_SET = "setting autonomy_allow_demand of Stages"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/stage"
"""String identifying the stage data module for logging purposes"""

DEF_CO2_PRICE: float = 0
"""Default value for parameter 'co2_price' in the stage data module"""

DEF_CO2_MIN: float = -float("inf")
"""Default value for parameter 'co2_min' in the stage data module"""

DEF_CO2_MAX: float = float("inf")
"""Default value for parameter 'co2_max' in the stage data module"""


class Stages:
    """
    Class for stage data. Manages stage ids, contains
    getters and setters for stage parameters and validation methods
    to control data integrity
    """

    # ------------- #
    # Property: ids #
    # ------------- #
    @property
    def ids(self) -> Set[StageId]:
        """
        Set of known stage ids
        """
        return self._ids

    @property
    def ids_in_order(self) -> List[StageId]:
        """
        List of known stage ids, in ascending order of start_year
        """
        ids_as_list = list(self._ids)
        stage_years = [self.get_start_year(s) for s in ids_as_list]
        sort_index = sorted(range(len(stage_years)), key=stage_years.__getitem__)
        ids_in_order = [ids_as_list[i] for i in sort_index]
        return ids_in_order

    def add_id(self, s: StageId) -> None:
        """
        Add a new stage id

        :param s: Id to be added
        :type s: StageId
        """
        if s in self._ids:
            raise exceptions.DuplicateIdException(
                ExceptionKey.ID_ADD.value, s, module=LOG_MODULE_STR
            )
        self._ids.add(s)

    # -------------------- #
    # Property: start_year #
    # -------------------- #
    def get_start_year(self, s: StageId) -> float:
        """
        Get the parameter 'start_year' which denotes the first year of a stage.
        This is a mandatory parameter.

        :param s: Stage id
        :type s: StageId
        :return: Start year
        :rtype: float
        """
        self._check_id(s, ExceptionKey.STARTYEAR_GET)
        start_year = self._start_year.get(s, None)
        if start_year is None:
            raise exceptions.MissingIdException(
                ExceptionKey.STARTYEAR_GET.value, s, module=LOG_MODULE_STR
            )
        return start_year

    def set_start_year(self, s: StageId, start_year: float) -> None:
        """
        Set the parameter 'start_year' which denotes the first year of a stage.
        This is a mandatory parameter.

        :param s: Stage id
        :type s: StageId
        :param start_year: Start year
        :type start_year: float
        """
        self._check_id(s, ExceptionKey.STARTYEAR_SET)
        self._start_year[s] = start_year

    # ------------------- #
    # Property: co2_price #
    # ------------------- #
    def get_co2_price(self, s: StageId) -> Value:
        """
        Get the parameter 'co2_price' which denotes the price that arises for
        each unit of CO2 emissions produced during a stage. This is an
        optional parameter with a default value of 0.

        :param s: Stage id
        :type s: StageId
        :return: CO2 price
        :rtype: Value
        """
        self._check_id(s, ExceptionKey.CO2PRICE_GET)
        return self._co2_price.get(
            s, Value(DEF_CO2_PRICE, CurrencyUnit.CHF / MassUnit.KG)
        )

    def set_co2_price(self, s: StageId, co2_price: Value) -> None:
        """
        Set the parameter 'co2_price' which denotes the price that arises for
        each unit of CO2 emissions produced during a stage. This is an
        optional parameter with a default value of 0.

        :param s: Stage id
        :type s: StageId
        :param co2_price: CO2 price
        :type co2_price: Value
        """
        self._check_id(s, ExceptionKey.CO2PRICE_SET)
        expected_unit = CurrencyUnit.CHF / MassUnit.KG
        if not co2_price.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.CO2PRICE_SET.value,
                [s],
                f"Unit {co2_price.unit} of co2_price[{s}] = {co2_price} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._co2_price[s] = co2_price

    # ----------------- #
    # Property: co2_min #
    # ----------------- #
    def get_co2_min(self, s: StageId) -> Value:
        """
        Get the parameter 'co2_min' which denotes the minimal amount of CO2
        emissions that have to be reached during a stage. This is an optional
        parameter with a default value of 0.

        :param s: _description_
        :type s: StageId
        :return: Minimal CO2 emissions
        :rtype: Value
        """
        self._check_id(s, ExceptionKey.CO2MIN_GET)
        return self._co2_min.get(s, Value(DEF_CO2_MIN, MassUnit.KG))

    def set_co2_min(self, s: StageId, co2_min: Value) -> None:
        """
        Set the parameter 'co2_min' which denotes the minimal amount of CO2
        emissions that have to be reached during a stage. This is an optional
        parameter with a default value of 0.

        :param s: _description_
        :type s: StageId
        :param co2_min: Minimal CO2 emissions
        :type co2_min: float
        """
        self._check_id(s, ExceptionKey.CO2MIN_SET)
        expected_unit = MassUnit.KG
        if not co2_min.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.CO2MIN_SET.value,
                [s],
                f"Unit {co2_min.unit} of co2_min[{s}] = {co2_min} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._co2_min[s] = co2_min

    # ----------------- #
    # Property: co2_max #
    # ----------------- #
    def get_co2_max(self, s: StageId) -> Value:
        """
        Get the parameter 'co2_max' which denotes the maximal amount of CO2
        emissions that are permitted during a stage. This is an optional
        parameter with a default value of infinity.

        :param s: Stage id
        :type s: StageId
        :return: Maximal CO2 emissions
        :rtype: Value
        """
        self._check_id(s, ExceptionKey.CO2MAX_GET)
        return self._co2_max.get(s, Value(DEF_CO2_MAX, MassUnit.KG))

    def set_co2_max(self, s: StageId, co2_max: Value) -> None:
        """
        Set the parameter 'co2_max' which denotes the maximal amount of CO2
        emissions that are permitted during a stage. This is an optional
        parameter with a default value of infinity.

        :param s: Stage id
        :type s: StageId
        :param co2_max: Maximal CO2 emissions
        :type co2_max: Value
        """
        self._check_id(s, ExceptionKey.CO2MAX_SET)
        expected_unit = MassUnit.KG
        if not co2_max.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.CO2MAX_SET.value,
                [s],
                f"Unit {co2_max.unit} of co2_max[{s}] = {co2_max} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._co2_max[s] = co2_max

    # ------------------------------------- #
    # Property: autonomy_allow_unmet_demand #
    # ------------------------------------- #

    def get_allow_unmet_demand(self, s: StageId) -> Optional[bool]:
        self._check_id(s, ExceptionKey.AUTALLOWUNMETDEMAND_GET)
        return self._autonomy_allow_unmet_demand.get(s, None)

    def set_allow_unmet_demand(self, s: StageId, val: bool) -> None:
        self._check_id(s, ExceptionKey.AUTALLOWUNMETDEMAND_SET)
        self._autonomy_allow_unmet_demand[s] = bool(val)

    # -------------------- #
    # Secondary properties #
    # -------------------- #
    @property
    def init_year(self) -> float:
        """Start year of the initial stage (i.e.; earliest start_year)"""
        return min(self._start_year.values())

    @property
    def final_year(self) -> float:
        """Start year of the final stage (i.e.; latest start_year)"""
        return max(self._start_year.values())

    @property
    def init_stage(self) -> StageId:
        """Earliest stage (i.e.; stage with earliest start_year)"""
        return min(self.ids, key=lambda s: self._start_year[s])

    @property
    def final_stage(self) -> StageId:
        """Final stage (i.e.; stage with latest start_year)"""
        return max(self.ids, key=lambda s: self._start_year[s])

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._ids: Set[StageId] = set()
        self._start_year: Dict[StageId, float] = {}
        self._co2_price: Dict[StageId, Value] = {}
        self._co2_min: Dict[StageId, Value] = {}
        self._co2_max: Dict[StageId, Value] = {}
        self._autonomy_allow_unmet_demand: Dict[StageId, Optional[bool]] = {}

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self) -> None:
        """
        Validate all stage data in this object. This entails sense-checking
        parameters in terms of quantity.
        """
        self._validate_start_years()
        self._validate_co2_min()
        self._validate_co2_max()
        self._validate_co2_minmax()
        self._validate_co2_price()

    def _validate_start_years(self) -> None:
        # Search for duplicate start years
        counts = collections.Counter(self._start_year.values())
        dupes = {
            s: start_year
            for s, start_year in self._start_year.items()
            if counts[start_year] > 1
        }
        if len(dupes) > 0:
            dupe_dict = {
                dupe_year: [s for s in self._ids if dupes[s] == dupe_year]
                for dupe_year in set(dupes.values())
            }
            msg = f"Duplicate start_years: {dupe_dict}"
            raise exceptions.DataException(
                ExceptionKey.STARTYEAR_SET.value,
                list(dupes.keys()),
                msg,
                module=LOG_MODULE_STR,
            )

    def _validate_co2_price(self) -> None:
        for s, co2_price in self._co2_price.items():
            if co2_price.is_negative:
                msg = f"{co2_price} = co2_price[{s}] < 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_co2_min(self) -> None:
        for s, co2_min in self._co2_min.items():
            # co2_min usually nonnegative
            if co2_min.is_negative:
                msg = f"{co2_min} = co2_min[{s}] < 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_co2_max(self) -> None:
        for s, co2_max in self._co2_max.items():
            # co2_max usually nonnegative
            if co2_max.is_negative:
                msg = f"{co2_max} = co2_max[{s}] < 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_co2_minmax(self) -> None:
        for s in self.ids:
            co2_min = self.get_co2_min(s)
            co2_max = self.get_co2_max(s)
            if co2_min > co2_max:
                msg = f"{co2_min} = co2_min[{s}] > co2_max[{s}] = {co2_max}"
                raise exceptions.DataException(
                    ExceptionKey.CO2MINMAX_VAL.value, [s], msg, module=LOG_MODULE_STR
                )

    # ---------- #
    # Id checker #
    # ---------- #
    def _check_id(self, x: StageId, where: ExceptionKey) -> None:
        if x not in self._ids:
            raise exceptions.UnknownIdException(where.value, x, module=LOG_MODULE_STR)
