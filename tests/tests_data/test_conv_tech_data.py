import pytest
from contextlib import contextmanager

from ehubx.data.conv_tech_data import ConversionTechs, ExceptionKey
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.hub_data import HubId, Hubs
from ehubx.data.time_data import TimeId, Times
from ehubx.data.time_series import TimeSeries
from ehubx.data.unit import DimlessUnit, Unit, CurrencyUnit
from ehubx.data.value import Value
from ehubx.data import exceptions
from ehubx.core.common import TimeSeriesKind


@contextmanager
def raises_with_key(exc_type, expected_key):
    with pytest.raises(exc_type) as excinfo:
        yield excinfo
    assert excinfo.value.key == expected_key


def make_basic_env():
    c = ConversionTechs()
    x = TechId("x1")
    s = StageId("s1")
    h = HubId("h1")
    t = TimeId(1)
    stages = Stages()
    stages.add_id(s)
    hubs = Hubs()
    hubs.add_id(h)
    techs = Techs()
    times = Times()
    times.add_id(t)
    return c, x, s, h, t, stages, hubs, techs, times


def test_add_remove_ids_and_duplicate_raise_keys():
    c, x, s, h, t, stages, hubs, techs, times = make_basic_env()
    c.add_id(x)
    with raises_with_key(exceptions.DuplicateIdException, ExceptionKey.ID_ADD.value):
        c.add_id(x)
    with raises_with_key(exceptions.MissingIdException, ExceptionKey.ID_REMOVE.value):
        c.remove_id(TechId("unknown"))


def test_in_ecs_get_set_and_missing_key():
    c, x, s, h, t, stages, hubs, techs, times = make_basic_env()
    c.add_id(x)
    with raises_with_key(exceptions.MissingIdException, ExceptionKey.INECS_GET.value):
        c.get_in_ecs(x)
    # add input ec and unit
    c.add_in_ec(x, EcId("e1"), DimlessUnit())
    assert EcId("e1") in c.get_in_ecs(x)


def test_in_ec_main_auto_and_validation():
    c, x, s, h, t, stages, hubs, techs, times = make_basic_env()
    c.add_id(x)
    techs.add_id(x)
    # set in_ec_main to unknown ec (not present in in_ecs) -> validation should raise
    c._in_ec_main[x] = EcId("e_unknown")
    with raises_with_key(exceptions.DataException, ExceptionKey.INECMAIN_VAL.value):
        c.validate(stages, hubs, Ecs(), techs, times)


def test_in_part_set_unit_and_default_return():
    c, x, s, h, t, stages, hubs, techs, times = make_basic_env()
    c.add_id(x)
    # add input ec with a specific unit
    c.add_in_ec(x, EcId("e1"), DimlessUnit())

    # setter unit mismatch
    with raises_with_key(exceptions.DataException, ExceptionKey.INPART_SET.value):
        c.set_in_part(s, x, EcId("e1"), Value(1.0, unit=CurrencyUnit.CHF))

    # default when single input ec
    val = c.get_in_part(s, x, EcId("e1"))
    assert val.to_float(DimlessUnit()) == pytest.approx(1.0)


def test_out_ecs_and_out_eff_unit_checks_and_getters():
    c, x, s, h, t, stages, hubs, techs, times = make_basic_env()
    c.add_id(x)
    # add in_ec (main) and out_ec with units
    c.add_in_ec(x, EcId("in"), DimlessUnit())
    c.add_out_ec(x, EcId("out"), DimlessUnit())

    with raises_with_key(exceptions.MissingIdException, ExceptionKey.OUTECS_GET.value):
        # remove the out_ec entry to force missing
        c._out_ecs.pop(x, None)
        c.get_out_ecs(x)

    # restore and test out_eff unit mismatch and success
    c.add_out_ec(x, EcId("out"), DimlessUnit())
    # expected unit for out_eff is out_unit / in_unit = [-]/[-] = [-]
    with raises_with_key(exceptions.DataException, ExceptionKey.OUTEFF_SET.value):
        c.set_out_eff(s, x, EcId("out"), t, Value(1.0, unit=Value(1.0, unit=CurrencyUnit.CHF).unit))

    # correct unit -> set and get
    c.set_out_eff(s, x, EcId("out"), t, Value(1.0, unit=DimlessUnit()))
    ts = c.get_out_eff(s, x, EcId("out"))
    assert ts.get_value(t).to_float(DimlessUnit()) == pytest.approx(1.0)


