"""Common writer module, responsible for recurring tasks having to do with file
and directory management"""

import os
import shutil
from datetime import datetime
from enum import Enum
from typing import Optional, Union

import pandas as pd

from ehubx.core import exceptions, logging
from ehubx.data.stage_data import StageId
from ehubx.data.time_data import Times
from ehubx.data.time_series import TimeSeries
from ehubx.data.unit import Unit
from ehubx.data.value import Value


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "writ/common"
"""Module string for the common writer module for logging purposes"""

DIRNAME_PROFILES: str = "profiles"
"""Name for the profiles subdirectory in any results directory"""

COL_ENTRY: str = "Entry"
COL_VALUE: str = "Value"
COL_UNIT: str = "Unit"
COL_FILE: str = "File"
COL_STAGE: str = "Stage"
COL_HUB: str = "Hub"
COL_EC: str = "Ec"
COL_TECH: str = "Tech"
COL_NETLINK: str = "Net Link"
COL_NETLINKDIR: str = "Net Link Direction"
COL_NETTECH: str = "Net Tech"
COL_LOADSHIFT: str = "Load shift"
COL_ATESSCHEDULE: str = "ATES schedule"
COL_SOURCE: str = "Source"
COL_INPUTORRESULT: str = "Input/Result"
KEY_TIME: str = "Time"
KEY_TIMEHOR: str = "Horizon time"


class FileGranularity(Enum):
    """Setting for file granularity controlling the writing process"""

    MIN = 0
    """Minimal file granularity setting. All data will be written to the least
    possible amount of files. In particular, all tech-related data and
    demand-related data will be placed in single respective files"""

    DEFAULT = 1
    """Default file granularity setting. For techs, a single file will be
    created for every tech. All demand-related data will be placed in a single
    demand file."""

    MAX = 2
    """Maximal file granularity setting. All data will be distributed into a
    lot of files. For techs, a single file will be created for every tech and
    additional files will be created for every tech submodule that the tech
    belongs to. For demand-related data, three individual files will be
    created for demands, load shedding and load shifting respectively. """


def create_dir(
    dir_path: str, add_time_to_dir: bool = False, dir_desc: Optional[str] = None
) -> Optional[str]:
    """
    Creates a directory. Checks whether this folder already exists and whether
    to add a timestamp to the directory name.

    :param dir_path: Base path of the directory to be created (without
        timestamp
    :type dir_path: str
    :param add_time_to_dir: Whether a timestamp will be added to the
        requested directory name, defaults to False
    :type add_time_to_dir: bool
    :param dir_desc: Description of the directory to be created, defaults to
        None
    :type dir_desc: str, optional
    :return: Path of the created directory
    :rtype: Optional[str]
    """
    # Add timestamp
    if dir_path.endswith(".csv"):
        dir_path = dir_path[:-4]
    if add_time_to_dir:
        dir_path += f"_{datetime.now().strftime('%Y-%m-%d_%H-%M')}"
    par_path = os.path.abspath(os.path.join(dir_path, os.path.pardir))
    # Description string
    desc = f"{dir_desc} " if dir_desc else ""
    # Parent directory must exist
    if not os.path.isdir(par_path):
        if not os.path.isdir(os.path.abspath(os.path.join(par_path, os.pardir))):
            msg = (
                f"Failed to create {desc}directory at {dir_path} "
                f"since {par_path} does not exist, and neither does its "
                "parent directory"
            )
            raise exceptions.EhubXException(msg, module=LOG_MODULE_STR)
        os.mkdir(par_path)
    # If directory already exists, ask for confirmation
    if os.path.isdir(dir_path):
        if len(os.listdir(dir_path)) == 0:
            os.rmdir(dir_path)
        else:
            logging.pause_console_log(write_console_entry=False)
            query_str = (
                f"{desc}directory {dir_path} already exists and is "
                "nonempty. Delete files? [y/n]: "
            )
            answer = ""
            while answer not in {"y", "n"}:
                answer = input(query_str)
            logging.resume_console_log(write_console_entry=False)
            if answer == "n":
                logging.log(
                    "User decision: Do not overwrite existing "
                    f"{desc}directory {dir_path}",
                    module=LOG_MODULE_STR,
                )
                return None
            logging.log(
                f"User decision: Overwrite existing {desc}directory {dir_path}",
                module=LOG_MODULE_STR,
            )
            while os.path.exists(dir_path):
                try:
                    shutil.rmtree(dir_path)
                except PermissionError:
                    logging.pause_console_log(write_console_entry=False)
                    input(
                        f"Failed to remove existing {desc}directory "
                        f"{dir_path}. Maybe one of its files is open in "
                        "another program? Press Enter to try again ..."
                    )
                    logging.resume_console_log(write_console_entry=False)
    # Create directory
    os.mkdir(dir_path)
    logging.log(f"Created {desc}directory {dir_path}", module=LOG_MODULE_STR)
    # Return directory path
    return dir_path


