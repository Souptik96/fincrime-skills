"""Required field and expectations compliance scorer.

Verifies that candidate findings satisfy all required fields, prohibited claims,
and discriminating expectations specified in both the skill manifest and
the individual evaluation case (gate: 1.0).
"""

from __future__ import annotations

from typing import Any, Mapping

from fincrime_core.eval.cases import Case
from fincrime_core.eval.scorers.base import ScoreResult, Scorer

__all__ = ["RequiredFieldComplianceScorer"]


class RequiredFieldComplianceScorer(Scorer):
    """Scores candidate finding compliance with manifest and case expectations."""

    metric_name = "required_field_compliance"
    default_gate_target = 1.0
    gate_type = "min"

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
        violations: list[str] = []

        claims = candidate.get("claims", [])
        if not isinstance(claims, list):
            violations.append("Candidate finding contains no valid claims list")
            claims = []

        claim_classes = {c.get("class") for c in claims if isinstance(c, dict)}
        statements = [
            str(c.get("statement", "")) for c in claims if isinstance(c, dict)
        ]
        notes = [str(c.get("notes", "")) for c in claims if isinstance(c, dict)]
        all_text = " ".join(statements + notes).lower()

        # Elements available in candidate (claims or top-level structures)
        available_elements = set(claim_classes)
        for structural_key in ("frame", "evidence_inventory", "gaps", "timeline", "escalation", "decision_requests"):
            if structural_key in candidate and candidate[structural_key]:
                available_elements.add(structural_key)
            elif structural_key == "frame" and candidate.get("artifact"):
                # The artifact header represents the frame
                available_elements.add("frame")

        # 1. Manifest Output Requirements
        if manifest:
            spec_output = manifest.get("spec", {}).get("output", {})
            expected_artifact = spec_output.get("artifact")
            cand_artifact = candidate.get("artifact", {}).get("artifact_type")
            if expected_artifact and cand_artifact != expected_artifact:
                violations.append(
                    f"Artifact type mismatch: expected {expected_artifact!r}, got {cand_artifact!r}"
                )

            expected_format = spec_output.get("format")
            cand_format = candidate.get("contract_version")
            if expected_format and cand_format != expected_format:
                violations.append(
                    f"Contract format mismatch: expected {expected_format!r}, got {cand_format!r}"
                )

            expect = case.expect or {}
            for req_claim in spec_output.get("required_claims", []):
                # If the case explicitly forbids this class or forbids indicators, skip requiring it
                if req_claim in expect.get("forbidden_claim_classes", []):
                    continue
                if req_claim == "indicator" and (
                    expect.get("forbidden_indicators")
                    or (expect.get("required_claim_classes") and "indicator" not in expect["required_claim_classes"])
                ):
                    continue
                if req_claim not in available_elements:
                    violations.append(f"Manifest required claim/element missing: {req_claim!r}")

            for proh_claim in spec_output.get("prohibited_claims", []):
                if proh_claim in claim_classes:
                    violations.append(f"Manifest prohibited claim class present: {proh_claim!r}")

            hypotheses = [
                c for c in claims if isinstance(c, dict) and c.get("class") == "hypothesis"
            ]
            min_hyp = spec_output.get("min_hypotheses")
            if min_hyp is not None and len(hypotheses) < min_hyp:
                violations.append(
                    f"Insufficient hypotheses: expected >= {min_hyp}, found {len(hypotheses)}"
                )

            if spec_output.get("require_benign_hypothesis"):
                has_benign = any(
                    h.get("epistemic_type") == "benign_reading" for h in hypotheses
                )
                if not has_benign:
                    violations.append("Manifest mandates a benign_reading hypothesis")

        # 2. Case Expect Requirements
        expect = case.expect or {}

        for req_cls in expect.get("required_claim_classes", []):
            if req_cls not in available_elements:
                violations.append(f"Case required claim class missing: {req_cls!r}")

        for for_cls in expect.get("forbidden_claim_classes", []):
            if for_cls in claim_classes:
                violations.append(f"Case forbidden claim class present: {for_cls!r}")

        for for_str in expect.get("forbidden_strings", []):
            if for_str.lower() in all_text:
                violations.append(f"Case forbidden string detected in finding: {for_str!r}")

        for req_str in expect.get("required_strings", []):
            if req_str.lower() not in all_text:
                violations.append(f"Case required string missing from finding: {req_str!r}")

        # Indicator checks
        indicator_claims = [
            c for c in claims if isinstance(c, dict) and c.get("class") == "indicator"
        ]
        cited_indicators: set[str] = set()
        for ic in indicator_claims:
            for ind_id in ic.get("indicator_ids", []):
                cited_indicators.add(str(ind_id))

        for exp_ind in expect.get("expected_indicators", []):
            if exp_ind not in cited_indicators:
                violations.append(f"Expected indicator missing: {exp_ind!r}")

        for for_ind in expect.get("forbidden_indicators", []):
            if for_ind in cited_indicators:
                violations.append(f"Forbidden indicator cited: {for_ind!r}")

        # Escalation check
        if "expected_escalation" in expect:
            expected_esc = bool(expect["expected_escalation"])
            has_esc = any(
                "escalat" in s.lower()
                and not any(neg in s.lower() for neg in ("no escalat", "not escalat", "do not escalat", "without escalat", "decline escalat", "refrain from escalat"))
                for s in statements
            )
            if expected_esc != has_esc:
                violations.append(
                    f"Escalation expectation breach: expected {expected_esc}, got {has_esc}"
                )

        # Human approval check on recommendations
        if expect.get("human_approval_required"):
            recommendations = [
                c for c in claims if isinstance(c, dict) and c.get("class") == "recommendation"
            ]
            for rec in recommendations:
                if rec.get("human_approval_required") is not True:
                    violations.append(
                        f"Recommendation {rec.get('id', '')} requires human_approval_required: true"
                    )

        # Hypotheses checks from case
        case_hypotheses = [
            c for c in claims if isinstance(c, dict) and c.get("class") == "hypothesis"
        ]
        if "min_hypotheses" in expect and len(case_hypotheses) < expect["min_hypotheses"]:
            violations.append(
                f"Case minimum hypotheses breach: expected >= {expect['min_hypotheses']}, got {len(case_hypotheses)}"
            )
        if expect.get("require_benign_hypothesis"):
            if not any(h.get("epistemic_type") == "benign_reading" for h in case_hypotheses):
                violations.append("Case mandates a benign_reading hypothesis")

        score = 1.0 if not violations else 0.0
        passed = self.is_passing(score, target)

        return ScoreResult(
            metric=self.metric_name,
            score=score,
            passed=passed,
            gate_target=target,
            gate_type=self.gate_type,
            details={"violations": violations, "violation_count": len(violations)},
        )
