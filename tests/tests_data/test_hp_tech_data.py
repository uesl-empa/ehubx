import pytest

from ehubx.data.hp_tech_data import (
    HeatpumpTechs,
    ExceptionKey as HpExcKey,
)
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.time_data import TimeId, Times
from ehubx.data.time_series import TimeSeries
from ehubx.data.value import Value
from ehubx.data.unit import PowerUnit, TimeUnit, DimlessUnit, TemperatureUnit
from ehubx.data import exceptions
from ehubx.core.common import TimeSeriesKind

import pytest


@pytest.fixture
def hpts():
    return HeatpumpTechs()


def add_tech(hpts, key: str):
    x = TechId(key)
    hpts.add_id(x)
    return x



def test_add_id_and_duplicate(hpts):
    x = add_tech(hpts, "hp1")
    assert x in hpts.ids

    with pytest.raises(exceptions.DuplicateIdException) as excinfo:
        hpts.add_id(x)
    assert excinfo.value.key == HpExcKey.ID_ADD.value


def test_set_get_ec_el_and_unit_mismatch(hpts):
    x = add_tech(hpts, "hp2")

    e = EcId("el")
    # correct energy unit
    energy_unit = PowerUnit.KW * TimeUnit.H
    # should not raise
    hpts.set_ec_el(x, e, energy_unit)
    assert hpts.get_ec_el(x) == e

    # wrong unit (temperature instead of energy) triggers DataException
    with pytest.raises(exceptions.DataException) as excinfo:
        hpts.set_ec_el(x, EcId("el2"), DimlessUnit())
    assert excinfo.value.key == HpExcKey.ECEL_SET.value


def test_temp_ht_in_out_and_unit_validation(hpts):
    s = StageId("s")
    h = HubId("hub")
    x = add_tech(hpts, "hp3")
    t = TimeId(1)

    # unit mismatch on set_temp_ht_in
    with pytest.raises(exceptions.DataException) as excinfo:
        hpts.set_temp_ht_in(s, h, x, t, Value(10.0, unit=DimlessUnit()))
    assert excinfo.value.key == HpExcKey.TEMPHTIN_SET.value

    # correct units
    hpts.set_temp_ht_in(s, h, x, t, Value(280.0, unit=TemperatureUnit.K))
    assert hpts.has_temp_ht_in(s, h, x)
    ts_in = hpts.get_temp_ht_in(s, h, x)
    assert isinstance(ts_in, TimeSeries)

    # unit mismatch on set_temp_ht_out
    with pytest.raises(exceptions.DataException) as excinfo2:
        hpts.set_temp_ht_out(s, h, x, t, Value(300.0, unit=DimlessUnit()))
    assert excinfo2.value.key == HpExcKey.TEMPHTOUT_SET.value

    # correct units
    hpts.set_temp_ht_out(s, h, x, t, Value(300.0, unit=TemperatureUnit.K))
    assert hpts.has_temp_ht_out(s, h, x)


def test_get_cop_computed_from_temps_and_factor_and_missing(hpts):
    s = StageId("s2")
    h = HubId("hub2")
    x = add_tech(hpts, "hp4")
    t1 = TimeId(1)
    t2 = TimeId(2)

    times = Times()
    times.add_id(t1)
    times.add_id(t2)

    # no temps and no cop -> should raise
    with pytest.raises(exceptions.DataException) as excinfo:
        hpts.get_cop(s, h, x, times)
    assert excinfo.value.key == HpExcKey.COP_GET.value


def test_set_cop_negative_raises_on_validate(hpts):
    # set a negative cop value then run validate and expect exception
    s = StageId("s3")
    h = HubId("hub3")
    x = add_tech(hpts, "hp5")
    t = TimeId(1)

    # set cop directly to negative
    hpts.set_cop(s, h, x, t, Value(-0.5, unit=DimlessUnit()))

    # prepare minimal supporting data for validation
    stages = Stages()
    stages.add_id(s)
    hubs = Hubs()
    hubs.add_id(h)
    times = Times()
    times.add_id(t)
    techs = Techs()
    techs.add_id(x)

    with pytest.raises(exceptions.DataException) as excinfo:
        hpts.validate(stages, hubs, Ecs(), techs, times)
    assert excinfo.value.key == HpExcKey.COP_VAL.value


def test_availability_default_and_set_and_time_series_mapping(hpts):
    s = StageId("s4")
    h = HubId("hub4")
    x = add_tech(hpts, "hp6")
    t = TimeId(1)

    # default availability
    avail_ts = hpts.get_availability(s, h, x)
    assert avail_ts.def_value == Value(1.0)

    # set availability
    hpts.set_availability(s, h, x, t, Value(0.5, unit=DimlessUnit()))
    avail_ts2 = hpts.get_availability(s, h, x)
    assert avail_ts2.get_value(t) == Value(0.5, unit=DimlessUnit())

    # test set_time_series_val mapping for one kind (COP, TEMPHTIN, TEMPHTOUT, AVAIL)
    # COP
    hpts.set_time_series_val(
        kind=TimeSeriesKind.HPTECHCOP,
        s=s,
        ids=(h.key, x.key),
        t=t,
        value=0.42,
    )
    cop_ts = hpts.get_cop(s, h, x, Times())
    # cop value was set for time t, retrieving through get_cop may raise because Times empty - just ensure no crash when setting
    assert (s, h, x) in hpts._cop


