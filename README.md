# ehubX

ehubX is a Python platform for optimization-based energy system models. Its input structure is based on YAML and CSV files which are translated into a Mixed-Integer Linear Programming (MILP) model that is solved using external optimization solvers. ehubX capabilities include a multitude of modules such as:

* Imports, exports, demands, load shedding, load shifting
* Storage, conversion, solar, wind and electromobility technologies
* Network transfer
* Multi-stage, multi-hub and multi-objective models

## Installation

Use a clean and fresh virtual Python environment in which you should also install poetry. Then, simply navigating to the cloned repository and running "poetry install" inside that repository is all that is required.

## Examples

The examples directory contains demo projects that give an impression on how to work with ehubX models. The most academic example and a good place to start is the *toy_model*.

## Project Info
- Main contact: [Dennis Beermann](dennis.beermann@empa.ch)
- Developers: Dennis Beermann, Léonie Fierz (former)
- Programming Language and Version: Python 3.11
- Contributors: Robin Mutschler, Binod Koirala, ...
- Third-party dependencies: Mainly [Pyomo](http://www.pyomo.org/) and a third-party optimization solver (e.g.; [Gurobi](https://www.gurobi.com/), [GLPK](https://www.gnu.org/software/glpk/)). For a full list, see pyproject.toml

## Project Status
In development (see also CHANGELOG.rst)
