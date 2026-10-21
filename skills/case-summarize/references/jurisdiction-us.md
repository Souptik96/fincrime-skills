# Jurisdiction note — United States

The `case-summarize` skill summarizes what the evidence records. It does not
decide, does not file, and does not close a case. Its jurisdiction scope is
the **United States**, and this note says what that means in practice.

## What the skill relies on here

- **The Finding Contract** `fincrime/finding/1.0.0`, which is
  jurisdiction-agnostic: it constrains how a claim is made, not what the law
  requires.
- **The evidence reference grammar** — an RFC 6901 pointer per reference.
  A transaction is cited as `txn:<id>#<pointer>` and a document as
  `doc:<id>#<pointer>`, and the pointer must resolve to the value the
  timeline entry describes.
- **The knowledge pack** `core-2026-10`, for the indicators, typologies and
  regulatory records the summary cites. Each record carries its own
  `jurisdictions`, its own sources, and its own dates. The records this
  skill relies on are:
  - `IND-MULTI-ACCOUNT-AGGREGATION`, `IND-FUNNEL-ACCOUNT-AGGREGATION`,
    `IND-CIRCULAR-TRANSFER-CHAIN`, `IND-THIRD-PARTY-TRANSFER-CHAIN` and
    `IND-COMMON-OWNERSHIP-SHELL-CHAIN`, each with the benign explanations a
    summary has to carry with it;
  - `TYP-STRUCTURING-SMURFING`, `TYP-MULE-ACCOUNT-NETWORK`,
    `TYP-ACCOUNT-TAKEOVER-LAUNDERING`, `TYP-SHELL-COMPANY-LAYERING` and
    `TYP-TRADE-BASED-MONEY-LAUNDERING` for the typologies the summary may
    name;
  - `REG-TRANSFER-1010-410F` and `REG-TRAVEL-RULE-1010-410E` for the
    transfer-recordkeeping and information-accompanying context behind a
    multi-party movement of funds.

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
