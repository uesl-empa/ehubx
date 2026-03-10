"""Autonomy submodel"""

from datetime import datetime

from pyomo.core import Binary, Block, Constraint, NonNegativeReals, Param, Var

from ehubx.core import logging
from ehubx.data.ec_data import EcId, Ecs, ImpExpType
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId
from ehubx.data.time_data import TimeId, Times
from ehubx.data.unit import TimeUnit
from ehubx.model.demand_model import (
    PAR_DEMANDSUMBIGM,
    SET_DEMANDPROFILETUPLE,
    SET_DEMANDSUMTUPLE,
    SET_DEMANDTUPLE,
    VAR_DEMANDUNMET,
)
from ehubx.model.ec_model import get_ec_model_unit
from ehubx.model.import_model import SET_IMPTUPLE, VAR_IMP
from ehubx.model.stage_model import SET_STAGE
from ehubx.model.times_model import SET_TIME, SET_TIMEHORIZON


# -------- #
# Literals #
# -------- #
VAR_AUTALIVE: str = "V_AutAlive"
"""Name of variable indicating whether the system is still autonomous (alive)."""

VAR_AUTONOMY: str = "V_Autonomy"
"""Name of variable representing total autonomy duration."""

PAR_AUTENABLE: str = "P_AutEnable"
"""Name of binary parameter controlling whether the autonomy module is active.
This is a configuration marker set by the optimizer; it is not used as a
mathematical gating constraint in this module."""

CON_AUTENABLEDSET: str = "C_AutEnabledSet"
"""Name of container holding all constraints active when autonomy is enabled."""

CON_AUTZERO: str = "C_AutZero"
"""Name of constraint forcing autonomy duration to zero when autonomy is disabled."""

CON_AUTPREFIX: str = "C_AutPrefix"
"""Name of constraint enforcing prefix structure of the alive variable."""

CON_AUTNOCROSSIMPORTWHENALIVE: str = "C_AutNoCrossImportWhenAlive"
"""Name of constraint prohibiting cross-import of energy carriers while the
system is autonomous."""

CON_AUTUNMETDEMANDGATED: str = "C_AutUnmetDemandGated"
"""Name of constraint linking unmet demand to autonomy status."""

CON_AUTHOURSDEF: str = "C_AutHoursDef"
"""Name of constraint defining total autonomy duration when autonomy is enabled."""

LOG_MODULE_STR: str = "mod/autonomy"


def build(model, system: EnergySystem) -> None:
    times: Times = system.times
    ecs: Ecs = system.ecs

    # Required model sets
    #   DB: I think you don't need these assertions. We don't check them anywhere else
    #       and if they are not present, we are in deep trouble anyway and ane error
    #       will have been thrown much earlier than in this module.
    if not hasattr(model, SET_STAGE):
        raise AttributeError(
            f"Autonomy requires model.{SET_STAGE} for consistent indexing "
            "(use model sets, not data-module .ids)."
        )
    if not hasattr(model, SET_TIMEHORIZON):
        raise AttributeError(
            f"Autonomy requires model.{SET_TIMEHORIZON} for chronological indexing."
        )
    if not hasattr(model, SET_TIME):
        raise AttributeError(f"Autonomy requires model.{SET_TIME}.")

    s_stage = getattr(model, SET_STAGE)
    s_time_hor = getattr(model, SET_TIMEHORIZON)

    # Start measuring build time
    start = datetime.now()

    # Variables and configuration
    setattr(model, VAR_AUTALIVE, Var(s_stage, s_time_hor, domain=Binary))
    setattr(model, VAR_AUTONOMY, Var(domain=NonNegativeReals))

    setattr(model, PAR_AUTENABLE, Param(within=Binary, initialize=0, mutable=True))

    # Precompute time-id map (needed for import max lookup + weights)
    sth_to_tid = _make_setelem_to_timeid_map(times, s_time_hor)

    # Enabled constraint "set"
    con_enabled = Block()
    setattr(model, CON_AUTENABLEDSET, con_enabled)

    # Constraints
    _con_aut_prefix_of_ones(con_enabled, model, s_stage, s_time_hor)
    _con_aut_no_cross_import_while_alive(
        con_enabled,
        model,
        ecs=ecs,
        imports=system.imports,
        times=times,
        mass_unit=system.mass_unit,
        power_unit=system.power_unit,
        stime_to_tid=sth_to_tid,
        s_time=s_time_hor,
    )
    _con_aut_unmet_demand_gated(
        con_enabled,
        model,
        ecs=ecs,
        demands=system.demands,
        times=times,
        mass_unit=system.mass_unit,
        power_unit=system.power_unit,
        s_time=s_time_hor,
    )
    _con_aut_hours_definition(con_enabled, model, s_stage, s_time_hor)

    # Disabled-state constraint
    def _rule_autonomy_zero(_m):
        return getattr(model, VAR_AUTONOMY) == 0

    setattr(model, CON_AUTZERO, Constraint(rule=_rule_autonomy_zero))

    # Default: disabled (optimizer will enable when objective requires it)
    set_autonomy_enabled(model, enabled=False)

    # Log
    elapsed = datetime.now() - start
    logging.log_file(
        f"Built autonomy module. Elapsed time: {int(elapsed.total_seconds())}s",
        module=LOG_MODULE_STR,
    )


