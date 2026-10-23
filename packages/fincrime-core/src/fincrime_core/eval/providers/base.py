"""Base interface for evaluation candidate finding providers.

Every provider adapter implements ``EvaluationProvider``, producing candidate
finding documents for a given evaluation case.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping

from fincrime_core.eval.cases import Case

__all__ = ["EvaluationProvider"]


class EvaluationProvider(ABC):
    """Abstract provider that generates candidate findings for evaluation cases."""

    @abstractmethod
    def generate_finding(
        self,
        skill_name: str,
        case: Case,
        manifest: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate or retrieve a candidate finding document for a given case.

        Args:
            skill_name: The name of the skill under evaluation.
            case: The Case instance containing input and expectations.
            manifest: The optional parsed skill manifest (fincrime.skill.yaml).
            **kwargs: Additional runtime provider parameters.

        Returns:
            A candidate finding dictionary adhering to fincrime/finding/1.0.0.
        """
        raise NotImplementedError
