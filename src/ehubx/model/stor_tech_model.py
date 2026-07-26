"""Storage technology submodel"""

from datetime import datetime

from pyomo.core import Any, Constraint, Model, NonNegativeReals, Param, Set, Var

from ehubx.core import common, logging
from ehubx.data.ec_data import Ecs
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.stor_tech_data import StorageTechs
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.time_data import TimeId, Times
from ehubx.data.unit import CurrencyUnit, MassUnit, PowerUnit
from ehubx.model.ec_model import get_ec_model_unit
from ehubx.model.tech_model import (
    SET_TECH,
    SET_TECHTUPLE,
    VAR_TECHCAP,
    VAR_YTECHUSED,
)
from ehubx.model.times_model import SET_TIME, SET_TIMEHORIZON


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/stor_tech"
"""String identifying the storage technology model for logging purposes"""

SET_STORTECH: str = "S_StorTech"
"""Name of set with storage techs"""

SET_STORTECHTUPLE: str = "S_StorTechTuple"
"""Name of set with storage tech tuples"""

VAR_STORTECHINFLOW: str = "V_StorTechInflow"
"""Name of variable for storage tech inflow"""

VAR_STORTECHOUTFLOW: str = "V_StorTechOutflow"
"""Name of variable for storage tech outflow"""

VAR_STORTECHENERGY: str = "V_StorTechEnergy"
"""Name of variable for energy stored in storage techs"""

VAR_STORTECHENERGYFINAL: str = "V_StorTechEnergyFinal"
"""Name of variable for the storage energy level after the last horizon timestep"""

VAR_STORTECHFILLCOST: str = "V_StorTechFillCost"
"""Name of variable for the storage fill cost"""

VAR_STORTECHFILLCOSTTOTAL: str = "V_StorTechFillCostTotal"
"""Name of variable for the total cost of pre-filled energy in non-cyclic
storage"""

PAR_STORTECHEC: str = "P_StorTechEc"
"""Name of parameter specifying the ecs stored in storage techs"""

CON_STORTECHINFLOWMAX: str = "C_StorTechInflowMax"
"""Name of constraint limiting maximal stor tech inflow based on maximal
charging speed and tech capacity"""

CON_STORTECHOUTFLOWMAX: str = "C_StorTechOutflowMax"
"""Name of constraint limiting maximal stor tech outflow based on maximal
discharging speed and tech capacity"""

CON_STORTECHUSED: str = "C_StorTechUsed"
"""Name of constraint identifying tech usage for storage techs"""

CON_STORTECHCHARGINGDYNAMIC: str = "C_StorTechChargingDynamic"
"""Name of constraint specifying the charging and discharging dynamic for
storage techs. Contains a periodic approach connecting the last and first
time steps in terms of energy levels"""

CON_STORTECHENERGYMIN: str = "C_StorTechEnergyMin"
"""Name of constraint setting a lower limit for stored energy based on minimal
SOC and tech capacity"""

CON_STORTECHENERGYMAX: str = "C_StorTechEnergyMax"
"""Name of constraint setting a lower limit for stored energy based on maximal
SOC and tech capacity"""

CON_STORTECHENERGYINIT: str = "C_StorTechEnergyInit"
"""Name of constraint setting the initial storage energy based on the
parameter 'soc_init'"""

CON_STORTECHENERGYFINALSOCMIN: str = "C_StorTechEnergyFinalSocMin"
"""Name of constraint setting a lower limit for the final stored energy of
non-cyclic storage based on minimal SOC and tech capacity"""

CON_STORTECHENERGYFINALSOCMAX: str = "C_StorTechEnergyFinalSocMax"
"""Name of constraint setting an upper limit for the final stored energy of
non-cyclic storage based on maximal SOC and tech capacity"""

CON_STORTECHENERGYFINAL: str = "C_StorTechEnergyFinal"
"""Name of constraint setting the final stored energy of cyclic storage equal to
its initial stored energy"""

CON_STORTECHFILLCOST: str = "C_StorTechFillCost"
"""Name of constraint defining the per-tuple storage fill cost"""

CON_STORTECHFILLCOSTTOTAL: str = "C_StorTechFillCostTotal"
"""Name of constraint setting the total fill cost of non-cyclic storage as the
sum of the tech-specific fill costs"""


