# ms3: synthetic two-stage model

Two-stage copy of `examples/clustering_demo`, made with
`scripts/make_ms_demo.py <repo> <out>`: every S1 profile is duplicated as S2,
time-shifted (same shift for all columns of a file), and the demand, price and
load-shedding profiles of S2 are rescaled and get a few injected spikes, so
that the two stages have different extreme periods. Afterwards, the S2 export
price was set to half the import price to avoid price arbitrage.

Capacities are fixed (as in the demo), so this model shows operation and cost
differences only, not design differences.
