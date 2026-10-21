"""Phase 3 exit criterion: the cross-skill QA gate.

The exit criterion has two halves, and they pull against each other. A
reviewer that never finds a defect is useless; a reviewer that reports a
defect in a conformant artifact trains people to ignore it. So the gate is
measured on both, against the same corpus:

* **Zero false defects.** Each skill ships a golden artifact, produced by
  hand against a closed evidence set. Validating it must return no defects
  at all - not no errors, *no defects*. A warning on the golden corpus is a
  false defect, because the golden artifact is the reference for what a
  conformant artifact looks like.
* **Seeded defect recall.** The golden artifacts are then deliberately
  broken in the four ways this project exists to catch, and the validator
  must catch them at a recall of at least 90%.

The seeded defects are the four failures the Finding Contract encodes
structurally, not stylistically:

``missing_benign_hypothesis``
    An adverse reading standing alone (rule R-3b). The structural defence
    against a model that reaches a conclusion: a hypothesis typed as an
    adverse reading may not stand without a benign reading beside it.

``ungrounded_recommendation``
    A recommendation that cites no evidence and explains no motivating claim
    (rule R-10). An instruction the artifact does not support.

``culpability_assertion``
    Model-authored text that asserts criminality of the subject (rule R-6).
    This one is heuristic, so it is reported as a warning by design; the
    test asserts that it is *reported*, not that it is an error.

``uncited_indicator``
    An indicator claim that names no indicator id (rule R-2), or names one
    that is not in the declared pack.

The gate runs in the promotion context: a new skill ships under the
strictest enforcement, where stale knowledge blocks rather than being
disclosed. Nothing in ``core-2026-10`` is expired as of the gate date, so
the release and promotion contexts agree today; promotion is the stricter of
the two and is the one that matters for a new artifact.
"""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any, Callable

import pytest

from fincrime_cli.yamlite import parse_file as parse_yaml_file
from fincrime_core.knowledge.model import load_pack
from fincrime_core.provenance.hashing import hash_evidence_set
from fincrime_core.validate.schema import JsonSchemaValidator
from fincrime_core.validate.validator import EnforcementContext, Validator

REPO_ROOT = Path(__file__).resolve().parents[3]
PACK_DIR = REPO_ROOT / "knowledge" / "packs" / "core-2026-10"
CONTRACTS_DIR = REPO_ROOT / "contracts"

#: The gate date. Fixed, so the gate does not move with the wall clock.
AS_OF = date(2026, 10, 21)

#: The golden artifact each skill ships, and the skill it belongs to.
GOLDEN: dict[str, str] = {
    "alert-triage": "golden_triage_report",
    "case-summarize": "golden_case_summary",
    "evidence-request": "golden_request_dossier",
}
SKILLS = sorted(GOLDEN)

#: The jurisdictions the three skills declare in their manifests.
ALLOWED_JURISDICTIONS = ["US"]


# --------------------------------------------------------------------------
# Fixtures and helpers
# --------------------------------------------------------------------------


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _examples(skill: str) -> Path:
    return REPO_ROOT / "skills" / skill / "examples"


def _manifest(skill: str) -> dict[str, Any]:
    return parse_yaml_file(REPO_ROOT / "skills" / skill / "fincrime.skill.yaml")


