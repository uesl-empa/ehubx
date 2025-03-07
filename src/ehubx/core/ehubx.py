"""
ehubX module. Contains top-level UI functionality
"""

import os
from datetime import datetime
from typing import Callable, Dict, Optional

from pyomo import environ  # noqa: F401
from pyomo.core import Model

from ehubx.core import exceptions, logging, optimizer, rom
from ehubx.core.common import MultiObjMethod, ObjectiveType, SolverKind
from ehubx.core.solver import Glpk, Gurobi, Solver
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.pareto_front_data import ParetoFront
from ehubx.model import energy_system_model
from ehubx.parser import energy_system_parser
from ehubx.writer import energy_system_writer
from ehubx.writer.common_writer import FileGranularity, create_dir
from ehubx.writer.pareto_writer import save_pareto_front


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "ehubx"
"""String identifying the ehubX module for logging purposes"""

DIRNAME_IIS: str = "iis"
"""Name for Irreducible Infeasible Subsystems (IIS) in the results
subdirectory"""

DIRNAME_INPUTS: str = "inputs"
"""Name of the inputs subdirectory in the model directory"""

DIRNAME_RESULTS: str = "results"
"""Name of the results subdirectory in the model directory"""

DIRNAME_RUN: str = "run"
"""Name of the run subdirectory in the results subdirectory"""

DIRNAME_ROM: str = "rom"
"""Name of the reduced-order modeling subdirectory in the model directory"""

FILENAME_LP: str = "model.lp"
"""Default name of LP file containing the energy system model"""

FILENAME_OPTVARS_SINGLEOBJ: str = "opt_vars.csv"
"""Default name of CSV file holding all optimization variables"""


# Dictionary translating from solver kind to type
SOLVER_KIND_TO_TYPE: Dict[SolverKind, type] = {
    SolverKind.GUROBI: Gurobi,
    SolverKind.GLPK: Glpk,
}

# Dictionary translating from type to solver kind
SOLVER_TYPE_TO_KIND: Dict[type, SolverKind] = {
    Gurobi: SolverKind.GUROBI,
    Glpk: SolverKind.GLPK,
}


