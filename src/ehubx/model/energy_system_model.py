"""Energy system model"""
from datetime import datetime
from pyomo.core import Constraint, minimize, Model, NonNegativeReals, \
    Objective, Reals, Var
from pyomo.core.base.PyomoModel import ConcreteModel
from ehubx.core import logging
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.stage_data import Stages, StageId
from ehubx.data.hub_data import HubId
from ehubx.data.ec_data import EcId
from ehubx.data.time_data import TimeId
from ehubx.data.demand_data import Demands
from ehubx.model import stage_model
from ehubx.model import hub_model
from ehubx.model import tech_model
from ehubx.model import stor_tech_model
from ehubx.model import ebm_tech_model
from ehubx.model import conv_tech_model
from ehubx.model import solar_tech_model
from ehubx.model import wind_tech_model
from ehubx.model import hp_tech_model
from ehubx.model import ates_tech_model
from ehubx.model import ec_model
from ehubx.model import import_model
from ehubx.model import export_model
from ehubx.model import demand_model
from ehubx.model import load_shedding_model
from ehubx.model import load_shifting_model
from ehubx.model import autarky_model
from ehubx.model import network_model
from ehubx.model import times_model

# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/system"
"""String identifying the energy system model for logging purposes"""

VAR_SYSTEMCOSTCO2PENALTY: str = "V_SystemCostCo2Penalty"
"""Name of variable for system-wide CO2 penalty costs"""

VAR_SYSTEMCOST: str = "V_SystemCost"
"""Name of variable for system-wide costs"""

VAR_SYSTEMCO2: str = "V_SystemCo2"
"""Name of variable for system-wide CO2 emissions (per stage)"""

VAR_SYSTEMCO2TOTAL: str = "V_SystemCo2Total"
"""Name of variable for system-wide total CO2 emissions (summed over stages)"""

VAR_SYSTEMAUTARKY: str = "V_SystemAutarky"
"""Name of variable for system-wide autarky"""

VAR_DEMANDSUPPLY: str = "V_DemandSupply"
"""Name of variable for demand supply"""

CON_SYSTEMCO2PENALTY: str = "C_SystemCostCo2Penalty"
"""Name of constraint fixing the system-wide CO2 penalty variable"""

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

CON_SYSTEMAUTARKY: str = "C_SystemAutarkyTotal"
"""Name of constraint fixing the total system autarky"""

CON_SYSTEMDEMANDSUPPLY: str = "C_SystemDemandSupply"
"""Name of constraint fixing the system-wide demand supply"""

CON_SYSTEMENERGYBALANCE: str = "C_SystemEnergyBalance"
"""Name of constraint with the system-wide total energy balance"""

OBJ_SYSTEMCOST: str = "O_SystemCost"
"""Name of objective for system costs"""

OBJ_SYSTEMCO2: str = "O_SystemCo2"
"""Name of objective for system CO2 emissions"""

OBJ_SYSTEMAUTARKY: str = "O_SystemAutarky"
"""Name of objective for system autarky"""


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
    logging.log(("Finished building energy system model. Elapsed time: "
                 f"{int(elpsed.total_seconds())}s"), module=LOG_MODULE_STR)
    return model


def _build_modules(model: Model, energy_system: EnergySystem) -> None:
    stage_model.build(model, energy_system.stages)
    hub_model.build(model, energy_system.hubs)
    ec_model.build(model, energy_system.ecs)
    times_model.build(model, energy_system.times)
    import_model.build(model, energy_system.imports, energy_system.times)
    export_model.build(model, energy_system.exports, energy_system.times)
    demand_model.build(model, energy_system.stages, energy_system.demands,
                       energy_system.times)
    load_shedding_model.build(model, energy_system.stages, energy_system.hubs,
                              energy_system.ecs, energy_system.demands,
                              energy_system.load_shedding, energy_system.times)
    load_shifting_model.build(model, energy_system.demands,
                              energy_system.load_shifting, energy_system.times)
    network_model.build(model, energy_system.stages, energy_system.hubs,
                        energy_system.net_links, energy_system.net_techs,
                        energy_system.times)
    tech_model.build(model, energy_system.stages, energy_system.techs)
    stor_tech_model.build(model, energy_system.stages, energy_system.techs,
                          energy_system.stor_techs, energy_system.times)
    ebm_tech_model.build(model, energy_system.stages, energy_system.ebm_techs,
                         energy_system.times)
    conv_tech_model.build(model, energy_system.techs,
                          energy_system.conv_techs, energy_system.times)
    solar_tech_model.build(model, energy_system.conv_techs,
                           energy_system.solar_techs, energy_system.solar_data)
    wind_tech_model.build(model, energy_system.conv_techs,
                          energy_system.wind_techs, energy_system.wind_data)
    hp_tech_model.build(model, energy_system.techs, energy_system.hp_techs,
                        energy_system.times)
    ates_tech_model.build(model, energy_system.times)
    autarky_model.build(model, energy_system.conv_techs, energy_system.ecs,
                        energy_system.imports, energy_system.autarky,
                        energy_system.times)


