"""Tests for the SKILL.md frontmatter reader."""

from __future__ import annotations

from pathlib import Path

import pytest

from fincrime_cli.frontmatter import (
    FrontmatterError,
    load_skill_md,
    split_frontmatter,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
REFERENCE_SKILL_MD = REPO_ROOT / "skills" / "investigation-qa" / "SKILL.md"


class TestSplitFrontmatter:
    def test_the_block_and_the_body_are_separated(self) -> None:
        block, body = split_frontmatter("---\nname: x\n---\n# Title\n")
        assert block == "name: x"
        assert body == "# Title\n"

    def test_a_file_without_frontmatter_is_rejected(self) -> None:
        with pytest.raises(FrontmatterError, match="does not begin"):
            split_frontmatter("# Title\n")

    def test_an_unclosed_block_is_rejected(self) -> None:
        with pytest.raises(FrontmatterError, match="not closed"):
            split_frontmatter("---\nname: x\n")


class TestLoadSkillMd:
    def test_the_reference_skill_parses(self) -> None:
        frontmatter = load_skill_md(REFERENCE_SKILL_MD)
        assert frontmatter.name == "investigation-qa"
        assert frontmatter.license == "Apache-2.0"
        assert "Review a financial-crime investigation artifact" in frontmatter.description
        assert frontmatter.metadata["jurisdiction"] == "US"
        assert "## Procedure" in frontmatter.body

    def test_the_description_is_a_folded_single_line(self) -> None:
        frontmatter = load_skill_md(REFERENCE_SKILL_MD)
        assert "\n" not in frontmatter.description

    def test_a_file_with_invalid_yaml_is_rejected(self, tmp_path: Path) -> None:
        target = tmp_path / "SKILL.md"
        target.write_text("---\nname: [unterminated\n---\nbody\n", encoding="utf-8")
        with pytest.raises(FrontmatterError):
            load_skill_md(target)

    def test_a_frontmatter_that_is_not_a_mapping_is_rejected(self, tmp_path: Path) -> None:
        target = tmp_path / "SKILL.md"
        target.write_text("---\n- a\n- b\n---\nbody\n", encoding="utf-8")
        with pytest.raises(FrontmatterError, match="not a mapping"):
            load_skill_md(target)
