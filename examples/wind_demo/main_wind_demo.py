import os

from ehubx import EhubX, Glpk, ObjectiveType, RomMethod, RomSettings


# Wind demo: should a Swiss municipality build wind turbines on a nearby Jura
# crest, and which ones?
#
# - One hub (Village) with the hourly electricity demand of a municipality of
#   about 5000 inhabitants (22.5 GWh/a). Grid electricity is bought at a
#   time-of-use tariff, and surplus wind power can be sold at a lower price.
# - One wind group (JuraCrest) with one year of hourly wind speed at 100 m
#   (Mont Crosin, ERA5 2023 via Open-Meteo, scaled to an annual mean of
#   5.5 m/s). The available area of 4 km^2 is split into pasture (60%) and
#   forest (40%); building in forest costs more.
# - Three turbine types: Enercon E-82 (2.3 MW, pasture only), Vestas V112
#   (3.45 MW) and Enercon E-138 (4.26 MW).
#
# The full year (8760 h) is reduced to about 50 representative hours with TSAM
# clustering, which solves in seconds and stays within a few percent of the
# full-year result. Input sources and assumptions: see README.md.

if __name__ == "__main__":
    ehubx = EhubX()
    ehubx.model_dir_path = os.path.abspath(os.path.dirname(__file__))
    ehubx.parse()
    # Reduce the year to representative hours (remove this line to solve the
    # full year, which takes a few minutes with GLPK)
    ehubx.rom(rom_settings=RomSettings(method=RomMethod.CLUSTER_TSAM, num_ts_target=50))
    ehubx.build()
    ehubx.set_solver(Glpk())
    ehubx.solve_single_obj(obj_type=ObjectiveType.COST)
