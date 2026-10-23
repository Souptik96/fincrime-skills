"""The ``fincrime`` command.

Five subcommands, and the order of the argument parser mirrors the order of
a contributor's work: make a skill, check it, export a policy set, check a
policy set against an artifact, and check a knowledge pack's integrity and
staleness.

Every command is deterministic given its inputs. The one thing that looks
like a clock is ``--as-of``: it is a parameter, and the resolved date is
printed in the output header, so a run is never silently date-dependent.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any, Sequence

from fincrime_core.contract.loader import parse_finding
from fincrime_core.eval.cases import validate_case_suite
from fincrime_core.knowledge.model import load_pack, validate_pack
from fincrime_core.paths import repo_root
from fincrime_core.policy.evaluator import PolicyEvaluator
from fincrime_core.policy.set import export_policy_set, load_policy_set
from fincrime_core.validate.validator import EnforcementContext, Validator

from fincrime_cli.demo import cmd_demo
from fincrime_cli.evalcmd import cmd_eval
from fincrime_cli.explain import cmd_explain
from fincrime_cli.knowledgecmd import (
    cmd_knowledge_check,
    cmd_knowledge_inspect,
    cmd_knowledge_list,
    cmd_knowledge_typologies,
    cmd_knowledge_validate,
)
from fincrime_cli.policycmd import (
    cmd_policy_check,
    cmd_policy_export,
    cmd_policy_list,
)
from fincrime_cli.scaffold import scaffold_skill
from fincrime_cli.skillcheck import check_skill_package

__all__ = ["main", "build_parser"]

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2

#: The default policy set, relative to the repository root.
DEFAULT_POLICY_SET = Path("policies") / "default" / "policy-set.json"

#: The directory holding the knowledge packs, relative to the repository root.
PACKS_DIR = Path("knowledge") / "packs"


def _repo_root() -> Path | None:
    return repo_root()


def _default_policy_set_path() -> Path | None:
    root = _repo_root()
    if root is None:
        return None
    candidate = root / DEFAULT_POLICY_SET
    return candidate if candidate.is_file() else None


def _packs_root() -> Path | None:
    root = _repo_root()
    if root is None:
        return None
    candidate = root / PACKS_DIR
    return candidate if candidate.is_dir() else None


def _print_findings(findings: Sequence[Any]) -> None:
    for finding in findings:
        severity = getattr(finding, "severity", "error")
        code = getattr(finding, "code", "FINDING")
        message = getattr(finding, "message", str(finding))
        print(f"  {severity:5s}  {code}  {message}")


def _resolved_as_of(args: argparse.Namespace) -> date:
    """The date a freshness check is made as of.

    ``--as-of`` is a parameter. When it is absent the date is today, and the
    resolved date is printed in the header, so a run is never silently
    date-dependent.
    """
    explicit = getattr(args, "as_of", None)
    return explicit if explicit is not None else date.today()


def _context_label(args: argparse.Namespace) -> str:
    """The enforcement context a check ran in."""
    return "promotion" if getattr(args, "promotion", False) else "release"


def _summary(counts: dict[str, int]) -> str:
    return (
        f"{counts.get('error', 0)} error(s), {counts.get('warn', 0)} warning(s)"
    )


def _count(findings: Sequence[Any]) -> dict[str, int]:
    counts = {"error": 0, "warn": 0, "info": 0}
    for finding in findings:
        severity = getattr(finding, "severity", "error")
        if severity in counts:
            counts[severity] += 1
    return counts


# -- new skill ---------------------------------------------------------


def _cmd_new_skill(args: argparse.Namespace) -> int:
    try:
        result = scaffold_skill(
            name=args.name,
            outdir=args.outdir,
            jurisdiction=args.jurisdiction,
            artifact_type=args.artifact_type,
            knowledge_pack=args.knowledge_pack or "",
            force=args.force,
        )
    except (FileExistsError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE

    print(f"Created {result.root}")
    for path in result.files:
        print(f"  {path.relative_to(result.root.parent)}")
    print()
    print("Next: fill in the purpose, the stage text and the case suite, then run")
    print(f"  fincrime validate {result.root}")
    return EXIT_OK


# -- validate ----------------------------------------------------------


def _validate_skill(args: argparse.Namespace, path: Path) -> int:
    policy_set = None
    policy_path = args.policy_set or _default_policy_set_path()
    if policy_path is not None and Path(policy_path).is_file():
        policy_set = load_policy_set(policy_path)

    as_of = _resolved_as_of(args)
    result = check_skill_package(
        path,
        policy_set=policy_set,
        packs_root=_packs_root(),
        as_of=as_of,
        promotion=getattr(args, "promotion", False),
    )
    print(f"skill package: {path}")
    print(f"context: {_context_label(args)}  as of: {as_of.isoformat()}")
    print(f"findings: {_summary(_count(result.findings))}")
    _print_findings(result.findings)
    if result.maintenance_required:
        print("status: MAINTENANCE_REQUIRED")

    if args.json:
        print()
        print(
            json.dumps(
                {
                    "path": str(path),
                    "valid": result.valid,
                    "context": _context_label(args),
                    "as_of": as_of.isoformat(),
                    "maintenance_required": result.maintenance_required,
                    "findings": [finding.to_dict() for finding in result.findings],
                },
                indent=2,
            )
        )

    return EXIT_OK if result.valid else EXIT_FINDINGS


def _validate_suite(args: argparse.Namespace, path: Path) -> int:
    result = validate_case_suite(path)
    print(f"case suite: {path}")
    if result.suite is not None:
        suite = result.suite
        print(
            f"cases: {suite.case_count}  mixed: {suite.mixed_count} "
            f"({suite.mixed_ratio:.0%})  negative: {suite.negative_count} "
            f"({suite.negative_ratio:.0%})"
        )
    print(f"findings: {_summary(_count(result.findings))}")
    _print_findings(result.findings)

    if args.json:
        print()
        print(
            json.dumps(
                {
                    "path": str(path),
                    "valid": result.valid,
                    "findings": [finding.to_dict() for finding in result.findings],
                },
                indent=2,
            )
        )

    return EXIT_OK if result.valid else EXIT_FINDINGS


def _validate_pack(args: argparse.Namespace, path: Path) -> int:
    as_of = _resolved_as_of(args)
    promotion = getattr(args, "promotion", False)
    result = validate_pack(path, promotion=promotion, as_of=as_of)
    print(f"knowledge pack: {path}")
    print(f"context: {_context_label(args)}  as of: {as_of.isoformat()}")
    print(f"records: {len(result.records)}  checksum: {'ok' if result.checksum_ok else 'MISMATCH'}")
    print(f"findings: {_summary(_count(result.findings))}")
    _print_findings(result.findings)

    if args.json:
        print()
        print(
            json.dumps(
                {
                    "path": str(path),
                    "valid": result.valid,
                    "context": _context_label(args),
                    "as_of": as_of.isoformat(),
                    "checksum_ok": result.checksum_ok,
                    "findings": [finding.to_dict() for finding in result.findings],
                },
                indent=2,
            )
        )

    return EXIT_OK if result.valid else EXIT_FINDINGS


def _validate_artifact(args: argparse.Namespace, path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        artifact = json.load(handle)

    evidence_set: dict[str, Any] = {}
    if args.evidence_set:
        with Path(args.evidence_set).open("r", encoding="utf-8") as handle:
            evidence_set = json.load(handle)

    expired: list[str] = []
    known: list[str] = []
    known_indicators: list[str] = []
    if args.knowledge_pack:
        pack = load_pack(args.knowledge_pack)
        known = [record.id for record in pack.records]
        known_indicators = list(pack.indicator_ids())
        if args.as_of is not None:
            expired = [
                record.id for record in pack.records if record.is_expired(args.as_of)
            ]

    validator = Validator(
        evidence_set=evidence_set,
        known_indicator_ids=known_indicators or None,
        known_knowledge_ids=known or None,
        expired_knowledge_ids=expired or None,
    )
    enforcement = (
        EnforcementContext(EnforcementContext.PROMOTION)
        if args.promotion
        else EnforcementContext(EnforcementContext.RELEASE)
    )
    result = validator.validate(artifact, enforcement)

    print(f"artifact: {path}")
    print(f"valid: {result.valid}")
    print(
        "metrics: "
        f"evidence_attribution_accuracy={result.evidence_attribution_accuracy:.3f} "
        f"unsupported_claim_rate={result.unsupported_claim_rate:.3f}"
    )
    _print_findings(result.defects)

    if args.json:
        print()
        print(json.dumps(result.to_dict(), indent=2))

    return EXIT_OK if result.valid else EXIT_FINDINGS


def _validate_policy_set(args: argparse.Namespace, path: Path) -> int:
    try:
        policy_set = load_policy_set(path)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_FINDINGS
    print(f"policy set: {path}")
    print(f"id: {policy_set.id}  version: {policy_set.version}  rules: {len(policy_set.rules)}")
    return EXIT_OK


def _cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if not path.exists():
        print(f"error: {path} does not exist", file=sys.stderr)
        return EXIT_USAGE

    if path.is_dir():
        if (path / "SKILL.md").exists() or (path / "fincrime.skill.yaml").exists():
            return _validate_skill(args, path)
        if (path / "suite.json").exists():
            return _validate_suite(args, path)
        if (path / "manifest.json").exists():
            return _validate_pack(args, path)
        print(
            f"error: {path} is not a skill package, a case suite, or a knowledge pack",
            file=sys.stderr,
        )
        return EXIT_USAGE

    if path.suffix in (".yaml", ".yml"):
        return _validate_policy_set(args, path)
    if path.suffix == ".json":
        if args.policy_set is not None or _is_policy_set(path):
            return _validate_policy_set(args, path)
        return _validate_artifact(args, path)

    print(f"error: cannot tell what {path} is", file=sys.stderr)
    return EXIT_USAGE


def _is_policy_set(path: Path) -> bool:
    try:
        load_policy_set(path)
    except (OSError, ValueError):
        return False
    return True


# -- policy ------------------------------------------------------------


def _cmd_policy_export(args: argparse.Namespace) -> int:
    try:
        policy_set = load_policy_set(args.set)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_FINDINGS

    document = export_policy_set(policy_set)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(
            json.dumps(document, indent=2) + "\n", encoding="utf-8", newline="\n"
        )
        print(f"wrote {args.out}")
        print(f"checksum: {document['checksum']}")
    else:
        print(json.dumps(document, indent=2))
    return EXIT_OK


def _cmd_policy_check(args: argparse.Namespace) -> int:
    try:
        policy_set = load_policy_set(args.set)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_FINDINGS

    with Path(args.artifact).open("r", encoding="utf-8") as handle:
        artifact = json.load(handle)

    try:
        finding = parse_finding(artifact)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_FINDINGS

    evaluator = PolicyEvaluator(policy_set.rules)
    violations = evaluator.evaluate(finding)
    print(f"policy set: {args.set} ({policy_set.id} {policy_set.version})")
    print(f"artifact: {args.artifact}")
    print(f"violations: {len(violations)}")
    for violation in violations:
        print(f"  {violation.severity:5s}  {violation.rule_id}  {violation.message}")

    if args.json:
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


# -- knowledge ---------------------------------------------------------


def _cmd_knowledge_validate(args: argparse.Namespace) -> int:
    return _validate_pack(args, Path(args.pack))


def _cmd_knowledge_check(args: argparse.Namespace) -> int:
    from fincrime_core.knowledge.expiry import plan_expiry_actions

    path = Path(args.pack)
    try:
        pack = load_pack(path)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_FINDINGS

    as_of = args.as_of or date.today()
    actions = plan_expiry_actions(pack, as_of)

    print(f"knowledge pack: {path} ({pack.id} {pack.version})")
    print(f"as of: {as_of.isoformat()}")
    print(f"records: {len(pack.records)}  stale: {len(actions)}")

    if args.json:
        print()
        print(
            json.dumps(
                {
                    "pack": pack.id,
                    "version": pack.version,
                    "as_of": as_of.isoformat(),
                    "actions": [action.to_dict() for action in actions],
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


# -- parser ------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="fincrime",
        description=(
            "Scaffold, validate and inspect financial-crime skills. Every check "
            "is deterministic: a finding is a diff, not a claim."
        ),
    )
    parser.add_argument(
        "--version", action="store_true", help="print the version and exit"
    )
    subparsers = parser.add_subparsers(dest="command")

    # new
    new_parser = subparsers.add_parser("new", help="create a new skill package")
    new_subparsers = new_parser.add_subparsers(dest="new_command")
    new_skill = new_subparsers.add_parser("skill", help="scaffold a skill package")
    new_skill.add_argument("name", help="the skill name, in kebab-case")
    new_skill.add_argument(
        "--outdir", default="skills", help="the directory to write the package into"
    )
    new_skill.add_argument(
        "--jurisdiction", default="US", help="the jurisdiction scope of the skill"
    )
    new_skill.add_argument(
        "--artifact-type", default=None, help="the artifact type the skill produces"
    )
    new_skill.add_argument(
        "--knowledge-pack", default=None, help="the knowledge pack the skill depends on"
    )
    new_skill.add_argument(
        "--force", action="store_true", help="overwrite the scaffolded files"
    )
    new_skill.set_defaults(func=_cmd_new_skill)

    # validate
    validate_parser = subparsers.add_parser(
        "validate", help="validate a skill package, case suite, pack, policy set or artifact"
    )
    validate_parser.add_argument("path", help="what to validate")
    validate_parser.add_argument(
        "--policy-set", default=None, help="the policy set the manifest's policy ids resolve against"
    )
    validate_parser.add_argument(
        "--evidence-set", default=None, help="the evidence set an artifact was produced against"
    )
    validate_parser.add_argument(
        "--knowledge-pack", default=None, help="the knowledge pack an artifact cites"
    )
    validate_parser.add_argument(
        "--as-of", type=date.fromisoformat, default=None, help="the date the check is made as of"
    )
    validate_parser.add_argument(
        "--promotion",
        action="store_true",
        help="apply the promotion enforcement context: stale knowledge blocks",
    )
    validate_parser.add_argument("--json", action="store_true", help="emit the findings as JSON")
    validate_parser.set_defaults(func=_cmd_validate)

    # policy
    policy_parser = subparsers.add_parser("policy", help="list, export and check policy sets")
    policy_subparsers = policy_parser.add_subparsers(dest="policy_command")
    policy_list = policy_subparsers.add_parser(
        "list", help="list available policy sets and rules"
    )
    policy_list.add_argument(
        "--policies-dir", default=None, help="directory containing policy sets"
    )
    policy_list.add_argument(
        "--format", choices=["text", "json"], default="text", help="output format"
    )
    policy_list.add_argument("--json", action="store_true", help="emit policy sets as JSON")
    policy_list.set_defaults(func=cmd_policy_list)

    policy_export = policy_subparsers.add_parser("export", help="export a policy set")
    policy_export.add_argument(
        "--set", default="default", dest="set", help="the policy set to export (defaults to default)"
    )
    policy_export.add_argument("--out", default=None, help="where to write the export")
    policy_export.set_defaults(func=cmd_policy_export)

    policy_check = policy_subparsers.add_parser(
        "check", help="evaluate a policy set against an artifact"
    )
    policy_check.add_argument(
        "--set", default="default", dest="set", help="the policy set (defaults to default)"
    )
    policy_check.add_argument(
        "--artifact", default=None, help="the finding document (optional: checks policy set if omitted)"
    )
    policy_check.add_argument("--json", action="store_true", help="emit the violations as JSON")
    policy_check.set_defaults(func=cmd_policy_check)

    # knowledge
    knowledge_parser = subparsers.add_parser("knowledge", help="list, inspect, and check knowledge packs")
    knowledge_subparsers = knowledge_parser.add_subparsers(dest="knowledge_command")

    knowledge_list = knowledge_subparsers.add_parser(
        "list", help="list available knowledge packs and record counts"
    )
    knowledge_list.add_argument(
        "--packs-dir", default=None, help="directory containing knowledge packs"
    )
    knowledge_list.add_argument(
        "--as-of",
        type=date.fromisoformat,
        default=None,
        help="date for freshness checks",
    )
    knowledge_list.add_argument(
        "--format", choices=["text", "json"], default="text", help="output format"
    )
    knowledge_list.add_argument("--json", action="store_true", help="emit knowledge packs as JSON")
    knowledge_list.set_defaults(func=cmd_knowledge_list)

    knowledge_inspect = knowledge_subparsers.add_parser(
        "inspect", help="inspect an indicator or knowledge record"
    )
    knowledge_inspect.add_argument(
        "--indicator", default=None, help="the indicator ID to inspect"
    )
    knowledge_inspect.add_argument(
        "--record", default=None, help="the record ID to inspect"
    )
    knowledge_inspect.add_argument(
        "--pack", default=None, help="pack directory to search (defaults to knowledge/packs)"
    )
    knowledge_inspect.add_argument(
        "--as-of",
        type=date.fromisoformat,
        default=None,
        help="date for freshness checks",
    )
    knowledge_inspect.add_argument(
        "--format", choices=["text", "json"], default="text", help="output format"
    )
    knowledge_inspect.add_argument("--json", action="store_true", help="emit inspection report as JSON")
    knowledge_inspect.set_defaults(func=cmd_knowledge_inspect)

    knowledge_typologies = knowledge_subparsers.add_parser(
        "typologies", help="list the 12 AML/CTF typologies and paired benign twins"
    )
    knowledge_typologies.add_argument(
        "--format", choices=["text", "json"], default="text", help="output format"
    )
    knowledge_typologies.add_argument("--json", action="store_true", help="emit typologies as JSON")
    knowledge_typologies.set_defaults(func=cmd_knowledge_typologies)

    knowledge_validate = knowledge_subparsers.add_parser(
        "validate", help="check a pack's integrity against its manifest"
    )
    knowledge_validate.add_argument("--pack", required=True, help="the pack directory")
    knowledge_validate.add_argument(
        "--as-of",
        type=date.fromisoformat,
        default=None,
        help="the date the freshness check is made as of (defaults to today)",
    )
    knowledge_validate.add_argument(
        "--promotion",
        action="store_true",
        help="apply the promotion enforcement context: an expired record blocks",
    )
    knowledge_validate.add_argument("--json", action="store_true", help="emit the findings as JSON")
    knowledge_validate.set_defaults(func=cmd_knowledge_validate)

    knowledge_check = knowledge_subparsers.add_parser(
        "check", help="plan the refreshes a pack needs"
    )
    knowledge_check.add_argument("--pack", required=True, help="the pack directory")
    knowledge_check.add_argument(
        "--as-of",
        type=date.fromisoformat,
        default=None,
        help="the date the check is made as of (defaults to today)",
    )
    knowledge_check.add_argument("--json", action="store_true", help="emit the plan as JSON")
    knowledge_check.set_defaults(func=cmd_knowledge_check)

    # eval
    eval_parser = subparsers.add_parser("eval", help="evaluate skills against test suites and gates")
    eval_parser.add_argument("--skill", default=None, help="skill name, directory, or 'all'")
    eval_parser.add_argument("--suite", default=None, help="path to evaluation suite directory or suite.json")
    eval_parser.add_argument("--replay", action="store_true", help="run offline against pre-recorded replay corpus")
    eval_parser.add_argument("--mock", action="store_true", help="run against deterministic mock provider")
    eval_parser.add_argument("--gates", action="store_true", help="enforce manifest evaluation gates (exit 1 on breach)")
    eval_parser.add_argument(
        "--format", choices=["markdown", "json"], default="markdown", help="output report format"
    )
    eval_parser.add_argument("--out", default=None, help="write evaluation report to specified file")
    eval_parser.add_argument(
        "--as-of",
        type=date.fromisoformat,
        default=None,
        help="date for freshness and knowledge expiration checks",
    )
    eval_parser.set_defaults(func=cmd_eval)

    # demo
    demo_parser = subparsers.add_parser(
        "demo", help="demonstrate the Finding Contract vs unconstrained LLMs"
    )
    demo_parser.add_argument(
        "--skill", default="alert-triage", help="the skill to demonstrate (default: alert-triage)"
    )
    demo_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="run without pauses or interactive prompts",
    )
    demo_parser.add_argument(
        "--json", action="store_true", help="emit the demonstration result as JSON"
    )
    demo_parser.set_defaults(func=cmd_demo)

    # explain
    explain_parser = subparsers.add_parser(
        "explain", help="explain validation rules, defect codes, and artifact failures"
    )
    explain_parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help="the rule ID, defect code, or policy ID to explain",
    )
    explain_parser.add_argument(
        "--artifact", default=None, help="the finding artifact to validate and explain"
    )
    explain_parser.add_argument(
        "--evidence-set",
        default=None,
        help="the evidence set the artifact was produced against",
    )
    explain_parser.add_argument(
        "--policy-set", default=None, help="the policy set to check against"
    )
    explain_parser.add_argument(
        "--as-of",
        type=date.fromisoformat,
        default=None,
        help="the date the check is made as of",
    )
    explain_parser.add_argument(
        "--list",
        action="store_true",
        help="list all explainable rules and defect codes",
    )
    explain_parser.add_argument(
        "--json", action="store_true", help="emit the explanation as JSON"
    )
    explain_parser.set_defaults(func=cmd_explain)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if getattr(args, "version", False):
        from fincrime_cli import __version__

        print(f"fincrime {__version__}")
        return EXIT_OK

    if not hasattr(args, "func"):
        parser.print_help()
        return EXIT_USAGE

    try:
        return int(args.func(args))
    except BrokenPipeError:  # pragma: no cover - depends on the shell
        return EXIT_OK
    except KeyboardInterrupt:  # pragma: no cover - interactive
        print("interrupted", file=sys.stderr)
        return EXIT_USAGE


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
