.. _input_files:

Input files
============

Please note that in this chapter, we use the following notation conventions regarding :ref:`units <units>`:

* **[CAP]**: Capacity unit of a technology
* **[ec]**: For parameters where there is obviously one energy carrier, [ec] will refer to the unit of that ec.
* **[ec_in]**, **[ec_out]** Units of input/output energy carriers
* **[ec_in_main]**, **[ec_out_main]**: Unit of main input/output energy carriers of conversion technologies
* **[CAP_sub]**, **[CAP_main]**: Capacity units of sub/main techs for coupled technologies.
* We will some of the following units in the list below as stand-ins for the basic units, but these can always be changed to other, equivalent units in the inputs (for example, one could use *EUR* instead of *CHF* for currency units, or *s* instead of *h* for time units).
    * **CHF**: Swiss Franc, stand-in for currency units
    * **kg**: kilograms, stand-in for mass units
    * **m**: meters, stand-in for length units
    * **h**: hours, stand-in for time units

.. _file_overview:

File overview
--------------

.. code-block:: ruby

    model
    |-- inputs
        |-- basic
            |-- demands.yaml
            |-- ecs.yaml
            |-- exports.yaml
            |-- hubs.yaml
            |-- imports.yaml
            |-- stages.yaml
            |-- techs.yaml
        |-- network
            |-- network_links.yaml
            |-- network__techs.yaml
        |-- renewables
            |-- solar_areas.csv
            |-- solar_irradiation.csv


Parameter legend
-----------------

* **per-year**: Whether this parameter can be specified as year-dependent (see :ref:`parameter types <parameter_types>`)
* **per-ts**: Whether this parameter can be specified as a timeseries (see :ref:`parameter types <parameter_types>`). This will happen by specifying a path to a time series file, and the specific structure is dependent on the parameter itself.
* **file**: File in which this parameter is specified.


.. _stages_yaml:

stages.yaml
------------

.. literalinclude:: model_inputs/basic/stages.yaml
    :language: ruby
    :caption: Model *stages.yaml* file

**System parameters**:

* **system_params** (*mandatory*): Dictionary of system-wide parameters
* **interest_rate_def** (*mandatory, [-]*): Default interest rate used across the system when no other rate is specified.
* **trl_threshold** (*optional, default=0, [-]*): Technology readiness level (TRL) threshold value above which technologies can be installed and used.
* **num_times_horizon** (*mandatory, [-]*): Number of time steps in the time horizon.
* **self_sufficiency_calculation_method** (*optional, default="none"*): Method how the system's self-sufficiency value should be calculated. Can be "none" (self-sufficiency is not calcualted), "quadratic" (self-sufficiency value is calculated using its quadratic definition), or "linearized" (self-sufficiency value is calculated using a triangulation-based discretization of the expected domain for internal imports and cross-imports).
* **self_sufficiency_min** (*optional, [-], default=0*): Minimal value for the overall system self-sufficiency.
* **self_sufficiency_max** (*optional, [-], default=1*): Maximal value for the overall system self-sufficiency.
* **curreny_unit** (*optional, default="CHF"*): Unit for currency values in the result files, see :ref:`units <units>`.
* **length_unit** (*optional, default="m"*): Unit for length values in the result files, see :ref:`units <units>`.
* **mass_unit** (*optional, default="kg"*): Unit for mass values in the result files, see :ref:`units <units>`.
* **power_unit** (*optional, default="kW"*): Unit for power values in the result files, see :ref:`units <units>`.

**Stages**:

* **stages** (*optional, default=[]*): Identifiable list of stages
* **stage_id** (*mandatory*): Stage id
* **start_year** (*mandatory, [-]*): First year of the stage. This year is used to interpolate year-dependent parameters (see :ref:`parameter types <parameter_types>`). Among the stages, each start year must be unique. The stages do not have to be defined in order of their start year.
* **co2_price** (*optional, default=0, [CHF/kg]*): Price for CO2 emissions.
* **co2_min** (*optional, default=* -:math:`\infty`, *, [kg]*): Minimal amount of CO2 emissions in this stage.
* **co2_max** (*optional*, *default=* :math:`\infty`, *[kg]*): Maximal amount of CO2 emissions in this stage.


.. _hubs_yaml:

hubs.yaml
------------

.. literalinclude:: model_inputs/basic/hubs.yaml
    :language: ruby
    :caption: Model *hubs.yaml* file

.. literalinclude:: model_inputs/basic/profiles/hub_profiles.csv
    :language: ruby
    :caption: *hub_profiles.csv*: Time series file for hub profiles.

.. literalinclude:: model_inputs/basic/profiles/ates_profiles.csv
    :language: ruby
    :caption: *ates_profiles.csv*: Time series file for ATES profiles.

**Technology lists**:

* **tech_lists** (*optional, default=[]*): Identifiable list of tech lists.
* **tech_list_id** (*mandatory*): Tech list id.
* **techs** (*mandatory*): Tech ids which belong to the tech list.

**Hubs**:

* **hubs** (*optional, default=[]*): Identifiable list of hubs.
* **hub_id** (*mandatory*): Hub id.
* **allowed_tech_lists** (*optional, default=[]*): List of tech list ids which are allowed for this hub. If a single tech list id (e.g.; *TechList1* above) is passed, this is equivalent to passing a list with this element (i.e., *TechList1*).
* **techs** (*optional, default=[]*): Identifiable list of techs for which hub-specific parameters are to be defined.

**Hub-speficic technology parameters**:

* **tech_params** (*optional, default={}*) Dictionary with parameters for the :ref:`tech model <tech_model>`.
* **age_init** (*optional, default=0, [a]*): Age of preinstalled technology at this hub.
* **cap_init** (*optional, default=0, [CAP]*): Capacity amount of preinstalled technology at this hub.
* **cap_min** (*optional, default=0, [CAP], per-year*): Minimal amount of installed capacity at this hub.
* **cap_max** (*optional*, *default=* :math:`\infty`, *[CAP], per-year*): Maximal amount of installed capacity at this hub.
* **last_inst_year** (*optional*, *default=* :math:`\infty`, *[-]*): Last year where installation of this technology is allowed at this hub.

