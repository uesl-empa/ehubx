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

def try_run(*args):
    try:
        return rl.run(*args)
    except Exception as exc:  # failed runs are reported, not hidden
        return {"error": str(exc).strip().splitlines()[-1]}

print("Variants:", {k: v for k, v in rl.VARIANTS.items()})"""


def md(text):
    return nbf.v4.new_markdown_cell(text)


def code(text):
    return nbf.v4.new_code_cell(text)


def e0():
    cells = [
        md(
            "# E0 – Baseline: M0 vs M1, M1b, M2\n\n"
            "- **Goal:** Speed up optimization by grouping `8,760` hours into `~150–185` representative hours, and test three clustering versions against the full-year reference (**M0**).\n"
            "- **Methods compared:**\n\n"
            "| ID | Method | Key difference in plain terms |\n"
            "|---|---|---|\n"
            "| **M0** | Full year (reference) | No clustering — all `8,760` hours kept as ground truth. |\n"
            "| **M1** | Current `main` | Groups hours and tries to keep peaks, but drops peaks in some stages of multi-stage models and slightly drifts annual totals. |\n"
            "| **M1b** | Intermediate fix (PR #58) | Keeps peaks across all stages in multi-stage models, but annual totals still drift slightly. |\n"
            "| **M2** | Proposed fix (#57) | Protects each series' peak and minimum as its own step and averages each group's members — exact annual totals and exact peaks across all stages. |\n\n"
            "- **Test cases** (target: `150` steps for `demo`/`ms3`, `144` for `swissx`):\n"
            "  - **demo**: small 1-stage model (`examples/clustering_demo`), solved.\n"
            "  - **ms3**: synthetic 2-stage model (`models/ms3`), solved.\n"
            "  - **swissx**: 178 real 4-stage profiles, clustering quality only (not solved).\n"
            "- *Technical background (algorithm settings, commit IDs, exact differences, and metric definitions) is in the **Appendix** at the end.*"
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
            "## 1. Sanity check: clustering structure per stage\n\n"
            "- Checks that every stage has:\n"
            "  - the same number of clustered steps,\n"
            "  - `0` empty (\"phantom\") steps,\n"
            "  - weights summing to `8,760` h."
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
            'structure["case_stage"] = structure["case"] + "/" + structure["stage"]\n'
            "fig, axes = plt.subplots(1, 2, figsize=(13, 3.8))\n"
            'used_p = structure.pivot(index="case_stage", columns="variant", values="used")[VARS]\n'
            'used_p.plot.bar(ax=axes[0], rot=25)\n'
            'axes[0].set_title("Clustered steps used per stage"); axes[0].set_ylabel("clustered steps"); axes[0].set_xlabel("")\n'
            'axes[0].grid(axis="y", alpha=0.3)\n'
            'wsum_p = structure.pivot(index="case_stage", columns="variant", values="weight_sum")[VARS]\n'
            'wsum_p.plot.bar(ax=axes[1], rot=25, legend=False)\n'
            'axes[1].axhline(8760, color="k", ls="--", lw=1, label="8,760 h target")\n'
            'axes[1].set_title("Sum of weights per stage"); axes[1].set_ylabel("hours [h]"); axes[1].set_xlabel("")\n'
            'axes[1].grid(axis="y", alpha=0.3); axes[1].legend()\n'
            'fig.suptitle("Section 1 – Clustering structure per stage (sanity check)", y=1.03)\n'
            "plt.tight_layout()\n"
            'print(f"Total phantom steps: {int(structure[\'phantom\'].sum())} | Steps with weight != members: {int(structure[\'weight_ne_members\'].sum())}")'
        ),
        md(
            "**Summary (Section 1):**\n"
            "- All three methods produce identical step counts (`178` for `demo`/`ms3`, `185` for `swissx`), `0` phantom steps, and weights summing to `8,760` h.\n"
            "- Phantom steps (issue 2) do not trigger on these datasets (they require near-identical extreme hours)."
        ),
        md(
            "## 2. How well the clustered inputs match the full year\n\n"
            "- Errors on non-constant input series (`0` = exact match; formulas in the **Appendix**):\n"
            "  - `wsum_err`: annual totals\n"
            "  - `max_err` / `min_err`: peaks and minima\n"
            "  - `dc_nrmse`: sorted value distribution (duration curve)\n"
            "  - `chr_nrmse`: hour-by-hour match"
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
            "d = met[~met.constant].copy()\n"
            'cols = [("wsum_err", "Annual total error [%]"), ("max_err", "Peak error [% of range]"),\n'
            '        ("dc_nrmse", "Duration-curve error [%]"), ("chr_nrmse", "Hourly match error [%]")]\n'
            "fig, axes = plt.subplots(2, 4, figsize=(16, 6.5))\n"
            'for j, (col, title) in enumerate(cols):\n'
            '    for i, agg in enumerate(["mean", "max"]):\n'
            "        ax = axes[i, j]\n"
            '        pt = d.assign(val=lambda x: x[col].abs() * 100).pivot_table(\n'
            '            index="case", columns="variant", values="val", aggfunc=agg\n'
            "        )[VARS]\n"
            "        pt.plot.bar(ax=ax, rot=0, legend=(i == 0 and j == 0))\n"
            '        ax.set_title(f"{agg.title()} {title}"); ax.set_xlabel("")\n'
            '        ax.set_ylabel("error [%]"); ax.grid(axis="y", alpha=0.3)\n'
            'fig.suptitle("Section 2a – Input-level errors across cases (0 = exact match to full year)", y=1.02)\n'
            "plt.tight_layout()"
        ),
        code(
            'sx = d[d.case == "swissx"].copy()\n'
            "fig, axes = plt.subplots(1, 2, figsize=(12, 3.8))\n"
            'for ax, (col, title) in zip(axes, [("wsum_err", "Max annual total error [%]"), ("max_err", "Max peak error [% of range]")]):\n'
            '    pt = sx.assign(val=lambda x: x[col].abs() * 100).pivot_table(\n'
            '        index="stage", columns="variant", values="val", aggfunc="max"\n'
            "    )[VARS]\n"
            "    pt.plot.bar(ax=ax, rot=0)\n"
            '    ax.set_title(title); ax.set_xlabel(""); ax.set_ylabel("error [%]"); ax.grid(axis="y", alpha=0.3)\n'
            'fig.suptitle("Section 2b – SwissX worst-case errors by stage (shows M1 multi-stage peak loss)", y=1.03)\n'
            "plt.tight_layout()"
        ),
        md(
            "**Summary (Section 2):**\n"
            "- **Annual totals (`wsum_err`):** exact only in `M2` (`≤ 3e-16`), vs. `0.07–0.2 %` mean and up to `2.8 %` max in `M1`/`M1b` (`swissx` S4).\n"
            "- **Peaks (`max_err`):** `M1` loses multi-stage peaks (up to `41 %` in `ms3`, `52 %` in `swissx` S1/S4); `M1b` restores them (`≤ 1e-6`); `M2` is exact.\n"
            "- **Shape (`dc_nrmse`, `chr_nrmse`):** `M2` is `3–9 %` higher at this `K` because `M1` pulls near-peak hours into extreme clusters (better high-end shape, biased totals)."
        ),
        md(
            "## 3. Impact on optimization results (demo, ms3)\n\n"
            "- Compares solved outputs against the full-year reference (`M0`):\n"
            "  - total cost (`obj_err`),\n"
            "  - installed capacities (`cap_abs_diff_rel`),\n"
            "  - energy imports, exports, and load shedding."
        ),
        code(
            "cmp = []\n"
            'for c in ("demo", "ms3"):\n'
            "    for v in VARS:\n"
            "        r = red[(c, v)]\n"
            '        cmp.append({"case": c, "variant": v, **rl.solution_compare(full[c], r)})\n'
            "cmp_df = pd.DataFrame(cmp)\n"
            "fig, axes = plt.subplots(1, 2, figsize=(12, 3.8))\n"
            'obj_pt = cmp_df.assign(err=lambda x: x["obj_err"] * 100).pivot(index="case", columns="variant", values="err")[VARS]\n'
            "obj_pt.plot.bar(ax=axes[0], rot=0)\n"
            'axes[0].axhline(0, color="k", lw=0.8)\n'
            'axes[0].set_title("Total cost error vs. M0 [%]"); axes[0].set_ylabel("error [%]"); axes[0].set_xlabel("")\n'
            'axes[0].grid(axis="y", alpha=0.3)\n'
            "for container in axes[0].containers:\n"
            '    axes[0].bar_label(container, fmt="%.1f%%", fontsize=8, padding=2)\n'
            'time_rows = [{"case": c, "variant": "M0", "secs_solve": full[c]["secs_solve"]} for c in ("demo", "ms3")]\n'
            'time_df = pd.concat([pd.DataFrame(time_rows), cmp_df[["case", "variant", "secs_solve"]]], ignore_index=True)\n'
            'time_pt = time_df.pivot(index="case", columns="variant", values="secs_solve")[["M0"] + VARS]\n'
            "time_pt.plot.bar(ax=axes[1], rot=0)\n"
            'axes[1].set_title("Solver runtime [s]"); axes[1].set_ylabel("seconds [s]"); axes[1].set_xlabel("")\n'
            'axes[1].grid(axis="y", alpha=0.3)\n'
            'fig.suptitle("Section 3a – Optimization cost error and solve time vs. full year (M0)", y=1.03)\n'
            "plt.tight_layout()\n"
            'print(f"Capacity diff vs M0: {cmp_df[\'cap_abs_diff_rel\'].max():.1%} | Technologies flipped: {int(cmp_df[\'techs_flipped\'].max())} (all capacities fixed)")'
        ),
        code(
            "fig, axes = plt.subplots(1, 2, figsize=(14, 4.5))\n"
            'for ax, c in zip(axes, ("demo", "ms3")):\n'
            '    runs = {"M0": full[c], **{v: red[(c, v)] for v in VARS}}\n'
            "    ft = rl.flow_table(runs)\n"
            '    ft = ft[ft["M0"].abs() > 1e-9]\n'
            '    rel = (ft[VARS].div(ft["M0"], axis=0) - 1) * 100\n'
            "    rel.plot.barh(ax=ax)\n"
            '    ax.axvline(0, color="k", lw=0.8)\n'
            '    ax.set_title(f"{c}: annual energy flows vs. M0"); ax.set_xlabel("difference vs. M0 [%]")\n'
            '    ax.grid(axis="x", alpha=0.3)\n'
            'fig.suptitle("Section 3b – Energy flow differences vs. full year (M0) [%]", y=1.02)\n'
            "plt.tight_layout()"
        ),
        md(
            "**Summary (Section 3):**\n"
            "- **Cost objective error vs. `M0`:** `demo` `+5.8 %` (`M1`/`M1b`) → `+5.6 %` (`M2`); `ms3` `+6.5 %` (`M1`/`M1b`) → `+6.3 %` (`M2`).\n"
            "- **Energy flows:** demand-driven imports (`E5`, `E6`, `H2-E1`) are exact in `M2` vs. `0.3 %` off in `M1`; load shedding (`+3–4 %`) and `E2` import (`+1 %`) are high in all methods.\n"
            "- **Design:** capacities are fixed in `demo`/`ms3`, so capacity differences are `0` (a free-capacity model is needed)."
        ),
        md(
            "## Findings (E0)\n\n"
            "- **Key takeaway:**\n"
            "  - Differences *between* clustering methods are small (`≤ 0.3` percentage points in cost objective).\n"
            "  - The shared error across all three methods is much larger (`≈ 6 %`).\n"
            "  - The remaining gap comes from typical-hour ROM itself, not the bugs fixed in `#57` (see **E1**).\n"
            "- **Clustering structure:**\n"
            "  - Same step counts across all methods: `178` (`demo`, `ms3`) and `185` (`swissx`).\n"
            "  - Every step has member hours (`0` phantom steps) and weights sum to `8,760` h.\n"
            "  - Phantom steps (issue 2) do not trigger on these datasets; they require near-identical extreme hours (covered by unit tests).\n"
            "- **Annual totals (`wsum_err`):**\n"
            "  - `M2`: exact (`≤ 3e-16`) for every series.\n"
            "  - `M1` / `M1b`: mean error `0.07–0.2 %`; max `1 %` (`demo`/`ms3`) and up to **`2.8 %`** (`M1b`, `swissx` S4).\n"
            "- **Peaks & minima (`max_err`, `min_err`):**\n"
            "  - `M1` (`main`) loses peaks/minima on any stage that initially gets fewer clusters than the largest stage (it re-clusters those stages with extreme protection turned off to equalize step counts):\n"
            "    - `ms3`: clustered peak up to `41 %` of range below true peak.\n"
            "    - `swissx`: up to `52 %` below true peak (stages S1 and S4).\n"
            "  - `M1b`: fixes multi-stage peaks to `≤ 1e-6` (from `tsam` rounding).\n"
            "  - `M2`: preserves peaks and minima **exactly**.\n"
            "  - Single-stage `demo`: all methods keep peaks.\n"
            "- **Profile shape (`dc_nrmse`, `chr_nrmse`):**\n"
            "  - `M2` is `3–9 %` *higher* than `M1` at this target `K`.\n"
            "  - Why: `M1` pulls near-peak hours into extreme clusters (better high-end shape, biased totals), whereas `M2` keeps totals exact and assigns near-peak hours to regular clusters.\n"
            "  - This gap closes as `K` grows (see **E1**).\n"
            "- **Optimization results (`demo`, `ms3`):**\n"
            "  - Cost objective vs. full horizon (`M0`):\n"
            "    - `demo`: `+5.8 %` (`M1`, `M1b`) → `+5.6 %` (`M2`).\n"
            "    - `ms3`: `+6.5 %` (`M1`, `M1b`) → `+6.3 %` (`M2`).\n"
            "  - Energy flows:\n"
            "    - Demand-driven imports (`E5`, `E6`, `H2-E1`): exact in `M2`, off by `0.3 %` in `M1`.\n"
            "    - Load shedding (`+3–4 %`) and `E2` import (`+1 %`): elevated across all methods.\n"
            "  - **Limitation:** all capacities in `demo`/`ms3` are fixed, so design differences cannot appear here — a free-capacity model is needed next."
        ),
        md(
            "## Appendix: Technical Background\n\n"
            "### Shared ROM Setup\n\n"
            "- **Reference (`M0`):** Unclustered full horizon (`8,760` h).\n"
            "- **Clustered methods (`M1`, `M1b`, `M2`):**\n"
            "  - Algorithm: `tsam` 1-hour typical periods (`hoursPerPeriod=1`), hierarchical Ward clustering (`rescaleClusterPeriods=False`).\n"
            "  - Weights & storage:\n"
            "    - Each horizon hour maps to one clustered step weighted by member count.\n"
            "    - Storage state-of-charge remains tracked across all `8,760` h via the horizon → cluster map.\n"
            "  - Size & stage rules:\n"
            "    - Targets below `2 × max(series per stage)` are raised to that floor.\n"
            "    - All stages in a multi-stage model share one common cluster count.\n"
            "  - **E0 targets:** `150` (`demo`, `ms3`), `144` (`swissx`, matching thesis runs).\n\n"
            "### Detailed Method Comparison\n\n"
            "| ID | Code | Extreme periods (max/min) | Multi-stage sync | Cluster values | Key difference / issue |\n"
            "|---|---|---|---|---|---|\n"
            "| **M0** | `bd1a0c89` (branch) | None (`8,760` h) | — | Exact hourly data | Reference ground truth. |\n"
            "| **M1** | `d436c9b7` (`main`) | `tsam` `new_cluster_center` (near-peak hours can join) | Re-cluster shorter stages to `num_ts_max` with `extremePeriodMethod=\"None\"` | `tsam` `durationRepresentation` + rounding | Re-clustered stages lose extremes; weighted sums drift; phantom steps possible. |\n"
            "| **M1b** | `f69e03d5` (PR #58) | Same `tsam` `new_cluster_center` | Re-cluster shorter stages with `num_ts + (num_ts_max - num_ts_s)` regular clusters, keeping `new_cluster_center` | Same `durationRepresentation` + rounding | Keeps multi-stage extremes (`= M1` on 1 stage); weighted-sum drift, phantom steps, slower 2-pass clustering. |\n"
            "| **M2** | `bd1a0c89` (`57-rom-extreme-periods`) | Hand-picked per stage: each non-constant series' max & min extracted as a 1-hour cluster before `tsam` | Single pass to common `num_ts_reg + max_s(len(ext_s))` (shorter stages get more regular clusters) | **Exact mean** of member hours | Exact weighted sums, exact peaks/minima, no phantom steps, faster single-pass clustering. |\n\n"
            "- **What each comparison isolates:**\n"
            "  - `M1 → M1b`: Effect of keeping extreme periods during multi-stage sync (no change for 1-stage `demo`).\n"
            "  - `M1/M1b → M2`: Effect of explicit 1-hour extremes + exact member means + single-pass sync.\n"
            "  - `M1/M1b/M2 vs M0`: Baseline error of typical-hour ROM itself vs. full `8,760` h.\n\n"
            "### Cases & Metric Definitions\n\n"
            "- **swissx setup note:**\n"
            "  - All `178` profiles enter as demand series of a pseudo system so clustering sees the same matrix as the full model.\n"
            "  - Not solved (requires the wind module and hours of Gurobi runtime).\n"
            "- **Structure metrics** (`stage_summary` in `scripts/romlab.py`):\n"
            "  - `used`: clustered steps with `≥ 1` member hour.\n"
            "  - `phantom`: clustered steps with `0` member hours (issue 2).\n"
            "  - `weight_ne_members`: steps whose weight differs from their member count.\n"
            "- **Input metrics** (`series_metrics` in `scripts/romlab.py`, non-constant series only; let $x$ = full hourly series, $r = \\max(x) - \\min(x)$, $v_k$ = clustered values, $w_k$ = cluster weights, and $\\hat{x}_t = v_{c(t)}$ = rebuilt hourly series):\n"
            "  - `wsum_err` (annual totals): $(\\sum_k w_k v_k - \\sum_t x_t) / |\\sum_t x_t|$ (unnormalized $\\sum_k w_k v_k - \\sum_t x_t$ when $\\sum_t x_t = 0$).\n"
            "  - `max_err` / `min_err` (peaks and minima): $(\\max_{w_k > 0} v_k - \\max x) / r$ and $(\\min_{w_k > 0} v_k - \\min x) / r$.\n"
            "  - `dc_nrmse` (duration curve): $\\mathrm{RMSE}(\\text{sort}_{\\downarrow}(\\text{repeat}(v_k, \\text{round}(w_k))),\\, \\text{sort}_{\\downarrow}(x)) / r$.\n"
            "  - `chr_nrmse` (hour-by-hour match): $\\mathrm{RMSE}(\\hat{x}, x) / r$, measuring what the storage balance sees.\n"
            "- **Model metrics** (`solution_compare` in `scripts/romlab.py`):\n"
            "  - `obj_err`: relative objective cost error.\n"
            "  - `cap_abs_diff_rel`: relative total capacity difference.\n"
            "  - `techs_flipped`: count of built/unbuilt technology changes.\n"
            "  - `secs_solve`: solver runtime in seconds."
        ),
    ]
    return cells


def e1():
    cells = [
        md(
            "# E1 – Convergence with the number of clustered time steps\n\n"
            "- **Goal:** Test how fast accuracy and runtime improve as clustered steps `K` increase toward the full year (`8,760` h).\n"
            "- **Sweep:**\n"
            "  - Target `K` ∈ `{24, 48, 96, 192, 384, 768, 1460, 2920}`.\n"
            "  - Plots use *actual* clustered steps (targets are raised to `2 × max(series)` and extremes are added on top).\n"
            "- **Test cases:**\n"
            "  - **demo** (1 stage): `M1`, `M2` (`M1b` = `M1` for 1 stage), solved.\n"
            "  - **ms3** (2 stages): `M1`, `M1b`, `M2`, solved.\n"
            "  - **swissx** (4 stages): `M1`, `M1b`, `M2`, clustering quality only.\n"
            "- *Method & metric definitions are in the **Appendix** of `E0_baseline.ipynb`.*"
        ),
        code(SETUP),
        code(
            "K = [24, 48, 96, 192, 384, 768, 1460, 2920]\n"
            'VARS = {"demo": ["M1", "M2"], "ms3": ["M1", "M1b", "M2"], "swissx": ["M1", "M1b", "M2"]}\n'
            'COLORS = {"M1": "C0", "M1b": "C1", "M2": "C2"}\n'
            'MODE = {"demo": "rom", "ms3": "rom", "swissx": "cluster"}\n'
            'prof = {c: rl.run(c, "M0", "profiles") for c in VARS}\n'
            'full = {c: rl.run(c, "M0", "full") for c in ("demo", "ms3")}\n'
            "rows = []\n"
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
            'print(f"Loaded {len(res)} runs ({int(res[\'num_ts\'].isna().sum())} failed); full solve time [s]: " + str({c: round(full[c]["secs_solve"]) for c in full}))'
        ),
        md(
            "## 1. Model-level convergence (demo, ms3)\n\n"
            "- **Metrics:** objective error (`obj_err`), relative capacity difference (`cap_abs_diff_rel`), and solve time (`secs_solve`).\n"
            "- **Axes:** log scale for actual clustered steps; dashed/solid reference lines show `M0` full-year value (`0 %` error or full solve time)."
        ),
        code(
            'cols = [("obj_err", "Cost error vs. M0 [%]"), ("cap_abs_diff_rel", "Capacity diff vs. M0 [%]"), ("secs_solve", "Solve time [s]")]\n'
            "fig, axes = plt.subplots(2, 3, figsize=(15, 7))\n"
            'for i, c in enumerate(["demo", "ms3"]):\n'
            "    for j, (col, title) in enumerate(cols):\n"
            "        ax = axes[i, j]\n"
            "        for v in VARS[c]:\n"
            '            d = res[(res.case == c) & (res.variant == v)].dropna(subset=["num_ts"])\n'
            '            y = d[col] * (100 if col != "secs_solve" else 1)\n'
            '            ax.plot(d.num_ts, y, marker="o", color=COLORS[v], label=rl.LABELS[v])\n'
            '        if col == "secs_solve":\n'
            '            ax.axhline(full[c]["secs_solve"], color="k", ls="--", label="M0 full")\n'
            "        else:\n"
            '            ax.axhline(0, color="k", lw=0.8)\n'
            '        ax.set_xscale("log"); ax.set_xlabel("clustered time steps")\n'
            '        ax.set_ylabel("%" if col != "secs_solve" else "seconds [s]")\n'
            '        ax.set_title(f"{c}: {title}"); ax.grid(True, alpha=0.3)\n'
            "handles, labels = axes[1, 2].get_legend_handles_labels()\n"
            'fig.legend(handles, labels, loc="upper center", ncol=4, bbox_to_anchor=(0.5, 0.98))\n'
            'fig.suptitle("Section 1 – Model-level convergence vs. actual clustered steps (log scale)", y=1.03)\n'
            'plt.tight_layout(rect=[0, 0, 1, 0.93])'
        ),
        md(
            "**Summary (Section 1):**\n"
            "- **Slow cost convergence:** `demo` `M2` drops only from `+5.7 %` (`60` steps) to `+3.0 %` (`2,948` steps, a third of the year); `ms3` goes `+6.9 %` → `+3.1 %`.\n"
            "- **Method gap:** `M2` beats `M1` at small `K` (`5.7 %` vs. `6.7 %` on `demo`, `6.9 %` vs. `7.6 %` on `ms3`), then all three converge similarly.\n"
            "- **Solve time:** ROM gives a modest `2–4×` speed-up (`19–65 s` vs. `76 s` on `demo`; `35–180 s` vs. `144 s` on `ms3`)."
        ),
        md(
            "## 2. Input-level convergence (all cases)\n\n"
            "- **Metrics:** mean absolute errors across non-constant series (`wsum_err`, `max_err`, `dc_nrmse`, `chr_nrmse`; `0` = exact match) plus clustering runtime (`secs_cluster`).\n"
            "- **X-axis:** log scale for actual clustered time steps."
        ),
        code(
            'cols = [("wsum_err", "Annual total error [%]"), ("max_err", "Peak error [% of range]"),\n'
            '        ("dc_nrmse", "Duration-curve error [%]"), ("chr_nrmse", "Hourly match error [%]")]\n'
            "fig, axes = plt.subplots(3, 4, figsize=(17, 10))\n"
            'for i, c in enumerate(["demo", "ms3", "swissx"]):\n'
            "    for j, (col, title) in enumerate(cols):\n"
            "        ax = axes[i, j]\n"
            "        for v in VARS[c]:\n"
            '            d = res[(res.case == c) & (res.variant == v)].dropna(subset=["num_ts"])\n'
            '            ax.plot(d.num_ts, d[col] * 100, marker="o", color=COLORS[v], label=rl.LABELS[v])\n'
            '        ax.set_xscale("log"); ax.set_title(f"{c}: mean {title}")\n'
            '        ax.set_xlabel("clustered time steps"); ax.set_ylabel("error [%]"); ax.grid(True, alpha=0.3)\n'
            "handles, labels = axes[1, 0].get_legend_handles_labels()\n"
            'fig.legend(handles, labels, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 0.99))\n'
            'fig.suptitle("Section 2a – Input-level errors vs. actual clustered steps (log scale; 0 = exact)", y=1.03)\n'
            'plt.tight_layout(rect=[0, 0, 1, 0.95])'
        ),
        code(
            "fig, axes = plt.subplots(1, 3, figsize=(15, 3.8))\n"
            'for ax, c in zip(axes, ["demo", "ms3", "swissx"]):\n'
            "    for v in VARS[c]:\n"
            '        d = res[(res.case == c) & (res.variant == v)].dropna(subset=["num_ts"])\n'
            '        ax.plot(d.num_ts, d["secs_cluster"], marker="o", color=COLORS[v], label=rl.LABELS[v])\n'
            '    ax.set_xscale("log"); ax.set_title(f"{c}: clustering time")\n'
            '    ax.set_xlabel("clustered time steps"); ax.set_ylabel("seconds [s]"); ax.grid(True, alpha=0.3)\n'
            "handles, labels = axes[1].get_legend_handles_labels()\n"
            'fig.legend(handles, labels, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 0.95))\n'
            'fig.suptitle("Section 2b – Clustering runtime [s] vs. actual clustered steps", y=1.05)\n'
            'plt.tight_layout(rect=[0, 0, 1, 0.87])'
        ),
        md(
            "**Summary (Section 2):**\n"
            "- **Fast vs. slow input metrics:** `dc_nrmse` falls quickly (`0.14` → `0.02`), while `chr_nrmse` stays high (`0.23` → `0.10`), pointing to time/storage coupling as the main error source.\n"
            "- **Method comparison:** `M2` keeps exact totals and peaks at all `K` and matches `M1` `dc_nrmse` from `~400` steps onward, while `M1` still loses up to `52 %` of peak range (`8 %` on `swissx` at `1,500` steps).\n"
            "- **Clustering speed:** `M2` is much faster (`44–81 s` vs. `210–2,300 s` on `swissx`; `7–12 s` vs. `23–143 s` on `demo`)."
        ),
        md(
            "## Findings (E1)\n\n"
            "- **Key takeaway:**\n"
            "  - Objective error converges slowly as `K` grows, even though input profile errors drop quickly.\n"
            "  - The bottleneck is how typical-hour ROM couples time and storage, not profile accuracy.\n"
            "- **Actual vs. target step count:**\n"
            "  - Actual steps often exceed target `K` because of the `2 × max(series)` floor plus extreme steps:\n"
            "    - `demo` / `ms3`: target `24` → `60` steps (`2 × 16` series + `28` extremes).\n"
            "    - `swissx`: targets `24` and `48` both → `133` steps (`2 × 46` series + `41` extremes).\n"
            "  - Below `~100` steps, the `2 × series` rule dominates.\n"
            "- **Slow objective convergence:**\n"
            "  - Cost error vs. full year (`M2`):\n"
            "    - `demo`: `+5.7 %` (`60`) → `+5.5 %` (`220`) → `+4.5 %` (`796`) → `+3.8 %` (`1,488`) → **`+3.0 %`** (`2,948`, one-third of a year).\n"
            "    - `ms3`: `+6.9 %` → `+3.1 %` over the same sweep.\n"
            "  - Input errors drop much faster:\n"
            "    - `M2` weighted totals: exact at every `K`.\n"
            "    - Duration-curve error (`dc_nrmse`): `0.14` → `0.02`.\n"
            "  - **Likely cause (time/storage coupling):**\n"
            "    - All hours in a cluster share one set of operational dispatch variables.\n"
            "    - In `stor_tech_model.py` (`_con_stor_tech_charging_dynamic`), storage energy level tracks all `8,760` horizon hours, while charging/discharging flows are indexed by clustered step.\n"
            "    - Storage must therefore charge/discharge identically across hours scattered over the year, restricting operation and raising cost.\n"
            "    - Slow decay of chronological error `chr_nrmse` (`0.23` → `0.10`) points the same way; share of error to be quantified in **E7**.\n"
            "    - Chronology-preserving methods (**M3** typical days, **M4** downsampling) may behave very differently.\n"
            "- **Methods compared (`M1`, `M1b`, `M2`):**\n"
            "  - All three converge similarly overall, with `M2` consistently cleaner:\n"
            "    - Lower small-`K` cost error: `5.7 %` vs. `6.7 %` (`demo` at `60` steps); `6.9 %` vs. `7.6 %` (`ms3`).\n"
            "    - Exact annual totals and exact peaks/minima at every `K`.\n"
            "    - Duration-curve error slightly higher at small `K`, equal from `~400` steps onward.\n"
            "  - `M1` still loses up to `52 %` of peak range in multi-stage models (even `8 %` on `swissx` at `1,500` steps).\n"
            "- **Runtime:**\n"
            "  - **Clustering time (`M2` much faster):**\n"
            "    - `swissx`: `44–81 s` (`M2`) vs. `210–2,300 s` (`M1`/`M1b`, due to `tsam` extreme handling and re-clustering).\n"
            "    - `demo`: `7–12 s` (`M2`) vs. `23–143 s` (`M1`/`M1b`).\n"
            "  - **Solve time (indicative, measured with 6 runs in parallel):**\n"
            "    - Full horizon (`M0`): `76 s` (`demo`), `144 s` (`ms3`).\n"
            "    - ROM: `19–65 s` (`demo`), `35–180 s` (`ms3`) — only `2–4×` speed-up on these small models.\n"
            "- **Next steps:**\n"
            "  - Prioritize **E7** (storage/time coupling) and **M3**/**M4** (chronology-preserving methods) over further tuning of typical-hour clustering (**E2**, **E3**).\n"
            "  - Add a test model with **free capacities** to evaluate design differences."
        ),
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
