# Ecosystem Listings & Skill Registry Integration Guide

> **Release:** FinCrime Skills v1.0.0  
> **Status:** Published & Registry Ready  
> **Licensing:** Apache-2.0  
> **Compatible Host Systems:** Anthropic Agent Skills, Claude Desktop, OpenAI Assistants API, LangGraph, AutoGen, CrewAI, and Custom Python Agent Pipelines.

---

## 1. Overview & Registry Standards

FinCrime Skills are packaged according to the open **Agent Skills specification** (`SKILL.md` frontmatter + markdown instructions) combined with the normative **FinCrime Skill Manifest** (`fincrime.skill.yaml` sidecar).

This dual-layer architecture provides universal compatibility across the emerging agent ecosystem:
- **Ecosystem Crawlers & Registries** (e.g. `npx skills`, `skills.sh`, `agentskills.in`) read the `SKILL.md` frontmatter and metadata tags to index the skill by category, compliance domain, and jurisdiction.
- **FinCrime Runtime Enforcers** (`fincrime-core`, `fincrime-cli`) validate the `fincrime.skill.yaml` sidecar to guarantee evidence pointer grounding, rule compliance, and closed-world schema integrity.

---

## 2. Standardized Discovery Metadata

Every skill in the repository is tagged with standard taxonomy fields designed for automated discovery by ecosystem crawlers and registry indexes:

```yaml
---
name: alert-triage
description: >-
  Take a raw alert and the transaction and customer evidence behind it, and
  produce a triage finding that names the indicators that match, states a
  benign reading beside every adverse reading, and records the gaps that
  block a conclusion.
license: Apache-2.0
metadata:
  fincrime_version: "1.0.0"
  contract_version: "fincrime/finding/1.0.0"
  knowledge_pack: "core-2026-10"
  category: "fincrime"
  jurisdiction: "US"
  compliance: "BSA/AML"
  risk_tier: "medium"
  domain: "triage"
---
```

### Standard Tags:
- `category: fincrime` — Categorizes the capability within regulatory technology (RegTech) and financial crime AI.
- `jurisdiction: US` — Invariant scope: regulatory rules, statutory thresholds (CTR $10,000), and reporting frameworks align strictly with US federal law (FinCEN / BSA / OFAC).
- `compliance: BSA/AML` — Identifies compliance domain (Bank Secrecy Act / Anti-Money Laundering).
- `license: Apache-2.0` — Permissive open-source license enabling internal institutional deployment.

---

## 3. Skill Catalog & Installation via `npx skills`

All six production skills can be added directly to any Agent Skills compatible environment using the standard `npx skills` package manager.

### 3.1 Alert Triage (`alert-triage`)
Evaluates raw transaction monitoring alerts against customer profile and account history; balances adverse readings with mandatory benign alternatives.

```bash
npx skills add fincrime/fincrime-skills/skills/alert-triage
```

### 3.2 Case Summarization (`case-summarize`)
Synthesizes complex multi-account, multi-counterparty investigative cases into chronological timelines anchored to RFC 6901 pointers.

```bash
npx skills add fincrime/fincrime-skills/skills/case-summarize
```

### 3.3 Evidence Request Dossier (`evidence-request`)
Translates decisive evidentiary gaps into structured Requests for Information (RFIs); requires human approval for all customer outreach.

```bash
npx skills add fincrime/fincrime-skills/skills/evidence-request
```

### 3.4 Investigation Question Answering (`investigation-qa`)
Audits existing investigative artifacts, answers evidentiary questions, and enforces strict negative assertions against unsubstantiated facts.

```bash
npx skills add fincrime/fincrime-skills/skills/investigation-qa
```

### 3.5 Sanctions Alert Triage (`sanctions-alert`)
Assesses OFAC/UN watchlist screening hits against customer identification records; evaluates attribute matches while strictly prohibiting autonomous asset blocking.

```bash
npx skills add fincrime/fincrime-skills/skills/sanctions-alert
```

### 3.6 SAR Narrative Drafting (`sar-narrative-draft`)
Drafts FinCEN Form 111 Part V Suspicious Activity narratives under 31 CFR § 1020.320; guarantees evidence attribution without asserting legal guilt (*mens rea*).

```bash
npx skills add fincrime/fincrime-skills/skills/sar-narrative-draft
```

---

## 4. Local Host Directory Setup (`.agentskills/` & `.claude/skills/`)

For desktop hosts (such as Claude Desktop or local IDE assistants), FinCrime skills can be mirrored or symlinked into host configuration roots:

```bash
# Verify skill package integrity prior to deployment
fincrime validate skills/alert-triage

# Inspect installed knowledge pack and typologies
fincrime knowledge typologies
```

---

## 5. Registry Submissions Specification

### 5.1 `skills.sh` / `agentskills.in` Registration Manifest
When indexing `fincrime-skills` on public or internal corporate skill registries, use the following canonical registry descriptor:

```json
{
  "name": "fincrime-skills",
  "version": "1.0.0",
  "description": "Deterministic, evidence-linked finding contracts for financial crime compliance AI agents.",
  "homepage": "https://github.com/fincrime/fincrime-skills",
  "repository": "https://github.com/fincrime/fincrime-skills.git",
  "license": "Apache-2.0",
  "author": "FinCrime Skills Consortium",
  "category": "fincrime",
  "compliance": "BSA/AML",
  "jurisdiction": "US",
  "skills": [
    {
      "name": "alert-triage",
      "path": "skills/alert-triage",
      "description": "Assess transaction monitoring alerts with mandatory benign twin alternatives."
    },
    {
      "name": "case-summarize",
      "path": "skills/case-summarize",
      "description": "Synthesize multi-account investigations with RFC 6901 pointer-anchored timelines."
    },
    {
      "name": "evidence-request",
      "path": "skills/evidence-request",
      "description": "Turn decisive evidence gaps into structured RFIs with human approval gates."
    },
    {
      "name": "investigation-qa",
      "path": "skills/investigation-qa",
      "description": "Audit compliance artifacts and enforce negative assertion discipline."
    },
    {
      "name": "sanctions-alert",
      "path": "skills/sanctions-alert",
      "description": "Assess OFAC screening alerts with attribute matching and false-positive triage."
    },
    {
      "name": "sar-narrative-draft",
      "path": "skills/sar-narrative-draft",
      "description": "Draft FinCEN Part V narratives with evidence grounding and zero culpability claims."
    }
  ]
}
```

### 5.2 GitHub Awesome List Entries

#### For `awesome-ai-agents`:
```markdown
- [FinCrime Skills](https://github.com/fincrime/fincrime-skills) - Deterministic, evidence-linked finding contract system and evaluation benchmark for financial crime compliance AI agents (AML, KYC, Sanctions, SARs). Zero dependencies, air-gapped runtime, and empirical hallucination reduction from 37.8% to 0.0% (p < 0.001).
```

#### For `awesome-compliance`:
```markdown
- [FinCrime Skills](https://github.com/fincrime/fincrime-skills) - Open-source regulatory finding contracts and evaluation suites conforming to FinCEN CDD Rule (31 CFR § 1010.230) and Federal Reserve SR 11-7 model risk management guidance. Includes 12 typologies paired with benign twins and a 360-case synthetic benchmark.
```

---

## 6. Verification & Automated CI Sync

To ensure that registry manifests and skills never drift from implementation truth:

```bash
# Validate all skills, case suites, and golden artifacts
make validate-skills

# Run offline replay benchmark across all 6 skills
fincrime eval --skill all --replay --gates
```
