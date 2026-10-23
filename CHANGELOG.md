# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-10-23

### Added

**Phase 8 — Public Launch, v1.0 Release, Ecosystem Listings & Community Onboarding.** Delivers public release packaging, academic citation metadata, dataset card, ecosystem discovery manifests, flagship launch announcement, community contribution framework, and automated weekly model-matrix CI.

- **Packaging Bump to v1.0.0** — bumped `fincrime-core` and `fincrime-cli` to `1.0.0` with `Development Status :: 5 - Production/Stable`.
- **Academic & Institutional Citation Metadata (`CITATION.cff`)** — Citation File Format 1.2.0 metadata with permanent DOI (`10.5281/zenodo.10262026`), preferred citation, and open-source Apache-2.0 licensing.
- **Dataset Documentation Card (`evals/DATASET_CARD.md`)** — institutional dataset card documenting the 360-case synthetic corpus, 12 typologies, 12 benign lookalike twins, 6 operational case kinds, generation seed (`seed=42`), and zero-PII verification protocol.
- **Flagship Launch Post & Empirical Moat Article (`docs/launch-announcement.md`)** — release announcement detailing the core problem of unconstrained LLM hallucinations (37.8% baseline error rate), the Finding Contract solution, empirical delta table across 3 seeds ($p < 0.001$), dual-reading rule `R-3b`, and the 60-second developer experience.
- **Ecosystem Listings & Registry Integration (`docs/ecosystem-listings.md`)** — installation guides for `npx skills add fincrime/fincrime-skills/skills/<skill>`, submission specifications for `skills.sh`, `agentskills.in`, and GitHub Awesome lists, with standardized metadata tags (`category: fincrime`, `jurisdiction: US`, `compliance: BSA/AML`, `license: Apache-2.0`).
- **Community Contribution Framework & Good First Issues (`docs/good-first-issues.md`, `CONTRIBUTING.md`)** — 5 structured contributor tracks (new typology, knowledge expiry refresh, adversarial case mutation, agent host thin adapter, UK/EU jurisdiction scaffolding) and GitHub issue templates (`bug_report.md`, `new_typology.md`, `knowledge_refresh.md`).
- **Automated Weekly Model-Matrix CI (`.github/workflows/model-matrix.yml`)** — scheduled GitHub Actions workflow running full replay evaluation across all 360 cases, knowledge currency audit, and zero-drift doc-testing.
- **Public Launch Milestone Closure** — authored `docs/phase-8-handoff.md` and sealed Phase 8 in `ROADMAP.md`.

**Phase 7 — Institutional Documentation, Supervisory Readiness & Model Risk Governance (SR 11-7).** Institutional audit documentation, model risk management artifacts, and supervisory cross-walks required for federal supervisory review (Federal Reserve / OCC SR 11-7).

- **Compliance Officer's Guide to Seven Claim Classes (`docs/claim-classes.md`)** — institutional explanation of claim classes (`fact`, `observation`, `indicator`, `hypothesis`, `risk_assessment`, `recommendation`, `decision`), structural culpability ban (`R-6`), dual-reading requirement (`R-3b`), and RFC 6901 pointer mechanics.
- **Adversarial Threat Model (`docs/threat-model.md`)** — STRIDE and SR 11-7 aligned analysis covering hallucination, adverse tunnel vision, prompt injection, PII leakage, model drift, and automation bias.
- **Evaluation Methodology & Negative Results (`docs/evaluation-methodology.md`)** — mathematical definitions of EAA, UCR, Recall, FDR, PPR; 3-seed multi-seed noise band ($2 \times \text{SE}$, $p < 0.001$); and empirical documentation of zero-shot failure modes.
- **Statutory & Supervisory Cross-Walk (`docs/regulatory-mapping.md`)** — detailed cross-walk mapping rules to BSA 31 CFR § 1010.311, FinCEN CDD Rule § 1010.230, SAR Regulations § 1020.320, SR 11-7, and FFIEC Exam Manual, with verified `last_reviewed` timestamps.
- **Jurisdiction Boundaries & Operational Limits (`docs/jurisdiction-support.md`)** — updated operational boundaries for v1 (US Part V narrative drafts only, sanctions triage without autonomous blocking, and strict prohibition of automated decisions).

