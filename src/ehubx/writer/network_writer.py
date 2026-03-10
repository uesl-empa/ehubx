"""Network link writer module. Writes out information from the network
submodule to files"""

import os
from typing import Dict, List, Optional, Tuple

import pandas as pd
from pyomo.core import Model, value

from ehubx.core import exceptions
from ehubx.core.common import TimeSeriesKind
from ehubx.data.ec_data import EcId
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.net_link_data import NetLinkDirection, NetLinkId
from ehubx.data.net_tech_data import NetTechId
from ehubx.data.time_series import TimeSeries
from ehubx.data.unit import DimlessUnit, TimeUnit
from ehubx.data.value import Value
from ehubx.model import ec_model, network_model
from ehubx.parser.csv_parser import HeaderId
from ehubx.parser.net_link_parser import YAMLKEY_AVAILABILITY
from ehubx.writer.common_writer import (
    DfStBuilder,
    DfStColumn,
    FileGranularity,
    add_to_df_ts_cl,
    create_dir,
    init_df_ts_cl,
    init_df_ts_hor,
)


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "writ/net_link"
"""String identifying the network link writer module for logging purposes"""

FILENAME_NETWORK: str = "network"
"""Filename for for all network-related data (network links & network techs)"""

FILENAME_TIMESERIES_NETLINKS: str = "network_links.csv"
"""Filename for network link time series"""

SOURCE: str = "network"
"""Display name for the network module in result files"""

ENTRY_HUBSTART: str = "Link start hub"
"""Entry name for network link parameter 'hub_start' in result files"""

ENTRY_HUBEND: str = "Link end hub"
"""Entry name for network link parameter 'hub_end' in result files"""

ENTRY_LENGTH: str = "Link length"
"""Entry name for network link parameter 'length' in result files"""

ENTRY_BIDIRECTIONAL: str = "Link bidirectional?"
"""Entry name for network link parameter 'bidirectional' in result files"""

ENTRY_CAPMIN: str = "Minimal link capacity (cap_min)"
"""Entry name for network link parameter 'cap_min' in result files"""

ENTRY_CAPMAX: str = "Maximal link capacity (cap_max)"
"""Entry name for network link parameter 'cap_max' in result files"""

ENTRY_AVAILABILITY: str = "Link availability (availability)"
"""Entry name for network link parameter 'availability' in result files"""

ENTRY_SUMMIN: str = "Minimal summed-up link transmission (sum_min)"
"""Entry name for network link parameter 'sum_min' in result files"""

ENTRY_SUMMAX: str = "Maximal summed-up link transmission (sum_max)"
"""Entry name for network link parameter 'sum_max' in result files"""

ENTRY_ALLOWEDINSTAGE: str = "Allowed in stage?"
"""Entry name monitoring whether a network tech is allowed in a stage, in
result files"""

ENTRY_ALLOWEDONLINK: str = "Allowed on link?"
"""Entry name monitoring whether a network tech is allowed on a link, in
result files"""

ENTRY_EC: str = "Network tech ec"
"""Entry name for network tech parameter 'ec' in result files"""

ENTRY_LIFETIME: str = "Lifetime"
"""Entry name for network tech parameter 'lifetime' in result files"""

ENTRY_INTERESTRATE: str = "Interest rate"
"""Entry name for network tech parameter 'interest_rate' in result files"""

ENTRY_UNITCAPMIN: str = "Minimal amount of installable capacity (unit_cap_min)"
"""Entry name for network tech parameter 'unit_cap_min' in result files"""

ENTRY_ONETIMECAPEX: str = "Fixed CAPEX installation price (one_time_capex)"
"""Entry name for network tech parameter 'one_time_capex' in result files"""

ENTRY_CAPEXPERCAP: str = "CAPEX price per installed capacity (capex_per_cap)"
"""Entry name for network tech parameter 'capex_per_cap' in result files"""

ENTRY_ONETIMEOPEX: str = "Fixed OPEX price (one_time_opex)"
"""Entry name for network tech parameter 'one_time_opex' in result files"""

ENTRY_OPEXPERCAP: str = "OPEX price per capacity (opex_per_cap)"
"""Entry name for network tech parameter 'opex_per_cap' in result files"""

ENTRY_OPEXPERENERGY: str = "OPEX price per transmitted energy (opex_per_energy)"
"""Entry name for network tech parameter 'opex_per_energy' in result files"""

ENTRY_CO2PERCAP: str = "Embodied CO2 per installed capacity (co2_per_cap)"
"""Entry name for network tech parameter 'co2_per_cap' in result files"""

ENTRY_CO2PERENERGY: str = "Embodied CO2 per transmitted energy (co2_per_energy)"
"""Entry name for network tech parameter 'co2_per_energy' in result files"""

ENTRY_TRANSDECAY: str = "Transmission decay (trans_decay)"
"""Entry name for network tech parameter 'trans_decay' in result files"""

ENTRY_CAPINIT: str = "Initially installed capacity (cap_init)"
"""Entry name for network parameter 'cap_init' in result files"""

ENTRY_AGEINIT: str = "Age of initially installed capacity (age_init)"
"""Entry name for network parameter 'age_init' in result files"""

ENTRY_NETHUBIN: str = f"Network hub input ({network_model.VAR_NETHUBIN})"
"""Entry name for network hub input variable in result files"""

ENTRY_NETHUBOUT: str = f"Network hub output ({network_model.VAR_NETHUBOUT})"
"""Entry name for network hub output variable in result files"""

ENTRY_NETLINKIN: str = f"Network link input ({network_model.VAR_NETLINKIN})"
"""Entry name for network link input variable in result files"""

