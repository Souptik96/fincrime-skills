"""Tests for the knowledge pack loader, its integrity checks, and expiry.

The pack loader's docstring used to promise that it rejected a pack whose
contents did not match its manifest, and it did not. These tests pin the
behaviour the docstring now describes: a pack that fails its integrity
checks produces findings, and never an exception.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from fincrime_core.knowledge.expiry import plan_expiry_actions
from fincrime_core.knowledge.model import load_pack, validate_pack

REPO_ROOT = Path(__file__).resolve().parents[3]
SAMPLE_PACK = REPO_ROOT / "knowledge" / "examples" / "sample-pack"
CORE_PACK = REPO_ROOT / "knowledge" / "packs" / "core-2026-10"


def _record(**overrides: Any) -> dict[str, Any]:
    record = {
        "id": "IND-TEST",
        "type": "indicator",
        "pack": "test-pack",
        "version": "1.0.0",
        "title": "A test indicator",
        "definition": "A pattern, described.",
        "prohibited_attributes": ["nationality"],
        "evidence_to_cite": ["the transaction records"],
        "benign_explanations": ["A legitimate business doing ordinary business."],
        "jurisdictions": ["US"],
        "sources": [{"citation": "A citation."}],
        "as_of": "2026-01-01",
        "review_by": "2026-07-01",
        "expires_at": "2027-01-01",
        "status": "active",
        "maintainer": "@someone",
    }
    record.update(overrides)
    return record


def _write_pack(root: Path, records: list[dict[str, Any]], **manifest_overrides: Any) -> Path:
    """Write a pack whose manifest is correct for the records given."""
    from fincrime_core.knowledge.model import _file_sha256, _pack_checksum

    entries = []
    for record in records:
        relative = f"records/{record['type']}/{record['id']}.json"
        path = root / relative
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
        "id": "test-pack",
        "version": "1.0.0",
        "as_of": "2026-01-01",
        "description": "A pack for testing.",
        "jurisdictions": ["US"],
        "maintainer": "@someone",
        "records": entries,
    }
    manifest.update(manifest_overrides)
    manifest["checksum"] = _pack_checksum([(e["id"], e["sha256"]) for e in entries])
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return root


class TestValidatePack:
    def test_a_correct_pack_validates(self, tmp_path: Path) -> None:
        _write_pack(tmp_path / "pack", [_record()])
        result = validate_pack(tmp_path / "pack")
        assert result.valid, [f.message for f in result.findings]
        assert result.checksum_ok
        assert len(result.records) == 1

    def test_a_tampered_record_is_rejected(self, tmp_path: Path) -> None:
        pack = _write_pack(tmp_path / "pack", [_record()])
        record_path = pack / "records" / "indicator" / "IND-TEST.json"
        record = json.loads(record_path.read_text(encoding="utf-8"))
        record["definition"] = "Something else entirely."
        record_path.write_text(json.dumps(record, indent=2), encoding="utf-8")

        result = validate_pack(pack)
        assert not result.valid
        assert "pack_record_hash_mismatch" in {finding.code for finding in result.findings}

    def test_an_unlisted_record_is_rejected(self, tmp_path: Path) -> None:
        pack = _write_pack(tmp_path / "pack", [_record()])
        extra = _record(id="IND-EXTRA")
        extra_path = pack / "records" / "indicator" / "IND-EXTRA.json"
        extra_path.write_text(json.dumps(extra, indent=2), encoding="utf-8")

        result = validate_pack(pack)
        assert not result.valid
        assert "pack_record_unlisted" in {finding.code for finding in result.findings}

    def test_a_missing_record_is_rejected(self, tmp_path: Path) -> None:
        pack = _write_pack(tmp_path / "pack", [_record()])
        (pack / "records" / "indicator" / "IND-TEST.json").unlink()

        result = validate_pack(pack)
        assert not result.valid
        assert "pack_record_missing" in {finding.code for finding in result.findings}

    def test_a_malformed_record_is_a_finding_not_an_exception(self, tmp_path: Path) -> None:
        pack = _write_pack(tmp_path / "pack", [_record()])
        (pack / "records" / "indicator" / "IND-TEST.json").write_text(
            "{ not json", encoding="utf-8"
        )

        result = validate_pack(pack)
        assert not result.valid
        assert "pack_record_unreadable" in {finding.code for finding in result.findings}

    def test_a_record_that_fails_the_record_contract_is_rejected(self, tmp_path: Path) -> None:
        pack = _write_pack(tmp_path / "pack", [_record()])
        record_path = pack / "records" / "indicator" / "IND-TEST.json"
        record = json.loads(record_path.read_text(encoding="utf-8"))
        del record["jurisdictions"]
        record_path.write_text(json.dumps(record, indent=2), encoding="utf-8")

        result = validate_pack(pack)
        assert not result.valid
        assert "pack_record_invalid" in {finding.code for finding in result.findings}

    def test_a_missing_manifest_is_a_finding_not_an_exception(self, tmp_path: Path) -> None:
        (tmp_path / "pack").mkdir()
        result = validate_pack(tmp_path / "pack")
        assert not result.valid
        assert "pack_manifest_missing" in {finding.code for finding in result.findings}

    def test_a_file_beside_the_records_is_not_read_as_a_record(self, tmp_path: Path) -> None:
        pack = _write_pack(tmp_path / "pack", [_record()])
        (pack / "notes.json").write_text(json.dumps({"id": "X", "type": "indicator"}), encoding="utf-8")

        result = validate_pack(pack)
        assert result.valid, [f.message for f in result.findings]
        assert len(result.records) == 1

    def test_the_committed_sample_pack_is_valid(self) -> None:
        result = validate_pack(SAMPLE_PACK)
        assert result.valid, [f.message for f in result.findings]
        assert result.checksum_ok

    def test_the_committed_core_pack_is_valid(self) -> None:
        result = validate_pack(CORE_PACK)
        assert result.valid, [f.message for f in result.findings]
        assert result.checksum_ok

    def test_the_core_pack_holds_the_expected_records(self) -> None:
        index = load_pack(CORE_PACK).index()
        assert len(index) == 83
        assert len(index.indicator_ids()) == 25
        assert len(index.by_type("typology")) == 8
        assert len(index.by_type("regulatory")) == 20
        assert len(index.by_type("request")) == 30

    def test_the_pack_exposes_its_indicator_and_record_ids(self) -> None:
        pack = load_pack(CORE_PACK)
        assert len(pack.indicator_ids()) == 25
        assert len(pack.record_ids()) == 83
        assert "IND-STRUCT-THRESHOLD-PROXIMITY" in pack.indicator_ids()
        assert all(
            record_id.startswith("IND-") for record_id in pack.indicator_ids()
        )

    def test_the_core_pack_is_current_as_of_its_own_date(self) -> None:
        result = validate_pack(CORE_PACK, promotion=True, as_of=date(2026, 10, 21))
        assert result.valid, [f.message for f in result.findings]

    def test_the_core_pack_blocks_promotion_once_it_is_stale(self) -> None:
        result = validate_pack(CORE_PACK, promotion=True, as_of=date(2027, 11, 1))
        assert not result.valid
        assert "pack_record_expired" in {f.code for f in result.findings}

    def test_the_core_pack_only_warns_in_the_release_context(self) -> None:
        result = validate_pack(CORE_PACK, promotion=False, as_of=date(2027, 11, 1))
        assert result.valid
        assert "pack_record_expired" in {f.code for f in result.findings}


class TestPackPromotionGate:
    """The pack promotion gate: graded by context, as ADR-0006 requires."""

    def _expired_pack(self, tmp_path: Path) -> Path:
        return _write_pack(
            tmp_path / "pack",
            [_record(expires_at="2027-01-01", review_by="2026-07-01")],
        )

    def test_an_expired_record_blocks_promotion(self, tmp_path: Path) -> None:
        pack = self._expired_pack(tmp_path)
        result = validate_pack(pack, promotion=True, as_of=date(2028, 1, 1))
        assert not result.valid
        expired = [f for f in result.findings if f.code == "pack_record_expired"]
        assert expired
        assert expired[0].severity == "error"
        assert expired[0].record_id == "IND-TEST"

    def test_an_expired_record_only_warns_in_the_release_context(self, tmp_path: Path) -> None:
        pack = self._expired_pack(tmp_path)
        result = validate_pack(pack, promotion=False, as_of=date(2028, 1, 1))
        assert result.valid
        expired = [f for f in result.findings if f.code == "pack_record_expired"]
        assert expired
        assert expired[0].severity == "warn"

    def test_the_same_pack_and_date_give_different_verdicts_by_context(
        self, tmp_path: Path
    ) -> None:
        pack = self._expired_pack(tmp_path)
        promoted = validate_pack(pack, promotion=True, as_of=date(2028, 1, 1))
        released = validate_pack(pack, promotion=False, as_of=date(2028, 1, 1))
        assert promoted.valid is False
        assert released.valid is True

    def test_a_current_record_passes_the_promotion_gate(self, tmp_path: Path) -> None:
        pack = _write_pack(tmp_path / "pack", [_record()])
        result = validate_pack(pack, promotion=True, as_of=date(2026, 10, 21))
        assert result.valid, [f.message for f in result.findings]
        assert "pack_record_expired" not in {f.code for f in result.findings}

    def test_without_a_date_no_freshness_claim_is_made(self, tmp_path: Path) -> None:
        pack = self._expired_pack(tmp_path)
        result = validate_pack(pack)
        assert result.valid
        assert "pack_record_expired" not in {f.code for f in result.findings}

    def test_a_review_due_record_is_disclosed_but_never_blocks(self, tmp_path: Path) -> None:
        pack = _write_pack(
            tmp_path / "pack",
            [_record(review_by="2026-07-01", expires_at="2027-01-01")],
        )
        result = validate_pack(pack, promotion=True, as_of=date(2026, 8, 1))
        assert result.valid
        assert "pack_record_review_due" in {f.code for f in result.findings}

    def test_the_date_may_be_given_as_a_string(self, tmp_path: Path) -> None:
        pack = self._expired_pack(tmp_path)
        result = validate_pack(pack, promotion=True, as_of="2028-01-01")
        assert not result.valid
        assert "pack_record_expired" in {f.code for f in result.findings}


class TestLoadPack:
    def test_a_malformed_record_is_skipped_not_raised(self, tmp_path: Path) -> None:
        pack = _write_pack(tmp_path / "pack", [_record()])
        (pack / "records" / "indicator" / "IND-TEST.json").write_text(
            "{ not json", encoding="utf-8"
        )

        loaded = load_pack(pack)
        assert loaded.records == ()

    def test_the_committed_sample_pack_loads(self) -> None:
        loaded = load_pack(SAMPLE_PACK)
        assert loaded.id == "sample-pack"
        assert {record.id for record in loaded.records} == {
            "IND-STRUCT-THRESHOLD-PROXIMITY",
            "REQ-SOF-001",
        }


class TestExpiryPlan:
    def test_a_current_record_needs_no_refresh(self) -> None:
        pack = load_pack(SAMPLE_PACK)
        actions = plan_expiry_actions(pack, date(2026, 10, 21))
        assert actions == ()

    def test_an_expired_record_produces_one_action(self) -> None:
        pack = load_pack(SAMPLE_PACK)
        actions = plan_expiry_actions(pack, date(2028, 1, 1))
        assert len(actions) == 2
        assert {action.record_id for action in actions} == {
            "IND-STRUCT-THRESHOLD-PROXIMITY",
            "REQ-SOF-001",
        }

    def test_the_action_carries_the_refresh_diff(self) -> None:
        pack = load_pack(SAMPLE_PACK)
        action = plan_expiry_actions(pack, date(2028, 1, 1))[0]
        assert action.issue_title.startswith("knowledge: refresh ")
        assert action.suggested_review_by > action.review_by
        assert action.suggested_expires_at > action.expires_at
        assert "review_by" in action.issue_body
        assert "expires_at" in action.issue_body
        assert "definition" in action.fields_to_reverify
        assert "benign_explanations" in action.fields_to_reverify

    def test_the_plan_is_deterministic(self) -> None:
        pack = load_pack(SAMPLE_PACK)
        first = plan_expiry_actions(pack, date(2028, 1, 1))
        second = plan_expiry_actions(pack, date(2028, 1, 1))
        assert [a.to_dict() for a in first] == [a.to_dict() for a in second]

    def test_a_review_due_record_is_distinguished_from_an_expired_one(self) -> None:
        pack = load_pack(SAMPLE_PACK)
        # The sample records are reviewed by 2027-04-01 and expire on
        # 2027-10-01, so a date between the two is a review, not an expiry.
        actions = plan_expiry_actions(pack, date(2027, 5, 1))
        assert {action.status for action in actions} == {"review_due"}

    def test_a_deprecated_record_is_reported_after_the_grace_period(self) -> None:
        pack = load_pack(SAMPLE_PACK)
        actions = plan_expiry_actions(pack, date(2028, 1, 1))
        assert {action.status for action in actions} == {"expired"}
        later = plan_expiry_actions(pack, date(2028, 12, 1))
        assert {action.status for action in later} == {"deprecation_due"}