**Hub-speficic storage technology parameters**:

* **storage_params** (*optional, default={}*) Dictionary with parameters for the :ref:`storage model<storage_model>`.
* **soc_init** (*optional*, *default=* :math:`\infty`, *[-]*): Initial state of charge at the beginning of each stage's time horizon, as a value between 0 and 1, relative to the total installed storage capacity. Alternatively, setting this value to :math:`\infty` lets the optimizer choose it without any restriction. Due to the periodicity constraint (see :ref:`storage model<storage_model>`), the initial state of charge will also be the stage of charge at the end of the time horizon.

**Hub-specific conversion technology parameters**:

* **conversion_params** (*optional, default={}*): Dictionary with parameters for the :ref:`conversion model<conversion_model>`.
* **out_sum_min** (*optional, default=0, [ec_out_main], per-year*): Minimal value for the summed-up output of the conversion technology's main output carrier across the time horizon.
* **out_sum_max** (*optional*, *default=* :math:`\infty`, *[ec_out_main], per-year*): Maximal value for the summed-up output of the conversion technology's main output carrier across the time horizon.
* **availability** (*optional, default=1, [-], per-ts*): Multiplier for the conversion technology's availability to output energy. An availability of 1 means that the technology is able to operate at full capacity, an availability of 0 means that it is not able to produce any output.
* **profile_path** (*optional, default=None, file*): File path (relative to hubs.yaml) of a time series file with time-specific data for the time-dependent conversion parameters above. It has to contain the following headers:
    * *stage_id*: Stage id
    * *hub_id*: Hub id, only the currently active hub is parsed
    * *tech_id*: Technology id, only the currentivly active tech is parsed.
    * *profile_key*: Name of parameter for which time-dependent data is being defined. Only *availability* is parsed.

**Hub-specific ATES technology parameters**:

* **ates_params** (*optional, default=[]*): Dictionary with parameters for the :ref:`ates model <ates_model>`.
* **elec_per_energy_heat** (*optional, [-], per-year*): Electricity consumption (in kW) for each amount of heating output (in kW). If this parameter is not set, it will be calculated from the parameter *elec_per_flow_heat*.
* **elec_per_energy_cool** (*optional, [-], per-year*): Electricity consumption (in kW) for each amount of cooling output (in kW). If this parameter is not set, it will be calculated from the parameter *elec_per_flow_cool*.
* **well_distance** (*optional, [m], per-year*): Well distance between well pairs. This parameter is mandatory if max_pump_rate_per_cold_well or max_pump_rate_per_warm_well are not specified.
* **schedule_params** (*optional, default = {}*): List with schedule-dependent parameters.
* **schedule_id** (*mandatory each schedule block*): Id of ATES schedule (as defined in *ates_params* below).
* **well_pairs_min** (*optional, default=0, [-], per-year*): Minimal number of well pairs that have to be operating under this schedule for this ATES technology at this hub.
* **well_pairs_max** (*optional, default=* :math:`\infty`, *, [-], per-year*): Maximal number of well pairs that may be operating under this schedule for this ATES technology at this hub.
* **max_pump_rate_per_warm_well** (*optional, [m^3/s], per-year*): Maximal pumping rate for extraction from a warm well. If this parameter is not specified, the maximal pumping rate is calculated using the Theis equation, based on the parameters *well_radius*, *storativity_aquifer*, *hydraulic_conductivity_aquifer*, *thickness_aquifer*, and *max_drawdown*.
* **max_pump_rate_per_cold_well** (*optional, [m^3/s], per-year*): Maximal pumping rate for extraction from a cold well. If this parameter is not specified, the maximal pumping rate is calculated using the Theis equation, based on the parameters *well_radius*, *storativity_aquifer*, *hydraulic_conductivity_aquifer*, *thickness_aquifer*, and *max_drawdown*.
* **thermal_radius_per_warm_well** (*optional, [m], per-year*): Thermal radius, i.e.; approximation of the furthest distance from the well center at which the injection of warm fluid into the well still affects the underground thermal state. If this parameter is not specified, the thermal radius is calculated using the conductive and convective radii, based on the parameters *specific_heat_capacity_fluid*, *max_pump_rate_per_cold_well*, *specific_heat_capacity_aquifer*, *thickness_aquifer*, and *groundwater_velocity*.
* **thermal_radius_per_cold_well** (*optional, [m], per-year*): Thermal radius, approximation of the furthest distance from the well center at which the injection of cold fluid into the well still affects the underground thermal state. If this parameter is not specified, the thermal radius is calculated using the conductive and convective radii, based on the parameters *specific_heat_capacity_fluid*, *max_pump_rate_per_warm_well*, *specific_heat_capacity_aquifer*, *thickness_aquifer*, and *groundwater_velocity*.
* **max_heat_over_cool** (*optional, default=* :math:`\infty`, *[-], per-year*): Maximal quotient of total (i.e.; summed-up over time) ATES heating output over total ATES cooling output for this technology in this schedule. For feasibility reasons, the product between this parameter and *max_cool_over_heat* must not be smaller than one.
* **max_cool_over_heat** (*optional, default=* :math:`\infty`, *[-], per-year*): Maximal quotient of total (i.e.; summed-up over time) ATES cooling output over total ATES heating output for this technology in this schedule. For feasibility reasons, the product between this parameter and *max_heat_over_cool* must not be smaller than one.
* **availability** (*optional, default=1, [-], per-ts*): Multiplier for the ATES technology's ability to extract and inject energy. An availability of 1 means that the technology is able to operate at full capacity, an availability of 0 means that it is not able to extract or inject any energy.
* **profile_path** (*optional, default=None, file*): File path (relative to hubs.yaml) of a time series file with time-specific data for the time-dependent ATES parameters above. It has to contain the following headers:
    * *stage_id*: Stage id.
    * *hub_id*: Hub id, only the currently active hub is parsed.
    * *tech_id*: Technology id, only the currentivly active tech is parsed.
    * *ates_schedule_id*: Id of ATES schedule.
    * *profile_key*: Name of parameter for which time-dependent data is gathered. Only *availability* is parsed.

**Hub-specific Electricity-Based Mobility (EBM) technology parameters**:

