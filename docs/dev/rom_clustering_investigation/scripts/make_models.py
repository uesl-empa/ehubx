"""Generate synthetic test models for E1b, E7, and E4 under models/.

Models created:
  - pv_bat:        1-stage free-capacity PV + Battery + Heat Pump + Boiler + TES
  - pv_bat_nostor: same as pv_bat without Bat and TES
  - demo_nostor:   copy of examples/clustering_demo without EBM storage (X2)
"""

import csv
import os
import shutil

import numpy as np


HERE = os.path.dirname(os.path.abspath(__file__))
INV = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(INV, "..", "..", ".."))
MODELS_DIR = os.path.join(INV, "models")


def _write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf8", newline="\n") as f:
        f.write(text)


def _write_csv(path: str, rows) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf8", newline="") as f:
        csv.writer(f).writerows(rows)


def _ar1(rng: np.random.Generator, n: int, phi: float, sigma: float) -> np.ndarray:
    x = np.zeros(n)
    for t in range(1, n):
        x[t] = phi * x[t - 1] + sigma * rng.normal()
    return x


def _build_pv_bat_profiles(seed: int = 42):
    rng = np.random.default_rng(seed)
    n = 8760
    t = np.arange(n)
    hour = t % 24
    day = t // 24
    dow = day % 7

    # Seasonal envelope: +1 in mid-January (day 15), -1 in mid-July
    winter = np.cos(2 * np.pi * (day - 15) / 365.0)
    summer = -winter

    # 1. Solar irradiation [kW/m^2]: seasonal day length + clear-sky bell + clouds
    day_len = 12.0 + 3.5 * summer
    sunrise = 12.0 - day_len / 2.0
    sunset = 12.0 + day_len / 2.0
    in_day = (hour >= sunrise) & (hour <= sunset)
    solar_angle = np.where(in_day, np.sin(np.pi * (hour - sunrise) / day_len), 0.0)
    clear_sky = (0.48 + 0.47 * (summer + 1) / 2.0) * np.maximum(0.0, solar_angle)
    cloud_noise = _ar1(rng, n, phi=0.88, sigma=0.14)
    cloud_factor = np.clip(0.82 + cloud_noise, 0.20, 1.05)
    solar = np.where(in_day, clear_sky * cloud_factor, 0.0)

    # 2. Electricity demand [kW]: diurnal double peak + winter lift + weekday factor
    morning = np.exp(-0.5 * ((hour - 8.5) / 2.0) ** 2)
    evening = np.exp(-0.5 * ((hour - 19.5) / 2.3) ** 2)
    midday = np.exp(-0.5 * ((hour - 13.5) / 3.0) ** 2)
    wkday = np.where(dow < 5, 1.05, 0.90)
    el_noise = _ar1(rng, n, phi=0.75, sigma=3.5)
    el_dem = (28.0 + 18.0 * morning + 28.0 * evening + 10.0 * midday + 8.0 * winter) * wkday + el_noise
    el_dem = np.clip(el_dem, 18.0, 115.0)

    # 3. Heat demand [kW]: winter heating + morning/evening peaks + 5-day cold snap
    heat_season = np.clip((winter + 0.25) / 1.25, 0.0, 1.0) ** 1.3
    heat_diurnal = 0.72 + 0.32 * morning + 0.28 * evening
    cold_snap = np.exp(-0.5 * ((day - 22.0) / 2.0) ** 2)
    heat_noise = _ar1(rng, n, phi=0.80, sigma=2.5)
    heat_dem = np.where(
        heat_season > 0.02,
        (78.0 * heat_season * heat_diurnal + 45.0 * cold_snap + heat_noise),
        0.0,
    )
    heat_dem = np.clip(heat_dem, 0.0, 155.0)

    # 4. Heat pump COP [kWh/kWh]: warmer in summer & afternoon, lower in cold snap
    temp_proxy = 8.0 + 11.0 * summer + 3.5 * np.sin(2 * np.pi * (hour - 9) / 24.0) - 9.0 * cold_snap
    hp_cop = np.clip(2.6 + 0.08 * temp_proxy + 0.12 * _ar1(rng, n, phi=0.7, sigma=0.3), 1.9, 4.6)

    # 5. Grid electricity price [CHF/kWh]: higher during evening/winter/low-solar
    el_price = (
        0.13
        + 0.06 * winter
        + 0.09 * evening
        + 0.05 * morning
        - 0.07 * np.clip(solar, 0.0, 1.0)
        + 0.08 * cold_snap
        + 0.015 * _ar1(rng, n, phi=0.75, sigma=0.8)
    )
    el_price = np.clip(el_price, 0.05, 0.45)

    return solar, el_dem, heat_dem, hp_cop, el_price


