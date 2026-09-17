"""
Wind data module

Each wind group has a time-series of wind speed profiles for each stage.

Wind speed profile -> (stage, wind_group) -> time series
The wind speed profile represents wind at a reference level of 100 m based on Elenas wind data.
Adjustments from the reference height to hub height use terrain-specific height and roughness values
via the logarithmic wind profile model.
Each wind group contains one or more terrain types (Alps, Jura, Plateau),
each with its own reference height and roughness length.
Turbulence intensity is derived from roughness length at model build time via TI ~= 1/ln(hub_height/z0).

"""

import math
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from ehubx.core import logging
from ehubx.core.common import TimeSeriesKind
from ehubx.data import exceptions
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.index import Index, IndexKind
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.time_data import TimeId, Times
from ehubx.data.time_series import TimeSeries
from ehubx.data.unit import DimlessUnit, LengthUnit, TimeUnit, Unit
from ehubx.data.value import Value


class WindGroupId(Index):
    """wind group index"""

    def __init__(self, key: str):
        super().__init__(IndexKind.WINDGROUP, key)


class TerrainId(Index):
    """terrain (spatial region) index within a wind group"""

    def __init__(self, key: str):
        super().__init__(IndexKind.TERRAIN, key)


class ExceptionKey(Enum):

    SPEED_GET = "getting 'speed' from WindData"
    SPEED_SET = "setting 'speed' of WindData"
    SPEED_DEFSET = "setting default 'speed' of WindData"
    SPEED_VAL = "validating 'speed' of WindData"

    # wind areas
    AREA_GET = "getting 'area' from WindData"
    AREA_SET = "setting 'area' of WindData"
    AREA_VAL = "validating 'area' of WindData"

    WINDGROUPS_GET = "getting 'wind_groups' from WindData"
    WINDGROUPS_ADD = "adding 'wind_groups' to WindData"
    WINDGROUPS_VAL = "validating 'wind_groups' of WindData"

    TERRAIN_GET = "getting 'terrain' from WindData"
    TERRAIN_SET = "setting 'terrain' of WindData"
    TERRAIN_VAL = "validating 'terrain' of WindData"

    TURBINT_GET = "getting 'turbulence_intensity' from WindData"
    TURBINT_SET = "setting 'turbulence_intensity' of WindData"
    TURBINT_VAL = "validating 'turbulence_intensity' of WindData"

# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/wind_data"
"""String identifying the wind data module for logging purposes"""

DEF_SPEED: float = 0
"""Default value for parameter 'speed' in the wind data module"""

TERRAIN_COST_COMPONENTS: tuple = (
    "one_time_capex",
    "capex_per_cap",
    "one_time_opex",
    "opex_per_cap",
)
"""
Cost components have terrain-specific multipliers.
Alps > Jura > Plateau due to diffficult access and higher logistics and transport costs.
Only assumptions -> need to be validated with real data for Switzerland.
Austria: turbines above 1400 m have 8% higher costs than turbines below 1400 m.
"""

def adjust_speed_for_height_roughness(
    speed_ms: float,
    ref_height_m: float,
    roughness_m: float,
    target_height_m: float,
) -> float:
    """
    Adjust wind speed for a given hub height and surface roughness using logarithmic wind profile model.
    Logarithmic wnid profile according to Laurenz:
    v(z) = v_ref * ln(z/z0) / ln(z_ref/z0)

    NOTE: the unit needs to be consistent with expected unit of speed parameter (e.g. m/s).

    :param speed_ms: Wind speed at reference height (m/s)
    :type speed_ms: float
    :param ref_height_m: Reference height (m)
    :type ref_height_m: float
    :param roughness_m: Surface roughness length (m)
    :type roughness_m: float
    :param target_height_m: Target height (m)
    :type target_height_m: float
    :return: Adjusted wind speed (m/s)
    :rtype: float
    """

    if roughness_m <= 0 or target_height_m <= 0:
        return speed_ms

    adjusted_speed_ms = speed_ms * math.log(target_height_m / roughness_m)
    adjusted_speed_ms /= math.log(ref_height_m / roughness_m)
    return adjusted_speed_ms


