# Investigation plan: impact of time clustering (ROM) on ehubX results

Status: draft plan · Related: issue #57, PR #58

## 1. Why

The fixes on #57/#58 showed that how the time series are clustered can move results by several percent: objective error vs the full model went from +6.7% to +5.7% (single-stage demo) and from +7.4% to +6.8% (two-stage demo) from changes in the clustering details alone. We currently do not know:

- how large the ROM error is for realistic models, and how it depends on the number of clustered time steps;
- whether the error is in the **objective only** or also in the **design decisions** (which technologies, what capacities), which is what users act on;
- which parts of the clustering drive the error (extreme periods, feature scaling, period length, multi-stage handling, storage);
- what default settings and user guidance we should give.

## 2. Questions to answer

1. **Accuracy vs size:** How do objective, design and key KPIs converge towards the full model as `num_ts_target` grows? Where is the knee?
2. **Design regret:** If the design from the ROM is fixed and operated over the full horizon, how much worse is it than the full-model optimum? Is it even feasible?
3. **Extreme periods:** Do max/min extreme periods help, and are some of them wasted (e.g. the first zero hour of PV, see note in §6 E2)?
4. **Feature scaling:** All series currently count equally in the clustering distance (after tsam's normalisation). Does weighting by relevance (demands, prices, renewables vs temperatures, limits) improve results?
5. **Period length:** Are 1-hour periods (current) better or worse than typical days (24 h) for models with daily patterns and storage?
6. **Multi-stage:** Does a common number of clustered steps across stages cost accuracy compared with per-stage counts? How does a stage with many extremes affect the others?
7. **Storage:** Is short-term and seasonal storage operation represented correctly via the horizon-to-cluster mapping?
8. **Robustness:** Are results stable under small data perturbations, and do edge cases (negative prices, zero profiles, many series on a short horizon) behave correctly?

## 3. Methods compared

| ID | Method | Description | Scope |
|---|---|---|---|
| **M0** | Full time horizon | No clustering, all 8760 h. Reference for all metrics. | core |
| **M1** | Existing ehubX method (typical hours) | tsam, 1-hour periods, hierarchical (Ward) clustering, extremes via tsam's `new_cluster_center`. As on `main`; PR #58 (per-stage re-clustering to a common count) is run as variant **M1b**. | core |
| **M2** | Proposed fix of M1 | Branch `57-rom-extreme-periods`: extreme hours picked by hand (max/min of each series) as single-hour clusters, remaining hours clustered into the regular clusters, common count across stages, clustered values = exact member means. Sub-variants from E2/E3 (extreme handling, series weighting). | core |
| M3 | Typical days (as in MANGO) | 24-hour periods clustered into representative days (tsam `hoursPerPeriod=24`), each horizon hour mapped to (typical day, hour of day), weight = days per cluster. Keeps the daily shape and within-day chronology. | optional |
| M4 | Temporal downsampling (as in PyPSA) | Average consecutive hours into 2-, 4-, 8-hour… blocks; weight = block length. Keeps full chronology, loses within-block variability and peaks. | optional |

Notes:
- All methods are compared at equal numbers of clustered time steps (e.g. M3 with 8 typical days ≈ 192 steps vs M1/M2/M4 with ~192 steps).
- M3 and M4 appear to fit the existing horizon-to-cluster mapping (`get_cluster_ts`) and per-stage weights, so storage would keep running over horizon hours. This needs to be verified before implementing them.
- M4 needs no clustering algorithm at all and is the simplest baseline; if it performs close to M2, that is an important finding in itself.

## 4. Test models

| Model | Stages | Why | Status |
|---|---|---|---|
| `examples/clustering_demo` | 1 | Reference, already used | available |
| Two-stage synthetic (ms3, from #57 work) | 2 | Multi-stage, known behaviour | in scratchpad, to be moved here |
| SwissX (from `ehubx-swissx-wind`) | 4 | Real multi-stage model: national scale, PV, wind, hydro storage | profiles in `models/swissx/` |
| A model with large PV share + battery | 1–2 | Many zeros, daily storage | to be selected/built |
| A model with seasonal storage (e.g. H2/thermal) | 1–2 | Chronology over the year | to be selected/built |
| A model with negative prices | 1 | Edge case from issue 4 | synthetic |

Models should be small enough that the **full 8760 h model solves** (needed as reference).

## 5. Metrics

**Model-level (primary)**
- Relative objective error vs full model.
- Design: installed capacity per technology and hub; absolute and relative difference; technology choice changes (built / not built).
- **Design regret:** fix the ROM design, re-solve operation over the full horizon; report cost increase vs full optimum and infeasibility / load shedding.
- Key KPIs: imports/exports, emissions, renewable share, storage throughput, curtailment.
- Solve time and model size (variables, constraints) for ROM vs full.

**Input-level (cheap, explains model-level results)**
- Weighted sum error per series (should be 0 with the current fix).
- Peak and minimum retention.
- Duration-curve error (e.g. RMSE between full and clustered duration curves).
- Preservation of correlations between series (e.g. PV vs demand) and of ramps.

## 6. Experiments

Each experiment is a script that writes a tidy results table (one row per model × variant × K).

- **E0 – Baseline / reproducibility.** M0 vs M1, M1b and M2 at the same K. Confirms the changes and fixes the baseline.
- **E1 – Convergence sweep.** K ∈ {24, 48, 96, 192, 384, 768, 1460, 2920} for M1 and M2 (later also M3, M4), against M0. Plot all model-level metrics vs K.
- **E2 – Extreme periods.** Variants: none / max only / max + min / max + min but skip minima or maxima that repeat in many hours (e.g. PV zeros, capped prices). Compare at equal total K, so the cost of extremes is visible.
- **E3 – Feature scaling and weighting.** tsam normalisation as now vs weights per series type (e.g. higher for demands, prices, renewable profiles; lower for temperatures and limits) vs dropping series that hardly vary.
- **E4 – Alternative methods (optional).** M3 (typical days) and M4 (downsampling) vs M2 at equal K, after a feasibility check of the code (mapping, weights, extreme days for M3).
- **E5 – Multi-stage.** Common K (current) vs per-stage K with the same total; effect of one stage with many more series/extremes.
- **E6 – Clustering algorithm.** Hierarchical (Ward, current) vs k-means vs k-medoids; mean vs medoid representation.
- **E7 – Storage.** For storage-heavy models: compare state-of-charge trajectories, storage capacities and seasonal shift between ROM and full.
- **E8 – Robustness.** Small random perturbations of input data (±1–5%) and edge cases; check stability of design and objective.

Order: E0 → E1 → E2 → E3 first (cheap, highest expected impact, needed by the rest); E4–E8 depending on findings.

## 7. Folder layout

```
docs/dev/rom_clustering_investigation/
  PLAN.md          this file
  REPORT.md        findings, written as experiments complete
  scripts/         experiment scripts (one per experiment, plus shared helpers)
  models/          small synthetic test models (input files only)
  results/         raw result tables and plots (git-ignored; final plots copied into REPORT.md)
```

## 8. Deliverables

1. `REPORT.md` with results per experiment, plots and a short conclusion.
2. Recommended defaults (`num_ts_target`, extreme handling, scaling) and user guidance for `docs/source/main_file.rst`.
3. Code changes, if any, as separate issues/PRs with their own tests (as done for #57).
4. Optionally: a reusable "ROM vs full" comparison utility (objective, design, regret) for users to check their own models.

## 9. Open points

- Which real multi-stage model(s) can be used as reference, and can their data be stored in the repo?
- Solver and time budget for the full-horizon reference runs (Gurobi on the server?).
- Is design regret (fix design, operate over full horizon) supported by the current API, or does it need a helper?
- Should M3/M4 (E4) be in scope, given they may need code changes? M4 is likely the cheaper of the two.
