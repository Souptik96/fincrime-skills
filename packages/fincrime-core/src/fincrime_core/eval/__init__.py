"""Evaluation: the case suite loader and the mix enforcement it carries."""

from __future__ import annotations

from fincrime_core.eval.cases import (
    DEFAULT_REQUIREMENTS,
    MIXED_CASE_KINDS,
    Case,
    CaseSuite,
    SuiteFinding,
    SuiteValidationResult,
    load_case_schema,
    load_case_suite,
    load_case_suite_schema,
    validate_case_suite,
)

__all__ = [
    "Case",
    "CaseSuite",
    "DEFAULT_REQUIREMENTS",
    "MIXED_CASE_KINDS",
    "SuiteFinding",
    "SuiteValidationResult",
    "load_case_schema",
    "load_case_suite",
    "load_case_suite_schema",
    "validate_case_suite",
]
