"""Self-sufficiency submodel"""

from datetime import datetime
from enum import Enum
from typing import List, Tuple

import numpy as np
from pyomo.core import Binary, Constraint, Model, NonNegativeReals, Param, Set, Var

from ehubx.core import logging
from ehubx.data.conv_tech_data import ConversionTechs
from ehubx.data.demand_data import Demands
from ehubx.data.ec_data import EcId, Ecs, ImpExpType
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.hub_data import HubId
from ehubx.data.import_data import Imports
from ehubx.data.self_sufficiency_data import (
    SelfSufficiency,
    SelfSufficiencyCalculationMethod,
)
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.tech_data import TechId
from ehubx.data.time_data import TimeId, Times
from ehubx.data.unit import MassUnit, PowerUnit, TimeUnit
from ehubx.model.conv_tech_model import SET_CONVTECHTUPLE, VAR_CONVTECHOUT
from ehubx.model.ec_model import get_ec_model_unit
from ehubx.model.import_model import SET_IMPTUPLE, VAR_IMP
from ehubx.model.times_model import SET_TIME


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/self_suff"
"""String identifying the self-sufficiency model for logging purposes"""

SET_SELFSUFFICIENCYLINDIMINT = "S_SelfSufficiencyLinDimImp"
"""Name of set for self-sufficiency linearization in the internal-import
dimension"""

SET_SELFSUFFICIENCYLINDIMCROSS = "S_SelfSufficiencyLinDimCross"
"""Name of set for self-sufficiency linearization in the cross-import
dimension"""

SET_SELFSUFFICIENCYLINSIMPLEX = "S_SelfSuffiencyLinSimplex"
"""Name of simplex set for self-sufficiency linearization"""

VAR_SELFSUFFIMPINTERNAL: str = "V_SelfSufficiencyImpInternal"
"""Name of variable for internal imports"""

VAR_SELFSUFFIMPCROSS: str = "V_SelfSufficiencyImpCross"
"""Name of variable for cross-border imports"""

VAR_SELFSUFFICIENCY: str = "V_SelfSufficiency"
"""Name of variable for overall self-sufficiency value"""

VAR_SELFSUFFCONVEXMULTIPLIERS: str = "V_SelfSufficiencyConvexMultipliers"
"""Name of variable for convex multipliers in linearization"""

VAR_SELFSUFFACTIVESIMPLEX: str = "V_SelfSufficiencyActiveSimplex"
"""Name of variable for active simplex in the grid"""

PAR_SELFSUFFIMPINTERNALZERO: str = "P_SelfSufficiencyImpInternalZero"
"""Name of parameter marking whether no internal import possibilities exist"""

PAR_SELFSUFFIMPCROSSZERO: str = "P_SelfSufficiencyImpCrossZero"
"""Name of parameter marking whether no cross-import possibilities exist"""

CON_SELFSUFFIMPINTERNAL: str = "C_SelfSufficiencyImpInternal"
"""Name of constraint fixing internal imports"""

CON_SELFSUFFICIENCYIMPCROSS: str = "C_SelfSufficiencyImpCross"
"""Name of constraint fixing cross-imports"""

CON_SELFSUFFICIENCYSELFSUFFICIENCYLINEARIZED: str = (
    "C_SelfSufficiencySelfSufficiencyLinearized"
)
"""Name of constraint for self-sufficiency value (linearized version)"""

CON_SELFSUFFICIENCYSELFSUFFICIENCYQUADRATIC: str = (
    "C_SelfSufficiencySelfSufficiencyQuadratic"
)
"""Name of constraint for self-sufficiency value (quadratic version)"""

CON_SELFSUFFICIENCYMIN: str = "C_SelfSufficiencyMin"
"""Name of constraint respecting the parameter self_sufficiency_min"""

CON_SELFSUFFICIENCYMAX: str = "C_SelfSufficiencyMax"
"""Name of constraint respecting the parameter self_sufficiency_max"""

