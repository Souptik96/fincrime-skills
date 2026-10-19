PYTHON ?= python
VENV := .venv
VENV_PY := $(VENV)/Scripts/python
CORE := packages/fincrime-core
TESTS := $(CORE)/tests

.DEFAULT_GOAL := help
.PHONY: help dev test lint validate eval ci clean install

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

dev: install  ## Create the venv and install the core in editable mode
	$(VENV_PY) -m pip install --quiet --upgrade pip
	$(VENV_PY) -m pip install --quiet -e "$(CORE)[dev]"

install:  ## Create the venv if it does not exist
	@if not exist "$(VENV_PY)" ( \
		$(PYTHON) -m venv "$(VENV)" \
	)
	@if not exist "$(VENV_PY)" ( \
		echo "Could not create the venv. Create it manually and re-run 'make dev'." && exit 1 \
	)

test:  ## Run the test suite
	$(VENV_PY) -m pytest $(TESTS) -q

lint:  ## Enforce the zero-dependency invariant (ADR-0002)
	$(VENV_PY) scripts/check_imports.py

lint-network:  ## Run the suite with sockets disabled (air-gap safety)
	$(VENV_PY) scripts/check_no_network.py -- $(TESTS) -q

lint-schema:  ## Cross-check our schema validator against the reference implementation
	$(VENV_PY) scripts/check_schema_parity.py

validate:  ## Validate the canonical contracts
	$(VENV_PY) -m json.tool contracts/finding.schema.json > NUL
	$(VENV_PY) -c "import json,pathlib; [json.loads(p.read_text(encoding='utf-8')) for p in pathlib.Path('contracts').glob('*.json')]; print('contracts OK')"

eval:  ## Run the evaluation suites (Phase 2+)
	@echo "No evaluation suites have shipped yet (Phase 4)."

ci: lint validate test lint-network lint-schema  ## Run everything CI runs
	@echo "CI checks passed."

clean:  ## Remove build and cache artifacts
	rmdir /s /q $(VENV) 2>nul || true
	rmdir /s /q .pytest_cache 2>nul || true
	rmdir /s /q **/__pycache__ 2>nul || true
