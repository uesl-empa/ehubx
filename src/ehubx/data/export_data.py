"""
Export data module
"""
from enum import Enum
from typing import Dict, List, Set, Tuple
from ehubx.core.common import TimeSeriesKind
from ehubx.core import logging
from ehubx.data.stage_data import Stages, StageId
from ehubx.data.hub_data import Hubs, HubId
from ehubx.data.ec_data import Ecs, EcId
from ehubx.data.time_data import Times, TimeId
from ehubx.data.time_series import TimeSeries
from ehubx.data import exceptions


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the export data module
    """
    TUPLES_ADD = "adding to 'tuples' of Exports"
    TUPLES_REMOVE = "removing from 'tuples' of Exports"
    TUPLES_VAL = "validating 'tuples' of Exports"
    PRICE_SET = "setting 'price' of Exports"
    PRICE_DEFSET = "setting default 'price' of Exports"
    PRICE_GET = "getting 'price' from Exports"
    PRICE_VAL = "validating 'price' of Exports"
    CO2_SET = "setting 'co2' of Exports"
    CO2_DEFSET = "setting default 'co2' of Exports"
    CO2_GET = "getting 'co2' from Exports"
    CO2_VAL = "validating 'co2' of Exports"
    MAX_SET = "setting 'max' of Exports"
    MAX_DEFSET = "setting default 'max' of Exports"
    MAX_GET = "getting 'max' from Exports"
    MAX_VAL = "validating 'max' of Exports"
    MIN_SET = "setting 'min' of Exports"
    MIN_DEFSET = "setting default 'min' of Exports"
    MIN_GET = "getting 'min' from Exports"
    MIN_VAL = "validating 'min' of Exports"
    MINMAX_VAL = "validating 'min' against 'max' of Exports"
    SUMMAX_SET = "setting 'sum_max' of Exports"
    SUMMAX_GET = "getting 'sum_max' from Exports"
    SUMMAX_VAL = "validating 'sum_max' of Exports"
    SUMMIN_SET = "setting 'sum_min' of Exports"
    SUMMIN_GET = "getting 'sum_min' from Exports"
    SUMMIN_VAL = "validating 'sum_min' of Exports"
    SUMMINMAX_VAL = "validating 'sum_min' against 'sum_max' of Exports"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/export"
"""String identifying the export data module for logging purposes"""

DEF_PRICE: float = 0
"""Default value for parameter 'price' in the export data module"""

DEF_CO2: float = 0
"""Default value for parameter 'co2' in the export data module"""

DEF_MAX: float = float("inf")
"""Default value for parameter 'max' in the export data module"""

DEF_MIN: float = 0
"""Default value for parameter 'min' in the export data module"""

DEF_SUMMAX: float = float("inf")
"""Default value for parameter 'sum_max' in the export data module"""

DEF_SUMMIN: float = 0
"""Default value for parameter 'sum_min' in the export data module"""


class Exports:
    """
    Class for export data. Manages export tuples ids, contains
    getters and setters for export parameters and validation methods
    to control data integrity
    """

    # ---------------- #
    # Property: tuples #
    # ---------------- #
    @property
    def tuples(self) -> Set[Tuple[StageId, HubId, EcId]]:
        """
        Set of known export (stage, hub, ec) tuples
        """
        return self._tuples

    def add_tuple(self, s: StageId, h: HubId, e: EcId) -> None:
        """
        Add a new export (stage, hub, ec) tuple

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
            raise exceptions.DataException(exc_key, [s, h, e], msg,
                                           module=LOG_MODULE_STR)
        self._tuples.add((s, h, e))
        self._price[s, h, e] = TimeSeries()
        self._co2[s, h, e] = TimeSeries()
        self._max[s, h, e] = TimeSeries()
        self._min[s, h, e] = TimeSeries()
        self._price[s, h, e].def_value = DEF_PRICE
        self._co2[s, h, e].def_value = DEF_CO2
        self._max[s, h, e].def_value = DEF_MAX
        self._min[s, h, e].def_value = DEF_MIN

    # --------------- #
    # Property: price #
    # --------------- #
    def get_price(self, s: StageId, h: HubId, e: EcId) -> TimeSeries:
        """
        Get the parameter 'price' which denotes the price per power unit that
        will be paid for export. This is an optional parameter with a
        default value of 0.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: ec
        :type e: EcId
        :return: Export prices [CHF/kW]
        :rtype: TimeSeries
        """
        self._check_ids(s, h, e, ExceptionKey.PRICE_GET)
        return self._price[s, h, e]

    def set_price(self, s: StageId, h: HubId, e: EcId, t: TimeId,
                  price: float) -> None:
        """
        At a specific time, set the parameter 'price' which denotes the price
        per power unit that will be paid for export. This is an optional
        parameter with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: ec
        :type e: EcId
        :param t: Time
        :type t: TimeId
        :param price: Export price [CHF/kW]
        :type price: float
        """
        self._check_ids(s, h, e, ExceptionKey.PRICE_SET)
        self._price[s, h, e].set_value(t, price)

    def set_price_def(self, s: StageId, h: HubId, e: EcId,
                      price_def: float) -> None:
        """
        Set the default (with respect to time) value for the parameter 'price'
        which denotes the price per power unit that will be paid for
        export. This is an optional parameter with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: ec
        :type e: EcId
        :param price_def: Default export price [CHF/kW]
        :type price_def: float
        """
        self._check_ids(s, h, e, ExceptionKey.PRICE_DEFSET)
        self._price[s, h, e].def_value = price_def

    def clear_price(self) -> None:
        """Clear all price data from this object"""
        for (s, h, e) in self._price:
            self._price[s, h, e].clear()

    # ------------- #
    # Property: co2 #
    # ------------- #
    def get_co2(self, s: StageId, h: HubId, e: EcId) -> TimeSeries:
        """
        Get the parameter 'co2' which denotes the embedded co2 per power unit
        that will be redeemed for export of an ec. This is an optional
        parameter with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: ec
        :type e: EcId
        :return: Embedded CO2 values [kg/kW]
        :rtype: TimeSeries
        """
        self._check_ids(s, h, e, ExceptionKey.CO2_GET)
        return self._co2[s, h, e]

    def set_co2(self, s: StageId, h: HubId, e: EcId, t: TimeId, co2: float
                ) -> None:
        """
        At a specific time, set the parameter 'co2' which denotes the embedded
        co2 per power unit that will be redeemed for the export of an ec. This
        is an optional parameter with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: ec
        :type e: EcId
        :param t: Time
        :type t: TimeId
        :param co2: Embedded CO2 [kg/kW]
        :type co2: float
        """
        self._check_ids(s, h, e, ExceptionKey.CO2_SET)
        self._co2[s, h, e].set_value(t, co2)

    def set_co2_def(self, s: StageId, h: HubId, e: EcId, co2_def: float
                    ) -> None:
        """
        Set the default (with respect to time) value for the parameter 'co2'
        which denotes the embedded co2 per power unit that will be redeemed for
        the export of an ec. This is an optional parameter with a default value
        of 0.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: ec
        :type e: EcId
        :param co2_def: Default embedded CO2 [kg/kW]
        :type co2_def: float
        """
        self._check_ids(s, h, e, ExceptionKey.CO2_DEFSET)
        self._co2[s, h, e].def_value = co2_def

    def clear_co2(self) -> None:
        """Clear all CO2 data from this object"""
        for (s, h, e) in self._co2:
            self._co2[s, h, e].clear()

    # ------------- #
    # Property: max #
    # ------------- #
    def get_max(self, s: StageId, h: HubId, e: EcId) -> TimeSeries:
        """
        Get the parameter 'max' which denotes the maximal allowed export
        amounts. This is an optional parameter with a default value of
        infinity.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: ec
        :type e: EcId
        :return: Maximal allowed exports [kW]
        :rtype: TimeSeries
        """
        self._check_ids(s, h, e, ExceptionKey.MAX_GET)
        return self._max[s, h, e]

    def set_max(self, s: StageId, h: HubId, e: EcId, t: TimeId,
                exp_max: float) -> None:
        """
        At a specific time, set the parameter 'max' which denotes the maximal
        allowed export amount. This is an optional parameter with a default
        value of infinity.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: ec
        :type e: EcId
        :param t: Time
        :type t: TimeId
        :param imp_max: Maximal allowed export [kW]
        :type imp_max: float
        """
        self._check_ids(s, h, e, ExceptionKey.MAX_SET)
        self._max[s, h, e].set_value(t, exp_max)

    def set_max_def(self, s: StageId, h: HubId, e: EcId,
                    max_def: float) -> None:
        """
        Set the default value for the parameter 'max' which denotes the maximal
        allowed export amount. This is an optional parameter with a default
        value of infinity.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: ec
        :type e: EcId
        :param max_def: Default maximal allowed export [kW]
        :type max_def: float
        """
        self._check_ids(s, h, e, ExceptionKey.MAX_DEFSET)
        self._max[s, h, e].def_value = max_def

    def clear_max(self) -> None:
        """Clear all maximal allowed export data from this object"""
        for (s, h, e) in self._max:
            self._max[s, h, e].clear()

    # ------------- #
    # Property: min #
    # ------------- #
    def get_min(self, s: StageId, h: HubId, e: EcId) -> TimeSeries:
        """
        Get the parameter 'min' which denotes the minimal allowed export
        amounts. This is an optional parameter with a default value of
        0.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: ec
        :type e: EcId
        :return: Minimal allowed exports [kW]
        :rtype: TimeSeries
        """
        self._check_ids(s, h, e, ExceptionKey.MIN_GET)
        return self._min[s, h, e]

    def set_min(self, s: StageId, h: HubId, e: EcId, t: TimeId,
                exp_min: float) -> None:
        """
        At a specific time, set the parameter 'min' which denotes the minimal
        allowed export amount. This is an optional parameter with a default
        value of 0.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: ec
        :type e: EcId
        :param t: Time
        :type t: TimeId
        :param imp_min: Minimal allowed export [kW]
        :type imp_min: float
        """
        self._check_ids(s, h, e, ExceptionKey.MIN_SET)
        self._min[s, h, e].set_value(t, exp_min)

    def set_min_def(self, s: StageId, h: HubId, e: EcId,
                    min_def: float) -> None:
        """
        Set the default value for the parameter 'min' which denotes the minimal
        allowed export amount. This is an optional parameter with a default
        value of 0.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: ec
        :type e: EcId
        :param min_def: Default minimal allowed export [kW]
        :type min_def: float
        """
        self._check_ids(s, h, e, ExceptionKey.MIN_DEFSET)
        self._min[s, h, e].def_value = min_def

    def clear_min(self) -> None:
        """Clear all minimal allowed export data from this object"""
        for (s, h, e) in self._min:
            self._min[s, h, e].clear()

    # ----------------- #
    # Property: sum_min #
    # ----------------- #
    def get_sum_min(self, s: StageId, h: HubId, e: EcId) -> float:
        """
        Get the parameter 'sum_min' which denotes the minimal amount of an ec
        that has to be exported over the entire time horizon.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: ec
        :type e: EcId
        :return: Minimal export amount over the time horizon [kWh]
        :rtype: float
        """
        self._check_ids(s, h, e, ExceptionKey.SUMMIN_GET)
        return self._sum_min.get((s, h, e), DEF_SUMMIN)

    def set_sum_min(self, s: StageId, h: HubId, e: EcId,
                    sum_min: float) -> None:
        """
        Set the parameter 'sum_min' which denotes the minimal amount of an ec
        that has to be exported over the entire time horizon.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: ec
        :type e: EcId
        :param sum_min: Minimal export amount over the time horizon [kWh]
        :type sum_min: float
        """
        self._check_ids(s, h, e, ExceptionKey.SUMMIN_SET)
        self._sum_min[s, h, e] = sum_min

    # ----------------- #
    # Property: sum_max #
    # ----------------- #
    def get_sum_max(self, s: StageId, h: HubId, e: EcId) -> float:
        """
        Get the parameter 'sum_max' which denotes the maximal amount of an ec
        that may be exported over the entire time horizon.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: ec
        :type e: EcId
        :return: Maximal export amount over the time horizon [kWh]
        :rtype: float
        """
        self._check_ids(s, h, e, ExceptionKey.SUMMAX_GET)
        return self._sum_max.get((s, h, e), DEF_SUMMAX)

    def set_sum_max(self, s: StageId, h: HubId, e: EcId,
                    sum_max: float) -> None:
        """
        Set the parameter 'sum_max' which denotes the maximal amount of an ec
        that may be exported over the entire time horizon.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: ec
        :type e: EcId
        :param sum_max: Maximal export amount over the time horizon [kWh]
        :type sum_max: float
        """
        self._check_ids(s, h, e, ExceptionKey.SUMMAX_SET)
        self._sum_max[s, h, e] = sum_max

    # ------------------------------- #
    # Secondary property: time_series #
    # ------------------------------- #
    @property
    def time_series(self) -> List[Tuple[TimeSeriesKind, StageId,
                                        Tuple[str, ...], TimeSeries]]:
        """
        Time series profiles in the exports module. This is a list of tuples.
        Each list element has the following list entries: 1) ProfileKind of the
        profile. 2) Stage. 3) Tuple of string identifiers specific to the
        ProfileKind. 4) The TimeSeries itself

        :return: All time series of the exports module
        :rtype: List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...],
            TimeSeries]]
        """
        all_series: List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...],
                               TimeSeries]] = []
        # Price
        for (s, h, e), series in self._price.items():
            if series.has_values:
                all_series.append((TimeSeriesKind.EXPORTPRICE, s,
                                   (h.key, e.key), series))
        # min
        for (s, h, e), series in self._min.items():
            if series.has_values:
                all_series.append((TimeSeriesKind.EXPORTMIN, s,
                                   (h.key, e.key), series))
        # max
        for (s, h, e), series in self._max.items():
            if series.has_values:
                all_series.append((TimeSeriesKind.EXPORTMAX, s,
                                   (h.key, e.key), series))
        # co2
        for (s, h, e), series in self._co2.items():
            if series.has_values:
                all_series.append((TimeSeriesKind.EXPORTCO2, s,
                                   (h.key, e.key), series))
        return all_series

    def set_time_series_val(self, kind: TimeSeriesKind, s: StageId,
                            ids: Tuple[str, ...], t: TimeId, value: float
                            ) -> None:
        """
        Set the value for a time series in the export data class. The time
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
        if kind == TimeSeriesKind.EXPORTPRICE:
            h = HubId(ids[0])
            e = EcId(ids[1])
            self.set_price(s, h, e, t, value)
        if kind == TimeSeriesKind.EXPORTMAX:
            h = HubId(ids[0])
            e = EcId(ids[1])
            self.set_max(s, h, e, t, value)
        if kind == TimeSeriesKind.EXPORTMIN:
            h = HubId(ids[0])
            e = EcId(ids[1])
            self.set_min(s, h, e, t, value)
        if kind == TimeSeriesKind.EXPORTCO2:
            h = HubId(ids[0])
            e = EcId(ids[1])
            self.set_co2(s, h, e, t, value)

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._tuples: Set[Tuple[StageId, HubId, EcId]] = set()
        self._price: Dict[Tuple[StageId, HubId, EcId], TimeSeries] = {}
        self._co2: Dict[Tuple[StageId, HubId, EcId], TimeSeries] = {}
        self._max: Dict[Tuple[StageId, HubId, EcId], TimeSeries] = {}
        self._min: Dict[Tuple[StageId, HubId, EcId], TimeSeries] = {}
        self._sum_max: Dict[Tuple[StageId, HubId, EcId], float] = {}
        self._sum_min: Dict[Tuple[StageId, HubId, EcId], float] = {}

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self, stages: Stages, hubs: Hubs, ecs: Ecs,
                 times: Times) -> None:
        """
        Validate all export data in this object. Apart from sense-checking
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
        self._validate_price(times)
        self._validate_co2(times)
        self._validate_max(times)
        self._validate_min(times)
        self._validate_minmax(times)
        self._validate_sum_max()
        self._validate_sum_min()
        self._validate_sum_minmax()

    def _validate_tuples(self, stages: Stages, hubs: Hubs,
                         ecs: Ecs) -> None:
        exc_key = ExceptionKey.TUPLES_VAL.value
        for (s, h, e) in self._tuples:
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

    def _validate_price(self, times: Times) -> None:
        exc_key = ExceptionKey.PRICE_VAL.value
        for (s, h, e), price in self._price.items():
            # Unknown time ids
            price.validate(times, exc_key, module=LOG_MODULE_STR)
            # Price values usually nonnegative (time values)
            if price.has_values:
                for t in times.ids:
                    if price.get_value(t) < 0:
                        msg = (f"{price.get_value(t)} = price[{s}, {h}, {e}]"
                            f"[{t}] < 0")
                        logging.log_warning(msg, module=LOG_MODULE_STR)
                        break
            # Price values usually nonnegative (default value)
            if not price.has_values:
                price_def = price.def_value
                assert price_def is not None
                if price_def < 0:
                    msg = f"{price_def} = price[{s}, {h}, {e}] < 0"
                    logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_co2(self, times: Times) -> None:
        exc_key = ExceptionKey.CO2_VAL.value
        for (s, h, e), co2 in self._co2.items():
            # Unknown time ids
            co2.validate(times, exc_key, module=LOG_MODULE_STR)
            # CO2 values usually nonnegative (time values)
            if co2.has_values:
                for t in times.ids:
                    if co2.get_value(t) < 0:
                        msg = (f"{co2.get_value(t)} = co2"
                            f"[{s}, {h}, {e}][{t}] < 0")
                        logging.log_warning(msg, module=LOG_MODULE_STR)
                        break
            # CO2 values usually nonnegative (default value)
            if not co2.has_values:
                co2_def = co2.def_value
                assert co2_def is not None
                if co2_def < 0:
                    msg = (f"{co2_def} = co2"
                        f"[{s}, {h}, {e}] < 0")
                    logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_max(self, times: Times) -> None:
        exc_key = ExceptionKey.MAX_VAL.value
        for (s, h, e), exp_max in self._max.items():
            # Unknown time ids
            exp_max.validate(times, exc_key, module=LOG_MODULE_STR)
            # Max values must be nonnegative (time values)
            if exp_max.has_values:
                for t in times.ids:
                    if exp_max.get_value(t) < 0:
                        msg = (f"{exp_max.get_value(t)} = max"
                            f"[{s}, {h}, {e}][{t}] < 0")
                        raise exceptions.DataException(exc_key, [s, h, e, t],
                            msg, module=LOG_MODULE_STR)
            # Max values must be nonnegative (default value)
            if not exp_max.has_values:
                exp_max_def = exp_max.def_value
                assert exp_max_def is not None
                if exp_max_def < 0:
                    msg = f"{exp_max_def} = max[{s}, {h}, {e}] < 0"
                    raise exceptions.DataException(exc_key, [s, h, e],
                        msg, module=LOG_MODULE_STR)

    def _validate_min(self, times: Times) -> None:
        exc_key = ExceptionKey.MIN_VAL.value
        for (s, h, e), exp_min in self._min.items():
            # Unknown time ids
            exp_min.validate(times, exc_key, module=LOG_MODULE_STR)
            # Min values usually nonnegative (time values)
            if exp_min.has_values:
                for t in times.ids:
                    if exp_min.get_value(t) < 0:
                        msg = (f"{exp_min.get_value(t)} = min"
                            f"[{s}, {h}, {e}][{t}] < 0")
                        logging.log_warning(msg, module=LOG_MODULE_STR)
                        break
            # Min values usually nonnegative (default valuee)
            if not exp_min.has_values:
                exp_min_def = exp_min.def_value
                assert exp_min_def is not None
                if exp_min_def < 0:
                    msg = f"{exp_min_def} = min[{s}, {h}, {e}] < 0"
                    logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_minmax(self, times: Times) -> None:
        exc_key = ExceptionKey.MINMAX_VAL.value
        for (s, h, e) in self.tuples:
            exp_min = self.get_min(s, h, e)
            exp_max = self.get_max(s, h, e)
            # exp_min must not be larger than exp_max (time values)
            if exp_min.has_values or exp_max.has_values:
                for t in times.ids:
                    if exp_min.get_value(t) > exp_max.get_value(t):
                        msg = (f"{exp_min.get_value(t)} = min[{s}, {h}, {e}]"
                               f"[{t}] > max[{s}, {h}, {e}][{t}] = "
                               f"{exp_max.get_value(t)}")
                        raise exceptions.DataException(exc_key, [s, h, e, t],
                            msg, module=LOG_MODULE_STR)
            # exp_min must not be larger than exp_max (default values)
            if not (exp_min.has_values or exp_max.has_values):
                exp_min_def = exp_min.def_value
                exp_max_def = exp_max.def_value
                assert exp_min_def is not None
                assert exp_max_def is not None
                if exp_min_def > exp_max_def:
                    msg = (f"{exp_min_def} = min[{s}, {h}, {e}] > "
                           f"max[{s}, {h}, {e}] = {exp_max_def}")
                    raise exceptions.DataException(exc_key, [s, h, e],
                        msg, module=LOG_MODULE_STR)

    def _validate_sum_max(self) -> None:
        exc_key = ExceptionKey.SUMMAX_VAL.value
        for (s, h, e), sum_max in self._sum_max.items():
            # sum_max values must be nonnegative
            if sum_max < 0:
                msg = f"{sum_max} = sum_max[{s}, {h}, {e}] < 0"
                raise exceptions.DataException(exc_key, [s, h, e], msg,
                                               module=LOG_MODULE_STR)

    def _validate_sum_min(self) -> None:
        for (s, h, e), sum_min in self._sum_min.items():
            # sum_min values usually nonnegative
            if sum_min < 0:
                msg = f"{sum_min} = sum_min[{s}, {h}, {e}] < 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_sum_minmax(self) -> None:
        exc_key = ExceptionKey.SUMMINMAX_VAL.value
        for (s, h, e) in self.tuples:
            sum_min = self.get_sum_min(s, h, e)
            sum_max = self.get_sum_max(s, h, e)
            # sum_min must not be larger than sum_max
            if sum_min > sum_max:
                msg = (f"{sum_min} = sum_min[{s}, {h}, {e}] > "
                       f"sum_max[{s}, {h}, {e}] = {sum_max}")
                raise exceptions.DataException(exc_key, [s, h, e], msg,
                                               module=LOG_MODULE_STR)

    # ---------- #
    # Id checker #
    # ---------- #
    def _check_ids(self, s: StageId, h: HubId, e: EcId,
                   where: ExceptionKey) -> None:
        if (s, h, e) not in self._tuples:
            msg = (f"Encountered tuple ({s}, {h}, {e}) which is not an export "
                   f"tuple. This happened while {where.value}")
            raise exceptions.DataException(where.value, [s, h, e], msg,
                                           module=LOG_MODULE_STR)
