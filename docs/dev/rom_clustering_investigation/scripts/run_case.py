"""Run one case of the ROM investigation and dump the results as JSON.

The ehubX implementation used is whatever is first on PYTHONPATH, so the same
script runs every method variant (see romlab.py, which sets PYTHONPATH).

usage: run_case.py <case> <mode> <num_ts_target> <out_json> [method] [fix_caps_json]

case    demo | ms3 | swissx | pv_bat | pv_bat_nostor | pv_bat_bak1 | demo_nostor
mode    profiles  original time series only (no clustering, no solve)
        cluster   clustering only
        full      solve the full-horizon model
        rom       cluster and solve
        regret    solve full-horizon operation with capacities fixed from fix_caps_json
                  (technology capacities and build decisions only; network
                  capacities are NOT fixed, so use it only on models without
                  network links to size, e.g. pv_bat, not demo)
method  tsam (default) | M3 (typical days) | M4 (temporal downsampling)
"""

import copy
import csv
import json
import os
import re
import sys
import time
import warnings

warnings.filterwarnings("ignore")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import tsam.timeseriesaggregation as tsam  # noqa: E402
from pyomo.core import Objective, Var, value  # noqa: E402

import ehubx  # noqa: E402
from ehubx import EhubX, ObjectiveType, RomMethod, RomSettings, SolverKind  # noqa: E402
from ehubx.core import rom  # noqa: E402
from ehubx.core.common import TimeSeriesKind  # noqa: E402
from ehubx.data.ec_data import EcId  # noqa: E402
from ehubx.data.energy_system_data import EnergySystem  # noqa: E402
from ehubx.data.hub_data import HubId  # noqa: E402
from ehubx.data.stage_data import StageId  # noqa: E402
from ehubx.data.time_data import TimeId, Times  # noqa: E402
from ehubx.data.unit import PowerUnit, TimeUnit  # noqa: E402
from ehubx.data.value import Value  # noqa: E402
from ehubx.model import ebm_tech_model, stor_tech_model, tech_model  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
INV = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(INV, "..", "..", ".."))
CASES = {
    "demo": os.path.join(REPO, "examples", "clustering_demo"),
    "ms3": os.path.join(INV, "models", "ms3"),
    "pv_bat": os.path.join(INV, "models", "pv_bat"),
    "pv_bat_nostor": os.path.join(INV, "models", "pv_bat_nostor"),
    "pv_bat_bak1": os.path.join(INV, "models", "pv_bat_bak1"),
    "demo_nostor": os.path.join(INV, "models", "demo_nostor"),
}
SWISSX_DIR = os.path.join(INV, "models", "swissx", "profiles")
SWISSX_FILES = (
    "demands.csv",
    "imports.csv",
    "exports.csv",
    "hub_profiles.csv",
    "solar_irradiation.csv",
    "wind_speed.csv",
)


def _is_int(text: str) -> bool:
    return text.strip().isdigit()


def load_swissx_profiles():
    """Return [(stage, name, values)] for every profile column of SwissX."""
    out = []
    for fname in SWISSX_FILES:
        with open(os.path.join(SWISSX_DIR, fname), newline="") as f:
            rows = [r for r in csv.reader(f) if r and any(c.strip() for c in r)]
        head = [r for r in rows if not _is_int(r[0])]
        data = [r for r in rows if _is_int(r[0])]
        stage_row = next(r for r in head if r[0] == "stage_id")
        label_rows = [r for r in head if r[0] not in ("stage_id", "hub_id", "unit")]
        for j in range(1, len(stage_row)):
            stage = stage_row[j].strip()
            if not stage:
                continue
            label = "|".join(r[j].strip() for r in label_rows if j < len(r))
            name = f"{fname[:-4]}|{label}|{j}"
            vals = [float(r[j]) if j < len(r) and r[j].strip() else 0.0 for r in data]
            out.append((stage, name, vals))
    return out


