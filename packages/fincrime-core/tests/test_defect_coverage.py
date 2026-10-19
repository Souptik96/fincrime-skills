"""Every active defect code must be reachable, and the taxonomy must not lie.

The reviewer found six defect codes declared in the taxonomy that the
validator could never emit. A declared code that is never emitted gives a
false impression of enforcement coverage, and a documented code that is never
produced is worse than an undocumented one.

Two guards prevent that class of drift permanently:

1. **Behavioural coverage.** Every code marked ``stage: active`` in the
   taxonomy must be produced by some input. The check is behavioural, not a
   scan of the source: a static scan is itself fragile, and it once reported
   ``malformed_evidence_ref`` as a ghost even though it is emitted through a
   lookup table rather than a literal.

2. **Reserved vocabulary.** A code marked ``stage: planned`` must NOT be
   emitted today. If one starts being emitted, the taxonomy is stale and the
   test fails rather than letting the drift pass silently.
"""

from __future__ import annotations

import copy
from typing import Any

import pytest

from fincrime_core.validate.defects import load_defect_taxonomy
from fincrime_core.validate.validator import Validator

BASE_CLAIM = {
    "id": "C-001",
    "class": "fact",
    "statement": "A statement.",
    "confidence": {"level": "high", "basis": "Read from the evidence."},
    "evidence_refs": ["subject:s1#"],
}


def _artifact(claims: list[dict[str, Any]], **artifact_overrides: Any) -> dict[str, Any]:
    artifact = {
        "skill_id": "s",
        "skill_version": "1.0.0",
        "artifact_type": "triage_report",
        "subject_ids": ["s1"],
        "jurisdictions": ["US"],
        "created_at": "2026-01-01T00:00:00Z",
        "completeness": "complete",
    }
    artifact.update(artifact_overrides)
    return {
        "contract_version": "fincrime/finding/1.0.0",
        "artifact": artifact,
        "provenance": {
            "skill_id": "s",
            "skill_version": "1.0.0",
            "model": {"provider": "p", "id": "i"},
            "prompt_sha256": "a" * 64,
            "evidence_set_sha256": "b" * 64,
            "knowledge_pack": {"id": "k", "version": "v", "as_of": "2026-01-01"},
            "policy_set": {"id": "p", "version": "1"},
            "run_id": "r",
            "timestamp": "2026-01-01T00:00:00Z",
        },
        "claims": claims,
        "human_decision_required": [
            {"decision_id": "D-01", "question": "q", "owner_role": "r"}
        ],
    }


EVIDENCE_SET = {"subject": {"subject_id": "s1"}}


def _codes(
    artifact: dict[str, Any],
    evidence_set: dict[str, Any] | None = None,
    **validator_kwargs: Any,
) -> set[str]:
    result = Validator(
        evidence_set=evidence_set if evidence_set is not None else EVIDENCE_SET,
        **validator_kwargs,
    ).validate(artifact)
    return {d.code for d in result.defects}


