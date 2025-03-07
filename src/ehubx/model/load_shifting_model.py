"""Load shifting submodel"""

from datetime import datetime

from pyomo.core import (
    Binary,
    Constraint,
    Model,
    NonNegativeReals,
    Param,
    Reals,
    Set,
    Var,
)

from ehubx.core import common, logging
from ehubx.data.demand_data import Demands
from ehubx.data.ec_data import EcId
from ehubx.data.hub_data import HubId
from ehubx.data.load_shifting_data import LoadShiftId, LoadShifting
from ehubx.data.stage_data import StageId
from ehubx.data.time_data import TimeId, Times
from ehubx.model.ec_model import SET_EC
from ehubx.model.hub_model import SET_HUB
from ehubx.model.stage_model import SET_STAGE
from ehubx.model.times_model import SET_TIME, SET_TIMEHORIZON


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/load_shift"
"""String identifying the load shifting model for logging purposes"""

MULT_SHIFT_ABOVE_DEMAND: float = 10
"""Multiplier to the demand value to set a maximal upper threshold for
above-shifts"""

MULT_SHIFT_BELOW_DEMAND: float = 1
"""Multiplier to the demand value to set a maximal upper threshold for
below-shifts"""

SET_LOADSHIFTING: str = "S_LoadShifting"
"""Name of set with all load shifting indices"""

SET_LOADSHIFTINGTUPLE: str = "S_LoadShiftingTuple"
"""Name of set with all load shifting tuples"""

SET_LOADSHIFTINGTUPLEFIX: str = "S_LoadShiftingTupleFix"
"""Name of set with all load shifting tuples which have fixed costs"""

VAR_LOADSHIFTING: str = "V_LoadShifting"
"""Name of variable for load shifting amounts"""

VAR_LOADSHIFTINGABOVE: str = "V_LoadShiftingAbove"
"""Name of variable for above-parts of load shifting"""

VAR_LOADSHIFTINGBELOW: str = "V_LoadShiftingBelow"
"""Name of variable for below-parts of load shifting"""

VAR_LOADSHIFTINGABOVEPEAK: str = "V_LoadShiftingAbovePeak"
"""Name of variable for peak value of above-parts of load shifting"""

VAR_LOADSHIFTINGBELOWPEAK: str = "V_LoadShiftingBelowPeak"
"""Name of variable for peak value of below-parts of load shifting"""

VAR_LOADHSHIFTINGCOSTENERGY: str = "V_LoadShiftingCostEnergy"
"""Name of variable for energy-related load shifting costs"""

VAR_LOADHSHIFTINGCOSTPEAK: str = "V_LoadShiftingCostPeak"
"""Name of variable for peak-related load shifting costs"""

VAR_LOADHSHIFTINGCOSTFIX: str = "V_LoadShiftingCostFix"
"""Name of variable for fixed amounts in load shifting costs"""

VAR_LOADHSHIFTINGCOSTTOTAL: str = "V_LoadShiftingCostTotal"
"""Name of variable for total load shifting costs"""

VAR_YLOADHSHIFTING: str = "V_YLoadShifting"
"""Name of variable monitoring whether any amount of load shifting occurs"""

PAR_LOADSHIFTINGIDOFTUPLE: str = "P_LoadShiftingIdOfTuple"
"""Name of parameter holding the load shifting id for each load shifting
tuple"""

CON_LOADHSHIFTINGNEUTRALITYONINTERVALS: str = "C_LoadShiftingNeutralityOnIntervals"
"""Name of constraint enforcing load shifting neutrality on load shift
intervals"""

CON_LOADHSHIFTINGNEUTRALITYOVERALL: str = "C_LoadShiftingNeutralityOverall"
"""Name of constraint enforcing load shifting neutrality on entire time
horizon"""

CON_LOADHSHIFTINGABOVEBLEOW: str = "C_LoadShiftingAboveBelow"
"""Name of constraint composing load shifting from the above and below parts"""

