import math

import pytest

from ehubx.data.exceptions import UnitException, ValueException
from ehubx.data.unit import CompoundUnit, DimlessUnit, PowerUnit, Unit
from ehubx.data.value import Value


def test_parse_dimless_zero():
    value = Value.from_str("0")
    assert value.unit == DimlessUnit()


def test_parse_negative_dimless_number():
    value = Value.from_str("-1.2")
    assert value.to_float() == -1.2
    assert value.unit == DimlessUnit()
    with pytest.raises(UnitException):
        value.to_float(PowerUnit.KW)


def test_parse_invalid_missing_space_simple_unit():
    with pytest.raises(ValueException):
        Value.from_str("-14.3kW")


def test_parse_negative_power_unit():
    value = Value.from_str("-14.3 kW")
    assert isinstance(value.unit, PowerUnit)
    assert value.to_float(PowerUnit.KW) == -14.3


def test_parse_invalid_missing_space_compound_unit_1():
    with pytest.raises(ValueException):
        Value.from_str("-14.3kW/kW")


def test_parse_dimless_compound_unit_same_units():
    value = Value.from_str("-14.3 kW/kW")
    assert isinstance(value.unit, DimlessUnit)
    assert value.to_float() == -14.3


def test_parse_invalid_missing_space_compound_unit_2():
    with pytest.raises(ValueException):
        Value.from_str("-14.3MW/kW")


def test_parse_compound_unit_conversion():
    value = Value.from_str("-14.3 t/kW")
    assert isinstance(value.unit, CompoundUnit)
    assert value.to_float(Unit.from_str("t/kW")) == -14.3
    assert value.to_float(Unit.from_str("kt/kW")) == -0.0143
    assert value.to_float(Unit.from_str("kg/kW")) == -14300
    with pytest.raises(UnitException):
        value.to_float(PowerUnit.KW)
    with pytest.raises(UnitException):
        value.to_float(Unit.from_str("kW/MW"))


# Additional tests for edge cases


def test_parse_positive_infinity_dimless():
    value = Value.from_str("inf")
    assert math.isinf(value.to_float())
    assert value.to_float() > 0
    assert value.unit == DimlessUnit()


def test_parse_negative_infinity_dimless():
    value = Value.from_str("-inf")
    assert math.isinf(value.to_float())
    assert value.to_float() < 0
    assert value.unit == DimlessUnit()


def test_parse_positive_infinity_with_unit():
    value = Value.from_str("inf kW")
    assert isinstance(value.unit, PowerUnit)
    assert math.isinf(value.to_float(PowerUnit.KW))
    assert value.to_float(PowerUnit.KW) > 0


def test_parse_negative_infinity_with_unit():
    value = Value.from_str("-inf kW")
    assert isinstance(value.unit, PowerUnit)
    assert math.isinf(value.to_float(PowerUnit.KW))
    assert value.to_float(PowerUnit.KW) < 0


def test_parse_underscored_numeric_dimless():
    value = Value.from_str("1_000")
    assert value.to_float() == 1000.0
    assert value.unit == DimlessUnit()


def test_parse_underscored_numeric_with_unit():
    value = Value.from_str("1_000 kW")
    assert isinstance(value.unit, PowerUnit)
    assert value.to_float(PowerUnit.KW) == 1000.0


def test_parse_negative_large_number_with_multiple_underscores():
    value = Value.from_str("-1_345_983 kW")
    assert isinstance(value.unit, PowerUnit)
    assert value.to_float(PowerUnit.KW) == -1345983.0