CON_SELFSUFFCONVMULTACTIVESIMPLEX: str = "C_SelfSufficiencyConvexMultActiveSimplex"
"""Name of constraint connecting convex self-sufficiency multipliers to active
simplex"""

CON_SELFSUFFINTIMPLIN: str = "C_SelfSufficiencyInternalImpLin"
"""Name of constraint linearizing the internal-import variable in
self-sufficiency model"""

CON_SELFSUFFCROSSIMPLIN: str = "C_SelfSufficiencyCrossImpLin"
"""Name of constraint linearizing the cross-import variable in
self-sufficiency model"""

CON_SELFSUFFCONVMULT: str = "C_SelfSufficiencyConvexMult"
"""Name of constraint for convex multipliers in self-sufficiency
linearization"""

CON_SELFSUFFACTIVESIMPLEX: str = "C_SelfSufficiencyActiveSimplex"
"""Name of constraint handling the active simplex in self-sufficiency
linearization"""

CON_SELFSUFFSELFSUFFSTAGE: str = "C_SelfSufficiencySelfSufficiencyStage"
"""Name of """


class ExceptionKey(Enum):
    """
    Key strings for exception messages occuring in the self-sufficiency model module
    """

    CROSSIMPUNBOUNDED = "calculating upper bound for V_SelfSufficiencyImpCross"
    INTERNALIMPUNBOUNDED = "calculating upper bound for V_SelfSufficiencyImpInternal"


def build(model: Model, system: EnergySystem) -> None:
    """
    Builds the self-sufficiency submodel. For a mathematical description in thorough
    detail, please refer to the section 'Self-sufficiency model' in the documentation.

    :param model: Pyomo model
    :type model: Model
    :param system: Energy system data
    :type system: EnergySystem
    """
    # Extract data from modules
    conv_techs: ConversionTechs = system.conv_techs
    ecs: Ecs = system.ecs
    imports: Imports = system.imports
    demands: Demands = system.demands
    self_sufficiency: SelfSufficiency = system.self_sufficiency
    stages: Stages = system.stages
    times: Times = system.times
    mass_unit: MassUnit = system.mass_unit
    power_unit: PowerUnit = system.power_unit
    # Skip self-sufficiency module if it is not set to be included
    if self_sufficiency.calculation_method == SelfSufficiencyCalculationMethod.NONE:
        logging.log_file(
            "Skipped building self-sufficiency model as instructed",
            module=LOG_MODULE_STR,
        )
        return
    # Start measuring build time
    start = datetime.now()

    # Build
    _build_base(
        model,
        conv_techs,
        ecs,
        imports,
        demands,
        self_sufficiency,
        stages,
        times,
        mass_unit,
        power_unit,
    )
    # Logging
    elapsed = datetime.now() - start
    logging.log_file(
        f"Built self-sufficiency module. Elapsed time: {int(elapsed.total_seconds())}s",
        module=LOG_MODULE_STR,
    )


def _build_base(
    model: Model,
    conv_techs: ConversionTechs,
    ecs: Ecs,
    imports: Imports,
    demands: Demands,
    self_sufficiency: SelfSufficiency,
    stages: Stages,
    times: Times,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
) -> None:
    # [VAR] Internal imports. These include a) imports of ecs with
    #       is_energy=True and imp_exp_type=internal, and b) outputs of
    #       conversion techs where the output ec satisfies the properties from
    #       a) and the conversion tech has a single input ec with
    #       imp_exp_type=internal and is_energy=False.
    setattr(model, VAR_SELFSUFFIMPINTERNAL, Var(domain=NonNegativeReals))
    # [CON] Internal imports
    _con_self_sufficiency_imp_internal(model, conv_techs, ecs, times)
    # [VAR] Cross-border imports. These are all imports of ecs with
    #       is_energy=True and imp_exp_type=cross.
    setattr(model, VAR_SELFSUFFIMPCROSS, Var(domain=NonNegativeReals))
    # [CON] Cross-imports
    _con_self_sufficiency_imp_cross(model, ecs, times)
    # [VAR] Self-sufficiency value
    setattr(model, VAR_SELFSUFFICIENCY, Var(domain=NonNegativeReals))
    # [CON] Self-sufficiency definition. Nonlinear version is V_SelfSufficiency =
    #       V_SelfSufficiencyImpInternal / (V_SelfSufficiencyImpInternal
    #       + V_SelfSufficiencyImpCross). Linearized version uses a simple
    #       triangulation of a rectangle that values of
    #       (V_SelfSufficiencyImpInternal, V_SelfSufficiencyImpCross) expected
    #       in
    _con_self_sufficiency_self_sufficiency(
        model,
        conv_techs,
        ecs,
        imports,
        demands,
        self_sufficiency,
        stages,
        times,
        mass_unit,
        power_unit,
    )
    # [CON] Self-sufficiency min/max limits
    _con_self_sufficiency_minmax(model, self_sufficiency)


