import pytest

from ehubx.data.tech_data import (
    Techs,
    TechId,
    ExceptionKey as TechExcKey,
    copy_over_tech,
)
from ehubx.data.stage_data import Stages, StageId
from ehubx.data.hub_data import Hubs, HubId
from ehubx.data.value import Value
from ehubx.data.unit import MassUnit, TimeUnit, CurrencyUnit, DimlessUnit
from ehubx.data import exceptions


def test_add_id_duplicate_and_remove_missing():
    t = Techs()
    x = TechId("tech1")

    # add id
    t.add_id(x)

    # adding duplicate -> DuplicateIdException with correct key
    with pytest.raises(exceptions.DuplicateIdException) as excinfo:
        t.add_id(x)
    assert excinfo.value.key == TechExcKey.ID_ADD.value

    # removing missing id -> MissingIdException with correct key
    missing = TechId("missing")
    with pytest.raises(exceptions.MissingIdException) as excinfo:
        t.remove_id(missing)
    assert excinfo.value.key == TechExcKey.ID_REMOVE.value


def test_cap_unit_get_set_and_unknown():
    t = Techs()
    x = TechId("tech2")

    # get for unknown id -> MissingIdException with CAPUNIT_GET
    with pytest.raises(exceptions.MissingIdException) as excinfo:
        t.get_cap_unit(x)
    assert excinfo.value.key == TechExcKey.CAPUNIT_GET.value

    # add id and check default unit is dimless
    t.add_id(x)
    assert t.get_cap_unit(x).same_type_as(DimlessUnit())

    # set and get unit
    t.set_cap_unit(x, MassUnit.KG)
    assert t.get_cap_unit(x).same_type_as(MassUnit.KG)

    # set on unknown id -> MissingIdException with CAPUNIT_SET
    unknown = TechId("unknown")
    with pytest.raises(exceptions.MissingIdException) as excinfo:
        t.set_cap_unit(unknown, MassUnit.KG)
    assert excinfo.value.key == TechExcKey.CAPUNIT_SET.value


def test_lifetime_missing_and_set_unit_mismatch():
    t = Techs()
    x = TechId("tech3")
    t.add_id(x)

    # lifetime not set -> MissingIdException with LIFETIME_GET
    with pytest.raises(exceptions.MissingIdException) as excinfo:
        t.get_lifetime(x)
    assert excinfo.value.key == TechExcKey.LIFETIME_GET.value

    # set lifetime with wrong unit -> DataException with LIFETIME_SET
    with pytest.raises(exceptions.DataException) as excinfo:
        t.set_lifetime(x, Value(5, CurrencyUnit.EUR))
    assert excinfo.value.key == TechExcKey.LIFETIME_SET.value

    # set with correct unit and read back
    t.set_lifetime(x, Value(10, TimeUnit.A))
    assert t.get_lifetime(x) == Value(10, TimeUnit.A)


def test_unit_cap_min_set_unit_mismatch():
    t = Techs()
    x = TechId("tech4")
    s = StageId("s1")

    t.add_id(x)

    # set tech cap unit to mass
    t.set_cap_unit(x, MassUnit.KG)

    # setting unit_cap_min with wrong unit should raise DataException
    with pytest.raises(exceptions.DataException) as excinfo:
        t.set_unit_cap_min(s, x, Value(1, DimlessUnit()))
    assert excinfo.value.key == TechExcKey.UNITCAPMIN_SET.value


def test_cap_min_unknown_hub_validation():
    """cap_min with an unknown hub should raise CAPMIN_VAL during validation"""
    t = Techs()
    x = TechId("tech5")
    s = StageId("s2")
    h = HubId("hub1")

    stages = Stages()
    hubs = Hubs()

    stages.add_id(s)
    stages.set_start_year(s, 2020)

    # NOTE: do NOT add hub h to hubs -> should be unknown

    t.add_id(x)
    # set cap unit compatible with Value below
    t.set_cap_unit(x, MassUnit.KG)

    # set cap_min > 0 for a hub that is unknown to Hubs
    t.set_cap_min(s, h, x, Value(1, MassUnit.KG))

    # validation should raise CAPMIN_VAL due to unknown hub
    with pytest.raises(exceptions.DataException) as excinfo:
        t.validate(stages, hubs)
    assert excinfo.value.key == TechExcKey.CAPMIN_VAL.value


