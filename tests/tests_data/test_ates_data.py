import pytest

from ehubx.data.ates_data import AtesData, AtesScheduleId, ExceptionKey
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.time_data import TimeId, Times
from ehubx.data.unit import (
    LengthUnit,
    TimeUnit,
    MassUnit,
    PowerUnit,
    TemperatureUnit,
    Unit,
)
from ehubx.data.value import Value
from ehubx.data.exceptions import (
    DataException,
    MissingIdException,
    MissingIdsException,
    DuplicateIdException,
)
from ehubx.core import common
from contextlib import contextmanager

@contextmanager
def raises_with_key(exc_type, expected_key):
    with pytest.raises(exc_type) as excinfo:
        yield excinfo
    assert excinfo.value.key == expected_key


def make_basic_env():
    hubs = Hubs()
    h = HubId("h1")
    hubs.add_id(h)

    stages = Stages()
    s = StageId("s1")
    stages.add_id(s)

    times = Times()
    for i in range(1, 5):
        t = TimeId(i)
        times.add_id(t)

    return h, s, hubs, stages, times


def test_darcy_and_pore_velocity_and_unit_checks():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()

    # Wrong unit for darcy velocity
    with pytest.raises(DataException) as excinfo:
        a.set_darcy_velocity(h, Value(1.0, PowerUnit.KW))
    assert excinfo.value.key == ExceptionKey.DARCYVELOCITY_SET.value

    # Correct unit
    a.set_darcy_velocity(h, Value(2.0, LengthUnit.M / TimeUnit.D))
    assert a.get_darcy_velocity(h).to_float(LengthUnit.M / TimeUnit.D) == 2.0

    # Porosity must be dimless
    # Pore velocity needs to be darcy velocity divided by porosity
    a.set_porosity_aquifer(h, Value(0.5))
    pore = a.get_pore_velocity(h)
    assert pore.to_float(LengthUnit.M / TimeUnit.D) == pytest.approx(4.0)


def test_density_and_volumetric_heat_capacity():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()

    density_unit = MassUnit.KG / (LengthUnit.M ** 3)
    a.set_density_rock(h, Value(1000.0, density_unit))

    spec_unit = (PowerUnit.KW * TimeUnit.H) / (MassUnit.KG * TemperatureUnit.K)
    a.set_specific_heat_capacity_rock(h, Value(4.0, spec_unit))

    vol = a.get_volumetric_heat_capacity_rock(h)
    # Expected unit: kW*h/(m^3*K) and numeric 1000 * 4 = 4000
    expected_unit = Unit.from_str("kW*h/(m^3*K)")
    assert vol.unit.same_type_as(expected_unit)
    assert vol.to_float(expected_unit) == pytest.approx(4000.0)


def test_thickness_and_hydraulic_transmissivity():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()

    a.set_thickness_aquifer(h, Value(10.0, LengthUnit.M))
    assert a.get_thickness_aquifer(h).to_float(LengthUnit.M) == 10.0

    a.set_hydraulic_conductivity_aquifer(h, Value(2.0, LengthUnit.M / TimeUnit.D))
    transmissivity = a.get_hydraulic_transmissivity_aquifer(h)
    expected_unit = Unit.from_str("m^2/d")
    assert transmissivity.unit.same_type_as(expected_unit)
    assert transmissivity.to_float(expected_unit) == pytest.approx(20.0)


def test_available_area_default_and_set_unit_check():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()

    # default should be inf area
    area = a.get_available_area(s, h)
    assert not area.is_finite
    assert area.unit.same_type_as(LengthUnit.M ** 2)

    # wrong unit
    with pytest.raises(DataException) as excinfo:
        a.set_available_area(s, h, Value(10.0, PowerUnit.KW))
    assert excinfo.value.key == ExceptionKey.AVAILABLEAREA_SET.value

    # correct unit
    a.set_available_area(s, h, Value(100.0, LengthUnit.M ** 2))
    assert a.get_available_area(s, h).to_float(LengthUnit.M ** 2) == 100.0


def test_schedule_ids_add_and_duplicate_and_phase_id_checks():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()

    i = AtesScheduleId("sch1")
    a.add_schedule_id(h, i)

    with pytest.raises(DuplicateIdException) as excinfo:
        a.add_schedule_id(h, i)
    assert excinfo.value.key == ExceptionKey.SCHEDULEID_ADD.value

    # Setting phase start without schedule id should raise
    j = AtesScheduleId("sch2")
    with pytest.raises(DataException) as excinfo:
        a.set_phase_w2c_start(h, j, TimeId(1))
    assert excinfo.value.key == ExceptionKey.PHASEW2CSTART_SET.value

    # Now set properly
    a.add_schedule_id(h, j)
    a.set_phase_w2c_start(h, j, TimeId(1))
    a.set_phase_w2c_end(h, j, TimeId(2))
    assert a.get_phase_w2c_start(h, j) == TimeId(1)
    assert a.get_phase_w2c_end(h, j) == TimeId(2)


