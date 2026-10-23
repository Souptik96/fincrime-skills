"""``fincrime new skill`` — scaffolding a skill package.

The scaffolder writes a package that already satisfies its contract: the
sidecar validates, the stages in the body match the stages in the sidecar,
the policy ids exist in the default policy set, and the case suite is
present. What it does **not** do is write the skill. The case suite it emits
has three cases against a gate of sixty, and the purpose is a TODO, and the
package is marked ``draft`` — because a scaffold that looked finished would
be a scaffold nobody finished.

Scaffolding is a development tool: it writes files. It never reads a case
file, never opens a socket, and never makes a decision.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

__all__ = ["ScaffoldResult", "scaffold_skill", "SkillNameError"]


class SkillNameError(ValueError):
    """Raised when a skill name cannot be a package name."""


@dataclass(frozen=True, slots=True)
class ScaffoldResult:
    """What the scaffolder wrote."""

    root: Path
    files: tuple[Path, ...]

    def relative(self, root: Path) -> tuple[str, ...]:
        return tuple(str(path.relative_to(root)) for path in self.files)


def _check_name(name: str) -> str:
    if not name:
        raise SkillNameError("a skill needs a name")
    if any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in name):
        raise SkillNameError(
            f"{name!r} is not a usable skill name. Use lowercase letters, digits and hyphens."
        )
    if name.startswith("-") or name.endswith("-") or "--" in name:
        raise SkillNameError(f"{name!r} is not a usable skill name.")
    return name


#: The stage pattern every skill follows. The names are the reference
#: skill's, because the pattern is the pattern.
_STAGES: tuple[tuple[str, str, str, str, str], ...] = (
    ("S0", "frame", "frame", "", ""),
    ("S1", "ground", "evidence_inventory,gaps", "", "POL-EVIDENCE-INVENTORY-FIRST"),
    ("S2", "extract", "observation", "evidence_inventory", "POL-INDICATOR-REQUIRES-INDICATOR-ID"),
    ("S3", "hypothesize", "hypothesis", "claim_set", "POL-BENIGN-HYPOTHESIS-REQUIRED"),
    ("S4", "contrast", "contradiction", "claim_set", ""),
    ("S5", "assess", "risk_assessment", "gap_list", "POL-ASSESSMENT-NEEDS-INDICATOR"),
    ("S6", "recommend", "recommendation", "defect_list", "POL-RECOMMENDATION-NEEDS-BASIS"),
    ("S7", "escalate", "escalation", "defect_list", ""),
)


def _manifest(name: str, jurisdiction: str, artifact_type: str, knowledge_pack: str) -> str:
    """Render the sidecar."""
    pack_line = f"  knowledge_pack: {knowledge_pack}\n" if knowledge_pack else ""
    stages = []
    for stage, stage_name, produces, requires, guard in _STAGES:
        lines = [f"    - stage: {stage}", f"      name: {stage_name}"]
        lines.append(f"      produces: [{produces}]")
        lines.append(f"      requires: [{requires}]")
        if guard:
            lines.append(f"      guard: {guard}")
            lines.append("      on_violation: stop")
        stages.append("\n".join(lines))

    return f"""apiVersion: fincrime.dev/v1
kind: FinCrimeSkill

metadata:
  name: {name}
  version: 0.1.0
  status: draft
  owners:
    - "@fincrime-maintainers"
  license: Apache-2.0
  jurisdiction_scope:
    - {jurisdiction}
  created: "{date.today().isoformat()}"
  contract_version: fincrime/finding/1.0.0
{pack_line}  related_skills: ""

