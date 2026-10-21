# Jurisdiction note — United States

The `evidence-request` skill drafts information requests. It does not issue
one, does not contact a customer or a third party, and does not dispose of a
case. Its jurisdiction scope is the **United States**, and this note says what
that means in practice.

## What the skill relies on here

- **The Finding Contract** `fincrime/finding/1.0.0`, which is
  jurisdiction-agnostic: it constrains how a claim is made, not what the law
  requires.
- **The request catalogue** in the knowledge pack `core-2026-10`. Every
  request this skill drafts is anchored to a catalogue record, and each record
  states what it establishes and what it does not. The records cited are:
  - `REQ-BANK-STATEMENTS-12M`, `REQ-POS-SETTLEMENT-BATCH`,
    `REQ-ATM-TRANSACTION-LOG` for the account, card and terminal record;
  - `REQ-SOURCE-OF-WEALTH`, `REQ-UBO-REGISTRY-PROOF`,
    `REQ-UBO-CHART-SIGNED-DECLARATION`, `REQ-CORPORATE-REGISTRY-EXTRACT`
    for ownership and the entity behind it;
  - `REQ-COUNTERPARTY-BANK-STATEMENTS`, `REQ-INVOICE-LEDGER` and
    `REQ-COMMERCIAL-CONTRACTS` for the onward movement of funds and the
    trade behind it.
- **The regulatory context** `REG-CDD-1010-230` for the risk-based
  customer due diligence the records support,
  `REG-BENEFICIAL-OWNERSHIP-RULE` for the ownership records, and
  `REG-RECORD-RETENTION-1010-430` for the periods that have to be covered.

## What it does not cover

- **Issuing anything.** No request is sent, no customer or third party is
  contacted, and no record is fetched. A human approves and issues.
- **The reporting decision.** Whether a report is required, and when, is a
  decision the skill does not make. The dossier names the decision the human
  still owns.
- **Lawful-route determinations.** Whether the firm may lawfully obtain a
  record is a legal question. The skill flags the request for a human rather
  than drafting it as though the route were available.
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
