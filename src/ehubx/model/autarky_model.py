"""Autarky submodel"""
from datetime import datetime
from enum import Enum
from pyomo.core import Constraint, Model, NonNegativeReals, Param, Var
from ehubx.core import logging
from ehubx.data.stage_data import StageId
from ehubx.data.hub_data import HubId
from ehubx.data.tech_data import TechId
from ehubx.data.conv_tech_data import ConversionTechs
from ehubx.data.ec_data import Ecs, EcId, ImpExpType
from ehubx.data.import_data import Imports
from ehubx.data.autarky_data import Autarky, AutarkyCalculationMethod
from ehubx.data.time_data import Times, TimeId
from ehubx.model.import_model import SET_IMPTUPLE, VAR_IMP
from ehubx.model.conv_tech_model import SET_CONVTECHTUPLE, VAR_CONVTECHOUT
from ehubx.model.times_model import SET_TIME
from ehubx.model import exceptions

# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/autarky"
"""String identifying the autarky model for logging purposes"""

VAR_AUTARKYIMPINTERNAL: str = "V_AutarkyImpInternal"
"""Name of variable for internal imports"""

VAR_AUTARKYIMPCROSS: str = "V_AutarkyImpCross"
"""Name of variable for cross-border imports"""

VAR_AUTARKY: str = "V_Autarky"
"""Name of variable for overall autarky value"""

PAR_AUTARKYIMPINTERNALZERO: str = "P_AutarkyImpInternalZero"
"""Name of parameter marking whether no internal import possibilities exist"""

PAR_AUTARKYIMPCROSSZERO: str = "P_AutarkyImpCrossZero"
"""Name of parameter marking whether no cross-import possibilities exist"""

CON_AUTARKYIMPINTERNAL: str = "C_AutarkyImpInternal"
"""Name of constraint fixing internal imports"""

CON_AUTARKYIMPCROSS: str = "C_AutarkyImpCross"
"""Name of constraint fixing cross-imports"""

CON_AUTARKYAUTARKYLINEARIZED: str = "C_AutarkyAutarkyLinearized"
"""Name of constraint for autarky value (linearized version)"""

CON_AUTARKYAUTARKYQUADRATIC: str = "C_AutarkyAutarkyQuadratic"
"""Name of constraint for autarky value (quadratic version)"""

CON_AUTARKYMIN: str = "C_AutarkyMin"
"""Name of constraint respecting the parameter autarky_min"""