def test_phase_checks_and_durations():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()

    # Setup schedule and phases
    i = AtesScheduleId("sch1")
    a.add_schedule_id(h, i)
    a.set_phase_w2c_start(h, i, TimeId(1))
    a.set_phase_w2c_end(h, i, TimeId(2))
    a.set_phase_c2w_start(h, i, TimeId(3))
    a.set_phase_c2w_end(h, i, TimeId(4))

    # is_in checks
    assert a.is_in_w2c_phase(h, i, TimeId(1))
    assert not a.is_in_w2c_phase(h, i, TimeId(3))
    assert a.is_in_c2w_phase(h, i, TimeId(3))

    # wrap-around case
    a.set_phase_w2c_start(h, i, TimeId(3))
    a.set_phase_w2c_end(h, i, TimeId(1))

    assert a.is_in_w2c_phase(h, i, TimeId(4))
    assert a.is_in_w2c_phase(h, i, TimeId(1))
    assert not a.is_in_w2c_phase(h, i, TimeId(2))

    # durations
    a.set_phase_w2c_start(h, i, TimeId(1))
    a.set_phase_w2c_end(h, i, TimeId(2))
    dur = a.get_phase_duration_w2c(h, i, times)
    assert dur.to_float(TimeUnit.H) == 2

    # wrap durations
    a.set_phase_w2c_start(h, i, TimeId(3))
    a.set_phase_w2c_end(h, i, TimeId(1))
    dur2 = a.get_phase_duration_w2c(h, i, times)
    # (1 - 1 + 1) + (4 - 3 + 1) = 3
    assert dur2.to_float(TimeUnit.H) == 3

def test_validation_checks():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()
    i = AtesScheduleId("sch1")

    # Validation errors
    # Unknown hub in darcy_velocity
    a.set_darcy_velocity(HubId("unknown"), Value(1.0, LengthUnit.M / TimeUnit.D))
    with pytest.raises(DataException) as excinfo:
        a.validate(stages, Hubs(), times)
    assert excinfo.value.key == ExceptionKey.DARCYVELOCITY_VAL.value

    # Negative darcy velocity
    h2 = HubId("h2")
    hubs.add_id(h2)
    a.set_darcy_velocity(h2, Value(-1.0, LengthUnit.M / TimeUnit.D))
    with pytest.raises(DataException) as excinfo:
        a.validate(stages, hubs, times)
    assert excinfo.value.key == ExceptionKey.DARCYVELOCITY_VAL.value

    # Porosity <= eps
    a = AtesData()
    hubs2 = Hubs()
    hubs2.add_id(h)
    a._porosity_aquifer[h] = Value(common.EPS_ZEROCHECK / 2)
    with pytest.raises(DataException) as excinfo:
        a.validate(stages, hubs2, times)
    assert excinfo.value.key == ExceptionKey.POROSITYAQ_VAL.value

    # Available area unknown stage
    a = AtesData()
    hubs3 = Hubs()
    hubs3.add_id(h)
    a._available_area[StageId("s_unknown"), h] = Value(1.0, LengthUnit.M ** 2)
    with pytest.raises(DataException) as excinfo:
        a.validate(stages, hubs3, times)
    assert excinfo.value.key == ExceptionKey.AVAILABLEAREA_VAL.value


def test_missing_phase_getters_raise_missingids():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()

    i = AtesScheduleId("sch1")
    a.add_schedule_id(h, i)

    with raises_with_key(MissingIdsException, ExceptionKey.PHASEW2CSTART_GET.value):
        a.get_phase_w2c_start(h, i)
    with raises_with_key(MissingIdsException, ExceptionKey.PHASEW2CEND_GET.value):
        a.get_phase_w2c_end(h, i)
    with raises_with_key(MissingIdsException, ExceptionKey.PHASEC2WSTART_GET.value):
        a.get_phase_c2w_start(h, i)
    with raises_with_key(MissingIdsException, ExceptionKey.PHASEC2WEND_GET.value):
        a.get_phase_c2w_end(h, i)


