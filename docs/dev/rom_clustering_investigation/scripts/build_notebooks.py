"""Generate the experiment notebooks (E0, E1) and execute them.

usage: build_notebooks.py

The notebooks are saved with their outputs, so they can be viewed without
running them. Runs come from the cache in results/runs (see run_batch.py).
"""

import os

import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor

HERE = os.path.dirname(os.path.abspath(__file__))
NB_DIR = os.path.join(os.path.dirname(HERE), "notebooks")

SETUP = """\
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join("..", "scripts")))
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import romlab as rl

pd.set_option("display.float_format", lambda x: f"{x:,.4g}")
pd.set_option("display.max_rows", 200)
pd.set_option("display.width", 200)

def try_run(*args):
    try:
        return rl.run(*args)
    except Exception as exc:  # failed runs are reported, not hidden
        return {"error": str(exc).strip().splitlines()[-1]}

print({k: v for k, v in rl.VARIANTS.items()})"""


def md(text):
    return nbf.v4.new_markdown_cell(text)


def code(text):
    return nbf.v4.new_code_cell(text)


def findings(name):
    path = os.path.join(NB_DIR, f"{name}_findings.md")
    if os.path.isfile(path):
        return [md(open(path, encoding="utf8").read())]
    return [md("## Findings\n\n_To be written after the first run._")]


