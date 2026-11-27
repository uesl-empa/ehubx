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


def e1b():
    cells = [
        md(
            "# E1b – Free-capacity sizing & design regret\n\n"
            "- **Goal:** Test whether ROM picks the right technology sizes when capacities are free to vary (`demo`/`ms3` had fixed sizes).\n"
            "- **Test model (`pv_bat`):**\n"
            "  - 1 stage, `8,760` h, 5 technologies with free capacities: **PV**, **Battery (`Bat`)**, **Heat Pump (`HP`)**, **Gas Boiler (`Boiler`)**, and **Thermal Storage (`TES`)**.\n"
            "  - Includes an expensive emergency heat backup (`5.0 CHF/kWh`, `0` used in `M0`) to measure peak shortfall if ROM under-sizes heating.\n"
            "- **Design regret:** Fix the capacities chosen by ROM (`M1`, `M2`) and re-solve full `8,760` h operation — how much more expensive is the ROM design than the true full-year optimum (`M0`)?\n"
            "- *Sweep:* `K` ∈ `{48, 96, 192, 384, 768, 1460}`."
        ),
        code(SETUP),
        code(
            "K_EXP = [48, 96, 192, 384, 768, 1460]\n"
            'VARS = ["M1", "M2"]\n'
            'COLORS = {"M1": "C0", "M2": "C2"}\n'
            'TECHS = ["PV", "Bat", "HP", "Boiler", "TES"]\n'
            'full = rl.run("pv_bat", "M0", "full")\n'
            'prof = rl.run("pv_bat", "M0", "profiles")\n'
            'tot_heat = sum(prof["series"]["TimeSeriesKind.DEMAND|S1|H1|Heat"]["values"])\n'
            "rows = []\n"
            "for v in VARS:\n"
            "    for k in K_EXP:\n"
            '        r = rl.run("pv_bat", v, "rom", k)\n'
            '        rg = rl.run("pv_bat", v, "regret", k)\n'
            "        sc = rl.solution_compare(full, r)\n"
            '        row = {"variant": v, "target": k, "num_ts": r["num_ts"],\n'
            '               "obj_err_pct": sc["obj_err"] * 100,\n'
            '               "regret_pct": (rg["objective"] - full["objective"]) / full["objective"] * 100,\n'
            '               "cap_diff_pct": sc["cap_abs_diff_rel"] * 100,\n'
            '               "heat_bak_pct": rg["flows"].get("V_Imp[S1,H1,Heat]", 0.0) / tot_heat * 100,\n'
            '               "secs_solve": r["secs_solve"]}\n'
            "        for t in TECHS:\n"
            '            row[t] = r["caps"].get(f"S1,H1,{t}", 0.0)\n'
            "        rows.append(row)\n"
            "df = pd.DataFrame(rows)\n"
            'print("M0 full cost:", round(full["objective"], 1), "| M0 caps:", {t: round(full["caps"].get(f"S1,H1,{t}", 0.0), 1) for t in TECHS})'
        ),
        md(
            "## 1. Technology sizing accuracy (`PV`, `Bat`, `HP`, `Boiler`, `TES`)\n\n"
            "- **Left (top-to-bottom / panels):** Installed capacity relative to `M0` (`1.0` = exact match) across `K`, plus absolute capacities at `K=192`.\n"
            "- **Check:** Does `M2` avoid the under-sizing traps seen at small `K`?"
        ),
        code(
            "fig, axes = plt.subplots(2, 3, figsize=(15, 7.5))\n"
            "for idx, t in enumerate(TECHS):\n"
            "    ax = axes[idx // 3, idx % 3]\n"
            '    m0_val = full["caps"].get(f"S1,H1,{t}", 0.0)\n'
            "    for v in VARS:\n"
            "        d = df[df.variant == v]\n"
            '        ax.plot(d.num_ts, d[t] / m0_val, marker="o", color=COLORS[v], label=rl.LABELS[v])\n'
            '    ax.axhline(1.0, color="k", ls="--", lw=1, label="M0 full (= 1.0)")\n'
            '    ax.set_xscale("log"); ax.set_ylim(0, 1.45)\n'
            '    ax.set_title(f"{t} capacity / M0 (M0 = {m0_val:.0f})"); ax.set_xlabel("clustered steps")\n'
            '    ax.set_ylabel("ratio to M0"); ax.grid(True, alpha=0.3)\n'
            "ax = axes[1, 2]\n"
            "for v in VARS:\n"
            "    d = df[df.variant == v]\n"
            '    ax.plot(d.num_ts, d.cap_diff_pct, marker="o", color=COLORS[v], label=rl.LABELS[v])\n'
            'ax.axhline(0, color="k", lw=0.8); ax.set_xscale("log")\n'
            'ax.set_title("Total capacity difference vs. M0 [%]"); ax.set_xlabel("clustered steps")\n'
            'ax.set_ylabel("error [%]"); ax.grid(True, alpha=0.3)\n'
            "handles, labels = axes[0, 0].get_legend_handles_labels()\n"
            'fig.legend(handles, labels, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 0.99))\n'
            'fig.suptitle("Section 1 – Installed capacities vs. full-year optimum (M0)", y=1.03)\n'
            "plt.tight_layout(rect=[0, 0, 1, 0.94])"
        ),
        md(
            "**Summary (Section 1):**\n"
            "- At the smallest target (`K=48`, `58` steps), both methods under-build battery (`M2`: `202` kWh, `M1`: `41` kWh vs. `516` kWh in `M0`) and `PV` (`cap_diff`: `33.4 %` in `M2`, `47.9 %` in `M1`).\n"
            "- From `K=96` (`106` steps) onward, both recover the full 5-technology mix within `2–10 %` total capacity difference (`M2` `K=96`: `cap_diff = 2.3 %`).\n"
            "- `M2` slightly under-sizes `Boiler` (`56.5–56.8` kW vs. `58.9` kW in `M0` at `K=96–192`), whereas `M1` slightly over-sizes it (`62.0–65.5` kW)."
        ),
        md(
            "## 2. Predicted cost error vs. true Design Regret\n\n"
            "- **ROM cost error:** how far ROM's *own* objective sits from `M0`.\n"
            "- **Design Regret:** extra cost when ROM's chosen capacities are operated over the real `8,760` h year.\n"
            "- **Emergency backup heat (% of annual demand):** share of total heat demand (`202.1 MWh/yr`) served by expensive emergency backup (`5.0 CHF/kWh`) during cold-snap peaks."
        ),
        code(
            "fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))\n"
            "for v in VARS:\n"
            "    d = df[df.variant == v]\n"
            '    axes[0].plot(d.num_ts, d.obj_err_pct, marker="o", color=COLORS[v], label=rl.LABELS[v])\n'
            '    axes[1].plot(d.num_ts, d.regret_pct, marker="o", color=COLORS[v], label=rl.LABELS[v])\n'
            '    axes[2].plot(d.num_ts, d.heat_bak_pct, marker="o", color=COLORS[v], label=rl.LABELS[v])\n'
            'axes[0].axhline(0, color="k", lw=0.8); axes[0].set_xscale("log"); axes[0].set_title("ROM predicted cost error [%]"); axes[0].set_ylabel("error [%]")\n'
            'axes[1].axhline(0, color="k", lw=0.8); axes[1].set_xscale("log"); axes[1].set_title("True Design Regret (8,760 h re-solve) [%]"); axes[1].set_ylabel("regret [%]")\n'
            'axes[2].axhline(0, color="k", lw=0.8); axes[2].set_xscale("log"); axes[2].set_title("Emergency backup heat [% of annual demand]"); axes[2].set_ylabel("% of annual heat demand")\n'
            'for ax in axes:\n    ax.set_xlabel("clustered steps"); ax.grid(True, alpha=0.3)\n'
            "handles, labels = axes[0].get_legend_handles_labels()\n"
            'fig.legend(handles, labels, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 0.96))\n'
            'fig.suptitle("Section 2 – ROM predicted cost error vs. true Design Regret", y=1.04)\n'
            "plt.tight_layout(rect=[0, 0, 1, 0.88])"
        ),
        md(
            "**Summary (Section 2):**\n"
            "- **Crucial gap:** ROM's predicted cost error looks large (`+12.1 %` at `K=96`, `+9.5 %` at `K=192`), yet true **Design Regret is only `0.15–1.25 %`** for `M2` from `K=96` onward.\n"
            "- **Relative backup heat is tiny (`≤ 0.11 %`), even in `M2`:** `0.11 %` (`K=48`), `0.05–0.08 %` (`K=96–192`), `0.04 %` (`K=384`), down to **`0.006 %`** at `K=1460` (better than `M1`'s `0.012 %`). Because emergency heat is priced at `5.0 CHF/kWh` (~40× normal heat cost), even `0.08 %` unmet heat adds `~0.8–1.2 %` to annual cost.\n"
            "- **Why `M2` uses more backup heat than `M1` at small `K` (`48–384`):**\n"
            "  - **`M2` (1-hour extreme + exact means):** locks only the single `131.4 kW` peak hour as its own cluster (`weight = 1`) and averages surrounding cold-snap hours (`122–127 kW`) down into regular clusters (`108–115 kW`). Since `TES` easily bridges one isolated peak hour, `M2` sizes `HP + Boiler` `3–6 kW` below `M0` (`107.2–110.5` vs. `113.5 kW`), leaving a small multi-hour cold-snap shortfall on the real year.\n"
            "  - **`M1` (`new_cluster_center`):** pulls `5–12` near-peak hours into the `131.4 kW` peak cluster at `K=48–96`, exaggerating peak duration and accidentally **over-sizing `Boiler`** (`62–75 kW` vs. `58.9 kW` in `M0`) — masking shortfall at the cost of over-sizing and biased totals."
        ),
        md(
            "## Findings (E1b)\n\n"
            "- **Key takeaway:**\n"
            "  - Even when ROM's predicted cost error is `+9.5 %` to `+12.1 %` (`K=96–192`), **`M2` picks near-optimal investment sizes** with only **`0.15–1.25 %` true Design Regret**.\n"
            "  - Extreme-hour protection prevents catastrophic under-sizing once `K ≥ 96` (`~106` steps); at `K=48` (`58` steps), battery capacity collapses (`-61 %` in `M2`, `-92 %` in `M1`) and regret jumps to `6.3–12.1 %`.\n"
            "- **Why predicted cost error ≠ Design Regret:**\n"
            "  - Typical-hour clustering makes storage look artificially restricted inside the ROM solve (inflating ROM operating cost), while still preserving the peak and price spread signals needed to size `PV`, `Bat`, `HP`, `Boiler`, and `TES` accurately.\n"
            "- **Why `M2` shows slightly higher backup heat (`0.04–0.08 %`) at `K=96–384`:**\n"
            "  - `M2` isolates only the single highest hour (`131.4 kW`, `weight = 1`), while nearby cold-snap hours (`122–127 kW`) get averaged into regular clusters (`108–115 kW`). `TES` covers the single isolated peak hour in ROM, so `HP + Boiler` is sized `3–6 kW` smaller (`107.2–110.5` vs. `113.5 kW` in `M0`).\n"
            "  - By contrast, `M1` groups `5–12` near-peak hours into the `131.4 kW` peak cluster, accidentally over-sizing `Boiler` (`62–75 kW`) and hiding the shortfall until `K ≥ 768` — where `M2` resolves the cold-snap plateau and beats `M1` on both backup heat (`0.006 %` vs. `0.012 %`) and regret (`0.15 %` vs. `0.21 %`).\n"
            "- **Caveat — `M2` does not have lower regret than `M1` at moderate `K`:**\n"
            "  - At `K=96–384`, `M1` regret is `0.07–0.35 %` vs. `0.69–1.25 %` for `M2`; `M2` is better only at `K=48` and `K ≥ 768`.\n"
            "  - The gap comes almost entirely from emergency heat priced at `5.0 CHF/kWh`, so the `M1`/`M2` ranking depends on that penalty. With backup heat at `1.0 CHF/kWh` (E1c, model `pv_bat_bak1`; same `M0` optimum), `M2` regret drops to `0.11–0.22 %` at `K=96–384` vs. `0.03–0.12 %` for `M1`, so the two are close.\n"
            "  - The case for `M2` (#57) is correctness (exact totals, peaks kept in all stages, no crashes), not better sizing. Protecting the *duration* of peaks (near-peak hours or extreme days), not only the single peak hour, is the likely fix for the `M2` shortfall.\n"
            "  - All sizing results come from one synthetic model (`pv_bat`, seed 42)."
        ),
    ]
    return cells


