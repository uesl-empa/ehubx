"""
ec (energy carrier) data module
"""
from typing import Dict, List, Set
from enum import Enum
from ehubx.data.index import Index, IndexKind
from ehubx.data import exceptions


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
    naturally occuring resource such as solar irradiation or wind."""

    CROSS = "cross"
    """ec has to be physically imported from beyond the system boundary. This
    type of import is typical for e.g.; electricity or gas"""


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the ec data module
    """
    ID_ADD = "adding to 'ids' of Ecs"
    IMPEXPTYPE_SET = "setting 'imp_exp_type' of Ecs"
    IMPEXPTYPE_GET = "getting 'imp_exp_type' from Ecs"
    ISENERGY_SET = "setting 'is_energy' of Ecs"
    ISENERGY_GET = "getting 'is_energy' from Ecs"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/ec"
"""String identifying the ec data module for logging purposes"""

DEF_IMPEXPTYPE: ImpExpType = ImpExpType.NONE
"""Default value for the parameter 'imp_exp_type' in the autarky data module"""

DEF_ISENERGY: bool = True
"""Default value for the parameter 'is_energy' in the autarky data module"""


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
        Set of known wind ec ids
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
            raise exceptions.DuplicateIdException(ExceptionKey.ID_ADD.value, e,
                                                  module=LOG_MODULE_STR)
        self._ids.add(e)

    # ---------------------- #
    # Property: imp_exp_type #
    # ---------------------- #
    def get_imp_exp_type(self, e: EcId) -> ImpExpType:
        """
        Get the parameter 'imp_exp_type' which specifies whether import and
        export of this ec happens internally, across borders, or does not have
        a specific type. It affects the calculation of the autarky value since
        import of internal ecs increases the autarky value for a hub. This is
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
        a specific type. It affects the calculation of the autarky value since
        import of internal ecs increases the autarky value for a hub. This is
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
        kW). It affects the calculation of the autarky value since import of
        energy-ecs contribute directly to the total resource or cross-border
        imports which are used to calculate the autarky value. On the other
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
        kW). It affects the calculation of the autarky value since import of
        energy-ecs contribute directly to the total resource or cross-border
        imports which are used to calculate the autarky value. On the other
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

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._ids: Set[EcId] = set()
        self._imp_exp_type: Dict[EcId, ImpExpType] = {}
        self._is_energy: Dict[EcId, bool] = {}

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
            raise exceptions.UnknownIdException(where.value, e,
                                                module=LOG_MODULE_STR)
