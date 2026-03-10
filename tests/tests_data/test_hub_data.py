import pytest

from ehubx.data import exceptions as data_exceptions
from ehubx.data.hub_data import Hubs, HubId, ExceptionKey
from ehubx.data.index import IndexKind


def test_hubid_properties_and_equality():
    h1 = HubId("hub_a")
    h2 = HubId("hub_a")
    h3 = HubId("hub_b")

    # kind and key
    assert h1.kind == IndexKind.HUB
    assert h1.key == "hub_a"

    # equality and hashing
    assert h1 == h2
    assert h1 != h3
    assert len({h1, h2, h3}) == 2


def test_add_and_ids_in_order():
    hubs = Hubs()
    assert hubs.ids == set()
    assert hubs.ids_in_order == []

    h_b = HubId("b")
    h_a = HubId("a")

    hubs.add_id(h_b)
    hubs.add_id(h_a)

    assert h_a in hubs.ids
    assert h_b in hubs.ids

    # ids_in_order should be sorted by key
    assert [h.key for h in hubs.ids_in_order] == ["a", "b"]


def test_add_duplicate_raises_duplicateidexception_and_key():
    hubs = Hubs()
    h = HubId("dup")
    hubs.add_id(h)

    with pytest.raises(data_exceptions.DuplicateIdException) as excinfo:
        hubs.add_id(h)

    exc = excinfo.value
    # Exception key must match the ExceptionKey enum value used in the module
    assert exc.key == ExceptionKey.ID_ADD.value
    # and the duplicated index should be the one we added
    assert exc.index.key == "dup"


def test_check_id_raises_unknownidexception_and_key():
    hubs = Hubs()
    unknown = HubId("unknown")

    with pytest.raises(data_exceptions.UnknownIdException) as excinfo:
        hubs._check_id(unknown, ExceptionKey.ID_ADD)

    exc = excinfo.value
    assert exc.key == ExceptionKey.ID_ADD.value
    assert exc.index.key == "unknown"


def test_check_id_passes_for_known_id():
    hubs = Hubs()
    h = HubId("known")
    hubs.add_id(h)

    # Should not raise
    hubs._check_id(h, ExceptionKey.ID_ADD)
