# Jurisdiction Support & Operational Scope Boundaries

> **Target Audience:** Compliance Officers, Legal Counsel, Regulatory Examiners, and Technology Implementers.  
> **Normative Reference:** [ADR-0008 (v1 Scope: Six Skills, One Jurisdiction, Part V Only)](file:///c:/Users/soupt/.gemini/antigravity-ide/scratch/fincrime-skills/docs/adr/0008-v1-scope.md)  
> **Status:** Normative Boundary Specification  

A compliance skill that names a jurisdiction without explicitly defining its legal basis and operational limits provides zero assurance to a supervisory examiner. The person who evaluates this document is the person who must defend automated investigative outputs to federal regulators.

This document formally specifies what is supported, what is conditionally supported with strict guardrails, and what is **strictly NOT supported**.

---

## 1. United States Jurisdiction Scope (v1.0 Production)

**Supported Statutory Scope:** US Bank Secrecy Act (BSA) / Anti-Money Laundering (AML) Transaction Monitoring and Investigation (31 U.S.C. § 5311 et seq., 31 CFR Chapter X).

Every skill manifest and knowledge record in v1.0 is strictly bound to `jurisdictions: ["US"]` (Rule `R-12`, `R-12a`).

### 1.1. Operational Capability Scope Matrix

| Functional Area | Status | Governance Limit & Enforcement Mechanism |
| :--- | :---: | :--- |
| **Currency Transaction Thresholds** | **Supported** | Threshold values ($10,000) are parameterized policy inputs, not hardcoded assumptions (31 CFR § 1010.311). |
| **Structuring & Threshold Proximity** | **Supported** | Supported as a *measured transaction pattern*, never as an assertion of criminal culpability or intent (Rule `R-6`). |
| **Investigation Chronology & Timelines**| **Supported** | Every event and timestamp must resolve directly to verified evidence records (Rule `R-1b`). |
| **Evidence Gap & Contradiction Tracking**| **Supported** | Explicit tracking of missing records; decisive gaps automatically cap finding confidence (Rule `R-8`, `R-11`). |
| **SAR Narrative Drafting (Part V)** | **Supported (Draft Only)** | **Structured draft narrative only.** Under ADR-0008, the system assists in drafting the Part V narrative. It is structurally barred from generating electronic filing artifacts (BSA E-Filing batch XML) and carries an immutable, non-strippable draft notice (ADR-0009 / Rules `R-NOTICE-1..3`). |
| **Sanctions Alert Match Evaluation** | **Supported (Match Eval Only)** | Supported solely for **alert match evaluation, entity attribute comparison, and false-positive triage**. Never performs automated asset freezing or list modifications. |
| **Escalation to Human Decision** | **Supported** | Mandatory in every finding via `human_decision_required` (Rule `ART-1`). |

---

## 2. Strictly NOT Supported (Out of Scope & Prohibited Operations)

To prevent supervisory ambiguity, the following operational capabilities are **strictly prohibited and unsupported** across all skills in this repository:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        STRICTLY PROHIBITED & UNSUPPORTED CAPABILITIES                  │
└────────────────────────────────────────────────────────────────────────────────────────┘
  [X] Autonomous Account Closure or Freezing
  [X] Automated Sanctions Asset Blocking or List Ingestion
  [X] Autonomous Electronic Regulatory Filing (BSA E-Filing Batch XML / FinCEN Filing)
  [X] Numeric Customer Credit or Fraud Scoring
  [X] Real-Time Transaction Monitoring Rule Engine Execution / Core Banking Telemetry
  [X] Non-US Jurisdictions (UK, EU, APAC, FATF Non-US Jurisdictions)
```

1. **Autonomous Account Closure or Restriction:** The project does not produce, recommend, or execute automated account termination, debit freezes, or transaction holds. All operational decisions require human BSA Officer ownership (Rule `R-5`, `R-7`).
2. **Automated Sanctions Asset Blocking:** The system evaluates name, DOB, and geographic attribute proximity for alert triage. It **never** issues asset freezing directives or executes blocking actions under OFAC regulations (31 CFR Part 501).
3. **Autonomous Regulatory Filing:** No code path in this repository connects to the FinCEN BSA E-Filing system, generates electronic filing XML batches, or submits regulatory reports. All outputs are marked as draft investigative summaries.
4. **Numeric Customer Risk Scoring:** The project does not assign predictive credit scores or single numeric risk scores (e.g. "Customer Risk: 87/100"). Risk assessments are qualitative, evidence-anchored, and confidence-capped (Rule `R-4`, `R-11`).
5. **Real-Time Transaction Interception:** The skill architecture operates as an investigative copilot over retrospective alert batches and evidence sets; it is not a real-time inline payment processing filter.
6. **Non-US Jurisdictions:** Any attempt to invoke foreign statutory standards (e.g., UK Proceeds of Crime Act 2002, EU 6AMLD, German GwG) triggers an immediate `jurisdiction_overreach` defect (Rule `R-12`, `R-12a`).

---

## 3. Regulatory Knowledge Basis & Expiry Lifecycle

The regulatory rules governing US jurisdiction support reside in versioned, dated Knowledge Packs (`packages/fincrime-core/src/fincrime_core/knowledge/`). 

Static restatements in documentation are avoided to prevent regulatory drift:
- Each pack record carries explicit `as_of`, `review_by`, and `expires_at` metadata.
- If the system clock exceeds a pack's `expires_at` date, the validator automatically downgrades finding confidence and flags the output (`knowledge_stale: true`, ADR-0006).
- An automated expiry bot (`scripts/knowledge_expiry_bot.py`) monitors knowledge currency in CI.

---

## 4. Requirements for Adding a New Jurisdiction

Adding support for an additional jurisdiction (e.g., United Kingdom, European Union, Singapore) is not a configuration toggle or documentation edit. Per project governance, adding a jurisdiction requires:

1. **A Dedicated Jurisdiction Knowledge Pack:** Containing statutory citations, threshold values, and supervisory typologies with verified `jurisdictions: ["<ISO_COUNTRY_CODE>"]`.
2. **A Validated Synthetic Evaluation Suite:** A minimum of 60 synthetic evaluation cases (including 40% adversarial and benign lookalike twins) reflecting domestic typologies and commercial conventions.
3. **An Updated Entry in this Document:** Formally enumerating the supported and unsupported capabilities under domestic supervisory law.
4. **Independent Legal & Compliance Review:** Sign-off by an accredited domain practitioner in that jurisdiction.

Until all four prerequisites are satisfied in full, any skill claiming support for a non-US jurisdiction will fail CI validation under Rule `R-12a`.

---

## 5. Jurisdiction Boundary Verification Commands

Verify the active jurisdiction enforcement rules using the `fincrime` CLI:

```bash
fincrime explain R-12
```

```bash
fincrime explain R-12a
```
