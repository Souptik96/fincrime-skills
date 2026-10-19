# Example 01 — Alert triage on a cash-structuring alert

This is the flagship example. It is the difference between a prompt pack and a
contract, shown on one case.

Everything here is **synthetic**, generated from a recorded seed. No customer
data is involved, and none is required to reproduce it.

## The case

A US bank's transaction-monitoring engine fires its cash-structuring scenario
on a customer with a three-year relationship who runs a neighbourhood
restaurant.

| | |
|---|---|
| Alert | `9930`, rule `SC-TM-CASH-STRUCTURING`, window 2026-03-01 → 2026-03-12 |
| Subject | `5512`, individual, small-business segment, KYC current |
| Declared profile | Neighbourhood restaurant, daily card and cash takings, ~$42,000/month |
| Activity | 3 cash deposits of $9,400 / $9,700 / $9,600, at 3 different branches, 4–7 March |
| Missing | Payroll records, point-of-sale settlement records, source-of-funds documentation |
| Present | The KYC docket, which records the business registration but nothing about the cash |

## What an agent produces with no skill

> *"The customer deposited $9,400–$9,800 in cash at four branches in nine days,
> which is consistent with structuring to evade reporting requirements. The
> account should be escalated and a SAR filed."*

Defects found:

| Defect | Severity | Why |
|---|---|---|
| `unsupported_claim` | error | No evidence references at all. Nothing in the narrative can be checked. |
| `missing_benign_reading` | error | One hypothesis. A cash-intensive restaurant is a live alternative and it was never considered. |
| `missing_gap` | error | The decisive evidence — payroll and settlement records — is absent, and the narrative does not say so. |
| `recommendation_without_basis` | error | "A SAR should be filed" cites nothing. |
| `escalation_missed` | error | No human decision is named. The narrative itself makes the call. |
| `unsupported_claim` | warn | "structuring to evade reporting requirements" asserts intent, which no evidence supports. |

## What the same model produces with the skill

```jsonc
{
  "id": "C-001",
  "class": "fact",
  "statement": "Three cash deposits totalling $28,700 were made between 2026-03-04 and 2026-03-07, at three different branches.",
  "evidence_refs": ["txn:8841#/amount", "txn:8842#/amount", "txn:8843#/amount"],
  "confidence": { "level": "high", "basis": "Read directly from the transaction records." }
}
```

```jsonc
{
  "id": "C-002",
  "class": "indicator",
  "statement": "Cash deposits cluster immediately below the $10,000 currency transaction reporting threshold, across dispersed branches.",
  "evidence_refs": ["txn:8841#/amount", "txn:8842#/amount", "txn:8843#/amount"],
  "indicator_ids": ["IND-STRUCT-THRESHOLD-PROXIMITY"],
  "policy_ids": ["POL-STRUCT-THRESHOLD-PROXIMITY"],
  "confidence": { "level": "moderate", "basis": "Threshold proximity is measured; intent is not established." }
}
```

```jsonc
{
  "id": "C-003",
  "class": "hypothesis",
  "epistemic_type": "adverse_reading",
  "statement": "The cash activity may be structured to avoid the reporting threshold.",
  "evidence_refs": ["txn:8841#/amount"],
  "falsifier": "Payroll or point-of-sale settlement records showing the cash as genuine revenue.",
  "confidence": { "level": "low", "basis": "The decisive corroborating evidence is absent." }
}
```

```jsonc
{
  "id": "C-004",
  "class": "hypothesis",
  "epistemic_type": "benign_reading",
  "statement": "The cash activity may be ordinary revenue for a cash-intensive business.",
  "evidence_refs": ["txn:8841#/amount"],
  "falsifier": "Absence of payroll or point-of-sale settlement records supporting the declared business.",
  "confidence": { "level": "low", "basis": "The decisive corroborating evidence is absent." }
}
```

```jsonc
{
  "id": "C-006",
  "class": "recommendation",
  "statement": "Request source-of-funds documentation and six months of point-of-sale settlement records, then re-triage.",
  "evidence_refs": ["txn:8841#/amount"],
  "human_approval_required": true,
  "confidence": { "level": "moderate", "basis": "Follows the documented request catalogue." }
}
```

The full artifact is in [`artifact.json`](artifact.json). The evidence set is in
[`evidence-set.json`](evidence-set.json).

## Why this is better

The skilled output is **not more cautious prose**. It is a different kind of
object:

1. **Every factual claim is checkable.** `txn:8841#/amount` resolves to `9400`.
   A reviewer can verify each of the three references in seconds.
2. **The benign alternative is not optional.** `C-004` cannot be omitted without
   the artifact failing validation. This is structural — writing around a
   keyword filter does not work, because the requirement is a field, not a
   phrase.
3. **The missing evidence is named.** `G-01` records that payroll and settlement
   records are absent, and every downstream claim's confidence reflects it.
4. **The decision is left with a human.** `D-01` names the question and the
   role that owns it. The agent does not say "should be escalated"; it says
   "here is what would change the answer".
5. **No intent is asserted.** "Consistent with an indicator" is not the same
   claim as "structured to evade reporting", and only the first is supported.

## Reproducing it

```bash
pip install -e "packages/fincrime-core[dev]"
python -m pytest packages/fincrime-core/tests -q
```

The validator runs against the committed artifact in the test suite. To check it
yourself:

```python
import json
from fincrime_core import Validator

evidence_set = json.load(open("evidence-set.json"))
artifact = json.load(open("artifact.json"))

result = Validator(evidence_set=evidence_set).validate(artifact)
print(result.valid)                        # True
print(result.evidence_attribution_accuracy) # 1.0
print(result.unsupported_claim_rate)        # 0.0
```

## The metric difference

| Metric | No skill | With skill | Δ |
|---|---|---|---|
| Evidence attribution accuracy | 0.00 | 1.00 | +1.00 |
| Unsupported claim rate | 0.55 | 0.00 | −0.55 |
| Benign false-positive rate | 1.00 | 0.10 | −0.90 |
| Escalation accuracy | 0.50 | 0.90 | +0.40 |

Those figures are the *shape* of what the published conformance report will
contain. The actual numbers are produced by the evaluation harness against the
committed case suites, always reported as a delta against a no-skill baseline
([ADR-0007](../../../docs/adr/0007-no-skill-baseline.md)).
