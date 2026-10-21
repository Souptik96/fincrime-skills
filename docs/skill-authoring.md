# Writing a FinCrime skill

This guide is for someone who has not read the architecture. It is enough to
author a skill, validate it, and test it.

If you want the reasoning behind the rules — why the claim classes are
closed, why the evidence reference grammar is what it is — read the
[architecture decision records](adr/). If you want to change a *control*,
read the ADRs first, because every control here is enforceable by code and
every change to one is a change to what a firm can defend.

---

## 1. What a skill is

A skill is a directory with a body an agent reads and a sidecar a machine
reads:

```text
skills/my-skill/
├── SKILL.md                        # the body: what the agent does
├── fincrime.skill.yaml             # the sidecar: the machine contract
├── references/jurisdiction-us.md   # what this skill relies on, and where
└── evals/suites/my-skill/
    ├── suite.json                  # the suite manifest and its requirements
    └── cases/*.json                # the cases
```

The body and the sidecar are **additive**. A host that knows nothing about
FinCrime loads `SKILL.md` and works. The sidecar is what lets a host that
does know enforce anything.

Start with the scaffolder:

```bash
fincrime new skill my-skill --outdir skills
fincrime validate skills/my-skill
```

What it writes already satisfies the contract. What it does **not** do is
write the skill: the purpose is a TODO, the case suite has three cases
against a gate of sixty, and the package is marked `draft`. A scaffold that
looked finished would be a scaffold nobody finished.

---

## 2. `SKILL.md`: the body

The body has YAML frontmatter, then prose.

```markdown
---
name: my-skill
description: >-
  One sentence on what this skill does, one on when to use it, and one on
  what it produces.
license: Apache-2.0
metadata:
  contract_version: "fincrime/finding/1.0.0"
  jurisdiction: "US"
---

# My Skill

...
```

Three rules the checker enforces:

- **`name` must equal the directory name.** A host loads a skill by
  directory name; if the two disagree, nobody can tell which one is right.
- **`description` must say what, when, and what it produces.** A host decides
  whether to load a skill from this text alone.
- **The stages in the body must match the stages in the sidecar.** An agent
  reads the body; a host reads the sidecar.

### The stage pattern

Every skill follows S0–S7. The stages are the same in every skill because
the ordering is the control:

| Stage | Produces | The point |
|---|---|---|
| S0 Frame | `frame` | Establish what is under review, and against what closed world. |
| S1 Ground | `evidence_inventory`, `gaps` | Enumerate what evidence exists **before** asserting anything. |
| S2 Extract | `observation` | Check that each claim's references resolve. |
| S3 Hypothesize | `hypothesis` | Form the readings, including the benign one. |
| S4 Contrast | `contradiction` | Surface what conflicts. |
| S5 Assess | `risk_assessment` | State what the evidence supports, and no more. |
| S6 Recommend | `recommendation` | Say what to change, anchored to a claim. |
| S7 Escalate | `escalation` | Name the decision the human still owns. |

S1 before S2 is not a style preference. A claim made before the analyst
knows what evidence exists is a claim about a world the analyst has not
seen. That is the `POL-EVIDENCE-INVENTORY-FIRST` guard, and it is the one
guard the default policy set carries.

---

## 3. `fincrime.skill.yaml`: the sidecar

The sidecar is validated against
[`contracts/skill-manifest.schema.json`](../contracts/skill-manifest.schema.json).
The important parts:

### `metadata`

| Field | Notes |
|---|---|
| `name` | Kebab-case. Must equal the directory name and the frontmatter name. |
| `version` | Semantic version. |
| `status` | `draft`, `stable`, `deprecated`, `maintenance_required`. |
| `owners` | Who maintains it. A skill nobody owns is a skill nobody maintains. |
| `jurisdiction_scope` | Never empty, never `global`. |
| `contract_version` | The Finding Contract the skill produces, e.g. `fincrime/finding/1.0.0`. |
| `knowledge_pack` | The pack the skill depends on. Optional while the pack does not exist yet. |

### `spec.inputs`

Each input names a `contract_ref` — a contract **id**, not a path. A skill
is distributed on its own, without the repository, so it has to be able to
say which contract it needs.

### `spec.output`

`required_claims` and `optional_claims` name **output elements**: one of the
seven claim classes, or one of the structural sections of the Finding
Contract (`frame`, `evidence_inventory`, `gaps`, `contradiction`, `timeline`,
`escalation`, `draft_notice`). The vocabulary is closed, so a manifest
cannot promise an output nobody can produce.

`prohibited_claims` names what the skill must never produce. It must be
disjoint from `required_claims`; the checker rejects a skill that is
required to produce and forbidden to produce the same element.

Every stage's `produces` must be covered by `required_claims` or
`optional_claims`.

### `spec.policies`

The policy ids the skill depends on. A policy id is either **enforceable**
(evaluated by the policy engine) or **procedural** (followed by the agent and
measured by the evaluation suite). The distinction lives in the policy set,
not here; a manifest just names ids.

