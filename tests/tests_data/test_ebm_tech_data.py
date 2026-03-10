import pytest
from contextlib import contextmanager

from ehubx.core.common import TimeSeriesKind

from ehubx.data.ebm_tech_data import EbmTechs, ExceptionKey
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.time_data import TimeId, Times
from ehubx.data.unit import DimlessUnit, LengthUnit, TimeUnit, Unit, PowerUnit
from ehubx.data.value import Value
from ehubx.data import exceptions


@contextmanager
def raises_with_key(exc_type, expected_key):
    with pytest.raises(exc_type) as excinfo:
        yield excinfo
    assert excinfo.value.key == expected_key


def make_env():
    e = EbmTechs()
    tech = TechId("t1")
    stage = StageId("s1")
    hub = HubId("h1")
    times = Times()
    for i in range(1, 4):
        times.add_id(TimeId(i))
    stages = Stages()
    hubs = Hubs()
    techs = Techs()
    ecs = Ecs()
    return e, tech, stage, hub, stages, hubs, techs, ecs, times


def test_getters_unknown_id_raise_expected_keys():
    e, tech, stage, hub, *_ = make_env()
    # none of these have the id added -> should raise UnknownIdException with specific key
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.INEFF_GET.value):
        e.get_in_eff(stage, tech)
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.OUTEFF_GET.value):
        e.get_out_eff(stage, tech)
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.STANDBYLOSS_GET.value):
        e.get_standby_loss(stage, tech)
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.STORAGECAP_GET.value):
        e.get_storage_cap(stage, tech)
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.SOCMIN_GET.value):
        e.get_soc_min(stage, tech)
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.SOCMAX_GET.value):
        e.get_soc_max(stage, tech)
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.SOCINIT_GET.value):
        e.get_soc_init(hub, tech)
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.CHARGEMAX_GET.value):
        e.get_charge_max(stage, tech)
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.DISCHARGEMAX_GET.value):
        e.get_discharge_max(stage, tech)
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.DISCHARGECONTROL_GET.value):
        e.get_discharge_control(stage, tech)


def test_setters_unknown_id_raise_set_keys():
    e, tech, stage, hub, *_ = make_env()
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.INEFF_SET.value):
        e.set_in_eff(stage, tech, Value(1.0, DimlessUnit()))
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.OUTEFF_SET.value):
        e.set_out_eff(stage, tech, Value(1.0, DimlessUnit()))
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.STORAGECAP_SET.value):
        e.set_storage_cap(stage, tech, Value(1.0, DimlessUnit()))
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.SOCMIN_SET.value):
        e.set_soc_min(stage, tech, Value(0.1, DimlessUnit()))
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.SOCMAX_SET.value):
        e.set_soc_max(stage, tech, Value(0.9, DimlessUnit()))


def test_duplicate_add_id_raises_duplicate_key():
    e, tech, *_ = make_env()
    e.add_id(tech)
    with raises_with_key(exceptions.DuplicateIdException, ExceptionKey.ID_ADD.value):
        e.add_id(tech)


def test_set_in_eff_unit_mismatch_uses_out_eff_key():
    e, tech, stage, *_ = make_env()
    e.add_id(tech)
    # in_eff expects dimless but implementation uses OUTEFF_SET as key for unit mismatch
    with raises_with_key(exceptions.DataException, ExceptionKey.INEFF_SET.value):
        e.set_in_eff(stage, tech, Value(1.0, LengthUnit.M))


def test_set_availability_wrong_unit_and_negative_time_value_validation():
    e, tech, stage, hub, stages, hubs, techs, ecs, times = make_env()
    e.add_id(tech)
    techs.add_id(tech)
    # wrong unit on set_availability
    with raises_with_key(exceptions.DataException, ExceptionKey.AVAILABILITY_SET.value):
        e.set_availability(stage, hub, tech, TimeId(1), Value(0.5, LengthUnit.M))

    # set availability time value negative and validate
    e.set_availability(stage, hub, tech, TimeId(1), Value(-0.2, DimlessUnit()))
    with raises_with_key(exceptions.DataException, ExceptionKey.AVAILABILITY_VAL.value):
        e.validate(stages, hubs, techs, ecs, times)


