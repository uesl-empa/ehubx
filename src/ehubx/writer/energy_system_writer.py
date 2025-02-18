"""Energy system writer module. Writes out information from the energy system
to files"""
import os
from typing import List, Tuple
from datetime import datetime
import pandas as pd
from pyomo.core import Model, Objective, value
from ehubx.core import logging
from ehubx.core import exceptions
from ehubx.data.energy_system_data import EnergySystem
import ehubx.data.exceptions as data_exceptions
from ehubx.model import energy_system_model
from ehubx.model import autarky_model
from ehubx.writer.common_writer import create_dir, FileGranularity, \
    init_df_st, add_to_df_st
from ehubx.writer import import_writer
from ehubx.writer import export_writer
from ehubx.writer import demand_writer
from ehubx.writer import load_shedding_writer
from ehubx.writer import load_shifting_writer
from ehubx.writer import tech_writer
from ehubx.writer import conv_tech_writer
from ehubx.writer import solar_writer
from ehubx.writer import wind_writer
from ehubx.writer import ebm_tech_writer
from ehubx.writer import hp_tech_writer
from ehubx.writer import network_writer

# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "writ/system"
"""String identifying the energy system writer module for logging purposes"""

FILENAME_SYSTEM: str = "system"
"""Filename for the energy system csv file in the write_all method"""

FILENAME_TECH_TIMESERIES_CSV: str = "tech_ts.csv"
"""Filename for time series with tech-related data"""

SOURCE: str = "system"
"""Display name for the system module in result files"""

SOURCE_STAGES: str = "stages"
"""Display name for the stage module in result files"""

SOURCE_AUTARKY: str = "autarky"
"""Display name for the autarky module in result files"""

ENTRY_INTERESTRATEDEF: str = "Default interest rate"
"""Entry name for the system-wide default interest rate in result files"""

ENTRY_TRLTHRESHOLD: str = "TRL threshold"
"""Entry name for the Technology Readiness Level (TRL) threshold in result
files"""

ENTRY_NUMTIMESHORIZON: str = "Number of horizon timesteps"
"""Entry name for the number of horizon timesteps in result files"""

ENTRY_NUMTIMESCLUSTERED: str = "Number of clustered timesteps"
"""Entry name for the number of clustered timesteps in result files"""

ENTRY_STAGESTARTYEAR: str = "Stage start year"
"""Entry name for the stage start year in result files"""

ENTRY_STAGECO2PRICE: str = "CO2 price"
"""Entry name for the CO2 price in result files"""

ENTRY_STAGECO2MIN: str = "Minimal CO2 emissions"
"""Entry name for the minimal CO2 emissions in result files"""

ENTRY_STAGECO2MAX: str = "Maximal CO2 emissions"
"""Entry name for the maximal CO2 emissions in result files"""

ENTRY_AUTARKYCALCULATIONMETHOD: str = "Autarky calculation method"
"""Entry name for the autarky calculation method in result files"""

ENTRY_AUTARKYMIN: str = "Minimal autarky"
"""Entry name for the minimal autarky in result files"""

ENTRY_AUTARKYMAX: str = "Maximal autarky"
"""Entry name for the maximal autarky in result files"""

ENTRY_SYSTEMCO2PENALTY: str = \
    f"CO2 penalty cost ({energy_system_model.VAR_SYSTEMCOSTCO2PENALTY})"
"""Entry name for the CO2 penalty cost variable in result files"""

ENTRY_SYSTEMCO2: str = f"CO2 emissions ({energy_system_model.VAR_SYSTEMCO2})"
"""Entry name for the CO2 emissions variable in result files"""

ENTRY_SYSTEMCO2TOTAL: str = \
    f"Total CO2 emissions ({energy_system_model.VAR_SYSTEMCO2TOTAL})"
"""Entry name for the total CO2 emissions variable in result files"""

ENTRY_SYSTEMCOST: str = f"Cost ({energy_system_model.VAR_SYSTEMCOST})"
"""Entry name for the cost variable in result files"""

ENTRY_SYSTEMAUTARKY: str = f"Autarky ({energy_system_model.VAR_SYSTEMAUTARKY})"
"""Entry name for the autarky variable in result files"""

ENTRY_OBJECTIVEVAL: str = "Objective value"
"""Entry name for the objective value in result files"""

ENTRY_AUTARKYIMPINTERNAL: str = \
    f"Internal imports ({autarky_model.VAR_AUTARKYIMPINTERNAL})"
"""Entry name for the internal import variable from the autarky module in
result  files"""

ENTRY_AUTARKYIMPCROSS: str = \
    f"Cross-imports ({autarky_model.VAR_AUTARKYIMPCROSS})"
"""Entry name for the cross-import variable from the autarky module in result
files"""

ENTRY_AUTARKY: str = f"Autarky ({autarky_model.VAR_AUTARKY})"
"""Entry name for the autarky variable in result files"""


