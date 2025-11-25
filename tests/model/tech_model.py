"""Technology submodel"""

from datetime import datetime

from pyomo.core import Binary, Constraint, Model, NonNegativeReals, Reals, Set, Var

from ehubx.core import common, exceptions, logging
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.unit import (
    CurrencyUnit,
    DimlessUnit,
    LengthUnit,
    MassUnit,
    PowerUnit,
    TimeUnit,
    Unit,
)
from ehubx.data.value import Value
from ehubx.model.common import calculate_crf
from ehubx.model.hub_model import SET_HUB
from ehubx.model.stage_model import SET_STAGE


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/tech"
"""String identifying the technology model for logging purposes"""

SET_TECH: str = "S_Tech"
"""Name of set with tech indices"""

SET_TECHTUPLE: str = "S_TechTuple"
"""Name of set with tech tuples"""

VAR_TECHCAP: str = "V_TechCap"
"""Name of variable for tech capacity"""

VAR_TECHCAPINSTL: str = "V_TechCapInstl"
"""Name of variable for installed tech capacity"""

VAR_YTECHCAPINSTL: str = "V_YTechCapInstl"
"""Name of binary variable monitoring tech capacity installation"""

VAR_YTECHUSED: str = "V_YTechUsed"
"""Name of binary variable monitoring tech usage"""

VAR_TECHCOSTCAPEX: str = "V_TechCostCapex"
"""Name of variable for CAPEX costs of tech installation"""

VAR_TECHCOSTOPEXCAP: str = "V_TechCostOpexCap"
"""Name of variable for OPEX costs for tech capacity"""

VAR_TECHCOSTTOTAL: str = "V_TechCostTotal"
"""Name of variable for total tech capacity-related costs (CAPEX and OPEX)"""

VAR_TECHCO2INSTL: str = "V_TechCo2Instl"
"""Name of variable for embodied CO2 from tech installation"""

VAR_TECHCO2TOTAL: str = "V_TechCo2Total"
"""Name of variable for embodied CO2 from tech installation
(summed over hubs)"""

CON_TECHCAP: str = "C_TechCap"
"""Name of constraint fixing the tech capacity"""

CON_YTECHINSTL: str = "C_YTechInstl"
"""Name of constraint determining whether any technology was installed"""

CON_TECHUNITCAPMIN: str = "C_TechUnitCapMin"
"""Name of constraint respecting the unit_cap_min parameter"""

CON_TECHINSTLALLOWED: str = "C_TechInstlAllowed"
"""Name of constraint respecting the last_instl_year parameter"""

CON_TECHCOUPLEDCAP: str = "C_TechCoupledCap"
"""Name of constraint respecting capacity for coupled techs"""

CON_TECHCOSTCAPEX: str = "C_TechCostCapex"
"""Name of constraint calculating tech costs from CAPEX"""

CON_TECHCOSTOPEXCAP: str = "C_TechCostOpexCap"
"""Name of constraint calculating tech costs from OPEX"""

CON_TECHCOSTTOTAL: str = "C_TechCostTotal"
"""Name of constraint calculating total tech costs (CAPEX + OPEX)"""

CON_TECHCO2INSTL: str = "C_TechCo2Instl"
"""Name of constraint calculating embodied CO2 emissions from tech
installation"""

CON_TECHCO2TOTAL: str = "C_TechCo2Total"
"""Name of constraint calculating total embodied CO2 emissions from tech
installation (summed over hubs)"""


def build(model: Model, system: EnergySystem) -> None:
    """
    Builds the technology submodel. For a mathematical description in thorough
    detail, please refer to the section 'Technology model' in the
    documentation.

    :param model: Pyomo model
    :type model: Model
    :param system: Energy system data
    :type system: EnergySystem
    """
    # Extract data from modules
    stages: Stages = system.stages
    techs: Techs = system.techs
    currency_unit: CurrencyUnit = system.currency_unit
    length_unit: LengthUnit = system.length_unit
    mass_unit: MassUnit = system.mass_unit
    power_unit: PowerUnit = system.power_unit
    # Start measuring build time
    start = datetime.now()
    _build_base(model, system)
    _build_cost(model, stages, techs, currency_unit, length_unit, mass_unit, power_unit)
    _build_co2(model, stages, techs, length_unit, mass_unit, power_unit)
    # Logging
    elapsed = datetime.now() - start
    logging.log_file(
        f"Built tech module. Elapsed time: {int(elapsed.total_seconds())}s",
        module=LOG_MODULE_STR,
    )


