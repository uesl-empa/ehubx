"""Storage technology submodel"""
from datetime import datetime
from pyomo.core import Any, Constraint, Model, NonNegativeReals, Param, Set, \
    Var
from ehubx.core import common
from ehubx.core import logging
from ehubx.data.stage_data import Stages, StageId
from ehubx.data.hub_data import HubId
from ehubx.data.tech_data import Techs, TechId
from ehubx.data.stor_tech_data import StorageTechs
from ehubx.data.time_data import Times, TimeId
from ehubx.model.demand_model import PAR_BIGMGENERIC
from ehubx.model.tech_model import SET_TECH, SET_TECHTUPLE, VAR_TECHCAP, \
    VAR_YTECHUSED
from ehubx.model.times_model import SET_TIME, SET_TIMEHORIZON

# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/stor_tech"
"""String identifying the storage technology model for logging purposes"""

SET_STORTECH: str = "S_StorTech"
"""Name of set with storage techs"""

SET_STORTECHTUPLE: str = "S_StorTechTuple"
"""Name of set with storage tech tuples"""

VAR_STORTECHINFLOW: str = "V_StorTechInflow"
"""Name of variable for storage tech inflow"""

VAR_STORTECHOUTFLOW: str = "V_StorTechOutflow"
"""Name of variable for storage tech outflow"""

VAR_STORTECHENERGY: str = "V_StorTechEnergy"
"""Name of variable for energy stored in storage techs"""

PAR_STORTECHEC: str = "P_StorTechEc"
"""Name of parameter specifying the ecs stored in storage techs"""

CON_STORTECHINFLOWMAX: str = "C_StorTechInflowMax"
"""Name of constraint limiting maximal stor tech inflow based on maximal
charging speed and tech capacity"""

CON_STORTECHOUTFLOWMAX: str = "C_StorTechOutflowMax"
"""Name of constraint limiting maximal stor tech outflow based on maximal
discharging speed and tech capacity"""

CON_STORTECHUSED: str = "C_StorTechUsed"
"""Name of constraint identifying tech usage for storage techs"""

CON_STORTECHCHARGINGDYNAMIC: str = "C_StorTechChargingDynamic"
"""Name of constraint specifying the charging and discharging dynamic for
storage techs. Contains a periodic approach connecting the last and first
time steps in terms of energy levels"""

CON_STORTECHENERGYMIN: str = "C_StorTechEnergyMin"
"""Name of constraint setting a lower limit for stored energy based on minimal
SOC and tech capacity"""

CON_STORTECHENERGYMAX: str = "C_StorTechEnergyMax"
"""Name of constraint setting a lower limit for stored energy based on maximal
SOC and tech capacity"""

CON_STORTECHENERGYINIT: str = "C_StorTechEnergyInit"
"""Name of constraint setting the initial storage energy based on the
parameter 'soc_init'"""


def build(model: Model, stages: Stages, techs: Techs,
          stor_techs: StorageTechs, times: Times) -> None:
    """
    Builds the storage technology submodel. For a mathematical description
    in thorough detail, please refer to the section 'Storage model' in the
    documentation.

    :param model: Pyomo model
    :type model: Model
    :param stages: Stage data object
    :type stages: Stages
    :param techs: Technology data object
    :type techs: Techs
    :param stor_techs: Storage technology data object
    :type stor_techs: StorageTechs
    :param times: Time data object
    :type times: Times
    """
    # Start measuring build time
    start = datetime.now()
    _build_base(model, stages, techs, stor_techs, times)
    # Logging
    elapsed = datetime.now() - start
    logging.log_file(
        "Built storage tech module. Elapsed time: "
        f"{int(elapsed.total_seconds())}s", module=LOG_MODULE_STR)


