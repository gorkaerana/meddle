from operator import attrgetter
from pathlib import Path

import pytest

from mdl import Command


path_name = attrgetter("name")
here = Path(__file__).parent
scrapped_mdl_dir = here / "mdl_examples" / "scrapped"
mdl_files = sorted(
    scrapped_mdl_dir.rglob("*.mdl"),
    key=path_name,
)


@pytest.mark.parametrize("path", mdl_files, ids=path_name)
def test_loading(path, benchmark):
    benchmark(Command.loads, path.read_text())
    assert True


@pytest.mark.parametrize("path", mdl_files, ids=path_name)
def test_validating(path, benchmark):
    command = benchmark(Command.loads, path.read_text())
    assert command.validate()
