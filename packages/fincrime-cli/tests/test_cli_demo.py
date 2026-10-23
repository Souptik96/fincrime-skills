"""Tests for the ``fincrime demo`` command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fincrime_cli.demo import run_demo
from fincrime_cli.main import EXIT_OK, main


class TestCliDemo:
    def test_demo_terminal_output(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["demo"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        assert "FINCRIME VERIFICATION ENGINE" in out
        assert "UNCONSTRAINED BASELINE LLM" in out
        assert "EVIDENCE-LINKED FINDING" in out
        assert "HEAD-TO-HEAD COMPARISON SCORECARD" in out
        assert "100.0% (RFC 6901 Verified)" in out
        assert "PASS (Objective Facts)" in out
        assert "PASS (Adverse + Benign Twin)" in out
        assert "zero network, zero API keys" in out

    def test_demo_json_output(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["demo", "--json"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        document = json.loads(out)
        assert document["skill"] == "alert-triage"
        assert "scenario" in document
        assert "unconstrained_llm" in document
        assert len(document["unconstrained_llm"]["defects"]) >= 4

        elf = document["evidence_linked_finding"]
        assert elf["validation"]["valid"] is True
        assert elf["validation"]["metrics"]["evidence_attribution_accuracy"] == 1.0
        assert elf["validation"]["metrics"]["unsupported_claim_rate"] == 0.0
        assert elf["validation"]["defects"] == []

        assert document["execution"]["network_calls"] == 0
        assert document["execution"]["duration_seconds"] < 5.0

    def test_demo_non_interactive_flag(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["demo", "--non-interactive"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        assert "FINCRIME VERIFICATION ENGINE" in out

    def test_demo_custom_skill(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["demo", "--skill", "alert-triage"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        assert "alert-triage" in out

    def test_run_demo_function_directly(self) -> None:
        payload = run_demo(skill="alert-triage", non_interactive=True)
        assert isinstance(payload, dict)
        assert payload["evidence_linked_finding"]["validation"]["valid"] is True
        assert payload["comparison"]["evidence_attribution"]["finding_contract"] == "100.0% (RFC 6901 grounded to evidence set)"
