"""Aquifer Thermal Energy Storage (ATES) technology submodel"""

from datetime import datetime
from typing import Dict, Tuple

import numpy as np
from pyomo.core import Constraint, Model, NonNegativeReals, Set, Var

from ehubx.core import logging
from ehubx.data.ates_data import AtesData, AtesScheduleId
from ehubx.data.ates_tech_data import AtesTechs
from ehubx.data.ec_data import EcId
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.time_data import TimeId, Times
from ehubx.model.common import calculate_crf
from ehubx.model.ec_model import SET_EC
from ehubx.model.hub_model import SET_HUB
from ehubx.model.stage_model import SET_STAGE
from ehubx.model.tech_model import (
    CON_TECHCO2INSTL,
    CON_TECHCOSTCAPEX,
    CON_TECHCOSTOPEXCAP,
    SET_TECH,
    SET_TECHTUPLE,
    VAR_TECHCAP,
    VAR_TECHCAPINSTL,
    VAR_TECHCO2INSTL,
    VAR_TECHCOSTCAPEX,
    VAR_TECHCOSTOPEXCAP,
    VAR_YTECHCAPINSTL,
    VAR_YTECHUSED,
)
from ehubx.model.times_model import SET_TIME


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/ates_tech"
"""String identifying the ATES technology model for logging purposes"""

SET_ATESTECHTUPLE: str = "S_AtesTechTuple"
"""Name of set with ATES tech tuples"""

SET_ATESSCHEDULE: str = "S_AtesSchedule"
"""Name of set with ATES schedules"""

SET_ATESTECHTUPLESCHEDULE: str = "S_AtesTechTupleSchedule"
"""Name of set with ATES tech tuples and their schedules"""

SET_ATESTECHIN: str = "S_AtesTechIn"
"""Name of set for all input tuples for ATES techs"""

SET_ATESTECHOUT: str = "S_AtesTechOut"
"""Name of set for all output tuples for ATES techs"""

VAR_ATESTECHCAPSCHEDULE: str = "V_AtesTechCapSchedule"
"""Name of variable for ATES tech capacity assignment to schedule"""

VAR_ATESTECHELECSCHEDULE: str = "V_AtesTechElecSchedule"
"""Name of variable for ATES tech electricity input per schedule"""

VAR_ATESTECHHEATSCHEDULE: str = "V_AtesTechHeatSchedule"
"""Name of variable for ATES tech heating output per schedule"""

VAR_ATESTECHCOOLSCHEDULE: str = "V_AtesTechCoolSchedule"
"""Name of variable for ATES tech cooling output per schedule"""

VAR_ATESTECHIN: str = "V_AtesTechIn"
"""Name of variable for ATES tech inputs"""

VAR_ATESTECHOUT: str = "V_AtesTechOut"
"""Name of variable for ATES tech outputs"""

CON_ATESTECHCAPAVAILABLEAREA: str = "C_AtesTechCapAvailableArea"
"""Name of constraint limiting the total installed tech capacity for ATES
techs by the available ATES area"""

CON_ATESTECHCAPFROMSCHEDULES: str = "C_AtesTechCapFromSchedules"
"""Name of constraint composing the total tech capacity for ATES techs
from capacities across schedules"""

CON_ATESTECHELECPERHEATCOOL: str = "C_AtesTechElecPerHeatCool"
"""Name of constraint relating electricity consumption to heating and
cooling outputs"""

CON_ATESTECHHEATPHASES: str = "C_AtesTechHeatPhases"
"""Name of constraint forbidding heating output outside of W2C phases"""

CON_ATESTECHCOOLPHASES: str = "C_AtesTechCoolPhases"
"""Name of constraint forbidding cooling output outside of C2W phases"""

CON_ATESTECHINFROMSCHEDULES: str = "C_AtesTechInFromSchedules"
"""Name of constraint composing the total ATES tech input from schedules"""

CON_ATESTECHOUTFROMSCHEDULES: str = "C_AtesTechOutFromSchedules"
"""Name of constraint composing the total ATES tech output from schedules"""

