"""Parse a Finding Contract document into typed models.

The JSON Schemas in ``contracts/`` are normative. This loader is a convenience
that produces the dataclasses in :mod:`fincrime_core.contract.model`. It is
deliberately permissive about *shape* (it reports what it can) and strict about
*values* (an invalid enum raises), because the validator's job is to report
defects, not to crash on a bad artifact.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from fincrime_core.contract.model import (
    Artifact,
    Claim,
    Confidence,
    Contradiction,
    DecisionRequest,
    EvidenceItem,
    Finding,
    Gap,
    KnowledgePackRef,
    ModelRef,
    PolicySetRef,
    Provenance,
    TimelineEntry,
)

__all__ = ["parse_finding", "parse_confidence", "parse_claim", "parse_artifact", "parse_provenance"]


def _as_str_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(str(item) for item in value)
    return ()


def parse_confidence(raw: Any) -> Confidence:
    """Parse a confidence object, defaulting to the lowest level when absent."""
    if not isinstance(raw, Mapping):
        return Confidence(level="insufficient_information", basis="no confidence supplied")
    return Confidence(
        level=str(raw.get("level", "insufficient_information")),
        basis=str(raw.get("basis", "")),
        would_be_raised_by=_as_str_tuple(raw.get("would_be_raised_by")),
        ceiling=raw.get("ceiling"),
    )


def parse_claim(raw: Mapping[str, Any]) -> Claim:
    """Parse one claim."""
    return Claim(
        id=str(raw.get("id", "")),
        class_=str(raw.get("class", "")),
        statement=str(raw.get("statement", "")),
        confidence=parse_confidence(raw.get("confidence")),
        evidence_refs=_as_str_tuple(raw.get("evidence_refs")),
        indicator_ids=_as_str_tuple(raw.get("indicator_ids")),
        policy_ids=_as_str_tuple(raw.get("policy_ids")),
        knowledge_ids=_as_str_tuple(raw.get("knowledge_ids")),
        jurisdictions=_as_str_tuple(raw.get("jurisdictions")),
        epistemic_type=raw.get("epistemic_type"),
        falsifier=raw.get("falsifier"),
        competing_with=_as_str_tuple(raw.get("competing_with")),
        decided_by=raw.get("decided_by"),
        human_approval_required=raw.get("human_approval_required"),
        explains=_as_str_tuple(raw.get("explains")),
        carried_forward_from=raw.get("carried_forward_from"),
    )


def parse_artifact(raw: Mapping[str, Any]) -> Artifact:
    """Parse the artifact header."""
    return Artifact(
        skill_id=str(raw.get("skill_id", "")),
        skill_version=str(raw.get("skill_version", "")),
        artifact_type=str(raw.get("artifact_type", "")),
        subject_ids=_as_str_tuple(raw.get("subject_ids")),
        jurisdictions=_as_str_tuple(raw.get("jurisdictions")),
        created_at=str(raw.get("created_at", "")),
        completeness=str(raw.get("completeness", "complete")),
        scope_note=raw.get("scope_note"),
        knowledge_stale=bool(raw.get("knowledge_stale", False)),
    )


def _as_mapping(value: Any) -> Mapping[str, Any]:
    """Coerce a value to a mapping, tolerating a malformed nested object.

    The loader must not raise on a malformed artifact. A validator that
    crashes on a bad artifact is a denial of service on exactly the artifacts
    an analyst most needs to inspect.
    """
    return value if isinstance(value, Mapping) else {}


def parse_provenance(raw: Mapping[str, Any]) -> Provenance:
    """Parse the provenance chain."""
    model_raw = _as_mapping(raw.get("model"))
    pack_raw = _as_mapping(raw.get("knowledge_pack"))
    policy_raw = _as_mapping(raw.get("policy_set"))
    return Provenance(
        skill_id=str(raw.get("skill_id", "")),
        skill_version=str(raw.get("skill_version", "")),
        model=ModelRef(
            provider=str(model_raw.get("provider", "")),
            id=str(model_raw.get("id", "")),
            temperature=model_raw.get("temperature"),
            seed=model_raw.get("seed"),
        ),
        prompt_sha256=str(raw.get("prompt_sha256", "")),
        evidence_set_sha256=str(raw.get("evidence_set_sha256", "")),
        knowledge_pack=KnowledgePackRef(
            id=str(pack_raw.get("id", "")),
            version=str(pack_raw.get("version", "")),
            as_of=str(pack_raw.get("as_of", "")),
            stale=bool(pack_raw.get("stale", False)),
        ),
        policy_set=PolicySetRef(
            id=str(policy_raw.get("id", "")),
            version=str(policy_raw.get("version", "")),
        ),
        run_id=str(raw.get("run_id", "")),
        timestamp=str(raw.get("timestamp", "")),
    )


def parse_finding(raw: Mapping[str, Any]) -> Finding:
    """Parse a complete finding document.

    Raises ``ValueError`` only for values that cannot be represented at all
    (an unknown claim class or confidence level). Everything else is left for
    the validator to report, so that a malformed artifact is *inspected*
    rather than *rejected*.
    """
    claims = tuple(parse_claim(item) for item in raw.get("claims") or () if isinstance(item, Mapping))
    inventory = tuple(
        EvidenceItem(
            source_id=str(item.get("source_id", "")),
            kind=str(item.get("kind", "")),
            present=bool(item.get("present", False)),
            summary=item.get("summary"),
            decisive=bool(item.get("decisive", False)),
            note=item.get("note"),
        )
        for item in raw.get("evidence_inventory") or ()
        if isinstance(item, Mapping)
    )
    gaps = tuple(
        Gap(
            gap_id=str(item.get("gap_id", "")),
            description=str(item.get("description", "")),
            decisive=bool(item.get("decisive", False)),
            blocks_conclusion=bool(item.get("blocks_conclusion", False)),
            request_ref=item.get("request_ref"),
        )
        for item in raw.get("gaps") or ()
        if isinstance(item, Mapping)
    )
    contradictions = tuple(
        Contradiction(
            contradiction_id=str(item.get("contradiction_id", "")),
            description=str(item.get("description", "")),
            status=str(item.get("status", "")),
            claim_refs=_as_str_tuple(item.get("claim_refs")),
            evidence_refs=_as_str_tuple(item.get("evidence_refs")),
        )
        for item in raw.get("contradictions") or ()
        if isinstance(item, Mapping)
    )
    timeline = tuple(
        TimelineEntry(
            timestamp=str(item.get("timestamp", "")),
            description=str(item.get("description", "")),
            evidence_refs=_as_str_tuple(item.get("evidence_refs")),
        )
        for item in raw.get("timeline") or ()
        if isinstance(item, Mapping)
    )
    decisions = tuple(
        DecisionRequest(
            decision_id=str(item.get("decision_id", "")),
            question=str(item.get("question", "")),
            owner_role=str(item.get("owner_role", "")),
            would_change_if=_as_str_tuple(item.get("would_change_if")),
        )
        for item in raw.get("human_decision_required") or ()
        if isinstance(item, Mapping)
    )

    return Finding(
        contract_version=str(raw.get("contract_version", "")),
        artifact=parse_artifact(_as_mapping(raw.get("artifact"))),
        provenance=parse_provenance(_as_mapping(raw.get("provenance"))),
        claims=claims,
        human_decision_required=decisions,
        evidence_inventory=inventory,
        gaps=gaps,
        contradictions=contradictions,
        timeline=timeline,
        draft_notice=raw.get("draft_notice"),
        validation=raw.get("validation"),
    )
