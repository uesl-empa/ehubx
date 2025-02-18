"""Wind technology submodel"""
from pyomo.core import Constraint, Model, NonNegativeReals, Set, Var
from datetime import datetime
from ehubx.core import logging
from ehubx.data.stage_data import StageId
from ehubx.data.hub_data import HubId
from ehubx.data.tech_data import TechId
from ehubx.data.conv_tech_data import ConversionTechs
from ehubx.data.wind_data import WindData, WindparkId
from ehubx.data.wind_tech_data import WindTechs
from ehubx.data.time_data import TimeId
from ehubx.model.stage_model import SET_STAGE
from ehubx.model.hub_model import SET_HUB
from ehubx.model.tech_model import VAR_TECHCAP, VAR_YTECHCAPINSTL
from ehubx.model.conv_tech_model import SET_CONVTECHTUPLE, VAR_CONVTECHIN, \
    CON_CONVTECHCAPANDAVAILABILITY
from ehubx.model.times_model import SET_TIME

# Literals
LOG_MODULE_STR: str = "mod/wind_tech"
"""String identifying the wind technology model for logging purposes"""

SET_WINDTECHTUPLE: str = "S_WindTechTuple"
"""Name of set with tech tuples of wind techs"""

SET_WINDPARK: str = "S_WindPark"
"""Name of set with wind park indices"""

VAR_WINDTECHINCIDENT: str = "V_WindTechIncident"
"""Name of variable for wind tech incident"""

VAR_WINDTECHCURTAILMENT: str = "V_WindTechCurtailment"
"""Name of variable for wind tech curtailment"""

CON_WINDTECHINCIDENT: str = "C_WindTechIncident"
"""Name of constraint setting the wind tech incident based on velocity and
tech capacity"""

CON_WINDTECHCURTAILMAX: str = "C_WindTechCurtailMax"
"""Name of constraint setting an upper limit to curtailment based on parameter
'curtail_max_rel'"""

CON_WINDTECHIN: str = "C_WindTechIn"
"""Name of constraint setting the conversion tech input of wind techs based on
wind tech incident and curtailment"""

CON_WINDTECHAREAMIN: str = "C_WindTechAreaMin"
"""Name of constraint constraint setting the minimal tech capacity for wind
techs based on minimal required area (parameter 'turbine_footprint')"""

CON_WINDPARKAREA: str = "C_WindParkArea"
"""Name of constraint limiting tech capacity for wind techs based on available
windpark area"""

DEF_AIRDENSITY: float = 1.23
"""Air density [kg/m^3] at 15°C and 101.325 kPa """

# TODO: We need to cite a source for this wind model


def build(model: Model, conv_techs: ConversionTechs, wind_techs: WindTechs,
          wind_data: WindData) -> None:
    """
    Builds the wind technology submodel. For a mathematical description
    in thorough detail, please refer to the section 'Wind model' in the
    documentation.

    :param model: Pyomo model
    :type model: Model
    :param conv_techs: Conversion technology data object
    :type conv_techs: ConversionTechs
    :param wind_techs: Wind technology data object
    :type wind_techs: WindTechs
    :param wind_data: Wind data object
    :type wind_data: WindData
    """
    # Start measuring build time
    start = datetime.now()
    # [SET] Wind techs
    setattr(model, SET_WINDTECHTUPLE,
            Set(within=getattr(model, SET_CONVTECHTUPLE),
                initialize=[(s, h, x)
                            for (s, h, x) in getattr(model, SET_CONVTECHTUPLE)
                            if TechId(x) in wind_techs.ids]))
    # [VAR] Wind tech incident
    setattr(model, VAR_WINDTECHINCIDENT,
            Var(getattr(model, SET_WINDTECHTUPLE),
                getattr(model, SET_TIME),
                domain=NonNegativeReals))
    # [CON] Wind tech incident (includes availabilility)
    _con_wind_tech_incident(model, conv_techs, wind_techs, wind_data)
    # [VAR] Wind tech curtailment
    setattr(model, VAR_WINDTECHCURTAILMENT,
            Var(getattr(model, SET_WINDTECHTUPLE),
                getattr(model, SET_TIME),
                domain=NonNegativeReals))
    # [CON] Maximal curtailment
    _con_wind_tech_curtail_max(model, wind_techs)
    # [CON] Wind input equals incident minus curtailment
    _con_wind_tech_in(model, conv_techs)
    # Deactivate conversion tech constraint, limiting output by capacity and
    # availability
    _con_deactivate_conv_tech_cap_and_availability(model)
    # [CON] Limit minimal area for each wind tech by turbine footprint of one
    #       single wind tech
    _con_wind_tech_area_min(model, wind_techs)
    # [SET] Windparks
    setattr(model, SET_WINDPARK,
            Set(initialize=[wp.key for wp in wind_data.windpark_ids]))
    # [CON] Limit total installed capacity for each wind tech by windpark area
    _con_windpark_area(model, conv_techs, wind_data)
    # Logging
    elapsed = datetime.now() - start
    logging.log_file(
        "Built wind tech module. Elapsed time: "
        f"{int(elapsed.total_seconds())}s", module=LOG_MODULE_STR)