CON_ATESTECHHEATCAP: str = "C_AtesTechHeatCap"
"""Name of constraint limiting heating output of ATES techs by capacity"""

CON_ATESTECHCOOLCAP: str = "C_AtesTechCoolCap"
"""Name of constraint limiting cooling output of ATES techs by capacity"""

CON_ATESTECHMAXHEATOVERCOOL: str = "C_AtesTechMaxHeatOverCool"
"""Name of constraint limiting maximal heating (W2C) output of ATES techs
relative to cooling (C2W) output"""

CON_ATESTECHMAXCOOLOVERHEAT: str = "C_AtesTechMaxCoolOverHeat"
"""Name of constraint limiting maximal cooling (C2W) output of ATES techs
relative to heating (W2C) output"""

CON_ATESTECHCOSTCAPEX: str = "C_AtesTechCostCapex"
"""Name of constraint setting CAPEX costs for ATES techs"""

CON_ATESTECHCOSTOPEXCAP: str = "C_AtesTechCostOpexCap"
"""Name of constraint setting OPEX costs for ATES techs"""

CON_ATESTECHCO2INSTL: str = "C_AtesTechCo2Instl"
"""Name of constraint setting CO2 emissions for ATES techs"""


def build(
    model: Model,
    stages: Stages,
    hubs: Hubs,
    techs: Techs,
    ates_techs: AtesTechs,
    ates_data: AtesData,
    times: Times,
) -> None:
    # Start measuring build time
    start = datetime.now()
    # Build
    _build_for_schedules(model, hubs, ates_techs, ates_data, times)
    _build_overall(model, ates_techs)
    _build_cost(model, stages, techs, ates_techs, ates_data, times)
    _build_emissions(model, stages, techs, ates_techs, ates_data, times)
    # Log
    elapsed = datetime.now() - start
    logging.log_file(
        f"Built ATES tech module. Elapsed time: {int(elapsed.total_seconds())}s",
        module=LOG_MODULE_STR,
    )


def _build_for_schedules(
    model: Model, hubs: Hubs, ates_techs: AtesTechs, ates_data: AtesData, times: Times
) -> None:
    # [SET] ATES tech tuples
    setattr(
        model,
        SET_ATESTECHTUPLE,
        Set(
            within=getattr(model, SET_TECHTUPLE),
            initialize=[
                (s, h, x)
                for (s, h, x) in getattr(model, SET_TECHTUPLE)
                if TechId(x) in ates_techs.ids
            ],
        ),
    )
    # [CON] Respect available ATES area for ATES tech capacities
    _con_ates_tech_cap_available_area(model, ates_data)
    # [SET] ATES schedules
    setattr(
        model,
        SET_ATESSCHEDULE,
        Set(
            initialize=list(
                {i.key for h in hubs.ids for i in ates_data.get_schedule_ids(h)}
            )
        ),
    )
    getattr(model, SET_ATESSCHEDULE)
    # [SET] ATES schedules and tech tuples with schedule
    setattr(
        model,
        SET_ATESTECHTUPLESCHEDULE,
        Set(
            within=(
                getattr(model, SET_STAGE)
                * getattr(model, SET_HUB)
                * getattr(model, SET_TECH)
                * getattr(model, SET_ATESSCHEDULE)
            )
        ),
    )
    for s, h, x in getattr(model, SET_ATESTECHTUPLE):
        for i in ates_data.get_schedule_ids(HubId(h)):
            getattr(model, SET_ATESTECHTUPLESCHEDULE).add((s, h, x, i.key))
    # [VAR] ATES tech capacity per schedule
    setattr(
        model,
        VAR_ATESTECHCAPSCHEDULE,
        Var(getattr(model, SET_ATESTECHTUPLESCHEDULE), domain=NonNegativeReals),
    )
    # [CON] ATES tech capacity across schedules
    _con_ates_tech_cap_from_schedules(model)
    # [VAR] ATES electricity input for each schedule
    setattr(
        model,
        VAR_ATESTECHELECSCHEDULE,
        Var(
            getattr(model, SET_ATESTECHTUPLESCHEDULE) * getattr(model, SET_TIME),
            domain=NonNegativeReals,
        ),
    )
    # [VAR] ATES heating output for each schedule
    setattr(
        model,
        VAR_ATESTECHHEATSCHEDULE,
        Var(
            getattr(model, SET_ATESTECHTUPLESCHEDULE) * getattr(model, SET_TIME),
            domain=NonNegativeReals,
        ),
    )
    # [VAR] ATES cooling output for each schedule
    setattr(
        model,
        VAR_ATESTECHCOOLSCHEDULE,
        Var(
            getattr(model, SET_ATESTECHTUPLESCHEDULE) * getattr(model, SET_TIME),
            domain=NonNegativeReals,
        ),
    )
    # [CON] Respect phases for output (only heating in W2C, only cooling in
    #       C2W)
    _con_ates_tech_heatcool_phases(model, ates_data)
    # [CON] Respect electricity consumption for heating and cooling outputs
    _con_ates_tech_elec_per_heatcool(model, ates_techs, ates_data)
    # [CON] Respect tech capacity (indicating covered area). For each schedule,
    #       the maximum heating and cooling powers have to respect the product
    #       of maximal power density and covered area.
    _con_ates_tech_heatcool_cap(model, ates_techs, ates_data, times)
    # [CON] Respect the parameters max_heat_over_cool and max_cool_over_heat
    _con_ates_tech_max_heat_over_cool(model, ates_techs)
    _con_ates_tech_max_cool_over_heat(model, ates_techs)


