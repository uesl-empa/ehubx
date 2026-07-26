"""Conversion technology submodel"""

from datetime import datetime

from pyomo.core import Constraint, Model, NonNegativeReals, Reals, Set, Var, quicksum

from ehubx.core import common, logging
from ehubx.data.conv_tech_data import ConversionTechs
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId
from ehubx.data.tech_data import TechId
from ehubx.data.time_data import TimeId, Times
from ehubx.data.unit import CurrencyUnit, MassUnit, PowerUnit
from ehubx.model.ec_model import SET_EC, get_ec_model_unit
from ehubx.model.stage_model import SET_STAGE
from ehubx.model.tech_model import (
    SET_TECHTUPLE,
    VAR_TECHCAP,
    VAR_YTECHUSED,
)
from ehubx.model.times_model import SET_TIME


# Literals
LOG_MODULE_STR: str = "mod/conv_tech"
"""String identifying the conversion technology model for logging purposes"""

SET_CONVTECHTUPLE: str = "S_ConvTechTuple"
"""Name of set of conversion tech tuples"""

SET_CONVTECHIN: str = "S_ConvTechIn"
"""Name of set for all input tuples for conversion techs"""

SET_CONVTECHOUT: str = "S_ConvTechOut"
"""Name of set for all output tuples for conversion techs"""

VAR_CONVTECHIN: str = "V_ConvTechIn"
"""Name of variable for conversion tech inputs"""

VAR_CONVTECHOUT: str = "V_ConvTechOut"
"""Name of variable for conversion tech outputs"""

VAR_CONVTECHCOSTOPEXOUT: str = "V_ConvTechCostOpexOut"
"""Name of variable for cost of OPEX for conversion tech outputs"""

VAR_CONVTECHCO2OPER: str = "V_ConvTechCo2Oper"
"""Name of variable for operational CO2 from tech input"""

VAR_CONVTECHCO2OPERTOTAL: str = "V_ConvTechCo2OperTotal"
"""Name of variable for the total operational CO2 from tech input"""

VAR_CONVTECHCOSTTOTAL: str = "V_ConvTechCostTotal"
"""Name of variable for total cost in conversion tech module (equals OPEX for "
conversion outputs)"""

CON_CONVTECHINPART: str = "C_ConvTechInPart"
"""Name of constraint calculating the input composition of a conversion
technology"""

CON_CONVTECHOUTEFF: str = "C_ConvTechOutEff"
"""Name of constraint incorporating the output efficiency of a conversion
technology"""

CON_CONVTECHUSED: str = "C_ConvTechUsed"
"""Name of constraint determining whether a conversion technology was used"""

CON_CONVTECHCAPANDAVAILABILITY: str = "C_ConvTechCapAndAvailability"
"""Name of constraint limiting conversion technology output by capacity and
availability"""

CON_CONVTECHOUTSUMMIN: str = "C_ConvTechOutSumMin"
"""Name of constraint respecting the conversion parameter out_sum_min"""

CON_CONVTECHOUTSUMMAX: str = "C_ConvTechOutSumMax"
"""Name of constraint respecting the conversion parameter out_sum_max"""

CON_CONVTECHCOSTOPEXOUT: str = "C_ConvTechCostOpexOut"
"""Name of constraint calculation the OPEX costs for conversion outputs"""

CON_CONVTECHCO2OPER: str = "C_ConvTechCo2Oper"
"""Name of constraint calculation the operational CO2 emissions"""

CON_CONVTECHCO2OPERTOTAL: str = "C_ConvTechCo2OperTotal"
"""Name of constraint calculation the total operational CO2 emissions"""

CON_CONVTECHCOSTTOTAL: str = "C_ConvTechCostTotal"
"""Name of constraint calculation the total conversion costs (equals OPEX for "
conversion outputs)"""


