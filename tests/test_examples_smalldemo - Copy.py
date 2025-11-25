import os

import pytest
from pyomo.core import value

from ehubx import EhubX, Glpk, ObjectiveType
from ehubx.model import (
    ates_tech_model,
    conv_tech_model,
    demand_model,
    ebm_tech_model,
    export_model,
    hp_tech_model,
    import_model,
    load_shedding_model,
    load_shifting_model,
    network_model,
    solar_tech_model,
    stor_tech_model,
    tech_model,
)
from tests.util import (
    DIRNAME_EXAMPLES,
    DIRNAME_TMPTESTMODEL,
    clear_tmp_model,
    init_tmp_model,
)


def test_examples_smalldemo():
    # Init
    example_model_dir = os.path.join(DIRNAME_EXAMPLES, "small_demo")
    init_tmp_model(example_model_dir)
    # Run
    ehubx = EhubX()
    ehubx.model_dir_path = DIRNAME_TMPTESTMODEL
    ehubx.parse()
    ehubx.build()
    glpk = Glpk()
    ehubx.set_solver(glpk)
    ehubx.solve_single_obj(obj_type=ObjectiveType.CO2)
    model = ehubx._model
    # Check H1 (conversion)
    assert value(
        getattr(model, tech_model.VAR_TECHCAP)["S1", "H1", "X1Conv"]
    ) == pytest.approx(10)
    assert value(
        getattr(model, tech_model.VAR_TECHCAPINSTL)["S1", "H1", "X1Conv"]
    ) == pytest.approx(10)
    assert value(
        getattr(model, tech_model.VAR_YTECHCAPINSTL)["S1", "H1", "X1Conv"]
    ) == pytest.approx(1)
    # assert value(
    #     getattr(model, tech_model.VAR_YTECHUSED)["S1", "H1", "X1Conv"]
    # ) == pytest.approx(1)
    assert value(
        getattr(model, conv_tech_model.VAR_CONVTECHIN)["S1", "H1", "X1Conv", "E1", 1]
    ) == pytest.approx(11.1111111111)
    assert value(
        getattr(model, conv_tech_model.VAR_CONVTECHOUT)["S1", "H1", "X1Conv", "E0", 1]
    ) == pytest.approx(10)
    assert value(
        getattr(model, demand_model.VAR_DEMANDSUPPLY)["S1", "H1", "E0", 1]
    ) == pytest.approx(10)
    # Check H2 (storage)
    assert value(
        getattr(model, stor_tech_model.VAR_STORTECHINFLOW)["S1", "H2", "X2Stor", 1]
    ) == pytest.approx(21.37268485)
    assert value(
        getattr(model, stor_tech_model.VAR_STORTECHOUTFLOW)["S1", "H2", "X2Stor", 1]
    ) == pytest.approx(0)
    assert value(
        getattr(model, stor_tech_model.VAR_STORTECHENERGY)["S1", "H2", "X2Stor", 1]
    ) == pytest.approx(0)
    assert value(
        getattr(model, stor_tech_model.VAR_STORTECHENERGY)["S1", "H2", "X2Stor", 2]
    ) == pytest.approx(21.37268485)
    # Check H3 (Solar)
    assert value(
        getattr(model, conv_tech_model.VAR_CONVTECHIN)["S1", "H3", "X3Solar", "E3", 1]
    ) == pytest.approx(20)
    assert value(
        getattr(model, conv_tech_model.VAR_CONVTECHOUT)["S1", "H3", "X3Solar", "E0", 1]
    ) == pytest.approx(10)
    assert value(
        getattr(model, solar_tech_model.VAR_SOLARTECHINCIDENT)["S1", "H3", "X3Solar", 1]
    ) == pytest.approx(20)
    # Check H5 (Load shedding)
    assert value(
        getattr(model, load_shedding_model.VAR_LOADSHEDDING)["S1", "H5", "E0", 1]
    ) == pytest.approx(5)
    assert value(
        getattr(model, demand_model.VAR_DEMANDSUPPLY)["S1", "H5", "E0", 1]
    ) == pytest.approx(5)
    # Check H6 (Load shifting)
    assert value(
        getattr(model, load_shifting_model.VAR_LOADSHIFTINGTOTAL)["S1", "H6", "E0", 1]
    ) == pytest.approx(0)
    assert value(
        getattr(model, load_shifting_model.VAR_LOADSHIFTINGTOTAL)["S1", "H6", "E0", 2]
    ) == pytest.approx(10)
    assert value(
        getattr(model, load_shifting_model.VAR_LOADSHIFTINGTOTAL)["S1", "H6", "E0", 3]
    ) == pytest.approx(-10)
    assert value(
        getattr(model, load_shifting_model.VAR_LOADSHIFTING)["ls1", "S1", "H6", "E0", 1]
    ) == pytest.approx(0)
    assert value(
        getattr(model, load_shifting_model.VAR_LOADSHIFTING)["ls1", "S1", "H6", "E0", 2]
    ) == pytest.approx(10)
    assert value(
        getattr(model, load_shifting_model.VAR_LOADSHIFTING)["ls1", "S1", "H6", "E0", 3]
    ) == pytest.approx(-10)
    assert value(
        getattr(model, load_shifting_model.VAR_LOADSHIFTINGABOVE)[
            "ls1", "S1", "H6", "E0", 2
        ]
    ) == pytest.approx(10)
    assert value(
        getattr(model, load_shifting_model.VAR_LOADSHIFTINGBELOW)[
            "ls1", "S1", "H6", "E0", 2
        ]
    ) == pytest.approx(0)
    assert value(
        getattr(model, load_shifting_model.VAR_LOADSHIFTINGABOVE)[
            "ls1", "S1", "H6", "E0", 3
        ]
    ) == pytest.approx(0)
    assert value(
        getattr(model, load_shifting_model.VAR_LOADSHIFTINGBELOW)[
            "ls1", "S1", "H6", "E0", 3
        ]
    ) == pytest.approx(10)
    assert value(
        getattr(model, load_shifting_model.VAR_LOADSHIFTINGABOVEPEAK)[
            "ls1", "S1", "H6", "E0"
        ]
    ) == pytest.approx(10)
    assert value(
        getattr(model, load_shifting_model.VAR_LOADSHIFTINGBELOWPEAK)[
            "ls1", "S1", "H6", "E0"
        ]
    ) == pytest.approx(10)
    assert value(
        getattr(model, demand_model.VAR_DEMANDSUPPLY)["S1", "H6", "E0", 1]
    ) == pytest.approx(10)
    assert value(
        getattr(model, demand_model.VAR_DEMANDSUPPLY)["S1", "H6", "E0", 2]
    ) == pytest.approx(20)
    # Check H7 (Import & Export)
    assert value(
        getattr(model, import_model.VAR_IMP)["S1", "H7", "E0", 1]
    ) == pytest.approx(5)
    assert value(
        getattr(model, export_model.VAR_EXP)["S1", "H7", "E0", 1]
    ) == pytest.approx(5)
    # Check H8 & H9 (Network)
    assert value(
        getattr(model, network_model.VAR_NETTECHIN)["S1", "H8", "L1", "N1", 1]
    ) == pytest.approx(10.1005017)
    assert value(
        getattr(model, network_model.VAR_NETTECHOUT)["S1", "H9", "L1", "N1", 1]
    ) == pytest.approx(10)
    assert value(
        getattr(model, network_model.VAR_NETLINKIN)["S1", "H8", "L1", "E0", 1]
    ) == pytest.approx(10.1005017)
    assert value(
        getattr(model, network_model.VAR_NETLINKOUT)["S1", "H9", "L1", "E0", 1]
    ) == pytest.approx(10)
    assert value(
        getattr(model, network_model.VAR_NETHUBIN)["S1", "H8", "E0", 1]
    ) == pytest.approx(10.1005017)
    assert value(
        getattr(model, network_model.VAR_NETHUBOUT)["S1", "H9", "E0", 1]
    ) == pytest.approx(10)
    # Check H11 (coupled tech)
    assert value(
        getattr(model, tech_model.VAR_TECHCAP)["S1", "H11", "X11Main"]
    ) == pytest.approx(20)
    assert value(
        getattr(model, tech_model.VAR_TECHCAP)["S1", "H11", "X11Conv"]
    ) == pytest.approx(10)
    # Check H13 (heatpump)
    assert value(
        getattr(model, tech_model.VAR_TECHCAP)["S1", "H13", "X13Hp"]
    ) == pytest.approx(48)
    assert value(
        getattr(model, hp_tech_model.VAR_HPTECHIN)["S1", "H13", "X13Hp", "E13a", 1]
    ) == pytest.approx(7.142857143)
    assert value(
        getattr(model, hp_tech_model.VAR_HPTECHIN)["S1", "H13", "X13Hp", "E13b", 1]
    ) == pytest.approx(14)
    assert value(
        getattr(model, hp_tech_model.VAR_HPTECHIN)["S1", "H13", "X13Hp", "E13d", 1]
    ) == pytest.approx(6.857142857)
    assert value(
        getattr(model, hp_tech_model.VAR_HPTECHOUT)["S1", "H13", "X13Hp", "E0", 1]
    ) == pytest.approx(10)
    assert value(
        getattr(model, hp_tech_model.VAR_HPTECHOUT)["S1", "H13", "X13Hp", "E13c", 1]
    ) == pytest.approx(10)
    assert value(
        getattr(model, hp_tech_model.VAR_HPTECHELECHT)["S1", "H13", "X13Hp", 1]
    ) == pytest.approx(2.857142857)
    assert value(
        getattr(model, hp_tech_model.VAR_HPTECHELECCO)["S1", "H13", "X13Hp", 1]
    ) == pytest.approx(4)  #
    # Check H14 (ebm)
    assert value(
        getattr(model, ebm_tech_model.VAR_EBMTECHINFLOW)["S1", "H14", "X14Ebm", 1]
    ) == pytest.approx(5.600005)
    assert value(
        getattr(model, ebm_tech_model.VAR_EBMTECHOUTFLOW)["S1", "H14", "X14Ebm", 1]
    ) == pytest.approx(5.000005)
    assert value(
        getattr(model, ebm_tech_model.VAR_EBMTECHENERGY)["S1", "H14", "X14Ebm", 1]
    ) == pytest.approx(0)
    assert value(
        getattr(model, ebm_tech_model.VAR_EBMTECHENERGY)["S1", "H14", "X14Ebm", 3]
    ) == pytest.approx(0.4)
    # Check H15 (ATES)
    assert value(
        getattr(model, tech_model.VAR_TECHCAP)["S1", "H15", "X15Ates"]
    ) == pytest.approx(104.359174931735)
    assert value(
        getattr(model, ates_tech_model.VAR_ATESTECHCAPSCHEDULE)[
            "S1", "H15", "X15Ates", "AS15"
        ]
    ) == pytest.approx(104.359174931735)
    assert value(
        getattr(model, ates_tech_model.VAR_ATESTECHELECSCHEDULE)[
            "S1", "H15", "X15Ates", "AS15", 1
        ]
    ) == pytest.approx(50.0)
    assert value(
        getattr(model, ates_tech_model.VAR_ATESTECHELECSCHEDULE)[
            "S1", "H15", "X15Ates", "AS15", 2
        ]
    ) == pytest.approx(50.0)
    assert value(
        getattr(model, ates_tech_model.VAR_ATESTECHELECSCHEDULE)[
            "S1", "H15", "X15Ates", "AS15", 3
        ]
    ) == pytest.approx(60)
    assert value(
        getattr(model, ates_tech_model.VAR_ATESTECHHEATSCHEDULE)[
            "S1", "H15", "X15Ates", "AS15", 1
        ]
    ) == pytest.approx(1000)
    assert value(
        getattr(model, ates_tech_model.VAR_ATESTECHHEATSCHEDULE)[
            "S1", "H15", "X15Ates", "AS15", 2
        ]
    ) == pytest.approx(1000)
    assert value(
        getattr(model, ates_tech_model.VAR_ATESTECHHEATSCHEDULE)[
            "S1", "H15", "X15Ates", "AS15", 3
        ]
    ) == pytest.approx(0)
    assert value(
        getattr(model, ates_tech_model.VAR_ATESTECHCOOLSCHEDULE)[
            "S1", "H15", "X15Ates", "AS15", 1
        ]
    ) == pytest.approx(0)
    assert value(
        getattr(model, ates_tech_model.VAR_ATESTECHCOOLSCHEDULE)[
            "S1", "H15", "X15Ates", "AS15", 2
        ]
    ) == pytest.approx(0)
    assert value(
        getattr(model, ates_tech_model.VAR_ATESTECHCOOLSCHEDULE)[
            "S1", "H15", "X15Ates", "AS15", 3
        ]
    ) == pytest.approx(1000)
    assert value(
        getattr(model, ates_tech_model.VAR_ATESTECHIN)["S1", "H15", "X15Ates", "E0", 1]
    ) == pytest.approx(50)
    assert value(
        getattr(model, ates_tech_model.VAR_ATESTECHIN)["S1", "H15", "X15Ates", "E0", 2]
    ) == pytest.approx(50)
    assert value(
        getattr(model, ates_tech_model.VAR_ATESTECHIN)["S1", "H15", "X15Ates", "E0", 3]
    ) == pytest.approx(60)
    assert value(
        getattr(model, ates_tech_model.VAR_ATESTECHOUT)[
            "S1", "H15", "X15Ates", "E15a", 1
        ]
    ) == pytest.approx(1000)
    assert value(
        getattr(model, ates_tech_model.VAR_ATESTECHOUT)[
            "S1", "H15", "X15Ates", "E15a", 2
        ]
    ) == pytest.approx(1000)
    assert value(
        getattr(model, ates_tech_model.VAR_ATESTECHOUT)[
            "S1", "H15", "X15Ates", "E15a", 3
        ]
    ) == pytest.approx(0)
    assert value(
        getattr(model, ates_tech_model.VAR_ATESTECHOUT)[
            "S1", "H15", "X15Ates", "E15b", 1
        ]
    ) == pytest.approx(0)
    assert value(
        getattr(model, ates_tech_model.VAR_ATESTECHOUT)[
            "S1", "H15", "X15Ates", "E15b", 2
        ]
    ) == pytest.approx(0)
    assert value(
        getattr(model, ates_tech_model.VAR_ATESTECHOUT)[
            "S1", "H15", "X15Ates", "E15b", 3
        ]
    ) == pytest.approx(1000)
    # Clear
    clear_tmp_model()
