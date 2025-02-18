.. role:: raw-math(raw)
    :format: latex html

.. |Y_Hub| replace:: :ref:`hubs.yaml<hubs_yaml>`
.. |Y_NetLink| replace:: :ref:`network_links.yaml<network_links_yaml>`
.. |Y_Imp| replace:: :ref:`imports.yaml<imports_yaml>`
.. |Y_Exp| replace:: :ref:`exports.yaml<exports_yaml>`
.. |Y_Demand| replace:: :ref:`demands.yaml<demands_yaml>`
.. |Y_Tech| replace:: :ref:`techs.yaml<techs_yaml>`
.. |Y_NetTech| replace:: :ref:`network_techs.yaml<network_techs_yaml>`
.. |S_Stage| replace:: :math:`\mathcal{S}_{Stage}`
.. |S_Hub| replace:: :math:`\mathcal{S}_{Hub}`
.. |S_Ec| replace:: :math:`\mathcal{S}_{Ec}`
.. |S_Time| replace:: :math:`\mathcal{S}_{Time}`
.. |S_TimeHorizon| replace:: :math:`\mathcal{S}_{TimeHorizon}`

.. _model:

Model
=======

The ehubX model is built from sub-models (or *modules*) that address different aspects of the energy system. Each model adds to (and in some occasions removes from) a Pyomo model object. The models are loosely organized quite similarily to the :ref:`input file structure<input_files>`:

.. code-block:: ruby

    energy_system_model
    |-- stage_model
    |-- hub_model
    |-- ec_model
    |-- times_model
    |-- import_model
    |-- export_model
    |-- demand_model
        |-- load_shedding_model
        |-- load_shifting_model
    |-- network_model
    |-- tech_model
        |-- stor_tech_model
        |-- conv_tech_model
            |-- solar_tech_model
            |-- wind_tech_model
        |-- ebm_tech_model
        |-- ates_tech_model
        |-- hp_tech_model



.. _stage_model:

Stage model
-------------

This module introduces an index set |S_Stage| of stages. They consist of unique string labels (e.g.; :math:`S1`).



.. _hub_model:

Hub model
-----------

This module introduces an index set |S_Hub| of hubs. They consist of unique string labels (e.g.; :math:`H1`).



.. _ec_model:

Ec model
---------

This module introduces an index set |S_Ec| of ecs (energy carriers). They consist of unique string labels (e.g.; :math:`E1`).



.. _times_model:

Times model
------------

This module introduces two index sets |S_TimeHorizon| and |S_Time| (energy carriers). They each consist of unique integers :math:`1, 2, ...` that act as time indices. In case where :ref:`reduced-order modeling <rom>` is employed, |S_Time| holds the cluster indices and |S_TimeHorizon| holds the full-horizon indices. If no clustering is used, these two sets are identical.



.. _import_model:

Import model
--------------

Import of energy carriers is possible for certain tuples of stages, hubs and ecs, as defined piecewise in |Y_Imp|. The set of all importable tuples is labeled :math:`\mathcal{S}_{ImpTuple} \subset \mathcal{S}_{Stage} \times \mathcal{S}_{Hub} \times \mathcal{S}_{Ec}`. The variable

:math:`\mathcal{V}_{Imp}: \mathcal{S}_{ImpTuple} \times \mathcal{S}_{Time} \to \mathbb{R}^+_0`

denotes the import amounts per time step. These values may be constrained

a) in a piecewise manner by :math:`min[s, h, e, t] \le \mathcal{V}_{Imp}[s, h, e, t] \le max[s, h, e, t]` where :math:`min` and :math:`max` are parameters from |Y_Imp|.
b) in a summed-up manner by :math:`sum\_min[s, h, e] \le \sum_{t \in \mathcal{S}_{Time}} weight[s, t] \cdot \mathcal{V}_{Imp}[s, h, e, t] \le sum\_max[s, h, e]` where :math:`sum\_min` and :math:`sum_\max` are parameters from |Y_Imp| and :math:`weight` is a :ref:`clustering<clustering>` value.

Certain costs are associated with imports which are defined per import tuple using the parameter :math:`price` from |Y_Imp| by a fixed variable

:raw-math:`$$ \begin{align*} \mathcal{V}_{ImpCost}: \mathcal{S}_{ImpTuple} &\to \mathbb{R} \\ \mathcal{V}_{ImpCost}[s, h, e] &= \sum_{t \in \mathcal{S}_{Time}} weight[s, t] \cdot price[s, h, e, t] \cdot \mathcal{V}_{Imp}[s, h, e, t] \end{align*} $$`

Similarily, imports might come with CO2 emissions. These are quantified using the parameter :math:`co2` from |Y_Imp| and tracked in a  fixed variable

:raw-math:`$$ \begin{align*} \mathcal{V}_{ImpCo2}: \mathcal{S}_{ImpTuple} &\to \mathbb{R} \\ \mathcal{V}_{ImpCo2}[s, h, e] &= \sum_{t \in \mathcal{S}_{Time}} weight[s, t] \cdot co2[s, h, e, t] \cdot \mathcal{V}_{Imp}[s, h, e, t] \end{align*} $$`

Information about costs and CO2 for imports are required in the :ref:`energy system model<energy_system_model>`. They are bundled in the following fixed variables for convenience:

:raw-math:`$$ \begin{align*} \mathcal{V}_{ImpCostTotal} &\in \mathbb{R}^+_0, \quad &\mathcal{V}_{ImpCostTotal} &= \sum_{(s, h, e) \in \mathcal{S}_{ImpTuple}} \mathcal{V}_{ImpCost}[s, h, e] \\ \mathcal{V}_{ImpCo2Total}: \mathcal{S}_{Stage} &\to \mathbb{R}, \quad &\mathcal{V}_{ImpCo2Total}[s] &= \sum_{\substack{(s', h, e) \in \mathcal{S}_{ImpTuple} \\ s'=s}} \mathcal{V}_{ImpCo2}[s', h, e] \end{align*} $$`



.. _export_model:

Export model
--------------

Export of energy carriers is possible for certain tuples of stages, hubs and ecs, as defined piecewise in |Y_Exp|. The set of all exportable tuples is labeled :math:`\mathcal{S}_{ExpTuple} \subset \mathcal{S}_{Stage} \times \mathcal{S}_{Hub} \times \mathcal{S}_{Ec}`. The variable

:math:`\mathcal{V}_{Exp}: \mathcal{S}_{ExpTuple} \times \mathcal{S}_{Time} \to \mathbb{R}^+_0`

denotes the export amounts per time step. These values may be constrained

a) in a piecewise manner by :math:`min[s, h, e, t] \le \mathcal{V}_{Exp}[s, h, e, t] \le max[s, h, e, t]` where :math:`min` and :math:`max` are parameters from |Y_Exp|.
b) in a summed-up manner by :math:`sum\_min[s, h, e] \le \sum_{t \in \mathcal{S}_{Time}} weight[s, t] \cdot \mathcal{V}_{Exp}[s, h, e, t] \le sum\_max[s, h, e]` where :math:`sum\_min` and :math:`sum_\max` are parameters from |Y_Exp| and :math:`weight` is a :ref:`clustering<clustering>` value.

Certain profits are associated with exports which are defined per export tuple using the parameter :math:`price` from |Y_Exp| by a fixed variable

:raw-math:`$$ \begin{align*} \mathcal{V}_{ExpProfit}: \mathcal{S}_{ExpTuple} &\to \mathbb{R} \\ \mathcal{V}_{ExpProfit}[s, h, e] &= \sum_{t \in \mathcal{S}_{Time}} weight[s, t] \cdot price[s, h, e, t] \cdot \mathcal{V}_{Exp}[s, h, e, t] \end{align*} $$`

Similarily, exports might come with reductions in CO2 emissions. These are quantified using the parameter :math:`co2` from |Y_Exp| and tracked in a  fixed variable

:raw-math:`$$ \begin{align*} \mathcal{V}_{ExpCo2}: \mathcal{S}_{ExpTuple} &\to \mathbb{R} \\ \mathcal{V}_{ExpCo2}[s, h, e] &= \sum_{t \in \mathcal{S}_{Time}} weight[s, t] \cdot co2[s, h, e, t] \cdot \mathcal{V}_{Exp}[s, h, e, t] \end{align*} $$`

Information about profits and CO2 for exports are required in the :ref:`energy system model<energy_system_model>`. They are bundled in the following fixed variables for convenience:

:raw-math:`$$ \begin{align*} \mathcal{V}_{ExpProfitTotal} &\in \mathbb{R}^+_0, \quad &\mathcal{V}_{ExpProfitTotal} &= \sum_{(s, h, e) \in \mathcal{S}_{ExpTuple}} \mathcal{V}_{ExpProfit}[s, h, e] \\ \mathcal{V}_{ExpCo2Total}: \mathcal{S}_{Stage} &\to \mathbb{R}, \quad &\mathcal{V}_{ExpCo2Total}[s] &= \sum_{\substack{(s', h, e) \in \mathcal{S}_{ExpTuple} \\ s'=s}} \mathcal{V}_{ExpCo2}[s', h, e] \end{align*} $$`



.. _demand_model:

Demand model
--------------

There are demand values for certain tuples of stages, hubs and ecs, as defined piecewise in |Y_Demand|. The set of all demand tuples is labeled :math:`\mathcal{S}_{DemandTuple} \subset \mathcal{S}_{Stage} \times \mathcal{S}_{Hub} \times \mathcal{S}_{Ec}`. This set is required by the :ref:`energy system model<energy_system_model>`.

Additionally, certain formulations in other modules require a so-called *big-M* parameter which is very common in MILP formulations. Essentially, this is a positive value that is "as large as it needs to be", usually larger than any values an optimization variable is going to assume. Since it's important that this parameter is chosen "tightly", ehubX will try to calculate it specifically for the occasions where it is needed. However, sometimes the chosen input parameters don't allow this and we require a fallback option. For this reason, the demand module calculates a generic big-M parameter which is larger than any value we are likely to encounter in our energy system. This parameter is given by

:raw-math:`$$ \mathcal{P}_{BigMGeneric} = \left \{ \begin{array}{rl} 10^6, & \text{if } \mathcal{S}_{DemandTuple} = \emptyset \\ 10^3 \left( \max\limits_{\substack{s \in \mathcal{S}_{Stage} \\ t \in \mathcal{S}_{Time}}} \sum\limits_{\substack{(s', h, e) \in \mathcal{S}_{DemandTuple} \\ s' = s}} demand[s', h, e, t] \right) + 10^{-5}, & else \end{array} \right . $$`

Note the underlying assumption here that the demand series will be able to quantify the general dimensionality of the system. Especially in systems with small demand profiles (but also in general), it might be prudent to explicitly set values for certain parameters so that the generic big-M parameter does not have to be used. Tailored warning messages are routinely written to the :ref:`logfile<logging>` for this reason, notifying the user which parameters are missing to calculate a specific big-M parameter (the most common candidate for this is :math:`cap\_max` from |Y_Hub| and |Y_NetLink|).



.. _loadshedding_model:

Load shedding model
---------------------

The load shedding module parses the data model for the set of stage-hub-ec tuples :math:`\mathcal{S}_{LoadSheddingTuple} \subset \mathcal{S}_{Stage} \times \mathcal{S}_{Hub} \times \mathcal{S}_{Ec}` for which load shedding is enabled (as specified in |Y_Demand|). Naturally, these are only allowed to be tuples that are also associated with a demand profile, and a data validation procedure ensures this before the model is built. A load shedding variable

:raw-math:`$$ \mathcal{V}_{LoadShedding}: \mathcal{S}_{LoadShedding} \times \mathcal{S}_{Time} \to \mathbb{R}^+_0 $$`

measures the amount of demand that is chosen not be delivered by the system. This variable is constrained from above in the following way:

:raw-math:`$$ \begin{align*} \mathcal{V}_{LoadShedding}[s, h, e, t] \le \min \big( &max\_abs[s, h, e, t], \\ &max\_rel[s, h, e, t] \cdot demand[s, h, e, t] \big) \end{align*} $$`

where :math:`max\_abs`, :math:`max\_rel` and :math:`demand` are parameters from |Y_Demand|. Due to the integration of :math:`\mathcal{V}_{LoadShedding}` into the :ref:`energy system model<energy_system_model>`, the variable is not able to take values larger than :math:`\mathcal{V}_{Demand}`, thereby ensuring that the model is not able to shed more amounts than the actual demand. Additionally, a warning is logged if :math:`max\_rel` is set to a value larger than one to make the user aware of this circumstance.

Shedding loads is associated with certain costs. These are measure by the fixed variable

:raw-math:`$$ \begin{align*} \mathcal{V}_{LoadSheddingCost}: \mathcal{S}_{LoadShedding} &\to \mathbb{R}^+_0, \\ \mathcal{V}_{LoadSheddingCost}[s, h, e] &= \sum\limits_{t \in \mathcal{S}_{Time}} weight[s, t] \cdot energy\_cost[s, h, e, t] \cdot \mathcal{V}_{LoadShedding}[s, h, e, t] \end{align*} $$`

Here, :math:`energy\_cost` is a parameter from |Y_Demand| and :math:`weight` is a :ref:`clustering<clustering>` value. Inforomation about these costs are required in the :ref:`energy system model<energy_system_model>`. They are bundled in the following fixed variable for convenience:

:raw-math:`$$ \mathcal{V}_{LoadSheddingCostTotal} \in \mathbb R^+_0, \quad \mathcal{V}_{LoadSheddingCostTotal} = \sum\limits_{(s, h, e) \in \mathcal{S}_{LoadSheddingTuple}} \mathcal{V}_{LoadSheddingCost}[s, h, e] $$`



.. _loadshifting_model:

Load shifting model
---------------------

The load shifting module introduces a set of stage-hub-ec index tuples :math:`\mathcal{S}_{LoadShiftingTuple} \subset \mathcal{S}_{Stage} \times \mathcal{S}_{Hub} \times \mathcal{S}_{Ec}` for which load shifting is possible. The set is gathered from the load shifting entries defined in |Y_Demand|.

