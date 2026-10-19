"""Shared fixtures for the core test suite."""

from __future__ import annotations

import copy
from typing import Any

import pytest

#: A minimal, valid evidence set. The transaction ids are chosen so that the
#: canonical example references in the docs resolve against it.
EVIDENCE_SET: dict[str, Any] = {
    "evidence_set_version": "fincrime/evidence-set/1.0.0",
    "alert": {
        "alert_id": "9930",
        "rule_id": "SC-TM-CASH-STRUCTURING",
        "rule_name": "Cash structuring",
        "triggered_at": "2026-03-12T00:00:00Z",
        "window": {"from": "2026-03-01T00:00:00Z", "to": "2026-03-12T00:00:00Z"},
        "subject_id": "5512",
    },
    "subject": {
        "subject_id": "5512",
        "type": "individual",
        "risk_rating": "medium",
        "segment": "small_business",
        "onboarded_at": "2023-04-02",
        "kyc_status": "current",
        "declared_profile": {
            "business": "Neighbourhood restaurant",
            "expected_activity": "Daily card and cash takings",
            "expected_monthly_volume": 42000,
            "cash_intensity": "medium",
        },
    },
    "transactions": [
        {
            "txn_id": "8841",
            "ts": "2026-03-04T10:12:00Z",
            "direction": "inbound",
            "amount": 9400,
            "currency": "USD",
            "channel": "cash",
            "branch_id": "BR-011",
        },
        {
            "txn_id": "8842",
            "ts": "2026-03-05T11:40:00Z",
            "direction": "inbound",
            "amount": 9700,
            "currency": "USD",
            "channel": "cash",
            "branch_id": "BR-022",
        },
        {
            "txn_id": "8843",
            "ts": "2026-03-07T09:05:00Z",
            "direction": "inbound",
            "amount": 9600,
            "currency": "USD",
            "channel": "cash",
            "branch_id": "BR-033",
        },
    ],
    "policies": {
        "policy_set_id": "firm-aml",
        "policy_set_version": "7.2",
        "jurisdictions": ["US"],
        "scenarios": [
            {
                "rule_id": "SC-TM-CASH-STRUCTURING",
                "name": "Cash structuring",
                "question": "Does cash activity deviate from the expected profile in a way consistent with evasion of reporting thresholds?",
                "severity": "high",
                "min_window_coverage": 0.8,
            }
        ],
        "thresholds": [
            {
                "policy_id": "POL-STRUCT-THRESHOLD-PROXIMITY",
                "name": "Currency transaction reporting threshold",
                "value": 10000,
                "currency": "USD",
                "jurisdictions": ["US"],
                "effective_from": "2020-01-01",
            }
        ],
    },
    "documents": [
        {
            "doc_id": "kYC-2291",
            "kind": "kyc_docket",
            "present": True,
            "fields": {"business_registration_number": "BR-8891"},
        }
    ],
}

