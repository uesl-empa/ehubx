"""
ec (energy carrier) data module
"""

from enum import Enum
from typing import Dict, List, Set

from ehubx.data import exceptions
from ehubx.data.index import Index, IndexKind
from ehubx.data.unit import DimlessUnit, MassUnit, PowerUnit, TimeUnit, Unit
from ehubx.data.value import Value


class EcId(Index):
    """
    ec (energy carrier) index
    """

    def __init__(self, key: str):
        super().__init__(IndexKind.EC, key)


class ImpExpType(Enum):
    """
    Import and export nature of an ec
    """

    NONE = "none"
    """ec has no specific import-export nature."""

    INTERNAL = "internal"
    """ec import/export happens internally. This essentially means that it is a
    naturally occuring resource such as solar irradiation."""

    CROSS = "cross"
    """ec has to be physically imported from beyond the system boundary. This
    type of import is typical for e.g.; electricity or gas"""


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the ec data module
    """

    ID_ADD = "adding to 'ids' of Ecs"
    UNIT_GET = "getting 'unit' from Ecs"
    UNIT_SET = "setting 'unit' of Ecs"
    IMPEXPTYPE_SET = "setting 'imp_exp_type' of Ecs"
    IMPEXPTYPE_GET = "getting 'imp_exp_type' from Ecs"
    ISENERGY_SET = "setting 'is_energy' of Ecs"
    ISENERGY_GET = "getting 'is_energy' from Ecs"
    HEURMAX_SET = "setting 'heuristic_max' of Ecs"
    HEURMAX_GET = "getting 'heuristic_max' from Ecs"
    HEURSUMMAX_SET = "setting 'heuristic_sum_max' of Ecs"
    HEURSUMMAX_GET = "getting 'heuristic_sum_max' from Ecs"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/ec"
"""String identifying the ec data module for logging purposes"""

DEF_UNIT: Unit = DimlessUnit()
"""Default value for the parameter 'unit' in the ec data module"""

DEF_IMPEXPTYPE: ImpExpType = ImpExpType.NONE
"""Default value for the parameter 'imp_exp_type' in the ec data module"""

DEF_ISENERGY: bool = True
"""Default value for the parameter 'is_energy' in the ec data module"""

DEF_HEURSUMMAX: float = float("inf")
"""Default value for the parameter 'heuristic_sum_max' in the ec data module"""


# Energy carrier main class
class Ecs:
    """
    Class to hold energy carrier (EC) data. Manages ec ids
    """

    # ------------- #
    # Property: ids #
    # ------------- #
    @property
    def ids(self) -> Set[EcId]:
        """
        Set of known ec ids
        """
        return self._ids

    @property
    def ids_in_order(self) -> List[EcId]:
        """
        List of known ec ids in alphabetical order
        """
        ids = list(self.ids)
        ids.sort(key=lambda e: e.key)
        return ids

    def add_id(self, e: EcId) -> None:
        """
        Add a new ec id

        :param e: Id to be added
        :type e: EcId
        """
        if e in self._ids:
            raise exceptions.DuplicateIdException(
                ExceptionKey.ID_ADD.value, e, module=LOG_MODULE_STR
            )
        self._ids.add(e)

    # -------------- #
    # Property: unit #
    # -------------- #
    def get_unit(self, e: EcId) -> Unit:
        """
        Get the unit of an ec. This is used to determine the type of unit
        that the ec is measured in, such as 1, kWh, kg, ... It is used
        to determine how the ec is treated in calculations and analyses.
        :param e: ec
        :type e: EcId
        :return: Unit of the ec
        :rtype: Unit
        """

        self._check_id(e, ExceptionKey.UNIT_GET)
        return self._unit.get(e, DEF_UNIT)

    def set_unit(self, e: EcId, unit: Unit) -> None:
        """
        Set the unit of an ec. This is used to determine the type of unit
        that the ec is measured in, such as p1, kWh, kg, ... It is used
        to determine how the ec is treated in calculations and analyses.

        :param e: ec
        :type e: EcId
        :param unit: Unit of the ec. This must be either a mass unit (e.g. kg) or an
            energy unit (e.g. kWh)
        :type unit: Unit
        """
        self._check_id(e, ExceptionKey.UNIT_SET)
        if not unit.same_type_as(MassUnit.KG) and not unit.same_type_as(
            PowerUnit.KW * TimeUnit.H
        ):
            raise exceptions.UnitException(
                str(unit),
                msg=(
                    f"Unit {unit} is not a valid unit for an ec. Only units of type "
                    f"{MassUnit.KG} or {PowerUnit.KW * TimeUnit.H} are allowed."
                ),
                module=LOG_MODULE_STR,
            )
        self._unit[e] = unit

    # ---------------------- #
    # Property: imp_exp_type #
    # ---------------------- #
    def get_imp_exp_type(self, e: EcId) -> ImpExpType:
        """
        Get the parameter 'imp_exp_type' which specifies whether import and
        export of this ec happens internally, across borders, or does not have
        a specific type. It affects the calculation of the self-sufficiency value since
        import of internal ecs increases the self-sufficiency value for a hub. This is
        an optional parameter with a default value of 'none'.

        :param e: ec
        :type e: EcId
        :return: Import-export type
        :rtype: ImpExpType
        """
        self._check_id(e, ExceptionKey.IMPEXPTYPE_GET)
        return self._imp_exp_type.get(e, DEF_IMPEXPTYPE)

    def set_imp_exp_type(self, e: EcId, imp_exp_type: ImpExpType) -> None:
        """
        Set the parameter 'imp_exp_type' which specifies whether import and
        export of this ec happens internally, across borders, or does not have
        a specific type. It affects the calculation of the self-sufficiency value since
        import of internal ecs increases the self-sufficiency value for a hub. This is
        an optional parameter with a default value of 'none'.

        :param e: ec
        :type e: EcId
        :param price: Import-export type
        :type price: float
        """
        self._check_id(e, ExceptionKey.IMPEXPTYPE_SET)
        self._imp_exp_type[e] = imp_exp_type

    # ------------------- #
    # Property: is_energy #
    # ------------------- #
    def is_energy(self, e: EcId) -> bool:
        """
        Return whether an ec actually measures energy. Usually, this coincides
        with the question whether this ec is measured in units of energy (e.g.
        kW). It affects the calculation of the self-sufficiency value since import of
        energy-ecs contribute directly to the total resource or cross-border
        imports which are used to calculate the self-sufficiency value. On the other
        hand, import of non-energy-ecs contributes indirectly to these values
        since they become relevant as inputs to conversion technologies. This
        is optional parameter with a default value of True.

        :param e: ec
        :type e: EcId
        :return: Whether the ec measures energy
        :rtype: bool
        """
        self._check_id(e, ExceptionKey.ISENERGY_GET)
        return self._is_energy.get(e, DEF_ISENERGY)

    def set_is_energy(self, e: EcId, is_energy: bool) -> None:
        """
        Set whether an ec actually measures energy. Usually, this coincides
        with the question whether this ec is measured in units of energy (e.g.
        kW). It affects the calculation of the self-sufficiency value since import of
        energy-ecs contribute directly to the total resource or cross-border
        imports which are used to calculate the self-sufficiency value. On the other
        hand, import of non-energy-ecs contributes indirectly to these values
        since they become relevant as inputs to conversion technologies. This
        is optional parameter with a default value of True.

        :param e: ec
        :type e: EcId
        :param is_energy: Whether the ec measures energy
        :type is_energy: bool
        """
        self._check_id(e, ExceptionKey.ISENERGY_SET)
        self._is_energy[e] = is_energy

    # ----------------------- #
    # Property: heuristic_max #
    # ----------------------- #
    def get_heuristic_max(self, e: EcId) -> Value:
        """
        Get the parameter 'heuristic_max' which specifies a heuristic maximum value
        (per timestep) for all streams flowing into or out of a balancing node for this
        ec. This limit will only be applied if no other more specific limits are
        available.

        :param e: ec
        :type e: EcId
        :return: Heuristic maximum value
        :rtype: Value
        """
        self._check_id(e, ExceptionKey.HEURMAX_GET)
        if e not in self._heur_max:
            raise exceptions.DataException(
                ExceptionKey.HEURMAX_GET.value,
                [e],
                f"ehubX was forced to use a heuristical maximum flow value for ec {e} "
                f"which has not been set. Please set such a value in ecs.yaml",
                module=LOG_MODULE_STR,
            )
        return self._heur_max[e]

    def set_heuristic_max(self, e: EcId, heuristic_max: Value) -> None:
        """
        Set the parameter 'heuristic_max' which specifies a heuristic maximum value
        (per timestep) for all streams flowing into or out of a balancing node for this
        ec. This limit will only be applied if no other more specific limits are
        available.

        :param e: ec
        :type e: EcId
        :param heuristic_max: Heuristic maximum value
        :type heuristic_max: Value
        """
        self._check_id(e, ExceptionKey.HEURMAX_SET)
        expected_unit = self.get_unit(e) / TimeUnit.H
        if not heuristic_max.unit.same_type_as(expected_unit):
            raise exceptions.UnitException(
                str(heuristic_max.unit),
                msg=(
                    f"Heuristic maximum value for ec {e} has unit "
                    f"{heuristic_max.unit} which is not compatible with the ec unit "
                    f"{expected_unit}."
                ),
                module=LOG_MODULE_STR,
            )
        if heuristic_max.is_negative:
            raise exceptions.DataException(
                ExceptionKey.HEURMAX_SET.value,
                [e],
                f"Heuristic maximum value for ec {e} must be non-negative.",
                module=LOG_MODULE_STR,
            )
        self._heur_max[e] = heuristic_max

    # --------------------------- #
    # Property: heuristic_sum_max #
    # --------------------------- #
    def get_heuristic_sum_max(self, e: EcId) -> Value:
        """
        Get the parameter 'heuristic_sum_max' which specifies a heuristic maximum value
        (summed over all timesteps) for the sum of all streams flowing into or out of a
        balancing node for this ec. This limit will only be applied if no other more
        specific limits are available.

        :param e: ec
        :type e: EcId
        :return: Heuristic sum maximum value
        :rtype: Value
        """
        self._check_id(e, ExceptionKey.HEURSUMMAX_GET)
        return self._heur_sum_max.get(e, Value(DEF_HEURSUMMAX, self.get_unit(e)))

    def set_heuristic_sum_max(self, e: EcId, heuristic_sum_max: Value) -> None:
        """
        Set the parameter 'heuristic_sum_max' which specifies a heuristic maximum value
        (summed over all timesteps) for the sum of all streams flowing into or out of a
        balancing node for this ec. This limit will only be applied if no other more
        specific limits are available.

        :param e: ec
        :type e: EcId
        :param heuristic_sum_max: Heuristic sum maximum value
        :type heuristic_sum_max: Value
        """
        self._check_id(e, ExceptionKey.HEURSUMMAX_SET)
        expected_unit = self.get_unit(e)
        if not heuristic_sum_max.unit.same_type_as(expected_unit):
            raise exceptions.UnitException(
                str(heuristic_sum_max.unit),
                msg=(
                    f"Heuristic sum maximum value for ec {e} has unit "
                    f"{heuristic_sum_max.unit} which is not compatible with the "
                    f"expected unit {expected_unit}."
                ),
                module=LOG_MODULE_STR,
            )
        if heuristic_sum_max.is_negative:
            raise exceptions.DataException(
                ExceptionKey.HEURSUMMAX_SET.value,
                [e],
                f"Heuristic sum maximum value for ec {e} must be non-negative.",
                module=LOG_MODULE_STR,
            )
        self._heur_sum_max[e] = heuristic_sum_max

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._ids: Set[EcId] = set()
        self._unit: Dict[EcId, Unit] = {}
        self._imp_exp_type: Dict[EcId, ImpExpType] = {}
        self._is_energy: Dict[EcId, bool] = {}
        self._heur_max: Dict[EcId, Value] = {}
        self._heur_sum_max: Dict[EcId, Value] = {}

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self) -> None:
        """
        Validate all ec data in this object.
        """

    # ---------- #
    # Id checker #
    # ---------- #
    def _check_id(self, e: EcId, where: ExceptionKey) -> None:
        if e not in self._ids:
            raise exceptions.UnknownIdException(where.value, e, module=LOG_MODULE_STR)
