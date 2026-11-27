# Analysis: Adding Typical-Day Clustering (`M3` + Extreme Days) to ehubX

## 1. Executive Summary & Evidence (`E1b`, `E7`, `E4`)

- **Why typical hours (`M2`) alone are not enough for storage-heavy models:**
  - `M2` achieves low **Design Regret** (`0.15–1.25 %` for `K ≥ 96`) and preserves exact annual totals and peaks.
  - However, **E7** proved that `> 95 %` of `M2`'s slow-converging ROM cost error (`+9.5 %` at `K=192`, `+3.5 %` at `K=1460`) comes from forcing storage (`stor_tech_model.py`, `ebm_tech_model.py`) to share one charge/discharge rate across unrelated hours in the same cluster:
    - `Bat` throughput in `M2` is throttled to `59.0 %` of `M0` at `K=192` (`83.4 %` at `K=1460`).
    - Removing storage collapses `M2` cost error below `0.8 %` (`demo_nostor`: `-0.69 % → -0.11 %`; `pv_bat_nostor`: `-0.79 % → -0.05 %`).
- **What typical days (`M3`) already achieved in `E4` & `E7`:**
  - Preserving 24-hour chronology immediately restores realistic storage cycling (`Bat` throughput `89.4 %` at `K=192`, `93.4 %` at `K=1460`, hourly `SOC` correlation `0.84–0.88`).
  - Cuts `pv_bat` ROM operating-cost error from `+9.52 %` (`M2`) down to **`+0.96 %`** at `K=192` (`8` typical days), and cuts `demo` error from `+5.53 %` to `+2.95 %`.
- **The missing piece in plain `M3`:**
  - Without extreme-day protection, `M3` misses the winter cold snap (`0 kW` Boiler at `K ≤ 96`), causing `+70–227 %` Design Regret at `K ≤ 96` and `+8.06 %` at `K=192`.
- **Verdict:**
  - Adding **typical days with extreme-day protection (`M3e`)** to `ehubx.core.rom` is high-value, low-risk, and requires **zero changes** to `ehubx.data`, `ehubx.model`, or `ehubx.writer`.

---

## 2. Why `ehubX` Already Supports Typical Days Natively

- **Codebase audit (`src/ehubx/`):**
  - `stor_tech_model.py`, `ebm_tech_model.py`, `autonomy_model.py`, and all `writer/*` modules depend **only** on:
    - `Times.is_clustered`
    - `Times.get_cluster_ts(s, t_hor)`
    - `Times.get_weight(s, t)`
  - Neither `model/` nor `writer/` assumes 1-hour periods; `SET_TIMEHORIZON` remains `1..8760`.
- **Mapping scheme (verified in `run_case.py:cluster_typical_days`):**
  - Partition `8,760` hours into `365` days (`d = 0..364`) × `24` hours (`h = 0..23`).
  - Map day `d` to day-cluster `c_d ∈ {0..D-1}`, and horizon hour `t_full = 24*d + h + 1` to clustered step `t_cl = 24*c_d + h + 1` (`1..24*D`).
  - Set `weight(s, t_cl) = count of days in cluster c_d` (weights sum to `24 * 365 = 8,760` h).
  - Compute each clustered profile value as the **exact mean** over all days assigned to `c_d` at hour-of-day `h` (guarantees exact weighted sums).
  - **Result:** Intra-day 24 h dispatch is uncoupled across hours of the day, while `VAR_STORTECHENERGY` still runs across all `8,760` hours so inter-day/seasonal `SOC` continuity works out of the box.

---

## 3. Proposed Public API (`src/ehubx/core/rom.py`)

| Option | Design | Pros | Cons |
|---|---|---|---|
| **Option A (Recommended)** | Add `hours_per_period: int = 1` (and optional `extreme_periods` / `max_extreme_periods`) to `RomSettings` under `RomMethod.CLUSTER_TSAM` | 100 % backward-compatible default (`1`); single enum; clean extension | `num_ts_target` semantics when `hours_per_period=24` must be documented clearly (target total hours vs. rounded to multiple of `24`) |
| **Option B** | Add `RomMethod.CLUSTER_TSAM_DAYS` with `num_days_target` | Explicit unit (`days` vs. `hours`) | Splits `tsam` code paths/enums for the same underlying library |

