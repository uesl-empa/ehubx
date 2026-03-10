import math
from contextlib import contextmanager

import pytest

from ehubx.data.ates_tech_data import (
    AtesTechs,
    WellPairAreaCalcMethod,
    _calc_max_pump_rate_from_cooper_jacobs,
    _calc_thermal_radius,
    ExceptionKey,
)
from ehubx.data.ates_data import AtesData, AtesScheduleId
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.time_data import TimeId, Times
from ehubx.data.time_series import TimeSeries
from ehubx.data.unit import (    DimlessUnit,
    LengthUnit,
    MassUnit,
    PowerUnit,
    TemperatureUnit,
    TimeUnit,
    CurrencyUnit,
)
from ehubx.data.value import Value
from ehubx.data import exceptions


@contextmanager
def raises_with_key(exc_type, expected_key):
    with pytest.raises(exc_type) as excinfo:
        yield excinfo
    assert excinfo.value.key == expected_key


def make_basic_env():
    atech = AtesTechs()
    tech = TechId("t1")
    stage = StageId("s1")
    hub = HubId("h1")
    sched = AtesScheduleId("sch1")
    times = Times()
    for i in range(1, 5):
        times.add_id(TimeId(i))
    stages = Stages()
    stages.add_id(stage)
    hubs = Hubs()
    hubs.add_id(hub)
    ates = AtesData()
    ates.add_schedule_id(hub, sched)
    return atech, tech, stage, hub, sched, ates, stages, hubs, times


def test_add_id_duplicate_raises_with_key():
    atech, tech, *_ = make_basic_env()
    atech.add_id(tech)
    with raises_with_key(exceptions.DuplicateIdException, ExceptionKey.ID_ADD.value):
        atech.add_id(tech)


def test_unknown_and_missing_getters_raise_expected_keys():
    atech, tech, stage, hub, sched, ates, stages, hubs, times = make_basic_env()

    # Unknown id -> UnknownIdException (key passes through)
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.DENSITYFLUID_GET.value):
        atech.get_density_fluid(tech)

    # Also assert unknown for ec getters
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.ECEL_GET.value):
        atech.get_ec_el(tech)
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.ECHT_GET.value):
        atech.get_ec_ht(tech)
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.ECCO_GET.value):
        atech.get_ec_co(tech)

    # Add id -> missing value raises MissingIdException with same key
    atech.add_id(tech)
    with raises_with_key(exceptions.MissingIdException, ExceptionKey.DENSITYFLUID_GET.value):
        atech.get_density_fluid(tech)

    # ec getters missing
    with raises_with_key(exceptions.MissingIdException, ExceptionKey.ECEL_GET.value):
        atech.get_ec_el(tech)
    with raises_with_key(exceptions.MissingIdException, ExceptionKey.ECHT_GET.value):
        atech.get_ec_ht(tech)
    with raises_with_key(exceptions.MissingIdException, ExceptionKey.ECCO_GET.value):
        atech.get_ec_co(tech)

    with raises_with_key(exceptions.MissingIdException, ExceptionKey.WELLRADIUS_GET.value):
        atech.get_well_radius(tech)

    with raises_with_key(exceptions.MissingIdsException, ExceptionKey.WELLDISTANCE_GET.value):
        atech.get_well_distance(stage, hub, tech)


