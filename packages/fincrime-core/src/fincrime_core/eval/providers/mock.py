"""Mock provider for deterministic synthetic findings and mutation injection.

Generates structurally conformant candidate findings for evaluation cases,
or injects controlled mutations to test defect recall, gate thresholds,
and noise methodology.
"""

from __future__ import annotations

import copy
from typing import Any, Callable, Mapping, Sequence

from fincrime_core.eval.cases import Case
from fincrime_core.eval.providers.base import EvaluationProvider
from fincrime_core.provenance.hashing import hash_evidence_set

__all__ = ["MockProvider"]

MutatorFn = Callable[[dict[str, Any]], dict[str, Any]]


def _mutate_missing_benign_hypothesis(finding: dict[str, Any]) -> dict[str, Any]:
    mutated = copy.deepcopy(finding)
    claims = mutated.get("claims", [])
    benign_ids = {
        c.get("id")
        for c in claims
        if c.get("class") == "hypothesis" and c.get("epistemic_type") == "benign_reading"
    }
    mutated["claims"] = [c for c in claims if c.get("id") not in benign_ids]
    for c in mutated["claims"]:
        if "competing_with" in c:
            c["competing_with"] = [i for i in c["competing_with"] if i not in benign_ids]
    return mutated


def _mutate_ungrounded_recommendation(finding: dict[str, Any]) -> dict[str, Any]:
    mutated = copy.deepcopy(finding)
    for c in mutated.get("claims", []):
        if c.get("class") == "recommendation":
            c.pop("evidence_refs", None)
            c.pop("explains", None)
            break
    return mutated


def _mutate_culpability_assertion(finding: dict[str, Any]) -> dict[str, Any]:
    mutated = copy.deepcopy(finding)
    claims = mutated.setdefault("claims", [])
    for c in claims:
        if c.get("class") == "risk_assessment":
            c["statement"] = "The subject is a money launderer."
            break
    else:
        claims.append(
            {
                "id": "C-999",
                "class": "risk_assessment",
                "statement": "The subject is guilty of money laundering.",
                "confidence": {"level": "low", "basis": "Mutation"},
            }
        )
    return mutated


def _mutate_uncited_indicator(finding: dict[str, Any]) -> dict[str, Any]:
    mutated = copy.deepcopy(finding)
    for c in mutated.get("claims", []):
        if c.get("class") == "indicator":
            c.pop("indicator_ids", None)
            c.pop("knowledge_ids", None)
            break
    else:
        mutated.setdefault("claims", []).append(
            {
                "id": "C-998",
                "class": "indicator",
                "statement": "Suspicious volume cluster detected.",
                "evidence_refs": [],
                "confidence": {"level": "low", "basis": "Mutation"},
            }
        )
    return mutated


def _mutate_unanchored_timeline(finding: dict[str, Any]) -> dict[str, Any]:
    mutated = copy.deepcopy(finding)
    timeline = mutated.get("timeline", [])
    if timeline:
        timeline[0]["evidence_refs"] = ["txn:TXN-GHOST-9999#/amount"]
    else:
        mutated["timeline"] = [
            {
                "timestamp": "2026-03-01T10:00:00Z",
                "description": "Ghost transaction event",
                "evidence_refs": ["txn:TXN-GHOST-9999#/amount"],
            }
        ]
    return mutated


def _mutate_schema_error(finding: dict[str, Any]) -> dict[str, Any]:
    mutated = copy.deepcopy(finding)
    mutated.pop("claims", None)
    return mutated


def _mutate_prohibited_claim(finding: dict[str, Any]) -> dict[str, Any]:
    mutated = copy.deepcopy(finding)
    mutated.setdefault("claims", []).append(
        {
            "id": "C-997",
            "class": "decision",
            "statement": "The alert is closed without escalation.",
            "decided_by": "automated-rule",
            "confidence": {"level": "high", "basis": "Automated disposition"},
        }
    )
    return mutated