def swissx_system() -> EnergySystem:
    """Pseudo system: every SwissX profile is a demand of its own carrier."""
    profiles = load_swissx_profiles()
    kwh = PowerUnit.KW * TimeUnit.H
    num_ts = len(profiles[0][2])
    system = EnergySystem()
    system.num_times_horizon = num_ts
    times = Times()
    for t in range(1, num_ts + 1):
        times.add_id(TimeId(t))
    system.times = times
    hub = HubId("H1")
    system.hubs.add_id(hub)
    stages = sorted({s for s, _, _ in profiles})
    for i, s in enumerate(stages):
        system.stages.add_id(StageId(s))
        system.stages.set_start_year(StageId(s), 2020 + 10 * i)
    for k, (s, name, vals) in enumerate(profiles):
        ec = EcId("E" + re.sub(r"[^A-Za-z0-9]", "", name)[:40] + f"x{k}")
        system.ecs.add_id(ec)
        system.ecs.set_unit(ec, kwh)
        system.demands.add_profile_tuple(StageId(s), hub, ec, kwh)
        for t, v in enumerate(vals, start=1):
            system.demands.set_demand_in_profile(
                StageId(s), hub, ec, TimeId(t), Value(v, PowerUnit.KW)
            )
    return system


# ------------------------------------------------ custom ROM (M3, M4) --


def _extract_stage_dfs(system: EnergySystem):
    """Return {StageId: pd.DataFrame} indexed 0..N-1 with column tuple (kind, stage, *ids)."""
    hor = system.times.ids_horizon_in_order
    by_stage = {s: {} for s in system.stages.ids}
    for kind, stage_id, ids, ts in system.time_series:
        col = (kind.value, stage_id.key) + ids
        by_stage[stage_id][col] = [ts.get_value(t).to_float() for t in hor]
    return {s: pd.DataFrame(cols) for s, cols in by_stage.items()}


def _apply_clustered_system(
    system: EnergySystem,
    num_ts: int,
    order_by_stage: dict,
    df_cl_by_stage: dict,
) -> EnergySystem:
    """Build a reduced EnergySystem given per-stage 0-based cluster assignments & mean tables."""
    sys_red = copy.deepcopy(system)
    sys_red.times.clear_ids()
    for t_key in range(1, num_ts + 1):
        sys_red.times.add_id(TimeId(t_key))

    for s, order in order_by_stage.items():
        counts = np.bincount(order, minlength=num_ts)
        for t_idx in range(num_ts):
            sys_red.times.set_weight(s, TimeId(t_idx + 1), float(counts[t_idx]))
        for t_full_idx, t_cl_idx in enumerate(order):
            sys_red.times.set_cluster_ts(s, TimeId(int(t_cl_idx) + 1), TimeId(t_full_idx + 1))

    for _, _, _, series in sys_red.time_series:
        series.clear()
    for s, df_cl in df_cl_by_stage.items():
        for col in df_cl.columns:
            kind = TimeSeriesKind(col[0])
            stage_id = StageId(col[1])
            ids = tuple(col[2:])
            vals = df_cl[col].to_numpy()
            for t_idx in range(num_ts):
                sys_red.set_time_series_val(
                    kind, stage_id, ids, TimeId(t_idx + 1), float(vals[t_idx])
                )
    return sys_red


def cluster_typical_days(system: EnergySystem, target: int) -> EnergySystem:
    """M3: 24-hour typical days via hierarchical clustering + exact member means."""
    n_hor = system.times.num_horizon_ts
    n_days = n_hor // 24
    num_days = max(1, min(n_days - 1, round(target / 24)))
    num_ts = 24 * num_days
    dfs = _extract_stage_dfs(system)
    order_by_stage = {}
    df_cl_by_stage = {}
    for s, df_s in dfs.items():
        df_ts = df_s.copy()
        df_ts.index = pd.to_datetime(np.arange(len(df_ts)), unit="h")
        agg = tsam.TimeSeriesAggregation(
            df_ts,
            noTypicalPeriods=num_days,
            hoursPerPeriod=24,
            clusterMethod="hierarchical",
            extremePeriodMethod="None",
            rescaleClusterPeriods=False,
            representationMethod="meanRepresentation",
        )
        agg.createTypicalPeriods()
        day_order = np.asarray(agg.clusterOrder, dtype=int)
        labels, first_pos = np.unique(day_order, return_index=True)
        relabel = np.empty(num_days, dtype=int)
        relabel[labels[np.argsort(first_pos)]] = np.arange(len(labels))
        day_order = relabel[day_order]

        # Expand day cluster -> hour-level cluster 0..(24*num_days - 1)
        hour_of_day = np.tile(np.arange(24), n_days)
        order = np.repeat(day_order, 24) * 24 + hour_of_day
        order_by_stage[s] = order
        df_cl_by_stage[s] = df_s.groupby(order).mean()
    return _apply_clustered_system(system, num_ts, order_by_stage, df_cl_by_stage)


