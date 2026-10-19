"""The defect taxonomy.

Defect codes are stable identifiers. Free text is never a code. The taxonomy is
loaded from ``contracts/defect-taxonomy.json`` at runtime so that the
documentation, the linter and the contract test suite cannot drift apart.

Two enforcement kinds exist, and the distinction is load-bearing:

``structural``
    Enforced by the contract or by an exact check. A structural defect is a
    fact about the artifact, and it is always ``error`` severity.

``graded``
    A fact about the artifact whose *severity depends on the change context*.
    The canonical case is an expired knowledge citation: it is a hard block when
    promoting new or modified content, and a disclosure on an unchanged
    released artifact (ADR-0006). Graded defects are always ``warn`` in the
    default (release) context and are escalated by the CI gate, not by the
    validator.

``heuristic``
    Detected by a lexical or statistical detector. A heuristic is a detector,
    not a proof, so it is reported at ``warn`` severity. In particular the
    culpability lint is *heuristic*: no keyword filter can prevent a semantic
    misstatement, and pretending otherwise would produce a false sense of
    security. The real defense against a semantic misstatement is structural —
    the ``epistemic_type`` pairing rules in :mod:`fincrime_core.validate.claim_lints`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

from fincrime_core.paths import contracts_dir

__all__ = ["Defect", "DefectInfo", "load_defect_taxonomy", "DEFECT_CODES"]

#: Canonical defect codes. Kept as a module constant so that a typo in a lint
#: is a test failure rather than a silently new code.
DEFECT_CODES: tuple[str, ...] = (
    "unsupported_claim",
    "misclassified_claim",
    "missing_benign_reading",
    "missing_gap",
    "overstated_confidence",
    "contradiction_ignored",
    "recommendation_without_basis",
    "provenance_gap",
    "escalation_missed",
    "jurisdiction_overreach",
    "missing_draft_notice",
    "conflicting_draft_notice",
    "unknown_indicator",
    "expired_knowledge_citation",
    "over_broad_citation",
    "malformed_evidence_ref",
    "schema_violation",
    "decisive_gap_unacknowledged",
)

_CONTRACTS_DIR = contracts_dir()


@dataclass(frozen=True, slots=True)
class DefectInfo:
    """Static metadata about a defect code."""

    code: str
    name: str
    severity: str
    description: str
    remediation: str
    enforcement: str

    @property
    def is_structural(self) -> bool:
        return self.enforcement == "structural"

    @property
    def is_graded(self) -> bool:
        return self.enforcement == "graded"

    @property
    def is_heuristic(self) -> bool:
        return self.enforcement == "heuristic"


@dataclass(frozen=True, slots=True)
class Defect:
    """A single validation finding."""

    code: str
    severity: str
    message: str
    claim_id: str | None = None
    rule_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
        }
        if self.claim_id:
            payload["claim_id"] = self.claim_id
        if self.rule_id:
            payload["rule_id"] = self.rule_id
        return payload

    def sort_key(self) -> tuple[str, int, str, str]:
        """A deterministic ordering key.

        Defects are ordered by severity (errors first), then by claim id, then
        by code, then by message. Determinism matters: the validator's output
        is diffed between runs and between model versions, and a reordering
        would masquerade as a behavioural change.
        """
        severity_rank = {"error": 0, "warn": 1, "info": 2}
        return (
            severity_rank.get(self.severity, 3),
            self.claim_id or "",
            self.code,
            self.message,
        )


@lru_cache(maxsize=1)
def load_defect_taxonomy(path: str | None = None) -> dict[str, DefectInfo]:
    """Load the defect taxonomy from ``contracts/defect-taxonomy.json``.

    Falls back to a built-in minimal taxonomy when the contracts directory is
    not present (for example when the package is installed as a wheel without
    the repository alongside it). The fallback is intentionally incomplete and
    is covered by a test that asserts the packaged taxonomy is complete.
    """
    target = Path(path) if path else _CONTRACTS_DIR / "defect-taxonomy.json"
    raw: Mapping[str, Any] = {}
    if target.exists():
        with target.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
    entries = raw.get("defects") or []
    if not entries:
        entries = [
            {
                "code": "schema_violation",
                "name": "Schema violation",
                "severity": "error",
                "description": "The artifact does not satisfy the Finding Contract.",
                "remediation": "Correct the artifact so it validates.",
                "enforcement": "structural",
            }
        ]
    return {
        entry["code"]: DefectInfo(
            code=entry["code"],
            name=entry["name"],
            severity=entry.get("severity", "error"),
            description=entry.get("description", ""),
            remediation=entry.get("remediation", ""),
            enforcement=entry.get("enforcement", "structural"),
        )
        for entry in entries
    }
