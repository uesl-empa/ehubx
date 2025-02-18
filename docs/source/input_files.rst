.. _input_files:

Input files
============

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
            |-- wind_areas.csv
            |-- wind_velocity.csv


Parameter legend
-----------------

* **per-year**: Whether this parameter can be specified as year-dependent (see :ref:`parameter_types`)
* **per-ts**: Whether this parameter can be specified as a timeseries (see :ref:`parameter_types`). This will happen by specifying a path to a time series file, and the specific structure is dependent on the parameter itself.
* **file**: File in which this parameter is specified.


.. _stages_yaml:

stages.yaml
------------

.. literalinclude:: model_inputs/basic/stages.yaml
    :language: ruby
    :caption: Model *stages.yaml* file

**System parameters**:

* **system_params** (*mandatory*): Dictionary of system-wide parameters
* **interest_rate_def** (*mandatory, [1]*): Default interest rate used across the system when no other rate is specified.
* **trl_threshold** (*optional, default=0, [1]*): Technology readiness level (TRL) threshold value above which technologies can be installed and used.
* **num_times_horizon** (*mandatory, [1]*): Number of time steps in the time horizon.
* **autarky_calculation_method** (*optional, default="none"*): Method how the system's autarky value should be calculated. Can be "none" (autarky is not calcualted), "quadratic" (autarky value is calculated using its quadratic definition), or "linearized" (autarky value is calculated using a triangulation-based discretization of the expected domain for internal imports and cross-imports).
* **autarky_min** (*optional, [1], default=0*): Minimal value for the overall system autarky.
* **autarky_max** (*optional, [1], default=1*): Maximal value for the overall system autarky.

**Stages**:

* **stages** (*optional, default=[]*): Identifiable list of stages
* **stage_id** (*mandatory*): Stage id
* **start_year** (*mandatory, [1]*): First year of the stage. This year is used to interpolate year-dependent parameters (see :ref:`parameter_types`). Among the stages, each start year must be unique. The stages do not have to be defined in order of their start year.
* **co2_price** (*optional, default=0, [CHF/kg]*): Price for CO2 emissions.
* **co2_min** (*optional, default=0, [kg]*): Minimal amount of CO2 emissions in this stage.
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

* **tech_params** (*optional, default={}*) Dictionary with parameters for the :ref:`tech_model`.
* **age_init** (*optional, default=0, [a]*): Age of preinstalled technology at this hub.
* **cap_init** (*optional, default=0, [CAP]*): Capacity amount of preinstalled technology at this hub.
* **cap_min** (*optional, default=0, [CAP], per-year*): Minimal amount of installed capacity at this hub.
* **cap_max** (*optional*, *default=* :math:`\infty`, *[CAP], per-year*): Maximal amount of installed capacity at this hub.
* **last_inst_year** (*optional*, *default=* :math:`\infty`, *[1]*): Last year where installation of this technology is allowed at this hub.

**Hub-speficic storage parameters**:

* **storage_params** (*optional, default={}*) Dictionary with parameters for the :ref:`storage model<storage_model>`.
* **soc_init** (*optional*, *default=* :math:`\infty`, *[1]*): Initial state of charge at the beginning of each stage's time horizon, as a value between 0 and 1, relative to the total installed storage capacity. Alternatively, setting this value to :math:`\infty` lets the optimizer choose it without any restriction. Due to the periodicity constraint (see :ref:`storage model<storage_model>`), the initial state of charge will also be the stage of charge at the end of the time horizon.

**Hub-specific conversion parameters**:

* **conversion_params** (*optional, default={}*) Dictionary with parameters for the :ref:`conversion model<conversion_model>`.
* **out_sum_min** (*optional, default=0, [kWh], per-year*): Minimal value for the summed-up output of the conversion technology's main output carrier across the time horizon.
* **out_sum_max** (*optional*, *default=* :math:`\infty`, *[kWh], per-year*): Maximal value for the summed-up output of the conversion technology's main output carrier across the time horizon.
* **availability** (*optional, default=1, [1], per-ts*): Multiplier for the conversion technology's availability to output energy. An availability of 1 means that the technology is able to operate at full capacity, an availability of 0 means that it is not able to produce any output.
* **profile_path** (*optional, default=None, file*): File path (relative to hubs.yaml) of a time series file with time-specific data for the time-dependent conversion parameters above. It has to contain the following headers:
    * *stage_id*: Stage id
    * *hub_id*: Hub id, only the currently active hub is parsed
    * *tech_id*: Technology id, only the currentivly active tech is parsed.
    * *profile_key*: Name of parameter for which time-dependent data is being defined. Only *availability* is parsed.

