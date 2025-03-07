"""
Common module. Contains repeating functionality and centralized parameters
"""

import os
from enum import Enum


# ------------ #
# Enumerations #
# ------------ #
class MultiObjMethod(Enum):
    """Algorithms to solve a bicriterial optimization problem"""

    EPSCONSTRAINT = "eps-constraint"
    """epsilon-constraint method"""

    WEIGHTEDSUM = "weighted-sum"
    """Weighted-sum method"""


class ObjectiveType(Enum):
    """Objective types that ehubX can optimize for"""

    COST = "cost"
    """Cost (minimize)"""

    CO2 = "co2"
    """CO2 (minimize)"""

    AUTARKY = "autarky"
    """Autarky (maximize)"""


class TimeSeriesKind(Enum):
    """Kinds of time series profiles"""

    IMPORTPRICE = "import_price"
    """Import price with indices (stage, hub, ec)"""

    IMPORTMIN = "import_min"
    """Minimal import with indices (stage, hub, ec)"""

    IMPORTMAX = "import_max"
    """Import max with indices (stage, hub, ec)"""

    IMPORTCO2 = "import_co2"
    """Import CO2 with indices (stage, hub, ec)"""

    EXPORTPRICE = "export_price"
    """Export price with indices (stage, hub, ec)"""

    EXPORTMIN = "export_min"
    """Minimal export with indices (stage, hub, ec)"""

    EXPORTMAX = "export_max"
    """Export max with indices (stage, hub, ec)"""

    EXPORTCO2 = "export_co2"
    """Export CO2 with indices (stage, hub, ec)"""

    DEMAND = "demand"
    "Demand with indices (stage, hub, ec)"

    LOADSHEDMAXABS = "load_shedding_max_abs"
    """Load shedding max_abs (stage, hub, ec)"""

    LOADSHEDMAXREL = "load_shedding_max_rel"
    """Load shedding max_rel (stage, hub, ec)"""

    LOADSHEDENERGYCOST = "load_shedding_energy_cost"
    """Load shedding energy cost (stage, hub, ec)"""

    LOADSHIFTMAXABOVEABS = "load_shifting_max_above_abs"
    """Load shifting max_above_abs (stage, hub, ec)"""

    LOADSHIFTMAXABOVEREL = "load_shifting_max_above_rel"
    """Load shifting max_above_rel (stage, hub, ec)"""

    LOADSHIFTMAXBELOWABS = "load_shifting_max_below_abs"
    """Load shifting max_below_abs (stage, hub, ec)"""

    LOADSHIFTMAXBELOWREL = "load_shifting_max_below_rel"
    """Load shifting max_below_rel (stage, hub, ec)"""

    LOADSHIFTENERGYCOSTABOVE = "load_shifting_energy_cost_above"
    """Load shifting energy_cost_above (stage, hub, ec)"""

    LOADSHIFTENERGYCOSTBELOW = "load_shifting_energy_cost_below"
    """Load shifting energy_cost_below (stage, hub, ec)"""

    LOADSHIFTFIXCOST = "load_shifting_fix_cost"
    """Load shifting fix_cost (stage, hub, ec)"""

    CONVTECHOUTEFF = "conv_tech_out_eff"
    """Conversion technology output efficiency (stage, tech, ec)"""

    CONVTECHAVAIL = "conv_tech_availability"
    """Conversion technology availability (stage, hub, tech)"""

    EBMTECHDEMANDNOM = "ebm_tech_demand_nominal"
    """EBM technology nominal demand (stage, hub, tech)"""

    EBMTECHAVAIL = "ebm_tech_availability"
    """EBM technology availability (stage, hub, tech)"""

    HPTECHCOP = "hp_tech_cop"
    """Heat pump technology COP (stage, hub, tech)"""

    HPTECHTEMPHTIN = "hp_tech_temp_ht_in"
    """Heat pump technology temperature of heat intake (stage, hub, tech)"""

    HPTECHTEMPHTOUT = "hp_tech_temp_ht_out"
    """Heat pump technology temperature of heat output (stage, hub, tech)"""

    SOLARIRRAD = "solar_irradiation"
    """Solar irradiation (stage, ec)"""

    WINDVELOCITY = "wind_velocity"
    """Wind velocity (stage, ec)"""

    NETLINKAVAIL = "net_link_availability"
    """Network link availability (stage, link, net_link_direction)"""


