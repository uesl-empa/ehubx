import pytest

from ehubx.data.load_shedding_data import (
    LoadShedding,
    ExceptionKey,
    DEF_ENABLED,
    DEF_MAXREL,
)
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.demand_data import Demands
from ehubx.data.time_data import TimeId, Times
from ehubx.data.value import Value
from ehubx.data.unit import PowerUnit, TimeUnit, DimlessUnit, CurrencyUnit, Unit
from ehubx.data.exceptions import DataException
from ehubx.core.common import TimeSeriesKind


def raises_with_key(exc_type, expected_key):
    with pytest.raises(exc_type) as excinfo:
        yield excinfo
    assert excinfo.value.key == expected_key


def make_basic_env():
    s = StageId("S1")
    h = HubId("H1")
    e = EcId("E0")

    stages = Stages()
    stages.add_id(s)

    hubs = Hubs()
    hubs.add_id(h)

    ecs = Ecs()
    ecs.add_id(e)
    # set ec unit to an energy unit (kWh equivalent: kW*h)
    ecs.set_unit(e, PowerUnit.KW * TimeUnit.H)

    demands = Demands()
    demands.add_profile_tuple(s, h, e, ecs.get_unit(e))

    times = Times()
    times.add_id(TimeId(1))
    times.add_id(TimeId(2))

    return s, h, e, stages, hubs, ecs, demands, times


def test_add_tuple_defaults():
    s, h, e, stages, hubs, ecs, demands, times = make_basic_env()
    ls = LoadShedding()

    ls.add_tuple(s, h, e, ecs.get_unit(e))

    assert (s, h, e) in ls.tuples
    # enabled default
    assert ls.is_enabled(s, h, e) == DEF_ENABLED

    # max_abs default is inf and unit is ec_unit / h
    max_abs = ls.get_max_abs(s, h, e)
    assert not max_abs.def_value.is_finite
    expected_unit = ecs.get_unit(e) / TimeUnit.H
    assert max_abs.def_value.unit.same_type_as(expected_unit)

    # max_rel default
    max_rel = ls.get_max_rel(s, h, e)
    assert max_rel.def_value == Value(DEF_MAXREL)
    assert isinstance(max_rel.def_value.unit, DimlessUnit)

    # energy_cost default unit should be CurrencyUnit.CHF / ec_unit
    energy_cost = ls.get_energy_cost(s, h, e)
    assert energy_cost.def_value.unit.same_type_as(CurrencyUnit.CHF / ecs.get_unit(e))


def test_enabled_toggle_and_get_enabled_tuples():
    s, h, e, stages, hubs, ecs, demands, times = make_basic_env()
    ls = LoadShedding()
    ls.add_tuple(s, h, e, ecs.get_unit(e))

    assert ls.get_enabled_tuples() == {(s, h, e)}

    ls.set_enabled(s, h, e, False)
    assert ls.get_enabled_tuples() == set()

    ls.set_enabled(s, h, e, True)
    assert ls.get_enabled_tuples() == {(s, h, e)}


def test_id_checks_raise_data_exceptions_with_expected_keys():
    s = StageId("Sx")
    h = HubId("Hx")
    e = EcId("Ex")
    ls = LoadShedding()

    with pytest.raises(DataException) as excinfo:
        ls.is_enabled(s, h, e)
    assert excinfo.value.key == ExceptionKey.ENABLED_GET.value

    with pytest.raises(DataException) as excinfo:
        ls.set_enabled(s, h, e, True)
    assert excinfo.value.key == ExceptionKey.ENABLED_SET.value

    with pytest.raises(DataException) as excinfo:
        ls.get_max_abs(s, h, e)
    assert excinfo.value.key == ExceptionKey.MAXABS_GET.value

    with pytest.raises(DataException) as excinfo:
        ls.set_max_abs(s, h, e, TimeId(1), Value(1.0))
    assert excinfo.value.key == ExceptionKey.MAXABS_SET.value

    with pytest.raises(DataException) as excinfo:
        ls.set_max_abs_def(s, h, e, Value(1.0))
    assert excinfo.value.key == ExceptionKey.MAXABS_DEFSET.value

    with pytest.raises(DataException) as excinfo:
        ls.get_max_rel(s, h, e)
    assert excinfo.value.key == ExceptionKey.MAXREL_GET.value

    with pytest.raises(DataException) as excinfo:
        ls.get_energy_cost(s, h, e)
    assert excinfo.value.key == ExceptionKey.ENERGYCOST_GET.value


