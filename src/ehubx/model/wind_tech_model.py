"""Wind technology submodel"""

import math
from datetime import datetime

from pyomo.core import Any, Binary, Constraint, Model, NonNegativeReals, Param, Set, Var

from ehubx.core import common, logging
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId
from ehubx.data.tech_data import TechId
from ehubx.data.time_data import TimeId
from ehubx.data.unit import DimlessUnit, LengthUnit, PowerUnit, TimeUnit
from ehubx.data.wind_data import TerrainId, WindGroupId, adjust_speed_for_height_roughness
from ehubx.data.wind_tech_data import WindTechs
from ehubx.model.common import calculate_crf
from ehubx.model.ec_model import get_ec_model_unit
from ehubx.model.stage_model import SET_STAGE
from ehubx.model.tech_model import (
    CON_TECHCOSTCAPEX,
    CON_TECHCOSTOPEXCAP,
    SET_TECH,
    SET_TECHTUPLE,
    VAR_TECHCAP,
    VAR_TECHCAPINSTL,
    VAR_TECHCOSTCAPEX,
    VAR_TECHCOSTOPEXCAP,
    VAR_YTECHCAPINSTL,
    VAR_YTECHUSED,
    get_model_cap_unit,
)
from ehubx.model.times_model import SET_TIME


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/wind_tech"
"""String identifying the wind technology model for logging purposes"""

SET_WINDTECH: str = "S_WindTech"
"""Name of set for all wind techs"""

SET_WINDGROUPS: str = "S_WindGroups"
"""Name of set for all wind groups (used for wind speed profiles)"""

SET_WINDSUBGROUP: str = "S_WindSubGroup"
"""Name of set for all (wind_group, terrain) sub-group tuples.
Each wind group is split into terrain sub-groups so that capacity, output,
area, and costs are tracked separately per terrain type within a group.
When no terrain area data is available each wind group forms its own
singleton sub-group (terrain key == wind group key)."""

SET_WINDTECHTUPLE: str = "S_WindTechTuple"
"""Name of set for all wind tech tuples (stage, hub, ec)"""

VAR_WINDTECHCAPINGROUP: str = "V_WindTechCapInGroup"
"""Name of variable for wind tech capacity in (wind_group, terrain) sub-group"""

VAR_WINDTECHOUT: str = "V_WindTechOut"
"""Name of variable for wind tech outputs"""

VAR_WINDTECHOUTINGROUP: str = "V_WindTechOutInGroup"
"""Name of variable for wind tech outputs in (wind_group, terrain) sub-group"""

PAR_WINDTECHEC: str = "P_WindTechEc"
"""Name of parameter specifying the ec produced by wind techs"""

CON_WINDTECHCAP: str = "C_WindTechCap"
"""Name of constraint setting capacity as sum over all sub-groups"""

CON_WINDTECHCAPINGROUP: str = "C_WindTechCapInGroup"
"""Name of constraint respecting the tech capacity for wind techs in sub-group"""

CON_WINDTECHUSED: str = "C_WindTechUsed"
"""Name of constraint determing tech usage of wind techs"""

VAR_WINDTECHCURT: str = "V_WindTechCurt"
"""Wind curtailment (unused but available power) per (wind_group, terrain) sub-group"""

PAR_WINDTECHCURTMAXREL: str = "P_WindTechCurtMaxRel"
"""Max curtailment share (0..1) per (s,h,x)"""

PAR_WINDTECHCURTMINREL: str = "P_WindTechCurtMinRel"
"""Min curtailment share (0..1) per (s,h,x)"""

CON_WINDTECHOUTPUTSUMOVERGROUPS: str = "C_WindTechOutputSumOverGroups"
"""Wind tech output is equal to the sum of its output in all sub-groups"""

CON_WINDTECHCURTMAX: str = "C_WindTechCurtMax"
"""Curtailment upper bound"""

CON_WINDTECHCURTMIN: str = "C_WindTechCurtMin"
"""Curtailment lower bound"""

SET_WINDHUBTUPLE: str = "S_WindHubTuple"
"""(stage, hub) tuples where wind techs exist"""

PAR_WINDTECHAREAPERTURBINE: str = "P_WindTechAreaPerTurbine"
"""Area required per turbine in model area units"""

CON_WINDAREACAP: str = "C_WindAreaCap"
"""Area capacity constraint per (stage, hub, wind_group, terrain)"""

CON_WINDTECHGROUPALLOWED: str = "C_WindTechGroupAllowed"
"""Force zero sub-group capacity for disallowed (tech, wind_group, terrain) sub-groups"""

VAR_WINDTECHCAPINSTLGROUP: str = "V_WindTechCapInstlInGroup"
"""New capacity installed in a specific (wind_group, terrain) sub-group at a given stage"""

CON_WINDTECHCAPINSTLGROUPSUM: str = "C_TechCapInstlGroupSum"
"""V_TechCapInstl[s,h,x] == sum_{(w,terrain)} V_WindTechCapInstlInGroup[s,h,x,w,terrain]"""

CON_WINDTECHCAPINGROUPMIN: str = "C_WindTechCapInGroupMin"
"""Sub-group stickiness: capacity in (w,terrain) >= sum of within-lifetime installs in that sub-group"""

CON_WINDAREAINSTLCAP: str = "C_WindAreaInstlCap"
"""Area constraint at installation time per (wind_group, terrain) sub-group"""

PAR_WINDTECHPAVAIL: str = "P_WindTechPAvail"
"""Available power capacity factor per (s, x, wind_group, terrain, t)"""

PAR_WINDTECHCP: str = "P_WindTechCp"
"""Power coefficient Cp per wind tech"""

PAR_WINDTECHROTORDIAM: str = "P_WindTechRotorDiam"
"""Rotor diameter (m) per wind tech"""

PAR_WINDTERRAINCAPEXCAP: str = "P_WindTerrainCapexCap"
"""Terrain multiplier for capex_per_cap indexed by (wind_group, terrain)"""

PAR_WINDTERRAINOPEXCAP: str = "P_WindTerrainOpexCap"
"""Terrain multiplier for opex_per_cap indexed by (wind_group, terrain)"""

PAR_WINDTERRAINCAPEXONE: str = "P_WindTerrainCapexOne"
"""Terrain multiplier for one_time_capex indexed by (wind_group, terrain)"""

PAR_WINDTERRAINOPEXONE: str = "P_WindTerrainOpexOne"
"""Terrain multiplier for one_time_opex indexed by (wind_group, terrain)"""

CON_WINDTERRAINCOSTSTCAPEX: str = "C_WindTerrainCostCapex"
"""Terrain-adjusted CAPEX constraint for wind techs (replaces C_TechCostCapex)"""

CON_WINDTERRAINCOSTSTOPEXCAP: str = "C_WindTerrainCostOpexCap"
"""Terrain-adjusted OPEX constraint for wind techs (replaces C_TechCostOpexCap)"""