def test_setters_wrong_units_raise_keys():
    atech, tech, stage, hub, sched, ates, stages, hubs, times = make_basic_env()
    atech.add_id(tech)

    # ec_el expects energy unit (kW*h)
    with raises_with_key(exceptions.DataException, ExceptionKey.ECEL_SET.value):
        atech.set_ec_el(tech, EcId("e1"), PowerUnit.KW)

    # density expects mass/volume
    with raises_with_key(exceptions.DataException, ExceptionKey.DENSITYFLUID_SET.value):
        atech.set_density_fluid(tech, Value(1.0, PowerUnit.KW))

    # specific heat expects kW*h/(kg*K)
    with raises_with_key(exceptions.DataException, ExceptionKey.SPECIFICHEATCAPFLUID_SET.value):
        atech.set_specific_heat_capacity_fluid(tech, Value(1.0, PowerUnit.KW))

    # well radius expects length
    with raises_with_key(exceptions.DataException, ExceptionKey.WELLRADIUS_SET.value):
        atech.set_well_radius(tech, Value(1.0, PowerUnit.KW))

    # well distance expects length (note we need to pass stage & hub)
    with raises_with_key(exceptions.DataException, ExceptionKey.WELLDISTANCE_SET.value):
        atech.set_well_distance(stage, hub, tech, Value(1.0, PowerUnit.KW))

    # well_pairs_min expects dimless
    with raises_with_key(exceptions.DataException, ExceptionKey.WELLPAIRSMIN_SET.value):
        atech.set_well_pairs_min(stage, hub, tech, sched, Value(1.0, LengthUnit.M))

    # well_pairs_max has a bug that raises WELLPAIRSMIN_SET.value on unit error
    with raises_with_key(exceptions.DataException, ExceptionKey.WELLPAIRSMAX_SET.value):
        atech.set_well_pairs_max(stage, hub, tech, sched, Value(1.0, LengthUnit.M))

    # elec_per_flow_heat expects kW*h/m^3
    with raises_with_key(exceptions.DataException, ExceptionKey.ELECPERFLOWHEAT_SET.value):
        atech.set_elec_per_flow_heat(stage, tech, Value(1.0, PowerUnit.KW))

    # elec_per_flow_cool expects kW*h/m^3
    with raises_with_key(exceptions.DataException, ExceptionKey.ELECPERFLOWCOOL_SET.value):
        atech.set_elec_per_flow_cool(stage, tech, Value(1.0, PowerUnit.KW))

    # ec_ht and ec_co expect energy unit
    with raises_with_key(exceptions.DataException, ExceptionKey.ECHT_SET.value):
        atech.set_ec_ht(tech, EcId("e2"), PowerUnit.KW)
    with raises_with_key(exceptions.DataException, ExceptionKey.ECCO_SET.value):
        atech.set_ec_co(tech, EcId("e3"), PowerUnit.KW)

    # max pump rate setters expect m^3/h
    with raises_with_key(exceptions.DataException, ExceptionKey.MAXPUMPRATEWARM_SET.value):
        atech.set_max_pump_rate_per_warm_well(stage, hub, tech, sched, Value(1.0, LengthUnit.M))
    with raises_with_key(exceptions.DataException, ExceptionKey.MAXPUMPRATECOLD_SET.value):
        atech.set_max_pump_rate_per_cold_well(stage, hub, tech, sched, Value(1.0, LengthUnit.M))


