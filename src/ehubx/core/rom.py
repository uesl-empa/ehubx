"""Reduced-order modeling module"""

import copy
import csv
import math
import os
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import tsam.timeseriesaggregation as tsam  # type: ignore

from ehubx.core import exceptions, logging
from ehubx.core.common import TimeSeriesKind
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.stage_data import StageId
from ehubx.data.time_data import TimeId
from ehubx.writer.common_writer import create_dir
from ehubx.writer.energy_system_writer import write_data_time_series


# ---------- #
# ROM method #
# ---------- #
class RomMethod(Enum):
    """Reduced-order modeling method"""

    NONE = "none"
    """Do not perform ROM"""

    CLUSTER_TSAM = "tsam clustering"
    """Clustering using the tsam package
    (https://tsam.readthedocs.io/en/latest/)"""

    CUT_TIME = "cut time"
    """Cut all time series after num_ts_target"""


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "rom"
"""String identifying the ROM module for logging purposes"""

DIRNAME_PROFILES: str = "profiles"
"""Name for the profiles subdirectory in the ROM directory"""

FILENAME_TIMEMAP: str = "time_map.csv"
"""Name for the time map file in the ROM directory"""

FILENAME_DEMANDPROFILES: str = "demands.csv"
"""Name for reduced demand profiles in the ROM directory"""


# ------------ #
# ROM settings #
# ------------ #
class RomSettings:
    """Settings for Reduced-Order Modeling"""

    @property
    def num_ts_target(self) -> int:
        """Target number of reduced-order timesteps"""
        return self._num_ts_target

    @num_ts_target.setter
    def num_ts_target(self, num_ts_target: int) -> None:
        if num_ts_target <= 0:
            msg = f"Tried to set nonpositive value num_ts_target={num_ts_target}"
            raise exceptions.EhubXException(msg, module=LOG_MODULE_STR)
        self._num_ts_target = num_ts_target

    def __init__(
        self, method: RomMethod = RomMethod.CLUSTER_TSAM, num_ts_target: int = 10
    ) -> None:
        self.method = method
        self.num_ts_target = num_ts_target


def rom(
    energy_system: EnergySystem,
    rom_settings: RomSettings,
    write_rom: bool = True,
    rom_dir_path: Optional[str] = None,
    add_time_to_dir: bool = False,
) -> Optional[EnergySystem]:
    """
    Perform reduced-order modeling on the energy system data. A reduced-
    order model is calculated based on the provided settings. Specifically,
    the 'method' argument will determine what kind of ROM strategy will
    be employed.

    :param energy_system: Energy system to be reduced
    :type energy_system: EnergySystem
    :param rom_settings: Settings for reduced-order modeling
    :type rom_settings: RomSettings
    :param write_rom: Whether to write out the reduced-order energy-system
    :type write_rom: bool
    :param rom_dir_path: ROM directory
    :type rom_dir_path: str, optional
    :param add_time_to_dir: Whether a timestamp will be added to the
        ROM directory name, defaults to False
    :type add_time_to_dir: bool
    :return: Reduced-order energy system
    :rtype: Optional[EnergySystem]
    """

    # No ROM
    sys_rom: Optional[EnergySystem] = None
    if rom_settings.method == RomMethod.NONE:
        msg = (
            "Called reduced-order modeling with the method set to "
            "None in the ROM settings. Skipping ..."
        )
        logging.log_warning(msg, module=LOG_MODULE_STR)
        return sys_rom

    # Some modules are not compatible with rom at the moment:
    if len(energy_system.load_shifting.ids) > 0:
        raise exceptions.EhubXException(
            "Can currently not perform reduced-order modeling under presence "
            "of load shifting",
            module=LOG_MODULE_STR,
        )

    # Cut the time horizon after num_ts_target
    if rom_settings.method == RomMethod.CUT_TIME:
        sys_rom = _cut_time(
            energy_system,
            rom_settings.num_ts_target,
            write_rom,
            rom_dir_path,
            add_time_to_dir,
        )

    # Perform tsam clustering
    if rom_settings.method == RomMethod.CLUSTER_TSAM:
        sys_rom = _cluster_tsam(
            energy_system,
            rom_settings.num_ts_target,
            write_rom,
            rom_dir_path,
            add_time_to_dir,
        )

    # Return
    return sys_rom


