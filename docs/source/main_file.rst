.. _main_file:

The main file
===============

Interacting with the ehubX library is typically performed in a main Python file, which in its most basic form resembles the following:

.. code-block:: ruby
    :caption: Basic ehubX main file

    from ehubx import EhubX, Gurobi

    # Create an EhubX object
    ehubx = EhubX()
    # Set the model path and parse the input files
    ehubx.model_dir_path = "path/to/model/dir"
    ehubx.parse()
    # Build the model
    ehubx.build()
    # Set the solver
    ehubx.set_solver(Gurobi())
    # Solve using a single objective
    ehubx.solve_single_obj()
    # Solve using two objectives
    ehubx.solve_double_obj()

In the sections that follow, we will examine each block in this main file in detail, explaining the processes involved and the various options available to customize an ehubX run.


.. _ehubx_object:

The EhubX Object
-----------------

.. code-block:: ruby
    :linenos:
    :caption: Creating an EhubX object

    ehubx = EhubX()

The ehubX class serves as the primary interface through which users can access the platform's functionalities. The process begins with the creation of an ehubX object.


.. _parsing:

Parsing from Input Files
-------------------------

.. code-block:: ruby
    :linenos:
    :caption: Parsing from input files

    ehubx.model_dir_path = "path/to/model/dir"
    ehubx.parse()

The primary method for defining an ehubX model is through :ref:`input files <input_files>`. Each model must be located in a *model directory* and follow a specific structure, as detailed in the :ref:`file overview <file_overview>`. In line 1, we direct the ehubX object to the model directory. Line 2 then parses all data from the input files, creating the attribute :code:`ehubx.energy_system`, which is an instance of the class :code:`ehubx.data.energy_system_data.EnergySystem`.

Modifying model data through code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For a typical application, the aforementioned step is sufficient to load the model data into the ehubX object. However, since each attribute in ehubX has its own getters and setters, there is also the option to modify the model data afterward, as demonstrated below:

.. code-block:: ruby
    :linenos:
    :caption: Modifying model data after parsing

    from ehubx import EhubX
    from ehubx.data import stage_data, hub_data, ec_data, time_data, value

    ehubx = EhubX()
    ehubx.model_dir_path = "path/to/model/dir"
    ehubx.parse()
    ehubx.energy_system.imports.set_max(stage_data.StageId("S1"),
                                        hub_data.HubId("H1"),
                                        ec_data.EcId("E1"),
                                        time_data.TimeId(2),
                                        value.Value.from_str("500kW"))

In the example above, we access the :code:`imports` section of the energy system data to set a maximum import threshold of 500kW for a specific stage, hub, ec, and time (refer to the parameter *max* of :ref:`imports.yaml <imports_yaml>`). To utilize the ehubX classes :code:`StageId`, :code:`HubId`, :code:`EcId`, :code:`TimeId`, and :code:`Value`, these are imported in line 2. It is important to note that modifying and retrieving parameters in this manner requires a deeper understanding of the ehubX source code. However, as a general guideline, every parameter *x* in the :ref:`input files <input_files>` will have corresponding getter and setter methods named :code:`get_x` and :code:`set_x`, which can be used for modification and retrieval.

Deactivating submodules
^^^^^^^^^^^^^^^^^^^^^^^^

As an additional option, users can deactivate and reactivate most of the ehubX submodules entirely. For instance, if a user wishes to test how the model would change without storage technologies, they can deactivate the :ref:`storage model <storage_model>` using the following syntax:

.. code-block:: ruby
    :linenos:
    :caption: Deactivating the storage model

    from ehubx import EhubX

    ehubx = EhubX()
    ehubx.model_dir_path = "path/to/model/dir"
    ehubx.parse()
    ehubx.energy_system.deactivate_stor_techs()
    # ehubx.energy_system.reactivate_stor_techs()

By invoking the deactivation method in line 6, ehubX will store the currently parsed object :code:`ehubx.energy_system.stor_techs` and replace it with an empty object of the same type, which contains no storage technology candidates. The :code:`reactivate_stor_techs` command in line 7 can be used to restore the previously stored version. Similar methods exist for other submodules, and multiple deactivation calls can be combined as well. It is important to note that some modules are considered submodules of others (e.g., :code:`ehubx.model.stor_tech_model` is a submodule of :code:`ehubx.model.tech_model`). If a higher-order module is deactivated, it will also deactivate all its lower-order modules. Conversely, if a lower-order module is reactivated, it will ensure that all higher-order modules are reactivated as well.



