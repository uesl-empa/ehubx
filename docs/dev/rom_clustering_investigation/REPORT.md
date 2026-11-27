# ROM clustering investigation: findings so far

Plan and method definitions (M0–M4): `PLAN.md`. Details, plots and code per
experiment: `notebooks/`. Test models: `models/README.md`. Follow-up on
typical days: `TYPICAL_DAYS_ANALYSIS.md`.

K is the clustered-step target; *ROM cost error* is the ROM objective vs. the
full-horizon (M0) objective; *design regret* is the cost of operating the ROM
design over the full year (capacities fixed) vs. M0.

## Main findings

1. **Correctness (E0, E1).** M2 (#57) gives exact weighted totals and keeps
   peaks in every stage, and it no longer crashes on multi-stage models. M1
   (main) biases totals and can lose extremes in multi-stage models.
2. **ROM cost error is dominated by storage, not by profile error (E1, E7).**
   With typical hours, all hours of a cluster share one storage dispatch. On
   `pv_bat`, M2 overestimates cost by +9.5 % at K=192 and +3.5 % at K=1460.
   Without storage (`*_nostor` models), the error is below 1 %.
3. **Design regret is much smaller than the ROM cost error (E1b).** For K ≥ 96
   the M2 regret on `pv_bat` is 0.15–1.25 %. M1 is *not* worse: at K=96–384 its
   regret is lower (0.07–0.35 %). M2 is better only at K=48 and K ≥ 768.
4. **That M1/M2 regret gap is mostly an artefact of the 5 CHF/kWh backup heat
   price (E1c).** M2 keeps only the single peak hour, so it sizes heating
   3–6 kW too small. With backup heat at 1.0 CHF/kWh (same M0 optimum), M2
   regret drops to 0.11–0.22 % at K=96–384, close to M1 (0.03–0.12 %).
5. **Typical days (M3, no extreme days) fix the storage error but miss the
   cold snap (E4).** The ROM cost error is +0.96 % at K=192, but the regret is
   +8.1 % at K=192 and +70–227 % at K ≤ 96 (no boiler). The cost error does not
   converge (+1.3–1.6 % at K=384–1460), and the regret plateaus at about 1.2 %.
6. **Downsampling (M4) works only with short blocks (E4).** Blocks of about
   11 h or longer (K ≤ 768) remove storage from the design (regret +21–46 %).
   With 6 h blocks (K=1460) the regret is 0.78 %, and with 3 h blocks (K=2920)
   +0.98 % cost error and 0.16 % regret.

### Design regret on `pv_bat` (backup heat 5.0 vs. 1.0 CHF/kWh)

| K | M1, 5.0 | M2, 5.0 | M1, 1.0 | M2, 1.0 |
|---|---|---|---|---|
| 48 | 12.05 % | 6.34 % | 12.05 % | 5.23 % |
| 96 | 0.07 % | 0.79 % | 0.07 % | 0.11 % |
| 192 | 0.07 % | 1.25 % | 0.03 % | 0.22 % |
| 384 | 0.35 % | 0.69 % | 0.12 % | 0.17 % |
| 768 | 0.31 % | 0.26 % | 0.15 % | 0.12 % |
| 1460 | 0.21 % | 0.15 % | 0.06 % | 0.07 % |

## Recommendations

- Merge #57 (M2) for correctness, not for better sizing.
- In M2, protect the *duration* of peaks (near-peak hours or extreme days), not
  only the single peak hour; this is the likely fix for its heating shortfall.
- For storage-heavy models where operating cost matters, typical days with
  extreme-day protection (see `TYPICAL_DAYS_ANALYSIS.md`), or downsampling to
  about 3 h blocks if ~3,000 steps are affordable.

## Limitations

- All sizing and regret results come from one synthetic single-stage model
  (`pv_bat`, seed 42). Other seeds or models may change the M1/M2 ranking.
- Regret mode fixes technology capacities only (not networks).
- Solve times are indicative: up to 6 runs shared the machine.
- SwissX is used for clustering only (no solves).
