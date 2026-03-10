# ehubX

ehubX is a Python platform for optimization-based energy system models. Its input structure is based on YAML and CSV files which are translated into a Mixed-Integer Linear Programming (MILP) model that is solved using external optimization solvers. ehubX capabilities include a multitude of modules such as:

* Imports, exports, demands, load shedding, load shifting
* Storage, conversion, solar, wind and electromobility technologies
* Network transfer
* Multi-stage, multi-hub and multi-objective models

## Installation

We recommend setting up **ehubX** in a dedicated Python virtual environment to avoid conflicts with other packages. The step-by-step guide below is formulated using [conda](https://docs.conda.io/en/latest/) but can be adapted for other package managers or a manual setup. Similarly, we use [poetry](https://python-poetry.org/) for dependency management, which can be replaced with [pip](https://pip.pypa.io/en/stable/) if preferred.

Since ehubX relies on external MILP solvers, additionally ensure that you have a compatible solver installed and properly configured in your environment (see *Specify solver* in the documentation).

### Steps

1. **Clone the ehubX repository.**

2. **Create a new virtual environment:**

   ```
   conda create -n ehubx python=PYTHON_VERSION
   ```

Make sure that the ``PYTHON_VERSION`` you choose is compatible with the current version of ehubX (see *pyproject.toml* in the root directory).

3. **Activate the environment:**

    ```
    conda activate ehubx
    ```

4. **Install [poetry](https://python-poetry.org/) for dependency management**:

    ```
    conda install -c conda-forge poetry
    ```

5. Navigate to the cloned ehubX directory and install using poetry:

    ```
    cd PATH_TO_EHUBX_REPO
    poetry install
    ```

6. Run any of the main scripts in the examples folder to verify the installation.

## Documentation

Documentation is currently available locally. Run

    sphinx-build -M html docs/source docs/build

in a terminal and the documentation will be available under docs/build/html

## Examples

The examples directory contains demo projects that give an impression on how to work with ehubX models. The most academic example and a good place to start is the *toy_model*.

## Project Info
- Main contact: [Dennis Beermann](dennis.beermann@empa.ch)
- Developers: Dennis Beermann, Léonie Fierz (former)
- Programming Language: Python
- Contributors: Robin Mutschler, Binod Koirala, ...
- Third-party dependencies: Mainly [Pyomo](http://www.pyomo.org/) and a third-party optimization solver (e.g.; [Gurobi](https://www.gurobi.com/), [GLPK](https://www.gnu.org/software/glpk/)). For a full list, see pyproject.toml

## Project Status
In development (see also CHANGELOG.rst)
