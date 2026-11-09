"""
Autonomy data module
"""

from enum import Enum


class AutonomyStageAggregationMethod(Enum):
    """How stage autonomies are aggregated into the system autonomy"""

    SUM = "sum"
    """System autonomy is the sum of the stage autonomies:
    V_SystemAutonomy = sum_s V_Autonomy[s]"""

    MAXMIN = "maxmin"
    """System autonomy is the autonomy of the worst stage:
    V_SystemAutonomy <= V_Autonomy[s] for all s, so maximizing it maximizes
    the minimum stage autonomy. Per-stage values of non-binding stages are
    not unique."""


class Autonomy:
    """Data and settings of the autonomy module"""

    def __init__(self) -> None:
        self.stage_aggregation_method: AutonomyStageAggregationMethod = (
            AutonomyStageAggregationMethod.SUM
        )
