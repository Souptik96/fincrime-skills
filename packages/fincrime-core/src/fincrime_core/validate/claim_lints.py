"""Claim lints: the rules that make evidence discipline checkable.

The lints fall into two tiers, and the tiering is the point.

**Structural lints (R-1 .. R-9) are the real defense.** They are exact
checks over typed fields. A claim of class ``fact`` with no resolvable evidence
reference does not validate, regardless of how the prose reads. A hypothesis
that is typed as an ``adverse_reading`` cannot stand alone: the artifact must
contain a ``benign_reading`` hypothesis. This is what prevents a model from
asserting criminality by soft synonym, because the *structure* of the artifact
is checked, not its vocabulary.

**The culpability lint (R-6) is heuristic.** A deny-list catches accidents.
It cannot prevent a semantic misstatement, and it will produce false positives
on legitimate phrasing ("not suspected of structuring", "structured data"). It
is therefore reported at ``warn`` severity, is negation-aware, and is held to a
zero-false-positive standard on the golden corpus. Its role is to catch what
the structural rules cannot see, and to be honest about its own limits.

The lints are pure functions. They read the artifact, the evidence index and
the knowledge index, and return defects. They never mutate and never raise.
"""

from __future__ import annotations

import re
from typing import Iterable, Mapping, Sequence

from fincrime_core.contract.model import Claim, Confidence, Finding
from fincrime_core.validate.defects import Defect
from fincrime_core.validate.evidence_refs import SourceIndex

__all__ = [
    "CulpabilityMatcher",
    "lint_claims",
    "lint_artifact",
    "DEFAULT_CULPABILITY_PATTERNS",
]

#: Culpability phrases that assert or imply criminality of the subject.
#:
#: Deliberately narrow. A broad list produces false positives, and a lint that
#: cries wolf is worse than no lint, because it trains reviewers to ignore it.
#: The structural ``epistemic_type`` rules are the primary defense; this list
#: catches the common failure of writing the conclusion into an observation.
DEFAULT_CULPABILITY_PATTERNS: tuple[str, ...] = (
    r"\bis\s+a\s+money\s+launderer\b",
    r"\bis\s+a\s+money\s+mule\b",
    r"\bis\s+a\s+drug\s+dealer\b",
    r"\bis\s+a\s+trafficker\b",
    r"\bis\s+guilty\s+of\b",
    r"\bcommitted\s+(?:money\s+laundering|laundering|fraud|theft)\b",
    r"\bproceeds\s+of\s+crime\b",
    r"\bcriminal\s+enterprise\b",
    r"\bsanctioned\s+(?:person|individual|party|entity)\b",
    r"\bacted\s+to\s+evade\b",
)

#: Phrases that neutralise a match when they appear in the same clause. Used to
#: keep the heuristic from firing on negated or quoted statements.
_NEGATION_CUES: tuple[str, ...] = (
    "not ",
    "no evidence",
    "never ",
    "cannot ",
    "does not ",
    "did not ",
    "without ",
    "rather than ",
    "instead of ",
    "unclear whether",
    "cannot be determined",
    "no basis to conclude",
    "not suspected",
    "is not established",
)


class CulpabilityMatcher:
    """Negation-aware matcher for culpability phrasing.

    The matcher scans a statement sentence by sentence. A sentence is skipped
    when it carries a negation cue, because "the account is not structuring"
    must not be reported as a culpability assertion. The matcher is
    deterministic and side-effect free.
    """

    __slots__ = ("_patterns",)

    def __init__(self, patterns: Iterable[str] | None = None) -> None:
        source = tuple(patterns) if patterns is not None else DEFAULT_CULPABILITY_PATTERNS
        self._patterns: tuple[re.Pattern[str], ...] = tuple(
            re.compile(pattern, re.IGNORECASE) for pattern in source
        )

    def find(self, statement: str) -> list[str]:
        """Return the patterns that matched ``statement``, ignoring negated clauses."""
        if not statement:
            return []
        hits: list[str] = []
        for sentence in re.split(r"(?<=[.;!?])\s+", statement):
            lowered = sentence.lower()
            if any(cue in lowered for cue in _NEGATION_CUES):
                continue
            for pattern in self._patterns:
                if pattern.search(sentence):
                    hits.append(pattern.pattern)
        return hits

    def is_clean(self, statement: str) -> bool:
        return not self.find(statement)


def _defect(code: str, message: str, claim_id: str | None = None, rule_id: str | None = None) -> Defect:
    return Defect(code=code, severity="error", message=message, claim_id=claim_id, rule_id=rule_id)


def _warn(code: str, message: str, claim_id: str | None = None, rule_id: str | None = None) -> Defect:
    return Defect(code=code, severity="warn", message=message, claim_id=claim_id, rule_id=rule_id)


