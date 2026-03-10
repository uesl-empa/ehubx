import pytest
from contextlib import contextmanager

from ehubx.data.export_data import Exports, ExceptionKey
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.time_data import TimeId, Times
from ehubx.data.time_series import TimeSeries
from ehubx.data.value import Value
from ehubx.data.unit import PowerUnit, TimeUnit, CurrencyUnit, MassUnit, Unit
from ehubx.data import exceptions
from ehubx.core.common import TimeSeriesKind


@contextmanager
def raises_with_key(exc_type, expected_key):
    with pytest.raises(exc_type) as excinfo:
        yield excinfo
    assert excinfo.value.key == expected_key


def make_basic_context():
    s = StageId("s1")
    h = HubId("h1")
    e = EcId("e1")
    t = TimeId(1)

    stages = Stages()
    hubs = Hubs()
    ecs = Ecs()
    times = Times()

    stages.add_id(s)
    hubs.add_id(h)
    ecs.add_id(e)
    # set ec unit to kWh (Power * Time)
    ecs.set_unit(e, PowerUnit.KW * TimeUnit.H)
    times.add_id(t)

    return s, h, e, t, stages, hubs, ecs, times


def test_add_duplicate_tuple_raises_expected_key():
    exports = Exports()
    s, h, e, t, stages, hubs, ecs, times = make_basic_context()

    exports.add_tuple(s, h, e, ecs.get_unit(e))
    with raises_with_key(exceptions.DataException, ExceptionKey.TUPLES_ADD.value):
        exports.add_tuple(s, h, e, ecs.get_unit(e))


def test_set_price_before_tuple_raises_expected_key():
    exports = Exports()
    s, h, e, t, stages, hubs, ecs, times = make_basic_context()

    with raises_with_key(exceptions.DataException, ExceptionKey.PRICE_SET.value):
        exports.set_price(s, h, e, t, Value(1.0, CurrencyUnit.CHF))


def test_set_and_get_price_and_time_series_setter():
    exports = Exports()
    s, h, e, t, stages, hubs, ecs, times = make_basic_context()

    exports.add_tuple(s, h, e, ecs.get_unit(e))

    # default price should be available and have the expected unit
    price_ts = exports.get_price(s, h, e)
    assert isinstance(price_ts, TimeSeries)
    assert price_ts.def_value == Value(0, CurrencyUnit.CHF / ecs.get_unit(e))

    # set a price for a known time id
    price_unit = Unit.get_def_unit(CurrencyUnit.CHF / ecs.get_unit(e))
    exports.set_price(s, h, e, t, Value(5.0, price_unit))
    assert price_ts.get_value(t) == Value(5.0, price_unit)

    # set using set_time_series_val should also work for EXPORTPRICE
    exports.set_time_series_val(TimeSeriesKind.EXPORTPRICE, s, (h.key, e.key), t, 7.5)
    assert price_ts.get_value(t) == Value(7.5, price_unit)

    # also test EXPORTMIN/EXPORTMAX/EXPORTCO2 time series setting
    exports.set_time_series_val(TimeSeriesKind.EXPORTMIN, s, (h.key, e.key), t, 1.0)
    min_ts = exports.get_min(s, h, e)
    val_min = min_ts.get_value(t)
    assert val_min == Value(1.0, Unit.get_def_unit(val_min.unit))

    exports.set_time_series_val(TimeSeriesKind.EXPORTMAX, s, (h.key, e.key), t, 10.0)
    max_ts = exports.get_max(s, h, e)
    val_max = max_ts.get_value(t)
    assert val_max == Value(10.0, Unit.get_def_unit(val_max.unit))

    exports.set_time_series_val(TimeSeriesKind.EXPORTCO2, s, (h.key, e.key), t, 0.2)
    co2_ts = exports.get_co2(s, h, e)
    val_co2 = co2_ts.get_value(t)
    assert val_co2 == Value(0.2, Unit.get_def_unit(val_co2.unit))


def test_validate_unknown_time_raises_with_price_key():
    exports = Exports()
    s, h, e, t, stages, hubs, ecs, times = make_basic_context()

    # add tuple and set a price for a time id not in times
    exports.add_tuple(s, h, e, ecs.get_unit(e))
    other_t = TimeId(99)
    price_unit = Unit.get_def_unit(CurrencyUnit.CHF / ecs.get_unit(e))
    exports.set_price(s, h, e, other_t, Value(1.0, price_unit))

    # validate should complain about unknown time id in price with PRICE_VAL key
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.PRICE_VAL.value):
        exports.validate(stages, hubs, ecs, times)


def test_min_max_minmax_validation():
    exports = Exports()
    s, h, e, t, stages, hubs, ecs, times = make_basic_context()

    exports.add_tuple(s, h, e, ecs.get_unit(e))

    # set defaults such that min > max
    # units for min/max are ec_unit / TimeUnit.H
    unit_minmax = Unit.get_def_unit(ecs.get_unit(e) / TimeUnit.H)
    exports.set_min_def(s, h, e, Value(10.0, unit_minmax))
    exports.set_max_def(s, h, e, Value(5.0, unit_minmax))

    with raises_with_key(exceptions.DataException, ExceptionKey.MINMAX_VAL.value):
        exports.validate(stages, hubs, ecs, times)


def test_sum_min_max_validation():
    exports = Exports()
    s, h, e, t, stages, hubs, ecs, times = make_basic_context()

    exports.add_tuple(s, h, e, ecs.get_unit(e))

    # sum units are in ec unit
    exports.set_sum_min(s, h, e, Value(200.0, ecs.get_unit(e)))
    exports.set_sum_max(s, h, e, Value(100.0, ecs.get_unit(e)))

    with raises_with_key(exceptions.DataException, ExceptionKey.SUMMINMAX_VAL.value):
        exports.validate(stages, hubs, ecs, times)


def test_validate_tuples_unknown_ids_raises_tuples_val():
    exports = Exports()
    s, h, e, t, stages, hubs, ecs, times = make_basic_context()

    # add tuple but do not add the stage/hub/ec to their data classes
    exports.add_tuple(s, h, e, ecs.get_unit(e))

    # create empty data classes so ids missing
    stages_empty = Stages()
    hubs_empty = Hubs()
    ecs_empty = Ecs()

    with raises_with_key(exceptions.DataException, ExceptionKey.TUPLES_VAL.value):
        exports.validate(stages_empty, hubs_empty, ecs_empty, times)