**Hub-specific Electricity-Based Mobility (EBM) parameters**:

* **ebm_params** (*mandatory for EBM techs*) Dictionary with parameters for the :ref:`EBM model<ebm_model>`.
* **num_vehicles** (*mandatory, [1], per-year*): Number of vehicles in the EBM fleet.
* **soc_init** (*optional, default=* :math:`\infty`, *[1]*): Initial state of charge for the EBM fleet at the beginning of each stage's time horizon, as a value between 0 and 1, relative to the total storage capacity. Alternatively, setting this value to :math:`\infty` lets the optimizer choose it without any restriction. Due to the periodicity constraint (see :ref:`storage model<storage_model>`), the initial state of charge will also be the stage of charge at the end of the time horizon.
* **demand_modifier** (*optional, default=1, [1], per-ts*): Modifier for the EBM demand curve. The values of *demand_nominal* are multiplied with this modifier value to obtain the actual demand.
* **demand_nominal** (*optional, default=0, [kW], per-ts*): Nominal EBM demand of a single vehicle. These values are multiplied with *demand_modifier* to obtain the actual demand of one vehicle. This value is then again multiplied by *num_vehicles* to determine the demand of the entire fleet.
* **availability** (*optional, default=1, [1], per-ts*): Multiplier for the technology's ability to charge and discharge. An availability of 1 means that the entire fleet is available for charging and discharging, an availability of 0 means that the entire fleet is unavailable.
* **profile_path** (*optional, default=None, file*): File path (relative to hubs.yaml) of a time series file with time-specific data for the time-dependent EBM parameters above. It has to contain the following headers:
    * *stage_id*: Stage id.
    * *hub_id*: Hub id, only the currently active hub is parsed.
    * *tech_id*: Technology id, only the currentivly active tech is parsed.
    * *profile_key*: Name of parameter for which time-dependent data is gathered. Only *demand_nominal* and *availability* are parsed.

**Hub-specific heat pump parameters**:

* **heatpump_params** (*mandatory for heat pump techs*): Dictionary with parameters for the :ref:`heat pump model<heatpump_model>`.
* **cop** (*semi-mandatory, [1], per-ts*): Coefficient of performance for heat pump (see :ref:`heat pump model<heatpump_model>`). Either this parameter or *temp_heat_in* and *temp_heat_out* have to be specified.
* **temp_heat_in** (*semi-mandatory, [°C], per-ts*): Temperature in Celcius of heating mode heat intake (i.e.; evaporator inlet temperature). Needs to be specified if *cop* is not specified to calculate the COP.
* **temp_heat_out** (*semi-mandatory, [°C], per-ts*): Temperature in Celcius of heating mode heat outlet (i.e.; condenser outlet temperature). Needs to be specified if *cop* is not specified to calculate the COP.
* **profile_path** (*optional, default=None, file*): File path (relative to hubs.yaml) of a time series file with time-specific data for the time-dependent heat pump parameters above. It has to contain the following headers:
    * *stage_id*: Stage id.
    * *hub_id*: Hub id, only the currently active hub is parsed.
    * *tech_id*: Technology id, only the currentivly active tech is parsed.
    * *profile_key*: Name of parameter for which time-dependent data is gathered. Only *cop*, *temp_heat_in* and *temp_heat_out* are parsed.

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
* **cap_init** (*optional, default=0, [kW]*): Capacity amount of preinstalled network technology on this link.

**Link-specific EC parameters**

