"""Energy system model"""

from datetime import datetime

from pyomo.core import (
    Constraint,
    Model,
    NonNegativeReals,
    Objective,
    Reals,
    Var,
    minimize,
)
from pyomo.core.base.PyomoModel import ConcreteModel

from ehubx.core import logging
from ehubx.data.demand_data import Demands
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.time_data import TimeId
from ehubx.data.unit import (
    CurrencyUnit,
    FreightUnit,
    LengthUnit,
    MassUnit,
    PassengerUnit,
    PowerUnit,
    TimeUnit,
)
from ehubx.model import (
    ates_tech_model,
    autonomy_model,
    conv_tech_model,
    demand_model,
    ebm_tech_model,
    ec_model,
    export_model,
    hp_tech_model,
    hub_model,
    import_model,
    load_shedding_model,
    load_shifting_model,
    network_model,
    self_sufficiency_model,
    solar_tech_model,
    stage_model,
    stor_tech_model,
    tech_model,
    times_model,
)


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/system"
"""String identifying the energy system model for logging purposes"""

VAR_SYSTEMCOSTCO2PENALTYPERSTAGE: str = "V_SystemCostCo2PenaltyPerStage"
"""Name of variable for the system-wide CO2 penalty costs of one stage s,
i.e.; co2_price[s] times V_SystemCo2[s]. Building block of
V_SystemCostCo2Penalty and of V_SystemCostPerStage"""

VAR_SYSTEMCOSTCO2PENALTY: str = "V_SystemCostCo2Penalty"
"""Name of variable for the system-wide CO2 penalty costs, i.e.;
V_SystemCostCo2PenaltyPerStage summed over all stages s (unweighted)"""

VAR_SYSTEMCOSTPERSTAGE: str = "V_SystemCostPerStage"
"""Name of variable for the system-wide costs of one stage s, i.e.; the
per-stage costs of all submodules plus the CO2 penalty of that stage. These
are actual (unweighted) costs, unlike V_SystemCost"""

VAR_SYSTEMCOST: str = "V_SystemCost"
"""Name of variable for the system-wide costs that are optimized, i.e.; the
average of V_SystemCostPerStage weighted by the parameter stage_weight from
stages.yaml. With the default stage weights, this is the plain average over
the stages"""

VAR_SYSTEMCO2: str = "V_SystemCo2"
"""Name of variable for system-wide CO2 emissions (per stage)"""

VAR_SYSTEMCO2TOTAL: str = "V_SystemCo2Total"
"""Name of variable for system-wide total CO2 emissions (summed over stages)"""

VAR_SYSTEMSELFSUFFICIENCY: str = "V_SystemSelfSufficiency"
"""Name of variable for system-wide self-sufficiency"""

VAR_SYSTEMAUTONOMY: str = "V_SystemAutonomy"
"""Name of variable for system-wide autonomy"""
CON_SYSTEMCO2PENALTYPERSTAGE: str = "C_SystemCostCo2PenaltyPerStage"
"""Name of constraint fixing the system-wide CO2 penalty variable per stage"""

CON_SYSTEMCO2PENALTY: str = "C_SystemCostCo2Penalty"
"""Name of constraint fixing the system-wide CO2 penalty variable"""

CON_SYSTEMCOSTPERSTAGE: str = "C_SystemCostPerStage"
"""Name of constraint fixing the system costs per stage"""

CON_SYSTEMCOSTTOTAL: str = "C_SystemCostTotal"
"""Name of constraint fixing the total system costs"""

CON_SYSTEMCO2: str = "C_SystemCo2"
"""Name of constraint fixing the system CO2 emissions (per stage)"""

CON_SYSTEMCO2TOTAL: str = "C_SystemCo2Total"
"""Name of constraint fixing the total system CO2 emissions (summed over
stages)"""

CON_SYSTEMCO2MIN: str = "C_SystemCo2Min"
"""Name of constraint respecting the parameter co2_min"""

CON_SYSTEMCO2MAX: str = "C_SystemCo2Max"
"""Name of constraint respecting the parameter co2_max"""