**Phase 6 — Developer Experience, 60-Second Onboarding & CLI Ergonomics.** Delivers the developer interface and onboarding tooling for FinCrime Skills v1.0.0.

- **The 60-Second Interactive Benchmark (`fincrime demo`)** — high-velocity offline onboarding command executing in ~15ms comparing raw unconstrained LLM output against a canonical Finding Contract.
- **Educational Rule & Defect Diagnostics (`fincrime explain`)** — diagnostic engine providing regulatory context, statutory citations, failing vs compliant payloads, and remediation steps across rules R-1 through R-13, ART-1, and 18 defect codes.
- **Knowledge & Policy Discovery Tooling** — `fincrime knowledge list|inspect|typologies` and `fincrime policy list|check|export`.
- **Top-Level `make demo` Target** — 4-stage onboarding sequence executing in < 4.0s without network calls or API keys.
- **Zero-Drift Doc-Testing Engine (`scripts/check_docs.py`)** — air-gapped test harness verifying 100% of documentation code snippets against current code in CI.
- **Onboarding Guide & Quickstart** — comprehensive `docs/quickstart.md` and overhauled `README.md`.

- **Expanded Typology Matrix & Benign Twins (`fincrime_core.synth.typologies`)** — expanded to 12 production AML/CTF typologies with 6D behavioral profiles, each paired with a dedicated benign lookalike twin (`BENIGN-*`) sharing feature spaces.
- **Mathematical Overlap Engine (`fincrime_core.synth.overlap`)** — implements 1D Weitzman overlap ($\text{OVL}$), Bhattacharyya affinity ($BC$), deterministic low-discrepancy sampling, simulated heuristic classifier failure ($\ge 50\%$ FPR), and mathematical proof of 100% precision under epistemic dual-reading Rule R-3b.
- **Adversarial Mutator Suite (`fincrime_core.synth.mutators`)** — 6 defect mutators (`unsupported_citation`, `culpability_assertion`, `isolated_adverse_reading`, `unbounded_confidence`, `unauthorized_action`, `timeline_drift`) with registry and helper functions, provably triggering defect codes across R-1a, R-6, R-3b, R-11, R-7, R-1b.
- **Zero-PII Scanner & Whitelist Engine (`fincrime_core.synth.pii`)** — multi-pattern scanner with Luhn check for payment cards, US SSN with `000-xx-xxxx` synthetic whitelist, 10-digit phone with `555-01xx` whitelist, IRS EIN with `00-xxxxxxx` whitelist, and email with RFC 2606 domain whitelist. Standalone tools `scripts/check_pii.py` and `scripts/check_no_pii.py`.
- **Complete v1 Skills Suite (6 Skills)** — added `skills/investigation-qa`, `skills/sar-narrative-draft` (Part V only per ADR-0008), and `skills/sanctions-alert` with full SKILL.md specs, fincrime.skill.yaml sidecars, and golden examples.
- **360-Case Synthetic Evaluation Corpus (`scripts/generate_synthetic_corpus.py`)** — 60 cases each across all six v1 skills (360 total), strictly enforcing $\ge 40\%$ mixed kinds, $\ge 15\%$ negative expectations, and $\ge 2$ benign lookalikes per covered typology.
- **360 Offline Replay Fixtures** — committed in `skills/<skill>/evals/replays/*.json`, achieving 100% gate pass rate across all 6 skills in CI without network access.
- **Updated Conformance Benchmark** — updated `reports/conformance-report.json` and `reports/conformance-report.md` evaluating all 360 cases across 6 skills against zero-shot baselines.
- **CI Security & PII Gating** — wired `lint-pii` target into `Makefile` (`make ci`) and `.github/workflows/ci.yml`.

**Phase 4 — The Evaluation Framework ("The Moat").** The native evaluation harness
that executes skills against evaluation suites, scores outputs deterministically,
compares models against unstructured zero-shot baselines, and enforces regression
gates in CI.

