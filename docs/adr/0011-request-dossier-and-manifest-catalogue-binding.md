# ADR-0011 — The request dossier and the manifest catalogue binding

- **Status:** Accepted
- **Date:** 2026-10-21
- **Decides:** what an information request is an artifact of, and how a skill
  declares the request-catalogue records it depends on.

## Context

Phase 3 shipped three skills. Two of them produced artifacts the Finding
Contract already had a place for: `triage_report` and `case_summary`. The
third, `evidence-request`, produces something the contract did not name: a
**request dossier**.

A request dossier is not a finding. It asserts nothing about a subject. It
takes the decisive gaps a triage or an investigation left behind, maps each
one to a record in the firm's request catalogue, and states what that record
would establish and who must approve the request. Its job is to make an
information request defensible *before* it is made, not to reach a conclusion
after it is.

Two things followed from that, and neither was written down.

**First, the artifact type was missing.** `contracts/finding.schema.json`
enumerates the artifact types a skill may produce. `request_dossier` was
added to that enumeration when the skill shipped, without the RFC and ADR
that `VERSIONING.md` requires for a change to the Finding Contract. The
change was additive and backwards-compatible, but the omission was a process
failure and it is recorded here rather than quietly ratified.

**Second, the manifest had nowhere to put a request record.** The
`knowledge` block of `contracts/skill-manifest.schema.json` had four keys:
`indicators`, `scenarios`, `typologies` and `regulatory`. There was no key
for a request-catalogue record. The `evidence-request` skill needed to
declare the thirteen `REQ-*` records it depends on, so that
`fincrime validate` resolves each one against the declared pack and fails a
skill that cites a record the pack does not contain — the same treatment every
indicator already received. With no key of its own, the records were carried
under `knowledge.scenarios`, with a comment explaining the workaround.

That worked, and it was wrong. `SCN-*` and `REQ-*` are different things, and
conflating them made the manifest say something false about the skill: that
its investigative scenarios were request templates.

## Decision

### `request_dossier` is an artifact type of the Finding Contract

`request_dossier` joins `triage_report`, `case_summary`, `sar_narrative`,
`evidence_request_plan`, `qa_result` and `sanctions_assessment` in the
`artifact.artifact_type` enumeration of `contracts/finding.schema.json`.

It is an **additive** amendment within the `1.x` contract axis, as
`VERSIONING.md` requires: no existing artifact type is removed, no existing
enum is narrowed, no field changes meaning, and no previously-valid artifact
becomes invalid. A validator built against the previous schema rejects a
`request_dossier` as an enum violation — a flagged non-conformance, not a
crash — which is how `VERSIONING.md` says a `1.x` validator treats content
it does not yet know. The contract version stays `fincrime/finding/1.0.0`:
an additive amendment within a major does not reject anything, and the minor
axis is reserved for the changes `VERSIONING.md` names as minor.

The dossier obeys the same structural rules as every other artifact. It
carries observations, recommendations, gaps and contradictions; it carries no
`decision` claim, because the dossier never decides whether a request is
made; it names the human decision that it does not make; and every
recommendation that would affect a customer declares that human approval is
required.

### The manifest declares request records under `knowledge.requests`

`contracts/skill-manifest.schema.json` gains one property under
`spec.properties.knowledge.properties`:

```json
"requests": {
  "type": "array",
  "items": { "type": "string" },
  "description": "Request catalogue records the skill cites, from the declared pack."
}
```

The `knowledge` block remains closed (`additionalProperties: false`), so the
amendment is exactly one key wide. `skills/evidence-request/fincrime.skill.yaml`
declares its thirteen records under `knowledge.requests`, and the workaround
comment is deleted rather than retained as history — the schema now says what
it means.

### Scenarios and requests are different domains

The two namespaces are kept apart, deliberately, and the manifest keys are
the boundary:

| Namespace | Domain | What it is | Manifest key |
|---|---|---|---|
| `SCN-*` | Investigation | A narrative pattern the analyst may encounter: the shape of a case, not a record to be obtained | `knowledge.scenarios` |
| `REQ-*` | Information request | A catalogue record that can be requested: a defined document, from a named holder, answering a stated question | `knowledge.requests` |

A scenario tells an agent what a situation looks like. A request tells an
agent what to ask for. The distinction matters operationally: a scenario may
be carried across an investigation without a cost, while a request reaches a
customer or a third party and carries intrusion, privacy and authority
consequences. That is why the request catalogue is a separate key, why each
record in it is a named artefact with a holder, and why the dossier that
cites one must name the gap it closes and the human who approves it.

Nothing stops a pack from publishing both kinds of record. The rule is that
the manifest must say which is which.

### The catalogue binding is checked, not assumed

A record a skill declares must exist in the declared pack, and an expired
record a skill depends on blocks promotion — the rule of
[ADR-0006](0006-graded-knowledge-expiry.md) applies to `knowledge.requests`
exactly as it applies to `knowledge.indicators`. Moving the records from
`scenarios` to `requests` changes nothing about that enforcement; it changes
what the manifest *says*.

## Consequences

**Good.** The manifest for `evidence-request` now describes the skill
accurately: the requests it depends on are requests, and the scenarios it
works through are scenarios. The contract's artifact-type enumeration is
complete for the first time since Phase 3, and the change to it is recorded
in the ADR that `VERSIONING.md` requires. A reader of the manifest can tell
which identifiers reach outside the firm and which do not.

**Bad.** The manifest contract has one more key, and every consumer of the
`knowledge` block must tolerate it. The core's own readers already iterate
the block's values rather than its keys, so a reader that looks up a key by
name must now learn one more name.

**Bad.** `request_dossier` was added to the contract without its ADR, and
this ADR is the repair rather than the process. The omission is recorded in
the changelog so that the sequence of events stays visible.

**Neutral.** `request_dossier` and `evidence_request_plan` are two artifact
types for related work. The first is what this skill produces: a dossier of
requests anchored to catalogue records. The second is the older, plan-shaped
type, kept because removing it would be a breaking change within `1.x`.

## Alternatives rejected

- **Keep the request records under `knowledge.scenarios`.** Zero work, and
  it is what was shipped. Rejected because it makes the manifest assert
  something untrue, and because the next author who reads the key learns the
  wrong model of the knowledge block.
- **A free-form `knowledge` block.** Any key, any shape. Rejected: the
  closedness of the block is what lets `fincrime validate` check every
  identifier a skill declares against the pack.
- **A new top-level `request_catalogue` key in the manifest.** Rejected as
  over-fitted to one skill. The manifest is a contract of a skill's
  dependencies, and a request record is a dependency like any other.
- **A separate contract for the request catalogue.** Rejected as a fifth
  contract to keep in step with the others for the sake of one record type.
  The catalogue lives in the knowledge pack, and the pack is already a
  versioned, dated, immutable artefact.
- **A `2.0.0` contract for the new artifact type.** Rejected: `VERSIONING.md`
  makes an added artifact type additive within `1.x`, and reserving the major
  axis for changes that would reject a previously-valid artifact would spend
  it on a change that rejects nothing.
