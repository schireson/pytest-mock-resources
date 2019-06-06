# -*- coding: utf-8 -*-
#
# Configuration file for the Sphinx documentation builder.
#
# This file does only contain a selection of the most common options. For a
# full list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = 'Schireson Pytest Mock Resources'
copyright = '2019, Schireson'
author = 'Omar Khan'

# The short X.Y version
version = '0.1'
# The full version, including alpha/beta/rc tags
release = '0.1.46'


# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.ifconfig',
    'm2r'
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The parser(s) of non-RST files
# source_parsers = {
#     '.md': CommonMarkParser,
# }

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = ['.rst', '.md']

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = None


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'classic'
html_theme_options = {
    "stickysidebar": True,
    "externalrefs": True,
    "codebgcolor": "rgb(242, 247, 255)",
    "footerbgcolor": "rgb(33, 105, 165)",  # (CSS color): Background color for the footer line.
    "headbgcolor": "rgb(238, 238, 238)",  # (CSS color): Background color for headings.
    "headlinkcolor": "rgb(40, 40, 40)",  # (CSS color): Link color for headings.
    "headtextcolor": "rgb(40, 40, 40)",  # (CSS color): Text color for headings.
    "relbarbgcolor": "rgb(33, 105, 165)",  # (CSS color): Background color for the relation bar.
    "sidebarbgcolor": "rgb(228, 228, 228)",  # (CSS color): Background color for the sidebar.
    "sidebarbtncolor": "rgb(40, 40, 40)",  # (CSS color): Background color for the sidebar collapse button (used when collapsiblesidebar is True).
    "sidebarlinkcolor": "rgb(40, 40, 40)",  # (CSS color): Link color for the sidebar.
    "sidebartextcolor": "rgb(40, 40, 40)",  # (CSS color): Text color for the sidebar.
    # "bgcolor": "",  # (CSS color): Body background color.
    # "bodyfont": "",  # (CSS font-family): Font for normal text.
    # "codetextcolor": "",  # (CSS color): Default text color for code blocks, if not set differently by the highlighting style.
    # "footertextcolor": "",  # (CSS color): Text color for the footer line.
    # "headfont": "",  # (CSS font-family): Font for headings.
    # "linkcolor": "",  # (CSS color): Body link color.
    # "relbarlinkcolor": "",  # (CSS color): Link color for the relation bar.
    # "relbartextcolor": "",  # (CSS color): Text color for the relation bar.
    # "textcolor": "",  # (CSS color): Body text color.
    # "visitedlinkcolor": "",  # (CSS color): Body color for visited links.
}

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# The default sidebars (for documents that don't match any pattern) are
# defined by theme itself.  Builtin themes are using these templates by
# default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
# 'searchbox.html']``.
#
# html_sidebars = {}


# -- Options for HTMLHelp output ---------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'Schireson-Pytest-Mock-Resourcesdoc'


# -- Options for LaTeX output ------------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'SchiresonPytestMockResources.tex', 'Schireson Pytest Mock Resources Documentation',
     'Schireson', 'manual'),
]


# -- Options for manual page output ------------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'schiresonpytestmockresources', 'Schireson Pytest Mock Resources Documentation',
     [author], 1)
]


# -- Options for Texinfo output ----------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'SchiresonPytestMockResources', 'Schireson Pytest Mock Resources Documentation',
     author, 'SchiresonPytestMockResources', 'One line description of project.',
     'Miscellaneous'),
]


# -- Options for Epub output -------------------------------------------------

# Bibliographic Dublin Core info.
epub_title = project

# The unique identifier of the text. This can be a ISBN number
# or the project homepage.
#
# epub_identifier = ''

# A unique identification for the text.
#
# epub_uid = ''

# A list of files that should not be packed into the epub file.
epub_exclude_files = ['search.html']


# -- Extension configuration -------------------------------------------------

# -- Options for intersphinx extension ---------------------------------------

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {'https://docs.python.org/': None}
