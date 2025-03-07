import os

from ehubx import EhubX, ObjectiveType, RomMethod, RomSettings, SolverKind


if __name__ == "__main__":
    # Create ehubX object and set path
    ehubx = EhubX()
    # Set model path and parse
    ehubx.model_dir_path = os.path.abspath(os.path.dirname(__file__))
    ehubx.parse()
    # Perform reduced-order modeling
    ehubx.rom(rom_settings=RomSettings(method=RomMethod.CLUSTER_TSAM, num_ts_target=5))
    # Build the reduced-order model and solve
    ehubx.build()
    ehubx.solve_single_obj(
        obj_type=ObjectiveType.COST,
        solver_kind=SolverKind.GUROBI,
        opt_vars_filename="results_rom",
        model_lp_path="model_rom.lp",
    )
    # Build the full-order model and solve
    ehubx.build(use_rom=False)
    ehubx.solve_single_obj(
        obj_type=ObjectiveType.COST,
        solver_kind=SolverKind.GUROBI,
        opt_vars_filename="results_full",
        model_lp_path="model_full.lp",
    )
