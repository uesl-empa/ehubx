"""Heatpump technology submodel"""

from datetime import datetime

from pyomo.core import Constraint, Model, NonNegativeReals, Set, Var

from ehubx.core import common, logging
from ehubx.data.hp_tech_data import HeatpumpTechs
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.time_data import TimeId, Times
from ehubx.model.demand_model import PAR_BIGMGENERIC
from ehubx.model.ec_model import SET_EC
from ehubx.model.tech_model import SET_TECHTUPLE, VAR_TECHCAP, VAR_YTECHUSED
from ehubx.model.times_model import SET_TIME


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/hp_tech"
"""String identifying the heat pump technology model for logging purposes"""

SET_HPTECHTUPLE: str = "S_HpTechTuple"
"""Name of set for all heat pump tech tuples (stage, hub, ec)"""

SET_HPTECHIN: str = "S_HpTechIn"
"""Name of set for all input tuples for heat pump techs"""

SET_HPTECHOUT: str = "S_HpTechOut"
"""Name of set for all output tuples for heat pump techs"""

VAR_HPTECHIN: str = "V_HpTechIn"
"""Name of variable for heat pump tech inputs"""

VAR_HPTECHOUT: str = "V_HpTechOut"
"""Name of variable for heat pump tech outputs"""

VAR_HPTECHELECHT: str = "V_HpTechElecHt"
"""Name of variable for heat pump tech electrity power consumed in heating
mode"""

VAR_HPTECHELECCO: str = "V_HpTechElecCo"
"""Name of variable for heat pump tech electrity power consumed in cooling
mode"""

CON_HPTECHTOTALELEC: str = "C_HpTechTotalElec"
"""Name of constraint for total heat pump tech electrity consumption (sum of
heating and cooling consumptions)"""

CON_HPTECHPOWBALHT: str = "C_HpTechPowBalHt"
"""Name of constraint for heat pump power balance in heating mode"""

CON_HPTECHPOWBALCO: str = "C_HpTechPowBalCo"
"""Name of constraint for heat pump power balance in cooling mode"""

CON_HPTECHCOPHT: str = "C_HpTechCopHt"
"""Name of constraint for respecting the heat pump COP in heating mode"""

CON_HPTECHCOPCO: str = "C_HpTechCopCo"
"""Name of constraint for respecting the heat pump COP in cooling mode"""

CON_HPTECHCAP: str = "C_HpTechCap"
"""Name of constraint respecting the tech capacity for heat pumps"""

CON_HPTECHUSED: str = "C_HpTechUsed"
"""Name of constraint determing tech usage of heat pumps"""


def build(model: Model, techs: Techs, hp_techs: HeatpumpTechs, times: Times) -> None:
    """
    Builds the heatpump technology submodel. For a mathematical description
    in thorough detail, please refer to the section 'Heat pump model' in the
    documentation.

    :param model: Pyomo model
    :type model: Model
    :param techs: Technology data object
    :type techs: Techs
    :param hp_techs: Heatpump technology data object
    :type hp_techs: HeatpumpTechs
    :param times: Time data object
    :type times: Times
    """
    # Start measuring build time
    start = datetime.now()
    # Build
    _build_base(model, techs, hp_techs, times)
    # Log
    elapsed = datetime.now() - start
    logging.log_file(
        f"Built heat pump tech module. Elapsed time: {int(elapsed.total_seconds())}s",
        module=LOG_MODULE_STR,
    )