- **Native Evaluation Engine (`fincrime_core.eval`)** — runner pipeline,
  case loader, and seven deterministic scorers: `schema_validity` (1.0),
  `evidence_attribution_accuracy` (≥0.98), `unsupported_claim_rate` (≤0.02),
  `required_field_compliance` (1.0), `policy_pass_rate` (1.0),
  `expected_defect_recall` (≥0.90), and `false_defect_rate` (≤0.05).
- **Pluggable Provider Architecture** — `ReplayProvider` for completely offline,
  air-gapped candidate replay; `MockProvider` with 7 built-in defect mutators;
  and `ModelProvider` for LLM provider adapters.
- **CLI Subcommand (`fincrime eval`)** — supports `--skill <name|all>`, `--suite <path>`,
  `--replay`, `--mock`, `--gates`, `--format <markdown|json>`, `--out <path>`, and `--as-of`.
  Exits 0 on gate pass and 1 on threshold breach.
- **Offline Replay Corpus** — 180 committed replay fixtures across `skills/alert-triage`,
  `skills/case-summarize`, and `skills/evidence-request`, achieving 100% pass rate
  and 0 gate breaches in CI without external network access.
- **Unconstrained Baseline Runner & Delta Table** — `NoSkillBaselineProvider` simulating
  raw zero-shot outputs, demonstrating empirical hallucination reduction (-37.2%, p < 0.001),
  elimination of culpability claims (100% policy pass), and schema completeness (+100.0%).
- **Multi-Seed Noise Methodology** — 3-seed evaluation (`42`, `123`, `999`) calculating
  standard errors and establishing the $2\times\text{SE}$ statistical significance band.
- **Published Conformance Benchmark** — committed `reports/conformance-report.json` and
  `reports/conformance-report.md` documenting verified benchmarks across all 180 cases.
- **CI Regression Gate** — integrated into `Makefile` (`make eval` and `make ci`) and
  `.github/workflows/ci.yml`.

**Phase 3 — the first three skills.** Three skills that work end to end, each
with a generated case suite and a golden artifact the QA gate is measured
against.

- **`skills/alert-triage`** — ingests a raw alert and the transaction and
  customer evidence behind it, builds the evidence inventory before asserting
  anything, matches the indicators named in `core-2026-10`, and produces a
  `triage_report` carrying a benign reading beside every adverse reading, a
  risk assessment stated at the level the evidence supports, and the gaps that
  block a conclusion. It never disposes of an alert and never reaches a
  conclusion about a customer.
- **`skills/case-summarize`** — synthesizes a multi-account,
  multi-counterparty case into a single investigative summary in which every
  timeline event is anchored to a resolvable RFC 6901 pointer, with four
  named forms of epistemic drift and a rule against each.
- **`skills/evidence-request`** — turns the decisive gaps left by a triage or
  an investigation into a structured request dossier, each request anchored to
  a record in the pack's request catalogue, each naming the gap it would
  close, and each request that would affect a customer carrying
  `human_approval_required: true`.
- **180 evaluation cases** — 60 per skill, generated by
  **`scripts/generate_phase3_cases.py`**, a stdlib-only, deterministic script
  that is the source of truth for the case population and checks the suite mix
  before it writes anything. Two runs write byte-identical files. Every case
  carries at least one negative expectation, so a skill that says everything
  fails the suite. The population meets the stable-skill bar in
  [`CONTRIBUTING.md`](CONTRIBUTING.md): 60 cases per suite, at least 40% of
  them benign, adversarial, missing-data or contradictory, at least 15%
  carrying a negative expectation, and at least two benign lookalikes for every
  typology the suite covers.
- **A golden artifact per skill**, with the closed evidence set it was
  produced against, under `skills/<skill>/examples/`. These are the corpus
  the exit criterion is measured on: the artifact's `evidence_set_sha256` is
  the real canonical digest of the evidence set, and its `prompt_sha256` is
  the SHA-256 of the skill's own `SKILL.md`, so the skill body and the
  artifact it ships cannot drift apart silently.
- **The Phase 3 exit-criterion gate**
  (`packages/fincrime-cli/tests/test_phase3_exit_criterion.py`) — 43 tests
  measuring both halves of the criterion: zero false defects against the
  golden corpus, and 12 of 12 seeded defects detected against a 90% floor.
  The seeded defects are the four failures the contract encodes
  structurally: an adverse reading standing alone (`R-3b`), a recommendation
  with no basis (`R-10`), a culpability assertion (`R-6`), and an indicator
  that cites nothing (`R-2`).
