"""The committed example must validate.

An example that no longer validates is worse than no example: it is a claim
about the project's behaviour that has quietly become false. This test binds
the documented example to the implementation.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fincrime_core.validate.validator import Validator

REPO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLE_DIR = REPO_ROOT / "examples" / "01-alert-triage-structuring"


class TestCommittedExample:
    @pytest.fixture()
    def example(self) -> tuple[dict, dict]:
        with (EXAMPLE_DIR / "evidence-set.json").open("r", encoding="utf-8") as handle:
            evidence_set = json.load(handle)
        with (EXAMPLE_DIR / "artifact.json").open("r", encoding="utf-8") as handle:
            artifact = json.load(handle)
        return evidence_set, artifact

    def test_the_example_validates(self, example: tuple[dict, dict]) -> None:
        evidence_set, artifact = example
        result = Validator(evidence_set=evidence_set).validate(artifact)
        assert result.valid, [d.to_dict() for d in result.errors]
        assert result.errors == []

    def test_the_example_has_full_evidence_attribution(self, example: tuple[dict, dict]) -> None:
        evidence_set, artifact = example
        result = Validator(evidence_set=evidence_set).validate(artifact)
        assert result.evidence_attribution_accuracy == 1.0
        assert result.unsupported_claim_rate == 0.0

    def test_the_example_demonstrates_a_benign_reading(self, example: tuple[dict, dict]) -> None:
        evidence_set, artifact = example
        result = Validator(evidence_set=evidence_set).validate(artifact)
        epistemic_types = {c.get("epistemic_type") for c in artifact["claims"]}
        assert "adverse_reading" in epistemic_types
        assert "benign_reading" in epistemic_types

    def test_the_example_leaves_the_decision_with_a_human(self, example: tuple[dict, dict]) -> None:
        evidence_set, artifact = example
        assert artifact["human_decision_required"]
        result = Validator(evidence_set=evidence_set).validate(artifact)
        assert "escalation_missed" not in result.error_codes

    def test_the_example_records_its_decisive_gap(self, example: tuple[dict, dict]) -> None:
        evidence_set, artifact = example
        decisive = [g for g in artifact["gaps"] if g.get("decisive")]
        assert decisive

    def test_removing_the_benign_hypothesis_breaks_the_example(self, example: tuple[dict, dict]) -> None:
        """The example must fail when the benign reading is removed.

        This is the check that proves the structural defense works, and that
        the documented example is not accidentally passing for a different
        reason.
        """
        evidence_set, artifact = example
        broken = json.loads(json.dumps(artifact))
        broken["claims"] = [c for c in broken["claims"] if c.get("epistemic_type") != "benign_reading"]
        result = Validator(evidence_set=evidence_set).validate(broken)
        assert not result.valid
        assert "missing_benign_reading" in result.error_codes

    def test_removing_evidence_refs_breaks_the_example(self, example: tuple[dict, dict]) -> None:
        evidence_set, artifact = example
        broken = json.loads(json.dumps(artifact))
        for claim in broken["claims"]:
            if claim["class"] in ("fact", "observation", "indicator"):
                claim.pop("evidence_refs", None)
        result = Validator(evidence_set=evidence_set).validate(broken)
        assert not result.valid
        assert "unsupported_claim" in result.error_codes

    def test_a_dangling_reference_breaks_the_example(self, example: tuple[dict, dict]) -> None:
        evidence_set, artifact = example
        broken = json.loads(json.dumps(artifact))
        broken["claims"][0]["evidence_refs"] = ["txn:0000#/amount"]
        result = Validator(evidence_set=evidence_set).validate(broken)
        assert not result.valid
        assert "unsupported_claim" in result.error_codes
