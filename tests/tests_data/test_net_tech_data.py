import pytest

from contextlib import contextmanager

from ehubx.data.net_tech_data import NetworkTechs, NetTechId, ExceptionKey
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.net_link_data import NetLinkId, NetworkLinks
from ehubx.data.unit import PowerUnit, TimeUnit, DimlessUnit, LengthUnit, CurrencyUnit
from ehubx.data.value import Value
from ehubx.data.exceptions import (
    DataException,
    DuplicateIdException,
    UnknownIdException,
    MissingIdException,
)
from ehubx.data.index import IndexKind


@contextmanager
def raises_with_key(exc_type, expected_key):
    with pytest.raises(exc_type) as excinfo:
        yield excinfo
    assert excinfo.value.key == expected_key


def test_nettechid_properties_and_ids_in_order():
    n1 = NetTechId("n_a")
    n2 = NetTechId("n_a")
    n3 = NetTechId("n_b")

    assert n1.kind == IndexKind.NETTECH
    assert n1.key == "n_a"

    assert n1 == n2
    assert n1 != n3
    assert len({n1, n2, n3}) == 2


def test_add_and_ids_in_order():
    nts = NetworkTechs()
    assert nts.ids == set()
    assert nts.ids_in_order == []

    n_b = NetTechId("b")
    n_a = NetTechId("a")

    nts.add_id(n_b)
    nts.add_id(n_a)

    assert n_a in nts.ids
    assert n_b in nts.ids

    assert [n.key for n in nts.ids_in_order] == ["a", "b"]


def test_add_duplicate_raises_duplicateidexception_and_key():
    nts = NetworkTechs()
    n = NetTechId("dup")
    nts.add_id(n)

    with pytest.raises(DuplicateIdException) as excinfo:
        nts.add_id(n)

    exc = excinfo.value
    assert exc.key == ExceptionKey.ID_ADD.value
    assert exc.index.key == "dup"


def test_check_id_raises_unknownidexception_and_key():
    nts = NetworkTechs()
    unknown = NetTechId("unknown")

    with pytest.raises(UnknownIdException) as excinfo:
        nts._check_id(unknown, ExceptionKey.ID_ADD)

    exc = excinfo.value
    assert exc.key == ExceptionKey.ID_ADD.value
    assert exc.index.key == "unknown"


def test_set_and_get_ec_and_default_units():
    nts = NetworkTechs()
    n = NetTechId("net1")
    nts.add_id(n)

    e = EcId("ec1")
    ecs = Ecs()
    ecs.add_id(e)

    # set ec with an energy unit (kW*h)
    ec_unit = PowerUnit.KW * TimeUnit.H
    nts.set_ec(n, e, ec_unit)

    assert nts.get_ec(n) == e

    # default cap_init unit should be ec_unit / TimeUnit.H -> PowerUnit.KW
    val = nts.get_cap_init(NetLinkId("l1"), n)
    assert val.unit.same_type_as(PowerUnit.KW)

    # default unit_cap_min should be ec_unit / TimeUnit.H
    stages = Stages()
    s = StageId("s1")
    stages.add_id(s)
    unit_cap_min = nts.get_unit_cap_min(s, n)
    assert unit_cap_min.unit.same_type_as(PowerUnit.KW)


def test_lifetime_set_unit_validation_and_negative_validate():
    nts = NetworkTechs()
    n = NetTechId("net2")
    nts.add_id(n)

    # wrong unit
    with raises_with_key(DataException, ExceptionKey.LIFETIME_SET.value):
        nts.set_lifetime(n, Value(10.0, LengthUnit.M))

    # negative lifetime should cause validation to fail
    nts.set_lifetime(n, Value(-5.0, TimeUnit.A))

    with pytest.raises(DataException) as excinfo:
        nts.validate(Stages(), NetworkLinks(), Ecs())
    assert excinfo.value.key == ExceptionKey.LIFETIME_VAL.value


def test_interest_rate_set_unit_validation_and_negative_validate():
    nts = NetworkTechs()
    n = NetTechId("net3")
    nts.add_id(n)

    # wrong unit
    with raises_with_key(DataException, ExceptionKey.INTERESTRATE_SET.value):
        nts.set_interest_rate(n, Value(0.05, TimeUnit.A))

    # negative interest rate should fail validation
    nts.set_interest_rate(n, Value(-0.05))
    with pytest.raises(DataException) as excinfo:
        nts.validate(Stages(), NetworkLinks(), Ecs())
    assert excinfo.value.key == ExceptionKey.INTERESTRATE_VAL.value


def test_unit_cap_min_set_unit_validation():
    nts = NetworkTechs()
    n = NetTechId("net4")
    nts.add_id(n)

    e = EcId("ec2")
    ec_unit = PowerUnit.KW * TimeUnit.H
    nts.set_ec(n, e, ec_unit)

    stages = Stages()
    s = StageId("s2")
    stages.add_id(s)

    # wrong unit
    with raises_with_key(DataException, ExceptionKey.UNITCAPMIN_SET.value):
        nts.set_unit_cap_min(s, n, Value(1.0, DimlessUnit()))


def test_trans_decay_unit_and_negative_validate():
    nts = NetworkTechs()
    n = NetTechId("net5")
    nts.add_id(n)

    stages = Stages()
    s = StageId("s3")
    stages.add_id(s)

    # wrong unit
    with raises_with_key(DataException, ExceptionKey.TRANSDECAY_SET.value):
        nts.set_trans_decay(s, n, Value(0.1, DimlessUnit()))

    # negative value should fail on validate
    nts.set_trans_decay(s, n, Value(-1.0, DimlessUnit() / LengthUnit.M))
    with pytest.raises(DataException) as excinfo:
        nts.validate(stages, NetworkLinks(), Ecs())
    assert excinfo.value.key == ExceptionKey.TRANSDECAY_VAL.value


