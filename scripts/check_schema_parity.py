#!/usr/bin/env python3
"""Cross-check the dependency-free schema validator against the reference one.

The contracts are normative JSON Schema 2020-12. ``fincrime_core`` ships its
own dependency-free subset validator so the core can run air-gapped
(ADR-0002), but that implementation must agree with a reference validator
byte-for-byte on the corpus — otherwise the two would be different contracts.

This script uses ``jsonschema`` when it is available (it is a dev-only
dependency) and skips cleanly when it is not, so the core's own CI remains
dependency-free.

Usage::

    python scripts/check_schema_parity.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = REPO_ROOT / "contracts"
CORE_SRC = REPO_ROOT / "packages" / "fincrime-core" / "src"

sys.path.insert(0, str(CORE_SRC))

from fincrime_core.validate.schema import JsonSchemaValidator  # noqa: E402

#: Corpus of instances exercised against every schema. Each entry is
#: (schema file, instance, must_be_valid).
CORPUS: list[tuple[str, object, bool]] = [
    ("finding.schema.json", {"contract_version": "fincrime/finding/1.0.0"}, False),
    ("finding.schema.json", {}, False),
    (
        "finding.schema.json",
        {
            "contract_version": "fincrime/finding/1.0.0",
            "artifact": {
                "skill_id": "s",
                "skill_version": "1.0.0",
                "artifact_type": "triage_report",
                "subject_ids": ["x"],
                "jurisdictions": ["US"],
                "created_at": "2026-01-01T00:00:00Z",
                "completeness": "complete",
            },
            "provenance": {
                "skill_id": "s",
                "skill_version": "1.0.0",
                "model": {"provider": "p", "id": "i"},
                "prompt_sha256": "a" * 64,
                "evidence_set_sha256": "b" * 64,
                "knowledge_pack": {"id": "k", "version": "v", "as_of": "2026-01-01"},
                "policy_set": {"id": "p", "version": "1"},
                "run_id": "r",
                "timestamp": "2026-01-01T00:00:00Z",
            },
            "claims": [
                {
                    "id": "C-001",
                    "class": "hypothesis",
                    "statement": "s",
                    "confidence": {"level": "low", "basis": "b"},
                    "epistemic_type": "adverse_reading",
                    "falsifier": "f",
                }
            ],
            "human_decision_required": [
                {"decision_id": "D-01", "question": "q", "owner_role": "r"}
            ],
        },
        True,
    ),
    (
        "finding.schema.json",
        {
            "contract_version": "fincrime/finding/1.0.0",
            "artifact": {
                "skill_id": "s",
                "skill_version": "1.0.0",
                "artifact_type": "triage_report",
                "subject_ids": ["x"],
                "jurisdictions": ["US"],
                "created_at": "2026-01-01T00:00:00Z",
                "completeness": "complete",
            },
            "provenance": {
                "skill_id": "s",
                "skill_version": "1.0.0",
                "model": {"provider": "p", "id": "i"},
                "prompt_sha256": "a" * 64,
                "evidence_set_sha256": "b" * 64,
                "knowledge_pack": {"id": "k", "version": "v", "as_of": "2026-01-01"},
                "policy_set": {"id": "p", "version": "1"},
                "run_id": "r",
                "timestamp": "2026-01-01T00:00:00Z",
            },
            "claims": [
                {
                    "id": "C-001",
                    "class": "hypothesis",
                    "statement": "s",
                    "confidence": {"level": "low", "basis": "b"},
                    "epistemic_type": "adverse_reading",
                }
            ],
            "human_decision_required": [
                {"decision_id": "D-01", "question": "q", "owner_role": "r"}
            ],
        },
        False,
    ),
    ("skill-manifest.schema.json", {"apiVersion": "fincrime.dev/v1", "kind": "FinCrimeSkill"}, False),
    ("evidence-ref-grammar.schema.json", {}, False),
    ("case.schema.json", {"case_id": "x", "suite": "s", "version": "1.0.0", "kind": "golden"}, False),
]


def main() -> int:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        print("jsonschema is not installed; skipping parity check.")
        print("Install it with: pip install jsonschema")
        return 0

    failures: list[str] = []
    checked = 0

    for schema_name, instance, expected_valid in CORPUS:
        schema_path = CONTRACTS / schema_name
        with schema_path.open("r", encoding="utf-8") as handle:
            schema = json.load(handle)

        ours = JsonSchemaValidator(schema)
        ours_valid = ours.is_valid(instance)

        reference = Draft202012Validator(schema)
        reference_valid = reference.is_valid(instance)

        checked += 1
        if ours_valid != reference_valid:
            failures.append(
                f"{schema_name}: our validator says {ours_valid}, reference says {reference_valid}"
            )
        if ours_valid != expected_valid:
            failures.append(
                f"{schema_name}: expected validity {expected_valid}, got {ours_valid}"
            )

    if failures:
        print("Schema parity FAILED:")
        for failure in failures:
            print(f"  {failure}")
        return 1

    print(f"Schema parity OK: {checked} instances agree with the reference implementation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
