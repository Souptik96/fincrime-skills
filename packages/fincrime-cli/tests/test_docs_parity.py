"""Tests for documentation parity and zero drift."""

from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.check_docs import extract_snippets, main as check_docs_main, run_check_docs


def test_docs_zero_drift() -> None:
    """All documentation snippets execute cleanly in an air-gapped sandbox."""
    passed, results = run_check_docs()
    assert passed, f"Documentation snippets failed: {[r.to_dict() for r in results if not r.passed]}"
    assert len(results) >= 20


def test_extract_snippets() -> None:
    """Snippets are correctly extracted from markdown files with line numbers."""
    readme_path = REPO_ROOT / "README.md"
    snippets = extract_snippets(readme_path)
    assert len(snippets) > 0
    languages = {s.language.lower() for s in snippets}
    assert "bash" in languages
    assert "python" in languages


def test_check_docs_cli_json() -> None:
    """The check_docs script CLI returns 0 and valid JSON report."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        exit_code = check_docs_main(["--json"])
    assert exit_code == 0
    payload = json.loads(buf.getvalue())
    assert payload["all_passed"] is True
    assert payload["failed_snippets"] == 0
    assert payload["total_snippets"] >= 20