VAR_YWINDTECHCAPINSTLGROUP: str = "V_YWindTechCapInstlGroup"
"""Binary: new capacity installed in this (wind_group, terrain) sub-group at this stage"""

VAR_YWINDTECHUSEDGROUP: str = "V_YWindTechUsedGroup"
"""Binary: cumulative capacity present in this (wind_group, terrain) sub-group"""

CON_YWINDTECHCAPINSTLGROUP: str = "C_YWindTechCapInstlGroup"
"""BigM: V_WindTechCapInstlInGroup <= bigM * V_YWindTechCapInstlGroup"""

CON_YWINDTECHUSEDGROUP: str = "C_YWindTechUsedGroup"
"""BigM: V_WindTechCapInGroup <= bigM * V_YWindTechUsedGroup"""

AIR_DENSITY_KG_M3: float = 1.225
"""Assumed constant air density (kg/m^3)."""



_TI_SELECTION_LOGGED: set[tuple] = set()
"""Remember which TI source selections were already logged to avoid log spam."""
# -------------------- #
#       Helper         #
# -------------------- #
def _theoretical_fixed_cp_power_watt(
    v: float,
    v_in: float,
    v_out: float,
    p_rated_w: float,
    rotor_diameter_m: float,
    cp: float,
    rho: float,
) -> float:
    # TODO: add more info and make the variable names easier to understand.
    # remove the unit from the variable name
    """
    Ideal wind turbine power curve evaluated at a single wind speed, based on
    theoretical formulation with a fixed power coefficient. The power is computed as:

        P(v) = 0 if v <= 0, v < v_in, or v >= v_out
        P(v) = min(P_rated, 0.5 * rho * A * Cp * v^3)   otherwise

    where A = pi * (rotor_diameter_m / 2)^2 is the rotor swept area [m^2].

    :param v: Wind speed [m/s]
    :param v_in: Cut-in wind speed [m/s]; below this the turbine is offline
    :param v_out: Cut-out wind speed [m/s]; at or above this the turbine shuts down
    :param p_rated_w: Rated (nameplate) power of the turbine [W]
    :param rotor_diameter_m: Rotor diameter [m]
    :param cp: Power coefficient [-]; typical values 0.30-0.50
    :param rho: Air density [kg/m^3]
    :return: Turbine power output [W]
    """

    if v <= 0.0:
        return 0.0
    # if v < v_in:
    #     return 0.0
    # Safety Buffers
    # Add tiny tolerance (0.1 m/s) to cut-in speed
    # Prevent'on-the-edge' wind speeds from flipping to 0 due to rounding
    if v < (v_in - 0.1):
        return 0.0
    if v >= v_out:
        return 0.0

    r = 0.5 * rotor_diameter_m
    A = math.pi * r * r  # m^2
    p = 0.5 * rho * A * cp * (v**3)  # W
    return min(p_rated_w, max(0.0, p))


def _power_with_turb_intensity(
    v_mean: float,
    turb_intensity: float,
    v_in: float,
    v_out: float,
    p_rated: float,
    rotor_diameter_m: float,
    cp: float,
    rho: float,
    dv: float = 0.25,
    n_sigma: float = 6.0,
    sigma_floor: float = 0.05,
) -> float:
    """
    Expected turbine power E[P(V)] accounting for wind speed variability due to
    turbulence intensity, using discrete Gaussian-kernel integration.

    Wind speed V is modelled as approximately normally distributed:

        V ~ N(v_mean, sigma^2),   sigma = max(turb_intensity * v_mean, sigma_floor)

    The expected power is approximated over a uniform grid of wind speed samples
    v_i in [0, v_max] with spacing dv:

        E[P(V)] ~= sum_i [ w_i * P(v_i) ] / sum_i w_i
        w_i = exp(-0.5 * ((v_i - v_mean) / sigma)^2)

    where P(v_i) is evaluated using :func:`_theoretical_fixed_cp_power_watt`.
    If v_mean <= 0 or turb_intensity <= 0, the deterministic power curve is
    used directly (no Gaussian smearing needed).

    :param v_mean: Mean wind speed [m/s]
    :param turb_intensity: Turbulence intensity [-]; ratio of wind speed standard
        deviation to mean (sigma_v / v_mean); typical values 0.05-0.20
    :param v_in: Cut-in wind speed [m/s]
    :param v_out: Cut-out wind speed [m/s]
    :param p_rated: Rated turbine power [W]
    :param rotor_diameter_m: Rotor diameter [m]
    :param cp: Power coefficient [-]
    :param rho: Air density [kg/m^3]
    :param dv: Grid spacing for numerical integration [m/s] (default 0.25)
    :param n_sigma: Integration range as multiple of sigma (default 6.0)
    :param sigma_floor: Minimum sigma to avoid a degenerate Gaussian [m/s]
        (default 0.05)
    :return: Expected turbine power output [W]
    """

    if turb_intensity is None:
        turb_intensity = 0.0
    turb_intensity = max(0.0, float(turb_intensity))

    # if v_mean or TI <=0, the function will return 0
    if v_mean <= 0.0 or turb_intensity <= 0.0:
        return _theoretical_fixed_cp_power_watt(
            v_mean, v_in, v_out, p_rated, rotor_diameter_m, cp, rho
        )

    sigma = max(turb_intensity * v_mean, sigma_floor)

    # choose integration range wide enough so truncation is small
    v_min = 0.0
    v_max = max(v_out + 2.0, v_mean + n_sigma * sigma)

    # build grid
    n = int(math.ceil((v_max - v_min) / dv)) + 1

    num = 0.0
    den = 0.0

    for i in range(n):
        v = v_min + i * dv

        # Gaussian kernel weight around v_mean
        z = (v - v_mean) / sigma
        w = math.exp(-0.5 * z * z)

        den += w
        num += w * _theoretical_fixed_cp_power_watt(
            v, v_in, v_out, p_rated, rotor_diameter_m, cp, rho
        )

    if den <= 0.0:
        return _theoretical_fixed_cp_power_watt(
            v_mean, v_in, v_out, p_rated, rotor_diameter_m, cp, rho
        )

    return max(0.0, num / den)


def _roughness_based_turbulence_intensity(hub_height_m: float, rough_m: float) -> float:
    """
    Fixed turbulence intensity derived from hub height and terrain roughness.
    """
    if rough_m > 0.0 and hub_height_m > rough_m:
        return max(0.0, 1.0 / math.log(hub_height_m / rough_m))
    return 0.0