CON_SYSTEMSELFSUFFICIENCY: str = "C_SystemSelfSufficiencyTotal"
"""Name of constraint fixing the total system self-sufficiency"""

CON_SYSTEMAUTONOMY: str = "C_SystemAutonomyTotal"
"""Name of constraint fixing the total system autonomy"""

CON_SYSTEMDEMANDSUPPLYPROFILE: str = "C_SystemDemandSupplyProfile"
"""Name of constraint fixing the system-wide demand supply for demand profiles"""

CON_SYSTEMENERGYBALANCE: str = "C_SystemEnergyBalance"
"""Name of constraint with the system-wide total energy balance"""

OBJ_SYSTEMCOST: str = "O_SystemCost"
"""Name of objective for system costs"""

OBJ_SYSTEMCO2: str = "O_SystemCo2"
"""Name of objective for system CO2 emissions"""

OBJ_SYSTEMSELFSUFFICIENCY: str = "O_SystemSelfSufficiency"
"""Name of objective for system self-sufficiency"""

OBJ_SYSTEMAUTONOMY: str = "O_SystemAutonomy"
"""Name of objective for system autonomy"""


def build(energy_system: EnergySystem) -> Model:
    """
    Builds all of the energy system's submodules alongside the overarching
    energy system model components itself. For a mathematical description in
    thorough detail, please refer to the section 'Energy system model' in the
    documentation.

    :param energy_system: Energy system data object
    :type energy_system: EnergySystem
    :return: Pyomo model
    :rtype: Model
    """
    start_time = datetime.now()
    logging.log("Starting to build energy system model", module=LOG_MODULE_STR)
    model = ConcreteModel()
    _build_modules(model, energy_system)
    _build_self(model, energy_system)
    elpsed = datetime.now() - start_time
    logging.log(
        (
            "Finished building energy system model. Elapsed time: "
            f"{int(elpsed.total_seconds())}s"
        ),
        module=LOG_MODULE_STR,
    )
    return model


def _build_modules(model: Model, energy_system: EnergySystem) -> None:
    stage_model.build(model, energy_system)
    hub_model.build(model, energy_system)
    ec_model.build(model, energy_system)
    times_model.build(model, energy_system)
    import_model.build(model, energy_system)
    export_model.build(model, energy_system)
    demand_model.build(model, energy_system)
    load_shedding_model.build(model, energy_system)
    load_shifting_model.build(model, energy_system)
    network_model.build(model, energy_system)
    tech_model.build(model, energy_system)
    stor_tech_model.build(model, energy_system)
    ebm_tech_model.build(model, energy_system)
    conv_tech_model.build(model, energy_system)
    solar_tech_model.build(model, energy_system)
    hp_tech_model.build(model, energy_system)
    ates_tech_model.build(model, energy_system)
    self_sufficiency_model.build(model, energy_system)
    autonomy_model.build(model, energy_system)


def _build_self(model: Model, energy_system: EnergySystem) -> None:
    _build_self_co2(model, energy_system.stages, energy_system.mass_unit)
    _build_self_cost(
        model,
        energy_system.stages,
        energy_system.currency_unit,
        energy_system.mass_unit,
    )
    _build_self_self_sufficiency(model)
    _build_self_autonomy(model)
    _build_self_demand_supply_profile(
        model,
        energy_system.ecs,
        energy_system.demands,
        energy_system.mass_unit,
        energy_system.power_unit,
        energy_system.length_unit,
        energy_system.passenger_unit,
        energy_system.freight_unit,
    )
    # [CON] Energy balance
    _con_energy_balance(model)


