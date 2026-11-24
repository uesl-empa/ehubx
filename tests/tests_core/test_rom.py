import csv
import os
from typing import Dict, List, Optional

import numpy as np
import pytest

from ehubx.core import exceptions, rom
from ehubx.core.rom import RomMethod, RomSettings
from ehubx.data.ec_data import EcId
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.hub_data import HubId
from ehubx.data.stage_data import StageId
from ehubx.data.time_data import TimeId, Times
from ehubx.data.time_series import TimeSeries
from ehubx.data.unit import CurrencyUnit, PowerUnit, TimeUnit
from ehubx.data.value import Value


HUB = HubId("H1")
KWH = PowerUnit.KW * TimeUnit.H

Profiles = Dict[str, Dict[str, np.ndarray]]


def make_system(demands: Profiles, prices: Optional[Profiles] = None) -> EnergySystem:
    """
    Build a minimal energy system with one hub. demands and prices map
    stage -> ec -> profile. Every stage in demands is added to the system.
    """
    system = EnergySystem()
    num_ts = len(next(iter(next(iter(demands.values())).values())))
    system.num_times_horizon = num_ts
    times = Times()
    for t in range(1, num_ts + 1):
        times.add_id(TimeId(t))
    system.times = times
    system.hubs.add_id(HUB)
    ecs = {
        e for profiles in (demands, prices or {}) for p in profiles.values() for e in p
    }
    for e in sorted(ecs):
        system.ecs.add_id(EcId(e))
        system.ecs.set_unit(EcId(e), KWH)
    for i, s in enumerate(demands):
        system.stages.add_id(StageId(s))
        system.stages.set_start_year(StageId(s), 2025 + 10 * i)
    for s, profiles in demands.items():
        for e, vals in profiles.items():
            system.demands.add_profile_tuple(StageId(s), HUB, EcId(e), KWH)
            for t, v in enumerate(vals, start=1):
                system.demands.set_demand_in_profile(
                    StageId(s), HUB, EcId(e), TimeId(t), Value(float(v), PowerUnit.KW)
                )
    for s, profiles in (prices or {}).items():
        for e, vals in profiles.items():
            system.imports.add_tuple(StageId(s), HUB, EcId(e), KWH)
            for t, v in enumerate(vals, start=1):
                system.imports.set_price(
                    StageId(s),
                    HUB,
                    EcId(e),
                    TimeId(t),
                    Value(float(v), CurrencyUnit.CHF / KWH),
                )
    return system


def cluster(system: EnergySystem, num_ts_target: int) -> Optional[EnergySystem]:
    return rom.rom(
        system,
        RomSettings(method=RomMethod.CLUSTER_TSAM, num_ts_target=num_ts_target),
        write_rom=False,
    )


def series_by_key(system: EnergySystem) -> Dict[tuple, TimeSeries]:
    return {(kind, s, ids): series for kind, s, ids, series in system.time_series}


def values(series: TimeSeries, ids: List[TimeId]) -> np.ndarray:
    return np.array([series.get_value(t).to_float() for t in ids])


@pytest.fixture(name="multistage")
def fixture_multistage() -> EnergySystem:
    """Two stages with a different number of time series and different peaks"""
    rng = np.random.default_rng(42)
    num_ts = 300
    daily = 1 + np.sin(np.arange(num_ts) * 2 * np.pi / 24)
    return make_system(
        demands={
            "S1": {
                "E1": daily * 100 + rng.uniform(0, 20, num_ts),
                "E2": rng.uniform(0, 5, num_ts),
                "E3": rng.gamma(2, 3, num_ts),
            },
            "S2": {"E1": daily[::-1] * 80 + rng.uniform(0, 50, num_ts)},
        },
        prices={
            "S1": {"E1": rng.uniform(5, 80, num_ts)},
            "S2": {"E1": rng.uniform(10, 120, num_ts)},
        },
    )


def test_no_clustering_if_target_not_smaller_than_horizon():
    rng = np.random.default_rng(4)
    system = make_system({"S1": {"E1": rng.uniform(0, 1, 50)}})
    assert cluster(system, 50) is None


def test_input_system_is_not_modified(multistage):
    before = {
        key: values(series, multistage.times.ids_horizon_in_order)
        for key, series in series_by_key(multistage).items()
    }
    cluster(multistage, 10)
    assert not multistage.times.is_clustered
    for key, series in series_by_key(multistage).items():
        np.testing.assert_array_equal(
            values(series, multistage.times.ids_horizon_in_order), before[key]
        )


def test_time_map_is_written(multistage, tmp_path):
    rom_dir = os.path.join(tmp_path, "rom")
    sys_rom = rom.rom(
        multistage,
        RomSettings(method=RomMethod.CLUSTER_TSAM, num_ts_target=10),
        write_rom=True,
        rom_dir_path=rom_dir,
    )
    assert sys_rom is not None
    with open(os.path.join(rom_dir, rom.FILENAME_TIMEMAP), encoding="utf8") as file:
        rows = list(csv.DictReader(file))
    num_hor = multistage.times.num_horizon_ts
    assert len(rows) == num_hor * len(multistage.stages.ids)
    for row in rows:
        s, t_hor = StageId(row["stage_id"]), TimeId(int(row["ts_full"]))
        t_cl = sys_rom.times.get_cluster_ts(s, t_hor)
        assert int(row["ts_cluster"]) == t_cl.key_as_int