def set_autonomy_enabled(model, enabled: bool) -> None:
    s_time = getattr(model, SET_TIME, None)
    s_time_hor = getattr(model, SET_TIMEHORIZON, None)

    if enabled:
        if s_time is None or s_time_hor is None:
            raise AttributeError(
                "Autonomy requires s_time and s_time_horizon on the model."
            )

    if model.find_component(PAR_AUTENABLE) is not None:
        getattr(model, PAR_AUTENABLE).set_value(1 if enabled else 0)

    if enabled:
        getattr(model, CON_AUTENABLEDSET).activate()
        getattr(model, CON_AUTZERO).deactivate()
    else:
        getattr(model, CON_AUTENABLEDSET).deactivate()
        getattr(model, CON_AUTZERO).activate()


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _k(x):
    return getattr(x, "key_as_int", getattr(x, "key", x))


def _make_setelem_to_timeid_map(times: Times, s_time_entry):
    tid_by_key = {_k(ti): ti for ti in times.ids}
    out = {}
    for te in s_time_entry:
        k = _k(te)
        out[te] = tid_by_key.get(k, TimeId(k))
    return out


# ---------------------------------------------------------------------
# Prefix-of-ones on s_time_horizon
# DB: Suggest to rename, "prefix_of_ones" is a bit opaque.
#     Maybe "con_aut_alive_nonincreasing"
# ---------------------------------------------------------------------
def _con_aut_prefix_of_ones(container, model, s_stage, s_time_hor) -> None:
    key2elem = {_k(te): te for te in s_time_hor}
    ordered_keys = sorted(key2elem.keys())
    idx = range(len(ordered_keys) - 1)

    # DB: I have a question, why not just do this? I haven't tried it but it seems more
    #     straightforward, and you wouldn't need to reorder the time horizon or build a
    # key2elem map:
    #
    # def _rule_prefix(_m, s, t_hor):
    #     if t_hor == s_time_hor.last():
    #         return Constraint.Skip
    #     t_hor_next = s_time_hor.next(t_hor)
    #     return (getattr(model, VAR_AUTALIVE)[s, t_hor]
    #             >= getattr(model, VAR_AUTALIVE)[s, t_hor_next])
    #
    # setattr(container, CON_AUTPREFIX,
    #         Constraint(s_stage, s_time_hor, rule=_rule_prefix))

    def _rule_prefix(_m, s, i):
        t = key2elem[ordered_keys[i]]
        tn = key2elem[ordered_keys[i + 1]]
        return getattr(model, VAR_AUTALIVE)[s, t] >= getattr(model, VAR_AUTALIVE)[s, tn]

    setattr(container, CON_AUTPREFIX, Constraint(s_stage, idx, rule=_rule_prefix))


