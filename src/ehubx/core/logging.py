"""
Logging module. Used for console output and logfiles.
"""

import os
from datetime import datetime
from typing import List, Optional

from ehubx import __version__


# -------- #
# Literals #
# -------- #
TIME_WIDTH_FILE: int = 7
"""Number of characters in timestamp column of logfile"""

MODULE_WIDTH_FILE: int = 17
"""Number of characters in module column of logfile"""

SYMBOL_WIDTH_FILE: int = 3
"""Number of characters in symbol (None, warning or error) column of logfile"""

MAX_MODULE_LENGTH: int = 15
"""Maximal expected number of charaacters in a module string"""

MIN_LOGFILE_WIDTH: int = 80
"""Minimal number of characters in each logfile line"""

MIN_MESSAGE_WIDTH_FILE: int = 50
"""Minimal number of charaacters in message column of logfile"""

MAX_MSG_LENGTH_CONSOLE: int = 98
"""Maximal number of characters in the message column of the console log"""

LOG_MODULE_STR: str = "logging"
"""Module string for the logging module for logging purposes"""


class LoggingException(Exception):
    """
    Exception that can arise from within the logging module
    """

    def __init__(self, msg: str, module: str = ""):
        msg = ":".join([msg, module])
        super().__init__(msg)


# ---------------- #
# Module functions #
# ---------------- #
def log(msg: str, module: str = "", print_time: bool = True) -> None:
    """
    Print a message to logfile and console

    :param msg: Message to be printed
    :type msg: str
    :param module: String of the module where the log was triggered, defaults
        to ""
    :type module: str, optional
    :param print_time: Whether to add a timestamp with the current time in the
        time column of the logfile, defaults to True
    :type print_time: bool, optional
    """
    log_file(msg, module=module, print_time=print_time)
    log_console(msg, module=module)


def log_warning(msg: str, module: str = "") -> None:
    """
    Print a warning to logfile and console

    :param msg: Warning message to be printed
    :type msg: str
    :param module: String of the module where the log was triggered, defaults
        to ""
    :type module: str, optional
    """
    log_file_warning(msg, module=module)
    log_console_warning(msg, module=module)


def log_error(msg: str, module: str = "") -> None:
    """
    Print an error to logfile and console

    :param msg: Error message to be printed
    :type msg: str
    :param module: String of the module where the log was triggered, defaults
        to ""
    :type module: str, optional
    """
    log_file_error(msg, module=module)
    log_console_error(msg, module=module)


def log_console(msg: str, module: str = "") -> None:
    """
    Print a message to the console log

    :param msg: Message to be printed
    :type msg: str
    :param module: String of the module where the log was triggered, defaults
        to ""
    :type module: str, optional
    """
    # Cannot log while logger is paused
    if Logger().is_console_paused:
        raise LoggingException(
            "Tried to log while logger is paused", module=LOG_MODULE_STR
        )
    # Log
    module = _fix_str_length(module, MAX_MODULE_LENGTH)
    msg_str = [
        msg[chunk : (chunk + MAX_MSG_LENGTH_CONSOLE)]
        for chunk in range(0, len(msg), MAX_MSG_LENGTH_CONSOLE)
    ]

    print(
        (f"| {module} | " + _fix_str_length(msg_str[0], MAX_MSG_LENGTH_CONSOLE) + " |")
    )
    for i in range(1, len(msg_str)):
        print(
            (
                "| "
                + " " * 18
                + _fix_str_length(msg_str[i], MAX_MSG_LENGTH_CONSOLE)
                + " |"
            )
        )


def log_console_warning(msg: str, module: str = "") -> None:
    """
    Print a warning message to the console log

    :param msg: Warning message to be printed
    :type msg: str
    :param module: String of the module where the log was triggered, defaults
        to ""
    :type module: str, optional
    """
    log_console(f"Warning: {msg}", module=module)


def log_console_error(msg: str, module: str = "") -> None:
    """
    Print an error message to the console log

    :param msg: Error message to be printed
    :type msg: str
    :param module: String of the module where the log was triggered, defaults
        to ""
    :type module: str, optional
    """
    log_console(f"ERROR: {msg}", module=module)


