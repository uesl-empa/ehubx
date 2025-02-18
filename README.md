# ehubX

ehubX is a Python platform for optimization-based energy system models. Its input structure is based on YAML and CSV files which are translated into a Mixed-Integer Linear Programming (MILP) model that is solved using external optimization solvers. ehubX capabilities include a multitude of modules such as:

* Imports, exports, demands, load shedding, load shifting
* Storage, conversion, solar, wind and electromobility technologies
* Network transfer
* Multi-stage, multi-hub and multi-objective models

## Installation

ehubX installation is managed through [Poetry](https://python-poetry.org/). Inside the ehubX repository directory, running `poetry install` installs ehubX and all its dependencies. Additionally, ehubX requires an optimization solver: [GLPK](https://www.gnu.org/software/glpk/) can be installed e.g.; using Anaconda with `conda install -c conda-forge glpk`. Alternatively, [Gurobi](https://www.gurobi.com/) can be used.

## Documentation

Documentation is currently available locally. Run

    sphinx-build -M html docs/source docs/build

in a terminal and the documentation will be available under docs/build/html

## Examples

The examples directory contains demo projects that give an impression on how to work with ehubX models.

## Project Info
- Main contact: [Dennis Beermann](dennis.beermann@empa.ch)
- Developers: Dennis Beermann, Léonie Fierz (former)
- Programming Language and Version: Python 3.11
- Contributors: Robin Mutschler, Binod Koirala, ...
- Third-party dependencies: Mainly [Pyomo](http://www.pyomo.org/) and a third-party optimization solver (e.g.; [Gurobi](https://www.gurobi.com/), [GLPK](https://www.gnu.org/software/glpk/)). For a full list, see pyproject.toml

## Project Status
In development (see also CHANGELOG.rst)