CON_LOADHSHIFTINGMAXABOVE: str = "C_LoadShiftingMaxAbove"
"""Name of constraint setting an upper limit for above parts of load
shifting"""

CON_LOADHSHIFTINGMAXBELOW: str = "C_LoadShiftingMaxBelow"
"""Name of constraint setting an upper limit for below parts of load
shifting"""

CON_LOADHSHIFTINGINTERVALCAP: str = "C_LoadShiftingIntervalCap"
"""Name of constraint respecting load shifting capacity on the load shifting
intervals"""

CON_LOADHSHIFTINGABOVEPEAK: str = "C_LoadShiftingAbovePeak"
"""Name of constraint setting the peak variable for above load shifts"""

CON_LOADHSHIFTINGBELOWPEAK: str = "C_LoadShiftingBelowPeak"
"""Name of constraint setting the peak variable for below load shifts"""

CON_YLOADHSHIFTING: str = "C_YLoadShifting"
"""Name of constraint setting the binary monitoring variable for fix costs"""

CON_LOADSHIFTINGCOSTENERGY: str = "C_LoadShiftingCostEnergy"
"""Name of constraint setting the energy-related load shifting cost"""

CON_LOADSHIFTINGCOSTPEAK: str = "C_LoadShiftingCostPeak"
"""Name of constraint setting the peak-related load shifting cost"""

CON_LOADSHIFTINGCOSTFIX: str = "C_LoadShiftingCostFix"
"""Name of constraint setting the fixed load shifting costs"""

CON_LOADSHIFTINGCOSTTOTAL: str = "C_LoadShiftingCostTotal"
"""Name of constraint setting the total load shifting costs"""


def build(
    model: Model, demands: Demands, load_shifting: LoadShifting, times: Times
) -> None:
    """
    Builds the load shifting submodel. For a mathematical description in
    thorough detail, please refer to the section 'Load shifting model' in the
    documentation.

    :param model: Pyomo model
    :type model: Model
    :param demands: Demand data object
    :type demands: Demands
    :param load_shifting: Load shifting data object
    :type load_shifting: LoadShifting
    :param times: Time data object
    :type times: Times
    """
    # Start measuring build time
    start = datetime.now()
    # Build
    _build_base(model, demands, load_shifting, times)
    _build_cost(model, load_shifting, times)
    # Logging
    elapsed = datetime.now() - start
    logging.log_file(
        f"Built load shifting module. Elapsed time: {int(elapsed.total_seconds())}s",
        module=LOG_MODULE_STR,
    )


