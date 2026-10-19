# Versioning

## The four version axes

They move independently. A skill patch must not force a CLI upgrade, and a
knowledge refresh must not force a contract change.

| Element | Scheme | Who may bump | Compatibility promise |
|---|---|---|---|
| **Finding Contract** | `fincrime/finding/<major>.<minor>.<patch>` | Core maintainers, via RFC + ADR | Within `1.x`: additive only. Removing a field, narrowing an enum, or changing the meaning of a class is **major**. |
| **Skill** | SemVer in `fincrime.skill.yaml` | Skill owner + a maintainer | MAJOR = changed required claims or semantics. MINOR = new optional claim class, reference, or case suite. PATCH = wording. |
| **Knowledge pack** | `core-YYYY-MM` | Domain owners | **Immutable once published.** A correction is a new pack. Records carry their own `version`. |
| **Policy rule** | SemVer per rule | Rule author | A semantic change to a rule is a MAJOR bump and a MAJOR bump of every skill that depends on it. |
| **Evaluation suite** | `fincrime-cases@YYYY-MM-DD` | Eval maintainers | **Append-only within a version.** Editing a case's expectations is a new suite version, and scores across versions are not comparable without a re-run. |
| **Dataset** | `fincrime-data@YYYY-MM` | Data maintainers | Immutable once published, with a DOI per frozen release. |
| **CLI / packages** | SemVer | Core maintainers | `fincrime-core` and `fincrime-evals` version separately. |

## Pre-1.0

The contract version is `0.x` and **minor bumps may break it**. This is stated
prominently so early adopters know. Post-1.0, `1.x` is backward-compatible and
`2.0` breaks.

## What counts as a breaking change

A change is breaking if it would cause a previously-valid artifact to be
rejected, or a previously-accepted skill to be rejected.

| Change | Contract | Skill | Action |
|---|---|---|---|
| New optional claim class | minor | none | Additive. Older validators treat an unknown class as a flagged non-conformance, not a crash. |
| New required field on an existing class | **major** | major | Requires `2.0` and a migration guide. |
| Narrowing an enum | **major** | major | |
| Changing the meaning of a claim class | **major** | major | The most dangerous change. Requires an ADR and a migration guide. |
| Removing a policy rule | n/a | minor if unused | |
| Tightening a policy rule so existing artifacts fail | n/a | major for affected skills | |
| Renaming an indicator id | n/a | major for dependent skills | Kept resolvable via a `deprecated_aliases` map. |
| Changing a case's expectations | n/a | n/a | **New suite version.** Never an in-place edit. |

## Deprecation

| Element | Signal | Duration | End state |
|---|---|---|---|
| Skill | `status: deprecated` + `DEPRECATED.md` + a `docs/deprecations.md` entry | 2 minor releases | Removed from the recommended set; still installable |
| Claim class (within a contract major) | `deprecated: true` in the schema | 1 minor | Retained but flagged; the validator warns |
| Indicator | `status: deprecated` + `deprecated_aliases` | Until superseded + 1 pack | Still resolvable, not citable for new artifacts |
| Policy rule | `status: deprecated` | 1 minor | Not evaluated; the skill's `policies.required` must be updated |
| Contract major | `fincrime/finding/2.0.0` published | Both supported ≥ 2 minor releases | A 1.x validator refuses a 2.x artifact with a clear message |

## Stale regulatory content

The architecture prevents a stale regulatory claim from silently becoming truth
through four mechanisms. See
[ADR-0006](docs/adr/0006-graded-knowledge-expiry.md) for the enforcement detail.

1. **Every regulatory record is dated and sourced.** `as_of`, `review_by`,
   `expires_at`, and `sources[]` are required. Derived and paraphrased content
   only — never verbatim regulatory text, which is both a copyright problem and
   a staleness trap.
2. **Packs are immutable and dated.** `core-2026-10` never changes. A
   correction is `core-2027-01`. Every artifact records the pack id, version and
   `as_of`, so a reader can always tell *when* a record was true.
3. **Expiry enforcement is graded by change type.** Hard block when promoting
   new or modified content; warning and disclosure on an unchanged released
   artifact. A skill whose knowledge has been expired for more than 180 days is
   deprecated, not deleted.
4. **Provenance anchoring.** `fincrime knowledge show <id>` shows the current
   record and what it said on the date an artifact was produced.

**The rule in one line:** every artifact states the knowledge pack it was
produced under, and every knowledge record states when it was true. A reader can
therefore always distinguish *"the skill said this"* from *"this is currently
true."*

## Compatibility matrix

Published in this file and enforced by CI.

| Contract | `fincrime-core` | Skills | Status |
|---|---|---|---|
| `fincrime/finding/1.0.0` | `0.1.x` | `investigation-qa@1.0.0` (draft) | Current |
| `fincrime/finding/2.0.0` | — | — | Not started |

## Deprecation process

1. Mark the element deprecated in its manifest or schema.
2. Add an entry to `docs/deprecations.md` with the reason and the replacement.
3. Emit a warning from the validator when it is used.
4. Remove it after the window, in a MAJOR release with a migration note.

Emergency security fixes may skip the window and are called out in the
changelog.
