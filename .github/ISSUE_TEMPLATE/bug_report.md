---
name: Bug Report / False Positive Report
about: Create a report to help us improve the validator, linter, or skill execution
title: "[BUG] <Brief description of defect or issue>"
labels: ["bug", "triage"]
assignees: []
---

## Description of Defect / Bug

A clear and concise description of the defect encountered.

## Component Affected

- [ ] Core Finding Contract (`contracts/*.json`)
- [ ] Schema / Evidence Resolver Validator (`fincrime-core`)
- [ ] Policy Evaluator / Rule Catalog (`fincrime-core`)
- [ ] CLI Command (`fincrime ...`)
- [ ] Skill Package (`skills/<skill-name>`)
- [ ] Knowledge Pack (`knowledge/packs/core-2026-10`)
- [ ] Other:

## Reproduction Steps

1. Command executed:
   ```bash
   fincrime validate <path-to-artifact> --evidence-set <path-to-evidence>
   ```
2. Exact exit code or defect code emitted (e.g. `unsupported_claim`, `malformed_evidence_ref`, `R-3b`):
   ```
   [Insert defect code and message here]
   ```

## Expected vs Actual Behavior

- **Expected:** (e.g., artifact should pass validation or emit a warning instead of an error)
- **Actual:** (e.g., validator flagged `R-1a` on a valid RFC 6901 pointer)

## Minimal Reproducible Artifact Payload

```json
{
  "contract_version": "fincrime/finding/1.0.0",
  "claims": [
    ...
  ]
}
```

## Privacy & Invariant Checklist

- [ ] **Zero-PII Confirmation:** This report contains NO real customer names, SSNs, phone numbers, or account numbers. All data uses synthetic placeholders.
- [ ] **Standard Library Check:** If this is a proposed fix, it introduces NO third-party runtime dependencies.
