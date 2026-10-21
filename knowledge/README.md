# Knowledge packs

A knowledge pack is a dated, cited, jurisdiction-scoped set of records: the
indicators, typologies, regulatory mappings, request-catalogue entries and
scenarios a skill depends on. ADR-0006 governs what a pack is and what
happens when it goes stale.

This file is the format specification. The normative contracts are
[`contracts/knowledge-pack-manifest.schema.json`](../contracts/knowledge-pack-manifest.schema.json)
and [`contracts/knowledge-record.schema.json`](../contracts/knowledge-record.schema.json).

## Layout

```text
knowledge/packs/<pack-id>/
├── manifest.json
└── records/
    ├── indicator/<IND-ID>.json
    ├── typology/<TYP-ID>.json
    ├── regulatory/<REG-ID>.json
    ├── request/<REQ-ID>.json
    └── scenario/<SC-ID>.json
```

Only the `records/` directory is read. A pack may carry notes, schemas or
generator output beside its records, and none of that is a record.

A worked example is in [`examples/sample-pack/`](examples/sample-pack). It is
an example, not a published pack: it exists so the format, the loader and
the expiry tooling have something real to exercise.

## The published packs

| Pack | Version | As of | Records | Scope |
|---|---|---|---|---|
| [`packs/core-2026-10`](packs/core-2026-10) | 1.0.0 | 2026-10-01 | 83 | US |

`core-2026-10` is the first dated pack: 25 indicators, 8 typologies, 20 US
regulatory mappings and 30 request-catalogue entries. It is built from a
reviewed source by [`scripts/build_core_pack.py`](../scripts/build_core_pack.py),
so the published bytes and the reviewed content are the same thing:

```bash
python scripts/build_core_pack.py --check
```

re-derives the pack from its source and reports any difference. Editing a
published record in place is not the way to correct it: a pack is immutable
once published, so a correction is a new pack version.

## The manifest

| Field | Meaning |
|---|---|
| `id` | The pack id, for example `core-2026-10`. Kebab-case. |
| `version` | Semantic version of the pack. |
| `as_of` | The date the pack's content was last verified as a whole. |
| `description` | What the pack covers, in prose. |
| `jurisdictions` | Never empty, never `global`. Regulatory content is never jurisdiction-agnostic. |
| `maintainer` | A person or a team, named. A record nobody owns expires silently. |
| `records` | The index: every record's id, type, path and file hash. |
| `checksum` | The sha256 of the canonical JSON of the record index, sorted by record id. |
| `notes` | Optional. |

## The records

Each record is a JSON file conforming to the knowledge-record contract. The
fields that carry the weight:

- `definition` — derived and paraphrased. **Verbatim regulatory text is not
  permitted.** It is a copyright problem and a staleness trap.
- `sources[]` — at least one citation, with a URL where one exists. A
  definition nobody can trace is an assertion.
- `jurisdictions[]` — never empty, never `global`.
- `as_of`, `review_by`, `expires_at` — all three present. These are what the
  expiry plan reads.
- `benign_explanations[]` — at least one, for indicators. **This is the most
  valuable field in the file.** It is the source material for the
  benign-hypothesis rule and for the benign population that measures a
  false-positive rate. An indicator without one is a detector with no
  false-positive population.
- `prohibited_attributes[]` — the bias control. An indicator may not be
  defined over a protected or proxy-protected attribute. The record contract
  requires the field; the list is the vocabulary of attributes that may not
  appear.
- `maintainer` — a person, not a team.

## Immutability

**A published pack is immutable. A correction is a new pack version.**

A pack is the thing a reviewer reviewed, the thing a run was anchored to,
and the thing an auditor will ask for. Editing a published pack in place
means the record a reviewer approved is not the record a run used. So a
correction ships as a new version, and the old one stays available.

## Integrity

```bash
fincrime knowledge validate --pack knowledge/packs/<pack-id>
```

Four things are checked, all of them integrity rather than judgement:

1. the manifest satisfies its contract;
2. every record file parses and satisfies the record contract;
3. every record file's sha256 matches the hash the manifest recorded;
4. the manifest's checksum matches the checksum computed from the index.

A pack that fails any of these is refused, and the findings say which.

## Expiry

```bash
fincrime knowledge check --pack knowledge/packs/<pack-id> --as-of 2026-10-21
```

The plan is a pure function of the pack and the date. It reports, for each
stale record, what changed since it was last verified and what a maintainer
has to re-verify before re-dating it. It does not file anything; the
[expiry workflow](../.github/workflows/knowledge-expiry.yml) renders the plan
into issues and files them.

Three states, in the order they are checked:

| State | When |
|---|---|
| `expired` | `expires_at` has passed. |
| `review_due` | `review_by` has passed but the record has not expired. |
| `deprecation_due` | The record expired more than 180 days ago. |

Enforcement is graded (ADR-0006):

- **Released content** — stale knowledge is disclosed, not blocked. The
  artifact is flagged and the skill is marked `MAINTENANCE_REQUIRED`.
- **Promotion** — promoting new or modified content against expired
  knowledge is a hard block. `fincrime validate --promotion` applies it.

## The expiry bot

The bot is a recruitment mechanism, not a warning system. Once a day it
computes the plan and opens one labelled issue per stale record, addressed
to the record's maintainer, containing the precise refresh diff required.
A domain expert is handed a twenty-minute task, not an alarm.

The workflow contains no expiry logic of its own. Everything it needs comes
from `fincrime knowledge check --json`, which is deterministic and takes its
date as an argument.
