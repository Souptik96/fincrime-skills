# The Compliance Officer's Guide to Claim Classes

> **Target Audience:** Chief Compliance Officers (CCOs), BSA/AML Officers, Model Risk Auditors (SR 11-7 / OCC 2011-12), and Regulatory Examiners (FinCEN, OCC, Federal Reserve, FDIC).  
> **Contract Version:** `fincrime/finding/1.0.0`  
> **Status:** Normative Supervisory Guide  

---

## 1. Executive Summary: Why Free-Text LLMs Fail Compliance

Traditional generative AI models deployed in financial crime compliance introduce severe regulatory vulnerabilities. When prompted without structural constraints, Large Language Models (LLMs) exhibit three fatal failure modes:

1. **Unsubstantiated Hallucination:** Fabricating transaction amounts, counterparty names, dates, or non-existent account relationships.
2. **Premature Legal Accusation (Culpability Drift):** Asserting criminal mens rea ("The subject intentionally structured deposits to evade CTR filing") without judicial authority or evidentiary proof.
3. **Confirmation Bias (Adverse Tunnel Vision):** Fixating exclusively on suspicious indicators while completely ignoring legitimate commercial explanations (e.g., seasonal retail cash flow, catering payroll, escrow disbursements).

In regulated institutions subject to the **Bank Secrecy Act (BSA)**, **FinCEN SAR Regulations (31 CFR § 1020.320)**, and the **Federal Reserve / OCC Supervisory Guidance on Model Risk Management (SR 11-7 / OCC Bulletin 2011-12)**, an ungrounded or accusatory LLM output cannot be defended during an examination.

The `fincrime-skills` architecture eliminates these risks at compile time and runtime. Rather than treating an LLM output as unconstrained prose, the system forces all model output into an **epistemic ontology of seven discrete claim classes**. Every single assertion emitted by an agent must be typed, structurally validated, and mathematically anchored to immutable records.

---

## 2. The Seven Claim Classes

The Finding Contract (`contracts/finding.schema.json`) defines seven mutually exclusive claim classes. An agent cannot invent a class, emit untyped assertions, or blur the boundary between observed fact and subjective hypothesis.

```text
               ┌────────────────────────────────────────────────────────┐
               │                THE SEVEN CLAIM CLASSES                 │
               └────────────────────────────────────────────────────────┘
                                            │
           ┌────────────────────────────────┴────────────────────────┐
           ▼                                                         ▼
   [EVIDENTIARY CORE]                                     [ANALYTICAL SYNTHESIS]
Mandatory RFC 6901 Pointer                                Epistemic Bounds & Guards
   ├── fact                                                  ├── hypothesis (Dual-Reading)
   ├── observation                                           ├── risk_assessment (Capped)
   └── indicator                                             ├── recommendation (Approval Req)
                                                             └── decision (Human Attribution)
```

### 2.1. `fact`
* **Definition:** A direct, verbatim extraction from an official record in the closed-world evidence set.
* **Requirements:** Mandatory RFC 6901 pointer (`requires_evidence = True`, Rule `R-1`, `R-1a`). Must reflect zero interpretation or extrapolation.
* **Compliant Example:** "Account #019283 was opened on 2024-03-15 with a stated occupation of 'Independent Florist'." (`txn:act-019283#/open_date`)
* **Prohibited Assertion:** "Account #019283 was opened as a front company for laundering." (Violates `fact` definition and Rule `R-6`).

### 2.2. `observation`
* **Definition:** A direct mathematical aggregation, count, velocity calculation, or chronological sequence computed exclusively from referenced facts.
* **Requirements:** Mandatory RFC 6901 pointer (`requires_evidence = True`, Rule `R-1`, `R-1a`). All underlying arithmetic must be reproducible from the cited data points.
* **Compliant Example:** "The subject conducted four cash deposits totaling $38,200 across three branch locations within a 72-hour window." (`txn:dep-1#/amount`, `txn:dep-2#/amount`, `txn:dep-3#/amount`, `txn:dep-4#/amount`)
* **Prohibited Assertion:** "The subject repeatedly structured funds." (Interpretation/culpability label; not an observation).

### 2.3. `indicator`
* **Definition:** A formal detection pattern matching an official typology cataloged in the active supervisory knowledge pack.
* **Requirements:** Mandatory RFC 6901 pointer (`requires_evidence = True`, Rule `R-1`) AND must cite an active `indicator_id` published in the firm's knowledge pack (`R-2`, `R-2b`).
* **Compliant Example:** "Cash velocity profile exhibits proximity to currency reporting thresholds." (`indicator_ids: ["IND-CASH-INTENSITY-PROFILE-MISMATCH"]`, `knowledge_ids: ["FIN-2023-A001"]`)
* **Prohibited Assertion:** Invented indicators or ad-hoc tags not registered in the immutable pack (`R-2` defect).

