"""RFC 6901 evidence-reference resolution.

This module is the single most important correctness surface in the project.
Every claim's evidence attribution is decided here, and the metric
``evidence_attribution_accuracy`` is computed over its results. Two properties
are therefore non-negotiable:

**Totality.** Resolution never raises. ``resolve`` returns a
:class:`Resolution` for *every* input, including malformed, dangling and
hostile references. A validator that crashes on a malformed artifact is a
denial-of-service on exactly the artifacts an analyst most needs to inspect.

**Purity.** Resolution depends only on the evidence set and the reference. No
clock, no network, no filesystem, no randomness, no global state.

Grammar (ADR-0004)::

    evidence-ref    = source-id "#" json-pointer
    source-id       = type ":" instance
    type            = ALPHA *( ALPHA / DIGIT / "_" / "-" )
    instance        = 1*64( UNRESERVED / ":" / "." / "-" / "_" )
    json-pointer    = *( "/" reference-token )
    reference-token = *( unescaped / escaped )
    escaped         = "~" ( "0" / "1" )
    unescaped       = %x00-2E / %x30-7D / %x7F-10FFFF

The ``#`` separator is required. There is no range syntax: a claim spanning
several items carries one reference per item.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

__all__ = [
    "EVIDENCE_REF_PATTERN",
    "EVIDENCE_REF_PATTERN_STR",
    "SOURCE_ID_PATTERN",
    "Resolution",
    "SourceIndex",
    "parse_evidence_ref",
    "unescape_token",
    "escape_token",
    "build_source_index",
]

#: A source id: ``type:instance``.
SOURCE_ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*:[A-Za-z0-9._:-]{1,64}$")

#: The canonical evidence-reference pattern, as a string. This exact string is
#: mirrored in ``contracts/evidence-ref-grammar.schema.json`` and the two are
#: asserted equal by a contract test, so the grammar and the implementation
#: cannot drift.
#:
#: The fragment part is an RFC 6901 pointer: zero or more ``/``-prefixed
#: tokens, each token being a sequence of unescaped characters or RFC 6901
#: escapes (``~0`` -> ``~``, ``~1`` -> ``/``). ``#`` and ``/`` and ``~`` are
#: excluded from the unescaped set: a second ``#`` would be a second fragment
#: separator, and RFC 6901 requires it to be percent-encoded.
EVIDENCE_REF_PATTERN_STR = (
    r"^[A-Za-z][A-Za-z0-9_-]*:[A-Za-z0-9._:-]{1,64}#(/([^/~#]|~[01])*)*$"
)

EVIDENCE_REF_PATTERN = re.compile(EVIDENCE_REF_PATTERN_STR)

#: The same grammar with named groups, used for extraction.
_EVIDENCE_REF_NAMED = re.compile(
    r"^(?P<source_id>[A-Za-z][A-Za-z0-9_-]*:[A-Za-z0-9._:-]{1,64})"
    r"#"
    r"(?P<pointer>(?:/(?:[^/~#]|~[01])*)*)$"
)

#: A pointer resolving to a collection longer than this is rejected as
#: over-broad: citing "the whole transaction list" is not evidence attribution.
MAX_CITED_COLLECTION_LENGTH = 20


class EvidenceRefError(ValueError):
    """Raised only by strict helpers. :func:`resolve` never raises."""


@dataclass(frozen=True, slots=True)
class Resolution:
    """The outcome of resolving one evidence reference.

    ``ok`` is the only thing callers should branch on first. When it is false,
    ``error_code`` names a stable machine-readable reason.
    """

    ok: bool
    source_id: str | None = None
    pointer: str = ""
    value: Any = None
    error_code: str | None = None
    error_message: str | None = None

    @property
    def is_over_broad(self) -> bool:
        return self.error_code == "over_broad_citation"


def unescape_token(token: str) -> str:
    """Decode one RFC 6901 reference token.

    Decoding order matters: ``~1`` must be replaced before ``~0``, otherwise
    the sequence ``~01`` would decode to ``~1`` instead of ``/1``.
    """
    if "~" not in token:
        return token
    return token.replace("~1", "/").replace("~0", "~")


def escape_token(token: str) -> str:
    """Encode one RFC 6901 reference token."""
    return token.replace("~", "~0").replace("/", "~1")


def parse_evidence_ref(ref: str) -> tuple[str, str]:
    """Split a reference into ``(source_id, json_pointer)``.

    Raises :class:`EvidenceRefError` for a malformed reference. Callers that
    must not raise should use :func:`resolve`.
    """
    if not isinstance(ref, str):
        raise EvidenceRefError(f"evidence ref must be a string, got {type(ref).__name__}")
    match = _EVIDENCE_REF_NAMED.match(ref)
    if match is None:
        raise EvidenceRefError(f"malformed evidence ref: {ref!r}")
    return match.group("source_id"), match.group("pointer")


def _walk_pointer(document: Any, pointer: str) -> tuple[bool, Any, str | None]:
    """Resolve ``pointer`` against ``document``.

    Returns ``(found, value, error_message)``. Implements RFC 6901 section 4
    array index rules, including the ``-`` token meaning "one past the end"
    (which is not a valid reference target for a value lookup).
    """
    if pointer == "":
        return True, document, None

    current = document
    for raw_token in pointer.split("/")[1:]:
        token = unescape_token(raw_token)
        if isinstance(current, Mapping):
            if token not in current:
                return False, None, f"key {token!r} not present"
            current = current[token]
        elif isinstance(current, Sequence) and not isinstance(current, (str, bytes)):
            if token == "-":
                return False, None, "array token '-' does not reference a value"
            if not token.isdigit():
                return False, None, f"array index {token!r} is not a non-negative integer"
            index = int(token)
            if index >= len(current):
                return False, None, f"array index {index} out of range"
            current = current[index]
        else:
            return False, None, f"cannot descend into {type(current).__name__} with token {token!r}"
    return True, current, None


class SourceIndex:
    """The closed world of evidence an artifact may reference.

    The index maps a ``source_id`` to the JSON object it names. It is built
    from the evidence set, so a reference to anything absent is unresolvable by
    construction — there is no path by which an artifact can cite a record the
    analyst never saw.
    """

    __slots__ = ("_entries",)

    def __init__(self, entries: Mapping[str, Any] | None = None) -> None:
        self._entries: dict[str, Any] = dict(entries or {})

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, source_id: object) -> bool:
        return source_id in self._entries

    def get(self, source_id: str) -> Any:
        """Return the indexed object, or raise ``KeyError`` if absent."""
        return self._entries[source_id]

    def source_ids(self) -> Iterable[str]:
        return self._entries.keys()

    def register(self, source_id: str, value: Any) -> None:
        """Add an entry. Duplicate ids overwrite; the builder must be idempotent."""
        self._entries[source_id] = value

    def resolve(self, ref: str) -> Resolution:
        """Resolve one reference. Never raises."""
        try:
            source_id, pointer = parse_evidence_ref(ref)
        except EvidenceRefError as exc:
            return Resolution(ok=False, error_code="malformed_ref", error_message=str(exc))

        if source_id not in self._entries:
            return Resolution(
                ok=False,
                source_id=source_id,
                pointer=pointer,
                error_code="unknown_source",
                error_message=f"source {source_id!r} is not present in the evidence set",
            )

        found, value, message = _walk_pointer(self._entries[source_id], pointer)
        if not found:
            return Resolution(
                ok=False,
                source_id=source_id,
                pointer=pointer,
                error_code="unresolved_pointer",
                error_message=message or "pointer did not resolve",
            )

        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            if len(value) > MAX_CITED_COLLECTION_LENGTH:
                return Resolution(
                    ok=False,
                    source_id=source_id,
                    pointer=pointer,
                    value=value,
                    error_code="over_broad_citation",
                    error_message=(
                        f"pointer resolves to a collection of {len(value)} items, which exceeds the "
                        f"maximum cited collection length of {MAX_CITED_COLLECTION_LENGTH}; "
                        "cite the specific items instead"
                    ),
                )

        return Resolution(ok=True, source_id=source_id, pointer=pointer, value=value)


def _first(record: Mapping[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def build_source_index(evidence_set: Mapping[str, Any]) -> SourceIndex:
    """Build the :class:`SourceIndex` for an evidence set.

    The mapping from a record to its source id is deterministic and documented:

    ==========================  =========================  ==================
    Record                      Source id                 Example
    ==========================  =========================  ==================
    the alert                   ``alert:<alert_id>``      ``alert:9930``
    the subject                 ``subject:<subject_id>``  ``subject:5512``
    a transaction               ``txn:<txn_id>``          ``txn:8842``
    a document                  ``doc:<doc_id>``          ``doc:kYC-2291``
    a watchlist record          ``wl:<entry_id>``         ``wl:OFAC-1234``
    a prior finding             ``prior:<finding_id>``    ``prior:pf-77``
    an entity                   ``entity:<entity_id>``    ``entity:ent-9``
    ==========================  =========================  ==================

    A record whose natural id is missing or non-string is not indexed, which
    means it cannot be cited. That is the correct behaviour: an unidentifiable
    record cannot be attributed to.
    """
    index = SourceIndex()

    alert = evidence_set.get("alert")
    if isinstance(alert, Mapping):
        alert_id = _first(alert, "alert_id")
        if alert_id:
            index.register(f"alert:{alert_id}", dict(alert))

    subject = evidence_set.get("subject")
    if isinstance(subject, Mapping):
        subject_id = _first(subject, "subject_id")
        if subject_id:
            index.register(f"subject:{subject_id}", dict(subject))

    for txn in evidence_set.get("transactions") or ():
        if isinstance(txn, Mapping):
            txn_id = _first(txn, "txn_id")
            if txn_id:
                index.register(f"txn:{txn_id}", dict(txn))

    for doc in evidence_set.get("documents") or ():
        if isinstance(doc, Mapping):
            doc_id = _first(doc, "doc_id")
            if doc_id:
                index.register(f"doc:{doc_id}", dict(doc))

    for record in evidence_set.get("watchlist_records") or ():
        if isinstance(record, Mapping):
            entry_id = _first(record, "entry_id")
            if entry_id:
                index.register(f"wl:{entry_id}", dict(record))

    for finding in evidence_set.get("prior_findings") or ():
        if isinstance(finding, Mapping):
            finding_id = _first(finding, "finding_id")
            if finding_id:
                index.register(f"prior:{finding_id}", dict(finding))

    for entity in evidence_set.get("entities") or ():
        if isinstance(entity, Mapping):
            entity_id = _first(entity, "entity_id")
            if entity_id:
                index.register(f"entity:{entity_id}", dict(entity))

    return index