`fincrime validate` resolves every id — and every stage `guard` — against
the policy set, and fails if one does not exist. A skill may not depend on a
control nobody can point at.

### `spec.evaluation`

`suite` is the path to the case suite, `case_count_min` is the gate, and
`gates` are the metric thresholds the suite must meet.

### `spec.safety`

`human_approval_required` lists the outputs that a human must approve.
`prohibited_actions` lists what the skill may never do. `closed_world` is
always `true`: the evidence set is closed, and anything outside it cannot be
cited.

---

## 4. Writing claims that validate

This is the part that matters, and it is short.

### The seven claim classes

| Class | What it is | Evidence required |
|---|---|---|
| `fact` | Read directly from a record. | Yes |
| `observation` | A pattern in the evidence. | Yes |
| `indicator` | A named pattern from the knowledge pack. | Yes, plus an `indicator_id` |
| `hypothesis` | A reading of what the pattern might mean. | Yes, plus a `falsifier` and an `epistemic_type` |
| `risk_assessment` | What the evidence supports, stated as a confidence. | Either evidence or `insufficient_information` |
| `recommendation` | What to do next. | Evidence, or the claim it explains |
| `decision` | A decision that was made. | `decided_by` naming a human or a policy |

### The rules that fail your artifact

- **A reference that does not resolve fails the artifact.** Any reference,
  on any claim class. A fabricated reference cannot hide behind a class that
  merely declines to require one.
- **An adverse reading may not stand alone.** A `hypothesis` with
  `epistemic_type: adverse_reading` requires a competing
  `benign_reading` in the same artifact. This is structural: writing around
  a keyword filter does not work, because the requirement is a field, not a
  phrase.
- **A partial evidence set caps confidence.** A conclusion drawn from an
  incomplete window cannot be stated at `high`.
- **A recommendation must have a basis**, and a consequential one must
  require human approval. The skill layer may never assert that no approval
  is needed.
- **A decisive gap caps the assessment.** If a gap blocks the conclusion, the
  risk assessment is `low` or `insufficient_information`, never a graded
  judgement.
- **The artifact must name the decision the agent did not make.**

### The evidence reference grammar

Every reference is `<source_id>#<json-pointer>`, and the pointer is RFC 6901:

```jsonc
"evidence_refs": ["txn:8841#/amount", "subject:5512#/declared_profile/cash_intensity"]
```

- `source_id` is at least three characters, and may contain `:`.
- The pointer is `/`-separated, and `/` inside a key is `~1` and `~` is `~0`.
- An array index is `0` or a number with no leading zero.
- The whole pointer may be empty (`txn:8841#`), which means the whole
  source — but citing a collection is not evidence attribution, and the
  validator reports it.

Cite the specific value, not the document. One reference per item.

### Confidence

Never a number. One of `high`, `moderate`, `low`, `insufficient_information`,
with a `basis` that says why.

`insufficient_information` is a **successful terminal state**, not a failure.
An artifact that says "the evidence does not support a conclusion" is
correct, and it is a better artifact than one that guesses.

---

## 5. Policies

The default policy set is [`policies/default/policy-set.json`](../policies/default/policy-set.json).
It is the baseline every skill inherits, and it is the exportable,
firm-readable form of the core's structural lints.

```bash
fincrime policy check --set policies/default/policy-set.json \
    --artifact examples/01-alert-triage-structuring/artifact.json
```

A firm set overrides the default **rule by rule**, never wholesale. A firm
that tightens one control does not silently lose the others.

### Writing an enforceable rule

Six kinds, and no free-text expressions: `require`, `forbid`, `threshold`,
`count`, `consistency`, `composite`. If a constraint cannot be evaluated by
code, it does not belong in the policy layer — it belongs in the skill body
and is measured by the evaluation suite.

| Kind | What it does |
|---|---|
| `require` | A field must be present, or must have at least N entries. |
| `forbid` | A statement must not match a regular expression. |
| `threshold` | A numeric field must be within a range. |
| `count` | The number of matching claims must be within a range. |
| `consistency` | A field must equal a value. |
| `composite` | `all`, `any`, and `not` over other rules. |

Two things that are not obvious:

- **`when`** gates a rule on the artifact rather than on a claim, for
  example `{"field": "artifact.completeness", "equals": "partial"}`. It is
  how a rule reaches a property of the artifact header.
- **`require.any_of`** is a per-claim disjunction. `composite.any` is
  decided across the whole selected set, so it cannot say "this claim has
  evidence references *or* is stated as insufficient information".

`pattern` is a regular expression, matched case-insensitively. `forbid` also
takes `negation_aware: true`, which skips a sentence that carries a
negation — so "not suspected of structuring" is not a violation.

---

## 6. The case suite

The suite is the binding constraint on the whole project. A case with a
benign twin and a documented expected outcome is worth more than a new
skill.

```text
evals/suites/my-skill/
├── suite.json
└── cases/
    ├── golden-001.json
    ├── adversarial-001.json
    └── benign-001.json
```

### `suite.json`

