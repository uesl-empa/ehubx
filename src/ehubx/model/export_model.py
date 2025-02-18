"""Export submodel"""
from pyomo.core import Constraint, Model, NonNegativeReals, Set, Var
from datetime import datetime
from ehubx.core import logging
from ehubx.data.stage_data import StageId
from ehubx.data.hub_data import HubId
from ehubx.data.ec_data import EcId
from ehubx.data.export_data import Exports
from ehubx.data.time_data import Times, TimeId
from ehubx.model.stage_model import SET_STAGE
from ehubx.model.hub_model import SET_HUB
from ehubx.model.ec_model import SET_EC
from ehubx.model.times_model import SET_TIME

# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/export"
"""String identifying the export model for logging purposes"""

SET_EXPTUPLE: str = "S_ExpTuple"
"""Name of set of export tuples"""

VAR_EXP: str = "V_Exp"
"""Name of variable for exports"""

VAR_EXPPROFIT: str = "V_ExpProfit"
"""Name of variable for export profits (per export tuple)"""

VAR_EXPPROFITTOTAL: str = "V_ExpProfitTotal"
"""Name of variable for total export profits"""

VAR_EXPCO2: str = "V_ExpCo2"
"""Name of variable for export-related CO2 emission reductions (per export
tuple)"""

VAR_EXPCO2TOTAL: str = "V_ExpCo2Total"
"""Name of variable for total export-related CO2 emission reductions"""

CON_EXPMIN: str = "C_ExpMin"
"""Name of constraint respecting the export minimum"""

CON_EXPMAX: str = "C_ExpMax"
"""Name of constraint respecting the export maximum"""

CON_EXPSUMMIN: str = "C_ExpSumMin"
"""Name of constraint respecting the minimum for summed-up exports"""

CON_EXPSUMMAX: str = "C_ExpSumMax"
"""Name of constraint respecting the maximum for summed-up exports"""

CON_EXPPROFIT: str = "C_ExpProfit"
"""Name of constraint setting the export profits (per export tuple)"""

CON_EXPPROFITTOTAL: str = "C_ExpProfitTotal"
"""Name of constraint setting the total export profits"""

CON_EXPCO2: str = "C_ExpCo2"
"""Name of constraint setting the emission reductions from exports (per
export tuple)"""

CON_EXPCO2TOTAL: str = "C_ExpCo2Total"
"""Name of constraint setting the total emission reductions from exports"""


def build(model: Model, exports: Exports, times: Times) -> None:
    """
    Builds the export submodel. For a mathematical description in thorough
    detail, please refer to the section 'Export model' in the documentation.

    :param model: Pyomo model
    :type model: Model
    :param exports: Export data object
    :type exports: Exports
    :param times: Time data object
    :type times: Times
    """
    # Start measuring build time
    start = datetime.now()
    # Build
    _build_base(model, exports, times)
    _build_profit(model, exports, times)
    _build_co2(model, exports, times)
    # Logging
    elapsed = datetime.now() - start
    logging.log_file(
        "Built export module. Elapsed time: "
        f"{int(elapsed.total_seconds())}s", module=LOG_MODULE_STR)


def _build_base(model: Model, exports: Exports, times: Times) -> None:
    # [SET] Export tuples
    setattr(model, SET_EXPTUPLE,
            Set(within=(getattr(model, SET_STAGE)
                        * getattr(model, SET_HUB)
                        * getattr(model, SET_EC)),
                initialize=[(s.key, h.key, e.key)
                            for (s, h, e) in exports.tuples]))
    # [VAR] Export
    setattr(model, VAR_EXP,
            Var((getattr(model, SET_EXPTUPLE)
                 * getattr(model, SET_TIME)), domain=NonNegativeReals))
    # [CON] Enforce minimal and maximal exports
    _con_exp_minmax(model, exports)
    # [CON] Enforce minima and maxima for summed-up exports
    _con_exp_sum_minmax(model, exports, times)


def _build_profit(model: Model, exports: Exports, times: Times) -> None:
    # [VAR] Export profit
    setattr(model, VAR_EXPPROFIT,
            Var(getattr(model, SET_EXPTUPLE), domain=NonNegativeReals))
    # [CON] Export profit
    _con_exp_profit(model, exports, times)
    # [VAR] Total export profit
    setattr(model, VAR_EXPPROFITTOTAL,
            Var(domain=NonNegativeReals))
    # [CON] Total export profit
    _con_exp_profit_total(model)


def _build_co2(model: Model, exports: Exports, times: Times) -> None:
    # [VAR] CO2 emissions from exports
    setattr(model, VAR_EXPCO2,
            Var(getattr(model, SET_EXPTUPLE), domain=NonNegativeReals))
    # [CON] Set CO2 emissions for exports
    _con_exp_co2(model, exports, times)
    # [VAR] Total CO2 emissions from exports
    setattr(model, VAR_EXPCO2TOTAL,
            Var(getattr(model, SET_STAGE), domain=NonNegativeReals))
    # [CON] Total CO2 emissions from exports
    _con_exp_co2_total(model)


