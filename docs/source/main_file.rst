.. _main_file:

The main file
===============

Interacting with the ehubX library is usually done in a main python file which - in its most basic form - looks something like this:

.. code-block:: ruby
    :caption: Basic ehubX main file

    from ehubx import EhubX, Gurobi

    # Create EhubX object
    ehubx = EhubX()
    # Set model path and parse
    ehubx.model_dir_path = "path/to/model/dir"
    ehubx.parse()
    # Build the model
    ehubx.build()
    # Set a solver
    ehubx.set_solver(Gurobi())
    # Single-objective solve
    ehubx.solve_single_obj()
    # Double-objective solve
    ehubx.solve_double_obj()

In the sections below, we will go through all blocks in this main file and explain in detail what happens in it and what other options exist to customize an ehubX run.


.. _ehubx_object:

The EhubX object
-----------------

.. code-block:: ruby
    :linenos:
    :caption: Creating an EhubX object

    ehubx = EhubX()

The ehubX class is the main interface that users will employ to trigger certain functionality of the platform. It all starts with the creation of an ehubX object.


.. _parsing:

Parsing from input files
-------------------------

.. code-block:: ruby
    :linenos:
    :caption: Parsing from input files

    ehubx.model_dir_path = "path/to/model/dir"
    ehubx.parse()

The primary way to describe an ehubX models is through :ref:`input files <input_files>`. For each model, these have to be located in a *model directory* and adhere to a specific structure as explained in :ref:`file_overview`. In line 1, we point the ehubX object towards the model directory. Line 2 then parses all data from the input files and creates the attribute :code:`ehubx.energy_system` which is an instance of the class :code:`ehubx.data.energy_system_data.EnergySystem`.

Modifying model data through code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For a normal application, this step would be enough to read the model data into the ehubX object. However, every attribute in ehubX has its own getters and setters, so the option also exists to modify the model data after the fact, as illustrated below:

.. code-block:: ruby
    :linenos:
    :caption: Modifying model data after parsing

    from ehubx import EhubX
    from ehubx.data import stage_data, hub_data, ec_data, time_data

    ehubx = EhubX()
    ehubx.model_dir_path = "path/to/model/dir"
    ehubx.parse()
    ehubx.energy_system.imports.set_max(stage_data.StageId("S1"),
                                        hub_data.HubId("H1"),
                                        ec_data.EcId("E1"),
                                        time_data.TimeId(2), 500)

In the above example, we have accessed the :code:`imports` section of the energy system data to set a maximal import threshold for a certain stage, hub, ec and time of 500 (cf. parameter *max* of :ref:`imports_yaml`). In order to have access to the ehubX index classes :code:`StageId`, :code:`HubId`, :code:`EcId` and :code:`TimeId`, these are imported in line 2. It has to be noted that getting and setting parameters in this way requires more detailed knowledge of the ehubX source code. However, as a general rule of thumb, every parameter *x* in the :ref:`input files<input_files>` will have getter and setter methods called :code:`get_x` and :code:`set_x` which can be used to modify and retrieve it.

Deactivating submodules
^^^^^^^^^^^^^^^^^^^^^^^^

As an additional option, it is possible to deactivate and reactivate most of the ehubX submodules entirely. For example, if the user wanted to test how the model would change if no storage technologies were available, they could try to deactivate the :ref:`storage model<storage_model>` with the following syntax:

.. code-block:: ruby
    :linenos:
    :caption: Deactivating the storage model

    from ehubx import EhubX

    ehubx = EhubX()
    ehubx.model_dir_path = "path/to/model/dir"
    ehubx.parse()
    ehubx.energy_system.deactivate_stor_techs()
    # ehubx.energy_system.reactivate_stor_techs()

Upon calling the deactivation method as in line 6, ehubX will stash the currently parsed object :code:`ehubx.energy_system.stor_techs` and replace it with an empty object of the same type, containing no storage technology candidates. The :code:`reactivate_stor_techs` command in line 7 could be used to restore the stashed version. Identical methods exist for the other submodules, and multiple deactivation calls can be combined as well. One thing to be noted is that some modules are considered submodules of others (e.g.; :code:`ehubx.model.stor_tech_model` is a submodule of :code:`ehubx.model.tech_model`). If a higher-order module were to be deactivated, it would trigger the deactivation of all its lower-order modules as well. The same goes in reverse for the reactivation syntax: If a lower-order module is reactivated, it will make sure that all higher-order modules are reactivated as well.



.. _rom:

Reduced-order modeling
-----------------------

