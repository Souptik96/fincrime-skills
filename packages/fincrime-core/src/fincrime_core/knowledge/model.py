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

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

from fincrime_core.paths import contracts_dir
from fincrime_core.provenance.hashing import canonical_json, sha256_hex
from fincrime_core.validate.schema import JsonSchemaValidator

__all__ = [
    "KnowledgeRecord",
    "KnowledgePack",
    "KnowledgeIndex",
    "ExpiryStatus",
    "PackFinding",
    "PackValidationResult",
    "parse_record",
    "load_pack",
    "validate_pack",
    "parse_iso_date",
    "resolve_date",
]

#: A record whose knowledge has been expired for longer than this is moved to
#: ``deprecated`` in the skills index rather than silently kept active.
DEPRECATION_GRACE_DAYS = 180

#: The directory inside a pack that holds the record files. Everything else in
#: the pack directory is ignored, so a stray index or a scratch file cannot be
#: mistaken for a record.
RECORDS_DIRNAME = "records"

#: The name of the pack manifest.
MANIFEST_FILENAME = "manifest.json"


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


def resolve_date(value: date | str | None) -> date | None:
    """Normalise a caller-supplied date into a ``date``, or ``None``.

    ``None`` means "no date was given", and every freshness check is skipped
    rather than silently made against today: the core reads no clock.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return parse_iso_date(value)


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
        return (on or date.today()) >= expiry + timedelta(days=DEPRECATION_GRACE_DAYS)


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

    def indicator_ids(self) -> tuple[str, ...]:
        """The ids of the pack's indicator records."""
        return tuple(record.id for record in self.records if record.type == "indicator")

    def record_ids(self) -> tuple[str, ...]:
        """The ids of every record in the pack."""
        return tuple(record.id for record in self.records)


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


@lru_cache(maxsize=1)
def _load_record_schema() -> JsonSchemaValidator:
    """The normative schema for a single knowledge record."""
    with (contracts_dir() / "knowledge-record.schema.json").open("r", encoding="utf-8") as handle:
        return JsonSchemaValidator(json.load(handle))


@lru_cache(maxsize=1)
def _load_pack_manifest_schema() -> JsonSchemaValidator:
    """The normative schema for a knowledge pack manifest."""
    with (contracts_dir() / "knowledge-pack-manifest.schema.json").open("r", encoding="utf-8") as handle:
        return JsonSchemaValidator(json.load(handle))


def parse_record(raw: Mapping[str, Any]) -> KnowledgeRecord:
    """Parse a knowledge record document.

    A record missing its identifying fields is not a record, so this raises
    ``ValueError`` rather than producing a record with an empty id. Callers
    that must not raise (the pack loader) catch it and report a finding.
    """
    if not isinstance(raw, Mapping):
        raise ValueError("a knowledge record must be a JSON object")
    for required in ("id", "type"):
        if not raw.get(required):
            raise ValueError(f"a knowledge record must carry a non-empty {required!r}")
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


def _pack_checksum(entries: Sequence[tuple[str, str]]) -> str:
    """Compute the pack checksum from the record index.

    The checksum covers the record ids and their file hashes, sorted by id, so
    it is independent of the order the manifest happens to list them in and of
    the filesystem's ordering.
    """
    payload = [{"id": record_id, "sha256": digest} for record_id, digest in sorted(entries)]
    return sha256_hex(canonical_json(payload))