def test_missing_param_getters_raise_missingid():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()

    with raises_with_key(MissingIdException, ExceptionKey.DENSITYROCK_GET.value):
        a.get_density_rock(h)
    with raises_with_key(MissingIdException, ExceptionKey.THICKNESSAQ_GET.value):
        a.get_thickness_aquifer(h)
    with raises_with_key(MissingIdException, ExceptionKey.HYDRAULICCONDUCTAQ_GET.value):
        a.get_hydraulic_conductivity_aquifer(h)
    with raises_with_key(MissingIdException, ExceptionKey.POROSITYAQ_GET.value):
        a.get_porosity_aquifer(h)
    with raises_with_key(MissingIdException, ExceptionKey.MAXDRAWDOWN_GET.value):
        a.get_max_drawdown(h)


def test_pore_velocity_missing_dependencies():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()

    # both missing -> darcy missing triggers
    with raises_with_key(MissingIdException, ExceptionKey.DARCYVELOCITY_GET.value):
        a.get_pore_velocity(h)

    # darcy present but porosity missing -> porosity missing triggers
    a.set_darcy_velocity(h, Value(1.0, LengthUnit.M / TimeUnit.D))
    with raises_with_key(MissingIdException, ExceptionKey.POROSITYAQ_GET.value):
        a.get_pore_velocity(h)


def test_phase_single_point_membership_and_duration():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()
    i = AtesScheduleId("sch1")
    a.add_schedule_id(h, i)

    # single-point phase (start == end)
    a.set_phase_w2c_start(h, i, TimeId(2))
    a.set_phase_w2c_end(h, i, TimeId(2))

    assert a.is_in_w2c_phase(h, i, TimeId(2))
    assert not a.is_in_w2c_phase(h, i, TimeId(1))

    dur = a.get_phase_duration_w2c(h, i, times)
    assert dur.to_float(TimeUnit.H) == 1


def test_phase_overlap_variants_raise_dat_exception():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()
    i = AtesScheduleId("sch1")
    a.add_schedule_id(h, i)

    # Case 1: w2c start lies inside c2w
    a.set_phase_c2w_start(h, i, TimeId(1))
    a.set_phase_c2w_end(h, i, TimeId(4))
    a.set_phase_w2c_start(h, i, TimeId(2))
    a.set_phase_w2c_end(h, i, TimeId(3))
    with raises_with_key(DataException, ExceptionKey.PHASES_VAL.value):
        a.validate(stages, hubs, times)

    # Case 2: w2c end lies inside c2w
    a = AtesData()
    a.add_schedule_id(h, i)
    a.set_phase_c2w_start(h, i, TimeId(1))
    a.set_phase_c2w_end(h, i, TimeId(3))
    a.set_phase_w2c_start(h, i, TimeId(3))
    a.set_phase_w2c_end(h, i, TimeId(4))
    with raises_with_key(DataException, ExceptionKey.PHASES_VAL.value):
        a.validate(stages, hubs, times)


def test_set_density_and_porosity_wrong_units_raise():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()

    with raises_with_key(DataException, ExceptionKey.DENSITYROCK_SET.value):
        a.set_density_rock(h, Value(1.0, PowerUnit.KW))

    with raises_with_key(DataException, ExceptionKey.POROSITYAQ_SET.value):
        a.set_porosity_aquifer(h, Value(0.5, LengthUnit.M))


def test_schedule_ids_independence():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()
    h2 = HubId("h2")
    hubs.add_id(h2)

    i = AtesScheduleId("sch1")
    a.add_schedule_id(h, i)

    assert i in a.get_schedule_ids(h)
    assert a.get_schedule_ids(h2) == set()


def test_porosity_equal_eps_raises():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()
    a._porosity_aquifer[h] = Value(common.EPS_ZEROCHECK)
    with raises_with_key(DataException, ExceptionKey.POROSITYAQ_VAL.value):
        a.validate(stages, hubs, times)


def test_hydraulic_transmissivity_missing_dependencies_raises():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()
    a.set_hydraulic_conductivity_aquifer(h, Value(1.0, LengthUnit.M / TimeUnit.D))
    with raises_with_key(MissingIdException, ExceptionKey.THICKNESSAQ_GET.value):
        a.get_hydraulic_transmissivity_aquifer(h)


def test_set_max_temp_spread_wrong_unit_raises():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()
    with raises_with_key(DataException, ExceptionKey.MAXTEMPSPREADWARM_SET.value):
        a.set_max_temperature_spread_warm(h, Value(1.0, LengthUnit.M))
    with raises_with_key(DataException, ExceptionKey.MAXTEMPSPREADCOLD_SET.value):
        a.set_max_temperature_spread_cold(h, Value(1.0, LengthUnit.M))


