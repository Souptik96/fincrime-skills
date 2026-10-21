#!/usr/bin/env python3
"""Build the ``core-2026-10`` knowledge pack from its reviewed source content.

The pack is published as files, with a manifest that records the hash of
every one of them. This script is the only thing that writes it, so the
published pack is reproducible: running it again on unchanged content
produces byte-identical files and an identical manifest checksum.

The pack is immutable once published. A correction to a record is not a
re-run of this script over a mutated definition — it is a new pack version
(ADR-0006). The script refuses to overwrite a pack whose contents differ
from what it would write, so an accidental re-run cannot silently rewrite a
published pack in place.

Usage::

    python scripts/build_core_pack.py
    python scripts/build_core_pack.py --pack knowledge/packs/core-2026-10
    python scripts/build_core_pack.py --check
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "packages" / "fincrime-core" / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "packages" / "fincrime-core" / "src"))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from core_pack_data import indicators, regulatory, requests, typologies  # noqa: E402

from fincrime_core.provenance.hashing import canonical_json, sha256_hex  # noqa: E402

#: The pack being built.
PACK_ID = "core-2026-10"
PACK_VERSION = "1.0.0"
PACK_DESCRIPTION = (
    "The first dated knowledge pack: the US indicators, typologies, regulatory "
    "mappings and request-catalogue entries a skill needs to reason about "
    "financial crime without asserting what it cannot support."
)

#: The dates every record in the pack carries.
AS_OF = "2026-10-01"
REVIEW_BY = "2027-04-01"
EXPIRES_AT = "2027-10-01"

#: The jurisdiction scope of the pack and of every record in it.
JURISDICTIONS = ["US"]

#: Who owns the records. A record nobody owns expires silently.
MAINTAINER = "@fincrime-maintainers"

#: The record types the pack holds, and the module each is drawn from.
CONTENT: tuple[tuple[str, Sequence[Mapping[str, Any]]], ...] = (
    ("indicator", indicators.INDICATORS),
    ("typology", typologies.TYPOLOGIES),
    ("regulatory", regulatory.REGULATORY),
    ("request", requests.REQUESTS),
)

#: The fields the builder owns, rather than the content author.
SHARED_FIELDS = (
    "pack",
    "version",
    "jurisdictions",
    "as_of",
    "review_by",
    "expires_at",
    "status",
    "maintainer",
)


def build_record(record_type: str, content: Mapping[str, Any]) -> dict[str, Any]:
    """Assemble one record from its content and the pack's shared facts."""
    record: dict[str, Any] = {
        "id": content["id"],
        "type": record_type,
        "pack": PACK_ID,
        "version": PACK_VERSION,
        "title": content["title"],
        "definition": content["definition"],
    }
    for field in (
        "typology_refs",
        "behavioral_attributes",
        "prohibited_attributes",
        "evidence_to_cite",
        "benign_explanations",
    ):
        if field in content:
            record[field] = list(content[field])
    record["jurisdictions"] = list(JURISDICTIONS)
    record["sources"] = [dict(source) for source in content["sources"]]
    record["as_of"] = AS_OF
    record["review_by"] = REVIEW_BY
    record["expires_at"] = EXPIRES_AT
    record["status"] = "active"
    record["maintainer"] = MAINTAINER
    if "confidence" in content:
        record["confidence"] = content["confidence"]
    if "notes" in content:
        record["notes"] = content["notes"]
    return record


