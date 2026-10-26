import pytest

from ehubx.core.common import HOURS_PER_YEAR
from ehubx.data import energy_system_data
from ehubx.data.energy_system_data import EnergySystem, ExceptionKey as SysExceptionKey
from ehubx.data.ec_data import EcId, ExceptionKey as EcExceptionKey
from ehubx.data.stage_data import StageId
from ehubx.data.hub_data import HubId
from ehubx.data.tech_data import TechId
from ehubx.data.time_data import TimeId
from ehubx.data.value import Value
from ehubx.data.unit import (
    PowerUnit,
    DimlessUnit,
    CurrencyUnit,
    LengthUnit,
    MassUnit,
    TimeUnit,
)
from ehubx.data import exceptions


def test_interest_rate_missing_and_setter_unit_validation():
    sys = EnergySystem()

    # Getting when not set -> MissingValueException with correct key
    with pytest.raises(exceptions.MissingValueException) as excinfo:
        _ = sys.interest_rate_def
    assert excinfo.value.key == SysExceptionKey.INTERESTRATEDEF_GET.value

    # Setting with correct unit works
    v = Value(0.05, DimlessUnit())
    sys.interest_rate_def = v
    assert sys.interest_rate_def == v

    # Setting with incorrect unit raises DataException with expected key
    with pytest.raises(exceptions.DataException) as excinfo2:
        sys.interest_rate_def = Value(1.0, PowerUnit.KW)
    assert excinfo2.value.key == SysExceptionKey.INTERESTRATEDEF_VAL.value


def test_trl_threshold_default_and_setter_validation():
    sys = EnergySystem()

    # Default when not set -> Value(0)
    assert sys.trl_threshold == Value(0)

    # Setting with wrong unit raises DataException with expected key
    with pytest.raises(exceptions.DataException) as excinfo:
        sys.trl_threshold = Value(1.0, PowerUnit.KW)
    assert excinfo.value.key == SysExceptionKey.TRLTHRESHOLD_SET.value


def test_num_times_horizon_missing_and_validation():
    sys = EnergySystem()

    # Getting when not set -> MissingValueException with correct key
    with pytest.raises(exceptions.MissingValueException) as excinfo:
        _ = sys.num_times_horizon
    assert excinfo.value.key == SysExceptionKey.NUMTIMESHORIZON_GET.value

    # Setting invalid (<= 0) and running validate should raise DataException
    sys.num_times_horizon = -1
    with pytest.raises(exceptions.DataException) as excinfo2:
        sys.validate()
    assert excinfo2.value.key == SysExceptionKey.NUMTIMESHORIZON_VAL.value


def test_interest_rate_negative_validation_raises_on_validate():
    sys = EnergySystem()
    sys.interest_rate_def = Value(-0.01, DimlessUnit())

    with pytest.raises(exceptions.DataException) as excinfo:
        sys.validate()
    assert excinfo.value.key == SysExceptionKey.INTERESTRATEDEF_VAL.value


def test_get_heur_limits_raises_if_no_heuristic_max_set():
    sys = EnergySystem()

    # Add minimal ids to allow calls to proceed to ec heuristic checks
    s = StageId("s1")
    h = HubId("h1")
    e = EcId("e1")
    sys.stages.add_id(s)
    sys.hubs.add_id(h)
    sys.ecs.add_id(e)

    # No heuristic_max set for ec -> get_heur_limit_* should raise DataException
    with pytest.raises(exceptions.DataException) as excinfo_in:
        sys.get_heur_limit_max_in(s, h, e)
    assert excinfo_in.value.key == EcExceptionKey.HEURMAX_GET.value

    with pytest.raises(exceptions.DataException) as excinfo_sum:
        sys.get_heur_limit_max_sum_in(s, h, e)
    # Fallback also calls get_heuristic_max -> same key
    assert excinfo_sum.value.key == EcExceptionKey.HEURMAX_GET.value


# -------- #
# Unit Properties Tests
# -------- #
def test_currency_unit_default_and_setter():
    sys = EnergySystem()

    # Default currency is CHF
    assert sys.currency_unit == CurrencyUnit.CHF

    # Can set to different currency
    sys.currency_unit = CurrencyUnit.EUR
    assert sys.currency_unit == CurrencyUnit.EUR

    sys.currency_unit = CurrencyUnit.USD
    assert sys.currency_unit == CurrencyUnit.USD


def test_length_unit_default_and_setter():
    sys = EnergySystem()

    # Default length unit is M
    assert sys.length_unit == LengthUnit.M

    # Can set to different unit
    sys.length_unit = LengthUnit.KM
    assert sys.length_unit == LengthUnit.KM

    sys.length_unit = LengthUnit.M
    assert sys.length_unit == LengthUnit.M


def test_mass_unit_default_and_setter():
    sys = EnergySystem()

    # Default mass unit is KG
    assert sys.mass_unit == MassUnit.KG

    # Can set to different unit
    sys.mass_unit = MassUnit.T
    assert sys.mass_unit == MassUnit.T

    sys.mass_unit = MassUnit.KG
    assert sys.mass_unit == MassUnit.KG


