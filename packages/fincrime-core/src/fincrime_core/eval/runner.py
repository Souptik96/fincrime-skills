"""The Case Runner Pipeline: executes evaluation suites and scores candidate findings.

Loads evaluation cases, dispatches candidate generation through the selected
provider adapter (ReplayProvider, MockProvider, or ModelProvider), evaluates
outputs with the deterministic scorers, and aggregates results.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from fincrime_core.eval.cases import Case, CaseSuite, load_case_suite
from fincrime_core.eval.metrics import GateEvaluationResult, GateEvaluator, MetricAggregator
from fincrime_core.eval.providers.base import EvaluationProvider
from fincrime_core.eval.scorers import CompoundScorer, ScoreResult
from fincrime_core.validate.validator import EnforcementContext, ValidationResult, Validator

__all__ = [
    "CaseExecutionResult",
    "SuiteExecutionResult",
    "CaseRunnerPipeline",
]


@dataclass(frozen=True, slots=True)
class CaseExecutionResult:
    """The outcome of running and scoring a single evaluation case."""

    case_id: str
    kind: str
    passed: bool
    scores: Mapping[str, ScoreResult]
    defects: tuple[dict[str, Any], ...] = ()
    schema_errors: tuple[dict[str, Any], ...] = ()
    duration_ms: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "kind": self.kind,
            "passed": self.passed,
            "scores": {k: v.to_dict() for k, v in self.scores.items()},
            "defects": list(self.defects),
            "schema_errors": list(self.schema_errors),
            "duration_ms": self.duration_ms,
            "error": self.error,
        }


@dataclass(frozen=True, slots=True)
class SuiteExecutionResult:
    """The aggregate outcome of running an entire evaluation suite."""

    suite_id: str
    skill: str
    case_count: int
    passed_count: int
    case_results: tuple[CaseExecutionResult, ...]
    metrics: Mapping[str, float]
    gate_results: GateEvaluationResult | None = None
    passed_all_gates: bool = True
    duration_ms: float = 0.0

    @property
    def failed_count(self) -> int:
        return self.case_count - self.passed_count

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite_id": self.suite_id,
            "skill": self.skill,
            "case_count": self.case_count,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "passed_all_gates": self.passed_all_gates,
            "metrics": dict(self.metrics),
            "gate_results": self.gate_results.to_dict() if self.gate_results else None,
            "duration_ms": self.duration_ms,
            "cases": [c.to_dict() for c in self.case_results],
        }


class CaseRunnerPipeline:
    """Executes evaluation cases through provider adapters and deterministic scorers."""

    def __init__(
        self,
        provider: EvaluationProvider,
        scorer: CompoundScorer | None = None,
        known_indicator_ids: Sequence[str] | None = None,
        known_knowledge_ids: Sequence[str] | None = None,
        expired_knowledge_ids: Sequence[str] | None = None,
        allowed_jurisdictions: Sequence[str] | None = None,
        policy_evaluator: Any = None,
    ) -> None:
        self.provider = provider
        self.scorer = scorer or CompoundScorer()
        self.known_indicator_ids = list(known_indicator_ids) if known_indicator_ids else None
        self.known_knowledge_ids = list(known_knowledge_ids) if known_knowledge_ids else None
        self.expired_knowledge_ids = list(expired_knowledge_ids) if expired_knowledge_ids else None
        self.allowed_jurisdictions = list(allowed_jurisdictions) if allowed_jurisdictions else ["US"]
        self.policy_evaluator = policy_evaluator

    def run_case(
        self,
        case: Case,
        skill_name: str,
        manifest: Mapping[str, Any] | None = None,
        gate_targets: Mapping[str, float] | None = None,
    ) -> CaseExecutionResult:
        """Run a single case through the candidate provider and scorers."""
        start_time = time.perf_counter()

        try:
            candidate = self.provider.generate_finding(
                skill_name=skill_name,
                case=case,
                manifest=manifest,
            )
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return CaseExecutionResult(
                case_id=case.case_id,
                kind=case.kind,
                passed=False,
                scores={},
                error=f"Candidate generation failed: {exc}",
                duration_ms=duration_ms,
            )

        inline_input = case.document.get("input", {}).get("inline", {})
        evidence_set = dict(inline_input.get("evidence_set", {}))
        if "subject_scope" not in evidence_set and "subject_scope" in inline_input:
            evidence_set["subject_scope"] = inline_input["subject_scope"]
        if "subject" not in evidence_set and "subject" in inline_input:
            evidence_set["subject"] = inline_input["subject"]
        if "alert" not in evidence_set and "alert" in inline_input:
            evidence_set["alert"] = inline_input["alert"]

        validator = Validator(
            evidence_set=evidence_set,
            known_indicator_ids=self.known_indicator_ids,
            known_knowledge_ids=self.known_knowledge_ids,
            expired_knowledge_ids=self.expired_knowledge_ids,
            allowed_jurisdictions=self.allowed_jurisdictions,
        )

        val_result = validator.validate(
            candidate, EnforcementContext(EnforcementContext.PROMOTION)
        )

        scores = self.scorer.score_all(
            candidate=candidate,
            case=case,
            manifest=manifest,
            validation_result=val_result,
            gate_targets=gate_targets,
            known_indicator_ids=self.known_indicator_ids,
            known_knowledge_ids=self.known_knowledge_ids,
            expired_knowledge_ids=self.expired_knowledge_ids,
            allowed_jurisdictions=self.allowed_jurisdictions,
            policy_evaluator=self.policy_evaluator,
        )

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        passed = all(s.passed for s in scores.values())

        return CaseExecutionResult(
            case_id=case.case_id,
            kind=case.kind,
            passed=passed,
            scores=scores,
            defects=tuple(d.to_dict() for d in val_result.defects),
            schema_errors=tuple(
                {"path": e.path, "message": e.message, "keyword": e.keyword}
                for e in val_result.schema_errors
            ),
            duration_ms=duration_ms,
        )

    def run_suite(
        self,
        suite: CaseSuite | str | Path,
        manifest: Mapping[str, Any] | None = None,
        gates: Mapping[str, float] | None = None,
    ) -> SuiteExecutionResult:
        """Run all cases in a suite and aggregate metrics and gate evaluations."""
        suite_obj: CaseSuite
        if isinstance(suite, (str, Path)):
            loaded_suite, findings = load_case_suite(suite)
            if any(f.severity == "error" for f in findings):
                err_msgs = [f.message for f in findings if f.severity == "error"]
                raise ValueError(f"Failed to load suite from {suite}: {'; '.join(err_msgs)}")
            suite_obj = loaded_suite
        else:
            suite_obj = suite

        skill_name = suite_obj.skill or (manifest.get("metadata", {}).get("name") if manifest else "")

        # Extract declared gates if not explicitly supplied
        effective_gates = dict(gates) if gates is not None else {}
        if not effective_gates and manifest:
            declared = manifest.get("spec", {}).get("evaluation", {}).get("gates")
            if isinstance(declared, Mapping):
                effective_gates = {str(k): float(v) for k, v in declared.items()}

        start_time = time.perf_counter()
        case_results: list[CaseExecutionResult] = []

        for case in suite_obj.cases:
            res = self.run_case(
                case=case,
                skill_name=skill_name,
                manifest=manifest,
                gate_targets=effective_gates,
            )
            case_results.append(res)

        total_duration_ms = (time.perf_counter() - start_time) * 1000.0

        scores_list = [c.scores for c in case_results if not c.error]
        kinds_list = [c.kind for c in case_results]
        aggregated_metrics = MetricAggregator.aggregate(scores_list, kinds_list)

        gate_results: GateEvaluationResult | None = None
        passed_all_gates = True
        if effective_gates:
            gate_results = GateEvaluator.evaluate(aggregated_metrics, effective_gates)
            passed_all_gates = gate_results.passed

        passed_count = sum(1 for c in case_results if c.passed)

        return SuiteExecutionResult(
            suite_id=suite_obj.suite_id,
            skill=skill_name,
            case_count=len(case_results),
            passed_count=passed_count,
            case_results=tuple(case_results),
            metrics=aggregated_metrics,
            gate_results=gate_results,
            passed_all_gates=passed_all_gates,
            duration_ms=total_duration_ms,
        )