def _golden(skill: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """The golden artifact and the closed evidence set it was produced against."""
    base = _examples(skill)
    return (
        _load_json(base / f"{GOLDEN[skill]}.json"),
        _load_json(base / "golden_evidence_set.json"),
    )


@pytest.fixture(scope="module")
def knowledge_index() -> dict[str, list[str]]:
    """The knowledge the validator resolves indicator and record ids against."""
    pack = load_pack(PACK_DIR)
    return {
        "known_indicator_ids": list(pack.indicator_ids()),
        "known_knowledge_ids": [record.id for record in pack.records],
        "expired_knowledge_ids": [r.id for r in pack.records if r.is_expired(AS_OF)],
    }


@pytest.fixture(scope="module")
def make_validator(knowledge_index: dict[str, list[str]]) -> Callable[[dict[str, Any]], Validator]:
    """Build a validator over one closed evidence set."""

    def _make(evidence_set: dict[str, Any]) -> Validator:
        return Validator(
            evidence_set=evidence_set,
            known_indicator_ids=knowledge_index["known_indicator_ids"],
            known_knowledge_ids=knowledge_index["known_knowledge_ids"],
            expired_knowledge_ids=knowledge_index["expired_knowledge_ids"],
            allowed_jurisdictions=ALLOWED_JURISDICTIONS,
        )

    return _make


# --------------------------------------------------------------------------
# Seeded defects
# --------------------------------------------------------------------------

Mutator = Callable[[dict[str, Any]], dict[str, Any]]


def _drop_benign_hypothesis(artifact: dict[str, Any]) -> dict[str, Any]:
    """Remove the benign reading, leaving the adverse reading standing alone."""
    mutated = copy.deepcopy(artifact)
    removed = {
        claim["id"]
        for claim in mutated["claims"]
        if claim.get("class") == "hypothesis" and claim.get("epistemic_type") == "benign_reading"
    }
    assert removed, "the golden artifact carries no benign reading to remove"
    mutated["claims"] = [c for c in mutated["claims"] if c["id"] not in removed]
    for claim in mutated["claims"]:
        if "competing_with" in claim:
            claim["competing_with"] = [i for i in claim["competing_with"] if i not in removed]
    return mutated


def _unground_recommendation(artifact: dict[str, Any]) -> dict[str, Any]:
    """Strip the basis from a recommendation: no evidence, no motivating claim."""
    mutated = copy.deepcopy(artifact)
    for claim in mutated["claims"]:
        if claim.get("class") == "recommendation":
            claim.pop("evidence_refs", None)
            claim.pop("explains", None)
            break
    else:  # pragma: no cover - the golden artifacts all carry recommendations
        raise AssertionError("the golden artifact carries no recommendation to unground")
    return mutated


def _assert_culpability(artifact: dict[str, Any]) -> dict[str, Any]:
    """Write the conclusion into the artifact, the way the R-6 lint exists to catch."""
    mutated = copy.deepcopy(artifact)
    for claim in mutated["claims"]:
        if claim.get("class") == "risk_assessment":
            claim["statement"] = "The subject is a money launderer."
            break
    else:  # pragma: no cover - the golden artifacts all carry assessments
        raise AssertionError("the golden artifact carries no risk assessment to contaminate")
    return mutated


def _uncited_indicator(artifact: dict[str, Any]) -> dict[str, Any]:
    """Make an indicator claim that cites no indicator id."""
    mutated = copy.deepcopy(artifact)
    for claim in mutated["claims"]:
        if claim.get("class") == "indicator":
            claim.pop("indicator_ids", None)
            claim.pop("knowledge_ids", None)
            return mutated
    # The evidence-request dossier asserts no indicator. Add one that is
    # ungrounded, which is the same defect arriving by another route.
    mutated["claims"].append(
        {
            "id": "C-099",
            "class": "indicator",
            "statement": "Cash deposits cluster immediately below the reporting threshold.",
            "evidence_refs": ["txn:TXN-6613#/amount"],
            "confidence": {"level": "low", "basis": "Seeded defect."},
        }
    )
    return mutated


#: The seeded defects, with the defect each one must produce.
MUTATIONS: dict[str, tuple[Mutator, str, str, str]] = {
    "missing_benign_hypothesis": (
        _drop_benign_hypothesis,
        "missing_benign_reading",
        "R-3b",
        "error",
    ),
    "ungrounded_recommendation": (
        _unground_recommendation,
        "recommendation_without_basis",
        "R-10",
        "error",
    ),
    "culpability_assertion": (
        _assert_culpability,
        "unsupported_claim",
        "R-6",
        "warn",
    ),
    "uncited_indicator": (
        _uncited_indicator,
        "unsupported_claim",
        "R-2",
        "error",
    ),
}


def _defects(result: Any) -> list[Any]:
    return [d.to_dict() for d in result.defects]


# --------------------------------------------------------------------------
# Zero false defects
# --------------------------------------------------------------------------


@pytest.mark.parametrize("skill", SKILLS)
def test_golden_artifact_produces_zero_false_defects(
    skill: str, make_validator: Callable[[dict[str, Any]], Validator]
) -> None:
    """A conformant artifact must produce no defects at all."""
    artifact, evidence_set = _golden(skill)
    result = make_validator(evidence_set).validate(
        artifact, EnforcementContext(EnforcementContext.PROMOTION)
    )
    assert result.schema_errors == [], f"{skill}: schema errors: {result.schema_errors}"
    assert result.defects == [], f"{skill}: false defects: {_defects(result)}"
    assert result.valid
    assert result.unsupported_claim_rate == 0.0
    assert result.evidence_attribution_accuracy == 1.0


@pytest.mark.parametrize("skill", SKILLS)
def test_golden_evidence_set_conforms_to_the_contract(skill: str) -> None:
    """The closed world must itself be conformant, or its references mean nothing."""
    evidence_set = _load_json(_examples(skill) / "golden_evidence_set.json")
    schema = _load_json(CONTRACTS_DIR / "evidence-set.schema.json")
    errors = JsonSchemaValidator(schema).validate(evidence_set)
    assert errors == [], f"{skill}: evidence set schema errors: {errors}"


@pytest.mark.parametrize("skill", SKILLS)
def test_golden_artifact_records_the_real_evidence_set_hash(skill: str) -> None:
    """The provenance chain must name the digest of the evidence actually held."""
    artifact, evidence_set = _golden(skill)
    assert artifact["provenance"]["evidence_set_sha256"] == hash_evidence_set(evidence_set)


@pytest.mark.parametrize("skill", SKILLS)
def test_golden_artifact_records_the_real_prompt_hash(skill: str) -> None:
    """The skill body and its golden artifact must not drift apart silently."""
    artifact, _ = _golden(skill)
    digest = hashlib.sha256((REPO_ROOT / "skills" / skill / "SKILL.md").read_bytes()).hexdigest()
    assert artifact["provenance"]["prompt_sha256"] == digest, (
        f"{skill}: the recorded prompt hash does not match the current SKILL.md"
    )


@pytest.mark.parametrize("skill", SKILLS)
def test_golden_artifact_names_the_human_decision_it_did_not_make(skill: str) -> None:
    """A skill that decides nothing must still say what the human owns."""
    artifact, _ = _golden(skill)
    decisions = artifact.get("human_decision_required") or []
    assert decisions, f"{skill}: the artifact names no human decision"
    for decision in decisions:
        assert decision["question"].strip()
        assert decision["owner_role"].strip()


# --------------------------------------------------------------------------
# The cross-skill gate
# --------------------------------------------------------------------------


def _element_present(element: str, artifact: dict[str, Any]) -> bool:
    """How each element a manifest declares is expected to appear in an artifact."""
    if element in ("observation", "indicator", "hypothesis", "risk_assessment", "recommendation"):
        return any(claim.get("class") == element for claim in artifact.get("claims", []))
    if element == "evidence_inventory":
        return bool(artifact.get("evidence_inventory"))
    if element == "gaps":
        return bool(artifact.get("gaps"))
    if element == "timeline":
        return bool(artifact.get("timeline"))
    if element == "contradiction":
        return bool(artifact.get("contradictions"))
    if element == "frame":
        header = artifact.get("artifact") or {}
        return bool(header.get("skill_id")) and bool(header.get("jurisdictions")) and bool(
            artifact.get("provenance")
        )
    if element == "escalation":
        return bool(artifact.get("human_decision_required"))
    if element == "decision":
        return any(claim.get("class") == "decision" for claim in artifact.get("claims", []))
    raise AssertionError(f"unknown finding element: {element!r}")


@pytest.mark.parametrize("skill", SKILLS)
def test_golden_artifact_carries_every_required_claim(skill: str) -> None:
    """Each skill must actually produce the claims its manifest declares."""
    manifest = _manifest(skill)
    artifact, _ = _golden(skill)
    required = manifest["spec"]["output"]["required_claims"]
    missing = [element for element in required if not _element_present(element, artifact)]
    assert not missing, f"{skill}: the golden artifact is missing {missing}"


@pytest.mark.parametrize("skill", SKILLS)
def test_golden_artifact_carries_no_prohibited_claim(skill: str) -> None:
    """The prohibited claims must be absent, not merely rare."""
    manifest = _manifest(skill)
    artifact, _ = _golden(skill)
    classes = {claim.get("class") for claim in artifact.get("claims", [])}
    for prohibited in manifest["spec"]["output"]["prohibited_claims"]:
        assert prohibited not in classes, f"{skill}: the artifact carries a {prohibited} claim"


@pytest.mark.parametrize("skill", SKILLS)
def test_golden_artifact_type_matches_the_manifest(skill: str) -> None:
    """The artifact header and the sidecar must agree on what this skill produces."""
    manifest = _manifest(skill)
    artifact, _ = _golden(skill)
    output = manifest["spec"]["output"]
    assert artifact["artifact"]["artifact_type"] == output["artifact"]
    assert artifact["contract_version"] == output["format"]
    assert artifact["artifact"]["skill_id"] == manifest["metadata"]["name"]
    assert artifact["artifact"]["skill_version"] == manifest["metadata"]["version"]


@pytest.mark.parametrize("skill", SKILLS)
def test_golden_artifact_honours_the_manifest_hypothesis_rules(skill: str) -> None:
    """The hypothesis rules a manifest declares must hold in the golden artifact."""
    manifest = _manifest(skill)
    artifact, _ = _golden(skill)
    output = manifest["spec"]["output"]
    hypotheses = [c for c in artifact.get("claims", []) if c.get("class") == "hypothesis"]
    if output.get("min_hypotheses"):
        assert len(hypotheses) >= output["min_hypotheses"], (
            f"{skill}: {len(hypotheses)} hypotheses, needs {output['min_hypotheses']}"
        )
    if output.get("require_benign_hypothesis"):
        assert any(h.get("epistemic_type") == "benign_reading" for h in hypotheses), (
            f"{skill}: the golden artifact carries no benign reading"
        )
    adverse = [h for h in hypotheses if h.get("epistemic_type") == "adverse_reading"]
    if adverse:
        assert any(h.get("epistemic_type") == "benign_reading" for h in hypotheses), (
            f"{skill}: an adverse reading stands without a benign reading"
        )


def test_every_request_that_affects_a_customer_requires_human_approval() -> None:
    """The evidence-request safety rule: nothing touches a customer without a human."""
    artifact, _ = _golden("evidence-request")
    recommendations = [c for c in artifact["claims"] if c.get("class") == "recommendation"]
    assert recommendations
    for recommendation in recommendations:
        assert recommendation.get("human_approval_required") is True, (
            f"{recommendation['id']} would affect a customer without human approval"
        )


def test_case_summary_timeline_entries_all_resolve() -> None:
    """Every stated event is anchored to a pointer that resolves to what it describes."""
    artifact, evidence_set = _golden("case-summarize")
    timeline = artifact.get("timeline") or []
    assert timeline, "the golden case summary carries no timeline"
    index = Validator(evidence_set=evidence_set).source_index
    for entry in timeline:
        assert entry.get("evidence_refs"), f"timeline entry has no reference: {entry}"
        for ref in entry["evidence_refs"]:
            resolution = index.resolve(ref)
            assert resolution.ok, f"timeline entry cites an unresolvable reference: {ref}"


def test_unanchored_timeline_entry_is_detected_by_validator(
    make_validator: Callable[[dict[str, Any]], Validator],
) -> None:
    """A timeline entry whose pointer dangles must be reported, not carried.

    The timeline is the artifact's account of what happened and when. Before
    rule R-1b nothing resolved a timeline reference, so a dangling pointer
    passed validation with zero defects: the case summary could state an
    event that no record in the evidence set supported.
    """
    artifact, evidence_set = _golden("case-summarize")
    mutated = copy.deepcopy(artifact)
    timeline = mutated.get("timeline") or []
    assert timeline, "the golden case summary carries no timeline"
    timeline[0]["evidence_refs"] = ["txn:TXN-GHOST#/amount"]

    result = make_validator(evidence_set).validate(
        mutated, EnforcementContext(EnforcementContext.PROMOTION)
    )

    matching = [
        d for d in result.defects if d.code == "unsupported_claim" and d.rule_id == "R-1b"
    ]
    assert matching, f"expected an unsupported_claim defect from R-1b, got {_defects(result)}"
    assert matching[0].severity == "error"
    assert "TXN-GHOST" in matching[0].message
    assert not result.valid


# --------------------------------------------------------------------------
# Seeded defect recall
# --------------------------------------------------------------------------


@pytest.mark.parametrize("skill", SKILLS)
@pytest.mark.parametrize("mutation", sorted(MUTATIONS))
def test_seeded_defect_is_detected(
    skill: str,
    mutation: str,
    make_validator: Callable[[dict[str, Any]], Validator],
) -> None:
    """Each seeded defect must be reported, with the right code and rule."""
    mutate, code, rule_id, severity = MUTATIONS[mutation]
    artifact, evidence_set = _golden(skill)
    result = make_validator(evidence_set).validate(
        mutate(artifact), EnforcementContext(EnforcementContext.PROMOTION)
    )
    matching = [
        d for d in result.defects if d.code == code and d.rule_id == rule_id
    ]
    assert matching, (
        f"{skill}/{mutation}: expected a {code} defect from {rule_id}, got {_defects(result)}"
    )
    assert matching[0].severity == severity


def test_seeded_defect_recall_is_at_least_ninety_percent(
    make_validator: Callable[[dict[str, Any]], Validator],
) -> None:
    """The headline number: of the defects we planted, how many did we find?"""
    seeded = 0
    detected = 0
    missed: list[str] = []
    for skill in SKILLS:
        artifact, evidence_set = _golden(skill)
        validator = make_validator(evidence_set)
        for name, (mutate, code, rule_id, _severity) in MUTATIONS.items():
            seeded += 1
            result = validator.validate(
                mutate(artifact), EnforcementContext(EnforcementContext.PROMOTION)
            )
            if any(d.code == code and d.rule_id == rule_id for d in result.defects):
                detected += 1
            else:
                missed.append(f"{skill}/{name}")
    recall = detected / seeded if seeded else 0.0
    assert recall >= 0.90, f"recall {recall:.0%}, missed {missed}"
