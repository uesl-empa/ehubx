"""Time submodel"""
from pyomo.core import Model, Set
from datetime import datetime
from ehubx.core import logging
from ehubx.data.time_data import Times

# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/time"
"""String identifying the time model for logging purposes"""

SET_TIME: str = "S_Time"
"""Name of set with time indices"""

SET_TIMEHORIZON: str = "S_TimeHorizon"
"""Name of set with horizon time indices"""


def build(model: Model, times: Times) -> None:
    """
    Builds the time submodel. For a mathematical description in thorough
    detail, please refer to the section 'Times model' in the documentation.

    :param model: Pyomo model
    :type model: Model
    :param times: Time data object
    :type times: Times
    """
    # Start measuring build time
    start = datetime.now()
    # [SET] Times
    time_ids = [t.key_as_int for t in times.ids]
    time_ids.sort()
    setattr(model, SET_TIME,
            Set(initialize=time_ids))
    # [SET] Horizon times
    time_horizon_ids = [t.key_as_int for t in times.ids_horizon]
    time_horizon_ids.sort()
    setattr(model, SET_TIMEHORIZON,
            Set(initialize=time_horizon_ids))
    # Logging
    elapsed = datetime.now() - start
    logging.log_file(
        "Built times module. Elapsed time: "
        f"{int(elapsed.total_seconds())}s", module=LOG_MODULE_STR)
