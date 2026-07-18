Changelog
==========

**2.3.0** (18.07.2026)
------------------------
- Publish codebase on GitHub and make it open-source under the GNU General Public License v3.
- Added ReadTheDocs configuration for automatic documentation generation.

**2.2.4** (11.12.2025)
------------------------
- ATES module reworked following insights from Bispebjerg paper.
- Advective radius now based on thermal-front velocity.
- Renamed some ates_param entries in hubs.yaml for clarity.

**2.2.3** (09.10.2025)
------------------------
- Tightened the problem formulation by significantly improving bigM values.
- Removed generic bigM parameter from demands model entirely.
- Many crucial elements like capacity are now guaranteed to carry upper bounds
- New parameters heur_max and heur_sum_max in ecs.yaml, mandatory for all ecs without demand data.

**2.2.2** (06.08.2025)
------------------------
- The units for currency, length, mass, and power defined in stages.yaml are now taken as the units in which the optimization is formulated. This was done to allow the modeler to scale the system in order to avoid large matrix coefficient ranges which often lead to numerical instabilities.
- The outut files are now also written in these units

**2.2.1** (28.07.2025)
------------------------
- Added possibility to specify demand_sums (i.e., annual demands)
- Fixed an infeasibility issue occuring with negative prices and costs
- Added minmax parameters for number of wells in ATES module
- Added availability parameters for ATES and heatpumps
- Improved value parsing so entries like "inf kW" or "1_000 kW" are now possible. Unfortunately, numbers and units must be separated by a space now, so entries like "20kW" will no longer be recognized.
- Reintroduced functionality into the load shifting module for Sisslerfeld:
  - Multiple load shifts for a single tuple
  - Sizing of load shift capacity done by the optimizer now