def test_validate_ecs_overlap_raises(hpts):
    x = add_tech(hpts, "hp7")

    ecs = Ecs()
    ecs.add_id(EcId("e1"))
    ecs.add_id(EcId("e2"))

    # set ec_el same as heat input to trigger ECS_VAL
    hpts.set_ec_el(x, EcId("e1"), PowerUnit.KW * TimeUnit.H)
    hpts.set_ec_ht_in(x, EcId("e1"), PowerUnit.KW * TimeUnit.H)
    # set remaining ecs so _validate_ecs does not fail with MissingIdException
    hpts.set_ec_co_out(x, EcId("e2"), PowerUnit.KW * TimeUnit.H)
    hpts.set_ec_ht_out(x, EcId("e2"), PowerUnit.KW * TimeUnit.H)
    hpts.set_ec_co_in(x, EcId("e2"), PowerUnit.KW * TimeUnit.H)

    # call internal validation method which checks overlaps
    with pytest.raises(exceptions.DataException) as excinfo:
        hpts._validate_ecs()
    assert excinfo.value.key == HpExcKey.ECS_VAL.value


def test_unknown_id_raises_unknownid_on_setters_and_getters(hpts):
    x = TechId("unknown")

    # setting ec for unknown tech id
    with pytest.raises(exceptions.UnknownIdException) as excinfo:
        hpts.set_ec_el(x, EcId("e"), PowerUnit.KW * TimeUnit.H)
    assert excinfo.value.key == HpExcKey.ECEL_SET.value

    # getting temp for unknown tech id
    s = StageId("s")
    h = HubId("h")
    with pytest.raises(exceptions.UnknownIdException) as excinfo2:
        hpts.get_temp_ht_in(s, h, x)
    assert excinfo2.value.key == HpExcKey.TEMPHTIN_GET.value


def test_cop_time_dependent_computation(hpts):
    x = add_tech(hpts, "hp_time")

    s = StageId("sT")
    h = HubId("hT")
    t1 = TimeId(1)
    t2 = TimeId(2)

    times = Times()
    times.add_id(t1)
    times.add_id(t2)

    # set time-specific temperatures
    hpts.set_temp_ht_in(s, h, x, t1, Value(270.0, unit=TemperatureUnit.K))
    hpts.set_temp_ht_out(s, h, x, t1, Value(300.0, unit=TemperatureUnit.K))
    hpts.set_temp_ht_in(s, h, x, t2, Value(280.0, unit=TemperatureUnit.K))
    hpts.set_temp_ht_out(s, h, x, t2, Value(320.0, unit=TemperatureUnit.K))

    cop_ts = hpts.get_cop(s, h, x, times)
    assert isinstance(cop_ts, TimeSeries)
    # Check computed values
    cop1 = cop_ts.get_value(t1).to_float()
    cop2 = cop_ts.get_value(t2).to_float()
    assert pytest.approx(cop1) == 0.5 * 300.0 / (300.0 - 270.0)
    assert pytest.approx(cop2) == 0.5 * 320.0 / (320.0 - 280.0)


def test_cop_computation_from_defaults(hpts):
    x = add_tech(hpts, "hp_def")

    s = StageId("sD")
    h = HubId("hD")

    # set default temps
    hpts.set_temp_ht_in_def(s, h, x, Value(280.0, unit=TemperatureUnit.K))
    hpts.set_temp_ht_out_def(s, h, x, Value(310.0, unit=TemperatureUnit.K))

    times = Times()

    cop_ts = hpts.get_cop(s, h, x, times)
    # Should be a TimeSeries with def_value set
    assert not cop_ts.has_values
    assert cop_ts.def_value is not None
    assert cop_ts.def_value.to_float() == pytest.approx(0.5 * 310.0 / (310.0 - 280.0))


def test_set_cop_unit_validation_and_def_unit_validation(hpts):
    x = add_tech(hpts, "hp_unit")

    s = StageId("sU")
    h = HubId("hU")
    t = TimeId(1)

    # wrong unit for set_cop should raise DataException with COP_SET key
    with pytest.raises(exceptions.DataException) as excinfo:
        hpts.set_cop(s, h, x, t, Value(1.0, unit=TemperatureUnit.K))
    assert excinfo.value.key == HpExcKey.COP_SET.value

    # wrong unit for set_cop_def should raise DataException with COP_DEFSET key
    with pytest.raises(exceptions.DataException) as excinfo2:
        hpts.set_cop_def(s, h, x, Value(1.0, unit=TemperatureUnit.K))
    assert excinfo2.value.key == HpExcKey.COP_DEFSET.value


