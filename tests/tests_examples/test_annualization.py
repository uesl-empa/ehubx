"""End-to-end tests for the annualize_horizon setting.

The fixture model_annualization spans two identical days (48 hourly time
steps) with annualize_horizon set in its stages.yaml. Hub H1 has a demand
profile with a daily peak supplied by a fuel-fired conversion tech and a
battery, hub H2 has an annual demand_sum supplied by direct imports.
"""

import os

import pytest
from pyomo.core import value

from ehubx import EhubX, Glpk, ObjectiveType, RomMethod, RomSettings
from ehubx.core.common import HOURS_PER_YEAR
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId
from ehubx.data.tech_data import TechId
from ehubx.data.unit import CurrencyUnit, PowerUnit, TimeUnit
from ehubx.data.value import Value
from ehubx.model import (
    conv_tech_model,
    demand_model,
    energy_system_model,
    import_model,
    stor_tech_model,
    tech_model,
)
from ehubx.writer import energy_system_writer

from ..util import DIRNAME_TMPTESTMODEL, init_tmp_model

DIRNAME_ANNUALIZATIONMODEL: str = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "model_annualization")
)

NUM_TS: int = 48
"""Number of horizon time steps in the fixture"""

FACTOR: float = HOURS_PER_YEAR / NUM_TS
"""Annualization factor of the fixture"""

S1 = StageId("S1")
H1 = HubId("H1")
XBAT = TechId("XBat")

FILL_PRICE: float = 0.01
"""Fill price of the battery in the non-cyclic tests [CHF/kWh]"""


def _solve(annualize_horizon=None, cut_to=None, fill_price=None) -> EhubX:
    """Parse, optionally override the setting, make the battery non-cyclic
    with the given fill price or cut the horizon, build and solve the fixture
    with GLPK"""
    init_tmp_model(DIRNAME_ANNUALIZATIONMODEL)
    ehubx = EhubX()
    ehubx.model_dir_path = DIRNAME_TMPTESTMODEL
    ehubx.parse()
    if annualize_horizon is not None:
        ehubx.energy_system.annualize_horizon = annualize_horizon
    if fill_price is not None:
        # Start full, so that the initial energy (and thus the fill) is not 0
        stor_techs = ehubx.energy_system.stor_techs
        stor_techs.set_cyclic(H1, XBAT, False)
        stor_techs.set_soc_init(H1, XBAT, Value(1))
        stor_techs.set_fill_price(
            H1, XBAT, Value(fill_price, CurrencyUnit.CHF / (PowerUnit.KW * TimeUnit.H))
        )
    if cut_to is not None:
        ehubx.rom(
            rom_settings=RomSettings(method=RomMethod.CUT_TIME, num_ts_target=cut_to),
            write_rom=False,
        )
    ehubx.build()
    ehubx.set_solver(Glpk())
    ehubx.solve_single_obj(obj_type=ObjectiveType.COST, write_model=False)
    return ehubx


def _system(ehubx: EhubX):
    """The energy system the model was built from"""
    return ehubx.energy_system_rom or ehubx.energy_system


def _raw_import_cost(ehubx: EhubX) -> float:
    """Import cost summed over the modelled time steps with weight 1"""
    system = _system(ehubx)
    var_imp = getattr(ehubx._model, import_model.VAR_IMP)
    cost = 0.0
    for s, h, e in system.imports.tuples:
        price = system.imports.get_price(s, h, e)
        for t in system.times.ids:
            cost += price.get_value(t).to_float() * value(
                var_imp[s.key, h.key, e.key, t.key_as_int]
            )
    return cost


def _weighted_sum(ehubx: EhubX, var, *index) -> float:
    """Sum of a time-indexed variable weighted by the time step weights"""
    system = _system(ehubx)
    return sum(
        system.times.get_weight(S1, t) * value(var[(*index, t.key_as_int)])
        for t in system.times.ids
    )


def test_operating_costs_are_scaled_to_a_year():
    ehubx = _solve()
    model = ehubx._model

    imp_cost_total = value(getattr(model, import_model.VAR_IMPCOSTTOTAL))
    assert imp_cost_total == pytest.approx(FACTOR * _raw_import_cost(ehubx))

    # Two identical days: the annual cost is 365 times the cost of one day
    day_cost = _raw_import_cost(ehubx) / 2
    assert imp_cost_total == pytest.approx(365 * day_cost)

    # Capacity costs are annual by construction and add up unscaled
    system_cost = value(getattr(model, energy_system_model.VAR_SYSTEMCOST))
    tech_cost_total = value(getattr(model, tech_model.VAR_TECHCOSTTOTAL))
    assert system_cost == pytest.approx(tech_cost_total + imp_cost_total)


def test_switched_off_reproduces_the_legacy_behaviour():
    ehubx = _solve(annualize_horizon=False)
    model = ehubx._model

    assert _system(ehubx).times.annualization_factor == 1.0
    imp_cost_total = value(getattr(model, import_model.VAR_IMPCOSTTOTAL))
    assert imp_cost_total == pytest.approx(_raw_import_cost(ehubx))


def test_cut_horizon_matches_native_short_horizon():
    # Day 2 repeats day 1, so cutting the horizon to one day and annualizing
    # it must give the same annual cost as the two-day horizon
    full = _solve()
    cut = _solve(cut_to=24)

    assert _system(cut).times.num_horizon_ts == 24
    assert _system(cut).times.annualization_factor == pytest.approx(HOURS_PER_YEAR / 24)
    cost_full = value(getattr(full._model, energy_system_model.VAR_SYSTEMCOST))
    cost_cut = value(getattr(cut._model, energy_system_model.VAR_SYSTEMCOST))
    assert cost_cut == pytest.approx(cost_full, rel=1e-6)


