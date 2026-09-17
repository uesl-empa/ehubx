# GitLab → GitHub migration audit

Audit of the `port/gitlab-outstanding` branch: what existed only on each
side, and how each difference was resolved.

- **Base:** `github/main` @ `da44b931` ("Upgrade to 2.3.1 (#14)", 2026-07-26)
- **Port commit:** `24507591` — 36 files, +1705 / −178
- **Version:** stays **2.3.1** (see [Version](#version))
- **Generated:** 2026-09-16

---

## 1. Why this is not a merge

The two repositories **share no common ancestor**:

```
$ git merge-base origin/main github/main
(exit 1 — no common commit)
```

GitHub was seeded by periodically copying GitLab's working tree into a fresh
history (28 commits: "Transfer from GitLab", "Reconsituted current code state
of GitLab main"). GitLab's history is independent and 947 commits long.

So `git merge` and `git cherry-pick` do not work between them. The port was
applied as a **content patch onto `github/main`**, with conflicts resolved by
hand. The branch is exactly one commit on top of `da44b931`; no GitLab history
is introduced.

---

## 2. Commits that existed only on GitLab

These are the changes made on GitLab **after** the last snapshot
(`4ee7dc8c`, 2026-07-26) — i.e. the entire port payload.

| Commit | Date | Author | Subject | Ported? |
|---|---|---|---|---|
| `85937eb7` | 2026-07-27 | Arijit Upadhyay | Adding two new transport units (passenger pkm and freight tkm) and handling across the model | **Yes** |
| `d4333e07` | 2026-07-27 | Arijit Upadhyay | Modified tests to handle a few exceptions since pipeline on Gitlab failed | **Yes** (test changes only) |
| `a72b6491` | 2026-08-19 | Barton Chen | Fix opex_per_energy cost to use only main output carrier (#279) | **Yes** |
| `7db314a1` | 2026-08-19 | Barton Chen | Update model.rst formula for ConvTechCostOpexOut to match fix (#279) | **Yes** |
| `8bacfcd1` | 2026-08-19 | Chen, Yi-Chung | Merge branch 'issue279...' into 'main' | n/a (merge commit) |
| `383117f6` | 2026-09-14 | Barton Chen | Add GitHub migration notice to README | **No — deliberately GitLab-only** |

`383117f6` is the freeze notice on the GitLab README. It is intentionally not
ported: it describes GitLab's status and would be wrong on GitHub.

---

## 3. Commits that existed only on GitHub

All 28 GitHub commits are GitHub-only in the literal sense (no shared history).
What matters is the **work that exists only on GitHub** and therefore had to
survive the port:

| Commit | Date | Subject | Significance |
|---|---|---|---|
| `da44b931` | 2026-07-26 | Upgrade to 2.3.1 (#14) | Current version |
| `0be6a48c` | 2026-07-26 | Introduced autonomy as an objective and a model (#12) | **`autonomy_model.py`, 490 lines — no GitLab equivalent** |
| `4ee7dc8c` | 2026-07-26 | Reconsituted current code state of GitLab main (#11) | The snapshot this port builds on |
| `eaf20efb` | 2026-07-18 | Upgraded ci.yml to include manual PyPI testing | TestPyPI dispatch path |
| `8edb880e` | 2026-07-18 | Added automatic PyPI pipeline upon release (#7) | Release automation |
| `d11a085a` | 2026-07-18 | Include PyPI installation instructions (#6) | |
| `a1e72ce9` | 2026-07-18 | Upgrade to 2.3.0 (#5) | Open-source release |
| `e2932e21` | 2026-07-18 | Fixing readthedocs (#3) | `.readthedocs.yaml` |
| `1b8f2d0c` | 2026-07-18 | Make public ready (#2) | **GPLv3 `LICENSE`** |
| `dd132fcb` | 2025-03-07 | Added ruff, removed flake8, ... pre-commit hooks | Lint config |

Older commits (`ccd3353c` … `fb65816c`, 2025-02 → 2026-03) are earlier
GitLab transfers and CI/docs experiments, superseded by `4ee7dc8c`.

---

## 4. Files that exist on only one side

### Only on GitHub — all preserved by the port

| File | Origin | Status after port |
|---|---|---|
| `src/ehubx/model/autonomy_model.py` | `0be6a48c` | **Kept** (+ updated for new unit signature) |
| `LICENSE` (GPLv3) | `1b8f2d0c` | **Kept** |
| `.github/workflows/ci.yml` | `8edb880e` | **Kept** |
| `.readthedocs.yaml` | `e2932e21` | **Kept** |
| `docs/requirements.txt` | `e2932e21` | **Kept** — see [§6](#6-issues-caught) |
| `docs/build_docs.bat` | — | **Kept** — see [§6](#6-issues-caught) |

### Only on GitLab — **not** ported

| File(s) | Why not |
|---|---|
| `.gitlab-ci.yml` | GitLab-specific CI; GitHub uses `.github/workflows/ci.yml` |
| `.devcontainer/` (5 files) | Dev-environment config incl. Gurobi licence scripts. **Not ported — decide separately** |
| `.vscode/launch.json`, `settings.json` | Editor config. **Not ported — decide separately** |
| `models/about.txt`, `sphinx_log.txt` | Local artifacts, not source |

> **Open item:** `.devcontainer/` and `.vscode/` are genuinely useful developer
> tooling that GitHub lacks. They were out of scope for this port (they are not
> part of either ported feature) but are worth a follow-up PR.

---

## 5. How each conflict was resolved

`git apply --3way` reported **8 conflict hunks in 6 files**. Resolutions:

| File | Conflict | Resolution |
|---|---|---|
| `src/ehubx/__init__.py` | `__version__` 2.3.1 vs 2.2.4 | **Kept GitHub's 2.3.1** — never downgrade |
| `docs/source/conf.py` | `release` 2.3.1 vs 2.2.4 | **Kept GitHub's 2.3.1** |
| `src/ehubx/data/energy_system_data.py` | 2 hunks: unit fields + properties | **Kept both sides** — `time_unit` (GH) *and* `passenger_unit`/`freight_unit` (GL); purely additive |
| `src/ehubx/model/stor_tech_model.py` | Unit import line | **Union** — GitLab's line drops `CurrencyUnit`, which is used twice in the file |
| `src/ehubx/model/conv_tech_model.py` | `_con_conv_tech_out_sum_minmax` call | **Combined** — GitLab's widened signature **plus** GitHub's `_con_conv_tech_co2_oper` / `_co2_oper_total` calls |
| `src/ehubx/model/demand_model.py` | Unit import | **Union** — kept `TimeId` (GH, used 5×) and GitLab's new unit types |
| `src/ehubx/model/demand_model.py` | Constraint return statement | **Hand-merged** — both sides rewrote the same line independently |

### The two resolutions that mattered most

**`conv_tech_model.py` — CO2 constraints**

GitLab's side of the hunk omits two calls that simply do not exist on GitLab.
Taking "theirs" would have silently deleted GitHub's operational CO2 emission
constraints:

```python
# resolved to:
_con_conv_tech_out_sum_minmax(
    model, ecs, conv_techs, times, mass_unit, power_unit,
    length_unit, passenger_unit, freight_unit,   # <- from GitLab
)
_con_conv_tech_co2_oper(model, times, conv_techs, mass_unit)   # <- GitHub-only, kept
_con_conv_tech_co2_oper_total(model)                           # <- GitHub-only, kept
```

**`demand_model.py` — unmet demand vs unit resolution**

GitHub had renamed the term to `total_served_plus_unmet` (load-shedding work);
GitLab had changed how the unit is resolved. Neither side alone is correct:

```python
# resolved to: GitHub's semantics + GitLab's unit handling
unit_energy = get_ec_model_unit(
    ecs.get_unit(EcId(e)), mass_unit, power_unit,
    length_unit, passenger_unit, freight_unit,
)
demand_sum = demands.get_demand_sum(...).to_float(unit=unit_energy)
return total_served_plus_unmet == demand_sum
```

---

## 6. Issues caught

Six problems that a naive "apply and resolve" would have shipped. Items 1-4
were resolution hazards; items 5 and 6 are pre-existing GitHub-only defects
that the port surfaced because GitLab had never had them.

1. **Deleted CO2 constraints** (`conv_tech_model.py`) — see above.
2. **Lost unmet-demand term** (`demand_model.py`) — see above.
3. **Stale `get_ec_model_unit()` callers in GitHub-only code.** GitLab's patch
   widened this function from 3 to 6 parameters. Of the 42 call sites on
   `github/main`, the patch updated those it knew about, but could not touch
   code that exists only on GitHub. The remainder had to be fixed by hand:

   | File | Calls fixed | Also needed |
   |---|---|---|
   | `autonomy_model.py` | 5 | 3 signatures + 3 call sites widened |
   | `demand_model.py` | 5 | `_con_unmet_demand_gate_all` signature + call site |
   | `stor_tech_model.py` | 2 | `_con_stor_tech_fill_cost` signature + call site |
   | `stor_tech_writer.py` | 1 (multi-line) | — |

   The model-side breakages were caught by the test run (`TypeError:
   get_ec_model_unit() missing 3 required positional arguments`); the
   `stor_tech_writer.py` one was a multi-line call that grep missed and
   **only mypy caught**.
4. **`docs/requirements.txt` deletion.** The cross-history diff tried to remove
   it and `docs/build_docs.bat`, since GitLab never had them. `.readthedocs.yaml`
   references `docs/requirements.txt`, so this would have **broken the docs
   build**. Both restored. A CRLF-only change to `docs/make.bat` was also
   reverted as noise.
5. **`soc_init` rows labelled `soc_max`** (`stor_tech_writer.py`,
   `ebm_tech_writer.py`). On `github/main` the `soc_init` loop in both writers
   passed `ENTRY_SOCMAX` to `add_row()`, so initial-SOC values were written to
   the result files under **"Maximal SOC (soc_max)"**. `ENTRY_SOCINIT` was
   defined in both files and never used, and the `# soc_init` comment directly
   above the call confirms the intent. GitLab had the correct label, so the fix
   arrived with the content patch.

   This changes the `ENTRY` column value of those rows from
   `Maximal SOC (soc_max)` to `Initial SOC (soc_init)`. Downstream scripts
   filtering on that string will behave differently — correctly, but
   differently. It is the one **output-affecting** change in the port that is
   not a new capability.
6. **TSCL output filenames built from the wrong variable** (`tech_writer.py`).
   In `_format_file_granularity`, the `source != SOURCE` branch of the `-TSCL`
   loop assigned to `filename_ts_hor`, the horizon variable belonging to the
   separate `-TS` loop above, leaving `filename_ts_cl` at its loop default.
   Because that default omits the tech id `x`, techs sharing a `source`
   collided on one output path and overwrote each other. Also GitHub-only;
   separated into its own commit since it belongs to neither ported feature.

---

## 7. Verification

Run against `github/main` as baseline, same machine and environment:

| Check | Baseline (`da44b931`) | Ported (`24507591`) |
|---|---|---|
| pytest | 233 failed, 553 passed | 233 failed, 553 passed |
| New failures introduced | — | **0** |
| Previously-failing tests fixed | — | 0 |
| ruff | clean | clean |
| mypy | 1 error (`time_series.py:232`) | same 1 error |

Failure sets were compared name-by-name, not just by count.

### Caveat

The 233 baseline failures are **environmental, not code defects**:

- **GLPK is not installed locally** — CI installs it (`apt-get install glpk-utils`)
- **Logger state leaks between tests** — tests pass individually, fail in a full run

This means the **solver-dependent tests never actually executed here**. The
numerical behaviour of both ported features is therefore *not* verified locally;
CI is the real check. Treat green CI as a merge precondition.

---

## 8. Output compatibility

**Verified: the port does not change the output file schema.**

Result CSVs use a fixed 14-column schema defined by `DfStColumn` in
`writer/common_writer.py`:

    ENTRY, VALUE, UNIT, STAGE, HUB, EC, TECH, NET_LINK, NET_LINK_DIR,
    NET_TECH, LOAD_SHIFT, ATES_SCHEDULE, SOURCE, INPUT_OR_RESULT

`git diff github/main HEAD -- src/ehubx/writer/common_writer.py` is empty: the
enum is untouched. `add_row()` emits each parameter as a **row**, with the
parameter name as a *value* in the `ENTRY` column, so adding model parameters
can never widen the file. No new `ENTRY_` constants were defined either.

Consequences for downstream scripts:

| Change | Effect on existing models |
|---|---|
| New `ENTRY` rows | None â no new entries defined |
| New columns | None â schema unchanged |
| New `UNIT` values | Only for pkm/tkm carriers, which could not previously be declared |
| `soc_init` row label | **Changes** â see [§6](#6-issues-caught) item 5 |

`get_ec_model_unit()` can now return length, passenger or freight units, which
reach the `UNIT` column. This is reachable only for carriers declared in those
units, and `set_unit()` rejected them before this port, so **existing models
produce identical output**. The change is additive.

The one genuine output difference is the `soc_init` label fix. It corrects rows
that were mislabelled `Maximal SOC (soc_max)`; scripts filtering on that string
will see different results.

This makes the port **MINOR (2.4.0)** under SemVer, not MAJOR.

---

## Version

The port leaves the version at **2.3.1**. It does not bump it, because
a version bump belongs to a release commit, not a port.

Suggested next release: **2.4.0**.

- Transport units add new capability (new `pkm` / `tkm` units, new
  `energy_system` properties) → MINOR under SemVer
- The opex fix alone would be PATCH (2.3.2), but MINOR absorbs it

Bump all three in the same commit, or the package misreports itself:

```
pyproject.toml          version = "2.4.0"
src/ehubx/__init__.py   __version__ = "2.4.0"
docs/source/conf.py     release = "2.4.0"
```

Then add a CHANGELOG entry and publish a GitHub Release tagged `2.4.0`
(bare tag, no `v` prefix) — `publish_pypi` triggers on `release: published`.

> **PyPI is write-once.** Once `2.4.0` is uploaded it can never be replaced,
> even after deletion. Use the `workflow_dispatch` → `testpypi` path first.

---

## Open items

- [x] ~~Verify the transport-units change does not alter **output file
      columns**.~~ **Resolved: columns are unchanged; MINOR (2.4.0) stands.**
      See [§8](#8-output-compatibility).
- [ ] Decide whether to port `.devcontainer/` and `.vscode/` from GitLab.
- [ ] Grant Barton Chen write access to `uesl-empa/ehubx` (currently 403;
      this port must go via a fork).
- [ ] Triage the ~30 remaining GitLab feature branches (ATES, wind, currency
      scaling, parser overhaul) before GitLab is archived.