The variable

:raw-math:`$$ \mathcal{V}_{LoadShifting}: \mathcal{S}_{LoadShiftingTuple} \times \mathcal{S}_{Time} \to \mathbb{R} $$`

represents the amount of load shifting being performed at each time step, with positive values indicating an over-production of the ec and negative values indicating an under-production. We also use the terminology *above/below the demand curve* in connection to positive/negative load shifting values. The essential characteristic of any load shifting model is that no energy can be created or destroyed by it, only shifts along the time axis can occur. In ehubX, the way this characteristic is formulated is through *load shifting intervals*: The time horizon :math:`\mathcal{S}_{TimeHorizon}` is segmented into equidistant intervals

:raw-math:`$$ \begin{align*} \mathcal{S}_{TimeHorizon} &= \Big \{ \underbrace{1, ... , interval\_length}_{\mathcal{I}_1}, ~\underbrace{interval\_length + 1, ..., 2 \cdot interval\_length}_{\mathcal{I}_2}, ... \Big \} \\ &= \mathcal{I}_1 ~\cup~ \mathcal{I}_2 ~\cup~ ... ~\cup~ \mathcal{I}_N ~\cup~ \mathcal{R} \end{align*} $$`

Here, :math:`interval\_length` is a parameter from |Y_Demand| and :math:`\mathcal{R}` holds the remaining time indices at the end of the horizon that did not fit into an interval anymore. We now demand *neutrality* on each load shifting interval (:math:`n=1,...,N`) through the constraints

:raw-math:`$$ \begin{align*} \sum\limits_{t \in \mathcal{I}_n} \mathcal{V}_{LoadShifting}[s, h, e, cluster\_ts[s, t]] = 0 \end{align*} $$`

Here, :math:`cluster\_ts` is a :ref:`clustering<clustering>` value mapping giving us the cluster timestep that represents the horizon timestep :math:`t`. This constraint ensures that no energy can be created or destroyed within any load shifting interval. To also account for the remainder set :math:`\mathcal{R}`, we additionally introduce a *global neutrality condition*

:raw-math:`$$ \sum\limits_{t \in \mathcal{S}_{TimeHorizon}} \mathcal{V}_{LoadShifting}[s, h, e, cluster\_ts[s, t]] = 0 $$`

Be aware that because of the way clustering works, the above equality is equivalent to

:raw-math:`$$ \sum\limits_{t \in \mathcal{S}_{Time}} weight[s, t] \cdot \mathcal{V}_{LoadShifting} [s, h, e, t] = 0 $$`

where :math:`weight` is a :ref:`clustering<clustering>` value. The fact that both over-deliverance and under-deliverance of the demand curve is measured in the variable :math:`\mathcal{V}_{LoadShifting}` motivates a splitting of this variable into a positive and negative part. This is done by introducing two nonnegative variables

:raw-math:`$$ \mathcal{V}_{LoadShiftingAbove}, \mathcal{V}_{LoadShiftingBelow}: \mathcal{S}_{LoadShiftingTuple} \times \mathcal{S}_{Time} \to \mathbb{R}^+_0 $$`

These are connected to the main load shifting variable via the constraint

:raw-math:`$$ \mathcal{V}_{LoadShifting}[s, h, e, t] = \mathcal{V}_{LoadShiftingAbove}[s, h, e, t] - \mathcal{V}_{LoadShiftingBelow}[s, h, e, t] $$`

In a precise formulation, we would usually be forced to introduce an additional binary variable that tracks whether :math:`\mathcal{V}_{LoadShifting}` is positive or negative, allowing only one of the variables :math:`\mathcal{V}_{LoadShiftingAbove}` and :math:`\mathcal{V}_{LoadShiftingBelow}` to take nonzero values at a time. However, this would drastically increase the complexity of the model by the presence of a time-dependent binary variable. Instead, we rely on the fact that if certain costs (i.e.; the *energy costs* introduced below) are associated with the the above and below variables, an optimal solution will always try to avoid situations where both variables take nonzero values simulteneously. For example, take the case of :math:`\mathcal{V}_{LoadShifting}[s, h, e, t] = 3` which could be comprised of the following two value pairs for the sub-variables:

a) :math:`\mathcal{V}_{LoadShiftingAbove}[s, h, e, t] = 5` and :math:`\mathcal{V}_{LoadShiftingBelow}[s, h, e, t] = 2`
b) :math:`\mathcal{V}_{LoadShiftingAbove}[s, h, e, t] = 3` and :math:`\mathcal{V}_{LoadShiftingBelow}[s, h, e, t] = 0`

Without the presence of costs for the sub-variables, these two solutions would be identical for an optimization model. However, if :math:`\mathcal{V}_{LoadShiftingAbove}[s, h, e, t]` and :math:`\mathcal{V}_{LoadShiftingBelow}[s, h, e, t]` both enter in the problem's object function which is to be minimized, the optimizer will choose the second option to keep the sub-variable's values as small as possible. A similar reasoning as the one employed here is used in the :ref:`storage model<storage_model>` for the variables :math:`\mathcal{V}_{StorTechInflow}` and :math:`\mathcal{V}_{StorTechOutflow}`.

Next, let us introduce the fixed variables which quantify the energy costs we mentioned above:

:raw-math:`$$ \begin{align*} &\mathcal{V}_{LoadShiftingCostEnergy}: \mathcal{S}_{LoadShiftingTuple} \to \mathbb{R}, \\ &\mathcal{V}_{LoadShiftingCostEnergy}[s, h, e] = \sum\limits_{t \in \mathcal{S}_{LoadShiftingTuple}} \bigg( \\ &weight[s, t] \cdot \big( energy\_cost\_above[s, h, e, t] \cdot \mathcal{V}_{LoadShiftingAbove}[s, h, e, t] \\ &+ energy\_cost\_below[s, h, e, t] \cdot \mathcal{V}_{LoadShiftingBelow}[s, h, e, t] ) \bigg) \end{align*} $$`

Here, :math:`energy\_cost\_above` and :math:`energy\_cost\_below` are parameters from |Y_Demand| and :math:`weight` is a :ref:`clustering<clustering>` value. Because of the reasons explained above, a warning is written to the logfile if the energy cost parameters are chosen as zero.

Moving on to the next constraint, the maximum load shifting amounts above and below the demand curve may be bounded as follows:

:raw-math:`$$ \begin{align*} \mathcal{V}_{LoadShiftingAbove}[s, h, e, t] \le \min \big( &max\_above\_abs[s, h, e, t], \\ &max\_above\_rel[s, h, e, t] \cdot demand[s, h, e, t] \big) \\ \mathcal{V}_{LoadShiftingBelow}[s, h, e, t] \le \min \big( &max\_below\_abs[s, h, e, t], \\ &max\_below\_rel[s, h, e, t] \cdot demand[s, h, e, t] \big) \end{align*} $$`

The parameters :math:`max\_above\_abs`, :math:`max\_above\_rel`, :math:`max\_below\_abs` and :math:`max\_below\_rel` are input parameters of |Y_Demand|. A warning is included if :math:`max\_below\_rel` is larger than one since we cannot withhold more from the demand side than the actual demand itself.

Another limiting factor that is included in the load shifting module is a concept of available *capacity*, specified as a parameter in |Y_Demand|. This relates to the total energy that can be shifted either above or below the demand curve on each load shifting interval:

:raw-math:`$$ \sum\limits_{t \in \mathcal{I}_n} \mathcal{V}_{LoadShiftingAbove}[s, h, e, cluster\_ts[s, t]] \le capacity[s, h, e] $$`

Note that because of the interval neutrality condition, the above constraint is equivalent to

:raw-math:`$$ \sum\limits_{t \in \mathcal{I}_n} \mathcal{V}_{LoadShiftingBelow}[s, h, e, cluster\_ts[s, t]] \le capacity[s, h, e] $$`

Another kind of cost that can be attributed to the load shifting process is the peak amount of load shifting that ever occurs on the time horizon. In order to quantify this, we first need variables measuring the peak value in each direction:

:raw-math:`$$ \mathcal{V}_{LoadShiftingAbovePeak}, \mathcal{V}_{LoadShidftingBelowPeak}: \mathcal{S}_{LoadShiftingTuple} \to \mathbb{R}_0^+ $$`

If we want to maintain linearity of the model, we cannot simply set these variables to the maximum of :math:`\mathcal{V}_{LoadShiftingAbove}` and :math:`\mathcal{V}_{LoadShiftingBelow}`. Instead, we repeat the solution we already applied for the energy costs above. First, we set a bound in one direction as follows:

:raw-math:`$$ \begin{align*} \mathcal{V}_{LoadShiftingAbove}[s, h, e, t] &\le \mathcal{V}_{LoadShiftingAbovePeak}[s, h, e] \\ \mathcal{V}_{LoadShiftingBelow}[s, h, e, t] &\le \mathcal{V}_{LoadShiftingBelowPeak}[s, h, e] \end{align*} $$`

This will require the peak variables to be larger or equal to the largest shift-variables. Next, if the cost associated with the peak variables is nonzero, the optimizer will try to get them as small as possible, thereby forcing them to exactly the maximum value. We measure this cost by the fixed variable

:raw-math:`$$ \begin{align*} \mathcal{V}_{LoadShiftingCostPeak}: \mathcal{S}_{LoadShiftingTuple} \to &~\mathbb{R}, \\ \mathcal{V}_{LoadShiftingCostPeak}[s, h, e, t] = (&peak\_cost\_above[s, h, e] \cdot \mathcal{V}_{LoadShiftingAbovePeak}[s, h, e] \\ &peak\_cost\_below[s, h, e] \cdot \mathcal{V}_{LoadShiftingBelowPeak}[s, h, e]) \end{align*} $$`

Here, :math:`peak\_cost\_above` and :math:`peak\_cost\_below` are parameters taken from |Y_Demand|.

The third and last kind of cost that can be associated with load shifting is one that occurs every time any amount of load shifting occurs at all. For this to work, the model requires a binary variable that tracks when this is case:

:raw-math:`$$ \mathcal{V}_{YLoadShifting}: \mathcal{S}_{LoadShiftingTuple} \times \mathcal{S}_{Time} \to \{0, 1\} $$`

It has to be mentioned that adding this variable to the model might make it exceedingly harder to solve because of the multitude of binary decision variables that are involved. For this reason, ehubX only adds this variable when we need it, i.e.; if the *fix cost parameter* :math:`fix\_cost` from |Y_Demand| is given as a time series or if its default value is nonzero. In order to force this variable to 1 every time load shifting occurs, we require a big-M parameter :math:`BigM_{LoadShiftTotal}[s, h, e, t]` and the constraint

:raw-math:`$$ \mathcal{V}_{LoadShiftingAbove}[s, h, e, t] + \mathcal{V}_{LoadShiftingBelow}[s, h, e, t] \le BigM_{LoadShiftTotal}[s, h, e, t] \cdot \mathcal{V}_{YLoadShifting}[s, h, e, t] $$`

The big-M parameter needs to be larger than any value the left-hand side could possibly take. For our purposes, we choose the following value:

:raw-math:`$$ \begin{align*} BigM_{LoadShiftTotal}[s, h, e, t] = \min \Big( &max\_above\_abs[s, h, e, t], max\_above\_rel[s, h, e, t] \cdot demand[s, h, e, t], \\ &10 \cdot demand[s, h, e, t] \Big) \\ + \min \Big( &max\_below\_abs[s, h, e, t], max\_below\_rel[s, h, e, t] \cdot demand[s, h, e, t], \\ &demand[s, h, e, t] \Big) \end{align*} $$`

With the above constraint, :math:`\mathcal{V}_{YLoadShifting}` will always be 1 if :math:`\mathcal{V}_{LoadShifting}` is nonzero. Therefore, we can use it to specify the fixed cost variable

:raw-math:`\begin{align*} &\mathcal{V}_{LoadShiftingCostFix}: \mathcal{S}_{LoadShifting} \to \mathbb{R}^+_0 \\ &\mathcal{V}_{LoadShiftingCostFix}[s, h, e] = \sum\limits_{t \in \mathcal{S}_{Time}} weight[s, t] \cdot fix\_cost[s, h, e, t] \cdot \mathcal{V}_{YLoadShifting}[s, h, e, t] \end{align*}`

Since all costs must enter the :ref:`energy system model<energy_system_model>`, we create a single variable that holds the entire load shifting costs of the model:

:raw-math:`\begin{align*} \mathcal{V}_{LoadShiftingCostTotal} \in \mathbb{R}, \quad &\mathcal{V}_{LoadShiftingCostTotal} = \\ \sum\limits_{(s, h, e) \in \mathcal{S}_{LoadShiftingTuple}} \Big( &\mathcal{V}_{LoadShiftingCostEnergy}[s, h, e] + \mathcal{V}_{LoadShiftingCostPeak}[s, h, e] \\ &+ \mathcal{V}_{LoadShiftingCostFix}[s, h, e] \Big) \end{align*}`

.. _tech_model:

Technology model
------------------

Technologies are a main functionality of any energy hub model. In ehubX, the set of all technologies is given by :math:`\mathcal{S}_{Tech}`. A technology may only be eligible for certain stages (due to its *technology readiness level*, see :ref:`techs.yaml<techs_yaml>`) or for certain hubs (due to *tech_lists*, see :ref:`hubs.yaml<hubs_yaml>`). The stage-hub-tech tuples of all allowed combinations is captured in the set :math:`\mathcal{S}_{TechTuple} \subset \mathcal{S}_{Stage} \times \mathcal{S}_{Hub} \times \mathcal{S}_{Tech}`. It contains all tuples :math:`(s, h, x)` where

* The technology :math:`x` is ready in the stage :math:`s`, meaning the tech's TRL at the stage's start year is larger or equal to the TRL threshold defined in :ref:`stages.yaml<stages_yaml>`.
* The technology :math:`x` occurs in one of the tech lists of hub :math:`h`.

The key feature of technologies is that they have a certain capacity

:raw-math:`\begin{align*} \mathcal{V}_{TechCap}: \mathcal{S}_{TechTuple} \to \mathbb{R}_0^+ \end{align*}`

