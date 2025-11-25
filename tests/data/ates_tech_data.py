"""
ATES technology data module
"""

import collections
import math
from enum import Enum
from typing import Dict, List, Set, Tuple

from scipy.special import expi

from ehubx.core import common, logging
from ehubx.data import exceptions
from ehubx.data.ates_data import AtesData, AtesScheduleId
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.index import Index
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.time_data import TimeId, Times
from ehubx.data.time_series import TimeSeries
from ehubx.data.unit import (
    CurrencyUnit,
    DimlessUnit,
    LengthUnit,
    MassUnit,
    PowerUnit,
    TemperatureUnit,
    TimeUnit,
    Unit,
)
from ehubx.data.value import Value


class WellPairAreaCalcMethod(Enum):
    """Method to calculate the total thermally affected area of a well pair"""

    TWOCIRCLES = "two circles"
    """Area is calculated as the area of the two circles defined by the
    thermal radii"""

    SMALLESTRECTANGLE = "smallest rectangle"
    """Area is calculated as the area of the smallest rectangle that contains
    both circles defined by the thermal radii"""


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the ATES technology data
    module
    """

    ID_ADD = "adding to 'ids' of AtesTechs"
    ID_REMOVE = "removing from 'ids' of AtesTechs"
    ID_VAL = "validating 'ids' of AtesTechs"
    ECEL_SET = "setting 'ec_el' of AtesTechs"
    ECEL_GET = "getting 'ec_el' from AtesTechs"
    ECEL_VAL = "validating 'ec_el' of AtesTechs"
    ECHT_SET = "setting 'ec_ht' of AtesTechs"
    ECHT_GET = "getting 'ec_ht' from AtesTechs"
    ECHT_VAL = "validating 'ec_ht' of AtesTechs"
    ECCO_SET = "setting 'ec_co' of AtesTechs"
    ECCO_GET = "getting 'ec_co' from AtesTechs"
    ECCO_VAL = "validating 'ec_co' of AtesTechs"
    ECS_VAL = "validating ecs of AtesTechs"
    DENSITYFLUID_SET = "setting 'density_fluid' of AtesTechs"
    DENSITYFLUID_GET = "getting 'density_fluid' from AtesTechs"
    DENSITYFLUID_VAL = "validating 'density_fluid' of AtesTechs"
    SPECIFICHEATCAPFLUID_SET = "setting 'specific_heat_capacity_fluid' of AtesTechs"
    SPECIFICHEATCAPFLUID_GET = "getting 'specific_heat_capacity_fluid' from AtesTechs"
    SPECIFICHEATCAPFLUID_VAL = "validating 'specific_heat_capacity_fluid' of AtesTechs"
    WELLRADIUS_SET = "setting 'well_radius' of AtesTechs"
    WELLRADIUS_GET = "getting 'well_radius' from AtesTechs"
    WELLRADIUS_VAL = "validating 'well_radius' of AtesTechs"
    WELLPAIRSMAX_SET = "setting 'well_pairs_max' of AtesTechs"
    WELLPAIRSMAX_GET = "getting 'well_pairs_max' from AtesTechs"
    WELLPAIRSMAX_VAL = "validating 'well_pairs_max' of AtesTechs"
    WELLPAIRSMIN_SET = "setting 'well_pairs_min' of AtesTechs"
    WELLPAIRSMIN_GET = "getting 'well_pairs_min' from AtesTechs"
    WELLPAIRSMIN_VAL = "validating 'well_pairs_min' of AtesTechs"
    WELLPAIRSMINMAX_VAL = (
        "validating 'well_pairs_min' against 'well_pairs_max' of AtesTechs"
    )
    MAXPUMPRATEWARM_SET = "setting 'max_pump_rate_per_warm_well of AtesAtechs"
    MAXPUMPRATEWARM_GET = "getting 'max_pump_rate_per_warm_well from AtesAtechs"
    MAXPUMPRATEWARM_VAL = "validating 'max_pump_rate_per_warm_well of AtesAtechs"
    MAXPUMPRATECOLD_SET = "setting 'max_pump_rate_per_cold_well of AtesAtechs"
    MAXPUMPRATECOLD_GET = "getting 'max_pump_rate_per_cold_well from AtesAtechs"
    MAXPUMPRATECOLD_VAL = "validating 'max_pump_rate_per_cold_well of AtesAtechs"
    THERMALRADIUSWARM_SET = "setting 'thermal_radius_per_warm_well' of AtesTechs"
    THERMALRADIUSWARM_GET = "getting 'thermal_radius_per_warm_well' from AtesTechs"
    THERMALRADIUSWARM_VAL = "validating 'thermal_radius_per_warm_well' of AtesTechs"
    THERMALRADIUSCOLD_SET = "setting 'thermal_radius_per_cold_well' of AtesTechs"
    THERMALRADIUSCOLD_GET = "getting 'thermal_radius_per_cold_well' from AtesTechs"
    THERMALRADIUSCOLD_VAL = "validating 'thermal_radius_per_cold_well' of AtesTechs"
    WELLPAIRAREACALCMETHOD_SET = "setting 'well_pair_area_calc_method of AtesTechs"
    WELLPAIRAREACALCMETHOD_GET = "getting 'well_pair_area_calc_method from AtesTechs"
    WELLPAIRAREACALCMETHOD_VAL = "validating 'well_pair_area_calc_method of AtesTechs"
    ELECPERENERGYHEAT_SET = "setting 'elec_per_energy_heat' of AtesTechs"
    ELECPERENERGYHEAT_GET = "getting 'elec_per_energy_heat' from AtesTechs"
    ELECPERENERGYHEAT_VAL = "validating 'elec_per_energy_heat' of AtesTechs"
    ELECPERENERGYCOOL_SET = "setting 'elec_per_energy_cool' of AtesTechs"
    ELECPERENERGYCOOL_GET = "getting 'elec_per_energy_cool' from AtesTechs"
    ELECPERENERGYCOOL_VAL = "validating 'elec_per_energy_cool' of AtesTechs"
    ELECPERFLOWHEAT_SET = "setting 'elec_per_flow_heat' of AtesTechs"
    ELECPERFLOWHEAT_GET = "getting 'elec_per_flow_heat' from AtesTechs"
    ELECPERFLOWHEAT_VAL = "validating 'elec_per_flow_heat' of AtesTechs"
    ELECPERFLOWCOOL_SET = "setting 'elec_per_flow_cool' of AtesTechs"
    ELECPERFLOWCOOL_GET = "getting 'elec_per_flow_cool' from AtesTechs"
    ELECPERFLOWCOOL_VAL = "validating 'elec_per_flow_cool' of AtesTechs"
    MAXHEATOVERCOOL_SET = "setting 'max_heat_over_cool' of AtesTechs"
    MAXHEATOVERCOOL_GET = "getting 'max_heat_over_cool' from AtesTechs"
    MAXHEATOVERCOOL_VAL = "validating 'max_heat_over_cool' of AtesTechs"
    MAXCOOLOVERHEAT_SET = "setting 'max_cool_over_heat' of AtesTechs"
    MAXCOOLOVERHEAT_GET = "getting 'max_cool_over_heat' from AtesTechs"
    MAXCOOLOVERHEAT_VAL = "validating 'max_cool_over_heat' of AtesTechs"
    MAXHEATOVERCOOLMAXCOOLOVERHEAT_VAL = (
        "validating 'max_heat_over_cool' against 'max_cool_over_heat' of AtesTechs"
    )
    CAPEXPERWELLPAIR_SET = "setting 'capex_per_well_pair' of AtesTechs"
    CAPEXPERWELLPAIR_GET = "getting 'capex_per_well_pair' from AtesTechs"
    CAPEXPERWELLPAIR_VAL = "validating 'capex_per_well_pair' of AtesTechs"
    OPEXPERWELLPAIR_SET = "setting 'opex_per_well_pair' of AtesTechs"
    OPEXPERWELLPAIR_GET = "getting 'opex_per_well_pair' from AtesTechs"
    OPEXPERWELLPAIR_VAL = "validating 'opex_per_well_pair' of AtesTechs"
    CO2PERWELLPAIR_SET = "setting 'co2_per_well_pair' of AtesTechs"
    CO2PERWELLPAIR_GET = "getting 'co2_per_well_pair' from AtesTechs"
    CO2PERWELLPAIR_VAL = "validating 'co2_per_well_pair' of AtesTechs"
    SCHEDULEEXISTENCE_VAL = "validating existence of schedule for AtesTechs"
    AVAILABILITY_SET = "setting 'availability' of AtesTechs"
    AVAILABILITY_DEFSET = "setting default 'availability' of AtesTechs"
    AVAILABILITY_GET = "getting 'availability' from AtesTechs"
    AVAILABILITY_VAL = "validating 'availability' of AtesTechs"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/ates_tech"
"""String identifying the ATES technology data module for logging purposes"""


DEF_WELLPAIRAREACALCMETHOD: WellPairAreaCalcMethod = (
    WellPairAreaCalcMethod.SMALLESTRECTANGLE
)
"""The default area calculation method for a well pair"""

DEF_ELECPERFLOWHEAT: float = 0
"""Default value for parameter 'elec_per_flow_heat' in the ATES technology
data module"""

DEF_ELECPERFLOWCOOL: float = 0
"""Default value for parameter 'elec_per_flow_cool' in the ATES technology
data module"""

DEF_CAPEXPERWELLPAIR: float = 0
"""Default value for parameter 'capex_per_well_pair' in the ATES technology
data module"""

DEF_OPEXPERWELLPAIR: float = 0
"""Default value for parameter 'opex_per_well_pair' in the ATES technology
data module"""

DEF_CO2PERWELLPAIR: float = 0
"""Default value for parameter 'co2_per_well_pair' in the ATES technology
data module"""

DEF_WELLPAIRSMIN: float = 0
"""Default value for parameter 'well_pairs_min' in the ATES technology
data module"""

DEF_WELLPAIRSMAX: float = float("inf")
"""Default value for parameter 'well_pairs_max' in the ATES technology
data module"""

DEF_MAXHEATOVERCOOL: float = float("inf")
"""Default value for parameter 'max_heat_over_cool' in the ATES technology
data module"""

DEF_MAXCOOLOVERHEAT: float = float("inf")
"""Default value for parameter 'max_cool_over_heat' in the ATES technology
data module"""

DEF_AVAILABILITY: float = 1.0
"""Default value for parameter 'availability' in the ATES technology data module"""


class AtesTechs:
    """
    Class to hold ATES (Aquifer Thermal Energy Storage) data. Manages ATES
    technology ids, contains getters and setters for ATES technology parameters
    and validation methods to control data integrity
    """

    # ------------- #
    # Property: ids #
    # ------------- #
    @property
    def ids(self) -> Set[TechId]:
        """
        Set of known ATES technology ids
        """
        return self._ids

    @property
    def ids_in_order(self) -> List[TechId]:
        """
        List of ATES tech ids in alphabetical order
        """
        ids = list(self.ids)
        ids.sort(key=lambda x: x.key)
        return ids

    def add_id(self, x: TechId) -> None:
        """
        Add a new ATES technology id

        :param x: Id to be added
        :type x: TechId
        """
        if x in self._ids:
            raise exceptions.DuplicateIdException(
                ExceptionKey.ID_ADD.value, x, module=LOG_MODULE_STR
            )
        self._ids.add(x)

    # --------------- #
    # Property: ec_el #
    # --------------- #
    def get_ec_el(self, x: TechId) -> EcId:
        """
        Get the electricity ec powering the well pumps. This is a mandatory
        parameter.

        :param x: ATES technology
        :type x: TechId
        :return: Electricity ec
        :rtype: EcId
        """
        self._check_id(x, ExceptionKey.ECEL_GET)
        if x not in self._ec_el:
            raise exceptions.MissingIdException(
                ExceptionKey.ECEL_GET.value, x, module=LOG_MODULE_STR
            )
        return self._ec_el[x]

    def set_ec_el(self, x: TechId, e: EcId, ec_unit: Unit) -> None:
        """
        Set the electricity ec powering the well pumps. This is a mandatory
        parameter.

        :param x: ATES technology
        :type x: TechId
        :param e: Electricity ec
        :type e: EcId
        :param ec_unit: Unit of the ec
        :type ec_unit: Unit
        """
        self._check_id(x, ExceptionKey.ECEL_SET)
        self._ec_el[x] = e
        energy_unit = PowerUnit.KW * TimeUnit.H
        if not ec_unit.same_type_as(energy_unit):
            raise exceptions.DataException(
                ExceptionKey.ECEL_SET.value,
                [x, e],
                f"Received {ec_unit} for the electricity carriwer of ATES  technology "
                f"'{x}' but only units like {energy_unit} are valid",
                module=LOG_MODULE_STR,
            )

    # --------------- #
    # Property: ec_ht #
    # --------------- #
    def get_ec_ht(self, x: TechId) -> EcId:
        """
        Get the ec for output heating energy, i.e. the energy that is extracted
        from the warm well in the warm-to-cold pumping cycle.

        :param x: ATES technology
        :type x: TechId
        :return: Heating ec
        :rtype: EcId
        """
        self._check_id(x, ExceptionKey.ECHT_GET)
        if x not in self._ec_ht:
            raise exceptions.MissingIdException(
                ExceptionKey.ECHT_GET.value, x, module=LOG_MODULE_STR
            )
        return self._ec_ht[x]

    def set_ec_ht(self, x: TechId, e: EcId, ec_unit: Unit) -> None:
        """
        Set the ec for output heating energy, i.e. the energy that is extracted
        from the warm well in the warm-to-cold pumping cycle.

        :param x: ATES technology
        :type x: TechId
        :param e: Heating ec
        :type e: EcId
        :param ec_unit: Unit of the ec
        :type ec_unit: Unit
        """
        self._check_id(x, ExceptionKey.ECHT_SET)
        self._ec_ht[x] = e
        energy_unit = PowerUnit.KW * TimeUnit.H
        if not ec_unit.same_type_as(energy_unit):
            raise exceptions.DataException(
                ExceptionKey.ECHT_SET.value,
                [x, e],
                f"Received {ec_unit} for the heating carrier of ATES technology "
                f"'{x}' but only units like {energy_unit} are valid",
                module=LOG_MODULE_STR,
            )

    # --------------- #
    # Property: ec_co #
    # --------------- #
    def get_ec_co(self, x: TechId) -> EcId:
        """
        Get the ec for output cooling energy, i.e. the energy that is extracted
        from the cold well in the cold-to-warm pumping cycle.

        :param x: ATES technology
        :type x: TechId
        :return: Cooling ec
        :rtype: EcId
        """
        self._check_id(x, ExceptionKey.ECCO_GET)
        if x not in self._ec_co:
            raise exceptions.MissingIdException(
                ExceptionKey.ECCO_GET.value, x, module=LOG_MODULE_STR
            )
        return self._ec_co[x]

    def set_ec_co(self, x: TechId, e: EcId, ec_unit: Unit) -> None:
        """
        Set the ec for output cooling energy, i.e. the energy that is extracted
        from the cold well in the cold-to-warm pumping cycle.

        :param x: ATES technology
        :type x: TechId
        :param e: Cooling ec
        :type e: EcId
        :param ec_unit: Unit of the ec
        :type ec_unit: Unit
        """
        self._check_id(x, ExceptionKey.ECCO_SET)
        self._ec_co[x] = e
        energy_unit = PowerUnit.KW * TimeUnit.H
        if not ec_unit.same_type_as(energy_unit):
            raise exceptions.DataException(
                ExceptionKey.ECCO_SET.value,
                [x, e],
                f"Received {ec_unit} for the cooling carrier of ATES technology "
                f"'{x}' but only units like {energy_unit} are valid",
                module=LOG_MODULE_STR,
            )

    # ---------------------------- #
    # Property: in_ecs and out_ecs #
    # ---------------------------- #
    def get_in_ecs(self, x: TechId) -> Set[EcId]:
        """
        Get all input ecs for an ATES technology.

        :param x: ATES technology
        :type x: TechId
        :return: Input ecs
        :rtype: Set[EcId]
        """
        return {self.get_ec_el(x)}

    def get_out_ecs(self, x: TechId) -> Set[EcId]:
        """
        Get all output ecs for an ATES technology.

        :param x: ATES technology
        :type x: TechId
        :return: Output ecs
        :rtype: Set[EcId]
        """
        return {self.get_ec_ht(x), self.get_ec_co(x)}

    # ----------------------- #
    # Property: density_fluid #
    # ----------------------- #
    def get_density_fluid(self, x: TechId) -> Value:
        """
        Get the density of the fluid stored in the ATES wells. This is a
        mandatory parameter.

        :param x: ATES technology
        :type x: TechId
        :return: Fluid density
        :rtype: Value
        """
        exc_key = ExceptionKey.DENSITYFLUID_GET
        self._check_id(x, exc_key)
        if x not in self._density_fluid:
            raise exceptions.MissingIdException(exc_key.value, x, module=LOG_MODULE_STR)
        return self._density_fluid[x]

    def set_density_fluid(self, x: TechId, density_fluid: Value) -> None:
        """
        Set the density of the fluid stored in the ATES wells. This is a
        mandatory parameter.

        :param x: ATES technology
        :type x: TechId
        :param density_fluid: Fluid density
        :type density_fluid: Value
        """
        self._check_id(x, ExceptionKey.DENSITYFLUID_SET)
        expected_unit = MassUnit.KG / (LengthUnit.M**3)
        if not density_fluid.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.DENSITYFLUID_SET.value,
                [x],
                f"Unit of density_fluid[{x}] = {density_fluid} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._density_fluid[x] = density_fluid

    # -------------------------------------- #
    # Property: specific_heat_capacity_fluid #
    # -------------------------------------- #
    def get_specific_heat_capacity_fluid(self, x: TechId) -> Value:
        """
        Get the specific heat capacity of the fluid stored in the ATES wells.
        This is a mandatory parameter.

        :param x: ATES technology
        :type x: TechId
        :return: Fluid specific heat capacity
        :rtype: Value
        """
        exc_key = ExceptionKey.SPECIFICHEATCAPFLUID_GET
        self._check_id(x, exc_key)
        if x not in self._specific_heat_capacity_fluid:
            raise exceptions.MissingIdException(exc_key.value, x, module=LOG_MODULE_STR)
        return self._specific_heat_capacity_fluid[x]

    def set_specific_heat_capacity_fluid(
        self, x: TechId, spec_heat_cap_fluid: Value
    ) -> None:
        """
        Set the specific heat capacity of the fluid stored in the ATES wells.
        This is a mandatory parameter.

        :param x: ATES technology
        :type x: TechId
        :param spec_heat_cap_fluid: Fluid specific heat capacity
        :type spec_heat_cap_fluid: Value
        """
        self._check_id(x, ExceptionKey.SPECIFICHEATCAPFLUID_SET)
        expected_unit = (PowerUnit.KW * TimeUnit.H) / (MassUnit.KG * TemperatureUnit.K)
        if not spec_heat_cap_fluid.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.SPECIFICHEATCAPFLUID_SET.value,
                [x],
                f"Unit of spec_heat_cap_fluid[{x}] = {spec_heat_cap_fluid} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._specific_heat_capacity_fluid[x] = spec_heat_cap_fluid

    # --------------------- #
    # Property: well_radius #
    # --------------------- #
    def get_well_radius(self, x: TechId) -> Value:
        """
        Get the radius of a well. This is a mandatory parameter if the
        parameters 'max_pump_rate_per_warm_well' or
        'max_pump_rate_per_cold_well' are not specified, since the well radius
        is then used to calculate these rates.

        :param x: ATES technology
        :type x: TechId
        :return: Well radius
        :rtype: Value
        """
        exc_key = ExceptionKey.WELLRADIUS_GET
        self._check_id(x, exc_key)
        if x not in self._well_radius:
            raise exceptions.MissingIdException(exc_key.value, x, module=LOG_MODULE_STR)
        return self._well_radius[x]

    def set_well_radius(self, x: TechId, well_radius: Value) -> None:
        """
        Set the radius of a well. This is a mandatory parameter if the
        parameters 'max_pump_rate_per_warm_well' or
        'max_pump_rate_per_cold_well' are not specified, since the well radius
        is then used to calculate these rates.

        :param x: ATES technology
        :type x: TechId
        :param well_radius: Well radius
        :type well_radius: Value
        """
        self._check_id(x, ExceptionKey.WELLRADIUS_SET)
        expected_unit = LengthUnit.M
        if not well_radius.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.DENSITYFLUID_SET.value,
                [x],
                f"Unit of well_radius[{x}] = {well_radius} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._well_radius[x] = well_radius

    # ------------------------ #
    # Property: well_pairs_min #
    # ------------------------ #
    def get_well_pairs_min(
        self, s: StageId, h: HubId, x: TechId, i: AtesScheduleId
    ) -> Value:
        """
        Get the minimum number of allowed well pairs for an ATES technolog in a stage,
        hub, and a specific ATES schedule. This is a an optional parameter with a
        default value of 0.
        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: ATES technology
        :type x: TechId
        :param i: ATES schedule
        :type i: AtesScheduleId
        :return: Minimum number of well pairs
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.WELLPAIRSMIN_GET)
        return self._well_pairs_min.get((s, h, x, i), Value(DEF_WELLPAIRSMIN))

    def set_well_pairs_min(
        self, s: StageId, h: HubId, x: TechId, i: AtesScheduleId, well_pairs_min: Value
    ) -> None:
        """
        Set the minimum number of allowed well pairs for an ATES technolog in a stage,
        hub, and a specific ATES schedule. This is a an optional parameter with a
        default value of 0.
        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: ATES technology
        :type x: TechId
        :param i: ATES schedule
        :type i: AtesScheduleId
        :param well_pairs_min: Minimum number of well pairs
        :type well_pairs_min: Value
        """
        self._check_id(x, ExceptionKey.WELLPAIRSMIN_SET)
        expected_unit = DimlessUnit()
        if not well_pairs_min.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.WELLPAIRSMIN_SET.value,
                [s, h, x, i],
                f"Unit of well_pairs_min[{s}, {h}, {x}, {i}] = "
                f"{well_pairs_min} does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._well_pairs_min[s, h, x, i] = well_pairs_min

    # ------------------------ #
    # Property: well_pairs_max #
    # ------------------------ #
    def get_well_pairs_max(
        self, s: StageId, h: HubId, x: TechId, i: AtesScheduleId
    ) -> Value:
        """
        Get the maximal number of allowed well pairs for an ATES technolog in a stage,
        hub, and a specific ATES schedule. This is a an optional parameter with a
        default value of infinity.
        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: ATES technology
        :type x: TechId
        :param i: ATES schedule
        :type i: AtesScheduleId
        :return: Maximum number of well pairs
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.WELLPAIRSMAX_GET)
        return self._well_pairs_max.get((s, h, x, i), Value(DEF_WELLPAIRSMAX))

    def set_well_pairs_max(
        self, s: StageId, h: HubId, x: TechId, i: AtesScheduleId, well_pairs_max: Value
    ) -> None:
        """
        Set the minimum number of allowed well pairs for an ATES technolog in a stage,
        hub, and a specific ATES schedule. This is a an optional parameter with a
        default value of 0.
        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: ATES technology
        :type x: TechId
        :param i: ATES schedule
        :type i: AtesScheduleId
        :param well_pairs_max: Maximum number of well pairs
        :type well_pairs_max: Value
        """
        self._check_id(x, ExceptionKey.WELLPAIRSMAX_SET)
        expected_unit = DimlessUnit()
        if not well_pairs_max.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.WELLPAIRSMIN_SET.value,
                [s, h, x, i],
                f"Unit of well_pairs_max[{s}, {h}, {x}, {i}] = "
                f"{well_pairs_max} does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._well_pairs_max[s, h, x, i] = well_pairs_max

    # ------------------------------------- #
    # Property: max_pump_rate_per_warm_well #
    # ------------------------------------- #
    def get_max_pump_rate_per_warm_well(
        self,
        s: StageId,
        h: HubId,
        x: TechId,
        i: AtesScheduleId,
        ates_data: AtesData,
        times: Times,
    ) -> Value:
        """
        Get the maximal rate at which fluid can be pumped from a warm well.
        This parameter is optional but if is not set, the following
        parameters need to be available instead to compute the rate:
        well_radius, storativity_aquifer (AtesData),
        hydraulic_transmissivity_aquifer (AtesData), and max_drawdown
        (AtesData).

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: ATES tech
        :type x: TechId
        :param i: ATES schedule
        :type i: AtesScheduleId
        :param ates_data: AtesData
        :type ates_data: AtesData
        :param times: Times
        :type times: Times
        :return: Maximal pump rate from a single warm well
        :rtype: Value
        """
        exc_key = ExceptionKey.MAXPUMPRATEWARM_GET
        self._check_id(x, exc_key)
        # Prefer returning a set value
        if (s, h, x, i) in self._max_pump_rate_per_warm_well:
            return self._max_pump_rate_per_warm_well[s, h, x, i]
        # Use Theis equation if value is not set
        storativity_aq = ates_data.get_storativity_aquifer(h)
        hydr_transmiss_aq = ates_data.get_hydraulic_transmissivity_aquifer(h)
        pumping_duration = ates_data.get_phase_duration_w2c(h, i, times)
        max_drawdown = ates_data.get_max_drawdown(h)
        well_radius = self.get_well_radius(x)
        max_pump_rate = _calc_max_pump_rate_from_theis_equation(
            max_drawdown,
            well_radius,
            pumping_duration,
            hydr_transmiss_aq,
            storativity_aq,
        )
        return max_pump_rate

    def set_max_pump_rate_per_warm_well(
        self,
        s: StageId,
        h: HubId,
        x: TechId,
        i: AtesScheduleId,
        max_pump_rate_warm: Value,
    ) -> None:
        """
        Set the maximal rate at which fluid can be pumped from a warm well.
        This parameter is optional but if is not set, the following parameters
        need to be available instead to compute the rate: well_radius,
        storativity_aquifer (AtesData), hydraulic_transmissivity_aquifer
        (AtesData), and max_drawdown (AtesData).

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: ATES tech
        :type x: TechId
        :param i: ATES schedule
        :type i: AtesScheduleId
        :param ates_data: AtesData
        :type ates_data: AtesData
        :param times: Times
        :type times: Times
        :param max_pump_rate_warm: Maximal pump rate from a single warm well
        :type max_pump_rate_warm: Value
        """
        self._check_id(x, ExceptionKey.MAXPUMPRATEWARM_SET)
        expected_unit = (LengthUnit.M**3) / TimeUnit.H
        if not max_pump_rate_warm.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.MAXPUMPRATEWARM_SET.value,
                [s, h, x, i],
                f"Unit of max_pump_rate_warm[{s}, {h}, {x}, {i}] = "
                f"{max_pump_rate_warm} does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._max_pump_rate_per_warm_well[s, h, x, i] = max_pump_rate_warm

    # ------------------------------------- #
    # Property: max_pump_rate_per_cold_well #
    # ------------------------------------- #
    def get_max_pump_rate_per_cold_well(
        self,
        s: StageId,
        h: HubId,
        x: TechId,
        i: AtesScheduleId,
        ates_data: AtesData,
        times: Times,
    ) -> Value:
        """
        Set the maximal rate at which fluid can be pumped from a cold well.
        This parameter is optional but if is not set, the following parameters
        need to be available instead to compute the rate: well_radius,
        storativity_aquifer (AtesData), hydraulic_transmissivity_aquifer
        (AtesData), and max_drawdown (AtesData).

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: ATES technology
        :type x: TechId
        :param i: ATES schedule
        :type i: AtesScheduleId
        :param ates_data: AtesData
        :type ates_data: AtesData
        :param times: Times
        :type times: Times
        :return: Maximal pump rate from a single cold well
        :rtype: Value
        """
        exc_key = ExceptionKey.MAXPUMPRATECOLD_GET
        self._check_id(x, exc_key)
        # Prefer returning a set value
        if (s, h, x, i) in self._max_pump_rate_per_cold_well:
            return self._max_pump_rate_per_cold_well[s, h, x, i]
        # Use Theis equation if value is not set
        storativity_aq = ates_data.get_storativity_aquifer(h)
        hydr_transmiss_aq = ates_data.get_hydraulic_transmissivity_aquifer(h)
        pumping_duration = ates_data.get_phase_duration_c2w(h, i, times)
        max_drawdown = ates_data.get_max_drawdown(h)
        well_radius = self.get_well_radius(x)
        max_pump_rate = _calc_max_pump_rate_from_theis_equation(
            max_drawdown,
            well_radius,
            pumping_duration,
            hydr_transmiss_aq,
            storativity_aq,
        )
        return max_pump_rate

    def set_max_pump_rate_per_cold_well(
        self,
        s: StageId,
        h: HubId,
        x: TechId,
        i: AtesScheduleId,
        max_pump_rate_cold: Value,
    ) -> None:
        """
        Set the maximal rate at which fluid can be pumped from a cold well.
        This parameter is optional but if is not set, the following parameters
        need to be available instead to compute the rate: well_radius,
        storativity_aquifer (AtesData), hydraulic_transmissivity_aquifer
        (AtesData), and max_drawdown (AtesData).

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: ATES technology
        :type x: TechId
        :param i: ATES schedule
        :type i: AtesScheduleId
        :param ates_data: AtesData
        :type ates_data: AtesData
        :param times: Times
        :type times: Times
        :return: Maximal pump rate from
        :param max_pump_rate_cold: Maximal pump rate from a single cold well
        :type max_pump_rate_cold: Value
        """
        self._check_id(x, ExceptionKey.MAXPUMPRATECOLD_SET)
        expected_unit = (LengthUnit.M**3) / TimeUnit.H
        if not max_pump_rate_cold.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.MAXPUMPRATECOLD_SET.value,
                [s, h, x, i],
                f"Unit of max_pump_rate_cold[{s}, {h}, {x}, {i}] = "
                f"{max_pump_rate_cold} does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._max_pump_rate_per_cold_well[s, h, x, i] = max_pump_rate_cold

    # -------------------------------------- #
    # Property: thermal_radius_per_warm_well #
    # -------------------------------------- #
    def get_thermal_radius_per_warm_well(
        self,
        s: StageId,
        h: HubId,
        x: TechId,
        i: AtesScheduleId,
        ates_data: AtesData,
        times: Times,
    ) -> Value:
        """
        Get the thermal radius for a warm well. The thermal radius is an
        approximation of the furthest distance from the well center at which
        the injection of warm fluid into the well still affects the
        underground thermal state. This parameter is optional but if not
        set, the following parameters need to be available instead to
        compute the thermal radius: specific_heat_capacity_fluid,
        max_pump_rate_per_cold_well, specific_heat_capacity_aquifer
        (AtesData), thickness_aquifer (AtesData), groundwater_velocity
        (AtesData).

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: ATES technology
        :type x: TechId
        :param i: ATES schedule
        :type i: AtesScheduleId
        :param ates_data: AtesData
        :type ates_data: AtesData
        :param times: Times
        :type times: Times
        :return: Thermal radius of warm well
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.THERMALRADIUSWARM_GET)
        # Return value directly if thermal radius is specifically set
        if (s, h, x, i) in self._thermal_radius_warm:
            return self._thermal_radius_warm[s, h, x, i]
        # Calculate value otherwise
        density_aq = ates_data.get_density_aquifer(h)
        sp_heat_cap_aq = ates_data.get_specific_heat_capacity_aquifer(h)
        density_fl = self.get_density_fluid(x)
        sp_heat_cap_fl = self.get_specific_heat_capacity_fluid(x)
        thickness_aq = ates_data.get_thickness_aquifer(h)
        injection_duration = ates_data.get_phase_duration_c2w(h, i, times)
        max_pump_rate = self.get_max_pump_rate_per_cold_well(
            s, h, x, i, ates_data, times
        )
        ground_velo = ates_data.get_groundwater_velocity(h)
        therm_rad = _calc_thermal_radius(
            density_aq,
            sp_heat_cap_aq,
            thickness_aq,
            ground_velo,
            density_fl,
            sp_heat_cap_fl,
            injection_duration,
            max_pump_rate,
        )
        return therm_rad

    def set_thermal_radius_per_warm_well(
        self,
        s: StageId,
        h: HubId,
        x: TechId,
        i: AtesScheduleId,
        thermal_radius_warm: Value,
    ) -> None:
        """
        Set the thermal radius for a warm well. The thermal radius is an
        approximation of the furthest distance from the well center at which
        the injection of warm fluid into the well still affects the underground
        thermal state. This parameter is optional but if not set, the following
        parameters need to be available instead to compute the thermal radius:
        specific_heat_capacity_fluid, max_pump_rate_per_cold_well,
        specific_heat_capacity_aquifer (AtesData), thickness_aquifer (AtesData)
        , groundwater_velocity (AtesData).

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: ATES technology
        :type x: TechId
        :param i: ATES schedule
        :type i: AtesScheduleId
        :param ates_data: AtesData
        :type ates_data: AtesData
        :param times: Times
        :type times: Times
        :param thermal_radius_warm: Thermal radius of warm well
        :type thermal_radius_warm: Value
        """
        self._check_id(x, ExceptionKey.THERMALRADIUSWARM_SET)
        expected_unit = LengthUnit.M
        if not thermal_radius_warm.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.THERMALRADIUSWARM_SET.value,
                [s, h, x, i],
                f"Unit of thermal_radius_warm[{s}, {h}, {x}, {i}] = "
                f"{thermal_radius_warm} does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._thermal_radius_warm[s, h, x, i] = thermal_radius_warm

    # -------------------------------------- #
    # Property: thermal_radius_per_cold_well #
    # -------------------------------------- #
    def get_thermal_radius_per_cold_well(
        self,
        s: StageId,
        h: HubId,
        x: TechId,
        i: AtesScheduleId,
        ates_data: AtesData,
        times: Times,
    ) -> Value:
        """
        Get the thermal radius for a cold well. The thermal radius is an
        approximation of the distance from the well center at which the
        injection of warm fluid into the well still affects the underground
        thermal state. This parameter is optional but if not set, the following
        parameters need to be available instead to compute the thermal radius:
        specific_heat_capacity_fluid, max_pump_rate_per_warm_well,
        specific_heat_capacity_aquifer (AtesData), thickness_aquifer (AtesData)
        , groundwater_velocity (AtesData).

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: ATES technology
        :type x: TechId
        :param i: ATES schedule
        :type i: AtesScheduleId
        :param ates_data: AtesData
        :type ates_data: AtesData
        :param times: Times
        :type times: Times
        :return: Thermal radius of a cold well
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.THERMALRADIUSCOLD_GET)
        # Return value directly if thermal radius is specifically set
        if (s, h, x, i) in self._thermal_radius_cold:
            return self._thermal_radius_cold[s, h, x, i]
        # Calculate value otherwise
        density_aq = ates_data.get_density_aquifer(h)
        sp_heat_cap_aq = ates_data.get_specific_heat_capacity_aquifer(h)
        thickness_aq = ates_data.get_thickness_aquifer(h)
        ground_velo = ates_data.get_groundwater_velocity(h)
        density_fl = self.get_density_fluid(x)
        sp_heat_cap_fl = self.get_specific_heat_capacity_fluid(x)
        injection_duration = ates_data.get_phase_duration_w2c(h, i, times)
        max_pump_rate = self.get_max_pump_rate_per_warm_well(
            s, h, x, i, ates_data, times
        )
        therm_rad = _calc_thermal_radius(
            density_aq,
            sp_heat_cap_aq,
            thickness_aq,
            ground_velo,
            density_fl,
            sp_heat_cap_fl,
            injection_duration,
            max_pump_rate,
        )
        return therm_rad

    def set_thermal_radius_per_cold_well(
        self,
        s: StageId,
        h: HubId,
        x: TechId,
        i: AtesScheduleId,
        thermal_radius_cold: Value,
    ) -> None:
        """
        Set the thermal radius for a cold well. The thermal radius is an
        approximation of the distance from the well center at which the
        injection of warm fluid into the well still affects the underground
        thermal state. This parameter is optional but if not set, the following
        parameters need to be available instead to compute the thermal radius:
        specific_heat_capacity_fluid, max_pump_rate_per_warm_well,
        specific_heat_capacity_aquifer (AtesData), thickness_aquifer (AtesData)
        , groundwater_velocity (AtesData).

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: ATES technology
        :type x: TechId
        :param i: ATES schedule
        :type i: AtesScheduleId
        :param ates_data: AtesData
        :type ates_data: AtesData
        :param times: Times
        :type times: Times
        :param thermal_radius_cold: Thermal radius of a cold well
        :type thermal_radius_cold: Value
        """
        self._check_id(x, ExceptionKey.THERMALRADIUSCOLD_SET)
        expected_unit = LengthUnit.M
        if not thermal_radius_cold.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.THERMALRADIUSCOLD_SET.value,
                [s, h, x, i],
                f"Unit of thermal_radius_cold[{s}, {h}, {x}, {i}] = "
                f"{thermal_radius_cold} does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._thermal_radius_cold[s, h, x, i] = thermal_radius_cold

    # ------------------------------------ #
    # Property: well_pair_area_calc_method #
    # ------------------------------------ #
    def get_well_pair_area_calc_method(self, x: TechId) -> WellPairAreaCalcMethod:
        """
        Get the method to calculate the total thermally affected area of a well
        pair. This is an optional parameter. If no calculation method is
        specified, the area will be determined by the smallest-rectangle
        method.

        :param x: ATES technology
        :type x: TechId
        :return: Well pair area calculation method
        :rtype: WellPairAreaCalcMethod
        """
        self._check_id(x, ExceptionKey.WELLPAIRAREACALCMETHOD_GET)
        return self._well_pair_area_calc_method.get(x, DEF_WELLPAIRAREACALCMETHOD)

    def set_well_pair_area_calc_method(
        self, x: TechId, method: WellPairAreaCalcMethod
    ) -> None:
        """
        Set the method to calculate the total thermally affected area of a well
        pair. This is an optional parameter. If no calculation method is
        specified, the area will be determined by the smallest-rectangle
        method.

        :param x: ATES technology
        :type x: TechId
        :param method: Well pair area calculation method
        :type method: WellPairAreaCalcMethod
        """
        self._check_id(x, ExceptionKey.WELLPAIRAREACALCMETHOD_SET)
        self._well_pair_area_calc_method[x] = method

    # ------------------------------ #
    # Property: elec_per_energy_heat #
    # ------------------------------ #
    def get_elec_per_energy_heat(
        self, s: StageId, h: HubId, x: TechId, ates_data: AtesData
    ) -> Value:
        """
        Get the amount of electricity consumption per unit of provided heating
        energy. This is an optional parameter. If not set, it will be
        calculated from the parameter elec_per_flow_heat.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: ATES technology
        :type x: TechId
        :param ates_data: AtesData
        :type ates_data: AtesData
        :return: Electricity consumption per unit of provided heating energy
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.ELECPERENERGYHEAT_GET)
        if (s, h, x) in self._elec_per_energy_heat:
            return self._elec_per_energy_heat[s, h, x]
        density_fl = self.get_density_fluid(x)
        spec_heat_cap_fl = self.get_specific_heat_capacity_fluid(x)
        max_temp_spread_warm = ates_data.get_max_temperature_spread_warm(h)
        elec_per_flow_heat = self.get_elec_per_flow_heat(s, x)
        elec_per_energy_heat = elec_per_flow_heat / (
            density_fl * spec_heat_cap_fl * max_temp_spread_warm
        )
        return elec_per_energy_heat

    def set_elec_per_energy_heat(
        self, s: StageId, h: HubId, x: TechId, elec_per_energy_heat: Value
    ) -> None:
        """
        Set the amount of electricity consumption per unit of provided heating
        energy. This is an optional parameter. If not set, it will be
        calculated from the parameter elec_per_flow_heat.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: ATES technology
        :type x: TechId
        :param elec_per_energy_heat: Electricity consumption per unit of
            provided heating energy
        :type elec_per_energy_heat: Value
        """
        self._check_id(x, ExceptionKey.ELECPERENERGYHEAT_SET)
        expected_unit = DimlessUnit()
        if not elec_per_energy_heat.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.ELECPERENERGYHEAT_SET.value,
                [s, h, x],
                f"Unit of elec_per_energy_heat[{s}, {h}, {x}] = "
                f"{elec_per_energy_heat} does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._elec_per_energy_heat[s, h, x] = elec_per_energy_heat

    # ------------------------------ #
    # Property: elec_per_energy_cool #
    # ------------------------------ #
    def get_elec_per_energy_cool(
        self, s: StageId, h: HubId, x: TechId, ates_data: AtesData
    ) -> Value:
        """
        Get the amount of electricity consumption per unit of provided cooling
        energy. This is an optional parameter. If not set, it will be
        calculated from the parameter elec_per_flow_cool.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: ATES technology
        :type x: TechId
        :param ates_data: AtesData
        :type ates_data: AtesData
        :return: Electricity consumption per unit of provided cooling energy
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.ELECPERENERGYCOOL_GET)
        if (s, h, x) in self._elec_per_energy_cool:
            return self._elec_per_energy_cool[s, h, x]
        density_fl = self.get_density_fluid(x)
        spec_heat_cap_fl = self.get_specific_heat_capacity_fluid(x)
        max_temp_spread_cold = ates_data.get_max_temperature_spread_cold(h)
        elec_per_flow_cool = self.get_elec_per_flow_cool(s, x)
        elec_per_energy_cool_fl = elec_per_flow_cool / (
            density_fl * spec_heat_cap_fl * max_temp_spread_cold
        )
        return elec_per_energy_cool_fl

    def set_elec_per_energy_cool(
        self, s: StageId, h: HubId, x: TechId, elec_per_energy_cool: Value
    ) -> None:
        """
        Set the amount of electricity consumption per unit of provided cooling
        energy. This is an optional parameter. If not set, it will be
        calculated from the parameter elec_per_flow_cool.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: ATES technology
        :type x: TechId
        :param elec_per_energy_cool: Electricity consumption per unit of
            provided cooling energy
        :type elec_per_energy_cool: Value
        """
        self._check_id(x, ExceptionKey.ELECPERENERGYCOOL_SET)
        expected_unit = DimlessUnit()
        if not elec_per_energy_cool.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.ELECPERENERGYCOOL_SET.value,
                [s, h, x],
                f"Unit of elec_per_energy_cool[{s}, {h}, {x}] = "
                f"{elec_per_energy_cool} does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._elec_per_energy_cool[s, h, x] = elec_per_energy_cool

    # ---------------------------- #
    # Property: elec_per_flow_heat #
    # ---------------------------- #
    def get_elec_per_flow_heat(self, s: StageId, x: TechId) -> Value:
        """
        Get the amount of electricity consumption per unit of fluid extracted
        from warm wells. This is an optional parameter with a default value of
        0.

        :param s: Stage
        :type s: StageId
        :param x: ATES technology
        :type x: TechId
        :return: Electricity consumption per unit of extracted fluid from warm
            wells
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.ELECPERFLOWHEAT_GET)
        elec_per_flow_heat = self._elec_per_flow_heat.get(
            (s, x),
            Value(
                DEF_ELECPERFLOWHEAT,
                unit=(PowerUnit.KW / (LengthUnit.M**3) / TimeUnit.H),
            ),
        )
        return elec_per_flow_heat

    def set_elec_per_flow_heat(
        self, s: StageId, x: TechId, elec_per_flow_heat: Value
    ) -> None:
        """
        Set the amount of electricity consumption per unit of fluid extracted
        from warm wells. This is an optional parameter with a default value of
        0.

        :param s: Stage
        :type s: StageId
        :param x: ATES technology
        :type x: TechId
        :param elec_per_flow_heat: Electricity consumption per unit of
            extracted fluid from warm wells
        :type elec_per_flow_heat: Value
        """
        self._check_id(x, ExceptionKey.ELECPERFLOWHEAT_SET)
        expected_unit = (PowerUnit.KW * TimeUnit.H) / (LengthUnit.M**3)
        if not elec_per_flow_heat.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.ELECPERFLOWHEAT_SET.value,
                [s, x],
                f"Unit of elec_per_flow_heat[{s}, {x}] = {elec_per_flow_heat} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._elec_per_flow_heat[s, x] = elec_per_flow_heat

    # ---------------------------- #
    # Property: elec_per_flow_cool #
    # ---------------------------- #
    def get_elec_per_flow_cool(self, s: StageId, x: TechId) -> Value:
        """
        Get the amount of electricity consumption per unit of fluid extracted
        from cold wells. This is an optional parameter with a default value of
        0.

        :param s: Stage
        :type s: StageId
        :param x: ATES technology
        :type x: TechId
        :return: Electricity consumption per unit of extracted fluid from cold
            wells
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.ELECPERFLOWCOOL_GET)
        elec_per_flow_cool = self._elec_per_flow_cool.get(
            (s, x),
            Value(
                DEF_ELECPERFLOWCOOL,
                unit=(PowerUnit.KW / (LengthUnit.M**3) / TimeUnit.H),
            ),
        )
        return elec_per_flow_cool

    def set_elec_per_flow_cool(
        self, s: StageId, x: TechId, elec_per_flow_cool: Value
    ) -> None:
        """
        Set the amount of electricity consumption per unit of fluid extracted
        from cold wells. This is an optional parameter with a default value of
        0.

        :param s: Stage
        :type s: StageId
        :param x: ATES technology
        :type x: TechId
        :param elec_per_flow_cool: Electricity consumption per unit of
            extracted fluid from cold wells
        :type elec_per_flow_cool: Value
        """
        self._check_id(x, ExceptionKey.ELECPERFLOWCOOL_SET)
        expected_unit = (PowerUnit.KW * TimeUnit.H) / (LengthUnit.M**3)
        if not elec_per_flow_cool.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.ELECPERFLOWCOOL_SET.value,
                [s, x],
                f"Unit of elec_per_flow_cool[{s}, {x}] = {elec_per_flow_cool} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._elec_per_flow_cool[s, x] = elec_per_flow_cool

    # ---------------------------- #
    # Property: max_heat_over_cool #
    # ---------------------------- #
    def get_max_heat_over_cool(
        self, s: StageId, h: HubId, x: TechId, i: AtesScheduleId
    ) -> Value:
        """
        Get the maximal allowed quotient between total heating output over
        total cooling output for an entire schedule. This is an optional
        parameter with a default value of infinity.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: ATES technology
        :type x: TechId
        :param i: Ates Schedule
        :type i: AtesScheduleId
        :return: Maximal allowed quotient between total heating output
            over total cooling output
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.MAXHEATOVERCOOL_GET)
        max_heat_over_cool = self._max_heat_over_cool.get(
            (s, h, x, i), Value(DEF_MAXHEATOVERCOOL)
        )
        return max_heat_over_cool

    def set_max_heat_over_cool(
        self,
        s: StageId,
        h: HubId,
        x: TechId,
        i: AtesScheduleId,
        max_heat_over_cool: Value,
    ) -> None:
        """
        Set the maximal allowed quotient between total heating output over
        total cooling output for an entire schedule. This is an optional
        parameter with a default value of infinity.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: ATES technology
        :type x: TechId
        :param i: Ates Schedule
        :type i: AtesScheduleId
        :param max_heat_over_cool: Maximal allowed quotient between total
            heating output  over total cooling output
        :type max_heat_over_cool: Value
        """
        self._check_id(x, ExceptionKey.MAXHEATOVERCOOL_SET)
        expected_unit = DimlessUnit()
        if not max_heat_over_cool.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.MAXHEATOVERCOOL_SET.value,
                [s, h, x, i],
                f"Unit of max_heat_over_cool[{s}, {h}, {x}, {i}] = "
                f"{max_heat_over_cool} does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._max_heat_over_cool[s, h, x, i] = max_heat_over_cool

    # ---------------------------- #
    # Property: max_cool_over_heat #
    # ---------------------------- #
    def get_max_cool_over_heat(
        self, s: StageId, h: HubId, x: TechId, i: AtesScheduleId
    ) -> Value:
        """
        Get the maximal allowed quotient between total cooling output over
        total heating output for an entire schedule. This is an optional
        parameter with a default value of infinity.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: ATES technology
        :type x: TechId
        :param i: Ates Schedule
        :type i: AtesScheduleId
        :return: Maximal allowed quotient between total cooling output
            over total heating output
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.MAXCOOLOVERHEAT_GET)
        max_cool_over_heat = self._max_cool_over_heat.get(
            (s, h, x, i), Value(DEF_MAXCOOLOVERHEAT)
        )
        return max_cool_over_heat

    def set_max_cool_over_heat(
        self,
        s: StageId,
        h: HubId,
        x: TechId,
        i: AtesScheduleId,
        max_cool_over_heat: Value,
    ) -> None:
        """
        Set the maximal allowed quotient between total cooling output over
        total heating output for an entire schedule. This is an optional
        parameter with a default value of infinity.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: ATES technology
        :type x: TechId
        :param i: Ates Schedule
        :type i: AtesScheduleId
        :param max_cool_over_heat: Maximal allowed quotient between total
            cooling output over total heating output
        :type max_cool_over_heat: Value
        """
        self._check_id(x, ExceptionKey.MAXCOOLOVERHEAT_SET)
        expected_unit = DimlessUnit()
        if not max_cool_over_heat.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.MAXCOOLOVERHEAT_SET.value,
                [s, h, x, i],
                f"Unit of max_cool_over_heat[{s}, {h}, {x}, {i}] = "
                f"{max_cool_over_heat} does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._max_cool_over_heat[s, h, x, i] = max_cool_over_heat

    # ------------------------------ #
    # Calculate area for a well pair #
    # ------------------------------ #
    def calc_area_per_well_pair(
        self,
        thermal_radius_warm: Value,
        thermal_radius_cold: Value,
        calc_method: WellPairAreaCalcMethod,
    ) -> Value:
        """
        Calculate the surface area required by a pair of wells, depending on
        the calculation method and thermal well radii.

        :param thermal_radius_warm: Thermal radius of warm well
        :type thermal_radius_warm: Value
        :param thermal_radius_cold: Thermal radius of cold well
        :type thermal_radius_cold: Value
        :param calc_method: Area calculation method
        :type calc_method: WellPairAreaCalcMethod
        :return: Calculated surface area
        :rtype: Value
        """
        # Area of the two circles with respective radii
        if calc_method == WellPairAreaCalcMethod.TWOCIRCLES:
            area = math.pi * (thermal_radius_warm**2 + thermal_radius_cold**2)
            return area
        # Area of smallest rectangle containing two circles with these radii
        side_1 = 2 * (thermal_radius_warm + thermal_radius_cold)
        side_2 = 2 * max(thermal_radius_warm, thermal_radius_cold)
        area = side_1 * side_2
        return area

    # ------------------------------------ #
    # Calculation: Maximal power densities #
    # ------------------------------------ #
    def calc_max_power_densities(
        self,
        s: StageId,
        h: HubId,
        x: TechId,
        i: AtesScheduleId,
        ates_data: AtesData,
        times: Times,
    ) -> Tuple[Value, Value]:
        """
        Calculate the maximal power densities (heating and cooling) that can be
        achieved by an ATES technology for an ATES schedule. These are the
        densities that can be achieved if each well pair operated at maximal
        pumping capacity for the entire phase duration.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: ATES technology
        :type x: TechId
        :param i: ATES schedule
        :type i: AtesScheduleId
        :param ates_data: AtesData
        :type ates_data: AtesData
        :param times: Times
        :type times: Times
        :return: Maximal heating and cooling power densities
        :rtype: Tuple[Value, Value]
        """
        # Calculate the area per well pair
        thermal_radius_warm = self.get_thermal_radius_per_warm_well(
            s, h, x, i, ates_data, times
        )
        thermal_radius_cold = self.get_thermal_radius_per_cold_well(
            s, h, x, i, ates_data, times
        )
        area_calc_method = self.get_well_pair_area_calc_method(x)
        area_per_well_pair = self.calc_area_per_well_pair(
            thermal_radius_warm, thermal_radius_cold, area_calc_method
        )
        # Calculate the maximal heating and cooling powers per well pair
        density_fl = self.get_density_fluid(x)
        spec_heat_cap_fl = self.get_specific_heat_capacity_fluid(x)
        max_pump_rate_warm = self.get_max_pump_rate_per_warm_well(
            s, h, x, i, ates_data, times
        )
        max_pump_rate_cold = self.get_max_pump_rate_per_cold_well(
            s, h, x, i, ates_data, times
        )
        max_temp_spread_warm = ates_data.get_max_temperature_spread_warm(h)
        max_temp_spread_cold = ates_data.get_max_temperature_spread_cold(h)
        max_heat_power_per_well_pair = (
            density_fl * spec_heat_cap_fl * max_pump_rate_warm * max_temp_spread_warm
        )
        max_cool_power_per_well_pair = (
            density_fl * spec_heat_cap_fl * max_pump_rate_cold * max_temp_spread_cold
        )
        # Return maximal power densities
        max_power_density_heat = max_heat_power_per_well_pair / area_per_well_pair
        max_power_density_cool = max_cool_power_per_well_pair / area_per_well_pair
        return max_power_density_heat, max_power_density_cool

    # ----------------------------- #
    # Property: capex_per_well_pair #
    # ----------------------------- #
    def get_capex_per_well_pair(self, s: StageId, x: TechId) -> Value:
        """
        Get the parameter 'capex_per_well_pair' which denotes the amount of
        CAPEX cost for the installation of one pair of ATES wells. This is an
        optional parameter with a default value of 0.

        :param s: Stage id
        :type s: StageId
        :param x: Technology id
        :type x: TechId
        :return: CAPEX cost per ATES well pair
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.CAPEXPERWELLPAIR_GET)
        return self._capex_per_well_pair.get(
            (s, x), Value(DEF_CAPEXPERWELLPAIR, CurrencyUnit.CHF)
        )

    def set_capex_per_well_pair(
        self, s: StageId, x: TechId, capex_per_well_pair: Value
    ) -> None:
        """
        Set the parameter 'capex_per_well_pair' which denotes the amount of
        CAPEX cost for the installation of one pair of ATES wells. This is an
        optional parameter with a default value of 0.

        :param s: Stage id
        :type s: StageId
        :param x: Technology id
        :type x: TechId
        :param capex_per_well_pair: CAPEX cost per ATES well pair
        :type capex_per_well_pair: Value
        """
        self._check_id(x, ExceptionKey.CAPEXPERWELLPAIR_SET)
        expected_unit = CurrencyUnit.CHF
        if not capex_per_well_pair.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.CAPEXPERWELLPAIR_SET.value,
                [s, x],
                f"Unit of capex_per_well_pair[{s}, {x}] = "
                f"{capex_per_well_pair} does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._capex_per_well_pair[s, x] = capex_per_well_pair

    # ---------------------------- #
    # Property: opex_per_well_pair #
    # ---------------------------- #
    def get_opex_per_well_pair(self, s: StageId, x: TechId) -> Value:
        """
        Get the parameter 'opex_per_well_pair' which denotes the amount of
        OPEX cost for each pair of ATES wells. This is an optional parameter
        with a default value of 0.

        :param s: Stage id
        :type s: StageId
        :param x: ATES technology id
        :type x: TechId
        :return: OPEX cost per ATES well pair
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.OPEXPERWELLPAIR_GET)
        return self._opex_per_well_pair.get(
            (s, x), Value(DEF_OPEXPERWELLPAIR, CurrencyUnit.CHF)
        )

    def set_opex_per_well_pair(
        self, s: StageId, x: TechId, opex_per_well_pair: Value
    ) -> None:
        """
        Set the parameter 'opex_per_well_pair' which denotes the amount of
        OPEX cost for each pair of ATES wells. This is an optional parameter
        with a default value of 0.

        :param s: Stage id
        :type s: StageId
        :param x: ATES technology id
        :type x: TechId
        :param opex_per_well_pair: OPEX cost per ATES well pair
        :type opex_per_well_pair: Value
        """
        self._check_id(x, ExceptionKey.OPEXPERWELLPAIR_SET)
        expected_unit = CurrencyUnit.CHF
        if not opex_per_well_pair.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.OPEXPERWELLPAIR_SET.value,
                [s, x],
                f"Unit of opex_per_well_pair[{s}, {x}] = "
                f"{opex_per_well_pair} does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._opex_per_well_pair[s, x] = opex_per_well_pair

    # --------------------------- #
    # Property: co2_per_well_pair #
    # --------------------------- #
    def get_co2_per_well_pair(self, s: StageId, x: TechId) -> Value:
        """
        Get the parameter 'co2_per_well_pair' which denotes the amount of
        embedded CO2 that arises for each pair of ATES wells. This is an
        optional parameter with a default value of 0.

        :param s: Stage id
        :type s: StageId
        :param x: ATES technology id
        :type x: TechId
        :return: Embedded CO2 per ATES well pair
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.CO2PERWELLPAIR_GET)
        return self._co2_per_well_pair.get(
            (s, x), Value(DEF_CO2PERWELLPAIR, MassUnit.KG)
        )

    def set_co2_per_well_pair(
        self, s: StageId, x: TechId, co2_per_well_pair: Value
    ) -> None:
        """
        Set the parameter 'co2_per_well_pair' which denotes the amount of
        embedded CO2 that arises for each pair of ATES wells. This is an
        optional parameter with a default value of 0.

        :param s: Stage id
        :type s: StageId
        :param x: ATES technology id
        :type x: TechId
        :param co2_per_well_pair: Embedded CO2 per ATES well pair
        :type co2_per_well_pair: Value
        """
        self._check_id(x, ExceptionKey.CO2PERWELLPAIR_SET)
        expected_unit = MassUnit.KG
        if not co2_per_well_pair.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.CO2PERWELLPAIR_SET.value,
                [s, x],
                f"Unit of co2_per_well_pair[{s}, {x}] = "
                f"{co2_per_well_pair} does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._co2_per_well_pair[s, x] = co2_per_well_pair

    # ---------------------- #
    # Property: availability #
    # ---------------------- #
    def get_availability(
        self, s: StageId, h: HubId, x: TechId, i: AtesScheduleId
    ) -> TimeSeries:
        """
        Get the parameter 'availability' for an ATES technology.
        Availability is a relative value that scales the amount of available
        ATES capacity for that technology, thereby limiting the technology's
        operation possibility. An availability value of e.g.; 0.5 means that
        only half of the installed technology is available at that time. This
        is an optional parameter with a default value of 1.

        :param s: Stage id
        :type s: StageId
        :param h: Hub id
        :type h: HubId
        :param x: ATES technology id
        :type x: TechId
        :param i: ATES schedule id
        :type i: AtesScheduleId
        :return: Availability time series
        :rtype: TimeSeries
        """
        self._check_id(x, ExceptionKey.AVAILABILITY_GET)
        availability = self._availability.get((s, h, x, i), None)
        if availability is None:
            availability = TimeSeries()
            availability.def_value = Value(DEF_AVAILABILITY)
        return availability

    def set_availability(
        self,
        s: StageId,
        h: HubId,
        x: TechId,
        i: AtesScheduleId,
        t: TimeId,
        availability: Value,
    ) -> None:
        """
        Set the parameter 'availability' for an ATES technology.
        Availability is a relative value that scales the amount of available
        ATES capacity for that technology, thereby limiting the technology's
        operation possibility. An availability value of e.g.; 0.5 means that
        only half of the installed technology is available at that time. This
        is an optional parameter with a default value of 1.

        :param s: Stage id
        :type s: StageId
        :param h: Hub id
        :type h: HubId
        :param x: ATES technology id
        :type x: TechId
        :param i: ATES schedule id
        :type i: AtesScheduleId
        :param t: Time id
        :type t: TimeId
        :param availability: Availability value
        :type availability: Value
        """
        self._check_id(x, ExceptionKey.AVAILABILITY_SET)
        if (s, h, x, i) not in self._availability:
            self._availability[s, h, x, i] = TimeSeries()
            self._availability[s, h, x, i].def_value = Value(DEF_AVAILABILITY)
        self._availability[s, h, x, i].set_value(t, availability)

    def set_availability_def(
        self,
        s: StageId,
        h: HubId,
        x: TechId,
        i: AtesScheduleId,
        availability_def: Value,
    ) -> None:
        """
        Set the default (with respect to time) parameter 'availability' for an ATES
        technology. Availability is a relative value that scales the amount of available
        ATES capacity for that technology, thereby limiting the technology's
        operation possibility. An availability value of e.g.; 0.5 means that
        only half of the installed technology is available at that time. This
        is an optional parameter with a default value of 1.

        :param s: Stage id
        :type s: StageId
        :param h: Hub id
        :type h: HubId
        :param x: ATES technology id
        :type x: TechId
        :param i: ATES schedule id
        :type i: AtesScheduleId
        :param availability_def: Availability value
        :type availability_def: Value
        """
        self._check_id(x, ExceptionKey.AVAILABILITY_DEFSET)
        if (s, h, x, i) not in self._availability:
            self._availability[s, h, x, i] = TimeSeries()
        expected_unit = DimlessUnit()
        if not availability_def.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.AVAILABILITY_DEFSET.value,
                [s, h, x, i],
                f"Unit of availability[{s}, {h}, {x}, {i}] = "
                f"{availability_def} does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._availability[s, h, x, i].def_value = availability_def

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._ids: Set[TechId] = set()
        self._ec_el: Dict[TechId, EcId] = {}
        self._ec_ht: Dict[TechId, EcId] = {}
        self._ec_co: Dict[TechId, EcId] = {}
        self._density_fluid: Dict[TechId, Value] = {}
        self._specific_heat_capacity_fluid: Dict[TechId, Value] = {}
        self._well_radius: Dict[TechId, Value] = {}
        self._well_pair_area_calc_method: Dict[TechId, WellPairAreaCalcMethod] = {}
        self._elec_per_energy_heat: Dict[Tuple[StageId, HubId, TechId], Value] = {}
        self._elec_per_energy_cool: Dict[Tuple[StageId, HubId, TechId], Value] = {}
        self._elec_per_flow_heat: Dict[Tuple[StageId, TechId], Value] = {}
        self._elec_per_flow_cool: Dict[Tuple[StageId, TechId], Value] = {}
        self._max_heat_over_cool: Dict[
            Tuple[StageId, HubId, TechId, AtesScheduleId], Value
        ] = {}
        self._max_cool_over_heat: Dict[
            Tuple[StageId, HubId, TechId, AtesScheduleId], Value
        ] = {}
        self._well_pairs_min: Dict[
            Tuple[StageId, HubId, TechId, AtesScheduleId], Value
        ] = {}
        self._well_pairs_max: Dict[
            Tuple[StageId, HubId, TechId, AtesScheduleId], Value
        ] = {}
        self._max_pump_rate_per_warm_well: Dict[
            Tuple[StageId, HubId, TechId, AtesScheduleId], Value
        ] = {}
        self._max_pump_rate_per_cold_well: Dict[
            Tuple[StageId, HubId, TechId, AtesScheduleId], Value
        ] = {}
        self._thermal_radius_warm: Dict[
            Tuple[StageId, HubId, TechId, AtesScheduleId], Value
        ] = {}
        self._thermal_radius_cold: Dict[
            Tuple[StageId, HubId, TechId, AtesScheduleId], Value
        ] = {}
        self._capex_per_well_pair: Dict[Tuple[StageId, TechId], Value] = {}
        self._opex_per_well_pair: Dict[Tuple[StageId, TechId], Value] = {}
        self._co2_per_well_pair: Dict[Tuple[StageId, TechId], Value] = {}
        self._availability: Dict[
            Tuple[StageId, HubId, TechId, AtesScheduleId], TimeSeries
        ] = {}

    # ---------- #
    # Validation #
    # ---------- #
    def validate(
        self,
        stages: Stages,
        hubs: Hubs,
        techs: Techs,
        ecs: Ecs,
        ates_data: AtesData,
        times: Times,
    ) -> None:
        """
        Validate all ATES technology data in this object. Apart from sense-
        checking parameter in terms of quantity, this includes checking
        whether the ids from other data classes used here are known there as
        well.

        :param stages: Stages data class
        :type stages: Stages
        :param hubs: Hubs data class
        :type hubs: Hubs
        :param ecs: ecs data class
        :type ecs: Ecs
        :param ates_data: ATES data class
        :type ates_data: AtesData
        """
        self._validate_ids(techs)
        self._validate_ec_el(ecs)
        self._validate_ec_ht(ecs)
        self._validate_ec_co(ecs)
        self._validate_ecs()
        self._validate_schedule_existence(techs, ates_data)
        self._validate_density_fluid()
        self._validate_spec_heat_cap_fluid()
        self._validate_well_radius()
        self._validate_num_well_pairs_min(stages, hubs, ates_data)
        self._validate_num_well_pairs_max(stages, hubs, ates_data)
        self._validate_num_well_pairs_minmax()
        self._validate_max_pump_rate_per_warm_well(stages, hubs, ates_data)
        self._validate_max_pump_rate_per_cold_well(stages, hubs, ates_data)
        self._validate_thermal_radius_warm(stages, hubs, ates_data)
        self._validate_thermal_radius_cold(stages, hubs, ates_data)
        self._validate_elec_per_energy_heat(stages, hubs)
        self._validate_elec_per_energy_cool(stages, hubs)
        self._validate_elec_per_flow_heat(stages)
        self._validate_elec_per_flow_cool(stages)
        self._validate_max_heat_over_cool(stages, hubs, ates_data)
        self._validate_max_cool_over_heat(stages, hubs, ates_data)
        self._validate_max_heatovercool_cooloverheat()
        self._validate_capex_per_well_pair(stages)
        self._validate_opex_per_well_pair(stages)
        self._validate_co2_per_well_pair(stages)
        self._validate_availability(stages, hubs, ates_data, times)

    def _validate_ids(self, techs: Techs) -> None:
        exc_key = ExceptionKey.ID_VAL.value
        for x in self._ids:
            # stor_tech not in techs
            if x not in techs.ids:
                msg = f"ates_tech {x} not part of techs"
                raise exceptions.DataException(exc_key, [x], msg, module=LOG_MODULE_STR)

    def _validate_ec_el(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.ECEL_VAL.value
        for x, e in self._ec_el.items():
            if e not in ecs.ids:
                msg = f"Unknown ec_el {e} for {x}"
                raise exceptions.DataException(
                    exc_key, [x, e], msg, module=LOG_MODULE_STR
                )

    def _validate_ec_ht(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.ECHT_VAL.value
        for x, e in self._ec_ht.items():
            if e not in ecs.ids:
                msg = f"Unknown ec_ht {e} for {x}"
                raise exceptions.DataException(
                    exc_key, [x, e], msg, module=LOG_MODULE_STR
                )

    def _validate_ec_co(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.ECCO_VAL.value
        for x, e in self._ec_co.items():
            if e not in ecs.ids:
                msg = f"Unknown ec_co {e} for {x}"
                raise exceptions.DataException(
                    exc_key, [x, e], msg, module=LOG_MODULE_STR
                )

    def _validate_ecs(self) -> None:
        exc_key = ExceptionKey.ECS_VAL.value
        for x in self._ids:
            all_ecs: List[Index] = [
                self.get_ec_el(x),
                self.get_ec_ht(x),
                self.get_ec_co(x),
            ]
            dupes = [e for e, cnt in collections.Counter(all_ecs).items() if cnt > 1]
            if len(dupes) > 0:
                msg = (
                    f"ATES tech {x} has the ecs {dupes} occuring "
                    "multiple times across ec_el, ec_ht, and ec_co"
                )
                raise exceptions.DataException(
                    exc_key, dupes, msg, module=LOG_MODULE_STR
                )

    def _validate_schedule_existence(self, techs: Techs, ates_data: AtesData) -> None:
        exc_key = ExceptionKey.SCHEDULEEXISTENCE_VAL.value
        for x in self.ids:
            for h in techs.get_allowed_hubs(x):
                if not ates_data.get_schedule_ids(h):
                    msg = (
                        f"ATES tech {x} is allowed in hub {h} but there "
                        "is no ATES schedule for that hub"
                    )
                    raise exceptions.DataException(
                        exc_key, [h, x], msg, module=LOG_MODULE_STR
                    )

    def _validate_density_fluid(self) -> None:
        exc_key = ExceptionKey.DENSITYFLUID_VAL.value
        for x, density_fluid in self._density_fluid.items():
            if density_fluid.is_negative:
                msg = f"{density_fluid} = density_fluid[{x}] < 0"
                raise exceptions.DataException(exc_key, [x], msg, module=LOG_MODULE_STR)

    def _validate_spec_heat_cap_fluid(self) -> None:
        exc_key = ExceptionKey.SPECIFICHEATCAPFLUID_VAL.value
        for x, spec_heat_cap_fl in self._specific_heat_capacity_fluid.items():
            if spec_heat_cap_fl.is_negative:
                msg = f"{spec_heat_cap_fl} = specific_heat_capacity_fluid[{x}] < 0"
                raise exceptions.DataException(exc_key, [x], msg, module=LOG_MODULE_STR)

    def _validate_well_radius(self) -> None:
        exc_key = ExceptionKey.WELLRADIUS_VAL.value
        for x, well_radius in self._well_radius.items():
            if well_radius.is_negative:
                msg = f"{well_radius} = well_radius[{x}] < 0"
                raise exceptions.DataException(exc_key, [x], msg, module=LOG_MODULE_STR)

    def _validate_num_well_pairs_min(
        self, stages: Stages, hubs: Hubs, ates_data: AtesData
    ) -> None:
        exc_key = ExceptionKey.WELLPAIRSMIN_VAL.value
        for (s, h, x, i), well_pairs_min in self._well_pairs_min.items():
            if s not in stages.ids:
                msg = f"Unknown stage {s} in well_pairs_min" f"[{s}, {h}, {x}, {i}]"
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if h not in hubs.ids:
                msg = f"Unknown hub {s} in well_pairs_min" f"[{s}, {h}, {x}, {i}]"
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if i not in ates_data.get_schedule_ids(h):
                msg = (
                    f"ATES schedule {i} is unknown for hub {h} in "
                    f"well_pairs_min[{s}, {h}, {x}, {i}]"
                )
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if well_pairs_min.is_negative:
                logging.log_warning(
                    f"{well_pairs_min} = well_pairs_min" f"[{s, h, x, i}] < 0",
                    module=LOG_MODULE_STR,
                )

    def _validate_num_well_pairs_max(
        self, stages: Stages, hubs: Hubs, ates_data: AtesData
    ) -> None:
        exc_key = ExceptionKey.WELLPAIRSMAX_VAL.value
        for (s, h, x, i), well_pairs_max in self._well_pairs_max.items():
            if s not in stages.ids:
                msg = f"Unknown stage {s} in well_pairs_max" f"[{s}, {h}, {x}, {i}]"
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if h not in hubs.ids:
                msg = f"Unknown hub {s} in well_pairs_max" f"[{s}, {h}, {x}, {i}]"
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if i not in ates_data.get_schedule_ids(h):
                msg = (
                    f"ATES schedule {i} is unknown for hub {h} in "
                    f"well_pairs_max[{s}, {h}, {x}, {i}]"
                )
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if well_pairs_max.is_negative:
                raise exceptions.DataException(
                    exc_key,
                    [s, h, x, i],
                    f"{well_pairs_max} = max_pump_rate_per_warm_well"
                    f"[{s, h, x, i}] < 0",
                    module=LOG_MODULE_STR,
                )

    def _validate_num_well_pairs_minmax(self) -> None:
        exc_key = ExceptionKey.WELLPAIRSMAX_VAL.value
        keys = set(self._well_pairs_min.keys()).union(set(self._well_pairs_max.keys()))
        for s, h, x, i in keys:
            well_pairs_min = self.get_well_pairs_min(s, h, x, i)
            well_pairs_max = self.get_well_pairs_max(s, h, x, i)
            # well_pairs_min must be less than or equal to well_pairs_max
            if well_pairs_min > well_pairs_max:
                msg = (
                    f"well_pairs_min[{s}, {h}, {x}, {i}] = {well_pairs_min} "
                    f"> well_pairs_max[{s}, {h}, {x}, {i}] = {well_pairs_max}"
                )
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )

    def _validate_max_pump_rate_per_warm_well(
        self, stages: Stages, hubs: Hubs, ates_data: AtesData
    ) -> None:
        exc_key = ExceptionKey.MAXPUMPRATEWARM_VAL.value
        for (s, h, x, i), max_pump_rate in self._max_pump_rate_per_warm_well.items():
            if s not in stages.ids:
                msg = (
                    f"Unknown stage {s} in max_pump_rate_per_warm_well"
                    f"[{s}, {h}, {x}, {i}]"
                )
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if h not in hubs.ids:
                msg = (
                    f"Unknown hub {h} in max_pump_rate_per_warm_well"
                    f"[{s}, {h}, {x}, {i}]"
                )
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if i not in ates_data.get_schedule_ids(h):
                msg = (
                    f"ATES schedule {i} is unknown for hub {h} in "
                    f"max_pump_rate_per_warm_well[{s}, {h}, {x}, {i}]"
                )
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if max_pump_rate.is_negative:
                msg = f"{max_pump_rate} = max_pump_rate_per_warm_well[{s, h, x, i}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )

    def _validate_max_pump_rate_per_cold_well(
        self, stages: Stages, hubs: Hubs, ates_data: AtesData
    ) -> None:
        exc_key = ExceptionKey.MAXPUMPRATECOLD_VAL.value
        for (s, h, x, i), max_pump_rate in self._max_pump_rate_per_cold_well.items():
            if s not in stages.ids:
                msg = (
                    f"Unknown stage {s} in max_pump_rate_per_cold_well"
                    f"[{s}, {h}, {x}, {i}]"
                )
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if h not in hubs.ids:
                msg = (
                    f"Unknown hub {h} in max_pump_rate_per_cold_well"
                    f"[{s}, {h}, {x}, {i}]"
                )
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if i not in ates_data.get_schedule_ids(h):
                msg = (
                    f"ATES schedule {i} is unknown for hub {h} in "
                    f"max_pump_rate_per_cold_well[{s}, {h}, {x}, {i}]"
                )
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if max_pump_rate.is_negative:
                msg = f"{max_pump_rate} = max_pump_rate_per_cold_well[{s, h, x, i}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )

    def _validate_thermal_radius_warm(
        self, stages: Stages, hubs: Hubs, ates_data: AtesData
    ) -> None:
        exc_key = ExceptionKey.THERMALRADIUSWARM_VAL.value
        for (s, h, x, i), therm_rad_warm in self._thermal_radius_warm.items():
            if s not in stages.ids:
                msg = f"Unknown stage {s} in thermal_radius_warm[{s}, {h}, {x}, {i}]"
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in thermal_radius_warm[{s}, {h}, {x}, {i}]"
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if i not in ates_data.get_schedule_ids(h):
                msg = (
                    f"ATES schedule {i} is unknown for hub {h} in "
                    f"thermal_radius_warm[{s}, {h}, {x}, {i}]"
                )
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if therm_rad_warm.is_negative:
                msg = f"{therm_rad_warm} = thermal_radius_warm[{s, h, x, i}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )

    def _validate_thermal_radius_cold(
        self, stages: Stages, hubs: Hubs, ates_data: AtesData
    ) -> None:
        exc_key = ExceptionKey.THERMALRADIUSCOLD_VAL.value
        for (s, h, x, i), therm_rad_cold in self._thermal_radius_cold.items():
            if s not in stages.ids:
                msg = f"Unknown stage {s} in thermal_radius_cold[{s}, {h}, {x}, {i}]"
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in thermal_radius_cold[{s}, {h}, {x}, {i}]"
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if i not in ates_data.get_schedule_ids(h):
                msg = (
                    f"ATES schedule {i} is unknown for hub {h} in "
                    f"thermal_radius_cold[{s}, {h}, {x}, {i}]"
                )
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if therm_rad_cold.is_negative:
                msg = f"{therm_rad_cold} = thermal_radius_cold[{s, h, x, i}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )

    def _validate_elec_per_energy_heat(self, stages: Stages, hubs: Hubs) -> None:
        exc_key = ExceptionKey.ELECPERENERGYHEAT_VAL.value
        for (s, h, x), elec_per_en in self._elec_per_energy_heat.items():
            if s not in stages.ids:
                msg = f"Unknown stage {s} in elec_per_energy_heat[{s}, {h}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, h, x], msg, module=LOG_MODULE_STR
                )
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in elec_per_energy_heat[{s}, {h}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, h, x], msg, module=LOG_MODULE_STR
                )
            if elec_per_en.is_negative:
                msg = f"{elec_per_en} = elec_per_energy_heat[{s}, {h}, {x}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, h, x], msg, module=LOG_MODULE_STR
                )

    def _validate_elec_per_energy_cool(
        self,
        stages: Stages,
        hubs: Hubs,
    ) -> None:
        exc_key = ExceptionKey.ELECPERENERGYCOOL_VAL.value
        for (s, h, x), elec_per_en in self._elec_per_energy_cool.items():
            if s not in stages.ids:
                msg = f"Unknown stage {s} in elec_per_energy_cool[{s}, {h}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, h, x], msg, module=LOG_MODULE_STR
                )
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in elec_per_energy_cool[{s}, {h}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, h, x], msg, module=LOG_MODULE_STR
                )
            if elec_per_en.is_negative:
                msg = f"{elec_per_en} = elec_per_energy_cool[{s}, {h}, {x}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, h, x], msg, module=LOG_MODULE_STR
                )

    def _validate_elec_per_flow_heat(self, stages: Stages) -> None:
        exc_key = ExceptionKey.ELECPERFLOWHEAT_VAL.value
        for (s, x), elec_per_flow in self._elec_per_flow_heat.items():
            if s not in stages.ids:
                msg = f"Unknown stage {s} in elec_per_flow_heat[{s}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            if elec_per_flow.is_negative:
                msg = f"{elec_per_flow} = elec_per_flow_heat[{s}, {x}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            if elec_per_flow.is_negative:
                msg = f"{elec_per_flow} = elec_per_flow_heat[{s}, {x}] ~ 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_elec_per_flow_cool(self, stages: Stages) -> None:
        exc_key = ExceptionKey.ELECPERFLOWCOOL_VAL.value
        for (s, x), elec_per_flow in self._elec_per_flow_cool.items():
            if s not in stages.ids:
                msg = f"Unknown stage {s} in elec_per_flow_cool[{s}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            if elec_per_flow.is_negative:
                msg = f"{elec_per_flow} = elec_per_flow_cool[{s}, {x}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )

    def _validate_max_heat_over_cool(
        self, stages: Stages, hubs: Hubs, ates_data: AtesData
    ) -> None:
        exc_key = ExceptionKey.MAXHEATOVERCOOL_VAL.value
        for (s, h, x, i), max_heat_over_cool in self._max_heat_over_cool.items():
            if s not in stages.ids:
                msg = f"Unknown stage {s} in max_heat_over_cool[{s}, {h}, {x}, {i}]"
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in max_heat_over_cool[{s}, {h}, {x}, {i}]"
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if i not in ates_data.get_schedule_ids(h):
                msg = (
                    f"Unknown ATES schedule id {i} for hub {h} in "
                    f"max_heat_over_cool[{s}, {h}, {x}, {i}]"
                )
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if max_heat_over_cool.is_negative:
                msg = (
                    f"{max_heat_over_cool} = max_heat_over_cool[{s}, {h}, {x}, {i}] < 0"
                )
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if max_heat_over_cool < Value(common.EPS_ZEROCHECK):
                msg = (
                    f"{max_heat_over_cool} = max_heat_over_cool[{s}, {h}, {x}, {i}] ~ 0"
                )
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_max_cool_over_heat(
        self, stages: Stages, hubs: Hubs, ates_data: AtesData
    ) -> None:
        exc_key = ExceptionKey.MAXCOOLOVERHEAT_VAL.value
        for (s, h, x, i), max_cool_over_heat in self._max_cool_over_heat.items():
            if s not in stages.ids:
                msg = f"Unknown stage {s} in max_cool_over_heat[{s}, {h}, {x}, {i}]"
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in max_cool_over_heat[{s}, {h}, {x}, {i}]"
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if i not in ates_data.get_schedule_ids(h):
                msg = (
                    f"Unknown ATES schedule id {i} for hub {h} in "
                    f"max_cool_over_heat[{s}, {h}, {x}, {i}]"
                )
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if max_cool_over_heat.is_negative:
                msg = (
                    f"{max_cool_over_heat} = max_cool_over_heat[{s}, {h}, {x}, {i}] < 0"
                )
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )
            if max_cool_over_heat < Value(common.EPS_ZEROCHECK):
                msg = (
                    f"{max_cool_over_heat} = max_cool_over_heat[{s}, {h}, {x}, {i}] ~ 0"
                )
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_max_heatovercool_cooloverheat(self) -> None:
        exc_key = ExceptionKey.MAXHEATOVERCOOLMAXCOOLOVERHEAT_VAL.value
        keys = set(self._max_heat_over_cool.keys()).union(
            set(self._max_cool_over_heat.keys())
        )
        for s, h, x, i in keys:
            max_heat_over_cool = self.get_max_heat_over_cool(s, h, x, i)
            max_cool_over_heat = self.get_max_cool_over_heat(s, h, x, i)
            # Product of the two max_x_over_y's must be at least 1
            product = max_heat_over_cool * max_cool_over_heat
            if product < Value(1):
                msg = (
                    f"{product} = max_heat_over_cool"
                    f"[{s}, {h}, {x}, {i}] * max_cool_over_heat"
                    f"[{s}, {h}, {x}, {i}] < 1 (max_heat_over_cool"
                    f"[{s}, {h}, {x}, {i}] = {max_heat_over_cool}, "
                    f"(max_cool_over_heat[{s}, {h}, {x}, {i}] = "
                    f"{max_cool_over_heat})"
                )
                raise exceptions.DataException(
                    exc_key, [s, h, x, i], msg, module=LOG_MODULE_STR
                )

    def _validate_capex_per_well_pair(self, stages: Stages) -> None:
        exc_key = ExceptionKey.CAPEXPERWELLPAIR_VAL.value
        for (s, x), capex in self._capex_per_well_pair.items():
            if s not in stages.ids:
                msg = f"Unknown stage {s} in capex_per_well_pair[{s}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            if capex.is_negative:
                msg = f"{capex} = capex_per_well_pair[{s}, {x}] < 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_opex_per_well_pair(self, stages: Stages) -> None:
        exc_key = ExceptionKey.OPEXPERWELLPAIR_VAL.value
        for (s, x), opex in self._opex_per_well_pair.items():
            if s not in stages.ids:
                msg = f"Unknown stage {s} in opex_per_well_pair[{s}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            if opex.is_negative:
                msg = f"{opex} = opex_per_well_pair[{s}, {x}] < 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_co2_per_well_pair(self, stages: Stages) -> None:
        exc_key = ExceptionKey.CO2PERWELLPAIR_VAL.value
        for (s, x), co2 in self._co2_per_well_pair.items():
            if s not in stages.ids:
                msg = f"Unknown stage {s} in co2_per_well_pair[{s}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            if co2.is_negative:
                msg = f"{co2} = co2_per_well_pair[{s}, {x}] < 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_availability(
        self, stages: Stages, hubs: Hubs, ates_data: AtesData, times: Times
    ) -> None:
        exc_key = ExceptionKey.AVAILABILITY_VAL.value
        for (s, h, x, i), availability in self._availability.items():
            # Unknown stage id
            if s not in stages.ids:
                raise exceptions.DataException(
                    exc_key,
                    [s, h, x],
                    f"Unknown stage {s} in availability[{s}, {h}, {x}, {i}]",
                    module=LOG_MODULE_STR,
                )
            # Unknown hub id
            if h not in hubs.ids:
                raise exceptions.DataException(
                    exc_key,
                    [s, h, x],
                    f"Unknown hub {h} in availability[{s}, {h}, {x}, {i}]",
                    module=LOG_MODULE_STR,
                )
            # Unknown ATES schedule id
            if i not in ates_data.get_schedule_ids(h):
                raise exceptions.DataException(
                    exc_key,
                    [s, h, x],
                    f"ATES schedule {i} is unknown for hub {h} in "
                    f"availability[{s}, {h}, {x}, {i}]",
                    module=LOG_MODULE_STR,
                )
            # Time values
            if availability.has_values:
                # Unknown time ids
                availability.validate(times, exc_key, module=LOG_MODULE_STR)
                # Availability values must be nonnegative (time values)
                for t in times.ids:
                    if availability.get_value(t).is_negative:
                        raise exceptions.DataException(
                            exc_key,
                            [s, h, x],
                            f"{availability.get_value(t)} = availability["
                            f"{s}, {h}, {x}, {i}][{t}] < 0",
                            module=LOG_MODULE_STR,
                        )
                # Availability values should be smaller than 1 (time values)
                for t in times.ids:
                    if availability.get_value(t) > Value(1):
                        logging.log_warning(
                            f"{availability.get_value(t)} = availability["
                            f"{s}, {h}, {x}, {i}][{t}] > 1",
                            module=LOG_MODULE_STR,
                        )
                        break
            # Default values
            if not availability.has_values:
                availability_def = availability.def_value
                assert availability_def is not None
                # Availability values must be nonnegative (default value)
                if availability_def.is_negative:
                    raise exceptions.DataException(
                        exc_key,
                        [s, h, x],
                        f"{availability_def} = availability_def["
                        f"{s}, {h}, {x}, {i}] < 0",
                        module=LOG_MODULE_STR,
                    )
                # Constant availability usually not zero (default value)
                if availability_def < Value(common.EPS_ZEROCHECK):
                    logging.log_warning(
                        f"{availability_def} = availability_def[{s}, {h}, {x}, {i}"
                        "] ~ 0",
                        module=LOG_MODULE_STR,
                    )
                # Availability values usually smaller than 1 (default value)
                if availability_def > Value(1):
                    msg = f"{availability_def} = availability[{s}, {h}, {x}, {i}] > 1"
                    logging.log_warning(msg, module=LOG_MODULE_STR)

    # ---------- #
    # Id checker #
    # ---------- #
    def _check_id(self, x: TechId, key: ExceptionKey) -> None:
        if x not in self._ids:
            raise exceptions.UnknownIdException(key.value, x, module=LOG_MODULE_STR)


