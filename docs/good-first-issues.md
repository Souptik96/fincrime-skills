# Good First Issues & Community Contributor Tracks

> **Release:** FinCrime Skills v1.0.0  
> **Status:** Open Community Onboarding  
> **License:** Apache-2.0  
> **Prerequisites:** Python 3.10+, Git, Standard Library only (zero third-party dependencies required).

Welcome to the FinCrime Skills community! We are committed to making financial crime compliance AI deterministic, evidence-grounded, and auditable.

To help new contributors make an immediate impact without navigating the entire codebase, we have structured **5 onboarding tracks** designed for software engineers, compliance analysts, machine learning researchers, and regulatory specialists.

---

## The 4 Non-Negotiable Invariants

Before choosing a track, every contributor must understand our four architectural invariants:
1. **Zero-Dependency Core (ADR-0002):** `fincrime-core` and `fincrime-cli` have zero runtime third-party dependencies (`dependencies = []`). Only Python standard library modules are permitted.
2. **Air-Gap Safety (ADR-0003):** All commands and tests execute with network sockets blocked (`scripts/check_no_network.py`). The core cannot connect to external networks.
3. **Zero Real PII (ADR-0007):** No real customer data. All test data must use reserved synthetic namespaces (`example.com`, `000-xx-xxxx`, `555-01xx`, `00-xxxxxxx`).
4. **Zero Documentation Drift:** Every code snippet in markdown documentation is continuously executed and validated in CI by `scripts/check_docs.py`.

---

## 5 Structured Contributor Tracks

```text
┌────────────────────────────────────────────────────────────────────────┐
│                      5 COMMUNITY ONBOARDING TRACKS                     │
├────────────────────────────────────────────────────────────────────────┤
│ Track 1: Author a New Typology & Benign Lookalike Twin                 │
│ Track 2: Knowledge Pack Expiry Maintenance & Record Adoption           │
│ Track 3: Adversarial Case Mutation & Attribution Stress-Testing        │
│ Track 4: LangGraph & OpenAI Agents Thin Tool Adapters                  │
│ Track 5: UK & EU Jurisdiction Scaffolding (JMLSG / AMLD6)               │
└────────────────────────────────────────────────────────────────────────┘
```

---

### Track 1: Author a New Typology & Benign Lookalike Twin
* **Difficulty:** Intermediate  
* **Target Audience:** Compliance Officers, AML Investigators, Financial Crime Analysts  
* **Goal:** Expand `fincrime_core.synth.typologies` by introducing a real-world AML typology paired with its operational benign twin.

#### Context:
Heuristic filters fail because illicit patterns look identical to ordinary commercial activity. Every typology (`TYP-*`) requires a corresponding **Benign Twin** (`BENIGN-*`) sharing feature spaces.

#### Example Candidate Typologies:
- **Trade-Based Money Laundering Over-Invoicing** (`TYP-TBML-OVERINVOICE`) vs **Expedited Charter Freight Surcharge** (`BENIGN-TBML-EXPEDITE`).
- **Payroll Funnel Laundering** (`TYP-PAYROLL-GHOST-EMPLOYEES`) vs **Seasonal Agricultural Contractor Payroll** (`BENIGN-PAYROLL-SEASONAL`).

#### Verification Workflow:
```bash
# Validate knowledge pack and typologies
fincrime knowledge typologies

# Inspect indicators and benign explanations
fincrime knowledge inspect --indicator IND-STRUCT-THRESHOLD-PROXIMITY
```

---

### Track 2: Knowledge Pack Expiry Maintenance & Record Adoption
* **Difficulty:** Beginner  
* **Target Audience:** Regulatory Specialists, Law Students, Compliance Engineers  
* **Goal:** Adopt a regulatory record in `knowledge/packs/core-2026-10`, audit statutory citations, and maintain currency under ADR-0006.