def _build_base(model: Model, stages: Stages, techs: Techs,
                stor_techs: StorageTechs, times: Times) -> None:
    # [SET] Storage techs
    setattr(model, SET_STORTECH,
            Set(within=getattr(model, SET_TECH),
                initialize=[x.key for x in stor_techs.ids]))
    # [SET] Storage techs tuples
    setattr(model, SET_STORTECHTUPLE,
            Set(within=getattr(model, SET_TECHTUPLE),
                initialize=[(s, h, x)
                            for (s, h, x) in getattr(model, SET_TECHTUPLE)
                            if x in getattr(model, SET_STORTECH)]))
    # [PAR] Stored ec
    setattr(model, PAR_STORTECHEC,
            Param(getattr(model, SET_STORTECH), within=Any,
                  initialize={x.key: stor_techs.get_ec(x).key
                              for x in stor_techs.ids}))
    # [VAR] Storage inflow
    setattr(model, VAR_STORTECHINFLOW,
            Var(getattr(model, SET_STORTECHTUPLE), getattr(model, SET_TIME),
                domain=NonNegativeReals))
    # [VAR] Storage outflow
    setattr(model, VAR_STORTECHOUTFLOW,
            Var(getattr(model, SET_STORTECHTUPLE), getattr(model, SET_TIME),
                domain=NonNegativeReals))
    # [CON] Respect maximal inflow and outflow (based on capacity)
    _con_stor_tech_inoutflow_max(model, stor_techs)
    # [CON] Tech usage (monitored over sum summed-up sum of inflow and outflow)
    _con_stor_tech_used(model, techs, stor_techs, times)
    # [VAR] Storage energy
    setattr(model, VAR_STORTECHENERGY,
            Var(getattr(model, SET_STORTECHTUPLE),
                getattr(model, SET_TIMEHORIZON),
                domain=NonNegativeReals))
    # [CON] Charging dynamic: Energy level changes from one horizon_ts to the
    #       next based on flow and standby loss. A cyclical SOC approach is
    #       used so that the flow at the last horizon_ts charges the first
    #       horizon_ts
    _con_stor_tech_charging_dynamic(model, stor_techs, times)
    # [CON] Respect minimal and maximal storage energy levels (based on cap)
    _con_stor_tech_energy_minmax(model, stor_techs)
    # [CON] Initial energy. Constraint depends on initial SOC value in data
    #       model. For inf, the first energy value of the first stage can be
    #       chosen by the optimizer. Otherwise, energy is set in all stages by
    #       the initial  SOC value
    _con_stor_tech_energy_init(model, stages, stor_techs)


def _con_stor_tech_inoutflow_max(model: Model,
                                 stor_techs: StorageTechs) -> None:

    def __rule_stor_tech_inflow_max(model, s, h, x, t):
        # Get parameter
        charge_max = stor_techs.get_charge_max(StageId(s), TechId(x))
        if charge_max == float("inf"):
            return Constraint.Skip
        # Calculate maximal inflow
        inflow_max = charge_max * getattr(model, VAR_TECHCAP)[s, h, x]
        # Set constraint
        return getattr(model, VAR_STORTECHINFLOW)[s, h, x, t] <= inflow_max

    def __rule_stor_tech_outflow_max(model, s, h, x, t):
        # Get parameter
        discharge_max = stor_techs.get_discharge_max(StageId(s), TechId(x))
        if discharge_max == float("inf"):
            return Constraint.Skip
        # Calculate maximal outflow
        outflow_max = discharge_max * getattr(model, VAR_TECHCAP)[s, h, x]
        # Set constraint
        return getattr(model, VAR_STORTECHOUTFLOW)[s, h, x, t] <= outflow_max

    setattr(model, CON_STORTECHINFLOWMAX,
            Constraint(getattr(model, SET_STORTECHTUPLE),
                       getattr(model, SET_TIME),
                       rule=__rule_stor_tech_inflow_max))
    setattr(model, CON_STORTECHOUTFLOWMAX,
            Constraint(getattr(model, SET_STORTECHTUPLE),
                       getattr(model, SET_TIME),
                       rule=__rule_stor_tech_outflow_max))


def _con_stor_tech_used(model: Model, techs: Techs, stor_techs: StorageTechs,
                        times: Times) -> None:
    # Get length of full time horizon
    num_horizon_ts = times.num_horizon_ts

    def __rule_stor_tech_used(model, s, h, x):
        # Get parameters
        cap_max = techs.get_cap_max(StageId(s), HubId(h), TechId(x))
        charge_max = stor_techs.get_charge_max(StageId(s), TechId(x))
        discharge_max = stor_techs.get_discharge_max(StageId(s), TechId(x))
        # Calculate big-M parameter
        big_m = getattr(model, PAR_BIGMGENERIC) * times.num_horizon_ts
        if cap_max < float("inf"):
            inflow_max = cap_max * min(charge_max, 1)
            outflow_max = cap_max * min(discharge_max, 1)
            big_m = (common.EPS_BIGM
                     + (inflow_max + outflow_max) * num_horizon_ts)
        else:
            logging.log_file_warning(
                f"cap_max[{s}, {h}, {x}] not available to calculate a big-M "
                "value for maximal storage tech inflow/outflow. Using generic "
                f"big-M value {getattr(model, PAR_BIGMGENERIC).value} based "
                "on demands instead",
                module=LOG_MODULE_STR)
        # Calculate total summed-up flow in both directions
        flow_abs_sum = sum(
            times.get_weight(StageId(s), TimeId(t))
            * (getattr(model, VAR_STORTECHINFLOW)[s, h, x, t]
               + getattr(model, VAR_STORTECHOUTFLOW)[s, h, x, t])
            for t in getattr(model, SET_TIME))
        # Set constraint
        return flow_abs_sum <= big_m * getattr(model, VAR_YTECHUSED)[s, h, x]

    setattr(model, CON_STORTECHUSED,
            Constraint(getattr(model, SET_STORTECHTUPLE),
                       rule=__rule_stor_tech_used))