def _build_base(
    model: Model, techs: Techs, hp_techs: HeatpumpTechs, times: Times
) -> None:
    # [SET] Heat pump tech tuples
    setattr(
        model,
        SET_HPTECHTUPLE,
        Set(
            within=getattr(model, SET_TECHTUPLE),
            initialize=[
                (s, h, x)
                for (s, h, x) in getattr(model, SET_TECHTUPLE)
                if TechId(x) in hp_techs.ids
            ],
        ),
    )
    # [SET] Tuples of heat pump tech tuples and their input ecs
    setattr(
        model,
        SET_HPTECHIN,
        Set(
            within=(getattr(model, SET_HPTECHTUPLE) * getattr(model, SET_EC)),
            initialize=[
                (s, h, x, e.key)
                for (s, h, x) in getattr(model, SET_HPTECHTUPLE)
                for e in [
                    hp_techs.get_ec_el(TechId(x)),
                    hp_techs.get_ec_ht_in(TechId(x)),
                    hp_techs.get_ec_co_in(TechId(x)),
                ]
            ],
        ),
    )
    # [SET] Tuples of heat pump tech tuples and their output ecs
    setattr(
        model,
        SET_HPTECHOUT,
        Set(
            within=(getattr(model, SET_HPTECHTUPLE) * getattr(model, SET_EC)),
            initialize=[
                (s, h, x, e.key)
                for (s, h, x) in getattr(model, SET_HPTECHTUPLE)
                for e in [
                    hp_techs.get_ec_ht_out(TechId(x)),
                    hp_techs.get_ec_co_out(TechId(x)),
                ]
            ],
        ),
    )
    # [VAR] Heat pump input
    setattr(
        model,
        VAR_HPTECHIN,
        Var(
            getattr(model, SET_HPTECHIN),
            getattr(model, SET_TIME),
            domain=NonNegativeReals,
        ),
    )
    # [VAR] Heat pump output
    setattr(
        model,
        VAR_HPTECHOUT,
        Var(
            getattr(model, SET_HPTECHOUT),
            getattr(model, SET_TIME),
            domain=NonNegativeReals,
        ),
    )
    # [VAR] Separate electricity consumption variables for heating/cooling
    setattr(
        model,
        VAR_HPTECHELECHT,
        Var(
            getattr(model, SET_HPTECHTUPLE) * getattr(model, SET_TIME),
            domain=NonNegativeReals,
        ),
    )
    setattr(
        model,
        VAR_HPTECHELECCO,
        Var(
            getattr(model, SET_HPTECHTUPLE) * getattr(model, SET_TIME),
            domain=NonNegativeReals,
        ),
    )
    # [CON] Total electricity consumption from heating and cooling modes
    _con_hp_tech_total_elec(model, hp_techs)
    # [CON] Energy balance equations (evaporator power plus electricity
    #       consumption (from compressor) equals condenser power)
    _con_hp_tech_pow_bal_ht(model, hp_techs)
    _con_hp_tech_pow_bal_co(model, hp_techs)
    # [CON] COPs linking condenser power output to electricity consumption
    _con_hp_tech_cop(model, hp_techs, times)
    # [CON] Tech usage (monitored over summed-up condenser power)
    _con_hp_tech_used(model, techs, hp_techs, times)
    # [CON] Respect heat pump tech capacity (pertains to condenser power)
    _con_hp_tech_cap(model, hp_techs)


def _con_hp_tech_total_elec(model: Model, hp_techs: HeatpumpTechs) -> None:
    def __rule_hp_tech_total_elec(model, s, h, x, t):
        # Get parameter
        ec_el = hp_techs.get_ec_el(TechId(x))
        # Calculate total electricity consumption
        total_elec = (
            getattr(model, VAR_HPTECHELECHT)[s, h, x, t]
            + getattr(model, VAR_HPTECHELECCO)[s, h, x, t]
        )
        # Set constraint
        return getattr(model, VAR_HPTECHIN)[s, h, x, ec_el.key, t] == total_elec

    setattr(
        model,
        CON_HPTECHTOTALELEC,
        Constraint(
            getattr(model, SET_HPTECHTUPLE),
            getattr(model, SET_TIME),
            rule=__rule_hp_tech_total_elec,
        ),
    )


def _con_hp_tech_pow_bal_ht(model: Model, hp_techs: HeatpumpTechs) -> None:
    def __rule_hp_tech_pow_bal_ht(model, s, h, x, t):
        # Get parameters
        ec_ht_in = hp_techs.get_ec_ht_in(TechId(x))
        ec_ht_out = hp_techs.get_ec_ht_out(TechId(x))
        # Get component powers for heating mode
        pow_evap = getattr(model, VAR_HPTECHIN)[s, h, x, ec_ht_in.key, t]
        pow_cond = getattr(model, VAR_HPTECHOUT)[s, h, x, ec_ht_out.key, t]
        pow_elec = getattr(model, VAR_HPTECHELECHT)[s, h, x, t]
        # Set constraint
        return pow_evap + pow_elec == pow_cond

    setattr(
        model,
        CON_HPTECHPOWBALHT,
        Constraint(
            getattr(model, SET_HPTECHTUPLE),
            getattr(model, SET_TIME),
            rule=__rule_hp_tech_pow_bal_ht,
        ),
    )


def _con_hp_tech_pow_bal_co(model: Model, hp_techs: HeatpumpTechs) -> None:
    def __rule_hp_tech_pow_bal_co(model, s, h, x, t):
        # Get parameters
        ec_co_in = hp_techs.get_ec_co_in(TechId(x))
        ec_co_out = hp_techs.get_ec_co_out(TechId(x))
        # Get component powers for cooling mode
        pow_evap = getattr(model, VAR_HPTECHOUT)[s, h, x, ec_co_out.key, t]
        pow_cond = getattr(model, VAR_HPTECHIN)[s, h, x, ec_co_in.key, t]
        pow_elec = getattr(model, VAR_HPTECHELECCO)[s, h, x, t]
        # Set constraint
        return pow_evap + pow_elec == pow_cond

    setattr(
        model,
        CON_HPTECHPOWBALCO,
        Constraint(
            getattr(model, SET_HPTECHTUPLE),
            getattr(model, SET_TIME),
            rule=__rule_hp_tech_pow_bal_co,
        ),
    )