def build(model: Model, system: EnergySystem) -> None:
    """
    Builds the storage technology submodel. For a mathematical description
    in thorough detail, please refer to the section 'Storage model' in the
    documentation.

    :param model: Pyomo model
    :type model: Model
    :param system: Energy system data
    :type system: EnergySystem
    """
    # Start measuring build time
    start = datetime.now()
    _build_base(model, system)
    # Logging
    elapsed = datetime.now() - start
    logging.log_file(
        f"Built storage tech module. Elapsed time: {int(elapsed.total_seconds())}s",
        module=LOG_MODULE_STR,
    )


def _build_base(model: Model, system: EnergySystem) -> None:
    # Extract data from modules
    stages: Stages = system.stages
    techs: Techs = system.techs
    stor_techs: StorageTechs = system.stor_techs
    times: Times = system.times
    ecs: Ecs = system.ecs
    mass_unit: MassUnit = system.mass_unit
    power_unit: PowerUnit = system.power_unit
    # [SET] Storage techs
    setattr(
        model,
        SET_STORTECH,
        Set(
            within=getattr(model, SET_TECH), initialize=[x.key for x in stor_techs.ids]
        ),
    )
    # [SET] Storage techs tuples
    setattr(
        model,
        SET_STORTECHTUPLE,
        Set(
            within=getattr(model, SET_TECHTUPLE),
            initialize=[
                (s, h, x)
                for (s, h, x) in getattr(model, SET_TECHTUPLE)
                if x in getattr(model, SET_STORTECH)
            ],
        ),
    )
    # [PAR] Stored ec
    setattr(
        model,
        PAR_STORTECHEC,
        Param(
            getattr(model, SET_STORTECH),
            within=Any,
            initialize={x.key: stor_techs.get_ec(x).key for x in stor_techs.ids},
        ),
    )
    # [VAR] Storage inflow
    setattr(
        model,
        VAR_STORTECHINFLOW,
        Var(
            getattr(model, SET_STORTECHTUPLE),
            getattr(model, SET_TIME),
            domain=NonNegativeReals,
        ),
    )
    # [VAR] Storage outflow
    setattr(
        model,
        VAR_STORTECHOUTFLOW,
        Var(
            getattr(model, SET_STORTECHTUPLE),
            getattr(model, SET_TIME),
            domain=NonNegativeReals,
        ),
    )
    # [VAR] Final energy level
    setattr(
        model,
        VAR_STORTECHENERGYFINAL,
        Var(getattr(model, SET_STORTECHTUPLE), within=NonNegativeReals),
    )
    # [VAR] Per-tuple fill cost
    setattr(
        model,
        VAR_STORTECHFILLCOST,
        Var(getattr(model, SET_STORTECHTUPLE), within=NonNegativeReals),
    )
    # [VAR] Total fill cost
    setattr(
        model,
        VAR_STORTECHFILLCOSTTOTAL,
        Var(within=NonNegativeReals),
    )
    # [CON] Respect maximal inflow and outflow (based on capacity)
    _con_stor_tech_inoutflow_max(model, stor_techs)
    # [CON] Tech usage (monitored over sum summed-up sum of inflow and outflow)
    _con_stor_tech_used(model, system)
    # [VAR] Storage energy
    setattr(
        model,
        VAR_STORTECHENERGY,
        Var(
            getattr(model, SET_STORTECHTUPLE),
            getattr(model, SET_TIMEHORIZON),
            domain=NonNegativeReals,
        ),
    )
    # [CON] Charging dynamic: Energy level changes from one horizon_ts to the
    #       next based on flow and standby loss. A cyclical SOC approach is
    #       used so that the flow at the last horizon_ts charges the first
    #       horizon_ts
    # _con_stor_tech_charging_dynamic(model, stor_techs, times)
    # [CON] Respect minimal and maximal storage energy levels (based on cap)
    _con_stor_tech_energy_minmax(model, stor_techs)
    # [CON] Initial energy. Constraint depends on initial SOC value in data
    #       model. For inf, the first energy value of the first stage can be
    #       chosen by the optimizer. Otherwise, energy is set in all stages by
    #       the initial  SOC value
    _con_stor_tech_energy_init(model, stages, techs, stor_techs)
    # [CON] charging dynamic
    _con_stor_tech_charging_dynamic(model, stor_techs, times)
    # [CON] SOC bounds on the final energy level
    _con_stor_tech_energy_final_soc(model, stor_techs)
    # [CON] Final energy level: cyclic: equals initial; non-cyclic: set by
    # the charging dynamic at the last horizon timestep
    _con_stor_tech_energy_final(model, stor_techs)
    # [CON] Per-tuple fill cost
    _con_stor_tech_fill_cost(model, stor_techs, ecs, mass_unit, power_unit)
    # [CON] Total fill cost
    _con_stor_tech_fill_cost_total(model)


