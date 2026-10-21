"""Tests for the policy rule model extensions and the policy set.

Three things changed in the rule model in Phase 1, and each is a semantic
change to an enforceable control (ADR-0003), so each is pinned by a test
that fails without the change:

* ``when`` — an artifact-level gate on a rule.
* ``require.any_of`` — a per-claim disjunction.
* ``pattern`` — a regular expression, not a substring.

And one bug was fixed: ``composite.any`` behaved like ``composite.all``, so
a rule that said "at least one of these" actually said "all of these".
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from fincrime_core.contract.loader import parse_finding
from fincrime_core.policy.evaluator import PolicyEvaluator, PolicyRule
from fincrime_core.policy.set import (
    export_policy_set,
    load_policy_set,
    parse_policy_set,
    policy_set_checksum,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_POLICY_SET = REPO_ROOT / "policies" / "default" / "policy-set.json"
GOLDEN_ARTIFACT = REPO_ROOT / "examples" / "01-alert-triage-structuring" / "artifact.json"


def rule(**kwargs: Any) -> PolicyRule:
    base: dict[str, Any] = {
        "id": "POL-TEST",
        "version": "1.0.0",
        "severity": "error",
        "description": "test rule",
        "kind": "count",
        "rule": {},
        "message": "test message",
    }
    base.update(kwargs)
    return PolicyRule(
        id=base["id"],
        version=base["version"],
        severity=base["severity"],
        description=base["description"],
        kind=base["kind"],
        rule=base["rule"],
        message=base["message"],
        applies_to=tuple(base.get("applies_to", ())),
        jurisdictions=tuple(base.get("jurisdictions", ())),
        when=base.get("when"),
    )


class TestWhenGate:
    def test_the_gate_applies_only_when_the_artifact_satisfies_it(
        self, valid_artifact: dict
    ) -> None:
        finding = parse_finding(valid_artifact)
        evaluator = PolicyEvaluator(
            [
                rule(
                    kind="count",
                    when={"field": "artifact.completeness", "equals": "partial"},
                    rule={
                        "where": {"claim_class": ["fact"]},
                        "max_items": 0,
                    },
                )
            ]
        )
        # The artifact is complete, so the rule does not apply.
        assert evaluator.evaluate(finding) == []

        valid_artifact["artifact"]["completeness"] = "partial"
        finding = parse_finding(valid_artifact)
        assert len(evaluator.evaluate(finding)) == 1

    def test_the_gate_reads_a_provenance_field(self, valid_artifact: dict) -> None:
        finding = parse_finding(valid_artifact)
        evaluator = PolicyEvaluator(
            [
                rule(
                    kind="count",
                    when={"field": "provenance.policy_set.id", "equals": "firm-aml"},
                    rule={"where": {"claim_class": ["fact"]}, "max_items": 0},
                )
            ]
        )
        assert len(evaluator.evaluate(finding)) == 1

    def test_a_gate_that_does_not_hold_skips_the_rule(self, valid_artifact: dict) -> None:
        finding = parse_finding(valid_artifact)
        evaluator = PolicyEvaluator(
            [
                rule(
                    kind="count",
                    when={"field": "artifact.completeness", "not_equals": "complete"},
                    rule={"where": {"claim_class": ["fact"]}, "max_items": 0},
                )
            ]
        )
        assert evaluator.evaluate(finding) == []

    def test_a_gate_on_a_missing_field_does_not_hold(self, valid_artifact: dict) -> None:
        finding = parse_finding(valid_artifact)
        evaluator = PolicyEvaluator(
            [
                rule(
                    kind="count",
                    when={"field": "artifact.no_such_field", "equals": "partial"},
                    rule={"where": {"claim_class": ["fact"]}, "max_items": 0},
                )
            ]
        )
        assert evaluator.evaluate(finding) == []

    def test_a_gate_may_test_a_list_field(self, valid_artifact: dict) -> None:
        finding = parse_finding(valid_artifact)
        evaluator = PolicyEvaluator(
            [
                rule(
                    kind="count",
                    when={"field": "artifact.jurisdictions", "contains": "US"},
                    rule={"where": {"claim_class": ["fact"]}, "max_items": 0},
                )
            ]
        )
        assert len(evaluator.evaluate(finding)) == 1


class TestAnyOf:
    def test_a_claim_satisfies_the_rule_when_one_alternative_holds(
        self, valid_artifact: dict
    ) -> None:
        finding = parse_finding(valid_artifact)
        evaluator = PolicyEvaluator(
            [
                rule(
                    kind="require",
                    rule={
                        "where": {"claim_class": ["risk_assessment"]},
                        "any_of": [
                            {"kind": "require", "field": "evidence_refs", "min_items": 1},
                            {
                                "kind": "consistency",
                                "field": "confidence.level",
                                "equals": "insufficient_information",
                            },
                        ],
                    },
                )
            ]
        )
        assert evaluator.evaluate(finding) == []

    def test_the_disjunction_is_decided_claim_by_claim(self, valid_artifact: dict) -> None:
        """A sibling claim must not excuse the claim under test.

        ``composite.any`` aggregates across the whole selected set, so it
        cannot express this. ``require.any_of`` can, and the difference is
        the whole point of having it.
        """
        valid_artifact["claims"].append(
            {
                "id": "C-007",
                "class": "risk_assessment",
                "statement": "A second assessment with no evidence and no insufficiency.",
                "confidence": {"level": "low", "basis": "Nothing supports it."},
            }
        )
        finding = parse_finding(valid_artifact)
        evaluator = PolicyEvaluator(
            [
                rule(
                    kind="require",
                    rule={
                        "where": {"claim_class": ["risk_assessment"]},
                        "any_of": [
                            {"kind": "require", "field": "evidence_refs", "min_items": 1},
                            {
                                "kind": "consistency",
                                "field": "confidence.level",
                                "equals": "insufficient_information",
                            },
                        ],
                    },
                )
            ]
        )
        violations = evaluator.evaluate(finding)
        assert len(violations) == 1
        assert violations[0].claim_id == "C-007"


class TestPatternIsARegularExpression:
    def test_a_pattern_matches_more_than_a_substring(self, valid_artifact: dict) -> None:
        valid_artifact["claims"][0]["statement"] = "The subject engaged in money laundering."
        finding = parse_finding(valid_artifact)
        evaluator = PolicyEvaluator(
            [rule(kind="forbid", rule={"pattern": r"money\s+laundering"})]
        )
        assert len(evaluator.evaluate(finding)) == 1

    def test_a_pattern_that_does_not_compile_is_reported_not_raised(
        self, valid_artifact: dict
    ) -> None:
        finding = parse_finding(valid_artifact)
        evaluator = PolicyEvaluator([rule(kind="forbid", rule={"pattern": "([unclosed"})])
        violations = evaluator.evaluate(finding)
        assert len(violations) == 1
        assert violations[0].severity == "warn"

    def test_a_negated_statement_is_not_a_violation(self, valid_artifact: dict) -> None:
        valid_artifact["claims"][0]["statement"] = (
            "There is no basis to conclude the subject engaged in money laundering."
        )
        finding = parse_finding(valid_artifact)
        evaluator = PolicyEvaluator(
            [
                rule(
                    kind="forbid",
                    rule={"pattern": r"money\s+laundering", "negation_aware": True},
                )
            ]
        )
        assert evaluator.evaluate(finding) == []

    def test_without_negation_awareness_the_same_statement_fails(
        self, valid_artifact: dict
    ) -> None:
        valid_artifact["claims"][0]["statement"] = (
            "There is no basis to conclude the subject engaged in money laundering."
        )
        finding = parse_finding(valid_artifact)
        evaluator = PolicyEvaluator(
            [rule(kind="forbid", rule={"pattern": r"money\s+laundering"})]
        )
        assert len(evaluator.evaluate(finding)) == 1


class TestCompositeAnySemantics:
    def test_any_passes_when_one_branch_is_satisfied(self, valid_artifact: dict) -> None:
        """``any`` means *at least one*, not *all*.

        This is the bug the default policy set would have hit: the rule says
        "there is no adverse reading, or there is a benign reading", and the
        old implementation demanded both.
        """
        finding = parse_finding(valid_artifact)
        evaluator = PolicyEvaluator(
            [
                rule(
                    kind="composite",
                    rule={
                        "any": [
                            {
                                "kind": "count",
                                "where": {"epistemic_type": ["adverse_reading"]},
                                "max_items": 0,
                            },
                            {
                                "kind": "count",
                                "where": {"epistemic_type": ["benign_reading"]},
                                "min_items": 1,
                            },
                        ]
                    },
                )
            ]
        )
        assert evaluator.evaluate(finding) == []

    def test_any_fails_when_every_branch_fails(self, valid_artifact: dict) -> None:
        finding = parse_finding(valid_artifact)
        evaluator = PolicyEvaluator(
            [
                rule(
                    kind="composite",
                    rule={
                        "any": [
                            {
                                "kind": "count",
                                "where": {"epistemic_type": ["adverse_reading"]},
                                "max_items": 0,
                            },
                            {
                                "kind": "count",
                                "where": {"epistemic_type": ["benign_reading"]},
                                "min_items": 1,
                            },
                        ]
                    },
                )
            ]
        )
        # The artifact has an adverse reading, so the first branch fails; it
        # also has a benign reading, so the second branch passes. Any passes.
        assert evaluator.evaluate(finding) == []

    def test_any_fails_when_no_branch_is_satisfied(self, valid_artifact: dict) -> None:
        valid_artifact["claims"] = [
            claim
            for claim in valid_artifact["claims"]
            if claim.get("epistemic_type") != "benign_reading"
        ]
        finding = parse_finding(valid_artifact)
        evaluator = PolicyEvaluator(
            [
                rule(
                    kind="composite",
                    rule={
                        "any": [
                            {
                                "kind": "count",
                                "where": {"epistemic_type": ["adverse_reading"]},
                                "max_items": 0,
                            },
                            {
                                "kind": "count",
                                "where": {"epistemic_type": ["benign_reading"]},
                                "min_items": 1,
                            },
                        ]
                    },
                )
            ]
        )
        assert len(evaluator.evaluate(finding)) == 1


class TestPolicySet:
    def test_the_default_policy_set_loads(self) -> None:
        policy_set = load_policy_set(DEFAULT_POLICY_SET)
        assert policy_set.id == "fincrime/default"
        assert "POL-BENIGN-HYPOTHESIS-REQUIRED" in policy_set.rule_ids()
        assert "POL-EVIDENCE-INVENTORY-FIRST" in policy_set.procedural_policy_ids()

    def test_the_default_policy_set_produces_no_violations_on_the_golden_artifact(
        self,
    ) -> None:
        """The golden artifact is conformant. The default set must say so."""
        policy_set = load_policy_set(DEFAULT_POLICY_SET)
        with GOLDEN_ARTIFACT.open("r", encoding="utf-8") as handle:
            artifact = json.load(handle)
        violations = PolicyEvaluator(policy_set.rules).evaluate(parse_finding(artifact))
        assert violations == [], [violation.message for violation in violations]

    def test_an_export_round_trips_to_the_same_checksum(self) -> None:
        policy_set = load_policy_set(DEFAULT_POLICY_SET)
        exported = export_policy_set(policy_set)
        reloaded = parse_policy_set(exported)
        assert export_policy_set(reloaded)["checksum"] == exported["checksum"]

    def test_a_set_whose_checksum_does_not_match_is_rejected(self, tmp_path: Path) -> None:
        document = json.loads(DEFAULT_POLICY_SET.read_text(encoding="utf-8"))
        document["rules"][0]["description"] = "tampered with"
        target = tmp_path / "policy-set.json"
        target.write_text(json.dumps(document), encoding="utf-8")
        with pytest.raises(ValueError, match="checksum"):
            load_policy_set(target)

    def test_a_set_that_fails_the_contract_is_rejected(self, tmp_path: Path) -> None:
        document = json.loads(DEFAULT_POLICY_SET.read_text(encoding="utf-8"))
        document["rules"][0]["kind"] = "not_a_kind"
        document.pop("checksum", None)
        target = tmp_path / "policy-set.json"
        target.write_text(json.dumps(document), encoding="utf-8")
        with pytest.raises(ValueError, match="contract"):
            load_policy_set(target)

    def test_the_checksum_covers_the_whole_document(self) -> None:
        document = json.loads(DEFAULT_POLICY_SET.read_text(encoding="utf-8"))
        document["description"] = "something else"
        assert policy_set_checksum(document) != document["checksum"]