def _con_self_sufficiency_imp_internal(
    model: Model, conv_techs: ConversionTechs, ecs: Ecs, times: Times
) -> None:
    def __rule_self_sufficiency_imp_internal(model):
        imp_internal = 0
        # a) Imports of ecs with is_energy=True and imp_exp_type=internal:
        imp_internal += sum(
            times.get_weight(StageId(s), TimeId(t))
            * getattr(model, VAR_IMP)[s, h, e, t]
            for (s, h, e) in getattr(model, SET_IMPTUPLE)
            if ecs.is_energy(EcId(e))
            if ecs.get_imp_exp_type(EcId(e)) == ImpExpType.INTERNAL
            for t in getattr(model, SET_TIME)
        )
        # b) Outputs of conversion techs for those output ecs satisfying the
        #    properties from a) and the conversion tech has a single input ec
        #    with imp_exp_type=internal and is_energy=False.
        for s, h, x in getattr(model, SET_CONVTECHTUPLE):
            # Only consider conv_tech if there is a single input&output ec
            if (
                len(conv_techs.get_in_ecs(TechId(x))) > 1
                or len(conv_techs.get_out_ecs(TechId(x))) > 1
            ):
                continue
            # Only consider conv_tech if input ec is internal and not is_energy
            # and if output ec is is_energy
            e_in = conv_techs.get_in_ec_main(TechId(x))
            e_out = conv_techs.get_out_ec_main(TechId(x))
            if not (
                ecs.get_imp_exp_type(e_in) == ImpExpType.INTERNAL
                and not ecs.is_energy(e_in)
                and ecs.is_energy(e_out)
            ):
                continue
            # Add output of conv_tech to internal imports
            imp_internal += sum(
                times.get_weight(s, TimeId(t))
                * getattr(model, VAR_CONVTECHOUT)[s, h, x, e_out.key, t]
                for t in getattr(model, SET_TIME)
            )
        # Mark trivial constraint
        setattr(
            model,
            PAR_SELFSUFFIMPINTERNALZERO,
            Param(initialize=(isinstance(imp_internal, int) and imp_internal == 0)),
        )
        # Set constraint
        return getattr(model, VAR_SELFSUFFIMPINTERNAL) == imp_internal

    setattr(
        model,
        CON_SELFSUFFIMPINTERNAL,
        Constraint(rule=__rule_self_sufficiency_imp_internal),
    )


def _con_self_sufficiency_imp_cross(model: Model, ecs: Ecs, times: Times) -> None:
    def __rule_self_sufficiency_imp_cross(model):
        # Imports of ecs with is_energy=True and imp_exp_type=cross:
        imp_cross = sum(
            times.get_weight(StageId(s), TimeId(t))
            * getattr(model, VAR_IMP)[s, h, e, t]
            for (s, h, e) in getattr(model, SET_IMPTUPLE)
            if ecs.is_energy(EcId(e))
            if ecs.get_imp_exp_type(EcId(e)) == ImpExpType.CROSS
            for t in getattr(model, SET_TIME)
        )
        # Mark trivial constraint
        setattr(
            model,
            PAR_SELFSUFFIMPCROSSZERO,
            Param(initialize=(isinstance(imp_cross, int) and imp_cross == 0)),
        )
        # Set constraint
        return getattr(model, VAR_SELFSUFFIMPCROSS) == imp_cross

    setattr(
        model,
        CON_SELFSUFFICIENCYIMPCROSS,
        Constraint(rule=__rule_self_sufficiency_imp_cross),
    )


