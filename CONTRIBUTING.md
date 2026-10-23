# Contributing

Thank you for considering a contribution. This project is small and strict on
purpose, so please read this before opening a pull request.

## The rule that governs everything

> **A capability ships when it has (a) a contract, (b) a case suite with a
> benign population, (c) a deterministic gate it passes, and (d) a named owner
> who can maintain its knowledge.**

Not when it is written. Not when it is interesting. Not when it fills a
category in a taxonomy. This rule is what keeps six skills excellent instead of
thirty mediocre ones.

## What we are looking for, in priority order

For new contributors looking for guided entry points, please explore our **[5 Good First Issue Tracks](docs/good-first-issues.md)** covering typologies, knowledge records, adversarial mutation, adapters, and UK/EU scaffolding.

| # | Contribution | Why it is valuable |
|---|---|---|
| 1 | **Cases** for an existing skill | The corpus is the binding constraint on the whole project. A case with a benign twin and a documented expected outcome is worth more than a new skill. |
| 2 | **Knowledge records** — indicators, benign explanations, typologies | The benign twin is the most underrated artifact in FinCrime AI: it is what stops the agent from flagging ordinary people. |
| 3 | **A new skill** | Welcome, but it comes with ≥ 60 cases and a benign population. |
| 4 | **Adapters** | Thin bindings for hosts that need tools rather than instructions. |
| 5 | **Documentation and examples** | Valuable, especially for people outside the developer audience. |

**We are not looking for** more prose about AML. Typology content is public and
already implemented in a dozen repositories; it is not where the value is.

## Requirements for a new skill

Your PR will not merge without all of these. The full guide is
[`docs/skill-authoring.md`](docs/skill-authoring.md); the command that checks
most of them is `fincrime validate skills/<name>`.

| # | Requirement | Threshold |
|---|---|---|
| 1 | `SKILL.md` with valid Agent Skills frontmatter | `name` matches the directory; description states what / when / what it produces |
| 2 | `fincrime.skill.yaml` sidecar | Validates against `contracts/skill-manifest.schema.json` |
| 3 | Consistency between body and sidecar | Stages, output classes, and policy ids must match |
| 4 | **Case suite** | **≥ 60 cases** |
| 5 | **Case mix** | **≥ 40%** benign / adversarial / missing-data / contradictory |
| 6 | **Negative expectations** | **≥ 15%** of cases assert something the skill must *not* say |
| 7 | **A benign population** | At least one benign lookalike per typology the skill can detect |
| 8 | **A worked example** | In `examples/`, including one benign case |
| 9 | **Gates pass** | `fincrime eval --gates` |
| 10 | **A named owner** | In the sidecar `owners` field, and in `CODEOWNERS` |
| 11 | A jurisdiction entry | In `docs/jurisdiction-support.md` |
| 12 | Knowledge it depends on is not expired | No expired records in the current pack |

Start from `fincrime new skill <name> --outdir skills`. It writes a package
that already satisfies requirements 1–3, so you are editing a valid package
rather than assembling one.

## Requirements for a knowledge record

A record is **not** accepted without:

- `sources[]` — at least one citation, with a URL where one exists
- `jurisdictions[]` — never empty, never "global"
- `as_of`, `review_by`, `expires_at` — all present
- `benign_explanations[]` — at least one, for indicators
- `prohibited_attributes[]` — the bias control; an indicator may not be defined
  over a protected or proxy-protected attribute
- `maintainer` — a person, not a team
- **Derived and paraphrased content only.** Verbatim regulatory text is not
  permitted: it is a copyright problem and a staleness trap.

## Local development

```bash
make dev      # venv + editable install of the core and the CLI
make test     # the core test suite
make test-cli # the CLI test suite
make lint     # the zero-dependency invariant
make validate # contract validation
make validate-skills  # every skill package in skills/
make ci       # everything CI runs
```

Every PR must keep `make ci` green. The CI job posts a comment on your PR with
the per-skill metric delta — that comment is the feedback loop, and it is
usually the fastest way to see what your change actually did.

## Architectural Invariants

Every contribution must preserve the four core invariants that define this repository:

1. **Zero-Dependency Runtime (ADR-0002):** The core and CLI have zero required third-party dependencies (`dependencies = []`). The trust boundary of a bank deployment must not depend on external supply chains or network access. Enforced by `scripts/check_imports.py` in CI.
2. **Air-Gap Safety (ADR-0003):** All evaluation suites, commands, and unit tests run with network sockets blocked. No network calls are permitted during execution. Enforced by `scripts/check_no_network.py` in CI.
3. **Zero-PII Guarantee (ADR-0007):** All evaluation datasets, replays, and documentation examples use synthetic, reserved namespaces (RFC 2606 domains, `000-xx-xxxx` SSNs, `555-01xx` numbers, `00-xxxxxxx` EINs, synthetic card numbers). No real customer data may ever be committed. Enforced by `scripts/check_pii.py` in CI.
4. **Zero Documentation Drift Guarantee:** Every Python and shell code snippet in markdown documentation is continuously executed and validated against live code in an air-gapped sandbox. Enforced by `scripts/check_docs.py` in CI.

## Style

- **Python:** standard library only in `fincrime-core` **and** in
  `fincrime-cli`. No exceptions. See
  [ADR-0002](docs/adr/0002-zero-dependency-core.md). The import linter is
  blocking, and it covers both packages.
- **Contracts:** JSON Schema 2020-12, `additionalProperties: false` on closed
  objects, `if`/`then` for conditional requirements.
- **Comments and docstrings:** explain *why*, not *what*. A comment that
  restates the code is noise; a comment that records a decision, a constraint,
  or a rejected alternative is the most valuable thing in the repository.
- **Prose:** spell out the reasoning. This project's users are risk professionals
  making decisions with consequences; hedging and jargon cost them.

## Behavioural requirements for a PR

- Every behavioural claim in a PR description must be backed by a **metric
  delta** in the CI comment. "This makes the agent better" is not an
  acceptable rationale.
- A PR that adds prose without adding cases is incomplete. We will ask you to
  close the loop.
- Generated artifacts are committed; generators are committed; the seed is
  recorded.
- **No real data. Ever.** The PII scanner is a merge gate.

## Reporting a false positive

If the validator or a lint fires on a legitimate artifact, that is a bug and we
want it. Open an issue with the artifact and the defect code. False positives
in the heuristic lints are especially welcome — a lint that cries wolf is worse
than no lint, and we hold the heuristic layer to a zero-false-positive standard
on the golden corpus.

## Code of conduct

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).