def _get_turbulence_intensity(
    system: EnergySystem,
    s: str,
    w: str,
    t: int,
    hub_height_m: float,
    rough_m: float,
) -> float:
    """
    Resolve turbulence intensity using the supported precedence:
    1. Time-series TI from wind_turbulence_intensity_profile.csv
    2. Fixed TI from wind_turbulence_intensity_fixed.csv
    3. Roughness-derived TI from hub height and terrain roughness
    """
    stage_id = StageId(s)
    wind_group_id = WindGroupId(w)
    time_id = TimeId(t)

    ti_profile = system.wind_data.get_turbulence_intensity_profile(stage_id, wind_group_id)
    if ti_profile is not None:
        log_key = ("timeseries", s, w)
        if log_key not in _TI_SELECTION_LOGGED:
            _TI_SELECTION_LOGGED.add(log_key)
            logging.log_file(
                f"Using time-series turbulence intensity from wind_turbulence_intensity_profile.csv "
                f"for stage '{s}', wind group '{w}'",
                module=LOG_MODULE_STR,
            )
        return max(0.0, ti_profile.get_value(time_id).to_float(DimlessUnit()))

    fixed_ti = system.wind_data.get_fixed_turbulence_intensity(stage_id, wind_group_id)
    if fixed_ti is not None:
        log_key = ("fixed", s, w)
        if log_key not in _TI_SELECTION_LOGGED:
            _TI_SELECTION_LOGGED.add(log_key)
            logging.log_file(
                f"Using fixed turbulence intensity from wind_turbulence_intensity_fixed.csv for stage '{s}', wind group '{w}'",
                module=LOG_MODULE_STR,
            )
        return max(0.0, fixed_ti.to_float(DimlessUnit()))

    log_key = ("roughness", w, rough_m, hub_height_m)
    if log_key not in _TI_SELECTION_LOGGED:
        _TI_SELECTION_LOGGED.add(log_key)
        logging.log_file(
            f"Using roughness-derived turbulence intensity for wind group '{w}' "
            f"(hub height={hub_height_m:g} m, roughness={rough_m:g} m)",
            module=LOG_MODULE_STR,
        )
    return _roughness_based_turbulence_intensity(hub_height_m, rough_m)


## TODO: add another function to calculte wind power from power curve
# _capacity_factor_from_power_curve(...)


def build(model: Model, system: EnergySystem) -> None:
    """
    Builds the wind technology submodel. For a mathematical description
    in thorough detail, please refer to the section 'Wind technology model' in the
    documentation.

    :param model: Pyomo model
    :type model: Model
    :param system: Energy system data
    :type system: EnergySystem
    """
    # Start measuring build time
    start = datetime.now()
    # Build
    _build_base(model, system)
    # Log
    elapsed = datetime.now() - start
    logging.log_file(
        f"Built wind tech module. Elapsed time: {int(elapsed.total_seconds())}s",
        module=LOG_MODULE_STR,
    )


