import os

from ehubx import EhubX, MultiObjMethod, ObjectiveType, SolverKind

if __name__ == "__main__":
    ehubx = EhubX()
    ehubx.model_dir_path = os.path.abspath(os.path.dirname(__file__))
    ehubx.parse()

    ehubx.build()
    ehubx.solve_single_obj(
        obj_type=ObjectiveType.AUTONOMY,
        solver_kind=SolverKind.GUROBI,
        results_dir_path="results_autonomy",
    )
    ehubx.solve_double_obj(
        obj_type_1=ObjectiveType.AUTONOMY,
        obj_type_2=ObjectiveType.COST,
        num_pareto_points=10,
        results_dir_path="results_autonomy_pareto",
    )
