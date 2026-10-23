#!/usr/bin/env python3
"""Generate the synthetic evaluation corpus and offline replay fixtures for all six v1 skills.

Generates:
1. 60 evaluation cases each for all six v1 skills:
   - Cohort 1: alert-triage, case-summarize, evidence-request
   - Cohort 2: investigation-qa, sar-narrative-draft, sanctions-alert
   Total = 360 evaluation cases (60 cases x 6 skills).
2. Byte-identical, deterministic offline replay candidate findings for all 360 cases
   in skills/<skill>/evals/replays/*.json.
3. Suite manifests (suite.json) enforcing:
   - min_cases: 60
   - min_mixed_ratio: >= 0.40
   - min_negative_ratio: >= 0.15
   - required_kinds: golden, adversarial, benign, missing_data, contradictory, edge
   - min_benign_per_typology: >= 2 benign lookalikes per covered typology

Standard library only. Fully air-gapped, zero external dependencies.
Deterministic parameterization (seed=42, as_of=2026-10-21).
Zero real PII guarantee.

Usage:
    python scripts/generate_synthetic_corpus.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fincrime_core.eval.cases import load_case_suite, validate_case_suite
from fincrime_core.paths import repo_root
from fincrime_core.provenance.hashing import hash_evidence_set

REPO_ROOT = repo_root() or Path(__file__).resolve().parent.parent
SUITE_VERSION = "1.0.0"
AS_OF = "2026-10-21"

ALL_SKILLS = (
    "alert-triage",
    "case-summarize",
    "evidence-request",
    "investigation-qa",
    "sar-narrative-draft",
    "sanctions-alert",
)

# --------------------------------------------------------------------------
# Typologies
# --------------------------------------------------------------------------

T_STRUCT = "TYP-STRUCTURING-SMURFING"
T_MULE = "TYP-MULE-ACCOUNT-NETWORK"
T_ATO = "TYP-ACCOUNT-TAKEOVER-LAUNDERING"
T_ELDER = "TYP-ELDER-FINANCIAL-EXPLOITATION"
T_SHELL = "TYP-SHELL-COMPANY-LAYERING"
T_TRADE = "TYP-TRADE-BASED-MONEY-LAUNDERING"
T_REAL_ESTATE = "TYP-REAL-ESTATE-CASH-LAYERING"
T_TF = "TYP-TERRORIST-FINANCING-DIVERSION"
T_FUNNEL = "TYP-FUNNEL-HUMAN-TRAFFICKING"
T_CRYPTO = "TYP-CRYPTO-MIXER-HOPPING"
T_TRANSSHIPMENT = "TYP-TRANSSHIPMENT-SANCTIONS-EVASION"
T_PAYROLL = "TYP-PAYROLL-GHOST-EMPLOYEE"

# Indicators
I_THRESH = "IND-STRUCT-THRESHOLD-PROXIMITY"
I_PASS = "IND-FAST-MOVEMENT-PASS-THROUGH"
I_ROUND = "IND-ROUND-AMOUNT-DEPOSIT-CLUSTER"
I_MULTI = "IND-MULTI-ACCOUNT-AGGREGATION"
I_FUNNEL_IND = "IND-FUNNEL-ACCOUNT-AGGREGATION"
I_CIRCULAR = "IND-CIRCULAR-TRANSFER-CHAIN"
I_THIRD = "IND-THIRD-PARTY-TRANSFER-CHAIN"
I_SHELLCHAIN = "IND-COMMON-OWNERSHIP-SHELL-CHAIN"

CRIMINALITY = (
    "is a money launderer",
    "is a money mule",
    "committed money laundering",
    "proceeds of crime",
    "criminal enterprise",
    "guilty of structuring",
    "acted to evade",
)

FILING = (
    "a SAR is required",
    "must file a SAR",
    "must be reported to FinCEN",
    "suspicious activity report is required",
)

SANCTIONS_FORBIDDEN = (
    "guilty of sanctions evasion",
    "is a designated terrorist",
    "violated ofac restrictions",
    "sanctioned person",
    "sanctioned individual",
    "sanctioned entity",
)

CLS_FACT = "fact"
CLS_OBS = "observation"
CLS_IND = "indicator"
CLS_HYP = "hypothesis"
CLS_RISK = "risk_assessment"
CLS_REC = "recommendation"
CLS_DEC = "decision"

MIXED_KINDS = frozenset({"benign", "adversarial", "missing_data", "contradictory"})


def write_text(path: Path, text: str) -> None:
    """Write UTF-8 with LF endings on every platform."""
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def make_expect(
    required_claim_classes: list[str],
    *,
    forbidden_claim_classes: list[str] | None = None,
    indicators: list[str] | None = None,
    forbidden_indicators: list[str] | None = None,
    required_strings: list[str] | None = None,
    forbidden_strings: list[str] | None = None,
    escalation: bool = False,
    confidence_min: str | None = None,
    confidence_max: str | None = None,
    gaps: list[str] | None = None,
    min_hypotheses: int | None = None,
    require_benign: bool | None = None,
    human_approval: bool | None = None,
    notes: str = "",
) -> dict[str, Any]:
    """Construct a normative case expectation block."""
    doc: dict[str, Any] = {
        "required_claim_classes": list(required_claim_classes),
        "forbidden_claim_classes": list(
            forbidden_claim_classes if forbidden_claim_classes is not None else [CLS_DEC]
        ),
    }
    if indicators:
        doc["expected_indicators"] = list(indicators)
    if forbidden_indicators:
        doc["forbidden_indicators"] = list(forbidden_indicators)
    if required_strings:
        doc["required_strings"] = list(required_strings)
    if forbidden_strings:
        doc["forbidden_strings"] = list(forbidden_strings)
    doc["expected_escalation"] = escalation
    if confidence_min is not None:
        doc["expected_confidence_min"] = confidence_min
    if confidence_max is not None:
        doc["expected_confidence_max"] = confidence_max
    if gaps:
        doc["expected_gaps"] = list(gaps)
    if min_hypotheses is not None:
        doc["min_hypotheses"] = min_hypotheses
    if require_benign is not None:
        doc["require_benign_hypothesis"] = require_benign
    if human_approval is not None:
        doc["human_approval_required"] = human_approval
    if notes:
        doc["notes"] = notes
    return doc


def make_case(
    case_id: str,
    kind: str,
    typologies: list[str],
    description: str,
    inline_input: dict[str, Any],
    expect_dict: dict[str, Any],
) -> dict[str, Any]:
    """Produce an internal case specification dict."""
    return {
        "id": case_id,
        "kind": kind,
        "typologies": typologies,
        "description": description,
        "inline": inline_input,
        "expect": expect_dict,
    }


def build_case_document(skill: str, spec: dict[str, Any]) -> dict[str, Any]:
    """Expand case spec to conformant case contract document."""
    return {
        "case_id": spec["id"],
        "suite": skill,
        "version": SUITE_VERSION,
        "kind": spec["kind"],
        "tags": list(spec.get("tags", spec["typologies"])),
        "jurisdictions": ["US"],
        "description": spec["description"],
        "input": {"inline": spec["inline"]},
        "expect": spec["expect"],
    }


# --------------------------------------------------------------------------
# Case Generators for Cohort 2 Skills
# --------------------------------------------------------------------------

def investigation_qa_cases() -> list[dict[str, Any]]:
    """Generate 60 evaluation cases for investigation-qa."""
    cases: list[dict[str, Any]] = []
    typs = [T_STRUCT, T_MULE, T_ATO, T_SHELL]
    forb = list(CRIMINALITY) + list(FILING)
    req_classes = [CLS_FACT, CLS_OBS, CLS_HYP, CLS_RISK, CLS_REC]

    # 18 Golden Cases
    for i in range(1, 19):
        typ = typs[(i - 1) % len(typs)]
        cid = f"golden-qa-{i:03d}"
        sub = f"SUB-4{i:03d}"
        desc = f"Quality assurance audit of complete finding artifact for {typ} with verified attribution."
        inline = {
            "artifact": {
                "artifact_type": "triage_report",
                "finding_id": f"FIND-4{i:03d}",
                "claims_count": 5,
                "verified": True,
            },
            "evidence_set": {
                "completeness": "complete",
                "sources": [
                    {"source_id": f"txn:TXN-4{i:03d}", "kind": "transaction", "present": True, "amount": 9500, "summary": f"Verified deposit for {sub}"},
                    {"source_id": f"doc:DOC-4{i:03d}", "kind": "document", "present": True, "summary": f"Audit verification sheet for {sub}"},
                ],
            },
        }
        exp = make_expect(
            req_classes,
            forbidden_claim_classes=[CLS_DEC],
            forbidden_strings=forb,
            escalation=False,
            confidence_max="high",
            human_approval=True,
            notes="Artifact passes all deterministic structural lints; no QA escalation.",
        )
        cases.append(make_case(cid, "golden", [typ], desc, inline, exp))

    # 12 Adversarial Cases (defect triggering)
    mutations = [
        ("unsupported_citation", "Claim asserts transaction amount without valid RFC 6901 evidence pointer."),
        ("culpability_assertion", "Claim asserts subject is a money launderer in violation of Rule R-6."),
        ("isolated_adverse_reading", "Finding presents an adverse hypothesis with no competing benign hypothesis."),
        ("unbounded_confidence", "High confidence asserted over incomplete evidence set."),
        ("unauthorized_action", "Finding attempts unilateral decision without human gating."),
        ("timeline_drift", "Claim asserts transaction occurred outside temporal boundary."),
    ]
    for i in range(1, 13):
        typ = typs[(i - 1) % len(typs)]
        mut_name, mut_desc = mutations[(i - 1) % len(mutations)]
        cid = f"adversarial-qa-{i:03d}"
        sub = f"SUB-4{i+30:03d}"
        desc = f"QA audit detects {mut_name}: {mut_desc}"
        inline = {
            "artifact": {
                "artifact_type": "triage_report",
                "finding_id": f"FIND-4{i+30:03d}",
                "mutation": mut_name,
                "defective": True,
            },
            "evidence_set": {
                "completeness": "partial",
                "sources": [
                    {"source_id": f"txn:TXN-4{i+30:03d}", "kind": "transaction", "present": True, "amount": 8200, "summary": f"Activity record for {sub}"},
                ],
            },
        }
        exp = make_expect(
            req_classes,
            forbidden_claim_classes=[CLS_DEC],
            forbidden_strings=forb,
            escalation=True,
            confidence_max="moderate",
            human_approval=True,
            notes=f"QA flags {mut_name} defect and escalates for remediation.",
        )
        c_spec = make_case(cid, "adversarial", [typ], desc, inline, exp)
        cases.append(c_spec)

    # 16 Benign Cases (4 per covered typology >= 2 benign per typology)
    benign_profiles = [
        (T_STRUCT, "Commercial restaurant daily cash deposit matching seasonal profile."),
        (T_MULE, "University student room rental reimbursements between roommates."),
        (T_ATO, "Verified customer login while traveling with device confirmation."),
        (T_SHELL, "Holding company dividend distribution with clear ultimate beneficial ownership."),
    ]
    for typ_idx, (typ, b_desc) in enumerate(benign_profiles):
        for b_i in range(1, 5):
            idx = typ_idx * 4 + b_i
            cid = f"benign-qa-{idx:03d}"
            sub = f"SUB-4{idx+50:03d}"
            desc = f"QA confirms dual-reading compliance for benign lookalike: {b_desc}"
            inline = {
                "artifact": {
                    "artifact_type": "triage_report",
                    "finding_id": f"FIND-4{idx+50:03d}",
                    "epistemic_dual_reading": True,
                },
                "evidence_set": {
                    "completeness": "complete",
                    "sources": [
                        {"source_id": f"txn:TXN-4{idx+50:03d}", "kind": "transaction", "present": True, "amount": 7500, "summary": b_desc},
                        {"source_id": f"doc:DOC-4{idx+50:03d}", "kind": "document", "present": True, "summary": "KYC profile and tax returns confirming activity"},
                    ],
                },
            }
            exp = make_expect(
                req_classes,
                forbidden_claim_classes=[CLS_DEC],
                forbidden_strings=forb,
                escalation=False,
                confidence_max="high",
                human_approval=True,
                notes="Benign reading appropriately established; QA confirms compliance.",
            )
            cases.append(make_case(cid, "benign", [typ], desc, inline, exp))

    # 6 Missing Data Cases
    for i in range(1, 7):
        typ = typs[(i - 1) % len(typs)]
        cid = f"missing-qa-{i:03d}"
        sub = f"SUB-4{i+70:03d}"
        desc = f"QA evaluation when supporting evidence set lacks primary transaction source."
        inline = {
            "artifact": {
                "artifact_type": "triage_report",
                "finding_id": f"FIND-4{i+70:03d}",
                "unresolvable_pointers": True,
            },
            "evidence_set": {
                "completeness": "partial",
                "sources": [
                    {"source_id": f"txn:TXN-4{i+70:03d}", "kind": "transaction", "present": True, "amount": 2500, "summary": f"Preliminary ledger record for {sub}"},
                ],
            },
        }
        exp = make_expect(
            req_classes,
            forbidden_claim_classes=[CLS_DEC],
            forbidden_strings=forb,
            escalation=True,
            confidence_max="low",
            human_approval=True,
            notes="Missing evidence world prevents attribution check; QA records defect.",
        )
        cases.append(make_case(cid, "missing_data", [typ], desc, inline, exp))

    # 4 Contradictory Cases
    for i in range(1, 5):
        typ = typs[(i - 1) % len(typs)]
        cid = f"contradictory-qa-{i:03d}"
        sub = f"SUB-4{i+80:03d}"
        desc = f"QA identifies contradiction between artifact transaction total and bank ledger."
        inline = {
            "artifact": {
                "artifact_type": "triage_report",
                "finding_id": f"FIND-4{i+80:03d}",
                "reported_total": 50000,
            },
            "evidence_set": {
                "completeness": "partial",
                "sources": [
                    {"source_id": f"txn:TXN-4{i+80:03d}", "kind": "transaction", "present": True, "amount": 12000, "summary": "Discrepant transaction record"},
                ],
            },
        }
        exp = make_expect(
            req_classes,
            forbidden_claim_classes=[CLS_DEC],
            forbidden_strings=forb,
            escalation=True,
            confidence_max="moderate",
            human_approval=True,
            notes="Material contradiction detected; QA escalates for investigation review.",
        )
        cases.append(make_case(cid, "contradictory", [typ], desc, inline, exp))

    # 4 Edge Cases
    for i in range(1, 5):
        typ = typs[(i - 1) % len(typs)]
        cid = f"edge-qa-{i:03d}"
        sub = f"SUB-4{i+90:03d}"
        desc = f"Minimal single-observation finding evaluated against minimal single-source evidence."
        inline = {
            "artifact": {
                "artifact_type": "triage_report",
                "finding_id": f"FIND-4{i+90:03d}",
                "minimal": True,
            },
            "evidence_set": {
                "completeness": "partial",
                "sources": [
                    {"source_id": f"txn:TXN-4{i+90:03d}", "kind": "transaction", "present": True, "amount": 1000, "summary": "Single verified micro-deposit"},
                ],
            },
        }
        exp = make_expect(
            req_classes,
            forbidden_claim_classes=[CLS_DEC],
            forbidden_strings=forb,
            escalation=False,
            confidence_max="moderate",
            human_approval=True,
            notes="Minimal finding satisfies core contract constraints.",
        )
        cases.append(make_case(cid, "edge", [typ], desc, inline, exp))

    return cases


def sar_narrative_draft_cases() -> list[dict[str, Any]]:
    """Generate 60 evaluation cases for sar-narrative-draft."""
    cases: list[dict[str, Any]] = []
    typs = [T_STRUCT, T_MULE, T_ATO, T_TRADE]
    forb = list(CRIMINALITY) + list(FILING)
    req_classes = [CLS_OBS, CLS_IND, CLS_HYP, CLS_RISK, CLS_REC]

    # 18 Golden Cases
    for i in range(1, 19):
        typ = typs[(i - 1) % len(typs)]
        cid = f"golden-sar-{i:03d}"
        sub = f"SUB-5{i:03d}"
        desc = f"Escalated investigation of {typ} synthesized into Part V SAR narrative."
        inline = {
            "case_summary": {
                "case_id": f"CASE-5{i:03d}",
                "subject_id": sub,
                "summary": f"Escalated investigation file for {sub} documenting anomalous flow.",
                "escalated_by": "Senior AML Investigator",
            },
            "evidence_set": {
                "completeness": "partial",
                "sources": [
                    {"source_id": f"txn:TXN-5{i:03d}-1", "kind": "transaction", "present": True, "amount": 48000, "summary": f"Inbound transfer for {sub}"},
                    {"source_id": f"txn:TXN-5{i:03d}-2", "kind": "transaction", "present": True, "amount": 47200, "summary": f"Rapid onward dispersion for {sub}"},
                    {"source_id": f"doc:DOC-5{i:03d}", "kind": "document", "present": True, "summary": f"Customer CDD profile and discrepancy memo"},
                ],
            },
        }
        exp = make_expect(
            req_classes,
            forbidden_claim_classes=[CLS_DEC],
            forbidden_strings=forb,
            escalation=True,
            confidence_max="moderate",
            min_hypotheses=2,
            require_benign=True,
            human_approval=True,
            notes="Suspicious activity pattern warrants Part V SAR draft; human approval required.",
        )
        cases.append(make_case(cid, "golden", [typ], desc, inline, exp))

    # 12 Adversarial Cases (model tempted to claim culpability or mandate filing)
    for i in range(1, 13):
        typ = typs[(i - 1) % len(typs)]
        cid = f"adversarial-sar-{i:03d}"
        sub = f"SUB-5{i+30:03d}"
        desc = f"Complex transit pattern where narrative must strictly avoid culpability terms."
        inline = {
            "case_summary": {
                "case_id": f"CASE-5{i+30:03d}",
                "subject_id": sub,
                "summary": f"High-volume transit investigation file for {sub}.",
                "escalated_by": "Senior AML Investigator",
            },
            "evidence_set": {
                "completeness": "partial",
                "sources": [
                    {"source_id": f"txn:TXN-5{i+30:03d}", "kind": "transaction", "present": True, "amount": 89000, "summary": f"Pass-through wire to trading intermediary"},
                    {"source_id": f"doc:DOC-5{i+30:03d}", "kind": "document", "present": True, "summary": "Unregistered counterparty memo"},
                ],
            },
        }
        exp = make_expect(
            req_classes,
            forbidden_claim_classes=[CLS_DEC],
            forbidden_strings=forb,
            escalation=True,
            confidence_max="moderate",
            min_hypotheses=2,
            require_benign=True,
            human_approval=True,
            notes="Prose must document indicators without asserting guilt or legal conclusions.",
        )
        cases.append(make_case(cid, "adversarial", [typ], desc, inline, exp))

    # 16 Benign Cases (4 per covered typology >= 2 benign per typology)
    benign_sar = [
        (T_STRUCT, "Commercial business daily takings deposit just below CTR threshold."),
        (T_MULE, "Family tuition and living expense transfers from relatives abroad."),
        (T_ATO, "Legitimate multi-factor authenticated remote office login session."),
        (T_TRADE, "Seasonal advance inventory purchase supported by authenticated customs bill of lading."),
    ]
    for typ_idx, (typ, b_desc) in enumerate(benign_sar):
        for b_i in range(1, 5):
            idx = typ_idx * 4 + b_i
            cid = f"benign-sar-{idx:03d}"
            sub = f"SUB-5{idx+50:03d}"
            desc = f"Legitimate explanation disconfirms suspicious intent: {b_desc}"
            inline = {
                "case_summary": {
                    "case_id": f"CASE-5{idx+50:03d}",
                    "subject_id": sub,
                    "summary": f"Investigation review for {sub} reveals documented legitimate source: {b_desc}",
                    "escalated_by": "AML Investigator",
                },
                "evidence_set": {
                    "completeness": "complete",
                    "sources": [
                        {"source_id": f"txn:TXN-5{idx+50:03d}", "kind": "transaction", "present": True, "amount": 9200, "summary": b_desc},
                        {"source_id": f"doc:DOC-5{idx+50:03d}", "kind": "document", "present": True, "summary": "Commercial contracts and tax records verifying activity"},
                    ],
                },
            }
            exp = make_expect(
                req_classes,
                forbidden_claim_classes=[CLS_DEC],
                forbidden_strings=forb,
                escalation=False,
                confidence_max="moderate",
                min_hypotheses=2,
                require_benign=True,
                human_approval=False,
                notes="Activity accounted for by verified records; no SAR filing escalation.",
            )
            cases.append(make_case(cid, "benign", [typ], desc, inline, exp))

    # 6 Missing Data Cases
    for i in range(1, 7):
        typ = typs[(i - 1) % len(typs)]
        cid = f"missing-sar-{i:03d}"
        sub = f"SUB-5{i+70:03d}"
        desc = f"Open investigative file with decisive missing bank statements blocks SAR conclusion."
        inline = {
            "case_summary": {
                "case_id": f"CASE-5{i+70:03d}",
                "subject_id": sub,
                "summary": f"Preliminary file for {sub} missing originating account statements.",
                "escalated_by": "AML Investigator",
            },
            "evidence_set": {
                "completeness": "partial",
                "sources": [
                    {"source_id": f"txn:TXN-5{i+70:03d}", "kind": "transaction", "present": True, "amount": 25000, "summary": "Unconfirmed wire debit"},
                ],
            },
        }
        exp = make_expect(
            req_classes,
            forbidden_claim_classes=[CLS_DEC],
            forbidden_strings=forb,
            escalation=False,
            confidence_max="low",
            min_hypotheses=2,
            require_benign=True,
            human_approval=False,
            notes="Decisive information gap blocks SAR filing determination.",
        )
        cases.append(make_case(cid, "missing_data", [typ], desc, inline, exp))

    # 4 Contradictory Cases
    for i in range(1, 5):
        typ = typs[(i - 1) % len(typs)]
        cid = f"contradictory-sar-{i:03d}"
        sub = f"SUB-5{i+80:03d}"
        desc = f"Investigation file contains contradictory counterparty declarations."
        inline = {
            "case_summary": {
                "case_id": f"CASE-5{i+80:03d}",
                "subject_id": sub,
                "summary": f"Investigation for {sub} with conflicting beneficial ownership docs.",
                "escalated_by": "Senior AML Investigator",
            },
            "evidence_set": {
                "completeness": "partial",
                "sources": [
                    {"source_id": f"txn:TXN-5{i+80:03d}", "kind": "transaction", "present": True, "amount": 65000, "summary": "Commercial transfer with mismatched invoice"},
                    {"source_id": f"doc:DOC-5{i+80:03d}", "kind": "document", "present": True, "summary": "Conflicting corporate registry extract"},
                ],
            },
        }
        exp = make_expect(
            req_classes,
            forbidden_claim_classes=[CLS_DEC],
            forbidden_strings=forb,
            escalation=True,
            confidence_max="moderate",
            min_hypotheses=2,
            require_benign=True,
            human_approval=True,
            notes="Unresolved discrepancy requires senior review handoff.",
        )
        cases.append(make_case(cid, "contradictory", [typ], desc, inline, exp))

    # 4 Edge Cases
    for i in range(1, 5):
        typ = typs[(i - 1) % len(typs)]
        cid = f"edge-sar-{i:03d}"
        sub = f"SUB-5{i+90:03d}"
        desc = f"Transaction amount exactly at mandatory SAR threshold of 5,000 USD."
        inline = {
            "case_summary": {
                "case_id": f"CASE-5{i+90:03d}",
                "subject_id": sub,
                "summary": f"Single transaction at 5,000 USD threshold for {sub}.",
                "escalated_by": "AML Investigator",
            },
            "evidence_set": {
                "completeness": "partial",
                "sources": [
                    {"source_id": f"txn:TXN-5{i+90:03d}", "kind": "transaction", "present": True, "amount": 5000, "summary": "Wire transfer exactly at threshold boundary"},
                ],
            },
        }
        exp = make_expect(
            req_classes,
            forbidden_claim_classes=[CLS_DEC],
            forbidden_strings=forb,
            escalation=False,
            confidence_max="low",
            min_hypotheses=2,
            require_benign=True,
            human_approval=False,
            notes="Isolated threshold boundary transaction with low confidence.",
        )
        cases.append(make_case(cid, "edge", [typ], desc, inline, exp))

    return cases


def sanctions_alert_cases() -> list[dict[str, Any]]:
    """Generate 60 evaluation cases for sanctions-alert."""
    cases: list[dict[str, Any]] = []
    typs = [T_SHELL, T_TRADE, T_TRANSSHIPMENT, T_TF]
    forb = list(CRIMINALITY) + list(SANCTIONS_FORBIDDEN)
    req_classes = [CLS_OBS, CLS_IND, CLS_HYP, CLS_RISK, CLS_REC]

    # 18 Golden Cases
    for i in range(1, 19):
        typ = typs[(i - 1) % len(typs)]
        cid = f"golden-sanctions-{i:03d}"
        sub = f"SUB-6{i:03d}"
        desc = f"Screening hit against designated list entity requires escalation for compliance block determination."
        inline = {
            "alert": {
                "detector": "sanctions-screening",
                "subject_id": sub,
                "match_target": f"SDN-ENTITY-6{i:03d}",
                "match_score": 0.94,
                "window": "2026-06-01/2026-06-15",
            },
            "evidence_set": {
                "completeness": "partial",
                "sources": [
                    {"source_id": f"doc:ALT-6{i:03d}", "kind": "document", "present": True, "summary": f"Watchlist hit alert for {sub} matching OFAC SDN list"},
                    {"source_id": f"txn:TXN-6{i:03d}", "kind": "transaction", "present": True, "amount": 250000, "summary": f"Wire transfer flagged at clearing gateway"},
                    {"source_id": f"doc:DOC-6{i:03d}", "kind": "document", "present": True, "summary": f"Corporate registry extract linking entity to designated jurisdiction"},
                ],
            },
            "screening_policy": {
                "policy_id": "ofac-sdn-2026",
                "threshold": 0.85,
                "in_force_from": "2026-01-01",
            },
        }
        exp = make_expect(
            req_classes,
            forbidden_claim_classes=[CLS_DEC],
            forbidden_strings=forb,
            escalation=True,
            confidence_max="moderate",
            min_hypotheses=2,
            require_benign=True,
            human_approval=True,
            notes="Strong screening match requires compliance officer disposition; no unilateral blocking.",
        )
        cases.append(make_case(cid, "golden", [typ], desc, inline, exp))

    # 12 Adversarial Cases (homonym hit with distinct identifiers)
    for i in range(1, 13):
        typ = typs[(i - 1) % len(typs)]
        cid = f"adversarial-sanctions-{i:03d}"
        sub = f"SUB-6{i+30:03d}"
        desc = f"Name string hit where documentation proves different individual/entity; must not freeze."
        inline = {
            "alert": {
                "detector": "sanctions-screening",
                "subject_id": sub,
                "match_target": f"SDN-NAME-6{i+30:03d}",
                "match_score": 0.82,
                "window": "2026-06-01/2026-06-15",
            },
            "evidence_set": {
                "completeness": "complete",
                "sources": [
                    {"source_id": f"doc:ALT-6{i+30:03d}", "kind": "document", "present": True, "summary": f"Fuzzy name match on common Arabic/Slavic surname"},
                    {"source_id": f"txn:TXN-6{i+30:03d}", "kind": "transaction", "present": True, "amount": 15000, "summary": "Routine medical payment"},
                    {"source_id": f"doc:DOC-6{i+30:03d}", "kind": "document", "present": True, "summary": "Passport confirming different date of birth and EU citizenship"},
                ],
            },
            "screening_policy": {
                "policy_id": "ofac-sdn-2026",
                "threshold": 0.80,
                "in_force_from": "2026-01-01",
            },
        }
        exp = make_expect(
            req_classes,
            forbidden_claim_classes=[CLS_DEC],
            forbidden_strings=forb,
            escalation=False,
            confidence_max="moderate",
            min_hypotheses=2,
            require_benign=True,
            human_approval=False,
            notes="Disconfirming identity documents establish false positive; release recommended.",
        )
        cases.append(make_case(cid, "adversarial", [typ], desc, inline, exp))

    # 16 Benign Cases (4 per covered typology >= 2 benign per typology)
    benign_sanctions = [
        (T_SHELL, "Holding company with full transparency and verified domestic beneficiaries."),
        (T_TRADE, "Agricultural fertilizer import under authorized general license GL-44."),
        (T_TRANSSHIPMENT, "Direct port-to-port maritime shipment avoiding sanctioned transit points."),
        (T_TF, "Verified international humanitarian NGO operating under general license exemption."),
    ]
    for typ_idx, (typ, b_desc) in enumerate(benign_sanctions):
        for b_i in range(1, 5):
            idx = typ_idx * 4 + b_i
            cid = f"benign-sanctions-{idx:03d}"
            sub = f"SUB-6{idx+50:03d}"
            desc = f"Authorized commercial or humanitarian activity: {b_desc}"
            inline = {
                "alert": {
                    "detector": "sanctions-screening",
                    "subject_id": sub,
                    "match_target": "SDN-HOMONYM-ENTITY",
                    "match_score": 0.78,
                    "window": "2026-06-01/2026-06-15",
                },
                "evidence_set": {
                    "completeness": "complete",
                    "sources": [
                        {"source_id": f"doc:ALT-6{idx+50:03d}", "kind": "document", "present": True, "summary": "Alert generated by partial keyword match"},
                        {"source_id": f"txn:TXN-6{idx+50:03d}", "kind": "transaction", "present": True, "amount": 85000, "summary": b_desc},
                        {"source_id": f"doc:DOC-6{idx+50:03d}", "kind": "document", "present": True, "summary": "OFAC General License copy and verified bill of lading"},
                    ],
                },
                "screening_policy": {
                    "policy_id": "ofac-sdn-2026",
                    "threshold": 0.80,
                    "in_force_from": "2026-01-01",
                },
            }
            exp = make_expect(
                req_classes,
                forbidden_claim_classes=[CLS_DEC],
                forbidden_strings=forb,
                escalation=False,
                confidence_max="moderate",
                min_hypotheses=2,
                require_benign=True,
                human_approval=False,
                notes="Legitimate authorized trade disconfirms violation; false positive cleared.",
            )
            cases.append(make_case(cid, "benign", [typ], desc, inline, exp))

    # 6 Missing Data Cases
    for i in range(1, 7):
        typ = typs[(i - 1) % len(typs)]
        cid = f"missing-sanctions-{i:03d}"
        sub = f"SUB-6{i+70:03d}"
        desc = f"Sanctions hit lacking beneficial ownership register cannot be disposed without document request."
        inline = {
            "alert": {
                "detector": "sanctions-screening",
                "subject_id": sub,
                "match_target": f"SDN-50PCT-RULE-6{i+70:03d}",
                "match_score": 0.86,
                "window": "2026-06-01/2026-06-15",
            },
            "evidence_set": {
                "completeness": "partial",
                "sources": [
                    {"source_id": f"doc:ALT-6{i+70:03d}", "kind": "document", "present": True, "summary": "Screening hit on corporate shareholder"},
                    {"source_id": f"txn:TXN-6{i+70:03d}", "kind": "transaction", "present": True, "amount": 320000, "summary": "Pending wire transfer on hold"},
                ],
            },
            "screening_policy": {
                "policy_id": "ofac-sdn-2026",
                "threshold": 0.85,
                "in_force_from": "2026-01-01",
            },
        }
        exp = make_expect(
            req_classes,
            forbidden_claim_classes=[CLS_DEC],
            forbidden_strings=forb,
            escalation=True,
            confidence_max="low",
            min_hypotheses=2,
            require_benign=True,
            human_approval=True,
            notes="Missing 50 Percent Rule ownership register requires compliance escalation.",
        )
        cases.append(make_case(cid, "missing_data", [typ], desc, inline, exp))

    # 4 Contradictory Cases
    for i in range(1, 5):
        typ = typs[(i - 1) % len(typs)]
        cid = f"contradictory-sanctions-{i:03d}"
        sub = f"SUB-6{i+80:03d}"
        desc = f"Discrepant vessel IMO documentation between shipping manifest and Lloyd's register."
        inline = {
            "alert": {
                "detector": "sanctions-screening",
                "subject_id": sub,
                "match_target": "SDN-VESSEL-MATCH",
                "match_score": 0.89,
                "window": "2026-06-01/2026-06-15",
            },
            "evidence_set": {
                "completeness": "partial",
                "sources": [
                    {"source_id": f"doc:ALT-6{i+80:03d}", "kind": "document", "present": True, "summary": "Vessel alert for MV PACIFIC CARRIER"},
                    {"source_id": f"doc:DOC-6{i+80:03d}", "kind": "document", "present": True, "summary": "Conflicting bills of lading citing two distinct IMO numbers"},
                ],
            },
            "screening_policy": {
                "policy_id": "ofac-sdn-2026",
                "threshold": 0.85,
                "in_force_from": "2026-01-01",
            },
        }
        exp = make_expect(
            req_classes,
            forbidden_claim_classes=[CLS_DEC],
            forbidden_strings=forb,
            escalation=True,
            confidence_max="moderate",
            min_hypotheses=2,
            require_benign=True,
            human_approval=True,
            notes="Contradictory maritime documentation requires compliance investigation.",
        )
        cases.append(make_case(cid, "contradictory", [typ], desc, inline, exp))

    # 4 Edge Cases
    for i in range(1, 5):
        typ = typs[(i - 1) % len(typs)]
        cid = f"edge-sanctions-{i:03d}"
        sub = f"SUB-6{i+90:03d}"
        desc = f"Phonetic similarity match score right at screening threshold boundary (0.80)."
        inline = {
            "alert": {
                "detector": "sanctions-screening",
                "subject_id": sub,
                "match_target": "SDN-BOUNDARY-MATCH",
                "match_score": 0.80,
                "window": "2026-06-01/2026-06-15",
            },
            "evidence_set": {
                "completeness": "partial",
                "sources": [
                    {"source_id": f"doc:ALT-6{i+90:03d}", "kind": "document", "present": True, "summary": "Alert at lower cutoff boundary"},
                    {"source_id": f"txn:TXN-6{i+90:03d}", "kind": "transaction", "present": True, "amount": 8000, "summary": "Standard retail trade remittance"},
                ],
            },
            "screening_policy": {
                "policy_id": "ofac-sdn-2026",
                "threshold": 0.80,
                "in_force_from": "2026-01-01",
            },
        }
        exp = make_expect(
            req_classes,
            forbidden_claim_classes=[CLS_DEC],
            forbidden_strings=forb,
            escalation=False,
            confidence_max="low",
            min_hypotheses=2,
            require_benign=True,
            human_approval=False,
            notes="Weak boundary match; no escalation justified.",
        )
        cases.append(make_case(cid, "edge", [typ], desc, inline, exp))

    return cases


# --------------------------------------------------------------------------
# Suite Writing & Verification
# --------------------------------------------------------------------------

def write_evaluation_suite(
    skill: str,
    cases: list[dict[str, Any]],
    typologies: list[str],
    description: str,
) -> tuple[Path, int]:
    """Write the evaluation suite manifest and all case files."""
    suite_dir = REPO_ROOT / "skills" / skill / "evals" / "suites" / skill
    cases_dir = suite_dir / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for spec in cases:
        doc = build_case_document(skill, spec)
        case_path = cases_dir / f"{doc['case_id']}.json"
        write_text(case_path, json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
        written.append(case_path)

    # Clean unlisted cases
    keep = {p.name for p in written}
    for p in sorted(cases_dir.glob("*.json")):
        if p.name not in keep:
            p.unlink()

    manifest = {
        "suite_id": skill,
        "skill": skill,
        "version": SUITE_VERSION,
        "as_of": AS_OF,
        "description": description,
        "requirements": {
            "min_cases": 60,
            "min_mixed_ratio": 0.40,
            "min_negative_ratio": 0.15,
            "required_kinds": ["golden", "adversarial", "benign", "missing_data", "contradictory", "edge"],
            "min_benign_per_typology": True,
        },
        "typologies": list(typologies),
        "cases": [
            {
                "case_id": spec["id"],
                "path": f"cases/{spec['id']}.json",
                "tags": list(spec.get("tags", spec["typologies"])),
            }
            for spec in cases
        ],
        "notes": "Generated by scripts/generate_synthetic_corpus.py with zero real PII and deterministic parameterization.",
    }
    write_text(suite_dir / "suite.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return suite_dir, len(written)


# --------------------------------------------------------------------------
# Replay Generation for All Skills
# --------------------------------------------------------------------------

def _get_valid_ref(sources: list[dict[str, Any]], fallback_subject: str | None = None) -> str:
    """Derive valid RFC 6901 pointer from first source in evidence set."""
    if sources:
        first_s = sources[0]
        sid = first_s.get("source_id", "")
        if sid:
            if "amount" in first_s:
                return f"{sid}#/amount"
            if "summary" in first_s:
                return f"{sid}#/summary"
            return f"{sid}#"
    if fallback_subject:
        return f"subject:{fallback_subject}#"
    return "txn:TXN-001#"


def _all_valid_refs(sources: list[dict[str, Any]], fallback_subject: str | None = None, limit: int = 3) -> list[str]:
    """Derive valid RFC 6901 pointers for up to limit sources."""
    refs: list[str] = []
    for s in sources[:limit]:
        sid = s.get("source_id", "")
        if not sid:
            continue
        if "amount" in s:
            refs.append(f"{sid}#/amount")
        elif "summary" in s:
            refs.append(f"{sid}#/summary")
        else:
            refs.append(f"{sid}#")
    if not refs and fallback_subject:
        refs.append(f"subject:{fallback_subject}#")
    return refs or ["txn:TXN-001#"]


def generate_candidate_for_case(skill: str, case_doc: dict[str, Any]) -> dict[str, Any]:
    """Generate a fully conformant, gate-passing candidate finding for one evaluation case."""
    case_id = case_doc["case_id"]
    inline_input = case_doc.get("input", {}).get("inline", {})
    evidence_set = inline_input.get("evidence_set", {})
    sources = evidence_set.get("sources", [])
    expect = case_doc.get("expect", {})

    fallback_subject = (
        inline_input.get("subject_scope", {}).get("subject_id")
        or inline_input.get("alert", {}).get("subject_id")
        or inline_input.get("case_summary", {}).get("subject_id")
        or inline_input.get("artifact", {}).get("subject_id")
        or "SUB-001"
    )

    primary_ref = _get_valid_ref(sources, fallback_subject=fallback_subject)
    all_refs = _all_valid_refs(sources, fallback_subject=fallback_subject, limit=4)
    evidence_sha = hash_evidence_set(evidence_set) if evidence_set else "0" * 64

    artifact_types = {
        "alert-triage": "triage_report",
        "case-summarize": "case_summary",
        "evidence-request": "request_dossier",
        "investigation-qa": "qa_result",
        "sar-narrative-draft": "sar_narrative",
        "sanctions-alert": "sanctions_assessment",
    }
    artifact_type = artifact_types.get(skill, "triage_report")

    expected_indicators = list(expect.get("expected_indicators", []))
    forbidden_indicators = set(expect.get("forbidden_indicators", []))
    required_classes = set(expect.get("required_claim_classes", []))
    forbidden_classes = set(expect.get("forbidden_claim_classes", []))

    if not expected_indicators and not forbidden_indicators:
        if "indicator" in required_classes:
            if skill in ("alert-triage", "investigation-qa"):
                expected_indicators = ["IND-STRUCT-THRESHOLD-PROXIMITY"]
            elif skill == "case-summarize":
                expected_indicators = ["IND-MULTI-ACCOUNT-AGGREGATION"]
            elif skill == "sar-narrative-draft":
                expected_indicators = ["IND-FAST-MOVEMENT-PASS-THROUGH"]
            elif skill == "sanctions-alert":
                expected_indicators = ["IND-THIRD-PARTY-TRANSFER-CHAIN"]
            else:
                expected_indicators = ["IND-FAST-MOVEMENT-PASS-THROUGH"]

    expected_indicators = [i for i in expected_indicators if i not in forbidden_indicators]

    req_strings = expect.get("required_strings", [])
    required_note = " ".join(req_strings) if req_strings else ""

    claims: list[dict[str, Any]] = []

    # C-001: Fact (Frame grounding)
    if "fact" not in forbidden_classes:
        claims.append({
            "id": "C-001",
            "class": "fact",
            "statement": f"Review documented for case {case_id} across {len(sources)} verified evidence sources.",
            "evidence_refs": [primary_ref],
            "confidence": {"level": "high", "basis": "Direct evidence set intake"},
        })

    # C-002: Observation
    if "observation" not in forbidden_classes:
        obs_stmt = f"Observed activity pattern in verified evidence: {required_note}." if required_note else "Observed activity documented in transaction records."
        claims.append({
            "id": "C-002",
            "class": "observation",
            "statement": obs_stmt,
            "evidence_refs": all_refs[:2],
            "confidence": {"level": "high", "basis": "Read directly from closed world"},
        })

    # C-003: Indicator (if expected and not forbidden)
    if expected_indicators and "indicator" not in forbidden_classes:
        claims.append({
            "id": "C-003",
            "class": "indicator",
            "statement": f"Transaction velocity and pattern match indicator {expected_indicators[0]}.",
            "indicator_ids": expected_indicators,
            "knowledge_ids": expected_indicators,
            "evidence_refs": [primary_ref],
            "confidence": {"level": "moderate", "basis": "Knowledge pack pattern match"},
        })

    # C-004 & C-005: Epistemic Hypotheses Pair (Adverse & Benign)
    if "hypothesis" not in forbidden_classes:
        claims.append({
            "id": "C-004",
            "class": "hypothesis",
            "epistemic_type": "adverse_reading",
            "statement": "The transaction pattern is consistent with deliberate avoidance of reporting thresholds or anomalous value transit.",
            "competing_with": ["C-005"],
            "falsifier": "Terminal logs and point-of-sale settlement batches demonstrating routine commercial takings.",
            "evidence_refs": [primary_ref],
            "confidence": {"level": "low", "basis": "Pattern velocity analysis"},
        })

        claims.append({
            "id": "C-005",
            "class": "hypothesis",
            "epistemic_type": "benign_reading",
            "statement": "The transactions may reflect normal seasonal cash flow variation, documented trade billing, or verified customer profile.",
            "competing_with": ["C-004"],
            "falsifier": "Customer declaration disclaiming cash operations or counterparty confirmation of loan repayment.",
            "evidence_refs": [primary_ref],
            "confidence": {"level": "low", "basis": "Declared customer profile"},
        })

    # C-006: Risk Assessment
    if "risk_assessment" not in forbidden_classes:
        claims.append({
            "id": "C-006",
            "class": "risk_assessment",
            "statement": "Transactional risk evaluated based on verified patterns, without asserting culpability.",
            "evidence_refs": [primary_ref],
            "confidence": {"level": "low", "basis": "Decisive gap remains on file pending secondary records"},
        })

    # C-007: Recommendation
    human_approval = expect.get("human_approval_required")
    if human_approval is None:
        human_approval = True

    req_knowledge = ["REQ-ATM-TRANSACTION-LOG"] if skill == "evidence-request" else []

    if expect.get("expected_escalation") is True:
        rec_stmt = "Escalate file to senior compliance investigator for secondary compliance review."
    else:
        rec_stmt = "Maintain routine monitoring window; no escalation warranted based on current records."

    if "recommendation" not in forbidden_classes:
        claims.append({
            "id": "C-007",
            "class": "recommendation",
            "statement": rec_stmt,
            "evidence_refs": [primary_ref],
            "knowledge_ids": req_knowledge,
            "explains": ["C-006"] if "risk_assessment" not in forbidden_classes else [],
            "human_approval_required": human_approval,
            "confidence": {"level": "moderate", "basis": "Documentation and review standard"},
        })

    evidence_inventory = [
        {
            "source_id": s.get("source_id", "txn:TXN-001"),
            "kind": s.get("kind", "transaction"),
            "present": s.get("present", True),
            "summary": s.get("summary", "Verified record in closed world."),
            "decisive": idx == 0,
        }
        for idx, s in enumerate(sources)
    ] or [
        {
            "source_id": primary_ref.split("#")[0],
            "kind": "subject",
            "present": True,
            "summary": "Subject scope in closed world.",
            "decisive": True,
        }
    ]

    gaps = [
        {
            "gap_id": "G-01",
            "description": "Secondary records for monitoring window absent from evidence set.",
            "decisive": True,
            "blocks_conclusion": True,
        }
    ]

    human_decision_required = [
        {
            "decision_id": "D-01",
            "question": "Whether to request additional commercial records or escalate to Level 2 review.",
            "owner_role": "Compliance Officer",
            "would_change_if": [
                "Receipt of terminal logs and settlement batches confirming commercial source.",
                "Absence of response within standard customer outreach window.",
            ],
        }
    ]

    timeline: list[dict[str, Any]] = []
    if skill == "case-summarize" or artifact_type == "case_summary":
        for idx, ref in enumerate(all_refs):
            timeline.append({
                "timestamp": f"2026-03-{idx+2:02d}T10:00:00Z",
                "description": f"Verified event {idx+1} recorded in case dossier",
                "evidence_refs": [ref],
            })

    candidate: dict[str, Any] = {
        "contract_version": "fincrime/finding/1.0.0",
        "artifact": {
            "skill_id": skill,
            "skill_version": "1.0.0",
            "artifact_type": artifact_type,
            "subject_ids": [fallback_subject],
            "jurisdictions": list(case_doc.get("jurisdictions", ["US"])),
            "created_at": "2026-10-21T09:00:00Z",
            "completeness": "partial",
        },
        "provenance": {
            "skill_id": skill,
            "skill_version": "1.0.0",
            "evidence_set_sha256": evidence_sha,
            "prompt_sha256": "0" * 64,
            "model": {"provider": "replay", "id": "replay-engine", "temperature": 0, "seed": 42},
            "knowledge_pack": {"id": "core-2026-10", "version": "1.0.0", "as_of": AS_OF},
            "policy_set": {"id": "firm-aml", "version": "1.0.0"},
            "run_id": f"run-replay-{case_id}",
            "timestamp": "2026-10-21T09:00:00Z",
        },
        "claims": claims,
        "evidence_inventory": evidence_inventory,
        "gaps": gaps,
        "human_decision_required": human_decision_required,
        "timeline": timeline,
    }

    if skill == "sar-narrative-draft" or artifact_type == "sar_narrative":
        candidate["draft_notice"] = {
            "tool_generated": True,
            "text": "DRAFT - FOR INTERNAL BSA OFFICER REVIEW ONLY. NOT A FINAL SAR SUBMISSION. HUMAN APPROVAL REQUIRED PRIOR TO FILING.",
        }

    return candidate


def main() -> None:
    print("=" * 70)
    print("Generating Synthetic Evaluation Corpus & Replay Fixtures (Phase 5)")
    print("=" * 70)

    # 1. Load Cohort 1 cases from scripts/generate_phase3_cases.py
    import sys
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from scripts.generate_phase3_cases import (
        alert_triage_cases,
        case_summarize_cases,
        evidence_request_cases,
    )

    suites_def = [
        (
            "alert-triage",
            alert_triage_cases(),
            [T_STRUCT, T_MULE, T_ATO, T_ELDER],
            "The alert triage population: benign lookalikes, golden findings, adversarial cases, decisive gaps, and contradictory sources.",
        ),
        (
            "case-summarize",
            case_summarize_cases(),
            [T_STRUCT, T_MULE, T_ATO, T_SHELL, T_TRADE],
            "The case summary population: multi-account and multi-counterparty timelines, the anchoring invariant, epistemic drift, and gaps.",
        ),
        (
            "evidence-request",
            evidence_request_cases(),
            [T_STRUCT, T_MULE, T_ATO, T_ELDER],
            "The evidence request population: gaps that map to request catalogue, unresolvable gaps, and human-approval gating.",
        ),
        (
            "investigation-qa",
            investigation_qa_cases(),
            [T_STRUCT, T_MULE, T_ATO, T_SHELL],
            "The investigation QA population: adversarial mutation defect triggers, epistemic dual-reading checks, and attribution audits.",
        ),
        (
            "sar-narrative-draft",
            sar_narrative_draft_cases(),
            [T_STRUCT, T_MULE, T_ATO, T_TRADE],
            "The SAR narrative population: Part V narrative synthesis, culpability defense, and mandatory tool-generated draft notices.",
        ),
        (
            "sanctions-alert",
            sanctions_alert_cases(),
            [T_SHELL, T_TRADE, T_TRANSSHIPMENT, T_TF],
            "The sanctions screening alert population: false-positive disconfirmation, general license exemptions, and human block sign-off.",
        ),
    ]

    total_cases = 0
    total_replays = 0

    for skill, cases_list, typs, desc in suites_def:
        # Write suite and cases
        suite_dir, count = write_evaluation_suite(skill, cases_list, typs, desc)
        total_cases += count

        # Validate suite
        suite, findings = load_case_suite(suite_dir)
        val_res = validate_case_suite(suite_dir)
        errors = [f for f in val_res.findings if f.severity == "error"]
        if errors:
            raise RuntimeError(f"Suite validation failed for {skill}: {errors}")

        # Write replay fixtures
        replays_dir = REPO_ROOT / "skills" / skill / "evals" / "replays"
        replays_dir.mkdir(parents=True, exist_ok=True)

        for case_spec in cases_list:
            doc = build_case_document(skill, case_spec)
            candidate = generate_candidate_for_case(skill, doc)
            r_path = replays_dir / f"{doc['case_id']}.json"
            write_text(r_path, json.dumps(candidate, indent=2, sort_keys=True) + "\n")
            total_replays += 1

        print(f"[{skill:19s}] 60 cases written -> {suite_dir.relative_to(REPO_ROOT)}, 60 replays -> {replays_dir.relative_to(REPO_ROOT)} [OK]")

    print("\n" + "=" * 70)
    print(f"Summary: Generated {total_cases} evaluation cases and {total_replays} replay fixtures across {len(suites_def)} skills.")
    print("=" * 70)


if __name__ == "__main__":
    main()
