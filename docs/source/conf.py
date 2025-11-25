# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
from typing import List


project = "ehubX"
copyright = "Copyright 2024, Urban Energy Systems Lab, Empa"
author = "Urban Energy Systems Lab, Empa"
release = "2.2.3"

# -- General configuration ---------------------------------------------------


# extensions = ['sphinx.ext.autosectionlabel', 'sphinx.ext.autodoc']
extensions = ["sphinx.ext.autodoc", "sphinx.ext.mathjax"]

templates_path = ["_templates"]
exclude_patterns: List[str] = []


# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# -- Options for PDF output --------------------------------------------------
latex_engine = "xelatex"
latex_documents = [
    (
        "index",
        "ehubX.tex",
        "ehubX Documentation",
        "Urban Energy Systems Lab, Empa",
        "manual",
    ),
]
latex_elements = {
    "preamble": r"""
\usepackage{pdflscape}
\usepackage{adjustbox}
""",
}