class WindData:
    """
    Class for wind data.
    Contains getters and setters for wind parameters and validation methods to control data integrity
    """

    # --------------- #
    # Property: speed #
    # --------------- #
    def get_raw_speed_profile(self, s: StageId, w: WindGroupId) -> TimeSeries:
        """
        Get the raw wind speed time series for a stage and wind group,
        at reference measurement height.
        Use adjust_speed_for_height_roughness() with terrain-specific height and
        roughness to obtain the speed at hub height.

        Returns a time series (8760 h) with default value 0 if no data is defined.

        :param s: Stage id
        :param w: Wind group id
        :return: Raw speed profile at reference height
        """
        series = self._speed.get((s, w), None)
        if series is not None:
            return series
        fallback = TimeSeries()
        fallback.def_value = Value(DEF_SPEED, LengthUnit.M / TimeUnit.S)
        return fallback

    def set_speed_in_profile(
        self, s: StageId, w: WindGroupId, t: TimeId, speed: Value
    ) -> None:
        """
        Set wind speed at a specific time step for a stage and wind group.

        :param s: Stage
        :param w: Wind group
        :param t: Timestep
        :param speed: Wind speed value
        """
        expected_unit = LengthUnit.M / TimeUnit.S
        if (s, w) not in self._speed:
            self._speed[s, w] = TimeSeries()
            self._speed[s, w].def_value = Value(DEF_SPEED, expected_unit)
        self._speed[s, w].set_value(t, speed)

    def set_speed_in_profile_def(
        self,
        s: StageId,
        w: WindGroupId,
        speed_def: Value,
    ) -> None:
        """
        Set default (with respect to time) wind speed.

        :param s: Stage
        :param w: Wind group
        :param speed_def: Default wind speed
        """
        expected_unit = LengthUnit.M / TimeUnit.S
        if (s, w) not in self._speed:
            self._speed[s, w] = TimeSeries()
            self._speed[s, w].def_value = Value(DEF_SPEED, expected_unit)
        self._speed[s, w].def_value = speed_def

    # ------------------------ #
    # Property: wind area      #
    # ------------------------ #
    def get_area(self, s: StageId, h: HubId, w: WindGroupId) -> Optional[Value]:
        """
        Get available wind area for (stage, hub, wind group).
        If no area is defined for (s, h, w), return None.
        => The model can then skip the area constraint for this tuple but shouldn't.
        """
        return self._area.get((s, h, w), None)

    def set_area(self, s: StageId, h: HubId, w: WindGroupId, area: Value) -> None:
        """
        Set available wind area for (stage, hub, wind group).

        Expected unit type: area (e.g. m^2, km^2).
        Exact unit conversion/compatibility is validated in validate().
        """
        self._area[(s, h, w)] = area

    # --------------------- #
    # Property: Wind groups #
    # --------------------- #
    def get_wind_groups(self) -> Set[WindGroupId]:
        """
        Get the set of wind groups defined in the data.

        :return: Set of wind group ids
        """
        return self._wind_groups

    def add_wind_group(self, w: WindGroupId) -> None:
        """
        Add a wind group to the data.

        :param w: Wind group id
        """
        if w in self._wind_groups:
            raise exceptions.DuplicateIdException(
                ExceptionKey.WINDGROUPS_ADD.value, w, module=LOG_MODULE_STR
            )
        self._wind_groups.add(w)

    # --------------------------------- #
    # Property: Wind group height       #
    # --------------------------------- #
    def get_wind_group_height(self, w: WindGroupId) -> Optional[Value]:
        """
        Get the reference measurement height of a wind-group speed profile.

        :param w: Wind group id
        :return: Reference height, or None if not set
        """
        return self._wind_group_heights.get(w, None)

    def set_wind_group_height(self, w: WindGroupId, height: Value) -> None:
        """
        Set the reference measurement height of a wind-group speed profile.

        :param w: Wind group id
        :param height: Reference height (length unit)
        """
        self._wind_group_heights[w] = height

    # --------------------------------- #
    # Property: Fixed wind group TI     #
    # --------------------------------- #
    def get_fixed_turbulence_intensity(
        self, s: StageId, w: WindGroupId
    ) -> Optional[Value]:
        """
        Get the fixed turbulence intensity for a stage and wind group.

        :param s: Stage id
        :param w: Wind group id
        :return: Fixed turbulence intensity, or None if not set
        """
        return self._fixed_turbulence_intensity.get((s, w), None)

    def set_fixed_turbulence_intensity(
        self, s: StageId, w: WindGroupId, turb_intensity: Value
    ) -> None:
        """
        Set the fixed turbulence intensity for a stage and wind group.

        :param s: Stage id
        :param w: Wind group id
        :param turb_intensity: Dimensionless turbulence intensity
        """
        self._fixed_turbulence_intensity[s, w] = turb_intensity

    # --------------------------------- #
    # Property: Terrain roughness       #
    # --------------------------------- #
    def get_terrain_roughness(self, terrain: TerrainId) -> Optional[Value]:
        """
        Get the surface roughness length for a terrain type.

        :param terrain: Terrain id
        :return: Roughness length, or None if not set
        """
        return self._terrain_roughness.get(terrain, None)

    def set_terrain_roughness(self, terrain: TerrainId, roughness: Value) -> None:
        """
        Set the surface roughness length for a terrain type.

        :param terrain: Terrain id
        :param roughness: Roughness length (length unit)
        """
        self._terrain_roughness[terrain] = roughness

    def get_terrains(self) -> Set[TerrainId]:
        """Return all terrain ids that have roughness defined."""
        return set(self._terrain_roughness)

    # ---------------------------------------- #
    # Property: Terrain area fractions         #
    # ---------------------------------------- #
    def set_terrain_area_frac(
        self, w: WindGroupId, terrain: TerrainId, frac: float
    ) -> None:
        """
        Set the fractional area of a terrain type within a wind group.

        :param w: Wind group id
        :param terrain: Terrain id
        :param frac: Area fraction (0-1)
        """
        self._terrain_areas[w, terrain] = frac

    def get_terrain_area_frac(
        self, w: WindGroupId, terrain: TerrainId
    ) -> float:
        """
        Get the fractional area of a terrain type within a wind group.
        Returns 0.0 if not defined.

        :param w: Wind group id
        :param terrain: Terrain id
        :return: Area fraction (0-1)
        """
        return self._terrain_areas.get((w, terrain), 0.0)

    def get_terrain_fracs_for_group(
        self, w: WindGroupId
    ) -> Dict[TerrainId, float]:
        """
        Return a dict of {terrain: area_fraction} for all terrains with nonzero
        fraction in wind group w.

        :param w: Wind group id
        :return: Dict mapping TerrainId to fraction (0-1)
        """
        return {
            terrain: frac
            for (ww, terrain), frac in self._terrain_areas.items()
            if ww == w and frac > 0.0
        }

    def has_terrain_areas(self) -> bool:
        """Return True if terrain area fractions have been loaded."""
        return self._terrain_areas_loaded

    def set_terrain_areas_loaded(self) -> None:
        """Mark terrain area fractions as loaded (called by parser after CSV read)."""
        self._terrain_areas_loaded = True

    # ------------------------------------ #
    # Property: terrain cost multipliers   #
    # ------------------------------------ #
    def set_terrain_multiplier(
        self, w: WindGroupId, terrain: TerrainId, component: str, value: float
    ) -> None:
        """
        Set a terrain cost multiplier for a (wind group, terrain) pair and cost component.

        :param w: Wind group id (e.g. W1, W2, W3)
        :param terrain: Terrain id (e.g. Alps, Jura, Plateau)
        :param component: Cost component - one of TERRAIN_COST_COMPONENTS
        :param value: Multiplier (1.0 = no adjustment)
        """
        if component not in TERRAIN_COST_COMPONENTS:
            raise exceptions.DataException(
                "setting terrain multiplier of WindData",
                [w, terrain],
                f"Unknown cost component '{component}'. "
                f"Must be one of {TERRAIN_COST_COMPONENTS}",
                module=LOG_MODULE_STR,
            )
        key = (w, terrain)
        if key not in self._terrain_multipliers:
            self._terrain_multipliers[key] = {}
        self._terrain_multipliers[key][component] = value

    def get_terrain_multiplier_raw(
        self, w: WindGroupId, terrain: "TerrainId", component: str
    ) -> float:
        """
        Get the raw terrain cost multiplier for a specific (wind_group, terrain) pair
        and cost component, without area-fraction weighting.
        Returns 1.0 if not defined.
        1.0 = no additional cost penalty for terrain
        """
        return self._terrain_multipliers.get((w, terrain), {}).get(component, 1.0)

    def has_terrain_multipliers(self) -> bool:
        """Return True if terrain multipliers were loaded from CSV."""
        return self._terrain_multipliers_loaded

    def set_terrain_multipliers_loaded(self) -> None:
        """Mark terrain multipliers as loaded (called by parser after CSV read)."""
        self._terrain_multipliers_loaded = True

    # ---------------------------------------- #
    # Property: Turbulence intensity profile   #
    # ---------------------------------------- #
    def get_turbulence_intensity_profile(
        self, s: StageId, w: WindGroupId
    ) -> Optional[TimeSeries]:
        """
        Get the turbulence intensity time series for a stage and wind group.

        :param s: Stage id
        :param w: Wind group id
        :return: Time series, or None if not defined
        """
        return self._turbulence_intensity.get((s, w), None)

    def set_turbulence_intensity_in_profile(
        self, s: StageId, w: WindGroupId, t: TimeId, turb_intensity: Value
    ) -> None:
        """
        Set turbulence intensity at a specific time step for a stage and wind group.

        :param s: Stage
        :param w: Wind group
        :param t: Timestep
        :param turb_intensity: Dimensionless turbulence intensity value
        """
        expected_unit = DimlessUnit()
        if (s, w) not in self._turbulence_intensity:
            self._turbulence_intensity[s, w] = TimeSeries()
            self._turbulence_intensity[s, w].def_value = Value(0, expected_unit)
        self._turbulence_intensity[s, w].set_value(t, turb_intensity)

    def set_turbulence_intensity_in_profile_def(
        self, s: StageId, w: WindGroupId, turb_intensity_def: Value
    ) -> None:
        """
        Set default turbulence intensity for a stage and wind group.

        :param s: Stage
        :param w: Wind group
        :param turb_intensity_def: Default turbulence intensity
        """
        expected_unit = DimlessUnit()
        if (s, w) not in self._turbulence_intensity:
            self._turbulence_intensity[s, w] = TimeSeries()
            self._turbulence_intensity[s, w].def_value = Value(0, expected_unit)
        self._turbulence_intensity[s, w].def_value = turb_intensity_def

    # ------------------------------- #
    # Secondary property: time_series #
    # ------------------------------- #
    @property
    def time_series(
        self,
    ) -> List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...], TimeSeries]]:
        """
        Time series profiles in the wind module. This is a list of tuples.
        Each list element: 1) ProfileKind. 2) Stage. 3) Tuple of string
        identifiers specific to the ProfileKind. 4) The TimeSeries itself.

        :return: All time series of the wind module
        """
        all_series: List[
            Tuple[TimeSeriesKind, StageId, Tuple[str, ...], TimeSeries]
        ] = []

        # wind speed (per stage, wind_group - no height dimension)
        for (s, w), series in self._speed.items():
            if series.has_values:
                all_series.append(
                    (TimeSeriesKind.WINDSPEED, s, (w.key,), series)
                )

        for (s, w), series in self._turbulence_intensity.items():
            if series.has_values:
                all_series.append(
                    (TimeSeriesKind.WINDTURBULENCEINTENSITY, s, (w.key,), series)
                )

        return all_series

    def set_time_series_val(
        self,
        kind: TimeSeriesKind,
        s: StageId,
        ids: Tuple[str, ...],
        t: TimeId,
        value: float,
    ) -> None:
        """
        Set the value for a time series in the wind data class.

        For WINDSPEED: ids = (wind_group_key,)

        :param kind: Kind of time series
        :param s: Stage
        :param ids: Remaining ids, other than stage and time
        :param t: Time id
        :param value: Value to set in the respective default unit
        """
        unit: Unit
        if kind == TimeSeriesKind.WINDSPEED:
            if len(ids) == 0:
                raise exceptions.DataException(
                    ExceptionKey.SPEED_SET.value,
                    [s],
                    msg="Missing wind group id in wind speed time-series ids",
                    module=LOG_MODULE_STR,
                )
            w = WindGroupId(ids[0])
            unit = Unit.get_def_unit(LengthUnit.M / TimeUnit.S)
            self.set_speed_in_profile(s, w, t, Value(value, unit=unit))
        elif kind == TimeSeriesKind.WINDTURBULENCEINTENSITY:
            if len(ids) == 0:
                raise exceptions.DataException(
                    ExceptionKey.TURBINT_SET.value,
                    [s],
                    msg="Missing wind group id in turbulence-intensity time-series ids",
                    module=LOG_MODULE_STR,
                )
            w = WindGroupId(ids[0])
            unit = Unit.get_def_unit(DimlessUnit())
            self.set_turbulence_intensity_in_profile(s, w, t, Value(value, unit=unit))

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._speed: Dict[Tuple[StageId, WindGroupId], TimeSeries] = {}
        self._turbulence_intensity: Dict[Tuple[StageId, WindGroupId], TimeSeries] = {}
        self._area: Dict[Tuple[StageId, HubId, WindGroupId], Value] = {}
        self._wind_groups: Set[WindGroupId] = set()
        # Reference height per wind-group speed profile
        self._wind_group_heights: Dict[WindGroupId, Value] = {}
        self._fixed_turbulence_intensity: Dict[Tuple[StageId, WindGroupId], Value] = {}
        # Surface roughness per terrain type
        self._terrain_roughness: Dict[TerrainId, Value] = {}
        # area fractions per (wind_group, terrain), summing to 1 per wind group
        self._terrain_areas: Dict[Tuple[WindGroupId, TerrainId], float] = {}
        self._terrain_areas_loaded: bool = False
        # cost multipliers per (wind_group, terrain) for terrain-adjusted costs;
        # effective per-group multiplier is the area-weighted average
        self._terrain_multipliers: Dict[Tuple[WindGroupId, TerrainId], Dict[str, float]] = {}
        self._terrain_multipliers_loaded: bool = False

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self, stages: Stages, hubs: Hubs, times: Times) -> None:
        """
        Validate all wind data in this object.

        :param stages: Stages data class
        :param hubs: Hubs data class
        :param times: Times data class
        """
        self._validate_speed(stages, times)
        self._validate_turbulence_intensity(stages, times)
        self._validate_area(stages, hubs)
        self._validate_wind_group_heights()
        self._validate_wind_group_turbulence_intensity(stages)
        self._validate_terrain_roughness()

    def _validate_speed(self, stages: Stages, times: Times) -> None:
        exc_key = ExceptionKey.SPEED_VAL.value
        for (s, w), speed in self._speed.items():
            if s not in stages.ids:
                msg = f"Unknown stage {s} in speed[{s}, {w}]"
                raise exceptions.DataException(
                    exc_key, [s, w], msg, module=LOG_MODULE_STR
                )
            if w not in self._wind_groups:
                msg = f"Unknown wind group {w} in speed[{s}, {w}]"
                raise exceptions.DataException(
                    exc_key, [s, w], msg, module=LOG_MODULE_STR
                )
            if speed.has_values:
                speed.validate(times, exc_key)
                for t in times.ids:
                    if speed.get_value(t).is_negative:
                        msg = f"{speed.get_value(t)} = speed[{s}, {w}][{t}] < 0"
                        raise exceptions.DataException(
                            exc_key, [s, w, t], msg, module=LOG_MODULE_STR
                        )
            if not speed.has_values:
                speed_def = speed.def_value
                assert speed_def is not None
                if speed_def.is_negative:
                    msg = f"{speed_def} = speed_def[{s}, {w}] < 0"
                    raise exceptions.DataException(
                        exc_key, [s, w], msg, module=LOG_MODULE_STR
                    )

    def _validate_area(self, stages: Stages, hubs: Hubs) -> None:
        exc_key = ExceptionKey.AREA_VAL.value
        expected_unit = LengthUnit.M * LengthUnit.M

        for (s, h, w), area in self._area.items():
            if s not in stages.ids:
                msg = f"Unknown stage {s} in area[{s}, {h}, {w}]"
                raise exceptions.DataException(
                    exc_key, [s, h, w], msg, module=LOG_MODULE_STR
                )
            if h not in hubs.ids:
                msg = f"Unknown hub {h} in area[{s}, {h}, {w}]"
                raise exceptions.DataException(
                    exc_key, [s, h, w], msg, module=LOG_MODULE_STR
                )
            if w not in self._wind_groups:
                msg = f"Unknown wind group {w} in area[{s}, {h}, {w}]"
                raise exceptions.DataException(
                    exc_key, [s, h, w], msg, module=LOG_MODULE_STR
                )
            a = area.to_float(unit=expected_unit)
            if a < 0.0:
                msg = f"{area} = area[{s}, {h}, {w}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, h, w], msg, module=LOG_MODULE_STR
                )

    def _validate_turbulence_intensity(self, stages: Stages, times: Times) -> None:
        exc_key = ExceptionKey.TURBINT_VAL.value
        for (s, w), turb_intensity in self._turbulence_intensity.items():
            if s not in stages.ids:
                msg = f"Unknown stage {s} in turbulence_intensity[{s}, {w}]"
                raise exceptions.DataException(
                    exc_key, [s, w], msg, module=LOG_MODULE_STR
                )
            if w not in self._wind_groups:
                msg = f"Unknown wind group {w} in turbulence_intensity[{s}, {w}]"
                raise exceptions.DataException(
                    exc_key, [s, w], msg, module=LOG_MODULE_STR
                )
            if turb_intensity.has_values:
                turb_intensity.validate(times, exc_key)
                for t in times.ids:
                    ti = turb_intensity.get_value(t).to_float(DimlessUnit())
                    if ti < 0.0 or ti > 1.0:
                        msg = (
                            f"{turb_intensity.get_value(t)} = turbulence_intensity"
                            f"[{s}, {w}][{t}] must be within [0, 1]"
                        )
                        raise exceptions.DataException(
                            exc_key, [s, w, t], msg, module=LOG_MODULE_STR
                        )
            if not turb_intensity.has_values:
                ti_def = turb_intensity.def_value
                assert ti_def is not None
                ti_def_float = ti_def.to_float(DimlessUnit())
                if ti_def_float < 0.0 or ti_def_float > 1.0:
                    msg = (
                        f"{ti_def} = turbulence_intensity_def[{s}, {w}] "
                        "must be within [0, 1]"
                    )
                    raise exceptions.DataException(
                        exc_key, [s, w], msg, module=LOG_MODULE_STR
                    )

    def _validate_wind_group_heights(self) -> None:
        exc_key = ExceptionKey.WINDGROUPS_VAL.value
        for w, height in self._wind_group_heights.items():
            if w not in self._wind_groups:
                msg = f"Unknown wind group {w} in profile height data"
                raise exceptions.DataException(
                    exc_key, [w], msg, module=LOG_MODULE_STR
                )
            h = height.to_float(LengthUnit.M)
            if h <= 0.0:
                msg = f"{height} = reference height of wind group {w} must be > 0"
                raise exceptions.DataException(
                    exc_key, [w], msg, module=LOG_MODULE_STR
                )

    def _validate_wind_group_turbulence_intensity(self, stages: Stages) -> None:
        exc_key = ExceptionKey.TURBINT_VAL.value
        for (s, w), turb_intensity in self._fixed_turbulence_intensity.items():
            if s not in stages.ids:
                msg = f"Unknown stage {s} in fixed turbulence intensity data"
                raise exceptions.DataException(
                    exc_key, [s, w], msg, module=LOG_MODULE_STR
                )
            if w not in self._wind_groups:
                msg = f"Unknown wind group {w} in fixed turbulence intensity data"
                raise exceptions.DataException(
                    exc_key, [s, w], msg, module=LOG_MODULE_STR
                )
            ti = turb_intensity.to_float(DimlessUnit())
            if ti < 0.0 or ti > 1.0:
                msg = (
                    f"{turb_intensity} = fixed turbulence intensity for "
                    f"stage {s}, wind group {w} must be within [0, 1]"
                )
                raise exceptions.DataException(
                    exc_key, [s, w], msg, module=LOG_MODULE_STR
                )

    def _validate_terrain_roughness(self) -> None:
        exc_key = ExceptionKey.TERRAIN_VAL.value
        for terrain, roughness in self._terrain_roughness.items():
            r = roughness.to_float(LengthUnit.M)
            if r <= 0.0:
                msg = f"{roughness} = roughness of terrain {terrain} must be > 0"
                raise exceptions.DataException(
                    exc_key, [terrain], msg, module=LOG_MODULE_STR
                )

