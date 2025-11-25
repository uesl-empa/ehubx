Input structure
================

ehubX is based around yaml and csv files. The input structure is designed to be human-readable and machine-parseable at the same time. This document describes the basic structure of the input files, the types of lists and parameters, how to reference nodes in the input files, and the expected structure of the files. While reading this section, it is recommended to have a look at the example input files in the :code:`examples/` directory of the ehubX repository.

.. _list_types:

List types in yaml files
--------------------------

The yaml files in ehubX contain many nodes that can be nested within each other, resulting in a tree-like structure. The most basic of these nodes is the list node, which can take several forms. The following example shows the different types of lists that can be used in ehubX yaml files:

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

* **Empty lists**: This is the only way to pass an empty list. If :code:`[]` is not specified, the yaml node :code:`empty_list` will not be interpreted as an empty list but as an *empty parameter* (see :ref:`parameter types <parameter_types>`).
* **Inline lists**: If the list in question has a relatively simple structure (e.g., an array of floats), it can be passed on the same line as the list name, after the colon. Note that this list type is also used for the specification of a *year-dependent parameter* (see :ref:`parameter types <parameter_types>`).
* **Simple multiline lists**: A list can equivalently be passed in bullet form. Note that in the above example, :code:`simple_list_inline` and :code:`simple_list_bullet` are completely equivalent after parsing.
* **Identifiable lists**: When the members of a list become dictionary nodes themselves, we require that these members each contain a special *id* parameter by which we can refer to them. The name of this identifier depends on the yaml node in question: In the above example, it is :code:`list_id`, but in ehubX input documents, we often see identifiers such as :code:`hub_id` or :code:`tech_id`. During the parsing process, it is verified that each list member has the required identifier and that there are no duplicate identifiers within the list.


.. _node_paths:

Node paths
-----------

During parsing, ehubX often provides feedback on the input structure, such as when a mandatory parameter is missing or an unexpected value is set. In these cases, ehubX references the file path where the parameter was specified and provides a **node path** to the parameter's location. This might look like the following:

.. code-block:: console
  :caption: Referencing a parameter

  Parsing exception in file /path/to/project/inputs/hubs.yaml: Missing mandatory value detected at node hubs["H1"]/techs["X1"]/tech_params/param_name

The originating file that is referenced in this message had the structure:

.. code-block:: ruby
  :caption: Source file with missing parameter

  hubs:
  - hub_id: H1
    techs:
    - tech_id: X1
    tech_params:
      param_name:  # Missing value

As shown, the node path is a chain of elements of the following two types:

* If the parameter is contained in a dictionary node with a specific name (e.g., :code:`tech_params` above), the node path includes this name followed by a forward slash (e.g., :code:`tech_params/` above).
* If the path to the parameter goes through a specific element of an *identifiable list* (see :ref:`list types<list_types>`, e.g., :code:`hubs` and :code:`techs` above), the name of that identifiable list and the unique identifier of the list element are included in the node path in the same way one would reference a dictionary element in Python (e.g., :code:`hubs["H1"]` and :code:`techs["X1"]` above).

This approach allows every yaml node in an ehubX input document to be referenced in a clear and readable manner.

.. _parameter_types:

Parameter types
----------------

.. code-block:: ruby
    :caption: Parameter types

    empty_param:
    scalar_param: 42 kW
    yeardep_param: [[2020, 0.85 m], [2025, 0.90 m]]
    timeseries_param: link/to/series.csv

* **Empty parameters**: Functions identically to omitting the parameter entirely. If *empty_param* is an optional key, no value will be set and the default value will be used. If it is mandatory, an error will be thrown.
* **Scalar parameters**: A single value that will be applied throughout. If the parameter is considered stage- or time-dependent in the model, this scalar value will be used for all stages and/or time steps. The value can be either a simple number (e.g., :code:`42`) or a number with a unit (e.g., :code:`42 kW`, see :ref:`units <units>`). The correct unit type for each parameter can be found in the :ref:`input files <input_files>` section.
* **Year-dependent parameters**: The value is given as an array of arrays, where each inner array contains two elements: a year and a value (potentially with a unit). This parameterizes a piecewise constant year-to-value function. For each stage in the model, its stage year is used to obtain an interpolated value from this piecewise constant function by selecting the value from the closest year node at or before the stage year. For stage years before the earliest year node, the first node value is assigned. In the above example, all stage years up to 2024 are assigned the value 0.85 m, and all stage years from 2025 onwards are assigned the value 0.90 m.
* **Transient parameters**: If the parameter is *transient* (i.e., time-dependent), it is specified in an external csv file whose path relative to the current yaml file is given as the value. The structure of these csv files depends on the parameter type, but a general overview is provided in the :ref:`csv files <csv_files>` section. Specific details for each transient parameter are given in the corresponding subsection of :ref:`input files <input_files>` where the parameter occurs.


.. _units:

Units
-------

ehubX provides its own unit system to ensure input file consistency and error-free model execution. ehubX parses nearly all value parameters as strings and attempts to interpret them as numbers with units. If a unit is not recognized, an error will be thrown. If no unit is provided, the value will be interpreted as dimensionless. Examples are provided below:

.. code-block:: ruby
  :caption: Units

  42 kW           # 42 kilowatts
  3.6 m           # 3.6 meters
  0.85            # dimensionless value
  1000 kWh        # 1000 kilowatt-hours
  -2.5 m/s        # -2.5 meters per second
  3 1/h           # 3 per hour
  15 kWh/(m^2*h)  # 15 kilowatt-hours per square meter per hour

