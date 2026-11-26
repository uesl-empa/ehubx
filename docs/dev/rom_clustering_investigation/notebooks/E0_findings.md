## Findings (E0)

**Structure.** At these targets all three methods give the same number of
clustered steps (178 for demo/ms3, 185 for SwissX), every step has members,
and all weights sum to 8760. The phantom steps of issue 2 do not occur with
these data; they need near-identical extreme hours (see the unit test).

**Totals.** Only M2 keeps the weighted sum of every series exact (≤ 3e-16).
M1 and M1b have mean errors of 0.07–0.2 % and maxima of 1 % (demo/ms3) and
up to **2.8 %** (M1b, SwissX S4).

**Peaks.** M1 (`main`) loses the extremes of all stages but one in multi-stage
models: in ms3 the clustered peak is up to 41 % of the range below the true
peak, in SwissX up to 52 % (stages S1 and S4). M1b fixes this (errors ≤ 1e-6,
from tsam's rounding), M2 keeps peaks and minima exactly. Single stage (demo):
all methods keep the peaks.

**Shape.** The duration-curve error (`dc_nrmse`) and the error of the rebuilt
hourly profile (`chr_nrmse`) are about 3–9 % *higher* for M2 than for M1. M1
pulls near-peak hours into the extreme clusters, which shapes the high end of
the duration curve better but biases the totals; M2 keeps totals exact and
puts these hours in regular clusters. See E1: the gap closes as K grows.

**Model results (demo, ms3).** Cost objective vs full horizon: demo +5.8 %
(M1, M1b) → +5.6 % (M2); ms3 +6.5 % (M1) / +6.5 % (M1b) → +6.3 % (M2).
Demand-driven imports match the full model exactly with M2 (E5, E6, H2-E1),
while M1 is off by 0.3 %. Load shedding is 3–4 % too high and the E2 import
1 % too high with all methods. Note: all capacities in demo/ms3 are fixed
(identical in every run), so these models cannot show design differences — we
need a model with free capacities for that.

**Main point.** The differences *between* methods (≤ 0.3 percentage points
of objective) are much smaller than the error that all of them share
(≈ 6 %). The remaining error is not caused by the details of the clustering
fixed in #57; see E1.