* **ec_params** (*optional, default={}*): Dictionary with link-specific EC parameters for the :ref:`network model<network_model>`.
* **ec_id** (*mandatory*): Id of EC. Must be part of this link's *ec_ids*.
* **cap_min** (*optional, default=0, [kW], per-year*): Minimal amount of cummulative capacity on this link of network techs that can transport this EC.
* **cap_max** (*optional*, *default=* :math:`\infty`, *[kW], per-year*): Maximal amount of cummulative capacity on this link of network techs that can transport this EC.
* **sum_min_forward** (*optional, default=0, [kWh], per-year*): Minimal amount of energy for this EC that is transported along this link from the start hub to the end hub.
* **sum_min_backward** (*optional, default=0, [kWh], per-year*): Minimal amount of energy for this EC that is transported along this link from the end hub to the start hub. This parameter is only taken into consideration if the link is *bidirectional*.
* **sum_max_forward** (*optional*, *default=* :math:`\infty`, *[kWh], per-year*): Maximal amount of energy for this EC that is transported along this link from the start hub to the end hub.
* **sum_max_backward** (*optional*, *default=* :math:`\infty`, *[kWh], per-year*): Maximal amount of energy for this EC that is transported along this link from the end hub to the start hub. This parameter is only taken into consideration if the link is *bidirectional*.
* **availability** (*optional, default=1, [1], per-ts*): Multiplier for all network technology's ability on this link to transmit energy. An availability of 1 means that each technology is able to operate at full capacity, an availability of 0 means that none is not able to transmit anything.
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
    *  :code:`storage` (:ref:`storage_model`),
    *  :code:`conversion` (:ref:`conversion_model`),
    *  :code:`solar` (:ref:`solar_model`)
    *  :code:`wind` (:ref:`wind_model`)
    *  :code:`ebm` (:ref:`ebm_model`),
    *  :code:`ates` (:ref:`ates_model`) and
    *  :code:`heatpump` (:ref:`heatpump_model`)..

**Technology parameters**:

* **tech_params** (*optional, default={}*) Dictionary with parameters for the :ref:`tech_model`.
* **lifetime** (*mandatory, [a]*): Lifetime of technology from installation to EOL.
* **unit_cap_min** (*optional, default=0, [CAP], per-year*): Minimal amount of capacity that has to be installed if any installation takes place (so installed capacity will either be 0 or at least this amount).
* **trl** (*optional, default=* :math:`\infty`, *, [1], per-year*): Technology Readiness Level (TRL) for the technology. Only technologies with a TRL above the threshold value specified in :ref:`stages_yaml` can be installed.

**Technology cost parameters**:

* **costs** (*mandatory*): Dictionary with cost parameters for the :ref:`tech_model` and the :ref:`conversion_model`.
* **interest_rate** (*optional, default=None, [1]*): Interest rate for this technology. If none is specified, the default interest rate defined in :ref:`stages_yaml` will be used.
* **one_time_capex** (*optional, default=0, [CHF], per-year*): Fixed CAPEX cost that occurs if any amount of capacity is installed for this technology.
* **capex_per_cap** (*optional, default=0, [CHF/CAP], per-year*): CAPEX cost per amount of installed capacity for this technology.
* **one_time_opex** (*optional, default=0, [CHF], per-year*): Operation & maintenance cost that occurs if any amount of this technology is used during the time horizon.
* **opex_per_cap** (*optional, default=0, [CHF/CAP], per-year*): Operation & maintenance cost per amount of installed capacity for this technology.
* **opex_per_energy** (*optional, default=0, [CHF/kWh], per-year*): Operation & maintenance cost for conversion technologies per amount of output of the conversion technology's main output carrier (see :ref:`conversion model<conversion_model>` for more details)

**Technology emission parameters**:

* **emissions** (*optional, default={}*): Dictionary with emission parameters for the :ref:`tech_model`.
* **co2_per_cap** (*optional, default=0, [kg/CAP], per-year*): Embodied CO2 that arises per amount of newly installed capacity for this technology.

**Storage parameters**:

* **storage_params** (*mandatory for storage techs*): Dictionary with parameters for the :ref:`storage_model`.
* **ec** (*mandatory for storage techs*): Id of EC that is storable in this technology. The value must be an id which is defined in :ref:`ecs_yaml`.
* **in_eff** (*optional, default=1, [1], per-year*): Efficiency of storage input, i.e.; percentage of the charging energy that makes it into the storage technology.
* **out_eff** (*optional, default=1, [1], per-year*): Efficiency of output, i.e.; percentage of the energy that can be used at the end of the discharging process.
* **charge_max** (*optional*, *default=1, [1/h], per-year*): Maximal relative charging power per installed capacity.
* **discharge_max** (*optional*, *default=1, [1/h], per-year*): Maximal relative discharging power per installed capacity.
* **soc_min** (*optional, default=0, [1], per-year*): Minimal stage of charge (fraction of total storage capacity) that is allowed in the storage technology.
* **soc_max** (*optional, default=1, [1], per-year*): Maximal stage of charge (fraction of total storage capacity) that is allowed in the storage technology.
* **standby_loss** (*optional, default=0, [1/h], per-year*): Fraction of stored energy that is lost per timestep independent of other storage operations.

**Conversion parameters**:

* **conversion_params** (*mandatory for conversion techs*): Dictionary with parameters for the :ref:`conversion_model`.
* **in_ecs** (*mandatory for conversion techs*): Identifiable list that defines the composition of conversion inputs.
* **in_id** (*mandatory for conversion techs*): Id of input EC or input EC group.
* **in_part** (*mandatory for conversion techs, [1], per-year*): Input part of the conversion technology's total input energy that consists of the above ec. The relation between all in_parts defines the relation between all input flows into the conversion technology (cf. :ref:`conversion_model`)
* **main_in_ec** (*mandatory for conversion techs with more than one input ec, default=e for conversion techs with a single in_ec e*): Id of input ec that is desgignated the *main input ec*.
* **out_ecs** (*mandatory for conversion techs*): Identifiable list that defines the efficiency values of the conversion technology's energy output.
* **ec_id** (*mandatory for conversion techs*): Id of output ec.
* **out_eff** (*mandatory for conversion techs, [1], per-year or per-ts*): This efficiency value describes the quotient between this output ec's energy output and the main input ec's energy input. It can be given as a year-dependent parameter. Alternatively, it can be given by a relative path to a time series file. This csv file must have the three headers: stage, tech and ec.
* **main_out_ec** (*mandatory for conversion techs with more than one output ec, default=e, for conversion techs with a single out_ec e*): Id of output ec that is designated the *main output ec*.

.. literalinclude:: model_inputs/basic/profiles/efficiency_profiles.csv
    :language: ruby
    :caption: *efficiency_profiles.csv*: Model output efficiency file for conversion technologies


**Solar parameters**

* **solar_params** (*optional, default={}*): Dictionary with parameters for the :ref:`solar_model`.
* **curtail_max_rel** (*optional, default=1, [1], per-year*): Fraction of solar power that can be curtailed. A value of 0 means that all power has to be used while a value of 1 indicates that any part of the energy can be curtailed.

**Wind parameters**

* **wind_params** (*mandatory for wind techs*): Dictionary with parameters for the :ref:`wind_model`.
* **turbine_footprint** (*mandatory for wind techs, [*:math:`m^2` ] *, per-year*): TBD
* **rotor_area** (*mandatory for wind techs, [*:math:`m^2` ] *, per-year*): TBD
* **velo_cut_in** (*mandatory for wind techs, [m/s], per-year*): TBD
* **velo_nominal** (*mandatory for wind techs, [m/s], per-year*): TBD
* **velo_cut_off** (*mandatory for wind techs, [m/s], per-year*): TBD
* **curtail_max_rel** (*optional, default=1, [1], per-year*): Fraction of wind power that can be curtailed. A value of 0 means that all power has to be used while a value of 1 indicates that any part of the energy can be curtailed.

**Electricity-Based Mobility (EBM) parameters**

