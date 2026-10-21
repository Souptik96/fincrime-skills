# Golden example — evidence request

`golden_request_dossier.json` is the reference for what a conformant
`request_dossier` looks like. It is the artifact the Phase 3 exit criterion
validates for zero false defects, and it is the baseline every seeded-defect
mutation in `packages/fincrime-cli/tests/test_phase3_exit_criterion.py` is
applied to.

`golden_evidence_set.json` is the closed world the artifact was produced
against — what the triage already held when the gaps were recorded.

## What the example shows

- Two gaps, one decisive and one not, each naming the catalogue record that
  would close it.
- Recommendations that carry the catalogue record id in `knowledge_ids`,
  name the gap they close in `explains`, and carry
  `human_approval_required: true`, because every request in this dossier
  would affect the customer.
- A risk assessment stated at `low` because a decisive gap blocks a
  conclusion.
- `human_decision_required`, naming which of the drafted requests are issued.
  The artifact carries no `decision` claim and sends nothing to anybody.

## Provenance

`provenance.evidence_set_sha256` is the canonical digest of
`golden_evidence_set.json`, and `provenance.prompt_sha256` is the SHA-256 of
`skills/evidence-request/SKILL.md`. Both are checked by the exit-criterion
test, so editing either file means recomputing the digest in the artifact.