The last example demonstrates that units can be expressed in more complex forms, such as ratios or rates. If the same unit appears in both the numerator and denominator, it will cancel out. While there are practical limitations to this system, the following overview lists all supported basic units from which compound units can be derived through multiplication, division, or powers:

- **Length**: *m*, *km*, *ft*, or *mi*.
- **Time**: *s*, *min*, *h*, *d*, or *a*.
- **Power**: *W*, *kW*, *MW*, *GW*, or *TW*.
- **Energy**: *kWh*, *MWh*, *GWh*, or *TWh*. These are parsed internally as power multiplied by time. Unfortunately, units such as *J* are not supported by the ehubX unit system.
- **Mass**: *kg*, *t*, *kt*, *Mt*.
- **Currency**: *EUR*, *kEUR*, *MEUR*, *USD*, *kUSD*, *MUSD*, *GBP*, *kGBP*, *MGBP*, *CHF*, *kCHF*, or *MCHF*. Due to varying exchange rates, no actual conversion occurs between different currencies (e.g., EUR and CHF). Instead, ehubX assumes that all monetary values are given in the same currency and will not convert between them. It is the user's responsibility to ensure that currency inputs use consistent units. However, conversions between different scales of the same currency (e.g., kCHF and CHF) are supported.
- **Temperature**: *K*. Due to the non-proportional nature of temperature scales, ehubX does not support temperature units such as *°C* or *°F*. Users are expected to convert these values to Kelvin before passing them to ehubX.
- **Dimensionless**: If no unit is provided, the value is interpreted as dimensionless.

Finally, some parameters in ehubX are specified relative to the concept of a technology's **capacity**. This is an optimization variable that ehubX can select within certain bounds to achieve optimal technology scaling for a model. Since all technologies fall into one of several types (see :ref:`tech model <tech_model>` for more details), the term "capacity" carries different physical interpretations for each technology type and may therefore have different units. The following table provides an overview of capacity units for each technology type:


.. list-table:: Capacity units for technology types
  :header-rows: 1

  * - Tech type
    - Capacity unit
    - Physical interpretation
  * - :ref:`Storage <storage_model>` and :ref:`EBM <ebm_model>`
    - *[ec_unit]*, the stored unit
    - Maximum storable amount
  * - :ref:`Conversion <conversion_model>`
    - *[ec_unit/h]*, where *ec_unit* is the main output unit
    - Maximum output rate of the main output carrier
  * - :ref:`Solar <solar_model>` and :ref:`ATES <ates_model>`
    - *[m^2]*
    - Area covered by installation
  * - :ref:`Heat pump technologies <heatpump_model>`
    - *[kW]*
    - Maximal thermal condenser power.

.. _csv_files:

csv files
----------

.. code-block:: ruby
    :caption: csv file structure

    header_1, I_11, ..., I_1m
       ...    ...         ...
    header_n, I_n1, ..., I_nm
    unit,     u_1,  ..., u_m   # (optional)
    -------------------------
    J_1,      0.3,  ..., 0.8
    ...       ...        ...
    J_r,      0.4,  ..., 0.9

CSV files in ehubX all adhere to the same basic structure depicted above (note that the dashed line is not actually part of the CSV document but serves only to visualize the distinction between the header and body).

* The file begins with *n+1* rows that constitute the *header* of the CSV file. Each of these rows can be considered as one dimension of an n-dimensional index tuple.

  * The keys for these header rows (:code:`header_1`, ..., :code:`header_n`) are collected in the first column and must take specific string values expected by ehubX. These values depend on the specific CSV file but typically include entries like :code:`stage_id`, :code:`hub_id`, :code:`tech_id`, or :code:`ec_id`.
  * For each of the subsequent columns, the header rows contain an index tuple (e.g., (:code:`I_11`, ..., :code:`I_n1`) for the second column). These index tuples must not contain any duplicates.

* Below the header, there is an optional row that contains the *units* (see :ref:`Units <units>`) of the values in the CSV file. This row is not mandatory and can be omitted if all values are unitless. If present, it must contain the same number of columns as the header. Unitless columns can be represented either by an empty unit or the number *1*.

* Following the optional unit row begins the *body* of the CSV file.

  * The first column contains the *indices* of the CSV file.
  * Starting from the second column, the *values* of the CSV file are provided, given in the specified unit.

While this outlines the general structure of an ehubX CSV file, there is a commonly used special case where the CSV file is employed to define time-specific model parameters. Typically, these parameters will have a *default value* specified in a YAML file in the following manner:

.. code-block:: ruby
    :caption: Setting a time-dependent parameter with default value (yaml)

    example_param: 0.5 kW
    profile_path: profiles.csv

The parameter :code:`example_param` has its default value of 0.5 set in a YAML file. This value will be used for all indices not included in the file :code:`profiles.csv`, which may look like this:

.. code-block:: ruby
    :caption: Setting a time-dependent parameter with default value (csv)

    stage_id,    S1
    profile_key, example_param
    unit,        kW
    1,           0.30
    2,           0.35
    3,           0.40

In this way, the parameter values for time steps 1 to 3 and the stage :code:`S1` will be taken from the CSV file. For all other stages, the default value of 0.5 kW set in the YAML file will be applied. This rule of *time-dependent before default* is followed for every input parameter.