* **ebm_params** (*mandatory for EBM techs*) Dictionary with parameters for the :ref:`EBM model<ebm_model>`.
* **num_vehicles** (*mandatory, [-], per-year*): Number of vehicles in the EBM fleet.
* **soc_init** (*optional, default=* :math:`\infty`, *[-]*): Initial state of charge for the EBM fleet at the beginning of each stage's time horizon, as a value between 0 and 1, relative to the total storage capacity. Alternatively, setting this value to :math:`\infty` lets the optimizer choose it without any restriction. Due to the periodicity constraint (see :ref:`storage model<storage_model>`), the initial state of charge will also be the stage of charge at the end of the time horizon.
* **demand_modifier** (*optional, default=1, [-], per-ts*): Modifier for the EBM demand curve. The values of *demand_nominal* are multiplied with this modifier value to obtain the actual demand.
* **demand_nominal** (*optional, default=0, [ec/h], per-ts*): Nominal EBM demand of a single vehicle. These values are multiplied with *demand_modifier* to obtain the actual demand of one vehicle. This value is then again multiplied by *num_vehicles* to determine the demand of the entire fleet.
* **availability** (*optional, default=1, [-], per-ts*): Multiplier for the technology's ability to charge and discharge. An availability of 1 means that the entire fleet is available for charging and discharging, an availability of 0 means that the entire fleet is unavailable.
* **profile_path** (*optional, default=None, file*): File path (relative to hubs.yaml) of a time series file with time-specific data for the time-dependent EBM parameters above. It has to contain the following headers:
    * *stage_id*: Stage id.
    * *hub_id*: Hub id, only the currently active hub is parsed.
    * *tech_id*: Technology id, only the currentivly active tech is parsed.
    * *profile_key*: Name of parameter for which time-dependent data is gathered. Only *demand_nominal* and *availability* are parsed.

**Hub-specific heat pump technology parameters**:

* **heatpump_params** (*mandatory for heat pump techs*): Dictionary with parameters for the :ref:`heat pump model<heatpump_model>`.
* **cop** (*optional, [-], per-ts*): Coefficient of performance for the heat pump. If this parameter is not specified, the COP is calculated using a dampened Carnot efficiency (see :ref:`heat pump model<heatpump_model>`) with the parameters *temp_heat_in*, *temp_heat_out* and *cop_factor*.
* **temp_heat_in** (*optional, [K], per-ts*): Temperature of heating mode heat inlet (i.e.; evaporator inlet temperature). This parameter becomes mandatory if the parameter *cop* is not set, since the inlet temperature is then used to calculate the COP.
* **temp_heat_out** (*optional, [K], per-ts*): Temperature of heating mode heat outlet (i.e.; condenser outlet temperature). This parameter becomes mandatory if the parameter *cop* is not set, since the outlet temperature is then used to calculate the COP.
* **availability** (*optional, default=1, [-], per-ts*): Multiplier for the heat pump's maximal condenser power. An availability of 1 means that the heat pump is able to operate at full capacity, an availability of 0 means that it is not able to operate at all.
* **profile_path** (*optional, default=None, file*): File path (relative to hubs.yaml) of a time series file with time-specific data for the time-dependent heat pump parameters above. It has to contain the following headers:
    * *stage_id*: Stage id.
    * *hub_id*: Hub id, only the currently active hub is parsed.
    * *tech_id*: Technology id, only the currentivly active tech is parsed.
    * *profile_key*: Name of parameter for which time-dependent data is gathered. Only *cop*, *temp_heat_in*, *temp_heat_out* and *availability* are parsed.

**ATES parameters (technology-independent)**:

* **ates_params** (*mandatory for hubs with ATES technologies*): Dictionary with ATES-specific parameters which are independent of technologies for this hub.
* **groundwater_velocity** (*optional, [m/d]*): Groundwater (i.e.; Darcy) velocity. This parameter becomes mandatory if the parameters *thermal_radius_per_warm_well* or *thermal_radius_per_cold_well* are not set, since the groundwater velocity is then used to calculate these radii.
* **specific_heat_capacity_aquifer** (*optional, [Ws/(kg*K)]*): Specific heat capacity of the aquifer. This parameter becomes mandatory if the parameters *thermal_radius_per_warm_well* or *thermal_radius_per_cold_well* are not set, since the specific heat capacity is then used to calculate these radii.
* **thickness_aquifer** (*optional, [m]*): Thickness (i.e.; height) of the aquifer. This parameter becomes mandatory if the parameters *thermal_radius_per_warm_well* or *thermal_radius_per_cold_well* are not set, since the thickness is then used to calculate these radii.
* **storativity_aquifer** (*optional, [-]*): Storativity (or storage coefficient) of the aquifer which is the volume of water released from storage per unit decline in hydraulic head in the aquifer, per unit area of the aquifer. This parameter becomes mandatory if the parameters *max_pump_rate_per_warm_well* or *max_pump_rate_per_cold_well* are not set, since the storativity is then used to calculate these rates.
* **max_drawdown** (*optional, [m]*): Maximal allowed drawdown (i.e.; surface decline) at the border of an ATES well. This parameter becomes mandatory if the parameters *max_pump_rate_per_warm_well* or *max_pump_rate_per_cold_well* are not set, since the maximal drawdown is then used to calculate these rates.
* **max_temperature_spread_warm** (*mandatory, [K]*): Maximal allowed temperature spread between the natural aquifer temperature and the temperature of fluid in the warm wells.
* **max_temperature_spread_cold** (*mandatory, [K]*): Maximal allowed temperature spread between the natural aquifer temperature and the temperature of fluid in the cold wells.
* **available_area** (*optional*, *default=* :math:`\infty, [m^2]`, per-year*): Available aquifer area for ATES installation.
* **schedules** (*mandatory*): List of ATES schedules (see :ref:`ates model <ates_model>`).
* **schedule_id** (*mandatory*): Id of ATES schedule
* **phase_w2c_start_id** (*mandatory*): Time id of the start of the warm-to-cold pumping phase.
* **phase_w2c_end_id** (*mandatory*): Time id of the end of the warm-to-cold pumping phase.
* **phase_c2w_start_id** (*mandatory*): Time id of the start of the cold-to-warm pumping phase.
* **phase_c2w_end_id** (*mandatory*): Time id of the end of the cold-to-warm pumping phase.

