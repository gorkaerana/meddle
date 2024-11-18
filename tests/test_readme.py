from pathlib import Path
import subprocess

from markdown_it import MarkdownIt
import pytest


@pytest.fixture
def readme_path(project_root_dir) -> Path:
    return project_root_dir / "README.md"


@pytest.fixture
def readme_contents(readme_path) -> Path:
    return readme_path.read_text()


@pytest.fixture
def readme_python_code(readme_contents):
    return "\n".join(
        token.content
        for token in MarkdownIt().parse(readme_contents)
        if (
            (token.type == "fence")
            and (token.tag == "code")
            and (token.info == "python")
        )
    )


@pytest.fixture
def readme_executable_file(readme_python_code, tmp_path):
    readme_py_path = tmp_path / "readme.py"
    readme_py_path.write_text(readme_python_code)
    return readme_py_path


@pytest.fixture
def python_executable(project_root_dir):
    return project_root_dir / ".venv" / "bin" / "python3"


def test_readme_python_code_chunks(python_executable, readme_executable_file):
    process = subprocess.run(
        [python_executable, readme_executable_file], capture_output=True
    )
    assert process.returncode == 0
