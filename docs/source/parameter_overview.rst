.. only:: latex

   .. raw:: latex

      \begin{landscape}


Parameter overview
===================

This section contains an extensive table listing all input parameters that can be specified in ehubX models. The table provides information on whether a parameter is mandatory or optional, its default value (if applicable), the unit, and whether it can be defined as year-dependent or as a time series. Additionally, the table indicates the specific node paths within the input files where each parameter can be found. Please note the section about unit conventions mentioned at the beginning of the section :ref:`input files <input_files>` which is also relevant for this section.

Legend
-------

* **Name**: Name of parameter (only used within this table)
* **Mandatory**: Whether this parameter has to be set for the model to be built correctly. Non-mandatory parameters usually have a default value. Used symbols are:
    * **✓**: Parameter is mandatory.
    * (**✓**): Parameter is mandatory under some conditions.
    * ✖: Parameter is optional.
* **Default**: Default value for optional parameters
* **Unit**: Unit for the parameter (see :ref:`units <units>`).
* **Per year**: Whether this parameter can be specified as year-dependent (see :ref:`parameter types <parameter_types>`)
    * **✓**: Parameter can be specified as year-dependent.
    * ✖: Parameter cannot be specified as year-dependent.
* **Per ts**: Whether this parameter can be specified as a timeseries (see :ref:`parameter types <parameter_types>`). This will happen by specifying a path to a time series file, and the specific structure is dependent on the parameter itself.
    * **✓**: Parameter can be specified as a time series.
    * ✖: Parameter cannot be specified as a time series.
* **Node path(s)**: Node path(s) (see :ref:`node paths <node_paths>`) within the file where this parameter is specified.
* **File**: File in which this parameter is specified.

Parameter table
----------------


.. only:: latex

   .. raw:: latex

      \begingroup\scriptsize
      \setlength{\tabcolsep}{2pt}%

.. only:: latex

   .. tabularcolumns:: p{0.17\linewidth}p{0.05\linewidth}p{0.06\linewidth}p{0.06\linewidth}p{0.05\linewidth}p{0.05\linewidth}p{0.36\linewidth}p{0.16\linewidth}