def _build_base(
    model: Model, demands: Demands, load_shifting: LoadShifting, times: Times
) -> None:
    # [SET] Load shifting ids
    setattr(
        model, SET_LOADSHIFTING, Set(initialize=[ls.key for ls in load_shifting.ids])
    )
    # [SET] Load shifting tuples (stage, hub, ec)
    setattr(
        model,
        SET_LOADSHIFTINGTUPLE,
        Set(
            within=(
                getattr(model, SET_STAGE)
                * getattr(model, SET_HUB)
                * getattr(model, SET_EC)
            ),
            initialize=[
                (s.key, h.key, e.key)
                for ls in load_shifting.ids
                for (s, h, e) in load_shifting.get_tuples(ls)
            ],
        ),
    )
    # [PAR] Load shifting id of tuple
    load_shifting_id_of_tuple = {}
    for ls in load_shifting.ids:
        for s, h, e in load_shifting.get_tuples(ls):
            load_shifting_id_of_tuple[s.key, h.key, e.key] = ls.key
    setattr(
        model,
        PAR_LOADSHIFTINGIDOFTUPLE,
        Param(
            getattr(model, SET_LOADSHIFTINGTUPLE),
            within=getattr(model, SET_LOADSHIFTING),
            initialize=load_shifting_id_of_tuple,
        ),
    )
    # [VAR] Load shifting amount per (s, h, e) tuple
    setattr(
        model,
        VAR_LOADSHIFTING,
        Var(
            getattr(model, SET_LOADSHIFTINGTUPLE),
            getattr(model, SET_TIME),
            domain=Reals,
        ),
    )
    # [CON] Enforce load shifting neutrality on shifting intervals.
    _con_load_shifting_neutrality_on_intervals(model, load_shifting, times)
    # [CON] Enforce overall load shifting neutrality, i.e., over full time
    #       horizon
    _con_load_shifting_neutrality_overall(model, times)
    # [VAR] Load shifting amount above load curve
    setattr(
        model,
        VAR_LOADSHIFTINGABOVE,
        Var(
            getattr(model, SET_LOADSHIFTINGTUPLE),
            getattr(model, SET_TIME),
            domain=NonNegativeReals,
        ),
    )
    # [VAR] Load shifting amount below load curve
    setattr(
        model,
        VAR_LOADSHIFTINGBELOW,
        Var(
            getattr(model, SET_LOADSHIFTINGTUPLE),
            getattr(model, SET_TIME),
            domain=NonNegativeReals,
        ),
    )
    # [CON] Force load shifting to be made of above-shifts minus below-shifts
    _con_load_shifting_abovebelow(model)
    # [CON] Respect absolute and relative maximal values for above and below
    #       shifts
    _con_load_shifting_max_abovebelow(model, demands, load_shifting)
    # [CON] Respect interval capacity, i.e. time integral over total amount of
    #       above-shifts on each load interval
    _con_load_shifting_interval_cap(model, load_shifting, times)

    # [VAR] Peak value of all above-shifts on the full time horizon
    setattr(
        model,
        VAR_LOADSHIFTINGABOVEPEAK,
        Var(getattr(model, SET_LOADSHIFTINGTUPLE), domain=NonNegativeReals),
    )
    # [VAR] Peak value of all below-shifts on the full time horizon
    setattr(
        model,
        VAR_LOADSHIFTINGBELOWPEAK,
        Var(getattr(model, SET_LOADSHIFTINGTUPLE), domain=NonNegativeReals),
    )
    # [CON] Force the peak values to lie above all time-dependent values
    _con_load_shifting_peak(model)
    # [VAR] Binary variable to monitor load shifting occurences. Only defend
    #       for tuples with fix costs
    _var_y_load_shifting(model, load_shifting)
    # [VAR] Force YLoadShifting to 1 if LoadShifting is larger than 0
    _con_y_load_shifting(model, demands, load_shifting)


def _build_cost(model: Model, load_shifting: LoadShifting, times: Times) -> None:
    # [VAR] Load shifting energy cost, i.e. time integral over all
    #       absolute load shifting power above and below the demand curve
    setattr(
        model,
        VAR_LOADHSHIFTINGCOSTENERGY,
        Var(getattr(model, SET_LOADSHIFTINGTUPLE), domain=NonNegativeReals),
    )
    # [CON] Load shifting energy cost
    _con_load_shifting_cost_energy(model, load_shifting, times)
    # [VAR] Load shifting peak cost, i.e., cost for highest shifts on time
    #       horizon
    setattr(
        model,
        VAR_LOADHSHIFTINGCOSTPEAK,
        Var(getattr(model, SET_LOADSHIFTINGTUPLE), domain=NonNegativeReals),
    )
    # [CON] Load shifting peak cost
    _con_load_shifting_cost_peak(model, load_shifting)
    # [VAR] Load shifting fix cost, i.e.; costs occuring any time load shifting
    #       is used at all
    setattr(
        model,
        VAR_LOADHSHIFTINGCOSTFIX,
        Var(getattr(model, SET_LOADSHIFTINGTUPLEFIX), domain=NonNegativeReals),
    )
    # [CON] Load shifting fix cost
    _con_load_shifting_cost_fix(model, load_shifting, times)
    # [VAR] Total load shifting cost
    setattr(model, VAR_LOADHSHIFTINGCOSTTOTAL, Var(domain=NonNegativeReals))
    # [CON] Total load shedding cost
    _con_load_shifting_cost_total(model)


