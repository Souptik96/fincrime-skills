# fincrime-core

The **Evidence-Linked Finding (ELF)** contract, its deterministic validator, the
policy evaluator, and the knowledge engine.

This package is the trust boundary of the FinCrime Skills project. It is
**dependency-free** and has **no network capability** — see
[ADR-0002](../../docs/adr/0002-zero-dependency-core.md).

## Install

```bash
pip install fincrime-core
```

The core has zero required runtime dependencies. It installs and runs in an
air-gapped environment with no package-index access.

## Use

```python
from fincrime_core import Validator, EnforcementContext

validator = Validator(evidence_set=evidence_set)
result = validator.validate(artifact)

if not result.valid:
    for defect in result.errors:
        print(f"{defect.code}: {defect.message}")

print(result.evidence_attribution_accuracy)   # deterministic
print(result.unsupported_claim_rate)          # deterministic
```

## What it guarantees

| Property | Mechanism |
|---|---|
| A factual claim cannot exist without evidence | Schema `if`/`then` on the claim class |
| Evidence attribution is measurable, not judged | RFC 6901 resolution over a closed world |
| A hypothesis cannot assert criminality alone | `epistemic_type` pairing: an `adverse_reading` requires a `benign_reading` |
| A decision must be attributable | `decided_by` is required for the `decision` class |
| Stale regulatory content is disclosed | Dated knowledge records with graded expiry enforcement |
| The artifact is auditable | Canonical hashing of the evidence set and the prompt |

## Contracts

The normative definitions live in [`contracts/`](../../contracts) and are
versioned independently of this package. The Finding Contract is
`fincrime/finding/1.0.0`.

## Licence

Apache-2.0.
