Parameter overview
===================

Legend
-------

* **Name**: Name of parameter (only used within this table)
* **Mandatory**: Whether this parameter has to be set for the model to be built correctly. Non-mandatory parameters usually have a default value. Used symbols are:
    * **✓**: Parameter is mandatory.
    * (**✓**): Parameter is mandatory under some conditions.
    * ✖: Parameter is optional.
* **Default**: Default value for optional parameters
* **Unit**: Unit for the parameter (see :ref:`units`).
* **Per year**: Whether this parameter can be specified as year-dependent (see :ref:`parameter_types`)
    * **✓**: Parameter can be specified as year-dependent.
    * ✖: Parameter cannot be specified as year-dependent.
* **Per ts**: Whether this parameter can be specified as a timeseries (see :ref:`parameter_types`). This will happen by specifying a path to a time series file, and the specific structure is dependent on the parameter itself.
    * **✓**: Parameter can be specified as a time series.
    * ✖: Parameter cannot be specified as a time series.
* **Node path(s)**: Node path(s) (see :ref:`node_paths`) within the file where this parameter is specified.
* **File**: File in which this parameter is specified.

Parameter table
----------------

.. list-table:: Parameter list
    :header-rows: 1

    * - Name
      - Mandatory
      - Default
      - Unit
      - Per year
      - Per ts
      - Node path(s)
      - File

    * - **Allowed net_tech lists** (link)
      - ✖
      - []
      -
      - ✖
      - ✖
      - :code:`start_hubs[ID]/end_hubs[ID]/links[ID]/allowed_net_tech_lists`
      - :ref:`links.yaml<network_links_yaml>`

    * - **Allowed tech lists** (tech)
      - ✖
      - []
      -
      - ✖
      - ✖
      - :code:`hubs[ID]/allowed_tech_lists`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Autarky calculation method** (autarky)
      - ✖
      - "none"
      -
      -
      -
      - :code:`system_params/autarky_calculation_method`
      - :ref:`stages.yaml<stages_yaml>`

    * - **Availability** (conversion)
      - ✖
      - 1
      - 1
      - **✓**
      - **✓**
      - :code:`hubs[ID]/techs[ID]/conversion_params/availability`, :code:`hubs[ID]/techs[ID]/conversion_params/profile_path`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Availability** (ebm)
      - ✖
      - 1
      - 1
      - **✓**
      - **✓**
      - :code:`hubs[ID]/techs[ID]/ebm_params/availability`, :code:`hubs[ID]/techs[ID]/ebm_params/profile_path`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Availability** (net_links)
      - ✖
      - 1
      - 1
      - **✓**
      - **✓**
      - :code:`start_hubs[ID]/end_hubs[id]/links[id]/ec_params[id]/availability`, :code:`start_hubs[ID]/end_hubs[id]/links[id]/ec_params[id]/profile_path`
      - :ref:`network_links.yaml<network_links_yaml>`

    * - **Available area** (ates)
      - ✖
      - :math:`\infty`
      - :math:`m^2`
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
      - :ref:`links.yaml<network_links_yaml>`

    * - **Capacity factor** (coupling)
      - **✓**
      -
      - 1
      - ✖
      - ✖
      - :code:`techs[ID]/coupling_params/cap_factor`
      - :ref:`techs.yaml<techs_yaml>`

    * - **CAPEX per capacity** (net_tech)
      - ✖
      - 0
      - CHF/kW/m
      - **✓**
      - ✖
      - :code:`net_techs[ID]/costs/capex_per_cap`
      - :ref:`net_techs.yaml<network_techs_yaml>`

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
      - kg/kW
      - ✖
      - **✓**
      - :code:`stages[ID]/hubs[ID]/ecs[ID]/co2`, :code:`stages[ID]/hubs[ID]/ecs[ID]/profile_path`
      - :ref:`imports.yaml<imports_yaml>`, :ref:`exports.yaml<exports_yaml>`

    * - **CO2 per installed capacity** (net_tech)
      - ✖
      - 0
      - kg/kW/m
      - **✓**
      - ✖
      - :code:`net_techs[ID]/emissions/co2_per_cap`
      - :ref:`net_techs.yaml<network_techs_yaml>`

    * - **CO2 per installed capacity** (tech)
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
      - kg/kWh/m
      - **✓**
      - ✖
      - :code:`net_techs[ID]/emissions/co2_per_energy`
      - :ref:`net_techs.yaml<network_techs_yaml>`

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
      - 0
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

    * - **Cool** (ates)
      - **✓**
      -
      -
      - ✖
      - ✖
      - :code:`techs[ID]/ates_params/ecs`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Cut-in velocity** (wind)
      - **✓**
      -
      - :math:`m/s`
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/wind_params/velo_cut_in`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Cut-off velocity** (wind)
      - **✓**
      -
      - :math:`m/s`
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/wind_params/velo_cut_off`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Demand** (demand)
      - ✖
      - 0
      - kW
      - ✖
      - **✓**
      - :code:`demands[ID]/profile_path`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Demand modifier** (ebm)
      - ✖
      - 1
      - 1
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ebm_params/demand_modifier`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Discharge controllability** (ebm)
      - ✖
      - 1
      - 1
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ebm_params/discharge_controllability`
      - :ref:`techs.yaml<techs_yaml>`

    * - **EC** (ebm)
      - **✓**
      -
      -
      - ✖
      - ✖
      - :code:`techs[ID]/ebm_params/ec`
      - :ref:`techs.yaml<techs_yaml>`

    * - **EC** (net_tech)
      - **✓**
      -
      -
      - ✖
      - ✖
      - :code:`net_techs[ID]/ec`
      - :ref:`net_techs.yaml<network_techs_yaml>`

    * - **EC** (storage)
      - **✓**
      -
      -
      - ✖
      - ✖
      - :code:`techs[ID]/storage_params/ec`
      - :ref:`techs.yaml<techs_yaml>`

    * - **ECs** (link)
      - **✓**
      -
      -
      - ✖
      - ✖
      - :code:`start_hubs[ID]/end_hubs[ID]/links[ID]/ecs`
      - :ref:`links.yaml<network_links_yaml>`

    * - **ECs** (load_shedding)
      - **✓**
      -
      -
      - ✖
      - ✖
      - :code:`load_shedding/manual[pos]/ecs`
      - :ref:`demands.yaml<demands_yaml>`

    * - **ECs** (load_shifting)
      - **✓**
      -
      -
      - ✖
      - ✖
      - :code:`load_shifting[ID]/ecs`
      - :ref:`demands.yaml<demands_yaml>`

    * - **ECs** (windpark)
      - **✓**
      -
      -
      - ✖
      - ✖
      - :code:`windparks[ID]/ecs`
      - :ref:`ecs.yaml<ecs_yaml>`

    * - **Elec** (ates)
      - **✓**
      -
      -
      - ✖
      - ✖
      - :code:`techs[ID]/ates_params/ecs`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Electricity consumption per cooling energy** (ates)
      - **(✓)**
      -
      - 1
      - ✖
      - ✖
      - :code:`techs[ID]/ates_params/elec_per_energy_cool`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Electricity consumption per heating energy** (ates)
      - **(✓)**
      -
      - 1
      - ✖
      - ✖
      - :code:`techs[ID]/ates_params/elec_per_energy_heat`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Electricity consumption per heating flow** (ates)
      - ✖
      -
      - 1
      - ✖
      - ✖
      - :code:`techs[ID]/ates_params/elec_per_energy_heat`
      - :ref:`techs.yaml<techs_yaml>`

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
      - CHF/kW
      - ✖
      - ✖
      - :code:`load_shedding/preset/energy_cost`, :code:`load_shedding/manual[pos]/energy_cost`, :code:`load_shedding/manual[pos]/profile_path`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Energy cost, above** (load_shifting)
      - ✖
      - 0
      - CHF/kWh
      - ✖
      - **✓**
      - :code:`load_shifting[ID]/energy_cost_above`, :code:`load_shifting[ID]/profile_path`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Energy cost, below** (load_shifting)
      - ✖
      - 0
      - CHF/kWh
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
      - :math:`kg/m^3`
      - ✖
      - ✖
      - :code:`techs[ID]/ates_params`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Fluid specific heat capacity** (ates)
      - **✓**
      -
      - :math:`J/(kg*K)`
      - ✖
      - ✖
      - :code:`techs[ID]/ates_params`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Groundwater velocity** (ates)
      - (**✓**)
      -
      - :math:`m/d`
      - ✖
      - ✖
      - :code:`hubs[ID]/ates_params/groundwater_velocity`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Heat** (ates)
      - **✓**
      -
      -
      - ✖
      - ✖
      - :code:`techs[ID]/ates_params/ecs`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Hubs** (load_shedding)
      - **✓**
      -
      -
      - ✖
      - ✖
      - :code:`load_shedding/manual[pos]/hubs`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Hubs** (load_shifting)
      - **✓**
      -
      -
      - ✖
      - ✖
      - :code:`load_shifting[ID]/hubs`
      - :ref:`demands.yaml<demands_yaml>`

    * - **imp_exp_type** (autarky)
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
      - :ref:`links.yaml<network_links_yaml>`

    * - **Initial age** (tech)
      - ✖
      - 0
      - a
      - ✖
      - ✖
      - :code:`hubs[ID]/techs[ID]/tech_params/age_init`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Initial capacity** (net_tech)
      - ✖
      - 0
      - kW
      - ✖
      - ✖
      - :code:`start_hubs[ID]/end_hubs[ID]/links[ID]/net_tech_params/cap_init`
      - :ref:`links.yaml<network_links_yaml>`

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
      - 1
      - ✖
      - ✖
      - :code:`hubs[ID]/techs[ID]/ebm_params/soc_init`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Initial stage of charge** (storage)
      - ✖
      - :math:`\infty`
      - 1
      - ✖
      - ✖
      - :code:`hubs[ID]/techs[ID]/storage_params/soc_init`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Input ec** (conversion)
      - **✓**
      -
      -
      - ✖
      - ✖
      - :code:`techs[ID]/conversion_params/in_ecs[ID]/in_id`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Input efficiency** (ebm)
      - ✖
      - 1
      - 1
      - **✓**
      - ✖
      - :code:`techs[ID]/ebm_params/in_eff`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Input efficiency** (storage)
      - ✖
      - 1
      - 1
      - **✓**
      - ✖
      - :code:`techs[ID]/storage_params/in_eff`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Input part** (conversion)
      - **✓**
      -
      -
      - **✓**
      - ✖
      - :code:`techs[ID]/conversion_params/in_ecs[ID]/in_part`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Interest rate default** (system)
      - **✓**
      -
      - 1
      - ✖
      - ✖
      - :code:`system_params/interest_rate_def`
      - :ref:`stages.yaml<stages_yaml>`

    * - **Interest rate** (net_tech)
      - ✖
      -
      - 1
      - ✖
      - ✖
      - :code:`net_techs[ID]/costs/interest_rate`
      - :ref:`net_techs.yaml<network_techs_yaml>`

    * - **Interest rate** (tech)
      - ✖
      -
      - 1
      - ✖
      - ✖
      - :code:`techs[ID]/costs/interest_rate`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Interval capacity** (load_shifting)
      - ✖
      - :math:`\infty`
      - kWh
      - ✖
      - ✖
      - :code:`load_shifting[ID]/interval_cap`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Interval length** (load_shifting)
      - **✓**
      -
      -
      - ✖
      - ✖
      - :code:`load_shifting[ID]/interval_length`
      - :ref:`demands.yaml<demands_yaml>`

    * - **is_energy** (autarky)
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
      - 1
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
      - :ref:`links.yaml<network_links_yaml>`

    * - **Lifetime** (net_tech)
      - **✓**
      -
      - a
      - ✖
      - ✖
      - :code:`net_techs[ID]/lifetime`
      - :ref:`net_techs.yaml<network_techs_yaml>`

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
      - kW
      - ✖
      - **✓**
      - :code:`stages[ID]/hubs[ID]/ecs[ID]/max`, :code:`stages[ID]/hubs[ID]/ecs[ID]/profile_path`
      - :ref:`imports.yaml<imports_yaml>`, :ref:`exports.yaml<exports_yaml>`

    * - **Maximal autarky** (autarky)
      - ✖
      - 1
      -
      -
      -
      - :code:`system_params/autarky_max`
      - :ref:`stages.yaml<stages_yaml>`

    * - **Maximal capacity** (link)
      - ✖
      - :math:`\infty`
      - kW
      - **✓**
      - ✖
      - :code:`start_hubs[ID]/end_hubs[ID]/links[ID]/ec_params/cap_max`
      - :ref:`links.yaml<network_links_yaml>`

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
      - kW
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ebm_params/charge_max`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Maximal charging power** (storage)
      - ✖
      - :math:`\infty`
      - kW/CAP
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/storage_params/charge_max`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Maximal curtailment** (solar)
      - ✖
      - 1
      - 1
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/solar_params/curtail_max_rel`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Maximal curtailment** (wind)
      - ✖
      - 1
      - 1
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/wind_params/curtail_max_rel`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Maximal discharging power** (ebm)
      - ✖
      - :math:`\infty`
      - kW
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ebm_params/discharge_max`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Maximal discharging power** (storage)
      - ✖
      - :math:`\infty`
      - kW/CAP
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/storage_params/discharge_max`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Maximal drawdown of aquifer** (ates)
      - (**✓**)
      -
      - :math:`m`
      - ✖
      - ✖
      - :code:`hubs[ID]/ates_params/max_drawdown`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Maximal total heating over cooling** (ates)
      - ✖
      - :math:`\infty`
      - 1
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ates_params/schedule_params[ID]/max_heat_over_cool`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Maximal total cooling over heating** (ates)
      - ✖
      - :math:`\infty`
      - 1
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ates_params/schedule_params[ID]/max_cool_over_heat`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Maximal load shedding, absolute** (load_shedding)
      - ✖
      - :math:`\infty`
      - kW
      - ✖
      - ✖
      - :code:`load_shedding/preset/max_abs`, :code:`load_shedding/manual[pos]/max_abs`, :code:`load_shedding/manual[pos]/profile_path`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Maximal load shedding, relative** (load_shedding)
      - ✖
      - 1
      - 1
      - ✖
      - ✖
      - :code:`load_shedding/preset/max_rel`, :code:`load_shedding/manual[pos]/max_rel`, :code:`load_shedding/manual[pos]/profile_path`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Maximal load shifting, absolute-above** (load_shifting)
      - ✖
      - :math:`\infty`
      - kW
      - ✖
      - **✓**
      - :code:`load_shifting[ID]/max_above_abs`, :code:`load_shifting[ID]/profile_path`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Maximal load shifting, absolute-below** (load_shifting)
      - ✖
      - :math:`\infty`
      - kW
      - ✖
      - **✓**
      - :code:`load_shifting[ID]/max_below_abs`, :code:`load_shifting[ID]/profile_path`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Maximal load shifting, relative-above** (load_shifting)
      - ✖
      - :math:`\infty`
      - 1
      - ✖
      - **✓**
      - :code:`load_shifting[ID]/max_above_rel`, :code:`load_shifting[ID]/profile_path`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Maximal load shifting, relative-below** (load_shifting)
      - ✖
      - 1
      - 1
      - ✖
      - **✓**
      - :code:`load_shifting[ID]/max_below_rel`, :code:`load_shifting[ID]/profile_path`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Maximal pumping rate per cold well** (ates)
      - ✖
      -
      - :math:`m^3/s`
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ates_params/schedule_params[ID]/max_pump_rate_per_cold_well`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Maximal pumping rate per warm well** (ates)
      - ✖
      -
      - :math:`m^3/s`
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ates_params/schedule_params[ID]/max_pump_rate_per_warm_well`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Maximal stage of charge** (storage)
      - ✖
      - 1
      - 1
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/storage_params/soc_max`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Maximal summed-up backward transport** (link)
      - ✖
      - :math:`\infty`
      - kWh
      - **✓**
      - ✖
      - :code:`start_hubs[ID]/end_hubs[ID]/links[ID]/ec_params/sum_max_backward`
      - :ref:`links.yaml<network_links_yaml>`

    * - **Maximal summed-up forward transport** (link)
      - ✖
      - :math:`\infty`
      - kWh
      - **✓**
      - ✖
      - :code:`start_hubs[ID]/end_hubs[ID]/links[ID]/ec_params/sum_max_forward`
      - :ref:`links.yaml<network_links_yaml>`

    * - **Maximal summed-up imports/exports** (import/export)
      - ✖
      - :math:`\infty`
      - kWh
      - ✖
      - ✖
      - :code:`stages[ID]/hubs[ID]/ecs[ID]/sum_max`
      - :ref:`imports.yaml<imports_yaml>`, :ref:`exports.yaml<exports_yaml>`

    * - **Maximal summed-up output** (conversion)
      - ✖
      - :math:`\infty`
      - kWh
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/conversion_params/out_sum_max`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Maximal temperature spread for cold wells** (ates)
      - **✓**
      -
      - :math:`°C`
      - ✖
      - ✖
      - :code:`hubs[ID]/ates_params/max_temperature_spread_cold`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Maximal temperature spread for warm wells** (ates)
      - **✓**
      -
      - :math:`°C`
      - ✖
      - ✖
      - :code:`hubs[ID]/ates_params/max_temperature_spread_warm`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Min** (import/export)
      - ✖
      - 0
      - kW
      - ✖
      - **✓**
      - :code:`stages[ID]/hubs[ID]/ecs[ID]/min`, :code:`stages[ID]/hubs[ID]/ecs[ID]/profile_path`
      - :ref:`imports.yaml<imports_yaml>`, :ref:`exports.yaml<exports_yaml>`

    * - **Minimal summed-up backward transport** (link)
      - ✖
      - :math:`\infty`
      - kWh
      - **✓**
      - ✖
      - :code:`start_hubs[ID]/end_hubs[ID]/links[ID]/ec_params/sum_max_backward`
      - :ref:`links.yaml<network_links_yaml>`

    * - **Maximal summed-up forward transport** (link)
      - ✖
      - :math:`\infty`
      - kWh
      - **✓**
      - ✖
      - :code:`start_hubs[ID]/end_hubs[ID]/links[ID]/ec_params/sum_max_forward`
      - :ref:`links.yaml<network_links_yaml>`

    * - **Maximal summed-up imports/exports** (import/export)
      - ✖
      - :math:`\infty`
      - kWh
      - ✖
      - ✖
      - :code:`stages[ID]/hubs[ID]/ecs[ID]/sum_max`
      - :ref:`imports.yaml<imports_yaml>`, :ref:`exports.yaml<exports_yaml>`

    * - **Maximal summed-up output** (conversion)
      - ✖
      - :math:`\infty`
      - kWh
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/conversion_params/out_sum_max`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Min** (import/export)
      - ✖
      - 0
      - kW
      - ✖
      - **✓**
      - :code:`stages[ID]/hubs[ID]/ecs[ID]/min`, :code:`stages[ID]/hubs[ID]/ecs[ID]/profile_path`
      - :ref:`imports.yaml<imports_yaml>`, :ref:`exports.yaml<exports_yaml>`

    * - **Minimal autarky** (autarky)
      - ✖
      - 0
      -
      -
      -
      - :code:`system_params/autarky_min`
      - :ref:`stages.yaml<stages_yaml>`

    * - **Minimal capacity** (link)
      - ✖
      - 0
      - kW
      - **✓**
      - ✖
      - :code:`start_hubs[ID]/end_hubs[ID]/links[ID]/ec_params/cap_min`
      - :ref:`links.yaml<network_links_yaml>`

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
      - 1
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ebm_params/soc_min`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Minimal stage of charge** (storage)
      - ✖
      - 0
      - 1
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/storage_params/soc_min`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Minimal summed-up backward transport** (link)
      - ✖
      - 0
      - kWh
      - **✓**
      - ✖
      - :code:`start_hubs[ID]/end_hubs[ID]/links[ID]/ec_params/sum_min_backward`
      - :ref:`links.yaml<network_links_yaml>`

    * - **Minimal summed-up forward transport** (link)
      - ✖
      - 0
      - kWh
      - **✓**
      - ✖
      - :code:`start_hubs[ID]/end_hubs[ID]/links[ID]/ec_params/sum_min_forward`
      - :ref:`links.yaml<network_links_yaml>`

    * - **Minimal summed-up imports/exports** (import/export)
      - ✖
      - 0
      - kWh
      - ✖
      - ✖
      - :code:`stages[ID]/hubs[ID]/ecs[ID]/sum_min`
      - :ref:`imports.yaml<imports_yaml>`, :ref:`exports.yaml<exports_yaml>`

    * - **Minimal summed-up output** (conversion)
      - ✖
      - 0
      - kWh
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/conversion_params/out_sum_min`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Minimal unit capacity** (net_tech)
      - ✖
      - 0
      - kW
      - **✓**
      - ✖
      - :code:`net_techs[ID]/unit_cap_min`
      - :ref:`net_techs.yaml<network_techs_yaml>`

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
      - kW
      - **✓**
      - **✓**
      - :code:`hubs[ID]/techs[ID]/ebm_params/demand_nominal`, :code:`hubs[ID]/techs[ID]/ebm_params/profile_path`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Nominal velocity** (wind)
      - **✓**
      -
      - :math:`m/s`
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/wind_params/velo_nominal`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Number of horizon timesteps** (system)
      - **✓**
      -
      - 1
      - ✖
      - ✖
      - :code:`system_params/num_times_horizon`
      - :ref:`stages.yaml<stages_yaml>`

    * - **Number of vehicles** (ebm)
      - **✓**
      -
      - 1
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[id]/ebm_params/num_vehicles`
      - :ref:`hubs_yaml`

    * - **One-time CAPEX cost** (net_tech)
      - ✖
      - 0
      - CHF/m
      - **✓**
      - ✖
      - :code:`net_techs[ID]/costs/one_time_capex`
      - :ref:`net_techs.yaml<network_techs_yaml>`

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
      - :ref:`net_techs.yaml<network_techs_yaml>`

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
      - CHF/kW/m
      - **✓**
      - ✖
      - :code:`net_techs[ID]/costs/opex_per_cap`
      - :ref:`net_techs.yaml<network_techs_yaml>`

    * - **OPEX per output energy** (conversion)
      - ✖
      - 0
      - CHF/kWh
      - **✓**
      - ✖
      - :code:`techs[ID]/costs/opex_per_energy`
      - :ref:`techs.yaml<techs_yaml>`

    * - **OPEX per transported energy** (net_tech)
      - ✖
      - 0
      - CHF/kWh/m
      - **✓**
      - ✖
      - :code:`net_techs[ID]/costs/opex_per_energy`
      - :ref:`net_techs.yaml<network_techs_yaml>`

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
      - 1
      - **✓**
      - **✓**
      - :code:`techs[ID]/conversion_params/out_ecs[ID]/out_eff`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Output efficiency** (EBM)
      - ✖
      - 1
      - 1
      - **✓**
      - ✖
      - :code:`techs[ID]/ebm_params/out_eff`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Output efficiency** (storage)
      - ✖
      - 1
      - 1
      - **✓**
      - ✖
      - :code:`techs[ID]/storage_params/out_eff`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Peak cost, above** (load_shifting)
      - ✖
      - 0
      - CHF/kW
      - ✖
      - ✖
      - :code:`load_shifting[ID]/peak_cost_above`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Peak cost, below** (load_shifting)
      - ✖
      - 0
      - CHF/kW
      - ✖
      - ✖
      - :code:`load_shifting[ID]/peak_cost_below`
      - :ref:`demands.yaml<demands_yaml>`

    * - **Price** (import/export)
      - ✖
      - 0
      - CHF/kW
      - ✖
      - **✓**
      - :code:`stages[ID]/hubs[ID]/ecs[ID]/price`, :code:`stages[ID]/hubs[ID]/ecs[ID]/profile_path`
      - :ref:`imports.yaml<imports_yaml>`, :ref:`exports.yaml<exports_yaml>`

    * - **Rotor area** (wind)
      - **✓**
      -
      - :math:`m^2`
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/wind_params/rotor_area`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Specific heat capacity of aquifer** (ates)
      - (**✓**)
      -
      - :math:`J/(kg*K)`
      - ✖
      - ✖
      - :code:`hubs[ID]/ates_params/specific_heat_capacity_aquifer`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Solar area** (solar)
      - ✖
      - 0
      - :math:`m^2`
      - ✖
      - ✖
      -
      - :ref:`solar_areas.csv<solar_areas_csv>`

    * - **Solar irradiation** (solar)
      - ✖
      - 0
      - kW/:math:`m^2`
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
      - 1
      - ✖
      - ✖
      - :code:`stages[ID]/start_year`
      - :ref:`stages.yaml<stages_yaml>`

    * - **Standby loss** (ebm)
      - ✖
      - 0
      - 1
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ebm_params/standby_loss`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Standby loss** (storage)
      - ✖
      - 0
      - 1
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/storage_params/standby_loss`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Storage capacity** (ebm)
      - **✓**
      -
      - kWh
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ebm_params/storage_cap`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Storativity of aquifer** (ates)
      - (**✓**)
      -
      - :math:`1`
      - ✖
      - ✖
      - :code:`hubs[ID]/ates_params/storativity_aquifer`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Thermal radius per cold well** (ates)
      - ✖
      -
      - :math:`m`
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ates_params/schedule_params[ID]/thermal_radius_per_cold_well`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Thermal radius per warm well** (ates)
      - ✖
      -
      - :math:`m`
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/ates_params/schedule_params[ID]/thermal_radius_per_warm_well`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Thickness of aquifer** (ates)
      - (**✓**)
      -
      - :math:`m`
      - ✖
      - ✖
      - :code:`hubs[ID]/ates_params/thickness_aquifer`
      - :ref:`hubs.yaml<hubs_yaml>`

    * - **Transmission loss** (net_tech)
      - ✖
      - 0
      - 1/m
      - **✓**
      - ✖
      - :code:`net_techs[ID]/trans_loss`
      - :ref:`net_techs.yaml<network_techs_yaml>`

    * - **TRL** (net_tech)
      - ✖
      - :math:`\infty`
      - 1
      - **✓**
      - ✖
      - :code:`net_techs[ID]/trl`
      - :ref:`net_techs.yaml<network_techs_yaml>`

    * - **TRL** (tech)
      - ✖
      - :math:`\infty`
      - 1
      - **✓**
      - ✖
      - :code:`techs[ID]/tech_params/trl`
      - :ref:`techs.yaml<techs_yaml>`

    * - **TRL threshold** (system)
      - ✖
      - 0
      - 1
      - ✖
      - ✖
      - :code:`system_params/trl_threshold`
      - :ref:`stages.yaml<stages_yaml>`

    * - **Turbine footprint** (wind)
      - **✓**
      -
      - :math:`m^2`
      - **✓**
      - ✖
      - :code:`hubs[ID]/techs[ID]/wind_params/turbine_footprint`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Well pair area calculation method** (ates)
      - ✖
      - "smallest rectangle"
      -
      - ✖
      - ✖
      - :code:`techs[ID]/ates_params/well_pair_area_calc_method`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Well radius** (ates)
      - (**✓**)
      -
      - :math:`m`
      - ✖
      - ✖
      - :code:`techs[ID]/ates_params/well_radius`
      - :ref:`techs.yaml<techs_yaml>`

    * - **Wind area** (wind)
      - ✖
      - 0
      - :math:`m^2`
      - ✖
      - ✖
      -
      - :ref:`wind_areas.csv<wind_areas_csv>`

    * - **Wind velocity** (wind)
      - ✖
      - 0
      - m/s
      - ✖
      - ✖
      -
      - :ref:`wind_velocity.csv<wind_velocity_csv>`
