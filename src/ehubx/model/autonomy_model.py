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
    PAR_DEMANDUNMETALLOWED,
    SET_DEMANDPROFILETUPLE,
    SET_DEMANDSUMTUPLE,
    SET_DEMANDTUPLE,
    VAR_DEMANDUNMET,
)
from ehubx.model.ec_model import get_ec_model_unit
from ehubx.model.export_model import SET_EXPTUPLE, VAR_EXP
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

DEF_AUT_BIGM_FALLBACK: float = 1e6
"""Default value for the fallback Big-M for autonomy import gating
when no finite bound is available."""

DEF_AUT_BIGM_STRICT: bool = False
"""Default value controlling Big-M fallback behavior. If True, raises an error
when no finite bound is available instead of using a fallback Big-M."""

CON_AUTENABLEDSET: str = "C_AutEnabledSet"
"""Name of container holding all constraints active when autonomy is enabled."""

CON_AUTZERO: str = "C_AutZero"
"""Name of constraint forcing autonomy duration to zero when autonomy is disabled."""

CON_AUTPREFIX: str = "C_AutPrefix"
"""Name of constraint enforcing prefix structure of the alive variable."""

CON_AUTNOCROSSIMPORTWHENALIVE: str = "C_AutNoCrossImportWhenAlive"
"""Name of constraint prohibiting cross-import of energy carriers while the
system is autonomous."""

CON_AUTNOCROSSEXPORTWHENALIVE: str = "C_AutNoCrossExportWhenAlive"
"""Name of constraint prohibiting cross-export of energy carriers while the
system is autonomous."""

CON_AUTUNMETDEMANDGATED: str = "C_AutUnmetDemandGated"
"""Name of constraint linking unmet demand to autonomy status."""

CON_AUTHOURSDEF: str = "C_AutHoursDef"
"""Name of constraint defining total autonomy duration when autonomy is enabled."""

LOG_MODULE_STR: str = "mod/autonomy"


