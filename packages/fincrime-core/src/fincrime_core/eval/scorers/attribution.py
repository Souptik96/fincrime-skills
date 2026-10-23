"""Evidence attribution and unsupported claim rate scorers.

Measures evidence reference grounding against the closed evidence set:
- evidence_attribution_accuracy (gate: >= 0.98)
- unsupported_claim_rate (gate: <= 0.02)
"""

from __future__ import annotations

from typing import Any, Mapping

from fincrime_core.eval.cases import Case
from fincrime_core.eval.scorers.base import ScoreResult, Scorer
from fincrime_core.validate.validator import EnforcementContext, ValidationResult, Validator

__all__ = ["EvidenceAttributionScorer", "UnsupportedClaimRateScorer"]


def _ensure_validation_result(
    candidate: dict[str, Any],
    case: Case,
    validation_result: ValidationResult | None,
    **kwargs: Any,
) -> ValidationResult:
    """Ensure a ValidationResult is available, running Validator if needed."""
    if validation_result is not None:
        return validation_result

    evidence_set = (
        case.document.get("input", {}).get("inline", {}).get("evidence_set", {})
    )
    known_indicators = kwargs.get("known_indicator_ids")
    known_knowledge = kwargs.get("known_knowledge_ids")
    expired = kwargs.get("expired_knowledge_ids")
    jurisdictions = kwargs.get("allowed_jurisdictions", ["US"])

    validator = Validator(
        evidence_set=evidence_set,
        known_indicator_ids=known_indicators,
        known_knowledge_ids=known_knowledge,
        expired_knowledge_ids=expired,
        allowed_jurisdictions=jurisdictions,
    )
    return validator.validate(candidate, EnforcementContext(EnforcementContext.PROMOTION))


class EvidenceAttributionScorer(Scorer):
    """Scores accuracy of evidence references resolving to verified sources."""

    metric_name = "evidence_attribution_accuracy"
    default_gate_target = 0.98
    gate_type = "min"

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
        res = _ensure_validation_result(candidate, case, validation_result, **kwargs)

        score = float(res.evidence_attribution_accuracy)
        passed = self.is_passing(score, target)

        details = {
            "unsupported_claim_rate": res.unsupported_claim_rate,
            "resolved_refs": dict(res.resolved_refs),
            "unsupported_defects": [
                d.to_dict() for d in res.defects if d.code == "unsupported_claim"
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


class UnsupportedClaimRateScorer(Scorer):
    """Scores fraction of evidence-bearing claims lacking valid citations."""

    metric_name = "unsupported_claim_rate"
    default_gate_target = 0.02
    gate_type = "max"

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
        res = _ensure_validation_result(candidate, case, validation_result, **kwargs)

        score = float(res.unsupported_claim_rate)
        passed = self.is_passing(score, target)

        details = {
            "unsupported_defects": [
                d.to_dict() for d in res.defects if d.code == "unsupported_claim"
            ]
        }

        return ScoreResult(
            metric=self.metric_name,
            score=score,
            passed=passed,
            gate_target=target,
            gate_type=self.gate_type,
            details=details,
        )
