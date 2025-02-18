# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ehubX'
copyright = 'Copyright 2024, Urban Energy Systems Lab, Empa'
author = 'Dennis Beermann'
release = '2.1'

# -- General configuration ---------------------------------------------------


# extensions = ['sphinx.ext.autosectionlabel', 'sphinx.ext.autodoc']
extensions = ['sphinx.ext.autodoc']

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
