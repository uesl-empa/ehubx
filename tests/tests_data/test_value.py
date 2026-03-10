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

def test_from_str_too_many_parts():
    with pytest.raises(ValueException):
        Value.from_str("1 kW extra")


def test_from_str_nan_disallowed():
    with pytest.raises(ValueException):
        Value.from_str("nan")
    with pytest.raises(ValueException):
        Value.from_str("NaN")


def test_add_and_radd_sum_and_mismatch():
    a = Value.from_str("1 kW")
    b = Value.from_str("2 kW")
    assert (a + b).to_float(PowerUnit.KW) == 3.0
    assert sum([a, b]).to_float(PowerUnit.KW) == 3.0

    with pytest.raises(UnitException):
        _ = a + Value.from_str("1 t")


def test_sub_neg_and_mismatch():
    a = Value.from_str("5 kW")
    b = Value.from_str("2 kW")
    assert (a - b).to_float(PowerUnit.KW) == 3.0
    assert (-b).to_float(PowerUnit.KW) == -2.0

    with pytest.raises(UnitException):
        _ = a - Value.from_str("1 t")


def test_mul_with_numeric_and_value():
    v = Value.from_str("3 kW")
    assert (v * 2).to_float(PowerUnit.KW) == 6.0
    assert (2 * v).to_float(PowerUnit.KW) == 6.0

    # multiply with dimless value
    dv = Value.from_str("2")
    prod = v * dv
    assert prod.unit == PowerUnit.KW
    assert prod.to_float(PowerUnit.KW) == 6.0

    # multiply two values with units produces compound unit and numeric product
    v2 = Value.from_str("2 kW")
    pp = v * v2
    assert pp.to_float(Unit.from_str("kW*kW")) == 6.0


def test_truediv_and_result_unit():
    a = Value.from_str("6 kW")
    b = Value.from_str("3 kW")
    res = a / b
    assert res.to_float() == 2.0
    assert isinstance(res.unit, DimlessUnit)


def test_pow_and_root_and_errors():
    v = Value.from_str("3 kW")
    p = v ** 2
    assert p.to_float(Unit.from_str("kW*kW")) == 9.0

    with pytest.raises(TypeError):
        _ = v ** 2.5

    # root of a unit squared
    u = Value.from_str("4 kW^2")
    r = u.root(2)
    assert r.to_float(PowerUnit.KW) == 2.0

    with pytest.raises(ValueError):
        u.root(0)

    # negative value even root
    neg = Value.from_str("-4 kW^2")
    with pytest.raises(ValueError):
        neg.root(2)


def test_eq_and_mismatch():
    v1 = Value.from_str("1000 kW")
    v2 = Value.from_str("1 MW")
    assert v1 == v2

    with pytest.raises(ValueError):
        _ = Value.from_str("1 kW") == Value.from_str("1 t")


def test_str_and_properties_and_comparisons():
    v = Value.from_str("1000 kW")
    assert str(v) == f"{v._value} {v.unit}"
    assert v.is_positive
    assert not v.is_negative
    assert v.is_nonnegative

    z = Value(0.0)
    assert not z.is_positive
    assert not z.is_negative
    assert z.is_nonnegative
    assert z.is_nonpositive

    assert Value.from_str("1 kW") < Value.from_str("2 kW")
    with pytest.raises(UnitException):
        _ = Value.from_str("1 kW") < Value.from_str("1 t")


def test_is_finite_for_infinities():
    assert Value.from_str("1").is_finite
    assert not Value.from_str("inf").is_finite
    assert not Value.from_str("-inf").is_finite
