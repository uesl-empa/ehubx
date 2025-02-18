"""
Conversion technology data module
"""
from enum import Enum
from typing import Dict, List, Set, Tuple
from ehubx.core.common import TimeSeriesKind, EPS_ZEROCHECK
from ehubx.core import logging
from ehubx.data.stage_data import Stages, StageId
from ehubx.data.hub_data import Hubs, HubId
from ehubx.data.tech_data import Techs, TechId
from ehubx.data.ec_data import Ecs, EcId
from ehubx.data.time_data import Times, TimeId
from ehubx.data.time_series import TimeSeries
from ehubx.data import exceptions


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the conversion technology
    data module
    """
    ID_ADD = "adding to 'ids' of ConversionTechs"
    ID_REMOVE = "removing from 'ids' of ConversionTechs"
    ID_VAL = "validating 'ids' of ConversionTechs"
    OPEXPERENERGY_SET = "setting 'opex_per_energy' of ConversionTechs"
    OPEXPERENERGY_GET = "getting 'opex_per_energy' from ConversionTechs"
    OPEXPERENERGY_VAL = "validating 'opex_per_energy' of ConversionTechs"
    INECS_ADD = "adding to 'in_ecs' of ConversionTechs"
    INECS_GET = "getting 'in_ecs' from ConversionTechs"
    INECS_VAL = "validating 'in_ecs' of ConversionTechs"
    INECMAIN_SET = "setting 'in_ec_main' of ConversionTechs"
    INECMAIN_GET = "getting 'in_ec_main' from ConversionTechs"
    INECMAIN_VAL = "validating 'in_ec_main' of ConversionTechs"
    INPART_SET = "setting 'in_part' of ConversionTechs"
    INPART_GET = "getting 'in_part' from ConversionTechs"
    INPART_VAL = "validating 'in_part' of 'in_ecs' of ConversionTechs"
    OUTECS_ADD = "adding to 'out_ecs' of ConversionTechs"
    OUTECS_GET = "gettin 'out_ecs' from ConversionTechs"
    OUTECS_VAL = "validating to 'out_ecs' of ConversionTechs"
    OUTECMAIN_SET = "setting 'out_ec_main' of ConversionTechs"
    OUTECMAIN_GET = "getting 'out_ec_main' from ConversionTechs"
    OUTECMAIN_VAL = "validating 'out_ec_main' of ConversionTechs"
    OUTEFF_SET = "setting 'out_eff' of ConversionTechs"
    OUTEFF_DEFSET = "setting default 'out_eff' of ConversionTechs"
    OUTEFF_GET = "getting 'out_eff' from ConversionTechs"
    OUTEFF_VAL = "validating 'out_eff' 'out_ecs' of ConversionTechs"
    OUTSUMMIN_SET = "setting 'out_sum_min' of ConversionTechs"
    OUTSUMMIN_GET = "getting 'out_sum_min' from ConversionTechs"
    OUTSUMMIN_VAL = "validating 'out_sum_min' of ConversionTechs"
    OUTSUMMAX_SET = "setting 'out_sum_max' of ConversionTechs"
    OUTSUMMAX_GET = "getting 'out_sum_max' from ConversionTechs"
    OUTSUMMAX_VAL = "validating 'out_sum_max' of ConversionTechs"
    OUTSUMMINMAX_VAL = ("validating 'out_sum_min' against 'out_sum_max' "
                        "of ConversionTechs")
    AVAILABILITY_SET = "setting 'availability' of ConversionTechs"
    AVAILABILITY_DEFSET = "setting default 'availability' of ConversionTechs"
    AVAILABILITY_GET = "getting 'availability' from ConversionTechs"
    AVAILABILITY_VAL = "validating 'availability' of ConversionTechs"
    COPYOVERTECH = ("copying conv_tech from one ConversionTechs instance "
                    "to another")


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/conv_tech"
"""String identifying the conversion technology data module for logging
purposes"""

DEF_OPEXPERENERGY: float = 0
"""Default value for parameter 'opex_per_energy' in the conversion technology
data module"""

DEF_INPART: float = 1
"""Default value for parameter 'in_part' in the conversion technology
data module"""

DEF_OUTSUMMIN: float = 0
"""Default value for parameter 'out_sum_min' in the conversion technology
data module"""

DEF_OUTSUMMAX: float = float("inf")
"""Default value for parameter 'out_sum_max' in the conversion technology
data module"""

DEF_AVAILABILITY: float = 1
"""Default value for parameter 'availability' in the conversion technology
data module"""


class ConversionTechs:
    """
    Class to hold conversion technology data. Manages conversion technology
    ids, contains getters and setters for conversion technology parameters and
    validation methods to control data integrity
    """

    # ------------- #
    # Property: ids #
    # ------------- #
    @property
    def ids(self) -> Set[TechId]:
        """
        Set of known conversion technology ids
        """
        return self._ids

    @property
    def ids_in_order(self) -> List[TechId]:
        """
        List of known conversion tech ids in alphabetical order
        """
        ids = list(self.ids)
        ids.sort(key=lambda x: x.key)
        return ids

    def add_id(self, x: TechId) -> None:
        """
        Add a new conversion technology id

        :param x: Id to be added
        :type x: TechId
        """
        if x in self._ids:
            raise exceptions.DuplicateIdException(ExceptionKey.ID_ADD.value, x,
                                                  module=LOG_MODULE_STR)
        self._ids.add(x)

    def remove_id(self, x: TechId) -> None:
        """
        Remove a conversion technology id

        :param x: Id to be removed
        :type x: TechId
        """
        if x not in self._ids:
            raise exceptions.MissingIdException(ExceptionKey.ID_REMOVE.value,
                                                x, module=LOG_MODULE_STR)
        self._ids.remove(x)
        if x in self._in_ecs:
            self._in_ecs.pop(x)
        if x in self._in_ec_main:
            self._in_ec_main.pop(x)
        for (s, x2, e) in list(self._in_part.keys()):
            if x == x2:
                self._in_part.pop((s, x, e))
        if x in self._out_ecs:
            self._out_ecs.pop(x)
        if x in self._out_ec_main:
            self._out_ec_main.pop(x)
        for (s, x2, e) in list(self._out_eff.keys()):
            if x == x2:
                self._out_eff.pop((s, x, e))
        for (s, x2) in list(self._opex_per_energy.keys()):
            if x == x2:
                self._opex_per_energy.pop((s, x))
        for (s, h, x2) in list(self._out_sum_min.keys()):
            if x == x2:
                self._out_sum_min.pop((s, h, x))
        for (s, h, x2) in list(self._out_sum_max.keys()):
            if x == x2:
                self._out_sum_max.pop((s, h, x))
        for (s, h, x2) in list(self._availability.keys()):
            if x == x2:
                self._availability.pop((s, h, x))

    # ------------------------- #
    # Property: opex_per_energy #
    # ------------------------- #
    def get_opex_per_energy(self, s: StageId, x: TechId) -> float:
        """
        Get the parameter 'opex_per_energy' which quantifies the amount of
        operation & maintenance cost for a conversion technology per amount of
        output of the conversion technology's main output carrier.

        :param s: Stage id
        :type s: StageId
        :param x: Id of conversion technology
        :type x: TechId
        :return: opex_per_energy value
        :rtype: float
        """
        self._check_id(x, ExceptionKey.OPEXPERENERGY_GET)
        return self._opex_per_energy.get((s, x), DEF_OPEXPERENERGY)

    def set_opex_per_energy(self, s: StageId, x: TechId,
                            opex_per_energy: float) -> None:
        """
        Get the parameter 'opex_per_energy' which quantifies the amount of
        operation & maintenance cost for a conversion technology per amount of
        output of the conversion technology's main output carrier.

        :param s: Stage id
        :type s: StageId
        :param x: Id of conversion technology
        :type x: TechId
        :param opex_per_energy: opex_per_energy value
        :type opex_per_energy: float
        """
        self._check_id(x, ExceptionKey.OPEXPERENERGY_SET)
        self._opex_per_energy[s, x] = opex_per_energy

    # ---------------- #
    # Property: in_ecs #
    # ---------------- #
    def get_in_ecs(self, x: TechId) -> Set[EcId]:
        """
        Get all input ecs of a conversion technology

        :param x: Id of conversion technology
        :type x: TechId
        :return: Set of all input ecs
        :rtype: Set[EcId]
        """
        self._check_id(x, ExceptionKey.INECS_GET)
        in_ecs = self._in_ecs.get(x, None)
        if in_ecs is None:
            raise exceptions.MissingIdException(ExceptionKey.INECS_GET.value,
                                                x, module=LOG_MODULE_STR)
        return in_ecs

    def add_in_ec(self, x: TechId, e: EcId) -> None:
        """
        Add an input ec to a conversion technology

        :param x: Id of conversion technology
        :type x: TechId
        :param e: Id of input ec to be added
        :type e: EcId
        """
        self._check_id(x, ExceptionKey.INECS_ADD)
        if x not in self._in_ecs:
            self._in_ecs[x] = set()
        self._in_ecs[x].add(e)

    # -------------------- #
    # Property: in_ec_main #
    # -------------------- #
    def get_in_ec_main(self, x: TechId) -> EcId:
        """
        Get a conversion technology's main input ec. If in_ec_main is not
        defined and the technology only has a single input ec, that ec's id is
        returned

        :param x: Id of conversion technology
        :type x: TechId
        :return: Main input ec
        :rtype: EcId
        """
        self._check_id(x, ExceptionKey.INECMAIN_GET)
        if x not in self._in_ec_main:
            # Try to return automatically
            if x in self._in_ecs and len(self._in_ecs[x]) == 1:
                [in_ec_main] = self._in_ecs[x]
                return in_ec_main
            raise exceptions.MissingIdException(
                ExceptionKey.INECMAIN_GET.value, x,
                module=LOG_MODULE_STR)
        return self._in_ec_main[x]

    def set_in_ec_main(self, x: TechId, e: EcId) -> None:
        """
        Set a conversion technology's main input ec

        :param x: Id of conversion technology
        :type x: TechId
        :param e: Main input ec
        :type e: EcId
        """
        self._check_id(x, ExceptionKey.INECMAIN_SET)
        self._in_ec_main[x] = e

    # ----------------- #
    # Property: in_part #
    # ----------------- #
    def get_in_part(self, s: StageId, x: TechId, e: EcId) -> float:
        """
        Get the parameter 'in_part' for a conversion technology's input ec.
        in_part quantifies the percentage to which each input ec adds to the
        total input ec composition.

        :param s: Stage Id
        :type s: StageId
        :param x: Id of conversion technology
        :type x: TechId
        :param e: Id of input ec
        :type e: EcId
        :return: Parameter in_part
        :rtype: float
        """
        self._check_id(x, ExceptionKey.INPART_GET)
        if (s, x, e) not in self._in_part:
            # Try to return automatically
            if x in self._in_ecs and self._in_ecs[x] == {e}:
                return DEF_INPART
            key_val = ExceptionKey.INPART_GET.value
            msg = (f"Unknown ({s.kind_as_str}, {x.kind_as_str}, "
                   f"{e.kind_as_str}) index tuple ({s.key}, {x.key}, {e.key}) "
                   "for 'in_part' of ConversionTechs")
            raise exceptions.DataException(key_val, [s, x, e], msg,
                                           module=LOG_MODULE_STR)
        return self._in_part[s, x, e]

    def set_in_part(self, s: StageId, x: TechId, e: EcId,
                    in_part: float) -> None:
        """
        Set the parameter 'in_part' for a conversion technology's input ec.
        in_part quantifies the percentage to which each input ec adds to the
        total input ec composition.

        :param s: Stage Id
        :type s: StageId
        :param x: Id of conversion technology
        :type x: TechId
        :param e: Id of input ec
        :type e: EcId
        :param in_part: Parameter in_part
        :type in_part: float
        """
        self._check_id(x, ExceptionKey.INPART_SET)
        self._in_part[s, x, e] = in_part

    # ----------------- #
    # Property: out_ecs #
    # ----------------- #
    def get_out_ecs(self, x: TechId) -> Set[EcId]:
        """
        Get all output ecs of a conversion technology

        :param x: Id of conversion technology
        :type x: TechId
        :return: Set of all output ecs
        :rtype: Set[EcId]
        """
        self._check_id(x, ExceptionKey.OUTECS_GET)
        out_ecs = self._out_ecs.get(x, None)
        if out_ecs is None:
            raise exceptions.MissingIdException(
                ExceptionKey.OUTECS_GET.value, x,
                module=LOG_MODULE_STR)
        return out_ecs

    def add_out_ec(self, x: TechId, e: EcId) -> None:
        """
        Add an output ec to a conversion technology

        :param x: Id of conversion technology
        :type x: TechId
        :param e: Id of output ec to be added
        :type e: EcId
        """
        self._check_id(x, ExceptionKey.OUTECS_ADD)
        if x not in self._out_ecs:
            self._out_ecs[x] = set()
        self._out_ecs[x].add(e)

    # --------------------- #
    # Property: out_ec_main #
    # --------------------- #
    def get_out_ec_main(self, x: TechId) -> EcId:
        """
        Get a conversion technology's main output ec. If out_ec_main is not
        defined and the technology only has a single output ec, that ec's id is
        returned

        :param x: Id of conversion technology
        :type x: TechId
        :return: Main output ec
        :rtype: EcId
        """
        self._check_id(x, ExceptionKey.OUTECMAIN_GET)
        if x not in self._out_ec_main:
            # Try to return automatically
            if x in self._out_ecs and len(self._out_ecs[x]) == 1:
                [out_ec_main] = self._out_ecs[x]
                return out_ec_main
            raise exceptions.MissingIdException(
                ExceptionKey.OUTECMAIN_GET.value, x,
                module=LOG_MODULE_STR)
        return self._out_ec_main[x]

    def set_out_ec_main(self, x: TechId, e: EcId) -> None:
        """
        Set a conversion technology's main output ec

        :param x: Id of conversion technology
        :type x: TechId
        :param e: Main output ec
        :type e: EcId
        """
        self._check_id(x, ExceptionKey.OUTECMAIN_SET)
        self._out_ec_main[x] = e

    # ----------------- #
    # Property: out_eff #
    # ----------------- #
    def get_out_eff(self, s: StageId, x: TechId, e: EcId) -> TimeSeries:
        """
        Get the parameter 'out_eff' for a conversion technology's output ec.
        out_eff quantifies the relative output of that ec relative to the
        technology's main input ec. E.g.; a value of 0.5 means that the output
        amount of that ec is identical to half the input amount of the main
        input ec.

        :param s: Stage id
        :type s: StageId
        :param x: Id of conversion technology
        :type x: TechId
        :param e: Id of output ec
        :type e: EcId
        :return: Time series for parameter out_eff
        :rtype: TimeSeries
        """
        self._check_id(x, ExceptionKey.OUTEFF_GET)
        if (s, x, e) in self._out_eff:
            return self._out_eff[s, x, e]
        key_val = ExceptionKey.OUTEFF_GET.value
        msg = f"Unknown ({s.kind_as_str}, {x.kind_as_str}, " + \
            f"{e.kind_as_str}) index tuple ({s.key}, {x.key}, " + \
            f"{e.key}) for 'out_eff' of ConversionTechs"
        raise exceptions.DataException(key_val, [s, x, e], msg,
                                       module=LOG_MODULE_STR)

    def set_out_eff(self, s: StageId, x: TechId, e: EcId, t: TimeId,
                    out_eff: float) -> None:
        """
        Set the parameter 'out_eff' for a conversion technology's output ec.
        out_eff quantifies the relative output of that ec relative to the
        technology's main input ec. E.g.; a value of 0.5 means that the output
        amount of that ec is identical to half the input amount of the main
        input ec.

        :param s: Stage id
        :type s: StageId
        :param x: Id of conversion technology
        :type x: TechId
        :param e: Id of output ec
        :type e: EcId
        :param t: Time id
        :type t: TimeId
        :param out_eff: Value of parameter out_eff
        :type out_eff: float
        """
        self._check_id(x, ExceptionKey.OUTEFF_SET)
        if (s, x, e) not in self._out_eff:
            self._out_eff[s, x, e] = TimeSeries()
        self._out_eff[s, x, e].set_value(t, out_eff)

    def set_out_eff_def(self, s: StageId, x: TechId, e: EcId,
                        out_eff_def: float) -> None:
        """
        Set the default (with respect to time) parameter 'out_eff' for a
        conversion technology's output ec. out_eff quantifies the relative
        output of that ec relative to the technology's main input ec. E.g.; a
        value of 0.5 means that the output amount of that ec is identical to
        half the input amount of the main input ec.

        :param s: Stage id
        :type s: StageId
        :param x: Id of conversion technology
        :type x: TechId
        :param e: Id of output ec
        :type e: EcId
        :param out_eff_def: Default value of parameter out_eff
        :type out_eff_def: float
        """
        self._check_id(x, ExceptionKey.OUTEFF_SET)
        if (s, x, e) not in self._out_eff:
            self._out_eff[s, x, e] = TimeSeries()
        self._out_eff[s, x, e].def_value = out_eff_def

    def clear_out_eff(self) -> None:
        """
        Remove all data for the parameter 'out_eff' from conversion
        technologies
        """
        for (s, x, e) in self._out_eff:
            self._out_eff[s, x, e].clear()

    # --------------------- #
    # Property: out_sum_min #
    # --------------------- #
    def get_out_sum_min(self, s: StageId, h: HubId, x: TechId) -> float:
        """
        Get the parameter 'out_sum_min' for a conversion technology.
        out_sum_min quantifies the minimal amount of the technology's main
        output ec that has to be output over the entire time horizon.

        :param s: Stage id
        :type s: StageId
        :param h: Hub id
        :type h: HubId
        :param x: Id of conversion technology
        :type x: TechId
        :return: Parameter out_sum_min
        :rtype: float
        """
        self._check_id(x, ExceptionKey.OUTSUMMIN_GET)
        return self._out_sum_min.get((s, h, x), DEF_OUTSUMMIN)

    def set_out_sum_min(self, s: StageId, h: HubId, x: TechId,
                        out_sum_min: float) -> None:
        """
        Set the parameter 'out_sum_min' for a conversion technology.
        out_sum_min quantifies the minimal amount of the technology's main
        output ec that has to be output over the entire time horizon.

        :param s: Stage id
        :type s: StageId
        :param h: Hub id
        :type h: HubId
        :param x: Id of conversion technology
        :type x: TechId
        :param out_sum_min: Parameter out_sum_min
        :type out_sum_min: float
        """
        self._check_id(x, ExceptionKey.OUTSUMMIN_SET)
        self._out_sum_min[s, h, x] = out_sum_min

    # --------------------- #
    # Property: out_sum_max #
    # --------------------- #
    def get_out_sum_max(self, s: StageId, h: HubId, x: TechId) -> float:
        """
        Get the parameter 'out_sum_max' for a conversion technology.
        out_sum_max quantifies the maximal amount of the technology's main
        output ec that can be output over the entire time horizon.

        :param s: Stage id
        :type s: StageId
        :param h: Hub id
        :type h: HubId
        :param x: Id of conversion technology
        :type x: TechId
        :return: Parameter out_sum_max
        :rtype: float
        """
        self._check_id(x, ExceptionKey.OUTSUMMAX_GET)
        return self._out_sum_max.get((s, h, x), DEF_OUTSUMMAX)

    def set_out_sum_max(self, s: StageId, h: HubId, x: TechId,
                        out_sum_max: float) -> None:
        """
        Set the parameter 'out_sum_max' for a conversion technology.
        out_sum_max quantifies the maximal amount of the technology's main
        output ec that can be output over the entire time horizon.

        :param s: Stage id
        :type s: StageId
        :param h: Hub id
        :type h: HubId
        :param x: Id of conversion technology
        :type x: TechId
        :param out_sum_max: Parameter out_sum_max
        :type out_sum_max: float
        """
        self._check_id(x, ExceptionKey.OUTSUMMAX_SET)
        self._out_sum_max[s, h, x] = out_sum_max

    # ---------------------- #
    # Property: availability #
    # ---------------------- #
    def get_availability(self, s: StageId, h: HubId, x: TechId) -> TimeSeries:
        """
        Get the parameter 'availability' for a conversion technology.
        availability is a relative value that scales the amount of available
        capacity for that technology, thereby limiting the technology's
        operation possibility. An availability value of e.g.; 0.5 means that
        only half of the installed technology is available at that time

        :param s: Stage id
        :type s: StageId
        :param h: Hub id
        :type h: HubId
        :param x: Id of conversion technology
        :type x: TechId
        :return: Time series for availability [1]
        :rtype: TimeSeries
        """
        self._check_id(x, ExceptionKey.AVAILABILITY_GET)
        availability = self._availability.get((s, h, x), None)
        if availability is None:
            availability = TimeSeries()
            availability.def_value = DEF_AVAILABILITY
        return availability

    def set_availability(self, s: StageId, h: HubId, x: TechId,
                         t: TimeId, availability: float) -> None:
        """
        Set the parameter 'availability' for a conversion technology.
        availability is a relative value that scales the amount of available
        capacity for that technology, thereby limiting the technology's
        operation possibility. An availability value of e.g.; 0.5 means that
        only half of the installed technology is available at that time

        :param s: Stage id
        :type s: StageId
        :param h: Hub id
        :type h: HubId
        :param x: Id of conversion technology
        :type x: TechId
        :param t: Time id
        :type t: TimeId
        :param availability: availability [1]
        :type availability: float
        """
        self._check_id(x, ExceptionKey.AVAILABILITY_SET)
        if (s, h, x) not in self._availability:
            self._availability[s, h, x] = TimeSeries()
            self._availability[s, h, x].def_value = DEF_AVAILABILITY
        self._availability[s, h, x].set_value(t, availability)

    def set_availability_def(self, s: StageId, h: HubId, x: TechId,
                             availability_def: float) -> None:
        """
        Set the default (with respect to time) parameter 'availability' for a
        conversion technology. availability is a relative value that scales the
        amount of available capacity for that technology, thereby limiting the
        technology's operation possibility. An availability value of e.g.; 0.5
        means that only half of the installed technology is available at that
        time

        :param s: Stage id
        :type s: StageId
        :param h: Hub id
        :type h: HubId
        :param x: Id of conversion technology
        :type x: TechId
        :param availability_def: Default value of availability [1]
        :type availability_def: float
        """
        self._check_id(x, ExceptionKey.AVAILABILITY_SET)
        if (s, h, x) not in self._availability:
            self._availability[s, h, x] = TimeSeries()
        self._availability[s, h, x].def_value = availability_def

    def clear_availability(self) -> None:
        """
        Remove all data for the parameter 'availability' from conversion
        technologies
        """
        for (s, h, x) in self._availability:
            self._availability[s, h, x].clear()

    # ------------------------------- #
    # Secondary property: time_series #
    # ------------------------------- #
    @property
    def time_series(self) -> List[Tuple[TimeSeriesKind, StageId,
                                        Tuple[str, ...], TimeSeries]]:
        """
        Time series profiles in the conversion technology module. This is a
        list of tuples. Each list element has the following list entries: 1)
        ProfileKind of the profile. 2) Stage. 3) Tuple of string identifiers
        specific to the ProfileKind. 4) The TimeSeries itself

        :return: All time series of the conversion technology module
        :rtype: List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...],
            TimeSeries]]
        """
        all_series: List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...],
                               TimeSeries]] = []
        # Output efficiency
        for (s, x, e), series in self._out_eff.items():
            if series.has_values:
                all_series.append((TimeSeriesKind.CONVTECHOUTEFF, s,
                                   (x.key, e.key), series))
        # Availability
        for (s, h, x), series in self._availability.items():
            if series.has_values:
                all_series.append((TimeSeriesKind.CONVTECHAVAIL, s,
                                   (h.key, x.key), series))
        return all_series

    def set_time_series_val(self, kind: TimeSeriesKind, s: StageId,
                            ids: Tuple[str, ...], t: TimeId, value: float
                            ) -> None:
        """
        Set the value for a time series in the conversion technology data
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
        :param value: Value to set
        :type value: float
        """
        if kind == TimeSeriesKind.CONVTECHAVAIL:
            h = HubId(ids[0])
            x = TechId(ids[1])
            self.set_availability(s, h, x, t, value)
        if kind == TimeSeriesKind.CONVTECHOUTEFF:
            x = TechId(ids[0])
            e = EcId(ids[1])
            self.set_out_eff(s, x, e, t, value)

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._ids: Set[TechId] = set()
        self._in_ecs: Dict[TechId, Set[EcId]] = {}
        self._in_ec_main: Dict[TechId, EcId] = {}
        self._in_part: Dict[Tuple[StageId, TechId, EcId], float] = {}
        self._out_ecs: Dict[TechId, Set[EcId]] = {}
        self._out_ec_main: Dict[TechId, EcId] = {}
        self._out_eff: Dict[Tuple[StageId, TechId, EcId], TimeSeries] = {}
        self._opex_per_energy: Dict[Tuple[StageId, TechId], float] = {}
        self._out_sum_min: Dict[Tuple[StageId, HubId, TechId], float] = {}
        self._out_sum_max: Dict[Tuple[StageId, HubId, TechId], float] = {}
        self._availability: Dict[Tuple[StageId, HubId, TechId],
                                 TimeSeries] = {}

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self, stages: Stages, hubs: Hubs, ecs: Ecs,
                 techs: Techs, times: Times) -> None:
        """
        Validate all conversion technology data in this object. Apart from
        sense-checking parameter in terms of quantity, this includes checking
        whether the ids from other data classes used here are known there as
        well.

        :param stages: Stages data class
        :type stages: Stages
        :param hubs: Hubs data class
        :type hubs: Hubs
        :param ecs: ecs data class
        :type ecs: Ecs
        :param techs: Techs data class
        :type techs: Techs
        :param times: Times data class
        :type times: Times
        """
        self._validate_ids(techs)
        self._validate_in_ecs(ecs)
        self._validate_in_ec_main()
        self._validate_in_part(stages, techs)
        self._validate_out_ecs(ecs)
        self._validate_inout_ecs()
        self._validate_out_ec_main()
        self._validate_out_eff(stages, times)
        self._validate_out_sum_min(stages, hubs)
        self._validate_out_sum_max(stages, hubs)
        self._validate_out_sum_minmax()
        self._validate_opex_per_energy(stages)
        self._validate_availability(stages, hubs, times)

    def _validate_ids(self, techs: Techs) -> None:
        exc_key = ExceptionKey.ID_VAL.value
        for x in self._ids:
            # stor_tech not in techs
            if x not in techs.ids:
                msg = f"conv_tech {x} not part of techs"
                raise exceptions.DataException(exc_key, [x], msg,
                                               module=LOG_MODULE_STR)

    def _validate_in_ecs(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.INECS_VAL.value
        for x, in_ecs in self._in_ecs.items():
            # in_ecs must not be empty
            if not in_ecs:
                msg = f"Empty in_ecs[{x}]"
                raise exceptions.DataException(exc_key, [x], msg,
                                               module=LOG_MODULE_STR)
            for e in in_ecs:
                # Unknown ec
                if e not in ecs.ids:
                    msg = f"Unknown in_ec {e} for {x}"
                    raise exceptions.DataException(exc_key, [x, e], msg,
                                                   module=LOG_MODULE_STR)

    def _validate_in_ec_main(self) -> None:
        exc_key = ExceptionKey.INECMAIN_VAL.value
        for x, in_ec_main in self._in_ec_main.items():
            in_ecs = self._in_ecs.get(x, set())
            if in_ec_main not in in_ecs:
                msg = (f"in_ec_main[{x}] = {in_ec_main} is not part of "
                       f"in_ecs[{x}] = {in_ecs}")
                raise exceptions.DataException(exc_key, [x, in_ec_main], msg,
                                               module=LOG_MODULE_STR)

    def _validate_in_part(self, stages: Stages, techs: Techs) -> None:
        exc_key = ExceptionKey.INPART_VAL.value
        for (s, x, e), in_part in self._in_part.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in in_part[{s}, {x}, {e}]"
                raise exceptions.DataException(exc_key, [s, x, e], msg,
                                               module=LOG_MODULE_STR)
            # e must be part of in_ecs
            in_ecs = self._in_ecs.get(x, set())
            if e not in in_ecs:
                msg = (f"ec {e} of in_part[{s}, {x}, {e}] is not part of "
                       f"in_ecs[{x}] = {in_ecs}")
                raise exceptions.DataException(exc_key, [s, x, e], msg,
                                               module=LOG_MODULE_STR)
            # in_part must be nonnegative
            if in_part < 0:
                msg = f"{in_part} = in_part[{s}, {x}, {e}] < 0"
                raise exceptions.DataException(exc_key, [s, x, e], msg,
                                               module=LOG_MODULE_STR)
            # in_part usually not zero
            if in_part < EPS_ZEROCHECK:
                msg = f"{in_part} = in_part[{s}, {x}, {e}] ~ 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)
        # Sum of in_parts must be larger than zero
        for x in self.ids:
            for s in techs.get_allowed_stages(x):
                in_part_total = sum(self.get_in_part(s, x, e)
                                    for e in self.get_in_ecs(x))
                if in_part_total < EPS_ZEROCHECK:
                    msg = (f"Sum of in_parts for stage {s} and conv_tech {x} "
                           "is zero")
                    raise exceptions.DataException(exc_key, [s, x], msg,
                                                   module=LOG_MODULE_STR)

    def _validate_out_ecs(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.OUTECS_VAL.value
        for x, out_ecs in self._out_ecs.items():
            # out_ecs must not be empty
            if not out_ecs:
                msg = f"Empty out_ecs[{x}]"
                raise exceptions.DataException(exc_key, [x], msg,
                                               module=LOG_MODULE_STR)
            for e in out_ecs:
                # Unknown ec
                if e not in ecs.ids:
                    msg = f"Unknown out_ec {e} for {x}"
                    raise exceptions.DataException(exc_key, [x, e], msg,
                                                   module=LOG_MODULE_STR)

    def _validate_inout_ecs(self) -> None:
        for x in self.ids:
            in_ecs = self.get_in_ecs(x)
            out_ecs = self.get_out_ecs(x)
            common_ecs = in_ecs.intersection(out_ecs)
            if common_ecs:
                msg = (f"For {x}, the ecs {common_ecs} "
                       "are both inputs and outputs")
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_out_ec_main(self) -> None:
        exc_key = ExceptionKey.OUTECMAIN_VAL.value
        for x, out_ec_main in self._out_ec_main.items():
            out_ecs = self._out_ecs.get(x, set())
            if out_ec_main not in out_ecs:
                msg = (f"out_ec_main[{x}] = {out_ec_main} is not part of "
                       f"out_ecs[{x}] = {out_ecs}")
                raise exceptions.DataException(exc_key, [x, out_ec_main], msg,
                                               module=LOG_MODULE_STR)

    def _validate_out_eff(self, stages: Stages, times: Times) -> None:
        exc_key = ExceptionKey.OUTEFF_VAL.value
        for (s, x, e), out_eff in self._out_eff.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in out_eff[{s}, {x}, {e}]"
                raise exceptions.DataException(exc_key, [s, x, e], msg,
                                               module=LOG_MODULE_STR)
            # e must be part of out_ecs
            out_ecs = self._out_ecs.get(x, set())
            if e not in out_ecs:
                msg = (f"ec {e} of out_eff[{s}, {x}, {e}] is not part of "
                       f"out_ecs[{x}] = {out_ecs}")
                raise exceptions.DataException(exc_key, [s, x, e], msg,
                                               module=LOG_MODULE_STR)
            # Time values
            if out_eff.has_values:
                # Unknown time ids
                out_eff.validate(times, exc_key)
                # out_eff must not be negative
                for t in times.ids:
                    if out_eff.get_value(t) < 0:
                        msg = (f"{out_eff.get_value(t)} = out_eff"
                               f"[{s}, {x}, {e}][{t}] < 0")
                        raise exceptions.DataException(exc_key, [s, x, e, t],
                            msg, module=LOG_MODULE_STR)
            # Default values
            if not out_eff.has_values:
                out_eff_def = out_eff.def_value
                assert out_eff_def is not None
                # out_eff must be nonnegative
                if out_eff_def < 0:
                    msg = (f"{out_eff_def} = out_eff_def"
                           f"[{s}, {x}, {e}] < 0")
                    raise exceptions.DataException(exc_key, [s, x, e], msg,
                                                module=LOG_MODULE_STR)
                # out_eff usually not zero
                if out_eff_def < EPS_ZEROCHECK:
                    msg = (f"{out_eff_def} = out_eff_def"
                           f"[{s}, {x}, {e}] ~ 0")
                    logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_opex_per_energy(self, stages: Stages) -> None:
        exc_key = ExceptionKey.OPEXPERENERGY_VAL.value
        for (s, x), opex_per_energy in self._opex_per_energy.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in opex_per_energy[{s}, {x}]"
                raise exceptions.DataException(exc_key, [s], msg,
                                               module=LOG_MODULE_STR)
            # opex_per_energy usually nonnegative
            if opex_per_energy < 0:
                msg = f"{opex_per_energy} = opex_per_energy[{s}, {x}] < 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_out_sum_min(self, stages: Stages, hubs: Hubs) -> None:
        exc_key = ExceptionKey.OUTSUMMIN_VAL.value
        for (s, h, x), out_sum_min in self._out_sum_min.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in out_sum_min[{s}, {h}, {x}]"
                raise exceptions.DataException(exc_key, [s, h, x], msg,
                                               module=LOG_MODULE_STR)
            # Unknown hub
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in out_sum_min[{s}, {h}, {x}]"
                raise exceptions.DataException(exc_key, [s, h, x], msg,
                                               module=LOG_MODULE_STR)
            # out_sum_min is usually nonnegative
            if out_sum_min < 0:
                msg = f"{out_sum_min} = out_sum_min[{s}, {h}, {x}] < 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_out_sum_max(self, stages: Stages, hubs: Hubs) -> None:
        exc_key = ExceptionKey.OUTSUMMAX_VAL.value
        for (s, h, x), out_sum_max in self._out_sum_max.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in out_sum_max[{s}, {h}, {x}]"
                raise exceptions.DataException(exc_key, [s, h, x], msg,
                                               module=LOG_MODULE_STR)
            # Unknown hub
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in out_sum_max[{s}, {h}, {x}]"
                raise exceptions.DataException(exc_key, [s, h, x], msg,
                                               module=LOG_MODULE_STR)
            # out_sum_max must be nonnegative
            if out_sum_max < 0:
                msg = f"{out_sum_max} = out_sum_max[{s}, {h}, {x}] < 0"
                raise exceptions.DataException(exc_key, [s, h, x], msg,
                                               module=LOG_MODULE_STR)

    def _validate_out_sum_minmax(self) -> None:
        exc_key = ExceptionKey.OUTSUMMINMAX_VAL.value
        keys = set(self._out_sum_min.keys()
                   ).union(set(self._out_sum_max.keys()))
        for (s, h, x) in keys:
            out_sum_min = self.get_out_sum_min(s, h, x)
            out_sum_max = self.get_out_sum_max(s, h, x)
            # out_sum_min must not be larger than out_sum_max
            if out_sum_min > out_sum_max:
                msg = (f"{out_sum_min} = out_sum_min[{s}, {h}, {x}] > "
                       f"out_sum_max[{s}, {h}, {x}] = {out_sum_max}")
                raise exceptions.DataException(exc_key, [s, h, x], msg,
                                               module=LOG_MODULE_STR)

    def _validate_availability(self, stages: Stages, hubs: Hubs,
                               times: Times) -> None:
        exc_key = ExceptionKey.AVAILABILITY_VAL.value
        for (s, h, x), availability in self._availability.items():
            # Unknown stage id
            if s not in stages.ids:
                msg = f"Unknown stage {s} in availability[{s}, {h}, {x}]"
                raise exceptions.DataException(exc_key, [s, h, x], msg,
                                               module=LOG_MODULE_STR)
            # Unknown hub id
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in availability[{s}, {h}, {x}]"
                raise exceptions.DataException(exc_key, [s, h, x], msg,
                                               module=LOG_MODULE_STR)
            # Time values
            if availability.has_values:
                # Unknown time ids
                availability.validate(times, exc_key, module=LOG_MODULE_STR)
                # Availability values must be nonnegative (time values)
                for t in times.ids:
                    if availability.get_value(t) < 0:
                        msg = (f"{availability.get_value(t)} = availability["
                            f"{s}, {h}, {x}][{t}] < 0")
                        raise exceptions.DataException(exc_key, [s, h, x], msg,
                                                       module=LOG_MODULE_STR)
                # Availability values should be smaller than 1 (time values)
                for t in times.ids:
                    if availability.get_value(t) > 1:
                        msg = (f"{availability.get_value(t)} = availability["
                            f"{s}, {h}, {x}][{t}] > 1")
                        logging.log_warning(msg, module=LOG_MODULE_STR)
                        break
            # Default values
            if not availability.has_values:
                availability_def = availability.def_value
                assert availability_def is not None
                # Availability values must be nonnegative (default value)
                if availability_def < 0:
                    msg = (f"{availability_def} = availability_def["
                        f"{s}, {h}, {x}] < 0")
                    raise exceptions.DataException(exc_key, [s, h, x], msg,
                                                   module=LOG_MODULE_STR)
                # Constant availability usually not zero (default value)
                if availability_def < EPS_ZEROCHECK:
                    msg = (f"{availability_def} = availability_def["
                        f"{s}, {h}, {x}] ~ 0")
                    logging.log_warning(msg, module=LOG_MODULE_STR)
                # Availability values usually smaller than 1 (default value)
                if availability_def > 1:
                    msg = (
                        f"{availability_def} = availability["
                        f"{s}, {h}, {x}] > 1")
                    logging.log_warning(msg, module=LOG_MODULE_STR)

    # ---------- #
    # Id checker #
    # ---------- #
    def _check_id(self, x: TechId, key: ExceptionKey) -> None:
        if x not in self._ids:
            raise exceptions.UnknownIdException(key.value, x,
                                                module=LOG_MODULE_STR)


def copy_over_conv_tech(x: TechId, src: ConversionTechs,
                        tar: ConversionTechs, stages: Stages, hubs: Hubs,
                        times: Times) -> None:
    """
    Copy a conversion technology from one ConversionTechs data object to
    another.

    :param x: Conversion technology id to be copied
    :type x: TechId
    :param src: Source data object
    :type src: ConversionTechs
    :param tar: Target data object
    :type tar: ConversionTechs
    :param stages: Stages
    :type stages: Stages
    :param hubs: Hubs
    :type hubs: Hubs
    :param times: Times
    :type times: Times
    """
    # id
    if x not in src.ids:
        raise exceptions.DataException(ExceptionKey.COPYOVERTECH.value, [x],
            (f"Failed to copy {x} from ConversionTechs instance "
             f"because {x} is not part of that ConversionTechs instance"),
            module=LOG_MODULE_STR)
    if x in tar.ids:
        raise exceptions.DataException(ExceptionKey.COPYOVERTECH.value, [x],
            (f"Failed to copy {x} to ConversionTechs instance because {x} is "
             "already part of that ConversionTechs instance"),
            module=LOG_MODULE_STR)
    tar.add_id(x)
    # in_ecs
    for e in src.get_in_ecs(x):
        tar.add_in_ec(x, e)
    tar.set_in_ec_main(x, src.get_in_ec_main(x))
    # in_part
    for s in stages.ids:
        for e in src.get_in_ecs(x):
            tar.set_in_part(s, x, e, src.get_in_part(s, x, e))
    # out_ecs
    for e in src.get_out_ecs(x):
        tar.add_out_ec(x, e)
    tar.set_out_ec_main(x, src.get_out_ec_main(x))
    # out_eff
    for s in stages.ids:
        for e in src.get_out_ecs(x):
            out_eff_def = src.get_out_eff(s, x, e).def_value
            assert out_eff_def is not None
            tar.set_out_eff_def(s, x, e, out_eff_def)
            if src.get_out_eff(s, x, e).has_values:
                for t in times.ids:
                    tar.set_out_eff(s, x, e, t,
                                    src.get_out_eff(s, x, e).get_value(t))
    # opex_per_energy
    for s in stages.ids:
        tar.set_opex_per_energy(s, x, src.get_opex_per_energy(s, x))
    # out_sum_minmax
    for s in stages.ids:
        for h in hubs.ids:
            tar.set_out_sum_min(s, h, x, src.get_out_sum_min(s, h, x))
            tar.set_out_sum_max(s, h, x, src.get_out_sum_max(s, h, x))
    # availability
    for s in stages.ids:
        for h in hubs.ids:
            availability_def = src.get_availability(s, h, x).def_value
            assert availability_def is not None
            tar.set_availability_def(s, h, x, availability_def)
            if src.get_availability(s, h, x).has_values:
                for t in times.ids:
                    tar.set_availability(s, h, x, t,
                        src.get_availability(s, h, x).get_value(t))
