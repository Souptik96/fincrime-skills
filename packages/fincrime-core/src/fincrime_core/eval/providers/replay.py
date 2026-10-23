"""Offline replay provider for evaluation runs.

Replays pre-recorded, committed candidate findings for test cases offline.
Requires zero network sockets and zero external API keys, fulfilling the
offline CI gate requirement (ADR-0005).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from fincrime_core.eval.cases import Case
from fincrime_core.eval.providers.base import EvaluationProvider

__all__ = ["ReplayProvider"]


class ReplayProvider(EvaluationProvider):
    """Replays pre-recorded candidate findings from disk or memory."""

    def __init__(
        self,
        replay_dir: str | Path | None = None,
        replays: Mapping[str, dict[str, Any]] | None = None,
    ) -> None:
        """Initialize the replay provider.

        Args:
            replay_dir: Path to directory holding replay JSON files.
            replays: Optional dictionary mapping case_id to candidate finding dict.
        """
        self.replay_dir = Path(replay_dir) if replay_dir is not None else None
        self._replays = dict(replays) if replays is not None else {}

    def generate_finding(
        self,
        skill_name: str,
        case: Case,
        manifest: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Retrieve pre-recorded finding for the case."""
        case_id = case.case_id
        if case_id in self._replays:
            return self._replays[case_id]

        if self.replay_dir is not None:
            # Check candidate paths:
            # 1. replay_dir / f"{case_id}.json"
            # 2. replay_dir / skill_name / f"{case_id}.json"
            candidates = [
                self.replay_dir / f"{case_id}.json",
                self.replay_dir / skill_name / f"{case_id}.json",
            ]
            for candidate in candidates:
                if candidate.is_file():
                    with candidate.open("r", encoding="utf-8") as handle:
                        data = json.load(handle)
                    if isinstance(data, dict):
                        return data

            raise FileNotFoundError(
                f"Replay finding not found for case {case_id!r} under {self.replay_dir}"
            )

        raise KeyError(f"No replay finding available for case {case_id!r}")
