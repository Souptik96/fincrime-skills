"""Tests for the YAML subset parser.

The parser is hand-written so the CLI can stay stdlib-only, and it is
checked against PyYAML so it does not become a different format with a
different name. The parity test skips when PyYAML is absent; the behaviour
tests never do.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from fincrime_cli.yamlite import YamlSubsetError, parse

REPO_ROOT = Path(__file__).resolve().parents[3]
REFERENCE_SIDECAR = REPO_ROOT / "skills" / "investigation-qa" / "fincrime.skill.yaml"


class TestScalars:
    def test_a_plain_scalar_is_a_string(self) -> None:
        assert parse("key: value") == {"key": "value"}

    def test_the_scalar_types_follow_yaml_12(self) -> None:
        document = parse(
            "\n".join(
                [
                    "a_null: null",
                    "a_tilde: ~",
                    "an_empty:",
                    "a_true: true",
                    "a_false: false",
                    "an_int: 42",
                    "a_negative_int: -7",
                    "a_float: 3.5",
                    "a_string: yes",
                ]
            )
        )
        assert document == {
            "a_null": None,
            "a_tilde": None,
            "an_empty": None,
            "a_true": True,
            "a_false": False,
            "an_int": 42,
            "a_negative_int": -7,
            "a_float": 3.5,
            "a_string": "yes",
        }

    def test_a_quoted_scalar_is_always_a_string(self) -> None:
        assert parse('key: "42"') == {"key": "42"}
        assert parse("key: '42'") == {"key": "42"}

    def test_a_double_quoted_scalar_handles_escapes(self) -> None:
        assert parse(r'key: "a \"b\" c\nd"') == {"key": 'a "b" c\nd'}

    def test_a_single_quoted_scalar_doubles_its_quote(self) -> None:
        assert parse("key: 'it''s'") == {"key": "it's"}

    def test_a_value_may_contain_a_colon(self) -> None:
        assert parse("key: http://example.com/path") == {"key": "http://example.com/path"}

    def test_a_value_may_contain_a_hash(self) -> None:
        assert parse("key: value # not a comment") == {"key": "value"}

    def test_a_quoted_value_may_contain_a_hash(self) -> None:
        assert parse('key: "value # not a comment"') == {"key": "value # not a comment"}


class TestCollections:
    def test_a_block_sequence_of_scalars(self) -> None:
        assert parse("items:\n  - one\n  - two") == {"items": ["one", "two"]}

    def test_a_sequence_may_share_the_key_indentation(self) -> None:
        assert parse("items:\n- one\n- two") == {"items": ["one", "two"]}

    def test_a_block_sequence_of_mappings(self) -> None:
        document = parse(
            "\n".join(
                [
                    "items:",
                    "  - name: first",
                    "    value: 1",
                    "  - name: second",
                    "    value: 2",
                ]
            )
        )
        assert document == {
            "items": [
                {"name": "first", "value": 1},
                {"name": "second", "value": 2},
            ]
        }

    def test_a_flow_sequence(self) -> None:
        assert parse("items: [a, b, c]") == {"items": ["a", "b", "c"]}

    def test_an_empty_flow_sequence(self) -> None:
        assert parse("items: []") == {"items": []}

    def test_a_nested_mapping(self) -> None:
        assert parse("a:\n  b:\n    c: 1") == {"a": {"b": {"c": 1}}}

    def test_an_empty_mapping_value_is_null(self) -> None:
        assert parse("a:\nb: 1") == {"a": None, "b": 1}


class TestBlockScalars:
    def test_a_folded_scalar_joins_its_lines(self) -> None:
        document = parse("purpose: >-\n  one\n  two\n  three")
        assert document == {"purpose": "one two three"}

    def test_a_literal_scalar_keeps_its_lines(self) -> None:
        document = parse("purpose: |-\n  one\n  two")
        assert document == {"purpose": "one\ntwo"}

    def test_a_literal_scalar_keeps_its_indentation(self) -> None:
        document = parse("purpose: |-\n  one\n    two")
        assert document == {"purpose": "one\n  two"}

    def test_a_stripped_scalar_has_no_trailing_newline(self) -> None:
        document = parse("purpose: |-\n  one\n")
        assert document == {"purpose": "one"}

    def test_a_clipped_scalar_has_one_trailing_newline(self) -> None:
        document = parse("purpose: |\n  one\n")
        assert document == {"purpose": "one\n"}


class TestComments:
    def test_a_whole_line_comment_is_ignored(self) -> None:
        assert parse("# a comment\nkey: value") == {"key": "value"}

    def test_a_trailing_comment_is_ignored(self) -> None:
        assert parse("key: value  # a comment") == {"key": "value"}


class TestRejections:
    """Anything outside the subset is a hard error, never a silent misparse."""

    @pytest.mark.parametrize(
        "document",
        [
            "key: &anchor value",
            "key: *alias",
            "key: !!str value",
            "<<: {a: 1}",
            "key: value\n---\nkey: other",
            "key: {a: 1}",
        ],
    )
    def test_unsupported_constructs_are_rejected(self, document: str) -> None:
        with pytest.raises(YamlSubsetError):
            parse(document)

    def test_tab_indentation_is_rejected(self) -> None:
        with pytest.raises(YamlSubsetError, match="tab"):
            parse("a:\n\tb: 1")

    def test_a_document_that_is_not_a_mapping_is_a_scalar(self) -> None:
        """A scalar document is valid YAML. The sidecar checker rejects it."""
        assert parse("not a mapping") == "not a mapping"

    def test_an_unterminated_quote_is_rejected(self) -> None:
        with pytest.raises(YamlSubsetError):
            parse('key: "unterminated')

    def test_an_unterminated_flow_sequence_is_rejected(self) -> None:
        with pytest.raises(YamlSubsetError):
            parse("key: [a, b")


class TestParityWithPyYAML:
    """The subset must agree with the reference implementation."""

    CORPUS = [
        "key: value",
        "a: 1\nb: 2.5\nc: true\nd: null",
        "items:\n  - one\n  - two",
        "items:\n  - name: first\n    value: 1\n  - name: second\n    value: 2",
        "flow: [a, b, c]",
        "empty: []",
        "nested:\n  a:\n    b: 1",
        "folded: >-\n  one\n  two",
        "literal: |-\n  one\n  two",
        "quoted: \"a \\\"b\\\" c\"",
        "single: 'it''s'",
        "comment: value  # trailing",
        "# leading comment\nkey: value",
        "colon: http://example.com",
        "dash-in-value: some-value",
        "a: 1\n\nb: 2",
    ]

    @pytest.mark.parametrize("document", CORPUS)
    def test_the_subset_agrees_with_pyyaml(self, document: str) -> None:
        yaml = pytest.importorskip("yaml")
        assert parse(document) == yaml.safe_load(document)

    def test_the_reference_sidecar_parses_identically(self) -> None:
        yaml = pytest.importorskip("yaml")
        text = REFERENCE_SIDECAR.read_text(encoding="utf-8")
        assert parse(text) == yaml.safe_load(text)

    def test_the_reference_frontmatter_parses_identically(self) -> None:
        yaml = pytest.importorskip("yaml")
        text = (REPO_ROOT / "skills" / "investigation-qa" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        block = text.split("---")[1]
        assert parse(block) == yaml.safe_load(block)
