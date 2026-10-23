"""Integration tests for the ``fincrime eval`` CLI subcommand.

Verifies end-to-end evaluation execution, replay providers, gate enforcement,
format options (markdown, json), and exit code semantics.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fincrime_cli.main import EXIT_FINDINGS, EXIT_OK, EXIT_USAGE, main

REPO_ROOT = Path(__file__).resolve().parents[3]
ALERT_TRIAGE_DIR = REPO_ROOT / "skills" / "alert-triage"
CASE_SUMMARIZE_DIR = REPO_ROOT / "skills" / "case-summarize"
EVIDENCE_REQUEST_DIR = REPO_ROOT / "skills" / "evidence-request"


class TestEvalCLI:
    def test_eval_help_returns_ok(self, capsys: pytest.CaptureFixture) -> None:
        with pytest.raises(SystemExit) as excinfo:
            main(["eval", "--help"])
        assert excinfo.value.code == 0
        out = capsys.readouterr().out
        assert "usage: fincrime eval" in out
        assert "--replay" in out
        assert "--gates" in out

    def test_eval_missing_args_returns_usage(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["eval"])
        assert code == EXIT_USAGE
        err = capsys.readouterr().err
        assert "specify --skill" in err

    def test_eval_alert_triage_replay_gates_pass(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["eval", "--skill", "alert-triage", "--replay", "--gates"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        assert "# FinCrime Skill Evaluation Report" in out
        assert "Overall Gate Status:** **PASS**" in out
        assert "schema_validity" in out
        assert "evidence_attribution_accuracy" in out
        assert "unsupported_claim_rate" in out
        assert "required_field_compliance" in out
        assert "policy_pass_rate" in out
        assert "expected_defect_recall" in out
        assert "false_defect_rate" in out

    def test_eval_json_format_output(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["eval", "--skill", "case-summarize", "--replay", "--format", "json"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        payload = json.loads(out)
        assert "suites" in payload
        assert len(payload["suites"]) == 1
        suite = payload["suites"][0]
        assert suite["skill"] == "case-summarize"
        assert suite["case_count"] == 60
        assert suite["passed_count"] == 60
        assert suite["metrics"]["schema_validity"] == 1.0
        assert suite["metrics"]["evidence_attribution_accuracy"] == 1.0

    def test_eval_write_to_out_file(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        out_file = tmp_path / "report.md"
        code = main(
            [
                "eval",
                "--skill",
                "evidence-request",
                "--replay",
                "--gates",
                "--out",
                str(out_file),
            ]
        )
        assert code == EXIT_OK
        assert out_file.is_file()
        content = out_file.read_text(encoding="utf-8")
        assert "FinCrime Skill Evaluation Report" in content
        assert "evidence-request" in content

    def test_eval_direct_suite_path(self, capsys: pytest.CaptureFixture) -> None:
        suite_path = ALERT_TRIAGE_DIR / "evals" / "suites" / "alert-triage"
        code = main(["eval", "--suite", str(suite_path), "--replay", "--gates"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        assert "Suite: `alert-triage`" in out

    def test_eval_skill_all(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["eval", "--skill", "all", "--replay", "--gates"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        assert "Suites Evaluated:** 6" in out
        assert "alert-triage" in out
        assert "case-summarize" in out
        assert "evidence-request" in out
        assert "investigation-qa" in out
        assert "sar-narrative-draft" in out
        assert "sanctions-alert" in out

    def test_eval_mock_provider(self, capsys: pytest.CaptureFixture) -> None:
        # MockProvider generates synthetic findings; runs without crashing
        code = main(["eval", "--skill", "alert-triage", "--mock"])
        assert code in (EXIT_OK, EXIT_FINDINGS)
        out = capsys.readouterr().out
        assert "Suite: `alert-triage`" in out