def _con_load_shifting_neutrality_on_intervals(
    model: Model, load_shifting: LoadShifting, times: Times
) -> None:
    def __rule_load_shifting_neutrality_on_intervals(model, s, h, e, t_hor):
        # Get parameters
        ls = getattr(model, PAR_LOADSHIFTINGIDOFTUPLE)[s, h, e]
        interval_length = load_shifting.get_interval_length(LoadShiftId(ls))
        # Ignore edge intervals
        if t_hor + interval_length - 1 > getattr(model, SET_TIMEHORIZON).last():
            return Constraint.Skip
        # Avoid overlapping intervals by only defining the neutrality
        # constraint if t is the start id of the shift interval
        rem = (t_hor - getattr(model, SET_TIMEHORIZON).first()) % interval_length
        if rem != 0:
            return Constraint.Skip
        # Calculate load shifting balance on shift interval
        load_shifting_balance = 0
        for tau in range(t_hor, t_hor + interval_length):
            tau_clus = times.get_cluster_ts(StageId(s), TimeId(tau)).key_as_int
            load_shifting_balance += getattr(model, VAR_LOADSHIFTING)[s, h, e, tau_clus]
        # Set constraint
        return load_shifting_balance == 0

    setattr(
        model,
        CON_LOADHSHIFTINGNEUTRALITYONINTERVALS,
        Constraint(
            getattr(model, SET_LOADSHIFTINGTUPLE),
            getattr(model, SET_TIMEHORIZON),
            rule=__rule_load_shifting_neutrality_on_intervals,
        ),
    )


def _con_load_shifting_neutrality_overall(model: Model, times: Times) -> None:
    def __rule_load_shifting_neutrality_overall(model, s, h, e):
        # Calculate load shifting balance on entire time horizon
        load_shifting_balance = sum(
            times.get_weight(StageId(s), TimeId(t))
            * getattr(model, VAR_LOADSHIFTING)[s, h, e, t]
            for t in getattr(model, SET_TIME)
        )
        # Set constraint
        return load_shifting_balance == 0

    setattr(
        model,
        CON_LOADHSHIFTINGNEUTRALITYOVERALL,
        Constraint(
            getattr(model, SET_LOADSHIFTINGTUPLE),
            rule=__rule_load_shifting_neutrality_overall,
        ),
    )


def _con_load_shifting_abovebelow(model: Model) -> None:
    def __rule_load_shifting_above_below(model, s, h, e, t):
        # Calulate load shifting
        load_shifting = (
            getattr(model, VAR_LOADSHIFTINGABOVE)[s, h, e, t]
            - getattr(model, VAR_LOADSHIFTINGBELOW)[s, h, e, t]
        )
        # Set the constraint
        return getattr(model, VAR_LOADSHIFTING)[s, h, e, t] == load_shifting

    setattr(
        model,
        CON_LOADHSHIFTINGABOVEBLEOW,
        Constraint(
            getattr(model, SET_LOADSHIFTINGTUPLE),
            getattr(model, SET_TIME),
            rule=__rule_load_shifting_above_below,
        ),
    )