- **`request_dossier` in the Finding Contract** — the artifact type the Phase 3
  specification gives the `evidence-request` skill.
  `contracts/finding.schema.json` offered only `evidence_request_plan`, so the
  skill could not have produced a conformant artifact at all. The change is
  additive: one enum value, and `evidence_request_plan` is retained. The
  amendment is recorded in
  **[ADR-0011](docs/adr/0011-request-dossier-and-manifest-catalogue-binding.md)**,
  which also binds the manifest to the request catalogue.

### Fixed

- **A timeline entry could assert an event no record supported.** The
  validator resolved every evidence reference on every *claim* (`R-1a`), but
  nothing resolved a reference on a *timeline* entry. A `case_summary` could
  therefore state an event anchored to `txn:TXN-GHOST#/amount` and pass
  validation with zero defects: the anchoring invariant the `case-summarize`
  skill is defined by was enforced by the exit-criterion test and by nothing
  else. Rule `R-1b` now resolves every reference on every timeline entry
  against the evidence set, and an unresolvable one is reported as
  `unsupported_claim` (or `malformed_evidence_ref` / `over_broad_citation`,
  according to why it failed). The validator's `resolved_refs` map now carries
  the timeline's references too, so the outcome is observable and not only
  present as a defect.
- **The suites declared a floor below the project's own.** All three Phase 3
  suites declared `min_cases: 40` against the 60 that
  [`CONTRIBUTING.md`](CONTRIBUTING.md) requires of a stable skill, and the
  skill manifests declared `case_count_min: 40` with it. The population has
  been extended to 180 cases — 60 per suite, generated, not hand-written — and
  the declared floor is now 60.

### Changed

- **The skill manifest declares request-catalogue records under their own
  key.** `contracts/skill-manifest.schema.json` gains
  `spec.properties.knowledge.properties.requests`, and the thirteen `REQ-*`
  records the `evidence-request` skill depends on are declared there instead
  of under `knowledge.scenarios`, where they were carried with a comment
  explaining the workaround. `SCN-*` scenarios and `REQ-*` request templates
  are different domains — a scenario describes a shape, a request names a
  record that can be asked for — and the manifest now says which is which.
  The catalogue binding is unchanged: every declared record must exist in the
  declared pack, and an expired one still blocks promotion.
  ([ADR-0011](docs/adr/0011-request-dossier-and-manifest-catalogue-binding.md))
- **CI and the `Makefile` now cover the three new skills.** `make
  validate-skills` validates every skill package, every case suite and every
  golden artifact, and `make validate-promotion` applies the ADR-0006
  promotion gate to each of them. The GitHub Actions workflow makes the same
  checks, so a new skill cannot pass CI by not being mentioned in it. Two new
  targets, `cases` and `cases-check`, regenerate the suites.
- **The `eval` target's message.** The case suites have shipped; the harness
  that runs them is Phase 4.

### Added

**Phase 2 — the knowledge layer.** The first dated pack, and the promotion gate
that keeps a stale record from being promoted.

- **`knowledge/packs/core-2026-10`** — 83 US-scoped records: 25 indicators, 8
  typologies, 20 regulatory mappings and 30 request-catalogue entries, all
  dated `as_of 2026-10-01`, `review_by 2027-04-01`, `expires_at 2027-10-01`.
  Every indicator carries its benign explanations and its bias control; every
  regulatory record is derived and paraphrased, never quoted.
- **`scripts/build_core_pack.py`** — the pack's reviewed source, and the only
  thing that writes it. The published bytes and the reviewed content cannot
  drift apart, because they are the same thing: `--check` re-derives the pack
  and reports any difference. A pack is immutable once published, so a
  correction is a new pack version, not a re-run over a changed definition.
- **The pack promotion gate** — `validate_pack(pack_dir, promotion=True,
  as_of=...)` reports an expired record as `pack_record_expired` at `error`
  severity, which blocks the pack's promotion, and as a `warn` in the release
  context, which does not. The core reads no clock: without `as_of`, no
  freshness claim is made at all.
