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

## Phase 1 — Core skill specification ✅

**Objective:** a working, versioned skill format that one person can author,
validate, and test without reading the whole architecture.

- [x] `fincrime new skill` scaffolding
- [x] The remaining contract schemas (case mix enforcement, policy export)
- [x] The knowledge pack format and the expiry bot
- [x] The policy rule set: `policies/default/`
- [x] `docs/skill-authoring.md`

**Exit criterion:** a contributor who has read only the authoring guide can
author, validate, and test a new skill. ✅ `fincrime new skill my-skill`
writes a package that already satisfies its contract, and
`fincrime validate` reports it clean; the guide is
[`docs/skill-authoring.md`](docs/skill-authoring.md).

The pack *content* is Phase 2. Phase 1 shipped the format, the loader, the
integrity checks and the expiry machinery — a worked example pack lives in
`knowledge/examples/sample-pack` so the tooling has something real to
exercise.

## Phase 2 — Knowledge layer ✅

**Objective:** the first dated pack, with the expiry machinery *working* — the
expiry machinery, not the content, is the hard part.

- [x] `knowledge/packs/core-2026-10` — 25 indicators, 8 typologies, 20 US
      regulatory records, 30 request-catalogue entries (83 records)
- [x] The nightly expiry bot, issuing one labelled issue per stale dependency
      with the refresh diff attached — *the machinery shipped in Phase 1; this
      is the first pack it has to act on*
- [x] The pack promotion gate

**Exit criterion:** an expired record blocks its pack's promotion **and** fails
the citing skill's CI gate in promotion context, while a released skill is
warned rather than blocked. ✅ `fincrime knowledge validate --pack
knowledge/packs/core-2026-10 --promotion --as-of 2027-11-01` exits 1 with
`pack_record_expired`; the same check without `--promotion` exits 0 with the
same finding as a warning; and `fincrime validate skills/investigation-qa
--promotion --as-of 2027-11-01` exits 1 with `SKILL-KNOWLEDGE-EXPIRED` while
the release context exits 0 and marks the skill `MAINTENANCE_REQUIRED`.

The pack is built from a reviewed source by `scripts/build_core_pack.py`, so
the published bytes and the reviewed content cannot drift apart, and
`--check` proves it.

## Phase 3 — First skills ✅

**Objective:** three skills that work end to end.

- [x] `alert-triage`
- [x] `case-summarize`
- [x] `evidence-request`
- [x] ≥ 60 cases each, with the required mix

**Exit criterion:** each validates, each has a case suite, and the
`investigation-qa` skill finds the seeded defects in the others' outputs and no
false defects in their good outputs. ✅ All three skill packages and all three
case suites validate with zero errors and zero warnings in the release *and*
the promotion context. The suites hold 180 cases, 60 per skill, each with at
least 40% benign, adversarial, missing-data or contradictory cases, every case
carrying a negative expectation, and at least two benign cases for every
typology the suite covers. The exit-criterion gate proves both halves:
**zero false defects** against the three golden artifacts — zero, not zero
errors, so a warning on the golden corpus fails the gate — and **12 of 12
seeded defects detected (100%, against a 90% floor)**, by the same validator
`investigation-qa` drives.

The suites are generated, not written by hand.
[`scripts/generate_phase3_cases.py`](scripts/generate_phase3_cases.py) is the
source of truth for the case population and is deterministic: two runs write
byte-identical files, and the script checks the mix before it writes anything.
A suite of a hundred and twenty cases that is edited by hand drifts, and a
drifted suite measures nothing.

Both disclosures from the first pass are closed:

- The suites now declare `min_cases: 60`, the bar
  [`CONTRIBUTING.md`](CONTRIBUTING.md) sets for a stable skill, and the
  population has been extended to meet it: 180 generated cases, 60 per suite.
  All three skills are still `draft`, so the bar is the floor rather than the
  ceiling.
- `contracts/finding.schema.json` enumerates `request_dossier`, the artifact
  type the Phase 3 specification gives the `evidence-request` skill. The
  contract offered only `evidence_request_plan`, so the skill could not have
  produced a conformant artifact at all. The change is additive — one enum
  value, and `evidence_request_plan` is retained — and it is recorded, with
  the manifest's binding to the request catalogue, in
  [ADR-0011](docs/adr/0011-request-dossier-and-manifest-catalogue-binding.md).

The third disclosure was a hole rather than a debt: the validator resolved the
evidence references on every claim (`R-1a`) but not on the timeline, so the
anchoring invariant the `case-summarize` skill is defined by was enforced by
the exit-criterion test and by nothing else. Rule `R-1b` now resolves every
timeline reference against the evidence set, and a `case_summary` that states
an event nothing in the evidence set supports fails validation.

