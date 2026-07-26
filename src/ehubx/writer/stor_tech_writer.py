"""Storage technology writer module. Writes out information from the
storage technology submodule to files"""

from typing import Optional

import pandas as pd
from pyomo.core import Model, value

from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.tech_data import TechId
from ehubx.data.time_series import TimeSeries
from ehubx.data.unit import DimlessUnit, TimeUnit
from ehubx.data.value import Value
from ehubx.model import ec_model, stor_tech_model
from ehubx.writer.common_writer import (
    DfStBuilder,
    add_to_df_ts_cl,
    add_to_df_ts_hor,
)


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "writ/stor_tech"
"""String identifying the storage technology writer module for logging
purposes"""

SOURCE: str = "stor_tech"
"""Display name for the storage tech module in result files"""

ENTRY_EC: str = "Stored ec"
"""Entry name for storage ec in result files"""

ENTRY_INEFF: str = "Input efficiency (in_eff)"
"""Entry name for storage input parameter 'in_eff' in result files"""

ENTRY_OUTEFF: str = "Output efficiency (out_eff)"
"""Entry name for storage input parameter 'out_eff' in result files"""

ENTRY_CHARGEMAX: str = "Maximal charging speed (charge_max)"
"""Entry name for storage input parameter 'charge_max' in result files"""

ENTRY_DISCHARGEMAX: str = "Maximal discharging speed (discharge_max)"
"""Entry name for storage input parameter 'discharge_max' in result files"""

ENTRY_STANDBYLOSS: str = "Standby loss (standy_loss)"
"""Entry name for storage input parameter 'standby_loss' in result files"""

ENTRY_SOCMIN: str = "Minimal SOC (soc_min)"
"""Entry name for storage input parameter 'soc_min' in result files"""

ENTRY_SOCMAX: str = "Maximal SOC (soc_max)"
"""Entry name for storage input parameter 'soc_max' in result files"""

ENTRY_SOCINIT: str = "Initial SOC (soc_init)"
"""Entry name for storage input parameter 'soc_init' in result files"""

ENTRY_INFLOW: str = f"Storage inflow ({stor_tech_model.VAR_STORTECHINFLOW})"
"""Entry name for storage inflow variable in result files"""

ENTRY_OUTFLOW: str = f"Storage outflow ({stor_tech_model.VAR_STORTECHOUTFLOW})"
"""Entry name for storage outflow variable in result files"""

ENTRY_ENERGY: str = f"Storage energy ({stor_tech_model.VAR_STORTECHENERGY})"
"""Entry name for storage energy variable in result files"""

ENTRY_STORTECHFILLCOST: str = (
    f"Storage fill cost ({stor_tech_model.VAR_STORTECHFILLCOST})"
)
"""Entry name for storage fill cost variable in result files"""

ENTRY_STORTECHFILLCOSTTOTAL: str = (
    f"Total storage fill cost ({stor_tech_model.VAR_STORTECHFILLCOSTTOTAL})"
)
"""Entry name for total storage fill cost variable in result files"""

ENTRY_STORTECHENERGYFINAL: str = (
    f"Final storage energy ({stor_tech_model.VAR_STORTECHENERGYFINAL})"
)
"""Entry name for final storage energy level in result files"""


def format_all(
    energy_system: EnergySystem,
    model: Model,
    df_st_builder: DfStBuilder,
    df_ts_hor: pd.DataFrame,
    df_ts_cl: Optional[pd.DataFrame],
) -> None:
    # Tech-specific properties
    for tech_id in energy_system.stor_techs.ids_in_order:
        _format_tech(energy_system, model, tech_id, df_st_builder, df_ts_hor, df_ts_cl)
    # Total storage fill cost
    var = getattr(model, stor_tech_model.VAR_STORTECHFILLCOSTTOTAL)
    total_fill_cost_fl = value(var, exception=False)
    if total_fill_cost_fl is not None:
        total_fill_cost = Value(total_fill_cost_fl, unit=energy_system.currency_unit)
        df_st_builder.add_row(
            ENTRY_STORTECHFILLCOSTTOTAL,
            total_fill_cost,
            unit=energy_system.currency_unit,
            source=SOURCE,
            in_res="result",
        )