def _build_self_cost(
    model: Model, stages: Stages, currency_unit: CurrencyUnit, mass_unit: MassUnit
) -> None:
    # [VAR] System CO2 penalty cost per stage
    setattr(
        model,
        VAR_SYSTEMCOSTCO2PENALTYPERSTAGE,
        Var(getattr(model, stage_model.SET_STAGE), domain=Reals),
    )
    # [CON] System CO2 penalty cost per stage
    _con_system_cost_co2_penalty_per_stage(model, stages, currency_unit, mass_unit)
    # [VAR] System CO2 penalty cost
    setattr(model, VAR_SYSTEMCOSTCO2PENALTY, Var(domain=Reals))
    # [CON] System CO2 penalty cost
    _con_system_cost_co2_penalty(model)
    # [VAR] System cost per stage
    setattr(
        model,
        VAR_SYSTEMCOSTPERSTAGE,
        Var(getattr(model, stage_model.SET_STAGE), domain=Reals),
    )
    # [CON] System cost per stage
    _con_system_cost_per_stage(model)
    # [VAR] System cost
    setattr(model, VAR_SYSTEMCOST, Var(domain=Reals))
    # [CON] System cost
    _con_system_cost(model, stages)
    # [OBJ] System cost
    _obj_system_cost(model)


def _build_self_co2(model: Model, stages: Stages, mass_unit: MassUnit) -> None:
    # [VAR] System CO2 emissions
    setattr(
        model, VAR_SYSTEMCO2, Var(getattr(model, stage_model.SET_STAGE), domain=Reals)
    )
    # [CON] System CO2 emissions
    _con_system_co2(model)
    # [CON] Enforce minimal and maximal CO2 emissions
    _con_system_co2_minmax(model, stages, mass_unit)
    # [VAR] Total system CO2 emissions (stages summed-up)
    setattr(model, VAR_SYSTEMCO2TOTAL, Var(domain=Reals))
    # [CON] Total system CO2 emissions (stages summed-up)
    _con_system_co2_total(model)
    # [OBJ] System CO2 emissions
    _obj_system_co2(model)


def _build_self_self_sufficiency(model: Model) -> None:
    # Skip this without presence of self-sufficiency submodule
    if self_sufficiency_model.VAR_SELFSUFFICIENCY not in model.component_map(Var):
        return
    # [VAR] System self-sufficiency
    setattr(model, VAR_SYSTEMSELFSUFFICIENCY, Var(domain=NonNegativeReals))
    # [CON] System self-sufficiency
    _con_system_self_sufficiency(model)
    # [OBJ] System self-sufficiency
    _obj_system_self_sufficiency(model)


def _build_self_autonomy(model: Model) -> None:
    # Skip this without presence of autonomy submodule
    if autonomy_model.VAR_AUTONOMY not in model.component_map(Var):
        return
    # [VAR] System autonomy
    setattr(model, VAR_SYSTEMAUTONOMY, Var(domain=NonNegativeReals))
    # [CON] System autonomy
    _con_system_autonomy(model)
    # [OBJ] System autonomy
    _obj_system_autonomy(model)


def _build_self_demand_supply_profile(
    model: Model,
    ecs: Ecs,
    demands: Demands,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
    length_unit: LengthUnit,
    passenger_unit: PassengerUnit,
    freight_unit: FreightUnit,
) -> None:
    # [CON] Define demand supply for tuples with demand-profiles by respecting
    #       load shedding and load shifting
    _con_demand_supply_profile(
        model,
        ecs,
        demands,
        mass_unit,
        power_unit,
        length_unit,
        passenger_unit,
        freight_unit,
    )


def _con_system_cost_co2_penalty_per_stage(
    model: Model, stages: Stages, currency_unit: CurrencyUnit, mass_unit: MassUnit
) -> None:
    def __rule_system_cost_co2_penalty_per_stage(model, s):
        # Calculate the CO2 penalty value of this stage
        system_cost_co2_penalty_per_stage = (
            stages.get_co2_price(StageId(s)).to_float(unit=currency_unit / mass_unit)
            * getattr(model, VAR_SYSTEMCO2)[s]
        )
        # Set the constraint
        return (
            getattr(model, VAR_SYSTEMCOSTCO2PENALTYPERSTAGE)[s]
            == system_cost_co2_penalty_per_stage
        )

    setattr(
        model,
        CON_SYSTEMCO2PENALTYPERSTAGE,
        Constraint(
            getattr(model, stage_model.SET_STAGE),
            rule=__rule_system_cost_co2_penalty_per_stage,
        ),
    )


