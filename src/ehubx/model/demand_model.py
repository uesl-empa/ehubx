"""Demand submodel"""

from datetime import datetime

from pyomo.core import Model, Param, Set

from ehubx.core import common, logging
from ehubx.data.demand_data import Demands
from ehubx.data.stage_data import Stages
from ehubx.data.time_data import Times
from ehubx.model.ec_model import SET_EC
from ehubx.model.hub_model import SET_HUB
from ehubx.model.stage_model import SET_STAGE


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/demand"
"""String identifying the demand model for logging purposes"""

SET_DEMANDTUPLE: str = "S_DemandTuple"
"""Name of set for demand tuples"""

PAR_BIGMGENERIC: str = "P_BigMGeneric"
"""Name of generic big-M parameter based on demand data values"""


def build(model: Model, stages: Stages, demands: Demands, times: Times) -> None:
    """
    Builds the demand submodel. For a mathematical description in thorough
    detail, please refer to the section 'Demand model' in the documentation.

    :param model: Pyomo model
    :type model: Model
    :param stages: Stage data object
    :type stages: Stages
    :param demands: Demand data object
    :type demands: Demands
    :param times: Time data object
    :type times: Times
    """
    # Start measuring build time
    start = datetime.now()
    # [SET] Tuples (s, h, e) with demand values
    setattr(
        model,
        SET_DEMANDTUPLE,
        Set(
            within=(
                getattr(model, SET_STAGE)
                * getattr(model, SET_HUB)
                * getattr(model, SET_EC)
            ),
            initialize=[(s.key, h.key, e.key) for (s, h, e) in demands.tuples],
        ),
    )

    # [PAR] Generic value for bigM based on demand data
    demand_sum_per_ts = [
        sum(
            [
                demands.get_demand(s2, h, e).get_value(t)
                for (s2, h, e) in demands.tuples
                if s == s2
            ]
        )
        for s in stages.ids
        for t in times.ids
    ]
    bigm_generic = 1e6
    if max(demand_sum_per_ts) < common.EPS_ZEROCHECK:
        logging.log_file_warning(
            "Model has no demand data to compute a generic big-M parameter. "
            "Using 1e6 instead ...",
            module=LOG_MODULE_STR,
        )
    else:
        bigm_generic = 1000 * max(demand_sum_per_ts) + common.EPS_BIGM
        logging.log_file(
            f"Calculated generic big-M parameter of {bigm_generic} "
            "based on demand data.",
            module=LOG_MODULE_STR,
        )
    setattr(model, PAR_BIGMGENERIC, Param(initialize=bigm_generic))
    # Logging
    elapsed = datetime.now() - start
    logging.log_file(
        f"Built demand module. Elapsed time: {int(elapsed.total_seconds())}s",
        module=LOG_MODULE_STR,
    )