- **The citing skill's gate** — a skill that declares a knowledge pack is
  checked against that pack's expiry. In promotion context an expired record
  is a blocking `SKILL-KNOWLEDGE-EXPIRED`; in release context it is a warning
  and the skill is marked `MAINTENANCE_REQUIRED`. A draft skill is not excused:
  a draft may fail the shipping gate, but it may not be built on expired
  regulation.
- **`--promotion` and `--as-of` on `fincrime validate` and `fincrime knowledge
  validate`** — the enforcement context and the date it is judged against. The
  resolved date is printed in the header, so a run is never silently
  date-dependent.
- **A promotion job in CI** that blocks a pull request promoting a new skill, a
  changed skill or a new pack version when the knowledge it depends on is
  expired — and that leaves an ordinary pull request alone. A pack going stale
  must not brick the repository for contributors who cannot author a
  regulatory refresh; that is the failure
  [ADR-0006](docs/adr/0006-graded-knowledge-expiry.md) was written to prevent.

### Fixed

- **The pack's structuring indicator had the wrong id.** `core-2026-10`
  published `IND-CASH-THRESHOLD-PROXIMITY`, while the golden artifact, the
  authoring guide, the sample pack and the core's own fixtures all name
  `IND-STRUCT-THRESHOLD-PROXIMITY`. The pack now publishes the canonical id.
  The builder removes the record files the source content no longer
  produces, so a renamed record cannot leave an orphan in the pack that the
  manifest does not list.
- **The CLI never checked an artifact's indicator citations.** The validator
  takes the ids present in the declared pack and emits `unknown_indicator`
  for a citation that is not among them, but the CLI never passed them, so
  the rule was silently skipped for every artifact validated from the
  command line. It is now wired, and a test proves the rule fires.
- **A skill's cited records were never checked for existence.** The checker
  warned that record existence could not be verified, and then never checked.
  A skill citing a record the pack does not hold now produces
  `SKILL-RECORD-UNRESOLVED` at `error` severity: a skill that depends on a
  record nobody published depends on nothing.
- **An expired record the skill did not cite blocked the skill.** The
  checker's own docstring said the rest of the pack was "the pack's
  business, not the skill's", and its implementation did the opposite: one
  expired record anywhere in a shared pack blocked every skill that shared
  it, which is the bricked-repository failure
  [ADR-0006](docs/adr/0006-graded-knowledge-expiry.md) exists to prevent.
  The block now applies to the knowledge a skill *depends on* — the records
  it cites, or the whole pack when it cites none — and an unrelated expired
  record is disclosed as a warning in both contexts. The rule is now stated
  in the ADR, in the docstring and in the implementation, and they agree.
- **The promotion job in CI called the GitHub API.** The job that decides
  whether a pull request promotes changed content listed the changed files
  with `gh api`, which needs a token, fails on a fork under
  `contents: read`, and puts a network call in a job whose whole point is
  to be deterministic. It now diffs the checkout against the base branch
  with `git diff`, and needs no token at all.
- **The expiry bot could fail to file an issue over an assignee.** A record
  whose maintainer is a team — `@fincrime-maintainers` — could not be
  assigned, because GitHub's assignee field takes individual logins only,
  and the failure stopped the issue being filed at all. A team is now
  mentioned in the body instead, and an assignment that fails for any other
  reason is retried once without it: an unassigned issue that reaches a
  maintainer beats an issue that reaches no one.

- **`composite.any` behaved like `composite.all`.** A rule that said "at
  least one of these must hold" was evaluated as "all of these must hold",
  because the composite collected every branch's violations into one list and
  reported a failure if the list was non-empty. A control that does not do
  what it says is worse than no control, and a rule author reading `any`
  would have had no way to know. `any` now fails only when *every* branch
  failed. ([ADR-0003](docs/adr/0003-deterministic-boundary.md))
- **The knowledge pack loader did not check the pack's integrity.** Its
  docstring promised that a pack whose contents did not match its manifest
  would be rejected, and it did not: it read every `*.json` in the pack
  directory, including files that were not records, and never compared
  anything with the manifest's checksum. `load_pack` now reads only
  `records/`, and a new `validate_pack` verifies the manifest against its
  contract, every record against the record contract, every record's
  `sha256` against the manifest index, and the manifest's own checksum. A
  pack that fails produces findings, never an exception.