#: A fully conformant artifact. Every test that needs a valid baseline starts
#: from this document, so a change to the contract that breaks it is caught
#: immediately.
VALID_ARTIFACT: dict[str, Any] = {
    "contract_version": "fincrime/finding/1.0.0",
    "artifact": {
        "skill_id": "alert-triage",
        "skill_version": "1.0.0",
        "artifact_type": "triage_report",
        "subject_ids": ["5512"],
        "jurisdictions": ["US"],
        "created_at": "2026-03-13T09:00:00Z",
        "completeness": "complete",
    },
    "provenance": {
        "skill_id": "alert-triage",
        "skill_version": "1.0.0",
        "model": {"provider": "example", "id": "example-model-1", "temperature": 0, "seed": 42},
        "prompt_sha256": "a" * 64,
        "evidence_set_sha256": "b" * 64,
        "knowledge_pack": {"id": "fincrime-knowledge", "version": "core-2026-10", "as_of": "2026-10-01"},
        "policy_set": {"id": "firm-aml", "version": "7.2"},
        "run_id": "run-0001",
        "timestamp": "2026-03-13T09:00:00Z",
    },
    "claims": [
        {
            "id": "C-001",
            "class": "fact",
            "statement": "Three cash deposits were made between 2026-03-04 and 2026-03-07.",
            "evidence_refs": ["txn:8841#/amount", "txn:8842#/amount", "txn:8843#/amount"],
            "confidence": {"level": "high", "basis": "Read directly from the transaction records."},
        },
        {
            "id": "C-002",
            "class": "indicator",
            "statement": "Cash deposits cluster immediately below the currency transaction reporting threshold.",
            "evidence_refs": ["txn:8841#/amount", "txn:8842#/amount", "txn:8843#/amount"],
            "indicator_ids": ["IND-STRUCT-THRESHOLD-PROXIMITY"],
            "policy_ids": ["POL-STRUCT-THRESHOLD-PROXIMITY"],
            "confidence": {"level": "moderate", "basis": "Threshold proximity is measured; intent is not established."},
        },
        {
            "id": "C-003",
            "class": "hypothesis",
            "epistemic_type": "adverse_reading",
            "statement": "The cash activity may be structured to avoid the reporting threshold.",
            "evidence_refs": ["txn:8841#/amount"],
            "falsifier": "Payroll or point-of-sale settlement records showing the cash as genuine revenue.",
            "confidence": {"level": "low", "basis": "The decisive corroborating evidence is absent."},
        },
        {
            "id": "C-004",
            "class": "hypothesis",
            "epistemic_type": "benign_reading",
            "statement": "The cash activity may be ordinary revenue for a cash-intensive business.",
            "evidence_refs": ["txn:8841#/amount"],
            "falsifier": "Absence of payroll or point-of-sale settlement records supporting the declared business.",
            "confidence": {"level": "low", "basis": "The decisive corroborating evidence is absent."},
        },
        {
            "id": "C-005",
            "class": "risk_assessment",
            "statement": "Threshold proximity is high; documentation support for the declared business is absent.",
            "evidence_refs": ["txn:8841#/amount"],
            "confidence": {"level": "low", "basis": "Only one side of the hypothesis pair is evidenced."},
        },
        {
            "id": "C-006",
            "class": "recommendation",
            "statement": "Request source-of-funds documentation and six months of settlement records, then re-triage.",
            "evidence_refs": ["txn:8841#/amount"],
            "human_approval_required": True,
            "confidence": {"level": "moderate", "basis": "Follows the documented request catalogue."},
        },
    ],
    "evidence_inventory": [
        {"source_id": "txn:8841", "kind": "transaction", "present": True, "decisive": True},
        {"source_id": "txn:8842", "kind": "transaction", "present": True},
        {"source_id": "txn:8843", "kind": "transaction", "present": True},
        {"source_id": "subject:5512", "kind": "subject", "present": True},
        {"source_id": "doc:kYC-2291", "kind": "document", "present": True},
    ],
    "gaps": [
        {
            "gap_id": "G-01",
            "description": "Payroll or point-of-sale settlement records supporting the declared business are absent.",
            "decisive": True,
            "blocks_conclusion": True,
        }
    ],
    "human_decision_required": [
        {
            "decision_id": "D-01",
            "question": "Whether to escalate this alert to a level 2 investigator.",
            "owner_role": "AML Level 1 Investigator",
            "would_change_if": ["Receipt of settlement records consistent with the declared business."],
        }
    ],
}


@pytest.fixture()
def evidence_set() -> dict[str, Any]:
    return copy.deepcopy(EVIDENCE_SET)


@pytest.fixture()
def valid_artifact() -> dict[str, Any]:
    return copy.deepcopy(VALID_ARTIFACT)


@pytest.fixture()
def known_ids() -> dict[str, Any]:
    return {
        "known_indicator_ids": ["IND-STRUCT-THRESHOLD-PROXIMITY"],
        "known_knowledge_ids": [],
        "expired_knowledge_ids": [],
    }
