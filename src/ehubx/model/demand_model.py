"""Demand submodel"""

from datetime import datetime
from typing import Dict, Tuple

from pyomo.core import Binary, Constraint, Model, NonNegativeReals, Param, Set, Var

from ehubx.core import logging
from ehubx.data.demand_data import Demands
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId
from ehubx.data.time_data import TimeId, Times
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

VAR_DEMANDUNMET: str = "V_DemandUnmet"
"""Name of variable for unmet demand"""

PAR_DEMANDUNMETALLOWED = "P_DemandUnmetAllowed"
"""Name of parameter for allowed unmet demand"""

PAR_DEMANDSUMBIGM = "P_DemandSumBigM"
"""Name of parameter for Big-M demand sum"""

CON_DEMANDUNMETGATED = "C_DemandUnmetGated"
"""Gate unmet demand for all demand tuples (profiles use demand(t), sums use Big-M)."""

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

    # [VAR] Balance the unmet demand
    setattr(
        model,
        VAR_DEMANDUNMET,
        Var(
            getattr(model, SET_DEMANDTUPLE),
            getattr(model, SET_TIME),
            within=NonNegativeReals,
        ),
    )

    #  [PAR] Flag: 0 = unmet demand forbidden, 1 = allowed
    setattr(
        model,
        PAR_DEMANDUNMETALLOWED,
        Param(within=Binary, initialize=0, mutable=True),
    )

    S_Time = getattr(model, SET_TIME)

    # Build TimeId lookup once (robust to clustering)
    stime_to_tid = _make_stime_to_timeid_map(system.times, S_Time)

    # [CON] Constraint demand supply for tuples with demand-sum
    _con_demand_supply_sum(
        model, ecs, demands, times, mass_unit, power_unit, stime_to_tid
    )

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

    setattr(
        model,
        PAR_DEMANDSUMBIGM,
        Param(
            getattr(model, SET_DEMANDTUPLE),
            within=NonNegativeReals,
            initialize=lambda m, s, h, e: demand_sum_per_tuple.get(
                (StageId(s), HubId(h), EcId(e)), 0.0
            ),
            mutable=False,
        ),
    )

    # [CON] gate unmet demand for all demand tuples (profile + sum)
    _con_unmet_demand_gate_all(
        model, ecs, demands, times, mass_unit, power_unit, stime_to_tid
    )

    # Logging
    elapsed = datetime.now() - start
    logging.log_file(
        f"Built demand module. Elapsed time: {int(elapsed.total_seconds())}s",
        module=LOG_MODULE_STR,
    )


def _make_stime_to_timeid_map(times: Times, S_Time):
    """Map Pyomo S_Time elements to Times TimeId objects (safe with clustering)."""

    def key(x):
        return getattr(x, "key_as_int", getattr(x, "key", x))

    tid_by_key = {key(ti): ti for ti in times.ids}
    return {t_elem: tid_by_key.get(key(t_elem), TimeId(t_elem)) for t_elem in S_Time}


def _con_demand_supply_sum(
    model: Model,
    ecs: Ecs,
    demands: Demands,
    times: Times,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
    stime_to_tid,
) -> None:
    S_Time = getattr(model, SET_TIME)

    def __rule_demand_supply_sum(m, s, h, e):
        unit_energy = get_ec_model_unit(ecs.get_unit(EcId(e)), mass_unit, power_unit)

        total_served_plus_unmet = sum(
            times.get_weight(StageId(s), stime_to_tid[t_elem])
            * (
                getattr(m, VAR_DEMANDSUPPLY)[s, h, e, t_elem]
                + getattr(m, VAR_DEMANDUNMET)[s, h, e, t_elem]
            )
            for t_elem in S_Time
        )

        demand_sum = demands.get_demand_sum(StageId(s), HubId(h), EcId(e)).to_float(
            unit=unit_energy
        )
        return total_served_plus_unmet == demand_sum

    setattr(
        model,
        CON_DEMANDSUPPLYSUM,
        Constraint(getattr(model, SET_DEMANDSUMTUPLE), rule=__rule_demand_supply_sum),
    )


def _con_unmet_demand_gate_all(
    model: Model,
    ecs: Ecs,
    demands: Demands,
    times: Times,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
    stime_to_tid,
) -> None:
    """
    Unified unmet-demand gating for *all* demand tuples:

      V_AutUnmetDemand[s,h,e,t] <= M(s,h,e,t) * P_DemandUnmetAllowed

    where M(s,h,e,t) is:
      - for demand-profile tuples: the actual demand at (s,h,e,t) in power units
      - for demand-sum tuples: (DemandSumBigM[s,h,e] / weight(s,t)) in power units
      - otherwise: 0 (no unmet allowed / irrelevant tuple)
    """
    S_Time = getattr(model, SET_TIME)
    S_DemandTuple = getattr(model, SET_DEMANDTUPLE)
    S_Profile = getattr(model, SET_DEMANDPROFILETUPLE)
    S_Sum = getattr(model, SET_DEMANDSUMTUPLE)

    profile_set = set(S_Profile.data())
    sum_set = set(S_Sum.data())

    def rule(m, s, h, e, t_elem):
        # If unmet is globally disabled, this forces unmet = 0 no matter what.
        flag = getattr(m, PAR_DEMANDUNMETALLOWED)

        # Case A: profile tuple -> bound by actual per-timestep demand
        if (s, h, e) in profile_set:
            t_id = stime_to_tid[t_elem]
            unit_pw = (
                get_ec_model_unit(ecs.get_unit(EcId(e)), mass_unit, power_unit)
                / TimeUnit.H
            )

            dv = demands.get_demand_profile(StageId(s), HubId(h), EcId(e)).get_value(
                t_id
            )
            demand_pw = 0.0 if dv is None else dv.to_float(unit=unit_pw)
            M = demand_pw

        # Case B: sum tuple -> bound by per-timestep Big-M derived from total energy
        elif (s, h, e) in sum_set:
            M_energy = getattr(m, PAR_DEMANDSUMBIGM)[s, h, e]  # energy units
            w_t = times.get_weight(StageId(s), stime_to_tid[t_elem])
            if w_t <= 0:
                return Constraint.Skip
            M = M_energy / w_t

        # Case C: other tuples -> no unmet supposed to exist
        else:
            M = 0.0

        return getattr(m, VAR_DEMANDUNMET)[s, h, e, t_elem] <= M * flag

    setattr(model, CON_DEMANDUNMETGATED, Constraint(S_DemandTuple, S_Time, rule=rule))