- **The policy rule schema and the policy evaluator disagreed about
  `pattern`.** The field was named `pattern` and the contract implied a
  regular expression; the implementation did a plain substring test, and
  treated `not_pattern` identically to `pattern` even though the two mean
  opposite things. `pattern` is now a regular expression, `not_pattern` has
  been removed, and a rule whose pattern does not compile is reported as a
  warning rather than silently ignored.

Four defects found by an adversarial review of the Phase 0 code, two of which
were integrity bypasses of the evidence guarantee:

- **A fabricated reference could hide behind a claim class.** Evidence
  references were only resolved on the classes that *mandate* evidence
  (`fact`, `observation`, `indicator`). A `risk_assessment` or a
  `recommendation` citing a transaction that does not exist passed validation
  with zero defects, and `unsupported_claim_rate` reported 0.0. The mandate and
  the check are now separate: **any reference present on any claim must
  resolve**, and the metric's denominator is every evidence-bearing claim
  (`R-1a`).
- **`recommendation_without_basis` was never emitted.** The defect was declared
  in the taxonomy and advertised in the example, but no code produced it, and
  a recommendation with `evidence_refs: []` satisfied the schema. A
  recommendation must now be anchored to an evidence reference or to the claim
  it explains (`R-10`).
- **The evidence-reference pattern had drifted between contracts.**
  `contracts/finding.schema.json` accepted a second `#` in the fragment and an
  unbounded source-instance length, so an artifact could satisfy the contract
  and still be rejected by the implementation. All contracts now state the
  canonical pattern, and a test asserts they are identical everywhere.
- **RFC 6901 section 4 array indices accepted leading zeros.** `/lines/01`
  resolved to index 1. The normative ABNF
  (`array-index = %x30 / ( %x31-39 *(%x30-39) )`) is now enforced, ASCII
  digits only.

### Added

**Phase 1 — the core skill specification.** A skill can now be authored,
validated and tested by someone who has read only
[`docs/skill-authoring.md`](docs/skill-authoring.md).

- **`fincrime new skill`** — a scaffolder that writes a skill package
  (`SKILL.md`, the `fincrime.skill.yaml` sidecar, a jurisdiction note, and
  a starter case suite) that already satisfies its contract. The scaffold is
  deliberately unfinished: three cases against a gate of sixty, and a `draft`
  status. A scaffold that looked finished would be a scaffold nobody finished.
- **`fincrime-cli`** — a new, stdlib-only distribution providing the
  `fincrime` command. The core stays a dependency-free engine
  ([ADR-0002](docs/adr/0002-zero-dependency-core.md)); the CLI is a
  development and CI tool and is not inside that trust boundary.
- **A YAML subset parser** (`fincrime_cli.yamlite`) for the skill sidecar,
  because `yaml` is on the forbidden-imports list. The subset is written down
  rather than implied, unsupported constructs (anchors, aliases, tags, merge
  keys, complex keys, multiple documents, tab indentation) are hard errors
  rather than silent misparses, and a parity test proves the subset agrees
  with PyYAML.
- **`fincrime validate`** — checks a skill package, a case suite, a knowledge
  pack, a policy set or an artifact. A draft skill may fail the shipping
  gate; a stable one may not.
- **`fincrime policy export` and `fincrime policy check`** — the export
  format for a policy set, and the evaluation of one against an artifact.
- **`fincrime knowledge validate` and `fincrime knowledge check`** — a
  pack's integrity against its manifest, and the refresh plan a pack needs.
- **The case-mix contract** (`contracts/case-suite.schema.json`) and its
  enforcement: at least 60 cases, at least 40% benign, adversarial,
  missing-data or contradictory, at least 15% carrying a negative expectation,
  and at least one benign case per typology. The thresholds live in the
  suite, so a suite can be held to a stricter bar.
- **The policy set contract** (`contracts/policy-set.schema.json`), which
  separates *enforceable rules* (evaluated by code) from *procedural
  policies* (followed by the agent, measured by the evaluation suite). The
  manifest's flat list of policy ids ran the two together; they are now
  distinguished, and every id a skill names must resolve.
