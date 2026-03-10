"""ATES technology writer module. Writes out information from the ATES
technology submodule to files"""

import pandas as pd
from pyomo.core import Model, value

from ehubx.core import exceptions
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.hub_data import HubId
from ehubx.data.tech_data import TechId
from ehubx.data.time_series import TimeSeries
from ehubx.data.unit import (
    DimlessUnit,
    LengthUnit,
    MassUnit,
    PowerUnit,
    TemperatureUnit,
    TimeUnit,
)
from ehubx.data.value import Value
from ehubx.model import ates_tech_model
from ehubx.writer.common_writer import DfStBuilder, add_to_df_ts_hor


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "writ/ates_tech"
"""String identifying the ATES technology writer module for logging purposes"""

SOURCE: str = "ates_tech"
"""Display name for the ATES tech module in result files"""

ENTRY_ECEL: str = "Electricity ec"
"""Entry name for electricity ec in result files"""

ENTRY_ECHEAT: str = "Heating ec"
"""Entry name for heating ec in result files"""

ENTRY_ECCOOL: str = "Cooling ec"
"""Entry name for cooling ec in result files"""

ENTRY_FLUIDDENSITY: str = "Fluid density"
"""Entry name for fluid density in result files"""

ENTRY_FLUIDSPECHEATCAP: str = "Fluid specific heat capacity"
"""Entry name for fluid specific heat capacity in result files"""

ENTRY_AQUIFERSPECHEATCAP: str = "Aquifer specific heat capacity"
"""Entry name for aquifer specific heat capacity in result files"""

ENTRY_AQUIFERTHICKNESS: str = "Aquifer thickness"
"""Entry name for aquifer thickness in result files"""

ENTRY_AQUIFERHYDRAULCOND: str = "Aquifer hydraulic conductivity"
"""Entry name for aquifer hydraulic conductivity in result files"""

ENTRY_AQUIFERHYDRTRANS: str = "Aquifer hydraulic transmissivity"
"""Entry name for aquifer hydraulic transmissivity in result files"""

ENTRY_AQUIFERPOROSITY: str = "Aquifer porosity"
"""Entry name for aquifer porosity in result files"""

ENTRY_MAXDRAWDOWN: str = "Maximal drawdown"
"""Entry name for maximal drawdown in result files"""

ENTRY_MAXTEMPSPREADWARM: str = "Maximal temperature spread per warm well"
"""Entry name for maximal temperature spread per warm well in result files"""

ENTRY_MAXTEMPSPREADCOLD: str = "Maximal temperature spread per cold well"
"""Entry name for maximal temperature spread per cold well in result files"""

ENTRY_AVAILABLEAREA: str = "Available area"
"""Entry name for available aquifer area in result files"""

ENTRY_PHASEW2CSTART: str = "Phase start, warm to cold"
"""Entry name for phase start, warm to cold in result files"""

ENTRY_PHASEW2CEND: str = "Phase end, warm to cold"
"""Entry name for phase end, warm to cold in result files"""

ENTRY_PHASEW2CDURATION: str = "Phase duration, warm to cold"
"""Entry name for phase duration, warm to cold in result files"""

ENTRY_PHASEC2WSTART: str = "Phase start, cold to warm"
"""Entry name for phase start, cold to warm in result files"""

ENTRY_PHASEC2WEND: str = "Phase end, cold to warm"
"""Entry name for phase end, cold to warm in result files"""

ENTRY_PHASEC2WDURATION: str = "Phase duration, cold to warm"
"""Entry name for phase duration, cold to warm in result files"""

ENTRY_WELLRADIUS: str = "Well radius"
"""Entry name for well radius in result files"""

ENTRY_DARCYVELOCITY: str = "Darcy velocity"
"""Entry name for darcy velocity in result files"""

ENTRY_MAXPUMPRATEWARM: str = "Max pump rate per warm well"
"""Entry name for maximal pump rate per warm well in result files"""