def _con_system_cost_co2_penalty(model: Model) -> None:
    def __rule_system_cost_co2_penalty(model):
        # Calculate the CO2 penalty value by summing up the stages
        system_cost_co2_penalty = sum(
            getattr(model, VAR_SYSTEMCOSTCO2PENALTYPERSTAGE)[s]
            for s in getattr(model, stage_model.SET_STAGE)
        )
        # Set the constraint
        return getattr(model, VAR_SYSTEMCOSTCO2PENALTY) == system_cost_co2_penalty

    setattr(
        model, CON_SYSTEMCO2PENALTY, Constraint(rule=__rule_system_cost_co2_penalty)
    )


def _con_system_cost_per_stage(model: Model) -> None:
    def __rule_system_cost_per_stage(model, s):
        system_cost_per_stage = 0
        # Tech cost (CAPEX and OPEX from installation)
        system_cost_per_stage += getattr(model, tech_model.VAR_TECHCOSTPERSTAGE)[s]
        # Conversion tech cost (OPEX from energy output)
        system_cost_per_stage += getattr(
            model, conv_tech_model.VAR_CONVTECHCOSTPERSTAGE
        )[s]
        # Storage tech cost (OPEX from storage outflow)
        system_cost_per_stage += getattr(
            model, stor_tech_model.VAR_STORTECHCOSTPERSTAGE
        )[s]
        # Import cost
        system_cost_per_stage += getattr(model, import_model.VAR_IMPCOSTPERSTAGE)[s]
        # Export profit
        system_cost_per_stage -= getattr(model, export_model.VAR_EXPPROFITPERSTAGE)[s]
        # Load shedding cost
        system_cost_per_stage += getattr(
            model, load_shedding_model.VAR_LOADSHEDDINGCOSTPERSTAGE
        )[s]
        # Load shifting cost
        system_cost_per_stage += getattr(
            model, load_shifting_model.VAR_LOADSHIFTINGCOSTPERSTAGE
        )[s]
        # Network tech cost (investment, CAPEX, OPEX from installation and
        #                    OPEX from transmission)
        system_cost_per_stage += getattr(
            model, network_model.VAR_NETTECHCOSTPERSTAGE
        )[s]
        # CO2 penalty cost
        system_cost_per_stage += getattr(model, VAR_SYSTEMCOSTCO2PENALTYPERSTAGE)[s]
        # Set system cost of this stage
        return getattr(model, VAR_SYSTEMCOSTPERSTAGE)[s] == system_cost_per_stage

    setattr(
        model,
        CON_SYSTEMCOSTPERSTAGE,
        Constraint(
            getattr(model, stage_model.SET_STAGE), rule=__rule_system_cost_per_stage
        ),
    )


def _con_system_cost(model: Model, stages: Stages) -> None:
    def __rule_system_cost_total_var(model):
        # Weight of each stage in the objective function
        stage_weights = {
            s: stages.get_stage_weight(StageId(s))
            for s in getattr(model, stage_model.SET_STAGE)
        }
        # The stage data validation guarantees that this sum is positive
        stage_weight_sum = sum(stage_weights.values())
        # Weighted sum of the stages' system costs
        system_cost_weighted = sum(
            stage_weights[s] * getattr(model, VAR_SYSTEMCOSTPERSTAGE)[s]
            for s in getattr(model, stage_model.SET_STAGE)
        )
        ## Autonomy-module costs are not yet decomposed per stage (added on github main
        ## after the resilience_extension had branched out. They enter unweighted.
        # Unmet demand penalty cost
        system_cost_weighted += getattr(model, demand_model.VAR_DEMANDUNMETCOSTTOTAL)
        # Storage fill cost (pre filled energy in non-cyclic storage)
        system_cost_weighted += getattr(model, stor_tech_model.VAR_STORTECHFILLCOSTTOTAL)

        # Set system cost as the weighted average over the stages. Dividing by
        # the sum of the stage weights keeps the system cost an annual cost,
        # independent of the number of stages and of the scale of the weights
        return stage_weight_sum * getattr(model, VAR_SYSTEMCOST) == system_cost_weighted

    setattr(model, CON_SYSTEMCOSTTOTAL, Constraint(rule=__rule_system_cost_total_var))