def test_out_sum_min_max_and_minmax_validation():
    c, x, s, h, t, stages, hubs, techs, times = make_basic_env()
    c.add_id(x)
    techs.add_id(x)
    # add out ec and set as main
    c.add_out_ec(x, EcId("o"), DimlessUnit())
    c.set_out_ec_main(x, EcId("o"))

    # set min and max with units
    c.set_out_sum_min(s, h, x, Value(10.0, unit=DimlessUnit()))
    c.set_out_sum_max(s, h, x, Value(5.0, unit=DimlessUnit()))

    ecs = Ecs()
    ecs.add_id(EcId("o"))
    # ensure input ecs exist so validation reaches the min/max comparison
    c.add_in_ec(x, EcId("i"), DimlessUnit())
    ecs.add_id(EcId("i"))
    with raises_with_key(exceptions.DataException, ExceptionKey.OUTSUMMINMAX_VAL.value):
        c.validate(stages, hubs, ecs, techs, times)


def test_availability_default_and_defset_unit_check_and_time_series_listing():
    c, x, s, h, t, stages, hubs, techs, times = make_basic_env()
    c.add_id(x)
    techs.add_id(x)

    # get_availability default
    ts = c.get_availability(s, h, x)
    assert ts.def_value.to_float(DimlessUnit()) == pytest.approx(1.0)

    # def unit mismatch
    with raises_with_key(exceptions.DataException, ExceptionKey.AVAILABILITY_DEFSET.value):
        c.set_availability_def(s, h, x, Value(1.0, unit=CurrencyUnit.CHF))

    # set a time series availability value and an out_eff value -> ensure time_series lists them
    c.add_in_ec(x, EcId("in"), DimlessUnit())
    c.add_out_ec(x, EcId("out"), DimlessUnit())
    c.set_out_eff(s, x, EcId("out"), t, Value(0.5, unit=DimlessUnit()))
    c.set_availability(s, h, x, t, Value(0.8, unit=DimlessUnit()))

    found_kinds = {k for k, _, _, _ in c.time_series}
    assert TimeSeriesKind.CONVTECHOUTEFF in found_kinds
    assert TimeSeriesKind.CONVTECHAVAIL in found_kinds


def test_opex_per_energy_get_and_set():
    c, x, s, h, t, stages, hubs, techs, times = make_basic_env()

    # Unknown tech id -> setting should raise UnknownIdException
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.OPEXPERENERGY_SET.value):
        c.set_opex_per_energy(s, x, Value(1.0, unit=CurrencyUnit.CHF))

    # Prepare tech and ecs so validation reaches the opex_per_energy validator
    c.add_id(x)
    techs.add_id(x)
    c.add_in_ec(x, EcId("i"), DimlessUnit())
    c.add_out_ec(x, EcId("o"), DimlessUnit())
    c.set_out_ec_main(x, EcId("o"))

    ecs = Ecs()
    ecs.add_id(EcId("i"))
    ecs.add_id(EcId("o"))

    # Default getter should return DEF_OPEXPERENERGY with expected unit
    default = c.get_opex_per_energy(s, x)
    expected_unit = CurrencyUnit.CHF / DimlessUnit()
    assert default.to_float(expected_unit) == pytest.approx(0.0)

    # Unit mismatch on setting should raise DataException
    with raises_with_key(exceptions.DataException, ExceptionKey.OPEXPERENERGY_SET.value):
        c.set_opex_per_energy(s, x, Value(1.0, unit=DimlessUnit()))

    # Correct unit -> set and get
    val = Value(2.5, unit=expected_unit)
    c.set_opex_per_energy(s, x, val)
    got = c.get_opex_per_energy(s, x)
    assert got.to_float(expected_unit) == pytest.approx(2.5)

    # If opex is set for an unknown stage, validation should raise
    s_unknown = StageId("s_unknown")
    c.set_opex_per_energy(s_unknown, x, Value(1.0, unit=expected_unit))
    with raises_with_key(exceptions.DataException, ExceptionKey.OPEXPERENERGY_VAL.value):
        c.validate(stages, hubs, ecs, techs, times)


