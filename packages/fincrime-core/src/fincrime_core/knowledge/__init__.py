"""The knowledge engine: dated, cited, jurisdiction-scoped records (ADR-0006)."""

from __future__ import annotations

from fincrime_core.knowledge.expiry import (
    EXPIRY_INTERVAL_DAYS,
    EXPIRY_LABEL,
    REVIEW_INTERVAL_DAYS,
    ExpiryAction,
    plan_expiry_actions,
)
from fincrime_core.knowledge.model import (
    DEPRECATION_GRACE_DAYS,
    ExpiryStatus,
    KnowledgeIndex,
    KnowledgePack,
    KnowledgeRecord,
    PackFinding,
    PackValidationResult,
    load_pack,
    parse_iso_date,
    parse_record,
    validate_pack,
)

__all__ = [
    "DEPRECATION_GRACE_DAYS",
    "EXPIRY_INTERVAL_DAYS",
    "EXPIRY_LABEL",
    "REVIEW_INTERVAL_DAYS",
    "ExpiryAction",
    "ExpiryStatus",
    "KnowledgeIndex",
    "KnowledgePack",
    "KnowledgeRecord",
    "PackFinding",
    "PackValidationResult",
    "load_pack",
    "parse_iso_date",
    "parse_record",
    "plan_expiry_actions",
    "validate_pack",
]
