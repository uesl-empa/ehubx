import pytest
from contextlib import contextmanager

from ehubx.data.stor_tech_data import StorageTechs, ExceptionKey, DEF_INEFF, DEF_CHARGEMAX
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.unit import DimlessUnit, TimeUnit
from ehubx.data.value import Value
from ehubx.data import exceptions


@contextmanager
def raises_with_key(exc_type, expected_key):
    with pytest.raises(exc_type) as excinfo:
        yield excinfo
    assert excinfo.value.key == expected_key


def make_basic_env():
    st = StorageTechs()
    t = TechId("t1")
    s = StageId("s1")
    h = HubId("h1")
    stages = Stages()
    stages.add_id(s)
    hubs = Hubs()
    hubs.add_id(h)
    techs = Techs()
    techs.add_id(t)
    ecs = Ecs()
    return st, t, s, h, stages, hubs, techs, ecs


def test_add_id_duplicate_raises_with_key():
    st, t, *_ = make_basic_env()
    st.add_id(t)
    with raises_with_key(exceptions.DuplicateIdException, ExceptionKey.ID_ADD.value):
        st.add_id(t)


def test_ec_get_set_and_validate_keys():
    st, t, s, h, stages, hubs, techs, ecs = make_basic_env()

    # Unknown id -> UnknownIdException
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.EC_GET.value):
        st.get_ec(t)

    # Add id -> missing value raises MissingIdException
    st.add_id(t)
    with raises_with_key(exceptions.MissingIdException, ExceptionKey.EC_GET.value):
        st.get_ec(t)

    # Set ec and get works
    e = EcId("e1")
    st.set_ec(t, e)
    assert st.get_ec(t) == e

    # Validate with ecs missing ec should raise EC_VAL
    with raises_with_key(exceptions.DataException, ExceptionKey.EC_VAL.value):
        st.validate(stages, hubs, ecs, techs)

    # Add ec and validate should pass
    ecs.add_id(e)
    st.validate(stages, hubs, ecs, techs)


def test_in_eff_unit_mismatch_and_negative_validation():
    st, t, s, h, stages, hubs, techs, ecs = make_basic_env()
    st.add_id(t)

    # Unit mismatch for in_eff -> DataException (note: implementation raises OUTEFF_SET key)
    with raises_with_key(exceptions.DataException, ExceptionKey.INEFF_SET.value):
        st.set_in_eff(s, t, Value(1, TimeUnit.H))

    # Negative in_eff should be caught during validate -> INEFF_VAL
    st.set_in_eff(s, t, Value(-0.5, DimlessUnit()))
    with raises_with_key(exceptions.DataException, ExceptionKey.INEFF_VAL.value):
        st.validate(stages, hubs, ecs, techs)


def test_defaults_and_charge_max_unit_mismatch():
    st, t, s, h, stages, hubs, techs, ecs = make_basic_env()
    st.add_id(t)

    # Defaults
    # in_eff default
    assert st.get_in_eff(s, t) == Value(DEF_INEFF)
    # charge_max default includes time unit
    default_charge = st.get_charge_max(s, t)
    assert default_charge == Value(DEF_CHARGEMAX, DimlessUnit() / TimeUnit.H)

    # Unit mismatch for charge_max -> CHARGEMAX_SET
    with raises_with_key(exceptions.DataException, ExceptionKey.CHARGEMAX_SET.value):
        st.set_charge_max(s, t, Value(1, DimlessUnit()))


def test_soc_minmax_and_init_bounds():
    st, t, s, h, stages, hubs, techs, ecs = make_basic_env()
    st.add_id(t)

    # soc_min > soc_max -> SOCMINMAX_VAL
    st.set_soc_min(s, t, Value(0.8, DimlessUnit()))
    st.set_soc_max(s, t, Value(0.6, DimlessUnit()))

    with raises_with_key(exceptions.DataException, ExceptionKey.SOCMINMAX_VAL.value):
        st.validate(stages, hubs, ecs, techs)

    # Fix min/max, then check soc_init bounds
    st.set_soc_min(s, t, Value(0.3, DimlessUnit()))
    st.set_soc_max(s, t, Value(0.7, DimlessUnit()))

    # soc_init negative -> SOCINIT_VAL
    st.set_soc_init(h, t, Value(-0.1, DimlessUnit()))
    with raises_with_key(exceptions.DataException, ExceptionKey.SOCINIT_VAL.value):
        st.validate(stages, hubs, ecs, techs)

    # soc_init below soc_min -> SOCINITMINMAX_VAL
    st.set_soc_init(h, t, Value(0.2, DimlessUnit()))
    with raises_with_key(exceptions.DataException, ExceptionKey.SOCINITMINMAX_VAL.value):
        st.validate(stages, hubs, ecs, techs)

    # soc_init above soc_max -> SOCINITMINMAX_VAL
    st.set_soc_init(h, t, Value(0.8, DimlessUnit()))
    with raises_with_key(exceptions.DataException, ExceptionKey.SOCINITMINMAX_VAL.value):
        st.validate(stages, hubs, ecs, techs)

    # Correct bounds -> pass
    st.set_soc_init(h, t, Value(0.5, DimlessUnit()))
    st.validate(stages, hubs, ecs, techs)