def test_power_unit_default_and_setter():
    sys = EnergySystem()

    # Default power unit is KW
    assert sys.power_unit == PowerUnit.KW

    # Can set to different unit
    sys.power_unit = PowerUnit.W
    assert sys.power_unit == PowerUnit.W

    sys.power_unit = PowerUnit.MW
    assert sys.power_unit == PowerUnit.MW


# -------- #
# TRL Threshold Validation
# -------- #
def test_trl_threshold_with_valid_value():
    """Test that _validate_trl_threshold passes with a valid (non-negative) trl_threshold"""
    sys = EnergySystem()

    # Set trl_threshold to positive value
    sys.trl_threshold = Value(5, DimlessUnit())

    # Should not raise - validation passes for non-negative trl_threshold
    sys._validate_trl_threshold()
    assert sys.trl_threshold == Value(5, DimlessUnit())


def test_trl_threshold_negative_value_validation():
    """Test that _validate_trl_threshold logs warning for negative trl_threshold"""
    sys = EnergySystem()

    # Set trl_threshold to negative value
    sys.trl_threshold = Value(-1, DimlessUnit())

    # Should log warning but not raise
    sys._validate_trl_threshold()
    assert sys.trl_threshold == Value(-1, DimlessUnit())


# -------- #
# Interest Rate Validation
# -------- #
def test_interest_rate_def_with_valid_value():
    """Test that _validate_interest_rate_def passes with a valid (non-negative) interest_rate_def"""
    sys = EnergySystem()
    sys.interest_rate_def = Value(0.05, DimlessUnit())

    # Should not raise - validation passes for non-negative interest_rate_def
    sys._validate_interest_rate_def()
    assert sys.interest_rate_def == Value(0.05, DimlessUnit())


def test_interest_rate_def_zero_value():
    """Test that _validate_interest_rate_def passes with zero interest_rate_def"""
    sys = EnergySystem()
    sys.interest_rate_def = Value(0.0, DimlessUnit())

    # Should not raise - zero is valid
    sys._validate_interest_rate_def()
    assert sys.interest_rate_def == Value(0.0, DimlessUnit())


# -------- #
# Num Times Horizon Validation
# -------- #
def test_num_times_horizon_with_valid_value():
    """Test that _validate_num_times_horizon passes with a valid (positive) num_times_horizon"""
    sys = EnergySystem()
    sys.num_times_horizon = 10

    # Should not raise - validation passes for positive num_times_horizon
    sys._validate_num_times_horizon()
    assert sys.num_times_horizon == 10


def test_num_times_horizon_one():
    """Test that _validate_num_times_horizon passes with num_times_horizon = 1"""
    sys = EnergySystem()
    sys.num_times_horizon = 1

    # Should not raise - 1 is the minimum valid value
    sys._validate_num_times_horizon()
    assert sys.num_times_horizon == 1


# -------- #
# Annualize Horizon
# -------- #
def _system_with_horizon(num_horizon_ts: int) -> EnergySystem:
    sys = EnergySystem()
    for i in range(1, num_horizon_ts + 1):
        sys.times.add_id(TimeId(i))
    return sys


def _capture_logs(monkeypatch):
    logged = {"warning": [], "info": []}
    monkeypatch.setattr(
        energy_system_data.logging,
        "log_warning",
        lambda msg, **_: logged["warning"].append(msg),
    )
    monkeypatch.setattr(
        energy_system_data.logging, "log", lambda msg, **_: logged["info"].append(msg)
    )
    return logged


def test_annualize_horizon_defaults_to_false_and_delegates_to_times():
    sys = EnergySystem()
    assert sys.annualize_horizon is False
    assert sys.times.annualize_horizon is False

    # The setting lives in the time data object
    sys.annualize_horizon = True
    assert sys.times.annualize_horizon is True
    sys.times.annualize_horizon = False
    assert sys.annualize_horizon is False


def test_validate_annualize_horizon_warns_when_horizon_is_not_a_year(monkeypatch):
    sys = _system_with_horizon(3)
    logged = _capture_logs(monkeypatch)

    sys._validate_annualize_horizon()

    assert len(logged["warning"]) == 1
    assert "annualize_horizon" in logged["warning"][0]
    assert logged["info"] == []


def test_validate_annualize_horizon_logs_factor_when_switched_on(monkeypatch):
    sys = _system_with_horizon(3)
    sys.annualize_horizon = True
    logged = _capture_logs(monkeypatch)

    sys._validate_annualize_horizon()

    assert logged["warning"] == []
    assert len(logged["info"]) == 1
    assert f"{HOURS_PER_YEAR / 3:.4f}" in logged["info"][0]


def test_validate_annualize_horizon_is_silent_for_a_full_year(monkeypatch):
    sys = _system_with_horizon(int(HOURS_PER_YEAR))
    logged = _capture_logs(monkeypatch)

    sys._validate_annualize_horizon()
    sys.annualize_horizon = True
    sys._validate_annualize_horizon()

    assert logged["warning"] == []
    assert logged["info"] == []