def _build_overall(model: Model, ates_techs: AtesTechs) -> None:
    # [SET] Tuples of ATES tech tuples and their input ec (elec)
    setattr(
        model,
        SET_ATESTECHIN,
        Set(
            within=(getattr(model, SET_ATESTECHTUPLE) * getattr(model, SET_EC)),
            initialize=[
                (s, h, x, ates_techs.get_ec_el(TechId(x)).key)
                for (s, h, x) in getattr(model, SET_ATESTECHTUPLE)
            ],
        ),
    )
    # [SET] Tuples of ATES tech tuples and their output ecs (heatt & cool)
    setattr(
        model,
        SET_ATESTECHOUT,
        Set(
            within=(getattr(model, SET_ATESTECHTUPLE) * getattr(model, SET_EC)),
            initialize=[
                (s, h, x, e.key)
                for (s, h, x) in getattr(model, SET_ATESTECHTUPLE)
                for e in [
                    ates_techs.get_ec_ht(TechId(x)),
                    ates_techs.get_ec_co(TechId(x)),
                ]
            ],
        ),
    )
    # [VAR] ATES input (electricity)
    setattr(
        model,
        VAR_ATESTECHIN,
        Var(
            getattr(model, SET_ATESTECHIN) * getattr(model, SET_TIME),
            domain=NonNegativeReals,
        ),
    )
    # [VAR] ATES output (heating and cooling)
    setattr(
        model,
        VAR_ATESTECHOUT,
        Var(
            getattr(model, SET_ATESTECHOUT) * getattr(model, SET_TIME),
            domain=NonNegativeReals,
        ),
    )
    # [CON] ATES input & output is made from sum over schedules
    _con_ates_tech_inout_from_schedules(model, ates_techs)


def _build_cost(
    model: Model,
    stages: Stages,
    techs: Techs,
    ates_techs: AtesTechs,
    ates_data: AtesData,
    times: Times,
) -> None:
    # Deactivate conventional CAPEX costs from tech module for ATES techs
    _con_deactivate_tech_cost_capex(model, ates_techs)
    # Set CAPEX costs for ATES techs
    _con_ates_tech_cost_capex(model, stages, techs, ates_techs, ates_data, times)
    # Deactivate conventional OPEX costs from tech module for ATES techs
    _con_deactivate_tech_cost_opex_cap(model, ates_techs)
    # Set OPEX costs for ATES techs
    _con_ates_tech_cost_opex_cap(model, stages, techs, ates_techs, ates_data, times)


