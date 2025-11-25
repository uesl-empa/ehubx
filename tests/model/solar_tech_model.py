"""Solar technology submodel"""

from datetime import datetime

from pyomo.core import Constraint, Model, NonNegativeReals, Set, Var

from ehubx.core import logging
from ehubx.data.conv_tech_data import ConversionTechs
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.hub_data import HubId
from ehubx.data.solar_data import SolarData
from ehubx.data.solar_tech_data import SolarTechs
from ehubx.data.stage_data import StageId
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.time_data import TimeId
from ehubx.data.unit import LengthUnit, MassUnit, PowerUnit, TimeUnit
from ehubx.model.conv_tech_model import (
    CON_CONVTECHCAPANDAVAILABILITY,
    SET_CONVTECHTUPLE,
    VAR_CONVTECHIN,
)
from ehubx.model.ec_model import SET_EC, get_ec_model_unit
from ehubx.model.hub_model import SET_HUB
from ehubx.model.stage_model import SET_STAGE
from ehubx.model.tech_model import (
    CON_YTECHINSTL,
    VAR_TECHCAP,
    VAR_TECHCAPINSTL,
    VAR_YTECHCAPINSTL,
)
from ehubx.model.times_model import SET_TIME


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/sol_tech"
"""String identifying the solar technology model for logging purposes"""

SET_SOLARTECHTUPLE: str = "S_SolarTechTuple"
"""Name of set with all tech tuples for solar techs"""

SET_SOLAREC: str = "S_SolarEc"
"""Name of set with solar ecs"""

VAR_SOLARTECHINCIDENT: str = "V_SolarTechIncident"
"""Name of variable for solar tech incident"""

CON_YTECHINSTLSOLAR: str = "C_YTechInstlSolar"
"""Name of constraint determining whether any solar technology was installed"""

CON_SOLARTECHINCIDENT: str = "C_SolarTechIncident"
"""Name of constraint to set the solar tech incident based on irradiation and
tech capacity"""

CON_SOLARTECHINMAXINCIDENTAVAILABILITY: str = "C_SolarTechInMaxIncidentAvailability"
"""Name of constraint setting an upper limit for the conversion tech input of
solar techs based on availability and solar tech incident"""

CON_SOLARTECHINMINCURTAILAVAILABILITY: str = "C_SolarTechInMinCurtailAvailability"
"""Name of constraint setting a lower limit for the conversion tech input of
solar techs based on availability and maximal relative curtailment"""

CON_SOLARAREA: str = "C_SolarArea"
"""Name of constraint respecting the available area in capacity
installation """