.. list-table:: Parameter list
    :header-rows: 1
    :widths: 15 6 10 8 5 5 30 10

    * - Name
      - Mandatory
      - Default
      - Unit
      - Per year
      - Per ts
      - Node path(s)
      - File

    * - **Availability** (ates)
      - ✖
      - 1
      - [-]
      - **✓**
      - **✓**
      - :code:`hubs[ID]/techs[ID]/ates_params/availability`, :code:`hubs[ID]/techs[ID]/ates_params/profile_path`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Availability** (conversion)
      - ✖
      - 1
      - [-]
      - **✓**
      - **✓**
      - :code:`hubs[ID]/techs[ID]/conversion_params/availability`, :code:`hubs[ID]/techs[ID]/conversion_params/profile_path`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Availability** (ebm)
      - ✖
      - 1
      - [-]
      - **✓**
      - **✓**
      - :code:`hubs[ID]/techs[ID]/ebm_params/availability`, :code:`hubs[ID]/techs[ID]/ebm_params/profile_path`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Availability** (heatpump)
      - ✖
      - 1
      - [-]
      - **✓**
      - **✓**
      - :code:`hubs[ID]/techs[ID]/heatpump_params/availability`, :code:`hubs[ID]/techs[ID]/heatpump_params/profile_path`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Availability** (net_links)
      - ✖
      - 1
      - [-]
      - **✓**
      - **✓**
      - :code:`start_hubs[ID]/end_hubs[id]/links[id]/ec_params[id]/availability`, :code:`start_hubs[ID]/end_hubs[id]/links[id]/ec_params[id]/profile_path`
      - :ref:`network_links.yaml<network_links_yaml>`

    * - **Available area** (ates)
      - ✖
      - :math:`\infty`
      - m^2
      - **✓**
      - ✖
      - :code:`hubs[ID]/ates_params/available_area`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Bidirectional** (link)
      - ✖
      - False
      -
      - ✖
      - ✖
      - :code:`start_hubs[ID]/end_hubs[ID]/links[ID]/bidirectional`
      - :ref:`network_links.yaml<network_links_yaml>`

    * - **Capacity factor** (coupling)
      - **✓**
      -
      - CAP_sub/CAP_main
      - ✖
      - ✖
      - :code:`techs[ID]/coupling_params/cap_factor`
      - :ref:`techs.yaml<techs_yaml>`

    * - **CAPEX per capacity** (load_shifting)
      - ✖
      - 0
      - CHF/ec
      - ✖
      - ✖
      - :code:`load_shifting[ID]/capex_per_cap`
      - :ref:`demands.yaml<demands_yaml>`

    * - **CAPEX per capacity** (net_tech)
      - ✖
      - 0
      - CHF/((ec/h)*m)
      - **✓**
      - ✖
      - :code:`net_techs[ID]/costs/capex_per_cap`
      - :ref:`network_techs.yaml<network_techs_yaml>`

    * - **CAPEX per capacity** (tech)
      - ✖
      - 0
      - CHF/CAP
      - **✓**
      - ✖
      - :code:`techs[ID]/costs/capex_per_cap`
      - :ref:`techs.yaml<techs_yaml>`

    * - **CO2** (import/export)
      - ✖
      - 0
      - kg/ec
      - ✖
      - **✓**
      - :code:`stages[ID]/hubs[ID]/ecs[ID]/co2`, :code:`stages[ID]/hubs[ID]/ecs[ID]/profile_path`
      - :ref:`imports.yaml<imports_yaml>`, :ref:`exports.yaml<exports_yaml>`

    * - **CO2 per capacity** (net_tech)
      - ✖
      - 0
      - kg/((ec/h)*m)
      - **✓**
      - ✖
      - :code:`net_techs[ID]/emissions/co2_per_cap`
      - :ref:`network_techs.yaml<network_techs_yaml>`

    * - **CO2 per capacity** (tech)
      - ✖
      - 0
      - kg/CAP
      - **✓**
      - ✖
      - :code:`techs[ID]/emissions/co2_per_cap`
      - :ref:`techs.yaml<techs_yaml>`

    * - **CO2 per transported energy** (net_tech)
      - ✖
      - 0
      - kg/(ec*m)
      - **✓**
      - ✖
      - :code:`net_techs[ID]/emissions/co2_per_energy`
      - :ref:`network_techs.yaml<network_techs_yaml>`

    * - **CO2 max** (stage)
      - ✖
      - :math:`\infty`
      - kg
      - ✖
      - ✖
      - :code:`stages[ID]/co2_max`
      - :ref:`stages.yaml<stages_yaml>`


    * - **CO2 min** (stage)
      - ✖
      - :math:`-\infty`
      - kg
      - ✖
      - ✖
      - :code:`stages[ID]/co2_min`
      - :ref:`stages.yaml<stages_yaml>`

    * - **CO2 price** (stage)
      - ✖
      - 0
      - CHF/kg
      - ✖
      - ✖
      - :code:`stages[ID]/co2_price`
      - :ref:`stages.yaml<stages_yaml>`

    * - **COP** (heatpump)
      - (**✓**)
      -
      - [-]
      - **✓**
      - **✓**
      - :code:`hubs[ID]/techs[ID]/heatpump_params/cop`, :code:`hubs[ID]/techs[ID]/heatpump_params/profile_path`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **COP factor** (heatpump)
      - (**✓**)
      -
      - [-]
      - **✓**
      - X
      - :code:`techs[ID]/heatpump_params/cop_factor`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Darcy velocity** (ates)
      - (**✓**)
      -
      - m/d
      - ✖
      - ✖
      - :code:`hubs[ID]/ates_params/darcy_velocity`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Demand** (demand)
      - ✖
      - 0
      - ec
      - ✖
      - **✓**
      - :code:`demands[ID]/profile_path`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Demand modifier** (ebm)
      - ✖
      - 1
      - [-]
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ebm_params/demand_modifier`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Discharge controllability** (ebm)
      - ✖
      - 1
      - [-]
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ebm_params/discharge_controllability`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Electricity consumption per cooling energy** (ates)
      - **(✓)**
      -
      - [-]
      - ✖
      - ✖
      - :code:`hubs[ID]/techs[ID]/ates_params/elec_per_energy_cool`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Electricity consumption per heating energy** (ates)
      - **(✓)**
      -
      - [-]
      - ✖
      - ✖
      - :code:`hubs[ID]/techs[ID]/ates_params/elec_per_energy_heat`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Enabled** (load_shedding)
      - ✖
      - True
      -
      - ✖
      - ✖
      - :code:`load_shedding/preset/enabled`, :code:`load_shedding/manual[pos]/enabled`
      - :ref:`demands.yaml<demands_yaml>`

    * - **End of cold-to-warm phase** (ates)
      - **✓**
      -
      -
      - ✖
      - ✖
      - :code:`hubs[ID]/ates_params/schedules[ID]/phase_c2w_end_id`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **End of warm-to-cold phase** (ates)
      - **✓**
      -
      -
      - ✖
      - ✖
      - :code:`hubs[ID]/ates_params/schedules[ID]/phase_w2c_end_id`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Energy cost** (load_shedding)
      - ✖
      - 0
      - CHF/ec
      - ✖
      - ✖
      - :code:`load_shedding/preset/energy_cost`, :code:`load_shedding/manual[pos]/energy_cost`, :code:`load_shedding/manual[pos]/profile_path`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Energy cost, above** (load_shifting)
      - ✖
      - 0
      - CHF/ec
      - ✖
      - **✓**
      - :code:`load_shifting[ID]/energy_cost_above`, :code:`load_shifting[ID]/profile_path`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Energy cost, below** (load_shifting)
      - ✖
      - 0
      - CHF/ec
      - ✖
      - **✓**
      - :code:`load_shifting[ID]/energy_cost_below`, :code:`load_shifting[ID]/profile_path`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Fix cost** (load_shifting)
      - ✖
      - 0
      - CHF/h
      - ✖
      - **✓**
      - :code:`load_shifting[ID]/fix_cost`, :code:`load_shifting[ID]/profile_path`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Fluid density** (ates)
      - **✓**
      -
      - kg/m^3
      - ✖
      - ✖
      - :code:`techs[ID]/ates_params`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Fluid specific heat capacity** (ates)
      - **✓**
      -
      - Ws/(kg*K)
      - ✖
      - ✖
      - :code:`techs[ID]/ates_params`
      - :ref:`techs.yaml<techs_yaml>`

    * - **heur_max** (ec)
      - (**✓**)
      -
      - ec/h
      -
      -
      - :code:`ecs[ID]/heur_max`
      - :ref:`ecs.yaml<ecs_yaml>`

    * - **heur_sum_max** (ec)
      - (**✓**)
      -
      - ec
      -
      -
      - :code:`ecs[ID]/heur_sum_max`
      - :ref:`ecs.yaml<ecs_yaml>`

    * - **imp_exp_type** (self-sufficiency)
      - ✖
      - "none"
      -
      - ✖
      - ✖
      - :code:`ecs[ID]/imp_exp_type`
      - :ref:`ecs.yaml<ecs_yaml>`

    * - **Initial age** (net_tech)
      - ✖
      - 0
      - a
      - ✖
      - ✖
      - :code:`start_hubs[ID]/end_hubs[ID]/links[ID]/net_tech_params/age_init`
      - :ref:`network_links.yaml<network_links_yaml>`

    * - **Initial age** (tech)
      - ✖
      - 0
      - a
      - ✖
      - ✖
      - :code:`hubs[ID]/techs[ID]/tech_params/age_init`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Initial capacity** (load_shifting)
      - ✖
      - 0
      - ec
      - ✖
      - ✖
      - :code:`load_shifting[ID]/cap_max`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Initial capacity** (net_tech)
      - ✖
      - 0
      - ec/h
      - ✖
      - ✖
      - :code:`start_hubs[ID]/end_hubs[ID]/links[ID]/net_tech_params/cap_init`
      - :ref:`network_links.yaml<network_links_yaml>`

    * - **Initial capacity** (tech)
      - ✖
      - 0
      - CAP
      - ✖
      - ✖
      - :code:`hubs[ID]/techs[ID]/tech_params/cap_init`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Initial stage of charge** (ebm)
      - ✖
      - :math:`\infty`
      - [-]
      - ✖
      - ✖
      - :code:`hubs[ID]/techs[ID]/ebm_params/soc_init`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Initial stage of charge** (storage)
      - ✖
      - :math:`\infty`
      - [-]
      - ✖
      - ✖
      - :code:`hubs[ID]/techs[ID]/storage_params/soc_init`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Input efficiency** (ebm)
      - ✖
      - 1
      - [-]
      - **✓**
      - ✖
      - :code:`techs[ID]/ebm_params/in_eff`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Input efficiency** (storage)
      - ✖
      - 1
      - [-]
      - **✓**
      - ✖
      - :code:`techs[ID]/storage_params/in_eff`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Input part** (conversion)
      - **✓**
      -
      - ec_in
      - **✓**
      - ✖
      - :code:`techs[ID]/conversion_params/in_ecs[ID]/in_part`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Interest rate default** (system)
      - **✓**
      -
      - [-]
      - ✖
      - ✖
      - :code:`system_params/interest_rate_def`
      - :ref:`stages.yaml<stages_yaml>`

    * - **Interest rate** (net_tech)
      - ✖
      -
      - [-]
      - ✖
      - ✖
      - :code:`net_techs[ID]/costs/interest_rate`
      - :ref:`network_techs.yaml<network_techs_yaml>`

    * - **Interest rate** (tech)
      - ✖
      -
      - [-]
      - ✖
      - ✖
      - :code:`techs[ID]/costs/interest_rate`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Interval length** (load_shifting)
      - **✓**
      -
      - h
      - ✖
      - ✖
      - :code:`load_shifting[ID]/interval_length`
      - :ref:`demands.yaml<demands_yaml>`

    * - **is_energy** (self-sufficiency)
      - ✖
      - True
      -
      - ✖
      - ✖
      - :code:`ecs[ID]/is_energy`
      - :ref:`ecs.yaml<ecs_yaml>`

    * - **Last installation year** (tech)
      - ✖
      - :math:`\infty`
      -
      - ✖
      - ✖
      - :code:`hubs[ID]/techs[ID]/tech_params/last_inst_year`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Length** (link)
      - **✓**
      -
      - m
      - ✖
      - ✖
      - :code:`start_hubs[ID]/end_hubs[ID]/links[ID]/length`
      - :ref:`network_links.yaml<network_links_yaml>`

    * - **Lifetime** (net_tech)
      - **✓**
      -
      - a
      - ✖
      - ✖
      - :code:`net_techs[ID]/lifetime`
      - :ref:`network_techs.yaml<network_techs_yaml>`

    * - **Lifetime** (tech)
      - **✓**
      -
      - a
      - ✖
      - ✖
      - :code:`techs[ID]/tech_params/lifetime`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Main input ec** (conversion)
      - (**✓**)
      -
      -
      - ✖
      - ✖
      - :code:`techs[ID]/conversion_params/main_in_ec`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Main output ec** (conversion)
      - (**✓**)
      -
      -
      - ✖
      - ✖
      - :code:`techs[ID]/conversion_params/main_out_ec`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Main tech id** (coupling)
      - ✓
      -
      -
      - ✖
      - ✖
      - :code:`techs[ID]/coupling_params/main_tech_id`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Max** (import/export)
      - ✖
      - :math:`\infty`
      - ec/h
      - ✖
      - **✓**
      - :code:`stages[ID]/hubs[ID]/ecs[ID]/max`, :code:`stages[ID]/hubs[ID]/ecs[ID]/profile_path`
      - :ref:`imports.yaml<imports_yaml>`, :ref:`exports.yaml<exports_yaml>`

    * - **Maximal self-sufficiency** (self-sufficiency)
      - ✖
      - 1
      - [-]
      -
      -
      - :code:`system_params/self_sufficiency_max`
      - :ref:`stages.yaml<stages_yaml>`

    * - **Maximal capacity** (link)
      - ✖
      - :math:`\infty`
      - ec/h
      - **✓**
      - ✖
      - :code:`start_hubs[ID]/end_hubs[ID]/links[ID]/ec_params/cap_max`
      - :ref:`network_links.yaml<network_links_yaml>`

    * - **Maximal capacity** (load_shifting)
      - ✖
      - :math:`\infty`
      - ec
      - ✖
      - ✖
      - :code:`load_shifting[ID]/cap_max`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Maximal capacity** (tech)
      - ✖
      - :math:`\infty`
      - CAP
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/tech_params/cap_max`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Maximal charging power** (ebm)
      - ✖
      - :math:`\infty`
      - ec/h
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ebm_params/charge_max`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Maximal charging power** (storage)
      - ✖
      - :math:`\infty`
      - 1/h
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/storage_params/charge_max`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Maximal curtailment** (solar)
      - ✖
      - 1
      - [-]
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/solar_params/curtail_max_rel`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Maximal discharging power** (ebm)
      - ✖
      - :math:`\infty`
      - ec/h
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ebm_params/discharge_max`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Maximal discharging power** (storage)
      - ✖
      - :math:`\infty`
      - 1/h
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/storage_params/discharge_max`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Maximal drawdown of aquifer** (ates)
      - (**✓**)
      -
      - m
      - ✖
      - ✖
      - :code:`hubs[ID]/ates_params/max_drawdown`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Maximal total heating over cooling** (ates)
      - ✖
      - :math:`\infty`
      - [-]
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ates_params/schedule_params[ID]/max_heat_over_cool`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Maximal total cooling over heating** (ates)
      - ✖
      - :math:`\infty`
      - [-]
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ates_params/schedule_params[ID]/max_cool_over_heat`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Maximal load shedding, absolute** (load_shedding)
      - ✖
      - :math:`\infty`
      - ec/h
      - ✖
      - ✖
      - :code:`load_shedding/preset/max_abs`, :code:`load_shedding/manual[pos]/max_abs`, :code:`load_shedding/manual[pos]/profile_path`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Maximal load shedding, relative** (load_shedding)
      - ✖
      - 1
      - [-]
      - ✖
      - ✖
      - :code:`load_shedding/preset/max_rel`, :code:`load_shedding/manual[pos]/max_rel`, :code:`load_shedding/manual[pos]/profile_path`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Maximal load shifting, absolute-above** (load_shifting)
      - ✖
      - :math:`\infty`
      - ec/h
      - ✖
      - **✓**
      - :code:`load_shifting[ID]/max_above_abs`, :code:`load_shifting[ID]/profile_path`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Maximal load shifting, absolute-below** (load_shifting)
      - ✖
      - :math:`\infty`
      - ec/h
      - ✖
      - **✓**
      - :code:`load_shifting[ID]/max_below_abs`, :code:`load_shifting[ID]/profile_path`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Maximal load shifting, relative-above** (load_shifting)
      - ✖
      - :math:`\infty`
      - [-]
      - ✖
      - **✓**
      - :code:`load_shifting[ID]/max_above_rel`, :code:`load_shifting[ID]/profile_path`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Maximal load shifting, relative-below** (load_shifting)
      - ✖
      - 1
      - [-]
      - ✖
      - **✓**
      - :code:`load_shifting[ID]/max_below_rel`, :code:`load_shifting[ID]/profile_path`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Maximal number of well pairs** (ates)
      - ✖
      - :math:`\infty`
      -
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[id]/ates_params/schedule_params[ID]/well_pairs_max`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Maximal pumping rate per cold well** (ates)
      - ✖
      -
      - m^3/h
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ates_params/schedule_params[ID]/max_pump_rate_per_cold_well`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Maximal pumping rate per warm well** (ates)
      - ✖
      -
      - m^3/h
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ates_params/schedule_params[ID]/max_pump_rate_per_warm_well`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Maximal stage of charge** (storage)
      - ✖
      - 1
      - [-]
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/storage_params/soc_max`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Maximal summed-up backward transport** (link)
      - ✖
      - :math:`\infty`
      - ec
      - **✓**
      - ✖
      - :code:`start_hubs[ID]/end_hubs[ID]/links[ID]/ec_params/sum_max_backward`
      - :ref:`network_links.yaml<network_links_yaml>`

    * - **Maximal summed-up forward transport** (link)
      - ✖
      - :math:`\infty`
      - ec
      - **✓**
      - ✖
      - :code:`start_hubs[ID]/end_hubs[ID]/links[ID]/ec_params/sum_max_forward`
      - :ref:`network_links.yaml<network_links_yaml>`

    * - **Maximal summed-up imports/exports** (import/export)
      - ✖
      - :math:`\infty`
      - ec
      - ✖
      - ✖
      - :code:`stages[ID]/hubs[ID]/ecs[ID]/sum_max`
      - :ref:`imports.yaml<imports_yaml>`, :ref:`exports.yaml<exports_yaml>`

    * - **Maximal summed-up output** (conversion)
      - ✖
      - :math:`\infty`
      - ec
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/conversion_params/out_sum_max`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Maximal temperature spread for cold wells** (ates)
      - **✓**
      -
      - K
      - ✖
      - ✖
      - :code:`hubs[ID]/ates_params/max_temperature_spread_cold`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Maximal temperature spread for warm wells** (ates)
      - **✓**
      -
      - K
      - ✖
      - ✖
      - :code:`hubs[ID]/ates_params/max_temperature_spread_warm`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Min** (import/export)
      - ✖
      - 0
      - ec/h
      - ✖
      - **✓**
      - :code:`stages[ID]/hubs[ID]/ecs[ID]/min`, :code:`stages[ID]/hubs[ID]/ecs[ID]/profile_path`
      - :ref:`imports.yaml<imports_yaml>`, :ref:`exports.yaml<exports_yaml>`

    * - **Minimal number of well pairs** (ates)
      - ✖
      - 0
      -
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[id]/ates_params/schedule_params[ID]/well_pairs_min`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Minimal summed-up backward transport** (link)
      - ✖
      - :math:`\infty`
      - ec
      - **✓**
      - ✖
      - :code:`start_hubs[ID]/end_hubs[ID]/links[ID]/ec_params/sum_max_backward`
      - :ref:`network_links.yaml<network_links_yaml>`

    * - **Maximal summed-up forward transport** (link)
      - ✖
      - :math:`\infty`
      - ec
      - **✓**
      - ✖
      - :code:`start_hubs[ID]/end_hubs[ID]/links[ID]/ec_params/sum_max_forward`
      - :ref:`network_links.yaml<network_links_yaml>`

    * - **Maximal summed-up imports/exports** (import/export)
      - ✖
      - :math:`\infty`
      - ec
      - ✖
      - ✖
      - :code:`stages[ID]/hubs[ID]/ecs[ID]/sum_max`
      - :ref:`imports.yaml<imports_yaml>`, :ref:`exports.yaml<exports_yaml>`

    * - **Maximal summed-up output** (conversion)
      - ✖
      - :math:`\infty`
      - ec_out_main
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/conversion_params/out_sum_max`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Min** (import/export)
      - ✖
      - 0
      - ec/h
      - ✖
      - **✓**
      - :code:`stages[ID]/hubs[ID]/ecs[ID]/min`, :code:`stages[ID]/hubs[ID]/ecs[ID]/profile_path`
      - :ref:`imports.yaml<imports_yaml>`, :ref:`exports.yaml<exports_yaml>`

    * - **Minimal self-sufficiency** (self-sufficiency)
      - ✖
      - 0
      - [-]
      -
      -
      - :code:`system_params/self_sufficiency_min`
      - :ref:`stages.yaml<stages_yaml>`

    * - **Minimal capacity** (link)
      - ✖
      - 0
      - ec/h
      - **✓**
      - ✖
      - :code:`start_hubs[ID]/end_hubs[ID]/links[ID]/ec_params/cap_min`
      - :ref:`network_links.yaml<network_links_yaml>`

    * - **Minimal capacity** (load_shifting)
      - ✖
      - 0
      - ec
      - ✖
      - ✖
      - :code:`load_shifting[ID]/cap_min`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Minimal capacity** (tech)
      - ✖
      - 0
      - CAP
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/tech_params/cap_min`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Minimal stage of charge** (ebm)
      - ✖
      - 0
      - [-]
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ebm_params/soc_min`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Minimal stage of charge** (storage)
      - ✖
      - 0
      - [-]
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/storage_params/soc_min`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Minimal summed-up backward transport** (link)
      - ✖
      - 0
      - ec
      - **✓**
      - ✖
      - :code:`start_hubs[ID]/end_hubs[ID]/links[ID]/ec_params/sum_min_backward`
      - :ref:`network_links.yaml<network_links_yaml>`

    * - **Minimal summed-up forward transport** (link)
      - ✖
      - 0
      - ec
      - **✓**
      - ✖
      - :code:`start_hubs[ID]/end_hubs[ID]/links[ID]/ec_params/sum_min_forward`
      - :ref:`network_links.yaml<network_links_yaml>`

    * - **Minimal summed-up imports/exports** (import/export)
      - ✖
      - 0
      - ec
      - ✖
      - ✖
      - :code:`stages[ID]/hubs[ID]/ecs[ID]/sum_min`
      - :ref:`imports.yaml<imports_yaml>`, :ref:`exports.yaml<exports_yaml>`

    * - **Minimal summed-up output** (conversion)
      - ✖
      - 0
      - ec_out_main
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/conversion_params/out_sum_min`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Minimal unit capacity** (net_tech)
      - ✖
      - 0
      - ec/h
      - **✓**
      - ✖
      - :code:`net_techs[ID]/unit_cap_min`
      - :ref:`network_techs.yaml<network_techs_yaml>`

    * - **Minimal unit capacity** (tech)
      - ✖
      - 0
      - CAP
      - **✓**
      - ✖
      - :code:`techs[ID]/tech_params/unit_cap_min`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Nominal demand** (ebm)
      - ✖
      - 0
      - ec/h
      - **✓**
      - **✓**
      - :code:`hubs[ID]/techs[ID]/ebm_params/demand_nominal`, :code:`hubs[ID]/techs[ID]/ebm_params/profile_path`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Number of horizon timesteps** (system)
      - **✓**
      -
      -
      - ✖
      - ✖
      - :code:`system_params/num_times_horizon`
      - :ref:`stages.yaml<stages_yaml>`

    * - **Number of vehicles** (ebm)
      - **✓**
      -
      -
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[id]/ebm_params/num_vehicles`
      - :ref:`hubs.yaml <hubs_yaml>`

    * - **One-time CAPEX cost** (net_tech)
      - ✖
      - 0
      - CHF/m
      - **✓**
      - ✖
      - :code:`net_techs[ID]/costs/one_time_capex`
      - :ref:`network_techs.yaml<network_techs_yaml>`

    * - **One-time CAPEX cost** (tech)
      - ✖
      - 0
      - CHF
      - **✓**
      - ✖
      - :code:`techs[ID]/costs/one_time_capex`
      - :ref:`techs.yaml<techs_yaml>`

    * - **One-time OPEX cost** (net_tech)
      - ✖
      - 0
      - CHF/m
      - **✓**
      - ✖
      - :code:`net_techs[ID]/costs/one_time_opex`
      - :ref:`network_techs.yaml<network_techs_yaml>`

    * - **One-time OPEX cost** (tech)
      - ✖
      - 0
      - CHF
      - **✓**
      - ✖
      - :code:`techs[ID]/costs/one_time_opex`
      - :ref:`techs.yaml<techs_yaml>`

    * - **OPEX cost per capacity** (tech)
      - ✖
      - 0
      - CHF/CAP
      - **✓**
      - ✖
      - :code:`techs[ID]/costs/opex_per_cap`
      - :ref:`techs.yaml<techs_yaml>`

    * - **OPEX cost per capacity** (net_tech)
      - ✖
      - 0
      - CHF/((ec/h)*m)
      - **✓**
      - ✖
      - :code:`net_techs[ID]/costs/opex_per_cap`
      - :ref:`network_techs.yaml<network_techs_yaml>`

    * - **OPEX per output energy** (conversion)
      - ✖
      - 0
      - CHF/out_ec_main
      - **✓**
      - ✖
      - :code:`techs[ID]/costs/opex_per_energy`
      - :ref:`techs.yaml<techs_yaml>`

    * - **OPEX per transported energy** (net_tech)
      - ✖
      - 0
      - CHF/(ec*m)
      - **✓**
      - ✖
      - :code:`net_techs[ID]/costs/opex_per_energy`
      - :ref:`network_techs.yaml<network_techs_yaml>`

    * - **Output ec** (conversion)
      - **✓**
      -
      -
      - ✖
      - ✖
      - :code:`techs[ID]/conversion_params/out_ecs[ID]/ec_id`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Output efficiency** (conversion)
      - **✓**
      -
      - ec_out/ec_in_main
      - **✓**
      - **✓**
      - :code:`techs[ID]/conversion_params/out_ecs[ID]/out_eff`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Output efficiency** (EBM)
      - ✖
      - 1
      - [-]
      - **✓**
      - ✖
      - :code:`techs[ID]/ebm_params/out_eff`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Output efficiency** (storage)
      - ✖
      - 1
      - [-]
      - **✓**
      - ✖
      - :code:`techs[ID]/storage_params/out_eff`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Peak cost, above** (load_shifting)
      - ✖
      - 0
      - CHF/(ec/h)
      - ✖
      - ✖
      - :code:`load_shifting[ID]/peak_cost_above`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Peak cost, below** (load_shifting)
      - ✖
      - 0
      - CHF/(ec/h)
      - ✖
      - ✖
      - :code:`load_shifting[ID]/peak_cost_below`
      - :ref:`demands.yaml<demands_yaml>`

    * - **(Effective) Porosity of aquifer** (ates)
      - (**✓**)
      -
      - [-]
      - ✖
      - ✖
      - :code:`hubs[ID]/ates_params/porosity_aquifer`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Price** (import/export)
      - ✖
      - 0
      - CHF/ec
      - ✖
      - **✓**
      - :code:`stages[ID]/hubs[ID]/ecs[ID]/price`, :code:`stages[ID]/hubs[ID]/ecs[ID]/profile_path`
      - :ref:`imports.yaml<imports_yaml>`, :ref:`exports.yaml<exports_yaml>`

    * - **Rock density** (ates)
      - (**✓**)
      -
      - Ws/(kg*K)
      - ✖
      - ✖
      - :code:`hubs[ID]/ates_params/density_rock`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Rock specific heat capacity** (ates)
      - (**✓**)
      -
      - Ws/(kg*K)
      - ✖
      - ✖
      - :code:`hubs[ID]/ates_params/specific_heat_capacity_rock`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Self-sufficiency calculation method** (self-sufficiency)
      - ✖
      - "none"
      -
      -
      -
      - :code:`system_params/self_sufficiency_calculation_method`
      - :ref:`stages.yaml<stages_yaml>`

    * - **Solar area** (solar)
      - ✖
      - 0
      - m^2
      - ✖
      - ✖
      -
      - :ref:`solar_areas.csv<solar_areas_csv>`

    * - **Solar irradiation** (solar)
      - ✖
      - 0
      - (ec/h)/m^2
      - ✖
      - ✖
      -
      - :ref:`solar_irradiation.csv<solar_irradiation_csv>`

    * - **Stages** (load_shedding)
      - **✓**
      -
      -
      - ✖
      - ✖
      - :code:`load_shedding/manual[pos]/stages`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Stages** (load_shifting)
      - **✓**
      -
      -
      - ✖
      - ✖
      - :code:`load_shifting[ID]/stages`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Start of cold-to-warm phase** (ates)
      - **✓**
      -
      -
      - ✖
      - ✖
      - :code:`hubs[ID]/ates_params/schedules[ID]/phase_c2w_start_id`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Start of warm-to-cold phase** (ates)
      - **✓**
      -
      -
      - ✖
      - ✖
      - :code:`hubs[ID]/ates_params/schedules[ID]/phase_w2c_start_id`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Start year** (stage)
      - **✓**
      -
      -
      - ✖
      - ✖
      - :code:`stages[ID]/start_year`
      - :ref:`stages.yaml<stages_yaml>`

    * - **Standby loss** (ebm)
      - ✖
      - 0
      - [-]
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ebm_params/standby_loss`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Standby loss** (storage)
      - ✖
      - 0
      - [-]
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/storage_params/standby_loss`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Storage capacity** (ebm)
      - **✓**
      -
      - ec
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ebm_params/storage_cap`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Temperature, heating inlet** (heatpump)
      - (**✓**)
      -
      - K
      - **✓**
      - **✓**
      - :code:`hubs[ID]/techs[ID]/heatpump_params/temp_heat_in`, :code:`hubs[ID]/techs[ID]/heatpump_params/profile_path`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Temperature, heating outlet** (heatpump)
      - (**✓**)
      -
      - K
      - **✓**
      - **✓**
      - :code:`hubs[ID]/techs[ID]/heatpump_params/temp_heat_out`, :code:`hubs[ID]/techs[ID]/heatpump_params/profile_path`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Thermal radius per cold well** (ates)
      - ✖
      -
      - m
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ates_params/schedule_params[ID]/thermal_radius_per_cold_well`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Thermal radius per warm well** (ates)
      - ✖
      -
      - m
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ates_params/schedule_params[ID]/thermal_radius_per_warm_well`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Thickness of aquifer** (ates)
      - (**✓**)
      -
      - m
      - ✖
      - ✖
      - :code:`hubs[ID]/ates_params/thickness_aquifer`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Transmission decay** (net_tech)
      - ✖
      - 0
      - 1/m
      - **✓**
      - ✖
      - :code:`net_techs[ID]/trans_decay`
      - :ref:`network_techs.yaml<network_techs_yaml>`

    * - **TRL** (net_tech)
      - ✖
      - :math:`\infty`
      -
      - **✓**
      - ✖
      - :code:`net_techs[ID]/trl`
      - :ref:`network_techs.yaml<network_techs_yaml>`

    * - **TRL** (tech)
      - ✖
      - :math:`\infty`
      -
      - **✓**
      - ✖
      - :code:`techs[ID]/tech_params/trl`
      - :ref:`techs.yaml<techs_yaml>`

    * - **TRL threshold** (system)
      - ✖
      - 0
      -
      - ✖
      - ✖
      - :code:`system_params/trl_threshold`
      - :ref:`stages.yaml<stages_yaml>`

    * - **Well pair area calculation method** (ates)
      - ✖
      - "smallest rectangle"
      -
      - ✖
      - ✖
      - :code:`techs[ID]/ates_params/well_pair_area_calc_method`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Well distance** (ates)
      - **(✓)**
      -
      - m
      - ✓
      - ✖
      - :code:`hubs[ID]/techs[ID]/ates_params/well_distance`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Well radius** (ates)
      - (**✓**)
      -
      - m
      - ✖
      - ✖
      - :code:`techs[ID]/ates_params/well_radius`
      - :ref:`techs.yaml<techs_yaml>`

.. only:: latex

   .. raw:: latex

      \endgroup

.. only:: latex

   .. raw:: latex

      \end{landscape}