def _obj_system_cost(model: Model):
    def __rule_system_cost_obj(model):
        return getattr(model, VAR_SYSTEMCOST)

    setattr(
        model, OBJ_SYSTEMCOST, Objective(rule=__rule_system_cost_obj, sense=minimize)
    )
    getattr(model, OBJ_SYSTEMCOST).deactivate()


def _con_system_co2(model: Model) -> None:
    def __rule_system_co2_var(model, s):
        # Tech installation CO2
        system_co2 = getattr(model, tech_model.VAR_TECHCO2TOTAL)[s]
        # Import CO2
        system_co2 += getattr(model, import_model.VAR_IMPCO2TOTAL)[s]
        # Export CO2
        system_co2 -= getattr(model, export_model.VAR_EXPCO2TOTAL)[s]
        # Network tech CO2 (tech installation & transmission)
        system_co2 += getattr(model, network_model.VAR_NETTECHCO2TOTAL)[s]
        # Operational conv tech CO2
        system_co2 += getattr(model, conv_tech_model.VAR_CONVTECHCO2OPERTOTAL)[s]
        # Set system CO2
        return getattr(model, VAR_SYSTEMCO2)[s] == system_co2

    setattr(
        model,
        CON_SYSTEMCO2,
        Constraint(getattr(model, stage_model.SET_STAGE), rule=__rule_system_co2_var),
    )


def _con_system_co2_total(model: Model) -> None:
    def __rule_system_co2_total(model):
        # Calculate total system CO2 across all stages
        system_co2_total = sum(
            getattr(model, VAR_SYSTEMCO2)[s]
            for s in getattr(model, stage_model.SET_STAGE)
        )
        # Set the constraint
        return getattr(model, VAR_SYSTEMCO2TOTAL) == system_co2_total

    setattr(model, CON_SYSTEMCO2TOTAL, Constraint(rule=__rule_system_co2_total))


def _obj_system_co2(model: Model):
    def __rule_system_co2_obj(model):
        return getattr(model, VAR_SYSTEMCO2TOTAL)

    setattr(model, OBJ_SYSTEMCO2, Objective(rule=__rule_system_co2_obj, sense=minimize))
    getattr(model, OBJ_SYSTEMCO2).deactivate()


def _con_system_co2_minmax(model: Model, stages: Stages, mass_unit: MassUnit) -> None:
    def __rule_system_co2_min(model, s):
        co2_min = stages.get_co2_min(StageId(s)).to_float(unit=mass_unit)
        if co2_min == -float("inf"):
            return Constraint.Skip
        return getattr(model, VAR_SYSTEMCO2)[s] >= co2_min

    def __rule_system_co2_max(model, s):
        co2_max = stages.get_co2_max(StageId(s)).to_float(unit=mass_unit)
        if co2_max == float("inf"):
            return Constraint.Skip
        return getattr(model, VAR_SYSTEMCO2)[s] <= co2_max

    setattr(
        model,
        CON_SYSTEMCO2MIN,
        Constraint(getattr(model, stage_model.SET_STAGE), rule=__rule_system_co2_min),
    )
    setattr(
        model,
        CON_SYSTEMCO2MAX,
        Constraint(getattr(model, stage_model.SET_STAGE), rule=__rule_system_co2_max),
    )


def _con_system_self_sufficiency(model: Model) -> None:
    def __rule_system_self_sufficiency(model):
        return getattr(model, VAR_SYSTEMSELFSUFFICIENCY) == getattr(
            model, self_sufficiency_model.VAR_SELFSUFFICIENCY
        )

    setattr(
        model,
        CON_SYSTEMSELFSUFFICIENCY,
        Constraint(rule=__rule_system_self_sufficiency),
    )


def _con_system_autonomy(model: Model) -> None:
    def __rule_system_autonomy(model):
        return getattr(model, VAR_SYSTEMAUTONOMY) == sum(
            getattr(model, autonomy_model.VAR_AUTONOMY)[s]
            for s in getattr(model, stage_model.SET_STAGE)
        )

    setattr(
        model,
        CON_SYSTEMAUTONOMY,
        Constraint(rule=__rule_system_autonomy),
    )


