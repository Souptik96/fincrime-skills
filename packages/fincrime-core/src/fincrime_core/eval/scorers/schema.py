"""Deterministic schema validity scorer.

Verifies strict compliance with fincrime/finding/1.0.0.
Gate target: 1.0 (100% schema validity).
"""

from __future__ import annotations

from typing import Any, Mapping

from fincrime_core.eval.cases import Case
from fincrime_core.eval.scorers.base import ScoreResult, Scorer
from fincrime_core.validate.validator import ValidationResult, load_finding_schema

__all__ = ["SchemaValidityScorer"]


class SchemaValidityScorer(Scorer):
    """Scores candidate findings for canonical JSON Schema validity."""

    metric_name = "schema_validity"
    default_gate_target = 1.0
    gate_type = "min"

    def __init__(self) -> None:
        self._schema_validator = load_finding_schema()

    def score(
        self,
        candidate: dict[str, Any],
        case: Case,
        manifest: Mapping[str, Any] | None = None,
        validation_result: ValidationResult | None = None,
        gate_target: float | None = None,
        **kwargs: Any,
    ) -> ScoreResult:
        target = gate_target if gate_target is not None else self.default_gate_target

        if validation_result is not None:
            schema_errors = validation_result.schema_errors
        else:
            schema_errors = self._schema_validator.validate(candidate)

        is_valid = len(schema_errors) == 0
        score = 1.0 if is_valid else 0.0
        passed = self.is_passing(score, target)

        details = {
            "error_count": len(schema_errors),
            "errors": [
                {"path": e.path, "message": e.message, "keyword": e.keyword}
                for e in schema_errors
            ],
        }

        return ScoreResult(
            metric=self.metric_name,
            score=score,
            passed=passed,
            gate_target=target,
            gate_type=self.gate_type,
            details=details,
        )