def test_demand_nominal_time_values_affect_consumption():
    e, tech, stage, hub, stages, hubs, techs, ecs, times = make_env()
    e.add_id(tech)
    techs.add_id(tech)
    ecs.add_id(EcId("e1"))
    ecs.set_unit(EcId("e1"), PowerUnit.KW * TimeUnit.H)
    e.set_ec(tech, EcId("e1"), PowerUnit.KW * TimeUnit.H)
    # set default and a time value
    e.set_demand_nominal_def(stage, hub, tech, Value(1.0, Unit.get_def_unit(PowerUnit.KW)))
    e.set_demand_nominal(stage, hub, tech, TimeId(1), Value(2.0, Unit.get_def_unit(PowerUnit.KW)))
    # set vehicles and modifier
    e.set_num_vehicles(stage, hub, tech, 3)
    e.set_demand_modifier(stage, hub, tech, Value(1.5, DimlessUnit()))

    cons = e.get_consumption(stage, hub, tech, times)
    # def_value should be num_vehicles * demand_modifier * default (3 * 1.5 * 1 = 4.5)
    assert cons.def_value == Value(4.5, Unit.get_def_unit(PowerUnit.KW))
    # time-specific value at TimeId(1)
    assert cons.get_value(TimeId(1)) == Value(3 * 1.5 * 2.0, Unit.get_def_unit(PowerUnit.KW))


def test_time_series_setter_produces_expected_units_and_listing():
    e, tech, stage, hub, stages, hubs, techs, ecs, times = make_env()
    e.add_id(tech)
    techs.add_id(tech)
    ecs.add_id(EcId("e1"))
    ecs.set_unit(EcId("e1"), PowerUnit.KW * TimeUnit.H)
    e.set_ec(tech, EcId("e1"), PowerUnit.KW * TimeUnit.H)

    t = TimeId(1)
    # set demand nominal via time_series helper
    e.set_time_series_val(TimeSeriesKind.EBMTECHDEMANDNOM, stage, (hub.key, tech.key), t, 2.5)
    ts = e.get_demand_nominal(stage, hub, tech)
    # the set value should be present
    assert ts.get_value(t) == Value(2.5, Unit.get_def_unit(PowerUnit.KW))

    # set availability via helper
    e.set_time_series_val(TimeSeriesKind.EBMTECHAVAIL, stage, (hub.key, tech.key), t, 0.6)
    found = {k for k, _, _, _ in e.time_series}
    assert TimeSeriesKind.EBMTECHDEMANDNOM in found
    assert TimeSeriesKind.EBMTECHAVAIL in found


def test_demand_nominal_default_negative_logs_as_error_on_validate():
    e, tech, stage, hub, stages, hubs, techs, ecs, times = make_env()
    e.add_id(tech)
    techs.add_id(tech)
    ecs.add_id(EcId("e1"))
    ecs.set_unit(EcId("e1"), PowerUnit.KW * TimeUnit.H)
    e.set_ec(tech, EcId("e1"), PowerUnit.KW * TimeUnit.H)

    # set default negative value
    e.set_demand_nominal_def(stage, hub, tech, Value(-1.0, Unit.get_def_unit(PowerUnit.KW)))
    # validation should raise an error for negative default
    with raises_with_key(exceptions.DataException, ExceptionKey.DEMANDNOMINAL_VAL.value):
        e.validate(stages, hubs, techs, ecs, times)


def test_availability_default_and_getter():
    e, tech, stage, hub, stages, hubs, techs, ecs, times = make_env()
    e.add_id(tech)
    # get_availability returns TimeSeries with default def_value
    ts = e.get_availability(stage, hub, tech)
    assert ts.def_value == Value(1, DimlessUnit())


def test_get_ec_missing_raises():
    e, tech, stage, hub, stages, hubs, techs, ecs, times = make_env()
    e.add_id(tech)
    with raises_with_key(exceptions.MissingIdException, ExceptionKey.EC_GET.value):
        e.get_ec(tech)


def test_num_vehicles_default_and_set():
    e, tech, stage, hub, *_ = make_env()
    e.add_id(tech)
    # default
    assert e.get_num_vehicles(stage, hub, tech) == 0
    # set and get
    e.set_num_vehicles(stage, hub, tech, 5.5)
    assert e.get_num_vehicles(stage, hub, tech) == 5.5


def test_standby_loss_default_and_unit_mismatch():
    e, tech, stage, *_ = make_env()
    e.add_id(tech)
    sl = e.get_standby_loss(stage, tech)
    expected_unit = DimlessUnit() / TimeUnit.H
    assert sl.unit.same_type_as(expected_unit)
    # wrong unit
    with raises_with_key(exceptions.DataException, ExceptionKey.STANDBYLOSS_SET.value):
        e.set_standby_loss(stage, tech, Value(1.0, PowerUnit.KW))