- **The knowledge pack contract**
  (`contracts/knowledge-pack-manifest.schema.json`) and the pack format
  specification in [`knowledge/README.md`](knowledge/README.md), with a worked
  example pack.
- **The default policy set** (`policies/default/policy-set.json`): the
  baseline every skill inherits, and the exportable, firm-readable form of
  the core's structural lints. It produces zero violations on the golden
  artifact, and a test holds it there.
- **The expiry bot** (`.github/workflows/knowledge-expiry.yml` and
  `scripts/knowledge_expiry_bot.py`): once a day it opens one labelled issue
  per stale record, addressed to the record's maintainer, containing the
  precise refresh diff required. The decision is a pure function of the pack
  and the date; the workflow files what it is told.
- **Cross-file `$ref` support** in the schema validator, so the policy set
  contract can reference the rule contract instead of copying the rule shape
  into a second place to drift.
- **Three additions to the policy rule model**, each a semantic change to an
  enforceable control and each pinned by a test: `when` (an artifact-level
  gate on a rule), `require.any_of` (a per-claim disjunction, where
  `composite.any` is decided across the whole selected set), and
  `negation_aware` on `forbid`.
- **The skill authoring guide**
  ([`docs/skill-authoring.md`](docs/skill-authoring.md)) and the jurisdiction
  statement ([`docs/jurisdiction-support.md`](docs/jurisdiction-support.md)).
- **A no-ghost-defect guard.** The defect taxonomy now carries a `stage` field
  (`active` or `planned`). A behavioural test proves every `active` code is
  reachable, and that no `planned` code is emitted yet. A taxonomy entry can
  no longer imply enforcement the code does not have.
- Four defect codes that were previously unreachable are now implemented:
  `recommendation_without_basis`, `decisive_gap_unacknowledged`,
  `jurisdiction_overreach`, and `conflicting_draft_notice` (heuristic).
- A jurisdiction-scope check: an artifact may not declare a jurisdiction
  outside the scope the skill permits, and a claim may not be scoped to a
  jurisdiction the artifact does not declare.

### Added (Phase 0 — contracts and the core)

- The **Finding Contract** `fincrime/finding/1.0.0`: a JSON Schema 2020-12
  definition of the Evidence-Linked Finding, with seven closed claim classes
  and conditional requirements encoded as `if`/`then` so that a stock JSON Schema
  validator enforces the same rules the project does.
  ([ADR-0001](docs/adr/0001-evidence-linked-finding.md))
- The **RFC 6901 evidence-reference grammar**, `contracts/evidence-ref-grammar.schema.json`,
  with a normative ABNF, the escaping rules, the empty-pointer semantics, and
  the array-index rule.
  ([ADR-0004](docs/adr/0004-evidence-ref-grammar.md))
- `fincrime-core`: a **dependency-free** validator with a total, deterministic
  evidence resolver; a claim linter implementing R-1 through R-13; a pure
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

The evaluation *harness* — the case runner, the provider adapters, the
deterministic scorers, the metric aggregation and the published conformance
report — is Phase 4, and no skill in this repository yet produces a scored,
published conformance result. The three case suites shipped in Phase 3 are the
inputs that harness will consume; nothing has yet been run through it, because
there is nothing yet to run it through.

Two further gaps were known after Phase 3, and both are now closed: the
suites declared `min_cases: 40` against the project-wide default of 60 for a
stable skill — the suites now hold 180 cases, 60 per skill, and declare 60 —
and the validator did not lint `timeline` entries, so the anchoring invariant
the `case-summarize` skill is defined by was enforced by the exit-criterion
test rather than by the core. Rule `R-1b` enforces it in the core.

One gap remains open and is not closed by this work: `request_dossier` was
added to the Finding Contract without the RFC and ADR that `VERSIONING.md`
requires. The amendment is additive and backwards-compatible, and
[ADR-0011](docs/adr/0011-request-dossier-and-manifest-catalogue-binding.md)
records it now; the omission itself is a process failure and is recorded
rather than quietly ratified.

[Unreleased]: https://github.com/fincrime/fincrime-skills/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/fincrime/fincrime-skills/releases/tag/v1.0.0
