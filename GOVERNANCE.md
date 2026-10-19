# Governance

## Roles

| Role | Count | Responsibilities |
|---|---|---|
| **Core maintainers** | 2–3 | Merges, releases, contract changes, CI, security response. Any core change requires two approvals. |
| **Domain maintainers** | ≥ 1 per skill | Own the skill's content, the indicators, the benign explanations, and the knowledge records. A domain maintainer is a compliance or financial-crime practitioner, **not** only an engineer. |
| **Eval maintainers** | 1–2 | Case suites, the harness, the conformance report, the baselines. |
| **Triagers** | 2–4 | Issues and pull requests, with an explicit triage rotation. |
| **Emeritus maintainers** | as earned | Advisory; no merge rights. |

**The domain maintainer is the credibility anchor.** The project's central claim
is that it produces defensible financial-crime analysis. That claim cannot be
established by engineers alone. A skill with no domain owner does not ship.

## Release rules

- **No release without two maintainers present.** The bus-factor policy is
  written down before it is needed, not after.
- A **contract change** (the Finding Contract, the skill manifest, the policy
  rule model) requires two maintainer approvals and an ADR.
- A **skill release** requires one maintainer and the skill's domain owner.
- A **knowledge pack promotion** requires one maintainer and the record owner.

## The cut rule

> **A capability ships when it has (a) a contract, (b) a case suite with a
> benign population, (c) a deterministic gate it passes, and (d) a named owner
> who can maintain its knowledge.**

This rule is enforced by the merge gate, not by good intentions. It is what
keeps six skills excellent instead of thirty mediocre ones.

## Scope reduction is a legitimate decision

If the project cannot sustain its scope, **reducing the scope is a success, not
a failure.** Dropping a skill, a jurisdiction, or a weekly run is a planned
decision recorded in `ROADMAP.md`, not a silent drift. A scoped, honest project
survives; a broad, abandoned one does not.

A project that would rather delete a skill than serve stale regulatory content
is a project an institution can trust. We would rather be smaller and correct.

## RFC process

Changes to any of the following require an RFC (a short document in
`docs/rfcs/`, open for comment for at least 7 days):

- the Finding Contract or any normative schema
- the claim class ontology or the defect taxonomy
- the policy rule model
- the evidence-reference grammar
- the licensing of the contracts (which determines who may build on them)

The RFC process is deliberately light. It exists to catch the changes that are
hard to reverse, not to gate ordinary work.

## Decision-making

- Ordinary technical decisions: the responsible maintainer decides and records
  the reasoning in the pull request.
- Anything that changes a normative contract: an ADR, reviewed as above.
- Anything that changes the licensing of the contracts: maintainer consensus,
  with a written rationale, published before the change.

## Maintenance responsibilities

| Asset | Who maintains it | Cadence |
|---|---|---|
| `contracts/` | Core maintainers | On change, with an ADR |
| `packages/fincrime-core` | Core maintainers | Continuous |
| `knowledge/packs/*` | The named domain owner of each record | On `review_by` (typically quarterly) |
| `skills/*` | The skill's domain owner | On change, and when its knowledge is refreshed |
| `evals/suites/*` | Eval maintainers | Continuously; cases are added, never edited in place |
| `policies/default` | Core maintainers | On change |

## The expiry bot as a recruitment mechanism

The knowledge expiry bot is not only a maintenance tool. It is the project's
most reliable source of external contributors: it opens a labelled issue per
stale dependency, assigned to the record owner, containing the precise refresh
diff required. A domain expert can pick one up in about twenty minutes.

This is deliberate. Sustainable maintenance of regulatory content is the hardest
problem this project faces, and a mechanism that converts it into small,
well-specified contributions is the answer.

## How a domain maintainer is appointed

Co-signature by an existing domain maintainer and one core maintainer. The
candidate must demonstrate that they can author a benign explanation for a
typology and a knowledge record with a citable source — a practical test, not
a credential.

## Contact

- Security: see `SECURITY.md`.
- General: the discussions board.

## Code of conduct

See `CODE_OF_CONDUCT.md`.