ENTRY_NETLINKOUT: str = f"Network link output ({network_model.VAR_NETLINKOUT})"
"""Entry name for network link output variable in result files"""

ENTRY_NETTECHIN: str = f"Network tech input ({network_model.VAR_NETTECHIN})"
"""Entry name for network tech input variable in result files"""

ENTRY_NETTECHOUT: str = f"Network tech output ({network_model.VAR_NETTECHOUT})"
"""Entry name for network tech output variable in result files"""

ENTRY_YNETTECHUSED: str = f"Network tech used? ({network_model.VAR_YNETTECHUSED})"
"""Entry name for network tech usage variable in result files"""

ENTRY_NETTECHCAP: str = f"Network tech capacity ({network_model.VAR_NETTECHCAP})"
"""Entry name for network tech capacity variable in result files"""

ENTRY_NETTECHCAPINSTL: str = (
    f"Network tech capacity installation ({network_model.VAR_NETTECHCAPINSTL})"
)
"""Entry name for network tech capacity installation variable in result
files"""

ENTRY_YNETTECHCAPINSTL: str = (
    f"Any network tech capacity installation? ({network_model.VAR_YNETTECHCAPINSTL})"
)
"""Entry name for binary variable monitoring network tech capacity
installation in result files"""

ENTRY_NETTECHCOSTCAPEX: str = (
    f"CAPEX installation costs ({network_model.VAR_NETTECHCOSTCAPEX})"
)
"""Entry name for network tech CAPEX cost variable in result files"""

ENTRY_NETTECHCOSTOPEXCAP: str = (
    f"OPEX capacity costs ({network_model.VAR_NETTECHCOSTOPEXCAP})"
)
"""Entry name for network tech OPEX cost variable per capacity in result
files"""

ENTRY_NETTECHCOSTOPEXTRANS: str = (
    f"OPEX transmission costs ({network_model.VAR_NETTECHCOSTOPEXTRANS})"
)
"""Entry name for network tech OPEX cost variable per transmission in result
files"""

ENTRY_NETTECHCOSTTOTAL: str = (
    f"Total network tech costs ({network_model.VAR_NETTECHCOSTTOTAL})"
)
"""Entry name for total network tech cost variable in result files"""

ENTRY_NETTECHCO2INSTL: str = (
    f"Embodied CO2 from network tech installation ({network_model.VAR_NETTECHCO2INSTL})"
)
"""Entry name for embodied CO2 variable for network tech installation in
result files"""

ENTRY_NETTECHCO2TRANS: str = (
    f"Embodied CO2 from network transmissions ({network_model.VAR_NETTECHCO2TRANS})"
)
"""Entry name for embodied CO2 variable for network transmissions in result
files"""

ENTRY_NETTECHCO2TOTAL: str = (
    f"Total embodied CO2 from network techs ({network_model.VAR_NETTECHCO2TOTAL})"
)
"""Entry name for total embodied CO2 variable for network techs in result
files"""


def format_all(
    energy_system: EnergySystem,
    model: Model,
    dir_path: str,
    file_granularity: FileGranularity = FileGranularity.DEFAULT,
) -> List[Tuple[pd.DataFrame, str]]:
    # Initialize dataframes
    dfs: List[Tuple[pd.DataFrame, str]] = []
    df_st_builder = DfStBuilder()
    df_ts_hor = init_df_ts_hor(energy_system.times)
    df_ts_cl: Optional[pd.DataFrame] = None
    if energy_system.times.is_clustered:
        df_ts_cl = init_df_ts_cl(energy_system.times)

    # Total CO2
    var = getattr(model, network_model.VAR_NETTECHCO2TOTAL)
    for s in energy_system.stages.ids_in_order:
        co2_total_fl = value(var[s.key], exception=False)
        if co2_total_fl is not None:
            co2_total = Value(co2_total_fl, unit=energy_system.mass_unit)
            df_st_builder.add_row(
                ENTRY_NETTECHCO2TOTAL,
                co2_total,
                unit=energy_system.mass_unit,
                stage=s.key,
                source=SOURCE,
                in_res="result",
            )

    # Network hub input
    var = getattr(model, network_model.VAR_NETHUBIN)
    for s in energy_system.stages.ids_in_order:
        for h_, e_ in getattr(model, network_model.SET_NETHUBIN):
            ec_unit = ec_model.get_ec_model_unit(
                energy_system.ecs.get_unit(EcId(e_)),
                energy_system.mass_unit,
                energy_system.power_unit,
            )
            flow_unit = ec_unit / TimeUnit.H
            hub_in = TimeSeries()
            for t in energy_system.times.ids:
                hub_in_fl = value(var[s.key, h_, e_, t.key_as_int], exception=False)
                if hub_in_fl is not None:
                    hub_in.set_value(t, Value(hub_in_fl, flow_unit))
            add_to_df_ts_cl(
                df_ts_hor,
                df_ts_cl,
                energy_system.times,
                ENTRY_NETHUBIN,
                hub_in,
                unit=flow_unit,
                stage=s.key,
                hub=h_,
                ec=e_,
                source=SOURCE,
                in_res="result",
            )

    # Network hub output
    var = getattr(model, network_model.VAR_NETHUBOUT)
    for s in energy_system.stages.ids_in_order:
        for h_, e_ in getattr(model, network_model.SET_NETHUBOUT):
            ec_unit = ec_model.get_ec_model_unit(
                energy_system.ecs.get_unit(EcId(e_)),
                energy_system.mass_unit,
                energy_system.power_unit,
            )
            flow_unit = ec_unit / TimeUnit.H
            hub_out = TimeSeries()
            for t in energy_system.times.ids:
                hub_out_fl = value(var[s.key, h_, e_, t.key_as_int], exception=False)
                if hub_out_fl is not None:
                    hub_out.set_value(t, Value(hub_out_fl, flow_unit))
            add_to_df_ts_cl(
                df_ts_hor,
                df_ts_cl,
                energy_system.times,
                ENTRY_NETHUBOUT,
                hub_out,
                unit=flow_unit,
                stage=s.key,
                hub=h_,
                ec=e_,
                source=SOURCE,
                in_res="result",
            )

    # Link-specific values
    for li in energy_system.net_links.ids_in_order:
        _format_link(energy_system, model, li, df_st_builder, df_ts_hor, df_ts_cl)

    # Tech-specific values
    for n in energy_system.net_techs.ids_in_order:
        _format_tech(energy_system, model, n, df_st_builder)

    # Remove ununsed columns
    cols_to_drop_st = {DfStColumn.TECH, DfStColumn.LOAD_SHIFT}
    cols_to_drop_ts = [DfStColumn.TECH.value, DfStColumn.LOAD_SHIFT.value]
    df_ts_hor.columns = df_ts_hor.columns.droplevel(cols_to_drop_ts)
    if df_ts_cl is not None:
        df_ts_cl.columns = df_ts_cl.columns.droplevel(cols_to_drop_ts)

    # Build all-in-one dataframe
    df_st = df_st_builder.build(drop_columns=cols_to_drop_st)

    # Format for minimal file granularity
    dfs = _format_file_granularity(
        df_st, df_ts_hor, df_ts_cl, dir_path, file_granularity
    )

    # Return
    return dfs


