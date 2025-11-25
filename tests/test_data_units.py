import pytest

from ehubx.data.exceptions import UnitException
from ehubx.data.unit import CompoundUnit, DimlessUnit, MassUnit, PowerUnit, Unit


def test_unit_fromstr_1():
    unit = Unit.from_str("")
    assert isinstance(unit, DimlessUnit)


def test_unit_fromstr_2():
    unit = Unit.from_str(" ")
    assert isinstance(unit, DimlessUnit)


def test_unit_fromstr_3():
    unit = Unit.from_str("kW")
    assert unit == PowerUnit.KW


def test_unit_fromstr_4():
    unit = Unit.from_str(" kW ")
    assert unit == PowerUnit.KW


def test_unit_fromstr_5():
    unit = Unit.from_str("kW*MW")
    assert isinstance(unit, CompoundUnit)
    assert set(unit.numerator) == {PowerUnit.KW, PowerUnit.MW}
    assert unit.denominator == []


def test_unit_fromstr_6():
    unit = Unit.from_str("kW/MW")
    assert isinstance(unit, CompoundUnit)
    assert unit.numerator == [PowerUnit.KW]
    assert unit.denominator == [PowerUnit.MW]


def test_unit_fromstr_7():
    unit = Unit.from_str("kW/kW")
    assert unit == DimlessUnit()


def test_unit_fromstr_8():
    unit = Unit.from_str("kW*MW/kW")
    assert unit == PowerUnit.MW


def test_unit_fromstr_9():
    unit = Unit.from_str("kW/(MW*kW)")
    assert isinstance(unit, CompoundUnit)
    assert unit.numerator == []
    assert unit.denominator == [PowerUnit.MW]


def test_unit_fromstr_10():
    unit = Unit.from_str("kW/MW/kW")
    assert isinstance(unit, CompoundUnit)
    assert unit.numerator == []
    assert unit.denominator == [PowerUnit.MW]


def test_unit_fromstr_11():
    with pytest.raises(UnitException):
        Unit.from_str("kW/MW*MW")


def test_unit_fromstr_12():
    unit = Unit.from_str("kg/kW")
    assert unit == CompoundUnit.create(
        numerator=[MassUnit.KG], denominator=[PowerUnit.KW]
    )
