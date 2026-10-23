# Regulatory Mapping: Statutory & Supervisory Cross-Walk

> **Target Audience:** Bank Regulatory Examiners (FinCEN, OCC, Federal Reserve Board, FDIC), Chief Compliance Officers (CCOs), Model Risk Auditors (SR 11-7 / OCC 2011-12), and Legal Counsel.  
> **Governance Scope:** US Bank Secrecy Act (BSA) & Federal Reserve / OCC Model Risk Management Guidance.  
> **Contract Version:** `fincrime/finding/1.0.0`  
> **Status:** Normative Supervisory Cross-Walk (Auditable Governance Baseline)  

---

## 1. Executive Summary & Regulatory Authority

Financial crime compliance is one of the most strictly regulated operational domains in modern banking. Deploying artificial intelligence, machine learning, or automated agent skills in support of **Bank Secrecy Act (BSA)** / **Anti-Money Laundering (AML)** obligations requires adherence to both statutory financial crime mandates and federal supervisory guidance on model risk governance.

This document provides a formal, comprehensive cross-walk mapping the rules, contracts, and lints of the `fincrime-skills` architecture to:
1. **The Bank Secrecy Act (BSA) & FinCEN Regulations:** 31 U.S.C. § 5318(g), 31 CFR § 1010.311 (CTR), 31 CFR § 1010.230 (CDD), and 31 CFR § 1020.320 (SAR).
2. **Federal Reserve & OCC Model Risk Management Guidance:** SR 11-7 / OCC Bulletin 2011-12 (Supervisory Guidance on Model Risk Management).
3. **FFIEC BSA/AML Examination Manual:** Standards governing alert triage, narrative quality, and customer due diligence.
4. **Financial Action Task Force (FATF):** Recommendations 1 (Risk-Based Approach), 10 (Customer Due Diligence), and 20 (Suspicious Transaction Reporting).

Every control in `fincrime-skills` is mapped below with its rule identifier, statutory source, citation, control objective, deterministic verification mechanism, and explicit audit review date (`last_reviewed`).

---

## 2. Complete Supervisory Cross-Walk Table

