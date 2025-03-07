"""Technology submodel"""

from datetime import datetime

from pyomo.core import Binary, Constraint, Model, NonNegativeReals, Reals, Set, Var

from ehubx.core import common, logging
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.tech_data import TechId, Techs
from ehubx.model.common import calculate_crf
from ehubx.model.demand_model import PAR_BIGMGENERIC
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

CON_TECHCAPMIN: str = "C_TechCapMin"
"""Name of constraint respecting the cap_min parameter"""

CON_TECHCAPMAX: str = "C_TechCapMax"
"""Name of constraint respecting the cap_max parameter"""

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


def build(model: Model, stages: Stages, techs: Techs) -> None:
    """
    Builds the technology submodel. For a mathematical description in thorough
    detail, please refer to the section 'Technology model' in the
    documentation.

    :param model: Pyomo model
    :type model: Model
    :param stages: Stage data class
    :type stages: Stages
    :param techs: Technology data class
    :type techs: Techs
    """
    # Start measuring build time
    start = datetime.now()
    _build_base(model, stages, techs)
    _build_cost(model, stages, techs)
    _build_co2(model, stages, techs)
    # Logging
    elapsed = datetime.now() - start
    logging.log_file(
        f"Built tech module. Elapsed time: {int(elapsed.total_seconds())}s",
        module=LOG_MODULE_STR,
    )


