"""Sphinx configuration."""
project = "f451 Sensors"
author = "Martin Lanser"
copyright = "2022, Martin Lanser"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
