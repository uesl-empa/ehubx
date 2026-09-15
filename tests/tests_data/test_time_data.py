import pytest

from ehubx.core.common import HOURS_PER_YEAR
from ehubx.data.time_data import (
    DEF_ANNUALIZE_HORIZON,
    DEF_WEIGHT,
    ExceptionKey,
    TimeId,
    Times,
)
from ehubx.data.stage_data import StageId, Stages
from ehubx.data import exceptions as data_exceptions


def test_add_duplicate_time_id_raises_duplicate_id_exception_and_key():
    times = Times()
    t = TimeId(1)
    times.add_id(t)

    with pytest.raises(data_exceptions.DuplicateIdException) as excinfo:
        times.add_id(t)

    exc = excinfo.value
    assert exc.key == ExceptionKey.ID_ADD.value
    assert exc.index == t


def test_horizon_ids_ordering_first_last_and_is_clustered_and_clear():
    times = Times()
    times.add_horizon_id(TimeId(3))
    times.add_horizon_id(TimeId(1))
    times.add_horizon_id(TimeId(2))

    ordered = [t.key_as_int for t in times.ids_horizon_in_order]
    assert ordered == [1, 2, 3]

    # Add ids for only two of the horizon ids -> clustered should be True
    times.add_id(TimeId(1))
    times.add_id(TimeId(2))
    assert times.is_clustered

    assert times.first_horizon_id.key_as_int == 1
    assert times.last_horizon_id.key_as_int == 3

    times.clear_horizon_ids()
    assert len(times.ids) == 0
    assert len(times.ids_horizon) == 0


def test_get_set_weight_and_unknown_time_raises_unknownidexception():
    times = Times()
    s = StageId("s1")
    t = TimeId(10)
    times.add_id(t)

    # Default weight when not set
    assert times.get_weight(s, t) == DEF_WEIGHT

    # Set and get
    times.set_weight(s, t, 5.0)
    assert times.get_weight(s, t) == 5.0

    # Unknown time id -> UnknownIdException with expected key
    unknown_t = TimeId(99)
    with pytest.raises(data_exceptions.UnknownIdException) as excinfo:
        times.set_weight(s, unknown_t, 1.0)
    assert excinfo.value.key == ExceptionKey.WEIGHT_SET.value

    with pytest.raises(data_exceptions.UnknownIdException) as excinfo2:
        times.get_weight(s, unknown_t)
    assert excinfo2.value.key == ExceptionKey.WEIGHT_GET.value


def test_get_cluster_ts_behaviour_and_exceptions():
    times = Times()
    s = StageId("stage")

    # not clustered -> returns input
    t = TimeId(1)
    times.add_id(t)
    times.add_horizon_id(t)
    assert times.get_cluster_ts(s, t) == t

    # unknown horizon id -> UnknownIdException with expected key
    unknown_hor = TimeId(999)
    with pytest.raises(data_exceptions.UnknownIdException) as excinfo:
        times.get_cluster_ts(s, unknown_hor)
    assert excinfo.value.key == ExceptionKey.CLUSTERTS_GET.value

    # clustered but mapping missing -> DataException with expected key
    # make horizon larger than ids
    times = Times()
    times.add_horizon_id(TimeId(1))
    times.add_horizon_id(TimeId(2))
    times.add_id(TimeId(1))  # now num_horizon_ts=2, num_ts=1 -> clustered

    with pytest.raises(data_exceptions.DataException) as excinfo2:
        times.get_cluster_ts(s, TimeId(2))
    assert excinfo2.value.key == ExceptionKey.CLUSTERTS_GET.value


def test_validate_weight_fails_for_unknown_stage_and_negative_weight():
    times = Times()
    s = StageId("s_missing")
    t = TimeId(5)
    times.add_id(t)

    # weight references unknown stage -> validation error
    times.set_weight(s, t, 3.0)
    stages = Stages()  # s not added
    with pytest.raises(data_exceptions.DataException) as excinfo:
        times.validate(stages)
    assert excinfo.value.key == ExceptionKey.WEIGHT_VAL.value
    assert s in excinfo.value.indices
    assert t in excinfo.value.indices

    # negative weight -> validation error
    stages = Stages()
    stages.add_id(s)
    times.set_weight(s, t, -1.0)
    with pytest.raises(data_exceptions.DataException) as excinfo2:
        times.validate(stages)
    assert excinfo2.value.key == ExceptionKey.WEIGHT_VAL.value