# ---------------------------------------------------------------------
# Gate unmet demand: V_DemandUnmet <= demand(t) * (1 - y)
# (compute demand on-the-fly, cached per (s,h,e))
# ---------------------------------------------------------------------
def _con_aut_unmet_demand_gated(
    container,
    model,
    ecs: Ecs,
    demands,
    times: Times,
    mass_unit,
    power_unit,
    s_time,
) -> None:
    if not hasattr(model, VAR_DEMANDUNMET):
        return
    if not hasattr(model, SET_DEMANDPROFILETUPLE) and not hasattr(
        model, SET_DEMANDSUMTUPLE
    ):
        return

    s_profile = getattr(model, SET_DEMANDPROFILETUPLE, None)
    s_sum = getattr(model, SET_DEMANDSUMTUPLE, None)

    profile_set = set(s_profile.data()) if s_profile is not None else set()
    sum_set = set(s_sum.data()) if s_sum is not None else set()

    def rule(m, s, h, e, t_elem):
        # Only apply to demand tuples that are actually profile or sum demand tuples
        if (s, h, e) not in profile_set and (s, h, e) not in sum_set:
            return Constraint.Skip

        v_autalive = getattr(model, VAR_AUTALIVE)[s, t_elem]

        # Map horizon -> cluster
        t_clust_id = times.get_cluster_ts(StageId(s), TimeId(t_elem))
        t_clust = t_clust_id.key_as_int

        # A) profile tuples -> actual demand(t)
        if (s, h, e) in profile_set:
            unit_pw = (
                get_ec_model_unit(ecs.get_unit(EcId(e)), mass_unit, power_unit)
                / TimeUnit.H
            )
            dv = demands.get_demand_profile(StageId(s), HubId(h), EcId(e)).get_value(
                t_clust_id
            )
            # I woudln't do the line below like this, just do
            #   M = dv.to_float(unit=unit_pw)
            # If it cannot find a value for that time step, we are in trouble on a
            # whole other level anyway, and setting M = 0 would lead to more trouble
            # in this module. We can rely on the fact that dv should not be None here.
            M = 0.0 if dv is None else dv.to_float(unit=unit_pw)

        # B) sum tuples -> Big-M per timestep from total energy / weight
        else:
            energy_limit = getattr(model, PAR_DEMANDSUMBIGM)[s, h, e]
            w_t = times.get_weight(StageId(s), t_clust_id)
            if w_t <= 0:
                return Constraint.Skip
            M = energy_limit / w_t

        return getattr(model, VAR_DEMANDUNMET)[s, h, e, t_clust] <= M * (1 - v_autalive)

    container.CON_AUTUnmetDemandGated = Constraint(
        getattr(model, SET_DEMANDTUPLE), s_time, rule=rule
    )


