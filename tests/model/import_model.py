"""Import submodel"""

from datetime import datetime

from pyomo.core import Constraint, Model, NonNegativeReals, Reals, Set, Var

from ehubx.core import logging
from ehubx.data.ec_data import EcId
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId
from ehubx.data.time_data import TimeId
from ehubx.data.unit import CurrencyUnit, MassUnit, PowerUnit, TimeUnit
from ehubx.model.ec_model import SET_EC, get_ec_model_unit
from ehubx.model.hub_model import SET_HUB
from ehubx.model.stage_model import SET_STAGE
from ehubx.model.times_model import SET_TIME


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/import"
"""String identifying the import model for logging purposes"""

SET_IMPTUPLE: str = "S_ImpTuple"
"""Name of set of import tuples"""

VAR_IMP: str = "V_Imp"
"""Name of variable for imports"""

VAR_IMPCOST: str = "V_ImpCost"
"""Name of variable for import costs (per import tuple)"""

VAR_IMPCOSTTOTAL: str = "V_ImpCostTotal"
"""Name of variable for total import costs"""

VAR_IMPCO2: str = "V_ImpCo2"
"""Name of variable for import-related CO2 emissions (per import tuple)"""

VAR_IMPCO2TOTAL: str = "V_ImpCo2Total"
"""Name of variable for total import-related CO2 emissions"""

CON_IMPSUMMIN: str = "C_ImpSumMin"
"""Name of constraint respecting minimal value for summed-up imports"""

CON_IMPSUMMAX: str = "C_ImpSumMax"
"""Name of constraint respecting maximal value for summed-up imports"""

CON_IMPCOST: str = "C_ImpCost"
"""Name of constraint setting import costs (per import tuple)"""

CON_IMPCOSTTOTAL: str = "C_ImpCostTotal"
"""Name of constraint setting total import costs"""

CON_IMPCO2: str = "C_ImpCo2"
"""Name of constraint setting embodied CO2 emissions from imports (per import
tuple)"""

CON_IMPCO2TOTAL: str = "C_ImpCo2Total"
"""Name of constraint setting total embodied CO2 emissions from imports"""


def build(model: Model, system: EnergySystem) -> None:
    """
    Builds the import submodel. For a mathematical description in thorough
    detail, please refer to the section 'Import model' in the documentation.

    :param model: Pyomo model
    :type model: Model
    :param system: Energy system data
    :type system: EnergySystem
    """
    # Extract data from modules
    mass_unit = system.mass_unit
    power_unit = system.power_unit
    currency_unit = system.currency_unit
    # Start measuring build time
    start = datetime.now()
    # Build
    _build_base(model, system, mass_unit, power_unit)
    _build_cost(model, system, currency_unit, mass_unit, power_unit)
    _build_co2(model, system, mass_unit, power_unit)
    # Logging
    elapsed = datetime.now() - start
    logging.log_file(
        f"Built import module. Elapsed time: {int(elapsed.total_seconds())}s",
        module=LOG_MODULE_STR,
    )


def _build_base(
    model: Model,
    system: EnergySystem,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
) -> None:
    imports = system.imports
    ecs = system.ecs
    # [SET] Import tuples
    setattr(
        model,
        SET_IMPTUPLE,
        Set(
            within=(
                getattr(model, SET_STAGE)
                * getattr(model, SET_HUB)
                * getattr(model, SET_EC)
            ),
            initialize=[(s.key, h.key, e.key) for (s, h, e) in imports.tuples],
        ),
    )

    # [VAR] Import
    def _imp_bounds(model, s, h, e, t):
        imp_min: float = 0.0
        imp_max: float
        imp_unit = (
            get_ec_model_unit(ecs.get_unit(EcId(e)), mass_unit, power_unit) / TimeUnit.H
        )
        imp_min_ts = imports.get_min(StageId(s), HubId(h), EcId(e))
        imp_max_ts = imports.get_max(StageId(s), HubId(h), EcId(e))
        if imp_min_ts.has_values or imp_min_ts.def_value.is_finite:
            imp_min = imp_min_ts.get_value(TimeId(t)).to_float(unit=imp_unit)
        if imp_max_ts.has_values or imp_max_ts.def_value.is_finite:
            imp_max = imp_max_ts.get_value(TimeId(t)).to_float(unit=imp_unit)
        else:
            imp_max = system.get_heur_limit_max_in(
                StageId(s), HubId(h), EcId(e)
            ).to_float(unit=imp_unit)
        return (imp_min, imp_max)

    setattr(
        model,
        VAR_IMP,
        Var(
            getattr(model, SET_IMPTUPLE),
            getattr(model, SET_TIME),
            domain=NonNegativeReals,
            bounds=_imp_bounds,
        ),
    )
    # [CON] Enforce minima and maxima for summed-up imports
    _con_imp_sum_minmax(model, system, mass_unit, power_unit)


def _build_cost(
    model: Model,
    system: EnergySystem,
    currency_unit: CurrencyUnit,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
) -> None:
    # [VAR] Import cost
    setattr(model, VAR_IMPCOST, Var(getattr(model, SET_IMPTUPLE), domain=Reals))
    # [CON] Import cost
    _con_imp_cost(model, system, currency_unit, mass_unit, power_unit)
    # [VAR] Total import cost
    setattr(model, VAR_IMPCOSTTOTAL, Var(domain=Reals))
    # [CON] Total import cost
    _con_imp_cost_total(model)


