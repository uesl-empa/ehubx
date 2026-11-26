"""Helpers for the ROM clustering investigation notebooks.

Every method variant is a pinned ehubX commit. Its ``src`` folder is extracted
with ``git archive`` into ``results/src/<variant>`` and run_case.py is executed
in a subprocess with that folder on PYTHONPATH. Results are cached as JSON in
``results/runs``; delete a file (or pass ``force=True``) to recompute it.
"""

import json
import os
import subprocess
import sys
import tarfile
import io
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
INV = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(INV, "..", "..", ".."))
RESULTS = os.path.join(INV, "results")
PYTHON = sys.executable

# Method variants (see PLAN.md, section 3). M0 (full horizon) uses the M2 code.
VARIANTS: Dict[str, str] = {
    "M1": "d436c9b7",  # main: typical hours, tsam new_cluster_center
    "M1b": "f69e03d5",  # PR #58: per-stage re-clustering to a common count
    "M2": "bd1a0c89",  # 57-rom-extreme-periods: hand-picked extremes, member means
}
LABELS = {
    "M0": "M0 full horizon",
    "M1": "M1 existing (main)",
    "M1b": "M1b PR #58",
    "M2": "M2 proposed fix",
}


def ensure_src(variant: str) -> str:
    """Extract the src folder of a variant's commit; return the path to it."""
    dst = os.path.join(RESULTS, "src", variant)
    if not os.path.isdir(os.path.join(dst, "src", "ehubx")):
        os.makedirs(dst, exist_ok=True)
        tar = subprocess.run(
            ["git", "-C", REPO, "archive", VARIANTS[variant], "src"],
            check=True,
            capture_output=True,
        ).stdout
        with tarfile.open(fileobj=io.BytesIO(tar)) as tf:
            tf.extractall(dst)
    return os.path.join(dst, "src")


def run(case: str, variant: str, mode: str, target: int = 0, force: bool = False) -> dict:
    """Run (or load from cache) one case. variant M0 means mode full / profiles."""
    code = "M2" if variant == "M0" else variant
    out = os.path.join(RESULTS, "runs", f"{case}_{variant}_{mode}_{target}.json")
    if force or not os.path.isfile(out):
        env = dict(os.environ, PYTHONPATH=ensure_src(code))
        work = os.path.join(RESULTS, "work", f"{case}_{variant}_{mode}_{target}")
        os.makedirs(work, exist_ok=True)
        proc = subprocess.run(
            [PYTHON, os.path.join(HERE, "run_case.py"), case, mode, str(target), out],
            env=env,
            cwd=work,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"{case} {variant} {mode} {target} failed:\n{proc.stderr[-3000:]}"
            )
    with open(out) as f:
        return json.load(f)


# ---------------------------------------------------------------- metrics --


def series_metrics(profiles: dict, clustering: dict) -> pd.DataFrame:
    """Input-level error of a clustering, one row per time series.

    wsum_err   relative error of the weighted sum vs the horizon sum
    max_err    (clustered max - horizon max) / horizon range
    min_err    (clustered min - horizon min) / horizon range
    dc_nrmse   RMSE between horizon duration curve and clustered duration
               curve (clustered values repeated by their weights), / range
    chr_nrmse  RMSE between the horizon profile and the profile rebuilt from
               the horizon -> cluster map (what storage sees), / range
    """
    rows = []
    for key, ser in profiles["series"].items():
        cl = clustering["series"].get(key)
        if cl is None:
            continue
        s = ser["stage"]
        orig = np.asarray(ser["values"], dtype=float)
        st = clustering["stages"][s]
        ids = sorted(int(t) for t in st["weights"])
        w = np.array([st["weights"][str(t)] if str(t) in st["weights"] else st["weights"][t] for t in ids])
        v = np.array([cl["values"][str(t)] if str(t) in cl["values"] else cl["values"][t] for t in ids])
        rng = float(orig.max() - orig.min())
        total = float(orig.sum())
        wsum = float((w * v).sum())
        rebuilt = np.array([cl["values"].get(str(t), cl["values"].get(t)) for t in st["map"]])
        # duration curve: only meaningful if weights are integer member counts
        dc = np.sort(np.repeat(v, np.round(w).astype(int)))[::-1]
        oc = np.sort(orig)[::-1]
        n = min(len(dc), len(oc))
        used = w > 0
        rows.append(
            {
                "series": key,
                "stage": s,
                "kind": key.split("|")[0],
                "constant": rng == 0,
                "wsum_err": (wsum - total) / abs(total) if total else wsum - total,
                "max_err": (v[used].max() - orig.max()) / rng if rng else 0.0,
                "min_err": (v[used].min() - orig.min()) / rng if rng else 0.0,
                "dc_nrmse": float(np.sqrt(np.mean((dc[:n] - oc[:n]) ** 2))) / rng if rng else 0.0,
                "chr_nrmse": float(np.sqrt(np.mean((rebuilt - orig) ** 2))) / rng if rng else 0.0,
            }
        )
    return pd.DataFrame(rows)