def test_stage_with_only_zero_series():
    rng = np.random.default_rng(1)
    num_ts = 200
    system = make_system(
        {
            "S1": {"E1": rng.uniform(0, 1, num_ts)},
            "S2": {"E1": np.zeros(num_ts)},
        }
    )
    sys_rom = cluster(system, 10)
    assert sys_rom is not None
    demand = sys_rom.demands.get_demand_profile(StageId("S2"), HUB, EcId("E1"))
    assert not values(demand, sys_rom.times.ids_in_order).any()


def test_every_stage_gets_exactly_the_common_number_of_clusters():
    # A few outlier hours per series. Re-running tsam with more regular
    # clusters turns outliers into single-hour clusters, so tsam then skips
    # them as extreme periods and a re-clustered stage came out one cluster
    # short. The missing cluster was filled with NaN values and weight 1.
    rng = np.random.default_rng(0)
    num_ts = 400

    def spiky() -> np.ndarray:
        vals = rng.uniform(0, 1, num_ts)
        idx = rng.choice(num_ts, size=6, replace=False)
        vals[idx] += rng.uniform(3, 8, 6)
        return vals

    num_ser = {"S1": int(rng.integers(2, 6)), "S2": int(rng.integers(1, 5))}
    system = make_system(
        {s: {f"E{i}": spiky() for i in range(n)} for s, n in num_ser.items()}
    )
    sys_rom = cluster(system, 2 * max(num_ser.values()))
    assert sys_rom is not None
    times = sys_rom.times
    for kind, s, ids, series in sys_rom.time_series:
        assert not np.isnan(values(series, times.ids_in_order)).any(), (kind, s, ids)
    for s in sys_rom.stages.ids:
        used = {times.get_cluster_ts(s, t) for t in times.ids_horizon}
        assert len(used) == times.num_ts


def test_multistage_stages_share_all_cluster_time_steps(multistage):
    num_ts_target = 10
    sys_rom = cluster(multistage, num_ts_target)
    assert sys_rom is not None
    times = sys_rom.times
    # Horizon is untouched
    assert times.ids_horizon == multistage.times.ids_horizon
    # Each series contributes at most one max and one min. S1 has the most
    # extreme periods (4 series -> at most 8)
    num_ts_cl = times.num_ts
    assert num_ts_target < num_ts_cl <= num_ts_target + 8
    assert {t.key_as_int for t in times.ids} == set(range(1, num_ts_cl + 1))
    for s in sys_rom.stages.ids:
        # Every clustered time step is used in every stage, with an explicit
        # weight equal to its number of members
        members: Dict[TimeId, int] = {}
        for t_hor in times.ids_horizon:
            t_cl = times.get_cluster_ts(s, t_hor)
            members[t_cl] = members.get(t_cl, 0) + 1
        assert set(members) == times.ids
        for t_cl, num_members in members.items():
            assert (s, t_cl) in times._weight
            assert times.get_weight(s, t_cl) == num_members
        assert sum(times.get_weight(s, t) for t in times.ids) == times.num_horizon_ts


def test_no_phantom_time_step_when_extremes_share_a_cluster():
    # The peak hours of E1 and E2 are almost identical, so a plain clustering
    # would put them into one cluster. Both must become clusters of their own
    # without leaving an empty cluster behind that another stage still uses.
    rng = np.random.default_rng(0)
    num_ts = 300
    e1, e2 = rng.uniform(0, 1, num_ts), rng.uniform(0, 1, num_ts)
    e1[100], e2[100] = 10.0, 9.95
    e1[200], e2[200] = 9.95, 10.0
    system = make_system(
        {
            "S1": {"E1": e1, "E2": e2},
            "S2": {"E1": rng.uniform(0, 2, num_ts), "E2": rng.uniform(0, 3, num_ts)},
        }
    )
    sys_rom = cluster(system, 4)
    assert sys_rom is not None
    times = sys_rom.times
    for s in sys_rom.stages.ids:
        used = {times.get_cluster_ts(s, t) for t in times.ids_horizon}
        assert used == times.ids
        assert sum(times.get_weight(s, t) for t in times.ids) == num_ts


