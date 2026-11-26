# SwissX multi-stage profiles

Hourly input profiles (8760 h) of the SwissX model: one hub (H1), four stages
S1–S4 (2020/2030/2040/2050).

Source: local repo `ehubx-swissx-wind` (GitLab `ues-lab/team-mes/ehubx-swissx-wind`),
commit `01284db`, files copied unchanged:

| File | Source path | Content |
|---|---|---|
| `profiles/demands.csv` | `inputs/basic/profiles/` | demand profiles per energy carrier and stage |
| `profiles/imports.csv` | `inputs/basic/profiles/` | import prices and min/max import limits |
| `profiles/exports.csv` | `inputs/basic/profiles/` | electricity export price |
| `profiles/hub_profiles.csv` | `inputs/basic/profiles/` | technology availability (hydro storage turbine, alpine PV) |
| `profiles/solar_irradiation.csv` | `inputs/renewables/` | irradiation per orientation (kW/m²) |
| `profiles/wind_speed.csv` | `inputs/renewables/` | wind speed per wind group W1–W10 (m/s) |

Approximate number of time series per stage (all files): S1 43, S2 45,
S3 46, S4 44. With the current ROM rule (regular clusters ≥ 2 × series of the
largest stage) this gives at least ~92 regular clustered steps plus extremes,
if all these series enter the clustering.

Only the profiles are copied here. The full model (YAML inputs, scenario
settings) stays in `ehubx-swissx-wind`.

The profile files are git-ignored, because this repository is public and the
data comes from an internal repository. To recreate them, copy the six files
listed above from `ehubx-swissx-wind` into `profiles/`.
