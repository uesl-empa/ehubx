"""
Solar technology data module
"""
from typing import Dict, List, Set, Tuple
from enum import Enum
from ehubx.core import logging
from ehubx.data.stage_data import Stages, StageId
from ehubx.data.hub_data import Hubs
from ehubx.data.import_data import Imports
from ehubx.data.tech_data import Techs, TechId
from ehubx.data.conv_tech_data import ConversionTechs
from ehubx.data.solar_data import SolarData
from ehubx.data import exceptions


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the solar technology data
    module
    """
    ID_ADD = "adding to 'ids' of SolarTechs"
    ID_REMOVE = "removing from 'ids' of SolarTechs"
    ID_VAL = "validating 'ids' of SolarTechs"
    INECS_VAL = "validating 'in_ecs' of SolarTechs"
    OUTECS_VAL = "validating 'out_ecs' of SolarTechs"
    ECSIMPORTABLE_VAL = "validating importability of solar ecs"
    CURTAILMAXREL_SET = "setting 'curtail_max_rel' of SolarTechs"
    CURTAILMAXREL_GET = "getting 'curtail_max_rel' from SolarTechs"
    CURTAILMAXREL_VAL = "validating 'curtail_max_rel' of SolarTechs"
    AREACAPMININIT_VAL = ("validating 'cap_min' and 'cap_init' of Techs "
                          "against 'area' of SolarData")


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/solar_tech"
"""String identifying the solar technology data module for logging purposes"""

DEF_CURTAILMAXREL: float = 1
"""Default value for parameter 'curtail_max_rel' in the solar technology data
module"""


class SolarTechs:
    """
    Class for solar technology data. Manages solar technology ids, contains
    getters and setters for solar technology parameters and validation methods
    to control data integrity
    """

    # ------------- #
    # Property: ids #
    # ------------- #
    @property
    def ids(self) -> Set[TechId]:
        """
        Set of known solar technology ids
        """
        return self._ids

    @property
    def ids_in_order(self) -> List[TechId]:
        """
        Set of known solar technology ids in alphabetical order
        """
        ids = list(self.ids)
        ids.sort(key=lambda x: x.key)
        return ids

    def add_id(self, x: TechId) -> None:
        """
        Add a new solar technology id

        :param x: Id to be added
        :type x: TechId
        """
        if x in self._ids:
            raise exceptions.DuplicateIdException(ExceptionKey.ID_ADD.value, x,
                                                  module=LOG_MODULE_STR)
        self._ids.add(x)

    # ------------------------- #
    # Property: curtail_max_rel #
    # ------------------------- #
    def get_curtail_max_rel(self, s: StageId, x: TechId) -> float:
        """
        Get the parameter 'curtail_max_rel' which denotes the fraction of solar
        irradiation power that can be curtailed by a solar technology. A
        curtail_max_rel value of e.g.; 0.4 indicates that at least 60% of the
        irradiation power has to be converted into electrical power. This is an
        optional parameter with a default value of 1.

        :param s: Stage id
        :type s: StageId
        :param x: Id of solar technology
        :type x: TechId
        :return: Relative amount of maximal curtailment [1]
        :rtype: float
        """
        self._check_id(x, ExceptionKey.CURTAILMAXREL_GET)
        return self._curtail_max_rel.get((s, x), DEF_CURTAILMAXREL)

    def set_curtail_max_rel(self, s: StageId, x: TechId,
                            curtail_max_rel: float) -> None:
        """
        Set the parameter 'curtail_max_rel' which denotes the fraction of solar
        irradiation power that can be curtailed by a solar technology. A
        curtail_max_rel value of e.g.; 0.4 indicates that at least 60% of the
        irradiation power has to be converted into electrical power. This is an
        optional parameter with a default value of 1.

        :param s: Stage id
        :type s: StageId
        :param x: Id of solar technology
        :type x: TechId
        :param curtail_max_rel: Relative amount of maximal curtailment [1]
        :type curtail_max_rel: float
        """
        self._check_id(x, ExceptionKey.CURTAILMAXREL_SET)
        self._curtail_max_rel[s, x] = curtail_max_rel

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        self._ids: Set[TechId] = set()
        self._curtail_max_rel: Dict[Tuple[StageId, TechId], float] = {}

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self, stages: Stages, hubs: Hubs, imports: Imports,
                 techs: Techs, conv_techs: ConversionTechs,
                 solar_data: SolarData) -> None:
        """
        Validate all solar technology data in this object. Apart from sense-
        checking parameter in terms of quantity, this includes checking whether
        the ids from other data classes used here are known there as well.

        :param stages: Stages data class
        :type stages: Stages
        :param hubs: Hubs data class
        :type hubs: Hubs
        :param imports: Imports data class
        :type imports: Imports
        :param techs: Technology data class
        :type techs: Techs
        :param conv_techs: Conversion technology data class
        :type conv_techs: ConversionTechs
        :param solar_data: Solar data class
        :type solar_data: SolarData
        """
        self._validate_ids(conv_techs)
        self._validate_in_ecs(conv_techs, solar_data)
        self._validate_out_ecs(conv_techs)
        self._validate_ec_importability(techs, conv_techs, imports)
        self._validate_curtail_max_rel(stages)
        self._validate_capmininit_area(stages, hubs, techs, conv_techs,
                                       solar_data)

    def _validate_ids(self, conv_techs: ConversionTechs) -> None:
        exc_key = ExceptionKey.ID_VAL.value
        for x in self._ids:
            # solar_tech not in conv_techs
            if x not in conv_techs.ids:
                msg = f"solar_tech {x} not part of conv_techs"
                raise exceptions.DataException(exc_key, [x], msg,
                                               module=LOG_MODULE_STR)

    def _validate_in_ecs(self, conv_techs: ConversionTechs,
                         solar_data: SolarData) -> None:
        exc_key = ExceptionKey.INECS_VAL.value
        for x in self.ids:
            in_ecs = conv_techs.get_in_ecs(x)
            # Solar techs must have exactly one input ec
            if len(in_ecs) != 1:
                msg = (f"{x} has more than one input ec. Input ecs are: "
                       f"{in_ecs}")
                raise exceptions.DataException(exc_key, [x], msg,
                                               module=LOG_MODULE_STR)
            in_ec = list(in_ecs)[0]
            if in_ec not in solar_data.ecs:
                msg = f"{x} has input ec {in_ec} which is not a solar ec"
                raise exceptions.DataException(exc_key, [x, in_ec], msg,
                                               module=LOG_MODULE_STR)

    def _validate_out_ecs(self, conv_techs: ConversionTechs) -> None:
        exc_key = ExceptionKey.OUTECS_VAL.value
        for x in self.ids:
            out_ecs = conv_techs.get_out_ecs(x)
            # Solar techs must have exactly one output ec
            if len(out_ecs) != 1:
                msg = (f"{x} has more than one output ec. Output ecs are: "
                       f"{out_ecs}")
                raise exceptions.DataException(exc_key, [x], msg,
                                               module=LOG_MODULE_STR)

    def _validate_ec_importability(self, techs: Techs,
                                   conv_techs: ConversionTechs,
                                   imports: Imports) -> None:
        for x in self.ids:
            in_ec = conv_techs.get_in_ec_main(x)
            for s in techs.get_allowed_stages(x):
                for h in techs.get_allowed_hubs(x):
                    if (s, h, in_ec) not in imports.tuples:
                        msg = (f"{x} is allowed in stage {s} and hub {h} but "
                               f"its in_ec {in_ec} is not importable there")
                        logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_curtail_max_rel(self, stages: Stages) -> None:
        exc_key = ExceptionKey.CURTAILMAXREL_VAL.value
        for (s, x), curtail_max_rel in self._curtail_max_rel.items():
            # Unknown stage
            if s not in stages.ids:
                msg = f"Unknown stage {s} in curtail_max_rel[{s}, {x}]"
                raise exceptions.DataException(exc_key, [s, x], msg,
                                               module=LOG_MODULE_STR)
            # curtail_max_rel must be nonnegative
            if curtail_max_rel < 0:
                msg = f"{curtail_max_rel} = curtail_max_rel[{s}, {x}] < 0"
                raise exceptions.DataException(exc_key, [s, x], msg,
                                               module=LOG_MODULE_STR)
            # curtail_max_rel must not be larger than 1
            if curtail_max_rel > 1:
                msg = f"{curtail_max_rel} = curtail_max_rel[{s}, {x}] > 1"
                raise exceptions.DataException(exc_key, [s, x], msg,
                                               module=LOG_MODULE_STR)

    def _validate_capmininit_area(self, stages: Stages, hubs: Hubs,
                                  techs: Techs, conv_techs: ConversionTechs,
                                  solar_data: SolarData) -> None:
        for x in self.ids:
            in_ec = conv_techs.get_in_ec_main(x)
            for h in hubs.ids:
                cap_init = techs.get_cap_init(h, x)
                for s in stages.ids:
                    cap_min = techs.get_cap_min(s, h, x)
                    solar_area = solar_data.get_area(s, h, in_ec)
                    # Solar area should not be smaller than initial capacity
                    if solar_area < cap_init:
                        msg = (f"{x} has cap_init[{h}, {x}] = {cap_init} "
                               f"which exceeds solar_area[{s}, {h}, {in_ec}] "
                               f"= {solar_area} for {x}'s input ec {in_ec}")
                        logging.log_warning(msg, module=LOG_MODULE_STR)
                    # Solar area should not be smaller than minimal capacity
                    if solar_area < cap_min:
                        msg = (f"{x} has cap_min[{s}, {h}, {x}] = {cap_min} "
                               f"which exceeds solar_area[{s}, {h}, {in_ec}] "
                               f"= {solar_area} for {x}'s input ec {in_ec}")
                        logging.log_warning(msg, module=LOG_MODULE_STR)

    # ---------- #
    # Id checker #
    # ---------- #
    def _check_id(self, x: TechId, key: ExceptionKey) -> None:
        if x not in self._ids:
            raise exceptions.UnknownIdException(key.value, x,
                                                module=LOG_MODULE_STR)
