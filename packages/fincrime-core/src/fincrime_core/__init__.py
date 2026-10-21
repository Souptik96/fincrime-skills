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

from fincrime_core.contract.manifest import (
    ManifestFinding,
    SkillManifest,
    check_manifest_consistency,
    load_skill_manifest_schema,
    parse_skill_manifest,
    validate_skill_manifest,
)
from fincrime_core.contract.model import (
    CLAIM_CLASSES,
    CONFIDENCE_LEVELS,
    EPISTEMIC_TYPES,
    Claim,
    Confidence,
    Finding,
)
from fincrime_core.eval.cases import (
    Case,
    CaseSuite,
    SuiteFinding,
    SuiteValidationResult,
    load_case_suite,
    validate_case_suite,
)
from fincrime_core.knowledge.expiry import ExpiryAction, plan_expiry_actions
from fincrime_core.knowledge.model import (
    KnowledgePack,
    KnowledgeRecord,
    PackFinding,
    PackValidationResult,
    load_pack,
    validate_pack,
)
from fincrime_core.policy.evaluator import PolicyEvaluator, PolicyRule, PolicyViolation
from fincrime_core.policy.set import (
    PolicySet,
    ProceduralPolicy,
    export_policy_set,
    load_policy_set,
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
    "Case",
    "CaseSuite",
    "Claim",
    "Confidence",
    "CulpabilityMatcher",
    "Defect",
    "EVIDENCE_REF_PATTERN",
    "EnforcementContext",
    "ExpiryAction",
    "Finding",
    "KnowledgePack",
    "KnowledgeRecord",
    "ManifestFinding",
    "PackFinding",
    "PackValidationResult",
    "PolicyEvaluator",
    "PolicyRule",
    "PolicySet",
    "PolicyViolation",
    "ProceduralPolicy",
    "SkillManifest",
    "SourceIndex",
    "SuiteFinding",
    "SuiteValidationResult",
    "ValidationResult",
    "Validator",
    "build_source_index",
    "canonical_json",
    "check_manifest_consistency",
    "export_policy_set",
    "hash_evidence_set",
    "load_case_suite",
    "load_finding_schema",
    "load_pack",
    "load_policy_set",
    "load_skill_manifest_schema",
    "parse_evidence_ref",
    "parse_skill_manifest",
    "plan_expiry_actions",
    "sha256_hex",
    "validate_case_suite",
    "validate_pack",
    "validate_skill_manifest",
]
