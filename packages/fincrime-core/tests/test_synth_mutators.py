"""Tests for adversarial mutators and defect code verification."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from fincrime_core.paths import repo_root
from fincrime_core.synth.mutators import (
    MUTATOR_REGISTRY,
    apply_mutator,
    culpability_assertion_mutator,
    isolated_adverse_reading_mutator,
    list_mutator_names,
    timeline_drift_mutator,
    unauthorized_action_mutator,
    unbounded_confidence_mutator,
    unsupported_citation_mutator,
)
from fincrime_core.validate.validator import Validator


@pytest.fixture
def golden_setup() -> tuple[dict[str, Any], dict[str, Any], Validator]:
    """Load the golden triage report and evidence set from examples."""
    root = repo_root()
    assert root is not None, "Repository root must be resolvable"
    report_path = root / "skills" / "alert-triage" / "examples" / "golden_triage_report.json"
    evidence_path = root / "skills" / "alert-triage" / "examples" / "golden_evidence_set.json"

    with report_path.open("r", encoding="utf-8") as f:
        finding = json.load(f)
    with evidence_path.open("r", encoding="utf-8") as f:
        evidence_set = json.load(f)

    validator = Validator(evidence_set=evidence_set)
    # Sanity check: baseline golden finding must be clean
    base_result = validator.validate(finding)
    assert base_result.valid is True
    assert len(base_result.errors) == 0

    return finding, evidence_set, validator


def test_mutator_registry_has_all_six_mutators() -> None:
    """Registry must contain all 6 target adversarial mutators."""
    expected = {
        "unsupported_citation",
        "culpability_assertion",
        "isolated_adverse_reading",
        "unbounded_confidence",
        "unauthorized_action",
        "timeline_drift",
    }
    assert set(list_mutator_names()) == expected
    for name in expected:
        spec = MUTATOR_REGISTRY[name]
        assert spec.name == name
        assert spec.target_rule.startswith("R-")
        assert len(spec.target_defect_code) > 0


def test_unsupported_citation_mutator_triggers_r1a(golden_setup) -> None:
    """unsupported_citation_mutator must provably trigger defect unsupported_claim under R-1a."""
    finding, evidence_set, validator = golden_setup

    mutated = unsupported_citation_mutator(finding, ghost_ref="txn:TXN-GHOST-9999#/amount")
    result = validator.validate(mutated)

    matching = [
        d for d in result.defects
        if d.code == "unsupported_claim" and d.rule_id == "R-1a"
    ]
    assert len(matching) >= 1
    assert "TXN-GHOST-9999" in matching[0].message
    assert result.unsupported_claim_rate > 0.0


def test_culpability_assertion_mutator_triggers_r6(golden_setup) -> None:
    """culpability_assertion_mutator must provably trigger defect unsupported_claim under R-6 (warn)."""
    finding, evidence_set, validator = golden_setup

    mutated = culpability_assertion_mutator(finding)
    result = validator.validate(mutated)

    matching = [
        d for d in result.defects
        if d.code == "unsupported_claim" and d.rule_id == "R-6" and d.severity == "warn"
    ]
    assert len(matching) >= 1
    assert "criminality" in matching[0].message.lower()


def test_isolated_adverse_reading_mutator_triggers_r3b(golden_setup) -> None:
    """isolated_adverse_reading_mutator must provably trigger defect missing_benign_reading under R-3b."""
    finding, evidence_set, validator = golden_setup

    mutated = isolated_adverse_reading_mutator(finding)
    result = validator.validate(mutated)

    matching = [
        d for d in result.defects
        if d.code == "missing_benign_reading" and d.rule_id == "R-3b"
    ]
    assert len(matching) >= 1
    assert "benign_reading" in matching[0].message


def test_unbounded_confidence_mutator_triggers_r11(golden_setup) -> None:
    """unbounded_confidence_mutator must provably trigger defect decisive_gap_unacknowledged under R-11."""
    finding, evidence_set, validator = golden_setup

    mutated = unbounded_confidence_mutator(finding)
    result = validator.validate(mutated)

    matching = [
        d for d in result.defects
        if d.code == "decisive_gap_unacknowledged" and d.rule_id == "R-11"
    ]
    assert len(matching) >= 1
    assert "decisive evidence gap" in matching[0].message


def test_unauthorized_action_mutator_triggers_r7(golden_setup) -> None:
    """unauthorized_action_mutator must provably trigger defect escalation_missed under R-7."""
    finding, evidence_set, validator = golden_setup

    mutated = unauthorized_action_mutator(finding)
    result = validator.validate(mutated)

    matching = [
        d for d in result.defects
        if d.code == "escalation_missed" and d.rule_id == "R-7"
    ]
    assert len(matching) >= 1
    assert "human approval" in matching[0].message.lower()


def test_timeline_drift_mutator_triggers_r1b(golden_setup) -> None:
    """timeline_drift_mutator must provably trigger defect unsupported_claim under R-1b."""
    finding, evidence_set, validator = golden_setup

    mutated = timeline_drift_mutator(finding, ghost_ref="txn:TXN-GHOST-TIMELINE-9999#/ts")
    result = validator.validate(mutated)

    matching = [
        d for d in result.defects
        if d.code == "unsupported_claim" and d.rule_id == "R-1b"
    ]
    assert len(matching) >= 1
    assert "TXN-GHOST-TIMELINE-9999" in matching[0].message


def test_apply_mutator_registry_execution(golden_setup) -> None:
    """apply_mutator must execute cleanly and leave original golden finding unmodified."""
    finding, evidence_set, validator = golden_setup
    orig_copy = json.dumps(finding, sort_keys=True)

    for name in list_mutator_names():
        mutated = apply_mutator(finding, name)
        assert mutated is not finding
        spec = MUTATOR_REGISTRY[name]
        result = validator.validate(mutated)

        # Confirm target defect code is present in defects
        defect_codes = [d.code for d in result.defects]
        assert spec.target_defect_code in defect_codes, (
            f"Mutator {name} did not produce target defect code {spec.target_defect_code}"
        )

    # Verify input finding was not mutated in place
    assert json.dumps(finding, sort_keys=True) == orig_copy
