"""Tests for the enhanced ``fincrime knowledge`` and ``fincrime policy`` CLI suites."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fincrime_cli.main import EXIT_FINDINGS, EXIT_OK, EXIT_USAGE, main

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_POLICY_SET = REPO_ROOT / "policies" / "default" / "policy-set.json"
GOLDEN_ARTIFACT = REPO_ROOT / "examples" / "01-alert-triage-structuring" / "artifact.json"
CORE_PACK = REPO_ROOT / "knowledge" / "packs" / "core-2026-10"


class TestKnowledgeCli:
    def test_knowledge_list(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["knowledge", "list"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        assert "FINCRIME KNOWLEDGE PACKS REGISTRY" in out
        assert "core-2026-10" in out
        assert "OK" in out

    def test_knowledge_list_json(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["knowledge", "list", "--json"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        packs = json.loads(out)
        assert isinstance(packs, list)
        assert len(packs) >= 1
        core = next(p for p in packs if p["id"] == "core-2026-10")
        assert core["total_records"] >= 40
        assert core["indicators"] >= 20
        assert core["checksum_valid"] is True

    def test_knowledge_inspect_indicator(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["knowledge", "inspect", "--indicator", "IND-STRUCT-THRESHOLD-PROXIMITY"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        assert "IND-STRUCT-THRESHOLD-PROXIMITY" in out
        assert "Cash deposits clustered immediately below" in out
        assert "TYP-STRUCTURING-SMURFING" in out

    def test_knowledge_inspect_json(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["knowledge", "inspect", "--indicator", "IND-STRUCT-THRESHOLD-PROXIMITY", "--json"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        record = json.loads(out)
        assert record["id"] == "IND-STRUCT-THRESHOLD-PROXIMITY"
        assert record["type"] == "indicator"
        assert "TYP-STRUCTURING-SMURFING" in record["typology_refs"]
        assert len(record["benign_explanations"]) >= 1

    def test_knowledge_inspect_unknown(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["knowledge", "inspect", "--indicator", "IND-NONEXISTENT-999"])
        assert code == EXIT_USAGE
        err = capsys.readouterr().err
        assert "not found" in err

    def test_knowledge_typologies(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["knowledge", "typologies"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        assert "FINCRIME 12-TYPOLOGY MATRIX & BENIGN LOOKALIKE TWINS" in out
        assert "TYP-STRUCTURING-SMURFING" in out
        assert "BENIGN-STRUCTURING-HARVEST" in out
        assert "TYP-MULE-ACCOUNT-NETWORK" in out
        assert "Total Typologies: 12 AML/CTF" in out

    def test_knowledge_typologies_json(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["knowledge", "typologies", "--json"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        matrix = json.loads(out)
        assert isinstance(matrix, list)
        assert len(matrix) == 12
        ids = {t["id"] for t in matrix}
        assert "TYP-STRUCTURING-SMURFING" in ids
        assert "TYP-TRADE-BASED-MONEY-LAUNDERING" in ids
        assert "TYP-TRANSSHIPMENT-SANCTIONS-EVASION" in ids


class TestPolicyCli:
    def test_policy_list(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["policy", "list"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        assert "FINCRIME POLICY SETS REGISTRY" in out
        assert "fincrime/default" in out
        assert "POL-BENIGN-HYPOTHESIS-REQUIRED" in out

    def test_policy_list_json(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["policy", "list", "--json"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        sets = json.loads(out)
        assert isinstance(sets, list)
        assert len(sets) >= 1
        default_set = next(s for s in sets if s["id"] == "fincrime/default")
        assert default_set["rules_count"] >= 6

    def test_policy_check_inspection_only(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["policy", "check", "--set", "default"])
        assert code == EXIT_OK
        out = capsys.readouterr().out
        assert "policy set:" in out
        assert "rules: 6" in out

    def test_policy_check_with_artifact(self, capsys: pytest.CaptureFixture) -> None:
        code = main(
            [
                "policy",
                "check",
                "--set",
                "default",
                "--artifact",
                str(GOLDEN_ARTIFACT),
            ]
        )
        assert code == EXIT_OK
        out = capsys.readouterr().out
        assert "violations: 0" in out
