"""Stage submodel"""

from datetime import datetime

from pyomo.core import Model, Set

from ehubx.core import logging
from ehubx.data.energy_system_data import EnergySystem


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/stage"
"""String identifying the stage model for logging purposes"""

SET_STAGE: str = "S_Stage"
"""Name of set with stage indices"""


def build(model: Model, system: EnergySystem) -> None:
    """
    Builds the stage submodel. For a mathematical description in thorough
    detail, please refer to the section 'Stage model' in the documentation.

    :param model: Pyomo model
    :type model: Model
    :param system: Energy system data
    :type system: EnergySystem
    """
    stages = system.stages
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