def test_validate_annualize_horizon_is_silent_without_time_ids(monkeypatch):
    sys = EnergySystem()
    logged = _capture_logs(monkeypatch)

    sys._validate_annualize_horizon()

    assert logged["warning"] == []
    assert logged["info"] == []


# -------- #
# Annualized Fill Cost
# -------- #
FILL_PRICE_UNIT = CurrencyUnit.CHF / (PowerUnit.KW * TimeUnit.H)


def _system_with_storage(
    num_horizon_ts: int = 3,
    annualize_horizon: bool = True,
    cyclic: bool = False,
    fill_price: float = 0.1,
) -> EnergySystem:
    sys = _system_with_horizon(num_horizon_ts)
    sys.annualize_horizon = annualize_horizon
    sys.hubs.add_id(HubId("H1"))
    sys.stor_techs.add_id(TechId("XBat"))
    sys.stor_techs.set_cyclic(HubId("H1"), TechId("XBat"), cyclic)
    sys.stor_techs.set_fill_price(
        HubId("H1"), TechId("XBat"), Value(fill_price, FILL_PRICE_UNIT)
    )
    return sys


def test_validate_annualized_fill_cost_warns_for_non_cyclic_storage(monkeypatch):
    sys = _system_with_storage()
    logged = _capture_logs(monkeypatch)

    sys._validate_annualized_fill_cost()

    assert len(logged["warning"]) == 1
    assert "XBat" in logged["warning"][0]
    assert f"{HOURS_PER_YEAR / 3:.4f}" in logged["warning"][0]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"annualize_horizon": False},
        {"num_horizon_ts": int(HOURS_PER_YEAR)},
        {"cyclic": True},
        {"fill_price": 0.0},
    ],
    ids=["not_annualized", "full_year", "cyclic", "free_fill"],
)
def test_validate_annualized_fill_cost_is_silent_otherwise(monkeypatch, kwargs):
    sys = _system_with_storage(**kwargs)
    logged = _capture_logs(monkeypatch)

    sys._validate_annualized_fill_cost()

    assert logged["warning"] == []


# -------- #
# Time Series Property Tests
# -------- #
def test_time_series_property_returns_list():
    """Test that time_series property returns a list"""
    sys = EnergySystem()
    ts = sys.time_series

    # Should return a list (even if empty)
    assert isinstance(ts, list)


def test_time_series_property_aggregates_all_sources():
    """Test that time_series property aggregates from multiple sources"""
    sys = EnergySystem()
    ts = sys.time_series

    # The property concatenates time_series from multiple modules
    # Even with empty modules, it should combine results
    assert isinstance(ts, list)
    # Each element should be a tuple of (kind, stage_id, ids_tuple, time_series)
    for item in ts:
        assert isinstance(item, tuple)
        assert len(item) == 4


# -------- #
# Heuristic Limits Tests
# -------- #
def test_heur_limits_cached_after_first_calculation():
    """Test that heuristic limits are calculated once and cached"""
    sys = EnergySystem()

    # Add minimal ids
    s = StageId("s1")
    h = HubId("h1")
    e = EcId("e1")
    sys.stages.add_id(s)
    sys.hubs.add_id(h)
    sys.ecs.add_id(e)

    # First call should trigger calculation
    assert sys._heur_limits_ready is False

    # This will raise, but should set _heur_limits_ready
    try:
        sys.get_heur_limit_max_in(s, h, e)
    except exceptions.DataException:
        pass

    # Flag should be set after calculation attempt
    assert sys._heur_limits_ready is True


def test_get_heur_limit_max_out_raises_if_no_heuristic_max_set():
    """Test that get_heur_limit_max_out raises without heuristic_max"""
    sys = EnergySystem()

    s = StageId("s1")
    h = HubId("h1")
    e = EcId("e1")
    sys.stages.add_id(s)
    sys.hubs.add_id(h)
    sys.ecs.add_id(e)

    # Should raise DataException
    with pytest.raises(exceptions.DataException) as excinfo:
        sys.get_heur_limit_max_out(s, h, e)
    assert excinfo.value.key == EcExceptionKey.HEURMAX_GET.value


def test_get_heur_limit_max_sum_out_raises_if_no_heuristic_max_set():
    """Test that get_heur_limit_max_sum_out raises without heuristic_max"""
    sys = EnergySystem()

    s = StageId("s1")
    h = HubId("h1")
    e = EcId("e1")
    sys.stages.add_id(s)
    sys.hubs.add_id(h)
    sys.ecs.add_id(e)

    # Should raise DataException
    with pytest.raises(exceptions.DataException) as excinfo:
        sys.get_heur_limit_max_sum_out(s, h, e)
    assert excinfo.value.key == EcExceptionKey.HEURMAX_GET.value


# -------- #
# Setter-only coverage
# -------- #
def test_num_times_horizon_setter():
    """Test the num_times_horizon setter directly"""
    sys = EnergySystem()

    # Setter accepts any value (validation happens in validate method)
    sys.num_times_horizon = 100
    assert sys.num_times_horizon == 100

    sys.num_times_horizon = 1
    assert sys.num_times_horizon == 1
