"""Tests for the RFC 6901 evidence-reference resolver.

The resolver is the most important correctness surface in the project, so the
tests are correspondingly thorough: totality, escaping order, over-broad
rejection, and the closed-world property.
"""

from __future__ import annotations

import pytest

from fincrime_core.validate.evidence_refs import (
    EVIDENCE_REF_PATTERN,
    MAX_CITED_COLLECTION_LENGTH,
    SourceIndex,
    build_source_index,
    escape_token,
    parse_evidence_ref,
    unescape_token,
)


class TestParsing:
    def test_parses_source_and_pointer(self) -> None:
        assert parse_evidence_ref("txn:8842#/amount") == ("txn:8842", "/amount")

    def test_empty_pointer_is_the_whole_item(self) -> None:
        assert parse_evidence_ref("txn:8842#") == ("txn:8842", "")

    def test_nested_pointer(self) -> None:
        assert parse_evidence_ref("txn:8842#/counterparty/name") == ("txn:8842", "/counterparty/name")

    @pytest.mark.parametrize(
        "ref",
        [
            "txn:8842",  # missing the required '#'
            "txn8842#/amount",  # missing the source-id colon
            ":#/amount",  # empty type
            "txn:8842#/amount/extra#",  # two separators
            "txn:8842#/~2",  # invalid escape
            "",
        ],
    )
    def test_rejects_malformed(self, ref: str) -> None:
        with pytest.raises(ValueError):
            parse_evidence_ref(ref)

    def test_pattern_matches_canonical_forms(self) -> None:
        assert EVIDENCE_REF_PATTERN.match("txn:8842#/amount")
        assert EVIDENCE_REF_PATTERN.match("doc:kYC-2291#")
        assert not EVIDENCE_REF_PATTERN.match("txn:8842")


class TestEscaping:
    def test_unescape_order_matters(self) -> None:
        # "~01" must decode to "~1", not "/". If "~0" were replaced first the
        # result would be "/1".
        assert unescape_token("~01") == "~1"

    def test_unescape_slash(self) -> None:
        assert unescape_token("a~1b") == "a/b"

    def test_escape_round_trip(self) -> None:
        for token in ("plain", "with/slash", "with~tilde", "~01", "a~1b~0c"):
            assert unescape_token(escape_token(token)) == token


class TestResolution:
    def test_resolves_a_scalar(self) -> None:
        index = SourceIndex({"txn:8842": {"amount": 9400}})
        result = index.resolve("txn:8842#/amount")
        assert result.ok
        assert result.value == 9400

    def test_resolves_the_whole_item(self) -> None:
        index = SourceIndex({"txn:8842": {"amount": 9400}})
        result = index.resolve("txn:8842#")
        assert result.ok
        assert result.value == {"amount": 9400}

    def test_resolves_through_escaped_keys(self) -> None:
        index = SourceIndex({"doc:1": {"a/b": 1, "c~d": 2}})
        assert index.resolve("doc:1#/a~1b").value == 1
        assert index.resolve("doc:1#/c~0d").value == 2

    def test_unknown_source(self) -> None:
        index = SourceIndex({})
        result = index.resolve("txn:9999#/amount")
        assert not result.ok
        assert result.error_code == "unknown_source"

    def test_unresolved_pointer(self) -> None:
        index = SourceIndex({"txn:8842": {"amount": 9400}})
        result = index.resolve("txn:8842#/missing")
        assert not result.ok
        assert result.error_code == "unresolved_pointer"

    def test_malformed_ref_never_raises(self) -> None:
        index = SourceIndex({"txn:8842": {}})
        result = index.resolve("this is not a ref")
        assert not result.ok
        assert result.error_code == "malformed_ref"

    def test_non_string_ref_never_raises(self) -> None:
        index = SourceIndex({})
        for bad in (None, 42, [], {}):
            result = index.resolve(bad)  # type: ignore[arg-type]
            assert not result.ok
            assert result.error_code == "malformed_ref"

    def test_array_index_resolution(self) -> None:
        index = SourceIndex({"txn:1": {"lines": [{"amount": 1}, {"amount": 2}]}})
        assert index.resolve("txn:1#/lines/1/amount").value == 2

    def test_out_of_range_array_index(self) -> None:
        index = SourceIndex({"txn:1": {"lines": [{"amount": 1}]}})
        result = index.resolve("txn:1#/lines/9/amount")
        assert not result.ok
        assert result.error_code == "unresolved_pointer"

    def test_dash_token_does_not_resolve(self) -> None:
        index = SourceIndex({"txn:1": {"lines": [{"amount": 1}]}})
        result = index.resolve("txn:1#/lines/-")
        assert not result.ok

    def test_over_broad_citation_is_rejected(self) -> None:
        big = {"lines": [{"amount": index} for index in range(MAX_CITED_COLLECTION_LENGTH + 1)]}
        index = SourceIndex({"txn:1": big})
        result = index.resolve("txn:1#/lines")
        assert not result.ok
        assert result.is_over_broad

    def test_collection_at_the_limit_is_accepted(self) -> None:
        ok = {"lines": [{"amount": index} for index in range(MAX_CITED_COLLECTION_LENGTH)]}
        index = SourceIndex({"txn:1": ok})
        assert index.resolve("txn:1#/lines").ok

    def test_cannot_descend_into_a_scalar(self) -> None:
        index = SourceIndex({"txn:1": {"amount": 5}})
        result = index.resolve("txn:1#/amount/deeper")
        assert not result.ok


class TestSourceIndex:
    def test_indexes_every_record_type(self, evidence_set: dict) -> None:
        index = build_source_index(evidence_set)
        assert "alert:9930" in index
        assert "subject:5512" in index
        assert "txn:8841" in index
        assert "doc:kYC-2291" in index

    def test_records_without_an_identifier_are_not_citable(self) -> None:
        index = build_source_index({"transactions": [{"amount": 100}]})
        assert len(index) == 0

    def test_is_a_closed_world(self, evidence_set: dict) -> None:
        index = build_source_index(evidence_set)
        result = index.resolve("txn:9999#/amount")
        assert not result.ok
        assert result.error_code == "unknown_source"

    def test_is_idempotent(self, evidence_set: dict) -> None:
        first = build_source_index(evidence_set)
        second = build_source_index(evidence_set)
        assert set(first.source_ids()) == set(second.source_ids())