def _con_self_sufficiency_self_sufficiency(
    model: Model,
    conv_techs: ConversionTechs,
    ecs: Ecs,
    imports: Imports,
    demands: Demands,
    self_sufficiency: SelfSufficiency,
    stages: Stages,
    times: Times,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
) -> None:
    """
    Constructs self-sufficiency constraints based on the selected calculation method.
    Supports both Linearized and Quadratic formulations.
    """

    if (
        self_sufficiency.calculation_method
        == SelfSufficiencyCalculationMethod.LINEARIZED
    ):
        _con_self_sufficiency_self_sufficiency_linearized(
            model,
            conv_techs,
            ecs,
            imports,
            demands,
            stages,
            times,
            mass_unit,
            power_unit,
            total_nodes=900,
        )
    if (
        self_sufficiency.calculation_method
        == SelfSufficiencyCalculationMethod.QUADRATIC
    ):
        _con_self_sufficiency_self_sufficiency_quadratic(model)


def _con_self_sufficiency_self_sufficiency_linearized(
    model: Model,
    conv_techs: ConversionTechs,
    ecs: Ecs,
    imports: Imports,
    demands: Demands,
    stages: Stages,
    times: Times,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
    total_nodes: int,
) -> None:
    # Obtain maximal upper boundaries for V_SelfSufficiencyImpCross and
    # V_SelfSufficiencyImpInternal
    max_imp_cross: float = 0
    max_imp_internal: float = 0
    infinite_imp_cross: Binary = False
    infinite_imp_internal: Binary = False

    demand_sum_per_ts = {
        (s, t): sum(
            [
                demands.get_demand_profile(s2, h, e)
                .get_value(t)
                .to_float(
                    unit=(
                        get_ec_model_unit(ecs.get_unit(e), mass_unit, power_unit)
                        / TimeUnit.H
                    )
                )
                for (s2, h, e) in demands.tuples
                if s == s2
            ]
        )
        for s in stages.ids
        for t in times.ids
    }

    for s, h, e in getattr(model, SET_IMPTUPLE):
        # Contribution to max_imp_cross from imports
        if infinite_imp_cross and infinite_imp_internal:
            break
        if ecs.is_energy(EcId(e)) and ecs.get_imp_exp_type(EcId(e)) == ImpExpType.CROSS:
            max_imp_tuple = _calc_imp_sum_max(
                StageId(s),
                HubId(h),
                EcId(e),
                ecs,
                imports,
                times,
                mass_unit,
                power_unit,
            )
            if max_imp_tuple == float("inf"):
                logging.log_warning(
                    "Warning in building linearization of self-sufficiency variable: "
                    f"Sum over maximal imports for stage {s}, hub {h}, and "
                    f"ec {e} is unbounded for the cross-import ec {e}. "
                    "Please specify 'sum_max' or 'max' of imports",
                    module=LOG_MODULE_STR,
                )
                infinite_imp_cross = True
            max_imp_cross += max_imp_tuple

        # Contribution to max_imp_internal from imports
        if (
            ecs.is_energy(EcId(e))
            and ecs.get_imp_exp_type(EcId(e)) == ImpExpType.INTERNAL
        ):
            max_imp_tuple = _calc_imp_sum_max(
                StageId(s),
                HubId(h),
                EcId(e),
                ecs,
                imports,
                times,
                mass_unit,
                power_unit,
            )
            if max_imp_tuple == float("inf"):
                logging.log_warning(
                    "Warning in building linearization of self-sufficiency variable: "
                    f"Sum over imports for stage {s}, hub {h}, and ec {e} "
                    f"is unbounded for the internal import ec {e}. "
                    "Please specify 'sum_max' or 'max' of imports",
                    module=LOG_MODULE_STR,
                )
                infinite_imp_internal = True

            max_imp_internal += max_imp_tuple

    if infinite_imp_cross:
        # If an infinite output was found, set max_imp_internal to
        # 100 * total sum of demand. Assuming model.V_DemandSupply is a Pyomo
        # variable for demand
        max_imp_cross = 100 * (
            sum(demand_sum_per_ts.values()) if demand_sum_per_ts else 0
        )
        logging.log_warning(
            "Set max_imp_cross to 100 * total demand"
            f" due to infinite output: {max_imp_cross}",
            module=LOG_MODULE_STR,
        )

    if infinite_imp_internal is False:
        # Contribution to max_imp_internal from conversion technologies
        for s, h, x in getattr(model, SET_CONVTECHTUPLE):
            # Only consider conv_tech if there is a single input & output ec
            if (
                len(conv_techs.get_in_ecs(TechId(x))) > 1
                or len(conv_techs.get_out_ecs(TechId(x))) > 1
            ):
                continue
            # Only consider conv_tech if input ec is internal and not is_energy
            # and if output ec is is_energy
            e_in = conv_techs.get_in_ec_main(TechId(x))
            e_out = conv_techs.get_out_ec_main(TechId(x))
            e_out_unit = get_ec_model_unit(ecs.get_unit(e_out), mass_unit, power_unit)
            if not (
                ecs.get_imp_exp_type(e_in) == ImpExpType.INTERNAL
                and not ecs.is_energy(e_in)
                and ecs.is_energy(e_out)
            ):
                continue
            # Obtain upper boundary for summed-up output
            out_sum_max = conv_techs.get_out_sum_max(
                StageId(s), HubId(h), TechId(x)
            ).to_float(unit=e_out_unit)
            if out_sum_max == float("inf"):
                logging.log_warning(
                    "Warning in building linearization of self-sufficiency variable: "
                    f"The conversion tech {x} transforms ec {e_in} (internal, "
                    f"non-energy) to ec {e_out} (energy), contributing to "
                    "V_SelfSufficiencyInternalImp. However, the sum over its outputs "
                    f"in stage {s} and hub {h} is unbounded. Please specify "
                    "'out_sum_max' of ConversionTechs"
                )
                infinite_imp_internal = True
                break
            max_imp_internal += out_sum_max

    if infinite_imp_internal:
        # If an infinite output was found, set max_imp_internal to
        # 100 * total sum of demand. Assuming model.V_DemandSupply is a Pyomo
        # variable for demand
        max_imp_internal = 100 * (
            sum(demand_sum_per_ts.values()) if demand_sum_per_ts else 0
        )
        logging.log_warning(
            "Set max_imp_internal to 100 * total demand "
            f"due to infinite output: {max_imp_internal}",
            module=LOG_MODULE_STR,
        )

    # Adjust the mesh to maintain uniform triangles
    (
        imp_internal_nodes,
        imp_cross_nodes,
        internal_node_array,
        cross_node_array,
    ) = distribute_nodes_uniformly(max_imp_internal, max_imp_cross, total_nodes)

    # Number of simplexes (triangles)
    number_simplexes = 2 * (imp_internal_nodes - 1) * (imp_cross_nodes - 1)

    # Define sets
    setattr(
        model,
        SET_SELFSUFFICIENCYLINDIMINT,
        Set(initialize=range(1, imp_internal_nodes + 1)),
    )
    setattr(
        model,
        SET_SELFSUFFICIENCYLINDIMCROSS,
        Set(initialize=range(1, imp_cross_nodes + 1)),
    )
    setattr(
        model,
        SET_SELFSUFFICIENCYLINSIMPLEX,
        Set(initialize=range(1, number_simplexes + 1)),
    )

    # Compute the self-sufficiency matrix
    self_sufficiency_approx = precompute_self_sufficiency(
        internal_node_array, cross_node_array
    )

    # Variables
    setattr(
        model,
        VAR_SELFSUFFCONVEXMULTIPLIERS,
        Var(
            getattr(model, SET_SELFSUFFICIENCYLINDIMINT),
            getattr(model, SET_SELFSUFFICIENCYLINDIMCROSS),
            domain=NonNegativeReals,
        ),
    )
    setattr(
        model,
        VAR_SELFSUFFACTIVESIMPLEX,
        Var(getattr(model, SET_SELFSUFFICIENCYLINSIMPLEX), domain=Binary),
    )

    # Precompute triangle corners
    triangle_corners = {
        simplex_index: get_triangle_corners(simplex_index, imp_cross_nodes)
        for simplex_index in getattr(model, SET_SELFSUFFICIENCYLINSIMPLEX)
    }

    # Link V_SelfSufficiencyConvexMultipliers with
    # V_SelfSufficiencyActiveSimplex
    def lambda_z_rule(model, i, j):
        relevant_triangles = [
            simplex
            for simplex in getattr(model, SET_SELFSUFFICIENCYLINSIMPLEX)
            if (i, j) in triangle_corners[simplex]
        ]
        return getattr(model, VAR_SELFSUFFCONVEXMULTIPLIERS)[i, j] <= sum(
            getattr(model, VAR_SELFSUFFACTIVESIMPLEX)[simplex]
            for simplex in relevant_triangles
        )

    setattr(
        model,
        CON_SELFSUFFCONVMULTACTIVESIMPLEX,
        Constraint(
            getattr(model, SET_SELFSUFFICIENCYLINDIMINT),
            getattr(model, SET_SELFSUFFICIENCYLINDIMCROSS),
            rule=lambda_z_rule,
        ),
    )

    # R and I constraints
    setattr(
        model,
        CON_SELFSUFFINTIMPLIN,
        Constraint(
            expr=(
                sum(
                    getattr(model, VAR_SELFSUFFCONVEXMULTIPLIERS)[i, j]
                    * internal_node_array[i - 1]
                    for i in getattr(model, SET_SELFSUFFICIENCYLINDIMINT)
                    for j in getattr(model, SET_SELFSUFFICIENCYLINDIMCROSS)
                )
                == getattr(model, VAR_SELFSUFFIMPINTERNAL)
            )
        ),
    )

    setattr(
        model,
        CON_SELFSUFFCROSSIMPLIN,
        Constraint(
            expr=(
                sum(
                    getattr(model, VAR_SELFSUFFCONVEXMULTIPLIERS)[i, j]
                    * cross_node_array[j - 1]
                    for i in getattr(model, SET_SELFSUFFICIENCYLINDIMINT)
                    for j in getattr(model, SET_SELFSUFFICIENCYLINDIMCROSS)
                )
                == getattr(model, VAR_SELFSUFFIMPCROSS)
            )
        ),
    )

    setattr(
        model,
        CON_SELFSUFFCONVMULT,
        Constraint(
            expr=sum(
                getattr(model, VAR_SELFSUFFCONVEXMULTIPLIERS)[i, j]
                for i in getattr(model, SET_SELFSUFFICIENCYLINDIMINT)
                for j in getattr(model, SET_SELFSUFFICIENCYLINDIMCROSS)
            )
            == 1
        ),
    )

    # Exactly one active triangle
    setattr(
        model,
        CON_SELFSUFFACTIVESIMPLEX,
        Constraint(
            expr=(
                sum(
                    getattr(model, VAR_SELFSUFFACTIVESIMPLEX)[simplex_index]
                    for simplex_index in getattr(model, SET_SELFSUFFICIENCYLINSIMPLEX)
                )
                == 1
            )
        ),
    )

    # Linearized self-sufficiency function
    def self_sufficiency_rule(model):
        return getattr(model, VAR_SELFSUFFICIENCY) == sum(
            getattr(model, VAR_SELFSUFFCONVEXMULTIPLIERS)[i, j]
            * self_sufficiency_approx[i - 1, j - 1]
            for i in getattr(model, SET_SELFSUFFICIENCYLINDIMINT)
            for j in getattr(model, SET_SELFSUFFICIENCYLINDIMCROSS)
        )

    setattr(model, CON_SELFSUFFSELFSUFFSTAGE, Constraint(rule=self_sufficiency_rule))