.. _network_links_yaml:

network_links.yaml
-------------------

.. literalinclude:: model_inputs/network/network_links.yaml
    :language: ruby
    :caption: Model *network_links.yaml* file

.. literalinclude:: model_inputs/network/profiles/net_link_profiles.csv
    :language: ruby
    :caption: *net_link_profiles.csv*: Time series file for network link profiles.

**Network technology lists:**

* **net_tech_lists** (*optional, default=[]*): Identifiable list of network tech lists.
* **net_tech_list_id** (*mandatory*): Network tech list id.
* **net_techs** (*mandatory*): Network tech ids which belong to the network tech list.

**Links:**

* **start_hubs** (*optional, default=[]*): Identifiable list of start hubs for links.
* **start_hub_id** (*mandatory*): Id of start hub.
* **end_hubs** (*optional, default=[]*): Identifiable list of end hubs for links.
* **end_hub_id** (*mandatory*): Id of end hub.
* **links** (*optional, default=[]*): Identifiable list of links connecting the start hub and the end hub.
* **link_id** (*mandatory*): Id of link.
* **ecs** (*mandatory*): List of EC ids which can be transported along this link. Needs to contain at least one EC.
* **length** (*mandatory, [m]*): Length of link.
* **bidirectional** (*optional, default=False*): Boolean value indicating whether this link is bidirectional. If the value is True, ECs can be transported along this link in both directions. If the value is False, ECs can only be transported from the start hub to the end hub.
* **allowed_net_tech_lists** (*optional, default=[]*): List of network tech list ids for which installation and usage is allowed on this link.

**Link-specific network technology parameters**:

* **net_tech_params** (*optional, default={}*) Dictionary with link-specific network technology parameters for the :ref:`network model<network_model>`.
* **net_tech_id** (*mandatory*): Id of network technology. Must be part of one of the *allowed_net_tech_lists* on this link.
* **age_init** (*optional, default=0, [a]*): Age of preinstalled network technology on this link.
* **cap_init** (*optional, default=0, [ec/h]*): Capacity amount of preinstalled network technology on this link.

**Link-specific EC parameters**

* **ec_params** (*optional, default={}*): Dictionary with link-specific EC parameters for the :ref:`network model<network_model>`.
* **ec_id** (*mandatory*): Id of EC. Must be part of this link's *ec_ids*.
* **cap_min** (*optional, default=0, [ec/h], per-year*): Minimal amount of cummulative capacity on this link of network techs that can transport this EC.
* **cap_max** (*optional*, *default=* :math:`\infty`, *[ec/h], per-year*): Maximal amount of cummulative capacity on this link of network techs that can transport this EC.
* **sum_min_forward** (*optional, default=0, [ec], per-year*): Minimal amount of energy for this EC that is transported along this link from the start hub to the end hub.
* **sum_min_backward** (*optional, default=0, [ec], per-year*): Minimal amount of energy for this EC that is transported along this link from the end hub to the start hub. This parameter is only taken into consideration if the link is *bidirectional*.
* **sum_max_forward** (*optional*, *default=* :math:`\infty`, *[ec], per-year*): Maximal amount of energy for this EC that is transported along this link from the start hub to the end hub.
* **sum_max_backward** (*optional*, *default=* :math:`\infty`, *[ec], per-year*): Maximal amount of energy for this EC that is transported along this link from the end hub to the start hub. This parameter is only taken into consideration if the link is *bidirectional*.
* **availability** (*optional, default=1, [-], per-ts*): Multiplier for all network technology's ability on this link to transmit energy. An availability of 1 means that each technology is able to operate at full capacity, an availability of 0 means that none is not able to transmit anything.
* **profile_path** (*optional, default=None, file*): File path (relative to network_links.yaml) of a time series file with time-specific data for the time-dependent network link parameters above. It has to contain the following headers:
  * *stage_id*: Stage id, only the currently active stage id is parsed.
  * *link_id*: Network link id, only the currently active link id is parsed.
  * *ec_id*: EC id, only the currently active EC id is parsed.
  * *profile_key*: Name of parameter for which time-dependent data is being defined. Only *availability* is parsed.


.. _techs_yaml:

techs.yaml
------------

.. literalinclude:: model_inputs/basic/techs.yaml
    :language: ruby
    :caption: Model *techs.yaml* file

* **techs** (*optional, default=[]*): Identifiable list of technologies
* **tech_id** (*mandatory*): Technology id.
* **type** (*optional, default=None*): Type of technology. If this parameter is set correctly, the technology will be added to the respective submodel. Acceptable values are:
    *  :code:`storage` (:ref:`storage model <storage_model>`),
    *  :code:`conversion` (:ref:`conversion model <conversion_model>`),
    *  :code:`solar` (:ref:`solar model <solar_model>`)
    *  :code:`ebm` (:ref:`EBM model <ebm_model>`),
    *  :code:`ates` (:ref:`ates model <ates_model>`) and
    *  :code:`heatpump` (:ref:`heatpump model <heatpump_model>`)..

**Technology parameters**:

* **tech_params** (*optional, default={}*) Dictionary with parameters for the :ref:`tech model <tech_model>`.
* **lifetime** (*mandatory, [a]*): Lifetime of technology from installation to EOL.
* **unit_cap_min** (*optional, default=0, [CAP], per-year*): Minimal amount of capacity that has to be installed if any installation takes place (so installed capacity will either be 0 or at least this amount).
* **trl** (*optional, default=* :math:`\infty`, *, [-], per-year*): Technology Readiness Level (TRL) for the technology. Only technologies with a TRL above the threshold value specified in :ref:`stages.yaml <stages_yaml>` can be installed.

**Technology cost parameters**:

* **costs** (*mandatory*): Dictionary with cost parameters for the :ref:`tech model <tech_model>` and the :ref:`conversion model <conversion_model>`.
* **interest_rate** (*optional, default=None, [-]*): Interest rate for this technology. If none is specified, the default interest rate defined in :ref:`stages.yaml <stages_yaml>` will be used.
* **one_time_capex** (*optional, default=0, [CHF], per-year*): Fixed CAPEX cost that occurs if any amount of capacity is installed for this technology.
* **capex_per_cap** (*optional, default=0, [CHF/CAP], per-year*): CAPEX cost per amount of installed capacity for this technology.
* **one_time_opex** (*optional, default=0, [CHF], per-year*): Operation & maintenance cost that occurs if any amount of this technology is used during the time horizon.
* **opex_per_cap** (*optional, default=0, [CHF/CAP], per-year*): Operation & maintenance cost per amount of installed capacity for this technology.
* **opex_per_energy** (*optional, default=0, [CHF/(ec_out_main)], per-year*): Operation & maintenance cost for conversion technologies per amount of output of the conversion technology's main output carrier (see :ref:`conversion model<conversion_model>` for more details)

**Technology emission parameters**:

* **emissions** (*optional, default={}*): Dictionary with emission parameters for the :ref:`tech model <tech_model>`.
* **co2_per_cap** (*optional, default=0, [kg/CAP], per-year*): Embodied CO2 that arises per amount of newly installed capacity for this technology.

**Storage parameters**:

* **storage_params** (*mandatory for storage techs*): Dictionary with parameters for the :ref:`storage model <storage_model>`.
* **ec** (*mandatory for storage techs*): Id of EC that is storable in this technology. The value must be an id which is defined in :ref:`ecs.yaml <ecs_yaml>`.
* **in_eff** (*optional, default=1, [-], per-year*): Efficiency of storage input, i.e.; percentage of the charging energy that makes it into the storage technology.
* **out_eff** (*optional, default=1, [-], per-year*): Efficiency of output, i.e.; percentage of the energy that can be used at the end of the discharging process.
* **charge_max** (*optional*, *default=1, [1/h], per-year*): Maximal relative charging power per installed capacity.
* **discharge_max** (*optional*, *default=1, [1/h], per-year*): Maximal relative discharging power per installed capacity.
* **soc_min** (*optional, default=0, [-], per-year*): Minimal stage of charge (fraction of total storage capacity) that is allowed in the storage technology.
* **soc_max** (*optional, default=1, [-], per-year*): Maximal stage of charge (fraction of total storage capacity) that is allowed in the storage technology.
* **standby_loss** (*optional, default=0, [1/h], per-year*): Fraction of stored energy that is lost per timestep independent of other storage operations.

**Conversion parameters**:

* **conversion_params** (*mandatory for conversion techs*): Dictionary with parameters for the :ref:`conversion model <conversion_model>`.
* **in_ecs** (*mandatory for conversion techs*): Identifiable list that defines the composition of conversion inputs.
* **in_id** (*mandatory for conversion techs*): Id of input EC or input EC group.
* **in_part** (*mandatory for conversion techs, [ec_in], per-year*): Input part of the conversion technology's total input energy that consists of the above ec. The relation between all in_parts defines the relation between all input flows into the conversion technology (cf. :ref:`conversion model <conversion_model>`)
* **main_in_ec** (*mandatory for conversion techs with more than one input ec, default=e for conversion techs with a single in_ec e*): Id of input ec that is desgignated the *main input ec*.
* **out_ecs** (*mandatory for conversion techs*): Identifiable list that defines the efficiency values of the conversion technology's energy output.
* **ec_id** (*mandatory for conversion techs*): Id of output ec.
* **out_eff** (*mandatory for conversion techs, [ec_out / ec_in_main], per-year or per-ts*): This efficiency value describes the quotient between this output ec's energy output and the main input ec's energy input. It can be given as a year-dependent parameter. Alternatively, it can be given by a relative path to a time series file. This csv file must have the three headers: stage, tech and ec.
* **main_out_ec** (*mandatory for conversion techs with more than one output ec, default=e, for conversion techs with a single out_ec e*): Id of output ec that is designated the *main output ec*.

.. literalinclude:: model_inputs/basic/profiles/efficiency_profiles.csv
    :language: ruby
    :caption: *efficiency_profiles.csv*: Model output efficiency file for conversion technologies


**Solar parameters**

* **solar_params** (*optional, default={}*): Dictionary with parameters for the :ref:`solar model <solar_model>`.
* **curtail_max_rel** (*optional, default=1, [-], per-year*): Fraction of solar power that can be curtailed. A value of 0 means that all power has to be used while a value of 1 indicates that any part of the energy can be curtailed.

**ATES parameters**

* **ates_params** (*mandatory for ATES techs*): Dictionary with parameters for the :ref:`ates model <ates_model>`
* **ecs** (*mandatory*): Dictionary with ecs of the ATES technology.
* **elec** (*mandatory*): Ec that models electricity consumption of the well pumps.
* **heat** (*mandatory*): Ec that models heating energy extracted from the warm wells.
* **cool** (*mandatory*): Ec that models cooling energy extracted from the cold wells.
* **density_fluid** (*mandatory, [kg/m^3]*): Density of the fluid stored in the aquifer.
* **specific_heat_capacity_fluid** (*mandatory, [Ws/(kg*K)]*): Specific heat capacity of the fluid stored in the aquifer.
* **well_radius** (*optional, [m]*): Radius of a well. This parameter becomes mandatory if the parameters *max_pump_rate_per_warm_well* or *max_pump_rate_per_cold_well* in :ref:`hubs.yaml <hubs_yaml>` are not specified, since the radius is then used to calculate these rates.
* **well_pair_area_calc_method** (*optional, default="smallest rectangle"*): Calculation method for the area taken up by a well pair. Acceptable values are "two circles" and "smallest rectangle".
* **elec_per_flow_heat** (*optional, default=0, [kWh/m^3], per-year*): Electricity consumption (in kW) for each amount of warm-to-cold volume flow (in :math:`m^3/h`). This parameter is used to calculate the ATES electricity consumption per amount of output heating energy if the parameter *elec_per_energy_heat* is not set.
* **elec_per_flow_cool** (*optional, default=0, [kWh/m^3], per-year*): Electricity consumption (in kW) for each amount of cold-to-warm volume flow (in :math:`m^3/h`). This parameter is used to calculate the ATES electricity consumption per amount of output cooling energy if the parameter *elec_per_energy_cool* is not set.