def make_pv_bat(name: str = "pv_bat", include_storage: bool = True) -> str:
    root = os.path.join(MODELS_DIR, name, "inputs")
    if os.path.exists(os.path.join(MODELS_DIR, name)):
        shutil.rmtree(os.path.join(MODELS_DIR, name))

    solar, el_dem, heat_dem, hp_cop, el_price = _build_pv_bat_profiles()

    _write_text(
        os.path.join(root, "basic", "stages.yaml"),
        "system_params:\n"
        "  interest_rate_def: 0.05\n"
        "  num_times_horizon: 8760\n"
        "  currency_unit: CHF\n"
        "  mass_unit: kg\n"
        "  length_unit: m\n\n"
        "stages:\n"
        "- stage_id: S1\n"
        "  start_year: 2025\n",
    )

    _write_text(
        os.path.join(root, "basic", "ecs.yaml"),
        "ecs:\n"
        "- ec_id: El\n  unit: kWh\n"
        "- ec_id: Heat\n  unit: kWh\n"
        "- ec_id: Gas\n  unit: kWh\n"
        "- ec_id: Sol\n  unit: kWh\n",
    )

    _write_text(
        os.path.join(root, "basic", "demands.yaml"),
        "demand_profiles:\n- profiles/demands.csv\n",
    )

    _write_text(
        os.path.join(root, "basic", "imports.yaml"),
        "- stages: S1\n  hubs: H1\n  ec: El\n  profile_path: profiles/imports.csv\n\n"
        "- stages: S1\n  hubs: H1\n  ec: Gas\n  price: 0.11 CHF/kWh\n\n"
        "- stages: S1\n  hubs: H1\n  ec: Sol\n\n"
        "- stages: S1\n  hubs: H1\n  ec: Heat\n  price: 5.0 CHF/kWh\n",
    )

    _write_text(
        os.path.join(root, "basic", "exports.yaml"),
        "- stages: S1\n  hubs: H1\n  ec: El\n  price: 0.02 CHF/kWh\n",
    )

    _write_text(
        os.path.join(root, "basic", "techs.yaml"),
        "techs:\n"
        "- tech_id: PV\n"
        "  type: solar\n"
        "  tech_params:\n"
        "    lifetime: 25 a\n"
        "  costs:\n"
        "    capex_per_cap: 270 CHF/m^2\n"
        "  conversion_params:\n"
        "    in_ecs:\n"
        "    - in_id: Sol\n"
        "      in_part: 1 kWh\n"
        "    out_ecs:\n"
        "    - ec_id: El\n"
        "      out_eff: 0.20 kWh/kWh\n\n"
        "- tech_id: Bat\n"
        "  type: storage\n"
        "  tech_params:\n"
        "    lifetime: 15 a\n"
        "  costs:\n"
        "    capex_per_cap: 130 CHF/kWh\n"
        "  storage_params:\n"
        "    ec: El\n"
        "    charge_max: 0.5 1/h\n"
        "    discharge_max: 0.5 1/h\n"
        "    in_eff: 0.95\n"
        "    out_eff: 0.95\n"
        "    standby_loss: 0.0005 1/h\n"
        "    soc_min: 0.1\n"
        "    soc_max: 0.9\n\n"
        "- tech_id: HP\n"
        "  type: conversion\n"
        "  tech_params:\n"
        "    lifetime: 20 a\n"
        "  costs:\n"
        "    capex_per_cap: 900 CHF/kW\n"
        "  conversion_params:\n"
        "    in_ecs:\n"
        "    - in_id: El\n"
        "      in_part: 1 kWh\n"
        "    out_ecs:\n"
        "    - ec_id: Heat\n"
        "      out_eff: profiles/HP_cop.csv\n\n"
        "- tech_id: Boiler\n"
        "  type: conversion\n"
        "  tech_params:\n"
        "    lifetime: 20 a\n"
        "  costs:\n"
        "    capex_per_cap: 150 CHF/kW\n"
        "  conversion_params:\n"
        "    in_ecs:\n"
        "    - in_id: Gas\n"
        "      in_part: 1 kWh\n"
        "    out_ecs:\n"
        "    - ec_id: Heat\n"
        "      out_eff: 0.90 kWh/kWh\n\n"
        "- tech_id: TES\n"
        "  type: storage\n"
        "  tech_params:\n"
        "    lifetime: 20 a\n"
        "  costs:\n"
        "    capex_per_cap: 35 CHF/kWh\n"
        "  storage_params:\n"
        "    ec: Heat\n"
        "    charge_max: 0.5 1/h\n"
        "    discharge_max: 0.5 1/h\n"
        "    in_eff: 0.98\n"
        "    out_eff: 0.98\n"
        "    standby_loss: 0.005 1/h\n"
        "    soc_min: 0.05\n"
        "    soc_max: 0.95\n",
    )

    if include_storage:
        hubs_yaml = (
            "tech_lists:\n"
            "- tech_list_id: TL1\n"
            "  techs: [PV, Bat, HP, Boiler, TES]\n\n"
            "hubs:\n"
            "- hub_id: H1\n"
            "  allowed_tech_lists: TL1\n"
            "  techs:\n"
            "  - tech_id: Bat\n    tech_params:\n      cap_max: 2000 kWh\n"
            "  - tech_id: HP\n    tech_params:\n      cap_max: 200 kW\n"
            "  - tech_id: Boiler\n    tech_params:\n      cap_max: 200 kW\n"
            "  - tech_id: TES\n    tech_params:\n      cap_max: 1500 kWh\n"
        )
    else:
        hubs_yaml = (
            "tech_lists:\n"
            "- tech_list_id: TL1\n"
            "  techs: [PV, HP, Boiler]\n\n"
            "hubs:\n"
            "- hub_id: H1\n"
            "  allowed_tech_lists: TL1\n"
            "  techs:\n"
            "  - tech_id: HP\n    tech_params:\n      cap_max: 200 kW\n"
            "  - tech_id: Boiler\n    tech_params:\n      cap_max: 200 kW\n"
        )
    _write_text(os.path.join(root, "basic", "hubs.yaml"), hubs_yaml)

    # Empty network files (no multi-hub links needed)
    _write_text(os.path.join(root, "network", "network_links.yaml"), "")
    _write_text(os.path.join(root, "network", "network_techs.yaml"), "")

    # CSV profiles
    dem_rows = [
        ["ec_id", "El", "Heat"],
        ["stage_id", "S1", "S1"],
        ["hub_id", "H1", "H1"],
        ["unit", "kW", "kW"],
    ] + [[i + 1, f"{el_dem[i]:.6f}", f"{heat_dem[i]:.6f}"] for i in range(8760)]
    _write_csv(os.path.join(root, "basic", "profiles", "demands.csv"), dem_rows)

    imp_rows = [
        ["stage_id", "S1"],
        ["hub_id", "H1"],
        ["ec_id", "El"],
        ["profile_key", "price"],
        ["unit", "CHF/kWh"],
    ] + [[i + 1, f"{el_price[i]:.6f}"] for i in range(8760)]
    _write_csv(os.path.join(root, "basic", "profiles", "imports.csv"), imp_rows)

    hp_rows = [
        ["stage_id", "S1"],
        ["tech_id", "HP"],
        ["ec_id", "Heat"],
        ["unit", "kWh/kWh"],
    ] + [[i + 1, f"{hp_cop[i]:.6f}"] for i in range(8760)]
    _write_csv(os.path.join(root, "basic", "profiles", "HP_cop.csv"), hp_rows)

    _write_csv(
        os.path.join(root, "renewables", "solar_areas.csv"),
        [["stage_id", "S1"], ["hub_id", "H1"], ["unit", "m^2"], ["Sol", "3000"]],
    )
    sol_rows = [
        ["stage_id", "S1"],
        ["ec_id", "Sol"],
        ["unit", "kW/m^2"],
    ] + [[i + 1, f"{solar[i]:.6f}"] for i in range(8760)]
    _write_csv(os.path.join(root, "renewables", "solar_irradiation.csv"), sol_rows)

    return os.path.join(MODELS_DIR, name)