def _build_base(model: Model, system: EnergySystem) -> None:
    # Extract data from modules
    stages: Stages = system.stages
    techs: Techs = system.techs
    length_unit: LengthUnit = system.length_unit
    mass_unit: MassUnit = system.mass_unit
    power_unit: PowerUnit = system.power_unit
    # [SET] techs
    setattr(model, SET_TECH, Set(initialize=[x.key for x in system.techs.ids]))
    # [SET] Tuples of (stage, hub, tech) which are are allowed by TRL or
    #       allowed_tech_lists
    setattr(
        model,
        SET_TECHTUPLE,
        Set(
            within=(
                getattr(model, SET_STAGE)
                * getattr(model, SET_HUB)
                * getattr(model, SET_TECH)
            ),
            initialize=[
                (s.key, h.key, x.key)
                for x in techs.ids
                for s in techs.get_allowed_stages(x)
                for h in techs.get_allowed_hubs(x)
            ],
        ),
    )

    # [BOUND] Tech capacity
    def _cap_bounds(model, s, h, x):
        cap_min_fl: float = 0.0
        cap_max_fl: float
        cap_unit = get_model_cap_unit(
            techs.get_cap_unit(TechId(x)), length_unit, mass_unit, power_unit
        )
        cap_min = techs.get_cap_min(StageId(s), HubId(h), TechId(x))
        cap_max = techs.get_cap_max(StageId(s), HubId(h), TechId(x))
        if cap_min.is_positive:
            cap_min_fl = cap_min.to_float(unit=cap_unit)
        if cap_max.is_finite:
            cap_max_fl = cap_max.to_float(unit=cap_unit)
        else:
            if TechId(x) in system.ebm_techs.ids:
                cap_vehicle = system.ebm_techs.get_storage_cap(StageId(s), TechId(x))
                num_vehicles = system.ebm_techs.get_num_vehicles(
                    StageId(s), HubId(h), TechId(x)
                )
                cap_max = cap_vehicle * num_vehicles
            elif TechId(x) in system.stor_techs.ids:
                e = system.stor_techs.get_ec(TechId(x))
                cap_max = system.get_heur_limit_max_sum_out(StageId(s), HubId(h), e)
            elif TechId(x) in system.ates_techs.ids:
                cap_max = system.ates_data.get_available_area(StageId(s), HubId(h))
            elif TechId(x) in system.solar_techs.ids:
                max_area = sum(
                    system.solar_data.get_area(StageId(s), HubId(h), e)
                    for e in system.solar_data.ecs
                )
                cap_max = (
                    max_area if isinstance(max_area, Value) else Value(0, unit="m^2")
                )
            elif TechId(x) in system.hp_techs.ids:
                e = system.hp_techs.get_ec_ht_out(TechId(x))
                cap_max = system.get_heur_limit_max_out(StageId(s), HubId(h), e)
            elif TechId(x) in system.conv_techs.ids:
                e = system.conv_techs.get_out_ec_main(TechId(x))
                cap_max = system.get_heur_limit_max_out(StageId(s), HubId(h), e)
            else:
                raise exceptions.EhubXException(
                    f"Tech {x} has no defined cap_max and cannot be "
                    f"linked to a heuristic limit. Please define a "
                    f"cap_max value in hubs.yaml.",
                    module=LOG_MODULE_STR,
                )
            cap_max_fl = cap_max.to_float(unit=cap_unit)
        return (cap_min_fl, cap_max_fl)

    # [VAR] Total tech capacity
    setattr(
        model,
        VAR_TECHCAP,
        Var(getattr(model, SET_TECHTUPLE), domain=NonNegativeReals, bounds=_cap_bounds),
    )
    # [VAR] Tech capacity installed during any stage
    setattr(
        model,
        VAR_TECHCAPINSTL,
        Var(getattr(model, SET_TECHTUPLE), domain=NonNegativeReals),
    )
    # [VAR] Binary monitoring new tech installation
    setattr(model, VAR_YTECHCAPINSTL, Var(getattr(model, SET_TECHTUPLE), domain=Binary))
    # [VAR] Binary monitoring tech usage (needs a defining constraint in each
    #       tech submodule since usage depends on tech type)
    setattr(model, VAR_YTECHUSED, Var(getattr(model, SET_TECHTUPLE), domain=Binary))
    # [CON] Define TechCap as the sum of initial capacity and installed
    #       capacity from previous stages for which lifetime has not run out
    _con_tech_cap(model, stages, techs, length_unit, mass_unit, power_unit)
    # [CON] Force YTechCapInstl to 1 if TechCapInstl is nonzero
    _con_y_tech_instl(model)
    # [CON] Enforce the minimal unit capacity during installation
    _con_tech_unit_cap_min(model, techs, length_unit, mass_unit, power_unit)
    # [CON] Limit installation to allowed tuples
    _con_tech_instl_allowed(model, stages, techs)
    # [CON] Force capacity of coupled techs to the predefined
    #       fraction of the main tech's capacity
    _con_tech_coupled_cap(model, techs, length_unit, mass_unit, power_unit)


