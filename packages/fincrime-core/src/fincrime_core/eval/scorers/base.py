"""Base interface for deterministic scorers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping

from fincrime_core.eval.cases import Case
from fincrime_core.validate.validator import ValidationResult

__all__ = ["ScoreResult", "Scorer"]


@dataclass(frozen=True, slots=True)
class ScoreResult:
    """The outcome of evaluating one metric against a candidate finding."""

    metric: str
    score: float
    passed: bool
    gate_target: float | None = None
    gate_type: str = "min"  # "min" (score >= target) or "max" (score <= target)
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "score": self.score,
            "passed": self.passed,
            "gate_target": self.gate_target,
            "gate_type": self.gate_type,
            "details": dict(self.details),
        }


class Scorer(ABC):
    """Abstract base class for deterministic scorers."""

    metric_name: str = ""
    default_gate_target: float | None = None
    gate_type: str = "min"  # "min" or "max"

    @abstractmethod
    def score(
        self,
        candidate: dict[str, Any],
        case: Case,
        manifest: Mapping[str, Any] | None = None,
        validation_result: ValidationResult | None = None,
        gate_target: float | None = None,
        **kwargs: Any,
    ) -> ScoreResult:
        """Score the candidate finding against the case and manifest.

        Args:
            candidate: Raw candidate finding document.
            case: The Case instance containing discriminating expectations.
            manifest: Optional parsed skill manifest.
            validation_result: Pre-computed ValidationResult if available.
            gate_target: Optional override for the gate threshold.
            **kwargs: Extra contextual arguments (e.g., policy evaluator, pack).
        """
        raise NotImplementedError

    def is_passing(self, score: float, target: float | None) -> bool:
        """Check whether a score passes the gate target."""
        if target is None:
            return True
        if self.gate_type == "max":
            return score <= target
        return score >= target
