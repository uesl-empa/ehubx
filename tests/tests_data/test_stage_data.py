import pytest

from ehubx.data import exceptions
from ehubx.data.stage_data import Stages, StageId, ExceptionKey
from ehubx.data.value import Value
from ehubx.data.unit import MassUnit, CurrencyUnit


def test_add_duplicate_id_raises_duplicateid():
    stages = Stages()
    s = StageId("s1")
    stages.add_id(s)
    with pytest.raises(exceptions.DuplicateIdException) as excinfo:
        stages.add_id(s)
    assert excinfo.value.key == ExceptionKey.ID_ADD.value


def test_get_start_year_unknown_id_raises_unknownid():
    stages = Stages()
    s = StageId("unknown")
    with pytest.raises(exceptions.UnknownIdException) as excinfo:
        stages.get_start_year(s)
    assert excinfo.value.key == ExceptionKey.STARTYEAR_GET.value


def test_get_start_year_missing_raises_missingid():
    stages = Stages()
    s = StageId("s2")
    stages.add_id(s)
    with pytest.raises(exceptions.MissingIdException) as excinfo:
        stages.get_start_year(s)
    assert excinfo.value.key == ExceptionKey.STARTYEAR_GET.value


def test_set_and_get_start_year_and_ids_in_order():
    stages = Stages()
    a = StageId("a")
    b = StageId("b")
    c = StageId("c")
    for sid in (a, b, c):
        stages.add_id(sid)
    stages.set_start_year(a, 2020)
    stages.set_start_year(b, 2010)
    stages.set_start_year(c, 2030)

    assert stages.get_start_year(a) == 2020
    assert stages.get_start_year(b) == 2010
    assert stages.get_start_year(c) == 2030

    ids_in_order = stages.ids_in_order
    assert ids_in_order == [b, a, c]


def test_co2_price_defaults_and_wrong_unit():
    stages = Stages()
    s = StageId("s3")
    stages.add_id(s)

    co2_price = stages.get_co2_price(s)
    assert isinstance(co2_price, Value)
    # default price is 0
    assert co2_price.to_float() == 0
    expected_unit = CurrencyUnit.CHF / MassUnit.KG
    assert co2_price.unit.same_type_as(expected_unit)

    # setting wrong unit should raise DataException with correct key
    with pytest.raises(exceptions.DataException) as excinfo:
        stages.set_co2_price(s, Value(1.0, MassUnit.KG))
    assert excinfo.value.key == ExceptionKey.CO2PRICE_SET.value


def test_co2_min_max_defaults_and_wrong_unit():
    stages = Stages()
    s = StageId("s4")
    stages.add_id(s)

    co2_min = stages.get_co2_min(s)
    co2_max = stages.get_co2_max(s)
    assert isinstance(co2_min, Value)
    assert isinstance(co2_max, Value)
    assert co2_min.to_float() == float("-inf")
    assert co2_max.to_float() == float("inf")

    with pytest.raises(exceptions.DataException) as excinfo_min:
        stages.set_co2_min(s, Value(1.0, CurrencyUnit.CHF))
    assert excinfo_min.value.key == ExceptionKey.CO2MIN_SET.value

    with pytest.raises(exceptions.DataException) as excinfo_max:
        stages.set_co2_max(s, Value(1.0, CurrencyUnit.CHF))
    assert excinfo_max.value.key == ExceptionKey.CO2MAX_SET.value


def test_validate_duplicate_start_years_raises():
    stages = Stages()
    s1 = StageId("dup1")
    s2 = StageId("dup2")
    stages.add_id(s1)
    stages.add_id(s2)
    stages.set_start_year(s1, 2020)
    stages.set_start_year(s2, 2020)

    with pytest.raises(exceptions.DataException) as excinfo:
        stages.validate()
    assert excinfo.value.key == ExceptionKey.STARTYEAR_SET.value


def test_validate_co2_min_greater_than_max_raises():
    stages = Stages()
    s = StageId("s5")
    stages.add_id(s)
    stages.set_start_year(s, 2020)

    stages.set_co2_min(s, Value(2.0, MassUnit.KG))
    stages.set_co2_max(s, Value(1.0, MassUnit.KG))

    with pytest.raises(exceptions.DataException) as excinfo:
        stages.validate()
    assert excinfo.value.key == ExceptionKey.CO2MINMAX_VAL.value
