# Wind demo

Should a Swiss municipality build wind turbines on a nearby Jura crest, and
which ones? This example shows the wind module on a realistic, one-year case.

Run it from the repository root (a MILP solver is needed; GLPK is enough):

```bash
python examples/wind_demo/main_wind_demo.py
```

## Setup

| Item | Value | Source / assumption |
|---|---|---|
| Hub | `Village`, one electricity carrier `Elec` | |
| Demand | 22.5 GWh/a, hourly, with daily, weekly and seasonal pattern | Synthetic profile for a municipality of about 5000 inhabitants (see [Input data](#input-data)) |
| Grid import | 0.24 CHF/kWh weekdays 06:00–22:00, 0.18 CHF/kWh otherwise; 0.128 kg CO2/kWh | Typical Swiss time-of-use tariff level; CO2 intensity of the Swiss consumption mix |
| Export | 0.08 CHF/kWh | Lower than any import price, so importing and exporting at once never pays |
| Wind speed | Hourly at 100 m, 2023, Mont Crosin (47.18 N, 7.03 E), scaled to an annual mean of 5.5 m/s | [Open-Meteo](https://open-meteo.com/) historical weather API, ERA5 reanalysis, CC BY 4.0. ERA5 grid cells (~30 km) underestimate ridge-top winds (raw mean 4.5 m/s), so the series is scaled to a mean within the range the Swiss Wind Atlas gives for Jura crests |
| Wind area | 4 km², 60% pasture (roughness 0.1 m), 40% forest (0.8 m) | Assumption |
| Forest cost multipliers | CAPEX ×1.1, one-time CAPEX ×1.2, OPEX ×1.05 | Assumption (clearing, access roads) |
| Turbines | Enercon E-82 E2 (2.3 MW, 108 m hub, pasture only), Vestas V112 (3.45 MW, 119 m), Enercon E-138 EP3 (4.26 MW, 131 m) | Approximate public manufacturer data |
| Costs | CAPEX 2800 / 2600 / 2400 CHF/kW, 1.5 M CHF one-time per turbine type and terrain in which it is built, O&M 60 CHF/kW/a, lifetime 20 / 20 / 25 a, interest 5% | Rough estimates for Switzerland |
| Time resolution | 8760 h, clustered to 50 representative hours (TSAM) | Remove the `rom` call in `main_wind_demo.py` to solve the full year |

## Expected result

| | Full year (8760 h) | Clustered (50 h) |
|---|---|---|
| Built | 13.6 MW Enercon E-138, all on pasture | 13.3 MW Enercon E-138, all on pasture |
| Wind generation | 32.8 GWh/a (2411 full-load hours) | 31.6 GWh/a |
| Grid import / export | 8.9 / 19.2 GWh/a | 9.1 / 18.2 GWh/a |
| Total annual cost | 3.67 M CHF | 3.72 M CHF |
| Solve time (GLPK) | about 3.5 min | about 20 s |

The large-rotor E-138 has the highest yield per franc, so the smaller types are
not built. Pasture is cheaper and its area is not used up, so the forest stays
empty. The size, about three turbines, is an economic optimum: wind is cheaper
than grid electricity, but more expensive than the export price, so building
more would mainly add exports.

## Limitations

- Installed capacity is continuous (kW), so the result can correspond to a
  fractional number of turbines.
- The turbine power curve is idealized (constant power coefficient up to rated
  power) rather than the manufacturer's curve.
- The air density is fixed at its sea-level value (1.225 kg/m³). At the
  Jura crest, about 1200 m above sea level, it is roughly 12% lower, so the
  output is somewhat overestimated.
- Terrain roughness only enters the height extrapolation above the 100 m
  reference height and the turbulence intensity. There is no displacement
  height for the forest canopy, so forest sites come out with a slightly
  *higher* yield than pasture; in this demo the forest cost multipliers
  outweigh that.
- The demand profile is synthetic and daylight saving time is ignored.

## Input data

The three hourly files cover 8760 h (2023, time step 1 = 1 January 00:00 UTC).

- **`inputs/renewables/wind_speed.csv`**: hourly `wind_speed_100m` in m/s from
  the Open-Meteo historical weather API (`archive-api.open-meteo.com`,
  `models=era5`, latitude 47.18, longitude 7.03, 2023-01-01 to 2023-12-31,
  timezone GMT). The raw annual mean of 4.509 m/s was multiplied by 1.2197 to
  give 5.5 m/s, then rounded to 0.01 m/s.
- **`inputs/basic/profiles/demands.csv`**: synthetic. Each hour is the product
  of an hourly shape (weekdays: low at night, peaks around 08:00 and 18:00;
  weekends: lower, with a midday and an evening peak) and a seasonal factor
  1 + 0.18 · cos(2π (day of year − 15) / 365), so winter demand is about 40%
  higher than summer. The series is scaled to 22.5 GWh/a. Local time is taken
  as UTC+1.
- **`inputs/basic/profiles/imports.csv`**: 0.24 CHF/kWh Monday to Friday from
  06:00 to 22:00 local time (UTC+1), 0.18 CHF/kWh otherwise.