This variable measures in an abstract way the amount of installed assets for each technology in each allowed stage and hub. This is a good moment to mention that the technology module in ehubX operates in a sense like an abstract module, meaning that it has no way of actually contributing to the balance of any energy carrier. Instead, this functionality is performed by the technology submodules which are

* :ref:`conversion_model`,
* :ref:`storage_model`,
* :ref:`ebm_model`,
* :ref:`ates_model`,
* :ref:`heatpump_model`.

The way this works internally is that when a technology is added to a model (e.g.; a storage technology), an entry is added to both the technology module and the storage module. The entry in the storage module handles storage-specific behavior whereas the entry in the technology module governs the more general, technology-related functionality described in this section.

Coming back to the capacity variable, each technology submodule has its own physical interpretation of the capacity variable, specifically:

.. list-table:: Capacity variable for submodules
    :header-rows: 1

    * - Submodule
      - Physical meaning of capacity
      - Example unit
    * - Conversion
      - Output power
      - kW
    * - Storage
      - Maximal storable energy
      - kWh
    * - EBM
      - Total storage capacity
      - kWh
    * - ATES
      - TODO
      - TODO
    * - Heat pump
      - Condenser power
      - kW

Technology capacity is usually comprised of both *initial* technology (meaning it exists regardless of installation choices) and *installed* technology (chosen by the optimizer). The amount of installed technology is given by

:raw-math:`\begin{align*} \mathcal{V}_{TechCapInstl}: \mathcal{S}_{TechCap} \to \mathbb{R}_0^+ \end{align*}`

If a technology is installed in a certain stage, it will count towards the total capacity in this and future stages until its lifetime has run out. The same consideration has to be applied for initial technology whose lifetime will run out at a certain point as well. Therefore, a constraint exists which regulates the total available capacity considering initial and previous installation amounts:

:raw-math:`\begin{align*} \mathcal{V}_{TechCap}[s, h, x] = Cap_{init}[s, h, x] + \sum\limits_{\substack{s_{instl} \in \mathcal{S}_{Stage} \\ (s_{instl}, h, x) \in \mathcal{S}_{TechTuple}}} Cap_{instl}[s_{instl}, s, h, x] \end{align*}`

The initial capacity that is still operational in stage :math:`s` is given by

:raw-math:`\begin{align*} Cap_{init}[s, h, x] = \left \{ \begin{array}{rl} cap\_init[h, x], &\text{if } start\_year[s] - init\_year < lifetime[x] - age\_init[h, x] \\ 0, &\text{else} \end{array} \right . \end{align*}`

Here, :math:`cap\_init` and :math:`age\_init` are initial capacity parameters from :ref:`hubs_yaml`, :math:`start\_year` is the first year of a stage from :ref:`stages_yaml` and :math:`init\_year` is the start year of the first stage (earliest :math:`start\_year` in :ref:`stages_yaml`). The capacity installed in stage :math:`s_{instl}` that is still operational in stage :math:`s` is given by

:raw-math:`\begin{align*} Cap_{instl}[s_{instl}, s, h, x] = \left \{ \begin{array}{rl} \mathcal{V}_{TechCapInstl}[s_{instl}, h, x], &\text{if } 0 \le start\_year[s] - start\_year[s_{instl}] < lifetime[x] \\ 0, &\text{else} \end{array} \right . \end{align*}`

For the upcoming variable :math:`\mathcal{V}_{TechCostCapex}`, we require a binary variable that measures whether any amount of technology was installed at all. This variable is given by

:raw-math:`\begin{align*} \mathcal{V}_{YTechCapInstl}: \mathcal{S}_{TechTuple} \to \{0, 1\} \end{align*}`

This is achieved by a bigM constraint

:raw-math:`\begin{align*} \mathcal{V}_{TechCapInstl}[s, h, x] \le BigM_{TechCap}[s, h, x] \cdot \mathcal{V}_{YTechCapInstl}[s, h, x] \end{align*}`

where the big-M parameter has to provide an upper bound to the technology capacity and is chosen as

:raw-math:`\begin{align*} BigM_{TechCap}[s, h, x] = \left \{ \begin{array}{rl} cap\_max[s, h, x] + 10^{-5}, &\text{if } cap\_max[s, h, x] < \infty \\ \mathcal{P}_{BigMGeneric}, &\text{else} \end{array} \right . \end{align*}`

Here, :math:`cap\_max` is the maximal capacity parameter from :ref:`hubs_yaml` and :math:`{P}_{BigMGeneric}` is the demand-based default big-M parameter introduced in the :ref:`demand model<demand_model>`.

Similar to :math:`\mathcal{V}_{YTechCapInstl}`, we require another binary variable to monitor whether a certain technology was *used* at all, later used for the cost variable :math:`\mathcal{V}_{TechCostOpexCap}`. This variable is declared in the technology module as

:raw-math:`\begin{align*} \mathcal{V}_{YTechUsed}: \mathcal{S}_{TechTuple} \to \{0, 1 \} \end{align*}`

Since the concept of *usage* may mean something different depending on the type of technology, each submodule declares its own constraint that ties this variable to a specific behavior pattern.

Technology capacity is possibly subject to some constraint based on the input parameters, starting with :math:`unit\_cap\_min` from :ref:`techs_yaml`:

:raw-math:`\begin{align*} \mathcal{V}_{TechCapInstl}[s, h, x] \ge unit\_cap\_min[s, x] \cdot \mathcal{V}_{YTechCapInstl}[s, h, x] \end{align*}`

Another set of parameters that limits the capacity are :math:`cap\_min` and :math:`cap\_max` from :ref:`hubs_yaml`:

:raw-math:`\begin{align*} cap\_min[s, h, x] \le \mathcal{V}_{TechCap}[s, h, x] \le cap\_max[s, h, x] \end{align*}`

Furthermore, there is the parameter :math:`last_inst_year` from :ref:`techs_yaml` which may forbid any installation after that year:

:raw-math:`\begin{align*} \mathcal{V}_{YTechCapInstl}[s, h, x] = 0 \text{ if } start\_year[s] > last\_instl\_year[x] \end{align*}`

For technologies, we allow the concept of *coupled technologies* (based on the section *coupling\_params* in :ref:`techs_yaml`). All technologies with this field are collected in a subset :math:`\mathcal{S}_{SubTech} \subset \mathcal{S}_{Tech}` and every :math:`x \in \mathcal{S}_{SubTech}` is assigned a :math:`main\_tech\_id[x] \in \mathcal{S}_{Tech}` with their associated main technology, and a :math:`cap\_factor[x] \in \mathbb{R}^+_0` describing the factor relating the capacities between this tech and their main tech:

:raw-math:`\begin{align*} \mathcal{V}_{TechCap}[s, h, x] = cap\_factor[x] \cdot \mathcal{V}_{TechCap}[s, h, main\_tech\_id[x]] \end{align*}`

Certain costs are connected to the technology model, such as CAPEX costs:

:raw-math:`\begin{align*} \mathcal{V}_{TechCostCapex}: \mathcal{S}_{TechTuple} &\to \mathbb{R}, \\ \mathcal{V}_{TechCostCapex}[s, h, x] &= CRF(interest\_rate[x], lifetime[x]) \cdot \sum\limits_{\substack{s_{instl} \in \mathcal{S}_{Stage} \\ (s_{instl}, h, x) \in \mathcal{S}_{TechTuple}}} Capex_{Stage}[s_{instl}, s, h, x] \end{align*}`

Here :math:`CRF` is a standard *capital recovery factor* calculated from the technology's lifetime and interest rate as follows:

:raw-math:`\begin{align*} CRF(i, N) = \frac{i \cdot (i+1)^N}{(i+1)^{N-1}} \end{align*}`

The summand takes the following form:

:raw-math:`\begin{align*} Capex_{Stage}[s_{instl}, s, h, x] ~=~ \left \{ \begin{array}{rl} capex\_per\_cap[s, x] \cdot \mathcal{V}_{TechCapInstl}[s_{instl}, h, x] & \\ +~ one\_time\_capex[s, x] \cdot \mathcal{V}_{YTechCapInstl}[s_{instl}, h, x], &\text{if } 0 \le start\_year[s] - start\_year[s_{instl}] < lifetime[x] \\ 0, &\text{else} \end{array} \right . \end{align*}`

Here, :math:`capex\_per\_cap` and :math:`one\_time\_capex` are parameters from :ref:`techs_yaml`.

In addition to these installation-related CAPEX costs, operating and maintaining the technologies is associated with the *OPEX costs* parametrized by :math:`opex\_per\_cap` and :math:`one\_time\_opex` from :ref:`techs_yaml`:

:raw-math:`\begin{align*} \mathcal{V}_{TechCostOpexCap}: \mathcal{S}_{TechTuple} &\to \mathbb{R}, \\ \mathcal{V}_{TechCostOpexCap}[s, h, x] &= opex\_per\_cap[s, x] \cdot \mathcal{V}_{TechCap}[s, h, x] + one\_time\_opex[s, x] \cdot \mathcal{V}_{YTechUsed}[s, h, x] \end{align*}`

As can be seen, both costs have a part that arises per amount of installed capacity while another enters any time any amount of technology is installed or used at all. Adding up these costs gives us the following fixed variable:

:raw-math:`\begin{align*} \mathcal{V}_{TechCostTotal} &\in \mathbb{R}, \\ \mathcal{V}_{TechCostTotal} &= \sum\limits_{(s, h, x) \in \mathcal{S}_{TechTuple}} \big( \mathcal{V}_{TechCostCapex}[s, h, x] + \mathcal{V}_{TechCostOpexCap}[s, h, x] \big) \end{align*}`

Similar to the costs associated with tech installation, certain CO2-embodied emissions are associated with this process as well. We collect these in the variable

:raw-math:`\begin{align*} \mathcal{V}_{TechCo2Instl}: \mathcal{S}_{TechTuple} &\to \mathbb{R} \\ \mathcal{V}_{TechCo2Instl}[s, h, x] &= \sum\limits_{\substack{s_{instl} \in \mathcal{S}_{Stage} \\ (s_{instl}, h, x) \in \mathcal{S}_{TechTuple} \\ 0 \le start\_year[s] - start\_year[s_{instl}] \le lifetime[x]}} \frac{co2\_per\_cap[s, x]}{lifetime[x]} \cdot \mathcal{V}_{TechCapInstl}[s_{instl}, h, x] \end{align*}`

The parameter :math:`co\_per\_cap` comes from the :ref:`techs_yaml` file. As with the costs, we gather the total amount of CO2 emissions into a fixed variable for convenience:

:raw-math:`\begin{align*} \mathcal{V}_{TechCo2Total}: \mathcal{S} \to \mathbb{R}, \qquad \mathcal{V}_{TechCo2Total}[s] = \sum\limits_{\substack{(s', h, x) \in \mathcal{S}_{TechTuple} \\ s = s'}} \mathcal{V}_{TechCo2Instl}[s', h, x] \end{align*}`


.. _conversion_model:

Conversion model
------------------

The *conversion model* defines its own set of tech tuples

:raw-math:`\begin{align*} \mathcal{S}_{ConvTechTuple} = \big \{ (s, h, x) \in \mathcal{S}_{TechTuple}: ~ x \text{is a conversion technology } \big \} \end{align*}`

In addition, a conversion technology may have multiple input and output ecs, as defined in :ref:`techs_yaml` and illustrated below for an example with three inputs and two outputs:

.. image:: img/conversion_scheme.png
   :width: 400
   :alt: Schematics of a conversion technology with three inputs and two outputs

The model defines sets of input and output combinations

:raw-math:`\begin{align*} \mathcal{S}_{ConvTechIn} &= \big \{ (s, h, x, e): (s, h, x) \in \mathcal{S}_{ConvTechTuple}, e \text{ is in_ec of x } \big \} \\ \mathcal{S}_{ConvTechOut} &= \big \{ (s, h, x, e): (s, h, x) \in \mathcal{S}_{ConvTechTuple}, e \text{ is out_ec of x } \big \} \end{align*}`

Based on these sets, the following variables track intakes and outputs of conversion technologies at every time step:

:raw-math:`\begin{align*} \mathcal{V}_{ConvTechIn}: \mathcal{S}_{ConvTechIn} \times \mathcal{S}_{Time} &\to \mathbb{R}_0^+ \\ \mathcal{V}_{ConvTechOut}: \mathcal{S}_{ConvTechOut} \times \mathcal{S}_{Time} &\to \mathbb{R}_0^+ \end{align*}`

On the intake side, the ec amounts stand in a fixed relation to each other, expressed by the constraint

:raw-math:`\begin{align*} \mathcal{V}_{ConvTechIn}[s, h, x, e, t] = in\_part[s, x, e] \cdot \sum\limits_{\substack{e' \in \mathcal{S}_{Ec} \\ (s, h, x, e') \in \mathcal{S}_{ConvTechIn}}} \mathcal{V}_{ConvTechIn}[s, h, x, e', t] \end{align*}`

where :math:`in\_part` is a parameter defined in :ref:`techs_yaml`. Similarily, the output amounts of each output ec are specified based on the efficiency parameter :math:`out\_eff` from :ref:`techs_yaml` which relates to the input of the main input ec :math:`main\_in\_ec`:

:raw-math:`\begin{align*} \mathcal{V}_{ConvTechOut}[s, h, x, e, t] = out\_eff[s, x, e, t] \cdot \mathcal{V}_{ConvTechIn}[s, h, x, main\_in\_ec[x], t] \end{align*}`

From the :ref:`tech model<tech_model>`, we still have to define a constraint that determines the *usage* of a conversion technology.

:raw-math:`\begin{align*} \sum\limits_{t \in \mathcal{S}_{Time}} weight[s, t] \cdot \mathcal{V}_{ConvTechOut}[s, h, x, main\_out\_ec[x], t] \le BigM_{ConvMainOutSum}[s, h, x] \cdot \mathcal{V}_{YTechUsed}[s, h, x] \end{align*}`

