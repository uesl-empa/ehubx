"""Aquifer Thermal Energy Storage (ATES) technology submodel"""
from datetime import datetime
from pyomo.core import Constraint, Model, NonNegativeReals, Set, Var
from ehubx.core import logging
from ehubx.data.tech_data import TechId
from ehubx.data.ates_tech_data import AtesTechs
from ehubx.data.time_data import Times

# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/ates_tech"
"""String identifying the ATES technology model for logging purposes"""

SET_ATESTECHIN: str = "S_AtesTechIn"
"""Name of set for all input tuples for ATES techs"""

SET_ATESTECHOUT: str = "S_AtesTechOut"
"""Name of set for all output tuples for ATES techs"""

VAR_ATESTECHIN: str = "V_AtesTechIn"
"""Name of variable for ATES tech inputs"""

VAR_ATESTECHOUT: str = "V_AtesTechOut"
"""Name of variable for ATES tech outputs"""


def build(model: Model, times: Times) -> None:
    # Start measuring build time
    start = datetime.now()
    # Build
    _build(model, AtesTechs())
    # Log
    elapsed = datetime.now() - start
    logging.log_file(
        "Built ATES tech module. Elapsed time: "
        f"{int(elapsed.total_seconds())}s", module=LOG_MODULE_STR)


def _build(model: Model, ates_techs: AtesTechs) -> None:
    # [SET] ATES tech tuples
    model.S_AtesTechTuple = Set(within=model.S_TechTuple,
        initialize=[(s, h, x)
                    for (s, h, x) in model.S_TechTuple
                    if TechId(x) in ates_techs.ids])
    # [SET] Tuples of ATES tech tuples and their input ec (el)
    model.S_AtesTechIn = Set(within=model.S_AtesTechTuple * model.S_Ec,
        initialize=[(s, h, x, ates_techs.get_ec_el(TechId(x)).key)
                    for (s, h, x) in model.S_AtesTechTuple])
    # [SET] Tuples of ATES tech tuples and their output ecs (ht & co)
    model.S_AtesTechOut = Set(within=model.S_AtesTechTuple * model.S_Ec,
        initialize=[(s, h, x, e.key)
                    for (s, h, x) in model.S_AtesTechTuple
                    for e in [ates_techs.get_ec_ht(TechId(x)),
                              ates_techs.get_ec_co(TechId(x))]])
    # [VAR] ATES input (electricity)
    model.V_AtesTechIn = Var(model.S_AtesTechIn, model.S_Time,
                             domain=NonNegativeReals)
    # [VAR] ATES output (heating and cooling)
    model.V_AtesTechOut = Var(model.S_AtesTechOut, model.S_Time,
                              domain=NonNegativeReals)
    # [VAR] Separate electricitgy consumption variables for heating/cooling
    model.V_AtesTechElecHt = Var(model.S_AtesTechTuple * model.S_Time,
                                 domain=NonNegativeReals)
    model.V_AtesTechElecCo = Var(model.S_AtesTechTuple * model.S_Time,
                                 domain=NonNegativeReals)
    # [CON] Total electricity consumption from heating and cooling modes
    _con_ates_tech_total_elec(model, ates_techs)
    # [CON] COP (relation between output power and input electricity)
    _con_ates_tech_cop(model, ates_techs)


def _con_ates_tech_total_elec(model: Model, ates_techs: AtesTechs) -> None:

    def __rule_ates_tech_total_elec(model, s, h, x, t):
        # Get parameter
        ec_el = ates_techs.get_ec_el(TechId(x))
        # Calculate total electricity consumption
        total_elec = (model.V_AtesTechElecHt[s, h, x, t]
                      + model.V_AtesTechElecCo[s, h, x, t])
        # Set constraint
        return model.V_AtesTechIn[s, h, x, ec_el.key, t] == total_elec

    model.C_AtesTechTotalElec = Constraint(model.S_AtesTechTuple, model.S_Time,
                                           rule=__rule_ates_tech_total_elec)


def _con_ates_tech_cop(model: Model, ates_techs: AtesTechs) -> None:

    def __rule_ates_tech_cop_ht(model, s, h, x, t):
        # Get parameters
        ec_ht = ates_techs.get_ec_ht(TechId(x))
        cop_ht = 20  # TODO: Generalize
        # Calculate heating power from electricity
        pow_ht = cop_ht * model.V_AtesTechElecHt[s, h, x, t]
        # Set constraint
        return model.V_AtesTechOut[s, h, x, ec_ht.key, t] == pow_ht

    def __rule_ates_tech_cop_co(model, s, h, x, t):
        # Get parameters
        ec_co = ates_techs.get_ec_co(TechId(x))
        cop_co = 15  # TODO: Generalize
        # Calculate cooling power from electricity
        pow_co = cop_co * model.V_AtesTechElecCo[s, h, x, t]
        # Set constraint
        return model.V_AtesTechOut[s, h, x, ec_co.key, t] == pow_co

    model.C_AtesTechCopHt = Constraint(model.S_AtesTechTuple, model.S_Time,
                                       rule=__rule_ates_tech_cop_ht)
    model.C_AtesTechCopCo = Constraint(model.S_AtesTechTuple, model.S_Time,
                                       rule=__rule_ates_tech_cop_co)