.. _rom:

Reduced-order modeling
-----------------------

For larger models, it becomes advantageous to reduce the complexity of an ehubX model. This procedure is called *Reduced-Order Modeling (ROM)* and can be performed with the following syntax:

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


The :code:`rom` function of the :code:`EhubX` object accepts as one optional argument an instance of the implemented ROM methods. Currently, two such methods exist, which will be detailed further below. The second argument, :code:`num_ts_target`, specifies a target number of time steps after clustering. This is the primary setting to control the size of the ROM model, as reduction occurs along the time axis. In any case, calling the :code:`rom` method of the :code:`EhubX` object creates a second, reduced data model within it alongside the original model. An argument in the :ref:`build <building>` method can be used to control which data set will be employed to build the actual model.

.. _rom_cut:

ROM method: Cutting
^^^^^^^^^^^^^^^^^^^^

.. code-block:: ruby

    :caption: ROM method: Cutting the time horizon
    ehubx.rom(rom_settings=RomSettings(
        method=RomMethod.CUT_TIME,
        num_ts_target=150))


The first method is straightforward: it drops all horizon time IDs after the :code:`num_ts_target` argument in :code:`RomSettings`. Therefore, the resulting ROM model contains only horizon time steps from *1* to *num_ts_target*.

.. _rom_tsam:

ROM method: Time series aggregation (TSAM)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: ruby

    :caption: ROM method: Time series aggregation using TSAM
    ehubx.rom(rom_settings=RomSettings(
        method=RomMethod.CLUSTER_TSAM,
        num_ts_target=150))

The second ROM method is more sophisticated and utilizes the `tsam <https://tsam.readthedocs.io/en/latest/>`_ Python package. It gathers all time series that have been passed to the data object and uses a clustering algorithm to compute a representative set of time steps whose size will be close to (and not less than) :code:`num_ts_target`. These time steps are then taken as the set :math:`\mathcal{V}_{Time}`, while the original time steps remain as horizon time steps :math:`\mathcal{V}_{TimeHorizon}` (see also the :ref:`times model <times_model>`). As a result, most input series and time-dependent variables will now depend on the smaller set :math:`\mathcal{V}_{Time}` instead of :math:`\mathcal{V}_{TimeHorizon}`, thereby greatly reducing the complexity of the model.


.. _building:

Building the model
-------------------

Once the user is satisfied with the model data contained in the :code:`energy_system` attribute of the :code:`EhubX` object (either through :ref:`parsing` or with additional data modifications), the next step is to build the model using the command

.. code-block:: ruby
    :caption: Building the energy system model

    ehubx.build()

This straightforward command constructs the mixed-integer programming model that forms the mathematical foundation of the energy system model. It creates a `Pyomo <http://www.pyomo.org/>`_ model object with all necessary variables, constraints, parameters, and objectives, and stores it in the private attribute :code:`_model` of the :code:`ehubx` object. It is worth noting that during this process, all possible mathematical objectives (i.e., the optimization targets) are prepared but immediately deactivated, since only one objective can be active at a time. They will be activated as needed in the :ref:`single-objective solving <single_objective_solving>` and :ref:`double-objective solving <double_objective_solving>` methods.


.. _build_rom_vs_full:

Building ROM model vs. full model
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :code:`build()` command includes an optional parameter that is relevant when :ref:`ROM <rom>` is employed.

.. code-block:: ruby
    :caption: Building a ROM model vs. building a full-order model

    ehubx.build(use_rom=False)

The :code:`use_rom` option (*True* by default) specifies whether the ROM data or the full data should be used to build the model. This option is only relevant when a :ref:`ROM <rom>` step has been performed beforehand. If set to *True*, a reduced model will be built. If set to *False*, the :code:`EhubX` object will build the full-order model instead.


.. _modifying_models:

Modifying the model
^^^^^^^^^^^^^^^^^^^^

After the :code:`build` command has been called, it is still possible to manually modify the model to introduce custom components or alter existing model attributes. This is accomplished as follows:

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

