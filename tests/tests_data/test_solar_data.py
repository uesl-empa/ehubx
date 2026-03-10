import pytest
from contextlib import contextmanager

from ehubx.data.solar_data import SolarData, ExceptionKey, LOG_MODULE_STR
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.time_data import TimeId, Times
from ehubx.data.time_series import TimeSeries
from ehubx.data.time_series import TimeSeries as TS
from ehubx.data.time_series import TimeSeries
from ehubx.data.time_series import TimeSeries
from ehubx.data.time_series import TimeSeries
from ehubx.data.time_series import TimeSeries
from ehubx.data.time_series import TimeSeries
from ehubx.data.value import Value
from ehubx.data.unit import PowerUnit, TimeUnit, LengthUnit, MassUnit, Unit
from ehubx.data import exceptions
from ehubx.core.common import TimeSeriesKind


@contextmanager
def raises_with_key(exc_type, expected_key):
    with pytest.raises(exc_type) as excinfo:
        yield excinfo
    assert excinfo.value.key == expected_key


def test_add_duplicate_ec_raises_expected_key():
    sd = SolarData()
    e = EcId("e1")
    sd.add_ec(e, Unit.get_def_unit(PowerUnit.KW * TimeUnit.H))
    with raises_with_key(exceptions.DataException, ExceptionKey.ECS_ADD.value):
        sd.add_ec(e, Unit.get_def_unit(PowerUnit.KW * TimeUnit.H))


def test_get_irradiation_without_ec_raises():
    sd = SolarData()
    s = StageId("s1")
    e = EcId("e_missing")
    with raises_with_key(exceptions.DataException, ExceptionKey.IRRADIATION_GET.value):
        sd.get_irradiation(s, e)


def test_set_and_get_irradiation_and_default_and_time_series():
    sd = SolarData()
    e = EcId("solar1")
    ec_unit = Unit.get_def_unit(PowerUnit.KW * TimeUnit.H)
    sd.add_ec(e, ec_unit)

    s = StageId("st1")
    t = TimeId(1)

    # prepare supporting data
    stages = Stages()
    stages.add_id(s)
    times = Times()
    times.add_id(t)

    # default get_irradiation returns a TimeSeries with default value 0
    ts = sd.get_irradiation(s, e)
    assert isinstance(ts, TimeSeries)
    assert ts.def_value == Value(0, ec_unit / (TimeUnit.H * LengthUnit.M ** 2))

    # set a value and retrieve it
    unit_expected = Unit.get_def_unit(ec_unit / (TimeUnit.H * LengthUnit.M ** 2))
    sd.set_irradiation(s, e, t, Value(5.5, unit_expected))
    assert sd.get_irradiation(s, e).get_value(t) == Value(5.5, unit_expected)

    # time_series property should list the irradiation with the ec key
    all_ts = sd.time_series
    assert any(
        kind == TimeSeriesKind.SOLARIRRAD and ids == (e.key,) and series.get_value(t) == Value(5.5, unit_expected)
        for kind, stage, ids, series in all_ts
    )

    # set using the generic setter (float value) - should accept and store
    sd2 = SolarData()
    sd2.add_ec(e, ec_unit)
    sd2.set_time_series_val(TimeSeriesKind.SOLARIRRAD, s, (e.key,), t, 2.0)
    assert sd2.get_irradiation(s, e).get_value(t).to_float(unit_expected) == 2.0


def test_set_irradiation_def_and_validate_negative_default_raises():
    sd = SolarData()
    e = EcId("solar2")
    ec_unit = Unit.get_def_unit(PowerUnit.KW * TimeUnit.H)
    sd.add_ec(e, ec_unit)

    s = StageId("st1")

    # set default negative irradiation and expect validation to fail
    unit_expected = Unit.get_def_unit(ec_unit / (TimeUnit.H * LengthUnit.M ** 2))
    sd.set_irradiation_def(s, e, Value(-0.1, unit_expected))

    stages = Stages()
    stages.add_id(s)
    times = Times()
    # Include ec in Ecs with matching unit so validation proceeds to irradiation checks
    ecs = Ecs()
    ecs.add_id(e)
    ecs.set_unit(e, ec_unit)
    with raises_with_key(exceptions.DataException, ExceptionKey.IRRADIATION_VAL.value):
        sd.validate(stages, Hubs(), ecs, times)


def test_set_area_unit_mismatch_and_negative_validation():
    sd = SolarData()
    e = EcId("solar3")
    ec_unit = Unit.get_def_unit(PowerUnit.KW * TimeUnit.H)
    sd.add_ec(e, ec_unit)

    s = StageId("stA")
    h = HubId("hub1")

    stages = Stages()
    stages.add_id(s)
    hubs = Hubs()
    hubs.add_id(h)

    # wrong unit on set -> AREA_SET
    with raises_with_key(exceptions.DataException, ExceptionKey.AREA_SET.value):
        sd.set_area(s, h, e, Value(1.0, MassUnit.KG))

    # set negative area with correct unit -> AREA_VAL on validate
    sd.set_area(s, h, e, Value(-5.0, LengthUnit.M ** 2))
    times = Times()
    # Include ec in Ecs with matching unit so validation proceeds to area checks
    ecs = Ecs()
    ecs.add_id(e)
    ecs.set_unit(e, ec_unit)
    with raises_with_key(exceptions.DataException, ExceptionKey.AREA_VAL.value):
        sd.validate(stages, hubs, ecs, times)


def test_validate_ecs_unknown_and_unit_mismatch():
    sd = SolarData()
    e = EcId("e_unknown")
    # add ec to solar data but do not add it to Ecs -> Should raise ECS_VAL
    sd.add_ec(e, Unit.get_def_unit(PowerUnit.KW * TimeUnit.H))

    with raises_with_key(exceptions.DataException, ExceptionKey.ECS_VAL.value):
        sd.validate(Stages(), Hubs(), Ecs(), Times())

    # Now add the ec to Ecs but with a different unit -> unit mismatch
    ecs = Ecs()
    ecs.add_id(e)
    ecs.set_unit(e, MassUnit.KG)

    with raises_with_key(exceptions.DataException, ExceptionKey.ECS_VAL.value):
        sd.validate(Stages(), Hubs(), ecs, Times())
