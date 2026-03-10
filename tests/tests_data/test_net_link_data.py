import pytest
from contextlib import contextmanager

from ehubx.data.net_link_data import (
    NetLinkId,
    NetworkLinks,
    NetLinkDirection,
    ExceptionKey,
)
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.time_data import TimeId, Times
from ehubx.data.unit import PowerUnit, TimeUnit, LengthUnit, DimlessUnit, Unit
from ehubx.data.value import Value
from ehubx.data import exceptions


@contextmanager
def raises_with_key(exc_type, expected_key):
    with pytest.raises(exc_type) as excinfo:
        yield excinfo
    assert excinfo.value.key == expected_key


def test_add_duplicate_id_raises_duplicate_key():
    nl = NetworkLinks()
    li = NetLinkId("l1")
    nl.add_id(li)
    with raises_with_key(exceptions.DuplicateIdException, ExceptionKey.ID_ADD.value):
        nl.add_id(li)


def test_ids_in_order_returns_sorted_keys():
    nl = NetworkLinks()
    nl.add_id(NetLinkId("b"))
    nl.add_id(NetLinkId("a"))
    nl.add_id(NetLinkId("c"))
    ordered = nl.ids_in_order
    assert [x.key for x in ordered] == ["a", "b", "c"]


def test_get_ecs_and_add_ec_unknown_id_raises_expected_key():
    nl = NetworkLinks()
    li = NetLinkId("x")
    e = EcId("e")
    # get_ecs on unknown link -> UnknownIdException with ECS_GET
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.ECS_GET.value):
        nl.get_ecs(li)
    # add_ec on unknown link -> UnknownIdException with ECS_ADD
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.ECS_ADD.value):
        nl.add_ec(li, e, Unit.get_def_unit(PowerUnit.KW * TimeUnit.H))


def test_add_ec_sets_default_capacity_and_sum_units_and_cap_getters():
    nl = NetworkLinks()
    li = NetLinkId("l1")
    nl.add_id(li)
    e = EcId("e1")
    ec_unit = Unit.get_def_unit(PowerUnit.KW * TimeUnit.H)
    nl.add_ec(li, e, ec_unit)

    s = StageId("s1")
    cap_min = nl.get_cap_min(s, li, e)
    cap_max = nl.get_cap_max(s, li, e)
    # numeric defaults: cap_min == 0 (with expected unit), cap_max is infinite
    expected_unit = ec_unit / TimeUnit.H
    assert cap_min == Value(0.0, expected_unit)
    assert cap_max.is_finite is False
    # units: cap_max unit matches expected
    assert cap_max.unit.same_type_as(expected_unit)


def test_length_get_set_and_validation_errors():
    nl = NetworkLinks()
    li = NetLinkId("l1")
    # unknown id -> UnknownIdException
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.LENGTH_GET.value):
        nl.get_length(li)

    nl.add_id(li)
    # missing length -> MissingIdException with LENGTH_GET
    with raises_with_key(exceptions.MissingIdException, ExceptionKey.LENGTH_GET.value):
        nl.get_length(li)

    # wrong unit on set -> DataException with LENGTH_SET
    with raises_with_key(exceptions.DataException, ExceptionKey.LENGTH_SET.value):
        nl.set_length(li, Value(1.0, Unit.get_def_unit(PowerUnit.KW)))

    # correct set and negative validation
    nl.set_length(li, Value(-1.0, LengthUnit.M))
    # run validate and expect LENGTH_VAL key
    with raises_with_key(exceptions.DataException, ExceptionKey.LENGTH_VAL.value):
        nl.validate(Stages(), Hubs(), Ecs(), Times())