def _con_wind_tech_incident(model: Model, conv_techs: ConversionTechs,
                            wind_techs: WindTechs, wind_data: WindData
                            ) -> None:

    def __rule_wind_tech_incident(model, s, h, x, t):
        # Get parameters
        rotor_area = wind_techs.get_rotor_area(StageId(s), TechId(x))
        turbine_footprint = wind_techs.get_turbine_footprint(StageId(s),
                                                             TechId(x))
        e_wind = conv_techs.get_in_ec_main(TechId(x))
        velo = wind_data.get_velocity(StageId(s), e_wind).get_value(TimeId(t))
        velo_cut_in = wind_techs.get_velo_cut_in(StageId(s), TechId(x))
        velo_nominal = wind_techs.get_velo_nominal(StageId(s), TechId(x))
        velo_cut_off = wind_techs.get_velo_cut_off(StageId(s), TechId(x))
        availability = conv_techs.get_availability(StageId(s), HubId(h),
            TechId(x)).get_value(TimeId(t))
        # Calculate the "linear factor"
        # TODO: Specifiy this in more detail when the citation is here
        linear_factor = (0.5 * DEF_AIRDENSITY * rotor_area)
        linear_factor /= (1000 * turbine_footprint)
        # Calculate the wind tech incident:
        #   In [velo_cut_in, velo_nominal]: Cubic with wind speed
        #   In [velo_nominal, velo_cut_off]: Cubic with nominal wind speed
        #   Below velo_cut_in and above velo_cut_off: Zero
        wind_tech_incident = 0
        if (velo >= velo_cut_in) and (velo <= velo_nominal):
            wind_tech_incident = (linear_factor
                                  * getattr(model, VAR_TECHCAP)[s, h, x]
                                  * velo ** 3)
        if (velo > velo_nominal) and (velo <= velo_cut_off):
            wind_tech_incident = (linear_factor
                                  * getattr(model, VAR_TECHCAP)[s, h, x]
                                  * velo_nominal ** 3)
        # Multiply incident by tech availability
        wind_tech_incident *= availability
        # Set the constraint
        return (getattr(model, VAR_WINDTECHINCIDENT)[s, h, x, t]
                == wind_tech_incident)

    setattr(model, CON_WINDTECHINCIDENT,
            Constraint(getattr(model, SET_WINDTECHTUPLE),
                       getattr(model, SET_TIME),
                       rule=__rule_wind_tech_incident))


def _con_wind_tech_curtail_max(model: Model, wind_techs: WindTechs) -> None:

    def __rule_wind_tech_curtail_max(model, s, h, x, t):
        # Get parameters
        curtail_max_rel = wind_techs.get_curtail_max_rel(StageId(s), TechId(x))
        # Calculate the maximal curtailment
        curtail_max = (curtail_max_rel
                       * getattr(model, VAR_WINDTECHINCIDENT)[s, h, x, t])
        # Set the constraint
        return (getattr(model, VAR_WINDTECHCURTAILMENT)[s, h, x, t]
                <= curtail_max)

    setattr(model, CON_WINDTECHCURTAILMAX,
            Constraint(getattr(model, SET_WINDTECHTUPLE),
                       getattr(model, SET_TIME),
                       rule=__rule_wind_tech_curtail_max))


def _con_wind_tech_in(model: Model, conv_techs: ConversionTechs) -> None:

    def __rule_wind_tech_in(model, s, h, x, t):
        # Get wind ec
        e_wind = conv_techs.get_in_ec_main(TechId(x))
        # Calculate the wind tech input
        wind_tech_in = (getattr(model, VAR_WINDTECHINCIDENT)[s, h, x, t]
                        - getattr(model, VAR_WINDTECHCURTAILMENT)[s, h, x, t])
        # Set the constraint
        return (getattr(model, VAR_CONVTECHIN)[s, h, x, e_wind.key, t]
                == wind_tech_in)

    setattr(model, CON_WINDTECHIN,
            Constraint(getattr(model, SET_WINDTECHTUPLE),
                       getattr(model, SET_TIME),
                       rule=__rule_wind_tech_in))


def _con_deactivate_conv_tech_cap_and_availability(model: Model) -> None:
    for (s, h, x) in getattr(model, SET_WINDTECHTUPLE):
        for t in getattr(model, SET_TIME):
            getattr(model,
                    CON_CONVTECHCAPANDAVAILABILITY)[s, h, x, t].deactivate()


def _con_wind_tech_area_min(model: Model, wind_techs: WindTechs) -> None:

    def __rule_wind_tech_area_min(model, s, h, x):
        # Get turbine footprint
        turbine_footprint = wind_techs.get_turbine_footprint(StageId(s),
                                                             TechId(x))
        # Calculate minimal wind tech area
        min_area = turbine_footprint * getattr(model, VAR_YTECHCAPINSTL
                                               )[s, h, x]
        # Set the constraint
        return getattr(model, VAR_TECHCAP)[s, h, x] >= min_area

    setattr(model, CON_WINDTECHAREAMIN,
            Constraint(getattr(model, SET_WINDTECHTUPLE),
                       rule=__rule_wind_tech_area_min))


def _con_windpark_area(model: Model, conv_techs: ConversionTechs,
                       wind_data: WindData) -> None:

    def __rule_windpark_area(model, s, h, wp):
        # Get available windpark area
        windpark_area = wind_data.get_windpark_area(StageId(s),
            HubId(h), WindparkId(wp))
        # Calulate installed wind tech area
        installed_area = sum(
            getattr(model, VAR_TECHCAP)[s, h, x]
            for (s_, h_, x) in getattr(model, SET_WINDTECHTUPLE)
            if s_ == s
            if h_ == h
            if (conv_techs.get_in_ec_main(TechId(x))
                in wind_data.get_windpark_ecs(WindparkId(wp))))
        # Avoid the trivial case
        if isinstance(installed_area, int) and installed_area == 0:
            return Constraint.Skip
        # Set the constraint
        return installed_area <= windpark_area

    setattr(model, CON_WINDPARKAREA,
            Constraint(getattr(model, SET_STAGE),
                       getattr(model, SET_HUB),
                       getattr(model, SET_WINDPARK),
                       rule=__rule_windpark_area))
