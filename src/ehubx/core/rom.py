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
    if len(energy_system.ates_techs.ids) > 0:
        raise exceptions.EhubXException(
            "Can currently not perform reduced-order modeling under presence "
            "of ATES technologies",
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
    # series, splitting them by stage
    sys = copy.deepcopy(energy_system)
    df = __series_to_df(energy_system)
    # Get data from each stage
    df_by_s: Dict[StageId, pd.DataFrame] = {}
    for s in energy_system.stages.ids:
        try:
            df_by_s[s] = df.xs(s.key, level=1, axis=1, drop_level=False)
        except KeyError as exc:
            raise exceptions.EhubXException(
                f"No time series data was detected for stage {s}. In order "
                "for tsam clustering to work, time series data must be "
                "present for every stage",
                module=LOG_MODULE_STR,
            ) from exc
    # Determine maximal number of time series in each stage
    num_ser_by_s: Dict[StageId, int] = {
        s: len(df_by_s[s].columns) for s in energy_system.stages.ids
    }
    num_ser_max_s, _ = max(num_ser_by_s.items(), key=lambda item: item[1])
    num_ser_max = num_ser_by_s[num_ser_max_s]

    # Need at least twice as many cluster time steps as number of time series in each
    # stage
    if num_ts < 2 * num_ser_max:
        logging.log(
            f"Target number of clustered time steps ({num_ts}) is too small. Stage "
            f"{num_ser_max_s} has the most time series ({num_ser_max}), and therefore "
            f"we need at least twice as many clustered time steps. Changed target "
            f"number of clustered time steps to {2 * num_ser_max}",
            module=LOG_MODULE_STR,
        )
        num_ts = 2 * num_ser_max

    # Determine the extreme periods of each stage. All stages get the same
    # number of clustered time steps: the target number of regular clusters
    # plus the largest number of extreme periods among all stages. Stages with
    # fewer extreme periods get more regular clusters instead.
    ext_by_s: Dict[StageId, List[int]] = {
        s: __find_extreme_periods(df_s) for s, df_s in df_by_s.items()
    }
    num_ts = num_ts + max(len(ext) for ext in ext_by_s.values())

    # Perform clustering in each stage
    df_cl_per_stage: Dict[StageId, pd.DataFrame] = {}
    time_dict_per_stage: Dict[StageId, Dict[TimeId, TimeId]] = {}
    for s, df_s in df_by_s.items():
        logging.log_file(
            f"Started to calculate clustering for stage {s} "
            f"which has {len(df_s.columns)} time series ...",
            module=LOG_MODULE_STR,
        )
        order, df_cl_per_stage[s] = __cluster_stage(df_s, ext_by_s[s], num_ts)
        time_dict_per_stage[s] = {
            TimeId(t_full): TimeId(int(t_cl) + 1)
            for t_full, t_cl in enumerate(order, start=1)
        }
        logging.log(
            f"Finished clustering for stage {s} with {num_ts} clustered time "
            f"steps, {len(ext_by_s[s])} of which hold extreme values",
            module=LOG_MODULE_STR,
        )

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


def __find_extreme_periods(df_s: pd.DataFrame) -> List[int]:
    """
    Find the extreme periods of the time series of a stage, i.e. the horizon
    time steps at which a time series attains its maximum or its minimum.
    Constant time series do not have extreme periods.

    :param df_s: Time series of a stage, one column per series and one row
        per horizon time step
    :type df_s: pd.DataFrame
    :return: Positions (0-based rows of df_s) of the extreme periods, without
        duplicates
    :rtype: List[int]
    """
    values = df_s.to_numpy()
    ext: List[int] = []
    for col in values.T:
        if col.max() == col.min():
            continue
        for pos in (int(np.argmax(col)), int(np.argmin(col))):
            if pos not in ext:
                ext.append(pos)
    return ext


def __round_output(df_s: pd.DataFrame) -> int:
    """
    Decimal to which tsam rounds its output. The magnitude is taken from the
    smallest nonzero absolute value, so that negative values (e.g. negative
    prices) are supported. If all values are zero, the default is kept.

    :param df_s: Time series of a stage
    :type df_s: pd.DataFrame
    :return: Number of decimals
    :rtype: int
    """
    round_output = 6
    abs_vals = np.abs(df_s.values)
    abs_vals_nonzero = abs_vals[abs_vals > 0]
    if abs_vals_nonzero.size > 0:
        magnitude = math.floor(math.log(abs_vals_nonzero.min(), 10))
        if magnitude < -4:
            round_output = 2 - magnitude
    return round_output


def __cluster_stage(
    df_s: pd.DataFrame, ext: List[int], num_ts_cl: int
) -> Tuple[np.ndarray, pd.DataFrame]:
    """
    Cluster the time series of a stage into exactly num_ts_cl clustered time
    steps. Every extreme period forms a cluster of its own, all other horizon
    time steps are clustered with tsam (hierarchical clustering). Clusters
    are numbered in order of their first appearance in the time horizon.

    :param df_s: Time series of a stage, one column per series and one row
        per horizon time step
    :type df_s: pd.DataFrame
    :param ext: Positions of the extreme periods (see __find_extreme_periods)
    :type ext: List[int]
    :param num_ts_cl: Number of clustered time steps. Must be larger than the
        number of extreme periods and smaller than the number of horizon time
        steps
    :type num_ts_cl: int
    :return: The cluster (0-based) of every horizon time step, and the
        clustered time series with rows indexed by clustered time step 1, 2, ...
    :rtype: Tuple[np.ndarray, pd.DataFrame]
    """
    num_ts_hor = len(df_s)
    num_ts_reg = num_ts_cl - len(ext)
    is_ext = np.zeros(num_ts_hor, dtype=bool)
    is_ext[ext] = True
    pos_reg = np.flatnonzero(~is_ext)

    # Cluster the regular time steps. Every tsam period is a single time step,
    # so the order of the time steps is irrelevant and they can be re-indexed
    # contiguously after removing the extreme periods. tsam's own handling of
    # extreme periods is not used, as it does not guarantee the number of
    # clusters
    df_reg = df_s.iloc[pos_reg].copy()
    df_reg.index = pd.to_datetime(np.arange(1, len(pos_reg) + 1), unit="h")
    agg = tsam.TimeSeriesAggregation(
        df_reg,
        noTypicalPeriods=num_ts_reg,
        hoursPerPeriod=1,
        clusterMethod="hierarchical",
        extremePeriodMethod="None",
        rescaleClusterPeriods=False,
        roundOutput=__round_output(df_s),
        representationMethod="durationRepresentation",
    )
    df_typ = agg.createTypicalPeriods().reset_index(drop=True)

    # Cluster of every horizon time step (extreme periods are appended after
    # the regular clusters), then renumber by first appearance
    order = np.empty(num_ts_hor, dtype=int)
    order[pos_reg] = np.asarray(agg.clusterOrder, dtype=int)
    order[ext] = num_ts_reg + np.arange(len(ext))
    labels, first_pos = np.unique(order, return_index=True)
    if len(labels) != num_ts_cl or len(df_typ) != num_ts_reg:
        raise exceptions.EhubXException(
            f"tsam clustering returned {len(labels) - len(ext)} instead of the "
            f"requested {num_ts_reg} regular clusters",
            module=LOG_MODULE_STR,
        )
    relabel = np.empty(num_ts_cl, dtype=int)
    relabel[labels[np.argsort(first_pos)]] = np.arange(num_ts_cl)
    order = relabel[order]

    # Clustered time series: tsam's typical periods for the regular clusters,
    # the original values for the extreme periods
    vals_old = np.vstack([df_typ[df_s.columns].to_numpy(), df_s.to_numpy()[ext]])
    vals = np.empty_like(vals_old)
    vals[relabel] = vals_old
    df_cl = pd.DataFrame(vals, columns=df_s.columns)
    df_cl.index = df_cl.index + 1
    return order, df_cl


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
        df_data[col_id] = [series.get_value(t).to_float() for t in horizon_ids]

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
