---
name: alert-triage
description: >-
  Take a raw alert and the transaction and customer evidence behind it, and
  produce a triage finding that names the indicators that match, states a
  benign reading beside every adverse reading, and records the gaps that
  block a conclusion. Use when an alert has to be assessed for escalation or
  closure by a human, never when it has to be detected. Produces a
  `triage_report` conforming to `fincrime/finding/1.0.0`.
license: Apache-2.0
metadata:
  fincrime_version: "1.0.0"
  contract_version: "fincrime/finding/1.0.0"
  knowledge_pack: "core-2026-10"
  category: "fincrime"
  jurisdiction: "US"
  compliance: "BSA/AML"
  risk_tier: "medium"
  domain: "triage"
  related_skills: "case-summarize,evidence-request,investigation-qa"
---

# Alert Triage

> ⚠️ This skill **assesses** an alert. It never closes one, never escalates
> one on its own, never files, and never reaches a conclusion about a
> customer. It produces a triage finding that a human disposes of.
> Jurisdiction scope: **United States**. See `references/jurisdiction-us.md`.

## When to use

- A monitoring alert has fired and a human needs a structured assessment of
  what the evidence behind it does and does not support.
- The question is "is there anything here worth a person's time, and what
  would we need to know to answer it properly".
- A case is opening and the first artifact needs to be an evidence-grounded
  triage, not an opinion.
- A reviewer has to be able to see why an alert was escalated or why it was
  not, with the evidence that says so.

## When NOT to use

- To detect anything. Detection is a monitoring system's job. This skill
  structures what an analyst has already been given.
- To write the case narrative or the investigative summary. Use
  `case-summarize` once the case is open.
- To decide what happens to the customer, or to make any disposition at all.
  That decision is never this skill's to make.
- To draft a suspicious activity report. Use `sar-narrative-draft`, and note
  that the report is a human's filing, not an agent's.
- To request missing records. Use `evidence-request`, which works from the
  gap list this skill produces.

## Required inputs

| Input | Description |
|---|---|
| `alert` | The raw alert that opened the review: what was detected, when, and against which account or subject. |
| `evidence_set` | The closed world: every transaction, account, customer and document record the triage may cite. |
| `threshold_policy` | The currency transaction reporting threshold in force for the monitoring window, and the date it changed. A policy input, never a value written into this skill. |

## Optional inputs

| Input | Description |
|---|---|
| `knowledge_index` | The knowledge pack used to resolve indicator ids, their benign explanations, their sources and their dates. |
| `policy_rules` | The firm's deterministic rules, used to check enforceable controls. |
| `prior_findings` | Earlier triage or case artifacts for the same subject, where they exist. |

## Preconditions

| ID | Check | On failure | Message |
|---|---|---|---|
| PC-1 | The alert and the evidence set are supplied | `stop` | There is nothing to triage without the alert and the evidence behind it. |
| PC-2 | The evidence set is closed and every source carries a stable source id | `stop` | Evidence attribution cannot be checked against an open or unaddressable evidence set. |
| PC-3 | The reporting threshold in force for the monitoring window is supplied as a policy input | `stop` | A threshold written into the skill would be a stale claim. Supply the value in force for the window. |
| PC-4 | The declared knowledge pack is resolvable | `annotate` | Indicator existence and freshness cannot be verified; disclose it. |

## Procedure

Follow the stage pattern S0–S7. Each stage states what it produces and what it
requires. The order is the control: the evidence inventory is built before
anything is asserted, because a claim made before the analyst knows what
evidence exists is a claim about a world the analyst has not seen.

### S0 — Frame

Establish what is under assessment: the alert, the subject scope, the
jurisdiction, the monitoring window, the threshold in force for that window,
and the evidence set as the closed world. Produce `frame`.

*Requires:* nothing. *Guard:* none.

### S1 — Ground

Enumerate the evidence before asserting anything: what is present, what is
absent, and what each item is. Record the gaps that matter, marking the ones
that would be decisive against a conclusion. Produce `evidence_inventory` and
`gaps`.

*Requires:* the evidence set. *Guard:* `POL-EVIDENCE-INVENTORY-FIRST`.

### S2 — Extract

For every candidate pattern, resolve its evidence references against the
evidence set and check that the resolved value supports the statement, then
match the pattern against the named indicators in `core-2026-10`. An
indicator claim carries the indicator id and the records that evidence it.
Produce `observation` and `indicator`.

*Requires:* `evidence_inventory`. *Guard:* `POL-INDICATOR-REQUIRES-INDICATOR-ID`.

#### The indicators this skill matches

The three indicators below are the ones the skill cites from `core-2026-10`.
Each is a **measured pattern**, not a conclusion about intent, and each
carries the benign explanations that a triage must consider before it records
an adverse reading.

- **`IND-STRUCT-THRESHOLD-PROXIMITY`** — cash deposits clustered immediately
  below the currency transaction reporting threshold in force for the window.
  *Benign readings:* a cash-intensive legitimate business whose daily takings
  happen to fall below the threshold; deposits split across branches for
  operational reasons such as a branch's daily cash limit; seasonal or
  end-of-week takings that cluster by coincidence; a recently formed business
  whose declared cash intensity has not caught up with its takings.
