"""Autarky submodel"""

from datetime import datetime
from enum import Enum
from typing import List, Tuple

import numpy as np
from pyomo.core import Binary, Constraint, Model, NonNegativeReals, Param, Set, Var

from ehubx.core import logging
from ehubx.data.autarky_data import Autarky, AutarkyCalculationMethod
from ehubx.data.conv_tech_data import ConversionTechs
from ehubx.data.demand_data import Demands
from ehubx.data.ec_data import EcId, Ecs, ImpExpType
from ehubx.data.hub_data import HubId
from ehubx.data.import_data import Imports
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.tech_data import TechId
from ehubx.data.time_data import TimeId, Times
from ehubx.model.conv_tech_model import SET_CONVTECHTUPLE, VAR_CONVTECHOUT
from ehubx.model.import_model import SET_IMPTUPLE, VAR_IMP
from ehubx.model.times_model import SET_TIME


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


def build(
    model: Model,
    stages: Stages,
    ecs: Ecs,
    imports: Imports,
    demands: Demands,
    conv_techs: ConversionTechs,
    autarky: Autarky,
    times: Times,
) -> None:
    """
    Builds the autarky submodel. For a mathematical description in thorough
    detail, please refer to the section 'Autarky model' in the documentation.

    :param model: Pyomo model
    :type model: Model
    :param stages: Stages data object
    :type stages: Stages
    :param ecs: Energy carrier data object
    :type ecs: Ecs
    :param imports: Imports data object
    :type imports: Imports
    :param demands: Demands data object
    :type demands: Demands
    :param conv_techs: Conversion technology data object
    :type conv_techs: ConversionTechs
    :param autarky: Autarky data object
    :type autarky: Autarky
    :param times: Time data object
    :type times: Times
    """
    # Skip autarky module if it is not set to be included
    if autarky.calculation_method == AutarkyCalculationMethod.NONE:
        logging.log_file(
            "Skipped building autarky model as instructed", module=LOG_MODULE_STR
        )
        return
    # Start measuring build time
    start = datetime.now()

    # Build
    _build_base(model, conv_techs, ecs, imports, demands, autarky, stages, times)
    # Logging
    elapsed = datetime.now() - start
    logging.log_file(
        f"Built autarky module. Elapsed time: {int(elapsed.total_seconds())}s",
        module=LOG_MODULE_STR,
    )


def _build_base(
    model: Model,
    conv_techs: ConversionTechs,
    ecs: Ecs,
    imports: Imports,
    demands: Demands,
    autarky: Autarky,
    stages: Stages,
    times: Times,
) -> None:
    # [VAR] Internal imports. These include a) imports of ecs with
    #       is_energy=True and imp_exp_type=internal, and b) outputs of
    #       conversion techs where the output ec satisfies the properties from
    #       a) and the conversion tech has a single input ec with
    #       imp_exp_type=internal and is_energy=False.
    setattr(model, VAR_AUTARKYIMPINTERNAL, Var(domain=NonNegativeReals))
    # [CON] Internal imports
    _con_autarky_imp_internal(model, conv_techs, ecs, times)
    # [VAR] Cross-border imports. These are all imports of ecs with
    #       is_energy=True and imp_exp_type=cross.
    setattr(model, VAR_AUTARKYIMPCROSS, Var(domain=NonNegativeReals))
    # [CON] Cross-imports
    _con_autarky_imp_cross(model, ecs, times)
    # [VAR] Autarky value
    setattr(model, VAR_AUTARKY, Var(domain=NonNegativeReals))
    # [CON] Autarky definition. Nonlinear version is V_Autarky =
    #       V_AutarkyImpInternal / (V_AutarkyImpInternal + V_AutarkyImpCross)
    #       Linearized version uses a simple triangulation
    #       of a rectangle that values of
    #       (V_AutarkyImpInternal, V_AutarkyImpCross)
    #       are expected in
    _con_autarky_autarky(
        model, conv_techs, ecs, imports, demands, autarky, stages, times
    )
    # [CON] Autarky min/max limits
    _con_autarky_minmax(model, autarky)


def _con_autarky_imp_internal(
    model: Model, conv_techs: ConversionTechs, ecs: Ecs, times: Times
) -> None:
    def __rule_autarky_imp_internal(model):
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
            PAR_AUTARKYIMPINTERNALZERO,
            Param(initialize=(isinstance(imp_internal, int) and imp_internal == 0)),
        )
        # Set constraint
        return getattr(model, VAR_AUTARKYIMPINTERNAL) == imp_internal

    setattr(model, CON_AUTARKYIMPINTERNAL, Constraint(rule=__rule_autarky_imp_internal))