def precompute_self_sufficiency(
    internal_imp_value: np.ndarray, cross_imp_value: np.ndarray
) -> np.ndarray:
    """
    Precompute the self-sufficiency function A(R, I) over a mesh grid of R and
    I values. The function constructs a 2D grid using the provided R and I
    values, then computes the self-sufficiency function A(R, I) = R / (R + I)
    safely by avoiding division by zero.

    :param internal_imp_value: The set of discrete values representing
        internal imports (R)
    :type internal_imp_value: np.ndarray
    :param cross_imp_value: The set of discrete values representing cross
        imports (I)
    :type cross_imp_value: np.ndarray
    :return: A 2D numpy array containing the computed self-sufficiency values A
        (R, I) over the mesh grid. The values are computed as R / (R + I),
        avoiding division by zero.
    :rtype: np.ndarray
    """
    # Create mesh grids for R and I
    r_grid, i_grid = np.meshgrid(internal_imp_value, cross_imp_value, indexing="ij")

    # Initialize the result array with zeros
    self_sufficiency_values = np.zeros_like(r_grid)

    # Calculate R / (R + I) safely
    np.divide(
        r_grid,
        r_grid + i_grid,
        out=self_sufficiency_values,
        where=(r_grid + i_grid) != 0,
    )

    # Return
    return self_sufficiency_values