def test_validate_cluster_ts_fails_for_unknown_stage():
    times = Times()
    s = StageId("s_missing")
    t = TimeId(7)
    t_hor = TimeId(8)

    # prepare ids so set_cluster_ts succeeds
    times.add_id(t)
    times.add_horizon_id(t_hor)

    times.set_cluster_ts(s, t, t_hor)

    stages = Stages()  # s not added
    with pytest.raises(data_exceptions.DataException) as excinfo:
        times.validate(stages)
    assert excinfo.value.key == ExceptionKey.CLUSTERTS_VAL.value
    assert s in excinfo.value.indices
    assert t_hor in excinfo.value.indices


def _times_with_ids(num_ids: int) -> Times:
    times = Times()
    for i in range(1, num_ids + 1):
        times.add_id(TimeId(i))
    return times


def test_annualize_horizon_is_off_by_default_and_keeps_raw_weights():
    times = _times_with_ids(4)
    s = StageId("s1")

    assert DEF_ANNUALIZE_HORIZON is False
    assert times.annualize_horizon is False
    assert times.annualization_factor == 1.0

    times.set_weight(s, TimeId(1), 2.0)
    assert times.get_weight(s, TimeId(1)) == 2.0
    # 2 + 1 + 1 + 1: the raw weights sum up to the horizon length
    assert times.get_weight_sum(s) == pytest.approx(5.0)


def test_annualize_horizon_scales_weights_to_hours_per_year():
    times = _times_with_ids(4)
    s = StageId("s1")
    times.annualize_horizon = True

    assert times.annualization_factor == pytest.approx(HOURS_PER_YEAR / 4)
    assert times.get_weight(s, TimeId(1)) == pytest.approx(HOURS_PER_YEAR / 4)
    assert times.get_weight_sum(s) == pytest.approx(HOURS_PER_YEAR)

    # A raw weight set by hand is scaled as well
    times.set_weight(s, TimeId(1), 2.0)
    assert times.get_weight(s, TimeId(1)) == pytest.approx(2 * HOURS_PER_YEAR / 4)

    # Switching off restores the raw weights
    times.annualize_horizon = False
    assert times.get_weight(s, TimeId(1)) == 2.0


def test_annualize_horizon_is_a_no_op_for_a_full_year_horizon():
    times = _times_with_ids(int(HOURS_PER_YEAR))
    s = StageId("s1")
    times.annualize_horizon = True

    assert times.annualization_factor == pytest.approx(1.0)
    assert times.get_weight(s, TimeId(1)) == DEF_WEIGHT
    assert times.get_weight_sum(s) == pytest.approx(HOURS_PER_YEAR)


def test_annualize_horizon_with_clustered_weights_sums_to_hours_per_year():
    # 4 horizon ids clustered into 2 ids with cluster sizes 3 and 1
    times = Times()
    s = StageId("s1")
    for i in range(1, 5):
        times.add_horizon_id(TimeId(i))
    times.add_id(TimeId(1))
    times.add_id(TimeId(2))
    times.set_weight(s, TimeId(1), 3.0)
    times.set_weight(s, TimeId(2), 1.0)
    assert times.is_clustered
    assert times.get_weight_sum(s) == pytest.approx(4.0)

    times.annualize_horizon = True
    assert times.get_weight(s, TimeId(1)) == pytest.approx(3 * HOURS_PER_YEAR / 4)
    assert times.get_weight(s, TimeId(2)) == pytest.approx(HOURS_PER_YEAR / 4)
    assert times.get_weight_sum(s) == pytest.approx(HOURS_PER_YEAR)


def test_annualization_factor_follows_horizon_changes():
    # Mimics the cut-time ROM: horizon ids are cleared and fewer ids re-added
    times = Times()
    s = StageId("s1")
    times.annualize_horizon = True
    # No ids yet: no division by zero
    assert times.annualization_factor == 1.0

    for i in range(1, 5):
        times.add_id(TimeId(i))
    assert times.annualization_factor == pytest.approx(HOURS_PER_YEAR / 4)

    times.clear_horizon_ids()
    times.add_id(TimeId(1))
    times.add_id(TimeId(2))
    assert times.annualization_factor == pytest.approx(HOURS_PER_YEAR / 2)
    assert times.get_weight_sum(s) == pytest.approx(HOURS_PER_YEAR)