def _confidence_of(claim: Claim) -> Confidence:
    return claim.confidence


def lint_claims(
    finding: Finding,
    source_index: SourceIndex,
    known_indicator_ids: Sequence[str] | None = None,
    known_knowledge_ids: Sequence[str] | None = None,
    matcher: CulpabilityMatcher | None = None,
) -> list[Defect]:
    """Run the per-claim lints over a finding.

    Parameters
    ----------
    finding:
        The artifact under inspection.
    source_index:
        The closed world of evidence. References are resolved against it.
    known_indicator_ids:
        Indicator ids present in the declared knowledge pack. When ``None`` the
        indicator-existence check is skipped (it cannot be evaluated).
    known_knowledge_ids:
        Knowledge record ids present in the declared pack. Same convention.
    matcher:
        Culpability matcher. Defaults to the standard pattern set.
    """
    defects: list[Defect] = []
    matcher = matcher or CulpabilityMatcher()
    indicator_ids = set(known_indicator_ids) if known_indicator_ids is not None else None
    knowledge_ids = set(known_knowledge_ids) if known_knowledge_ids is not None else None

    claims = finding.claims
    by_id = {claim.id: claim for claim in claims}

    for claim in claims:
        # R-1: fact / observation / indicator require a resolvable evidence ref.
        if claim.requires_evidence:
            if not claim.evidence_refs:
                defects.append(
                    _defect(
                        "unsupported_claim",
                        f"Claim {claim.id} is of class '{claim.class_}' and carries no evidence reference.",
                        claim.id,
                        "R-1",
                    )
                )
            else:
                for ref in claim.evidence_refs:
                    resolution = source_index.resolve(ref)
                    if not resolution.ok:
                        code = {
                            "over_broad_citation": "over_broad_citation",
                            "malformed_ref": "malformed_evidence_ref",
                        }.get(resolution.error_code or "", "unsupported_claim")
                        defects.append(
                            _defect(
                                code,
                                f"Claim {claim.id} cites {ref!r} which does not resolve: "
                                f"{resolution.error_message}",
                                claim.id,
                                "R-1",
                            )
                        )

        # R-2: an indicator must name an indicator id that exists in the pack.
        if claim.class_ == "indicator":
            if not claim.indicator_ids:
                defects.append(
                    _defect(
                        "unsupported_claim",
                        f"Claim {claim.id} is an indicator but names no indicator id.",
                        claim.id,
                        "R-2",
                    )
                )
            elif indicator_ids is not None:
                for indicator_id in claim.indicator_ids:
                    if indicator_id not in indicator_ids:
                        defects.append(
                            _defect(
                                "unknown_indicator",
                                f"Claim {claim.id} names indicator {indicator_id!r}, which is not present "
                                "in the declared knowledge pack.",
                                claim.id,
                                "R-2",
                            )
                        )

        # R-2b: a cited knowledge id must exist in the declared pack.
        if knowledge_ids is not None:
            for knowledge_id in claim.knowledge_ids:
                if knowledge_id not in knowledge_ids:
                    defects.append(
                        _defect(
                            "unsupported_claim",
                            f"Claim {claim.id} cites knowledge record {knowledge_id!r}, which is not present "
                            "in the declared knowledge pack.",
                            claim.id,
                            "R-2",
                        )
                    )

        # R-3 / R-3a: a hypothesis needs a falsifier and a valid epistemic type.
        if claim.class_ == "hypothesis":
            if not claim.falsifier:
                defects.append(
                    _defect(
                        "misclassified_claim",
                        f"Hypothesis {claim.id} carries no falsifier.",
                        claim.id,
                        "R-3",
                    )
                )
            if claim.epistemic_type is None:
                defects.append(
                    _defect(
                        "misclassified_claim",
                        f"Hypothesis {claim.id} carries no epistemic_type; it must be one of "
                        "benign_reading, adverse_reading, data_gap, other.",
                        claim.id,
                        "R-3a",
                    )
                )

        # R-3b: an adverse reading may not stand alone. This is the structural
        # defense that a keyword filter cannot provide.
        if claim.class_ == "hypothesis" and claim.epistemic_type == "adverse_reading":
            has_benign = any(
                other.class_ == "hypothesis" and other.epistemic_type == "benign_reading"
                for other in claims
            )
            if not has_benign:
                defects.append(
                    _defect(
                        "missing_benign_reading",
                        f"Hypothesis {claim.id} is typed as an adverse_reading but the artifact contains no "
                        "benign_reading hypothesis. An adverse reading may not stand alone.",
                        claim.id,
                        "R-3b",
                    )
                )

        # R-3d: an adverse reading at high confidence when decisive evidence is
        # absent is an overstatement.
        if (
            claim.class_ == "hypothesis"
            and claim.epistemic_type == "adverse_reading"
            and claim.confidence.level == "high"
            and finding.decisive_gaps
        ):
            defects.append(
                _defect(
                    "overstated_confidence",
                    f"Hypothesis {claim.id} is an adverse_reading stated at high confidence while the artifact "
                    "records a decisive evidence gap.",
                    claim.id,
                    "R-3d",
                )
            )

        # R-4: a risk assessment with no indicator must say it is insufficient.
        if claim.class_ == "risk_assessment" and not claim.evidence_refs:
            if claim.confidence.level != "insufficient_information":
                defects.append(
                    _defect(
                        "misclassified_claim",
                        f"Risk assessment {claim.id} carries no evidence reference and therefore must be "
                        "stated as insufficient_information.",
                        claim.id,
                        "R-4",
                    )
                )

        # R-5: a decision must be attributable to a human or a deterministic policy.
        if claim.class_ == "decision" and not claim.decided_by:
            defects.append(
                _defect(
                    "provenance_gap",
                    f"Decision {claim.id} carries no decided_by, so it is not attributable to a human or a policy.",
                    claim.id,
                    "R-5",
                )
            )

        # R-7: a recommendation that could affect a customer must require approval.
        if claim.class_ == "recommendation" and claim.human_approval_required is False:
            defects.append(
                _defect(
                    "escalation_missed",
                    f"Recommendation {claim.id} declares that no human approval is required. The skill layer "
                    "may never assert that.",
                    claim.id,
                    "R-7",
                )
            )

        # R-6: heuristic culpability detection. Warn severity by design.
        hits = matcher.find(claim.statement)
        if hits:
            defects.append(
                _warn(
                    "unsupported_claim",
                    f"Claim {claim.id} contains phrasing that may assert criminality of the subject "
                    f"(matched: {', '.join(sorted(set(hits)))}). Verify manually; this is a heuristic, not a proof.",
                    claim.id,
                    "R-6",
                )
            )

    # R-8: a partial evidence set caps the confidence of every *conclusion*
    # drawn from it. It does not cap the confidence of a fact read directly
    # from a record that is present: that fact is complete in itself. What a
    # partial window undermines is the inference that the window supports.
    if finding.artifact.completeness == "partial":
        for claim in claims:
            if (
                claim.confidence.level == "high"
                and claim.class_ in ("indicator", "hypothesis", "risk_assessment", "recommendation")
            ):
                defects.append(
                    _defect(
                        "overstated_confidence",
                        f"Claim {claim.id} is a {claim.class_} stated at high confidence while the evidence set is "
                        "partial. A conclusion drawn from an incomplete window cannot be stated with high confidence.",
                        claim.id,
                        "R-8",
                    )
                )

    # R-9: competing_with links must point at real hypotheses.
    for claim in claims:
        for other_id in claim.competing_with:
            other = by_id.get(other_id)
            if other is None:
                defects.append(
                    _defect(
                        "provenance_gap",
                        f"Claim {claim.id} declares it competes with {other_id!r}, which is not a claim in this "
                        "artifact.",
                        claim.id,
                        "R-9",
                    )
                )
            elif other.class_ != "hypothesis":
                defects.append(
                    _defect(
                        "misclassified_claim",
                        f"Claim {claim.id} declares it competes with {other_id!r}, which is not a hypothesis.",
                        claim.id,
                        "R-9",
                    )
                )

    return defects