def _build_emissions(
    model: Model,
    stages: Stages,
    techs: Techs,
    ates_techs: AtesTechs,
    ates_data: AtesData,
    times: Times,
) -> None:
    # Deactivate conventional CO2 emissions from tech module for ATES techs
    _con_deactivate_tech_co2_instl(model, ates_techs)
    # Set CO2 emissions for ATES techs
    _con_ates_tech_co2_instl(model, stages, techs, ates_techs, ates_data, times)


def _con_ates_tech_cap_available_area(model: Model, ates_data: AtesData) -> None:
    def __rule_ates_tech_cap_available_area(model, s, h):
        # Available area
        max_cap = ates_data.get_available_area(StageId(s), HubId(h))
        # Get total ATES tech capacity
        total_cap = sum(
            getattr(model, VAR_TECHCAP)[s, h, x]
            for (s_, h_, x) in getattr(model, SET_ATESTECHTUPLE)
            if s == s_
            if h == h_
        )
        # Avoid trivial constraint
        if isinstance(total_cap, int) and total_cap == 0:
            return Constraint.Skip
        # Set constraint
        return total_cap <= max_cap

    setattr(
        model,
        CON_ATESTECHCAPAVAILABLEAREA,
        Constraint(
            getattr(model, SET_STAGE),
            getattr(model, SET_HUB),
            rule=__rule_ates_tech_cap_available_area,
        ),
    )


def _con_ates_tech_cap_from_schedules(model: Model) -> None:
    def __rule_ates_tech_cap_from_schedules(model, s, h, x):
        # Calculate total capacity from capacity across all schedules
        total_cap = sum(
            getattr(model, VAR_ATESTECHCAPSCHEDULE)[s, h, x, i]
            for (s_, h_, x_, i) in getattr(model, SET_ATESTECHTUPLESCHEDULE)
            if s_ == s
            if h_ == h
            if x_ == x
        )
        # Set constraint
        return getattr(model, VAR_TECHCAP)[s, h, x] == total_cap

    setattr(
        model,
        CON_ATESTECHCAPFROMSCHEDULES,
        Constraint(
            getattr(model, SET_ATESTECHTUPLE), rule=__rule_ates_tech_cap_from_schedules
        ),
    )


def _con_ates_tech_elec_per_heatcool(
    model: Model, ates_techs: AtesTechs, ates_data: AtesData
) -> None:
    # Variables
    var_elec = getattr(model, VAR_ATESTECHELECSCHEDULE)
    var_heat = getattr(model, VAR_ATESTECHHEATSCHEDULE)
    var_cool = getattr(model, VAR_ATESTECHCOOLSCHEDULE)

    def __rule_ates_tech_elec_per_heatcool(model, s, h, x, i, t):
        # Parameters
        elec_per_energy_heat = ates_techs.get_elec_per_energy_heat(
            StageId(s), HubId(h), TechId(x), ates_data
        )
        elec_per_energy_cool = ates_techs.get_elec_per_energy_heat(
            StageId(s), HubId(h), TechId(x), ates_data
        )
        # Get total electricity consumption
        total_elec = (
            elec_per_energy_heat * var_heat[s, h, x, i, t]
            + elec_per_energy_cool * var_cool[s, h, x, i, t]
        )
        # Set constraint
        return var_elec[s, h, x, i, t] == total_elec

    setattr(
        model,
        CON_ATESTECHELECPERHEATCOOL,
        Constraint(
            getattr(model, SET_ATESTECHTUPLESCHEDULE),
            getattr(model, SET_TIME),
            rule=__rule_ates_tech_elec_per_heatcool,
        ),
    )


