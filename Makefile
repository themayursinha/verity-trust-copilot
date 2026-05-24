VENV ?= .venv
PYTHON ?= $(VENV)/bin/python
RUFF ?= $(VENV)/bin/ruff
MYPY ?= $(VENV)/bin/mypy

.PHONY: test test-python test-js lint format-check typecheck check

test: test-python test-js

test-python:
	$(PYTHON) -m unittest discover -s tests

test-js:
	node --test static/evidence_quality.test.mjs

lint:
	$(RUFF) check .

format-check:
	$(RUFF) format --check .

typecheck:
	$(MYPY) security_questionnaire_copilot.py web_app.py

check: lint format-check typecheck test