For larger models, it becomes necessary to reduce the complexity of an ehubX model. This procedure is called *Reduced-Order Modeling (ROM)* and can be performed with the following syntax:

.. code-block:: ruby
    :caption: Basic ehubX main file

    from ehubx import EhubX, RomSettings, RomMethod

    ehubx = EhubX()
    ehubx.model_dir_path = "path/to/model/dir"
    ehubx.parse()

    # ROM
    ehubx.rom(rom_settings=RomSettings(
        method=RomMethod.CLUSTER_TSAM,
        num_ts_target=150))

    ehubx.build()
    ehubx.solve_single_obj()


The :code:`rom` function of the :code:`EhubX` object takes as one optional argument one of the implemented ROM methods. Currently, two such methods exist which will be detailed further below. The second argument :code:`num_ts_target` details a target number of time steps after clustering. This is the main setting to control the size of the ROM model, since reduction occurs alongside the time axis. In any case, calling the :code:`rom` method of the :code:`EhubX` object places a second, reduced data model inside it alongside the original model. There is an argument in the :ref:`build<building>` method which can be used to control which data set will be used to build the actual model.

.. _rom_cut:

ROM method: Cutting
^^^^^^^^^^^^^^^^^^^^

.. code-block:: ruby

    :caption: ROM method: Cutting the time horizon
    ehubx.rom(rom_settings=RomSettings(
        method=RomMethod.CUT_TIME,
        num_ts_target=150))


The first method is very simple: It drops all horizon time ids after the :code:`num_ts_target` argument in :code:`RomSettings`. Therefore, the resulting model ROM contains only horizon time steps from *1* to *num_ts_target*.

.. _rom_tsam:

ROM method: Time series aggregation (TSAM)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: ruby

    :caption: ROM method: Cutting the time horizon
    ehubx.rom(rom_settings=RomSettings(
        method=RomMethod.CLUSTER_TSAM,
        num_ts_target=150))

The second ROM method is a little more sophisticated and utilizes the `tsam <https://tsam.readthedocs.io/en/latest/>`_ Python package. It gathers all time series which have been passed to the data object and uses the clustering algorithm to compute a representative set of time steps whose size will be close to (but not less than) :code:`num_ts_target`. These time steps are then taken as the set :math:`\mathcal{V}_{Time}` while the original time steps remaing as horizon time steps :math:`\mathcal{V}_{TimeHorizon}` (see also the :ref:`times_model`). As a result, most input series and time-dependent variables will now depend on the much smaller set :math:`\mathcal{V}_{Time}` instead of :math:`\mathcal{V}_{TimeHorizon}`, thereby greatly reducing the complexity of the model.


.. _building:

Building the model
-------------------

Once the user is happy with the model data contained in the :code:`energy_system` attribute of the :code:`EhubX` object (either through :ref:`parsing` or with additional data modifications), it is time to build the model with the command

.. code-block:: ruby
    :caption: Building the energy system model

    ehubx.build()

This simple command will build the mixed-integer programming model that forms the mathematical basis of the energy system model. It will create a `Pyomo <http://www.pyomo.org/>`_ model object with all necessary variables, constraints, parameters, and objectives, and store it in the private attribute :code:`_model` of the :code:`ehubx` object. One thing of note in this process is that all possible mathematical objectives (i.e.; the optimization targets) are prepared but immediately deactivated since only one objective can be active at a time. They will be activated as needed in the :ref:`single-objective solving <single_objective_solving>` and :ref:`double-objective solving <double_objective_solving>` methods.


.. _build_rom_vs_full:

Building ROM model vs. full model
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :code:`build()` command contains an optional parameter that becomes relevant when :ref:`rom` is employed.

.. code-block:: ruby
    :caption: Building a ROM model vs. building a full-order model

    ehubx.build(use_rom=False)

The option :code:`use_rom` (*True* by default) specifies whether the ROM data or the full data should be used to build the model. This option is only relevant when a :ref:`rom` step was performed beforehand. If it is set to *True*, a reduced model will be built. If it is set to False, the :code:`EhubX` object will always build the full-order model.


.. _modifying_models:

Modifying the model
^^^^^^^^^^^^^^^^^^^^

After the :code:`build` command has been called, it is still possible to manually modify the model to introduce custom components or alter the existing model attributes. This is done as follows:

.. code-block:: ruby
    :caption: Modifying the energy system model
    :linenos:

    from ehubx import EhubX
    from pyomo.core import Var, Constraint

    ehubx = EhubX()
    ehubx.model_dir_path = "path/to/model/dir"
    ehubx.parse()
    ehubx.build()

    def my_mods(model):
        model.V_MyVar = Var()
        model.C_MyCon = Constraint(rule=lambda m: m.MyVar == 2 * m.V_ImpCostTotal)

    ehubx.modify_model(my_mods)

