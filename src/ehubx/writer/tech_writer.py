import os
from typing import List, Optional, Tuple

import pandas as pd
from pyomo.core import Model, value

from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.tech_data import TechId
from ehubx.model import tech_model
from ehubx.writer import (
    ates_writer,
    conv_tech_writer,
    ebm_tech_writer,
    hp_tech_writer,
    stor_tech_writer,
)
from ehubx.writer.common_writer import (
    COL_LOADSHIFT,
    COL_NETLINK,
    COL_NETLINKDIR,
    COL_NETTECH,
    COL_SOURCE,
    COL_TECH,
    FileGranularity,
    add_to_df_st,
    init_df_st,
    init_df_ts_cl,
    init_df_ts_hor,
)


# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "writ/tech"
"""String identifying the technology writer module for logging purposes"""

PREFIX_TECH_CSV: str = "tech"
"""Prefix for every technology csv output file"""

SOURCE: str = "tech"
"""Display name for the tech module in result files"""

ENTRY_ALLOWEDINSTAGE: str = "Allowed in stage?"
"""Entry name monitoring whether a tech is allowed in a stage, in result
files"""

ENTRY_ALLOWEDINHUB: str = "Allowed in hub?"
"""Entry name monitoring whether a tech is allowed in a hub, in result files"""

ENTRY_LIFETIME: str = "Lifetime"
"""Entry name for tech parameter 'lifetime' in result files"""

ENTRY_INTERESTRATE: str = "Interest rate"
"""Entry name for tech parameter 'interest_rate' in result files"""

ENTRY_UNITCAPMIN: str = "Minimal amount of installable capacity (unit_cap_min)"
"""Entry name for tech parameter 'unit_cap_min' in result files"""

ENTRY_ONETIMECAPEX: str = "Fixed CAPEX installation price (one_time_capex)"
"""Entry name for tech parameter 'one_time_capex' in result files"""

ENTRY_CAPEXPERCAP: str = "CAPEX price per installed capacity (capex_per_cap)"
"""Entry name for tech parameter 'capex_per_cap' in result files"""

ENTRY_ONETIMEOPEX: str = "Fixed OPEX price (one_time_opex)"
"""Entry name for tech parameter 'one_time_opex' in result files"""

ENTRY_OPEXPERCAP: str = "OPEX price per capacity (opex_per_cap)"
"""Entry name for tech parameter 'opex_per_cap' in result files"""

ENTRY_CO2PERCAP: str = "Embodied CO2 per installed capacity (co2_per_cap)"
"""Entry name for tech parameter 'co2_per_cap' in result files"""

ENTRY_LASTINSTLYEAR: str = "Last possible installation year (last_instl_year)"
"""Entry name for parameter 'last_instl_year' in result files"""

ENTRY_CAPINIT: str = "Initially installed capacity (cap_init)"
"""Entry name for parameter 'cap_init' in result files"""

ENTRY_AGEINIT: str = "Age of initially installed capacity (age_init)"
"""Entry name for parameter 'age_init' in result files"""

ENTRY_CAPMIN: str = "Minimal allowed capacity (cap_min)"
"""Entry name for parameter 'cap_min' in result files"""

ENTRY_CAPMAX: str = "Maximal allowed capacity (cap_max)"
"""Entry name for parameter 'cap_max' in result files"""

ENTRY_COUPLEDMAINTECH: str = "Id of coupled main tech (coupled_main_tech)"
"""Entry name for parameter 'coupled_main_tech' in result files"""

ENTRY_COUPLEDCAPFACTOR: str = "Capacity coupling factor (coupled_cap_factor)"
"""Entry name for parameter 'coupled_cap_factor' in result files"""

ENTRY_TECHCAP: str = f"Tech capacity ({tech_model.VAR_TECHCAP})"
"""Entry name for tech capacity variable in result files"""

ENTRY_TECHCAPINSTL: str = f"Tech capacity installation ({tech_model.VAR_TECHCAPINSTL})"
"""Entry name for tech capacity installation variable in result files"""

ENTRY_YTECHCAPINSTL: str = (
    f"Any capacity installation? ({tech_model.VAR_YTECHCAPINSTL})"
)
"""Entry name for binary variable monitoring tech installation in result
files"""

ENTRY_YTECHUSED: str = f"Any tech usage? ({tech_model.VAR_YTECHUSED})"
"""Entry name for tech usage variable in result files"""

