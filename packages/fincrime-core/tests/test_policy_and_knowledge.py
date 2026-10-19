"""Tests for the deterministic policy evaluator and the knowledge engine."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from fincrime_core.contract.loader import parse_finding
from fincrime_core.knowledge.model import KnowledgeIndex, KnowledgeRecord, parse_record
from fincrime_core.policy.evaluator import PolicyEvaluator, PolicyRule

CONTRACTS = Path(__file__).resolve().parents[3] / "contracts"


def rule(**kwargs) -> PolicyRule:
    base = {
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
    )


class TestPolicyEvaluator:
    def test_count_rule_fires_when_below_minimum(self, valid_artifact: dict) -> None:
        finding = parse_finding(valid_artifact)
        evaluator = PolicyEvaluator(
            [rule(kind="count", rule={"where": {"claim_class": ["hypothesis"]}, "min_items": 5})]
        )
        violations = evaluator.evaluate(finding)
        assert len(violations) == 1
        assert violations[0].rule_id == "POL-TEST"

    def test_count_rule_passes_when_satisfied(self, valid_artifact: dict) -> None:
        finding = parse_finding(valid_artifact)
        evaluator = PolicyEvaluator(
            [rule(kind="count", rule={"where": {"claim_class": ["hypothesis"]}, "min_items": 2})]
        )
        assert evaluator.evaluate(finding) == []

    def test_where_filter_selects_claims(self, valid_artifact: dict) -> None:
        finding = parse_finding(valid_artifact)
        evaluator = PolicyEvaluator(
            [
                rule(
                    kind="count",
                    rule={"where": {"epistemic_type": ["benign_reading"]}, "min_items": 1},
                )
            ]
        )
        assert evaluator.evaluate(finding) == []

    def test_composite_all_requires_every_branch(self, valid_artifact: dict) -> None:
        finding = parse_finding(valid_artifact)
        evaluator = PolicyEvaluator(
            [
                rule(
                    kind="composite",
                    rule={
                        "all": [
                            {"kind": "count", "where": {"claim_class": ["hypothesis"]}, "min_items": 2},
                            {"kind": "count", "where": {"epistemic_type": ["benign_reading"]}, "min_items": 1},
                        ]
                    },
                )
            ]
        )
        assert evaluator.evaluate(finding) == []

    def test_composite_all_reports_when_a_branch_fails(self, valid_artifact: dict) -> None:
        finding = parse_finding(valid_artifact)
        evaluator = PolicyEvaluator(
            [
                rule(
                    kind="composite",
                    rule={
                        "all": [
                            {"kind": "count", "where": {"claim_class": ["hypothesis"]}, "min_items": 2},
                            {"kind": "count", "where": {"epistemic_type": ["benign_reading"]}, "min_items": 5},
                        ]
                    },
                )
            ]
        )
        assert len(evaluator.evaluate(finding)) == 1

    def test_require_rule_checks_a_field(self, valid_artifact: dict) -> None:
        finding = parse_finding(valid_artifact)
        evaluator = PolicyEvaluator(
            [rule(kind="require", rule={"where": {"claim_class": ["hypothesis"]}, "field": "falsifier", "min_items": 1})]
        )
        assert evaluator.evaluate(finding) == []

    def test_jurisdiction_scoping_skips_a_non_matching_rule(self, valid_artifact: dict) -> None:
        finding = parse_finding(valid_artifact)
        evaluator = PolicyEvaluator(
            [
                rule(
                    kind="count",
                    rule={"where": {"claim_class": ["hypothesis"]}, "min_items": 99},
                    jurisdictions=["GB"],
                )
            ]
        )
        assert evaluator.evaluate(finding) == []

    def test_evaluation_is_deterministic(self, valid_artifact: dict) -> None:
        finding = parse_finding(valid_artifact)
        evaluator = PolicyEvaluator(
            [rule(kind="count", rule={"where": {"claim_class": ["hypothesis"]}, "min_items": 9})]
        )
        first = evaluator.evaluate(finding)
        second = evaluator.evaluate(finding)
        assert [v.sort_key() for v in first] == [v.sort_key() for v in second]

    def test_an_unknown_rule_kind_is_ignored_not_fatal(self, valid_artifact: dict) -> None:
        finding = parse_finding(valid_artifact)
        evaluator = PolicyEvaluator([rule(kind="not_a_kind")])
        assert evaluator.evaluate(finding) == []


class TestKnowledgeEngine:
    def _record(self, **overrides) -> KnowledgeRecord:
        raw = {
            "id": "IND-TEST",
            "type": "indicator",
            "pack": "core-2026-10",
            "version": "1.0.0",
            "title": "Test indicator",
            "definition": "A test indicator.",
            "jurisdictions": ["US"],
            "sources": [{"citation": "Test source"}],
            "as_of": "2026-01-01",
            "review_by": "2026-04-01",
            "expires_at": "2026-04-01",
            "status": "active",
            "maintainer": "@owner",
            "prohibited_attributes": ["nationality"],
            "benign_explanations": ["A benign explanation."],
        }
        raw.update(overrides)
        return parse_record(raw)

    def test_expiry_is_evaluated_against_a_supplied_date(self) -> None:
        record = self._record()
        assert not record.is_expired(date(2026, 3, 1))
        assert record.is_expired(date(2026, 5, 1))

    def test_review_due_is_distinct_from_expired(self) -> None:
        record = self._record(review_by="2026-02-01", expires_at="2026-12-01")
        assert record.is_review_due(date(2026, 3, 1))
        assert not record.is_expired(date(2026, 3, 1))

    def test_index_reports_expired_and_review_due(self) -> None:
        index = KnowledgeIndex(
            [
                self._record(id="IND-EXPIRED", expires_at="2026-01-01", review_by="2026-01-01"),
                self._record(id="IND-REVIEW", expires_at="2026-12-01", review_by="2026-02-01"),
            ]
        )
        status = index.expiry_status(date(2026, 3, 1))
        assert status.expired_ids == ("IND-EXPIRED",)
        assert status.review_due_ids == ("IND-REVIEW",)

    def test_deprecation_due_after_the_grace_period(self) -> None:
        record = self._record(expires_at="2026-01-01", review_by="2026-01-01")
        assert not record.is_deprecation_due(date(2026, 3, 1))
        assert record.is_deprecation_due(date(2026, 12, 1))

    def test_indicator_ids_are_indexed(self) -> None:
        index = KnowledgeIndex([self._record()])
        assert index.indicator_ids() == ("IND-TEST",)


class TestContractCoverage:
    def test_defect_taxonomy_covers_every_code_used_by_the_linter(self) -> None:
        from fincrime_core.validate.defects import DEFECT_CODES, load_defect_taxonomy

        taxonomy = load_defect_taxonomy()
        for code in DEFECT_CODES:
            assert code in taxonomy, f"defect code {code!r} is missing from the taxonomy"

    def test_defect_taxonomy_distinguishes_structural_from_heuristic(self) -> None:
        from fincrime_core.validate.defects import load_defect_taxonomy

        taxonomy = load_defect_taxonomy()
        for info in taxonomy.values():
            assert info.enforcement in ("structural", "graded", "heuristic")
            if info.is_structural:
                assert info.severity == "error", f"{info.code} is structural and must be an error"
            if info.is_graded:
                assert info.severity == "warn", f"{info.code} is graded and defaults to a warning"
            if info.is_heuristic:
                assert info.severity == "warn", f"{info.code} is heuristic and must be a warning"

    def test_expired_knowledge_is_graded_not_structural(self) -> None:
        """ADR-0006: expiry enforcement is graduated by change type."""
        from fincrime_core.validate.defects import load_defect_taxonomy

        taxonomy = load_defect_taxonomy()
        assert taxonomy["expired_knowledge_citation"].is_graded

    def test_policy_rule_schema_loads(self) -> None:
        with (CONTRACTS / "policy-rule.schema.json").open("r", encoding="utf-8") as handle:
            schema = json.load(handle)
        assert schema["$defs"]["ruleBody"]["properties"]["all"]