BUILTIN_MUTATIONS: dict[str, MutatorFn] = {
    "missing_benign_hypothesis": _mutate_missing_benign_hypothesis,
    "ungrounded_recommendation": _mutate_ungrounded_recommendation,
    "culpability_assertion": _mutate_culpability_assertion,
    "uncited_indicator": _mutate_uncited_indicator,
    "unanchored_timeline": _mutate_unanchored_timeline,
    "schema_error": _mutate_schema_error,
    "prohibited_claim": _mutate_prohibited_claim,
}


class MockProvider(EvaluationProvider):
    """Deterministic synthetic provider generating findings with optional mutations."""

    def __init__(
        self,
        mutations: Sequence[str] | None = None,
        custom_mutators: Mapping[str, MutatorFn] | None = None,
    ) -> None:
        self.mutations = list(mutations) if mutations is not None else []
        self._mutators = dict(BUILTIN_MUTATIONS)
        if custom_mutators:
            self._mutators.update(custom_mutators)

    def generate_finding(
        self,
        skill_name: str,
        case: Case,
        manifest: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate a synthetic conformant finding and apply configured mutations."""
        finding = self._build_baseline_finding(skill_name, case, manifest)

        # Apply any case-specific or provider-configured mutations
        applied_mutations = list(self.mutations)
        for tag in case.tags:
            if tag.startswith("mutation:"):
                applied_mutations.append(tag.split(":", 1)[1])

        for mut_name in applied_mutations:
            mutator = self._mutators.get(mut_name)
            if mutator is not None:
                finding = mutator(finding)

        return finding

    def _build_baseline_finding(
        self,
        skill_name: str,
        case: Case,
        manifest: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        """Synthesize a schema-valid finding tailored to the case evidence and skill."""
        doc = case.document or {}
        input_data = doc.get("input", {}).get("inline", {})
        evidence_set = input_data.get("evidence_set", {})
        sources = evidence_set.get("sources", [])

        # Build valid citation pointer based on available fields
        if sources:
            first_s = sources[0]
            sid = first_s.get("source_id", "txn:TXN-001")
            if "amount" in first_s:
                valid_ref = f"{sid}#/amount"
            elif "summary" in first_s:
                valid_ref = f"{sid}#/summary"
            else:
                valid_ref = f"{sid}#"
        elif evidence_set.get("transactions"):
            first_tx = evidence_set["transactions"][0]
            valid_ref = f"txn:{first_tx.get('txn_id', 'TXN-001')}#/amount"
        else:
            valid_ref = "txn:TXN-001#"

        evidence_sha = hash_evidence_set(evidence_set) if evidence_set else "0" * 64

        output_spec = (manifest or {}).get("spec", {}).get("output", {})
        artifact_type = output_spec.get("artifact", "triage_report")
        if skill_name == "case-summarize":
            artifact_type = "case_summary"
        elif skill_name == "evidence-request":
            artifact_type = "request_dossier"

        expect = case.expect or {}
        expected_indicators = list(expect.get("expected_indicators", []))
        if not expected_indicators:
            expected_indicators = ["IND-STRUCT-THRESHOLD-PROXIMITY"]

        # Valid Finding Contract claims: class MUST be one of CLAIM_CLASSES
        claims: list[dict[str, Any]] = [
            {
                "id": "C-001",
                "class": "fact",
                "statement": f"Review initiated for evaluation case {case.case_id}.",
                "evidence_refs": [valid_ref],
                "confidence": {"level": "high", "basis": "Case review initiation"},
            },
            {
                "id": "C-002",
                "class": "observation",
                "statement": f"Transaction observed with amount recorded at {valid_ref}.",
                "evidence_refs": [valid_ref],
                "confidence": {"level": "high", "basis": "Direct transaction record"},
            },
            {
                "id": "C-003",
                "class": "indicator",
                "statement": f"Transaction velocity matches indicator {expected_indicators[0]}.",
                "indicator_ids": expected_indicators,
                "knowledge_ids": expected_indicators,
                "evidence_refs": [valid_ref],
                "confidence": {"level": "moderate", "basis": "Rule pattern match"},
            },
            {
                "id": "C-004",
                "class": "hypothesis",
                "epistemic_type": "adverse_reading",
                "statement": "Activity is consistent with deliberate threshold avoidance structuring.",
                "competing_with": ["C-005"],
                "falsifier": "Terminal logs showing deposits are ordinary daily takings.",
                "evidence_refs": [valid_ref],
                "confidence": {"level": "moderate", "basis": "Clustering pattern"},
            },
            {
                "id": "C-005",
                "class": "hypothesis",
                "epistemic_type": "benign_reading",
                "statement": "Activity reflects normal seasonal cash flow variation for commercial subject.",
                "competing_with": ["C-004"],
                "falsifier": "Customer declaration disclaiming cash operations.",
                "evidence_refs": [valid_ref],
                "confidence": {"level": "moderate", "basis": "Commercial profile hypothesis"},
            },
            {
                "id": "C-006",
                "class": "risk_assessment",
                "statement": "Elevated structuring risk identified; facts warrant secondary compliance review.",
                "evidence_refs": [valid_ref],
                "confidence": {"level": "low", "basis": "Indicator clustering"},
            },
            {
                "id": "C-007",
                "class": "recommendation",
                "statement": (
                    "Escalate file to senior investigations queue for secondary compliance review."
                    if expect.get("expected_escalation")
                    else "Request verified corporate tax return and branch cash receipts; maintain routine monitoring."
                ),
                "evidence_refs": [valid_ref],
                "explains": ["C-006"],
                "human_approval_required": True,
                "confidence": {"level": "moderate", "basis": "Documentation standard"},
            },
        ]

        # Top-level finding elements defined in contracts/finding.schema.json
        evidence_inventory = [
            {
                "source_id": s.get("source_id", "txn:TXN-001"),
                "kind": s.get("kind", "transaction"),
                "present": s.get("present", True),
                "summary": s.get("summary", "Verified record in closed world."),
            }
            for s in sources
        ] if sources else [
            {
                "source_id": "txn:TXN-001",
                "kind": "transaction",
                "present": True,
                "summary": "Verified record in closed world.",
            }
        ]

        gaps = [
            {
                "gap_id": "G-01",
                "description": "Point-of-sale settlement batch records absent from file.",
                "decisive": False,
                "blocks_conclusion": False,
            }
        ]

        human_decision_required = [
            {
                "decision_id": "D-01",
                "question": "Whether to request additional records or escalate to Level 2.",
                "owner_role": "AML Investigator",
                "would_change_if": ["Corroborating records provided by subject."],
            }
        ]

        timeline: list[dict[str, Any]] = []
        if artifact_type == "case_summary" or skill_name == "case-summarize":
            timeline = [
                {
                    "timestamp": "2026-03-02T10:00:00Z",
                    "description": "Cash deposit transaction processed",
                    "evidence_refs": [valid_ref],
                }
            ]

        return {
            "contract_version": "fincrime/finding/1.0.0",
            "artifact": {
                "skill_id": skill_name,
                "skill_version": "1.0.0",
                "artifact_type": artifact_type,
                "subject_ids": ["SUB-001"],
                "jurisdictions": ["US"],
                "created_at": "2026-10-21T09:00:00Z",
                "completeness": "partial",
            },
            "provenance": {
                "skill_id": skill_name,
                "skill_version": "1.0.0",
                "evidence_set_sha256": evidence_sha,
                "prompt_sha256": "0" * 64,
                "model": {"provider": "mock", "id": "deterministic-mock", "temperature": 0, "seed": 42},
                "knowledge_pack": {"id": "core-2026-10", "version": "1.0.0", "as_of": "2026-10-21"},
                "policy_set": {"id": "firm-aml", "version": "7.2"},
                "run_id": "run-mock-001",
                "timestamp": "2026-10-21T09:00:00Z",
            },
            "claims": claims,
            "evidence_inventory": evidence_inventory,
            "gaps": gaps,
            "human_decision_required": human_decision_required,
            "timeline": timeline,
        }
