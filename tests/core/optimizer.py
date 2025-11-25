import os
from datetime import datetime
from typing import Any, List, Optional

import numpy as np
from pyomo.core import Constraint, Model, Objective, Var

from ehubx.core import exceptions, logging
from ehubx.core.common import (
    EPS_PARETOZEROCHECK_ABS,
    EPS_PARETOZEROCHECK_REL,
    EPS_WEIGHTEDSUM,
    ObjectiveType,
)
from ehubx.core.solver import Solver
from ehubx.data.pareto_front_data import ParetoFront, ParetoId
from ehubx.model.energy_system_model import (
    OBJ_SYSTEMCOST,
    VAR_SYSTEMCO2TOTAL,
    VAR_SYSTEMCOST,
    VAR_SYSTEMSELFSUFFICIENCY,
)
from ehubx.model.self_sufficiency_model import VAR_SELFSUFFICIENCY
from ehubx.writer.opt_vars_writer import save_opt_vars_to_csv


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "opt"
"""String identifying the optimizer module for logging purposes"""


# ------------------------------ #
# Solve single-objective problem #
# ------------------------------ #
def solve_single_obj(
    model: Model,
    solver: Solver,
    results_dir_path: str,
    opt_vars_filename: Optional[str],
) -> Any:
    # Actual solving process
    logging.log("Starting single-objective solve ...", module=LOG_MODULE_STR)
    logging.pause_console_log()
    start = datetime.now()
    results = solver.solve(model)
    elapsed_seconds = int((datetime.now() - start).total_seconds())
    logging.resume_console_log()
    solver.log_results(results, elapsed_seconds)
    # Postprocess and write out results
    iis_path: Optional[str] = None
    if results_dir_path:
        iis_path = os.path.join(results_dir_path, "iis")
    solver.postprocess(model, results, iis_path=iis_path)
    if solver.opt_was_found(results) and opt_vars_filename:
        results_path = os.path.join(results_dir_path, opt_vars_filename)
        save_opt_vars_to_csv(model, results_path)
    # Return results
    return results


# ------------------- #
# Weighted-sum method #
# ------------------- #
def weighted_sum_method(
    model: Model,
    solver: Solver,
    obj_type_1: ObjectiveType,
    obj_type_2: ObjectiveType,
    num_pareto_points: int,
    mo_results_dir_path: Optional[str] = None,
) -> ParetoFront:
    # Check mo_result_path
    if mo_results_dir_path is not None:
        if not os.path.isdir(mo_results_dir_path):
            raise exceptions.EhubXException(
                f"Results subdirectory path {mo_results_dir_path} does not exist",
                module=LOG_MODULE_STR,
            )
    # num_pareto_points must be positive
    if num_pareto_points < 1:
        raise exceptions.EhubXException(
            f"num_pareto_points={num_pareto_points} < 1", module=LOG_MODULE_STR
        )
    # Log
    logging.log(
        "Starting weighted-sum method to calculate a Pareto "
        f"front with {num_pareto_points} points ...",
        module=LOG_MODULE_STR,
    )
    # Initialize Pareto front
    pareto_front = ParetoFront()
    pareto_front.obj_key_1 = obj_type_1.value
    pareto_front.obj_key_2 = obj_type_2.value
    # Compute equidistant weights between almost-0 and almost-1
    weights = np.linspace(EPS_WEIGHTEDSUM, 1 - EPS_WEIGHTEDSUM, num=num_pareto_points)
    # Iterate over weights
    for cnt, weight in enumerate(weights):
        logging.log(
            f"Entering weighted sum iteration {cnt + 1} / {num_pareto_points} ...",
            module=LOG_MODULE_STR,
        )
        # Set objective and solve weighted-sum subproblem
        _set_weighted_objective(model, obj_type_1, obj_type_2, 1 - weight, weight)
        logging.log(
            "Computing weighted-sum subproblem, pausing console log ...",
            module=LOG_MODULE_STR,
        )
        logging.pause_console_log(write_console_entry=False)
        start = datetime.now()
        results = solver.solve(model)
        elapsed_seconds = int((datetime.now() - start).total_seconds())
        logging.resume_console_log()
        solver.log_results(results, elapsed_seconds)
        # Postprocess and write out results
        iis_path: Optional[str] = None
        if mo_results_dir_path:
            iis_path = os.path.join(mo_results_dir_path, "iis")
        solver.postprocess(model, results, iis_path=iis_path)
        # Subproblem solved
        if solver.opt_was_found(results):
            # Write out solution
            if mo_results_dir_path:
                ws_results_file_path = os.path.join(
                    mo_results_dir_path, f"ws_results_{cnt + 1}"
                )
                if cnt == 0:
                    ws_results_file_path += f"_{obj_type_1.value}"
                if cnt == num_pareto_points - 1:
                    ws_results_file_path += f"_{obj_type_2.value}"
                ws_results_file_path += ".csv"
                save_opt_vars_to_csv(model, ws_results_file_path)
            # Get Pareto point coordinates
            obj_val_1 = _get_objective_value(model, obj_type_1)
            obj_val_2 = _get_objective_value(model, obj_type_2)
            pareto_front.set_point(ParetoId(cnt + 1), obj_val_1, obj_val_2)
            logging.log(
                (
                    f"Successfully calculated Pareto point {cnt + 1} "
                    f"/ {num_pareto_points}: "
                    f"{obj_type_1.value} = {obj_val_1}, "
                    f"{obj_type_2.value} = {obj_val_2}"
                ),
                module=LOG_MODULE_STR,
            )
        # Subproblem not solved
        if not solver.opt_was_found(results):
            logging.log_warning(
                (
                    f"Failed to solve weighted-sum subproblem {cnt + 1} / "
                    f"{num_pareto_points}. Aborting weighted-sum method ..."
                ),
                module=LOG_MODULE_STR,
            )
            return pareto_front
        # Log end of iteration
        logging.log(
            (f"Finished weighted sum iteration {cnt + 1} / {num_pareto_points}"),
            module=LOG_MODULE_STR,
        )
    # Return
    logging.log("Finished weighted-sum method", module=LOG_MODULE_STR)
    return pareto_front