def _obj_system_self_sufficiency(model: Model):
    def __rule_system_self_sufficiency_obj(model):
        if self_sufficiency_model.VAR_SELFSUFFICIENCY in model.component_map(Var):
            return -getattr(model, self_sufficiency_model.VAR_SELFSUFFICIENCY)
        return 0.0

    setattr(
        model,
        OBJ_SYSTEMSELFSUFFICIENCY,
        Objective(rule=__rule_system_self_sufficiency_obj),
    )
    getattr(model, OBJ_SYSTEMSELFSUFFICIENCY).deactivate()


def _obj_system_autonomy(model: Model):
    def __rule_system_autonomy_obj(model):
        if VAR_SYSTEMAUTONOMY in model.component_map(Var):
            return -getattr(model, VAR_SYSTEMAUTONOMY)
        return 0.0

    setattr(
        model,
        OBJ_SYSTEMAUTONOMY,
        Objective(rule=__rule_system_autonomy_obj),
    )
    getattr(model, OBJ_SYSTEMAUTONOMY).deactivate()


def _con_demand_supply_profile(
    model: Model,
    ecs: Ecs,
    demands: Demands,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
    length_unit: LengthUnit,
    passenger_unit: PassengerUnit,
    freight_unit: FreightUnit,
) -> None:
    def __rule_demand_supply_profile(model, s, h, e, t):
        unit = (
            ec_model.get_ec_model_unit(
                ecs.get_unit(EcId(e)),
                mass_unit,
                power_unit,
                length_unit,
                passenger_unit,
                freight_unit,
            )
            / TimeUnit.H
        )
        demand_supply = (
            demands.get_demand_profile(StageId(s), HubId(h), EcId(e))
            .get_value(TimeId(t))
            .to_float(unit=unit)
        )
        if (s, h, e) in getattr(model, load_shedding_model.SET_LOADSHEDDINGTUPLE):
            demand_supply -= getattr(model, load_shedding_model.VAR_LOADSHEDDING)[
                s, h, e, t
            ]
        if (s, h, e) in getattr(model, load_shifting_model.SET_LOADSHIFTINGTUPLES):
            demand_supply += getattr(model, load_shifting_model.VAR_LOADSHIFTINGTOTAL)[
                s, h, e, t
            ]
        return (
            getattr(model, demand_model.VAR_DEMANDSUPPLY)[s, h, e, t]
            + getattr(model, demand_model.VAR_DEMANDUNMET)[s, h, e, t]
            == demand_supply
        )

    setattr(
        model,
        CON_SYSTEMDEMANDSUPPLYPROFILE,
        Constraint(
            getattr(model, demand_model.SET_DEMANDPROFILETUPLE),
            getattr(model, times_model.SET_TIME),
            rule=__rule_demand_supply_profile,
        ),
    )


