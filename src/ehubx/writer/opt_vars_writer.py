"""Optimization variable writer module. Contains functions to save the
optimization variables to csv"""

import os
from datetime import datetime
from typing import List, Optional

import pandas as pd
from pyomo.core import Model, Set, Var

from ehubx.core import exceptions, logging


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "writ/opt_vars"
"""Module string for the optimization variable writer module for logging
purposes"""

COL_VARNAME: str = "var_name"
"""Name of variable name column in the single-objective results csv file"""

COL_VARVALUE: str = "var_value"
"""Name of variable value column in the single-objective results csv file"""


def save_opt_vars_to_csv(
    model: Model,
    output_path: str,
    only_non_zero_results: bool = True,
    add_time_to_filename: bool = False,
) -> Optional[str]:
    """
    Writes all variables found in the model with their values to a csv file.
    The set-names of the sets used for the index of a variable are used as
    column names (set to NaN for variables not having that Set in the index)..

    :param model: Solved pyomo model
    :type model: Model
    :param output_path: Nominal path of the results csv file
    :type output_path: str
    :param only_non_zero_results: Whether only nonzero variable values should
        be written to the results file, defaults to True
    :type only_non_zero_results: bool, optional
    :param add_time_to_filename: Whether a timestamp will be added to the
        result filename, defaults to False
    :type add_time_to_filename: bool, optional
    :return: The output path of the csv file
    :rtype: Optional[str]
    """
    if not os.path.isdir(os.path.abspath(os.path.join(output_path, os.pardir))):
        raise exceptions.EhubXException(
            (
                "Parent directory of optimization variable csv output path "
                f"{output_path} does not exist"
            ),
            module=LOG_MODULE_STR,
        )
    if not output_path.endswith(".csv"):
        output_path += ".csv"
    if add_time_to_filename:
        output_path = output_path.replace(".csv", "")
        output_path += f"_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.csv"
    if os.path.exists(output_path):
        logging.pause_console_log(write_console_entry=False)
        query_str = (
            "Singleobjective optimization variable file "
            f"{output_path} already exists. Overwrite? [y/n]: "
        )
        answer = ""
        while answer not in {"y", "n"}:
            answer = input(query_str)
        logging.resume_console_log(write_console_entry=False)
        if answer == "n":
            logging.log(
                "User decision: Do not overwrite existing "
                f"optimization variable file {output_path}",
                module=LOG_MODULE_STR,
            )
            return None
        logging.log(
            f"User decision: Overwrite existing results file {output_path}",
            module=LOG_MODULE_STR,
        )
        while os.path.exists(output_path):
            try:
                os.remove(output_path)
            except PermissionError:
                logging.pause_console_log(write_console_entry=False)
                input(
                    "Failed to remove existing optimization variable file "
                    f"{output_path}. Maybe the file is open in another "
                    "program? Press any key to try again ..."
                )
                logging.resume_console_log(write_console_entry=False)
    all_vars = _vars_to_dataframe(model, only_non_zero_results)
    logging.log(
        f"Writing optimization variables to {output_path} ...", module=LOG_MODULE_STR
    )
    all_vars.to_csv(output_path)
    logging.log("Finished writing optimization variables", module=LOG_MODULE_STR)
    return output_path


def _vars_to_dataframe(model: Model, only_non_zero_results: bool) -> pd.DataFrame:
    model_vars = []
    for var in model.component_objects(Var, active=True):
        # Grab variable object
        var_obj = getattr(model, str(var))
        # Variables without indices
        if var_obj.index_set().dimen == 0:
            model_vars.append({COL_VARNAME: var_obj.name, COL_VARVALUE: var_obj.value})
            continue
        # Variables with indices - Get set components
        idx_names = _extract_set_components(var_obj.index_set())
        vars_v = []
        # Variable has one-dimensional index set
        if len(idx_names) == 1:
            vars_v = [
                {
                    COL_VARNAME: var_obj.name,
                    COL_VARVALUE: val.value,
                    **dict(zip(idx_names, [idx_vals])),
                }
                for idx_vals, val in var_obj.items()
            ]
        # Variable has multi-dimensional index set
        if len(idx_names) > 1:
            vars_v = [
                {
                    COL_VARNAME: var_obj.name,
                    COL_VARVALUE: val.value,
                    **dict(zip(idx_names, idx_vals)),
                }
                for idx_vals, val in var_obj.items()
            ]
        model_vars += vars_v
    # Define dataframe and filter nonzero results
    df = pd.DataFrame(model_vars).set_index(COL_VARNAME)
    if only_non_zero_results:
        return df[df[COL_VARVALUE] != 0]
    # Return
    return df


def _extract_set_components(pyomo_set: Set) -> List[str]:
    # It is necessary to manually specify the "within" domains of our multi-
    # dimensional subsets since Pyomo does not track this information during
    # model definition. Therefore, we collect these setnames here
    def flatten_set_names(name):
        if name in (
            "S_TechTuple",
            "S_SolarTechTuple",
            "S_WindTechTuple",
            "S_StorTechTuple",
            "S_EbmTechTuple",
            "S_HpTechTuple",
            "S_AtesTechTuple",
        ):
            return ["S_Stage", "S_Hub", "S_Tech"]
        elif name in (
            "S_ConvTechIn",
            "S_ConvTechOut",
            "S_HpTechIn",
            "S_HpTechOut",
            "S_AtesTechIn",
            "S_AtesTechOut",
        ):
            return ["S_Stage", "S_Hub", "S_Tech", "S_Ec"]
        elif name == "S_EBMTechAndEC":
            return ["S_EBMTech", "EC"]
        elif name == "S_EBMDefSetAndEC":
            return ["Stage", "Hub", "S_StorTech", "EC"]
        elif name in (
            "S_ImpTuple",
            "S_ExpTuple",
            "S_DemandTuple",
            "S_LoadSheddingTuple",
            "S_LoadShiftingTuple",
            "S_LoadShiftingTupleFix",
        ):
            return ["S_Stage", "S_Hub", "S_Ec"]
        elif name in {"S_NetLinkOut", "S_NetLinkIn"}:
            return ["S_Hub", "S_NetLink", "S_Ec"]
        elif name in {"S_NetHubOut", "S_NetHubIn"}:
            return ["S_Hub", "S_Ec"]
        elif name in {"S_NetTechOut", "S_NetTechIn"}:
            return ["S_Stage", "S_Hub", "S_NetLink", "S_NetTech"]
        elif name == "S_AtesTechTupleSchedule":
            return ["S_Stage", "S_Hub", "S_Tech", "S_AtesSchedule"]
        else:
            return [name]

    # Set is one-dimensional by Pyomo logic (could also be a manually defined
    # subset of a product of sets)
    if pyomo_set.dimen == 1:
        set_components = flatten_set_names(pyomo_set.name)
    # Set is multi-dimensional by Pyomo logic
    else:
        set_components = []
        for subset in pyomo_set.domain.subsets():
            set_components += flatten_set_names(subset.name)
    # Return
    return set_components