- **`IND-FAST-MOVEMENT-PASS-THROUGH`** — credits followed by debits of a
  similar or greater amount within a short window, leaving little balance and
  little time for the funds to be used in the account's apparent line of
  business. *Benign readings:* a payment processor or marketplace settlement
  account that receives and pays out on the same day by design; a payroll
  account funded and disbursed in the same window; a professional escrow or
  clearing account whose stated function is to pass funds through; a
  commercial account that sweeps surplus to treasury at the end of each day.
- **`IND-ROUND-AMOUNT-DEPOSIT-CLUSTER`** — cash or cheque deposits in exact
  multiples of a round figure, clustered in time and materially larger than
  the amounts usually seen on the account. *Benign readings:* a business that
  prices in round figures; a customer paying rent, tuition or an instalment
  in a round amount agreed in advance; a cash-heavy retail account whose
  daily takings settle at round figures; a teller machine crediting change in
  a round amount.

### S3 — Hypothesize

Form the readings the evidence supports. Every adverse reading carries a
competing benign reading, and every hypothesis carries a falsifier: the
observation that would settle it. Produce `hypothesis`.

*Requires:* the claim set. *Guard:* `POL-BENIGN-HYPOTHESIS-REQUIRED`.

### S4 — Contrast

Surface the contradictions: the customer's stated account against the account
records, the alert narrative against the transactions, one counterparty's
description against another's. Produce `contradiction`.

*Requires:* the claim set. *Guard:* none.

### S5 — Assess

State what the evidence supports as a confidence, with the basis, and state
the level at which the recorded gaps cap it. A decisive gap that blocks the
conclusion caps the assessment at `low` or `insufficient_information`; a
partial evidence set caps it at `moderate`. Produce `risk_assessment`.

*Requires:* `gap_list`. *Guard:* `POL-ASSESSMENT-NEEDS-INDICATOR`.

### S6 — Recommend

Say what should happen next, anchored to the claim that motivates it:
escalate for human review, obtain a specific record, or monitor. Each
recommendation names the claim it explains. Produce `recommendation`.

*Requires:* the claim set. *Guard:* `POL-RECOMMENDATION-NEEDS-BASIS`.

### S7 — Escalate

Name the decision the human still owns: whether the alert is escalated or
closed, by whom, and what would change the answer. Produce `escalation`.

*Requires:* the claim set. *Guard:* none.

## Output

A `triage_report` artifact conforming to `fincrime/finding/1.0.0`:

- `artifact.artifact_type` = `triage_report`
- `claims` — the required claims are `frame`, `evidence_inventory`, `gaps`,
  `observation`, `indicator`, `hypothesis`, `risk_assessment` and
  `recommendation`; `contradiction` and `escalation` are optional
- `hypothesis` claims carry `epistemic_type`, and an `adverse_reading` is
  never present without a competing `benign_reading` in the same artifact
- `indicator` claims carry `indicator_ids` drawn from `core-2026-10`
- `human_decision_required` — always at least one: whether to escalate or
  close the alert
- `provenance` — the model's identity, the prompt hash, the evidence-set
  hash, the knowledge pack version and its `as_of`, and the run identifier

**The triage report is not a disposition.** The skill must not produce a
`decision` claim. It produces the assessment; a human disposes of the alert.

## Escalation

Report a finding of severity `error` and refuse to sign off when:

- any `observation` or `indicator` claim carries an evidence reference that
  does not resolve, or no reference at all;
- an `adverse_reading` hypothesis stands without a `benign_reading` to
  compete with it;
- an `indicator` claim names an indicator that is not in the declared pack,
  or names no indicator at all;
- a reporting threshold is asserted that was not supplied as a policy input,
  or whose date of effect is not stated;
- the risk assessment states `high` confidence while a decisive gap blocks
  the conclusion, or states a level above the ceiling the evidence allows;
- a cited knowledge record has expired (an `error` when new work depends on
  it, a `warn` on an unchanged released artifact);
- the artifact states or implies that the customer is suspicious, that the
  activity is laundering, that a report is required, or that the subject is
  a criminal.

## Guardrails

- **Never** state that the customer is suspicious, that the activity is
  laundering, or that a report is required. Report what the evidence does
  and does not support.
- **Never** assert criminality of the subject. `POL-NO-CRIMINALITY-CLAIMS`
  is a hard control, not a style preference.
- **Never** use an indicator as a conclusion. An indicator is a named pattern
  from the pack; it says what was measured, never what it means.
- **Never** present the benign reading as a formality. It must be a real
  competitor, with its own falsifier, and it must be the reading the evidence
  would support if the customer is ordinary.
- **Never** hard-code the reporting threshold. The value in force for the
  monitoring window is a policy input.
- **Never** cite an indicator without the records that evidence it, and never
  cite a record without the pointer to the specific value.
- **Never** treat the absence of a record as evidence of absence. An absent
  record is a gap.
- **Never** decide. The skill produces an assessment; the human disposes of
  the alert.

## Provenance

Every triage report records the model's identity and version, the hash of the
prompt, the hash of the evidence set, the knowledge pack version and its
`as_of`, the policy set version, and the run identifier. Nothing in the
report is a claim the evidence set cannot be checked against.

## Evaluation

The case suite is at `evals/suites/alert-triage`. The Phase 3 bar is at
least 40 cases, at least 40% of them benign, adversarial, missing-data or
contradictory, at least 15% carrying a negative expectation, and at least
one benign case for every typology the skill names. A suite of agreeable
cases measures nothing.

The `investigation-qa` skill reviews the reports this skill produces: seeded
defects must be found, and a conformant report must produce no false defect.
