Input structure
================

.. _parameter_types:

Parameter types
----------------

.. code-block:: ruby
    :caption: Parameter types

    empty_param:
    scalar_param: 42
    yeardep_param: [[2020, 0.85], [2025, 0.90]]
    timeseries_param: link/to/series.csv

* **Empty parameters**: Same functionality as if the *empty_param* parameter did not occur at all.If *empty_param* is an optional key, no value will be set and the default value will be used for it. If it is mandatory, an error will be thrown.
* **Scalar parameters**: This singular value will be set. If the parameter is considered stage- or time-dependent in the model, this scalar value will be used for all stages and/or timesteps.
* **Year-dependent parameters**: The value is given as an array of arrays. Each of the interior arrays has to contain two elements: a year and a value. This way, we parameterize a piecewise constant year-to-value function. For every stage in the model, its stage year will be used to obtain an interpolated value from this piecewise constant function, taking the function's value from the closest year node before the stage year. For stage years before the earliest year node, the first node value will be assigned. In the above example, all stage years until 2024 will be assigned the value 0.85 and all stage years starting from 2025 will be assigned the value 0.90.
* **Transient parameters**: If the parameter is *transient* (i.e., time-dependent), it is given in an external csv file whose path relative to the current yaml file is passed as value. The structure of these csv files depends on the type of parameter in question but an overview for csv files is given in the section :ref:`csv_files`. Specific details for each transient parameter are given at the subsection of :ref:`input_files` for the file the parameter occurs in.


.. _list_types:

List types
-----------

.. code-block:: ruby
    :caption: List types

    empty_list: []

    simple_list_inline: [2.4, 3.6, 4.8]

    simple_list_bullet:
    - 2.4
    - 3.6
    - 4.8

    identifiable_list:
    - list_id: i1
      some_param: 0.24
    - list_id: i2
      some_param: 0.36
    - list_id: i3
      some_param: 0.48

* **Empty lists**: This is the only way to pass an empty list. If :code:`[]` is not specified, the yaml node :code:`empty_list` will not be interpreted as an empty list but as an *empty parameter* (see :ref:`parameter types<parameter_types>`).
* **Inline lists**: If the list in question has a relatively simple structure (e.g., an array of floats), then it can be passed in the same line as the list name, after the colon. Note that this list type is also used for the specification of a *year-dependent parameter* (see :ref:`parameter types<parameter_types>`).
* **Simple multiline lists**: A list can equivalently be passed in bullet form. Note that in the above example, :code:`simple_list_inline` and :code:`simple_list_bullet` are completely equivalent after parsing.
* **Identifiable lists**: When the members of a list become dictionary nodes themselves, we demand that these members each contain a special *id* parameter by which we can refer to them. The name of this identifier depends on the yaml node in question: In the above example, it is :code:`list_id` but in ehubX input documents, we often see e.g., :code:`hub_id` or :code:`tech_id`. During the parsing process, it is verified that each list member has the required identifier and that there are no duplicates within the list.


.. _csv_files:

csv files
----------

.. code-block:: ruby
    :caption: csv file structure

    header_1, I_11, ..., I_1m
       ...    ...         ...
    header_n, I_n1, ..., I_nm
    -------------------------
    J_1,      0.3,  ..., 0.8
    ...       ...        ...
    J_r,      0.4,  ..., 0.9

CSV files in ehubX all adher to the same basic structure which is depicted above (be aware that the dashed line is not actually part of the csv document but only serves to visualize the distinction between header and body).

* The file starts with n rows that make up the *header* of the csv file. Each of these rows can be considered as the dimension of an n-dimensional index tuple.

  * The keys for these header rows (:code:`header_1`, ..., :code:`header_n`) are collected in the first column and must take exact string values that are expected by ehubX. These will depend on the csv file in question but usually contain values like :code:`stage_id`, :code:`hub_id`, :code:`tech_id` or :code:`ec_id`.
  * For each of the following columns, the header rows contain an index tuple (e.g.; (:code:`I_11`, ..., :code:`I_n1`) for the second column). This is used to identify the column in the input parser. These index tuples must not contain any duplicates.

* Below the header starts the *body* of the csv file.

  * The first column contains the *indices* of the csv file.
  * Starting from the second column, here are the *values* of the csv file.

While this denotes the general structure of an ehubX csv file, there is one heavily used special case where the csv file is used to define time-specific model parameters. Usually, these parameters will have a *default value* that is specified in a yaml file in the following manner:

.. code-block:: ruby
    :caption: Setting a time-dependent parameter with default value (yaml)

    example_param: 0.5
    profile_path: profiles.csv

The parameter :code:`example_param` has its default value of 0.5 set in a yaml file. This value will be used for all indices that are not part of the file :code:`profiles.csv` which may look like this:

.. code-block:: ruby
    :caption: Setting a time-dependent parameter with default value (csv)

    stage_id,    S1
    profile_key, example_param
    1,           0.30
    2,           0.35
    3,           0.40

This way, the parameter value for the time steps 1 to 3 and the stage :code:`S1` will be used by the model. For all other time steps and all other stages, the default value of 0.5 set in the above yaml will be used. This rule of *time-dependent before default* is followed for every input parameter.

.. _node_paths:

Node paths
-----------

During parsing, it usually occurs that ehubX gives feedback on the input strucutre, e.g., if a mandatory parameter is missing or an unexpected value was set for a parameter. In this case, ehubX will refer to the file path in which the parameter was specified and give a so-called **node path** to the node of the parameter. This might look something like this:

.. code-block:: console
    :caption: Referencing a parameter

    Parsing exception in file /path/to/project/inputs/hubs.yaml: Missing mandatory value detected at node hubs["H1"]/techs["X1"]/tech_params/param_name

The originating file had this structure:

.. code-block:: ruby
    :caption: Source file with missing parameter

    hubs:
    - hub_id: H1
      techs:
      - tech_id: X1
        tech_params:
            param_name:  # Missing value

As can be seen, the node path is a chain of elements of the following two types:

* If the parameter is contained in a dictionary with a specific name (e.g.; :code:`tech_params` above), the node path will contain this name followed by a forward slash (e.g.; :code:`tech_params/` above).
* If the path to the parameter goes through a specific element of an *identifiable list* (see :ref:`list types<list_types>`, e.g.; :code:`hubs` and :code:`techs` above), the name of that identifiable list and the unique identifier of the list element enter the node path in the same way as one would reference a dictionary element in Python (e.g.; :code:`hubs["H1"]` and :code:`techs["X1"]` above).

In this way, every yaml node in an ehubX input document can be referenced in a readable way.

.. _units:

Units
------

.. list-table:: ehubX base units
    :header-rows: 1

    * - Energy
      - Power
      - Mass
      - Cost
      - Length
      - Area
      - Capacity
      - Unitless

    * - kWh
      - kW
      - kg
      - CHF
      - m
      - :math:`m^2`
      - CAP
      - 1

Note: A tech's capacity unit differs from module to module, so the generic unit of CAP has been introduced here. For example, a storage technology's capacity is measured in energy but a solar technology's capacity is given in area.
