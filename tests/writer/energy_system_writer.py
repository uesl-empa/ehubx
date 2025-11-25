"""Energy system writer module. Writes out information from the energy system
to files"""

import os
from datetime import datetime
from typing import List, Tuple

import pandas as pd
from pyomo.core import Model, Objective, value

import ehubx.data.exceptions as data_exceptions
from ehubx.core import exceptions, logging
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.unit import DimlessUnit
from ehubx.data.value import Value
from ehubx.model import energy_system_model, self_sufficiency_model
from ehubx.writer import (
    conv_tech_writer,
    demand_writer,
    ebm_tech_writer,
    export_writer,
    hp_tech_writer,
    import_writer,
    load_shedding_writer,
    network_writer,
    solar_writer,
    tech_writer,
)
from ehubx.writer.common_writer import (
    FileGranularity,
    add_to_df_st,
    create_dir,
    init_df_st,
)


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

SOURCE_SELFSUFF: str = "self-sufficiency"
"""Display name for the self-sufficiency module in result files"""

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

ENTRY_SELFSUFFCALCULATIONMETHOD: str = "Self-sufficiency calculation method"
"""Entry name for the self-sufficiency calculation method in result files"""

ENTRY_SELFSUFFMIN: str = "Minimal self-sufficiency"
"""Entry name for the minimal self-sufficiency in result files"""

ENTRY_SELFSUFFMAX: str = "Maximal self-sufficiency"
"""Entry name for the maximal self-sufficiency in result files"""

ENTRY_SYSTEMCO2PENALTY: str = (
    f"CO2 penalty cost ({energy_system_model.VAR_SYSTEMCOSTCO2PENALTY})"
)
"""Entry name for the CO2 penalty cost variable in result files"""

ENTRY_SYSTEMCO2: str = f"CO2 emissions ({energy_system_model.VAR_SYSTEMCO2})"
"""Entry name for the CO2 emissions variable in result files"""

ENTRY_SYSTEMCO2TOTAL: str = (
    f"Total CO2 emissions ({energy_system_model.VAR_SYSTEMCO2TOTAL})"
)
"""Entry name for the total CO2 emissions variable in result files"""

ENTRY_SYSTEMCOST: str = f"Cost ({energy_system_model.VAR_SYSTEMCOST})"
"""Entry name for the cost variable in result files"""

ENTRY_SYSTEMSELFSUFF: str = (
    f"Self-sufficiency ({energy_system_model.VAR_SYSTEMSELFSUFFICIENCY})"
)
"""Entry name for the self-sufficiency variable in result files"""

ENTRY_OBJECTIVEVAL: str = "Objective value"
"""Entry name for the objective value in result files"""

ENTRY_SELFSUFFIMPINTERNAL: str = (
    f"Internal imports ({self_sufficiency_model.VAR_SELFSUFFIMPINTERNAL})"
)
"""Entry name for the internal import variable from the self-sufficiency module in
result  files"""

ENTRY_SELFSUFFIMPCROSS: str = (
    f"Cross-imports ({self_sufficiency_model.VAR_SELFSUFFIMPCROSS})"
)
"""Entry name for the cross-import variable from the self-sufficiency module in result
files"""

ENTRY_SELFSUFF: str = f"Self-sufficiency ({self_sufficiency_model.VAR_SELFSUFFICIENCY})"
"""Entry name for the self-sufficiency variable in result files"""


def write_all(
    energy_system: EnergySystem,
    model: Model,
    dir_path: str,
    file_granularity: FileGranularity = FileGranularity.DEFAULT,
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
                "directory could not be created",
                module=LOG_MODULE_STR,
            )

    # Logging
    start_time = datetime.now()
    logging.log(
        f"Starting to write all energy system data to {dir_path} ...",
        module=LOG_MODULE_STR,
    )

    # Prepare list of dataframes to be written
    dfs: List[Tuple[pd.DataFrame, str]] = []

    # Format top-level parameters
    dfs += _format_all_system(energy_system, model, dir_path)

    # Call submodule formaters
    dfs += tech_writer.format_all(
        energy_system, model, dir_path, file_granularity=file_granularity
    )
    dfs += import_writer.format_all(
        energy_system, model, dir_path, file_granularity=file_granularity
    )
    dfs += demand_writer.format_all(
        energy_system, model, dir_path, file_granularity=file_granularity
    )
    dfs += network_writer.format_all(
        energy_system, model, dir_path, file_granularity=file_granularity
    )

    # Write all dataframes to csv files
    for df, filename in dfs:
        if len(df.columns) > 0:
            if filename.endswith("-TS.csv") or filename.endswith("-TSCL.csv"):
                df.to_csv(filename)
            else:
                df.to_csv(filename, index=False)

    # Finish
    elapsed = datetime.now() - start_time
    logging.log(
        (
            f"Finished writing all energy system data. Elapsed time: "
            f"{int(elapsed.total_seconds())}s"
        ),
        module=LOG_MODULE_STR,
    )