#### Context:
Financial crime regulations change over time. Under [ADR-0006](adr/0006-graded-knowledge-expiry.md), every record has an `expires_at` date. Stale knowledge triggers warnings or blocks promotion in CI.

#### Tasks:
1. Run `python scripts/knowledge_expiry_bot.py --check` to review upcoming expiration dates.
2. Review the statutory source (e.g. FinCEN, OCC, FATF, FFIEC).
3. Paraphrase and summarize updates (verbatim quotes are prohibited).
4. Update the record's `review_by` and `expires_at` metadata.

#### Verification Workflow:
```bash
# Validate knowledge pack currency
fincrime knowledge validate --pack knowledge/packs/core-2026-10

# List installed knowledge packs and review status
fincrime knowledge list
```

---

### Track 3: Adversarial Case Mutation & Attribution Stress-Testing
* **Difficulty:** Intermediate  
* **Target Audience:** AI Safety Engineers, QA Engineers, Red-Teamers  
* **Goal:** Author adversarial test cases that probe edge cases in RFC 6901 pointer resolution, temporal drift, or over-broad citations.

#### Context:
Our test suites in `skills/<skill>/evals/suites/` ensure models cannot cheat. We need adversarial cases that test:
- **Dangling Pointer Traps:** References to valid source IDs but non-existent JSON Pointer paths (`txn:TXN-01#/nonexistent_field`).
- **Temporal Drift:** Claims asserting events occurred before the account opening date.
- **Subtle Culpability:** Claims using veiled legal accusations to test Rule `R-6` detection.

#### Verification Workflow:
```bash
# Run replay evaluation across alert-triage suite
fincrime eval --skill alert-triage --replay --gates

# Explain Rule R-1a pointer resolution requirements
fincrime explain R-1a
```

---

### Track 4: LangGraph & OpenAI Agents Thin Tool Adapters
* **Difficulty:** Advanced  
* **Target Audience:** AI Engineers, Framework Integrators  
* **Goal:** Create thin, zero-dependency adapter wrappers under `adapters/` connecting FinCrime Skills to popular agent orchestration frameworks.

#### Context:
`fincrime-core` is intentionally framework-agnostic. We welcome thin adapters that convert `fincrime.skill.yaml` manifests into:
- LangChain / LangGraph tool definitions.
- OpenAI Agents function schemas (`tools = [{"type": "function", ...}]`).
- Anthropic Claude tool definitions.

#### Invariant:
Adapters must live in separate sub-packages or examples, keeping `fincrime-core` standard-library only.

#### Verification Workflow:
```bash
# Validate core import boundaries remain dependency-free
make lint

# Run CLI demo to inspect finding payload format
fincrime demo
```

---

### Track 5: UK & EU Jurisdiction Scaffolding (JMLSG / AMLD6)
* **Difficulty:** Advanced  
* **Target Audience:** UK / European Compliance Officers, International RegTech Practitioners  
* **Goal:** Scaffold the first international knowledge packs and jurisdiction documentation for UK (JMLSG / FCA) and EU (6AMLD / AMLA).

#### Context:
v1.0.0 is strictly US-scoped (FinCEN, BSA, OFAC). Expanding to a second jurisdiction requires an isolated knowledge pack (e.g., `knowledge/packs/uk-2026-10`) with distinct reporting thresholds (€10,000 / £10,000) and regulatory records.

#### Verification Workflow:
```bash
# Inspect existing jurisdiction support statement
fincrime explain R-12

# Validate policy rules
fincrime policy list
```

---

## How to Submit Your Contribution

1. Pick an issue or open one using our issue templates (`.github/ISSUE_TEMPLATE/`).
2. Fork the repository and create a feature branch (`git checkout -b feature/tbml-typology`).
3. Run the local verification suite:
   ```bash
   make dev
   make test
   make test-cli
   make lint
   make lint-pii
   make lint-docs
   make ci
   ```
4. Submit your pull request. Our automated CI will run the full air-gapped test matrix and post metric deltas.