def test_volumetric_heat_capacity_and_derived_values():
    atech, tech, stage, hub, sched, ates, stages, hubs, times = make_basic_env()
    atech.add_id(tech)

    # set correct fluid properties
    density = Value(1000.0, MassUnit.KG / (LengthUnit.M ** 3))
    spec = Value(4.0, (PowerUnit.KW * TimeUnit.H) / (MassUnit.KG * TemperatureUnit.K))
    atech.set_density_fluid(tech, density)
    atech.set_specific_heat_capacity_fluid(tech, spec)

    vol_fl = atech.get_volumetric_heat_capacity_fluid(tech)
    expected_unit = (PowerUnit.KW * TimeUnit.H) / (LengthUnit.M ** 3 * TemperatureUnit.K)
    assert vol_fl.to_float(expected_unit) == pytest.approx(4000.0)

    # set rock properties in ates_data and porosity to compute aquifer volumetric
    rock_density = Value(2000.0, MassUnit.KG / (LengthUnit.M ** 3))
    rock_spec = Value(2.0, (PowerUnit.KW * TimeUnit.H) / (MassUnit.KG * TemperatureUnit.K))
    ates.set_density_rock(hub, rock_density)
    ates.set_specific_heat_capacity_rock(hub, rock_spec)
    ates.set_porosity_aquifer(hub, Value(0.5))

    vol_aq = atech.get_volumetric_heat_capacity_aquifer(hub, tech, ates)
    # vol_fl = 4000, vol_rock = 4000 -> weighted avg = 4000
    assert vol_aq.to_float(expected_unit) == pytest.approx(4000.0)

    # thermal retardation factor and heat front velocity
    # need pore velocity: set darcy velocity and porosity
    ates.set_darcy_velocity(hub, Value(2.0, LengthUnit.M / TimeUnit.D))
    # porosity already set to 0.5 -> pore velocity = 4 m/d
    rf = atech.get_thermal_retardation_factor(hub, tech, ates)
    # porosity * vol_fl / vol_aq = 0.5 * 4000 / 4000 = 0.5
    assert rf.to_float(DimlessUnit()) == pytest.approx(0.5)

    hv = atech.get_heat_front_velocity(hub, tech, ates)
    # heat front velocity = rf * pore_velocity -> units Length/Time
    assert hv.unit.same_type_as(LengthUnit.M / TimeUnit.D)

    # computed thermal radii via AtesTechs methods
    # set phase windows in terms of time ids [1..4] so duration is >0
    ates.set_phase_w2c_start(hub, sched, TimeId(1))
    ates.set_phase_w2c_end(hub, sched, TimeId(2))
    ates.set_phase_c2w_start(hub, sched, TimeId(3))
    ates.set_phase_c2w_end(hub, sched, TimeId(4))
    # set geometric and pumping dependencies
    atech.set_well_radius(tech, Value(0.5, LengthUnit.M))
    atech.set_well_distance(stage, hub, tech, Value(10.0, LengthUnit.M))
    ates.set_hydraulic_conductivity_aquifer(hub, Value(2.0, LengthUnit.M / TimeUnit.D))
    ates.set_max_drawdown(hub, Value(1.0, LengthUnit.M))
    # thermal front velocity already available via rf and pore velocity
    # thickness set above; volumetric capacities set
    ates.set_thickness_aquifer(hub, Value(10.0, LengthUnit.M))
    twarm = atech.get_thermal_radius_per_warm_well(stage, hub, tech, sched, ates, times)
    tcold = atech.get_thermal_radius_per_cold_well(stage, hub, tech, sched, ates, times)
    assert twarm.unit.same_type_as(LengthUnit.M)
    assert tcold.unit.same_type_as(LengthUnit.M)


def test_calc_functions_and_thermal_radii():
    # test _calc_max_pump_rate_from_cooper_jacobs
    well_dist = Value(10.0, LengthUnit.M)
    max_drawdown = Value(1.0, LengthUnit.M)
    well_radius = Value(0.5, LengthUnit.M)
    hydr_trans = Value(2.0, (LengthUnit.M ** 2) / TimeUnit.D)

    max_rate = _calc_max_pump_rate_from_cooper_jacobs(
        well_dist, max_drawdown, well_radius, hydr_trans
    )
    assert max_rate.unit.same_type_as((LengthUnit.M ** 3) / TimeUnit.H)

    # test _calc_thermal_radius math against manual computation
    vol_aq = Value(4000.0, (PowerUnit.KW * TimeUnit.H) / (LengthUnit.M ** 3 * TemperatureUnit.K))
    thickness = Value(10.0, LengthUnit.M)
    heat_vel = Value(2.0, LengthUnit.M / TimeUnit.H)
    vol_fl = Value(2000.0, (PowerUnit.KW * TimeUnit.H) / (LengthUnit.M ** 3 * TemperatureUnit.K))
    inj_dur = Value(2.0, TimeUnit.H)
    max_inj_rate = Value(1.0, (LengthUnit.M ** 3) / TimeUnit.H)

    tr = _calc_thermal_radius(vol_aq, thickness, heat_vel, vol_fl, inj_dur, max_inj_rate)
    # compute volume-equivalent part
    therm_rad_vol_sq = vol_fl * max_inj_rate * inj_dur / (vol_aq * math.pi * thickness)
    therm_rad_vol = therm_rad_vol_sq.root(deg=2)
    therm_rad_adv = heat_vel * inj_dur
    expected = therm_rad_vol + therm_rad_adv
    assert tr.to_float(LengthUnit.M) == pytest.approx(expected.to_float(LengthUnit.M))