def write_all(energy_system: EnergySystem, model: Model, dir_path: str,
              file_granularity: FileGranularity = FileGranularity.DEFAULT
              ) -> None:
    """
    Writes out an entire model and its solution from both the energy system
    data and the optimization results.

    :param energy_system: Energy system data object
    :type energy_system: EnergySystem
    :param model: Solved pyomo model
    :type model: Model
    :param dir_path: Path where the result files will be placed
    :type dir_path: str
    :param file_granularity: Setting that controls how much the output should
        be split across different files, defaults to FileGranularity.DEFAULT
    :type file_granularity: FileGranularity
    """
    # Directory
    if not os.path.isdir(dir_path):
        if not create_dir(dir_path, dir_desc="results"):
            raise exceptions.EhubXException(
                "Could not write all energy system data data because the "
                "directory could not be created", module=LOG_MODULE_STR)

    # Logging
    start_time = datetime.now()
    logging.log(f"Starting to write all energy system data to {dir_path} ...",
                module=LOG_MODULE_STR)

    # Prepare list of dataframes to be written
    dfs: List[Tuple[pd.DataFrame, str]] = []

    # Format top-level parameters
    dfs += _format_all_system(energy_system, model, dir_path)

    # Call submodule formaters
    dfs += tech_writer.format_all(energy_system, model, dir_path,
                                  file_granularity=file_granularity)
    dfs += import_writer.format_all(energy_system, model, dir_path,
                                    file_granularity=file_granularity)
    dfs += demand_writer.format_all(energy_system, model, dir_path,
                                    file_granularity=file_granularity)
    dfs += network_writer.format_all(energy_system, model, dir_path,
                                     file_granularity=file_granularity)

    # Write all dataframes to csv files
    for (df, filename) in dfs:
        if len(df.columns) > 0:
            if filename.endswith("-TS.csv") or filename.endswith("-TSCL.csv"):
                df.to_csv(filename)
            else:
                df.to_csv(filename, index=False)

    # Finish
    elapsed = datetime.now() - start_time
    logging.log((f"Finished writing all energy system data. Elapsed time: "
                 f"{int(elapsed.total_seconds())}s"), module=LOG_MODULE_STR)


