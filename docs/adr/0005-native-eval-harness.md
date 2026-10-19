# ADR-0005: Native Evaluation Harness (No External Framework Dependency)

- **Status:** Accepted
- **Date:** 2026-10-19
- **Deciders:** core maintainers
- **Supersedes:** none

## Context

`microsoft/waza` (1.4k★, MIT) is a mature, well-regarded tool for evaluating
agent skills, and the blueprint originally proposed composing it for the
*generic* skill-eval mechanics while owning the FinCrime-specific scorers.

The review pushed back on that, citing rapid API churn, bloated dependency trees,
and unstable test runners in general agent-eval frameworks. That concern is
correct, and it is amplified by a project-specific factor the review surfaced:

**The harness sits on the same trust boundary as the core.** A bank that will not
pull a Go binary and an external toolchain into a financial-crime validation
pipeline will not accept a Python harness that shells out to one. The enterprise
selling point — *the entire toolchain runs offline, in your VPC, with no
dependencies* — is undermined by a single external harness.

Concrete cost analysis: the domain scorers (RFC 6901 resolution, claim lints,
policy evaluation, confusion matrices over golden cases) are required **regardless**
of harness choice. The generic machinery — provider adapters, seed management,
report rendering — is roughly 500 lines either way.

## Decision

**Build the evaluation harness natively** at `packages/fincrime-evals`.

- Runtime scoring path: **standard library only**.
- Test runner: `pytest` (a dev/test dependency, acceptable — it is not in the
  trust boundary at runtime).
- Provider adapters (`anthropic`, `openai`, `generic`, `replay`) are thin and
  owned by us.
- The `replay` provider makes the golden path run **offline with no API key and
  byte-reproducibly**, which is what allows the suite to run inside an air-gapped
  CI or an air-gapped bank environment.

`waza` is **not** a dependency and **not** planned. It may later become a
*consumer* of our `conformance.json` — a distribution channel, not a dependency.
If a future `waza` release provides a stable JSON import of our results, we will
add a thin exporter.

## Consequences

**Positive**
- The whole toolchain installs with no external harness and runs air-gapped.
- The enterprise review story stays clean: one dependency-free trust boundary.
- We own the report format, so the conformance report can be exactly the artifact
  we want, with negative results and metric formulas in the layout we need.
- No upstream release can break our CI.

**Negative**
- ~500 extra lines of generic machinery we would otherwise inherit.
- We forgo a community standard's feature momentum. If `waza` ships a capability
  we lack (e.g. a novel trigger-matching mode), we implement it ourselves.
- We take on the maintenance of provider-adapter API drift ourselves.

**Neutral**
- Our harness is domain-specific, so it will never be a general agent-eval
  framework. That is intentional and is why ADR-0002's zero-dependency rule does
  not create a conflict.

## Alternatives considered

| Alternative | Rejected because |
|---|---|
| Compose `microsoft/waza` | Adds an external artifact to the trust boundary we are selling; API churn risk; air-gapped CI depends on its release cadence. Reversed from the original blueprint (Part 18.5). |
| Compose `promptfoo` | Same objections; it is additionally aimed at prompt-level evaluation with a JS toolchain. |
| Build on `inspect_ai` (UK AISI) | Excellent framework, but a large dependency surface and a generic evaluation model. |
| Use a general eval framework and write a custom scorer plugin | The framework remains the dependency; only the scoring is ours. |
