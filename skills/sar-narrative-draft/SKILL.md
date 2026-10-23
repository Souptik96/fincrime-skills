---
name: sar-narrative-draft
description: >-
  Synthesize an escalated investigation file into the Part V Suspicious
  Activity Narrative of a FinCEN SAR under US jurisdiction (31 CFR 1020.320).
  Produces a sar_narrative conforming to fincrime/finding/1.0.0 with RFC 6901
  evidence attribution, mandatory benign alternative hypothesis, and draft notice.
license: Apache-2.0
metadata:
  fincrime_version: "1.0.0"
  contract_version: "fincrime/finding/1.0.0"
  knowledge_pack: "core-2026-10"
  category: "fincrime"
  jurisdiction: "US"
  compliance: "BSA/AML"
  risk_tier: "high"
  domain: "reporting"
  related_skills: "alert-triage,case-summarize,evidence-request,investigation-qa,sanctions-alert"
---

# SAR Narrative Draft (Part V Only)

## Purpose

The `sar-narrative-draft` skill ingests an escalated financial crime investigation file (case summary, transaction timeline, account profiles, indicator matches, and evidence set) and synthesizes the **Part V Suspicious Activity Narrative** for a FinCEN Suspicious Activity Report (SAR).

Per **ADR-0008**, this skill operates strictly under US jurisdiction and generates **Part V narrative prose only**, while pre-populating mapped structured fields (Parts I–IV). It **must not** serialize, construct, or validate electronic filing artifacts (such as BSA E-Filing batch XML), and no code path in this repository emits one.

## Core Procedural Principles

1. **Closed-World Evidence Discipline (R-1, R-1a, R-1b):**
   Every statement describing transaction dates, dollar values, counterparty names, and account numbers must carry an explicit RFC 6901 pointer (`txn:*`, `doc:*`, `cust:*`) resolving against the supplied evidence set. Fabricated or unanchored citations are strictly prohibited.

2. **No Criminal Culpability Claims (R-6 & POL-NO-CRIMINALITY-CLAIMS):**
   The skill documents suspicious transactional patterns and objective behavioral anomalies. It **must never** state legal conclusions of guilt or characterize subjects as criminals (e.g., "subject is a money launderer", "guilty of fraud", "committed money laundering").

3. **Mandatory Epistemic Dual-Reading (R-3b & POL-BENIGN-HYPOTHESIS-REQUIRED):**
   The narrative must present and evaluate both adverse and benign commercial hypotheses regarding the observed activity, identifying any decisive gaps that require law enforcement or subpoena resolution.

4. **Human Decision & Escalation Required (R-7 & Safety Bounds):**
   The drafted SAR narrative is a recommendation to the BSA Officer and AML Committee. Final SAR filing decisions require mandatory human review and approval (`human_approval_required: true`).

## Standard Part V Narrative Structure

The output `sar_narrative` adheres to the canonical five-section FinCEN narrative architecture:
- **Section 1: Introduction & Subject Identification:** Identifies subject, relationship to institution, and triggering alert window.
- **Section 2: Summary of Suspicious Activity:** Concise executive summary of aggregated volumes, velocity, and core typology.
- **Section 3: Chronological Transactional Narrative:** Chronological progression of transactions anchored to pointers.
- **Section 4: Typology & Indicator Analysis:** Analysis of matched indicators and competing benign hypotheses.
- **Section 5: Disposition & Action Taken:** Records internal account restrictions, law enforcement contact, and human sign-off recommendation.