ENTRY_MAXPUMPRATECOLD: str = "Max pump rate per cold well"
"""Entry name for maximal pump rate per cold well in result files"""

ENTRY_THERMRADWARM: str = "Thermal radius per warm well"
"""Entry name for thermal radius per warm well in result files"""

ENTRY_THERMRADCOLD: str = "Thermal radius per cold well"
"""Entry name for thermal radius per cold well in result files"""

ENTRY_WELLPAIRAREACALCMETHOD: str = "Well pair area calculation method"
"""Entry name for well pair area calculation method in result files"""

ENTRY_WELLPAIRAREA: str = "Well pair area"
"""Entry name for well pair area in result files"""

ENTRY_ELECPERENERGYHEAT: str = "Electricity consumption per heating energy"
"""Entry name for electricity consumption per heating energy in result files"""

ENTRY_ELECPERENERGYCOOL: str = "Electricity consumption per cooling energy"
"""Entry name for electricity consumption per cooling energy in result files"""

ENTRY_ELECPERFLOWHEAT: str = "Electricity consumption per warm-to-cold flow"
"""Entry name for electricity consumption per warm-to-cold flow in result
files"""

ENTRY_ELECPERFLOWCOOL: str = "Electricity consumption per cold-to-warm flow"
"""Entry name for electricity consumption per cold-to-warm flow in result
files"""

ENTRY_MAXHEATOVERCOOL: str = (
    "Maximal quotient of summed-up heating over "
    "cooling output energy (max_heat_over_cool)"
)

ENTRY_MAXCOOLOVERHEAT: str = (
    "Maximal quotient of summed-up cooling over "
    "heating output energy (max_heat_over_cool)"
)

ENTRY_AVAILABILITY: str = "Availability"
"""Entry name for availability of ATES Techs"""

ENTRY_MAXPOWDENSHT: str = "Maximal power density, heating"
"""Entry name for maximal power density of heating mode in result files"""

ENTRY_MAXPOWDENSCO: str = "Maximal power density, cooling"
"""Entry name for maximal power density of cooling mode in result files"""

ENTRY_CAPEXPERWELLPAIR: str = "CAPEX price per well pair"
"""Entry name for CAPEX price per well pair in result files"""

ENTRY_OPEXPERWELLPAIR: str = "OPEX price per well pair"
"""Entry name for OPEX price per well pair in result files"""

ENTRY_CO2PERWELLPAIR: str = "CO2 per well pair"
"""Entry name for embodied CO2 per well pair installation in result files"""

ENTRY_ATESTECHCAPSCHEDULE: str = "ATES tech capacity"
"""Entry name for ATES tech capacity per schedule in result files"""

ENTRY_ATESTECHNUMWELLPAIRS: str = "Number of well pairs"
"""Entry name for number of ATES well pairs per schedule in result files"""

ENTRY_ATESTECHELECSCHEDULE: str = "ATES tech electricity input"
"""Entry name for ATES tech electricity input per schedule in result files"""

ENTRY_ATESTECHHEATSCHEDULE: str = "ATES tech heating output"
"""Entry name for ATES tech heating output per schedule in result files"""

ENTRY_ATESTECHCOOLSCHEDULE: str = "ATES tech cooling output"
"""Entry name for ATES tech cooling output per schedule in result files"""

ENTRY_ATESTECHIN: str = "ATES tech input"
"""Entry name for ATES tech input in result files"""

ENTRY_ATESTECHOUT: str = "ATES tech output"
"""Entry name for ATES tech output in result files"""


def format_all(
    energy_system: EnergySystem,
    model: Model,
    df_st_builder: DfStBuilder,
    df_ts_hor: pd.DataFrame,
) -> None:
    # Tech-specific properties
    for tech_id in energy_system.ates_techs.ids_in_order:
        _format_tech(energy_system, model, tech_id, df_st_builder, df_ts_hor)
    # Hub-specific properties
    for hub_id in energy_system.hubs.ids_in_order:
        _format_hub(energy_system, model, hub_id, df_st_builder)