def _build_self(model: Model, energy_system: EnergySystem) -> None:
    _build_self_co2(model, energy_system.stages)
    _build_self_cost(model, energy_system.stages)
    _build_self_autarky(model)
    _build_self_demand_supply(model, energy_system.demands)
    # [CON] Energy balance
    _con_energy_balance(model)


def _build_self_cost(model: Model, stages: Stages) -> None:
    # [VAR] System CO2 penalty cost
    setattr(model, VAR_SYSTEMCOSTCO2PENALTY, Var(domain=Reals))
    # [CON] System CO2 penalty cost
    _con_system_cost_co2_penalty(model, stages)
    # [VAR] System cost
    setattr(model, VAR_SYSTEMCOST, Var(domain=Reals))
    # [CON] System cost
    _con_system_cost(model)
    # [OBJ] System cost
    _obj_system_cost(model)


def _build_self_co2(model: Model, stages: Stages) -> None:
    # [VAR] System CO2 emissions
    setattr(model, VAR_SYSTEMCO2,
            Var(getattr(model, stage_model.SET_STAGE), domain=Reals))
    # [CON] System CO2 emissions
    _con_system_co2(model)
    # [CON] Enforce minimal and maximal CO2 emissions
    _con_system_co2_minmax(model, stages)
    # [VAR] Total system CO2 emissions (stages summed-up)
    setattr(model, VAR_SYSTEMCO2TOTAL, Var(domain=Reals))
    # [CON] Total system CO2 emissions (stages summed-up)
    _con_system_co2_total(model)
    # [OBJ] System CO2 emissions
    _obj_system_co2(model)


def _build_self_autarky(model: Model) -> None:
    # Skip this without presence of autarky submodule
    if autarky_model.VAR_AUTARKY not in model.component_map(Var):
        return
    # [VAR] System autarky
    setattr(model, VAR_SYSTEMAUTARKY, Var(domain=NonNegativeReals))
    # [CON] System autarky
    _con_system_autarky(model)
    # [OBJ] System autarky
    _obj_system_autarky(model)


def _build_self_demand_supply(model: Model, demands: Demands) -> None:
    # [VAR] Supply to demand-side
    setattr(model, VAR_DEMANDSUPPLY,
            Var(getattr(model, demand_model.SET_DEMANDTUPLE),
                getattr(model, times_model.SET_TIME),
                within=NonNegativeReals))
    # [CON] Define demand supply by respecting load shedding and load shifting
    _con_demand_supply(model, demands)


def _con_system_cost_co2_penalty(model: Model, stages: Stages) -> None:

    def __rule_system_cost_co2_penalty(model):
        # Calculate the CO2 penalty value
        system_cost_co2_penalty = sum(
            (stages.get_co2_price(StageId(s))
             * getattr(model, VAR_SYSTEMCO2)[s])
            for s in getattr(model, stage_model.SET_STAGE))
        # Set the constraint
        return (getattr(model, VAR_SYSTEMCOSTCO2PENALTY)
                == system_cost_co2_penalty)

    setattr(model, CON_SYSTEMCO2PENALTY,
            Constraint(rule=__rule_system_cost_co2_penalty))


def _con_system_cost(model: Model) -> None:

    def __rule_system_cost_total_var(model):
        system_cost_total = 0
        # Tech cost (CAPEX and OPEX from installation)
        system_cost_total += getattr(model, tech_model.VAR_TECHCOSTTOTAL)
        # Conversion tech cost (OPEX from energy output)
        system_cost_total += getattr(model,
                                     conv_tech_model.VAR_CONVTECHCOSTTOTAL)
        # Import cost
        system_cost_total += getattr(model, import_model.VAR_IMPCOSTTOTAL)
        # Export profit
        system_cost_total -= getattr(model, export_model.VAR_EXPPROFITTOTAL)
        # Load shedding cost
        system_cost_total += getattr(model,
            load_shedding_model.VAR_LOADHSHEDDINGCOSTTOTAL)
        # Load shifting cost
        system_cost_total += getattr(model,
            load_shifting_model.VAR_LOADHSHIFTINGCOSTTOTAL)
        # Network tech cost (investment, CAPEX, OPEX from installation and
        #                    OPEX from transmission)
        system_cost_total += getattr(model, network_model.VAR_NETTECHCOSTTOTAL)
        # CO2 penalty cost
        system_cost_total += getattr(model, VAR_SYSTEMCOSTCO2PENALTY)
        # Set system cost
        return getattr(model, VAR_SYSTEMCOST) == system_cost_total

    setattr(model, CON_SYSTEMCOSTTOTAL,
            Constraint(rule=__rule_system_cost_total_var))