def _format_link(
    energy_system: EnergySystem,
    model: Model,
    li: NetLinkId,
    df_st_builder: DfStBuilder,
    df_ts_hor: pd.DataFrame,
    df_ts_cl: Optional[pd.DataFrame],
) -> None:
    # hub_start
    hub_start = energy_system.net_links.get_hub_start(li)
    df_st_builder.add_row(
        ENTRY_HUBSTART,
        hub_start.key,
        net_link=li.key,
        source=SOURCE,
        in_res="input",
    )

    # hub_end
    hub_end = energy_system.net_links.get_hub_end(li)
    df_st_builder.add_row(
        ENTRY_HUBEND,
        hub_end.key,
        net_link=li.key,
        source=SOURCE,
        in_res="input",
    )

    # bidirectional
    bidirectional = energy_system.net_links.is_bidirectional(li)
    df_st_builder.add_row(
        ENTRY_BIDIRECTIONAL,
        bidirectional,
        net_link=li.key,
        source=SOURCE,
        in_res="input",
    )

    # length
    length = energy_system.net_links.get_length(li)
    df_st_builder.add_row(
        ENTRY_LENGTH,
        length,
        unit=energy_system.length_unit,
        net_link=li.key,
        source=SOURCE,
        in_res="input",
    )

    # cap_min
    for s in energy_system.stages.ids_in_order:
        for e in energy_system.ecs.ids_in_order:
            if e not in energy_system.net_links.get_ecs(li):
                continue
            ec_unit = ec_model.get_ec_model_unit(
                energy_system.ecs.get_unit(e),
                energy_system.mass_unit,
                energy_system.power_unit,
            )
            cap_min = energy_system.net_links.get_cap_min(s, li, e)
            cap_unit = ec_unit / TimeUnit.H
            df_st_builder.add_row(
                ENTRY_CAPMIN,
                cap_min,
                unit=cap_unit,
                stage=s.key,
                ec=e.key,
                net_link=li.key,
                source=SOURCE,
                in_res="input",
            )

    # cap_max
    for s in energy_system.stages.ids_in_order:
        for e in energy_system.ecs.ids_in_order:
            if e not in energy_system.net_links.get_ecs(li):
                continue
            ec_unit = ec_model.get_ec_model_unit(
                energy_system.ecs.get_unit(e),
                energy_system.mass_unit,
                energy_system.power_unit,
            )
            cap_max = energy_system.net_links.get_cap_max(s, li, e)
            cap_unit = ec_unit / TimeUnit.H
            df_st_builder.add_row(
                ENTRY_CAPMAX,
                cap_max,
                unit=cap_unit,
                stage=s.key,
                ec=e.key,
                net_link=li.key,
                source=SOURCE,
                in_res="input",
            )

    # availability
    for s in energy_system.stages.ids_in_order:
        for e in energy_system.ecs.ids_in_order:
            if e not in energy_system.net_links.get_ecs(li):
                continue
            availability = energy_system.net_links.get_availability(s, li, e)
            if availability.has_values:
                add_to_df_ts_cl(
                    df_ts_hor,
                    df_ts_cl,
                    energy_system.times,
                    ENTRY_AVAILABILITY,
                    availability,
                    unit=DimlessUnit(),
                    stage=s.key,
                    ec=e.key,
                    net_link=li.key,
                    source=SOURCE,
                    in_res="input",
                )
            if not availability.has_values:
                availability_def = availability.def_value
                assert availability_def is not None
                df_st_builder.add_row(
                    ENTRY_AVAILABILITY,
                    availability_def,
                    unit=DimlessUnit(),
                    stage=s.key,
                    ec=e.key,
                    net_link=li.key,
                    source=SOURCE,
                    in_res="input",
                )

    # sum_min
    for s in energy_system.stages.ids_in_order:
        for e in energy_system.ecs.ids_in_order:
            if e not in energy_system.net_links.get_ecs(li):
                continue
            ec_unit = ec_model.get_ec_model_unit(
                energy_system.ecs.get_unit(e),
                energy_system.mass_unit,
                energy_system.power_unit,
            )
            sum_min = energy_system.net_links.get_sum_min(
                s, li, e, NetLinkDirection.FORWARD
            )
            df_st_builder.add_row(
                ENTRY_SUMMIN,
                sum_min,
                unit=ec_unit,
                stage=s.key,
                ec=e.key,
                net_link=li.key,
                net_link_dir=NetLinkDirection.FORWARD.value,
                source=SOURCE,
                in_res="input",
            )
            if energy_system.net_links.is_bidirectional(li):
                sum_min = energy_system.net_links.get_sum_min(
                    s, li, e, NetLinkDirection.BACKWARD
                )
                df_st_builder.add_row(
                    ENTRY_SUMMIN,
                    sum_min,
                    unit=ec_unit,
                    stage=s.key,
                    ec=e.key,
                    net_link=li.key,
                    net_link_dir=NetLinkDirection.BACKWARD.value,
                    source=SOURCE,
                    in_res="input",
                )

    # sum_max
    for s in energy_system.stages.ids_in_order:
        for e in energy_system.ecs.ids_in_order:
            if e not in energy_system.net_links.get_ecs(li):
                continue
            ec_unit = ec_model.get_ec_model_unit(
                energy_system.ecs.get_unit(e),
                energy_system.mass_unit,
                energy_system.power_unit,
            )
            sum_max = energy_system.net_links.get_sum_max(
                s, li, e, NetLinkDirection.FORWARD
            )
            df_st_builder.add_row(
                ENTRY_SUMMAX,
                sum_max,
                unit=ec_unit,
                stage=s.key,
                ec=e.key,
                net_link=li.key,
                net_link_dir=NetLinkDirection.FORWARD.value,
                source=SOURCE,
                in_res="input",
            )
            if energy_system.net_links.is_bidirectional(li):
                sum_max = energy_system.net_links.get_sum_max(
                    s, li, e, NetLinkDirection.BACKWARD
                )
                df_st_builder.add_row(
                    ENTRY_SUMMAX,
                    sum_max,
                    unit=ec_unit,
                    stage=s.key,
                    ec=e.key,
                    net_link=li.key,
                    net_link_dir=NetLinkDirection.BACKWARD.value,
                    source=SOURCE,
                    in_res="input",
                )

    # Network link input
    var = getattr(model, network_model.VAR_NETLINKIN)
    for s in energy_system.stages.ids_in_order:
        for h_, li_, e_ in getattr(model, network_model.SET_NETLINKIN):
            if li.key != li_:
                continue
            ec_unit = ec_model.get_ec_model_unit(
                energy_system.ecs.get_unit(EcId(e_)),
                energy_system.mass_unit,
                energy_system.power_unit,
            )
            flow_unit = ec_unit / TimeUnit.H
            link_in = TimeSeries()
            for t in energy_system.times.ids:
                link_in_fl = value(
                    var[s.key, h_, li_, e_, t.key_as_int], exception=False
                )
                if link_in_fl is not None:
                    link_in.set_value(t, Value(link_in_fl, flow_unit))
            add_to_df_ts_cl(
                df_ts_hor,
                df_ts_cl,
                energy_system.times,
                ENTRY_NETLINKIN,
                link_in,
                unit=flow_unit,
                stage=s.key,
                hub=h_,
                ec=e_,
                net_link=li_,
                source=SOURCE,
                in_res="result",
            )

    # Network link output
    var = getattr(model, network_model.VAR_NETLINKOUT)
    for s in energy_system.stages.ids_in_order:
        for h_, li_, e_ in getattr(model, network_model.SET_NETLINKOUT):
            if li.key != li_:
                continue
            ec_unit = ec_model.get_ec_model_unit(
                energy_system.ecs.get_unit(EcId(e_)),
                energy_system.mass_unit,
                energy_system.power_unit,
            )
            flow_unit = ec_unit / TimeUnit.H
            link_out = TimeSeries()
            for t in energy_system.times.ids:
                link_out_fl = value(
                    var[s.key, h_, li_, e_, t.key_as_int], exception=False
                )
                if link_out_fl is not None:
                    link_out.set_value(t, Value(link_out_fl, flow_unit))
            add_to_df_ts_cl(
                df_ts_hor,
                df_ts_cl,
                energy_system.times,
                ENTRY_NETLINKOUT,
                link_out,
                unit=flow_unit,
                stage=s.key,
                hub=h_,
                ec=e_,
                net_link=li_,
                source=SOURCE,
                in_res="result",
            )

    # Network tech input
    var = getattr(model, network_model.VAR_NETTECHIN)
    for s_, h_, li_, n_ in getattr(model, network_model.SET_NETTECHIN):
        if li.key != li_:
            continue
        e = energy_system.net_techs.get_ec(NetTechId(n_))
        ec_unit = ec_model.get_ec_model_unit(
            energy_system.ecs.get_unit(e),
            energy_system.mass_unit,
            energy_system.power_unit,
        )
        flow_unit = ec_unit / TimeUnit.H
        tech_in = TimeSeries()
        for t in energy_system.times.ids:
            tech_in_fl = value(var[s_, h_, li_, n_, t.key_as_int], exception=False)
            if tech_in_fl is not None:
                tech_in.set_value(t, Value(tech_in_fl, flow_unit))
        add_to_df_ts_cl(
            df_ts_hor,
            df_ts_cl,
            energy_system.times,
            ENTRY_NETTECHIN,
            tech_in,
            unit=flow_unit,
            stage=s_,
            hub=h_,
            ec=e.key,
            net_link=li_,
            net_tech=n_,
            source=SOURCE,
            in_res="result",
        )

    # Network tech output
    var = getattr(model, network_model.VAR_NETTECHOUT)
    for s_, h_, li_, n_ in getattr(model, network_model.SET_NETTECHOUT):
        if li.key != li_:
            continue
        e = energy_system.net_techs.get_ec(NetTechId(n_))
        ec_unit = ec_model.get_ec_model_unit(
            energy_system.ecs.get_unit(e),
            energy_system.mass_unit,
            energy_system.power_unit,
        )
        flow_unit = ec_unit / TimeUnit.H
        tech_out = TimeSeries()
        for t in energy_system.times.ids:
            tech_out_fl = value(var[s_, h_, li_, n_, t.key_as_int], exception=False)
            if tech_out_fl is not None:
                tech_out.set_value(t, Value(tech_out_fl, flow_unit))
        add_to_df_ts_cl(
            df_ts_hor,
            df_ts_cl,
            energy_system.times,
            ENTRY_NETTECHOUT,
            tech_out,
            unit=flow_unit,
            stage=s_,
            hub=h_,
            ec=e.key,
            net_link=li_,
            net_tech=n_,
            source=SOURCE,
            in_res="result",
        )


