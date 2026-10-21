"""The GitHub Actions workflows are themselves a contract.

A workflow file with a syntax error, or with a job whose keys were lost, is
a workflow that never runs — and it never runs *silently*: the checks it was
supposed to perform simply stop happening, and nothing fails. That is the
worst possible failure mode for a CI gate, and it is invisible to every other
test in this repository, because nothing else reads these files.

So they are parsed here, and the structure that matters is asserted: a
workflow is a mapping, it declares jobs, and every job has a runner and at
least one step. A job that lost its steps — which is how a job that
accidentally swallowed its neighbour's keys looks — fails here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS = sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml"))


def _load(path: Path) -> Any:
    yaml = pytest.importorskip("yaml", reason="PyYAML is not installed")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def test_there_are_workflows_to_check() -> None:
    assert WORKFLOWS, "no workflow files were found"


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda path: path.name)
def test_a_workflow_is_a_mapping_of_jobs(path: Path) -> None:
    document = _load(path)
    assert isinstance(document, dict), f"{path.name} is not a YAML mapping"
    jobs = document.get("jobs")
    assert isinstance(jobs, dict) and jobs, f"{path.name} declares no jobs"


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda path: path.name)
def test_every_job_has_a_runner_and_at_least_one_step(path: Path) -> None:
    document = _load(path)
    for name, job in document["jobs"].items():
        assert isinstance(job, dict), f"{path.name}: job {name!r} is not a mapping"
        assert job.get("runs-on"), f"{path.name}: job {name!r} has no runner"
        steps = job.get("steps")
        assert isinstance(steps, list), f"{path.name}: job {name!r} has no steps"
        assert steps, f"{path.name}: job {name!r} has an empty step list"
        for step in steps:
            assert isinstance(step, dict), f"{path.name}: job {name!r} has a malformed step"
            assert "uses" in step or "run" in step, (
                f"{path.name}: job {name!r} has a step that neither uses nor runs anything"
            )


def test_the_ci_workflow_keeps_its_jobs() -> None:
    """The jobs CI is expected to run, by name.

    A job that disappears from a workflow file is a check that stopped
    happening, and it is exactly as silent as a job that lost its steps.
    """
    document = _load(REPO_ROOT / ".github" / "workflows" / "ci.yml")
    assert set(document["jobs"]) == {"contract", "cli", "matrix", "promotion", "security"}


def test_the_matrix_job_keeps_its_version_strategy() -> None:
    document = _load(REPO_ROOT / ".github" / "workflows" / "ci.yml")
    strategy = document["jobs"]["matrix"]["strategy"]
    assert strategy["fail-fast"] is False
    assert strategy["matrix"]["python-version"] == ["3.10", "3.11", "3.12", "3.13"]


def test_the_promotion_job_makes_no_network_call() -> None:
    """The promotion gate is offline: it diffs the checkout, it does not call the API."""
    document = _load(REPO_ROOT / ".github" / "workflows" / "ci.yml")
    steps = document["jobs"]["promotion"]["steps"]
    scripts = "\n".join(step.get("run", "") for step in steps)
    assert "gh api" not in scripts
    assert "git diff" in scripts
    assert not any("GH_TOKEN" in step.get("env", {}) for step in steps)