def _build_base(
    model: Model,
    system: EnergySystem,
) -> None:
    """Build the base wind technology model with core sets, parameters,
    variables, and constraints.

    This function defines the fundamental components of the wind technology
    model, including:
    - Sets for wind technologies, wind groups, terrain sub-groups, and relevant tuples.
    - Parameters for area per turbine, available power, power coefficient,
        rotor diameter, and curtailment bounds.
    - Variables for wind tech capacity in sub-group, output, output in sub-group,
        and curtailment.
    - Constraints to ensure consistency between outputs, capacities, usage,
        curtailment bounds, and area capacity.
    """
    # Extract data from modules
    wind_techs: WindTechs = system.wind_techs
    # [SET] Wind techs
    setattr(
        model,
        SET_WINDTECH,
        Set(
            within=getattr(model, SET_TECH), initialize=[x.key for x in wind_techs.ids]
        ),
    )

    # [SET] Wind tech tuples
    setattr(
        model,
        SET_WINDTECHTUPLE,
        Set(
            within=getattr(model, SET_TECHTUPLE),
            initialize=[
                (s, h, x)
                for (s, h, x) in getattr(model, SET_TECHTUPLE)
                if TechId(x) in wind_techs.ids
            ],
        ),
    )

    # [SET] (stage, hub) tuples for which at least one wind tech exists
    setattr(
        model,
        SET_WINDHUBTUPLE,
        Set(
            within=Any,
            dimen=2,
            initialize=sorted(
                {(s, h) for (s, h, x) in getattr(model, SET_WINDTECHTUPLE)}
            ),
        ),
    )

    # [SET] Wind groups (for wind speed profiles - no terrain dimension)
    setattr(
        model,
        SET_WINDGROUPS,
        Set(
            within=Any,
            initialize=[w.key for w in system.wind_data.get_wind_groups()],
        ),
    )

    # [SET] (wind_group, terrain) sub-groups.
    # When terrain area fractions are defined each wind group is split into one
    # sub-group per terrain type (e.g. W1/Alps, W1/Jura, W1/Plateau). When no
    # terrain areas are available each wind group forms a singleton sub-group
    # with terrain key == wind group key (degenerate fallback).
    _subgroups = [
        (w.key, terrain.key)
        for w in system.wind_data.get_wind_groups()
        for terrain in system.wind_data.get_terrain_fracs_for_group(w)
    ]
    if not _subgroups:
        _subgroups = [(w.key, w.key) for w in system.wind_data.get_wind_groups()]
    setattr(
        model,
        SET_WINDSUBGROUP,
        Set(within=Any, dimen=2, initialize=_subgroups),
    )

    # [PAR] Area per turbine (converted to model area unit, e.g. m^2)
    # TODO: the calculation would be simplier if make this value as aera
    # per pwoer capacity (e.g. m2/kW) -> not prio
    # DB: Btw, I kind of disagree with that suggestion.
    area_unit = LengthUnit.M * LengthUnit.M
    setattr(
        model,
        PAR_WINDTECHAREAPERTURBINE,
        Param(
            getattr(model, SET_WINDTECH),
            within=NonNegativeReals,
            initialize={
                x.key: wind_techs.get_area_per_turbine(x).to_float(unit=area_unit)
                for x in wind_techs.ids
            },
        ),
    )

    # [VAR] Wind tech capacity in (wind_group, terrain) sub-group
    setattr(
        model,
        VAR_WINDTECHCAPINGROUP,
        Var(
            getattr(model, SET_WINDTECHTUPLE),
            getattr(model, SET_WINDSUBGROUP),
            within=NonNegativeReals,
        ),
    )

    # [VAR] Wind tech output
    setattr(
        model,
        VAR_WINDTECHOUT,
        Var(
            getattr(model, SET_WINDTECHTUPLE),
            getattr(model, SET_TIME),
            within=NonNegativeReals,
        ),
    )

    # [VAR] Wind tech output in (wind_group, terrain) sub-group
    setattr(
        model,
        VAR_WINDTECHOUTINGROUP,
        Var(
            getattr(model, SET_WINDTECHTUPLE),
            getattr(model, SET_WINDSUBGROUP),
            getattr(model, SET_TIME),
            within=NonNegativeReals,
        ),
    )

    # [VAR] Wind tech curtailment per (wind_group, terrain) sub-group
    setattr(
        model,
        VAR_WINDTECHCURT,
        Var(
            getattr(model, SET_WINDTECHTUPLE),
            getattr(model, SET_WINDSUBGROUP),
            getattr(model, SET_TIME),
            within=NonNegativeReals,
        ),
    )

    # [VAR] New wind tech capacity installed in a specific (wind_group, terrain)
    # sub-group at stage s
    setattr(
        model,
        VAR_WINDTECHCAPINSTLGROUP,
        Var(
            getattr(model, SET_WINDTECHTUPLE),
            getattr(model, SET_WINDSUBGROUP),
            within=NonNegativeReals,
        ),
    )

    # [VAR] Binary: any new capacity installed in this sub-group at this stage?
    setattr(
        model,
        VAR_YWINDTECHCAPINSTLGROUP,
        Var(
            getattr(model, SET_WINDTECHTUPLE),
            getattr(model, SET_WINDSUBGROUP),
            domain=Binary,
        ),
    )

    # [VAR] Binary: any cumulative capacity present in this sub-group?
    setattr(
        model,
        VAR_YWINDTECHUSEDGROUP,
        Var(
            getattr(model, SET_WINDTECHTUPLE),
            getattr(model, SET_WINDSUBGROUP),
            domain=Binary,
        ),
    )

    # Yes/No switch: "Did we build anything in this wind group?"
    # Flips switch, whenever the capacity number is above zero.
    # Binary flags mainly needed for one-time Capex and Opex
    def _con_y_wind_instl_group(model, s, h, x, w, terrain):
        cap_instl = getattr(model, VAR_WINDTECHCAPINSTLGROUP)[s, h, x, w, terrain]
        y_instl = getattr(model, VAR_YWINDTECHCAPINSTLGROUP)[s, h, x, w, terrain]
        cap_max = getattr(model, VAR_TECHCAP)[s, h, x].ub
        if cap_max is None or cap_max == float("inf"):
            return Constraint.Skip
        bigm = max(cap_max, 1) + common.EPS_BIGM
        return cap_instl <= bigm * y_instl

    setattr(
        model,
        CON_YWINDTECHCAPINSTLGROUP,
        Constraint(
            getattr(model, SET_WINDTECHTUPLE),
            getattr(model, SET_WINDSUBGROUP),
            rule=_con_y_wind_instl_group,
        ),
    )

    # [CON] BigM: V_WindTechCapInGroup <= bigM * V_YWindTechUsedGroup
    def _con_y_wind_used_group(model, s, h, x, w, terrain):
        cap = getattr(model, VAR_WINDTECHCAPINGROUP)[s, h, x, w, terrain]
        y_used = getattr(model, VAR_YWINDTECHUSEDGROUP)[s, h, x, w, terrain]
        cap_max = getattr(model, VAR_TECHCAP)[s, h, x].ub
        if cap_max is None or cap_max == float("inf"):
            return Constraint.Skip
        bigm = max(cap_max, 1) + common.EPS_BIGM
        return cap <= bigm * y_used

    setattr(
        model,
        CON_YWINDTECHUSEDGROUP,
        Constraint(
            getattr(model, SET_WINDTECHTUPLE),
            getattr(model, SET_WINDSUBGROUP),
            rule=_con_y_wind_used_group,
        ),
    )

    # [PAR] Output ec
    setattr(
        model,
        PAR_WINDTECHEC,
        Param(
            getattr(model, SET_WINDTECH),
            within=Any,
            initialize={x.key: wind_techs.get_ec(x).key for x in wind_techs.ids},
        ),
    )

    # [PAR] Power Coefficient per tech
    setattr(
        model,
        PAR_WINDTECHCP,
        Param(
            getattr(model, SET_WINDTECH),
            within=NonNegativeReals,
            initialize={
                x.key: wind_techs.get_power_coefficient(x).to_float(unit=DimlessUnit())
                for x in wind_techs.ids
            },
        ),
    )

    # [PAR] Rotor diameter per tech
    setattr(
        model,
        PAR_WINDTECHROTORDIAM,
        Param(
            getattr(model, SET_WINDTECH),
            within=NonNegativeReals,
            initialize={
                x.key: wind_techs.get_rotor_diameter(x).to_float(unit=LengthUnit.M)
                for x in wind_techs.ids
            },
        ),
    )

    # [PAR] Available power capacity factor P_avail(s, x, w, terrain, t).
    # Indexed over SET_WINDSUBGROUP so each (wind_group, terrain) pair has its
    # own CF computed from the terrain-specific height adjustment and TI.
    def _init_p_avail(m, s, x, w, terrain, t):
        """
        Compute the expected available power capacity factor for turbine type x
        in terrain sub-group (w, terrain) at stage s and timestep t.

        NOTE: Changed after the implementation of terrain-specific parameters.
        Wind profile reference height is linked to the wind group, while
        roughness and the derived turbulence intensity are linked to the terrain.

        Wind speed at the reference height is adjusted to hub height using the
        logarithmic wind profile for the specific terrain roughness and reference height.
        Turbulence intensity is then resolved with the following precedence:
        1. time-series TI from wind_turbulence_intensity_profile.csv for (stage, wind_group, time)
        2. fixed TI from wind_turbulence_intensity_fixed.csv for (stage, wind_group)
        3. roughness-derived TI from hub height and terrain roughness,
           TI ~= 1/ln(hub_height/roughness).

        :param m: Pyomo model instance
        :param s: Stage id (str key)
        :param x: Wind technology id (str key)
        :param w: Wind group id (str key)
        :param terrain: Terrain id (str key)
        :param t: Time id (int key)
        :return: Available power capacity factor [-] in [0, 1]
        """
        hub_height_val = system.wind_techs.get_hub_height(TechId(x))
        hub_height_m = hub_height_val.to_float(LengthUnit.M)

        v_in = wind_techs.get_cut_in_speed(TechId(x)).to_float(
            unit=LengthUnit.M / TimeUnit.S
        )
        v_out = wind_techs.get_cut_out_speed(TechId(x)).to_float(
            unit=LengthUnit.M / TimeUnit.S
        )
        cp = float(getattr(m, PAR_WINDTECHCP)[x])
        rotor_d = float(getattr(m, PAR_WINDTECHROTORDIAM)[x])

        rated_power_val = wind_techs.get_rated_power(TechId(x))
        p_rated_kw = rated_power_val.to_float(unit=PowerUnit.KW)
        if p_rated_kw <= 0.0:
            return 0.0
        p_rated_w = p_rated_kw * 1e3

        # Raw wind speed at reference height for this wind group
        v_ref = (
            system.wind_data.get_raw_speed_profile(StageId(s), WindGroupId(w))
            .get_value(TimeId(t))
            .to_float(unit=LengthUnit.M / TimeUnit.S)
        )

        terrain_id = TerrainId(terrain)
        ref_height_val = system.wind_data.get_wind_group_height(WindGroupId(w))
        roughness_val = system.wind_data.get_terrain_roughness(terrain_id)

        if ref_height_val is not None and roughness_val is not None:
            ref_h_m = ref_height_val.to_float(LengthUnit.M)
            rough_m = roughness_val.to_float(LengthUnit.M)
            v_hub = adjust_speed_for_height_roughness(
                speed_ms=v_ref,
                ref_height_m=ref_h_m,
                roughness_m=rough_m,
                target_height_m=hub_height_m,
            )
        else:
            rough_m = 0.0
            v_hub = v_ref

        ti = _get_turbulence_intensity(
            system=system,
            s=s,
            w=w,
            t=t,
            hub_height_m=hub_height_m,
            rough_m=rough_m,
        )

        p_exp_w = _power_with_turb_intensity(
            v_mean=v_hub,
            turb_intensity=ti,
            v_in=v_in,
            v_out=v_out,
            p_rated=p_rated_w,
            rotor_diameter_m=rotor_d,
            cp=cp,
            rho=AIR_DENSITY_KG_M3,
        )

        # Floor near-zero CFs to exactly 0 to avoid tiny LP coefficients.
        # 1e-4 keeps the matrix range within ~5 orders of magnitude vs 2e+08,
        # which prevents Gurobi barrier ordering from producing a near-singular
        # normal-equations matrix. Wind output below 0.01% rated is physically
        # negligible (cut-in speed not met).
        capacity_factor = p_exp_w / p_rated_w
        if capacity_factor < 1e-4:
            return 0.0
        return min(1.0, capacity_factor)

    setattr(
        model,
        PAR_WINDTECHPAVAIL,
        Param(
            getattr(model, SET_STAGE),
            getattr(model, SET_WINDTECH),
            getattr(model, SET_WINDSUBGROUP),
            getattr(model, SET_TIME),
            within=NonNegativeReals,
            initialize=_init_p_avail,
        ),
    )

    # [PAR] Curtailment bounds per (s,h,x)
    # (defaults from wind_tech_data if not specified)
    def _init_curt_max_rel(m, s, h, x):
        return system.wind_techs.get_curtail_max_rel(TechId(x), HubId(h)).to_float()

    def _init_curt_min_rel(m, s, h, x):
        return system.wind_techs.get_curtail_min_rel(TechId(x), HubId(h)).to_float()

    setattr(
        model,
        PAR_WINDTECHCURTMAXREL,
        Param(
            getattr(model, SET_WINDTECHTUPLE),
            within=NonNegativeReals,
            initialize=_init_curt_max_rel,
        ),
    )

    setattr(
        model,
        PAR_WINDTECHCURTMINREL,
        Param(
            getattr(model, SET_WINDTECHTUPLE),
            within=NonNegativeReals,
            initialize=_init_curt_min_rel,
        ),
    )
    """
    Build order, for reference
    _build_base calls all of the functions in this sequence:
    output-sum
    -> cap-sum
    -> used
    -> group-allowed
    -> cap-in-group (physics)
    -> curtailment
    -> area-cap
    -> install-sum
    -> location constraint
    -> install-area-cap
    -> cost-override (conditional)
    """
    # [CON] Wind tech output summed over all (wind_group, terrain) sub-groups
    _con_wind_tech_output_sum_over_groups(model)
    # [CON] Wind tech capacity is sum over sub-group capacities
    _con_wind_tech_cap(model)
    # [CON] Tech usage
    _con_wind_tech_used(model, system)
    # [CON] Restrict wind-tech to explicitly allowed wind groups
    _con_wind_tech_group_allowed(model, system)
    # [CON] Respect wind tech capacity per sub-group
    _con_wind_tech_cap_in_group(model)
    # [CON] Respect Curtailment restrictions
    _con_wind_tech_curt_bounds(model)
    # [CON] Respect Wind Area Capacity per (wind_group, terrain)
    _con_wind_area_cap(model, system)
    # [CON] Tie total install variable to per-sub-group install variable
    _con_wind_tech_cap_instl_group_sum(model)
    # [CON] Sub-group stickiness: turbines sited in a sub-group cannot move
    _con_wind_tech_cap_in_group_min(model, system)
    # [CON] Area constraint at installation time per (wind_group, terrain)
    _con_wind_area_instl_cap(model, system)
    # [CON] Terrain-adjusted cost overrides (only when CSV is present)
    if system.wind_data.has_terrain_multipliers():
        _override_wind_tech_costs(model, system)


