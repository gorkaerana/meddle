from pathlib import Path

import pytest

from mdl import Command


@pytest.mark.parametrize(
    "path",
    sorted(Path(__file__).parent.rglob("*.mdl"), key=lambda p: p.name)
)
def test_something(path, benchmark):
    command = benchmark(Command.loads, path.read_text())
    assert command.validate()