def _con_autarky_imp_cross(model: Model, ecs: Ecs, times: Times) -> None:
    def __rule_autarky_imp_cross(model):
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
            PAR_AUTARKYIMPCROSSZERO,
            Param(initialize=(isinstance(imp_cross, int) and imp_cross == 0)),
        )
        # Set constraint
        return getattr(model, VAR_AUTARKYIMPCROSS) == imp_cross

    setattr(model, CON_AUTARKYIMPCROSS, Constraint(rule=__rule_autarky_imp_cross))


def _con_autarky_autarky(
    model: Model,
    conv_techs: ConversionTechs,
    ecs: Ecs,
    imports: Imports,
    demands: Demands,
    autarky: Autarky,
    stages: Stages,
    times: Times,
) -> None:
    """
    Constructs autarky constraints based on the selected calculation method.
    Supports both Linearized and Quadratic formulations.
    """

    if autarky.calculation_method == AutarkyCalculationMethod.LINEARIZED:
        _con_autarky_autarky_linearized(
            model, conv_techs, ecs, imports, demands, stages, times, total_nodes=900
        )
    if autarky.calculation_method == AutarkyCalculationMethod.QUADRATIC:
        _con_autarky_autarky_quadratic(model)


def _con_autarky_autarky_linearized(
    model: Model,
    conv_techs: ConversionTechs,
    ecs: Ecs,
    imports: Imports,
    demands: Demands,
    stages: Stages,
    times: Times,
    total_nodes: int,
) -> None:
    # Obtain maximal upper boundaries for V_AutarkyImpCross and
    # V_AutarkyImpInternal
    max_imp_cross: float = 0
    max_imp_internal: float = 0
    infinite_imp_cross: Binary = False
    infinite_imp_internal: Binary = False

    demand_sum_per_ts = {
        (s, t): sum(
            [
                demands.get_demand(s2, h, e).get_value(t)
                for (s2, h, e) in demands.tuples
                if s == s2
            ]
        )
        for s in stages.ids
        for t in times.ids
    }

    for s, h, e in model.S_ImpTuple:
        # Contribution to max_imp_cross from imports
        if infinite_imp_cross and infinite_imp_internal:
            break
        if ecs.is_energy(EcId(e)) and ecs.get_imp_exp_type(EcId(e)) == ImpExpType.CROSS:
            max_imp_tuple = _calc_imp_sum_max(
                StageId(s), HubId(h), EcId(e), imports, times
            )
            if max_imp_tuple == float("inf"):
                logging.log_warning(
                    "Warning in building linearization of autarky variable: "
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
                StageId(s), HubId(h), EcId(e), imports, times
            )
            if max_imp_tuple == float("inf"):
                logging.log_warning(
                    "Warning in building linearization of autarky variable: "
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
        for s, h, x in model.S_ConvTechTuple:
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
            if not (
                ecs.get_imp_exp_type(e_in) == ImpExpType.INTERNAL
                and not ecs.is_energy(e_in)
                and ecs.is_energy(e_out)
            ):
                continue
            # Obtain upper boundary for summed-up output
            out_sum_max = conv_techs.get_out_sum_max(StageId(s), HubId(h), TechId(x))
            if out_sum_max == float("inf"):
                logging.log_warning(
                    "Warning in building linearization of autarky variable: "
                    f"The conversion tech {x} transforms ec {e_in} (internal, "
                    f"non-energy) to ec {e_out} (energy), contributing to "
                    "V_AutarkyInternalImp. However, the sum over its outputs "
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
    (imp_internal_nodes, imp_cross_nodes, internal_node_array, cross_node_array) = (
        distribute_nodes_uniformly(max_imp_internal, max_imp_cross, total_nodes)
    )

    # Number of simplexes (triangles)
    number_simplexes = 2 * (imp_internal_nodes - 1) * (imp_cross_nodes - 1)

    # Define sets
    model.i = Set(initialize=range(1, imp_internal_nodes + 1))
    model.j = Set(initialize=range(1, imp_cross_nodes + 1))
    model.simplex_index = Set(initialize=range(1, number_simplexes + 1))

    # Compute the autarky matrix
    autarky_approx = precompute_autarky(internal_node_array, cross_node_array)

    # Variables
    model.V_ConvexMultipliers = Var(model.i, model.j, domain=NonNegativeReals)
    model.V_ActiveSimplex = Var(model.simplex_index, domain=Binary)

    # Precompute triangle corners
    triangle_corners = {
        simplex_index: get_triangle_corners(simplex_index, imp_cross_nodes)
        for simplex_index in model.simplex_index
    }

    # Link V_ConvexMultipliers with V_ActiveSimplex
    def lambda_z_rule(model, i, j):
        relevant_triangles = [
            simplex
            for simplex in model.simplex_index
            if (i, j) in triangle_corners[simplex]
        ]
        return model.V_ConvexMultipliers[i, j] <= sum(
            model.V_ActiveSimplex[simplex] for simplex in relevant_triangles
        )

    model.C_ConvexMultActiveSimplex = Constraint(model.i, model.j, rule=lambda_z_rule)

    # R and I constraints
    model.C_InternalImpLin = Constraint(
        expr=(
            sum(
                model.V_ConvexMultipliers[i, j] * internal_node_array[i - 1]
                for i in model.i
                for j in model.j
            )
            == model.V_AutarkyImpInternal
        )
    )

    model.C_CrossImpLin = Constraint(
        expr=(
            sum(
                model.V_ConvexMultipliers[i, j] * cross_node_array[j - 1]
                for i in model.i
                for j in model.j
            )
            == model.V_AutarkyImpCross
        )
    )

    model.C_ConvexMultipliers = Constraint(
        expr=sum(model.V_ConvexMultipliers[i, j] for i in model.i for j in model.j) == 1
    )

    # Exactly one active triangle
    model.C_ActiveSimplex = Constraint(
        expr=(
            sum(
                model.V_ActiveSimplex[simplex_index]
                for simplex_index in model.simplex_index
            )
            == 1
        )
    )

    # Linearized autarky function
    def autarky_rule(model):
        return model.V_Autarky == sum(
            model.V_ConvexMultipliers[i, j] * autarky_approx[i - 1, j - 1]
            for i in model.i
            for j in model.j
        )

    model.C_AutarkyStage = Constraint(rule=autarky_rule)


def precompute_autarky(
    internal_imp_value: np.ndarray, cross_imp_value: np.ndarray
) -> np.ndarray:
    """
    Precompute the autarky function A(R, I) over a mesh grid of R and I values.
    The function constructs a 2D grid using the provided R and I values, then
    computes the autarky function A(R, I) = R / (R + I) safely by avoiding
    division by zero.

    :param internal_imp_value: The set of discrete values representing
        internal imports (R)
    :type internal_imp_value: np.ndarray
    :param cross_imp_value: The set of discrete values representing cross
        imports (I)
    :type cross_imp_value: np.ndarray
    :return: A 2D numpy array containing the computed autarky values A(R, I)
        over the mesh grid. The values are computed as R / (R + I), avoiding
        division by zero.
    :rtype: np.ndarray
    """
    # Create mesh grids for R and I
    r_grid, i_grid = np.meshgrid(internal_imp_value, cross_imp_value, indexing="ij")

    # Initialize the result array with zeros
    autarky_values = np.zeros_like(r_grid)

    # Calculate R / (R + I) safely
    np.divide(r_grid, r_grid + i_grid, out=autarky_values, where=(r_grid + i_grid) != 0)

    # Return
    return autarky_values


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


def _con_autarky_autarky_quadratic(model: Model) -> None:
    def __rule_autarky_autarky_quadratic(model):
        # In case there are neither internal imports
        # nor cross-imports, the autarky value is defined as 1.
        if model.P_AutarkyImpInternalZero and model.P_AutarkyImpCrossZero:
            return model.V_Autarky == 1

        # Otherwise, autarky is defined as
        # V_AutarkyImpInternal /
        # (V_AutarkyImpInternal + V_AutarkyImpCross)
        return (
            model.V_Autarky * (model.V_AutarkyImpInternal + model.V_AutarkyImpCross)
            == model.V_AutarkyImpInternal
        )

    setattr(
        model,
        CON_AUTARKYAUTARKYQUADRATIC,
        Constraint(rule=__rule_autarky_autarky_quadratic),
    )


def _calc_imp_sum_max(
    s: StageId, h: HubId, e: EcId, imports: Imports, times: Times
) -> float:
    # First boundary from sum_max
    sum_max_1 = imports.get_sum_max(s, h, e)
    # Second boundary from max
    sum_max_2: float = 0
    imp_max = imports.get_max(s, h, e)
    if imp_max.has_values:
        sum_max_2 = sum(
            times.get_weight(s, t) * imp_max.get_value(t) for t in times.ids
        )
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
