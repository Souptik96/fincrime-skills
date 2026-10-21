---
name: case-summarize
description: >-
  Synthesize the transactions, accounts, counterparties and documents of an open
  case into a single investigative summary whose every event is anchored to a
  resolvable evidence pointer. Use when a case spans several accounts or
  counterparties and the reader needs one account of what happened, without
  the summary drifting into certainty the evidence does not carry. Produces a
  `case_summary` conforming to `fincrime/finding/1.0.0`.
license: Apache-2.0
metadata:
  fincrime_version: "1.0.0"
  contract_version: "fincrime/finding/1.0.0"
  knowledge_pack: "core-2026-10"
  jurisdiction: "US"
  risk_tier: "medium"
  domain: "investigation"
  related_skills: "alert-triage,evidence-request,investigation-qa"
---

# Case Summarize

> ⚠️ This skill **summarizes** what the evidence records. It never decides,
> never files, never closes a case, and never strengthens a conclusion on its
> way into the summary. It produces an investigative summary that a human
> acts on. Jurisdiction scope: **United States**. See
> `references/jurisdiction-us.md`.

## When to use

- A case spans more than one account, more than one counterparty, or both,
  and the reader needs a single account of what happened.
- The alert triage is done and the case has moved on to investigation; the
  summary is the artifact the investigator reads next.
- Someone outside the immediate record — a reviewer, a supervisor, a second
  analyst — has to understand the case without reading every transaction.
- The activity in the record is long enough that a pattern and an episode
  have to be separated before anything can be said about it.

## When NOT to use

- To triage a new alert. Use `alert-triage`, which works on initial evidence
  and produces the gap list this skill starts from.
- To write a suspicious activity report narrative. Use
  `sar-narrative-draft`, and note that the report is a human's filing.
- To ask for records that are missing. Use `evidence-request`.
- To review an artifact for defects. Use `investigation-qa`.
- On free prose. The review and the summary are structural: free text has no
  claims to attribute.

## Required inputs

| Input | Description |
|---|---|
| `evidence_set` | The closed world: the transaction, account, counterparty and document records across every account in scope. |
| `subject_scope` | The accounts, counterparties and entities in scope, and the period the summary covers. |

## Optional inputs

| Input | Description |
|---|---|
| `knowledge_index` | The knowledge pack used to resolve indicator ids, their benign explanations and their dates. |
| `policy_rules` | The firm's deterministic rules, used to check enforceable controls. |
| `prior_findings` | Earlier artifacts for the same case, whose claims may be carried forward under the drift rule. |

## Preconditions

| ID | Check | On failure | Message |
|---|---|---|---|
| PC-1 | The evidence set and the subject scope are supplied | `stop` | There is nothing to summarize without the evidence and the scope it covers. |
| PC-2 | The evidence set is closed and every source carries a stable source id | `stop` | Evidence attribution cannot be checked against an open or unaddressable evidence set. |
| PC-3 | Every source in scope resolves by pointer | `stop` | A timeline anchored to a pointer that does not resolve is a timeline of assertions. |
| PC-4 | The declared knowledge pack is resolvable | `annotate` | Indicator existence and freshness cannot be verified; disclose it. |

## Procedure

Follow the stage pattern S0–S7. Each stage states what it produces and what it
requires.

### S0 — Frame

Establish what is under summary: the subject scope, the accounts and
counterparties in it, the period covered, the jurisdiction, and the evidence
set as the closed world. Produce `frame`.

*Requires:* nothing. *Guard:* none.

### S1 — Ground

Enumerate the evidence before asserting anything: which accounts, which
counterparties, which documents, and what is absent from the set. Record the
gaps that matter, marking the ones that would be decisive against a
conclusion. Produce `evidence_inventory` and `gaps`.

*Requires:* the evidence set. *Guard:* `POL-EVIDENCE-INVENTORY-FIRST`.

### S2 — Extract

