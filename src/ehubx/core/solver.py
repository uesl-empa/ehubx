"""
Solver module. Provides a variety of functionality to choose and customize a
third-party solver.
"""
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Set
from pyomo.core import Model
from pyomo.common.errors import ApplicationError
from pyomo.opt import SolverFactory, SolverManagerFactory, SolverStatus, \
    TerminationCondition
import gurobipy as grb
from ehubx.core import common
from ehubx.core import logging
from ehubx.core import exceptions

# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "solver"
"""Module string for the solver module for logging purposes"""

OPTKEY_LOGFILE: str = "LogFile"
"""Options key for third-party logfile location"""

OPTKEY_LOGTOCONSOLE: str = "LogToConsole"
"""Options key for whether third-party solver should write console logs"""

OPTKEY_MIPGAP: str = "MIPGap"
"""Options key for 'MIPGap' of Gurobi"""

OPTKEY_MIPFOCUS: str = "MIPFocus"
"""Options key for 'MIPFocus' of Gurobi"""

OPTKEY_NORELHEURWORK: str = "NoRelHeurWork"
"""Options key for 'NoRelHeurWork' option of Gurobi"""

OPTKEY_NUMERICFOCUS: str = "NumericFocus"
"""Options key for 'NumericFocus' option of Gurobi"""

OPTKEY_PRESOLVE: str = "Presolve"
"""Options key for 'Presolve' option of Gurobi"""

OPTKEY_SCALEFLAG: str = "ScaleFlag"
"""Options key for 'ScaleFlag' option of Gurobi"""

OPTKEY_SUBMIPCUTS: str = "SubMIPCuts"
"""Options key for 'SubMipCuts' option of Gurobi"""

OPTKEY_THREADS: str = "Threads"
"""Options key for 'Threads' option of Gurobi"""

OPTKEY_TIMELIMIT: str = "TimeLimit"
"""Options key for 'TimeLimit' option of Gurobi"""


class Solver(ABC):
    """
    Abstract class for third-party solvers
    """

    # --------------- #
    # Solving routine #
    # --------------- #
    @abstractmethod
    def solve(self, model: Model) -> Any:
        """
        Solve a pyomo model (abstract method)

        :param model: Pyomo model instance
        :type model: Model
        :return: Pyomo result dictionary
        :rtype: Any
        """
        raise NotImplementedError("Solve not implemented for "
                                  "abstract solver class")

    # ------- #
    # Options #
    # ------- #
    @property
    def options(self) -> Dict[str, Any]:
        """
        Options structure tailoring solver behavior
        """
        return self._options

    # ----------- #
    # Log results #
    # ----------- #
    def log_results(self, results: Any, elapsed_seconds: int) -> None:
        """
        Log information about the status of the optimization results to logfile
        and console

        :param results: Pyomo results dictionary obtained from the solve method
        :type results: Any
        :param elapsed_seconds: Time that was used for the solving routine
        :type elapsed_seconds: int
        """
        # Optimal solution found
        if self.opt_was_found(results):
            logging.log(
                "Optimal solution found. Elapsed time: "
                f"{elapsed_seconds}s", module=LOG_MODULE_STR)
        # Optimal solution not found
        if not self.opt_was_found(results):
            msg = ("Optimal solution not found. Elapsed time: "
                   f"{elapsed_seconds}s. Solver status: "
                   f"{results.solver.status}. ")
            # Termination condition
            msg += "Termination condition: "
            if (results.solver.termination_condition
                    == TerminationCondition.error):
                msg += "Error"
            elif (results.solver.termination_condition
                    == TerminationCondition.feasible):
                msg += "Feasible solution found"
            elif (results.solver.termination_condition
                    == TerminationCondition.infeasible):
                msg += "Problem infeasible"
            elif (results.solver.termination_condition
                    == TerminationCondition.infeasibleOrUnbounded):
                msg += ("Problem infeasible or unbounded")
            elif (results.solver.termination_condition
                    == TerminationCondition.licensingProblems):
                msg += "Licensing issue"
            elif (results.solver.termination_condition
                    == TerminationCondition.internalSolverError):
                msg += "Internal solver error"
            elif (results.solver.termination_condition
                    == TerminationCondition.maxTimeLimit):
                msg += "Time limit reached"
            else:
                msg += f"{results.solver.termination_condition}"
            logging.log_warning(msg, module=LOG_MODULE_STR)

    # ----------- #
    # Postprocess #
    # ----------- #
    @abstractmethod
    def postprocess(self, model: Model, results: Any, **kwargs) -> None:
        """
        Post-solving routines (abstract)

        :param model: Pyomo model instance
        :type model: Model
        :param results: Pyomo results dictionary obtained from the solve method
        :type results: Any
        """
        raise NotImplementedError(("Postprocess not implemented for "
                                   "abstract solver class"))

    # --------------------------- #
    # Check if solution was found #
    # --------------------------- #
    def opt_was_found(self, results: Any) -> bool:
        """
        This method reads the pyomo results dictionary to decide whether an
        optimal solution was found.

        :param results: Pyomo results dictionary returned from the solve method
        :type results: Any
        :return: Whether or not an optimal solution was found
        :rtype: bool
        """
        opt_found = (results.solver.status == SolverStatus.ok)
        opt_found &= (results.solver.termination_condition
                      == TerminationCondition.optimal)
        return opt_found

    # ------------ #
    # Construction #
    # ------------ #
    def __init__(self) -> None:
        self._options: Dict[str, Any] = {}
        self._time_limit_in_seconds: Optional[int] = None