def _build_cost(
    model: Model,
    stages: Stages,
    techs: Techs,
    currency_unit: CurrencyUnit,
    length_unit: LengthUnit,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
) -> None:
    # [VAR] CAPEX cost
    setattr(model, VAR_TECHCOSTCAPEX, Var(getattr(model, SET_TECHTUPLE), domain=Reals))
    # [CON] CAPEX cost
    _con_tech_cost_capex(
        model, stages, techs, currency_unit, length_unit, mass_unit, power_unit
    )
    # [VAR] OPEX (operation & maintenance) cost from capacity
    setattr(
        model, VAR_TECHCOSTOPEXCAP, Var(getattr(model, SET_TECHTUPLE), domain=Reals)
    )
    # [CON] OPEX cost from capacity
    _con_tech_cost_opex_cap(
        model, techs, currency_unit, length_unit, mass_unit, power_unit
    )
    # [VAR] Total cost
    setattr(model, VAR_TECHCOSTTOTAL, Var(domain=Reals))
    # [CON] Total cost
    _con_tech_cost_total(model)


def _build_co2(
    model: Model,
    stages: Stages,
    techs: Techs,
    length_unit: LengthUnit,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
) -> None:
    # [VAR] CO2 emissions from tech installation
    setattr(model, VAR_TECHCO2INSTL, Var(getattr(model, SET_TECHTUPLE), domain=Reals))
    # [CON] CO2 emissions from tech installation
    _con_tech_co2_instl(model, stages, techs, length_unit, mass_unit, power_unit)
    # [VAR] Total CO2 emissions from techs
    setattr(model, VAR_TECHCO2TOTAL, Var(getattr(model, SET_STAGE), domain=Reals))
    # [CON] Total CO2 emissions from techs
    _con_tech_co2_total(model)


# ------------------ #
# Constraint methods #
# ------------------ #
def _con_tech_cap(
    model: Model,
    stages: Stages,
    techs: Techs,
    length_unit: LengthUnit,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
) -> None:
    def __rule_tech_cap(model, s, h, x):
        # Parameters
        current_year = stages.get_start_year(StageId(s))
        tech_lifetime = techs.get_lifetime(TechId(x)).to_float(TimeUnit.A)
        age_init = techs.get_age_init(HubId(h), TechId(x)).to_float(TimeUnit.A)
        cap_unit = get_model_cap_unit(
            techs.get_cap_unit(TechId(x)), length_unit, mass_unit, power_unit
        )
        cap_init = techs.get_cap_init(HubId(h), TechId(x)).to_float(unit=cap_unit)
        tech_cap = 0
        # Initial capacity
        if current_year - stages.init_year < tech_lifetime - age_init:
            tech_cap += cap_init
        # Capacity installed during previous stages
        for s_instl in getattr(model, SET_STAGE):
            # Check that installation was possible in s_instl
            if (s_instl, h, x) not in getattr(model, SET_TECHTUPLE):
                continue
            # Check current stage is within lifetime of installed tech
            start_year_instl = stages.get_start_year(StageId(s_instl))
            if current_year < start_year_instl:
                continue
            if current_year - start_year_instl >= tech_lifetime:
                continue
            # Add installed capacity to total
            tech_cap += getattr(model, VAR_TECHCAPINSTL)[s_instl, h, x]
        # Set constraint
        return getattr(model, VAR_TECHCAP)[s, h, x] == tech_cap

    setattr(
        model,
        CON_TECHCAP,
        Constraint(getattr(model, SET_TECHTUPLE), rule=__rule_tech_cap),
    )


