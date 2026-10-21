"""Tests for the expiry bot's filing behaviour.

The bot files one issue per stale record, addressed to the record's
maintainer. Two failure modes are pinned here, because both would mean the
refresh never reaches a human:

* GitHub's assignee field accepts individual logins only, so a maintainer
  handle that names a team has to be mentioned rather than assigned;
* an assignment that fails for any other reason must not stop the issue from
  being filed, because an unassigned issue that reaches a maintainer beats
  an issue that does not reach one at all.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
BOT_PATH = REPO_ROOT / "scripts" / "knowledge_expiry_bot.py"


def _load_bot() -> ModuleType:
    """Load the bot script as a module, the way CI runs it."""
    spec = importlib.util.spec_from_file_location("knowledge_expiry_bot", BOT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BOT = _load_bot()


class _Completed:
    """A stand-in for a ``subprocess.run`` result."""

    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _action(maintainer: str) -> dict[str, Any]:
    return {
        "issue_title": "knowledge: refresh IND-TEST (core-2026-10)",
        "issue_body": "The refresh diff.",
        "labels": ["knowledge/expired", "knowledge/indicator"],
        "maintainer": maintainer,
    }


class TestTeamHandles:
    def test_a_team_handle_is_recognised(self) -> None:
        assert BOT.is_team_handle("@fincrime-maintainers")
        assert BOT.is_team_handle("fincrime-maintainers")
        assert BOT.is_team_handle("@team-aml")
        assert not BOT.is_team_handle("@a.person")

    def test_a_team_is_mentioned_rather_than_assigned(self, monkeypatch) -> None:
        commands: list[list[str]] = []

        def fake_run(command, **kwargs):  # type: ignore[no-untyped-def]
            commands.append(command)
            return _Completed(0, stdout="https://example.test/issues/1")

        monkeypatch.setattr(BOT.subprocess, "run", fake_run)
        filed, _detail = BOT.file_issue(_action("@fincrime-maintainers"))

        assert filed is True
        assert len(commands) == 1
        command = commands[0]
        assert "--assignee" not in command
        assert "@fincrime-maintainers" in command[command.index("--body") + 1]

    def test_a_person_is_assigned(self, monkeypatch) -> None:
        commands: list[list[str]] = []

        def fake_run(command, **kwargs):  # type: ignore[no-untyped-def]
            commands.append(command)
            return _Completed(0, stdout="https://example.test/issues/1")

        monkeypatch.setattr(BOT.subprocess, "run", fake_run)
        filed, _detail = BOT.file_issue(_action("@a.person"))

        assert filed is True
        command = commands[0]
        assert command[command.index("--assignee") + 1] == "a.person"


class TestAssignmentFailure:
    def test_it_retries_without_the_assignee(self, monkeypatch) -> None:
        commands: list[list[str]] = []

        def fake_run(command, **kwargs):  # type: ignore[no-untyped-def]
            commands.append(command)
            if "--assignee" in command:
                return _Completed(1, stderr="failed to assign: not a user")
            return _Completed(0, stdout="https://example.test/issues/1")

        monkeypatch.setattr(BOT.subprocess, "run", fake_run)
        filed, detail = BOT.file_issue(_action("@a.person"))

        assert filed is True
        assert len(commands) == 2
        assert "--assignee" in commands[0]
        assert "--assignee" not in commands[1]
        assert detail == "https://example.test/issues/1"

    def test_an_issue_that_was_created_is_not_filed_twice(self, monkeypatch) -> None:
        commands: list[list[str]] = []

        def fake_run(command, **kwargs):  # type: ignore[no-untyped-def]
            commands.append(command)
            return _Completed(1, stdout="https://example.test/issues/1", stderr="assign failed")

        monkeypatch.setattr(BOT.subprocess, "run", fake_run)
        filed, detail = BOT.file_issue(_action("@a.person"))

        assert filed is True
        assert len(commands) == 1
        assert detail == "https://example.test/issues/1"

    def test_a_failure_that_is_not_about_the_assignment_is_reported(self, monkeypatch) -> None:
        def fake_run(command, **kwargs):  # type: ignore[no-untyped-def]
            return _Completed(1, stderr="could not resolve host")

        monkeypatch.setattr(BOT.subprocess, "run", fake_run)
        filed, detail = BOT.file_issue(_action("@a.person"))

        assert filed is False
        assert detail == "could not resolve host"


def test_a_dry_run_plans_the_issues_and_files_nothing(
    tmp_path: Path, monkeypatch, capsys: pytest.CaptureFixture
) -> None:
    """The bot asks the CLI for the plan and files nothing in a dry run."""
    from fincrime_core.knowledge.model import _file_sha256, _pack_checksum

    record = {
        "id": "IND-STALE",
        "type": "indicator",
        "pack": "core-2026-10",
        "version": "1.0.0",
        "title": "A stale indicator",
        "definition": "A pattern, described.",
        "prohibited_attributes": ["nationality"],
        "evidence_to_cite": ["the transaction records"],
        "benign_explanations": ["A legitimate business doing ordinary business."],
        "jurisdictions": ["US"],
        "sources": [{"citation": "A citation."}],
        "as_of": "2026-10-01",
        "review_by": "2027-04-01",
        "expires_at": "2027-10-01",
        "status": "active",
        "maintainer": "@fincrime-maintainers",
    }
    pack_dir = tmp_path / "packs" / "core-2026-10"
    relative = "records/indicator/IND-STALE.json"
    path = pack_dir / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    entries = [
        {
            "id": record["id"],
            "type": record["type"],
            "path": relative,
            "sha256": _file_sha256(path),
        }
    ]
    manifest = {
        "id": "core-2026-10",
        "version": "1.0.0",
        "as_of": "2026-10-01",
        "description": "A pack for testing.",
        "jurisdictions": ["US"],
        "maintainer": "@fincrime-maintainers",
        "records": entries,
        "checksum": _pack_checksum([(e["id"], e["sha256"]) for e in entries]),
    }
    (pack_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def refuse(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("a dry run must not file anything")

    monkeypatch.setattr(BOT, "file_issue", refuse)
    code = BOT.main(
        ["--packs", str(tmp_path / "packs"), "--as-of", "2027-11-01", "--dry-run"]
    )

    out = capsys.readouterr().out
    assert code == 0
    assert "would file: knowledge: refresh IND-STALE (core-2026-10)" in out