def _con_wind_tech_output_sum_over_groups(model: Model) -> None:
    """
    Total electricity output.
    Add up output from all terrain types, hourly time-series profile.

    V_WindTechOut[s,h,x,t] = sum_{(w,terrain)} V_WindTechOutInGroup[s,h,x,w,terrain,t]
    """
    def __rule_wind_tech_output_sum_over_groups(model, s, h, x, t):
        return getattr(model, VAR_WINDTECHOUT)[s, h, x, t] == sum(
            getattr(model, VAR_WINDTECHOUTINGROUP)[s, h, x, w, terrain, t]
            for (w, terrain) in getattr(model, SET_WINDSUBGROUP)
        )

    setattr(
        model,
        CON_WINDTECHOUTPUTSUMOVERGROUPS,
        Constraint(
            getattr(model, SET_WINDTECHTUPLE),
            getattr(model, SET_TIME),
            rule=__rule_wind_tech_output_sum_over_groups,
        ),
    )


def _con_wind_tech_cap(model: Model) -> None:
    """
    Total installed capacity for a turbine type
    = add up its capacity across all terrain types
    = simple sum
    V_TechCap[s,h,x] = sum_{(w,terrain)} V_WindTechCapInGroup[s,h,x,w,terrain]
    """
    def __rule_wind_tech_cap(model, s, h, x):
        return getattr(model, VAR_TECHCAP)[s, h, x] == sum(
            getattr(model, VAR_WINDTECHCAPINGROUP)[s, h, x, w, terrain]
            for (w, terrain) in getattr(model, SET_WINDSUBGROUP)
        )

    setattr(
        model,
        CON_WINDTECHCAP,
        Constraint(getattr(model, SET_WINDTECHTUPLE), rule=__rule_wind_tech_cap),
    )