```jsonc
{
  "suite_id": "my-skill",
  "skill": "my-skill",
  "version": "1.0.0",
  "as_of": "2026-10-21",
  "requirements": {
    "min_cases": 60,
    "min_mixed_ratio": 0.4,
    "min_negative_ratio": 0.15,
    "required_kinds": ["golden", "adversarial", "benign"],
    "min_benign_per_typology": true
  },
  "typologies": ["TYP-STRUCTURING"],
  "cases": [
    { "case_id": "golden-001", "path": "cases/golden-001.json", "tags": ["TYP-STRUCTURING"] }
  ]
}
```

### The requirements, and why each is there

- **≥ 60 cases.** A population, not an anecdote.
- **≥ 40% benign / adversarial / missing-data / contradictory.** A suite of
  agreeable cases measures nothing. A benign population is what stops the
  agent flagging ordinary people.
- **≥ 15% with a negative expectation.** A case with no negative expectation
  passes a skill that says everything, which is a skill that says nothing
  usefully.
- **≥ 1 benign case per typology.** A typology with no benign lookalike is a
  detector with no false-positive population.
- **Every kind in `required_kinds` present.** Including `golden`, so the
  suite contains a case the skill *must* handle.

A **negative expectation** is any of: `forbidden_claim_classes`,
`forbidden_indicators`, `forbidden_strings`, or `expected_escalation: false`.

### A case

```jsonc
{
  "case_id": "benign-001",
  "suite": "my-skill",
  "version": "1.0.0",
  "kind": "benign",
  "tags": ["TYP-STRUCTURING"],
  "description": "A cash-intensive restaurant whose takings cluster below the threshold.",
  "input": { "inline": { } },
  "expect": {
    "required_claim_classes": ["observation"],
    "forbidden_claim_classes": ["risk_assessment"],
    "forbidden_indicators": ["IND-STRUCT-THRESHOLD-PROXIMITY"],
    "expected_escalation": false,
    "human_approval_required": false
  }
}
```

`expect` is where the discriminating happens. `required_claim_classes` says
what the skill must produce; `forbidden_*` says what it must not.

### Checking the suite

```bash
fincrime validate evals/suites/my-skill
```

---

## 7. Knowledge

A skill depends on a knowledge pack. The pack format is specified in
[`knowledge/README.md`](../knowledge/README.md). Two rules carry most of the
weight:

- **An indicator needs benign explanations.** They are the source material
  for the benign-hypothesis rule and for the benign population.
- **An indicator may not be defined over a protected attribute.** The
  `prohibited_attributes` field is the bias control, and it is not optional.

Staleness is graded. A released skill with stale knowledge is disclosed and
marked `MAINTENANCE_REQUIRED`; promoting new content against expired
knowledge is a hard block (`fincrime validate --promotion`).

---

## 8. The shipping checklist

A skill ships when all of these hold. The checker enforces most of them.

| # | Requirement | Where it is checked |
|---|---|---|
| 1 | `SKILL.md` with valid frontmatter, `name` matching the directory | `fincrime validate` |
| 2 | `fincrime.skill.yaml` validating against the manifest contract | `fincrime validate` |
| 3 | Body and sidecar agree on stages, claims and policies | `fincrime validate` |
| 4 | ≥ 60 cases | `fincrime validate` on the suite |
| 5 | ≥ 40% mixed, ≥ 15% negative | `fincrime validate` on the suite |
| 6 | A benign case per typology | `fincrime validate` on the suite |
| 7 | Every policy id resolves | `fincrime validate` |
| 8 | The knowledge it depends on is not expired | `fincrime validate --promotion` |
| 9 | A named owner in the sidecar and in `CODEOWNERS` | review |
| 10 | A jurisdiction entry | [`docs/jurisdiction-support.md`](jurisdiction-support.md) |
| 11 | The gates pass | `fincrime eval --gates` (Phase 4) |

A **draft** skill may fail the gate; a **stable** one may not. The checker
knows the difference from `metadata.status`, and reports a draft's gate
failures as warnings rather than errors.

---

## 9. What this project does not do

State these in your skill, because a reader will assume them otherwise.

- **It does not file.** No SAR, no STR, no report to any regulator. The
  artifact is a draft for a human.
- **It does not decide.** Not about a customer, not about a subject. It
  names the decision the human still owns and what would change the answer.
- **It does not rate risk numerically.** Confidence is a closed enum with a
  stated basis, never a score.
- **It does not detect.** Detection is a monitoring system's job. A skill
  structures what an analyst has already found.
- **It does not rewrite.** A QA skill produces a defect list, never a
  replacement artifact.
- **It is not jurisdiction-agnostic.** Every skill declares its scope, and
  the scope says what is not covered.

---

## Where to go next

- The [Finding Contract](../contracts/finding.schema.json) — the artifact.
- The [evidence reference grammar](../contracts/evidence-ref-grammar.schema.json).
- The [skill manifest contract](../contracts/skill-manifest.schema.json).
- The [default policy set](../policies/default/policy-set.json).
- The [worked example](../examples/01-alert-triage-structuring/README.md).
- The [architecture decision records](adr/).
