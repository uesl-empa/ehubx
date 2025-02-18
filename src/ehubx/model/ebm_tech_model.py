"""Electricity-based mobility (EBM) submodel"""
from datetime import datetime
from pyomo.core import Any, Constraint, Model, NonNegativeReals, Param, Set, \
    Var
from ehubx.core import common
from ehubx.core import logging
from ehubx.data.stage_data import Stages, StageId
from ehubx.data.hub_data import HubId
from ehubx.data.tech_data import TechId
from ehubx.data.ebm_tech_data import EbmTechs
from ehubx.data.time_data import Times, TimeId
from ehubx.model.tech_model import SET_TECH, SET_TECHTUPLE, VAR_TECHCAP, \
    VAR_YTECHUSED
from ehubx.model.times_model import SET_TIME, SET_TIMEHORIZON

# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/ebm_tech"
"""String identifying the EBM technology model for logging purposes"""

SET_EBMTECH: str = "S_EbmTech"
"""Name of set with EBM techs"""

SET_EBMTECHTUPLE: str = "S_EbmTechTuple"
"""Name of set with EBM tech tuples"""

VAR_EBMTECHINFLOW: str = "V_EbmTechInflow"
"""Name of variable for inflow into EBM techs"""

VAR_EBMTECHOUTFLOW: str = "V_EbmTechOutflow"
"""Name of variable for outflow into EBM techs"""

VAR_EBMTECHENERGY: str = "V_EbmTechEnergy"
"""Name of variable for energy stored in EBM techs"""

PAR_EBMTECHEC: str = "P_EbmTechEc"
"""Name of parameter specifying the ecs stored in EBM techs"""

CON_EBMTECHCAP: str = "C_EbmTechCap"
"""Name of constraint setting the tech capacity for EBM techs based on vehicle
size and storage capacity"""

CON_EBMTECHINFLOWMAX: str = "C_EbmTechInflowMax"
"""Name of constraint setting the maximal inflow for EBM techs"""

CON_EBMTECHOUTFLOWMAX: str = "C_EbmTechOutflowMax"
"""Name of constraint setting the maximal outflow for EBM techs"""

CON_EBMTECHUSED: str = "C_EbmTechUsed"
"""Name of constraint determining usage of EBM techs"""

CON_EBMTECHCHARGINGDYNAMIC: str = "C_EbmTechChargingDynamic"
"""Name of constraint defining the EBM charging dynamic connecting energy and
inflow/outflow"""

CON_EBMTECHENERGYMIN: str = "C_EbmTechEnergyMin"
"""Name of constraint setting a lower limit to the energy stored in EBM
techs"""

CON_EBMTECHENERGYMAX: str = "C_EbmTechEnergyMax"
"""Name of constraint setting an upper limit to the energy stored in EBM
techs"""

CON_EBMTECHENERGYINIT: str = "C_EbmTechEnergyInit"
"""Name of constraint setting the initial (i.e.; at the first time step)
energy levels for EBM techs"""


def build(model: Model, stages: Stages, ebm_techs: EbmTechs,
          times: Times) -> None:
    """
    Builds the electricity-based mobility (EBM) technology submodel. For a
    mathematical description in thorough detail, please refer to the section
    'EBM model' in the documentation.

    :param model: Pyomo model
    :type model: Model
    :param stages: Stage data object
    :type stages: Stages
    :param ebm_techs: EBM technology data object
    :type ebm_techs: EbmTechs
    :param times: Time data object
    :type times: Times
    """
    # Start measuring build time
    start = datetime.now()
    _build_base(model, stages, ebm_techs, times)
    # Logging
    elapsed = datetime.now() - start
    logging.log_file(("Built EBM tech module. Elapsed time: "
                      f"{int(elapsed.total_seconds())}s"),
                     module=LOG_MODULE_STR)


