"""The skill manifest: the machine-readable contract of a skill.

The manifest is the sidecar of an Agent Skills package. It is additive: a
host that knows nothing about FinCrime loads ``SKILL.md`` and works. This
module owns the *contract* — the schema, the typed view of a manifest, and
the checks that the sidecar and the body agree with each other.

The format of the file (YAML) is not owned here. The core parses manifests
that are already in memory, so that the zero-dependency core never needs a
YAML parser; the CLI owns the reading of the file and hands the document
over.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Mapping, Sequence

from fincrime_core.contract.model import FINDING_ELEMENTS
from fincrime_core.paths import contracts_dir
from fincrime_core.validate.schema import JsonSchemaValidator, SchemaError

__all__ = [
    "SkillManifest",
    "ManifestFinding",
    "load_skill_manifest_schema",
    "validate_skill_manifest",
    "parse_skill_manifest",
    "check_manifest_consistency",
]


@lru_cache(maxsize=1)
def load_skill_manifest_schema() -> JsonSchemaValidator:
    """The normative schema for a skill manifest."""
    with (contracts_dir() / "skill-manifest.schema.json").open("r", encoding="utf-8") as handle:
        return JsonSchemaValidator(json.load(handle))


@dataclass(frozen=True, slots=True)
class ManifestFinding:
    """One problem with a skill manifest."""

    code: str
    severity: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "severity": self.severity, "message": self.message}


@dataclass(frozen=True, slots=True)
class SkillManifest:
    """A parsed skill manifest."""

    name: str
    version: str
    status: str
    owners: tuple[str, ...]
    license: str
    jurisdiction_scope: tuple[str, ...]
    contract_version: str
    knowledge_pack: str
    related_skills: tuple[str, ...]
    purpose: str
    required_inputs: tuple[str, ...]
    optional_inputs: tuple[str, ...]
    preconditions: tuple[Mapping[str, Any], ...]
    stages: tuple[Mapping[str, Any], ...]
    required_claims: tuple[str, ...]
    optional_claims: tuple[str, ...]
    prohibited_claims: tuple[str, ...]
    required_policies: tuple[str, ...]
    optional_policies: tuple[str, ...]
    evaluation_suite: str
    evaluation_case_count_min: int
    evaluation_gates: Mapping[str, float]
    knowledge: Mapping[str, Any]
    safety: Mapping[str, Any]
    document: Mapping[str, Any] = None  # type: ignore[assignment]

    @property
    def is_stable(self) -> bool:
        return self.status == "stable"

    def policy_ids(self) -> tuple[str, ...]:
        """Every policy id the manifest names, required and optional."""
        return self.required_policies + self.optional_policies

    def guard_ids(self) -> tuple[str, ...]:
        """The policy ids the procedure's stages use as guards."""
        return tuple(
            str(stage["guard"]) for stage in self.stages if stage.get("guard")
        )


def validate_skill_manifest(document: Mapping[str, Any]) -> list[SchemaError]:
    """Validate a manifest document against the contract."""
    return load_skill_manifest_schema().validate(document)


def _as_str_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(str(item) for item in value)
    return ()


