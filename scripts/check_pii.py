#!/usr/bin/env python3
"""Scan repository files for accidental PII leaks, enforcing the zero-PII guarantee.

Zero runtime third-party dependencies (standard library only).
Scans for:
- Real US Social Security Numbers (SSN) (whitelisting reserved synthetic 000-xx-xxxx)
- Real Credit Card Numbers (validated with Luhn checksum)
- Real US Telephone Numbers (whitelisting reserved fictional 555-01xx)
- Real Corporate EINs (whitelisting 00-xxxxxxx)
- Real Email Addresses (whitelisting RFC 2606 reserved domains)

Usage::

    python scripts/check_pii.py
    python scripts/check_pii.py skills/ knowledge/ examples/
    python scripts/check_pii.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CORE_SRC = REPO_ROOT / "packages" / "fincrime-core" / "src"
if str(CORE_SRC) not in sys.path:
    sys.path.insert(0, str(CORE_SRC))

from fincrime_core.synth.pii import PIIViolation, scan_directory, scan_file  # noqa: E402

DEFAULT_TARGETS = ("skills", "knowledge", "examples", "reports")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan repository assets for real PII leaks (enforcing zero-PII)."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Paths to scan (default: skills, knowledge, examples, reports).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit findings as JSON.",
    )
    parser.add_argument(
        "--extensions",
        default=".json,.yaml,.yml,.md,.txt,.py",
        help="Comma-separated file extensions to scan.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    targets = [Path(p) for p in args.paths] if args.paths else [REPO_ROOT / d for d in DEFAULT_TARGETS]
    extensions = tuple(e.strip().lower() for e in args.extensions.split(","))

    all_violations: list[PIIViolation] = []
    scanned_file_count = 0

    for target in targets:
        if not target.exists():
            continue
        if target.is_file():
            scanned_file_count += 1
            all_violations.extend(scan_file(target))
        elif target.is_dir():
            v = scan_directory(target, extensions=extensions)
            all_violations.extend(v)

    if args.json:
        data = {
            "status": "violation" if all_violations else "clean",
            "violation_count": len(all_violations),
            "violations": [
                {
                    "file": v.file_path,
                    "line": v.line_number,
                    "type": v.pii_type,
                    "snippet": v.matched_value_redacted,
                    "context": v.context,
                }
                for v in all_violations
            ],
        }
        print(json.dumps(data, indent=2))
        return 1 if all_violations else 0

    if all_violations:
        print(f"\n[PII SCANNER] FAILED: {len(all_violations)} real PII violation(s) detected!\n")
        for v in all_violations:
            rel_path = v.file_path
            try:
                rel_path = str(Path(v.file_path).relative_to(REPO_ROOT))
            except ValueError:
                pass
            print(f"  * [{v.pii_type.upper()}] {rel_path}:{v.line_number} -> {v.matched_value_redacted}")
            print(f"    Context: {v.context}")
        print("\nAll datasets must remain 100% synthetic within reserved namespaces.")
        print("See SECURITY.md and fincrime_core.synth.pii for reserved namespaces.\n")
        return 1

    print("[PII SCANNER] OK: Zero real PII detected across scanned targets.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