def _build_base(model: Model, stages: Stages, ebm_techs: EbmTechs,
                times: Times) -> None:

    # [SET] EBM techs
    setattr(model, SET_EBMTECH,
            Set(within=getattr(model, SET_TECH),
                initialize=[x.key for x in ebm_techs.ids]))
    # [SET] EBM tech tuples
    setattr(model, SET_EBMTECHTUPLE,
            Set(within=getattr(model, SET_TECHTUPLE),
                initialize=[(s, h, x)
                            for (s, h, x) in getattr(model, SET_TECHTUPLE)
                            if TechId(x) in ebm_techs.ids]))
    # [CON] Fix tech capacity to storage capacity of entire fleet
    _con_ebm_tech_cap(model, ebm_techs)
    # [PAR] Stored ec
    setattr(model, PAR_EBMTECHEC,
            Param(getattr(model, SET_EBMTECH), within=Any,
                  initialize={x.key: ebm_techs.get_ec(x).key
                              for x in ebm_techs.ids}))
    # [VAR] EBM input (grid to vehicle)
    setattr(model, VAR_EBMTECHINFLOW,
            Var(getattr(model, SET_EBMTECHTUPLE), getattr(model, SET_TIME),
                domain=NonNegativeReals))
    # [VAR] EBM output (vehicle to grid)
    setattr(model, VAR_EBMTECHOUTFLOW,
            Var(getattr(model, SET_EBMTECHTUPLE), getattr(model, SET_TIME),
                domain=NonNegativeReals))
    # [CON] Respect maximal inflow and outflow (based on capacity)
    _con_ebm_tech_inoutflow_max(model, ebm_techs)
    # [CON] Tech usage (monitored over summed-up sum of inflow and outflow)
    _con_ebm_tech_used(model, ebm_techs, times)
    # [VAR] EBM tech stored energy
    setattr(model, VAR_EBMTECHENERGY,
            Var(getattr(model, SET_EBMTECHTUPLE),
                getattr(model, SET_TIMEHORIZON),
                domain=NonNegativeReals))
    # [CON] Charging dynamic: Fleet storage level changes from one horizon_ts
    #       to the next based on flow, standby loss and consumption. A cyclical
    #       SOC approach is used so that the flow at the last horizon_ts
    #       charges the first horizon_ts
    _con_ebm_tech_charging_dynamic(model, ebm_techs, times)
    # [CON] Respect minimal and maximal EBM storage energy levels
    _con_ebm_tech_energy_minmax(model, ebm_techs)
    # [CON] Initial energy. Constraint depends on initial SOC value in data
    #       model. For inf, the first energy value of the first stage can be
    #       chosen by the optimizer. Otherwise, energy is set in all stages by
    #       the initial SOC value
    _con_ebm_tech_energy_init(model, stages, ebm_techs)


def _con_ebm_tech_cap(model: Model, ebm_techs: EbmTechs) -> None:

    def __rule_ebm_tech_cap(model, s, h, x):
        # Get parameters
        storage_cap = ebm_techs.get_storage_cap(StageId(s), TechId(x))
        num_vehicles = ebm_techs.get_num_vehicles(StageId(s), HubId(h),
                                                  TechId(x))
        # Calculate capacity
        capacity = storage_cap * num_vehicles
        # Set constraint
        return getattr(model, VAR_TECHCAP)[s, h, x] == capacity

    setattr(model, CON_EBMTECHCAP,
            Constraint(getattr(model, SET_EBMTECHTUPLE),
                       rule=__rule_ebm_tech_cap))