# -------------------- #
# ROM method: Cut time #
# -------------------- #
def _cut_time(
    energy_system: EnergySystem,
    num_ts: int,
    write_rom: bool,
    rom_dir_path: Optional[str],
    add_time_to_dir: bool,
) -> EnergySystem:
    """
    Cut all time series in the full energy system

    :param energy_system: Energy system data object
    :type energy_system: EnergySystem
    :param num_ts: Number of time steps after which to cut
    :type num_ts: int
    :param write_rom: Whether to write ROM output
    :type rom_dir_path: bool
    :param rom_dir_path: Path of rom directory for writing outputs
    :type rom_dir_path: Optional[str]
    :param add_time_to_dir: Whether a timestamp should be added to the ROM
        directory path
    :type add_time_to_dir: bool
    :return: The reduced energy system.
    """

    # Make a carbon copy of the energy system data
    start_time = datetime.now()
    logging.log(
        "Starting reduced-order modeling (cut-time strategy) to "
        f"reduce the time horizon to the first {num_ts} time indices",
        module=LOG_MODULE_STR,
    )
    sys = copy.deepcopy(energy_system)

    # Build the time map
    time_map: List[Tuple[StageId, TimeId, Optional[TimeId]]] = []
    for s in energy_system.stages.ids:
        for t in range(1, num_ts + 1):
            time_map.append((s, TimeId(t), TimeId(t)))
        for t in range(num_ts + 1, sys.times.num_horizon_ts + 1):
            time_map.append((s, TimeId(t), None))

    # Cut profiles
    for _, _, _, series in sys.time_series:
        for t in range(num_ts + 1, sys.times.num_horizon_ts + 1):
            series.remove_value(TimeId(t))

    # Modify the time data.
    sys.times.clear_horizon_ids()
    for t in range(1, num_ts + 1):
        sys.times.add_id(TimeId(t))

    # Write ROM outputs
    if write_rom:
        if rom_dir_path is None:
            raise exceptions.EhubXException(
                "Failed to write ROM because rom_dir_path is unspecified",
                module=LOG_MODULE_STR,
            )
        __write_rom_time_map(time_map, rom_dir_path, add_time_to_dir)
        profile_dir_path = os.path.join(rom_dir_path, DIRNAME_PROFILES)
        write_data_time_series(sys, profile_dir_path)

    # Return the reduced energy system
    elapsed = datetime.now() - start_time
    logging.log(
        (
            f"Finished reduced-order modeling. Elapsed time: "
            f"{int(elapsed.total_seconds())}s"
        ),
        module=LOG_MODULE_STR,
    )
    return sys