def _con_wind_tech_cap_in_group(model: Model) -> None:
    """
    Power balance per (wind_group, terrain) sub-group:
    total available power
    is split between useful output and curtailment.
    = output + curtailed electricity = CF * installed capacity
    incl. terrain height adjustment and TI
    houtly time-series

    V_WindTechOutInGroup[s,h,x,w,terrain,t] + V_WindTechCurt[s,h,x,w,terrain,t]
        = P_avail[s,x,w,terrain,t] * V_WindTechCapInGroup[s,h,x,w,terrain]
    """
    def __rule_wind_tech_cap(model, s, h, x, w, terrain, t):
        cap = getattr(model, VAR_WINDTECHCAPINGROUP)[s, h, x, w, terrain]
        out = getattr(model, VAR_WINDTECHOUTINGROUP)[s, h, x, w, terrain, t]
        curt = getattr(model, VAR_WINDTECHCURT)[s, h, x, w, terrain, t]

        p_avail = float(getattr(model, PAR_WINDTECHPAVAIL)[s, x, w, terrain, t])
        if p_avail < 1e-4:
            p_avail = 0.0
        return out + curt == p_avail * cap

    setattr(
        model,
        CON_WINDTECHCAPINGROUP,
        Constraint(
            getattr(model, SET_WINDTECHTUPLE),
            getattr(model, SET_WINDSUBGROUP),
            getattr(model, SET_TIME),
            rule=__rule_wind_tech_cap,
        ),
    )


def _con_wind_tech_used(model: Model, system: EnergySystem) -> None:
    """
    Track whether a wind technology produces any output in a given (stage, hub).
    V_YTechUsed[s,h,x] is set to 1 whenever total weighted output is nonzero.
    This is required so that one-time Opex costs are correctly accounted for.

    sum_t( weight[s,t] * V_WindTechOut[s,h,x,t] ) <= bigM * V_YTechUsed[s,h,x]
    """
    times = system.times
    wind_techs = system.wind_techs

    def __rule_wind_tech_used(model, s, h, x):
        wind_ec = wind_techs.get_ec(TechId(x))
        ec_unit = get_ec_model_unit(
            system.ecs.get_unit(wind_ec), system.mass_unit, system.power_unit
        )
        bigm = system.get_heur_limit_max_sum_out(
            StageId(s), HubId(h), wind_ec
        ).to_float(unit=ec_unit)
        bigm = max(bigm, 1) + common.EPS_BIGM

        out_sum = sum(
            times.get_weight(StageId(s), TimeId(t))
            * getattr(model, VAR_WINDTECHOUT)[s, h, x, t]
            for t in getattr(model, SET_TIME)
        )
        return out_sum <= bigm * getattr(model, VAR_YTECHUSED)[s, h, x]

    setattr(
        model,
        CON_WINDTECHUSED,
        Constraint(getattr(model, SET_WINDTECHTUPLE), rule=__rule_wind_tech_used),
    )


def _con_wind_tech_group_allowed(model: Model, system: EnergySystem) -> None:
    """
    Enforce the optional allow-list from wind_params.allowed_terrains.

    For each (tech, wind_group, terrain) sub-group not allowed for the tech -
    per WindTechs.is_subgroup_allowed() - capacity in that sub-group is forced
    to zero:

        V_WindTechCapInGroup[s,h,x,w,terrain] = 0
    """

    def __rule_wind_tech_group_allowed(model, s, h, x, w, terrain):
        if system.wind_techs.is_subgroup_allowed(TechId(x), str(w), str(terrain)):
            return Constraint.Skip
        return getattr(model, VAR_WINDTECHCAPINGROUP)[s, h, x, w, terrain] == 0

    setattr(
        model,
        CON_WINDTECHGROUPALLOWED,
        Constraint(
            getattr(model, SET_WINDTECHTUPLE),
            getattr(model, SET_WINDSUBGROUP),
            rule=__rule_wind_tech_group_allowed,
        ),
    )


def _con_wind_tech_curt_bounds(model: Model) -> None:
    """
    Enforce relative curtailment bounds per (wind_group, terrain) sub-group.
    curtail_max_rel and curtail_min_rel may be set at tech level (techs.yaml)
    and/or hub level (hubs.yaml); the more restrictive value is used.
    Constraints are skipped when the bound is at its default (max=1, min=0).

    V_WindTechCurt[s,h,x,w,terrain,t] <= curtail_max_rel[s,h,x] *
        P_avail[s,x,w,terrain,t] * V_WindTechCapInGroup[s,h,x,w,terrain]
    V_WindTechCurt[s,h,x,w,terrain,t] >= curtail_min_rel[s,h,x] *
        P_avail[s,x,w,terrain,t] * V_WindTechCapInGroup[s,h,x,w,terrain]
    """
    eps = 1e-12

    def __rule_curt_max(model, s, h, x, w, terrain, t):
        max_rel = float(getattr(model, PAR_WINDTECHCURTMAXREL)[s, h, x])
        if max_rel >= 1.0 - eps:
            return Constraint.Skip

        curt = getattr(model, VAR_WINDTECHCURT)[s, h, x, w, terrain, t]
        p_avail = float(getattr(model, PAR_WINDTECHPAVAIL)[s, x, w, terrain, t])
        if p_avail < 1e-4:
            p_avail = 0.0
        cap = getattr(model, VAR_WINDTECHCAPINGROUP)[s, h, x, w, terrain]
        return curt <= max_rel * p_avail * cap

    def __rule_curt_min(model, s, h, x, w, terrain, t):
        min_rel = float(getattr(model, PAR_WINDTECHCURTMINREL)[s, h, x])
        if min_rel <= eps:
            return Constraint.Skip

        curt = getattr(model, VAR_WINDTECHCURT)[s, h, x, w, terrain, t]
        p_avail = float(getattr(model, PAR_WINDTECHPAVAIL)[s, x, w, terrain, t])
        if p_avail < 1e-4:
            p_avail = 0.0
        cap = getattr(model, VAR_WINDTECHCAPINGROUP)[s, h, x, w, terrain]
        return curt >= min_rel * p_avail * cap

    setattr(
        model,
        CON_WINDTECHCURTMAX,
        Constraint(
            getattr(model, SET_WINDTECHTUPLE),
            getattr(model, SET_WINDSUBGROUP),
            getattr(model, SET_TIME),
            rule=__rule_curt_max,
        ),
    )
    setattr(
        model,
        CON_WINDTECHCURTMIN,
        Constraint(
            getattr(model, SET_WINDTECHTUPLE),
            getattr(model, SET_WINDSUBGROUP),
            getattr(model, SET_TIME),
            rule=__rule_curt_min,
        ),
    )


