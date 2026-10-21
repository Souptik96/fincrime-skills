"""The deterministic policy evaluator.

Per ADR-0003, this is the layer that owns **enforceable controls**. The rules
are data (JSON, schema-validated against ``contracts/policy-rule.schema.json``),
not code, so a compliance engineer can read them and a firm can version them
independently of the engine.

The evaluator is a pure function: ``(rules, artifact) -> violations``. No clock,
no network, no filesystem, no randomness, no global state. The same rules and
the same artifact always produce the same violations in the same order.

Six rule kinds are supported, and no rule kind contains a free-text expression.
If a constraint cannot be evaluated by code, it does not belong here — it belongs
in the skill body and is measured by the evaluation suite instead.

Three additions to the rule model, all of them semantic changes to an
enforceable control (ADR-0003):

* ``when`` — an artifact-level gate. A rule that reaches a property of the
  artifact header rather than of a claim (``artifact.completeness``,
  ``provenance.knowledge_pack.stale``) has no other way to be expressed.
* ``require.any_of`` — a per-claim disjunction. ``composite.any`` aggregates
  across the whole selected set, so it cannot say "this claim has evidence
  references *or* is stated as insufficient information"; ``any_of`` is
  decided claim by claim.
* ``pattern`` is a regular expression, not a substring. A field named
  ``pattern`` that does substring matching is a contract that lies to whoever
  writes the rule.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from fincrime_core.contract.model import Claim, Finding
from fincrime_core.validate.culpability import CulpabilityMatcher

__all__ = ["PolicyRule", "PolicyViolation", "PolicyEvaluator", "load_rules"]


@dataclass(frozen=True, slots=True)
class PolicyRule:
    """A single deterministic rule."""

    id: str
    version: str
    severity: str
    description: str
    kind: str
    rule: Mapping[str, Any]
    message: str
    applies_to: tuple[str, ...] = ()
    jurisdictions: tuple[str, ...] = ()
    when: Mapping[str, Any] | None = None

    def applies_to_artifact(self, finding: Finding) -> bool:
        """True when this rule governs the given artifact."""
        if self.applies_to and finding.artifact.skill_id not in self.applies_to:
            return False
        if self.jurisdictions:
            artifact_jurisdictions = set(finding.artifact.jurisdictions)
            if not artifact_jurisdictions & set(self.jurisdictions):
                return False
        return True


@dataclass(frozen=True, slots=True)
class PolicyViolation:
    """A rule that the artifact failed."""

    rule_id: str
    severity: str
    message: str
    claim_id: str | None = None

    def sort_key(self) -> tuple[str, str, str]:
        severity_rank = {"error": 0, "warn": 1, "info": 2}
        return (severity_rank.get(self.severity, 3), self.rule_id, self.claim_id or "")


def load_rules(path: str | Path) -> tuple[PolicyRule, ...]:
    """Load policy rules from a JSON file.

    The file is either a single rule object or a list of rule objects.
    """
    with Path(path).open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    entries = raw if isinstance(raw, list) else raw.get("rules", [raw])
    rules: list[PolicyRule] = []
    for entry in entries:
        rules.append(
            PolicyRule(
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
        )
    return tuple(rules)


def _matches_where(claim: Claim, where: Mapping[str, Any]) -> bool:
    """Test a claim against a ``where`` filter.

    Every present filter must match (conjunctive). An absent filter matches
    everything.
    """
    if "claim_class" in where:
        classes = where["claim_class"]
        if isinstance(classes, str):
            classes = [classes]
        if claim.class_ not in classes:
            return False
    if "epistemic_type" in where:
        types = where["epistemic_type"]
        if isinstance(types, str):
            types = [types]
        if claim.epistemic_type not in types:
            return False
    if "confidence_level" in where:
        levels = where["confidence_level"]
        if isinstance(levels, str):
            levels = [levels]
        if claim.confidence.level not in levels:
            return False
    if "field" in where:
        field = where["field"]
        if not _claim_field(claim, field):
            return False
    if "has_field" in where:
        if not _claim_field(claim, where["has_field"]):
            return False
    return True


def _claim_field(claim: Claim, field: str) -> Any:
    """Read a field from a claim by dotted path."""
    current: Any = claim
    for part in field.split("."):
        if isinstance(current, Mapping):
            current = current.get(part)
        else:
            current = getattr(current, part, None)
        if current is None:
            return None
    return current


def _artifact_field(finding: Finding, field: str) -> Any:
    """Read a field from the finding itself by dotted path.

    This is how a rule reaches the artifact header — ``artifact.completeness``,
    ``artifact.jurisdictions``, ``provenance.knowledge_pack.stale`` — rather
    than a property of one claim.
    """
    current: Any = finding
    for part in field.split("."):
        if current is None:
            return None
        if isinstance(current, Mapping):
            current = current.get(part)
        else:
            current = getattr(current, part, None)
    return current


def _when_applies(when: Mapping[str, Any], finding: Finding) -> bool:
    """Test an artifact-level gate.

    Every predicate present must hold. An absent predicate holds vacuously,
    so a gate with one predicate is the common case.
    """
    value = _artifact_field(finding, str(when.get("field", "")))

    if "equals" in when and value != when["equals"]:
        return False
    if "not_equals" in when and value == when["not_equals"]:
        return False
    if "in" in when:
        options = when["in"] if isinstance(when["in"], (list, tuple)) else [when["in"]]
        if value not in options:
            return False
    if "not_in" in when:
        options = when["not_in"] if isinstance(when["not_in"], (list, tuple)) else [when["not_in"]]
        if value in options:
            return False
    if "contains" in when:
        if not isinstance(value, (list, tuple, set, str)):
            return False
        if when["contains"] not in value:
            return False
    if "matches" in when:
        if not isinstance(value, str):
            return False
        try:
            matched = re.search(str(when["matches"]), value, re.IGNORECASE) is not None
        except re.error:
            return False
        if not matched:
            return False
    return True


class PolicyEvaluator:
    """Evaluates policy rules against a finding."""

    __slots__ = ("_rules",)

    def __init__(self, rules: Iterable[PolicyRule]) -> None:
        self._rules = tuple(rules)

    @property
    def rules(self) -> tuple[PolicyRule, ...]:
        return self._rules

    def evaluate(self, finding: Finding) -> list[PolicyViolation]:
        """Evaluate every applicable rule. Never raises."""
        violations: list[PolicyViolation] = []
        for rule in self._rules:
            if not rule.applies_to_artifact(finding):
                continue
            try:
                violations.extend(self._evaluate_rule(rule, finding))
            except Exception as exc:  # pragma: no cover - defensive: a rule must never break validation
                violations.append(
                    PolicyViolation(
                        rule_id=rule.id,
                        severity="warn",
                        message=f"Rule {rule.id} could not be evaluated and was skipped: {exc}",
                    )
                )
        return sorted(violations, key=lambda v: v.sort_key())

    def _evaluate_rule(self, rule: PolicyRule, finding: Finding) -> list[PolicyViolation]:
        if rule.when is not None and not _when_applies(rule.when, finding):
            return []
        handler = {
            "require": self._eval_require,
            "forbid": self._eval_forbid,
            "threshold": self._eval_threshold,
            "count": self._eval_count,
            "consistency": self._eval_consistency,
            "composite": self._eval_composite,
        }.get(rule.kind)
        if handler is None:
            return []
        return handler(rule, finding)

    def _selected_claims(self, rule: PolicyRule, finding: Finding) -> list[Claim]:
        where = rule.rule.get("where") or {}
        claims = list(finding.claims)
        if not where:
            return claims
        return [claim for claim in claims if _matches_where(claim, where)]

    def _eval_require(self, rule: PolicyRule, finding: Finding) -> list[PolicyViolation]:
        where = rule.rule.get("where") or {}
        field = rule.rule.get("field")
        min_items = rule.rule.get("min_items")
        required = rule.rule.get("required")
        any_of = rule.rule.get("any_of")
        violations: list[PolicyViolation] = []

        if any_of is not None:
            for claim in self._selected_claims(rule, finding):
                if not self._claim_satisfies_any(rule, claim, any_of, finding):
                    violations.append(
                        PolicyViolation(
                            rule_id=rule.id,
                            severity=rule.severity,
                            message=rule.message or "The claim does not satisfy any permitted alternative.",
                            claim_id=claim.id,
                        )
                    )
            return violations

        if field and min_items is not None:
            for claim in self._selected_claims(rule, finding):
                value = _claim_field(claim, field)
                length = len(value) if isinstance(value, (list, tuple, str, Mapping)) else 0
                if length < min_items:
                    violations.append(
                        PolicyViolation(
                            rule_id=rule.id,
                            severity=rule.severity,
                            message=rule.message or f"{field} must have at least {min_items} entries.",
                            claim_id=claim.id,
                        )
                    )
        elif required:
            for claim in self._selected_claims(rule, finding):
                if not _claim_field(claim, required):
                    violations.append(
                        PolicyViolation(
                            rule_id=rule.id,
                            severity=rule.severity,
                            message=rule.message or f"{required} is required.",
                            claim_id=claim.id,
                        )
                    )
        return violations

    def _claim_satisfies_any(
        self,
        rule: PolicyRule,
        claim: Claim,
        alternatives: Sequence[Mapping[str, Any]],
        finding: Finding,
    ) -> bool:
        """True when ``claim`` satisfies at least one of the alternative bodies.

        The decision is made against this claim alone: a sibling claim that
        happens to satisfy an alternative must not excuse this one.
        """
        scoped = replace(finding, claims=(claim,))
        for alternative in alternatives:
            if not self._evaluate_subrule(rule, alternative, scoped):
                return True
        return False

    def _eval_forbid(self, rule: PolicyRule, finding: Finding) -> list[PolicyViolation]:
        where = rule.rule.get("where") or {}
        violations: list[PolicyViolation] = []
        pattern = rule.rule.get("pattern")
        if not pattern:
            return violations
        negation_aware = bool(rule.rule.get("negation_aware"))
        if negation_aware:
            matcher = CulpabilityMatcher([str(pattern)])
        else:
            try:
                compiled = re.compile(str(pattern), re.IGNORECASE)
            except re.error as exc:
                raise ValueError(f"policy pattern {pattern!r} is not a valid regular expression: {exc}") from exc

        for claim in self._selected_claims(rule, finding):
            if negation_aware:
                hit = bool(matcher.find(claim.statement))
            else:
                hit = bool(compiled.search(claim.statement))
            if hit:
                violations.append(
                    PolicyViolation(
                        rule_id=rule.id,
                        severity=rule.severity,
                        message=rule.message or f"Statement must not match {pattern!r}.",
                        claim_id=claim.id,
                    )
                )
        return violations

    def _eval_threshold(self, rule: PolicyRule, finding: Finding) -> list[PolicyViolation]:
        where = rule.rule.get("where") or {}
        field = rule.rule.get("field")
        violations: list[PolicyViolation] = []
        if not field:
            return violations
        for claim in self._selected_claims(rule, finding):
            value = _claim_field(claim, field)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                continue
            minimum = rule.rule.get("min")
            maximum = rule.rule.get("max")
            if minimum is not None and value < minimum:
                violations.append(
                    PolicyViolation(
                        rule_id=rule.id,
                        severity=rule.severity,
                        message=rule.message or f"{field} is below the permitted minimum.",
                        claim_id=claim.id,
                    )
                )
            if maximum is not None and value > maximum:
                violations.append(
                    PolicyViolation(
                        rule_id=rule.id,
                        severity=rule.severity,
                        message=rule.message or f"{field} exceeds the permitted maximum.",
                        claim_id=claim.id,
                    )
                )
        return violations

    def _eval_count(self, rule: PolicyRule, finding: Finding) -> list[PolicyViolation]:
        where = rule.rule.get("where") or {}
        minimum = rule.rule.get("min_items")
        maximum = rule.rule.get("max_items")
        selected = self._selected_claims(rule, finding)
        violations: list[PolicyViolation] = []
        if minimum is not None and len(selected) < minimum:
            violations.append(
                PolicyViolation(
                    rule_id=rule.id,
                    severity=rule.severity,
                    message=rule.message or f"At least {minimum} matching claims are required; found {len(selected)}.",
                )
            )
        if maximum is not None and len(selected) > maximum:
            violations.append(
                PolicyViolation(
                    rule_id=rule.id,
                    severity=rule.severity,
                    message=rule.message or f"At most {maximum} matching claims are permitted; found {len(selected)}.",
                )
            )
        return violations

    def _eval_consistency(self, rule: PolicyRule, finding: Finding) -> list[PolicyViolation]:
        expected = rule.rule.get("equals")
        field = rule.rule.get("field")
        if expected is None or not field:
            return []
        violations: list[PolicyViolation] = []
        for claim in self._selected_claims(rule, finding):
            value = _claim_field(claim, field)
            if value != expected:
                violations.append(
                    PolicyViolation(
                        rule_id=rule.id,
                        severity=rule.severity,
                        message=rule.message or f"{field} must equal {expected!r}.",
                        claim_id=claim.id,
                    )
                )
        return violations

    def _eval_composite(self, rule: PolicyRule, finding: Finding) -> list[PolicyViolation]:
        violations: list[PolicyViolation] = []
        for sub in rule.rule.get("all", ()):
            violations.extend(self._evaluate_subrule(rule, sub, finding))
        any_subs = rule.rule.get("any")
        if any_subs:
            # `any` means *at least one* branch must be satisfied, so the
            # composite fails only when every branch failed. Reading it the
            # other way round would make `any` a synonym for `all`, and a
            # control that does not do what it says is worse than no control.
            branch_results = [
                self._evaluate_subrule(rule, sub, finding) for sub in any_subs
            ]
            if all(branch_results):
                violations.append(
                    PolicyViolation(
                        rule_id=rule.id,
                        severity=rule.severity,
                        message=rule.message or "None of the permitted alternatives was satisfied.",
                    )
                )
        not_rule = rule.rule.get("not")
        if not_rule is not None:
            branch_violations = self._evaluate_subrule(rule, not_rule, finding)
            if not branch_violations:
                violations.append(
                    PolicyViolation(
                        rule_id=rule.id,
                        severity=rule.severity,
                        message=rule.message or "A forbidden condition was present.",
                    )
                )
        return violations

    def _evaluate_subrule(self, rule: PolicyRule, sub: Mapping[str, Any], finding: Finding) -> list[PolicyViolation]:
        """Evaluate a nested rule body under the parent rule's identity."""
        kind = sub.get("kind", "count")
        body = {key: value for key, value in sub.items() if key != "kind"}
        nested = PolicyRule(
            id=rule.id,
            version=rule.version,
            severity=rule.severity,
            description=rule.description,
            kind=kind,
            rule=body,
            message=rule.message,
            applies_to=rule.applies_to,
            jurisdictions=rule.jurisdictions,
        )
        handler = {
            "require": self._eval_require,
            "forbid": self._eval_forbid,
            "threshold": self._eval_threshold,
            "count": self._eval_count,
            "consistency": self._eval_consistency,
            "composite": self._eval_composite,
        }.get(kind)
        if handler is None:
            return []
        return handler(nested, finding)