### 2.4. `hypothesis`
* **Definition:** A tentative, falsifiable explanatory model accounting for observed facts and indicators.
* **Requirements:**
  1. Mandatory `falsifier`: What specific missing evidence or counter-fact would disprove this hypothesis? (Rule `R-3`).
  2. Mandatory `epistemic_type`: Must be classified as `benign_reading`, `adverse_reading`, `data_gap`, or `other` (Rule `R-3a`).
  3. **Mandatory Dual-Reading Invariant:** An `adverse_reading` cannot stand alone; it fails validation unless balanced by an explicit, competing `benign_reading` (Rule `R-3b`).
  4. Explicit `competing_with` pointers linking alternative hypotheses (Rule `R-9`).

### 2.5. `risk_assessment`
* **Definition:** An evaluative judgment regarding institutional or regulatory exposure.
* **Requirements:**
  1. Must cite evidence or default to `insufficient_information` (Rule `R-4`).
  2. **Confidence Capping:** Confidence cannot be stated as `high` or `moderate` if decisive evidence gaps remain unclosed (Rule `R-11`), or if the overall evidence set is declared `partial` (Rule `R-8`).

### 2.6. `recommendation`
* **Definition:** An operational, procedural next step proposed for investigative workflow (e.g., request invoices, conduct EDD, escalate to BSA Officer).
* **Requirements:**
  1. Mandatory basis: Must cite direct evidence or explicitly link to a motivating hypothesis/indicator via `explains` (Rule `R-10`).
  2. **Mandatory Human Approval Gate:** Must explicitly declare `human_approval_required: true`. Any claim declaring `human_approval_required: false` is immediately rejected (Rule `R-7`).

### 2.7. `decision`
* **Definition:** A definitive disposition or operational action taken on an alert or case (e.g., "File SAR", "Close Alert - No Suspicious Activity Found").
* **Supervisory Constraint:** **AI models are structurally prohibited from making decisions.**
* **Requirements:** Must carry an explicit `decided_by` field attributing the decision to a named human investigator or a deterministic, policy-approved rule engine (Rule `R-5`). An AI agent proposing a decision without human attribution triggers an unrecoverable `provenance_gap` defect.

---

## 3. Claim Class Summary Matrix

| Claim Class | Requires Evidence? | Resolution Rule | Permitted Epistemic Types | Confidence Capped by Gaps? | Human Approval Required? |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `fact` | **YES** | Rule `R-1`, `R-1a` | N/A | No (self-complete) | N/A |
| `observation` | **YES** | Rule `R-1`, `R-1a` | N/A | No (direct math) | N/A |
| `indicator` | **YES** | Rule `R-1`, `R-2` | N/A | Yes (Rule `R-8`) | N/A |
| `hypothesis` | Optional | Rule `R-1a` (if cited) | `benign`, `adverse`, `data_gap`, `other` | Yes (Rule `R-3d`) | N/A |
| `risk_assessment`| Optional | Rule `R-1a`, `R-4` | N/A | **YES** (Rule `R-8`, `R-11`) | N/A |
| `recommendation` | Optional | Rule `R-1a`, `R-10` | N/A | Yes (Rule `R-8`) | **MANDATORY** (`R-7`) |
| `decision` | Optional | Rule `R-1a`, `R-5` | N/A | N/A | **HUMAN ONLY** (`R-5`) |

---

## 4. Epistemic Constraints: Why Agents Cannot Assert Criminal Guilt

Under 31 U.S.C. § 5318(g) and established judicial doctrine, **structuring**, **money laundering**, and **fraud** are criminal offenses requiring specific intent (*mens rea*). A financial institution files a Suspicious Activity Report (SAR) to report *known or suspected violations of law or suspicious transactions*; an investigator or compliance analyst never acts as a judge or jury.

When an unconstrained LLM writes:
> *"The customer structured cash deposits of $9,500 to evade the $10,000 Currency Transaction Reporting threshold."*

It commits two critical legal and supervisory errors:
1. It asserts **culpability and motive** (intent to evade) which cannot be observed from ledger data alone.
2. It exposes the institution to defamation, supervisory censure, and regulatory critique for reaching unsubstantiated legal conclusions without an evidentiary hearing.

### The Structural Invariant: Rule `R-6` and Contract Schema Enforcement

In `fincrime-skills`, preventing culpability assertions is not a suggestion hidden in a system prompt. It is enforced through two layers of defense:

1. **Structural Typing (The Primary Defense):** The agent cannot emit ungrounded conclusions because narrative prose cannot become a finding unless it decomposes into `fact`, `observation`, and balanced `hypothesis` pairs.
2. **Deterministic Culpability Matcher (Rule `R-6`):** The validator runs an AST and pattern scan over all model-authored statements. Any assertion of legal guilt or criminal intent is immediately flagged:

```text
[WARN] unsupported_claim (Rule R-6): Claim C-004 contains phrasing that may assert 
criminality of the subject (matched: 'structured cash deposits to evade'). 
Verify manually; this is a heuristic, not a proof.
```