def _format_hub(
    energy_system: EnergySystem, model: Model, h: HubId, df_st_builder: DfStBuilder
) -> None:
    # Skip hub formating if no ates tech is allowed in this hub
    hub_has_ates_techs: bool = False
    for x in energy_system.ates_techs.ids:
        if h in energy_system.techs.get_allowed_hubs(x):
            hub_has_ates_techs = True
            break
    if not hub_has_ates_techs:
        return

    # Darcy groundwater velocity
    try:
        darcy_velo = energy_system.ates_data.get_darcy_velocity(h)
        df_st_builder.add_row(
            ENTRY_DARCYVELOCITY,
            darcy_velo,
            unit=(LengthUnit.M / TimeUnit.D),
            hub=h.key,
            source=SOURCE,
            in_res="input",
        )
    except exceptions.EhubXException:
        pass

    # Aquifer specific heat capacity
    try:
        aq_spec_heat_cap = energy_system.ates_data.get_specific_heat_capacity_rock(h)
        df_st_builder.add_row(
            ENTRY_AQUIFERSPECHEATCAP,
            aq_spec_heat_cap,
            unit=((PowerUnit.KW * TimeUnit.H) / (MassUnit.KG * TemperatureUnit.K)),
            hub=h.key,
            source=SOURCE,
            in_res="input",
        )
    except exceptions.EhubXException:
        pass

    # Aquifer thickness
    try:
        aq_thickness = energy_system.ates_data.get_thickness_aquifer(h)
        df_st_builder.add_row(
            ENTRY_AQUIFERTHICKNESS,
            aq_thickness,
            unit=LengthUnit.M,
            hub=h.key,
            source=SOURCE,
            in_res="input",
        )
    except exceptions.EhubXException:
        pass

    # Aquifer hydraulic conductivity
    try:
        aq_hydr_cond = energy_system.ates_data.get_hydraulic_conductivity_aquifer(h)
        df_st_builder.add_row(
            ENTRY_AQUIFERHYDRAULCOND,
            aq_hydr_cond,
            unit=(LengthUnit.M / TimeUnit.D),
            hub=h.key,
            source=SOURCE,
            in_res="input",
        )
    except exceptions.EhubXException:
        pass

    # Aquifer hydraulic transmissivity
    try:
        aq_hydr_trans = energy_system.ates_data.get_hydraulic_transmissivity_aquifer(h)
        df_st_builder.add_row(
            ENTRY_AQUIFERHYDRTRANS,
            aq_hydr_trans,
            unit=(LengthUnit.M**2 / TimeUnit.D),
            hub=h.key,
            source=SOURCE,
            in_res="input",
        )
    except exceptions.EhubXException:
        pass

    # Aquifer porosity
    try:
        aq_porosity = energy_system.ates_data.get_porosity_aquifer(h)
        df_st_builder.add_row(
            ENTRY_AQUIFERPOROSITY,
            aq_porosity,
            unit=DimlessUnit(),
            hub=h.key,
            source=SOURCE,
            in_res="input",
        )
    except exceptions.EhubXException:
        pass

    # Maximal drawdown
    try:
        max_drawdown = energy_system.ates_data.get_max_drawdown(h)
        df_st_builder.add_row(
            ENTRY_MAXDRAWDOWN,
            max_drawdown,
            unit=LengthUnit.M,
            hub=h.key,
            source=SOURCE,
            in_res="input",
        )
    except exceptions.EhubXException:
        pass

    # Maximal temperature spread per warm well
    try:
        max_temp_spread_warm = energy_system.ates_data.get_max_temperature_spread_warm(
            h
        )
        df_st_builder.add_row(
            ENTRY_MAXTEMPSPREADWARM,
            max_temp_spread_warm,
            unit=TemperatureUnit.K,
            hub=h.key,
            source=SOURCE,
            in_res="input",
        )
    except exceptions.EhubXException:
        pass

    # Maximal temperature spread per cold well
    try:
        max_temp_spread_cold = energy_system.ates_data.get_max_temperature_spread_cold(
            h
        )
        df_st_builder.add_row(
            ENTRY_MAXTEMPSPREADCOLD,
            max_temp_spread_cold,
            unit=TemperatureUnit.K,
            hub=h.key,
            source=SOURCE,
            in_res="input",
        )
    except exceptions.EhubXException:
        pass

    # Available area
    for s in energy_system.stages.ids_in_order:
        available_area = energy_system.ates_data.get_available_area(s, h)
        df_st_builder.add_row(
            ENTRY_AVAILABLEAREA,
            available_area,
            unit=(energy_system.length_unit**2),
            stage=s.key,
            hub=h.key,
            source=SOURCE,
            in_res="input",
        )

    # Phase start, warm to cold
    for i in energy_system.ates_data.get_schedule_ids(h):
        try:
            phase_start_w2c = energy_system.ates_data.get_phase_w2c_start(h, i)
            df_st_builder.add_row(
                ENTRY_PHASEW2CSTART,
                str(phase_start_w2c.key),
                hub=h.key,
                ates_schedule=i.key,
                source=SOURCE,
                in_res="input",
            )
        except exceptions.EhubXException:
            pass

    # Phase end, warm to cold
    for i in energy_system.ates_data.get_schedule_ids(h):
        try:
            phase_end_w2c = energy_system.ates_data.get_phase_w2c_end(h, i)
            df_st_builder.add_row(
                ENTRY_PHASEW2CEND,
                str(phase_end_w2c.key),
                hub=h.key,
                ates_schedule=i.key,
                source=SOURCE,
                in_res="input",
            )
        except exceptions.EhubXException:
            pass

    # Phase duration, warm to cold
    for i in energy_system.ates_data.get_schedule_ids(h):
        try:
            phase_duration_w2c = energy_system.ates_data.get_phase_duration_w2c(
                h, i, energy_system.times
            )
            df_st_builder.add_row(
                ENTRY_PHASEW2CDURATION,
                phase_duration_w2c,
                unit=TimeUnit.D,
                hub=h.key,
                ates_schedule=i.key,
                source=SOURCE,
                in_res="input",
            )
        except exceptions.EhubXException:
            pass

    # Phase start, cold to warm
    for i in energy_system.ates_data.get_schedule_ids(h):
        try:
            phase_start_c2w = energy_system.ates_data.get_phase_c2w_start(h, i)
            df_st_builder.add_row(
                ENTRY_PHASEC2WSTART,
                str(phase_start_c2w.key),
                hub=h.key,
                ates_schedule=i.key,
                source=SOURCE,
                in_res="input",
            )
        except exceptions.EhubXException:
            pass

    # Phase end, cold to warm
    for i in energy_system.ates_data.get_schedule_ids(h):
        try:
            phase_end_c2w = energy_system.ates_data.get_phase_c2w_end(h, i)
            df_st_builder.add_row(
                ENTRY_PHASEC2WEND,
                str(phase_end_c2w.key),
                hub=h.key,
                ates_schedule=i.key,
                source=SOURCE,
                in_res="input",
            )
        except exceptions.EhubXException:
            pass

    # Phase duration, cold to warm
    for i in energy_system.ates_data.get_schedule_ids(h):
        try:
            phase_duration_c2w = energy_system.ates_data.get_phase_duration_c2w(
                h, i, energy_system.times
            )
            df_st_builder.add_row(
                ENTRY_PHASEC2WDURATION,
                phase_duration_c2w,
                unit=TimeUnit.D,
                hub=h.key,
                ates_schedule=i.key,
                source=SOURCE,
                in_res="input",
            )
        except exceptions.EhubXException:
            pass