def test_ids_in_order_and_auto_main_selection_and_checks(caplog):
    c, x, s, h, t, stages, hubs, techs, times = make_basic_env()

    # ids_in_order
    a = TechId("a")
    b = TechId("b")
    c.add_id(b)
    c.add_id(a)
    c.add_id(TechId("c"))
    assert [i.key for i in c.ids_in_order] == ["a", "b", "c"]

    # auto in_ec_main when single input ec
    c.add_id(x)
    c.add_in_ec(x, EcId("in_single"), DimlessUnit())
    assert c.get_in_ec_main(x) == EcId("in_single")

    # auto out_ec_main when single output ec
    c.add_out_ec(x, EcId("out_single"), DimlessUnit())
    assert c.get_out_ec_main(x) == EcId("out_single")

    # set_out_ec_main with unknown out ec should raise
    with raises_with_key(exceptions.DataException, ExceptionKey.OUTECMAIN_SET.value):
        c.set_out_ec_main(x, EcId("does_not_exist"))


def test_in_out_ec_check_errors_and_time_series_setter():
    c, x, s, h, t, stages, hubs, techs, times = make_basic_env()
    c.add_id(x)

    # Setting in_part for an ec not registered should raise
    c.add_in_ec(x, EcId("i"), DimlessUnit())
    with raises_with_key(exceptions.DataException, ExceptionKey.INPART_SET.value):
        c.set_in_part(s, x, EcId("unknown"), Value(1.0, unit=DimlessUnit()))

    # Setting out_eff for an ec not registered should raise
    c.add_out_ec(x, EcId("o"), DimlessUnit())
    with raises_with_key(exceptions.DataException, ExceptionKey.OUTEFF_SET.value):
        c.set_out_eff(s, x, EcId("unknown"), t, Value(0.1, unit=DimlessUnit()))

    # set_time_series_val for CONVTECHAVAIL
    c.set_time_series_val(TimeSeriesKind.CONVTECHAVAIL, s, (h.key, x.key), t, 0.75)
    assert c.get_availability(s, h, x).get_value(t).to_float(DimlessUnit()) == pytest.approx(0.75)

    # set_time_series_val for CONVTECHOUTEFF
    c.add_in_ec(x, EcId("in"), DimlessUnit())
    c.add_out_ec(x, EcId("out"), DimlessUnit())
    # Ensure a main input is set (or automatically unique) so the unit calculation succeeds
    c.set_in_ec_main(x, EcId("in"))
    c.set_time_series_val(TimeSeriesKind.CONVTECHOUTEFF, s, (x.key, EcId("out").key), t, 0.25)
    ts = c.get_out_eff(s, x, EcId("out"))
    assert ts.get_value(t).to_float(DimlessUnit()) == pytest.approx(0.25)

    kinds = {k for k, _, _, _ in c.time_series}
    assert TimeSeriesKind.CONVTECHAVAIL in kinds
    assert TimeSeriesKind.CONVTECHOUTEFF in kinds


