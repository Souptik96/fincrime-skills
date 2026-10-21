---
name: evidence-request
description: >-
  Take the decisive evidence gaps left by a triage or an investigation and
  turn them into a structured, defensible set of information requests, each
  anchored to a record in the request catalogue and each naming the gap it
  would close. Use when the question is what to ask for next, and why that
  record rather than another. Produces a `request_dossier` conforming to
  `fincrime/finding/1.0.0`.
license: Apache-2.0
metadata:
  fincrime_version: "1.0.0"
  contract_version: "fincrime/finding/1.0.0"
  knowledge_pack: "core-2026-10"
  jurisdiction: "US"
  risk_tier: "low"
  domain: "investigation"
  related_skills: "alert-triage,case-summarize,investigation-qa"
---

# Evidence Request

> ⚠️ This skill **drafts** information requests. It never issues one, never
> contacts a customer, never contacts a third party, and never disposes of a
> case. Every request that could affect a customer waits for a human to
> approve it. Jurisdiction scope: **United States**. See
> `references/jurisdiction-us.md`.

## When to use

- A triage or an investigation has ended with decisive gaps: questions the
  evidence cannot answer, where the answer would change the outcome.
- Someone must decide what to ask a customer, a counterparty, a registrar or
  an acquirer for, and needs the request set justified rather than guessed.
- The existing request is vague — "get more information" — and has to become
  a named record, a named purpose and a named gap.
- A case is at the point where the remaining work is gathering, not
  analysing, and the gathering has to be defensible.

## When NOT to use

- To decide whether a case should be escalated. Use `alert-triage` or
  `case-summarize`, and read their gap lists.
- To draft a suspicious activity report narrative. Use
  `sar-narrative-draft`.
- To review an artifact for defects. Use `investigation-qa`.
- To interrogate a witness, a subject or a staff member. This skill is
  about records, and a person is not a record.
- To obtain evidence the firm has no lawful route to. The skill flags such
  a request for a human to decide; it does not draft it as though it were
  available.

## Required inputs

| Input | Description |
|---|---|
| `gap_list` | The decisive gaps, as recorded by the triage or investigation that produced them. |
| `evidence_set` | The closed world the gaps were identified against: what is already held, and what is not. |
| `subject_scope` | The customer, entity, account or counterparty the requests would be made of. |

## Optional inputs

| Input | Description |
|---|---|
| `knowledge_index` | The knowledge pack, whose request catalogue is the anchor for every request. |
| `policy_rules` | The firm's deterministic rules, used to check enforceable controls. |
| `prior_requests` | Requests already made, and what they returned, so the same ground is not covered twice. |

## Preconditions

| ID | Check | On failure | Message |
|---|---|---|---|
| PC-1 | The gap list and the evidence set are supplied | `stop` | There is nothing to request for without the gaps and the evidence already held. |
| PC-2 | The evidence set is closed and every source carries a stable source id | `stop` | A request cannot be justified against an evidence set nobody can check. |
| PC-3 | The subject scope is supplied | `stop` | A request with no named subject is not a request; it is a wish. |
| PC-4 | The declared knowledge pack and its request catalogue are resolvable | `stop` | A request that is not anchored to the catalogue cannot be justified to the person who has to approve it. |

## Procedure

Follow the stage pattern S0–S7. Each stage states what it produces and what it
requires.

### S0 — Frame

Establish what is under assessment: the subject scope, the artifact the gaps
came from, the jurisdiction, and the evidence set as the closed world.
Produce `frame`.

*Requires:* nothing. *Guard:* none.

### S1 — Ground

Enumerate what is already held and what is missing, and record the gaps with
the decision each one blocks. A gap is **decisive** when the answer would
change the assessment, not merely when it would be interesting. Produce
`evidence_inventory` and `gaps`.

*Requires:* the gap list and the evidence set. *Guard:* `POL-EVIDENCE-INVENTORY-FIRST`.

### S2 — Extract

For each decisive gap, state what the evidence currently shows, what it does
not show, and what would change if the missing record arrived. A gap is an
absence of evidence, and this stage describes the absence rather than
filling it. Produce `observation`.

*Requires:* `evidence_inventory`. *Guard:* `POL-INDICATOR-REQUIRES-INDICATOR-ID`.

### S3 — Hypothesize

Form the readings the evidence supports about why the record is missing and
what it would show — including at least one benign reading where an adverse
reading is in play. Produce `hypothesis`.

*Requires:* the claim set. *Guard:* `POL-BENIGN-HYPOTHESIS-REQUIRED`.

### S4 — Contrast

Surface the conflicts between candidate requests: two records that answer the
same gap, a request that overlaps one already made, a request the firm may
have no lawful route to. Produce `contradiction`.

*Requires:* the claim set. *Guard:* none.

### S5 — Assess

State whether the remaining gaps are decisive, and the level at which the
recorded gaps cap the assessment. Produce `risk_assessment`.

*Requires:* `gap_list`. *Guard:* `POL-ASSESSMENT-NEEDS-INDICATOR`.

### S6 — Recommend

Produce the request set. **Each recommendation names the catalogue record it
maps to** in `knowledge_ids`, names the gap it closes in `explains`, states
what the record would establish, and says where it comes from. A
recommendation that would affect a customer carries
`human_approval_required: true`. Produce `recommendation`.

*Requires:* the claim set. *Guard:* `POL-RECOMMENDATION-NEEDS-BASIS`.

### S7 — Escalate

Name the decision the human still owns: which of the drafted requests are
issued, to whom, by whom, and in what order. Produce `escalation`.

*Requires:* the claim set. *Guard:* none.

