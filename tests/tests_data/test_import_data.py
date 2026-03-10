import pytest

from ehubx.data.import_data import Imports, ExceptionKey
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.time_data import TimeId, Times
from ehubx.data.value import Value
from ehubx.data.unit import PowerUnit, TimeUnit, CurrencyUnit
from ehubx.data.exceptions import DataException
from ehubx.core.common import TimeSeriesKind


def make_basic_ids():
    s = StageId("s1")
    h = HubId("h1")
    e = EcId("e1")
    return s, h, e


def test_add_tuple_and_basic_time_series_behavior():
    imp = Imports()
    s, h, e = make_basic_ids()

    # add ids to their registries
    stages = Stages()
    stages.add_id(s)
    hubs = Hubs()
    hubs.add_id(h)
    ecs = Ecs()
    ecs.add_id(e)

    # give ec a unit (energy unit)
    energy_unit = PowerUnit.KW * TimeUnit.H
    ecs.set_unit(e, energy_unit)

    # add tuple
    imp.add_tuple(s, h, e, energy_unit)

    assert (s, h, e) in imp.tuples

    # times and a timestep
    times = Times()
    t = TimeId(1)
    times.add_id(t)

    # set and get price
    price_value = Value(10.0, CurrencyUnit.CHF / energy_unit)
    imp.set_price(s, h, e, t, price_value)

    got_price = imp.get_price(s, h, e)
    assert got_price.get_value(t) == price_value

    # set and get max/min
    imp.set_max(s, h, e, t, Value(5.0, ecs.get_unit(e) / TimeUnit.H))
    imp.set_min(s, h, e, t, Value(1.0, ecs.get_unit(e) / TimeUnit.H))

    got_max = imp.get_max(s, h, e)
    got_min = imp.get_min(s, h, e)
    assert got_max.get_value(t).to_float(got_max.get_value(t).unit) == pytest.approx(5.0)
    assert got_min.get_value(t).to_float(got_min.get_value(t).unit) == pytest.approx(1.0)

    # time_series listing includes entries for set values
    series_kinds = [s_kind for s_kind, _, _, _ in imp.time_series]
    assert TimeSeriesKind.IMPORTPRICE in series_kinds
    assert TimeSeriesKind.IMPORTMAX in series_kinds
    assert TimeSeriesKind.IMPORTMIN in series_kinds

    # set via set_time_series_val using default units
    imp.set_time_series_val(TimeSeriesKind.IMPORTPRICE, s, (h.key, e.key), t, 20.0)
    assert imp.get_price(s, h, e).get_value(t).to_float(imp.get_price(s, h, e).get_value(t).unit) == pytest.approx(20.0)


def test_duplicate_tuple_raises_with_correct_exception_key():
    imp = Imports()
    s, h, e = make_basic_ids()
    unit = PowerUnit.KW * TimeUnit.H
    imp.add_tuple(s, h, e, unit)

    with pytest.raises(DataException) as excinfo:
        imp.add_tuple(s, h, e, unit)

    assert excinfo.value.key == ExceptionKey.TUPLES_ADD.value


def test_get_price_on_unknown_tuple_raises_with_correct_exception_key():
    imp = Imports()
    s, h, e = make_basic_ids()

    with pytest.raises(DataException) as excinfo:
        imp.get_price(s, h, e)
    assert excinfo.value.key == ExceptionKey.PRICE_GET.value


def test_validate_detects_unknown_tuple_members():
    imp = Imports()
    s, h, e = make_basic_ids()
    unit = PowerUnit.KW * TimeUnit.H
    imp.add_tuple(s, h, e, unit)

    # Do not add s/h/e to Stages/Hubs/Ecs so validate should complain
    stages = Stages()
    hubs = Hubs()
    ecs = Ecs()
    times = Times()

    with pytest.raises(DataException) as excinfo:
        imp.validate(stages, hubs, ecs, times)
    assert excinfo.value.key == ExceptionKey.TUPLES_VAL.value


def test_validate_detects_price_unit_mismatch():
    imp = Imports()
    s, h, e = make_basic_ids()
    # Add tuple with energy unit
    energy_unit = PowerUnit.KW * TimeUnit.H
    imp.add_tuple(s, h, e, energy_unit)

    # Register ids
    stages = Stages(); stages.add_id(s)
    hubs = Hubs(); hubs.add_id(h)
    ecs = Ecs(); ecs.add_id(e)
    # Do NOT set ec unit in ecs -> default is dimless -> expected price unit will not match

    times = Times()
    t = TimeId(1); times.add_id(t)

    with pytest.raises(DataException) as excinfo:
        imp.validate(stages, hubs, ecs, times)
    assert excinfo.value.key == ExceptionKey.PRICE_VAL.value


def test_validate_detects_negative_max_value():
    imp = Imports()
    s, h, e = make_basic_ids()
    energy_unit = PowerUnit.KW * TimeUnit.H
    imp.add_tuple(s, h, e, energy_unit)

    # register ids
    stages = Stages(); stages.add_id(s)
    hubs = Hubs(); hubs.add_id(h)
    ecs = Ecs(); ecs.add_id(e); ecs.set_unit(e, energy_unit)

    times = Times(); t = TimeId(1); times.add_id(t)

    imp.set_max(s, h, e, t, Value(-1.0, ecs.get_unit(e) / TimeUnit.H))

    with pytest.raises(DataException) as excinfo:
        imp.validate(stages, hubs, ecs, times)
    assert excinfo.value.key == ExceptionKey.MAX_VAL.value


def test_validate_detects_min_greater_than_max():
    imp = Imports()
    s, h, e = make_basic_ids()
    energy_unit = PowerUnit.KW * TimeUnit.H
    imp.add_tuple(s, h, e, energy_unit)

    stages = Stages(); stages.add_id(s)
    hubs = Hubs(); hubs.add_id(h)
    ecs = Ecs(); ecs.add_id(e); ecs.set_unit(e, energy_unit)

    times = Times(); t = TimeId(1); times.add_id(t)

    imp.set_min(s, h, e, t, Value(10.0, ecs.get_unit(e) / TimeUnit.H))
    imp.set_max(s, h, e, t, Value(5.0, ecs.get_unit(e) / TimeUnit.H))

    with pytest.raises(DataException) as excinfo:
        imp.validate(stages, hubs, ecs, times)
    assert excinfo.value.key == ExceptionKey.MINMAX_VAL.value


def test_validate_detects_sum_min_greater_than_sum_max():
    imp = Imports()
    s, h, e = make_basic_ids()
    energy_unit = PowerUnit.KW * TimeUnit.H
    imp.add_tuple(s, h, e, energy_unit)

    stages = Stages(); stages.add_id(s)
    hubs = Hubs(); hubs.add_id(h)
    ecs = Ecs(); ecs.add_id(e); ecs.set_unit(e, energy_unit)

    imp.set_sum_min(s, h, e, Value(100.0, ecs.get_unit(e)))
    imp.set_sum_max(s, h, e, Value(10.0, ecs.get_unit(e)))

    with pytest.raises(DataException) as excinfo:
        imp.validate(stages, hubs, ecs, Times())
    assert excinfo.value.key == ExceptionKey.SUMMINMAX_VAL.value