* **ebm_params** (*mandatory for EBM techs*): Dictionary with parameters for the :ref:`EBM model<ebm_model>`.
* **ec** (*mandatory for EBM techs*): Id of the ec that powers EBM vehicles.
* **storage_cap** (*mandatory, [kWh], per-year*): Storage capacity of a single EBM vehicle.
* **in_eff** (*optional, default=1, [1], per-year*): Efficiency of storage input, i.e.; percentage of the charging energy that makes it into the EBM technology.
* **out_eff** (*optional, default=1, [1], per-year*): Efficiency of output, i.e.; percentage of the energy that can be used at the end of the discharging process.
* **standby_loss** (*optional, default=0, [1], per-year*): Fraction of stored energy that is lost per timestep independent of other storage operations.
* **soc_min** (*optional, default=0, [1], per-year*): Minimal stage of charge (fraction of the total storage capacity) that is allowed in the EBM technology.
* **soc_max** (*optional, default=1, [1], per-year*): Maximal stage of charge (fraction of total storage capacity) that is allowed in the EBM technology.
* **charge_max** (*optional*, *default=* :math:`\infty`, *[kW], per-year*): Maximal charging power of a single EBM vehicle.
* **discharge_max** (*optional*, *default=* :math:`\infty`, *[kW], per-year*): Maximal discharging power of a single EBM vehicle.
* **discharge_controllability** (*optional, default=1, [1], per-year*): Discharge controllability of the EBM fleet. This is a heuristic factor that dampens the maximal discharge speed of the EBM fleet. A discharge control of 1 means that the available (see :ref:`hubs_yaml` for the EBM availability parameter) portion of the fleet can be discharged at its maximal discharging power. A discharge control of 0 means that discharging is impossible.

**Coupling parameters**

* **coupling_params:** (*mandatory for coupled techs*): Dictionary with parameters for coupling (see :ref:`tech model<tech_model>`).
* **main_tech_id** (*mandatory*): Id of this tech's main tech.
* **cap_factor** (*mandatory*): Fraction of this tech's capacity in relation to the main tech's capacity.

**Heat pump parameters**

* **heatpump_params:** (*mandatory for heat pump techs*): Dictionary with parameters for heat pumps (see :ref:`heat pump model <heatpump_model>`).
* **ecs** (*mandatory*): Dictionary with energy carriers for the heat pump.
* **elec** (*mandatory*): Ec id of the heat pump's electricity ec.
* **heat_in** (*mandatory*): Ec id of the heat pump's input ec in heating mode.
* **heat_out** (*mandatory*): Ec id of the heat pump's output ec in heating mode.
* **cool_in** (*mandatory*): Ec id of the heat pump's input ec in cooling mode.
* **cool_out** (*mandatory*): Ec id of the heat pump's output ec in cooling mode.
* **cop_factor** (*optional, default=0.5, [1], per-year*): Parameter used to calculate heat pump COP from Carnot efficiency. Used together with temperatures if *cop* is not directly specified in :ref:`hubs_yaml`.


.. _network_techs_yaml:

network_techs.yaml
-------------------

.. literalinclude:: model_inputs/network/network_techs.yaml
    :language: ruby
    :caption: Model *network_techs.yaml* file

**Network technology parameters**

* **net_techs** (*optional, default={}*): Dictionary with network technology parameters for the :ref:`network_model`.
* **net_tech_id** (*mandatory*): Network technology id.
* **ec** (*mandatory*): ID of EC that is being transported with this technology.
* **lifetime_years** (*mandatory, [a]*): Lifetime of technology from installation to EOL.
* **trl** (*optional, default=* :math:`\infty`, *[1], per-year*): Technology Readiness Level (TRL) for the network technology. Only technologies with a TRL above the threshold value specified in :ref:`stages_yaml` can be installed.
* **unit_cap_min**: (*optional, default=0, [kW], per-year*): Minimal amount of capacity that has to be installed if any installation takes place (so installed capacity will either be 0 or at least this amount).
* **trans_loss** (*optional, default=0, [1/m], per-year*): Fraction of input transmission energy that is lost in the transmission process per unit of link length. A *trans_loss* value of 0 means that no energy is lost in the transmission process. A *trans_loss* value of 1 means that all energy is lost on any unit of link length.

**Network technology cost parameters**

* **costs** (*mandatory*): Dictionary with cost parameters for the :ref:`network_model`.
* **interest_rate** (*optional, default=None, [1]*): Interest rate for this network technology. If none is specified, the default interest rate defined in :ref:`stages_yaml` will be used.
* **one_time_capex** (*optional, default=0, [CHF/m], per-year*): Fixed CAPEX cost per length that occurs if any amount of capacity is installed for this network technology.
* **capex_per_cap** (*optional, default=0, [CHF/kW/m], per-year*): CAPEX cost per amount of installed capacity and length for this network technology.
* **one_time_opex** (*optional, default=0, [CHF/m], per-year*): Operation & maintenance cost per length that occurs if any amount of this network technology is used during the time horizon.
* **opex_per_cap** (*optional, default=0, [CHF/kW/m], per-year*): Operation & maintenance cost per amount of installed capacity and length for this technology.
* **opex_per_energy** (*optional, default=0, [CHF/kWh/m], per-year*): Operation & maintenance cost per amount of transported energy and length for this technology.