class EhubX:
    """
    Application class used for user interactions with the ehubX platform. Holds
    the energy system model and the solver, along with methods that perform
    streamlined workflows for typical user interactions
    """

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._model_dir_path: Optional[str] = None
        self._energy_system: EnergySystem = EnergySystem()
        self._energy_system_rom: Optional[EnergySystem] = None
        self._model_built_from_rom: Optional[bool] = None
        self._model: Optional[Model] = None
        self._solver: Optional[Solver] = None

    # ------------- #
    # Energy system #
    # ------------- #
    @property
    def energy_system(self) -> EnergySystem:
        """
        Energy system

        :return: Current energy system instance
        :rtype: EnergySystem
        """
        return self._energy_system

    @property
    def energy_system_rom(self) -> Optional[EnergySystem]:
        """
        Reduced-order energy system

        :return: Current reduced-order energy system instance
        :rtype: Optional[EnergySystem]
        """
        return self._energy_system_rom

    # ----- #
    # Paths #
    # ----- #
    @property
    def model_dir_path(self) -> str:
        """Current model directory, or empty string if it is not set"""
        return self._model_dir_path if self._model_dir_path else ""

    @model_dir_path.setter
    def model_dir_path(self, model_dir_path: str) -> None:
        # Catch nonexistent directory
        if not os.path.isdir(model_dir_path):
            raise exceptions.EhubXException(
                f"Cannot set model directory to {model_dir_path}: Directory "
                "does not exist"
            )
        # Set the path
        logging.set_logfile_path(os.path.join(model_dir_path, "ehubX.log"))
        self._model_dir_path = model_dir_path
        logging.log(f"Model path set to {model_dir_path}", module=LOG_MODULE_STR)

    @property
    def lp_file_path(self) -> str:
        """Current path to model LP file, or empty string if model directory
        is not set"""
        if not self._model_dir_path:
            return ""
        return os.path.join(self._model_dir_path, FILENAME_LP)

    @property
    def inputs_dir_path(self) -> str:
        """Path to inputs subdirectory, or empty string if model directory is
        not set"""
        if not self._model_dir_path:
            return ""
        return os.path.join(self._model_dir_path, DIRNAME_INPUTS)

    @property
    def rom_dir_path(self) -> str:
        """Path to ROM subdirectory, or empty string if model directory is not
        set"""
        if not self._model_dir_path:
            return ""
        return os.path.join(self._model_dir_path, DIRNAME_ROM)

    # ------ #
    # Solver #
    # ------ #
    @property
    def solver(self) -> Optional[Solver]:
        """
        Third-party optimization solver

        :return: Current instance (if any) of the solver class used for solving
            the optimization model.
        :rtype: Optional[Solver]
        """
        return self._solver

    def set_solver(self, solver: Optional[Solver]) -> None:
        """
        Set the third-party optimization solver. Setting None is possible to
        remove the currently set solver.

        :param solver: Instance of the solver class to be used from now on
        :type solver: Optional[Solver]
        """
        if solver is None:
            logging.log("Externally set ehubX solver to None", module=LOG_MODULE_STR)
        if solver is not None:
            logging.log(
                (f"Externally set a {SOLVER_TYPE_TO_KIND[type(solver)].value} solver"),
                module=LOG_MODULE_STR,
            )
        self._solver = solver

    def create_solver(self, solver_kind: SolverKind) -> None:
        """
        Create a third-party optimization solver (with default options) and
        set it as the currently employed solver.

        :param solver_kind: Solver kind to be used
        :type solver_kind: SolverKind
        """
        if solver_kind == SolverKind.GUROBI:
            self._solver = Gurobi()
        if solver_kind == SolverKind.GLPK:
            self._solver = Glpk()

    # ------ #
    # Parser #
    # ------ #
    def parse(self) -> None:
        """
        Parse the inputs subdirectory and create the energy system data from
        these files
        """
        self._energy_system = energy_system_parser.parse(self.inputs_dir_path)

    # ---------------------- #
    # Reduced-order modeling #
    # ---------------------- #
    def rom(
        self,
        rom_settings: rom.RomSettings = rom.RomSettings(),
        write_rom: bool = True,
        add_time_to_dir: bool = False,
    ) -> None:
        """
        Perform reduced-order modeling on the energy system data. A reduced-
        order model is calculated based on the provided settings. Specifically,
        the 'method' argument will determine what kind of ROM strategy will
        be employed.

        :param rom_settings: Settings for reduced-order modeling, defaults to
                             rom.RomSettings()
        :type rom_settings: rom.RomSettings, optional
        :param write_rom: Whether to write details of the ROM procedure to
                          the ROM subdirectory, defaults to True
        :type write_rom: bool, optional
        :param add_time_to_dir: Whether a timestamp will be added to the
            ROM directory name, defaults to False
        :type add_time_to_dir: bool
        """
        # Create subdirectory for ROM
        sys_rom = rom.rom(
            self.energy_system,
            rom_settings,
            write_rom=write_rom,
            rom_dir_path=self.rom_dir_path,
            add_time_to_dir=add_time_to_dir,
        )
        if sys_rom is not None:
            self._energy_system_rom = sys_rom

    def delete_rom(self) -> None:
        """Delete the reduced-order energy system model (if it exists)"""
        if not self.energy_system_rom:
            msg = (
                "Tried to undo reduced-order modeling when no reduced "
                "energy system model exists. Skipping ..."
            )
            logging.log_warning(msg, module=LOG_MODULE_STR)
        self._energy_system_rom = None

    # ------- #
    # Builder #
    # ------- #
    def build(self, use_rom: bool = True) -> None:
        """
        Build the energy system model from the current state of the energy
        system data.

        :param prefer_rom: If this input is set to True and a reduced-order
                           system exists, that is used to build the model.
                           Otherwise, the full-order system will be used
        :type prefer_rom: bool, optional
        """
        energy_system: EnergySystem = self.energy_system
        self._model_built_from_rom = False
        if use_rom and self.energy_system_rom is not None:
            energy_system = self.energy_system_rom
            self._model_built_from_rom = True
        energy_system.validate()
        self._model = energy_system_model.build(energy_system)

    # ------------------- #
    # Model modifications #
    # ------------------- #
    def modify_model(self, modify: Callable[[Model], None]):
        """
        Interface method used to modify the energy system model after it has
        been built.

        :param modify: Modifying function. This should take a Pyomo model
            object as only input and contain the desired modifications
        :type modify: Callable[[Model], None]
        """
        modify(self._model)

    # ------------------------------ #
    # Solve single-objective problem #
    # ------------------------------ #
    def solve_single_obj(
        self,
        obj_type: ObjectiveType = ObjectiveType.COST,
        solver_kind: SolverKind = SolverKind.GUROBI,
        write_model: bool = True,
        model_lp_path: Optional[str] = None,
        opt_vars_filename: Optional[str] = FILENAME_OPTVARS_SINGLEOBJ,
        file_granularity: FileGranularity = FileGranularity.DEFAULT,
        results_dir_path: str = "results",
    ) -> None:
        """
        Bundled method to perform single-objective optimization on the built
        energy system model. This routines sets an objective function,
        optionally writes an LP file of the model, creates a solver if none is
        set, solves the model and writes out the results to a CSV file.

        :param obj_type: Type of objective function that will be
            optimized, defaults to ObjectiveType.COST
        :type obj_type: ObjectiveType, optional
        :param solver_kind: Kind of third-party solver that will be used if no
            solver instance has been set, defaults to SolverKind.GUROBI
        :type solver_kind: SolverKind, optional
        :param write_model: Whether to write an LP file with the model,
            defaults to True
        :type write_model: bool, optional
        :param model_lp_path: path that the lp file of the model will be
            written to, relative to the model directory, defaults to None
        :type model_lp_path: Optional[str], optional
        :param opt_vars_filename: Name of the csv file that will be written to
            the results subdirectory with all optimization variables, defaults
            to "opt_vars.csv"
        :type opt_vars_filename: Optional[str], optional
        :param file_granularity: Setting that controls how much the output
            should be split across different files, defaults to
            FileGranularity.DEFAULT
        :type file_granularity: FileGranularity
        :param results_dir_path: Path of the results directory relative to
            the model directory, defaults to "results"
        :type results_dir_path: str
        """
        # Check that model is not None
        model: Optional[Model] = self._model
        if model is None:
            raise exceptions.EhubXException(
                "Tried to solve single-objective problem but no model exists",
                module=LOG_MODULE_STR,
            )
        # Select objective and write model to file
        optimizer.set_objective(model, obj_type)
        if write_model:
            self.write_lp(lp_file_path=model_lp_path)
        # Create new solver if necessary
        if self.solver is None:
            self.create_solver(solver_kind)
        solver: Solver = self.solver  # type: ignore
        # Set directory where results should be placed
        results_dir_path = os.path.join(self.model_dir_path, results_dir_path)
        if not create_dir(results_dir_path, dir_desc="results"):
            logging.log_warning(
                f"Failed to create results directory at {results_dir_path}. "
                "Stopping double-objective solving procedure ...",
                module=LOG_MODULE_STR,
            )
            return
        # Pass to optimization methods
        optimizer.solve_single_obj(
            model, solver, results_dir_path, opt_vars_filename=opt_vars_filename
        )
        # Write results
        energy_system = self._energy_system
        if self._model_built_from_rom:
            assert self._energy_system_rom is not None
            energy_system = self._energy_system_rom
        energy_system_writer.write_all(
            energy_system,
            self._model,
            results_dir_path,
            file_granularity=file_granularity,
        )

    # ------------------------------------------ #
    # Bundled double-objective solving procedure #
    # ------------------------------------------ #
    def solve_double_obj(
        self,
        obj_type_1: ObjectiveType = ObjectiveType.COST,
        obj_type_2: ObjectiveType = ObjectiveType.CO2,
        method: MultiObjMethod = MultiObjMethod.EPSCONSTRAINT,
        num_pareto_points: int = 4,
        solver_kind: SolverKind = SolverKind.GUROBI,
        write_model: bool = True,
        results_dir_path: str = "results",
    ) -> None:
        """
        Bundled method to perform double-objective (bicriterial) optimization
        on the built energy system model. This routines sets two objective
        functions that will be optimized for and performs a multiobjective
        strategy to approximate the Pareto front to a desired granularity. In
        the results subdirectory, one folder is created for the double-
        objective problem. Within that folder, an additional subdirectory is
        created for every scalarization method that is used in the
        multiobjective algorithm. Results of the Pareto front approximation are
        placed in the top folder. Additionally, CSV result files and
        (optionally) model LP files of the scalarizations are placed in the
        respective subdirectories.

        :param obj_type_1: Type of first objective function to be optimized,
            defaults to ObjectiveType.COST
        :type obj_type_1: ObjectiveType, optional
        :param obj_type_2: Type of second objective function to be optimized,
            defaults to ObjectiveType.CO2
        :type obj_type_2: ObjectiveType, optional
        :param method: Multiobjective optimization method that is used to
            approximately compute the Pareto front, defaults to MultiObjMethod.
            EPSCONSTRAINT
        :type method: MultiObjMethod, optional
        :param num_pareto_points: Number of Pareto points that should be
            computed, defaults to 4
        :type num_pareto_points: int, optional
        :param solver_kind: Kind of third-party solver that will be used if no
            solver instance has been set, defaults to SolverKind.GUROBI
        :type solver_kind: SolverKind, optional
        :param write_model: Whether to write an LP file for every
            scalarization, defaults to True
        :type write_model: bool, optional
        :param results_dir_path: Path of the results directory relative to
            the model directory, defaults to "results"
        :type results_dir_path: str
        """
        # Check that model is not None
        model: Optional[Model] = self._model
        if model is None:
            raise exceptions.EhubXException(
                "Tried to solve single-objective problem but no model exists",
                module=LOG_MODULE_STR,
            )
        # Make sure cost functions are distinct
        if obj_type_1 == obj_type_2:
            raise exceptions.EhubXException(
                (
                    f"Identical objective type {obj_type_1} for both "
                    "objective functions in double-objective solver"
                ),
                module=LOG_MODULE_STR,
            )
        # Create subdirectory for results
        results_dir_path = os.path.join(self.model_dir_path, results_dir_path)
        mo_results_dir_path = os.path.join(results_dir_path, "mo_results")
        if not create_dir(mo_results_dir_path, dir_desc="multiobjective results"):
            logging.log(
                "Failed to create multiobjective results directory at "
                f"{mo_results_dir_path}. Stopping double-objective solving "
                "procedure ...",
                module=LOG_MODULE_STR,
            )
            return
        # Select first objective and write model to file once
        optimizer.set_objective(model, obj_type_1)
        if write_model:
            self.write_lp(
                lp_file_path=os.path.join(
                    mo_results_dir_path, f"model_obj_{obj_type_1.value}.lp"
                )
            )
        # Create new solver if necessary
        if self._solver is None:
            self.create_solver(solver_kind)
        solver: Solver = self._solver  # type: ignore
        # Pass to multiobjective optimizer
        logging.log(
            (
                "Starting to solve a double-objective optimization "
                f"problem with objectives ({obj_type_1.value}, "
                f"{obj_type_2.value}) ..."
            ),
            module=LOG_MODULE_STR,
        )
        pareto_front: ParetoFront = ParetoFront()
        if method == MultiObjMethod.WEIGHTEDSUM:
            pareto_front = optimizer.weighted_sum_method(
                model,
                solver,
                obj_type_1,
                obj_type_2,
                num_pareto_points,
                mo_results_dir_path,
            )
        if method == MultiObjMethod.EPSCONSTRAINT:
            pareto_front = optimizer.eps_constraint_method(
                model,
                solver,
                obj_type_1,
                obj_type_2,
                num_pareto_points,
                mo_results_dir_path,
            )
        # Outputs
        save_pareto_front(pareto_front, mo_results_dir_path)

    # ------------ #
    # Model writer #
    # ------------ #
    def write_lp(self, lp_file_path: Optional[str] = None) -> None:
        """
        Writes an LP file of the current optimization model.

        :param lp_file_path: Path where the LP file will be placed relative to
            the model directory, defaults to None
        :type lp_file_path: Optional[str], optional
        """
        if self._model is None:
            raise exceptions.EhubXException(("Cannot write LP file: No model exists"))
        if lp_file_path is not None:
            lp_file_path = os.path.join(self.model_dir_path, lp_file_path)
        if lp_file_path is None:
            lp_file_path = self.lp_file_path
        logging.log(
            f"Start writing model to LP file: {lp_file_path}", module=LOG_MODULE_STR
        )
        start = datetime.now()
        self._model.write(lp_file_path, io_options={"symbolic_solver_labels": True})
        elapsed_seconds = int((datetime.now() - start).total_seconds())
        logging.log(
            f"Finished model writing. Elapsed time: {elapsed_seconds}s",
            module=LOG_MODULE_STR,
        )