Here, :math:`weight` is a :ref:`clustering<clustering>` value and :math:`BigM_{ConvMainOutSum}[s, h, x]` is a big-M parameter which has to provide an upper bound to the summed-up output of the conversion technology's main output ec over the time horizon. It is chosen as

:raw-math:`\begin{align*} BigM_{ConvMainOutSum}[s, h, x] = \left \{ \begin{array}{rl} out\_sum\_max[s, h, x], &\text{if } out\_sum\_max[s, h, x] < \infty \\ cap\_max[s, h, x] \cdot |\mathcal{S}_{TimeHorizon}| + 10^{-5}, &\text{elif } cap\_max[s, h, x] < \infty \\ \mathcal{P}_{BigMGeneric}, &\text{else} \end{array} \right . \end{align*}`

We recall that :math:`{P}_{BigMGeneric}` is the demand-based default big-M parameter introduced in the :ref:`demand model<demand_model>`. Furthermore, :math:`out\_sum\_max` and `:math:`cap\_max` are parameters from :ref:`hubs_yaml`.

The amount of output a conversion technology can generate is not only limited by the :ref:`technology model<tech_model>`'s *capacity*` but also by the *availability* parameter from :ref:`hubs_yaml`. Since availability works as a percentage value, the constraint for this restriction looks as follows:

:raw-math:`\begin{align*} \mathcal{V}_{ConvTechOut}[s, h, x, main\_out\_ec, t] \le availability[s, h, x, t] \cdot \mathcal{V}_{TechCap}[s, h, x] \end{align*}`

Note that restricting the :math:`main\_out\_ec` (see :ref:`techs_yaml`), all other output ecs are restricted accordingly due to the input-output dynamics defined above.

The :ref:`techs_yaml` offers the parameter :math:`out\_sum\_min` and :math:`out\_sum\_max` to limit the output amounts of the main output ec over the entire time horizon. Using the parameter :math:`weight` from the :ref:`clustering` logic, this is formulated as follows:

:raw-math:`\begin{align*} out\_sum\_min[s, h, x] \le \sum\limits_{t \in \mathcal{S}_{Time}} weight[s, t] \cdot \mathcal{V}_{ConvTechOut}[s, h, x, out\_ec\_main[x], t] \le out\_sum\_max[s, h, x] \end{align*}`

Lastly, the conversion technology model has its own cost concept in addition to the costs defined in the :ref:`tech model<tech_model>`, namely OPEX costs that arise proportionally to the amount of energy that is being output by the conversion technologies. The calculation of these costs uses the cost parameter :math:`opex\_per\_energy` from :ref:`techs_yaml`:

:raw-math:`\begin{align*} \mathcal{V}_{ConvTechCostOpexOut}&: \mathcal{S}_{ConvTechTuple} \to \mathbb{R}, \\ \mathcal{V}_{ConvTechCostOpexOut}[s, h, x] &= \sum\limits_{\substack{e \in \mathcal{S}_{Ec} \\ (s, h, x, e) \in \mathcal{S}_{ConvTechOut}}} opex\_per\_energy[s, h, x] \cdot \sum\limits_{t \in \mathcal{S}_{Time}} weight[s, t] \cdot \mathcal{V}_{ConvTechOut}[s, h, x, e, t] \end{align*}`

Finally, all costs in the conversion model (i.e.; only the energy-related OPEX costs above) are bundled into a single variable for convenient use outside of the conversion module:

:raw-math:`\begin{align*} \mathcal{V}_{ConvTechCostTotal} &\in \mathbb{R}, \\ \mathcal{V}_{ConvTechCostTotal} &= \sum\limits_{(s, h, x) \in \mathcal{S}_{ConvTechTuple}} \mathcal{V}_{ConvTechCostOpexOut}[s, h, x] \end{align*}`

.. _solar_model:

Solar model
-------------

*Solar technologies* are a special case of conversion technologies, converting solar irradiation into electrical power. The conversion model defines its own set of tech tuples

:raw-math:`\begin{align*} \mathcal{S}_{SolarTechTuple} = \big \{ (s, h, x) \in \mathcal{S}_{ConvTechTuple}: x \text{ is a solar technology} \big \} \end{align*}`

Additionally, solar technologies may only have a single energy carrier which is the solar irradition. Within this section, we therefore simply write :math:`e_{sol}[x]` for this energy carrier. If a conversion technology with more than one input ec is designated as solar, ehubX will throw an exception.

The main input variable associated with solar technologies is the *solar tech incident* which relates to the total amount of solar irradiation that is collected through the installed technology, as follows:

:raw-math:`\begin{align*} \mathcal{V}_{SolarTechIncident}[s, h, x, t] = solar\_irradiation[s, e_{sol}[x], t] \cdot \mathcal{V}_{TechCap}[s, h, x] \end{align*}`

The parameter :math:`solar\_irradiation` comes from the file :ref:`solar_irradiation_csv` which contains an irradiation amount per :math:`m^2` which is why the capacity variable :math:`\mathcal{V}_{TechCap}` for solar technologies is understood in :math:`m^2` as well. In order for this to work, the solar model disables the conversion-specific capacity limitation constraint (there understood in :math:`kW`) and defines its own version of this as follows:

:raw-math:`\begin{align*} \mathcal{V}_{ConvTechIn}[s, h, x, e_{sol}[x], t] \le availability[s, h, x, t] \cdot \mathcal{V}_{SolarTechIncident}[s, h, x, t] \end{align*}`

In contrast to the conversion model, it is the single input ec which is limited proportionally by the availability. Another difference lies in the fact that production of solar electricity can not always be freely chosen between zero and the upper limit from the previous constraint. Instead, *curtailment* must be employed to down-regulate the production of PV panels which is subject to the parameter :math:`curtail\_max\_rel` from :ref:`techs_yaml`:

:raw-math:`\begin{align*} \mathcal{V}_{ConvTechIn}[s, h, x, e_{sol}[x], t] \ge (1 - curtail\_max\_rel[s, x]) \cdot availability[s, h, x, t] \cdot \mathcal{V}_{SolarTechIncident}[s, h, x, t] \end{align*}`

Finally, we need to limit installed solar capacity (i.e.; area) by the total available area as defined in the file :ref:`solar_areas_csv`. This file is parsed into a parameter :math:`solar\_area` for which the following constraint has to hold:

:raw-math:`\begin{align*} \sum\limits_{\substack{x \in \mathcal{S}_{Tech} \\ (s, h, x) \in \mathcal{S}_{SolarTechTuple} \\ e = e_{sol}[x]}} \mathcal{V}_{TechCap}[s, h, x] \le solar\_area[s, h, e] \end{align*}`

.. _wind_model:

Wind model
------------

Test


.. _storage_model:

Storage model
---------------

.. image:: img/storage_scheme.png
   :width: 200
   :alt: Schematics of a storage technology and its ec

The *storage model* defines its own set of technologies

:raw-math:`\begin{align*} \mathcal{S}_{StorTech} = \big \{ x \in \mathcal{S}_{Tech}: ~ x \text{is a storage technology } \big \} \end{align*}`

and *storage tech tuples*

:raw-math:`\begin{align*} \mathcal{S}_{StorTechTuple} = \big \{ (s, h, x) \in \mathcal{S}_{TechTuple}: ~ x \in \mathcal{S}_{StorTech} \big \} \end{align*}`

In addition, a storage technology has exactly one ec that can be stored, defined as the parameter

:raw-math:`\begin{align*} \mathcal{P}_{StorTechEc}: \mathcal{S}_{StorTech} \to \mathcal{S}_{Ec} \end{align*}`

This mapping from storage technology to ec works using the parameter :math:`ec` from the section :math:`storage_params` in :ref:`techs_yaml`. During every time step, a storage technology is able to charge and discharge its stored ec using the variables

:raw-math:`\begin{align*} \mathcal{V}_{StorTechInflow}, \mathcal{V}_{StorTechOutflow}: \mathcal{S}_{StorTechTuple} \times \mathcal{S}_{Time} \to \mathbb{R}_0^+ \end{align*}`

The extent to which this is possible can be limited by the parameters :math:`charge\_max` and :math:`discharge\_max` from :ref:`techs_yaml`:

:raw-math:`\begin{align*} \mathcal{V}_{StorTechInflow}[s, h, x, t] &\le charge\_max[s, x] \cdot \mathcal{V}_{TechCap}[s, h, x] \\ \mathcal{V}_{StorTechOutflow}[s, h, x, t] &\le discharge\_max[s, x] \cdot \mathcal{V}_{TechCap}[s, h, x] \end{align*}`

Recall that :math:`\mathcal{V}_{TechCap}` is the total installed capacity from the :ref:`tech model<tech_model>` which, in case of the storage model, takes on the meaning of *storage capacity*, i.e.; total storable energy. Therefore, setting e.g. the parameter :math:`charge\_max` to 0.1 means that the storage technology would be able to charge by 10% of its total storage capacity at every time step, therefore it would take at least 10 time step to fully charge the storage.

The charging and discharging amounts can also be used to determine whether a storage technology was *used* in the sense of the :ref:`tech model<tech_model>` by adding the constraint

:raw-math:`\begin{align*} \sum\limits_{t \in \mathcal{S}_{Time}} weight[s, t] (\mathcal{V}_{StorTechInflow}[s, h, x, t] + \mathcal{V}_{StorTechOutflow}[s, h, x, t]) \le BigM_{StorTotalFlow}[s, h, x] \cdot \mathcal{V}_{YTechUsed}[s, h, x] \end{align*}`

Ideally, we would like to make use of the :math:`charge\_max` and :math:`discharge\_max` parameters for :math:`BigM_{StorTotalFlow}[s, h, x]` and therefore choose the following form:

:raw-math:`\begin{align*} BigM_{StorTotalFlow}[s, h, x] = \left \{ \begin{array}{rl} 10^{-5} + cap\_max[s, h, x] \cdot \big( \min(charge\_max[s, x], ~1) + &\\ \min(discharge\_max[s, x], ~1) \big) \cdot |\mathcal{S}_{TimeHorizon}|, &\text{if } cap\_max[s, h, x] < \infty \\ \mathcal{P}_{BigMGeneric}, &\text{else} \end{array} \right . \end{align*}`

Next, we introduce a *storage energy* variable to the model which keeps track of how much energy is currently stored in a storage technology:

:raw-math:`\begin{align*} \mathcal{V}_{StorTechEnergy}: \mathcal{S}_{StorTechTuple} \times \mathcal{S}_{TimeHorizon} \to \mathbb{R}_0^+ \end{align*}`

Note that this variable is not defined on the (possibly clustered) time domain :math:`\mathcal{S}_{Time}` but on the full time horizon :math:`\mathcal{S}_{TimeHorizon}`. This is done because the dynamics imposed on the variable will rely on comparing adjacent time steps, something that is not possible for clustered time steps. The storage energy's evolution is subject to a standby loss and the charging and discharging process:

:raw-math:`\begin{align*} \mathcal{V}_{StorTechEnergy}[s, h, x, t_h^+] = &(1 - standby\_loss[s, x]) \cdot \mathcal{V}_{StorTechEnergy}[s, h, x, t_h] \\ &+ in\_eff[s, x] \cdot \mathcal{V}_{StorTechInflow}[s, h, x, t\_cl[t_h]] - out\_eff[s, x]^{-1} \cdot \mathcal{V}_{StorTechOutflow}[s, h, x, t\_cl[t_h]] \end{align*}`

The parameters :math:`standby\_loss`, :math:`in\_eff` and :math:`out_eff` come from :ref:`techs_yaml`. It is important to note that the above constraint is formulated for every horizon time step :math:`t_h \in \mathcal{S}_{TimeHorizon}`. We have used the parameter :math:`t\_cl[t_h]` from the :ref:`clustering` procedure which assigns every horizon time step :math:`t_h` to its clustering time step. There is also the concept of a *next* time step which we define as

:raw-math:`\begin{align*} t_h^+ = \left \{ \begin{array}{rl} \text{first horizon time step}, &\text{if } t_h \text{ is the last horizon time step } \\ \text{horizon time step after } t_h, &\text{else} \end{array} \right . \end{align*}`

This way, we use a *circular* time model so no storage energy can be procued or destroyed over the time horizon. This assumption is fairly common in energy system models where no long-term energy storage effects have to be taken into account. For example, if the time horizon :math:`\mathcal{S}_{TimeHorizon}` encompasses a single year, storage technologies will be able to shift around energy throughout the year but not over multiple years.

The storage energy levels are additionally constrained by the parameters :math:`soc\_min` and :math:`soc\_max` from :math:`techs_yaml`:

:raw-math:`\begin{align*} soc\_min[s, x] \cdot \mathcal{V}_{TechCap}[s, h, x] \le \mathcal{V}_{StorTechEnergy}[s, h, x, t_h] \le \min(soc\_max[s, x], 1) \cdot \mathcal{V}_{TechCap}[s, h, x] \end{align*}`

For a final consideration, the energy storage level is currently able to 'start' at any initial value on the time horizon but has to follow the prescribed dynamics afterwards. Depending on the model at hand, this behavior may be desirable or we may want to set an initial value for the storage level. ehubX handles this by considering the parameter :math:`soc\_init` from :ref:`hubs_yaml`: If this parameter is infinite (which is its default value), no constraint will be set. Otherwise, the parameter will be used to fix the initial energy storage value:

:raw-math:`\begin{align*} \mathcal{V}_{StorTechEnergy}[s, h, x, t_{h,0}] = \left \{ \begin{array}{rl} \mathcal{V}_{StorTechEnergy}[s_0, h, x, t_{h,0}], &\text{if } s \neq s_0 \\ soc\_init[h, x] \cdot \mathcal{V}_{TechCap}[s, h, x], &\text{if } s = s_0 \text{ and } soc\_init[h, x] < \infty \end{array} \right . \end{align*}`

Here, :math:`s_0 \in \mathcal{S}_{Stage}` is the *first* stage in the model, i.e.; the one with the smallest :math:`start\_year`, and :math:`t_{h,0} \in \mathcal{S}_{TimeHorizon}` is the initial horizon time step. Note that regardless of whether an initial energy level is set in the first stage, the model has to maintain the same initial storage level across all stages.

