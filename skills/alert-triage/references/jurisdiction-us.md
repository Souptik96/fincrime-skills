# Jurisdiction note — United States

The `alert-triage` skill assesses an alert. It does not close it, does not
file, and does not decide anything about a customer. Its jurisdiction scope
is the **United States**, and this note says what that means in practice.

## What the skill relies on here

- **The Finding Contract** `fincrime/finding/1.0.0`, which is
  jurisdiction-agnostic: it constrains how a claim is made, not what the law
  requires.
- **The currency transaction reporting threshold**, supplied as a policy
  input by the evidence set and never hard-coded here. The value in force for
  the monitoring window is the one that applies, and the date it changed is
  part of the claim.
- **The knowledge pack** `core-2026-10`, for the indicators, typologies and
  regulatory records the triage cites. Each record carries its own
  `jurisdictions`, its own sources, and its own dates. The records this
  skill relies on are:
  - `IND-STRUCT-THRESHOLD-PROXIMITY`, `IND-FAST-MOVEMENT-PASS-THROUGH` and
    `IND-ROUND-AMOUNT-DEPOSIT-CLUSTER`, each with the benign explanations
    that a triage must consider before recording an adverse reading;
  - `TYP-STRUCTURING-SMURFING`, `TYP-MULE-ACCOUNT-NETWORK`,
    `TYP-ACCOUNT-TAKEOVER-LAUNDERING` and `TYP-ELDER-FINANCIAL-EXPLOITATION`
    for the typologies the triage may name;
  - `REG-STRUCTURING-1010-100` and `REG-CTR-1010-311` for the reporting and
    aggregation context behind a threshold-proximity finding.

## What it does not cover

- **The reporting decision.** Whether a report is required, and when, is a
  decision the skill does not make. It records what the evidence supports
  and names the decision the human still owns.
- **Filing.** No SAR, no CTR, no document that reads as one.
- **Sanctions and OFAC screening.** No sanctions list, no screening, no match
  handling.
- **Customer risk ratings.** No numeric risk rating is produced anywhere in
  this project.
- **Multi-jurisdiction analysis.** An artifact that declares a jurisdiction
  outside the scope the skill permits is rejected.
- **Tax, accounting and legal conclusions.**

## The project-wide statement

See [`docs/jurisdiction-support.md`](../../../docs/jurisdiction-support.md)
for what is supported in the United States, and what adding a jurisdiction
requires.