def test_calc_area_per_well_pair_methods():
    r1 = Value(2.0, LengthUnit.M)
    r2 = Value(1.0, LengthUnit.M)

    area_two = AtesTechs().calc_area_per_well_pair(r1, r2, WellPairAreaCalcMethod.TWOCIRCLES)
    # area = pi*(r1^2 + r2^2)
    expected = math.pi * (r1**2 + r2**2)
    assert area_two.to_float(LengthUnit.M ** 2) == pytest.approx(expected.to_float(LengthUnit.M ** 2))

    area_rect = AtesTechs().calc_area_per_well_pair(r1, r2, WellPairAreaCalcMethod.SMALLESTRECTANGLE)
    side_1 = 2 * (r1 + r2)
    side_2 = 2 * max(r1, r2)
    expected_rect = side_1 * side_2
    assert area_rect.to_float(LengthUnit.M ** 2) == pytest.approx(expected_rect.to_float(LengthUnit.M ** 2))


def test_calc_max_power_densities_units():
    atech, tech, stage, hub, sched, ates, stages, hubs, times = make_basic_env()
    atech.add_id(tech)
    # fluid props
    atech.set_density_fluid(tech, Value(1000.0, MassUnit.KG / (LengthUnit.M ** 3)))
    atech.set_specific_heat_capacity_fluid(tech, Value(4.0, (PowerUnit.KW * TimeUnit.H) / (MassUnit.KG * TemperatureUnit.K)))
    # rock and aquifer props
    ates.set_density_rock(hub, Value(2000.0, MassUnit.KG / (LengthUnit.M ** 3)))
    ates.set_specific_heat_capacity_rock(hub, Value(2.0, (PowerUnit.KW * TimeUnit.H) / (MassUnit.KG * TemperatureUnit.K)))
    ates.set_porosity_aquifer(hub, Value(0.5))
    ates.set_thickness_aquifer(hub, Value(10.0, LengthUnit.M))
    ates.set_darcy_velocity(hub, Value(2.0, LengthUnit.M / TimeUnit.D))
    # geometry and pumping deps
    atech.set_well_radius(tech, Value(0.5, LengthUnit.M))
    atech.set_well_distance(stage, hub, tech, Value(10.0, LengthUnit.M))
    ates.set_hydraulic_conductivity_aquifer(hub, Value(2.0, LengthUnit.M / TimeUnit.D))
    ates.set_max_drawdown(hub, Value(1.0, LengthUnit.M))
    # schedule windows
    ates.set_phase_w2c_start(hub, sched, TimeId(1))
    ates.set_phase_w2c_end(hub, sched, TimeId(2))
    ates.set_phase_c2w_start(hub, sched, TimeId(3))
    ates.set_phase_c2w_end(hub, sched, TimeId(4))
    # temp spreads
    ates.set_max_temperature_spread_warm(hub, Value(5.0, TemperatureUnit.K))
    ates.set_max_temperature_spread_cold(hub, Value(4.0, TemperatureUnit.K))

    ph, pc = atech.calc_max_power_densities(stage, hub, tech, sched, ates, times)
    assert ph.unit.same_type_as(PowerUnit.KW / (LengthUnit.M ** 2))
    assert pc.unit.same_type_as(PowerUnit.KW / (LengthUnit.M ** 2))


def test_max_pump_rate_computed_branch():
    atech, tech, stage, hub, sched, ates, stages, hubs, times = make_basic_env()
    atech.add_id(tech)

    # fill dependencies so computation branch executes
    atech.set_well_distance(stage, hub, tech, Value(10.0, LengthUnit.M))
    atech.set_well_radius(tech, Value(0.5, LengthUnit.M))
    ates.set_thickness_aquifer(hub, Value(10.0, LengthUnit.M))
    ates.set_hydraulic_conductivity_aquifer(hub, Value(2.0, LengthUnit.M / TimeUnit.D))
    ates.set_max_drawdown(hub, Value(1.0, LengthUnit.M))

    calc = atech.get_max_pump_rate_per_warm_well(stage, hub, tech, sched, ates)
    direct = _calc_max_pump_rate_from_cooper_jacobs(
        atech.get_well_distance(stage, hub, tech),
        ates.get_max_drawdown(hub),
        atech.get_well_radius(tech),
        ates.get_hydraulic_transmissivity_aquifer(hub),
    )
    assert calc.to_float((LengthUnit.M ** 3) / TimeUnit.H) == pytest.approx(
        direct.to_float((LengthUnit.M ** 3) / TimeUnit.H)
    )



