"""The policy set: a versioned, jurisdiction-scoped collection of rules.

A policy set is the artefact a firm hands to the engine and the artefact a
finding's ``provenance.policy_set`` reference names. It separates two kinds
of control that the manifest's flat list of policy ids had run together:

* **enforceable rules** — evaluated by code, in :mod:`fincrime_core.policy.evaluator`.
  A control a firm must be able to defend to a regulator lives here.
* **procedural policies** — followed by the agent as part of its procedure and
  measured by the evaluation suite. They are named in a skill's manifest, and
  the engine does not evaluate them.

The set carries a checksum over its own contents, so a reader can establish
that the rules that produced a verdict are the rules they have.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

from fincrime_core.paths import contracts_dir
from fincrime_core.policy.evaluator import PolicyRule
from fincrime_core.provenance.hashing import canonical_json, sha256_hex
from fincrime_core.validate.schema import JsonSchemaValidator, load_registry

__all__ = [
    "ProceduralPolicy",
    "PolicySet",
    "load_policy_set",
    "parse_policy_set",
    "export_policy_set",
    "policy_set_checksum",
    "load_policy_set_schema",
]


@dataclass(frozen=True, slots=True)
class ProceduralPolicy:
    """A policy the agent follows and the evaluation suite measures."""

    id: str
    version: str
    severity: str
    description: str
    check: str
    on_violation: str
    measured_by: str
    jurisdictions: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        document: dict[str, Any] = {
            "id": self.id,
            "version": self.version,
            "severity": self.severity,
            "description": self.description,
            "check": self.check,
            "on_violation": self.on_violation,
            "measured_by": self.measured_by,
        }
        if self.jurisdictions:
            document["jurisdictions"] = list(self.jurisdictions)
        return document


@dataclass(frozen=True, slots=True)
class PolicySet:
    """A versioned set of enforceable rules and procedural policies."""

    id: str
    version: str
    as_of: str
    description: str
    jurisdictions: tuple[str, ...]
    rules: tuple[PolicyRule, ...]
    procedural_policies: tuple[ProceduralPolicy, ...] = ()
    checksum: str = ""
    notes: str | None = None

    def rule_ids(self) -> tuple[str, ...]:
        return tuple(rule.id for rule in self.rules)

    def procedural_policy_ids(self) -> tuple[str, ...]:
        return tuple(policy.id for policy in self.procedural_policies)

    def policy_ids(self) -> tuple[str, ...]:
        """Every policy id this set defines, enforceable or procedural."""
        return self.rule_ids() + self.procedural_policy_ids()

    def has_policy(self, policy_id: str) -> bool:
        return policy_id in self.policy_ids()

    def to_dict(self) -> dict[str, Any]:
        document: dict[str, Any] = {
            "id": self.id,
            "version": self.version,
            "as_of": self.as_of,
            "description": self.description,
            "jurisdictions": list(self.jurisdictions),
            "rules": [rule_to_dict(rule) for rule in self.rules],
        }
        if self.procedural_policies:
            document["procedural_policies"] = [
                policy.to_dict() for policy in self.procedural_policies
            ]
        if self.notes:
            document["notes"] = self.notes
        document["checksum"] = self.checksum
        return document


def rule_to_dict(rule: PolicyRule) -> dict[str, Any]:
    """Render a rule back into its contract shape."""
    document: dict[str, Any] = {
        "id": rule.id,
        "version": rule.version,
        "severity": rule.severity,
        "description": rule.description,
        "kind": rule.kind,
        "rule": dict(rule.rule),
        "message": rule.message,
    }
    if rule.applies_to:
        document["applies_to"] = list(rule.applies_to)
    if rule.jurisdictions:
        document["jurisdictions"] = list(rule.jurisdictions)
    if rule.when is not None:
        document["when"] = dict(rule.when)
    return document


def policy_set_checksum(document: Mapping[str, Any]) -> str:
    """The checksum of a policy set document.

    The checksum covers the whole document except the checksum field itself,
    so any change to a rule, a version or a date changes the checksum.
    """
    payload = {key: value for key, value in document.items() if key != "checksum"}
    return sha256_hex(canonical_json(payload))


@lru_cache(maxsize=1)
def load_policy_set_schema() -> JsonSchemaValidator:
    """The normative schema for a policy set, with the contract registry loaded."""
    with (contracts_dir() / "policy-set.schema.json").open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    return JsonSchemaValidator(schema, registry=load_registry(contracts_dir()))


def _parse_rule(entry: Mapping[str, Any]) -> PolicyRule:
    return PolicyRule(
        id=str(entry["id"]),
        version=str(entry.get("version", "1.0.0")),
        severity=str(entry.get("severity", "error")),
        description=str(entry.get("description", "")),
        kind=str(entry["kind"]),
        rule=entry.get("rule") or {},
        message=str(entry.get("message", "")),
        applies_to=tuple(entry.get("applies_to") or ()),
        jurisdictions=tuple(entry.get("jurisdictions") or ()),
        when=entry.get("when"),
    )


def _parse_procedural(entry: Mapping[str, Any]) -> ProceduralPolicy:
    return ProceduralPolicy(
        id=str(entry["id"]),
        version=str(entry.get("version", "1.0.0")),
        severity=str(entry.get("severity", "error")),
        description=str(entry.get("description", "")),
        check=str(entry.get("check", "")),
        on_violation=str(entry.get("on_violation", "stop")),
        measured_by=str(entry.get("measured_by", "")),
        jurisdictions=tuple(entry.get("jurisdictions") or ()),
    )


def parse_policy_set(document: Mapping[str, Any]) -> PolicySet:
    """Parse a policy set document into its typed form.

    The document is assumed to have been validated against the contract; this
    function does not re-check it, it only reads.
    """
    rules = tuple(_parse_rule(entry) for entry in document.get("rules") or ())
    procedural = tuple(
        _parse_procedural(entry) for entry in document.get("procedural_policies") or ()
    )
    return PolicySet(
        id=str(document.get("id", "")),
        version=str(document.get("version", "")),
        as_of=str(document.get("as_of", "")),
        description=str(document.get("description", "")),
        jurisdictions=tuple(document.get("jurisdictions") or ()),
        rules=rules,
        procedural_policies=procedural,
        checksum=str(document.get("checksum", "")),
        notes=document.get("notes"),
    )


def load_policy_set(path: str | Path) -> PolicySet:
    """Load a policy set from a JSON file.

    The file is validated against ``contracts/policy-set.schema.json`` before
    it is parsed, so a malformed rule is a schema error rather than a
    surprising evaluation result. A set that carries a checksum is verified
    against it: a set whose rules have drifted from the checksum is not the
    set somebody reviewed.
    """
    with Path(path).open("r", encoding="utf-8") as handle:
        document = json.load(handle)
    errors = load_policy_set_schema().validate(document)
    if errors:
        detail = "; ".join(f"{error.path}: {error.message}" for error in errors)
        raise ValueError(f"policy set {path} does not satisfy the contract: {detail}")

    declared = str(document.get("checksum", ""))
    if declared:
        computed = policy_set_checksum(document)
        if computed != declared:
            raise ValueError(
                f"policy set {path} does not match its checksum "
                f"(declared {declared}, computed {computed})"
            )

    return parse_policy_set(document)


def export_policy_set(policy_set: PolicySet) -> dict[str, Any]:
    """Render a policy set for export, with its checksum recomputed."""
    document = policy_set.to_dict()
    document["checksum"] = ""
    document["checksum"] = policy_set_checksum(document)
    return document


def merge_policy_sets(*policy_sets: PolicySet) -> PolicySet:
    """Combine policy sets, with later sets overriding earlier rules by id.

    A firm set overrides the default set rule by rule, not wholesale: a firm
    that tightens one control does not silently lose the others.
    """
    rules: dict[str, PolicyRule] = {}
    procedural: dict[str, ProceduralPolicy] = {}
    for policy_set in policy_sets:
        for rule in policy_set.rules:
            rules[rule.id] = rule
        for policy in policy_set.procedural_policies:
            procedural[policy.id] = policy
    first = policy_sets[0] if policy_sets else None
    return PolicySet(
        id=first.id if first else "",
        version=first.version if first else "",
        as_of=first.as_of if first else "",
        description=first.description if first else "",
        jurisdictions=first.jurisdictions if first else (),
        rules=tuple(rules[rule_id] for rule_id in sorted(rules)),
        procedural_policies=tuple(procedural[policy_id] for policy_id in sorted(procedural)),
        checksum=first.checksum if first else "",
    )


def resolve_policy_ids(policy_set: PolicySet, policy_ids: Sequence[str]) -> tuple[str, ...]:
    """Return the ids in ``policy_ids`` that the set does not define."""
    known = set(policy_set.policy_ids())
    return tuple(policy_id for policy_id in policy_ids if policy_id not in known)
