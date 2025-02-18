"""Hub submodel"""
from pyomo.core import Model, Set
from datetime import datetime
from ehubx.core import logging
from ehubx.data.hub_data import Hubs

# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/hub"
"""String identifying the hub model for logging purposes"""

SET_HUB: str = "S_Hub"
"""Name of set with hub indices"""


def build(model: Model, hubs: Hubs) -> None:
    """
    Builds the hub submodel. For a mathematical description in thorough detail,
    please refer to the section 'Hub model' in the documentation.

    :param model: Pyomo model
    :type model: Model
    :param hubs: Hub data object
    :type hubs: Hubs
    """
    # Start measuring build time
    start = datetime.now()
    # [SET] Hubs
    setattr(model, SET_HUB,
            Set(initialize=[h.key for h in hubs.ids]))
    # Logging
    elapsed = datetime.now() - start
    logging.log_file(
        "Built hub module. Elapsed time: "
        f"{int(elapsed.total_seconds())}s", module=LOG_MODULE_STR)