Resolve every source in scope by pointer, then lay out what happened as a
timeline. **Every timeline entry carries at least one RFC 6901 evidence
reference** — `txn:*` for a transaction, `doc:*` for a document — and the
reference must resolve to the value the entry describes. An entry whose
pointer does not resolve is not an event: it is a gap, and it goes in the gap
list. State the patterns the resolved values show. Produce `observation` and
`timeline`.

*Requires:* `evidence_inventory`. *Guard:* `POL-INDICATOR-REQUIRES-INDICATOR-ID`.

#### The indicators this skill matches

The five indicators below are the ones the skill cites from `core-2026-10`.
Each is a **measured pattern** over the resolved records, and each carries the
benign explanations that a summary has to carry with it.

- **`IND-MULTI-ACCOUNT-AGGREGATION`** — activity that looks unremarkable
  account by account but aggregates across accounts with a common owner,
  signatory or address into a materially different picture. Defined only
  where the common control is evidenced, not assumed. *Benign readings:* a
  sole trader with an account per branch; a family business running a
  personal and a corporate account; a customer who prefers several accounts
  for administrative reasons; accounts that share an address because of a
  common landlord, a school or a company house.
- **`IND-FUNNEL-ACCOUNT-AGGREGATION`** — many distinct third-party
  originators crediting a small number of accounts, with the credits then
  consolidated downstream. *Benign readings:* a payment gateway crediting
  from many merchants and paying out to settlement; a charity or membership
  body collecting donations into a central fund; a ride-share or delivery
  platform crediting drivers on the customer's behalf; a payroll process
  crediting employees and consolidating statutory deductions.
- **`IND-CIRCULAR-TRANSFER-CHAIN`** — value leaving an account and returning
  to it, or to an account with a common owner, through one or more
  counterparties. *Benign readings:* a group treasury sweeping between
  operating accounts daily; a merchant refunding a deposit to the original
  payment method; a processor returning a chargeback or settlement
  adjustment; a business lending to itself through a subsidiary for a
  documented reason.
- **`IND-THIRD-PARTY-TRANSFER-CHAIN`** — credits received from one party and
  debited onward to unrelated third parties, with no apparent commercial
  relationship to the recipients. *Benign readings:* a market stall holder
  receiving cash from traders and paying suppliers; a concierge or payment
  service passing funds to end customers; a customer managing money for
  relatives and candid about it; a business holding funds briefly before a
  refund visible in the same account.
- **`IND-COMMON-OWNERSHIP-SHELL-CHAIN`** — two or more companies trading with
  each other while sharing owners, directors, registered addresses or
  signatories, persistently. *Benign readings:* a family group of companies
  sharing directors and premises; a holding structure used for tax or risk
  reasons with documented trades; two businesses sharing a serviced-office
  address and a director by coincidence; a group centralising functions and
  invoicing for them at a market rate.

### S3 — Hypothesize

Form the readings the evidence supports, including at least one benign
reading for every adverse reading, each with its own falsifier. Produce
`hypothesis`.

*Requires:* the claim set. *Guard:* `POL-BENIGN-HYPOTHESIS-REQUIRED`.

### S4 — Contrast

Surface the contradictions: two sources that disagree, a stated account that
the records do not support, a pattern that the period breaks. Produce
`contradiction`.

*Requires:* the claim set. *Guard:* none.

### S5 — Assess

State what the evidence supports as a confidence, with the basis, and state
the level at which the recorded gaps cap it. A decisive gap that blocks the
conclusion caps the assessment at `low` or `insufficient_information`; a
partial evidence set caps it at `moderate`. Produce `risk_assessment`.

*Requires:* `gap_list`. *Guard:* `POL-ASSESSMENT-NEEDS-INDICATOR`.

### S6 — Recommend

Say what should happen next, anchored to the claim that motivates it: obtain
a specific record, examine a specific counterparty, escalate, or close the
line of inquiry. Each recommendation names the claim it explains. Produce
`recommendation`.

*Requires:* the claim set. *Guard:* `POL-RECOMMENDATION-NEEDS-BASIS`.

### S7 — Escalate

Name the decision the human still owns: what the case does next, by whom,
and what would change the answer. Produce `escalation`.

