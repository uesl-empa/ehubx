import pytest
from unittest.mock import patch

from ehubx.data import exceptions as data_exceptions
from ehubx.data.time_data import ExceptionKey as TimeExcKey, TimeId
from ehubx.parser import time_parser


def test_parse_returns_times_with_expected_ids_and_logs():
    with patch("ehubx.core.logging.log_file") as mock_log_file:
        times = time_parser.parse(3)

    assert [t.key_as_int for t in times.ids_in_order] == [1, 2, 3]
    assert [t.key_as_int for t in times.ids_horizon_in_order] == [1, 2, 3]
    assert times.num_horizon_ts == 3
    mock_log_file.assert_called_once_with(
        "Parsed time horizon with 3 horizon time steps",
        module=time_parser.LOG_MODULE_STR,
    )


def test_parse_zero_horizon_logs_empty():
    with patch("ehubx.core.logging.log_file") as mock_log_file:
        times = time_parser.parse(0)

    assert times.num_horizon_ts == 0
    assert len(times.ids) == 0
    mock_log_file.assert_called_once_with(
        "Parsed time horizon with 0 horizon time steps",
        module=time_parser.LOG_MODULE_STR,
    )
