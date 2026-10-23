"""Evaluation engine: case suite loader, providers, deterministic scorers, and runner pipeline."""

from __future__ import annotations

from fincrime_core.eval.cases import (
    DEFAULT_REQUIREMENTS,
    MIXED_CASE_KINDS,
    Case,
    CaseSuite,
    SuiteFinding,
    SuiteValidationResult,
    load_case_schema,
    load_case_suite,
    load_case_suite_schema,
    validate_case_suite,
)
from fincrime_core.eval.metrics import (
    GATE_TYPES,
    GateBreach,
    GateEvaluationResult,
    GateEvaluator,
    MetricAggregator,
    normalize_gate_name,
)
from fincrime_core.eval.conformance import (
    ConformanceSummary,
    DeltaItem,
    MetricStats,
    MultiSeedResult,
    compute_delta_table,
    generate_conformance_report,
    run_multi_seed_evaluation,
)
from fincrime_core.eval.providers import (
    BUILTIN_MUTATIONS,
    EvaluationProvider,
    MockProvider,
    ModelProvider,
    NoSkillBaselineProvider,
    ReplayProvider,
)
from fincrime_core.eval.runner import (
    CaseExecutionResult,
    CaseRunnerPipeline,
    SuiteExecutionResult,
)
from fincrime_core.eval.scorers import (
    CompoundScorer,
    EvidenceAttributionScorer,
    ExpectedDefectRecallScorer,
    FalseDefectRateScorer,
    PolicyPassRateScorer,
    RequiredFieldComplianceScorer,
    SchemaValidityScorer,
    ScoreResult,
    Scorer,
    UnsupportedClaimRateScorer,
    default_scorers,
)

__all__ = [
    # Cases
    "Case",
    "CaseSuite",
    "DEFAULT_REQUIREMENTS",
    "MIXED_CASE_KINDS",
    "SuiteFinding",
    "SuiteValidationResult",
    "load_case_schema",
    "load_case_suite",
    "load_case_suite_schema",
    "validate_case_suite",
    # Providers
    "EvaluationProvider",
    "ReplayProvider",
    "MockProvider",
    "ModelProvider",
    "NoSkillBaselineProvider",
    "BUILTIN_MUTATIONS",
    # Scorers
    "Scorer",
    "ScoreResult",
    "SchemaValidityScorer",
    "EvidenceAttributionScorer",
    "UnsupportedClaimRateScorer",
    "RequiredFieldComplianceScorer",
    "PolicyPassRateScorer",
    "ExpectedDefectRecallScorer",
    "FalseDefectRateScorer",
    "CompoundScorer",
    "default_scorers",
    # Metrics & Gates
    "GATE_TYPES",
    "normalize_gate_name",
    "GateBreach",
    "GateEvaluationResult",
    "GateEvaluator",
    "MetricAggregator",
    # Runner
    "CaseExecutionResult",
    "SuiteExecutionResult",
    "CaseRunnerPipeline",
    # Conformance & Benchmark
    "MetricStats",
    "MultiSeedResult",
    "DeltaItem",
    "ConformanceSummary",
    "run_multi_seed_evaluation",
    "compute_delta_table",
    "generate_conformance_report",
]
