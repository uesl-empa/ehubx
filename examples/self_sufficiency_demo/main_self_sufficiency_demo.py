# This is a demo example to illustrate the functionality of the self-sufficiency
# module. Is has 3 time steps and two energy carriers which represent two ways
# to import energy into the system. The model serves to demonstrate a trade-off
# between cost and self-sufficiency.
#   a) Electrical energy, considered a cross-import. There is also a demand
#      curve for electrical energy. One way to satisfy this is to import
#      electricity directly which is cheaper than alternative b) since it is
#      available without having to install any technologies
#   b) Solar energy, considered an internal non-energy import. In order to
#      utilize it to to satisfy the electricity demand, a conversion technology
#      needs to be installed which is more expensive than alternative a) but
#      leads to higher self-sufficiency values
import os

from ehubx import EhubX, MultiObjMethod, ObjectiveType, SolverKind
from ehubx.data.self_sufficiency_data import SelfSufficiencyCalculationMethod


if __name__ == "__main__":
    # Create ehubX object
    ehubx = EhubX()
    # Set model path and parse
    ehubx.model_dir_path = os.path.abspath(os.path.dirname(__file__))
    ehubx.parse()
    # Build and solve model with quadratic self-sufficiency calculation method
    ehubx.energy_system.self_sufficiency.calculation_method = (
        SelfSufficiencyCalculationMethod.QUADRATIC
    )
    ehubx.build()
    ehubx.solve_single_obj(
        obj_type=ObjectiveType.SELFSUFFICIENCY,
        solver_kind=SolverKind.GUROBI,
        results_dir_path="results_quad",
    )
    ehubx.solve_double_obj(
        obj_type_1=ObjectiveType.COST,
        obj_type_2=ObjectiveType.SELFSUFFICIENCY,
        method=MultiObjMethod.EPSCONSTRAINT,
        num_pareto_points=10,
        solver_kind=SolverKind.GUROBI,
        results_dir_path="results_quad",
    )
    # Build and solve model with linearized self-sufficiency calculation method
    ehubx.energy_system.self_sufficiency.calculation_method = (
        SelfSufficiencyCalculationMethod.LINEARIZED
    )
    ehubx.build()
    ehubx.solve_single_obj(
        obj_type=ObjectiveType.SELFSUFFICIENCY,
        solver_kind=SolverKind.GUROBI,
        results_dir_path="results_lin",
    )
    ehubx.solve_double_obj(
        obj_type_1=ObjectiveType.COST,
        obj_type_2=ObjectiveType.SELFSUFFICIENCY,
        method=MultiObjMethod.EPSCONSTRAINT,
        num_pareto_points=10,
        solver_kind=SolverKind.GUROBI,
        results_dir_path="results_lin",
    )
