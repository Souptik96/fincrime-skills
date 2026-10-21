"""The typology content of the ``core-2026-10`` pack.

A typology is a *pattern of activity* that has been observed to be used to
move value in ways that make its origin hard to see. It is not a list of
crime. Every typology in this module carries the benign lookalikes it must
be told apart from, because a typology that only describes the guilty
activity produces false positives on honest commerce and teaches the reader
that the pattern is proof.
"""

from __future__ import annotations

from typing import Any

PROHIBITED = [
    "nationality",
    "ethnicity",
    "age_band",
    "religion",
    "disability",
    "political_opinion",
    "sex",
    "gender",
    "immigration_status",
    "language",
]

_FINCEN = "https://www.fincen.gov/resources/statutes-regulations/guidance"
_CFR_1010 = "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010"
_CFR_1020 = "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1020"
_CORNELL_1956 = "https://www.law.cornell.edu/uscode/text/18/1956"
_CORNELL_1957 = "https://www.law.cornell.edu/uscode/text/18/1957"
_CORNELL_5318 = "https://www.law.cornell.edu/uscode/text/31/5318"
_OFAC = "https://ofac.treasury.gov/"


def _src(citation: str, url: str) -> dict[str, str]:
    return {"citation": citation, "url": url, "retrieved": "2026-10-01"}