def log_file(
    msg: str, module: str = "", symbol: str = " ", print_time: bool = True
) -> None:
    """
    Print a message to the logfile

    :param msg: Message to be printed
    :type msg: str
    :param module: String of the module where the log was triggered, defaults
        to ""
    :type module: str, optional
    :param print_time: Whether to add a timestamp with the current time in the
        time column of the logfile, defaults to True
    :type print_time: bool, optional
    """
    # Cannot log while logger is paused
    if Logger().is_console_paused:
        raise LoggingException(
            "Tried to log while logger is paused", module=LOG_MODULE_STR
        )
    # Log
    logger = Logger()
    if not logger.has_started:
        logger.start()
    now = datetime.now()
    cur_day = now.strftime("%d/%m/%Y")
    msg_str = _segment_msg(msg, Logger().max_msg_width_file)
    time = " " * 5
    if print_time:
        time = now.strftime("%H:%M")

    with open(logger.logfile_path, "a", encoding="utf-8") as logfile:
        if cur_day != logger.last_known_day:
            logger.last_known_day = cur_day
            logfile.write(f"Day changed to {cur_day}\n")
        logfile.write(
            (
                f"{time} | {symbol} | "
                f"{_fix_str_length(module, MAX_MODULE_LENGTH)} | "
                f"{_fix_str_length(msg_str[0], Logger().max_msg_width_file)}"
                "\n"
            )
        )
        indent = TIME_WIDTH_FILE + SYMBOL_WIDTH_FILE + MODULE_WIDTH_FILE + 3
        for i in range(1, len(msg_str)):
            logfile.write(
                (
                    " " * indent
                    + _fix_str_length(msg_str[i], Logger().max_msg_width_file)
                    + "\n"
                )
            )


def log_file_warning(msg: str, module: str = "") -> None:
    """
    Print a warning message to the logfile

    :param msg: Warning message to be printed
    :type msg: str
    :param module: String of the module where the log was triggered, defaults
        to ""
    :type module: str, optional
    """
    log_file(msg, module=module, symbol="!")


def log_file_error(msg: str, module: str = "") -> None:
    """
    Print an error message to the logfile

    :param msg: Error message to be printed
    :type msg: str
    :param module: String of the module where the log was triggered, defaults
        to ""
    :type module: str, optional
    """
    log_file(msg, module=module, symbol="X")


def pause_console_log(write_console_entry: bool = True) -> None:
    """
    Pauses the console log to allow for upcoming expected console message to be
    separated from the ehubX logs.

    :param write_console_entry: Whether to write a console log entry announcing
        the pause beforehand, defaults to True
    :type write_console_entry: bool, optional
    """
    if write_console_entry:
        log_console("Pausing console log ...", module=LOG_MODULE_STR)
    Logger().pause_console()


def resume_console_log(write_console_entry: bool = True) -> None:
    """
    Resumes a paused console log.

    :param write_console_entry: Whether to write a console log entry announcing
        that logging is resumed, defaults to True
    :type write_console_entry: bool, optional
    """
    Logger().resume_console()
    if write_console_entry:
        log_console("Resuming console log ...", module=LOG_MODULE_STR)


def set_logfile_path(logfile_path: str) -> None:
    """
    Set the location of the log file

    :param logfile_path: Log file path
    :type logfile_path: str
    """
    Logger().set_logfile_path(logfile_path)


def set_max_logfile_width(logfile_width: Optional[int]) -> None:
    """
    Sets the maximal number of characters for the logfile lines

    :param logfile_width: Maximal number of characters in each logfile line,
        should not be smaller than MIN_LOGFILE_WIDTH
    :type logfile_width: Optional[int]
    """
    if logfile_width and logfile_width < MIN_LOGFILE_WIDTH:
        logfile_width = MIN_LOGFILE_WIDTH
    Logger().max_logfile_width = logfile_width


def _fix_str_length(string: str, length: Optional[int]) -> str:
    if length is None:
        return string
    return string.ljust(length)[:length]


def _segment_msg(msg: str, max_length: Optional[int]) -> List[str]:
    if max_length is None:
        return [msg]
    return [
        msg[chunk : (chunk + max_length)] for chunk in range(0, len(msg), max_length)
    ]