def e0():
    cells = [
        md(
            "# E0 – Baseline: M0 vs M1, M1b, M2\n\n"
            "Same target number of clustered time steps for all methods "
            "(150 for the demo models, 144 for SwissX as in the thesis runs).\n\n"
            "| ID | Method | Code |\n|---|---|---|\n"
            "| M0 | full horizon (8760 h) | branch code |\n"
            "| M1 | existing method (`main`) | `d436c9b7` |\n"
            "| M1b | PR #58 (per-stage re-clustering) | `f69e03d5` |\n"
            "| M2 | proposed fix (`57-rom-extreme-periods`) | `bd1a0c89` |\n\n"
            "Cases:\n"
            "- **demo**: `examples/clustering_demo`, 1 stage, solved with Gurobi.\n"
            "- **ms3**: synthetic 2-stage version of the demo (`models/ms3`), solved.\n"
            "- **swissx**: the 178 SwissX profiles (4 stages), clustered only. Every "
            "profile enters as a demand series of a pseudo system, so the "
            "clustering sees the same matrix as in the real model if all these "
            "profiles are time series there. The model is not solved (needs the "
            "wind module and hours of Gurobi time).\n\n"
            "Metrics are defined in `scripts/romlab.py` (`series_metrics`, "
            "`stage_summary`, `solution_compare`)."
        ),
        code(SETUP),
        code(
            'TARGET = {"demo": 150, "ms3": 150, "swissx": 144}\n'
            'MODE = {"demo": "rom", "ms3": "rom", "swissx": "cluster"}\n'
            'VARS = ["M1", "M1b", "M2"]\n'
            'prof = {c: rl.run(c, "M0", "profiles") for c in TARGET}\n'
            'full = {c: rl.run(c, "M0", "full") for c in ("demo", "ms3")}\n'
            "red = {(c, v): try_run(c, v, MODE[c], TARGET[c]) for c in TARGET for v in VARS}\n"
            "for k, r in red.items():\n"
            '    print(k, "ERROR: " + r["error"] if "error" in r else f"{r[\'num_ts\']} clustered steps")'
        ),
        md(
            "## 1. Structure of the clustering per stage\n\n"
            "`used` = clustered steps with at least one member hour, `phantom` = "
            "steps without members (issue 2), `weight_ne_members` = steps whose "
            "weight differs from their number of member hours."
        ),
        code(
            "rows = []\n"
            "for (c, v), r in red.items():\n"
            '    if "error" in r:\n'
            "        continue\n"
            '    df = rl.stage_summary(r, prof[c]["num_horizon_ts"])\n'
            '    df.insert(0, "variant", v); df.insert(0, "case", c)\n'
            "    rows.append(df)\n"
            "structure = pd.concat(rows, ignore_index=True)\n"
            "structure"
        ),
        md(
            "## 2. Input-level errors\n\n"
            "Absolute values, non-constant series only. `wsum_err`: relative error of "
            "the weighted sum; `max_err` / `min_err`: error of the clustered peak / "
            "minimum relative to the series range; `dc_nrmse`: duration-curve error; "
            "`chr_nrmse`: error of the hourly profile rebuilt from the horizon → "
            "cluster map (what the storage balance sees)."
        ),
        code(
            "met = []\n"
            "for (c, v), r in red.items():\n"
            '    if "error" in r:\n'
            "        continue\n"
            "    df = rl.series_metrics(prof[c], r)\n"
            '    df["case"], df["variant"] = c, v\n'
            "    met.append(df)\n"
            "met = pd.concat(met, ignore_index=True)\n"
            'rl.summarize_metrics(met, ["case", "variant"])'
        ),
        code(
            "# SwissX by stage and by input file\n"
            'sx = met[met.case == "swissx"].copy()\n'
            'sx["file"] = sx.series.str.split("|").str[3].str.split("x").str[0]\n'
            'display(rl.summarize_metrics(sx, ["variant", "stage"]))'
        ),
        code(
            "fig, axes = plt.subplots(1, 4, figsize=(16, 3.5))\n"
            'for ax, col in zip(axes, ["wsum_err", "max_err", "dc_nrmse", "chr_nrmse"]):\n'
            '    d = met[~met.constant].assign(val=lambda x: x[col].abs())\n'
            '    d.pivot_table(index="case", columns="variant", values="val", aggfunc="mean").plot.bar(ax=ax, rot=0)\n'
            '    ax.set_title(f"mean |{col}|"); ax.set_xlabel("")\n'
            "plt.tight_layout()"
        ),
        md("## 3. Model results (demo, ms3)"),
        code(
            "cmp = []\n"
            'for c in ("demo", "ms3"):\n'
            "    for v in VARS:\n"
            "        r = red[(c, v)]\n"
            '        row = {"case": c, "variant": v}\n'
            '        if "error" in r:\n'
            '            row["error"] = r["error"]\n'
            "        else:\n"
            '            row.update(num_ts=r["num_ts"], **rl.solution_compare(full[c], r))\n'
            "        cmp.append(row)\n"
            "pd.DataFrame(cmp)"
        ),
        code(
            'for c in ("demo", "ms3"):\n'
            '    runs = {"M0": full[c], **{v: red[(c, v)] for v in VARS if "error" not in red[(c, v)]}}\n'
            '    print(f"== {c}: capacities"); display(rl.cap_table(runs))\n'
            "    ft = rl.flow_table(runs)\n"
            '    rel = ft.drop(columns="M0").div(ft["M0"].where(ft["M0"].abs() > 1e-9), axis=0) - 1\n'
            '    print(f"== {c}: weighted import/export/shedding totals, relative to M0"); display(rel)'
        ),
        *findings("E0"),
    ]
    return cells


