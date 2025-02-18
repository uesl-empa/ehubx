"""Conversion technology writer module. Writes out information from the
conversion technology submodule to files"""
import os
from typing import Dict, List, Optional, Tuple
import pandas as pd
from pyomo.core import Model, value
from ehubx.core.common import TimeSeriesKind
from ehubx.core import exceptions
from ehubx.data.energy_system_data import EnergySystem
from ehubx.data.tech_data import TechId
from ehubx.data.conv_tech_data import ConversionTechs
from ehubx.data.time_data import Times
from ehubx.data.time_series import TimeSeries
from ehubx.parser.conv_tech_parser import YAMLKEY_AVAILABILITY, YAMLKEY_OUTEFF
from ehubx.parser.csv_parser import HeaderId
from ehubx.model import conv_tech_model
from ehubx.writer.common_writer import create_dir, add_to_df_st, \
    add_to_df_ts_cl
from ehubx.writer import solar_writer
from ehubx.writer import wind_writer

# -------- #
# Literals #
# -------- #
LOG_MODULE_STR: str = "writ/conv_tech"
"""String identifying the conversion technology writer module for logging
purposes"""

FILENAME_TIMESERIES_CONVTECHS: str = "conv_techs.csv"
"""Filename for conversion technology time series"""

POSTFIX_CONV_TECH_CSV: str = "conv"
"""Postfix for every conversion technology csv output file"""

SOURCE: str = "conv_tech"
"""Display name for the conversion tech module in result files"""

ENTRY_INECMAIN: str = "Main input ec"
"""Entry name for conversion input parameter 'in_ec_main' in result files"""

ENTRY_INPART: str = "Part of input composition (in_part)"
"""Entry name for conversion input parameter 'in_part' in result files"""

ENTRY_OUTECMAIN: str = "Main output ec"
"""Entry name for conversion input parameter 'out_ec_main' in result files"""

ENTRY_OUTEFF: str = "Output efficiency (out_eff)"
"""Entry name for conversion input parameter 'out_eff' in result files"""

ENTRY_OUTSUMMIN: str = "Minimal summed-up output (out_sum_min)"
"""Entry name for conversion input parameter 'out_sum_min' in result files"""

ENTRY_OUTSUMMAX: str = "Maximal summed-up output (out_sum_max)"
"""Entry name for conversion input parameter 'out_sum_max' in result files"""

ENTRY_AVAILABILITY: str = "Availability"
"""Entry name for conversion input parameter 'availability' in result files"""

ENTRY_OPEXPERENERGY: str = "OPEX cost per output energy (opex_per_energy)"
"""Entry name for conversion input parameter 'opex_per_energy' in result
files"""

ENTRY_CONVTECHIN: str = ("Conversion tech input "
                         f"({conv_tech_model.VAR_CONVTECHIN})")
"""Entry name for conversion input variable in result files"""

ENTRY_CONVTECHOUT: str = ("Conversion tech output "
                          f"({conv_tech_model.VAR_CONVTECHOUT})")
"""Entry name for conversion output variable in result files"""

ENTRY_CONVTECHCOSTOPEXOUT: str = \
    ("Conversion tech OPEX cost for output "
    f"({conv_tech_model.VAR_CONVTECHCOSTOPEXOUT})")
"""Entry name for output-related OPEX cost variable of conversion technologies
in result files """

ENTRY_CONVTECHCOSTOPEXTOTAL: str = (
    "Total conversion tech costs "
    f"({conv_tech_model.VAR_CONVTECHCOSTTOTAL})")
"""Entry name for total conversion-related costs in result files """


def format_all(energy_system: EnergySystem, model: Model, df_st: pd.DataFrame,
               df_ts_hor: pd.DataFrame, df_ts_cl: Optional[pd.DataFrame]
               ) -> None:
    # Total conversion-related costs
    var = getattr(model, conv_tech_model.VAR_CONVTECHCOSTTOTAL)
    conv_tech_cost_total = value(var, exception=False)
    if conv_tech_cost_total:
        add_to_df_st(df_st, ENTRY_CONVTECHCOSTOPEXTOTAL, conv_tech_cost_total,
                     unit="CHF", source=SOURCE, in_res="result")

    # Tech-specific properties
    for x in energy_system.conv_techs.ids_in_order:
        _format_tech(energy_system, model, x, df_st, df_ts_hor, df_ts_cl)

    # Child modules of this module
    solar_writer.format_all(energy_system, model, df_st, df_ts_hor, df_ts_cl)
    wind_writer.format_all(energy_system, model, df_st, df_ts_hor, df_ts_cl)