def get_triangle_corners(simplex_index: int, m: int) -> List[Tuple[int, int]]:
    """
    Determine the corner points of a given triangle in a 2D simplex grid. This
    function calculates the three corner points of a triangle based on its
    index `simplex_index` within a structured grid of size `m`. The grid is
    composed of two triangles per cell. The function ensures that the triangle
    is assigned correctly within the mesh grid.

    :param simplex_index: Index of the triangle within the simplex grid
    :type simplex_index: int
    :param m: Number of grid points along the second dimension (cross imports)
    :type m: int
    :return: A list of three corner points (row, col) representing the
        triangle. The corner `(1,1)` is excluded to avoid numerical issues in
        linearization.
    :rtype: List[Tuple[int, int]]
    """
    cell_index = (simplex_index - 1) // 2
    triangle_within_cell = (simplex_index - 1) % 2
    row = cell_index // (m - 1)
    col = cell_index % (m - 1)

    if triangle_within_cell == 0:
        corners = [(row + 1, col + 1), (row + 2, col + 1), (row + 1, col + 2)]
    else:
        corners = [(row + 2, col + 1), (row + 1, col + 2), (row + 2, col + 2)]

    # Exclude the corner (1, 1) during creation instead of filtering afterwards
    return [(r, c) for (r, c) in corners if not (r == 1 and c == 1)]