*Requires:* the claim set. *Guard:* none.

## Output

A `case_summary` artifact conforming to `fincrime/finding/1.0.0`:

- `artifact.artifact_type` = `case_summary`
- `claims` — the required claims are `frame`, `evidence_inventory`,
  `timeline`, `observation`, `gaps`, `risk_assessment` and `recommendation`;
  `hypothesis`, `contradiction`, `indicator` and `escalation` are optional
- `timeline` — an ordered array of entries, each with a `timestamp`, a
  `description`, and at least one evidence reference; **no entry without a
  resolving reference**, and no entry that asserts something the reference
  does not carry
- `human_decision_required` — always at least one: what the case does next
- `provenance` — the model's identity, the prompt hash, the evidence-set
  hash, the knowledge pack version and its `as_of`, and the run identifier

**The summary is not a conclusion.** The skill must not produce a `decision`
claim, and it must not raise the confidence of the material it summarizes.

## Epistemic drift

Epistemic drift is the failure this skill exists to prevent: the summary
says more than the evidence behind it says. It takes four forms, and each
has a rule.

| Drift | Rule |
|---|---|
| **A claim is carried forward more strongly than it was made.** | A claim brought from an earlier artifact is re-grounded against this artifact's evidence, or marked `carried_forward_from` with the earlier claim id. Its confidence is never raised on the way in. |
| **A pattern becomes a fact.** | A pattern over many transactions is an `observation`, not a `fact`, and a `fact` only where one record is read directly. |
| **An absence becomes a finding.** | A record that is not in the set is a gap, not evidence that the activity did not happen. |
| **A summary becomes a narrative.** | The summary says what the records show and where they are silent. It does not narrate intent, and it does not use a culprit's or a victim's arc. |

## Escalation

Report a finding of severity `error` and refuse to sign off when:

- any timeline entry carries no evidence reference, or a reference that does
  not resolve;
- any `observation` or `indicator` claim carries a reference that does not
  resolve, or no reference at all;
- a claim carried forward from an earlier artifact is stated more confidently
  than it was made there, and is not marked `carried_forward_from`;
- an `adverse_reading` hypothesis stands without a `benign_reading` to
  compete with it;
- an `indicator` claim names an indicator that is not in the declared pack;
- the risk assessment states `high` confidence while a decisive gap blocks
  the conclusion;
- a cited knowledge record has expired;
- the artifact states or implies that the subject is suspicious, that the
  activity is laundering, that a report is required, or that the subject is
  a criminal.

## Guardrails

- **Never** state that the subject is suspicious, that the activity is
  laundering, or that a report is required. Report what the records do and
  do not support.
- **Never** assert criminality of the subject.
  `POL-NO-CRIMINALITY-CLAIMS` is a hard control.
- **Never** write a timeline entry without a resolving reference. An
  unanchored event is the defect this skill is defined by.
- **Never** introduce an assertion the evidence does not carry, including
  the "obvious" ones — that an account is controlled by the subject, that two
  counterparties are related, that a payment was for an illicit purpose.
- **Never** raise the confidence of the material being summarized.
- **Never** treat the absence of a record as evidence of absence.
- **Never** decide. The skill produces the summary; a human decides what the
  case does next.

## Provenance

Every case summary records the model's identity and version, the hash of the
prompt, the hash of the evidence set, the knowledge pack version and its
`as_of`, the policy set version, and the run identifier. Every summary
statement is a claim the evidence set can be checked against.

## Evaluation

The case suite is at `evals/suites/case-summarize`. The Phase 3 bar is at
least 40 cases, at least 40% of them benign, adversarial, missing-data or
contradictory, at least 15% carrying a negative expectation, and at least
one benign case for every typology the skill names. The suite must include
multi-account and multi-counterparty cases, and cases where the timeline
cannot be completed.

The `investigation-qa` skill reviews the summaries this skill produces:
seeded defects — an unanchored timeline entry, an unsourced assertion, an
overstated conclusion — must be found, and a conformant summary must produce
no false defect.
