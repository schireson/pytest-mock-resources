#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

import os
import sys

from sphinx_pyproject import SphinxConfig

sys.path.insert(0, os.path.abspath(".."))

config = SphinxConfig("../../pyproject.toml")

project = "Pytest Mock Resources"
release = config.version
version = config.version

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx_autodoc_typehints",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
source_suffix = [".rst", ".md"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_sidebars = {"**": ["globaltoc.html", "relations.html", "sourcelink.html", "searchbox.html"]}

intersphinx_mapping = {"https://docs.python.org/": None}

autoclass_content = "both"
master_doc = "index"