def _con_y_tech_instl(model: Model) -> None:
    def __rule_y_tech_instl(model, s, h, x):
        var_tech_cap = getattr(model, VAR_TECHCAP)[s, h, x]
        var_tech_cap_instl = getattr(model, VAR_TECHCAPINSTL)[s, h, x]
        cap_max = var_tech_cap.ub
        if cap_max is None or cap_max == float("inf"):
            raise exceptions.EhubXException(
                f"Cannot determine maximum capacity for tech "
                f"{x} in stage {s} at hub {h} to calculate a bigM parameter for "
                f"{VAR_YTECHCAPINSTL}. Please set a finite cap_max value in hubs.yaml.",
                module=LOG_MODULE_STR,
            )
        bigm = max(cap_max, 1) + common.EPS_BIGM
        # Set constraint
        return var_tech_cap_instl <= bigm * getattr(model, VAR_YTECHCAPINSTL)[s, h, x]

    setattr(
        model,
        CON_YTECHINSTL,
        Constraint(getattr(model, SET_TECHTUPLE), rule=__rule_y_tech_instl),
    )


def _con_tech_unit_cap_min(
    model: Model,
    techs: Techs,
    length_unit: LengthUnit,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
) -> None:
    def __rule_tech_unit_cap_min(model, s, h, x):
        cap_unit = get_model_cap_unit(
            techs.get_cap_unit(TechId(x)), length_unit, mass_unit, power_unit
        )
        unit_cap_min = techs.get_unit_cap_min(StageId(s), TechId(x)).to_float(
            unit=cap_unit
        )
        if unit_cap_min < common.EPS_ZEROCHECK:
            return Constraint.Skip
        return (
            getattr(model, VAR_TECHCAPINSTL)[s, h, x]
            >= unit_cap_min * getattr(model, VAR_YTECHCAPINSTL)[s, h, x]
        )

    setattr(
        model,
        CON_TECHUNITCAPMIN,
        Constraint(getattr(model, SET_TECHTUPLE), rule=__rule_tech_unit_cap_min),
    )


def _con_tech_instl_allowed(model: Model, stages: Stages, techs: Techs) -> None:
    def __rule_tech_instl_allowed(model, s, h, x):
        # Get parameters
        stage_year = stages.get_start_year(StageId(s))
        last_instl_year = techs.get_last_inst_year(HubId(h), TechId(x))
        # If installation is allowed, no constraint necessary
        if stage_year <= last_instl_year:
            return Constraint.Skip
        # If installation is not allowed, force installation binary to zero
        return getattr(model, VAR_YTECHCAPINSTL)[s, h, x] == 0

    setattr(
        model,
        CON_TECHINSTLALLOWED,
        Constraint(getattr(model, SET_TECHTUPLE), rule=__rule_tech_instl_allowed),
    )


def _con_tech_coupled_cap(
    model: Model,
    techs: Techs,
    length_unit: LengthUnit,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
) -> None:
    def __rule_tech_coupled_cap(model, s, h, x):
        # Only define constraint for sub techs
        if TechId(x) not in techs.coupled_sub_techs:
            return Constraint.Skip
        # Parameters
        x_main = techs.get_coupled_main_tech(TechId(x)).key
        cap_unit = get_model_cap_unit(
            techs.get_cap_unit(TechId(x)), length_unit, mass_unit, power_unit
        )
        cap_unit_main = get_model_cap_unit(
            techs.get_cap_unit(TechId(x_main)), length_unit, mass_unit, power_unit
        )
        cap_factor = techs.get_coupled_cap_factor(TechId(x)).to_float(
            unit=(cap_unit / cap_unit_main)
        )
        # Tie sub capacity to main capacity
        return (
            getattr(model, VAR_TECHCAP)[s, h, x]
            == cap_factor * getattr(model, VAR_TECHCAP)[s, h, x_main]
        )

    setattr(
        model,
        CON_TECHCOUPLEDCAP,
        Constraint(getattr(model, SET_TECHTUPLE), rule=__rule_tech_coupled_cap),
    )


