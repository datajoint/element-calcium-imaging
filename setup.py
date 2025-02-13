#!/usr/bin/env python
from os import path
from setuptools import find_packages, setup
import urllib.request

pkg_name = "element_calcium_imaging"
here = path.abspath(path.dirname(__file__))

with open(path.join(here, "README.md"), "r") as f:
    long_description = f.read()


with open(path.join(here, pkg_name, "version.py")) as f:
    exec(f.read())

# TODO: Replace with `tomllib` once Python 3.10 support is dropped
def fetch_and_parse_dependencies(url):
    # Fetch the pyproject.toml file
    with urllib.request.urlopen(url) as f:
        toml_content = f.read().decode("UTF-8")

    # Manually parse the dependencies section
    lines = toml_content.split('\n')
    dependencies = []
    start_collecting = False

    for line in lines:
        line = line.strip()
        if line.startswith('dependencies = ['):
            start_collecting = True
            continue
        if start_collecting:
            if line.startswith(']'):
                break
            dependency = line.strip(',').strip('"')
            dependencies.append(dependency)

    return dependencies

# URL of CaImAn's pyproject.toml file
caiman_url = "https://raw.githubusercontent.com/flatironinstitute/CaImAn/main/pyproject.toml"

# Fetch and parse dependencies
caiman_requirements = fetch_and_parse_dependencies(caiman_url )



setup(
    name=pkg_name.replace("_", "-"),
    version=__version__,  # noqa: F821
    description="Calcium Imaging DataJoint Element",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="DataJoint",
    author_email="info@datajoint.com",
    license="MIT",
    url=f'https://github.com/datajoint/{pkg_name.replace("_", "-")}',
    keywords="neuroscience calcium-imaging science datajoint",
    packages=find_packages(exclude=["contrib", "docs", "tests*"]),
    scripts=[],
    install_requires=[
        "datajoint>=0.14.0",
        "ipykernel>=6.0.1",
        "ipywidgets",
        "plotly",
        "dash-extensions",
        "scikit-image",
        "element-interface @ git+https://github.com/datajoint/element-interface.git",
    ],
    extras_require={
        "caiman_requirements": [caiman_requirements],
        "caiman": ["caiman @ git+https://github.com/datajoint/CaImAn.git"],
        "elements": [
            "element-animal @ git+https://github.com/datajoint/element-animal.git",
            "element-event @ git+https://github.com/datajoint/element-event.git",
            "element-lab @ git+https://github.com/datajoint/element-lab.git",
            "element-session @ git+https://github.com/datajoint/element-session.git",
        ],
        "extract": ["matlabengine", "scipy"],
        "nd2": ["nd2"],
        "sbxreader": ["sbxreader @ git+https://github.com/jcouto/sbxreader.git"],
        "scanreader": ["scanreader @ git+https://github.com/atlab/scanreader.git"],
        "suite2p": ["suite2p[io]>=0.12.1"],
        "tests": ["pytest", "pytest-cov", "shutils"],
    },
)