TYPOLOGIES: list[dict[str, Any]] = [
    {
        "id": "TYP-STRUCTURING-SMURFING",
        "title": "Structuring and smurfing",
        "definition": (
            "The use of many small transactions, conducted by or for one person, so that the "
            "value is moved in amounts that fall below a reporting threshold, and the "
            "underlying activity is never reported as a single transaction. The defining "
            "feature is the relationship between the transaction and the reporting "
            "requirement it sits beneath, not the amount itself."
        ),
        "behavioral_attributes": [
            "amount_to_threshold_ratio",
            "deposit_frequency",
            "branch_dispersion",
            "common_control_evidence_strength",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the individual transactions, each cited by its own source id",
            "the threshold in force and the aggregation rule applied",
            "the evidence of common control between the accounts used",
        ],
        "benign_explanations": [
            "A cash-intensive business whose takings genuinely fall below the threshold on ordinary days.",
            "A customer who splits a payment across accounts for operational reasons such as daily limits.",
            "A business depositing at several branches because each site banks its own takings.",
            "A consumer who makes several small payments to different merchants on one occasion.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, guidance on the avoidance of reporting "
                "requirements, summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "high",
        "notes": (
            "The typology is the *pattern*. Any single small transaction is ordinary, and the "
            "pattern is only visible across transactions, accounts and counterparties."
        ),
    },
    {
        "id": "TYP-TRADE-BASED-MONEY-LAUNDERING",
        "title": "Trade-based money laundering",
        "definition": (
            "The use of the movement of goods and services — rather than of cash — to move "
            "value across a border, usually by over-invoicing or under-invoicing the trade, so "
            "that the value transferred and the value of the goods diverge. The defining "
            "feature is a divergence between a declared value and an independently supportable "
            "value, which requires a comparison class to be meaningful."
        ),
        "behavioral_attributes": [
            "invoice_to_market_value_ratio",
            "counterparty_price_divergence",
            "counterparty_geography",
            "trade_volume_vs_capacity",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the invoices, the contracts and the payments, each cited by its own source id",
            "the independent evidence of market value relied on, and the comparison class used",
            "the shipping, customs and insurance documentation for the goods",
        ],
        "benign_explanations": [
            "Related parties priced on a cost-plus basis as a matter of group policy.",
            "A market with few comparable trades, in which any benchmark is weak.",
            "Freight, insurance and tax bundled into one invoice and excluded from the other.",
            "A genuine change of price, quantity or quality between the compared periods.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, trade-based money laundering guidance, "
                "summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "TYP-MULE-ACCOUNT-NETWORK",
        "title": "Mule account networks",
        "definition": (
            "The use of a network of personal or small-business accounts, opened or used by "
            "people who do not know what the funds are for, to receive and onward-pass value "
            "on behalf of others. The defining feature is the absence of a declared "
            "relationship between the account holder and the movement of the money, together "
            "with the account's use as an intermediary."
        ),
        "behavioral_attributes": [
            "credit_to_debit_ratio",
            "non_related_party_outflow_ratio",
            "distinct_originator_count",
            "account_opening_velocity",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the inbound and outbound records for each account in the network",
            "the evidence linking the accounts, cited by its own source id",
            "each account holder's customer due diligence file and their stated purpose",
        ],
        "benign_explanations": [
            "A payment processor or marketplace settlement account that passes funds by design.",
            "A charity collecting donations and remitting them to a central fund.",
            "A consumer running a resale business on a marketplace.",
            "A family member managing another person's money, candidly and with the family's knowledge.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, guidance on money mule activity, "
                "summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "TYP-ELDER-FINANCIAL-EXPLOITATION",
        "title": "Elder financial exploitation",
        "definition": (
            "The theft, fraud or coercion of a person's money or property by a party the "
            "person knows or trusts, in circumstances where the victim is at a stage of life "
            "that makes the loss hard to notice, hard to report and hard to recover. The "
            "defining feature is the trust relationship and the asymmetry, not the victim's "
            "age, which is a risk factor and not a definition."
        ),
        "behavioral_attributes": [
            "credential_change_to_transfer_lag",
            "new_recipient_share",
            "transfer_amount_vs_baseline",
            "third_party_pressure_indicator",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the transaction records, the credential changes and any recorded contact with the customer",
            "the account's baseline pattern before the change",
            "the reported or observed circumstances, attributed to their source",
        ],
        "benign_explanations": [
            "A customer who has genuinely changed address, phone number or signatory.",
            "A customer making an unusual but properly motivated payment to a new recipient, such as a home improvement contractor.",
            "A bereaved customer reorganising an account they had left dormant.",
            "A joint account holder being added after a change in circumstances.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, guidance on elder financial exploitation, "
                "summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "moderate",
        "notes": (
            "The bias control matters here more than anywhere else in the pack. A pattern of "
            "this shape is not evidence of exploitation in a young customer, and a customer's "
            "age is not a risk factor in an indicator."
        ),
    },
    {
        "id": "TYP-SHELL-COMPANY-LAYERING",
        "title": "Shell company layering",
        "definition": (
            "The use of entities that exist on paper — with no genuine operations, staff or "
            "premises — to receive, hold and pass value, so that the party behind the value "
            "is separated from the transaction by one or more layers of corporate form. The "
            "defining feature is the absence of a real business behind the entity, which has "
            "to be tested against operations rather than inferred from a registration."
        ),
        "behavioral_attributes": [
            "shared_owner_count",
            "shared_address_ratio",
            "intra_group_flow_ratio",
            "return_to_origin_ratio",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the ownership and control evidence for each entity in the chain",
            "the operational evidence — staff, premises, inventory, customers — relied on",
            "the flows between the entities and their stated commercial rationale",
        ],
        "benign_explanations": [
            "A family group of companies that share directors and premises and trade honestly.",
            "A holding or joint-venture vehicle used for tax or risk reasons, with the trades documented.",
            "A newly incorporated company that has not yet traded and holds an opening balance.",
            "Two businesses that share a serviced office address by coincidence.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, guidance on shell companies and beneficial "
                "ownership, summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "TYP-REAL-ESTATE-CASH-LAYERING",
        "title": "Real estate cash layering",
        "definition": (
            "The use of a property transaction — often one that sits outside the ordinary "
            "scope of a person's activity — as the place where value is converted from one "
            "form into another, with the funding arriving in cash or in layers from several "
            "contributors. The defining feature is the size of the value relative to the "
            "buyer's documented capacity to pay."
        ),
        "behavioral_attributes": [
            "funder_count",
            "cash_share_of_purchase",
            "payment_layering_depth",
            "buyer_capacity_ratio",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the purchase agreement, the funding records and the title record",
            "the source of each contribution and the relationship between contributor and buyer",
            "the buyer's documented income, assets and existing borrowing",
        ],
        "benign_explanations": [
            "A purchase funded by a mortgage and a genuine cash deposit from savings.",
            "A family purchase where several relatives contribute and the arrangement is documented.",
            "An investor who used several lenders sequentially and documented each.",
            "A buyer who paid in cash because a cash offer was genuinely made on the property.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, guidance on residential real estate money "
                "laundering, summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "moderate",
    },
    {
        "id": "TYP-TERRORIST-FINANCING-DIVERSION",
        "title": "Terrorist financing diversion",
        "definition": (
            "The provision or collection of funds for, or on behalf of, a person or body "
            "designated under the sanctions regimes, however small the amounts and whatever "
            "the ostensible purpose. The defining feature is the destination, not the "
            "mechanism: small, ordinary transactions become material because of whom they "
            "reach."
        ),
        "behavioral_attributes": [
            "third_party_payment_routing",
            "counterparty_screening_hit_count",
            "payment_size_versus_profile_ratio",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the payment records and the routing through any intermediaries",
            "the screening result that identified the designated party, with its date and source",
            "the stated purpose of the payment and any supporting documentation",
        ],
        "benign_explanations": [
            "A name match that is a different person with the same name, and was cleared on further evidence.",
            "A payment to a person who shares a surname with a designated party.",
            "A charitable donation to an organisation later designated, made before the designation.",
            "A correspondent bank routing that included a designated party in its chain without that party's knowledge.",
        ],
        "sources": [
            _src(
                "Office of Foreign Assets Control, sanctions compliance and reporting guidance, "
                "summarised in the FinCrime regulatory index.",
                _OFAC,
            )
        ],
        "confidence": "high",
        "notes": (
            "Designation status is checked against the date of the transaction, not against "
            "today's list. A party designated after the payment does not make the payment "
            "reportable, and a party delisted today was still designated then."
        ),
    },
    {
        "id": "TYP-ACCOUNT-TAKEOVER-LAUNDERING",
        "title": "Account takeover and the laundering that follows",
        "definition": (
            "The acquisition of control of a victim's account — by credential theft, by "
            "impersonation, or by the coercion of the account holder — followed by the use of "
            "that account to move value, either into an account the attacker controls or on to "
            "third parties. The defining feature is a change in who controls the account, "
            "which the transaction history alone does not show."
        ),
        "behavioral_attributes": [
            "session_to_transfer_lag",
            "device_change_indicator",
            "authentication_retry_count",
            "credential_change_to_transfer_lag",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the session, device and authentication logs",
            "the transfer records made after the change of control",
            "the evidence of the change of control, cited by its own source id",
        ],
        "benign_explanations": [
            "A customer who travelled and began a session from a new device in a new country.",
            "A customer who replaced a phone and was signing in for the first time.",
            "A customer whose password expired and who reset it before a scheduled payment.",
            "A joint account holder returning to online banking after a long absence.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, guidance on account takeover, and the "
                "money laundering offences that may follow it, summarised in the FinCrime "
                "regulatory index.",
                _CORNELL_1956,
            )
        ],
        "confidence": "moderate",
    },
]
