# Dataset Card: FinCrime Synthetic Evaluation Benchmark Corpus v1.0.0

> **Dataset Name:** FinCrime Synthetic Evaluation Benchmark Corpus  
> **Version:** `1.0.0`  
> **Permanent DOI:** `10.5281/zenodo.10262026`  
> **Release Date:** `2026-10-23`  
> **License:** [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0)  
> **Repository:** [`https://github.com/fincrime/fincrime-skills`](https://github.com/fincrime/fincrime-skills)  
> **Curators:** The FinCrime Skills Maintainers & Contributors  
> **Primary Seed:** `seed=42` (with multi-seed validation on seeds `123` and `999`)  
> **PII Status:** **Zero Real PII Guaranteed** (Audited via `scripts/check_pii.py`)  

---

## 1. Dataset Summary

The **FinCrime Synthetic Evaluation Benchmark Corpus** is a standardized, air-gapped evaluation benchmark comprising **360 deterministic cases** engineered specifically to test the epistemic grounding, evidentiary attribution, and regulatory policy compliance of generative AI agents in financial crime compliance (AML, CTF, KYC, and sanctions screening).

Unlike generic NLP benchmark datasets or open-domain hallucination suites, this corpus simulates realistic anti-money laundering alert files, multi-account investigative dossiers, and transaction ledgers while strictly maintaining a **Zero-PII Guarantee** and closed-world evidence boundaries.

Every case in the corpus pairs an immutable, SHA-256 hashed evidence set (`evidence-set.json`) with normative expectations (required claim classes, forbidden claim classes, expected escalations, and human approval gates) conforming to **JSON Schema 2020-12** specifications.

---

## 2. Institutional Motivation & Privacy Invariants

### 2.1 The Compliance Data Paradox
Evaluating AI in financial crime compliance faces severe institutional barriers:
1. **SAR Secrecy (31 U.S.C. § 5318(g)(2)):** It is a federal criminal violation to disclose the existence or non-existence of a Suspicious Activity Report (SAR). Real SAR filings cannot be published or shared for open-source AI evaluation.
2. **Customer Privacy & Bank Secrecy:** Real bank ledgers contain non-public personal information (NPPI) protected by the Gramm-Leach-Bliley Act (GLBA) and GDPR.
3. **Adverse Tunnel Vision:** Real alert datasets typically preserve only suspicious alerts, inducing confirmation bias in machine learning models and LLMs that systematically misinterpret ordinary commercial cash flows.

### 2.2 The Zero-PII Protocol (ADR-0007)
This corpus was generated entirely in Python standard library (`fincrime_core.synth`) using deterministic pseudo-random generators seeded at `seed=42`. All generated identifiers strictly adhere to reserved synthetic namespaces:
- **Domains & Emails:** RFC 2606 reserved domains (`example.com`, `example.org`, `example.net`).
- **Social Security Numbers (SSN):** SSA-reserved unissued area prefix `000-xx-xxxx`.
- **Phone Numbers:** North American Numbering Plan (NANP) test range `555-0100` through `555-0199`.
- **Employer Identification Numbers (EIN):** IRS-reserved unissued prefix `00-xxxxxxx`.
- **Payment Card Numbers:** Test-prefix payment card numbers (e.g., `4000-0012-3456-xxxx`, `5105-1028-xxxx-xxxx`) validated by Luhn checksums and verified against production issuer BIN ranges.
- **Continuous Enforcement:** Every commit is audited by `scripts/check_pii.py` to prevent real PII leaks.

---

## 3. Dataset Structure & Distribution

The corpus consists of **360 cases** evenly distributed across all six v1 production skills (**60 cases per skill**):

```text
evals/
├── alert-triage/          (60 cases: alert framing, dual-reading, gap identification)
├── case-summarize/        (60 cases: multi-account timeline synthesis, RFC 6901 pointer anchoring)
├── evidence-request/      (60 cases: structured RFIs, human-approval boundary)
├── investigation-qa/      (60 cases: evidentiary question answering, negative assertion gating)
├── sanctions-alert/       (60 cases: OFAC/UN attribute match evaluation, false-positive triage)
└── sar-narrative-draft/   (60 cases: FinCEN Form 111 Part V narrative structuring)
```

### 3.1 Distribution by Case Kind
Every 60-case suite enforces strict population quotas to prevent easy overfitting:

| Case Kind | Ratio (%) | Description | Objective |
| :--- | :---: | :--- | :--- |
| **`golden`** | 30.0% | Standard conformant patterns with clear evidentiary links. | Establishes baseline precision and attribution accuracy. |
| **`benign`** | 20.0% | Legitimate business activity sharing behavioral indicators. | Tests Rule `R-3b` dual-reading and prevents false positives. |
| **`adversarial`** | 16.7% | Mutated payloads with dangling pointers and over-broad claims. | Verifies detector sensitivity and defect recall. |
| **`contradictory`**| 13.3% | Conflicting evidence records (e.g. mismatched dates/amounts). | Enforces conflict identification and epistemic humility. |
| **`edge`** | 10.0% | Boundary values (e.g. CTR exact threshold $10,000.00). | Validates deterministic threshold logic. |
| **`missing_data`** | 10.0% | Incomplete records with decisive evidentiary gaps. | Forces confidence ceilings and halts unsupported jumps. |

---

## 4. Typology & Benign Twin Matrix

The corpus covers **12 high-priority financial crime typologies**, each paired with a dedicated **Benign Twin** that shares overlapping feature spaces ($\text{Bhattacharyya Affinity} \ge 0.50$):

| Typology ID | Illicit Typology Description | Benign Lookalike Twin ID | Legitimate Commercial Reality |
| :--- | :--- | :--- | :--- |
| **`TYP-STRUCTURING-SMURFING`** | Repeated cash deposits just below $10,000 CTR reporting threshold. | **`BENIGN-STRUCTURING-COMMERCIAL-CASH`** | Convenience store / restaurant weekly cash deposit schedule. |
| **`TYP-MULE-ACCOUNT-NETWORK`** | Rapid movement of funds across multiple unrelated retail accounts. | **`BENIGN-MULE-STUDENT-STIPEND`** | University student parent stipend and pooled apartment rent payments. |
| **`TYP-ACCOUNT-TAKEOVER-LAUNDERING`** | Sudden credential modification followed by high-velocity outbound wires. | **`BENIGN-ATO-NEW-DEVICE-VACATION`** | Executive overseas business trip with new authorized laptop provisioning. |
| **`TYP-ELDER-FINANCIAL-EXPLOITATION`** | Large, atypical withdrawals by third-party caregiver or newly added signer. | **`BENIGN-ELDER-FAMILY-CARETAKER`** | Licensed eldercare trustee paying routine medical hospice invoices. |
| **`TYP-SHELL-COMPANY-LAYERING`** | Complex international wire routing through opaque holding entities. | **`BENIGN-SHELL-CENTRALIZED-TREASURY`** | Multijurisdictional conglomerate centralizing corporate treasury sweep. |
| **`TYP-HUMAN-TRAFFICKING-INDICATORS`** | High-volume recurring night transactions at budget motels / transport hubs. | **`BENIGN-HT-HOTEL-PAYROLL`** | Franchise hospitality manager paying weekly third-party cleaning contractors. |
| **`TYP-CRYPTOCURRENCY-MIXER-CASHOUT`** | Rapid conversion of unhosted tumbler outflows into clean fiat bank wires. | **`BENIGN-CRYPTO-P2P-ARBITRAGE`** | Registered OTC trading desk rebalancing cross-exchange liquidity. |
| **`TYP-FUNNEL-ACCOUNT-DEPOSIT`** | Deposits in multiple branch geographies withdrawn immediately at central branch. | **`BENIGN-FUNNEL-FRANCHISE-ROYALTY`** | Multi-state retail franchise collecting daily franchisee fee deposits. |
| **`TYP-TRADE-BASED-OVER-INVOICING`** | High-value commodity trade invoices drastically exceeding market spot price. | **`BENIGN-TRADE-EXPEDITE-FREIGHT`** | Critical manufacturing supply chain rush shipment with premium charter air freight. |
| **`TYP-REAL-ESTATE-CASH-PURCHASE`** | All-cash luxury property acquisition using nested private LLCs. | **`BENIGN-REAL-ESTATE-INHERITANCE`** | Family estate probate distribution liquidating commercial real estate. |
| **`TYP-TERRORIST-FINANCING-DIVERSION`** | Outbound non-profit wire transfers routed to high-risk conflict border areas. | **`BENIGN-TF-RELIEF-CHARITY`** | Registered international NGO providing medical disaster relief supplies. |
| **`TYP-SANCTIONS-CIRCUMVENTION-TRANSSHIPMENT`** | Rerouting dual-use technologies through unaligned third-country intermediaries. | **`BENIGN-SANCTIONS-DUAL-USE-MEDICAL`** | Authorized humanitarian shipment of diagnostic ultrasound equipment. |

---

## 5. Case File Schema & Verification

Each case file in the evaluation suite adheres to `contracts/case.schema.json`:

```json
{
  "case_id": "golden-001",
  "suite": "alert-triage",
  "version": "1.0.0",
  "kind": "golden",
  "typology": "TYP-STRUCTURING-SMURFING",
  "description": "Commercial cash structuring vs legitimate daily retail deposits.",
  "input": {
    "artifact": { ... },
    "evidence_set": { ... }
  },
  "expect": {
    "required_claim_classes": ["observation", "hypothesis"],
    "forbidden_claim_classes": ["decision"],
    "expected_escalation": true,
    "human_approval_required": true
  }
}
```

### 5.1 Verification Commands
To verify the integrity and zero-PII status of this dataset:

```bash
# Verify Zero-PII guarantee across all 360 cases
python scripts/check_pii.py

# Replay evaluation across all 360 cases and verify gates
fincrime eval --skill all --replay --gates
```

---

## 6. Dataset Citation

If you use this synthetic dataset in your research or institutional compliance audits, please cite:

```bibtex
@dataset{fincrime_skills_dataset_2026,
  author       = {{The FinCrime Skills Maintainers \& Contributors}},
  title        = {FinCrime Synthetic Evaluation Benchmark Corpus (360 Cases, v1.0.0)},
  year         = 2026,
  month        = oct,
  publisher    = {Zenodo},
  version      = {1.0.0},
  doi          = {10.5281/zenodo.10262026},
  url          = {https://github.com/fincrime/fincrime-skills}
}
```