def test_copy_over_tech_exceptions_and_basic_copy():
    src = Techs()
    tar = Techs()
    x = TechId("tech6")
    s = StageId("s3")
    h = HubId("hub2")

    stages = Stages()
    hubs = Hubs()
    stages.add_id(s)
    stages.set_start_year(s, 2020)
    hubs.add_id(h)

    # copying from missing tech -> DataException.COPYOVERTECH
    with pytest.raises(exceptions.DataException) as excinfo:
        copy_over_tech(x, src, tar, stages, hubs)
    assert excinfo.value.key == TechExcKey.COPYOVERTECH.value

    # add tech to src and set some properties
    src.add_id(x)
    src.set_cap_unit(x, MassUnit.KG)
    src.add_allowed_stage(s, x)
    src.add_allowed_hub(h, x)
    src.set_lifetime(x, Value(8, TimeUnit.A))
    src.set_interest_rate(x, Value(0.05))
    src.set_unit_cap_min(s, x, Value(0.1, MassUnit.KG))
    src.set_one_time_capex(s, x, Value(100, CurrencyUnit.EUR))

    # successful copy
    copy_over_tech(x, src, tar, stages, hubs)

    assert x in tar.ids
    assert tar.get_cap_unit(x).same_type_as(MassUnit.KG)
    assert s in tar.get_allowed_stages(x)
    assert h in tar.get_allowed_hubs(x)
    assert tar.get_lifetime(x) == Value(8, TimeUnit.A)
    assert tar.get_unit_cap_min(s, x) == Value(0.1, MassUnit.KG)

    # copying again to target where it already exists -> DataException
    with pytest.raises(exceptions.DataException) as excinfo:
        copy_over_tech(x, src, tar, stages, hubs)
    assert excinfo.value.key == TechExcKey.COPYOVERTECH.value


def test_validate_lifetime_and_interest_rate_and_unitcap_unknown_stage():
    t = Techs()
    x = TechId("tech7")
    s = StageId("s4")

    stages = Stages()
    hubs = Hubs()

    t.add_id(x)

    # negative lifetime -> LIFETIME_VAL
    t.set_lifetime(x, Value(-1, TimeUnit.A))
    with pytest.raises(exceptions.DataException) as excinfo:
        t.validate(stages, hubs)
    assert excinfo.value.key == TechExcKey.LIFETIME_VAL.value

    # fix lifetime, negative interest rate -> INTERESTRATE_VAL
    t.set_lifetime(x, Value(5, TimeUnit.A))
    t.set_interest_rate(x, Value(-0.1))
    with pytest.raises(exceptions.DataException) as excinfo:
        t.validate(stages, hubs)
    assert excinfo.value.key == TechExcKey.INTERESTRATE_VAL.value

    # unit_cap_min with unknown stage -> UNITCAPMIN_VAL
    # (need a stage id s not added to stages)
    t.set_interest_rate(x, Value(0.01))
    t.set_cap_unit(x, MassUnit.KG)
    t.set_unit_cap_min(s, x, Value(1, MassUnit.KG))
    with pytest.raises(exceptions.DataException) as excinfo:
        t.validate(stages, hubs)
    assert excinfo.value.key == TechExcKey.UNITCAPMIN_VAL.value


def test_negative_costs_and_age_warnings(capsys):
    t = Techs()
    x = TechId("tech8")
    s = StageId("s5")
    h = HubId("hub3")

    stages = Stages()
    hubs = Hubs()
    stages.add_id(s)
    stages.set_start_year(s, 2020)
    hubs.add_id(h)

    t.add_id(x)
    t.set_cap_unit(x, MassUnit.KG)

    # negative one_time_capex should log a warning
    t.set_one_time_capex(s, x, Value(-100, CurrencyUnit.EUR))
    t.validate(stages, hubs)
    captured = capsys.readouterr()
    assert "one_time_capex" in captured.out and "Warning" in captured.out

    # age_init >= lifetime should log a warning
    t.set_lifetime(x, Value(5, TimeUnit.A))
    t.set_age_init(h, x, Value(6, TimeUnit.A))
    t.validate(stages, hubs)
    captured = capsys.readouterr()
    assert ">= lifetime" in captured.out and "Warning" in captured.out


def test_cap_min_allowed_hubs_private_check():
    t = Techs()
    x = TechId("tech9")
    s = StageId("s6")
    h = HubId("hub4")

    t.add_id(x)
    t.set_cap_unit(x, MassUnit.KG)
    t.set_cap_min(s, h, x, Value(1, MassUnit.KG))

    # h not in allowed hubs for x -> CAPMINALLOWEDHUBS_VAL
    with pytest.raises(exceptions.DataException) as excinfo:
        t._validate_capmin_allowedhubs()
    assert excinfo.value.key == TechExcKey.CAPMINALLOWEDHUBS_VAL.value


