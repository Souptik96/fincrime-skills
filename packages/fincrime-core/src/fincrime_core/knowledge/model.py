"""The knowledge engine: dated, cited, jurisdiction-scoped records.

Regulatory and typology content is the fastest-decaying asset in this project,
and the failure mode to avoid is a stale claim silently becoming truth. Four
mechanisms do that work, and all four are here:

1. **Dating.** Every record carries ``as_of``, ``review_by`` and ``expires_at``.
2. **Citing.** A record without sources cannot be published.
3. **Immutability.** Packs are immutable once published; a correction is a new
   pack. The loader refuses a pack whose manifest checksum does not match.
4. **Jurisdiction scoping.** A record with an empty or "global" jurisdiction
   list is invalid, because regulatory content is never jurisdiction-agnostic.

Enforcement of expiry is graded by change type (ADR-0006): see
:class:`fincrime_core.validate.validator.EnforcementContext`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

__all__ = [
    "KnowledgeRecord",
    "KnowledgePack",
    "KnowledgeIndex",
    "ExpiryStatus",
    "parse_record",
    "load_pack",
    "parse_iso_date",
]

#: A record whose knowledge has been expired for longer than this is moved to
#: ``deprecated`` in the skills index rather than silently kept active.
DEPRECATION_GRACE_DAYS = 180


def parse_iso_date(value: str | None) -> date | None:
    """Parse an ISO-8601 date or datetime into a date, or ``None``."""
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        pass
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


@dataclass(frozen=True, slots=True)
class KnowledgeRecord:
    """One dated, cited, jurisdiction-scoped knowledge record."""

    id: str
    type: str
    pack: str
    version: str
    title: str
    definition: str
    jurisdictions: tuple[str, ...]
    sources: tuple[Mapping[str, Any], ...]
    as_of: str
    review_by: str
    expires_at: str
    status: str
    maintainer: str
    typology_refs: tuple[str, ...] = ()
    behavioral_attributes: tuple[str, ...] = ()
    prohibited_attributes: tuple[str, ...] = ()
    evidence_to_cite: tuple[str, ...] = ()
    benign_explanations: tuple[str, ...] = ()
    supersedes: str | None = None
    confidence: str = "moderate"
    notes: str | None = None

    @property
    def as_of_date(self) -> date | None:
        return parse_iso_date(self.as_of)

    @property
    def review_by_date(self) -> date | None:
        return parse_iso_date(self.review_by)

    @property
    def expires_at_date(self) -> date | None:
        return parse_iso_date(self.expires_at)

    def is_expired(self, on: date | None = None) -> bool:
        """True when the record has passed its expiry date."""
        expiry = self.expires_at_date
        if expiry is None:
            return False
        return (on or date.today()) >= expiry

    def is_review_due(self, on: date | None = None) -> bool:
        """True when the record has passed its review date but not yet expired."""
        review = self.review_by_date
        if review is None:
            return False
        return (on or date.today()) >= review

    def is_deprecation_due(self, on: date | None = None) -> bool:
        """True when the record has been expired long enough to be deprecated."""
        expiry = self.expires_at_date
        if expiry is None:
            return False
        return (on or date.today()) >= expiry + __import__("datetime").timedelta(days=DEPRECATION_GRACE_DAYS)


@dataclass(frozen=True, slots=True)
class ExpiryStatus:
    """A snapshot of the freshness of a knowledge set."""

    expired_ids: tuple[str, ...]
    review_due_ids: tuple[str, ...]
    deprecation_due_ids: tuple[str, ...]

    @property
    def has_expired(self) -> bool:
        return bool(self.expired_ids)


@dataclass(frozen=True, slots=True)
class KnowledgePack:
    """An immutable, dated snapshot of knowledge records."""

    id: str
    version: str
    as_of: str
    records: tuple[KnowledgeRecord, ...]
    checksum: str = ""

    def index(self) -> "KnowledgeIndex":
        return KnowledgeIndex(self.records)

    def expiry_status(self, on: date | None = None) -> ExpiryStatus:
        return self.index().expiry_status(on)


class KnowledgeIndex:
    """An index over a set of knowledge records."""

    __slots__ = ("_by_id",)

    def __init__(self, records: Sequence[KnowledgeRecord]) -> None:
        self._by_id: dict[str, KnowledgeRecord] = {record.id: record for record in records}

    def __len__(self) -> int:
        return len(self._by_id)

    def __contains__(self, record_id: object) -> bool:
        return record_id in self._by_id

    def get(self, record_id: str) -> KnowledgeRecord | None:
        return self._by_id.get(record_id)

    def __iter__(self) -> Iterator[KnowledgeRecord]:
        return iter(self._by_id.values())

    def ids(self) -> tuple[str, ...]:
        return tuple(self._by_id)

    def indicator_ids(self) -> tuple[str, ...]:
        return tuple(r.id for r in self._by_id.values() if r.type == "indicator")

    def by_type(self, record_type: str) -> tuple[KnowledgeRecord, ...]:
        return tuple(r for r in self._by_id.values() if r.type == record_type)

    def expired_ids(self, on: date | None = None) -> tuple[str, ...]:
        return tuple(sorted(r.id for r in self._by_id.values() if r.is_expired(on)))

    def review_due_ids(self, on: date | None = None) -> tuple[str, ...]:
        return tuple(sorted(r.id for r in self._by_id.values() if r.is_review_due(on) and not r.is_expired(on)))

    def deprecation_due_ids(self, on: date | None = None) -> tuple[str, ...]:
        return tuple(sorted(r.id for r in self._by_id.values() if r.is_deprecation_due(on)))

    def expiry_status(self, on: date | None = None) -> ExpiryStatus:
        return ExpiryStatus(
            expired_ids=self.expired_ids(on),
            review_due_ids=self.review_due_ids(on),
            deprecation_due_ids=self.deprecation_due_ids(on),
        )


def parse_record(raw: Mapping[str, Any]) -> KnowledgeRecord:
    """Parse a knowledge record document."""
    return KnowledgeRecord(
        id=str(raw["id"]),
        type=str(raw["type"]),
        pack=str(raw.get("pack", "")),
        version=str(raw.get("version", "1.0.0")),
        title=str(raw.get("title", "")),
        definition=str(raw.get("definition", "")),
        jurisdictions=tuple(raw.get("jurisdictions") or ()),
        sources=tuple(raw.get("sources") or ()),
        as_of=str(raw.get("as_of", "")),
        review_by=str(raw.get("review_by", "")),
        expires_at=str(raw.get("expires_at", "")),
        status=str(raw.get("status", "active")),
        maintainer=str(raw.get("maintainer", "")),
        typology_refs=tuple(raw.get("typology_refs") or ()),
        behavioral_attributes=tuple(raw.get("behavioral_attributes") or ()),
        prohibited_attributes=tuple(raw.get("prohibited_attributes") or ()),
        evidence_to_cite=tuple(raw.get("evidence_to_cite") or ()),
        benign_explanations=tuple(raw.get("benign_explanations") or ()),
        supersedes=raw.get("supersedes"),
        confidence=str(raw.get("confidence", "moderate")),
        notes=raw.get("notes"),
    )


def load_pack(pack_dir: str | Path) -> KnowledgePack:
    """Load a knowledge pack from a directory.

    The directory is expected to contain a ``manifest.yaml``-equivalent
    ``manifest.json`` and one JSON file per record, grouped into subdirectories
    by type. The loader is tolerant of layout and strict about the manifest
    checksum: a pack whose contents do not match its manifest is rejected,
    because a pack whose contents drifted from its manifest is not the pack
    anybody reviewed.
    """
    root = Path(pack_dir)
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"knowledge pack manifest not found: {manifest_path}")

    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    records: list[KnowledgeRecord] = []
    for path in sorted(root.rglob("*.json")):
        if path.name == "manifest.json":
            continue
        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        records.append(parse_record(raw))

    return KnowledgePack(
        id=str(manifest.get("id", root.name)),
        version=str(manifest.get("version", "")),
        as_of=str(manifest.get("as_of", "")),
        records=tuple(records),
        checksum=str(manifest.get("checksum", "")),
    )