def e7():
    cells = [
        md(
            "# E7 – Storage & time-coupling diagnosis\n\n"
            "- **Hypothesis:** In typical-hour clustering (`M2`), storage energy (`SOC`) is tracked across all `8,760` hours, while charging/discharging flows share one variable per cluster — locking hours scattered across the year to identical dispatch.\n"
            "- **Ablation test (`M2`, Sections 1–2):** Compare two model pairs **with vs. without storage**:\n"
            "  - `demo` (has EBM fleet storage `X2`) vs. `demo_nostor` (`X2` removed).\n"
            "  - `pv_bat` (has `Bat` + `TES`) vs. `pv_bat_nostor` (`Bat` and `TES` removed).\n"
            "- **Storage operation check (Sections 3–4):** Compare **`M2` (typical hours), `M3` (typical days), and `M4` (downsampling)** against `M0` on `pv_bat`:\n"
            "  - Hourly `SOC` trajectories (`Bat` & `TES` in winter and summer at `K=192`).\n"
            "  - Annual storage throughput, equivalent full cycles, and hourly `SOC` correlation across `K`."
        ),
        code(SETUP),
        code(
            "K_EXP = [48, 96, 192, 384, 768, 1460]\n"
            'PAIRS = [("demo", "demo_nostor"), ("pv_bat", "pv_bat_nostor")]\n'
            'full = {c: rl.run(c, "M0", "full") for pair in PAIRS for c in pair}\n'
            "rows = []\n"
            "for pair in PAIRS:\n"
            "    for c in pair:\n"
            "        for k in K_EXP:\n"
            '            r = rl.run(c, "M2", "rom", k)\n'
            "            sc = rl.solution_compare(full[c], r)\n"
            '            row = {"case": c, "target": k, "num_ts": r["num_ts"],\n'
            '                   "obj_err_pct": sc["obj_err"] * 100,\n'
            '                   "cap_diff_pct": sc["cap_abs_diff_rel"] * 100}\n'
            '            if c.startswith("pv_bat"):\n'
            '                rg = rl.run(c, "M2", "regret", k)\n'
            '                row["regret_pct"] = (rg["objective"] - full[c]["objective"]) / full[c]["objective"] * 100\n'
            "            rows.append(row)\n"
            "df = pd.DataFrame(rows)\n"
            'print("Loaded", len(df), "M2 storage-ablation runs")'
        ),
        md(
            "## 1. Ablation: `demo` vs. `demo_nostor` (removing EBM storage)\n\n"
            "- Compares `M2` objective error vs. `M0` as clustered steps grow."
        ),
        code(
            "fig, ax = plt.subplots(figsize=(7.5, 4))\n"
            'for c, col, lbl in [("demo", "C2", "demo (with EBM storage X2)"),\n'
            '                    ("demo_nostor", "C0", "demo_nostor (no storage)")]:\n'
            "    d = df[df.case == c]\n"
            '    ax.plot(d.num_ts, d.obj_err_pct, marker="o", color=col, label=lbl)\n'
            'ax.axhline(0, color="k", lw=0.8); ax.set_xscale("log")\n'
            'ax.set_xlabel("clustered steps"); ax.set_ylabel("cost error vs. M0 [%]")\n'
            'ax.set_title("Section 1 – Effect of removing EBM storage on demo (M2)")\n'
            "ax.grid(True, alpha=0.3); ax.legend(); plt.tight_layout()"
        ),
        md(
            "**Summary (Section 1):**\n"
            "- Removing EBM storage `X2` eliminates almost the entire ROM error: `demo` (`+5.76 %` → `+3.83 %`) drops to `demo_nostor` (**`-0.69 %` → `-0.11 %`**).\n"
            "- Confirms that non-storage parts of `demo` (demands, prices, solar, heat pump, conversion) converge below `0.5 %` error already at `120` steps."
        ),
        md(
            "## 2. Ablation: `pv_bat` vs. `pv_bat_nostor` (removing `Bat` and `TES`)\n\n"
            "- Compares ROM cost error, capacity difference, and true Design Regret with and without storage."
        ),
        code(
            "fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))\n"
            'for c, col, lbl in [("pv_bat", "C2", "pv_bat (with Bat + TES)"),\n'
            '                    ("pv_bat_nostor", "C0", "pv_bat_nostor (no storage)")]:\n'
            "    d = df[df.case == c]\n"
            '    axes[0].plot(d.num_ts, d.obj_err_pct, marker="o", color=col, label=lbl)\n'
            '    axes[1].plot(d.num_ts, d.cap_diff_pct, marker="o", color=col, label=lbl)\n'
            '    axes[2].plot(d.num_ts, d.regret_pct, marker="o", color=col, label=lbl)\n'
            'axes[0].set_title("ROM cost error vs. M0 [%]"); axes[0].set_ylabel("error [%]")\n'
            'axes[1].set_title("Capacity difference vs. M0 [%]"); axes[1].set_ylabel("error [%]")\n'
            'axes[2].set_title("True Design Regret [%]"); axes[2].set_ylabel("regret [%]")\n'
            "for ax in axes:\n"
            '    ax.axhline(0, color="k", lw=0.8); ax.set_xscale("log"); ax.set_xlabel("clustered steps"); ax.grid(True, alpha=0.3)\n'
            "handles, labels = axes[0].get_legend_handles_labels()\n"
            'fig.legend(handles, labels, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 0.96))\n'
            'fig.suptitle("Section 2 – Effect of removing Bat + TES on pv_bat (M2)", y=1.04)\n'
            "plt.tight_layout(rect=[0, 0, 1, 0.88])"
        ),
        md(
            "**Summary (Section 2):**\n"
            "- Without storage (`pv_bat_nostor`), `M2` cost error drops from **`+13.46 % → +3.47 %`** down to **`-0.79 % → -0.05 %`**!\n"
            "- Design Regret without storage is virtually zero (`0.00–0.23 %` across the entire sweep)."
        ),
        md(
            "## 3. Hourly storage `SOC` trajectories (`M0` vs. `M2`, `M3`, `M4` at `K=192`)\n\n"
            "- Sample winter week (`days 20–27`, including the cold snap) and summer week (`days 180–187`) for `Bat` and `TES`."
        ),
        code(
            'VARS_E7 = ["M2", "M3", "M4"]\n'
            'COLORS_E7 = {"M2": "C2", "M3": "C4", "M4": "C3"}\n'
            'runs_192 = {v: rl.run("pv_bat", v, "rom", 192) for v in VARS_E7}\n'
            'm0_soc = full["pv_bat"]["soc"]\n'
            "windows = [(20 * 24, 27 * 24, 'Winter week (days 20–27)'), (180 * 24, 187 * 24, 'Summer week (days 180–187)')]\n"
            "fig, axes = plt.subplots(2, 2, figsize=(15, 6.8))\n"
            'for i, tech in enumerate(["Bat", "TES"]):\n'
            '    key = f"S1,H1,{tech}"\n'
            "    for j, (a, b, wtitle) in enumerate(windows):\n"
            "        ax = axes[i, j]\n"
            "        hrs = np.arange(a, b) - a\n"
            '        ax.plot(hrs, m0_soc[key][a:b], color="k", lw=1.8, label="M0 full")\n'
            "        for v in VARS_E7:\n"
            '            ax.plot(hrs, runs_192[v]["soc"][key][a:b], color=COLORS_E7[v], ls="--", lw=1.3, label=rl.LABELS[v])\n'
            '        ax.set_title(f"{tech} SOC — {wtitle}"); ax.set_xlabel("hours in week"); ax.set_ylabel("stored energy [kWh]")\n'
            "        ax.grid(True, alpha=0.3)\n"
            "handles, labels = axes[0, 0].get_legend_handles_labels()\n"
            'fig.legend(handles, labels, loc="upper center", ncol=4, bbox_to_anchor=(0.5, 0.99))\n'
            'fig.suptitle("Section 3 – Hourly SOC trajectories at K=192: M0 vs. M2, M3, M4", y=1.03)\n'
            "plt.tight_layout(rect=[0, 0, 1, 0.94])"
        ),
        md(
            "**Summary (Section 3):**\n"
            "- **`M0` (full year):** `Bat` and `TES` follow clean, repeating 24-hour charge/discharge cycles.\n"
            "- **`M3` (typical days):** tracks `M0`'s daily cycling closely in both winter and summer because 24-hour chronology is preserved.\n"
            "- **`M2` (typical hours):** flattens and shifts daily `SOC` swings (`Bat` misses daily solar peaks; `TES` cannot buffer intra-day heat smoothly).\n"
            "- **`M4` (downsampling):** sits flat at `0 kWh` because 45.6-hour averaging erases diurnal price/solar swings so `Bat` and `TES` are not built at `K=192`."
        ),
        md(
            "## 4. Storage operation metrics across `K`: `M2` vs. `M3` vs. `M4`\n\n"
            "- Evaluates how closely each method reproduces `M0`'s actual storage usage on `pv_bat`:\n"
            "  - **Annual throughput (`% of M0`):** total kWh charged into storage over the year (`∑ max(SOC[t+1] - SOC[t], 0)`).\n"
            "  - **Equivalent full cycles (`cyc/yr`):** annual throughput divided by installed capacity.\n"
            "  - **Hourly `SOC` correlation:** Pearson correlation between ROM's `8,760` h `SOC` trajectory and `M0` (`1.0` = identical timing)."
        ),
        code(
            "def _soc_metrics(run, ref_run, tech):\n"
            '    key = f"S1,H1,{tech}"\n'
            '    cap = run["caps"].get(key, 0.0)\n'
            '    s = np.array(run["soc"][key], dtype=float)\n'
            '    r = np.array(ref_run["soc"][key], dtype=float)\n'
            "    thru = float(np.sum(np.maximum(np.diff(s, append=s[0]), 0.0)))\n"
            "    efc = thru / cap if cap > 1e-6 else 0.0\n"
            "    corr = float(np.corrcoef(s, r)[0, 1]) if s.std() > 1e-6 else 0.0\n"
            "    return thru, efc, corr\n\n"
            'm0_ref = {tech: _soc_metrics(full["pv_bat"], full["pv_bat"], tech) for tech in ("Bat", "TES")}\n'
            "op_rows = []\n"
            'for tech in ("Bat", "TES"):\n'
            "    thru0, efc0, _ = m0_ref[tech]\n"
            "    for v in VARS_E7:\n"
            "        for k in K_EXP:\n"
            '            r = rl.run("pv_bat", v, "rom", k)\n'
            '            thru, efc, corr = _soc_metrics(r, full["pv_bat"], tech)\n'
            '            op_rows.append({"tech": tech, "variant": v, "num_ts": r["num_ts"],\n'
            '                            "thru_pct": thru / thru0 * 100, "efc": efc, "corr": corr})\n'
            "op_df = pd.DataFrame(op_rows)\n\n"
            'cols = [("thru_pct", "Annual throughput [% of M0]", "% of M0", 100.0),\n'
            '        ("efc", "Equivalent full cycles [cyc/yr]", "cycles / yr", None),\n'
            '        ("corr", "Hourly SOC correlation vs. M0", "correlation", 1.0)]\n'
            "fig, axes = plt.subplots(2, 3, figsize=(15, 7))\n"
            'for i, tech in enumerate(("Bat", "TES")):\n'
            "    for j, (col, title, ylab, ref_val) in enumerate(cols):\n"
            "        ax = axes[i, j]\n"
            "        for v in VARS_E7:\n"
            "            d = op_df[(op_df.tech == tech) & (op_df.variant == v)]\n"
            '            ax.plot(d.num_ts, d[col], marker="o", color=COLORS_E7[v], label=rl.LABELS[v])\n'
            "        ref_y = m0_ref[tech][1] if col == 'efc' else ref_val\n"
            '        ax.axhline(ref_y, color="k", ls="--", lw=1, label="M0 full")\n'
            '        ax.set_xscale("log"); ax.set_title(f"{tech}: {title}")\n'
            '        ax.set_xlabel("clustered steps"); ax.set_ylabel(ylab); ax.grid(True, alpha=0.3)\n'
            "handles, labels = axes[0, 0].get_legend_handles_labels()\n"
            'fig.legend(handles, labels, loc="upper center", ncol=4, bbox_to_anchor=(0.5, 0.99))\n'
            'fig.suptitle("Section 4 – Storage operation fidelity: M2 vs. M3 vs. M4", y=1.03)\n'
            "plt.tight_layout(rect=[0, 0, 1, 0.94])"
        ),
        md(
            "**Summary (Section 4):**\n"
            "- **`M2` (typical hours) throttles storage usage:** at `K=192`, `Bat` delivers only **`59.0 %`** of `M0` throughput (`198` vs. `358` cycles/yr, `corr = 0.62`), rising slowly to `83.4 %` at `K=1460` (`TES`: `62.4 % → 70.8 %`).\n"
            "- **`M3` (typical days) recovers realistic cycling immediately:** `Bat` reaches **`89.4 %`** throughput at `K=192` (`340` cycles/yr, `corr = 0.84`) and `93.4 %` at `K=1460` (`corr = 0.88`); `TES` reaches `94.8–102.7 %` at `K=384–1460` (`corr = 0.76–0.84`).\n"
            "- **`M4` (downsampling) suppresses storage at small `K`:** `0 %` usage up to `K=384`, `< 6 %` at `K=768`, and only activates at `K=1460` (`74.8 %` `Bat` / `59.0 %` `TES` throughput)."
        ),
        md(
            "## Findings (E7)\n\n"
            "- **Key takeaway:**\n"
            "  - **Storage coupling is the dominant cause of the remaining cost error**: forcing storage to use the same charge/discharge rate across unrelated hours in the same cluster, not smoothing the input profiles. Without storage, the `M2` ROM cost error drops below `1 %`.\n"
            "  - Removing storage changes the model, so this ablation shows the dominant cause but is not an exact decomposition of the error.\n"
            "- **Ablation (`M2`):**\n"
            "  - `demo` (`+5.76 %` at `K=48` → `+3.83 %` at `K=1460`) drops to **`-0.69 %` → `-0.11 %`** in `demo_nostor`.\n"
            "  - `pv_bat` (`+13.46 %` at `K=48` → `+3.47 %` at `K=1460`) drops to **`-0.79 %` → `-0.05 %`** in `pv_bat_nostor` (with Design Regret `≤ 0.23 %`).\n"
            "- **Storage operation comparison (`M2` vs. `M3` vs. `M4`):**\n"
            "  - `M2` under-utilizes `Bat` (`59 %` throughput at `K=192`, `83 %` at `K=1460`) because scattered hours share one dispatch variable in `stor_tech_model.py` (`_con_stor_tech_charging_dynamic`).\n"
            "  - `M3` (typical days) preserves 24 h chronology and restores `89–93 %` of `Bat` throughput (`corr = 0.84–0.88`), explaining why `M3` slashes ROM cost error (`+0.96 %` at `K=192` in **E4**).\n"
            "  - `M4` (downsampling) wipes out storage (`0 %` throughput) whenever block length exceeds ~12 hours (`K ≤ 384`).\n"
            "- **Implication:**\n"
            "  - Further tuning of typical-hour clustering (`E2`, `E3`, `E6`) cannot fix storage dispatch; preserving daily chronology (`M3` + extreme-day protection) is the right path if operating-cost accuracy with storage matters."
        ),
    ]
    return cells


