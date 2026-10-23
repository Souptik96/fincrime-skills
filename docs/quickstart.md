# 60-Second Quickstart Guide

Get up and running with **FinCrime Skills** in under 60 seconds.

FinCrime Skills is an open framework of production-grade agent skills and machine-checkable **Finding Contracts** for financial crime compliance (AML, CFT, Sanctions, SAR/STR filings). It replaces unconstrained LLM hallucinations with deterministic, evidence-grounded findings compliant with FinCEN, BSA, FATF, and SR 11-7 standards.

---

## ⚡ The 60-Second Onboarding

Run the complete offline demo in your terminal:

```bash
make demo
```

Or invoke the CLI directly:

```bash
fincrime demo
```

This runs entirely offline in ~15ms, requires zero API keys, opens zero network sockets, and compares an unconstrained LLM response against a canonical **Governed Finding Contract**.

### Terminal Scorecard Output

```text
================================================================================
  FINCRIME AGENT GOVERNANCE BENCHMARK: RAW PROSE vs FINDING CONTRACT
================================================================================
  Scenario: TYP-STRUCTURING-SMURFING (Rapid structured cash deposits)
  Benign Alternative: BENIGN-STRUCTURING-COMMERCIAL-CASH (Daily retailer cash)
--------------------------------------------------------------------------------
  METRIC                         RAW LLM PROSE        FINDING CONTRACT
--------------------------------------------------------------------------------
  RFC 6901 JSON Pointers         0                    4 [PASS]
  Evidence Attribution (EAA)     0.0% [FAIL]          100.0% [PASS]
  Unsupported Claim Rate (UCR)   100.0% [FAIL]        0.0% [PASS]
  Benign Twin Hypothesis         Absent [FAIL]        Evaluated & Refuted [PASS]
  Deterministic Audit Trail      None [FAIL]          SHA-256 Checksummed [PASS]
  Machine Schema Validation      None [FAIL]          JSON-Schema Valid [PASS]
  Regulatory Rule Compliance     0/13 [FAIL]          13/13 Enforced [PASS]
================================================================================
```

---

## 🛠️ The 5 Core Commands

### 1. Educational Rule Diagnostics: `fincrime explain`

Get deep regulatory rationales (BSA, FinCEN, FFIEC, Federal Reserve SR 11-7), failing vs compliant JSON payloads, and remediation instructions for any compliance rule:

```bash
fincrime explain R-3b
```

You can also explain findings directly on an artifact:

```bash
fincrime explain --artifact skills/alert-triage/examples/golden_triage_report.json --evidence-set skills/alert-triage/examples/golden_evidence_set.json
```

Or list all supported regulatory rules:

```bash
fincrime explain --list
```

### 2. Knowledge Discovery: `fincrime knowledge`

Explore the 12 core AML/CFT typologies and their benign twin lookalikes:

```bash
fincrime knowledge typologies
```

Inspect specific indicators and typologies in installed packs:

```bash
fincrime knowledge inspect --indicator IND-CASH-INTENSITY-PROFILE-MISMATCH
```

List all registered knowledge records across all packs:

```bash
fincrime knowledge list
```

### 3. Policy Rule Checking: `fincrime policy`

Inspect compliance policy sets and audit finding artifacts against organizational thresholds:

```bash
fincrime policy list
```

Check an artifact against a policy set:

```bash
fincrime policy check --set policies/default/policy-set.json --artifact skills/alert-triage/examples/golden_triage_report.json
```

Export a policy set:

```bash
fincrime policy export --set policies/default/policy-set.json
```

### 4. Contract Validation: `fincrime validate`

Validate skill packages, evaluation case suites, knowledge packs, or finding artifacts:

```bash
fincrime validate skills/alert-triage
```

Validate a full evaluation case suite:

```bash
fincrime validate skills/alert-triage/evals/suites/alert-triage
```

Validate a finding artifact with evidence grounding:

```bash
fincrime validate skills/alert-triage/examples/golden_triage_report.json --evidence-set skills/alert-triage/examples/golden_evidence_set.json
```

### 5. Offline Replay Evaluation & Attribution Gates: `fincrime eval`

Evaluate skill runs against synthetic benchmark suites with deterministic gates:

```bash
fincrime eval --skill alert-triage --replay --gates
```

Run evaluations across all 6 skills:

```bash
fincrime eval --skill all --replay --gates
```

---

## 🐍 Python SDK Integration

FinCrime Core has **zero external dependencies** (ADR-0002) and runs on standard-library Python:

```python
import json
from pathlib import Path
from fincrime_core import Validator, load_policy_set, PolicyEvaluator
from fincrime_core.contract.loader import parse_finding

# Locate sample artifact and evidence set
root = Path(".").resolve()
if not (root / "skills").is_dir():
    root = root.parent

art_path = root / "skills/alert-triage/examples/golden_triage_report.json"
ev_path = root / "skills/alert-triage/examples/golden_evidence_set.json"
artifact = json.loads(art_path.read_text(encoding="utf-8"))
evidence_set = json.loads(ev_path.read_text(encoding="utf-8"))

# Validate RFC 6901 JSON pointer citations and Finding Contract schema
validator = Validator(evidence_set=evidence_set)
result = validator.validate(artifact)
assert result.valid, f"Validation failed: {result.errors}"
assert result.evidence_attribution_accuracy == 1.0
assert result.unsupported_claim_rate == 0.0

# Evaluate organizational compliance policy
policy_set = load_policy_set(root / "policies/default/policy-set.json")
finding = parse_finding(artifact)
evaluator = PolicyEvaluator(policy_set.rules)
violations = evaluator.evaluate(finding)
assert len(violations) == 0, f"Policy violations: {violations}"
print(f"Compliance Verified: EAA={result.evidence_attribution_accuracy:.1%}")
```

---

## 🛡️ Core Architecture & Invariants

1. **Zero-Dependency Runtime (ADR-0002)**: Both `fincrime-core` and `fincrime-cli` run on standard Python 3.10+ with zero third-party packages.
2. **Air-Gap Safety (ADR-0003)**: Sockets and external network calls are forbidden. Zero risk of data exfiltration.
3. **Zero-PII Guarantee (ADR-0007)**: Synthetic datasets use mathematically generated SSNs, routing numbers, and deterministic names. Zero real customer data.
4. **Attribution Gates (ADR-0008)**: Every claim must resolve via an RFC 6901 JSON pointer to a documented record in the evidence set. Unattributed assertions are hard errors.
