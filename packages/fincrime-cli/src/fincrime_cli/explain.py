"""fincrime explain: educational diagnostics and regulatory rationale.

Explains validation rules, defect codes, policy controls, and artifact failures.
Provides FinCEN / BSA / FFIEC regulatory context, RFC 6901 pointer details,
and concrete remediation diffs.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Sequence

from fincrime_core.paths import repo_root
from fincrime_core.policy.evaluator import PolicyEvaluator
from fincrime_core.policy.set import load_policy_set
from fincrime_core.validate.defects import DEFECT_CODES, load_defect_taxonomy
from fincrime_core.validate.validator import EnforcementContext, Validator

__all__ = [
    "cmd_explain",
    "explain_identifier",
    "explain_artifact_path",
    "RuleExplanation",
    "ArtifactExplanation",
]

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2

DEFAULT_POLICY_SET_REL = Path("policies") / "default" / "policy-set.json"


@dataclass(frozen=True, slots=True)
class RuleExplanation:
    """Educational breakdown of a Finding Contract rule or defect code."""

    rule_id: str
    name: str
    defect_code: str
    severity: str
    enforcement: str
    regulatory_rationale: str
    pointer_target: str
    failing_example: str
    passing_example: str
    remediation: str
    policy_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# Comprehensive regulatory rule catalog
RULE_CATALOG: dict[str, RuleExplanation] = {
    "R-1": RuleExplanation(
        rule_id="R-1",
        name="Mandatory Evidence Anchoring",
        defect_code="unsupported_claim",
        severity="error",
        enforcement="structural",
        regulatory_rationale=(
            "FinCEN Suspicious Activity Report (SAR) Regulations (31 CFR § 1020.320 / 31 U.S.C. § 5318(g)) "
            "and FFIEC BSA/AML Examination Manual. Factual assertions regarding customer activity must be "
            "anchored directly to transactional or documentary records. Asserting transactions or events without "
            "verifiable evidence constitutes unsubstantiated speculation, violates exam standards, and fails auditability."
        ),
        pointer_target="$.claims[i].evidence_refs",
        failing_example='{\n  "id": "C-001",\n  "class": "fact",\n  "statement": "Subject deposited $9,500.",\n  "evidence_refs": []\n}',
        passing_example='{\n  "id": "C-001",\n  "class": "fact",\n  "statement": "Subject deposited $9,500.",\n  "evidence_refs": ["txn:8841#/amount"]\n}',
        remediation=(
            "Supply at least one valid RFC 6901 pointer in 'evidence_refs' referencing the exact field "
            "in the evidence set (e.g., 'txn:8841#/amount')."
        ),
    ),
    "R-1a": RuleExplanation(
        rule_id="R-1a",
        name="Evidence Reference Resolution (Zero Hallucination)",
        defect_code="unsupported_claim",
        severity="error",
        enforcement="structural",
        regulatory_rationale=(
            "Federal Reserve SR 11-7 / OCC 2011-12 (Supervisory Guidance on Model Risk Management). "
            "Citations to non-existent data, phantom accounts, or fabricated transactions represent critical "
            "model hallucinations. Every cited pointer on every claim class must deterministically resolve "
            "against the closed-world evidence set."
        ),
        pointer_target="$.claims[i].evidence_refs[j]",
        failing_example='{\n  "evidence_refs": ["txn:unverified_wire_999#/amount"]\n}  // Pointer fails: source not in evidence set',
        passing_example='{\n  "evidence_refs": ["txn:8841#/amount"]\n}  // Resolves to 9400 in evidence set',
        remediation=(
            "Verify that the source ID (e.g. 'txn:8841') and JSON Pointer fragment (e.g. '#/amount') "
            "exist in the provided evidence set."
        ),
    ),
    "R-1b": RuleExplanation(
        rule_id="R-1b",
        name="Timeline Evidence Reference Resolution",
        defect_code="unsupported_claim",
        severity="error",
        enforcement="structural",
        regulatory_rationale=(
            "FinCEN SAR Narrative Chronology Guidance. Chronological event sequencing in an investigation "
            "must reflect verifiable timestamps and transaction references. Unanchored timeline entries "
            "introduce fabricated events into the audit trail."
        ),
        pointer_target="$.timeline[i].evidence_refs[j]",
        failing_example='{\n  "timestamp": "2026-03-04T10:12:00Z",\n  "evidence_refs": ["txn:ghost_id#/ts"]\n}',
        passing_example='{\n  "timestamp": "2026-03-04T10:12:00Z",\n  "evidence_refs": ["txn:8841#/ts"]\n}',
        remediation=(
            "Ensure every reference in timeline entries resolves to an indexed transaction or alert record."
        ),
    ),
    "R-2": RuleExplanation(
        rule_id="R-2",
        name="Indicator Identification & Knowledge Grounding",
        defect_code="unknown_indicator",
        severity="error",
        enforcement="structural",
        regulatory_rationale=(
            "FinCEN Advisory FIN-2019-A003 & FATF Guidance on Red Flags. Automated monitoring systems must "
            "map suspicious patterns to standardized, cataloged red-flag indicators rather than ad-hoc prose "
            "or unregistered codes."
        ),
        pointer_target="$.claims[i].indicator_ids",
        policy_id="POL-INDICATOR-REQUIRES-INDICATOR-ID",
        failing_example='{\n  "class": "indicator",\n  "indicator_ids": ["CUSTOM-FLAG-UNKNOWN"]\n}',
        passing_example='{\n  "class": "indicator",\n  "indicator_ids": ["IND-STRUCT-THRESHOLD-PROXIMITY"]\n}',
        remediation=(
            "Use registered indicator IDs from the declared knowledge pack (e.g., 'core-2026-10') or submit "
            "new indicators via the pack promotion process."
        ),
    ),
    "R-2b": RuleExplanation(
        rule_id="R-2b",
        name="Knowledge Record Grounding",
        defect_code="unsupported_claim",
        severity="error",
        enforcement="structural",
        regulatory_rationale=(
            "Model Risk Management SR 11-7 (External Data Integrity). Citations to external knowledge or "
            "typologies must reference verified, version-controlled records in the compliance knowledge pack."
        ),
        pointer_target="$.claims[i].knowledge_ids",
        failing_example='{\n  "knowledge_ids": ["TYP-OBSOLETE-RECORD-001"]\n}',
        passing_example='{\n  "knowledge_ids": ["TYP-STRUCTURING-SMURFING"]\n}',
        remediation="Anchor to an active record ID present in the declared knowledge pack.",
    ),
    "R-3": RuleExplanation(
        rule_id="R-3",
        name="Hypothesis Falsifier Requirement",
        defect_code="misclassified_claim",
        severity="error",
        enforcement="structural",
        regulatory_rationale=(
            "OCC Bulletin 2011-12 & Scientific Method in Financial Crime Investigation. Conceptual soundness "
            "demands that an investigative hypothesis specify concrete evidence that would disprove it. "
            "Unfalsifiable allegations cannot be audited or scientifically defended."
        ),
        pointer_target="$.claims[i].falsifier",
        failing_example='{\n  "class": "hypothesis",\n  "statement": "Subject is deliberately structuring deposits.",\n  "falsifier": null\n}',
        passing_example='{\n  "class": "hypothesis",\n  "statement": "Subject is deliberately structuring deposits.",\n  "falsifier": "Point-of-sale customer receipts showing daily cash takings naturally varying under $10,000."\n}',
        remediation="Define a clear documentary condition in 'falsifier' that would disprove the hypothesis.",
    ),
    "R-3a": RuleExplanation(
        rule_id="R-3a",
        name="Hypothesis Epistemic Categorization",
        defect_code="misclassified_claim",
        severity="error",
        enforcement="structural",
        regulatory_rationale=(
            "Explainable AI Standards in AML Triage. Investigators and regulators must clearly distinguish "
            "between adverse theories, benign explanations, and data gaps. Ambiguous assertions degrade auditability."
        ),
        pointer_target="$.claims[i].epistemic_type",
        failing_example='{\n  "class": "hypothesis",\n  "epistemic_type": null\n}',
        passing_example='{\n  "class": "hypothesis",\n  "epistemic_type": "adverse_reading"\n}',
        remediation="Set 'epistemic_type' to one of: 'benign_reading', 'adverse_reading', 'data_gap', 'other'.",
    ),
    "R-3b": RuleExplanation(
        rule_id="R-3b",
        name="Epistemic Dual-Reading Requirement (Benign Twin Competition)",
        defect_code="missing_benign_reading",
        severity="error",
        enforcement="structural",
        regulatory_rationale=(
            "FinCEN Guidance on Defensive SAR Filings and De-Risking / FFIEC Exam Manual. An adverse reading "
            "may not stand alone. In financial crime triage, an investigator must evaluate competing benign explanations "
            "(e.g., commercial business cash takings) before taking adverse action. Single-sided adverse assumptions "
            "generate false-positive rates >= 50% and drive discriminatory de-risking."
        ),
        pointer_target="$.claims[?(@.epistemic_type=='adverse_reading')]",
        policy_id="POL-BENIGN-HYPOTHESIS-REQUIRED",
        failing_example='[\n  {\n    "id": "H-01",\n    "class": "hypothesis",\n    "epistemic_type": "adverse_reading",\n    "statement": "Structuring to evade reporting."\n  }\n] // Error: No benign reading present',
        passing_example='[\n  {\n    "id": "H-01",\n    "class": "hypothesis",\n    "epistemic_type": "adverse_reading",\n    "statement": "Structuring to evade reporting.",\n    "competing_with": ["H-02"]\n  },\n  {\n    "id": "H-02",\n    "class": "hypothesis",\n    "epistemic_type": "benign_reading",\n    "statement": "Normal logistics depot weekend cash collections.",\n    "competing_with": ["H-01"]\n  }\n]',
        remediation=(
            "1. Formulate a competing hypothesis with epistemic_type 'benign_reading' (e.g. legitimate commercial takings).\n"
            "2. Establish a falsifier for both hypotheses.\n"
            "3. Link the two hypotheses using the 'competing_with' field."
        ),
    ),
    "R-3d": RuleExplanation(
        rule_id="R-3d",
        name="Confidence Bound on Decisive Evidence Gaps",
        defect_code="overstated_confidence",
        severity="error",
        enforcement="structural",
        regulatory_rationale=(
            "FFIEC BSA/AML Examination Standards for Investigative Quality. When decisive evidence required "
            "to substantiate illicit conduct is recorded as absent, an adverse conclusion cannot be asserted "
            "with high confidence."
        ),
        pointer_target="$.claims[i].confidence.level",
        failing_example='{\n  "class": "hypothesis",\n  "epistemic_type": "adverse_reading",\n  "confidence": {"level": "high"} // Artifact records decisive gaps\n}',
        passing_example='{\n  "class": "hypothesis",\n  "epistemic_type": "adverse_reading",\n  "confidence": {"level": "moderate"}\n}',
        remediation="Lower confidence level to 'moderate', 'low', or 'insufficient_information' until the decisive gap is closed.",
    ),
    "R-4": RuleExplanation(
        rule_id="R-4",
        name="Risk Assessment Grounding & Insufficient Info Boundary",
        defect_code="misclassified_claim",
        severity="error",
        enforcement="structural",
        regulatory_rationale=(
            "FFIEC Customer Risk Rating Standards. A risk assessment must either cite verifiable evidence "
            "or explicitly state that available information is insufficient. Unanchored numerical or categorical "
            "risk scores fail supervisory audits."
        ),
        pointer_target="$.claims[i].confidence.level",
        policy_id="POL-ASSESSMENT-NEEDS-INDICATOR",
        failing_example='{\n  "class": "risk_assessment",\n  "evidence_refs": [],\n  "confidence": {"level": "high"}\n}',
        passing_example='{\n  "class": "risk_assessment",\n  "evidence_refs": [],\n  "confidence": {"level": "insufficient_information"}\n}',
        remediation="Provide evidence references anchoring the risk assessment, or set confidence level to 'insufficient_information'.",
    ),
    "R-5": RuleExplanation(
        rule_id="R-5",
        name="Decision Provenance & Human Attribution",
        defect_code="provenance_gap",
        severity="error",
        enforcement="structural",
        regulatory_rationale=(
            "Federal Reserve SR 11-7 / OCC Model Governance. Autonomous AI models may not make final legal "
            "or regulatory determinations to close cases or file SARs. A decision claim must name the authorized "
            "human investigator or approved deterministic policy."
        ),
        pointer_target="$.claims[i].decided_by",
        failing_example='{\n  "class": "decision",\n  "statement": "Escalate for SAR filing.",\n  "decided_by": null\n}',
        passing_example='{\n  "class": "decision",\n  "statement": "Escalate for SAR filing.",\n  "decided_by": "compliance_officer:1042"\n}',
        remediation="Attribute the decision claim by setting 'decided_by' to an authorized human officer ID or approved policy ID.",
    ),
    "R-6": RuleExplanation(
        rule_id="R-6",
        name="Culpability Assertion Prevention (Regulatory Safe Harbor)",
        defect_code="unsupported_claim",
        severity="warn",
        enforcement="heuristic",
        regulatory_rationale=(
            "FinCEN SAR Filing Instructions & 31 U.S.C. § 5318(g) Safe Harbor Protection. SAR narratives report "
            "factual patterns, suspicious timing, and context. Filers must NEVER assert that a subject 'is guilty' "
            "or 'is a money launderer'. Accusatory assertions expose the institution to defamation liability and "
            "contravene FinCEN guidance."
        ),
        pointer_target="$.claims[i].statement",
        policy_id="POL-NO-CRIMINALITY-CLAIMS",
        failing_example='{\n  "statement": "The subject is a money launderer guilty of structuring cash."\n}',
        passing_example='{\n  "statement": "The subject executed cash deposits with amounts and frequencies consistent with cash structuring typologies."\n}',
        remediation="Replace accusatory phrases with objective descriptions of observed conduct and indicator alignment.",
    ),
    "R-7": RuleExplanation(
        rule_id="R-7",
        name="Consequential Escalation & Human Approval",
        defect_code="escalation_missed",
        severity="error",
        enforcement="structural",
        regulatory_rationale=(
            "SR 11-7 / OCC Human-in-the-Loop AI Governance. Recommendations that impact customer accounts, "
            "restrict services, or trigger regulatory disclosures must preserve human sign-off. AI agents "
            "cannot waive human approval."
        ),
        pointer_target="$.claims[i].human_approval_required",
        policy_id="POL-RECOMMENDATION-NEEDS-APPROVAL",
        failing_example='{\n  "class": "recommendation",\n  "statement": "Freeze accounts immediately.",\n  "human_approval_required": false\n}',
        passing_example='{\n  "class": "recommendation",\n  "statement": "Freeze accounts immediately.",\n  "human_approval_required": true\n}',
        remediation="Set 'human_approval_required': true on consequential recommendations.",
    ),
    "R-8": RuleExplanation(
        rule_id="R-8",
        name="Confidence Ceiling on Partial Evidence Windows",
        defect_code="overstated_confidence",
        severity="error",
        enforcement="structural",
        regulatory_rationale=(
            "FFIEC Examination Standards for Scope and Completeness. When an investigation window is partial "
            "or truncated, inferential conclusions (hypotheses, risk assessments, recommendations) cannot be "
            "stated with high confidence."
        ),
        pointer_target="$.claims[i].confidence.level",
        policy_id="POL-CONFIDENCE-CEILING-ON-PARTIAL-EVIDENCE",
        failing_example='{\n  "artifact": {"completeness": "partial"},\n  "confidence": {"level": "high"} // High confidence against partial data\n}',
        passing_example='{\n  "artifact": {"completeness": "partial"},\n  "confidence": {"level": "moderate"}\n}',
        remediation="Cap the confidence level to 'moderate' or 'low', or request complete records.",
    ),
    "R-9": RuleExplanation(
        rule_id="R-9",
        name="Competing Hypothesis Link Integrity",
        defect_code="provenance_gap",
        severity="error",
        enforcement="structural",
        regulatory_rationale=(
            "Audit Trail & Epistemic Graph Integrity. Competing hypothesis links must point to existing, "
            "valid hypothesis claims within the same artifact."
        ),
        pointer_target="$.claims[i].competing_with",
        failing_example='{\n  "competing_with": ["missing_claim_999"]\n}',
        passing_example='{\n  "competing_with": ["C-004"]\n}',
        remediation="Ensure every ID in 'competing_with' exists in claims and is of class 'hypothesis'.",
    ),
    "R-10": RuleExplanation(
        rule_id="R-10",
        name="Recommendation Basis Requirement",
        defect_code="recommendation_without_basis",
        severity="error",
        enforcement="structural",
        regulatory_rationale=(
            "FinCEN Case Adjudication Standards. Corrective actions and customer recommendations must have "
            "clear justification, grounded in verified evidence or motivating investigative claims."
        ),
        pointer_target="$.claims[i].explains",
        policy_id="POL-RECOMMENDATION-NEEDS-BASIS",
        failing_example='{\n  "class": "recommendation",\n  "evidence_refs": [],\n  "explains": []\n}',
        passing_example='{\n  "class": "recommendation",\n  "explains": ["C-003", "C-004"]\n}',
        remediation="Anchor the recommendation to evidence references or link motivating claim IDs in 'explains'.",
    ),
    "R-11": RuleExplanation(
        rule_id="R-11",
        name="Decisive Gap Unacknowledged in Risk Assessment",
        defect_code="decisive_gap_unacknowledged",
        severity="error",
        enforcement="structural",
        regulatory_rationale=(
            "BSA/AML Examination Standards. An investigator cannot grade risk as high or moderate when an "
            "acknowledged decisive information gap blocks conclusion."
        ),
        pointer_target="$.claims[i].confidence.level",
        failing_example='{\n  "class": "risk_assessment",\n  "confidence": {"level": "high"} // Decisive blocking gap on record\n}',
        passing_example='{\n  "class": "risk_assessment",\n  "confidence": {"level": "insufficient_information"}\n}',
        remediation="State assessment as 'low' or 'insufficient_information', or resolve the decisive evidence gap.",
    ),
    "R-12": RuleExplanation(
        rule_id="R-12",
        name="Claim Jurisdiction Scope",
        defect_code="jurisdiction_overreach",
        severity="error",
        enforcement="structural",
        regulatory_rationale=(
            "Jurisdictional Competence & Cross-Border Compliance. A claim cannot assert legal standards or "
            "statutes for jurisdictions outside those declared by the artifact."
        ),
        pointer_target="$.claims[i].jurisdictions",
        failing_example='{\n  "artifact": {"jurisdictions": ["US"]},\n  "claim": {"jurisdictions": ["EU", "US"]}\n}',
        passing_example='{\n  "artifact": {"jurisdictions": ["US"]},\n  "claim": {"jurisdictions": ["US"]}\n}',
        remediation="Scope claim jurisdictions to match the artifact's declared jurisdictions.",
    ),
    "R-12a": RuleExplanation(
        rule_id="R-12a",
        name="Artifact Jurisdiction Scope",
        defect_code="jurisdiction_overreach",
        severity="error",
        enforcement="structural",
        regulatory_rationale=(
            "Skill Certification Boundary. An artifact cannot declare jurisdictions beyond the skill's certified scope."
        ),
        pointer_target="$.artifact.jurisdictions",
        failing_example='artifact declares ["UK", "EU"] when skill manifest specifies ["US"]',
        passing_example='artifact declares ["US"]',
        remediation="Align artifact declared jurisdictions with skill manifest jurisdiction scope.",
    ),
    "R-13": RuleExplanation(
        rule_id="R-13",
        name="Conflicting Draft Notice (Premature Filing Assertion)",
        defect_code="conflicting_draft_notice",
        severity="warn",
        enforcement="heuristic",
        regulatory_rationale=(
            "FinCEN Electronic Filing Specifications & Safe Harbor Protection. AI-authored narratives must not "
            "assert that a SAR has already been filed or transmitted to FinCEN when only an automated draft was generated."
        ),
        pointer_target="$.claims[i].statement",
        failing_example='{\n  "statement": "We have submitted this Suspicious Activity Report to FinCEN."\n}',
        passing_example='{\n  "statement": "Draft SAR narrative prepared for compliance officer filing determination."\n}',
        remediation="Remove assertions of completed filing; the tool-generated draft notice is authoritative.",
    ),
    "ART-1": RuleExplanation(
        rule_id="ART-1",
        name="Human Escalation Boundary (Reserved Decision)",
        defect_code="escalation_missed",
        severity="error",
        enforcement="structural",
        regulatory_rationale=(
            "FFIEC & Federal Reserve Human Governance Mandate. AI systems cannot be the sole decider of case disposition. "
            "Every valid finding artifact must explicitly name at least one pending decision reserved for a human compliance officer."
        ),
        pointer_target="$.human_decision_required",
        failing_example='{\n  "human_decision_required": []\n}',
        passing_example='{\n  "human_decision_required": ["Senior AML Investigator must review depot receipts and authorize SAR escalation or case closure."]\n}',
        remediation="Populate 'human_decision_required' with the pending human compliance decisions.",
    ),
    "R-NOTICE-1": RuleExplanation(
        rule_id="R-NOTICE-1",
        name="Tool-Generated Safety Notice",
        defect_code="missing_draft_notice",
        severity="error",
        enforcement="structural",
        regulatory_rationale=(
            "ADR-0009 Tool-Generated Safety Notices. Regulatory draft narratives (SAR Part V) must carry a non-strippable "
            "tool-generated safety notice certifying draft status."
        ),
        pointer_target="$.draft_notice",
        failing_example='{\n  "draft_notice": null\n}',
        passing_example='{\n  "draft_notice": {"tool_generated": true, "text": "DRAFT - NOT FOR SUBMISSION WITHOUT HUMAN APPROVAL"}\n}',
        remediation="Render narrative through the certified renderer with 'tool_generated: true'.",
    ),
}

# Policy aliases
POLICY_TO_RULE: dict[str, str] = {
    "POL-INDICATOR-REQUIRES-INDICATOR-ID": "R-2",
    "POL-BENIGN-HYPOTHESIS-REQUIRED": "R-3b",
    "POL-ASSESSMENT-NEEDS-INDICATOR": "R-4",
    "POL-RECOMMENDATION-NEEDS-BASIS": "R-10",
    "POL-NO-CRIMINALITY-CLAIMS": "R-6",
    "POL-CONFIDENCE-CEILING-ON-PARTIAL-EVIDENCE": "R-8",
    "POL-RECOMMENDATION-NEEDS-APPROVAL": "R-7",
    "POL-EVIDENCE-INVENTORY-FIRST": "R-1",
}

# Defect code aliases
DEFECT_TO_RULE: dict[str, str] = {
    "unsupported_claim": "R-1",
    "misclassified_claim": "R-3",
    "missing_benign_reading": "R-3b",
    "missing_gap": "R-3d",
    "overstated_confidence": "R-8",
    "contradiction_ignored": "R-9",
    "recommendation_without_basis": "R-10",
    "provenance_gap": "R-5",
    "escalation_missed": "ART-1",
    "jurisdiction_overreach": "R-12",
    "missing_draft_notice": "R-NOTICE-1",
    "conflicting_draft_notice": "R-13",
    "unknown_indicator": "R-2",
    "expired_knowledge_citation": "R-2b",
    "over_broad_citation": "R-1a",
    "malformed_evidence_ref": "R-1a",
    "schema_violation": "R-1",
    "decisive_gap_unacknowledged": "R-11",
}


def explain_identifier(target: str) -> RuleExplanation | None:
    """Lookup explanation by rule ID, policy ID, or defect code."""
    cleaned = target.strip().upper().replace("_", "").replace("-", "")
    normalized_dash = target.strip().upper().replace("_", "-")

    # Direct rule match (supports R-3b, R3b, R3B, etc.)
    for rule_id, entry in RULE_CATALOG.items():
        rule_clean = rule_id.upper().replace("_", "").replace("-", "")
        if rule_id.upper().replace("_", "-") == normalized_dash or rule_clean == cleaned:
            return entry

    # Policy match
    for pol_id, mapped_rule in POLICY_TO_RULE.items():
        pol_clean = pol_id.upper().replace("_", "").replace("-", "")
        if pol_id.upper().replace("_", "-") == normalized_dash or pol_clean == cleaned:
            return RULE_CATALOG[mapped_rule]

    # Defect code match
    raw_defect = target.strip().lower().replace("-", "_")
    if raw_defect in DEFECT_TO_RULE:
        return RULE_CATALOG[DEFECT_TO_RULE[raw_defect]]

    # Case-insensitive search over defect codes
    for dcode in DEFECT_CODES:
        if dcode == raw_defect:
            mapped = DEFECT_TO_RULE.get(dcode, "R-1")
            return RULE_CATALOG.get(mapped)

    return None


@dataclass(frozen=True, slots=True)
class DefectDiagnostic:
    """Diagnostic detail for a specific defect detected in an artifact."""

    defect_code: str
    rule_id: str
    severity: str
    message: str
    claim_id: str | None
    pointer: str
    regulatory_rationale: str
    remediation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ArtifactExplanation:
    """Complete diagnostic report for a validated artifact."""

    artifact_path: str
    valid: bool
    evidence_attribution_accuracy: float
    unsupported_claim_rate: float
    total_defects: int
    diagnostics: list[DefectDiagnostic]

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_path": self.artifact_path,
            "valid": self.valid,
            "evidence_attribution_accuracy": self.evidence_attribution_accuracy,
            "unsupported_claim_rate": self.unsupported_claim_rate,
            "total_defects": self.total_defects,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
        }


def explain_artifact_path(
    artifact_path: Path,
    evidence_set_path: Path | None = None,
    policy_set_path: Path | None = None,
    as_of: date | None = None,
) -> ArtifactExplanation:
    """Validate an artifact and generate educational explanations for every defect."""
    with artifact_path.open("r", encoding="utf-8") as handle:
        artifact = json.load(handle)

    evidence_set: dict[str, Any] = {}
    if evidence_set_path and evidence_set_path.is_file():
        with evidence_set_path.open("r", encoding="utf-8") as handle:
            evidence_set = json.load(handle)

    validator = Validator(evidence_set=evidence_set)
    val_res = validator.validate(artifact, EnforcementContext(EnforcementContext.RELEASE))

    diagnostics: list[DefectDiagnostic] = []
    for defect in val_res.defects:
        # Resolve rule explanation
        rule_key = defect.rule_id or DEFECT_TO_RULE.get(defect.code, "R-1")
        expl = RULE_CATALOG.get(rule_key, RULE_CATALOG["R-1"])

        pointer = expl.pointer_target
        if defect.claim_id:
            pointer = f"$.claims[?(@.id=='{defect.claim_id}')]"

        diagnostics.append(
            DefectDiagnostic(
                defect_code=defect.code,
                rule_id=expl.rule_id,
                severity=defect.severity,
                message=defect.message,
                claim_id=defect.claim_id,
                pointer=pointer,
                regulatory_rationale=expl.regulatory_rationale,
                remediation=expl.remediation,
            )
        )

    return ArtifactExplanation(
        artifact_path=str(artifact_path),
        valid=val_res.valid,
        evidence_attribution_accuracy=round(val_res.evidence_attribution_accuracy, 3),
        unsupported_claim_rate=round(val_res.unsupported_claim_rate, 3),
        total_defects=len(diagnostics),
        diagnostics=diagnostics,
    )


def _render_rule_terminal(expl: RuleExplanation) -> None:
    print("=" * 80)
    print(f"  RULE EXPLANATION: {expl.rule_id} ({expl.defect_code})")
    print("=" * 80)
    print(f"Name:             {expl.name}")
    print(f"Rule ID:          {expl.rule_id}")
    print(f"Defect Code:      {expl.defect_code}")
    print(f"Severity:         {expl.severity.upper()}")
    print(f"Enforcement:      {expl.enforcement.capitalize()} (checked by validator)")
    if expl.policy_id:
        print(f"Policy Control:   {expl.policy_id}")
    print()
    print("REGULATORY RATIONALE:")
    for line in _wrap_text(expl.regulatory_rationale, 76):
        print(f"  {line}")
    print()
    print(f"RFC 6901 POINTER TARGET: {expl.pointer_target}")
    print()
    print("[-] FAILING ARTIFACT EXAMPLE:")
    for line in expl.failing_example.split("\n"):
        print(f"    {line}")
    print()
    print("[+] COMPLIANT ARTIFACT EXAMPLE:")
    for line in expl.passing_example.split("\n"):
        print(f"    {line}")
    print()
    print("REMEDIATION INSTRUCTIONS:")
    for line in _wrap_text(expl.remediation, 76):
        print(f"  {line}")
    print("=" * 80)


def _render_artifact_terminal(report: ArtifactExplanation) -> None:
    print("=" * 80)
    print("  FINCRIME ARTIFACT DIAGNOSTIC REPORT")
    print("=" * 80)
    print(f"Artifact:               {report.artifact_path}")
    print(f"Status:                 {'VALID (PASS)' if report.valid else 'DEFECTS DETECTED (FAIL)'}")
    print(f"Evidence Attribution:   {report.evidence_attribution_accuracy * 100:.1f}%")
    print(f"Unsupported Claim Rate: {report.unsupported_claim_rate * 100:.1f}%")
    print(f"Total Defects Found:    {report.total_defects}")
    print("=" * 80)
    print()

    if report.valid:
        print("[OK] Artifact satisfies all Finding Contract structural rules and policy controls.")
        print("No remediation required.")
        return

    for idx, d in enumerate(report.diagnostics, 1):
        print(f"DEFECT #{idx}: [{d.severity.upper()}] {d.rule_id} ({d.defect_code})")
        print("-" * 80)
        print(f"Message:     {d.message}")
        if d.claim_id:
            print(f"Claim ID:    {d.claim_id}")
        print(f"Target Path: {d.pointer}")
        print()
        print("Regulatory Rationale:")
        for line in _wrap_text(d.regulatory_rationale, 74):
            print(f"  {line}")
        print()
        print("Remediation:")
        for line in _wrap_text(d.remediation, 74):
            print(f"  {line}")
        print("-" * 80)
        print()


def _render_catalog_terminal() -> None:
    print("=" * 80)
    print("  FINCRIME RULE & DEFECT TAXONOMY CATALOG")
    print("=" * 80)
    print(f"{'Rule ID':<10} {'Severity':<8} {'Defect Code':<28} {'Rule Name'}")
    print("-" * 80)
    for rule_id, expl in sorted(RULE_CATALOG.items()):
        print(f"{rule_id:<10} {expl.severity.upper():<8} {expl.defect_code:<28} {expl.name}")
    print("-" * 80)
    print("Usage: fincrime explain <rule_id_or_defect_code>")
    print("Example: fincrime explain R-3b")
    print("Example: fincrime explain unsupported_claim")
    print("Example: fincrime explain --artifact <path> --evidence-set <path>")
    print("=" * 80)


def _wrap_text(text: str, width: int = 76) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current: list[str] = []
        cur_len = 0
        for word in words:
            if cur_len + len(word) + (1 if current else 0) <= width:
                current.append(word)
                cur_len += len(word) + (1 if len(current) > 1 else 0)
            else:
                lines.append(" ".join(current))
                current = [word]
                cur_len = len(word)
        if current:
            lines.append(" ".join(current))
    return lines


def cmd_explain(args: argparse.Namespace) -> int:
    """Entry point for ``fincrime explain``."""
    as_json = getattr(args, "json", False)

    # 1. Artifact inspection mode
    if getattr(args, "artifact", None):
        artifact_path = Path(args.artifact)
        if not artifact_path.exists():
            print(f"error: {artifact_path} does not exist", file=sys.stderr)
            return EXIT_USAGE

        evidence_path = Path(args.evidence_set) if getattr(args, "evidence_set", None) else None
        if evidence_path and not evidence_path.exists():
            print(f"error: {evidence_path} does not exist", file=sys.stderr)
            return EXIT_USAGE

        policy_path = Path(args.policy_set) if getattr(args, "policy_set", None) else None

        report = explain_artifact_path(
            artifact_path=artifact_path,
            evidence_set_path=evidence_path,
            policy_set_path=policy_path,
            as_of=getattr(args, "as_of", None),
        )

        if as_json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            _render_artifact_terminal(report)

        return EXIT_OK if report.valid else EXIT_FINDINGS

    # 2. Rule or defect code target mode
    target = getattr(args, "target", None)
    if target:
        expl = explain_identifier(target)
        if expl is None:
            print(f"error: unknown rule or defect code '{target}'", file=sys.stderr)
            print("Run 'fincrime explain --list' to view the catalog.", file=sys.stderr)
            return EXIT_USAGE

        if as_json:
            print(json.dumps(expl.to_dict(), indent=2))
        else:
            _render_rule_terminal(expl)

        return EXIT_OK

    # 3. List / Catalog mode
    if getattr(args, "list", False) or target is None:
        if as_json:
            catalog_payload = [e.to_dict() for e in RULE_CATALOG.values()]
            print(json.dumps(catalog_payload, indent=2))
        else:
            _render_catalog_terminal()
        return EXIT_OK

    return EXIT_OK
