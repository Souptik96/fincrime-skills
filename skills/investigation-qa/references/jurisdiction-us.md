# Jurisdiction note — United States

The `investigation-qa` skill reviews an artifact. It does not decide, does not
file, and does not rewrite. Its jurisdiction scope is the **United States**,
and this note says what that means in practice.

## What the skill relies on here

- **The Finding Contract** `fincrime/finding/1.0.0`, which is jurisdiction-
  agnostic: it constrains how a claim is made, not what the law requires.
- **The currency transaction reporting threshold**, supplied as a policy input
  by the evidence set, never hard-coded here. The value in force for the
  monitoring window is the one that applies.
- **The knowledge pack** for the indicators, typologies and request-catalogue
  entries the review cites. Each record carries its own `jurisdictions`, its
  own sources, and its own dates.

## What it does not cover

- **SAR filing and drafting.** The skill produces a defect list, never a
  filing, and never a document that reads as one.
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