It has to be mentioned at this point that the chosen storage formulation would allow for simultaneous inflow and outflow from the storage technology (i.e.; :math:`mathcal{V}_{StorTechInflow}[s, h, x, t] > 0` and :math:`mathcal{V}_{StorTechOutflow}[s, h, x, t] > 0`). It is generally possible to avoid this by introducing a time-dependent binary variable which monitors whether a charging or discharing process is taking place at the current time step. However, this drastically increases the complexity of the resulting MILP problem which is why ehubX decides to avoid this. Instead, we rely on the fact that if certain costs are associated with the flow variables, an optimal solution will always try to avoid situations where both variables take nonzero values simulteneously. For example, take the case of :math:`\mathcal{V}_{StorTechOutflow} - \mathcal{V}_{StorTechInflow} = 3` which could be comprised of the following two value pairs for the sub-variables:

a) :math:`\mathcal{V}_{StorTechOutflow}[s, h, e, t] = 5` and :math:`\mathcal{V}_{StorTechInflow}[s, h, e, t] = 2`
b) :math:`\mathcal{V}_{StorTechOutflow}[s, h, e, t] = 3` and :math:`\mathcal{V}_{StorTechInflow}[s, h, e, t] = 0`

If obtaining an amount of the ec :math:`e` is associated with certain cost within the energy system (e.g.; through costs in the :ref:`import model<import_model>`) and either the parameters :math:`in\_eff[s, x]` or :math:`out\_eff[s, x]` are smaller than 1, it will be undesirable from a mathematical perspective to operate the storage technology more than necessary, meaning the case b) above would be preferred to a). A similar reasoning as the one employed here is used in the :ref:`load shifting model<loadshifting_model>` for the variables :math:`\mathcal{V}_{LoadShiftingAbove}` and :math:`\mathcal{V}_{LoadShiftingBelow}`.


.. _ebm_model:

EBM model
-----------

First, we note that the electricity-based mobility (EBM) technology shares a lot of design overlap with the :ref:`storage model<storage_model>` since electric vehicles can essentially be thought of as batteries with an added consumption behavior.

.. image:: img/ebm_scheme.png
   :width: 200
   :alt: Schematics of an EBM technology and its ec

The *EBM model* defines its own set of technologies

:raw-math:`\begin{align*} \mathcal{S}_{EbmTech} = \big \{ x \in \mathcal{S}_{Tech}: ~ x \text{is an EBM technology } \big \} \end{align*}`

and *EBM tech tuples*

:raw-math:`\begin{align*} \mathcal{S}_{EbmTechTuple} = \big \{ (s, h, x) \in \mathcal{S}_{TechTuple}: ~ x \in \mathcal{S}_{EbmTech} \big \} \end{align*}`

The first deviation from the storage technology comes from the fact that the capacity of the EBM fleet is a fixed value that cannot be changed by the optimizer, originating from the parameters *num_vehicles* (from :ref:`hubs_yaml`) and *storage_cap* (from :ref:`techs_yaml`):

:raw-math:`\begin{align*} \mathcal{V}_{TechCap}[s, h, x] = num\_vehicles[s, h, x] \cdot storage\_cap[s, x] \end{align*}`

All capacity-related parameters from the :ref:`technology model<tech_model>` can still be specified and will work as intended yet their values will have no outcome on the optimization results. Note specifically that if no *cap_init* is specified in :ref:`hubs_yaml`, ehubX will install the necessary capacity itself, thereby modifying the total system cost.

Moving on, an EBM technology has exactly one ec that operates it, defined as the parameter

:raw-math:`\begin{align*} \mathcal{P}_{EbmTechEc}: \mathcal{S}_{EbmTech} \to \mathcal{S}_{Ec} \end{align*}`

This mapping from EBM technology to ec works using the parameter :math:`ec` from the section :math:`ebm_params` in :ref:`techs_yaml`. During every time step, an EBM technology can charge and discharge its stored ec using the variables

:raw-math:`\begin{align*} \mathcal{V}_{EbmTechInflow}, \mathcal{V}_{EbmTechOutflow}: \mathcal{S}_{EbmTechTuple} \times \mathcal{S}_{Time} \to \mathbb{R}_0^+ \end{align*}`

The extent to which this is possible is firstly limited by the parameters :math:`charge\_max` and :math:`discharge\_max` from :ref:`techs_yaml`. Second, the time-dependent parameter *availability* from :ref:`hubs_yaml` specifies the percentage of the fleet that is available for charging and discharging at any given point. Third and final, the parameter *discharge_controllability* from :ref:`techs_yaml` further dampens the fleet's ability to discharge at will. This results in the following constraints:

:raw-math:`\begin{align*} \mathcal{V}_{EbmTechInflow}[s, h, x, t] &\le num\_vehicles[s, h, x] \cdot availability[s, h, x] \cdot charge\_max[s, x] \\ \mathcal{V}_{StorTechOutflow}[s, h, x, t] &\le num\_vehicles[s, h, x] \cdot availability[s, h, x] \cdot discharge\_controllability[s, x] \cdot discharge\_max[s, x] \end{align*}`

The charging and discharging amounts can also be used to determine whether an EBM technology was *used* in the sense of the :ref:`tech model<tech_model>` by adding the constraint

:raw-math:`\begin{align*} \sum\limits_{t \in \mathcal{S}_{Time}} weight[s, t] (\mathcal{V}_{EbmTechInflow}[s, h, x, t] + \mathcal{V}_{EbmTechOutflow}[s, h, x, t]) \le BigM_{EbmTotalFlow}[s, h, x] \cdot \mathcal{V}_{YTechUsed}[s, h, x] \end{align*}`

Due to the constraints above this, the big-M parameter can be chosen as

:raw-math:`\begin{align*} BigM_{EbmTotalFlow}[s, h, x] = &10^{-5} +  num\_vehicles[s, h, x] \cdot \Big( \min(charge\_max[s, x], storage\_cap[s, x])  \\ &+ \min(discharge\_max[s, x], storage\_cap[s, x]) \Big) \cdot |\mathcal{S}_{TimeHorizon}| \end{align*}`

To avoid the case where :math:`charge\_max` or :math:`discharge\_max` are infinite, we have made additional use of the fact that an electric vehicle can never charge or discharge more than its storage capacity :math:`storage\_cap` in a single timestep due to model limitations.

Next, we introduce an *energy* variable to the model which keeps track of how much energy is currently stored in the entire EBM fleet:

:raw-math:`\begin{align*} \mathcal{V}_{EbmTechEnergy}: \mathcal{S}_{EbmTechTuple} \times \mathcal{S}_{TimeHorizon} \to \mathbb{R}_0^+ \end{align*}`

Note that this variable is not defined on the (possibly clustered) time domain :math:`\mathcal{S}_{Time}` but on the full time horizon :math:`\mathcal{S}_{TimeHorizon}`. This is done because the dynamics imposed on the variable will rely on comparing adjacent time steps, something that is not possible for clustered time steps. The storage energy's evolution is subject to a standby loss, the charging and discharging process and the fleet's energy consumption due to the demand:

:raw-math:`\begin{align*} \mathcal{V}_{EbmTechEnergy}[s, h, x, t_h^+] = &(1 - standby\_loss[s, x]) \cdot \mathcal{V}_{EbmTechEnergy}[s, h, x, t_h] \\ &+ in\_eff[s, x] \cdot \mathcal{V}_{EbmTechInflow}[s, h, x, t\_cl[t_h]] - out\_eff[s, x]^{-1} \cdot \mathcal{V}_{EbmTechOutflow}[s, h, x, t\_cl[t_h]] \\ &- num\_vehicles[s, h, x] \cdot demand\_modifier[s, h, x] \cdot demand\_nominal[s, h, x, t] \end{align*}`

The parameters :math:`standby\_loss`, :math:`in\_eff` and :math:`out_eff` come from :ref:`techs_yaml` whereas  :math:`num\_vehicles`, :math:`demand_modifier` and :math:`demand_nominal` can be specified in :ref:`hubs_yaml`. It is important to note that the above constraint is formulated for every horizon time step :math:`t_h \in \mathcal{S}_{TimeHorizon}`. We have used the parameter :math:`t\_cl[t_h]` from the :ref:`clustering` procedure which assigns every horizon time step :math:`t_h` to its clustering time step. There is also the concept of a *next* time step which we define as

:raw-math:`\begin{align*} t_h^+ = \left \{ \begin{array}{rl} \text{first horizon time step}, &\text{if } t_h \text{ is the last horizon time step } \\ \text{horizon time step after } t_h, &\text{else} \end{array} \right . \end{align*}`

This way, we use a *circular* time model so no EBM energy can be procued or destroyed over the time horizon. This assumption is fairly common in energy system models where no long-term energy storage effects have to be taken into account.

The EBM energy levels are additionally constrained by the parameters :math:`soc\_min` and :math:`soc\_max` from :math:`techs_yaml`:

:raw-math:`\begin{align*} \mathcal{V}_{EbmTechEnergy}[s, h, x, t_h] &\ge soc\_min[s, x] \cdot num\_vehicles[s, h, x] \cdot storage\_cap[s, x] \\ \mathcal{V}_{EbmTechEnergy}[s, h, x, t_h] &\le soc\_max[s, x] \cdot num\_vehicles[s, h, x] \cdot storage\_cap[s, x] \end{align*}`

For a final consideration, the energy level is currently able to 'start' at any initial value on the time horizon but has to follow the prescribed dynamics afterwards. Depending on the model at hand, this behavior may be desirable or we may want to set an initial value for the energy level. ehubX handles this by considering the parameter :math:`soc\_init` from :ref:`hubs_yaml`: If this parameter is infinite (which is its default value), no constraint will be set. Otherwise, the parameter will be used to fix the initial energy storage value:

:raw-math:`\begin{align*} \mathcal{V}_{EbmTechEnergy}[s, h, x, t_{h,0}] = \left \{ \begin{array}{rl} \mathcal{V}_{EbmTechEnergy}[s_0, h, x, t_{h,0}], &\text{if } s \neq s_0 \\ soc\_init[h, x] \cdot num\_vehicles[s, h, x] \cdot storage\_cap[s, x], &\text{if } s = s_0 \text{ and } soc\_init[h, x] < \infty \end{array} \right . \end{align*}`

Here, :math:`s_0 \in \mathcal{S}_{Stage}` is the *first* stage in the model, i.e.; the one with the smallest :math:`start\_year`, and :math:`t_{h,0} \in \mathcal{S}_{TimeHorizon}` is the initial horizon time step. Note that regardless of whether an initial energy level is set in the first stage, the model has to maintain the same initial storage level across all stages.

For a final point, the current model allows for a simultaneous charging and discharging process of EBM vehicles (:math:`\mathcal{V}_{EbmTechInflow}[s, h, x, t] > 0` and :math:`\mathcal{V}_{EbmTechOutflow}[s, h, x, t] > 0`). We would like to refer to the final section of the :ref:`storage model<storage_model>` because the considerations expressed there hold true in the exact same way for the EBM model.


.. _ates_model:

ATES model
------------

Test


.. _heatpump_model:

Heat pump model
-----------------

The heat pump model first defines its own set of tech tuples

:raw-math:`\begin{align*} \mathcal{S}_{HpTechTuple} = \big \{ (s, h, x) \in \mathcal{S}_{TechTuple}: ~ x \text{is a heat pump technology } \big \} \end{align*}`

Next, we need to understand that a heat pump has multiple inputs and outputs, as illustrated by the figure below:

.. image:: img/heatpump_scheme.png
   :width: 1000
   :alt: Schematics of a heat pump

The heat pump can operate either in heating or cooling mode but the interior workings are always comparable: The evaporator is connected to an input medium at temperature :math:`T_{Evap,in}` which is cooled down to :math:`T_{Evap,out}`. This absorbed heating power :math:`P_{Evap}` is compressed using an input power :math:`P_{Elec}`. On the condenser side, the added-up power of these two processes results in a heating power :math:`P_Cond` which increases the temperature :math:`T_{Cond,in}` of an input medium to an output temperature of :math:`T_{Cond,out}`.

* In heating mode, the evaporator is connected to a source medium (air, water, ...) and releases the condenser energy to a radiator or similar device.
* In cooling mode, the heating intake on the evaporator side is used to operate a chiller and the condenser side takes the cold medium from a source.

Since ehubX works based on energy carriers, we need to assign one energy carrier from :math:`\mathcal{S}_{Ec}` to each power node of this schematic. These are specified in :ref:`techs_yaml` and have the following interpretation:

.. list-table:: Energy carrier of heat pump technology :math:`x`
    :header-rows: 1

    * - Mode
      - Power node
      - Energy carrier from :math:`\mathcal{S}_{Ec}`
    * - Heating
      - Electricity consumption
      - :math:`ec\_el[x]`
    * - Heating
      - Evaporator power
      - :math:`ec\_ht\_in[x]`
    * - Heating
      - Condenser power
      - :math:`ec\_ht\_out[x]`
    * - Cooling
      - Electricity consumption
      - :math:`ec\_el[x]`
    * - Cooling
      - Evaporator power
      - :math:`ec\_co\_out[x]`
    * - Cooling
      - Condenser power
      - :math:`ec\_co\_in[x]`

As can be seen, we label the energy carriers from the perspective of the energy *usage*. It is also essential that the five energy carriers do not contain any duplicates since this would break the heat pump model below, leading to potential infeasibilities or unbounded solutions. Checks are included in the data validation phase to ensure that this is not the case. Using the above ecs, we define sets of input/output tuples for the heat pump:

:raw-math:`\begin{align*} \mathcal{S}_{HpTechIn} &= \Big \{ (s, h, x, e): (s, h, x) \in \mathcal{S}_{HpTechTuple}, ~e \in \{ec\_el[x], ec\_ht\_in[x], ec\_co\_in[x] \} \Big \} \\ \mathcal{S}_{HpTechOut} &= \Big \{ (s, h, x, e): (s, h, x) \in \mathcal{S}_{HpTechTuple}, ~e \in \{ec\_ht\_out[x], ec\_co\_out[x] \} \Big \} \end{align*}`