def lint_artifact(finding: Finding) -> list[Defect]:
    """Artifact-level lints that do not depend on the evidence set.

    Covers the tool-generated notice requirement (ADR-0009) and the escalation
    requirement.
    """
    defects: list[Defect] = []

    # A finding must name at least one decision the agent did not make.
    if not finding.human_decision_required:
        defects.append(
            _defect(
                "escalation_missed",
                "The artifact names no human decision, so it does not make clear what the human still owns.",
                None,
                "ART-1",
            )
        )

    # ADR-0009: a sar_narrative must carry the tool-generated draft notice.
    if finding.artifact.artifact_type == "sar_narrative":
        notice = finding.draft_notice
        if not notice:
            defects.append(
                _defect(
                    "missing_draft_notice",
                    "A sar_narrative artifact must carry the tool-generated draft notice.",
                    None,
                    "R-NOTICE-1",
                )
            )
        else:
            if not notice.get("tool_generated"):
                defects.append(
                    _defect(
                        "missing_draft_notice",
                        "The draft notice is not marked tool_generated, so it cannot be trusted to be "
                        "non-strippable.",
                        None,
                        "R-NOTICE-2",
                    )
                )
            if not str(notice.get("text", "")).strip():
                defects.append(
                    _defect(
                        "missing_draft_notice",
                        "The draft notice is empty.",
                        None,
                        "R-NOTICE-3",
                    )
                )

    return defects