## The request catalogue

The catalogue in `core-2026-10` is the anchor. A request that maps to no
catalogue record is not a request the skill may draft; it is a gap in the
catalogue, and the skill says so instead of improvising. The catalogue
entries this skill cites are:

- **`REQ-BANK-STATEMENTS-12M`** — the statements of the subject account for a
  full year, so that a pattern can be separated from an episode. Requested
  wherever a single transaction or a single month would be a weak basis.
- **`REQ-POS-SETTLEMENT-BATCH`** — the batch-level settlement file showing the
  individual card transactions and the net amount remitted. Establishes the
  card side of a cash-heavy merchant's takings, not the cash side.
- **`REQ-ATM-TRANSACTION-LOG`** — the terminal-level log of cash withdrawals
  and deposits, with terminal, location, time and amount. Requested where a
  dispersion across terminals is in question.
- **`REQ-SOURCE-OF-WEALTH`** — a signed statement of how the customer's wealth
  was accumulated, with supporting documentation. Establishes a stated
  explanation, which is a hypothesis and not a verified fact until the
  documents are in.
- **`REQ-UBO-REGISTRY-PROOF`** — the extract of the official beneficial-
  ownership register, obtained from the register itself rather than from the
  customer. Establishes what the register says, which is a different claim
  from what the customer said.
- **`REQ-UBO-CHART-SIGNED-DECLARATION`** — the customer's own ownership chart
  with a signed control declaration.
- **`REQ-CORPORATE-REGISTRY-EXTRACT`** — the official register entry for a
  company, with incorporation, registered office, directors and good
  standing. Establishes what the register says about the entity independently
  of the entity's own account of itself.
- **`REQ-COUNTERPARTY-BANK-STATEMENTS`** — the statements of a counterparty,
  obtained with the counterparty's authority or through a lawful request.
  Establishes the funds' onward movement, or its absence.
- **`REQ-INVOICE-LEDGER`** — the complete invoice ledger for a period,
  showing every invoice raised or received.
- **`REQ-COMMERCIAL-CONTRACTS`** — the contracts, purchase orders and delivery
  terms that explain why the subject transacted with the counterparty in
  question, at the price in question.

Each catalogue record states what it establishes and what it does not, and
each is the answer to a particular kind of gap. The skill's job is to match
the gap to the record, not to ask for the record.

## Output

A `request_dossier` artifact conforming to `fincrime/finding/1.0.0`:

- `artifact.artifact_type` = `request_dossier`
- `claims` — the required claims are `frame`, `gaps`, `observation` and
  `recommendation`; `evidence_inventory`, `hypothesis`, `contradiction`,
  `risk_assessment` and `escalation` are optional
- `recommendation` claims carry `knowledge_ids` naming the catalogue record
  they map to, `explains` naming the gap they close, and
  `human_approval_required: true` wherever the request would affect a
  customer
- `human_decision_required` — always at least one: which of the drafted
  requests are issued
- `provenance` — the model's identity, the prompt hash, the evidence-set
  hash, the knowledge pack version and its `as_of`, and the run identifier

> **Contract note.** The manifest declares `request_dossier`, as this skill's
> Phase 3 specification requires, and `contracts/finding.schema.json` now
> enumerates it alongside `evidence_request_plan`. Both names are legal
> artifact types; this skill uses `request_dossier` throughout.

**The dossier is not a request.** The skill must not produce a `decision`
claim, and it must not send anything to anybody.

## Escalation

Report a finding of severity `error` and refuse to sign off when:

- a recommendation does not map to a catalogue record;
- a recommendation names a gap it does not explain;
- a recommendation that would affect a customer does not carry
  `human_approval_required: true`;
- a `recommendation` claim carries neither evidence references nor the claim
  it explains;
- a gap is recorded as decisive without a stated consequence, or a gap is
  filled with an assumption;
- the dossier states or implies that the customer is suspicious, that the
  activity is laundering, that a report is required, or that the subject is
  a criminal;
- a cited knowledge record has expired.

## Guardrails

- **Never** issue a request, contact a customer, or contact a third party.
  The skill drafts; a human approves and issues.
- **Never** draft a request that answers no gap in the list. A catalogue is
  not a shopping list, and a request set is the minimum that closes the
  decisive gaps.
- **Never** present a missing record as evidence against the customer. Until
  the record arrives, the gap is a gap.
- **Never** draft a request the firm has no lawful route to make as though
  it were available. Flag it for the human to decide.
- **Never** state that the subject is suspicious, that the activity is
  laundering, or that a report is required.
- **Never** assert criminality of the subject.
  `POL-NO-CRIMINALITY-CLAIMS` is a hard control.
- **Never** let an unfilled request raise the confidence of the assessment
  behind it. A pending request caps what may be said, and the dossier says
  so.

## Provenance

Every dossier records the model's identity and version, the hash of the
prompt, the hash of the evidence set, the knowledge pack version and its
`as_of`, the policy set version, and the run identifier. Every request in it
names the catalogue record it is anchored to, so a reviewer can check the
justification without reading the case.

## Evaluation

The case suite is at `evals/suites/evidence-request`. The Phase 3 bar is at
least 40 cases, at least 40% of them benign, adversarial, missing-data or
contradictory, at least 15% carrying a negative expectation. The suite must
include cases where no request is warranted, cases where the catalogue has no
answer, and cases where the gap list is empty.

The `investigation-qa` skill reviews the dossiers this skill produces: seeded
defects — a recommendation mapped to no catalogue record, a request with no
human approval, a gap filled with an assumption — must be found, and a
conformant dossier must produce no false defect.