class SolverKind(Enum):
    """Third-party solvers that ehubX can interface with"""

    GUROBI = "Gurobi"
    """Gurobi (https://www.gurobi.com/)"""

    GLPK = "GLPK"
    """GLPK (https://www.gnu.org/software/glpk/)"""


# -------- #
# Literals #
# -------- #
EPS_ZEROCHECK: float = 1e-12
"""
Epsilon value that is used as a tolerance in numerical "almost" checks.
E.g.; x is considered almost 5 if abs(x-5) < EPS_ZEROCHECK
"""

EPS_SOFTZEROCHECK: float = 1e-2
"""
Epsilon value that is used as a tolerance in very forgiving "zero checks".
E.g.; x is considered close to 5 if abs(x-5) < EPS_SOFTZEROCHECK
"""

EPS_BIGM: float = 1e-5
"""
Epsilon value that is added to automatically calulated bigM values to
avoid bigM becoming zero accidentally.
"""

EPS_WEIGHTEDSUM: float = 1e-5
"""
Epsilon value that is used for the weighted sum method in multiobjective
optimization. If O_1 and O_2 are the objective functions, optimizing just O_1
is replaced by optimizing (1 - eps) * O_1 + eps * O_2. This gives stability
and increases the chance to obtain a Pareto optimal solution
"""

EPS_PARETOZEROCHECK_ABS: float = 1e-6
"""
Absolute epsilon value that is used together with EPS_PARETOZEROCHECK_REL to
check if two objective values x, y are sufficiently distinct,
i.e.; abs(x-y) >= eps_rel * max(abs(x), abs(y)) + eps_abs
"""

EPS_PARETOZEROCHECK_REL: float = 1e-3
"""
Relative epsilon value that is used together with EPS_PARETOZEROCHECK_ABS to
check if two objective values x, y are sufficiently distinct,
i.e.; abs(x-y) >= eps_rel * max(abs(x), abs(y)) + eps_abs
"""


def get_iterable_filename(path: str, length_iter: int = 2) -> str:
    """
    Given a file path, this method adds an iteration counter after the file
    name, looking the first counter for which no file exists

    :param path: Desired path to the filename e.g. /path/to/file.txt
    :type path: str
    :param length_iter: Length of the iteration counter, defaults to 2
    :type length_iter: int, optional
    :return: First iterated file path that is not taken yet, e.g.;
        /path/to/file_05.txt
    :rtype: str
    """
    format_string = "{:0" + str(length_iter) + "d}"
    raw_split = path.split(".")
    extension = raw_split[-1]
    full_path = ".".join(raw_split[0:-1])
    i = -1
    file_already_exists = True
    max_iter = pow(10, length_iter)

    def build_path(j: int):
        str_j = "_" + format_string.format(j)
        path = full_path + str_j + "." + extension
        return path

    while file_already_exists and (i < max_iter):
        i = i + 1
        try_path = build_path(i)
        file_already_exists = os.path.isfile(try_path)

    path = try_path if i < max_iter else build_path(0)

    return path


def celcius_to_kelvin(temp_c: float) -> float:
    """
    Convert a temperature given in degrees Celcius to Kelvin

    :param temp_c: Temperature in °C
    :type temp_c: float
    :return: Temperature in K
    :rtype: float
    """
    return temp_c + 273.15


def kelvin_to_celcius(temp_k: float) -> float:
    """
    Convert a temperature given in Kelving to degrees Celcius

    :param temp_k: Temperature in K
    :type temp_k: float
    :return: Temperature in °C
    :rtype: float
    """
    return temp_k - 273.15


def hours_to_days(timespan_h: float) -> float:
    """
    Convert a timespan given in hours to days

    :param timespan_h: Timespan in h
    :type timespan_h: float
    :return: Timespan in d
    :rtype: float
    """
    return timespan_h / 24


def days_to_hours(timespan_d: float) -> float:
    """
    Convert a timespan given in days to hours

    :param timespan_d: Timespan in d
    :type timespan_ds: float
    :return: Timespan in h
    :rtype: float
    """
    return timespan_d * 24


def hours_to_seconds(timespan_h: float) -> float:
    """
    Convert a timespan given in hours to seconds

    :param timespan_h: Timespan in h
    :type timespan_h: float
    :return: Timespan in s
    :rtype: float
    """
    return timespan_h * 3600


def seconds_to_hours(timespan_s: float) -> float:
    """
    Convert a timespan given in seconds to hours

    :param timespan_s: Timespan in s
    :type timespan_s: float
    :return: Timespan in h
    :rtype: float
    """
    return timespan_s / 3600