def _format_tech(energy_system: EnergySystem, model: Model, x: TechId,
                 df_st: pd.DataFrame, df_ts_hor: pd.DataFrame,
                 df_ts_cl: Optional[pd.DataFrame]) -> None:
    # in_ec_main
    in_ec_main = energy_system.conv_techs.get_in_ec_main(x)
    add_to_df_st(df_st, ENTRY_INECMAIN, in_ec_main.key, tech=x.key,
                 source=SOURCE, in_res="input")

    # in_part
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for e in energy_system.ecs.ids_in_order:
            if e not in energy_system.conv_techs.get_in_ecs(x):
                continue
            in_part = energy_system.conv_techs.get_in_part(s, x, e)
            add_to_df_st(df_st, ENTRY_INPART, in_part, stage=s.key, ec=e.key,
                         tech=x.key, source=SOURCE, in_res="input")

    # out_ec_main
    out_ec_main = energy_system.conv_techs.get_out_ec_main(x)
    add_to_df_st(df_st, ENTRY_OUTECMAIN, out_ec_main.key, tech=x.key,
                 source=SOURCE, in_res="input")

    # out_eff
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for e in energy_system.ecs.ids_in_order:
            if e not in energy_system.conv_techs.get_out_ecs(x):
                continue
            out_eff = energy_system.conv_techs.get_out_eff(s, x, e)
            if out_eff.has_values:
                add_to_df_ts_cl(df_ts_hor, df_ts_cl,
                    energy_system.times, ENTRY_OUTEFF, out_eff, unit="1",
                    stage=s.key, ec=e.key, tech=x.key, source=SOURCE,
                    in_res="input")
            if not out_eff.has_values:
                out_eff_def = out_eff.def_value
                assert out_eff_def is not None
                add_to_df_st(df_st, ENTRY_OUTEFF, out_eff_def, unit="1",
                             stage=s.key, ec=e.key, tech=x.key, source=SOURCE,
                             in_res="input")

    # out_sum_min
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            out_sum_min = energy_system.conv_techs.get_out_sum_min(s, h, x)

            add_to_df_st(df_st, ENTRY_OUTSUMMIN, out_sum_min, unit="kWh",
                         stage=s.key, hub=h.key, tech=x.key, source=SOURCE,
                         in_res="input")

    # out_sum_max
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            out_sum_max = energy_system.conv_techs.get_out_sum_max(s, h, x)
            add_to_df_st(df_st, ENTRY_OUTSUMMAX, out_sum_max, unit="kWh",
                         stage=s.key, hub=h.key, tech=x.key,
                         source=SOURCE, in_res="input")

    # availability
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            availability = energy_system.conv_techs.get_availability(
                s, h, x)
            if availability.has_values:
                add_to_df_ts_cl(df_ts_hor, df_ts_cl,
                    energy_system.times, ENTRY_AVAILABILITY, availability,
                    unit="1", stage=s.key, hub=h.key, tech=x.key,
                    source=SOURCE, in_res="input")
            if not availability.has_values:
                availability_def = availability.def_value
                assert availability_def is not None
                add_to_df_st(df_st, ENTRY_AVAILABILITY, availability_def,
                             unit="1", stage=s.key, hub=h.key, tech=x.key,
                             source=SOURCE, in_res="input")

    # opex_per_energy
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        opex_per_energy = energy_system.conv_techs.get_opex_per_energy(s, x)
        add_to_df_st(df_st, ENTRY_OPEXPERENERGY, opex_per_energy,
                     unit="CHF/kWh", stage=s.key, tech=x.key,
                     source=SOURCE, in_res="input")

    # Conversion input
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            for e in energy_system.ecs.ids_in_order:
                if e not in energy_system.conv_techs.get_in_ecs(x):
                    continue
                var = getattr(model, conv_tech_model.VAR_CONVTECHIN)
                conv_tech_in = TimeSeries()
                for t in energy_system.times.ids:
                    conv_tech_in.set_value(t, value(var[s.key, h.key, x.key,
                                                        e.key, t.key_as_int]))
                add_to_df_ts_cl(df_ts_hor, df_ts_cl,
                    energy_system.times, ENTRY_CONVTECHIN,
                    conv_tech_in, unit="kW", stage=s.key, hub=h.key,
                    tech=x.key, ec=e.key, source=SOURCE, in_res="result")

    # Conversion output
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            for e in energy_system.ecs.ids_in_order:
                if e not in energy_system.conv_techs.get_out_ecs(x):
                    continue
                var = getattr(model, conv_tech_model.VAR_CONVTECHOUT)
                conv_tech_out = TimeSeries()
                for t in energy_system.times.ids:
                    conv_tech_out.set_value(t, value(var[s.key, h.key, x.key,
                                                        e.key, t.key_as_int],
                                                     exception=False))
                add_to_df_ts_cl(df_ts_hor, df_ts_cl,
                    energy_system.times, ENTRY_CONVTECHOUT,
                    conv_tech_out, unit="kW", stage=s.key, hub=h.key,
                    tech=x.key, ec=e.key, source=SOURCE, in_res="result")

    # OPEX costs for conversion output
    for s in energy_system.stages.ids_in_order:
        if s not in energy_system.techs.get_allowed_stages(x):
            continue
        for h in energy_system.hubs.ids_in_order:
            if h not in energy_system.techs.get_allowed_hubs(x):
                continue
            var = getattr(model, conv_tech_model.VAR_CONVTECHCOSTOPEXOUT)
            conv_tech_cost_opex_out = value(var[s.key, h.key, x.key],
                                            exception=False)
            if conv_tech_cost_opex_out:
                add_to_df_st(df_st, ENTRY_CONVTECHCOSTOPEXOUT,
                             conv_tech_cost_opex_out, unit="CHF", stage=s.key,
                             hub=h.key, tech=x.key, source=SOURCE,
                             in_res="result")


