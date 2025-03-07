"""
Wind technology data module
"""

from enum import Enum
from typing import Dict, List, Set, Tuple

from ehubx.core import common, logging
from ehubx.data import exceptions
from ehubx.data.conv_tech_data import ConversionTechs
from ehubx.data.hub_data import Hubs
from ehubx.data.import_data import Imports
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.wind_data import WindData


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the wind technology data
    module
    """

    ID_ADD = "adding to 'ids' of WindTechs"
    ID_REMOVE = "removing from 'ids' of WindTechs"
    ID_VAL = "validating 'ids' of WindTechs"
    INECS_VAL = "validating 'in_ecs' of WindTechs"
    OUTECS_VAL = "validating 'out_ecs' of WindTechs"
    TURBINEFOOTPRINT_SET = "setting 'turbine_footprint' of WindTechs"
    TURBINEFOOTPRINT_GET = "getting 'turbine_footprint' from WindTechs"
    TURBINEFOOTPRINT_VAL = "validating 'turbine_footprint' of WindTechs"
    ROTORAREA_SET = "setting 'rotor_area' of WindTechs"
    ROTORAREA_GET = "getting 'rotor_area' from WindTechs"
    ROTORAREA_VAL = "validating 'rotor_area' of WindTechs"
    VELOCUTIN_SET = "setting 'velo_cut_in' of WindTechs"
    VELOCUTIN_GET = "getting 'velo_cut_in' from WindTechs"
    VELOCUTIN_VAL = "validating 'velo_cut_in' of WindTechs"
    VELONOMINAL_SET = "setting 'velo_nominal' of WindTechs"
    VELONOMINAL_GET = "getting 'velo_nominal' from WindTechs"
    VELONOMINAL_VAL = "validating 'velo_nominal' of WindTechs"
    VELOCUTOFF_SET = "setting 'velo_cut_off' of WindTechs"
    VELOCUTOFF_GET = "getting 'velo_cut_off' from WindTechs"
    VELOCUTOFF_VAL = "validating 'velo_cut_off' of WindTechs"
    VELOS_VAL = (
        "validating 'velo_cut_in', 'velo_nominal' and 'velo_cut_off"
        "of WindTechs against each other"
    )
    CURTAILMAXREL_SET = "setting 'curtail_max_rel' of WindTechs"
    CURTAILMAXREL_GET = "getting 'curtail_max_rel' from WindTechs"
    CURTAILMAXREL_VAL = "validating 'curtail_max_rel' of WindTechs"
    CAPMININITAREA_VAL = (
        "validating 'cap_min' and 'cap_init' of Techs "
        "against 'windpark_area' of WindData"
    )


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/wind_tech"
"""String identifying the wind technology data module for logging purposes"""

DEF_CURTAILMAXREL: float = 1
"""Default value for parameter 'curtail_max_rel' in the wind technology data
module"""


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

    # --------------------------- #
    # Property: turbine_footprint #
    # --------------------------- #
    def get_turbine_footprint(self, s: StageId, x: TechId) -> float:
        self._check_id(x, ExceptionKey.TURBINEFOOTPRINT_GET)
        turbine_footprint = self._turbine_footprint.get((s, x), None)
        if turbine_footprint is None:
            raise exceptions.MissingIdsException(
                ExceptionKey.TURBINEFOOTPRINT_GET.value, [s, x], module=LOG_MODULE_STR
            )
        return turbine_footprint

    def set_turbine_footprint(
        self, s: StageId, x: TechId, turbine_footprint: float
    ) -> None:
        self._check_id(x, ExceptionKey.TURBINEFOOTPRINT_SET)
        self._turbine_footprint[s, x] = turbine_footprint

    # -------------------- #
    # Property: rotor_area #
    # -------------------- #
    def get_rotor_area(self, s: StageId, x: TechId) -> float:
        self._check_id(x, ExceptionKey.ROTORAREA_GET)
        rotor_area = self._rotor_area.get((s, x), None)
        if rotor_area is None:
            raise exceptions.MissingIdsException(
                ExceptionKey.ROTORAREA_GET.value, [s, x], module=LOG_MODULE_STR
            )
        return rotor_area

    def set_rotor_area(self, s: StageId, x: TechId, rotor_area: float) -> None:
        self._check_id(x, ExceptionKey.ROTORAREA_SET)
        self._rotor_area[s, x] = rotor_area

    # --------------------- #
    # Property: velo_cut_in #
    # --------------------- #
    def get_velo_cut_in(self, s: StageId, x: TechId) -> float:
        self._check_id(x, ExceptionKey.VELOCUTIN_GET)
        velo_cut_in = self._velo_cut_in.get((s, x), None)
        if velo_cut_in is None:
            raise exceptions.MissingIdsException(
                ExceptionKey.VELOCUTIN_GET.value, [s, x], module=LOG_MODULE_STR
            )
        return velo_cut_in

    def set_velo_cut_in(self, s: StageId, x: TechId, velo_cut_in: float) -> None:
        self._check_id(x, ExceptionKey.VELOCUTIN_SET)
        self._velo_cut_in[s, x] = velo_cut_in

    # ---------------------- #
    # Property: velo_cut_off #
    # ---------------------- #
    def get_velo_cut_off(self, s: StageId, x: TechId) -> float:
        self._check_id(x, ExceptionKey.VELOCUTOFF_GET)
        velo_cut_off = self._velo_cut_off.get((s, x), None)
        if velo_cut_off is None:
            raise exceptions.MissingIdsException(
                ExceptionKey.VELOCUTOFF_GET.value, [s, x], module=LOG_MODULE_STR
            )
        return velo_cut_off

    def set_velo_cut_off(self, s: StageId, x: TechId, velo_cut_off: float) -> None:
        self._check_id(x, ExceptionKey.VELOCUTOFF_SET)
        self._velo_cut_off[s, x] = velo_cut_off

    # ---------------------- #
    # Property: velo_nominal #
    # ---------------------- #
    def get_velo_nominal(self, s: StageId, x: TechId) -> float:
        self._check_id(x, ExceptionKey.VELONOMINAL_GET)
        velo_nominal = self._velo_nominal.get((s, x), None)
        if velo_nominal is None:
            raise exceptions.MissingIdsException(
                ExceptionKey.VELONOMINAL_GET.value, [s, x], module=LOG_MODULE_STR
            )
        return velo_nominal

    def set_velo_nominal(self, s: StageId, x: TechId, velo_nominal: float) -> None:
        self._check_id(x, ExceptionKey.VELONOMINAL_SET)
        self._velo_nominal[s, x] = velo_nominal

    # ------------------------- #
    # Property: curtail_max_rel #
    # ------------------------- #
    def get_curtail_max_rel(self, s: StageId, x: TechId) -> float:
        self._check_id(x, ExceptionKey.CURTAILMAXREL_GET)
        return self._curtail_max_rel.get((s, x), DEF_CURTAILMAXREL)

    def set_curtail_max_rel(
        self, s: StageId, x: TechId, curtail_max_rel: float
    ) -> None:
        self._check_id(x, ExceptionKey.CURTAILMAXREL_SET)
        self._curtail_max_rel[s, x] = curtail_max_rel

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._ids: Set[TechId] = set()
        self._turbine_footprint: Dict[Tuple[StageId, TechId], float] = {}
        self._rotor_area: Dict[Tuple[StageId, TechId], float] = {}
        self._velo_cut_in: Dict[Tuple[StageId, TechId], float] = {}
        self._velo_cut_off: Dict[Tuple[StageId, TechId], float] = {}
        self._velo_nominal: Dict[Tuple[StageId, TechId], float] = {}
        self._curtail_max_rel: Dict[Tuple[StageId, TechId], float] = {}

    # ---------- #
    # Validation #
    # ---------- #
    def validate(
        self,
        stages: Stages,
        hubs: Hubs,
        imports: Imports,
        techs: Techs,
        conv_techs: ConversionTechs,
        wind_data: WindData,
    ) -> None:
        """
        Validate all wind technology data in this object. Apart from sense-
        checking parameter in terms of quantity, this includes checking whether
        the ids from other data classes used here are known there as well.

        :param stages: Stages data class
        :type stages: Stages
        :param hubs: Hubs data class
        :type hubs: Hubs
        :param imports: Imports data class
        :type imports: Improts
        :param techs: Technology data class
        :type techs: Techs
        :param conv_techs: Conversion technology data class
        :type conv_techs: ConversionTechs
        """
        self._validate_ids(conv_techs)
        self._validate_in_ecs(conv_techs, wind_data)
        self._validate_ec_importability(techs, conv_techs, imports)
        self._validate_out_ecs(conv_techs)
        self._validate_turbine_footprint(stages)
        self._validate_rotor_area(stages)
        self._validate_velo_cut_in(stages)
        self._validate_velo_nominal(stages)
        self._validate_velo_cut_off(stages)
        self._validate_velos()
        self._validate_curtail_max_rel(stages)
        self._validate_capmininit_area(stages, hubs, techs, conv_techs, wind_data)

    def _validate_ids(self, conv_techs: ConversionTechs) -> None:
        exc_key = ExceptionKey.ID_VAL.value
        for x in self._ids:
            # solar_tech not in conv_techs
            if x not in conv_techs.ids:
                msg = f"wind_tech {x} not part of conv_techs"
                raise exceptions.DataException(exc_key, [x], msg, module=LOG_MODULE_STR)

    def _validate_in_ecs(
        self, conv_techs: ConversionTechs, wind_data: WindData
    ) -> None:
        exc_key = ExceptionKey.INECS_VAL.value
        for x in self.ids:
            in_ecs = conv_techs.get_in_ecs(x)
            # Wind techs must have exactly one input ec
            if len(in_ecs) != 1:
                msg = f"{x} has more than one input ec. Input ecs are: {in_ecs}"
                raise exceptions.DataException(exc_key, [x], msg, module=LOG_MODULE_STR)
            in_ec = list(in_ecs)[0]
            if in_ec not in wind_data.ecs:
                msg = f"{x} has input ec {in_ec} which is not a wind ec"
                raise exceptions.DataException(
                    exc_key, [x, in_ec], msg, module=LOG_MODULE_STR
                )

    def _validate_out_ecs(self, conv_techs: ConversionTechs) -> None:
        exc_key = ExceptionKey.OUTECS_VAL.value
        for x in self.ids:
            out_ecs = conv_techs.get_out_ecs(x)
            # Wind techs must have exactly one output ec
            if len(out_ecs) != 1:
                msg = f"{x} has more than one output ec. Output ecs are: {out_ecs}"
                raise exceptions.DataException(exc_key, [x], msg, module=LOG_MODULE_STR)

    def _validate_ec_importability(
        self, techs: Techs, conv_techs: ConversionTechs, imports: Imports
    ) -> None:
        for x in self.ids:
            in_ec = conv_techs.get_in_ec_main(x)
            for s in techs.get_allowed_stages(x):
                for h in techs.get_allowed_hubs(x):
                    if (s, h, in_ec) not in imports.tuples:
                        msg = (
                            f"{x} is allowed in stage {s} and hub {h} but "
                            f"its in_ec {in_ec} is not importable there"
                        )
                        logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_turbine_footprint(self, stages: Stages) -> None:
        exc_key = ExceptionKey.TURBINEFOOTPRINT_VAL.value
        for (s, x), turbine_footprint in self._turbine_footprint.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in turbine_footprint[{s}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # turbine_footprint must be nonnegative
            if turbine_footprint < 0:
                msg = f"{turbine_footprint} = turbine_footprint[{s}, {x}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # turbine_footprint is usually positive
            if turbine_footprint < common.EPS_ZEROCHECK:
                msg = f"{turbine_footprint} = turbine_footprint[{s}, {x}] ~ 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_rotor_area(self, stages: Stages) -> None:
        exc_key = ExceptionKey.ROTORAREA_VAL.value
        for (s, x), rotor_area in self._rotor_area.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in rotor_area[{s}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # rotor_area must be nonnegative
            if rotor_area < 0:
                msg = f"{rotor_area} = rotor_area[{s}, {x}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # rotor_area is usually positive
            if rotor_area < common.EPS_ZEROCHECK:
                msg = f"{rotor_area} = rotor_area[{s}, {x}] ~ 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_velo_cut_in(self, stages: Stages) -> None:
        exc_key = ExceptionKey.ROTORAREA_VAL.value
        for (s, x), velo_cut_in in self._velo_cut_in.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in velo_cut_in[{s}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # velo_cut_in must be nonnegative
            if velo_cut_in < 0:
                msg = f"{velo_cut_in} = velo_cut_in[{s}, {x}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )

    def _validate_velo_nominal(self, stages: Stages) -> None:
        exc_key = ExceptionKey.ROTORAREA_VAL.value
        for (s, x), velo_nominal in self._velo_nominal.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in velo_nominal[{s}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # velo_nominal must be nonnegative
            if velo_nominal < 0:
                msg = f"{velo_nominal} = velo_nominal[{s}, {x}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # velo_nominal is usually positive
            if velo_nominal < common.EPS_ZEROCHECK:
                msg = f"{velo_nominal} = velo_nominal[{s}, {x}] ~ 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_velo_cut_off(self, stages: Stages) -> None:
        exc_key = ExceptionKey.ROTORAREA_VAL.value
        for (s, x), velo_cut_off in self._velo_cut_off.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in velo_cut_off[{s}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # velo_cut_off must be nonnegative
            if velo_cut_off < 0:
                msg = f"{velo_cut_off} = velo_cut_off[{s}, {x}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # velo_cut_off is usually positive
            if velo_cut_off < common.EPS_ZEROCHECK:
                msg = f"{velo_cut_off} = velo_cut_off[{s}, {x}] ~ 0"
                logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_velos(self) -> None:
        exc_key = ExceptionKey.VELOS_VAL.value
        keys = set(self._velo_cut_in.keys()).union(
            set(self._velo_nominal.keys()).union(set(self._velo_cut_off))
        )
        for s, x in keys:
            velo_cut_in = self.get_velo_cut_in(s, x)
            velo_nominal = self.get_velo_nominal(s, x)
            velo_cut_off = self.get_velo_cut_off(s, x)
            # velo_cut_in must not be larger than velo_nominal
            if velo_cut_in > velo_nominal:
                msg = (
                    f"{velo_cut_in} = velo_cut_in[{s}, {x}] > "
                    f"velo_nominal[{s}, {x}] = {velo_nominal}"
                )
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # velo_nominal must not be larger than velo_cut_off
            if velo_nominal > velo_cut_off:
                msg = (
                    f"{velo_nominal} = velo_nominal[{s}, {x}] > "
                    f"velo_cut_off[{s}, {x}] = {velo_cut_off}"
                )
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )

    def _validate_curtail_max_rel(self, stages: Stages) -> None:
        exc_key = ExceptionKey.CURTAILMAXREL_VAL.value
        for (s, x), curtail_max_rel in self._curtail_max_rel.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in curtail_max_rel[{s}, {x}]"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # curtail_max_rel must be nonnegative
            if curtail_max_rel < 0:
                msg = f"{curtail_max_rel} = curtail_max_rel[{s}, {x}] < 0"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )
            # curtail_max_rel must not be larger than 1
            if curtail_max_rel > 1:
                msg = f"{curtail_max_rel} = curtail_max_rel[{s}, {x}] > 1"
                raise exceptions.DataException(
                    exc_key, [s, x], msg, module=LOG_MODULE_STR
                )

    def _validate_capmininit_area(
        self,
        stages: Stages,
        hubs: Hubs,
        techs: Techs,
        conv_techs: ConversionTechs,
        wind_data: WindData,
    ) -> None:
        exc_key = ExceptionKey.CAPMININITAREA_VAL.value
        # Minimal capacity and area
        for s in stages.ids:
            for h in hubs.ids:
                for e in wind_data.ecs:
                    area_min = sum(
                        techs.get_cap_min(s, h, x)
                        for x in self.ids
                        if conv_techs.get_in_ec_main(x) == e
                    )
                    area_available = sum(
                        wind_data.get_windpark_area(s, h, wp)
                        for wp in wind_data.windpark_ids
                        if e in wind_data.get_windpark_ecs(wp)
                    )
                    # area_min must not be larger than area_available
                    if area_min > area_available:
                        msg = (
                            f"For stage {s}, hub {h} and ec {e}, only "
                            f"an area of {area_available} is available "
                            f"for capacity. But due to cap_min values, an "
                            f"area of at least {area_min} must be covered."
                        )
                        raise exceptions.DataException(
                            exc_key, [s, h, e], msg, module=LOG_MODULE_STR
                        )
        # Initial capacity and area
        for s in stages.ids:
            current_year = stages.get_start_year(s)
            for h in hubs.ids:
                for e in wind_data.ecs:
                    area_init: float = 0
                    for x in self.ids:
                        if conv_techs.get_in_ec_main(x) != e:
                            continue
                        tech_lifetime = techs.get_lifetime(x)
                        age_init = techs.get_age_init(h, x)
                        # If tech is still alive, initial capacity remains
                        if current_year - stages.init_year < tech_lifetime - age_init:
                            area_init += techs.get_cap_init(h, x)
                    area_available = sum(
                        wind_data.get_windpark_area(s, h, wp)
                        for wp in wind_data.windpark_ids
                        if e in wind_data.get_windpark_ecs(wp)
                    )
                    # area_init must not be larger than area_available
                    if area_init > area_available:
                        msg = (
                            f"For stage {s}, hub {h} and ec {e}, only "
                            f"an area of {area_available} is available "
                            "for capacity. But due to cap_init values, an "
                            f"area of at least {area_init} must be "
                            "covered."
                        )
                        raise exceptions.DataException(
                            exc_key, [s, h, e], msg, module=LOG_MODULE_STR
                        )

    # ---------- #
    # Id checker #
    # ---------- #
    def _check_id(self, x: TechId, key: ExceptionKey) -> None:
        if x not in self._ids:
            raise exceptions.UnknownIdException(key.value, x, module=LOG_MODULE_STR)