def _con_tech_cost_capex(
    model: Model,
    stages: Stages,
    techs: Techs,
    currency_unit: CurrencyUnit,
    length_unit: LengthUnit,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
) -> None:
    def __rule_tech_cost_capex(model, s, h, x):
        # Parameters
        current_year = stages.get_start_year(StageId(s))
        interest_rate = techs.get_interest_rate(TechId(x)).to_float()
        tech_lifetime = techs.get_lifetime(TechId(x)).to_float(TimeUnit.A)
        crf = calculate_crf(interest_rate, tech_lifetime)
        cost_capex = 0
        # Installation stages
        for s_instl in getattr(model, SET_STAGE):
            # Only consider valid tech tuples
            if (s_instl, h, x) not in getattr(model, SET_TECHTUPLE):
                continue
            # Check current stage is within lifetime of installed tech
            start_year_instl = stages.get_start_year(StageId(s_instl))
            if current_year < start_year_instl:
                continue
            if current_year - start_year_instl >= tech_lifetime:
                continue
            # Installation-stage-dependent parameters
            cap_unit = get_model_cap_unit(
                techs.get_cap_unit(TechId(x)), length_unit, mass_unit, power_unit
            )
            capex_per_cap = techs.get_capex_per_cap(
                StageId(s_instl), TechId(x)
            ).to_float(unit=(currency_unit / cap_unit))
            one_time_capex = techs.get_one_time_capex(
                StageId(s_instl), TechId(x)
            ).to_float(unit=currency_unit)
            # One-time capex costs (if installation occured)
            cost_capex += (
                crf * one_time_capex * getattr(model, VAR_YTECHCAPINSTL)[s_instl, h, x]
            )
            # Per-capacity capex costs
            cost_capex += (
                crf * capex_per_cap * getattr(model, VAR_TECHCAPINSTL)[s_instl, h, x]
            )

        # Set constraint
        return getattr(model, VAR_TECHCOSTCAPEX)[s, h, x] == cost_capex

    setattr(
        model,
        CON_TECHCOSTCAPEX,
        Constraint(getattr(model, SET_TECHTUPLE), rule=__rule_tech_cost_capex),
    )


def _con_tech_cost_opex_cap(
    model: Model,
    techs: Techs,
    currency_unit: CurrencyUnit,
    length_unit: LengthUnit,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
) -> None:
    def __rule_tech_cost_opex_cap(model, s, h, x):
        # Parameters
        cap_unit = get_model_cap_unit(
            techs.get_cap_unit(TechId(x)), length_unit, mass_unit, power_unit
        )
        opex_per_cap = techs.get_opex_per_cap(StageId(s), TechId(x)).to_float(
            unit=(currency_unit / cap_unit)
        )
        one_time_opex = techs.get_one_time_opex(StageId(s), TechId(x)).to_float(
            unit=currency_unit
        )
        # OPEX from capacity calulation
        cost_opex_cap = (
            one_time_opex * getattr(model, VAR_YTECHUSED)[s, h, x]
            + opex_per_cap * getattr(model, VAR_TECHCAP)[s, h, x]
        )
        # Set constraint
        return getattr(model, VAR_TECHCOSTOPEXCAP)[s, h, x] == cost_opex_cap

    setattr(
        model,
        CON_TECHCOSTOPEXCAP,
        Constraint(getattr(model, SET_TECHTUPLE), rule=__rule_tech_cost_opex_cap),
    )


def _con_tech_cost_total(model: Model) -> None:
    def __rule_tech_cost_total(model):
        # Calculate the total tech cost
        tech_cost_total = sum(
            getattr(model, VAR_TECHCOSTCAPEX)[s, h, x]
            + getattr(model, VAR_TECHCOSTOPEXCAP)[s, h, x]
            for (s, h, x) in getattr(model, SET_TECHTUPLE)
        )
        # Set the constraint
        return getattr(model, VAR_TECHCOSTTOTAL) == tech_cost_total

    setattr(model, CON_TECHCOSTTOTAL, Constraint(rule=__rule_tech_cost_total))


