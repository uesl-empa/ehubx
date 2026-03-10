import pytest

from ehubx.data.self_sufficiency_data import (
    SelfSufficiency,
    ExceptionKey as SSExceptionKey,
)
from ehubx.data.ec_data import Ecs, EcId, ImpExpType
from ehubx.data.import_data import Imports
from ehubx.data.export_data import Exports
from ehubx.data.stage_data import StageId
from ehubx.data.hub_data import HubId
from ehubx.data.value import Value
from ehubx.data.exceptions import DataException
from ehubx.data.unit import DimlessUnit


def test_validate_defaults_no_exception():
    ss = SelfSufficiency()
    ecs = Ecs()
    imports = Imports()
    exports = Exports()

    # Default min/max are 0 and 1 -> should not raise
    ss.validate(ecs, imports, exports)


def test_negative_min_warns_but_no_exception():
    ss = SelfSufficiency()
    ss.self_sufficiency_min = Value(-0.1)
    ecs = Ecs()
    imports = Imports()
    exports = Exports()

    # Negative min only logs a warning, no exception should be raised
    ss.validate(ecs, imports, exports)


def test_min_greater_than_one_raises_data_exception_with_expected_key():
    ss = SelfSufficiency()
    ss.self_sufficiency_min = Value(1.1)
    ecs = Ecs()
    imports = Imports()
    exports = Exports()

    with pytest.raises(DataException) as excinfo:
        ss.validate(ecs, imports, exports)

    assert excinfo.value.key == SSExceptionKey.SELFSUFFICIENCYMIN_VAL.value


def test_max_negative_raises_data_exception_with_expected_key():
    ss = SelfSufficiency()
    ss.self_sufficiency_max = Value(-0.01)
    ecs = Ecs()
    imports = Imports()
    exports = Exports()

    with pytest.raises(DataException) as excinfo:
        ss.validate(ecs, imports, exports)

    assert excinfo.value.key == SSExceptionKey.SELFSUFFICIENCYMAX_VAL.value


def test_min_larger_than_max_raises_data_exception_with_expected_key():
    ss = SelfSufficiency()
    ss.self_sufficiency_min = Value(0.9)
    ss.self_sufficiency_max = Value(0.8)
    ecs = Ecs()
    imports = Imports()
    exports = Exports()

    with pytest.raises(DataException) as excinfo:
        ss.validate(ecs, imports, exports)

    assert excinfo.value.key == SSExceptionKey.SELFSUFFICIENCYMINMAX_VAL.value


def test_export_import_cross_energy_logs_but_does_not_raise():
    ss = SelfSufficiency()

    ecs = Ecs()
    e = EcId("ec1")
    ecs.add_id(e)
    ecs.set_is_energy(e, True)
    ecs.set_imp_exp_type(e, ImpExpType.CROSS)

    s = StageId("s1")
    h = HubId("h1")

    imports = Imports()
    exports = Exports()

    # Add the same tuple to both imports and exports
    imports.add_tuple(s, h, e, DimlessUnit())
    exports.add_tuple(s, h, e, DimlessUnit())

    # This should only result in a logged warning, not an exception
    ss.validate(ecs, imports, exports)