def test_validate_unknown_ec_raises_ec_val_key():
    nts = NetworkTechs()
    n = NetTechId("net6")
    nts.add_id(n)

    e = EcId("ec_unknown")
    # set ec to an ec that is not present in Ecs
    nts.set_ec(n, e, PowerUnit.KW * TimeUnit.H)

    with pytest.raises(DataException) as excinfo:
        nts.validate(Stages(), NetworkLinks(), Ecs())
    assert excinfo.value.key == ExceptionKey.EC_VAL.value


def test_missing_getters_raise_missingid_and_keys():
    nts = NetworkTechs()
    n = NetTechId("missing_gets")
    nts.add_id(n)

    with raises_with_key(MissingIdException, ExceptionKey.EC_GET.value):
        nts.get_ec(n)

    with raises_with_key(MissingIdException, ExceptionKey.LIFETIME_GET.value):
        nts.get_lifetime(n)

    with raises_with_key(MissingIdException, ExceptionKey.INTERESTRATE_GET.value):
        nts.get_interest_rate(n)


def test_unit_cap_min_set_and_get_valid():
    nts = NetworkTechs()
    n = NetTechId("net_ucm")
    nts.add_id(n)

    e = EcId("ec3")
    ec_unit = PowerUnit.KW * TimeUnit.H
    nts.set_ec(n, e, ec_unit)

    stages = Stages()
    s = StageId("s_ucm")
    stages.add_id(s)

    v = Value(2.5, ec_unit / TimeUnit.H)
    nts.set_unit_cap_min(s, n, v)

    got = nts.get_unit_cap_min(s, n)
    assert got.to_float(ec_unit / TimeUnit.H) == pytest.approx(2.5)


def test_one_time_capex_and_opex_and_opex_per_energy_unit_validation():
    nts = NetworkTechs()
    n = NetTechId("net_costs")
    nts.add_id(n)

    stages = Stages()
    s = StageId("s_costs")
    stages.add_id(s)

    with raises_with_key(DataException, ExceptionKey.ONETIMECAPEX_SET.value):
        nts.set_one_time_capex(s, n, Value(1.0, DimlessUnit()))

    with raises_with_key(DataException, ExceptionKey.ONETIMEOPEX_SET.value):
        nts.set_one_time_opex(s, n, Value(1.0, DimlessUnit()))

    # opex_per_energy uses a default unit derived from the ec unit, so set an ec
    e = EcId("ec_costs")
    nts.set_ec(n, e, PowerUnit.KW * TimeUnit.H)

    with raises_with_key(DataException, ExceptionKey.OPEXPERENERGY_SET.value):
        nts.set_opex_per_energy(s, n, Value(1.0, DimlessUnit()))


def test_cap_init_and_age_init_validate_unknown_link_keys():
    nts = NetworkTechs()
    n = NetTechId("net_init")
    nts.add_id(n)

    e = EcId("ec_init")
    ec_unit = PowerUnit.KW * TimeUnit.H
    nts.set_ec(n, e, ec_unit)

    # set cap_init for a link that is not present in NetworkLinks
    li1 = NetLinkId("missing_link1")
    nts.set_cap_init(li1, n, Value(5.0, ec_unit / TimeUnit.H))

    # cap_init should raise when link unknown
    ecs = Ecs()
    ecs.add_id(e)
    with raises_with_key(DataException, ExceptionKey.CAPINIT_VAL.value):
        nts.validate(Stages(), NetworkLinks(), ecs)

    # make cap_init valid by adding link li1 to NetworkLinks
    net_links = NetworkLinks()
    net_links.add_id(li1)

    # Now set age_init for a different missing link li2 to trigger AGEINIT_VAL
    li2 = NetLinkId("missing_link2")
    nts.set_age_init(li2, n, Value(2.0, TimeUnit.A))

    with raises_with_key(DataException, ExceptionKey.AGEINIT_VAL.value):
        nts.validate(Stages(), net_links, ecs)


def test_allowed_stages_and_allowed_net_links_validation():
    nts = NetworkTechs()
    n = NetTechId("net_allowed")
    nts.add_id(n)

    s = StageId("s_unknown")
    nts.add_allowed_stage(s, n)

    # Unknown stage should trigger ALLOWEDSTAGES_VAL
    with raises_with_key(DataException, ExceptionKey.ALLOWEDSTAGES_VAL.value):
        nts.validate(Stages(), NetworkLinks(), Ecs())

    # Make the stage known so allowed_stages passes and allowed_net_links can be tested
    stages = Stages()
    stages.add_id(s)

    li = NetLinkId("l_unknown")
    nts.add_allowed_net_link(li, n)

    # Now unknown net_link should trigger ALLOWEDNETLINKS_VAL
    with raises_with_key(DataException, ExceptionKey.ALLOWEDNETLINKS_VAL.value):
        nts.validate(stages, NetworkLinks(), Ecs())


def test_trans_decay_set_get_success():
    nts = NetworkTechs()
    n = NetTechId("net_td_ok")
    nts.add_id(n)

    stages = Stages()
    s = StageId("s_td_ok")
    stages.add_id(s)

    v = Value(0.02, DimlessUnit() / LengthUnit.M)
    nts.set_trans_decay(s, n, v)

    got = nts.get_trans_decay(s, n)
    assert got == v