CON_AUTARKYMAX: str = "C_AutarkyMax"
"""Name of constraint respecting the parameter autarky_max"""


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the autarky model module
    """
    CROSSIMPUNBOUNDED = "calculating upper bound for V_AutarkyImpCross"
    INTERNALIMPUNBOUNDED = "calculating upper bound for V_AutarkyImpInternal"


def build(model: Model, conv_techs: ConversionTechs, ecs: Ecs,
          imports: Imports, autarky: Autarky, times: Times) -> None:
    """
    Builds the autarky submodel. For a mathematical description in thorough
    detail, please refer to the section 'Autarky model' in the documentation.

    :param model: Pyomo model
    :type model: Model
    :param conv_techs: Conversion technology data object
    :type conv_techs: ConversionTechs
    :param ecs: Energy carrier data object
    :type ecs: Ecs
    :param imports: Imports data object
    :type imports: Imports
    :param autarky: Autarky data object
    :type autarky: Autarky
    :param times: Time data object
    :type times: Times
    """
    # Skip autarky module if it is not set to be included
    if autarky.calculation_method == AutarkyCalculationMethod.NONE:
        logging.log_file("Skipped building autarky model as instructed",
                         module=LOG_MODULE_STR)
        return
    # Start measuring build time
    start = datetime.now()
    # Build
    _build_base(model, conv_techs, ecs, imports, autarky, times)
    # Logging
    elapsed = datetime.now() - start
    logging.log_file(
        "Built autarky module. Elapsed time: "
        f"{int(elapsed.total_seconds())}s", module=LOG_MODULE_STR)


def _build_base(model: Model, conv_techs: ConversionTechs, ecs: Ecs,
                imports: Imports, autarky: Autarky, times: Times) -> None:
    # [VAR] Internal imports. These include a) imports of ecs with
    #       is_energy=True and imp_exp_type=internal, and b) outputs of
    #       conversion techs where the output ec satisfies the properties from
    #       a) and the conversion tech has a single input ec with
    #       imp_exp_type=internal and is_energy=False.
    setattr(model, VAR_AUTARKYIMPINTERNAL,
            Var(domain=NonNegativeReals))
    # [CON] Internal imports
    _con_autarky_imp_internal(model, conv_techs, ecs, times)
    # [VAR] Cross-border imports. These are all imports of ecs with
    #       is_energy=True and imp_exp_type=cross.
    setattr(model, VAR_AUTARKYIMPCROSS,
            Var(domain=NonNegativeReals))
    # [CON] Cross-imports
    _con_autarky_imp_cross(model, ecs, times)
    # [VAR] Autarky value
    setattr(model, VAR_AUTARKY,
            Var(domain=NonNegativeReals))
    # [CON] Autarky definition. Nonlinear version is V_Autarky =
    #       V_AutarkyImpInternal / (V_AutarkyImpInternal + V_AutarkyImpCross)
    #       Linearized version uses a simple triangulation of a rectangle that
    #       values of (V_AutarkyImpInternal, V_AutarkyImpCross) are expected in
    _con_autarky_autarky(model, conv_techs, ecs, imports, autarky, times)
    # [CON] Autarky min/max limits
    _con_autarky_minmax(model, autarky)


def _con_autarky_imp_internal(model: Model, conv_techs: ConversionTechs,
                              ecs: Ecs, times: Times) -> None:

    def __rule_autarky_imp_internal(model):
        imp_internal = 0
        # a) Imports of ecs with is_energy=True and imp_exp_type=internal:
        imp_internal += sum(
            times.get_weight(StageId(s), TimeId(t))
            * getattr(model, VAR_IMP)[s, h, e, t]
            for (s, h, e) in getattr(model, SET_IMPTUPLE)
            if ecs.is_energy(EcId(e))
            if ecs.get_imp_exp_type(EcId(e)) == ImpExpType.INTERNAL
            for t in getattr(model, SET_TIME))
        # b) Outputs of conversion techs for those output ecs satisfying the
        #    properties from a) and the conversion tech has a single input ec
        #    with imp_exp_type=internal and is_energy=False.
        for (s, h, x) in getattr(model, SET_CONVTECHTUPLE):
            # Only consider conv_tech if there is a single input&output ec
            if (len(conv_techs.get_in_ecs(TechId(x))) > 1
                    or len(conv_techs.get_out_ecs(TechId(x))) > 1):
                continue
            # Only consider conv_tech if input ec is internal and not is_energy
            # and if output ec is is_energy
            e_in = conv_techs.get_in_ec_main(TechId(x))
            e_out = conv_techs.get_out_ec_main(TechId(x))
            if not (ecs.get_imp_exp_type(e_in) == ImpExpType.INTERNAL
                    and not ecs.is_energy(e_in)
                    and ecs.is_energy(e_out)):
                continue
            # Add output of conv_tech to internal imports
            imp_internal += sum(
                times.get_weight(s, TimeId(t))
                * getattr(model, VAR_CONVTECHOUT)[s, h, x, e_out.key, t]
                for t in getattr(model, SET_TIME))
        # Mark trivial constraint
        setattr(model, PAR_AUTARKYIMPINTERNALZERO,
                Param(initialize=(isinstance(imp_internal, int)
                                  and imp_internal == 0)))
        # Set constraint
        return getattr(model, VAR_AUTARKYIMPINTERNAL) == imp_internal

    setattr(model, CON_AUTARKYIMPINTERNAL,
            Constraint(rule=__rule_autarky_imp_internal))


def _con_autarky_imp_cross(model: Model, ecs: Ecs, times: Times) -> None:

    def __rule_autarky_imp_cross(model):
        # Imports of ecs with is_energy=True and imp_exp_type=cross:
        imp_cross = sum(
            times.get_weight(StageId(s), TimeId(t))
            * getattr(model, VAR_IMP)[s, h, e, t]
            for (s, h, e) in getattr(model, SET_IMPTUPLE)
            if ecs.is_energy(EcId(e))
            if ecs.get_imp_exp_type(EcId(e)) == ImpExpType.CROSS
            for t in getattr(model, SET_TIME))
        # Mark trivial constraint
        setattr(model, PAR_AUTARKYIMPCROSSZERO,
                Param(initialize=(isinstance(imp_cross, int)
                                  and imp_cross == 0)))
        # Set constraint
        return getattr(model, VAR_AUTARKYIMPCROSS) == imp_cross

    setattr(model, CON_AUTARKYIMPCROSS,
            Constraint(rule=__rule_autarky_imp_cross))


def _con_autarky_autarky(model: Model, conv_techs: ConversionTechs, ecs: Ecs,
                         imports: Imports, autarky: Autarky, times: Times
                         ) -> None:
    if (autarky.calculation_method
            == AutarkyCalculationMethod.LINEARIZED):
        _con_autarky_autarky_linearized(model, conv_techs, ecs, imports, times)
    if (autarky.calculation_method
            == AutarkyCalculationMethod.QUADRATIC):
        _con_autarky_autarky_quadratic(model)


def _con_autarky_autarky_linearized(model: Model, conv_techs: ConversionTechs,
                                    ecs: Ecs, imports: Imports, times: Times
                                    ) -> None:

    # Obtain maximal upper boundaries for V_AutarkyImpCross and
    # V_AutarkyImpInternal
    max_imp_cross: float = 0
    max_imp_internal: float = 0
    for (s, h, e) in getattr(model, SET_IMPTUPLE):
        # Contribution to max_imp_cross from imports
        if (ecs.is_energy(EcId(e))
                and ecs.get_imp_exp_type(EcId(e)) == ImpExpType.CROSS):
            max_imp_tuple = _calc_imp_sum_max(StageId(s), HubId(h), EcId(e),
                                              imports, times)
            if max_imp_tuple == float("inf"):
                msg = ("Error in building linearization of autarky variable: "
                       f"Sum over maximal imports for stage {s}, hub {h}, and "
                       f"ec {e} is unbounded for the cross-import ec {e}. "
                       "Please specify 'sum_max' or 'max' of imports")
                raise exceptions.ModelException(
                    ExceptionKey.CROSSIMPUNBOUNDED.value,
                    [StageId(s), HubId(h), EcId(e)], msg,
                    module=LOG_MODULE_STR)
            max_imp_cross += max_imp_tuple
        # Contribution to max_imp_internal from imports
        if (ecs.is_energy(EcId(e))
                and ecs.get_imp_exp_type(EcId(e)) == ImpExpType.INTERNAL):
            max_imp_tuple = _calc_imp_sum_max(StageId(s), HubId(h), EcId(e),
                                              imports, times)
            if max_imp_tuple == float("inf"):
                msg = ("Error in building linearization of autarky variable: "
                       f"Sum over imports for stage {s}, hub {h}, and ec {e} "
                       f"is unbounded for the internal import ec {e}. "
                       "Please specify 'sum_max' or 'max' of imports")
                raise exceptions.ModelException(
                    ExceptionKey.INTERNALIMPUNBOUNDED.value,
                    [StageId(s), HubId(h), EcId(e)], msg,
                    module=LOG_MODULE_STR)
            max_imp_internal += max_imp_tuple
    # Contribution to max_imp_internal from conversion technologies
    for (s, h, x) in getattr(model, SET_CONVTECHTUPLE):
        # Only consider conv_tech if there is a single input&output ec
        if (len(conv_techs.get_in_ecs(TechId(x))) > 1
                or len(conv_techs.get_out_ecs(TechId(x))) > 1):
            continue
        # Only consider conv_tech if input ec is internal and not is_energy
        # and if output ec is is_energy
        e_in = conv_techs.get_in_ec_main(TechId(x))
        e_out = conv_techs.get_out_ec_main(TechId(x))
        if not (ecs.get_imp_exp_type(e_in) == ImpExpType.INTERNAL
                and not ecs.is_energy(e_in)
                and ecs.is_energy(e_out)):
            continue
        # Obtain upper boundary for summed-up output
        out_sum_max = conv_techs.get_out_sum_max(StageId(s), HubId(h),
                                                 TechId(x))
        if out_sum_max == float("inf"):
            msg = ("Error in building linearization of autarky variable: The "
                   f"conversion tech {x} transforms ec {e_in} (internal, "
                   f"non-energy) to ec {e_out} (energy), contributing to "
                   "V_AutarkyInternalImp. However, the sum over its outputs "
                   f"in stage {s} and hub {h} is unbounded. Please specify "
                   "'out_sum_max' of ConversionTechs")
            raise exceptions.ModelException(
                ExceptionKey.INTERNALIMPUNBOUNDED.value,
                [StageId(s), HubId(h), TechId(x)], msg, module=LOG_MODULE_STR)
        max_imp_internal += out_sum_max

    # TODO: Continue implementation with max_imp_cross and max_imp_internal
    msg = "Linearization of autarky constraint not implemented yet"
    raise exceptions.ModelException("", [],
        "Autarky linearization not implemented yet", module=LOG_MODULE_STR)


def _con_autarky_autarky_quadratic(model: Model) -> None:

    def __rule_autarky_autarky_quadratic(model):
        # In case there are neither internal imports nor cross-imports, the
        # autarky value is defined as 1.
        if (getattr(model, PAR_AUTARKYIMPINTERNALZERO)
                and getattr(model, PAR_AUTARKYIMPCROSSZERO)):
            return getattr(model, VAR_AUTARKY) == 1

        # Otherwise, autarky is defined as
        #   V_AutarkyImpInternal / (V_AutarkyImpInternal + V_AutarkyImpCross)
        return (getattr(model, VAR_AUTARKY)
                * (getattr(model, VAR_AUTARKYIMPINTERNAL)
                   + getattr(model, VAR_AUTARKYIMPCROSS))
                == getattr(model, VAR_AUTARKYIMPINTERNAL))

    setattr(model, CON_AUTARKYAUTARKYQUADRATIC,
            Constraint(rule=__rule_autarky_autarky_quadratic))


def _calc_imp_sum_max(s: StageId, h: HubId, e: EcId, imports: Imports,
                      times: Times) -> float:
    # First boundary from sum_max
    sum_max_1 = imports.get_sum_max(s, h, e)
    # Second boundary from max
    sum_max_2: float = 0
    imp_max = imports.get_max(s, h, e)
    if imp_max.has_values:
        sum_max_2 = sum(times.get_weight(s, t) * imp_max.get_value(t)
                        for t in times.ids)
    if not imp_max.has_values:
        sum_max_2 = float("inf")
        imp_max_def = imp_max.def_value
        if imp_max_def is not None:
            sum_max_2 = imp_max_def * times.num_horizon_ts
    # Return the tighter of the two thresholds
    sum_max = min(sum_max_1, sum_max_2)
    return sum_max


def _con_autarky_minmax(model: Model, autarky: Autarky) -> None:

    def __rule_autarky_min(model):
        # Get minimal autarky value
        autarky_min = autarky.autarky_min
        # Set the constraint
        return getattr(model, VAR_AUTARKY) >= autarky_min

    def __rule_autarky_max(model):
        # Get minimal autarky value
        autarky_max = autarky.autarky_max
        # Set the constraint
        return getattr(model, VAR_AUTARKY) <= autarky_max

    setattr(model, CON_AUTARKYMIN, Constraint(rule=__rule_autarky_min))
    setattr(model, CON_AUTARKYMAX, Constraint(rule=__rule_autarky_max))
