---
name: sanctions-alert
description: >-
  Assess a sanctions or watchlist screening alert against customer identity and
  transaction evidence, evaluating match criteria, false-positive vs true-hit
  hypotheses, and documentation gaps. Use when a sanctions screening match
  requires structured assessment before human disposition; never use to
  unilaterally block, unblock, or freeze assets. Produces a `sanctions_assessment`
  conforming to `fincrime/finding/1.0.0`.
license: Apache-2.0
metadata:
  fincrime_version: "1.0.0"
  contract_version: "fincrime/finding/1.0.0"
  knowledge_pack: "core-2026-10"
  category: "fincrime"
  jurisdiction: "US"
  compliance: "BSA/AML"
  risk_tier: "high"
  domain: "sanctions"
  related_skills: "alert-triage,case-summarize,evidence-request,investigation-qa,sar-narrative-draft"
---

# Sanctions Alert Assessment

> ⚠️ This skill **assesses** a sanctions screening alert. It evaluates match
> quality, adverse vs benign hypotheses (e.g. name similarity vs distinct DOB/nationality),
> and records information gaps. It **never** unilaterally blocks funds, unblocks
> transactions, freezes assets, or makes legal determinations. All dispositions
> and escalation decisions require human sign-off.
> Jurisdiction scope: **United States** (OFAC 31 CFR 501, 515, 560).

## When to use

- A sanctions or screening alert fires against an originator, beneficiary, customer,
  vessel, aircraft, or crypto address and requires structured investigation.
- An analyst must determine whether a hit represents a true match to an OFAC SDN /
  Sectoral sanctions entry or a false positive due to phonetic / common-name overlap.
- An evidence-grounded assessment is required before escalating to a Sanctions Officer
  for block or rejection determination.
- Gaps in identity, beneficial ownership, or transshipment bills of lading must be
  catalogued before an unblock recommendation can be proposed.

## When NOT to use

- To execute screening or string matching. Fuzzy matching and watchlist ingestion
  are the screening engine's responsibility.
- To execute blocking, asset freezing, or transaction release. Actions of legal
  consequence are strictly reserved for human compliance officers.
- To draft a SAR narrative for money laundering activity unrelated to sanctions.
  Use `sar-narrative-draft`.
- To replace general AML transaction monitoring alert triage. Use `alert-triage`.

## Required inputs

| Input | Description |
|---|---|
| `alert` | The raw screening alert containing match criteria, scored attributes, and designated target identifier. |
| `evidence_set` | The closed world of customer identity records, transactions, invoices, and screening hit details. |
| `screening_policy` | The declared sanctions policy and threshold settings in force for the screening window. |

## Optional inputs

| Input | Description |
|---|---|
| `knowledge_index` | The declared knowledge pack used to resolve indicators and regulatory citations. |
| `policy_rules` | Deterministic firm policies governing sanctions reviews and false-positive criteria. |
| `prior_findings` | Prior screening or disposition artifacts for the subject. |

## Preconditions

| ID | Check | On failure | Message |
|---|---|---|---|
| PC-1 | The alert and evidence set are supplied | `stop` | Cannot evaluate sanctions screening alert without match alert and evidence set. |
| PC-2 | The evidence set is closed with stable source IDs | `stop` | Evidence attribution requires an addressable, closed evidence set. |
| PC-3 | The declared knowledge pack is resolvable | `annotate` | Regulatory records and typology grounding cannot be verified; disclose it. |

## Procedure

1. **S0 Frame**: Establish the assessment frame, subject scope, and jurisdiction context.
2. **S1 Ground**: Build the evidence inventory from closed sources and identify missing records.
3. **S2 Match Analysis**: Compare matched attributes (name, DOB, address, nationality, IDs) against designated list entry.
4. **S3 Epistemic Hypotheses**: Formulate at least one adverse hypothesis (true SDN match) and at least one benign hypothesis (false positive due to homonym, distinct citizenship, or general license).
5. **S4 Risk Assessment**: Evaluate likelihood based on matching score and available corroborating evidence.
6. **S5 Recommendation & Decision Request**: Formulate a recommendation (e.g. escalate for human block/release review) with mandatory human sign-off request.

## Output

Emits a canonical `sanctions_assessment` finding conforming to `fincrime/finding/1.0.0`.
- Requires RFC 6901 evidence references for all facts, observations, and indicators.
- Prohibits unilateral `decision` claims.
- Requires `human_decision_required` block for any recommendation.
