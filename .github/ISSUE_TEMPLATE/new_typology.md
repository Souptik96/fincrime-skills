---
name: New Typology & Benign Twin Proposal
about: Propose a new financial crime typology paired with its operational benign lookalike twin
title: "[TYPOLOGY] <Typology Name> / <Benign Twin Name>"
labels: ["typology", "knowledge", "good first issue"]
assignees: []
---

## 1. Illicit Typology Description

- **Typology ID:** `TYP-<NAME>`
- **Title:** 
- **Summary:**
- **Regulatory / Statutory Basis:** (e.g. FinCEN Advisory, FATF Typologies Report, FFIEC Manual)
- **Primary Observable Indicators:** (e.g. velocity, structuring, counterparty geography)

## 2. Benign Lookalike Twin (Mandatory per Rule R-3b)

- **Benign Twin ID:** `BENIGN-<NAME>`
- **Title:**
- **Legitimate Commercial / Retail Reality:** (Why does normal business activity mimic this illicit pattern?)
- **Exculpatory Evidence Sources:** (What records prove this is legitimate: e.g. invoices, payroll schedules, franchise agreements?)

## 3. Mathematical Overlap & Feature Space

- **Overlapping Features:** (e.g. cash deposit frequency, transaction amounts)
- **Distinguishing Discrepancies:** (What evidence rules out the adverse reading?)

## 4. Proposed Synthetic Test Case Outline

- **Target Skill:** `skills/<alert-triage|case-summarize|sar-narrative-draft>`
- **Expected Escalation:** `true` (for illicit) / `false` (for benign)
- **Falsification Criteria:**

## Contributor Attestation

- [ ] I confirm that all proposed indicators and case data use synthetic values with **Zero Real PII** (RFC 2606 test domains, `000-xx-xxxx` SSNs, `555-01xx` numbers).
- [ ] I understand that the typology must not assert criminal guilt (*mens rea*) and must support epistemic dual-reading under Rule `R-3b`.