def _format_tech(
    energy_system: EnergySystem,
    model: Model,
    x: TechId,
    df_st_builder: DfStBuilder,
    df_ts_hor: pd.DataFrame,
) -> None:
    # ec_el
    ec_el = energy_system.ates_techs.get_ec_el(x)
    df_st_builder.add_row(
        ENTRY_ECEL, ec_el.key, tech=x.key, source=SOURCE, in_res="input"
    )

    # ec_heat
    ec_heat = energy_system.ates_techs.get_ec_ht(x)
    df_st_builder.add_row(
        ENTRY_ECHEAT, ec_heat.key, tech=x.key, source=SOURCE, in_res="input"
    )

    # ec_cool
    ec_cool = energy_system.ates_techs.get_ec_co(x)
    df_st_builder.add_row(
        ENTRY_ECCOOL, ec_cool.key, tech=x.key, source=SOURCE, in_res="input"
    )

    # Well radius
    try:
        well_radius = energy_system.ates_techs.get_well_radius(x)
        df_st_builder.add_row(
            ENTRY_WELLRADIUS,
            well_radius,
            unit=LengthUnit.M,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )
    except exceptions.EhubXException:
        pass

    # Fluid density
    fluid_density = energy_system.ates_techs.get_density_fluid(x)
    df_st_builder.add_row(
        ENTRY_FLUIDDENSITY,
        fluid_density,
        unit=(MassUnit.KG / (LengthUnit.M**3)),
        tech=x.key,
        source=SOURCE,
        in_res="input",
    )

    # Fluid specific heat capacity
    fluid_spec_heat_cap = energy_system.ates_techs.get_specific_heat_capacity_fluid(x)
    df_st_builder.add_row(
        ENTRY_FLUIDSPECHEATCAP,
        fluid_spec_heat_cap,
        unit=((PowerUnit.KW * TimeUnit.H) / (MassUnit.KG * TemperatureUnit.K)),
        tech=x.key,
        source=SOURCE,
        in_res="input",
    )

    # Maximal pump rate per warm well
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            for i in energy_system.ates_data.get_schedule_ids(h):
                max_rate = energy_system.ates_techs.get_max_pump_rate_per_warm_well(
                    s, h, x, i, energy_system.ates_data
                )
                df_st_builder.add_row(
                    ENTRY_MAXPUMPRATEWARM,
                    max_rate,
                    unit=(LengthUnit.M**3 / TimeUnit.H),
                    stage=s.key,
                    hub=h.key,
                    tech=x.key,
                    ates_schedule=i.key,
                    source=SOURCE,
                    in_res="input",
                )

    # Maximal pump rate per cold well
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            for i in energy_system.ates_data.get_schedule_ids(h):
                max_rate = energy_system.ates_techs.get_max_pump_rate_per_cold_well(
                    s, h, x, i, energy_system.ates_data
                )
                df_st_builder.add_row(
                    ENTRY_MAXPUMPRATECOLD,
                    max_rate,
                    unit=(LengthUnit.M**3 / TimeUnit.H),
                    stage=s.key,
                    hub=h.key,
                    tech=x.key,
                    ates_schedule=i.key,
                    source=SOURCE,
                    in_res="input",
                )

    # Well pair area calculation method
    calc_method = energy_system.ates_techs.get_well_pair_area_calc_method(x)
    df_st_builder.add_row(
        ENTRY_WELLPAIRAREACALCMETHOD,
        calc_method.value,
        tech=x.key,
        source=SOURCE,
        in_res="input",
    )

    # Electricity consumption per heating energy
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            elec_per_en_heat = energy_system.ates_techs.get_elec_per_energy_heat(
                s, h, x, energy_system.ates_data
            )
            df_st_builder.add_row(
                ENTRY_ELECPERENERGYHEAT,
                elec_per_en_heat,
                unit=DimlessUnit(),
                stage=s.key,
                hub=h.key,
                tech=x.key,
                source=SOURCE,
                in_res="input",
            )

    # Electricity consumption per cooling energy
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            elec_per_en_cool = energy_system.ates_techs.get_elec_per_energy_cool(
                s, h, x, energy_system.ates_data
            )
            df_st_builder.add_row(
                ENTRY_ELECPERENERGYCOOL,
                elec_per_en_cool,
                unit=DimlessUnit(),
                stage=s.key,
                hub=h.key,
                tech=x.key,
                source=SOURCE,
                in_res="input",
            )

    # Maximal heating over cooling energy quotient
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            for i in energy_system.ates_data.get_schedule_ids(h):
                max_heat_over_cool = energy_system.ates_techs.get_max_heat_over_cool(
                    s, h, x, i
                )
                df_st_builder.add_row(
                    ENTRY_MAXHEATOVERCOOL,
                    max_heat_over_cool,
                    unit=DimlessUnit(),
                    stage=s.key,
                    hub=h.key,
                    tech=x.key,
                    ates_schedule=i.key,
                    source=SOURCE,
                    in_res="input",
                )

    # Maximal cooling over heating energy quotient
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            for i in energy_system.ates_data.get_schedule_ids(h):
                max_cool_over_heat = energy_system.ates_techs.get_max_cool_over_heat(
                    s, h, x, i
                )
                df_st_builder.add_row(
                    ENTRY_MAXCOOLOVERHEAT,
                    max_cool_over_heat,
                    unit=DimlessUnit(),
                    stage=s.key,
                    hub=h.key,
                    tech=x.key,
                    ates_schedule=i.key,
                    source=SOURCE,
                    in_res="input",
                )

    # Thermal radii and well pair area
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            for i in energy_system.ates_data.get_schedule_ids(h):
                # Thermal radius per warm well
                therm_rad_warm = (
                    energy_system.ates_techs.get_thermal_radius_per_warm_well(
                        s, h, x, i, energy_system.ates_data, energy_system.times
                    )
                )
                df_st_builder.add_row(
                    ENTRY_THERMRADWARM,
                    therm_rad_warm,
                    unit=energy_system.length_unit,
                    stage=s.key,
                    hub=h.key,
                    tech=x.key,
                    ates_schedule=i.key,
                    source=SOURCE,
                    in_res="input",
                )
                # Thermal radius per cold well
                therm_rad_cold = (
                    energy_system.ates_techs.get_thermal_radius_per_cold_well(
                        s, h, x, i, energy_system.ates_data, energy_system.times
                    )
                )
                df_st_builder.add_row(
                    ENTRY_THERMRADCOLD,
                    therm_rad_cold,
                    unit=energy_system.length_unit,
                    stage=s.key,
                    hub=h.key,
                    tech=x.key,
                    ates_schedule=i.key,
                    source=SOURCE,
                    in_res="input",
                )
                # Area per well pair
                well_pair_area = energy_system.ates_techs.calc_area_per_well_pair(
                    therm_rad_warm, therm_rad_cold, calc_method
                )
                df_st_builder.add_row(
                    ENTRY_WELLPAIRAREA,
                    well_pair_area,
                    unit=(energy_system.length_unit**2),
                    stage=s.key,
                    hub=h.key,
                    tech=x.key,
                    ates_schedule=i.key,
                    source=SOURCE,
                    in_res="input",
                )

    # Maximal power densities
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            for i in energy_system.ates_data.get_schedule_ids(h):
                max_pow_dens_ht, max_pow_dens_co = (
                    energy_system.ates_techs.calc_max_power_densities(
                        s, h, x, i, energy_system.ates_data, energy_system.times
                    )
                )
                df_st_builder.add_row(
                    ENTRY_MAXPOWDENSHT,
                    max_pow_dens_ht,
                    unit=(energy_system.power_unit / (energy_system.length_unit**2)),
                    stage=s.key,
                    hub=h.key,
                    tech=x.key,
                    ates_schedule=i.key,
                    source=SOURCE,
                    in_res="input",
                )
                df_st_builder.add_row(
                    ENTRY_MAXPOWDENSCO,
                    max_pow_dens_co,
                    unit=(energy_system.power_unit / (energy_system.length_unit**2)),
                    stage=s.key,
                    hub=h.key,
                    tech=x.key,
                    ates_schedule=i.key,
                    source=SOURCE,
                    in_res="input",
                )

    # availability
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            for i in energy_system.ates_data.get_schedule_ids(h):
                availability = energy_system.ates_techs.get_availability(s, h, x, i)
                if availability.has_values:
                    add_to_df_ts_hor(
                        df_ts_hor,
                        energy_system.times,
                        ENTRY_AVAILABILITY,
                        availability,
                        unit=DimlessUnit(),
                        stage=s.key,
                        hub=h.key,
                        tech=x.key,
                        ates_schedule=i.key,
                        source=SOURCE,
                        in_res="input",
                    )
                if not availability.has_values:
                    availability_def = availability.def_value
                    assert availability_def is not None
                    df_st_builder.add_row(
                        ENTRY_AVAILABILITY,
                        availability_def,
                        unit=DimlessUnit(),
                        stage=s.key,
                        hub=h.key,
                        tech=x.key,
                        ates_schedule=i.key,
                        source=SOURCE,
                        in_res="input",
                    )

    # capex_per_well_pair
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        capex_per_well_pair = energy_system.ates_techs.get_capex_per_well_pair(s, x)
        df_st_builder.add_row(
            ENTRY_CAPEXPERWELLPAIR,
            capex_per_well_pair,
            unit=energy_system.currency_unit,
            stage=s.key,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # opex_per_well_pair
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        opex_per_well_pair = energy_system.ates_techs.get_opex_per_well_pair(s, x)
        df_st_builder.add_row(
            ENTRY_OPEXPERWELLPAIR,
            opex_per_well_pair,
            unit=energy_system.currency_unit,
            stage=s.key,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # co2_per_well_pair
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        co2_per_well_pair = energy_system.ates_techs.get_co2_per_well_pair(s, x)
        df_st_builder.add_row(
            ENTRY_CO2PERWELLPAIR,
            co2_per_well_pair,
            unit=energy_system.mass_unit,
            stage=s.key,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # ATES area per schedule
    var_cap = getattr(model, ates_tech_model.VAR_ATESTECHCAPSCHEDULE)
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            for i in energy_system.ates_data.get_schedule_ids(h):
                cap_fl = value(var_cap[s.key, h.key, x.key, i.key], exception=False)
                if cap_fl is None:
                    continue
                cap = Value(cap_fl, unit=(energy_system.length_unit**2))
                df_st_builder.add_row(
                    ENTRY_ATESTECHCAPSCHEDULE,
                    cap,
                    unit=(energy_system.length_unit**2),
                    stage=s.key,
                    hub=h.key,
                    tech=x.key,
                    ates_schedule=i.key,
                    source=SOURCE,
                    in_res="result",
                )

    # Number of well pairs per schedule
    var_pairs = getattr(model, ates_tech_model.VAR_ATESTECHNUMWELLPAIRS)
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            for i in energy_system.ates_data.get_schedule_ids(h):
                pairs_fl = value(var_pairs[s.key, h.key, x.key, i.key], exception=False)
                if pairs_fl is None:
                    continue
                pairs = Value(pairs_fl)
                df_st_builder.add_row(
                    ENTRY_ATESTECHNUMWELLPAIRS,
                    pairs,
                    unit=DimlessUnit(),
                    stage=s.key,
                    hub=h.key,
                    tech=x.key,
                    ates_schedule=i.key,
                    source=SOURCE,
                    in_res="result",
                )

    # ATES electricity per schedule
    var_elec = getattr(model, ates_tech_model.VAR_ATESTECHELECSCHEDULE)
    flow_unit = energy_system.power_unit / TimeUnit.H
    for s_, h_, x_, i_ in getattr(model, ates_tech_model.SET_ATESTECHTUPLESCHEDULE):
        elec = TimeSeries()
        for t in energy_system.times.ids:
            elec_fl = value(var_elec[s_, h_, x_, i_, t.key_as_int], exception=False)
            if elec_fl is None:
                continue
            elec.set_value(t, Value(elec_fl, unit=flow_unit))
        add_to_df_ts_hor(
            df_ts_hor,
            energy_system.times,
            ENTRY_ATESTECHELECSCHEDULE,
            elec,
            unit=flow_unit,
            stage=s_,
            hub=h_,
            tech=x_,
            ates_schedule=i_,
            source=SOURCE,
            in_res="result",
        )

    # ATES heating per schedule
    var_heat = getattr(model, ates_tech_model.VAR_ATESTECHHEATSCHEDULE)
    for s_, h_, x_, i_ in getattr(model, ates_tech_model.SET_ATESTECHTUPLESCHEDULE):
        heat = TimeSeries()
        for t in energy_system.times.ids:
            heat_fl = value(var_heat[s_, h_, x_, i_, t.key_as_int], exception=False)
            if heat_fl is None:
                continue
            heat.set_value(t, Value(heat_fl, unit=flow_unit))
        add_to_df_ts_hor(
            df_ts_hor,
            energy_system.times,
            ENTRY_ATESTECHHEATSCHEDULE,
            heat,
            unit=flow_unit,
            stage=s_,
            hub=h_,
            tech=x_,
            ates_schedule=i_,
            source=SOURCE,
            in_res="result",
        )

    # ATES cooling per schedule
    var_cool = getattr(model, ates_tech_model.VAR_ATESTECHCOOLSCHEDULE)
    for s_, h_, x_, i_ in getattr(model, ates_tech_model.SET_ATESTECHTUPLESCHEDULE):
        cool = TimeSeries()
        for t in energy_system.times.ids:
            cool_fl = value(var_cool[s_, h_, x_, i_, t.key_as_int], exception=False)
            if cool_fl is None:
                continue
            cool.set_value(t, Value(cool_fl, unit=flow_unit))
        add_to_df_ts_hor(
            df_ts_hor,
            energy_system.times,
            ENTRY_ATESTECHCOOLSCHEDULE,
            cool,
            unit=flow_unit,
            stage=s_,
            hub=h_,
            tech=x_,
            ates_schedule=i_,
            source=SOURCE,
            in_res="result",
        )

    # ATES input
    var_in = getattr(model, ates_tech_model.VAR_ATESTECHIN)
    for s_, h_, x_, e_ in getattr(model, ates_tech_model.SET_ATESTECHIN):
        ates_in = TimeSeries()
        for t in energy_system.times.ids:
            in_fl = value(var_in[s_, h_, x_, e_, t.key_as_int], exception=False)
            if in_fl is None:
                continue
            ates_in.set_value(t, Value(in_fl, unit=flow_unit))
        add_to_df_ts_hor(
            df_ts_hor,
            energy_system.times,
            ENTRY_ATESTECHIN,
            ates_in,
            unit=flow_unit,
            stage=s_,
            hub=h_,
            tech=x_,
            ec=e_,
            source=SOURCE,
            in_res="result",
        )

    # ATES output
    var_out = getattr(model, ates_tech_model.VAR_ATESTECHOUT)
    for s_, h_, x_, e_ in getattr(model, ates_tech_model.SET_ATESTECHOUT):
        ates_out = TimeSeries()
        for t in energy_system.times.ids:
            out_fl = value(var_out[s_, h_, x_, e_, t.key_as_int], exception=False)
            if out_fl is None:
                continue
            ates_out.set_value(t, Value(out_fl, unit=flow_unit))
        add_to_df_ts_hor(
            df_ts_hor,
            energy_system.times,
            ENTRY_ATESTECHOUT,
            ates_out,
            unit=flow_unit,
            stage=s_,
            hub=h_,
            tech=x_,
            ec=e_,
            source=SOURCE,
            in_res="result",
        )
