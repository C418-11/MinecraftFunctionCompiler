# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Minecraft Function Compiler'
copyright = '2024, C418____11'
author = 'C418____11'
release = 'Debug'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc']

templates_path = ['_templates']
exclude_patterns = []

language = 'zh_CN'

python_display_short_literal_types = True
add_module_names = False

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']
html_short_title = "MCFC"
html_favicon = "./_static/favicon.png"

# -- AutoAPI Configuration ---------------------------------------------------
extensions.append('autoapi.extension')

autoapi_dirs = ["../"]
autoapi_ignore = ["*/tests/*", "*/build/*", "*/.venv*", "*/.git/*", "*/docs/*", "*/.output/*"]
autoapi_options = [
    "members",
    "inherited-members",
    "undoc-members",
    "private-members",
    "special-members",
    "show-inheritance",
    "show-module-summary",
    "imported-members",
]