def test_validate_ids_and_ec_checks_raise_keys():
    atech, tech, stage, hub, sched, ates, stages, hubs, times = make_basic_env()
    # ID validation: tech present in atech but missing from techs
    atech.add_id(tech)
    techs = Techs()
    ecs = Ecs()
    with raises_with_key(exceptions.DataException, ExceptionKey.ID_VAL.value):
        atech.validate(stages, hubs, techs, ecs, ates, times)

    # Now add tech to techs and set an unknown ec_el -> ECEL_VAL
    techs.add_id(tech)
    atech._ec_el[tech] = EcId("e_unknown")
    with raises_with_key(exceptions.DataException, ExceptionKey.ECEL_VAL.value):
        atech.validate(stages, hubs, techs, ecs, ates, times)

    # Duplicate ecs across el/ht/co should raise ECS_VAL (ensure ecs contains the ec)
    ecs.add_id(EcId("e1"))
    ecs.add_id(EcId("e2"))
    atech._ec_el[tech] = EcId("e1")
    atech._ec_ht[tech] = EcId("e1")
    atech._ec_co[tech] = EcId("e2")
    with raises_with_key(exceptions.DataException, ExceptionKey.ECS_VAL.value):
        atech.validate(stages, hubs, techs, ecs, ates, times)


def test_schedule_existence_and_well_pairs_minmax_raise_keys():
    atech, tech, stage, hub, sched, ates, stages, hubs, times = make_basic_env()
    techs = Techs()
    techs.add_id(tech)
    atech.add_id(tech)
    # allow tech in hub but no schedule in ates (make a fresh ates without schedules)
    techs.add_allowed_hub(hub, tech)
    a = AtesData()
    # add minimal ecs so we don't short-circuit on missing ec_* getters
    ecs = Ecs()
    ecs.add_id(EcId("e1"))
    ecs.add_id(EcId("e2"))
    ecs.add_id(EcId("e3"))
    atech._ec_el[tech] = EcId("e1")
    atech._ec_ht[tech] = EcId("e2")
    atech._ec_co[tech] = EcId("e3")
    with raises_with_key(exceptions.DataException, ExceptionKey.SCHEDULEEXISTENCE_VAL.value):
        atech.validate(stages, hubs, techs, ecs, a, times)

    # now test well_pairs min>max -> WELLPAIRSMAX_VAL
    a2 = AtesData()
    a2.add_schedule_id(hub, sched)
    atech._well_pairs_min[(stage, hub, tech, sched)] = Value(5, unit=DimlessUnit())
    atech._well_pairs_max[(stage, hub, tech, sched)] = Value(2, unit=DimlessUnit())
    with raises_with_key(exceptions.DataException, ExceptionKey.WELLPAIRSMAX_VAL.value):
        atech.validate(stages, hubs, techs, ecs, a2, times)