def test_coupled_techs_and_factors_validation():
    t = Techs()
    x_main = TechId("main")
    x_sub = TechId("sub")
    x_other = TechId("other")

    stages = Stages()
    hubs = Hubs()

    t.add_id(x_main)
    t.add_id(x_sub)
    t.add_id(x_other)

    # make main and sub and set cap units
    t.set_cap_unit(x_main, MassUnit.KG)
    t.set_cap_unit(x_sub, TimeUnit.A)  # intentionally different
    t.set_coupled_main_tech(x_sub, x_main)

    # add a stage so validate() doesn't fail earlier
    s = StageId("s_coupled")
    stages.add_id(s)
    stages.set_start_year(s, 2020)

    # wrong unit for coupled_cap_factor -> should fail validation
    t.set_coupled_cap_factor(x_sub, Value(1, DimlessUnit()))
    with pytest.raises(exceptions.DataException) as excinfo:
        t.validate(stages, hubs)
    assert excinfo.value.key == TechExcKey.COUPLEDCAPFACTOR_VAL.value

    # negative coupled_cap_factor -> should fail
    expected_unit = t.get_cap_unit(x_sub) / t.get_cap_unit(x_main)
    t.set_coupled_cap_factor(x_sub, Value(-1, expected_unit))
    with pytest.raises(exceptions.DataException) as excinfo:
        t.validate(stages, hubs)
    assert excinfo.value.key == TechExcKey.COUPLEDCAPFACTOR_VAL.value


def test_coupled_api_and_errors():
    t = Techs()
    x = TechId("solo")

    # unknown id passed to is_coupled_* should raise UnknownIdException
    with pytest.raises(exceptions.UnknownIdException) as excinfo:
        t.is_coupled_main_tech(x)
    assert excinfo.value.key == TechExcKey.COUPLEDMAINTECH_VAL.value

    with pytest.raises(exceptions.UnknownIdException) as excinfo:
        t.is_coupled_sub_tech(x)
    assert excinfo.value.key == TechExcKey.COUPLEDSUBTECH_VAL.value

    # get_coupled_main_tech for non-sub -> MissingIdException
    t.add_id(x)
    with pytest.raises(exceptions.MissingIdException) as excinfo:
        t.get_coupled_main_tech(x)
    assert excinfo.value.key == TechExcKey.COUPLEDMAINTECH_GET.value

    # set_coupled_main_tech with unknown ids should raise UnknownIdException
    x1 = TechId("x1")
    x2 = TechId("x2")
    with pytest.raises(exceptions.UnknownIdException) as excinfo:
        t.set_coupled_main_tech(x1, x2)
    assert excinfo.value.key == TechExcKey.COUPLEDMAINTECH_SET.value

    # get_coupled_cap_factor for non-sub tech should raise COUPLEDCAPFACTOR_NOTASUB
    with pytest.raises(exceptions.DataException) as excinfo:
        t.get_coupled_cap_factor(x)
    assert excinfo.value.key == TechExcKey.COUPLEDCAPFACTOR_NOTASUB.value


def test_cap_init_and_cap_max_validation():
    t = Techs()
    x = TechId("capty")
    s = StageId("s7")
    h = HubId("hub5")

    stages = Stages()
    hubs = Hubs()
    stages.add_id(s)
    stages.set_start_year(s, 2020)

    t.add_id(x)

    # cap_init with unknown hub -> CAPINIT_VAL
    t.set_cap_unit(x, MassUnit.KG)
    t.set_cap_init(h, x, Value(1, MassUnit.KG))
    with pytest.raises(exceptions.DataException) as excinfo:
        t.validate(stages, hubs)
    assert excinfo.value.key == TechExcKey.CAPINIT_VAL.value

    # cap_max negative -> CAPMAX_VAL
    hubs.add_id(h)
    t.set_cap_max(s, h, x, Value(-1, MassUnit.KG))
    with pytest.raises(exceptions.DataException) as excinfo:
        t.validate(stages, hubs)
    assert excinfo.value.key == TechExcKey.CAPMAX_VAL.value


def test_coupled_main_tech_conflict():
    t = Techs()
    a = TechId("a")
    b = TechId("b")
    c = TechId("c")

    t.add_id(a)
    t.add_id(b)
    t.add_id(c)

    # make (a) main tech for (b) and also (a) sub tech of (c)
    t.set_coupled_main_tech(b, a)
    t.set_coupled_main_tech(a, c)

    # call private validator directly to avoid needing stage data
    with pytest.raises(exceptions.DataException) as excinfo:
        t._validate_coupled_main_tech()
    assert excinfo.value.key == TechExcKey.COUPLEDMAINTECH_VAL.value


