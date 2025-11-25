import collections
import os
from enum import Enum
from typing import List, Optional

import pandas as pd

from ehubx.core import logging
from ehubx.parser import exceptions


class HeaderId(Enum):
    STAGEID = "stage_id"
    HUBID = "hub_id"
    NETLINKID = "net_link_id"
    TECHID = "tech_id"
    ECID = "ec_id"
    LOADSHIFTID = "loadshift_id"
    ATESSCHEDULEID = "ates_schedule_id"
    TIMEID = "time_id"
    PROFILEKEY = "profile_key"
    UNIT = "unit"


# Literals
LOG_MODULE_STR: str = "pars/csv"
FILETYPE_CSV: str = "CSV"
ATTR_UNIT: str = "unit"


def parse(file_path: str, header_ids: Optional[List[HeaderId]] = None) -> pd.DataFrame:
    if not os.path.isfile(file_path):
        raise exceptions.MissingFileException(
            file_path, FILETYPE_CSV, module=LOG_MODULE_STR
        )
    if header_ids is None:
        header_ids = []
    header_ids_as_str = [header_id.value for header_id in header_ids]
    _check_header(file_path, header_ids_as_str)
    while True:
        try:
            df = pd.read_csv(file_path, header=list(range(len(header_ids))))
            break
        except PermissionError:
            logging.pause_console_log(write_console_entry=False)
            input(
                f"Failed to read file {file_path} because of lacking "
                "permissions. Maybe it is blocked by another program? "
                "Press Enter to try again ..."
            )
            logging.resume_console_log(write_console_entry=False)
        except pd.errors.ParserError:
            logging.pause_console_log(write_console_entry=False)
            input(
                f"Pandas failed to parse file {file_path}. Probably it has "
                "invalid csv structure. Press Enter to try again ..."
            )
            logging.resume_console_log(write_console_entry=False)
    df = _format(df, header_ids_as_str, file_path)
    return df


def _check_header(file_path: str, header_ids_as_str: List[str]) -> None:
    while True:
        try:
            df_preview = pd.read_csv(
                file_path, nrows=len(header_ids_as_str), header=None
            )
            break
        except PermissionError:
            logging.pause_console_log(write_console_entry=False)
            input(
                f"Failed to read file {file_path} because of lacking "
                "permissions. Maybe it is blocked by another program? "
                "Press Enter to try again ..."
            )
            logging.resume_console_log(write_console_entry=False)
        except pd.errors.ParserError:
            logging.pause_console_log(write_console_entry=False)
            input(
                f"Pandas failed to parse file {file_path}. Probably it has "
                "invalid csv structure. Press Enter to try again ..."
            )
            logging.resume_console_log(write_console_entry=False)
        except pd.errors.EmptyDataError as exc:
            raise exceptions.ParsingException(
                file_path, "File is empty", module=LOG_MODULE_STR
            ) from exc
    header_ids_in_csv = {
        df_preview.loc[row_pos, 0] for row_pos in range(len(header_ids_as_str))
    }
    missing_header_ids = set(header_ids_as_str).difference(header_ids_in_csv)
    if len(missing_header_ids) > 0:
        msg = (
            "csv_parser could not find the expected header ids "
            + f"{missing_header_ids} (located in the starting rows of the "
            + "first column)"
        )
        raise exceptions.ParsingException(file_path, msg, module=LOG_MODULE_STR)
    # Check for header duplicates
    headers = [
        tuple(df_preview[col_no]) for col_no in range(1, len(df_preview.columns + 1))
    ]
    header_dupes = [
        header for header, cnt in collections.Counter(headers).items() if cnt > 1
    ]
    if len(header_dupes) > 0:
        msg = (
            "csv_parser encountered duplicate headers "
            + f"{set(header_dupes)} (located in the starting rows)"
        )
        raise exceptions.ParsingException(file_path, msg, module=LOG_MODULE_STR)


def _format(
    df: pd.DataFrame, header_ids_as_str: List[str], file_path: str
) -> pd.DataFrame:
    df.columns = df.columns.set_names(df.columns[0])
    df = df.set_index(df[df.columns[0]])
    df.index = df.index.set_names([HeaderId.TIMEID.value])
    df = df.drop(columns=[df.columns[0]])

    # Reorder levels
    df.columns = df.columns.reorder_levels(order=header_ids_as_str)
    df = df.sort_index(axis=1)

    # Determine units row (if it exists), otherwise assign empty strings
    unit_row_name = HeaderId.UNIT.value
    if unit_row_name in df.index:
        df.columns = df.columns.reorder_levels(order=header_ids_as_str)
        df = df.sort_index(axis=1)

        units = (
            df.loc[unit_row_name]
            .fillna("")
            .apply(
                (
                    lambda x: str(int(x))
                    if isinstance(x, float) and x.is_integer()
                    else str(x)
                )
            )
        )
        df = df.drop(index=unit_row_name)
    else:
        df.columns = df.columns.reorder_levels(order=header_ids_as_str)
        df = df.sort_index(axis=1)

        units = pd.Series([""] * df.shape[1], index=df.columns)

    # Store units as column metadata
    df.attrs[ATTR_UNIT] = units.to_dict()

    # Coerce to numeric values
    df = df.apply(pd.to_numeric, errors="coerce")

    # Check for nans
    num_coerced = df.isna().sum().sum()
    if num_coerced > 0:
        logging.log_warning(
            f"csv_parser found {num_coerced} NaN values while parsing {file_path}. "
            f"They will be replaced with 0 but please make sure that this is intended.",
            module=LOG_MODULE_STR,
        )
    df = df.fillna(0)

    return df
