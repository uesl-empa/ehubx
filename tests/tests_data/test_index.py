"""Tests for ehubx.data.index
"""

import pytest

from ehubx.data.index import Index, IndexKind


def test_indexkind_values() -> None:
    """IndexKind enum members have the expected string values."""
    expected = {
        IndexKind.STAGE: "stage",
        IndexKind.HUB: "hub",
        IndexKind.NETLINK: "net_link",
        IndexKind.TECH: "tech",
        IndexKind.NETTECH: "net tech",
        IndexKind.EC: "ec",
        IndexKind.LOADSHIFT: "load shift",
        IndexKind.TIME: "time",
        IndexKind.PARETOPOINT: "pareto_point",
        IndexKind.ATESSCHEDULE: "ates_schedule",
    }
    for kind, val in expected.items():
        assert kind.value == val


def test_index_properties_and_repr() -> None:
    """Index exposes kind, key and string representation as expected."""
    idx = Index(IndexKind.HUB, "hub_1")
    assert idx.kind == IndexKind.HUB
    assert idx.kind_as_str == "hub"
    assert idx.key == "hub_1"
    assert repr(idx) == "hub_1"


def test_equality_and_hashing() -> None:
    """Equality is by (kind, key) and indices are hashable."""
    a = Index(IndexKind.TECH, "t1")
    b = Index(IndexKind.TECH, "t1")
    c = Index(IndexKind.TECH, "t2")
    d = Index(IndexKind.HUB, "t1")

    assert a == b
    assert a != c
    assert a != d
    assert a != "t1"  # different type

    assert hash(a) == hash(b)

    mapping = {a: "value"}
    assert mapping[b] == "value"


def test_non_str_key_repr_typeerror() -> None:
    """If a non-str key is used, __repr__ will not return str and repr() should raise TypeError.

    This documents the current (arguably lax) behavior of the class: it doesn't
    enforce key's type on construction but repr() expects a string return value
    and so Python raises a TypeError when that contract is violated.
    """
    idx = Index(IndexKind.HUB, 123)
    assert idx.key == 123
    with pytest.raises(TypeError):
        _ = repr(idx)
