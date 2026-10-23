"""Deterministic policy pass rate scorer.

Evaluates candidate findings against enforceable firm rules (e.g.,
policies/default/policy-set.json) using PolicyEvaluator.
Gate target: 1.0 (100% policy pass rate).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from fincrime_core.contract.loader import parse_finding
from fincrime_core.eval.cases import Case
from fincrime_core.eval.scorers.base import ScoreResult, Scorer
from fincrime_core.paths import repo_root
from fincrime_core.policy.evaluator import PolicyEvaluator
from fincrime_core.policy.set import load_policy_set

__all__ = ["PolicyPassRateScorer"]


def _default_policy_evaluator() -> PolicyEvaluator | None:
    root = repo_root()
    if root is None:
        return None
    policy_path = root / "policies" / "default" / "policy-set.json"
    if policy_path.is_file():
        policy_set = load_policy_set(policy_path)
        return PolicyEvaluator(policy_set.rules)
    return None


class PolicyPassRateScorer(Scorer):
    """Scores candidate finding compliance with enforceable deterministic policy sets."""

    metric_name = "policy_pass_rate"
    default_gate_target = 1.0
    gate_type = "min"

    def __init__(self, evaluator: PolicyEvaluator | None = None) -> None:
        self._evaluator = evaluator

    def score(
        self,
        candidate: dict[str, Any],
        case: Case,
        manifest: Mapping[str, Any] | None = None,
        validation_result: Any = None,
        gate_target: float | None = None,
        **kwargs: Any,
    ) -> ScoreResult:
        target = gate_target if gate_target is not None else self.default_gate_target

        evaluator = kwargs.get("policy_evaluator") or self._evaluator
        if evaluator is None:
            evaluator = _default_policy_evaluator()

        violations = []
        if evaluator is not None:
            finding_model = parse_finding(candidate)
            violations = evaluator.evaluate(finding_model)

        score = 1.0 if not violations else 0.0
        passed = self.is_passing(score, target)

        details = {
            "violation_count": len(violations),
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "severity": v.severity,
                    "message": v.message,
                    "claim_id": v.claim_id,
                }
                for v in violations
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