def _format_all_system(
    energy_system: EnergySystem, model: Model, dir_path: str
) -> List[Tuple[pd.DataFrame, str]]:
    # Initialize dataframe
    df_st = init_df_st()

    # Default interest rate
    try:
        interest_rate = energy_system.interest_rate_def
        add_to_df_st(
            df_st,
            ENTRY_INTERESTRATEDEF,
            interest_rate,
            unit=DimlessUnit(),
            source=SOURCE,
            in_res="input",
        )
    except data_exceptions.MissingValueException:
        pass

    # TRL threshold
    trl_threshold = energy_system.trl_threshold
    add_to_df_st(
        df_st,
        ENTRY_TRLTHRESHOLD,
        trl_threshold,
        DimlessUnit(),
        source=SOURCE,
        in_res="input",
    )

    # Number of horizon timesteps
    num_ts_hor = energy_system.num_times_horizon
    add_to_df_st(
        df_st, ENTRY_NUMTIMESHORIZON, str(num_ts_hor), source=SOURCE, in_res="input"
    )

    # Number of clustered timesteps
    if energy_system.times.is_clustered:
        num_ts_cl = energy_system.times.num_ts
        add_to_df_st(
            df_st,
            ENTRY_NUMTIMESCLUSTERED,
            str(num_ts_cl),
            source=SOURCE,
            in_res="result",
        )

    # Stage start year
    for s in energy_system.stages.ids_in_order:
        start_year = energy_system.stages.get_start_year(s)
        add_to_df_st(
            df_st,
            ENTRY_STAGESTARTYEAR,
            str(start_year),
            stage=s.key,
            source=SOURCE_STAGES,
            in_res="input",
        )

    # Stage co2_min
    for s in energy_system.stages.ids_in_order:
        co2_min = energy_system.stages.get_co2_min(s)
        add_to_df_st(
            df_st,
            ENTRY_STAGECO2MIN,
            co2_min,
            unit=energy_system.mass_unit,
            stage=s.key,
            source=SOURCE_STAGES,
            in_res="input",
        )

    # Stage co2_max
    for s in energy_system.stages.ids_in_order:
        co2_max = energy_system.stages.get_co2_max(s)
        add_to_df_st(
            df_st,
            ENTRY_STAGECO2MAX,
            co2_max,
            unit=energy_system.mass_unit,
            stage=s.key,
            source=SOURCE_STAGES,
            in_res="input",
        )

    # Stage co2_price
    for s in energy_system.stages.ids_in_order:
        co2_price = energy_system.stages.get_co2_price(s)
        add_to_df_st(
            df_st,
            ENTRY_STAGECO2PRICE,
            co2_price,
            unit=(energy_system.currency_unit / energy_system.mass_unit),
            stage=s.key,
            source=SOURCE_STAGES,
            in_res="input",
        )

    # Self-sufficiency calculation method
    aut_calc_method = energy_system.self_sufficiency.calculation_method
    add_to_df_st(
        df_st,
        ENTRY_SELFSUFFCALCULATIONMETHOD,
        aut_calc_method.value,
        source=SOURCE_SELFSUFF,
        in_res="input",
    )

    # self_sufficiency_min
    self_suff_min = energy_system.self_sufficiency.self_sufficiency_min
    add_to_df_st(
        df_st,
        ENTRY_SELFSUFFMIN,
        self_suff_min,
        unit=DimlessUnit(),
        source=SOURCE_SELFSUFF,
        in_res="input",
    )

    # self_sufficiency_max
    self_suff_max = energy_system.self_sufficiency.self_sufficiency_max
    add_to_df_st(
        df_st,
        ENTRY_SELFSUFFMAX,
        self_suff_max,
        unit=DimlessUnit(),
        source=SOURCE_SELFSUFF,
        in_res="input",
    )

    # System CO2 penalty cost
    var = getattr(model, energy_system_model.VAR_SYSTEMCOSTCO2PENALTY)
    co2_penalty_fl = value(var, exception=False)
    if co2_penalty_fl is not None:
        co2_penalty = Value(co2_penalty_fl, unit=energy_system.currency_unit)
        add_to_df_st(
            df_st,
            ENTRY_SYSTEMCO2PENALTY,
            co2_penalty,
            unit=energy_system.currency_unit,
            source=SOURCE,
            in_res="result",
        )

    # System cost
    var = getattr(model, energy_system_model.VAR_SYSTEMCOST)
    cost = value(var, exception=False)
    add_to_df_st(
        df_st,
        ENTRY_SYSTEMCOST,
        cost,
        unit=energy_system.currency_unit,
        source=SOURCE,
        in_res="result",
    )

    # System CO2
    var = getattr(model, energy_system_model.VAR_SYSTEMCO2)
    for s in energy_system.stages.ids_in_order:
        co2 = value(var[s.key], exception=False)
        add_to_df_st(
            df_st,
            ENTRY_SYSTEMCO2,
            co2,
            unit=energy_system.mass_unit,
            stage=s.key,
            source=SOURCE,
            in_res="result",
        )

    # Total system CO2
    var = getattr(model, energy_system_model.VAR_SYSTEMCO2TOTAL)
    co2_total = value(var, exception=False)
    add_to_df_st(
        df_st,
        ENTRY_SYSTEMCO2TOTAL,
        co2_total,
        unit=energy_system.mass_unit,
        source=SOURCE,
        in_res="result",
    )

    # Objective value
    objectives = model.component_objects(Objective, active=True)
    for obj in objectives:
        obj_val = value(obj, exception=False)
        add_to_df_st(df_st, ENTRY_OBJECTIVEVAL, obj_val, source=SOURCE, in_res="result")

    # System self-sufficiency, energy_system_model.VAR_SYSTEMSELFSUFFICIENCY):
    var = getattr(model, energy_system_model.VAR_SYSTEMSELFSUFFICIENCY, None)
    if var is not None:
        self_suff_fl = value(var, exception=False)
        if self_suff_fl is not None:
            self_suff = Value(self_suff_fl)
            add_to_df_st(
                df_st,
                ENTRY_SYSTEMSELFSUFF,
                self_suff,
                unit=DimlessUnit(),
                source=SOURCE,
                in_res="result",
            )

    # Internal imports
    var = getattr(model, self_sufficiency_model.VAR_SELFSUFFIMPINTERNAL, None)
    if var is not None:
        internal_imp_fl = value(var, exception=False)
        if internal_imp_fl is not None:
            internal_imp = Value(internal_imp_fl)
            add_to_df_st(
                df_st,
                ENTRY_SELFSUFFIMPINTERNAL,
                internal_imp,
                source=SOURCE_SELFSUFF,
                in_res="result",
            )

    # Cross-imports
    var = getattr(model, self_sufficiency_model.VAR_SELFSUFFIMPCROSS, None)
    if var is not None:
        cross_imp_fl = value(var, exception=False)
        if cross_imp_fl is not None:
            cross_imp = Value(cross_imp_fl)
            add_to_df_st(
                df_st,
                ENTRY_SELFSUFFIMPCROSS,
                cross_imp,
                source=SOURCE_SELFSUFF,
                in_res="result",
            )

    # Self-sufficiency
    var = getattr(model, self_sufficiency_model.VAR_SELFSUFFICIENCY, None)
    if var is not None:
        self_suff_fl = value(var, exception=False)
        if self_suff_fl is not None:
            self_suff = Value(self_suff_fl)
            add_to_df_st(
                df_st,
                ENTRY_SELFSUFF,
                self_suff,
                source=SOURCE_SELFSUFF,
                in_res="result",
            )

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
                "the directory could not be created",
                module=LOG_MODULE_STR,
            )
    # Call submodule writers
    import_writer.write_data_time_series(energy_system, dir_path)
    export_writer.write_data_time_series(energy_system, dir_path)
    demand_writer.write_input_time_series(energy_system, dir_path)
    load_shedding_writer.write_data_time_series(energy_system, dir_path)
    conv_tech_writer.write_data_time_series(energy_system, dir_path)
    ebm_tech_writer.write_data_time_series(energy_system, dir_path)
    hp_tech_writer.write_data_time_series(energy_system, dir_path)
    solar_writer.write_data_time_series(energy_system, dir_path)
    network_writer.write_data_time_series(energy_system, dir_path)
