# ADR-0007: No-Skill Baseline as the Unit of Skill Value

- **Status:** Accepted
- **Date:** 2026-10-19
- **Deciders:** core maintainers
- **Supersedes:** none

## Context

A skill that improves nothing is indistinguishable from a skill that improves
everything, if the score is reported in isolation. A model at 85% on triage
without any skill and 86% with the skill means the skill is worth +1%, not 86%.

This is not hypothetical. arXiv 2606.17819 found that access to a skill
*significantly* changes model behavior — and, by the same token, that the skill's
value is only interpretable as a **marginal contribution over a no-skill
baseline**. A project that publishes absolute scores in a regulated domain is
publishing a number that does not mean what readers will take it to mean.

The risk this creates is not only interpretive. It is that the *project* starts
optimizing the absolute number, which is the same failure as benchmark gaming.

## Decision

**Every published score is a delta against a no-skill baseline**, computed with the
same model, the same harness, the same cases, and the same seeds, with the skill
removed and the output schema withheld from the prompt.

- The baseline prompt is **fixed, versioned, and committed** so the comparison is
  auditable.
- Each configuration runs **3 times** (seeds where supported). The report publishes
  the mean and the standard error.
- The **noise band is 2 × SE**. A delta inside the band is reported as
  **"no measurable effect on this metric"** — the code must be capable of printing
  that, and it must be printed rather than suppressed.
- **Negative deltas are published.**
- A skill that does not beat its baseline on `evidence_attribution_accuracy` and
  `benign_false_positive_rate` **is not shipped**. If a skill only improves prose
  without improving evidence discipline, that is reported plainly and the skill's
  scope is narrowed.

## Consequences

**Positive**
- The headline claim becomes defensible: "this skill changes behavior by X" rather
  than "our score is Y".
- The comparison is the honest unit and it is reproducible.
- Publishing negative results is a credibility asset in a domain where vendor
  claims are unverified, and it makes benchmark gaming structurally unattractive —
  you cannot show a gain you did not have.
- The baseline doubles as a free measurement of the *problem*: the no-skill
  hallucination rate of frontier models on realistic AML alerts is itself the
  project's most shareable artifact.

**Negative**
- 2× the compute per report. Mitigated by the replay provider and by running
  baselines on a schedule rather than every PR.
- Deltas are noisier than absolute scores and are harder to present. This is
  correct, not a defect.
- A skill that genuinely helps but where the effect is small will look weak. That
  is the correct reading, and it should narrow the skill's claimed scope.

**Neutral**
- The baseline is a first-class artifact in `evals/baselines/`, committed, so a
  score is a diff rather than a claim.

## Alternatives considered

| Alternative | Rejected because |
|---|---|
| Absolute scores only | Uninterpretable without a baseline; the reader cannot tell what the skill contributed. |
| LLM-judged "with vs without" narrative | Non-reproducible, and it would put the safety-adjacent comparison behind a judge. |
| Baselines as a separate published paper | Disconnects the baseline from the report; the comparison must be visible wherever the score is. |
| One run per configuration | A single run cannot distinguish a real delta from sampling noise. |
| Run baselines on every PR | Doubles CI cost for a measurement that changes slowly. Baselines are scheduled; deltas still gate every PR. |