**Electricity-Based Mobility (EBM) parameters**

* **ebm_params** (*mandatory for EBM techs*): Dictionary with parameters for the :ref:`EBM model<ebm_model>`.
* **ec** (*mandatory for EBM techs*): Id of the ec that powers EBM vehicles.
* **storage_cap** (*mandatory, [ec], per-year*): Storage capacity of a single EBM vehicle.
* **in_eff** (*optional, default=1, [-], per-year*): Efficiency of storage input, i.e.; percentage of the charging energy that makes it into the EBM technology.
* **out_eff** (*optional, default=1, [-], per-year*): Efficiency of output, i.e.; percentage of the energy that can be used at the end of the discharging process.
* **standby_loss** (*optional, default=0, [-], per-year*): Fraction of stored energy that is lost per timestep independent of other storage operations.
* **soc_min** (*optional, default=0, [-], per-year*): Minimal stage of charge (fraction of the total storage capacity) that is allowed in the EBM technology.
* **soc_max** (*optional, default=1, [-], per-year*): Maximal stage of charge (fraction of total storage capacity) that is allowed in the EBM technology.
* **charge_max** (*optional*, *default=* :math:`\infty`, *[ec/h], per-year*): Maximal charging power of a single EBM vehicle.
* **discharge_max** (*optional*, *default=* :math:`\infty`, *[ec/h], per-year*): Maximal discharging power of a single EBM vehicle.
* **discharge_controllability** (*optional, default=1, [-], per-year*): Discharge controllability of the EBM fleet. This is a heuristic factor that dampens the maximal discharge speed of the EBM fleet. A discharge control of 1 means that the available (see :ref:`hubs.yaml <hubs_yaml>` for the EBM availability parameter) portion of the fleet can be discharged at its maximal discharging power. A discharge control of 0 means that discharging is impossible.

**Coupling parameters**

* **coupling_params:** (*mandatory for coupled techs*): Dictionary with parameters for coupling (see :ref:`tech model<tech_model>`).
* **main_tech_id** (*mandatory*): Id of this tech's main tech.
* **cap_factor** (*mandatory, [CAP_sub/CAP_main]*): Fraction of this tech's capacity in relation to the main tech's capacity.

**Heat pump parameters**

* **heatpump_params:** (*mandatory for heat pump techs*): Dictionary with parameters for heat pumps (see :ref:`heat pump model <heatpump_model>`).
* **ecs** (*mandatory*): Dictionary with energy carriers for the heat pump.
* **elec** (*mandatory*): Ec id of the heat pump's electricity ec.
* **heat_in** (*mandatory*): Ec id of the heat pump's input ec in heating mode.
* **heat_out** (*mandatory*): Ec id of the heat pump's output ec in heating mode.
* **cool_in** (*mandatory*): Ec id of the heat pump's input ec in cooling mode.
* **cool_out** (*mandatory*): Ec id of the heat pump's output ec in cooling mode.
* **cop_factor** (*optional, default=0.5, [-], per-year*): Parameter used to calculate heat pump COP from Carnot efficiency. Used together with temperatures if *cop* is not directly specified in :ref:`hubs.yaml <hubs_yaml>`.


.. _network_techs_yaml:

network_techs.yaml
-------------------

.. literalinclude:: model_inputs/network/network_techs.yaml
    :language: ruby
    :caption: Model *network_techs.yaml* file

**Network technology parameters**

* **net_techs** (*optional, default={}*): Dictionary with network technology parameters for the :ref:`network model <network_model>`.
* **net_tech_id** (*mandatory*): Network technology id.
* **ec** (*mandatory*): ID of EC that is being transported with this technology.
* **lifetime_years** (*mandatory, [a]*): Lifetime of technology from installation to EOL.
* **trl** (*optional, default=* :math:`\infty`, *[-], per-year*): Technology Readiness Level (TRL) for the network technology. Only technologies with a TRL above the threshold value specified in :ref:`stages.yaml <stages_yaml>` can be installed.
* **unit_cap_min**: (*optional, default=0, [ec/h], per-year*): Minimal amount of capacity that has to be installed if any installation takes place (so installed capacity will either be 0 or at least this amount).
* **trans_decay** (*optional, default=0, [1/m], per-year*): Exponential factor in the transmission decay model resulting in a transmission loss along the linkj. A *trans_decay* value of 0 means that no energy is lost in the transmission process at all.

**Network technology cost parameters**

* **costs** (*mandatory*): Dictionary with cost parameters for the :ref:`network model <network_model>`.
* **interest_rate** (*optional, default=None, [-]*): Interest rate for this network technology. If none is specified, the default interest rate defined in :ref:`stages.yaml <stages_yaml>` will be used.
* **one_time_capex** (*optional, default=0, [CHF/m], per-year*): Fixed CAPEX cost per length that occurs if any amount of capacity is installed for this network technology.
* **capex_per_cap** (*optional, default=0, [CHF/((ec/h)*m)], per-year*): CAPEX cost per amount of installed capacity and length for this network technology.
* **one_time_opex** (*optional, default=0, [CHF/m], per-year*): Operation & maintenance cost per length that occurs if any amount of this network technology is used during the time horizon.
* **opex_per_cap** (*optional, default=0, [CHF/((ec/h)*m)], per-year*): Operation & maintenance cost per amount of installed capacity and length for this technology.
* **opex_per_energy** (*optional, default=0, [CHF/(ec*m)], per-year*): Operation & maintenance cost per amount of transported energy and length for this technology.

**Network technology emissions paramaeters**

* **emissions** (*optional, default={}*): Dictionary with emission parameters for the :ref:`network model <network_model>`.
* **co2_per_cap** (*optional, default=0, [kg/((ec/h)*m)], per-year*): Embodied CO2 that arises per length and per amount of newly installed capacity for this technology.
* **co2_per_energy** (*optional, default=0, [kg/(ec*m)], per-year*): Embodied CO2 that arises per length and per amount of transported energy for this technology.


.. _ecs_yaml:

ecs.yaml
---------

