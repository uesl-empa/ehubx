"""
ATES technology data module
"""
from enum import Enum
from typing import Dict, List, Set
import collections
from ehubx.data.index import Index
from ehubx.data.tech_data import Techs, TechId
from ehubx.data.ec_data import Ecs, EcId
from ehubx.data import exceptions


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


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/ates_tech"
"""String identifying the ATES technology data module for logging purposes"""


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

    def add_id(self, x: TechId) -> None:
        """
        Add a new ATES technology id

        :param x: Id to be added
        :type x: TechId
        """
        if x in self._ids:
            raise exceptions.DuplicateIdException(ExceptionKey.ID_ADD.value, x,
                                                  module=LOG_MODULE_STR)
        self._ids.add(x)

    # --------------- #
    # Property: ec_el #
    # --------------- #
    def get_ec_el(self, x: TechId) -> EcId:
        self._check_id(x, ExceptionKey.ECEL_GET)
        if x not in self._ec_el:
            raise exceptions.MissingIdException(
                ExceptionKey.ECEL_GET.value, x, module=LOG_MODULE_STR)
        return self._ec_el[x]

    def set_ec_el(self, x: TechId, e: EcId) -> None:
        self._check_id(x, ExceptionKey.ECEL_SET)
        self._ec_el[x] = e

    # --------------- #
    # Property: ec_ht #
    # --------------- #
    def get_ec_ht(self, x: TechId) -> EcId:
        self._check_id(x, ExceptionKey.ECHT_GET)
        if x not in self._ec_ht:
            raise exceptions.MissingIdException(
                ExceptionKey.ECHT_GET.value, x, module=LOG_MODULE_STR)
        return self._ec_ht[x]

    def set_ec_ht(self, x: TechId, e: EcId) -> None:
        self._check_id(x, ExceptionKey.ECHT_SET)
        self._ec_ht[x] = e

    # --------------- #
    # Property: ec_co #
    # --------------- #
    def get_ec_co(self, x: TechId) -> EcId:
        self._check_id(x, ExceptionKey.ECCO_GET)
        if x not in self._ec_co:
            raise exceptions.MissingIdException(
                ExceptionKey.ECCO_GET.value, x, module=LOG_MODULE_STR)
        return self._ec_co[x]

    def set_ec_co(self, x: TechId, e: EcId) -> None:
        self._check_id(x, ExceptionKey.ECCO_SET)
        self._ec_co[x] = e

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._ids: Set[TechId] = set()
        self._ec_el: Dict[TechId, EcId] = {}
        self._ec_ht: Dict[TechId, EcId] = {}
        self._ec_co: Dict[TechId, EcId] = {}

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self, techs: Techs, ecs: Ecs) -> None:
        """
        Validate all ATES technology data in this object. Apart from sense-
        checking parameter in terms of quantity, this includes checking
        whether the ids from other data classes used here are known there as
        well.

        :param stages: Stages data class
        :type stages: Stages
        :param techs: Techs data class
        :type techs: Techs
        :param ecs: ecs data class
        :type ecs: Ecs
        """
        self._validate_ids(techs)
        self._validate_ec_el(ecs)
        self._validate_ec_ht(ecs)
        self._validate_ec_co(ecs)
        self._validate_ecs()

    def _validate_ids(self, techs: Techs) -> None:
        exc_key = ExceptionKey.ID_VAL.value
        for x in self._ids:
            # stor_tech not in techs
            if x not in techs.ids:
                msg = f"ates_tech {x} not part of techs"
                raise exceptions.DataException(exc_key, [x], msg,
                                               module=LOG_MODULE_STR)

    def _validate_ec_el(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.ECEL_VAL.value
        for x, e in self._ec_el.items():
            if e not in ecs.ids:
                msg = f"Unknown ec_el {e} for {x}"
                raise exceptions.DataException(exc_key, [x, e], msg,
                                               module=LOG_MODULE_STR)

    def _validate_ec_ht(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.ECHT_VAL.value
        for x, e in self._ec_ht.items():
            if e not in ecs.ids:
                msg = f"Unknown ec_ht {e} for {x}"
                raise exceptions.DataException(exc_key, [x, e], msg,
                                               module=LOG_MODULE_STR)

    def _validate_ec_co(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.ECCO_VAL.value
        for x, e in self._ec_co.items():
            if e not in ecs.ids:
                msg = f"Unknown ec_co {e} for {x}"
                raise exceptions.DataException(exc_key, [x, e], msg,
                                               module=LOG_MODULE_STR)

    def _validate_ecs(self) -> None:
        exc_key = ExceptionKey.ECS_VAL.value
        for x in self._ids:
            all_ecs: List[Index] = [self.get_ec_el(x), self.get_ec_ht(x),
                                    self.get_ec_co(x)]
            dupes = [e for e, cnt in collections.Counter(all_ecs).items()
                     if cnt > 1]
            if len(dupes) > 0:
                msg = (f"ATES tech {x} has the ecs {dupes} occuring "
                       "multiple times across ec_el, ec_ht, and ec_co")
                raise exceptions.DataException(exc_key, dupes, msg,
                                               module=LOG_MODULE_STR)

    # ---------- #
    # Id checker #
    # ---------- #
    def _check_id(self, x: TechId, key: ExceptionKey) -> None:
        if x not in self._ids:
            raise exceptions.UnknownIdException(key.value, x,
                                                module=LOG_MODULE_STR)