def test_hub_start_end_and_start_end_validation():
    nl = NetworkLinks()
    li = NetLinkId("l1")
    nl.add_id(li)
    h = HubId("h1")

    # not set -> MissingIdException
    with raises_with_key(exceptions.MissingIdException, ExceptionKey.HUBSTART_GET.value):
        nl.get_hub_start(li)

    nl.set_hub_start(li, h)
    # validate with missing hub in Hubs -> HUBSTART_VAL
    with raises_with_key(exceptions.DataException, ExceptionKey.HUBSTART_VAL.value):
        nl.validate(Stages(), Hubs(), Ecs(), Times())

    # set both start and end to same hub and ensure HUBSTARTEND_SAME raised when hub exists
    hubs = Hubs()
    hubs.add_id(h)
    nl.set_hub_end(li, h)
    with raises_with_key(exceptions.DataException, ExceptionKey.HUBSTARTEND_SAME.value):
        nl.validate(Stages(), hubs, Ecs(), Times())


def test_validate_raises_for_unknown_ec_in_ecs():
    nl = NetworkLinks()
    li = NetLinkId("l1")
    nl.add_id(li)
    e = EcId("e1")
    nl.add_ec(li, e, Unit.get_def_unit(PowerUnit.KW * TimeUnit.H))

    # Ecs object without e -> ECS_VAL
    with raises_with_key(exceptions.DataException, ExceptionKey.ECS_VAL.value):
        nl.validate(Stages(), Hubs(), Ecs(), Times())


def test_availability_unit_and_time_validation():
    nl = NetworkLinks()
    li = NetLinkId("l1")
    nl.add_id(li)
    e = EcId("e1")
    nl.add_ec(li, e, Unit.get_def_unit(PowerUnit.KW * TimeUnit.H))
    s = StageId("s1")
    t = TimeId(1)

    # wrong unit for availability -> AVAILABILITY_SET
    with raises_with_key(exceptions.DataException, ExceptionKey.AVAILABILITY_SET.value):
        nl.set_availability(s, li, e, t, Value(0.5, Unit.get_def_unit(PowerUnit.KW)))

    # default availability_def wrong unit -> AVAILABILITY_DEFSET
    with raises_with_key(exceptions.DataException, ExceptionKey.AVAILABILITY_DEFSET.value):
        nl.set_availability_def(s, li, e, Value(0.1, Unit.get_def_unit(PowerUnit.KW)))

    # set availability time value negative and validate -> AVAILABILITY_VAL
    nl.set_availability(s, li, e, t, Value(-0.1, DimlessUnit()))
    times = Times()
    times.add_id(t)
    # add stage and ec so availability validation is reached
    stages = Stages()
    stages.add_id(s)
    ecs = Ecs()
    ecs.add_id(e)
    with raises_with_key(exceptions.DataException, ExceptionKey.AVAILABILITY_VAL.value):
        nl.validate(stages, Hubs(), ecs, times)


def test_sum_max_negative_and_sum_minmax():
    nl = NetworkLinks()
    li = NetLinkId("l1")
    nl.add_id(li)
    e = EcId("e1")
    ec_unit = Unit.get_def_unit(PowerUnit.KW * TimeUnit.H)
    nl.add_ec(li, e, ec_unit)

    s = StageId("s1")
    stages = Stages()
    stages.add_id(s)
    ecs = Ecs()
    ecs.add_id(e)

    # negative sum_max -> SUMMAX_VAL
    with raises_with_key(exceptions.DataException, ExceptionKey.SUMMAX_VAL.value):
        nl.set_sum_max(s, li, e, NetLinkDirection.FORWARD, Value(-1.0, ec_unit))
        nl.validate(stages, Hubs(), ecs, Times())

    # sum_min > sum_max -> SUMMINMAX_VAL
    nl.set_sum_max(s, li, e, NetLinkDirection.FORWARD, Value(2.0, ec_unit))
    nl.set_sum_min(s, li, e, NetLinkDirection.FORWARD, Value(3.0, ec_unit))
    with raises_with_key(exceptions.DataException, ExceptionKey.SUMMINMAX_VAL.value):
        nl.validate(stages, Hubs(), ecs, Times())
