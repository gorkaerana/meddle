from pathlib import Path

import pytest


@pytest.fixture
def root_test_dir():
    return Path(__file__).parent


@pytest.fixture
def mdl_examples_dir(root_test_dir):
    return root_test_dir / "mdl_examples"