def test_soc_min_max_init_unit_mismatch():
    e, tech, stage, hub, *_ = make_env()
    e.add_id(tech)
    with raises_with_key(exceptions.DataException, ExceptionKey.SOCMIN_SET.value):
        e.set_soc_min(stage, tech, Value(0.1, PowerUnit.KW))
    with raises_with_key(exceptions.DataException, ExceptionKey.SOCMAX_SET.value):
        e.set_soc_max(stage, tech, Value(0.9, PowerUnit.KW))
    with raises_with_key(exceptions.DataException, ExceptionKey.SOCINIT_SET.value):
        e.set_soc_init(hub, tech, Value(0.2, PowerUnit.KW))


def test_charge_discharge_and_discharge_control_unit_mismatch():
    e, tech, stage, hub, *_ = make_env()
    e.add_id(tech)
    # set ec to define expected units for charge/discharge
    e.set_ec(tech, EcId("e1"), Unit.from_str("kWh"))
    with raises_with_key(exceptions.DataException, ExceptionKey.CHARGEMAX_SET.value):
        e.set_charge_max(stage, tech, Value(1.0, DimlessUnit()))
    with raises_with_key(exceptions.DataException, ExceptionKey.DISCHARGEMAX_SET.value):
        e.set_discharge_max(stage, tech, Value(1.0, DimlessUnit()))
    with raises_with_key(exceptions.DataException, ExceptionKey.DISCHARGECONTROL_SET.value):
        e.set_discharge_control(stage, tech, Value(0.5, PowerUnit.KW))


def test_set_demand_nominal_creates_timeseries():
    e, tech, stage, hub, stages, hubs, techs, ecs, times = make_env()
    e.add_id(tech)
    ecs.add_id(EcId("e1"))
    ecs.set_unit(EcId("e1"), PowerUnit.KW * TimeUnit.H)
    e.set_ec(tech, EcId("e1"), PowerUnit.KW * TimeUnit.H)
    # set a timeseries value (creates the timeseries and default)
    e.set_demand_nominal(stage, hub, tech, TimeId(1), Value(2.2, Unit.get_def_unit(PowerUnit.KW)))
    ts = e.get_demand_nominal(stage, hub, tech)
    assert ts.get_value(TimeId(1)) == Value(2.2, Unit.get_def_unit(PowerUnit.KW))


def test_ids_property_and_ids_in_order():
    """Test the ids property and ids_in_order sorting."""
    e, *_ = make_env()
    # Initially empty
    assert e.ids == set()
    # Add multiple ids
    t1 = TechId("t3")
    t2 = TechId("t1")
    t3 = TechId("t2")
    e.add_id(t1)
    e.add_id(t2)
    e.add_id(t3)
    # ids is a set
    assert e.ids == {t1, t2, t3}
    # ids_in_order should be sorted by key
    ordered = e.ids_in_order
    assert ordered == [t2, t3, t1]  # t1, t2, t3 alphabetically


def test_set_ec_and_get_ec_valid():
    """Test successful ec setting and retrieval."""
    e, tech, *_ = make_env()
    e.add_id(tech)
    e.set_ec(tech, EcId("e_test"), PowerUnit.KW * TimeUnit.H)
    assert e.get_ec(tech) == EcId("e_test")


def test_storage_cap_unit_mismatch():
    """Test storage_cap unit validation matches ec unit."""
    e, tech, stage, *_ = make_env()
    e.add_id(tech)
    # Set ec with a specific unit
    e.set_ec(tech, EcId("e1"), PowerUnit.KW * TimeUnit.H)
    # Try to set storage cap with wrong unit
    with raises_with_key(exceptions.DataException, ExceptionKey.STORAGECAP_SET.value):
        e.set_storage_cap(stage, tech, Value(100.0, LengthUnit.M))


def test_demand_modifier_unit_mismatch():
    """Test demand_modifier expects dimless unit."""
    e, tech, stage, hub, *_ = make_env()
    e.add_id(tech)
    with raises_with_key(exceptions.DataException, ExceptionKey.DEMANDMODIFIER_SET.value):
        e.set_demand_modifier(stage, hub, tech, Value(1.5, PowerUnit.KW))


def test_in_eff_default_value():
    """Test in_eff getter returns default when not set."""
    e, tech, stage, *_ = make_env()
    e.add_id(tech)
    in_eff = e.get_in_eff(stage, tech)
    assert in_eff.to_float(DimlessUnit()) == pytest.approx(1.0)