def _con_hp_tech_cop(model: Model, hp_techs: HeatpumpTechs, times: Times) -> None:
    # Precompute COP for efficiency
    cops = {
        (s, h, x): hp_techs.get_cop(StageId(s), HubId(h), TechId(x), times)
        for (s, h, x) in getattr(model, SET_HPTECHTUPLE)
    }

    def __rule_hp_tech_cop_ht(model, s, h, x, t):
        # Get parameters
        cop = cops[s, h, x].get_value(TimeId(t))
        ec_ht_out = hp_techs.get_ec_ht_out(TechId(x))
        # Get component powers for cooling mode
        pow_cond = getattr(model, VAR_HPTECHOUT)[s, h, x, ec_ht_out.key, t]
        pow_elec = getattr(model, VAR_HPTECHELECHT)[s, h, x, t]
        # Set constraint
        return pow_cond == cop * pow_elec

    def __rule_hp_tech_cop_co(model, s, h, x, t):
        # Get parameters
        cop = cops[s, h, x].get_value(TimeId(t))
        ec_co_in = hp_techs.get_ec_co_in(TechId(x))
        # Get component powers for cooling mode
        pow_cond = getattr(model, VAR_HPTECHIN)[s, h, x, ec_co_in.key, t]
        pow_elec = getattr(model, VAR_HPTECHELECCO)[s, h, x, t]
        # Set constraint
        return pow_cond == cop * pow_elec

    setattr(
        model,
        CON_HPTECHCOPHT,
        Constraint(
            getattr(model, SET_HPTECHTUPLE),
            getattr(model, SET_TIME),
            rule=__rule_hp_tech_cop_ht,
        ),
    )
    setattr(
        model,
        CON_HPTECHCOPCO,
        Constraint(
            getattr(model, SET_HPTECHTUPLE),
            getattr(model, SET_TIME),
            rule=__rule_hp_tech_cop_co,
        ),
    )


def _con_hp_tech_cap(model: Model, hp_techs: HeatpumpTechs) -> None:
    def __rule_hp_tech_cap(model, s, h, x, t):
        # Get parameters
        ec_ht_out = hp_techs.get_ec_ht_out(TechId(x))
        ec_co_in = hp_techs.get_ec_co_in(TechId(x))
        # Get condenser outputs
        pow_cond = (
            getattr(model, VAR_HPTECHOUT)[s, h, x, ec_ht_out.key, t]
            + getattr(model, VAR_HPTECHIN)[s, h, x, ec_co_in.key, t]
        )
        # Set constraint
        return pow_cond <= getattr(model, VAR_TECHCAP)[s, h, x]

    setattr(
        model,
        CON_HPTECHCAP,
        Constraint(
            getattr(model, SET_HPTECHTUPLE),
            getattr(model, SET_TIME),
            rule=__rule_hp_tech_cap,
        ),
    )


def _con_hp_tech_used(
    model: Model, techs: Techs, hp_techs: HeatpumpTechs, times: Times
) -> None:
    # Get length of full time horizon
    num_horizon_ts = times.num_horizon_ts

    def __rule_hp_tech_used(model, s, h, x):
        # Get parameters
        ec_ht_out = hp_techs.get_ec_ht_out(TechId(x))
        ec_co_in = hp_techs.get_ec_co_in(TechId(x))
        cap_max = techs.get_cap_max(StageId(s), HubId(h), TechId(x))

        # Calculate big_m for summed-up output
        if cap_max < float("inf"):
            big_m = common.EPS_BIGM + num_horizon_ts * cap_max
        else:
            big_m = getattr(model, PAR_BIGMGENERIC) * num_horizon_ts
            logging.log_file_warning(
                f"cap_max[{s}, {h}, {x}] is not available to calculate a "
                "big-M value for summed-up output. Using generic big-M value "
                f"{getattr(model, PAR_BIGMGENERIC).value} based on demands "
                "instead",
                module=LOG_MODULE_STR,
            )
        # Calculate summed-up output
        out_sum = sum(
            (
                times.get_weight(StageId(s), TimeId(t))
                * (
                    getattr(model, VAR_HPTECHOUT)[s, h, x, ec_ht_out.key, t]
                    + getattr(model, VAR_HPTECHIN)[s, h, x, ec_co_in.key, t]
                )
            )
            for t in getattr(model, SET_TIME)
        )
        # Set constraint
        return out_sum <= big_m * getattr(model, VAR_YTECHUSED)[s, h, x]

    setattr(
        model,
        CON_HPTECHUSED,
        Constraint(getattr(model, SET_HPTECHTUPLE), rule=__rule_hp_tech_used),
    )
