"""Negation-aware detection of culpability phrasing.

The matcher lives in its own module because two layers need it: the claim
lints (which report a heuristic finding) and the policy evaluator (which can
enforce a firm's own deny-list as a deterministic rule). Sharing one
implementation is what keeps a firm's exported policy set and the core's
lint from drifting into disagreeing about the same sentence.

The matcher scans a statement sentence by sentence. A sentence is skipped
when it carries a negation cue, because "the account is not structuring" must
not be reported as a culpability assertion. It is deterministic and
side-effect free.
"""

from __future__ import annotations

import re
from typing import Iterable

__all__ = [
    "CulpabilityMatcher",
    "DEFAULT_CULPABILITY_PATTERNS",
    "NEGATION_CUES",
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
    r"\bguilty\s+of\b",
    r"\bcommitted\s+(?:money\s+laundering|laundering|fraud|theft)\b",
    r"\bproceeds\s+of\s+crime\b",
    r"\bcriminal\s+enterprise\b",
    r"\bsanctioned\s+(?:person|individual|party|entity)\b",
    r"\bacted\s+to\s+evade\b",
)

#: Phrases that neutralise a match when they appear in the same clause. Used to
#: keep the heuristic from firing on negated or quoted statements.
NEGATION_CUES: tuple[str, ...] = (
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

    @property
    def patterns(self) -> tuple[str, ...]:
        """The source patterns, as written."""
        return tuple(pattern.pattern for pattern in self._patterns)

    def find(self, statement: str) -> list[str]:
        """Return the patterns that matched ``statement``, ignoring negated clauses."""
        if not statement:
            return []
        hits: list[str] = []
        for sentence in re.split(r"(?<=[.;!?])\s+", statement):
            lowered = sentence.lower()
            if any(cue in lowered for cue in NEGATION_CUES):
                continue
            for pattern in self._patterns:
                if pattern.search(sentence):
                    hits.append(pattern.pattern)
        return hits

    def is_clean(self, statement: str) -> bool:
        """True when ``statement`` contains no culpability phrasing."""
        return not self.find(statement)