def test_copy_tech_exceptions_and_basic_copy():
    t = Techs()
    x = TechId("x_copy")
    x_new = TechId("x_copy_new")
    s = StageId("s_copy")
    h = HubId("h_copy")

    # copying missing tech -> MissingIdException
    with pytest.raises(exceptions.MissingIdException) as excinfo:
        t.copy_tech(x, x_new)
    assert excinfo.value.key == TechExcKey.TECH_COPY.value

    # add original tech and a target with duplicate id
    t.add_id(x)
    t.add_id(x_new)
    with pytest.raises(exceptions.DuplicateIdException) as excinfo:
        t.copy_tech(x, x_new)
    assert excinfo.value.key == TechExcKey.TECH_COPY.value

    # prepare a proper copy scenario: remove x_new and populate x's attributes
    t.remove_id(x_new)
    t.set_cap_unit(x, MassUnit.KG)
    t.add_allowed_stage(s, x)
    t.add_allowed_hub(h, x)
    t.set_lifetime(x, Value(7, TimeUnit.A))
    t.set_interest_rate(x, Value(0.03))
    t.set_unit_cap_min(s, x, Value(0.2, MassUnit.KG))
    t.set_one_time_capex(s, x, Value(1000, CurrencyUnit.EUR))
    t.set_capex_per_cap(s, x, Value(10, CurrencyUnit.EUR / MassUnit.KG))
    t.set_one_time_opex(s, x, Value(50, CurrencyUnit.EUR))
    t.set_opex_per_cap(s, x, Value(1, CurrencyUnit.EUR / MassUnit.KG))
    t.set_co2_per_cap(s, x, Value(5, MassUnit.KG / MassUnit.KG))
    t.set_last_inst_year(h, x, 2030)
    t.set_cap_init(h, x, Value(10, MassUnit.KG))
    t.set_age_init(h, x, Value(1, TimeUnit.A))
    t.set_cap_min(s, h, x, Value(2, MassUnit.KG))
    t.set_cap_max(s, h, x, Value(20, MassUnit.KG))

    # successful copy
    t.copy_tech(x, x_new)
    assert x_new in t.ids
    assert t.get_cap_unit(x_new).same_type_as(MassUnit.KG)
    assert s in t.get_allowed_stages(x_new)
    assert h in t.get_allowed_hubs(x_new)
    assert t.get_lifetime(x_new) == Value(7, TimeUnit.A)
    assert t.get_unit_cap_min(s, x_new) == Value(0.2, MassUnit.KG)
    assert t.get_one_time_capex(s, x_new) == Value(1000, CurrencyUnit.EUR)
    assert t.get_capex_per_cap(s, x_new) == Value(10, CurrencyUnit.EUR / MassUnit.KG)
    assert t.get_cap_init(h, x_new) == Value(10, MassUnit.KG)
    assert t.get_cap_min(s, h, x_new) == Value(2, MassUnit.KG)
    assert t.get_cap_max(s, h, x_new) == Value(20, MassUnit.KG)


def test_copying_main_tech_raises_exception():
    t = Techs()
    main = TechId("main")
    sub = TechId("sub")
    t.add_id(main)
    t.add_id(sub)
    t.set_coupled_main_tech(sub, main)

    # copying a main tech that has sub-techs triggers the internal Exception
    with pytest.raises(Exception):
        t.copy_tech(main, TechId("main_copy"))


def test_remove_tech_and_cleanup():
    t = Techs()
    x = TechId("to_remove")
    s = StageId("s_rem")
    h = HubId("h_rem")

    t.add_id(x)
    t.set_cap_unit(x, MassUnit.KG)
    t.add_allowed_stage(s, x)
    t.add_allowed_hub(h, x)
    t.set_unit_cap_min(s, x, Value(1, MassUnit.KG))

    # remove unknown tech -> MissingIdException
    with pytest.raises(exceptions.MissingIdException) as excinfo:
        t.remove_tech(TechId("unknown"))
    assert excinfo.value.key == TechExcKey.TECH_REMOVE.value

    # now remove the tech and check cleanup
    t.remove_tech(x)
    assert x not in t.ids
    # get_allowed_stages should return empty set after removal
    assert t.get_allowed_stages(x) == set()


def test_coupled_properties_and_default_cap_factor():
    t = Techs()
    a = TechId("A")
    b = TechId("B")
    c = TechId("C")
    t.add_id(a)
    t.add_id(b)
    t.add_id(c)

    # set B and C as subs of A
    t.set_coupled_main_tech(b, a)
    t.set_coupled_main_tech(c, a)

    assert t.coupled_main_techs == {a}
    assert t.coupled_sub_techs == {b, c}

    # default coupled cap factor for a sub-tech should be 1
    assert t.get_coupled_cap_factor(b) == Value(1)