def build(model: Model, system: EnergySystem) -> None:
    """
    Builds the conversion technology submodel. For a mathematical description in
    thorough detail, please refer to the section 'Conversion Tech Model' in the
    documentation.
    :param model: Pyomo model
    :type model: Model
    :param system: Energy system data
    :type system: EnergySystem
    """
    # Extract data from  modules
    ecs = system.ecs
    conv_techs = system.conv_techs
    times = system.times
    currency_unit = system.currency_unit
    mass_unit = system.mass_unit
    power_unit = system.power_unit
    # Start measuring build time
    start = datetime.now()
    # Build
    _build_base(model, system)
    _build_cost(model, ecs, conv_techs, times, currency_unit, mass_unit, power_unit)
    # Log
    elapsed = datetime.now() - start
    logging.log_file(
        f"Built conversion tech module. Elapsed time: {int(elapsed.total_seconds())}s",
        module=LOG_MODULE_STR,
    )


def _build_base(model: Model, system: EnergySystem) -> None:
    # Extract data from modules
    ecs = system.ecs
    conv_techs = system.conv_techs
    times = system.times
    mass_unit = system.mass_unit
    power_unit = system.power_unit
    # [SET] Conversion tech tuples
    setattr(
        model,
        SET_CONVTECHTUPLE,
        Set(
            within=getattr(model, SET_TECHTUPLE),
            initialize=[
                (s, h, x)
                for (s, h, x) in getattr(model, SET_TECHTUPLE)
                if TechId(x) in conv_techs.ids
            ],
        ),
    )

    # [SET] Tuples of conversion tech tuples and their input ecs
    setattr(
        model,
        SET_CONVTECHIN,
        Set(
            within=(getattr(model, SET_CONVTECHTUPLE) * getattr(model, SET_EC)),
            initialize=[
                (s, h, x, e.key)
                for (s, h, x) in getattr(model, SET_CONVTECHTUPLE)
                for e in conv_techs.get_in_ecs(TechId(x))
            ],
        ),
    )
    # [SET] Tuples of conversion tech tuples and their output  ecs
    setattr(
        model,
        SET_CONVTECHOUT,
        Set(
            within=(getattr(model, SET_CONVTECHTUPLE) * getattr(model, SET_EC)),
            initialize=[
                (s, h, x, e.key)
                for (s, h, x) in getattr(model, SET_CONVTECHTUPLE)
                for e in conv_techs.get_out_ecs(TechId(x))
            ],
        ),
    )
    # [VAR] Conversion input
    setattr(
        model,
        VAR_CONVTECHIN,
        Var(
            getattr(model, SET_CONVTECHIN),
            getattr(model, SET_TIME),
            domain=NonNegativeReals,
        ),
    )
    # [VAR] Conversion output
    setattr(
        model,
        VAR_CONVTECHOUT,
        Var(
            getattr(model, SET_CONVTECHOUT),
            getattr(model, SET_TIME),
            domain=NonNegativeReals,
        ),
    )
    # [VAR] Operational CO2 by conversion technology
    setattr(
        model,
        VAR_CONVTECHCO2OPER,
        Var(
            getattr(model, SET_CONVTECHTUPLE),
            domain=NonNegativeReals,
        ),
    )
    # [VAR] Total Operational CO2 by conversion technology
    setattr(
        model,
        VAR_CONVTECHCO2OPERTOTAL,
        Var(
            getattr(model, SET_STAGE),
            domain=NonNegativeReals,
        ),
    )
    # [CON] Input composition
    _con_conv_tech_in_part(model, ecs, conv_techs, mass_unit, power_unit)
    # [CON] Output efficiency
    _con_conv_tech_out_eff(model, ecs, conv_techs, mass_unit, power_unit)
    # [CON] Tech usage (monitored over summed-up output of main output EC)
    _con_conv_tech_used(model, system)
    # [CON] Respect conversion tech capacity (pertains to main output) and
    #       availability for the system output
    _con_conv_tech_cap_and_availability(model, conv_techs)
    # [CON] Enforce minima and maxima for up outputs
    _con_conv_tech_out_sum_minmax(model, ecs, conv_techs, times, mass_unit, power_unit)
    # [CON] Operational CO2 emissions
    _con_conv_tech_co2_oper(model, times, conv_techs, mass_unit)
    # [CON] Total Operational CO2 emissions
    _con_conv_tech_co2_oper_total(model)