The custom function defined in lines 9-11 takes a Pyomo :code:`model` object as input, expecting the :code:`_model` attribute of the :code:`ehubx` object. It can then utilize all capabilities that Pyomo offers to modify the model. In the example above, an additional variable called :code:`V_MyVar` is introduced along with a constraint named :code:`C_MyCon` that sets the new variable equal to twice the existing variable :code:`V_ImpCostTotal`. This function :code:`my_mods` is then passed to the :code:`modify_model` interface function of the :code:`ehubx` object, which applies the modifications. Performing meaningful modifications in this manner requires knowledge of Pyomo and the inner workings of the :code:`ehubx.model` package's source code, where the linear programming model is constructed. In the example above, this means the user must know that the model's collective import costs are stored in a variable called :code:`V_ImpCostTotal`.

.. _specify_solver:

Specifying the solver
----------------------

In the ehubX solving routines :ref:`single-objective solving <single_objective_solving>` and :ref:`double-objective solving <double_objective_solving>`, the actual mathematical solving phase of the energy system model that computes an optimal solution is delegated to an external solver. We offer a specific interface to specify and customize this solver, which will be demonstrated below using the `Gurobi <https://www.gurobi.com/>`_ solver as an example:

.. code-block:: ruby
    :caption: Setting and customizing a solver
    :linenos:

    from ehubx import EhubX, Gurobi

    ehubx = EhubX()
    solver = Gurobi()
    solver.set_mip_focus(1)
    ehubx.set_solver(solver)

The submodule :code:`ehubx.core.solver` provides interfaces to all supported solvers (currently `Gurobi <https://www.gurobi.com/>`_ and `GLPK <https://www.gnu.org/software/glpk/>`_). Please note that in order to choose a solver, it must be properly installed in the Python environment used to run ehubX. In the example above, the Gurobi solver is chosen and created as an object in line 4. All solver options can then be specified by calling methods of the created object, as illustrated in line 5 for the parameter :code:`mip_focus`. For detailed information about which parameters can be specified, please refer to the classes in the :code:`ehubx.core.solver` submodule. Finally, line 6 sets the customized solver for the :code:`ehubx` object. Please note that if no solver is specified, the methods for :ref:`single-objective solving <single_objective_solving>` and :ref:`double-objective solving <double_objective_solving>` will set a default solver instead.


.. _single_objective_solving:

Solving a single-objective model
---------------------------------

After a model has been built, ehubX can solve it using a single objective function, which is the standard case of mathematical optimization. This means that one objective is selected for which the system should be optimized, and the problem is then passed to an external :ref:`solver <specify_solver>`. The syntax for this step is as follows:

.. code-block:: ruby
    :caption: Solving a single-objective model

    ehubx.solve_single_obj()

This method combines several steps, namely:

* Setting an objective (cost, emissions, autonomy, or self-sufficiency)
* Writing out the model to an .lp file
* Creating a solver if none is specified
* The actual solving phase
* Writing out the results

All of these steps can be customized and tailored using optional input arguments, as detailed in the :code:`ehubx.core.ehubx.solve_single_obj` method. We will illustrate the various options below.

Setting an objective
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: ruby
    :caption: Solving a single-objective model (for a specific objective)

    from ehubx import ObjectiveType

    # ... Other steps ... #

    ehubx.solve_single_obj(objective_type=ObjectiveType.CO2)

The objective can be set using the optional :code:`objective_type` input argument. For the available settings, refer to the :code:`ehubx.core.ehubx.ObjectiveType` class. It is important to note that if an optimization other than cost is selected, ehubX will nevertheless incorporate a small fraction of the total cost variable into the chosen objective function. For instance, if CO2 minimization is selected, the effective cost function will be represented as :math:`\mathcal{V}_{SystemCo2Total} + \varepsilon \cdot \mathcal{V}_{SystemCost}`, where :math:`0 < \varepsilon \ll 1`. This approach is necessary because many constraints within the system are structured to expect a minimization of costs. Omitting this small cost component could lead to issues such as non-uniqueness of solutions or the failure of certain linearization techniques.


Setting a solver kind
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: ruby
    :caption: Solving a single-objective model (with solver specification)

    from ehubx import SolverKind

    # ... Other steps ... #

    ehubx.solve_single_obj(solver_kind=SolverKind.GLPK)

