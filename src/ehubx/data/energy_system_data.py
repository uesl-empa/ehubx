"""
Energy system data module. This module deals with system-wide parameters and
additionally acts as an umbrella class which manages the other data classes
"""

import copy
from datetime import datetime
from enum import Enum
from typing import List, Optional, Set, Tuple

from ehubx.core import logging
from ehubx.core.common import TimeSeriesKind
from ehubx.data import exceptions
from ehubx.data.ates_data import AtesData
from ehubx.data.ates_tech_data import AtesTechs
from ehubx.data.autarky_data import Autarky
from ehubx.data.conv_tech_data import ConversionTechs, copy_over_conv_tech
from ehubx.data.demand_data import Demands
from ehubx.data.ebm_tech_data import EbmTechs
from ehubx.data.ec_data import Ecs
from ehubx.data.export_data import Exports
from ehubx.data.hp_tech_data import HeatpumpTechs
from ehubx.data.hub_data import Hubs
from ehubx.data.import_data import Imports
from ehubx.data.load_shedding_data import LoadShedding
from ehubx.data.load_shifting_data import LoadShifting
from ehubx.data.net_link_data import NetworkLinks
from ehubx.data.net_tech_data import NetworkTechs
from ehubx.data.solar_data import SolarData
from ehubx.data.solar_tech_data import SolarTechs
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.stor_tech_data import StorageTechs
from ehubx.data.tech_data import Techs, copy_over_tech
from ehubx.data.time_data import TimeId, Times
from ehubx.data.time_series import TimeSeries
from ehubx.data.wind_data import WindData
from ehubx.data.wind_tech_data import WindTechs


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the energy system data
    module
    """

    TRLTHRESHOLD_VAL = "validating 'trl_threshold' of EnergySystem"
    INTERESTRATEDEF_GET = "getting 'interest_rate_def' from EnergySystem"
    INTERESTRATEDEF_VAL = "validating 'interest_rate_def' of EnergySystem"
    NUMTIMESHORIZON_GET = "getting 'num_times_horizon' from EnergySystem"
    NUMTIMESHORIZON_VAL = "validating 'num_times_horizon' of EnergySystem"


# -------- #
# Literals #
# -------- #
DEF_TRLTHRESHOLD: int = 0
"""Default value for parameter 'trl_threshold' in the energy system data
module"""

LOG_MODULE_STR: str = "data/system"
"""String identifying the energy system data module for logging purposes"""


class EnergySystem:
    """
    Class for data of the overall energy system. On the one hand, this class
    contains getters and setters for system-wide parameters and validation
    methods to control data integrity. On the other hand, it acts as an
    umbrella class of the data module, managing the other data classes as its
    attributes.
    """

    # ----------- #
    # Constructor #
    # ----------- #
    def __init__(self) -> None:
        # Properties
        self._interest_rate_def: Optional[float] = None
        self._trl_threshold: Optional[int] = None
        self._num_times_horizon: Optional[int] = None
        self._demand_file_paths: Set[str] = set()

        # Modules
        self.stages = Stages()
        self.hubs = Hubs()
        self.net_links = NetworkLinks()
        self.ecs = Ecs()
        self.imports = Imports()
        self.exports = Exports()
        self.demands = Demands()
        self.load_shedding = LoadShedding()
        self.load_shifting = LoadShifting()
        self.techs = Techs()
        self.stor_techs = StorageTechs()
        self.ebm_techs = EbmTechs()
        self.conv_techs = ConversionTechs()
        self.solar_techs = SolarTechs()
        self.wind_techs = WindTechs()
        self.hp_techs = HeatpumpTechs()
        self.ates_techs = AtesTechs()
        self.net_techs = NetworkTechs()
        self.autarky = Autarky()
        self.ates_data = AtesData()
        self.solar_data = SolarData()
        self.wind_data = WindData()
        self.times = Times()

        # Deactivated modules (stored for reactivation)
        self._deactivated_links: Optional[NetworkLinks] = None
        self._deactivated_imports: Optional[Imports] = None
        self._deactivated_exports: Optional[Exports] = None
        self._deactivated_demands: Optional[Demands] = None
        self._deactivated_load_shedding: Optional[LoadShedding] = None
        self._deactivated_load_shifting: Optional[LoadShifting] = None
        self._deactivated_techs: Techs = Techs()
        self._deactivated_stor_techs: Optional[StorageTechs] = None
        self._deactivated_ebm_techs: Optional[EbmTechs] = None
        self._deactivated_conv_techs: ConversionTechs = ConversionTechs()
        self._deactivated_solar_techs: Optional[SolarTechs] = None
        self._deactivated_wind_techs: Optional[WindTechs] = None
        self._deactivated_hp_techs: Optional[HeatpumpTechs] = None
        self._deactivated_ates_techs: Optional[AtesTechs] = None
        self._deactivated_net_techs: Optional[NetworkTechs] = None
        self._deactivated_autarky: Optional[Autarky] = None
        self._deactivated_ates_data: Optional[AtesData] = None
        self._deactivated_solar_data: Optional[SolarData] = None
        self._deactivated_wind_data: Optional[WindData] = None

        # Manual deactivation flags
        self.techs_deactivated: bool = False
        self.conv_techs_deactivated: bool = False

    # ---------------------------------- #
    # Property: interest_rate_categories #
    # ---------------------------------- #
    @property
    def interest_rate_def(self) -> float:
        """Default interest rate value used in the calculation of annuity
        costs. This is used everywhere in the model where no specific interest
        rate is specified instead (e.g.; for technologies). This is a mandatory
        parameter."""
        if self._interest_rate_def is None:
            raise exceptions.MissingValueException(
                ExceptionKey.INTERESTRATEDEF_GET.value, module=LOG_MODULE_STR
            )
        return self._interest_rate_def

    @interest_rate_def.setter
    def interest_rate_def(self, interest_rate_def: float) -> None:
        self._interest_rate_def = interest_rate_def

    # ------------- #
    # Property: TRL #
    # ------------- #
    @property
    def trl_threshold(self) -> int:
        """Threshold value for the Technology Readiness Level (TRL) value.
        Technologies can only be used in stages where their TRL is above this
        threshold level. This is an optional parameter with a default value of
        0."""
        if self._trl_threshold is None:
            return DEF_TRLTHRESHOLD
        return self._trl_threshold

    @trl_threshold.setter
    def trl_threshold(self, trl_threshold: int) -> None:
        self._trl_threshold = trl_threshold

    # --------------------------- #
    # Property: num_times_horizon #
    # --------------------------- #
    @property
    def num_times_horizon(self) -> int:
        """Number of horizon time steps in the system. This value must fit the
        length of all input time series in the data model. This is a mandatory
        parameter."""
        if self._num_times_horizon is None:
            raise exceptions.MissingValueException(
                ExceptionKey.NUMTIMESHORIZON_GET.value, module=LOG_MODULE_STR
            )
        return self._num_times_horizon

    @num_times_horizon.setter
    def num_times_horizon(self, num_times_horizon: int) -> None:
        self._num_times_horizon = num_times_horizon

    # ------------------------------- #
    # Secondary property: time_series #
    # ------------------------------- #
    @property
    def time_series(
        self,
    ) -> List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...], TimeSeries]]:
        """
        Time series profiles in the system. This is a list of tuples. Each
        list element has the following list entries: 1) ProfileKind of the
        profile. 2) Stage. 3) Tuple of string identifiers specific to the
        ProfileKind (usually ids excluding stage). 4) The TimeSeries itself

        :return: Time series of the energy system
        :rtype: List[Tuple[TimeSeriesKind, StageId, Tuple[str, ...],
            TimeSeries]]:
        """
        all_series: List[
            Tuple[TimeSeriesKind, StageId, Tuple[str, ...], TimeSeries]
        ] = []
        all_series += self.imports.time_series
        all_series += self.exports.time_series
        all_series += self.demands.time_series
        all_series += self.load_shedding.time_series
        # This does currently not work, which is the reason why clustering is
        # forbidden with load shifting data:
        # all_series += self.load_shifting.time_series
        all_series += self.conv_techs.time_series
        all_series += self.ebm_techs.time_series
        all_series += self.hp_techs.time_series
        all_series += self.solar_data.time_series
        all_series += self.wind_data.time_series
        all_series += self.net_links.time_series
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
        Set the value for a time series in the energy system data. The time
        series should be uniquely identified by the time series kind, the
        stage id and the remaining tuples.

        :param kind: Kind of time series
        :type kind: TimeSeriesKind
        :param s: Stage
        :type s: StageId
        :param ids: Remaining ids, other than stage and time
        :type ids: Tuple[str, ...]
        :param t: Time id
        :type t: TimeId
        :param value: Value to set
        :type value: float
        """
        self.imports.set_time_series_val(kind, s, ids, t, value)
        self.exports.set_time_series_val(kind, s, ids, t, value)
        self.demands.set_time_series_val(kind, s, ids, t, value)
        self.load_shedding.set_time_series_val(kind, s, ids, t, value)
        self.load_shifting.set_time_series_val(kind, s, ids, t, value)
        self.conv_techs.set_time_series_val(kind, s, ids, t, value)
        self.ebm_techs.set_time_series_val(kind, s, ids, t, value)
        self.hp_techs.set_time_series_val(kind, s, ids, t, value)
        self.solar_data.set_time_series_val(kind, s, ids, t, value)
        self.wind_data.set_time_series_val(kind, s, ids, t, value)
        self.net_links.set_time_series_val(kind, s, ids, t, value)

    # ------------------------- #
    # Module deactivation flags #
    # ------------------------- #
    @property
    def imports_deactivated(self) -> bool:
        """Whether the import module has been deactivated"""
        return self._deactivated_imports is not None

    @property
    def exports_deactivated(self) -> bool:
        """Whether the export module has been deactivated"""
        return self._deactivated_exports is not None

    @property
    def demands_deactivated(self) -> bool:
        """Whether the demand module has been deactivated"""
        return self._deactivated_demands is not None

    @property
    def load_shedding_deactivated(self) -> bool:
        """Whether the load shedding module has been deactivated"""
        return self._deactivated_load_shedding is not None

    @property
    def load_shifting_deactivated(self) -> bool:
        """Whether the load shifting module has been deactivated"""
        return self._deactivated_load_shifting is not None

    @property
    def network_deactivated(self) -> bool:
        """Whether the network module has been deactivated"""
        return self._deactivated_links is not None

    @property
    def stor_techs_deactivated(self) -> bool:
        """Whether the storage technology module has been deactivated"""
        return self._deactivated_stor_techs is not None

    @property
    def ebm_techs_deactivated(self) -> bool:
        """Whether the EBM technology module has been deactivated"""
        return self._deactivated_ebm_techs is not None

    @property
    def solar_techs_deactivated(self) -> bool:
        """Whether the solar technology module has been deactivated"""
        return self._deactivated_solar_techs is not None

    @property
    def wind_techs_deactivated(self) -> bool:
        """Whether the wind technology module has been deactivated"""
        return self._deactivated_wind_techs is not None

    @property
    def hp_techs_deactivated(self) -> bool:
        """Whether the heat pump technology module has been deactivated"""
        return self._deactivated_hp_techs is not None

    @property
    def ates_techs_deactivated(self) -> bool:
        """Whether the ATES technology module has been deactivated"""
        return self._deactivated_ates_techs is not None

    @property
    def autarky_deactivated(self) -> bool:
        """Whether the autarky module has been deactivated"""
        return self._deactivated_autarky is not None

    # ------------------- #
    # Module deactivation #
    # ------------------- #
    def deactivate_imports(self) -> None:
        """Deactivate the imports module. This resets the import data class but
        saves a copy for later reactivation."""
        if self.imports_deactivated:
            logging.log_warning(
                "Tried to deactivate already deactivated import module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        self._deactivated_imports = copy.deepcopy(self.imports)
        self.imports = Imports()
        logging.log("Deactivated import module", module=LOG_MODULE_STR)

    def deactivate_exports(self) -> None:
        """Deactivate the exports module. This resets the export data class but
        saves a copy for later reactivation."""
        if self.exports_deactivated:
            logging.log_warning(
                "Tried to deactivate already deactivated export module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        self._deactivated_exports = copy.deepcopy(self.exports)
        self.exports = Exports()
        logging.log("Deactivated export module", module=LOG_MODULE_STR)

    def deactivate_demands(self) -> None:
        """Deactivate the demand module. This resets the demand data class but
        saves a copy for later reactivation. It also triggers the deactivation
        of both the load shedding and load shifting modules-"""
        if self.demands_deactivated:
            logging.log_warning(
                "Tried to deactivate already deactivated demand module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        if not self.load_shedding_deactivated:
            logging.log(
                (
                    "Triggering load shedding module deactivation due to "
                    " demand module deactivation ..."
                ),
                module=LOG_MODULE_STR,
            )
            self.deactivate_load_shedding()
        if not self.load_shifting_deactivated:
            logging.log(
                (
                    "Triggering load shifting module deactivation due to "
                    "demand module deactivation ..."
                ),
                module=LOG_MODULE_STR,
            )
            self.deactivate_load_shifting()
        self._deactivated_demands = copy.deepcopy(self.demands)
        self.demands = Demands()
        logging.log("Deactivated demand module", module=LOG_MODULE_STR)

    def deactivate_load_shedding(self) -> None:
        """Deactivate the load shedding module. This resets the load shedding
        data class but saves a copy for later reactivation."""
        if self.load_shedding_deactivated:
            logging.log_warning(
                "Tried to deactivate already deactivated "
                "load shedding module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        self._deactivated_load_shedding = copy.deepcopy(self.load_shedding)
        self.load_shedding = LoadShedding()
        logging.log("Deactivated load shedding module", module=LOG_MODULE_STR)

    def deactivate_load_shifting(self) -> None:
        """Deactivate the load shifting module. This resets the load shifting
        data class but saves a copy for later reactivation."""
        if self.load_shifting_deactivated:
            logging.log_warning(
                "Tried to deactivate already deactivated "
                "load shifting module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        self._deactivated_load_shifting = copy.deepcopy(self.load_shifting)
        self.load_shifting = LoadShifting()
        logging.log("Deactivated load shifting module", module=LOG_MODULE_STR)

    def deactivate_ebm(self) -> None:
        """Deactivate the EBM technology module. This resets the EBM technology
        data class  but saves a copy for later reactivation."""
        raise NotImplementedError()

    def deactivate_network(self) -> None:
        """Deactivate the network module. This resets the network data class
        but saves a copy for later reactivation."""
        if self.network_deactivated:
            logging.log_warning(
                "Tried to deactivate already deactivated network module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        self._deactivated_links = copy.deepcopy(self.net_links)
        self._deactivated_net_techs = copy.deepcopy(self.net_techs)
        self.net_links = NetworkLinks()
        self.net_techs = NetworkTechs()
        logging.log("Deactivated network module", module=LOG_MODULE_STR)

    def deactivate_techs(self) -> None:
        """Deactivate the technology module. This resets the technology data
        class but saves a copy for later reactivation. It also triggers the
        deactivation of the conversion, storage, EBM and heat pump technology
        modules."""
        # Can only deactivate active module
        if self.techs_deactivated:
            logging.log_warning(
                "Tried to deactivate already deactivated tech module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        # Create backup of techs
        for x in self.techs.ids:
            if x not in self._deactivated_techs.ids:
                copy_over_tech(
                    x, self.techs, self._deactivated_techs, self.stages, self.hubs
                )
        # Trigger submodule deactivations
        if not self.stor_techs_deactivated:
            logging.log(
                "Triggering storage tech module deactivation due to "
                "tech module deactivation ...",
                module=LOG_MODULE_STR,
            )
            self.deactivate_stor_techs()
        if not self.conv_techs_deactivated:
            logging.log(
                "Triggering conversion tech module deactivation due "
                "to conversion tech module deactivation ...",
                module=LOG_MODULE_STR,
            )
            self.deactivate_conv_techs()
        if not self.ebm_techs_deactivated:
            logging.log(
                "Triggering EBM tech module deactivation due to "
                "tech module deactivation ...",
                module=LOG_MODULE_STR,
            )
            self.deactivate_ebm_techs()
        if not self.hp_techs_deactivated:
            logging.log(
                "Triggering heat pump tech module deactivation due to "
                "tech module deactivation ...",
                module=LOG_MODULE_STR,
            )
            self.deactivate_hp_techs()
        if not self.ates_techs_deactivated:
            logging.log(
                "Triggering ATES tech module deactivation due to "
                "tech module deactivation ...",
                module=LOG_MODULE_STR,
            )
            self.deactivate_ates_techs()
        # Deactivate module
        self.techs = Techs()
        self.techs_deactivated = True
        logging.log("Deactivated tech module", module=LOG_MODULE_STR)

    def deactivate_stor_techs(self) -> None:
        """Deactivate the storage technology module. This resets the storage
        technology data class but saves a copy for later reactivation."""
        # Can only deactivate active module
        if self.stor_techs_deactivated:
            logging.log_warning(
                "Tried to deactivate already deactivated "
                "storage tech module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        # Create backups of stor_techs and the ids in techs
        self._deactivated_stor_techs = copy.deepcopy(self.stor_techs)
        for x in self.stor_techs.ids.copy():
            if x not in self._deactivated_techs.ids:
                copy_over_tech(
                    x, self.techs, self._deactivated_techs, self.stages, self.hubs
                )
        # Deactivate module
        for x in self.stor_techs.ids:
            self.techs.remove_id(x)
        self.stor_techs = StorageTechs()
        logging.log("Deactivated storage tech module", module=LOG_MODULE_STR)

    def deactivate_ebm_techs(self) -> None:
        """Deactivate the EBM technology module. This resets the EBM
        technology data class but saves a copy for later reactivation."""
        # Can only deactivate active module
        if self.ebm_techs_deactivated:
            logging.log_warning(
                "Tried to deactivate already deactivated EBM tech module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        # Create backups of ebm_techs and the ids in techs
        self._deactivated_ebm_techs = copy.deepcopy(self.ebm_techs)
        for x in self.ebm_techs.ids.copy():
            if x not in self._deactivated_techs.ids:
                copy_over_tech(
                    x, self.techs, self._deactivated_techs, self.stages, self.hubs
                )
        # Deactivate module
        for x in self.ebm_techs.ids:
            self.techs.remove_id(x)
        self.ebm_techs = EbmTechs()
        logging.log("Deactivated EBM tech module", module=LOG_MODULE_STR)

    def deactivate_hp_techs(self) -> None:
        """Deactivate the heat pump technology module. This resets the heat
        pump technology data class but saves a copy for later reactivation."""
        # Can only deactivate active module
        if self.hp_techs_deactivated:
            logging.log_warning(
                "Tried to deactivate already deactivated "
                "heat pump tech module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        # Create backups of hp_techs and the ids in techs
        self._deactivated_hp_techs = copy.deepcopy(self.hp_techs)
        for x in self.hp_techs.ids.copy():
            if x not in self._deactivated_techs.ids:
                copy_over_tech(
                    x, self.techs, self._deactivated_techs, self.stages, self.hubs
                )
        # Deactivate module
        for x in self.hp_techs.ids:
            self.techs.remove_id(x)
        self.hp_techs = HeatpumpTechs()
        logging.log("Deactivated heat pump tech module", module=LOG_MODULE_STR)

    def deactivate_ates_techs(self) -> None:
        """Deactivate the ATES technology module. This resets the ATES
        technology data class butsaves a copy for later reactivation."""
        # Can only deactivate active module
        if self.ates_techs_deactivated:
            logging.log_warning(
                "Tried to deactivate already deactivated "
                "ATES tech module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        # Create backups of ates_techs, ates_data and the ids in techs
        self._deactivated_ates_techs = copy.deepcopy(self.ates_techs)
        self._deactivated_ates_data = copy.deepcopy(self.ates_data)
        for x in self.ates_techs.ids.copy():
            if x not in self._deactivated_techs.ids:
                copy_over_tech(
                    x, self.techs, self._deactivated_techs, self.stages, self.hubs
                )
        # Deactivate module
        for x in self.ates_techs.ids:
            self.techs.remove_id(x)
        self.ates_techs = AtesTechs()
        self.ates_data = AtesData()
        logging.log("Deactivated ATES tech module", module=LOG_MODULE_STR)

    def deactivate_conv_techs(self) -> None:
        """Deactivate the conversion technology module. This resets the
        conversion technology data class but saves a copy for later
        reactivation. It also triggers the deactivation of the solar technology
        and wind technology modules."""
        if self.conv_techs_deactivated:
            logging.log_warning(
                "Tried to deactivate already deactivated "
                "conversion tech module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        # Create backups of conv_techs and the ids in techs
        for x in self.conv_techs.ids.copy():
            if x not in self._deactivated_conv_techs.ids:
                copy_over_conv_tech(
                    x,
                    self.conv_techs,
                    self._deactivated_conv_techs,
                    self.stages,
                    self.hubs,
                    self.times,
                )
            if x not in self._deactivated_techs.ids:
                copy_over_tech(
                    x, self.techs, self._deactivated_techs, self.stages, self.hubs
                )
        # Trigger submodule deactivation
        if not self.solar_techs_deactivated:
            logging.log(
                "Triggering solar tech module deactivation due to "
                "conversion tech module deactivation ...",
                module=LOG_MODULE_STR,
            )
            self.deactivate_solar_techs()
        if not self.wind_techs_deactivated:
            logging.log(
                "Triggering wind tech module deactivation due to "
                "conversion tech module deactivation ...",
                module=LOG_MODULE_STR,
            )
            self.deactivate_wind_techs()
        # Deactivate module
        for x in self.conv_techs.ids.copy():
            self.techs.remove_id(x)
        self.conv_techs = ConversionTechs()
        self.conv_techs_deactivated = True
        logging.log("Deactivated conversion tech module", module=LOG_MODULE_STR)

    def deactivate_solar_techs(self) -> None:
        """Deactivate the solar technology module. This resets the solar
        technology data class and solar data classes but saves copies for later
        reactivation."""
        # Can only deactivate active module
        if self.solar_techs_deactivated:
            logging.log_warning(
                "Tried to deactivate already deactivated "
                "solar tech module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        # Create backups of solar_techs, solar_data, and the ids in conv_techs
        # and techs
        self._deactivated_solar_techs = copy.deepcopy(self.solar_techs)
        self._deactivated_solar_data = copy.deepcopy(self.solar_data)
        for x in self.solar_techs.ids:
            if x not in self._deactivated_conv_techs.ids:
                copy_over_conv_tech(
                    x,
                    self.conv_techs,
                    self._deactivated_conv_techs,
                    self.stages,
                    self.hubs,
                    self.times,
                )
            if x not in self._deactivated_techs.ids:
                copy_over_tech(
                    x, self.techs, self._deactivated_techs, self.stages, self.hubs
                )
        # Deactivate module
        for x in self.solar_techs.ids.copy():
            self.conv_techs.remove_id(x)
            self.techs.remove_id(x)
        self.solar_techs = SolarTechs()
        self.solar_data = SolarData()
        logging.log("Deactivated solar tech module", module=LOG_MODULE_STR)

    def deactivate_wind_techs(self) -> None:
        """Deactivate the wind technology module. This resets the wind
        technology data class and wind data class but saves copies for later
        reactivation."""
        # Can only deactivate active module
        if self.wind_techs_deactivated:
            logging.log_warning(
                "Tried to deactivate already deactivated "
                "wind tech module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        # Create backups of solar_techs, solar_data, and the ids in conv_techs
        # and techs
        self._deactivated_wind_techs = copy.deepcopy(self.wind_techs)
        self._deactivated_wind_data = copy.deepcopy(self.wind_data)
        for x in self.wind_techs.ids:
            if x not in self._deactivated_conv_techs.ids:
                copy_over_conv_tech(
                    x,
                    self.conv_techs,
                    self._deactivated_conv_techs,
                    self.stages,
                    self.hubs,
                    self.times,
                )
            if x not in self._deactivated_techs.ids:
                copy_over_tech(
                    x, self.techs, self._deactivated_techs, self.stages, self.hubs
                )
        # Deactivate module
        for x in self.wind_techs.ids.copy():
            self.conv_techs.remove_id(x)
            self.techs.remove_id(x)
        self.wind_techs = WindTechs()
        self.wind_data = WindData()
        logging.log("Deactivated wind tech module", module=LOG_MODULE_STR)

    def deactivate_autarky(self) -> None:
        """Deactivate the autarky module. This resets the autarky data class
        but saves a copy for later reactivation."""
        raise NotImplementedError()

    # ------------------- #
    # Module reactivation #
    # ------------------- #
    def reactivate_imports(self) -> None:
        """Reactivate the import module. This tries to overwrite the current
        import data class with the stashed version from deactivation."""
        # Can only reactivate deactivated modules
        if not self.imports_deactivated:
            logging.log_warning(
                "Tried to reactivate not-deactivated import module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        deactivated_imports = copy.deepcopy(self._deactivated_imports)
        assert deactivated_imports is not None
        self.imports = deactivated_imports
        self._deactivated_imports = None
        logging.log("Reactivated import module", module=LOG_MODULE_STR)

    def reactivate_exports(self) -> None:
        """Reactivate the export module. This tries to overwrite the current
        export data class with the stashed version from deactivation."""
        # Can only reactivate deactivated modules
        if not self.exports_deactivated:
            logging.log_warning(
                "Tried to reactivate not-deactivated export module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        deactivated_exports = copy.deepcopy(self._deactivated_exports)
        assert deactivated_exports is not None
        self.exports = deactivated_exports
        self._deactivated_exports = None
        logging.log("Reactivated export module", module=LOG_MODULE_STR)

    def reactivate_demands(self) -> None:
        """Reactivate the demand module. This tries to overwrite the current
        demand data class with the stashed version from deactivation."""
        # Can only reactivate deactivated modules
        if not self.demands_deactivated:
            logging.log_warning(
                "Tried to reactivate not-deactivated demand module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        deactivated_demands = copy.deepcopy(self._deactivated_demands)
        assert deactivated_demands is not None
        self.demands = deactivated_demands
        self._deactivated_demands = None
        logging.log("Reactivated demand module", module=LOG_MODULE_STR)

    def reactivate_load_shedding(self) -> None:
        """Reactivate the load shedding module. This tries to overwrite the
        current load shedding data class with the stashed version from
        deactivation. If the demand module is deactivated as well, it will be
        reactivated."""
        # Can only reactivate deactivated modules
        if not self.load_shedding_deactivated:
            logging.log_warning(
                "Tried to reactivate not-deactivated "
                "load shedding module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        if self.demands_deactivated:
            logging.log(
                "Triggering demand module reactivation due to "
                "load shedding module reactivation ...",
                module=LOG_MODULE_STR,
            )
            self.reactivate_demands()
        deactivated_load_shedding = copy.deepcopy(self._deactivated_load_shedding)
        assert deactivated_load_shedding is not None
        self.load_shedding = deactivated_load_shedding
        self._deactivated_load_shedding = None
        logging.log("Reactivated load shedding module", module=LOG_MODULE_STR)

    def reactivate_load_shifting(self) -> None:
        """Reactivate the load shifting module. This tries to overwrite the
        current load shifting data class with the stashed version from
        deactivation. If the demand module is deactivated as well, it will be
        reactivated."""
        # Can only reactivate deactivated modules
        if not self.load_shifting_deactivated:
            logging.log_warning(
                "Tried to reactivate not-deactivated "
                "load shifting module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        if self.demands_deactivated:
            logging.log(
                "Triggering demand module reactivation due to "
                "load shifting module reactivation ...",
                module=LOG_MODULE_STR,
            )
            self.reactivate_demands()
        deactivated_load_shifting = copy.deepcopy(self._deactivated_load_shifting)
        assert deactivated_load_shifting is not None
        self.load_shifting = deactivated_load_shifting
        self._deactivated_load_shifting = None
        logging.log("Reactivated load shifting module", module=LOG_MODULE_STR)

    def reactivate_network(self) -> None:
        """Reactivate the network module. This tries to overwrite the current
        network link and network technology data classes with the stashed
        versions from deactivation."""
        # Can only reactivate deactivated modules
        if not self.network_deactivated:
            logging.log_warning(
                "Tried to reactivate not-deactivated network module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        deactivated_links = copy.deepcopy(self._deactivated_links)
        deactivated_net_techs = copy.deepcopy(self._deactivated_net_techs)
        assert deactivated_links is not None
        assert deactivated_net_techs is not None
        self.net_links = deactivated_links
        self.net_techs = deactivated_net_techs
        self._deactivated_links = None
        self._deactivated_net_techs = None
        logging.log("Reactivated network module", module=LOG_MODULE_STR)

    def reactivate_techs(self) -> None:
        """Reactivate the technology module. This tries to overwrite the
        current technology data class with the stashed version from
        deactivation."""
        # Can only reactivate deactivated modules
        if not self.techs_deactivated:
            logging.log_warning(
                "Tried to reactivate not-deactivated tech module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        # Reactivate module
        self.techs = copy.deepcopy(self._deactivated_techs)
        self._deactivated_techs = Techs()
        self.techs_deactivated = False
        logging.log("Reactivated tech module", module=LOG_MODULE_STR)

    def reactivate_stor_techs(self) -> None:
        """Reactivate the storage technology module. This tries to overwrite
        current storage technology data class with the stashed version from
        deactivation. If the technology module is deactivated as well, it will
        be reactivated."""
        # Can only reactivate deactivated modules
        if not self.stor_techs_deactivated:
            logging.log_warning(
                "Tried to reactivate not-deactivated storage tech module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        # Trigger supermodule reactivation
        if self.techs_deactivated:
            logging.log(
                "Triggering tech module reactivation due to "
                "storage tech module reactivation ...",
                module=LOG_MODULE_STR,
            )
            self.reactivate_techs()
        else:
            # Manually reactivate the techs
            deactivated_stor_techs = copy.deepcopy(self._deactivated_stor_techs)
            assert deactivated_stor_techs is not None
            for x in deactivated_stor_techs.ids.copy():
                if x not in self.techs.ids:
                    copy_over_tech(
                        x, self._deactivated_techs, self.techs, self.stages, self.hubs
                    )
                    self._deactivated_techs.remove_id(x)
        # Reactivate module
        deactivated_stor_techs = copy.deepcopy(self._deactivated_stor_techs)
        assert deactivated_stor_techs is not None
        self.stor_techs = deactivated_stor_techs
        self._deactivated_stor_techs = None
        logging.log("Reactivated storage tech module", module=LOG_MODULE_STR)

    def reactivate_ebm_techs(self) -> None:
        """Reactivate the EBM technology module. This tries to overwrite the
        current EBM technology data class with the stashed version from
        deactivation. If the technology module is deactivated as well, it will
        be reactivated."""
        # Can only reactivate deactivated modules
        if not self.ebm_techs_deactivated:
            logging.log_warning(
                "Tried to reactivate not-deactivated EBM tech module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        # Trigger supermodule reactivation
        if self.techs_deactivated:
            logging.log(
                "Triggering tech module reactivation due to "
                "EBM tech module reactivation ...",
                module=LOG_MODULE_STR,
            )
            self.reactivate_techs()
        else:
            # Manually reactivate the techs
            deactivated_ebm_techs = copy.deepcopy(self._deactivated_ebm_techs)
            assert deactivated_ebm_techs is not None
            for x in deactivated_ebm_techs.ids.copy():
                if x not in self.techs.ids:
                    copy_over_tech(
                        x, self._deactivated_techs, self.techs, self.stages, self.hubs
                    )
                    self._deactivated_techs.remove_id(x)
        # Reactivate module
        deactivated_ebm_techs = copy.deepcopy(self._deactivated_ebm_techs)
        assert deactivated_ebm_techs is not None
        self.ebm_techs = deactivated_ebm_techs
        self._deactivated_ebm_techs = None
        logging.log("Reactivated EBM tech module", module=LOG_MODULE_STR)

    def reactivate_hp_techs(self) -> None:
        """Reactivate the heat pump technology module. This tries to overwrite
        the current heat pump technology data class with the stashed version
        from deactivation. If the technology module is deactivated as well, it
        will be reactivated."""
        # Can only reactivate deactivated modules
        if not self.hp_techs_deactivated:
            logging.log_warning(
                "Tried to reactivate not-deactivated "
                "heat pump tech module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        # Trigger supermodule reactivation
        if self.techs_deactivated:
            logging.log(
                "Triggering tech module reactivation due to "
                "heat pump tech module reactivation ...",
                module=LOG_MODULE_STR,
            )
            self.reactivate_techs()
        else:
            # Manually reactivate the techs
            deactivated_hp_techs = copy.deepcopy(self._deactivated_hp_techs)
            assert deactivated_hp_techs is not None
            for x in deactivated_hp_techs.ids.copy():
                if x not in self.techs.ids:
                    copy_over_tech(
                        x, self._deactivated_techs, self.techs, self.stages, self.hubs
                    )
                    self._deactivated_techs.remove_id(x)
        # Reactivate module
        deactivated_hp_techs = copy.deepcopy(self._deactivated_hp_techs)
        assert deactivated_hp_techs is not None
        self.hp_techs = deactivated_hp_techs
        self._deactivated_hp_techs = None
        logging.log("Reactivated heat pump tech module", module=LOG_MODULE_STR)

    def reactivate_ates_techs(self) -> None:
        """Reactivate the ATES technology module. This tries to overwrite
        the current ATES technology data class with the stashed version
        from deactivation. If the technology module is deactivated as well, it
        will be reactivated."""
        # Can only reactivate deactivated modules
        if not self.ates_techs_deactivated:
            logging.log_warning(
                "Tried to reactivate not-deactivated ATES tech module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        # Trigger supermodule reactivation
        if self.techs_deactivated:
            logging.log(
                "Triggering tech module reactivation due to "
                "ATES tech module reactivation ...",
                module=LOG_MODULE_STR,
            )
            self.reactivate_techs()
        else:
            # Manually reactivate the techs
            deactivated_ates_techs = copy.deepcopy(self._deactivated_ates_techs)
            assert deactivated_ates_techs is not None
            for x in deactivated_ates_techs.ids.copy():
                if x not in self.techs.ids:
                    copy_over_tech(
                        x, self._deactivated_techs, self.techs, self.stages, self.hubs
                    )
                    self._deactivated_techs.remove_id(x)
        # Reactivate module
        deactivated_ates_data = copy.deepcopy(self._deactivated_ates_data)
        deactivated_ates_techs = copy.deepcopy(self._deactivated_ates_techs)
        assert deactivated_ates_data is not None
        assert deactivated_ates_techs is not None
        self.ates_data = deactivated_ates_data
        self.ates_techs = deactivated_ates_techs
        self._deactivated_ates_techs = None
        self._deactivated_ates_data = None
        logging.log("Reactivated ATES tech module", module=LOG_MODULE_STR)

    def reactivate_conv_techs(self) -> None:
        """Reactivate the conversion technology module. This tries to overwrite
        the current conversion technology data class with the stashed version
        from deactivation. If the technology module is deactivated as well, it
        will be reactivated."""
        # Can only reactivate deactivated modules
        if not self.conv_techs_deactivated:
            logging.log_warning(
                "Tried to reactivate not-deactivated "
                "conversion tech module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        # Trigger supermodule reactivation
        if self.techs_deactivated:
            logging.log(
                "Triggering tech module reactivation due to "
                "conversion tech module reactivation ...",
                module=LOG_MODULE_STR,
            )
            self.reactivate_techs()
        else:
            # Manually reactivate the techs
            for x in self._deactivated_conv_techs.ids.copy():
                if x not in self.techs.ids:
                    copy_over_tech(
                        x, self._deactivated_techs, self.techs, self.stages, self.hubs
                    )
                    self._deactivated_techs.remove_id(x)
        # Reactivate module
        self.conv_techs = copy.deepcopy(self._deactivated_conv_techs)
        self._deactivated_conv_techs = ConversionTechs()
        self.conv_techs_deactivated = False
        logging.log("Reactivated conversion tech module", module=LOG_MODULE_STR)

    def reactivate_solar_techs(self) -> None:
        """Reactivate the solar technology module. This tries to overwrite
        the current solar technology data class with the stashed version
        from deactivation. If the conversion technology module is deactivated
        as well, it will be reactivated."""
        # Can only reactivate deactivated modules
        if not self.solar_techs_deactivated:
            logging.log_warning(
                "Tried to reactivate not-deactivated solar tech module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        # Trigger conv_tech module reactivation
        if self.conv_techs_deactivated:
            logging.log(
                "Triggering conversion tech module reactivation due "
                "to solar tech module reactivation ...",
                module=LOG_MODULE_STR,
            )
            self.reactivate_conv_techs()
        else:
            # Manually reactivate the conv_techs and techs
            deactivated_solar_techs = self._deactivated_solar_techs
            assert deactivated_solar_techs is not None
            for x in deactivated_solar_techs.ids:
                if x not in self.conv_techs.ids:
                    copy_over_conv_tech(
                        x,
                        self._deactivated_conv_techs,
                        self.conv_techs,
                        self.stages,
                        self.hubs,
                        self.times,
                    )
                    self._deactivated_conv_techs.remove_id(x)
                if x not in self.techs.ids:
                    copy_over_tech(
                        x, self._deactivated_techs, self.techs, self.stages, self.hubs
                    )
                    self._deactivated_techs.remove_id(x)
        # Reactivate the module
        deactivated_solar_data = copy.deepcopy(self._deactivated_solar_data)
        deactivated_solar_techs = copy.deepcopy(self._deactivated_solar_techs)
        assert deactivated_solar_data is not None
        assert deactivated_solar_techs is not None
        self.solar_data = deactivated_solar_data
        self.solar_techs = deactivated_solar_techs
        self._deactivated_solar_techs = None
        self._deactivated_solar_data = None
        logging.log("Reactivated solar tech module", module=LOG_MODULE_STR)

    def reactivate_wind_techs(self) -> None:
        """Reactivate the wind technology module. This tries to overwrite
        the current wind technology data class with the stashed version
        from deactivation. If the conversion technology module is deactivated
        as well, it will be reactivated."""
        # Can only reactivate deactivated modules
        if not self.wind_techs_deactivated:
            logging.log_warning(
                "Tried to reactivate not-deactivated wind tech module. Skipping ...",
                module=LOG_MODULE_STR,
            )
            return
        # Trigger conv_tech module reactivation
        if self.conv_techs_deactivated:
            logging.log(
                "Triggering conversion tech module reactivation due "
                "to wind tech module reactivation ...",
                module=LOG_MODULE_STR,
            )
            self.reactivate_conv_techs()
        else:
            # Manually reactivate the conv_techs and techs
            deactivated_wind_techs = self._deactivated_wind_techs
            assert deactivated_wind_techs is not None
            for x in deactivated_wind_techs.ids:
                if x not in self.conv_techs.ids:
                    copy_over_conv_tech(
                        x,
                        self._deactivated_conv_techs,
                        self.conv_techs,
                        self.stages,
                        self.hubs,
                        self.times,
                    )
                    self._deactivated_conv_techs.remove_id(x)
                if x not in self.techs.ids:
                    copy_over_tech(
                        x, self._deactivated_techs, self.techs, self.stages, self.hubs
                    )
                    self._deactivated_techs.remove_id(x)
        # Reactivate the module
        deactivated_wind_data = copy.deepcopy(self._deactivated_wind_data)
        deactivated_wind_techs = copy.deepcopy(self._deactivated_wind_techs)
        assert deactivated_wind_data is not None
        assert deactivated_wind_techs is not None
        self.wind_data = deactivated_wind_data
        self.wind_techs = deactivated_wind_techs
        self._deactivated_wind_techs = None
        self._deactivated_wind_data = None
        logging.log("Reactivated wind tech module", module=LOG_MODULE_STR)

    def reactivate_autarky(self) -> None:
        """Reactivate the autarky module. This tries to overwrite
        the current autarky data class with the stashed version from
        deactivation."""
        raise NotImplementedError("Autarky not implemented")

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self) -> None:
        """
        Validate all energy system data in this object. Apart from
        sense-checking energy system parameter in terms of quantity, this
        includes triggering the validation routines of all data classes
        contained in the module.
        """
        start_time = datetime.now()
        logging.log("Starting data validation ...", module=LOG_MODULE_STR)
        self._validate_self()
        self._validate_modules()
        elapsed = datetime.now() - start_time
        logging.log(
            f"Finished data validation. Elapsed time: {int(elapsed.total_seconds())}s",
            module=LOG_MODULE_STR,
        )

    def _validate_self(self) -> None:
        self._validate_trl_threshold()
        self._validate_interest_rate_def()
        self._validate_num_times_horizon()

    def _validate_trl_threshold(self) -> None:
        if self._trl_threshold is None:
            return
        if self._trl_threshold < 0:
            msg = f"{self._trl_threshold} = trl_threshold < 0"
            logging.log_warning(msg, module=LOG_MODULE_STR)

    def _validate_interest_rate_def(self) -> None:
        if self._interest_rate_def is None:
            return
        if self._interest_rate_def < 0:
            msg = f"{self._interest_rate_def} = interest_rate_def < 0"
            raise exceptions.DataException(
                ExceptionKey.INTERESTRATEDEF_VAL.value, [], msg, module=LOG_MODULE_STR
            )

    def _validate_num_times_horizon(self) -> None:
        if self._num_times_horizon is None:
            return
        if self._num_times_horizon <= 0:
            msg = f"{self._num_times_horizon} = num_times_horizon <= 0"
            raise exceptions.DataException(
                ExceptionKey.NUMTIMESHORIZON_VAL.value, [], msg, module=LOG_MODULE_STR
            )

    def _validate_modules(self) -> None:
        self.stages.validate()
        self.hubs.validate()
        self.ecs.validate()
        self.times.validate(self.stages)
        self.net_links.validate(self.stages, self.hubs, self.ecs, self.times)
        self.imports.validate(self.stages, self.hubs, self.ecs, self.times)
        self.exports.validate(self.stages, self.hubs, self.ecs, self.times)
        self.demands.validate(self.stages, self.hubs, self.ecs, self.times)
        self.load_shedding.validate(
            self.stages, self.hubs, self.ecs, self.demands, self.times
        )
        self.load_shifting.validate(
            self.stages, self.hubs, self.ecs, self.demands, self.times
        )
        self.techs.validate(self.stages, self.hubs)
        self.stor_techs.validate(self.stages, self.hubs, self.ecs, self.techs)
        self.ebm_techs.validate(
            self.stages, self.hubs, self.techs, self.ecs, self.times
        )
        self.conv_techs.validate(
            self.stages, self.hubs, self.ecs, self.techs, self.times
        )
        self.solar_data.validate(self.stages, self.hubs, self.ecs, self.times)
        self.solar_techs.validate(
            self.stages,
            self.hubs,
            self.imports,
            self.techs,
            self.conv_techs,
            self.solar_data,
        )
        self.wind_data.validate(self.stages, self.hubs, self.ecs, self.times)
        self.wind_techs.validate(
            self.stages,
            self.hubs,
            self.imports,
            self.techs,
            self.conv_techs,
            self.wind_data,
        )
        self.hp_techs.validate(self.stages, self.hubs, self.ecs, self.techs, self.times)
        self.ates_data.validate(self.stages, self.hubs, self.times)
        self.ates_techs.validate(
            self.stages, self.hubs, self.techs, self.ecs, self.ates_data
        )
        self.net_techs.validate(self.stages, self.net_links, self.ecs)
        self.autarky.validate(self.ecs, self.imports, self.exports)