def _obj_system_cost(model: Model):

    def __rule_system_cost_obj(model):
        return getattr(model, VAR_SYSTEMCOST)

    setattr(model, OBJ_SYSTEMCOST,
            Objective(rule=__rule_system_cost_obj, sense=minimize))
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
        # Set system CO2
        return getattr(model, VAR_SYSTEMCO2)[s] == system_co2

    setattr(model, CON_SYSTEMCO2,
            Constraint(getattr(model, stage_model.SET_STAGE),
                       rule=__rule_system_co2_var))


def _con_system_co2_total(model: Model) -> None:

    def __rule_system_co2_total(model):
        # Calculate total system CO2 across all stages
        system_co2_total = sum(getattr(model, VAR_SYSTEMCO2)[s]
                               for s in getattr(model, stage_model.SET_STAGE))
        # Set the constraint
        return getattr(model, VAR_SYSTEMCO2TOTAL) == system_co2_total

    setattr(model, CON_SYSTEMCO2TOTAL,
            Constraint(rule=__rule_system_co2_total))


def _obj_system_co2(model: Model):

    def __rule_system_co2_obj(model):
        return getattr(model, VAR_SYSTEMCO2TOTAL)

    setattr(model, OBJ_SYSTEMCO2,
            Objective(rule=__rule_system_co2_obj, sense=minimize))
    getattr(model, OBJ_SYSTEMCO2).deactivate()


def _con_system_co2_minmax(model: Model, stages: Stages) -> None:

    def __rule_system_co2_min(model, s):
        co2_min = stages.get_co2_min(StageId(s))
        return getattr(model, VAR_SYSTEMCO2)[s] >= co2_min

    def __rule_system_co2_max(model, s):
        co2_max = stages.get_co2_max(StageId(s))
        return getattr(model, VAR_SYSTEMCO2)[s] <= co2_max

    setattr(model, CON_SYSTEMCO2MIN,
            Constraint(getattr(model, stage_model.SET_STAGE),
                       rule=__rule_system_co2_min))
    setattr(model, CON_SYSTEMCO2MAX,
            Constraint(getattr(model, stage_model.SET_STAGE),
                       rule=__rule_system_co2_max))


def _con_system_autarky(model: Model) -> None:

    def __rule_system_autarky(model):
        return (getattr(model, VAR_SYSTEMAUTARKY)
                == getattr(model, autarky_model.VAR_AUTARKY))

    setattr(model, CON_SYSTEMAUTARKY,
            Constraint(rule=__rule_system_autarky))


def _obj_system_autarky(model: Model):

    def __rule_system_autarky_obj(model):
        if autarky_model.VAR_AUTARKY in model.component_map(Var):
            return -getattr(model, autarky_model.VAR_AUTARKY)
        return 0.0

    setattr(model, OBJ_SYSTEMAUTARKY,
            Objective(rule=__rule_system_autarky_obj))
    getattr(model, OBJ_SYSTEMAUTARKY).deactivate()


def _con_demand_supply(model: Model, demands: Demands) -> None:

    def __rule_demand(model, s, h, e, t):
        demand_supply = demands.get_demand(StageId(s), HubId(h),
                                           EcId(e)).get_value(TimeId(t))
        if (s, h, e) in getattr(model,
                                load_shedding_model.SET_LOADSHEDDINGTUPLE):
            demand_supply -= getattr(model,
                load_shedding_model.VAR_LOADSHEDDING)[s, h, e, t]
        if (s, h, e) in getattr(model,
                                load_shifting_model.SET_LOADSHIFTINGTUPLE):
            demand_supply += getattr(model,
                load_shifting_model.VAR_LOADSHIFTING)[s, h, e, t]
        return getattr(model, VAR_DEMANDSUPPLY)[s, h, e, t] == demand_supply

    setattr(model, CON_SYSTEMDEMANDSUPPLY,
            Constraint(getattr(model, demand_model.SET_DEMANDTUPLE),
                       getattr(model, times_model.SET_TIME),
                       rule=__rule_demand))


