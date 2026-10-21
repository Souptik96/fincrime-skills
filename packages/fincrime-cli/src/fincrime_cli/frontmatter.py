"""The Agent Skills frontmatter of a ``SKILL.md`` file.

A skill package is a directory with a ``SKILL.md`` at its root. The file
begins with a YAML frontmatter block delimited by ``---`` lines, and the rest
is the body an agent reads.

The frontmatter and the sidecar must agree: the frontmatter is what a host
that knows nothing about FinCrime sees, and the sidecar is what a host that
does see. Two descriptions of the same skill that disagree are worse than
one that is incomplete, so the two are compared in
:mod:`fincrime_cli.skillcheck`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fincrime_cli.yamlite import YamlSubsetError, parse

__all__ = ["FrontmatterError", "Frontmatter", "split_frontmatter", "load_skill_md"]


class FrontmatterError(ValueError):
    """Raised when a ``SKILL.md`` has no usable frontmatter."""


@dataclass(frozen=True, slots=True)
class Frontmatter:
    """The parsed frontmatter and the body that follows it."""

    data: dict[str, Any]
    body: str

    @property
    def name(self) -> str:
        return str(self.data.get("name", ""))

    @property
    def description(self) -> str:
        return str(self.data.get("description", ""))

    @property
    def license(self) -> str:
        return str(self.data.get("license", ""))

    @property
    def metadata(self) -> dict[str, Any]:
        value = self.data.get("metadata")
        return dict(value) if isinstance(value, dict) else {}


def split_frontmatter(text: str) -> tuple[str, str]:
    """Split a ``SKILL.md`` into its frontmatter block and its body."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        raise FrontmatterError("the file does not begin with a '---' frontmatter block")
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[1:index]), "\n".join(lines[index + 1 :])
    raise FrontmatterError("the frontmatter block is not closed by a '---' line")


def load_skill_md(path: str | Path) -> Frontmatter:
    """Read a ``SKILL.md`` and parse its frontmatter."""
    with Path(path).open("r", encoding="utf-8") as handle:
        text = handle.read()
    block, body = split_frontmatter(text)
    try:
        data = parse(block)
    except YamlSubsetError as exc:
        raise FrontmatterError(f"the frontmatter is not valid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise FrontmatterError("the frontmatter is not a mapping")
    return Frontmatter(data=data, body=body)
