.. _wind_module:

Wind model
==========

This page documents the wind-specific wind data and wind-technology model in
ehubX, including input data, core data structures, and optimization behavior.

Overview
--------

The wind implementation is split into two connected parts:

* Data and parsing layer:
  * Wind-speed profiles and their wind-group reference heights
  * Optional fixed and time-varying turbulence intensity inputs
  * Terrain roughness and optional terrain-area shares
  * Optional wind area and terrain-specific cost constraints
* Optimization layer:
  * Wind technology parameters (rated power, cut-in/out speed, rotor diameter,
    hub height, etc.)
  * Available output-factor calculation from adjusted wind speed and selected
    turbulence intensity
  * Wind-group/terrain capacity allocation, output, curtailment, and area
    constraints

Main source files
-----------------

* Data:
  * ``src/ehubx/data/wind_data.py``
  * ``src/ehubx/data/wind_tech_data.py``
* Parser:
  * ``src/ehubx/parser/wind_parser.py``
* Model:
  * ``src/ehubx/model/wind_tech_model.py``
* Writer:
  * ``src/ehubx/writer/wind_writer.py``

Input files
-----------

The wind model reads files from the renewables input folder:

* ``wind_groups.csv``
* ``wind_terrains.csv``
* ``wind_speed.csv``
* ``wind_turbulence_intensity_fixed.csv`` (optional)
* ``wind_turbulence_intensity_profile.csv`` (optional)
* ``wind_areas.csv`` (optional)
* ``wind_terrain_areas.csv`` (optional)
* ``wind_terrain_multipliers.csv`` (optional)

For details and examples of input structure, see :ref:`input_files`.

Wind data model
---------------

Wind speed is stored as a time series by tuple:

* ``(stage, wind_group) -> TimeSeries``

Additional metadata and optional TI inputs:

* ``wind_group -> height``
* ``(stage, wind_group) -> fixed turbulence intensity``
* ``(stage, wind_group) -> turbulence intensity TimeSeries``
* ``terrain -> roughness``
* ``(wind_group, terrain) -> area fraction``

Speed profile behavior
----------------------

For each wind-group/terrain subgroup, the wind-group speed profile is adjusted
from its reference height to the technology hub height using the terrain
roughness. Turbulence intensity is selected with the following precedence:

* ``wind_turbulence_intensity_profile.csv``: time-varying TI by ``(stage, wind_group, time)``
* ``wind_turbulence_intensity_fixed.csv``: fixed TI by ``(stage, wind_group)``
* roughness-derived fallback: ``1 / ln(hub_height / roughness)``

Model behavior
--------------

The wind-technology model creates wind-related sets, parameters, variables, and
constraints in ``wind_tech_model``. In particular:

* An available output factor is computed from:
  * wind speed
  * wind-group reference height
  * selected turbulence intensity, using profile, fixed, or roughness-derived data
  * technology parameters
* Wind-group/terrain outputs are summed to the total wind-technology output.
* Installed wind-technology capacity is split across terrain subgroups.
* Optional ``allowed_terrains`` in ``techs.yaml`` restricts a wind technology
  to selected terrains.
* Curtailment bounds can constrain unused available output.
* Wind-area constraints limit deployment only where ``wind_areas.csv`` defines
  an area for a specific ``(stage, hub, wind_group)`` tuple.

Related documentation
---------------------

* :ref:`model`
* :ref:`input_files`