def _con_exp_minmax(model: Model, exports: Exports) -> None:

    def __rule_exp_min(model, s, h, e, t):
        exp_min = exports.get_min(StageId(s), HubId(h), EcId(e)
                                  ).get_value(TimeId(t))
        return getattr(model, VAR_EXP)[s, h, e, t] >= exp_min

    def __rule_exp_max(model, s, h, e, t):
        exp_max = exports.get_max(StageId(s), HubId(h), EcId(e)
                                  ).get_value(TimeId(t))
        return getattr(model, VAR_EXP)[s, h, e, t] <= exp_max

    setattr(model, CON_EXPMIN,
            Constraint(getattr(model, SET_EXPTUPLE),
                       getattr(model, SET_TIME),
                       rule=__rule_exp_min))
    setattr(model, CON_EXPMAX,
            Constraint(getattr(model, SET_EXPTUPLE),
                       getattr(model, SET_TIME),
                       rule=__rule_exp_max))


def _con_exp_sum_minmax(model: Model, exports: Exports, times: Times) -> None:

    def __rule_exp_sum_min(model, s, h, e):
        # Get minimum for summed-up export
        sum_min = exports.get_sum_min(StageId(s), HubId(h), EcId(e))
        # Calculate summed-up export
        exp_sum = sum(
            times.get_weight(StageId(s), TimeId(t))
            * getattr(model, VAR_EXP)[s, h, e, t]
            for t in getattr(model, SET_TIME))
        # Set constraint
        return exp_sum >= sum_min

    def __rule_exp_sum_max(model, s, h, e):
        # Get minimum for summed-up export
        sum_max = exports.get_sum_max(StageId(s), HubId(h), EcId(e))
        # Calculate summed-up export
        exp_sum = sum(
            times.get_weight(StageId(s), TimeId(t))
            * getattr(model, VAR_EXP)[s, h, e, t]
            for t in getattr(model, SET_TIME))
        # Set constraint
        return exp_sum <= sum_max

    setattr(model, CON_EXPSUMMIN,
            Constraint(getattr(model, SET_EXPTUPLE), rule=__rule_exp_sum_min))
    setattr(model, CON_EXPSUMMAX,
            Constraint(getattr(model, SET_EXPTUPLE), rule=__rule_exp_sum_max))


def _con_exp_profit(model: Model, exports: Exports, times: Times) -> None:

    def __rule_exp_profit(model, s, h, e):
        # Get parameters
        price = exports.get_price(StageId(s), HubId(h), EcId(e))
        # Calculate profit
        profit = sum(
            price.get_value(TimeId(t))
            * times.get_weight(StageId(s), TimeId(t))
            * getattr(model, VAR_EXP)[s, h, e, t]
            for t in getattr(model, SET_TIME))
        # Set constraint
        return getattr(model, VAR_EXPPROFIT)[s, h, e] == profit

    setattr(model, CON_EXPPROFIT,
            Constraint(getattr(model, SET_EXPTUPLE), rule=__rule_exp_profit))


def _con_exp_profit_total(model: Model) -> None:

    def __rule_exp_profit_total(model):
        # Calculate the total export profit
        exp_profit_total = sum(
            getattr(model, VAR_EXPPROFIT)[s, h, e]
            for (s, h, e) in getattr(model, SET_EXPTUPLE))
        # Set the constraint
        return getattr(model, VAR_EXPPROFITTOTAL) == exp_profit_total

    setattr(model, CON_EXPPROFITTOTAL,
            Constraint(rule=__rule_exp_profit_total))


def _con_exp_co2(model: Model, exports: Exports, times: Times) -> None:

    def __rule_exp_co2(model, s, h, e):
        # Get parameters
        co2 = exports.get_co2(StageId(s), HubId(h), EcId(e))
        # Calculate emissions
        exp_co2 = sum(
            co2.get_value(TimeId(t))
            * times.get_weight(StageId(s), TimeId(t))
            * getattr(model, VAR_EXP)[s, h, e, t]
            for t in getattr(model, SET_TIME))
        # Set constraint
        return getattr(model, VAR_EXPCO2)[s, h, e] == exp_co2

    setattr(model, CON_EXPCO2,
            Constraint(getattr(model, SET_EXPTUPLE), rule=__rule_exp_co2))


def _con_exp_co2_total(model: Model) -> None:

    def __rule_exp_co2_total(model, s):
        # Calculate the total export CO2
        exp_co2_total = sum(
            getattr(model, VAR_EXPCO2)[s2, h, e]
            for (s2, h, e) in getattr(model, SET_EXPTUPLE)
            if s2 == s)
        # Set the constraint
        return getattr(model, VAR_EXPCO2TOTAL)[s] == exp_co2_total

    setattr(model, CON_EXPCO2TOTAL,
            Constraint(getattr(model, SET_STAGE), rule=__rule_exp_co2_total))
