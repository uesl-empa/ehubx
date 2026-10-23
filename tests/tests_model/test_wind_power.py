"""Unit tests for how the wind module computes the available output.

Expected values are worked out by hand in the comments, so a change to the
power curve, the height adjustment or the turbulence-intensity selection shows
up here rather than only as a small shift in the wind demo totals.
"""

import math
from unittest.mock import Mock

import pytest

from ehubx.data.wind_data import adjust_speed_for_height_roughness
from ehubx.model import wind_tech_model
from ehubx.model.wind_tech_model import (
    AIR_DENSITY_KG_M3,
    _get_turbulence_intensity,
    _power_with_turb_intensity,
    _roughness_based_turbulence_intensity,
    _theoretical_fixed_cp_power_watt,
)


# Test turbine: 3 MW, 100 m rotor, Cp = 0.4, cut-in 3 m/s, cut-out 25 m/s
V_IN = 3.0
V_OUT = 25.0
P_RATED_W = 3.0e6
ROTOR_DIAMETER_M = 100.0
CP = 0.4
RHO = AIR_DENSITY_KG_M3


def _power(v):
    return _theoretical_fixed_cp_power_watt(
        v, V_IN, V_OUT, P_RATED_W, ROTOR_DIAMETER_M, CP, RHO
    )


def _expected_power(v_mean, turb_intensity):
    return _power_with_turb_intensity(
        v_mean, turb_intensity, V_IN, V_OUT, P_RATED_W, ROTOR_DIAMETER_M, CP, RHO
    )


# ----------- #
# Power curve #
# ----------- #


def test_air_density_is_sea_level_value():
    assert AIR_DENSITY_KG_M3 == pytest.approx(1.225)


def test_power_curve_follows_cubic_law_below_rated():
    # 0.5 * 1.225 kg/m^3 * (pi * 50^2) m^2 * 0.4 * 8^3 m^3/s^3 = 985.2 kW
    area = math.pi * (ROTOR_DIAMETER_M / 2) ** 2
    expected = 0.5 * RHO * area * CP * 8.0**3
    assert expected == pytest.approx(985_203, rel=1e-5)
    assert _power(8.0) == pytest.approx(expected)


def test_power_curve_is_capped_at_rated_power():
    # The cubic law reaches 3 MW at about 11.6 m/s
    assert _power(15.0) == pytest.approx(P_RATED_W)
    assert _power(24.9) == pytest.approx(P_RATED_W)


def test_power_curve_is_zero_outside_operating_range():
    assert _power(0.0) == 0.0
    assert _power(-1.0) == 0.0
    assert _power(V_IN - 0.2) == 0.0
    assert _power(V_OUT) == 0.0
    assert _power(30.0) == 0.0


def test_power_curve_applies_cut_in_with_tolerance():
    # Speeds within 0.1 m/s below cut-in still produce power
    assert _power(V_IN - 0.05) > 0.0


# ----------------------------------- #
# Expected power with turbulence (TI) #
# ----------------------------------- #


def test_zero_turbulence_gives_the_power_curve():
    for v in (2.0, 6.0, 10.0, 20.0):
        assert _expected_power(v, 0.0) == pytest.approx(_power(v))


def test_turbulence_raises_output_in_the_cubic_region():
    # The power curve is convex below rated power, so spreading the wind speed
    # around the mean increases the expected power (Jensen's inequality)
    assert _expected_power(7.0, 0.15) > _power(7.0)


def test_turbulence_lowers_output_near_rated_speed():
    # Around the rated speed (about 11.6 m/s) the curve is concave
    assert _expected_power(11.6, 0.15) < _power(11.6)


def test_expected_power_stays_close_to_rated_well_above_rated_speed():
    # At 18 m/s with TI 0.1 (sigma 1.8 m/s), almost all probability mass lies
    # between the rated speed and the cut-out speed
    result = _expected_power(18.0, 0.10)
    assert result <= P_RATED_W
    assert result == pytest.approx(P_RATED_W, rel=1e-2)


def test_expected_power_never_exceeds_rated_power():
    for v in (5.0, 10.0, 12.0, 15.0, 20.0, 24.0):
        for ti in (0.05, 0.15, 0.3):
            assert _expected_power(v, ti) <= P_RATED_W * (1 + 1e-9)