def _format_tech(
    energy_system: EnergySystem, model: Model, n: NetTechId, df_st_builder: DfStBuilder
) -> None:
    # ec
    ec = energy_system.net_techs.get_ec(n)
    ec_unit = ec_model.get_ec_model_unit(
        energy_system.ecs.get_unit(ec),
        energy_system.mass_unit,
        energy_system.power_unit,
    )
    cap_unit = ec_unit / TimeUnit.H
    # Allowed stages
    for s in energy_system.stages.ids_in_order:
        allowed_in_stage = s in energy_system.net_techs.get_allowed_stages(n)
        df_st_builder.add_row(
            ENTRY_ALLOWEDINSTAGE,
            allowed_in_stage,
            stage=s.key,
            net_tech=n.key,
            source=SOURCE,
            in_res="input",
        )

    # Allowed links
    for li in energy_system.net_links.ids_in_order:
        allowed_on_link = li in energy_system.net_techs.get_allowed_net_links(n)
        df_st_builder.add_row(
            ENTRY_ALLOWEDONLINK,
            allowed_on_link,
            net_link=li.key,
            net_tech=n.key,
            source=SOURCE,
            in_res="input",
        )

    # ec
    df_st_builder.add_row(
        ENTRY_EC, ec.key, net_tech=n.key, source=SOURCE, in_res="input"
    )

    # lifetime
    lifetime = energy_system.net_techs.get_lifetime(n)
    df_st_builder.add_row(
        ENTRY_LIFETIME,
        lifetime,
        unit=TimeUnit.H,
        net_tech=n.key,
        source=SOURCE,
        in_res="input",
    )

    # interest_rate
    interest_rate = energy_system.net_techs.get_interest_rate(n)
    df_st_builder.add_row(
        ENTRY_INTERESTRATE,
        interest_rate,
        unit=DimlessUnit(),
        net_tech=n.key,
        source=SOURCE,
        in_res="input",
    )

    # unit_cap_min
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.net_techs.get_allowed_stages(n):
            continue
        unit_cap_min = energy_system.net_techs.get_unit_cap_min(s, n)
        df_st_builder.add_row(
            ENTRY_UNITCAPMIN,
            unit_cap_min,
            unit=cap_unit,
            stage=s.key,
            net_tech=n.key,
            source=SOURCE,
            in_res="input",
        )

    # one_time_capex
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.net_techs.get_allowed_stages(n):
            continue
        one_time_capex = energy_system.net_techs.get_one_time_capex(s, n)
        df_st_builder.add_row(
            ENTRY_ONETIMECAPEX,
            one_time_capex,
            unit=(energy_system.currency_unit / energy_system.length_unit),
            stage=s.key,
            net_tech=n.key,
            source=SOURCE,
            in_res="input",
        )

    # capex_per_cap
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.net_techs.get_allowed_stages(n):
            continue
        capex_per_cap = energy_system.net_techs.get_capex_per_cap(s, n)
        capex_per_cap_unit = energy_system.currency_unit / (
            cap_unit * energy_system.length_unit
        )
        df_st_builder.add_row(
            ENTRY_CAPEXPERCAP,
            capex_per_cap,
            unit=capex_per_cap_unit,
            stage=s.key,
            net_tech=n.key,
            source=SOURCE,
            in_res="input",
        )

    # one_time_opex
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.net_techs.get_allowed_stages(n):
            continue
        one_time_opex = energy_system.net_techs.get_one_time_opex(s, n)
        df_st_builder.add_row(
            ENTRY_ONETIMEOPEX,
            one_time_opex,
            unit=(energy_system.currency_unit / energy_system.length_unit),
            stage=s.key,
            net_tech=n.key,
            source=SOURCE,
            in_res="input",
        )

    # opex_per_cap
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.net_techs.get_allowed_stages(n):
            continue
        opex_per_cap = energy_system.net_techs.get_opex_per_cap(s, n)
        opex_per_cap_unit = energy_system.currency_unit / (
            cap_unit * energy_system.length_unit
        )
        df_st_builder.add_row(
            ENTRY_OPEXPERCAP,
            opex_per_cap,
            unit=opex_per_cap_unit,
            stage=s.key,
            net_tech=n.key,
            source=SOURCE,
            in_res="input",
        )

    # opex_per_energy
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.net_techs.get_allowed_stages(n):
            continue
        opex_per_energy = energy_system.net_techs.get_opex_per_energy(s, n)
        opex_per_energy_unit = energy_system.currency_unit / (
            ec_unit * energy_system.length_unit
        )
        df_st_builder.add_row(
            ENTRY_OPEXPERENERGY,
            opex_per_energy,
            unit=opex_per_energy_unit,
            stage=s.key,
            net_tech=n.key,
            source=SOURCE,
            in_res="input",
        )

    # co2_per_cap
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.net_techs.get_allowed_stages(n):
            continue
        co2_per_cap = energy_system.net_techs.get_co2_per_cap(s, n)
        co2_per_cap_unit = energy_system.mass_unit / (
            cap_unit * energy_system.length_unit
        )
        df_st_builder.add_row(
            ENTRY_CO2PERCAP,
            co2_per_cap,
            unit=co2_per_cap_unit,
            stage=s.key,
            net_tech=n.key,
            source=SOURCE,
            in_res="input",
        )

    # co2_per_energy
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.net_techs.get_allowed_stages(n):
            continue
        co2_per_energy = energy_system.net_techs.get_co2_per_energy(s, n)
        co2_per_energy_unit = energy_system.mass_unit / (
            ec_unit * energy_system.length_unit
        )
        df_st_builder.add_row(
            ENTRY_CO2PERENERGY,
            co2_per_energy,
            unit=co2_per_energy_unit,
            stage=s.key,
            net_tech=n.key,
            source=SOURCE,
            in_res="input",
        )

    # trans_decay
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.net_techs.get_allowed_stages(n):
            continue
        trans_decay = energy_system.net_techs.get_trans_decay(s, n)
        df_st_builder.add_row(
            ENTRY_TRANSDECAY,
            trans_decay,
            unit=(DimlessUnit() / energy_system.length_unit),
            stage=s.key,
            net_tech=n.key,
            source=SOURCE,
            in_res="input",
        )

    # cap_init
    for li in energy_system.net_links.ids_in_order:
        cap_init = energy_system.net_techs.get_cap_init(li, n)
        df_st_builder.add_row(
            ENTRY_CAPINIT,
            cap_init,
            unit=cap_unit,
            net_link=li.key,
            net_tech=n.key,
            source=SOURCE,
            in_res="input",
        )

    # age_init
    for li in energy_system.net_links.ids_in_order:
        age_init = energy_system.net_techs.get_age_init(li, n)
        df_st_builder.add_row(
            ENTRY_AGEINIT,
            age_init,
            unit=TimeUnit.A,
            net_link=li.key,
            net_tech=n.key,
            source=SOURCE,
            in_res="input",
        )

    # Any tech usage
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.net_techs.get_allowed_stages(n):
            continue
        for li in energy_system.net_links.ids_in_order:
            if li not in energy_system.net_techs.get_allowed_net_links(n):
                continue
            var = getattr(model, network_model.VAR_YNETTECHUSED)
            y_net_tech_used_fl = value(var[s.key, li.key, n.key], exception=False)
            if y_net_tech_used_fl is not None:
                y_net_tech_used = Value(y_net_tech_used_fl, DimlessUnit())
                df_st_builder.add_row(
                    ENTRY_YNETTECHUSED,
                    y_net_tech_used,
                    unit=DimlessUnit(),
                    stage=s.key,
                    net_link=li.key,
                    net_tech=n.key,
                    source=SOURCE,
                    in_res="result",
                )

    # Tech capacity
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.net_techs.get_allowed_stages(n):
            continue
        for li in energy_system.net_links.ids_in_order:
            if li not in energy_system.net_techs.get_allowed_net_links(n):
                continue
            var = getattr(model, network_model.VAR_NETTECHCAP)
            cap_fl = value(var[s.key, li.key, n.key], exception=False)
            if cap_fl is not None:
                cap = Value(cap_fl, cap_unit)
                df_st_builder.add_row(
                    ENTRY_NETTECHCAP,
                    cap,
                    unit=cap_unit,
                    stage=s.key,
                    net_link=li.key,
                    net_tech=n.key,
                    source=SOURCE,
                    in_res="result",
                )

    # Installed tech capacity
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.net_techs.get_allowed_stages(n):
            continue
        for li in energy_system.net_links.ids_in_order:
            if li not in energy_system.net_techs.get_allowed_net_links(n):
                continue
            var = getattr(model, network_model.VAR_NETTECHCAPINSTL)
            cap_instl_fl = value(var[s.key, li.key, n.key], exception=False)
            if cap_instl_fl is not None:
                cap_instl = Value(cap_instl_fl, unit=cap_unit)
                df_st_builder.add_row(
                    ENTRY_NETTECHCAPINSTL,
                    cap_instl,
                    unit=cap_unit,
                    stage=s.key,
                    net_link=li.key,
                    net_tech=n.key,
                    source=SOURCE,
                    in_res="result",
                )

    # Any tech installation
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.net_techs.get_allowed_stages(n):
            continue
        for li in energy_system.net_links.ids_in_order:
            if li not in energy_system.net_techs.get_allowed_net_links(n):
                continue
            var = getattr(model, network_model.VAR_YNETTECHCAPINSTL)
            y_cap_instl_fl = value(var[s.key, li.key, n.key], exception=False)
            if y_cap_instl_fl is not None:
                y_cap_instl = Value(y_cap_instl_fl, DimlessUnit())
                df_st_builder.add_row(
                    ENTRY_YNETTECHCAPINSTL,
                    y_cap_instl,
                    unit=DimlessUnit(),
                    stage=s.key,
                    net_link=li.key,
                    net_tech=n.key,
                    source=SOURCE,
                    in_res="result",
                )

    # CAPEX costs
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.net_techs.get_allowed_stages(n):
            continue
        for li in energy_system.net_links.ids_in_order:
            if li not in energy_system.net_techs.get_allowed_net_links(n):
                continue
            var = getattr(model, network_model.VAR_NETTECHCOSTCAPEX)
            capex_fl = value(var[s.key, li.key, n.key], exception=False)
            if capex_fl is not None:
                capex = Value(capex_fl, unit=energy_system.currency_unit)
                df_st_builder.add_row(
                    ENTRY_NETTECHCOSTCAPEX,
                    capex,
                    unit=energy_system.currency_unit,
                    stage=s.key,
                    net_link=li.key,
                    net_tech=n.key,
                    source=SOURCE,
                    in_res="result",
                )

    # OPEX costs from capacity
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.net_techs.get_allowed_stages(n):
            continue
        for li in energy_system.net_links.ids_in_order:
            if li not in energy_system.net_techs.get_allowed_net_links(n):
                continue
            var = getattr(model, network_model.VAR_NETTECHCOSTOPEXCAP)
            opex_cap_fl = value(var[s.key, li.key, n.key], exception=False)
            if opex_cap_fl is not None:
                opex_cap = Value(opex_cap_fl, unit=energy_system.currency_unit)
                df_st_builder.add_row(
                    ENTRY_NETTECHCOSTOPEXCAP,
                    opex_cap,
                    unit=energy_system.currency_unit,
                    stage=s.key,
                    net_link=li.key,
                    net_tech=n.key,
                    source=SOURCE,
                    in_res="result",
                )

    # OPEX costs from transmission
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.net_techs.get_allowed_stages(n):
            continue
        for li in energy_system.net_links.ids_in_order:
            if li not in energy_system.net_techs.get_allowed_net_links(n):
                continue
            var = getattr(model, network_model.VAR_NETTECHCOSTOPEXTRANS)
            opex_trans_fl = value(var[s.key, li.key, n.key], exception=False)
            if opex_trans_fl is not None:
                opex_trans = Value(opex_trans_fl, unit=energy_system.currency_unit)
                df_st_builder.add_row(
                    ENTRY_NETTECHCOSTOPEXTRANS,
                    opex_trans,
                    unit=energy_system.currency_unit,
                    stage=s.key,
                    net_link=li.key,
                    net_tech=n.key,
                    source=SOURCE,
                    in_res="result",
                )

    # CO2 from installation
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.net_techs.get_allowed_stages(n):
            continue
        for li in energy_system.net_links.ids_in_order:
            if li not in energy_system.net_techs.get_allowed_net_links(n):
                continue
            var = getattr(model, network_model.VAR_NETTECHCO2INSTL)
            co2_instl_fl = value(var[s.key, li.key, n.key], exception=False)
            if co2_instl_fl is not None:
                co2_instl = Value(co2_instl_fl, unit=energy_system.mass_unit)
                df_st_builder.add_row(
                    ENTRY_NETTECHCO2INSTL,
                    co2_instl,
                    unit=energy_system.mass_unit,
                    stage=s.key,
                    net_link=li.key,
                    net_tech=n.key,
                    source=SOURCE,
                    in_res="result",
                )

    # CO2 from transmission
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.net_techs.get_allowed_stages(n):
            continue
        for li in energy_system.net_links.ids_in_order:
            if li not in energy_system.net_techs.get_allowed_net_links(n):
                continue
            var = getattr(model, network_model.VAR_NETTECHCO2TRANS)
            co2_trans_fl = value(var[s.key, li.key, n.key], exception=False)
            if co2_trans_fl is not None:
                co2_trans = Value(co2_trans_fl, unit=energy_system.mass_unit)
                df_st_builder.add_row(
                    ENTRY_NETTECHCO2TRANS,
                    co2_trans,
                    unit=energy_system.mass_unit,
                    stage=s.key,
                    net_link=li.key,
                    net_tech=n.key,
                    source=SOURCE,
                    in_res="result",
                )

    # Total tech costs
    var = getattr(model, network_model.VAR_NETTECHCOSTTOTAL)
    cost_total_fl = value(var, exception=False)
    if cost_total_fl is not None:
        cost_total = Value(cost_total_fl, unit=energy_system.currency_unit)
        df_st_builder.add_row(
            ENTRY_NETTECHCOSTTOTAL,
            cost_total,
            unit=energy_system.currency_unit,
            source=SOURCE,
            in_res="result",
        )