def build(model: Model, system: EnergySystem) -> None:
    """
    Builds the solar technology submodel. For a mathematical description
    in thorough detail, please refer to the section 'Solar model' in the
    documentation.

    :param model: Pyomo model
    :type model: Model
    :param system: Energy system data
    :type system: EnergySystem
    """
    # Extract data from modules
    ecs: Ecs = system.ecs
    techs: Techs = system.techs
    conv_techs: ConversionTechs = system.conv_techs
    solar_techs: SolarTechs = system.solar_techs
    solar_data: SolarData = system.solar_data
    length_unit: LengthUnit = system.length_unit
    mass_unit: MassUnit = system.mass_unit
    power_unit: PowerUnit = system.power_unit
    # Start measuring build time
    start = datetime.now()
    # [SET] Solar tech tuples
    setattr(
        model,
        SET_SOLARTECHTUPLE,
        Set(
            within=getattr(model, SET_CONVTECHTUPLE),
            initialize=[
                (s, h, x)
                for (s, h, x) in getattr(model, SET_CONVTECHTUPLE)
                if TechId(x) in solar_techs.ids
            ],
        ),
    )

    # [VAR] Solar incident
    setattr(
        model,
        VAR_SOLARTECHINCIDENT,
        Var(
            getattr(model, SET_SOLARTECHTUPLE),
            getattr(model, SET_TIME),
            domain=NonNegativeReals,
        ),
    )
    # [CON] Deactivate bigM constraint for VAR_TECHCAPINSTL from tech module
    #       and replace with solar version (m^2-based)
    _con_replace_y_tech_instl(model, techs, conv_techs, solar_data, length_unit)
    # [CON] Solar incident
    _con_solar_tech_incident(
        model, ecs, conv_techs, solar_data, length_unit, mass_unit, power_unit
    )
    # [CON] Conversion input to solar tech is bound above by solar incident and
    #       tech availability
    _con_solar_tech_in_max_incident_availability(model, conv_techs)
    # [CON] Conversion input to solar tech is bound below by maximal
    #       curtailment and availability
    _con_solar_tech_in_min_curtail_availability(model, conv_techs, solar_techs)
    # [SET] Solar ECs
    e_solars = [conv_techs.get_in_ec_main(x).key for x in solar_techs.ids]
    e_solars = list(set(e_solars))
    setattr(model, SET_SOLAREC, Set(within=getattr(model, SET_EC), initialize=e_solars))
    # [CON] Limit total installed capacity for each solar EC by area
    _con_solar_area(model, conv_techs, solar_data, length_unit)
    # Deactivate conversion tech constraint, limiting output by capacity and
    # availability
    _con_deactivate_conv_tech_cap_and_availability(model)
    # Logging
    elapsed = datetime.now() - start
    logging.log_file(
        f"Built storage tech module. Elapsed time: {int(elapsed.total_seconds())}s",
        module=LOG_MODULE_STR,
    )


def _con_replace_y_tech_instl(
    model: Model,
    techs: Techs,
    conv_techs: ConversionTechs,
    solar_data: SolarData,
    length_unit: LengthUnit,
) -> None:
    for s, h, x in getattr(model, SET_SOLARTECHTUPLE):
        getattr(model, CON_YTECHINSTL)[s, h, x].deactivate()

    def __rule_y_tech_instl(model, s, h, x):
        # BigM parameter for capacity (i.e. area)
        ec_sol = conv_techs.get_in_ec_main(TechId(x))
        area_max = solar_data.get_area(StageId(s), HubId(h), ec_sol).to_float(
            unit=(length_unit**2)
        )
        cap_max = techs.get_cap_max(StageId(s), HubId(h), TechId(x)).to_float(
            unit=(length_unit**2)
        )
        big_m: float
        if cap_max < float("inf"):
            big_m = cap_max + 1e-6
        elif area_max < float("inf"):
            big_m = area_max + 1e-6
        else:
            big_m = 1e6
            logging.log_file_warning(
                f"area_max[{s}, {h}, {x}] not available to calculate a big-M "
                "value for solar tech capacity. Using 1e6 instead ",
                module=LOG_MODULE_STR,
            )
        # Set constraint
        return (
            getattr(model, VAR_TECHCAPINSTL)[s, h, x]
            <= big_m * getattr(model, VAR_YTECHCAPINSTL)[s, h, x]
        )

    setattr(
        model,
        CON_YTECHINSTLSOLAR,
        Constraint(getattr(model, SET_SOLARTECHTUPLE), rule=__rule_y_tech_instl),
    )


def _con_solar_tech_incident(
    model: Model,
    ecs: Ecs,
    conv_techs: ConversionTechs,
    solar_data: SolarData,
    length_unit: LengthUnit,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
) -> None:
    def __rule_solarar_tech_incident(model, s, h, x, t):
        # Get parameters
        e_solar = conv_techs.get_in_ec_main(TechId(x))
        ec_unit = get_ec_model_unit(ecs.get_unit(e_solar), mass_unit, power_unit)
        solar_irradiation = (
            solar_data.get_irradiation(StageId(s), e_solar)
            .get_value(TimeId(t))
            .to_float(unit=((ec_unit / TimeUnit.H) / (length_unit**2)))
        )
        # Calculate solar incident
        solar_tech_incident = solar_irradiation * getattr(model, VAR_TECHCAP)[s, h, x]
        # Set constraint
        return getattr(model, VAR_SOLARTECHINCIDENT)[s, h, x, t] == solar_tech_incident

    setattr(
        model,
        CON_SOLARTECHINCIDENT,
        Constraint(
            getattr(model, SET_SOLARTECHTUPLE),
            getattr(model, SET_TIME),
            rule=__rule_solarar_tech_incident,
        ),
    )


