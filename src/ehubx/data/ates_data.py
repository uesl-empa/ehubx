"""
ATES data module
"""

from enum import Enum
from typing import Dict, Set, Tuple

from ehubx.core import common
from ehubx.data import exceptions
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.index import Index, IndexKind
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.time_data import TimeId, Times
from ehubx.data.unit import (
    DimlessUnit,
    LengthUnit,
    MassUnit,
    PowerUnit,
    TemperatureUnit,
    TimeUnit,
)
from ehubx.data.value import Value


class AtesScheduleId(Index):
    """
    ATES schedule index. Different schedules allow the capacity of an ATES
    technology to be split into parts, each working on their own yearly
    schedule. This is an approximation of different well pairs operating on
    different schedules
    """

    def __init__(self, key: str) -> None:
        super().__init__(IndexKind.ATESSCHEDULE, key)


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the ATES data module
    """

    DARCYVELOCITY_SET = "setting 'darcy_velocity' of AtesData"
    DARCYVELOCITY_GET = "getting 'darcy_velocity' from AtesData"
    DARCYVELOCITY_VAL = "validating 'darcy_velocity' of AtesData"
    DENSITYROCK_SET = "setting density_rock of AtesData"
    DENSITYROCK_GET = "getting density_rock from AtesData"
    DENSITYROCK_VAL = "validating density_rock of AtesData"
    SPECIFICHEATCAPROCK_SET = "setting specific_heat_capacity_rock of AtesData"
    SPECIFICHEATCAPROCK_GET = "getting specific_heat_capacity_rock from AtesData"
    SPECIFICHEATCAPROCK_VAL = "validating specific_heat_capacity_rock of AtesData"
    POROSITYAQ_SET = "setting 'porosity_aquifer' of AtesData"
    POROSITYAQ_GET = "getting 'porosity_aquifer' from AtesData"
    POROSITYAQ_VAL = "validating 'porosity_aquifer' of AtesData"
    THICKNESSAQ_SET = "setting 'thickness_aq' of AtesData"
    THICKNESSAQ_GET = "getting 'thickness_aq' from AtesData"
    THICKNESSAQ_VAL = "validating 'thickness_aq' of AtesData"
    HYDRAULICCONDUCTAQ_SET = "setting 'hydraulic_conductivity_aquifer of AtesData"
    HYDRAULICCONDUCTAQ_GET = "getting 'hydraulic_conductivity_aquifer from AtesData"
    HYDRAULICCONDUCTAQ_VAL = "validating 'hydraulic_conductivity_aquifer of AtesData"
    HYDRAULICTRANSMISAQ_GET = "getting 'hydraulic_transmissivity_aquifer from AtesData"
    MAXDRAWDOWN_SET = "setting 'max_drawdown' of AtesData"
    MAXDRAWDOWN_GET = "getting 'max_drawdown' from AtesData"
    MAXDRAWDOWN_VAL = "validating 'max_drawdown' of AtesData"
    MAXTEMPSPREADWARM_SET = "setting 'max_temperature_spread_warm' of AtesData"
    MAXTEMPSPREADWARM_GET = "getting 'max_temperature_spread_warm' from AtesData"
    MAXTEMPSPREADWARM_VAL = "validating 'max_temperature_spread_warm' of AtesData"
    MAXTEMPSPREADCOLD_SET = "setting 'max_temperature_spread_cold' of AtesData"
    MAXTEMPSPREADCOLD_GET = "getting 'max_temperature_spread_cold' from AtesData"
    MAXTEMPSPREADCOLD_VAL = "validating 'max_temperature_spread_cold' of AtesData"
    AVAILABLEAREA_SET = "setting 'available_area' of AtesData"
    AVAILABLEAREA_GET = "getting 'available_area' from AtesData"
    AVAILABLEAREA_VAL = "validating 'available_area' of AtesData"
    SCHEDULEID_ADD = "adding to 'schedule_ids' of AtesData"
    SCHEDULEID_VAL = "validating 'schedule_ids' of AtesData"
    PHASEW2CSTART_SET = "setting 'phase_w2c_start' of AtesData"
    PHASEW2CSTART_GET = "getting 'phase_w2c_start' from AtesData"
    PHASEW2CSTART_VAL = "validating 'phase_w2c_start' of AtesData"
    PHASEW2CEND_SET = "setting 'phase_w2c_end' of AtesData"
    PHASEW2CEND_GET = "getting 'phase_w2c_end' from AtesData"
    PHASEW2CEND_VAL = "validating 'phase_w2c_end' of AtesData"
    PHASEC2WSTART_SET = "setting 'phase_c2w_start' of AtesData"
    PHASEC2WSTART_GET = "getting 'phase_c2w_start' from AtesData"
    PHASEC2WSTART_VAL = "validating 'phase_c2w_start' of AtesData"
    PHASEC2WEND_SET = "setting 'phase_c2w_end' of AtesData"
    PHASEC2WEND_GET = "getting 'phase_c2w_end' from AtesData"
    PHASEC2WEND_VAL = "validating 'phase_c2w_end' of AtesData"
    PHASES_VAL = "validating phases of AtesData"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/ates_data"
"""String identifying the ATES data module for logging purposes"""

DEF_AVAILABLEAREA: float = float("inf")
"""Default value for parameter 'available_area' of AtesData"""


class AtesData:
    """
    Class to hold ATES (Aquifer Thermal Energy Storage) data. Manages schedules
    and validation methods to control data integrity
    """

    # ------------------------ #
    # Property: darcy_velocity #
    # ------------------------ #
    def get_darcy_velocity(self, h: HubId) -> Value:
        """
        Get the Darcy groundwater velocity which influences the thermal radius of
        ATES wells. This parameter is mandatory if one of the  parameters
        'thermal_radius_per_warm_well', 'thermal_radius_per_cold_well' from the
        AtesTechs dataclass is not set, since then the groundwater velocity
        is required to calculate it.

        :param h: Hub
        :type h: HubId
        :return: Darcy velocity
        :rtype: Value
        """
        if h not in self._darcy_velocity:
            raise exceptions.MissingIdException(
                ExceptionKey.DARCYVELOCITY_GET.value, h, module=LOG_MODULE_STR
            )
        return self._darcy_velocity[h]

    def set_darcy_velocity(self, h: HubId, darcy_velocity: Value) -> None:
        """
        Set the the Darcy groundwater velocity which influences the thermal radius of
        ATES wells. This parameter is mandatory if one of the  parameters
        'thermal_radius_per_warm_well', 'thermal_radius_per_cold_well' from the
        AtesTechs dataclass is not set, since then the groundwater velocity
        is required to calculate it.

        :param h: Hub
        :type h: HubId
        :param darcy_velocity: Darcy groundwater velocity
        :type darcy_velocity: Value
        """
        expected_unit = LengthUnit.M / TimeUnit.D
        if not darcy_velocity.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.DARCYVELOCITY_SET.value,
                [h],
                f"Unit of darcy_velocity[{h}] = {darcy_velocity} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._darcy_velocity[h] = darcy_velocity

    # ----------------------- #
    # Property: Pore velocity #
    # ----------------------- #
    def get_pore_velocity(self, h: HubId) -> Value:
        """
        Get the pore groundwater velocity which influences the thermal radius of
        ATES wells. This parameter is calculated as the Darcy velocity divided
        by the porosity of the aquifer.

        :param h: Hub
        :type h: HubId
        :return: Pore velocity
        :rtype: Value
        """
        darcy_velo = self.get_darcy_velocity(h)
        porosity_aq = self.get_porosity_aquifer(h)
        return darcy_velo / porosity_aq

    # ---------------------- #
    # Property: density_rock #
    # ---------------------- #
    def get_density_rock(self, h: HubId) -> Value:
        """
        Get the density of the aquifer's rock material. This parameter is
        mandatory if one of the parameters 'thermal_radius_per_warm_well',
        'thermal_radius_per_cold_well' from the AtesTechs dataclass is not
        set, since then the density is then required to
        calculate it.

        :param h: Hub
        :type h: HubId
        :return: Density
        :rtype: Value
        """
        if h not in self._density_rock:
            raise exceptions.MissingIdException(
                ExceptionKey.DENSITYROCK_GET.value, h, module=LOG_MODULE_STR
            )
        return self._density_rock[h]

    def set_density_rock(self, h: HubId, density_rock: Value) -> None:
        """
        Set the density of the aquifer's rock material. This parameter is
        mandatory if one of the parameters 'thermal_radius_per_warm_well',
        'thermal_radius_per_cold_well' from the AtesTechs dataclass is not
        set, since then the density is then required to
        calculate it.

        :param h: Hub
        :type h: HubId
        :param density_rock: Density
        :type density_rock: Value
        """
        expected_unit = MassUnit.KG / (LengthUnit.M**3)
        if not density_rock.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.DENSITYROCK_SET.value,
                [h],
                f"Unit of density_rock[{h}] = {density_rock} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._density_rock[h] = density_rock

    # ------------------------------------- #
    # Property: specific_heat_capacity_rock #
    # ------------------------------------- #
    def get_specific_heat_capacity_rock(self, h: HubId) -> Value:
        """
        Get the specific heat capacity of the aquifer's rock material. This parameter is
        mandatory if one of the parameters 'thermal_radius_per_warm_well',
        'thermal_radius_per_cold_well' from the AtesTechs dataclass is not
        set, since then the specific heat capacity is then required to
        calculate it.

        :param h: Hub
        :type h: HubId
        :return: Specific heat capacity
        :rtype: Value
        """
        if h not in self._specific_heat_capacity_rock:
            raise exceptions.MissingIdException(
                ExceptionKey.SPECIFICHEATCAPROCK_GET.value, h, module=LOG_MODULE_STR
            )
        return self._specific_heat_capacity_rock[h]

    def set_specific_heat_capacity_rock(
        self, h: HubId, spec_heat_cap_rock: Value
    ) -> None:
        """
        Set the specific heat capacity of the aquifer's rock material. This parameter is
        mandatory if one of the parameters 'thermal_radius_per_warm_well',
        'thermal_radius_per_cold_well' from the AtesTechs dataclass is not
        set, since then the specific heat capacity is then required to
        calculate it.

        :param h: Hub
        :type h: HubId
        :param spec_heat_cap_aq: Specific heat capacity
        :type spec_heat_cap_rock: Value
        """
        expected_unit = (PowerUnit.KW * TimeUnit.H) / (MassUnit.KG * TemperatureUnit.K)
        if not spec_heat_cap_rock.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.SPECIFICHEATCAPROCK_SET.value,
                [h],
                f"Unit of spec_heat_cap_rock[{h}] = {spec_heat_cap_rock} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._specific_heat_capacity_rock[h] = spec_heat_cap_rock

    # --------------------------------------- #
    # Property: volumetric_heat_capacity_rock #
    # --------------------------------------- #
    def get_volumetric_heat_capacity_rock(self, h: HubId) -> Value:
        """
        Get the volumetric heat capacity of the aquifer's rock material. This
        parameter is calculated as the product of density and specific heat
        capacity of the rock material.

        :param h: Hub
        :type h: HubId
        :return: Volumetric heat capacity
        :rtype: Value
        """
        density_rock = self.get_density_rock(h)
        spec_heat_cap_rock = self.get_specific_heat_capacity_rock(h)
        return density_rock * spec_heat_cap_rock

    # --------------------------- #
    # Property: thickness_aquifer #
    # --------------------------- #
    def get_thickness_aquifer(self, h: HubId) -> Value:
        """
        Get the thickness (i.e.; the height) of the aquifer. This parameter is
        mandatory if one of the parameters 'thermal_radius_per_warm_well',
        'thermal_radius_per_cold_well' from the AtesTechs dataclass is not
        set, since then the aquifer thickness is then required to calculate it.

        :param h: Hub
        :type h: HubId
        :return: Aquifer thickness
        :rtype: Value
        """
        if h not in self._thickness_aquifer:
            raise exceptions.MissingIdException(
                ExceptionKey.THICKNESSAQ_GET.value, h, module=LOG_MODULE_STR
            )
        return self._thickness_aquifer[h]

    def set_thickness_aquifer(self, h: HubId, thickness_aquifer: Value) -> None:
        """
        Set the thickness (i.e.; the height) of the aquifer. This parameter is
        mandatory if one of the parameters 'thermal_radius_per_warm_well',
        'thermal_radius_per_cold_well' from the AtesTechs dataclass is not
        set, since then the aquifer thickness is then required to calculate it.

        :param h: Hub
        :type h: HubId
        :param thickness_aquifer: Aquifer thickness
        :type thickness_aquifer: Value
        """
        expected_unit = LengthUnit.M
        if not thickness_aquifer.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.THICKNESSAQ_SET.value,
                [h],
                f"Unit of thickness_aquifer[{h}] = {thickness_aquifer} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._thickness_aquifer[h] = thickness_aquifer

    # ---------------------------------------- #
    # Property: hydraulic_conductivity_aquifer #
    # ---------------------------------------- #
    def get_hydraulic_conductivity_aquifer(self, h: HubId) -> Value:
        """
        Get the hydraulic conductivity of the aquifer which indicates the ease
        and speed of groundwater flow. This parameter is mandatory if one of
        the  parameters 'thermal_radius_per_warm_well',
        'thermal_radius_per_cold_well' from the AtesTechs dataclass is not
        set, since then the hydraulic conductivity is then required to
        calculate it.

        :param h: Hub
        :type h: HubId
        :return: Hydraulic conductivity [m/d]
        :rtype: Value
        """
        if h not in self._hydraulic_conductivity_aquifer:
            raise exceptions.MissingIdException(
                ExceptionKey.HYDRAULICCONDUCTAQ_GET.value, h, module=LOG_MODULE_STR
            )
        return self._hydraulic_conductivity_aquifer[h]

    def set_hydraulic_conductivity_aquifer(self, h: HubId, hyd_cond_aq: Value) -> None:
        """
        Set the hydraulic conductivity of the aquifer which indicates the ease
        and speed of groundwater flow. This parameter is mandatory if one of
        the  parameters 'max_pump_rate_per_warm_well',
        'max_pump_rate_per_cold_well' from the AtesTechs dataclass is not
        set, since then the hydraulic conductivity is then required to
        calculate it.

        :param h: Hub
        :type h: HubId
        :param hyd_cond_aq: Hydraulic conductivity
        :type hyd_cond_aq: Value
        """
        expected_unit = LengthUnit.M / TimeUnit.D
        if not hyd_cond_aq.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.HYDRAULICCONDUCTAQ_SET.value,
                [h],
                f"Unit of hyd_cond_aq[{h}] = {hyd_cond_aq} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._hydraulic_conductivity_aquifer[h] = hyd_cond_aq

    # ------------------------------------------ #
    # Property: hydraulic_transmissivity_aquifer #
    # ------------------------------------------ #
    def get_hydraulic_transmissivity_aquifer(self, h: HubId) -> Value:
        """
        Get the hydraulic transmissivity of the aquifer which represents the
        aquifer's ability to transmit water. This parameter is not set
        directly but calculated as the product of hydraulic conductivity and
        aquifer thickness.

        :param h: Hub
        :type h: HubId
        :return: Hydraulic transmissivity
        :rtype: Value
        """
        hyd_cond_aq = self.get_hydraulic_conductivity_aquifer(h)
        thickness_aq = self.get_thickness_aquifer(h)
        return hyd_cond_aq * thickness_aq

    # -------------------------- #
    # Property: porosity_aquifer #
    # -------------------------- #
    def get_porosity_aquifer(self, h: HubId) -> Value:
        """
        Get the porosity of the aquifer which indicates the ease
        and speed of groundwater flow. XXX This parameter is mandatory if one of
        the  parameters 'thermal_radius_per_warm_well',
        'thermal_radius_per_cold_well' from the AtesTechs dataclass is not
        set, since then the hydraulic conductivity is then required to
        calculate it.

        :param h: Hub
        :type h: HubId
        :return: Porosity [-]
        :rtype: Value
        """
        if h not in self._porosity_aquifer:
            raise exceptions.MissingIdException(
                ExceptionKey.POROSITYAQ_GET.value, h, module=LOG_MODULE_STR
            )
        return self._porosity_aquifer[h]

    def set_porosity_aquifer(self, h: HubId, porosity_aq: Value) -> None:
        """
        Set the porosity of the aquifer which indicates the ease
        and speed of groundwater flow. XXX This parameter is mandatory if one of
        the  parameters 'thermal_radius_per_warm_well',
        'thermal_radius_per_cold_well' from the AtesTechs dataclass is not
        set, since then the hydraulic conductivity is then required to
        calculate it.

        :param h: Hub
        :type h: HubId
        :param porosity_aq: Porosity
        :type porosity_aq: Value
        """
        expected_unit = DimlessUnit()
        if not porosity_aq.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.POROSITYAQ_SET.value,
                [h],
                f"Unit of porosity_aq[{h}] = {porosity_aq} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._porosity_aquifer[h] = porosity_aq

    # ---------------------- #
    # Property: max_drawdown #
    # ---------------------- #
    def get_max_drawdown(self, h: HubId) -> Value:
        """
        Get the maximal allowed drawdown (i.e.; the surface decline) at the
        border of an ATES well. This parameter is
        mandatory if one of the  parameters 'max_pump_rate_per_warm_well',
        'max_pump_rate_per_cold_well' from the AtesTechs dataclass is not
        set, since then the maximal drawdown is then required to calculate it.

        :param h: Hub
        :type h: HubId
        :return: Maximal drawdown
        :rtype: Value
        """
        if h not in self._max_drawdown:
            raise exceptions.MissingIdException(
                ExceptionKey.MAXDRAWDOWN_GET.value, h, module=LOG_MODULE_STR
            )
        return self._max_drawdown[h]

    def set_max_drawdown(self, h: HubId, max_drawdown: Value) -> None:
        """
        Set the maximal allowed drawdown (i.e.; the surface decline) at the
        border of an ATES well. This parameter is
        mandatory if one of the  parameters 'max_pump_rate_per_warm_well',
        'max_pump_rate_per_cold_well' from the AtesTechs dataclass is not
        set, since then the maximal drawdown is then required to calculate it.

        :param h: Hub
        :type h: HubId
        :param max_drawdown: Maximal drawdown
        :type max_drawdown: Value
        """
        expected_unit = LengthUnit.M
        if not max_drawdown.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.MAXDRAWDOWN_SET.value,
                [h],
                f"Unit of max_drawdown[{h}] = {max_drawdown} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._max_drawdown[h] = max_drawdown

    # ------------------------------------- #
    # Property: max_temperature_spread_warm #
    # ------------------------------------- #
    def get_max_temperature_spread_warm(self, h: HubId) -> Value:
        """
        Get the maximal allowed temperature spread between the natural aquifer
        temperature and the temperature of fluid in the warm wells. This is a
        mandatory parameter.

        :param h: Hub
        :type h: HubId
        :return: Maximal temperature spread for warm wells
        :rtype: Value
        """
        if h not in self._max_temperature_spread_warm:
            raise exceptions.MissingIdException(
                ExceptionKey.MAXTEMPSPREADWARM_GET.value, h, module=LOG_MODULE_STR
            )
        return self._max_temperature_spread_warm[h]

    def set_max_temperature_spread_warm(
        self, h: HubId, max_temp_spread_warm: Value
    ) -> None:
        """
        Set the maximal allowed temperature spread between the natural aquifer
        temperature and the temperature of fluid in the warm wells. This is a
        mandatory parameter.

        :param h: Hub
        :type h: HubId
        :param max_temp_spread_warm: Maximal temperature spread for warm wells
        :type max_temp_spread_warm: Value
        """
        expected_unit = TemperatureUnit.K
        if not max_temp_spread_warm.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.MAXTEMPSPREADWARM_SET.value,
                [h],
                f"Unit of max_temp_spread_warm[{h}] = {max_temp_spread_warm} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._max_temperature_spread_warm[h] = max_temp_spread_warm

    # ------------------------------------- #
    # Property: max_temperature_spread_cold #
    # ------------------------------------- #
    def get_max_temperature_spread_cold(self, h: HubId) -> Value:
        """
        Get the maximal allowed temperature spread between the natural aquifer
        temperature and the temperature of fluid in the cold wells. This is a
        mandatory parameter.

        :param h: Hub
        :type h: HubId
        :return: Maximal temperature spread for cold wells
        :rtype: Value
        """
        if h not in self._max_temperature_spread_cold:
            raise exceptions.MissingIdException(
                ExceptionKey.MAXTEMPSPREADCOLD_GET.value, h, module=LOG_MODULE_STR
            )
        return self._max_temperature_spread_cold[h]

    def set_max_temperature_spread_cold(
        self, h: HubId, max_temp_spread_cold: Value
    ) -> None:
        """
        Set the maximal allowed temperature spread between the natural aquifer
        temperature and the temperature of fluid in the cold wells. This is a
        mandatory parameter.

        :param h: Hub
        :type h: HubId
        :param max_temp_spread_cold: Maximal temperature spread for cold wells
        :type max_temp_spread_cold: Value
        """
        expected_unit = TemperatureUnit.K
        if not max_temp_spread_cold.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.MAXTEMPSPREADCOLD_SET.value,
                [h],
                f"Unit of max_temp_spread_cold[{h}] = {max_temp_spread_cold} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._max_temperature_spread_cold[h] = max_temp_spread_cold

    # ------------------------ #
    # Property: available_area #
    # ------------------------ #
    def get_available_area(self, s: StageId, h: HubId) -> Value:
        """
        Get the available area which can be used to install ATES technologies.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :return: Available area for ATES wells
        :rtype: Value
        """
        available_area = self._available_area.get(
            (s, h), Value(DEF_AVAILABLEAREA, LengthUnit.M**2)
        )
        return available_area

    def set_available_area(self, s: StageId, h: HubId, available_area: Value) -> None:
        """
        Set the available area which can be used to install ATES technologies.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param available_area: Available area for ATES wells
        :type available_area: Value
        """
        expected_unit = LengthUnit.M**2
        if not available_area.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.AVAILABLEAREA_SET.value,
                [s, h],
                f"Unit of available_area[{h}] = {available_area} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._available_area[s, h] = available_area

    # ---------------------- #
    # Property: schedule_ids #
    # ---------------------- #
    def get_schedule_ids(self, h: HubId) -> Set[AtesScheduleId]:
        """
        Get the set of all ATES schedules ids for a hub

        :param h: Hub
        :type h: HubId
        :return: Set of ATES schedules
        :rtype: Set[AtesScheduleId]
        """
        return self._schedule_ids.get(h, set())

    def add_schedule_id(self, h: HubId, i: AtesScheduleId) -> None:
        """
        Add a new ATES schedule id for a hub

        :param h: Hub
        :type h: HubId
        :param i: Id to be added
        :type x: AtesScheduleId
        """
        if h not in self._schedule_ids:
            self._schedule_ids[h] = set()
        if i in self._schedule_ids[h]:
            raise exceptions.DuplicateIdException(
                ExceptionKey.SCHEDULEID_ADD.value, i, module=LOG_MODULE_STR
            )
        self._schedule_ids[h].add(i)

    # ------------------------- #
    # Property: phase_w2c_start #
    # ------------------------- #
    def get_phase_w2c_start(self, h: HubId, i: AtesScheduleId) -> TimeId:
        """
        Get the first horizon time index of an ATES schedule's warm-to-cold
        phase. If the start of a phase is smaller or equal to the end of a
        phase, the phase is interpreted as a connected time interval.
        Otherwise, it is interpreted as a set of two intervals, one from the
        phase start to the horizon end and the other from the horizon start to
        the phase end. The warm-to-cold and cold-to-warm phases of a schedule
        must not overlap. This is a mandatory parameter.

        :param h: Hub
        :type h: HubId
        :param i: ATES schedule
        :type i: AtesScheduleId
        :return: Start of warm-to-cold phase
        :rtype: TimeId
        """
        self._check_id(h, i, ExceptionKey.PHASEW2CSTART_GET)
        if (h, i) not in self._phase_w2c_start:
            raise exceptions.MissingIdsException(
                ExceptionKey.PHASEW2CSTART_GET.value, [h, i], module=LOG_MODULE_STR
            )
        return self._phase_w2c_start[h, i]

    def set_phase_w2c_start(
        self, h: HubId, i: AtesScheduleId, phase_w2c_start: TimeId
    ) -> None:
        """
        Set the first horizon time index of an ATES schedule's warm-to-cold
        phase. If the start of a phase is smaller or equal to the end of a
        phase, the phase is interpreted as a connected time interval.
        Otherwise, it is interpreted as a set of two intervals, one from the
        phase start to the horizon end and the other from the horizon start to
        the phase end. The warm-to-cold and cold-to-warm phases of a schedule
        must not overlap. This is a mandatory parameter.

        :param h: Hub
        :type h: HubId
        :param i: ATES schedule
        :type i: AtesScheduleId
        :param phase_w2c_start: Start of warm-to-cold phase
        :type phase_w2c_start: TimeId
        """
        self._check_id(h, i, ExceptionKey.PHASEW2CSTART_SET)
        self._phase_w2c_start[h, i] = phase_w2c_start

    # ----------------------- #
    # Property: phase_w2c_end #
    # ----------------------- #
    def get_phase_w2c_end(self, h: HubId, i: AtesScheduleId) -> TimeId:
        """
        Get the last horizon time index of an ATES schedule's warm-to-cold
        phase. If the start of a phase is smaller or equal to the end of a
        phase, the phase is interpreted as a connected time interval.
        Otherwise, it is interpreted as a set of two intervals, one from the
        phase start to the horizon end and the other from the horizon start to
        the phase end. The warm-to-cold and cold-to-warm phases of a schedule
        must not overlap. This is a mandatory parameter.

        :param h: Hub
        :type h: HubId
        :param i: ATES schedule
        :type i: AtesScheduleId
        :return: End of warm-to-cold phase
        :rtype: TimeId
        """
        self._check_id(h, i, ExceptionKey.PHASEW2CEND_GET)
        if (h, i) not in self._phase_w2c_end:
            raise exceptions.MissingIdsException(
                ExceptionKey.PHASEW2CEND_GET.value, [h, i], module=LOG_MODULE_STR
            )
        return self._phase_w2c_end[h, i]

    def set_phase_w2c_end(
        self, h: HubId, i: AtesScheduleId, phase_w2c_end: TimeId
    ) -> None:
        """
        Set the last horizon time index of an ATES schedule's warm-to-cold
        phase. If the start of a phase is smaller or equal to the end of a
        phase, the phase is interpreted as a connected time interval.
        Otherwise, it is interpreted as a set of two intervals, one from the
        phase start to the horizon end and the other from the horizon start to
        the phase end. The warm-to-cold and cold-to-warm phases of a schedule
        must not overlap. This is a mandatory parameter.

        :param h: Hub
        :type h: HubId
        :param i: ATES schedule
        :type i: AtesScheduleId
        :param phase_w2c_end: End of warm-to-cold phase
        :type phase_w2c_end: TimeId
        """
        self._check_id(h, i, ExceptionKey.PHASEW2CEND_SET)
        self._phase_w2c_end[h, i] = phase_w2c_end

    # ------------------------- #
    # Property: phase_c2w_start #
    # ------------------------- #
    def get_phase_c2w_start(self, h: HubId, i: AtesScheduleId) -> TimeId:
        """
        Get the first horizon time index of an ATES schedule's cold-to-warm
        phase. If the start of a phase is smaller or equal to the end of a
        phase, the phase is interpreted as a connected time interval.
        Otherwise, it is interpreted as a set of two intervals, one from the
        phase start to the horizon end and the other from the horizon start to
        the phase end. The warm-to-cold and cold-to-warm phases of a schedule
        must not overlap. This is a mandatory parameter.

        :param h: Hub
        :type h: HubId
        :param i: ATES schedule
        :type i: AtesScheduleId
        :return: Start of cold-to-warm phase
        :rtype: TimeId
        """
        self._check_id(h, i, ExceptionKey.PHASEC2WSTART_GET)
        if (h, i) not in self._phase_c2w_start:
            raise exceptions.MissingIdsException(
                ExceptionKey.PHASEC2WSTART_GET.value, [h, i], module=LOG_MODULE_STR
            )
        return self._phase_c2w_start[h, i]

    def set_phase_c2w_start(
        self, h: HubId, i: AtesScheduleId, phase_c2w_start: TimeId
    ) -> None:
        """
        Set the first horizon time index of an ATES schedule's cold-to-warm
        phase. If the start of a phase is smaller or equal to the end of a
        phase, the phase is interpreted as a connected time interval.
        Otherwise, it is interpreted as a set of two intervals, one from the
        phase start to the horizon end and the other from the horizon start to
        the phase end. The warm-to-cold and cold-to-warm phases of a schedule
        must not overlap. This is a mandatory parameter.

        :param h: Hub
        :type h: HubId
        :param i: ATES schedule
        :type i: AtesScheduleId
        :param phase_c2w_start: Start of cold-to-warm phase
        :type phase_c2w_start: TimeId
        """
        self._check_id(h, i, ExceptionKey.PHASEC2WSTART_SET)
        self._phase_c2w_start[h, i] = phase_c2w_start

    # ----------------------- #
    # Property: phase_c2w_end #
    # ----------------------- #
    def get_phase_c2w_end(self, h: HubId, i: AtesScheduleId) -> TimeId:
        """
        Get the last horizon time index of an ATES schedule's cold-to-warm
        phase. If the start of a phase is smaller or equal to the end of a
        phase, the phase is interpreted as a connected time interval.
        Otherwise, it is interpreted as a set of two intervals, one from the
        phase start to the horizon end and the other from the horizon start to
        the phase end. The warm-to-cold and cold-to-warm phases of a schedule
        must not overlap. This is a mandatory parameter.

        :param h: Hub
        :type h: HubId
        :param i: ATES schedule
        :type i: AtesScheduleId
        :return: End of cold-to-warm phase
        :rtype: TimeId
        """
        self._check_id(h, i, ExceptionKey.PHASEC2WEND_GET)
        if (h, i) not in self._phase_c2w_end:
            raise exceptions.MissingIdsException(
                ExceptionKey.PHASEC2WEND_GET.value, [h, i], module=LOG_MODULE_STR
            )
        return self._phase_c2w_end[h, i]

    def set_phase_c2w_end(
        self, h: HubId, i: AtesScheduleId, phase_c2w_end: TimeId
    ) -> None:
        """
        Set the last horizon time index of an ATES schedule's cold-to-warm
        phase. If the start of a phase is smaller or equal to the end of a
        phase, the phase is interpreted as a connected time interval.
        Otherwise, it is interpreted as a set of two intervals, one from the
        phase start to the horizon end and the other from the horizon start to
        the phase end. The warm-to-cold and cold-to-warm phases of a schedule
        must not overlap. This is a mandatory parameter.

        :param h: Hub
        :type h: HubId
        :param i: ATES schedule
        :type i: AtesScheduleId
        :param phase_c2w_end: End of cold-to-warm phase
        :type phase_c2w_end: TimeId
        """
        self._check_id(h, i, ExceptionKey.PHASEC2WEND_SET)
        self._phase_c2w_end[h, i] = phase_c2w_end

    # -------------- #
    # Phase checkers #
    # -------------- #
    def is_in_w2c_phase(self, h: HubId, i: AtesScheduleId, t: TimeId) -> bool:
        """
        Checks whether a given time index is part of an ATES schedule's
        warm-to-cold phase.

        :param h: Hub
        :type h: HubId
        :param i: ATES schedule
        :type i: AtesScheduleId
        :param t: Time
        :type t: TimeId
        :return: Whether the time index is part of the warm-to-cold phase
        :rtype: bool
        """
        t_start = self.get_phase_w2c_start(h, i)
        t_end = self.get_phase_w2c_end(h, i)
        # Phase is given by [t_start, t_end] with t_start <= t_end
        if t_start.key_as_int <= t_end.key_as_int:
            return (t_start.key_as_int <= t.key_as_int) and (
                t.key_as_int <= t_end.key_as_int
            )
        # Phase is given by [t_first, t_end] + [t_start, t_last]
        # with t_end <= t_start
        return (t.key_as_int <= t_end.key_as_int) or (
            t_start.key_as_int <= t.key_as_int
        )

    def is_in_c2w_phase(self, h: HubId, i: AtesScheduleId, t: TimeId) -> bool:
        """
        Checks whether a given time index is part of an ATES schedule's
        cold-to-warm phase.

        :param h: Hub
        :type h: HubId
        :param i: ATES schedule
        :type i: AtesScheduleId
        :param t: Time
        :type t: TimeId
        :return: Whether the time index is part of the cold-to-warm phase
        :rtype: bool
        """
        t_start = self.get_phase_c2w_start(h, i)
        t_end = self.get_phase_c2w_end(h, i)
        # Phase is given by [t_start, t_end]
        if t_start.key_as_int <= t_end.key_as_int:
            return (t_start.key_as_int <= t.key_as_int) and (
                t.key_as_int <= t_end.key_as_int
            )
        # Phase is given by [t_first, t_end] + [t_start, t_last]
        return (t.key_as_int <= t_end.key_as_int) or (
            t_start.key_as_int <= t.key_as_int
        )

    # --------------- #
    # Phase durations #
    # --------------- #
    def get_phase_duration_w2c(
        self, h: HubId, i: AtesScheduleId, times: Times
    ) -> Value:
        """
        Get the duration of an ATES schedule's warm-to-cold phase.

        :param h: Hub
        :type h: HubId
        :param i: Schedule
        :type i: AtesScheduleId
        :param times: Times
        :type times: Times
        :return: Duration of warm-to-cold phase
        :rtype: Value
        """
        t_start = self.get_phase_w2c_start(h, i)
        t_end = self.get_phase_w2c_end(h, i)
        duration = self._get_phase_duration(t_start, t_end, times)
        return duration

    def get_phase_duration_c2w(
        self, h: HubId, i: AtesScheduleId, times: Times
    ) -> Value:
        """
        Get the duration of an ATES schedule's cold-to-warm phase.

        :param h: Hub
        :type h: HubId
        :param i: Schedule
        :type i: AtesScheduleId
        :param times: Times
        :type times: Times
        :return: Duration of cold-to-warm phase
        :rtype: Value
        """
        t_start = self.get_phase_c2w_start(h, i)
        t_end = self.get_phase_c2w_end(h, i)
        duration = self._get_phase_duration(t_start, t_end, times)
        return duration

    def _get_phase_duration(
        self, t_start: TimeId, t_end: TimeId, times: Times
    ) -> Value:
        # Phase is given by [t_start, t_end] with t_start <= t_end
        if t_start.key_as_int <= t_end.key_as_int:
            duration_fl = t_end.key_as_int - t_start.key_as_int + 1
            return Value(duration_fl, TimeUnit.H)
        # Phase is given by [t_first, t_end] + [t_start, t_last]
        t_first = times.first_horizon_id
        t_last = times.last_horizon_id
        duration_fl = (t_end.key_as_int - t_first.key_as_int + 1) + (
            t_last.key_as_int - t_start.key_as_int + 1
        )
        duration = Value(duration_fl, TimeUnit.H)
        return duration

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._darcy_velocity: Dict[HubId, Value] = {}
        self._density_rock: Dict[HubId, Value] = {}
        self._specific_heat_capacity_rock: Dict[HubId, Value] = {}
        self._thickness_aquifer: Dict[HubId, Value] = {}
        self._hydraulic_conductivity_aquifer: Dict[HubId, Value] = {}
        self._porosity_aquifer: Dict[HubId, Value] = {}
        self._max_drawdown: Dict[HubId, Value] = {}
        self._max_temperature_spread_warm: Dict[HubId, Value] = {}
        self._max_temperature_spread_cold: Dict[HubId, Value] = {}
        self._available_area: Dict[Tuple[StageId, HubId], Value] = {}
        self._schedule_ids: Dict[HubId, Set[AtesScheduleId]] = {}
        self._phase_w2c_start: Dict[Tuple[HubId, AtesScheduleId], TimeId] = {}
        self._phase_w2c_end: Dict[Tuple[HubId, AtesScheduleId], TimeId] = {}
        self._phase_c2w_start: Dict[Tuple[HubId, AtesScheduleId], TimeId] = {}
        self._phase_c2w_end: Dict[Tuple[HubId, AtesScheduleId], TimeId] = {}

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self, stages: Stages, hubs: Hubs, times: Times) -> None:
        """
        Validate all ATES data in this object. Apart from sense-checking
        parameters in terms of quantity, this includes checking whether the ids
        from other data classes used here are known there as well.

        :param stages: Stages data class
        :type stages: Stages
        :param hubs: Hubs data class
        :type hubs: Hubs
        :param times: Times data class
        :type times: Times
        """
        self._validate_darcy_velocity(hubs)
        self._validate_spec_heat_cap_aq(hubs)
        self._validate_thickness_aq(hubs)
        self._validate_hydr_cond_aq(hubs)
        self._validate_porosity_aq(hubs)
        self._validate_max_drawdown(hubs)
        self._validate_max_temp_spread_warm(hubs)
        self._validate_max_temp_spread_cold(hubs)
        self._validate_available_area(stages, hubs)
        self._validate_phase_w2c_start(hubs, times)
        self._validate_phase_w2c_end(hubs, times)
        self._validate_phase_c2w_start(hubs, times)
        self._validate_phase_c2w_end(hubs, times)
        self._validate_phases()

    def _validate_darcy_velocity(self, hubs: Hubs) -> None:
        exc_key = ExceptionKey.DARCYVELOCITY_VAL.value
        for h, velo in self._darcy_velocity.items():
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in darcy_velocity[{h}]"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)
            if velo.is_negative:
                msg = f"{velo} = darcy_velocity[{h}] < 0"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)

    def _validate_spec_heat_cap_aq(self, hubs: Hubs) -> None:
        exc_key = ExceptionKey.SPECIFICHEATCAPROCK_VAL.value
        for h, _ in self._specific_heat_capacity_rock.items():
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in specific_heat_capacity_aquifer[{h}]"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)

    def _validate_thickness_aq(self, hubs: Hubs) -> None:
        exc_key = ExceptionKey.THICKNESSAQ_VAL.value
        for h, _ in self._thickness_aquifer.items():
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in thickness_aquifer[{h}]"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)

    def _validate_hydr_cond_aq(self, hubs: Hubs) -> None:
        exc_key = ExceptionKey.HYDRAULICCONDUCTAQ_VAL.value
        for h, _ in self._hydraulic_conductivity_aquifer.items():
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in hydraulic_conductivity_aquifer[{h}]"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)

    def _validate_porosity_aq(self, hubs: Hubs) -> None:
        exc_key = ExceptionKey.POROSITYAQ_VAL.value
        for h, porosity in self._porosity_aquifer.items():
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in porosity_aquifer[{h}]"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)
            if porosity <= Value(common.EPS_ZEROCHECK):
                msg = f"{porosity} = porosity_aquifer[{h}] <= 0"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)

    def _validate_max_drawdown(self, hubs: Hubs) -> None:
        exc_key = ExceptionKey.MAXDRAWDOWN_VAL.value
        for h, _ in self._max_drawdown.items():
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in max_drawdown[{h}]"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)

    def _validate_max_temp_spread_warm(self, hubs: Hubs) -> None:
        exc_key = ExceptionKey.MAXTEMPSPREADWARM_VAL.value
        for h, _ in self._max_temperature_spread_warm.items():
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in max_temperature_spread_warm[{h}]"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)

    def _validate_max_temp_spread_cold(self, hubs: Hubs) -> None:
        exc_key = ExceptionKey.MAXTEMPSPREADCOLD_VAL.value
        for h, _ in self._max_temperature_spread_cold.items():
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in max_temperature_spread_cold[{h}]"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)

    def _validate_available_area(self, stages: Stages, hubs: Hubs) -> None:
        exc_key = ExceptionKey.AVAILABLEAREA_VAL.value
        for (s, h), _ in self._available_area.items():
            if s not in stages.ids:
                msg = f"Unknown stage {s} in available_area[{s}, {h}]"
                raise exceptions.DataException(
                    exc_key, [s, h], msg, module=LOG_MODULE_STR
                )
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in available_area[{s}, {h}]"
                raise exceptions.DataException(
                    exc_key, [s, h], msg, module=LOG_MODULE_STR
                )

    def _validate_phase_w2c_start(self, hubs: Hubs, times: Times) -> None:
        exc_key = ExceptionKey.PHASEW2CSTART_VAL.value
        for (h, i), t in self._phase_w2c_start.items():
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in phase_w2c_start[{h}, {i}]"
                raise exceptions.DataException(
                    exc_key, [h, i, t], msg, module=LOG_MODULE_STR
                )
            if t not in times.ids_horizon:
                msg = f"Unknown time {t} = phase_w2c_start[{h}, {i}]"
                raise exceptions.DataException(
                    exc_key, [h, i, t], msg, module=LOG_MODULE_STR
                )

    def _validate_phase_w2c_end(self, hubs: Hubs, times: Times) -> None:
        exc_key = ExceptionKey.PHASEW2CEND_VAL.value
        for (h, i), t in self._phase_w2c_end.items():
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in phase_w2c_end[{h}, {i}]"
                raise exceptions.DataException(
                    exc_key, [h, i, t], msg, module=LOG_MODULE_STR
                )
            if t not in times.ids_horizon:
                msg = f"Unknown time {t} = phase_w2c_end[{h}, {i}]"
                raise exceptions.DataException(
                    exc_key, [h, i, t], msg, module=LOG_MODULE_STR
                )

    def _validate_phase_c2w_start(self, hubs: Hubs, times: Times) -> None:
        exc_key = ExceptionKey.PHASEC2WSTART_VAL.value
        for (h, i), t in self._phase_c2w_start.items():
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in phase_c2w_start[{h}, {i}]"
                raise exceptions.DataException(
                    exc_key, [h, i, t], msg, module=LOG_MODULE_STR
                )
            if t not in times.ids_horizon:
                msg = f"Unknown time {t} = phase_c2w_start[{h}, {i}]"
                raise exceptions.DataException(
                    exc_key, [h, i, t], msg, module=LOG_MODULE_STR
                )

    def _validate_phase_c2w_end(self, hubs: Hubs, times: Times) -> None:
        exc_key = ExceptionKey.PHASEC2WEND_VAL.value
        for (h, i), t in self._phase_c2w_end.items():
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in phase_c2w_end[{h}, {i}]"
                raise exceptions.DataException(
                    exc_key, [h, i, t], msg, module=LOG_MODULE_STR
                )
            if t not in times.ids_horizon:
                msg = f"Unknown time {t} = phase_c2w_end[{h}, {i}]"
                raise exceptions.DataException(
                    exc_key, [h, i, t], msg, module=LOG_MODULE_STR
                )

    def _validate_phases(self) -> None:
        exc_key = ExceptionKey.PHASES_VAL.value
        for h, schedules in self._schedule_ids.items():
            for i in schedules:
                msg = f"For hub {h} and ATES schedule {i}, "
                w2c_start = self.get_phase_w2c_start(h, i)
                w2c_end = self.get_phase_w2c_end(h, i)
                c2w_start = self.get_phase_c2w_start(h, i)
                c2w_end = self.get_phase_c2w_end(h, i)
                # Phase start and end must not be part of the other phase
                if self.is_in_c2w_phase(h, i, w2c_start):
                    msg += (
                        f"start of warm-to-cold phase (t={w2c_start}) "
                        "lies inside of cold-to-warm phase (t_start="
                        f"{c2w_start}, t_end={c2w_end})"
                    )
                    raise exceptions.DataException(
                        exc_key, [h, i, w2c_start], msg, module=LOG_MODULE_STR
                    )
                if self.is_in_c2w_phase(h, i, w2c_end):
                    msg += (
                        f"end of warm-to-cold phase (t={w2c_end}) "
                        "lies inside of cold-to-warm phase (t_start="
                        f"{c2w_start}, t_end={c2w_end})"
                    )
                    raise exceptions.DataException(
                        exc_key, [h, i, w2c_end], msg, module=LOG_MODULE_STR
                    )
                if self.is_in_w2c_phase(h, i, c2w_start):
                    msg += (
                        f"start of cold-to-warm phase (t={c2w_start}) "
                        "lies inside of warm-to-cold phase (t_start="
                        f"{w2c_start}, t_end={w2c_end})"
                    )
                    raise exceptions.DataException(
                        exc_key, [h, i, c2w_end], msg, module=LOG_MODULE_STR
                    )
                if self.is_in_w2c_phase(h, i, c2w_end):
                    msg += (
                        f"end of cold-to-warm phase (t={c2w_end}) "
                        "lies inside of warm-to-cold phase (t_start="
                        f"{w2c_start}, t_end={w2c_end})"
                    )
                    raise exceptions.DataException(
                        exc_key, [h, i, c2w_end], msg, module=LOG_MODULE_STR
                    )

    # ---------- #
    # Id checker #
    # ---------- #
    def _check_id(self, h: HubId, i: AtesScheduleId, key: ExceptionKey) -> None:
        if i not in self._schedule_ids.get(h, set()):
            msg = (
                f"Unknown ATES schedule id {i.key} for hub {h.key} detected while {key}"
            )
            raise exceptions.DataException(
                key.value, [h, i], msg, module=LOG_MODULE_STR
            )
