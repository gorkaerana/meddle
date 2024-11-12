from operator import attrgetter
from pathlib import Path

import pytest

from mdl import Command


path_name = attrgetter("name")
# "ADD" and "MODIFY" commands are only allowed as subcommands under
# "ALTER" MDL command
mdl_files = sorted(
    (
        p
        for p in Path(__file__).parent.rglob("*.mdl")
        if p.name not in {"add.mdl", "modify.mdl"}
    ),
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
