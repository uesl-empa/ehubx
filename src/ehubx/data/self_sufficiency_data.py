"""
Self-sufficiency data module
"""

from enum import Enum

from ehubx.core import logging
from ehubx.data import exceptions
from ehubx.data.ec_data import Ecs, ImpExpType
from ehubx.data.export_data import Exports
from ehubx.data.import_data import Imports
from ehubx.data.value import Value


class SelfSufficiencyCalculationMethod(Enum):
    """How the self-sufficiency module is calculated"""

    NONE = "none"
    """Self-sufficiency module is not calculated at all"""

    LINEARIZED = "linearized"
    """The expected range of the variable tuple (V_SelfSufficiencyImpInternal,
    V_Self-sufficiencyImpCross) is approximated as a rectangle divided into triangles,
    and a binary variable is used per triangle for the linearization of the
    quadratic self-sufficiency constraint"""

    QUADRATIC = "quadratic"
    """Quadratic self-sufficiency constraint is used directly"""


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the self-sufficiency data module
    """

    SELFSUFFICIENCYMIN_VAL = "validating 'self_sufficiency_min' of self-sufficiency"
    SELFSUFFICIENCYMAX_VAL = "validating 'self_sufficiency_max' of self-sufficiency"
    SELFSUFFICIENCYMINMAX_VAL = (
        "validating 'self_sufficiency_min' against "
        "'self_sufficiency_max' of self-sufficiency"
    )


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "data/self_sufficiency"
"""String identifying the self-sufficiency data module for logging purposes"""

DEF_SELFSUFFICIENCYMIN: float = 0
"""Default value for parameter 'self_sufficiency_min' in the self-sufficiency data
module"""

DEF_SELFSUFFICIENCYMAX: float = 1
"""Default value for parameter 'self_sufficiency_max' in the self-sufficiency data
module"""


class SelfSufficiency:
    """
    Class to hold self-sufficiency data
    """

    # ---------------------------- #
    # Property: calculation_method #
    # ---------------------------- #
    calculation_method: SelfSufficiencyCalculationMethod = (
        SelfSufficiencyCalculationMethod.NONE
    )
    """How the self-sufficiency module is calculated"""

    # ------------------------------ #
    # Property: self_sufficiency_min #
    # ------------------------------ #
    self_sufficiency_min: Value = Value(DEF_SELFSUFFICIENCYMIN)
    """Minimal system-wide self-sufficiency value"""

    # ------------------------------ #
    # Property: self_sufficiency_max #
    # ------------------------------ #
    self_sufficiency_max: Value = Value(DEF_SELFSUFFICIENCYMAX)
    """Maximal system-wide self-sufficiency value"""

    # ---------- #
    # Validation #
    # ---------- #
    def validate(self, ecs: Ecs, imports: Imports, exports: Exports) -> None:
        self._validate_self_sufficiency_minmax()
        self._validate_export_nonexistence(ecs, imports, exports)

    def _validate_self_sufficiency_minmax(self) -> None:
        # self_sufficiency_min usually nonnegative
        if self.self_sufficiency_min.is_negative:
            msg = f"{self.self_sufficiency_min} = self_sufficiency_min < 0"
            logging.log_warning(msg, module=LOG_MODULE_STR)
        # self_sufficiency_min must not be larger than one
        if self.self_sufficiency_min > Value(1):
            msg = f"{self.self_sufficiency_min} = self_sufficiency_min > 1"
            raise exceptions.DataException(
                ExceptionKey.SELFSUFFICIENCYMIN_VAL.value,
                [],
                msg,
                module=LOG_MODULE_STR,
            )
        # self_sufficiency_max must not be smaller than zero
        if self.self_sufficiency_max.is_negative:
            msg = f"{self.self_sufficiency_max} = self_sufficiency_max < 0"
            raise exceptions.DataException(
                ExceptionKey.SELFSUFFICIENCYMAX_VAL.value,
                [],
                msg,
                module=LOG_MODULE_STR,
            )
        # self_sufficiency_max usually not larger than one
        if self.self_sufficiency_max > Value(1):
            msg = f"{self.self_sufficiency_max} = self_sufficiency_max > 1"
            logging.log_warning(msg, module=LOG_MODULE_STR)
        # self_sufficiency_min must not be larger than self_sufficiency_max
        if self.self_sufficiency_min > self.self_sufficiency_max:
            msg = (
                f"{self.self_sufficiency_min} = self_sufficiency_min > "
                f"self_sufficiency_max = {self.self_sufficiency_max}"
            )
            raise exceptions.DataException(
                ExceptionKey.SELFSUFFICIENCYMINMAX_VAL.value,
                [],
                msg,
                module=LOG_MODULE_STR,
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
                        "unrealistic system behavior if self-sufficiency is chosen "
                        "as an objective. If that is the case, consider "
                        "removing this ec from the exports."
                    )
                    logging.log_file_warning(msg, module=LOG_MODULE_STR)