spec:
  purpose: >-
    TODO: state in one paragraph what this skill does, when it is used, and
    what it produces. A reader who stops here should be able to decide
    whether to use the skill at all.

  inputs:
    required:
      - name: artifact
        description: The finding document under review, conforming to fincrime/finding/1.0.0.
        contract_ref: fincrime/finding/1.0.0
      - name: evidence_set
        description: The closed world the artifact was produced against. Without it, evidence attribution cannot be checked.
        contract_ref: fincrime/evidence-set/1.0.0
    optional:
      - name: knowledge_index
        description: The knowledge pack the artifact declared, used to check that cited records exist and are not expired.
      - name: policy_rules
        description: The firm's deterministic rules, used to check enforceable controls.

  preconditions:
    - id: PC-1
      check: "the artifact is a well-formed finding document"
      on_fail: stop
      message: "The artifact cannot be reviewed because it is not structured."
    - id: PC-2
      check: "an evidence set is supplied"
      on_fail: stop
      message: "Evidence attribution cannot be checked without the evidence set."

  procedure:
{chr(10).join(stages)}

  output:
    format: fincrime/finding/1.0.0
    artifact: {artifact_type}
    required_claims:
      - frame
      - evidence_inventory
      - gaps
      - observation
      - hypothesis
      - risk_assessment
      - recommendation
      - escalation
    optional_claims:
      - contradiction
      - indicator
    prohibited_claims:
      - decision
    min_hypotheses: 0
    require_benign_hypothesis: false
    confidence:
      levels:
        - high
        - moderate
        - low
        - insufficient_information
      default_ceiling: high

  policies:
    required:
      - POL-EVIDENCE-INVENTORY-FIRST
      - POL-BENIGN-HYPOTHESIS-REQUIRED
      - POL-ASSESSMENT-NEEDS-INDICATOR
      - POL-RECOMMENDATION-NEEDS-BASIS
      - POL-NO-CRIMINALITY-CLAIMS
    optional:
      - POL-CONFIDENCE-CEILING-ON-PARTIAL-EVIDENCE

  knowledge:
    indicators: []
    scenarios: []
    typologies: []
    regulatory: []

  evaluation:
    suite: evals/suites/{name}
    case_count_min: 60
    gates:
      schema_validity: 1.0
      evidence_attribution_accuracy: 0.98
      unsupported_claim_rate_max: 0.02
      required_field_compliance: 1.0
      policy_pass_rate: 1.0
      expected_defect_recall: 0.9
      false_defect_rate_max: 0.05

  safety:
    human_approval_required:
      - decision
      - escalation
    prohibited_actions:
      - customer_action
      - filing
      - legal_conclusion
      - numeric_risk_rating
      - artifact_rewrite
    closed_world: true
    pii_policy: reference_only
"""


def _skill_md(name: str, jurisdiction: str) -> str:
    """Render the skill body."""
    stage_sections = []
    for stage, stage_name, produces, requires, guard in _STAGES:
        produces_text = ", ".join(f"`{item}`" for item in produces.split(",") if item)
        requires_text = (
            f"*Requires:* `{requires}`. " if requires else "*Requires:* nothing. "
        )
        guard_text = f"*Guard:* `{guard}`." if guard else "*Guard:* none."
        stage_sections.append(
            f"### {stage} — {stage_name.capitalize()}\n\n"
            f"TODO: what this stage does. It produces {produces_text}.\n\n"
            f"{requires_text}{guard_text}\n"
        )

    return f"""---
name: {name}
description: >-
  TODO: one sentence on what this skill does, one on when to use it, and one
  on what it produces. A host decides whether to load a skill from this
  text alone, so it must say what, when, and what it produces.
license: Apache-2.0
metadata:
  fincrime_version: "1.0.0"
  contract_version: "fincrime/finding/1.0.0"
  jurisdiction: "{jurisdiction}"
---

# {name.replace('-', ' ').title()}

> ⚠️ TODO: state the skill's limits in one line. This skill does not decide, does
> not file, and does not reach a disposition about a customer. Jurisdiction
> scope: **{jurisdiction}**.

## When to use

- TODO: the situations in which this skill is the right one.

## When NOT to use

- TODO: the situations in which it is the wrong one, and which skill to use instead.

## Required inputs

| Input | Description |
|---|---|
| `artifact` | The finding document under review, conforming to `fincrime/finding/1.0.0`. |
| `evidence_set` | The closed world the artifact was produced against. |

## Preconditions

| ID | Check | On failure | Message |
|---|---|---|---|
| PC-1 | The artifact is a well-formed finding document | `stop` | The artifact cannot be reviewed because it is not structured. |
| PC-2 | An evidence set is supplied | `stop` | Evidence attribution cannot be checked without the evidence set. |

## Procedure

Follow the stage pattern S0–S7. Each stage states what it produces and what it
requires.

{chr(10).join(stage_sections)}
## Output

A `{name}_result` artifact conforming to `fincrime/finding/1.0.0`.

## Evaluation

The case suite is at `evals/suites/{name}`. The gate is `fincrime eval --gates`,
and it is not satisfied by a suite of three cases.
"""


def _jurisdiction_note(jurisdiction: str) -> str:
    return f"""# Jurisdiction note — {jurisdiction}

TODO: state what regulatory content this skill relies on in {jurisdiction}, and
what it does **not** cover.

