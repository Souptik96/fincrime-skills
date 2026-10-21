"""The curated source content of the ``core-2026-10`` knowledge pack.

The content lives in data modules rather than in hand-written files because a
pack is a *published, immutable* artefact: it is written once, from a
reviewed source, and its manifest records the hash of every file. Generating
it from one reviewed source keeps the reviewed thing and the published thing
the same thing.

Each module holds the *content* of a record type — the title, the definition,
the citations — and nothing else. The shared facts (the pack id, the
jurisdiction, the dates, the maintainer) are added by
``scripts/build_core_pack.py``, so a record cannot drift out of agreement
with its siblings.

Nothing here is verbatim regulatory text. Every definition is derived and
paraphrased, which is a copyright requirement and a staleness requirement at
once: a quotation of a regulation goes stale the moment the regulation is
amended, while a paraphrase can be reviewed and re-dated.
"""

from __future__ import annotations

__all__ = ["indicators", "typologies", "regulatory", "requests"]
