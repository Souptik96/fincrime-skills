"""Tests for the claim lints and the top-level validator.

These tests encode the five seeded defects the Phase 0 exit criteria name, and
assert that the validator produces no false positives on the conformant
baseline.
"""

from __future__ import annotations

import copy

import pytest

from fincrime_core.validate.claim_lints import CulpabilityMatcher
from fincrime_core.validate.validator import EnforcementContext, Validator


def make_validator(evidence_set: dict, **kwargs) -> Validator:
    return Validator(evidence_set=evidence_set, **kwargs)


class TestBaseline:
    def test_conformant_artifact_has_no_errors(self, evidence_set: dict, valid_artifact: dict) -> None:
        result = make_validator(evidence_set).validate(valid_artifact)
        assert result.errors == [], [d.to_dict() for d in result.errors]
        assert result.valid

    def test_baseline_has_full_evidence_attribution(
        self, evidence_set: dict, valid_artifact: dict
    ) -> None:
        result = make_validator(evidence_set).validate(valid_artifact)
        assert result.evidence_attribution_accuracy == 1.0
        assert result.unsupported_claim_rate == 0.0

    def test_deterministic_across_runs(self, evidence_set: dict, valid_artifact: dict) -> None:
        validator = make_validator(evidence_set)
        first = validator.validate(valid_artifact)
        second = validator.validate(valid_artifact)
        assert [d.to_dict() for d in first.defects] == [d.to_dict() for d in second.defects]

    def test_defects_are_ordered_deterministically(
        self, evidence_set: dict, valid_artifact: dict
    ) -> None:
        broken = copy.deepcopy(valid_artifact)
        broken["claims"][0]["evidence_refs"] = []
        broken["claims"][2].pop("falsifier")
        result = make_validator(evidence_set).validate(broken)
        keys = [d.sort_key() for d in result.defects]
        assert keys == sorted(keys)


class TestSeededDefects:
    """The five seeded defects named in the Phase 0 exit criteria."""

    def test_seeded_1_missing_evidence_ref(
        self, evidence_set: dict, valid_artifact: dict
    ) -> None:
        artifact = copy.deepcopy(valid_artifact)
        artifact["claims"][0]["evidence_refs"] = []
        result = make_validator(evidence_set).validate(artifact)
        assert "unsupported_claim" in result.error_codes
        assert result.unsupported_claim_rate > 0

    def test_seeded_2_missing_benign_hypothesis(
        self, evidence_set: dict, valid_artifact: dict
    ) -> None:
        artifact = copy.deepcopy(valid_artifact)
        artifact["claims"] = [c for c in artifact["claims"] if c["id"] != "C-004"]
        result = make_validator(evidence_set).validate(artifact)
        assert "missing_benign_reading" in result.error_codes

    def test_seeded_3_decision_without_decided_by(
        self, evidence_set: dict, valid_artifact: dict
    ) -> None:
        artifact = copy.deepcopy(valid_artifact)
        artifact["claims"].append(
            {
                "id": "C-007",
                "class": "decision",
                "statement": "The subject is suspicious and should be reported.",
                "confidence": {"level": "high", "basis": "Assessment."},
            }
        )
        result = make_validator(evidence_set).validate(artifact)
        assert "provenance_gap" in result.error_codes

    def test_seeded_4_unknown_indicator_id(
        self, evidence_set: dict, valid_artifact: dict
    ) -> None:
        artifact = copy.deepcopy(valid_artifact)
        artifact["claims"][1]["indicator_ids"] = ["IND-DOES-NOT-EXIST"]
        result = make_validator(
            evidence_set, known_indicator_ids=["IND-STRUCT-THRESHOLD-PROXIMITY"]
        ).validate(artifact)
        assert "unknown_indicator" in result.error_codes

    def test_seeded_5_expired_knowledge_citation(
        self, evidence_set: dict, valid_artifact: dict
    ) -> None:
        artifact = copy.deepcopy(valid_artifact)
        artifact["claims"][1]["knowledge_ids"] = ["REG-US-OLD"]
        validator = make_validator(evidence_set, expired_knowledge_ids=["REG-US-OLD"])
        release = validator.validate(artifact, EnforcementContext(EnforcementContext.RELEASE))
        promotion = validator.validate(artifact, EnforcementContext(EnforcementContext.PROMOTION))
        assert "expired_knowledge_citation" in release.error_codes or any(
            d.code == "expired_knowledge_citation" for d in release.warnings
        )
        assert "expired_knowledge_citation" in promotion.error_codes


class TestStructuralHypotheses:
    def test_adverse_reading_requires_a_benign_reading(
        self, evidence_set: dict, valid_artifact: dict
    ) -> None:
        artifact = copy.deepcopy(valid_artifact)
        artifact["claims"] = [c for c in artifact["claims"] if c["id"] != "C-004"]
        result = make_validator(evidence_set).validate(artifact)
        assert "missing_benign_reading" in result.error_codes

    def test_hypothesis_requires_a_falsifier(
        self, evidence_set: dict, valid_artifact: dict
    ) -> None:
        artifact = copy.deepcopy(valid_artifact)
        artifact["claims"][2].pop("falsifier")
        result = make_validator(evidence_set).validate(artifact)
        assert "misclassified_claim" in result.error_codes

    def test_hypothesis_requires_an_epistemic_type(
        self, evidence_set: dict, valid_artifact: dict
    ) -> None:
        artifact = copy.deepcopy(valid_artifact)
        artifact["claims"][2].pop("epistemic_type")
        result = make_validator(evidence_set).validate(artifact)
        assert "misclassified_claim" in result.error_codes

    def test_soft_synonym_adverse_reading_is_still_structurally_blocked(
        self, evidence_set: dict, valid_artifact: dict
    ) -> None:
        """A euphemistic statement must not evade the benign-reading requirement.

        The whole point of the structural defense: the wording is irrelevant.
        """
        artifact = copy.deepcopy(valid_artifact)
        artifact["claims"][2]["statement"] = (
            "The pattern exhibited is suggestive of deliberate avoidance of reporting obligations."
        )
        artifact["claims"] = [c for c in artifact["claims"] if c["id"] != "C-004"]
        result = make_validator(evidence_set).validate(artifact)
        assert "missing_benign_reading" in result.error_codes

    def test_adverse_reading_at_high_confidence_with_a_decisive_gap(
        self, evidence_set: dict, valid_artifact: dict
    ) -> None:
        artifact = copy.deepcopy(valid_artifact)
        artifact["claims"][2]["confidence"] = {"level": "high", "basis": "Asserted."}
        result = make_validator(evidence_set).validate(artifact)
        assert "overstated_confidence" in result.error_codes


