# ADR-0001: The Evidence-Linked Finding (ELF) as the Core Abstraction

- **Status:** Accepted
- **Date:** 2026-10-19
- **Deciders:** core maintainers
- **Supersedes:** none

## Context

An agent investigating a financial-crime alert produces fluent, well-organized prose
that blends what the evidence shows with what the model assumes. A reviewer cannot
tell which sentences are evidence and which are inference. The failure is not
"the model is wrong" — it is that the artifact is *untyped*, so wrongness and
correctness are indistinguishable to any downstream consumer, human or machine.

We need a core abstraction that is simultaneously:
1. the thing the agent produces,
2. the thing a validator checks,
3. the thing an evaluation metric is computed over, and
4. the thing an auditor reads.

A workflow is only (1). A prompt is only (1) and (4)-ish. A schema is only (2) and
(3). Only a **structured record with a typed claim and a required evidence
reference** serves all four.

## Decision

The core abstraction is the **Evidence-Linked Finding (ELF)**: a structured record
containing a typed claim, a required evidence reference, a structured confidence
object, a jurisdiction scope, and a provenance chain.

Claim classes are a **closed enum of seven**:
`fact | observation | indicator | hypothesis | risk_assessment | recommendation | decision`.

Type rules are encoded in JSON Schema (`if`/`then` conditionals), not in prose, so
that a third party using only a stock JSON Schema validator enforces the same
rules we do.

A claim of class `fact`, `observation`, or `indicator` **cannot validate** without
at least one resolvable evidence reference. A `decision` cannot validate without
`decided_by` naming a human or a deterministic `policy_id`.

**An ELF that fails validation is structurally a non-finding.** It is not a
degraded finding; it is not a finding.

## Consequences

**Positive**
- Hallucination becomes a *checkable property* rather than a stated intention: a
  `fact` with an unresolvable ref cannot validate.
- The same schema serves generation, validation, evaluation, and audit. There is
  one artifact, not four representations of it.
- Cross-model and cross-host comparison becomes meaningful, because two artifacts
  can be compared structurally.
- A regulator-facing reviewer can follow one claim to one source record.

**Negative**
- The schema must be expressive enough for real investigative output without
  becoming a straitjacket. This is the primary risk of this decision and it is
  why Phase 0 includes a schema-usability spike against realistic cases (assumption
  A1 in the blueprint).
- Every skill author must think in claim classes. This is a real authoring cost and
  is why `fincrime new skill` scaffolds the structure.
- Model output must be structured, which some hosts do poorly. The replay
  provider and the schema-validity metric exist to measure this honestly.

**Neutral**
- Prose narrative is still permitted — as a `sar_narrative` artifact whose body
  is assembled *from* structured claims, each retaining its evidence refs. The
  narrative is a rendering of the ELF, never a replacement for it.

## Alternatives considered

| Alternative | Rejected because |
|---|---|
| Free-form narrative as the output | Untyped. Cannot be validated, scored, or compared. The core failure mode. |
| A workflow DAG as the core abstraction | Sequences steps; says nothing about the shape of the output, so it cannot be scored. |
| A prompt template as the core abstraction | Not an artifact. Not auditable. Trivially copyable. |
| A risk score as the core abstraction | False precision; requires a calibration regime we cannot ship or validate. Produces a number that looks authoritative and is not. |
| Per-claim-type flat lists (facts[], indicators[]…) | Loses the relationships between a hypothesis and the observations it explains, and between a claim and its competing hypothesis. The `competing_with` link is load-bearing. |