# ------------------------------------------ #
# Calculate thermal radius for a single well #
# ------------------------------------------ #
def _calc_thermal_radius(
    density_aquifer: Value,
    specific_heat_capacity_aquifer: Value,
    thickness_aquifer: Value,
    groundwater_celocity: Value,
    density_fluid: Value,
    specific_heat_capacity_fluid: Value,
    injection_duration: Value,
    max_injection_rate: Value,
) -> Value:
    """
    Calculates the thermal radius of a well based on
        a) The conductive radius
        b) The convective radius

    :param specific_heat_capacity_aquifer: Specific heat capacity of the
        aquifer
    :type specific_heat_capacity_aquifer: Value
    :param thickness_aquifer: Thickness of the aquifer
    :type thickness_aquifer: Value
    :param groundwater_celocity: Groundwater Darcy velocity
    :type groundwater_celocity: Value
    :param specific_heat_capacity_fluid: Specific heat capacity of the
        ATES fluid
    :type specific_heat_capacity_fluid: Value
    :param injection_duration: Well injection duration
    :type injection_duration: Value
    :param max_pump_rate: Maximal injection rate
    :type max_pump_rate: Value
    :return: Thermal radius of the well
    :rtype: Value
    """
    # Conductive part of thermal radius
    therm_rad_cond_sq: Value = (
        density_fluid
        * specific_heat_capacity_fluid
        * max_injection_rate
        * injection_duration
        / (
            density_aquifer
            * specific_heat_capacity_aquifer
            * math.pi
            * thickness_aquifer
        )
    )
    therm_rad_cond = therm_rad_cond_sq.root(deg=2)
    # Convective part of thermal radius
    therm_rad_conv = groundwater_celocity * injection_duration
    # Return
    therm_rad = therm_rad_cond + therm_rad_conv
    return therm_rad


