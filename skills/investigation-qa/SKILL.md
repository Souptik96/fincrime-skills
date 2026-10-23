---
name: investigation-qa
description: >-
  Review a financial-crime investigation artifact and return a structured defect
  list. Use when an analyst, a reviewer, or a second agent needs to check
  whether a draft triage report, case summary, sanctions assessment, or SAR
  narrative is evidence-linked, epistemically separated, and free of unsupported
  conclusions. Produces a QA result with per-defect remediation, never a
  rewritten artifact and never a disposition.
license: Apache-2.0
metadata:
  fincrime_version: "1.0.0"
  contract_version: "fincrime/finding/1.0.0"
  knowledge_pack: "core-2026-10"
  category: "fincrime"
  jurisdiction: "US"
  compliance: "BSA/AML"
  risk_tier: "low"
  domain: "investigation"
  related_skills: "alert-triage,case-summarize,sar-narrative-draft,evidence-request"
---

# Investigation QA

> ⚠️ This skill **reviews** an artifact. It never rewrites it, never decides, and
> never files. It produces a defect list that a human or the artifact's author
> acts on. Jurisdiction scope: **United States**. See `references/jurisdiction-us.md`.

## When to use

- Before an artifact is filed, stored in a case system, or passed to a downstream
  process.
- As a second pair of eyes that is not the original author.
- As a self-check before handoff, to catch defects while they are still cheap to fix.
- When adopting someone else's agent output and needing to know how much of it is
  actually supported.

## When NOT to use

- To produce an investigation in the first place. Use `alert-triage`,
  `case-summarize`, or `sar-narrative-draft`.
- As a decision about a customer or a subject. This skill has no standing to
  make one and does not try.
- On a narrative that has not been produced as a structured artifact. The
  review is structural; free prose has no claims to attribute.

## Required inputs

| Input | Description |
|---|---|
| `artifact` | The finding document under review, conforming to `fincrime/finding/1.0.0`. |
| `evidence_set` | The closed world the artifact was produced against. Without it, evidence attribution cannot be checked at all. |

## Optional inputs

| Input | Description |
|---|---|
| `knowledge_index` | The knowledge pack the artifact declared, used to check that cited indicators and records exist and are not expired. |
| `policy_rules` | The firm's deterministic rules, used to check enforceable controls. |
| `expected` | Case expectations, when the artifact is being scored rather than reviewed. |

## Preconditions

| ID | Check | On failure | Message |
|---|---|---|---|
| PC-1 | The artifact is a well-formed finding document | `stop` | The artifact cannot be reviewed because it is not structured. Report the schema violations. |
| PC-2 | An evidence set is supplied | `stop` | Evidence attribution cannot be checked without the evidence set. |
| PC-3 | The declared knowledge pack is resolvable | `annotate` | Indicator and record existence cannot be verified; disclose it. |

## Procedure

Follow the stage pattern S0–S7. Each stage states what it produces and what it
requires.

### S0 — Frame

Establish what is under review: the artifact type, the skill and version that
produced it, the subject scope, the jurisdiction, and the evidence set. Produce
`frame`.

*Requires:* nothing. *Guard:* none.

### S1 — Ground

Enumerate the artifact's claims by class, and the evidence references each
carries. Produce `evidence_inventory` and `gaps`.

*Requires:* the parsed artifact. *Guard:* `POL-EVIDENCE-INVENTORY-FIRST`.

### S2 — Extract

For every claim of class `fact`, `observation`, or `indicator`, determine
whether its evidence references resolve against the supplied evidence set, and
whether the resolved value supports the claim. Produce `observation` findings
about the artifact's own structure.

*Requires:* `evidence_inventory`. *Guard:* `POL-INDICATOR-REQUIRES-INDICATOR-ID`.

### S3 — Hypothesize

Determine whether the artifact's hypothesis set is complete: is there a benign
reading to compete with any adverse reading? Are the hypotheses falsifiable?
Produce `hypothesis` findings.

*Requires:* the claim set. *Guard:* `POL-BENIGN-HYPOTHESIS-REQUIRED`.

### S4 — Contrast

Determine whether the artifact surfaces the contradictions present in the
evidence, and whether its own claims conflict with each other or with the
evidence. Produce `contradiction` findings.

*Requires:* the claim set. *Guard:* none.

### S5 — Assess

Determine whether the stated confidence is supported by the evidence, and
whether the artifact's confidence claims are consistent with its own recorded
gaps. Produce `risk_assessment` findings.

*Requires:* the gap list. *Guard:* `POL-ASSESSMENT-NEEDS-INDICATOR`.

### S6 — Recommend

For each defect, produce a specific remediation: what to change, in which
claim, and what evidence would resolve it. Produce `recommendation` findings.

*Requires:* the defect list. *Guard:* `POL-RECOMMENDATION-NEEDS-BASIS`.

### S7 — Escalate

Name the decision the reviewer still owns, and the severity of the defect set
as a whole. A defect of severity `error` means the artifact is not
presentable. Produce `escalation`.

*Requires:* the defect list. *Guard:* none.

## Output

A `qa_result` artifact conforming to `fincrime/finding/1.0.0`:

- `artifact.artifact_type` = `qa_result`
- `claims` — one `observation` claim per defect, each citing the offending
  claim id and, where applicable, the evidence reference that fails
- `human_decision_required` — always at least one: whether to accept the
  artifact for filing, storage, or onward use
- `provenance` — the reviewer's identity, the artifact hash, and the evidence
  set hash

**The QA result is not a rewrite.** The skill must not produce a corrected
artifact; it produces a defect list. The author decides what to do with it.

## Escalation

Report a defect of severity `error` and refuse to sign off when:

- any `fact`, `observation`, or `indicator` claim carries an evidence reference
  that does not resolve, or no reference at all;
- an `adverse_reading` hypothesis stands without a `benign_reading` competitor;
- a `decision` claim is not attributable to a human or a policy;
- a claim asserts criminality of the subject;
- the artifact's jurisdiction scope is absent or the claims exceed it;
- a cited knowledge record has expired (a `warn` on an unchanged released
  artifact, an `error` when new work depends on it);
- a `sar_narrative` artifact lacks the tool-generated draft notice.

## Guardrails

- **Never** state that the subject is suspicious, that activity is laundering, or
  that a report is required. Report what the artifact does and does not support.
- **Never** rewrite the artifact. Report the defect and the remediation.
- **Never** infer a missing artifact. Absence is a gap, not a negative finding.
- **Never** treat a heuristic lint finding as proof. A culpability-lint hit is
  a prompt for a human to look, not a verdict.
- **Never** mark an artifact acceptable because it is well-formatted. Formatting
  is a floor, not a standard.

## Provenance

Every QA result records the reviewer's model and version, the hash of the
artifact under review, the hash of the evidence set, the knowledge pack version
and its `as_of`, and the run identifier.
