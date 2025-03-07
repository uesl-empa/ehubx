"""
Technology data module
"""

from enum import Enum
from typing import Dict, List, Set, Tuple

from ehubx.core import common, logging
from ehubx.data import exceptions
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.index import Index, IndexKind
from ehubx.data.stage_data import StageId, Stages


class TechId(Index):
    """
    Technology index
    """

    def __init__(self, key: str):
        super().__init__(IndexKind.TECH, key)


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the technology data module
    """

    ID_ADD = "adding to 'ids' of Techs"
    ID_REMOVE = "removing from 'ids' of Techs"
    TECH_COPY = "copying tech of Techs"
    TECH_REMOVE = "remove tech of Techs"
    ALLOWEDSTAGES_ADD = "adding to 'allowed_stages' of Techs"
    ALLOWEDSTAGES_REMOVE = "removing from 'allowed_stages' of Techs"
    ALLOWEDSTAGES_VAL = "validating 'allowed_stages' of Techs"
    ALLOWEDHUBS_ADD = "adding to 'allowed_hubs' of Techs"
    ALLOWEDHUBS_REMOVE = "removing from 'allowed_hubs' of Techs"
    ALLOWEDHUBS_VAL = "validating 'allowed_hubs' of Techs"
    LIFETIME_SET = "setting 'lifetime' of Techs"
    LIFETIME_GET = "getting 'lifetime' from Techs"
    LIFETIME_VAL = "validating 'lifetime' of Techs"
    INTERESTRATE_SET = "setting 'interest_rate' of Techs"
    INTERESTRATE_GET = "getting 'interest_rate' from Techs"
    INTERESTRATE_VAL = "validating 'interest_rate' of Techs"
    UNITCAPMIN_SET = "setting 'unit_cap_min' of Techs"
    UNITCAPMIN_GET = "getting 'unit_cap_min' from Techs"
    UNITCAPMIN_VAL = "validating 'unit_cap_min' of Techs"
    ONETIMECAPEX_SET = "setting 'one_time_capex' of Techs"
    ONETIMECAPEX_GET = "getting 'one_time_capex' from Techs"
    ONETIMECAPEX_VAL = "setting 'one_time_capex' of Techs"
    CAPEXPERCAP_SET = "setting 'capex_per_cap' of Techs"
    CAPEXPERCAP_GET = "getting 'capex_per_cap' from Techs"
    CAPEXPERCAP_VAL = "validating 'capex_per_cap' of Techs"
    ONETIMEOPEX_SET = "setting 'one_time_opex' of Techs"
    ONETIMEOPEX_GET = "getting 'one_time_opex' from Techs"
    ONETIMEOPEX_VAL = "validating 'one_time_opex' of Techs"
    OPEXPERCAP_SET = "setting 'opex_per_cap' of Techs"
    OPEXPERCAP_GET = "getting 'opex_per_cap' from Techs"
    OPEXPERCAP_VAL = "validating 'opex_per_cap' of Techs"
    CO2PERCAP_SET = "setting 'co2_per_cap' of Techs"
    CO2PERCAP_GET = "getting 'co2_per_cap' from Techs"
    CO2PERCAP_VAL = "validating 'co2_per_cap' of Techs"
    LASTINSTLYEAR_SET = "setting 'last_instl_year' of Techs"
    LASTINSTLYEAR_GET = "getting 'last_instl_year' from Techs"
    LASTINSTLYEAR_VAL = "validating 'last_instl_year' of Techs"
    CAPINIT_SET = "setting 'cap_init' of Techs"
    CAPINIT_GET = "getting 'cap_init' from Techs"
    CAPINIT_VAL = "setting 'cap_init' of Techs"
    AGEINIT_SET = "setting 'age_init' of Techs"
    AGEINIT_GET = "getting 'age_init' from Techs"
    AGEINIT_VAL = "setting 'age_init' of Techs"
    CAPMIN_SET = "setting 'cap_min' of Techs"
    CAPMIN_GET = "getting 'cap_min' from Techs"
    CAPMIN_VAL = "validating 'cap_min' of Techs"
    CAPMINALLOWEDHUBS_VAL = "validating 'cap_min' agains 'allowed_hubs' of Techs"
    CAPMAX_SET = "setting 'cap_max' of Techs"
    CAPMAX_GET = "getting 'cap_max' from Techs"
    CAPMAX_VAL = "validating 'cap_max' of Techs"
    COUPLEDMAINTECH_SET = "setting 'coupled_main_tech' of Techs"
    COUPLEDMAINTECH_GET = "getting 'coupled_main_tech' from Techs"
    COUPLEDMAINTECH_VAL = "validating 'coupled_main_tech' in Techs"
    COUPLEDSUBTECH_VAL = "validating 'coupled_sub_tech' in Techs"
    COUPLEDSUBTECHS_GET = "getting 'coupled_sub_techs' in Techs"
    COUPLEDCAPFACTOR_SET = "setting 'coupled_cap_factors' in Techs"
    COUPLEDCAPFACTOR_GET = "getting 'coupled_cap_factors' from Techs"
    COUPLEDCAPFACTOR_VAL = "validating 'coupled_cap_factors' in Techs"
    COUPLEDCAPFACTOR_NOTASUB = (
        "coupled_cap_factor' tech not a sub tech " + "in ConversionTechs"
    )
    COPYOVERTECH = "copying tech from one Techs instance to another"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/tech"
"""String identifying the technology data module for logging purposes"""

DEF_UNITCAPMIN: float = 0
"""Default value for parameter 'unit_cap_min' in the technology data module"""

DEF_ONETIMECAPEX: float = 0
"""Default value for parameter 'one_time_capex' in the technology data
module"""

DEF_CAPEXPERCAP: float = 0
"""Default value for parameter 'capex_per_cap' in the technology data module"""

DEF_ONETIMEOPEX: float = 0
"""Default value for parameter 'one_time_opex' in the technology data module"""

DEF_OPEXPERCAP: float = 0
"""Default value for parameter 'opex_per_cap' in the technology data module"""

DEF_CO2PERCAP: float = 0
"""Default value for parameter 'co2_per_cap' in the technology data module"""

DEF_LASTINSTLYEAR: float = float("inf")
"""Default value for parameter 'last_instl_year' in the technology data
module"""

DEF_CAPINIT: float = 0
"""Default value for parameter 'cap_init' in the technology data module"""

DEF_AGEINIT: float = 0
"""Default value for parameter 'age_init' in the technology data module"""

DEF_CAPMIN: float = 0
"""Default value for parameter 'cap_min' in the technology data module"""

DEF_CAPMAX: float = float("inf")
"""Default value for parameter 'cap_max' in the technology data module"""

DEF_COUPLEDCAPFACTOR: float = 1
"""Default value for parameter 'coupled_cap_factor' in the technology data
module"""


class Techs:
    """
    Class for technology data. Manages technology ids, contains
    getters and setters for technology parameters and validation methods
    to control data integrity
    """

    # ------------- #
    # Property: ids #
    # ------------- #
    @property
    def ids(self) -> Set[TechId]:
        """
        Set of known technology ids
        """
        return self._ids

    @property
    def ids_in_order(self) -> List[TechId]:
        """
        List of known tech ids in alphabetical order
        """
        ids = list(self.ids)
        ids.sort(key=lambda x: x.key)
        return ids

    def add_id(self, x: TechId) -> None:
        """
        Add a new technology id

        :param x: Id to be added
        :type x: TechId
        """
        if x in self._ids:
            raise exceptions.DuplicateIdException(
                ExceptionKey.ID_ADD.value, x, module=LOG_MODULE_STR
            )
        self._ids.add(x)

    def remove_id(self, x: TechId) -> None:
        """
        Remove an id and all associated parameters from the known technologies

        :param x: Id to be removed
        :type x: TechId
        """
        if x not in self._ids:
            raise exceptions.MissingIdException(
                ExceptionKey.ID_REMOVE.value, x, module=LOG_MODULE_STR
            )
        self._ids.remove(x)
        if x in self._allowed_stages:
            self._allowed_stages.pop(x)
        if x in self._allowed_hubs:
            self._allowed_hubs.pop(x)
        if x in self._lifetime:
            self._lifetime.pop(x)
        if x in self._interest_rate:
            self._interest_rate.pop(x)
        for s, x2 in list(self._unit_cap_min.keys()):
            if x == x2:
                self._unit_cap_min.pop((s, x))
        for s, x2 in list(self._one_time_capex.keys()):
            if x == x2:
                self._one_time_capex.pop((s, x))
        for s, x2 in list(self._capex_per_cap.keys()):
            if x == x2:
                self._capex_per_cap.pop((s, x))
        for s, x2 in list(self._one_time_opex.keys()):
            if x == x2:
                self._one_time_opex.pop((s, x))
        for s, x2 in list(self._opex_per_cap.keys()):
            if x == x2:
                self._opex_per_cap.pop((s, x))
        for s, x2 in list(self._co2_per_cap.keys()):
            if x == x2:
                self._co2_per_cap.pop((s, x))
        for h, x2 in list(self._last_instl_year.keys()):
            if x == x2:
                self._last_instl_year.pop((h, x))
        for h, x2 in list(self._cap_init.keys()):
            if x == x2:
                self._cap_init.pop((h, x))
        for h, x2 in list(self._age_init.keys()):
            if x == x2:
                self._age_init.pop((h, x))
        for s, h, x2 in list(self._cap_min.keys()):
            if x == x2:
                self._cap_min.pop((s, h, x))
        for s, h, x2 in list(self._cap_max.keys()):
            if x == x2:
                self._cap_max.pop((s, h, x))
        for x_sub in list(self._coupled_main_tech.keys()):
            if x == x_sub:
                self._coupled_main_tech.pop(x)
                continue
            if x == self._coupled_main_tech[x_sub]:
                self._coupled_main_tech.pop(x_sub)
        if x in self._coupled_cap_factor:
            self._coupled_cap_factor.pop(x)

    # --------- #
    # Copy tech #
    # --------- #
    def copy_tech(self, x: TechId, x_new: TechId) -> None:
        """
        Copy one of the object's technologies, giving it a new id

        :param x: Id of the existing technology to be copied
        :type x: TechId
        :param x_new: New technology id
        :type x_new: TechId
        """
        if x not in self._ids:
            raise exceptions.MissingIdException(
                ExceptionKey.TECH_COPY.value, x, module=LOG_MODULE_STR
            )
        if x_new in self._ids:
            raise exceptions.DuplicateIdException(
                ExceptionKey.TECH_COPY.value, x, module=LOG_MODULE_STR
            )
        self._ids.add(x_new)
        if x in self._allowed_stages:
            self._allowed_stages[x_new] = self._allowed_stages[x].copy()
        if x in self._allowed_hubs:
            self._allowed_hubs[x_new] = self._allowed_hubs[x].copy()
        if x in self._lifetime:
            self._lifetime[x_new] = self._lifetime[x]
        if x in self._interest_rate:
            self._interest_rate[x_new] = self._interest_rate[x]
        for s, x_ in list(self._unit_cap_min):
            if x == x_:
                self._unit_cap_min[s, x_new] = self._unit_cap_min[s, x]
        for s, x_ in list(self._one_time_capex):
            if x == x_:
                self._one_time_capex[s, x_new] = self._one_time_capex[s, x]
        for s, x_ in list(self._capex_per_cap):
            if x == x_:
                self._capex_per_cap[s, x_new] = self._capex_per_cap[s, x]
        for s, x_ in list(self._one_time_opex):
            if x == x_:
                self._one_time_opex[s, x_new] = self._one_time_opex[s, x]
        for s, x_ in list(self._opex_per_cap):
            if x == x_:
                self._opex_per_cap[s, x_new] = self._opex_per_cap[s, x]
        for s, x_ in list(self._co2_per_cap):
            if x == x_:
                self._co2_per_cap[s, x_new] = self._co2_per_cap[s, x]
        for h, x_ in list(self._last_instl_year):
            if x == x_:
                self._last_instl_year[h, x_new] = self._last_instl_year[h, x]
        for h, x_ in list(self._cap_init):
            if x == x_:
                self._cap_init[h, x_new] = self._cap_init[h, x]
        for h, x_ in list(self._age_init):
            if x == x_:
                self._age_init[h, x_new] = self._age_init[h, x]
        for s, h, x_ in list(self._cap_min):
            if x == x_:
                self._cap_min[s, h, x_new] = self._cap_min[s, h, x]
        for s, h, x_ in list(self._cap_max):
            if x == x_:
                self._cap_max[s, h, x_new] = self._cap_max[s, h, x]
        for x_sub in list(self._coupled_main_tech):
            if x == x_sub:
                self._coupled_main_tech[x_new] = self._coupled_main_tech[x]
            if x == self._coupled_main_tech[x_sub]:
                raise Exception()
        if x in self._coupled_cap_factor:
            self._coupled_cap_factor[x_new] = self._coupled_cap_factor[x]

    # ----------- #
    # Remove tech #
    # ----------- #
    def remove_tech(self, x: TechId) -> None:
        """
        Remove one of the data class's technologies

        :param x: Id of technology to be removed
        :type x: TechId
        """
        if x not in self._ids:
            raise exceptions.MissingIdException(
                ExceptionKey.TECH_REMOVE.value, x, module=LOG_MODULE_STR
            )
        self._ids.remove(x)
        self._allowed_stages.pop(x, None)
        self._allowed_hubs.pop(x, None)
        self._lifetime.pop(x, None)
        self._interest_rate.pop(x, None)
        for s, x_ in list(self._unit_cap_min):
            if x == x_:
                self._unit_cap_min.pop((s, x))
        for s, x_ in list(self._one_time_capex):
            if x == x_:
                self._one_time_capex.pop((s, x))
        for s, x_ in list(self._capex_per_cap):
            if x == x_:
                self._capex_per_cap.pop((s, x))
        for s, x_ in list(self._one_time_opex):
            if x == x_:
                self._one_time_opex.pop((s, x))
        for s, x_ in list(self._opex_per_cap):
            if x == x_:
                self._opex_per_cap.pop((s, x))
        for s, x_ in list(self._co2_per_cap):
            if x == x_:
                self._co2_per_cap.pop((s, x))
        for h, x_ in list(self._last_instl_year):
            if x == x_:
                self._last_instl_year.pop((h, x))
        for h, x_ in list(self._cap_init):
            if x == x_:
                self._cap_init.pop((h, x))
        for h, x_ in list(self._age_init):
            if x == x_:
                self._age_init.pop((h, x))
        for s, h, x_ in list(self._cap_min):
            if x == x_:
                self._cap_min.pop((s, h, x))
        for s, h, x_ in list(self._cap_max):
            if x == x_:
                self._cap_max.pop((s, h, x))
        for x_sub, x_main in self._coupled_main_tech.items():
            if x_sub == x:
                self._coupled_main_tech.pop(x)
            if x_main == x:
                self._coupled_main_tech.pop(x_sub)

    # ------------------------ #
    # Property: allowed_stages #
    # ------------------------ #
    def get_allowed_stages(self, x: TechId) -> Set[StageId]:
        """
        Get all stages that are considered allowed for a technology.
        Technologies are only considered installable, installed or useable in
        allowed stages.

        :param x: Technology id
        :type x: TechId
        :return: Set of allowed stage ids
        :rtype: Set[StageId]
        """
        return self._allowed_stages.get(x, set())

    def add_allowed_stage(self, s: StageId, x: TechId) -> None:
        """
        Add an allowed stage for a technology. Technologies are only
        considered installable, installed or useable in allowed stages.

        :param s: Id of stage to be added as allowed
        :type s: StageId
        :param x: Technology id
        :type x: TechId
        """
        if x not in self._allowed_stages:
            self._allowed_stages[x] = set()
        if s in self._allowed_stages[x]:
            msg = f"Added allowed_stage {s} for {x} which was already allowed"
            logging.log_warning(msg, module=LOG_MODULE_STR)
        self._allowed_stages[x].add(s)

    def remove_allowed_stage(self, s: StageId, x: TechId) -> None:
        """
        Remove a stage from the allowed stages of a technology. Technologies
        are only considered installable, installed or useable in allowed
        stages.

        :param s: Id of stage to be removed from allowed stages
        :type s: StageId
        :param x: Technology id
        :type x: TechId
        """
        if x not in self._allowed_stages:
            self._allowed_stages[x] = set()
        if s not in self._allowed_stages[x]:
            msg = f"Removing allowed_stage {s} for {x} which was already not allowed"
            logging.log_warning(msg, module=LOG_MODULE_STR)
            return
        self._allowed_stages[x].remove(s)

    # ---------------------- #
    # Property: allowed_hubs #
    # ---------------------- #
    def get_allowed_hubs(self, x: TechId) -> Set[HubId]:
        """
        Get all hubs that are considered allowed for a technology.
        Technologies are only considered installable, installed or useable in
        allowed hubs.

        :param x: Technology id
        :type x: TechId
        :return: Set of allowed hub ids
        :rtype: Set[HubId]
        """
        return self._allowed_hubs.get(x, set())

    def add_allowed_hub(self, h: HubId, x: TechId) -> None:
        """
        Add an allowed hub for a technology. Technologies are only
        considered installable, installed or useable in allowed hubs.

        :param h: Id of hub to be added as allowed
        :type h: HubId
        :param x: Technology id
        :type x: TechId
        """
        if x not in self._allowed_hubs:
            self._allowed_hubs[x] = set()
        if h in self._allowed_hubs[x]:
            msg = f"Added allowed_hub {h} for {x} which was already allowed"
            logging.log_warning(msg, module=LOG_MODULE_STR)
        self._allowed_hubs[x].add(h)

    def remove_allowed_hub(self, h: HubId, x: TechId) -> None:
        """
        Remove a hub from the allowed hubs of a technology. Technologies
        are only considered installable, installed or useable in allowed hubs.

        :param h: Id of hub to be removed from allowed hubs
        :type h: HubId
        :param x: Technology id
        :type x: TechId
        """
        if x not in self._allowed_hubs:
            self._allowed_hubs[x] = set()
        if h not in self._allowed_hubs[x]:
            msg = f"Removing allowed_hub {h} for {x} which was already not allowed"
            logging.log_warning(msg, module=LOG_MODULE_STR)
            return
        self._allowed_hubs[x].remove(h)

    # ------------------ #
    # Property: lifetime #
    # ------------------ #
    def get_lifetime(self, x: TechId) -> int:
        """
        Get the parameter 'lifetime' of a technology. From the moment they are
        installed, technologies can operate and will stay installed until they
        have reached their end of life. Initially installed technologies remain
        operational based on their initial age and lifetime. This is a
        mandatory parameter.

        :param x: Technology id
        :type x: TechId
        :return: Lifetime [a]
        :rtype: int
        """
        self._check_id(x, ExceptionKey.LIFETIME_GET)
        lifetime = self._lifetime.get(x, None)
        if lifetime is None:
            raise exceptions.MissingIdException(
                ExceptionKey.LIFETIME_GET.value, x, module=LOG_MODULE_STR
            )
        return lifetime

    def set_lifetime(self, x: TechId, lifetime: int) -> None:
        """
        Set the parameter 'lifetime' of a technology. From the moment they are
        installed, technologies can operate and will stay installed until they
        have reached their end of life. Initially installed technologies remain
        operational based on their initial age and lifetime. This is a
        mandatory parameter.

        :param x: Technology id
        :type x: TechId
        :param lifetime: Lifetime [a]
        :type lifetime: int
        """
        self._check_id(x, ExceptionKey.LIFETIME_SET)
        self._lifetime[x] = lifetime

    # ----------------------- #
    # Property: interest_rate #
    # ----------------------- #
    def get_interest_rate(self, x: TechId) -> float:
        """
        Get the parameter 'interest_rate' of a technology which is used to
        calculate yearly annuity payments for CAPEX investments. For the
        technology data class, interest rate is a mandatory parameter but it
        may be left blank in the input data, leaving the parser to set the
        default interest rate

        :param x: Technology id
        :type x: TechId
        :return: Interest rate (as a numerical value between 0 and 1) [1]
        :rtype: float
        """
        self._check_id(x, ExceptionKey.INTERESTRATE_GET)
        interest_rate = self._interest_rate.get(x, None)
        if interest_rate is None:
            raise exceptions.MissingIdException(
                ExceptionKey.INTERESTRATE_GET.value, x, module=LOG_MODULE_STR
            )
        return interest_rate

    def set_interest_rate(self, x: TechId, interest_rate: float) -> None:
        """
        Set the parameter 'interest_rate' of a technology which is used to
        calculate yearly annuity payments for CAPEX investments. For the
        technology data class, interest rate is a mandatory parameter but it
        may be left blank in the input data, leaving the parser to set the
        default interest rate

        :param x: Technology id
        :type x: TechId
        :param interest_rate: Interest rate (as a numerical value between 0 and
            1) [1]
        :type interest_rate: float
        """
        self._check_id(x, ExceptionKey.INTERESTRATE_SET)
        self._interest_rate[x] = interest_rate

    # ---------------------- #
    # Property: unit_cap_min #
    # ---------------------- #
    def get_unit_cap_min(self, s: StageId, x: TechId) -> float:
        """
        Get the parameter 'unit_cap_min' which denotes the minimal amount of
        technology capacity that has to be installed of a technology if any
        installation occurs at all. This is an optional parameter with a
        default value of 0.

        :param s: Stage id
        :type s: StageId
        :param x: Technology id
        :type x: TechId
        :return: Minimal amount of installable technology capacity [CAP]
        :rtype: float
        """
        self._check_id(x, ExceptionKey.UNITCAPMIN_GET)
        return self._unit_cap_min.get((s, x), DEF_UNITCAPMIN)

    def set_unit_cap_min(self, s: StageId, x: TechId, unit_cap_min: float) -> None:
        """
        Set the parameter 'unit_cap_min' which denotes the minimal amount of
        technology capacity that has to be installed of a technology if any
        installation occurs at all. This is an optional parameter with a
        default value of 0.

        :param s: Stage id
        :type s: StageId
        :param x: Technology id
        :type x: TechId
        :param unit_cap_min: Minimal amount of installable technology capacity
            [CAP]
        :type unit_cap_min: float
        """
        self._check_id(x, ExceptionKey.UNITCAPMIN_SET)
        self._unit_cap_min[s, x] = unit_cap_min

    # ------------------------ #
    # Property: one_time_capex #
    # ------------------------ #
    def get_one_time_capex(self, s: StageId, x: TechId) -> float:
        """
        Get the parameter 'one_time_capex' which denotes a fixed amount of
        CAPEX cost that occurs if any amount of capacity is installed for this
        technology. This is an optional parameter with a default value of 0.

        :param s: Stage id
        :type s: StageId
        :param x: Technology id
        :type x: TechId
        :return: Fixed CAPEX cost for installed technology [CHF]
        :rtype: float
        """
        self._check_id(x, ExceptionKey.ONETIMECAPEX_GET)
        return self._one_time_capex.get((s, x), DEF_ONETIMECAPEX)

    def set_one_time_capex(self, s: StageId, x: TechId, one_time_capex: float) -> None:
        """
        Set the parameter 'one_time_capex' which denotes a fixed amount of
        CAPEX cost that occurs if any amount of capacity is installed for this
        technology. This is an optional parameter with a default value of 0.

        :param s: Stage id
        :type s: StageId
        :param x: Technology id
        :type x: TechId
        :param one_time_capex: Fixed CAPEX cost for installed technology [CHF]
        :type one_time_capex: float
        """
        self._check_id(x, ExceptionKey.ONETIMECAPEX_SET)
        self._one_time_capex[s, x] = one_time_capex

    # ----------------------- #
    # Property: capex_per_cap #
    # ----------------------- #
    def get_capex_per_cap(self, s: StageId, x: TechId) -> float:
        """
        Get the parameter 'capex_per_cap' which denotes the amount of
        CAPEX cost for the installation of one unit of capacity for that
        technology. This is an optional parameter with a default value of 0.

        :param s: Stage id
        :type s: StageId
        :param x: Technology id
        :type x: TechId
        :return: CAPEX cost per unit of installed technology [CHF/CAP]
        :rtype: float
        """
        self._check_id(x, ExceptionKey.CAPEXPERCAP_GET)
        return self._capex_per_cap.get((s, x), DEF_CAPEXPERCAP)

    def set_capex_per_cap(self, s: StageId, x: TechId, capex_per_cap: float) -> None:
        """
        Set the parameter 'capex_per_cap' which denotes the amount of
        CAPEX cost for the installation of one unit of capacity for that
        technology. This is an optional parameter with a default value of 0.

        :param s: Stage id
        :type s: StageId
        :param x: Technology id
        :type x: TechId
        :param capex_per_cap: CAPEX cost per unit of installed technology
            [CHF/CAP]
        :type capex_per_cap: float
        """
        self._check_id(x, ExceptionKey.CAPEXPERCAP_SET)
        self._capex_per_cap[s, x] = capex_per_cap

    # ----------------------- #
    # Property: one_time_opex #
    # ----------------------- #
    def get_one_time_opex(self, s: StageId, x: TechId) -> float:
        """
        Get the parameter 'one_time_opex' which denotes a fixed amount of
        OPEX cost that arises if a technology is used at all during a stage.
        This is an optional parameter with a default value of 0.

        :param s: Stage id
        :type s: StageId
        :param x: Technology id
        :type x: TechId
        :return: Fixed OPEX cost for used technology [CHF]
        :rtype: float
        """
        self._check_id(x, ExceptionKey.ONETIMEOPEX_GET)
        return self._one_time_opex.get((s, x), DEF_ONETIMEOPEX)

    def set_one_time_opex(self, s: StageId, x: TechId, one_time_opex: float) -> None:
        """
        Set the parameter 'one_time_opex' which denotes a fixed amount of
        OPEX cost that arises if a technology is used at all during a stage.
        This is an optional parameter with a default value of 0.

        :param s: Stage id
        :type s: StageId
        :param x: Technology id
        :type x: TechId
        :param one_time_opex: Fixed OPEX cost for used technology [CHF]
        :type one_time_opex: float
        """
        self._check_id(x, ExceptionKey.ONETIMEOPEX_SET)
        self._one_time_opex[s, x] = one_time_opex

    # ---------------------- #
    # Property: opex_per_cap #
    # ---------------------- #
    def get_opex_per_cap(self, s: StageId, x: TechId) -> float:
        """
        Get the parameter 'opex_per_cap' which denotes the amount of
        OPEX cost for each unit of installed technology, arising if the
        technology is used during a stage. This is an optional parameter with a
        default value of 0.

        :param s: Stage id
        :type s: StageId
        :param x: Technology id
        :type x: TechId
        :return: OPEX cost per unit of installed technology, if the technology
            is used during a stage [CHF/CAP]
        :rtype: float
        """
        self._check_id(x, ExceptionKey.OPEXPERCAP_GET)
        return self._opex_per_cap.get((s, x), DEF_OPEXPERCAP)

    def set_opex_per_cap(self, s: StageId, x: TechId, opex_per_cap: float) -> None:
        """
        Set the parameter 'opex_per_cap' which denotes the amount of
        OPEX cost for each unit of installed technology, arising if the
        technology is used during a stage. This is an optional parameter with a
        default value of 0.

        :param s: Stage id
        :type s: StageId
        :param x: Technology id
        :type x: TechId
        :param opex_per_cap: OPEX cost per unit of installed technology, if the
            technology is used during a stage [CHF/CAP]
        :type opex_per_cap: float
        """
        self._check_id(x, ExceptionKey.OPEXPERCAP_SET)
        self._opex_per_cap[s, x] = opex_per_cap

    # --------------------- #
    # Property: co2_per_cap #
    # --------------------- #
    def get_co2_per_cap(self, s: StageId, x: TechId) -> float:
        """
        Get the parameter 'co2_per_cap' which denotes the amount of embedded
        CO2 that arises for each unit of installed technology. This is an
        optional parameter with a default value of 0.

        :param s: Stage id
        :type s: StageId
        :param x: Technology id
        :type x: TechId
        :return: Embedded CO2 per unit of installed technology [kg/CAP]
        :rtype: float
        """
        self._check_id(x, ExceptionKey.CO2PERCAP_GET)
        return self._co2_per_cap.get((s, x), DEF_CO2PERCAP)

    def set_co2_per_cap(self, s: StageId, x: TechId, co2_per_cap: float) -> None:
        """
        Set the parameter 'co2_per_cap' which denotes the amount of embedded
        CO2 that arises for each unit of installed technology. This is an
        optional parameter with a default value of 0.

        :param s: Stage id
        :type s: StageId
        :param x: Technology id
        :type x: TechId
        :param co2_per_cap: Embedded CO2 per unit of installed technology
            [kg/CAP]
        :type co2_per_cap: float
        """
        self._check_id(x, ExceptionKey.CO2PERCAP_SET)
        self._co2_per_cap[s, x] = co2_per_cap

    # ------------------------- #
    # Property: last_instl_year #
    # ------------------------- #
    def get_last_instl_year(self, h: HubId, x: TechId) -> float:
        """
        Get the parameter 'last_instl_year' which denotes the last year in a
        hub when a technology is allowed to be installed. This is an optional
        parameter with a default value of infinity.

        :param h: Hub id
        :type h: HubId
        :param x: Technology id
        :type x: TechId
        :return: Last installation year for the technology in this hub [1]
        :rtype: float
        """
        self._check_id(x, ExceptionKey.LASTINSTLYEAR_GET)
        return self._last_instl_year.get((h, x), DEF_LASTINSTLYEAR)

    def set_last_instl_year(self, h: HubId, x: TechId, last_instl_year: float) -> None:
        """
        Set the parameter 'last_instl_year' which denotes the last year in a
        hub when a technology is allowed to be installed. This is an optional
        parameter with a default value of infinity.

        :param h: Hub id
        :type h: HubId
        :param x: Technology id
        :type x: TechId
        :param last_instl_year: Last installation year for the technology in
            this hub [1]
        :type last_instl_year: float
        """
        self._check_id(x, ExceptionKey.LASTINSTLYEAR_SET)
        self._last_instl_year[h, x] = last_instl_year

    # ------------------ #
    # Property: cap_init #
    # ------------------ #
    def get_cap_init(self, h: HubId, x: TechId) -> float:
        """
        Get the parameter 'cap_init' which denotes a technology's initial
        capacity that is present in a hub during the first stage, independent
        of potential installation choices. This is an optional parameter with a
        default value of 0.

        :param h: Hub id
        :type h: HubId
        :param x: Technology id
        :type x: TechId
        :return: Initial installed capacity [CAP]
        :rtype: float
        """
        self._check_id(x, ExceptionKey.CAPINIT_GET)
        return self._cap_init.get((h, x), DEF_CAPINIT)

    def set_cap_init(self, h: HubId, x: TechId, cap_init: float) -> None:
        """
        Set the parameter 'cap_init' which denotes a technology's initial
        capacity that is present in a hub during the first stage, independent
        of potential installation choices. This is an optional parameter with a
        default value of 0.

        :param h: Hub id
        :type h: HubId
        :param x: Technology id
        :type x: TechId
        :param cap_init: Initial installed capacity [CAP]
        :type cap_init: float
        """
        self._check_id(x, ExceptionKey.CAPINIT_SET)
        self._cap_init[h, x] = cap_init

    # ------------------ #
    # Property: age_init #
    # ------------------ #
    def get_age_init(self, h: HubId, x: TechId) -> float:
        """
        Get the parameter 'age_init' which denotes the age of a technology's
        initial installation (if any) that is present in a hub during the first
        stage, independent of potential installation choices. This is an
        optional parameter with a default value of 0.

        :param h: Hub id
        :type h: HubId
        :param x: Technology id
        :type x: TechId
        :return: Age of initial installation [a]
        :rtype: float
        """
        self._check_id(x, ExceptionKey.AGEINIT_GET)
        return self._age_init.get((h, x), DEF_AGEINIT)

    def set_age_init(self, h: HubId, x: TechId, age_init: float) -> None:
        """
        Set the parameter 'age_init' which denotes the age of a technology's
        initial installation (if any) that is present in a hub during the first
        stage, independent of potential installation choices. This is an
        optional parameter with a default value of 0.

        :param h: Hub id
        :type h: HubId
        :param x: Technology id
        :type x: TechId
        :param age_init: Age of initial installation [a]
        :type age_init: float
        """
        self._check_id(x, ExceptionKey.AGEINIT_SET)
        self._age_init[h, x] = age_init

    # ----------------- #
    # Property: cap_min #
    # ----------------- #
    def get_cap_min(self, s: StageId, h: HubId, x: TechId) -> float:
        """
        Get the parameter 'cap_min' which denotes the minimal amount of
        capacity that has to be achieved through a combination of installation
        and remaining initial capacity. This is an optional parameter with a
        default value of 0.

        :param s: Stage id
        :type s: StageId
        :param h: Hub id
        :type h: HubId
        :param x: Technology id
        :type x: TechId
        :return: Minimal capacity [CAP]
        :rtype: float
        """
        self._check_id(x, ExceptionKey.CAPMIN_GET)
        return self._cap_min.get((s, h, x), DEF_CAPMIN)

    def set_cap_min(self, s: StageId, h: HubId, x: TechId, cap_min: float) -> None:
        """
        Set the parameter 'cap_min' which denotes the minimal amount of
        capacity that has to be achieved through a combination of installation
        and remaining initial capacity. This is an optional parameter with a
        default value of 0.

        :param s: Stage id
        :type s: StageId
        :param h: Hub id
        :type h: HubId
        :param x: Technology id
        :type x: TechId
        :param cap_min: Minimal capacity [CAP]
        :type cap_min: float
        """
        self._check_id(x, ExceptionKey.CAPMIN_SET)
        self._cap_min[s, h, x] = cap_min

    # ----------------- #
    # Property: cap_max #
    # ----------------- #
    def get_cap_max(self, s: StageId, h: HubId, x: TechId) -> float:
        """
        Get the parameter 'cap_max' which denotes the maximal amount of
        capacity that is permitted for the combination of installation and
        remaining initial capacity. This is an optional parameter with a
        default value of infinity.

        :param s: Stage id
        :type s: StageId
        :param h: Hub id
        :type h: HubId
        :param x: Technology id
        :type x: TechId
        :return: Maximal capacity [CAP]
        :rtype: float
        """
        self._check_id(x, ExceptionKey.CAPMAX_GET)
        return self._cap_max.get((s, h, x), DEF_CAPMAX)

    def set_cap_max(self, s: StageId, h: HubId, x: TechId, cap_max: float) -> None:
        """
        Set the parameter 'cap_max' which denotes the maximal amount of
        capacity that is permitted for the combination of installation and
        remaining initial capacity. This is an optional parameter with a
        default value of infinity.

        :param s: Stage id
        :type s: StageId
        :param h: Hub id
        :type h: HubId
        :param x: Technology id
        :type x: TechId
        :param cap_max: Maximal capacity [CAP]
        :type cap_max: float
        """
        self._check_id(x, ExceptionKey.CAPMAX_SET)
        self._cap_max[s, h, x] = cap_max

    # ---------------------------- #
    # Property: coupled_main_techs #
    # ---------------------------- #
    @property
    def coupled_main_techs(self) -> Set[TechId]:
        """
        Set of all main technologies (i.e. all that are coupled to a
        sub-technology)
        """
        return set(self._coupled_main_tech.values())

    @property
    def coupled_sub_techs(self) -> Set[TechId]:
        """
        Set of all sub-technologies (i.e. all that are´coupled to a main
        technology)
        """
        return set(self._coupled_main_tech.keys())

    def is_coupled_main_tech(self, x: TechId) -> bool:
        """
        Whether a technology is a main technology (i.e. coupled to a
        sub-technology)

        :param x: Technology id
        :type x: TechId
        :return: Whether technology is a main technology
        :rtype: bool
        """
        self._check_id(x, ExceptionKey.COUPLEDMAINTECH_VAL)
        return x in self._coupled_main_tech.values()

    def is_coupled_sub_tech(self, x: TechId) -> bool:
        """
        Whether a technology is a sub-technology (i.e. coupled to a
        main technology)

        :param x: Technology id
        :type x: TechId
        :return: Whether technology is a sub-technology
        :rtype: bool
        """
        self._check_id(x, ExceptionKey.COUPLEDSUBTECH_VAL)
        return x in self._coupled_main_tech

    def get_coupled_main_tech(self, x: TechId) -> TechId:
        """
        Get the main technology of a sub-technology.

        :param x: Id of sub-technology
        :type x: TechId
        :return: Id of main technology
        :rtype: TechId
        """
        self._check_id(x, ExceptionKey.COUPLEDMAINTECH_GET)
        if x not in self._coupled_main_tech:
            raise exceptions.MissingIdException(
                ExceptionKey.COUPLEDMAINTECH_GET.value, x, module=LOG_MODULE_STR
            )
        return self._coupled_main_tech[x]

    def get_coupled_sub_techs(self, x: TechId) -> Set[TechId]:
        """
        Get the sub-technologies of a technology (possibly none)

        :param x: Technology id
        :type x: TechId
        :return: Set of sub-technology ids
        :rtype: Set[TechId]
        """
        self._check_id(x, ExceptionKey.COUPLEDSUBTECHS_GET)
        return {
            x_sub
            for x_sub, main_tech in self._coupled_main_tech.items()
            if main_tech == x
        }

    def set_coupled_main_tech(self, x_sub: TechId, x_main: TechId) -> None:
        """
        Set a technology to be a sub-technology of a main technology

        :param x_sub: Id of the technology to become a sub-technology
        :type x_sub: TechId
        :param x_main: Id of main technology
        :type x_main: TechId
        """
        self._check_id(x_sub, ExceptionKey.COUPLEDMAINTECH_SET)
        self._check_id(x_main, ExceptionKey.COUPLEDMAINTECH_SET)
        self._coupled_main_tech[x_sub] = x_main

    # ---------------------------- #
    # Property: coupled_cap_factor #
    # ---------------------------- #
    def get_coupled_cap_factor(self, x: TechId) -> float:
        """
        Get the parameter 'cap_factor' for a coupled sub-technology. This
        denotes the fraction of the sub-technology'scapacity in relation to the
        main technology’s capacity. This is a optional parameter for
        sub-technologies with a default value of 1.

        :param x: Id of sub-technology
        :type x: TechId
        :return: Fraction of sub-technology's capacity in relation to the main
            technology's capacity [1]
        :rtype: float
        """
        self._check_id(x, ExceptionKey.COUPLEDCAPFACTOR_GET)
        if x not in self._coupled_cap_factor:
            # Try automatic return:
            if self.is_coupled_sub_tech(x):
                return DEF_COUPLEDCAPFACTOR
            exc_key = ExceptionKey.COUPLEDCAPFACTOR_NOTASUB.value
            msg = (
                "Tried to get 'coupled_cap_factor' of ConversionTechs "
                + f"for {x.kind_as_str} id {x.key} which is not a "
                + "sub tech"
            )
            raise exceptions.DataException(exc_key, [x], msg, module=LOG_MODULE_STR)
        return self._coupled_cap_factor[x]

    def set_coupled_cap_factor(self, x: TechId, coupled_cap_factor: float) -> None:
        """
        Set the parameter 'cap_factor' for a coupled sub-technology. This
        denotes the fraction of the sub-technology'scapacity in relation to the
        main technology’s capacity. This is a optional parameter for
        sub-technologies with a default value of 1.

        :param x: Id of sub-technology
        :type x: TechId
        :param coupled_cap_factor: Fraction of sub-technology's capacity in
            relation to the main technology's capacity [1]
        :type coupled_cap_factor: float
        """
        self._check_id(x, ExceptionKey.COUPLEDCAPFACTOR_SET)
        self._coupled_cap_factor[x] = coupled_cap_factor

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._ids: Set[TechId] = set()
        self._allowed_stages: Dict[TechId, Set[StageId]] = {}
        self._allowed_hubs: Dict[TechId, Set[HubId]] = {}
        self._lifetime: Dict[TechId, int] = {}
        self._interest_rate: Dict[TechId, float] = {}
        self._unit_cap_min: Dict[Tuple[StageId, TechId], float] = {}
        self._one_time_capex: Dict[Tuple[StageId, TechId], float] = {}
        self._capex_per_cap: Dict[Tuple[StageId, TechId], float] = {}
        self._one_time_opex: Dict[Tuple[StageId, TechId], float] = {}
        self._opex_per_cap: Dict[Tuple[StageId, TechId], float] = {}
        self._co2_per_cap: Dict[Tuple[StageId, TechId], float] = {}
        self._last_instl_year: Dict[Tuple[HubId, TechId], float] = {}
        self._cap_init: Dict[Tuple[HubId, TechId], float] = {}
        self._age_init: Dict[Tuple[HubId, TechId], float] = {}
        self._cap_min: Dict[Tuple[StageId, HubId, TechId], float] = {}
        self._cap_max: Dict[Tuple[StageId, HubId, TechId], float] = {}
        self._coupled_main_tech: Dict[TechId, TechId] = {}
        self._coupled_cap_factor: Dict[TechId, float] = {}

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self, stages: Stages, hubs: Hubs) -> None:
        """
        Validate all technology data in this object. Apart from sense-checking
        parameter in terms of quantity, this includes checking whether
        the ids from other data classes used here are known there as well.

        :param stages: Stages data class
        :type stages: Stages
        :param hubs: Hubs data class
        :type hubs: Hubs
        """
        self._validate_lifetime()
        self._validate_allowed_stages(stages)
        self._validate_allowed_hubs(hubs)
        self._validate_interest_rate()
        self._validate_unit_cap_min(stages)
        self._validate_one_time_capex(stages)
        self._validate_capex_per_cap(stages)
        self._validate_one_time_opex(stages)
        self._validate_opex_per_cap(stages)
        self._validate_co2_per_cap(stages)
        self._validate_last_instl_year(stages, hubs)
        self._validate_cap_init(hubs)
        self._validate_age_init(hubs)
        self._validate_cap_min(stages, hubs)
        self._validate_cap_max(stages, hubs)
        self._validate_coupled_main_tech()
        self._validate_coupled_cap_factor()

    def _validate_lifetime(self) -> None:
        for x, lifetime in self._lifetime.items():
            # Lifetime has to be positive
            if lifetime <= 0:
                msg = f"{lifetime} = lifetime[{x}] <= 0"
                raise exceptions.DataException(
                    ExceptionKey.LIFETIME_VAL.value, [x], msg, module=LOG_MODULE_STR
                )

    def _validate_allowed_stages(self, stages: Stages) -> None:
        exc_key = ExceptionKey.ALLOWEDSTAGES_VAL.value
        for x, allowed_stages in self._allowed_stages.items():
            for s in allowed_stages:
                # Unknown stage
                if s not in stages.ids:
                    msg = f"Unknown stage {s} in allowed_stages[{x}]"
                    raise exceptions.DataException(
                        exc_key, [s, x], msg, module=LOG_MODULE_STR
                    )
        # Identify techs that are allowed nowhere
        for x in self.ids:
            if not self.get_allowed_stages(x):
                msg = f"{x} is not allowed in any stage (due to TRL)"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_allowed_hubs(self, hubs: Hubs) -> None:
        exc_key = ExceptionKey.ALLOWEDHUBS_VAL.value
        for x, allowed_hubs in self._allowed_hubs.items():
            for h in allowed_hubs:
                # Unknown hub
                if h not in hubs.ids:
                    msg = f"Unknown hub {h} in allowed_hubs[{x}]"
                    raise exceptions.DataException(
                        exc_key, [h, x], msg, module=LOG_MODULE_STR
                    )
        # Identify techs that are allowed nowhere
        for x in self.ids:
            if not self.get_allowed_hubs(x):
                msg = f"{x} is not allowed in any hub (due to allowed_tech_lists)"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_interest_rate(self) -> None:
        for x, interest_rate in self._interest_rate.items():
            # Interest rate has to be nonpositive
            if interest_rate < 0:
                msg = f"{interest_rate} = interest_rate[{x}] < 0"
                raise exceptions.DataException(
                    ExceptionKey.INTERESTRATE_VAL.value, [x], msg, module=LOG_MODULE_STR
                )

    def _validate_unit_cap_min(self, stages: Stages) -> None:
        exc_key = ExceptionKey.UNITCAPMIN_VAL.value
        for (s, x), unit_cap_min in self._unit_cap_min.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in unit_cap_min[{s}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # unit_cap_min has to be nonnegative
            if unit_cap_min < 0:
                msg = f"{unit_cap_min} = unit_cap_min[{s}, {x}] < 0"
                raise exceptions.DataException(
                    ExceptionKey.UNITCAPMIN_VAL.value,
                    [s, x],
                    msg,
                    module=LOG_MODULE_STR,
                )

    def _validate_one_time_capex(self, stages: Stages) -> None:
        exc_key = ExceptionKey.ONETIMECAPEX_VAL.value
        for (s, x), one_time_capex in self._one_time_capex.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in one_time_capex[{s}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # one_time_capex usually nonnegative
            if one_time_capex < 0:
                msg = f"{one_time_capex} = one_time_capex[{s}, {x}] < 0"
                logging.log_warning(msg, LOG_MODULE_STR)

    def _validate_capex_per_cap(self, stages: Stages) -> None:
        exc_key = ExceptionKey.CAPEXPERCAP_VAL.value
        for (s, x), capex_per_cap in self._capex_per_cap.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in capex_per_cap[{s}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # capex_per_cap usually nonnegative
            if capex_per_cap < 0:
                msg = f"{capex_per_cap} = capex_per_cap[{s}, {x}] < 0"
                logging.log_warning(msg, LOG_MODULE_STR)

    def _validate_one_time_opex(self, stages: Stages) -> None:
        exc_key = ExceptionKey.ONETIMEOPEX_VAL.value
        for (s, x), one_time_opex in self._one_time_opex.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in one_time_opex[{s}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # one_time_opex usually nonnegative
            if one_time_opex < 0:
                msg = f"{one_time_opex} = one_time_opex[{s}, {x}] < 0"
                logging.log_warning(msg, LOG_MODULE_STR)

    def _validate_opex_per_cap(self, stages: Stages) -> None:
        exc_key = ExceptionKey.OPEXPERCAP_VAL.value
        for (s, x), opex_per_cap in self._opex_per_cap.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in opex_per_cap[{s}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # opex_per_cap usually nonnegative
            if opex_per_cap < 0:
                msg = f"{opex_per_cap} = opex_per_cap[{s}, {x}] < 0"
                logging.log_warning(msg, LOG_MODULE_STR)

    def _validate_co2_per_cap(self, stages: Stages) -> None:
        exc_key = ExceptionKey.CO2PERCAP_VAL.value
        for (s, x), co2_per_cap in self._co2_per_cap.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in co2_per_cap[{s}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # co2_per_cap usually nonnegative
            if co2_per_cap < 0:
                msg = f"{co2_per_cap} = co2_per_cap[{s}, {x}] < 0"
                logging.log_warning(msg, LOG_MODULE_STR)

    def _validate_cap_init(self, hubs: Hubs) -> None:
        exc_key = ExceptionKey.CAPINIT_VAL.value
        for (h, x), cap_init in self._cap_init.items():
            # Unknown hub
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in cap_init[{h}, {x}]"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)
            # cap_init must be nonnegative
            if cap_init < 0:
                msg = f"{cap_init} = cap_init[{h}, {x}] < 0"
                raise exceptions.DataException(
                    exc_key, [h, x], msg, module=LOG_MODULE_STR
                )

    def _validate_age_init(self, hubs: Hubs) -> None:
        exc_key = ExceptionKey.AGEINIT_VAL.value
        for (h, x), age_init in self._age_init.items():
            # Unknown hub
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in age_init[{h}, {x}]"
                raise exceptions.DataException(exc_key, [h], msg, module=LOG_MODULE_STR)
            # age_init must be nonnegative
            if age_init < 0:
                msg = f"{age_init} = age_init[{h}, {x}] < 0"
                raise exceptions.DataException(
                    exc_key, [h, x], msg, module=LOG_MODULE_STR
                )
            # age_init usually smaller than lifetime
            lifetime = self.get_lifetime(x)
            if age_init >= lifetime:
                msg = f"{age_init} = age_init[{h}, {x}] >= lifetime[{x}] = {lifetime}"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_cap_min(self, stages: Stages, hubs: Hubs) -> None:
        # self.set_cap_min(StageId("S1"), HubId("H1"), TechId("X1"), -1)
        exc_key = ExceptionKey.CAPMIN_VAL.value
        for (s, h, x), cap_min in self._cap_min.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in cap_min[{s}, {h}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, h, x], msg, module=LOG_MODULE_STR
                )
            # Unknown hub
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in cap_min[{s}, {h}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, h, x], msg, module=LOG_MODULE_STR
                )
            # cap_min usually nonnegative
            if cap_min < 0:
                msg = f"{cap_min} = cap_min[{s}, {h}, {x}] < 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_capmin_allowedhubs(self) -> None:
        exc_key = ExceptionKey.CAPMINALLOWEDHUBS_VAL.value
        for (s, h, x), cap_min in self._cap_min.items():
            # Check only makes sense for nonzero minimal capacity
            if cap_min < common.EPS_ZEROCHECK:
                continue
            # Cannot satisfy minimal capacity if tech is not allowed
            if h not in self.get_allowed_hubs(x):
                msg = (
                    f"0 < {cap_min} = cap_min[{s}, {h}, {x}] but {x} is "
                    f"not allowed in {h}"
                )
                raise exceptions.DataException(
                    exc_key, [s, h, x], msg, module=LOG_MODULE_STR
                )

    def _validate_cap_max(self, stages: Stages, hubs: Hubs) -> None:
        exc_key = ExceptionKey.CAPMAX_VAL.value
        for (s, h, x), cap_max in self._cap_max.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in cap_max[{s}, {h}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, h, x], msg, module=LOG_MODULE_STR
                )
            # Unknown hub
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in cap_max[{s}, {h}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, h, x], msg, module=LOG_MODULE_STR
                )
            # cap_max must be nonnegative
            if cap_max < 0:
                msg = f"{cap_max} = cap_max[{s}, {h}, {x}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, h, x], msg, module=LOG_MODULE_STR
                )

    def _validate_last_instl_year(self, stages: Stages, hubs: Hubs) -> None:
        exc_key = ExceptionKey.LASTINSTLYEAR_VAL.value
        init_stage = stages.init_stage
        init_year = stages.init_year
        for (h, x), year in self._last_instl_year.items():
            # Unknown hub
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in last_instl_year[{h}, {x}]"
                raise exceptions.DataException(
                    exc_key, [h, x], msg, module=LOG_MODULE_STR
                )
            # last_instl_year earlier than start year
            if year < init_year:
                msg = (
                    f"{year} = last_instl_year[{x}] < "
                    f"start_year[{init_stage}] = {init_year} "
                    "which is the initial stage year"
                )
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_coupled_main_tech(self) -> None:
        exc_key = ExceptionKey.COUPLEDMAINTECH_VAL.value
        # Techs must not be subs and mains at the same time
        for x in self.coupled_main_techs.intersection(self.coupled_sub_techs):
            subs = self.get_coupled_sub_techs(x)
            main = self.get_coupled_main_tech(x)
            msg = (
                f"{x} is coupled main tech with sub techs {subs}. But it "
                f"is also a sub tech with main tech {main}"
            )
            raise exceptions.DataException(exc_key, [x], msg, module=LOG_MODULE_STR)

    def _validate_coupled_cap_factor(self) -> None:
        exc_key = ExceptionKey.COUPLEDCAPFACTOR_VAL.value
        for x, coupled_cap_factor in self._coupled_cap_factor.items():
            # Only sub techs get coupled_cap_factor values
            if not self.is_coupled_sub_tech(x):
                msg = f"{x} in coupled_cap_factor[{x}] is not a sub tech"
                raise exceptions.DataException(exc_key, [x], msg, module=LOG_MODULE_STR)
            # coupled_cap_factor values have to be nonnegative
            if coupled_cap_factor < 0:
                msg = f"{coupled_cap_factor} = coupled_cap_factor[{x}] < 0"
                raise exceptions.DataException(exc_key, [x], msg, module=LOG_MODULE_STR)
            # coupled_cap_factor values usually positive
            if coupled_cap_factor < common.EPS_ZEROCHECK:
                msg = f"{coupled_cap_factor} = coupled_cap_factor[{x}] ~ 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    # ---------- #
    # Id checker #
    # ---------- #
    def _check_id(self, x: TechId, where: ExceptionKey) -> None:
        if x not in self._ids:
            raise exceptions.UnknownIdException(where.value, x, module=LOG_MODULE_STR)


def copy_over_tech(
    x: TechId, src: Techs, tar: Techs, stages: Stages, hubs: Hubs
) -> None:
    """
    Copy a technology from one Techs data object to another

    :param x: Technology id to be copied
    :type x: TechId
    :param src: Source data object
    :type src: Techs
    :param tar: Target data object
    :type tar: Techs
    :param stages: Stages
    :type stages: Stages
    :param hubs: Hubs
    :type hubs: Hubs
    """
    # id
    if x not in src.ids:
        raise exceptions.DataException(
            ExceptionKey.COPYOVERTECH.value,
            [x],
            (
                f"Failed to copy tech {x} from Techs instance because {x} is "
                "not part of that Techs instance"
            ),
            module=LOG_MODULE_STR,
        )
    if x in tar.ids:
        raise exceptions.DataException(
            ExceptionKey.COPYOVERTECH.value,
            [x],
            (
                f"Failed to copy tech {x} to Techs instance because {x} is "
                "already part of that Techs instance"
            ),
            module=LOG_MODULE_STR,
        )
    tar.add_id(x)
    # Allowed stages & hubs
    for s in src.get_allowed_stages(x):
        tar.add_allowed_stage(s, x)
    for h in src.get_allowed_hubs(x):
        tar.add_allowed_hub(h, x)
    # Scalar attributes
    tar.set_lifetime(x, src.get_lifetime(x))
    tar.set_interest_rate(x, src.get_interest_rate(x))
    # Stage-dependent attributes
    for s in stages.ids:
        tar.set_unit_cap_min(s, x, src.get_unit_cap_min(s, x))
        tar.set_one_time_capex(s, x, src.get_one_time_capex(s, x))
        tar.set_capex_per_cap(s, x, src.get_capex_per_cap(s, x))
        tar.set_one_time_opex(s, x, src.get_one_time_opex(s, x))
        tar.set_opex_per_cap(s, x, src.get_opex_per_cap(s, x))
        tar.set_co2_per_cap(s, x, src.get_co2_per_cap(s, x))
    # Hub-dependent attributes
    for h in hubs.ids:
        tar.set_last_instl_year(h, x, src.get_last_instl_year(h, x))
        tar.set_cap_init(h, x, src.get_cap_init(h, x))
        tar.set_age_init(h, x, src.get_age_init(h, x))
    # Stage-hub-dependent attributes
    for s in stages.ids:
        for h in hubs.ids:
            tar.set_cap_min(s, h, x, src.get_cap_min(s, h, x))
            tar.set_cap_max(s, h, x, src.get_cap_max(s, h, x))
    # Coupled attributes
    if x in src.coupled_sub_techs:
        x_main = src.get_coupled_main_tech(x)
        if x_main not in tar.ids:
            copy_over_tech(x_main, src, tar, stages, hubs)
        tar.set_coupled_main_tech(x, x_main)
        tar.set_coupled_cap_factor(x, src.get_coupled_cap_factor(x))
