.. _installation:

Installation
==============

We recommend setting up **ehubX** in a dedicated Python virtual environment to avoid conflicts with other packages. The step-by-step guide below is formulated using `conda <https://docs.conda.io/en/latest/>`_ but can be adapted for other package managers or manual setup. Similarly, we use `poetry <https://python-poetry.org/>`_ for dependency management, which can be replaced with `pip <https://pip.pypa.io/en/stable/>`_ if preferred. Since ehubX relies on external MILP solvers, additionally ensure that you have a compatible solver installed and properly configured in your environment (see :ref:`Specify solver <specify_solver>`).

1. Clone the ehubX repository.

2. Create a new virtual environment:

    .. code-block:: bash

        conda create -n ehubx python=PYTHON_VERSION

    Make sure that the `PYTHON_VERSION` you choose is compatible with the current version of ehubX (see pyproject.toml).

3. Activate the environment:

    .. code-block:: bash

        conda activate ehubx

4. Install `poetry <https://python-poetry.org/>`_ for dependency management:

    .. code-block:: bash

        conda install -c conda-forge poetry

5. Navigate to the cloned ehubX directory and install using poetry:

    .. code-block:: bash

        cd PATH_TO_EHUBX_REPO
        poetry install

6. Run any of the main scripts in the examples folder to verify the installation.