def _con_ates_tech_heatcool_phases(model: Model, ates_data: AtesData) -> None:
    def __rule_ates_tech_heat_phases(model, s, h, x, i, t):
        if not ates_data.is_in_w2c_phase(HubId(h), AtesScheduleId(i), TimeId(t)):
            return getattr(model, VAR_ATESTECHHEATSCHEDULE)[s, h, x, i, t] == 0
        return Constraint.Skip

    def __rule_ates_tech_cool_phases(model, s, h, x, i, t):
        if not ates_data.is_in_c2w_phase(HubId(h), AtesScheduleId(i), TimeId(t)):
            return getattr(model, VAR_ATESTECHCOOLSCHEDULE)[s, h, x, i, t] == 0
        return Constraint.Skip

    setattr(
        model,
        CON_ATESTECHHEATPHASES,
        Constraint(
            getattr(model, SET_ATESTECHTUPLESCHEDULE),
            getattr(model, SET_TIME),
            rule=__rule_ates_tech_heat_phases,
        ),
    )
    setattr(
        model,
        CON_ATESTECHCOOLPHASES,
        Constraint(
            getattr(model, SET_ATESTECHTUPLESCHEDULE),
            getattr(model, SET_TIME),
            rule=__rule_ates_tech_cool_phases,
        ),
    )


def _con_ates_tech_inout_from_schedules(model: Model, ates_techs: AtesTechs) -> None:
    def __rule_ates_tech_in_from_schedules(model, s, h, x, e, t):
        # Calculate total electricity input
        total_elec = sum(
            getattr(model, VAR_ATESTECHELECSCHEDULE)[s, h, x, i, t]
            for (s_, h_, x_, i) in getattr(model, SET_ATESTECHTUPLESCHEDULE)
            if s_ == s
            if h_ == h
            if x_ == x
        )
        # Set constraint
        return getattr(model, VAR_ATESTECHIN)[s, h, x, e, t] == total_elec

    def __rule_ates_tech_out_from_schedules(model, s, h, x, e, t):
        # Heating (W2C)
        if EcId(e) == ates_techs.get_ec_ht(TechId(x)):
            total_heat = sum(
                getattr(model, VAR_ATESTECHHEATSCHEDULE)[s, h, x, i, t]
                for (s_, h_, x_, i) in getattr(model, SET_ATESTECHTUPLESCHEDULE)
                if s_ == s
                if h_ == h
                if x_ == x
            )
            # Set constraint
            return getattr(model, VAR_ATESTECHOUT)[s, h, x, e, t] == total_heat
        # Cooling (C2W)
        total_cool = sum(
            getattr(model, VAR_ATESTECHCOOLSCHEDULE)[s, h, x, i, t]
            for (s_, h_, x_, i) in getattr(model, SET_ATESTECHTUPLESCHEDULE)
            if s_ == s
            if h_ == h
            if x_ == x
        )
        # Set constraint
        return getattr(model, VAR_ATESTECHOUT)[s, h, x, e, t] == total_cool

    setattr(
        model,
        CON_ATESTECHINFROMSCHEDULES,
        Constraint(
            getattr(model, SET_ATESTECHIN),
            getattr(model, SET_TIME),
            rule=__rule_ates_tech_in_from_schedules,
        ),
    )
    setattr(
        model,
        CON_ATESTECHOUTFROMSCHEDULES,
        Constraint(
            getattr(model, SET_ATESTECHOUT),
            getattr(model, SET_TIME),
            rule=__rule_ates_tech_out_from_schedules,
        ),
    )


