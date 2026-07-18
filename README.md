# ehubX

[![CI](https://github.com/uesl-empa/ehubx/actions/workflows/ci.yml/badge.svg)](https://github.com/uesl-empa/ehubx/actions/workflows/ci.yml)
[![Documentation Status](https://readthedocs.org/projects/ehubx/badge/?version=latest)](https://ehubx.readthedocs.io/)
![License](https://img.shields.io/badge/license-GPLv3-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)

ehubX is a Python framework for optimization-based energy system modeling developed by the [Urban Energy Systems Laboratory at Empa](https://www.empa.ch/web/s313). It has been applied in numerous large-scale energy system analyses for both scientific research and municipal planning projects.

Energy system models are defined through a combination of YAML configuration files and CSV input data. ehubX translates these inputs into Mixed-Integer Linear Programming (MILP) models that can be solved using a variety of external optimization solvers.

Its modular architecture supports a wide range of modeling capabilities, including:

- Energy imports, exports, demands, load shedding, and load shifting
- Storage, conversion, solar, wind, and electromobility technologies
- Energy network modeling and transfer
- Multi-stage, multi-hub, and multi-objective optimization
- Single- and multi-objective optimization with objectives such as costs, emissions, and self-sufficiency

## Installation

ehubX can be installed either via a PyPI pipeline, or for local development.

### PyPI installation

ehubX is available on [PyPI](https://pypi.org/project/ehubx/) and can simply be installed via the command

```
pip install ehubx
pip install ehubx==2.3.0  # Install a specific version
```

### Local development installation

For local development, we recommend setting up **ehubX** in a dedicated Python virtual environment to avoid conflicts with other packages. The step-by-step guide below is formulated using [conda](https://docs.conda.io/en/latest/) but can be adapted for other package managers or a manual setup. Similarly, we use [poetry](https://python-poetry.org/) for dependency management, which can be replaced with [pip](https://pip.pypa.io/en/stable/) if preferred.

Since ehubX relies on external MILP solvers, additionally ensure that you have a compatible solver installed and properly configured in your environment (see *Specify solver* in the documentation).

### Development installation

1. **Clone the ehubX repository.**

2. **Create a new virtual environment:**

   ```
   conda create -n ehubx python=PYTHON_VERSION
   ```

Make sure that the ``PYTHON_VERSION`` you choose is a compatible with the current version of ehubX (see *pyproject.toml* in the root directory).

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

The complete documentation is available at:

**https://ehubx.readthedocs.io/**

## Examples

The ``examples`` directory contains demo projects that give an impression on how to work with ehubX models. The most academic example and a good place to start is the *small_demo*.

## How to cite

TODO

## License 

Copyright (C) 2026 Urban Energy Systems Laboratory, Empa.

This project is licensed under the GNU General Public License v3.0 or later.
See the ``LICENSE`` file for details.