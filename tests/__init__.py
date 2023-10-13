"""
run all: python -m pytest -sv --cov-report term-missing --cov=element_calcium_imaging --sw -p no:warnings tests/
run one: python -m pytest -sv --cov-report term-missing --cov=element_calcium_imaging --sw -p no:warnings --pdb tests/module_name.py -k function_name
"""

import os
import pathlib
import sys
from contextlib import nullcontext

import datajoint as dj
import numpy as np
import pandas as pd
import pytest
from element_interface.utils import find_full_path, find_root_directory

# ------------------- SOME CONSTANTS -------------------

_tear_down = False

sessions_dirs = [
    "subject1/session1",
]

verbose = False

logger = dj.logger

# ------------------ GENERAL FUCNTION ------------------


class QuietStdOut:
    """If verbose set to false, used to quiet tear_down table.delete prints"""

    def __enter__(self):
        logger.setLevel("ERROR")
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, "w")

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.setLevel("INFO")
        sys.stdout.close()
        sys.stdout = self._original_stdout


verbose_context = nullcontext() if verbose else QuietStdOut()

# ------------------- FIXTURES -------------------


@pytest.fixture
def pipeline():
    with verbose_context:
        print("\n")
        from notebooks import tutorial_pipeline

    yield {
        "subject": tutorial_pipeline.subject,
        "lab": tutorial_pipeline.lab,
        "imaging": tutorial_pipeline.imaging,
        "scan": tutorial_pipeline.scan,
        "session": tutorial_pipeline.session,
        "Equipment": tutorial_pipeline.Equipment,
        "get_imaging_root_data_dir": tutorial_pipeline.get_imaging_root_data_dir,
    }

    if _tear_down:
        with verbose_context:
            pipeline.subject.Subject.delete()


@pytest.fixture(autouse=True)
def test_data(pipeline):
    root_dirs = pipeline["get_imaging_root_data_dir"]
    try:
        _ = [find_full_path(root_dirs(), p) for p in sessions_dirs]
    except FileNotFoundError as e:
        print(e)