def test_negative_values_and_consistency_checks_raise_expected_keys():
    atech, tech, stage, hub, sched, ates, stages, hubs, times = make_basic_env()
    techs = Techs()
    techs.add_id(tech)
    atech.add_id(tech)
    # ensure schedule exists
    ates2 = AtesData()
    ates2.add_schedule_id(hub, sched)

    # add ec so validation reaches the intended checks
    ecs = Ecs()
    ecs.add_id(EcId("e1"))
    ecs.add_id(EcId("e2"))
    ecs.add_id(EcId("e3"))
    atech._ec_el[tech] = EcId("e1")
    atech._ec_ht[tech] = EcId("e2")
    atech._ec_co[tech] = EcId("e3")

    # max pump rate negative
    atech.set_max_pump_rate_per_warm_well(stage, hub, tech, sched, Value(-1.0, unit=(LengthUnit.M**3)/TimeUnit.H))
    with raises_with_key(exceptions.DataException, ExceptionKey.MAXPUMPRATEWARM_VAL.value):
        atech.validate(stages, hubs, techs, ecs, ates2, times)
    # remove the offending max_pump_rate so the next check runs independently
    atech._max_pump_rate_per_warm_well.pop((stage, hub, tech, sched), None)

    # thermal radius negative
    atech._thermal_radius_warm[(stage, hub, tech, sched)] = Value(-1.0, unit=LengthUnit.M)
    with raises_with_key(exceptions.DataException, ExceptionKey.THERMALRADIUSWARM_VAL.value):
        atech.validate(stages, hubs, techs, ecs, ates2, times)
    # remove thermal radius to allow following checks to run
    atech._thermal_radius_warm.pop((stage, hub, tech, sched), None)
    # elec_per_energy_heat negative
    atech._elec_per_energy_heat[(stage, hub, tech)] = Value(-0.5, unit=DimlessUnit())
    with raises_with_key(exceptions.DataException, ExceptionKey.ELECPERENERGYHEAT_VAL.value):
        atech.validate(stages, hubs, techs, ecs, ates2, times)
    # remove elec_per_energy to allow subsequent checks
    atech._elec_per_energy_heat.pop((stage, hub, tech), None)

    # well distance less than radius
    atech.set_well_radius(tech, Value(2.0, LengthUnit.M))
    atech.set_well_distance(stage, hub, tech, Value(1.0, LengthUnit.M))
    with raises_with_key(exceptions.DataException, ExceptionKey.WELLDISTANCE_VAL.value):
        atech.validate(stages, hubs, techs, ecs, ates2, times)
    # clear well radius/distance entries
    atech._well_radius.pop(tech, None)
    atech._well_distance.pop((stage, hub, tech), None)

    # max heat/cool product < 1
    atech._max_heat_over_cool[(stage, hub, tech, sched)] = Value(0.1, unit=DimlessUnit())
    atech._max_cool_over_heat[(stage, hub, tech, sched)] = Value(0.1, unit=DimlessUnit())
    with raises_with_key(exceptions.DataException, ExceptionKey.MAXHEATOVERCOOLMAXCOOLOVERHEAT_VAL.value):
        atech.validate(stages, hubs, techs, ecs, ates2, times)


def test_availability_def_value_negative_raises_key():
    atech, tech, stage, hub, sched, ates, stages, hubs, times = make_basic_env()
    techs = Techs()
    techs.add_id(tech)
    atech.add_id(tech)
    ates2 = AtesData()
    ates2.add_schedule_id(hub, sched)

    ts = TimeSeries()
    ts.def_value = Value(-0.1, unit=DimlessUnit())
    atech._availability[(stage, hub, tech, sched)] = ts

    # make sure ec present
    ecs = Ecs()
    ecs.add_id(EcId("e1"))
    ecs.add_id(EcId("e2"))
    ecs.add_id(EcId("e3"))
    atech._ec_el[tech] = EcId("e1")
    atech._ec_ht[tech] = EcId("e2")
    atech._ec_co[tech] = EcId("e3")

    with raises_with_key(exceptions.DataException, ExceptionKey.AVAILABILITY_VAL.value):
        atech.validate(stages, hubs, techs, ecs, ates2, times)


