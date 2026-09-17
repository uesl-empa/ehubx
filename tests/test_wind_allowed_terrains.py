import pytest

from ehubx.data import exceptions
from ehubx.data.tech_data import TechId
from ehubx.data.wind_tech_data import WindTechs


def test_is_terrain_allowed_default_all_terrains_allowed():
    wind_techs = WindTechs()
    tech_id = TechId("WIND_X")
    wind_techs.add_id(tech_id)

    assert not wind_techs.has_allowed_terrains(tech_id)
    assert wind_techs.is_terrain_allowed(tech_id, "Alps")
    assert wind_techs.is_terrain_allowed(tech_id, "Plateau")


def test_is_terrain_allowed_with_allow_list():
    wind_techs = WindTechs()
    tech_id = TechId("WIND_X")
    wind_techs.add_id(tech_id)
    wind_techs.set_allowed_terrains(tech_id, {"Alps"})

    assert wind_techs.has_allowed_terrains(tech_id)
    assert wind_techs.is_terrain_allowed(tech_id, "Alps")
    assert not wind_techs.is_terrain_allowed(tech_id, "Jura")


def test_validate_allowed_terrains_raises_for_unknown_terrain():
    wind_techs = WindTechs()
    tech_id = TechId("WIND_X")
    wind_techs.add_id(tech_id)
    wind_techs.set_allowed_terrains(tech_id, {"Atlantis"})

    with pytest.raises(exceptions.DataException):
        wind_techs._validate_allowed_terrains({"Alps", "Jura", "Plateau"})


def test_is_subgroup_allowed_unrestricted_when_no_terrain_restriction():
    wind_techs = WindTechs()
    tech_id = TechId("WIND_X")
    wind_techs.add_id(tech_id)

    assert wind_techs.is_subgroup_allowed(tech_id, "W1", "Alps")
    assert wind_techs.is_subgroup_allowed(tech_id, "W2", "Jura")


def test_is_subgroup_allowed_restricted_by_terrain():
    wind_techs = WindTechs()
    tech_id = TechId("WIND_X")
    wind_techs.add_id(tech_id)
    wind_techs.set_allowed_terrains(tech_id, {"Alps"})

    assert wind_techs.is_subgroup_allowed(tech_id, "W1", "Alps")
    assert wind_techs.is_subgroup_allowed(tech_id, "W2", "Alps")
    assert not wind_techs.is_subgroup_allowed(tech_id, "W1", "Jura")


def test_is_subgroup_allowed_denies_degenerate_subgroup_with_terrain_restriction():
    wind_techs = WindTechs()
    tech_id = TechId("WIND_X")
    wind_techs.add_id(tech_id)
    wind_techs.set_allowed_terrains(tech_id, {"Alps"})

    # degenerate fallback sub-group (no terrain split available): terrain == wind_group
    assert not wind_techs.is_subgroup_allowed(tech_id, "W1", "W1")