def test_out_eff_negative_defaults_and_time_values_raise_on_validate():
    c, x, s, h, t, stages, hubs, techs, times = make_basic_env()
    c.add_id(x)
    techs.add_id(x)

    # prepare ecs so validation can check out_eff
    c.add_in_ec(x, EcId("in"), DimlessUnit())
    c.add_out_ec(x, EcId("out"), DimlessUnit())
    ecs = Ecs()
    ecs.add_id(EcId("in"))
    ecs.add_id(EcId("out"))

    # default negative out_eff should fail validation
    c.set_out_eff_def(s, x, EcId("out"), Value(-0.1, unit=DimlessUnit()))
    with raises_with_key(exceptions.DataException, ExceptionKey.OUTEFF_VAL.value):
        c.validate(stages, hubs, ecs, techs, times)

    # negative time value should also fail validation
    c2, x2, s2, h2, t2, stages2, hubs2, techs2, times2 = make_basic_env()
    c2.add_id(x2)
    techs2.add_id(x2)
    c2.add_in_ec(x2, EcId("in"), DimlessUnit())
    c2.add_out_ec(x2, EcId("out"), DimlessUnit())
    ecs2 = Ecs()
    ecs2.add_id(EcId("in"))
    ecs2.add_id(EcId("out"))
    # set a negative time value
    c2.set_out_eff(s2, x2, EcId("out"), t2, Value(-0.2, unit=DimlessUnit()))
    with raises_with_key(exceptions.DataException, ExceptionKey.OUTEFF_VAL.value):
        c2.validate(stages2, hubs2, ecs2, techs2, times2)


def test_availability_default_negative_raises_on_validate():
    c, x, s, h, t, stages, hubs, techs, times = make_basic_env()
    c.add_id(x)
    techs.add_id(x)
    c.add_in_ec(x, EcId("in"), DimlessUnit())
    c.add_out_ec(x, EcId("out"), DimlessUnit())
    ecs = Ecs()
    ecs.add_id(EcId("in"))
    ecs.add_id(EcId("out"))

    # set default availability negative
    c.set_availability_def(s, h, x, Value(-0.5, unit=DimlessUnit()))
    with raises_with_key(exceptions.DataException, ExceptionKey.AVAILABILITY_VAL.value):
        c.validate(stages, hubs, ecs, techs, times)


def test_inout_ecs_warning_and_remove_id_cleans_up(caplog, capsys):
    c, x, s, h, t, stages, hubs, techs, times = make_basic_env()
    c.add_id(x)
    techs.add_id(x)

    # add same ec as in and out -> should log a warning
    c.add_in_ec(x, EcId("both"), DimlessUnit())
    c.add_out_ec(x, EcId("both"), DimlessUnit())
    ecs = Ecs()
    ecs.add_id(EcId("both"))

    caplog.clear()
    c.validate(stages, hubs, ecs, techs, times)
    out = capsys.readouterr().out
    assert "both inputs and outputs" in out

    # populate other fields and then remove id -> subsequent getters should raise UnknownIdException
    c.set_in_part(s, x, EcId("both"), Value(1.0, unit=DimlessUnit()))
    c.set_out_eff(s, x, EcId("both"), t, Value(0.1, unit=DimlessUnit()))
    c.set_opex_per_energy(s, x, Value(1.0, unit=CurrencyUnit.CHF / DimlessUnit()))
    c.set_out_sum_min(s, h, x, Value(1.0, unit=DimlessUnit()))
    c.set_out_sum_max(s, h, x, Value(2.0, unit=DimlessUnit()))
    c.set_availability(s, h, x, t, Value(0.9, unit=DimlessUnit()))

    c.remove_id(x)
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.INECS_GET.value):
        c.get_in_ecs(x)


def test_get_opex_per_energy_unknown_id():
    c, x, s, h, t, stages, hubs, techs, times = make_basic_env()
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.OPEXPERENERGY_GET.value):
        c.get_opex_per_energy(s, x)