**Network technology emissions paramaeters**

* **emissions** (*optional, default={}*): Dictionary with emission parameters for the :ref:`network_model`.
* **co2_per_cap** (*optional, default=0, [kg/kW/m], per-year*): Embodied CO2 that arises per length and per amount of newly installed capacity for this technology.
* **co2_per_energy** (*optional, default=0, [kg/kWh/m], per-year*): Embodied CO2 that arises per length and per amount of transported energy for this technology.


.. _ecs_yaml:

ecs.yaml
---------

.. literalinclude:: model_inputs/basic/ecs.yaml
    :language: ruby
    :caption: Model *ecs.yaml* file

**Input EC groups**:

* **in_ec_groups** (*optional, default=[]*): Group of ECs which can be used to define a conversion technology group of the same size. One conversion technology will be created for every member of the EC group, and this technology will have this EC as input. In the above example, the technology with id *X3* has the EC group *EG1* as an input. Since this EC group contains the ECs *E1* and *E2*, ehubX will create two technologies named *X3_E1* and *X3_E2* which have the input ECs *E1* and *E2*, respectively. All other parameters of these technologies are taken from the yaml node of *X3*. For the specification of hub-dependent technology parameters in :ref:`hubs_yaml`, these have be specified for the actual technologies *X3_E1* and *X3_E2*. Adding a block for *X3* there will not have any effect.
* **ec_group_id** (*mandatory*): EC group id.
* **ecs** (*mandatory*): List of EC ids in the EC group. Must have at least one entry.

**Windparks**

* **windparks** (*optional, default=[]*): Identifiable list of windpark ids.
* **windpark_id** (*mandatory*): Windpark id.
* **ecs** (*mandatory*): List of EC ids in the windpark. Must have at least one entry.

**ECs**

* **ecs** (*optional, default=[]*): Identifiable list of EC ids.
* **ec_id** (*mandatory*): EC id.
* **is_energy** (*optional, default=True*): Whether or not this is a "real" energy carrier, i.e.; measured in energy and power units. This parameter is relevant for the :ref:`autarky model<autarky_model>`.
* **imp_exp_type** (*optional, default=none*): Specification whether import and export of this ec works as as cross-border, internal, or whether it remains unspecified. This setting is relevant for the :ref:`autarky model<autarky_model>`. Acceptable values are "cross" (cross-border), "internal" (internal) or "none" (unspecified).


.. _imports_yaml:

imports.yaml
-------------

.. literalinclude:: model_inputs/basic/imports.yaml
    :language: ruby
    :caption: Model *imports.yaml* file

This file contains parameters for the :ref:`import_model`.

* **stages** (*mandatory*): Stage ids for which import data is set in this entry.
* **hubs** (*mandatory*): Hub ids for which import data is set in this entry.
* **ecs** (*mandatory*): EC ids for which import data is set in this entry.
* **price** (*optional, default=0, [CHF/kW], per-ts*): Price for imported energy per timestep.
* **min** (*optional, default=0, [kW], per-ts*): Minimal amount of imported energy per timestep.
* **max** (*optional*, *default=* :math:`\infty`, *[kW], per-ts*): Maximal amount of imported energy per timestep.
* **co2** (*optional, default=0, [kg/kW], per-ts*): Embodied CO2 that arises per amount of imported energy per timestep.
* **sum_min** (*optional, default=0, [kWh]*): Minimal value for the summed-up imports across the time horizon.
* **sum_max** (*optional*, *default=* :math:`\infty`, *[kWh]*): Maximal value for the summed-up imports across the time horizon.
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

The exports file has the exact same syntax and scope as the :ref:`imports_yaml` file. It contains data for the :ref:`export_model`.


.. _demands_yaml:

demands.yaml
-------------

.. literalinclude:: model_inputs/basic/demands.yaml
    :language: ruby
    :caption: Model *demands.yaml* file

**Demand parameters**

