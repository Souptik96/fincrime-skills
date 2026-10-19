# Roadmap

The roadmap is a sequence of **provable** steps, not a feature list. Each phase
has an exit criterion, and a phase does not begin until the previous phase's
criterion is met.

## Phase 0 — Architecture ✅

**Objective:** freeze the architecture so no later phase re-litigates it.

- [x] Nine ADRs
- [x] The Finding Contract `fincrime/finding/1.0.0`
- [x] The RFC 6901 evidence-reference grammar
- [x] `fincrime-core`: validator, resolver, lints, policy evaluator, knowledge engine
- [x] CI baseline: import lint, socket-blocked suite, schema parity, Python matrix
- [x] The `investigation-qa` reference skill and a worked example

**Exit criteria:** ✅ contracts validate; a worked example validates; `make ci`
is green on a clean clone; the validator rejects the five seeded defects and
produces zero false positives on the conformant baseline; the resolver is total
and byte-stable.

## Phase 1 — Core skill specification

**Objective:** a working, versioned skill format that one person can author,
validate, and test without reading the whole architecture.

- [ ] `fincrime new skill` scaffolding
- [ ] The remaining contract schemas (case mix enforcement, policy export)
- [ ] The knowledge pack format and the expiry bot
- [ ] The policy rule set: `policies/default/`
- [ ] `docs/skill-authoring.md`

**Exit criterion:** a contributor who has read only the authoring guide can
author, validate, and test a new skill.

## Phase 2 — Knowledge layer

**Objective:** the first dated pack, with the expiry machinery *working* — the
expiry machinery, not the content, is the hard part.

- [ ] `knowledge/packs/core-2026-10` — ~25 indicators, ~8 typologies, ~20 US
      regulatory records, ~30 request-catalogue entries
- [ ] The nightly expiry bot, issuing one labelled issue per stale dependency
      with the refresh diff attached
- [ ] The pack promotion gate

**Exit criterion:** an expired record blocks its pack's promotion **and** fails
the citing skill's CI gate in promotion context, while a released skill is
warned rather than blocked.

## Phase 3 — First skills

**Objective:** three skills that work end to end.

- [ ] `alert-triage`
- [ ] `case-summarize`
- [ ] `evidence-request`
- [ ] ≥ 40 cases each, with the required mix

**Exit criterion:** each validates, each has a case suite, and the
`investigation-qa` skill finds the seeded defects in the others' outputs and no
false defects in their good outputs.

## Phase 4 — Evaluation framework

**Objective:** the actual moat.

- [ ] The native harness: case loader, provider adapters, deterministic scorers,
      metric aggregation, gate evaluation, report rendering
- [ ] The **replay** provider, so the golden path runs offline with no API key
- [ ] The **no-skill baseline** runner and the delta table
- [ ] Multi-seed noise methodology (3 seeds, 2×SE band, "no measurable effect")
- [ ] The published conformance report

**Exit criterion:** a published report with real numbers, a reproducible replay
path, and a CI gate that actually blocks a regression.

## Phase 5 — Synthetic datasets

**Objective:** the generator and the committed fixtures, with the privacy
guarantee enforced.

- [ ] 12 typologies and **12 benign lookalikes** with a feature-overlap test
- [ ] The adversarial mutators, each verified to trigger its target defect
- [ ] The PII scanner, proven to catch seeded violations *and* accept the
      generator's reserved namespaces
- [ ] ≥ 360 cases across the six v1 skills

**Exit criterion:** the corpus regenerates byte-identically from a seed and
contains no real data.

## Phase 6 — Developer experience

**Objective:** the 60-second path, for users and contributors alike.

- [ ] `fincrime validate | eval | demo | new | explain | knowledge | policy`
- [ ] `make demo` in under 30 seconds with no key and no network
- [ ] The README, the examples, the quickstart
- [ ] A CI job that executes every command appearing in the docs

**Exit criterion:** a stranger can clone, run the demo, and understand the
project in 60 seconds.

## Phase 7 — Documentation and readiness

**Objective:** everything a reviewer, an adopter, or a supervisor needs.

- [ ] The claim-classes guide, written for a compliance reader
- [ ] The threat model
- [ ] The evaluation methodology, publishing the formulas, the noise
      methodology, the judge protocol, **and the negative results**
- [ ] `docs/regulatory-mapping.md`, with a `last_reviewed` date per row
- [ ] `docs/jurisdiction-support.md`, stating what is **not** supported

**Exit criterion:** the project can be reviewed, run, and evaluated without a
maintainer present.

## Phase 8 — Public launch

- [ ] Publish v1.0, the conformance report, and the dataset DOI
- [ ] The methodology post with the measured hallucination rate
- [ ] Ecosystem listings (`npx skills`, skills.sh, agentskills.in, awesome-lists)
- [ ] The first 3–5 "good first issue" tracks
- [ ] The weekly model-matrix run

## After v1.0

| Item | Note |
|---|---|
| `kyc-file-review` | Needs a synthetic KYC document corpus |
| `source-of-funds` | Judgment-heavy; needs its own evaluation design |
| `ubo-ownership-map`, `network-mule-analysis` | Need the graph contract and loader |
| `fraud-ato-review` | The fraud chain starts here |
| `adverse-media-screen` | Needs a licensed corpus and a retrieval layer |
| `policy-interpret` | Only after the knowledge layer has survived a real expiry cycle |
| The MCP server | An adapter, not a dependency |
| The OpenAI Agents and LangGraph adapters | Thin bindings |
| A second jurisdiction | One at a time, with its own corpus and legal review |
| The `fincrime/finding` spec proposal to a neutral foundation | After v1.0 proves the contract |

## Considered and rejected

Recorded so that a future maintainer does not relitigate them. The full
rationale is in `docs/adr/` and the project blueprint.

Detection engines, transaction-monitoring rule DSLs, numeric customer risk
scoring, case-management UI, live watchlist integrations, real customer data, a
hosted service, a general-purpose agent-evaluation framework, multi-jurisdiction
breadth at launch, and any autonomous decision or filing capability.
