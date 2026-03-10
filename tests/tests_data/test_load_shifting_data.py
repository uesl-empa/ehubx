import pytest

from ehubx.data.load_shifting_data import (
    LoadShifting,
    LoadShiftId,
    ExceptionKey as LsExceptionKey,
)
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.demand_data import Demands
from ehubx.data.time_data import TimeId, Times
from ehubx.data.unit import DimlessUnit, TimeUnit, CurrencyUnit
from ehubx.data.value import Value
from ehubx.data import exceptions
from ehubx.core.common import TimeSeriesKind


def test_add_id_and_duplicate_key():
    ls = LoadShifting()
    lsid = LoadShiftId("ls1")
    ec = EcId("e1")
    # first add works
    ls.add_id(lsid, ec, DimlessUnit())
    assert lsid in ls.ids

    # duplicate add raises DuplicateIdException with correct key
    with pytest.raises(exceptions.DuplicateIdException) as excinfo:
        ls.add_id(lsid, ec, DimlessUnit())
    assert excinfo.value.key == LsExceptionKey.ID_ADD.value


def test_get_ec_unknown_raises_unknownid_key():
    ls = LoadShifting()
    lsid = LoadShiftId("ls_unknown")
    with pytest.raises(exceptions.UnknownIdException) as excinfo:
        ls.get_ec(lsid)
    assert excinfo.value.key == LsExceptionKey.EC_GET.value


def test_add_stage_without_id_raises_unknownid_key():
    ls = LoadShifting()
    lsid = LoadShiftId("ls1")
    sid = StageId("s1")
    with pytest.raises(exceptions.UnknownIdException) as excinfo:
        ls.add_stage(lsid, sid)
    assert excinfo.value.key == LsExceptionKey.STAGE_ADD.value


def test_interval_length_set_wrong_unit_and_missing_key():
    ls = LoadShifting()
    lsid = LoadShiftId("ls1")
    ec = EcId("e1")
    ls.add_id(lsid, ec, DimlessUnit())

    # wrong unit -> DataException with INTERVALLENGTH_SET
    with pytest.raises(exceptions.DataException) as excinfo:
        ls.set_interval_length(lsid, Value(1, DimlessUnit()))
    assert excinfo.value.key == LsExceptionKey.INTERVALLENGTH_SET.value

    # missing interval length -> MissingIdException with INTERVALLENGTH_GET
    with pytest.raises(exceptions.MissingIdException) as excinfo2:
        ls.get_interval_length(lsid)
    assert excinfo2.value.key == LsExceptionKey.INTERVALLENGTH_GET.value


def test_validate_stage_hub_ec_tuple_keys():
    ls = LoadShifting()
    lsid = LoadShiftId("ls1")
    s = StageId("s1")
    h = HubId("h1")
    e = EcId("e1")

    ls.add_id(lsid, e, DimlessUnit())
    ls.add_stage(lsid, s)
    ls.add_hub(lsid, h)

    stages = Stages()
    hubs = Hubs()
    ecs = Ecs()
    demands = Demands()
    times = Times()

    # Stage unknown -> STAGE_VAL
    with pytest.raises(exceptions.DataException) as exc_stage:
        ls.validate(stages, hubs, ecs, demands, times)
    assert exc_stage.value.key == LsExceptionKey.STAGE_VAL.value

    # make stage known, hub still unknown -> HUB_VAL
    stages.add_id(s)
    with pytest.raises(exceptions.DataException) as exc_hub:
        ls.validate(stages, hubs, ecs, demands, times)
    assert exc_hub.value.key == LsExceptionKey.HUB_VAL.value

    # make hub known, ec still unknown -> EC_VAL
    hubs.add_id(h)
    with pytest.raises(exceptions.DataException) as exc_ec:
        ls.validate(stages, hubs, ecs, demands, times)
    assert exc_ec.value.key == LsExceptionKey.EC_VAL.value

    # make ec known -> now tuples missing -> TUPLES_GET
    ecs.add_id(e)
    with pytest.raises(exceptions.DataException) as exc_tuple:
        ls.validate(stages, hubs, ecs, demands, times)
    assert exc_tuple.value.key == LsExceptionKey.TUPLES_GET.value


def test_time_series_contains_energy_cost_above_entry():
    ls = LoadShifting()
    lsid = LoadShiftId("ls1")
    s = StageId("s1")
    h = HubId("h1")
    e = EcId("e1")

    # prepare supporting data
    stages = Stages()
    hubs = Hubs()
    ecs = Ecs()
    demands = Demands()
    times = Times()

    stages.add_id(s)
    hubs.add_id(h)
    ecs.add_id(e)

    # add demand profile tuple so it's coherent
    demands.add_profile_tuple(s, h, e, DimlessUnit())

    ls.add_id(lsid, e, DimlessUnit())
    ls.add_stage(lsid, s)
    ls.add_hub(lsid, h)

    # set a time id and assign energy_cost_above at that time
    t = TimeId(1)
    times.add_id(t)

    # energy cost unit must be CurrencyUnit.CHF / ec unit
    cost_unit = CurrencyUnit.CHF / DimlessUnit()
    val = Value(5.0, cost_unit)
    ls.set_energy_cost_above(lsid, t, val)

    series_list = ls.time_series
    # there should be at least one entry for the energy_cost_above
    found = [entry for entry in series_list if entry[0] == TimeSeriesKind.LOADSHIFTENERGYCOSTABOVE]
    assert len(found) == 1
    kind, stage, keys, series = found[0]
    assert stage == s
    assert keys == (h.key, e.key, lsid.key)
    # and the series should contain the value at t
    assert series.get_value(t) == val


