"""End-to-end tests for the ``fincrime`` command.

These run the command as a user runs it, and assert on what it prints and
what it returns, because a command that works but says nothing is not much
use to a contributor.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fincrime_cli.main import EXIT_FINDINGS, EXIT_OK, EXIT_USAGE, main

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_POLICY_SET = REPO_ROOT / "policies" / "default" / "policy-set.json"
GOLDEN_ARTIFACT = REPO_ROOT / "examples" / "01-alert-triage-structuring" / "artifact.json"
EVIDENCE_SET = REPO_ROOT / "examples" / "01-alert-triage-structuring" / "evidence-set.json"
REFERENCE_SKILL = REPO_ROOT / "skills" / "investigation-qa"
SAMPLE_PACK = REPO_ROOT / "knowledge" / "examples" / "sample-pack"
CORE_PACK = REPO_ROOT / "knowledge" / "packs" / "core-2026-10"


class TestNewSkill:
    def test_it_scaffolds_a_package(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        code = main(["new", "skill", "demo-skill", "--outdir", str(tmp_path)])
        assert code == EXIT_OK
        assert (tmp_path / "demo-skill" / "SKILL.md").exists()
        assert "Created" in capsys.readouterr().out

    def test_it_refuses_to_overwrite(self, tmp_path: Path) -> None:
        main(["new", "skill", "demo-skill", "--outdir", str(tmp_path)])
        assert main(["new", "skill", "demo-skill", "--outdir", str(tmp_path)]) == EXIT_USAGE


class TestValidate:
    def test_the_reference_skill_validates(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["validate", str(REFERENCE_SKILL)])
        out = capsys.readouterr().out
        assert code == EXIT_OK
        assert "0 error(s)" in out

    def test_a_scaffolded_skill_validates(self, tmp_path: Path) -> None:
        main(["new", "skill", "demo-skill", "--outdir", str(tmp_path)])
        assert main(["validate", str(tmp_path / "demo-skill")]) == EXIT_OK

    def test_the_json_output_is_machine_readable(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        main(["new", "skill", "demo-skill", "--outdir", str(tmp_path)])
        main(["validate", str(tmp_path / "demo-skill"), "--json"])
        out = capsys.readouterr().out
        start = out.index("{")
        document = json.loads(out[start:])
        assert document["valid"] is True
        assert isinstance(document["findings"], list)

    def test_a_path_that_does_not_exist_is_a_usage_error(self, tmp_path: Path) -> None:
        assert main(["validate", str(tmp_path / "nothing")]) == EXIT_USAGE

    def test_a_directory_that_is_nothing_in_particular_is_a_usage_error(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "empty").mkdir()
        assert main(["validate", str(tmp_path / "empty")]) == EXIT_USAGE

    def test_the_case_suite_validates(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["validate", str(SAMPLE_PACK)])
        out = capsys.readouterr().out
        assert code == EXIT_OK
        assert "checksum: ok" in out


class TestPolicy:
    def test_the_default_set_produces_no_violations_on_the_golden_artifact(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        code = main(
            [
                "policy",
                "check",
                "--set",
                str(DEFAULT_POLICY_SET),
                "--artifact",
                str(GOLDEN_ARTIFACT),
            ]
        )
        out = capsys.readouterr().out
        assert code == EXIT_OK
        assert "violations: 0" in out

    def test_an_export_round_trips(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        target = tmp_path / "exported.json"
        code = main(
            [
                "policy",
                "export",
                "--set",
                str(DEFAULT_POLICY_SET),
                "--out",
                str(target),
            ]
        )
        assert code == EXIT_OK
        document = json.loads(target.read_text(encoding="utf-8"))
        assert len(document["checksum"]) == 64
        # The exported set loads and verifies against its own checksum.
        assert main(["validate", str(target)]) == EXIT_OK


class TestKnowledge:
    def test_the_sample_pack_validates(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["knowledge", "validate", "--pack", str(SAMPLE_PACK)])
        assert code == EXIT_OK
        assert "checksum: ok" in capsys.readouterr().out

    def test_the_plan_is_empty_for_a_current_pack(self, capsys: pytest.CaptureFixture) -> None:
        code = main(
            ["knowledge", "check", "--pack", str(SAMPLE_PACK), "--as-of", "2026-10-21"]
        )
        out = capsys.readouterr().out
        assert code == EXIT_OK
        assert "stale: 0" in out

    def test_the_plan_lists_the_stale_records(self, capsys: pytest.CaptureFixture) -> None:
        code = main(
            ["knowledge", "check", "--pack", str(SAMPLE_PACK), "--as-of", "2028-01-01", "--json"]
        )
        out = capsys.readouterr().out
        assert code == EXIT_OK
        document = json.loads(out[out.index("{") :])
        assert len(document["actions"]) == 2
        assert document["as_of"] == "2028-01-01"

    def test_the_plan_is_deterministic(self, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
        main(["knowledge", "check", "--pack", str(SAMPLE_PACK), "--as-of", "2028-01-01", "--json"])
        first = capsys.readouterr().out
        main(["knowledge", "check", "--pack", str(SAMPLE_PACK), "--as-of", "2028-01-01", "--json"])
        second = capsys.readouterr().out
        assert first == second

    def test_an_expired_record_blocks_the_pack_in_promotion_context(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        code = main(
            [
                "knowledge",
                "validate",
                "--pack",
                str(SAMPLE_PACK),
                "--as-of",
                "2028-01-01",
                "--promotion",
            ]
        )
        out = capsys.readouterr().out
        assert code == EXIT_FINDINGS
        assert "pack_record_expired" in out
        assert "promotion" in out

    def test_the_same_pack_only_warns_in_the_release_context(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        code = main(
            ["knowledge", "validate", "--pack", str(SAMPLE_PACK), "--as-of", "2028-01-01"]
        )
        out = capsys.readouterr().out
        assert code == EXIT_OK
        assert "pack_record_expired" in out
        assert "0 error(s)" in out

    def test_the_json_output_carries_the_context_and_the_date(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        main(
            [
                "knowledge",
                "validate",
                "--pack",
                str(SAMPLE_PACK),
                "--as-of",
                "2028-01-01",
                "--promotion",
                "--json",
            ]
        )
        out = capsys.readouterr().out
        document = json.loads(out[out.index("{") :])
        assert document["context"] == "promotion"
        assert document["as_of"] == "2028-01-01"
        assert document["valid"] is False

    def test_the_core_pack_validates(self, capsys: pytest.CaptureFixture) -> None:
        code = main(["knowledge", "validate", "--pack", str(CORE_PACK)])
        out = capsys.readouterr().out
        assert code == EXIT_OK
        assert "records: 83" in out
        assert "checksum: ok" in out

    def test_the_core_pack_is_clean_in_the_promotion_context(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        code = main(
            [
                "knowledge",
                "validate",
                "--pack",
                str(CORE_PACK),
                "--as-of",
                "2026-10-21",
                "--promotion",
            ]
        )
        assert code == EXIT_OK
        assert "0 error(s)" in capsys.readouterr().out


class TestSkillKnowledgeGate:
    """The exit criterion of Phase 2, end to end.

    An expired record blocks its pack's promotion and fails the citing
    skill's CI gate in promotion context, while a released skill is warned
    rather than blocked.
    """

    def test_an_expired_record_fails_the_citing_skill_in_promotion_context(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        code = main(
            [
                "validate",
                str(REFERENCE_SKILL),
                "--promotion",
                "--as-of",
                "2027-11-01",
            ]
        )
        out = capsys.readouterr().out
        assert code == EXIT_FINDINGS
        assert "SKILL-KNOWLEDGE-EXPIRED" in out
        assert "promotion" in out

    def test_the_same_skill_is_only_warned_in_the_release_context(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        code = main(["validate", str(REFERENCE_SKILL), "--as-of", "2027-11-01"])
        out = capsys.readouterr().out
        assert code == EXIT_OK
        assert "SKILL-KNOWLEDGE-EXPIRED" in out
        assert "status: MAINTENANCE_REQUIRED" in out

    def test_the_skill_is_clean_while_its_knowledge_is_current(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        code = main(
            [
                "validate",
                str(REFERENCE_SKILL),
                "--promotion",
                "--as-of",
                "2026-10-21",
            ]
        )
        out = capsys.readouterr().out
        assert code == EXIT_OK
        assert "SKILL-KNOWLEDGE-EXPIRED" not in out
        assert "MAINTENANCE_REQUIRED" not in out


class TestArtifactKnowledgeChecks:
    """An artifact's citations are checked against the pack it declares."""

    def test_the_golden_artifact_is_clean_against_the_core_pack(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        code = main(
            [
                "validate",
                str(GOLDEN_ARTIFACT),
                "--evidence-set",
                str(EVIDENCE_SET),
                "--knowledge-pack",
                str(CORE_PACK),
            ]
        )
        out = capsys.readouterr().out
        assert code == EXIT_OK
        assert "valid: True" in out

    def test_an_indicator_the_pack_does_not_hold_is_a_defect(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        document = json.loads(GOLDEN_ARTIFACT.read_text(encoding="utf-8"))
        for claim in document["claims"]:
            if claim.get("indicator_ids"):
                claim["indicator_ids"] = ["IND-NOT-IN-THE-PACK"]
        target = tmp_path / "artifact.json"
        target.write_text(json.dumps(document, indent=2), encoding="utf-8")

        code = main(
            [
                "validate",
                str(target),
                "--evidence-set",
                str(EVIDENCE_SET),
                "--knowledge-pack",
                str(CORE_PACK),
            ]
        )
        out = capsys.readouterr().out
        assert code == EXIT_FINDINGS
        assert "unknown_indicator" in out


class TestParser:
    def test_no_arguments_prints_the_help(self, capsys: pytest.CaptureFixture) -> None:
        assert main([]) == EXIT_USAGE
        assert "usage" in capsys.readouterr().out.lower()

    def test_the_version_is_printed(self, capsys: pytest.CaptureFixture) -> None:
        assert main(["--version"]) == EXIT_OK
        assert "fincrime" in capsys.readouterr().out