def _con_stor_tech_charging_dynamic(model: Model, stor_techs: StorageTechs,
                                    times: Times) -> None:

    # Get first and last full-horizon timesteps
    t_hor_first = getattr(model, SET_TIMEHORIZON).first()
    t_hor_last = getattr(model, SET_TIMEHORIZON).last()

    def __rule_stor_tech_charging_dynamic(model, s, h, x, t_hor):
        # Get parameters
        t = times.get_cluster_ts(StageId(s), TimeId(t_hor)).key_as_int
        in_eff = stor_techs.get_in_eff(StageId(s), TechId(x))
        out_eff = stor_techs.get_out_eff(StageId(s), TechId(x))
        standby_loss = stor_techs.get_standby_loss(StageId(s), TechId(x))
        # Calculate energy flow (for the storage tech) at this timestep
        energy_flow = (in_eff
                       * getattr(model, VAR_STORTECHINFLOW)[s, h, x, t]
                       - getattr(model, VAR_STORTECHOUTFLOW)[s, h, x, t]
                       / out_eff)
        # Calulate energy level at next horizon_ts
        energy_next = ((1 - standby_loss)
                       * getattr(model, VAR_STORTECHENERGY)[s, h, x, t_hor]
                       + energy_flow)
        # Get next horizon_ts (cycle back to start if at the end)
        t_hor_next = t_hor_first
        if t_hor != t_hor_last:
            t_hor_next = getattr(model, SET_TIMEHORIZON).next(t_hor)
        # Set the constraint
        return (getattr(model, VAR_STORTECHENERGY)[s, h, x, t_hor_next]
                == energy_next)

    setattr(model, CON_STORTECHCHARGINGDYNAMIC,
            Constraint(getattr(model, SET_STORTECHTUPLE),
                       getattr(model, SET_TIMEHORIZON),
                       rule=__rule_stor_tech_charging_dynamic))


def _con_stor_tech_energy_minmax(model: Model,
                                 stor_techs: StorageTechs) -> None:

    def __rule_stor_tech_energy_min(model, s, h, x, t):
        # Get parameter
        soc_min = stor_techs.get_soc_min(StageId(s), TechId(x))
        # Calculate minimal energy
        energy_min = soc_min * getattr(model, VAR_TECHCAP)[s, h, x]
        # Set constraint
        return getattr(model, VAR_STORTECHENERGY)[s, h, x, t] >= energy_min

    def __rule_stor_tech_energy_max(model, s, h, x, t):
        # Get parameter
        soc_max = min(stor_techs.get_soc_max(StageId(s), TechId(x)), 1)
        # Calculate maximal energy
        energy_max = soc_max * getattr(model, VAR_TECHCAP)[s, h, x]
        # Set constraint
        return getattr(model, VAR_STORTECHENERGY)[s, h, x, t] <= energy_max

    setattr(model, CON_STORTECHENERGYMIN,
            Constraint(getattr(model, SET_STORTECHTUPLE),
                       getattr(model, SET_TIMEHORIZON),
                       rule=__rule_stor_tech_energy_min))
    setattr(model, CON_STORTECHENERGYMAX,
            Constraint(getattr(model, SET_STORTECHTUPLE),
                       getattr(model, SET_TIMEHORIZON),
                       rule=__rule_stor_tech_energy_max))


def _con_stor_tech_energy_init(model: Model, stages: Stages,
                               stor_techs: StorageTechs) -> None:
    # Get initial stage and first full-horizon timestep
    s_0 = stages.init_stage
    t_hor_0 = getattr(model, SET_TIMEHORIZON).first()

    def __rule_stor_tech_energy_init(model, s, h, x):
        # Parameter
        soc_init = stor_techs.get_soc_init(HubId(h), TechId(x))
        # Case 1: Not first stage => Set to same initial energy as first stage
        if StageId(s) != s_0:
            return (getattr(model, VAR_STORTECHENERGY)[s, h, x, t_hor_0]
                    == getattr(model, VAR_STORTECHENERGY
                               )[s_0.key, h, x, t_hor_0])
        # Case 2: soc_init is a real value => Set the SOC of first stage
        if soc_init < float("inf"):
            return (getattr(model, VAR_STORTECHENERGY)[s, h, x, t_hor_0]
                    == soc_init * getattr(model, VAR_TECHCAP)[s, h, x])
        # Case 3: soc_init is infinite => Let optimizer choose the value
        return Constraint.Skip

    setattr(model, CON_STORTECHENERGYINIT,
            Constraint(getattr(model, SET_STORTECHTUPLE),
                       rule=__rule_stor_tech_energy_init))