def _build_base(model: Model, stages: Stages, techs: Techs) -> None:
    # [SET] techs
    setattr(model, SET_TECH, Set(initialize=[x.key for x in techs.ids]))
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
    # [VAR] Total tech capacity
    setattr(
        model, VAR_TECHCAP, Var(getattr(model, SET_TECHTUPLE), domain=NonNegativeReals)
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
    _con_tech_cap(model, stages, techs)
    # [CON] Force YTechCapInstl to 1 if TechCapInstl is nonzero
    _con_y_tech_instl(model, techs)
    # [CON] Enforce the minimal unit capacity during installation
    _con_tech_unit_cap_min(model, techs)
    # [CON] Enforce minimal and maximal capacity
    _con_tech_cap_minmax(model, techs)
    # [CON] Limit installation to allowed tuples
    _con_tech_instl_allowed(model, stages, techs)
    # [CON] Force capacity of coupled techs to the predefined
    #       fraction of the main tech's capacity
    _con_tech_coupled_cap(model, techs)


def _build_cost(model: Model, stages: Stages, techs: Techs) -> None:
    # [VAR] CAPEX cost
    setattr(model, VAR_TECHCOSTCAPEX, Var(getattr(model, SET_TECHTUPLE), domain=Reals))
    # [CON] CAPEX cost
    _con_tech_cost_capex(model, stages, techs)
    # [VAR] OPEX (operation & maintenance) cost from capacity
    setattr(
        model, VAR_TECHCOSTOPEXCAP, Var(getattr(model, SET_TECHTUPLE), domain=Reals)
    )
    # [CON] OPEX cost from capacity
    _con_tech_cost_opex_cap(model, techs)
    # [VAR] Total cost
    setattr(model, VAR_TECHCOSTTOTAL, Var(domain=Reals))
    # [CON] Total cost
    _con_tech_cost_total(model)


def _build_co2(model: Model, stages: Stages, techs: Techs) -> None:
    # [VAR] CO2 emissions from tech installation
    setattr(model, VAR_TECHCO2INSTL, Var(getattr(model, SET_TECHTUPLE), domain=Reals))
    # [CON] CO2 emissions from tech installation
    _con_tech_co2_instl(model, stages, techs)
    # [VAR] Total CO2 emissions from techs
    setattr(model, VAR_TECHCO2TOTAL, Var(getattr(model, SET_STAGE), domain=Reals))
    # [CON] Total CO2 emissions from techs
    _con_tech_co2_total(model)


# ------------------ #
# Constraint methods #
# ------------------ #
def _con_tech_cap(model: Model, stages: Stages, techs: Techs) -> None:
    def __rule_tech_cap(model, s, h, x):
        # Parameters
        current_year = stages.get_start_year(StageId(s))
        tech_lifetime = techs.get_lifetime(TechId(x))
        age_init = techs.get_age_init(HubId(h), TechId(x))
        cap_init = techs.get_cap_init(HubId(h), TechId(x))
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


def _con_y_tech_instl(model: Model, techs: Techs) -> None:
    def __rule_y_tech_instl(model, s, h, x):
        # BigM parameter for tech capacity
        big_m = getattr(model, PAR_BIGMGENERIC)
        cap_max = techs.get_cap_max(StageId(s), HubId(h), TechId(x))
        if cap_max < float("inf"):
            big_m = cap_max + common.EPS_BIGM
        else:
            logging.log_file_warning(
                f"cap_max[{s}, {h}, {x}] not available to calculate a big-M "
                "value for tech capacity. Using generic big-M "
                f"value {getattr(model, PAR_BIGMGENERIC).value} based on "
                "demands instead",
                module=LOG_MODULE_STR,
            )
        # Set constraint
        return (
            getattr(model, VAR_TECHCAPINSTL)[s, h, x]
            <= big_m * getattr(model, VAR_YTECHCAPINSTL)[s, h, x]
        )

    setattr(
        model,
        CON_YTECHINSTL,
        Constraint(getattr(model, SET_TECHTUPLE), rule=__rule_y_tech_instl),
    )


def _con_tech_unit_cap_min(model: Model, techs: Techs) -> None:
    def __rule_tech_unit_cap_min(model, s, h, x):
        unit_cap_min = techs.get_unit_cap_min(StageId(s), TechId(x))
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


def _con_tech_cap_minmax(model: Model, techs: Techs) -> None:
    def __rule_tech_cap_min(model, s, h, x):
        cap_min = techs.get_cap_min(StageId(s), HubId(h), TechId(x))
        if cap_min < common.EPS_ZEROCHECK:
            return Constraint.Skip
        return getattr(model, VAR_TECHCAP)[s, h, x] >= cap_min

    def __rule_tech_cap_max(model, s, h, x):
        cap_max = techs.get_cap_max(StageId(s), HubId(h), TechId(x))
        if cap_max == float("inf"):
            return Constraint.Skip
        return getattr(model, VAR_TECHCAP)[s, h, x] <= cap_max

    setattr(
        model,
        CON_TECHCAPMIN,
        Constraint(getattr(model, SET_TECHTUPLE), rule=__rule_tech_cap_min),
    )
    setattr(
        model,
        CON_TECHCAPMAX,
        Constraint(getattr(model, SET_TECHTUPLE), rule=__rule_tech_cap_max),
    )


def _con_tech_instl_allowed(model: Model, stages: Stages, techs: Techs) -> None:
    def __rule_tech_instl_allowed(model, s, h, x):
        # Get parameters
        stage_year = stages.get_start_year(StageId(s))
        last_instl_year = techs.get_last_instl_year(HubId(h), TechId(x))
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


def _con_tech_coupled_cap(model: Model, techs: Techs) -> None:
    def __rule_tech_coupled_cap(model, s, h, x):
        # Only define constraint for sub techs
        if TechId(x) not in techs.coupled_sub_techs:
            return Constraint.Skip
        # Parameters
        x_main = techs.get_coupled_main_tech(TechId(x)).key
        cap_factor = techs.get_coupled_cap_factor(TechId(x))
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


def _con_tech_cost_capex(model: Model, stages: Stages, techs: Techs) -> None:
    def __rule_tech_cost_capex(model, s, h, x):
        # Parameters
        current_year = stages.get_start_year(StageId(s))
        interest_rate = techs.get_interest_rate(TechId(x))
        tech_lifetime = techs.get_lifetime(TechId(x))
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
            capex_per_cap = techs.get_capex_per_cap(StageId(s_instl), TechId(x))
            one_time_capex = techs.get_one_time_capex(StageId(s_instl), TechId(x))
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


def _con_tech_cost_opex_cap(model: Model, techs: Techs) -> None:
    def __rule_tech_cost_opex_cap(model, s, h, x):
        # Parameters
        opex_per_cap = techs.get_opex_per_cap(StageId(s), TechId(x))
        one_time_opex = techs.get_one_time_opex(StageId(s), TechId(x))
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


def _con_tech_co2_instl(model: Model, stages: Stages, techs: Techs) -> None:
    def __rule_tech_co2_instl(model, s, h, x):
        # Parameters
        current_year = stages.get_start_year(StageId(s))
        tech_lifetime = techs.get_lifetime(TechId(x))
        co2_per_cap = techs.get_co2_per_cap(StageId(s), TechId(x))
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