class TestCulpabilityLint:
    def test_flags_a_culpability_assertion(self) -> None:
        matcher = CulpabilityMatcher()
        assert not matcher.is_clean("The customer is a money launderer.")

    def test_does_not_flag_a_negated_statement(self) -> None:
        matcher = CulpabilityMatcher()
        assert matcher.is_clean("There is no evidence that the customer committed money laundering.")

    def test_does_not_flag_a_benign_statement(self) -> None:
        matcher = CulpabilityMatcher()
        assert matcher.is_clean("Cash deposits cluster below the reporting threshold.")

    def test_is_reported_as_a_warning_not_an_error(
        self, evidence_set: dict, valid_artifact: dict
    ) -> None:
        artifact = copy.deepcopy(valid_artifact)
        artifact["claims"][0]["statement"] = "The customer is a money launderer."
        result = make_validator(evidence_set).validate(artifact)
        codes = {d.code for d in result.warnings}
        assert "unsupported_claim" in codes
        assert "unsupported_claim" not in {d.code for d in result.errors}


class TestOtherRules:
    def test_partial_evidence_caps_conclusion_confidence(
        self, evidence_set: dict, valid_artifact: dict
    ) -> None:
        artifact = copy.deepcopy(valid_artifact)
        artifact["artifact"]["completeness"] = "partial"
        # The indicator is a conclusion drawn from the window, so it must be
        # capped. A fact read from a present record is not.
        artifact["claims"][1]["confidence"] = {"level": "high", "basis": "Asserted."}
        result = make_validator(evidence_set).validate(artifact)
        assert "overstated_confidence" in result.error_codes

    def test_partial_evidence_does_not_cap_a_fact_read_from_a_present_record(
        self, evidence_set: dict, valid_artifact: dict
    ) -> None:
        """A fact about a record that is present is complete in itself.

        What a partial window undermines is the inference drawn from the
        window, not the reading of a record that is in the set.
        """
        artifact = copy.deepcopy(valid_artifact)
        artifact["artifact"]["completeness"] = "partial"
        result = make_validator(evidence_set).validate(artifact)
        fact_defects = [
            d for d in result.errors if d.claim_id == "C-001" and d.code == "overstated_confidence"
        ]
        assert fact_defects == []

    def test_missing_draft_notice_on_a_sar_narrative(
        self, evidence_set: dict, valid_artifact: dict
    ) -> None:
        artifact = copy.deepcopy(valid_artifact)
        artifact["artifact"]["artifact_type"] = "sar_narrative"
        result = make_validator(evidence_set).validate(artifact)
        assert "missing_draft_notice" in result.error_codes

    def test_present_draft_notice_is_accepted(
        self, evidence_set: dict, valid_artifact: dict
    ) -> None:
        artifact = copy.deepcopy(valid_artifact)
        artifact["artifact"]["artifact_type"] = "sar_narrative"
        artifact["draft_notice"] = {
            "text": "*** DRAFT DOCUMENT FOR HUMAN COMPLIANCE REVIEW ONLY ***",
            "tool_generated": True,
        }
        result = make_validator(evidence_set).validate(artifact)
        assert "missing_draft_notice" not in result.error_codes

    def test_draft_notice_not_tool_generated_is_rejected(
        self, evidence_set: dict, valid_artifact: dict
    ) -> None:
        artifact = copy.deepcopy(valid_artifact)
        artifact["artifact"]["artifact_type"] = "sar_narrative"
        artifact["draft_notice"] = {"text": "DRAFT", "tool_generated": False}
        result = make_validator(evidence_set).validate(artifact)
        assert "missing_draft_notice" in result.error_codes

    def test_recommendation_cannot_declare_that_no_approval_is_required(
        self, evidence_set: dict, valid_artifact: dict
    ) -> None:
        artifact = copy.deepcopy(valid_artifact)
        artifact["claims"][5]["human_approval_required"] = False
        result = make_validator(evidence_set).validate(artifact)
        assert "escalation_missed" in result.error_codes

    def test_missing_human_decision_is_reported(
        self, evidence_set: dict, valid_artifact: dict
    ) -> None:
        artifact = copy.deepcopy(valid_artifact)
        artifact["human_decision_required"] = []
        result = make_validator(evidence_set).validate(artifact)
        assert "escalation_missed" in result.error_codes


class TestTotality:
    @pytest.mark.parametrize(
        "artifact",
        [
            {},
            {"claims": "not a list"},
            {"claims": [None]},
            {"artifact": {"skill_id": 5}},
            {"provenance": {"model": "not an object"}},
            {"evidence_inventory": [{"source_id": 1}]},
        ],
    )
    def test_never_raises_on_malformed_artifacts(
        self, evidence_set: dict, artifact: dict
    ) -> None:
        result = make_validator(evidence_set).validate(artifact)
        assert not result.valid
