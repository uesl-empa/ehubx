"""
Storage technology data module
"""

from enum import Enum
from typing import Dict, List, Set, Tuple

from ehubx.core import common, logging
from ehubx.data import exceptions
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.unit import DimlessUnit, TimeUnit
from ehubx.data.value import Value


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the storage technology data
    module
    """

    ID_ADD = "adding to 'ids' of StorageTechs"
    ID_REMOVE = "removing from 'ids' of StorageTechs"
    ID_VAL = "validating 'id' of StorageTechs"
    EC_SET = "setting 'ec' of StorageTechs"
    EC_GET = "getting 'ec' from StorageTechs"
    EC_VAL = "validating 'ec' of StorageTechs"
    INEFF_SET = "setting 'in_eff' of StorageTechs"
    INEFF_GET = "getting 'in_eff' from StorageTechs"
    INEFF_VAL = "validating 'in_eff' of StorageTechs"
    OUTEFF_SET = "setting 'out_eff' of StorageTechs"
    OUTEFF_GET = "getting 'out_eff' from StorageTechs"
    OUTEFF_VAL = "validating 'out_eff' of StorageTechs"
    CHARGEMAX_SET = "setting 'charge_max' of StorageTechs"
    CHARGEMAX_GET = "getting 'charge_max' from StorageTechs"
    CHARGEMAX_VAL = "validating 'charge_max' of StorageTechs"
    DISCHARGEMAX_SET = "setting 'discharge_max' of StorageTechs"
    DISCHARGEMAX_GET = "getting 'discharge_max' from StorageTechs"
    DISCHARGEMAX_VAL = "validating 'discharge_max' of StorageTechs"
    STANDBYLOSS_SET = "setting 'standby_loss' of StorageTechs"
    STANDBYLOSS_GET = "getting 'standby_loss' from StorageTechs"
    STANDBYLOSS_VAL = "validating 'standby_loss' of StorageTechs"
    SOCMIN_SET = "setting 'soc_min' of StorageTechs"
    SOCMIN_GET = "getting 'soc_min' from StorageTechs"
    SOCMIN_VAL = "validating 'soc_min' of StorageTechs"
    SOCMAX_SET = "setting 'soc_max' of StorageTechs"
    SOCMAX_GET = "getting 'soc_max' from StorageTechs"
    SOCMAX_VAL = "validating 'soc_max' of StorageTechs"
    SOCMINMAX_VAL = "validating 'soc_min' against 'soc_max' of StorageTechs"
    SOCINIT_SET = "setting 'soc_init' of StorageTechs"
    SOCINIT_GET = "getting 'soc_init' from StorageTechs"
    SOCINIT_VAL = "validating 'soc_init' of StorageTechs"
    SOCINITMINMAX_VAL = (
        "validating 'soc_init' against 'soc_min' and 'soc_max' of StorageTechs"
    )


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/stor_tech"
"""String identifying the storage technology data module for logging
purposes"""

DEF_INEFF: float = 1
"""Default value for parameter 'in_eff' in the storage technology data
module"""

DEF_OUTEFF: float = 1
"""Default value for parameter 'out_eff' in the storage technology data
module"""

DEF_CHARGEMAX: float = 1
"""Default value for parameter 'charge_max' in the storage technology data
module"""

DEF_DISCHARGEMAX: float = 1
"""Default value for parameter 'discharge_max' in the storage technology data
module"""

DEF_STANDBYLOSS: float = 0
"""Default value for parameter 'standby_loss' in the storage technology data
module"""

DEF_SOCMIN: float = 0
"""Default value for parameter 'soc_min' in the storage technology data
module"""

DEF_SOCMAX: float = 1
"""Default value for parameter 'soc_max' in the storage technology data
module"""

DEF_SOCINIT: float = float("inf")
"""Default value for parameter 'soc_init' in the storage technology data
module"""


class StorageTechs:
    """
    Class for storage technology data. Manages storage technology ids, contains
    getters and setters for storage technology parameters and validation
    methods to control data integrity
    """

    # ------------- #
    # Property: ids #
    # ------------- #
    @property
    def ids(self) -> Set[TechId]:
        """
        Set of known storage technology ids
        """
        return self._ids

    @property
    def ids_in_order(self) -> List[TechId]:
        """
        List of known storage tech ids in alphabetical order
        """
        ids = list(self.ids)
        ids.sort(key=lambda x: x.key)
        return ids

    def add_id(self, x: TechId) -> None:
        """
        Add a new storage technology id

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
        Get the ec that is stored in the storage technology. This is a
        mandatory parameter for storage technologies

        :param x: Id of storage technology
        :type x: TechId
        :return: ec that is stored in the technology
        :rtype: EcId
        """
        self._check_id(x, ExceptionKey.EC_GET)
        ec = self._ec.get(x, None)
        if ec is None:
            raise exceptions.MissingIdException(
                ExceptionKey.EC_GET.value, x, module=LOG_MODULE_STR
            )
        return ec

    def set_ec(self, x: TechId, e: EcId) -> None:
        """
        Set the ec that is stored in the storage technology. This is a
        mandatory parameter for storage technologies.

        :param x: Id of storage technology
        :type x: TechId
        :param e: ec that is stored in the technology
        :type e: EcId
        :param ec_unit: Unit of the ec
        :type ec_unit: Unit
        """
        self._check_id(x, ExceptionKey.EC_SET)
        self._ec[x] = e

    # ---------------- #
    # Property: in_eff #
    # ---------------- #
    def get_in_eff(self, s: StageId, x: TechId) -> Value:
        """
        Get the parameter 'in_eff' for a storage technology during a stage
        which denotes the effectiveness of the charging process. An in_eff
        value of e.g.; 0.1 indicates that 90% of the input power can be
        transformed into stored energy. This is an optional parameter with a
        default value of 1.

        :param s: Stage id
        :type s: StageId
        :param x: Id of storage technology
        :type x: TechId
        :return: Input efficiency
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.INEFF_GET)
        return self._in_eff.get((s, x), Value(DEF_INEFF))

    def set_in_eff(self, s: StageId, x: TechId, in_eff: Value) -> None:
        """
        Set the parameter 'in_eff' for a storage technology during a stage
        which denotes the effectiveness of the charging process. An in_eff
        value of e.g.; 0.1 indicates that 90% of the input power can be
        transformed into stored energy. This is an optional parameter with a
        default value of 1.

        :param s: Stage id
        :type s: StageId
        :param x: Id of storage technology
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
        Get the parameter 'out_eff' for a storage technology during a stage
        which denotes the effectiveness of the discharging process. An out_eff
        value of e.g.; 0.1 indicates that 90% of the discharged energy can be
        used. This is an optional parameter with a default value of 1.

        :param s: Stage id
        :type s: StageId
        :param x: Id of storage technology
        :type x: TechId
        :return: Output efficiency
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.OUTEFF_GET)
        return self._out_eff.get((s, x), Value(DEF_OUTEFF))

    def set_out_eff(self, s: StageId, x: TechId, out_eff: Value) -> None:
        """
        Set the parameter 'out_eff' for a storage technology during a stage
        which denotes the effectiveness of the discharging process. An out_eff
        value of e.g.; 0.1 indicates that 90% of the discharged energy can be
        used. This is an optional parameter with a default value of 1.

        :param s: Stage id
        :type s: StageId
        :param x: Id of storage technology
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

    # -------------------- #
    # Property: charge_max #
    # -------------------- #
    def get_charge_max(self, s: StageId, x: TechId) -> Value:
        """
        Get the parameter 'charge_max' which denotes the maximal relative
        charging rate of a storage technology. A maximal charging rate of e.g.;
        0.4 indiciates that 40% of the technology's energy storage capacity can
        be charged from one time step to the next. This is an optional
        parameter with a default value of 1

        :param s: Stage id
        :type s: StageId
        :param x: Id of storage technology
        :type x: TechId
        :return: Maximal charging rate
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.CHARGEMAX_GET)
        return self._charge_max.get(
            (s, x), Value(DEF_CHARGEMAX, DimlessUnit() / TimeUnit.H)
        )

    def set_charge_max(self, s: StageId, x: TechId, charge_max: Value) -> None:
        """
        Set the parameter 'charge_max' which denotes the maximal relative
        charging rate of a storage technology. A maximal charging rate of e.g.;
        0.4 indiciates that 40% of the technology's energy storage capacity can
        be charged from one time step to the next. This is an optional
        parameter with a default value of 1.

        :param s: Stage id
        :type s: StageId
        :param x: Id of storage technology
        :type x: TechId
        :param charge_max: Maximal charging rate
        :type charge_max: float
        """
        self._check_id(x, ExceptionKey.CHARGEMAX_SET)
        expected_unit = DimlessUnit() / TimeUnit.H
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
        Get the parameter 'discharge_max' which denotes the maximal relative
        discharging rate of a storage technology. A maximal discharging rate of
        e.g.; 0.4 indicates that 40% of the technology's energy storage
        capacity can be discharged from one time step to the next. This is an
        optional parameter with a default value of 1.

        param s: Stage id
        :type s: StageId
        :param x: Id of storage technology
        :type x: TechId
        :param discharge_max: Maximal discharging rate
        :type discharge_max: float
        """
        self._check_id(x, ExceptionKey.DISCHARGEMAX_GET)
        return self._discharge_max.get(
            (s, x), Value(DEF_DISCHARGEMAX, DimlessUnit() / TimeUnit.H)
        )

    def set_discharge_max(self, s: StageId, x: TechId, discharge_max: Value) -> None:
        """
        Set the parameter 'discharge_max' which denotes the maximal relative
        discharging rate of a storage technology. A maximal discharging rate of
        e.g.; 0.4 indicates that 40% of the technology's energy storage
        capacity can be discharged from one time step to the next. This is an
        optional parameter with a default value of 1.

        param s: Stage id
        :type s: StageId
        :param x: Id of storage technology
        :type x: TechId
        :param discharge_max: Maximal discharging rate
        :type discharge_max: Value
        """
        self._check_id(x, ExceptionKey.DISCHARGEMAX_SET)
        expected_unit = DimlessUnit() / TimeUnit.H
        if not discharge_max.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.DISCHARGEMAX_SET.value,
                [s, x],
                f"Unit of discharge_max[{s}, {x}] = {discharge_max} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._discharge_max[s, x] = discharge_max

    # ---------------------- #
    # Property: standby_loss #
    # ---------------------- #
    def get_standby_loss(self, s: StageId, x: TechId) -> Value:
        """
        Get the parameter 'standby_loss' for a technology which denotes the
        relative loss rate of stored energy per time step. This is an optional
        parameter with a default value of 0.

        :param s: Stage id
        :type s: StageId
        :param x: Id of storage technology
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
        Set the parameter 'standby_loss' for a technology which denotes the
        relative loss rate of stored energy per time step. This is an optional
        parameter with a default value of 0.

        :param s: Stage id
        :type s: StageId
        :param x: Id of storage technology
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

    # ----------------- #
    # Property: soc_min #
    # ----------------- #
    def get_soc_min(self, s: StageId, x: TechId) -> Value:
        """
        Get the parameter 'soc_min' which denotes the minimal state of charge
        that is allowed for a storage technology. An soc_min value of e.g.;
        0.1 indicates that at least 10% of the technology's storage capacity
        must be filled at all times. This is an optional parameter with a
        default value of 0.

        :param s: Stage id
        :type s: StageId
        :param x: Id of storage technology
        :type x: TechId
        :return: Minimal state of charge
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.SOCMIN_GET)
        return self._soc_min.get((s, x), Value(DEF_SOCMIN))

    def set_soc_min(self, s: StageId, x: TechId, soc_min: Value) -> None:
        """
        Set the parameter 'soc_min' which denotes the minimal state of charge
        that is allowed for a storage technology. An soc_min value of e.g.;
        0.1 indicates that at least 10% of the technology's storage capacity
        must be filled at all times. This is an optional parameter with a
        default value of 0.

        :param s: Stage id
        :type s: StageId
        :param x: Id of storage technology
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
        that is allowed for a storage technology. An soc_max value of e.g.;
        0.8 indicates that at most 80% of the technology's storage capacity
        may be filled at all times. This is an optional parameter with a
        default value of 1.

        :param s: Stage id
        :type s: StageId
        :param x: Id of storage technology
        :type x: TechId
        :return: Maximal state of charge
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.SOCMAX_GET)
        return self._soc_max.get((s, x), Value(DEF_SOCMAX))

    def set_soc_max(self, s: StageId, x: TechId, soc_max: Value) -> None:
        """
        Set the parameter 'soc_max' which denotes the maximal state of charge
        that is allowed for a storage technology. An soc_max value of e.g.;
        0.8 indicates that at most 80% of the technology's storage capacity
        may be filled at all times. This is an optional parameter with a
        default value of 1.

        :param s: Stage id
        :type s: StageId
        :param x: Id of storage technology
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
        Get the parameter 'soc_init' which denotes a storage technology's
        initial state of charge (i.e.; at the first time step in every stage)
        in each hub. An initial state of charge of 0.4 indicates that, at the
        beginning of the time horizon, the technology's energy storage level is
        at 40% of its storage capacity. An soc_init value of infinity indicates
        that the initial state of charge level is not set but can be chosen by
        the optimizer. This is an optional parameter with a  default value of
        infinity.

        :param h: Hub id
        :type h: HubId
        :param x: Id of storage technology
        :type x: TechId
        :return: Initial state of charge
        :rtype: Value
        """
        self._check_id(x, ExceptionKey.SOCINIT_GET)
        return self._soc_init.get((h, x), Value(DEF_SOCINIT))

    def set_soc_init(self, h: HubId, x: TechId, soc_init: Value) -> None:
        """
        Set the parameter 'soc_init' which denotes a storage technology's
        initial state of charge (i.e.; at the first time step in every stage)
        in each hub. An initial state of charge of 0.4 indicates that, at the
        beginning of the time horizon, the technology's energy storage level is
        at 40% of its storage capacity. An soc_init value of infinity indicates
        that the initial state of charge level is not set but can be chosen by
        the optimizer. This is an optional parameter with a  default value of
        infinity.

        :param h: Hub id
        :type h: HubId
        :param x: Id of storage technology
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

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._ids: Set[TechId] = set()
        self._ec: Dict[TechId, EcId] = {}
        self._in_eff: Dict[Tuple[StageId, TechId], Value] = {}
        self._out_eff: Dict[Tuple[StageId, TechId], Value] = {}
        self._charge_max: Dict[Tuple[StageId, TechId], Value] = {}
        self._discharge_max: Dict[Tuple[StageId, TechId], Value] = {}
        self._standby_loss: Dict[Tuple[StageId, TechId], Value] = {}
        self._soc_min: Dict[Tuple[StageId, TechId], Value] = {}
        self._soc_max: Dict[Tuple[StageId, TechId], Value] = {}
        self._soc_init: Dict[Tuple[HubId, TechId], Value] = {}

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self, stages: Stages, hubs: Hubs, ecs: Ecs, techs: Techs) -> None:
        """
        Validate all storage technology data in this object. Apart from sense-
        checking parameter in terms of quantity, this includes checking whether
        the ids from other data classes used here are known there as well.

        :param stages: Stages data class
        :type stages: Stages
        :param hubs: Hubs data class
        :type hubs: Hubs
        :param ecs: ec data class
        :type ecs: Ecs
        :param techs: Technology data class
        :type techs: Techs
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
            if in_eff < Value(common.EPS_ZEROCHECK):
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
            if out_eff < Value(common.EPS_ZEROCHECK):
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

    # ---------- #
    # Id checker #
    # ---------- #
    def _check_id(self, x: TechId, key: ExceptionKey) -> None:
        if x not in self._ids:
            raise exceptions.UnknownIdException(key.value, x, module=LOG_MODULE_STR)
