"""
Time series data module
"""

from enum import Enum
from typing import Dict, Optional

from ehubx.data import exceptions
from ehubx.data.time_data import TimeId, Times
from ehubx.data.unit import Unit
from ehubx.data.value import Value


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the time series data module
    """

    VALUE_GET = "getting 'value' from Times"
    VALUE_REMOVE = "removing 'value' from Times"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/time_ser"
"""String identifying the time series data module for logging purposes"""


class TimeSeries:
    """
    Class for time series data which are functions mapping time instances to
    unit-aware Value objects. If no value is set for a given time, a default
    value will be returned, if provided.
    """

    def __init__(self) -> None:
        self._value: Dict[TimeId, Value] = {}
        self._unit: Optional[Unit] = None
        self._def_value: Optional[Value] = None

    # -------------- #
    # Property: unit #
    # -------------- #
    @property
    def unit(self) -> Optional[Unit]:
        """
        The unit of the time series. If no unit has been set, this will be None.
        """
        return self._unit

    # ----------------------------- #
    # Properties: value & def_value #
    # ----------------------------- #
    def get_value(self, t: TimeId) -> Value:
        value = self._value.get(t, self._def_value)
        if value is not None:
            return value
        raise exceptions.MissingIdException(
            ExceptionKey.VALUE_GET.value, t, module=LOG_MODULE_STR
        )

    def set_value(self, t: TimeId, value: Value) -> None:
        if self._unit is None:
            self._unit = Unit.get_def_unit(value.unit)
        elif not self._unit.same_type_as(value.unit):
            raise exceptions.UnitException(
                unit=str(value.unit),
                msg=f"Unit mismatch: cannot set value with unit {value.unit} "
                f"to TimeSeries with unit type {self._unit}.",
                module=LOG_MODULE_STR,
            )
        self._value[t] = value

    def remove_value(self, t: TimeId) -> None:
        if t in self._value:
            self._value.pop(t)

    def clear(self) -> None:
        self._value.clear()

    # ------------------- #
    # Property: def_value #
    # ------------------- #
    @property
    def def_value(self) -> Optional[Value]:
        return self._def_value

    @def_value.setter
    def def_value(self, def_value: Value) -> None:
        if self._unit is None:
            self._unit = Unit.get_def_unit(def_value.unit)
        elif not self._unit.same_type_as(def_value.unit):
            raise exceptions.UnitException(
                unit=str(def_value.unit),
                msg="Unit mismatch: cannot set default value with unit "
                f"{def_value.unit} to TimeSeries with unit type {self._unit}.",
                module=LOG_MODULE_STR,
            )
        self._def_value = def_value

    # -------------------- #
    # Secondary properties #
    # -------------------- #
    @property
    def has_values(self) -> bool:
        return len(self._value) > 0

    @property
    def num_values(self) -> int:
        return len(self._value)

    @property
    def max(self) -> Value:
        if self.has_values:
            return max(self._value.values())
        elif self.def_value is not None:
            return self.def_value
        else:
            return Value(float("inf"))

    @property
    def min(self) -> Value:
        if self.has_values:
            return min(self._value.values())
        elif self.def_value is not None:
            return self.def_value
        else:
            return Value(float("-inf"))

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self, times: Times, exc_key: str, module: str = "") -> None:
        for t in self._value:
            if t not in times.ids:
                raise exceptions.UnknownIdException(exc_key, t, module=module)

    def __repr__(self) -> str:
        repr_str = f"<TimeSeries: n_vals={len(self._value)}, "
        repr_str += f"def_val={self._def_value}>"
        return repr_str


class TimeSeriesFloat:
    """
    Class for time series data which are functions mapping time instances to
    float values. Apart from time-float value pairs, this class contains a
    default value property which will be returned if no data is specified.
    """

    # ----------------------------- #
    # Properties: value & def_value #
    # ----------------------------- #
    def get_value(self, t: TimeId) -> float:
        """
        Returns the value for a specific time id. If no specific value has been
        set for the time id, the default value will be returned instead. If
        no default value has been set either, a MissingIdException is thrown.

        :param t: Time
        :type t: TimeId
        :return: Value at the requested time id
        :rtype: float
        """
        value = self._value.get(t, self._def_value)
        if value is not None:
            return value
        raise exceptions.MissingIdException(
            ExceptionKey.VALUE_GET.value, t, module=LOG_MODULE_STR
        )

    def set_value(self, t: TimeId, value: float) -> None:
        """
        Sets the value for a specific time id.

        :param t: Time
        :type t: TimeId
        :param value: Value to be set
        :type value: float
        """
        self._value[t] = value

    def remove_value(self, t: TimeId) -> None:
        """
        Removes the value at a specific time id.

        :param t: Time id
        :type t: TimeId
        """
        if t in self._value:
            self._value.pop(t)

    def clear(self) -> None:
        """
        Clears all values that have been set using set_value (does not remove
        the default value)
        """
        self._value.clear()

    # ------------------- #
    # Property: def_value #
    # ------------------- #
    @property
    def def_value(self) -> Optional[float]:
        """The default value (if any) that is returned at time ids without a
        specific value"""
        return self._def_value

    @def_value.setter
    def def_value(self, def_value: float) -> None:
        self._def_value = def_value

    # -------------------- #
    # Secondary properties #
    # -------------------- #
    @property
    def has_values(self) -> bool:
        """Whether any time-specific data has been set"""
        return len(self._value) > 0

    @property
    def num_values(self) -> int:
        """Number of time-specific values that have been set"""
        return len(self._value)

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._value: Dict[TimeId, float] = {}
        self.def_value = None

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self, times: Times, exc_key: str, module: str = "") -> None:
        """
        Validate all data in this object. This entails checking whether all
        time ids are known to the time data object.

        :param times: Times data class
        :type times: Times
        :param exc_key: Exception key to be used if an unknown time id is found
        :type exc_key: str
        :param module: Module stirng to be used if an unknown time id is found
        :type module: str
        """
        for t in self._value:
            if t not in times.ids:
                raise exceptions.UnknownIdException(exc_key, t, module=module)

    def __repr__(self) -> str:
        repr_str = f"<TimeSeries: n_vals={len(self._value)}, "
        repr_str += f"def_val={self._def_value}>"
        return repr_str
