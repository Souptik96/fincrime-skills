"""FinCrime Core: the Evidence-Linked Finding contract, its validator, the
deterministic policy evaluator, and the knowledge engine.

The core is **dependency-free** (ADR-0002). It has no network capability, so it
cannot exfiltrate case data, and it installs in an air-gapped environment with
no index access.

Typical use::

    from fincrime_core import Validator, EnforcementContext

    validator = Validator(evidence_set=evidence_set)
    result = validator.validate(artifact)
    if not result.valid:
        for defect in result.errors:
            print(defect.code, defect.message)
"""

from __future__ import annotations

from fincrime_core.contract.model import (
    CLAIM_CLASSES,
    CONFIDENCE_LEVELS,
    EPISTEMIC_TYPES,
    Claim,
    Confidence,
    Finding,
)
from fincrime_core.provenance.hashing import canonical_json, hash_evidence_set, sha256_hex
from fincrime_core.validate.claim_lints import CulpabilityMatcher
from fincrime_core.validate.defects import Defect
from fincrime_core.validate.evidence_refs import (
    EVIDENCE_REF_PATTERN,
    SourceIndex,
    build_source_index,
    parse_evidence_ref,
)
from fincrime_core.validate.validator import (
    EnforcementContext,
    ValidationResult,
    Validator,
    load_finding_schema,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "CLAIM_CLASSES",
    "CONFIDENCE_LEVELS",
    "EPISTEMIC_TYPES",
    "Claim",
    "Confidence",
    "CulpabilityMatcher",
    "Defect",
    "EVIDENCE_REF_PATTERN",
    "EnforcementContext",
    "Finding",
    "SourceIndex",
    "ValidationResult",
    "Validator",
    "build_source_index",
    "canonical_json",
    "hash_evidence_set",
    "load_finding_schema",
    "parse_evidence_ref",
    "sha256_hex",
]