ENTRY_TECHCOSTCAPEX: str = f"CAPEX installation costs ({tech_model.VAR_TECHCOSTCAPEX})"
"""Entry name for tech CAPEX cost variable in result files"""

ENTRY_TECHCOSTOPEXCAP: str = f"OPEX capacity costs ({tech_model.VAR_TECHCOSTOPEXCAP})"
"""Entry name for tech OPEX cost variable per capacity in result files"""

ENTRY_TECHCOSTTOTAL: str = f"Total tech costs ({tech_model.VAR_TECHCOSTTOTAL})"
"""Entry name for total tech cost variable in result files"""

ENTRY_TECHCO2INSTL: str = (
    f"Embodied CO2 from tech installation ({tech_model.VAR_TECHCO2INSTL})"
)
"""Entry name for embodied CO2 variable for tech installation in result
files"""

ENTRY_TECHCO2TOTAL: str = (
    f"Total embodied CO2 from techs ({tech_model.VAR_TECHCO2TOTAL})"
)
"""Entry name for total embodied CO2 variable for techs in result files"""


def format_all(
    energy_system: EnergySystem,
    model: Model,
    dir_path: str,
    file_granularity: FileGranularity = FileGranularity.DEFAULT,
) -> List[Tuple[pd.DataFrame, str]]:
    # Initialize dataframes
    df_st = init_df_st()
    df_ts_hor = init_df_ts_hor(energy_system.times)
    df_ts_cl: Optional[pd.DataFrame] = None
    if energy_system.times.is_clustered:
        df_ts_cl = init_df_ts_cl(energy_system.times)

    # Total CO2
    for s in energy_system.stages.ids_in_order:
        var = getattr(model, tech_model.VAR_TECHCO2TOTAL)
        co2_total = value(var[s.key], exception=False)
        if co2_total:
            add_to_df_st(
                df_st,
                ENTRY_TECHCO2TOTAL,
                co2_total,
                unit="kg",
                stage=s.key,
                source=SOURCE,
                in_res="result",
            )

    # Tech-specific values
    for x in energy_system.techs.ids_in_order:
        _format_tech(energy_system, model, x, df_st)

    # Child modules of this module
    conv_tech_writer.format_all(energy_system, model, df_st, df_ts_hor, df_ts_cl)
    stor_tech_writer.format_all(energy_system, model, df_st, df_ts_hor, df_ts_cl)
    hp_tech_writer.format_all(energy_system, model, df_st, df_ts_hor, df_ts_cl)
    ates_writer.format_all(energy_system, model, df_st, df_ts_hor)
    ebm_tech_writer.format_all(energy_system, model, df_st, df_ts_hor, df_ts_cl)

    # Remove ununsed columns
    cols_to_drop_st = [COL_NETLINK, COL_NETLINKDIR, COL_NETTECH, COL_LOADSHIFT]
    cols_to_drop_ts = [COL_NETLINK, COL_NETTECH, COL_LOADSHIFT]
    df_st.drop(columns=(cols_to_drop_st), inplace=True)
    df_ts_hor.columns = df_ts_hor.columns.droplevel(cols_to_drop_ts)
    if df_ts_cl is not None:
        df_ts_cl.columns = df_ts_cl.columns.droplevel(cols_to_drop_ts)

    # Format for minimal file granularity
    dfs = _format_file_granularity(
        df_st, df_ts_hor, df_ts_cl, dir_path, file_granularity
    )

    # Return
    return dfs