# ----------------------------------- #
# Static (time-independent) dataframe #
# ----------------------------------- #
class DfStColumn(Enum):
    ENTRY = COL_ENTRY
    VALUE = COL_VALUE
    UNIT = COL_UNIT
    STAGE = COL_STAGE
    HUB = COL_HUB
    EC = COL_EC
    TECH = COL_TECH
    NET_LINK = COL_NETLINK
    NET_LINK_DIR = COL_NETLINKDIR
    NET_TECH = COL_NETTECH
    LOAD_SHIFT = COL_LOADSHIFT
    ATES_SCHEDULE = COL_ATESSCHEDULE
    SOURCE = COL_SOURCE
    INPUT_OR_RESULT = COL_INPUTORRESULT


class DfStBuilder:
    def __init__(self) -> None:
        self._rows: list[dict[DfStColumn, Optional[str]]] = []

    def add_row(
        self,
        entry: str,
        value: Union[str, Value, bool],
        unit: Optional[Unit] = None,
        stage: Optional[str] = None,
        hub: Optional[str] = None,
        ec: Optional[str] = None,
        tech: Optional[str] = None,
        net_link: Optional[str] = None,
        net_link_dir: Optional[str] = None,
        net_tech: Optional[str] = None,
        load_shift: Optional[str] = None,
        ates_schedule: Optional[str] = None,
        source: Optional[str] = None,
        in_res: Optional[str] = None,
    ) -> None:
        unit_str: Optional[str] = None
        value_str: Optional[str] = None
        if isinstance(value, Value):
            if unit is None:
                unit = value.unit
            unit_str = f"{unit}"
            value_str = f"{value.to_float(unit=unit)}"
        else:
            if unit is not None:
                unit_str = f"{unit}"
            value_str = f"{value}"
        row = {
            DfStColumn.ENTRY: entry,
            DfStColumn.VALUE: value_str,
            DfStColumn.UNIT: unit_str,
            DfStColumn.STAGE: stage,
            DfStColumn.HUB: hub,
            DfStColumn.EC: ec,
            DfStColumn.TECH: tech,
            DfStColumn.NET_LINK: net_link,
            DfStColumn.NET_LINK_DIR: net_link_dir,
            DfStColumn.NET_TECH: net_tech,
            DfStColumn.LOAD_SHIFT: load_shift,
            DfStColumn.ATES_SCHEDULE: ates_schedule,
            DfStColumn.SOURCE: source,
            DfStColumn.INPUT_OR_RESULT: in_res,
        }
        self._rows.append(row)

    def build(self, drop_columns: Optional[set[DfStColumn]] = None) -> pd.DataFrame:
        if drop_columns is None:
            drop_columns = set()

        # Build dataframe with all possible columns first
        data = [{c.value: row.get(c) for c in DfStColumn} for row in self._rows]
        df = pd.DataFrame(data, columns=[c.value for c in DfStColumn])

        # Drop the specified columns
        explicit_drop = {c.value for c in drop_columns}
        if explicit_drop:
            df = df.drop(columns=explicit_drop, errors="ignore")

        return df