The optional input argument :code:`solver_kind` allows for the setting of a specific solver kind. The existence of this argument allows the user to skip :ref:`specifying a solver <specify_solver>` if they do not intend to fine-tune the solver by setting specific options. The solving procedure will then set the requested solver with default arguments.


Writing out the model
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: ruby
    :caption: Solving a single-objective model (and writing a model file)

    ehubx.solve_single_obj(write_model=True,
                           model_lp_path="path/to/model.lp")

ehubX can export the entire model to an .lp file prior to solving, with the file's location specified by the argument :code:`model_lp_path`. If there is no need to write a model file, the argument :code:`write_model` can be set to :code:`False`. It is important to note that writing a model may take considerable time, depending on its size; therefore, if the user does not intend to utilize the model file, this step should be omitted.


Writing out the solution
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: ruby
    :caption: Solving a single-objective model (and writing a results file)

    from ehubx import FileGranularity

    # Other steps ...

    ehubx.solve_single_obj(results_dir_path="results_myrun",
                           opt_vars_filename="opt_vars.csv",
                           file_granularity=FileGranularity.MIN)

After the solving process is completed, ehubX provides several options for outputting the model results. Firstly, the argument :code:`results_dir_path` allows you to specify the path relative to the model directory where ehubX will save all result files. By default, this argument is set to :code:`results`.

Secondly, the optional argument :code:`opt_vars_filename` designates the name of a file that will contain all optimization variables of the mathematical model that have nonzero values.

.. image:: img/opt_vars.png
    :width: 1000
    :alt: Result file with nonzero optimization variables

The variable names in the *var_name* column match those in the :ref:`model documentation <model>`. The *var_value* column contains the corresponding values of the variables. All other columns represent indices of the variables, and the column names align with the set names used in the :ref:`model documentation <model>`.

In addition to this standard model output, customized outputs will also be generated. These will take the form of multiple CSV files that contain a combination of input and output data. The files will be organized into categories: *system*, *techs*, *import_export*, *loads*, and *network*.

.. image:: img/result_files_modules.png
    :width: 200
    :alt: Result files organized by modules

Furthermore, the output files are categorized into *static* (i.e., not time-dependent) values, time-dependent values (indicated by the suffix :code:`-TS` in the filename), and cluster-time-dependent values (indicated by the suffix :code:`-TSCL` in the filename).

Furthermore, the granularity with which results are divided across different files can be controlled by the argument :code:`file_granularity`, which accepts one of three predefined settings:

**FileGranularity.MIN:**

Three files are generated for each system, tech, import-export, load, and network section (static, time-dependent, cluster-dependent).

**FileGranularity.DEFAULT:**

* The system-wide values remain unchanged from the minimal file granularity.
* One output file is created for each tech.
* One output file is generated for each (stage, hub, ec) tuple in imports and exports.
* One output file is produced for each (stage, hub, ec) tuple in loads.
* One output file is created for each network link.

**FileGranularity.MAX:**

* The system-wide values remain unchanged from the minimal file granularity.
* The per-tech output files are further divided according to their submodules (e.g., conversion / storage / ...).
* The per-tuple output files in import-export are further split to separate import and export data.
* The per-tuple output files in loads are further divided to distinguish between demands, load shedding, and load shifting.
* The per-link output files in networks are further split to separate the employed network technologies.


.. _double_objective_solving:

Solving a double-objective model
---------------------------------

After a :ref:`model has been built <building>`, ehubX can solve it for two objectives simultaneously, a process known in the mathematical domain as *multi-objective optimization*. The goal of this process is to identify the set of *optimal compromises*. This set encompasses all variable configurations that are feasible within the constraints and have optimized one of the objective functions to a degree where further improvement is not possible without simultaneously degrading the second objective function. When the two objectives conflict, this typically results in a collection of objective values considered *optimal* under this definition, referred to as the *Pareto set*. The primary task of the double-objective optimization procedure is to compute a numerical approximation of this generally infinite set using a suitable algorithm. To illustrate this, below is a figure depicting such an approximation in graphical form:

.. image:: img/pareto_front.png
    :width: 600
    :alt: Pareto front for a double-objective optimization with cost and emission objective functions.