def _con_ebm_tech_inoutflow_max(model: Model, ebm_techs: EbmTechs) -> None:
    # Time series
    availability = {(s, h, x): ebm_techs.get_availability(StageId(s), HubId(h),
                                                          TechId(x))
                    for (s, h, x) in getattr(model, SET_EBMTECHTUPLE)}

    def __rule_ebm_tech_inflow_max(model, s, h, x, t):
        # Get parameters
        charge_max = ebm_techs.get_charge_max(StageId(s), TechId(x))
        num_vehicles = ebm_techs.get_num_vehicles(StageId(s), HubId(h),
                                                  TechId(x))
        availability_t = availability[s, h, x].get_value(TimeId(t))
        # Calculate maximal inflow
        inflow_max = 0
        if num_vehicles > 0 and availability_t > 0:
            inflow_max = charge_max * num_vehicles * availability_t
        # Set constraint
        if inflow_max == float("inf"):
            return Constraint.Skip
        return getattr(model, VAR_EBMTECHINFLOW)[s, h, x, t] <= inflow_max

    def __rule_ebm_tech_outflow_max(model, s, h, x, t):
        # Get parameters
        discharge_max = ebm_techs.get_discharge_max(StageId(s), TechId(x))
        num_vehicles = ebm_techs.get_num_vehicles(StageId(s), HubId(h),
                                                  TechId(x))
        availability_t = availability[s, h, x].get_value(TimeId(t))
        discharge_control = ebm_techs.get_discharge_control(StageId(s),
                                                            TechId(x))
        # Calculate maximal outflow
        outflow_max = 0
        if num_vehicles > 0 and availability_t > 0 and discharge_control > 0:
            outflow_max = (discharge_max * num_vehicles * availability_t
                           * discharge_control)
        # Set constraint
        if outflow_max == float("inf"):
            return Constraint.Skip
        return getattr(model, VAR_EBMTECHOUTFLOW)[s, h, x, t] <= outflow_max

    setattr(model, CON_EBMTECHINFLOWMAX,
            Constraint(getattr(model, SET_EBMTECHTUPLE),
                       getattr(model, SET_TIME),
                       rule=__rule_ebm_tech_inflow_max))
    setattr(model, CON_EBMTECHOUTFLOWMAX,
            Constraint(getattr(model, SET_EBMTECHTUPLE),
                       getattr(model, SET_TIME),
                       rule=__rule_ebm_tech_outflow_max))


def _con_ebm_tech_used(model: Model, ebm_techs: EbmTechs, times: Times
                       ) -> None:
    # Get length of full time horizon
    num_horizon_ts = times.num_horizon_ts

    def __rule_ebm_tech_used(model, s, h, x):
        # Get parameters
        num_vehicles = ebm_techs.get_num_vehicles(StageId(s), HubId(h),
                                                  TechId(x))
        charge_max = ebm_techs.get_charge_max(StageId(s), TechId(x))
        discharge_max = ebm_techs.get_discharge_max(StageId(s), TechId(x))
        storage_cap = ebm_techs.get_storage_cap(StageId(s), TechId(x))
        inflow_max = min(charge_max, storage_cap) * num_vehicles
        outflow_max = min(discharge_max, storage_cap) * num_vehicles

        # Calculate big-M parameter
        big_m = (common.EPS_BIGM
                 + (inflow_max + outflow_max) * num_horizon_ts)
        # Calculate total summed-up flow in both directions
        flow_abs_sum = sum(
            times.get_weight(StageId(s), TimeId(t))
            * (getattr(model, VAR_EBMTECHINFLOW)[s, h, x, t]
               + getattr(model, VAR_EBMTECHOUTFLOW)[s, h, x, t])
            for t in getattr(model, SET_TIME))
        # Set constraint
        return flow_abs_sum <= big_m * getattr(model, VAR_YTECHUSED)[s, h, x]

    setattr(model, CON_EBMTECHUSED,
            Constraint(getattr(model, SET_EBMTECHTUPLE),
                       rule=__rule_ebm_tech_used))


def _con_ebm_tech_charging_dynamic(model: Model, ebm_techs: EbmTechs,
                                   times: Times) -> None:

    # Get first and last full-horizon timesteps
    t_hor_first = getattr(model, SET_TIMEHORIZON).first()
    t_hor_last = getattr(model, SET_TIMEHORIZON).last()
    # Precompute consumption for efficiency
    consumption = {(s, h, x): ebm_techs.get_consumption(StageId(s), HubId(h),
                                                        TechId(x), times)
                   for (s, h, x) in getattr(model, SET_EBMTECHTUPLE)}

    def __rule_ebm_tech_charging_dynamic(model, s, h, x, t_hor):
        # Get parameters
        t = times.get_cluster_ts(StageId(s), TimeId(t_hor)).key_as_int
        in_eff = ebm_techs.get_in_eff(StageId(s), TechId(x))
        out_eff = ebm_techs.get_out_eff(StageId(s), TechId(x))
        standby_loss = ebm_techs.get_standby_loss(StageId(s), TechId(x))
        consumption_t = consumption[s, h, x].get_value(TimeId(t))
        # Calculate energy flow for the EBM fleet at this timestep
        energy_flow = (in_eff * getattr(model, VAR_EBMTECHINFLOW)[s, h, x, t]
                       - getattr(model, VAR_EBMTECHOUTFLOW)[s, h, x, t]
                       / out_eff)
        # Calculate energy level at next horizon_ts
        energy_next = ((1 - standby_loss)
                       * getattr(model, VAR_EBMTECHENERGY)[s, h, x, t_hor]
                       + energy_flow - consumption_t)
        # Get the next horizon_ts (cycle back to start if at the end)
        t_hor_next = t_hor_first
        if t_hor != t_hor_last:
            t_hor_next = getattr(model, SET_TIMEHORIZON).next(t_hor)
        # Set the constraint
        return (getattr(model, VAR_EBMTECHENERGY)[s, h, x, t_hor_next]
                == energy_next)

    setattr(model, CON_EBMTECHCHARGINGDYNAMIC,
            Constraint(getattr(model, SET_EBMTECHTUPLE),
                       getattr(model, SET_TIMEHORIZON),
                       rule=__rule_ebm_tech_charging_dynamic))


