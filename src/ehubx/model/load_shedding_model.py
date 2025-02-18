"""Load shedding submodel"""
from datetime import datetime
from pyomo.core import Constraint, Model, NonNegativeReals, Set, Var
from ehubx.core import logging
from ehubx.data.stage_data import Stages, StageId
from ehubx.data.hub_data import Hubs, HubId
from ehubx.data.ec_data import Ecs, EcId
from ehubx.data.demand_data import Demands
from ehubx.data.load_shedding_data import LoadShedding
from ehubx.data.time_data import Times, TimeId
from ehubx.model.stage_model import SET_STAGE
from ehubx.model.hub_model import SET_HUB
from ehubx.model.ec_model import SET_EC
from ehubx.model.times_model import SET_TIME

# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/load_shed"
"""String identifying the load shedding model for logging purposes"""

SET_LOADSHEDDINGTUPLE: str = "S_LoadSheddingTuple"
"""Name of set with all load shedding tuples"""

VAR_LOADSHEDDING: str = "V_LoadShedding"
"""Name of variable for load shedding amounts"""

VAR_LOADHSHEDDINGCOST: str = "V_LoadSheddingCost"
"""Name of variable for load shedding costs (per load shedding tuple)"""

VAR_LOADHSHEDDINGCOSTTOTAL: str = "V_LoadSheddingCostTotal"
"""Name of variable for total load shedding costs"""

CON_LOADSHEDDINGCOST: str = "C_LoadSheddingCost"
"""Name of constraint setting load shedding costs (per load sheddinfg tuple)"""

CON_LOADSHEDDINGCOSTTOTAL: str = "C_LoadSheddingCostTotal"
"""Name of constraint setting total load shedding costs"""

CON_LOADSHEDDINGMAX: str = "C_LoadSheddingMax"
"""Name of constraint respecting maximal load shedding values"""


def build(model: Model, stages: Stages, hubs: Hubs, ecs: Ecs, demands: Demands,
          load_shedding: LoadShedding, times: Times) -> None:
    """
    Builds the load shedding submodel. For a mathematical description
    in thorough detail, please refer to the section 'Load shedding model' in
    the documentation.

    :param model: Pyomo model
    :type model: Model
    :param stages: Stage data object
    :type stages: Stages
    :param hubs: Hub data object
    :type hubs: Hubs
    :param ecs: Energy carrier data object
    :type ecs: Ecs
    :param demands: Demand data object
    :type demands: Demands
    :param load_shedding: Load shedding data object
    :type load_shedding: LoadShedding
    :param times: Time data object
    :type times: Times
    """
    # Start measuring build time
    start = datetime.now()
    # Build
    _build_base(model, stages, hubs, ecs, demands, load_shedding)
    _build_cost(model, load_shedding, times)
    start = datetime.now()
    elapsed = datetime.now() - start
    logging.log_file(
        "Built load shedding module. Elapsed time: "
        f"{int(elapsed.total_seconds())}s", module=LOG_MODULE_STR)


def _build_base(model: Model, stages: Stages, hubs: Hubs, ecs: Ecs,
                demands: Demands, load_shedding: LoadShedding) -> None:
    # [SET] Load shedding tuples
    load_shedding_tuples = load_shedding.get_enabled_tuples(stages, hubs, ecs,
                                                            demands)
    setattr(model, SET_LOADSHEDDINGTUPLE,
            Set(within=(getattr(model, SET_STAGE)
                        * getattr(model, SET_HUB)
                        * getattr(model, SET_EC)),
                initialize=[(s.key, h.key, e.key)
                            for (s, h, e) in load_shedding_tuples]))
    # [VAR] Load shedding, i.e.; amount of demand that is not delivered
    setattr(model, VAR_LOADSHEDDING,
            Var(getattr(model, SET_LOADSHEDDINGTUPLE),
                getattr(model, SET_TIME),
                within=NonNegativeReals))
    # [CON] Enforce minimal and maximal load shedding values
    _con_load_shedding_max(model, demands, load_shedding)


def _build_cost(model: Model, load_shedding: LoadShedding,
                times: Times) -> None:
    # [VAR] Load shedding cost
    setattr(model, VAR_LOADHSHEDDINGCOST,
            Var(getattr(model, SET_LOADSHEDDINGTUPLE),
                domain=NonNegativeReals))
    # [CON] Load shedding cost
    _con_load_shedding_cost(model, load_shedding, times)
    # [VAR] Total load shedding cost
    setattr(model, VAR_LOADHSHEDDINGCOSTTOTAL, Var(domain=NonNegativeReals))
    # [CON] Total load shedding cost
    _con_load_shedding_cost_total(model)


def _con_load_shedding_cost(model: Model, load_shedding: LoadShedding,
                            times: Times) -> None:

    def __rule_load_shedding_cost(model, s, h, e):
        # Get parameters
        energy_cost = load_shedding.get_energy_cost(StageId(s), HubId(h),
                                                    EcId(e))
        # Calculate cost
        cost = sum(
            energy_cost.get_value(TimeId(t))
            * times.get_weight(StageId(s), TimeId(t))
            * getattr(model, VAR_LOADSHEDDING)[s, h, e, t]
            for t in getattr(model, SET_TIME))
        # Set constraint
        return getattr(model, VAR_LOADHSHEDDINGCOST)[s, h, e] == cost

    setattr(model, CON_LOADSHEDDINGCOST,
            Constraint(getattr(model, SET_LOADSHEDDINGTUPLE),
                       rule=__rule_load_shedding_cost))


def _con_load_shedding_cost_total(model: Model) -> None:

    def __rule_load_shedding_cost_total(model):
        # Calculate total load shedding cost
        load_shedding_cost_total = sum(
            getattr(model, VAR_LOADHSHEDDINGCOST)[s, h, e]
            for (s, h, e) in getattr(model, SET_LOADSHEDDINGTUPLE))
        # Set constraint
        return (getattr(model, VAR_LOADHSHEDDINGCOSTTOTAL)
                == load_shedding_cost_total)

    setattr(model, CON_LOADSHEDDINGCOSTTOTAL,
            Constraint(rule=__rule_load_shedding_cost_total))


def _con_load_shedding_max(model: Model, demands: Demands,
                           load_shedding: LoadShedding) -> None:

    def __rule_load_shedding_max(model, s, h, e, t):
        # Get parameters
        demand = demands.get_demand(StageId(s), HubId(h), EcId(e)
                                    ).get_value(TimeId(t))
        max_load_shedding_abs = load_shedding.get_max_abs(
            StageId(s), HubId(h), EcId(e)).get_value(TimeId(t))
        max_load_shedding_rel = load_shedding.get_max_rel(
            StageId(s), HubId(h), EcId(e)).get_value(TimeId(t))
        max_load_shedding = min(max_load_shedding_abs,
                                max_load_shedding_rel * demand)
        # Set constraint
        return (getattr(model, VAR_LOADSHEDDING)[s, h, e, t]
                <= max_load_shedding)

    setattr(model, CON_LOADSHEDDINGMAX,
            Constraint(getattr(model, SET_LOADSHEDDINGTUPLE),
                       getattr(model, SET_TIME),
                       rule=__rule_load_shedding_max))