def assert_extremes_and_sums_preserved(full: EnergySystem, red: EnergySystem) -> None:
    times = red.times
    ids_hor = full.times.ids_horizon_in_order
    ids_cl = times.ids_in_order
    series_full = series_by_key(full)
    series_red = series_by_key(red)
    assert series_full.keys() == series_red.keys()
    for (kind, s, ids), series in series_full.items():
        v_full = values(series, ids_hor)
        v_cl = values(series_red[kind, s, ids], ids_cl)
        weights = np.array([times.get_weight(s, t) for t in ids_cl])
        assert v_cl.max() == pytest.approx(v_full.max()), (kind, s, ids)
        assert v_cl.min() == pytest.approx(v_full.min()), (kind, s, ids)
        assert weights @ v_cl == pytest.approx(v_full.sum(), rel=1e-9), (kind, s, ids)
        # The horizon time steps holding the extremes map to single-member
        # clusters with the exact extreme value
        for pos in (int(np.argmax(v_full)), int(np.argmin(v_full))):
            t_cl = times.get_cluster_ts(s, ids_hor[pos])
            assert times.get_weight(s, t_cl) == 1
            assert series_red[kind, s, ids].get_value(t_cl).to_float() == pytest.approx(
                v_full[pos]
            )


def test_multistage_preserves_extremes_and_sums_in_every_stage(multistage):
    # The stages have a different number of time series and therefore a
    # different number of extreme periods
    sys_rom = cluster(multistage, 10)
    assert sys_rom is not None
    assert_extremes_and_sums_preserved(multistage, sys_rom)


def test_negative_values_are_supported():
    # e.g. negative electricity prices
    rng = np.random.default_rng(6)
    num_ts = 200
    system = make_system(
        demands={
            "S1": {"E1": rng.uniform(0, 1, num_ts)},
            "S2": {"E1": rng.uniform(0, 2, num_ts)},
        },
        prices={
            "S1": {"E1": rng.uniform(-20, 80, num_ts)},
            "S2": {"E1": -rng.uniform(1, 2, num_ts)},
        },
    )
    sys_rom = cluster(system, 10)
    assert sys_rom is not None
    assert_extremes_and_sums_preserved(system, sys_rom)


def test_clustered_values_are_member_means(multistage):
    sys_rom = cluster(multistage, 10)
    assert sys_rom is not None
    times = sys_rom.times
    ids_hor = multistage.times.ids_horizon_in_order
    full = series_by_key(multistage)
    reduced = series_by_key(sys_rom)
    for (kind, s, ids), series in full.items():
        v_full = values(series, ids_hor)
        t_cl_of_hor = np.array([times.get_cluster_ts(s, t).key_as_int for t in ids_hor])
        for t_cl in times.ids:
            members = v_full[t_cl_of_hor == t_cl.key_as_int]
            assert reduced[kind, s, ids].get_value(t_cl).to_float() == pytest.approx(
                members.mean()
            )


def test_small_values_keep_exact_sums_and_extremes():
    rng = np.random.default_rng(2)
    num_ts = 200
    tiny = rng.uniform(1e-9, 5e-9, num_ts)
    system = make_system({"S1": {"E1": tiny, "E2": rng.uniform(0, 1, num_ts)}})
    sys_rom = cluster(system, 10)
    assert sys_rom is not None
    times = sys_rom.times
    series = sys_rom.demands.get_demand_profile(StageId("S1"), HUB, EcId("E1"))
    v_cl = values(series, times.ids_in_order)
    w = np.array([times.get_weight(StageId("S1"), t) for t in times.ids_in_order])
    assert w @ v_cl == pytest.approx(tiny.sum(), rel=1e-9, abs=0)
    assert v_cl.min() == pytest.approx(tiny.min(), rel=1e-12, abs=0)
    assert v_cl.max() == pytest.approx(tiny.max(), rel=1e-12, abs=0)


def test_stage_with_only_zero_or_constant_series():
    rng = np.random.default_rng(1)
    num_ts = 200
    system = make_system(
        {
            "S1": {"E1": rng.uniform(0, 1, num_ts)},
            "S2": {"E1": np.zeros(num_ts), "E2": np.full(num_ts, 3.0)},
        }
    )
    sys_rom = cluster(system, 10)
    assert sys_rom is not None
    times = sys_rom.times
    reduced = series_by_key(sys_rom)
    for (_, s, _), series in reduced.items():
        assert sum(times.get_weight(s, t) for t in times.ids) == num_ts
        if s == StageId("S2"):
            vals = values(series, times.ids_in_order)
            assert np.ptp(vals) == 0


def test_no_clustering_if_time_steps_would_not_be_reduced():
    # 12 series raise the target to 24 regular clusters plus up to 24 extreme
    # periods, which is more than the 30 horizon time steps
    rng = np.random.default_rng(3)
    system = make_system({"S1": {f"E{i}": rng.uniform(0, 1, 30) for i in range(12)}})
    assert cluster(system, 10) is None
    assert system.times.num_horizon_ts == 30
    assert not system.times.is_clustered


def test_non_finite_values_raise():
    vals = np.random.default_rng(5).uniform(0, 1, 100)
    vals[10] = np.inf
    system = make_system({"S1": {"E1": vals}})
    with pytest.raises(exceptions.EhubXException, match="non-finite"):
        cluster(system, 10)
