# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- The **Finding Contract** `fincrime/finding/1.0.0`: a JSON Schema 2020-12
  definition of the Evidence-Linked Finding, with seven closed claim classes
  and conditional requirements encoded as `if`/`then` so that a stock JSON Schema
  validator enforces the same rules the project does.
  ([ADR-0001](docs/adr/0001-evidence-linked-finding.md))
- The **RFC 6901 evidence-reference grammar**, `contracts/evidence-ref-grammar.schema.json`,
  with a normative ABNF, the escaping rules, and the empty-pointer semantics.
  ([ADR-0004](docs/adr/0004-evidence-ref-grammar.md))
- `fincrime-core`: a **dependency-free** validator with a total, deterministic
  evidence resolver; a claim linter implementing R-1 through R-9; a pure
  deterministic policy evaluator; and a dated, cited, jurisdiction-scoped
  knowledge engine. ([ADR-0002](docs/adr/0002-zero-dependency-core.md),
  [ADR-0003](docs/adr/0003-deterministic-boundary.md))
- A **structural** defense against unsupported intent assertions: every
  hypothesis carries a closed-enum `epistemic_type`, and an `adverse_reading`
  cannot validate without a `benign_reading` competitor. The lexical
  culpability lint is retained as a secondary detector at `warn` severity.
- **Graded knowledge-expiry enforcement**: hard block when promoting new or
  modified content, warning plus `MAINTENANCE_REQUIRED` on an unchanged
  released artifact, and deprecation after 180 days. Runtime artifact behaviour
  is unchanged. ([ADR-0006](docs/adr/0006-graded-knowledge-expiry.md))
- Nine architecture decision records under `docs/adr/`.
- The `investigation-qa` reference skill, in Agent Skills format, with the
  `fincrime.skill.yaml` sidecar contract.
- A worked example (`examples/01-alert-triage-structuring`) that demonstrates
  the no-skill baseline against the skilled output, bound to the test suite so
  it cannot silently drift.
- CI: an AST import linter enforcing the zero-dependency invariant, a
  socket-blocked test run, a schema-parity cross-check against the reference
  JSON Schema implementation, a four-version Python matrix, and CodeQL.

### Not yet present

No skills have shipped and no evaluation suites exist yet. Those are Phase 3
and Phase 4 respectively. Nothing in this repository currently produces a
scored, published conformance result.

[Unreleased]: https://github.com/fincrime/fincrime-skills/compare/main...HEAD
