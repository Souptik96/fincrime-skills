"""``yamlite`` — a parser for the YAML subset this project uses.

The core has zero runtime dependencies (ADR-0002), and ``yaml`` is on the
forbidden list for good reason: a package that can open a socket can
exfiltrate a case file. But the skill sidecar is YAML, so something has to
read it.

The answer is a parser for a *restricted* subset, with the restriction
written down rather than implied. The supported subset is:

* block mappings and block sequences, nested by indentation;
* sequences of mappings (``- key: value`` and the keys that follow it);
* flow sequences (``[a, b]``, including the empty ``[]``);
* plain, single-quoted and double-quoted scalars;
* block scalars: ``|``, ``|-``, ``>``, ``>-`` (and their ``+`` variants);
* ``#`` comments, whole-line and trailing;
* scalar typing: ``null``/``~``/empty, ``true``/``false``, integers,
  floats, and strings for everything else. The typing rules are YAML 1.2's,
  so ``yes`` and ``no`` are strings.

Everything else is a **hard error**, never a silent misparse: anchors
(``&``), aliases (``*``), tags (``!``), merge keys (``<<``), complex keys
(``?``), multiple documents, and tab indentation. A parser that guesses is
worse than a parser that refuses, because a guessed sidecar becomes a skill
whose contract nobody checked.

The subset is verified against PyYAML by a parity test, in the same spirit
as the JSON Schema parity check in ``scripts/check_schema_parity.py``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

__all__ = ["YamlSubsetError", "parse", "parse_file", "SUPPORTED_SUBSET"]


class YamlSubsetError(ValueError):
    """Raised when a document uses something outside the supported subset.

    Carries the line number so the author is told where to look, which is the
    only useful thing a parser can say about a file it will not read.
    """

    def __init__(self, message: str, line: int | None = None) -> None:
        self.line = line
        super().__init__(f"line {line}: {message}" if line is not None else message)


#: A human-readable statement of what this parser accepts.
SUPPORTED_SUBSET = """\
block mappings and sequences, flow sequences, plain/quoted scalars, block
scalars (| |-, > >-), comments, and YAML 1.2 scalar typing. Anchors,
aliases, tags, merge keys, complex keys, multiple documents and tab
indentation are rejected."""

_INT_RE = re.compile(r"^[-+]?[0-9]+$")
_FLOAT_RE = re.compile(
    r"^[-+]?(?:[0-9]+\.[0-9]*|\.[0-9]+)(?:[eE][-+]?[0-9]+)?$|^[-+]?[0-9]+[eE][-+]?[0-9]+$"
)
_KEY_RE = re.compile(r"^(?:[A-Za-z0-9_][A-Za-z0-9_.\-/ ]*?)\s*:(?:\s|$)")
_ESCAPES = {
    "n": "\n",
    "t": "\t",
    "r": "\r",
    "b": "\b",
    "f": "\f",
    "0": "\0",
    '"': '"',
    "\\": "\\",
    "/": "/",
    " ": " ",
}


def parse(text: str) -> Any:
    """Parse a YAML document restricted to the supported subset."""
    return _Parser(text).parse_document()


def parse_file(path: str | Path) -> Any:
    """Parse a YAML file restricted to the supported subset."""
    with Path(path).open("r", encoding="utf-8") as handle:
        return parse(handle.read())


def _strip_comment(text: str) -> str:
    """Remove a trailing comment, respecting quoted spans.

    A ``#`` only starts a comment at the beginning of the line or after
    whitespace, and never inside a quoted scalar.
    """
    out: list[str] = []
    quote: str | None = None
    index = 0
    while index < len(text):
        char = text[index]
        if quote is not None:
            out.append(char)
            if char == "\\" and quote == '"' and index + 1 < len(text):
                out.append(text[index + 1])
                index += 2
                continue
            if char == quote:
                quote = None
            index += 1
            continue
        if char in ("'", '"'):
            quote = char
            out.append(char)
            index += 1
            continue
        if char == "#" and (index == 0 or text[index - 1] in " \t"):
            break
        out.append(char)
        index += 1
    return "".join(out).rstrip()


def _infer_scalar(text: str) -> Any:
    """Apply YAML 1.2 scalar typing to a plain scalar."""
    stripped = text.strip()
    if stripped in ("", "~", "null", "Null", "NULL"):
        return None
    if stripped in ("true", "True", "TRUE"):
        return True
    if stripped in ("false", "False", "FALSE"):
        return False
    if _INT_RE.match(stripped):
        return int(stripped)
    if _FLOAT_RE.match(stripped):
        return float(stripped)
    return stripped


class _Parser:
    """A recursive-descent parser over the raw lines of a document."""

    def __init__(self, text: str) -> None:
        normalised = text.replace("\r\n", "\n").replace("\r", "\n")
        self._lines = normalised.split("\n")
        self._pos = 0
        self._start = 0

    # -- line handling --------------------------------------------------

    def _current(self) -> str:
        return self._lines[self._pos]

    def _advance(self) -> None:
        self._pos += 1

    def _replace_current(self, text: str) -> None:
        self._lines[self._pos] = text

    @staticmethod
    def _is_blank(text: str) -> bool:
        return not text.strip()

    @staticmethod
    def _is_comment(text: str) -> bool:
        return text.lstrip().startswith("#")

    @staticmethod
    def _indent_of(text: str, line_number: int) -> int:
        stripped = text.lstrip(" \t")
        indent = len(text) - len(stripped)
        if "\t" in text[:indent]:
            raise YamlSubsetError("tab indentation is not supported", line_number)
        return indent

    def _peek(self) -> tuple[int, str, int] | None:
        """The next significant line as ``(indent, content, line number)``."""
        while self._pos < len(self._lines):
            raw = self._lines[self._pos]
            if self._is_blank(raw) or self._is_comment(raw):
                self._pos += 1
                continue
            number = self._pos + 1
            indent = self._indent_of(raw, number)
            content = _strip_comment(raw[indent:]).strip()
            if content in ("---", "..."):
                raise YamlSubsetError("multiple documents are not supported", number)
            if not content:
                self._pos += 1
                continue
            return indent, content, number
        return None

    # -- document -------------------------------------------------------

    def parse_document(self) -> Any:
        head = self._peek()
        if head is not None and head[1] == "---":
            self._advance()
        value = self._parse_node(0)
        trailing = self._peek()
        if trailing is not None:
            raise YamlSubsetError(f"unexpected content {trailing[1]!r}", trailing[2])
        return value

    def _parse_node(self, indent: int) -> Any:
        head = self._peek()
        if head is None:
            return None
        line_indent, content, number = head
        if line_indent < indent:
            return None
        if content == "-" or content.startswith("- "):
            return self._parse_sequence(line_indent)
        if self._is_mapping_start(content):
            return self._parse_mapping(line_indent)
        # A node that is neither a mapping nor a sequence is a scalar.
        self._advance()
        return self._read_inline_value(content, indent, number)

    def _is_mapping_start(self, content: str) -> bool:
        """True when a line begins a mapping rather than a scalar."""
        if content[0] in ("'", '"'):
            try:
                _, remainder = self._read_quoted(content, 0)
            except YamlSubsetError:
                return False
            return remainder.lstrip().startswith(":")
        return _KEY_RE.match(content) is not None

    # -- mappings -------------------------------------------------------

    def _parse_mapping(self, indent: int) -> dict[str, Any]:
        result: dict[str, Any] = {}
        while True:
            head = self._peek()
            if head is None:
                break
            line_indent, content, number = head
            if line_indent < indent:
                break
            if line_indent > indent:
                raise YamlSubsetError(
                    f"unexpected indentation in {content!r}", number
                )
            if content == "-" or content.startswith("- "):
                break

            key, rest = self._split_key(content, number)
            self._advance()

            if rest == "":
                result[key] = self._parse_child(indent)
            elif rest[0] in "|>":
                result[key] = self._read_block_scalar(rest, indent, number)
            else:
                result[key] = self._read_inline_value(rest, indent, number)
        return result

    def _split_key(self, content: str, number: int) -> tuple[str, str]:
        """Split ``key: value`` into its key and its value."""
        if content.startswith("?"):
            raise YamlSubsetError("complex keys are not supported", number)
        if content.startswith("<<"):
            raise YamlSubsetError("merge keys are not supported", number)
        if content.startswith("&"):
            raise YamlSubsetError("anchors are not supported", number)
        if content.startswith("*"):
            raise YamlSubsetError("aliases are not supported", number)
        if content.startswith("!"):
            raise YamlSubsetError("tags are not supported", number)

        if content[0] in ("'", '"'):
            key_text, remainder = self._read_quoted(content, number)
            remainder = remainder.lstrip()
            if not remainder.startswith(":"):
                raise YamlSubsetError(f"expected ':' after key {key_text!r}", number)
            return key_text, remainder[1:].strip()

        match = _KEY_RE.match(content)
        if match is None:
            raise YamlSubsetError(f"expected 'key: value', found {content!r}", number)
        colon_at = content.index(":")
        key = content[:colon_at].strip()
        rest = content[colon_at + 1 :].strip()
        if not key:
            raise YamlSubsetError(f"expected a key, found {content!r}", number)
        return key, rest

    def _parse_child(self, indent: int) -> Any:
        """The value of a key with nothing after the colon."""
        head = self._peek()
        if head is None:
            return None
        line_indent, content, _ = head
        if line_indent > indent:
            return self._parse_node(line_indent)
        if line_indent == indent and (content == "-" or content.startswith("- ")):
            return self._parse_sequence(line_indent)
        return None

    # -- sequences ------------------------------------------------------

    def _parse_sequence(self, indent: int) -> list[Any]:
        items: list[Any] = []
        while True:
            head = self._peek()
            if head is None:
                break
            line_indent, content, number = head
            if line_indent < indent:
                break
            if line_indent > indent:
                raise YamlSubsetError(
                    f"unexpected indentation in {content!r}", number
                )
            if not (content == "-" or content.startswith("- ")):
                break

            if content == "-":
                self._advance()
                items.append(self._parse_child(indent))
                continue

            rest = content[2:].strip()
            # Replace the dash with spaces so the item's content keeps the
            # column it already had, which is where YAML says it sits.
            raw = self._current()
            dash_at = raw.index("-", indent)
            content_at = dash_at + 1
            while content_at < len(raw) and raw[content_at] == " ":
                content_at += 1
            self._replace_current(raw[:dash_at] + " " * (content_at - dash_at) + raw[content_at:])
            items.append(self._parse_node(content_at))
        return items

    # -- scalars --------------------------------------------------------

    def _read_inline_value(self, text: str, indent: int, number: int) -> Any:
        if text.startswith('"') or text.startswith("'"):
            value, remainder = self._read_quoted(text, number)
            if remainder.strip():
                raise YamlSubsetError(
                    f"unexpected content after a quoted value: {remainder.strip()!r}", number
                )
            return value
        if text.startswith("["):
            return self._read_flow_sequence(text, number)
        if text.startswith(("&", "*", "!")):
            raise YamlSubsetError(
                "anchors, aliases and tags are not supported", number
            )
        if text.startswith("<<"):
            raise YamlSubsetError("merge keys are not supported", number)
        if text.startswith("{"):
            raise YamlSubsetError("flow mappings are not supported", number)

        parts = [text]
        while True:
            head = self._peek()
            if head is None:
                break
            line_indent, content, _ = head
            if line_indent <= indent:
                break
            if content == "-" or content.startswith("- "):
                break
            if _KEY_RE.match(content) or content.startswith("?"):
                break
            parts.append(content)
            self._advance()

        if len(parts) == 1:
            return _infer_scalar(parts[0])
        return " ".join(part.strip() for part in parts)

    def _read_quoted(self, text: str, number: int) -> tuple[str, str]:
        quote = text[0]
        index = 1
        out: list[str] = []
        while index < len(text):
            char = text[index]
            if quote == "'":
                if char == "'":
                    if index + 1 < len(text) and text[index + 1] == "'":
                        out.append("'")
                        index += 2
                        continue
                    return "".join(out), text[index + 1 :]
                out.append(char)
                index += 1
                continue

            if char == "\\":
                if index + 1 >= len(text):
                    raise YamlSubsetError("unterminated escape sequence", number)
                code = text[index + 1]
                if code == "u":
                    hex_digits = text[index + 2 : index + 6]
                    if len(hex_digits) != 4:
                        raise YamlSubsetError("malformed \\u escape", number)
                    try:
                        out.append(chr(int(hex_digits, 16)))
                    except ValueError as exc:
                        raise YamlSubsetError("malformed \\u escape", number) from exc
                    index += 6
                    continue
                if code not in _ESCAPES:
                    raise YamlSubsetError(f"unsupported escape \\{code}", number)
                out.append(_ESCAPES[code])
                index += 2
                continue
            if char == '"':
                return "".join(out), text[index + 1 :]
            out.append(char)
            index += 1
        raise YamlSubsetError("unterminated quoted scalar", number)

    def _read_flow_sequence(self, text: str, number: int) -> list[Any]:
        items: list[Any] = []
        rest = text[1:]
        rest = rest.lstrip()
        if rest.startswith("]"):
            return items
        while True:
            rest = rest.lstrip()
            if not rest:
                raise YamlSubsetError("unterminated flow sequence", number)
            if rest[0] in ("'", '"'):
                value, remainder = self._read_quoted(rest, number)
                items.append(value)
                rest = remainder
            elif rest[0] == "[":
                nested, remainder = self._read_flow_sequence(rest, number)
                items.append(nested)
                rest = remainder
            else:
                end = len(rest)
                depth = 0
                for position, char in enumerate(rest):
                    if char in ("[", "{"):
                        depth += 1
                    elif char in ("]", "}"):
                        if char == "]" and depth == 0:
                            end = position
                            break
                        depth -= 1
                    elif char == "," and depth == 0:
                        end = position
                        break
                items.append(_infer_scalar(rest[:end]))
                rest = rest[end:]
            rest = rest.lstrip()
            if rest.startswith(","):
                rest = rest[1:]
                continue
            if rest.startswith("]"):
                remainder = rest[1:].strip()
                if remainder:
                    raise YamlSubsetError(
                        f"unexpected content after a flow sequence: {remainder!r}", number
                    )
                return items
            raise YamlSubsetError("malformed flow sequence", number)

    # -- block scalars --------------------------------------------------

    def _read_block_scalar(self, indicator: str, indent: int, number: int) -> str:
        style = indicator[0]
        chomp = "clip"
        explicit_indent = 0
        for char in indicator[1:]:
            if char in "+-":
                chomp = "keep" if char == "+" else "strip"
            elif char.isdigit():
                explicit_indent = int(char)
            elif char in " \t":
                continue
            else:
                raise YamlSubsetError(
                    f"malformed block scalar indicator {indicator!r}", number
                )

        collected: list[str] = []
        while self._pos < len(self._lines):
            raw = self._lines[self._pos]
            if self._is_blank(raw):
                collected.append("")
                self._advance()
                continue
            line_indent = self._indent_of(raw, self._pos + 1)
            if line_indent <= indent:
                break
            collected.append(raw)
            self._advance()

        while collected and collected[-1] == "":
            collected.pop()

        if not collected:
            return ""

        if explicit_indent:
            block_indent = indent + explicit_indent
        else:
            block_indent = min(
                len(line) - len(line.lstrip(" ")) for line in collected if line.strip()
            )

        stripped = []
        for line in collected:
            if not line.strip():
                stripped.append("")
            elif len(line) - len(line.lstrip(" ")) >= block_indent:
                stripped.append(line[block_indent:])
            else:
                stripped.append(line.lstrip(" "))

        if style == "|":
            content = "\n".join(stripped)
        else:
            content = _fold(stripped)

        if chomp == "strip":
            return content.rstrip("\n")
        if chomp == "clip":
            return content.rstrip("\n") + "\n"
        return content + "\n"


def _fold(lines: list[str]) -> str:
    """Fold a block scalar: a single break becomes a space, a blank line a newline."""
    out: list[str] = []
    pending = 0
    first = True
    for line in lines:
        if not line.strip():
            pending += 1
            continue
        if first:
            out.append(line.rstrip())
            first = False
        else:
            out.append("\n" * pending if pending else " ")
            out.append(line.rstrip())
        pending = 0
    return "".join(out)