def _con_ebm_tech_energy_minmax(model: Model, ebm_techs: EbmTechs) -> None:

    def __rule_ebm_tech_energy_min(model, s, h, x, t):
        # Get parameters
        soc_min = ebm_techs.get_soc_min(StageId(s), TechId(x))
        storage_cap = ebm_techs.get_storage_cap(StageId(s), TechId(x))
        num_vehicles = ebm_techs.get_num_vehicles(StageId(s), HubId(h),
                                                  TechId(x))
        # Calculate minimal energy
        energy_min = soc_min * storage_cap * num_vehicles
        # Set constraint
        return getattr(model, VAR_EBMTECHENERGY)[s, h, x, t] >= energy_min

    def __rule_ebm_tech_energy_max(model, s, h, x, t):
        # Get parameters
        soc_max = ebm_techs.get_soc_max(StageId(s), TechId(x))
        storage_cap = ebm_techs.get_storage_cap(StageId(s), TechId(x))
        num_vehicles = ebm_techs.get_num_vehicles(StageId(s), HubId(h),
                                                  TechId(x))
        # Calculate minimal energy
        energy_max = soc_max * storage_cap * num_vehicles
        # Set constraint
        return getattr(model, VAR_EBMTECHENERGY)[s, h, x, t] <= energy_max

    setattr(model, CON_EBMTECHENERGYMIN,
            Constraint(getattr(model, SET_EBMTECHTUPLE),
                       getattr(model, SET_TIMEHORIZON),
                       rule=__rule_ebm_tech_energy_min))
    setattr(model, CON_EBMTECHENERGYMAX,
            Constraint(getattr(model, SET_EBMTECHTUPLE),
                       getattr(model, SET_TIMEHORIZON),
                       rule=__rule_ebm_tech_energy_max))


def _con_ebm_tech_energy_init(model: Model, stages: Stages, ebm_techs: EbmTechs
                              ) -> None:
    # Get initial stage and first full-horizon timestep
    s_0 = stages.init_stage
    t_hor_0 = getattr(model, SET_TIMEHORIZON).first()

    def __rule_ebm_tech_energy_init(model, s, h, x):
        # Parameters
        soc_init = ebm_techs.get_soc_init(HubId(h), TechId(x))
        num_vehicles = ebm_techs.get_num_vehicles(StageId(s), HubId(h),
                                                  TechId(x))
        storage_cap = ebm_techs.get_storage_cap(StageId(s), TechId(x))
        # Case 1: Not first stage => Set to same initial energy as first stage
        if StageId(s) != s_0:
            return (getattr(model, VAR_EBMTECHENERGY)[s, h, x, t_hor_0]
                    == getattr(model,
                               VAR_EBMTECHENERGY)[s_0.key, h, x, t_hor_0])
        # Case 2: soc_init is a real value => Set the SOC of first stage
        if soc_init < float("inf"):
            return (getattr(model, VAR_EBMTECHENERGY)[s, h, x, t_hor_0]
                    == soc_init * storage_cap * num_vehicles)
        # Case 3: soc_init is infinite => Let optimizer choose the value
        return Constraint.Skip

    setattr(model, CON_EBMTECHENERGYINIT,
            Constraint(getattr(model, SET_EBMTECHTUPLE),
                       rule=__rule_ebm_tech_energy_init))
