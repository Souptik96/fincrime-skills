"""Deterministic scorers for the FinCrime evaluation harness."""

from __future__ import annotations

from typing import Any, Mapping

from fincrime_core.eval.cases import Case
from fincrime_core.eval.scorers.attribution import (
    EvidenceAttributionScorer,
    UnsupportedClaimRateScorer,
)
from fincrime_core.eval.scorers.base import ScoreResult, Scorer
from fincrime_core.eval.scorers.compliance import RequiredFieldComplianceScorer
from fincrime_core.eval.scorers.defects import (
    ExpectedDefectRecallScorer,
    FalseDefectRateScorer,
)
from fincrime_core.eval.scorers.policy import PolicyPassRateScorer
from fincrime_core.eval.scorers.schema import SchemaValidityScorer
from fincrime_core.validate.validator import ValidationResult

__all__ = [
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
]


def default_scorers() -> list[Scorer]:
    """Return an instantiated list of the 7 default deterministic scorers."""
    return [
        SchemaValidityScorer(),
        EvidenceAttributionScorer(),
        UnsupportedClaimRateScorer(),
        RequiredFieldComplianceScorer(),
        PolicyPassRateScorer(),
        ExpectedDefectRecallScorer(),
        FalseDefectRateScorer(),
    ]


class CompoundScorer:
    """Orchestrates running multiple deterministic scorers against one candidate."""

    def __init__(self, scorers: list[Scorer] | None = None) -> None:
        self.scorers = list(scorers) if scorers is not None else default_scorers()

    def score_all(
        self,
        candidate: dict[str, Any],
        case: Case,
        manifest: Mapping[str, Any] | None = None,
        validation_result: ValidationResult | None = None,
        gate_targets: Mapping[str, float] | None = None,
        **kwargs: Any,
    ) -> dict[str, ScoreResult]:
        """Run all configured scorers against a candidate finding.

        Returns a dictionary mapping metric_name to ScoreResult.
        """
        targets = gate_targets or {}
        results: dict[str, ScoreResult] = {}
        for scorer in self.scorers:
            target = targets.get(scorer.metric_name)
            # Check for alternative key names like unsupported_claim_rate_max
            if target is None:
                if scorer.metric_name == "unsupported_claim_rate":
                    target = targets.get("unsupported_claim_rate_max")
                elif scorer.metric_name == "false_defect_rate":
                    target = targets.get("false_defect_rate_max")

            result = scorer.score(
                candidate=candidate,
                case=case,
                manifest=manifest,
                validation_result=validation_result,
                gate_target=target,
                **kwargs,
            )
            results[scorer.metric_name] = result

        return results
