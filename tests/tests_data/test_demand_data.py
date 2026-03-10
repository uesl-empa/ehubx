import pytest
from contextlib import contextmanager

from ehubx.data.demand_data import Demands, ExceptionKey
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.time_data import TimeId, Times
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.unit import DimlessUnit, MassUnit, TimeUnit, Unit
from ehubx.data.value import Value
from ehubx.data.time_series import TimeSeries
from ehubx.core.common import TimeSeriesKind
from ehubx.data import exceptions


@contextmanager
def raises_with_key(exc_type, expected_key):
    with pytest.raises(exc_type) as excinfo:
        yield excinfo
    assert excinfo.value.key == expected_key


def make_basic_env():
    d = Demands()
    s = StageId("s1")
    h = HubId("h1")
    e = EcId("e1")
    t = TimeId(1)
    stages = Stages()
    stages.add_id(s)
    hubs = Hubs()
    hubs.add_id(h)
    times = Times()
    times.add_id(t)
    ecs = Ecs()
    return d, s, h, e, t, stages, hubs, ecs, times


def test_add_profile_tuple_and_default_unit_and_duplicate():
    d, s, h, e, t, stages, hubs, ecs, times = make_basic_env()
    # add profile tuple
    d.add_profile_tuple(s, h, e, DimlessUnit())
    ts = d.get_demand_profile(s, h, e)
    assert isinstance(ts, TimeSeries)
    # default def_value unit is ec_unit / TimeUnit.H
    assert ts.def_value.unit.same_type_as(DimlessUnit() / TimeUnit.H)

    # duplicate addition raises
    with raises_with_key(exceptions.DataException, ExceptionKey.PROFILETUPLES_ADD.value):
        d.add_profile_tuple(s, h, e, DimlessUnit())


def test_add_profile_tuple_conflict_with_sum_tuple_raises():
    d, s, h, e, t, stages, hubs, ecs, times = make_basic_env()
    # first add as sum tuple manually
    d.set_demand_sum(s, h, e, Value(1.0, unit=DimlessUnit()))
    # adding profile tuple where sum_tuple exists should raise
    with raises_with_key(exceptions.DataException, ExceptionKey.PROFILETUPLES_ADD.value):
        d.add_profile_tuple(s, h, e, DimlessUnit())


def test_get_and_set_profile_missing_tuple_raises_keys():
    d, s, h, e, t, stages, hubs, ecs, times = make_basic_env()
    with raises_with_key(exceptions.DataException, ExceptionKey.DEMANDPROFILE_GET.value):
        d.get_demand_profile(s, h, e)
    with raises_with_key(exceptions.DataException, ExceptionKey.DEMANDPROFILE_SET.value):
        d.set_demand_in_profile(s, h, e, t, Value(1.0, unit=DimlessUnit()))
    with raises_with_key(exceptions.DataException, ExceptionKey.DEMANDPROFILE_DEFSET.value):
        d.set_demand_profile_def(s, h, e, Value(0.0, unit=DimlessUnit()))


def test_set_demand_sum_conflict_with_profile_raises_and_get_missing():
    d, s, h, e, t, stages, hubs, ecs, times = make_basic_env()
    # add profile tuple
    d.add_profile_tuple(s, h, e, DimlessUnit())
    with raises_with_key(exceptions.DataException, ExceptionKey.SUMTUPLES_ADD.value):
        d.set_demand_sum(s, h, e, Value(1.0, unit=DimlessUnit()))

    # get demand_sum missing raises
    with raises_with_key(exceptions.DataException, ExceptionKey.DEMANDSUM_GET.value):
        d.get_demand_sum(s, h, e)


def test_validate_demand_profile_unit_mismatch_raises_key():
    d, s, h, e, t, stages, hubs, ecs, times = make_basic_env()
    # add profile tuple with DimlessUnit
    d.add_profile_tuple(s, h, e, DimlessUnit())
    # but ecs reports mass unit for e -> unit mismatch
    ecs.add_id(e)
    ecs.set_unit(e, MassUnit.KG)
    with raises_with_key(exceptions.DataException, ExceptionKey.DEMANDPROFILE_VAL.value):
        d.validate(stages, hubs, ecs, times)


def test_validate_demand_sum_unit_mismatch_raises_key():
    d, s, h, e, t, stages, hubs, ecs, times = make_basic_env()
    ecs.add_id(e)
    # set demand_sum unit that does not match ecs.get_unit(e)
    ecs.set_unit(e, MassUnit.KG)
    d.set_demand_sum(s, h, e, Value(1.0, unit=DimlessUnit()))
    with raises_with_key(exceptions.DataException, ExceptionKey.DEMANDSUM_VAL.value):
        d.validate(stages, hubs, ecs, times)


def test_time_series_listing_and_set_time_series_val():
    d, s, h, e, t, stages, hubs, ecs, times = make_basic_env()
    # setup profile tuple with ec unit and set time value
    d.add_profile_tuple(s, h, e, DimlessUnit())
    d.set_demand_in_profile(s, h, e, t, Value(0.5, unit=Unit.get_def_unit(DimlessUnit() / TimeUnit.H)))
    found = {k for k, _, _, _ in d.time_series}
    assert TimeSeriesKind.DEMAND in found