def test_set_max_rel_unit_check_raises_expected_key():
    s, h, e, stages, hubs, ecs, demands, times = make_basic_env()
    ls = LoadShedding()
    ls.add_tuple(s, h, e, ecs.get_unit(e))

    # Wrong unit (not dimless)
    with pytest.raises(DataException) as excinfo:
        ls.set_max_rel(s, h, e, TimeId(1), Value(1.0, PowerUnit.KW))
    assert excinfo.value.key == ExceptionKey.MAXREL_SET.value

    # Wrong default unit
    with pytest.raises(DataException) as excinfo:
        ls.set_max_rel_def(s, h, e, Value(1.0, PowerUnit.KW))
    assert excinfo.value.key == ExceptionKey.MAXREL_DEFSET.value


def test_set_time_series_val_sets_values_correctly():
    s, h, e, stages, hubs, ecs, demands, times = make_basic_env()
    ls = LoadShedding()
    ls.add_tuple(s, h, e, ecs.get_unit(e))

    # LOADSHEDMAXABS
    ls.set_time_series_val(TimeSeriesKind.LOADSHEDMAXABS, s, (h.key, e.key), TimeId(1), 5.0)
    assert ls.get_max_abs(s, h, e).get_value(TimeId(1)).to_float(ecs.get_unit(e) / TimeUnit.H) == pytest.approx(5.0)

    # LOADSHEDMAXREL
    ls.set_time_series_val(TimeSeriesKind.LOADSHEDMAXREL, s, (h.key, e.key), TimeId(1), 0.5)
    assert ls.get_max_rel(s, h, e).get_value(TimeId(1)).to_float(DimlessUnit()) == pytest.approx(0.5)

    # LOADSHEDENERGYCOST
    ls.set_time_series_val(TimeSeriesKind.LOADSHEDENERGYCOST, s, (h.key, e.key), TimeId(1), 10.0)
    # energy cost unit is CurrencyUnit.CHF / ecs.get_unit(e)
    assert ls.get_energy_cost(s, h, e).get_value(TimeId(1)).to_float(CurrencyUnit.CHF / ecs.get_unit(e)) == pytest.approx(10.0)


def test_validate_checks_units_and_ranges_raise_expected_keys():
    s, h, e, stages, hubs, ecs, demands, times = make_basic_env()
    ls = LoadShedding()
    ls.add_tuple(s, h, e, ecs.get_unit(e))

    # Set a max_abs time value that is negative -> validation should fail
    ls.set_max_abs(s, h, e, TimeId(1), Value(-1.0, ecs.get_unit(e) / TimeUnit.H))
    with pytest.raises(DataException) as excinfo:
        ls.validate(stages, hubs, ecs, demands, times)
    assert excinfo.value.key == ExceptionKey.MAXABS_VAL.value

    # Fix max_abs then set negative max_rel time value -> validation should fail
    ls.get_max_abs(s, h, e).clear()
    ls.set_max_abs(s, h, e, TimeId(1), Value(5.0, ecs.get_unit(e) / TimeUnit.H))

    ls.set_max_rel(s, h, e, TimeId(1), Value(-0.5, DimlessUnit()))
    with pytest.raises(DataException) as excinfo:
        ls.validate(stages, hubs, ecs, demands, times)
    assert excinfo.value.key == ExceptionKey.MAXREL_VAL.value

    # Fix max_rel then corrupt energy_cost unit to trigger validation unit-check
    ls.get_max_rel(s, h, e).clear()
    ls.set_max_rel(s, h, e, TimeId(1), Value(0.5, DimlessUnit()))

    # corrupt unit (simulate bad internal state)
    ls._energy_cost[s, h, e]._unit = DimlessUnit()
    with pytest.raises(DataException) as excinfo:
        ls.validate(stages, hubs, ecs, demands, times)
    assert excinfo.value.key == ExceptionKey.ENERGYCOST_VAL.value


def test_validate_tuple_checks_against_demands_and_other_ids():
    # Unknown stage
    s, h, e, stages, hubs, ecs, demands, times = make_basic_env()
    ls = LoadShedding()
    # add tuple with a stage that won't be in stages passed to validate
    s_unknown = StageId("S_unknown")
    ls.add_tuple(s_unknown, h, e, ecs.get_unit(e))
    with pytest.raises(DataException) as excinfo:
        ls.validate(Stages(), hubs, ecs, demands, times)
    assert excinfo.value.key == ExceptionKey.TUPLES_VAL.value

    # Not a demand tuple
    ls = LoadShedding()
    ls.add_tuple(s, h, e, ecs.get_unit(e))
    # remove demand info so (s,h,e) is not a demand profile tuple
    demands_empty = Demands()
    with pytest.raises(DataException) as excinfo:
        ls.validate(stages, hubs, ecs, demands_empty, times)
    assert excinfo.value.key == ExceptionKey.TUPLES_VAL.value
