import os

import pytest
from pyomo.core import Objective, value

from ehubx import EhubX, Glpk, ObjectiveType, RomMethod, RomSettings
from ehubx.data.stage_data import StageId
from ehubx.data.time_data import TimeId
from ehubx.model import export_model, import_model, tech_model, wind_tech_model
from ehubx.model.times_model import SET_TIME

from ..util import (
    DIRNAME_EXAMPLES,
    DIRNAME_TMPTESTMODEL,
    init_tmp_model,
)


STAGE = "Y2030"
HUB = "Village"
EC = "Elec"
ANNUAL_DEMAND_KWH = 22.5e6


def test_examples_wind_demo():
    # Init
    example_model_dir = os.path.join(DIRNAME_EXAMPLES, "wind_demo")
    init_tmp_model(example_model_dir)

    # Run (clustered as in main_wind_demo.py)
    ehubx = EhubX()
    ehubx.model_dir_path = DIRNAME_TMPTESTMODEL
    ehubx.parse()
    ehubx.rom(rom_settings=RomSettings(method=RomMethod.CLUSTER_TSAM, num_ts_target=50))
    ehubx.build()
    ehubx.set_solver(Glpk())
    ehubx.solve_single_obj(obj_type=ObjectiveType.COST)
    model = ehubx._model
    system = ehubx.energy_system_rom

    # The clustered time steps still represent the full year
    weights = {
        t: system.times.get_weight(StageId(STAGE), TimeId(t))
        for t in getattr(model, SET_TIME)
    }
    assert sum(weights.values()) == pytest.approx(8760)

    # Only the large-rotor E-138 is built, and only on (cheaper) pasture.
    # Checked are values that the optimum fixes uniquely, with a tolerance that
    # absorbs small differences in the clustering.
    def cap(x):
        return value(getattr(model, tech_model.VAR_TECHCAP)[STAGE, HUB, x])

    assert cap("Wind_E82") == pytest.approx(0, abs=1e-3)
    assert cap("Wind_V112") == pytest.approx(0, abs=1e-3)
    assert cap("Wind_E138") == pytest.approx(13276, rel=0.02)

    cap_in_group = getattr(model, wind_tech_model.VAR_WINDTECHCAPINGROUP)
    by_terrain = {
        terrain: value(v)
        for (s, h, x, w, terrain), v in cap_in_group.items()
        if x == "Wind_E138"
    }
    assert by_terrain["Pasture"] == pytest.approx(cap("Wind_E138"), rel=1e-6)
    assert by_terrain["Forest"] == pytest.approx(0, abs=1e-3)

    # The pasture area is not exhausted: the size is an economic optimum.
    # Pasture: 4 km^2 * 60% / 0.35 km^2 per turbine * 4260 kW per turbine.
    assert cap("Wind_E138") < 0.9 * (4.0 * 0.6 / 0.35 * 4260)

    # Annual energy balance: wind + import - export = demand. Clustering keeps
    # the annual demand to within about 0.1%, not exactly.
    def annual(var, index):
        return sum(
            value(getattr(model, var)[index + (t,)]) * w for t, w in weights.items()
        )

    wind_out = getattr(model, wind_tech_model.VAR_WINDTECHOUT)
    generation = sum(value(v) * weights[k[-1]] for k, v in wind_out.items())
    imports = annual(import_model.VAR_IMP, (STAGE, HUB, EC))
    exports = annual(export_model.VAR_EXP, (STAGE, HUB, EC))
    assert generation + imports - exports == pytest.approx(ANNUAL_DEMAND_KWH, rel=1e-3)
    assert generation == pytest.approx(31.6e6, rel=0.03)
    assert imports == pytest.approx(9.1e6, rel=0.03)

    # Total annual cost
    objective = [o for o in model.component_objects(Objective, active=True)][0]
    assert value(objective) == pytest.approx(3.715e6, rel=0.01)