def _con_load_shifting_max_abovebelow(
    model: Model, demands: Demands, load_shifting: LoadShifting
) -> None:
    def __rule_load_shifting_max_above(model, s, h, e, t):
        # Parameters
        ls = getattr(model, PAR_LOADSHIFTINGIDOFTUPLE)[s, h, e]
        max_above_abs = load_shifting.get_max_above_abs(LoadShiftId(ls)).get_value(
            TimeId(t)
        )
        max_above_rel = load_shifting.get_max_above_rel(LoadShiftId(ls)).get_value(
            TimeId(t)
        )
        demand = demands.get_demand(StageId(s), HubId(h), EcId(e)).get_value(TimeId(t))
        # Calculate the maximal value for above-shifting
        max_above = min(max_above_abs, max_above_rel * demand)
        # Skip the constraint for infinite max
        if max_above == float("inf"):
            return Constraint.Skip
        # Set constraint
        return getattr(model, VAR_LOADSHIFTINGABOVE)[s, h, e, t] <= max_above

    def __rule_load_shifting_max_below(model, s, h, e, t):
        # Parameters
        ls = getattr(model, PAR_LOADSHIFTINGIDOFTUPLE)[s, h, e]
        max_below_abs = load_shifting.get_max_below_abs(LoadShiftId(ls)).get_value(
            TimeId(t)
        )
        max_below_rel = load_shifting.get_max_below_rel(LoadShiftId(ls)).get_value(
            TimeId(t)
        )
        demand = demands.get_demand(StageId(s), HubId(h), EcId(e)).get_value(TimeId(t))
        # Calculate the maximal value for below-shifting
        max_below = min(max_below_abs, max_below_rel * demand)
        # Skip the constraint for infinite max
        if max_below == float("inf"):
            return Constraint.Skip
        # Set constraint
        return getattr(model, VAR_LOADSHIFTINGBELOW)[s, h, e, t] <= max_below

    setattr(
        model,
        CON_LOADHSHIFTINGMAXABOVE,
        Constraint(
            getattr(model, SET_LOADSHIFTINGTUPLE),
            getattr(model, SET_TIME),
            rule=__rule_load_shifting_max_above,
        ),
    )
    setattr(
        model,
        CON_LOADHSHIFTINGMAXBELOW,
        Constraint(
            getattr(model, SET_LOADSHIFTINGTUPLE),
            getattr(model, SET_TIME),
            rule=__rule_load_shifting_max_below,
        ),
    )


def _con_load_shifting_interval_cap(
    model: Model, load_shifting: LoadShifting, times: Times
) -> None:
    def __rule_load_shifting_interval_cap(model, s, h, e, t_hor):
        # Get parameters
        ls = getattr(model, PAR_LOADSHIFTINGIDOFTUPLE)[s, h, e]
        interval_length = load_shifting.get_interval_length(LoadShiftId(ls))
        interval_cap = load_shifting.get_interval_cap(LoadShiftId(ls))
        if interval_cap == float("inf"):
            return Constraint.Skip
        # Ignore edge intervals
        if t_hor + interval_length - 1 > getattr(model, SET_TIMEHORIZON).last():
            return Constraint.Skip
        # Avoid overlapping intervals by only defining the capacity
        # constraint if t is the start id of the shift interval
        rem = (t_hor - getattr(model, SET_TIMEHORIZON).first()) % interval_length
        if rem != 0:
            return Constraint.Skip
        # Calculate load shifting above-energy on shift interval
        load_shifting_energy = 0
        for tau in range(t_hor, t_hor + interval_length):
            tau_clus = times.get_cluster_ts(StageId(s), TimeId(tau)).key_as_int
            load_shifting_energy += getattr(model, VAR_LOADSHIFTINGABOVE)[
                s, h, e, tau_clus
            ]
        # Set constraint
        return load_shifting_energy <= interval_cap

    setattr(
        model,
        CON_LOADHSHIFTINGINTERVALCAP,
        Constraint(
            getattr(model, SET_LOADSHIFTINGTUPLE),
            getattr(model, SET_TIMEHORIZON),
            rule=__rule_load_shifting_interval_cap,
        ),
    )


def _con_load_shifting_peak(model: Model) -> None:
    def __rule_load_shifting_above_peak(model, s, h, e, t):
        return (
            getattr(model, VAR_LOADSHIFTINGABOVEPEAK)[s, h, e]
            >= getattr(model, VAR_LOADSHIFTINGABOVE)[s, h, e, t]
        )

    def __rule_load_shifting_below_peak(model, s, h, e, t):
        return (
            getattr(model, VAR_LOADSHIFTINGBELOWPEAK)[s, h, e]
            >= getattr(model, VAR_LOADSHIFTINGBELOW)[s, h, e, t]
        )

    setattr(
        model,
        CON_LOADHSHIFTINGABOVEPEAK,
        Constraint(
            getattr(model, SET_LOADSHIFTINGTUPLE),
            getattr(model, SET_TIME),
            rule=__rule_load_shifting_above_peak,
        ),
    )
    setattr(
        model,
        CON_LOADHSHIFTINGBELOWPEAK,
        Constraint(
            getattr(model, SET_LOADSHIFTINGTUPLE),
            getattr(model, SET_TIME),
            rule=__rule_load_shifting_below_peak,
        ),
    )


