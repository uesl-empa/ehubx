"""Build a 2-stage copy of examples/clustering_demo in the scratchpad.

Stage S2 gets profiles derived from S1 but deliberately different
(time-shifted, rescaled, with a few injected spikes) so that the two stages
have different extreme periods.
"""

import csv
import os
import re
import shutil
import sys

import numpy as np

REPO = sys.argv[1]
OUT = sys.argv[2]
SRC = os.path.join(REPO, "examples", "clustering_demo", "inputs")
DST = os.path.join(OUT, "inputs")

if os.path.exists(OUT):
    shutil.rmtree(OUT)
shutil.copytree(SRC, DST)

# stages.yaml: add S2
p = os.path.join(DST, "basic", "stages.yaml")
txt = open(p, encoding="utf8").read()
txt = txt.rstrip() + "\n- stage_id: S2\n  start_year: 2035\n"
open(p, "w", encoding="utf8").write(txt)

# all yamls: stages: S1 -> stages: [S1, S2]
for root, _, files in os.walk(DST):
    for f in files:
        if f.endswith(".yaml") and f != "stages.yaml":
            fp = os.path.join(root, f)
            t = open(fp, encoding="utf8").read()
            t2 = re.sub(r"stages:\s*S1\s*$", "stages: [S1, S2]", t, flags=re.M)
            open(fp, "w", encoding="utf8").write(t2)

rng = np.random.default_rng(0)


def transform(vals: np.ndarray, col_idx: int, file_idx: int, perturb: bool) -> np.ndarray:
    # same shift for all columns of a file (keeps e.g. heat-pump temperatures
    # consistent); rescale and inject spikes only for demand/price-like files
    shift = 24 * 30 * (file_idx + 1) + 7 * file_idx
    out = np.roll(vals, shift)
    if perturb and np.ptp(vals) > 0:
        out = out * (1.0 + 0.1 * (col_idx % 3))
        idx = rng.choice(len(vals), size=3, replace=False)
        out[idx] = out[idx] + 0.5 * np.ptp(vals)
    return out


# profile csvs: duplicate every S1 column as S2
PERTURB = ("demands.csv", "imports.csv", "exports.csv", "load_shedding.csv")
file_idx = -1
for root, _, files in sorted(os.walk(DST)):
    for f in sorted(files):
        if not f.endswith(".csv") or "renewables" in root:
            continue
        fp = os.path.join(root, f)
        rows = list(csv.reader(open(fp, encoding="utf8")))
        # header rows: first col is not an int
        n_head = 0
        for r in rows:
            try:
                int(r[0])
                break
            except ValueError:
                n_head += 1
        stage_row = [i for i in range(n_head) if rows[i][0] == "stage_id"]
        if not stage_row:
            continue
        sr = stage_row[0]
        s1_cols = [j for j, v in enumerate(rows[sr]) if v == "S1"]
        if not s1_cols:
            continue
        data = np.array([[float(r[j]) for j in s1_cols] for r in rows[n_head:]])
        file_idx += 1
        new = np.column_stack([transform(data[:, k], k, file_idx, f in PERTURB) for k in range(len(s1_cols))])
        for i in range(n_head):
            extra = [("S2" if i == sr else rows[i][j]) for j in s1_cols]
            rows[i] = rows[i] + extra
        for i, r in enumerate(rows[n_head:]):
            rows[n_head + i] = r + [f"{v:.10g}" for v in new[i]]
        with open(fp, "w", newline="", encoding="utf8") as fh:
            csv.writer(fh).writerows(rows)
        print(f"{f}: duplicated {len(s1_cols)} S1 column(s) as S2")