def make_demo_nostor() -> str:
    out = os.path.join(MODELS_DIR, "demo_nostor")
    if os.path.exists(out):
        shutil.rmtree(out)
    src = os.path.join(REPO, "examples", "clustering_demo", "inputs")
    dst = os.path.join(out, "inputs")
    shutil.copytree(src, dst)
    _write_text(
        os.path.join(dst, "basic", "hubs.yaml"),
        "tech_lists:\n"
        "- tech_list_id: TL1\n"
        "  techs: [X1, X3, X4]\n\n"
        "hubs:\n"
        "- hub_id: H1\n"
        "  allowed_tech_lists: TL1\n"
        "  techs:\n"
        "  - tech_id: X1\n"
        "    tech_params:\n"
        "      cap_max: 20 kW\n"
        "    conversion_params:\n"
        "      profile_path: profiles/X1_availability.csv\n"
        "  - tech_id: X3\n"
        "    tech_params:\n"
        "      cap_max: 20 kW\n"
        "    heatpump_params:\n"
        "      profile_path: profiles/X3_hp.csv\n"
        "- hub_id: H2\n"
        "  allowed_tech_lists: []\n",
    )
    return out


if __name__ == "__main__":
    p1 = make_pv_bat("pv_bat", include_storage=True)
    p2 = make_pv_bat("pv_bat_nostor", include_storage=False)
    p3 = make_demo_nostor()
    print("Generated:", p1, p2, p3, sep="\n  ")