- **Recommendation:** Use **Option A** (`hours_per_period: int = 1`, validating `hours_per_period >= 1` and `num_horizon_ts % hours_per_period == 0`), rounding `num_ts_target` to `round(num_ts_target / hours_per_period)` periods (with a minimum of `1`) and logging the actual `D × hours_per_period` steps.

---

## 4. Key Engineering Subtleties to Resolve

1. **Extreme-day count explosion (highest risk):**
   - Extracting both `max` and `min` days across all `46` series on `swissx` could isolate `50–80` distinct extreme days (`1,200–1,920` steps), defeating compression.
   - **Mitigations to benchmark in `E4b`:**
     - Skip trivial/repeated minima (e.g., nighttime `0` PV, summer `0` heating, capped flat bounds).
     - Test **peaks-only vs. max+min**, or rank candidate extreme days by normalized extremeness / series relevance with an optional `max_extreme_periods` cap.
2. **Horizon divisibility & skip guard:**
   - Require `num_horizon_ts % hours_per_period == 0` (raises `EhubXException` otherwise, e.g., if horizon is not a multiple of `24`).
   - Skip clustering (return `None` with warning) whenever `D_reg + max_s(|ext_days_s|) >= n_days`.
3. **Multi-stage synchronization & cluster floor:**
   - Reuse `#57`'s single-pass sync across stages: `D_total = D_reg + max_s(|ext_days_s|)` so every stage gets exactly `D_total * hours_per_period` clustered steps.
   - Do **not** apply the `2 × num_ser_max` floor to typical days: on `swissx` (`46` series), that floor would force `92` days = `2,208` steps. For `hours_per_period > 1`, regular period count only needs `D_reg >= 1` (or `>= 2` periods).
4. **Seasonal storage & feature compatibility:**
   - Because `VAR_STORTECHENERGY` is still indexed over `SET_TIMEHORIZON` (`8,760` h), inter-day energy transfer works across days (matching Kotzur et al. 2018 linked-period formulations); still verify on a seasonal-storage (e.g., H2/ATES) test model.
   - Keep `load_shifting` and `ates_techs` blocked initially as in `rom.py` (noting that intra-day load shifting `<= 24 h` could be unlocked for `hours_per_period=24` in a later step).

---

## 5. Touchpoints & Implementation Roadmap

### Code & Docs Touchpoints
| File | Change |
|---|---|
| `src/ehubx/core/rom.py` | Extend `RomSettings` (`hours_per_period=1`, extreme-period options) and generalize `_cluster_tsam` / `__cluster_stage` for period length `L` (`1` or `24`). |
| `tests/tests_core/test_rom.py` | Unit tests for `hours_per_period=24`: weight sums (`8,760`), intra-day chronology, exact weighted sums, extreme-day retention, multi-stage sync, and non-divisible horizon error. |
| `docs/source/main_file.rst` | Document `hours_per_period` trade-off: `1` (best sizing/peaks per step) vs. `24` (accurate storage operation & cost). |
| `CHANGELOG.rst` | Entry under *Unreleased*. |
| `src/ehubx/{data,model,writer}/` | **No changes required.** |

### Recommended Next Steps
1. **Merge `#57` (`M2`) as-is** — it is a strict bugfix for typical-hour clustering and gives the best sizing/regret today.
2. **Run a small `E4b` experiment** (`M3e` on `pv_bat` and `swissx`) to test extreme-day selection rules (peaks-only vs. non-trivial max/min vs. capped extremes) and confirm `< 1 %` ROM cost error **and** `< 1 %` Design Regret simultaneously.
3. **Implement `hours_per_period=24` in `src/ehubx/core/rom.py`** in a dedicated follow-up PR with unit tests in `tests/tests_core/test_rom.py`.