def test_setters_and_getters_valid_values():
    atech, tech, stage, hub, sched, ates, stages, hubs, times = make_basic_env()
    atech.add_id(tech)

    # valid ecs and units
    atech.set_ec_el(tech, EcId("e1"), PowerUnit.KW * TimeUnit.H)
    atech.set_ec_ht(tech, EcId("e2"), PowerUnit.KW * TimeUnit.H)
    atech.set_ec_co(tech, EcId("e3"), PowerUnit.KW * TimeUnit.H)
    assert atech.get_ec_el(tech) == EcId("e1")
    assert atech.get_ec_ht(tech) == EcId("e2")
    assert atech.get_ec_co(tech) == EcId("e3")

    # fluid properties
    density = Value(1000.0, MassUnit.KG / (LengthUnit.M ** 3))
    atech.set_density_fluid(tech, density)
    assert atech.get_density_fluid(tech).to_float(MassUnit.KG / (LengthUnit.M ** 3)) == pytest.approx(1000.0)

    spec = Value(4.0, (PowerUnit.KW * TimeUnit.H) / (MassUnit.KG * TemperatureUnit.K))
    atech.set_specific_heat_capacity_fluid(tech, spec)
    assert atech.get_specific_heat_capacity_fluid(tech).to_float(
        (PowerUnit.KW * TimeUnit.H) / (MassUnit.KG * TemperatureUnit.K)
    ) == pytest.approx(4.0)

    # geometry
    atech.set_well_radius(tech, Value(0.5, LengthUnit.M))
    assert atech.get_well_radius(tech).to_float(LengthUnit.M) == pytest.approx(0.5)

    atech.set_well_distance(stage, hub, tech, Value(10.0, LengthUnit.M))
    assert atech.get_well_distance(stage, hub, tech).to_float(LengthUnit.M) == pytest.approx(10.0)

    # dimless counts
    atech.set_well_pairs_min(stage, hub, tech, sched, Value(2.0, unit=DimlessUnit()))
    atech.set_well_pairs_max(stage, hub, tech, sched, Value(5.0, unit=DimlessUnit()))
    assert atech._well_pairs_min[(stage, hub, tech, sched)].to_float(DimlessUnit()) == pytest.approx(2.0)
    assert atech._well_pairs_max[(stage, hub, tech, sched)].to_float(DimlessUnit()) == pytest.approx(5.0)

    # electricity per flow (units)
    atech.set_elec_per_flow_heat(stage, tech, Value(1.0, (PowerUnit.KW * TimeUnit.H) / (LengthUnit.M ** 3)))
    assert (
        atech._elec_per_flow_heat[(stage, tech)].to_float((PowerUnit.KW * TimeUnit.H) / (LengthUnit.M ** 3))
        == pytest.approx(1.0)
    )

    # elec per energy heat/cool computed from flow and thermodynamics
    ates.set_max_temperature_spread_warm(hub, Value(5.0, TemperatureUnit.K))
    ates.set_max_temperature_spread_cold(hub, Value(4.0, TemperatureUnit.K))
    atech.set_elec_per_flow_cool(stage, tech, Value(0.5, (PowerUnit.KW * TimeUnit.H) / (LengthUnit.M ** 3)))
    eph = atech.get_elec_per_energy_heat(stage, hub, tech, ates)
    epc = atech.get_elec_per_energy_cool(stage, hub, tech, ates)
    assert eph.unit.same_type_as(DimlessUnit())
    assert epc.unit.same_type_as(DimlessUnit())


def test_well_pairs_minmax_validate_success():
    atech, tech, stage, hub, sched, ates, stages, hubs, times = make_basic_env()
    atech.add_id(tech)
    techs = Techs()
    techs.add_id(tech)
    techs.add_allowed_hub(hub, tech)

    # add schedule and ecs so validate runs intended checks
    a = AtesData()
    a.add_schedule_id(hub, sched)
    ecs = Ecs()
    ecs.add_id(EcId("e1"))
    ecs.add_id(EcId("e2"))
    ecs.add_id(EcId("e3"))
    # ensure distinct ecs so duplicate-ecs validation does not trigger
    atech._ec_el[tech] = EcId("e1")
    atech._ec_ht[tech] = EcId("e2")
    atech._ec_co[tech] = EcId("e3")

    atech.set_well_pairs_min(stage, hub, tech, sched, Value(2.0, unit=DimlessUnit()))
    atech.set_well_pairs_max(stage, hub, tech, sched, Value(5.0, unit=DimlessUnit()))

    # should not raise
    atech.validate(stages, hubs, techs, ecs, a, times)


def test_well_pair_area_calc_method_default_and_setter():
    atech, tech, stage, hub, sched, ates, stages, hubs, times = make_basic_env()
    atech.add_id(tech)
    # default
    assert atech.get_well_pair_area_calc_method(tech) == WellPairAreaCalcMethod.SMALLESTRECTANGLE
    # set
    atech.set_well_pair_area_calc_method(tech, WellPairAreaCalcMethod.TWOCIRCLES)
    assert atech.get_well_pair_area_calc_method(tech) == WellPairAreaCalcMethod.TWOCIRCLES


