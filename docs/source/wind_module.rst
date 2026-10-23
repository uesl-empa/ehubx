.. _wind_module:

Wind module
===========

The wind module adds onshore wind turbines as a technology type. Wind speeds
are given per *wind group* (a geographic wind zone), adjusted to each turbine's
hub height, and converted into available output with an idealized power curve.
Wind groups can be split into *terrains* with their own roughness, siting rules
and cost multipliers, and the available land area can limit how many turbines
fit.

The equations are described in :ref:`wind_tech_model`, the input files in
:ref:`input_files`. A complete, realistic example is
``examples/wind_demo`` in the repository.

Setting up a wind model
-----------------------

1. **Define the turbine types** in :ref:`techs_yaml` with ``type: wind`` and
   ``wind_params`` (rated power, cut-in and cut-out speed, rotor diameter, hub
   height, power coefficient, area per turbine). Capacity is in kW of rated
   power, so costs such as ``capex_per_cap`` are per kW.
2. **Give the wind data** in the renewables folder:

   * ``wind_speed.csv``: the wind speed per stage, wind group and time step
   * ``wind_groups.csv``: the reference height of the wind data per wind group
   * ``wind_terrains.csv``: the surface roughness per terrain

   The parser only warns if one of them is missing. Without a reference height
   and a roughness, the wind speed is used as given (no adjustment to hub
   height) and, unless a turbulence intensity file is given, no turbulence is
   applied. So in practice, provide all three.

3. **Optionally add**:

   * ``wind_areas.csv``: the available land area per stage, hub and wind group
   * ``wind_terrain_areas.csv``: the share of each wind group per terrain
   * ``wind_terrain_multipliers.csv``: cost multipliers per wind group and terrain
   * ``wind_turbulence_intensity_profile.csv`` or
     ``wind_turbulence_intensity_fixed.csv``: turbulence intensity. Without
     them, it is derived from the hub height and the terrain roughness.

4. **Allow the turbines at a hub** through a tech list in :ref:`hubs_yaml`, and
   optionally set hub-level curtailment bounds in ``wind_params`` there.

How the available output is computed
------------------------------------

For each turbine type, wind group, terrain and time step:

* the wind speed is scaled from the reference height to the hub height with a
  logarithmic wind profile, using the terrain roughness
* the turbulence intensity is taken from the time-series file, else the fixed
  file, else derived as ``1 / ln(hub_height / roughness)``
* the expected power of one turbine is averaged over a normal distribution of
  wind speeds around the mean, using the idealized power curve
  ``min(rated_power, 0.5 * rho * A * Cp * v^3)`` between cut-in and cut-out
  speed
* dividing by the rated power gives the available capacity factor

Points to be aware of
---------------------

* ``rated_speed`` is mandatory in ``techs.yaml`` but currently not used.
* The air density is fixed at its sea-level value, which overestimates the
  output at high sites.
* A rougher terrain can come out with a *higher* output than a smoother one,
  because there is no displacement height for forest canopies.
* With ``wind_terrain_multipliers.csv``, one-time costs are charged once per
  terrain sub-group in which a turbine type is built.
* Capacity is continuous, so a result can correspond to a fractional number of
  turbines.

Source files
------------

* Data: ``src/ehubx/data/wind_data.py``, ``src/ehubx/data/wind_tech_data.py``
* Parser: ``src/ehubx/parser/wind_parser.py``
* Model: ``src/ehubx/model/wind_tech_model.py``
* Writer: ``src/ehubx/writer/wind_writer.py``