def _format_file_granularity(
    df_st: pd.DataFrame,
    df_ts_hor: pd.DataFrame,
    df_ts_cl: Optional[pd.DataFrame],
    dir_path,
    file_granularity: FileGranularity,
) -> List[Tuple[pd.DataFrame, str]]:
    # Initialize dataframe list
    dfs: List[Tuple[pd.DataFrame, str]] = []

    # Format for minimal file granularity
    if file_granularity == FileGranularity.MIN:
        # Filenames
        filename_st = os.path.join(dir_path, f"{FILENAME_NETWORK}.csv")
        filename_ts_hor = os.path.join(dir_path, f"{FILENAME_NETWORK}-TS.csv")
        filename_ts_cl = os.path.join(dir_path, f"{FILENAME_NETWORK}-TSCL.csv")
        # Append dfs
        dfs.append((df_st, filename_st))
        dfs.append((df_ts_hor, filename_ts_hor))
        if df_ts_cl is not None:
            dfs.append((df_ts_cl, filename_ts_cl))

    # Format for default file granularity
    if file_granularity.value == FileGranularity.DEFAULT.value:
        # Static files
        ids_st = df_st[DfStColumn.NET_LINK.value].unique()
        for li in ids_st:
            filename_st = SOURCE
            if li:
                filename_st = f"{SOURCE}_{li}"
            filename_st = os.path.join(dir_path, f"{filename_st}.csv")
            df_st_cur = df_st[df_st[DfStColumn.NET_LINK.value] == li]
            if len(df_st_cur) > 0:
                dfs.append((df_st_cur, filename_st))

        # Horizon time files
        ids_ts_hor = df_ts_hor.columns.get_level_values(
            DfStColumn.NET_LINK.value
        ).unique()
        for li in ids_ts_hor:
            filename_ts_hor = f"{SOURCE}-TS"
            if li:
                filename_ts_hor = f"{SOURCE}_{li}-TS"
            filename_ts_hor = os.path.join(dir_path, f"{filename_ts_hor}.csv")
            df_ts_hor_cur = df_ts_hor.xs(
                li, axis=1, level=DfStColumn.NET_LINK.value, drop_level=False
            )
            if len(df_ts_hor_cur) > 0:
                dfs.append((df_ts_hor_cur, filename_ts_hor))

        # Clustered time files
        if df_ts_cl is not None:
            ids_ts_cl = df_ts_cl.columns.get_level_values(
                DfStColumn.NET_LINK.value
            ).unique()
            for li in ids_ts_cl:
                filename_ts_cl = f"{SOURCE}-TSCL"
                if li:
                    filename_ts_cl = f"{SOURCE}_{li}-TSCL"
                filename_ts_cl = os.path.join(dir_path, f"{filename_ts_cl}.csv")
                df_ts_cl_cur = df_ts_cl.xs(
                    li, axis=1, level=DfStColumn.NET_LINK.value, drop_level=False
                )
                if len(df_ts_cl_cur) > 0:
                    dfs.append((df_ts_cl_cur, filename_ts_cl))

    # Format for maximal file granularity
    if file_granularity.value == FileGranularity.MAX.value:
        # Static files
        ids_st = df_st[
            [DfStColumn.NET_LINK.value, DfStColumn.NET_TECH.value]
        ].drop_duplicates()
        for li, n in ids_st.itertuples(index=False, name=None):
            filename_st = SOURCE
            if li:
                filename_st = f"{SOURCE}_{li}"
                if n:
                    filename_st = f"{SOURCE}_{li}_{n}"
            filename_st = os.path.join(dir_path, f"{filename_st}.csv")
            df_st_cur = df_st[
                (df_st[DfStColumn.NET_LINK.value] == li)
                & (df_st[DfStColumn.NET_TECH.value] == n)
            ]
            if len(df_st_cur) > 0:
                dfs.append((df_st_cur, filename_st))

        # Horizon time files
        ids_ts_hor = df_ts_hor.columns.to_frame(index=False)[
            [DfStColumn.NET_LINK.value, DfStColumn.NET_TECH.value]
        ]
        for li, n in ids_ts_hor.itertuples(index=False, name=None):
            filename_ts_hor = f"{SOURCE}-TS"
            if li:
                filename_ts_hor = f"{SOURCE}_{li}-TS"
                if n:
                    filename_ts_hor = f"{SOURCE}_{li}_{n}-TS"
            filename_ts_hor = os.path.join(dir_path, f"{filename_ts_hor}.csv")
            df_ts_hor_cur = df_ts_hor.xs(
                (li, n),
                axis=1,
                level=(DfStColumn.NET_LINK.value, DfStColumn.NET_TECH.value),
                drop_level=False,
            )
            if len(df_ts_hor_cur) > 0:
                dfs.append((df_ts_hor_cur, filename_ts_hor))

        # Clustered time files
        if df_ts_cl is not None:
            ids_ts_cl = df_ts_hor.columns.to_frame(index=False)[
                [DfStColumn.NET_LINK.value, DfStColumn.NET_TECH.value]
            ]
            for li, n in ids_ts_cl:
                filename_ts_cl = f"{SOURCE}-TSCL"
                if li:
                    filename_ts_cl = f"{SOURCE}_{li}-TSCL"
                    if n:
                        filename_ts_cl = f"{SOURCE}_{li}_{n}-TSCL"
                filename_ts_cl = os.path.join(dir_path, f"{filename_ts_cl}.csv")
                df_ts_cl_cur = df_ts_cl.xs(
                    (li, n),
                    axis=1,
                    level=(DfStColumn.NET_LINK.value, DfStColumn.NET_TECH.value),
                    drop_level=False,
                )
                if len(df_ts_cl_cur) > 0:
                    dfs.append((df_ts_cl_cur, filename_ts_cl))

    # Return
    return dfs


