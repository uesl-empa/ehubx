"""
Autarky data module
"""

from enum import Enum

from ehubx.core import logging
from ehubx.data import exceptions
from ehubx.data.ec_data import Ecs, ImpExpType
from ehubx.data.export_data import Exports
from ehubx.data.import_data import Imports


class AutarkyCalculationMethod(Enum):
    """How the autarky module is calculated"""

    NONE = "none"
    """Autarky module is not calculated at all"""

    LINEARIZED = "linearized"
    """The expected range of the variable tuple (V_AutarkyImpInternal,
    V_AutarkyImpCross) is approximated as a rectangle divided into triangles,
    and a binary variable is used per triangle for the linearization of the
    quadratic autarky constraint"""

    QUADRATIC = "quadratic"
    """Quadratic autarky constraint is used directly"""


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the autarky data module
    """

    AUTARKYMIN_VAL = "validating 'autarky_min' of Autarky"
    AUTARKYMAX_VAL = "validating 'autarky_max' of Autarky"
    AUTARKYMINMAX_VAL = "validating 'autarky_min' against 'autarky_max' of Autarky"


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/autarky"
"""String identifying the autarky data module for logging purposes"""

DEF_AUTARKYMIN: float = 0
"""Default value for parameter 'autarky_min' in the autarky data module"""

DEF_AUTARKYMAX: float = 1
"""Default value for parameter 'autarky_max' in the autarky data module"""


class Autarky:
    """
    Class to hold autarky data
    """

    # ---------------------------- #
    # Property: calculation_method #
    # ---------------------------- #
    calculation_method: AutarkyCalculationMethod = AutarkyCalculationMethod.NONE
    """How the autarky module is calculated"""

    # --------------------- #
    # Property: autarky_min #
    # --------------------- #
    autarky_min: float = DEF_AUTARKYMIN
    """Minimal system-wide autarky value"""

    # --------------------- #
    # Property: autarky_max #
    # --------------------- #
    autarky_max: float = DEF_AUTARKYMAX
    """Maximal system-wide autarky value"""

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self, ecs: Ecs, imports: Imports, exports: Exports) -> None:
        self._validate_autarky_minmax()
        self._validate_export_nonexistence(ecs, imports, exports)

    def _validate_autarky_minmax(self) -> None:
        # autarky_min usually nonnegative
        if self.autarky_min < 0:
            msg = f"{self.autarky_min} = autarky_min < 0"
            logging.log_warning(msg, module=LOG_MODULE_STR)
        # autarky_min must not be larger than one
        if self.autarky_min > 1:
            msg = f"{self.autarky_min} = autarky_min > 1"
            raise exceptions.DataException(
                ExceptionKey.AUTARKYMIN_VAL.value, [], msg, module=LOG_MODULE_STR
            )
        # autarky_max must not be smaller than zero
        if self.autarky_max < 0:
            msg = f"{self.autarky_max} = autarky_max < 0"
            raise exceptions.DataException(
                ExceptionKey.AUTARKYMAX_VAL.value, [], msg, module=LOG_MODULE_STR
            )
        # autarky_max usually not larger than one
        if self.autarky_max > 1:
            msg = f"{self.autarky_max} = autarky_max > 1"
            logging.log_warning(msg, module=LOG_MODULE_STR)
        # autarky_min must not be larger than autarky_max
        if self.autarky_min > self.autarky_max:
            msg = f"{self.autarky_min} = autarky_min < autarky_max = {self.autarky_max}"
            raise exceptions.DataException(
                ExceptionKey.AUTARKYMINMAX_VAL.value, [], msg, module=LOG_MODULE_STR
            )

    def _validate_export_nonexistence(
        self, ecs: Ecs, imports: Imports, exports: Exports
    ) -> None:
        for s, h, e in exports.tuples:
            if ecs.is_energy(e) and ecs.get_imp_exp_type(e) == ImpExpType.CROSS:
                if (s, h, e) in imports.tuples:
                    msg = (
                        f"Detected that ec {e} is of import-export-type "
                        "'cross' and has 'is_energy'=True. Furthermore, it "
                        f"can be both imported and exported in stage {s} "
                        f"and hub {h}. This will most likely lead to "
                        "unrealistic system behavior if autarky is chosen "
                        "as an objective. If that is the case, consider "
                        "removing this ec from the exports."
                    )
                    logging.log_file_warning(msg, module=LOG_MODULE_STR)