# ---------------------------------------------------------- #
# Calculate maximal pump rate for a well from Theis equation #
# ---------------------------------------------------------- #
def _calc_max_pump_rate_from_theis_equation(
    max_drawdown: Value,
    well_radius: Value,
    pumping_duration: Value,
    hydraulic_transmissivity_aquifer: Value,
    storativity_aquifer: Value,
) -> Value:
    """
    This method calculates the maximal pump rate for a well from the Theis
    equation. The Theis equation is a solution to the flow of water into a
    well in an aquifer. The equation is based on the following assumptions:
    - The aquifer is homogeneous and isotropic
    - The well is fully penetrating
    - The well is pumping at a constant rate
    - The aquifer is confined
    - The aquifer is infinite in extent
    - The aquifer is at steady state

    :param max_drawdown: Maximal allowable drawdown at the well boundary
    :type max_drawdown: Value
    :param well_radius: Well radius
    :type well_radius: Value
    :param pumping_duration: Pumping duration
    :type pumping_duration: Value
    :param hydraulic_transmissivity_aquifer: Hydraulic transmissivity of the aquifer
    :type hydraulic_transmissivity_aquifer: Value
    :param storativity_aquifer: Storage coefficient of the aquifer
    :type storativity_aquifer: Value
    :return: Maximal pumping rate
    :rtype: Value
    """
    well_function_arg = (
        well_radius**2
        * storativity_aquifer
        / (4 * hydraulic_transmissivity_aquifer * pumping_duration)
    )
    well_function_val_fl = -expi(-well_function_arg.to_float())
    well_function_val = Value(well_function_val_fl)
    max_pump_rate = (
        4
        * math.pi
        * hydraulic_transmissivity_aquifer
        * max_drawdown
        / well_function_val
    )
    return max_pump_rate