def _set_weighted_objective(
    model: Model,
    obj_type_1: ObjectiveType,
    obj_type_2: ObjectiveType,
    weight_1: float,
    weight_2: float,
) -> Objective:
    if model is None:
        raise exceptions.EhubXException(
            "Tried to set weighted objective without having built a model",
            module=LOG_MODULE_STR,
        )
    # Same objective occurs twice
    if obj_type_1 == obj_type_2:
        logging.log_warning(
            (
                "While setting a weighted objective, the objective "
                f"{obj_type_1.value} was used for both cost dimensions"
            ),
            module=LOG_MODULE_STR,
        )
    # Deactivate existing objective functions
    for o in model.component_map(Objective):
        model.find_component(o).deactivate()
    # Prepare variables that will be used in the weighted sum objective
    var_1: Optional[Var] = None
    var_2: Optional[Var] = None
    sub_str: List[str] = [""] * 2
    # Cost minimization
    if obj_type_1 == ObjectiveType.COST:
        var_1 = getattr(model, VAR_SYSTEMCOST)
        sub_str[0] = f"Cost minimization (weight = {weight_1})"
    if obj_type_2 == ObjectiveType.COST:
        var_2 = getattr(model, VAR_SYSTEMCOST)
        sub_str[1] = f"Cost minimization (weight = {weight_2})"
    # CO2 minimization
    if obj_type_1 == ObjectiveType.CO2:
        var_1 = getattr(model, VAR_SYSTEMCO2TOTAL)
        sub_str[0] = f"CO2 minimization (weight = {weight_1})"
    if obj_type_2 == ObjectiveType.CO2:
        var_2 = getattr(model, VAR_SYSTEMCO2TOTAL)
        sub_str[1] = f"CO2 minimization (weight = {weight_2})"
    # Self-sufficiency maximization
    if obj_type_1 == ObjectiveType.SELFSUFFICIENCY:
        if VAR_SELFSUFFICIENCY not in model.component_map(Var):
            msg_err = (
                "Cannot use the self-sufficiency objective function while "
                "the self-sufficiency submodule is deactivated."
            )
            raise exceptions.EhubXException(msg_err, module=LOG_MODULE_STR)
        var_1 = getattr(model, VAR_SYSTEMSELFSUFFICIENCY)
        sub_str[0] = f"Self-sufficiency maximization (weight = {weight_1})"
        weight_1 *= -1
    if obj_type_2 == ObjectiveType.SELFSUFFICIENCY:
        if VAR_SELFSUFFICIENCY not in model.component_map(Var):
            msg_err = (
                "Cannot use the self-sufficiency objective function while "
                "the self-sufficiency submodule is deactivated."
            )
            raise exceptions.EhubXException(msg_err, module=LOG_MODULE_STR)
        var_2 = getattr(model, VAR_SYSTEMSELFSUFFICIENCY)
        sub_str[1] = f"Self-sufficiency maximization (weight = {weight_2})"
        weight_2 *= -1
    assert var_1 is not None
    assert var_2 is not None
    # Logging
    msg = f"Setting weighted objective: {sub_str[0]} + {sub_str[1]}"
    logging.log(msg, module=LOG_MODULE_STR)
    # Defining, setting and activating the objective
    obj_name = f"O_Ws_{obj_type_1.value}_{obj_type_2.value}"
    obj = Objective(expr=(weight_1 * var_1 + weight_2 * var_2))
    if model.find_component(obj_name) is not None:
        model.del_component(obj_name)
    model.add_component(obj_name, obj)
    obj.activate()
    return obj


