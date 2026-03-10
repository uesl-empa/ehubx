import pytest

from ehubx.data.exceptions import UnitException
from ehubx.data.unit import CompoundUnit, DimlessUnit, MassUnit, PowerUnit, TimeUnit, Unit


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

def test_derived_unit_alias():
    unit = Unit.from_str("kWh")
    assert isinstance(unit, CompoundUnit)
    assert set(unit.numerator) == {PowerUnit.KW, TimeUnit.H}


def test_exponent_parsing_pow_and_star():
    unit = Unit.from_str("kW^2")
    assert isinstance(unit, CompoundUnit)
    assert unit.numerator == [PowerUnit.KW, PowerUnit.KW]


def test_unit_one_token_and_parentheses():
    unit = Unit.from_str("1/kW")
    assert isinstance(unit, CompoundUnit)
    assert unit.numerator == []
    assert unit.denominator == [PowerUnit.KW]

    # parentheses around denominator
    unit2 = Unit.from_str("kW/(kW*kW)")
    assert isinstance(unit2, CompoundUnit)
    # one kW cancels with numerator, leaving a single kW in denominator
    assert unit2.numerator == []
    assert unit2.denominator == [PowerUnit.KW]


def test_get_def_unit_and_conv_factor():
    # Basic unit def and conv
    assert Unit.get_def_unit(PowerUnit.MW) == PowerUnit.KW
    assert Unit.get_conv_factor_to_def_unit(PowerUnit.MW) == 1e3

    # Compound unit that cancels to dimless after normalization
    u = Unit.from_str("MW/kW")
    assert Unit.get_def_unit(u) == DimlessUnit()

    # Conv factor for compound
    u2 = Unit.from_str("kW/MW")
    assert Unit.get_conv_factor_to_def_unit(u2) == pytest.approx(1e-3)


def test_same_type_and_arithmetic():
    assert PowerUnit.KW.same_type_as(PowerUnit.MW)

    assert not PowerUnit.KW.same_type_as(TimeUnit.H)

    prod = PowerUnit.KW * PowerUnit.MW
    assert isinstance(prod, CompoundUnit)
    assert set(prod.numerator) == {PowerUnit.KW, PowerUnit.MW}

    div = PowerUnit.MW / PowerUnit.KW
    assert div == Unit.create(numerator=[PowerUnit.MW], denominator=[PowerUnit.KW])


def test_pow_and_root():
    sq = PowerUnit.KW ** 2
    assert isinstance(sq, CompoundUnit)
    assert sq.numerator == [PowerUnit.KW, PowerUnit.KW]

    assert (PowerUnit.KW ** 0) == DimlessUnit()

    with pytest.raises(TypeError):
        _ = PowerUnit.KW ** 2.5

    # valid root
    u = Unit.from_str("kW^2")
    assert u.root(2) == PowerUnit.KW

    # invalid degree
    with pytest.raises(UnitException):
        u.root(0)

    # root not divisible
    u2 = Unit.from_str("kW^3")
    with pytest.raises(ValueError):
        u2.root(2)


def test_as_key_and_str_repr():
    # Basic unit key
    key = PowerUnit.KW.as_key()
    assert key == (((str(PowerUnit.KW), 1),), ())

    # Compound unit string formatting
    cu = CompoundUnit._create(numerator=[PowerUnit.KW, PowerUnit.KW], denominator=[PowerUnit.MW])
    assert str(cu) == "kW^2/MW"