def test_expected_power_is_zero_for_calm_wind():
    assert _expected_power(0.0, 0.15) == 0.0


# ----------------------------- #
# Height and roughness profile  #
# ----------------------------- #


def test_log_profile_adjusts_speed_to_hub_height():
    # 6 m/s at 100 m over roughness 0.1 m, to 150 m:
    # 6 * ln(150 / 0.1) / ln(100 / 0.1) = 6 * 7.3132 / 6.9078 = 6.352 m/s
    result = adjust_speed_for_height_roughness(
        speed_ms=6.0, ref_height_m=100.0, roughness_m=0.1, target_height_m=150.0
    )
    assert result == pytest.approx(6.0 * math.log(1500) / math.log(1000))
    assert result == pytest.approx(6.352, abs=1e-3)


def test_log_profile_keeps_speed_at_reference_height():
    result = adjust_speed_for_height_roughness(
        speed_ms=6.0, ref_height_m=100.0, roughness_m=0.1, target_height_m=100.0
    )
    assert result == pytest.approx(6.0)


def test_log_profile_without_roughness_keeps_speed():
    result = adjust_speed_for_height_roughness(
        speed_ms=6.0, ref_height_m=100.0, roughness_m=0.0, target_height_m=150.0
    )
    assert result == 6.0


def test_rougher_terrain_gives_stronger_increase_above_reference_height():
    # Documents a known limitation: there is no displacement height, so above
    # the reference height a forest (0.8 m) gains more speed than pasture
    # (0.1 m)
    pasture = adjust_speed_for_height_roughness(6.0, 100.0, 0.1, 150.0)
    forest = adjust_speed_for_height_roughness(6.0, 100.0, 0.8, 150.0)
    assert forest > pasture > 6.0


# --------------------------------------- #
# Turbulence intensity and its selection  #
# --------------------------------------- #


def test_roughness_based_turbulence_intensity():
    # 1 / ln(100 m / 0.1 m) = 1 / 6.9078 = 0.1448
    assert _roughness_based_turbulence_intensity(100.0, 0.1) == pytest.approx(
        1 / math.log(1000)
    )
    assert _roughness_based_turbulence_intensity(100.0, 0.1) == pytest.approx(
        0.1448, abs=1e-4
    )


def test_roughness_based_turbulence_intensity_without_valid_roughness():
    assert _roughness_based_turbulence_intensity(100.0, 0.0) == 0.0
    assert _roughness_based_turbulence_intensity(100.0, 150.0) == 0.0


def _system(profile_ti=None, fixed_ti=None):
    system = Mock()
    if profile_ti is None:
        system.wind_data.get_turbulence_intensity_profile.return_value = None
    else:
        profile = Mock()
        profile.get_value.return_value.to_float.return_value = profile_ti
        system.wind_data.get_turbulence_intensity_profile.return_value = profile
    if fixed_ti is None:
        system.wind_data.get_fixed_turbulence_intensity.return_value = None
    else:
        fixed = Mock()
        fixed.to_float.return_value = fixed_ti
        system.wind_data.get_fixed_turbulence_intensity.return_value = fixed
    return system


@pytest.fixture(autouse=True)
def _reset_ti_log_memory():
    # _get_turbulence_intensity logs each selection once; keep tests independent
    wind_tech_model._TI_SELECTION_LOGGED.clear()
    yield
    wind_tech_model._TI_SELECTION_LOGGED.clear()


def _selected_ti(system):
    return _get_turbulence_intensity(
        system=system, s="S1", w="W1", t=1, hub_height_m=100.0, rough_m=0.1
    )


def test_turbulence_intensity_prefers_time_series():
    assert _selected_ti(_system(profile_ti=0.20, fixed_ti=0.12)) == pytest.approx(0.20)


def test_turbulence_intensity_falls_back_to_fixed_value():
    assert _selected_ti(_system(fixed_ti=0.12)) == pytest.approx(0.12)


def test_turbulence_intensity_falls_back_to_roughness():
    assert _selected_ti(_system()) == pytest.approx(1 / math.log(1000))


def test_negative_turbulence_intensity_is_clipped_to_zero():
    assert _selected_ti(_system(profile_ti=-0.1)) == 0.0
    assert _selected_ti(_system(fixed_ti=-0.1)) == 0.0
