"""Pre-compute (cache) the runs of an experiment in parallel.

usage: run_batch.py <E0|E1|E1b|E1c|E7|E4|all|new|extra> [workers]

The notebooks call romlab.run() for the same runs and then only read the cache.
"""

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import romlab

K_SWEEP = [24, 48, 96, 192, 384, 768, 1460, 2920]
K_EXP = [48, 96, 192, 384, 768, 1460]


def jobs(exp: str):
    j = []
    if exp in ("E0", "E1", "all"):
        for case in ("demo", "ms3", "swissx"):
            j.append((case, "M0", "profiles", 0))
        for case in ("demo", "ms3"):
            j.append((case, "M0", "full", 0))
    if exp in ("E0", "all"):
        for v in ("M1", "M1b", "M2"):
            j.append(("demo", v, "rom", 150))
            j.append(("ms3", v, "rom", 150))
            j.append(("swissx", v, "cluster", 144))
    if exp in ("E1", "all"):
        for k in K_SWEEP:
            for v in ("M1", "M2"):
                j.append(("demo", v, "rom", k))
            for v in ("M1", "M1b", "M2"):
                j.append(("ms3", v, "rom", k))
                j.append(("swissx", v, "cluster", k))
    if exp in ("E1b", "all", "new"):
        j.append(("pv_bat", "M0", "profiles", 0))
        j.append(("pv_bat", "M0", "full", 0))
        for k in K_EXP:
            for v in ("M1", "M2"):
                j.append(("pv_bat", v, "rom", k))
                j.append(("pv_bat", v, "regret", k))
    if exp in ("E7", "all", "new"):
        for case in ("demo_nostor", "pv_bat_nostor"):
            j.append((case, "M0", "profiles", 0))
            j.append((case, "M0", "full", 0))
        for k in K_EXP:
            j.append(("demo_nostor", "M2", "rom", k))
            j.append(("pv_bat_nostor", "M2", "rom", k))
            j.append(("pv_bat_nostor", "M2", "regret", k))
    if exp in ("E4", "all", "new"):
        for k in K_EXP:
            for v in ("M3", "M4"):
                j.append(("pv_bat", v, "rom", k))
                j.append(("pv_bat", v, "regret", k))
                j.append(("demo", v, "rom", k))
                j.append(("swissx", v, "cluster", k))
    if exp in ("E1c", "all", "extra"):
        # backup-price sensitivity of the M1/M2 regret ranking (1.0 instead of 5.0 CHF/kWh)
        j.append(("pv_bat_bak1", "M0", "profiles", 0))
        j.append(("pv_bat_bak1", "M0", "full", 0))
        for k in K_EXP:
            for v in ("M1", "M2"):
                j.append(("pv_bat_bak1", v, "rom", k))
                j.append(("pv_bat_bak1", v, "regret", k))
    if exp in ("E4", "all", "extra"):
        # M4 with 3 h blocks
        j.append(("pv_bat", "M4", "rom", 2920))
        j.append(("pv_bat", "M4", "regret", 2920))
        j.append(("demo", "M4", "rom", 2920))
        j.append(("swissx", "M4", "cluster", 2920))
    return list(dict.fromkeys(j))


def main() -> None:
    exp = sys.argv[1]
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    todo = jobs(exp)
    phases = [
        [j for j in todo if j[2] != "regret"],
        [j for j in todo if j[2] == "regret"],
    ]
    print(f"{len(todo)} runs, {workers} workers", flush=True)
    t0 = time.time()
    for phase in phases:
        if not phase:
            continue
        with ThreadPoolExecutor(workers) as pool:
            futs = {pool.submit(romlab.run, *job): job for job in phase}
            for f in as_completed(futs):
                job = futs[f]
                try:
                    f.result()
                    print(f"[{time.time() - t0:7.0f}s] ok   {job}", flush=True)
                except Exception as exc:  # noqa: BLE001
                    print(f"[{time.time() - t0:7.0f}s] FAIL {job}: {str(exc)[-600:]}", flush=True)


if __name__ == "__main__":
    main()
