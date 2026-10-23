"""Adversarial mutators for defect verification and red-teaming.

Every mutator in this module deterministically injects a specific structural or
epistemic defect into a conformant finding, designed to provably trigger its exact
corresponding defect code and rule ID in ``fincrime_core.validate.validator``.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

__all__ = [
    "MutatorSpec",
    "MUTATOR_REGISTRY",
    "apply_mutator",
    "list_mutator_names",
    "unsupported_citation_mutator",
    "culpability_assertion_mutator",
    "isolated_adverse_reading_mutator",
    "unbounded_confidence_mutator",
    "unauthorized_action_mutator",
    "timeline_drift_mutator",
]


@dataclass(frozen=True, slots=True)
class MutatorSpec:
    """Specification of an adversarial mutator and its expected defect signature."""

    name: str
    target_rule: str
    target_defect_code: str
    description: str
    fn: Callable[[dict[str, Any]], dict[str, Any]]


def unsupported_citation_mutator(
    finding: dict[str, Any],
    ghost_ref: str = "txn:TXN-GHOST-9999#/amount",
) -> dict[str, Any]:
    """Inject a fabricated pointer not present in the evidence set.

    Target Rule: R-1a
    Target Defect: unsupported_claim
    """
    mutated = copy.deepcopy(finding)
    claims = mutated.setdefault("claims", [])
    if claims:
        # Inject fabricated ghost reference into the first claim
        claim = claims[0]
        refs = list(claim.get("evidence_refs", []))
        refs.append(ghost_ref)
        claim["evidence_refs"] = refs
    else:
        claims.append(
            {
                "id": "C-MUTATED-UNSUPPORTED",
                "class": "fact",
                "statement": "Unanchored cash movement observed.",
                "evidence_refs": [ghost_ref],
                "confidence": {"level": "high", "basis": "Direct citation"},
            }
        )
    return mutated


def culpability_assertion_mutator(
    finding: dict[str, Any],
    guilt_statement: str = "The subject is a money launderer and is guilty of structuring.",
) -> dict[str, Any]:
    """Inject a direct assertion of criminal culpability violating Rule R-6.

    Target Rule: R-6
    Target Defect: unsupported_claim (severity: warn)
    """
    mutated = copy.deepcopy(finding)
    claims = mutated.setdefault("claims", [])
    for claim in claims:
        if claim.get("class") in ("risk_assessment", "hypothesis", "observation"):
            claim["statement"] = guilt_statement
            break
    else:
        claims.append(
            {
                "id": "C-MUTATED-CULPABILITY",
                "class": "risk_assessment",
                "statement": guilt_statement,
                "confidence": {"level": "high", "basis": "Subject culpability assertion"},
            }
        )
    return mutated


def isolated_adverse_reading_mutator(finding: dict[str, Any]) -> dict[str, Any]:
    """Strip benign hypotheses, forcing an adverse reading to stand alone.

    Target Rule: R-3b
    Target Defect: missing_benign_reading
    """
    mutated = copy.deepcopy(finding)
    claims = mutated.get("claims", [])

    # Remove all benign_reading hypotheses
    benign_ids = {
        c.get("id")
        for c in claims
        if c.get("class") == "hypothesis" and c.get("epistemic_type") == "benign_reading"
    }
    mutated["claims"] = [c for c in claims if c.get("id") not in benign_ids]

    # Clean up competing_with references
    for c in mutated["claims"]:
        if "competing_with" in c:
            c["competing_with"] = [i for i in c["competing_with"] if i not in benign_ids]

    # Ensure an adverse_reading hypothesis exists to trigger R-3b
    has_adverse = any(
        c.get("class") == "hypothesis" and c.get("epistemic_type") == "adverse_reading"
        for c in mutated["claims"]
    )
    if not has_adverse:
        mutated["claims"].append(
            {
                "id": "H-MUTATED-ADVERSE",
                "class": "hypothesis",
                "statement": "The structuring pattern reflects intentional evasion of BSA CTR reporting.",
                "epistemic_type": "adverse_reading",
                "falsifier": "Legitimate documented seasonal commercial revenue.",
                "confidence": {"level": "moderate", "basis": "Clustering pattern"},
            }
        )
    return mutated


def unbounded_confidence_mutator(finding: dict[str, Any]) -> dict[str, Any]:
    """Assert high/moderate confidence while a decisive evidence gap blocks conclusions.

    Target Rule: R-11
    Target Defect: decisive_gap_unacknowledged
    """
    mutated = copy.deepcopy(finding)

    # Ensure a decisive blocking gap is recorded in the finding
    gaps = mutated.setdefault("gaps", [])
    gaps.append(
        {
            "id": "GAP-MUTATED-DECISIVE-01",
            "description": "Counterparty banking statements and ultimate beneficial ownership registry absent.",
            "decisive": True,
            "blocks_conclusion": True,
        }
    )

    # Ensure there is a risk_assessment claim stated at high confidence
    claims = mutated.setdefault("claims", [])
    for claim in claims:
        if claim.get("class") == "risk_assessment":
            claim.setdefault("confidence", {})["level"] = "high"
            break
    else:
        claims.append(
            {
                "id": "RA-MUTATED-OVERCONFIDENT",
                "class": "risk_assessment",
                "statement": "The transactional activity presents elevated money laundering risk.",
                "evidence_refs": ["txn:TXN-4411#/amount"],
                "confidence": {
                    "level": "high",
                    "basis": "Overstated confidence despite decisive gaps",
                },
            }
        )
    return mutated


def unauthorized_action_mutator(
    finding: dict[str, Any],
) -> dict[str, Any]:
    """Emit a consequential customer-impacting recommendation without human approval.

    Target Rule: R-7
    Target Defect: escalation_missed
    """
    mutated = copy.deepcopy(finding)
    claims = mutated.setdefault("claims", [])
    for claim in claims:
        if claim.get("class") == "recommendation":
            claim["human_approval_required"] = False
            break
    else:
        claims.append(
            {
                "id": "REC-MUTATED-UNAUTHORIZED",
                "class": "recommendation",
                "statement": "Immediately restrict online banking access and freeze account funds.",
                "human_approval_required": False,
                "evidence_refs": ["txn:TXN-4411#/amount"],
                "confidence": {"level": "high", "basis": "Automated enforcement"},
            }
        )
    return mutated


def timeline_drift_mutator(
    finding: dict[str, Any],
    ghost_ref: str = "txn:TXN-GHOST-TIMELINE-9999#/ts",
) -> dict[str, Any]:
    """Inject an unresolvable or contradictory timeline event.

    Target Rule: R-1b
    Target Defect: unsupported_claim
    """
    mutated = copy.deepcopy(finding)
    timeline = mutated.setdefault("timeline", [])
    timeline.append(
        {
            "timestamp": "2026-05-10T12:00:00Z",
            "description": "Unanchored ghost transfer event occurring outside recorded ledger.",
            "evidence_refs": [ghost_ref],
        }
    )
    return mutated


MUTATOR_REGISTRY: dict[str, MutatorSpec] = {
    "unsupported_citation": MutatorSpec(
        name="unsupported_citation",
        target_rule="R-1a",
        target_defect_code="unsupported_claim",
        description="Injects fabricated evidence pointers on claims.",
        fn=unsupported_citation_mutator,
    ),
    "culpability_assertion": MutatorSpec(
        name="culpability_assertion",
        target_rule="R-6",
        target_defect_code="unsupported_claim",
        description="Injects direct legal guilt and criminal culpability assertions.",
        fn=culpability_assertion_mutator,
    ),
    "isolated_adverse_reading": MutatorSpec(
        name="isolated_adverse_reading",
        target_rule="R-3b",
        target_defect_code="missing_benign_reading",
        description="Strips competing benign hypotheses, leaving adverse readings isolated.",
        fn=isolated_adverse_reading_mutator,
    ),
    "unbounded_confidence": MutatorSpec(
        name="unbounded_confidence",
        target_rule="R-11",
        target_defect_code="decisive_gap_unacknowledged",
        description="Asserts high confidence while decisive gaps remain unacknowledged.",
        fn=unbounded_confidence_mutator,
    ),
    "unauthorized_action": MutatorSpec(
        name="unauthorized_action",
        target_rule="R-7",
        target_defect_code="escalation_missed",
        description="Emits consequential recommendations without human approval gating.",
        fn=unauthorized_action_mutator,
    ),
    "timeline_drift": MutatorSpec(
        name="timeline_drift",
        target_rule="R-1b",
        target_defect_code="unsupported_claim",
        description="Injects unanchored timeline events pointing to nonexistent transactions.",
        fn=timeline_drift_mutator,
    ),
}


def apply_mutator(finding: dict[str, Any], mutator_name: str) -> dict[str, Any]:
    """Apply a named mutator from the registry to a finding."""
    if mutator_name not in MUTATOR_REGISTRY:
        raise KeyError(
            f"Unknown mutator: {mutator_name!r}. Available: {sorted(MUTATOR_REGISTRY)}"
        )
    return MUTATOR_REGISTRY[mutator_name].fn(finding)


def list_mutator_names() -> list[str]:
    """Return the list of registered mutator names."""
    return list(MUTATOR_REGISTRY.keys())