### The Compliant Formulation
Instead of asserting intent, the compliant finding breaks the transaction pattern into:
- **`observation`:** "The customer deposited $9,500 in currency at 09:15 AM at Branch A, and $9,500 in currency at 02:30 PM at Branch B on the same calendar day." (Pointers: `txn:dep-1#/amount`, `txn:dep-2#/amount`).
- **`indicator`:** "Consecutive cash deposits just below the CTR threshold." (`IND-CASH-STRUCTURING-SUSPECTED`).
- **`hypothesis` (`adverse_reading`):** "Activity may represent an attempt to avoid currency transaction reporting." (Falsifier: "Documented proof that cash amounts correspond to distinct, unaggregated customer transactions").
- **`hypothesis` (`benign_reading`):** "Activity may reflect standard daily retail cash register sweeps from two separate boutique storefronts owned by the subject entity." (Falsifier: "Entity has only one registered business location in commercial registry").

---

## 5. The Dual-Reading Requirement (Rule `R-3b`)

One of the most dangerous phenomena in automated compliance review is **confirmation bias** (also known as *adverse tunnel vision*). Once an alert fires, standard models and inexperienced analysts tend to search exclusively for corroborating evidence of wrongdoing, disregarding obvious commercial explanations.

### The Rule `R-3b` Mandate
Under Rule `R-3b`, **an adverse hypothesis cannot stand alone**.

If a finding contains a hypothesis of epistemic type `adverse_reading`, the schema validator requires the presence of at least one competing hypothesis of epistemic type `benign_reading`. If no benign reading exists, **the finding fails validation immediately**:

```json
{
  "id": "H-001",
  "class": "hypothesis",
  "epistemic_type": "adverse_reading",
  "statement": "Subject is operating an unlicensed money transmission service.",
  "falsifier": "Registration certificate under state money transmitter registry."
}
```
*Validation Outcome without a benign counterpart:*
```text
[DEFECT] missing_benign_reading (Rule R-3b): Hypothesis H-001 is typed as an adverse_reading 
but the artifact contains no benign_reading hypothesis. An adverse reading may not stand alone.
```

### The Benign Twin Architecture
Every adverse typology in `fincrime-skills` is paired with an empirical **benign lookalike** (a "benign twin"). For example:
- *Adverse:* Shell company funnel account moving round-dollar wires with zero payroll.
- *Benign Twin:* Early-stage holding company or special purpose vehicle (SPV) executing authorized capital calls and legal retainer disbursements.

By mandating that the agent formulate both hypotheses simultaneously, the supervisory authority ensures that the investigator is presented with a fair, balanced, and objective evidentiary dossier.

---

## 6. RFC 6901 Evidence Pointer Mechanics

To guarantee **Zero Hallucination** (Evidence Attribution Accuracy = 100%), all factual assertions, indicators, and timeline events must anchor to the closed-world evidence set using **IETF RFC 6901 JSON Pointers**.

### Syntax Specification (ADR-0004)
Every pointer adheres to the strict formal grammar:
$$\text{evidence-ref} = \text{source-id} \mathbin{\text{\#}} \text{json-pointer}$$

- **`source-id`:** Identifies the verified evidence document (e.g. `txn:batch-2026-10`, `kyc:entity-profile`, `comm:email-record`).
- **`#`:** Mandatory separator between document identity and payload path.
- **`json-pointer`:** Precise path traversing the JSON document hierarchy to the specific cited value (e.g., `#/transactions/3/amount`, `#/registered_address/state`).

### Concrete Pointer Resolution
```json
{
  "id": "C-002",
  "class": "fact",
  "statement": "The beneficiary bank country is listed as LV (Latvia).",
  "confidence": {
    "level": "high",
    "basis": "Extracted directly from SWIFT MT103 field 59a."
  },
  "evidence_refs": [
    "swift:msg-9921#/beneficiary/bank_country"
  ]
}
```

When `Validator.validate()` executes:
1. The source index looks up `swift:msg-9921` in the closed evidence set. If absent, it emits `unsupported_claim` (Rule `R-1a`).
2. It evaluates the pointer `#/beneficiary/bank_country`. If the field is missing, or resolves to a mismatched value, it emits `unsupported_claim`.
3. If the pointer points to a broad collection exceeding 20 items (e.g. `swift:msg-9921#/transactions`), it emits `over_broad_citation`.

---

## 7. Institutional Review & Audit Commands

Bank auditors and compliance officers can test and verify these rules directly from the terminal using the `fincrime` CLI:

```bash
fincrime explain R-3b
```

```bash
fincrime explain R-1a
```

To validate an entire production skill suite and inspect defect enforcement:

```bash
fincrime validate skills/alert-triage
```

By enforcing these constraints, the `fincrime-skills` architecture bridges the gap between probabilistic generative AI and deterministic supervisory compliance.
