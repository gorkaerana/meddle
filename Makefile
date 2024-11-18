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