def _format_all_system(energy_system: EnergySystem, model: Model,
                       dir_path: str) -> List[Tuple[pd.DataFrame, str]]:
    # Initialize dataframe
    df_st = init_df_st()

    # Default interest rate
    try:
        interest_rate = energy_system.interest_rate_def
        add_to_df_st(df_st, ENTRY_INTERESTRATEDEF, interest_rate, unit="1",
                     source=SOURCE, in_res="input")
    except data_exceptions.MissingValueException:
        pass

    # TRL threshold
    trl_threshold = energy_system.trl_threshold
    add_to_df_st(df_st, ENTRY_TRLTHRESHOLD, trl_threshold, source=SOURCE,
                 in_res="input")

    # Number of horizon timesteps
    num_ts_hor = energy_system.num_times_horizon
    add_to_df_st(df_st, ENTRY_NUMTIMESHORIZON, num_ts_hor,
                 source=SOURCE, in_res="input")

    # Number of clustered timesteps
    if energy_system.times.is_clustered:
        num_ts_cl = energy_system.times.num_ts
        add_to_df_st(df_st, ENTRY_NUMTIMESCLUSTERED, num_ts_cl,
                     source=SOURCE, in_res="result")

    # Stage start year
    for s in energy_system.stages.ids_in_order:
        start_year = energy_system.stages.get_start_year(s)
        add_to_df_st(df_st, ENTRY_STAGESTARTYEAR, start_year, stage=s.key,
                     source=SOURCE_STAGES, in_res="input")

    # Stage co2_min
    for s in energy_system.stages.ids_in_order:
        co2_min = energy_system.stages.get_co2_min(s)
        add_to_df_st(df_st, ENTRY_STAGECO2MIN, co2_min, unit="kg",
                     stage=s.key, source=SOURCE_STAGES, in_res="input")

    # Stage co2_max
    for s in energy_system.stages.ids_in_order:
        co2_max = energy_system.stages.get_co2_max(s)
        add_to_df_st(df_st, ENTRY_STAGECO2MAX, co2_max, unit="kg",
                     stage=s.key, source=SOURCE_STAGES, in_res="input")

    # Stage co2_price
    for s in energy_system.stages.ids_in_order:
        co2_price = energy_system.stages.get_co2_price(s)
        add_to_df_st(df_st, ENTRY_STAGECO2PRICE, co2_price, unit="CHF/kg",
                     stage=s.key, source=SOURCE_STAGES, in_res="input")

    # Autarky calculation method
    aut_calc_method = energy_system.autarky.calculation_method
    add_to_df_st(df_st, ENTRY_AUTARKYCALCULATIONMETHOD, aut_calc_method.value,
                 source=SOURCE_AUTARKY, in_res="input")

    # autarky_min
    aut_min = energy_system.autarky.autarky_min
    add_to_df_st(df_st, ENTRY_AUTARKYMIN, aut_min, unit="1",
                 source=SOURCE_AUTARKY, in_res="input")

    # autarky_max
    aut_max = energy_system.autarky.autarky_max
    add_to_df_st(df_st, ENTRY_AUTARKYMAX, aut_max, unit="1",
                 source=SOURCE_AUTARKY, in_res="input")

    # System CO2 penalty cost
    var = getattr(model, energy_system_model.VAR_SYSTEMCOSTCO2PENALTY)
    co2_penalty = value(var, exception=False)
    add_to_df_st(df_st, ENTRY_SYSTEMCO2PENALTY, co2_penalty, unit="CHF",
                 source=SOURCE, in_res="result")

    # System cost
    var = getattr(model, energy_system_model.VAR_SYSTEMCOST)
    cost = value(var, exception=False)
    add_to_df_st(df_st, ENTRY_SYSTEMCOST, cost, unit="CHF",
                 source=SOURCE, in_res="result")

    # System CO2
    var = getattr(model, energy_system_model.VAR_SYSTEMCO2)
    for s in energy_system.stages.ids_in_order:
        co2 = value(var[s.key], exception=False)
        add_to_df_st(df_st, ENTRY_SYSTEMCO2, co2, unit="kg", stage=s.key,
                     source=SOURCE, in_res="result")

    # Total system CO2
    var = getattr(model, energy_system_model.VAR_SYSTEMCO2TOTAL)
    co2_total = value(var, exception=False)
    add_to_df_st(df_st, ENTRY_SYSTEMCO2TOTAL, co2_total, unit="kg",
                 source=SOURCE, in_res="result")

    # Objective value
    objectives = model.component_objects(Objective, active=True)
    for obj in objectives:
        obj_val = value(obj, exception=False)
        add_to_df_st(df_st, ENTRY_OBJECTIVEVAL, obj_val,
                     source=SOURCE, in_res="result")

    # System autarky, energy_system_model.VAR_SYSTEMAUTARKY):
    var = getattr(model, energy_system_model.VAR_SYSTEMAUTARKY, None)
    if var is not None:
        autarky = value(var, exception=False)
        add_to_df_st(df_st, ENTRY_SYSTEMAUTARKY, autarky, unit="1",
                    source=SOURCE, in_res="result")

    # Internal imports
    var = getattr(model, autarky_model.VAR_AUTARKYIMPINTERNAL, None)
    if var is not None:
        internal_imp = value(var, exception=False)
        add_to_df_st(df_st, ENTRY_AUTARKYIMPINTERNAL, internal_imp, unit="kWh",
                    source=SOURCE_AUTARKY, in_res="result")

    # Cross-imports
    var = getattr(model, autarky_model.VAR_AUTARKYIMPCROSS, None)
    if var is not None:
        cross_imp = value(var, exception=False)
        add_to_df_st(df_st, ENTRY_AUTARKYIMPCROSS, cross_imp, unit="kWh",
                    source=SOURCE_AUTARKY, in_res="result")

    # Autarky
    var = getattr(model, autarky_model.VAR_AUTARKY, None)
    if var is not None:
        autarky = value(var, exception=False)
        add_to_df_st(df_st, ENTRY_AUTARKY, autarky, unit="1",
                    source=SOURCE_AUTARKY, in_res="result")

    # Return
    filename = os.path.join(dir_path, f"{FILENAME_SYSTEM}.csv")
    return [(df_st, filename)]


def write_data_time_series(energy_system: EnergySystem, dir_path: str) -> None:
    """
    Writes all input time series with actual data (def_value is not enough) in
    an energy system data object to dedicated csv files in a directory

    :param energy_system: The energy system whose time series are to be written
    :type energy_system: EnergySystem
    :param dir_path: Path where the csv files will be placed
    :type dir_path: str
    """
    # Create directory if it does not exist
    if not os.path.isdir(dir_path):
        if not create_dir(dir_path):
            raise exceptions.EhubXException(
                "Could not write energy system input time series data because "
                "the directory could not be created", module=LOG_MODULE_STR)
    # Call submodule writers
    import_writer.write_data_time_series(
        energy_system.imports, energy_system.times, dir_path)
    export_writer.write_data_time_series(
        energy_system.exports, energy_system.times, dir_path)
    demand_writer.write_input_time_series(
        energy_system.demands, energy_system.times, dir_path)
    load_shedding_writer.write_data_time_series(
        energy_system.load_shedding, energy_system.times, dir_path)
    load_shifting_writer.write_time_series(
        energy_system.load_shifting, energy_system.times, dir_path)
    conv_tech_writer.write_data_time_series(
        energy_system.conv_techs, energy_system.times, dir_path)
    ebm_tech_writer.write_data_time_series(
        energy_system.ebm_techs, energy_system.times, dir_path)
    hp_tech_writer.write_data_time_series(
        energy_system.hp_techs, energy_system.times, dir_path)
    solar_writer.write_data_time_series(
        energy_system.solar_data, energy_system.times, dir_path)
    wind_writer.write_time_series(
        energy_system.wind_data, energy_system.times, dir_path)
    network_writer.write_time_series(
        energy_system.net_links, energy_system.times, dir_path)