def cluster_downsample(system: EnergySystem, target: int) -> EnergySystem:
    """M4: contiguous temporal downsampling into K equal-ish blocks + exact means."""
    n_hor = system.times.num_horizon_ts
    num_ts = max(1, min(target, n_hor - 1))
    blocks = np.array_split(np.arange(n_hor), num_ts)
    order = np.empty(n_hor, dtype=int)
    for k, blk in enumerate(blocks):
        order[blk] = k
    dfs = _extract_stage_dfs(system)
    order_by_stage = {s: order for s in dfs}
    df_cl_by_stage = {s: df_s.groupby(order).mean() for s, df_s in dfs.items()}
    return _apply_clustered_system(system, num_ts, order_by_stage, df_cl_by_stage)


# ------------------------------------------------------- dump helpers --


def series_key(kind, s, ids) -> str:
    return "|".join([str(kind), str(s)] + [str(i) for i in ids])


def dump_profiles(system: EnergySystem) -> dict:
    hor = system.times.ids_horizon_in_order
    series = {}
    for kind, s, ids, ts in system.time_series:
        series[series_key(kind, s, ids)] = {
            "stage": str(s),
            "values": [ts.get_value(t).to_float() for t in hor],
        }
    return {"num_horizon_ts": len(hor), "series": series}


def dump_clustering(full: EnergySystem, red: EnergySystem) -> dict:
    """Mapping horizon step -> clustered step, weights and clustered values."""
    times = red.times
    cl_ids = times.ids_in_order
    stages = {}
    for s in red.stages.ids:
        stages[str(s)] = {
            "map": [
                int(times.get_cluster_ts(s, t).key_as_int)
                for t in full.times.ids_horizon_in_order
            ],
            "weights": {int(t.key_as_int): float(times.get_weight(s, t)) for t in cl_ids},
        }
    series = {}
    for kind, s, ids, ts in red.time_series:
        series[series_key(kind, s, ids)] = {
            "stage": str(s),
            "values": {int(t.key_as_int): float(ts.get_value(t).to_float()) for t in cl_ids},
        }
    return {
        "num_ts": len(cl_ids),
        "num_horizon_ts_red": red.times.num_horizon_ts,
        "stages": stages,
        "series": series,
    }