# --------------------------- #
# ROM method: tsam clustering #
# --------------------------- #
def _cluster_tsam(
    energy_system: EnergySystem,
    num_ts: int,
    write_rom: bool,
    rom_dir_path: Optional[str],
    add_time_to_dir: bool,
) -> Optional[EnergySystem]:
    """
    Perform time clustering with the tsam package

    :param energy_system: Energy system data object
    :type energy_system: EnergySystem
    :param num_ts: Target number of cluster timesteps
    :type num_ts: int
    :param write_rom: Whether to write ROM output
    :type rom_dir_path: bool
    :param rom_dir_path: Path of rom directory for writing outputs
    :type rom_dir_path: Optional[str]
    :param add_time_to_dir: Whether a timestamp should be added to the ROM
        directory path
    :type add_time_to_dir: bool
    :return: The reduced energy system.
    """
    # Start
    start_time = datetime.now()
    logging.log(
        "Starting reduced-order modeling (clustering-tsam strategy) "
        f"to reduce the time horizon to a targeted {num_ts} time "
        "steps in the reduced system",
        module=LOG_MODULE_STR,
    )

    # Clustering only makes sense with fewer clustered ts than horizon ts
    if num_ts >= energy_system.times.num_horizon_ts:
        logging.log(
            "Stopped clustering because target number of clustered "
            f"time steps ({num_ts}) is larger than number of horizon "
            f"time steps ({energy_system.times.num_horizon_ts}) "
            "in the model",
            module=LOG_MODULE_STR,
        )
        return None

    # Make a carbon copy of the energy system data object and extract its time
    # series
    sys = copy.deepcopy(energy_system)
    df = __series_to_df(energy_system)

    # Need at least twice as many cluster time steps as number of time series
    if num_ts < 2 * len(df.columns):
        num_ts = 2 * len(df.columns)
        logging.log(
            "Changed target number of clustered time steps to "
            f"2 * num_series = {num_ts} because it was smaller than "
            "that before (num_series is the number of time series in "
            "the energy system data)",
            module=LOG_MODULE_STR,
        )

    # Prepare per-stage attributes
    df_cl_per_stage: Dict[StageId, pd.DataFrame] = {}
    time_dict_per_stage: Dict[StageId, Dict[TimeId, TimeId]] = {}
    err_per_stage: Dict[StageId, pd.DataFrame] = {}

    def __cluster_stage(
        s: StageId,
        num_ts_: int = num_ts,
        extreme_period_method: str = "new_cluster_center",
    ) -> None:
        """
        Perform time clustering for the time series in a specific stage

        :param s: Stage
        :type s: StageId
        :param num_ts_: Target number of clustered time steps, defaults to
            num_ts
        :type num_ts_: int, optional
        :param extreme_period_method: Method used to ensure time steps with
            extreme values are included. "new_cluster_center" adds a new
            cluster timestep for those, "None" does not try to include them,
            defaults to "new_cluster_center"
        :type extreme_period_method: str, optional
        """
        # Get data from this stage
        try:
            df_s = df.xs(s.key, axis=1, level=1, drop_level=False)
        except KeyError as exc:
            raise exceptions.EhubXException(
                f"No time series data was detected for stage {s}. In order "
                "for tsam clustering to work, time series data must be "
                "present for every stage",
                module=LOG_MODULE_STR,
            ) from exc

        # Log
        logging.log_file(
            f"Started to calculate clustering for stage {s} "
            f"which has {len(df_s.columns)} time series ...",
            module=LOG_MODULE_STR,
        )

        # Calculate "roundOutput" for tsam which is the decimal to which the
        # output will be rounded
        round_output = 6
        min_val = np.nanmin(np.where(df_s.values == 0, np.nan, df_s.values))
        magnitude = math.floor(math.log(min_val, 10))
        if magnitude < -4:
            round_output = 2 - magnitude

        # Construct the tsam aggregation object
        agg = tsam.TimeSeriesAggregation(
            df_s,
            noTypicalPeriods=num_ts_,
            hoursPerPeriod=1,
            clusterMethod="hierarchical",
            addPeakMax=df_s.columns.values.tolist(),
            addPeakMin=df_s.columns.values.tolist(),
            rescaleClusterPeriods=False,
            extremePeriodMethod=extreme_period_method,
            roundOutput=round_output,
            representationMethod="durationRepresentation",
        )

        # Calculate the clustered time series
        df_cl_per_stage[s] = agg.createTypicalPeriods().reset_index(drop=True)
        df_cl_per_stage[s].index += 1

        # Save results from stage clustering
        time_dict_per_stage[s] = {
            TimeId(t_full): TimeId(t_cl)
            for t_full, t_cl in enumerate(agg.clusterOrder + 1, start=1)
        }
        err_per_stage[s] = agg.accuracyIndicators()

    # Perform clustering in each stage
    for s in energy_system.stages.ids:
        __cluster_stage(s)

    # Detect mismatch in num_ts between stages. All stages should have the
    # same amount of clustered timesteps now
    num_ts_per_stage = {
        s: df_cl_per_stage[s].shape[0] for s in energy_system.stages.ids
    }
    num_ts_max = max(num_ts_per_stage.values())
    for s, num_ts_s in num_ts_per_stage.items():
        if num_ts_s != num_ts_max:
            # Recluster with maximal order
            logging.log(
                f"Restarting clustering in stage {s} to synchronize stages."
                f"{s} had {num_ts_s} cluster time steps, maximum across "
                f"stages is {num_ts_max}",
                module=LOG_MODULE_STR,
            )
            __cluster_stage(s, num_ts_=num_ts_max, extreme_period_method="None")
    num_ts = num_ts_max

    # Build the time map
    time_map: List[Tuple[StageId, TimeId, Optional[TimeId]]] = []
    time_map = [
        (s, t_full, time_dict_per_stage[s][t_full])
        for s in energy_system.stages.ids
        for t_full in energy_system.times.ids_horizon
    ]

    # Modify the time data
    sys.times.clear_ids()
    for s, time_dict in time_dict_per_stage.items():
        for t_cl in set(time_dict.values()):
            if t_cl not in sys.times.ids:
                sys.times.add_id(t_cl)
            weight = list(time_dict.values()).count(t_cl)
            sys.times.set_weight(s, t_cl, weight)
        for t_full, t_cl in time_dict.items():
            sys.times.set_cluster_ts(s, t_cl, t_full)

    # Redistribute profiles
    for _, _, _, series in sys.time_series:
        series.clear()
    df_cl = pd.concat(df_cl_per_stage.values(), axis=1).reset_index(drop=True)
    df_cl.index += 1
    __df_to_series(df_cl, sys)

    # Write ROM output
    if write_rom:
        if rom_dir_path is None:
            raise exceptions.EhubXException(
                "Failed to write ROM because rom_dir_path is unspecified",
                module=LOG_MODULE_STR,
            )
        __write_rom_time_map(time_map, rom_dir_path, add_time_to_dir)
        profile_dir_path = os.path.join(rom_dir_path, DIRNAME_PROFILES)
        write_data_time_series(sys, profile_dir_path)

    # Return the reduced energy system
    elapsed = datetime.now() - start_time
    logging.log(
        (
            f"Finished reduced-order modeling. Elapsed time: "
            f"{int(elapsed.total_seconds())}s"
        ),
        module=LOG_MODULE_STR,
    )
    return sys


