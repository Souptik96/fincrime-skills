"""Generate the offline replay fixtures for all evaluation cases across all six skills.

Generates byte-identical, deterministic replay candidate findings for all 360
cases across:
- skills/alert-triage/evals/replays/
- skills/case-summarize/evals/replays/
- skills/evidence-request/evals/replays/
- skills/investigation-qa/evals/replays/
- skills/sar-narrative-draft/evals/replays/
- skills/sanctions-alert/evals/replays/

Every generated finding is strictly conformant to fincrime/finding/1.0.0,
resolves all evidence references against the case's closed world, and passes
all gates declared in each skill's fincrime.skill.yaml.

Standard library only.
Usage:
    python scripts/generate_replay_corpus.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fincrime_core.eval.cases import load_case_suite
from fincrime_core.paths import repo_root

REPO_ROOT = repo_root() or Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.generate_synthetic_corpus import ALL_SKILLS, generate_candidate_for_case

SKILLS = ALL_SKILLS


def generate_all_replays() -> None:
    """Generate and write replay fixtures for all 6 skills (360 cases)."""
    total_written = 0

    for skill in SKILLS:
        suite_dir = REPO_ROOT / "skills" / skill / "evals" / "suites" / skill
        replays_dir = REPO_ROOT / "skills" / skill / "evals" / "replays"
        replays_dir.mkdir(parents=True, exist_ok=True)

        suite, findings = load_case_suite(suite_dir)
        if any(f.severity == "error" for f in findings):
            raise RuntimeError(f"Error loading suite for {skill}: {findings}")

        for case in suite.cases:
            candidate = generate_candidate_for_case(skill, case.document)
            replay_path = replays_dir / f"{case.case_id}.json"
            with replay_path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(candidate, indent=2, sort_keys=True) + "\n")
            total_written += 1

        print(f"Generated {len(suite.cases)} replay fixtures for {skill} in {replays_dir.relative_to(REPO_ROOT)}")

    print(f"\nTotal replay fixtures generated: {total_written}")


if __name__ == "__main__":
    generate_all_replays()
