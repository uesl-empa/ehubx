"""Pre-compute (cache) the runs of an experiment in parallel.

usage: run_batch.py <E0|E1|all> [workers]

The notebooks call romlab.run() for the same runs and then only read the cache.
"""

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import romlab

K_SWEEP = [24, 48, 96, 192, 384, 768, 1460, 2920]


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
    return list(dict.fromkeys(j))


def main() -> None:
    exp = sys.argv[1]
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    todo = jobs(exp)
    print(f"{len(todo)} runs, {workers} workers", flush=True)
    t0 = time.time()
    with ThreadPoolExecutor(workers) as pool:
        futs = {pool.submit(romlab.run, *job): job for job in todo}
        for f in as_completed(futs):
            job = futs[f]
            try:
                f.result()
                print(f"[{time.time() - t0:7.0f}s] ok   {job}", flush=True)
            except Exception as exc:  # noqa: BLE001
                print(f"[{time.time() - t0:7.0f}s] FAIL {job}: {str(exc)[-600:]}", flush=True)


if __name__ == "__main__":
    main()
