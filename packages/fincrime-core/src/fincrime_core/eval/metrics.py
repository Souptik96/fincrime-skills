"""Metric aggregation and gate evaluation for evaluation suites.

Aggregates deterministic scores across evaluation suites and evaluates
candidate runs against the thresholds declared in each skill manifest's
`evaluation.gates`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from fincrime_core.eval.scorers.base import ScoreResult

__all__ = [
    "MetricAggregator",
    "GateBreach",
    "GateEvaluationResult",
    "GateEvaluator",
    "normalize_gate_name",
    "GATE_TYPES",
]

#: Mapping of gate metric names to their comparison mode: 'min' or 'max'
GATE_TYPES: dict[str, str] = {
    "schema_validity": "min",
    "evidence_attribution_accuracy": "min",
    "unsupported_claim_rate": "max",
    "unsupported_claim_rate_max": "max",
    "required_field_compliance": "min",
    "policy_pass_rate": "min",
    "expected_defect_recall": "min",
    "false_defect_rate": "max",
    "false_defect_rate_max": "max",
}


def normalize_gate_name(name: str) -> str:
    """Normalize aliases like unsupported_claim_rate_max to canonical metric names."""
    if name == "unsupported_claim_rate_max":
        return "unsupported_claim_rate"
    if name == "false_defect_rate_max":
        return "false_defect_rate"
    return name


@dataclass(frozen=True, slots=True)
class GateBreach:
    """A single threshold breach in gate evaluation."""

    metric: str
    target: float
    actual: float
    gate_type: str  # "min" or "max"
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "target": self.target,
            "actual": self.actual,
            "gate_type": self.gate_type,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class GateEvaluationResult:
    """The outcome of evaluating suite metrics against gate thresholds."""

    passed: bool
    breaches: tuple[GateBreach, ...] = ()
    gate_details: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "breach_count": len(self.breaches),
            "breaches": [b.to_dict() for b in self.breaches],
            "gate_details": dict(self.gate_details),
        }


class MetricAggregator:
    """Aggregates per-case scores into suite-level metrics."""

    @staticmethod
    def aggregate(
        case_scores: Sequence[Mapping[str, ScoreResult]],
        case_kinds: Sequence[str] | None = None,
    ) -> dict[str, float]:
        """Aggregate per-case scores into overall suite metrics.

        Args:
            case_scores: List of dicts mapping metric name to ScoreResult for each case.
            case_kinds: Optional list of case kind strings matching case_scores length.

        Returns:
            Dictionary of canonical metric names mapped to their aggregated float score.
        """
        if not case_scores:
            return {
                "schema_validity": 0.0,
                "evidence_attribution_accuracy": 0.0,
                "unsupported_claim_rate": 0.0,
                "required_field_compliance": 0.0,
                "policy_pass_rate": 0.0,
                "expected_defect_recall": 1.0,
                "false_defect_rate": 0.0,
            }

        total_cases = len(case_scores)
        sum_schema = sum(res["schema_validity"].score for res in case_scores if "schema_validity" in res)
        sum_attr = sum(res["evidence_attribution_accuracy"].score for res in case_scores if "evidence_attribution_accuracy" in res)
        sum_unsupported = sum(res["unsupported_claim_rate"].score for res in case_scores if "unsupported_claim_rate" in res)
        sum_compliance = sum(res["required_field_compliance"].score for res in case_scores if "required_field_compliance" in res)
        sum_policy = sum(res["policy_pass_rate"].score for res in case_scores if "policy_pass_rate" in res)

        # Expected defect recall: average over cases that actually test expected defects
        defect_cases = [
            res["expected_defect_recall"].score
            for res in case_scores
            if "expected_defect_recall" in res
            and res["expected_defect_recall"].details.get("status") != "no_expected_defects"
        ]
        avg_defect_recall = sum(defect_cases) / len(defect_cases) if defect_cases else 1.0

        # False defect rate: average over golden reference cases
        golden_cases = [
            res["false_defect_rate"].score
            for res in case_scores
            if "false_defect_rate" in res
            and res["false_defect_rate"].details.get("status") != "not_golden_case"
        ]
        avg_false_defect_rate = sum(golden_cases) / len(golden_cases) if golden_cases else 0.0

        return {
            "schema_validity": sum_schema / total_cases,
            "evidence_attribution_accuracy": sum_attr / total_cases,
            "unsupported_claim_rate": sum_unsupported / total_cases,
            "required_field_compliance": sum_compliance / total_cases,
            "policy_pass_rate": sum_policy / total_cases,
            "expected_defect_recall": avg_defect_recall,
            "false_defect_rate": avg_false_defect_rate,
        }


class GateEvaluator:
    """Compares suite-level metrics against declared gate thresholds."""

    @staticmethod
    def evaluate(
        metrics: Mapping[str, float],
        declared_gates: Mapping[str, float],
    ) -> GateEvaluationResult:
        """Evaluate aggregated metrics against manifest gates.

        Args:
            metrics: Suite-level metrics from MetricAggregator.
            declared_gates: Gate thresholds from manifest (e.g., manifest.spec.evaluation.gates).

        Returns:
            GateEvaluationResult recording overall pass status and breach details.
        """
        breaches: list[GateBreach] = []
        details: dict[str, Any] = {}

        for raw_name, target in declared_gates.items():
            canonical_name = normalize_gate_name(raw_name)
            gate_type = GATE_TYPES.get(raw_name, GATE_TYPES.get(canonical_name, "min"))
            actual = float(metrics.get(canonical_name, 0.0))

            passed = False
            if gate_type == "max":
                passed = actual <= target
                msg = (
                    f"Gate {raw_name} passed ({actual:.4f} <= {target:.4f})"
                    if passed
                    else f"Gate {raw_name} BREACHED: {actual:.4f} exceeds ceiling {target:.4f}"
                )
            else:
                passed = actual >= target
                msg = (
                    f"Gate {raw_name} passed ({actual:.4f} >= {target:.4f})"
                    if passed
                    else f"Gate {raw_name} BREACHED: {actual:.4f} fell below floor {target:.4f}"
                )

            details[raw_name] = {
                "canonical_metric": canonical_name,
                "target": target,
                "actual": actual,
                "gate_type": gate_type,
                "passed": passed,
                "message": msg,
            }

            if not passed:
                breaches.append(
                    GateBreach(
                        metric=raw_name,
                        target=target,
                        actual=actual,
                        gate_type=gate_type,
                        message=msg,
                    )
                )

        return GateEvaluationResult(
            passed=len(breaches) == 0,
            breaches=tuple(breaches),
            gate_details=details,
        )