def _build_co2(
    model: Model,
    system: EnergySystem,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
) -> None:
    # [VAR] CO2 emissions from imports
    setattr(
        model, VAR_IMPCO2, Var(getattr(model, SET_IMPTUPLE), domain=NonNegativeReals)
    )
    # [CON] Set CO2 emissions from imports
    _con_imp_co2(model, system, mass_unit, power_unit)
    # [VAR] Total CO2 emissions from imports
    setattr(
        model, VAR_IMPCO2TOTAL, Var(getattr(model, SET_STAGE), domain=NonNegativeReals)
    )
    # [CON] Total CO2 emissions from imports
    _con_imp_co2_total(model)


def _con_imp_sum_minmax(
    model: Model,
    system: EnergySystem,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
) -> None:
    ecs = system.ecs
    imports = system.imports
    times = system.times

    def __rule_imp_sum_min(model, s, h, e):
        # Get minimum for summed-up import
        unit = get_ec_model_unit(ecs.get_unit(EcId(e)), mass_unit, power_unit)
        sum_min = imports.get_sum_min(StageId(s), HubId(h), EcId(e), ecs)
        if not sum_min.is_positive:
            return Constraint.Skip
        # Calculate summed-up import
        imp_sum = sum(
            times.get_weight(StageId(s), TimeId(t))
            * getattr(model, VAR_IMP)[s, h, e, t]
            for t in getattr(model, SET_TIME)
        )
        # Set constraint
        return imp_sum >= sum_min.to_float(unit=unit)

    def __rule_imp_sum_max(model, s, h, e):
        # Get minimum for summed-up import
        unit = get_ec_model_unit(ecs.get_unit(EcId(e)), mass_unit, power_unit)
        sum_max = imports.get_sum_max(StageId(s), HubId(h), EcId(e), ecs)
        if not sum_max.is_finite:
            return Constraint.Skip
        # Calculate summed-up import
        imp_sum = sum(
            times.get_weight(StageId(s), TimeId(t))
            * getattr(model, VAR_IMP)[s, h, e, t]
            for t in getattr(model, SET_TIME)
        )
        # Set constraint
        return imp_sum <= sum_max.to_float(unit=unit)

    setattr(
        model,
        CON_IMPSUMMIN,
        Constraint(getattr(model, SET_IMPTUPLE), rule=__rule_imp_sum_min),
    )
    setattr(
        model,
        CON_IMPSUMMAX,
        Constraint(getattr(model, SET_IMPTUPLE), rule=__rule_imp_sum_max),
    )


def _con_imp_cost(
    model: Model,
    system: EnergySystem,
    currency_unit: CurrencyUnit,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
) -> None:
    imports = system.imports
    ecs = system.ecs
    times = system.times

    def __rule_imp_cost(model, s, h, e):
        # Get parameters
        price = imports.get_price(StageId(s), HubId(h), EcId(e))
        unit = currency_unit / get_ec_model_unit(
            ecs.get_unit(EcId(e)), mass_unit, power_unit
        )
        # Calculate cost
        cost = sum(
            price.get_value(TimeId(t)).to_float(unit=unit)
            * times.get_weight(StageId(s), TimeId(t))
            * getattr(model, VAR_IMP)[s, h, e, t]
            for t in getattr(model, SET_TIME)
        )
        # Set constraint
        return getattr(model, VAR_IMPCOST)[s, h, e] == cost

    setattr(
        model,
        CON_IMPCOST,
        Constraint(getattr(model, SET_IMPTUPLE), rule=__rule_imp_cost),
    )


def _con_imp_cost_total(model: Model) -> None:
    def __rule_imp_cost_total(model):
        # Calculate the total import cost
        imp_cost_total = sum(
            getattr(model, VAR_IMPCOST)[s, h, e]
            for (s, h, e) in getattr(model, SET_IMPTUPLE)
        )
        # Set the constraint
        return getattr(model, VAR_IMPCOSTTOTAL) == imp_cost_total

    setattr(model, CON_IMPCOSTTOTAL, Constraint(rule=__rule_imp_cost_total))


def _con_imp_co2(
    model: Model,
    system: EnergySystem,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
) -> None:
    imports = system.imports
    ecs = system.ecs
    times = system.times

    def __rule_imp_co2(model, s, h, e):
        # Get parameters
        co2 = imports.get_co2(StageId(s), HubId(h), EcId(e))
        unit = mass_unit / get_ec_model_unit(
            ecs.get_unit(EcId(e)), mass_unit, power_unit
        )
        # Calculate emissions
        imp_co2 = sum(
            co2.get_value(TimeId(t)).to_float(unit=unit)
            * times.get_weight(StageId(s), TimeId(t))
            * getattr(model, VAR_IMP)[s, h, e, t]
            for t in getattr(model, SET_TIME)
        )
        # Set constraint
        return getattr(model, VAR_IMPCO2)[s, h, e] == imp_co2

    setattr(
        model, CON_IMPCO2, Constraint(getattr(model, SET_IMPTUPLE), rule=__rule_imp_co2)
    )


def _con_imp_co2_total(model: Model) -> None:
    def __rule_imp_co2_total(model, s):
        # Calculate the total import CO2
        imp_co2_total = sum(
            getattr(model, VAR_IMPCO2)[s2, h, e]
            for (s2, h, e) in getattr(model, SET_IMPTUPLE)
            if s2 == s
        )
        # Set the constraint
        return getattr(model, VAR_IMPCO2TOTAL)[s] == imp_co2_total

    setattr(
        model,
        CON_IMPCO2TOTAL,
        Constraint(getattr(model, SET_STAGE), rule=__rule_imp_co2_total),
    )