def build(model, system: EnergySystem) -> None:
    times: Times = system.times
    ecs: Ecs = system.ecs

    s_stage = getattr(model, SET_STAGE)
    s_time_hor = getattr(model, SET_TIMEHORIZON)

    # Start measuring build time
    start = datetime.now()

    # Variables and configuration
    setattr(model, VAR_AUTALIVE, Var(s_stage, s_time_hor, domain=Binary))
    setattr(
        model,
        VAR_AUTONOMY,
        Var(getattr(model, SET_STAGE), domain=NonNegativeReals),
    )

    setattr(model, PAR_AUTENABLE, Param(within=Binary, initialize=0, mutable=True))

    # Enabled constraint "set"
    con_enabled = Block()
    setattr(model, CON_AUTENABLEDSET, con_enabled)

    # Constraints
    con_aut_alive_nonincreasing(con_enabled, model, s_stage, s_time_hor)
    _con_aut_no_cross_import_while_alive(
        con_enabled,
        model,
        ecs=ecs,
        imports=system.imports,
        times=times,
        mass_unit=system.mass_unit,
        power_unit=system.power_unit,
    )
    _con_aut_no_cross_export_while_alive(
        con_enabled,
        model,
        ecs=ecs,
        exports=system.exports,
        times=times,
        mass_unit=system.mass_unit,
        power_unit=system.power_unit,
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
    def _rule_autonomy_zero(_m, s):
        return getattr(model, VAR_AUTONOMY)[s] == 0

    setattr(
        model,
        CON_AUTZERO,
        Constraint(getattr(model, SET_STAGE), rule=_rule_autonomy_zero),
    )
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


def configure_autonomy(model, enabled: bool) -> None:
    # Gate unmet demand according to autonomy
    if model.find_component(PAR_DEMANDUNMETALLOWED) is not None:
        user_flags = getattr(model, "autonomy_allow_unmet_demand_user", {})

        for s in getattr(model, SET_STAGE):
            user_flag = user_flags.get(s, None)

            if not enabled:
                effective_flag = 0
            else:
                effective_flag = 1 if user_flag is True else 0

            getattr(model, PAR_DEMANDUNMETALLOWED)[s].set_value(effective_flag)

    # Toggle autonomy constraint states
    if model.find_component(CON_AUTZERO) is not None:
        set_autonomy_enabled(model, enabled=enabled)


# ---------------------------------------------------------------------
# Non increasing alive prefixes (1,0) to keep continuity on s_time_horizon
# ---------------------------------------------------------------------
def con_aut_alive_nonincreasing(container, model, s_stage, s_time_hor) -> None:
    def _rule_prefix(_m, s, t_hor):
        if t_hor == s_time_hor.last():
            return Constraint.Skip
        t_hor_next = s_time_hor.next(t_hor)
        return (
            getattr(model, VAR_AUTALIVE)[s, t_hor]
            >= getattr(model, VAR_AUTALIVE)[s, t_hor_next]
        )

    setattr(
        container,
        CON_AUTPREFIX,
        Constraint(s_stage, s_time_hor, rule=_rule_prefix),
    )


# ---------------------------------------------------------------------
# Gate unmet demand: V_DemandUnmet <= demand(t) * (1 - v_autalive)
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

            M = dv.to_float(unit=unit_pw)

        # B) sum tuples -> Big-M per timestep from total energy / weight
        else:
            energy_limit = getattr(model, PAR_DEMANDSUMBIGM)[s, h, e]
            w_t = times.get_weight(StageId(s), t_clust_id)
            if w_t <= 0:
                return Constraint.Skip
            M = energy_limit / w_t

        # Strict mode (flag=0): unmet demand is globally forbidden.
        # Relaxed mode (flag=1): unmet demand is permitted only after autonomy is lost
        flag = getattr(model, PAR_DEMANDUNMETALLOWED)[s]
        return getattr(model, VAR_DEMANDUNMET)[s, h, e, t_clust] <= M * flag * (
            1 - v_autalive
        )

    setattr(
        container,
        CON_AUTUNMETDEMANDGATED,
        Constraint(getattr(model, SET_DEMANDTUPLE), s_time, rule=rule),
    )


# ---------------------------------------------------------------------
# Restrict CROSS imports while alive:
# Imp[s,h,e,t_cl] <= M[s,h,e,t_cl] * (1 - v_autalive[s,t_hor])
# ---------------------------------------------------------------------
def _con_aut_no_cross_import_while_alive(
    container,
    model,
    ecs: Ecs,
    imports,
    times: Times,
    mass_unit,
    power_unit,
) -> None:
    s_imp_tuple = getattr(model, SET_IMPTUPLE)
    s_time_hor = getattr(model, SET_TIMEHORIZON)

    # Build typed CROSS import tuples once
    cross_typed = []
    for s, h, e_key in s_imp_tuple:
        e_id = EcId(e_key)
        if ecs.is_energy(e_id) and ecs.get_imp_exp_type(e_id) == ImpExpType.CROSS:
            cross_typed.append((s, h, e_id))

    if not cross_typed:
        return

    # Precompute Big-M on clustered time indices only
    # Key: (s, h, e_id, t_cl)
    M = {}
    for s, h, e_id in cross_typed:
        s_id = StageId(s)
        h_id = HubId(h)

        for t_cl in getattr(model, SET_TIME):
            t_cl_id = TimeId(t_cl)
            unit_pow = (
                get_ec_model_unit(ecs.get_unit(e_id), mass_unit, power_unit)
                / TimeUnit.H
            )

            # (A) time-dependent max if defined
            imp_max = imports.get_max(s_id, h_id, e_id)
            if imp_max.has_values:
                v = imp_max.get_value(t_cl_id)
                if v is not None:
                    M[(s, h, e_id, t_cl)] = max(0.0, v.to_float(unit=unit_pow))
                    continue

            # (B) finite sum_max -> distribute across full horizon as average
            sm = imports.get_sum_max(s_id, h_id, e_id, ecs).to_float(
                unit=get_ec_model_unit(ecs.get_unit(e_id), mass_unit, power_unit)
            )
            if sm != float("inf") and times.num_horizon_ts > 0:
                M[(s, h, e_id, t_cl)] = max(0.0, sm / times.num_horizon_ts)
                continue

            # (C) fallback
            if DEF_AUT_BIGM_STRICT:
                raise ValueError(
                    f"No finite Big-M bound available for"
                    f"autonomy cross-import restriction "
                    f"(stage={s}, hub={h}, ec={e_id.key}, time={t_cl}). "
                    f"Specify an import max profile or finite sum_max."
                )

            logging.log_file(
                f"Warning: Using fallback Big-M={DEF_AUT_BIGM_FALLBACK} for autonomy "
                f"cross-import restriction "
                f"(stage={s}, hub={h}, ec={e_id.key}, time={t_cl}). "
                f"Specify an import max profile or finite sum_max to avoid fallback.",
                module=LOG_MODULE_STR,
            )

            M[(s, h, e_id, t_cl)] = DEF_AUT_BIGM_FALLBACK

    def _rule_imp(_blk, s, h, e_key, t_hor):
        e_id = EcId(e_key)

        # Skip non-CROSS tuples
        if not (ecs.is_energy(e_id) and ecs.get_imp_exp_type(e_id) == ImpExpType.CROSS):
            return Constraint.Skip

        # Chronological alive variable
        v_autalive = getattr(model, VAR_AUTALIVE)[s, t_hor]

        # Map full horizon timestep -> clustered timestep
        t_cl = times.get_cluster_ts(StageId(s), TimeId(t_hor)).key_as_int

        return getattr(model, VAR_IMP)[s, h, e_key, t_cl] <= M[(s, h, e_id, t_cl)] * (
            1 - v_autalive
        )

    setattr(
        container,
        CON_AUTNOCROSSIMPORTWHENALIVE,
        Constraint(
            s_imp_tuple,
            s_time_hor,
            rule=_rule_imp,
        ),
    )


# ---------------------------------------------------------------------
# Autonomy hours definition on s_time_horizon
# ---------------------------------------------------------------------
def _con_aut_hours_definition(container, model, s_stage, s_time_hor) -> None:
    def _rule_aut_hours(_blk, s):
        expr = sum(getattr(model, VAR_AUTALIVE)[s, t_hor] for t_hor in s_time_hor)
        return getattr(model, VAR_AUTONOMY)[s] == expr

    setattr(
        container,
        CON_AUTHOURSDEF,
        Constraint(s_stage, rule=_rule_aut_hours),
    )


# ---------------------------------------------------------------------
# Restrict CROSS exports while alive:
# Exp[s,h,e,t_cl] <= M[s,h,e,t_cl] * (1 - v_autalive[s,t_hor])
# ---------------------------------------------------------------------
def _con_aut_no_cross_export_while_alive(
    container,
    model,
    ecs: Ecs,
    exports,
    times: Times,
    mass_unit,
    power_unit,
) -> None:
    s_exp_tuple = getattr(model, SET_EXPTUPLE)
    s_time_hor = getattr(model, SET_TIMEHORIZON)
    # Build typed CROSS export tuples once
    cross_typed = []
    for s, h, e_key in s_exp_tuple:
        e_id = EcId(e_key)
        if ecs.is_energy(e_id) and ecs.get_imp_exp_type(e_id) == ImpExpType.CROSS:
            cross_typed.append((s, h, e_id))
    if not cross_typed:
        return
    # Precompute Big-M on clustered time indices only
    M = {}
    for s, h, e_id in cross_typed:
        s_id = StageId(s)
        h_id = HubId(h)
        for t_cl in getattr(model, SET_TIME):
            t_cl_id = TimeId(t_cl)
            unit_pow = (
                get_ec_model_unit(ecs.get_unit(e_id), mass_unit, power_unit)
                / TimeUnit.H
            )
            # (A) time-dependent max if defined
            exp_max = exports.get_max(s_id, h_id, e_id)
            if exp_max.has_values:
                v = exp_max.get_value(t_cl_id)
                if v is not None:
                    M[(s, h, e_id, t_cl)] = max(0.0, v.to_float(unit=unit_pow))
                    continue
            # (B) finite sum_max -> distribute across full horizon as average
            sm = exports.get_sum_max(s_id, h_id, e_id, ecs).to_float(
                unit=get_ec_model_unit(ecs.get_unit(e_id), mass_unit, power_unit)
            )
            if sm != float("inf") and times.num_horizon_ts > 0:
                M[(s, h, e_id, t_cl)] = max(0.0, sm / times.num_horizon_ts)
                continue
            # (C) fallback
            if DEF_AUT_BIGM_STRICT:
                raise ValueError(
                    f"No finite Big-M bound available for "
                    f"autonomy cross-export restriction "
                    f"(stage={s}, hub={h}, ec={e_id.key}, time={t_cl}). "
                    f"Specify an export max profile or finite sum_max."
                )
            logging.log_file(
                f"Warning: Using fallback Big-M={DEF_AUT_BIGM_FALLBACK} for autonomy "
                f"cross-export restriction "
                f"(stage={s}, hub={h}, ec={e_id.key}, time={t_cl}). "
                f"Specify an export max profile or finite sum_max to avoid fallback.",
                module=LOG_MODULE_STR,
            )
            M[(s, h, e_id, t_cl)] = DEF_AUT_BIGM_FALLBACK

    def _rule_exp(_blk, s, h, e_key, t_hor):
        e_id = EcId(e_key)
        # Skip non-CROSS tuples
        if not (ecs.is_energy(e_id) and ecs.get_imp_exp_type(e_id) == ImpExpType.CROSS):
            return Constraint.Skip
        # Chronological alive variable
        v_autalive = getattr(model, VAR_AUTALIVE)[s, t_hor]
        # Map full horizon timestep -> clustered timestep
        t_cl = times.get_cluster_ts(StageId(s), TimeId(t_hor)).key_as_int
        return getattr(model, VAR_EXP)[s, h, e_key, t_cl] <= M[(s, h, e_id, t_cl)] * (
            1 - v_autalive
        )

    setattr(
        container,
        CON_AUTNOCROSSEXPORTWHENALIVE,
        Constraint(
            s_exp_tuple,
            s_time_hor,
            rule=_rule_exp,
        ),
    )