Based on these sets, we can now define heat pump input and output variables as follows:

:raw-math:`\begin{align*} \mathcal{V}_{HpTechIn}: \mathcal{S}_{HpTechIn} \times \mathcal{S}_{Time} \to \mathbb{R}_0^+ \\ \mathcal{V}_{HpTechOut}: \mathcal{S}_{HpTechOut} \times \mathcal{S}_{Time} \to \mathbb{R}_0^+ \end{align*}`

Note that this formulation so far suggests that heating and cooling modes may occur simultaneously, e.g.; if :math:`\mathcal{V}_{HpTechOut}[s, h, x, ec\_ht\_out, t] > 0` and :math:`\mathcal{V}_{HpTechOut}[s, h, x, ec\_co\_out, t] > 0`. Indeed, we allow for this to be the case because ehubX never considers a single asset but a collection of them. As such, the heat pump capacity in a single is allowed to consist of multiple real-life heat pumps where some operate in heating and others in cooling mode. However, we do need to respect the distinction between different modes in the model itself, which is why we define two additional power consumption variable for heating and cooling mode:

:raw-math:`\begin{align*} \mathcal{V}_{HpTechElecHt}, \mathcal{V}_{HpTechElecCo}: \mathcal{S}_{HpTechTuple} \times \mathcal{S}_{Time} \to \mathbb{R}_0^+ \end{align*}`

The sum of these two variables needs to be identical to the total power consumption which is handled in the following constraint:

:raw-math:`\begin{align*} \mathcal{V}_{HpTechIn}[s, h, x, ec\_el[x], t] = \mathcal{V}_{HpTechElecHt}[s, h, x, t] + \mathcal{V}_{HpTechElecCo}[s, h, x, t] \end{align*}`

The heat pump needs to satisfy a power balance equation. More specifically, the condenser power is comprised of the sum of compressor consumption and  evaporator power. Formulating this for both heating and cooling modes reads:

:raw-math:`\begin{align*} \mathcal{V}_{HpTechOut}[s, h, x, ec\_ht\_out[x], t] &= \mathcal{V}_{HpTechElecHt}[s, h, x, t] + \mathcal{V}_{HpTechIn}[s, h, x, ec\_ht\_in[x], t] \\ \mathcal{V}_{HpTechIn}[s, h, x, ec\_co\_in[x], t] &= \mathcal{V}_{HpTechElecCo}[s, h, x, t] + \mathcal{V}_{HpTechOut}[s, h, x, ec\_co\_out[x], t]\end{align*}`

An essential indicator for heat pumps is the Coefficient of Performance (COP). In ehubX, this is considered as a potentially stage-, hub- and time-dependent parameter :math:`cop[s, h, x, t]` that acts as the quotient between condenser power and electricity consumption. Translated into heating and cooling modes, this yields the constraint

:raw-math:`\begin{align*} \mathcal{V}_{HpTechOut}[s, h, x, ec\_ht\_out[x], t] &= cop[s, h, x, t] \cdot \mathcal{V}_{HpTechElecHt}[s, h, x, t] \\ \mathcal{V}_{HpTechIn}[s, h, x, ec\_co\_in[x], t] &= cop[s, h, x, t] \cdot \mathcal{V}_{HpTechElecCo}[s, h, x, t] \end{align*}`

As an input, :math:`cop` can either be specified directly in :ref:`hubs_yaml`. If it is not given as a default or profile value, ehubX will try to calculate it from the parameters :math:`temp\_heat\_in`, :math:`temp\_heat\_out` and :math:`cop\_factor` (also from :ref:`hubs_yaml`) using a dampened Carnot efficiency model as follows:

:raw-math:`\begin{align*} cop[s, h, x, t] = cop\_factor[s, x] \cdot \frac{temp\_heat\_out[s, h, x, t]}{temp\_heat\_out[s, h, x, t] - temp\_heat\_in[s, h, x, t]} \end{align*}`

The heat pump module still needs to be linked to two quantities from the :ref:`tech model<tech_model>`, namely installed capacity and technology usage. For the capacity, it is common to measure heat pump capacity in terms of condenser power. For this model, this results in the following constraint:

:raw-math:`\begin{align*} \mathcal{V}_{HpTechOut}[s, h, x, ec\_ht\_out, t] + \mathcal{V}_{HpTechIn}[s, h, x, ec\_co\_in, t] \le \mathcal{V}_{TechCap}[s, h, x] \end{align*}`

Finally, detecting heat pump usage is also formulated using the condenser power:

:raw-math:`\begin{align*} \sum\limits_{t \in \mathcal{S}_{Time}} weight[s, t] \cdot \big( \mathcal{V}_{HpTechOut}[s, h, x, ec\_ht\_out, t] + \mathcal{V}_{HpTechIn}[s, h, x, ec\_co\_in, t] \big) \le BigM_{HpCondSum}[s, h, x] \cdot \mathcal{V}_{YTechUsed}[s, h, x] \end{align*}`

Here, :math:`weight` is a :ref:`clustering<clustering>` value and :math:`BigM_{HpCondSum}[s, h, x]` is a big-M parameter which has to provide an upper bound to the summed-up power of the heat pump condenser over the time horizon. It is chosen as

:raw-math:`\begin{align*} BigM_{HpTechCap}[s, h, x] = \left \{ \begin{array}{rl} cap\_max[s, h, x] \cdot |\mathcal{S}_{TimeHorizon}| + 10^{-5}, &\text{if } cap\_max[s, h, x] < \infty \\ \mathcal{P}_{BigMGeneric}, &\text{else} \end{array} \right . \end{align*}`

We recall that :math:`{P}_{BigMGeneric}` is the demand-based default big-M parameter introduced in the :ref:`demand model<demand_model>`. Furthermore, :math:`cap\_max` is a parameter from :ref:`hubs_yaml`.




.. _network_model:

Network model
---------------

.. image:: img/network_scheme.png
   :width: 700
   :alt: Network scheme

The network model makes it possible to transfer energy between different hubs of the model. In :ref:`network_links_yaml`, a set of link is defined running between hubs. We gather these in a set

:raw-math:`\begin{align*} \mathcal{S}_{NetLink} = \big \{ \ell: \ell \text{ is a network link } \big \} \end{align*}`

In addition, :ref:`network_techs_yaml` defines a set of network technologies that can be installed and used for the actual transfer, here collected in the set

:raw-math:`\begin{align*} \mathcal{S}_{NetTech} = \big \{ n: n \text{ is a network technology } \big \} \end{align*}`

:ref:`network_links_yaml` additionally defines a connectivity structure between hubs and ecs defined on the links. This structure can be expressed for all *inputs to the network* by the following set:

:raw-math:`\begin{align*} \mathcal{S}_{NetLinkIn} = &\big \{ (h, \ell, e): \ell \in \mathcal{S}_{NetLink}, ~ e \text{ is ec of } \ell, ~ h \text{ is } start\_hub \text{ of } \ell \big \} \\ &\cup \big \{ (h, \ell, e): \ell \in \mathcal{S}_{NetLink}, ~ \ell \text{ is bidirectional}, ~e \text{ is ec of } \ell, ~ h \text{ is } end\_hub \text{ of } \ell \big \} \end{align*}`

This clarifies also what we understand by *bidirectionality*: Every link is able to transfer an ec from its :math:`start\_hub` to its :math:`end\_hub` but only bidirectional links can also transfer energy the other way. The same logic allows to define all *outputs of the network* as

:raw-math:`\begin{align*} \mathcal{S}_{NetLinkOut} = &\big \{ (h, \ell, e): \ell \in \mathcal{S}_{NetLink}, ~ e \text{ is ec of } \ell, ~ h \text{ is } end\_hub \text{ of } \ell \big \} \\ &\cup \big \{ (h, \ell, e): \ell \in \mathcal{S}_{NetLink}, ~ \ell \text{ is bidirectional}, ~e \text{ is ec of } \ell, ~ h \text{ is } start\_hub \text{ of } \ell \big \} \end{align*}`

On these two sets, we have variables quantifying the amount of inputs and outputs to the network transfer system:

:raw-math:`\begin{align*} \mathcal{V}_{NetLinkIn} &: \mathcal{S}_{Stage} \times \mathcal{S}_{NetLinkIn} \times \mathcal{S}_{Time} \to \mathbb{R}_0^+ \\    \mathcal{V}_{NetLinkOut} &: \mathcal{S}_{Stage} \times \mathcal{S}_{NetLinkOut} \times \mathcal{S}_{Time} \to \mathbb{R}_0^+ \end{align*}`

From the perspective of the rest of the energy system, *links* are not really an aspect that is considered. So it stands to reason that for an energy balance perspective, the only relevant quantities are the inputs and outputs at each hub, aggregated over all possible links. We prepare this procedure by defining the *hub inputs/output sets* by

:raw-math:`\begin{align*} \mathcal{S}_{NetHubIn} &= \big \{ (h, e) \in \mathcal{S}_{Hub} \times \mathcal{S}_{Ec}: (h, \ell, e) \in \mathcal{S}_{NetLinkIn} \text{ for any } \ell \in \mathcal{S}_{NetLink} \big \} \\    \mathcal{S}_{NetHubOut} &= \big \{ (h, e) \in \mathcal{S}_{Hub} \times \mathcal{S}_{Ec}: (h, \ell, e) \in \mathcal{S}_{NetLinkOut} \text{ for any } \ell \in \mathcal{S}_{NetLink} \big \} \end{align*}`

Accordingly, we define the *hub inputs/outputs* on these sets:

:raw-math:`\begin{align*} \mathcal{V}_{NetHubIn} &: \mathcal{S}_{Stage} \times \mathcal{S}_{NetHubIn} \times \mathcal{S}_{Time} \to \mathbb{R}_0^+ \\    \mathcal{V}_{NetHubOut} &: \mathcal{S}_{Stage} \times \mathcal{S}_{NetHubOut} \times \mathcal{S}_{Time} \to \mathbb{R}_0^+ \end{align*}`

The connection between link inputs/outputs and hub inputs/outputs is naturally given by

:raw-math:`\begin{align*} \mathcal{V}_{NetHubIn}[s, h, e, t] &= \sum\limits_{\substack{\ell \in \mathcal{S}_{NetLink} \\ (h, \ell, e) \in \mathcal{S}_{NetLinkIn}}} \mathcal{V}_{NetLinkIn}[s, h, e, t] \\    \mathcal{V}_{NetHubOut}[s, h, e, t] &= \sum\limits_{\substack{\ell \in \mathcal{S}_{NetLink} \\ (h, \ell, e) \in \mathcal{S}_{NetLinkOut}}} \mathcal{V}_{NetLinkOut}[s, h, e, t]  \end{align*}`

In a next step, we consider that network transfer is possible through network technologies. Similar to the :ref:`technology model <tech_model>`, these technologies may only be eligible for certain stages (due to its *technology readiness level*, see :ref:`network_techs_yaml`) or certain links (due to *allowed_net_tech_lists*, see :ref:`network_links_yaml`). The stage-link-tech tuples of all allowed combinations is captured in the set :math:`\mathcal{S}_{NetTechTuple} \subset \mathcal{S}_{Stage} \times \mathcal{S}_{NetLink} \times \mathcal{S}_{NetTech}`. Based on these set, we can define the set of all possible network technologies that could contribute to a network transfer along a specific link in the sets

:raw-math:`\begin{align*} \mathcal{S}_{NetTechIn} &= \big \{ (s, h, \ell, n) \in \mathcal{S}_{Stage} \times \mathcal{S}_{Hub} \times \mathcal{S}_{NetLink} \times \mathcal{S}_{NetTech}: (s, \ell, n) \in \mathcal{S}_{NetTechTuple}, (h, \ell, ec[n]) \in \mathcal{S}_{NetLinkIn} \big \} \\    \mathcal{S}_{NetTechOut} &= \big \{ (s, h, \ell, n) \in \mathcal{S}_{Stage} \times \mathcal{S}_{Hub} \times \mathcal{S}_{NetLink} \times \mathcal{S}_{NetTech}: (s, \ell, n) \in \mathcal{S}_{NetTechTuple}, (h, \ell, ec[n]) \in \mathcal{S}_{NetLinkOut} \big \} \end{align*}`

Here we have used the parameter :math:`ec[n]` from :ref:`network_techs_yaml` which maps each network technology to its unique ec. As for the other sets, we assign the amount of network link transfer handled by each network technology to the variables

:raw-math:`\begin{align*} \mathcal{V}_{NetTechIn}&: \mathcal{S}_{NetTechIn} \times \mathcal{S}_{Time} \to \mathbb{R}_0^+ \\    \mathcal{V}_{NetTechOut}&: \mathcal{S}_{NetTechOut} \times \mathcal{S}_{Time} \to \mathbb{R}_0^+ \end{align*}`

Naturally, the link inputs/outputs are then simply given be the sum over all network technologies:

:raw-math:`\begin{align*} \mathcal{V}_{NetLinkIn}[s, h, \ell, e, t] &= \sum\limits_{\substack{n \in \mathcal{S}_{NetTech} \\ (s, h, \ell, n) \in \mathcal{S}_{NetTechIn} \\ e = ec[n]}} \mathcal{V}_{NetTechIn}[s, h, \ell, n, t] \\    \mathcal{V}_{NetLinkOut}[s, h, \ell, e, t] &= \sum\limits_{\substack{n \in \mathcal{S}_{NetTech} \\ (s, h, \ell, n) \in \mathcal{S}_{NetTechOut} \\ e = ec[n]}} \mathcal{V}_{NetTechOut}[s, h, \ell, n, t] \end{align*}`

This concludes the long establishment process for all variables. To summarize, we have defined three layers:

1. **Hub inputs/outputs**, set :math:`\mathcal{S}_{NetHubIn/Out} \subset \mathcal{S}_{Hub} \times \mathcal{S}_{Ec}`.

2. **Link inputs/outputs**, set :math:`\mathcal{S}_{NetLinkIn/Out} \subset \mathcal{S}_{Hub} \times \mathcal{S}_{NetLink} \times \mathcal{S}_{Ec}`

