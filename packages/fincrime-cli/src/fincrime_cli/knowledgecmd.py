"""fincrime knowledge: inspect, list, and validate knowledge packs and typologies.

Standard-library only, zero network, deterministic.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Sequence

from fincrime_core.knowledge.expiry import plan_expiry_actions
from fincrime_core.knowledge.model import (
    KnowledgePack,
    KnowledgeRecord,
    load_pack,
    validate_pack,
)
from fincrime_core.paths import repo_root
from fincrime_core.synth.typologies import TYPOLOGY_MATRIX, list_typology_ids

__all__ = [
    "cmd_knowledge_list",
    "cmd_knowledge_inspect",
    "cmd_knowledge_typologies",
    "cmd_knowledge_validate",
    "cmd_knowledge_check",
]

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2

DEFAULT_PACKS_REL = Path("knowledge") / "packs"


def _find_packs_root(explicit: str | None = None) -> Path | None:
    if explicit:
        p = Path(explicit)
        return p if p.is_dir() else None
    root = repo_root()
    if root is None:
        candidate = DEFAULT_PACKS_REL
        return candidate if candidate.is_dir() else None
    candidate = root / DEFAULT_PACKS_REL
    return candidate if candidate.is_dir() else None


def _discover_packs(packs_root: Path) -> list[tuple[Path, KnowledgePack]]:
    packs: list[tuple[Path, KnowledgePack]] = []
    # If the directory itself has a manifest.json
    if (packs_root / "manifest.json").is_file():
        try:
            packs.append((packs_root, load_pack(packs_root)))
        except Exception:
            pass
    # Subdirectories
    for subdir in sorted(packs_root.iterdir()):
        if subdir.is_dir() and (subdir / "manifest.json").is_file():
            try:
                packs.append((subdir, load_pack(subdir)))
            except Exception:
                continue
    return packs


def cmd_knowledge_list(args: argparse.Namespace) -> int:
    """List available knowledge packs with record counts and freshness status."""
    packs_dir_arg = getattr(args, "packs_dir", None)
    packs_root = _find_packs_root(packs_dir_arg)

    if packs_root is None or not packs_root.is_dir():
        print("error: knowledge packs directory not found", file=sys.stderr)
        return EXIT_USAGE

    as_of = getattr(args, "as_of", None) or date.today()
    discovered = _discover_packs(packs_root)

    pack_summaries: list[dict[str, Any]] = []
    for pack_path, pack in discovered:
        counts: dict[str, int] = {}
        for r in pack.records:
            counts[r.type] = counts.get(r.type, 0) + 1

        val_res = validate_pack(pack_path, promotion=False, as_of=as_of)
        expired = [r for r in pack.records if r.is_expired(as_of)]
        review_due = [r for r in pack.records if r.is_review_due(as_of) and not r.is_expired(as_of)]

        pack_summaries.append({
            "id": pack.id,
            "version": pack.version,
            "as_of": pack.as_of,
            "path": str(pack_path),
            "total_records": len(pack.records),
            "indicators": counts.get("indicator", 0),
            "typologies": counts.get("typology", 0),
            "requests": counts.get("request", 0),
            "regulatory": counts.get("regulatory", 0),
            "expired_records": len(expired),
            "review_due_records": len(review_due),
            "checksum_valid": val_res.checksum_ok,
            "status": "active" if not expired else "stale_records_present",
        })

    as_json = getattr(args, "json", False) or getattr(args, "format", "text") == "json"
    if as_json:
        print(json.dumps(pack_summaries, indent=2))
        return EXIT_OK

    print("=" * 80)
    print("  FINCRIME KNOWLEDGE PACKS REGISTRY")
    print(f"  Directory: {packs_root} | As Of: {as_of.isoformat()}")
    print("=" * 80)
    print(
        f"{'Pack ID':<20} {'Version':<10} {'Records':<8} {'Indicators':<11} "
        f"{'Typologies':<11} {'Checksum':<10} {'Freshness'}"
    )
    print("-" * 80)
    for p in pack_summaries:
        cs = "OK" if p["checksum_valid"] else "MISMATCH"
        print(
            f"{p['id']:<20} {p['version']:<10} {p['total_records']:<8} "
            f"{p['indicators']:<11} {p['typologies']:<11} {cs:<10} {p['status']}"
        )
    print("-" * 80)
    print("Inspect an indicator: fincrime knowledge inspect --indicator <id>")
    print("List AML typologies:   fincrime knowledge typologies")
    print("=" * 80)
    return EXIT_OK


def cmd_knowledge_inspect(args: argparse.Namespace) -> int:
    """Inspect a specific indicator or knowledge record."""
    target_id = getattr(args, "indicator", None) or getattr(args, "record", None)
    if not target_id:
        print("error: specify an indicator or record ID via --indicator <id> or --record <id>", file=sys.stderr)
        return EXIT_USAGE

    packs_root = _find_packs_root(getattr(args, "pack", None))
    if packs_root is None or not packs_root.is_dir():
        print("error: knowledge pack directory not found", file=sys.stderr)
        return EXIT_USAGE

    discovered = _discover_packs(packs_root)
    matched_record: KnowledgeRecord | None = None
    matched_pack: KnowledgePack | None = None

    for _, pack in discovered:
        for record in pack.records:
            if record.id.upper() == target_id.strip().upper():
                matched_record = record
                matched_pack = pack
                break
        if matched_record:
            break

    if matched_record is None:
        print(f"error: indicator/record '{target_id}' not found in knowledge packs", file=sys.stderr)
        # Suggest available indicators
        all_indicators: list[str] = []
        for _, pack in discovered:
            all_indicators.extend(pack.indicator_ids())
        if all_indicators:
            print("Available indicators in pack:", file=sys.stderr)
            for ind in sorted(all_indicators)[:10]:
                print(f"  - {ind}", file=sys.stderr)
            if len(all_indicators) > 10:
                print(f"  ... and {len(all_indicators) - 10} more.", file=sys.stderr)
        return EXIT_USAGE

    as_of = getattr(args, "as_of", None) or date.today()
    is_expired = matched_record.is_expired(as_of)
    is_review_due = matched_record.is_review_due(as_of)

    record_dict: dict[str, Any] = {
        "id": matched_record.id,
        "type": matched_record.type,
        "pack": matched_pack.id if matched_pack else matched_record.pack,
        "pack_version": matched_pack.version if matched_pack else matched_record.version,
        "title": matched_record.title,
        "definition": matched_record.definition,
        "jurisdictions": list(matched_record.jurisdictions),
        "status": matched_record.status,
        "as_of": matched_record.as_of,
        "review_by": matched_record.review_by,
        "expires_at": matched_record.expires_at,
        "freshness": "expired" if is_expired else ("review_due" if is_review_due else "current"),
        "maintainer": matched_record.maintainer,
        "typology_refs": list(matched_record.typology_refs),
        "behavioral_attributes": list(matched_record.behavioral_attributes),
        "prohibited_attributes": list(matched_record.prohibited_attributes),
        "evidence_to_cite": list(matched_record.evidence_to_cite),
        "benign_explanations": list(matched_record.benign_explanations),
        "sources": list(matched_record.sources),
    }

    as_json = getattr(args, "json", False) or getattr(args, "format", "text") == "json"
    if as_json:
        print(json.dumps(record_dict, indent=2))
        return EXIT_OK

    print("=" * 80)
    print(f"  KNOWLEDGE RECORD: {matched_record.id} ({matched_record.type.upper()})")
    print("=" * 80)
    print(f"Title:         {matched_record.title}")
    print(f"Record Type:   {matched_record.type}")
    print(f"Pack:          {record_dict['pack']} (v{record_dict['pack_version']})")
    print(f"Jurisdictions: {', '.join(matched_record.jurisdictions)}")
    print(f"Dates:         as_of={matched_record.as_of}  review_by={matched_record.review_by}  expires_at={matched_record.expires_at}")
    print(f"Freshness:     {record_dict['freshness'].upper()} (as of {as_of.isoformat()})")
    print(f"Maintainer:    {matched_record.maintainer}")
    print()
    print("DEFINITION:")
    for line in _wrap_text(matched_record.definition, 76):
        print(f"  {line}")
    print()

    if matched_record.typology_refs:
        print(f"Typology References:      {', '.join(matched_record.typology_refs)}")
    if matched_record.behavioral_attributes:
        print(f"Behavioral Attributes:    {', '.join(matched_record.behavioral_attributes)}")
    if matched_record.prohibited_attributes:
        print(f"Prohibited Attributes:    {', '.join(matched_record.prohibited_attributes)}")
    if matched_record.evidence_to_cite:
        print("Recommended Evidence:")
        for ev in matched_record.evidence_to_cite:
            print(f"  - {ev}")
    if matched_record.benign_explanations:
        print("Benign Lookalike Explanations (Epistemic Twin):")
        for b in matched_record.benign_explanations:
            print(f"  - {b}")
    if matched_record.sources:
        print("Authoritative Sources:")
        for s in matched_record.sources:
            title = s.get("title") or s.get("id") or "Source"
            citation = s.get("citation") or ""
            print(f"  - {title}: {citation}")
    print("=" * 80)
    return EXIT_OK


def cmd_knowledge_typologies(args: argparse.Namespace) -> int:
    """List the 12 production AML/CTF typologies and paired benign twins."""
    typology_list: list[dict[str, Any]] = []

    for t in TYPOLOGY_MATRIX:
        illicit = t.illicit_profile
        twin = t.benign_twin
        typology_list.append({
            "id": t.id,
            "title": t.title,
            "category": t.category.upper(),
            "definition": t.definition,
            "behavioral_attributes": list(t.behavioral_attributes),
            "benign_twin": {
                "id": twin.id,
                "title": twin.title,
                "commercial_scenario": twin.commercial_scenario,
                "exculpatory_evidence_requirements": list(twin.exculpatory_evidence_requirements),
            },
            "statistical_profile": {
                "velocity_daily": {"mean": illicit.velocity_daily.mean, "std": illicit.velocity_daily.std},
                "threshold_proximity_ratio": {
                    "mean": illicit.threshold_proximity_ratio.mean,
                    "std": illicit.threshold_proximity_ratio.std,
                },
                "round_amount_ratio": {
                    "mean": illicit.round_amount_ratio.mean,
                    "std": illicit.round_amount_ratio.std,
                },
            },
        })

    as_json = getattr(args, "json", False) or getattr(args, "format", "text") == "json"
    if as_json:
        print(json.dumps(typology_list, indent=2))
        return EXIT_OK

    print("=" * 80)
    print("  FINCRIME 12-TYPOLOGY MATRIX & BENIGN LOOKALIKE TWINS")
    print("=" * 80)
    print(f"{'Typology ID':<36} {'Category':<10} {'Paired Benign Lookalike Twin'}")
    print("-" * 80)
    for t in typology_list:
        print(f"{t['id']:<36} {t['category']:<10} {t['benign_twin']['id']}")
        print(f"  Title: {t['title']}")
        print(f"  Twin:  {t['benign_twin']['title']}")
        print(f"  Key Attributes: {', '.join(t['behavioral_attributes'][:3])}")
        print()
    print("-" * 80)
    print("Total Typologies: 12 AML/CTF | 100% paired with benign lookalikes (Rule R-3b)")
    print("=" * 80)
    return EXIT_OK


def cmd_knowledge_validate(args: argparse.Namespace) -> int:
    """Validate a knowledge pack's checksum and schema."""
    as_of = getattr(args, "as_of", None) or date.today()
    promotion = getattr(args, "promotion", False)
    pack_path = Path(args.pack)

    if not pack_path.is_dir():
        print(f"error: {pack_path} is not a directory", file=sys.stderr)
        return EXIT_USAGE

    result = validate_pack(pack_path, promotion=promotion, as_of=as_of)
    context_label = "promotion" if promotion else "release"
    print(f"knowledge pack: {pack_path}")
    print(f"context: {context_label}  as of: {as_of.isoformat()}")
    print(f"records: {len(result.records)}  checksum: {'ok' if result.checksum_ok else 'MISMATCH'}")
    err_count = sum(1 for f in result.findings if getattr(f, "severity", "") == "error")
    warn_count = sum(1 for f in result.findings if getattr(f, "severity", "") == "warn")
    print(f"findings: {err_count} error(s), {warn_count} warning(s)")
    for finding in result.findings:
        sev = getattr(finding, "severity", "error")
        code = getattr(finding, "code", "FINDING")
        msg = getattr(finding, "message", str(finding))
        print(f"  {sev:5s}  {code}  {msg}")

    if getattr(args, "json", False):
        print()
        print(
            json.dumps(
                {
                    "path": str(pack_path),
                    "valid": result.valid,
                    "context": context_label,
                    "as_of": as_of.isoformat(),
                    "checksum_ok": result.checksum_ok,
                    "findings": [f.to_dict() for f in result.findings],
                },
                indent=2,
            )
        )

    return EXIT_OK if result.valid else EXIT_FINDINGS


