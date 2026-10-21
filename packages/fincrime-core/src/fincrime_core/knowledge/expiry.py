"""The knowledge expiry plan: a pure function from a pack to a work list.

ADR-0006 makes the expiry bot a *recruitment* mechanism, not a warning
system: for each stale dependency it opens a labelled issue containing the
precise refresh diff required, so that a domain expert is handed a
twenty-minute task rather than a vague alarm.

This module holds the part that decides. It takes a pack and a date and
returns a deterministic list of refresh actions. It reads no clock, no
network, and no environment: the date is a parameter, so a plan is
reproducible and can be diffed between runs. The GitHub workflow in
``.github/workflows/knowledge-expiry.yml`` only renders and files what this
module decides.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Sequence

from fincrime_core.knowledge.model import (
    KnowledgePack,
    KnowledgeRecord,
    parse_iso_date,
)

__all__ = [
    "ExpiryAction",
    "plan_expiry_actions",
    "REVIEW_INTERVAL_DAYS",
    "EXPIRY_INTERVAL_DAYS",
    "EXPIRY_LABEL",
]

#: How long after a refresh a record should be reviewed again.
REVIEW_INTERVAL_DAYS = 180

#: How long after a refresh a record should remain valid.
EXPIRY_INTERVAL_DAYS = 365

#: The label every issue raised by the expiry bot carries.
EXPIRY_LABEL = "knowledge/expired"

#: The label naming the record type, for example ``knowledge/indicator``.
TYPE_LABEL_PREFIX = "knowledge/"


@dataclass(frozen=True, slots=True)
class ExpiryAction:
    """One record that needs a refresh, and the refresh it needs."""

    record_id: str
    title: str
    record_type: str
    pack_id: str
    maintainer: str
    status: str
    as_of: str
    review_by: str
    expires_at: str
    suggested_review_by: str
    suggested_expires_at: str
    fields_to_reverify: tuple[str, ...]
    issue_title: str
    issue_body: str
    labels: tuple[str, ...]

    @property
    def is_expired(self) -> bool:
        return self.status == "expired"

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "title": self.title,
            "record_type": self.record_type,
            "pack_id": self.pack_id,
            "maintainer": self.maintainer,
            "status": self.status,
            "as_of": self.as_of,
            "review_by": self.review_by,
            "expires_at": self.expires_at,
            "suggested_review_by": self.suggested_review_by,
            "suggested_expires_at": self.suggested_expires_at,
            "fields_to_reverify": list(self.fields_to_reverify),
            "issue_title": self.issue_title,
            "issue_body": self.issue_body,
            "labels": list(self.labels),
        }


#: The parts of a record a maintainer has to re-verify before re-dating it.
#: Re-dating without re-verifying is how a stale claim becomes truth.
_FIELDS_TO_REVERIFY: tuple[str, ...] = (
    "definition",
    "sources",
    "benign_explanations",
    "prohibited_attributes",
    "evidence_to_cite",
)


def _status_of(record: KnowledgeRecord, on: date) -> str | None:
    """The staleness status of a record, or ``None`` when it is current.

    The states are checked in order of severity. A record whose expiry passed
    more than the grace period ago is *both* expired and due for
    deprecation, and the honest report is the more serious of the two.
    """
    if record.is_deprecation_due(on):
        return "deprecation_due"
    if record.is_expired(on):
        return "expired"
    if record.is_review_due(on):
        return "review_due"
    return None


def _suggested_dates(on: date) -> tuple[str, str]:
    """The dates a refreshed record would carry, had it been reviewed today."""
    review_by = on + timedelta(days=REVIEW_INTERVAL_DAYS)
    expires_at = on + timedelta(days=EXPIRY_INTERVAL_DAYS)
    return review_by.isoformat(), expires_at.isoformat()


def _issue_body(
    record: KnowledgeRecord,
    pack_id: str,
    status: str,
    suggested_review_by: str,
    suggested_expires_at: str,
) -> str:
    """The refresh diff an owner is handed.

    The body is written to be actionable on its own: what is stale, what
    changes, and what has to be re-verified before the new dates are honest.
    """
    lines = [
        f"Knowledge record `{record.id}` ({record.type}) in pack `{pack_id}` is **{status}**.",
        "",
        f"- **Title:** {record.title}",
        f"- **Maintainer:** {record.maintainer}",
        f"- **As of:** {record.as_of}",
        f"- **Review by:** {record.review_by}",
        f"- **Expires at:** {record.expires_at}",
        "",
        "## Refresh diff",
        "",
        "```diff",
        f'-  "review_by":  "{record.review_by}",',
        f'+  "review_by":  "{suggested_review_by}",',
        f'-  "expires_at": "{record.expires_at}",',
        f'+  "expires_at": "{suggested_expires_at}"',
        "```",
        "",
        "The dates above are the mechanical result of refreshing the record "
        "today. They are only correct if the content below still is.",
        "",
        "## Re-verify before re-dating",
        "",
    ]
    for field in _FIELDS_TO_REVERIFY:
        lines.append(f"- [ ] `{field}` is still accurate")
    lines.extend(
        [
            "",
            "If the content has changed, update it in the same commit: a "
            "re-dated record whose content was not re-checked is how a stale "
            "claim becomes truth.",
            "",
            "## How",
            "",
            "1. Edit the record file in the pack.",
            "2. Update the record's `as_of`, `review_by` and `expires_at`.",
            "3. Update the pack manifest: the record's `sha256` and the pack "
            "`checksum` change with it.",
            "4. Run `fincrime knowledge validate --pack <pack dir>` and commit.",
            "",
            "A pack is immutable once published, so this refresh lands in the "
            "next pack version rather than in this one.",
        ]
    )
    return "\n".join(lines)


def plan_expiry_actions(pack: KnowledgePack, on: date) -> tuple[ExpiryAction, ...]:
    """Return the refresh actions a pack needs as of ``on``.

    The result is sorted by record id and contains one action per stale
    record: expired, review-due, and deprecation-due records all need a
    maintainer, and a deprecation-due record is one whose expiry passed more
    than :data:`DEPRECATION_GRACE_DAYS` ago.
    """
    actions: list[ExpiryAction] = []
    suggested_review_by, suggested_expires_at = _suggested_dates(on)

    for record in sorted(pack.records, key=lambda item: item.id):
        status = _status_of(record, on)
        if status is None:
            continue
        actions.append(
            ExpiryAction(
                record_id=record.id,
                title=record.title,
                record_type=record.type,
                pack_id=pack.id,
                maintainer=record.maintainer,
                status=status,
                as_of=record.as_of,
                review_by=record.review_by,
                expires_at=record.expires_at,
                suggested_review_by=suggested_review_by,
                suggested_expires_at=suggested_expires_at,
                fields_to_reverify=_FIELDS_TO_REVERIFY,
                issue_title=f"knowledge: refresh {record.id} ({pack.id})",
                issue_body=_issue_body(
                    record, pack.id, status, suggested_review_by, suggested_expires_at
                ),
                labels=(EXPIRY_LABEL, f"{TYPE_LABEL_PREFIX}{record.type}"),
            )
        )

    return tuple(actions)


def plan_expiry_actions_for_records(
    records: Sequence[KnowledgeRecord],
    pack_id: str,
    on: date,
) -> tuple[ExpiryAction, ...]:
    """Plan refresh actions for a bare list of records."""
    from fincrime_core.knowledge.model import KnowledgePack

    return plan_expiry_actions(
        KnowledgePack(id=pack_id, version="", as_of="", records=tuple(records)),
        on,
    )


def parse_as_of(value: str) -> date:
    """Parse an ``--as-of`` value into a date."""
    parsed = parse_iso_date(value)
    if parsed is None:
        raise ValueError(f"not a valid ISO-8601 date: {value!r}")
    return parsed