def _file_sha256(path: Path) -> str:
    """Hash a file's bytes."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _record_paths(root: Path) -> list[Path]:
    """Every record file in the pack, in a stable order.

    Only the ``records/`` directory is read. A pack may carry notes, schemas,
    or generator output beside its records, and none of that is a record.
    """
    records_dir = root / RECORDS_DIRNAME
    if not records_dir.is_dir():
        return []
    return sorted(path for path in records_dir.rglob("*.json") if path.is_file())


@dataclass(frozen=True, slots=True)
class PackFinding:
    """One problem with a knowledge pack."""

    code: str
    severity: str
    message: str
    record_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "record_id": self.record_id,
        }


@dataclass(frozen=True, slots=True)
class PackValidationResult:
    """The outcome of validating one knowledge pack."""

    pack_id: str
    findings: tuple[PackFinding, ...] = ()
    records: tuple[KnowledgeRecord, ...] = ()
    checksum_ok: bool = False

    @property
    def valid(self) -> bool:
        return not any(finding.severity == "error" for finding in self.findings)

    @property
    def errors(self) -> tuple[PackFinding, ...]:
        return tuple(finding for finding in self.findings if finding.severity == "error")

    @property
    def warnings(self) -> tuple[PackFinding, ...]:
        return tuple(finding for finding in self.findings if finding.severity == "warn")


def _freshness_findings(
    records: Sequence[KnowledgeRecord],
    promotion: bool,
    as_of: date | str | None,
) -> list[PackFinding]:
    """The freshness findings for a pack's records as of a date.

    ADR-0006 grades enforcement by change type rather than by staleness
    alone: an expired record blocks the promotion of a pack, and is only
    disclosed — a warning — in the release context. A record that is merely
    review-due is disclosed in both contexts and blocks neither.
    """
    resolved = resolve_date(as_of)
    if resolved is None:
        return []

    findings: list[PackFinding] = []
    for record in sorted(records, key=lambda item: item.id):
        if record.is_expired(resolved):
            if promotion:
                message = (
                    f"record {record.id} expired on {record.expires_at} and cannot be "
                    f"promoted: the pack is stale as of {resolved.isoformat()}. Refresh the "
                    "record's content, re-date it, and publish a new pack version."
                )
            else:
                message = (
                    f"record {record.id} expired on {record.expires_at}. The pack is stale as "
                    f"of {resolved.isoformat()}; the refresh lands in the next pack version."
                )
            findings.append(
                PackFinding(
                    code="pack_record_expired",
                    severity="error" if promotion else "warn",
                    message=message,
                    record_id=record.id,
                )
            )
        elif record.is_review_due(resolved):
            findings.append(
                PackFinding(
                    code="pack_record_review_due",
                    severity="warn",
                    message=(
                        f"record {record.id} is due for review (review_by "
                        f"{record.review_by}), as of {resolved.isoformat()}."
                    ),
                    record_id=record.id,
                )
            )
    return findings


def validate_pack(
    pack_dir: str | Path,
    promotion: bool = False,
    as_of: date | str | None = None,
) -> PackValidationResult:
    """Validate a knowledge pack against its manifest.

    Four things are checked, and all four are integrity checks rather than
    judgements about content:

    1. the manifest satisfies ``contracts/knowledge-pack-manifest.schema.json``;
    2. every record file parses and satisfies
       ``contracts/knowledge-record.schema.json``;
    3. every record file's sha256 matches the hash the manifest recorded;
    4. the manifest's checksum matches the checksum computed from the index.

    A fifth check is made when ``as_of`` is given: the pack's freshness as of
    that date. An expired record is a hard block in the promotion context and
    a disclosed warning in the release context, which is the grading
    ADR-0006 sets out. Without ``as_of`` no freshness claim is made at all —
    this function reads no clock, so the date is always the caller's.

    The function never raises: a pack that cannot be read produces findings,
    because a pack that fails to load is exactly the pack somebody needs to
    be told about.
    """
    root = Path(pack_dir)
    findings: list[PackFinding] = []
    records: list[KnowledgeRecord] = []

    manifest_path = root / MANIFEST_FILENAME
    if not manifest_path.exists():
        return PackValidationResult(
            pack_id=root.name,
            findings=(
                PackFinding(
                    code="pack_manifest_missing",
                    severity="error",
                    message=f"knowledge pack manifest not found: {manifest_path}",
                ),
            ),
        )

    try:
        with manifest_path.open("r", encoding="utf-8") as handle:
            manifest = json.load(handle)
    except (OSError, ValueError) as exc:
        return PackValidationResult(
            pack_id=root.name,
            findings=(
                PackFinding(
                    code="pack_manifest_unreadable",
                    severity="error",
                    message=f"knowledge pack manifest could not be read: {exc}",
                ),
            ),
        )

    if not isinstance(manifest, Mapping):
        return PackValidationResult(
            pack_id=root.name,
            findings=(
                PackFinding(
                    code="pack_manifest_unreadable",
                    severity="error",
                    message="knowledge pack manifest is not a JSON object",
                ),
            ),
        )

    pack_id = str(manifest.get("id", root.name))

    for error in _load_pack_manifest_schema().validate(manifest):
        findings.append(
            PackFinding(
                code="pack_manifest_invalid",
                severity="error",
                message=f"manifest: {error.path}: {error.message}",
            )
        )

    index = manifest.get("records")
    listed: dict[str, Mapping[str, Any]] = {}
    if isinstance(index, list):
        for entry in index:
            if isinstance(entry, Mapping) and entry.get("id"):
                listed[str(entry["id"])] = entry
    else:
        findings.append(
            PackFinding(
                code="pack_manifest_invalid",
                severity="error",
                message="manifest: 'records' must be an array of record index entries",
            )
        )

    seen: set[str] = set()
    for path in _record_paths(root):
        try:
            with path.open("r", encoding="utf-8") as handle:
                raw = json.load(handle)
        except (OSError, ValueError) as exc:
            findings.append(
                PackFinding(
                    code="pack_record_unreadable",
                    severity="error",
                    message=f"{path.name}: could not be read as JSON: {exc}",
                )
            )
            continue

        if not isinstance(raw, Mapping):
            findings.append(
                PackFinding(
                    code="pack_record_invalid",
                    severity="error",
                    message=f"{path.name}: a record must be a JSON object",
                )
            )
            continue

        for error in _load_record_schema().validate(raw):
            findings.append(
                PackFinding(
                    code="pack_record_invalid",
                    severity="error",
                    message=f"{path.name}: {error.path}: {error.message}",
                    record_id=str(raw.get("id")) if raw.get("id") else None,
                )
            )

        try:
            record = parse_record(raw)
        except ValueError as exc:
            findings.append(
                PackFinding(
                    code="pack_record_invalid",
                    severity="error",
                    message=f"{path.name}: {exc}",
                )
            )
            continue

        seen.add(record.id)
        records.append(record)

        entry = listed.get(record.id)
        if entry is None:
            findings.append(
                PackFinding(
                    code="pack_record_unlisted",
                    severity="error",
                    message=(
                        f"record {record.id} is present in the pack but is not listed in the manifest. "
                        "A pack whose contents drifted from its manifest is not the pack anybody reviewed."
                    ),
                    record_id=record.id,
                )
            )
            continue

        expected_path = str(entry.get("path", ""))
        actual_path = path.relative_to(root).as_posix()
        if expected_path and expected_path != actual_path:
            findings.append(
                PackFinding(
                    code="pack_record_path_mismatch",
                    severity="error",
                    message=(
                        f"record {record.id} is at {actual_path} but the manifest lists it at {expected_path}"
                    ),
                    record_id=record.id,
                )
            )

        expected_hash = str(entry.get("sha256", ""))
        if expected_hash:
            actual_hash = _file_sha256(path)
            if actual_hash != expected_hash:
                findings.append(
                    PackFinding(
                        code="pack_record_hash_mismatch",
                        severity="error",
                        message=(
                            f"record {record.id} does not match the hash the manifest recorded "
                            f"(expected {expected_hash}, found {actual_hash})"
                        ),
                        record_id=record.id,
                    )
                )

    for record_id in sorted(set(listed) - seen):
        findings.append(
            PackFinding(
                code="pack_record_missing",
                severity="error",
                message=f"the manifest lists record {record_id} but no file for it was found",
                record_id=record_id,
            )
        )

    computed = _pack_checksum([(rid, str(entry.get("sha256", ""))) for rid, entry in listed.items()])
    declared = str(manifest.get("checksum", ""))
    checksum_ok = bool(declared) and computed == declared
    if not checksum_ok:
        findings.append(
            PackFinding(
                code="pack_checksum_mismatch",
                severity="error",
                message=(
                    f"the pack checksum does not match the record index "
                    f"(declared {declared or 'none'}, computed {computed})"
                ),
            )
        )

    findings.extend(_freshness_findings(records, promotion, as_of))

    return PackValidationResult(
        pack_id=pack_id,
        findings=tuple(findings),
        records=tuple(records),
        checksum_ok=checksum_ok,
    )


def load_pack(pack_dir: str | Path) -> KnowledgePack:
    """Load a knowledge pack from a directory, leniently.

    The directory contains a ``manifest.json`` and one JSON file per record
    under ``records/``. This loader is tolerant: a record that cannot be
    parsed is skipped rather than raising, because a caller that only wants
    the usable records should still get them.

    It does **not** verify the manifest's integrity claims. Use
    :func:`validate_pack` for that; this function reads, it does not vouch.
    """
    root = Path(pack_dir)
    manifest_path = root / MANIFEST_FILENAME
    if not manifest_path.exists():
        raise FileNotFoundError(f"knowledge pack manifest not found: {manifest_path}")

    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    records: list[KnowledgeRecord] = []
    for path in _record_paths(root):
        try:
            with path.open("r", encoding="utf-8") as handle:
                raw = json.load(handle)
            records.append(parse_record(raw))
        except (OSError, ValueError):
            continue

    return KnowledgePack(
        id=str(manifest.get("id", root.name)),
        version=str(manifest.get("version", "")),
        as_of=str(manifest.get("as_of", "")),
        records=tuple(records),
        checksum=str(manifest.get("checksum", "")),
    )
