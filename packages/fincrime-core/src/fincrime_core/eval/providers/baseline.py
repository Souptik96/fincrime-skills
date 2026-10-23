"""Baseline unconstrained zero-shot provider for empirical comparative evaluation.

Simulates raw, unguided LLM outputs without the FinCrime skill system:
- High hallucination rate (unsupported claims and unresolved citations)
- Direct culpability and legal guilt assertions (violating Rule R-6 and POL-NO-CRIMINALITY-CLAIMS)
- Lack of benign reading hypotheses and falsifiers
- Absence of human approval gates on recommendations
- Non-deterministic variance across seeds for multi-seed noise methodology
"""

from __future__ import annotations

import random
from typing import Any, Mapping

from fincrime_core.eval.cases import Case
from fincrime_core.eval.providers.base import EvaluationProvider

__all__ = ["NoSkillBaselineProvider"]


class NoSkillBaselineProvider(EvaluationProvider):
    """Generates unconstrained zero-shot candidate findings representing raw LLM behavior."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self._rng = random.Random(seed)

    def generate_finding(
        self,
        skill_name: str,
        case: Case,
        manifest: Mapping[str, Any] | None = None,
        as_of: Any = None,
    ) -> dict[str, Any]:
        """Generate a simulated unconstrained zero-shot finding for a case."""
        case_id = case.case_id
        inline_input = case.document.get("input", {}).get("inline", {})
        evidence_set = inline_input.get("evidence_set", {})
        sources = evidence_set.get("sources", [])
        fallback_subject = (
            inline_input.get("subject_scope", {}).get("subject_id")
            or inline_input.get("alert", {}).get("subject_id")
            or "SUB-001"
        )
        primary_ref = f"{sources[0].get('source_id', 'txn:001')}#/summary" if sources else f"subject:{fallback_subject}#"

        # Stochastic noise variations based on seed
        hallucinate_ref = self._rng.random() < 0.65
        assert_culpability = self._rng.random() < 0.75
        omit_benign = self._rng.random() < 0.90
        omit_human_gate = self._rng.random() < 0.85
        schema_defect = self._rng.random() < 0.40

        claims: list[dict[str, Any]] = []

        # Claim 1: Fact / Opening statement
        claims.append(
            {
                "id": "C-001",
                "class": "fact",
                "statement": f"Investigated alert for subject in case {case_id}.",
                "evidence_refs": [primary_ref],
                "confidence": {"level": "high", "basis": "Initial review"},
            }
        )

        # Claim 2: Hallucinated / Unsupported Observation
        obs_refs = [] if hallucinate_ref else [primary_ref]
        claims.append(
            {
                "id": "C-002",
                "class": "observation",
                "statement": "Multiple suspicious transactions executed during the monitoring window.",
                "evidence_refs": obs_refs,
                "confidence": {"level": "high", "basis": "Assumed from alert"},
            }
        )

        # Claim 3: Culpability / Criminality Assertion (Violates R-6 / POL-NO-CRIMINALITY-CLAIMS)
        if assert_culpability:
            risk_stmt = "The customer is guilty of structuring cash transactions to evade regulatory reporting."
        else:
            risk_stmt = "Transactions present heightened illicit finance indicators without commercial justification."

        culpability_refs = ["txn:HALLUCINATED-999#/amount"] if hallucinate_ref else [primary_ref]
        claims.append(
            {
                "id": "C-003",
                "class": "risk_assessment",
                "statement": risk_stmt,
                "evidence_refs": culpability_refs,
                "confidence": {"level": "high", "basis": "Pattern analysis"},
            }
        )

        # Claim 4: Adverse Hypothesis only (omitting competing benign hypothesis)
        claims.append(
            {
                "id": "C-004",
                "class": "hypothesis",
                "epistemic_type": "adverse_reading",
                "statement": "Funds represent proceeds of illegal smurfing activity.",
                "evidence_refs": culpability_refs,
                "confidence": {"level": "moderate", "basis": "Subject profile"},
            }
        )

        if not omit_benign:
            claims.append(
                {
                    "id": "C-005",
                    "class": "hypothesis",
                    "epistemic_type": "benign_reading",
                    "statement": "Activity could theoretically represent legitimate commercial turnover.",
                    "evidence_refs": [primary_ref],
                    "confidence": {"level": "low", "basis": "Alternative"},
                }
            )

        # Claim 5: Recommendation without human approval gate
        rec_stmt = "File Suspicious Activity Report (SAR) immediately and close customer account."
        claims.append(
            {
                "id": "C-006",
                "class": "recommendation",
                "statement": rec_stmt,
                "evidence_refs": [primary_ref],
                "human_approval_required": False if omit_human_gate else True,
                "confidence": {"level": "high", "basis": "Direct filing recommendation"},
            }
        )

        finding: dict[str, Any] = {
            "contract_version": "fincrime/finding/1.0.0",
            "finding_id": f"finding:baseline:{case_id}",
            "artifact": {
                "artifact_type": "triage_decision" if "triage" in skill_name else "case_summary",
                "artifact_id": f"art:baseline:{case_id}",
                "title": f"Zero-shot Review {case_id}",
                "summary": "Automated zero-shot summary without skill constraints.",
            },
            "subject": {
                "subject_id": fallback_subject,
                "name": "Target Customer",
            },
            "claims": claims,
        }

        if schema_defect:
            # Inject an invalid enum or malformed field that triggers schema failure
            finding["artifact"]["artifact_type"] = "unconstrained_text_memo"

        return finding
