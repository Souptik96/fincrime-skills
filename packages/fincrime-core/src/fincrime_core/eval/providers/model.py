"""Model provider adapter interface for live LLM evaluation runs.

Provides a pluggable adapter for connecting real model APIs (e.g., Anthropic,
OpenAI, Gemini, local LLM servers) to the evaluation harness while strictly
preserving standard-library runtime invariants (ADR-0002, ADR-0005).
"""

from __future__ import annotations

import json
from typing import Any, Callable, Mapping

from fincrime_core.eval.cases import Case
from fincrime_core.eval.providers.base import EvaluationProvider

__all__ = ["ModelProvider"]

ModelCallable = Callable[[str, Case, Mapping[str, Any] | None], dict[str, Any]]


class ModelProvider(EvaluationProvider):
    """Adapter for executing candidate generation via model functions or endpoints."""

    def __init__(
        self,
        model_name: str = "generic-model",
        generator: ModelCallable | None = None,
        endpoint_url: str | None = None,
        api_key: str | None = None,
        system_prompt: str | None = None,
    ) -> None:
        """Initialize the model provider adapter.

        Args:
            model_name: Name/identifier of the model under evaluation.
            generator: Pluggable callable that accepts (skill_name, case, manifest)
                and returns the candidate finding dict.
            endpoint_url: Optional HTTP endpoint URL for REST-based model servers.
            api_key: Optional API key or bearer token.
            system_prompt: Optional override for system instructions.
        """
        self.model_name = model_name
        self.generator = generator
        self.endpoint_url = endpoint_url
        self.api_key = api_key
        self.system_prompt = system_prompt

    def generate_finding(
        self,
        skill_name: str,
        case: Case,
        manifest: Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Generate a candidate finding by delegating to the model generator or endpoint."""
        if self.generator is not None:
            return self.generator(skill_name, case, manifest)

        if self.endpoint_url is not None:
            # Note: Network execution is disabled during air-gapped CI checks.
            # When run with live endpoints, this uses stdlib urllib.
            import urllib.request

            payload = {
                "skill": skill_name,
                "case_id": case.case_id,
                "input": case.document.get("input", {}),
                "model": self.model_name,
            }
            req = urllib.request.Request(
                self.endpoint_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            if self.api_key:
                req.add_header("Authorization", f"Bearer {self.api_key}")

            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, dict):
                return data
            raise ValueError(f"Endpoint returned invalid JSON structure: {type(data)}")

        raise NotImplementedError(
            f"ModelProvider({self.model_name!r}) requires either a generator callable "
            "or an active endpoint_url."
        )