def _format_tech(
    energy_system: EnergySystem,
    model: Model,
    x: TechId,
    df_st_builder: DfStBuilder,
    df_ts_hor: pd.DataFrame,
    df_ts_cl: Optional[pd.DataFrame],
) -> None:
    # ec
    ec = energy_system.stor_techs.get_ec(x)
    df_st_builder.add_row(ENTRY_EC, ec.key, tech=x.key, source=SOURCE, in_res="input")

    # in_eff
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        in_eff = energy_system.stor_techs.get_in_eff(s, x)
        df_st_builder.add_row(
            ENTRY_INEFF,
            in_eff,
            unit=DimlessUnit(),
            stage=s.key,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # out_eff
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        out_eff = energy_system.stor_techs.get_out_eff(s, x)
        df_st_builder.add_row(
            ENTRY_OUTEFF,
            out_eff,
            unit=DimlessUnit(),
            stage=s.key,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # charge_max
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        charge_max = energy_system.stor_techs.get_charge_max(s, x)
        df_st_builder.add_row(
            ENTRY_CHARGEMAX,
            charge_max,
            unit=(DimlessUnit() / TimeUnit.H),
            stage=s.key,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # discharge_max
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        discharge_max = energy_system.stor_techs.get_discharge_max(s, x)
        df_st_builder.add_row(
            ENTRY_DISCHARGEMAX,
            discharge_max,
            unit=(DimlessUnit() / TimeUnit.H),
            stage=s.key,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # standby_loss
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        standby_loss = energy_system.stor_techs.get_standby_loss(s, x)
        df_st_builder.add_row(
            ENTRY_STANDBYLOSS,
            standby_loss,
            unit=(DimlessUnit() / TimeUnit.H),
            stage=s.key,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # soc_min
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        soc_min = energy_system.stor_techs.get_soc_min(s, x)
        df_st_builder.add_row(
            ENTRY_SOCMIN,
            soc_min,
            unit=DimlessUnit(),
            stage=s.key,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # soc_max
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        soc_max = energy_system.stor_techs.get_soc_max(s, x)
        df_st_builder.add_row(
            ENTRY_SOCMAX,
            soc_max,
            unit=DimlessUnit(),
            stage=s.key,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # soc_init
    for h in energy_system.hubs.ids_in_order:
        if h not in energy_system.techs.get_allowed_hubs(x):
            continue
        soc_init = energy_system.stor_techs.get_soc_init(h, x)
        df_st_builder.add_row(
            ENTRY_SOCMAX,
            soc_init,
            unit=DimlessUnit(),
            hub=h.key,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # Storage inflow
    ec_unit = ec_model.get_ec_model_unit(
        energy_system.ecs.get_unit(energy_system.stor_techs.get_ec(x)),
        energy_system.mass_unit,
        energy_system.power_unit,
    )
    flow_unit = ec_unit / TimeUnit.H
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, stor_tech_model.VAR_STORTECHINFLOW)
            inflow = TimeSeries()
            for t in energy_system.times.ids:
                inflow_fl = value(
                    var[s.key, h.key, x.key, t.key_as_int], exception=False
                )
                if inflow_fl is not None:
                    inflow.set_value(t, Value(inflow_fl, unit=flow_unit))
            add_to_df_ts_cl(
                df_ts_hor,
                df_ts_cl,
                energy_system.times,
                ENTRY_INFLOW,
                inflow,
                unit=flow_unit,
                stage=s.key,
                hub=h.key,
                tech=x.key,
                source=SOURCE,
                in_res="result",
            )

    # Storage outflow
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, stor_tech_model.VAR_STORTECHOUTFLOW)
            outflow = TimeSeries()
            for t in energy_system.times.ids:
                outflow_fl = value(
                    var[s.key, h.key, x.key, t.key_as_int], exception=False
                )
                if outflow_fl is not None:
                    outflow.set_value(t, Value(outflow_fl, unit=flow_unit))
            add_to_df_ts_cl(
                df_ts_hor,
                df_ts_cl,
                energy_system.times,
                ENTRY_OUTFLOW,
                outflow,
                unit=flow_unit,
                stage=s.key,
                hub=h.key,
                tech=x.key,
                source=SOURCE,
                in_res="result",
            )

    # Storage energy
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, stor_tech_model.VAR_STORTECHENERGY)
            energy = TimeSeries()
            for t in energy_system.times.ids_horizon:
                energy_fl = value(
                    var[s.key, h.key, x.key, t.key_as_int], exception=False
                )
                if energy_fl is not None:
                    energy.set_value(t, Value(energy_fl, unit=ec_unit))
            add_to_df_ts_hor(
                df_ts_hor,
                energy_system.times,
                ENTRY_ENERGY,
                energy,
                unit=ec_unit,
                stage=s.key,
                hub=h.key,
                tech=x.key,
                source=SOURCE,
                in_res="result",
            )

    # Storage fill cost
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, stor_tech_model.VAR_STORTECHFILLCOST)
            fill_cost_fl = value(var[s.key, h.key, x.key], exception=False)
            if fill_cost_fl is not None:
                fill_cost = Value(fill_cost_fl, unit=energy_system.currency_unit)
                df_st_builder.add_row(
                    ENTRY_STORTECHFILLCOST,
                    fill_cost,
                    unit=energy_system.currency_unit,
                    stage=s.key,
                    hub=h.key,
                    tech=x.key,
                    source=SOURCE,
                    in_res="result",
                )

    # Final storage energy (non-cyclic storage)
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, stor_tech_model.VAR_STORTECHENERGYFINAL)
            energy_final_fl = value(var[s.key, h.key, x.key], exception=False)
            if energy_final_fl is not None:
                ec_id = energy_system.stor_techs.get_ec(x)
                energy_unit = ec_model.get_ec_model_unit(
                    energy_system.ecs.get_unit(ec_id),
                    energy_system.mass_unit,
                    energy_system.power_unit,
                )
                df_st_builder.add_row(
                    ENTRY_STORTECHENERGYFINAL,
                    Value(energy_final_fl, unit=energy_unit),
                    unit=energy_unit,
                    stage=s.key,
                    hub=h.key,
                    tech=x.key,
                    source=SOURCE,
                    in_res="result",
                )