def _build_cost(
    model: Model,
    ecs: Ecs,
    conv_techs: ConversionTechs,
    times: Times,
    currency_unit: CurrencyUnit,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
) -> None:
    # [VAR] OPEX (operation & maintenance) cost from conversion output
    setattr(
        model,
        VAR_CONVTECHCOSTOPEXOUT,
        Var(getattr(model, SET_CONVTECHTUPLE), domain=Reals),
    )
    # [CON] OPEX (operation & maintenance) cost from conversion output
    _con_conv_tech_cost_opex_out(
        model, ecs, conv_techs, times, currency_unit, mass_unit, power_unit
    )
    # [VAR] Total cost
    setattr(model, VAR_CONVTECHCOSTTOTAL, Var(domain=Reals))
    # [OBJ] Total cost
    _con_conv_tech_cost_total(model)


def _con_conv_tech_in_part(
    model: Model,
    ecs: Ecs,
    conv_techs: ConversionTechs,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
) -> None:
    def __rule_conv_tech_in_part(model, s, h, x, e, t):
        # Get parameters
        e_in_main = conv_techs.get_in_ec_main(TechId(x))
        if EcId(e) == e_in_main:
            return Constraint.Skip
        ec_unit = get_ec_model_unit(ecs.get_unit(EcId(e)), mass_unit, power_unit)
        ec_unit_main = get_ec_model_unit(ecs.get_unit(e_in_main), mass_unit, power_unit)
        in_part = conv_techs.get_in_part(StageId(s), TechId(x), EcId(e)).to_float(
            unit=ec_unit
        )
        in_part_main = conv_techs.get_in_part(
            StageId(s), TechId(x), e_in_main
        ).to_float(unit=ec_unit_main)

        # Get input variables
        var_in = getattr(model, VAR_CONVTECHIN)[s, h, x, e, t]
        var_in_main = getattr(model, VAR_CONVTECHIN)[s, h, x, e_in_main.key, t]

        # Calculate input variables normed to in_parts
        rel_in = var_in / in_part
        rel_in_main = var_in_main / in_part_main

        # Set constraint
        return rel_in == rel_in_main

    setattr(
        model,
        CON_CONVTECHINPART,
        Constraint(
            getattr(model, SET_CONVTECHIN),
            getattr(model, SET_TIME),
            rule=__rule_conv_tech_in_part,
        ),
    )


def _con_conv_tech_out_eff(
    model: Model,
    ecs: Ecs,
    conv_techs: ConversionTechs,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
) -> None:
    def __rule_conv_tech_out_eff(model, s, h, x, e, t):
        # Get parameters
        in_ec_main = conv_techs.get_in_ec_main(TechId(x))
        ec_unit = get_ec_model_unit(ecs.get_unit(EcId(e)), mass_unit, power_unit)
        in_ec_main_unit = get_ec_model_unit(
            ecs.get_unit(in_ec_main), mass_unit, power_unit
        )
        # Get conversion efficiency
        efficiency = (
            conv_techs.get_out_eff(StageId(s), TechId(x), EcId(e))
            .get_value(TimeId(t))
            .to_float(unit=(ec_unit / in_ec_main_unit))
        )
        # Calculate conversion output based on efficiency and main ec input:
        out = efficiency * getattr(model, VAR_CONVTECHIN)[s, h, x, in_ec_main.key, t]
        # Set constraint
        return getattr(model, VAR_CONVTECHOUT)[s, h, x, e, t] == out

    setattr(
        model,
        CON_CONVTECHOUTEFF,
        Constraint(
            getattr(model, SET_CONVTECHOUT),
            getattr(model, SET_TIME),
            rule=__rule_conv_tech_out_eff,
        ),
    )