# ------------------------- #
# Time-dependent dataframes #
# ------------------------- #
def init_df_ts_hor(times: Times) -> pd.DataFrame:
    col_ids = pd.MultiIndex.from_tuples(
        [],
        names=[
            COL_ENTRY,
            COL_UNIT,
            COL_STAGE,
            COL_HUB,
            COL_EC,
            COL_TECH,
            COL_NETLINK,
            COL_NETTECH,
            COL_LOADSHIFT,
            COL_ATESSCHEDULE,
            COL_SOURCE,
            COL_INPUTORRESULT,
        ],
    )
    df = pd.DataFrame(columns=col_ids)
    df.index = [t.key_as_int for t in times.ids_horizon_in_order]
    return df


def init_df_ts_cl(times: Times) -> pd.DataFrame:
    col_ids = pd.MultiIndex.from_tuples(
        [],
        names=[
            COL_ENTRY,
            COL_UNIT,
            COL_STAGE,
            COL_HUB,
            COL_EC,
            COL_TECH,
            COL_NETLINK,
            COL_NETTECH,
            COL_LOADSHIFT,
            COL_ATESSCHEDULE,
            COL_SOURCE,
            COL_INPUTORRESULT,
        ],
    )
    df = pd.DataFrame(columns=col_ids)
    df.index = [t.key_as_int for t in times.ids_in_order]
    return df


def add_to_df_ts_hor(
    df_ts_hor: pd.DataFrame,
    times: Times,
    entry: str,
    series: TimeSeries,
    unit: Unit,
    stage: str = "",
    hub: str = "",
    ec: str = "",
    tech: str = "",
    net_link: str = "",
    net_tech: str = "",
    source: str = "",
    load_shift: str = "",
    ates_schedule: str = "",
    in_res: str = "",
) -> None:
    new_id = (
        entry,
        str(unit),
        stage,
        hub,
        ec,
        tech,
        net_link,
        net_tech,
        load_shift,
        ates_schedule,
        source,
        in_res,
    )

    if new_id in df_ts_hor:
        raise exceptions.EhubXException(
            "Cannot add time series for output formating because of a "
            "duplicate id issue",
            module=LOG_MODULE_STR,
        )
    df_ts_hor[new_id] = [
        series.get_value(t).to_float(unit=unit) for t in times.ids_horizon_in_order
    ]


def add_to_df_ts_cl(
    df_ts_hor: pd.DataFrame,
    df_ts_cl: Optional[pd.DataFrame],
    times: Times,
    entry: str,
    series: TimeSeries,
    unit: Unit,
    stage: str = "",
    hub: str = "",
    ec: str = "",
    tech: str = "",
    net_link: str = "",
    net_tech: str = "",
    load_shift: str = "",
    ates_schedule: str = "",
    source: str = "",
    in_res: str = "",
) -> None:
    new_id = (
        entry,
        str(unit),
        stage,
        hub,
        ec,
        tech,
        net_link,
        net_tech,
        load_shift,
        ates_schedule,
        source,
        in_res,
    )

    if times.is_clustered:
        # Clustering exists => Clustered series to clustered df and horizon df
        assert df_ts_cl is not None
        if new_id in df_ts_cl:
            raise exceptions.EhubXException(
                "Cannot add time series for output formating because of a "
                "duplicate id issue",
                module=LOG_MODULE_STR,
            )
        df_ts_cl[new_id] = [
            series.get_value(t).to_float(unit=unit) for t in times.ids_in_order
        ]

        if new_id in df_ts_hor:
            raise exceptions.EhubXException(
                "Cannot add time series for output formating because of a "
                "duplicate id issue",
                module=LOG_MODULE_STR,
            )
        df_ts_hor[new_id] = [
            series.get_value(times.get_cluster_ts(StageId(stage), t_hor)).to_float(
                unit=unit
            )
            for t_hor in times.ids_horizon_in_order
        ]

    if not times.is_clustered:
        # No clustering => Save time series to horizon dataframe
        if new_id in df_ts_hor:
            raise exceptions.EhubXException(
                "Cannot add time series for output formating because of a "
                "duplicate id issue",
                module=LOG_MODULE_STR,
            )
        df_ts_hor[new_id] = [
            series.get_value(t).to_float(unit=unit) for t in times.ids_in_order
        ]