# --------- #
# Write ROM #
# --------- #
def __write_rom_time_map(
    time_map: List[Tuple[StageId, TimeId, Optional[TimeId]]],
    rom_dir_path: str,
    add_time_to_dir: bool,
) -> None:
    # Directories and files
    rom_dir_path_new = create_dir(
        rom_dir_path, add_time_to_dir=add_time_to_dir, dir_desc="ROM"
    )
    if rom_dir_path_new is None:
        raise exceptions.EhubXException(
            "Could not write ROM data because the directory could not be created",
            module=LOG_MODULE_STR,
        )
    rom_dir_path = rom_dir_path_new
    time_map_path = os.path.join(rom_dir_path, FILENAME_TIMEMAP)

    # Write time map
    if time_map:
        with open(time_map_path, "w", newline="", encoding="utf8") as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow(["stage_id", "ts_full", "ts_cluster"])
            for s, t_full, t_cluster in time_map:
                t_cluster_key: Optional[int] = None
                if t_cluster:
                    t_cluster_key = t_cluster.key_as_int
                csv_writer.writerow([s.key, t_full.key_as_int, t_cluster_key])

    # Log
    logging.log(f"Written ROM time data to {rom_dir_path}", module=LOG_MODULE_STR)


def __series_to_df(sys: EnergySystem) -> pd.DataFrame:
    """
    Creates a pandas dataframe from all time series in the energy system.
    Each time series takes a column in the dataframe, so there are a number of
    rows equal to the number of horizon time ids. Each column is indexed by a
    multiindex whose first component is the string of the corresponding kind of
    time series. The second index is the stage of the series. Then come all
    other string identifiers which belong to this time series (as returned from
    energy_system.time_series). Finally, the last non-used components of the
    multtindex are filled up with empty strings.

    :param sys: Energy system data object
    :type sys: EnergySystem
    :return: The retuned dataframe, formated as explained above
    :rtype: pd.DataFrame
    """
    # Get the time series and horizon ids
    all_series = sys.time_series
    horizon_ids = sys.times.ids_horizon_in_order

    # Obtain the number of components in the column multiindex
    dim_col_id = max(len(ids) for _, _, ids, _ in all_series) + 2

    # Format the index for each series and obtain the time series as a list
    # Do this for every stage
    df_data: Dict[Tuple[str, ...], List[float]] = {}
    for kind, stage_id, ids, series in all_series:
        col_id = (kind.value, stage_id.key) + ids + ("",) * (dim_col_id - len(ids) - 2)
        df_data[col_id] = [series.get_value(t) for t in horizon_ids]

    # Build the dataframe and make the index start at 1 instead of 0
    df = pd.DataFrame(df_data)
    df.index += 1
    df.index = pd.to_datetime(df.index, unit="h")
    df = df.sort_index()

    # Return
    return df


def __df_to_series(df: pd.DataFrame, sys: EnergySystem) -> None:
    for col in df.columns:
        kind = TimeSeriesKind(col[0])
        s = StageId(col[1])
        ids = tuple(col[2:])
        for t in sys.times.ids:
            sys.set_time_series_val(kind, s, ids, t, df[col][t.key_as_int])
