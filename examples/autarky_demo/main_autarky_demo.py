# This is a demo example to illustrate the functionality of the autarky
# module. Is has 3 time steps and two energy carriers which represent two ways
# to import energy into the system. The model serves to demonstrate a trade-off
# between cost and autarky.
#   a) Electrical energy, considered a cross-import. There is also a demand
#      curve for electrical energy. One way to satisfy this is to import
#      electricity directly which is cheaper than alternative b) since it is
#      available without having to install any technologies
#   b) Solar energy, considered an internal non-energy import. In order to
#      utilize it to to satisfy the electricity demand, a conversion technology
#      needs to be installed which is more expensive than alternative a) but
#      leads to higher autarky values
import os

from ehubx import EhubX, MultiObjMethod, ObjectiveType, SolverKind
from ehubx.data.autarky_data import AutarkyCalculationMethod


if __name__ == "__main__":
    # Create ehubX object
    ehubx = EhubX()
    # Set model path and parse
    ehubx.model_dir_path = os.path.abspath(os.path.dirname(__file__))
    ehubx.parse()
    # Build and solve model with quadratic autarky calculation method
    ehubx.energy_system.autarky.calculation_method = AutarkyCalculationMethod.QUADRATIC
    ehubx.build()
    ehubx.solve_single_obj(
        obj_type=ObjectiveType.AUTARKY,
        solver_kind=SolverKind.GUROBI,
        results_dir_path="results_quad",
    )
    ehubx.solve_double_obj(
        obj_type_1=ObjectiveType.COST,
        obj_type_2=ObjectiveType.AUTARKY,
        method=MultiObjMethod.EPSCONSTRAINT,
        num_pareto_points=10,
        solver_kind=SolverKind.GUROBI,
        results_dir_path="results_quad",
    )
    # Build and solve model with linearized autarky calculation method
    ehubx.energy_system.autarky.calculation_method = AutarkyCalculationMethod.LINEARIZED
    ehubx.build()
    ehubx.solve_single_obj(
        obj_type=ObjectiveType.AUTARKY,
        solver_kind=SolverKind.GUROBI,
        results_dir_path="results_lin",
    )
    ehubx.solve_double_obj(
        obj_type_1=ObjectiveType.COST,
        obj_type_2=ObjectiveType.AUTARKY,
        method=MultiObjMethod.EPSCONSTRAINT,
        num_pareto_points=10,
        solver_kind=SolverKind.GUROBI,
        results_dir_path="results_lin",
    )