def e4():
    cells = [
        md(
            "# E4 – Alternative chronology-preserving methods (`M3`, `M4`) vs. `M2`\n\n"
            "- **Goal:** Test whether keeping time order fixes storage operation and lowers both ROM cost error and Design Regret.\n"
            "- **Methods compared (`K` ∈ `{48, 96, 192, 384, 768, 1460}`):**\n"
            "  - **`M2` (Typical hours, `#57`):** 1-hour clusters + hand-picked extreme hours (breaks chronology, keeps peaks).\n"
            "  - **`M3` (Typical days, 24 h):** Hierarchical clustering of full 24-hour days (`round(K/24)` days, no extreme-day protection; keeps daily chronology).\n"
            "  - **`M4` (Temporal downsampling):** Averages consecutive hours into `K` equal-length contiguous blocks (keeps full-year order, smooths peaks & daily cycles).\n"
            "- **Cases:** `pv_bat` (sizing + regret + SOC), `demo` (ROM cost), and `swissx` (input accuracy + clustering speed)."
        ),
        code(SETUP),
        code(
            "K_EXP = [48, 96, 192, 384, 768, 1460]\n"
            'VARS = ["M2", "M3", "M4"]\n'
            'COLORS = {"M2": "C2", "M3": "C4", "M4": "C3"}\n'
            'TECHS = ["PV", "Bat", "HP", "Boiler", "TES"]\n'
            'full_pb = rl.run("pv_bat", "M0", "full")\n'
            'full_dm = rl.run("demo", "M0", "full")\n'
            'prof_sx = rl.run("swissx", "M0", "profiles")\n'
            "rows, sx_rows = [], []\n"
            "for v in VARS:\n"
            "    for k in K_EXP:\n"
            '        r = rl.run("pv_bat", v, "rom", k)\n'
            '        rg = rl.run("pv_bat", v, "regret", k)\n'
            "        sc = rl.solution_compare(full_pb, r)\n"
            '        rd = rl.run("demo", v, "rom", k)\n'
            '        row = {"variant": v, "target": k, "num_ts": r["num_ts"],\n'
            '               "obj_err_pct": sc["obj_err"] * 100,\n'
            '               "regret_pct": (rg["objective"] - full_pb["objective"]) / full_pb["objective"] * 100,\n'
            '               "cap_diff_pct": sc["cap_abs_diff_rel"] * 100,\n'
            '               "secs_solve": r["secs_solve"],\n'
            '               "demo_err_pct": (rd["objective"] - full_dm["objective"]) / full_dm["objective"] * 100}\n'
            "        for t in TECHS:\n"
            '            row[t] = r["caps"].get(f"S1,H1,{t}", 0.0)\n'
            "        rows.append(row)\n"
            '        rs = rl.run("swissx", v, "cluster", k)\n'
            "        m = rl.series_metrics(prof_sx, rs); m = m[~m.constant]\n"
            '        sx_rows.append({"variant": v, "target": k, "num_ts": rs["num_ts"], "secs_cluster": rs["secs_cluster"],\n'
            '                        "max_err": m["max_err"].abs().mean() * 100,\n'
            '                        "dc_nrmse": m["dc_nrmse"].mean() * 100,\n'
            '                        "chr_nrmse": m["chr_nrmse"].mean() * 100})\n'
            "df = pd.DataFrame(rows); sx = pd.DataFrame(sx_rows)\n"
            'print("Loaded", len(df), "pv_bat/demo runs and", len(sx), "swissx runs")'
        ),
        md(
            "## 1. Cost error, Design Regret, sizing error, and solve time (`pv_bat`)\n\n"
            "- Compares `M2`, `M3`, and `M4` vs. `M0` across actual clustered steps (log scale)."
        ),
        code(
            'panels = [("obj_err_pct", "ROM predicted cost error vs. M0 [%]", "error [%]"),\n'
            '          ("regret_pct", "True Design Regret (8,760 h re-solve) [%]", "regret [%]"),\n'
            '          ("cap_diff_pct", "Capacity difference vs. M0 [%]", "error [%]"),\n'
            '          ("secs_solve", "ROM solver runtime [s]", "seconds [s]")]\n'
            "fig, axes = plt.subplots(2, 2, figsize=(13, 8))\n"
            "for idx, (col, title, ylab) in enumerate(panels):\n"
            "    ax = axes[idx // 2, idx % 2]\n"
            "    for v in VARS:\n"
            "        d = df[df.variant == v]\n"
            '        ax.plot(d.num_ts, d[col], marker="o", color=COLORS[v], label=rl.LABELS[v])\n'
            '    if col == "secs_solve":\n'
            '        ax.axhline(full_pb["secs_solve"], color="k", ls="--", label="M0 full")\n'
            "    else:\n"
            '        ax.axhline(0, color="k", lw=0.8)\n'
            '    if col == "regret_pct":\n'
            '        ax.set_ylim(-2, 55)\n'
            '    ax.set_xscale("log"); ax.set_title(title); ax.set_xlabel("clustered steps"); ax.set_ylabel(ylab); ax.grid(True, alpha=0.3)\n'
            "handles, labels = axes[1, 1].get_legend_handles_labels()\n"
            'fig.legend(handles, labels, loc="upper center", ncol=4, bbox_to_anchor=(0.5, 0.99))\n'
            'fig.suptitle("Section 1 – pv_bat convergence: typical hours (M2) vs. typical days (M3) vs. downsampling (M4)", y=1.03)\n'
            "plt.tight_layout(rect=[0, 0, 1, 0.94])"
        ),
        md(
            "**Summary (Section 1):**\n"
            "- **ROM cost error:** `M3` slashes operating-cost error to **`+0.96 %`** at `K=192` (`8` days) vs. `+9.52 %` for `M2`; `M4` severely under-predicts cost (`-9.4 %` to `-10.6 %` at `K ≤ 384`).\n"
            "- **Design Regret (plot clipped at `55 %`):** **`M2` wins (`0.79–1.25 %` at `K=96–192`)**. Plain `M3` misses cold-snap peaks (`+227 %` at `K=48`, `+70 %` at `K=96`, `+8.1 %` at `K=192`); `M4` drops storage (`+21–46 %` regret at `K ≤ 768`).\n"
            "- **Solve time:** `M3` and `M4` solve `2–3×` faster than `M0` (`13–22 s` up to `K=384` vs. `40 s` for `M0`)."
        ),
        md(
            "## 2. Installed technology mix & `Bat` SOC trajectory (`K ≈ 192`)\n\n"
            "- **Left:** Chosen capacities relative to `M0` (`1.0` = exact) at `K=192`.\n"
            "- **Right:** Winter-week `Bat` SOC (`days 20–27`) showing why `M3` matches `M0` operation while `M4` drops battery storage."
        ),
        code(
            "fig, axes = plt.subplots(1, 2, figsize=(15, 4.5))\n"
            'k192 = df[df.target == 192].set_index("variant")\n'
            'm0_caps = {t: full_pb["caps"].get(f"S1,H1,{t}", 0.0) for t in TECHS}\n'
            "ratios = pd.DataFrame({v: [k192.loc[v, t] / m0_caps[t] for t in TECHS] for v in VARS}, index=TECHS)\n"
            'ratios.plot.bar(ax=axes[0], rot=0, color=[COLORS[v] for v in VARS])\n'
            'axes[0].axhline(1.0, color="k", ls="--", lw=1, label="M0 full")\n'
            'axes[0].set_title("Capacity mix relative to M0 (K=192)"); axes[0].set_ylabel("ratio to M0"); axes[0].grid(axis="y", alpha=0.3)\n'
            "a, b = 20 * 24, 27 * 24\n"
            "hrs = np.arange(a, b) - a\n"
            'axes[1].plot(hrs, full_pb["soc"]["S1,H1,Bat"][a:b], color="k", lw=1.8, label="M0 full")\n'
            "for v in VARS:\n"
            '    r = rl.run("pv_bat", v, "rom", 192)\n'
            '    axes[1].plot(hrs, r["soc"]["S1,H1,Bat"][a:b], color=COLORS[v], ls="--", lw=1.4, label=rl.LABELS[v])\n'
            'axes[1].set_title("Bat SOC — Winter week (days 20–27, K=192)"); axes[1].set_xlabel("hours in week"); axes[1].set_ylabel("stored energy [kWh]")\n'
            'axes[1].grid(True, alpha=0.3); axes[1].legend()\n'
            'fig.suptitle("Section 2 – Why M3 preserves daily cycling while M4 drops storage at K=192", y=1.03)\n'
            "plt.tight_layout()"
        ),
        md(
            "**Summary (Section 2):**\n"
            "- At `K=192`, `M4` averages over `45.6`-hour blocks, erasing diurnal arbitrage so it builds **`0 kWh` `Bat` and `0 kWh` `TES`** (and compensates by over-building `PV` `1.77×`).\n"
            "- `M3` preserves daily `Bat` cycling (`SOC` tracks `M0` closely), but without extreme-day protection it under-sizes `Boiler` (`36.8` vs. `58.9 kW`)."
        ),
        md(
            "## 3. Cross-check on `demo` cost error and `swissx` clustering metrics\n\n"
            "- **Panels:** `demo` cost error, `swissx` mean peak error (`max_err`), `swissx` hourly match error (`chr_nrmse`), and `swissx` clustering time (`secs_cluster`)."
        ),
        code(
            "fig, axes = plt.subplots(1, 4, figsize=(17, 3.8))\n"
            "for v in VARS:\n"
            "    d = df[df.variant == v]; ds = sx[sx.variant == v]\n"
            '    axes[0].plot(d.num_ts, d.demo_err_pct, marker="o", color=COLORS[v], label=rl.LABELS[v])\n'
            '    axes[1].plot(ds.num_ts, ds.max_err, marker="o", color=COLORS[v], label=rl.LABELS[v])\n'
            '    axes[2].plot(ds.num_ts, ds.chr_nrmse, marker="o", color=COLORS[v], label=rl.LABELS[v])\n'
            '    axes[3].plot(ds.num_ts, ds.secs_cluster, marker="o", color=COLORS[v], label=rl.LABELS[v])\n'
            'axes[0].axhline(0, color="k", lw=0.8); axes[0].set_title("demo: cost error vs. M0 [%]"); axes[0].set_ylabel("error [%]")\n'
            'axes[1].set_title("swissx: mean peak error [%]"); axes[1].set_ylabel("error [% of range]")\n'
            'axes[2].set_title("swissx: mean hourly error [%]"); axes[2].set_ylabel("error [% of range]")\n'
            'axes[3].set_title("swissx: clustering time [s]"); axes[3].set_ylabel("seconds [s]")\n'
            "for ax in axes:\n"
            '    ax.set_xscale("log"); ax.set_xlabel("clustered steps"); ax.grid(True, alpha=0.3)\n'
            "handles, labels = axes[0].get_legend_handles_labels()\n"
            'fig.legend(handles, labels, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 0.96))\n'
            'fig.suptitle("Section 3 – demo cost convergence and swissx profile/runtime comparison", y=1.05)\n'
            "plt.tight_layout(rect=[0, 0, 1, 0.87])"
        ),
        md(
            "**Summary (Section 3):**\n"
            "- On `demo`, `M3` halves cost error vs. `M2` (`+2.95 %` vs. `+5.53 %` at `K=192`); `M4` barely improves on `M2` (`+5.53 %` at `K=192`).\n"
            "- On `swissx`, only `M2` preserves peaks (`0.0 %` error vs. `26.3 %` in `M3` and `31.1 %` in `M4` at `K=192`), and `M2` also has the lowest `chr_nrmse` (`6.1 %` vs. `9.1 %` / `10.7 %`), while `M3`/`M4` cluster slightly faster (`34–36 s` vs. `45–52 s`)."
        ),
        md(
            "## Findings (E4)\n\n"
            "- **Key takeaway:**\n"
            "  - Neither plain `M3` nor `M4` is a drop-in replacement for `M2` — each solves one piece and breaks another.\n"
            "- **Comparison by method:**\n"
            "  - **`M2` (Typical hours + extremes):** Highest ROM operating-cost error (`+9.5 %` on `pv_bat` at `K=192`), **yet lowest Design Regret of `M2`/`M3`/`M4` (`0.79–1.25 %` at `K=96–192`)** and `0 %` peak error on `swissx`. Note that `M1` (main) has even lower regret at `K=96–384` (`0.07–0.35 %`, see E1b).\n"
            "  - **`M3` (Typical days, no extremes):** Cuts ROM operating-cost error at small `K` (`+0.96 %` on `pv_bat` and `+2.95 %` on `demo` at `K=192`) by keeping 24 h storage cycles intact, **but missing extreme days causes `0 kW` Boiler at `K ≤ 96` (`+70–227 %` regret) and `+8.1 %` regret at `K=192`**. Its `pv_bat` cost error does not converge with `K` (`+1.3–1.6 %` at `K=384–1460`), and its regret (`7.7 %` at `K=384`) plateaus at about `1.2 %` from `K=768`.\n"
            "  - **`M4` (Downsampling):** Fails with blocks of about 11 h or longer (`K ≤ 768`), wiping out `Bat` and `TES` investments (`+21–46 %` regret). With 6 h blocks (`K=1460`) it is competitive (`0.78 %` regret), and with 3 h blocks (`K=2920`, extra run, not in the plots) it reaches `+0.98 %` ROM cost error and `0.16 %` regret on `pv_bat` (`+3.06 %` on `demo`), i.e. as good as `M2` at `K=1460`.\n"
            "- **Recommendation:**\n"
            "  - Keep **`M2`** as the immediate fix for `#57` for correctness (exact totals, peaks kept in all stages). Its sizing is not better than `M1` at moderate `K` (see E1b).\n"
            "  - If high operating-cost accuracy with storage is needed in a future feature, build **`M3 + extreme-day protection`** (combining `M3`'s 24 h chronology with `M2`'s extreme protection)."
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
    write("E1b_design_regret", e1b())
    write("E7_storage_coupling", e7())
    write("E4_alternative_methods", e4())
