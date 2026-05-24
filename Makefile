PYTHON ?= python3

.PHONY: test test-python test-js lint format-check typecheck check

test: test-python test-js

test-python:
	$(PYTHON) -m unittest discover -s tests

test-js:
	node --test static/evidence_quality.test.mjs

lint:
	ruff check .

format-check:
	ruff format --check .

typecheck:
	mypy security_questionnaire_copilot.py web_app.py

check: lint format-check typecheck test
