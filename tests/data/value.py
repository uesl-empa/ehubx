from __future__ import annotations

import numbers
from typing import Any, Optional

from ehubx.data import exceptions
from ehubx.data.unit import DimlessUnit, Unit


# Literals
LOG_MODULE_STR: str = "data/value"


class Value:
    def __init__(self, value: float, unit: Unit = DimlessUnit()):
        if not isinstance(value, numbers.Real):
            raise TypeError(f"Value must be a real number, got {type(value)}.")
        self._unit: Unit = Unit.get_def_unit(unit)
        self._value: float = float(value) * Unit.get_conv_factor_to_def_unit(unit)

    @property
    def unit(self) -> Unit:
        return self._unit

    @classmethod
    def from_str(cls, s: str) -> Value:
        s = s.strip()
        parts = s.split()

        if len(parts) == 1:
            number_str = parts[0]
            unit_str = ""
        elif len(parts) == 2:
            number_str, unit_str = parts
        else:
            raise exceptions.ValueException(
                value=s,
                msg=f"Failed to parse value string '{s}'",
                reason=(
                    "Too many parts. Expected at most one space between "
                    "value and unit."
                ),
                module=LOG_MODULE_STR,
            )

        number_str = number_str.replace("_", "")

        if number_str.lower() == "inf":
            value = float("inf")
        elif number_str.lower() == "-inf":
            value = float("-inf")
        else:
            try:
                value = float(number_str)
            except ValueError:
                raise exceptions.ValueException(
                    value=s,
                    msg=f"Invalid number '{number_str}' in string '{s}'",
                    reason="Failed to convert to float.",
                    module=LOG_MODULE_STR,
                )

        if value != value:  # NaN check
            raise exceptions.ValueException(
                value=s,
                msg="'nan' is not supported as a value.",
                reason="NaN is explicitly disallowed.",
                module=LOG_MODULE_STR,
            )

        try:
            unit = Unit.from_str(unit_str) if unit_str else DimlessUnit()
        except exceptions.UnitException as ex:
            raise exceptions.ValueException(
                value=s,
                msg=f"Invalid unit '{unit_str}' in string '{s}'",
                reason=f"Failed to parse unit {unit_str} from string.",
                module=LOG_MODULE_STR,
            ) from ex

        return cls(value, unit)

    def to_float(self, unit: Optional[Unit] = None) -> float:
        if unit is None:
            return self._value
        if not self.unit.same_type_as(unit):
            raise exceptions.UnitException(
                unit=str(unit),
                msg=f"Unit mismatch: cannot convert from {self.unit} to {unit}.",
                module=LOG_MODULE_STR,
            )
        conv_factor = Unit.get_conv_factor_to_def_unit(unit)
        return self._value / conv_factor

    @property
    def is_finite(self) -> bool:
        return self._value not in (float("inf"), float("-inf"), float("nan"))

    def __add__(self, other: Value) -> Value:
        if not isinstance(other, Value):
            raise NotImplementedError()

        if not self.same_unit_type_as(other):
            raise exceptions.UnitException(
                unit=str(other.unit),
                msg=f"Unit mismatch: cannot add {self.unit} with {other.unit}.",
                module=LOG_MODULE_STR,
            )

        # Convert other's value to self's unit and sum
        total_value = self._value + other._value

        # Return a new Value with the sum in self's unit
        return Value(total_value, self.unit)

    def __radd__(self, other: Any) -> Value:
        # To support sum(), which starts with 0 as initial value
        if other == 0:
            return self
        return self.__add__(other)

    def __sub__(self, other: Value) -> Value:
        if not isinstance(other, Value):
            raise NotImplementedError(
                "Subtraction only supported between Value instances."
            )

        if not self.same_unit_type_as(other):
            raise exceptions.UnitException(
                unit=str(other.unit),
                msg=f"Unit mismatch: cannot subtract {self.unit} and {other.unit}.",
                module=LOG_MODULE_STR,
            )

        result_value = self._value - other.to_float(self.unit)
        return Value(result_value, self.unit)

    def __neg__(self) -> Value:
        return Value(-self._value, self.unit)

    def __mul__(self, other: Value | int | float) -> Value:
        if isinstance(other, Value):
            result_value = self._value * other._value
            result_unit = Unit.get_def_unit(self.unit * other.unit)
            return Value(result_value, result_unit)
        elif isinstance(other, (int, float)):
            return Value(self._value * other, Unit.get_def_unit(self._unit))
        else:
            raise NotImplementedError(
                "Multiplication only supported between Value instances "
                "or with numeric types."
            )

    def __rmul__(self, other: float | int) -> Value:
        return self.__mul__(other)

    def __truediv__(self, other: Any) -> Value:
        if not isinstance(other, Value):
            raise NotImplementedError(
                "Division only supported between Value instances."
            )

        result_value = self._value / other._value
        result_unit = Unit.get_def_unit(self.unit / other.unit)
        return Value(result_value, result_unit)

    def __pow__(self, exponent: int) -> Value:
        if not isinstance(exponent, int):
            raise TypeError("Exponent must be an integer.")

        result_value = self._value**exponent
        result_unit = Unit.get_def_unit(self.unit**exponent)
        return Value(result_value, result_unit)

    def root(self, deg: int = 2) -> Value:
        if not isinstance(deg, int) or deg <= 0:
            raise ValueError("Degree of root function must be a positive integer.")

        if self._value < 0 and deg % 2 == 0:
            raise ValueError("Cannot take even root of a negative value.")

        result_value = self._value ** (1 / deg)
        result_unit = Unit.get_def_unit(self.unit.root(deg=deg))
        return Value(result_value, result_unit)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Value):
            raise NotImplementedError(
                "Comparison only supported between Value instances."
            )
        if not self.same_unit_type_as(other):
            raise ValueError(
                "Cannot compare Values with different units: "
                f"{self.unit} and {other.unit}"
            )
        return self._value == other._value

    def __str__(self) -> str:
        return f"{self._value} {self.unit}"

    def __repr__(self) -> str:
        return self.__str__()

    def same_unit_type_as(self, other: Value) -> bool:
        return self.unit.same_type_as(other.unit)

    @property
    def is_positive(self) -> bool:
        return self._value > 0

    @property
    def is_negative(self) -> bool:
        return self._value < 0

    @property
    def is_nonnegative(self) -> bool:
        return self._value >= 0

    @property
    def is_nonpositive(self) -> bool:
        return self._value <= 0

    def __lt__(self, other: Value) -> bool:
        if not self.same_unit_type_as(other):
            raise exceptions.UnitException(
                unit=str(other.unit),
                msg=f"Unit mismatch: cannot compare {self.unit} with {other.unit}.",
                module=LOG_MODULE_STR,
            )
        return self._value < other.to_float(self.unit)

    def __le__(self, other: Value) -> bool:
        if not self.same_unit_type_as(other):
            raise exceptions.UnitException(
                unit=str(other.unit),
                msg=f"Unit mismatch: cannot compare {self.unit} with {other.unit}.",
                module=LOG_MODULE_STR,
            )
        return self._value <= other.to_float(self.unit)

    def __gt__(self, other: Value) -> bool:
        if not self.same_unit_type_as(other):
            raise exceptions.UnitException(
                unit=str(other.unit),
                msg=f"Unit mismatch: cannot compare {self.unit} with {other.unit}.",
                module=LOG_MODULE_STR,
            )
        return self._value > other.to_float(self.unit)

    def __ge__(self, other: Value) -> bool:
        if not self.same_unit_type_as(other):
            raise exceptions.UnitException(
                unit=str(other.unit),
                msg=f"Unit mismatch: cannot compare {self.unit} with {other.unit}.",
                module=LOG_MODULE_STR,
            )
        return self._value >= other.to_float(self.unit)