def _con_conv_tech_used(model: Model, system: EnergySystem) -> None:
    # Extract data from modules
    ecs = system.ecs
    conv_techs = system.conv_techs
    times = system.times
    mass_unit = system.mass_unit
    power_unit = system.power_unit

    def __rule_conv_tech_used(model, s, h, x):
        # Get parameters
        e_out_main = conv_techs.get_out_ec_main(TechId(x))
        e_out_main_unit = get_ec_model_unit(
            ecs.get_unit(e_out_main), mass_unit, power_unit
        )
        # a) bigM by user-defined out_sum_max
        bigm_summax = conv_techs.get_out_sum_max(
            StageId(s), HubId(h), TechId(x)
        ).to_float(unit=e_out_main_unit)
        bigm = bigm_summax
        # b) bigM by capacity times horizon length
        if TechId(x) not in system.solar_techs.ids:
            cap_max = getattr(model, VAR_TECHCAP)[s, h, x].ub
            bigm_cap = cap_max * system.times.num_horizon_ts
            bigm = min(bigm, bigm_cap)
        # c) bigM by heuristic limit
        bigm_heur = system.get_heur_limit_max_sum_out(
            StageId(s), HubId(h), e_out_main
        ).to_float(unit=e_out_main_unit)
        bigm = min(bigm, bigm_heur)
        # Calculate summed-up output
        out_sum = sum(
            times.get_weight(StageId(s), TimeId(t))
            * getattr(model, VAR_CONVTECHOUT)[s, h, x, e_out_main.key, t]
            for t in getattr(model, SET_TIME)
        )
        # Set constraint
        bigm = max(bigm, 1) + common.EPS_BIGM
        return out_sum <= bigm * getattr(model, VAR_YTECHUSED)[s, h, x]

    setattr(
        model,
        CON_CONVTECHUSED,
        Constraint(getattr(model, SET_CONVTECHTUPLE), rule=__rule_conv_tech_used),
    )


def _con_conv_tech_cap_and_availability(
    model: Model, conv_techs: ConversionTechs
) -> None:
    def __rule_conv_tech_cap_and_availability(model, s, h, x, t):
        # Get parameters
        out_ec_main = conv_techs.get_out_ec_main(TechId(x))
        availability = (
            conv_techs.get_availability(StageId(s), HubId(h), TechId(x))
            .get_value(TimeId(t))
            .to_float()
        )
        # Calculate maximal output of main output ec
        out_max = availability * getattr(model, VAR_TECHCAP)[s, h, x]
        # Set constraint
        return getattr(model, VAR_CONVTECHOUT)[s, h, x, out_ec_main.key, t] <= out_max

    setattr(
        model,
        CON_CONVTECHCAPANDAVAILABILITY,
        Constraint(
            getattr(model, SET_CONVTECHTUPLE),
            getattr(model, SET_TIME),
            rule=__rule_conv_tech_cap_and_availability,
        ),
    )


def _con_conv_tech_out_sum_minmax(
    model: Model,
    ecs: Ecs,
    conv_techs: ConversionTechs,
    times: Times,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
) -> None:
    def __rule_conv_tech_out_sum_min(model, s, h, x):
        # Get parameters
        out_ec_main = conv_techs.get_out_ec_main(TechId(x))
        ec_unit = get_ec_model_unit(ecs.get_unit(out_ec_main), mass_unit, power_unit)
        out_sum_min = conv_techs.get_out_sum_min(
            StageId(s), HubId(h), TechId(x)
        ).to_float(unit=ec_unit)
        if out_sum_min <= 0:
            return Constraint.Skip
        # Calculate summed-up output for main output ec
        out_sum_main = sum(
            times.get_weight(StageId(s), TimeId(t))
            * getattr(model, VAR_CONVTECHOUT)[s, h, x, out_ec_main.key, t]
            for t in getattr(model, SET_TIME)
        )
        # Set constraint
        return out_sum_main >= out_sum_min

    def __rule_conv_tech_out_sum_max(model, s, h, x):
        # Get parameters
        out_ec_main = conv_techs.get_out_ec_main(TechId(x))
        ec_unit = get_ec_model_unit(ecs.get_unit(out_ec_main), mass_unit, power_unit)
        out_sum_max = conv_techs.get_out_sum_max(
            StageId(s), HubId(h), TechId(x)
        ).to_float(unit=ec_unit)
        if out_sum_max == float("inf"):
            return Constraint.Skip
        # Calculate up output for main output ec
        out_sum_main = sum(
            times.get_weight(StageId(s), TimeId(t))
            * getattr(model, VAR_CONVTECHOUT)[s, h, x, out_ec_main.key, t]
            for t in getattr(model, SET_TIME)
        )
        # Set constraint
        return out_sum_main <= out_sum_max

    setattr(
        model,
        CON_CONVTECHOUTSUMMIN,
        Constraint(
            getattr(model, SET_CONVTECHTUPLE), rule=__rule_conv_tech_out_sum_min
        ),
    )
    setattr(
        model,
        CON_CONVTECHOUTSUMMAX,
        Constraint(
            getattr(model, SET_CONVTECHTUPLE), rule=__rule_conv_tech_out_sum_max
        ),
    )