def _con_ates_tech_heatcool_cap(
    model: Model, ates_techs: AtesTechs, ates_data: AtesData, times: Times
) -> None:
    # Precompute maximal power densities
    max_power_density_heat: Dict[
        Tuple[StageId, HubId, TechId, AtesScheduleId], float
    ] = {}
    max_power_density_cool: Dict[
        Tuple[StageId, HubId, TechId, AtesScheduleId], float
    ] = {}
    for s, h, x, i in getattr(model, SET_ATESTECHTUPLESCHEDULE):
        max_pow_heat, max_pow_cool = ates_techs.calc_max_power_densities(
            StageId(s), HubId(h), TechId(x), AtesScheduleId(i), ates_data, times
        )
        max_power_density_heat[StageId(s), HubId(h), TechId(x), AtesScheduleId(i)] = (
            max_pow_heat
        )
        max_power_density_cool[StageId(s), HubId(h), TechId(x), AtesScheduleId(i)] = (
            max_pow_cool
        )

    def __rule_ates_tech_heat_cap(model, s, h, x, i, t):
        # Calculate maximal heating power based on maximal heating power
        # density and installed capacity (= area)
        max_heat = (
            max_power_density_heat[StageId(s), HubId(h), TechId(x), AtesScheduleId(i)]
            * getattr(model, VAR_ATESTECHCAPSCHEDULE)[s, h, x, i]
        )
        # Set constraint
        return getattr(model, VAR_ATESTECHHEATSCHEDULE)[s, h, x, i, t] <= max_heat

    def __rule_ates_tech_cool_cap(model, s, h, x, i, t):
        # Calculate maximal cooling power based on maximal cooling power
        # density and installed capacity (= area)
        max_cool = (
            max_power_density_cool[StageId(s), HubId(h), TechId(x), AtesScheduleId(i)]
            * getattr(model, VAR_ATESTECHCAPSCHEDULE)[s, h, x, i]
        )
        # Set constraint
        return getattr(model, VAR_ATESTECHCOOLSCHEDULE)[s, h, x, i, t] <= max_cool

    setattr(
        model,
        CON_ATESTECHHEATCAP,
        Constraint(
            getattr(model, SET_ATESTECHTUPLESCHEDULE),
            getattr(model, SET_TIME),
            rule=__rule_ates_tech_heat_cap,
        ),
    )
    setattr(
        model,
        CON_ATESTECHCOOLCAP,
        Constraint(
            getattr(model, SET_ATESTECHTUPLESCHEDULE),
            getattr(model, SET_TIME),
            rule=__rule_ates_tech_cool_cap,
        ),
    )


def _con_ates_tech_max_heat_over_cool(model: Model, ates_techs: AtesTechs) -> None:
    def __rule_ates_tech_max_heat_over_cool(model, s, h, x, i):
        # Parameter
        max_heat_over_cool = ates_techs.get_max_heat_over_cool(
            StageId(s), HubId(h), TechId(x), AtesScheduleId(i)
        )
        if np.isinf(max_heat_over_cool):
            return Constraint.Skip
        # Calculate total heating and cooling output
        total_heat = sum(
            getattr(model, VAR_ATESTECHHEATSCHEDULE)[s, h, x, i, t]
            for t in getattr(model, SET_TIME)
        )
        total_cool = sum(
            getattr(model, VAR_ATESTECHCOOLSCHEDULE)[s, h, x, i, t]
            for t in getattr(model, SET_TIME)
        )
        # Set constraint
        return total_heat <= max_heat_over_cool * total_cool

    setattr(
        model,
        CON_ATESTECHMAXHEATOVERCOOL,
        Constraint(
            getattr(model, SET_ATESTECHTUPLESCHEDULE),
            rule=__rule_ates_tech_max_heat_over_cool,
        ),
    )


def _con_ates_tech_max_cool_over_heat(model: Model, ates_techs: AtesTechs) -> None:
    def __rule_ates_tech_max_cool_over_heat(model, s, h, x, i):
        # Parameter
        max_cool_over_heat = ates_techs.get_max_cool_over_heat(
            StageId(s), HubId(h), TechId(x), AtesScheduleId(i)
        )
        if np.isinf(max_cool_over_heat):
            return Constraint.Skip
        # Calculate total heating and cooling output
        total_heat = sum(
            getattr(model, VAR_ATESTECHHEATSCHEDULE)[s, h, x, i, t]
            for t in getattr(model, SET_TIME)
        )
        total_cool = sum(
            getattr(model, VAR_ATESTECHCOOLSCHEDULE)[s, h, x, i, t]
            for t in getattr(model, SET_TIME)
        )
        # Set constraint
        return total_cool <= max_cool_over_heat * total_heat

    setattr(
        model,
        CON_ATESTECHMAXCOOLOVERHEAT,
        Constraint(
            getattr(model, SET_ATESTECHTUPLESCHEDULE),
            rule=__rule_ates_tech_max_cool_over_heat,
        ),
    )


