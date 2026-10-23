"""Tests for the ``fincrime explain`` command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fincrime_cli.explain import RULE_CATALOG, explain_identifier
from fincrime_cli.main import EXIT_FINDINGS, EXIT_OK, EXIT_USAGE, main

REPO_ROOT = Path(__file__).resolve().parents[3]
GOLDEN_ARTIFACT = REPO_ROOT / "examples" / "01-alert-triage-structuring" / "artifact.json"
EVIDENCE_SET = REPO_ROOT / "examples" / "01-alert-triage-structuring" / "evidence-set.json"


class TestCliExplainRules:
    def test_explain_r3b_rule(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["explain", "R-3b"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        assert "RULE EXPLANATION: R-3b (missing_benign_reading)" in out
        assert "Epistemic Dual-Reading Requirement" in out
        assert "POL-BENIGN-HYPOTHESIS-REQUIRED" in out
        assert "REGULATORY RATIONALE:" in out
        assert "FinCEN Guidance on Defensive SAR Filings" in out
        assert "RFC 6901 POINTER TARGET:" in out
        assert "REMEDIATION INSTRUCTIONS:" in out

    def test_explain_r1a_rule(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["explain", "R-1a"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        assert "Evidence Reference Resolution" in out
        assert "SR 11-7" in out

    def test_explain_r6_rule(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["explain", "R-6"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        assert "Culpability Assertion Prevention" in out
        assert "Safe Harbor" in out

    def test_explain_by_defect_code(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["explain", "missing_benign_reading"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        assert "R-3b" in out

        code2 = main(["explain", "unsupported_claim"])
        assert code2 == EXIT_OK
        out2 = capsys.readouterr().out
        assert "R-1" in out2

    def test_explain_by_policy_id(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["explain", "POL-BENIGN-HYPOTHESIS-REQUIRED"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        assert "R-3b" in out

    def test_explain_rule_json(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["explain", "R-3b", "--json"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        document = json.loads(out)
        assert document["rule_id"] == "R-3b"
        assert document["defect_code"] == "missing_benign_reading"
        assert document["policy_id"] == "POL-BENIGN-HYPOTHESIS-REQUIRED"
        assert "FinCEN" in document["regulatory_rationale"]

    def test_explain_list_catalog(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["explain", "--list"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        assert "FINCRIME RULE & DEFECT TAXONOMY CATALOG" in out
        assert "R-1" in out
        assert "R-3b" in out
        assert "R-6" in out

    def test_explain_list_catalog_json(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["explain", "--list", "--json"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        catalog = json.loads(out)
        assert isinstance(catalog, list)
        assert len(catalog) >= 15
        rule_ids = {entry["rule_id"] for entry in catalog}
        assert "R-1" in rule_ids
        assert "R-3b" in rule_ids
        assert "R-6" in rule_ids

    def test_explain_unknown_target(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["explain", "UNKNOWN_NONEXISTENT_RULE_999"])
        assert code == EXIT_USAGE
        err = capsys.readouterr().err
        assert "unknown rule or defect code" in err

    def test_explain_identifier_helper(self) -> None:
        assert explain_identifier("r-3b") is not None
        assert explain_identifier("R3B") is not None
        assert explain_identifier("missing-benign-reading") is not None
        assert explain_identifier("pol-no-criminality-claims") is not None
        assert explain_identifier("invalid_rule") is None


class TestCliExplainArtifact:
    def test_explain_golden_artifact_valid(self, capsys: pytest.CaptureFixture) -> None:
        code = main(
            [
                "explain",
                "--artifact",
                str(GOLDEN_ARTIFACT),
                "--evidence-set",
                str(EVIDENCE_SET),
            ]
        )
        assert code == EXIT_OK
        out = capsys.readouterr().out
        assert "FINCRIME ARTIFACT DIAGNOSTIC REPORT" in out
        assert "VALID (PASS)" in out
        assert "Total Defects Found:    0" in out
        assert "No remediation required." in out

    def test_explain_golden_artifact_valid_json(self, capsys: pytest.CaptureFixture) -> None:
        code = main(
            [
                "explain",
                "--artifact",
                str(GOLDEN_ARTIFACT),
                "--evidence-set",
                str(EVIDENCE_SET),
                "--json",
            ]
        )
        assert code == EXIT_OK
        out = capsys.readouterr().out
        report = json.loads(out)
        assert report["valid"] is True
        assert report["total_defects"] == 0
        assert report["evidence_attribution_accuracy"] == 1.0

    def test_explain_artifact_with_defect(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        # Load golden artifact, strip benign reading to trigger R-3b defect
        raw = json.loads(GOLDEN_ARTIFACT.read_text(encoding="utf-8"))
        raw["claims"] = [c for c in raw["claims"] if c.get("epistemic_type") != "benign_reading"]
        bad_art = tmp_path / "bad_artifact.json"
        bad_art.write_text(json.dumps(raw), encoding="utf-8")

        code = main(
            [
                "explain",
                "--artifact",
                str(bad_art),
                "--evidence-set",
                str(EVIDENCE_SET),
            ]
        )
        assert code == EXIT_FINDINGS
        out = capsys.readouterr().out
        assert "DEFECTS DETECTED (FAIL)" in out
        assert "DEFECT #1" in out
        assert "missing_benign_reading" in out
        assert "Regulatory Rationale:" in out
        assert "Remediation:" in out

    def test_explain_nonexistent_artifact(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["explain", "--artifact", "does_not_exist_xyz.json"])
        assert code == EXIT_USAGE
        err = capsys.readouterr().err
        assert "does not exist" in err
