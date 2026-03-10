import pytest
from contextlib import contextmanager

from ehubx.data.ec_data import EcId, Ecs, ImpExpType, ExceptionKey
from ehubx.data.unit import (
    PowerUnit,
    TimeUnit,
    MassUnit,
    LengthUnit,
    Unit,
)
from ehubx.data.value import Value
from ehubx.data import exceptions


@contextmanager
def raises_with_key(exc_type, expected_key):
    with pytest.raises(exc_type) as excinfo:
        yield excinfo
    assert excinfo.value.key == expected_key


def test_add_duplicate_id_raises_duplicate_key():
    ecs = Ecs()
    e = EcId("e1")
    ecs.add_id(e)
    with raises_with_key(exceptions.DuplicateIdException, ExceptionKey.ID_ADD.value):
        ecs.add_id(e)


def test_ids_in_order_returns_sorted_keys():
    ecs = Ecs()
    ecs.add_id(EcId("b"))
    ecs.add_id(EcId("a"))
    ecs.add_id(EcId("c"))
    ordered = ecs.ids_in_order
    assert [x.key for x in ordered] == ["a", "b", "c"]


def test_getters_for_unknown_id_raise_expected_keys():
    ecs = Ecs()
    e = EcId("x")
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.UNIT_GET.value):
        ecs.get_unit(e)
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.IMPEXPTYPE_GET.value):
        ecs.get_imp_exp_type(e)
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.ISENERGY_GET.value):
        ecs.is_energy(e)
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.HEURMAX_GET.value):
        ecs.get_heuristic_max(e)
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.HEURSUMMAX_GET.value):
        ecs.get_heuristic_sum_max(e)


def test_set_and_get_unit_and_invalid_unit():
    ecs = Ecs()
    e = EcId("e1")
    ecs.add_id(e)

    ecs.set_unit(e, MassUnit.KG)
    assert ecs.get_unit(e) == MassUnit.KG

    ecs.set_unit(e, PowerUnit.KW * TimeUnit.H)
    assert ecs.get_unit(e) == PowerUnit.KW * TimeUnit.H

    # Invalid unit (power alone) should raise UnitException
    with pytest.raises(exceptions.UnitException):
        ecs.set_unit(e, PowerUnit.KW)

    # Completely unrelated unit also raises
    with pytest.raises(exceptions.UnitException):
        ecs.set_unit(e, LengthUnit.M)


def test_imp_exp_and_is_energy_behaviour_and_keys():
    ecs = Ecs()
    e = EcId("e1")
    ecs.add_id(e)

    # imp/exp default
    assert ecs.get_imp_exp_type(e) == ImpExpType.NONE
    ecs.set_imp_exp_type(e, ImpExpType.CROSS)
    assert ecs.get_imp_exp_type(e) == ImpExpType.CROSS

    # is_energy default and set
    assert ecs.is_energy(e) is True
    ecs.set_is_energy(e, False)
    assert ecs.is_energy(e) is False

    # setting on unknown id raises UnknownIdException with correct key
    unknown = EcId("unknown")
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.IMPEXPTYPE_SET.value):
        ecs.set_imp_exp_type(unknown, ImpExpType.INTERNAL)
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.ISENERGY_SET.value):
        ecs.set_is_energy(unknown, True)


def test_heuristic_max_and_sum_behaviour():
    ecs = Ecs()
    e = EcId("e1")
    ecs.add_id(e)
    ecs.set_unit(e, PowerUnit.KW * TimeUnit.H)  # kWh

    # get_heuristic_max not set -> DataException with HEURMAX_GET
    with raises_with_key(exceptions.DataException, ExceptionKey.HEURMAX_GET.value):
        ecs.get_heuristic_max(e)

    # set heuristic_max with correct unit (kW)
    ecs.set_heuristic_max(e, Value(10.0, Unit.get_def_unit(PowerUnit.KW)))
    assert ecs.get_heuristic_max(e) == Value(10.0, Unit.get_def_unit(PowerUnit.KW))

    # wrong unit for heuristic_max (kg) -> UnitException
    with pytest.raises(exceptions.UnitException):
        ecs.set_heuristic_max(e, Value(5.0, MassUnit.KG))

    # negative value -> DataException with HEURMAX_SET
    with raises_with_key(exceptions.DataException, ExceptionKey.HEURMAX_SET.value):
        ecs.set_heuristic_max(e, Value(-1.0, Unit.get_def_unit(PowerUnit.KW)))

    # heuristic_sum_max default is inf with ec unit
    sum_val = ecs.get_heuristic_sum_max(e)
    assert sum_val.unit.same_type_as(ecs.get_unit(e))
    assert not sum_val.is_finite

    # set heuristic_sum_max with correct unit (kWh)
    ecs.set_heuristic_sum_max(e, Value(100.0, ecs.get_unit(e)))
    assert ecs.get_heuristic_sum_max(e) == Value(100.0, ecs.get_unit(e))

    # wrong unit for heuristic_sum_max -> UnitException
    with pytest.raises(exceptions.UnitException):
        ecs.set_heuristic_sum_max(e, Value(1.0, MassUnit.KG))

    # negative -> DataException with HEURSUMMAX_SET
    with raises_with_key(exceptions.DataException, ExceptionKey.HEURSUMMAX_SET.value):
        ecs.set_heuristic_sum_max(e, Value(-1.0, ecs.get_unit(e)))