def test_big_m_values_follow_the_annualized_weights():
    # The 'tech used' constraints bound the weighted flow sum by a big-M value
    # built from the installed capacity. Before the fix that value was
    # capacity times the horizon length, which the annualized flow sum exceeds
    # by far; the model has to remain feasible with the tech in use
    ehubx = _solve()
    model = ehubx._model
    var_cap = getattr(model, tech_model.VAR_TECHCAP)
    var_used = getattr(model, tech_model.VAR_YTECHUSED)

    cap_conv = value(var_cap["S1", "H1", "XConv"])
    out_conv = _weighted_sum(
        ehubx,
        getattr(model, conv_tech_model.VAR_CONVTECHOUT),
        "S1",
        "H1",
        "XConv",
        "E0",
    )
    assert value(var_used["S1", "H1", "XConv"]) == pytest.approx(1)
    assert out_conv > cap_conv * NUM_TS

    cap_bat = value(var_cap["S1", "H1", "XBat"])
    flow_bat = _weighted_sum(
        ehubx, getattr(model, stor_tech_model.VAR_STORTECHINFLOW), "S1", "H1", "XBat"
    ) + _weighted_sum(
        ehubx, getattr(model, stor_tech_model.VAR_STORTECHOUTFLOW), "S1", "H1", "XBat"
    )
    assert cap_bat > 0
    assert value(var_used["S1", "H1", "XBat"]) == pytest.approx(1)
    assert flow_bat > 2 * cap_bat * NUM_TS


def test_demand_sum_is_an_annual_demand():
    ehubx = _solve()
    var_supply = getattr(ehubx._model, demand_model.VAR_DEMANDSUPPLY)

    supply_horizon = sum(
        value(var_supply["S1", "H2", "E0", t]) for t in range(1, NUM_TS + 1)
    )
    assert supply_horizon == pytest.approx(87600 * NUM_TS / HOURS_PER_YEAR)
    assert _weighted_sum(ehubx, var_supply, "S1", "H2", "E0") == pytest.approx(87600)


def test_setting_and_hours_represented_are_written_to_the_results():
    _solve()
    system_csv = os.path.join(
        DIRNAME_TMPTESTMODEL, "results", energy_system_writer.FILENAME_SYSTEM + ".csv"
    )
    with open(system_csv, encoding="utf8") as file:
        rows = [line.split(",") for line in file.read().splitlines()]

    entries = {row[0]: row[1] for row in rows}
    assert entries[energy_system_writer.ENTRY_ANNUALIZEHORIZON] == "True"
    assert entries[energy_system_writer.ENTRY_NUMTIMESHORIZON] == str(NUM_TS)
    assert float(entries[energy_system_writer.ENTRY_HOURSREPRESENTED]) == HOURS_PER_YEAR


def test_clustering_and_annualization_coexist():
    # TSAM sets the cluster sizes, which sum up to the horizon length; the
    # annualization factor scales them so that they sum up to a year
    init_tmp_model(DIRNAME_ANNUALIZATIONMODEL)
    ehubx = EhubX()
    ehubx.model_dir_path = DIRNAME_TMPTESTMODEL
    ehubx.parse()
    ehubx.rom(
        rom_settings=RomSettings(method=RomMethod.CLUSTER_TSAM, num_ts_target=6),
        write_rom=False,
    )
    rom = ehubx.energy_system_rom
    assert rom is not None
    assert rom.times.is_clustered
    assert rom.annualize_horizon is True
    assert rom.times.annualization_factor == pytest.approx(FACTOR)

    raw_weights = [rom.times._weight[S1, t] for t in rom.times.ids]
    assert sum(raw_weights) == NUM_TS
    assert rom.times.get_weight_sum(S1) == pytest.approx(HOURS_PER_YEAR)

    # The reduced model builds with the scaled weights
    ehubx.build()
    assert ehubx._model is not None


def _fill_cost_and_initial_energy(ehubx: EhubX):
    """Fill cost and initial energy of the battery in stage S1"""
    model = ehubx._model
    var_fill_cost = getattr(model, stor_tech_model.VAR_STORTECHFILLCOST)
    var_energy = getattr(model, stor_tech_model.VAR_STORTECHENERGY)
    fill_cost = value(var_fill_cost["S1", "H1", "XBat"])
    energy_init = value(var_energy["S1", "H1", "XBat", 1])
    return fill_cost, energy_init


def test_fill_cost_is_paid_once_per_repetition_of_the_horizon():
    # The annualized horizon repeats FACTOR times a year, and a non-cyclic
    # storage has to be refilled at the start of every repetition
    ehubx = _solve(annualize_horizon=True, fill_price=FILL_PRICE)
    assert _system(ehubx).times.annualization_factor == pytest.approx(FACTOR)
    fill_cost, energy_init = _fill_cost_and_initial_energy(ehubx)

    assert energy_init > 0
    assert fill_cost == pytest.approx(FACTOR * energy_init * FILL_PRICE)
    fill_cost_total = value(
        getattr(ehubx._model, stor_tech_model.VAR_STORTECHFILLCOSTTOTAL)
    )
    assert fill_cost_total == pytest.approx(fill_cost)


def test_fill_cost_is_paid_once_when_switched_off():
    ehubx = _solve(annualize_horizon=False, fill_price=FILL_PRICE)
    assert _system(ehubx).times.annualization_factor == 1.0
    fill_cost, energy_init = _fill_cost_and_initial_energy(ehubx)

    assert energy_init > 0
    assert fill_cost == pytest.approx(energy_init * FILL_PRICE)
