"""
Network technology data module
"""

from enum import Enum
from typing import Dict, List, Set, Tuple

from ehubx.core import logging
from ehubx.data import exceptions
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.index import Index, IndexKind
from ehubx.data.net_link_data import NetLinkId, NetworkLinks
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.unit import (
    CurrencyUnit,
    DimlessUnit,
    LengthUnit,
    MassUnit,
    TimeUnit,
    Unit,
)
from ehubx.data.value import Value


class NetTechId(Index):
    """
    Network technology index
    """

    def __init__(self, key: str) -> None:
        super().__init__(IndexKind.NETTECH, key)


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the network technology
    data module
    """

    ID_ADD = "adding to 'ids' of NetworkTechs"
    ID_REMOVE = "removing from 'ids' of NetworkTechs"
    EC_SET = "setting 'ec' of NetworkTechs"
    EC_GET = "getting 'ec' from NetworkTechs"
    EC_VAL = "validating 'ec' of NetworkTechs"
    LIFETIME_SET = "setting 'lifetime' of NetworkTechs"
    LIFETIME_GET = "getting 'lifetime' from NetworkTechs"
    LIFETIME_VAL = "validating 'lifetime' of NetworkTechs"
    INTERESTRATE_SET = "setting 'interest_rate' of NetworkTechs"
    INTERESTRATE_GET = "getting 'interest_rate' from NetworkTechs"
    INTERESTRATE_VAL = "validating 'interest_rate' of NetworkTechs"
    UNITCAPMIN_SET = "setting 'unit_cap_min' of NetworkTechs"
    UNITCAPMIN_GET = "getting 'unit_cap_min' from NetworkTechs"
    UNITCAPMIN_VAL = "validating 'unit_cap_min' of NetworkTechs"
    ONETIMECAPEX_SET = "setting 'one_time_capex' of NetworkTechs"
    ONETIMECAPEX_GET = "getting 'one_time_capex' from NetworkTechs"
    ONETIMECAPEX_VAL = "validating 'one_time_capex' of NetworkTechs"
    CAPEXPERCAP_SET = "setting 'capex_per_cap' of NetworkTechs"
    CAPEXPERCAP_GET = "getting 'capex_per_cap' from NetworkTechs"
    CAPEXPERCAP_VAL = "validating 'capex_per_cap' of NetworkTechs"
    ONETIMEOPEX_SET = "setting 'one_time_opex' of NetworkTechs"
    ONETIMEOPEX_GET = "getting 'one_time_opex' from NetworkTechs"
    ONETIMEOPEX_VAL = "validating 'one_time_opex' of NetworkTechs"
    OPEXPERCAP_SET = "setting 'opex_per_cap' of NetworkTechs"
    OPEXPERCAP_GET = "getting 'opex_per_cap' from NetworkTechs"
    OPEXPERCAP_VAL = "validating 'opex_per_cap' of NetworkTechs"
    OPEXPERENERGY_SET = "setting 'opex_per_energy' of NetworkTechs"
    OPEXPERENERGY_GET = "getting 'opex_per_energy' from NetworkTechs"
    OPEXPERENERGY_VAL = "validating 'opex_per_energy' of NetworkTechs"
    CO2PERCAP_SET = "setting 'co2_per_cap' of NetworkTechs"
    CO2PERCAP_GET = "getting 'co2_per_cap' from NetworkTechs"
    CO2PERCAP_VAL = "validating 'co2_per_cap' of NetworkTechs"
    CO2PERENERGY_SET = "setting 'co2_per_energy' of NetworkTechs"
    CO2PERENERGY_GET = "getting 'co2_per_energy' from NetworkTechs"
    CO2PERENERGY_VAL = "validating 'co2_per_energy' of NetworkTechs"
    TRANSDECAY_SET = "setting 'trans_decay' of NetworkTechs"
    TRANSDECAY_GET = "getting 'trans_decay' from NetworkTechs"
    TRANSDECAY_VAL = "validating 'trans_decay' of NetworkTechs"
    CAPINIT_SET = "setting 'cap_init' of NetworkTechs"
    CAPINIT_GET = "getting 'cap_init' from NetworkTechs"
    CAPINIT_VAL = "validating 'cap_init' of NetworkTechs"
    AGEINIT_SET = "setting 'age_init' of NetworkTechs"
    AGEINIT_GET = "getting 'cap_init' from NetworkTechs"
    AGEINIT_VAL = "validating 'age_init' of NetworkTechs"
    ALLOWEDSTAGES_ADD = "adding to 'allowed_stages' in NetworkTechs"
    ALLOWEDSTAGES_REMOVE = "removing from 'allowed_stages' in NetworkTechs"
    ALLOWEDSTAGES_VAL = "validating 'allowed_stages' of NetworkTechs"
    ALLOWEDNETLINKS_ADD = "adding to 'allowed_net_links' in NetworkTechs"
    ALLOWEDNETLINKS_REMOVE = "removing from 'allowed_net_links' in NetworkTechs"
    ALLOWEDNETLINKS_VAL = "validating 'allowed_net_links' of NetworkTechs"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/net_tech"
"""String identifying the network technology data module for logging
purposes"""

DEF_UNITCAPMIN: float = 0
"""Default value for parameter 'unit_cap_min' in the network technology data
module"""

DEF_ONETIMECAPEX: float = 0
"""Default value for parameter 'one_time_capex' in the network technology data
module"""

DEF_CAPEXPERCAP: float = 0
"""Default value for parameter 'capex_per_cap' in the network technology data
module"""

DEF_ONETIMEOPEX: float = 0
"""Default value for parameter 'one_time_opex' in the network technology data
module"""

DEF_OPEXPERCAP: float = 0
"""Default value for parameter 'opex_per_cap' in the network technology data
module"""

DEF_OPEXPERENERGY: float = 0
"""Default value for parameter 'opex_per_energy' in the network technology data
module"""

DEF_CO2PERCAP: float = 0
"""Default value for parameter 'co2_per_cap' in the network technology data
module"""

DEF_CO2PERENERGY: float = 0
"""Default value for parameter 'co2_per_energy' in the network technology data
module"""

DEF_TRANSDECAY: float = 0
"""Default value for parameter 'trans_decay' in the network technology data module"""

DEF_CAPINIT: float = 0
"""Default value for parameter 'cap_init' in the network technology data
module"""

DEF_AGEINIT: float = 0
"""Default value for parameter 'age_init' in the network technology data
module"""


class NetworkTechs:
    """
    Class for network technology data. Manages network technology ids, contains
    getters and setters for network technology parameters and validation
    methods to control data integrity
    """

    # ------------- #
    # Property: ids #
    # ------------- #
    @property
    def ids(self) -> Set[NetTechId]:
        """
        Set of known network technology ids
        """
        return self._ids

    @property
    def ids_in_order(self) -> List[NetTechId]:
        """
        List of known network tech ids in alphabetical order
        """
        ids = list(self.ids)
        ids.sort(key=lambda n: n.key)
        return ids

    def add_id(self, n: NetTechId) -> None:
        """
        Add a new network technology id

        :param n: Id to be added
        :type n: NetTechId
        """
        if n in self._ids:
            raise exceptions.DuplicateIdException(
                ExceptionKey.ID_ADD.value, n, module=LOG_MODULE_STR
            )
        self._ids.add(n)

    # ------------ #
    # Property: ec #
    # ------------ #
    def get_ec(self, n: NetTechId) -> EcId:
        """
        Get the ec that can be transported in the network technology. This is
        a mandatory parameter.

        :param n: Network technology
        :type n: NetTechId
        :return: ec
        :rtype: EcId
        """
        self._check_id(n, ExceptionKey.EC_GET)
        ec = self._ec.get(n, None)
        if ec is None:
            raise exceptions.MissingIdException(
                ExceptionKey.EC_GET.value, n, module=LOG_MODULE_STR
            )
        return ec

    def set_ec(self, n: NetTechId, ec: EcId, ec_unit: Unit) -> None:
        """
        Set the ec that can be transported in the network technology. This is
        a mandatory parameter that needs to be set before most other parameters.

        :param n: Network technology
        :type n: NetTechId
        :param ec: ec
        :type ec: EcId
        :param ec_unit: Unit of the ec
        :type ec_unit: Unit
        """
        self._check_id(n, ExceptionKey.EC_SET)
        self._ec[n] = ec
        self._unit_cap_min_def[n] = Value(DEF_UNITCAPMIN, ec_unit / TimeUnit.H)
        self._capex_per_cap_def[n] = Value(
            DEF_CAPEXPERCAP, CurrencyUnit.CHF / ((ec_unit / TimeUnit.H) * LengthUnit.M)
        )
        self._opex_per_cap_def[n] = Value(
            DEF_OPEXPERCAP, CurrencyUnit.CHF / ((ec_unit / TimeUnit.H) * LengthUnit.M)
        )
        self._opex_per_energy_def[n] = Value(
            DEF_OPEXPERENERGY,
            (CurrencyUnit.CHF / (ec_unit * LengthUnit.M)),
        )
        self._co2_per_cap_def[n] = Value(
            DEF_CO2PERCAP, MassUnit.KG / ((ec_unit / TimeUnit.H) * LengthUnit.M)
        )
        self._co2_per_energy_def[n] = Value(
            DEF_CO2PERENERGY, (MassUnit.KG / (ec_unit * LengthUnit.M))
        )
        self._cap_init_def[n] = Value(DEF_CAPINIT, ec_unit / TimeUnit.H)

    # ------------------ #
    # Property: lifetime #
    # ------------------ #
    def get_lifetime(self, n: NetTechId) -> Value:
        """
        Get the parameter 'lifetime' of a network technology. From the moment
        they are installed, network technologies can operate and will stay
        installed until they have reached their end of life. Initially
        installed network technologies remain operational based on their
        initial age and lifetime. This is a mandatory parameter.

        :param n: Network technology.
        :type n: NetTechId
        :return: Lifetime
        :rtype: Value
        """
        self._check_id(n, ExceptionKey.LIFETIME_GET)
        lifetime = self._lifetime.get(n, None)
        if lifetime is None:
            raise exceptions.MissingIdException(
                ExceptionKey.LIFETIME_GET.value, n, module=LOG_MODULE_STR
            )
        return lifetime

    def set_lifetime(self, n: NetTechId, lifetime: Value) -> None:
        """
        Set the parameter 'lifetime' of a network technology. From the moment
        they are installed, network technologies can operate and will stay
        installed until they have reached their end of life. Initially
        installed network technologies remain operational based on their
        initial age and lifetime. This is a mandatory parameter.

        :param n: Network technology.
        :type n: NetTechId
        :param lifetime: Lifetime [a]
        :type lifetime: float
        """
        self._check_id(n, ExceptionKey.LIFETIME_SET)
        expected_unit = TimeUnit.A
        if not lifetime.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.LIFETIME_SET.value,
                [n],
                f"Unit {lifetime.unit} of lifetime[{n}] "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._lifetime[n] = lifetime

    # ----------------------- #
    # Property: interest_rate #
    # ----------------------- #
    def get_interest_rate(self, n: NetTechId) -> Value:
        """
        Get the parameter 'interest_rate' of a network technology which is used
        to calculate yearly annuity payments for CAPEX investments. For the
        network technology data class, interest rate is a mandatory parameter
        but it may be left blank in the input data, leaving the parser to set
        the default interest rate

        :param n: Network technology
        :type n: NetTechId
        :return: Interest rate
        :rtype: Value
        """
        self._check_id(n, ExceptionKey.INTERESTRATE_GET)
        interest_rate = self._interest_rate.get(n, None)
        if interest_rate is None:
            raise exceptions.MissingIdException(
                ExceptionKey.INTERESTRATE_GET.value, n, module=LOG_MODULE_STR
            )
        return interest_rate

    def set_interest_rate(self, n: NetTechId, interest_rate: Value) -> None:
        """
        Set the parameter 'interest_rate' of a network technology which is used
        to calculate yearly annuity payments for CAPEX investments. For the
        network technology data class, interest rate is a mandatory parameter
        but it may be left blank in the input data, leaving the parser to set
        the default interest rate

        :param n: Network technology
        :type n: NetTechId
        :param interest_rate: Interest rate
        :type interest_rate: Value
        """
        self._check_id(n, ExceptionKey.INTERESTRATE_SET)
        expected_unit = DimlessUnit()
        if not interest_rate.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.INTERESTRATE_SET.value,
                [n],
                f"Unit {interest_rate.unit} of interest_rate[{n}] "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._interest_rate[n] = interest_rate

    # ---------------------- #
    # Property: unit_cap_min #
    # ---------------------- #
    def get_unit_cap_min(self, s: StageId, n: NetTechId) -> Value:
        """
        Get the parameter 'unit_cap_min' which denotes the minimal amount of
        network technology capacity that has to be installed of a technology if
        any installation occurs at all. This is an optional parameter with a
        default value of 0.

        :param s: Stage
        :type s: StageId
        :param n: Network technology
        :type n: NetTechId
        :return: Minimal amount of installable network technology capacity
        :rtype: Value
        """
        self._check_id(n, ExceptionKey.UNITCAPMIN_GET)
        return self._unit_cap_min.get((s, n), self._unit_cap_min_def[n])

    def set_unit_cap_min(self, s: StageId, n: NetTechId, unit_cap_min: Value) -> None:
        """
        Set the parameter 'unit_cap_min' which denotes the minimal amount of
        network technology capacity that has to be installed of a technology if
        any installation occurs at all. This is an optional parameter with a
        default value of 0.

        :param s: Stage
        :type s: StageId
        :param n: Network technology
        :type n: NetTechId
        :param unit_cap_min: Minimal amount of installable network technology capacity
        :type unit_cap_min: Value
        """
        self._check_id(n, ExceptionKey.UNITCAPMIN_SET)
        if not unit_cap_min.same_unit_type_as(self._unit_cap_min_def[n]):
            raise exceptions.DataException(
                ExceptionKey.UNITCAPMIN_SET.value,
                [s, n],
                f"Unit {unit_cap_min.unit} of unit_cap_min[{s}, {n}] "
                f"does not match expected unit {self._unit_cap_min_def[n].unit}",
                module=LOG_MODULE_STR,
            )
        self._unit_cap_min[s, n] = unit_cap_min

    # ------------------------ #
    # Property: one_time_capex #
    # ------------------------ #
    def get_one_time_capex(self, s: StageId, n: NetTechId) -> Value:
        """
        Get the parameter 'one_time_capex' which denotes a fixed amount of
        CAPEX cost per link length that occurs if any amount of capacity is
        installed for this network technology. This is an optional parameter
        with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param n: Network technology
        :type n: NetTechId
        :return: Fixed CAPEX cost per link length for installed network technology
        :rtype: float
        """
        self._check_id(n, ExceptionKey.ONETIMECAPEX_GET)
        return self._one_time_capex.get(
            (s, n), Value(DEF_ONETIMECAPEX, CurrencyUnit.CHF / LengthUnit.M)
        )

    def set_one_time_capex(
        self, s: StageId, n: NetTechId, one_time_capex: Value
    ) -> None:
        """
        Set the parameter 'one_time_capex' which denotes a fixed amount of
        CAPEX cost per link length that occurs if any amount of capacity is
        installed for this network technology. This is an optional parameter
        with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param n: Network technology
        :type n: NetTechId
        :param one_time_capex: Fixed CAPEX cost per link length for installed
            network technology
        :type one_time_capex: Value
        """
        self._check_id(n, ExceptionKey.ONETIMECAPEX_SET)
        expected_unit = CurrencyUnit.CHF / LengthUnit.M
        if not one_time_capex.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.ONETIMECAPEX_SET.value,
                [s, n],
                f"Unit {one_time_capex.unit} of one_time_capex[{s}, {n}] "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._one_time_capex[s, n] = one_time_capex

    # ----------------------- #
    # Property: capex_per_cap #
    # ----------------------- #
    def get_capex_per_cap(self, s: StageId, n: NetTechId) -> Value:
        """
        Get the parameter 'capex_per_cap' which denotes the amount of
        CAPEX cost per link length for the installation of one unit of capacity
        for that network technology. This is an optional parameter with a
        default value of 0.

        :param s: Stage
        :type s: StageId
        :param n: Network technology
        :type n: NetTechId
        :return: CAPEX cost per link length per unit of installed network
            technology
        :rtype: Value
        """
        self._check_id(n, ExceptionKey.CAPEXPERCAP_GET)
        return self._capex_per_cap.get((s, n), self._capex_per_cap_def[n])

    def set_capex_per_cap(self, s: StageId, n: NetTechId, capex_per_cap: Value) -> None:
        """
        Set the parameter 'capex_per_cap' which denotes the amount of
        CAPEX cost per link length for the installation of one unit of capacity
        for that network technology. This is an optional parameter with a
        default value of 0.

        :param s: Stage
        :type s: StageId
        :param n: Network technology
        :type n: NetTechId
        :param capex_per_cap: CAPEX cost per link length per unit of installed
            network technology
        :type capex_per_cap: float
        """
        self._check_id(n, ExceptionKey.CAPEXPERCAP_SET)
        expected_unit = self._capex_per_cap_def[n].unit
        if not capex_per_cap.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.CAPEXPERCAP_SET.value,
                [s, n],
                f"Unit {capex_per_cap.unit} of capex_per_cap[{s}, {n}] "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._capex_per_cap[s, n] = capex_per_cap

    # ----------------------- #
    # Property: one_time_opex #
    # ----------------------- #
    def get_one_time_opex(self, s: StageId, n: NetTechId) -> Value:
        """
        Get the parameter 'one_time_opex' which denotes a fixed amount of
        OPEX cost per link length that arises if a network technology is used
        at all during a stage. This is an optional parameter with a default
        value of 0.

        :param s: Stage
        :type s: StageId
        :param n: Network technology
        :type n: NetTechId
        :return: Fixed OPEX cost per link length for used network technology
        :rtype: Value
        """
        self._check_id(n, ExceptionKey.ONETIMEOPEX_GET)
        return self._one_time_opex.get(
            (s, n), Value(DEF_ONETIMEOPEX, CurrencyUnit.CHF / LengthUnit.M)
        )

    def set_one_time_opex(self, s: StageId, n: NetTechId, one_time_opex: Value) -> None:
        """
        Set the parameter 'one_time_opex' which denotes a fixed amount of
        OPEX cost per link length that arises if a network technology is used
        at all during a stage. This is an optional parameter with a default
        value of 0.

        :param s: Stage
        :type s: StageId
        :param n: Network technology
        :type n: NetTechId
        :param one_time_opex: Fixed OPEX cost per link length for used network
            technology
        :type one_time_opex: Value
        """
        self._check_id(n, ExceptionKey.ONETIMEOPEX_SET)
        expected_unit = CurrencyUnit.CHF / LengthUnit.M
        if not one_time_opex.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.ONETIMEOPEX_SET.value,
                [s, n],
                f"Unit {one_time_opex.unit} of one_time_opex[{s}, {n}] "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._one_time_opex[s, n] = one_time_opex

    # ---------------------- #
    # Property: opex_per_cap #
    # ---------------------- #
    def get_opex_per_cap(self, s: StageId, n: NetTechId) -> Value:
        """
        Get the parameter 'opex_per_cap' which denotes the amount of
        OPEX cost per link length for each unit of installed network
        technology, arising if the technology is used during a stage. This is
        an optional parameter with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param n: Network technology
        :type n: NetTechId
        :return: OPEX cost per link length per unit of installed network
            technology, if the technology is used during a stage
        :rtype: Value
        """
        self._check_id(n, ExceptionKey.OPEXPERCAP_GET)
        return self._opex_per_cap.get((s, n), self._opex_per_cap_def[n])

    def set_opex_per_cap(self, s: StageId, n: NetTechId, opex_per_cap: Value) -> None:
        """
        Set the parameter 'opex_per_cap' which denotes the amount of
        OPEX cost per link length for each unit of installed network
        technology, arising if the technology is used during a stage. This is
        an optional parameter with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param n: Network technology
        :type n: NetTechId
        :param opex_per_cap: OPEX cost per link length per unit of installed
            network technology, if the technology is used during a stage
        :type opex_per_cap: Value
        """
        self._check_id(n, ExceptionKey.OPEXPERCAP_SET)
        expected_unit = self._opex_per_cap_def[n].unit
        if not opex_per_cap.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.OPEXPERCAP_SET.value,
                [s, n],
                f"Unit {opex_per_cap.unit} of opex_per_cap[{s}, {n}] "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._opex_per_cap[s, n] = opex_per_cap

    # ------------------------- #
    # Property: opex_per_energy #
    # ------------------------- #
    def get_opex_per_energy(self, s: StageId, n: NetTechId) -> Value:
        """
        Get the parameter 'opex_per_energy' which denotes the amount of
        OPEX cost per link length for each unit of transmitted energy through a
        network technology. This is an optional parameter with a default value
        of 0.

        :param s: Stage
        :type s: StageId
        :param n: Network technology
        :type n: NetTechId
        :return: OPEX cost per link length per unit of transmitted energy
        :rtype: Value
        """
        self._check_id(n, ExceptionKey.OPEXPERCAP_GET)
        return self._opex_per_energy.get((s, n), self._opex_per_energy_def[n])

    def set_opex_per_energy(
        self, s: StageId, n: NetTechId, opex_per_energy: Value
    ) -> None:
        """
        Set the parameter 'opex_per_energy' which denotes the amount of
        OPEX cost per link length for each unit of transmitted energy through a
        network technology. This is an optional parameter with a default value
        of 0.

        :param s: Stage
        :type s: StageId
        :param n: Network technology
        :type n: NetTechId
        :param opex_per_energy: OPEX cost per link length per unit of
            transmitted energy
        :type opex_per_energy: Value
        """
        self._check_id(n, ExceptionKey.OPEXPERENERGY_SET)
        expected_unit = self._opex_per_energy_def[n].unit
        if not opex_per_energy.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.OPEXPERENERGY_SET.value,
                [s, n],
                f"Unit {opex_per_energy.unit} of opex_per_energy[{s}, {n}] "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._opex_per_energy[s, n] = opex_per_energy

    # --------------------- #
    # Property: co2_per_cap #
    # --------------------- #
    def get_co2_per_cap(self, s: StageId, n: NetTechId) -> Value:
        """
        Get the parameter 'co2_per_cap' which denotes the amount of embedded
        CO2 per link length that arises for each unit of installed network
        technology. This is an optional parameter with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param n: Network technology
        :type n: NetTechId
        :return: Embedded CO2 per link length per unit of installed network technology
        :rtype: Value
        """
        self._check_id(n, ExceptionKey.CO2PERCAP_GET)
        return self._co2_per_cap.get((s, n), self._co2_per_cap_def[n])

    def set_co2_per_cap(self, s: StageId, n: NetTechId, co2_per_cap: Value) -> None:
        """
        Set the parameter 'co2_per_cap' which denotes the amount of embedded
        CO2 per link length that arises for each unit of installed network
        technology. This is an optional parameter with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param n: Network technology
        :type n: NetTechId
        :param co2_per_cap: Embedded CO2 per link length per unit of installed
            network technology
        :type co2_per_cap: float
        """
        self._check_id(n, ExceptionKey.CO2PERCAP_SET)
        expected_unit = self._co2_per_cap_def[n].unit
        if not co2_per_cap.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.CO2PERCAP_SET.value,
                [s, n],
                f"Unit {co2_per_cap.unit} of co2_per_cap[{s}, {n}] "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._co2_per_cap[s, n] = co2_per_cap

    # ------------------------ #
    # Property: co2_per_energy #
    # --------------------- -- #
    def get_co2_per_energy(self, s: StageId, n: NetTechId) -> Value:
        """
        Get the parameter 'co2_per_energy' which denotes the amount of embedded
        CO2 per link length that arises for each unit of transmitted energy
        through a network technology. This is an optional parameter with a
        default value of 0.

        :param s: Stage
        :type s: StageId
        :param n: Network technology
        :type n: NetTechId
        :return: Embedded CO2 per link length per unit of transmitted energy
        :rtype: Value
        """
        self._check_id(n, ExceptionKey.CO2PERENERGY_GET)
        return self._co2_per_energy.get((s, n), self._co2_per_energy_def[n])

    def set_co2_per_energy(
        self, s: StageId, n: NetTechId, co2_per_energy: Value
    ) -> None:
        """
        Set the parameter 'co2_per_energy' which denotes the amount of embedded
        CO2 per link length that arises for each unit of transmitted energy
        through a network technology. This is an optional parameter with a
        default value of 0.

        :param s: Stage
        :type s: StageId
        :param n: Network technology
        :type n: NetTechId
        :param co2_per_energy: Embedded CO2 per link length per unit of
            transmitted energy
        :type co2_per_energy: Value
        """
        self._check_id(n, ExceptionKey.CO2PERENERGY_SET)
        expected_unit = self._co2_per_energy_def[n].unit
        if not co2_per_energy.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.CO2PERENERGY_SET.value,
                [s, n],
                f"Unit {co2_per_energy.unit} of co2_per_energy[{s}, {n}] "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._co2_per_energy[s, n] = co2_per_energy

    # --------------------- #
    # Property: trans_decay #
    # --------------------- #
    def get_trans_decay(self, s: StageId, n: NetTechId) -> Value:
        """
        Get the parameter 'trans_decay' which denotes the decay parameter in the
        exponential dynamic transmission model. The relative loss rate per unit
        of link length is then given exp(-trans_decay * unit_length). This is an
        optional parameter with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param n: Network technology
        :type n: NetTechId
        :return: Transmission decay rate
        :rtype: Value
        """
        self._check_id(n, ExceptionKey.TRANSDECAY_GET)
        return self._trans_decay.get(
            (s, n), Value(DEF_TRANSDECAY, DimlessUnit() / LengthUnit.M)
        )

    def set_trans_decay(self, s: StageId, n: NetTechId, trans_decay: Value) -> None:
        """
        Set the parameter 'trans_decay' which denotes the decay parameter in the
        exponential dynamic transmission model. The relative loss rate per unit
        of link length is then given exp(-trans_decay * unit_length). This is an
        optional parameter with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param n: Network technology
        :type n: NetTechId
        :param trans_decay: Transmission decay rate
        :type trans_decay: Value
        """
        self._check_id(n, ExceptionKey.TRANSDECAY_SET)
        expected_unit = DimlessUnit() / LengthUnit.M
        if not trans_decay.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.TRANSDECAY_SET.value,
                [s, n],
                f"Unit {trans_decay.unit} of trans_decay[{s}, {n}] "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._trans_decay[s, n] = trans_decay

    # ------------------ #
    # Property: cap_init #
    # ------------------ #
    def get_cap_init(self, li: NetLinkId, n: NetTechId) -> Value:
        """
        Get the parameter 'cap_init' which denotes a network technology's
        initial capacity that is present on a link during the first stage,
        independent of potential installation choices. This is an optional
        parameter with a default value of 0.

        :param li: Network link
        :type li: NetLinkId
        :param n: Network technology
        :type n: NetTechId
        :return: Initial capacity
        :rtype: float
        """
        self._check_id(n, ExceptionKey.CAPINIT_GET)
        return self._cap_init.get((li, n), self._cap_init_def[n])

    def set_cap_init(self, li: NetLinkId, n: NetTechId, cap_init: Value) -> None:
        """
        Set the parameter 'cap_init' which denotes a network technology's
        initial capacity that is present on a link during the first stage,
        independent of potential installation choices. This is an optional
        parameter with a default value of 0.

        :param li: Network link
        :type li: NetLinkId
        :param n: Network technology
        :type n: NetTechId
        :param cap_init: Initial capacity
        :type cap_init: Value
        """
        self._check_id(n, ExceptionKey.CAPINIT_SET)
        expected_unit = self._cap_init_def[n].unit
        if not cap_init.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.CAPINIT_SET.value,
                [li, n],
                f"Unit {cap_init.unit} of cap_init[{li}, {n}] "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._cap_init[li, n] = cap_init

    # ------------------ #
    # Property: age_init #
    # ------------------ #
    def get_age_init(self, li: NetLinkId, n: NetTechId) -> Value:
        """
        Get the parameter 'age_init' which denotes the age of a network
        technology's initial installation (if any) that is present on a link
        during the first stage, independent of potential installation choices.
        This is an optional parameter with a default value of 0.

        :param li: Network link
        :type li: NetLinkId
        :param n: Network technology
        :type n: NetTechId
        :return: Age of initial installation
        :rtype: Value
        """
        self._check_id(n, ExceptionKey.AGEINIT_GET)
        return self._age_init.get((li, n), Value(DEF_AGEINIT, TimeUnit.A))

    def set_age_init(self, li: NetLinkId, n: NetTechId, age_init: Value) -> None:
        """
        Set the parameter 'age_init' which denotes the age of a network
        technology's initial installation (if any) that is present on a link
        during the first stage, independent of potential installation choices.
        This is an optional parameter with a default value of 0.

        :param li: Network link
        :type li: NetLinkId
        :param n: Network technology
        :type n: NetTechId
        :param age_init: Age of initial installation
        :type age_init: Value
        """
        self._check_id(n, ExceptionKey.AGEINIT_SET)
        expected_unit = TimeUnit.A
        if not age_init.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.AGEINIT_SET.value,
                [li, n],
                f"Unit {age_init.unit} of age_init[{li}, {n}] "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._age_init[li, n] = age_init

    # ------------------------ #
    # Property: allowed_stages #
    # ------------------------ #
    def get_allowed_stages(self, n: NetTechId) -> Set[StageId]:
        """
        Get all stages that are considered allowed for a network technology.
        Technologies are only considered installable, installed or useable in
        allowed stages.

        :param n: Network technology
        :type n: NetTechId
        :return: Set of allowed stages
        :rtype: Set[StageId]
        """
        return self._allowed_stages.get(n, set())

    def add_allowed_stage(self, s: StageId, n: NetTechId) -> None:
        """
        Add an allowed stage for a network technology. Technologies are only
        considered installable, installed or useable in allowed stages.

        :param s: Stage
        :type s: StageId
        :param n: Network technology
        :type n: NetTechId
        """
        if n not in self._allowed_stages:
            self._allowed_stages[n] = set()
        if s in self._allowed_stages[n]:
            msg = f"Added allowed_stage {s} for {n} which was already allowed"
            logging.log_warning(msg, module=LOG_MODULE_STR)
        self._allowed_stages[n].add(s)

    def remove_allowed_stage(self, s: StageId, n: NetTechId) -> None:
        """
        Remove a stage from the allowed stages of a network technology.
        Technologies are only considered installable, installed or useable in
        allowed stages.

        :param s: Stage
        :type s: StageId
        :param n: Network technology
        :type n: NetTechId
        """
        if n not in self._allowed_stages:
            self._allowed_stages[n] = set()
        if s not in self._allowed_stages[n]:
            msg = f"Removing allowed_stage {s} for {n} which was already not allowed"
            logging.log_warning(msg, module=LOG_MODULE_STR)
            return
        self._allowed_stages[n].remove(s)

    # --------------------------- #
    # Property: allowed_net_links #
    # --------------------------- #
    def get_allowed_net_links(self, n: NetTechId) -> Set[NetLinkId]:
        """
        Get all network links that are considered allowed for a technology.
        Technologies are only considered installable, installed or useable on
        allowed links.

        :param n: Network technology
        :type n: NetTechId
        :return: Network link
        :rtype: Set[NetLinkId]
        """
        return self._allowed_net_links.get(n, set())

    def add_allowed_net_link(self, li: NetLinkId, n: NetTechId) -> None:
        """
        Add an allowed network link for a network technology. Technologies are
        only considered installable, installed or useable on allowed links.

        :param li: Network link
        :type li: NetLinkId
        :param n: Network technology
        :type n: NetTechId
        """
        if n not in self._allowed_net_links:
            self._allowed_net_links[n] = set()
        if li in self._allowed_net_links[n]:
            msg = f"Added allowed_net_link {li} for {n} which was already allowed"
            logging.log_warning(msg, module=LOG_MODULE_STR)
        self._allowed_net_links[n].add(li)

    def remove_allowed_net_link(self, li: NetLinkId, n: NetTechId) -> None:
        """
        Remove a network link from the allowed links of a network technology.
        Technologies are only considered installable, installed or useable on
        allowed links.

        :param li: Network link
        :type li: NetLinkId
        :param n: Network technology
        :type n: NetTechId
        """
        if n not in self._allowed_net_links:
            self._allowed_net_links[n] = set()
        if li not in self._allowed_net_links[n]:
            msg = (
                f"Removing allowed_net_link {li} for {n} which was already not allowed"
            )
            logging.log_warning(msg, module=LOG_MODULE_STR)
            return
        self._allowed_net_links[n].remove(li)

    # -------------------- #
    # Construction methods #
    # -------------------- #
    def __init__(self) -> None:
        self._ids: Set[NetTechId] = set()
        self._ec: Dict[NetTechId, EcId] = {}
        self._lifetime: Dict[NetTechId, Value] = {}
        self._interest_rate: Dict[NetTechId, Value] = {}
        self._unit_cap_min: Dict[Tuple[StageId, NetTechId], Value] = {}
        self._unit_cap_min_def: Dict[NetTechId, Value] = {}
        self._one_time_capex: Dict[Tuple[StageId, NetTechId], Value] = {}
        self._capex_per_cap: Dict[Tuple[StageId, NetTechId], Value] = {}
        self._capex_per_cap_def: Dict[NetTechId, Value] = {}
        self._one_time_opex: Dict[Tuple[StageId, NetTechId], Value] = {}
        self._opex_per_cap: Dict[Tuple[StageId, NetTechId], Value] = {}
        self._opex_per_cap_def: Dict[NetTechId, Value] = {}
        self._opex_per_energy: Dict[Tuple[StageId, NetTechId], Value] = {}
        self._opex_per_energy_def: Dict[NetTechId, Value] = {}
        self._co2_per_cap: Dict[Tuple[StageId, NetTechId], Value] = {}
        self._co2_per_cap_def: Dict[NetTechId, Value] = {}
        self._co2_per_energy: Dict[Tuple[StageId, NetTechId], Value] = {}
        self._co2_per_energy_def: Dict[NetTechId, Value] = {}
        self._trans_decay: Dict[Tuple[StageId, NetTechId], Value] = {}
        self._cap_init: Dict[Tuple[NetLinkId, NetTechId], Value] = {}
        self._cap_init_def: Dict[NetTechId, Value] = {}
        self._age_init: Dict[Tuple[NetLinkId, NetTechId], Value] = {}
        self._allowed_stages: Dict[NetTechId, Set[StageId]] = {}
        self._allowed_net_links: Dict[NetTechId, Set[NetLinkId]] = {}

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self, stages: Stages, net_links: NetworkLinks, ecs: Ecs) -> None:
        """
        Validate all network technology data in this object. Apart from sense-
        checking parameter in terms of quantity, this includes checking whether
        the ids from other data classes used here are known there as well.

        :param stages: Stages data class
        :type stages: Stages
        :param net_links: Network links data class
        :type net_links: NetworkLinks
        :param ecs: ecs data class
        :type ecs: Ecs
        """
        self._validate_ec(ecs)
        self._validate_lifetime()
        self._validate_interest_rate()
        self._validate_unit_cap_min(stages)
        self._validate_one_time_capex(stages)
        self._validate_capex_per_cap(stages)
        self._validate_one_time_opex(stages)
        self._validate_opex_per_cap(stages)
        self._validate_opex_per_energy(stages)
        self._validate_co2_per_cap(stages)
        self._validate_co2_per_energy(stages)
        self._validate_trans_decay(stages)
        self._validate_cap_init(net_links)
        self._validate_age_init(net_links)
        self._validate_allowed_stages(stages)
        self._validate_allowed_net_links(net_links)

    def _validate_ec(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.EC_VAL.value
        for n, e in self._ec.items():
            # Unknown ec
            if e not in ecs.ids:
                msg = f"Unknown ec {e} in ec[{n}]"
                raise exceptions.DataException(
                    exc_key, [n, e], msg, module=LOG_MODULE_STR
                )

    def _validate_lifetime(self) -> None:
        for n, lifetime in self._lifetime.items():
            # Lifetime has to be positive
            if lifetime <= Value(0, TimeUnit.A):
                msg = f"{lifetime} = lifetime[{n}] <= 0"
                raise exceptions.DataException(
                    ExceptionKey.LIFETIME_VAL.value, [n], msg, module=LOG_MODULE_STR
                )

    def _validate_interest_rate(self) -> None:
        for n, interest_rate in self._interest_rate.items():
            # Interest rate has to be nonnegative
            if interest_rate.is_negative:
                msg = f"{interest_rate} = interest_rate[{n}] < 0"
                raise exceptions.DataException(
                    ExceptionKey.INTERESTRATE_VAL.value, [n], msg, module=LOG_MODULE_STR
                )

    def _validate_unit_cap_min(self, stages: Stages) -> None:
        exc_key = ExceptionKey.UNITCAPMIN_VAL.value
        for (s, n), unit_cap_min in self._unit_cap_min.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in unit_cap_min[{s}, {n}]"
                raise exceptions.DataException(
                    exc_key, [s, n], msg, module=LOG_MODULE_STR
                )
            # unit_cap_min has to be nonnegative
            if unit_cap_min.is_negative:
                msg = f"{unit_cap_min} = unit_cap_min[{s}, {n}] < 0"
                raise exceptions.DataException(
                    ExceptionKey.UNITCAPMIN_VAL.value,
                    [s, n],
                    msg,
                    module=LOG_MODULE_STR,
                )

    def _validate_one_time_capex(self, stages: Stages) -> None:
        exc_key = ExceptionKey.ONETIMECAPEX_VAL.value
        for (s, n), one_time_capex in self._one_time_capex.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in one_time_capex[{s}, {n}]"
                raise exceptions.DataException(
                    exc_key, [s, n], msg, module=LOG_MODULE_STR
                )
            # one_time_capex usually nonnegative
            if one_time_capex.is_negative:
                msg = f"{one_time_capex} = one_time_capex[{s}, {n}] < 0"
                logging.log_warning(msg, LOG_MODULE_STR)

    def _validate_capex_per_cap(self, stages: Stages) -> None:
        exc_key = ExceptionKey.CAPEXPERCAP_VAL.value
        for (s, n), capex_per_cap in self._capex_per_cap.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in capex_per_cap[{s}, {n}]"
                raise exceptions.DataException(
                    exc_key, [s, n], msg, module=LOG_MODULE_STR
                )
            # capex_per_cap usually nonnegative
            if capex_per_cap.is_negative:
                msg = f"{capex_per_cap} = capex_per_cap[{s}, {n}] < 0"
                logging.log_warning(msg, LOG_MODULE_STR)

    def _validate_one_time_opex(self, stages: Stages) -> None:
        exc_key = ExceptionKey.ONETIMEOPEX_VAL.value
        for (s, n), one_time_opex in self._one_time_opex.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in one_time_opex[{s}, {n}]"
                raise exceptions.DataException(
                    exc_key, [s, n], msg, module=LOG_MODULE_STR
                )
            # one_time_opex usually nonnegative
            if one_time_opex.is_negative:
                msg = f"{one_time_opex} = one_time_opex[{s}, {n}] < 0"
                logging.log_warning(msg, LOG_MODULE_STR)

    def _validate_opex_per_cap(self, stages: Stages) -> None:
        exc_key = ExceptionKey.OPEXPERCAP_VAL.value
        for (s, n), opex_per_cap in self._opex_per_cap.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in opex_per_cap[{s}, {n}]"
                raise exceptions.DataException(
                    exc_key, [s, n], msg, module=LOG_MODULE_STR
                )
            # opex_per_cap usually nonnegative
            if opex_per_cap.is_negative:
                msg = f"{opex_per_cap} = opex_per_cap[{s}, {n}] < 0"
                logging.log_warning(msg, LOG_MODULE_STR)

    def _validate_opex_per_energy(self, stages: Stages) -> None:
        exc_key = ExceptionKey.OPEXPERENERGY_VAL.value
        for (s, n), opex_per_energy in self._opex_per_energy.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in opex_per_energy[{s}, {n}]"
                raise exceptions.DataException(
                    exc_key, [s, n], msg, module=LOG_MODULE_STR
                )
            # opex_per_energy usually nonnegative
            if opex_per_energy.is_negative:
                msg = f"{opex_per_energy} = opex_per_energy[{s}, {n}] < 0"
                logging.log_warning(msg, LOG_MODULE_STR)

    def _validate_co2_per_cap(self, stages: Stages) -> None:
        exc_key = ExceptionKey.CO2PERCAP_VAL.value
        for (s, n), co2_per_cap in self._co2_per_cap.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in co2_per_cap[{s}, {n}]"
                raise exceptions.DataException(
                    exc_key, [s, n], msg, module=LOG_MODULE_STR
                )
            # co2_per_cap usually nonnegative
            if co2_per_cap.is_negative:
                msg = f"{co2_per_cap} = co2_per_cap[{s}, {n}] < 0"
                logging.log_warning(msg, LOG_MODULE_STR)

    def _validate_co2_per_energy(self, stages: Stages) -> None:
        exc_key = ExceptionKey.CO2PERENERGY_VAL.value
        for (s, n), co2_per_energy in self._co2_per_energy.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in co2_per_energy[{s}, {n}]"
                raise exceptions.DataException(
                    exc_key, [s, n], msg, module=LOG_MODULE_STR
                )
            # co2_per_energy usually nonnegative
            if co2_per_energy.is_negative:
                msg = f"{co2_per_energy} = co2_per_energy[{s}, {n}] < 0"
                logging.log_warning(msg, LOG_MODULE_STR)

    def _validate_trans_decay(self, stages: Stages) -> None:
        exc_key = ExceptionKey.TRANSDECAY_VAL.value
        for (s, n), trans_decay in self._trans_decay.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in trans_decay[{s}, {n}]"
                raise exceptions.DataException(
                    exc_key, [s, n], msg, module=LOG_MODULE_STR
                )
            # trans_decay must be nonnegative
            if trans_decay.is_negative:
                msg = f"{trans_decay} = trans_decay[{s}, {n}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, n], msg, module=LOG_MODULE_STR
                )

    def _validate_cap_init(self, links: NetworkLinks) -> None:
        exc_key = ExceptionKey.CAPINIT_VAL.value
        for (li, n), cap_init in self._cap_init.items():
            # Unknown hub
            if li not in links.ids:
                msg = f"Unknown link {li} in cap_init[{li}, {n}]"
                raise exceptions.DataException(
                    exc_key, [li], msg, module=LOG_MODULE_STR
                )
            # cap_init must be nonnegative
            if cap_init.is_negative:
                msg = f"{cap_init} = cap_init[{li}, {n}] < 0"
                raise exceptions.DataException(
                    exc_key, [li, n], msg, module=LOG_MODULE_STR
                )

    def _validate_age_init(self, links: NetworkLinks) -> None:
        exc_key = ExceptionKey.AGEINIT_VAL.value
        for (li, n), age_init in self._age_init.items():
            # Unknown hub
            if li not in links.ids:
                msg = f"Unknown link {li} in age_init[{li}, {n}]"
                raise exceptions.DataException(
                    exc_key, [li], msg, module=LOG_MODULE_STR
                )
            # age_init must be nonnegative
            if age_init.is_negative:
                msg = f"{age_init} = age_init[{li}, {n}] < 0"
                raise exceptions.DataException(
                    exc_key, [li, n], msg, module=LOG_MODULE_STR
                )

    def _validate_allowed_stages(self, stages: Stages) -> None:
        exc_key = ExceptionKey.ALLOWEDSTAGES_VAL.value
        for n, allowed_stages in self._allowed_stages.items():
            for s in allowed_stages:
                # Unknown stage
                if s not in stages.ids:
                    msg = f"Unknown stage {s} in allowed_stages[{n}]"
                    raise exceptions.DataException(
                        exc_key, [s, n], msg, module=LOG_MODULE_STR
                    )
        # Identify net_techs that are allowed nowhere
        for n in self.ids:
            if not self.get_allowed_stages(n):
                msg = f"{n} is not allowed in any stage (due to TRL)"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_allowed_net_links(self, net_links: NetworkLinks) -> None:
        exc_key = ExceptionKey.ALLOWEDNETLINKS_VAL.value
        for n, allowed_net_links in self._allowed_net_links.items():
            for li in allowed_net_links:
                # Unknown net_link
                if li not in net_links.ids:
                    msg = f"Unknown net_link {li} in allowed_net_links[{n}]"
                    raise exceptions.DataException(
                        exc_key, [li, n], msg, module=LOG_MODULE_STR
                    )
        # Identify net_techs that are allowed nowhere
        for n in self.ids:
            if not self.get_allowed_net_links(n):
                msg = (
                    f"{n} is not allowed in any net_link (due to "
                    "allowed_net_tech_lists)"
                )
                logging.log_warning(msg, module=LOG_MODULE_STR)

    # ---------- #
    # Id checker #
    # ---------- #
    def _check_id(self, n: NetTechId, where: ExceptionKey) -> None:
        if n not in self._ids:
            raise exceptions.UnknownIdException(where.value, n, module=LOG_MODULE_STR)
