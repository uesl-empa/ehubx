"""
EBM (electricity-based mobility) technology data module
"""

from enum import Enum
from typing import Dict, List, Set, Tuple

from ehubx.core import logging
from ehubx.core.common import EPS_ZEROCHECK, TimeSeriesKind
from ehubx.data import exceptions
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.time_data import TimeId, Times
from ehubx.data.time_series import TimeSeries
from ehubx.data.unit import DimlessUnit, TimeUnit, Unit
from ehubx.data.value import Value


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the EBM technology data
    module
    """

    ID_ADD = "adding to 'ids' of EbmTechs"
    ID_REMOVE = "removing from 'ids' of EbmTechs"
    ID_VAL = "validating 'id' of EbmTechs"
    EC_GET = "getting 'ec' from EbmTechs"
    EC_SET = "setting 'ec' of EbmTechs"
    EC_VAL = "validating 'ec' of EbmTechs"
    NUMVEHICLES_GET = "getting 'num_vehicles' from EbmTechs"
    NUMVEHICLES_SET = "setting 'num_vehicles' of EbmTechs"
    NUMVEHICLES_VAL = "validating 'num_vehicles' of EbmTechs"
    INEFF_GET = "getting 'in_eff' from EbmTechs"
    INEFF_SET = "setting 'in_eff' of EbmTechs"
    INEFF_VAL = "validating 'in_eff' of EbmTechs"
    OUTEFF_GET = "getting 'out_eff' from EbmTechs"
    OUTEFF_SET = "setting 'out_eff' of EbmTechs"
    OUTEFF_VAL = "validating 'out_eff' of EbmTechs"
    STANDBYLOSS_GET = "getting 'standby_loss' from EbmTechs"
    STANDBYLOSS_SET = "setting 'standby_loss' of EbmTechs"
    STANDBYLOSS_VAL = "validating 'standby_loss' of EbmTechs"
    STORAGECAP_GET = "getting 'storage_cap' from EbmTechs"
    STORAGECAP_SET = "setting 'storage_cap' of EbmTechs"
    STORAGECAP_VAL = "validating 'storage_cap' of EbmTechs"
    SOCMIN_GET = "getting 'soc_min' from EbmTechs"
    SOCMIN_SET = "setting 'soc_min' of EbmTechs"
    SOCMIN_VAL = "validating 'soc_min' of EbmTechs"
    SOCMAX_GET = "getting 'soc_max' from EbmTechs"
    SOCMAX_SET = "setting 'soc_max' of EbmTechs"
    SOCMAX_VAL = "validating 'soc_max' of EbmTechs"
    SOCMINMAX_VAL = "validating 'soc_min' against 'soc_max' of EbmTechs"
    SOCINIT_GET = "getting 'soc_init' from EbmTechs"
    SOCINIT_SET = "setting 'soc_init' of EbmTechs"
    SOCINIT_VAL = "validating 'soc_init' of EbmTechs"
    SOCINITMINMAX_VAL = (
        "validating 'soc_init' against 'soc_min' and 'soc_max' of EbmTechs"
    )
    CHARGEMAX_GET = "getting 'charge_max' from EbmTechs"
    CHARGEMAX_SET = "setting 'charge_max' of EbmTechs"
    CHARGEMAX_VAL = "validating 'charge_max' of EbmTechs"
    DISCHARGEMAX_GET = "getting 'discharge_max' from EbmTechs"
    DISCHARGEMAX_SET = "setting 'discharge_max' of EbmTechs"
    DISCHARGEMAX_VAL = "validating 'discharge_max' of EbmTechs"
    DISCHARGECONTROL_SET = "setting 'discharge_controllability' of EbmTechs"
    DISCHARGECONTROL_GET = "getting 'discharge_controllability' from EbmTechs"
    DISCHARGECONTROL_VAL = "validating 'discharge_control' of EbmTechs"
    DEMANDMODIFIER_SET = "setting 'demand_modifier' of EbmTechs"
    DEMANDMODIFIER_GET = "getting 'demand_modifier' from EbmTechs"
    DEMANDMODIFIER_VAL = "validating 'demand_modifier' of EbmTechs"
    DEMANDNOMINAL_SET = "setting 'demand_nominal' of EbmTechs"
    DEMANDNOMINAL_DEFSET = "setting default 'demand_nominal' of EbmTechs"
    DEMANDNOMINAL_GET = "getting 'demand_nominal' from EbmTechs"
    DEMANDNOMINAL_VAL = "validating 'demand_nominal' of EbmTechs"
    AVAILABILITY_SET = "setting 'availability' of EbmTechs"
    AVAILABILITY_DEFSET = "setting default value for 'availability' of EbmTechs"
    AVAILABILITY_GET = "getting 'availability' from EbmTechs"
    AVAILABILITY_VAL = "validating 'availability' of EbmTechs"
    CONSUMPTION_GET = "getting 'consumption' from EbmTechs"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/ebm"
"""String identifying the EBM technology data module for logging purposes"""

DEF_INEFF: float = 1
"""Default value for parameter 'in_eff' in the EBM technology data module"""

DEF_OUTEFF: float = 1
"""Default value for parameter 'out_eff' in the EBM technology data module"""

DEF_STANDBYLOSS: float = 0
"""Default value for parameter 'standby_loss' in the EBM technology data
module"""

DEF_SOCMIN: float = 0
"""Default value for parameter 'soc_min' in the EBM technology data module"""

DEF_SOCMAX: float = 1
"""Default value for parameter 'soc_max' in the EBM technology data module"""

DEF_SOCINIT: float = float("inf")
"""Default value for parameter 'soc_init' in the EBM technology data module"""

DEF_CHARGEMAX: float = float("inf")
"""Default value for parameter 'charge_max' in the EBM technology data
module"""

DEF_DISCHARGEMAX: float = float("inf")
"""Default value for parameter 'discharge_max' in the EBM technology data
module"""

DEF_DISCHARGECONTROL: float = 1
"""Default value for parameter 'discharge_control' in the EBM
technology data module"""

DEF_NUMVEHICLES: int = 0
"""Default value for parameter 'num_vehicles' in the EBM technology data
module"""

DEF_DEMANDMODIFIER: float = 1
"""Default value for parameter 'demand_modifier' in the EBM technology data
module"""

DEF_DEMANDNOMINAL: float = 0
"""Default value for parameter 'demand_nominal' in the EBM technology data
module"""

DEF_AVAILABILITY: float = 1
"""Default value for parameter 'availability' in the EBM technology data
module"""


class EbmTechs:
    """
    Class to hold EBM (electricity-based mobility) technology data. Manages EBM
    technology ids, contains getters and setters for EBM technology parameters
    and validation methods to control data integrity
    """

    # --------------- #
    # Property: techs #
    # --------------- #
    @property
    def ids(self) -> Set[TechId]:
        """
        Set of known EBM technology ids
        """
        return self._ids

    @property
    def ids_in_order(self) -> List[TechId]:
        """
        List of EBM tech ids in alphabetical order
        """
        ids = list(self.ids)
        ids.sort(key=lambda x: x.key)
        return ids

    def add_id(self, x: TechId) -> None:
        """
        Add a new EBM technology id

        :param x: Id to be added
        :type x: TechId
        """
        if x in self._ids:
            raise exceptions.DuplicateIdException(
                ExceptionKey.ID_ADD.value, x, module=LOG_MODULE_STR
            )
        self._ids.add(x)

    # ------------ #
    # Property: ec #
    # ------------ #
    def get_ec(self, x: TechId) -> EcId:
        """
        Get the ec that powers and gets stored in the EBM fleet.

        :param x: EBM technology
        :type x: TechId
        :return: EBM ec
        :rtype: EcId
        """
        self._check_id(x, ExceptionKey.EC_GET)
        if x not in self._ec:
            raise exceptions.MissingIdException(
                ExceptionKey.EC_GET.value, x, module=LOG_MODULE_STR
            )
        return self._ec[x]

    def set_ec(self, x: TechId, e: EcId, ec_unit: Unit) -> None:
        """
        Set the ec that powers and gets stored in the EBM fleet.

        :param x: EBM technology
        :type x: TechId
        :param e: EBM ec
        :type e: EcId
        :param ec_unit: Unit of the ec
        :type ec_unit: Unit
        """
        self._check_id(x, ExceptionKey.EC_SET)
        self._ec[x] = e
        self._ec_unit[x] = ec_unit

    # ---------------------- #
    # Property: num_vehicles #
    # ---------------------- #
    def get_num_vehicles(self, s: StageId, h: HubId, x: TechId) -> float:
        """
        Get the parameter 'num_vehicles' which denotes the number of vehicles
        in the EBM fleet. This is a mandatory parameter.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: EBM technology
        :type x: TechId
        :return: Number of vehicles in EBM fleet
        :rtype: float
        """
        self._check_id(x, ExceptionKey.NUMVEHICLES_GET)
        return self._num_vehicles.get((s, h, x), DEF_NUMVEHICLES)

    def set_num_vehicles(
        self, s: StageId, h: HubId, x: TechId, num_vehicles: float
    ) -> None:
        """
        Set the parameter 'num_vehicles' which denotes the number of vehicles
        in the EBM fleet. This is a mandatory parameter.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: EBM technology
        :type x: TechId
        :param num_vehicles: Number of vehicles in EBM fleet [1]
        :type num_vehicles: float
        """
        self._check_id(x, ExceptionKey.NUMVEHICLES_SET)
        self._num_vehicles[s, h, x] = num_vehicles

    # ---------------- #
    # Property: in_eff #
    # ---------------- #
    def get_in_eff(self, s: StageId, x: TechId) -> Value:
        """
        Get the parameter 'in_eff' which denotes the effectiveness of the
        charging process. An in_eff value of e.g.; 0.1 indicates that 90% of
        the input power can be transformed into stored energy. This is an
        optional parameter with a default value of 1.

        :param s: Stage
        :type s: StageId
        :param x: EBM technology
        :type x: TechId
        :return: Input efficiency
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.INEFF_GET)
        return self._in_eff.get((s, x), Value(DEF_INEFF))

    def set_in_eff(self, s: StageId, x: TechId, in_eff: Value) -> None:
        """
        Set the parameter 'in_eff' which denotes the effectiveness of the
        charging process. An in_eff value of e.g.; 0.1 indicates that 90% of
        the input power can be transformed into stored energy. This is an
        optional parameter with a default value of 1

        :param s: Stage
        :type s: StageId
        :param x: EBM technology
        :type x: TechId
        :param in_eff: Input efficiency
        :type in_eff: Value
        """
        self._check_id(x, ExceptionKey.INEFF_SET)
        expected_unit = DimlessUnit()
        if not in_eff.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.INEFF_SET.value,
                [s, x],
                f"Unit of in_eff[{s}, {x}] = {in_eff} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._in_eff[s, x] = in_eff

    # ----------------- #
    # Property: out_eff #
    # ----------------- #
    def get_out_eff(self, s: StageId, x: TechId) -> Value:
        """
        Get the parameter 'out_eff' which denotes the effectiveness of the
        discharging process. An out_eff value of e.g.; 0.1 indicates that 90%
        of the discharged energy can be used. This is an optional parameter
        with a default value of 1.

        :param s: Stage
        :type s: StageId
        :param x: EBM technology
        :type x: TechId
        :return: Output efficiency
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.OUTEFF_GET)
        return self._out_eff.get((s, x), Value(DEF_OUTEFF))

    def set_out_eff(self, s: StageId, x: TechId, out_eff: Value) -> None:
        """
        Set the parameter 'out_eff' which denotes the effectiveness of the
        discharging process. An out_eff value of e.g.; 0.1 indicates that 90%
        of the discharged energy can be used. This is an optional parameter
        with a default value of 1.

        :param s: Stage
        :type s: StageId
        :param x: EBM technology
        :type x: TechId
        :param out_eff: Output efficiency
        :type out_eff: Value
        """
        self._check_id(x, ExceptionKey.OUTEFF_SET)
        expected_unit = DimlessUnit()
        if not out_eff.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.OUTEFF_SET.value,
                [s, x],
                f"Unit of out_eff[{s}, {x}] = {out_eff} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._out_eff[s, x] = out_eff

    # ---------------------- #
    # Property: standby_loss #
    # ---------------------- #
    def get_standby_loss(self, s: StageId, x: TechId) -> Value:
        """
        Get the parameter 'standby_loss' which denotes the
        relative loss rate of stored energy per time step. This is an optional
        parameter with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param x: EBM technology
        :type x: TechId
        :return: Standby loss
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.STANDBYLOSS_GET)
        return self._standby_loss.get(
            (s, x), Value(DEF_STANDBYLOSS, DimlessUnit() / TimeUnit.H)
        )

    def set_standby_loss(self, s: StageId, x: TechId, standby_loss: Value) -> None:
        """
        Set the parameter 'standby_loss' which denotes the
        relative loss rate of stored energy per time step. This is an optional
        parameter with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param x: EBM technology
        :type x: TechId
        :param standby_loss: Standby loss
        :type standby_loss: Value
        """
        self._check_id(x, ExceptionKey.STANDBYLOSS_SET)
        expected_unit = DimlessUnit() / TimeUnit.H
        if not standby_loss.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.STANDBYLOSS_SET.value,
                [s, x],
                f"Unit of standby_loss[{s}, {x}] = {standby_loss} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._standby_loss[s, x] = standby_loss

    # --------------------- #
    # Property: storage_cap #
    # --------------------- #
    def get_storage_cap(self, s: StageId, x: TechId) -> Value:
        """
        Get the parameter 'storage_cap' which denotes the amount of energy
        that can be stored in a single EBM vehicle. This is mandatory
        parameter.

        :param s: Stage
        :type s: StageId
        :param x: EBM technology
        :type x: TechId
        :return: Storage capacity of a single EBM vehicle
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.STORAGECAP_GET)
        if (s, x) not in self._storage_cap:
            raise exceptions.MissingIdException(
                ExceptionKey.STORAGECAP_GET.value, x, module=LOG_MODULE_STR
            )
        return self._storage_cap[s, x]

    def set_storage_cap(self, s: StageId, x: TechId, storage_cap: Value) -> None:
        """
        Set the parameter 'storage_cap' which denotes the amount of energy
        that can be stored in a single EBM vehicle. This is mandatory
        parameter.

        :param s: Stage
        :type s: StageId
        :param x: EBM technology
        :type x: TechId
        :param storage_cap: Storage capacity of a single EBM vehicle [kWh]
        :type storage_cap: Value
        """
        self._check_id(x, ExceptionKey.STORAGECAP_SET)
        expected_unit = self._ec_unit[x]
        if not storage_cap.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.STORAGECAP_SET.value,
                [s, x],
                f"Unit of storage_cap[{s}, {x}] = {storage_cap} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._storage_cap[s, x] = storage_cap

    # ----------------- #
    # Property: soc_min #
    # ----------------- #
    def get_soc_min(self, s: StageId, x: TechId) -> Value:
        """
        Get the parameter 'soc_min' which denotes the minimal state of charge
        that is allowed for an EBM technology. An soc_min value of e.g.;
        0.1 indicates that at least 10% of the technology's storage capacity
        must be filled at all times. This is an optional parameter with a
        default value of 0.

        :param s: Stage
        :type s: StageId
        :param x: EBM technology
        :type x: TechId
        :return: Minimal state of charge
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.SOCMIN_GET)
        return self._soc_min.get((s, x), Value(DEF_SOCMIN))

    def set_soc_min(self, s: StageId, x: TechId, soc_min: Value) -> None:
        """
        Set the parameter 'soc_min' which denotes the minimal state of charge
        that is allowed for an EBM technology. An soc_min value of e.g.;
        0.1 indicates that at least 10% of the technology's storage capacity
        must be filled at all times. This is an optional parameter with a
        default value of 0.

        :param s: Stage
        :type s: StageId
        :param x: EBM technology
        :type x: TechId
        :param soc_min: Minimal state of charge
        :type soc_min: Value
        """
        self._check_id(x, ExceptionKey.SOCMIN_SET)
        expected_unit = DimlessUnit()
        if not soc_min.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.SOCMIN_SET.value,
                [s, x],
                f"Unit of soc_min[{s}, {x}] = {soc_min} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._soc_min[s, x] = soc_min

    # ----------------- #
    # Property: soc_max #
    # ----------------- #
    def get_soc_max(self, s: StageId, x: TechId) -> Value:
        """
        Get the parameter 'soc_max' which denotes the maximal state of charge
        that is allowed for an EBM technology. An soc_max value of e.g.;
        0.8 indicates that at most 80% of the technology's storage capacity
        may be filled at all times. This is an optional parameter with a
        default value of 1.

        :param s: Stage
        :type s: StageId
        :param x: EBM technology
        :type x: TechId
        :return: Maximal state of charge
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.SOCMAX_GET)
        return self._soc_max.get((s, x), Value(DEF_SOCMAX))

    def set_soc_max(self, s: StageId, x: TechId, soc_max: Value) -> None:
        """
        Set the parameter 'soc_max' which denotes the maximal state of charge
        that is allowed for an EBM technology. An soc_max value of e.g.;
        0.8 indicates that at most 80% of the technology's storage capacity
        may be filled at all times. This is an optional parameter with a
        default value of 1.

        :param s: Stage
        :type s: StageId
        :param x: EBM technology
        :type x: TechId
        :param soc_max: Maximal state of charge
        :type soc_max: Value
        """
        self._check_id(x, ExceptionKey.SOCMAX_SET)
        excepted_unit = DimlessUnit()
        if not soc_max.unit.same_type_as(excepted_unit):
            raise exceptions.DataException(
                ExceptionKey.SOCMAX_SET.value,
                [s, x],
                f"Unit of soc_max[{s}, {x}] = {soc_max} "
                f"does not match expected unit {excepted_unit}",
                module=LOG_MODULE_STR,
            )
        self._soc_max[s, x] = soc_max

    # ------------------ #
    # Property: soc_init #
    # ------------------ #
    def get_soc_init(self, h: HubId, x: TechId) -> Value:
        """
        Get the parameter 'soc_init' which denotes an EBM technology's
        initial state of charge (i.e.; at the first time step in every stage)
        in each hub. An initial state of charge of 0.4 indicates that, at the
        beginning of the time horizon, the fleet's collective energy storage
        level is at 40% of its total storage capacity. An soc_init value of
        infinity indicates that the initial state of charge level is not set
        but can be chosen by the optimizer. This is an optional parameter with
        a default value of infinity.

        :param h: Hub
        :type h: HubId
        :param x: EBM technology
        :type x: TechId
        :return: Initial state of charge
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.SOCINIT_GET)
        return self._soc_init.get((h, x), Value(DEF_SOCINIT))

    def set_soc_init(self, h: HubId, x: TechId, soc_init: Value) -> None:
        """
        Set the parameter 'soc_init' which denotes an EBM technology's
        initial state of charge (i.e.; at the first time step in every stage)
        in each hub. An initial state of charge of 0.4 indicates that, at the
        beginning of the time horizon, the fleet's collective energy storage
        level is at 40% of its total storage capacity. An soc_init value of
        infinity indicates that the initial state of charge level is not set
        but can be chosen by the optimizer. This is an optional parameter with
        a default value of infinity.

        :param h: Hub
        :type h: HubId
        :param x: EBM technology
        :type x: TechId
        :param soc_init: Initial state of charge
        :type soc_init: Value
        """
        self._check_id(x, ExceptionKey.SOCINIT_SET)
        expected_unit = DimlessUnit()
        if not soc_init.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.SOCINIT_SET.value,
                [h, x],
                f"Unit of soc_init[{h}, {x}] = {soc_init} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._soc_init[h, x] = soc_init

    # -------------------- #
    # Property: charge_max #
    # -------------------- #
    def get_charge_max(self, s: StageId, x: TechId) -> Value:
        """
        Get the parameter 'charge_max' which denotes the maximal charging rate
        of a single EBM vehicle. This is an optional parameter with a default
        value of infinity.

        :param s: Stage
        :type s: StageId
        :param x: EBM technology
        :type x: TechId
        :return: Maximal charging speed of a single EBM vehicle
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.CHARGEMAX_GET)
        unit = self._ec_unit[x] / TimeUnit.H
        return self._charge_max.get((s, x), Value(DEF_CHARGEMAX, unit))

    def set_charge_max(self, s: StageId, x: TechId, charge_max: Value) -> None:
        """
        Set the parameter 'charge_max' which denotes the maximal charging rate
        of a single EBM vehicle. This is an optional parameter with a default
        value of infinity.

        :param s: Stage
        :type s: StageId
        :param x: EBM technology
        :type x: TechId
        :param charge_max: Maximal charging speed of a single EBM vehicle
        :type charge_max: Value
        """
        self._check_id(x, ExceptionKey.CHARGEMAX_SET)
        expected_unit = self._ec_unit[x] / TimeUnit.H
        if not charge_max.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.CHARGEMAX_SET.value,
                [s, x],
                f"Unit of charge_max[{s}, {x}] = {charge_max} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._charge_max[s, x] = charge_max

    # ----------------------- #
    # Property: discharge_max #
    # ----------------------- #
    def get_discharge_max(self, s: StageId, x: TechId) -> Value:
        """
        Get the parameter 'discharge_max' which denotes the maximal discharging
        rate of a single EBM vehicle. This is an optional parameter with a
        default value of infinity.

        :param s: Stage
        :type s: StageId
        :param x: EBM technology
        :type x: TechId
        :return: Maximal discharging speed of a single EBM vehicle
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.DISCHARGEMAX_GET)
        unit = self._ec_unit[x] / TimeUnit.H
        return self._discharge_max.get((s, x), Value(DEF_DISCHARGEMAX, unit))

    def set_discharge_max(self, s: StageId, x: TechId, discharge_max: Value) -> None:
        """
        Set the parameter 'discharge_max' which denotes the maximal discharging
        rate of a single EBM vehicle. This is an optional parameter with a
        default value of infinity.

        :param s: Stage
        :type s: StageId
        :param x: EBM technology
        :type x: TechId
        :param discharge_max: Maximal discharging speed of a single EBM vehicle
        :type discharge_max: Value
        """
        self._check_id(x, ExceptionKey.DISCHARGEMAX_SET)
        expected_unit = self._ec_unit[x] / TimeUnit.H
        if not discharge_max.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.DISCHARGEMAX_SET.value,
                [s, x],
                f"Unit of discharge_max[{s}, {x}] = {discharge_max} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._discharge_max[s, x] = discharge_max

    # --------------------------- #
    # Property: discharge_control #
    # --------------------------- #
    def get_discharge_control(self, s: StageId, x: TechId) -> Value:
        """
        Get the parameter 'discharge_control' which is a heuristic factor that
        dampens the maximal discharge speed of the EBM fleet. A discharge
        control of 0.4 means that the available portion of the fleet can be
        discharged at 40% of its maximal discharging power. A discharge control
        of 0 means that discharging is impossible. This is an optional
        parameter with a default value of 1.

        :param s: Stage
        :type s: StageId
        :param x: EBM technology
        :type x: TechId
        :return: Discharge control
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.DISCHARGECONTROL_GET)
        return self._discharge_control.get((s, x), Value(DEF_DISCHARGECONTROL))

    def set_discharge_control(
        self, s: StageId, x: TechId, discharge_control: Value
    ) -> None:
        """
        Set the parameter 'discharge_control' which is a heuristic factor that
        dampens the maximal discharge speed of the EBM fleet. A discharge
        control of 0.4 means that the available portion of the fleet can be
        discharged at 40% of its maximal discharging power. A discharge control
        of 0 means that discharging is impossible. This is an optional
        parameter with a default value of 1.

        :param s: Stage
        :type s: StageId
        :param x: EBM technology
        :type x: TechId
        :param discharge_control: Discharge control
        :type discharge_control: Value
        """
        self._check_id(x, ExceptionKey.DISCHARGECONTROL_SET)
        expected_unit = DimlessUnit()
        if not discharge_control.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.DISCHARGECONTROL_SET.value,
                [s, x],
                f"Unit of discharge_control[{s}, {x}] = {discharge_control} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._discharge_control[s, x] = discharge_control

    # ------------------------- #
    # Property: demand_modifier #
    # ------------------------- #
    def get_demand_modifier(self, s: StageId, h: HubId, x: TechId) -> Value:
        """
        Get the parameter 'demand_modifier' which is multiplied with the
        value(s) of the parameter 'demand_nominal' to obtain the total
        consumption of an average EBM vehicle. This is an optional parameter
        with a default value of 1.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: EBM technology
        :type x: TechId
        :return: Demand modifier
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.DEMANDMODIFIER_GET)
        return self._demand_modifier.get((s, h, x), Value(DEF_DEMANDMODIFIER))

    def set_demand_modifier(
        self, s: StageId, h: HubId, x: TechId, demand_modifier: Value
    ) -> None:
        """
        Set the parameter 'demand_modifier' which is multiplied with the
        value(s) of the parameter 'demand_nominal' to obtain the total
        consumption of an average EBM vehicle. This is an optional parameter
        with a default value of 1.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: EBM technology
        :type x: TechId
        :param demand_modifier: Demand modifier
        :type demand_modifier: Value
        """
        self._check_id(x, ExceptionKey.DEMANDMODIFIER_SET)
        expected_unit = DimlessUnit()
        if not demand_modifier.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.DEMANDMODIFIER_SET.value,
                [s, h, x],
                f"Unit of demand_modifier[{s}, {h}, {x}] = {demand_modifier} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._demand_modifier[s, h, x] = demand_modifier

    # ------------------------ #
    # Property: demand_nominal #
    # ------------------------ #
    def get_demand_nominal(self, s: StageId, h: HubId, x: TechId) -> TimeSeries:
        """
        Get the parameter 'demand_nominal' which is multiplied with the
        parameter 'demand_modifier' to obtain the total consumption of an
        average EBM vehicle. This is an optional parameter with a default value
        of 0.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: EBM technology
        :type x: TechId
        :return: Nominal demands of a single EBM vehicle
        :rtype: TimeSeries
        """
        self._check_id(x, ExceptionKey.DEMANDNOMINAL_GET)
        if (s, h, x) not in self._demand_nominal:
            unit = self._ec_unit[x] / TimeUnit.H
            demand_nominal = TimeSeries()
            demand_nominal.def_value = Value(DEF_DEMANDNOMINAL, unit)
            return demand_nominal
        return self._demand_nominal[s, h, x]

    def set_demand_nominal(
        self, s: StageId, h: HubId, x: TechId, t: TimeId, demand_nominal: Value
    ) -> None:
        """
        At a specific time, set the parameter 'demand_nominal' which is
        multiplied with the parameter 'demand_modifier' to obtain the total
        consumption of an average EBM vehicle. This is an optional parameter
        with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: EBM technology
        :type x: TechId
        :param t: Time
        :type t: TimeId
        :param demand_nominal: Nominal demand of a single EBM vehicle
        :type demand_nominal: Value
        """
        self._check_id(x, ExceptionKey.DEMANDNOMINAL_SET)
        expected_unit = self._ec_unit[x] / TimeUnit.H
        if (s, h, x) not in self._demand_nominal:
            self._demand_nominal[s, h, x] = TimeSeries()
            self._demand_nominal[s, h, x].def_value = Value(
                DEF_DEMANDNOMINAL, expected_unit
            )
        self._demand_nominal[s, h, x].set_value(t, demand_nominal)

    def set_demand_nominal_def(
        self, s: StageId, h: HubId, x: TechId, demand_nominal_def: Value
    ) -> None:
        """
        Set the default (with respect to time) value for the parameter
        'demand_nominal' which is multiplied with the parameter
        'demand_modifier' to obtain the total consumption of an average EBM
        vehicle. This is an optional parameter with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: EBM technology
        :type x: TechId
        :param demand_nominal_def: Default nominal demand of a single EBM vehicle
        :type demand_nominal_def: Value
        """
        self._check_id(x, ExceptionKey.DEMANDNOMINAL_DEFSET)
        expected_unit = self._ec_unit[x] / TimeUnit.H
        if (s, h, x) not in self._demand_nominal:
            self._demand_nominal[s, h, x] = TimeSeries()
        if not demand_nominal_def.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.DEMANDNOMINAL_DEFSET.value,
                [s, h, x],
                f"Unit of default value for demand_nominal[{s}, {h}, {x}] = "
                f"{demand_nominal_def} does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._demand_nominal[s, h, x].def_value = demand_nominal_def

    # ---------------------- #
    # Property: availability #
    # ---------------------- #
    def get_availability(self, s: StageId, h: HubId, x: TechId) -> TimeSeries:
        """
        Get the parameter 'availability' which is a multiplier for the
        technology’s ability to charge and discharge. An availability of 0.3
        means that 30% of the fleet is available for charging and discharging.
        This is an optional parameter with a default value of 1.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: EBM technology
        :type x: TechId
        :return: Availability multipliers for charging and discharging
        :rtype: TimeSeries
        """
        self._check_id(x, ExceptionKey.AVAILABILITY_GET)
        if (s, h, x) not in self._availability:
            availability = TimeSeries()
            availability.def_value = Value(DEF_AVAILABILITY)
            return availability
        return self._availability[s, h, x]

    def set_availability(
        self, s: StageId, h: HubId, x: TechId, t: TimeId, availability: Value
    ) -> None:
        """
        At a specific time, set the parameter 'availability' which is a
        multiplier for the technology’s ability to charge and discharge. An
        availability of 0.3 means that 30% of the fleet is available for
        charging and discharging. This is an optional parameter with a default
        value of 1.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: EBM technology
        :type x: TechId
        :param t: Time
        :type t: TimeId
        :param availability: Availability multiplier for charging and discharging
        :type availability: Value
        """
        self._check_id(x, ExceptionKey.AVAILABILITY_SET)
        expected_unit = DimlessUnit()
        if not availability.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.AVAILABILITY_SET.value,
                [s, h, x],
                f"Unit of availability[{s}, {h}, {x}] = {availability} does not "
                f"match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        if (s, h, x) not in self._availability:
            self._availability[s, h, x] = TimeSeries()
            self._availability[s, h, x].def_value = Value(DEF_AVAILABILITY)
        self._availability[s, h, x].set_value(t, availability)

    def set_availability_def(
        self, s: StageId, h: HubId, x: TechId, availability_def: Value
    ) -> None:
        """
        Set the default (with respect to time) value for the parameter
        'availability' which is a multiplier for the technology’s ability to
        charge and discharge. An availability of 0.3 means that 30% of the
        fleet is available for charging and discharging. This is an optional
        parameter with a default value of 1.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: EBM technology
        :type x: TechId
        :param availability_def: Default availability multiplier for charging
            and discharging
        :type availability_def: Value
        """
        self._check_id(x, ExceptionKey.AVAILABILITY_DEFSET)
        if (s, h, x) not in self._availability:
            self._availability[s, h, x] = TimeSeries()
        expected_unit = DimlessUnit()
        if not availability_def.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.AVAILABILITY_DEFSET.value,
                [s, h, x],
                f"Unit of availability[{s}, {h}, {x}] = "
                f"{availability_def} does not match expected unit "
                f"{expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._availability[s, h, x].def_value = availability_def

    # --------------------- #
    # Property: Consumption #
    # --------------------- #
    def get_consumption(
        self, s: StageId, h: HubId, x: TechId, times: Times
    ) -> TimeSeries:
        """
        Get the consumption of the EBM fleet which is obtained by multiplying
        the parameters 'num_vehicles' (size of fleet), 'demand_nominal' and
        'demand_multiplier'.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: EBM technology
        :type x: TechId
        :param times: Time
        :type times: Times
        :return: Consumption values of the entire EBM fleet
        :rtype: TimeSeries
        """
        self._check_id(x, ExceptionKey.CONSUMPTION_GET)
        demand_modifier = self.get_demand_modifier(s, h, x)
        demand_nominal = self.get_demand_nominal(s, h, x)
        demand_nominal_def = demand_nominal.def_value
        assert demand_nominal_def is not None
        num_vehicles = self.get_num_vehicles(s, h, x)
        consumption = TimeSeries()
        consumption.def_value = num_vehicles * demand_modifier * demand_nominal_def
        if demand_nominal.has_values:
            for t in times.ids:
                cons = num_vehicles * demand_modifier * demand_nominal.get_value(t)
                consumption.set_value(t, cons)
        return consumption

    # ------------------------------- #
    # Secondary property: time_series #
    # ------------------------------- #
    @property
    def time_series(
        self,
    ) -> List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...], TimeSeries]]:
        """
        Time series profiles in the EBM technology module. This is a
        list of tuples. Each list element has the following list entries: 1)
        ProfileKind of the profile. 2) Stage. 3) Tuple of string identifiers
        specific to the ProfileKind. 4) The TimeSeries itself

        :return: All time series of the EBM technology module
        :rtype: List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...],
            TimeSeries]]
        """
        all_series: List[
            Tuple[TimeSeriesKind, StageId, Tuple[str, ...], TimeSeries]
        ] = []
        # Nominal demand
        for (s, h, x), series in self._demand_nominal.items():
            if series.has_values:
                all_series.append(
                    (TimeSeriesKind.EBMTECHDEMANDNOM, s, (h.key, x.key), series)
                )
        # Availability
        for (s, h, x), series in self._availability.items():
            if series.has_values:
                all_series.append(
                    (TimeSeriesKind.EBMTECHAVAIL, s, (h.key, x.key), series)
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
        Set the value for a time series in the EB; technology data
        class. The time series should be uniquely identified by the time series
        kind, the stage id and the remaining tuples.

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
        unit: Unit
        if kind == TimeSeriesKind.EBMTECHAVAIL:
            h = HubId(ids[0])
            x = TechId(ids[1])
            unit = DimlessUnit()
            self.set_availability(s, h, x, t, Value(value, unit=unit))
        if kind == TimeSeriesKind.EBMTECHDEMANDNOM:
            h = HubId(ids[0])
            x = TechId(ids[1])
            unit = Unit.get_def_unit(self._ec_unit[x] / TimeUnit.H)
            self.set_demand_nominal(s, h, x, t, Value(value, unit=unit))

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._ids: Set[TechId] = set()
        self._ec: Dict[TechId, EcId] = {}
        self._ec_unit: Dict[TechId, Unit] = {}
        self._in_eff: Dict[Tuple[StageId, TechId], Value] = {}
        self._out_eff: Dict[Tuple[StageId, TechId], Value] = {}
        self._standby_loss: Dict[Tuple[StageId, TechId], Value] = {}
        self._soc_min: Dict[Tuple[StageId, TechId], Value] = {}
        self._soc_max: Dict[Tuple[StageId, TechId], Value] = {}
        self._soc_init: Dict[Tuple[HubId, TechId], Value] = {}
        self._num_vehicles: Dict[Tuple[StageId, HubId, TechId], float] = {}
        self._storage_cap: Dict[Tuple[StageId, TechId], Value] = {}
        self._charge_max: Dict[Tuple[StageId, TechId], Value] = {}
        self._discharge_max: Dict[Tuple[StageId, TechId], Value] = {}
        self._discharge_control: Dict[Tuple[StageId, TechId], Value] = {}
        self._demand_modifier: Dict[Tuple[StageId, HubId, TechId], Value] = {}
        self._demand_nominal: Dict[Tuple[StageId, HubId, TechId], TimeSeries] = {}
        self._availability: Dict[Tuple[StageId, HubId, TechId], TimeSeries] = {}

    # ---------- #
    # Validation #
    # ---------- #
    def validate(
        self, stages: Stages, hubs: Hubs, techs: Techs, ecs: Ecs, times: Times
    ) -> None:
        """
        Validate all EBM technology data in this object. Apart from
        sense-checking parameter in terms of quantity, this includes checking
        whether the ids from other data classes used here are known there as
        well.

        :param stages: Stages data class
        :type stages: Stages
        :param hubs: Hubs data class
        :type hubs: Hubs
        :param techs: Techs data class
        :type techs: Techs
        :param ecs: ecs data class
        :type ecs: Ecs
        :param times: Times data class
        :type times: Times
        """
        self._validate_ids(techs)
        self._validate_ec(ecs)
        self._validate_in_eff(stages)
        self._validate_out_eff(stages)
        self._validate_charge_max(stages)
        self._validate_discharge_max(stages)
        self._validate_standby_loss(stages)
        self._validate_soc_min(stages)
        self._validate_soc_max(stages)
        self._validate_soc_minmax()
        self._validate_soc_init(hubs)
        self._validate_soc_initminmax()
        self._validate_num_vehicles()
        self._validate_storage_cap()
        self._validate_discharge_control()
        self._validate_demand_modifier()
        self._validate_demand_nominal(times)
        self._validate_availability(times)

    def _validate_ids(self, techs: Techs) -> None:
        exc_key = ExceptionKey.ID_VAL.value
        for x in self._ids:
            # stor_tech not in techs
            if x not in techs.ids:
                msg = f"stor_tech {x} not part of techs"
                raise exceptions.DataException(exc_key, [x], msg, module=LOG_MODULE_STR)

    def _validate_ec(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.EC_VAL.value
        for x, e in self._ec.items():
            # Unknown ec
            if e not in ecs.ids:
                msg = f"Unknown ec in ec[{x}] = {e}"
                raise exceptions.DataException(
                    exc_key, [x, e], msg, module=LOG_MODULE_STR
                )

    def _validate_in_eff(self, stages: Stages) -> None:
        exc_key = ExceptionKey.INEFF_VAL.value
        for (s, x), in_eff in self._in_eff.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in in_eff[{s}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # in_eff must be nonnegative
            if in_eff.is_negative:
                msg = f"{in_eff} = in_eff[{s}, {x}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # in_eff usually not zero
            if in_eff < Value(EPS_ZEROCHECK):
                msg = f"{in_eff} = in_eff[{s}, {x}] ~ 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)
            # in_eff usually not larger than one
            if in_eff > Value(1):
                msg = f"{in_eff} = in_eff[{s}, {x}] > 1"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_out_eff(self, stages: Stages) -> None:
        exc_key = ExceptionKey.OUTEFF_VAL.value
        for (s, x), out_eff in self._out_eff.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in out_eff[{s}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # out_eff must be nonnegative
            if out_eff.is_negative:
                msg = f"{out_eff} = out_eff[{s}, {x}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # out_eff usually not zero
            if out_eff < Value(EPS_ZEROCHECK):
                msg = f"{out_eff} = out_eff[{s}, {x}] ~ 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)
            # out_eff usually not larger than one
            if out_eff > Value(1):
                msg = f"{out_eff} = out_eff[{s}, {x}] > 1"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_charge_max(self, stages: Stages) -> None:
        exc_key = ExceptionKey.CHARGEMAX_VAL.value
        for (s, x), charge_max in self._charge_max.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in charge_max[{s}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # charge_max must be nonnegative
            if charge_max.is_negative:
                msg = f"{charge_max} = charge_max[{s}, {x}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )

    def _validate_discharge_max(self, stages: Stages) -> None:
        exc_key = ExceptionKey.DISCHARGEMAX_VAL.value
        for (s, x), discharge_max in self._discharge_max.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in discharge_max[{s}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # discharge_max must be nonnegative
            if discharge_max.is_negative:
                msg = f"{discharge_max} = discharge_max[{s}, {x}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )

    def _validate_standby_loss(self, stages: Stages) -> None:
        exc_key = ExceptionKey.STANDBYLOSS_VAL.value
        for (s, x), standby_loss in self._standby_loss.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in standby_loss[{s}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # standby_loss must be nonnegative
            if standby_loss.is_negative:
                msg = f"{standby_loss} = standby_loss[{s}, {x}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )

    def _validate_soc_min(self, stages: Stages) -> None:
        exc_key = ExceptionKey.SOCMIN_VAL.value
        for (s, x), soc_min in self._soc_min.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in soc_min[{s}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # soc_min usually nonnegative
            if soc_min.is_negative:
                msg = f"{soc_min} = soc_min[{s}, {x}] < 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)
            # soc_min must not be larger than one
            if soc_min > Value(1):
                msg = f"{soc_min} = soc_min[{s}, {x}] > 1"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )

    def _validate_soc_max(self, stages: Stages) -> None:
        exc_key = ExceptionKey.SOCMAX_VAL.value
        for (s, x), soc_max in self._soc_max.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in soc_max[{s}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # soc_max must be nonnegative
            if soc_max.is_negative:
                msg = f"{soc_max} = soc_max[{s}, {x}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # soc_max usually larger than one
            if soc_max > Value(1):
                msg = f"{soc_max} = soc_max[{s}, {x}] > 1"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_soc_minmax(self) -> None:
        exc_key = ExceptionKey.SOCMINMAX_VAL.value
        keys = set(self._soc_min.keys()).union(set(self._soc_max.keys()))
        for s, x in keys:
            soc_min = self.get_soc_min(s, x)
            soc_max = self.get_soc_max(s, x)
            # soc_min must not be larger than soc_max
            if soc_min > soc_max:
                msg = f"{soc_min} = soc_min[{s}, {x}] > soc_max[{s}, {x}] = {soc_max}"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )

    def _validate_soc_init(self, hubs: Hubs) -> None:
        exc_key = ExceptionKey.SOCINIT_VAL.value
        for (h, x), soc_init in self._soc_init.items():
            # Unknown hub
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in soc_init[{h}, {x}]"
                raise exceptions.DataException(
                    exc_key, [h, x], msg, module=LOG_MODULE_STR
                )
            # soc_init must be nonnegative
            if soc_init.is_negative:
                msg = f"{soc_init} = soc_init[{h}, {x}] < 0"
                raise exceptions.DataException(
                    exc_key, [h, x], msg, module=LOG_MODULE_STR
                )
            # soc_init must not be larger than one
            if soc_init > Value(1):
                msg = f"{soc_init} = soc_init[{h}, {x}] > 1"
                raise exceptions.DataException(
                    exc_key, [h, x], msg, module=LOG_MODULE_STR
                )

    def _validate_soc_initminmax(self) -> None:
        exc_key = ExceptionKey.SOCINITMINMAX_VAL.value
        tuples_minmax = set(self._soc_min.keys()).union(set(self._soc_max.keys()))
        for (h, x), soc_init in self._soc_init.items():
            for s, x2 in tuples_minmax:
                if x2 != x:
                    continue
                soc_min = self.get_soc_min(s, x)
                soc_max = self.get_soc_max(s, x)
                # soc_init must not be smaller than soc_min
                if soc_init < soc_min:
                    msg = (
                        f"{soc_init} = soc_init[{h}, {x}] < "
                        f"soc_min[{s}, {x}] = {soc_min}"
                    )
                    raise exceptions.DataException(
                        exc_key, [s, h, x], msg, module=LOG_MODULE_STR
                    )
                # soc_init must not be larger than soc_max
                if soc_init > soc_max:
                    msg = (
                        f"{soc_init} = soc_init[{h}, {x}] > "
                        f"soc_max[{s}, {x}] = {soc_max}"
                    )
                    raise exceptions.DataException(
                        exc_key, [s, h, x], msg, module=LOG_MODULE_STR
                    )

    def _validate_num_vehicles(self) -> None:
        exc_key = ExceptionKey.NUMVEHICLES_VAL.value
        for (s, h, x), num_vehicles in self._num_vehicles.items():
            # num_vehicles must be nonnegative
            if num_vehicles < 0:
                msg = f"{num_vehicles} = num_vehicles[{s}, {h}, {x}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, h, x], msg, module=LOG_MODULE_STR
                )
            # num_vehicles usually positive
            if num_vehicles < EPS_ZEROCHECK:
                msg = f"{num_vehicles} = num_vehicles[{s}, {h}, {x}] ~ 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_storage_cap(self) -> None:
        exc_key = ExceptionKey.STORAGECAP_VAL.value
        for (s, x), storage_cap in self._storage_cap.items():
            # storage_cap must be nonnegative
            if storage_cap.is_negative:
                msg = f"{storage_cap} = storage_cap[{s}, {x}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )

    def _validate_discharge_control(self) -> None:
        exc_key = ExceptionKey.DISCHARGECONTROL_VAL.value
        for (s, x), discharge_control in self._discharge_control.items():
            # discharge_control must be nonnegative
            if discharge_control.is_negative:
                msg = f"{discharge_control} = discharge_control[{s}, {x}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # storage_cap usually positive
            if discharge_control < Value(EPS_ZEROCHECK):
                msg = f"{discharge_control} = discharge_control[{s}, {x}] ~ 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_demand_modifier(self) -> None:
        exc_key = ExceptionKey.DEMANDMODIFIER_VAL.value
        for (s, h, x), demand_modifier in self._demand_modifier.items():
            # demand_modifier must be nonnegative
            if demand_modifier.is_negative:
                msg = f"{demand_modifier} = demand_modifier[{s}, {h}, {x}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, h, x], msg, module=LOG_MODULE_STR
                )

    def _validate_demand_nominal(self, times: Times) -> None:
        exc_key = ExceptionKey.DEMANDNOMINAL_VAL.value
        for (s, h, x), demand_nominal in self._demand_nominal.items():
            # Unknown time ids
            demand_nominal.validate(times, exc_key, module=LOG_MODULE_STR)
            # demand_nominal must be nonnegative (time values)
            if demand_nominal.has_values:
                for t in times.ids:
                    if demand_nominal.get_value(t).is_negative:
                        msg = (
                            f"{demand_nominal.get_value(t)} = "
                            f"demand_nominal[{s}, {h}, {x}][{t}] < 0"
                        )
                        raise exceptions.DataException(
                            exc_key, [s, h, x, t], msg, module=LOG_MODULE_STR
                        )
            # demand_nominal must be nonnegative (default values)
            if not demand_nominal.has_values:
                demand_nominal_def = demand_nominal.def_value
                assert demand_nominal_def is not None
                if demand_nominal_def.is_negative:
                    msg = f"{demand_nominal_def} = demand_nominal[{s}, {h}, {x}] < 0"
                    raise exceptions.DataException(
                        exc_key, [s, h, x], msg, module=LOG_MODULE_STR
                    )

    def _validate_availability(self, times: Times) -> None:
        exc_key = ExceptionKey.AVAILABILITY_VAL.value
        for (s, h, x), availability in self._availability.items():
            # Unknown time ids
            availability.validate(times, exc_key, module=LOG_MODULE_STR)
            # availability must be nonnegative (time values)
            if availability.has_values:
                for t in times.ids:
                    if availability.get_value(t).is_negative:
                        msg = (
                            f"{availability.get_value(t)} = availability"
                            f"[{s}, {h}, {x}][{t}] < 0"
                        )
                        raise exceptions.DataException(
                            exc_key, [s, h, x, t], msg, module=LOG_MODULE_STR
                        )
            # availability must be nonnegative (default values)
            if not availability.has_values:
                availability_def = availability.def_value
                assert availability_def is not None
                if availability_def.is_negative:
                    msg = f"{availability_def} = availability[{s}, {h}, {x}] < 0"
                    raise exceptions.DataException(
                        exc_key, [s, h, x], msg, module=LOG_MODULE_STR
                    )

    # ----------- #
    # Id checkers #
    # ----------- #
    def _check_id(self, x: TechId, key: ExceptionKey) -> None:
        if x not in self._ids:
            raise exceptions.UnknownIdException(key.value, x, module=LOG_MODULE_STR)

    def _check_ec(self, x: TechId, e: EcId, key: ExceptionKey) -> None:
        if x not in self._ec or self._ec[x] != e:
            raise exceptions.DataException(
                key.value,
                [x, e],
                f"Encountered ec {e} which is not assigned to EBM tech {x} "
                f"while {key.value}",
                module=LOG_MODULE_STR,
            )