def _con_wind_area_cap(model: Model, system: EnergySystem) -> None:
    """
    Limit the total land area occupied by installed turbines per
    (stage, hub, wind_group, terrain) sub-group.

    Turbines in one wind group and terrain type can't occupy more land than that available.
    Check for units!
    If units mismatch, area constraint is almost never binding.

    The available area for a sub-group is the fraction of the wind group's
    total area that belongs to that terrain type:
        area_avail(s,h,w,terrain) = area(s,h,w) * frac(w,terrain) / total_frac(w)

    Skipped if no wind area is defined for the given (stage, hub, wind_group) tuple
    or if the terrain fraction is zero.

    sum_x( V_WindTechCapInGroup[s,h,x,w,terrain] * area_per_turbine[x] / rated_power[x] )
        <= area_avail(s,h,w,terrain)
    """
    area_unit = LengthUnit.M * LengthUnit.M

    def __rule_wind_area_cap(m, s, h, w, terrain):
        area_val = system.wind_data.get_area(StageId(s), HubId(h), WindGroupId(w))
        if area_val is None:
            return Constraint.Skip

        total_area = area_val.to_float(unit=area_unit)

        # Compute terrain sub-group area
        terrain_fracs = system.wind_data.get_terrain_fracs_for_group(WindGroupId(w))
        if not terrain_fracs and terrain == w:
            area_avail = total_area
        else:
            total_frac = sum(terrain_fracs.values())
            frac = terrain_fracs.get(TerrainId(terrain), 0.0)
            if total_frac <= 0.0 or frac <= 0.0:
                return Constraint.Skip
            area_avail = total_area * (frac / total_frac)

        used_area = sum(
            getattr(m, VAR_WINDTECHCAPINGROUP)[s, h, x, w, terrain]
            * getattr(m, PAR_WINDTECHAREAPERTURBINE)[x]
            / system.wind_techs.get_rated_power(TechId(x)).to_float(unit=system.power_unit)
            for (ss, hh, x) in getattr(m, SET_WINDTECHTUPLE)
            if ss == s and hh == h
        )

        return used_area <= area_avail

    setattr(
        model,
        CON_WINDAREACAP,
        Constraint(
            getattr(model, SET_WINDHUBTUPLE),
            getattr(model, SET_WINDSUBGROUP),
            rule=__rule_wind_area_cap,
        ),
    )


def _con_wind_tech_cap_instl_group_sum(model: Model) -> None:
    """
    Total installed capacity to per turbine type.
    Only for newly built capacity at stage s, instead of cumulative caoacity.

    V_TechCapInstl[s,h,x] == sum_{(w,terrain)} V_WindTechCapInstlInGroup[s,h,x,w,terrain]
    """
    def __rule(model, s, h, x):
        return getattr(model, VAR_TECHCAPINSTL)[s, h, x] == sum(
            getattr(model, VAR_WINDTECHCAPINSTLGROUP)[s, h, x, w, terrain]
            for (w, terrain) in getattr(model, SET_WINDSUBGROUP)
        )

    setattr(
        model,
        CON_WINDTECHCAPINSTLGROUPSUM,
        Constraint(getattr(model, SET_WINDTECHTUPLE), rule=__rule),
    )


def _con_wind_tech_cap_in_group_min(model: Model, system: EnergySystem) -> None:
    """
    Turbines cant teleport between wind groups and terrains within lifetime.
    Once location is fixed, it cannot be changed in later stages within lifetime,.
    -> capacity physically installed in (w, terrain) at stage s_instl
    must remain in that sub-group at all later stages within its lifetime.

    V_WindTechCapInGroup[s,h,x,w,terrain]
        >= sum_{s_instl: start_year <= current_year, within lifetime}
               V_WindTechCapInstlInGroup[s_instl,h,x,w,terrain]
    """
    stages = system.stages
    techs = system.techs

    def __rule(model, s, h, x, w, terrain):
        current_year = stages.get_start_year(StageId(s))
        tech_lifetime = techs.get_lifetime(TechId(x)).to_float(TimeUnit.A)

        relevant = [
            s_instl
            for s_instl in getattr(model, SET_STAGE)
            if (s_instl, h, x) in getattr(model, SET_WINDTECHTUPLE)
            and stages.get_start_year(StageId(s_instl)) <= current_year
            and current_year - stages.get_start_year(StageId(s_instl)) < tech_lifetime
        ]

        if not relevant:
            return Constraint.Skip

        lower = sum(
            getattr(model, VAR_WINDTECHCAPINSTLGROUP)[s_instl, h, x, w, terrain]
            for s_instl in relevant
        )
        return getattr(model, VAR_WINDTECHCAPINGROUP)[s, h, x, w, terrain] >= lower

    setattr(
        model,
        CON_WINDTECHCAPINGROUPMIN,
        Constraint(
            getattr(model, SET_WINDTECHTUPLE),
            getattr(model, SET_WINDSUBGROUP),
            rule=__rule,
        ),
    )


def _con_wind_area_instl_cap(model: Model, system: EnergySystem) -> None:
    """
    Ensure the total area occupied by all within-lifetime installations in
    sub-group (w, terrain) does not exceed the available terrain sub-group area
    at each (stage, hub).
    Includes previous installations within their lifetime.

    area_avail(s,h,w,terrain) = area(s,h,w) * frac(w,terrain) / total_frac(w)

    Skipped if no wind area is defined or if the terrain fraction is zero.

    sum_{s_instl: within lifetime at s} sum_x
        V_WindTechCapInstlInGroup[s_instl,h,x,w,terrain] * area_per_turbine[x] / rated_power[x]
        <= area_avail(s,h,w,terrain)
    """
    area_unit = LengthUnit.M * LengthUnit.M
    stages = system.stages
    techs = system.techs

    def __rule_wind_area_instl_cap(m, s, h, w, terrain):
        area_val = system.wind_data.get_area(StageId(s), HubId(h), WindGroupId(w))
        if area_val is None:
            return Constraint.Skip

        total_area = area_val.to_float(unit=area_unit)

        terrain_fracs = system.wind_data.get_terrain_fracs_for_group(WindGroupId(w))
        if not terrain_fracs and terrain == w:
            area_avail = total_area
        else:
            total_frac = sum(terrain_fracs.values())
            frac = terrain_fracs.get(TerrainId(terrain), 0.0)
            if total_frac <= 0.0 or frac <= 0.0:
                return Constraint.Skip
            area_avail = total_area * (frac / total_frac)

        current_year = stages.get_start_year(StageId(s))

        terms = [
            getattr(m, VAR_WINDTECHCAPINSTLGROUP)[ss, hh, x, w, terrain]
            * getattr(m, PAR_WINDTECHAREAPERTURBINE)[x]
            / system.wind_techs.get_rated_power(TechId(x)).to_float(unit=system.power_unit)
            for (ss, hh, x) in getattr(m, SET_WINDTECHTUPLE)
            if hh == h
            and stages.get_start_year(StageId(ss)) <= current_year
            and current_year - stages.get_start_year(StageId(ss))
            < techs.get_lifetime(TechId(x)).to_float(TimeUnit.A)
        ]

        if not terms:
            return Constraint.Skip

        return sum(terms) <= area_avail

    setattr(
        model,
        CON_WINDAREAINSTLCAP,
        Constraint(
            getattr(model, SET_WINDHUBTUPLE),
            getattr(model, SET_WINDSUBGROUP),
            rule=__rule_wind_area_instl_cap,
        ),
    )


