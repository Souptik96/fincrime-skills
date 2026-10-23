"""Tests for the Phase 5 synthetic typology matrix, benign twins, and feature overlap engine."""

from __future__ import annotations

import pytest

from fincrime_core.synth.overlap import (
    compute_1d_gaussian_overlap,
    compute_bhattacharyya_coefficient,
    compute_profile_overlap,
    evaluate_epistemic_classifier,
    evaluate_heuristic_threshold,
    sample_corpus_pair,
    sample_feature_vector,
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

EXPECTED_12_TYPOLOGY_IDS = [
    "TYP-STRUCTURING-SMURFING",
    "TYP-MULE-ACCOUNT-NETWORK",
    "TYP-ELDER-FINANCIAL-EXPLOITATION",
    "TYP-ACCOUNT-TAKEOVER-LAUNDERING",
    "TYP-TRADE-BASED-MONEY-LAUNDERING",
    "TYP-SHELL-COMPANY-LAYERING",
    "TYP-REAL-ESTATE-CASH-LAYERING",
    "TYP-TERRORIST-FINANCING-DIVERSION",
    "TYP-FUNNEL-HUMAN-TRAFFICKING",
    "TYP-CRYPTO-MIXER-HOPPING",
    "TYP-TRANSSHIPMENT-SANCTIONS-EVASION",
    "TYP-PAYROLL-GHOST-EMPLOYEE",
]


def test_typology_matrix_has_12_typologies() -> None:
    """The typology matrix must contain exactly 12 production AML/CTF typologies."""
    ids = list_typology_ids()
    assert len(ids) == 12
    assert ids == EXPECTED_12_TYPOLOGY_IDS


def test_typology_models_structural_completeness() -> None:
    """Every typology model must have complete attributes, category, and definition."""
    valid_categories = {"aml", "ctf", "sanctions", "fraud"}
    for typology in TYPOLOGY_MATRIX:
        assert typology.id.startswith("TYP-")
        assert len(typology.title.strip()) > 5
        assert typology.category in valid_categories
        assert len(typology.definition.strip()) > 30
        assert len(typology.behavioral_attributes) >= 3

        # Illicit profile check
        profile = typology.illicit_profile
        for name, feat in profile.as_dict().items():
            assert feat.std > 0, f"{typology.id} {name} std must be positive"
            assert feat.min_val <= feat.mean <= feat.max_val, f"{typology.id} {name} mean out of bounds"


def test_12_paired_benign_twins_completeness() -> None:
    """Each typology must have a paired benign twin lookalike with exculpatory evidence requirements."""
    for typology in TYPOLOGY_MATRIX:
        twin = typology.benign_twin
        assert twin.id.startswith("BENIGN-")
        assert twin.typology_id == typology.id
        assert len(twin.commercial_scenario.strip()) > 40
        assert len(twin.exculpatory_evidence_requirements) >= 3

        # Lookup helpers
        assert get_benign_twin(typology.id) is twin
        assert get_typology(typology.id) is typology


def test_gaussian_overlap_mathematical_bounds() -> None:
    """Weitzman and Bhattacharyya overlap metrics must respect mathematical bounds."""
    f1 = GaussianFeature(mean=10.0, std=2.0)
    f2 = GaussianFeature(mean=10.0, std=2.0)
    # Identical distributions have overlap 1.0
    assert compute_1d_gaussian_overlap(f1, f2) == pytest.approx(1.0, abs=1e-4)
    assert compute_bhattacharyya_coefficient(f1, f2) == pytest.approx(1.0, abs=1e-4)

    # Completely separated distributions have overlap close to 0
    f_far = GaussianFeature(mean=100.0, std=1.0)
    assert compute_1d_gaussian_overlap(f1, f_far) < 0.001
    assert compute_bhattacharyya_coefficient(f1, f_far) < 0.001


def test_all_12_pairs_exceed_80_percent_feature_overlap() -> None:
    """All 12 typology / benign lookalike pairs must exhibit >= 80% mean feature overlap.

    This ensures benign twins cannot be trivially separated from typologies
    by surface-level transactional statistics alone.
    """
    for typology in TYPOLOGY_MATRIX:
        summary = compute_profile_overlap(
            typology.illicit_profile, typology.benign_twin.behavioral_profile
        )

        assert summary.mean_overlap >= 0.80, (
            f"{typology.id} vs {typology.benign_twin.id} mean overlap "
            f"{summary.mean_overlap:.3f} is below 80% floor"
        )
        assert summary.geometric_overlap >= 0.75, (
            f"{typology.id} geometric overlap {summary.geometric_overlap:.3f} below 75%"
        )
        # Every single feature dimension must maintain substantial overlap
        assert summary.min_overlap >= 0.60, (
            f"{typology.id} min feature overlap {summary.min_overlap:.3f} below 60%"
        )


def test_heuristic_threshold_classifier_produces_high_false_positives() -> None:
    """A purely statistical threshold rule catches illicit cases but fails on benign twins.

    In TYP-STRUCTURING-SMURFING:
    - Setting a heuristic threshold on velocity >= 3.0 and threshold_proximity >= 0.85
      flags both criminals and honest agricultural harvest vendors.
    """
    structuring = get_typology("TYP-STRUCTURING-SMURFING")

    def threshold_rule(v) -> bool:
        return v.velocity_daily >= 3.0 and v.threshold_proximity_ratio >= 0.85

    result = evaluate_heuristic_threshold(
        structuring, threshold_predicate=threshold_rule, n_samples=100, seed=42
    )

    # Catches most illicit cases (high recall)
    assert result.recall >= 0.80, f"Expected recall >= 0.80, got {result.recall:.2f}"

    # BUT flags over 50% of honest agricultural vendors (high false positive rate)
    assert result.false_positive_rate >= 0.50, (
        f"Expected FPR >= 0.50 on benign twin, got {result.false_positive_rate:.2f}"
    )

    # Consequently, precision is poor (~50-65%), proving heuristic thresholding is inadequate
    assert result.precision <= 0.70, (
        f"Expected precision <= 0.70 under heuristic threshold, got {result.precision:.2f}"
    )


def test_epistemic_classifier_achieves_perfect_separation() -> None:
    """Under Rule R-3b, pairing benign hypotheses with exculpatory evidence achieves 100% precision.

    This proves that closed-world evidence attribution and mandatory benign_reading
    hypothesis testing are mathematically necessary to triage benign lookalikes.
    """
    for typology in TYPOLOGY_MATRIX:
        result = evaluate_epistemic_classifier(typology, n_samples=100, seed=42)

        assert result.precision == 1.0
        assert result.recall == 1.0
        assert result.false_positive_rate == 0.0
        assert result.f1_score == 1.0


def test_deterministic_feature_sampling() -> None:
    """Sampling feature vectors must be 100% reproducible given a fixed seed."""
    typology = get_typology("TYP-MULE-ACCOUNT-NETWORK")

    run1_illicit, run1_benign = sample_corpus_pair(typology, n_samples=10, seed=42)
    run2_illicit, run2_benign = sample_corpus_pair(typology, n_samples=10, seed=42)

    assert len(run1_illicit) == 10
    assert len(run1_benign) == 10

    for v1, v2 in zip(run1_illicit, run2_illicit):
        assert v1.as_dict() == v2.as_dict()

    for v1, v2 in zip(run1_benign, run2_benign):
        assert v1.as_dict() == v2.as_dict()

    # Different seeds produce different samples
    run3_illicit, _ = sample_corpus_pair(typology, n_samples=10, seed=999)
    assert run1_illicit[0].as_dict() != run3_illicit[0].as_dict()