def distribute_nodes_uniformly(
    imp_internal_max: float, imp_cross_max: float, total_nodes: int = 900
) -> Tuple[int, int, np.ndarray, np.ndarray]:
    """
    Redistributes the total number of nodes while ensuring uniform simplex
    spacing. Keeps triangle shapes close to equilateral, ensures grid node
    count stays the same, and adapts based on imp_internal_max and
    imp_cross_max without extreme stretching.

    :param imp_internal_max: Maximum range in the R direction (Internal supply)
    :type imp_internal_max: float
    :param imp_cross_max: Maximum range in the I direction (Cross import)
    :type imp_cross_max: float
    :param total_nodes: Fixed total number of nodes in the grid, defaults to
        900
    :type total_nodes: int, optional
    :return: Adjusted number of nodes in R direction, adjusted number of nodes
        in I direction, uniformly spaced grid points for R, and uniformly
        spaced grid points for I
    :rtype: Tuple[int, int, np.ndarray, np.ndarray]
    """
    # Compute target spacing to maintain uniformity
    target_spacing = np.sqrt((imp_internal_max * imp_cross_max) / total_nodes)
    # Compute number of nodes for uniform triangle spacing
    imp_internal_nodes = int(imp_internal_max / target_spacing)
    imp_cross_nodes = int(imp_cross_max / target_spacing)

    # Ensure product is exactly 900 (adjust for rounding)
    while imp_internal_nodes * imp_cross_nodes != total_nodes:
        if imp_internal_nodes * imp_cross_nodes > total_nodes:
            imp_internal_nodes -= 1
        else:
            imp_cross_nodes += 1

    # Generate uniform node distributions
    internal_node_array = np.linspace(0, imp_internal_max, imp_internal_nodes)
    cross_node_array = np.linspace(0, imp_cross_max, imp_cross_nodes)

    # Return
    return (imp_internal_nodes, imp_cross_nodes, internal_node_array, cross_node_array)