class TestDefectCoverage:
    """Each active code must be produced by the case below it."""

    def test_unsupported_claim_missing_reference(self) -> None:
        claim = {**copy.deepcopy(BASE_CLAIM), "evidence_refs": []}
        assert "unsupported_claim" in _codes(_artifact([claim]))

    def test_unsupported_claim_unresolvable_reference_on_any_class(self) -> None:
        """The bypass the review found: a fabricated ref on a risk assessment."""
        claim = {
            "id": "C-001",
            "class": "risk_assessment",
            "statement": "High risk.",
            "confidence": {"level": "moderate", "basis": "b"},
            "evidence_refs": ["txn:FABRICATED#/amount"],
        }
        assert "unsupported_claim" in _codes(_artifact([claim]))

    def test_malformed_evidence_ref(self) -> None:
        claim = {**copy.deepcopy(BASE_CLAIM), "evidence_refs": ["not a reference"]}
        assert "malformed_evidence_ref" in _codes(_artifact([claim]))

    def test_over_broad_citation(self) -> None:
        evidence_set = {"subject": {"subject_id": "s1", "lines": list(range(30))}}
        claim = {**copy.deepcopy(BASE_CLAIM), "evidence_refs": ["subject:s1#/lines"]}
        result = Validator(evidence_set=evidence_set).validate(_artifact([claim]))
        assert "over_broad_citation" in {d.code for d in result.defects}
    def test_misclassified_claim(self) -> None:
        claim = {
            "id": "C-001",
            "class": "hypothesis",
            "statement": "s",
            "confidence": {"level": "low", "basis": "b"},
            "epistemic_type": "adverse_reading",
        }
        assert "misclassified_claim" in _codes(_artifact([claim]))

    def test_missing_benign_reading(self) -> None:
        claim = {
            "id": "C-001",
            "class": "hypothesis",
            "statement": "s",
            "confidence": {"level": "low", "basis": "b"},
            "epistemic_type": "adverse_reading",
            "falsifier": "f",
        }
        assert "missing_benign_reading" in _codes(_artifact([claim]))

    def test_overstated_confidence(self) -> None:
        """R-8 caps a *conclusion* drawn from a partial window.

        A fact read from a record that is present is complete in itself, so
        the rule applies to conclusions, not to facts.
        """
        claim = {
            "id": "C-001",
            "class": "indicator",
            "statement": "A conclusion drawn from the window.",
            "confidence": {"level": "high", "basis": "b"},
            "evidence_refs": ["subject:s1#"],
            "indicator_ids": ["IND-X"],
        }
        artifact = _artifact([claim], completeness="partial")
        assert "overstated_confidence" in _codes(artifact)

    def test_recommendation_without_basis(self) -> None:
        claim = {
            "id": "C-001",
            "class": "recommendation",
            "statement": "Escalate.",
            "confidence": {"level": "low", "basis": "b"},
            "evidence_refs": [],
            "human_approval_required": True,
        }
        assert "recommendation_without_basis" in _codes(_artifact([claim]))

    def test_recommendation_with_a_basis_is_accepted(self) -> None:
        claim = {
            "id": "C-001",
            "class": "recommendation",
            "statement": "Escalate.",
            "confidence": {"level": "low", "basis": "b"},
            "evidence_refs": ["subject:s1#"],
            "human_approval_required": True,
        }
        assert "recommendation_without_basis" not in _codes(_artifact([claim]))

    def test_recommendation_may_cite_a_claim_instead_of_evidence(self) -> None:
        """A recommendation's basis may be the claim it explains."""
        facts = copy.deepcopy(BASE_CLAIM)
        recommendation = {
            "id": "C-002",
            "class": "recommendation",
            "statement": "Escalate.",
            "confidence": {"level": "low", "basis": "b"},
            "evidence_refs": [],
            "explains": ["C-001"],
            "human_approval_required": True,
        }
        assert "recommendation_without_basis" not in _codes(_artifact([facts, recommendation]))

    def test_provenance_gap(self) -> None:
        claim = {
            "id": "C-001",
            "class": "decision",
            "statement": "Escalate.",
            "confidence": {"level": "low", "basis": "b"},
        }
        assert "provenance_gap" in _codes(_artifact([claim]))

    def test_escalation_missed(self) -> None:
        artifact = _artifact([copy.deepcopy(BASE_CLAIM)])
        artifact["human_decision_required"] = []
        assert "escalation_missed" in _codes(artifact)

    def test_escalation_missed_when_approval_is_disclaimed(self) -> None:
        claim = {
            "id": "C-001",
            "class": "recommendation",
            "statement": "Escalate.",
            "confidence": {"level": "low", "basis": "b"},
            "evidence_refs": ["subject:s1#"],
            "human_approval_required": False,
        }
        assert "escalation_missed" in _codes(_artifact([claim]))

    def test_jurisdiction_overreach_on_a_claim(self) -> None:
        claim = {**copy.deepcopy(BASE_CLAIM), "jurisdictions": ["GB"]}
        assert "jurisdiction_overreach" in _codes(_artifact([claim]))

    def test_jurisdiction_overreach_on_the_artifact(self) -> None:
        artifact = _artifact([copy.deepcopy(BASE_CLAIM)], jurisdictions=["GB"])
        assert "jurisdiction_overreach" in _codes(artifact, allowed_jurisdictions=["US"])

    def test_missing_draft_notice(self) -> None:
        artifact = _artifact([copy.deepcopy(BASE_CLAIM)], artifact_type="sar_narrative")
        assert "missing_draft_notice" in _codes(artifact)

    def test_conflicting_draft_notice(self) -> None:
        claim = {
            **copy.deepcopy(BASE_CLAIM),
            "statement": "This SAR has been filed with FinCEN.",
        }
        artifact = _artifact([claim], artifact_type="sar_narrative")
        artifact["draft_notice"] = {"text": "DRAFT", "tool_generated": True}
        assert "conflicting_draft_notice" in _codes(artifact)

    def test_unknown_indicator(self) -> None:
        claim = {
            "id": "C-001",
            "class": "indicator",
            "statement": "s",
            "confidence": {"level": "moderate", "basis": "b"},
            "evidence_refs": ["subject:s1#"],
            "indicator_ids": ["IND-NOPE"],
        }
        assert "unknown_indicator" in _codes(_artifact([claim]), known_indicator_ids=["IND-YES"])

    def test_expired_knowledge_citation(self) -> None:
        claim = {**copy.deepcopy(BASE_CLAIM), "knowledge_ids": ["REG-OLD"]}
        assert "expired_knowledge_citation" in _codes(
            _artifact([claim]), expired_knowledge_ids=["REG-OLD"]
        )

    def test_schema_violation(self) -> None:
        artifact = _artifact([copy.deepcopy(BASE_CLAIM)])
        artifact["contract_version"] = "fincrime/finding/9.9.9"
        assert "schema_violation" in _codes(artifact)

    def test_decisive_gap_unacknowledged(self) -> None:
        claim = {
            "id": "C-001",
            "class": "risk_assessment",
            "statement": "High risk.",
            "confidence": {"level": "moderate", "basis": "b"},
            "evidence_refs": ["subject:s1#"],
        }
        artifact = _artifact([claim])
        artifact["gaps"] = [
            {
                "gap_id": "G-01",
                "description": "The decisive record is absent.",
                "decisive": True,
                "blocks_conclusion": True,
            }
        ]
        assert "decisive_gap_unacknowledged" in _codes(artifact)


