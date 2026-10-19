# ADR-0006: Knowledge Expiry Enforcement Graduated by Change Type

- **Status:** Accepted
- **Date:** 2026-10-19
- **Deciders:** core maintainers + domain maintainer
- **Supersedes:** none

## Context

Regulatory and typology content is the fastest-decaying asset in this project, and
the blueprint's original design made an expired knowledge pack a **hard CI break**
for any skill citing it.

The review identified the flaw: this **bricks the repository for contributors** who
cannot author a regulatory refresh. It is a self-inflicted denial of service, and
it creates a perverse incentive — the safest response to a red build is to stop
running the build. The realistic outcome is "expiry abandonware": a project that
looks alive, cites stale regulation, and has stopped enforcing anything.

The underlying requirement is still real: **stale regulatory claims must not
silently become truth.**

## Decision

Enforcement strictness is graded by **change type**, not by staleness alone.

| Context | Expired knowledge cited | Enforcement |
|---|---|---|
| Promoting a **new** skill, or a **new version** of an existing skill | Forbidden | **Hard block** — merge refused |
| A released skill whose **content changed** in the PR | Forbidden | **Hard block** |
| A released skill, **unchanged**, in a normal CI run | Allowed, disclosed | **Warning**; skill marked `MAINTENANCE_REQUIRED` in the conformance report and on the skills index |
| A published conformance report | Allowed, disclosed | The report's knowledge-status section lists every expired dependency, its owner, and its review-due date |

**Runtime artifact behavior is unchanged.** An artifact citing expired knowledge
is still marked `knowledge_stale: true` and still has its confidence ceiling
dropped to `low`. The graduation affects *whether the repository's CI goes red*,
not *whether the artifact is honest about its staleness*. This distinction is the
whole point: we relax the build gate, never the truthfulness of the artifact.

**A skill whose knowledge has been expired for more than 180 days is moved to
`status: deprecated`** in the skills index — moved, not deleted — and is excluded
from the recommended set.

**The expiry bot is a recruitment mechanism.** For each stale dependency it opens
a labelled issue, assigned to the record owner, containing the precise refresh
diff required. It hands the contributor a 20-minute task, not a warning. It is
idempotent: the same record never generates a second open issue.

**Immutability and dating remain absolute.** Packs are immutable once published;
a correction is a new pack. Every artifact records the pack id, version, and
`as_of`, so "what did the skill believe in March?" is always answerable. That is
the mechanism that stops a stale claim from silently becoming truth later.

## Consequences

**Positive**
- The repository stays usable and contributions keep flowing while knowledge is
  being refreshed.
- Staleness is *disclosed* rather than merely *blocked* — and disclosure is what a
  reader actually needs.
- The bot creates a high-frequency, low-judgment contribution path for domain
  experts, which is the project's most reliable source of external contributors.
- A hard block on *new* work still prevents new artifacts from being built on
  expired regulation.

**Negative**
- A released skill can ship with expired knowledge. The mitigation is disclosure
  plus a 180-day deprecation timer, not prevention.
- Two enforcement modes to implement and document, which is more complexity than
  one rule.
- The `MAINTENANCE_REQUIRED` signal must be visible in every surface that lists
  skills, or it will be ignored.

**Neutral**
- The validator computes two severities for the same finding — `error` and `warn`
  — and the CI gate selects by change type.

## Alternatives considered

| Alternative | Rejected because |
|---|---|
| Hard CI break on any expired citation | Bricks the repo for contributors; drives abandonment. This is the failure the review caught. |
| No enforcement at all (warning only) | New skills would be built on expired regulation. The promotion block is the part that must stay hard. |
| Auto-refresh expired records from a scraper | Copyright, staleness, reproducibility, and unaccountable source changes. Knowledge is hand-authored and dated. |
| Remove skills whose knowledge expires | Destroys the corpus and the contributor relationship. Deprecate, don't delete. |
| Version-check only, with no per-artifact disclosure | Does not answer the reader's question ("is this current?"). |