def e1():
    cells = [
        md(
            "# E1 – Convergence with the number of clustered time steps\n\n"
            "Target K ∈ {24, 48, 96, 192, 384, 768, 1460, 2920}. Results are "
            "plotted against the *actual* number of clustered steps, since the "
            "target is raised to 2 × the number of series of the largest stage and "
            "extremes are added on top.\n\n"
            "- demo (1 stage): M1, M2 (M1b = M1 for one stage), solved.\n"
            "- ms3 (2 stages): M1, M1b, M2, solved.\n"
            "- swissx (4 stages): M1, M1b, M2, clustering only."
        ),
        code(SETUP),
        code(
            "K = [24, 48, 96, 192, 384, 768, 1460, 2920]\n"
            'VARS = {"demo": ["M1", "M2"], "ms3": ["M1", "M1b", "M2"], "swissx": ["M1", "M1b", "M2"]}\n'
            'MODE = {"demo": "rom", "ms3": "rom", "swissx": "cluster"}\n'
            'prof = {c: rl.run(c, "M0", "profiles") for c in VARS}\n'
            'full = {c: rl.run(c, "M0", "full") for c in ("demo", "ms3")}\n'
            "rows, met = [], []\n"
            "for c, vs in VARS.items():\n"
            "    for v in vs:\n"
            "        for k in K:\n"
            "            r = try_run(c, v, MODE[c], k)\n"
            '            row = {"case": c, "variant": v, "target": k}\n'
            '            if "error" in r:\n'
            '                row["error"] = r["error"]; rows.append(row); continue\n'
            '            row["num_ts"] = r["num_ts"]\n'
            '            row["secs_cluster"] = r["secs_cluster"]\n'
            '            st = rl.stage_summary(r, prof[c]["num_horizon_ts"])\n'
            '            row["phantom"] = int(st.phantom.sum())\n'
            '            if MODE[c] == "rom":\n'
            "                row.update(rl.solution_compare(full[c], r))\n"
            "            m = rl.series_metrics(prof[c], r)\n"
            "            m = m[~m.constant]\n"
            '            for col in ["wsum_err", "max_err", "min_err", "dc_nrmse", "chr_nrmse"]:\n'
            '                row[col] = m[col].abs().mean()\n'
            "            rows.append(row)\n"
            "res = pd.DataFrame(rows)\n"
            'print("full solve time [s]:", {c: round(full[c]["secs_solve"]) for c in full})\n'
            "res"
        ),
        md("## Model-level convergence (demo, ms3)"),
        code(
            'cols = ["obj_err", "cap_abs_diff_rel", "secs_solve"]\n'
            "fig, axes = plt.subplots(2, 3, figsize=(15, 7))\n"
            'for i, c in enumerate(["demo", "ms3"]):\n'
            "    for j, col in enumerate(cols):\n"
            "        ax = axes[i, j]\n"
            "        for v in VARS[c]:\n"
            '            d = res[(res.case == c) & (res.variant == v)].dropna(subset=["num_ts"])\n'
            '            y = d[col] * (100 if col != "secs_solve" else 1)\n'
            '            ax.plot(d.num_ts, y, marker="o", label=rl.LABELS[v])\n'
            '        if col == "secs_solve":\n'
            '            ax.axhline(full[c]["secs_solve"], color="k", ls="--", label="M0 full")\n'
            '        else:\n'
            '            ax.axhline(0, color="k", lw=0.8)\n'
            '        ax.set_xscale("log"); ax.set_xlabel("clustered time steps")\n'
            '        ax.set_title(f"{c}: {col}" + (" [%]" if col != "secs_solve" else " [s]"))\n'
            "axes[0, 0].legend(); plt.tight_layout()"
        ),
        md("## Input-level convergence (all cases)"),
        code(
            'cols = ["wsum_err", "max_err", "dc_nrmse", "chr_nrmse"]\n'
            "fig, axes = plt.subplots(3, 4, figsize=(17, 10))\n"
            'for i, c in enumerate(["demo", "ms3", "swissx"]):\n'
            "    for j, col in enumerate(cols):\n"
            "        ax = axes[i, j]\n"
            "        for v in VARS[c]:\n"
            '            d = res[(res.case == c) & (res.variant == v)].dropna(subset=["num_ts"])\n'
            '            ax.plot(d.num_ts, d[col], marker="o", label=rl.LABELS[v])\n'
            '        ax.set_xscale("log"); ax.set_title(f"{c}: mean |{col}|")\n'
            '        ax.set_xlabel("clustered time steps")\n'
            "axes[0, 0].legend(); plt.tight_layout()"
        ),
        *findings("E1"),
    ]
    return cells


def write(name, cells):
    nb = nbf.v4.new_notebook()
    nb.cells = cells
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    os.makedirs(NB_DIR, exist_ok=True)
    path = os.path.join(NB_DIR, f"{name}.ipynb")
    ExecutePreprocessor(timeout=3600, kernel_name="python3").preprocess(
        nb, {"metadata": {"path": NB_DIR}}
    )
    nbf.write(nb, path)
    print("wrote", path)


if __name__ == "__main__":
    write("E0_baseline", e0())
    write("E1_convergence", e1())
