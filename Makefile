mypy:
	mypy .

pyright:
	pyright .

type_check: mypy pyright

format:
	ruff format

lint:
	ruff check

# qc = quality control
qc: format lint type_check

install_dev:
	uv sync

test:
	pytest tests/test_mdl_grammar.py tests/test_parser.py tests/test_readme.py --workers auto

benchmark:
	pytest tests/test_benchmark.py
