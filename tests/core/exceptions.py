"""
Top-level exception module
"""

from ehubx.core import logging


class EhubXException(Exception):
    """
    Top-level ehubX exception. Contains an exception message and a string for
    the module where it was thrown.
    """

    def __init__(self, msg: str, module: str = ""):
        logging.log_error(msg, module=module)
        super().__init__(msg)