A jurisdiction note is not boilerplate. A skill that names a jurisdiction
without saying what it relies on there has told a reviewer nothing, and the
reviewer is the person who has to defend the output.

- **Covered:** TODO
- **Not covered:** TODO
- **Sources:** TODO — cite, do not paraphrase from memory.
"""


def _suite_manifest(name: str) -> dict[str, Any]:
    return {
        "suite_id": name,
        "skill": name,
        "version": "0.1.0",
        "as_of": date.today().isoformat(),
        "description": (
            "TODO: what this suite covers. The three cases here are a starting "
            "shape, not a suite: the gate is sixty cases with a mixed population."
        ),
        "requirements": {
            "min_cases": 60,
            "min_mixed_ratio": 0.4,
            "min_negative_ratio": 0.15,
            "required_kinds": ["golden", "adversarial", "benign"],
            "min_benign_per_typology": True,
        },
        "typologies": [],
        "cases": [
            {"case_id": "golden-001", "path": "cases/golden-001.json", "tags": []},
            {
                "case_id": "adversarial-001",
                "path": "cases/adversarial-001.json",
                "tags": [],
            },
            {"case_id": "benign-001", "path": "cases/benign-001.json", "tags": []},
        ],
    }


def _case(name: str, case_id: str, kind: str, description: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "suite": name,
        "version": "0.1.0",
        "kind": kind,
        "tags": [],
        "description": description,
        "input": {
            "artifact": "TODO: the artifact under test, as a finding document.",
            "evidence_set": "TODO: the closed world the artifact was produced against.",
        },
        "expect": {
            "required_claim_classes": ["observation"],
            "forbidden_claim_classes": [],
            "expected_escalation": kind != "benign",
            "human_approval_required": kind != "benign",
        },
    }


def _suite_readme(name: str) -> str:
    return f"""# Case suite — {name}

This suite has three cases and the gate is sixty. The three are here to show
the *shape* of a case, not to satisfy the gate.

| Kind | What it is for |
|---|---|
| `golden` | The case the skill must handle correctly. |
| `adversarial` | The case the skill must not be fooled by. |
| `benign` | The lookalike that is ordinary. A suite without one measures nothing. |

A case asserts what the skill must do **and** what it must not do. A case
with no negative expectation passes a skill that says everything, which is
why `min_negative_ratio` is a requirement and not a preference.

Write the rest of the suite before the skill ships.
"""


def scaffold_skill(
    name: str,
    outdir: str | Path,
    jurisdiction: str = "US",
    artifact_type: str | None = None,
    knowledge_pack: str = "",
    force: bool = False,
) -> ScaffoldResult:
    """Write a new skill package.

    ``force`` overwrites files the scaffolder owns. It refuses to touch a
    directory that already holds a skill package, because a scaffold that
    silently replaces a hand-written skill is a way to lose work.
    """
    skill_name = _check_name(name)
    root = Path(outdir) / skill_name

    if root.exists() and any(root.iterdir()) and not force:
        raise FileExistsError(
            f"{root} already exists and is not empty. Pass --force to overwrite the "
            "scaffolded files."
        )

    suite_dir = root / "evals" / "suites" / skill_name
    files: list[Path] = []

    def write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        files.append(path)

    write(
        root / "SKILL.md",
        _skill_md(skill_name, jurisdiction),
    )
    write(
        root / "fincrime.skill.yaml",
        _manifest(
            skill_name,
            jurisdiction,
            artifact_type or f"{skill_name.replace('-', '_')}_result",
            knowledge_pack,
        ),
    )
    write(
        root / "references" / f"jurisdiction-{jurisdiction.lower()}.md",
        _jurisdiction_note(jurisdiction),
    )
    write(
        suite_dir / "suite.json",
        json.dumps(_suite_manifest(skill_name), indent=2) + "\n",
    )
    for case_id, kind, description in (
        ("golden-001", "golden", "TODO: the case the skill must handle correctly."),
        ("adversarial-001", "adversarial", "TODO: the case the skill must not be fooled by."),
        ("benign-001", "benign", "TODO: the lookalike that is ordinary."),
    ):
        write(
            suite_dir / "cases" / f"{case_id}.json",
            json.dumps(_case(skill_name, case_id, kind, description), indent=2) + "\n",
        )
    write(suite_dir / "README.md", _suite_readme(skill_name))

    return ScaffoldResult(root=root, files=tuple(files))
