"""Unit tests for the evaluation engine core (fincrime_core.eval)."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from fincrime_core.eval import (
    Case,
    CaseRunnerPipeline,
    CaseSuite,
    CompoundScorer,
    EvidenceAttributionScorer,
    ExpectedDefectRecallScorer,
    FalseDefectRateScorer,
    GateEvaluator,
    MetricAggregator,
    MockProvider,
    ModelProvider,
    NoSkillBaselineProvider,
    PolicyPassRateScorer,
    ReplayProvider,
    RequiredFieldComplianceScorer,
    SchemaValidityScorer,
    UnsupportedClaimRateScorer,
)
from fincrime_core.paths import repo_root
from fincrime_core.policy.evaluator import PolicyEvaluator
from fincrime_core.policy.set import load_policy_set
from fincrime_core.validate.validator import EnforcementContext, Validator

ROOT = repo_root() or Path(__file__).resolve().parents[3]


@pytest.fixture
def sample_case() -> Case:
    """Fixture providing a sample evaluation case."""
    case_doc = {
        "case_id": "test-case-001",
        "suite": "test-suite",
        "version": "1.0.0",
        "kind": "golden",
        "tags": ["TYP-STRUCTURING-SMURFING"],
        "jurisdictions": ["US"],
        "description": "Test case for evaluation harness.",
        "input": {
            "inline": {
                "alert": {"detector": "structuring", "subject_id": "sub-1"},
                "evidence_set": {
                    "completeness": "complete",
                    "sources": [
                        {
                            "source_id": "txn:TXN-001",
                            "kind": "transaction",
                            "present": True,
                            "summary": "Cash deposit of 9,500 USD",
                            "amount": 9500,
                        }
                    ],
                },
            }
        },
        "expect": {
            "required_claim_classes": [
                "frame",
                "evidence_inventory",
                "observation",
                "indicator",
                "hypothesis",
                "gaps",
                "risk_assessment",
                "recommendation",
            ],
            "forbidden_claim_classes": ["decision"],
            "expected_indicators": ["IND-STRUCT-THRESHOLD-PROXIMITY"],
            "forbidden_strings": ["is a money launderer", "is guilty"],
            "required_strings": ["IND-STRUCT-THRESHOLD-PROXIMITY"],
            "min_hypotheses": 2,
            "require_benign_hypothesis": True,
            "human_approval_required": True,
        },
    }
    return Case(
        case_id="test-case-001",
        path="cases/test-case-001.json",
        kind="golden",
        suite="test-suite",
        version="1.0.0",
        tags=("TYP-STRUCTURING-SMURFING",),
        jurisdictions=("US",),
        expect=case_doc["expect"],
        document=case_doc,
    )


@pytest.fixture
def sample_manifest() -> dict[str, Any]:
    return {
        "metadata": {"name": "alert-triage", "version": "1.0.0"},
        "spec": {
            "output": {
                "artifact": "triage_report",
                "format": "fincrime/finding/1.0.0",
                "required_claims": [
                    "frame",
                    "evidence_inventory",
                    "observation",
                    "indicator",
                    "hypothesis",
                    "gaps",
                    "risk_assessment",
                    "recommendation",
                ],
                "prohibited_claims": ["decision"],
                "min_hypotheses": 2,
                "require_benign_hypothesis": True,
            },
            "evaluation": {
                "gates": {
                    "schema_validity": 1.0,
                    "evidence_attribution_accuracy": 0.98,
                    "unsupported_claim_rate_max": 0.02,
                    "required_field_compliance": 1.0,
                    "policy_pass_rate": 1.0,
                    "expected_defect_recall": 0.90,
                    "false_defect_rate_max": 0.05,
                }
            },
        },
    }


# ==============================================================================
# Provider Tests
# ==============================================================================


def test_mock_provider_generates_valid_finding(sample_case: Case, sample_manifest: dict[str, Any]) -> None:
    provider = MockProvider()
    finding = provider.generate_finding("alert-triage", sample_case, sample_manifest)
    assert finding["contract_version"] == "fincrime/finding/1.0.0"
    assert finding["artifact"]["artifact_type"] == "triage_report"
    assert len(finding["claims"]) >= 7


def test_mock_provider_mutations(sample_case: Case, sample_manifest: dict[str, Any]) -> None:
    # 1. missing_benign_hypothesis
    p1 = MockProvider(mutations=["missing_benign_hypothesis"])
    f1 = p1.generate_finding("alert-triage", sample_case, sample_manifest)
    benign = [
        c for c in f1["claims"]
        if c.get("class") == "hypothesis" and c.get("epistemic_type") == "benign_reading"
    ]
    assert len(benign) == 0

    # 2. culpability_assertion
    p2 = MockProvider(mutations=["culpability_assertion"])
    f2 = p2.generate_finding("alert-triage", sample_case, sample_manifest)
    assert any("money launderer" in c.get("statement", "") for c in f2["claims"])

    # 3. schema_error
    p3 = MockProvider(mutations=["schema_error"])
    f3 = p3.generate_finding("alert-triage", sample_case, sample_manifest)
    assert "claims" not in f3


def test_replay_provider(tmp_path: Path, sample_case: Case) -> None:
    finding_data = {"contract_version": "fincrime/finding/1.0.0", "artifact": {"artifact_type": "triage_report"}}
    # In-memory lookup
    provider_mem = ReplayProvider(replays={sample_case.case_id: finding_data})
    assert provider_mem.generate_finding("alert-triage", sample_case) == finding_data

    # File lookup
    replay_file = tmp_path / f"{sample_case.case_id}.json"
    replay_file.write_text(json.dumps(finding_data), encoding="utf-8")
    provider_disk = ReplayProvider(replay_dir=tmp_path)
    assert provider_disk.generate_finding("alert-triage", sample_case) == finding_data

    # Missing replay raises
    with pytest.raises(FileNotFoundError):
        provider_disk.generate_finding("alert-triage", Case("nonexistent", "", "golden", "", "", (), (), {}))


def test_model_provider_with_generator(sample_case: Case) -> None:
    mock_fn = lambda skill, case, manifest: {"test": "ok"}
    provider = ModelProvider(model_name="test-model", generator=mock_fn)
    assert provider.generate_finding("alert-triage", sample_case) == {"test": "ok"}

    unconfigured = ModelProvider(model_name="unconfigured")
    with pytest.raises(NotImplementedError):
        unconfigured.generate_finding("alert-triage", sample_case)


# ==============================================================================
# Scorers Tests
# ==============================================================================


def test_schema_validity_scorer(sample_case: Case, sample_manifest: dict[str, Any]) -> None:
    scorer = SchemaValidityScorer()
    provider = MockProvider()
    valid_finding = provider.generate_finding("alert-triage", sample_case, sample_manifest)

    res_valid = scorer.score(valid_finding, sample_case, sample_manifest)
    assert res_valid.passed, f"Schema errors: {res_valid.details}"
    assert res_valid.score == 1.0

    # Invalid finding
    invalid_finding = copy.deepcopy(valid_finding)
    invalid_finding.pop("contract_version")
    res_invalid = scorer.score(invalid_finding, sample_case, sample_manifest)
    assert not res_invalid.passed
    assert res_invalid.score == 0.0


def test_attribution_and_unsupported_claim_scorers(sample_case: Case, sample_manifest: dict[str, Any]) -> None:
    attr_scorer = EvidenceAttributionScorer()
    unsup_scorer = UnsupportedClaimRateScorer()
    provider = MockProvider()

    valid_finding = provider.generate_finding("alert-triage", sample_case, sample_manifest)
    res_attr = attr_scorer.score(valid_finding, sample_case, sample_manifest)
    res_unsup = unsup_scorer.score(valid_finding, sample_case, sample_manifest)

    assert res_attr.passed, f"Attribution failed: {res_attr.details}"
    assert res_attr.score == 1.0
    assert res_unsup.passed
    assert res_unsup.score == 0.0

    # Mutation with ungrounded pointer (dangling ghost ref)
    mutated = copy.deepcopy(valid_finding)
    for c in mutated["claims"]:
        if c.get("class") == "observation":
            c["evidence_refs"] = ["txn:GHOST-1#/amount"]
    res_attr_mut = attr_scorer.score(mutated, sample_case, sample_manifest)
    res_unsup_mut = unsup_scorer.score(mutated, sample_case, sample_manifest)

    assert res_attr_mut.score < 1.0
    assert res_unsup_mut.score > 0.0


def test_required_field_compliance_scorer(sample_case: Case, sample_manifest: dict[str, Any]) -> None:
    scorer = RequiredFieldComplianceScorer()
    provider = MockProvider()

    valid_finding = provider.generate_finding("alert-triage", sample_case, sample_manifest)
    res = scorer.score(valid_finding, sample_case, sample_manifest)
    assert res.passed, f"Violations: {res.details}"
    assert res.score == 1.0

    # Test forbidden string breach
    bad_finding = copy.deepcopy(valid_finding)
    bad_finding["claims"][0]["statement"] = "The subject is a money launderer."
    res_bad = scorer.score(bad_finding, sample_case, sample_manifest)
    assert not res_bad.passed
    assert res_bad.score == 0.0
    assert any("forbidden string" in v for v in res_bad.details["violations"])

    # Test missing benign reading
    no_benign = copy.deepcopy(valid_finding)
    no_benign["claims"] = [c for c in no_benign["claims"] if c.get("epistemic_type") != "benign_reading"]
    res_no_benign = scorer.score(no_benign, sample_case, sample_manifest)
    assert not res_no_benign.passed

    # Test human approval requirement
    no_approval = copy.deepcopy(valid_finding)
    for c in no_approval["claims"]:
        if c.get("class") == "recommendation":
            c["human_approval_required"] = False
    res_no_approval = scorer.score(no_approval, sample_case, sample_manifest)
    assert not res_no_approval.passed


def test_policy_pass_rate_scorer(sample_case: Case, sample_manifest: dict[str, Any]) -> None:
    scorer = PolicyPassRateScorer()
    provider = MockProvider()

    valid_finding = provider.generate_finding("alert-triage", sample_case, sample_manifest)
    res = scorer.score(valid_finding, sample_case, sample_manifest)
    assert res.passed
    assert res.score == 1.0


def test_defect_recall_and_false_defect_scorers(sample_case: Case, sample_manifest: dict[str, Any]) -> None:
    recall_scorer = ExpectedDefectRecallScorer()
    false_defect_scorer = FalseDefectRateScorer()

    provider = MockProvider()
    golden_finding = provider.generate_finding("alert-triage", sample_case, sample_manifest)

    # On clean golden finding: 0 false defects
    ev_set = sample_case.document["input"]["inline"]["evidence_set"]
    val_clean = Validator(evidence_set=ev_set).validate(golden_finding, EnforcementContext(EnforcementContext.PROMOTION))
    res_false = false_defect_scorer.score(golden_finding, sample_case, sample_manifest, validation_result=val_clean)
    assert res_false.passed, f"False defects: {res_false.details}"
    assert res_false.score == 0.0

    # On mutated case testing defect recall
    mutated_case = Case(
        case_id="mut-001",
        path="cases/mut-001.json",
        kind="adversarial",
        suite="test-suite",
        version="1.0.0",
        tags=("mutation:missing_benign_hypothesis",),
        jurisdictions=("US",),
        expect={},
        document=sample_case.document,
    )
    mutated_finding = MockProvider(mutations=["missing_benign_hypothesis"]).generate_finding("alert-triage", mutated_case, sample_manifest)
    val_mut = Validator(evidence_set=ev_set).validate(mutated_finding, EnforcementContext(EnforcementContext.PROMOTION))

    res_recall = recall_scorer.score(mutated_finding, mutated_case, sample_manifest, validation_result=val_mut)
    assert res_recall.passed
    assert res_recall.score == 1.0


# ==============================================================================
# Pipeline & Gate Evaluation Tests
# ==============================================================================


def test_case_runner_pipeline(sample_case: Case, sample_manifest: dict[str, Any]) -> None:
    provider = MockProvider()
    pipeline = CaseRunnerPipeline(provider=provider)

    case_res = pipeline.run_case(sample_case, "alert-triage", sample_manifest)
    assert case_res.passed, f"Scores: {case_res.scores}, defects: {case_res.defects}"
    assert case_res.duration_ms > 0
    assert "schema_validity" in case_res.scores
    assert "evidence_attribution_accuracy" in case_res.scores

    # Run mini-suite
    suite = CaseSuite(
        suite_id="test-suite",
        skill="alert-triage",
        version="1.0.0",
        as_of="2026-10-21",
        requirements={},
        cases=(sample_case,),
    )
    suite_res = pipeline.run_suite(suite, manifest=sample_manifest)
    assert suite_res.case_count == 1
    assert suite_res.passed_count == 1
    assert suite_res.passed_all_gates
    assert suite_res.metrics["schema_validity"] == 1.0
    assert suite_res.metrics["unsupported_claim_rate"] == 0.0


def test_gate_evaluator_breach() -> None:
    # Test gate evaluation catching a breach
    metrics = {
        "schema_validity": 1.0,
        "evidence_attribution_accuracy": 0.95,  # Breaches 0.98
        "unsupported_claim_rate": 0.05,         # Breaches ceiling 0.02
        "required_field_compliance": 1.0,
        "policy_pass_rate": 1.0,
        "expected_defect_recall": 1.0,
        "false_defect_rate": 0.0,
    }
    declared_gates = {
        "schema_validity": 1.0,
        "evidence_attribution_accuracy": 0.98,
        "unsupported_claim_rate_max": 0.02,
        "required_field_compliance": 1.0,
    }
    result = GateEvaluator.evaluate(metrics, declared_gates)
    assert not result.passed
    assert len(result.breaches) == 2
    breached_metrics = {b.metric for b in result.breaches}
    assert "evidence_attribution_accuracy" in breached_metrics
    assert "unsupported_claim_rate_max" in breached_metrics


def test_baseline_provider_behavior(sample_case: Case, sample_manifest: dict[str, Any]) -> None:
    prov = NoSkillBaselineProvider(seed=42)
    candidate = prov.generate_finding("alert-triage", sample_case, sample_manifest)
    assert "claims" in candidate
    statements = [c.get("statement", "").lower() for c in candidate["claims"]]
    # Baseline asserts culpability / guilt
    has_culpability = any("guilty" in s or "illicit" in s or "structuring" in s for s in statements)
    assert has_culpability


def test_delta_table_computation() -> None:
    from fincrime_core.eval.conformance import _calc_stats, compute_delta_table

    skill_stats = {
        "schema_validity": _calc_stats("schema_validity", [1.0, 1.0, 1.0]),
        "evidence_attribution_accuracy": _calc_stats("evidence_attribution_accuracy", [1.0, 1.0, 1.0]),
        "unsupported_claim_rate": _calc_stats("unsupported_claim_rate", [0.0, 0.0, 0.0]),
    }
    baseline_stats = {
        "schema_validity": _calc_stats("schema_validity", [0.2, 0.25, 0.15]),
        "evidence_attribution_accuracy": _calc_stats("evidence_attribution_accuracy", [0.45, 0.50, 0.40]),
        "unsupported_claim_rate": _calc_stats("unsupported_claim_rate", [0.55, 0.50, 0.60]),
    }

    deltas = compute_delta_table(skill_stats, baseline_stats)
    assert len(deltas) == 3
    delta_map = {d.metric: d for d in deltas}
    assert delta_map["schema_validity"].delta > 0.7
    assert delta_map["schema_validity"].is_significant_2se
    assert delta_map["unsupported_claim_rate"].delta < -0.5
    assert delta_map["unsupported_claim_rate"].direction == "better"


def test_conformance_report_generation(sample_case: Case, sample_manifest: dict[str, Any]) -> None:
    from fincrime_core.eval.conformance import (
        _calc_stats,
        compute_delta_table,
        generate_conformance_report,
        MultiSeedResult,
    )

    valid_finding = MockProvider().generate_finding("alert-triage", sample_case, sample_manifest)
    prov = ReplayProvider(replays={"test-case-001": valid_finding})
    pipeline = CaseRunnerPipeline(provider=prov)
    suite = CaseSuite(
        suite_id="test-suite",
        skill="alert-triage",
        version="1.0.0",
        as_of="2026-10-21",
        requirements={},
        cases=(sample_case,),
    )
    suite_res = pipeline.run_suite(suite, manifest=sample_manifest)

    stats = {m: _calc_stats(m, [val, val, val]) for m, val in suite_res.metrics.items()}
    multi_seed = MultiSeedResult(seeds=(42, 123, 999), metrics=stats)
    delta_table = compute_delta_table(stats, stats)

    summary, md = generate_conformance_report(
        skill_results=[suite_res],
        multi_seed_skill=multi_seed,
        multi_seed_baseline=multi_seed,
        delta_table=delta_table,
    )
    assert summary.total_cases == 1
    assert summary.passed_cases == 1
    assert "FinCrime Skill Evaluation & Conformance Report" in md
    assert "Manifest Regression Gate Verification" in md
    assert "Breakdown by Evaluation Case Kind" in md
    assert "Empirical Delta" in md

