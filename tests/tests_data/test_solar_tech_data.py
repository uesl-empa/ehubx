import pytest
from contextlib import contextmanager

from ehubx.data.solar_tech_data import SolarTechs, ExceptionKey
from ehubx.data.conv_tech_data import ConversionTechs
from ehubx.data.ec_data import EcId, Ecs
from ehubx.data.hub_data import Hubs
from ehubx.data.stage_data import StageId, Stages
from ehubx.data.tech_data import TechId, Techs
from ehubx.data.import_data import Imports
from ehubx.data.solar_data import SolarData
from ehubx.data.unit import DimlessUnit, PowerUnit, TimeUnit
from ehubx.data.value import Value
from ehubx.data import exceptions


@contextmanager
def raises_with_key(exc_type, expected_key):
    with pytest.raises(exc_type) as excinfo:
        yield excinfo
    assert excinfo.value.key == expected_key


def make_env():
    s = SolarTechs()
    x = TechId("x1")
    stages = Stages()
    hubs = Hubs()
    techs = Techs()
    conv_techs = ConversionTechs()
    imports = Imports()
    solar_data = SolarData()
    return s, x, stages, hubs, techs, conv_techs, imports, solar_data


def test_duplicate_add_id_raises_duplicate_key():
    s, x, *_ = make_env()
    s.add_id(x)
    with raises_with_key(exceptions.DuplicateIdException, ExceptionKey.ID_ADD.value):
        s.add_id(x)


def test_get_set_curtail_unknown_id_raises_expected_keys():
    s, x, stages, *_ = make_env()
    # get before adding id -> UnknownIdException with CURTAILMAXREL_GET
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.CURTAILMAXREL_GET.value):
        s.get_curtail_max_rel(StageId("s1"), x)
    # set before adding id -> UnknownIdException with CURTAILMAXREL_SET
    with raises_with_key(exceptions.UnknownIdException, ExceptionKey.CURTAILMAXREL_SET.value):
        s.set_curtail_max_rel(StageId("s1"), x, Value(0.5, DimlessUnit()))


def test_set_curtail_unit_mismatch_raises_unit_exception():
    s, x, *_ = make_env()
    s.add_id(x)
    # providing a unit incompatible with DimlessUnit should raise UnitException
    with pytest.raises(exceptions.UnitException):
        s.set_curtail_max_rel(StageId("s1"), x, Value(0.2, PowerUnit.KW * TimeUnit.H))


def test_get_default_curtail_max_rel():
    s, x, *_ = make_env()
    s.add_id(x)
    assert s.get_curtail_max_rel(StageId("s1"), x) == Value(1)


def test_validate_ids_raises_id_val_key():
    s, x, stages, hubs, techs, conv_techs, imports, solar_data = make_env()
    # add solar tech id but not to conv_techs -> validate should raise DataException with ID_VAL
    s.add_id(x)
    with raises_with_key(exceptions.DataException, ExceptionKey.ID_VAL.value):
        s.validate(stages, hubs, imports, techs, conv_techs, solar_data)


def test_validate_in_ecs_raises_inecs_val_when_multiple_or_non_solar_ec():
    s, x, stages, hubs, techs, conv_techs, imports, solar_data = make_env()
    # add conv tech id and two input ecs to trigger the "more than one input ec" case
    conv_techs.add_id(x)
    conv_techs.add_in_ec(x, EcId("e1"), PowerUnit.KW * TimeUnit.H)
    conv_techs.add_in_ec(x, EcId("e2"), PowerUnit.KW * TimeUnit.H)
    s.add_id(x)
    with raises_with_key(exceptions.DataException, ExceptionKey.INECS_VAL.value):
        s.validate(stages, hubs, imports, techs, conv_techs, solar_data)


def test_validate_out_ecs_raises_outecs_val_when_multiple_outputs():
    s, x, stages, hubs, techs, conv_techs, imports, solar_data = make_env()
    # set up a single input ec that is known to solar_data so _validate_in_ecs passes
    conv_techs.add_id(x)
    conv_techs.add_in_ec(x, EcId("in1"), PowerUnit.KW * TimeUnit.H)
    solar_data.add_ec(EcId("in1"), PowerUnit.KW * TimeUnit.H)
    # now add two outputs to trigger OUTECS_VAL
    conv_techs.add_out_ec(x, EcId("e1"), PowerUnit.KW * TimeUnit.H)
    conv_techs.add_out_ec(x, EcId("e2"), PowerUnit.KW * TimeUnit.H)
    s.add_id(x)
    with raises_with_key(exceptions.DataException, ExceptionKey.OUTECS_VAL.value):
        s.validate(stages, hubs, imports, techs, conv_techs, solar_data)


def test_validate_curtail_max_rel_checks_stage_and_bounds():
    s, x, stages, hubs, techs, conv_techs, imports, solar_data = make_env()
    s.add_id(x)
    # ensure conv_techs knows about x so id validation passes
    conv_techs.add_id(x)
    # set curtail for an unknown stage -> validation should raise CURTAILMAXREL_VAL
    conv_techs.add_in_ec(x, EcId("in1"), PowerUnit.KW * TimeUnit.H)
    conv_techs.add_out_ec(x, EcId("out1"), PowerUnit.KW * TimeUnit.H)
    solar_data.add_ec(EcId("in1"), PowerUnit.KW * TimeUnit.H)
    s.set_curtail_max_rel(StageId("s_missing"), x, Value(0.5, DimlessUnit()))
    with raises_with_key(exceptions.DataException, ExceptionKey.CURTAILMAXREL_VAL.value):
        s.validate(stages, hubs, imports, techs, conv_techs, solar_data)

    # negative value
    s = SolarTechs()
    s.add_id(x)
    conv_techs.add_in_ec(x, EcId("in1"), PowerUnit.KW * TimeUnit.H)
    conv_techs.add_out_ec(x, EcId("out1"), PowerUnit.KW * TimeUnit.H)
    s.set_curtail_max_rel(StageId("s1"), x, Value(-0.1, DimlessUnit()))
    stages.add_id(StageId("s1"))
    with raises_with_key(exceptions.DataException, ExceptionKey.CURTAILMAXREL_VAL.value):
        s.validate(stages, hubs, imports, techs, conv_techs, solar_data)

    # value > 1
    s = SolarTechs()
    s.add_id(x)
    conv_techs.add_in_ec(x, EcId("in1"), PowerUnit.KW * TimeUnit.H)
    conv_techs.add_out_ec(x, EcId("out1"), PowerUnit.KW * TimeUnit.H)
    s.set_curtail_max_rel(StageId("s1"), x, Value(1.2, DimlessUnit()))
    stages = Stages()
    stages.add_id(StageId("s1"))
    with raises_with_key(exceptions.DataException, ExceptionKey.CURTAILMAXREL_VAL.value):
        s.validate(stages, hubs, imports, techs, conv_techs, solar_data)