* **demands** (*optional, default={}*): Identifiable list of demands that contain data for the :ref:`demand_model`. Each demand encompasses a set of (stage, hub, EC) tuples for which demand values are defined. If such a tuple occurs in multiple demands, the values are summed up to calculate the actual demand that is used in the model.
* **demand_id** (*mandatory*): Demand id.
* **profile_path** (*mandatory, file*): File path (relative to demands.yaml) of a time series file with time-specific data for the demand values. It has to contain the following headers:
  * *stage_id*: Stage id.
  * *hub_id*: Hub id.
  * *ec_id*: EC id.

.. literalinclude:: model_inputs/basic/profiles/demand_profiles.csv
    :language: ruby
    :caption: *demand_profiles.csv*: Time series file for demand profiles.

**Load shedding parameters**

* **load_shedding** (*optional, default={}*): Dictionary with parameters for the :ref:`loadshedding_model`.
* **preset** (*optional, default={}*): Dictionary with preset parameters for all (stage, hub, EC) tuples which have a demand profile (see the demand parameter section above). Any parameter in this dictionary will be used for for all (stage, hub, EC) demand tuples which do not have a corresponding parameter in the *manual* list that overwrites it.
* **enabled (preset)** (*optional, default=True*): Boolean value indicating whether load shedding will be enabled or not.
* **max_abs (preset)** (*optional*, *default=* :math:`\infty`, *[kW]*): Maximal amount of absolute demand energy that can be shed per timestep. This parameter and *max_rel* impose upper bounds on load shedding, both of which will be respected by the model.
* **max_rel (preset)** (*optional, default=1, [1]*): Maximal fraction of total demand energy that can be shed per timestep. This parameter and *max_abs* impose upper bounds on load shedding, both of which will be respected by the model.
* **energy_cost (preset)** (*optional, default=1e6, [CHF/kW]*): Penalization cost per amount of shedded demand energy per timestep.
* **manual** (*optional, default=[]*): List of manual load shedding dictionaries that can be used to overwrite the default values specified in the *preset* section. This section specifies a set of (stage, hub, EC) tuples for which the manual parameters are set. Each such tuple may only occur in a single manual section.
* **stages** (*mandatory*): List of stage ids for this manual section. Can also be a single stage id.
* **hubs** (*mandatory*): List of hub ids for this manual section. Can also be a single hub id.
* **ecs** (*mandatory*): List of EC ids for this manual section. Can also be a single EC id.
* **enabled (manual)** (*optional, default=None*): Overwrites *enabled (preset)*.
* **max_abs (manual)** (*optional, default=None, [kW], per-ts*): Overwrites *max_abs (preset)*. In this section, the parameter can be time-dependent if given as a time series under *profile_path*.
* **max_rel (manual)** (*optional, default=None, [1], per-ts*): Overwrites *max_rel (preset)*. In this section, the parameter can be time-dependent if given as a time series under *profile_path*.
* **energy_cost (manual)** (*optional, default=None, [CHF/kW], per-ts*): Overwrites *energy_cost (preset)*. In this section, the parameter can be time-dependent if given as a time series under *profile_path*.
* **profile_path** (*optional, default=None, file*): File path (relative to demands.yaml) of a time series file with time-specific data for the time-dependent parameters of this manual section above. It has to contain the following headers:

  * *stage_id*: Stage id, only the stages occuring in *stages* above are parsed.
  * *hub_id*: Hub id, only the hubs occuring in *hubs* above are parsed.
  * *ec_id*: EC id, only the stages occuring in *ecs* above are parsed.
  * *profile_key*: Name of parameter for which time-dependent data is being defined. Only *max_abs*, *max_rel* and *energy_cost* are parsed.

.. literalinclude:: model_inputs/basic/profiles/loadshedding_profiles.csv
    :language: ruby
    :caption: *loadshedding_profiles.csv*: Time series file for load shedding profiles.


**Load shifting parameters**