# --------------------------- #
# Objective getter and setter #
# --------------------------- #
def _get_objective_value(model: Model, obj_type: ObjectiveType) -> float:
    obj_value: Optional[float] = None
    if obj_type == ObjectiveType.COST:
        obj_value = getattr(model, VAR_SYSTEMCOST).value
    if obj_type == ObjectiveType.CO2:
        obj_value = getattr(model, VAR_SYSTEMCO2TOTAL).value
    if obj_type == ObjectiveType.SELFSUFFICIENCY:
        obj_value = getattr(model, VAR_SYSTEMSELFSUFFICIENCY).value
    assert obj_value is not None
    return obj_value


# ---------------- #
# Objective setter #
# ---------------- #
def set_objective(model: Model, objective_type: ObjectiveType) -> None:
    msg = "Setting objective function: "
    # Deactivate all objectives
    for o in model.component_map(Objective):
        model.find_component(o).deactivate()
    obj: Optional[Objective] = None
    # Cost minimization
    if objective_type == ObjectiveType.COST:
        getattr(model, OBJ_SYSTEMCOST).activate()
        msg += "Cost minimization"
    # CO2 minimization (include small amount of cost minimization as well
    # since it often improves the chance of finding unique solutions, e.g.;
    # for V_LoadShiftingAbove and V_LoadShiftingBelow)
    if objective_type == ObjectiveType.CO2:
        var_cost = getattr(model, VAR_SYSTEMCOST)
        var_co2 = getattr(model, VAR_SYSTEMCO2TOTAL)
        obj = Objective(expr=(var_co2 + EPS_WEIGHTEDSUM * var_cost))
        obj_name = "O_SystemCo2Weak"
        if model.find_component(obj_name) is not None:
            model.del_component(obj_name)
        model.add_component(obj_name, obj)
        obj.activate()
        msg += "CO2 minimization"
    # Self-sufficiency maximization (include small amount of cost minimization as
    # well since it often improves the chance of finding unique solutions,
    # e.g.; for V_LoadShiftingAbove and V_LoadShiftingBelow)
    if objective_type == ObjectiveType.SELFSUFFICIENCY:
        # Self-sufficiency module is not included
        if VAR_SYSTEMSELFSUFFICIENCY not in model.component_map(Var):
            msg_err = (
                "Cannot set the self-sufficiency objective function while "
                "the self-sufficiency submodule is deactivated."
            )
            raise exceptions.EhubXException(msg_err, module=LOG_MODULE_STR)

        var_cost = getattr(model, VAR_SYSTEMCOST)
        var_self_sufficiency = getattr(model, VAR_SYSTEMSELFSUFFICIENCY)
        obj = Objective(expr=(-var_self_sufficiency + EPS_WEIGHTEDSUM * var_cost))
        obj_name = "O_SystemSelfSufficiencyWeak"
        if model.find_component(obj_name) is not None:
            model.del_component(obj_name)
        model.add_component(obj_name, obj)
        obj.activate()
        msg += "Self-sufficiency maximization"
    logging.log(msg, module=LOG_MODULE_STR)


