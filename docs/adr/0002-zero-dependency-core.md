# ADR-0002: Zero-Dependency Core Engine Invariant

- **Status:** Accepted
- **Date:** 2026-10-19
- **Deciders:** core maintainers
- **Supersedes:** none

## Context

`fincrime-core` is the trust boundary of this project. It runs inside bank
environments, frequently air-gapped, under vendor-risk and model-risk review, and
it processes artifacts that may contain sensitive financial data.

Two properties matter more here than in an ordinary OSS library:

1. **It must be auditable.** A compliance engineer must be able to read the whole
   validator. "Read the transitive dependency tree" is not an answer a bank will
   accept for a component that decides whether an allegation is evidence-linked.
2. **It must not be able to exfiltrate.** A validator with network capability is
   a validator with a data-exfiltration surface, regardless of intent.

A dependency is also a maintenance liability: an upstream deprecation, a
supply-chain compromise, or an API break in a transitive dependency can break the
exact artifact a bank archived for audit.

The review proposed Pydantic v2 for the data models. Pydantic is a non-stdlib
runtime dependency and would violate both properties.

## Decision

**`fincrime-core` has ZERO required runtime dependencies.** Standard library only.

- Data models: stdlib `dataclasses` plus a hand-rolled validator.
- JSON Schema validation: a small, self-contained JSON Schema 2020-12 subset
  validator covering exactly the keywords the contracts use.
- Pydantic models are available as an **optional extra** (`fincrime-core[pydantic]`),
  generated from the same JSON Schemas so the two cannot drift.
- `fincrime-evals` may depend on `pytest` (a dev/test dependency) but its runtime
  scoring path uses only the standard library.

Enforced by CI:
- `scripts/check_imports.py` — AST scan of `packages/fincrime-core` for any
  non-stdlib import. **Blocking.**
- `scripts/check_no_network.py` — the golden suite runs with sockets disabled.
  **Blocking.**
- `pip install packages/fincrime-core` in a clean venv must report zero `Requires`.

## Consequences

**Positive**
- `pip install fincrime-core` works in an air-gapped VPC with no index access.
- The security review story is strong and simple: *the validator has no network
  capability at all*, therefore it cannot exfiltrate. This is checkable, not a
  promise.
- The validator is small enough to read end to end.
- No upstream supply-chain event can reach the trust boundary.

**Negative**
- We write and maintain a JSON Schema subset validator (~300 lines) and a
  hand-rolled model layer. That is real work we would otherwise inherit.
- The subset validator covers only the keywords our contracts use. If a future
  contract needs `$dynamicRef` or tuple validation, the subset must grow — a
  conscious, reviewable change.
- Consumers who want rich typed validation must install the optional extra.

**Neutral**
- The JSON Schemas themselves remain **standards-compliant** and can be enforced
  by any third-party validator. Our subset validator is an implementation of the
  standard for our keyword set, not a private dialect.

## Alternatives considered

| Alternative | Rejected because |
|---|---|
| Pydantic v2 in core | Non-stdlib dependency in the trust boundary; conflicts with the zero-dep invariant this ADR establishes. Available as an optional extra instead. |
| `jsonschema` library in core | Same objection, smaller. |
| OPA/Rego for policy evaluation in core | Requires a Go/Wasm runtime. Rego remains a supported **export format** with a parity test, evaluated by the native reference evaluator. |
| Composing `microsoft/waza` for eval mechanics | See ADR-0005. |
| jsonschema in `fincrime-evals` only | Acceptable (test-time dependency), but the *runtime* validator still needs a subset implementation for the library to be usable standalone. |
