"""
Clustering data module
"""

from typing import Dict, Optional, Set, Tuple

import pandas as pd

from ehubx.data.time_data import TimeId


class ClusteringData:
    """
    Class to hold clustering data.
    """

    # ------------------ #
    # Property: time_ids #
    # ------------------ #
    @property
    def time_ids(self) -> Set[TimeId]:
        """
        Set of known time ids
        """
        return {TimeId(t) for t in range(1, self.no_ts + 1)}

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self.no_ts: int = 0
        self.horizon_map: Dict[Tuple[str, int], int] = {}
        self.weight: Dict[Tuple[str, int], int] = {}
        self.profiles: Optional[pd.DataFrame] = None
        self.errors: Optional[pd.DataFrame] = None
