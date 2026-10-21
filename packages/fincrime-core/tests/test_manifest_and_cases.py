"""Tests for the skill manifest contract and the case suite loader.

The manifest is the machine-readable contract of a skill; the case suite is
the binding constraint on whether that skill is any good. Both are checked
here, against the contracts rather than against the reference skill, so a
change to either is caught by a test that fails without it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from fincrime_core.contract.manifest import (
    check_manifest_consistency,
    parse_skill_manifest,
    validate_skill_manifest,
)
from fincrime_core.eval.cases import validate_case_suite

REPO_ROOT = Path(__file__).resolve().parents[3]
REFERENCE_SKILL = REPO_ROOT / "skills" / "investigation-qa"


def _manifest(**overrides: Any) -> dict[str, Any]:
    document: dict[str, Any] = {
        "apiVersion": "fincrime.dev/v1",
        "kind": "FinCrimeSkill",
        "metadata": {
            "name": "test-skill",
            "version": "1.0.0",
            "status": "draft",
            "owners": ["@someone"],
            "license": "Apache-2.0",
            "jurisdiction_scope": ["US"],
        },
        "spec": {
            "purpose": "A test skill.",
            "inputs": {
                "required": [
                    {
                        "name": "artifact",
                        "description": "The finding document.",
                        "contract_ref": "fincrime/finding/1.0.0",
                    }
                ]
            },
            "preconditions": [
                {"id": "PC-1", "check": "a check", "on_fail": "stop", "message": "m"}
            ],
            "procedure": [
                {"stage": "S0", "name": "frame", "produces": ["frame"], "requires": []}
            ],
            "output": {
                "format": "fincrime/finding/1.0.0",
                "artifact": "test_result",
                "required_claims": ["frame"],
                "optional_claims": ["observation"],
                "prohibited_claims": ["decision"],
                "min_hypotheses": 0,
                "require_benign_hypothesis": False,
                "confidence": {
                    "levels": ["high", "moderate", "low"],
                    "default_ceiling": "high",
                },
            },
            "policies": {"required": ["POL-TEST"]},
            "knowledge": {"indicators": [], "scenarios": [], "typologies": [], "regulatory": []},
            "evaluation": {
                "suite": "evals/suites/test-skill",
                "case_count_min": 60,
                "gates": {"schema_validity": 1.0},
            },
            "safety": {
                "human_approval_required": ["decision"],
                "prohibited_actions": ["filing"],
                "closed_world": True,
            },
        },
    }
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(document.get(key), dict):
            document[key].update(value)
        else:
            document[key] = value
    return document


class TestSkillManifest:
    def test_a_conformant_manifest_validates(self) -> None:
        assert validate_skill_manifest(_manifest()) == []

    def test_the_reference_skill_manifest_validates(self) -> None:
        from fincrime_cli.yamlite import parse  # noqa: PLC0415

        document = parse(
            (REFERENCE_SKILL / "fincrime.skill.yaml").read_text(encoding="utf-8")
        )
        assert validate_skill_manifest(document) == []

    def test_the_reference_skill_manifest_is_self_consistent(self) -> None:
        from fincrime_cli.yamlite import parse  # noqa: PLC0415

        document = parse(
            (REFERENCE_SKILL / "fincrime.skill.yaml").read_text(encoding="utf-8")
        )
        manifest = parse_skill_manifest(document)
        assert check_manifest_consistency(manifest) == []

    def test_an_unknown_output_element_is_rejected(self) -> None:
        document = _manifest()
        document["spec"]["output"]["required_claims"] = ["not_an_element"]
        manifest = parse_skill_manifest(document)
        codes = {finding.code for finding in check_manifest_consistency(manifest)}
        assert "SKILL-OUTPUT-ELEMENT-UNKNOWN" in codes

    def test_an_element_that_is_both_required_and_prohibited_is_rejected(self) -> None:
        document = _manifest()
        document["spec"]["output"]["prohibited_claims"] = ["frame"]
        manifest = parse_skill_manifest(document)
        codes = {finding.code for finding in check_manifest_consistency(manifest)}
        assert "SKILL-OUTPUT-ELEMENT-CONTRADICTORY" in codes

    def test_a_stage_that_produces_an_undeclared_element_is_rejected(self) -> None:
        document = _manifest()
        document["spec"]["procedure"][0]["produces"] = ["hypothesis"]
        manifest = parse_skill_manifest(document)
        codes = {finding.code for finding in check_manifest_consistency(manifest)}
        assert "SKILL-STAGE-PRODUCES-UNKNOWN-ELEMENT" in codes

    def test_an_empty_jurisdiction_scope_is_rejected(self) -> None:
        document = _manifest()
        document["metadata"]["jurisdiction_scope"] = []
        manifest = parse_skill_manifest(document)
        codes = {finding.code for finding in check_manifest_consistency(manifest)}
        assert "SKILL-JURISDICTION-SCOPE-EMPTY" in codes

    def test_a_manifest_with_no_suite_is_rejected(self) -> None:
        document = _manifest()
        document["spec"]["evaluation"]["suite"] = ""
        manifest = parse_skill_manifest(document)
        codes = {finding.code for finding in check_manifest_consistency(manifest)}
        assert "SKILL-EVALUATION-SUITE-MISSING" in codes

    def test_the_manifest_carries_its_policy_ids(self) -> None:
        document = _manifest()
        document["spec"]["policies"] = {
            "required": ["POL-A"],
            "optional": ["POL-B"],
        }
        document["spec"]["procedure"][0]["guard"] = "POL-C"
        manifest = parse_skill_manifest(document)
        assert manifest.policy_ids() == ("POL-A", "POL-B")
        assert manifest.guard_ids() == ("POL-C",)


def _case(case_id: str, kind: str, **overrides: Any) -> dict[str, Any]:
    document: dict[str, Any] = {
        "case_id": case_id,
        "suite": "test-suite",
        "version": "1.0.0",
        "kind": kind,
        "tags": [],
        "input": {"inline": {}},
        "expect": {
            "required_claim_classes": ["observation"],
            "forbidden_claim_classes": [],
            "expected_escalation": True,
        },
    }
    document.update(overrides)
    return document


def _write_suite(root: Path, cases: list[dict[str, Any]], **overrides: Any) -> Path:
    suite_dir = root / "suite"
    (suite_dir / "cases").mkdir(parents=True, exist_ok=True)
    entries = []
    for case in cases:
        relative = f"cases/{case['case_id']}.json"
        (suite_dir / relative).write_text(json.dumps(case, indent=2), encoding="utf-8")
        entries.append({"case_id": case["case_id"], "path": relative, "tags": case.get("tags", [])})

    manifest: dict[str, Any] = {
        "suite_id": "test-suite",
        "skill": "test-skill",
        "version": "1.0.0",
        "as_of": "2026-10-21",
        "requirements": {
            "min_cases": len(cases),
            "min_mixed_ratio": 0.0,
            "min_negative_ratio": 0.0,
            "required_kinds": ["golden"],
        },
        "cases": entries,
    }
    manifest.update(overrides)
    (suite_dir / "suite.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return suite_dir


class TestCaseSuite:
    def test_a_conformant_suite_validates(self, tmp_path: Path) -> None:
        suite = _write_suite(tmp_path, [_case("golden-001", "golden")])
        result = validate_case_suite(suite)
        assert result.valid, [f.message for f in result.findings]
        assert result.suite is not None
        assert result.suite.case_count == 1

    def test_a_case_that_fails_the_case_contract_is_rejected(self, tmp_path: Path) -> None:
        case = _case("golden-001", "golden")
        del case["expect"]["required_claim_classes"]
        suite = _write_suite(tmp_path, [case])
        result = validate_case_suite(suite)
        assert not result.valid
        assert "case_invalid" in {finding.code for finding in result.findings}

    def test_a_duplicate_case_id_is_rejected(self, tmp_path: Path) -> None:
        case = _case("golden-001", "golden")
        suite = _write_suite(tmp_path, [case])
        manifest = json.loads((suite / "suite.json").read_text(encoding="utf-8"))
        manifest["cases"].append({"case_id": "golden-001", "path": "cases/other.json"})
        (suite / "suite.json").write_text(json.dumps(manifest), encoding="utf-8")
        result = validate_case_suite(suite)
        assert "case_duplicate_id" in {finding.code for finding in result.findings}

    def test_an_unlisted_case_file_is_rejected(self, tmp_path: Path) -> None:
        suite = _write_suite(tmp_path, [_case("golden-001", "golden")])
        (suite / "cases" / "extra.json").write_text(
            json.dumps(_case("extra-001", "golden")), encoding="utf-8"
        )
        result = validate_case_suite(suite)
        assert "case_unlisted" in {finding.code for finding in result.findings}

    def test_too_few_cases_fails_the_gate(self, tmp_path: Path) -> None:
        suite = _write_suite(
            tmp_path,
            [_case("golden-001", "golden")],
            requirements={
                "min_cases": 60,
                "min_mixed_ratio": 0.4,
                "min_negative_ratio": 0.15,
                "required_kinds": ["golden"],
            },
        )
        result = validate_case_suite(suite)
        assert "suite_case_count_below_minimum" in {finding.code for finding in result.findings}

    def test_too_few_mixed_cases_fails_the_gate(self, tmp_path: Path) -> None:
        cases = [_case(f"golden-{index:03d}", "golden") for index in range(4)]
        cases.append(_case("benign-001", "benign"))
        suite = _write_suite(
            tmp_path,
            cases,
            requirements={
                "min_cases": 5,
                "min_mixed_ratio": 0.4,
                "min_negative_ratio": 0.0,
                "required_kinds": ["golden"],
            },
        )
        result = validate_case_suite(suite)
        assert "suite_mixed_ratio_below_minimum" in {finding.code for finding in result.findings}

    def test_too_few_negative_expectations_fails_the_gate(self, tmp_path: Path) -> None:
        cases = [_case(f"golden-{index:03d}", "golden") for index in range(4)]
        cases.append(
            _case(
                "benign-001",
                "benign",
                expect={
                    "required_claim_classes": ["observation"],
                    "forbidden_claim_classes": ["risk_assessment"],
                    "expected_escalation": False,
                },
            )
        )
        suite = _write_suite(
            tmp_path,
            cases,
            requirements={
                "min_cases": 5,
                "min_mixed_ratio": 0.0,
                "min_negative_ratio": 0.4,
                "required_kinds": ["golden"],
            },
        )
        result = validate_case_suite(suite)
        assert "suite_negative_ratio_below_minimum" in {finding.code for finding in result.findings}

    def test_a_typology_with_no_benign_case_fails_the_gate(self, tmp_path: Path) -> None:
        case = _case("golden-001", "golden", tags=["TYP-STRUCTURING"])
        suite = _write_suite(
            tmp_path,
            [case],
            typologies=["TYP-STRUCTURING"],
            requirements={
                "min_cases": 1,
                "min_mixed_ratio": 0.0,
                "min_negative_ratio": 0.0,
                "required_kinds": ["golden"],
                "min_benign_per_typology": True,
            },
        )
        result = validate_case_suite(suite)
        assert "suite_benign_typology_uncovered" in {finding.code for finding in result.findings}

    def test_a_missing_required_kind_fails_the_gate(self, tmp_path: Path) -> None:
        suite = _write_suite(
            tmp_path,
            [_case("golden-001", "golden")],
            requirements={
                "min_cases": 1,
                "min_mixed_ratio": 0.0,
                "min_negative_ratio": 0.0,
                "required_kinds": ["golden", "adversarial"],
            },
        )
        result = validate_case_suite(suite)
        assert "suite_missing_required_kind" in {finding.code for finding in result.findings}

    @pytest.mark.parametrize(
        "expect",
        [
            {"forbidden_claim_classes": ["risk_assessment"]},
            {"forbidden_indicators": ["IND-X"]},
            {"forbidden_strings": ["SAR should be filed"]},
            {"expected_escalation": False},
        ],
    )
    def test_a_negative_expectation_is_recognised(self, tmp_path: Path, expect: dict) -> None:
        document = {
            "required_claim_classes": ["observation"],
            "forbidden_claim_classes": [],
            **expect,
        }
        suite = _write_suite(
            tmp_path,
            [_case("golden-001", "golden", expect=document)],
        )
        result = validate_case_suite(suite)
        assert result.suite is not None
        assert result.suite.negative_count == 1

    def test_a_case_with_only_positive_expectations_is_not_negative(self, tmp_path: Path) -> None:
        suite = _write_suite(tmp_path, [_case("golden-001", "golden")])
        result = validate_case_suite(suite)
        assert result.suite is not None
        assert result.suite.negative_count == 0
