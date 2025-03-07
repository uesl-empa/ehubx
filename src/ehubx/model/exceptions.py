"""Model exceptions module"""

from typing import List

from ehubx.core.exceptions import EhubXException
from ehubx.data.index import Index


class ModelException(EhubXException):
    """
    General exception that inherits from the main ehubX exception and can be
    thrown from the model module. In addition to its EhubXException properties,
    it contains a key string which can be used to identify its origin, and a
    list of indices for which the exception was thrown.
    """

    def __init__(self, key: str, indices: List[Index], msg: str, module: str = ""):
        self.key = key
        self.indices = indices
        super().__init__(msg, module)