**2.2.0** (23.06.2025)
------------------------
- Introduced the Unit and Value classes which offer handling of physical units and values.
- Each ec now carries a unit. All modules check their input parameters for validity of units.
- Calculations with phyiscal units are now carried out directoy by the Value class, removing the need for manual unit transformations and ensuring cosistency across the code base and model.
- Changed the parameter responsible for network transmission losses to an exponential factor
- Removed preset functionality from load shedding module (presets don't work with potentially varying units anymore)
- Parameter nodes for imports, exports, load shifting and load shedding can now only be defined for a single ec to ensure unit consistency.

**2.1.7** (01.05.2025)
------------------------
- Fixed mistakes during tsam clustering, now fewer time steps in multistage models
- Greatly increased performance for time series parsing
- Fixed error for initial SOC constraint when first stage is not allowed for the tech

**2.1.6** (06.03.2025)
------------------------

Completely integrated the ATES technology submodule

**2.1.5** (14.02.2025)
------------------------

- Added customized output formating for all data (writer module)
- Renamed root module from ehubX to ehubx
- Changed directory generation logic

**2.1.4** (31.01.2025)
------------------------

- Introduced the writer subpackage
- Clustering and cutting implemented and tested
- Added a clustering example
- Added availability to network links

**2.1.3** (22.01.2025)
------------------------

- Autarky module based Wassim Chedhli's work in his master thesis added
- Included an example for an autarky maximizing model
- Fixed minor mistakes in multiobjective optimization routines


**2.1.2** (07.01.2025)
------------------------

- Main ehubX modules moved to new "core" submodule
- Added docstrings for core and data submodules
- Changed error to a warning when identical ECs are used for the heatpump tech

**2.1.1** (31.12.2024)
------------------------

- Added a custom model modification interface to the ehubX class
- Slight improvement of the network tech module for consistency (NetTechTuples)
- Finalized model documenation

**2.1.0** (17.12.2024)
------------------------

- Included a heat pump module. This is essentially a 3-in, 2-out conversion technology that can run in two modes (heating and cooling).
- Fixed the EBM module so it is now up to date with the current ehubX standard.

**2.0.3** (10.12.2024)
------------------------

Fixed a bug where not all output sets were written to results.csv

**2.0.2** (04.11.2024)
------------------------

Adapted tech models to work on "tech tuples" similar to other modules. Tech variables are no longer defined on all (stage, hub, tech) tuples but only on those where stage is allowed (due to TRL) and hub is allowed (due to allowed tech lists) for the tech.

**2.0.1** (25.10.2024)
------------------------

Small adaptations to input structure after dev meeting feedback. Changes include:

- New input file subdirectories (basic / networks / renewables). Renamed links.yaml -> network_links.yaml and net_techs.yaml -> network_techs.yaml
- trl_threshold, num_times_horizon and interest_rate_def in stages.yaml, remove system.yaml, remove interest rate categories. Tech interest rates and TRLs now optional (no interest rate: Use interest_rate_def. no TRL: Use trl=inf)
- Removed stage length from model
- Miscalleneous warnings
- Renamed "capex" -> "capex_per_cap", "fom" -> "opex_per_cap", "one_time_fom" -> "one_time_opex", "vom" -> "opex_per_energy", "embodied_co2eqeq" -> "co2_per_cap"
- Replaced "agg" with "sum" everywhere
- Removed "trans" from trains_agg_min_forward & co
- Removed "subtype" from techs.yaml and put solar and wind directly under "type"
- Renamed "lifetime_years" to "lifetime"
- Moved "in_ec_groups" to ec.yaml
- Renamed discharge_control to v2g_discharge_controllability
- Made imports and exports work with multiple tuples per entry
- Changed copyright in docs to (C) Copyright 2024, Urban Energy Systems Lab, Empa.


**2.0**
----------
Rewrite of ehubX in preparation for the open-source release. Changes
include:

- Complete redesign of the input structure on every level, improving for conciseness and consistency
- Input parser now contains general-purpose csv and yaml parsers. The parsing procedure is much more robust, allowing for empty or missing entries everywhere it is feasible. Logging warnings and custom exceptions give detailed and robust feedback to the user concerning wrong or unusual data in the input files.
- All data models now contain validation methods, giving feedback in the form of warnings or exceptions to the user when wrong or unusual patterns are detected in the input parameter data.
- The model generation module has been completely reworked to define a cleaner and more consistent model. Usage of Pyomo parameters was mostly avoided to save on model generation time, instead drawing data directly from the data model itself.
- New EhubX class now handles all user interactions with ehubX. Users can create an ehubX object and interact with its methods to parse, build and solve a model. Bundled methods are also available to streamline beginning-to-end  single-objective or multiobjective workflows
- A solver wrapper has been created to interact with the Gurobi and GLPK solvers through pyomo. It offers special functions to set the most commonly used parameters.
- Examples have been reduced to a single toy model for now
- Started documentation. Wrote the part about input files and added stubs for some other sections that will get written in future patches.
- Added a weighted-sum method for Pareto-front computations alongside the eps-constraint method.
- Tests deactivated for now, will get re-introduced in a future patch

**1.1**
----------
- More than two years since the last release. Changed to MAJOR.MINOR versioning system based on practical experiences at the lab.
- This system is the ehubX legacy version which still runs with most older models (e.g., VSE, Rheintal). After this, a major overhaul of the input system will take place that will make ehubX incompatible to all previous models.
- The input structure does not yet support yearly parameters and the network.yaml still has the old structure. There is little to no user feedback or sense-checking of inputs.
- The output structure is still a single auto-generated CSV file.
- From the model perspective:
  - m2-based solar module is default but kW-based module still exists
  - EBM-module exists
  - Load shift and load shedding modules exist
  - Autarky module still in legacy form
- Only input parser is tested thoroughly


**1.0.0**
-----------

# Features

- BRAKING YAML INTERFACE:

  - decoupling of technology and hub parameters to facilitate tech yaml sharing and multistage model formulation.
  - redefinded the min/max cap and min/max output parameters to defiend per stage and hub
  - availability per stage and hub

- do use the interest rate defined in YAML to calculate CRF factor instead of general interest rate parameter

- Autarky implementation

- Add CO2 export and Carbon Balance

# Cleanup

- Remove unused parameters in tech yaml (e.g. ramping)
- Removed name and capacity unit parameter from all dataclasses and yaml, which were for information only
- improve main script

# Bugfixes

- fix disabling capacity constraint for solar and wind techs
- explizit definition of main input and output enenrgy carrier for conversion technologies


**0.3.0**
-----------
# Features

- Update how the gurobi solver is called in case of multiobjective optimization so that model is cached
- Temporal clustering (autarky module not yet working with typical hours, equations need to be adapted)
- Normalization for network added
- Conversion tech availability
- Net link cap time-dependent
- Storage efficiency

# Cleanup

- remove unused parameters in conversion tech (min_load, max_load from YAML and model, seasonal, virtual, partLTech from data model)
- remove ramping parameters from yaml and data model (as it will not be implemented right now)
- remove name attribute from all data model classes

# Bugfixes

- Fix to network parse "inf" for unit_cap_max
- Fixed storage initial SoC
- Fixed constraints in conversion tech, speed up model build time.


**0.2.0**
------
# Features

- Adding Coupled Technology
- Removed Excel Input Parser
- Adding Example with 168h
- Efficiency parameter per timestep
- Running tests with glpk
- Normalize data
- Updated wind equations
- Improvements for import/export
- ...probably incomplete

# Bugfixes

- Bug Fixes Solar/Wind
- Fixed duplicating techs for more than two ec in a ec group
- Bug with V_YTechUsed
- Fix duplicated P_CurtaIlFactor in Wind and Solar module
- ... probably incomplete


**0.1.0**
------

Initial version created with the UES Lab Python project template from https://gitlab.empa.ch/ues-lab/tools/templates/python-cicd