def _con_stor_tech_inoutflow_max(model: Model, stor_techs: StorageTechs) -> None:
    def __rule_stor_tech_inflow_max(model, s, h, x, t):
        # Get parameter
        charge_max = stor_techs.get_charge_max(StageId(s), TechId(x)).to_float()
        if charge_max == float("inf"):
            return Constraint.Skip
        # Calculate maximal inflow
        inflow_max = charge_max * getattr(model, VAR_TECHCAP)[s, h, x]
        # Set constraint
        return getattr(model, VAR_STORTECHINFLOW)[s, h, x, t] <= inflow_max

    def __rule_stor_tech_outflow_max(model, s, h, x, t):
        # Get parameter
        discharge_max = stor_techs.get_discharge_max(StageId(s), TechId(x)).to_float()
        if discharge_max == float("inf"):
            return Constraint.Skip
        # Calculate maximal outflow
        outflow_max = discharge_max * getattr(model, VAR_TECHCAP)[s, h, x]
        # Set constraint
        return getattr(model, VAR_STORTECHOUTFLOW)[s, h, x, t] <= outflow_max

    setattr(
        model,
        CON_STORTECHINFLOWMAX,
        Constraint(
            getattr(model, SET_STORTECHTUPLE),
            getattr(model, SET_TIME),
            rule=__rule_stor_tech_inflow_max,
        ),
    )
    setattr(
        model,
        CON_STORTECHOUTFLOWMAX,
        Constraint(
            getattr(model, SET_STORTECHTUPLE),
            getattr(model, SET_TIME),
            rule=__rule_stor_tech_outflow_max,
        ),
    )


def _con_stor_tech_used(model: Model, system: EnergySystem) -> None:
    # Extract data from modules
    ecs: Ecs = system.ecs
    stor_techs: StorageTechs = system.stor_techs
    times: Times = system.times
    mass_unit: MassUnit = system.mass_unit
    power_unit: PowerUnit = system.power_unit

    def __rule_stor_tech_used(model, s, h, x):
        # Get parameters
        ec = stor_techs.get_ec(TechId(x))
        ec_unit = get_ec_model_unit(ecs.get_unit(ec), mass_unit, power_unit)
        # a) bigM by tech capacity and charge_max, discharge_max
        var_cap = getattr(model, VAR_TECHCAP)[s, h, x]
        cap_max = var_cap.ub
        charge_max = stor_techs.get_charge_max(StageId(s), TechId(x)).to_float()
        discharge_max = stor_techs.get_discharge_max(StageId(s), TechId(x)).to_float()
        inflow_max = cap_max * min(charge_max, 1)
        outflow_max = cap_max * min(discharge_max, 1)
        bigm_cap = (inflow_max + outflow_max) * times.num_horizon_ts
        bigm = bigm_cap
        # b) bigM by heuristic limits
        max_sum_in = system.get_heur_limit_max_sum_in(
            StageId(s), HubId(h), ec
        ).to_float(unit=ec_unit)
        max_sum_out = system.get_heur_limit_max_sum_out(
            StageId(s), HubId(h), ec
        ).to_float(unit=ec_unit)
        bigm_heur = max_sum_in + max_sum_out
        bigm = min(bigm, bigm_heur)
        bigm = max(bigm, 1) + common.EPS_BIGM
        # Calculate total summed-up flow in both directions
        bigm += common.EPS_BIGM
        flow_abs_sum = sum(
            times.get_weight(StageId(s), TimeId(t))
            * (
                getattr(model, VAR_STORTECHINFLOW)[s, h, x, t]
                + getattr(model, VAR_STORTECHOUTFLOW)[s, h, x, t]
            )
            for t in getattr(model, SET_TIME)
        )
        # Set constraint
        return flow_abs_sum <= bigm * getattr(model, VAR_YTECHUSED)[s, h, x]

    setattr(
        model,
        CON_STORTECHUSED,
        Constraint(getattr(model, SET_STORTECHTUPLE), rule=__rule_stor_tech_used),
    )


