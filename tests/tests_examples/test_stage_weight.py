"""Tests for the stage_weight parameter, which weights the contribution of
each stage to the cost objective. The model in 'model_stage_weight' has two
stages that share one technology fleet but differ in their fuel price, so
which technology is optimal depends on which stage the objective counts.
"""

import os

import pytest
from pyomo.core import value

from ehubx import EhubX, Glpk, ObjectiveType
from ehubx.data.stage_data import StageId
from ehubx.model import (
    conv_tech_model,
    energy_system_model,
    export_model,
    import_model,
    load_shedding_model,
    load_shifting_model,
    network_model,
    stor_tech_model,
    tech_model,
)
from ..util import (
    DIRNAME_EXAMPLES,
    DIRNAME_TMPTESTMODEL,
    init_tmp_model,
)


DIRNAME_STAGEWEIGHTMODEL: str = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "model_stage_weight"
)
"""Directory of the two-stage model used to test the stage weights"""

# Per-stage cost variables of all submodules that contribute to the system
# cost, paired with the sign with which they enter it
PER_STAGE_COST_VARS = [
    (tech_model.VAR_TECHCOSTPERSTAGE, 1),
    (conv_tech_model.VAR_CONVTECHCOSTPERSTAGE, 1),
    (stor_tech_model.VAR_STORTECHCOSTPERSTAGE, 1),
    (import_model.VAR_IMPCOSTPERSTAGE, 1),
    (export_model.VAR_EXPPROFITPERSTAGE, -1),
    (load_shedding_model.VAR_LOADSHEDDINGCOSTPERSTAGE, 1),
    (load_shifting_model.VAR_LOADSHIFTINGCOSTPERSTAGE, 1),
    (network_model.VAR_NETTECHCOSTPERSTAGE, 1),
    (energy_system_model.VAR_SYSTEMCOSTCO2PENALTYPERSTAGE, 1),
]


def _solve_stage_weight_model(stage_weights=None):
    """Build and solve the two-stage test model with the given stage weights"""
    init_tmp_model(DIRNAME_STAGEWEIGHTMODEL)
    ehubx = EhubX()
    ehubx.model_dir_path = DIRNAME_TMPTESTMODEL
    ehubx.parse()
    # Stage weights have to be set before the model is built, because the
    # constraint rules evaluate them at construction time
    if stage_weights is not None:
        for stage_id_str, stage_weight in stage_weights.items():
            ehubx.energy_system.stages.set_stage_weight(
                StageId(stage_id_str), stage_weight
            )
    ehubx.build()
    ehubx.set_solver(Glpk())
    ehubx.solve_single_obj(obj_type=ObjectiveType.COST)
    return ehubx._model


def _cost_per_stage(model, s: str) -> float:
    return value(getattr(model, energy_system_model.VAR_SYSTEMCOSTPERSTAGE)[s])


def _tech_cap(model, x: str) -> float:
    return value(getattr(model, tech_model.VAR_TECHCAP)["S1", "H1", x])


def test_stage_weight_default_is_average_not_sum():
    # By default every stage has weight 1, which makes the system cost the
    # plain average over the stages. Summing the stages instead would make the
    # cost depend on how many stages a model happens to have
    model = _solve_stage_weight_model()

    cost_s1 = _cost_per_stage(model, "S1")
    cost_s2 = _cost_per_stage(model, "S2")
    system_cost = value(getattr(model, energy_system_model.VAR_SYSTEMCOST))

    assert system_cost == pytest.approx((cost_s1 + cost_s2) / 2)
    assert system_cost != pytest.approx(cost_s1 + cost_s2)


def test_stage_weight_is_scale_invariant():
    # Only the ratios of the stage weights matter, not their magnitude
    model_default = _solve_stage_weight_model()
    system_cost_default = value(
        getattr(model_default, energy_system_model.VAR_SYSTEMCOST)
    )

    model_scaled = _solve_stage_weight_model({"S1": 3, "S2": 3})
    system_cost_scaled = value(
        getattr(model_scaled, energy_system_model.VAR_SYSTEMCOST)
    )

    assert system_cost_scaled == pytest.approx(system_cost_default)


def test_stage_weight_zero_excludes_stage_from_objective():
    # A stage weighted 0 does not contribute to the objective at all
    model = _solve_stage_weight_model({"S1": 1, "S2": 0})

    system_cost = value(getattr(model, energy_system_model.VAR_SYSTEMCOST))

    assert system_cost == pytest.approx(_cost_per_stage(model, "S1"))


def test_stage_weight_zero_still_enforces_constraints_of_that_stage():
    # The costs of a stage weighted 0 are ignored, but its demands still have
    # to be met, which is the entire point of the parameter
    model = _solve_stage_weight_model({"S1": 1, "S2": 0})

    # The zero-weight stage keeps incurring real (unweighted) costs ...
    assert _cost_per_stage(model, "S2") > 0
    # ... because it still has to import fuel to serve its demand
    imp_cost_s2 = value(getattr(model, import_model.VAR_IMPCOSTPERSTAGE)["S2"])
    assert imp_cost_s2 > 0


def test_stage_weight_flips_optimal_design():
    # Fuel is cheap in S1 and expensive in S2. Weighting S1 alone makes the
    # cheap, inefficient technology optimal; weighting S2 alone makes the
    # expensive, efficient one optimal
    model_s1 = _solve_stage_weight_model({"S1": 1, "S2": 0})
    assert _tech_cap(model_s1, "XCheap") > 0
    assert _tech_cap(model_s1, "XEff") == pytest.approx(0)

    model_s2 = _solve_stage_weight_model({"S1": 0, "S2": 1})
    assert _tech_cap(model_s2, "XEff") > 0
    assert _tech_cap(model_s2, "XCheap") == pytest.approx(0)


def test_system_cost_per_stage_sums_up_the_submodules():
    # Every submodule's per-stage cost has to end up in the system cost of
    # that stage, so that no cost can silently escape the objective
    model = _solve_stage_weight_model()

    for s in getattr(model, "S_Stage"):
        submodule_costs = sum(
            sign * value(getattr(model, var_name)[s])
            for var_name, sign in PER_STAGE_COST_VARS
        )
        assert _cost_per_stage(model, s) == pytest.approx(submodule_costs)


def test_single_stage_cost_is_unaffected_by_stage_weights():
    # With only one stage, the weighted average is that stage's cost, whatever
    # the weight is. This keeps single-stage models exactly as they were
    example_model_dir = os.path.join(DIRNAME_EXAMPLES, "small_demo")
    init_tmp_model(example_model_dir)
    ehubx = EhubX()
    ehubx.model_dir_path = DIRNAME_TMPTESTMODEL
    ehubx.parse()
    ehubx.energy_system.stages.set_stage_weight(StageId("S1"), 0.25)
    ehubx.build()
    ehubx.set_solver(Glpk())
    ehubx.solve_single_obj(obj_type=ObjectiveType.COST)
    model = ehubx._model

    system_cost = value(getattr(model, energy_system_model.VAR_SYSTEMCOST))

    assert system_cost == pytest.approx(_cost_per_stage(model, "S1"))
    assert system_cost == pytest.approx(5602.6977288754)