3. **Tech inputs/outputs**, set :math:`\mathcal{S}_{NetTechIn/Out} \subset \mathcal{S}_{Stage} \times \mathcal{S}_{Hub} \times \mathcal{S}_{NetLink} \times \mathcal{S}_{NetTech}`

where each layer is defined as the aggregated sum of the layer below it.

In a next step, we connect the input and output amounts for the network technologies by the following constraint:

:raw-math:`\begin{align*} \mathcal{V}_{NetTechOut}[s, h_{out}, \ell, n, t] = (1 - trans\_loss[s, n])^{length[\ell]} \cdot \mathcal{V}_{NetTechIn}[s, h_{in}[\ell], \ell, n, t] \end{align*}`

where :math:`trans\_loss` is the transmission loss parameter from :ref:`network_techs_yaml`, :math:`length` is the link length from :ref:`network_links_yaml` and :math:`h_{in}` is given by

:raw-math:`\begin{align*} h_{in}[\ell] = \left \{ \begin{array}{rl} hub\_start[\ell], &\text{if } h_{out} = hub\_end[\ell] \\ hub\_end[\ell], &\text{if } h_{out} = hub\_start[\ell] \end{array} \right . \end{align*}`

In :ref:`network_links_yaml`, the parameters :math:`trans\_sum\_min\_forward`, :math:`trans\_sum\_min\_backward`, :math:`trans\_sum\_max\_forward` and :math:`trans\_sum\_max\_backward` denote maximal and minimal transmission amounts for an ec along each link in forward and backward directions. They result in the constraints

:raw-math:`\begin{align*} trans\_sum\_min[s, h_{out}, \ell, e] ~\le~ \sum\limits_{t \in \mathcal{S}_{Time}} weight[s, t] \cdot \mathcal{V}_{NetLinkOut}[s, h_{out}, \ell, e, t] ~\le~ trans\_sum\_max[s, h_{out}, \ell, e] \end{align*}`

where we have used the parameters

:raw-math:`\begin{align*} trans\_sum\_min[s, h_{out}, \ell, e] &= \left \{ \begin{array}{rl} trans\_sum\_min\_forward[s, \ell, e], &\text{if } h_{out} = hub\_end[\ell] \\ trans\_sum\_min\_backard[s, \ell, e], &\text{if } h_{out} = hub\_start[\ell] \end{array} \right . \\    trans\_sum\_max[s, h_{out}, \ell, e] &= \left \{ \begin{array}{rl} trans\_sum\_max\_forward[s, \ell, e], &\text{if } h_{out} = hub\_end[\ell] \\ trans\_sum\_max\_backard[s, \ell, e], &\text{if } h_{out} = hub\_start[\ell] \end{array} \right . \end{align*}`

As it was done for the :ref:`technology model<tech_model>`, ehubX needs to be able to have an understanding of *capacity* for network technologies, and be able to make its own decisions about the optimal capacity along eacah link. We prepare this by introducing the variable

:raw-math:`\begin{align*} \mathcal{V}_{NetTechCap}: \mathcal{S}_{Stage} \times \mathcal{S}_{NetLink} \times \mathcal{S}_{NetTech} \to \mathbb{R} \end{align*}`

These capacities are to be understood as the maximal amount of *input* power that the technologies can handle. In contrast to the technology model, we do not specify minimal or maximal capacities for each technology, but rather each ec along a link. To formulate this mathematically, we require the set

:raw-math:`\begin{align*} \mathcal{S}_{NetLinkAndEc} = \big \{ (\ell, e) \in \mathcal{S}_{NetLink} \times \mathcal{S}_{Ec}: e \in ecs[\ell] \big \} \end{align*}`

The capacity restrictions then take the following form for all :math:`s \in \mathcal{S}_{Stage}` and all :math:`(\ell, e) \in \mathcal{S}_{NetLinkAndEc}`:

:raw-math:`\begin{align*} cap\_min[s, \ell, e] \le \sum\limits_{\substack{n \in \mathcal{S}_{NetTech} \\ e = ec[n]}} \mathcal{V}_{NetTechCap}[s, \ell, n] \le cap\_max[s, \ell, e] \end{align*}`

The total capacity of a network technology along a link is composed of both the remnants of the *initial capacity* (:math:`cap\_init` in :ref:`network_links_yaml`) and the *installed capacity* from previous stages, which ehubX can decide upon via the variable

:raw-math:`\begin{align*} \mathcal{V}_{NetTechCapInstl}: \mathcal{S}_{Stage} \times \mathcal{S}_{NetLink} \times \mathcal{S}_{NetTech} \to \mathbb{R}_0^+ \end{align*}`

To formulate the sum of network technology capacity, we add the constraint

:raw-math:`\begin{align*} \mathcal{V}_{NetTechCap}[s, \ell, n] = Cap_{init}[s, \ell, n] + \sum\limits_{s_{instl} \in \mathcal{S}_{Stage}} Cap_{instl}[s_{instl}, s, \ell, n] \end{align*}`

The initial capacity that is still operational in stage :math:`s` is given by

:raw-math:`\begin{align*} Cap_{init}[s, \ell, n] = \left \{ \begin{array}{rl} cap\_init[\ell, n], &\text{if } start\_year[s] - init\_year < lifetime[n] - age\_init[\ell, n] \\ 0, &\text{else} \end{array} \right . \end{align*}`

Here, :math:`cap\_init` and :math:`age\_init` are initial capacity parameters from :ref:`network_links_yaml`, :math:`start\_year` is the first year of a stage from :ref:`stages_yaml`, and :math:`init\_year` is the start year of the first stage (earliest :math:`start\_year` in :ref:`stages_yaml`). The capacity installed in stage :math:`s_{instl}` that is still operational in stage :math:`s` is given by

:raw-math:`\begin{align*} Cap_{instl}[s_{instl}, s, \ell, n] = \left \{ \begin{array}{rl} \mathcal{V}_{NetTechCapInstl}[s_{instl}, \ell, n], &\text{if } 0 \le start\_year[s] - start\_year[s_{instl}] < lifetime[n] \\ 0, &\text{else} \end{array} \right . \end{align*}`

:math:`lifetime` is the lifetime of a network technology parametrized in :ref:`network_techs_yaml`.

Now that network technology capacity can be installed by the optimizer, we need to limit the actual network inputs by this capacity, as follows:

:raw-math:`\begin{align*} \sum\limits_{\substack{h \in \mathcal{S}_{Hub} \\ (s, h, \ell, n) \in \mathcal{S}_{NetTechIn}}} \mathcal{V}_{NetTechIn}[s, h, \ell, n, t] \le \mathcal{V}_{NetTechCap}[s, \ell, n] \end{align*}`

The sum over the hubs in this formulation only accounts for the fact that the link :math:`\ell` might have a single input hub (just :math:`hub\_start[\ell]` if :math:`\ell` is unidirectional) or two input hubs (:math:`hub\_start[\ell]` and :math:`hub\_end[\ell]` if :math:`\ell` is bidirectional).

As a next step, we need to respect the parameter :math:`unit\_cap\_min` from :ref:`network_techs_yaml` which declares the minimal amount of capacity that has to be installed if any installation takes place at all. To implement this, we first require a binary variable monitoring whether any installation takes place at all, given by

:raw-math:`\begin{align*} \mathcal{V}_{YNetTechCapInstl}: \mathcal{S}_{Stage} \times \mathcal{S}_{NetLink} \times \mathcal{S}_{NetTech} \to \{0, 1 \} \end{align*}`

This variable is forced to activate if :math:`\mathcal{V}_{NetTechCapInstl}` is nonnegative by the big-M constraint

:raw-math:`\begin{align*} \mathcal{V}_{NetTechCapInstl[s, \ell, n]} \le BigM_{NetTechCap}[s, \ell, n] \cdot \mathcal{V}_{YNetTechCapInstl}[s, \ell, n] \end{align*}`

where the big-M parameter can be parametrized with :math:`cap\_max` from :ref:`network_links_yaml` and the generic big-M value :math:`\mathcal{P}_{BigMGeneric}` from the :ref:`demand model<demand_model>` as

:raw-math:`\begin{align*} BigM_{NetTechCap}[s, \ell, n] = \left \{ \begin{array}{rl} 10^{-5} + cap\_max[s, \ell, ec[n]], &\text{if } cap\_max[s, \ell, ec[n]] < \infty \\ \mathcal{P}_{BigMGeneric}, &\text{else} \end{array} \right . \end{align*}`

Now that we have the binary variable :math:`\mathcal{V}_{YNetTechCapInstl}`, we can include the functionality of :math:`unit\_cap\_min` from :ref:`network_techs_yaml` by demanding that

:raw-math:`\begin{align*} \mathcal{V}_{NetTechCapInstl}[s, \ell, n] \ge unit\_cap\_min[s, n] \cdot \mathcal{V}_{YNetTechCapInstl[s, \ell, n] \end{align*}`

We also need to track if a network technology is *used* at all on a specific stage-link tuple which is monitored by a binary variable

:raw-math:`\begin{align*} \mathcal{V}_{YNetTechUsed}: \mathcal{S}_{NetTechTuple} \to \{0, 1 \} \end{align*}`

This relationship is enforced by the a big-M constraint

:raw-math:`\begin{align*} \sum\limits_{\substack{h \in \mathcal{S}_{Hub} \\ (s, h, \ell, n) \in \mathcal{S}_{NetTechIn}}} \sum\limits_{t \in \mathcal{S}_{Time}} weight[s, t] \cdot \mathcal{V}_{NetTechIn}[s, h, \ell, n, t] \le BigM_{NetTechLinkIn}[s, \ell, n] \cdot \mathcal{V}_{YNetTechUsed}[s, \ell, n] \end{align*}`

Here, the big-M parameter :math:`BigM_{NetTechLinkIn}[s, \ell, n]` is a tight upper limit to the maximal amount of network input that is possible, given by

:raw-math:`\begin{align*} BigM_{NetTechLinkIn}[s, \ell, n] = \left \{ \begin{array}{rl} 10^{-5} + cap\_max[s, \ell, e] \cdot |\mathcal{S}_{TimeHorizon}|, &\text{if } cap\_max[s, \ell, e] < \infty \\ \mathcal{P}_{BigMGeneric}, &\text{else} \end{array} \right .\end{align*}`

:math:`cap\_max` is the maximal capacity parameter from :ref:`network_links_yaml` and :math:`\mathcal{P}_{BigMGeneric}` is the demand-based default big-M parameter introduced in the :ref:`demand model<demand_model>`.

At this point, we can consider the costs that arise from network technology installation and maintenance. Starting with CAPEX costs, we introduce the fixed variable

:raw-math:`\begin{align*} \mathcal{V}_{NetTechCostCapex}: \mathcal{S}_{NetTechTuple} &\to \mathbb{R}, \\ \mathcal{V}_{NetTechCostCapex}[s, \ell, n] &= length[\ell] \cdot CRF(interest\_rate[n], lifetime[n]) \cdot \sum\limits_{\substack{s_{instl} \in \mathcal{S}_{Stage} \\ (s_{instl}, \ell, n) \in \mathcal{S}_{NetTechTuple}}} \cdot Capex_{Stage}[s_{instl}, s, \ell, n] \end{align*}`

where we have used the same formulation as in the :ref:`technology model<tech_model>` but added the link length parameter :math:`length` from :ref:`network_links_yaml`. :math:`CRF` is a standard *capital recovery factor* calculated from the technology's lifetime and interest rate as follows:

:raw-math:`\begin{align*} CRF(i, N) = \frac{i \cdot (i+1)^N}{(i+1)^{N-1}} \end{align*}`

The summand takes the following form:

:raw-math:`\begin{align*} Capex_{Stage}[s_{instl}, s, \ell, n] ~=~ \left \{ \begin{array}{rl} capex\_per\_cap[s, n] \cdot \mathcal{V}_{NetTechCapInstl}[s_{instl}, \ell, n] & \\ +~ one\_time\_capex[s, n] \cdot \mathcal{V}_{YNetTechCapInstl}[s_{instl}, \ell, n], &\text{if } 0 \le start\_year[s] - start\_year[s_{instl}] < lifetime[n] \\ 0, &\text{else} \end{array} \right . \end{align*}`

Here, :math:`capex\_per\_cap` and :math:`one\_time\_capex` are parameters from :ref:`network_techs_yaml`.

In addition to these installation-related CAPEX costs, operating and maintaining the network technologies is associated with the *OPEX costs* parametrized by :math:`opex\_per\_cap` and :math:`one\_time\_opex` from :ref:`network_techs_yaml`:

:raw-math:`\begin{align*} \mathcal{V}_{NetTechCostOpexCap}: \mathcal{S}_{NetTechTuple} &\to \mathbb{R}, \\ \mathcal{V}_{NetTechCostOpexCap}[s, \ell, n] &= length[ell] \cdot \big( opex\_per\_cap[s, n] \cdot \mathcal{V}_{NetTechCap}[s, \ell, n] + one\_time\_opex[s, n] \cdot \mathcal{V}_{YNetTechUsed}[s, \ell, n] \big) \end{align*}`

As can be seen, both costs have a part that arises per amount of installed capacity while another enters any time any amount of network technology is installed or used at all. On top of these capacity-related costs, the network model contains a cost factor that arises from the parameter :math:`opex\_per\_energy` in :ref:`network_techs_yaml`, given for the amount of transmitted energy by the variable

:raw-math:`\begin{align*} \mathcal{V}_{NetTechCostOpexTrans}: \mathcal{S}_{NetTechTuple} &\to \mathbb{R}, \\ \mathcal{V}_{NetTechCostOpexTrans}[s, \ell, n] &= length[\ell] \cdot opex\_per\_energy[s, n] \cdot \sum\limits_{\substack{h \in \mathcal{S}_{Hub} \\ (s, h, \ell, n) \in \mathcal{S}_{NetTechIn}}} \sum\limits_{t \in \mathcal{S}_{Time}} weight[s, t] \cdot \mathcal{V}_{NetTechIn}[s, h, \ell, n, t] \end{align*}`

