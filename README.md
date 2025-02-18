# ehubX

ehubX is a Python platform for optimization-based energy system models. Its input structure is based on YAML and CSV files which are translated into a Mixed-Integer Linear Programming (MILP) model that is solved using external optimization solvers. ehubX capabilities include a multitude of modules such as:

* Imports, exports, demands, load shedding, load shifting
* Storage, conversion, solar, wind and electromobility technologies
* Network transfer
* Multi-stage, multi-hub and multi-objective models

## Installation

### Installation (local)

Installation instructions are available as a video [here](https://empach.sharepoint.com/:v:/s/external-project_EXTEhubDevelopment/EVAizIAJ7KdAoS2KFGS_l6oBMQ6tDdA6JPNV5J_Tb7olwA?e=8anU48) (TODO: access currently Empa-internal)

## Installation (devcontainer)

Installation instructions are available as a video [here](https://empach.sharepoint.com/:v:/s/external-project_EXTEhubDevelopment/ETZmXKry2k9DrbPzJ-SGD1EBNIZGGlBNKQPGqyqAcqzHQw?nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJTdHJlYW1XZWJBcHAiLCJyZWZlcnJhbFZpZXciOiJTaGFyZURpYWxvZy1MaW5rIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXcifX0%3D&e=VrHD8O) (TODO: access currently Empa-internal)

## Documentation

Documentation is currently available locally. Run

    sphinx-build -M html docs/source docs/build

in a terminal and the documentation will be available under docs/build/html

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
