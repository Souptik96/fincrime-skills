---
name: Knowledge Pack Record Expiry & Maintenance
about: Adopt or refresh an expiring regulatory record in a knowledge pack (ADR-0006)
title: "[KNOWLEDGE REFRESH] <Record ID> (e.g. REG-CTR-1010-311)"
labels: ["knowledge", "maintenance", "good first issue"]
assignees: []
---

## 1. Expiring Record Details

- **Knowledge Pack:** `knowledge/packs/core-2026-10`
- **Record ID:** (e.g. `REG-CTR-1010-311` or `IND-STRUCT-THRESHOLD-PROXIMITY`)
- **Current Expiration Date (`expires_at`):**
- **Record Maintainer:**

## 2. Regulatory Review & Statutory Currency

- **Statutory / Supervisory Authority:** (e.g. FinCEN, OCC, FDIC, Federal Reserve, FATF)
- **Current Regulation / Code of Federal Regulations (CFR):**
- **Have the underlying statutory thresholds or rules changed?**
  - [ ] No change — regulation remains current and active.
  - [ ] Yes — regulation amended (provide summary of changes below).

## 3. Proposed Updates (Derived & Paraphrased Only)

> **Important:** Do NOT paste verbatim copyrighted text or unedited statutory code. All summaries must be derived and paraphrased.

- **Updated Summary / Abstract:**
- **Updated Citations / URLs:**
- **Proposed New Dates:**
  - `as_of:` (Date of review)
  - `review_by:` (+6 months)
  - `expires_at:` (+12 months)

## 4. Verification Check

- [ ] Ran `python scripts/knowledge_expiry_bot.py --check` locally.
- [ ] Ran `fincrime knowledge validate --pack knowledge/packs/core-2026-10`.