def stage_summary(clustering: dict, num_horizon_ts: int) -> pd.DataFrame:
    """Per stage: clustered steps, steps used (members > 0), weight sum, phantoms."""
    rows = []
    for s, st in clustering["stages"].items():
        members = pd.Series(st["map"]).value_counts()
        w = {int(t): x for t, x in st["weights"].items()}
        phantom = [t for t in w if t not in members.index]
        rows.append(
            {
                "stage": s,
                "num_ts": len(w),
                "used": int((members > 0).sum()),
                "phantom": len(phantom),
                "weight_sum": sum(w.values()),
                "weight_sum_err": sum(w.values()) - num_horizon_ts,
                "weight_ne_members": sum(
                    1 for t, x in w.items() if abs(x - members.get(t, 0)) > 1e-9
                ),
            }
        )
    return pd.DataFrame(rows)


def solution_compare(full: dict, red: dict) -> dict:
    """Objective and capacity differences between a ROM solve and the full solve."""
    caps = sorted(set(full["caps"]) | set(red["caps"]))
    cf = np.array([full["caps"].get(c, 0.0) for c in caps])
    cr = np.array([red["caps"].get(c, 0.0) for c in caps])
    built_f = cf > 1e-6
    built_r = cr > 1e-6
    return {
        "obj_err": (red["objective"] - full["objective"]) / abs(full["objective"]),
        "cap_abs_diff_rel": float(np.abs(cr - cf).sum() / max(np.abs(cf).sum(), 1e-12)),
        "techs_flipped": int((built_f != built_r).sum()),
        "secs_solve": red.get("secs_solve"),
    }


def cap_table(runs: Dict[str, dict]) -> pd.DataFrame:
    caps = sorted({c for r in runs.values() for c in r["caps"]})
    return pd.DataFrame({k: [r["caps"].get(c, 0.0) for c in caps] for k, r in runs.items()}, index=caps)


def flow_table(runs: Dict[str, dict]) -> pd.DataFrame:
    keys = sorted({c for r in runs.values() for c in r["flows"]})
    return pd.DataFrame({k: [r["flows"].get(c, 0.0) for c in keys] for k, r in runs.items()}, index=keys)


def summarize_metrics(df: pd.DataFrame, by: Optional[List[str]] = None) -> pd.DataFrame:
    """Aggregate series metrics (non-constant series only)."""
    d = df[~df["constant"]].copy()
    for c in ("wsum_err", "max_err", "min_err"):
        d[c] = d[c].abs()
    agg = {
        "wsum_err": ["mean", "max"],
        "max_err": ["mean", "max"],
        "min_err": ["mean", "max"],
        "dc_nrmse": "mean",
        "chr_nrmse": "mean",
    }
    out = d.groupby(by).agg(agg) if by else d.agg(agg)
    return out