def test_out_eff_default_value():
    """Test out_eff getter returns default when not set."""
    e, tech, stage, *_ = make_env()
    e.add_id(tech)
    out_eff = e.get_out_eff(stage, tech)
    assert out_eff.to_float(DimlessUnit()) == pytest.approx(1.0)


def test_charge_max_default_unit_depends_on_ec():
    """Test charge_max default unit is ec_unit/h."""
    e, tech, stage, *_ = make_env()
    e.add_id(tech)
    # set ec with specific unit first
    e.set_ec(tech, EcId("e1"), PowerUnit.KW * TimeUnit.H)
    # default charge_max should use that ec unit in /h
    charge_max = e.get_charge_max(stage, tech)
    expected_unit = (PowerUnit.KW * TimeUnit.H) / TimeUnit.H
    assert charge_max.unit.same_type_as(expected_unit)


def test_discharge_max_default_unit_depends_on_ec():
    """Test discharge_max default unit is ec_unit/h."""
    e, tech, stage, *_ = make_env()
    e.add_id(tech)
    e.set_ec(tech, EcId("e1"), PowerUnit.KW * TimeUnit.H)
    discharge_max = e.get_discharge_max(stage, tech)
    expected_unit = (PowerUnit.KW * TimeUnit.H) / TimeUnit.H
    assert discharge_max.unit.same_type_as(expected_unit)


def test_discharge_control_default_value():
    """Test discharge_control getter returns default when not set."""
    e, tech, stage, *_ = make_env()
    e.add_id(tech)
    dc = e.get_discharge_control(stage, tech)
    assert dc.to_float(DimlessUnit()) == pytest.approx(1.0)


def test_demand_modifier_default_value():
    """Test demand_modifier getter returns default when not set."""
    e, tech, stage, hub, *_ = make_env()
    e.add_id(tech)
    dm = e.get_demand_modifier(stage, hub, tech)
    assert dm.to_float(DimlessUnit()) == pytest.approx(1.0)


def test_soc_min_default_value():
    """Test soc_min getter returns default when not set."""
    e, tech, stage, *_ = make_env()
    e.add_id(tech)
    soc_min = e.get_soc_min(stage, tech)
    assert soc_min.to_float(DimlessUnit()) == pytest.approx(0.0)


def test_soc_max_default_value():
    """Test soc_max getter returns default when not set."""
    e, tech, stage, *_ = make_env()
    e.add_id(tech)
    soc_max = e.get_soc_max(stage, tech)
    assert soc_max.to_float(DimlessUnit()) == pytest.approx(1.0)


def test_soc_init_default_is_infinity():
    """Test soc_init getter returns infinity when not set."""
    e, tech, hub, *_ = make_env()
    e.add_id(tech)
    soc_init = e.get_soc_init(hub, tech)
    assert soc_init.to_float(DimlessUnit()) == float("inf")


def test_set_availability_def_unit_mismatch():
    """Test set_availability_def with wrong unit raises error."""
    e, tech, stage, hub, *_ = make_env()
    e.add_id(tech)
    with raises_with_key(exceptions.DataException, ExceptionKey.AVAILABILITY_DEFSET.value):
        e.set_availability_def(stage, hub, tech, Value(0.8, PowerUnit.KW))


def test_set_demand_nominal_def_unit_mismatch():
    """Test set_demand_nominal_def with wrong unit raises error."""
    e, tech, stage, hub, *_ = make_env()
    e.add_id(tech)
    e.set_ec(tech, EcId("e1"), PowerUnit.KW * TimeUnit.H)
    # expect ec_unit / TimeUnit.H
    with raises_with_key(exceptions.DataException, ExceptionKey.DEMANDNOMINAL_DEFSET.value):
        e.set_demand_nominal_def(stage, hub, tech, Value(1.0, DimlessUnit()))


def test_demand_nominal_missing_returns_empty_timeseries():
    """Test get_demand_nominal returns empty TimeSeries when not set."""
    e, tech, stage, hub, *_ = make_env()
    e.add_id(tech)
    e.set_ec(tech, EcId("e1"), PowerUnit.KW * TimeUnit.H)
    ts = e.get_demand_nominal(stage, hub, tech)
    # Should be a TimeSeries object (default created)
    assert ts is not None
    assert ts.def_value == Value(0, Unit.get_def_unit(PowerUnit.KW))
