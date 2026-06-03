PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip
STREAMLIT ?= .venv/bin/streamlit

.PHONY: install test smoke lint format run clean reindex

install:
	python3 -m venv .venv
	$(PIP) install -r requirements.txt

test:
	$(PYTHON) -m pytest -q

smoke:
	$(PYTHON) -m pytest tests/test_app_smoke.py -q

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

run:
	$(STREAMLIT) run app.py

reindex:
	$(PYTHON) scripts/reindex_memory.py

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
