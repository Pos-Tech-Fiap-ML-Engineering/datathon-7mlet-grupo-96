VENV := .venv

.PHONY: setup lint test serve

setup:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -e ".[dev]"

lint:
	$(VENV)/bin/ruff check src tests

test:
	$(VENV)/bin/pytest -q

serve:
	$(VENV)/bin/uvicorn bandit_platform.service.app:app --reload --port 8000
