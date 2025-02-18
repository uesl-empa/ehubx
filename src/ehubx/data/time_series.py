"""
Time series data module
"""
from typing import Dict, Optional
from enum import Enum
from ehubx.data.time_data import Times, TimeId
from ehubx.data import exceptions


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
        raise exceptions.MissingIdException(ExceptionKey.VALUE_GET.value, t,
                                            module=LOG_MODULE_STR)

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
    def def_value(self, def_value) -> None:
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
        self.def_value: Optional[float] = None

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