The custom function defined in lines 9-11 takes a Pyomo :code:`model` object as input, expecting the attribute :code:`_model` of the :code:`ehubx` object. It can then proceed to use all means that Pyomo offers to modify the model. In the above example, it introduces an additional variable called :code:`V_MyVar` and a constraint named :code:`C_MyCon` that sets the new variable as equal to twice the existing variable :code:`V_ImpCostTotal`. This function :code:`my_mods` is then passed to the interface function :code:`modify_model` of the :code:`ehubx` object which will apply the modifications. Performing meaningful modifications in this manner requires some knowledge about Pyomo and the inner workings of the :code:`ehubx.model` package's source code where the linear programming model is built. In the above example, this would mean that the user has to know that the model's collective import costs are gathered in a variable called :code:`V_ImpCostTotal`.

.. _specify_solver:

Specifying the solver
----------------------

In the ehubX solving routines :ref:`single-objective solving <single_objective_solving>` and :ref:`double-objective solving <double_objective_solving>`, the actual mathematical solving phase of the energy system model that computes an optimal solution is delegated to an external solver. We offer a specific interface to specify and customize this solver which will be demonstrated below by example of the `Gurobi <https://www.gurobi.com/>`_ solver:

.. code-block:: ruby
    :caption: Setting and customizing a solver
    :linenos:

    from ehubx import EhubX, Gurobi

    ehubx = EhubX()
    solver = Gurobi()
    solver.set_mip_focus(1)
    ehubx.set_solver(solver)

The submodule :code:`ehubx.core.solver` offers the interfaces to all supported solvers (currently, these are `Gurobi <https://www.gurobi.com/>`_ and `GLPK <https://www.gnu.org/software/glpk/>`_). Please note that in order choose a solver, it needs to be properly installed in the Python environment that is used to run ehubX. In the above example, the Gurobi solver is chosen which is created as an object in line 4. All solver options can then be specified by calling the methods of the created object, as illustrated in line 5 for the parameter :code:`mip_focus`. For detailed information about which parameters can be specified, please refer to the classes in the :code:`ehubx.core.solver` submodule. Finally, line 6 sets the customized solver for the :code:`ehubx` object. Please note that if no solver is specified, the methods for :ref:`single-objective solving <single_objective_solving>` and :ref:`double-objective solving <double_objective_solving>` will set a default solver instead.


.. _single_objective_solving:

Solving a single-objective model
---------------------------------

After a :ref:`model has been built<building>`, ehubX can solve it using a single objective function which is the standard case of mathematical optimization. This means that one objective is picked for which the system should be optimized, and the problem is passed to an external :ref:`solver<specify_solver>`. The syntax for this step is given by

.. code-block:: ruby
    :caption: Solving a single-objective model

    ehubx.solve_single_obj()

This method combines several steps, namely:

* Setting an objective (cost, emissions or autarky)
* Writing out the model to a .lp file
* Creating a solver if none is specified
* Actual solving phase
* Writing out the results

All of these steps can be customized and tailored using optional input arguments, as detailed in the :code:`ehubx.core.ehubx.solve_single_obj` method. We will illustrate the various options below.

Setting an objective
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: ruby
    :caption: Solving a single-objective model (for a specific objective)

    from ehubx import ObjectiveType

    # ... Other steps ... #

    ehubx.solve_single_obj(objective_type=ObjectiveType.CO2)

The objective can be set using the optional :code:`objective_type` input argument. For the available settings, see the :code:`ehubx.core.ehubx.ObjectiveType` class. One thing of note here is that if anything other than cost optimization is chosen, ehubX will add a tiny portion of the total cost variable to the chosen objective function anyway. This means that if, for example, CO2 optimization will try to minimize the variable :math:`\mathcal{V}_{SystemCo2Total}`, the actually employed cost function will be :math:`\mathcal{V}_{SystemCo2Total} + \varepsilon \cdot \mathcal{V}_{SystemCost}`, with :math:`0 < \varepsilon \ll 1`. This is done because a lot of constraints in the system are formalized in such a way that they expect the model to minimize costs in a certain sense. If this tiny portion of cost minimization were not included, a lot of problems would arise, having to do with non-uniqueness of solutions or linearization tricks not working.