def _con_self_sufficiency_self_sufficiency_quadratic(model: Model) -> None:
    def __rule_self_sufficiency_self_sufficiency_quadratic(model):
        # In case there are neither internal imports
        # nor cross-imports, the self-sufficiency value is defined as 1.
        if getattr(model, PAR_SELFSUFFIMPINTERNALZERO) and getattr(
            model, PAR_SELFSUFFIMPCROSSZERO
        ):
            return getattr(model, VAR_SELFSUFFICIENCY) == 1

        # Otherwise, self-sufficiency is defined as
        # V_SelfSufficiencyImpInternal /
        # (V_SelfSufficiencyImpInternal + V_SelfSufficiencyImpCross)
        return getattr(model, VAR_SELFSUFFICIENCY) * (
            getattr(model, VAR_SELFSUFFIMPINTERNAL)
            + getattr(model, VAR_SELFSUFFIMPCROSS)
        ) == getattr(model, VAR_SELFSUFFIMPINTERNAL)

    setattr(
        model,
        CON_SELFSUFFICIENCYSELFSUFFICIENCYQUADRATIC,
        Constraint(rule=__rule_self_sufficiency_self_sufficiency_quadratic),
    )


def _calc_imp_sum_max(
    s: StageId,
    h: HubId,
    e: EcId,
    ecs: Ecs,
    imports: Imports,
    times: Times,
    mass_unit: MassUnit,
    power_unit: PowerUnit,
) -> float:
    # First boundary from sum_max
    ec_unit = get_ec_model_unit(ecs.get_unit(e), mass_unit, power_unit)
    sum_max_1 = imports.get_sum_max(s, h, e, ecs).to_float(unit=ec_unit)
    # Second boundary from max
    sum_max_2: float = 0
    imp_max = imports.get_max(s, h, e)
    if imp_max.has_values:
        sum_max_2 = sum(
            times.get_weight(s, t)
            * imp_max.get_value(t).to_float(unit=(ec_unit / TimeUnit.H))
            for t in times.ids
        )
    if not imp_max.has_values:
        sum_max_2 = float("inf")
        imp_max_def = imp_max.def_value
        if imp_max_def is not None:
            sum_max_2 = (
                imp_max_def.to_float(unit=(ec_unit / TimeUnit.H)) * times.num_horizon_ts
            )
    # Return the tighter of the two thresholds
    sum_max = min(sum_max_1, sum_max_2)
    return sum_max


def _con_self_sufficiency_minmax(
    model: Model, self_sufficiency: SelfSufficiency
) -> None:
    def __rule_self_sufficiency_min(model):
        # Get minimal self-sufficiency value
        self_sufficiency_min = self_sufficiency.self_sufficiency_min.to_float()
        # Set the constraint
        return getattr(model, VAR_SELFSUFFICIENCY) >= self_sufficiency_min

    def __rule_self_sufficiency_max(model):
        # Get minimal self-sufficiency value
        self_sufficiency_max = self_sufficiency.self_sufficiency_max.to_float()
        # Set the constraint
        return getattr(model, VAR_SELFSUFFICIENCY) <= self_sufficiency_max

    setattr(model, CON_SELFSUFFICIENCYMIN, Constraint(rule=__rule_self_sufficiency_min))
    setattr(model, CON_SELFSUFFICIENCYMAX, Constraint(rule=__rule_self_sufficiency_max))
