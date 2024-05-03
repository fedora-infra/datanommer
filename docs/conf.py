# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#

import importlib.metadata
import os
import sys


SUBMODULES = ("models", "commands")

topdir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))

for submodule in SUBMODULES:
    sys.path.insert(0, os.path.join(topdir, f"datanommer.{submodule}"))


# -- Project information -----------------------------------------------------

project = "Datanommer"
copyright = "2013, Contributors to the Fedora Project"
author = "Fedora Infrastructure"

# The full version, including alpha/beta/rc tags
release = importlib.metadata.version("datanommer.models")

# The short X.Y version
version = ".".join(release.split(".")[:2])


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.extlinks",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "myst_parser",
    "sphinx_click",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Explcitely set the master doc
# https://github.com/readthedocs/readthedocs.org/issues/2569
master_doc = "index"


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "alabaster"


# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {
    "github_user": "fedora-infra",
    "github_repo": "datanommer",
    "page_width": "1040px",
    "show_related": True,
    "sidebar_collapse": True,
    "caption_font_size": "140%",
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]


# -- Extension configuration -------------------------------------------------

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

myst_enable_extensions = [
    "colon_fence",
]
myst_heading_anchors = 3


# -- Options for intersphinx extension ---------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}


# -- Misc -----


def run_apidoc(_):
    from sphinx.ext import apidoc

    for submodule in SUBMODULES:
        print(
            " ".join(
                [
                    "sphinx-apidoc",
                    "-f",
                    "-o",
                    os.path.join(topdir, "docs", "_source", submodule),
                    "-T",
                    "-e",
                    "-M",
                    "--implicit-namespaces",
                    os.path.join(topdir, f"datanommer.{submodule}", "datanommer"),
                    # exclude patterns:
                    os.path.join(topdir, f"datanommer.{submodule}", "tests"),
                    os.path.join(
                        topdir, f"datanommer.{submodule}", "datanommer", submodule, "alembic"
                    ),
                ]
            )
        )
        apidoc.main(
            [
                "-f",
                "-o",
                os.path.join(topdir, "docs", "_source", submodule),
                "-T",
                "-e",
                "-M",
                "--implicit-namespaces",
                os.path.join(topdir, f"datanommer.{submodule}", "datanommer"),
                # exclude patterns:
                os.path.join(topdir, f"datanommer.{submodule}", "tests"),
                os.path.join(topdir, f"datanommer.{submodule}", "datanommer", submodule, "alembic"),
            ]
        )
        # This file is going to cause duplicate references
        os.remove(os.path.join(topdir, "docs", "_source", submodule, "datanommer.rst"))
        generate_click_commands(
            os.path.join(topdir, "docs", "_source", "commands.rst"),
            "datanommer.commands",
            nested="full",
        )


def setup(app):
    app.connect("builder-inited", run_apidoc)


def generate_click_commands(output, module, *, with_header=True, nested=None):
    commands = []
    for ep in importlib.metadata.entry_points(group="console_scripts"):
        ep_module = ep.value.partition(":")[0]
        if not ep_module.startswith(f"{module}.") and ep_module != module:
            continue
        commands.append((ep.name, ep.value))
    if not commands:
        return
    with open(output, "w") as fh:
        if with_header:
            fh.write("Commands\n")
            fh.write("========\n")
            fh.write("\n")
        for name, module in commands:
            fh.write(f".. click:: {module}\n")
            fh.write(f"   :prog: {name}\n")
            if nested:
                fh.write(f"   :nested: {nested}\n")
            fh.write("\n")