def _override_wind_tech_costs(model: Model, system: EnergySystem) -> None:
    """
    Override the standard CAPEX and OPEX cost constraints for wind tech tuples
    with terrain-adjusted versions that apply per-sub-group cost multipliers loaded
    from wind_terrain_multipliers.csv.

    Called only when system.wind_data.has_terrain_multipliers() is True.
    """
    wind_data = system.wind_data
    wind_techs = system.wind_techs
    stages = system.stages
    techs = system.techs
    currency_unit = system.currency_unit
    length_unit = system.length_unit
    mass_unit = system.mass_unit
    power_unit = system.power_unit

    logging.log_file(
        "Applying terrain cost multipliers to wind tech cost constraints",
        module=LOG_MODULE_STR,
    )

    # Terrain multipliers per (wind_group, terrain) sub-group - raw values,
    # no area-fraction weighting needed because sub-group capacity carries the split.
    def _terrain_init_subgroup(component: str):
        result = {}
        for w in wind_data.get_wind_groups():
            for terrain in wind_data.get_terrain_fracs_for_group(w):
                result[w.key, terrain.key] = wind_data.get_terrain_multiplier_raw(
                    w, terrain, component
                )
        if not result:
            # Degenerate fallback: terrain == wind group
            for w in wind_data.get_wind_groups():
                result[w.key, w.key] = 1.0
        return result

    setattr(
        model,
        PAR_WINDTERRAINCAPEXCAP,
        Param(
            getattr(model, SET_WINDSUBGROUP),
            within=NonNegativeReals,
            initialize=_terrain_init_subgroup("capex_per_cap"),
        ),
    )
    setattr(
        model,
        PAR_WINDTERRAINOPEXCAP,
        Param(
            getattr(model, SET_WINDSUBGROUP),
            within=NonNegativeReals,
            initialize=_terrain_init_subgroup("opex_per_cap"),
        ),
    )
    setattr(
        model,
        PAR_WINDTERRAINCAPEXONE,
        Param(
            getattr(model, SET_WINDSUBGROUP),
            within=NonNegativeReals,
            initialize=_terrain_init_subgroup("one_time_capex"),
        ),
    )
    setattr(
        model,
        PAR_WINDTERRAINOPEXONE,
        Param(
            getattr(model, SET_WINDSUBGROUP),
            within=NonNegativeReals,
            initialize=_terrain_init_subgroup("one_time_opex"),
        ),
    )

    # Deactivate standard cost constraints for all wind tech tuples
    capex_con = getattr(model, CON_TECHCOSTCAPEX)
    opex_con = getattr(model, CON_TECHCOSTOPEXCAP)
    for s, h, x in getattr(model, SET_WINDTECHTUPLE):
        capex_con[s, h, x].deactivate()
        opex_con[s, h, x].deactivate()

    # Terrain-adjusted CAPEX: replace C_TechCostCapex for wind tuples.
    # capex_per_cap is applied per (w, terrain) sub-group using the sub-group
    # installation variable - no pre-aggregation needed.
    def __rule_terrain_capex(model, s, h, x):
        current_year = stages.get_start_year(StageId(s))
        interest_rate = techs.get_interest_rate(TechId(x)).to_float()
        tech_lifetime = techs.get_lifetime(TechId(x)).to_float(TimeUnit.A)
        crf = calculate_crf(interest_rate, tech_lifetime)
        cap_unit = get_model_cap_unit(
            techs.get_cap_unit(TechId(x)), length_unit, mass_unit, power_unit
        )
        cost_capex = 0
        for s_instl in getattr(model, SET_STAGE):
            if (s_instl, h, x) not in getattr(model, SET_WINDTECHTUPLE):
                continue
            start_year_instl = stages.get_start_year(StageId(s_instl))
            if current_year < start_year_instl:
                continue
            if current_year - start_year_instl >= tech_lifetime:
                continue
            capex_per_cap = techs.get_capex_per_cap(
                StageId(s_instl), TechId(x)
            ).to_float(unit=(currency_unit / cap_unit))
            one_time_capex = techs.get_one_time_capex(
                StageId(s_instl), TechId(x)
            ).to_float(unit=currency_unit)
            cost_capex += crf * one_time_capex * sum(
                float(getattr(model, PAR_WINDTERRAINCAPEXONE)[w, terrain])
                * getattr(model, VAR_YWINDTECHCAPINSTLGROUP)[s_instl, h, x, w, terrain]
                for (w, terrain) in getattr(model, SET_WINDSUBGROUP)
            )
            # capex_per_cap: applied directly per (w, terrain) sub-group
            cost_capex += crf * capex_per_cap * sum(
                float(getattr(model, PAR_WINDTERRAINCAPEXCAP)[w, terrain])
                * getattr(model, VAR_WINDTECHCAPINSTLGROUP)[s_instl, h, x, w, terrain]
                for (w, terrain) in getattr(model, SET_WINDSUBGROUP)
            )
        return getattr(model, VAR_TECHCOSTCAPEX)[s, h, x] == cost_capex

    setattr(
        model,
        CON_WINDTERRAINCOSTSTCAPEX,
        Constraint(getattr(model, SET_WINDTECHTUPLE), rule=__rule_terrain_capex),
    )

    # Terrain-adjusted OPEX: replace C_TechCostOpexCap for wind tuples.
    # opex_per_cap is applied directly per (w, terrain) sub-group.
    def __rule_terrain_opex(model, s, h, x):
        cap_unit = get_model_cap_unit(
            techs.get_cap_unit(TechId(x)), length_unit, mass_unit, power_unit
        )
        opex_per_cap = techs.get_opex_per_cap(StageId(s), TechId(x)).to_float(
            unit=(currency_unit / cap_unit)
        )
        one_time_opex = techs.get_one_time_opex(StageId(s), TechId(x)).to_float(
            unit=currency_unit
        )
        cost_opex = one_time_opex * sum(
            float(getattr(model, PAR_WINDTERRAINOPEXONE)[w, terrain])
            * getattr(model, VAR_YWINDTECHUSEDGROUP)[s, h, x, w, terrain]
            for (w, terrain) in getattr(model, SET_WINDSUBGROUP)
        )
        # opex_per_cap: applied directly per (w, terrain) sub-group
        cost_opex += opex_per_cap * sum(
            float(getattr(model, PAR_WINDTERRAINOPEXCAP)[w, terrain])
            * getattr(model, VAR_WINDTECHCAPINGROUP)[s, h, x, w, terrain]
            for (w, terrain) in getattr(model, SET_WINDSUBGROUP)
        )
        return getattr(model, VAR_TECHCOSTOPEXCAP)[s, h, x] == cost_opex

    setattr(
        model,
        CON_WINDTERRAINCOSTSTOPEXCAP,
        Constraint(getattr(model, SET_WINDTECHTUPLE), rule=__rule_terrain_opex),
    )

    logging.log_file(
        "Terrain cost override applied to "
        f"{len(list(getattr(model, SET_WINDTECHTUPLE)))} wind tech tuple(s)",
        module=LOG_MODULE_STR,
    )


