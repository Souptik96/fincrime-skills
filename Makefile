PYTHON ?= python
VENV := .venv
VENV_PY := $(VENV)/Scripts/python
CORE := packages/fincrime-core
CLI := packages/fincrime-cli
TESTS := $(CORE)/tests
CLI_TESTS := $(CLI)/tests

.DEFAULT_GOAL := help
.PHONY: help dev test test-cli lint lint-network lint-schema validate eval validate-skills validate-promotion cases cases-check ci clean install

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

dev: install  ## Create the venv and install the core and the CLI in editable mode
	$(VENV_PY) -m pip install --quiet --upgrade pip
	$(VENV_PY) -m pip install --quiet -e "$(CORE)[dev]" -e "$(CLI)[dev]"

install:  ## Create the venv if it does not exist
	@if not exist "$(VENV_PY)" ( \
		$(PYTHON) -m venv "$(VENV)" \
	)
	@if not exist "$(VENV_PY)" ( \
		echo "Could not create the venv. Create it manually and re-run 'make dev'." && exit 1 \
	)

test:  ## Run the core test suite
	$(VENV_PY) -m pytest $(TESTS) -q

test-cli:  ## Run the CLI test suite
	$(VENV_PY) -m pytest $(CLI_TESTS) -q

lint:  ## Enforce the zero-dependency invariant (ADR-0002)
	$(VENV_PY) scripts/check_imports.py

lint-network:  ## Run the suite with sockets disabled (air-gap safety)
	$(VENV_PY) scripts/check_no_network.py -- $(TESTS) -q
	$(VENV_PY) scripts/check_no_network.py -- $(CLI_TESTS) -q

lint-schema:  ## Cross-check our schema validator against the reference implementation
	$(VENV_PY) scripts/check_schema_parity.py

validate:  ## Validate the canonical contracts
	$(VENV_PY) -m json.tool contracts/finding.schema.json > NUL
	$(VENV_PY) -c "import json,pathlib; [json.loads(p.read_text(encoding='utf-8')) for p in pathlib.Path('contracts').glob('*.json')]; print('contracts OK')"

validate-skills:  ## Validate every skill package, case suite and golden artifact
	$(VENV_PY) -m fincrime_cli.main validate skills/investigation-qa
	$(VENV_PY) -m fincrime_cli.main validate skills/alert-triage
	$(VENV_PY) -m fincrime_cli.main validate skills/case-summarize
	$(VENV_PY) -m fincrime_cli.main validate skills/evidence-request
	$(VENV_PY) -m fincrime_cli.main validate skills/alert-triage/evals/suites/alert-triage
	$(VENV_PY) -m fincrime_cli.main validate skills/case-summarize/evals/suites/case-summarize
	$(VENV_PY) -m fincrime_cli.main validate skills/evidence-request/evals/suites/evidence-request
	$(VENV_PY) -m fincrime_cli.main validate skills/alert-triage/examples/golden_triage_report.json --evidence-set skills/alert-triage/examples/golden_evidence_set.json --knowledge-pack knowledge/packs/core-2026-10
	$(VENV_PY) -m fincrime_cli.main validate skills/case-summarize/examples/golden_case_summary.json --evidence-set skills/case-summarize/examples/golden_evidence_set.json --knowledge-pack knowledge/packs/core-2026-10
	$(VENV_PY) -m fincrime_cli.main validate skills/evidence-request/examples/golden_request_dossier.json --evidence-set skills/evidence-request/examples/golden_evidence_set.json --knowledge-pack knowledge/packs/core-2026-10
	$(VENV_PY) -m fincrime_cli.main knowledge validate --pack knowledge/examples/sample-pack
	$(VENV_PY) -m fincrime_cli.main knowledge validate --pack knowledge/packs/core-2026-10

validate-promotion:  ## Apply the promotion gate (ADR-0006): stale knowledge blocks
	$(VENV_PY) -m fincrime_cli.main validate skills/investigation-qa --promotion
	$(VENV_PY) -m fincrime_cli.main validate skills/alert-triage --promotion
	$(VENV_PY) -m fincrime_cli.main validate skills/case-summarize --promotion
	$(VENV_PY) -m fincrime_cli.main validate skills/evidence-request --promotion
	$(VENV_PY) -m fincrime_cli.main knowledge validate --pack knowledge/packs/core-2026-10 --promotion

# Regenerate the Phase 3 case suites. The script is the source of truth for
# the case population and it is deterministic: two runs write byte-identical
# files. It checks the suite mix before it writes anything.
cases:
	$(VENV_PY) scripts/generate_phase3_cases.py

cases-check:
	$(VENV_PY) scripts/generate_phase3_cases.py

eval:  ## Run the evaluation suites (Phase 4)
	@echo "The case suites have shipped (Phase 3); the harness that runs them is Phase 4."

ci: lint validate test test-cli lint-network lint-schema validate-skills  ## Run everything CI runs
	@echo "CI checks passed."

clean:  ## Remove build and cache artifacts
	rmdir /s /q $(VENV) 2>nul || true
	rmdir /s /q .pytest_cache 2>nul || true
	rmdir /s /q **/__pycache__ 2>nul || true