def _var_y_load_shifting(model: Model, load_shifting: LoadShifting) -> None:
    # [SET] Initialize tuple set for tuples with fix costs
    setattr(
        model,
        SET_LOADSHIFTINGTUPLEFIX,
        Set(within=getattr(model, SET_LOADSHIFTINGTUPLE)),
    )
    for s, h, e in getattr(model, SET_LOADSHIFTINGTUPLE):
        # Parameters
        ls = getattr(model, PAR_LOADSHIFTINGIDOFTUPLE)[s, h, e]
        fix_cost = load_shifting.get_fix_cost(LoadShiftId(ls))
        # Check if fix cost is not zero
        if not fix_cost.has_values:
            fix_cost_def = fix_cost.def_value
            assert fix_cost_def is not None
            if abs(fix_cost_def) <= common.EPS_ZEROCHECK:
                continue
        # Add to fix set
        getattr(model, SET_LOADSHIFTINGTUPLEFIX).add((s, h, e))

    setattr(
        model,
        VAR_YLOADHSHIFTING,
        Var(
            getattr(model, SET_LOADSHIFTINGTUPLEFIX),
            getattr(model, SET_TIME),
            domain=Binary,
        ),
    )


def _con_y_load_shifting(
    model: Model, demands: Demands, load_shifting: LoadShifting
) -> None:
    def __rule_y_load_shifting(model, s, h, e, t):
        # Parameters
        ls = getattr(model, PAR_LOADSHIFTINGIDOFTUPLE)[s, h, e]
        max_above_abs = load_shifting.get_max_above_abs(LoadShiftId(ls)).get_value(
            TimeId(t)
        )
        max_above_rel = load_shifting.get_max_above_rel(LoadShiftId(ls)).get_value(
            TimeId(t)
        )
        max_below_abs = load_shifting.get_max_below_abs(LoadShiftId(ls)).get_value(
            TimeId(t)
        )
        max_below_rel = load_shifting.get_max_below_rel(LoadShiftId(ls)).get_value(
            TimeId(t)
        )
        demand = demands.get_demand(StageId(s), HubId(h), EcId(e)).get_value(TimeId(t))
        # Calculate upper bound for above-shifts
        max_above = min(
            max_above_abs, max_above_rel * demand, MULT_SHIFT_ABOVE_DEMAND * demand
        )
        max_below = min(
            max_below_abs, max_below_rel * demand, MULT_SHIFT_BELOW_DEMAND * demand
        )
        # Calculate the total absolute shifting
        abs_shifting = (
            getattr(model, VAR_LOADSHIFTINGABOVE)[s, h, e, t]
            + getattr(model, VAR_LOADSHIFTINGBELOW)[s, h, e, t]
        )
        # Calculate the upper bound for the total absolute shifting
        abs_bound = max_above + max_below
        # Set constraint
        return (
            abs_shifting <= abs_bound * getattr(model, VAR_YLOADHSHIFTING)[s, h, e, t]
        )

    setattr(
        model,
        CON_YLOADHSHIFTING,
        Constraint(
            getattr(model, SET_LOADSHIFTINGTUPLEFIX),
            getattr(model, SET_TIME),
            rule=__rule_y_load_shifting,
        ),
    )