class Logger:
    """
    Singleton class responsible for logging to files and the console
    """

    last_known_day: Optional[str] = None
    """Last known day that a log occured"""
    _logfile_path: Optional[str] = None
    _has_started: bool = False
    _is_console_paused: bool = False
    _max_logfile_width: Optional[int] = None
    _max_msg_width_file: Optional[int] = None

    @property
    def has_started(self) -> bool:
        """
        Whether or not the logging procedure has been started
        """
        return self._has_started

    @property
    def is_console_paused(self) -> bool:
        """
        Whether or not the console is currently paused
        """
        return self._is_console_paused

    @property
    def logfile_path(self) -> str:
        """
        Current path to the logfile, or empty string if it is not set
        """
        if self._logfile_path is None:
            return ""
        return self._logfile_path

    def set_logfile_path(self, logfile_path: str) -> None:
        """
        Sets the path to the logfile and starts the logging process

        :param logfile_path: Path to the logfile
        :type logfile_path: str
        """

        fail_msg = f"Unable to set log file path to {logfile_path}"
        if os.path.isdir(logfile_path):
            fail_msg += " (the path exists as a directory)"
            raise LoggingException(fail_msg, module=LOG_MODULE_STR)
        dir_name = os.path.dirname(logfile_path)
        if not (os.path.isdir(dir_name) or dir_name == ""):
            fail_msg += " (parent directory does not exist)"
            raise LoggingException(fail_msg, module=LOG_MODULE_STR)
        if not os.path.splitext(logfile_path)[-1] == ".log":
            logfile_path += ".log"
        self._logfile_path = logfile_path
        self.start()
        log_console(f"Log file path set to {logfile_path}", module=LOG_MODULE_STR)

    @property
    def max_logfile_width(self) -> Optional[int]:
        """
        Maximal number of characters in each logfile line
        """
        return self._max_logfile_width

    @max_logfile_width.setter
    def max_logfile_width(self, max_logfile_width: Optional[int]) -> None:
        self._max_logfile_width = max_logfile_width

    @property
    def max_msg_width_file(self) -> Optional[int]:
        """
        Maximal number of characters in the message column of the logfile
        """
        if not self._max_logfile_width:
            return None
        return (
            self._max_logfile_width
            - TIME_WIDTH_FILE
            - SYMBOL_WIDTH_FILE
            - MODULE_WIDTH_FILE
            - 3
        )

    def start(self) -> None:
        """
        Create the logfile, write header and initial entry,
        and mark the Logger as started
        """
        # Check if logfile path exists
        if self._logfile_path is None:
            raise LoggingException(
                "Tried to start log while logfile path if not set",
                module=LOG_MODULE_STR,
            )
        now = datetime.now()
        self.last_known_day = now.strftime("%d/%m/%Y")
        header_width = MIN_LOGFILE_WIDTH
        if self.max_logfile_width:
            header_width = self.max_logfile_width
        with open(self._logfile_path, "w", encoding="utf-8") as logfile:
            logfile.write("/" + "=" * (header_width - 2) + "\\\n")
            logfile.write("|" + " " * (int(header_width / 2) - 5) + "ehubX log\n")
            logfile.write(f"| Version: {__version__}\n")
            logfile.write("=" * header_width + "\n")
            module_str = _fix_str_length("Module", MAX_MODULE_LENGTH)
            msg_str = _fix_str_length("Message", Logger().max_msg_width_file)
            logfile.write(f"Time  | ? | {module_str} | {msg_str}\n")
            logfile.write("-" * header_width + "\n")
        self._has_started = True
        log_file(f"Started logfile on {self.last_known_day}", module="logging")
        print("=" * 120)
        print("|" + " " * 55 + "ehubX log" + " " * 54 + "|")
        version_str = _fix_str_length(
            f"Version: {__version__}", MAX_MSG_LENGTH_CONSOLE + 18
        )
        print("| " + version_str + " |")
        print("=" * 120)
        print("| Module          | Message" + " " * 92 + "|")
        print("-" * 120)

    def pause_console(self) -> None:
        """
        Pause the console log, allowing to allow for upcoming expected console
        message to be separated from the ehubX logs
        """
        if not self._has_started:
            raise LoggingException(("Tried to pause a logger that has not started yet"))
        print("-" * 120 + "\n")
        self._is_console_paused = True

    def resume_console(self) -> None:
        """
        Resume console log
        """
        if not self._is_console_paused:
            raise LoggingException(("Tried to resume a logger that is not paused"))
        print("\n" + "-" * 120)
        self._is_console_paused = False

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(Logger, cls).__new__(cls)
            cls.instance._has_started = False
            cls.instance._logfile_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "ehubX.log")
            )
        return cls.instance