def _con_solar_tech_in_max_incident_availability(
    model: Model,
    conv_techs: ConversionTechs,
) -> None:
    def __rule_solarar_tech_in_max_incident_availability(model, s, h, x, t):
        # Get parameters
        e_solar = conv_techs.get_in_ec_main(TechId(x))
        availability = (
            conv_techs.get_availability(StageId(s), HubId(h), TechId(x))
            .get_value(TimeId(t))
            .to_float()
        )
        # Get maximum input:
        in_max = availability * getattr(model, VAR_SOLARTECHINCIDENT)[s, h, x, t]
        # Set constraint
        return getattr(model, VAR_CONVTECHIN)[s, h, x, e_solar.key, t] <= in_max

    setattr(
        model,
        CON_SOLARTECHINMAXINCIDENTAVAILABILITY,
        Constraint(
            getattr(model, SET_SOLARTECHTUPLE),
            getattr(model, SET_TIME),
            rule=__rule_solarar_tech_in_max_incident_availability,
        ),
    )


def _con_solar_tech_in_min_curtail_availability(
    model: Model, conv_techs: ConversionTechs, solar_techs: SolarTechs
) -> None:
    def __rule_solarar_tech_in_min_curtail_availability(model, s, h, x, t):
        # Get parameters
        e_solar = conv_techs.get_in_ec_main(TechId(x))
        curtail_max_rel = solar_techs.get_curtail_max_rel(
            StageId(s), TechId(x)
        ).to_float()
        availability = (
            conv_techs.get_availability(StageId(s), HubId(h), TechId(x))
            .get_value(TimeId(t))
            .to_float()
        )
        # Calculate minimal input
        in_min = (
            (1 - curtail_max_rel)
            * availability
            * getattr(model, VAR_SOLARTECHINCIDENT)[s, h, x, t]
        )
        # Set constraint
        return getattr(model, VAR_CONVTECHIN)[s, h, x, e_solar.key, t] >= in_min

    setattr(
        model,
        CON_SOLARTECHINMINCURTAILAVAILABILITY,
        Constraint(
            getattr(model, SET_SOLARTECHTUPLE),
            getattr(model, SET_TIME),
            rule=__rule_solarar_tech_in_min_curtail_availability,
        ),
    )


def _con_deactivate_conv_tech_cap_and_availability(model: Model) -> None:
    for s, h, x in getattr(model, SET_SOLARTECHTUPLE):
        for t in getattr(model, SET_TIME):
            getattr(model, CON_CONVTECHCAPANDAVAILABILITY)[s, h, x, t].deactivate()


def _con_solar_area(
    model: Model,
    conv_techs: ConversionTechs,
    solar_data: SolarData,
    length_unit: LengthUnit,
) -> None:
    def __rule_solar_area(model, s, h, e):
        # Get parameters
        solar_area = solar_data.get_area(StageId(s), HubId(h), EcId(e)).to_float(
            unit=(length_unit**2)
        )
        # Calculate installed area
        installed_area = sum(
            getattr(model, VAR_TECHCAP)[s, h, x]
            for (s_, h_, x) in getattr(model, SET_SOLARTECHTUPLE)
            if s == s_
            if h == h_
            if EcId(e) == conv_techs.get_in_ec_main(TechId(x))
        )
        # Skip trivial constraint
        if isinstance(installed_area, int) and installed_area == 0:
            return Constraint.Skip
        # Set the constraint
        return installed_area <= solar_area

    setattr(
        model,
        CON_SOLARAREA,
        Constraint(
            getattr(model, SET_STAGE),
            getattr(model, SET_HUB),
            getattr(model, SET_SOLAREC),
            rule=__rule_solar_area,
        ),
    )
