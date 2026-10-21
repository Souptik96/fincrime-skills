"""The indicator content of the ``core-2026-10`` pack.

An indicator is a *measured pattern*, never a conclusion. Every definition
here says what was observed, and every one of them is paired with the
benign explanations that would produce the same observation — because an
indicator without a benign population is a detector with no false-positive
rate, and a detector with no false-positive rate is an accusation.

Every indicator lists the full set of attributes it may not be defined over.
The list is the bias control: an indicator is defined over behaviour, never
over a protected attribute or a proxy for one.
"""

from __future__ import annotations

from typing import Any

#: The attributes an indicator may not be defined over, directly or as a
#: proxy. Listed in full on every indicator so that the control is visible in
#: the record rather than in a policy document nobody reads.
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
_OFAC = "https://ofac.treasury.gov/"


def _src(citation: str, url: str) -> dict[str, str]:
    """One source entry: a citation, where it can be read, and when it was read."""
    return {"citation": citation, "url": url, "retrieved": "2026-10-01"}


INDICATORS: list[dict[str, Any]] = [
    {
        "id": "IND-STRUCT-THRESHOLD-PROXIMITY",
        "title": "Cash deposits clustered immediately below the currency transaction reporting threshold",
        "definition": (
            "Cash deposits that cluster immediately below the currency transaction reporting "
            "threshold in force for the monitoring window, across one or more accounts or "
            "branches. The indicator describes a measured distribution of amounts; it does not "
            "describe intent, and it is not on its own evidence that a reporting requirement "
            "was avoided."
        ),
        "typology_refs": ["TYP-STRUCTURING-SMURFING"],
        "behavioral_attributes": [
            "deposit_amount",
            "deposit_frequency",
            "branch_dispersion",
            "cash_intensity_of_declared_business",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "each deposit record that forms the cluster, cited by its own source id and pointer",
            "the threshold value in force for the monitoring window, and the date it changed",
            "the subject's declared business profile and stated cash intensity, where one exists",
        ],
        "benign_explanations": [
            "A cash-intensive legitimate business depositing daily takings that happen to fall below the reporting threshold.",
            "A business splitting deposits across branches for operational reasons such as a branch's daily cash limit or a till shortage.",
            "Seasonal or end-of-week takings that cluster below the threshold by coincidence of trading volume.",
            "A recently formed business whose declared cash intensity is below its actual takings because it has not yet been re-profiled.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, currency transaction reporting requirements "
                "and the aggregation rule, summarised in the FinCrime regulatory index.",
                _CFR_1010,
            )
        ],
        "confidence": "moderate",
        "notes": (
            "The benign explanations are the most valuable part of this record. An indicator "
            "without them is a detector with no false-positive population."
        ),
    },
    {
        "id": "IND-FAST-MOVEMENT-PASS-THROUGH",
        "title": "Funds received and disbursed with little or no economic residence in the account",
        "definition": (
            "Credits to an account followed by debits of a similar or greater amount within a "
            "short window, leaving little balance and little time for the funds to be used in "
            "the account's apparent line of business. The pattern measures the residence time "
            "and turnover of the balance; it does not establish that the funds were proceeds."
        ),
        "typology_refs": ["TYP-MULE-ACCOUNT-NETWORK", "TYP-ACCOUNT-TAKEOVER-LAUNDERING"],
        "behavioral_attributes": [
            "credit_to_debit_ratio",
            "dwell_time_of_balance",
            "balance_residual_after_drain",
            "counterparty_diversity",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the credit and debit records, each cited by its own source id and pointer",
            "the account's expected activity profile, and the account's normal balance range",
            "the payors and payees involved, including whether they recur across accounts",
        ],
        "benign_explanations": [
            "A payment processor or marketplace settlement account that receives and pays out on the same day by design.",
            "A payroll account that receives a funding transfer and disburses salaries in the same window.",
            "A professional escrow or clearing account whose stated function is to pass funds through.",
            "A commercial account used to sweep surplus funds to a treasury account at the end of each day.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, money laundering offences as summarised in the "
                "FinCrime regulatory index; the indicator is a behavioural measure, not a legal test.",
                _CORNELL_1956,
            )
        ],
        "confidence": "moderate",
        "notes": (
            "A short dwell time is only meaningful relative to the account's stated function. "
            "The function has to be established before the pattern means anything."
        ),
    },
    {
        "id": "IND-FUNNEL-ACCOUNT-AGGREGATION",
        "title": "Many third-party credits concentrated into a small number of accounts",
        "definition": (
            "A set of accounts receiving credits from a large number of distinct third-party "
            "originators, with the credits then consolidated into one or a few downstream "
            "accounts. The indicator measures the concentration of originators and the "
            "consolidation that follows; it does not identify who the originators are or what "
            "their relationship is."
        ),
        "typology_refs": ["TYP-MULE-ACCOUNT-NETWORK", "TYP-STRUCTURING-SMURFING"],
        "behavioral_attributes": [
            "distinct_originator_count",
            "credit_concentration_ratio",
            "downstream_consolidation_ratio",
            "account_age_of_originators",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the list of originators with the count of credits per originator",
            "the downstream accounts and the consolidation totals",
            "the account opening dates and the customer due diligence file for each account",
        ],
        "benign_explanations": [
            "A payment gateway account that legitimately receives credits from many merchants and pays out to a settlement account.",
            "A charitable or membership organisation collecting individual donations and remitting them to a central fund.",
            "A ride-share or delivery platform that credits drivers on the customer's behalf.",
            "An employer payroll process that credits employees' accounts and consolidates statutory deductions.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, guidance on money laundering and funnel accounts, "
                "summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "moderate",
    },
    {
        "id": "IND-ROUND-AMOUNT-DEPOSIT-CLUSTER",
        "title": "Deposits in round denominations that exceed the account's usual amounts",
        "definition": (
            "Cash or cheque deposits whose amounts are exact multiples of a round figure, "
            "clustered in time and materially larger than the amounts usually seen on the "
            "account. The indicator measures the shape of the amounts; it does not establish "
            "their source."
        ),
        "typology_refs": ["TYP-STRUCTURING-SMURFING", "TYP-ELDER-FINANCIAL-EXPLOITATION"],
        "behavioral_attributes": [
            "amount_roundness_ratio",
            "amount_deviation_from_account_baseline",
            "deposit_sequence_regularity",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the deposit records forming the cluster",
            "the account's historical amount distribution, over a stated period",
            "the source of the funds as stated by the customer, where a statement exists",
        ],
        "benign_explanations": [
            "A business that prices in round figures or invoices in round amounts.",
            "A customer paying a rent, tuition or instalment in a round amount agreed in advance.",
            "A cash-heavy retail account whose daily takings happen to settle at round figures.",
            "A bank or building society teller machine that credits the change in a round amount.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, guidance on the avoidance of reporting "
                "requirements, summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "low",
        "notes": (
            "Roundness on its own is close to meaningless; it is only useful in combination "
            "with frequency, dispersion across counterparties, and the account's baseline."
        ),
    },
    {
        "id": "IND-DORMANT-ACCOUNT-ACTIVATION-VELOCITY",
        "title": "A long-dormant account becomes active and starts transacting",
        "definition": (
            "An account with little or no activity for a long period resumes and begins to "
            "receive and send transactions, often with a change in counterparty profile. The "
            "indicator measures the change in activity; it does not explain it, and a resumption "
            "of activity is a legitimate event in itself."
        ),
        "typology_refs": ["TYP-ACCOUNT-TAKEOVER-LAUNDERING", "TYP-MULE-ACCOUNT-NETWORK"],
        "behavioral_attributes": [
            "dormancy_duration",
            "activity_resumption_velocity",
            "counterparty_profile_shift",
            "credential_change_indicator",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the account's transaction history over the dormant period and since resumption",
            "the account opening and closure records",
            "any change of credentials, contact details or authorised signers since dormancy",
        ],
        "benign_explanations": [
            "A seasonal or cyclical customer returning to an account they still maintain.",
            "A beneficiary or executor resuming use of an account after a period of inactivity.",
            "A dormant account reactivated by a new product or a system migration.",
            "A student or seasonal worker returning to the country and resuming transactions.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, customer identification and account "
                "takeover guidance, summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "low",
        "notes": (
            "Dormancy is a normal customer behaviour, and an account that reactivates after "
            "a change of address is a different account from one that reactivates with a new "
            "device and a new counterparty set."
        ),
    },
    {
        "id": "IND-GEOGRAPHIC-ATM-DISPERSION",
        "title": "Cash withdrawals dispersed across many ATMs in a wide geography",
        "definition": (
            "Cash withdrawals made from a large number of automated teller machines spread "
            "across a wide area, within a short period, at a rate above the account's usual "
            "withdrawal pattern. The indicator measures dispersion and rate; it does not "
            "establish why the money was withdrawn."
        ),
        "typology_refs": ["TYP-STRUCTURING-SMURFING", "TYP-ACCOUNT-TAKEOVER-LAUNDERING"],
        "behavioral_attributes": [
            "atm_count",
            "geographic_spread_radius",
            "withdrawal_rate_deviation",
            "withdrawal_amount_uniformity",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the withdrawal records, each cited by its own source id and pointer",
            "the terminal identifiers and their locations",
            "the account's historical withdrawal pattern, over a stated period",
        ],
        "benign_explanations": [
            "A traveller or a seasonal worker withdrawing cash in the places they visit.",
            "A business that pays out daily cash to several sites and withdraws at the nearest terminal.",
            "A customer who uses different terminals to avoid a per-terminal daily limit, as a matter of convenience.",
            "Cash-intensive work, such as market trading or event staffing, paid partly in cash.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, currency transaction reporting and "
                "aggregation guidance, summarised in the FinCrime regulatory index.",
                _CFR_1010,
            )
        ],
        "confidence": "low",
    },
    {
        "id": "IND-STRUCTURED-CASH-DEP-BRANCH-CROSS",
        "title": "Cash deposits split across branches of the same institution",
        "definition": (
            "Cash deposits made at different branches of the same institution within a short "
            "window, in amounts that would have been reportable had they been made in one "
            "transaction. The indicator measures the dispersion of deposits across a single "
            "institution's network; it does not establish that a reporting requirement was "
            "avoided, because branch dispersion has operational explanations."
        ),
        "typology_refs": ["TYP-STRUCTURING-SMURFING"],
        "behavioral_attributes": [
            "branch_dispersion_count",
            "deposit_amount_uniformity",
            "time_window_concentration",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the deposit records, each cited by its own source id and pointer",
            "the branch identifiers and the aggregation rule applied for the date",
            "the customer's stated reason for depositing at more than one branch, where recorded",
        ],
        "benign_explanations": [
            "A customer who works near one branch and lives near another.",
            "A business with several sites that deposits each site's takings at its local branch.",
            "A customer avoiding a branch queue or a daily branch limit.",
            "An automated cash-handling arrangement between a business and its branches.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, currency transaction reporting and the "
                "aggregation rule, summarised in the FinCrime regulatory index.",
                _CFR_1010,
            )
        ],
        "confidence": "moderate",
    },
    {
        "id": "IND-CRYPTO-ONRAMP-LAYERING",
        "title": "Digital-asset conversion activity layered across on-ramps and wallets",
        "definition": (
            "A sequence of conversions between fiat and digital assets across several "
            "on-ramps, wallets and counterparties, in which no single step is notable and the "
            "sequence as a whole moves value without an apparent commercial purpose. The "
            "indicator measures the layering; it does not identify the value's owner or its "
            "purpose, and much legitimate activity has the same shape."
        ),
        "typology_refs": ["TYP-SHELL-COMPANY-LAYERING"],
        "behavioral_attributes": [
            "conversion_count",
            "onramp_diversity",
            "wallet_diversity",
            "dwell_time_between_conversions",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the conversion or transaction records, each cited by its own source id and pointer",
            "the account and wallet linkage evidence relied on, and how the linkage was established",
            "the stated business purpose of the digital-asset activity, where one exists",
        ],
        "benign_explanations": [
            "A customer rebalancing a long-held position across two exchanges for custody reasons.",
            "A merchant accepting digital assets and converting them at several on-ramps to reduce processing fees.",
            "A treasury operation moving funds between an exchange and a cold wallet on a schedule.",
            "A cross-border worker converting remittances at the best available rate.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, guidance on convertible virtual currency and "
                "money services businesses, summarised in the FinCrime regulatory index.",
                _CFR_1020,
            )
        ],
        "confidence": "low",
        "notes": (
            "Linkage between a fiat account and a wallet is an analytical inference, not a fact. "
            "It has to be cited as an inference with its basis stated."
        ),
    },
    {
        "id": "IND-UNBACKED-LOAN-PAYOFF",
        "title": "A loan repaid promptly from funds the borrower cannot have earned",
        "definition": (
            "A loan or credit facility repaid within a short period, from a source of funds that "
            "does not correspond to the borrower's documented income, and often shortly after "
            "the advance. The indicator measures the repayment and its funding; it does not "
            "establish the borrower's intent."
        ),
        "typology_refs": ["TYP-SHELL-COMPANY-LAYERING", "TYP-MULE-ACCOUNT-NETWORK"],
        "behavioral_attributes": [
            "days_to_repayment",
            "repayment_source_relationship",
            "income_documentation_coverage",
            "advance_to_repayment_ratio",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the loan agreement, the disbursement record and the repayment record",
            "the borrower's documented income over the relevant period",
            "the source of the repayment funds, and the relationship between the parties",
        ],
        "benign_explanations": [
            "A business repaying a facility from a seasonal cash peak.",
            "A lender or broker repaying a facility that it had bridged on the customer's behalf.",
            "A borrower whose income is not documented because it is paid in cash or in kind.",
            "A refinance that the borrower's own cash flow supported but that was recorded in the wrong period.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, lending-related money laundering guidance, "
                "summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "moderate",
    },
    {
        "id": "IND-CASH-INTENSITY-PROFILE-MISMATCH",
        "title": "Cash activity inconsistent with the customer's stated business model",
        "definition": (
            "Cash volume on an account that is materially out of line with the cash intensity "
            "of the business the customer described at onboarding, or that changes sharply "
            "without a stated change in the business. The indicator measures the mismatch "
            "between the stated profile and the observed activity."
        ),
        "typology_refs": ["TYP-STRUCTURING-SMURFING", "TYP-TRADE-BASED-MONEY-LAUNDERING"],
        "behavioral_attributes": [
            "cash_ratio_vs_declared_profile",
            "profile_drift_over_time",
            "product_mix_mismatch",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the customer due diligence file, with the date the profile was taken and the profile itself",
            "the cash and non-cash transaction totals over the comparison period",
            "the stated industry benchmark, or the subject's own expected mix, relied on",
        ],
        "benign_explanations": [
            "A business that moved from wholesale to retail, or from card to cash, without updating its profile.",
            "A seasonal business whose cash share swings with the season and whose profile is a mid-year snapshot.",
            "A customer whose stated turnover was understated at onboarding and later corrected.",
            "A cash-intensive profession — such as cash-only retail or vending — that was profiled too narrowly.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, customer due diligence and risk "
                "assessment guidance, summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "moderate",
    },
    {
        "id": "IND-MULTI-ACCOUNT-AGGREGATION",
        "title": "Activity spread across accounts that a single person controls",
        "definition": (
            "Transaction activity that looks unremarkable account by account, but which "
            "aggregates across several accounts with a common owner, signatory or address into "
            "a materially different picture. The indicator is defined only where the common "
            "control is evidenced rather than assumed."
        ),
        "typology_refs": ["TYP-STRUCTURING-SMURFING", "TYP-SHELL-COMPANY-LAYERING"],
        "behavioral_attributes": [
            "aggregate_volume_across_linked_accounts",
            "common_control_evidence_strength",
            "cross_account_counterparty_overlap",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the evidence of common control, cited by its own source id",
            "the per-account and the aggregated transaction totals",
            "the shared attributes used to link the accounts, and each one's strength",
        ],
        "benign_explanations": [
            "A sole trader who operates several accounts for different branches of the business.",
            "A family running a small business across a personal and a corporate account.",
            "A customer who prefers several accounts for administrative reasons, such as separate funds.",
            "Accounts that share an address because they belong to a common landlord, a school or a company house.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, customer identification programme "
                "guidance, summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "moderate",
        "notes": (
            "The linkage has to be evidence-based. Shared attributes such as an address, a "
            "phone number or a device are indicators of linkage, not evidence of it."
        ),
    },
    {
        "id": "IND-CHECK-SEQUENCING-THEN-WIRE",
        "title": "A cheque deposit followed closely by an outbound wire of similar size",
        "definition": (
            "A cheque or other payable instrument deposited and followed within a short window "
            "by an outbound electronic transfer of a similar amount, where the account's "
            "ordinary activity does not involve that sequence. The indicator measures the "
            "sequence and its timing; it does not establish the purpose of either leg."
        ),
        "typology_refs": ["TYP-STRUCTURING-SMURFING", "TYP-TRADE-BASED-MONEY-LAUNDERING"],
        "behavioral_attributes": [
            "deposit_to_transfer_lag",
            "amount_similarity_ratio",
            "sequence_frequency",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the deposit record and the outbound transfer record",
            "the account's ordinary activity pattern, over a stated period",
            "the stated purpose of the outbound transfer, where a payment instruction exists",
        ],
        "benign_explanations": [
            "A business that takes a cheque for a sale and settles the supplier the same week.",
            "A customer paying a deposit on a property or a vehicle.",
            "An agent who receives a cheque and remits the proceeds, as their business model states.",
            "A payment processor settling a merchant's takings the day after the deposit.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, funds transfer and reporting guidance, "
                "summarised in the FinCrime regulatory index.",
                _CFR_1010,
            )
        ],
        "confidence": "moderate",
    },
    {
        "id": "IND-PAYROLL-TO-OUTFLOW-MISMATCH",
        "title": "Outflows disproportionate to the payroll the account is said to fund",
        "definition": (
            "Outbound payments from an account that funds payroll, materially exceeding the "
            "payroll the account is documented to pay, and not accounted for by the stated "
            "business expenses. The indicator measures the difference between the declared "
            "purpose of the account and the money that leaves it."
        ),
        "typology_refs": ["TYP-STRUCTURING-SMURFING", "TYP-ELDER-FINANCIAL-EXPLOITATION"],
        "behavioral_attributes": [
            "payroll_coverage_ratio",
            "non_payroll_outflow_share",
            "destination_diversity",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the payroll register and the corresponding payroll payments",
            "the non-payroll outbound transfers, each cited by its own source id",
            "the account's stated purpose and the customer's business description",
        ],
        "benign_explanations": [
            "A business that pays some staff in cash collected from other sources.",
            "An employer paying contractors or agencies alongside its own payroll.",
            "A seasonal employer whose payroll register lags the actual hiring.",
            "A family account that mixes a business payroll with household spending.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, guidance on the use of business accounts "
                "and payroll-related activity, summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "low",
    },
    {
        "id": "IND-TRADE-INVOICE-VALUE-ANOMALY",
        "title": "Invoiced values inconsistent with the goods or services delivered",
        "definition": (
            "Invoice values that depart materially from what comparable trade would cost — the "
            "goods over-invoiced and the payments under-invoiced, or the reverse — with no "
            "commercial reason offered. The indicator measures the divergence between the "
            "declared value and the market value of the trade."
        ),
        "typology_refs": ["TYP-TRADE-BASED-MONEY-LAUNDERING", "TYP-REAL-ESTATE-CASH-LAYERING"],
        "behavioral_attributes": [
            "invoice_to_market_value_ratio",
            "invoice_series_divergence",
            "counterparty_price_divergence",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the invoice, the contract and the payment record, each cited by its own source id",
            "the independent evidence of the market value relied on",
            "the customs or tax documentation, where the trade crossed a border",
        ],
        "benign_explanations": [
            "A long-standing relationship between related parties priced on a cost-plus basis.",
            "A market with few comparable trades, so the benchmark is weak.",
            "A genuine change in price, quantity or quality between the compared periods.",
            "Freight, insurance and tax included in one invoice and excluded from the other.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, trade-based money laundering guidance, "
                "summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "low",
        "notes": (
            "A comparison needs a comparison class. Without one, the divergence is an "
            "opinion, and the record has to say which class was used."
        ),
    },
    {
        "id": "IND-COMMON-OWNERSHIP-SHELL-CHAIN",
        "title": "A chain of entities sharing owners, addresses or directors",
        "definition": (
            "Two or more companies that transact with each other while sharing owners, "
            "directors, registered addresses or signatory details, with the pattern persisting "
            "across the relationship. The indicator measures the structural overlap; it does "
            "not establish that either entity is a front."
        ),
        "typology_refs": ["TYP-SHELL-COMPANY-LAYERING", "TYP-TRADE-BASED-MONEY-LAUNDERING"],
        "behavioral_attributes": [
            "shared_owner_count",
            "shared_address_ratio",
            "shared_signatory_count",
            "intra_group_flow_ratio",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the ownership and control evidence for each entity, cited by its own source id",
            "the invoices and payments between the entities",
            "the stated commercial relationship between the entities",
        ],
        "benign_explanations": [
            "A family group of companies that share directors and premises and trade honestly.",
            "A holding structure used for tax or risk reasons, with the trades fully documented.",
            "Two businesses that share a serviced-office address and a director by coincidence.",
            "A group that centralises functions and invoices for them at a market rate.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, guidance on shell companies and beneficial "
                "ownership, summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "moderate",
    },
    {
        "id": "IND-MULE-ONBOARDING-BURST",
        "title": "A burst of new accounts opened in a short window with a shared pattern",
        "definition": (
            "Many accounts opened within a short period, by different applicants, sharing "
            "characteristics such as a common address, a common device, a common contact "
            "number, or a common pattern of first transactions. The indicator measures the "
            "burst and the shared characteristics; it does not identify the organiser."
        ),
        "typology_refs": ["TYP-MULE-ACCOUNT-NETWORK"],
        "behavioral_attributes": [
            "account_opening_velocity",
            "shared_attribute_count",
            "first_transaction_similarity",
            "dormancy_before_activity",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the account opening records and the applications behind them",
            "the evidence for each shared characteristic, cited by its own source id",
            "the first transactions on each account",
        ],
        "benign_explanations": [
            "A marketing campaign that brought in a cohort of customers at once.",
            "A students' union or a sports club registering members in batches.",
            "A payroll migration that moved staff onto a new platform.",
            "An employer onboarding seasonal workers at the start of a season.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, customer identification programme "
                "guidance, summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "moderate",
    },
    {
        "id": "IND-THIRD-PARTY-TRANSFER-CHAIN",
        "title": "Funds sent onward to third parties the account holder does not transact with",
        "definition": (
            "Credits received from one party and debited onward to unrelated third parties, "
            "without the account holder appearing to have a commercial relationship with the "
            "recipients. The indicator measures the absence of a stated relationship; it does "
            "not establish that the funds were held for others."
        ),
        "typology_refs": ["TYP-MULE-ACCOUNT-NETWORK", "TYP-ACCOUNT-TAKEOVER-LAUNDERING"],
        "behavioral_attributes": [
            "non_related_party_outflow_ratio",
            "outflow_granularity",
            "recipient_diversity",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the inbound and outbound transaction records",
            "any statement of the account holder's role in the movement of the funds",
            "the customer due diligence file and the declared purpose of the account",
        ],
        "benign_explanations": [
            "A market stall holder who receives cash from traders and pays suppliers.",
            "A concierge or a payment service that passes funds to end customers.",
            "A customer who manages money for relatives and is candid about it.",
            "A business holding funds briefly before a refund, with the refunds visible in the same account.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, guidance on third-party payment "
                "processing, summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "moderate",
    },
    {
        "id": "IND-ELDER-CREDENTIAL-CHANGE-TRANSFER",
        "title": "A change in account credentials followed by an unusual outbound transfer",
        "definition": (
            "An account whose contact details, credentials or authorised signers change, "
            "immediately followed by an outbound transfer that departs from the account's "
            "established pattern. The indicator measures the sequence; it does not establish "
            "who made the change or whether the customer is being targeted."
        ),
        "typology_refs": ["TYP-ELDER-FINANCIAL-EXPLOITATION", "TYP-ACCOUNT-TAKEOVER-LAUNDERING"],
        "behavioral_attributes": [
            "credential_change_to_transfer_lag",
            "transfer_amount_vs_baseline",
            "recipient_newness",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the credential change record, with its timestamp and channel",
            "the outbound transfer record",
            "the account's historical transfer pattern, over a stated period",
        ],
        "benign_explanations": [
            "A customer who has genuinely changed address or phone number.",
            "A customer who has been coerced into changing a credential by a legitimate need, such as a fraud team resetting access after a breach.",
            "A joint account holder who has been added or removed.",
            "A customer who has been bereaved and is reorganising a dormant account.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, guidance on elder financial exploitation and "
                "account takeover, summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "moderate",
        "notes": (
            "This indicator is defined over behaviour. It is not defined over the customer's "
            "age, and a pattern of this shape is not evidence of exploitation in a young "
            "customer or evidence against an old one."
        ),
    },
    {
        "id": "IND-ATO-SESSION-TRANSFER-VELOCITY",
        "title": "Transfers made soon after an account session begins in an unusual way",
        "definition": (
            "Outbound transfers made within a short window of a session that started in an "
            "unusual way — a new device, a new location, or a failed authentication followed by "
            "a successful one — and that depart from the account's usual transfer pattern. The "
            "indicator measures the conjunction of session anomaly and transfer velocity."
        ),
        "typology_refs": ["TYP-ACCOUNT-TAKEOVER-LAUNDERING"],
        "behavioral_attributes": [
            "session_to_transfer_lag",
            "device_change_indicator",
            "authentication_retry_count",
            "transfer_amount_vs_baseline",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the session and authentication logs",
            "the outbound transfer records",
            "the account's historical transfer pattern, over a stated period",
        ],
        "benign_explanations": [
            "A customer who travels and starts a session from a new device in a new country.",
            "A customer who replaced a phone and is signing in for the first time.",
            "A customer whose password expired and who reset it before a scheduled payment.",
            "A joint account holder who has not used online banking for some time.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, guidance on account takeover and "
                "fraud, summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "moderate",
    },
    {
        "id": "IND-CASH-STORE-REFUND-RATIO",
        "title": "Cash refunds that make up an unusual share of a retail business's takings",
        "definition": (
            "Cash refunds issued by a retail business that exceed what its product mix and "
            "return policy would predict, concentrated on cash transactions. The indicator "
            "measures the divergence between the refund profile and the stated return policy."
        ),
        "typology_refs": ["TYP-STRUCTURING-SMURFING"],
        "behavioral_attributes": [
            "refund_to_sales_ratio",
            "cash_refund_share",
            "refund_pattern_regularity",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the refund records, each cited by its own source id",
            "the sales records for the same period",
            "the published return policy the refund rate is compared against",
        ],
        "benign_explanations": [
            "A retailer in a sector with a genuinely high return rate, such as clothing or electrical goods.",
            "A seasonal peak in returns following a period of heavy sales.",
            "A business whose till system defaults to cash refunds for any reversal.",
            "A business that has recently tightened its returns policy, or recently loosened it.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, guidance on cash-intensive retail activity, "
                "summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "low",
    },
    {
        "id": "IND-GIFT-CARD-PURCHASE-VELOCITY",
        "title": "High-velocity purchases of stored-value instruments",
        "definition": (
            "A pattern of purchases of stored-value or prepaid instruments at a high rate, "
            "often in repeated rounded amounts and from several points of sale, with rapid "
            "subsequent use. The indicator measures the velocity and the use pattern."
        ),
        "typology_refs": ["TYP-STRUCTURING-SMURFING", "TYP-MULE-ACCOUNT-NETWORK"],
        "behavioral_attributes": [
            "purchase_velocity",
            "redemption_velocity",
            "amount_rounding_ratio",
            "point_of_sale_diversity",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the purchase records and the redemption records",
            "the merchant category codes of the points of sale",
            "the source of the funds used to buy the instruments, where known",
        ],
        "benign_explanations": [
            "A retailer that sells stored-value cards as its own product line.",
            "A consumer preparing for an event, holiday or celebration.",
            "An employer distributing incentive or welfare vouchers on a scheduled cycle.",
            "A business running a promotional discount funded by prepaid cards.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, guidance on money services businesses and "
                "prepaid access, summarised in the FinCrime regulatory index.",
                _CFR_1020,
            )
        ],
        "confidence": "low",
    },
    {
        "id": "IND-REAL-ESTATE-CASH-LAYERING",
        "title": "Property bought with layered cash funding from unrelated contributors",
        "definition": (
            "A property purchase funded in cash, or in a small deposit followed by cash "
            "payments, where the funds arrive in tranches from several contributors who have "
            "no declared connection to the buyer. The indicator measures the number and "
            "diversity of the funders and the layer in which they are paid."
        ),
        "typology_refs": ["TYP-REAL-ESTATE-CASH-LAYERING", "TYP-SHELL-COMPANY-LAYERING"],
        "behavioral_attributes": [
            "funder_count",
            "funder_relationship_diversity",
            "cash_share_of_purchase",
            "payment_layering_depth",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the purchase agreement, the funding records and the title record",
            "the source of each contribution and the relationship between the contributor and the buyer",
            "any stated explanation for the funding structure",
        ],
        "benign_explanations": [
            "A family purchase where several relatives contribute and the arrangement is documented.",
            "A property bought with a mortgage and a cash deposit from a genuine savings account.",
            "An investor who has used several lenders sequentially and has documented each.",
            "A buyer who prefers cash for a purchase where a cash offer was genuinely made.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, guidance on real estate and residential "
                "property money laundering, summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "moderate",
    },
    {
        "id": "IND-CIRCULAR-TRANSFER-CHAIN",
        "title": "Funds returning to their origin through a chain of counterparties",
        "definition": (
            "A sequence of transfers in which value leaves an account and returns to it, or to "
            "an account with a common owner, after passing through one or more unrelated "
            "counterparties. The indicator measures the return of value to the origin within a "
            "stated window."
        ),
        "typology_refs": ["TYP-SHELL-COMPANY-LAYERING", "TYP-STRUCTURING-SMURFING"],
        "behavioral_attributes": [
            "return_to_origin_ratio",
            "chain_length",
            "chain_completion_time",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the full chain of transfers, each leg cited by its own source id",
            "the ownership or control relationship between the endpoints",
            "the stated commercial reason for each leg",
        ],
        "benign_explanations": [
            "A group treasury that sweeps funds between operating accounts daily.",
            "A merchant that refunds a deposit to the original payment method.",
            "A payment processor that returns a chargeback or a settlement adjustment.",
            "A business lending money to itself through a subsidiary for a documented reason.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, money laundering offences as summarised in "
                "the FinCrime regulatory index; the indicator is a behavioural measure.",
                _CORNELL_1956,
            )
        ],
        "confidence": "moderate",
    },
    {
        "id": "IND-WIRE-SEQUENCING-NEUTHRESHOLD",
        "title": "Electronic transfers sequenced just under a reporting or review threshold",
        "definition": (
            "A series of electronic transfers, each just below an applicable reporting or "
            "internal review threshold, whose sum would have crossed it. The indicator measures "
            "the sequencing of the amounts relative to the threshold; it does not establish "
            "that the threshold was known or intended."
        ),
        "typology_refs": ["TYP-STRUCTURING-SMURFING", "TYP-TERRORIST-FINANCING-DIVERSION"],
        "behavioral_attributes": [
            "amount_to_threshold_ratio",
            "sequence_count",
            "sequence_time_window",
            "counterparty_diversity",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "each transfer in the sequence, cited by its own source id",
            "the threshold and its effective dates",
            "the account's relationship to the recipients",
        ],
        "benign_explanations": [
            "A customer who knows a per-payment limit and pays just under it for convenience.",
            "A treasury team splitting an invoice payment across two settlements to meet two different cut-off times.",
            "A wholesaler paying several suppliers each just under a contractual discount threshold.",
            "A payment that is genuinely below a statutory threshold at each leg and only in aggregate reaches it.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, funds transfer and reporting guidance, "
                "summarised in the FinCrime regulatory index.",
                _CFR_1010,
            )
        ],
        "confidence": "low",
    },
    {
        "id": "IND-REGULAR-EXCHANGE-INDEXED-PATTERN",
        "title": "A repeating pattern of activity that is regular rather than irregular",
        "definition": (
            "Activity that recurs on a fixed cycle — the same amounts, on the same days, to the "
            "same counterparties — which is the shape of a scheduled arrangement rather than a "
            "response to events. The indicator measures the regularity, which is a fact about "
            "the data, and not its purpose."
        ),
        "typology_refs": ["TYP-TRADE-BASED-MONEY-LAUNDERING", "TYP-SHELL-COMPANY-LAYERING"],
        "behavioral_attributes": [
            "periodicity_estimate",
            "amount_repeat_ratio",
            "counterparty_repeat_ratio",
            "calendar_alignment",
        ],
        "prohibited_attributes": list(PROHIBITED),
        "evidence_to_cite": [
            "the transaction series over a period long enough for the periodicity to be visible",
            "the account's stated business model, and the schedule it implies",
            "the counterparty relationships relied on",
        ],
        "benign_explanations": [
            "A payroll or a standing order that runs on a fixed date every month.",
            "A retailer that settles with a supplier on a fixed weekly cycle.",
            "A customer paying a family member a fixed amount on a fixed date.",
            "A subscription service whose charges recur on a billing cycle.",
        ],
        "sources": [
            _src(
                "Financial Crimes Enforcement Network, guidance on trade-based money laundering "
                "and periodic transfer patterns, summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "low",
        "notes": (
            "Regularity is not suspiciousness. Most honest commerce is regular, and the "
            "indicator only carries weight where the regularity is unexplained by the stated "
            "business model."
        ),
    },
]