Setting a solver kind
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: ruby
    :caption: Solving a single-objective model (with solver specification)

    from ehubx import SolverKind

    # ... Other steps ... #

    ehubx.solve_single_obj(solver_kind=SolverKind.GLPK)

The optional input argument :code:`solver_kind` allows for the setting of a specific solver kind. The existence of this argument allows the user to skip :ref:`specifying a solver<specify_solver>` if they do not intend to fine-tune the solver by setting specific options. The solving procedure will then set the requested solver with default arguments.


Writing out the model
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: ruby
    :caption: Solving a single-objective model (and writing a model file)

    ehubx.solve_single_obj(write_model=True,
                           model_lp_path="path/to/model.lp")

ehubX can write out the entire model before solving to an .lp file whose location can be specified in the argument :code:`model_lp_path`. If no model file should be written, the argument :code:`write_model` can be set to :code:`False`. It has to be noted here that writing a model can take a long time, dependent on the size, so if the user has no intention of working with the model file, this phase should be skipped.


Writing out the solution
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: ruby
    :caption: Solving a single-objective model (and writing a results file)

    from ehubx import FileGranularity

    # Other steps ...

    ehubx.solve_single_obj(results_dir_path="results_myrun",
                           opt_vars_filename="opt_vars.csv",
                           file_granularity=FileGranularity.MIN)

After the solving was performed, ehubX offers various options to write out the model. First of all, the argument :code:`results_dir_path` can be used to specify the path relative to the model directory where ehubX will save all result files. The default value for this argument is :code:`results`.

Second, the optional argument :code:`opt_vars_filename` specifies the name of a file which will contain all optimization variables of the mathematical model which have taken nonzero values.

.. image:: img/opt_vars.png
   :width: 1000
   :alt: Result file with nonzero optimization variables

The names of the variables (in the column *var_name* should be identical to the ones in the :ref:`model documentation<model>`. The column :code:`var_value` contains the value of the variable. All other columns hold indices of the variable, and the column names should align with the set names used in the :ref:`model documentation<model>` as well.


In addition to this generic model output, customized outputs will be generated as well. These will take the form of multiple csv files and hold a combination of input and output data. The files will be organized into categories *system*, *techs*, *import_export*, *loads* and *network*.

.. image:: img/result_files_modules.png
   :width: 200
   :alt: Result files organized by modules

Additionally, output files are be split into *static* (i.e.; not time-dependent) values, time-dependent values (suffix :code:`-TS` in filename), and cluster-time-dependent values (suffix :code:`-TSCL` in filename).

Furthermore, the granularity to which results are split across different files can be controlled by the argument :code:`file_granularity` which may take one of three predefined settings:

**FileGranularity.MIN:**

Three files are created per system, tech, import-export, load and network section (static, time-dependent, cluster-dependent).

**FileGranularity.DEFAULT:**

* The system-wide values are unchanged from the minimal file granularity.
* One output file is created for each tech.
* One output file is created for each (stage, hub, ec) tuple in imports and exports.
* One output file is created for each (stage, hub, ec) tuple in loads.
* One output file is created for each network link.

**FileGranularity.MAX:**

* The system-wide values are unchanged from the minimal file granularity.
* The per-tech output files are further split according to their submodules (e.g.; conversion / storage / ...)
* The per-tuple output files in import-export are further split to separate import and export data.
* The per-tuple output files in loads are further split to separate demands, load shedding and load shifting.
* The per-link output files in networks are further split to separate the employed network techs.


.. _double_objective_solving:

Solving a double-objective model
---------------------------------

After a :ref:`model has been built<building>`, ehubX can solve it for two objectives simultaneously, a process that is known in the mathematical domain as *multi-objective optimization**. The aim of this process is to find the set of *optimal compromises*. This denotes the set of all variable configurations that are feasible with the constraints, and which have optimized one of the objective functions to an extent where it is not possible to further improve them without at the same time deteriorating the second objective function. When the two objectives stand in conflict, this generally leads to a whole set of objective values which are considered *optimal* under this definition, a set that is referred to as the *Pareto set*. The main task of the double-objective optimization procedure is to compute a numerical approximation of this - generally infinite - set by a suitable algorithm. To give a visualization, below is a figure containing such an approximation in graphical form:

.. image:: img/pareto_front.png
   :width: 600
   :alt: Pareto front for a double-objective optimization with cost and emission objective functions.

In this example, the chosen objectives were to

a) minimize the overall system cost, and
b) minimize the overall system emissions.

We notice that all of the computed optima are incomparable against each other since further decreasing e.g.; the cost value always comes at the cost of an increase in the emissions value.

In ehubX, this double-objective optimization is carried out by the command:

