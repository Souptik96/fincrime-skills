PYTHON ?= python
VENV := .venv
VENV_PY := $(VENV)/Scripts/python
CORE := packages/fincrime-core
CLI := packages/fincrime-cli
TESTS := $(CORE)/tests
CLI_TESTS := $(CLI)/tests

.DEFAULT_GOAL := help
.PHONY: help dev test test-cli lint lint-pii lint-network lint-schema lint-docs validate eval validate-skills validate-promotion cases cases-check ci clean install demo

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

demo:  ## 30-second onboarding demo: Finding Contract vs unconstrained LLMs
	$(VENV_PY) -m fincrime_cli.main demo
	@echo "--- [1/3] Live Schema & Policy Validation ---"
	$(VENV_PY) -m fincrime_cli.main validate skills/alert-triage/examples/golden_triage_report.json --evidence-set skills/alert-triage/examples/golden_evidence_set.json
	@echo "--- [2/3] Regulatory Rule Explanation (Rule R-3b) ---"
	$(VENV_PY) -m fincrime_cli.main explain R-3b
	@echo "--- [3/3] Offline Replay Evaluation & Attribution Metrics ---"
	$(VENV_PY) -m fincrime_cli.main eval --skill alert-triage --replay --gates
	@echo "Demo complete in < 5s with zero external dependencies and zero network access."

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

lint-pii:  ## Scan for real PII leaks across assets (zero-PII guarantee)
	$(VENV_PY) scripts/check_pii.py

lint-network:  ## Run the suite with sockets disabled (air-gap safety)
	$(VENV_PY) scripts/check_no_network.py -- $(TESTS) -q
	$(VENV_PY) scripts/check_no_network.py -- $(CLI_TESTS) -q

lint-schema:  ## Cross-check our schema validator against the reference implementation
	$(VENV_PY) scripts/check_schema_parity.py

lint-docs:  ## Verify documentation code snippets (guarantee zero drift)
	$(VENV_PY) scripts/check_docs.py

validate:  ## Validate the canonical contracts
	$(VENV_PY) -m json.tool contracts/finding.schema.json > NUL
	$(VENV_PY) -c "import json,pathlib; [json.loads(p.read_text(encoding='utf-8')) for p in pathlib.Path('contracts').glob('*.json')]; print('contracts OK')"

validate-skills:  ## Validate every skill package, case suite and golden artifact
	$(VENV_PY) -m fincrime_cli.main validate skills/investigation-qa
	$(VENV_PY) -m fincrime_cli.main validate skills/alert-triage
	$(VENV_PY) -m fincrime_cli.main validate skills/case-summarize
	$(VENV_PY) -m fincrime_cli.main validate skills/evidence-request
	$(VENV_PY) -m fincrime_cli.main validate skills/sar-narrative-draft
	$(VENV_PY) -m fincrime_cli.main validate skills/sanctions-alert
	$(VENV_PY) -m fincrime_cli.main validate skills/alert-triage/evals/suites/alert-triage
	$(VENV_PY) -m fincrime_cli.main validate skills/case-summarize/evals/suites/case-summarize
	$(VENV_PY) -m fincrime_cli.main validate skills/evidence-request/evals/suites/evidence-request
	$(VENV_PY) -m fincrime_cli.main validate skills/investigation-qa/evals/suites/investigation-qa
	$(VENV_PY) -m fincrime_cli.main validate skills/sar-narrative-draft/evals/suites/sar-narrative-draft
	$(VENV_PY) -m fincrime_cli.main validate skills/sanctions-alert/evals/suites/sanctions-alert
	$(VENV_PY) -m fincrime_cli.main validate skills/alert-triage/examples/golden_triage_report.json --evidence-set skills/alert-triage/examples/golden_evidence_set.json --knowledge-pack knowledge/packs/core-2026-10
	$(VENV_PY) -m fincrime_cli.main validate skills/case-summarize/examples/golden_case_summary.json --evidence-set skills/case-summarize/examples/golden_evidence_set.json --knowledge-pack knowledge/packs/core-2026-10
	$(VENV_PY) -m fincrime_cli.main validate skills/evidence-request/examples/golden_request_dossier.json --evidence-set skills/evidence-request/examples/golden_evidence_set.json --knowledge-pack knowledge/packs/core-2026-10
	$(VENV_PY) -m fincrime_cli.main validate skills/investigation-qa/examples/golden_qa_result.json --evidence-set skills/investigation-qa/examples/golden_evidence_set.json --knowledge-pack knowledge/packs/core-2026-10
	$(VENV_PY) -m fincrime_cli.main validate skills/sar-narrative-draft/examples/golden_sar_narrative.json --evidence-set skills/sar-narrative-draft/examples/golden_evidence_set.json --knowledge-pack knowledge/packs/core-2026-10
	$(VENV_PY) -m fincrime_cli.main validate skills/sanctions-alert/examples/golden_sanctions_assessment.json --evidence-set skills/sanctions-alert/examples/golden_evidence_set.json --knowledge-pack knowledge/packs/core-2026-10
	$(VENV_PY) -m fincrime_cli.main knowledge validate --pack knowledge/examples/sample-pack
	$(VENV_PY) -m fincrime_cli.main knowledge validate --pack knowledge/packs/core-2026-10

validate-promotion:  ## Apply the promotion gate (ADR-0006): stale knowledge blocks
	$(VENV_PY) -m fincrime_cli.main validate skills/investigation-qa --promotion
	$(VENV_PY) -m fincrime_cli.main validate skills/alert-triage --promotion
	$(VENV_PY) -m fincrime_cli.main validate skills/case-summarize --promotion
	$(VENV_PY) -m fincrime_cli.main validate skills/evidence-request --promotion
	$(VENV_PY) -m fincrime_cli.main validate skills/sar-narrative-draft --promotion
	$(VENV_PY) -m fincrime_cli.main validate skills/sanctions-alert --promotion
	$(VENV_PY) -m fincrime_cli.main knowledge validate --pack knowledge/packs/core-2026-10 --promotion

# Regenerate the synthetic case suites and replays (Phase 5).
cases:
	$(VENV_PY) scripts/generate_synthetic_corpus.py

cases-check:
	$(VENV_PY) scripts/generate_synthetic_corpus.py

eval:  ## Run the evaluation suites and gates (Phase 4)
	$(VENV_PY) -m fincrime_cli.main eval --skill all --replay --gates
	$(VENV_PY) scripts/generate_conformance_report.py

ci: lint lint-pii lint-docs validate test test-cli lint-network lint-schema validate-skills eval  ## Run everything CI runs
	@echo "CI checks passed."

clean:  ## Remove build and cache artifacts
	rmdir /s /q $(VENV) 2>nul || true
	rmdir /s /q .pytest_cache 2>nul || true
	rmdir /s /q **/__pycache__ 2>nul || true