def write_data_time_series(energy_system: EnergySystem, dir_path: str) -> None:
    """
    Writes all time series with actual data (def_value is not enough) in a
    NetworkLinks data object to a dedicated csv file in a directory

    :param energy_system: Energy system data object
    :type energy_system: EnergySystem
    :param dir_path: Path where the csv file will be placed
    :type dir_path: str
    """
    # Create directory if it does not exist
    if not os.path.isdir(dir_path):
        if not create_dir(dir_path):
            raise exceptions.EhubXException(
                "Could not write network link time series data because "
                "the directory could not be created",
                module=LOG_MODULE_STR,
            )

    # Gather time series
    data: Dict[Tuple[str, str, str, str, str], List[float]] = {}
    for kind, stage, ids, series in energy_system.net_links.time_series:
        # Skip series without values
        if not series.has_values:
            continue
        if kind == TimeSeriesKind.NETLINKAVAIL:
            unit = DimlessUnit()
            data[stage.key, ids[0], ids[1], YAMLKEY_AVAILABILITY, str(unit)] = [
                series.get_value(t).to_float(unit=unit)
                for t in energy_system.times.ids_in_order
            ]

    # Write demands file
    if data:
        df = pd.DataFrame(data)
        df.columns.names = [
            HeaderId.STAGEID.value,
            HeaderId.NETLINKID.value,
            HeaderId.ECID.value,
            HeaderId.PROFILEKEY.value,
            HeaderId.UNIT.value,
        ]
        df.index += 1
        df.to_csv(os.path.join(dir_path, FILENAME_TIMESERIES_NETLINKS))