def write_data_time_series(conv_techs: ConversionTechs, times: Times,
                           dir_path: str) -> None:
    """
    Writes all time series with actual data (def_value is not enough) in a
    conversion technology data object to a dedicated csv file in a directory

    :param conv_techs: The conversion technology data object whose time series
        are to be written
    :type conv_techs: ConversionTechs
    :param times: Times data object
    :type times: Times
    :param dir_path: Path where the csv file will be placed
    :type dir_path: str
    """
    # Create directory if it does not exist
    if not os.path.isdir(dir_path):
        if not create_dir(dir_path):
            raise exceptions.EhubXException(
                "Could not write conversion tech time series data because "
                "the directory could not be created", module=LOG_MODULE_STR)

    # Gather time series from input data
    data: Dict[Tuple[str, str, str, str, str], List[float]] = {}
    for (kind, stage, ids, series) in conv_techs.time_series:
        # Skip series without values
        if not series.has_values:
            continue
        if kind == TimeSeriesKind.CONVTECHOUTEFF:
            data[stage.key, "", ids[1], ids[0], YAMLKEY_OUTEFF] = [
                series.get_value(t) for t in times.ids_in_order]
        if kind == TimeSeriesKind.CONVTECHAVAIL:
            data[stage.key, ids[0], "", ids[1], YAMLKEY_AVAILABILITY] = [
                series.get_value(t) for t in times.ids_in_order]

    # Write file
    if data:
        df = pd.DataFrame(data)
        df.columns.names = [HeaderId.STAGEID.value, HeaderId.HUBID.value,
                            HeaderId.ECID.value, HeaderId.TECHID.value,
                            HeaderId.PROFILEKEY.value]
        df.index += 1
        df.to_csv(os.path.join(dir_path, FILENAME_TIMESERIES_CONVTECHS))