# ---------------------------------------------------------------------
# Restrict CROSS imports while alive: Imp <= M * (1 - y)
# ---------------------------------------------------------------------
def _con_aut_no_cross_import_while_alive(
    container,
    model,
    ecs: Ecs,
    imports,
    times: Times,
    mass_unit,
    power_unit,
    stime_to_tid,
    s_time,
) -> None:
    S_ImpTuple = getattr(model, SET_IMPTUPLE)

    # 1) Build a list of indices we actually constrain (CROSS only)
    # DB: Do you really need two lists here? Seems like you could just do
    #     cross_typed and extract the key when you need it be calling
    #     e.key for (s, h, e) in cross_typed when you need the string. That would
    #     improve readability
    cross_index = []  # elements are (s, h, e_key, t_elem)
    cross_typed = []  # same but with typed EcId for M lookup: (s, h, e_id, t_elem)

    for s, h, e_key in S_ImpTuple:
        e_id = EcId(e_key)
        if ecs.is_energy(e_id) and ecs.get_imp_exp_type(e_id) == ImpExpType.CROSS:
            for t_elem in s_time:
                cross_index.append((s, h, e_key, t_elem))
                cross_typed.append((s, h, e_id, t_elem))

    # If no CROSS imports exist, don't add the constraint
    if not cross_index:
        return

    # 2) Precompute Big-M only for those indices
    M = {}
    for s, h, e_id, t_elem in cross_typed:
        s_id = StageId(s)
        h_id = HubId(h)

        unit_pow = (
            get_ec_model_unit(ecs.get_unit(e_id), mass_unit, power_unit) / TimeUnit.H
        )
        t_id = stime_to_tid[t_elem]

        # (A) time-dependent max if defined
        imp_max = imports.get_max(s_id, h_id, e_id)
        if imp_max.has_values:
            v = imp_max.get_value(t_id)
            if v is not None:
                M[(s, h, e_id, t_elem)] = max(0.0, v.to_float(unit=unit_pow))
                continue

        # (B) finite sum_max -> distribute across horizon as average
        sm = imports.get_sum_max(s_id, h_id, e_id, ecs).to_float(
            unit=get_ec_model_unit(ecs.get_unit(e_id), mass_unit, power_unit)
        )
        if sm != float("inf") and times.num_horizon_ts > 0:
            M[(s, h, e_id, t_elem)] = max(0.0, sm / times.num_horizon_ts)
            continue

        # (C) fallback
        M[(s, h, e_id, t_elem)] = 1e6

    # 3) Constraint rule over exactly cross_index
    #   DB: Have you actually tried running this on a clustered horizon? I think this
    #       would fail because you are indexing the whole logic over t_elem from
    #       time_horizon but the imports are defined over time (clustered). Stuff like
    #       this would become more apparent if you defined the constraints straight over
    #       the preconfigured sets in the model, not by using your own iteratively
    #       defined index lists. I would do it like this:
    #
    #       setattr(
    #           container,
    #           CON_AUTNOCROSSIMPORTWHENALIVE,
    #           Constraint(
    #               getattr(model, SET_IMPTUPLE),
    #               getattr(model, SET_TIMEHORIZON),  <-- Here it's abundandly clear
    #               rule=_rule_imp,
    #           ),
    #       )
    #
    #   And of course you will need to access the clustered time step of the current
    #   full horizon timestep again, as before.
    def _rule_imp(_blk, s, h, e_key, t_elem):
        e_id = EcId(e_key)
        y = getattr(model, VAR_AUTALIVE)[s, t_elem]
        return getattr(model, VAR_IMP)[s, h, e_key, t_elem] <= M[
            (s, h, e_id, t_elem)
        ] * (1 - y)

    setattr(
        container,
        CON_AUTNOCROSSIMPORTWHENALIVE,
        Constraint(cross_index, rule=_rule_imp),
    )


# ---------------------------------------------------------------------
# Autonomy hours definition on s_time_horizon
#   DB: I would prefer if you stuck to one style of defining your constraints.
#       All the previous ones were done with rule functions, and this one uses an expr.
#       Also, think about the definition of the objective variable itself here when we
#       have mutliple stages. Currently you just sum them all up, but are we sure this
#       is scientifically correct? I don't know the answer, and this is very practical,
#       but this should be discussed at some point.
# ---------------------------------------------------------------------
def _con_aut_hours_definition(container, model, s_stage, s_time_hor) -> None:
    expr = 0
    for s in s_stage:
        for t_elem in s_time_hor:
            expr += getattr(model, VAR_AUTALIVE)[s, t_elem]

    setattr(
        container,
        CON_AUTHOURSDEF,
        Constraint(expr=getattr(model, VAR_AUTONOMY) == expr),
    )
