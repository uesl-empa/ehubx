"""Common writer module, responsible for recurring tasks having to do with file
and directory management"""
import os
import shutil
from typing import Optional, Union
from datetime import datetime
from enum import Enum
import pandas as pd
from ehubx.core import exceptions
from ehubx.core import logging
from ehubx.data.stage_data import StageId
from ehubx.data.time_data import Times
from ehubx.data.time_series import TimeSeries

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
COL_WINDPARK: str = "Windpark"
COL_LOADSHIFT: str = "Load shift"
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


def create_dir(dir_path: str, add_time_to_dir: bool = False,
               dir_desc: Optional[str] = None) -> Optional[str]:
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
        if not os.path.isdir(
                os.path.abspath(os.path.join(par_path, os.pardir))):
            msg = (f"Failed to create {desc}directory at {dir_path} "
                   f"since {par_path} does not exist, and neither does its "
                   "parent directory")
            raise exceptions.EhubXException(msg, module=LOG_MODULE_STR)
        os.mkdir(par_path)
    # If directory already exists, ask for confirmation
    if os.path.isdir(dir_path):
        if len(os.listdir(dir_path)) == 0:
            os.rmdir(dir_path)
        else:
            logging.pause_console_log(write_console_entry=False)
            query_str = (f"{desc}directory {dir_path} already exists and is "
                         "nonempty. Delete files? [y/n]: ")
            answer = ""
            while answer not in {"y", "n"}:
                answer = input(query_str)
            logging.resume_console_log(write_console_entry=False)
            if answer == "n":
                logging.log(
                    "User decision: Do not overwrite existing "
                    f"{desc}directory {dir_path}", module=LOG_MODULE_STR)
                return None
            logging.log(
                f"User decision: Overwrite existing {desc}directory "
                f"{dir_path}", module=LOG_MODULE_STR)
            while os.path.exists(dir_path):
                try:
                    shutil.rmtree(dir_path)
                except PermissionError:
                    logging.pause_console_log(write_console_entry=False)
                    input(f"Failed to remove existing {desc}directory "
                          f"{dir_path}. Maybe one of its files is open in "
                          "another program? Press Enter to try again ...")
                    logging.resume_console_log(write_console_entry=False)
    # Create directory
    os.mkdir(dir_path)
    logging.log(f"Created {desc}directory {dir_path}",
                module=LOG_MODULE_STR)
    # Return directory path
    return dir_path


# ----------------------------------- #
# Static (time-independent) dataframe #
# ----------------------------------- #
def init_df_st() -> pd.DataFrame:
    df = pd.DataFrame(columns=[COL_ENTRY,
                               COL_VALUE,
                               COL_UNIT,
                               COL_STAGE,
                               COL_HUB,
                               COL_EC,
                               COL_TECH,
                               COL_NETLINK,
                               COL_NETLINKDIR,
                               COL_NETTECH,
                               COL_WINDPARK,
                               COL_LOADSHIFT,
                               COL_SOURCE,
                               COL_INPUTORRESULT])
    return df


def add_to_df_st(df: pd.DataFrame, entry: str, value: Union[str, float, bool],
                 unit: str = "", stage: str = "", hub: str = "", ec: str = "",
                 tech: str = "", net_link: str = "", net_link_dir: str = "",
                 net_tech: str = "", windpark: str = "", load_shift: str = "",
                 source: str = "", in_res: str = "") -> None:
    df.loc[df.shape[0]] = [entry, value, unit, stage, hub, ec, tech, net_link,
                           net_link_dir, net_tech, windpark, load_shift,
                           source, in_res]


# ------------------------- #
# Time-dependent dataframes #
# ------------------------- #
def init_df_ts_hor(times: Times) -> pd.DataFrame:
    col_ids = pd.MultiIndex.from_tuples([],
                                        names=[COL_ENTRY,
                                               COL_UNIT,
                                               COL_STAGE,
                                               COL_HUB,
                                               COL_EC,
                                               COL_TECH,
                                               COL_NETLINK,
                                               COL_NETTECH,
                                               COL_LOADSHIFT,
                                               COL_SOURCE,
                                               COL_INPUTORRESULT])
    df = pd.DataFrame(columns=col_ids)
    df.index = [t.key_as_int for t in times.ids_horizon_in_order]
    return df


def init_df_ts_cl(times: Times) -> pd.DataFrame:
    col_ids = pd.MultiIndex.from_tuples([],
                                        names=[COL_ENTRY,
                                               COL_UNIT,
                                               COL_STAGE,
                                               COL_HUB,
                                               COL_EC,
                                               COL_TECH,
                                               COL_NETLINK,
                                               COL_NETTECH,
                                               COL_LOADSHIFT,
                                               COL_SOURCE,
                                               COL_INPUTORRESULT])
    df = pd.DataFrame(columns=col_ids)
    df.index = [t.key_as_int for t in times.ids_in_order]
    return df


def add_to_df_ts_hor(df_ts_hor: pd.DataFrame,
        times: Times, entry: str, series: TimeSeries, unit: str = "",
        stage: str = "", hub: str = "", ec: str = "", tech: str = "",
        net_link: str = "", net_tech: str = "", source: str = "",
        load_shift: str = "", in_res: str = "") -> None:
    new_id = (entry, unit, stage, hub, ec, tech, net_link, net_tech,
              load_shift, source, in_res)

    if new_id in df_ts_hor:
        raise exceptions.EhubXException(
            "Cannot add time series for output formating because of a "
            "duplicate id issue", module=LOG_MODULE_STR)
    df_ts_hor[new_id] = [series.get_value(t)
                         for t in times.ids_horizon_in_order]


def add_to_df_ts_cl(df_ts_hor: pd.DataFrame,
        df_ts_cl: Optional[pd.DataFrame], times: Times, entry: str,
        series: TimeSeries, unit: str = "", stage: str = "", hub: str = "",
        ec: str = "", tech: str = "", net_link: str = "", net_tech: str = "",
        load_shift: str = "", source: str = "", in_res: str = "") -> None:
    new_id = (entry, unit, stage, hub, ec, tech, net_link, net_tech,
              load_shift, source, in_res)

    if times.is_clustered:
        # Clustering exists => Clustered series to clustered df and horizon df
        assert df_ts_cl is not None
        if new_id in df_ts_cl:
            raise exceptions.EhubXException(
                "Cannot add time series for output formating because of a "
                "duplicate id issue", module=LOG_MODULE_STR)
        df_ts_cl[new_id] = [series.get_value(t)
                            for t in times.ids_in_order]

        if new_id in df_ts_hor:
            raise exceptions.EhubXException(
                "Cannot add time series for output formating because of a "
                "duplicate id issue", module=LOG_MODULE_STR)
        df_ts_hor[new_id] = [
            series.get_value(times.get_cluster_ts(StageId(stage), t_hor))
            for t_hor in times.ids_horizon_in_order]

    if not times.is_clustered:
        # No clustering => Save time series to horizon dataframe
        if new_id in df_ts_hor:
            raise exceptions.EhubXException(
                "Cannot add time series for output formating because of a "
                "duplicate id issue", module=LOG_MODULE_STR)
        df_ts_hor[new_id] = [series.get_value(t) for t in times.ids_in_order]
