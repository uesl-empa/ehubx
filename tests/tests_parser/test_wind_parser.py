from ehubx.data.ec_data import Ecs
from ehubx.data.hub_data import Hubs
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.tech_data import Techs
from ehubx.data.time_data import TimeId
from ehubx.data.time_data import Times
from ehubx.data.unit import LengthUnit
from ehubx.data.wind_data import WindData
from ehubx.data.wind_data import TerrainId, WindGroupId
from ehubx.data.wind_tech_data import WindTechs
from ehubx.parser import wind_parser


def _write_csv(directory, name, content):
    """Write a small CSV fixture into the temporary test directory."""
    path = directory / name
    path.write_text(content, encoding="utf-8")


def test_parse_group_heights_terrain_roughness_and_transposed_areas(tmp_path):
    """Parse wind group metadata and terrain shares from compact CSV fixtures."""
    _write_csv(
        tmp_path,
        "wind_groups.csv",
        "wind_group_id,W1,W2\nunit,m,m\nheight,100,120\n",
    )
    _write_csv(
        tmp_path,
        "wind_terrains.csv",
        "terrain_id,Alps,Plateau\nunit,m,m\nroughness,0.6,0.1\n",
    )
    # Areas are stored in the repo's transposed layout: rows are terrains,
    # columns are wind groups.
    _write_csv(
        tmp_path,
        "wind_terrain_areas.csv",
        "wind_group_id,W1,W2\nunit,1,1\nAlps,0.8,0.2\nPlateau,0.2,0.8\n",
    )

    wind_data = wind_parser.parse_data(str(tmp_path))

    assert wind_data.get_wind_group_height(WindGroupId("W1")).to_float(
        LengthUnit.M
    ) == 100
    assert wind_data.get_wind_group_height(WindGroupId("W2")).to_float(
        LengthUnit.M
    ) == 120
    assert wind_data.get_terrain_roughness(TerrainId("Alps")).to_float(
        LengthUnit.M
    ) == 0.6
    assert wind_data.get_terrain_area_frac(
        WindGroupId("W1"), TerrainId("Alps")
    ) == 0.8
    assert wind_data.get_terrain_area_frac(
        WindGroupId("W2"), TerrainId("Plateau")
    ) == 0.8


def test_parse_fixed_turbulence_intensity_from_fixed_file(tmp_path):
    """Parse stage-level fixed turbulence intensity values per wind group."""
    _write_csv(
        tmp_path,
        "wind_groups.csv",
        "wind_group_id,W1,W2\nunit,m,m\nheight,100,120\n",
    )
    _write_csv(
        tmp_path,
        "wind_turbulence_intensity_fixed.csv",
        (
            "stage_id,S1,S1\n"
            "wind_group_id,W1,W2\n"
            "unit,1,1\n"
            "turbulence_intensity,0.11,0.16\n"
        ),
    )

    wind_data = wind_parser.parse_data(str(tmp_path))

    assert wind_data.get_fixed_turbulence_intensity(
        StageId("S1"), WindGroupId("W1")
    ).to_float() == 0.11
    assert wind_data.get_fixed_turbulence_intensity(
        StageId("S1"), WindGroupId("W2")
    ).to_float() == 0.16


def test_parse_turbulence_intensity_profile(tmp_path):
    """Parse time-series turbulence intensity input for a wind group."""
    _write_csv(
        tmp_path,
        "wind_groups.csv",
        "wind_group_id,W1\nunit,m\nheight,100\n",
    )
    _write_csv(
        tmp_path,
        "wind_turbulence_intensity_profile.csv",
        "stage_id,S1\nwind_group_id,W1\nunit,1\n1,0.10\n2,0.20\n",
    )

    wind_data = wind_parser.parse_data(str(tmp_path))
    ti_profile = wind_data.get_turbulence_intensity_profile(
        StageId("S1"), WindGroupId("W1")
    )

    assert ti_profile is not None
    assert ti_profile.get_value(TimeId(1)).to_float() == 0.10
    assert ti_profile.get_value(TimeId(2)).to_float() == 0.20


def test_parse_data_allows_empty_directory_for_non_wind_setup(tmp_path):
    """An input set without wind files should still parse cleanly."""
    wind_data = wind_parser.parse_data(str(tmp_path))

    assert wind_data.get_wind_groups() == set()
    assert wind_data.time_series == []


def test_empty_wind_objects_validate_for_non_wind_setup():
    """Empty wind containers must validate for legacy non-wind models."""
    wind_data = WindData()
    wind_techs = WindTechs()

    stages = Stages()
    hubs = Hubs()
    times = Times()
    ecs = Ecs()
    techs = Techs()

    wind_data.validate(stages, hubs, times)
    wind_techs.validate(ecs, techs, terrain_keys=set())
