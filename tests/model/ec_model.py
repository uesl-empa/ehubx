"""Energy carrier (ec) submodel"""

from datetime import datetime

from pyomo.core import Model, Set

from ehubx.core import logging
from ehubx.data.ec_data import Ecs
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.unit import MassUnit, PowerUnit, TimeUnit, Unit


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "mod/ec"
"""String identifying the ec model for logging purposes"""

SET_EC: str = "S_Ec"
"""Name of set of ec indices"""


def build(model: Model, system: EnergySystem) -> None:
    """
    Builds the energy carrier (ec) submodel. For a mathematical description
    in thorough detail, please refer to the section 'Ec model' in the
    documentation.

    :param model: Pyomo model
    :type model: Model
    :param system: Energy system data
    :type system: EnergySystem
    """
    # Extract data from modules
    ecs: Ecs = system.ecs
    # Start measuring build time
    start = datetime.now()
    # [SET] Energy carriers
    setattr(model, SET_EC, Set(initialize=[e.key for e in ecs.ids]))
    # Logging
    elapsed = datetime.now() - start
    logging.log_file(
        f"Built ec module. Elapsed time: {int(elapsed.total_seconds())}s",
        module=LOG_MODULE_STR,
    )


def get_ec_model_unit(
    ec_unit: Unit, model_mass_unit: MassUnit, model_power_unit: PowerUnit
) -> Unit:
    """
    Get the unit of an ec that will be used in the MILP model. This is either
    the model mass unit or time the model power unit multiplied by hours,
    depending on the unit of the ec.

    :param ec_unit: Unit of the ec
    :type ec_unit: Unit
    :param model_mass_unit: Mass unit used in the model
    :type model_mass_unit: MassUnit
    :param model_power_unit: Power unit used in the model
    :type model_power_unit: PowerUnit
    :raises RuntimeError: If the ec_unit is not a valid unit for an ec
    :return: The model unit corresponding to the ec_unit
    :rtype: Unit
    """
    if ec_unit.same_type_as(MassUnit.KG):
        return model_mass_unit
    elif ec_unit.same_type_as(PowerUnit.KW * TimeUnit.H):
        return model_power_unit * TimeUnit.H
    else:
        raise RuntimeError(
            f"Unexpected ec_unit {ec_unit} encountered. This should never happen."
        )
