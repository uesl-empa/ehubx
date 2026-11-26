## Findings (E1)

**Actual size.** The target is often not what the model gets. demo/ms3: a
target of 24 gives 60 steps (2 × 16 series + 28 extremes). SwissX: targets 24
and 48 both give 133 steps (2 × 46 series + 41 extremes); the 2 × series rule
dominates below ~100.

**Objective converges slowly.** demo, M2: +5.7 % at 60 steps, +5.5 % at 220,
+4.5 % at 796, +3.8 % at 1488 and still **+3.0 % at 2948 steps** (a third of
the year). ms3 behaves the same (+6.9 % → +3.1 %). The input-level errors fall
much faster (totals exact, duration curve error 0.14 → 0.02). So the ROM error
of these models is **not mainly a matter of how well the profiles are
represented**.

Likely cause: with typical *hours*, all hours of a cluster share one set of
operation variables. The storage energy level runs over the horizon, but its
in- and outflows are indexed by the clustered step
(`stor_tech_model.py`, `_con_stor_tech_charging_dynamic`), so the storage
charges or discharges by the same amount in every hour of a cluster, i.e. at
hours spread over the whole year. The structure is confirmed in the code; its
share of the objective error is still to be quantified (E7). This
restricts storage operation (and anything else that couples hours) and makes
the ROM more expensive. Typical days (M3) or downsampling (M4) keep the
chronology and may behave very differently. The weak decrease of
`chr_nrmse` (0.23 → 0.10) points the same way.

**Methods compared.** The three methods converge alike. M2 has a lower
objective error at small K (demo: 5.7 % vs 6.7 % at 60 steps; ms3: 6.9 % vs
7.6 %) and exact totals and peaks at every K. M1 loses up to 52 % of the peak
range in multi-stage models even at 1500 steps (SwissX: 8 %). M2's
duration-curve error is a bit higher at small K and equal from ~400 steps on.

**Clustering time.** M2 is much faster: SwissX 44–81 s vs 210–2300 s for
M1/M1b (tsam's extreme-period handling and the re-clustering are expensive);
demo 7–12 s vs 23–143 s.

**Solve time.** Full demo: 76 s, ms3: 144 s; ROM 19–65 s and 35–180 s. The
speed-up of the ROM is only 2–4× for these small models. Solve times were
measured with 6 runs in parallel and are only indicative.

**Next.** E7 (storage / coupling over time) and the alternative methods M3/M4
look more important than further tuning of the typical-hours clustering (E2,
E3). A model with free capacities is needed for the design comparison.
