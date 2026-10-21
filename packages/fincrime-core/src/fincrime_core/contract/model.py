"""Typed models for the Finding Contract.

Standard-library ``dataclasses`` only, per ADR-0002: the core must have zero
required runtime dependencies. The models here are a convenience layer over the
JSON Schemas in ``contracts/``; the schemas remain the normative definition, and
``fincrime_core.contract.loader`` parses documents into these types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

__all__ = [
    "CLAIM_CLASSES",
    "EPISTEMIC_TYPES",
    "CONFIDENCE_LEVELS",
    "FINDING_ELEMENTS",
    "Claim",
    "Confidence",
    "Provenance",
    "Artifact",
    "EvidenceItem",
    "Gap",
    "Contradiction",
    "TimelineEntry",
    "DecisionRequest",
    "Finding",
]

#: The closed enum of claim classes. Mirrors ``contracts/finding.schema.json``.
CLAIM_CLASSES: tuple[str, ...] = (
    "fact",
    "observation",
    "indicator",
    "hypothesis",
    "risk_assessment",
    "recommendation",
    "decision",
)

#: The output elements a skill may be required to produce: the seven claim
#: classes, plus the structural elements of the Finding Contract that are not
#: claims but are part of an artifact (the frame, the evidence inventory, the
#: gap list, the escalation).
#:
#: A skill declares what it produces against this vocabulary, so that a
#: manifest cannot name an output nobody can produce and a reader of the
#: manifest knows exactly what the artifact will contain.
FINDING_ELEMENTS: tuple[str, ...] = CLAIM_CLASSES + (
    "frame",
    "evidence_inventory",
    "gaps",
    "contradiction",
    "timeline",
    "escalation",
    "draft_notice",
)

#: The closed enum of hypothesis epistemic types (Part 5.1.1 of the blueprint).
#: This is the structural defense against a lexical culpability filter being
#: bypassed by soft synonyms.
EPISTEMIC_TYPES: tuple[str, ...] = (
    "benign_reading",
    "adverse_reading",
    "data_gap",
    "other",
)

#: Confidence levels. ``insufficient_information`` is a first-class, successful
#: terminal state, not a failure.
CONFIDENCE_LEVELS: tuple[str, ...] = (
    "high",
    "moderate",
    "low",
    "insufficient_information",
)

_CONFIDENCE_ORDER = {name: index for index, name in enumerate(CONFIDENCE_LEVELS)}


@dataclass(frozen=True, slots=True)
class Confidence:
    """A structured confidence statement. Never a bare number, never free text."""

    level: str
    basis: str
    would_be_raised_by: tuple[str, ...] = ()
    ceiling: str | None = None

    def __post_init__(self) -> None:
        if self.level not in CONFIDENCE_LEVELS:
            raise ValueError(f"invalid confidence level: {self.level!r}")

    @property
    def rank(self) -> int:
        """Ordinal rank, used for ceiling comparisons. Lower is more confident."""
        return _CONFIDENCE_ORDER[self.level]

    def at_or_above(self, other: str) -> bool:
        """True when this confidence is at least as strong as ``other``."""
        return self.rank <= _CONFIDENCE_ORDER[other]

    def apply_ceiling(self, ceiling: str) -> "Confidence":
        """Return a copy whose level is capped at ``ceiling``.

        Used when a knowledge pack is stale or the evidence set is partial: the
        agent cannot claim more confidence than the evidence supports, and the
        cap is applied by the validator rather than requested by the model.
        """
        if self.rank <= _CONFIDENCE_ORDER[ceiling]:
            return self
        return Confidence(
            level=ceiling,
            basis=self.basis,
            would_be_raised_by=self.would_be_raised_by,
            ceiling=ceiling,
        )


@dataclass(frozen=True, slots=True)
class Claim:
    """One typed assertion inside a finding."""

    id: str
    class_: str
    statement: str
    confidence: Confidence
    evidence_refs: tuple[str, ...] = ()
    indicator_ids: tuple[str, ...] = ()
    policy_ids: tuple[str, ...] = ()
    knowledge_ids: tuple[str, ...] = ()
    jurisdictions: tuple[str, ...] = ()
    epistemic_type: str | None = None
    falsifier: str | None = None
    competing_with: tuple[str, ...] = ()
    decided_by: str | None = None
    human_approval_required: bool | None = None
    explains: tuple[str, ...] = ()
    carried_forward_from: str | None = None

    def __post_init__(self) -> None:
        if self.class_ not in CLAIM_CLASSES:
            raise ValueError(f"invalid claim class: {self.class_!r}")
        if self.epistemic_type is not None and self.epistemic_type not in EPISTEMIC_TYPES:
            raise ValueError(f"invalid epistemic_type: {self.epistemic_type!r}")

    @property
    def requires_evidence(self) -> bool:
        """True for claim classes that MUST carry at least one evidence reference.

        This is a *mandate*: a fact, observation or indicator cannot stand
        without a reference. It is not a statement about what happens to
        references that are present on other classes.
        """
        return self.class_ in ("fact", "observation", "indicator")

    @property
    def cites_evidence(self) -> bool:
        """True when the claim carries at least one evidence reference."""
        return bool(self.evidence_refs)

    @property
    def is_evidence_bearing(self) -> bool:
        """True when the claim is subject to evidence-attribution checking.

        A claim that carries references is always subject to it, whatever its
        class. A fabricated reference on a risk assessment or a recommendation
        is exactly the failure this project exists to prevent, and it must not
        be able to hide behind a class that does not *mandate* evidence.
        """
        return self.requires_evidence or self.cites_evidence

    @property
    def is_hypothesis(self) -> bool:
        return self.class_ == "hypothesis"


@dataclass(frozen=True, slots=True)
class Artifact:
    """Header identifying what produced the finding and under what scope."""

    skill_id: str
    skill_version: str
    artifact_type: str
    subject_ids: tuple[str, ...]
    jurisdictions: tuple[str, ...]
    created_at: str
    completeness: str
    scope_note: str | None = None
    knowledge_stale: bool = False


@dataclass(frozen=True, slots=True)
class ModelRef:
    provider: str
    id: str
    temperature: float | None = None
    seed: int | None = None


@dataclass(frozen=True, slots=True)
class KnowledgePackRef:
    id: str
    version: str
    as_of: str
    stale: bool = False


@dataclass(frozen=True, slots=True)
class PolicySetRef:
    id: str
    version: str


@dataclass(frozen=True, slots=True)
class Provenance:
    """The audit chain. A reader must be able to establish what was seen, what
    was used, and when the regulatory basis was current."""

    skill_id: str
    skill_version: str
    model: ModelRef
    prompt_sha256: str
    evidence_set_sha256: str
    knowledge_pack: KnowledgePackRef
    policy_set: PolicySetRef
    run_id: str
    timestamp: str


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    source_id: str
    kind: str
    present: bool
    summary: str | None = None
    decisive: bool = False
    note: str | None = None


@dataclass(frozen=True, slots=True)
class Gap:
    gap_id: str
    description: str
    decisive: bool = False
    blocks_conclusion: bool = False
    request_ref: str | None = None


@dataclass(frozen=True, slots=True)
class Contradiction:
    contradiction_id: str
    description: str
    status: str
    claim_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TimelineEntry:
    timestamp: str
    description: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DecisionRequest:
    """A decision the agent explicitly did not make."""

    decision_id: str
    question: str
    owner_role: str
    would_change_if: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Finding:
    """A complete artifact. ``claims`` is the spine; everything else is context."""

    contract_version: str
    artifact: Artifact
    provenance: Provenance
    claims: tuple[Claim, ...]
    human_decision_required: tuple[DecisionRequest, ...]
    evidence_inventory: tuple[EvidenceItem, ...] = ()
    gaps: tuple[Gap, ...] = ()
    contradictions: tuple[Contradiction, ...] = ()
    timeline: tuple[TimelineEntry, ...] = ()
    draft_notice: Mapping[str, Any] | None = None
    validation: Mapping[str, Any] | None = None

    def claims_of_class(self, class_: str) -> tuple[Claim, ...]:
        """All claims of a given class, in document order."""
        return tuple(c for c in self.claims if c.class_ == class_)

    @property
    def hypotheses(self) -> tuple[Claim, ...]:
        return self.claims_of_class("hypothesis")

    @property
    def has_benign_reading(self) -> bool:
        """True when at least one hypothesis is explicitly typed as a benign reading."""
        return any(h.epistemic_type == "benign_reading" for h in self.hypotheses)

    @property
    def has_adverse_reading(self) -> bool:
        return any(h.epistemic_type == "adverse_reading" for h in self.hypotheses)

    @property
    def decisive_gaps(self) -> tuple[Gap, ...]:
        return tuple(g for g in self.gaps if g.decisive)