.. literalinclude:: model_inputs/basic/ecs.yaml
    :language: ruby
    :caption: Model *ecs.yaml* file

**Input EC groups**:

* **in_ec_groups** (*optional, default=[]*): Group of ECs which can be used to define a conversion technology group of the same size. One conversion technology will be created for every member of the EC group, and this technology will have this EC as input. In the above example, the technology with id *X3* has the EC group *EG1* as an input. Since this EC group contains the ECs *E1* and *E2*, ehubX will create two technologies named *X3_E1* and *X3_E2* which have the input ECs *E1* and *E2*, respectively. All other parameters of these technologies are taken from the yaml node of *X3*. For the specification of hub-dependent technology parameters in :ref:`hubs.yaml <hubs_yaml>`, these have be specified for the actual technologies *X3_E1* and *X3_E2*. Adding a block for *X3* there will not have any effect.
* **ec_group_id** (*mandatory*): EC group id.
* **ecs** (*mandatory*): List of EC ids in the EC group. Must have at least one entry.

**ECs**

* **ecs** (*optional, default=[]*): Identifiable list of EC ids.
* **ec_id** (*mandatory*): EC id.
* **unit** (*mandatory*): Unit of the ec. Must either be a mass unit or an energy unit.
* **is_energy** (*optional, default=True*): Whether or not this is a "real" energy carrier, i.e.; measured in energy and power units. This parameter is relevant for the :ref:`self-sufficiency model<self_sufficiency_model>`.
* **imp_exp_type** (*optional, default=none*): Specification whether import and export of this ec works as as cross-border, internal, or whether it remains unspecified. This setting is relevant for the :ref:`self-sufficiency model<self_sufficiency_model>`. Acceptable values are "cross" (cross-border), "internal" (internal) or "none" (unspecified).
* **heur_max** (*optional, default=None, [ec/h]*): Heuristic maximum value per timestep for all streams flowing into or out of a balancing node for this ec. This limit will only be applied if no other, more specific limits are available.
* **heur_sum_max** (*optional, default=None, [ec]*): Heuristic maximum value for all streams (summed over all timesteps) flowing into or out of a balancing node for this ec. This limit will only be applied if no other, more specific limits are available.


.. _imports_yaml:

imports.yaml
-------------

.. literalinclude:: model_inputs/basic/imports.yaml
    :language: ruby
    :caption: Model *imports.yaml* file

This file contains parameters for the :ref:`import model <import_model>`.

* **stages** (*mandatory*): Stage ids for which import data is set in this entry.
* **hubs** (*mandatory*): Hub ids for which import data is set in this entry.
* **ecs** (*mandatory*): EC ids for which import data is set in this entry.
* **price** (*optional, default=0, [CHF/ec], per-ts*): Price for imported energy per timestep.
* **min** (*optional, default=0, [ec/h], per-ts*): Minimal amount of imported energy per timestep.
* **max** (*optional*, *default=* :math:`\infty`, *[ec/h], per-ts*): Maximal amount of imported energy per timestep.
* **co2** (*optional, default=0, [kg/ec], per-ts*): Embodied CO2 that arises per amount of imported energy per timestep.
* **sum_min** (*optional, default=0, [ec]*): Minimal value for the summed-up imports across the time horizon.
* **sum_max** (*optional*, *default=* :math:`\infty`, *[ec]*): Maximal value for the summed-up imports across the time horizon.
* **profile_path** (*optional, default=None, file*): File path (relative to imports.yaml) of a time series file with time-specific data for the time-dependent import parameters above. It has to contain the following headers:
  * *stage_id*: Stage id, only the currently active stage id is parsed.
  * *hub_id*: Hub id, only the currently active hub id is parsed.
  * *ec_id*: EC id, only the currently active EC id is parsed.
  * *profile_key*: Name of parameter for which time-dependent data is being defined. Only *price*, *min*, *max* and *co2* are parsed.

.. literalinclude:: model_inputs/basic/profiles/import_profiles.csv
    :language: ruby
    :caption: *import_profiles.csv*: Time series file for import profiles.


.. _exports_yaml:

exports.yaml
-------------

The exports file has the exact same syntax and scope as the :ref:`imports.yaml <imports_yaml>` file. It contains data for the :ref:`export model <export_model>`.


.. _demands_yaml:

demands.yaml
-------------

.. literalinclude:: model_inputs/basic/demands.yaml
    :language: ruby
    :caption: Model *demands.yaml* file

**Demand parameters**

* **demands** (*optional, default={}*): Identifiable list of demands that contain data for the :ref:`demand model <demand_model>`. Each demand encompasses a set of (stage, hub, EC) tuples for which demand values are defined. If such a tuple occurs in multiple demands, the values are summed up to calculate the actual demand that is used in the model.
* **demand_id** (*mandatory*): Demand id.
* **profile_path** (*mandatory, file*): File path (relative to demands.yaml) of a time series file with time-specific data for the demand values. It has to contain the following headers:
  * *stage_id*: Stage id.
  * *hub_id*: Hub id.
  * *ec_id*: EC id.

.. literalinclude:: model_inputs/basic/profiles/demand_profiles.csv
    :language: ruby
    :caption: *demand_profiles.csv*: Time series file for demand profiles.

**Load shedding parameters**

* **load_shedding** (*optional, default={}*): Dictionary with parameters for the :ref:`load shifting model <loadshedding_model>`.
* **stages** (*mandatory*): List of stage ids for this load shedding entry. Can also be a single stage id.
* **hubs** (*mandatory*): List of hub ids for this load shedding entry. Can also be a single hub id.
* **ecs** (*mandatory*): List of EC ids for this load shedding entry. Can also be a single EC id.
* **enabled** (*optional, default=None*): Overwrites *enabled (preset)*.
* **max_abs** (*optional, default=None, [ec/h], per-ts*): Maximal absolute amount of demand that can be shed in this section. This parameter and *max_rel* impose upper bounds on how much the demand energy can be reduced, both of which will be respected by the model.
* **max_rel** (*optional, default=None, [-], per-ts*): Maximal portion of demand that can be shed in this section. This parameter and *max_abs* impose upper bounds on how much the demand energy can be reduced, both of which will be respected by the model.
* **energy_cost** (*optional, default=None, [CHF/ec], per-ts*): Penalization cost per amount of energy that is shed in this section, per timestep.
* **profile_path** (*optional, default=None, file*): File path (relative to demands.yaml) of a time series file with time-specific data for the time-dependent parameters of this manual section above. It has to contain the following headers:

  * *stage_id*: Stage id, only the stages occuring in *stages* above are parsed.
  * *hub_id*: Hub id, only the hubs occuring in *hubs* above are parsed.
  * *ec_id*: EC id, only the stages occuring in *ecs* above are parsed.
  * *profile_key*: Name of parameter for which time-dependent data is being defined. Only *max_abs*, *max_rel* and *energy_cost* are parsed.

