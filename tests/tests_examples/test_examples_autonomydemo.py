import os

import pytest
import yaml
from pyomo.core import value

from ehubx import EhubX
from ehubx.model import autonomy_model

from ..util import DIRNAME_EXAMPLES, DIRNAME_TMPTESTMODEL, init_tmp_model


def _build_autonomy_demo(allow_unmet_demand):
    """Build the autonomy demo model with the flag set on all stages (None = key absent)."""
    init_tmp_model(os.path.join(DIRNAME_EXAMPLES, "autonomy_demo"))

    stages_file = os.path.join(DIRNAME_TMPTESTMODEL, "inputs", "basic", "stages.yaml")
    with open(stages_file, encoding="utf-8") as f:
        content = yaml.safe_load(f)
    for stage in content["stages"]:
        if allow_unmet_demand is None:
            stage.pop("autonomy_allow_unmet_demand", None)
        else:
            stage["autonomy_allow_unmet_demand"] = allow_unmet_demand
    with open(stages_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(content, f, sort_keys=False)

    ehubx = EhubX()
    ehubx.model_dir_path = DIRNAME_TMPTESTMODEL
    ehubx.parse()
    ehubx.build()
    return ehubx._model


def _unmet_allowed_values(model, enabled):
    autonomy_model.configure_autonomy(model, enabled=enabled)
    par = getattr(model, autonomy_model.PAR_DEMANDUNMETALLOWED)
    return {value(par[s]) for s in getattr(model, autonomy_model.SET_STAGE)}


@pytest.mark.parametrize(
    "flag, expected_if_enabled",
    [
        (True, 1),   # This catches the problem observed in #17 regression:
                     # demand_model.build() stopped storing the per-stage
                     # flags, so this silently became 0
        (False, 0),
        (None, 0),   # key absent
    ],
)
def test_autonomy_allow_unmet_demand_reaches_model(flag, expected_if_enabled):
    model = _build_autonomy_demo(flag)
    assert model.find_component(autonomy_model.PAR_DEMANDUNMETALLOWED) is not None

    # Autonomy enabled: the stage flag decides
    assert _unmet_allowed_values(model, enabled=True) == {expected_if_enabled}
    # Autonomy disabled: unmet demand is never allowed, whatever the flag
    assert _unmet_allowed_values(model, enabled=False) == {0}
    