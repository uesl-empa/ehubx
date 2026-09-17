"""
Wind technology data module
"""

from enum import Enum
from typing import Dict, List, Set

from ehubx.core import logging
from ehubx.data import exceptions
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.unit import DimlessUnit, LengthUnit, PowerUnit, TimeUnit, Unit
from ehubx.data.value import Value


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the wind technology data
    module
    """

    ID_ADD = "adding to 'ids' of WindTechs"
    ID_REMOVE = "removing from 'ids' of WindTechs"
    ID_VAL = "validating 'ids' of WindTechs"
    EC_SET = "setting 'ec' of WindTechs"
    EC_GET = "getting 'ec' from WindTechs"
    EC_VAL = "validating 'ec' of WindTechs"

    # Specifications for Turbineparameters
    SPECS_SET = "setting turbine specs of WindTechs"
    SPECS_GET = "getting turbine specs from WindTechs"
    SPECS_VAL = "validating turbine specs of WindTechs"

    # Area requirement per turbine
    AREA_SET = "setting area per turbine of WindTechs"
    AREA_GET = "getting area per turbine from WindTechs"
    AREA_VAL = "validating area per turbine of WindTechs"

    # Allowed terrains per tech
    ALLOWEDTERRAINS_SET = "setting allowed terrains of WindTechs"
    ALLOWEDTERRAINS_GET = "getting allowed terrains from WindTechs"
    ALLOWEDTERRAINS_VAL = "validating allowed terrains of WindTechs"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/wind_tech"
"""String identifying the wind technology data module for logging purposes"""


class WindTechs:
    """
    Class for wind technology data. Manages wind technology ids, contains
    getters and setters for wind technology parameters and validation methods
    to control data integrity
    """

    # ------------- #
    # Property: ids #
    # ------------- #
    @property
    def ids(self) -> Set[TechId]:
        """
        Set of known wind technology ids
        """
        return self._ids

    @property
    def ids_in_order(self) -> List[TechId]:
        """
        Set of known wind technology ids in alphabetical order
        """
        ids = list(self.ids)
        ids.sort(key=lambda x: x.key)
        return ids

    def add_id(self, x: TechId) -> None:
        """
        Add a new wind technology id

        :param x: Id to be added
        :type x: TechId
        """
        if x in self._ids:
            raise exceptions.DuplicateIdException(
                ExceptionKey.ID_ADD.value, x, module=LOG_MODULE_STR
            )
        self._ids.add(x)

    # ------------ #
    # Property: ec #
    # ------------ #
    def get_ec(self, x: TechId) -> EcId:
        """
        Get the ec that is produced by the wind technology.
        Mandatory parameter for wind technologies,
        otherwise error message before solving
        Wind turbines: ElWind.
        Wind-El13 conversion technology: ElWind -> El13. (incl. losses)

        :param x: Id of wind technology
        :type x: TechId
        :return: ec that is produced by the technology
        :rtype: EcId
        """
        self._check_id(x, ExceptionKey.EC_GET)
        ec = self._ec.get(x, None)
        if ec is None:
            raise exceptions.MissingIdException(
                ExceptionKey.EC_GET.value, x, module=LOG_MODULE_STR
            )
        return ec

    def set_ec(self, x: TechId, e: EcId, ec_unit: Unit) -> None:
        """
        Set the ec that is stored in the storage technology.
        Mandatory parameter for storage technologies,
        otherwise error message before solving

        :param x: Id of storage technology
        :type x: TechId
        :param e: ec that is stored in the technology
        :type e: EcId
        :param ec_unit: Unit of the ec
        :type ec_unit: Unit
        :param ec_unit: Unit of the ec
        :type ec_unit: Unit
        """
        self._check_id(x, ExceptionKey.EC_SET)
        self._ec[x] = e
        energy_unit = PowerUnit.KW * TimeUnit.H
        if not ec_unit.same_type_as(energy_unit):
            raise exceptions.DataException(
                ExceptionKey.EC_SET.value,
                [x, e],
                f"Unit of ec_el[{x}] = {ec_unit} does not match expected unit "
                f"{energy_unit}",
                module=LOG_MODULE_STR,
            )

    # ---------------------- #
    # Turbine specifications #
    # ---------------------- #
    def set_rated_power(self, x: TechId, rated_power: Value) -> None:
        """Store rated power for a wind technology."""
        self._check_id(x, ExceptionKey.SPECS_SET)
        expected_unit = PowerUnit.KW
        if not rated_power.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.SPECS_SET.value,
                [x],
                f"Unit of rated_power[{x}] = {rated_power.unit} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._rated_power[x] = rated_power

    def set_cut_in_speed(self, x: TechId, cut_in_speed: Value) -> None:
        """Store cut-in wind speed for a wind technology."""
        self._check_id(x, ExceptionKey.SPECS_SET)
        expected_unit = LengthUnit.M / TimeUnit.S
        if not cut_in_speed.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.SPECS_SET.value,
                [x],
                f"Unit of cut_in_speed[{x}] = {cut_in_speed.unit} does not match "
                f"expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._cut_in_speed[x] = cut_in_speed

    def set_rated_speed(self, x: TechId, rated_speed: Value) -> None:
        """Store rated wind speed for a wind technology."""
        self._check_id(x, ExceptionKey.SPECS_SET)
        expected_unit = LengthUnit.M / TimeUnit.S
        if not rated_speed.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.SPECS_SET.value,
                [x],
                f"Unit of rated_speed[{x}] = {rated_speed.unit} does not match "
                f"expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._rated_speed[x] = rated_speed

    def set_cut_out_speed(self, x: TechId, cut_out_speed: Value) -> None:
        """Store cut-out wind speed for a wind technology."""
        self._check_id(x, ExceptionKey.SPECS_SET)
        expected_unit = LengthUnit.M / TimeUnit.S
        if not cut_out_speed.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.SPECS_SET.value,
                [x],
                f"Unit of cut_out_speed[{x}] = {cut_out_speed.unit} does not match "
                f"expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._cut_out_speed[x] = cut_out_speed

    def get_rated_power(self, x: TechId) -> Value:
        self._check_id(x, ExceptionKey.SPECS_GET)
        val = self._rated_power.get(x)
        if val is None:
            raise exceptions.MissingIdException(
                ExceptionKey.SPECS_GET.value, x, module=LOG_MODULE_STR
            )
        return val

    def get_cut_in_speed(self, x: TechId) -> Value:
        self._check_id(x, ExceptionKey.SPECS_GET)
        val = self._cut_in_speed.get(x)
        if val is None:
            raise exceptions.MissingIdException(
                ExceptionKey.SPECS_GET.value, x, module=LOG_MODULE_STR
            )
        return val

    def get_rated_speed(self, x: TechId) -> Value:
        self._check_id(x, ExceptionKey.SPECS_GET)
        val = self._rated_speed.get(x)
        if val is None:
            raise exceptions.MissingIdException(
                ExceptionKey.SPECS_GET.value, x, module=LOG_MODULE_STR
            )
        return val

    def get_cut_out_speed(self, x: TechId) -> Value:
        self._check_id(x, ExceptionKey.SPECS_GET)
        val = self._cut_out_speed.get(x)
        if val is None:
            raise exceptions.MissingIdException(
                ExceptionKey.SPECS_GET.value, x, module=LOG_MODULE_STR
            )
        return val

    # ---------------------- #
    # Area per turbine       #
    # ---------------------- #
    def set_area_per_turbine(self, x: TechId, area_per_turbine: Value) -> None:
        """
        Store area requirement per turbine.
        Be carefule of units.
        Especially for area constraint.
        Global unit for length is set as m!
        If unit mismatch -> area constraint is never binding!!
        """
        self._check_id(x, ExceptionKey.AREA_SET)
        expected_unit = LengthUnit.M**2
        if not area_per_turbine.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.AREA_SET.value,
                [x],
                f"Unit of area_per_turbine[{x}] = {area_per_turbine.unit} does "
                f"not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._area_per_turbine[x] = area_per_turbine

    def get_area_per_turbine(self, x: TechId) -> Value:
        """
        Get area requirement per turbine.
        """
        self._check_id(x, ExceptionKey.AREA_GET)
        val = self._area_per_turbine.get(x)
        if val is None:
            raise exceptions.MissingIdException(
                ExceptionKey.AREA_GET.value, x, module=LOG_MODULE_STR
            )
        return val

    # ------------------------------- #
    # Allowed terrains per wind tech  #
    # ------------------------------- #
    def set_allowed_terrains(self, x: TechId, terrain_keys: Set[str]) -> None:
        """
        Set the allowed terrains for a wind technology.
        If this is set, the wind technology is restricted to these terrain types.
        """
        self._check_id(x, ExceptionKey.ALLOWEDTERRAINS_SET)
        self._allowed_terrains[x] = set(terrain_keys)

    def get_allowed_terrains(self, x: TechId) -> Set[str]:
        """
        Get explicitly configured allowed terrains for a wind technology.
        Returns an empty set if no explicit allow-list exists.
        """
        self._check_id(x, ExceptionKey.ALLOWEDTERRAINS_GET)
        return set(self._allowed_terrains.get(x, set()))

    def has_allowed_terrains(self, x: TechId) -> bool:
        """Return True if wind tech x has an explicit allowed_terrains restriction."""
        self._check_id(x, ExceptionKey.ALLOWEDTERRAINS_GET)
        return x in self._allowed_terrains

    def is_terrain_allowed(self, x: TechId, terrain_key: str) -> bool:
        """
        Check if wind tech x is allowed in the given terrain.
        Only meaningful when has_allowed_terrains(x) is True;
        prefer is_subgroup_allowed() to resolve eligibility for a (wind_group, terrain) sub-group.
        """
        self._check_id(x, ExceptionKey.ALLOWEDTERRAINS_GET)
        allowed = self._allowed_terrains.get(x, None)
        if allowed is None:
            return True
        return terrain_key in allowed

    def is_subgroup_allowed(
        self, x: TechId, wind_group_key: str, terrain_key: str
    ) -> bool:
        """
        Check if wind tech x may be sited in the (wind_group, terrain) sub-group.
        Restricted by allowed_terrains if set for the tech; otherwise unrestricted.
        Sub-groups without a real terrain split (terrain_key == wind_group_key,
        the degenerate fallback used when no terrain data is available) are
        disallowed when an allowed_terrains restriction is set, since terrain
        membership cannot be determined there.
        """
        if not self.has_allowed_terrains(x):
            return True
        if terrain_key == wind_group_key:
            return False
        return self.is_terrain_allowed(x, terrain_key)

    # ------------------------------- #
    # Aero Params (Cp and Diameter)   #
    # ------------------------------- #
    def set_power_coefficient(self, x: TechId, power_coefficient: Value) -> None:
        self._check_id(x, ExceptionKey.SPECS_SET)
        expected_unit = DimlessUnit()
        if not power_coefficient.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.SPECS_SET.value,
                [x],
                f"Unit of power_coefficient[{x}] = {power_coefficient.unit} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._power_coefficient[x] = power_coefficient

    def get_power_coefficient(self, x: TechId) -> Value:
        self._check_id(x, ExceptionKey.SPECS_GET)
        val = self._power_coefficient.get(x)
        if val is None:
            raise exceptions.MissingIdException(
                ExceptionKey.SPECS_GET.value, x, module=LOG_MODULE_STR
            )
        return val

    def set_rotor_diameter(self, x: TechId, rotor_diameter: Value) -> None:
        self._check_id(x, ExceptionKey.SPECS_SET)
        expected_unit = LengthUnit.M
        if not rotor_diameter.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.SPECS_SET.value,
                [x],
                f"Unit of rotor_diameter[{x}] = {rotor_diameter.unit} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._rotor_diameter[x] = rotor_diameter

    def get_rotor_diameter(self, x: TechId) -> Value:
        self._check_id(x, ExceptionKey.SPECS_GET)
        val = self._rotor_diameter.get(x)
        if val is None:
            raise exceptions.MissingIdException(
                ExceptionKey.SPECS_GET.value, x, module=LOG_MODULE_STR
            )
        return val

    def set_hub_height(self, x: TechId, hub_height: Value) -> None:
        self._check_id(x, ExceptionKey.SPECS_SET)
        expected_unit = LengthUnit.M
        if not hub_height.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.SPECS_SET.value,
                [x],
                f"Unit of hub_height[{x}] = {hub_height.unit} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._hub_height[x] = hub_height

    def get_hub_height(self, x: TechId) -> Value:
        self._check_id(x, ExceptionKey.SPECS_GET)
        val = self._hub_height.get(x)
        if val is None:
            raise exceptions.MissingIdException(
                ExceptionKey.SPECS_GET.value, x, module=LOG_MODULE_STR
            )
        return val

    # ------------------- #
    # Curtailment bounds  #
    # ------------------- #
    DEF_CURTAIL_MAX_REL = Value(1.0)
    DEF_CURTAIL_MIN_REL = Value(0.0)

    def set_curtail_min_rel(self, x: TechId, curtail_min_rel: Value) -> None:
        self._check_id(x, ExceptionKey.SPECS_SET)
        expected_unit = DimlessUnit()
        if not curtail_min_rel.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.SPECS_SET.value,
                [x],
                f"Unit of curtail_min_rel[{x}] = {curtail_min_rel.unit} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._curtail_min_rel[x] = curtail_min_rel

    def set_curtail_max_rel(self, x: TechId, curtail_max_rel: Value) -> None:
        self._check_id(x, ExceptionKey.SPECS_SET)
        expected_unit = DimlessUnit()
        if not curtail_max_rel.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.SPECS_SET.value,
                [x],
                f"Unit of curtail_max_rel[{x}] = {curtail_max_rel.unit} "
                f"does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._curtail_max_rel[x] = curtail_max_rel

    def set_curtail_min_rel_hub(self, h: HubId, curtail_min_rel: Value) -> None:
        expected_unit = DimlessUnit()
        if not curtail_min_rel.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.SPECS_SET.value,
                [h],
                f"Unit of curtail_min_rel for hub override (hub={h}) = "
                f"{curtail_min_rel.unit} does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._curtail_min_rel_hub[h] = curtail_min_rel

    def set_curtail_max_rel_hub(self, h: HubId, curtail_max_rel: Value) -> None:
        expected_unit = DimlessUnit()
        if not curtail_max_rel.unit.same_type_as(expected_unit):
            raise exceptions.DataException(
                ExceptionKey.SPECS_SET.value,
                [h],
                f"Unit of curtail_max_rel for hub override (hub={h}) = "
                f"{curtail_max_rel.unit} does not match expected unit {expected_unit}",
                module=LOG_MODULE_STR,
            )
        self._curtail_max_rel_hub[h] = curtail_max_rel

    def get_curtail_max_rel(self, x: TechId, h: HubId | None = None) -> Value:
        self._check_id(x, ExceptionKey.SPECS_GET)
        tech_val = self._curtail_max_rel.get(x, self.DEF_CURTAIL_MAX_REL)
        if h is not None and h in self._curtail_max_rel_hub:
            hub_val = self._curtail_max_rel_hub[h]
            if hub_val < tech_val:
                logging.log_file(
                    f"curtail_max_rel for tech '{x.key}' at hub '{h.key}': "
                    f"hub-level {hub_val.to_float():.3f} is more restrictive than "
                    f"tech-level {tech_val.to_float():.3f}, using "
                    f"{hub_val.to_float():.3f}",
                    module=LOG_MODULE_STR,
                )
                return hub_val
            if tech_val < hub_val:
                logging.log_file(
                    f"curtail_max_rel for tech '{x.key}' at hub '{h.key}': "
                    f"tech-level {tech_val.to_float():.3f} is more restrictive than "
                    f"hub-level {hub_val.to_float():.3f}, "
                    f"using {tech_val.to_float():.3f}",
                    module=LOG_MODULE_STR,
                )
        return tech_val

    def get_curtail_min_rel(self, x: TechId, h: HubId | None = None) -> Value:
        self._check_id(x, ExceptionKey.SPECS_GET)
        tech_val = self._curtail_min_rel.get(x, self.DEF_CURTAIL_MIN_REL)
        if h is not None and h in self._curtail_min_rel_hub:
            hub_val = self._curtail_min_rel_hub[h]
            if hub_val > tech_val:
                logging.log_file(
                    f"curtail_min_rel for tech '{x.key}' at hub '{h.key}': "
                    f"hub-level {hub_val.to_float():.3f} is more restrictive than "
                    f"tech-level {tech_val.to_float():.3f}, "
                    f"using {hub_val.to_float():.3f}",
                    module=LOG_MODULE_STR,
                )
                return hub_val
            if tech_val > hub_val:
                logging.log_file(
                    f"curtail_min_rel for tech '{x.key}' at hub '{h.key}': "
                    f"tech-level {tech_val.to_float():.3f} is more restrictive than "
                    f"hub-level {hub_val.to_float():.3f}, "
                    f"using {tech_val.to_float():.3f}",
                    module=LOG_MODULE_STR,
                )
        return tech_val

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._ids: Set[TechId] = set()
        self._ec: Dict[TechId, EcId] = dict()

        # turbine specs (per TechId)
        self._rated_power: Dict[TechId, Value] = {}
        self._cut_in_speed: Dict[TechId, Value] = {}
        self._rated_speed: Dict[TechId, Value] = {}
        self._cut_out_speed: Dict[TechId, Value] = {}

        # aerodynamic / rotor params
        self._power_coefficient: Dict[TechId, Value] = {}
        self._rotor_diameter: Dict[TechId, Value] = {}
        self._hub_height: Dict[TechId, Value] = {}

        # curtailment bounds (defaults if missing)
        self._curtail_max_rel: Dict[TechId, Value] = {}
        self._curtail_min_rel: Dict[TechId, Value] = {}

        # hub-specific overrides (applies to all wind techs at the hub)
        self._curtail_max_rel_hub: Dict[HubId, Value] = {}
        self._curtail_min_rel_hub: Dict[HubId, Value] = {}

        # area requirement per turbine (per TechId)
        self._area_per_turbine: Dict[TechId, Value] = {}

        # optional allow-list of terrains per technology
        self._allowed_terrains: Dict[TechId, Set[str]] = {}

    # ---------- #
    # Validation #
    # ---------- #
    def validate(
        self,
        ecs: Ecs,
        techs: Techs,
        terrain_keys: Set[str] | None = None,
    ) -> None:
        """
        Validate all wind technology data in this object. Apart from sense-
        checking parameter in terms of quantity, this includes checking whether
        the ids from other data classes used here are known there as well.

        :param ecs: Ecs data class
        :type ecs: Ecs
        :param techs: Technology data class
        :type techs: Techs
        """
        self._validate_ids(techs)
        self._validate_ec(ecs)
        self._validate_specs()
        self._validate_area_per_turbine()
        self._validate_aero_params()
        self._validate_curtailment()
        if terrain_keys is not None:
            self._validate_allowed_terrains(terrain_keys)

    def _validate_ids(self, techs: Techs) -> None:
        exc_key = ExceptionKey.ID_VAL.value
        for x in self._ids:
            # wind_tech not in techs
            if x not in techs.ids:
                msg = f"wind_tech {x} not part of techs"
                raise exceptions.DataException(exc_key, [x], msg, module=LOG_MODULE_STR)

    def _validate_ec(self, ecs: Ecs) -> None:
        exc_key = ExceptionKey.EC_VAL.value
        for x, e in self._ec.items():
            # Unknown ec
            if e not in ecs.ids:
                msg = f"Unknown ec in ec[{x}] = {e}"
                raise exceptions.DataException(
                    exc_key, [x, e], msg, module=LOG_MODULE_STR
                )

    def _validate_specs(self) -> None:
        exc_key = ExceptionKey.SPECS_VAL.value
        speed_unit = LengthUnit.M / TimeUnit.S

        for x in self._ids:
            # required: rated_power, cut_in_speed, cut_out_speed
            if (
                x not in self._rated_power
                or x not in self._cut_in_speed
                or x not in self._cut_out_speed
            ):
                raise exceptions.DataException(
                    exc_key,
                    [x],
                    "Missing turbine specs. "
                    "Required: rated_power_kw, cut_in_speed_ms, cut_out_speed_ms",
                    module=LOG_MODULE_STR,
                )

            p = self._rated_power[x].to_float(unit=PowerUnit.KW)
            if p <= 0:
                raise exceptions.DataException(
                    exc_key,
                    [x],
                    f"rated_power_kw[{x}] must be > 0",
                    module=LOG_MODULE_STR,
                )

            cut_in_speed = self._cut_in_speed[x].to_float(unit=speed_unit)
            cut_out_speed = self._cut_out_speed[x].to_float(unit=speed_unit)

            if not (0 <= cut_in_speed < cut_out_speed):
                raise exceptions.DataException(
                    exc_key,
                    [x],
                    (
                        "Expected 0 <= cut_in_speed < cut_out_speed "
                        f"for {x}, got {cut_in_speed}, {cut_out_speed}"
                    ),
                    module=LOG_MODULE_STR,
                )

    def _validate_area_per_turbine(self) -> None:
        """
        Validate area requirement per turbine.

        Rules:
        - each wind tech must define it
        - must be > 0
        - unit must be of type area (length^2), we validate via conversion to m^2
        """
        exc_key = ExceptionKey.AREA_VAL.value
        area_unit = LengthUnit.M * LengthUnit.M

        for x in self._ids:
            if x not in self._area_per_turbine:
                raise exceptions.DataException(
                    exc_key,
                    [x],
                    "Missing wind param 'area_per_turbine_km2' for wind tech",
                    module=LOG_MODULE_STR,
                )

            a = self._area_per_turbine[x].to_float(unit=area_unit)
            if a <= 0.0:
                raise exceptions.DataException(
                    exc_key,
                    [x],
                    f"area_per_turbine[{x}] must be > 0",
                    module=LOG_MODULE_STR,
                )

    def _validate_curtailment(self) -> None:
        exc_key = ExceptionKey.SPECS_VAL.value

        def _check_pair(
            min_rel: Value, max_rel: Value, x: TechId, h: HubId | None = None
        ):
            ids = [h, x] if h is not None else [x]
            if not (Value(0) <= min_rel <= Value(1)):
                raise exceptions.DataException(
                    exc_key,
                    ids,
                    f"curtail_min_rel must be in [0,1], got {min_rel}",
                    module=LOG_MODULE_STR,
                )
            if not (Value(0) <= max_rel <= Value(1)):
                raise exceptions.DataException(
                    exc_key,
                    ids,
                    f"curtail_max_rel must be in [0,1], got {max_rel}",
                    module=LOG_MODULE_STR,
                )
            if min_rel > max_rel:
                raise exceptions.DataException(
                    exc_key,
                    ids,
                    f"Expected curtail_min_rel <= curtail_max_rel, "
                    f"got {min_rel} > {max_rel}",
                    module=LOG_MODULE_STR,
                )

        # tech-level
        for x in self._ids:
            _check_pair(
                self.get_curtail_min_rel(x),
                self.get_curtail_max_rel(x),
                x,
            )

        # hub overrides — applies to all wind techs at the hub
        all_hubs = set(self._curtail_max_rel_hub) | set(self._curtail_min_rel_hub)
        for h in all_hubs:
            hub_max = self._curtail_max_rel_hub.get(h, self.DEF_CURTAIL_MAX_REL)
            hub_min = self._curtail_min_rel_hub.get(h, self.DEF_CURTAIL_MIN_REL)
            if not (Value(0) <= hub_min <= Value(1)):
                raise exceptions.DataException(
                    exc_key, [h],
                    f"curtail_min_rel hub override must be in [0,1], got {hub_min}",
                    module=LOG_MODULE_STR,
                )
            if not (Value(0) <= hub_max <= Value(1)):
                raise exceptions.DataException(
                    exc_key, [h],
                    f"curtail_max_rel hub override must be in [0,1], got {hub_max}",
                    module=LOG_MODULE_STR,
                )
            if hub_min > hub_max:
                raise exceptions.DataException(
                    exc_key, [h],
                    f"Expected curtail_min_rel <= curtail_max_rel for hub override, "
                    f"got {hub_min} > {hub_max}",
                    module=LOG_MODULE_STR,
                )

    def _validate_aero_params(self) -> None:
        exc_key = ExceptionKey.SPECS_VAL.value

        for x in self._ids:
            if x not in self._power_coefficient:
                raise exceptions.DataException(
                    exc_key,
                    [x],
                    "Missing wind param 'power_coefficient' for wind tech",
                    module=LOG_MODULE_STR,
                )
            if x not in self._rotor_diameter:
                raise exceptions.DataException(
                    exc_key,
                    [x],
                    "Missing wind param 'rotor_diameter_m' for wind tech",
                    module=LOG_MODULE_STR,
                )

            cp = self._power_coefficient[x].to_float(unit=DimlessUnit())
            if not (0.0 < cp <= 1.0):
                raise exceptions.DataException(
                    exc_key,
                    [x],
                    f"power_coefficient[{x}] must be in (0,1], got {cp}",
                    module=LOG_MODULE_STR,
                )

            d = self._rotor_diameter[x].to_float(unit=LengthUnit.M)
            if d <= 0.0:
                raise exceptions.DataException(
                    exc_key,
                    [x],
                    f"rotor_diameter_m[{x}] must be > 0, got {d}",
                    module=LOG_MODULE_STR,
                )

    def _validate_allowed_terrains(self, terrain_keys: Set[str]) -> None:
        exc_key = ExceptionKey.ALLOWEDTERRAINS_VAL.value
        for x, allowed_terrains in self._allowed_terrains.items():
            self._check_id(x, ExceptionKey.ALLOWEDTERRAINS_VAL)
            for terrain in allowed_terrains:
                if terrain not in terrain_keys:
                    raise exceptions.DataException(
                        exc_key,
                        [x],
                        (
                            f"Unknown terrain '{terrain}' in allowed_terrains of "
                            f"wind tech '{x.key}'. Known terrains: "
                            f"{sorted(terrain_keys)}"
                        ),
                        module=LOG_MODULE_STR,
                    )

    # ---------- #
    # Id checker #
    # ---------- #
    def _check_id(self, x: TechId, key: ExceptionKey) -> None:
        if x not in self._ids:
            raise exceptions.UnknownIdException(key.value, x, module=LOG_MODULE_STR)