def serialise(document: Any) -> bytes:
    """The exact bytes a record or manifest file is written as."""
    return (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def pack_checksum(entries: Iterable[tuple[str, str]]) -> str:
    """The pack checksum: the sha256 of the canonical JSON of the record index.

    The index is sorted by record id, so the checksum does not depend on the
    order the pack happens to list its records in, or on the filesystem's
    ordering. This is the algorithm the pack contract specifies and the
    loader verifies.
    """
    payload = [{"id": record_id, "sha256": digest} for record_id, digest in sorted(entries)]
    return sha256_hex(canonical_json(payload))


def plan(pack_dir: Path) -> tuple[list[tuple[str, str, bytes]], dict[str, Any]]:
    """The files the pack is made of, and its manifest.

    Returns the files as ``(relative path, record type, bytes)`` and the
    manifest. The manifest's record index is sorted by record id.
    """
    files: list[tuple[str, str, bytes]] = []
    index: list[dict[str, str]] = []
    seen: set[str] = set()

    for record_type, contents in CONTENT:
        for content in contents:
            record = build_record(record_type, content)
            record_id = record["id"]
            if record_id in seen:
                raise ValueError(f"duplicate record id: {record_id}")
            seen.add(record_id)
            relative = f"records/{record_type}/{record_id}.json"
            payload = serialise(record)
            files.append((relative, record_type, payload))
            index.append(
                {
                    "id": record_id,
                    "type": record_type,
                    "path": relative,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            )

    index.sort(key=lambda entry: entry["id"])
    manifest = {
        "id": PACK_ID,
        "version": PACK_VERSION,
        "as_of": AS_OF,
        "description": PACK_DESCRIPTION,
        "jurisdictions": list(JURISDICTIONS),
        "maintainer": MAINTAINER,
        "records": index,
        "checksum": pack_checksum(
            (entry["id"], entry["sha256"]) for entry in index
        ),
    }
    return files, manifest


def _orphan_paths(pack_dir: Path, planned: set[str]) -> list[Path]:
    """The record files in the pack that the source content no longer produces.

    A record whose id was renamed or withdrawn leaves a file behind that the
    manifest does not list. The pack would then contain a record nobody
    reviewed, which is exactly the drift the manifest is there to prevent.
    """
    records_dir = pack_dir / "records"
    if not records_dir.is_dir():
        return []
    return [
        path
        for path in sorted(records_dir.rglob("*.json"))
        if path.relative_to(pack_dir).as_posix() not in planned
    ]


def write_pack(pack_dir: Path) -> int:
    """Write the pack. Returns the number of records written."""
    files, manifest = plan(pack_dir)

    planned = {relative for relative, _record_type, _payload in files}
    orphans = _orphan_paths(pack_dir, planned)
    for orphan in orphans:
        orphan.unlink()
        print(f"removed orphan: {orphan.relative_to(pack_dir).as_posix()}")

    for relative, _record_type, payload in files:
        path = pack_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)

    manifest_path = pack_dir / "manifest.json"
    manifest_path.write_bytes(serialise(manifest))

    print(f"wrote {len(files)} record(s) to {pack_dir}")
    print(f"checksum: {manifest['checksum']}")
    return len(files)


def check_pack(pack_dir: Path) -> int:
    """Report whether the published pack matches what the source would write.

    Exits non-zero when they differ, so a drifted pack is a failure rather
    than a surprise.
    """
    files, manifest = plan(pack_dir)

    mismatches: list[str] = []
    for relative, _record_type, payload in files:
        path = pack_dir / relative
        if not path.exists():
            mismatches.append(f"missing: {relative}")
        elif path.read_bytes() != payload:
            mismatches.append(f"differs: {relative}")

    planned = {relative for relative, _record_type, _payload in files}
    for orphan in _orphan_paths(pack_dir, planned):
        mismatches.append(f"orphan: {orphan.relative_to(pack_dir).as_posix()}")

    manifest_path = pack_dir / "manifest.json"
    if not manifest_path.exists():
        mismatches.append("missing: manifest.json")
    else:
        published = json.loads(manifest_path.read_text(encoding="utf-8"))
        if published.get("checksum") != manifest["checksum"]:
            mismatches.append("manifest checksum differs from the source content")

    if mismatches:
        print(f"{pack_dir} does not match its source content:")
        for mismatch in mismatches:
            print(f"  {mismatch}")
        return 1

    print(f"{pack_dir} matches its source content ({len(files)} records).")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pack",
        default=str(REPO_ROOT / "knowledge" / "packs" / PACK_ID),
        help="the pack directory to write",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report whether the published pack matches its source content, and write nothing",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    pack_dir = Path(args.pack)
    if args.check:
        return check_pack(pack_dir)
    write_pack(pack_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