.. code-block:: ruby
    :caption: Solving a double-objective model

    ehubx.solve_double_obj()

This method combines several steps, namely:

* Writing out the model to a .lp file for one of the objectives
* Selecting a multi-objective algorithm if none is selected
* Setting the number of Pareto points that will be computed if none is selected
* Performing the multi-objective algorithm.
* In each iteration of the algorithm (which entails solving a single-objective optimization problem on its own), writing out the results of this iteration to a csv file

All of these steps can be customized and tailored using optional input arguments, as detailed in the :code:`ehubx.core.ehubx.solve_double_obj` method. We will illustrate the various options below.


Setting the objectives
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: ruby
    :caption: Solving a double-objective model (for specific objectives)

    from ehubx import ObjectiveType

    # ... Other steps ... #

    ehubx.solve_double_obj(obj_type_1=ObjectiveType.COST,
                           obj_type_2=ObjectiveType.CO2)

The objectives can be set using the optional :code:`obj_type_1` and :code:`obj_type_2` input arguments. For the available settings, see the :code:`ehubx.core.ehubx.ObjectiveType` class.


Setting a solver kind
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: ruby
    :caption: Solving a double-objective model (for specific objectives)

    from ehubx import SolverKind

    # ... Other steps ... #

    ehubx.solve_double_obj(solver_kind=SolverKind.GLPK)

This section works identically as setting the solver kind for :ref:`single-objective solves<single_objective_solving>`.


Choosing the number of computed Pareto points
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: ruby
    :caption: Solving a double-objective model (for a specific number of Pareto points)

    ehubx.solve_double_obj(num_pareto_points=4)

ehubX will compute a certain number of Pareto points which are used to approximate the Pareto front. The total number of these can be set by specifying the optional argument :code:`num_pareto_points`. Keep in mind that for the calculation of each Pareto point, a single-objective optimization problem will be solved under the hood. So choosing too high a value here can quickly blow up the solving time here.


Selecting a multiobjective algorithm
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: ruby
    :caption: Solving a double-objective model (with a specific multi-objective algorithm)

    from ehubx import MultiObjMethod

    # ... Other steps ... #

    ehubx.solve_double_obj(method=MultiObjMethod.EPSCONSTRAINT)

Two multiobjective algorithms can be selected in ehubX that will compute an approximation of the Pareto front. The method can be selected by specifying the optional input argument :code:`method` which expects an instance of the enumeration class :code:`ehubx.core.ehubx.MultiObjMethod`. The two strategies, briefly explained, are as follows:

a) **Weighted-sum method**: This method takes the two objectives :math:`O_1`,  :math:`O_2` and a weight :math:`\omega \in [0,1]` and sets the *weighted-sum objective* of :math:`O_\omega = \omega \cdot O_1 + (1-\omega) \cdot O_2`. Under certain conditions which are usually satisfied in the sort of models built with ehubX, this will produce a Pareto-optimal point. The weighted-sum algorithm will work with several weights :math:`\omega_1, ..., \omega_n` to produce a total number of :math:`n` Pareto points, as specified by the optional argument :code:`num_pareto_points`. Please note that it is not guaranteed that all computed Pareto points will be distinct. It is entirely possible that different values for :math:`\omega` will produce the same Pareto point, depending on the problem.
b) **Epsilon-constraint method**: This method chooses the first objective :math:`O_1` and optimize the system for this objective only. At the same time, it adds a constraint that the second objective :math:`O_2` be bounded by a threshold value :math:`\varepsilon` by :math:`O_2 \le \varepsilon` (if :math:`O_2` is to be minimized), or :math:`O_2 \ge \varepsilon` (if :math:`O_2` is to be maximized). Varying the threshold value :math:`\varepsilon` will produce different Pareto points. This is repeated until a number of Pareto points equal to the optional argument :code:`num_pareto_points` has been computed.


Writing out the model
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: ruby
    :caption: Solving a double-objective model (and writing a model file)

    ehubx.solve_double_obj(write_model=True)

The optional argument :code:`write_model` can be used to dictate whether a model.lp file should be written for the first objective function. It has to be noted here that writing a model can take a long time, dependent on the size, so if the user has no intention of working with the model file, this phase should be skipped.


Specifying the results directory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: ruby
    :caption: Solving a double-objective model (and setting a time stamp for the multiobjective subdirectory)

    ehubx.solve_double_obj(results_dir_path = "results")

The solutions to a multiobjective run will be saved in a directory whose path can be specified using the optional argument :code:`results_dir_path`, relative to the model directory.