class Gurobi(Solver):
    """
    Class for the third-party Gurobi solver
    """

    # ------------ #
    # Construction #
    # ------------ #
    def __init__(self) -> None:
        super().__init__()
        self._log_file: Optional[str] = None
        self._mip_gap: Optional[float] = None
        self._mip_focus: Optional[int] = None
        self._no_rel_heur_work: Optional[float] = None
        self._numeric_focus: Optional[int] = None
        self._log_to_console: Optional[bool] = None
        self._presolve: Optional[int] = None
        self._scale_flag: Optional[int] = None
        self._sub_mip_cuts: Optional[int] = None
        self._threads: Optional[int] = None
        self._time_limit: Optional[int] = None
        logging.log("Created new Gurobi solver", module=LOG_MODULE_STR)

    # --------------- #
    # Solving routine #
    # --------------- #
    def solve(self, model: Model) -> Any:
        """
        Solve a pyomo model with Gurobi

        :param model: Pyomo model instance
        :type model: Model
        :return: Pyomo result dictionary
        :rtype: Any
        """
        solver_factory = SolverFactory("gurobi", io_format="python")
        for key, value in self.options.items():
            solver_factory.options[key] = value
        solver_manager = SolverManagerFactory("serial")
        try:
            result = solver_manager.solve(model, opt=solver_factory, tee=True)
            return result
        except ApplicationError as exc:
            logging.resume_console_log()
            raise exceptions.EhubXException(
                "Something went during the solving process, either on the "
                "Pyomo side or with the equipped solver itself. Check the "
                "third-party log messages in the console above for more "
                "details", module=LOG_MODULE_STR) from exc

    # -------------- #
    # Option setters #
    # -------------- #
    def set_log_file(self, log_file: str) -> None:
        """
        Set the location of the Gurobi logfile

        :param log_file: Logfile path
        :type log_file: str
        """
        # Parent directory of log_file must exist
        par_dir = os.path.abspath(os.path.join(log_file, os.pardir))
        if not os.path.isdir(par_dir):
            raise exceptions.EhubXException(
                (f"Cannot set Gurobi log file path to {log_file} because "
                 "parent directory does not exist"), module=LOG_MODULE_STR)
        # Set option
        self._options[OPTKEY_LOGFILE] = log_file
        # Logging
        logging.log(f"Set Gurobi logfile to {log_file}", module=LOG_MODULE_STR)

    def set_mip_gap(self, mip_gap: float) -> None:
        """
        Set the 'MIPGap' parameter for the Gurobi solver

        :param mip_gap: Bound for the relative MIP gap abs(z_p - z_d)/abs(z_p)
            (z_p primal bound, z_d dual bound) below which the current solution
            is considered optimal
        :type mip_gap: float
        """
        # mip_gap must not be negative
        if mip_gap < 0:
            raise exceptions.EhubXException(f"{mip_gap} = mip_gap < 0",
                                            module=LOG_MODULE_STR)
        # MIP gap usually not larger than 1
        if mip_gap > 1:
            logging.log_warning(f"{mip_gap} = mip_gap > 1",
                                module=LOG_MODULE_STR)
        # Set option
        self._options[OPTKEY_MIPGAP] = mip_gap
        # Logging
        logging.log("Set MIP gap (objective optimality tolerance) to "
                    f"{mip_gap}",
                    module=LOG_MODULE_STR)

    def set_mip_focus(self, mip_focus: int) -> None:
        """
        Set the 'MIPFocus' parameter for the Gurobi solver

        :param mip_focus: Value for the MIPFocus setting (0: Default balance,
            1: Focus on finding feasible solutions, 2: Focus on proving
            optimality, 3: Focus on improving objective bound)
        :type mip_focus: int
        """
        # mip_focus must be within specific set
        valid_set: Set[int] = {0, 1, 2, 3}
        if mip_focus not in valid_set:
            raise exceptions.EhubXException(
                f"{mip_focus} = mip_focus not in {valid_set}",
                module=LOG_MODULE_STR)
        # Set option
        self._options[OPTKEY_MIPFOCUS] = mip_focus
        # Logging
        msg = f"Set mip_focus to {mip_focus} ("
        if mip_focus == 0:
            msg += "Default balance)"
        if mip_focus == 1:
            msg += "Focus on finding feasible solutions quickly)"
        if mip_focus == 2:
            msg += "Focus on quickly proving optimality)"
        if mip_focus == 3:
            msg += "Focus on quickly improving objective bound)"
        logging.log(msg, module=LOG_MODULE_STR)

    def set_no_rel_heur_work(self, no_rel_heur_work: float) -> None:
        """
        Set the 'NoRelHeurWork' parameter for the Gurobi solver

        :param no_rel_heur_work: Amount of work that Gurobi can spend in the
            NoRel heuristic. Roughly, 1 unit of this parameter corresponds to
            one second but it also highly depends on the machine
        :type no_rel_heur_work: float
        """
        # no_rel_heur_work must be nonnegative
        if no_rel_heur_work < 0:
            raise exceptions.EhubXException(
                f"{no_rel_heur_work} = no_rel_heur_work < 0",
                module=LOG_MODULE_STR)
        # Set option
        self._options[OPTKEY_NORELHEURWORK] = no_rel_heur_work
        # Logging
        logging.log("Set no_rel_heur_work (maximum amount of work spent in "
                    f"the NoRel heuristic) to {no_rel_heur_work}",
                    module=LOG_MODULE_STR)

    def set_numeric_focus(self, numeric_focus: int) -> None:
        """
        Set the 'NumericFocus' parameter for the Gurobi solver

        :param numeric_focus: Value for the NumericFocus setting (0: Default,
            1: Focus on speed over avoiding numerical issues, 2: compromise
            between speed and avoiding numerical issues, focus on avoiding
            numerical issues over speed)
        :type numeric_focus: int
        """
        # numeric_focus must be within specific set
        valid_set: Set[int] = {0, 1, 2, 3}
        if numeric_focus not in valid_set:
            raise exceptions.EhubXException(
                f"{numeric_focus} = numeric_focus not in {valid_set}",
                module=LOG_MODULE_STR)
        # Set option
        self._options[OPTKEY_NUMERICFOCUS] = numeric_focus
        # Logging
        msg = f"Set numeric_focus to {numeric_focus} ("
        if numeric_focus == 0:
            msg += "Default choice)"
        if numeric_focus == 1:
            msg += "Focus on speed over avoiding numerical issues)"
        if numeric_focus == 2:
            msg += "Compromise between speed and avoiding numerical issues)"
        if numeric_focus == 3:
            msg += "Focus on avoiding numerical issues over speed)"
        logging.log(msg, module=LOG_MODULE_STR)

    def set_log_to_console(self, log_to_console: bool) -> None:
        """
        Set the 'LogToConsole' parameter for the Gurobi solver

        :param log_to_console: Whether or not Gurobi should write console
            messages
        :type log_to_console: bool
        """
        self._log_to_console = log_to_console
        # Logging
        msg = f"Set log_to_console to {log_to_console} ("
        if log_to_console:
            msg += "Solver console output enabled)"
        if not log_to_console:
            msg += "Solver console output disabled)"
        self._options[OPTKEY_LOGTOCONSOLE] = log_to_console
        logging.log(msg, module=LOG_MODULE_STR)

    def set_presolve(self, presolve: int) -> None:
        """
        Set the 'Presolve' parameter for the Gurobi solver

        :param presolve: Value for the Presolve setting (-1: Automatic, 0:
            Off, 1: Conservative, 2: Aggressive)
        :type presolve: int
        """
        # presolve must be within specific set
        valid_set: Set[int] = {-1, 0, 1, 2}
        if presolve not in valid_set:
            raise exceptions.EhubXException(
                f"{presolve} = presolve not in {valid_set}",
                module=LOG_MODULE_STR)
        # Set option
        self._options[OPTKEY_PRESOLVE] = presolve
        # Logging
        msg = f"Set presolve to {presolve} ("
        if presolve == -1:
            msg += "Automatic)"
        if presolve == 0:
            msg += "Off)"
        if presolve == 1:
            msg += "Conservative)"
        if presolve == 2:
            msg += "Aggresive)"
        logging.log(msg, module=LOG_MODULE_STR)

    def set_scale_flag(self, scale_flag: int) -> None:
        """
        Set the 'ScaleFlag' parameter for the Gurobi solver

        :param scale_flag: Value for the ScaleFlag setting (-1: Automatic, 0:
            Off, 1: Equilibrium, 2: Multi-pass)
        :type scale_flag: int
        """
        # scale_flag must be within specific set
        valid_set: Set[int] = {-1, 0, 1, 2, 3}
        if scale_flag not in valid_set:
            raise exceptions.EhubXException(
                f"{scale_flag} = scale_flag not in {valid_set}",
                module=LOG_MODULE_STR)
        # Set option
        self._options[OPTKEY_SCALEFLAG] = scale_flag
        # Logging
        msg = f"Set scale_flag to {scale_flag} ("
        if scale_flag == -1:
            msg += "Automatic)"
        if scale_flag == 0:
            msg += "Off)"
        if scale_flag == 1:
            msg += "Equilibrium)"
        if scale_flag == 2:
            msg += "Multi-pass)"
        logging.log(msg, module=LOG_MODULE_STR)

    def set_sub_mip_cuts(self, sub_mip_cuts: int) -> None:
        """
        Set the 'SubMIPCuts' parameter for the Gurobi solver

        :param sub_mip_cuts: Value for the SubMIPCuts setting (-1: Automatic,
            0: Off, 1: Moderate, 2: Aggressive)
        :type sub_mip_cuts: int
        """
        # sub_mip_cuts must be within specific set
        valid_set: Set[int] = {-1, 0, 1, 2}
        if sub_mip_cuts not in valid_set:
            raise exceptions.EhubXException(
                f"{sub_mip_cuts} = sub_mip_cuts not in {valid_set}",
                module=LOG_MODULE_STR)
        # Set option
        self._options[OPTKEY_SUBMIPCUTS] = sub_mip_cuts
        # Logging
        msg = f"Set sub_mip_cuts to {sub_mip_cuts} ("
        if sub_mip_cuts == -1:
            msg += "Automatic)"
        if sub_mip_cuts == 0:
            msg += "Off)"
        if sub_mip_cuts == 1:
            msg += "Moderate)"
        if sub_mip_cuts == 2:
            msg += "Aggressive)"
        logging.log(msg, module=LOG_MODULE_STR)

    def set_threads(self, threads: int) -> None:
        """
        Set the 'Threads' parameter for the Gurobi solver

        :param threads: Value for the number of threads that can be used for
            parallel algorithms
        :type threads: int
        """
        # threads must be nonnegative
        if threads < 0:
            raise exceptions.EhubXException(f"{threads} = threads < 0",
                                            module=LOG_MODULE_STR)
        # threads must not be larger than the number of virtual processors
        cpu_count = os.cpu_count()
        if cpu_count is not None:
            if threads > cpu_count:
                raise exceptions.EhubXException(
                    f"{threads} = threads > cpu_count = {os.cpu_count()}",
                    module=LOG_MODULE_STR)
        # Set option
        self._options[OPTKEY_THREADS] = threads
        # Logging
        logging.log(f"Set threads to {threads}", module=LOG_MODULE_STR)

    def set_time_limit(self, time_limit: int) -> None:
        """
        Set the 'TimeLimit' parameter for the Gurobi solver

        :param time_limit: Maximal time (in seconds) for which Gurobi is
            allowed to solve
        :type time_limit: int
        """
        # time limit must be nonnegative
        if time_limit < 0:
            raise exceptions.EhubXException(f"{time_limit} = time_limit < 0",
                                            module=LOG_MODULE_STR)
        # Set option
        self._options[OPTKEY_TIMELIMIT] = time_limit
        # Logging
        logging.log(f"Set time_limit to {time_limit}", module=LOG_MODULE_STR)

    # ----------- #
    # Postprocess #
    # ----------- #
    def postprocess(self, model: Model, results: Any, **kwargs) -> None:
        """
        Post-solving routine. This computes an IIS for systems that have been
        found to be infeasible.

        :param model: Pyomo model instance
        :type model: Model
        :param results: Pyomo results dictionary obtained from the solve method
        :type results: Any
        :param iis_path: Path to the IIS file that will be created if the
            solved system was found to be infeasible
        :type iis_path: Optional[str]
        """
        iis_path: Optional[str] = None
        for key, value in kwargs.items():
            if key == "iis_path":
                iis_path = value
        if (results.solver.termination_condition
                == TerminationCondition.infeasibleOrUnbounded):
            if iis_path is None:
                logging.log(
                    ("Skipping IIS computation because keyword argument "
                    "'iis_path' was not passed to postprocess routine"))
            if iis_path is not None:
                self._calc_iis(model, iis_path)

    # ----------------------------------- #
    # Irreducible infeasible system (IIS) #
    # ----------------------------------- #
    def _calc_iis(self, model: Model, iis_dir: str) -> None:
        logging.log("Start computing Irreducible infeasible system (IIS)",
                    module=LOG_MODULE_STR)
        # Files and directories
        if not os.path.isdir(os.path.abspath(
                os.path.join(iis_dir, os.pardir))):
            raise exceptions.EhubXException(
                ("Could not calculate iis because parent directory of "
                 f"{iis_dir} does not exist"), module=LOG_MODULE_STR)
        if not os.path.isdir(iis_dir):
            os.mkdir(iis_dir)
            logging.log(f"Created IIS directory at {iis_dir}",
                        module=LOG_MODULE_STR)
        iis_path_ilp = common.get_iterable_filename(os.path.join(iis_dir,
                                                                 "iis.ilp"))
        iis_path_mps = iis_path_ilp.replace(".ilp", ".mps")
        # Writing out infeasible model to .mps
        logging.pause_console_log()
        model.write(iis_path_mps, io_options={"symbolic_solver_labels": True})
        # Reimport as Gurobi model and compute IIS
        grb_model = grb.read(iis_path_mps)  # type: ignore
        grb_model.computeIIS()
        logging.resume_console_log()
        # Remove temporary file and write out IIS system
        os.remove(iis_path_mps)
        logging.log("Finished computing IIS. Writing to file ...",
                    module=LOG_MODULE_STR)
        grb_model.write(iis_path_ilp)
        logging.log(f"IIS written to {iis_path_ilp}",
                    module=LOG_MODULE_STR)


class Glpk(Solver):
    """
    Class for the third-party GLPK solver
    """

    # --------------- #
    # Solving routine #
    # --------------- #
    def solve(self, model: Model) -> Any:
        """
        Solve a pyomo model with GLPK

        :param model: Pyomo model instance
        :type model: Model
        :return: Pyomo result dictionary
        :rtype: Any
        """
        solver_factory = SolverFactory("glpk", io_format="python")
        for key, value in self.options.items():
            solver_factory.options[key] = value
        solver_manager = SolverManagerFactory("serial")
        result = solver_manager.solve(model, opt=solver_factory, tee=True,
                                      timelimit=None)
        return result

    # ----------- #
    # Postprocess #
    # ----------- #
    def postprocess(self, model: Model, results: Any, **kwargs) -> None:
        """
        Post-processing routine. This is empty for the GLPK solver

        :param model: Pyomo model instance
        :type model: Model
        :param results: Pyomo results dictionary obtained from the solve method
        :type results: Any
        """

    # ------------ #
    # Construction #
    # ------------ #
    def __init__(self):
        super().__init__()
        logging.log("Created new GLPK solver", module=LOG_MODULE_STR)