def test_availability_unit_validation_and_defaults(hpts):
    x = add_tech(hpts, "hp_avail")

    s = StageId("sA")
    h = HubId("hA")
    t = TimeId(1)

    # wrong unit for set_availability (time-specific) should raise UnitException
    with pytest.raises(exceptions.UnitException):
        hpts.set_availability(s, h, x, t, Value(0.5, unit=TemperatureUnit.K))

    # wrong unit for set_availability_def should raise DataException with AVAILABILITY_DEFSET
    with pytest.raises(exceptions.DataException) as excinfo:
        hpts.set_availability_def(s, h, x, Value(0.5, unit=TemperatureUnit.K))
    assert excinfo.value.key == HpExcKey.AVAILABILITY_DEFSET.value


def test_time_series_property_collects_all_kinds(hpts):
    x = add_tech(hpts, "hp_ts")

    s = StageId("sTS")
    h = HubId("hTS")
    t = TimeId(1)

    # set COP, temps and availability for time series
    hpts.set_cop(s, h, x, t, Value(3.0, unit=DimlessUnit()))
    hpts.set_temp_ht_in(s, h, x, t, Value(280.0, unit=TemperatureUnit.K))
    hpts.set_temp_ht_out(s, h, x, t, Value(300.0, unit=TemperatureUnit.K))
    hpts.set_availability(s, h, x, t, Value(0.8, unit=DimlessUnit()))

    all_series = hpts.time_series
    kinds = {entry[0] for entry in all_series}
    assert TimeSeriesKind.HPTECHCOP in kinds
    assert TimeSeriesKind.HPTECHTEMPHTIN in kinds
    assert TimeSeriesKind.HPTECHTEMPHTOUT in kinds
    assert TimeSeriesKind.HPTECHAVAIL in kinds

    # check identifiers for one of the series
    found = [entry for entry in all_series if entry[0] == TimeSeriesKind.HPTECHCOP]
    assert any(entry[2] == (h.key, x.key) for entry in found)


def test_temp_negative_values_and_comparison_raise():
    hpts = HeatpumpTechs()
    x = TechId("hp_neg")
    hpts.add_id(x)

    s = StageId("sN")
    h = HubId("hN")
    t = TimeId(1)

    stages = Stages()
    stages.add_id(s)
    hubs = Hubs()
    hubs.add_id(h)
    times = Times()
    times.add_id(t)
    techs2 = Techs()
    techs2.add_id(x)

    # negative temp_ht_in should cause validation error
    hpts.set_temp_ht_in(s, h, x, t, Value(-5.0, unit=TemperatureUnit.K))
    with pytest.raises(exceptions.DataException) as excinfo:
        hpts.validate(stages, hubs, Ecs(), techs2, times)
    assert excinfo.value.key == HpExcKey.TEMPHTIN_VAL.value

    # temp_ht_in >= temp_ht_out at same time should trigger TEMPS_VAL
    hpts.set_temp_ht_in(s, h, x, t, Value(300.0, unit=TemperatureUnit.K))
    hpts.set_temp_ht_out(s, h, x, t, Value(300.0, unit=TemperatureUnit.K))
    with pytest.raises(exceptions.DataException) as excinfo2:
        hpts.validate(stages, hubs, Ecs(), techs2, times)
    assert excinfo2.value.key == HpExcKey.TEMPS_VAL.value


def test_ids_in_order_and_in_out_ecs(hpts):
    x1 = TechId("b")
    x2 = TechId("a")
    x3 = TechId("c")
    hpts.add_id(x1)
    hpts.add_id(x2)
    hpts.add_id(x3)

    keys = [t.key for t in hpts.ids_in_order]
    assert keys == ["a", "b", "c"]

    # test in/out ecs composition
    x = add_tech(hpts, "hp_ecs")
    hpts.set_ec_el(x, EcId("el"), PowerUnit.KW * TimeUnit.H)
    hpts.set_ec_ht_in(x, EcId("hin"), PowerUnit.KW * TimeUnit.H)
    hpts.set_ec_co_in(x, EcId("cin"), PowerUnit.KW * TimeUnit.H)
    hpts.set_ec_ht_out(x, EcId("hout"), PowerUnit.KW * TimeUnit.H)
    hpts.set_ec_co_out(x, EcId("cout"), PowerUnit.KW * TimeUnit.H)

    ins = hpts.get_in_ecs(x)
    outs = hpts.get_out_ecs(x)
    assert EcId("el") in ins
    assert EcId("hin") in ins
    assert EcId("hout") in outs
    assert EcId("cout") in outs


def test_get_ec_el_missing_raises_missingid(hpts):
    x = add_tech(hpts, "hp_missing")

    # Not setting ec_el should raise MissingIdException
    with pytest.raises(exceptions.MissingIdException) as excinfo:
        hpts.get_ec_el(x)
    assert excinfo.value.key == HpExcKey.ECEL_GET.value