* **load_shifting** (*optional, default={}*): Identifiable list with parameters for the :ref:`loadshifting_model`.
* **load_shift_id** (*mandatory*): Load shift id.
* **stages** (*mandatory*): List of stage ids for this load shifting element. Can also be a single stage id.
* **hubs** (*mandatory*): List of hub ids for this load shifting element. Can also be a single hub id.
* **ecs** (*mandatory*): List of EC ids for this load shifting element. Can also be a single EC id.
* **interval_length** (*mandatory, [1]*): Number of timesteps that are included in the load shift interval.
* **interval_cap** (*optional, default=* :math:`\infty`, *[kWh], per-year*): Amount of installed load shifting capacity, i.e.; amount of energy that can be used for load shifting purposes in above or below direction on each load shift interval.
* **max_above_abs** (*optional*, *default=* :math:`\infty`, *[kW], per-ts*): Maximal amount of load shifting that can occur above the demand curve. This parameter and *max_above_rel* impose upper bounds how much the supplied energy is allowed to exceed the demand curve, both of which will be respected by the model.
* **max_above_rel** (*optional*, *default=* :math:`\infty`, *[1], per-ts*): Maximal amount of load shifting that can occur above the demand curve, relative to the demand curve itself. A value of *max_above_rel=0* means that no energy beyond the demand is allowed to be delivered. A value of *max_above_rel=1* means that twice the value of the demand curve is allowed to be delivered. This parameter and *max_above_abs* impose upper bounds on how much the supplied energy is allowed to exceed the demand curve, both of which will be respected by the model.
* **max_below_abs** (*optional*, *default=* :math:`\infty`, *[kW], per-ts*): Maximal amount of load shifting that can occur below the demand curve. This parameter and *max_below_rel* impose upper bounds on how much of the demand energy can be withheld by the system, both of which will be respected by the model.
* **max_below_rel** (*optional, default=1, [1], per-ts*): Maximal amount of load shifting that can occur below the demand curve, relative to the demand curve itself. A value of *max_below_rel=0* means that no part of the demand energy is allowed to be withheld. A value of *max_above_rel=1* means that all of the demand energy can be withheld. This parameter and *max_below_abs* impose upper bounds how much of the demand energy can be withheld, both of which will be respected by the model.
* **peak_cost_above** (*optional, default=0, [CHF/kW]*): Cost for the largest supply excess above the demand curve on the time horizon.
* **peak_cost_below** (*optional, default=0, [CHF/kW]*): Cost for the largest amount of withheld demand energy on the time horizon.
* **energy_cost_above** (*optional, default=0, [CHF/kW], per-ts*): Penalization cost per amount of excess energy beyond the demand curve, per timestep.
* **energy_cost_below** (*optional, default=0, [CHF/kW], per-ts*): Penalization cost per amount of energy withheld from the demand curve, per timestep.
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

This file contains the amount of available area [:math:`m^2`] that can be used for the installation of solar technologies. It is required by the :ref:`solar_model` and needs to contain the headers

* *stage_id*: Stage id.
* *hub_id*: Hub id.

Furthermore, each main row contains the solar area values for a specific energy carrier.


.. _solar_irradiation_csv:

solar_irradiation.csv
----------------------

.. literalinclude:: model_inputs/renewables/solar_irradiation.csv
    :language: ruby
    :caption: *solar_irradiation.csv*: Solar irradiation timeseries.

This file contains time series for solar irradiation [kW/:math:`m^2`] which are required parameters for the :ref:`solar_model`. It needs to contain the headers

* *stage_id*: Stage id.
* *ec_id*: EC id.


.. _wind_areas_csv:

wind_areas.csv
---------------

.. literalinclude:: model_inputs/renewables/wind_areas.csv
    :language: ruby
    :caption: *wind_areas.csv*: Available wind areas per stage, hub and windpark.

This file contains the amount of available area [:math:`m^2`] that can be used for the installation of wind technologies. It is required by the :ref:`wind_model` and needs to contain the headers

* *stage_id*: Stage id.
* *hub_id*: Hub id.

Furthermore, each main row contains the solar area values for a specific windpark.


.. _wind_velocity_csv:

wind_velocity.csv
------------------

.. literalinclude:: model_inputs/renewables/wind_velocity.csv
    :language: ruby
    :caption: *wind_velocity.csv*: Wind velocity timeseries.

This file contains time series for wind velocities [m/s] which are required parameters for the :ref:`wind_model`. It needs to contain the headers

* *stage_id*: Stage id.
* *ec_id*: EC id.
