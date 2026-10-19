# ADR-0003: Deterministic vs. Probabilistic Boundary

- **Status:** Accepted
- **Date:** 2026-10-19
- **Deciders:** core maintainers
- **Supersedes:** none

## Context

The project must make a hard distinction between two kinds of work:

- **Interpretation and reasoning** — reading a case, forming hypotheses, judging
  whether a pattern is consistent with a typology, drafting a narrative, deciding
  what evidence to request next. This is where an LLM adds value and where it also
  fails.
- **Enforceable control** — is a threshold crossed? is a claim evidence-linked? is
  a decision attributable? is the deadline computed correctly? These must be
  *reproducible* and *identical across models and runs*.

The failure mode of ignoring this boundary is specific and observed: an LLM asked
"is this reportable?" answers confidently and inconsistently, and no one can show a
regulator why. The failure mode of the opposite error is over-constraining the
model into uselessness.

## Decision

**A single, explicit boundary rule governs the entire project:**

> **If the check needs a reading of the output → evaluation suite.
> If the check needs only a field → policy layer.
> If the check needs a value from outside the artifact → neither; it belongs in the
> evidence set.**

Concretely:

| Concern | Owner |
|---|---|
| Explaining what a structuring pattern looks like | LLM (skill) |
| Computing that a deposit was below the applicable reporting threshold | Policy layer (deterministic) |
| Judging whether the "why" of an activity is supported | LLM (reasoning) |
| Enforcing that the "why" carries an evidence reference | Policy layer (deterministic) |
| Computing the SAR filing deadline from the detection date | Policy layer (deterministic) |
| Enforcing that the deadline appears in the output | Policy layer (deterministic) |
| Deciding whether the narrative is clear and readable | LLM |
| Enforcing that the narrative contains no culpability phrases | Policy layer (deterministic) |
| Concluding the subject is laundering money | **Neither — forbidden** |

**Enforceable controls are never expressed only in prose.** A rule that a firm must
be able to defend to a regulator is expressed in the policy layer and evaluated by
code.

The policy layer uses a small, closed rule model (six kinds: `require`, `forbid`,
`threshold`, `count`, `consistency`, `composite`) with a **pure** reference
evaluator — no clock, no network, no filesystem, no randomness. OPA/Rego is
supported as an **export format** with a parity test, not as the runtime.

**LLM judges are used only for a small, clearly-labeled secondary rubric** (narrative
clarity, hypothesis quality, analyst usefulness) and **never gate a release**. The
gate weight is ≥ 80% deterministic.

## Consequences

**Positive**
- Safety-critical metrics are reproducible and auditable. A model-risk reviewer can
  re-run the suite and get the same numbers.
- A model change cannot silently change an enforceable control's verdict.
- The Rego export gives enterprises a path into an existing policy stack, with a
  parity test proving equivalence.

**Negative**
- Some checks that *feel* like they should be enforceable are not, because
  "structural" language is not fully captured by a closed rule model. This is a
  known gap; the mitigation is the LLM-judge layer, honestly labeled as
  non-authoritative.
- The rule model must grow for new needs, and each addition is a semantic change
  to an enforceable control.

**Neutral**
- A rule that cannot be evaluated by code is not a defect — it means the
  constraint belongs in the skill body and is measured by the eval suite. The
  boundary is a routing decision, not a quality judgement.

## Alternatives considered

| Alternative | Rejected because |
|---|---|
| A deterministic rules engine for everything (no LLM) | Cannot read a case or form a hypothesis. Deterministic *enforcement* of *probabilistic* output is the design, not deterministic everything. |
| All judgment left to the LLM | Non-reproducible, unauditable, and the specific failure we exist to prevent. |
| A workflow/DAG engine as the orchestration layer | An agent *is* the runtime. A deterministic engine is the right tool for enforceable rules, not for reasoning. |
| OPA/Rego as the canonical rule format | Strong, but a second language and a runtime in the trust boundary (ADR-0002). Retained as an export. |
| Python rules | Untyped, unvalidatable, un-diffable, and impossible to lint for coverage. |
| JSON Logic as the rule expression language | Attractive, but our operation set (thresholds, set membership, patterns, cross-field) is small enough that a constrained model is clearer and more auditable. Revisit if expressiveness becomes a real blocker. |