def cmd_knowledge_check(args: argparse.Namespace) -> int:
    """Plan refreshes and detect stale knowledge records."""
    pack_path = Path(args.pack)
    if not pack_path.is_dir():
        print(f"error: {pack_path} is not a directory", file=sys.stderr)
        return EXIT_USAGE

    try:
        pack = load_pack(pack_path)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_FINDINGS

    as_of = getattr(args, "as_of", None) or date.today()
    actions = plan_expiry_actions(pack, as_of)

    print(f"knowledge pack: {pack_path} ({pack.id} {pack.version})")
    print(f"as of: {as_of.isoformat()}")
    print(f"records: {len(pack.records)}  stale: {len(actions)}")

    if getattr(args, "json", False):
        print()
        print(
            json.dumps(
                {
                    "pack": pack.id,
                    "version": pack.version,
                    "as_of": as_of.isoformat(),
                    "actions": [a.to_dict() for a in actions],
                },
                indent=2,
            )
        )
        return EXIT_OK

    for action in actions:
        print()
        print(f"  {action.record_id}  [{action.status}]  {action.title}")
        print(f"    {action.issue_title}")
        if action.maintainer:
            print(f"    maintainer: {action.maintainer}")
    return EXIT_OK


def _wrap_text(text: str, width: int = 76) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current: list[str] = []
        cur_len = 0
        for word in words:
            if cur_len + len(word) + (1 if current else 0) <= width:
                current.append(word)
                cur_len += len(word) + (1 if len(current) > 1 else 0)
            else:
                lines.append(" ".join(current))
                current = [word]
                cur_len = len(word)
        if current:
            lines.append(" ".join(current))
    return lines
