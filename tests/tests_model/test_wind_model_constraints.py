from unittest.mock import Mock

import pytest
from pyomo.environ import ConcreteModel, Param, Set, Var, value

from ehubx.data.wind_data import TerrainId
from ehubx.model import wind_tech_model
from ehubx.model.stage_model import SET_STAGE


class _Scalar:
    def __init__(self, value):
        self.value = value

    def to_float(self, unit=None):
        return self.value


def _stages(years):
    stages = Mock()
    stages.get_start_year.side_effect = lambda stage: years[stage.key]
    return stages


def _add_wind_install_components(model, stages):
    tuples = [(stage, "H1", "Wind") for stage in stages]
    setattr(model, SET_STAGE, Set(initialize=list(stages)))
    setattr(
        model,
        wind_tech_model.SET_WINDTECHTUPLE,
        Set(dimen=3, initialize=tuples),
    )
    setattr(
        model,
        wind_tech_model.SET_WINDSUBGROUP,
        Set(dimen=2, initialize=[("W1", "Plateau")]),
    )
    setattr(
        model,
        wind_tech_model.VAR_WINDTECHCAPINSTLGROUP,
        Var(
            getattr(model, wind_tech_model.SET_WINDTECHTUPLE),
            getattr(model, wind_tech_model.SET_WINDSUBGROUP),
        ),
    )


def test_wind_capacity_stays_in_subgroup_during_lifetime():
    model = ConcreteModel()
    years = {"S1": 2020, "S2": 2030, "S3": 2040, "S4": 2050}
    _add_wind_install_components(model, years)
    setattr(
        model,
        wind_tech_model.VAR_WINDTECHCAPINGROUP,
        Var(
            getattr(model, wind_tech_model.SET_WINDTECHTUPLE),
            getattr(model, wind_tech_model.SET_WINDSUBGROUP),
        ),
    )

    system = Mock()
    system.stages = _stages(years)
    system.techs.get_lifetime.return_value = _Scalar(25)
    wind_tech_model._con_wind_tech_cap_in_group_min(model, system)

    installed = getattr(model, wind_tech_model.VAR_WINDTECHCAPINSTLGROUP)
    capacity = getattr(model, wind_tech_model.VAR_WINDTECHCAPINGROUP)
    for stage, amount in zip(years, [1, 2, 3, 4]):
        installed[stage, "H1", "Wind", "W1", "Plateau"].value = amount

    # At 2050, the 2020 installation has expired; later installs remain.
    capacity["S4", "H1", "Wind", "W1", "Plateau"].value = 9
    constraint = getattr(model, wind_tech_model.CON_WINDTECHCAPINGROUPMIN)[
        "S4", "H1", "Wind", "W1", "Plateau"
    ]
    assert value(constraint.body) == pytest.approx(0)


def test_wind_area_counts_previous_installations_within_lifetime():
    model = ConcreteModel()
    years = {"S1": 2020, "S2": 2030}
    _add_wind_install_components(model, years)
    setattr(
        model,
        wind_tech_model.SET_WINDHUBTUPLE,
        Set(dimen=2, initialize=[("S1", "H1"), ("S2", "H1")]),
    )
    model.wind_tech_ids = Set(initialize=["Wind"])
    setattr(
        model,
        wind_tech_model.PAR_WINDTECHAREAPERTURBINE,
        Param(model.wind_tech_ids, initialize={"Wind": 10}),
    )

    system = Mock()
    system.stages = _stages(years)
    system.techs.get_lifetime.return_value = _Scalar(25)
    system.power_unit = Mock()
    system.wind_techs.get_rated_power.return_value = _Scalar(2)
    system.wind_data.get_area.return_value = _Scalar(100)
    system.wind_data.get_terrain_fracs_for_group.return_value = {
        TerrainId("Plateau"): 0.5,
        TerrainId("Jura"): 0.5,
    }
    wind_tech_model._con_wind_area_instl_cap(model, system)

    installed = getattr(model, wind_tech_model.VAR_WINDTECHCAPINSTLGROUP)
    installed["S1", "H1", "Wind", "W1", "Plateau"].value = 4
    installed["S2", "H1", "Wind", "W1", "Plateau"].value = 6

    constraint = getattr(model, wind_tech_model.CON_WINDAREAINSTLCAP)[
        "S2", "H1", "W1", "Plateau"
    ]
    assert value(constraint.body) == pytest.approx(50)
    assert value(constraint.upper) == pytest.approx(50)