In this example, the selected objectives were to

a) minimize the overall system cost, and
b) minimize the overall system emissions.

It is evident that all computed optima are incomparable with one another, as further reducing, for instance, the cost value invariably results in an increase in the emissions value.

In ehubX, this double-objective optimization is carried out by the command:

.. code-block:: ruby
    :caption: Solving a double-objective model

    ehubx.solve_double_obj()

This method combines several steps, namely:

* Writing out the model to a .lp file for one of the objectives
* Selecting a multi-objective algorithm if none is selected
* Setting the target number of Pareto points that will be computed if none is selected
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

The objectives can be specified using the optional :code:`obj_type_1` and :code:`obj_type_2` input arguments. For a list of available settings, refer to the :code:`ehubx.core.ehubx.ObjectiveType` class.


Setting a solver kind
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: ruby
    :caption: Solving a double-objective model (for specific objectives)

    from ehubx import SolverKind

    # ... Other steps ... #

    ehubx.solve_double_obj(solver_kind=SolverKind.GLPK)

This section works identically as setting the solver kind for :ref:`single-objective solves <single_objective_solving>`.


Choosing the number of computed Pareto points
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: ruby
    :caption: Solving a double-objective model (for a specific number of Pareto points)

    ehubx.solve_double_obj(num_pareto_points=4)

ehubX computes a specified number of Pareto points to approximate the Pareto front. The total number of these points can be set by specifying the optional argument :code:`num_pareto_points`. It is important to note that for each Pareto point, a single-objective optimization problem is solved internally. Therefore, selecting a high value for this parameter may significantly increase the solving time.


Selecting a multiobjective algorithm
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: ruby
    :caption: Solving a double-objective model (with a specific multi-objective algorithm)

    from ehubx import MultiObjMethod

    # ... Other steps ... #

    ehubx.solve_double_obj(method=MultiObjMethod.EPSCONSTRAINT)

Two multi-objective algorithms can be selected in ehubX to compute an approximation of the Pareto front. The method can be specified by using the optional input argument :code:`method`, which expects an instance of the enumeration class :code:`ehubx.core.ehubx.MultiObjMethod`. The two strategies are briefly explained here:

a) **Weighted-sum method**: This method takes the two objectives :math:`O_1` and :math:`O_2`, along with a weight :math:`\omega \in [0,1]`, to set the *weighted-sum objective* as :math:`O_\omega = \omega \cdot O_1 + (1-\omega) \cdot O_2`. Under certain conditions, which are typically satisfied in models built with ehubX, this approach will yield a Pareto-optimal point. The weighted-sum algorithm will utilize several weights :math:`\omega_1, ..., \omega_n` to produce a total of :math:`n` Pareto points, as specified by the optional argument :code:`num_pareto_points`. It is important to note that it is not guaranteed that all computed Pareto points will be distinct; different values for :math:`\omega` may lead to the same Pareto point, depending on the specific problem.

b) **Epsilon-constraint method**: This method focuses on the first objective :math:`O_1` and optimizes the system solely for this objective. Simultaneously, it introduces a constraint that bounds the second objective :math:`O_2` by a threshold value :math:`\varepsilon`, such that :math:`O_2 \le \varepsilon` (if :math:`O_2` is to be minimized) or :math:`O_2 \ge \varepsilon` (if :math:`O_2` is to be maximized). By varying the threshold value :math:`\varepsilon`, different Pareto points can be generated. This process is repeated until the number of computed Pareto points matches the optional argument :code:`num_pareto_points`.


Writing out the model
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: ruby
    :caption: Solving a double-objective model (and writing a model file)

    ehubx.solve_double_obj(write_model=True)

The optional argument :code:`write_model` can be used to specify whether a model.lp file should be written for the first objective function. It is important to note that writing a model may take considerable time, depending on its size; therefore, if the user does not intend to utilize the model file, this step should be omitted.


Specifying the results directory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: ruby
    :caption: Solving a double-objective model (and setting a time stamp for the multiobjective subdirectory)

    ehubx.solve_double_obj(results_dir_path = "results")

The solutions to a multi-objective run will be saved in a directory whose path can be specified using the optional argument :code:`results_dir_path`, relative to the model directory.
