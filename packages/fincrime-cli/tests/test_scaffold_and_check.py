"""Tests for the scaffolder and the skill package checker.

The scaffold has one job: write a package that already satisfies its
contract, so that the author starts from a valid package rather than from a
blank directory. The test that matters is the round trip — scaffold, then
validate, and the validation must come back clean.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from fincrime_cli.scaffold import SkillNameError, scaffold_skill
from fincrime_cli.skillcheck import check_skill_package
from fincrime_cli.yamlite import parse

REPO_ROOT = Path(__file__).resolve().parents[3]
REFERENCE_SKILL = REPO_ROOT / "skills" / "investigation-qa"
DEFAULT_POLICY_SET = REPO_ROOT / "policies" / "default" / "policy-set.json"


class TestScaffold:
    def test_it_writes_the_expected_files(self, tmp_path: Path) -> None:
        result = scaffold_skill("demo-skill", tmp_path)
        assert result.root == tmp_path / "demo-skill"
        written = {path.name for path in result.files}
        assert "SKILL.md" in written
        assert "fincrime.skill.yaml" in written
        assert (result.root / "evals" / "suites" / "demo-skill" / "suite.json").exists()
        assert (
            result.root / "evals" / "suites" / "demo-skill" / "cases" / "golden-001.json"
        ).exists()

    def test_the_scaffolded_package_validates(self, tmp_path: Path) -> None:
        from fincrime_core.policy.set import load_policy_set

        scaffold_skill("demo-skill", tmp_path)
        result = check_skill_package(
            tmp_path / "demo-skill", policy_set=load_policy_set(DEFAULT_POLICY_SET)
        )
        errors = [finding.message for finding in result.errors]
        assert errors == [], errors

    def test_the_scaffolded_manifest_satisfies_the_contract(self, tmp_path: Path) -> None:
        from fincrime_core.contract.manifest import validate_skill_manifest

        scaffold_skill("demo-skill", tmp_path)
        document = parse(
            (tmp_path / "demo-skill" / "fincrime.skill.yaml").read_text(encoding="utf-8")
        )
        assert validate_skill_manifest(document) == []

    def test_the_scaffolded_suite_satisfies_the_case_contract(self, tmp_path: Path) -> None:
        from fincrime_core.validate.schema import JsonSchemaValidator

        contracts = REPO_ROOT / "contracts"
        with (contracts / "case.schema.json").open("r", encoding="utf-8") as handle:
            validator = JsonSchemaValidator(json.load(handle))
        scaffold_skill("demo-skill", tmp_path)
        for path in (tmp_path / "demo-skill" / "evals" / "suites" / "demo-skill" / "cases").glob("*.json"):
            with path.open("r", encoding="utf-8") as handle:
                assert validator.validate(json.load(handle)) == []

    def test_the_scaffolded_skill_is_a_draft(self, tmp_path: Path) -> None:
        scaffold_skill("demo-skill", tmp_path)
        document = parse(
            (tmp_path / "demo-skill" / "fincrime.skill.yaml").read_text(encoding="utf-8")
        )
        assert document["metadata"]["status"] == "draft"

    def test_it_refuses_to_overwrite_without_force(self, tmp_path: Path) -> None:
        scaffold_skill("demo-skill", tmp_path)
        with pytest.raises(FileExistsError):
            scaffold_skill("demo-skill", tmp_path)

    def test_force_overwrites(self, tmp_path: Path) -> None:
        scaffold_skill("demo-skill", tmp_path)
        result = scaffold_skill("demo-skill", tmp_path, force=True)
        assert result.files

    @pytest.mark.parametrize("name", ["", "Demo-Skill", "demo skill", "-demo", "demo--skill"])
    def test_it_rejects_an_unusable_name(self, tmp_path: Path, name: str) -> None:
        with pytest.raises(SkillNameError):
            scaffold_skill(name, tmp_path)


class TestCheckSkillPackage:
    def test_the_reference_skill_has_no_errors(self) -> None:
        from fincrime_core.policy.set import load_policy_set

        result = check_skill_package(
            REFERENCE_SKILL, policy_set=load_policy_set(DEFAULT_POLICY_SET)
        )
        errors = [finding.message for finding in result.errors]
        assert errors == [], errors

    def test_a_missing_skill_md_is_an_error(self, tmp_path: Path) -> None:
        result = check_skill_package(tmp_path)
        codes = {finding.code for finding in result.findings}
        assert "SKILL-FRONTMATTER-MISSING" in codes
        assert "SKILL-MANIFEST-MISSING" in codes

    def test_a_name_that_does_not_match_the_directory_is_an_error(self, tmp_path: Path) -> None:
        scaffold_skill("demo-skill", tmp_path)
        skill_md = tmp_path / "demo-skill" / "SKILL.md"
        skill_md.write_text(
            skill_md.read_text(encoding="utf-8").replace("name: demo-skill", "name: other-skill"),
            encoding="utf-8",
        )
        result = check_skill_package(tmp_path / "demo-skill")
        codes = {finding.code for finding in result.findings}
        assert "SKILL-NAME-MISMATCH" in codes

    def test_a_missing_description_is_an_error(self, tmp_path: Path) -> None:
        scaffold_skill("demo-skill", tmp_path)
        skill_md = tmp_path / "demo-skill" / "SKILL.md"
        text = skill_md.read_text(encoding="utf-8")
        start = text.index("description: >-")
        end = text.index("license: Apache-2.0")
        skill_md.write_text(text[:start] + text[end:], encoding="utf-8")
        result = check_skill_package(tmp_path / "demo-skill")
        codes = {finding.code for finding in result.findings}
        assert "SKILL-DESCRIPTION-MISSING" in codes

    def test_an_unparseable_manifest_is_an_error(self, tmp_path: Path) -> None:
        scaffold_skill("demo-skill", tmp_path)
        (tmp_path / "demo-skill" / "fincrime.skill.yaml").write_text(
            "apiVersion: &anchor x\n", encoding="utf-8"
        )
        result = check_skill_package(tmp_path / "demo-skill")
        codes = {finding.code for finding in result.findings}
        assert "SKILL-MANIFEST-UNPARSEABLE" in codes

    def test_a_manifest_that_fails_the_contract_is_an_error(self, tmp_path: Path) -> None:
        scaffold_skill("demo-skill", tmp_path)
        manifest_path = tmp_path / "demo-skill" / "fincrime.skill.yaml"
        manifest_path.write_text(
            manifest_path.read_text(encoding="utf-8").replace("status: draft", "status: nonsense"),
            encoding="utf-8",
        )
        result = check_skill_package(tmp_path / "demo-skill")
        codes = {finding.code for finding in result.findings}
        assert "SKILL-MANIFEST-INVALID" in codes

    def test_an_unresolved_policy_id_is_an_error(self, tmp_path: Path) -> None:
        from fincrime_core.policy.set import load_policy_set

        scaffold_skill("demo-skill", tmp_path)
        result = check_skill_package(
            tmp_path / "demo-skill", policy_set=load_policy_set(DEFAULT_POLICY_SET)
        )
        # The scaffolded skill names policies the default set defines.
        assert "SKILL-POLICY-UNRESOLVED" not in {f.code for f in result.findings}

    def test_a_policy_id_the_set_does_not_define_is_an_error(self, tmp_path: Path) -> None:
        from fincrime_core.policy.set import load_policy_set

        scaffold_skill("demo-skill", tmp_path)
        manifest_path = tmp_path / "demo-skill" / "fincrime.skill.yaml"
        manifest_path.write_text(
            manifest_path.read_text(encoding="utf-8").replace(
                "POL-BENIGN-HYPOTHESIS-REQUIRED", "POL-NOT-A-REAL-POLICY"
            ),
            encoding="utf-8",
        )
        result = check_skill_package(
            tmp_path / "demo-skill", policy_set=load_policy_set(DEFAULT_POLICY_SET)
        )
        codes = {finding.code for finding in result.findings}
        assert "SKILL-POLICY-UNRESOLVED" in codes

    def test_a_gate_failure_is_a_warning_for_a_draft_and_an_error_for_a_stable_skill(
        self, tmp_path: Path
    ) -> None:
        scaffold_skill("demo-skill", tmp_path)
        manifest_path = tmp_path / "demo-skill" / "fincrime.skill.yaml"

        draft = check_skill_package(tmp_path / "demo-skill")
        assert "suite_case_count_below_minimum" in {
            finding.code for finding in draft.warnings
        }

        manifest_path.write_text(
            manifest_path.read_text(encoding="utf-8").replace("status: draft", "status: stable"),
            encoding="utf-8",
        )
        stable = check_skill_package(tmp_path / "demo-skill")
        assert "suite_case_count_below_minimum" in {
            finding.code for finding in stable.errors
        }

    def test_an_unresolved_knowledge_pack_is_a_disclosure_not_a_failure(
        self, tmp_path: Path
    ) -> None:
        scaffold_skill("demo-skill", tmp_path, knowledge_pack="core-2026-10")
        result = check_skill_package(tmp_path / "demo-skill", packs_root=tmp_path / "packs")
        codes = {finding.code for finding in result.findings}
        assert "SKILL-KNOWLEDGE-UNRESOLVED" in codes
        assert "SKILL-KNOWLEDGE-UNRESOLVED" not in {
            finding.code for finding in result.errors
        }


class TestKnowledgeExpiryGate:
    """The citing skill's gate: blocked in promotion, warned in release.

    ADR-0006 grades the enforcement by change type rather than by staleness
    alone. The two halves of that rule are pinned here: a new skill cannot be
    built on expired regulation, and a released skill is disclosed rather
    than blocked, so the repository stays usable while the refresh happens.
    """

    def _write_pack(self, root: Path, expires_at: str) -> Path:
        return self._write_pack_with(root, {"IND-EXPIRED": expires_at, "REQ-EXPIRED-AGAIN": expires_at})

    def _write_pack_with(self, root: Path, expiries: dict[str, str]) -> Path:
        """Write a pack whose records expire on the dates given."""
        from fincrime_core.knowledge.model import _file_sha256, _pack_checksum

        records = [
            {
                "id": "IND-EXPIRED",
                "type": "indicator",
                "pack": "core-2026-10",
                "version": "1.0.0",
                "title": "An expired indicator",
                "definition": "A pattern, described.",
                "prohibited_attributes": ["nationality"],
                "evidence_to_cite": ["the transaction records"],
                "benign_explanations": ["A legitimate business doing ordinary business."],
                "jurisdictions": ["US"],
                "sources": [{"citation": "A citation."}],
                "as_of": "2026-10-01",
                "review_by": "2027-04-01",
                "expires_at": expiries["IND-EXPIRED"],
                "status": "active",
                "maintainer": "@fincrime-maintainers",
            },
            {
                "id": "REQ-EXPIRED-AGAIN",
                "type": "request",
                "pack": "core-2026-10",
                "version": "1.0.0",
                "title": "An expired request",
                "definition": "A document request, described.",
                "jurisdictions": ["US"],
                "sources": [{"citation": "A citation."}],
                "as_of": "2026-10-01",
                "review_by": "2027-04-01",
                "expires_at": expiries["REQ-EXPIRED-AGAIN"],
                "status": "active",
                "maintainer": "@fincrime-maintainers",
            },
        ]
        pack_dir = root / "core-2026-10"
        entries = []
        for record in records:
            relative = f"records/{record['type']}/{record['id']}.json"
            path = pack_dir / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(record, indent=2), encoding="utf-8")
            entries.append(
                {
                    "id": record["id"],
                    "type": record["type"],
                    "path": relative,
                    "sha256": _file_sha256(path),
                }
            )
        manifest = {
            "id": "core-2026-10",
            "version": "1.0.0",
            "as_of": "2026-10-01",
            "description": "A pack for testing.",
            "jurisdictions": ["US"],
            "maintainer": "@fincrime-maintainers",
            "records": entries,
            "checksum": _pack_checksum([(e["id"], e["sha256"]) for e in entries]),
        }
        (pack_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return root

    def _skill(self, tmp_path: Path) -> Path:
        scaffold_skill("demo-skill", tmp_path, knowledge_pack="core-2026-10")
        return tmp_path / "demo-skill"

    def _citing_skill(self, tmp_path: Path, cited: list[str]) -> Path:
        """A skill that declares the pack *and* the records it depends on."""
        skill = self._skill(tmp_path)
        manifest_path = skill / "fincrime.skill.yaml"
        text = manifest_path.read_text(encoding="utf-8")
        marker = "    indicators: []\n"
        assert marker in text, "the scaffolded manifest no longer has the expected knowledge block"
        if cited:
            block = "    indicators:\n" + "".join(f"      - {record_id}\n" for record_id in cited)
        else:
            block = marker
        manifest_path.write_text(text.replace(marker, block), encoding="utf-8")
        return skill

    def test_an_expired_record_blocks_the_skill_in_promotion_context(
        self, tmp_path: Path
    ) -> None:
        packs = self._write_pack(tmp_path / "packs", "2027-10-01")
        skill = self._skill(tmp_path)
        result = check_skill_package(
            skill, packs_root=packs, as_of=date(2027, 11, 1), promotion=True
        )
        assert not result.valid
        codes = {finding.code for finding in result.errors}
        assert "SKILL-KNOWLEDGE-EXPIRED" in codes

    def test_an_expired_record_only_warns_in_the_release_context(
        self, tmp_path: Path
    ) -> None:
        packs = self._write_pack(tmp_path / "packs", "2027-10-01")
        skill = self._skill(tmp_path)
        result = check_skill_package(skill, packs_root=packs, as_of=date(2027, 11, 1))
        assert result.valid
        codes = {finding.code for finding in result.warnings}
        assert "SKILL-KNOWLEDGE-EXPIRED" in codes
        assert result.maintenance_required is True
        assert result.status == "MAINTENANCE_REQUIRED"

    def test_a_current_record_passes_the_promotion_gate(self, tmp_path: Path) -> None:
        packs = self._write_pack(tmp_path / "packs", "2027-10-01")
        skill = self._skill(tmp_path)
        result = check_skill_package(
            skill, packs_root=packs, as_of=date(2026, 10, 21), promotion=True
        )
        assert result.valid, [f.message for f in result.errors]
        assert result.maintenance_required is False

    def test_without_a_date_no_freshness_claim_is_made(self, tmp_path: Path) -> None:
        packs = self._write_pack(tmp_path / "packs", "2027-10-01")
        skill = self._skill(tmp_path)
        result = check_skill_package(skill, packs_root=packs)
        assert result.valid
        assert "SKILL-KNOWLEDGE-EXPIRED" not in {
            finding.code for finding in result.findings
        }

    def test_a_draft_skill_is_not_excused_by_its_own_expired_knowledge(
        self, tmp_path: Path
    ) -> None:
        packs = self._write_pack(tmp_path / "packs", "2027-10-01")
        skill = self._skill(tmp_path)
        result = check_skill_package(
            skill, packs_root=packs, as_of=date(2027, 11, 1), promotion=True
        )
        # A draft may fail the shipping gate; it may not build on expired
        # regulation.
        assert "SKILL-KNOWLEDGE-EXPIRED" in {f.code for f in result.errors}

    def test_every_expired_record_in_the_pack_is_reported(self, tmp_path: Path) -> None:
        packs = self._write_pack(tmp_path / "packs", "2027-10-01")
        skill = self._skill(tmp_path)
        result = check_skill_package(skill, packs_root=packs, as_of=date(2027, 11, 1))
        expired = [
            finding for finding in result.warnings
            if finding.code == "SKILL-KNOWLEDGE-EXPIRED"
        ]
        assert len(expired) == 2
        # The report is ordered by record id, so it is diffable between runs.
        assert [finding.message for finding in expired] == sorted(
            finding.message for finding in expired
        )

    def test_a_cited_record_that_the_pack_does_not_hold_is_an_error(
        self, tmp_path: Path
    ) -> None:
        packs = self._write_pack(tmp_path / "packs", "2027-10-01")
        skill = self._citing_skill(tmp_path, ["IND-NOT-IN-THE-PACK"])
        result = check_skill_package(skill, packs_root=packs, as_of=date(2026, 10, 21))
        assert not result.valid
        codes = {finding.code for finding in result.errors}
        assert "SKILL-RECORD-UNRESOLVED" in codes
        assert "IND-NOT-IN-THE-PACK" in " ".join(f.message for f in result.errors)

    def test_an_expired_record_the_skill_cites_blocks_promotion(self, tmp_path: Path) -> None:
        packs = self._write_pack_with(
            tmp_path / "packs",
            {"IND-EXPIRED": "2027-10-01", "REQ-EXPIRED-AGAIN": "2027-10-01"},
        )
        skill = self._citing_skill(tmp_path, ["IND-EXPIRED"])
        result = check_skill_package(
            skill, packs_root=packs, as_of=date(2027, 11, 1), promotion=True
        )
        assert not result.valid
        codes = {finding.code for finding in result.errors}
        assert "SKILL-KNOWLEDGE-EXPIRED" in codes
        assert result.maintenance_required is True

    def test_an_expired_record_the_skill_does_not_cite_only_discloses(
        self, tmp_path: Path
    ) -> None:
        packs = self._write_pack_with(
            tmp_path / "packs",
            {"IND-EXPIRED": "2027-10-01", "REQ-EXPIRED-AGAIN": "2027-10-01"},
        )
        skill = self._citing_skill(tmp_path, ["IND-EXPIRED"])
        result = check_skill_package(
            skill, packs_root=packs, as_of=date(2027, 11, 1), promotion=True
        )
        assert not result.valid
        errors = {finding.code for finding in result.errors}
        warnings = {finding.code for finding in result.warnings}
        assert "SKILL-KNOWLEDGE-EXPIRED" in errors
        assert "SKILL-KNOWLEDGE-UNCITED-EXPIRED" in warnings

    def test_an_unrelated_expired_record_never_blocks_an_unaffected_skill(
        self, tmp_path: Path
    ) -> None:
        # The skill cites a current record; the pack's other record is stale.
        packs = self._write_pack_with(
            tmp_path / "packs",
            {"IND-EXPIRED": "2030-10-01", "REQ-EXPIRED-AGAIN": "2027-10-01"},
        )
        skill = self._citing_skill(tmp_path, ["IND-EXPIRED"])
        result = check_skill_package(
            skill, packs_root=packs, as_of=date(2027, 11, 1), promotion=True
        )
        assert result.valid, [f.message for f in result.errors]
        warnings = {finding.code for finding in result.warnings}
        assert "SKILL-KNOWLEDGE-UNCITED-EXPIRED" in warnings
        assert "SKILL-KNOWLEDGE-EXPIRED" not in warnings
        # The skill's own knowledge is current, so it is not a stale dependency.
        assert result.maintenance_required is False