# --------------------- #
# eps-constraint method #
# --------------------- #
def eps_constraint_method(
    model: Model,
    solver: Solver,
    obj_type_1: ObjectiveType,
    obj_type_2: ObjectiveType,
    num_pareto_points: int,
    mo_results_dir_path: Optional[str] = None,
) -> ParetoFront:
    # Check mo_result_path
    if mo_results_dir_path:
        if not os.path.isdir(mo_results_dir_path):
            raise exceptions.EhubXException(
                f"Results subdirectory path {mo_results_dir_path} does not exist",
                module=LOG_MODULE_STR,
            )
    # num_pareto_points must be larger than one
    if num_pareto_points <= 1:
        raise exceptions.EhubXException(
            f"num_pareto_points={num_pareto_points} < 2", module=LOG_MODULE_STR
        )
    # IIS path
    iis_path: Optional[str] = None
    if mo_results_dir_path:
        iis_path = os.path.join(mo_results_dir_path, "iis")
    # Log
    logging.log(
        "Starting eps-constraint method to calculate a Pareto "
        f"front with {num_pareto_points} points ...",
        module=LOG_MODULE_STR,
    )
    # Initialize Pareto points
    pareto_front = ParetoFront()
    pareto_front.obj_key_1 = obj_type_1.value
    pareto_front.obj_key_2 = obj_type_2.value
    # Compute first and last Pareto points by weighted-sum method
    init_weights = [EPS_WEIGHTEDSUM, 1 - EPS_WEIGHTEDSUM]
    for cnt, weight in enumerate(init_weights):
        logging.log(
            f"Entering eps-constraint initial phase {cnt + 1} / 2",
            module=LOG_MODULE_STR,
        )
        # Set objective and solve weighted-sum subproblem
        weighted_obj = _set_weighted_objective(
            model, obj_type_1, obj_type_2, 1 - weight, weight
        )
        logging.log(
            "Computing weighted-sum subproblem, pausing console log ...",
            module=LOG_MODULE_STR,
        )
        logging.pause_console_log(write_console_entry=False)
        start = datetime.now()
        results = solver.solve(model)
        elapsed_seconds = int((datetime.now() - start).total_seconds())
        logging.resume_console_log()
        solver.log_results(results, elapsed_seconds)
        # Postprocess and write out results
        solver.postprocess(model, results, iis_path=iis_path)
        # Subproblem solved
        if solver.opt_was_found(results):
            # Write out solution
            if mo_results_dir_path:
                csv_file_path: str = ""
                if cnt == 0:
                    csv_file_path += os.path.join(
                        mo_results_dir_path, f"epscon_results_1_{obj_type_1.value}"
                    )
                if cnt == 1:
                    csv_file_path += os.path.join(
                        mo_results_dir_path,
                        f"epscon_results_{num_pareto_points}_{obj_type_2.value}",
                    )
                csv_file_path += ".csv"
                save_opt_vars_to_csv(model, csv_file_path)
            # Get Pareto point coordinates
            obj_val_1 = _get_objective_value(model, obj_type_1)
            obj_val_2 = _get_objective_value(model, obj_type_2)
            pareto_id_int = 1 if cnt == 0 else num_pareto_points
            pareto_front.set_point(ParetoId(pareto_id_int), obj_val_1, obj_val_2)
            logging.log(
                (
                    f"Successfully calculated initial-phase Pareto "
                    f"point {cnt + 1} / 2: "
                    f"{obj_type_1.value} = {obj_val_1}, "
                    f"{obj_type_2.value} = {obj_val_2}"
                ),
                module=LOG_MODULE_STR,
            )
        # Subproblem not solved
        if not solver.opt_was_found(results):
            logging.log_warning(
                (
                    f"Failed to solve eps-constraint initial phase {cnt + 1} "
                    f"/ 2. Aborting eps-constraint method ..."
                ),
                module=LOG_MODULE_STR,
            )
            return pareto_front
        # Log end of iteration
        logging.log(
            f"Finished eps-constraint initial phase {cnt + 1} / 2",
            module=LOG_MODULE_STR,
        )

    # Enter eps-constraint main phase
    logging.log("Starting eps-constraint main phase ...", module=LOG_MODULE_STR)
    weighted_obj.deactivate()
    set_objective(model, obj_type_1)
    # Check that initial Pareto points are actually distinct:
    obj2_init = []
    for pareto_id in pareto_front.ids:
        (_, obj2) = pareto_front.get_point(pareto_id)
        obj2_init.append(obj2)
    eps_rel = EPS_PARETOZEROCHECK_REL
    eps_abs = EPS_PARETOZEROCHECK_ABS
    if abs(obj2_init[0] - obj2_init[1]) < (
        eps_rel * max(abs(obj2_init[0]), abs(obj2_init[1])) + eps_abs
    ):
        logging.log_warning(
            (
                "Initial phase of eps-constraint method produced nearly "
                f"identical values in the second objective: "
                f"{obj_type_2.value}_1 = {obj2_init[0]}, "
                f"{obj_type_2.value}_2 = {obj2_init[1]}. "
                "Aborting eps-constraint method ..."
            ),
            module=LOG_MODULE_STR,
        )
        return pareto_front
    # Calculate threshold values for the 2nd objective
    obj2_thresholds = np.linspace(obj2_init[0], obj2_init[1], num=num_pareto_points)
    # Iterate over main iterations
    for cnt, threshold in enumerate(obj2_thresholds):
        if cnt == 0 or cnt == num_pareto_points - 1:
            continue
        logging.log(
            (f"Entering eps-constraint main phase {cnt} / {num_pareto_points - 2}"),
            module=LOG_MODULE_STR,
        )
        # Set threshold constraint
        _set_threshold_constraint(model, obj_type_2, threshold)
        logging.log(
            "Computing eps-constraint main phase, pausing console log ...",
            module=LOG_MODULE_STR,
        )
        logging.pause_console_log(write_console_entry=False)
        start = datetime.now()
        results = solver.solve(model)
        elapsed_seconds = int((datetime.now() - start).total_seconds())
        logging.resume_console_log()
        solver.log_results(results, elapsed_seconds)
        # Postprocess and write out results
        solver.postprocess(model, results, iis_path=iis_path)
        # Subproblem solved
        if solver.opt_was_found(results):
            # Write out solution
            if mo_results_dir_path:
                csv_file_path = os.path.join(
                    mo_results_dir_path, f"epscon_results_{cnt + 1}.csv"
                )
                save_opt_vars_to_csv(model, csv_file_path, add_time_to_filename=False)
            # Get Pareto point coordinates
            obj_val_1 = _get_objective_value(model, obj_type_1)
            obj_val_2 = _get_objective_value(model, obj_type_2)
            pareto_front.set_point(ParetoId(cnt + 1), obj_val_1, obj_val_2)
            logging.log(
                (
                    f"Successfully calculated main-phase Pareto "
                    f"point {cnt} / {num_pareto_points - 2}: "
                    f"{obj_type_1.value} = {obj_val_1}, "
                    f"{obj_type_2.value} = {obj_val_2}"
                ),
                module=LOG_MODULE_STR,
            )
        # Subproblem not solved
        if not solver.opt_was_found(results):
            logging.log_warning(
                (
                    f"Failed to solve eps-constraint main phase {cnt} "
                    f"/ {num_pareto_points - 2}. Aborting eps-constraint "
                    "method ..."
                ),
                module=LOG_MODULE_STR,
            )
            return pareto_front
        # Log end of iteration
        logging.log(
            (f"Finished eps-constraint main phase {cnt} / {num_pareto_points - 2}"),
            module=LOG_MODULE_STR,
        )

    # Return Pareto points
    logging.log("Finished eps-constraint method", module=LOG_MODULE_STR)
    return pareto_front


