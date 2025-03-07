"""Stage submodel"""

from datetime import datetime

from pyomo.core import Model, Set

from ehubx.core import logging
from ehubx.data.stage_data import Stages


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/stage"
"""String identifying the stage model for logging purposes"""

SET_STAGE: str = "S_Stage"
"""Name of set with stage indices"""


def build(model: Model, stages: Stages) -> None:
    """
    Builds the stage submodel. For a mathematical description in thorough
    detail, please refer to the section 'Stage model' in the documentation.

    :param model: Pyomo model
    :type model: Model
    :param stages: Stage data class
    :type stages: Stages
    """
    # Start measuring build time
    start = datetime.now()
    # [SET] Stages
    setattr(model, SET_STAGE, Set(initialize=[s.key for s in stages.ids]))
    # Log
    elapsed = datetime.now() - start
    logging.log_file(
        f"Built stage module. Elapsed time: {int(elapsed.total_seconds())}s",
        module=LOG_MODULE_STR,
    )
