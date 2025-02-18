"""
Heatpump technology data module
"""
from enum import Enum
from typing import Dict, List, Set, Tuple
import collections
from ehubx.core.common import TimeSeriesKind, celcius_to_kelvin, EPS_ZEROCHECK
from ehubx.core import logging
from ehubx.data.index import Index
from ehubx.data.stage_data import Stages, StageId
from ehubx.data.hub_data import Hubs, HubId
from ehubx.data.tech_data import Techs, TechId
from ehubx.data.ec_data import Ecs, EcId
from ehubx.data.time_data import Times, TimeId
from ehubx.data.time_series import TimeSeries
from ehubx.data import exceptions


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the heatpump technology data
    module
    """
    ID_ADD = "adding to 'ids' of HeatpumpTechs"
    ID_REMOVE = "removing from 'ids' of HeatpumpTechs"
    ID_VAL = "validating 'ids' of HeatpumpTechs"
    ECEL_SET = "setting 'ec_el' of HeatpumpTechs"
    ECEL_GET = "getting 'ec_el' from HeatpumpTechs"
    ECEL_VAL = "validating 'ec_el' of HeatpumpTechs"
    ECHTIN_SET = "setting 'ec_ht_in' of HeatpumpTechs"
    ECHTIN_GET = "getting 'ec_ht_in' from HeatpumpTechs"
    ECHTIN_VAL = "validating 'ec_ht_in' of HeatpumpTechs"
    ECCOIN_SET = "setting 'ec_co_in' of HeatpumpTechs"
    ECCOIN_GET = "getting 'ec_co_in' from HeatpumpTechs"
    ECCOIN_VAL = "validating 'ec_co_in' of HeatpumpTechs"
    ECHTOUT_SET = "setting 'ec_ht_out' of HeatpumpTechs"
    ECHTOUT_GET = "getting 'ec_ht_out' from HeatpumpTechs"
    ECHTOUT_VAL = "validating 'ec_ht_out' of HeatpumpTechs"
    ECCOOUT_SET = "setting 'ec_co_out' of HeatpumpTechs"
    ECCOOUT_GET = "getting 'ec_co_out' from HeatpumpTechs"
    ECCOOUT_VAL = "validating 'ec_co_out' of HeatpumpTechs"
    ECS_VAL = "validating ecs of HeatpumpTechs"
    TEMPHTIN_SET = "setting 'temp_ht_in' of HeatpumpTechs"
    TEMPHTIN_DEFSET = "setting default 'temp_ht_in' of HeatpumpTechs"
    TEMPHTIN_GET = "getting 'temp_ht_in' from HeatpumpTechs"
    TEMPHTIN_VAL = "validating 'temp_ht_in' of HeatpumpTechs"
    TEMPHTOUT_SET = "setting 'temp_ht_out' of HeatpumpTechs"
    TEMPHTOUT_DEFSET = "setting default 'temp_ht_out' of HeatpumpTechs"
    TEMPHTOUT_GET = "getting 'temp_ht_out' from HeatpumpTechs"
    TEMPHTOUT_VAL = "validating 'temp_ht_out' of HeatpumpTechs"
    TEMPS_VAL = "validating temperatures of HeatpumpTechs"
    COPFACTOR_SET = "setting 'cop_factor' of HeatpumpTechs"
    COPFACTOR_GET = "getting 'cop_factor' from HeatpumpTechs"
    COPFACTOR_VAL = "validating 'cop_factor' of HeatpumpTechs"
    COP_SET = "setting 'cop' of HeatpumpTechs"
    COP_DEFSET = "setting default 'cop' of HeatpumpTechs"
    COP_GET = "getting 'cop' from HeatpumpTechs"
    COP_VAL = "validating 'cop' of HeatpumpTechs"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/hp_tech"
"""String identifying the heatpump technology data module for logging
purposes"""

DEF_COPFACTOR: float = 0.5
"""Default value for parameter 'cop_factor' in the heatpump technology data
module"""


class HeatpumpTechs:
    """
    Class for heatpump technology data. Manages heatpump technology ids,
    contains getters and setters for heatpump technology parameters and
    validation methods to control data integrity
    """

    # ------------- #
    # Property: ids #
    # ------------- #
    @property
    def ids(self) -> Set[TechId]:
        """
        Set of known heatpump technology ids
        """
        return self._ids

    @property
    def ids_in_order(self) -> List[TechId]:
        """
        List of known heat pump tech ids in alphabetical order
        """
        ids = list(self.ids)
        ids.sort(key=lambda x: x.key)
        return ids

    def add_id(self, x: TechId) -> None:
        """
        Add a new heatpump technology id

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
        """
        Get the electricity ec powering the heat pump's compressor. This is a
        mandatory parameter.

        :param x: Heat pump technology
        :type x: TechId
        :return: Electricity ec
        :rtype: EcId
        """
        self._check_id(x, ExceptionKey.ECEL_GET)
        if x not in self._ec_el:
            raise exceptions.MissingIdException(
                ExceptionKey.ECEL_GET.value, x, module=LOG_MODULE_STR)
        return self._ec_el[x]

    def set_ec_el(self, x: TechId, e: EcId) -> None:
        """
        Set the electricity ec powering the heat pump's compressor. This is a
        mandatory parameter.

        :param x: Heat pump technology
        :type x: TechId
        :param e: Electricity ec
        :type e: EcId
        """
        self._check_id(x, ExceptionKey.ECEL_SET)
        self._ec_el[x] = e

    # ------------------ #
    # Property: ec_ht_in #
    # ------------------ #
    def get_ec_ht_in(self, x: TechId) -> EcId:
        """
        Get the ec for the input heating energy, i.e.; evaporator energy for a
        heat pump in heating mode.

        :param x: Heat pump technology
        :type x: TechId
        :return: Input heating ec
        :rtype: EcId
        """
        self._check_id(x, ExceptionKey.ECHTIN_GET)
        if x not in self._ec_ht_in:
            raise exceptions.MissingIdException(
                ExceptionKey.ECHTIN_GET.value, x, module=LOG_MODULE_STR)
        return self._ec_ht_in[x]

    def set_ec_ht_in(self, x: TechId, e: EcId) -> None:
        """
        Set the ec for the input heating energy, i.e.; evaporator energy for a
        heat pump in heating mode.

        :param x: Heat pump technology
        :type x: TechId
        :param e: Input heating ec
        :type e: EcId
        """
        self._check_id(x, ExceptionKey.ECHTIN_SET)
        self._ec_ht_in[x] = e

    # ------------------ #
    # Property: ec_co_in #
    # ------------------ #
    def get_ec_co_in(self, x: TechId) -> EcId:
        """
        Get the ec for the input cooling inergy, i.e.; condenser energy for a
        heat pump in cooling mode.

        :param x: Heat pump technology
        :type x: TechId
        :return: Input cooling ec
        :rtype: EcId
        """
        self._check_id(x, ExceptionKey.ECCOIN_GET)
        if x not in self._ec_co_in:
            raise exceptions.MissingIdException(
                ExceptionKey.ECCOIN_GET.value, x, module=LOG_MODULE_STR)
        return self._ec_co_in[x]

    def set_ec_co_in(self, x: TechId, e: EcId) -> None:
        """
        Set the ec for the input cooling inergy, i.e.; condenser energy for a
        heat pump in cooling mode.

        :param x: Heat pump technology
        :type x: TechId
        :param e: Input cooling ec
        :type e: EcId
        """
        self._check_id(x, ExceptionKey.ECCOIN_SET)
        self._ec_co_in[x] = e

    # ------------------- #
    # Property: ec_ht_out #
    # ------------------- #
    def get_ec_ht_out(self, x: TechId) -> EcId:
        """
        Get the ec for the output heating energy, i.e.; condenser energy for a
        heat pump in heating mode.

        :param x: Heat pump technology
        :type x: TechId
        :return: Output heating ec
        :rtype: EcId
        """
        self._check_id(x, ExceptionKey.ECHTOUT_GET)
        if x not in self._ec_ht_out:
            raise exceptions.MissingIdException(
                ExceptionKey.ECHTOUT_GET.value, x, module=LOG_MODULE_STR)
        return self._ec_ht_out[x]

    def set_ec_ht_out(self, x: TechId, e: EcId) -> None:
        """
        Set the ec for the output heating energy, i.e.; condenser energy for a
        heat pump in heating mode.

        :param x: Heat pump technology
        :type x: TechId
        :param e: Output heating ec
        :type e: EcId
        """
        self._check_id(x, ExceptionKey.ECHTOUT_SET)
        self._ec_ht_out[x] = e

    # ------------------- #
    # Property: ec_co_out #
    # ------------------- #
    def get_ec_co_out(self, x: TechId) -> EcId:
        """
        Get the ec for the output cooling inergy, i.e.; evaporator energy for a
        heat pump in cooling mode.

        :param x: Heat pump technology
        :type x: TechId
        :return: Output cooling ec
        :rtype: EcId
        """
        self._check_id(x, ExceptionKey.ECCOOUT_GET)
        if x not in self._ec_co_out:
            raise exceptions.MissingIdException(
                ExceptionKey.ECCOOUT_GET.value, x, module=LOG_MODULE_STR)
        return self._ec_co_out[x]

    def set_ec_co_out(self, x: TechId, e: EcId) -> None:
        """
        Set the ec for the output cooling inergy, i.e.; evaporator energy for a
        heat pump in cooling mode.

        :param x: Heat pump technology
        :type x: TechId
        :param e: Output cooling ec
        :type e: EcId
        """
        self._check_id(x, ExceptionKey.ECCOOUT_SET)
        self._ec_co_out[x] = e

    # -------------------- #
    # Property: temp_ht_in #
    # -------------------- #
    def get_temp_ht_in(self, s: StageId, h: HubId, x: TechId) -> TimeSeries:
        """
        Get the parameter 'temp_heat_in' which denotes the temperature of the
        heating input medium, i.e.; the temperature of the warm evaporator
        side. This is an optional parameter but it becomes mandatory if
        the parameter cop is not specified, since temperatures are then used
        to calculate the COP.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: Heat pump technology
        :type x: TechId
        :return: Temperatures of warm evaporator side [°C]
        :rtype: TimeSeries
        """
        self._check_id(x, ExceptionKey.TEMPHTIN_GET)
        if (s, h, x) not in self._temp_ht_in:
            raise exceptions.MissingIdsException(
                ExceptionKey.TEMPHTIN_GET.value, [s, h, x],
                module=LOG_MODULE_STR)
        return self._temp_ht_in[s, h, x]

    def set_temp_ht_in(self, s: StageId, h: HubId, x: TechId, t: TimeId,
                       temp_ht_in: float) -> None:
        """
        At a specific time, set the parameter 'temp_heat_in' which denotes the
        temperature of the heating input medium, i.e.; the temperature of the
        warm evaporator side. This is an optional parameter but it becomes
        mandatory if the parameter cop is not specified, since temperatures are
        then used to calculate the COP.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: Heat pump technology
        :type x: TechId
        :param t: Time
        :type t: TimeId
        :param temp_ht_in: Temperature of warm evaporator side [°C]
        :type temp_ht_in: float
        """
        self._check_id(x, ExceptionKey.TEMPHTIN_SET)
        if (s, h, x) not in self._temp_ht_in:
            self._temp_ht_in[s, h, x] = TimeSeries()
        self._temp_ht_in[s, h, x].set_value(t, temp_ht_in)

    def set_temp_ht_in_def(self, s: StageId, h: HubId, x: TechId,
                           temp_ht_in_def: float) -> None:
        """
        Set the default (with respect to time) value for the parameter
        'temp_heat_in' which denotes  the temperature of the heating input
        medium, i.e.; the temperature of the warm evaporator side. This is an
        optional parameter but it becomes mandatory if the parameter cop is not
        specified, since temperatures are then used to calculate the COP.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: Heat pump technology
        :type x: TechId
        :param temp_ht_in_def: Default temperature of warm evaporator side [°C]
        :type temp_ht_in_def: float
        """
        self._check_id(x, ExceptionKey.TEMPHTIN_DEFSET)
        if (s, h, x) not in self._temp_ht_in:
            self._temp_ht_in[s, h, x] = TimeSeries()
        self._temp_ht_in[s, h, x].def_value = temp_ht_in_def

    def has_temp_ht_in(self, s: StageId, h: HubId, x: TechId) -> bool:
        """
        Returns whether the parameter 'temp_ht_in' has been set.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: Heat pump technology
        :type x: TechId
        :return: Whether temp_ht_in has been set
        :rtype: bool
        """
        return ((s, h, x) in self._temp_ht_in)

    # --------------------- #
    # Property: temp_ht_out #
    # --------------------- #
    def get_temp_ht_out(self, s: StageId, h: HubId, x: TechId) -> TimeSeries:
        """
        Get the parameter 'temp_heat_out' which denotes the temperature of the
        heating output medium, i.e.; the temperature of the warm condenser
        side. This is an optional parameter but it becomes mandatory if
        the parameter cop is not specified, since temperatures are then used
        to calculate the COP.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: Heat pump technology
        :type x: TechId
        :return: Temperatures of warm condenser side [°C]
        :rtype: TimeSeries
        """
        self._check_id(x, ExceptionKey.TEMPHTOUT_GET)
        if (s, h, x) not in self._temp_ht_out:
            raise exceptions.MissingIdsException(
                ExceptionKey.TEMPHTOUT_GET.value, [s, h, x],
                module=LOG_MODULE_STR)
        return self._temp_ht_out[s, h, x]

    def set_temp_ht_out(self, s: StageId, h: HubId, x: TechId, t: TimeId,
                        temp_ht_out: float) -> None:
        """
        At a specific time, set the parameter 'temp_heat_out' which denotes the
        temperature of the heating output medium, i.e.; the temperature of the
        warm condenser side. This is an optional parameter but it becomes
        mandatory if the parameter cop is not specified, since temperatures are
        then used to calculate the COP.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: Heat pump technology
        :type x: TechId
        :param t: Time
        :type t: TimeId
        :param temp_ht_out: Temperature of warm condenser side [°C]
        :type temp_ht_out: float
        """
        self._check_id(x, ExceptionKey.TEMPHTOUT_SET)
        if (s, h, x) not in self._temp_ht_out:
            self._temp_ht_out[s, h, x] = TimeSeries()
        self._temp_ht_out[s, h, x].set_value(t, temp_ht_out)

    def set_temp_ht_out_def(self, s: StageId, h: HubId, x: TechId,
                            temp_ht_out_def: float) -> None:
        """
        Set the default (with respect to time) value for the parameter
        'temp_heat_out' which denotes the temperature of the
        heating output medium, i.e.; the temperature of the warm condenser
        side. This is an optional parameter but it becomes mandatory if
        the parameter cop is not specified, since temperatures are then used
        to calculate the COP.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: Heat pump technology
        :type x: TechId
        :param temp_ht_out_def: Default temperature of warm condenser side [°C]
        :type temp_ht_out_def: float
        """
        self._check_id(x, ExceptionKey.TEMPHTOUT_DEFSET)
        if (s, h, x) not in self._temp_ht_out:
            self._temp_ht_out[s, h, x] = TimeSeries()
        self._temp_ht_out[s, h, x].def_value = temp_ht_out_def

    def has_temp_ht_out(self, s: StageId, h: HubId, x: TechId) -> bool:
        """
        Returns whether the parameter 'temp_ht_out' has been set.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: Heat pump technology
        :type x: TechId
        :return: Whether temp_ht_out has been set
        :rtype: bool
        """
        return ((s, h, x) in self._temp_ht_out)

    # -------------------- #
    # Property: cop_factor #
    # -------------------- #
    def get_cop_factor(self, s: StageId, x: TechId) -> float:
        """
        Get the parameter 'cop_factor' which denotes a typical scaling quotient
        between the heat pump's actual COP and the theoretical Carnot
        efficiency. This is an optional parameter with a default value of 0.5.

        :param s: Stage
        :type s: StageId
        :param x: Heat pump technology
        :type x: TechId
        :return: Quotient between actual COP and Carnot efficiency [1]
        :rtype: float
        """
        self._check_id(x, ExceptionKey.COPFACTOR_GET)
        cop_factor = self._cop_factor.get((s, x), DEF_COPFACTOR)
        return cop_factor

    def set_cop_factor(self, s: StageId, x: TechId, cop_factor: float) -> None:
        """
        Set the parameter 'cop_factor' which denotes a typical scaling quotient
        between the heat pump's actual COP and the theoretical Carnot
        efficiency. This is an optional parameter with a default value of 0.5.

        :param s: Stage
        :type s: StageId
        :param x: Heat pump technology
        :type x: TechId
        :param cop_factor: Quotient between actual COP and Carnot efficiency
            [1]
        :type cop_factor: float
        """
        self._check_id(x, ExceptionKey.COPFACTOR_SET)
        self._cop_factor[s, x] = cop_factor

    def has_cop_factor(self, s: StageId, x: TechId) -> bool:
        """
        Returns whether the parameter 'cop_factor' has been set.

        :param s: Stage
        :type s: StageId
        :param x: Heat pump technology
        :type x: TechId
        :return: Whether cop_factor has been set
        :rtype: bool
        """
        return ((s, x) in self._cop_factor)

    # ------------- #
    # Property: cop #
    # ------------- #
    def get_cop(self, s: StageId, h: HubId, x: TechId,
                times: Times) -> TimeSeries:
        """
        Get the parameter 'cop' which describes the Coefficient of
        Performance (COP); a quotient between a heat pump's condenser power
        (i.e.; heating output or cooling input power) and the heat pump's
        electricity consumption. This is the primary way that ehubX will try to
        obtain the COP. If 'cop' is not specified, the parameters 'temp_ht_in',
        'temp_co_in', 'temp_ht_out', 'temp_co_in', and 'cop_factor' need to be
        specified instead to calculate the COP.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: Heat pump technology
        :type x: TechId
        :param times: Times
        :type times: Times
        :return: COP values [1]
        :rtype: TimeSeries
        """
        self._check_id(x, ExceptionKey.COP_GET)
        # COP parameter not present
        if (s, h, x) not in self._cop:
            # Try to compute COP using adjusted Carnot efficiency
            if ((s, h, x) in self._temp_ht_in
                    and (s, h, x) in self._temp_ht_out):
                temp_ht_in = self.get_temp_ht_in(s, h, x)
                temp_ht_out = self.get_temp_ht_out(s, h, x)
                cop_factor = self.get_cop_factor(s, x)
                cop = TimeSeries()
                # Temperature data is time-dependent
                if (temp_ht_in.has_values or temp_ht_out.has_values):
                    for t in times.ids:
                        temp_ht_in_k = celcius_to_kelvin(
                            temp_ht_in.get_value(t))
                        temp_ht_out_k = celcius_to_kelvin(
                            temp_ht_out.get_value(t))
                        cop_t = (cop_factor * temp_ht_out_k
                                / (temp_ht_out_k - temp_ht_in_k))
                        cop.set_value(t, cop_t)
                    return cop
                # Temperature data is time-independent
                assert temp_ht_out.def_value is not None
                assert temp_ht_in.def_value is not None
                temp_ht_in_k = celcius_to_kelvin(temp_ht_in.def_value)
                temp_ht_out_k = celcius_to_kelvin(temp_ht_out.def_value)
                cop_def = (cop_factor * temp_ht_out_k
                           / (temp_ht_out_k - temp_ht_in_k))
                cop.def_value = cop_def
                return cop
            # Temperature data not present -> exception
            msg = (f"Failed to get cop for stage {s}, hub {h} and heat pump "
                   f"tech {x}. Neither is the value set explicitly nor do all "
                   "temperature values exist to compute the value")
            raise exceptions.DataException(ExceptionKey.COP_GET.value,
                                           [s, h, x], msg,
                                           module=LOG_MODULE_STR)
        # Return existing COP parameter
        return self._cop[s, h, x]

    def set_cop(self, s: StageId, h: HubId, x: TechId, t: TimeId,
                cop: float) -> None:
        """
        At a specific time, set the parameter 'cop' which describes the
        Coefficient of Performance (COP); a quotient between a heat pump's
        condenser power (i.e.; heating output or cooling input power) and the
        heat pump's electricity consumption. This is the primary way that ehubX
        will try to obtain the COP. If 'cop' is not specified, the parameters
        'temp_ht_in', 'temp_co_in', 'temp_ht_out', 'temp_co_in', and
        'cop_factor' need to be specified instead to calculate the COP.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: Heat pump technology
        :type x: TechId
        :param cop: COP value [1]
        :type cop: float
        """
        self._check_id(x, ExceptionKey.COP_SET)
        if (s, h, x) not in self._cop:
            self._cop[s, h, x] = TimeSeries()
        self._cop[s, h, x].set_value(t, cop)

    def set_cop_def(self, s: StageId, h: HubId, x: TechId,
                    cop_def: float) -> None:
        """
        Set the default (with respect to time) value for the parameter 'cop'
        which describes the Coefficient of Performance (COP); a quotient
        between a heat pump's condenser power (i.e.; heating output or cooling
        input power) and the heat pump's electricity consumption. This is the
        primary way that ehubX will try to obtain the COP. If 'cop' is not
        specified, the parameters 'temp_ht_in', 'temp_co_in', 'temp_ht_out',
        'temp_co_in', and 'cop_factor' need to be specified instead to
        calculate the COP.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param x: Heat pump technology
        :type x: TechId
        :param cop_def: Default COP value [1]
        :type cop_def: float
        """
        self._check_id(x, ExceptionKey.COP_SET)
        if (s, h, x) not in self._cop:
            self._cop[s, h, x] = TimeSeries()
        self._cop[s, h, x].def_value = cop_def

    # ------------------------------- #
    # Secondary property: time_series #
    # ------------------------------- #
    @property
    def time_series(self) -> List[Tuple[TimeSeriesKind, StageId,
                                        Tuple[str, ...], TimeSeries]]:
        """
        Time series profiles in the heat pump technology module. This is a
        list of tuples. Each list element has the following list entries: 1)
        ProfileKind of the profile. 2) Stage. 3) Tuple of string identifiers
        specific to the ProfileKind. 4) The TimeSeries of the profile

        :return: All time series of the heat pump technology module
        :rtype: List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...],
            TimeSeries]]
        """
        all_series: List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...],
                               TimeSeries]] = []
        # COP
        for (s, h, x), series in self._cop.items():
            if series.has_values:
                all_series.append((TimeSeriesKind.HPTECHCOP, s,
                                   (h.key, x.key), series))
        # Temperature of heat intake
        for (s, h, x), series in self._temp_ht_in.items():
            if series.has_values:
                all_series.append((TimeSeriesKind.HPTECHTEMPHTIN, s,
                                   (h.key, x.key), series))
        # Temperature of heat output
        for (s, h, x), series in self._temp_ht_out.items():
            if series.has_values:
                all_series.append((TimeSeriesKind.HPTECHTEMPHTOUT, s,
                                   (h.key, x.key), series))
        return all_series

    def set_time_series_val(self, kind: TimeSeriesKind, s: StageId,
                            ids: Tuple[str, ...], t: TimeId, value: float
                            ) -> None:
        """
        Set the value for a time series in the heatpump technology data
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
        if kind == TimeSeriesKind.HPTECHCOP:
            h = HubId(ids[0])
            x = TechId(ids[1])
            self.set_cop(s, h, x, t, value)
        if kind == TimeSeriesKind.HPTECHTEMPHTIN:
            h = HubId(ids[0])
            x = TechId(ids[1])
            self.set_temp_ht_in(s, h, x, t, value)
        if kind == TimeSeriesKind.HPTECHTEMPHTOUT:
            h = HubId(ids[0])
            x = TechId(ids[1])
            self.set_temp_ht_out(s, h, x, t, value)

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._ids: Set[TechId] = set()
        self._ec_el: Dict[TechId, EcId] = {}
        self._ec_ht_in: Dict[TechId, EcId] = {}
        self._ec_co_in: Dict[TechId, EcId] = {}
        self._ec_ht_out: Dict[TechId, EcId] = {}
        self._ec_co_out: Dict[TechId, EcId] = {}
        self._cop: Dict[Tuple[StageId, HubId, TechId], TimeSeries] = {}
        self._cop_factor: Dict[Tuple[StageId, TechId], float] = {}
        self._temp_ht_in: Dict[Tuple[StageId, HubId, TechId], TimeSeries] = {}
        self._temp_ht_out: Dict[Tuple[StageId, HubId, TechId], TimeSeries] = {}

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self, stages: Stages, hubs: Hubs, ecs: Ecs,
                 techs: Techs, times: Times) -> None:
        """
        Validate all heatpump technology data in this object. Apart from
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
        """
        self._validate_ids(techs)
        self._validate_ec_el(ecs)
        self._validate_ec_ht_in(ecs)
        self._validate_ec_co_in(ecs)
        self._validate_ec_ht_out(ecs)
        self._validate_ec_co_out(ecs)
        self._validate_ecs()
        self._validate_cop(stages, hubs, times)
        self._validate_cop_factor(stages)
        self._validate_temp_ht_in(stages, hubs, times)
        self._validate_temp_ht_out(stages, hubs, times)
        self._validate_temps(times)

    def _validate_ids(self, techs: Techs) -> None:
        exc_key = ExceptionKey.ID_VAL.value
        for x in self._ids:
            # stor_tech not in techs
            if x not in techs.ids:
                msg = f"hp_tech {x} not part of techs"
                raise exceptions.DataException(exc_key, [x], msg,
                                               module=LOG_MODULE_STR)

    def _validate_ec_el(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.ECEL_VAL.value
        for x, e in self._ec_el.items():
            if e not in ecs.ids:
                msg = f"Unknown ec_el {e} for {x}"
                raise exceptions.DataException(exc_key, [x, e], msg,
                                               module=LOG_MODULE_STR)

    def _validate_ec_ht_in(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.ECHTIN_VAL.value
        for x, e in self._ec_ht_in.items():
            if e not in ecs.ids:
                msg = f"Unknown ec_ht_in {e} for {x}"
                raise exceptions.DataException(exc_key, [x, e], msg,
                                               module=LOG_MODULE_STR)

    def _validate_ec_co_in(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.ECCOIN_VAL.value
        for x, e in self._ec_co_in.items():
            if e not in ecs.ids:
                msg = f"Unknown ec_co_in {e} for {x}"
                raise exceptions.DataException(exc_key, [x, e], msg,
                                               module=LOG_MODULE_STR)

    def _validate_ec_ht_out(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.ECHTOUT_VAL.value
        for x, e in self._ec_ht_out.items():
            if e not in ecs.ids:
                msg = f"Unknown ec_ht_out {e} for {x}"
                raise exceptions.DataException(exc_key, [x, e], msg,
                                               module=LOG_MODULE_STR)

    def _validate_ec_co_out(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.ECCOOUT_VAL.value
        for x, e in self._ec_co_out.items():
            if e not in ecs.ids:
                msg = f"Unknown ec_co_out {e} for {x}"
                raise exceptions.DataException(exc_key, [x, e], msg,
                                               module=LOG_MODULE_STR)

    def _validate_ecs(self) -> None:
        for x in self._ids:
            all_ecs: List[Index] = [self.get_ec_el(x), self.get_ec_ht_in(x),
                                    self.get_ec_co_in(x),
                                    self.get_ec_ht_out(x),
                                    self.get_ec_co_out(x)]
            dupes = [e for e, cnt in collections.Counter(all_ecs).items()
                     if cnt > 1]
            if len(dupes) > 0:
                msg = (f"Heat pump tech {x} has the ecs {dupes} occuring "
                       "multiple times across ec_el, ec_ht_in, ec_co_in, "
                       "ec_ht_out and ec_co_out")
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_cop(self, stages: Stages, hubs: Hubs, times: Times) -> None:
        exc_key = ExceptionKey.COP_VAL.value
        for (s, h, x), cop in self._cop.items():
            # Unknown stage id
            if s not in stages.ids:
                msg = f"Unknown stage {s} in cop[{s}, {h}, {x}]"
                raise exceptions.DataException(exc_key, [s, h, x], msg,
                                               module=LOG_MODULE_STR)
            # Unknown hub id
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in cop[{s}, {h}, {x}]"
                raise exceptions.DataException(exc_key, [s, h, x], msg,
                                               module=LOG_MODULE_STR)
            # Time values
            if cop.has_values:
                # Unknown time ids
                cop.validate(times, exc_key, module=LOG_MODULE_STR)
                # COP values must be nonnegative (time values)
                for t in times.ids:
                    if cop.get_value(t) < 0:
                        msg = (f"{cop.get_value(t)} = cop["
                               f"{s}, {h}, {x}][{t}] < 0")
                        raise exceptions.DataException(exc_key, [s, h, x], msg,
                                                       module=LOG_MODULE_STR)
            # Default values
            if not cop.has_values:
                cop_def = cop.def_value
                assert cop_def is not None
                # COP values must be nonnegative (default value)
                if cop_def < 0:
                    msg = (f"{cop_def} = cop_def[{s}, {h}, {x}] < 0")
                    raise exceptions.DataException(exc_key, [s, h, x], msg,
                                                   module=LOG_MODULE_STR)
                # Constant COP usually not zero (default value)
                if cop_def < EPS_ZEROCHECK:
                    msg = (f"{cop_def} = cop_def[{s}, {h}, {x}] ~ 0")
                    logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_cop_factor(self, stages: Stages) -> None:
        exc_key = ExceptionKey.COPFACTOR_VAL.value
        for (s, x), cop_factor in self._cop_factor.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in cop_factor[{s}, {x}]"
                raise exceptions.DataException(exc_key, [s, x], msg,
                                               module=LOG_MODULE_STR)
            # cop_factor must be nonnegative
            if cop_factor < 0:
                msg = f"{cop_factor} = cop_factor[{s}, {x}] < 0"
                raise exceptions.DataException(exc_key, [s, x], msg,
                                               module=LOG_MODULE_STR)
            # cop_factor is usually not larger than one
            if cop_factor > 1:
                msg = f"{cop_factor} = cop_factor[{s}, {x}] > 1"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_temp_ht_in(self, stages: Stages, hubs: Hubs, times: Times
                             ) -> None:
        exc_key = ExceptionKey.TEMPHTIN_VAL.value
        for (s, h, x), temp_ht_in in self._temp_ht_in.items():
            # Unknown stage id
            if s not in stages.ids:
                msg = f"Unknown stage {s} in temp_ht_in[{s}, {h}, {x}]"
                raise exceptions.DataException(exc_key, [s, h, x], msg,
                                               module=LOG_MODULE_STR)
            # Unknown hub id
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in temp_ht_in[{s}, {h}, {x}]"
                raise exceptions.DataException(exc_key, [s, h, x], msg,
                                               module=LOG_MODULE_STR)
            # Time values
            if temp_ht_in.has_values:
                # Unknown time ids
                temp_ht_in.validate(times, exc_key, module=LOG_MODULE_STR)
                # Temperature values must be larger than -273.15 (time values)
                for t in times.ids:
                    if temp_ht_in.get_value(t) < (-273.15):
                        msg = (f"{temp_ht_in.get_value(t)} = temp_ht_in["
                               f"{s}, {h}, {x}][{t}] < -273.15")
                        raise exceptions.DataException(exc_key, [s, h, x], msg,
                                                       module=LOG_MODULE_STR)
            # Default values
            if not temp_ht_in.has_values:
                temp_ht_in_def = temp_ht_in.def_value
                assert temp_ht_in_def is not None
                # Temperature values must be larger than -273.15 (default val)
                if temp_ht_in_def < (-273.15):
                    msg = (f"{temp_ht_in_def} = temp_ht_in_def["
                           f"{s}, {h}, {x}] < -273.15")
                    raise exceptions.DataException(exc_key, [s, h, x], msg,
                                                   module=LOG_MODULE_STR)

    def _validate_temp_ht_out(self, stages: Stages, hubs: Hubs, times: Times
                              ) -> None:
        exc_key = ExceptionKey.TEMPHTOUT_VAL.value
        for (s, h, x), temp_ht_out in self._temp_ht_out.items():
            # Unknown stage id
            if s not in stages.ids:
                msg = f"Unknown stage {s} in temp_ht_out[{s}, {h}, {x}]"
                raise exceptions.DataException(exc_key, [s, h, x], msg,
                                               module=LOG_MODULE_STR)
            # Unknown hub id
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in temp_ht_out[{s}, {h}, {x}]"
                raise exceptions.DataException(exc_key, [s, h, x], msg,
                                               module=LOG_MODULE_STR)
            # Time values
            if temp_ht_out.has_values:
                # Unknown time ids
                temp_ht_out.validate(times, exc_key, module=LOG_MODULE_STR)
                # Temperature values must be larger than -273.15 (time values)
                for t in times.ids:
                    if temp_ht_out.get_value(t) < (-273.15):
                        msg = (f"{temp_ht_out.get_value(t)} = temp_ht_out["
                               f"{s}, {h}, {x}][{t}] < -273.15")
                        raise exceptions.DataException(exc_key, [s, h, x], msg,
                                                       module=LOG_MODULE_STR)
            # Default values
            if not temp_ht_out.has_values:
                temp_ht_out_def = temp_ht_out.def_value
                assert temp_ht_out_def is not None
                # Temperature values must be larger than -273.15 (default val)
                if temp_ht_out_def < (-273.15):
                    msg = (f"{temp_ht_out_def} = temp_ht_out_def["
                           f"{s}, {h}, {x}] < -273.15")
                    raise exceptions.DataException(exc_key, [s, h, x], msg,
                                                   module=LOG_MODULE_STR)

    def _validate_temps(self, times: Times) -> None:
        exc_key = ExceptionKey.TEMPS_VAL.value
        keys = set(self._temp_ht_in.keys()).intersection(
            set(self._temp_ht_out.keys()))
        for (s, h, x) in keys:
            temp_ht_in = self._temp_ht_in[s, h, x]
            temp_ht_out = self._temp_ht_out[s, h, x]
            # temp_ht_in must be smaller than temp_ht_out (time values)
            if temp_ht_in.has_values or temp_ht_out.has_values:
                for t in times.ids:
                    if temp_ht_in.get_value(t) >= temp_ht_out.get_value(t):
                        msg = (f"{temp_ht_in.get_value(t)} = temp_ht_in["
                               f"{s}, {h}, {x}][{t}] >= temp_ht_out["
                               f"{s}, {h}, {x}][{t}] = "
                               f"{temp_ht_out.get_value(t)}")
                        raise exceptions.DataException(exc_key, [s, h, x, t],
                            msg, module=LOG_MODULE_STR)
            # temp_ht_in must not be larger than imp_max (default values)
            if not (temp_ht_in.has_values or temp_ht_out.has_values):
                temp_ht_in_def = temp_ht_in.def_value
                temp_ht_out_def = temp_ht_out.def_value
                assert temp_ht_in_def is not None
                assert temp_ht_out_def is not None
                if temp_ht_in_def >= temp_ht_out_def:
                    msg = (f"{temp_ht_in_def} = temp_ht_in[{s}, {h}, {x}] >= "
                           f"temp_ht_out[{s}, {h}, {x}] = {temp_ht_out_def}")
                    raise exceptions.DataException(exc_key, [s, h, x],
                        msg, module=LOG_MODULE_STR)

    # ---------- #
    # Id checker #
    # ---------- #
    def _check_id(self, x: TechId, key: ExceptionKey) -> None:
        if x not in self._ids:
            raise exceptions.UnknownIdException(key.value, x,
                                                module=LOG_MODULE_STR)