def parse_skill_manifest(document: Mapping[str, Any]) -> SkillManifest:
    """Parse a manifest document into its typed form.

    The document is assumed to have been validated against the contract.
    """
    metadata = document.get("metadata") or {}
    spec = document.get("spec") or {}
    inputs = spec.get("inputs") or {}
    output = spec.get("output") or {}
    policies = spec.get("policies") or {}
    evaluation = spec.get("evaluation") or {}

    return SkillManifest(
        name=str(metadata.get("name", "")),
        version=str(metadata.get("version", "")),
        status=str(metadata.get("status", "draft")),
        owners=_as_str_tuple(metadata.get("owners")),
        license=str(metadata.get("license", "")),
        jurisdiction_scope=_as_str_tuple(metadata.get("jurisdiction_scope")),
        contract_version=str(metadata.get("contract_version", "")),
        knowledge_pack=str(metadata.get("knowledge_pack", "")),
        related_skills=tuple(
            part.strip()
            for part in str(metadata.get("related_skills", "")).split(",")
            if part.strip()
        ),
        purpose=str(spec.get("purpose", "")),
        required_inputs=tuple(
            str(item.get("name", ""))
            for item in inputs.get("required") or ()
            if isinstance(item, Mapping)
        ),
        optional_inputs=tuple(
            str(item.get("name", ""))
            for item in inputs.get("optional") or ()
            if isinstance(item, Mapping)
        ),
        preconditions=tuple(spec.get("preconditions") or ()),
        stages=tuple(spec.get("procedure") or ()),
        required_claims=_as_str_tuple(output.get("required_claims")),
        optional_claims=_as_str_tuple(output.get("optional_claims")),
        prohibited_claims=_as_str_tuple(output.get("prohibited_claims")),
        required_policies=_as_str_tuple(policies.get("required")),
        optional_policies=_as_str_tuple(policies.get("optional")),
        evaluation_suite=str(evaluation.get("suite", "")),
        evaluation_case_count_min=int(evaluation.get("case_count_min", 0) or 0),
        evaluation_gates=dict(evaluation.get("gates") or {}),
        knowledge=dict(spec.get("knowledge") or {}),
        safety=dict(spec.get("safety") or {}),
        document=document,
    )


def check_manifest_consistency(manifest: SkillManifest) -> list[ManifestFinding]:
    """Check the manifest against itself and against the output vocabulary.

    These are the checks a JSON Schema cannot express: an output element that
    is not one of the Finding Contract's, an element that is both required
    and prohibited, a stage that produces something the output does not
    allow.
    """
    findings: list[ManifestFinding] = []

    for element in (
        manifest.required_claims + manifest.optional_claims + manifest.prohibited_claims
    ):
        if element not in FINDING_ELEMENTS:
            findings.append(
                ManifestFinding(
                    code="SKILL-OUTPUT-ELEMENT-UNKNOWN",
                    severity="error",
                    message=(
                        f"{element!r} is not an element of the Finding Contract "
                        f"({', '.join(FINDING_ELEMENTS)})"
                    ),
                )
            )

    overlap = sorted(set(manifest.required_claims) & set(manifest.prohibited_claims))
    if overlap:
        findings.append(
            ManifestFinding(
                code="SKILL-OUTPUT-ELEMENT-CONTRADICTORY",
                severity="error",
                message=(
                    f"{', '.join(overlap)} is both required and prohibited. A skill cannot be "
                    "required to produce and forbidden to produce the same element."
                ),
            )
        )

    allowed = set(manifest.required_claims) | set(manifest.optional_claims)
    for stage in manifest.stages:
        produces = stage.get("produces") or ()
        for produced in produces:
            if produced not in allowed:
                findings.append(
                    ManifestFinding(
                        code="SKILL-STAGE-PRODUCES-UNKNOWN-ELEMENT",
                        severity="error",
                        message=(
                            f"stage {stage.get('stage', '?')} produces {produced!r}, which the output "
                            "block does not allow. Every claim a stage produces must be required or optional."
                        ),
                    )
                )

    if not manifest.evaluation_suite:
        findings.append(
            ManifestFinding(
                code="SKILL-EVALUATION-SUITE-MISSING",
                severity="error",
                message="the manifest names no evaluation suite. A skill without a suite has no gate.",
            )
        )

    if not manifest.jurisdiction_scope:
        findings.append(
            ManifestFinding(
                code="SKILL-JURISDICTION-SCOPE-EMPTY",
                severity="error",
                message=(
                    "the manifest declares no jurisdiction scope. Regulatory content is never "
                    "jurisdiction-agnostic."
                ),
            )
        )

    return findings