.. literalinclude:: model_inputs/basic/profiles/loadshedding_profiles.csv
    :language: ruby
    :caption: *loadshedding_profiles.csv*: Time series file for load shedding profiles.


**Load shifting parameters**

* **load_shifting** (*optional, default={}*): Identifiable list with parameters for the :ref:`load shifting model <loadshifting_model>`.
* **load_shift_id** (*mandatory*): Load shift id.
* **stages** (*mandatory*): List of stage ids for this load shifting element. Can also be a single stage id.
* **hubs** (*mandatory*): List of hub ids for this load shifting element. Can also be a single hub id.
* **ecs** (*mandatory*): List of EC ids for this load shifting element. Can also be a single EC id.
* **interval_length** (*mandatory, [-]*): Number of timesteps that are included in the load shift interval.
* **capex_per_cap** (*optional, default=0, [CHF/ec]*): CAPEX cost for load shifting capacity installation.
* **cap_min** (*optional, default=0, [ec]*): Minimal amount of load shifting capacity that has to be available for this load shift element.
* **cap_max** (*optional*, *default=* :math:`\infty`, *[ec]*): Maximal amount of load shifting capacity that is allowed for this load shift element.
* **cap_init** (*optional, default=0, [ec]*): Initial amount of load shifting capacity that is available for this load shift element.
* **max_above_abs** (*optional*, *default=* :math:`\infty`, *[ec/h], per-ts*): Maximal amount of load shifting that can occur above the demand curve. This parameter and *max_above_rel* impose upper bounds how much the supplied energy is allowed to exceed the demand curve, both of which will be respected by the model.
* **max_above_rel** (*optional*, *default=* :math:`\infty`, *[-], per-ts*): Maximal amount of load shifting that can occur above the demand curve, relative to the demand curve itself. A value of *max_above_rel=0* means that no energy beyond the demand is allowed to be delivered. A value of *max_above_rel=1* means that twice the value of the demand curve is allowed to be delivered. This parameter and *max_above_abs* impose upper bounds on how much the supplied energy is allowed to exceed the demand curve, both of which will be respected by the model.
* **max_below_abs** (*optional*, *default=* :math:`\infty`, *[ec/h], per-ts*): Maximal amount of load shifting that can occur below the demand curve. This parameter and *max_below_rel* impose upper bounds on how much of the demand energy can be withheld by the system, both of which will be respected by the model.
* **max_below_rel** (*optional, default=1, [-], per-ts*): Maximal amount of load shifting that can occur below the demand curve, relative to the demand curve itself. A value of *max_below_rel=0* means that no part of the demand energy is allowed to be withheld. A value of *max_above_rel=1* means that all of the demand energy can be withheld. This parameter and *max_below_abs* impose upper bounds how much of the demand energy can be withheld, both of which will be respected by the model.
* **peak_cost_above** (*optional, default=0, [CHF/(ec/h)]*): Cost for the largest supply excess above the demand curve on the time horizon.
* **peak_cost_below** (*optional, default=0, [CHF/(ec/h)]*): Cost for the largest amount of withheld demand energy on the time horizon.
* **energy_cost_above** (*optional, default=0, [CHF/ec], per-ts*): Penalization cost per amount of excess energy beyond the demand curve, per timestep.
* **energy_cost_below** (*optional, default=0, [CHF/ec], per-ts*): Penalization cost per amount of energy withheld from the demand curve, per timestep.
* **fix_cost** (*optional, default=0, [CHF/h], per-ts*): Fixed cost that arises per timestep when any amount of load shifting (either over or under the demand curve) occurs. *Be aware*: For each load shift element where this parameter is set, one binary variable will be added to the MILP model for each time step. This will drastically increase the complexity and solving speed of the model, and should only be used for comparably small systems.
* **profile_path** (*optional, default=None, file*): File path (relative to demands.yaml) of a time series file with time-specific data for the time-dependent parameters of this load shift element. It has to contain the following headers:

  * *loadshift_id*: Load shift id, only the current load shift id will be parsed.
  * *profile_key*: Name of parameter for which time-dependent data is being defined. Only *max_above_abs*, *max_above_rel*, *max_below_abs*, *max_below_rel*, *energy_cost_above* and *energy_cost_below* are parsed.

.. literalinclude:: model_inputs/basic/profiles/loadshifting_profiles.csv
    :language: ruby
    :caption: *loadshifting_profiles.csv*: Time series file for load shifting profiles.


.. _solar_areas_csv:

solar_areas.csv
----------------

.. literalinclude:: model_inputs/renewables/solar_areas.csv
    :language: ruby
    :caption: *solar_areas.csv*: Available solar areas per stage, hub and EC.

This file contains the amount of available area [m^2] that can be used for the installation of solar technologies. It is required by the :ref:`solar model <solar_model>` and needs to contain the headers

* *stage_id*: Stage id.
* *hub_id*: Hub id.

Furthermore, each main row contains the solar area values for a specific energy carrier.


.. _solar_irradiation_csv:

solar_irradiation.csv
----------------------

.. literalinclude:: model_inputs/renewables/solar_irradiation.csv
    :language: ruby
    :caption: *solar_irradiation.csv*: Solar irradiation timeseries.

This file contains time series for solar irradiation [(ec/h)/m^2] which are required parameters for the :ref:`solar model <solar_model>`. It needs to contain the headers

* *stage_id*: Stage id.
* *ec_id*: EC id.
