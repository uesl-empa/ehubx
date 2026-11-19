import pyomo.environ as pe
import pytest
from pyomo.opt import TerminationCondition

from ehubx import EhubX, Highs, SolverKind
from ehubx.core.ehubx import SOLVER_KIND_TO_TYPE, SOLVER_TYPE_TO_KIND


def _toy_milp(demand: float) -> pe.ConcreteModel:
    """min x + 5y  s.t.  x <= 10y,  x >= demand,  y binary.
    Optimum for demand <= 10: x = demand, y = 1. Infeasible for demand > 10."""
    m = pe.ConcreteModel()
    m.x = pe.Var(domain=pe.NonNegativeReals)
    m.y = pe.Var(domain=pe.Binary)
    m.cap = pe.Constraint(expr=m.x <= 10 * m.y)
    m.dem = pe.Constraint(expr=m.x >= demand)
    m.obj = pe.Objective(expr=m.x + 5 * m.y, sense=pe.minimize)
    return m


def test_highs_feasible_loads_solution():
    model = _toy_milp(demand=3)
    solver = Highs()
    results = solver.solve(model)
    assert solver.opt_was_found(results)
    assert pe.value(model.x) == pytest.approx(3)
    assert pe.value(model.y) == pytest.approx(1)


def test_highs_infeasible_returns_results_instead_of_raising():
    """Pyomo's HiGHS interface raises when no solution can be loaded. Highs
    must return the results instead, so ehubX can log the model as infeasible
    like with the other solvers"""
    model = _toy_milp(demand=20)
    solver = Highs()
    results = solver.solve(model)
    assert not solver.opt_was_found(results)
    assert results.solver.termination_condition == TerminationCondition.infeasible
    assert model.x.value is None


@pytest.mark.parametrize("solver_kind", list(SolverKind))
def test_solver_kind_and_type_tables_match(solver_kind):
    solver_type = SOLVER_KIND_TO_TYPE[solver_kind]
    assert SOLVER_TYPE_TO_KIND[solver_type] is solver_kind
    ehubx = EhubX()
    ehubx.create_solver(solver_kind)
    assert type(ehubx.solver) is solver_type


def test_set_solver_highs():
    ehubx = EhubX()
    solver = Highs()
    ehubx.set_solver(solver)
    assert ehubx.solver is solver