def _con_conv_tech_cost_opex_out(
    model: Model,
    ecs: Ecs,
    conv_techs: ConversionTechs,
    times: Times,
    currency_unit: CurrencyUnit,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
) -> None:
    def __rule_conv_tech_cost_opex_out(model, s, h, x):
        # Get parameters
        out_ec_main = conv_techs.get_out_ec_main(TechId(x))
        ec_unit = get_ec_model_unit(ecs.get_unit(out_ec_main), mass_unit, power_unit)
        opex_per_energy = conv_techs.get_opex_per_energy(
            StageId(s), TechId(x)
        ).to_float(unit=(currency_unit / ec_unit))
        # Calculate summed-up output for all output ECs
        out_sum = sum(
            times.get_weight(StageId(s), TimeId(t))
            * getattr(model, VAR_CONVTECHOUT)[s, h, x, e.key, t]
            for e in conv_techs.get_out_ecs(TechId(x))
            for t in getattr(model, SET_TIME)
        )
        # Calulate OPEX per output energy cost
        cost_opex_out = opex_per_energy * out_sum
        # Set constraint
        return getattr(model, VAR_CONVTECHCOSTOPEXOUT)[s, h, x] == cost_opex_out

    setattr(
        model,
        CON_CONVTECHCOSTOPEXOUT,
        Constraint(
            getattr(model, SET_CONVTECHTUPLE), rule=__rule_conv_tech_cost_opex_out
        ),
    )


def _con_conv_tech_co2_oper(
    model: Model,
    times: Times,
    conv_techs: ConversionTechs,
    mass_unit: MassUnit,
) -> None:
    def __rule_conv_tech_co2_oper(model, s, h, x):
        co2_oper = sum(
            times.get_weight(StageId(s), TimeId(t))
            * conv_techs.get_co2_per_in(
                StageId(s),
                TechId(x),
                e,
            ).to_float(
                unit=mass_unit
                / conv_techs.get_in_part(
                    StageId(s),
                    TechId(x),
                    e,
                ).unit
            )
            * getattr(model, VAR_CONVTECHIN)[s, h, x, e.key, t]
            for e in conv_techs.get_in_ecs(TechId(x))
            for t in getattr(model, SET_TIME)
        )

        return getattr(model, VAR_CONVTECHCO2OPER)[s, h, x] == co2_oper

    setattr(
        model,
        CON_CONVTECHCO2OPER,
        Constraint(
            getattr(model, SET_CONVTECHTUPLE),
            rule=__rule_conv_tech_co2_oper,
        ),
    )


def _con_conv_tech_co2_oper_total(model: Model) -> None:
    """Sum operational CO2 emissions over all conversion technologies."""

    def __rule_conv_tech_co2_oper_total(model, s):
        co2_oper_total = quicksum(
            getattr(model, VAR_CONVTECHCO2OPER)[s_tuple, h, x]
            for s_tuple, h, x in getattr(model, SET_CONVTECHTUPLE)
            if s_tuple == s
        )

        return getattr(model, VAR_CONVTECHCO2OPERTOTAL)[s] == co2_oper_total

    setattr(
        model,
        CON_CONVTECHCO2OPERTOTAL,
        Constraint(
            getattr(model, SET_STAGE),
            rule=__rule_conv_tech_co2_oper_total,
        ),
    )


def _con_conv_tech_cost_total(model: Model) -> None:
    def __rule_conv_tech_cost_total(model):
        # Calculate the total conversion tech cost
        conv_tech_cost_total = sum(
            getattr(model, VAR_CONVTECHCOSTOPEXOUT)[s, h, x]
            for (s, h, x) in getattr(model, SET_CONVTECHTUPLE)
        )
        # Set the constraint
        return getattr(model, VAR_CONVTECHCOSTTOTAL) == conv_tech_cost_total

    setattr(model, CON_CONVTECHCOSTTOTAL, Constraint(rule=__rule_conv_tech_cost_total))