class TestTaxonomyHonesty:
    def test_every_active_code_is_reachable(self) -> None:
        """The no-ghost-defect guard.

        Each active code is listed with the case that produces it. If a code
        is added to the taxonomy and never implemented, this test fails.
        """
        taxonomy = load_defect_taxonomy()
        reachable: set[str] = set()

        scenarios = {
            "unsupported_claim": lambda: _codes(
                _artifact([{**copy.deepcopy(BASE_CLAIM), "evidence_refs": []}])
            ),
            "malformed_evidence_ref": lambda: _codes(
                _artifact([{**copy.deepcopy(BASE_CLAIM), "evidence_refs": ["not a ref"]}])
            ),
            "over_broad_citation": lambda: _codes(
                _artifact([{**copy.deepcopy(BASE_CLAIM), "evidence_refs": ["subject:s1#/lines"]}]),
                evidence_set={"subject": {"subject_id": "s1", "lines": list(range(30))}},
            ),
            "misclassified_claim": lambda: _codes(
                _artifact(
                    [
                        {
                            "id": "C-001",
                            "class": "hypothesis",
                            "statement": "s",
                            "confidence": {"level": "low", "basis": "b"},
                            "epistemic_type": "adverse_reading",
                        }
                    ]
                )
            ),
            "missing_benign_reading": lambda: _codes(
                _artifact(
                    [
                        {
                            "id": "C-001",
                            "class": "hypothesis",
                            "statement": "s",
                            "confidence": {"level": "low", "basis": "b"},
                            "epistemic_type": "adverse_reading",
                            "falsifier": "f",
                        }
                    ]
                )
            ),
            "overstated_confidence": lambda: _codes(
                _artifact(
                    [
                        {
                            "id": "C-001",
                            "class": "indicator",
                            "statement": "A conclusion drawn from the window.",
                            "confidence": {"level": "high", "basis": "b"},
                            "evidence_refs": ["subject:s1#"],
                            "indicator_ids": ["IND-X"],
                        }
                    ],
                    completeness="partial",
                )
            ),
            "recommendation_without_basis": lambda: _codes(
                _artifact(
                    [
                        {
                            "id": "C-001",
                            "class": "recommendation",
                            "statement": "s",
                            "confidence": {"level": "low", "basis": "b"},
                            "evidence_refs": [],
                            "human_approval_required": True,
                        }
                    ]
                )
            ),
            "provenance_gap": lambda: _codes(
                _artifact(
                    [
                        {
                            "id": "C-001",
                            "class": "decision",
                            "statement": "s",
                            "confidence": {"level": "low", "basis": "b"},
                        }
                    ]
                )
            ),
            "escalation_missed": lambda: _codes(
                {**_artifact([copy.deepcopy(BASE_CLAIM)]), "human_decision_required": []}
            ),
            "jurisdiction_overreach": lambda: _codes(
                _artifact([{**copy.deepcopy(BASE_CLAIM), "jurisdictions": ["GB"]}])
            ),
            "missing_draft_notice": lambda: _codes(
                _artifact([copy.deepcopy(BASE_CLAIM)], artifact_type="sar_narrative")
            ),
            "conflicting_draft_notice": lambda: _codes(
                {
                    **_artifact(
                        [{**copy.deepcopy(BASE_CLAIM), "statement": "This SAR has been filed."}],
                        artifact_type="sar_narrative",
                    ),
                    "draft_notice": {"text": "DRAFT", "tool_generated": True},
                }
            ),
            "unknown_indicator": lambda: _codes(
                _artifact(
                    [
                        {
                            "id": "C-001",
                            "class": "indicator",
                            "statement": "s",
                            "confidence": {"level": "moderate", "basis": "b"},
                            "evidence_refs": ["subject:s1#"],
                            "indicator_ids": ["IND-NOPE"],
                        }
                    ]
                ),
                known_indicator_ids=["IND-YES"],
            ),
            "expired_knowledge_citation": lambda: _codes(
                _artifact([{**copy.deepcopy(BASE_CLAIM), "knowledge_ids": ["REG-OLD"]}]),
                expired_knowledge_ids=["REG-OLD"],
            ),
            "schema_violation": lambda: _codes(
                {
                    **_artifact([copy.deepcopy(BASE_CLAIM)]),
                    "contract_version": "fincrime/finding/9.9.9",
                }
            ),
            "decisive_gap_unacknowledged": lambda: _codes(
                {
                    **_artifact(
                        [
                            {
                                "id": "C-001",
                                "class": "risk_assessment",
                                "statement": "High risk.",
                                "confidence": {"level": "moderate", "basis": "b"},
                                "evidence_refs": ["subject:s1#"],
                            }
                        ]
                    ),
                    "gaps": [
                        {
                            "gap_id": "G-01",
                            "description": "Absent.",
                            "decisive": True,
                            "blocks_conclusion": True,
                        }
                    ],
                }
            ),
        }

        for code, scenario in scenarios.items():
            reachable |= scenario()

        active_codes = {code for code, info in taxonomy.items() if info.is_active}
        unreachable = active_codes - reachable
        assert not unreachable, (
            f"defect codes declared active but never emitted: {sorted(unreachable)}. "
            "Either implement them or mark them stage: planned in the taxonomy."
        )

    def test_planned_codes_are_not_emitted(self) -> None:
        """A reserved code must not start being emitted without the taxonomy
        being updated, or the stage marker becomes a lie."""
        taxonomy = load_defect_taxonomy()
        planned = {code for code, info in taxonomy.items() if not info.is_active}
        assert planned, "the taxonomy should reserve at least one code for a later phase"
        emitted = set()
        for scenario in (
            lambda: _codes(_artifact([{**copy.deepcopy(BASE_CLAIM), "evidence_refs": []}])),
            lambda: _codes(_artifact([{**copy.deepcopy(BASE_CLAIM), "evidence_refs": ["x"]}])),
            lambda: _codes(
                {
                    **_artifact([copy.deepcopy(BASE_CLAIM)]),
                    "human_decision_required": [],
                }
            ),
        ):
            emitted |= scenario()
        assert not (emitted & planned)

    def test_every_code_has_a_stage(self) -> None:
        taxonomy = load_defect_taxonomy()
        for info in taxonomy.values():
            assert info.stage in ("active", "planned")

    def test_planned_codes_declare_their_phase(self) -> None:
        taxonomy = load_defect_taxonomy()
        for info in taxonomy.values():
            if info.stage == "planned":
                assert info.planned_for, f"{info.code} is planned but names no phase"
