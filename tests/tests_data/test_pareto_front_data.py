import pytest
from contextlib import contextmanager

from ehubx.data.pareto_front_data import ParetoFront, ParetoId, ExceptionKey
from ehubx.data import exceptions


@contextmanager
def raises_with_key(exc_type, expected_key):
    with pytest.raises(exc_type) as excinfo:
        yield excinfo
    assert excinfo.value.key == expected_key


def test_ids_empty_initially():
    pf = ParetoFront()
    assert pf.ids == []


def test_set_and_get_point_and_ids_ordering():
    pf = ParetoFront()

    p_high = ParetoId(10)
    p_low = ParetoId(1)

    pf.set_point(p_high, 10.0, 20.0)
    pf.set_point(p_low, -5.0, 3.2)

    ids = pf.ids
    assert [i.pos for i in ids] == [1, 10]

    assert pf.get_point(p_high) == (10.0, 20.0)
    assert pf.get_point(p_low) == (-5.0, 3.2)


def test_get_point_unknown_id_raises_missing_key():
    pf = ParetoFront()
    missing = ParetoId(42)
    with raises_with_key(exceptions.MissingIdException, ExceptionKey.POINT_GET.value):
        pf.get_point(missing)