| Rule ID | Regulatory Source | Statutory / Regulatory Citation | Control Objective & Supervisory Intent | Verification Mechanism (fincrime-core) | Last Reviewed |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **`R-1`** | FinCEN SAR Regulations & FFIEC Exam Manual | 31 U.S.C. § 5318(g); 31 CFR § 1020.320; FFIEC Manual (SAR Narrative Quality) | Factual assertions regarding customer identity, accounts, or transactions must be anchored to verifiable records. Speculative assertions without evidence are barred. | Validator structural check (`claim.requires_evidence and not claim.evidence_refs`) $\rightarrow$ Defect `unsupported_claim` | `2026-10-21` |
| **`R-1a`** | Fed / OCC Model Risk Management Guidance | SR 11-7 Section II; OCC Bulletin 2011-12 (Conceptual Soundness & Input Verification) | Zero Hallucination: Every pointer on every claim class must resolve to verified data in the closed evidence set. Citations to phantom accounts are rejected. | RFC 6901 pointer resolution via `SourceIndex.resolve(ref)` $\rightarrow$ Defect `unsupported_claim` or `over_broad_citation` | `2026-10-21` |
| **`R-1b`** | FinCEN SAR Narrative Chronology Guidance | 31 CFR § 1020.320; FFIEC BSA/AML Manual (Chronological Sequence) | Chronological event sequencing in an investigation must reflect verifiable timestamps. Unanchored timeline entries are prohibited. | Validator check on every `TimelineEntry.evidence_refs` against `SourceIndex` $\rightarrow$ Defect `unsupported_claim` | `2026-10-21` |
| **`R-2`** | FinCEN Advisory Series & FATF Guidance | FATF Recommendation 20; FinCEN Suspicious Activity Reporting Guidance | Typology indicators must cite established supervisory red flags, preventing models from inventing ad-hoc or unvalidated suspicion categories. | Membership verification in active Knowledge Pack (`known_indicator_ids`) $\rightarrow$ Defect `unknown_indicator` | `2026-10-21` |
| **`R-2b`** | Fed SR 11-7 Model Governance | SR 11-7 Section II (Model Integrity & Knowledge Currency) | Cited regulatory knowledge records must exist in the active immutable knowledge pack to ensure legal and factual validity. | Membership verification in active Knowledge Pack (`known_knowledge_ids`) $\rightarrow$ Defect `unsupported_claim` | `2026-10-21` |
| **`R-3`** | OCC Model Risk Management Guidance | OCC Bulletin 2011-12 (Effective Challenge Doctrine) | Conceptual Soundness: Hypotheses must be falsifiable; the system must document what specific evidence would disprove the theory. | Validator check (`not claim.falsifier`) $\rightarrow$ Defect `misclassified_claim` | `2026-10-21` |
| **`R-3a`** | FFIEC BSA/AML Examination Manual | 31 CFR § 1010.230; FFIEC Manual (Sound Investigation Methodology) | All hypotheses must carry an explicit epistemic type (`benign_reading`, `adverse_reading`, `data_gap`, `other`) to prevent blurring facts with theories. | Schema check (`epistemic_type not in EPISTEMIC_TYPES`) $\rightarrow$ Defect `misclassified_claim` | `2026-10-21` |
| **`R-3b`** | FFIEC Exam Manual & OCC Model Guidance | OCC Bulletin 2011-12 (Mitigation of Confirmation Bias); FinCEN SAR Narrative Guidance | Dual-Reading Invariant: An adverse hypothesis cannot stand alone; it must be balanced by a competing benign hypothesis with legitimate business explanations. | Validator invariant check (`has_adverse and not has_benign`) $\rightarrow$ Defect `missing_benign_reading` | `2026-10-21` |
| **`R-3d`** | Fed SR 11-7 Uncertainty Estimation | SR 11-7 Section III (Assessing Model Uncertainty & Limitations) | Overconfidence Limitation: An adverse hypothesis cannot be stated at `high` confidence when decisive investigative records are missing. | Validator check (`adverse and high confidence and finding.decisive_gaps`) $\rightarrow$ Defect `overstated_confidence` | `2026-10-21` |
| **`R-4`** | FinCEN Customer Due Diligence (CDD) Rule | 31 CFR § 1010.230 (Customer Risk Profiling & Beneficial Ownership) | Risk assessments lacking direct evidence references must be stated as `insufficient_information`. | Validator check (`class == 'risk_assessment' and not evidence_refs and confidence != 'insufficient_information'`) $\rightarrow$ Defect `misclassified_claim` | `2026-10-21` |
| **`R-5`** | Fed / OCC Model Risk Guidance & FinCEN Regulations | SR 11-7 (Human Decision Boundaries); 31 CFR § 1020.320 (BSA Officer Responsibility) | Non-Autonomous Decisions: AI models are prohibited from deciding case dispositions. All decisions must be attributed to named human analysts or policy rules. | Validator check (`class == 'decision' and not claim.decided_by`) $\rightarrow$ Defect `provenance_gap` | `2026-10-21` |
| **`R-6`** | Bank Secrecy Act / FinCEN SAR Instructions | 31 U.S.C. § 5318(g); FinCEN SAR Form Instructions (Prohibition of Guilt Assertions) | Prohibition of Culpability Accusations: Models must describe objective transaction patterns without asserting legal guilt or criminal mens rea (e.g. "structuring"). | Deterministic pattern scanner (`CulpabilityMatcher.find()`) $\rightarrow$ Warning `unsupported_claim` | `2026-10-21` |
| **`R-7`** | Fed SR 11-7 / OCC Model Governance | SR 11-7 Section II (Managerial Oversight & Human Decision Gates) | Human Approval Mandate: Any recommendation affecting customer accounts or operational status must declare `human_approval_required: true`. | Validator check (`class == 'recommendation' and claim.human_approval_required is False`) $\rightarrow$ Defect `escalation_missed` | `2026-10-21` |
| **`R-8`** | FFIEC BSA/AML Examination Manual | FFIEC Manual (Evaluating Completeness of Records) | Partial Evidence Discipline: If the evidence set is declared `partial`, inferential conclusions cannot be stated with `high` confidence. | Validator check (`artifact.completeness == 'partial' and confidence == 'high'`) $\rightarrow$ Defect `overstated_confidence` | `2026-10-21` |
| **`R-9`** | OCC Model Risk Guidance | OCC Bulletin 2011-12 (Alternative Model Comparison & Benchmarking) | Structural Consistency: Pointers in `competing_with` must resolve to real, competing hypotheses present in the same artifact. | Validator cross-reference check in finding claim table $\rightarrow$ Defect `provenance_gap` or `misclassified_claim` | `2026-10-21` |
| **`R-10`** | FinCEN SAR & CDD Supervisory Standards | 31 CFR § 1010.230; FFIEC Manual (Soundness of Investigative Steps) | Evidentiary Basis for Action: Recommendations must be anchored to cited evidence or linked to motivating claims via `explains`. | Validator check (`class == 'recommendation' and not evidence_refs and not explains`) $\rightarrow$ Defect `recommendation_without_basis` | `2026-10-21` |
| **`R-11`** | Federal Reserve SR 11-7 | SR 11-7 Section III (Robustness & Impact of Critical Missing Inputs) | Gap-Enforced Prudence: A risk assessment cannot assert `high` or `moderate` confidence while an unclosed decisive evidence gap blocks conclusion. | Validator check (`gap.decisive and gap.blocks_conclusion and confidence in ('high', 'moderate')`) $\rightarrow$ Defect `decisive_gap_unacknowledged` | `2026-10-21` |
| **`R-12`** | BSA Statutory Jurisdiction Limits | 31 U.S.C. § 5311 et seq.; 31 CFR Chapter X (US Territory Limitation) | Jurisdiction Integrity: Claims cannot assert authority or scope over jurisdictions not declared in the artifact header. | Validator subset check (`claim.jurisdictions <= artifact.jurisdictions`) $\rightarrow$ Defect `jurisdiction_overreach` | `2026-10-21` |
| **`R-12a`** | Skill Scope Boundaries | ADR-0008 (US Scope Only); 31 CFR Chapter X | Artifact Scope Integrity: The artifact cannot declare jurisdictions outside the permitted scope defined in the skill manifest. | Validator subset check (`artifact.jurisdictions <= allowed_jurisdictions`) $\rightarrow$ Defect `jurisdiction_overreach` | `2026-10-21` |
| **`R-13`** | FinCEN SAR Regulations | 31 CFR § 1020.320; 31 U.S.C. § 5318(g)(2) (Filing Integrity & Confidentiality) | Anti-Contradiction: Model-authored text must not claim that an electronic filing has already been completed or transmitted to FinCEN. | Regex scan (`_FILING_ASSERTION_PATTERNS`) $\rightarrow$ Warning `conflicting_draft_notice` | `2026-10-21` |
| **`ART-1`** | Fed SR 11-7 / OCC Model Governance | SR 11-7 Section II (Managerial Oversight & Human Challenge) | Mandatory Human Decision Gate: Every valid finding must explicitly declare at least one decision the AI system did NOT make via `human_decision_required`. | Artifact validator check (`not finding.human_decision_required`) $\rightarrow$ Defect `escalation_missed` | `2026-10-21` |
| **`R-NOTICE-1..3`**| FinCEN SAR Regulations | 31 CFR § 1020.320; ADR-0009 (Tool-Generated Draft Notices) | Host-Generated Draft Notice: SAR narrative artifacts must carry an immutable, non-strippable draft notice with `tool_generated: true`. | Schema and validator inspection on `finding.draft_notice` $\rightarrow$ Defect `missing_draft_notice` | `2026-10-21` |

