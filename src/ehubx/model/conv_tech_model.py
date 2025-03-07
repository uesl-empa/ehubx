"""Conversion technology submodel"""

from datetime import datetime

from pyomo.core import Constraint, Model, NonNegativeReals, Set, Var

from ehubx.core import common, logging
from ehubx.data.conv_tech_data import ConversionTechs
from ehubx.data.ec_data import EcId
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.time_data import TimeId, Times
from ehubx.model.demand_model import PAR_BIGMGENERIC
from ehubx.model.ec_model import SET_EC
from ehubx.model.tech_model import SET_TECHTUPLE, VAR_TECHCAP, VAR_YTECHUSED
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

CON_CONVTECHCOSTTOTAL: str = "C_ConvTechCostTotal"
"""Name of constraint calculation the total conversion costs (equals OPEX for "
conversion outputs)"""


def build(
    model: Model, techs: Techs, conv_techs: ConversionTechs, times: Times
) -> None:
    """
    Builds the conversion technology submodel. For a mathematical description
    in thorough detail, please refer to the section 'Conversion model' in the
    documentation.

    :param model: Pyomo model
    :type model: Model
    :param techs: Technology data object
    :type techs: Techs
    :param conv_techs: Conversion technology data object
    :type conv_techs: ConversionTechs
    :param times: Time data object
    :type times: Times
    """
    # Start measuring build time
    start = datetime.now()
    # Build
    _build_base(model, techs, conv_techs, times)
    _build_cost(model, conv_techs, times)
    # Log
    elapsed = datetime.now() - start
    logging.log_file(
        f"Built conversion tech module. Elapsed time: {int(elapsed.total_seconds())}s",
        module=LOG_MODULE_STR,
    )


def _build_base(
    model: Model, techs: Techs, conv_techs: ConversionTechs, times: Times
) -> None:
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
    # [CON] Input composition
    _con_conv_tech_in_part(model, conv_techs)
    # [CON] Output efficiency
    _con_conv_tech_out_eff(model, conv_techs)
    # [CON] Tech usage (monitored over summed-up output of main output EC)
    _con_conv_tech_used(model, techs, conv_techs, times)
    # [CON] Respect conversion tech capacity (pertains to main output) and
    #       availability for the system output
    _con_conv_tech_cap_and_availability(model, conv_techs)
    # [CON] Enforce minima and maxima for up outputs
    _con_conv_tech_out_sum_minmax(model, conv_techs, times)


def _build_cost(model: Model, conv_techs: ConversionTechs, times: Times) -> None:
    # [VAR] OPEX (operation & maintenance) cost from conversion output
    setattr(
        model,
        VAR_CONVTECHCOSTOPEXOUT,
        Var(getattr(model, SET_CONVTECHTUPLE), domain=NonNegativeReals),
    )
    # [CON] OPEX (operation & maintenance) cost from conversion output
    _con_conv_tech_cost_opex_out(model, conv_techs, times)
    # [VAR] Total cost
    setattr(model, VAR_CONVTECHCOSTTOTAL, Var(domain=NonNegativeReals))
    # [OBJ] Total cost
    _con_conv_tech_cost_total(model)


def _con_conv_tech_in_part(model: Model, conv_techs: ConversionTechs) -> None:
    def __rule_conv_tech_in_part(model, s, h, x, e, t):
        # Get parameter
        in_part = conv_techs.get_in_part(StageId(s), TechId(x), EcId(e))
        # Calculate total input
        in_total = sum(
            getattr(model, VAR_CONVTECHIN)[s, h, x, e_.key, t]
            for e_ in conv_techs.get_in_ecs(TechId(x))
        )
        # Calculate total in_parts
        in_part_total = sum(
            conv_techs.get_in_part(StageId(s), TechId(x), e_)
            for e_ in conv_techs.get_in_ecs(TechId(x))
        )
        # Set constraint
        return getattr(model, VAR_CONVTECHIN)[s, h, x, e, t] == (
            in_part * in_total / in_part_total
        )

    setattr(
        model,
        CON_CONVTECHINPART,
        Constraint(
            getattr(model, SET_CONVTECHIN),
            getattr(model, SET_TIME),
            rule=__rule_conv_tech_in_part,
        ),
    )


def _con_conv_tech_out_eff(model: Model, conv_techs: ConversionTechs) -> None:
    def __rule_conv_tech_out_eff(model, s, h, x, e, t):
        # Get parameters
        in_ec_main = conv_techs.get_in_ec_main(TechId(x))
        efficiency = conv_techs.get_out_eff(StageId(s), TechId(x), EcId(e)).get_value(
            TimeId(t)
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


def _con_conv_tech_used(
    model: Model, techs: Techs, conv_techs: ConversionTechs, times: Times
) -> None:
    # Get length of full time horizon
    num_horizon_ts = times.num_horizon_ts

    def __rule_conv_tech_used(model, s, h, x):
        # Get parameters
        out_ec_main = conv_techs.get_out_ec_main(TechId(x))
        out_sum_max = conv_techs.get_out_sum_max(StageId(s), HubId(h), TechId(x))
        cap_max = techs.get_cap_max(StageId(s), HubId(h), TechId(x))

        # Calculate big_m for summed-up output
        if out_sum_max < float("inf"):
            big_m = out_sum_max
        elif cap_max < float("inf"):
            big_m = common.EPS_BIGM + num_horizon_ts * cap_max
        else:
            big_m = getattr(model, PAR_BIGMGENERIC) * num_horizon_ts
            logging.log_file_warning(
                f"Neither out_sum_max[{s}, {h}, {x}] nor "
                f"cap_max[{s}, {h}, {x}] are available to calculate a big-M "
                "value for summed-up output. Using generic big-M value "
                f"{getattr(model, PAR_BIGMGENERIC).value} based on demands "
                "instead",
                module=LOG_MODULE_STR,
            )
        # Calculate summed-up output
        out_sum = sum(
            times.get_weight(StageId(s), TimeId(t))
            * getattr(model, VAR_CONVTECHOUT)[s, h, x, out_ec_main.key, t]
            for t in getattr(model, SET_TIME)
        )
        # Set constraint
        return out_sum <= big_m * getattr(model, VAR_YTECHUSED)[s, h, x]

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
        availability = conv_techs.get_availability(
            StageId(s), HubId(h), TechId(x)
        ).get_value(TimeId(t))
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
    model: Model, conv_techs: ConversionTechs, times: Times
) -> None:
    def __rule_conv_tech_out_sum_min(model, s, h, x):
        # Get parameters
        out_ec_main = conv_techs.get_out_ec_main(TechId(x))
        out_sum_min = conv_techs.get_out_sum_min(StageId(s), HubId(h), TechId(x))
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
        out_sum_max = conv_techs.get_out_sum_max(StageId(s), HubId(h), TechId(x))
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
    model: Model, conv_techs: ConversionTechs, times: Times
) -> None:
    def __rule_conv_tech_cost_opex_out(model, s, h, x):
        # Get parameters
        opex_per_energy = conv_techs.get_opex_per_energy(StageId(s), TechId(x))
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
