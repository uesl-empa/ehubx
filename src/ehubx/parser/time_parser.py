from ehubx.core import logging
from ehubx.data.time_data import Times, TimeId

# Literals
LOG_MODULE_STR: str = "pars/time"


def parse(num_times_horizon: int) -> Times:
    times = Times()
    for t in range(1, num_times_horizon + 1):
        times.add_id(TimeId(t))
    _log(times)
    return times


def _log(times: Times) -> None:
    logging.log_file((f"Parsed time horizon with {times.num_horizon_ts} "
                      "horizon time steps"), module=LOG_MODULE_STR)
