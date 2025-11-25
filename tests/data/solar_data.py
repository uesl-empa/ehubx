"""
Solar data module
"""

from enum import Enum
from typing import Dict, List, Set, Tuple

from ehubx.core.common import TimeSeriesKind
from ehubx.data import exceptions
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.time_data import TimeId, Times
from ehubx.data.time_series import TimeSeries
from ehubx.data.unit import LengthUnit, TimeUnit, Unit
from ehubx.data.value import Value


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the solar data module
    """

    ECS_ADD = "adding to 'ecs' of SolarData"
    ECS_VAL = "validating 'ecs' of SolarData"
    IRRADIATION_GET = "getting 'irradiation' from SolarData"
    IRRADIATION_SET = "setting 'irradiation' of SolarData"
    IRRADIATION_DEFSET = "setting default 'irradiation' of SolarData"
    IRRADIATION_VAL = "validating 'irradiation' of SolarData"
    AREA_GET = "getting 'area' from SolarData"
    AREA_SET = "setting 'area' of SolarData"
    AREA_VAL = "validating 'area' of SolarData"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/solar_data"
"""String identifying the solar data module for logging purposes"""

DEF_IRRADIATION: float = 0
"""Default value for parameter 'irradiation' in the solar data module"""

DEF_AREA: float = 0
"""Default value for parameter 'area' in the solar data module"""


class SolarData:
    """
    Class for solar data. Contains getters and setters for solar
    parameters and validation methods to control data integrity
    """

    # ------------- #
    # Property: ecs #
    # ------------- #
    @property
    def ecs(self) -> Set[EcId]:
        """
        Set of known solar ec ids
        """
        return self._ecs

    def add_ec(self, e: EcId, ec_unit: Unit) -> None:
        """
        Add a solar ec to the data object.

        :param e: Solar ec id
        :type e: EcId
        :param ec_unit: Unit of the solar ec
        :type ec_unit: Unit
        """
        if e in self._ecs:
            raise exceptions.DataException(
                ExceptionKey.ECS_ADD.value,
                [e],
                msg=f"Solar ec {e} already exists in the data object.",
                module=LOG_MODULE_STR,
            )
        self._ecs.add(e)
        self._ec_unit[e] = ec_unit

    # --------------------- #
    # Property: irradiation #
    # --------------------- #
    def get_irradiation(self, s: StageId, e: EcId) -> TimeSeries:
        """
        Get the irradiation time series for a stage and a solar ec. This is an
        optional parameter with a default value of 0.

        :param s: Stage id
        :type s: StageId
        :param e: Solar ec
        :type e: EcId
        :return: Irradiation profile
        :rtype: TimeSeries
        """
        self._check_ec(e, ExceptionKey.IRRADIATION_GET)
        unit = self._ec_unit[e] / (TimeUnit.H * LengthUnit.M**2)
        if (s, e) not in self._irradiation:
            series = TimeSeries()
            series.def_value = Value(DEF_IRRADIATION, unit)
            return series
        return self._irradiation[s, e]

    def set_irradiation(
        self, s: StageId, e: EcId, t: TimeId, irradiation: Value
    ) -> None:
        """
        Set the irradiation level for a solar ec at a specific time step. This
        is an optional parameter with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param e: Solar ec
        :type e: EcId
        :param t: Timestep
        :type t: TimeId
        :param irradiation: Irradiation level
        :type irradiation: Value
        """
        self._check_ec(e, ExceptionKey.IRRADIATION_SET)
        expected_unit = self._ec_unit[e] / (TimeUnit.H * LengthUnit.M**2)
        if (s, e) not in self._irradiation:
            self._irradiation[s, e] = TimeSeries()
            self._irradiation[s, e].def_value = Value(DEF_IRRADIATION, expected_unit)
        self._irradiation[s, e].set_value(t, irradiation)
        self._ecs.add(e)

    def set_irradiation_def(self, s: StageId, e: EcId, irradiation_def: Value) -> None:
        """
        Set the default (with respect to time) irradiation level for a solar
        ec. This is an optional parameter with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param e: Solar ec
        :type e: EcId
        :param irradiation_def: Default irradiation level
        :type irradiation_def: Value
        """
        self._check_ec(e, ExceptionKey.IRRADIATION_DEFSET)
        expected_unit = self._ec_unit[e] / (TimeUnit.H * LengthUnit.M**2)
        if (s, e) not in self._irradiation:
            self._irradiation[s, e] = TimeSeries()
            self._irradiation[s, e].def_value = Value(DEF_IRRADIATION, expected_unit)
        self._irradiation[s, e].def_value = irradiation_def
        self._ecs.add(e)

    # -------------- #
    # Property: area #
    # -------------- #
    def get_area(self, s: StageId, h: HubId, e: EcId) -> Value:
        """
        Get the available area that can be used for the installation of a solar
        technology in a given stage and hub, and for a solar ec. This is an
        optional parameter with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: Solar ec
        :type e: EcId
        :return: Available area
        :rtype: Value
        """
        self._check_ec(e, ExceptionKey.AREA_GET)
        return self._area.get((s, h, e), Value(DEF_AREA, LengthUnit.M**2))

    def set_area(self, s: StageId, h: HubId, e: EcId, area: Value) -> None:
        """
        Set the available area that can be used for the installation of a solar
        technology in a given stage and hub, and for a solar ec. This is an
        optional parameter with a default value of 0.

        :param s: Stage
        :type s: StageId
        :param h: Hub
        :type h: HubId
        :param e: Solar ec
        :type e: EcId
        :param area: Available area
        :type area: Value
        """
        self._check_ec(e, ExceptionKey.AREA_SET)
        expected_unit = LengthUnit.M**2
        if not area.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.AREA_SET.value,
                [s, h, e],
                msg=f"Unit mismatch: cannot set area value {area} for solar ec {e} "
                f"in stage {s} and hub {h}. Expected unit is {expected_unit}.",
                module=LOG_MODULE_STR,
            )
        self._area[s, h, e] = area
        self._ecs.add(e)

    # ------------------------------- #
    # Secondary property: time_series #
    # ------------------------------- #
    @property
    def time_series(
        self,
    ) -> List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...], TimeSeries]]:
        """
        Time series profiles in the solar module. This is a list of tuples.
        Each list element has the following list entries: 1) ProfileKind of
        the profile. 2) Stage. 3) Tuple of string identifiers specific to the
        ProfileKind. 4) The TimeSeries itself

        :return: All time series of the solar module
        :rtype: List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...],
            TimeSeries]]
        """
        all_series: List[
            Tuple[TimeSeriesKind, StageId, Tuple[str, ...], TimeSeries]
        ] = []
        # irradiation
        for (s, e), series in self._irradiation.items():
            if series.has_values:
                all_series.append((TimeSeriesKind.SOLARIRRAD, s, (e.key,), series))
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
        Set the value for a time series in the solar data class. The time
        series should be uniquely identified by the time series kind, the
        stage  id and the remaining tuples.

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
        if kind == TimeSeriesKind.SOLARIRRAD:
            e = EcId(ids[0])
            unit = Unit.get_def_unit(self._ec_unit[e] / (TimeUnit.H * LengthUnit.M**2))
            self.set_irradiation(s, e, t, Value(value, unit=unit))

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._ecs: Set[EcId] = set()
        self._ec_unit: Dict[EcId, Unit] = {}
        self._irradiation: Dict[Tuple[StageId, EcId], TimeSeries] = {}
        self._area: Dict[Tuple[StageId, HubId, EcId], Value] = {}

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self, stages: Stages, hubs: Hubs, ecs: Ecs, times: Times) -> None:
        """
        Validate all solar data in this object. Apart from sense- checking
        parameter in terms of quantity, this includes checking whether
        the ids from other data classes used here are known there as well.

        :param stages: Stages data class
        :type stages: Stages
        :param hubs: Hubs data class
        :type hubs: Hubs
        :param ecs: ecs data class
        :type ecs: Ecs
        :param times: Times data class
        :type times: Times
        """
        self._validate_ecs(ecs)
        self._validate_irradiation(stages, ecs, times)
        self._validate_area(stages, hubs, ecs)

    def _validate_ecs(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.ECS_VAL.value
        for e in self.ecs:
            # Unknown EC
            if e not in ecs.ids:
                msg = f"Unknown ec {e} in solar ecs"
                raise exceptions.DataException(exc_key, [e], msg, module=LOG_MODULE_STR)
            # Wrong unit
            expected_unit = ecs.get_unit(e)
            if not self._ec_unit[e].same_type_as(expected_unit):
                raise exceptions.DataException(
                    exc_key,
                    [e],
                    f"Unit {self._ec_unit[e]} of solar ec {e} "
                    f"does not match expected unit {expected_unit}",
                    module=LOG_MODULE_STR,
                )

    def _validate_irradiation(self, stages: Stages, ecs: Ecs, times: Times) -> None:
        exc_key = ExceptionKey.IRRADIATION_VAL.value
        for (s, e), irradiation in self._irradiation.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in irradiation[{s}, {e}]"
                raise exceptions.DataException(
                    exc_key, [s, e], msg, module=LOG_MODULE_STR
                )
            # Time values
            if irradiation.has_values:
                # Unknown time ids
                irradiation.validate(times, exc_key)
                # irradiation must not be negative
                for t in times.ids:
                    if irradiation.get_value(t).is_negative:
                        msg = (
                            f"{irradiation.get_value(t)} = "
                            f"irradiation[{s}, {e}][{t}] < 0"
                        )
                        raise exceptions.DataException(
                            exc_key, [s, e, t], msg, module=LOG_MODULE_STR
                        )
            # Default value
            if not irradiation.has_values:
                irradiation_def = irradiation.def_value
                assert irradiation_def is not None
                # irradiation must not be negative
                if irradiation_def.is_negative:
                    msg = f"{irradiation_def} = irradiation_def[{s}, {e}] < 0"
                    raise exceptions.DataException(
                        exc_key, [s, e], msg, module=LOG_MODULE_STR
                    )

    def _validate_area(self, stages: Stages, hubs: Hubs, ecs: Ecs) -> None:
        exc_key = ExceptionKey.AREA_VAL.value
        for (s, h, e), area in self._area.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in area[{s}, {h}, {e}]"
                raise exceptions.DataException(
                    exc_key, [s, h, e], msg, module=LOG_MODULE_STR
                )
            # Unknown hub
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in area[{s}, {h}, {e}]"
                raise exceptions.DataException(
                    exc_key, [s, h, e], msg, module=LOG_MODULE_STR
                )
            # area must not be negative
            if area.is_negative:
                msg = f"{area} = area[{s}, {h}, {e}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, h, e], msg, module=LOG_MODULE_STR
                )

    # ---------- #
    # Ec checker #
    # ---------- #
    def _check_ec(self, e: EcId, where: ExceptionKey) -> None:
        if e not in self._ecs:
            raise exceptions.DataException(
                where.value,
                [e],
                f"Encountered ec {e} which is not registered as a solar ec"
                f"while {where.value}",
                module=LOG_MODULE_STR,
            )
