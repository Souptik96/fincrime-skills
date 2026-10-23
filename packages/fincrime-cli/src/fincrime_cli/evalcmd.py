"""CLI dispatcher and reporting for ``fincrime eval``.

Executes evaluation suites against candidate provider adapters (offline replay,
mock defect injector, or model adapters), scores outputs deterministically,
evaluates manifest regression gates, and formats reports as markdown or JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Sequence

from fincrime_core.eval.cases import load_case_suite
from fincrime_core.eval.metrics import GateEvaluationResult, GateEvaluator, MetricAggregator
from fincrime_core.eval.providers.mock import MockProvider
from fincrime_core.eval.providers.replay import ReplayProvider
from fincrime_core.eval.runner import CaseRunnerPipeline, SuiteExecutionResult
from fincrime_core.knowledge.model import load_pack
from fincrime_core.paths import repo_root
from fincrime_core.policy.evaluator import PolicyEvaluator
from fincrime_core.policy.set import load_policy_set

from fincrime_cli.yamlite import parse_file

__all__ = ["eval_suite", "cmd_eval", "format_markdown_report"]

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2


def _resolve_skill_dir(skill_arg: str, root: Path | None) -> Path:
    p = Path(skill_arg)
    if p.is_dir() and (p / "fincrime.skill.yaml").exists():
        return p
    if root is not None:
        candidate = root / "skills" / skill_arg
        if candidate.is_dir():
            return candidate
    raise ValueError(f"Could not locate skill directory for: {skill_arg}")


def _load_knowledge_context(
    root: Path | None, as_of: date | None = None
) -> tuple[list[str], list[str], list[str]]:
    """Loads known indicator ids, knowledge ids, and expired ids from default packs."""
    known_indicators: list[str] = []
    known_ids: list[str] = []
    expired_ids: list[str] = []

    if root is None:
        return known_indicators, known_ids, expired_ids

    packs_dir = root / "knowledge" / "packs"
    if not packs_dir.is_dir():
        return known_indicators, known_ids, expired_ids

    for pack_path in packs_dir.iterdir():
        if pack_path.is_dir() and (pack_path / "manifest.json").exists():
            try:
                pack = load_pack(pack_path)
                known_ids.extend([rec.id for rec in pack.records])
                known_indicators.extend(list(pack.indicator_ids()))
                if as_of is not None:
                    expired_ids.extend([r.id for r in pack.records if r.is_expired(as_of)])
            except Exception:
                pass

    return known_indicators, known_ids, expired_ids


def _load_policy_evaluator(root: Path | None) -> PolicyEvaluator | None:
    if root is None:
        return None
    default_policy = root / "policies" / "default" / "policy-set.json"
    if default_policy.is_file():
        try:
            return PolicyEvaluator(load_policy_set(default_policy).rules)
        except Exception:
            return None
    return None


def format_markdown_report(
    results: Sequence[SuiteExecutionResult],
    gates_enforced: bool = False,
    as_of: date | None = None,
) -> str:
    """Renders a human-readable Markdown evaluation report."""
    lines: list[str] = []
    lines.append("# FinCrime Skill Evaluation Report")
    lines.append("")
    if as_of:
        lines.append(f"- **As of Date:** `{as_of.isoformat()}`")
    lines.append(f"- **Suites Evaluated:** {len(results)}")
    all_passed = all(r.passed_all_gates for r in results)
    status_str = "PASS" if all_passed else "FAIL"
    lines.append(f"- **Overall Gate Status:** **{status_str}**")
    lines.append("")

    for res in results:
        lines.append(f"## Suite: `{res.suite_id}` (Skill: `{res.skill}`)")
        lines.append("")
        lines.append(
            f"- **Cases:** {res.passed_count}/{res.case_count} passed "
            f"({res.failed_count} failed) | **Duration:** {res.duration_ms:.1f}ms"
        )
        if gates_enforced:
            suite_gate_status = "PASS" if res.passed_all_gates else "BREACH"
            lines.append(f"- **Gate Evaluation:** **{suite_gate_status}**")
        lines.append("")

        lines.append("| Metric | Score | Gate Target | Gate Type | Status |")
        lines.append("| :--- | :---: | :---: | :---: | :---: |")

        gate_details = res.gate_results.gate_details if res.gate_results else {}

        # Canonical display order
        metrics_order = [
            "schema_validity",
            "evidence_attribution_accuracy",
            "unsupported_claim_rate",
            "required_field_compliance",
            "policy_pass_rate",
            "expected_defect_recall",
            "false_defect_rate",
        ]

        for metric in metrics_order:
            actual = res.metrics.get(metric, 0.0)
            detail = gate_details.get(metric)
            if not detail:
                # Check for _max suffix in gate details
                detail = gate_details.get(f"{metric}_max")

            if detail:
                target_str = f"{detail['target']:.4f}"
                type_str = detail["gate_type"]
                status = "PASS" if detail["passed"] else "**BREACH**"
            else:
                target_str = "-"
                type_str = "-"
                status = "INFO"

            lines.append(f"| `{metric}` | `{actual:.4f}` | {target_str} | {type_str} | {status} |")

        lines.append("")

        if res.gate_results and res.gate_results.breaches:
            lines.append("### Gate Breaches")
            for b in res.gate_results.breaches:
                lines.append(f"- ⚠️ **{b.metric}**: {b.message}")
            lines.append("")

    return "\n".join(lines)


def eval_suite(
    suite_path: Path,
    skill_dir: Path | None = None,
    provider: Any = None,
    enforce_gates: bool = False,
    as_of: date | None = None,
    root: Path | None = None,
) -> SuiteExecutionResult:
    """Executes a single evaluation suite."""
    manifest: dict[str, Any] = {}
    if skill_dir and (skill_dir / "fincrime.skill.yaml").exists():
        manifest = parse_file(skill_dir / "fincrime.skill.yaml")

    gates: dict[str, float] = {}
    if manifest:
        gates = manifest.get("evaluation", {}).get("gates", {})

    known_indicators, known_ids, expired_ids = _load_knowledge_context(root, as_of)
    policy_eval = _load_policy_evaluator(root)

    pipeline = CaseRunnerPipeline(
        provider=provider,
        known_indicator_ids=known_indicators,
        known_knowledge_ids=known_ids,
        expired_knowledge_ids=expired_ids,
        policy_evaluator=policy_eval,
    )

    return pipeline.run_suite(suite_path, manifest=manifest, gates=gates)


def cmd_eval(args: argparse.Namespace) -> int:
    """Entry point for ``fincrime eval`` subcommand."""
    root = repo_root()
    as_of: date | None = getattr(args, "as_of", None)

    # Determine skills to evaluate
    skill_dirs: list[Path] = []
    if getattr(args, "skill", None):
        if args.skill == "all":
            if root is not None:
                skills_parent = root / "skills"
                if skills_parent.is_dir():
                    for sk in sorted(skills_parent.iterdir()):
                        if sk.is_dir() and (sk / "fincrime.skill.yaml").exists() and (sk / "evals").is_dir():
                            skill_dirs.append(sk)
        else:
            try:
                skill_dirs.append(_resolve_skill_dir(args.skill, root))
            except ValueError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return EXIT_USAGE
    elif getattr(args, "suite", None):
        suite_path = Path(args.suite)
        if not suite_path.exists():
            print(f"error: suite path {suite_path} does not exist", file=sys.stderr)
            return EXIT_USAGE
        # Detect skill from suite path
        skill_name = suite_path.name if suite_path.is_dir() else suite_path.parent.name
        if root is not None and (root / "skills" / skill_name).is_dir():
            skill_dirs.append(root / "skills" / skill_name)
    else:
        print("error: specify --skill <name|all> or --suite <path>", file=sys.stderr)
        return EXIT_USAGE

    enforce_gates: bool = bool(getattr(args, "gates", False))
    use_replay: bool = bool(getattr(args, "replay", False))
    use_mock: bool = bool(getattr(args, "mock", False))
    output_format: str = getattr(args, "format", "markdown") or "markdown"
    out_path: str | None = getattr(args, "out", None)

    suite_results: list[SuiteExecutionResult] = []

    for s_dir in skill_dirs:
        # Determine suite path
        if getattr(args, "suite", None) and len(skill_dirs) == 1:
            s_path = Path(args.suite)
        else:
            s_path = s_dir / "evals" / "suites" / s_dir.name
            if not s_path.exists():
                # check if suite.json exists inside evals/suites/
                candidates = list((s_dir / "evals" / "suites").glob("*.json"))
                if candidates:
                    s_path = candidates[0]

        if not s_path.exists():
            print(f"error: suite for skill {s_dir.name} not found at {s_path}", file=sys.stderr)
            return EXIT_FINDINGS

        # Determine provider
        if use_mock:
            prov = MockProvider()
        elif use_replay or (s_dir / "evals" / "replays").is_dir():
            replay_dir = s_dir / "evals" / "replays"
            if not replay_dir.is_dir():
                print(f"error: replay dir {replay_dir} does not exist", file=sys.stderr)
                return EXIT_FINDINGS
            prov = ReplayProvider(replay_dir=replay_dir)
        else:
            print(
                f"error: no provider configured for skill {s_dir.name}. "
                "Specify --replay to run committed replay fixtures.",
                file=sys.stderr,
            )
            return EXIT_USAGE

        try:
            res = eval_suite(
                suite_path=s_path,
                skill_dir=s_dir,
                provider=prov,
                enforce_gates=enforce_gates,
                as_of=as_of,
                root=root,
            )
            suite_results.append(res)
        except Exception as exc:
            print(f"error evaluating {s_dir.name}: {exc}", file=sys.stderr)
            return EXIT_FINDINGS

    # Format output
    if output_format.lower() == "json":
        payload = {
            "suites": [r.to_dict() for r in suite_results],
            "passed_all_gates": all(r.passed_all_gates for r in suite_results),
            "enforce_gates": enforce_gates,
            "as_of": as_of.isoformat() if as_of else None,
        }
        output_text = json.dumps(payload, indent=2)
    else:
        output_text = format_markdown_report(
            suite_results, gates_enforced=enforce_gates, as_of=as_of
        )

    # Write to output file if requested
    if out_path:
        out_p = Path(out_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(output_text + "\n", encoding="utf-8")

    # Output to stdout safely across platform consoles
    try:
        print(output_text)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "ascii"
        print(output_text.encode(encoding, errors="replace").decode(encoding, errors="replace"))

    # If --gates was specified, return non-zero on any gate breach
    if enforce_gates:
        if not all(r.passed_all_gates for r in suite_results):
            return EXIT_FINDINGS

    return EXIT_OK
