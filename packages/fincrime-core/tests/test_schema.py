"""Tests for the JSON Schema subset validator.

The subset validator must agree with a reference implementation on the
corpus. That cross-check runs in CI where ``jsonschema`` is available as a
dev dependency; here we assert the behaviours the contracts depend on.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from fincrime_core.validate.schema import JsonSchemaValidator

CONTRACTS = Path(__file__).resolve().parents[3] / "contracts"


def load(name: str) -> dict:
    with (CONTRACTS / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


class TestFindingSchema:
    def test_contract_files_are_valid_json(self) -> None:
        for path in sorted(CONTRACTS.glob("*.json")):
            with path.open("r", encoding="utf-8") as handle:
                json.load(handle)

    def test_required_top_level_fields(self) -> None:
        validator = JsonSchemaValidator(load("finding.schema.json"))
        errors = validator.validate({})
        assert errors

    def test_claim_class_enum_is_closed(self) -> None:
        validator = JsonSchemaValidator(load("finding.schema.json"))
        artifact = {
            "contract_version": "fincrime/finding/1.0.0",
            "artifact": {},
            "provenance": {},
            "claims": [
                {
                    "id": "C-001",
                    "class": "not_a_class",
                    "statement": "x",
                    "confidence": {"level": "high", "basis": "y"},
                }
            ],
            "human_decision_required": [],
        }
        assert validator.validate(artifact)

    def test_conditional_requirements_are_enforced(self) -> None:
        """A hypothesis without a falsifier must fail the schema alone.

        A third party using only a stock JSON Schema validator must enforce the
        same rules we do. That is the portability claim.
        """
        validator = JsonSchemaValidator(load("finding.schema.json"))
        base = {
            "contract_version": "fincrime/finding/1.0.0",
            "artifact": {
                "skill_id": "s",
                "skill_version": "1.0.0",
                "artifact_type": "triage_report",
                "subject_ids": ["x"],
                "jurisdictions": ["US"],
                "created_at": "2026-01-01T00:00:00Z",
                "completeness": "complete",
            },
            "provenance": {
                "skill_id": "s",
                "skill_version": "1.0.0",
                "model": {"provider": "p", "id": "i"},
                "prompt_sha256": "a" * 64,
                "evidence_set_sha256": "b" * 64,
                "knowledge_pack": {"id": "k", "version": "v", "as_of": "2026-01-01"},
                "policy_set": {"id": "p", "version": "1"},
                "run_id": "r",
                "timestamp": "2026-01-01T00:00:00Z",
            },
            "human_decision_required": [
                {"decision_id": "D-01", "question": "q", "owner_role": "r"}
            ],
        }
        hypothesis = {
            "id": "C-001",
            "class": "hypothesis",
            "statement": "s",
            "confidence": {"level": "low", "basis": "b"},
            "epistemic_type": "adverse_reading",
        }
        without_falsifier = {**base, "claims": [hypothesis]}
        assert validator.validate(without_falsifier)

        with_falsifier = {
            **base,
            "claims": [{**hypothesis, "falsifier": "would be refuted by X"}],
        }
        assert validator.validate(with_falsifier) == []


class TestSubsetBehaviour:
    def test_type_mismatch(self) -> None:
        validator = JsonSchemaValidator({"type": "string"})
        assert validator.validate(5)

    def test_boolean_is_not_an_integer(self) -> None:
        validator = JsonSchemaValidator({"type": "integer"})
        assert validator.validate(True)
        assert not validator.validate(5)

    def test_const_and_enum(self) -> None:
        assert JsonSchemaValidator({"const": "x"}).validate("y")
        assert not JsonSchemaValidator({"const": "x"}).validate("x")
        assert JsonSchemaValidator({"enum": ["a", "b"]}).validate("c")

    def test_additional_properties_false(self) -> None:
        validator = JsonSchemaValidator(
            {"type": "object", "properties": {"a": {}}, "additionalProperties": False}
        )
        assert validator.validate({"a": 1, "b": 2})
        assert not validator.validate({"a": 1})

    def test_array_bounds_and_uniqueness(self) -> None:
        assert JsonSchemaValidator({"minItems": 2}).validate([1])
        assert JsonSchemaValidator({"maxItems": 1}).validate([1, 2])
        assert JsonSchemaValidator({"uniqueItems": True}).validate([1, 1])

    def test_pattern_and_length(self) -> None:
        assert JsonSchemaValidator({"pattern": "^C-[0-9]+$"}).validate("X-1")
        assert JsonSchemaValidator({"minLength": 2}).validate("a")

    def test_numeric_bounds(self) -> None:
        assert JsonSchemaValidator({"minimum": 5}).validate(4)
        assert JsonSchemaValidator({"maximum": 5}).validate(6)
        assert JsonSchemaValidator({"exclusiveMinimum": 5}).validate(5)

    def test_ref_resolution(self) -> None:
        schema = {
            "$defs": {"positive": {"type": "integer", "minimum": 1}},
            "type": "object",
            "properties": {"n": {"$ref": "#/$defs/positive"}},
        }
        validator = JsonSchemaValidator(schema)
        assert validator.validate({"n": 0})
        assert not validator.validate({"n": 1})

    def test_if_then(self) -> None:
        schema = {
            "type": "object",
            "if": {"properties": {"kind": {"const": "special"}}, "required": ["kind"]},
            "then": {"required": ["extra"]},
        }
        validator = JsonSchemaValidator(schema)
        assert validator.validate({"kind": "special"})
        assert not validator.validate({"kind": "ordinary"})

    def test_any_of_and_one_of(self) -> None:
        assert JsonSchemaValidator({"anyOf": [{"type": "string"}, {"type": "integer"}]}).validate(1.5)
        assert JsonSchemaValidator({"oneOf": [{"type": "integer"}, {"type": "number"}]}).validate(True)

    def test_date_time_format_is_checked(self) -> None:
        validator = JsonSchemaValidator({"type": "string", "format": "date-time"})
        assert validator.validate("not-a-timestamp")
        assert not validator.validate("2026-01-01T00:00:00Z")

    def test_additional_properties_schema(self) -> None:
        validator = JsonSchemaValidator(
            {"type": "object", "additionalProperties": {"type": "string"}}
        )
        assert validator.validate({"a": 1})
        assert not validator.validate({"a": "x"})


class TestContractSchemas:
    @pytest.mark.parametrize(
        "name",
        [
            "finding.schema.json",
            "evidence-set.schema.json",
            "skill-manifest.schema.json",
            "knowledge-record.schema.json",
            "policy-rule.schema.json",
            "case.schema.json",
            "evidence-ref-grammar.schema.json",
        ],
    )
    def test_schema_documents_are_self_consistent(self, name: str) -> None:
        schema = load(name)
        assert "$schema" in schema
        assert "$id" in schema
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"

    def test_claim_classes_enum_matches_the_schema(self) -> None:
        from fincrime_core.contract.model import CLAIM_CLASSES

        schema = load("finding.schema.json")
        enum = schema["$defs"]["claim"]["properties"]["class"]["enum"]
        assert set(enum) == set(CLAIM_CLASSES)

    def test_evidence_ref_pattern_matches_the_grammar_contract(self) -> None:
        from fincrime_core.validate.evidence_refs import EVIDENCE_REF_PATTERN_STR

        grammar = load("evidence-ref-grammar.schema.json")
        assert EVIDENCE_REF_PATTERN_STR == grammar["properties"]["evidence_ref_pattern"]["const"]

    def test_evidence_ref_pattern_is_identical_in_every_contract(self) -> None:
        """The evidence-reference grammar must be stated once, identically.

        The review found the pattern in ``finding.schema.json`` had drifted
        from the canonical one: it accepted a second ``#`` in the fragment and
        an unbounded source-instance length, so an artifact could satisfy the
        contract and still be rejected by the implementation. The two are now
        asserted equal everywhere the pattern appears.
        """
        from fincrime_core.validate.evidence_refs import EVIDENCE_REF_PATTERN_STR

        canonical = EVIDENCE_REF_PATTERN_STR
        occurrences: list[tuple[str, str]] = []

        for path in sorted(CONTRACTS.glob("*.json")):
            with path.open("r", encoding="utf-8") as handle:
                document = json.load(handle)

            def walk(node: Any) -> None:
                if isinstance(node, dict):
                    for key, value in node.items():
                        if key == "pattern" and isinstance(value, str) and "#" in value and "/(" in value:
                            occurrences.append((path.name, value))
                        walk(value)
                elif isinstance(node, list):
                    for item in node:
                        walk(item)

            walk(document)

        assert occurrences, "no evidence-reference pattern was found in the contracts"
        for filename, pattern in occurrences:
            assert pattern == canonical, (
                f"{filename} states a different evidence-reference pattern from the canonical one. "
                "The contract and the implementation must agree exactly."
            )

    def test_the_finding_schema_rejects_a_second_hash(self) -> None:
        """A second '#' would terminate the fragment under RFC 3986."""
        from fincrime_core.validate.schema import JsonSchemaValidator

        validator = JsonSchemaValidator(load("finding.schema.json")["$defs"]["evidence_ref"])
        assert not validator.is_valid("txn:123#/amount#second")
        assert not validator.is_valid("txn:" + ("a" * 100) + "#/amount")
        assert validator.is_valid("txn:123#/amount")
        assert validator.is_valid("txn:123#")