def _con_energy_balance(model: Model) -> None:

    def __rule_energy_balance(model, s, h, e, t):
        energy_rest = 0
        # Storage tech outflow
        energy_rest += sum(
            getattr(model, stor_tech_model.VAR_STORTECHOUTFLOW)[s, h, x, t]
            for (s_, h_, x) in getattr(model,
                                       stor_tech_model.SET_STORTECHTUPLE)
            if s_ == s if h_ == h
            if e == getattr(model, stor_tech_model.PAR_STORTECHEC)[x])
        # Storage tech inflow
        energy_rest -= sum(
            getattr(model, stor_tech_model.VAR_STORTECHINFLOW)[s, h, x, t]
            for (s_, h_, x) in getattr(model,
                                       stor_tech_model.SET_STORTECHTUPLE)
            if s_ == s if h == h_
            if e == getattr(model, stor_tech_model.PAR_STORTECHEC)[x])
        # EBM tech outflow
        energy_rest += sum(
            getattr(model, ebm_tech_model.VAR_EBMTECHOUTFLOW)[s, h, x, t]
            for (s_, h_, x) in getattr(model, ebm_tech_model.SET_EBMTECHTUPLE)
            if s_ == s if h_ == h
            if e == getattr(model, ebm_tech_model.PAR_EBMTECHEC)[x])
        # EBM tech inflow
        energy_rest -= sum(
            getattr(model, ebm_tech_model.VAR_EBMTECHINFLOW)[s, h, x, t]
            for (s_, h_, x) in getattr(model, ebm_tech_model.SET_EBMTECHTUPLE)
            if s_ == s if h_ == h
            if e == getattr(model, ebm_tech_model.PAR_EBMTECHEC)[x])
        # Conversion tech output
        energy_rest += sum(
            getattr(model, conv_tech_model.VAR_CONVTECHOUT)[s, h, x, e, t]
            for (s_, h_, x, e_) in getattr(model,
                                           conv_tech_model.SET_CONVTECHOUT)
            if s_ == s if h == h_ if e == e_)
        # Conversion tech input
        energy_rest -= sum(
            getattr(model, conv_tech_model.VAR_CONVTECHIN)[s, h, x, e, t]
            for (s_, h_, x, e_) in getattr(model,
                                           conv_tech_model.SET_CONVTECHIN)
            if s == s_ if h == h_ if e == e_)
        # Heat pump tech output
        energy_rest += sum(
            getattr(model, hp_tech_model.VAR_HPTECHOUT)[s, h, x, e, t]
            for (s_, h_, x, e_) in getattr(model, hp_tech_model.SET_HPTECHOUT)
            if s_ == s if h == h_ if e == e_)
        # Heat pump tech input
        energy_rest -= sum(
            getattr(model, hp_tech_model.VAR_HPTECHIN)[s, h, x, e, t]
            for (s_, h_, x, e_) in getattr(model, hp_tech_model.SET_HPTECHIN)
            if s_ == s if h == h_ if e == e_)
        # ATES tech output
        energy_rest += sum(
            getattr(model, ates_tech_model.VAR_ATESTECHOUT)[s, h, x, e, t]
            for (s_, h_, x, e_) in getattr(model,
                                           ates_tech_model.SET_ATESTECHOUT)
            if s_ == s if h == h_ if e == e_)
        # ATES tech input
        energy_rest -= sum(
            getattr(model, ates_tech_model.VAR_ATESTECHIN)[s, h, x, e, t]
            for (s_, h_, x, e_) in getattr(model,
                                           ates_tech_model.SET_ATESTECHIN)
            if s_ == s if h == h_ if e == e_)
        # Demand supply
        if (s, h, e) in getattr(model, demand_model.SET_DEMANDTUPLE):
            energy_rest -= getattr(model, VAR_DEMANDSUPPLY)[s, h, e, t]
        # Import
        if (s, h, e) in getattr(model, import_model.SET_IMPTUPLE):
            energy_rest += getattr(model, import_model.VAR_IMP)[s, h, e, t]
        # Export
        if (s, h, e) in getattr(model, export_model.SET_EXPTUPLE):
            energy_rest -= getattr(model, export_model.VAR_EXP)[s, h, e, t]
        # Network output
        if (h, e) in getattr(model, network_model.SET_NETHUBOUT):
            energy_rest += getattr(model,
                                   network_model.VAR_NETHUBOUT)[s, h, e, t]
        # Network input
        if (h, e) in getattr(model, network_model.SET_NETHUBIN):
            energy_rest -= getattr(model,
                                   network_model.VAR_NETHUBIN)[s, h, e, t]
        # If no variables modify the energy balance, skip the constraint
        if isinstance(energy_rest, int):
            return Constraint.Skip
        return energy_rest == 0

    setattr(model, CON_SYSTEMENERGYBALANCE,
            Constraint(getattr(model, stage_model.SET_STAGE),
                       getattr(model, hub_model.SET_HUB),
                       getattr(model, ec_model.SET_EC),
                       getattr(model, times_model.SET_TIME),
                       rule=__rule_energy_balance))
