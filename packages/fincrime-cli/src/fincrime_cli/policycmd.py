"""fincrime policy: inspect, list, check, and export policy sets.

Standard-library only, zero network, deterministic.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from fincrime_core.contract.loader import parse_finding
from fincrime_core.paths import repo_root
from fincrime_core.policy.evaluator import PolicyEvaluator
from fincrime_core.policy.set import PolicySet, export_policy_set, load_policy_set

__all__ = [
    "cmd_policy_list",
    "cmd_policy_check",
    "cmd_policy_export",
]

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2

DEFAULT_POLICIES_DIR_REL = Path("policies")
DEFAULT_POLICY_SET_REL = Path("policies") / "default" / "policy-set.json"


def _resolve_policy_set_path(target: str | None) -> Path | None:
    root = repo_root()
    if target is None or target == "default":
        if root is not None and (root / DEFAULT_POLICY_SET_REL).is_file():
            return root / DEFAULT_POLICY_SET_REL
        if DEFAULT_POLICY_SET_REL.is_file():
            return DEFAULT_POLICY_SET_REL
        return None

    candidate = Path(target)
    if candidate.is_file():
        return candidate
    if root is not None and (root / target).is_file():
        return root / target
    return None


def cmd_policy_list(args: argparse.Namespace) -> int:
    """List available policy sets with rules and metadata."""
    policies_dir_arg = getattr(args, "policies_dir", None)
    root = repo_root()

    if policies_dir_arg:
        p_dir = Path(policies_dir_arg)
    elif root is not None:
        p_dir = root / DEFAULT_POLICIES_DIR_REL
    else:
        p_dir = DEFAULT_POLICIES_DIR_REL

    if not p_dir.is_dir():
        print(f"error: policies directory '{p_dir}' not found", file=sys.stderr)
        return EXIT_USAGE

    discovered_sets: list[tuple[Path, PolicySet]] = []
    for path in sorted(p_dir.rglob("*.json")):
        try:
            pset = load_policy_set(path)
            discovered_sets.append((path, pset))
        except (OSError, ValueError):
            continue

    summaries: list[dict[str, Any]] = []
    for path, pset in discovered_sets:
        rules_info = [
            {
                "id": r.id,
                "version": r.version,
                "severity": r.severity,
                "description": r.description,
                "message": r.message,
            }
            for r in pset.rules
        ]
        summaries.append({
            "id": pset.id,
            "version": pset.version,
            "as_of": str(pset.as_of),
            "path": str(path),
            "jurisdictions": list(pset.jurisdictions),
            "description": pset.description,
            "rules_count": len(pset.rules),
            "rules": rules_info,
        })

    as_json = getattr(args, "json", False) or getattr(args, "format", "text") == "json"
    if as_json:
        print(json.dumps(summaries, indent=2))
        return EXIT_OK

    print("=" * 80)
    print("  FINCRIME POLICY SETS REGISTRY")
    print(f"  Directory: {p_dir}")
    print("=" * 80)
    for s in summaries:
        print(f"Policy Set:    {s['id']} (v{s['version']})")
        print(f"Path:          {s['path']}")
        print(f"As Of:         {s['as_of']} | Jurisdictions: {', '.join(s['jurisdictions'])}")
        print(f"Description:   {s['description']}")
        print(f"Rules ({s['rules_count']}):")
        for r in s["rules"]:
            print(f"  - [{r['severity'].upper():<5}] {r['id']:<35} {r['description']}")
        print("-" * 80)
    print("Check policy: fincrime policy check --set default --artifact <path>")
    print("Export policy: fincrime policy export --set default --out <path>")
    print("=" * 80)
    return EXIT_OK


def cmd_policy_check(args: argparse.Namespace) -> int:
    """Evaluate a policy set against an artifact, or inspect the set itself."""
    set_path = _resolve_policy_set_path(getattr(args, "set", None))
    if set_path is None or not set_path.is_file():
        print(f"error: policy set '{args.set}' not found", file=sys.stderr)
        return EXIT_USAGE

    try:
        policy_set = load_policy_set(set_path)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_FINDINGS

    artifact_arg = getattr(args, "artifact", None)
    if not artifact_arg:
        # Just inspect the policy set itself
        print(f"policy set: {set_path} ({policy_set.id} {policy_set.version})")
        print(f"as of: {policy_set.as_of}  jurisdictions: {', '.join(policy_set.jurisdictions)}")
        print(f"rules: {len(policy_set.rules)}")
        for rule in policy_set.rules:
            print(f"  [{rule.severity.upper():<5}] {rule.id:<35} {rule.description}")
        return EXIT_OK

    artifact_path = Path(artifact_arg)
    if not artifact_path.is_file():
        print(f"error: artifact '{artifact_path}' does not exist", file=sys.stderr)
        return EXIT_USAGE

    with artifact_path.open("r", encoding="utf-8") as handle:
        artifact = json.load(handle)

    try:
        finding = parse_finding(artifact)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_FINDINGS

    evaluator = PolicyEvaluator(policy_set.rules)
    violations = evaluator.evaluate(finding)
    print(f"policy set: {set_path} ({policy_set.id} {policy_set.version})")
    print(f"artifact: {artifact_path}")
    print(f"violations: {len(violations)}")
    for violation in violations:
        print(f"  {violation.severity:5s}  {violation.rule_id}  {violation.message}")

    if getattr(args, "json", False):
        print()
        print(
            json.dumps(
                [
                    {
                        "rule_id": violation.rule_id,
                        "severity": violation.severity,
                        "message": violation.message,
                        "claim_id": violation.claim_id,
                    }
                    for violation in violations
                ],
                indent=2,
            )
        )

    errors = [violation for violation in violations if violation.severity == "error"]
    return EXIT_OK if not errors else EXIT_FINDINGS


def cmd_policy_export(args: argparse.Namespace) -> int:
    """Export a policy set to standard JSON format."""
    set_path = _resolve_policy_set_path(getattr(args, "set", None))
    if set_path is None or not set_path.is_file():
        print(f"error: policy set '{args.set}' not found", file=sys.stderr)
        return EXIT_USAGE

    try:
        policy_set = load_policy_set(set_path)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_FINDINGS

    document = export_policy_set(policy_set)
    if getattr(args, "out", None):
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(document, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
        print(f"wrote {out_path}")
        print(f"checksum: {document['checksum']}")
    else:
        print(json.dumps(document, indent=2))
    return EXIT_OK