def _con_tech_co2_instl(
    model: Model,
    stages: Stages,
    techs: Techs,
    length_unit: LengthUnit,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
) -> None:
    def __rule_tech_co2_instl(model, s, h, x):
        # Parameters
        current_year = stages.get_start_year(StageId(s))
        tech_lifetime = techs.get_lifetime(TechId(x)).to_float(TimeUnit.A)
        cap_unit = get_model_cap_unit(
            techs.get_cap_unit(TechId(x)), length_unit, mass_unit, power_unit
        )
        co2_per_cap = techs.get_co2_per_cap(StageId(s), TechId(x)).to_float(
            unit=(mass_unit / cap_unit)
        )
        co2_instl = 0
        # Installation stages
        for s_instl in getattr(model, SET_STAGE):
            # Only consider valid tech tuples
            if (s_instl, h, x) not in getattr(model, SET_TECHTUPLE):
                continue
            # Check current stage is within lifetime of installed tech
            start_year_instl = stages.get_start_year(StageId(s_instl))
            if current_year < start_year_instl:
                continue
            if current_year - start_year_instl >= tech_lifetime:
                continue
            # Add the CO2 for the current stage
            co2_instl += (
                co2_per_cap * getattr(model, VAR_TECHCAP)[s_instl, h, x] / tech_lifetime
            )

        # Set constraint
        return getattr(model, VAR_TECHCO2INSTL)[s, h, x] == co2_instl

    setattr(
        model,
        CON_TECHCO2INSTL,
        Constraint(getattr(model, SET_TECHTUPLE), rule=__rule_tech_co2_instl),
    )


def _con_tech_co2_total(model: Model) -> None:
    def __rule_tech_co2_total(model, s):
        # Calculate the total tech CO2
        tech_co2_total = sum(
            getattr(model, VAR_TECHCO2INSTL)[s, h, x]
            for (s_, h, x) in getattr(model, SET_TECHTUPLE)
            if s == s_
        )
        # Set the constraint
        return getattr(model, VAR_TECHCO2TOTAL)[s] == tech_co2_total

    setattr(
        model,
        CON_TECHCO2TOTAL,
        Constraint(getattr(model, SET_STAGE), rule=__rule_tech_co2_total),
    )


def get_model_cap_unit(
    cap_unit: Unit,
    model_length_unit: LengthUnit,
    model_mass_unit: MassUnit,
    model_power_unit: PowerUnit,
) -> Unit:
    """
    Get the unit of a tech capacity that will be used in the MILP model. This
    is either an ec unit (mass or energy), an ec unit divided by hours, or an
    area unit, depending on the unit of the tech capacity.

    :param cap_unit: Unit of the tech capacity
    :type cap_unit: Unit
    :param model_length_unit: Length unit used in the model
    :type model_length_unit: LengthUnit
    :param model_mass_unit: Mass unit used in the model
    :type model_mass_unit: MassUnit
    :param model_power_unit: Power unit used in the model
    :type model_power_unit: PowerUnit
    :raises RuntimeError: If the cap_unit is not a valid unit for a tech capacity
    :return: The model unit corresponding to the cap_unit
    :rtype: Unit
    """
    # Storage-like techs (energy)
    if cap_unit.same_type_as(model_power_unit * TimeUnit.H):
        return model_power_unit * TimeUnit.H
    # Storage-like techs (energy)
    elif cap_unit.same_type_as(model_mass_unit):
        return model_mass_unit
    # Conversion-like techs (power)
    elif cap_unit.same_type_as(model_power_unit):
        return model_power_unit
    # Conversion-like techs (mass over time)
    elif cap_unit.same_type_as(model_mass_unit / TimeUnit.H):
        return model_mass_unit / TimeUnit.H
    # Area-capacity techs
    elif cap_unit.same_type_as(model_length_unit**2):
        return model_length_unit**2
    # Dimless techs (happens if they don't have a type)
    elif cap_unit.same_type_as(DimlessUnit()):
        return DimlessUnit()
    else:
        raise RuntimeError(
            f"Unexpected cap_unit {cap_unit} encountered. This should never happen."
        )