def _con_energy_balance(model: Model) -> None:
    def __rule_energy_balance(model, s, h, e, t):
        energy_rest = 0
        # Storage tech outflow
        energy_rest += sum(
            getattr(model, stor_tech_model.VAR_STORTECHOUTFLOW)[s, h, x, t]
            for (s_, h_, x) in getattr(model, stor_tech_model.SET_STORTECHTUPLE)
            if s_ == s
            if h_ == h
            if e == getattr(model, stor_tech_model.PAR_STORTECHEC)[x]
        )
        # Storage tech inflow
        energy_rest -= sum(
            getattr(model, stor_tech_model.VAR_STORTECHINFLOW)[s, h, x, t]
            for (s_, h_, x) in getattr(model, stor_tech_model.SET_STORTECHTUPLE)
            if s_ == s
            if h == h_
            if e == getattr(model, stor_tech_model.PAR_STORTECHEC)[x]
        )
        # EBM tech outflow
        energy_rest += sum(
            getattr(model, ebm_tech_model.VAR_EBMTECHOUTFLOW)[s, h, x, t]
            for (s_, h_, x) in getattr(model, ebm_tech_model.SET_EBMTECHTUPLE)
            if s_ == s
            if h_ == h
            if e == getattr(model, ebm_tech_model.PAR_EBMTECHEC)[x]
        )
        # EBM tech inflow
        energy_rest -= sum(
            getattr(model, ebm_tech_model.VAR_EBMTECHINFLOW)[s, h, x, t]
            for (s_, h_, x) in getattr(model, ebm_tech_model.SET_EBMTECHTUPLE)
            if s_ == s
            if h_ == h
            if e == getattr(model, ebm_tech_model.PAR_EBMTECHEC)[x]
        )
        # Conversion tech output
        energy_rest += sum(
            getattr(model, conv_tech_model.VAR_CONVTECHOUT)[s, h, x, e, t]
            for (s_, h_, x, e_) in getattr(model, conv_tech_model.SET_CONVTECHOUT)
            if s_ == s
            if h == h_
            if e == e_
        )
        # Conversion tech input
        energy_rest -= sum(
            getattr(model, conv_tech_model.VAR_CONVTECHIN)[s, h, x, e, t]
            for (s_, h_, x, e_) in getattr(model, conv_tech_model.SET_CONVTECHIN)
            if s == s_
            if h == h_
            if e == e_
        )
        # Heat pump tech output
        energy_rest += sum(
            getattr(model, hp_tech_model.VAR_HPTECHOUT)[s, h, x, e, t]
            for (s_, h_, x, e_) in getattr(model, hp_tech_model.SET_HPTECHOUT)
            if s_ == s
            if h == h_
            if e == e_
        )
        # Heat pump tech input
        energy_rest -= sum(
            getattr(model, hp_tech_model.VAR_HPTECHIN)[s, h, x, e, t]
            for (s_, h_, x, e_) in getattr(model, hp_tech_model.SET_HPTECHIN)
            if s_ == s
            if h == h_
            if e == e_
        )
        # ATES tech output
        energy_rest += sum(
            getattr(model, ates_tech_model.VAR_ATESTECHOUT)[s, h, x, e, t]
            for (s_, h_, x, e_) in getattr(model, ates_tech_model.SET_ATESTECHOUT)
            if s_ == s
            if h == h_
            if e == e_
        )
        # ATES tech input
        energy_rest -= sum(
            getattr(model, ates_tech_model.VAR_ATESTECHIN)[s, h, x, e, t]
            for (s_, h_, x, e_) in getattr(model, ates_tech_model.SET_ATESTECHIN)
            if s_ == s
            if h == h_
            if e == e_
        )
        # Demand supply
        if (s, h, e) in getattr(model, demand_model.SET_DEMANDTUPLE):
            energy_rest -= getattr(model, demand_model.VAR_DEMANDSUPPLY)[s, h, e, t]
        # Import
        if (s, h, e) in getattr(model, import_model.SET_IMPTUPLE):
            energy_rest += getattr(model, import_model.VAR_IMP)[s, h, e, t]
        # Export
        if (s, h, e) in getattr(model, export_model.SET_EXPTUPLE):
            energy_rest -= getattr(model, export_model.VAR_EXP)[s, h, e, t]
        # Network output
        if (h, e) in getattr(model, network_model.SET_NETHUBOUT):
            energy_rest += getattr(model, network_model.VAR_NETHUBOUT)[s, h, e, t]
        # Network input
        if (h, e) in getattr(model, network_model.SET_NETHUBIN):
            energy_rest -= getattr(model, network_model.VAR_NETHUBIN)[s, h, e, t]
        # If no variables modify the energy balance, skip the constraint
        if isinstance(energy_rest, int):
            return Constraint.Skip
        return energy_rest == 0

    setattr(
        model,
        CON_SYSTEMENERGYBALANCE,
        Constraint(
            getattr(model, stage_model.SET_STAGE),
            getattr(model, hub_model.SET_HUB),
            getattr(model, ec_model.SET_EC),
            getattr(model, times_model.SET_TIME),
            rule=__rule_energy_balance,
        ),
    )


def configure_energy_system_features(model: Model, enabled: bool) -> None:
    autonomy_model.configure_autonomy(model, enabled)
