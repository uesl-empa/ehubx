"""Demand submodel"""

from datetime import datetime
from typing import Dict, Tuple

from pyomo.core import Constraint, Model, NonNegativeReals, Set, Var

from ehubx.core import logging
from ehubx.data.demand_data import Demands
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId
from ehubx.data.time_data import Times
from ehubx.data.unit import MassUnit, PowerUnit, TimeUnit
from ehubx.model.ec_model import SET_EC, get_ec_model_unit
from ehubx.model.hub_model import SET_HUB
from ehubx.model.stage_model import SET_STAGE
from ehubx.model.times_model import SET_TIME


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/demand"
"""String identifying the demand model for logging purposes"""

SET_DEMANDTUPLE: str = "S_DemandTuple"
"""Name of set for demand tuples"""

SET_DEMANDPROFILETUPLE: str = "S_DemandProfileTuple"
"""Name of set for demand-profile tuples"""

SET_DEMANDSUMTUPLE: str = "S_DemandSumTuple"
"""Name of set for demand-sum tuples"""

VAR_DEMANDSUPPLY: str = "V_DemandSupply"
"""Name of variable for demand supply"""

CON_DEMANDSUPPLYSUM: str = "C_DemandSupplySum"
"""Name of constraint fixing the demand supply for demand-sums"""


def build(model: Model, system: EnergySystem) -> None:
    """
    Builds the demand submodel. For a mathematical description in thorough detail,
    please refer to the section 'Demand Model' in the documentation.
    :param model: Pyomo model
    :type model: Model
    :param system: Energy system data
    :type system: EnergySystem
    """
    # Extract data from modules
    ecs = system.ecs
    demands = system.demands
    times = system.times
    mass_unit = system.mass_unit
    power_unit = system.power_unit
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
    # [SET] Tuples (s, h, e) with demand-profile values
    setattr(
        model,
        SET_DEMANDPROFILETUPLE,
        Set(
            within=getattr(model, SET_DEMANDTUPLE),
            initialize=[(s.key, h.key, e.key) for (s, h, e) in demands.profile_tuples],
        ),
    )
    # [SET] Tuples (s, h, e) with demand-sum values
    setattr(
        model,
        SET_DEMANDSUMTUPLE,
        Set(
            within=getattr(model, SET_DEMANDTUPLE),
            initialize=[(s.key, h.key, e.key) for (s, h, e) in demands.sum_tuples],
        ),
    )

    # [VAR] Supply to demand-side
    setattr(
        model,
        VAR_DEMANDSUPPLY,
        Var(
            getattr(model, SET_DEMANDTUPLE),
            getattr(model, SET_TIME),
            within=NonNegativeReals,
        ),
    )

    # [CON] Constraint demand supply for tuples with demand-sum
    _con_demand_supply_sum(model, ecs, demands, times, mass_unit, power_unit)

    # [PAR] Generic value for bigM based on demand data
    demand_sum_per_tuple: Dict[Tuple[StageId, HubId, EcId], float] = {}
    for s, h, e in demands.profile_tuples:
        unit = get_ec_model_unit(ecs.get_unit(e), mass_unit, power_unit) / TimeUnit.H
        demand_profile = demands.get_demand_profile(s, h, e)
        demand_sum_per_tuple[s, h, e] = sum(
            times.get_weight(s, t) * demand_profile.get_value(t).to_float(unit=unit)
            for t in times.ids
        )
    for s, h, e in demands.sum_tuples:
        unit = get_ec_model_unit(ecs.get_unit(e), mass_unit, power_unit)
        demand_sum = demands.get_demand_sum(s, h, e)
        demand_sum_per_tuple[(s, h, e)] = demand_sum.to_float(unit=unit)
    # Logging
    elapsed = datetime.now() - start
    logging.log_file(
        f"Built demand module. Elapsed time: {int(elapsed.total_seconds())}s",
        module=LOG_MODULE_STR,
    )


def _con_demand_supply_sum(
    model: Model,
    ecs: Ecs,
    demands: Demands,
    times: Times,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
) -> None:
    def __rule_demand_supply_sum(model, s, h, e):
        # Get demand-sum
        demand_sum = demands.get_demand_sum(StageId(s), HubId(h), EcId(e))
        # Calculate total supply
        total_supply = sum(
            times.get_weight(StageId(s), t)
            * getattr(model, VAR_DEMANDSUPPLY)[s, h, e, t.key_as_int]
            for t in times.ids
        )
        unit = get_ec_model_unit(ecs.get_unit(EcId(e)), mass_unit, power_unit)
        # Set contraint
        return total_supply == demand_sum.to_float(unit=unit)

    setattr(
        model,
        CON_DEMANDSUPPLYSUM,
        Constraint(
            getattr(model, SET_DEMANDSUMTUPLE),
            rule=__rule_demand_supply_sum,
        ),
    )