def dump_solution(ex: EhubX, system: EnergySystem) -> dict:
    m = ex._model
    res = {"objective": [value(o) for o in m.component_objects(Objective, active=True)][0]}
    res["caps"] = {
        ",".join(str(x) for x in k): value(v)
        for k, v in getattr(m, tech_model.VAR_TECHCAP).items()
        if v.value is not None and abs(v.value) > 1e-6
    }
    res["caps_instl"] = {
        ",".join(str(x) for x in k): float(value(v))
        for k, v in getattr(m, tech_model.VAR_TECHCAPINSTL).items()
    }
    # Hourly storage SOC trajectories (full horizon)
    hor_ints = [t.key_as_int for t in system.times.ids_horizon_in_order]
    soc = {}
    for tup_name, var_name in (
        (stor_tech_model.SET_STORTECHTUPLE, stor_tech_model.VAR_STORTECHENERGY),
        (ebm_tech_model.SET_EBMTECHTUPLE, ebm_tech_model.VAR_EBMTECHENERGY),
    ):
        if hasattr(m, tup_name) and hasattr(m, var_name):
            var_e = getattr(m, var_name)
            for s, h, x in getattr(m, tup_name):
                soc[f"{s},{h},{x}"] = [
                    round(float(value(var_e[s, h, x, t_h])), 3) for t_h in hor_ints
                ]
    if soc:
        res["soc"] = soc
    # Weighted sums of time-indexed import / export / shedding variables
    times = system.times
    time_set = {t.key_as_int for t in times.ids}
    flows = {}
    for v in m.component_objects(Var, active=True):
        if not any(x in v.name for x in ("Imp", "Exp", "Shed", "Unmet")):
            continue
        for k, vv in v.items():
            if vv.value is None or not isinstance(k, tuple) or k[-1] not in time_set:
                continue
            w = times.get_weight(StageId(k[0]), TimeId(k[-1]))
            key = f"{v.name}[{','.join(str(x) for x in k[:-1])}]"
            flows[key] = flows.get(key, 0.0) + w * vv.value
    res["flows"] = {k: x for k, x in flows.items() if abs(x) > 1e-6}
    return res


def main() -> None:
    case, mode, target, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
    method = sys.argv[5] if len(sys.argv) > 5 else "tsam"
    fix_caps_json = sys.argv[6] if len(sys.argv) > 6 else ""

    res = {"case": case, "mode": mode, "target": target, "method": method, "ehubx": ehubx.__file__}
    t0 = time.time()
    if case == "swissx":
        if mode in ("full", "rom", "regret"):
            raise SystemExit("swissx can only be clustered, not solved")
        system = swissx_system()
        ex = None
    else:
        ex = EhubX()
        ex.model_dir_path = CASES[case]
        ex.parse()
        system = ex.energy_system
    res["secs_parse"] = time.time() - t0

    if mode == "profiles":
        res.update(dump_profiles(system))
    elif mode in ("cluster", "rom"):
        t1 = time.time()
        if method == "M3":
            red = cluster_typical_days(system, target)
            if ex is not None:
                ex._energy_system_rom = red
        elif method == "M4":
            red = cluster_downsample(system, target)
            if ex is not None:
                ex._energy_system_rom = red
        else:
            settings = RomSettings(RomMethod.CLUSTER_TSAM, target)
            if ex is None:
                red = rom.rom(system, settings, write_rom=False)
            else:
                ex.rom(settings, write_rom=False)
                red = ex.energy_system_rom
        res["secs_cluster"] = time.time() - t1
        res["clustered"] = red is not None
        if red is not None:
            res.update(dump_clustering(system, red))
    if mode in ("full", "rom", "regret"):
        t1 = time.time()
        ex.build(use_rom=(mode == "rom"))
        if mode == "regret":
            with open(fix_caps_json) as f:
                ref = json.load(f)
            fixed_caps = ref.get("caps_instl", ref.get("caps", {}))

            def _fix_design(model):
                v_instl = getattr(model, tech_model.VAR_TECHCAPINSTL)
                v_y = getattr(model, tech_model.VAR_YTECHCAPINSTL)
                for k, v in v_instl.items():
                    key_str = ",".join(str(x) for x in k)
                    val = float(fixed_caps.get(key_str, 0.0))
                    if val < 1e-6:
                        v.fix(0.0)
                        v_y[k].fix(0)
                    else:
                        v.fix(val)
                        v_y[k].fix(1)

            ex.modify_model(_fix_design)
        ex.solve_single_obj(
            obj_type=ObjectiveType.COST,
            solver_kind=SolverKind.GUROBI,
            write_model=False,
            opt_vars_filename=None,
            results_dir_path=os.path.join(os.getcwd(), f"solver_results_{time.time_ns()}"),
        )
        res["secs_solve"] = time.time() - t1
        sys_used = ex.energy_system_rom if mode == "rom" else system
        res.update(dump_solution(ex, sys_used))
    res["secs_total"] = time.time() - t0
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out + ".tmp", "w") as f:
        json.dump(res, f)
    os.replace(out + ".tmp", out)


if __name__ == "__main__":
    main()
