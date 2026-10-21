# Golden example — alert triage

`golden_triage_report.json` is the reference for what a conformant
`triage_report` looks like. It is the artifact the Phase 3 exit criterion
validates for zero false defects, and it is the baseline every seeded-defect
mutation in `packages/fincrime-cli/tests/test_phase3_exit_criterion.py` is
applied to.

`golden_evidence_set.json` is the closed world the artifact was produced
against. Every evidence reference in the artifact resolves inside it, and
nothing outside it may be cited.

## What the example shows

- An evidence inventory built before anything is asserted.
- An indicator claim naming `IND-STRUCT-THRESHOLD-PROXIMITY`, with the
  records that evidence it and the pack record it comes from.
- An adverse reading and a competing benign reading, each with a falsifier.
- A risk assessment stated at `low` because a decisive gap blocks a
  conclusion.
- A recommendation that names the catalogue records it would obtain and
  carries `human_approval_required: true`.
- `human_decision_required`, naming the disposition that the human still
  owns. The artifact carries no `decision` claim.

## Provenance

`provenance.evidence_set_sha256` is the canonical digest of
`golden_evidence_set.json`, and `provenance.prompt_sha256` is the SHA-256 of
`skills/alert-triage/SKILL.md`. Both are checked by the exit-criterion test,
so editing either file means recomputing the digest in the artifact.
