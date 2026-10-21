"""The top-level validator.

``Validator.validate`` is the single entry point that turns a raw artifact plus
an evidence set into a :class:`ValidationResult`. It is:

* **pure** — no clock, no network, no filesystem beyond reading the contracts,
  no randomness, no global state;
* **total** — it never raises on a malformed artifact; every problem becomes a
  defect;
* **deterministic** — identical inputs produce byte-identical output, which is
  what lets a score be a diff rather than a claim.

The order of checks is fixed and documented, because the defect ordering is
part of the output contract:

1. Schema validation against ``contracts/finding.schema.json``.
2. Evidence-reference resolution (R-1) and claim lints (R-2 .. R-9).
3. Artifact-level lints (escalation, tool-generated notice).
4. Knowledge freshness (graded by enforcement context, per ADR-0006).
5. Policy rule evaluation.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from fincrime_core.contract.loader import parse_finding
from fincrime_core.contract.model import Finding
from fincrime_core.provenance.hashing import hash_evidence_set
from fincrime_core.validate.claim_lints import CulpabilityMatcher, lint_artifact, lint_claims
from fincrime_core.validate.defects import Defect
from fincrime_core.validate.evidence_refs import SourceIndex, build_source_index
from fincrime_core.paths import contracts_dir
from fincrime_core.validate.schema import JsonSchemaValidator, SchemaError

__all__ = ["ValidationResult", "Validator", "EnforcementContext", "load_finding_schema"]

_CONTRACTS_DIR = contracts_dir()

#: Defect codes that supersede a generic schema violation for the same claim.
#: The contract encodes these rules structurally so that a stock JSON Schema
#: validator enforces them too, which produces a generic schema error in
#: addition to the specific lint defect. A consumer keying on defect codes
#: should see the specific code, not both.
_SUPERSEDING_CODES = frozenset({"recommendation_without_basis"})


def _superseded_claim_paths(defects: list[Defect], claims: Sequence[Any]) -> set[str]:
    """Return the JSON paths of claims whose generic schema error is superseded.

    The contract encodes these rules structurally so that a stock JSON Schema
    validator enforces them too, which produces a generic schema error in
    addition to the specific lint defect. A consumer keying on defect codes
    should see the specific code, not both.
    """
    by_claim = {
        d.claim_id for d in defects if d.code in _SUPERSEDING_CODES and d.claim_id
    }
    if not by_claim:
        return set()
    paths: set[str] = set()
    for index, claim in enumerate(claims):
        if getattr(claim, "id", None) in by_claim:
            paths.add(f"$.claims[{index}]")
    return paths


def _path_is_superseded(path: str, superseded: set[str]) -> bool:
    """True when a schema error path is covered by a superseding lint defect."""
    for candidate in superseded:
        if path == candidate or path.startswith(candidate + ".") or path.startswith(candidate + "["):
            return True
    return False


def load_finding_schema(path: str | None = None) -> JsonSchemaValidator:
    """Load the Finding Contract schema as a validator."""
    target = Path(path) if path else _CONTRACTS_DIR / "finding.schema.json"
    with target.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    return JsonSchemaValidator(schema)


#: Enforcement context identifiers. These are module-level constants because a
#: class body's default argument cannot reference the class being defined.
RELEASE_CONTEXT = "release"
"""Existing released content: stale knowledge is disclosed, not blocked."""

PROMOTION_CONTEXT = "promotion"
"""New or modified content: stale knowledge is a hard block."""


class EnforcementContext:
    """How strictly a knowledge-freshness finding should be enforced.

    Per ADR-0006, enforcement strictness depends on the *change type*, not on
    the staleness alone. A released skill that has not changed is warned about;
    promoting new work against expired knowledge is blocked.
    """

    RELEASE = RELEASE_CONTEXT
    PROMOTION = PROMOTION_CONTEXT

    def __init__(self, mode: str = RELEASE_CONTEXT) -> None:
        if mode not in (RELEASE_CONTEXT, PROMOTION_CONTEXT):
            raise ValueError(f"unknown enforcement context: {mode!r}")
        self.mode = mode

    @property
    def blocks_on_stale(self) -> bool:
        return self.mode == PROMOTION_CONTEXT


@dataclass(slots=True)
class ValidationResult:
    """The outcome of validating one artifact."""

    valid: bool
    defects: list[Defect] = field(default_factory=list)
    schema_errors: list[SchemaError] = field(default_factory=list)
    evidence_set_sha256: str = ""
    resolved_refs: dict[str, bool] = field(default_factory=dict)

    @property
    def errors(self) -> list[Defect]:
        return [d for d in self.defects if d.severity == "error"]

    @property
    def warnings(self) -> list[Defect]:
        return [d for d in self.defects if d.severity == "warn"]

    @property
    def error_codes(self) -> tuple[str, ...]:
        return tuple(d.code for d in self.errors)

    @property
    def unsupported_claim_rate(self) -> float:
        """Fraction of evidence-bearing claims that failed attribution.

        This is one of the project's headline metrics. It is computed
        deterministically: a claim counts as unsupported when it is of a class
        that mandates evidence and has none, or when any reference it carries
        fails to resolve.

        The denominator is every *evidence-bearing* claim, not only the
        classes that mandate evidence. A risk assessment or a recommendation
        that cites a fabricated reference is unsupported, and excluding it
        would let the failure hide behind the claim class.
        """
        bearing = [c for c in self._claims if c.is_evidence_bearing]
        if not bearing:
            return 0.0
        unsupported = 0
        for claim in bearing:
            if claim.requires_evidence and not claim.evidence_refs:
                unsupported += 1
                continue
            if any(not self.resolved_refs.get(ref, False) for ref in claim.evidence_refs):
                unsupported += 1
        return unsupported / len(bearing)

    @property
    def evidence_attribution_accuracy(self) -> float:
        """Complement of :attr:`unsupported_claim_rate` over evidence-requiring claims."""
        return 1.0 - self.unsupported_claim_rate

    _claims: Sequence[Any] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "defects": [d.to_dict() for d in self.defects],
            "schema_errors": [
                {"path": e.path, "message": e.message, "keyword": e.keyword} for e in self.schema_errors
            ],
            "metrics": {
                "unsupported_claim_rate": self.unsupported_claim_rate,
                "evidence_attribution_accuracy": self.evidence_attribution_accuracy,
                "error_count": len(self.errors),
                "warning_count": len(self.warnings),
            },
        }


class Validator:
    """Validates artifacts against the Finding Contract.

    The validator is constructed with the evidence set, because the evidence
    set is the closed world: a claim can only cite what the analyst actually
    had.
    """

    __slots__ = (
        "_evidence_set",
        "_source_index",
        "_schema",
        "_matcher",
        "_known_indicator_ids",
        "_known_knowledge_ids",
        "_expired_knowledge_ids",
        "_allowed_jurisdictions",
    )

    def __init__(
        self,
        evidence_set: Mapping[str, Any] | None = None,
        schema: JsonSchemaValidator | None = None,
        matcher: CulpabilityMatcher | None = None,
        known_indicator_ids: Sequence[str] | None = None,
        known_knowledge_ids: Sequence[str] | None = None,
        expired_knowledge_ids: Sequence[str] | None = None,
        allowed_jurisdictions: Sequence[str] | None = None,
    ) -> None:
        self._evidence_set = dict(evidence_set or {})
        self._source_index: SourceIndex = build_source_index(self._evidence_set)
        self._schema = schema or load_finding_schema()
        self._matcher = matcher or CulpabilityMatcher()
        self._known_indicator_ids = known_indicator_ids
        self._known_knowledge_ids = known_knowledge_ids
        self._expired_knowledge_ids = set(expired_knowledge_ids or ())
        self._allowed_jurisdictions = allowed_jurisdictions

    @property
    def source_index(self) -> SourceIndex:
        return self._source_index

    def validate(
        self,
        artifact: Mapping[str, Any],
        enforcement: EnforcementContext | None = None,
    ) -> ValidationResult:
        """Validate a raw artifact document. Never raises."""
        enforcement = enforcement or EnforcementContext(EnforcementContext.RELEASE)

        schema_errors = self._schema.validate(artifact)
        defects: list[Defect] = []

        for error in schema_errors:
            defects.append(
                Defect(
                    code="schema_violation",
                    severity="error",
                    message=f"{error.path}: {error.message}",
                    rule_id=error.keyword,
                )
            )

        try:
            finding = parse_finding(artifact)
        except ValueError as exc:
            defects.append(
                Defect(
                    code="schema_violation",
                    severity="error",
                    message=f"artifact could not be parsed into the contract model: {exc}",
                )
            )
            return self._finalise(defects, schema_errors, [])

        resolved: dict[str, bool] = {}
        for claim in finding.claims:
            for ref in claim.evidence_refs:
                if ref in resolved:
                    continue
                resolved[ref] = self._source_index.resolve(ref).ok

        # Timeline references are resolved too, so that the outcome of R-1b is
        # observable in the result and not only as a defect.
        for entry in finding.timeline:
            for ref in entry.evidence_refs:
                if ref in resolved:
                    continue
                resolved[ref] = self._source_index.resolve(ref).ok

        defects.extend(
            lint_claims(
                finding,
                self._source_index,
                known_indicator_ids=self._known_indicator_ids,
                known_knowledge_ids=self._known_knowledge_ids,
                matcher=self._matcher,
            )
        )
        defects.extend(lint_artifact(finding, allowed_jurisdictions=self._allowed_jurisdictions))
        defects.extend(self._check_knowledge_freshness(finding, enforcement))

        # Drop the generic schema error for any condition a specific lint has
        # already reported with an actionable code.
        superseded = _superseded_claim_paths(defects, finding.claims)
        if superseded:
            schema_errors = [
                error for error in schema_errors if not _path_is_superseded(error.path, superseded)
            ]
            defects = [
                defect
                for defect in defects
                if not (
                    defect.code == "schema_violation"
                    and any(
                        defect.message.startswith(path + ":") for path in superseded
                    )
                )
            ]

        return self._finalise(defects, schema_errors, finding.claims, resolved)

    def _check_knowledge_freshness(
        self, finding: Finding, enforcement: EnforcementContext
    ) -> list[Defect]:
        """Flag citations of expired knowledge records (ADR-0006)."""
        if not self._expired_knowledge_ids:
            return []
        defects: list[Defect] = []
        cited: set[str] = set()
        for claim in finding.claims:
            cited.update(claim.knowledge_ids)
        for knowledge_id in sorted(cited & self._expired_knowledge_ids):
            severity = "error" if enforcement.blocks_on_stale else "warn"
            defects.append(
                Defect(
                    code="expired_knowledge_citation",
                    severity=severity,
                    message=(
                        f"Artifact cites knowledge record {knowledge_id!r}, which has passed its expiry date. "
                        + (
                            "This blocks promotion of new or modified content."
                            if enforcement.blocks_on_stale
                            else "This is disclosed in the conformance report and the skill is marked MAINTENANCE_REQUIRED."
                        )
                    ),
                    rule_id="KNOW-1",
                )
            )
        return defects

    @staticmethod
    def _finalise(
        defects: list[Defect],
        schema_errors: list[SchemaError],
        claims: Sequence[Any],
        resolved: Mapping[str, bool] | None = None,
    ) -> ValidationResult:
        ordered = sorted(defects, key=lambda d: d.sort_key())
        result = ValidationResult(
            valid=not any(d.severity == "error" for d in ordered),
            defects=ordered,
            schema_errors=list(schema_errors),
            resolved_refs=dict(resolved or {}),
        )
        result._claims = list(claims)
        return result
