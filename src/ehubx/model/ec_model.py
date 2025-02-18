"""Energy carrier (ec) submodel"""
from pyomo.core import Model, Set
from datetime import datetime
from ehubx.core import logging
from ehubx.data.ec_data import Ecs

# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/ec"
"""String identifying the ec model for logging purposes"""

SET_EC: str = "S_Ec"
"""Name of set of ec indices"""


def build(model: Model, ecs: Ecs) -> None:
    """
    Builds the energy carrier (ec) submodel. For a mathematical description
    in thorough detail, please refer to the section 'Ec model' in the
    documentation.

    :param model: Pyomo model
    :type model: Model
    :param ecs: Energy carrier data object
    :type ecs: Ecs
    """
    # Start measuring build time
    start = datetime.now()
    # [SET] Energy carriers
    setattr(model, SET_EC, Set(initialize=[e.key for e in ecs.ids]))
    # Logging
    elapsed = datetime.now() - start
    logging.log_file(
        "Built ec module. Elapsed time: "
        f"{int(elapsed.total_seconds())}s", module=LOG_MODULE_STR)