def test_negative_available_area_is_allowed():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()
    a.set_available_area(s, h, Value(-1.0, LengthUnit.M ** 2))
    assert a.get_available_area(s, h).to_float(LengthUnit.M ** 2) == -1.0


def test_max_drawdown_wrong_unit_raises():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()
    with raises_with_key(DataException, ExceptionKey.MAXDRAWDOWN_SET.value):
        a.set_max_drawdown(h, Value(1.0, PowerUnit.KW))


def test_validate_spec_heat_cap_unknown_hub_raises():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()
    unknown = HubId("unknown")
    spec_unit = (PowerUnit.KW * TimeUnit.H) / (MassUnit.KG)
    # insert into internal dict with unknown hub
    a._specific_heat_capacity_rock[unknown] = Value(1.0, spec_unit)
    with raises_with_key(DataException, ExceptionKey.SPECIFICHEATCAPROCK_VAL.value):
        a.validate(stages, hubs, times)


def test_validate_thickness_unknown_hub_raises():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()
    unknown = HubId("unknown")
    a._thickness_aquifer[unknown] = Value(1.0, LengthUnit.M)
    with raises_with_key(DataException, ExceptionKey.THICKNESSAQ_VAL.value):
        a.validate(stages, hubs, times)


def test_validate_hydraulic_conductivity_unknown_hub_raises():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()
    unknown = HubId("unknown")
    a._hydraulic_conductivity_aquifer[unknown] = Value(1.0, LengthUnit.M / TimeUnit.D)
    with raises_with_key(DataException, ExceptionKey.HYDRAULICCONDUCTAQ_VAL.value):
        a.validate(stages, hubs, times)


def test_validate_max_temp_spread_unknown_hub_raises():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()
    unknown = HubId("unknown")
    a._max_temperature_spread_warm[unknown] = Value(1.0, TemperatureUnit.K)
    a._max_temperature_spread_cold[unknown] = Value(1.0, TemperatureUnit.K)
    with raises_with_key(DataException, ExceptionKey.MAXTEMPSPREADWARM_VAL.value):
        a.validate(stages, hubs, times)


def test_validate_available_area_unknown_hub_raises():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()
    unknown = HubId("unknown")
    a._available_area[s, unknown] = Value(1.0, LengthUnit.M ** 2)
    with raises_with_key(DataException, ExceptionKey.AVAILABLEAREA_VAL.value):
        a.validate(stages, hubs, times)


def test_phase_time_not_in_horizon_variants_raise():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()
    i = AtesScheduleId("sch1")
    a.add_schedule_id(h, i)

    a._phase_w2c_start[h, i] = TimeId(999)
    with raises_with_key(DataException, ExceptionKey.PHASEW2CSTART_VAL.value):
        a.validate(stages, hubs, times)

    a = AtesData()
    a.add_schedule_id(h, i)
    a._phase_w2c_end[h, i] = TimeId(999)
    with raises_with_key(DataException, ExceptionKey.PHASEW2CEND_VAL.value):
        a.validate(stages, hubs, times)

    a = AtesData()
    a.add_schedule_id(h, i)
    a._phase_c2w_start[h, i] = TimeId(999)
    with raises_with_key(DataException, ExceptionKey.PHASEC2WSTART_VAL.value):
        a.validate(stages, hubs, times)

    a = AtesData()
    a.add_schedule_id(h, i)
    a._phase_c2w_end[h, i] = TimeId(999)
    with raises_with_key(DataException, ExceptionKey.PHASEC2WEND_VAL.value):
        a.validate(stages, hubs, times)


def test_validate_phases_wraparound_overlap_cases():
    h, s, hubs, stages, times = make_basic_env()
    a = AtesData()
    i = AtesScheduleId("sch1")
    a.add_schedule_id(h, i)

    # c2w wrap-around includes 1, w2c start at 1 -> overlap
    a.set_phase_c2w_start(h, i, TimeId(3))
    a.set_phase_c2w_end(h, i, TimeId(1))
    a.set_phase_w2c_start(h, i, TimeId(1))
    a.set_phase_w2c_end(h, i, TimeId(2))
    with raises_with_key(DataException, ExceptionKey.PHASES_VAL.value):
        a.validate(stages, hubs, times)

    # another variant: w2c wrap and c2w overlapping
    a = AtesData()
    a.add_schedule_id(h, i)
    a.set_phase_w2c_start(h, i, TimeId(4))
    a.set_phase_w2c_end(h, i, TimeId(2))
    a.set_phase_c2w_start(h, i, TimeId(2))
    a.set_phase_c2w_end(h, i, TimeId(3))
    with raises_with_key(DataException, ExceptionKey.PHASES_VAL.value):
        a.validate(stages, hubs, times)