def test_getters_unknown_id_raise_correct_keys():
    ls = LoadShifting()
    with pytest.raises(exceptions.UnknownIdException) as exc1:
        ls.get_stage_hub_tuples(LoadShiftId("x"))
    assert exc1.value.key == LsExceptionKey.TUPLES_GET.value

    with pytest.raises(exceptions.UnknownIdException) as exc2:
        ls.get_max_above_abs(LoadShiftId("x"))
    assert exc2.value.key == LsExceptionKey.MAXABOVEABS_GET.value


def test_cap_min_max_init_validations():
    ls = LoadShifting()
    lsid = LoadShiftId("ls1")
    e = EcId("e1")
    ls.add_id(lsid, e, DimlessUnit())

    ecs = Ecs()
    ecs.add_id(e)
    stages = Stages()
    hubs = Hubs()
    demands = Demands()
    times = Times()

    # cap_max negative -> CAPMAX_VAL
    ls.set_cap_max(lsid, Value(-1.0, DimlessUnit()))
    with pytest.raises(exceptions.DataException) as exc_max:
        ls.validate(stages, hubs, ecs, demands, times)
    assert exc_max.value.key == LsExceptionKey.CAPMAX_VAL.value

    # cap_min > cap_max -> CAPMINMAXINIT_VAL
    ls.set_cap_max(lsid, Value(5.0, DimlessUnit()))
    ls.set_cap_min(lsid, Value(10.0, DimlessUnit()))
    with pytest.raises(exceptions.DataException) as exc_minmax:
        ls._validate_cap_minmaxinit()
    assert exc_minmax.value.key == LsExceptionKey.CAPMINMAXINIT_VAL.value

    # cap_init < cap_min -> CAPMINMAXINIT_VAL
    ls.set_cap_min(lsid, Value(10.0, DimlessUnit()))
    ls.set_cap_max(lsid, Value(20.0, DimlessUnit()))
    ls.set_cap_init(lsid, Value(5.0, DimlessUnit()))
    with pytest.raises(exceptions.DataException) as exc_init_min:
        ls._validate_cap_minmaxinit()
    assert exc_init_min.value.key == LsExceptionKey.CAPMINMAXINIT_VAL.value

    # cap_init > cap_max -> CAPMINMAXINIT_VAL
    ls.set_cap_min(lsid, Value(0.0, DimlessUnit()))
    ls.set_cap_max(lsid, Value(10.0, DimlessUnit()))
    ls.set_cap_init(lsid, Value(20.0, DimlessUnit()))
    with pytest.raises(exceptions.DataException) as exc_init_max:
        ls._validate_cap_minmaxinit()
    assert exc_init_max.value.key == LsExceptionKey.CAPMINMAXINIT_VAL.value


def test_max_above_rel_unit_mismatch_uses_maxbelowrel_key():
    ls = LoadShifting()
    lsid = LoadShiftId("ls1")
    e = EcId("e1")
    ls.add_id(lsid, e, DimlessUnit())

    t = TimeId(1)
    times = Times()
    times.add_id(t)

    # set with wrong unit -> DataException with (surprising) MAXBELOWREL_SET key
    with pytest.raises(exceptions.DataException) as exc:
        ls.set_max_above_rel(lsid, t, Value(1.0, TimeUnit.H))
    assert exc.value.key == LsExceptionKey.MAXABOVEREL_SET.value

    # default with wrong unit
    with pytest.raises(exceptions.DataException) as exc2:
        ls.set_max_above_rel_def(lsid, Value(1.0, TimeUnit.H))
    assert exc2.value.key == LsExceptionKey.MAXABOVEREL_DEFSET.value


def test_interval_length_zero_and_too_long_behaviour():
    ls = LoadShifting()
    lsid = LoadShiftId("ls1")
    e = EcId("e1")
    ls.add_id(lsid, e, DimlessUnit())

    stages = Stages()
    hubs = Hubs()
    ecs = Ecs()
    ecs.add_id(e)
    demands = Demands()
    times = Times()

    # Set interval_length zero -> INTERVALLENGTH_VAL on validate
    ls.set_interval_length(lsid, Value(0.0, TimeUnit.H))
    with pytest.raises(exceptions.DataException) as exc_zero:
        ls.validate(stages, hubs, ecs, demands, times)
    assert exc_zero.value.key == LsExceptionKey.INTERVALLENGTH_VAL.value

    # If interval_length is larger than horizon, only a warning is logged and no exception
    ls.set_interval_length(lsid, Value(3.0, TimeUnit.H))
    # make a small horizon
    times.add_horizon_id(TimeId(1))
    # should not raise
    ls.validate(stages, hubs, ecs, demands, times)


def test_energy_cost_above_unit_mismatch_raises_unit_exception():
    ls = LoadShifting()
    lsid = LoadShiftId("ls1")
    e = EcId("e1")
    ls.add_id(lsid, e, DimlessUnit())

    ecs = Ecs()
    ecs.add_id(e)
    times = Times()
    t = TimeId(1)
    times.add_id(t)

    # set energy cost with wrong unit (TimeUnit instead of Currency/EC)
    with pytest.raises(exceptions.UnitException):
        ls.set_energy_cost_above(lsid, t, Value(1.0, TimeUnit.H))
