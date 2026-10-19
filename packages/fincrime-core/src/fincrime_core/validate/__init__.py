"""Deterministic validation: schema, evidence resolution, claim lints."""

from __future__ import annotations

from fincrime_core.validate.claim_lints import CulpabilityMatcher, lint_artifact, lint_claims
from fincrime_core.validate.defects import Defect, DefectInfo, load_defect_taxonomy
from fincrime_core.validate.evidence_refs import (
    EVIDENCE_REF_PATTERN,
    SOURCE_ID_PATTERN,
    Resolution,
    SourceIndex,
    build_source_index,
    escape_token,
    parse_evidence_ref,
    unescape_token,
)
from fincrime_core.validate.schema import JsonSchemaValidator, SchemaError
from fincrime_core.validate.validator import (
    EnforcementContext,
    ValidationResult,
    Validator,
    load_finding_schema,
)

__all__ = [
    "CulpabilityMatcher",
    "Defect",
    "DefectInfo",
    "EVIDENCE_REF_PATTERN",
    "EnforcementContext",
    "JsonSchemaValidator",
    "Resolution",
    "SOURCE_ID_PATTERN",
    "SchemaError",
    "SourceIndex",
    "ValidationResult",
    "Validator",
    "build_source_index",
    "escape_token",
    "lint_artifact",
    "lint_claims",
    "load_defect_taxonomy",
    "load_finding_schema",
    "parse_evidence_ref",
    "unescape_token",
]