---

## 3. Statutory Authority Alignment Breakdown

### 3.1. Bank Secrecy Act (BSA) & Currency Transaction Reporting (31 CFR § 1010.311)
Under 31 U.S.C. § 5313 and 31 CFR § 1010.311, financial institutions must report currency deposits or withdrawals in excess of $10,000. 
- Structuring indicators (`IND-CASH-INTENSITY-PROFILE-MISMATCH`) detect transactions calibrated below thresholds.
- **Rule `R-6`** enforces that the system documents measured currency flows without asserting that the subject committed criminal structuring under 31 U.S.C. § 5324.

### 3.2. FinCEN Suspicious Activity Reports (31 CFR § 1020.320)
FinCEN regulations mandate reporting of transactions involving $5,000 or more that have no business or apparent lawful purpose.
- **Rule `R-3b`** directly supports this standard by forcing the model to explicitly evaluate whether an apparent business or lawful purpose exists (`benign_reading`).
- **Rule `R-1`** and **`R-1a`** ensure that every transaction amount, counterparty name, and account reference reported in the narrative is grounded in bank records.
- **Rules `R-NOTICE-1..3`** and **ADR-0009** guarantee that draft narratives cannot be misconstrued as completed electronic filings.

### 3.3. Federal Reserve SR 11-7 / OCC Bulletin 2011-12
Federal banking guidance requires model risk management covering development, independent validation, and operational governance:
- **Input Verification & Conceptual Soundness:** Enforced by Rules `R-1`, `R-1a`, `R-1b`, and closed-world evidence hashing.
- **Rigor of Alternative Hypotheses:** Enforced by Rules `R-3`, `R-3a`, `R-3b`, and `R-9`.
- **Limits on Model Autonomy:** Enforced by Rules `R-5`, `R-7`, and `ART-1`.
- **Knowledge Currency & Degradation:** Enforced by ADR-0006, `R-8`, and `R-11`.

---

## 4. Supervisory Audit Inspection Commands

Supervisory examiners and internal audit teams can inspect individual regulatory rules and verify live rule catalogs using the `fincrime` CLI:

```bash
fincrime explain R-1
```

```bash
fincrime explain R-5
```

```bash
fincrime explain --list
```

This ensures complete supervisory transparency and zero ambiguity during regulatory examination.
