# Golden example — case summary

`golden_case_summary.json` is the reference for what a conformant
`case_summary` looks like. It is the artifact the Phase 3 exit criterion
validates for zero false defects, and it is the baseline every seeded-defect
mutation in `packages/fincrime-cli/tests/test_phase3_exit_criterion.py` is
applied to.

`golden_evidence_set.json` is the closed world the artifact was produced
against, spanning two accounts of one subject and two counterparties.

## What the example shows

- A `timeline` whose every entry carries at least one RFC 6901 evidence
  reference that resolves to the value the entry describes. The exit
  criterion test checks each one.
- An `indicator` claim naming `IND-MULTI-ACCOUNT-AGGREGATION`, grounded in a
  registration record that evidences the common ownership rather than
  assuming it.
- An adverse reading and a competing benign reading, each with a falsifier.
- A claim carried no further than the evidence carries it: the risk
  assessment is stated at `low` because a decisive gap blocks a conclusion.
- `human_decision_required`, naming what the case does next. The artifact
  carries no `decision` claim.

## Provenance

`provenance.evidence_set_sha256` is the canonical digest of
`golden_evidence_set.json`, and `provenance.prompt_sha256` is the SHA-256 of
`skills/case-summarize/SKILL.md`. Both are checked by the exit-criterion
test, so editing either file means recomputing the digest in the artifact.
