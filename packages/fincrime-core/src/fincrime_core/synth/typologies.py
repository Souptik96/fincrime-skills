"""Typology models and benign lookalike twins for synthetic data generation.

Every financial crime typology describes a behavioral pattern that can be used
to conceal the origin, destination, or ownership of value. Crucially, honest
commercial and civil activities can exhibit near-identical statistical features
(e.g., transaction velocity, threshold proximity, round numbers, geographic
dispersion).

A robust evaluation framework must test that skills do not conflate
heuristic transaction patterns with guilt. Every typology defined here is
paired with a deterministic *benign twin lookalike* requiring explicit
epistemic hypothesis testing and exculpatory evidence resolution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

__all__ = [
    "GaussianFeature",
    "BehavioralProfile",
    "BenignLookalike",
    "TypologyModel",
    "TYPOLOGY_MATRIX",
    "get_typology",
    "get_benign_twin",
    "list_typology_ids",
]


@dataclass(frozen=True, slots=True)
class GaussianFeature:
    """Mean and standard deviation for a continuous behavioral feature."""

    mean: float
    std: float
    min_val: float = 0.0
    max_val: float = 1.0

    def sample_deterministic(self, quantile: float) -> float:
        """Deterministic quantile mapping in [min_val, max_val]."""
        # Approximated inverse error function mapping for deterministic testing
        # quantile in (0, 1) -> value
        q = min(max(quantile, 0.001), 0.999)
        # Rational approximation of probit / normal quantile
        # Abramowitz and Stegun formula 26.2.23
        import math

        if q < 0.5:
            t = math.sqrt(-2.0 * math.log(q))
            z = -(t - ((0.010328 * t + 0.802853) * t + 2.515517) /
                  (((0.001308 * t + 0.189269) * t + 1.432788) * t + 1.0))
        else:
            t = math.sqrt(-2.0 * math.log(1.0 - q))
            z = (t - ((0.010328 * t + 0.802853) * t + 2.515517) /
                 (((0.001308 * t + 0.189269) * t + 1.432788) * t + 1.0))
        val = self.mean + z * self.std
        return min(max(val, self.min_val), self.max_val)


@dataclass(frozen=True, slots=True)
class BehavioralProfile:
    """Quantitative distribution profile across 6 key transaction features."""

    velocity_daily: GaussianFeature
    threshold_proximity_ratio: GaussianFeature
    round_amount_ratio: GaussianFeature
    geographic_dispersion_entropy: GaussianFeature
    inflow_outflow_latency_hours: GaussianFeature
    counterparty_concentration: GaussianFeature

    def as_dict(self) -> dict[str, GaussianFeature]:
        return {
            "velocity_daily": self.velocity_daily,
            "threshold_proximity_ratio": self.threshold_proximity_ratio,
            "round_amount_ratio": self.round_amount_ratio,
            "geographic_dispersion_entropy": self.geographic_dispersion_entropy,
            "inflow_outflow_latency_hours": self.inflow_outflow_latency_hours,
            "counterparty_concentration": self.counterparty_concentration,
        }


@dataclass(frozen=True, slots=True)
class BenignLookalike:
    """A benign twin whose transactional features mirror the paired typology."""

    id: str
    typology_id: str
    title: str
    commercial_scenario: str
    exculpatory_evidence_requirements: tuple[str, ...]
    behavioral_profile: BehavioralProfile


@dataclass(frozen=True, slots=True)
class TypologyModel:
    """A production AML/CTF/Sanctions/Fraud typology model paired with a benign twin."""

    id: str
    title: str
    category: str  # "aml", "ctf", "sanctions", "fraud"
    definition: str
    behavioral_attributes: tuple[str, ...]
    illicit_profile: BehavioralProfile
    benign_twin: BenignLookalike


# ---------------------------------------------------------------------------
# The 12 Production Typologies and their Paired 12 Benign Twins
# ---------------------------------------------------------------------------

_TYP_1_STRUCTURING = TypologyModel(
    id="TYP-STRUCTURING-SMURFING",
    title="Structuring and Smurfing",
    category="aml",
    definition=(
        "The intentional breakdown of large currency amounts into multiple smaller "
        "deposits under statutory currency transaction reporting thresholds ($10,000 in US)."
    ),
    behavioral_attributes=(
        "amount_to_threshold_ratio",
        "deposit_frequency",
        "branch_dispersion",
        "common_control_evidence_strength",
    ),
    illicit_profile=BehavioralProfile(
        velocity_daily=GaussianFeature(mean=4.2, std=0.8, min_val=1.0, max_val=15.0),
        threshold_proximity_ratio=GaussianFeature(mean=0.92, std=0.04, min_val=0.5, max_val=1.0),
        round_amount_ratio=GaussianFeature(mean=0.85, std=0.08, min_val=0.0, max_val=1.0),
        geographic_dispersion_entropy=GaussianFeature(mean=0.78, std=0.10, min_val=0.0, max_val=1.0),
        inflow_outflow_latency_hours=GaussianFeature(mean=12.0, std=4.0, min_val=0.5, max_val=72.0),
        counterparty_concentration=GaussianFeature(mean=0.15, std=0.05, min_val=0.0, max_val=1.0),
    ),
    benign_twin=BenignLookalike(
        id="BENIGN-STRUCTURING-HARVEST",
        typology_id="TYP-STRUCTURING-SMURFING",
        title="Seasonal Agricultural Harvest & Farmers Market Daily Cash Takings",
        commercial_scenario=(
            "An agricultural producer banking daily cash receipts at local branches at the close of "
            "each market day during peak seasonal harvest. Individual daily stall revenues "
            "naturally peak between $8,500 and $9,800 due to stall capacity and daily consumer sales volume."
        ),
        exculpatory_evidence_requirements=(
            "farmers_market_stall_license",
            "daily_pos_cash_register_z_tapes",
            "seasonal_crop_yield_and_scale_tickets",
            "agricultural_commissioner_grower_certificate",
        ),
        behavioral_profile=BehavioralProfile(
            velocity_daily=GaussianFeature(mean=3.9, std=0.7, min_val=1.0, max_val=15.0),
            threshold_proximity_ratio=GaussianFeature(mean=0.90, std=0.05, min_val=0.5, max_val=1.0),
            round_amount_ratio=GaussianFeature(mean=0.82, std=0.09, min_val=0.0, max_val=1.0),
            geographic_dispersion_entropy=GaussianFeature(mean=0.74, std=0.11, min_val=0.0, max_val=1.0),
            inflow_outflow_latency_hours=GaussianFeature(mean=14.0, std=4.5, min_val=0.5, max_val=72.0),
            counterparty_concentration=GaussianFeature(mean=0.18, std=0.06, min_val=0.0, max_val=1.0),
        ),
    ),
)

_TYP_2_MULE = TypologyModel(
    id="TYP-MULE-ACCOUNT-NETWORK",
    title="Mule Account Networks",
    category="aml",
    definition=(
        "The operation of personal or small business accounts to receive and immediately onward-transfer "
        "illicit funds on behalf of third parties, acting as transactional intermediaries."
    ),
    behavioral_attributes=(
        "credit_to_debit_ratio",
        "non_related_party_outflow_ratio",
        "distinct_originator_count",
        "account_opening_velocity",
    ),
    illicit_profile=BehavioralProfile(
        velocity_daily=GaussianFeature(mean=5.5, std=1.2, min_val=1.0, max_val=25.0),
        threshold_proximity_ratio=GaussianFeature(mean=0.45, std=0.15, min_val=0.1, max_val=1.0),
        round_amount_ratio=GaussianFeature(mean=0.72, std=0.12, min_val=0.0, max_val=1.0),
        geographic_dispersion_entropy=GaussianFeature(mean=0.82, std=0.08, min_val=0.0, max_val=1.0),
        inflow_outflow_latency_hours=GaussianFeature(mean=2.1, std=0.8, min_val=0.1, max_val=24.0),
        counterparty_concentration=GaussianFeature(mean=0.88, std=0.07, min_val=0.0, max_val=1.0),
    ),
    benign_twin=BenignLookalike(
        id="BENIGN-MULE-TUITION-POOLING",
        typology_id="TYP-MULE-ACCOUNT-NETWORK",
        title="University Student Shared Housing & Tuition Fee Pooling",
        commercial_scenario=(
            "A designated student house manager receiving individual semester rent and tuition payments "
            "from 5 flatmates via P2P apps and immediately issuing a single consolidated wire transfer "
            "to the university bursar or landlord management company."
        ),
        exculpatory_evidence_requirements=(
            "joint_residential_lease_agreement",
            "university_bursar_tuition_invoice",
            "student_id_enrollment_verifications",
            "flatmate_cost_sharing_reconciliation",
        ),
        behavioral_profile=BehavioralProfile(
            velocity_daily=GaussianFeature(mean=5.1, std=1.0, min_val=1.0, max_val=25.0),
            threshold_proximity_ratio=GaussianFeature(mean=0.42, std=0.14, min_val=0.1, max_val=1.0),
            round_amount_ratio=GaussianFeature(mean=0.75, std=0.11, min_val=0.0, max_val=1.0),
            geographic_dispersion_entropy=GaussianFeature(mean=0.79, std=0.09, min_val=0.0, max_val=1.0),
            inflow_outflow_latency_hours=GaussianFeature(mean=2.4, std=0.9, min_val=0.1, max_val=24.0),
            counterparty_concentration=GaussianFeature(mean=0.85, std=0.08, min_val=0.0, max_val=1.0),
        ),
    ),
)

_TYP_3_ELDER = TypologyModel(
    id="TYP-ELDER-FINANCIAL-EXPLOITATION",
    title="Elder Financial Exploitation",
    category="fraud",
    definition=(
        "The unauthorized, coerced, or fraudulent diversion of an older adult's funds or assets "
        "by caregivers, relatives, or predatory third parties."
    ),
    behavioral_attributes=(
        "credential_change_to_transfer_lag",
        "new_recipient_share",
        "transfer_amount_vs_baseline",
        "third_party_pressure_indicator",
    ),
    illicit_profile=BehavioralProfile(
        velocity_daily=GaussianFeature(mean=2.8, std=0.9, min_val=0.5, max_val=10.0),
        threshold_proximity_ratio=GaussianFeature(mean=0.75, std=0.18, min_val=0.1, max_val=1.0),
        round_amount_ratio=GaussianFeature(mean=0.90, std=0.06, min_val=0.0, max_val=1.0),
        geographic_dispersion_entropy=GaussianFeature(mean=0.35, std=0.12, min_val=0.0, max_val=1.0),
        inflow_outflow_latency_hours=GaussianFeature(mean=8.0, std=3.0, min_val=0.5, max_val=48.0),
        counterparty_concentration=GaussianFeature(mean=0.94, std=0.04, min_val=0.0, max_val=1.0),
    ),
    benign_twin=BenignLookalike(
        id="BENIGN-ELDER-HOME-MODIFICATION",
        typology_id="TYP-ELDER-FINANCIAL-EXPLOITATION",
        title="Senior Living Accessibility & Mobility Contractor Payments",
        commercial_scenario=(
            "An elderly customer paying milestone draws to a licensed general contractor for wheelchair "
            "ramp construction, roll-in shower installation, and medical stairlift retrofitting on their home."
        ),
        exculpatory_evidence_requirements=(
            "municipal_building_permit_accessibility",
            "licensed_contractor_signed_scope_of_work",
            "milestone_inspection_and_completion_signoff",
            "architectural_accessibility_plans",
        ),
        behavioral_profile=BehavioralProfile(
            velocity_daily=GaussianFeature(mean=2.5, std=0.8, min_val=0.5, max_val=10.0),
            threshold_proximity_ratio=GaussianFeature(mean=0.72, std=0.19, min_val=0.1, max_val=1.0),
            round_amount_ratio=GaussianFeature(mean=0.88, std=0.07, min_val=0.0, max_val=1.0),
            geographic_dispersion_entropy=GaussianFeature(mean=0.32, std=0.11, min_val=0.0, max_val=1.0),
            inflow_outflow_latency_hours=GaussianFeature(mean=9.5, std=3.2, min_val=0.5, max_val=48.0),
            counterparty_concentration=GaussianFeature(mean=0.91, std=0.05, min_val=0.0, max_val=1.0),
        ),
    ),
)

_TYP_4_ATO = TypologyModel(
    id="TYP-ACCOUNT-TAKEOVER-LAUNDERING",
    title="Account Takeover Laundering",
    category="fraud",
    definition=(
        "The compromise and unauthorized control of a legitimate account followed by immediate "
        "rapid funds depletion or intermediary pass-through transfers."
    ),
    behavioral_attributes=(
        "session_to_transfer_lag",
        "device_change_indicator",
        "authentication_retry_count",
        "credential_change_to_transfer_lag",
    ),
    illicit_profile=BehavioralProfile(
        velocity_daily=GaussianFeature(mean=6.8, std=1.5, min_val=1.0, max_val=30.0),
        threshold_proximity_ratio=GaussianFeature(mean=0.82, std=0.12, min_val=0.1, max_val=1.0),
        round_amount_ratio=GaussianFeature(mean=0.78, std=0.10, min_val=0.0, max_val=1.0),
        geographic_dispersion_entropy=GaussianFeature(mean=0.91, std=0.06, min_val=0.0, max_val=1.0),
        inflow_outflow_latency_hours=GaussianFeature(mean=0.8, std=0.3, min_val=0.05, max_val=12.0),
        counterparty_concentration=GaussianFeature(mean=0.82, std=0.10, min_val=0.0, max_val=1.0),
    ),
    benign_twin=BenignLookalike(
        id="BENIGN-ATO-EXPAT-RELOCATION",
        typology_id="TYP-ACCOUNT-TAKEOVER-LAUNDERING",
        title="Corporate Executive International Relocation on Emergency Device",
        commercial_scenario=(
            "A corporate executive relocating internationally whose mobile handset was damaged during travel, "
            "authenticating online banking on a replacement device from an overseas corporate IP to execute "
            "urgent pre-scheduled international relocation wires."
        ),
        exculpatory_evidence_requirements=(
            "corporate_expatriate_assignment_letter",
            "airline_boarding_pass_and_customs_entry_stamp",
            "corporate_it_hardware_replacement_ticket",
            "relocation_management_closing_invoice",
        ),
        behavioral_profile=BehavioralProfile(
            velocity_daily=GaussianFeature(mean=6.4, std=1.3, min_val=1.0, max_val=30.0),
            threshold_proximity_ratio=GaussianFeature(mean=0.80, std=0.13, min_val=0.1, max_val=1.0),
            round_amount_ratio=GaussianFeature(mean=0.75, std=0.11, min_val=0.0, max_val=1.0),
            geographic_dispersion_entropy=GaussianFeature(mean=0.88, std=0.07, min_val=0.0, max_val=1.0),
            inflow_outflow_latency_hours=GaussianFeature(mean=1.1, std=0.4, min_val=0.05, max_val=12.0),
            counterparty_concentration=GaussianFeature(mean=0.80, std=0.11, min_val=0.0, max_val=1.0),
        ),
    ),
)

_TYP_5_TBML = TypologyModel(
    id="TYP-TRADE-BASED-MONEY-LAUNDERING",
    title="Trade-Based Money Laundering Over-Invoicing",
    category="aml",
    definition=(
        "The cross-border movement of illicit value using commercial trade transactions, typically "
        "through systematic over-invoicing or under-invoicing of physical goods relative to fair value."
    ),
    behavioral_attributes=(
        "invoice_to_market_value_ratio",
        "counterparty_price_divergence",
        "counterparty_geography",
        "trade_volume_vs_capacity",
    ),
    illicit_profile=BehavioralProfile(
        velocity_daily=GaussianFeature(mean=1.8, std=0.5, min_val=0.1, max_val=10.0),
        threshold_proximity_ratio=GaussianFeature(mean=0.88, std=0.10, min_val=0.1, max_val=1.0),
        round_amount_ratio=GaussianFeature(mean=0.65, std=0.15, min_val=0.0, max_val=1.0),
        geographic_dispersion_entropy=GaussianFeature(mean=0.84, std=0.08, min_val=0.0, max_val=1.0),
        inflow_outflow_latency_hours=GaussianFeature(mean=36.0, std=10.0, min_val=2.0, max_val=120.0),
        counterparty_concentration=GaussianFeature(mean=0.72, std=0.12, min_val=0.0, max_val=1.0),
    ),
    benign_twin=BenignLookalike(
        id="BENIGN-TBML-AEROSPACE-TOOLING",
        typology_id="TYP-TRADE-BASED-MONEY-LAUNDERING",
        title="Custom Aerospace Precision Tooling & Expedited Air Freight",
        commercial_scenario=(
            "Cross-border procurement of prototype aerospace CNC titanium tooling with significant non-recurring "
            "engineering (NRE) charges, proprietary metallurgy surcharges, and charter air freight included on the master invoice."
        ),
        exculpatory_evidence_requirements=(
            "aerospace_engineering_nre_contract",
            "certified_cmm_inspection_reports",
            "charter_air_waybill_with_cargo_manifest",
            "customs_binding_classification_ruling",
        ),
        behavioral_profile=BehavioralProfile(
            velocity_daily=GaussianFeature(mean=1.7, std=0.5, min_val=0.1, max_val=10.0),
            threshold_proximity_ratio=GaussianFeature(mean=0.85, std=0.11, min_val=0.1, max_val=1.0),
            round_amount_ratio=GaussianFeature(mean=0.62, std=0.14, min_val=0.0, max_val=1.0),
            geographic_dispersion_entropy=GaussianFeature(mean=0.81, std=0.09, min_val=0.0, max_val=1.0),
            inflow_outflow_latency_hours=GaussianFeature(mean=38.0, std=11.0, min_val=2.0, max_val=120.0),
            counterparty_concentration=GaussianFeature(mean=0.70, std=0.13, min_val=0.0, max_val=1.0),
        ),
    ),
)

_TYP_6_SHELL = TypologyModel(
    id="TYP-SHELL-COMPANY-LAYERING",
    title="Shell Company Layering",
    category="aml",
    definition=(
        "The use of multi-layered corporate entities with no apparent commercial premises, employees, "
        "or operations to obscure beneficial ownership and transfer capital."
    ),
    behavioral_attributes=(
        "shared_owner_count",
        "shared_address_ratio",
        "intra_group_flow_ratio",
        "return_to_origin_ratio",
    ),
    illicit_profile=BehavioralProfile(
        velocity_daily=GaussianFeature(mean=3.2, std=0.8, min_val=0.5, max_val=15.0),
        threshold_proximity_ratio=GaussianFeature(mean=0.78, std=0.15, min_val=0.1, max_val=1.0),
        round_amount_ratio=GaussianFeature(mean=0.88, std=0.08, min_val=0.0, max_val=1.0),
        geographic_dispersion_entropy=GaussianFeature(mean=0.25, std=0.10, min_val=0.0, max_val=1.0),
        inflow_outflow_latency_hours=GaussianFeature(mean=4.5, std=1.5, min_val=0.5, max_val=48.0),
        counterparty_concentration=GaussianFeature(mean=0.65, std=0.12, min_val=0.0, max_val=1.0),
    ),
    benign_twin=BenignLookalike(
        id="BENIGN-SHELL-FLEET-LEASING-SPV",
        typology_id="TYP-SHELL-COMPANY-LAYERING",
        title="Bankruptcy-Remote Corporate Equipment Fleet Leasing SPV",
        commercial_scenario=(
            "A bankruptcy-remote special purpose vehicle (SPV) established solely to hold title to heavy "
            "construction machinery, sharing registered agent facilities with parent group entities and transferring "
            "intercompany lease proceeds."
        ),
        exculpatory_evidence_requirements=(
            "master_equipment_lease_agreement",
            "state_ucc1_financing_statement_filings",
            "audited_consolidated_group_tax_return",
            "spv_corporate_resolution_and_trust_indenture",
        ),
        behavioral_profile=BehavioralProfile(
            velocity_daily=GaussianFeature(mean=3.0, std=0.7, min_val=0.5, max_val=15.0),
            threshold_proximity_ratio=GaussianFeature(mean=0.75, std=0.16, min_val=0.1, max_val=1.0),
            round_amount_ratio=GaussianFeature(mean=0.85, std=0.09, min_val=0.0, max_val=1.0),
            geographic_dispersion_entropy=GaussianFeature(mean=0.28, std=0.11, min_val=0.0, max_val=1.0),
            inflow_outflow_latency_hours=GaussianFeature(mean=5.2, std=1.8, min_val=0.5, max_val=48.0),
            counterparty_concentration=GaussianFeature(mean=0.62, std=0.13, min_val=0.0, max_val=1.0),
        ),
    ),
)

_TYP_7_REAL_ESTATE = TypologyModel(
    id="TYP-REAL-ESTATE-CASH-LAYERING",
    title="Real Estate Cash Layering",
    category="aml",
    definition=(
        "The conversion of illicit cash into high-value real estate through structured deposits, "
        "multiple third-party cashier's checks, and opaque closing escrow accounts."
    ),
    behavioral_attributes=(
        "funder_count",
        "cash_share_of_purchase",
        "payment_layering_depth",
        "buyer_capacity_ratio",
    ),
    illicit_profile=BehavioralProfile(
        velocity_daily=GaussianFeature(mean=4.0, std=1.0, min_val=0.5, max_val=20.0),
        threshold_proximity_ratio=GaussianFeature(mean=0.91, std=0.06, min_val=0.2, max_val=1.0),
        round_amount_ratio=GaussianFeature(mean=0.92, std=0.05, min_val=0.0, max_val=1.0),
        geographic_dispersion_entropy=GaussianFeature(mean=0.68, std=0.12, min_val=0.0, max_val=1.0),
        inflow_outflow_latency_hours=GaussianFeature(mean=18.0, std=6.0, min_val=1.0, max_val=96.0),
        counterparty_concentration=GaussianFeature(mean=0.92, std=0.05, min_val=0.0, max_val=1.0),
    ),
    benign_twin=BenignLookalike(
        id="BENIGN-REAL-ESTATE-FAMILY-POOL",
        typology_id="TYP-REAL-ESTATE-CASH-LAYERING",
        title="Multi-Generational Family Home Purchase & Down Payment Gift Pooling",
        commercial_scenario=(
            "Extended family members pooling personal savings via bank cashier's checks with documented "
            "non-repayable gift letters to fund the equity down payment for a multi-generational primary residence."
        ),
        exculpatory_evidence_requirements=(
            "notarized_family_gift_affidavits",
            "hud1_closing_settlement_statement",
            "donor_12m_bank_statements_proving_origin",
            "title_insurance_preliminary_report",
        ),
        behavioral_profile=BehavioralProfile(
            velocity_daily=GaussianFeature(mean=3.7, std=0.9, min_val=0.5, max_val=20.0),
            threshold_proximity_ratio=GaussianFeature(mean=0.88, std=0.07, min_val=0.2, max_val=1.0),
            round_amount_ratio=GaussianFeature(mean=0.89, std=0.06, min_val=0.0, max_val=1.0),
            geographic_dispersion_entropy=GaussianFeature(mean=0.65, std=0.13, min_val=0.0, max_val=1.0),
            inflow_outflow_latency_hours=GaussianFeature(mean=20.0, std=6.5, min_val=1.0, max_val=96.0),
            counterparty_concentration=GaussianFeature(mean=0.89, std=0.06, min_val=0.0, max_val=1.0),
        ),
    ),
)

_TYP_8_TF = TypologyModel(
    id="TYP-TERRORIST-FINANCING-DIVERSION",
    title="Terrorist Financing Diversion",
    category="ctf",
    definition=(
        "The collection or redirection of funds, frequently through non-profit organizations or informal "
        "remittance corridors, to designated terrorist organizations or violent extremist groups."
    ),
    behavioral_attributes=(
        "third_party_payment_routing",
        "counterparty_screening_hit_count",
        "payment_size_versus_profile_ratio",
    ),
    illicit_profile=BehavioralProfile(
        velocity_daily=GaussianFeature(mean=2.2, std=0.6, min_val=0.2, max_val=10.0),
        threshold_proximity_ratio=GaussianFeature(mean=0.25, std=0.10, min_val=0.05, max_val=1.0),
        round_amount_ratio=GaussianFeature(mean=0.80, std=0.10, min_val=0.0, max_val=1.0),
        geographic_dispersion_entropy=GaussianFeature(mean=0.86, std=0.07, min_val=0.0, max_val=1.0),
        inflow_outflow_latency_hours=GaussianFeature(mean=16.0, std=5.0, min_val=1.0, max_val=72.0),
        counterparty_concentration=GaussianFeature(mean=0.35, std=0.10, min_val=0.0, max_val=1.0),
    ),
    benign_twin=BenignLookalike(
        id="BENIGN-TF-REFUGEE-RELIEF",
        typology_id="TYP-TERRORIST-FINANCING-DIVERSION",
        title="UNHCR Registered Humanitarian Refugee Medical Support",
        commercial_scenario=(
            "Small, repetitive personal remittances sent by naturalized expatriates to relatives residing "
            "in UNHCR-administered refugee camps near conflict border zones for verified emergency medical treatment."
        ),
        exculpatory_evidence_requirements=(
            "unhcr_refugee_registration_card",
            "hospital_certified_medical_invoices",
            "physician_emergency_prescription_records",
            "red_cross_family_tracing_documentation",
        ),
        behavioral_profile=BehavioralProfile(
            velocity_daily=GaussianFeature(mean=2.1, std=0.6, min_val=0.2, max_val=10.0),
            threshold_proximity_ratio=GaussianFeature(mean=0.24, std=0.09, min_val=0.05, max_val=1.0),
            round_amount_ratio=GaussianFeature(mean=0.78, std=0.11, min_val=0.0, max_val=1.0),
            geographic_dispersion_entropy=GaussianFeature(mean=0.83, std=0.08, min_val=0.0, max_val=1.0),
            inflow_outflow_latency_hours=GaussianFeature(mean=17.5, std=5.5, min_val=1.0, max_val=72.0),
            counterparty_concentration=GaussianFeature(mean=0.38, std=0.11, min_val=0.0, max_val=1.0),
        ),
    ),
)

_TYP_9_FUNNEL = TypologyModel(
    id="TYP-FUNNEL-HUMAN-TRAFFICKING",
    title="Funnel Account and Human Trafficking Indicators",
    category="aml",
    definition=(
        "The use of branch networks across multiple geographic locations to deposit cash into a single "
        "funnel account, followed by immediate withdrawals at a distant urban or border branch, characteristic "
        "of human smuggling and trafficking organizations."
    ),
    behavioral_attributes=(
        "multi_state_deposit_frequency",
        "deposit_to_withdrawal_distance_km",
        "teller_cash_outflow_velocity",
        "origin_terminal_dispersion",
    ),
    illicit_profile=BehavioralProfile(
        velocity_daily=GaussianFeature(mean=7.5, std=1.8, min_val=1.0, max_val=35.0),
        threshold_proximity_ratio=GaussianFeature(mean=0.65, std=0.18, min_val=0.1, max_val=1.0),
        round_amount_ratio=GaussianFeature(mean=0.94, std=0.04, min_val=0.0, max_val=1.0),
        geographic_dispersion_entropy=GaussianFeature(mean=0.95, std=0.04, min_val=0.0, max_val=1.0),
        inflow_outflow_latency_hours=GaussianFeature(mean=1.5, std=0.6, min_val=0.1, max_val=24.0),
        counterparty_concentration=GaussianFeature(mean=0.20, std=0.06, min_val=0.0, max_val=1.0),
    ),
    benign_twin=BenignLookalike(
        id="BENIGN-FUNNEL-FIELD-CREW",
        typology_id="TYP-FUNNEL-HUMAN-TRAFFICKING",
        title="Regional Disaster Restoration Field Crew Per-Diem Reimbursements",
        commercial_scenario=(
            "A regional commercial storm and flood restoration contractor deploying emergency repair crews "
            "across 4 states; crew leads deposit unspent project petty cash at local regional branches, "
            "with central operations withdrawing cash in the metropolitan headquarters for weekly subcontractor advances."
        ),
        exculpatory_evidence_requirements=(
            "commercial_restoration_work_orders",
            "fleet_vehicle_telematics_and_gps_logs",
            "daily_subcontractor_timesheets",
            "emergency_insurance_carrier_retainer_agreements",
        ),
        behavioral_profile=BehavioralProfile(
            velocity_daily=GaussianFeature(mean=7.0, std=1.6, min_val=1.0, max_val=35.0),
            threshold_proximity_ratio=GaussianFeature(mean=0.62, std=0.17, min_val=0.1, max_val=1.0),
            round_amount_ratio=GaussianFeature(mean=0.91, std=0.05, min_val=0.0, max_val=1.0),
            geographic_dispersion_entropy=GaussianFeature(mean=0.92, std=0.05, min_val=0.0, max_val=1.0),
            inflow_outflow_latency_hours=GaussianFeature(mean=1.8, std=0.7, min_val=0.1, max_val=24.0),
            counterparty_concentration=GaussianFeature(mean=0.24, std=0.07, min_val=0.0, max_val=1.0),
        ),
    ),
)

_TYP_10_CRYPTO = TypologyModel(
    id="TYP-CRYPTO-MIXER-HOPPING",
    title="Virtual Asset Mixer Hopping and Peeling Chains",
    category="aml",
    definition=(
        "The rapid routing of digital asset transactions through multiple decentralized mixing protocols, "
        "unhosted intermediary addresses, and cross-chain bridges to break on-chain transactional provenance."
    ),
    behavioral_attributes=(
        "wallet_hop_velocity",
        "chain_peeling_depth",
        "mixer_smart_contract_interaction",
        "fiat_offramp_velocity",
    ),
    illicit_profile=BehavioralProfile(
        velocity_daily=GaussianFeature(mean=12.0, std=2.5, min_val=2.0, max_val=60.0),
        threshold_proximity_ratio=GaussianFeature(mean=0.55, std=0.20, min_val=0.05, max_val=1.0),
        round_amount_ratio=GaussianFeature(mean=0.20, std=0.10, min_val=0.0, max_val=1.0),
        geographic_dispersion_entropy=GaussianFeature(mean=0.90, std=0.06, min_val=0.0, max_val=1.0),
        inflow_outflow_latency_hours=GaussianFeature(mean=0.4, std=0.15, min_val=0.01, max_val=8.0),
        counterparty_concentration=GaussianFeature(mean=0.12, std=0.04, min_val=0.0, max_val=1.0),
    ),
    benign_twin=BenignLookalike(
        id="BENIGN-CRYPTO-MM-REBALANCING",
        typology_id="TYP-CRYPTO-MIXER-HOPPING",
        title="Algorithmic DeFi Market Maker Cross-DEX Inventory Rebalancing",
        commercial_scenario=(
            "An institutional proprietary trading desk executing automated algorithmic arbitrage and "
            "delta-neutral inventory rebalancing across multiple decentralized exchange (DEX) liquidity pools "
            "and layer-2 rollups."
        ),
        exculpatory_evidence_requirements=(
            "institutional_cdd_and_corporate_charter",
            "proprietary_trading_desk_audited_api_logs",
            "smart_contract_security_audit_reports",
            "cpa_certified_digital_asset_inventory_ledger",
        ),
        behavioral_profile=BehavioralProfile(
            velocity_daily=GaussianFeature(mean=11.5, std=2.2, min_val=2.0, max_val=60.0),
            threshold_proximity_ratio=GaussianFeature(mean=0.52, std=0.19, min_val=0.05, max_val=1.0),
            round_amount_ratio=GaussianFeature(mean=0.22, std=0.11, min_val=0.0, max_val=1.0),
            geographic_dispersion_entropy=GaussianFeature(mean=0.88, std=0.07, min_val=0.0, max_val=1.0),
            inflow_outflow_latency_hours=GaussianFeature(mean=0.5, std=0.18, min_val=0.01, max_val=8.0),
            counterparty_concentration=GaussianFeature(mean=0.14, std=0.05, min_val=0.0, max_val=1.0),
        ),
    ),
)

_TYP_11_TRANSSHIPMENT = TypologyModel(
    id="TYP-TRANSSHIPMENT-SANCTIONS-EVASION",
    title="Transshipment Sanctions Evasion",
    category="sanctions",
    definition=(
        "The diversion and rerouting of restricted or dual-use commodities through intermediate third-country "
        "transshipment ports (e.g. Free Trade Zones) to disguise the ultimate sanctioned end-user or destination."
    ),
    behavioral_attributes=(
        "intermediate_port_dwell_time",
        "bill_of_lading_consignee_switching",
        "dual_use_hs_code_classification",
        "vessel_ais_gap_count",
    ),
    illicit_profile=BehavioralProfile(
        velocity_daily=GaussianFeature(mean=1.5, std=0.4, min_val=0.1, max_val=8.0),
        threshold_proximity_ratio=GaussianFeature(mean=0.86, std=0.10, min_val=0.1, max_val=1.0),
        round_amount_ratio=GaussianFeature(mean=0.50, std=0.15, min_val=0.0, max_val=1.0),
        geographic_dispersion_entropy=GaussianFeature(mean=0.92, std=0.05, min_val=0.0, max_val=1.0),
        inflow_outflow_latency_hours=GaussianFeature(mean=44.0, std=12.0, min_val=4.0, max_val=168.0),
        counterparty_concentration=GaussianFeature(mean=0.58, std=0.12, min_val=0.0, max_val=1.0),
    ),
    benign_twin=BenignLookalike(
        id="BENIGN-TRANSSHIPMENT-FEEDER-LOGISTICS",
        typology_id="TYP-TRANSSHIPMENT-SANCTIONS-EVASION",
        title="Global Hub-and-Spoke Feeder Vessel Consolidation",
        commercial_scenario=(
            "An international container shipping line discharging containers at a major regional transshipment "
            "hub for feeder vessel consolidation and onward delivery to non-sanctioned shallow-draft secondary ports."
        ),
        exculpatory_evidence_requirements=(
            "through_bill_of_lading_with_final_port_declared",
            "port_authority_non_manipulation_certificate",
            "continuous_satellite_ais_track_history",
            "customs_bonded_feeder_manifest",
        ),
        behavioral_profile=BehavioralProfile(
            velocity_daily=GaussianFeature(mean=1.4, std=0.4, min_val=0.1, max_val=8.0),
            threshold_proximity_ratio=GaussianFeature(mean=0.84, std=0.11, min_val=0.1, max_val=1.0),
            round_amount_ratio=GaussianFeature(mean=0.48, std=0.14, min_val=0.0, max_val=1.0),
            geographic_dispersion_entropy=GaussianFeature(mean=0.89, std=0.06, min_val=0.0, max_val=1.0),
            inflow_outflow_latency_hours=GaussianFeature(mean=46.0, std=13.0, min_val=4.0, max_val=168.0),
            counterparty_concentration=GaussianFeature(mean=0.55, std=0.13, min_val=0.0, max_val=1.0),
        ),
    ),
)

_TYP_12_PAYROLL = TypologyModel(
    id="TYP-PAYROLL-GHOST-EMPLOYEE",
    title="Payroll and Ghost Employee Fraud",
    category="fraud",
    definition=(
        "The disbursement of company payroll to non-existent or fictitious employees, often sharing banking "
        "details, IP addresses, or residential information, followed by immediate cash liquidation."
    ),
    behavioral_attributes=(
        "shared_direct_deposit_routing",
        "payroll_origination_ip_entropy",
        "immediate_atm_sweep_ratio",
        "tax_identifier_validation_failure",
    ),
    illicit_profile=BehavioralProfile(
        velocity_daily=GaussianFeature(mean=8.2, std=1.8, min_val=1.0, max_val=40.0),
        threshold_proximity_ratio=GaussianFeature(mean=0.35, std=0.12, min_val=0.05, max_val=1.0),
        round_amount_ratio=GaussianFeature(mean=0.90, std=0.06, min_val=0.0, max_val=1.0),
        geographic_dispersion_entropy=GaussianFeature(mean=0.18, std=0.06, min_val=0.0, max_val=1.0),
        inflow_outflow_latency_hours=GaussianFeature(mean=2.8, std=0.9, min_val=0.1, max_val=24.0),
        counterparty_concentration=GaussianFeature(mean=0.96, std=0.03, min_val=0.0, max_val=1.0),
    ),
    benign_twin=BenignLookalike(
        id="BENIGN-PAYROLL-SEASONAL-DORMITORY",
        typology_id="TYP-PAYROLL-GHOST-EMPLOYEE",
        title="Seasonal Factory Congregate Dormitory Workers",
        commercial_scenario=(
            "A food processing manufacturing facility employing temporary seasonal workers residing in "
            "employer-provided congregate housing. Workers use the facility HR computer terminal for banking "
            "and hold payroll debit cards with an on-site local credit union ATM."
        ),
        exculpatory_evidence_requirements=(
            "form_i9_employment_eligibility_verifications",
            "biometric_turnstile_shift_clock_records",
            "congregate_dormitory_residential_lease",
            "state_unemployment_tax_contribution_filing",
        ),
        behavioral_profile=BehavioralProfile(
            velocity_daily=GaussianFeature(mean=7.8, std=1.6, min_val=1.0, max_val=40.0),
            threshold_proximity_ratio=GaussianFeature(mean=0.33, std=0.11, min_val=0.05, max_val=1.0),
            round_amount_ratio=GaussianFeature(mean=0.88, std=0.07, min_val=0.0, max_val=1.0),
            geographic_dispersion_entropy=GaussianFeature(mean=0.21, std=0.07, min_val=0.0, max_val=1.0),
            inflow_outflow_latency_hours=GaussianFeature(mean=3.2, std=1.0, min_val=0.1, max_val=24.0),
            counterparty_concentration=GaussianFeature(mean=0.93, std=0.04, min_val=0.0, max_val=1.0),
        ),
    ),
)


TYPOLOGY_MATRIX: tuple[TypologyModel, ...] = (
    _TYP_1_STRUCTURING,
    _TYP_2_MULE,
    _TYP_3_ELDER,
    _TYP_4_ATO,
    _TYP_5_TBML,
    _TYP_6_SHELL,
    _TYP_7_REAL_ESTATE,
    _TYP_8_TF,
    _TYP_9_FUNNEL,
    _TYP_10_CRYPTO,
    _TYP_11_TRANSSHIPMENT,
    _TYP_12_PAYROLL,
)

_BY_ID: dict[str, TypologyModel] = {t.id: t for t in TYPOLOGY_MATRIX}
_BENIGN_BY_TYPOLOGY: dict[str, BenignLookalike] = {t.id: t.benign_twin for t in TYPOLOGY_MATRIX}


def get_typology(typology_id: str) -> TypologyModel:
    """Retrieve a typology model by ID."""
    if typology_id not in _BY_ID:
        raise KeyError(f"Unknown typology ID: {typology_id!r}. Known: {sorted(_BY_ID)}")
    return _BY_ID[typology_id]


def get_benign_twin(typology_id: str) -> BenignLookalike:
    """Retrieve the paired benign twin lookalike for a typology."""
    if typology_id not in _BENIGN_BY_TYPOLOGY:
        raise KeyError(f"No benign twin for typology ID: {typology_id!r}")
    return _BENIGN_BY_TYPOLOGY[typology_id]


def list_typology_ids() -> list[str]:
    """Return the 12 production typology IDs in fixed order."""
    return [t.id for t in TYPOLOGY_MATRIX]