def _con_load_shifting_cost_energy(
    model: Model, load_shifting: LoadShifting, times: Times
) -> None:
    def __rule_load_shifting_cost_energy(model, s, h, e):
        # Parameters
        ls = getattr(model, PAR_LOADSHIFTINGIDOFTUPLE)[s, h, e]
        energy_cost_above = load_shifting.get_energy_cost_above(LoadShiftId(ls))
        energy_cost_below = load_shifting.get_energy_cost_below(LoadShiftId(ls))
        # Calculate load shifting energy cost
        cost = sum(
            times.get_weight(StageId(s), TimeId(t))
            * (
                energy_cost_above.get_value(TimeId(t))
                * getattr(model, VAR_LOADSHIFTINGABOVE)[s, h, e, t]
                + energy_cost_below.get_value(TimeId(t))
                * getattr(model, VAR_LOADSHIFTINGBELOW)[s, h, e, t]
            )
            for t in getattr(model, SET_TIME)
        )
        # Set constraint
        return getattr(model, VAR_LOADHSHIFTINGCOSTENERGY)[s, h, e] == cost

    setattr(
        model,
        CON_LOADSHIFTINGCOSTENERGY,
        Constraint(
            getattr(model, SET_LOADSHIFTINGTUPLE), rule=__rule_load_shifting_cost_energy
        ),
    )


def _con_load_shifting_cost_peak(model: Model, load_shifting: LoadShifting) -> None:
    def __rule_load_shifting_cost_peak(model, s, h, e):
        # Parameters
        ls = getattr(model, PAR_LOADSHIFTINGIDOFTUPLE)[s, h, e]
        peak_cost_above = load_shifting.get_peak_cost_above(LoadShiftId(ls))
        peak_cost_below = load_shifting.get_peak_cost_below(LoadShiftId(ls))
        # Calculate load shifting peak cost
        cost = (
            peak_cost_above * getattr(model, VAR_LOADSHIFTINGABOVEPEAK)[s, h, e]
            + peak_cost_below * getattr(model, VAR_LOADSHIFTINGBELOWPEAK)[s, h, e]
        )
        # Set constraint
        return getattr(model, VAR_LOADHSHIFTINGCOSTPEAK)[s, h, e] == cost

    setattr(
        model,
        CON_LOADSHIFTINGCOSTPEAK,
        Constraint(
            getattr(model, SET_LOADSHIFTINGTUPLE), rule=__rule_load_shifting_cost_peak
        ),
    )


def _con_load_shifting_cost_fix(
    model: Model, load_shifting: LoadShifting, times: Times
) -> None:
    def __rule_load_shifting_cost_fix(model, s, h, e):
        # Parameters
        ls = getattr(model, PAR_LOADSHIFTINGIDOFTUPLE)[s, h, e]
        fix_cost = load_shifting.get_fix_cost(LoadShiftId(ls))
        # Calculate total fix cost
        cost = sum(
            times.get_weight(StageId(s), TimeId(t))
            * fix_cost.get_value(TimeId(t))
            * getattr(model, VAR_YLOADHSHIFTING)[s, h, e, t]
            for t in getattr(model, SET_TIME)
        )
        # Set constraint
        return getattr(model, VAR_LOADHSHIFTINGCOSTFIX)[s, h, e] == cost

    setattr(
        model,
        CON_LOADSHIFTINGCOSTFIX,
        Constraint(
            getattr(model, SET_LOADSHIFTINGTUPLEFIX), rule=__rule_load_shifting_cost_fix
        ),
    )


def _con_load_shifting_cost_total(model: Model) -> None:
    def __rule_load_shifting_cost_total(model):
        # Calculate total load shifting cost
        load_shifting_cost_total = sum(
            getattr(model, VAR_LOADHSHIFTINGCOSTENERGY)[s, h, e]
            + getattr(model, VAR_LOADHSHIFTINGCOSTPEAK)[s, h, e]
            for (s, h, e) in getattr(model, SET_LOADSHIFTINGTUPLE)
        )
        # Add fix costs
        load_shifting_cost_total += sum(
            getattr(model, VAR_LOADHSHIFTINGCOSTFIX)[s, h, e]
            for (s, h, e) in getattr(model, SET_LOADSHIFTINGTUPLEFIX)
        )
        # Set constraint
        return getattr(model, VAR_LOADHSHIFTINGCOSTTOTAL) == load_shifting_cost_total

    setattr(
        model,
        CON_LOADSHIFTINGCOSTTOTAL,
        Constraint(rule=__rule_load_shifting_cost_total),
    )