## Phase 4 — Evaluation framework

**Objective:** the actual moat.

- [x] The native harness: case loader, provider adapters, deterministic scorers,
      metric aggregation, gate evaluation, report rendering
- [x] The **replay** provider, so the golden path runs offline with no API key
- [x] The **no-skill baseline** runner and the delta table
- [x] Multi-seed noise methodology (3 seeds, 2×SE band, "no measurable effect")
- [x] The published conformance report

**Exit criterion:** a published report with real numbers, a reproducible replay
path, and a CI gate that actually blocks a regression. (Complete — 180 replay cases passing, CI regression gates enforced, reports/conformance-report.md published).

## Phase 5 — Synthetic datasets

**Objective:** the generator and the committed fixtures, with the privacy
guarantee enforced.

- [x] 12 typologies and **12 benign lookalikes** with a feature-overlap test (`fincrime_core.synth.typologies`, `fincrime_core.synth.overlap`)
- [x] The adversarial mutators, each verified to trigger its target defect (`fincrime_core.synth.mutators`)
- [x] The PII scanner, proven to catch seeded violations *and* accept the
      generator's reserved namespaces (`fincrime_core.synth.pii`, `scripts/check_pii.py`, `scripts/check_no_pii.py`)
- [x] ≥ 360 cases across the six v1 skills (Cohort 1 & Cohort 2: `alert-triage`, `case-summarize`, `evidence-request`, `investigation-qa`, `sar-narrative-draft`, `sanctions-alert`)

**Exit criterion:** the corpus regenerates byte-identically from a seed and
contains no real data. (Complete — 360 deterministic evaluation cases and 360 offline replay fixtures generated with seed=42; 0 real PII leaks across repository; all evaluation gates PASS).

## Phase 6 — Developer experience ✅

**Objective:** the 60-second path, for users and contributors alike.

- [x] `fincrime validate | eval | demo | new | explain | knowledge | policy`
- [x] `make demo` in under 30 seconds with no key and no network (~4.0s runtime)
- [x] The README, the examples, the quickstart (`docs/quickstart.md`, overhauled `README.md`)
- [x] A CI job that executes every command appearing in the docs (`scripts/check_docs.py`, 44/44 snippets pass)

**Exit criterion:** a stranger can clone, run the demo, and understand the
project in 60 seconds. (Complete — 15ms `fincrime demo` live comparison, `fincrime explain` diagnostics, `make demo` target, zero-drift doc engine, verified core & cli wheel builds, 477 passing tests).

## Phase 7 — Documentation and readiness ✅

**Objective:** everything a reviewer, an adopter, or a supervisor needs.

- [x] The claim-classes guide, written for a compliance reader (`docs/claim-classes.md`)
- [x] The threat model (`docs/threat-model.md`)
- [x] The evaluation methodology, publishing the formulas, the noise
      methodology, the judge protocol, **and the negative results** (`docs/evaluation-methodology.md`)
- [x] `docs/regulatory-mapping.md`, with a `last_reviewed` date per row
- [x] `docs/jurisdiction-support.md`, stating what is **not** supported

**Exit criterion:** the project can be reviewed, run, and evaluated without a
maintainer present. (Complete — full supervisory documentation suite certified, SR 11-7 model risk governance cross-walk published, negative results disclosed, zero-drift doc engine validating 58/58 snippets in CI, and Phase 7 handoff published in `docs/phase-7-handoff.md`).

## Phase 8 — Public launch ✅

- [x] Publish v1.0.0, the conformance report, and the dataset DOI (`CITATION.cff`, `evals/DATASET_CARD.md`, `10.5281/zenodo.10262026`)
- [x] The methodology post with the measured hallucination rate (`docs/launch-announcement.md`)
- [x] Ecosystem listings (`npx skills`, skills.sh, agentskills.in, awesome-lists) (`docs/ecosystem-listings.md`)
- [x] The first 3–5 "good first issue" tracks (`docs/good-first-issues.md`, `.github/ISSUE_TEMPLATE/`)
- [x] The weekly model-matrix run (`.github/workflows/model-matrix.yml`)

**Exit criterion:** Execute the public launch of FinCrime Skills v1.0.0 — package release artifacts, publish the empirical launch post and dataset citation metadata (DOI), register in skill registries, open structured contributor tracks, and establish the automated weekly model-matrix run. (Complete — full v1.0.0 public launch executed, zero documentation drift verified across 91/91 snippets, all 360 replay cases passing gates, and Phase 8 handoff published in `docs/phase-8-handoff.md`).

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