# --------------------------- #
# Threshold constraint setter #
# --------------------------- #
def _set_threshold_constraint(
    model: Model, obj_type: ObjectiveType, threshold: float
) -> None:
    sub_str: Optional[str] = None
    obj_var: Optional[Var] = None
    is_upper_threshold: bool = True
    # Cost minimization
    if obj_type == ObjectiveType.COST:
        obj_var = getattr(model, VAR_SYSTEMCOST)
        sub_str = f"Cost maximum (threshold = {threshold})"
    # CO2 minimization
    if obj_type == ObjectiveType.CO2:
        obj_var = getattr(model, VAR_SYSTEMCO2TOTAL)
        sub_str = f"CO2 maximum (threshold = {threshold})"
    # Self-sufficiency maximization
    if obj_type == ObjectiveType.SELFSUFFICIENCY:
        if VAR_SYSTEMSELFSUFFICIENCY not in model.component_map(Var):
            msg_err = (
                "Cannot use the self-sufficiency objective function while "
                "the self-sufficiency submodule is deactivated."
            )
            raise exceptions.EhubXException(msg_err, module=LOG_MODULE_STR)
        obj_var = getattr(model, VAR_SYSTEMSELFSUFFICIENCY)
        is_upper_threshold = False
        sub_str = f"Self-sufficiency minimum (threshold = {threshold})"
    assert obj_var is not None
    # Logging
    msg = f"Setting threshold constraint: {sub_str}"
    logging.log(msg, module=LOG_MODULE_STR)
    # Defining and settingthe constraint
    con_name = f"C_EpsCon_{obj_type.value}"
    if is_upper_threshold:
        con = Constraint(expr=(obj_var <= threshold))
    else:
        con = Constraint(expr=(obj_var >= threshold))
    if model.find_component(con_name) is not None:
        model.del_component(con_name)
    model.add_component(con_name, con)
