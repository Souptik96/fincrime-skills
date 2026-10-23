"""Synthetic dataset generation, behavioral profiles, benign lookalikes, and mutators.

This module provides the generator foundation for Phase 5:
- 12 production AML/CTF/Sanctions/Fraud typologies with paired benign twins.
- Quantitative distribution overlap metrics and epistemic separation engines.
- Adversarial mutators for defect recall validation.
- PII scanner and zero-PII privacy guarantee enforcement.
"""

from __future__ import annotations

from fincrime_core.synth.mutators import (
    MUTATOR_REGISTRY,
    MutatorSpec,
    apply_mutator,
    culpability_assertion_mutator,
    isolated_adverse_reading_mutator,
    list_mutator_names,
    timeline_drift_mutator,
    unauthorized_action_mutator,
    unbounded_confidence_mutator,
    unsupported_citation_mutator,
)
from fincrime_core.synth.overlap import (
    ClassifierResult,
    FeatureVector,
    ProfileOverlapSummary,
    compute_1d_gaussian_overlap,
    compute_bhattacharyya_coefficient,
    compute_profile_overlap,
    evaluate_epistemic_classifier,
    evaluate_heuristic_threshold,
    sample_corpus_pair,
    sample_feature_vector,
)
from fincrime_core.synth.pii import (
    PIIViolation,
    RESERVED_SYNTHETIC_NAMESPACES,
    luhn_checksum,
    redact_pii,
    scan_directory,
    scan_file,
    scan_text,
)
from fincrime_core.synth.typologies import (
    TYPOLOGY_MATRIX,
    BehavioralProfile,
    BenignLookalike,
    GaussianFeature,
    TypologyModel,
    get_benign_twin,
    get_typology,
    list_typology_ids,
)

__all__ = [
    "GaussianFeature",
    "BehavioralProfile",
    "BenignLookalike",
    "TypologyModel",
    "TYPOLOGY_MATRIX",
    "get_typology",
    "get_benign_twin",
    "list_typology_ids",
    "FeatureVector",
    "ProfileOverlapSummary",
    "ClassifierResult",
    "compute_1d_gaussian_overlap",
    "compute_bhattacharyya_coefficient",
    "compute_profile_overlap",
    "sample_feature_vector",
    "sample_corpus_pair",
    "evaluate_heuristic_threshold",
    "evaluate_epistemic_classifier",
    "MutatorSpec",
    "MUTATOR_REGISTRY",
    "apply_mutator",
    "list_mutator_names",
    "unsupported_citation_mutator",
    "culpability_assertion_mutator",
    "isolated_adverse_reading_mutator",
    "unbounded_confidence_mutator",
    "unauthorized_action_mutator",
    "timeline_drift_mutator",
    "PIIViolation",
    "RESERVED_SYNTHETIC_NAMESPACES",
    "luhn_checksum",
    "redact_pii",
    "scan_directory",
    "scan_file",
    "scan_text",
]