def _format_tech(
    energy_system: EnergySystem, model: Model, x: TechId, df_st: pd.DataFrame
) -> None:
    # Get the capacity unit
    cap_unit: str = "CAP"
    if x in energy_system.conv_techs.ids or x in energy_system.hp_techs.ids:
        cap_unit = "kW"
    if (
        x in energy_system.solar_techs.ids
        or x in energy_system.wind_techs.ids
        or x in energy_system.ates_techs.ids
    ):
        cap_unit = "m^2"
    if x in energy_system.stor_techs.ids or x in energy_system.ebm_techs.ids:
        cap_unit = "kWh"

    # Allowed stages
    for s in energy_system.stages.ids_in_order:
        allowed_in_stage = s in energy_system.techs.get_allowed_stages(x)
        add_to_df_st(
            df_st,
            ENTRY_ALLOWEDINSTAGE,
            allowed_in_stage,
            stage=s.key,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # Allowed hubs
    for h in energy_system.hubs.ids_in_order:
        allowed_in_hub = h in energy_system.techs.get_allowed_hubs(x)
        add_to_df_st(
            df_st,
            ENTRY_ALLOWEDINHUB,
            allowed_in_hub,
            hub=h.key,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # Lifetime
    lifetime = energy_system.techs.get_lifetime(x)
    add_to_df_st(
        df_st,
        ENTRY_LIFETIME,
        lifetime,
        unit="a",
        tech=x.key,
        source=SOURCE,
        in_res="input",
    )

    # Interest rate
    interest_rate = energy_system.techs.get_interest_rate(x)
    add_to_df_st(
        df_st,
        ENTRY_INTERESTRATE,
        interest_rate,
        tech=x.key,
        source=SOURCE,
        in_res="input",
    )

    # unit_cap_min
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        unit_cap_min = energy_system.techs.get_unit_cap_min(s, x)
        add_to_df_st(
            df_st,
            ENTRY_UNITCAPMIN,
            unit_cap_min,
            unit=cap_unit,
            stage=s.key,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # one_time_capex
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        one_time_capex = energy_system.techs.get_one_time_capex(s, x)
        add_to_df_st(
            df_st,
            ENTRY_ONETIMECAPEX,
            one_time_capex,
            unit="CHF",
            stage=s.key,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # capex_per_cap
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        capex_per_cap = energy_system.techs.get_capex_per_cap(s, x)
        add_to_df_st(
            df_st,
            ENTRY_CAPEXPERCAP,
            capex_per_cap,
            unit=f"CHF/{cap_unit}",
            stage=s.key,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # one_time_opex
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        one_time_opex = energy_system.techs.get_one_time_opex(s, x)
        add_to_df_st(
            df_st,
            ENTRY_ONETIMEOPEX,
            one_time_opex,
            unit="CHF",
            stage=s.key,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # opex_per_cap
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        opex_per_cap = energy_system.techs.get_opex_per_cap(s, x)
        add_to_df_st(
            df_st,
            ENTRY_OPEXPERCAP,
            opex_per_cap,
            unit=f"CHF/{cap_unit}",
            stage=s.key,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # co2_per_cap
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        co2_per_cap = energy_system.techs.get_co2_per_cap(s, x)
        add_to_df_st(
            df_st,
            ENTRY_CO2PERCAP,
            co2_per_cap,
            unit=f"CHF/{cap_unit}",
            stage=s.key,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # last_instl_year
    for h in energy_system.hubs.ids_in_order:
        if h not in energy_system.techs.get_allowed_hubs(x):
            continue
        last_instl_year = energy_system.techs.get_last_instl_year(h, x)
        add_to_df_st(
            df_st,
            ENTRY_LASTINSTLYEAR,
            last_instl_year,
            hub=h.key,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # cap_init
    for h in energy_system.hubs.ids_in_order:
        if h not in energy_system.techs.get_allowed_hubs(x):
            continue
        cap_init = energy_system.techs.get_cap_init(h, x)
        add_to_df_st(
            df_st,
            ENTRY_CAPINIT,
            cap_init,
            unit=cap_unit,
            hub=h.key,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # age_init
    for h in energy_system.hubs.ids_in_order:
        if h not in energy_system.techs.get_allowed_hubs(x):
            continue
        age_init = energy_system.techs.get_age_init(h, x)
        add_to_df_st(
            df_st,
            ENTRY_AGEINIT,
            age_init,
            unit="a",
            hub=h.key,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # cap_min
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            cap_min = energy_system.techs.get_cap_min(s, h, x)
            add_to_df_st(
                df_st,
                ENTRY_CAPMIN,
                cap_min,
                unit=cap_unit,
                stage=s.key,
                hub=h.key,
                tech=x.key,
                source=SOURCE,
                in_res="input",
            )

    # cap_max
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            cap_max = energy_system.techs.get_cap_max(s, h, x)
            add_to_df_st(
                df_st,
                ENTRY_CAPMAX,
                cap_max,
                unit=cap_unit,
                stage=s.key,
                hub=h.key,
                tech=x.key,
                source=SOURCE,
                in_res="input",
            )

    # coupled_main_tech
    if x in energy_system.techs.coupled_sub_techs:
        coupled_main_tech = energy_system.techs.get_coupled_main_tech(x)
        add_to_df_st(
            df_st,
            ENTRY_COUPLEDMAINTECH,
            coupled_main_tech.key,
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # coupled_cap_factor
    if x in energy_system.techs.coupled_sub_techs:
        coupled_cap_factor = energy_system.techs.get_coupled_cap_factor(x)
        add_to_df_st(
            df_st,
            ENTRY_COUPLEDCAPFACTOR,
            coupled_cap_factor,
            unit="1",
            tech=x.key,
            source=SOURCE,
            in_res="input",
        )

    # Tech capacity
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, tech_model.VAR_TECHCAP)
            cap = value(var[s.key, h.key, x.key], exception=False)
            if cap is not None:
                add_to_df_st(
                    df_st,
                    ENTRY_TECHCAP,
                    cap,
                    unit=cap_unit,
                    stage=s.key,
                    hub=h.key,
                    tech=x.key,
                    source=SOURCE,
                    in_res="result",
                )

    # Installed tech capacity
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, tech_model.VAR_TECHCAPINSTL)
            cap_instl = value(var[s.key, h.key, x.key], exception=False)
            if cap_instl is not None:
                add_to_df_st(
                    df_st,
                    ENTRY_TECHCAPINSTL,
                    cap_instl,
                    unit=cap_unit,
                    stage=s.key,
                    hub=h.key,
                    tech=x.key,
                    source=SOURCE,
                    in_res="result",
                )

    # Any tech installation
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, tech_model.VAR_YTECHCAPINSTL)
            y_cap_instl = value(var[s.key, h.key, x.key], exception=False)
            if y_cap_instl is not None:
                add_to_df_st(
                    df_st,
                    ENTRY_YTECHCAPINSTL,
                    y_cap_instl,
                    stage=s.key,
                    hub=h.key,
                    tech=x.key,
                    source=SOURCE,
                    in_res="result",
                )

    # Any tech usage
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, tech_model.VAR_YTECHUSED)
            y_tech_used = value(var[s.key, h.key, x.key], exception=False)
            if y_tech_used is not None:
                add_to_df_st(
                    df_st,
                    ENTRY_YTECHUSED,
                    y_tech_used,
                    stage=s.key,
                    hub=h.key,
                    tech=x.key,
                    source=SOURCE,
                    in_res="result",
                )

    # Tech CAPEX costs
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, tech_model.VAR_TECHCOSTCAPEX)
            cost_capex = value(var[s.key, h.key, x.key], exception=False)
            if cost_capex is not None:
                add_to_df_st(
                    df_st,
                    ENTRY_TECHCOSTCAPEX,
                    cost_capex,
                    unit="CHF",
                    stage=s.key,
                    hub=h.key,
                    tech=x.key,
                    source=SOURCE,
                    in_res="result",
                )

    # Tech OPEX costs from capacity
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, tech_model.VAR_TECHCOSTOPEXCAP)
            cost_opex_cap = value(var[s.key, h.key, x.key], exception=False)
            if cost_opex_cap is not None:
                add_to_df_st(
                    df_st,
                    ENTRY_TECHCOSTOPEXCAP,
                    cost_opex_cap,
                    unit="CHF",
                    stage=s.key,
                    hub=h.key,
                    tech=x.key,
                    source=SOURCE,
                    in_res="result",
                )

    # Total tech costs
    var = getattr(model, tech_model.VAR_TECHCOSTTOTAL)
    cost_total = value(var, exception=False)
    add_to_df_st(
        df_st,
        ENTRY_TECHCOSTTOTAL,
        cost_total,
        unit="CHF",
        tech=x.key,
        source=SOURCE,
        in_res="result",
    )

    # CO2 from installation
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, tech_model.VAR_TECHCO2INSTL)
            co2_instl = value(var[s.key, h.key, x.key], exception=False)
            if co2_instl is not None:
                add_to_df_st(
                    df_st,
                    ENTRY_TECHCO2INSTL,
                    co2_instl,
                    unit="kg",
                    stage=s.key,
                    hub=h.key,
                    tech=x.key,
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

    # Format for minimal file granularity (One csv file "tech" for
    # static, horizon time and clustered time df each)
    if file_granularity == FileGranularity.MIN:
        # Filenames
        filename_st = os.path.join(dir_path, f"{PREFIX_TECH_CSV}.csv")
        filename_ts_hor = os.path.join(dir_path, f"{PREFIX_TECH_CSV}-TS.csv")
        filename_ts_cl = os.path.join(dir_path, f"{PREFIX_TECH_CSV}-TSCL.csv")
        # Append dfs
        dfs.append((df_st, filename_st))
        dfs.append((df_ts_hor, filename_ts_hor))
        if df_ts_cl is not None:
            dfs.append((df_ts_cl, filename_ts_cl))

    # Format for default file granularity (split by techs but keep tech
    # submodules like conv_tech together)
    if file_granularity == FileGranularity.DEFAULT:
        # Static files
        ids_st = df_st[COL_TECH].unique()
        for x in ids_st:
            filename_st = SOURCE
            if x:
                filename_st = f"{SOURCE}_{x}"
            filename_st = os.path.join(dir_path, f"{filename_st}.csv")
            df_st_cur = df_st[df_st[COL_TECH] == x]
            if len(df_st_cur) > 0:
                dfs.append((df_st_cur, filename_st))

        # Horizon time files
        ids_ts_hor = df_ts_hor.columns.get_level_values(COL_TECH).unique()
        for x in ids_ts_hor:
            filename_ts_hor = f"{SOURCE}-TS"
            if x:
                filename_ts_hor = f"{SOURCE}_{x}-TS"
            filename_ts_hor = os.path.join(dir_path, f"{filename_ts_hor}.csv")
            df_ts_hor_cur = df_ts_hor.xs(x, axis=1, level=COL_TECH, drop_level=False)
            if len(df_ts_hor_cur) > 0:
                dfs.append((df_ts_hor_cur, filename_ts_hor))

        # Clustered time files
        if df_ts_cl is not None:
            ids_ts_cl = df_ts_cl.columns.get_level_values(COL_TECH).unique()
            for x in ids_ts_cl:
                filename_ts_cl = f"{SOURCE}-TSCL"
                if x:
                    filename_ts_cl = f"{SOURCE}_{x}-TSCL"
                filename_ts_cl = os.path.join(dir_path, f"{filename_ts_cl}.csv")
                df_ts_cl_cur = df_ts_cl.xs(x, axis=1, level=COL_TECH, drop_level=False)
                if len(df_ts_cl_cur) > 0:
                    dfs.append((df_ts_cl_cur, filename_ts_cl))

    # Format for maximal file granularity (split by techs and tech submodules
    # like conv_tech)
    if file_granularity == FileGranularity.MAX:
        # Static files
        ids_st = df_st[[COL_TECH, COL_SOURCE]].drop_duplicates()
        for x, source in ids_st.itertuples(index=False, name=None):
            filename_st = source
            if x:
                filename_st = f"{SOURCE}_{x}"
                if source != SOURCE:
                    filename_st += f"_{source}"
            filename_st = os.path.join(dir_path, f"{filename_st}.csv")
            df_st_cur = df_st[(df_st[COL_TECH] == x) & (df_st[COL_SOURCE] == source)]
            if len(df_st_cur) > 0:
                dfs.append((df_st_cur, filename_st))

        # Horizon time files
        ids_ts_hor = df_ts_hor.columns.to_frame(index=False)[[COL_TECH, COL_SOURCE]]
        for x, source in ids_ts_hor.itertuples(index=False, name=None):
            filename_ts_hor = f"{source}TS"
            if x:
                if source == SOURCE:
                    filename_ts_hor = f"{SOURCE}_{x}-TS"
                if source != SOURCE:
                    filename_ts_hor = f"{SOURCE}_{x}_{source}-TS"
            filename_ts_hor = os.path.join(dir_path, f"{filename_ts_hor}.csv")
            df_ts_hor_cur = df_ts_hor.xs(
                (x, source), axis=1, level=(COL_TECH, COL_SOURCE), drop_level=False
            )
            if len(df_ts_hor_cur) > 0:
                dfs.append((df_ts_hor_cur, filename_ts_hor))

        # Clustered time files
        if df_ts_cl:
            ids_ts_cl = df_ts_cl.columns.to_frame(index=False)[[COL_TECH, COL_SOURCE]]
            for x, source in ids_ts_cl.itertuples(index=False, name=None):
                filename_ts_cl = f"{source}-TSCL"
                if x:
                    if source == SOURCE:
                        filename_ts_cl = f"{SOURCE}_{x}-TSCL"
                    if source != SOURCE:
                        filename_ts_hor = f"{SOURCE}_{x}_{source}-TSCL"
                filename_ts_cl = os.path.join(dir_path, f"{filename_ts_cl}.csv")
                df_ts_cl_cur = df_ts_cl.xs(
                    (x, source), axis=1, level=(COL_TECH, COL_SOURCE), drop_level=False
                )
                if len(df_ts_hor_cur) > 0:
                    dfs.append((df_ts_cl_cur, filename_ts_cl))

    # Return
    return dfs
