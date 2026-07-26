"""
Energy system data module. This module deals with system-wide parameters and
additionally acts as an umbrella class which manages the other data classes
"""

import itertools
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from ehubx.core import logging
from ehubx.core.common import (
    MULT_HEUR_LIMIT_FROM_DEMAND,
    MULT_HEUR_SUM_LIMIT_FROM_DEMAND,
    TimeSeriesKind,
)
from ehubx.data import exceptions
from ehubx.data.ates_data import AtesData
from ehubx.data.ates_tech_data import AtesTechs
from ehubx.data.conv_tech_data import ConversionTechs
from ehubx.data.demand_data import Demands
from ehubx.data.ebm_tech_data import EbmTechs
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.export_data import Exports
from ehubx.data.hp_tech_data import HeatpumpTechs
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.import_data import Imports
from ehubx.data.load_shedding_data import LoadShedding
from ehubx.data.load_shifting_data import LoadShifting
from ehubx.data.net_link_data import NetworkLinks
from ehubx.data.net_tech_data import NetworkTechs
from ehubx.data.self_sufficiency_data import SelfSufficiency
from ehubx.data.solar_data import SolarData
from ehubx.data.solar_tech_data import SolarTechs
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.stor_tech_data import StorageTechs
from ehubx.data.tech_data import Techs
from ehubx.data.time_data import TimeId, Times
from ehubx.data.time_series import TimeSeries
from ehubx.data.unit import (
    CurrencyUnit,
    DimlessUnit,
    LengthUnit,
    MassUnit,
    PowerUnit,
    TimeUnit,
)
from ehubx.data.value import Value


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the energy system data
    module
    """

    TRLTHRESHOLD_SET = "setting 'trl_threshold' of EnergySystem"
    TRLTHRESHOLD_VAL = "validating 'trl_threshold' of EnergySystem"
    INTERESTRATEDEF_GET = "getting 'interest_rate_def' from EnergySystem"
    INTERESTRATEDEF_VAL = "validating 'interest_rate_def' of EnergySystem"
    NUMTIMESHORIZON_GET = "getting 'num_times_horizon' from EnergySystem"
    NUMTIMESHORIZON_VAL = "validating 'num_times_horizon' of EnergySystem"
    CURRENCYUNIT_GET = "getting 'currency_unit' from EnergySystem"
    CURRENCYUNIT_VAL = "validating 'currency_unit' of EnergySystem"
    LENGTHUNIT_GET = "getting 'length_unit' from EnergySystem"
    LENGTHUNIT_VAL = "validating 'length_unit' of EnergySystem"
    MASSUNIT_GET = "getting 'mass_unit' from EnergySystem"
    MASSUNIT_VAL = "validating 'mass_unit' of EnergySystem"
    POWERUNIT_GET = "getting 'power_unit' from EnergySystem"
    POWERUNIT_VAL = "validating 'power_unit' of EnergySystem"
    HEURLIMIT = "calculating heuristic limits of EnergySystem"


# -------- #
# Literals #
# -------- #
DEF_TRLTHRESHOLD: int = 0
"""Default value for parameter 'trl_threshold' in the energy system data
module"""

LOG_MODULE_STR: str = "data/system"
"""String identifying the energy system data module for logging purposes"""


class EnergySystem:
    """
    Class for data of the overall energy system. On the one hand, this class
    contains getters and setters for system-wide parameters and validation
    methods to control data integrity. On the other hand, it acts as an
    umbrella class of the data module, managing the other data classes as its
    attributes.
    """

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        # Properties
        self._interest_rate_def: Optional[Value] = None
        self._trl_threshold: Optional[Value] = None
        self._num_times_horizon: Optional[int] = None
        self._currency_unit: CurrencyUnit = CurrencyUnit.CHF
        self._length_unit: LengthUnit = LengthUnit.M
        self._mass_unit: MassUnit = MassUnit.KG
        self._power_unit: PowerUnit = PowerUnit.KW
        self._time_unit: TimeUnit = TimeUnit.H
        self._demand_file_paths: Set[str] = set()
        self._heur_limit_max_in_sh: Dict[Tuple[StageId, HubId, EcId], Value] = {}
        self._heur_limit_max_in: Dict[EcId, Value] = {}
        self._heur_limit_max_out_sh: Dict[Tuple[StageId, HubId, EcId], Value] = {}
        self._heur_limit_max_out: Dict[EcId, Value] = {}
        self._heur_limit_max_sum_in_sh: Dict[Tuple[StageId, HubId, EcId], Value] = {}
        self._heur_limit_max_sum_in: Dict[EcId, Value] = {}
        self._heur_limit_max_sum_out_sh: Dict[Tuple[StageId, HubId, EcId], Value] = {}
        self._heur_limit_max_sum_out: Dict[EcId, Value] = {}
        self._heur_limits_ready: bool = False

        # Modules
        self.stages = Stages()
        self.hubs = Hubs()
        self.net_links = NetworkLinks()
        self.ecs = Ecs()
        self.imports = Imports()
        self.exports = Exports()
        self.demands = Demands()
        self.load_shedding = LoadShedding()
        self.load_shifting = LoadShifting()
        self.techs = Techs()
        self.stor_techs = StorageTechs()
        self.ebm_techs = EbmTechs()
        self.conv_techs = ConversionTechs()
        self.solar_techs = SolarTechs()
        self.hp_techs = HeatpumpTechs()
        self.ates_techs = AtesTechs()
        self.net_techs = NetworkTechs()
        self.self_sufficiency = SelfSufficiency()
        self.ates_data = AtesData()
        self.solar_data = SolarData()
        self.times = Times()

    # ---------------------------------- #
    # Property: interest_rate_categories #
    # ---------------------------------- #
    @property
    def interest_rate_def(self) -> Value:
        """Default interest rate value used in the calculation of annuity
        costs. This is used everywhere in the model where no specific interest
        rate is specified instead (e.g.; for technologies). This is a mandatory
        parameter."""
        if self._interest_rate_def is None:
            raise exceptions.MissingValueException(
                ExceptionKey.INTERESTRATEDEF_GET.value, module=LOG_MODULE_STR
            )
        return self._interest_rate_def

    @interest_rate_def.setter
    def interest_rate_def(self, interest_rate_def: Value) -> None:
        expected_unit = DimlessUnit()
        if not interest_rate_def.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.INTERESTRATEDEF_VAL.value,
                [],
                f"Unit {interest_rate_def.unit} of interest_rate_def "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._interest_rate_def = interest_rate_def

    # ------------- #
    # Property: TRL #
    # ------------- #
    @property
    def trl_threshold(self) -> Value:
        """Threshold value for the Technology Readiness Level (TRL) value.
        Technologies can only be used in stages where their TRL is above this
        threshold level. This is an optional parameter with a default value of
        0."""
        if self._trl_threshold is None:
            return Value(DEF_TRLTHRESHOLD)
        return self._trl_threshold

    @trl_threshold.setter
    def trl_threshold(self, trl_threshold: Value) -> None:
        expected_unit = DimlessUnit()
        if not trl_threshold.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.TRLTHRESHOLD_SET.value,
                [],
                f"Unit {trl_threshold.unit} of trl_threshold "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._trl_threshold = trl_threshold

    # --------------------------- #
    # Property: num_times_horizon #
    # --------------------------- #
    @property
    def num_times_horizon(self) -> int:
        """Number of horizon time steps in the system. This value must fit the
        length of all input time series in the data model. This is a mandatory
        parameter."""
        if self._num_times_horizon is None:
            raise exceptions.MissingValueException(
                ExceptionKey.NUMTIMESHORIZON_GET.value, module=LOG_MODULE_STR
            )
        return self._num_times_horizon

    @num_times_horizon.setter
    def num_times_horizon(self, num_times_horizon: int) -> None:
        self._num_times_horizon = num_times_horizon

    # ----------------------- #
    # Property: currency_unit #
    # ----------------------- #
    @property
    def currency_unit(self) -> CurrencyUnit:
        """Currency unit used in the system. This is an optional parameter which
        defaults to CHF."""
        return self._currency_unit

    @currency_unit.setter
    def currency_unit(self, currency_unit: CurrencyUnit) -> None:
        self._currency_unit = currency_unit

    # --------------------- #
    # Property: length_unit #
    # --------------------- #
    @property
    def length_unit(self) -> LengthUnit:
        """Length unit used in the system. This is an optional parameter which
        defaults to meters."""
        return self._length_unit

    @length_unit.setter
    def length_unit(self, length_unit: LengthUnit) -> None:
        self._length_unit = length_unit

    # ------------------- #
    # Property: mass_unit #
    # ------------------- #
    @property
    def mass_unit(self) -> MassUnit:
        """Mass unit used in the system. This is an optional parameter which
        defaults to kilograms."""
        return self._mass_unit

    @mass_unit.setter
    def mass_unit(self, mass_unit: MassUnit) -> None:
        self._mass_unit = mass_unit

    # -------------------- #
    # Property: power_unit #
    # -------------------- #
    @property
    def power_unit(self) -> PowerUnit:
        """Power unit used in the system. This is an optional parameter which
        defaults to kilowatts."""
        return self._power_unit

    @power_unit.setter
    def power_unit(self, power_unit: PowerUnit) -> None:
        self._power_unit = power_unit

    # -------------------- #
    # Property: time_unit #
    # -------------------- #
    @property
    def time_unit(self) -> TimeUnit:
        """Time unit used in the system. This is an optional parameter which
        defaults to hours."""
        return self._time_unit

    @time_unit.setter
    def time_unit(self, time_unit: TimeUnit) -> None:
        self._time_unit = time_unit

    # ------------------------------- #
    # Secondary property: time_series #
    # ------------------------------- #
    @property
    def time_series(
        self,
    ) -> List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...], TimeSeries]]:
        """
        Time series profiles in the system. This is a list of tuples. Each
        list element has the following list entries: 1) ProfileKind of the
        profile. 2) Stage. 3) Tuple of string identifiers specific to the
        ProfileKind (usually ids excluding stage). 4) The TimeSeries itself

        :return: Time series of the energy system
        :rtype: List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...],
            TimeSeries]]:
        """
        all_series: List[
            Tuple[TimeSeriesKind, StageId, Tuple[str, ...], TimeSeries]
        ] = []
        all_series += self.imports.time_series
        all_series += self.exports.time_series
        all_series += self.demands.time_series
        all_series += self.load_shedding.time_series
        all_series += self.net_links.time_series
        all_series += self.solar_data.time_series
        all_series += self.conv_techs.time_series
        all_series += self.ebm_techs.time_series
        all_series += self.hp_techs.time_series
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
        Set the value for a time series in the energy system data. The time
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
        self.imports.set_time_series_val(kind, s, ids, t, value)
        self.exports.set_time_series_val(kind, s, ids, t, value)
        self.demands.set_time_series_val(kind, s, ids, t, value)
        self.load_shedding.set_time_series_val(kind, s, ids, t, value)
        self.net_links.set_time_series_val(kind, s, ids, t, value)
        self.solar_data.set_time_series_val(kind, s, ids, t, value)
        self.conv_techs.set_time_series_val(kind, s, ids, t, value)
        self.ebm_techs.set_time_series_val(kind, s, ids, t, value)
        self.hp_techs.set_time_series_val(kind, s, ids, t, value)

    # ------------------------ #
    # Heuristical limit values #
    # ------------------------ #
    def get_heur_limit_max_in(self, s: StageId, h: HubId, e: EcId) -> Value:
        """
        Get a heuristically determined maximal limit value for an inflow stream into a
        balance node. This value is currently calculated solely depending on the demand
        data, and an exception will be thrown if insufficient demand data exists to
        determine a value.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: Carrier
        :type e: EcId
        :return: Maximal inflow limit value (time-independent)
        :rtype: Value
        """
        if not self._heur_limits_ready:
            self._calc_heur_limits()
        return self._get_heur_limit_max_in(s, h, e)

    def get_heur_limit_max_out(self, s: StageId, h: HubId, e: EcId) -> Value:
        """
        Get a heuristically determined maximal limit value for an outflow stream from a
        balance node. This value is currently calculated solely depending on the demand
        data, and an exception will be thrown if insufficient demand data exists to
        determine a value.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: Carrier
        :type e: EcId
        :return: Maximal outflow limit value (time-independent)
        :rtype: Value
        """
        if not self._heur_limits_ready:
            self._calc_heur_limits()
        return self._get_heur_limit_max_out(s, h, e)

    def get_heur_limit_max_sum_in(self, s: StageId, h: HubId, e: EcId) -> Value:
        """
        Get a heuristically determined maximal limit value for the sum of all inflow
        streams into a balance node over the time horizon. This value is currently
        calculated solely depending on the demand data, and an exception will be
        thrown if insufficient demand data exists to determine a value.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: Carrier
        :type e: EcId
        :return: Maximal horizon-sum over inflow limit values
        :rtype: Value
        """
        if not self._heur_limits_ready:
            self._calc_heur_limits()
        return self._get_heur_limit_max_sum_in(s, h, e)

    def get_heur_limit_max_sum_out(self, s: StageId, h: HubId, e: EcId) -> Value:
        """
        Get a heuristically determined maximal limit value for the sum of all outflow
        streams from a balance node over the time horizon. This value is currently
        calculated solely depending on the demand data, and an exception will be
        thrown if insufficient demand data exists to determine a value.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: Carrier
        :type e: EcId
        :return: Maximal horizon-sum over outflow limit values
        :rtype: Value
        """
        if not self._heur_limits_ready:
            self._calc_heur_limits()
        return self._get_heur_limit_max_sum_out(s, h, e)

    def _get_heur_limit_max_in(self, s: StageId, h: HubId, e: EcId) -> Value:
        if (s, h, e) in self._heur_limit_max_in_sh:
            return self._heur_limit_max_in_sh[s, h, e]
        if e in self._heur_limit_max_in:
            return self._heur_limit_max_in[e]
        ec_unit = self.ecs.get_unit(e)
        max_in_vals = (
            self._heur_limit_max_in[e_]
            for e_ in self._heur_limit_max_in
            if ec_unit.same_type_as(self.ecs.get_unit(e_))
        )
        max_in = max(max_in_vals, default=None)
        if max_in is not None and max_in.is_finite:
            return max_in
        return self.ecs.get_heuristic_max(e)

    def _get_heur_limit_max_out(self, s: StageId, h: HubId, e: EcId) -> Value:
        if (s, h, e) in self._heur_limit_max_out_sh:
            return self._heur_limit_max_out_sh[s, h, e]
        if e in self._heur_limit_max_out:
            return self._heur_limit_max_out[e]
        ec_unit = self.ecs.get_unit(e)
        max_out_vals = (
            self._heur_limit_max_out[e_]
            for e_ in self._heur_limit_max_out
            if ec_unit.same_type_as(self.ecs.get_unit(e_))
        )
        max_out = max(max_out_vals, default=None)
        if max_out is not None and max_out.is_finite:
            return max_out
        return self.ecs.get_heuristic_max(e)

    def _get_heur_limit_max_sum_in(self, s: StageId, h: HubId, e: EcId) -> Value:
        if (s, h, e) in self._heur_limit_max_sum_in_sh:
            return self._heur_limit_max_sum_in_sh[s, h, e]
        if e in self._heur_limit_max_sum_in:
            return self._heur_limit_max_sum_in[e]
        ec_unit = self.ecs.get_unit(e)
        max_sum_in_vals = (
            self._heur_limit_max_sum_in[e_]
            for e_ in self._heur_limit_max_sum_in
            if ec_unit.same_type_as(self.ecs.get_unit(e_))
        )
        max_sum_in = max(max_sum_in_vals, default=None)
        if max_sum_in is not None and max_sum_in.is_finite:
            return max_sum_in
        heur_sum_max = self.ecs.get_heuristic_sum_max(e)
        if heur_sum_max is not None and heur_sum_max.is_finite:
            return heur_sum_max
        return self.ecs.get_heuristic_max(e) * Value(
            self.times.num_horizon_ts, unit=TimeUnit.H
        )

    def _get_heur_limit_max_sum_out(self, s: StageId, h: HubId, e: EcId) -> Value:
        if (s, h, e) in self._heur_limit_max_sum_out_sh:
            return self._heur_limit_max_sum_out_sh[s, h, e]
        if e in self._heur_limit_max_sum_out:
            return self._heur_limit_max_sum_out[e]
        ec_unit = self.ecs.get_unit(e)
        max_sum_out_vals = (
            self._heur_limit_max_sum_out[e_]
            for e_ in self._heur_limit_max_sum_out
            if ec_unit.same_type_as(self.ecs.get_unit(e_))
        )
        max_sum_out = max(max_sum_out_vals, default=None)
        if max_sum_out is not None and max_sum_out.is_finite:
            return max_sum_out
        heur_sum_max = self.ecs.get_heuristic_sum_max(e)
        if heur_sum_max is not None and heur_sum_max.is_finite:
            return heur_sum_max
        return self.ecs.get_heuristic_max(e) * Value(
            self.times.num_horizon_ts, unit=TimeUnit.H
        )

    def _calc_heur_limits(self) -> None:
        mult = MULT_HEUR_LIMIT_FROM_DEMAND
        mult_sum = MULT_HEUR_SUM_LIMIT_FROM_DEMAND
        for s, h, e in itertools.product(
            self.stages.ids,
            self.hubs.ids,
            self.ecs.ids,
        ):
            if (s, h, e) in self.demands.profile_tuples:
                dem_prof = self.demands.get_demand_profile(s, h, e)
                max_dem = dem_prof.max
                sum_dem = sum(
                    Value(self.times.get_weight(s, t), unit=TimeUnit.H)  # Bit of a hack
                    * dem_prof.get_value(t)
                    for t in self.times.ids
                )
                assert isinstance(sum_dem, Value)
                if max_dem.is_finite:
                    self._heur_limit_max_in_sh[s, h, e] = mult * max_dem
                    self._heur_limit_max_out_sh[s, h, e] = mult * max_dem
                if sum_dem.is_finite:
                    self._heur_limit_max_sum_in_sh[s, h, e] = mult_sum * sum_dem
                    self._heur_limit_max_sum_out_sh[s, h, e] = mult_sum * sum_dem

        for e in self.ecs.ids:
            max_in_vals = (
                self._heur_limit_max_in_sh[s, h, e_]
                for (s, h, e_) in self._heur_limit_max_in_sh
                if e == e_
            )
            max_out_vals = (
                self._heur_limit_max_out_sh[s, h, e_]
                for (s, h, e_) in self._heur_limit_max_out_sh
                if e == e_
            )
            max_sum_in_vals = (
                self._heur_limit_max_sum_in_sh[s, h, e_]
                for (s, h, e_) in self._heur_limit_max_sum_in_sh
                if e == e_
            )
            max_sum_out_vals = (
                self._heur_limit_max_sum_out_sh[s, h, e_]
                for (s, h, e_) in self._heur_limit_max_sum_out_sh
                if e == e_
            )
            heur_limit_max_in = max(max_in_vals, default=None)
            heur_limit_max_out = max(max_out_vals, default=None)
            heur_limit_max_sum_in = max(max_sum_in_vals, default=None)
            heur_limit_max_sum_out = max(max_sum_out_vals, default=None)
            if heur_limit_max_in is not None and heur_limit_max_in.is_finite:
                self._heur_limit_max_in[e] = heur_limit_max_in
            if heur_limit_max_out is not None and heur_limit_max_out.is_finite:
                self._heur_limit_max_out[e] = heur_limit_max_out
            if heur_limit_max_sum_in is not None and heur_limit_max_sum_in.is_finite:
                self._heur_limit_max_sum_in[e] = heur_limit_max_sum_in
            if heur_limit_max_sum_out is not None and heur_limit_max_sum_out.is_finite:
                self._heur_limit_max_sum_out[e] = heur_limit_max_sum_out

        self._heur_limits_ready = True

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self) -> None:
        """
        Validate all energy system data in this object. Apart from
        sense-checking energy system parameter in terms of quantity, this
        includes triggering the validation routines of all data classes
        contained in the module.
        """
        start_time = datetime.now()
        logging.log("Starting data validation ...", module=LOG_MODULE_STR)
        self._validate_self()
        self._validate_modules()
        elapsed = datetime.now() - start_time
        logging.log(
            f"Finished data validation. Elapsed time: {int(elapsed.total_seconds())}s",
            module=LOG_MODULE_STR,
        )

    def _validate_self(self) -> None:
        self._validate_trl_threshold()
        self._validate_interest_rate_def()
        self._validate_num_times_horizon()

    def _validate_trl_threshold(self) -> None:
        if self._trl_threshold is None:
            return
        if self._trl_threshold.is_negative:
            msg = f"{self._trl_threshold} = trl_threshold < 0"
            logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_interest_rate_def(self) -> None:
        if self._interest_rate_def is None:
            return
        if self._interest_rate_def.is_negative:
            msg = f"{self._interest_rate_def} = interest_rate_def < 0"
            raise exceptions.DataException(
                ExceptionKey.INTERESTRATEDEF_VAL.value, [], msg, module=LOG_MODULE_STR
            )

    def _validate_num_times_horizon(self) -> None:
        if self._num_times_horizon is None:
            return
        if self._num_times_horizon <= 0:
            msg = f"{self._num_times_horizon} = num_times_horizon <= 0"
            raise exceptions.DataException(
                ExceptionKey.NUMTIMESHORIZON_VAL.value, [], msg, module=LOG_MODULE_STR
            )

    def _validate_modules(self) -> None:
        self.stages.validate()
        self.hubs.validate()
        self.ecs.validate()
        self.times.validate(self.stages)
        self.net_links.validate(self.stages, self.hubs, self.ecs, self.times)
        self.imports.validate(self.stages, self.hubs, self.ecs, self.times)
        self.exports.validate(self.stages, self.hubs, self.ecs, self.times)
        self.demands.validate(self.stages, self.hubs, self.ecs, self.times)
        self.load_shedding.validate(
            self.stages, self.hubs, self.ecs, self.demands, self.times
        )
        self.load_shifting.validate(
            self.stages, self.hubs, self.ecs, self.demands, self.times
        )
        self.techs.validate(self.stages, self.hubs)
        self.stor_techs.validate(self.stages, self.hubs, self.ecs, self.techs)
        self.ebm_techs.validate(
            self.stages, self.hubs, self.techs, self.ecs, self.times
        )
        self.conv_techs.validate(
            self.stages, self.hubs, self.ecs, self.techs, self.times
        )
        self.solar_data.validate(self.stages, self.hubs, self.ecs, self.times)
        self.solar_techs.validate(
            self.stages,
            self.hubs,
            self.imports,
            self.techs,
            self.conv_techs,
            self.solar_data,
        )
        self.hp_techs.validate(self.stages, self.hubs, self.ecs, self.techs, self.times)
        self.ates_data.validate(self.stages, self.hubs, self.times)
        self.ates_techs.validate(
            self.stages, self.hubs, self.techs, self.ecs, self.ates_data, self.times
        )
        self.net_techs.validate(self.stages, self.net_links, self.ecs)
        self.self_sufficiency.validate(self.ecs, self.imports, self.exports)