def _con_deactivate_tech_cost_capex(model: Model, ates_techs: AtesTechs) -> None:
    for s, h, x in getattr(model, SET_TECHTUPLE):
        if TechId(x) not in ates_techs.ids:
            continue
        getattr(model, CON_TECHCOSTCAPEX)[s, h, x].deactivate()


def _con_ates_tech_cost_capex(
    model: Model,
    stages: Stages,
    techs: Techs,
    ates_techs: AtesTechs,
    ates_data: AtesData,
    times: Times,
) -> None:
    def __rule_ates_tech_cost_capex(model, s, h, x):
        # Parameters
        current_year = stages.get_start_year(StageId(s))
        interest_rate = techs.get_interest_rate(TechId(x))
        tech_lifetime = techs.get_lifetime(TechId(x))
        crf = calculate_crf(interest_rate, tech_lifetime)
        # Area per well pair
        therm_rad_warm_max = max(
            [
                ates_techs.get_thermal_radius_per_warm_well(
                    s_, HubId(h), TechId(x), i, ates_data, times
                )
                for s_ in stages.ids
                for i in ates_data.get_schedule_ids(HubId(h))
            ]
        )
        therm_rad_cold_max = max(
            [
                ates_techs.get_thermal_radius_per_cold_well(
                    s_, HubId(h), TechId(x), i, ates_data, times
                )
                for s_ in stages.ids
                for i in ates_data.get_schedule_ids(HubId(h))
            ]
        )
        area_calc_method = ates_techs.get_well_pair_area_calc_method(TechId(x))
        area_per_well_pair_max = ates_techs.calc_area_per_well_pair(
            therm_rad_warm_max, therm_rad_cold_max, area_calc_method
        )
        cost_capex = 0
        for s_instl in stages.ids_in_order:
            # Only consider valid tech tuples
            if (s_instl.key, h, x) not in getattr(model, SET_TECHTUPLE):
                continue
            # Check current stage is within lifetime of installed tech
            start_year_instl = stages.get_start_year(s_instl)
            if current_year < start_year_instl:
                continue
            if current_year - start_year_instl >= tech_lifetime:
                continue
            # Installation-stage-dependent parameters
            capex_per_well_pair = ates_techs.get_capex_per_well_pair(s_instl, TechId(x))
            one_time_capex = techs.get_one_time_capex(s_instl, TechId(x))
            # One-time capex costs (if installation occured)
            cost_capex += (
                crf
                * one_time_capex
                * getattr(model, VAR_YTECHCAPINSTL)[s_instl.key, h, x]
            )
            # Per-well-pair capex costs
            cost_capex += (
                crf
                * capex_per_well_pair
                * getattr(model, VAR_TECHCAPINSTL)[s_instl.key, h, x]
                / area_per_well_pair_max
            )

        # Set constraint
        return getattr(model, VAR_TECHCOSTCAPEX)[s, h, x] == cost_capex

    setattr(
        model,
        CON_ATESTECHCOSTCAPEX,
        Constraint(getattr(model, SET_ATESTECHTUPLE), rule=__rule_ates_tech_cost_capex),
    )


def _con_deactivate_tech_cost_opex_cap(model: Model, ates_techs: AtesTechs) -> None:
    for s, h, x in getattr(model, SET_TECHTUPLE):
        if TechId(x) not in ates_techs.ids:
            continue
        getattr(model, CON_TECHCOSTOPEXCAP)[s, h, x].deactivate()