def _con_stor_tech_charging_dynamic(
    model: Model, stor_techs: StorageTechs, times: Times
) -> None:
    # Get first and last full-horizon timesteps
    t_hor_first = getattr(model, SET_TIMEHORIZON).first()
    t_hor_last = getattr(model, SET_TIMEHORIZON).last()

    def __rule_stor_tech_charging_dynamic(model, s, h, x, t_hor):
        # Get parameters
        t = times.get_cluster_ts(StageId(s), TimeId(t_hor)).key_as_int
        in_eff = stor_techs.get_in_eff(StageId(s), TechId(x)).to_float()
        out_eff = stor_techs.get_out_eff(StageId(s), TechId(x)).to_float()
        standby_loss = stor_techs.get_standby_loss(StageId(s), TechId(x)).to_float()
        # Calculate energy flow (for the storage tech) at this timestep
        energy_flow = (
            in_eff * getattr(model, VAR_STORTECHINFLOW)[s, h, x, t]
            - getattr(model, VAR_STORTECHOUTFLOW)[s, h, x, t] / out_eff
        )
        # Calculate energy level at next horizon_ts
        energy_next = (1 - standby_loss) * getattr(model, VAR_STORTECHENERGY)[
            s, h, x, t_hor
        ] + energy_flow
        # Last horizon timestep: cyclic wraps back, non-cyclic writes to the
        # final-energy variable so the last timestep's flows are still debited
        if t_hor == t_hor_last:
            if stor_techs.get_cyclic(HubId(h), TechId(x)):
                return (
                    getattr(model, VAR_STORTECHENERGY)[s, h, x, t_hor_first]
                    == energy_next
                )
            return getattr(model, VAR_STORTECHENERGYFINAL)[s, h, x] == energy_next
        # All other timesteps
        t_hor_next = getattr(model, SET_TIMEHORIZON).next(t_hor)
        return getattr(model, VAR_STORTECHENERGY)[s, h, x, t_hor_next] == energy_next

    setattr(
        model,
        CON_STORTECHCHARGINGDYNAMIC,
        Constraint(
            getattr(model, SET_STORTECHTUPLE),
            getattr(model, SET_TIMEHORIZON),
            rule=__rule_stor_tech_charging_dynamic,
        ),
    )


def _con_stor_tech_energy_minmax(model: Model, stor_techs: StorageTechs) -> None:
    def __rule_stor_tech_energy_min(model, s, h, x, t):
        # Get parameter
        soc_min = stor_techs.get_soc_min(StageId(s), TechId(x)).to_float()
        # Calculate minimal energy
        energy_min = soc_min * getattr(model, VAR_TECHCAP)[s, h, x]
        # Set constraint
        return getattr(model, VAR_STORTECHENERGY)[s, h, x, t] >= energy_min

    def __rule_stor_tech_energy_max(model, s, h, x, t):
        # Get parameter
        soc_max = min(stor_techs.get_soc_max(StageId(s), TechId(x)).to_float(), 1)
        # Calculate maximal energy
        energy_max = soc_max * getattr(model, VAR_TECHCAP)[s, h, x]
        # Set constraint
        return getattr(model, VAR_STORTECHENERGY)[s, h, x, t] <= energy_max

    setattr(
        model,
        CON_STORTECHENERGYMIN,
        Constraint(
            getattr(model, SET_STORTECHTUPLE),
            getattr(model, SET_TIMEHORIZON),
            rule=__rule_stor_tech_energy_min,
        ),
    )
    setattr(
        model,
        CON_STORTECHENERGYMAX,
        Constraint(
            getattr(model, SET_STORTECHTUPLE),
            getattr(model, SET_TIMEHORIZON),
            rule=__rule_stor_tech_energy_max,
        ),
    )


def _con_stor_tech_energy_init(
    model: Model, stages: Stages, techs: Techs, stor_techs: StorageTechs
) -> None:
    # Get initial stage and first full-horizon timestep
    t_hor_0 = getattr(model, SET_TIMEHORIZON).first()

    def __rule_stor_tech_energy_init(model, s, h, x):
        # Parameter
        soc_init = stor_techs.get_soc_init(HubId(h), TechId(x)).to_float()
        # Case 1: Not first stage => Set to same initial energy as first possible stage
        for s_0 in stages.ids_in_order:
            if StageId(s) == s_0:
                break
            if s_0 in techs.get_allowed_stages(TechId(x)):
                return (
                    getattr(model, VAR_STORTECHENERGY)[s, h, x, t_hor_0]
                    == getattr(model, VAR_STORTECHENERGY)[s_0.key, h, x, t_hor_0]
                )
        # Case 2: soc_init is a real value => Set the SOC of first stage
        if soc_init < float("inf"):
            return (
                getattr(model, VAR_STORTECHENERGY)[s, h, x, t_hor_0]
                == soc_init * getattr(model, VAR_TECHCAP)[s, h, x]
            )
        # Case 3: soc_init is infinite => Let optimizer choose the value
        return Constraint.Skip

    setattr(
        model,
        CON_STORTECHENERGYINIT,
        Constraint(
            getattr(model, SET_STORTECHTUPLE), rule=__rule_stor_tech_energy_init
        ),
    )


