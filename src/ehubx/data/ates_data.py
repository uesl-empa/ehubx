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

    GROUNDWATERVELOCITY_SET = "setting 'groundwater_velocity' of AtesData"
    GROUNDWATERVELOCITY_GET = "getting 'groundwater_velocity' from AtesData"
    GROUNDWATERVELOCITY_VAL = "validating 'groundwater_velocity' of AtesData"
    SPECIFICHEATCAPAQ_SET = "setting specific_heat_capacity_aquifer of AtesData"
    SPECIFICHEATCAPAQ_GET = "getting specific_heat_capacity_aquifer from AtesData"
    SPECIFICHEATCAPAQ_VAL = "validating specific_heat_capacity_aquifer of AtesData"
    THICKNESSAQ_SET = "setting 'thickness_aq' of AtesData"
    THICKNESSAQ_GET = "getting 'thickness_aq' from AtesData"
    THICKNESSAQ_VAL = "validating 'thickness_aq' of AtesData"
    HYDRAULICCONDUCTAQ_SET = "setting 'hydraulic_conductivity_aquifer of AtesData"
    HYDRAULICCONDUCTAQ_GET = "getting 'hydraulic_conductivity_aquifer from AtesData"
    HYDRAULICCONDUCTAQ_VAL = "validating 'hydraulic_conductivity_aquifer of AtesData"
    HYDRAULICTRANSMISAQ_GET = "getting 'hydraulic_transmissivity_aquifer from AtesData"
    STORATIVITYAQ_SET = "setting 'storativity_aquifer' of AtesData"
    STORATIVITYAQ_GET = "getting 'storativity_aquifer' from AtesData"
    STORATIVITYAQ_VAL = "validating 'storativity_aquifer' of AtesData"
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

    # ------------------------------ #
    # Property: groundwater_velocity #
    # ------------------------------ #
    def get_groundwater_velocity(self, h: HubId) -> float:
        """
        Get the groundwater velocity (specifically the Darcy velocity) which
        influences the thermal radius of ATES wells. This parameter is
        mandatory if one of the  parameters 'thermal_radius_per_warm_well',
        'thermal_radius_per_cold_well' from the AtesTechs dataclass is not
        set, since then the groundwater velocity is required to calculate it.

        :param h: Hub
        :type h: HubId
        :return: Groundwater velocity [m/d]
        :rtype: float
        """
        if h not in self._groundwater_velocity:
            raise exceptions.MissingIdException(
                ExceptionKey.GROUNDWATERVELOCITY_GET.value, h, module=LOG_MODULE_STR
            )
        return self._groundwater_velocity[h]

    def set_groundwater_velocity(self, h: HubId, groundwater_velocity: float) -> None:
        """
        Set the groundwater velocity (specifically the Darcy velocity) which
        influences the thermal radius of ATES wells. This parameter is
        mandatory if one of the  parameters 'thermal_radius_per_warm_well',
        'thermal_radius_per_cold_well' from the AtesTechs dataclass is not
        set, since then the groundwater velocity is required to calculate it.

        :param h: Hub
        :type h: HubId
        :param groundwater_velocity: Groundwater velocity [m/d]
        :type groundwater_velocity: float
        """
        self._groundwater_velocity[h] = groundwater_velocity

    # ---------------------------------------- #
    # Property: specific_heat_capacity_aquifer #
    # ---------------------------------------- #
    def get_specific_heat_capacity_aquifer(self, h: HubId) -> float:
        """
        Get the specific heat capacity of the aquifer. This parameter is
        mandatory if one of the parameters 'thermal_radius_per_warm_well',
        'thermal_radius_per_cold_well' from the AtesTechs dataclass is not
        set, since then the specific heat capacity is then required to
        calculate it.

        :param h: Hub
        :type h: HubId
        :return: Specific heat capacity [J/(kg*K)]
        :rtype: float
        """
        if h not in self._specific_heat_capacity_aquifer:
            raise exceptions.MissingIdException(
                ExceptionKey.SPECIFICHEATCAPAQ_GET.value, h, module=LOG_MODULE_STR
            )
        return self._specific_heat_capacity_aquifer[h]

    def set_specific_heat_capacity_aquifer(
        self, h: HubId, spec_heat_cap_aq: float
    ) -> None:
        """
        Set the specific heat capacity of the aquifer. This parameter is
        mandatory if one of the parameters 'thermal_radius_per_warm_well',
        'thermal_radius_per_cold_well' from the AtesTechs dataclass is not
        set, since then the specific heat capacity is then required to
        calculate it.

        :param h: Hub
        :type h: HubId
        :param spec_heat_cap_aq: Specific heat capacity [J/(kg*K)]
        :type spec_heat_cap_aq: float
        """
        self._specific_heat_capacity_aquifer[h] = spec_heat_cap_aq

    # --------------------------- #
    # Property: thickness_aquifer #
    # --------------------------- #
    def get_thickness_aquifer(self, h: HubId) -> float:
        """
        Get the thickness (i.e.; the height) of the aquifer. This parameter is
        mandatory if one of the parameters 'thermal_radius_per_warm_well',
        'thermal_radius_per_cold_well' from the AtesTechs dataclass is not
        set, since then the aquifer thickness is then required to calculate it.

        :param h: Hub
        :type h: HubId
        :return: Aquifer thickness [m]
        :rtype: float
        """
        if h not in self._thickness_aquifer:
            raise exceptions.MissingIdException(
                ExceptionKey.THICKNESSAQ_GET.value, h, module=LOG_MODULE_STR
            )
        return self._thickness_aquifer[h]

    def set_thickness_aquifer(self, h: HubId, thickness_aquifer: float) -> None:
        """
        Set the thickness (i.e.; the height) of the aquifer. This parameter is
        mandatory if one of the parameters 'thermal_radius_per_warm_well',
        'thermal_radius_per_cold_well' from the AtesTechs dataclass is not
        set, since then the aquifer thickness is then required to calculate it.

        :param h: Hub
        :type h: HubId
        :param thickness_aquifer: Aquifer thickness [m]
        :type thickness_aquifer: float
        """
        self._thickness_aquifer[h] = thickness_aquifer

    # ---------------------------------------- #
    # Property: hydraulic_conductivity_aquifer #
    # ---------------------------------------- #
    def get_hydraulic_conductivity_aquifer(self, h: HubId) -> float:
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
        :rtype: float
        """
        if h not in self._hydraulic_conductivity_aquifer:
            raise exceptions.MissingIdException(
                ExceptionKey.HYDRAULICCONDUCTAQ_GET.value, h, module=LOG_MODULE_STR
            )
        return self._hydraulic_conductivity_aquifer[h]

    def set_hydraulic_conductivity_aquifer(self, h: HubId, hyd_cond_aq: float) -> None:
        """
        Set the hydraulic conductivity of the aquifer which indicates the ease
        and speed of groundwater flow. This parameter is mandatory if one of
        the  parameters 'max_pump_rate_per_warm_well',
        'max_pump_rate_per_cold_well' from the AtesTechs dataclass is not
        set, since then the hydraulic conductivity is then required to
        calculate it.

        :param h: Hub
        :type h: HubId
        :param hyd_cond_aq: Hydraulic conductivity [m/d]
        :type hyd_cond_aq: float
        """
        self._hydraulic_conductivity_aquifer[h] = hyd_cond_aq

    # ------------------------------------------ #
    # Property: hydraulic_transmissivity_aquifer #
    # ------------------------------------------ #
    def get_hydraulic_transmissivity_aquifer(self, h: HubId) -> float:
        """
        Get the hydraulic transmissivity of the aquifer which represents the
        aquifer's ability to transmit water. This parameter is not set
        directly but calculated as the product of hydraulic conductivity and
        aquifer thickness.

        :param h: Hub
        :type h: HubId
        :return: Hydraulic transmissivity [m^2/d]
        :rtype: float
        """
        hyd_cond_aq = self.get_hydraulic_conductivity_aquifer(h)
        thickenss_aq = self.get_thickness_aquifer(h)
        hyd_trans_aq = hyd_cond_aq * thickenss_aq
        return hyd_trans_aq

    # ----------------------------- #
    # Property: storativity_aquifer #
    # ----------------------------- #
    def get_storativity_aquifer(self, h: HubId) -> float:
        """
        Get the aquifer's storativity (or storage coefficient) which is the
        volume of water released from storage per unit decline in hydraulic
        head in the aquifer, per unit area of the aquifer. This parameter is
        mandatory if one of the  parameters 'max_pump_rate_per_warm_well',
        'max_pump_rate_per_cold_well' from the AtesTechs dataclass is not
        set, since then the storativity is then equired to calculate it.

        :param h: Hub
        :type h: HubId
        :return: Storativity [1]
        :rtype: float
        """
        if h not in self._storativity_aquifer:
            raise exceptions.MissingIdException(
                ExceptionKey.STORATIVITYAQ_GET.value, h, module=LOG_MODULE_STR
            )
        return self._storativity_aquifer[h]

    def set_storativity_aquifer(self, h: HubId, storativity_aquifer: float) -> None:
        """
        Set the aquifer's storativity (or storage coefficient) which is the
        volume of water released from storage per unit decline in hydraulic
        head in the aquifer, per unit area of the aquifer. This parameter is
        mandatory if one of the  parameters 'max_pump_rate_per_warm_well',
        'max_pump_rate_per_cold_well' from the AtesTechs dataclass is not
        set, since then the storativity is then required to calculate it.

        :param h: Hub
        :type h: HubId
        :param storativity_aquifer: Storativity [1]
        :type storativity_aquifer: float
        """
        self._storativity_aquifer[h] = storativity_aquifer

    # ---------------------- #
    # Property: max_drawdown #
    # ---------------------- #
    def get_max_drawdown(self, h: HubId) -> float:
        """
        Get the maximal allowed drawdown (i.e.; the surface decline) at the
        border of an ATES well. This parameter is
        mandatory if one of the  parameters 'max_pump_rate_per_warm_well',
        'max_pump_rate_per_cold_well' from the AtesTechs dataclass is not
        set, since then the maximal drawdown is then required to calculate it.

        :param h: Hub
        :type h: HubId
        :return: Maximal drawdown [m]
        :rtype: float
        """
        if h not in self._max_drawdown:
            raise exceptions.MissingIdException(
                ExceptionKey.MAXDRAWDOWN_GET.value, h, module=LOG_MODULE_STR
            )
        return self._max_drawdown[h]

    def set_max_drawdown(self, h: HubId, max_drawdown: float) -> None:
        """
        Set the maximal allowed drawdown (i.e.; the surface decline) at the
        border of an ATES well. This parameter is
        mandatory if one of the  parameters 'max_pump_rate_per_warm_well',
        'max_pump_rate_per_cold_well' from the AtesTechs dataclass is not
        set, since then the maximal drawdown is then required to calculate it.

        :param h: Hub
        :type h: HubId
        :param max_drawdown: Maximal drawdown [m]
        :type max_drawdown: float
        """
        self._max_drawdown[h] = max_drawdown

    # ------------------------------------- #
    # Property: max_temperature_spread_warm #
    # ------------------------------------- #
    def get_max_temperature_spread_warm(self, h: HubId) -> float:
        """
        Get the maximal allowed temperature spread between the natural aquifer
        temperature and the temperature of fluid in the warm wells. This is a
        mandatory parameter.

        :param h: Hub
        :type h: HubId
        :return: Maximal temperature spread for warm wells [°C]
        :rtype: float
        """
        if h not in self._max_temperature_spread_warm:
            raise exceptions.MissingIdException(
                ExceptionKey.MAXTEMPSPREADWARM_GET.value, h, module=LOG_MODULE_STR
            )
        return self._max_temperature_spread_warm[h]

    def set_max_temperature_spread_warm(
        self, h: HubId, max_temp_spread_warm: float
    ) -> None:
        """
        Set the maximal allowed temperature spread between the natural aquifer
        temperature and the temperature of fluid in the warm wells. This is a
        mandatory parameter.

        :param h: Hub
        :type h: HubId
        :param max_temp_spread_warm: Maximal temperature spread for warm wells
            [°C]
        :type max_temp_spread_warm: float
        """
        self._max_temperature_spread_warm[h] = max_temp_spread_warm

    # ------------------------------------- #
    # Property: max_temperature_spread_cold #
    # ------------------------------------- #
    def get_max_temperature_spread_cold(self, h: HubId) -> float:
        """
        Get the maximal allowed temperature spread between the natural aquifer
        temperature and the temperature of fluid in the cold wells. This is a
        mandatory parameter.

        :param h: Hub
        :type h: HubId
        :return: Maximal temperature spread for cold wells [°C]
        :rtype: float
        """
        if h not in self._max_temperature_spread_cold:
            raise exceptions.MissingIdException(
                ExceptionKey.MAXTEMPSPREADCOLD_GET.value, h, module=LOG_MODULE_STR
            )
        return self._max_temperature_spread_cold[h]

    def set_max_temperature_spread_cold(
        self, h: HubId, max_temp_spread_cold: float
    ) -> None:
        """
        Set the maximal allowed temperature spread between the natural aquifer
        temperature and the temperature of fluid in the cold wells. This is a
        mandatory parameter.

        :param h: Hub
        :type h: HubId
        :param max_temp_spread_cold: Maximal temperature spread for cold wells
            [°C]
        :type max_temp_spread_cold: float
        """
        self._max_temperature_spread_cold[h] = max_temp_spread_cold

    # ------------------------ #
    # Property: available_area #
    # ------------------------ #
    def get_available_area(self, s: StageId, h: HubId) -> float:
        """
        Get the available area which can be used to install ATES technologies.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :return: Available area for ATES wells [m^2]
        :rtype: float
        """
        available_area = self._available_area.get((s, h), DEF_AVAILABLEAREA)
        return available_area

    def set_available_area(self, s: StageId, h: HubId, available_area: float) -> None:
        """
        Set the available area which can be used to install ATES technologies.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param available_area: Available area for ATES wells [m^2]
        :type available_area: float
        """
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
    ) -> float:
        """
        Get the duration of an ATES schedule's warm-to-cold phase.

        :param h: Hub
        :type h: HubId
        :param i: Schedule
        :type i: AtesScheduleId
        :param times: Times
        :type times: Times
        :return: Duration of warm-to-cold phase [h]
        :rtype: float
        """
        t_start = self.get_phase_w2c_start(h, i)
        t_end = self.get_phase_w2c_end(h, i)
        duration = self._get_phase_duration(t_start, t_end, times)
        return duration

    def get_phase_duration_c2w(
        self, h: HubId, i: AtesScheduleId, times: Times
    ) -> float:
        """
        Get the duration of an ATES schedule's cold-to-warm phase.

        :param h: Hub
        :type h: HubId
        :param i: Schedule
        :type i: AtesScheduleId
        :param times: Times
        :type times: Times
        :return: Duration of cold-to-warm phase [h]
        :rtype: float
        """
        t_start = self.get_phase_c2w_start(h, i)
        t_end = self.get_phase_c2w_end(h, i)
        duration = self._get_phase_duration(t_start, t_end, times)
        return duration

    def _get_phase_duration(
        self, t_start: TimeId, t_end: TimeId, times: Times
    ) -> float:
        # Phase is given by [t_start, t_end] with t_start <= t_end
        if t_start.key_as_int <= t_end.key_as_int:
            duration = float(t_end.key_as_int - t_start.key_as_int + 1)
            return duration
        # Phase is given by [t_first, t_end] + [t_start, t_last]
        t_first = times.first_horizon_id
        t_last = times.last_horizon_id
        duration = float(
            (t_end.key_as_int - t_first.key_as_int + 1)
            + (t_last.key_as_int - t_start.key_as_int + 1)
        )
        return duration

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._groundwater_velocity: Dict[HubId, float] = {}
        self._specific_heat_capacity_aquifer: Dict[HubId, float] = {}
        self._thickness_aquifer: Dict[HubId, float] = {}
        self._hydraulic_conductivity_aquifer: Dict[HubId, float] = {}
        self._storativity_aquifer: Dict[HubId, float] = {}
        self._max_drawdown: Dict[HubId, float] = {}
        self._max_temperature_spread_warm: Dict[HubId, float] = {}
        self._max_temperature_spread_cold: Dict[HubId, float] = {}
        self._available_area: Dict[Tuple[StageId, HubId], float] = {}
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
        self._validate_groundwater_velocity(hubs)
        self._validate_spec_heat_cap_aq(hubs)
        self._validate_thickness_aq(hubs)
        self._validate_hydr_cond_aq(hubs)
        self._validate_storativity_aq(hubs)
        self._validate_max_drawdown(hubs)
        self._validate_max_temp_spread_warm(hubs)
        self._validate_max_temp_spread_cold(hubs)
        self._validate_available_area(stages, hubs)
        self._validate_phase_w2c_start(hubs, times)
        self._validate_phase_w2c_end(hubs, times)
        self._validate_phase_c2w_start(hubs, times)
        self._validate_phase_c2w_end(hubs, times)
        self._validate_phases()

    def _validate_groundwater_velocity(self, hubs: Hubs) -> None:
        exc_key = ExceptionKey.GROUNDWATERVELOCITY_VAL.value
        for h, velo in self._groundwater_velocity.items():
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in groundwater_velocity[{h}]"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)
            if velo < 0:
                msg = f"{velo} = groundwater_velocity[{h}] < 0"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)

    def _validate_spec_heat_cap_aq(self, hubs: Hubs) -> None:
        exc_key = ExceptionKey.SPECIFICHEATCAPAQ_VAL.value
        for h, spec_heat_cap in self._specific_heat_capacity_aquifer.items():
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in specific_heat_capacity_aquifer[{h}]"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)
            if spec_heat_cap <= common.EPS_ZEROCHECK:
                msg = f"{spec_heat_cap} = groundwater_velocity[{h}] <= 0"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)

    def _validate_thickness_aq(self, hubs: Hubs) -> None:
        exc_key = ExceptionKey.THICKNESSAQ_VAL.value
        for h, thickness in self._thickness_aquifer.items():
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in thickness_aquifer[{h}]"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)
            if thickness <= common.EPS_ZEROCHECK:
                msg = f"{thickness} = thickness_aquifer[{h}] <= 0"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)

    def _validate_hydr_cond_aq(self, hubs: Hubs) -> None:
        exc_key = ExceptionKey.HYDRAULICCONDUCTAQ_VAL.value
        for h, hydr_cond_aq in self._hydraulic_conductivity_aquifer.items():
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in hydraulic_conductivity_aquifer[{h}]"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)
            if hydr_cond_aq <= common.EPS_ZEROCHECK:
                msg = f"{hydr_cond_aq} = hydraulic_conductivity_aquifer[{h}] <= 0"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)

    def _validate_storativity_aq(self, hubs: Hubs) -> None:
        exc_key = ExceptionKey.STORATIVITYAQ_VAL.value
        for h, storativity in self._storativity_aquifer.items():
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in storativity_aquifer[{h}]"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)
            if storativity <= common.EPS_ZEROCHECK:
                msg = f"{storativity} = storativity_aquifer[{h}] <= 0"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)

    def _validate_max_drawdown(self, hubs: Hubs) -> None:
        exc_key = ExceptionKey.MAXDRAWDOWN_VAL.value
        for h, max_drawdown in self._max_drawdown.items():
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in max_drawdown[{h}]"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)
            if max_drawdown <= common.EPS_ZEROCHECK:
                msg = f"{max_drawdown} = max_drawdown[{h}] <= 0"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)

    def _validate_max_temp_spread_warm(self, hubs: Hubs) -> None:
        exc_key = ExceptionKey.MAXTEMPSPREADWARM_VAL.value
        for h, max_temp_spread_warm in self._max_temperature_spread_warm.items():
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in max_temperature_spread_warm[{h}]"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)
            if max_temp_spread_warm <= common.EPS_ZEROCHECK:
                msg = f"{max_temp_spread_warm} = max_temperature_spread_warm[{h}] <= 0"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)

    def _validate_max_temp_spread_cold(self, hubs: Hubs) -> None:
        exc_key = ExceptionKey.MAXTEMPSPREADCOLD_VAL.value
        for h, max_temp_spread_cold in self._max_temperature_spread_cold.items():
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in max_temperature_spread_cold[{h}]"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)
            if max_temp_spread_cold <= common.EPS_ZEROCHECK:
                msg = f"{max_temp_spread_cold} = max_temperature_spread_cold[{h}] <= 0"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)

    def _validate_available_area(self, stages: Stages, hubs: Hubs) -> None:
        exc_key = ExceptionKey.AVAILABLEAREA_VAL.value
        for (s, h), available_area in self._available_area.items():
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
            if available_area < 0:
                msg = f"{available_area} = available_area[{s}, {h}] < 0"
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