def _con_ates_tech_cost_opex_cap(
    model: Model,
    stages: Stages,
    techs: Techs,
    ates_techs: AtesTechs,
    ates_data: AtesData,
    times: Times,
) -> None:
    def __rule_ates_tech_cost_opex_cap(model, s, h, x):
        # Parameters
        opex_per_well_pair = ates_techs.get_opex_per_well_pair(StageId(s), TechId(x))
        one_time_opex = techs.get_one_time_opex(StageId(s), TechId(x))
        # Area per well pair
        therm_rad_warm_max = max(
            [
                ates_techs.get_thermal_radius_per_warm_well(
                    s_, HubId(h), TechId(x), i, ates_data, times
                )
                for s_ in stages.ids
                for i in ates_data.get_schedule_ids(HubId(h))
            ]
        )
        therm_rad_cold_max = max(
            [
                ates_techs.get_thermal_radius_per_cold_well(
                    s_, HubId(h), TechId(x), i, ates_data, times
                )
                for s_ in stages.ids
                for i in ates_data.get_schedule_ids(HubId(h))
            ]
        )
        area_calc_method = ates_techs.get_well_pair_area_calc_method(TechId(x))
        area_per_well_pair_max = ates_techs.calc_area_per_well_pair(
            therm_rad_warm_max, therm_rad_cold_max, area_calc_method
        )
        # OPEX from capacity calculation
        cost_opex_cap = (
            one_time_opex * getattr(model, VAR_YTECHUSED)[s, h, x]
            + opex_per_well_pair
            * getattr(model, VAR_TECHCAP)[s, h, x]
            / area_per_well_pair_max
        )
        # Set constraint
        return getattr(model, VAR_TECHCOSTOPEXCAP)[s, h, x] == cost_opex_cap

    setattr(
        model,
        CON_ATESTECHCOSTOPEXCAP,
        Constraint(
            getattr(model, SET_ATESTECHTUPLE), rule=__rule_ates_tech_cost_opex_cap
        ),
    )


def _con_deactivate_tech_co2_instl(model: Model, ates_techs: AtesTechs) -> None:
    for s, h, x in getattr(model, SET_TECHTUPLE):
        if TechId(x) not in ates_techs.ids:
            continue
        getattr(model, CON_TECHCO2INSTL)[s, h, x].deactivate()


def _con_ates_tech_co2_instl(
    model: Model,
    stages: Stages,
    techs: Techs,
    ates_techs: AtesTechs,
    ates_data: AtesData,
    times: Times,
) -> None:
    def __rule_ates_tech_co2_instl(model, s, h, x):
        # Parameters
        current_year = stages.get_start_year(StageId(s))
        tech_lifetime = techs.get_lifetime(TechId(x))
        co2_per_well_pair = ates_techs.get_co2_per_well_pair(StageId(s), TechId(x))
        co2_instl = 0
        # Area per well pair
        therm_rad_warm_max = max(
            [
                ates_techs.get_thermal_radius_per_warm_well(
                    s_, HubId(h), TechId(x), i, ates_data, times
                )
                for s_ in stages.ids
                for i in ates_data.get_schedule_ids(HubId(h))
            ]
        )
        therm_rad_cold_max = max(
            [
                ates_techs.get_thermal_radius_per_cold_well(
                    s_, HubId(h), TechId(x), i, ates_data, times
                )
                for s_ in stages.ids
                for i in ates_data.get_schedule_ids(HubId(h))
            ]
        )
        area_calc_method = ates_techs.get_well_pair_area_calc_method(TechId(x))
        area_per_well_pair_max = ates_techs.calc_area_per_well_pair(
            therm_rad_warm_max, therm_rad_cold_max, area_calc_method
        )
        # Installation stages
        for s_instl in stages.ids_in_order:
            # Only consider valid tech tuples
            if (s_instl.key, h, x) not in getattr(model, SET_TECHTUPLE):
                continue
            # Check current stage is within lifetime of installed tech
            start_year_instl = stages.get_start_year(s_instl)
            if current_year < start_year_instl:
                continue
            if current_year - start_year_instl >= tech_lifetime:
                continue
            # Add the CO2 for the current stage
            co2_instl += (
                co2_per_well_pair
                * getattr(model, VAR_TECHCAP)[s_instl.key, h, x]
                / area_per_well_pair_max
                / tech_lifetime
            )

        # Set constraint
        return getattr(model, VAR_TECHCO2INSTL)[s, h, x] == co2_instl

    setattr(
        model,
        CON_ATESTECHCO2INSTL,
        Constraint(getattr(model, SET_ATESTECHTUPLE), rule=__rule_ates_tech_co2_instl),
    )