def test_in_out_ecs_sets():
    atech, tech, stage, hub, sched, ates, stages, hubs, times = make_basic_env()
    atech.add_id(tech)
    atech.set_ec_el(tech, EcId("e_el"), PowerUnit.KW * TimeUnit.H)
    atech.set_ec_ht(tech, EcId("e_ht"), PowerUnit.KW * TimeUnit.H)
    atech.set_ec_co(tech, EcId("e_co"), PowerUnit.KW * TimeUnit.H)
    assert atech.get_in_ecs(tech) == {EcId("e_el")}
    assert atech.get_out_ecs(tech) == {EcId("e_ht"), EcId("e_co")}


def test_cost_and_co2_setters_wrong_units():
    atech, tech, stage, hub, sched, ates, stages, hubs, times = make_basic_env()
    atech.add_id(tech)
    # wrong units
    with raises_with_key(exceptions.DataException, ExceptionKey.CAPEXPERWELLPAIR_SET.value):
        atech.set_capex_per_well_pair(stage, tech, Value(1.0, LengthUnit.M))
    with raises_with_key(exceptions.DataException, ExceptionKey.OPEXPERWELLPAIR_SET.value):
        atech.set_opex_per_well_pair(stage, tech, Value(1.0, LengthUnit.M))
    with raises_with_key(exceptions.DataException, ExceptionKey.CO2PERWELLPAIR_SET.value):
        atech.set_co2_per_well_pair(stage, tech, Value(1.0, LengthUnit.M))

    # defaults
    assert atech.get_capex_per_well_pair(stage, tech).unit.same_type_as(CurrencyUnit.CHF)
    assert atech.get_opex_per_well_pair(stage, tech).unit.same_type_as(CurrencyUnit.CHF)
    assert atech.get_co2_per_well_pair(stage, tech).unit.same_type_as(MassUnit.KG)


def test_availability_default_is_one():
    atech, tech, stage, hub, sched, ates, stages, hubs, times = make_basic_env()
    atech.add_id(tech)
    ts = atech.get_availability(stage, hub, tech, sched)
    assert ts.def_value.to_float(DimlessUnit()) == pytest.approx(1.0)


def test_precomputed_max_pump_rate_and_thermal_radius_positive():
    atech, tech, stage, hub, sched, ates, stages, hubs, times = make_basic_env()
    atech.add_id(tech)
    techs = Techs()
    techs.add_id(tech)
    techs.add_allowed_hub(hub, tech)

    a = AtesData()
    a.add_schedule_id(hub, sched)
    ecs = Ecs()
    ecs.add_id(EcId("e1"))
    ecs.add_id(EcId("e2"))
    ecs.add_id(EcId("e3"))
    # ensure distinct heating/cooling ecs so validation passes
    atech._ec_el[tech] = EcId("e1")
    atech._ec_ht[tech] = EcId("e2")
    atech._ec_co[tech] = EcId("e3")

    atech.set_max_pump_rate_per_warm_well(stage, hub, tech, sched, Value(1.0, unit=(LengthUnit.M ** 3) / TimeUnit.H))
    atech._thermal_radius_warm[(stage, hub, tech, sched)] = Value(1.0, LengthUnit.M)

    # should not raise
    atech.validate(stages, hubs, techs, ecs, a, times)

    val = atech.get_max_pump_rate_per_warm_well(stage, hub, tech, sched, a)
    assert val.to_float((LengthUnit.M ** 3) / TimeUnit.H) == pytest.approx(1.0)


def test_availability_def_value_valid_does_not_raise():
    atech, tech, stage, hub, sched, ates, stages, hubs, times = make_basic_env()
    atech.add_id(tech)
    techs = Techs()
    techs.add_id(tech)
    techs.add_allowed_hub(hub, tech)

    a = AtesData()
    a.add_schedule_id(hub, sched)
    ecs = Ecs()
    ecs.add_id(EcId("e1"))
    ecs.add_id(EcId("e2"))
    ecs.add_id(EcId("e3"))
    # ensure distinct heating/cooling ecs so validation passes
    atech._ec_el[tech] = EcId("e1")
    atech._ec_ht[tech] = EcId("e2")
    atech._ec_co[tech] = EcId("e3")

    ts = TimeSeries()
    ts.def_value = Value(0.6, unit=DimlessUnit())
    atech._availability[(stage, hub, tech, sched)] = ts

    # should not raise
    atech.validate(stages, hubs, techs, ecs, a, times)