def _con_stor_tech_energy_final_soc(model: Model, stor_techs: StorageTechs) -> None:
    def __rule_min(model, s, h, x):
        if stor_techs.get_cyclic(HubId(h), TechId(x)):
            return Constraint.Skip
        soc_min = stor_techs.get_soc_min(StageId(s), TechId(x)).to_float()
        return (
            getattr(model, VAR_STORTECHENERGYFINAL)[s, h, x]
            >= soc_min * getattr(model, VAR_TECHCAP)[s, h, x]
        )

    def __rule_max(model, s, h, x):
        if stor_techs.get_cyclic(HubId(h), TechId(x)):
            return Constraint.Skip
        soc_max = stor_techs.get_soc_max(StageId(s), TechId(x)).to_float()
        return (
            getattr(model, VAR_STORTECHENERGYFINAL)[s, h, x]
            <= min(soc_max, 1) * getattr(model, VAR_TECHCAP)[s, h, x]
        )

    setattr(
        model,
        CON_STORTECHENERGYFINALSOCMIN,
        Constraint(getattr(model, SET_STORTECHTUPLE), rule=__rule_min),
    )
    setattr(
        model,
        CON_STORTECHENERGYFINALSOCMAX,
        Constraint(getattr(model, SET_STORTECHTUPLE), rule=__rule_max),
    )


def _con_stor_tech_energy_final(model: Model, stor_techs: StorageTechs) -> None:
    t_hor_first = getattr(model, SET_TIMEHORIZON).first()

    def __rule_stor_tech_energy_final(model, s, h, x):
        # Non-cyclic storage: the final level is set by the charging dynamic at
        # the last horizon timestep
        if not stor_techs.get_cyclic(HubId(h), TechId(x)):
            return Constraint.Skip
        # Cyclic storage: the final level equals the initial level
        return (
            getattr(model, VAR_STORTECHENERGYFINAL)[s, h, x]
            == getattr(model, VAR_STORTECHENERGY)[s, h, x, t_hor_first]
        )

    setattr(
        model,
        CON_STORTECHENERGYFINAL,
        Constraint(
            getattr(model, SET_STORTECHTUPLE), rule=__rule_stor_tech_energy_final
        ),
    )


def _con_stor_tech_fill_cost_total(model: Model) -> None:
    def __rule_fill_cost_total(m):
        return getattr(m, VAR_STORTECHFILLCOSTTOTAL) == sum(
            getattr(m, VAR_STORTECHFILLCOST)[s, h, x]
            for (s, h, x) in getattr(m, SET_STORTECHTUPLE)
        )

    setattr(model, CON_STORTECHFILLCOSTTOTAL, Constraint(rule=__rule_fill_cost_total))


def _con_stor_tech_fill_cost(
    model: Model, stor_techs: StorageTechs, ecs: Ecs, mass_unit, power_unit
) -> None:
    t_hor_0 = getattr(model, SET_TIMEHORIZON).first()

    def __rule_fill_cost(m, s, h, x):
        if stor_techs.get_cyclic(HubId(h), TechId(x)):
            return getattr(m, VAR_STORTECHFILLCOST)[s, h, x] == 0
        price_val = stor_techs.get_fill_price(HubId(h), TechId(x))
        ec_id = stor_techs.get_ec(TechId(x))
        unit_energy = get_ec_model_unit(ecs.get_unit(ec_id), mass_unit, power_unit)
        price = price_val.to_float(unit=CurrencyUnit.CHF / unit_energy)
        return (
            getattr(m, VAR_STORTECHFILLCOST)[s, h, x]
            == getattr(m, VAR_STORTECHENERGY)[s, h, x, t_hor_0] * price
        )

    setattr(
        model,
        CON_STORTECHFILLCOST,
        Constraint(getattr(model, SET_STORTECHTUPLE), rule=__rule_fill_cost),
    )