Adding up these costs gives us the following fixed variable:

:raw-math:`\begin{align*} \mathcal{V}_{NetTechCostTotal} &\in \mathbb{R}, \\ \mathcal{V}_{NetTechCostTotal} &= \sum\limits_{(s, \ell, n) \in \mathcal{S}_{NetTechTuple}} \big( \mathcal{V}_{NetTechCostCapex}[s, \ell, n] + \mathcal{V}_{NetTechCostOpexCap}[s, \ell, n] + \mathcal{V}_{NetTechCostOpexTrans}[s, \ell, n] \big) \end{align*}`

Similar to the costs associated with network technologies, certain CO2-embodied emissions are associated with this process as well. We collect these in the variable

:raw-math:`\begin{align*} \mathcal{V}_{NetTechCo2Instl}: \mathcal{S}_{NetTechTuple} &\to \mathbb{R} \\ \mathcal{V}_{NetTechCo2Instl}[s, \ell, n] &= length[\ell] \cdot \sum\limits_{\substack{s_{instl} \in \mathcal{S}_{Stage} \\ (s_{instl}, \ell, n) \in \mathcal{S}_{NetTechTuple} \\ 0 \le start\_year[s] - start\_year[s_{instl}] \le lifetime[n]}} \frac{co2\_per\_cap[s, n]}{lifetime[n]} \cdot \mathcal{V}_{NetTechCapInstl}[s_{instl}, \ell, n] \end{align*}`

The parameter :math:`co\_per\_cap` comes from the :ref:`network_techs_yaml` file.

In addition to installation-related CO2 emissions, they may arise relative to the total amount of transmitted energy, as parametrized by :math:`co2\_per\_energy` from :ref:`network_techs_yaml` and tracked by the fixed variable

:raw-math:`\begin{align*} \mathcal{V}_{NetTechCo2Trans}: \mathcal{S}_{NetTechTuple} &\to \mathbb{R} \\ \mathcal{V}_{NetTechCo2Trans}[s, \ell, n] &= length[\ell] \cdot co2\_per\_energy[s, n] \cdot \sum\limits_{\substack{h \in \mathcal{S}_{Hub} \\ (s, h, \ell, n) \in \mathcal{S}_{NetTechIn}}} \sum\limits_{t \in \mathcal{S}_{Time}} weight[s, n] \cdot \mathcal{V}_{NetTechIn}[s, h, \ell, n, t] \end{align*}`

 As with the costs, we gather the total amount of CO2 emissions into a fixed variable for convenience:

:raw-math:`\begin{align*} \mathcal{V}_{NetTechCo2Total}: \mathcal{S} \to \mathbb{R}, \qquad \mathcal{V}_{NetTechCo2Total}[s] = \sum\limits_{\substack{(s', \ell, n) \in \mathcal{S}_{NetTechTuple} \\ s = s'}} \big( \mathcal{V}_{NetTechCo2Instl}[s', \ell, n] + \mathcal{V}_{NetTechCo2Trans}[s', \ell, n] \big) \end{align*}`



.. _autarky_model:

Autarky model
---------------

In ehubX, the concept of autarky is calculated by two kinds of energy imports. The first is called *cross-border imports*, measured in a fixed scalar variable

:raw-math:`\begin{align*} \mathcal{V}_{AutarkyImpCross} &\in \mathbb{R}_0^+, \\ \mathcal{V}_{AutarkyImpCross} &= \sum\limits_{\substack{(s, h, e) \in \mathcal{S}_{ImpTuple} \\ is\_energy[e] = True \\ imp\_exp\_type[e] = cross}} \sum\limits_{t \in \mathcal{S}_{Time}} weight[s, t] \cdot \mathcal{V}_{Imp}[s, h, e, t] \end{align*}`

The ec-specific parameters :math:`is\_energy` and :math:`imp\_exp\_type` can be specified in :ref:`ecs_yaml`, and :math:`weight` is a :ref:`clustering` parameter. The idea behind this variable is that it should measure all imports into the system that would be unavailable if neighboring energy systems were not able to provide them. We think of energy carriers like electricity or gas that are purchased from different countries or regions.

In contrast the these cross-import, the ehubX model also allows for "imports" that originate in natural resources and would remain be available if the energy system became completely isolated. These are e.g.; solar/wind energy or thermal resources. The total amount of these imports is measured in the fixed scalar variable

:raw-math:`\begin{align*} \mathcal{V}_{AutarkyImpInternal} &\in \mathbb{R}_0^+, \\ \mathcal{V}_{AutarkyImpInternal} &= \sum\limits_{\substack{(s, h, e) \in \mathcal{S}_{ImpTuple} \\ is\_energy[e] = True \\ imp\_exp\_type[e] = internal}} \sum\limits_{t \in \mathcal{S}_{Time}} weight[s, t] \cdot \mathcal{V}_{Imp}[s, h, e, t] + \sum\limits_{\substack{(s, h, x, e) \in \mathcal{S}_{ConvTechOut} \\ x \in \mathcal{S}_{ConvTechInternal}}} \sum\limits_{t \in \mathcal{S}_{Time}} weight[s, t] \cdot \mathcal{V}_{ConvTechOut}[s, h, x, e, t] \end{align*}`

The first summand in the above equation is a similar type of value as in the definition of :math:`\mathcal{V}_{AutarkyImpCross}`. The second term considers the internal import of ecs that are not directly measured in terms of energy. Examples include solar irradiation or wind speed. These ecs are characterized by the fact that they have :math:`is\_energy[e] = False` and :math:`imp\_exp\_type[e] = internal`. In order to accurately include these carriers into the internal imports, we have considered a special subset of conversion technologies, given by

:raw-math:`\begin{align*} \mathcal{S}_{ConvTechInternal} = \big \{ x \in \mathcal{S}_{ConvTech}: ~ x \text{ has } &\text{a single input } ec\_in \text{ with } is\_energy[ec\_in] = False \text{ and } imp\_exp\_type[ec\_in] = internal \\ \text{and } &\text{a single output } ec\_out \text{ with } is\_energy[ec\_out] = True \big \} \end{align*}`

These technologies transform a single non-energy internal input ec into a single energy output ec, and the outputs of the conversion technology are included in the internal imports.

Having calculated both internal imports and cross-border imports, the autarky measure is defined as

:raw-math:`\begin{align*} Autarky = \frac{\mathcal{V}_{AutarkyImpInternal}}{\mathcal{V}_{AutarkyImpInternal} + \mathcal{V}_{AutarkyImpCross}} \end{align*}`

The actual variable we use to track the autarky measure is given by

:raw-math:`\begin{align*} \mathcal{V}_{Autarky} \in \mathbb{R}_0^+ \end{align*}`

There are now two options, based on the autarky calculation method selected in :ref:`stages_yaml`. First, if the method **'quadratic'** is chosen, this nonlinear constraint is directly included in the model, making it a quadratically constrained system:

:raw-math:`\begin{align*} \mathcal{V}_{Autarky} \cdot \big(\mathcal{V}_{AutarkyImpInternal} + \mathcal{V}_{AutarkyImpCross}) = \mathcal{V}_{AutarkyImpInternal} \end{align*}`

Second, if the method **'linearized'** is chosen, ...
[TODO: Add implementation & doc for this]


Finally, independent of the method that is used for the calculation of the variable :math:`\mathcal{V}_{Autarky}`, two additional constraints based on the parameters *autarky\_min* and *autarky\_max* from :ref:`stages_yaml` are added:

:raw-math:`\begin{align*} autarky\_min ~\le~ \mathcal{V}_{Autarky} ~\le~ autarky\_max \end{align*}`



.. _energy_system_model:

Energy system model
--------------------

The energy system model connects the variables from the submodels and defines the objective function for the optimization model. The most important task of the energy system model is to define energy balance equations which ensure that no energy can be created or destroyed within the model. This balance equation is given for all stages :math:`s \in \mathcal{S}_{Stage}`, hubs :math:`h \in \mathcal{S}_{Hub}`, ecs :math:`e \in \mathcal{S}_{Ec}`, and time steps :math:`t \in \mathcal{S}_{Time}` by

:raw-math:`\begin{align*} 0 =~ & \mathcal{V}_{Imp}^*[s, h, e, t] - \mathcal{V}_{Exp}^*[s, h, e, t] + \mathcal{V}_{DemandSupply}^*[s, h, e, t] \\    +&\sum\limits_{\substack{x \in \mathcal{S}_{Tech} \\ (s, h, x) \in \mathcal{S}_{StorTechTuple}}} \big( \mathcal{V}_{StorTechOutflow}[s, h, x, t] - \mathcal{V}_{StorTechInflow}[s, h, x, t] \big) \\    +& \sum\limits_{\substack{x \in \mathcal{S}_{Tech} \\ (s, h, x) \in \mathcal{S}_{EbmTechTuple}}} \big( \mathcal{V}_{EbmTechOutflow}[s, h, x, t] - \mathcal{V}_{EbmTechInflow}[s, h, x, t] \big) \\     +& \sum\limits_{\substack{x \in \mathcal{S}_{Tech} \\ (s, h, x, e) \in \mathcal{S}_{ConvTechOut}}} \mathcal{V}_{ConvTechOut}[s, h, x, e, t] - \sum\limits_{\substack{x \in \mathcal{S}_{Tech} \\ (s, h, x, e) \in \mathcal{S}_{ConvTechIn}}} \mathcal{V}_{ConvTechIn}[s, h, x, e, t] \\    +& \sum\limits_{\substack{x \in \mathcal{S}_{Tech} \\ (s, h, x, e) \in \mathcal{S}_{HpTechOut}}} \mathcal{V}_{HpTechOut}[s, h, x, e, t] - \sum\limits_{\substack{x \in \mathcal{S}_{Tech} \\ (s, h, x, e) \in \mathcal{S}_{HpTechIn}}} \mathcal{V}_{HpTechIn}[s, h, x, e, t] \\    +& \mathcal{V}_{NetHubOut}^*[s, h, e, t] - \mathcal{V}_{NetHubIn}^*[s, h, e, t] \end{align*}`

Some new elements have occured in this constraint. First of all, a star symbol has been added to simplify the notation. Take for example a tuple :math:`(s, h, e) \in \mathcal{S}_{Stage} \times \mathcal{S}_{Hub} \times \mathcal{S}_{Ec}`. Then we define

:raw-math:`\begin{align*} \mathcal{V}_{Imp}^*[s, h, e, t] = \left \{ \begin{array}{rl} \mathcal{V}_{Imp}[s, h, e, t], &\text{if } (s, h, e) \in \mathcal{S}_{ImpTuple} \\ 0, &\text{else} \end{array} \right . \end{align*}`

and similarily for other star-notated variables where the tuple :math:`(s, h, e)` might not belong to the respective definition set. Second, the *amount of power dispatched to the demand side* is given by

:raw-math:`\begin{align*} \mathcal{V}_{DemandSupply}&: \mathcal{S}_{DemandTuple} \times \mathcal{S}_{Time} \to \mathbb{R}_0^+, \\ \mathcal{V}_{DemandSupply}&[s, h, e, t] = demand[s, h, e, t] - \mathcal{V}_{LoadShedding}^*[s, h, e, t] + \mathcal{V}_{LoadShifting}^*[s, h, e, t] \end{align*}`

Here, :math:`demand` is the parameter for the load amount from :ref:`demands_yaml` and :math:`\mathcal{V}_{LoadShedding}`, :math:`\mathcal{V}_{LoadShifting}` come from the :ref:`load shedding model<loadshedding_model>` and :ref:`load shifting model<loadshifting_model>` respectively.

In addition to energy balancing, the energy system model has the job of defining the overall *CO2 emissions* which are gathered in a global fixed variable

:raw-math:`\begin{align*} \mathcal{V}_{SystemCo2}: \mathcal{S}_{Stage} &\to \mathbb{R}, \\ \mathcal{V}_{SystemCo2}[s] &= \mathcal{V}_{TechCo2Total}[s] + \mathcal{V}_{ImpCo2Total}[s] - \mathcal{V}_{ExpCo2Total}[s] + \mathcal{V}_{NetTechCo2Total}[s] \end{align*}`

Every stage has the potential to include CO2 penalization costs via the optional parameter :math:`co2\_price` from :ref:`stages_yaml` which are defined as:

:raw-math:`\begin{align*} \mathcal{V}_{SystemCostCo2Penalty} \in \mathbb{R}, \quad \mathcal{V}_{SystemCostCo2Penalty} = \sum\limits_{s \in \mathcal{S}{Stage}} co2\_price[s] \cdot \mathcal{V}_{SystemCo2}[s] \end{align*}`

In addition, :ref:`stages_yaml` contains the parameters :math:`co2\_min` and :math:`co2\_max` which result in the following straightforward constraints for the CO2 emission amounts:

:raw-math:`\begin{align*} co2\_min[s] \le \mathcal{V}_{SystemCo2}[s] \le co2\_max[s] \end{align*}`

Finally, when CO2 emissions are to be chosen as an objective function, they need to be gathered in a single variable which is given by

:raw-math:`\begin{align*} \mathcal{V}_{SystemCo2Total} \in \mathbb{R}, \quad \mathcal{V}_{SystemCo2Total} = \sum\limits_{s \in \mathcal{S}{Stage}} \mathcal{V}_{SystemCo2}[s] \end{align*}`

Moving from system CO2 emissions to system costs, these are collected in a similar global variable

:raw-math:`\begin{align*} \mathcal{V}_{SystemCost} \in~ &\mathbb{R}, \\ \mathcal{V}_{SystemCost} =~ &\mathcal{V}_{TechCostTotal} + \mathcal{V}_{ConvTechCostTotal} + \mathcal{V}_{ImpCostTotal} - \mathcal{V}_{ExpProfitTotal} \\ &~ + \mathcal{V}_{LoadSheddingCostTotal} + \mathcal{V}_{LoadShiftingCostTotal} + \mathcal{V}_{NetTechCostTotal} + \mathcal{V}_{SystemCostCo2Penalty} \end{align*}`

This variable is a possible objective function of the system alongside the CO2 total emissions.

