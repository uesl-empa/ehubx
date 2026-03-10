import pytest

from ehubx.data.time_series import (
    TimeSeries,
    TimeSeriesFloat,
    ExceptionKey as TSExceptionKey,
)
from ehubx.data.time_data import TimeId, Times
from ehubx.data.value import Value
from ehubx.data.unit import PowerUnit, CurrencyUnit
from ehubx.data import exceptions


def test_exception_key_literals():
    assert TSExceptionKey.VALUE_GET.value == "getting 'value' from Times"
    assert TSExceptionKey.VALUE_REMOVE.value == "removing 'value' from Times"


def test_time_series_set_get_and_unit_mismatch():
    ts = TimeSeries()
    t1 = TimeId(1)

    # set a value with a power unit
    v_kw = Value(5.0, PowerUnit.KW)
    ts.set_value(t1, v_kw)
    assert ts.get_value(t1) == v_kw

    # setting a value with incompatible unit should raise UnitException
    with pytest.raises(exceptions.UnitException):
        ts.set_value(TimeId(2), Value(1.0, CurrencyUnit.EUR))


def test_time_series_missing_get_raises_expected_key():
    ts = TimeSeries()
    t = TimeId(1)

    with pytest.raises(exceptions.MissingIdException) as excinfo:
        ts.get_value(t)
    assert excinfo.value.key == TSExceptionKey.VALUE_GET.value


def test_time_series_def_value_and_remove_clear_behavior():
    ts = TimeSeries()
    t1 = TimeId(1)
    t2 = TimeId(2)

    # default value is returned when specific value missing
    ts.def_value = Value(3.0, PowerUnit.KW)
    assert ts.get_value(t1) == ts.def_value

    # set explicit values
    ts.set_value(t1, Value(10.0, PowerUnit.KW))
    ts.set_value(t2, Value(1.0, PowerUnit.KW))
    assert ts.has_values
    assert ts.num_values == 2

    # remove one value
    ts.remove_value(t2)
    assert ts.num_values == 1

    # clear all
    ts.clear()
    assert not ts.has_values
    assert ts.num_values == 0


def test_time_series_min_max_and_inf_defaults():
    ts = TimeSeries()

    # when there are no values and no def_value, max/min are +/- inf
    assert ts.max.to_float() == pytest.approx(float("inf"))
    assert ts.min.to_float() == pytest.approx(float("-inf"))

    # default value will be returned by min/max when present
    ts.def_value = Value(4.0)
    assert ts.max == ts.def_value
    assert ts.min == ts.def_value


def test_time_series_validate_raises_unknown_key_on_invalid_id():
    ts = TimeSeries()
    t_known = TimeId(1)
    t_unknown = TimeId(2)

    ts.set_value(t_unknown, Value(1.0, PowerUnit.KW))

    times = Times()
    times.add_id(t_known)

    with pytest.raises(exceptions.UnknownIdException) as excinfo:
        ts.validate(times, "my_exc_key", module="m")
    assert excinfo.value.key == "my_exc_key"


def test_time_series_float_basic_and_exceptions():
    tsf = TimeSeriesFloat()
    t = TimeId(1)

    # default missing raises MissingIdException with correct key
    with pytest.raises(exceptions.MissingIdException) as excinfo:
        tsf.get_value(t)
    assert excinfo.value.key == TSExceptionKey.VALUE_GET.value

    # default value usage
    tsf.def_value = 2.5
    assert tsf.get_value(t) == pytest.approx(2.5)

    # set and remove
    tsf.set_value(t, 7.5)
    assert tsf.get_value(t) == pytest.approx(7.5)
    tsf.remove_value(t)
    assert tsf.get_value(t) == pytest.approx(2.5)

    # validate unknown ids
    tsf.set_value(TimeId(2), 1.0)
    times = Times()
    times.add_id(TimeId(3))
    with pytest.raises(exceptions.UnknownIdException) as excinfo2:
        tsf.validate(times, "float_val_key", module="m")
    assert excinfo2.value.key == "float_val_key"
