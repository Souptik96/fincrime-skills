# FinCrime Skills

**Skills that make AI agents behave like financial-crime investigators — and a
test suite that proves they don't hallucinate.**

> **Status: Phase 3 (the first skills).** The contracts, the validator, the
> skill format, and the `fincrime` command are in place, and three skills now
> work end to end against dated knowledge: `alert-triage`, `case-summarize` and
> `evidence-request`. Each ships 60 evaluation cases and a golden artifact the
> QA gate is measured against. There is still no published conformance result:
> the harness that runs the suites is Phase 4.

---

## The problem

An agent given an AML alert produces fluent, well-organized prose that blends
what the evidence shows with what the model assumes:

> *"The customer deposited $9,400–$9,800 in cash at four branches over nine
> days, which is consistent with structuring to evade reporting requirements.
> The account should be escalated and a SAR filed."*

Nothing in the current pipeline can tell which sentences are evidence and which
are inference. The narrative is plausible. It may also be false. And a SAR
narrative reaches a regulator and law enforcement.

## What this project does

It replaces the narrative with a **contract**.

Every output is a structured **Evidence-Linked Finding (ELF)**: a set of typed
claims, each bound to a specific value in the supplied evidence.

| Claim class | Requires | Can assert criminality? |
|---|---|---|
| `fact` | ≥ 1 resolvable evidence reference | No |
| `observation` | ≥ 1 resolvable evidence reference | No |
| `indicator` | ≥ 1 evidence reference **and** a valid indicator id | No |
| `hypothesis` | a `falsifier` and an `epistemic_type` | No — phrased as a possibility |
| `risk_assessment` | ≥ 1 evidence reference, or `insufficient_information` | No |
| `recommendation` | ≥ 1 evidence reference | No |
| `decision` | `decided_by` naming a human or a policy | No |

A `fact` that cannot cite evidence **does not validate**. It is not a degraded
finding; it is structurally a non-finding. That turns "don't hallucinate" from a
prompt instruction into a checkable property.

**No keyword filter is the defense.** A model can evade a deny-list by writing
*"exhibited behavior suggestive of deliberate structuring."* So the real
constraint is structural: every hypothesis is typed, and an `adverse_reading`
**cannot stand alone** — the artifact must contain a `benign_reading` to compete
with it. The wording is irrelevant.

## What it is not

- **Not a detector.** Detection is upstream. We analyse what a monitoring system produced.
- **Not a copilot.** Prose is a rendering of the structured artifact, never the artifact.
- **Not a decision engine.** No skill freezes, closes, declines, de-risks, or files.
- **Not a risk score.** Risk is expressed as drivers and confidence, never as a number that looks authoritative and is not.
- **Not multi-jurisdiction.** v1 is US (FinCEN / BSA / OFAC) only. See `docs/jurisdiction-support.md`.

## Install

```bash
# the skills (works with Claude Code, Codex, Cursor, Copilot, Gemini CLI, and 30+ others)
npx skills add fincrime/fincrime-skills/skills/alert-triage

# the validator and contract library
pip install fincrime-core

# the command: scaffold, validate, export, check
pip install fincrime-cli
```

The core has **zero runtime dependencies** and **no network capability** — it
installs and runs in an air-gapped environment with no package-index access
([ADR-0002](docs/adr/0002-zero-dependency-core.md)). The CLI is stdlib-only
too, for the same reason.

## Use

```python
from fincrime_core import Validator

validator = Validator(evidence_set=evidence_set)
result = validator.validate(artifact)

for defect in result.errors:
    print(f"{defect.code}: {defect.message}")

print(result.evidence_attribution_accuracy)   # deterministic, not judged
print(result.unsupported_claim_rate)          # deterministic, not judged
```

## Authoring a skill

```bash
fincrime new skill my-skill --outdir skills   # writes a package that already validates
fincrime validate skills/my-skill              # checks it against the contract
fincrime policy check --set policies/default/policy-set.json --artifact artifact.json
```

The guide is [`docs/skill-authoring.md`](docs/skill-authoring.md). It is the
whole of what a contributor needs to read.

## Why this is different from a prompt pack

| | A prompt pack | This |
|---|---|---|
| Output | Prose | A machine-checkable contract |
| Evidence | Whatever the prose cites | Every claim bound to a resolvable reference |
| Quality claim | "This makes your agent better" | Published metrics against a **no-skill baseline** |
| Verification | Reading | `fincrime validate` |
| Regulatory content | Prose, silently stale | Dated, cited, expiring, jurisdiction-scoped |
| Benchmarking | None | Deterministic scorers; LLM judges never gate |

## Repository layout

```text
contracts/     the canonical, versioned JSON Schemas (the product)
packages/      fincrime-core (contract, validator, policy, knowledge) + fincrime-cli
skills/        portable Agent Skills packages (v1: 6 skills, US only)
knowledge/     dated, cited, expiring knowledge packs
policies/      deterministic rules (data, not prose)
evals/         case suites, baselines, published conformance report
adapters/      optional: MCP, OpenAI Agents, LangGraph (none required)
docs/          the authoring guide, the jurisdiction statement, and the ADRs
```

## Architecture decisions

Eleven ADRs, each ≤ 2 pages, stating context / decision / consequences:

| ADR | Decision |
|---|---|
| [0001](docs/adr/0001-evidence-linked-finding.md) | The Evidence-Linked Finding as the core abstraction |
| [0002](docs/adr/0002-zero-dependency-core.md) | Zero-dependency core engine invariant |
| [0003](docs/adr/0003-deterministic-boundary.md) | Deterministic vs. probabilistic boundary |
| [0004](docs/adr/0004-evidence-ref-grammar.md) | RFC 6901 evidence-reference grammar |
| [0005](docs/adr/0005-native-eval-harness.md) | Native evaluation harness (no external framework) |
| [0006](docs/adr/0006-graded-knowledge-expiry.md) | Graded knowledge-expiry enforcement |
| [0007](docs/adr/0007-no-skill-baseline.md) | No-skill baseline as the unit of skill value |
| [0008](docs/adr/0008-v1-scope.md) | v1 scope: six skills, one jurisdiction, Part V only |
| [0009](docs/adr/0009-tool-generated-safety-notices.md) | Tool-generated safety notices (non-strippable) |
| [0010](docs/adr/0010-skill-format-and-cli-boundary.md) | The skill format and the engine/tooling boundary |
| [0011](docs/adr/0011-request-dossier-and-manifest-catalogue-binding.md) | The request dossier and the manifest catalogue binding |

## Development

```bash
make dev      # venv + editable install of the core and the CLI
make test     # unit, contract, golden, adversarial, PII
make test-cli # the CLI suite
make lint     # import lint (zero-dep invariant)
make validate # contract validation
make validate-skills  # every skill package in skills/
make ci       # everything CI runs
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). A skill ships when it has a contract, a
case suite with a benign population, a deterministic gate it passes, and a named
owner who can maintain its knowledge. Not when it is written.

## Security

See [SECURITY.md](SECURITY.md). **No customer data is ever collected, stored, or
requested by this project.** All datasets are synthetic and generated from a
seed.

## Licence

Code and contracts: **Apache-2.0**. Knowledge packs and documentation:
**CC-BY-4.0**. See [NOTICE](NOTICE) for third-party attributions.
