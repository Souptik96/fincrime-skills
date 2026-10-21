"""The request-catalogue content of the ``core-2026-10`` pack.

A request-catalogue entry is a *standard document request*: what to ask for,
why it is being asked, and what the answer has to establish. Each entry
carries the evidence the response is expected to bear on, because a document
that arrives without a stated purpose produces a pile of paperwork rather
than a finding.

The requests are the "evidence-request" skill's raw material. They are
ordinary, well-understood information requests; what makes them hard is
deciding which one to make, and being able to say what each one would and
would not establish.
"""

from __future__ import annotations

from typing import Any

_FINCEN = "https://www.fincen.gov/resources/statutes-regulations/guidance"
_CFR_1010 = "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010"
_CFR_1020 = "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1020"
_CORNELL_5318 = "https://www.law.cornell.edu/uscode/text/31/5318"
_OFAC = "https://ofac.treasury.gov/"


def _src(citation: str, url: str) -> dict[str, str]:
    return {"citation": citation, "url": url, "retrieved": "2026-10-01"}


REQUESTS: list[dict[str, Any]] = [
    {
        "id": "REQ-POS-SETTLEMENT-BATCH",
        "title": "Point-of-sale settlement batches",
        "definition": (
            "The batch-level settlement file a merchant's acquirer or processor settles on, "
            "showing the individual card transactions and the net amount remitted. It is "
            "requested when a cash-heavy merchant's card volume is being compared with the "
            "rest of its takings, and it establishes the card side of the picture, not the "
            "cash side."
        ),
        "evidence_to_cite": [
            "the settlement batch, with the settlement date and the net amount",
            "the individual transactions in the batch, cited by their own transaction ids",
            "the acquirer's or processor's identification of the merchant account",
        ],
        "sources": [
            _src(
                "Card settlement data is requested to test a cash-intensity profile; the "
                "reporting and recordkeeping context is summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REQ-SOURCE-OF-WEALTH",
        "title": "Source of wealth statement",
        "definition": (
            "A signed statement from the customer describing how their wealth was "
            "accumulated, supported by the underlying documentation. It is requested where "
            "the balance is high relative to the documented income, and it establishes a "
            "stated explanation, which is a hypothesis and not a verified fact until the "
            "supporting documents are in."
        ),
        "evidence_to_cite": [
            "the signed statement, with its date and the person who signed it",
            "the supporting documents relied on, each cited by its own source id",
            "the stated period over which the wealth was accumulated",
        ],
        "sources": [
            _src(
                "Customer due diligence and source-of-wealth expectations, summarised in the "
                "FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REQ-AUDITED-FINANCIAL-STATEMENTS",
        "title": "Audited financial statements",
        "definition": (
            "The audited accounts of a company for the relevant financial years, with the "
            "auditor's opinion. They are requested where the transaction volume being "
            "assessed has to be placed against the entity's declared turnover, and they "
            "establish a figure that has been independently examined rather than a figure the "
            "customer asserted."
        ),
        "evidence_to_cite": [
            "the audited accounts, the financial years they cover and the audit opinion",
            "the turnover figure, and the note in which it is disclosed",
            "the auditor's identity and the date of the opinion",
        ],
        "sources": [
            _src(
                "Financial information supporting customer due diligence and risk assessment, "
                "summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REQ-UBO-REGISTRY-PROOF",
        "title": "Beneficial ownership registry extract",
        "definition": (
            "The extract of the official beneficial-ownership register showing the persons "
            "who own or control a legal entity customer, obtained from the register itself "
            "rather than from the customer. It is requested where the customer's own account "
            "of its ownership is in question, and it establishes what the register says, "
            "which is a different claim from what the customer said."
        ),
        "evidence_to_cite": [
            "the register extract, with the date of retrieval and the register version",
            "the ownership and control entries for the entity",
            "any difference between the extract and the customer's own account",
        ],
        "sources": [
            _src(
                "Beneficial ownership identification requirements, summarised in the FinCrime "
                "regulatory index.",
                _CFR_1010,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REQ-UBO-CHART-SIGNED-DECLARATION",
        "title": "Ownership chart and signed control declaration",
        "definition": (
            "The customer's own ownership chart, together with a signed declaration "
            "identifying the natural persons who own or control the entity and the basis of "
            "their control. It is requested alongside, or in place of, a register extract, and "
            "it establishes what the customer asserts, which is only as good as the "
            "declaration's evidential basis."
        ),
        "evidence_to_cite": [
            "the ownership chart, with the date it was produced",
            "the signed declaration, and the identity of the signatory and their authority",
            "the basis of control asserted for each owner",
        ],
        "sources": [
            _src(
                "Beneficial ownership identification and certification requirements, summarised "
                "in the FinCrime regulatory index.",
                _CFR_1010,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REQ-COMMERCIAL-CONTRACTS",
        "title": "Underlying commercial contracts",
        "definition": (
            "The contracts, purchase orders and delivery terms that explain why the subject "
            "transacted with the counterparty in question, at the price in question. It is "
            "requested wherever an invoice value has to be compared with a market value, and "
            "it establishes the commercial rationale, which is what distinguishes a benign "
            "price from an unexplained one."
        ),
        "evidence_to_cite": [
            "the contract, with its date, the parties and the price terms",
            "the purchase orders or delivery notes that evidence performance",
            "any amendment to the contract between the stated parties",
        ],
        "sources": [
            _src(
                "Trade-based activity is assessed against the underlying commercial "
                "relationship, summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REQ-BILL-OF-LADING",
        "title": "Bills of lading",
        "definition": (
            "The transport documents for a shipment, showing what was shipped, the quantity, "
            "the route and the parties. They are requested where the declared value of a "
            "trade has to be tested against what physically moved, and they establish "
            "existence and movement of goods, which a set of invoices does not."
        ),
        "evidence_to_cite": [
            "the bill of lading, with the carrier, the vessel or vehicle and the ports",
            "the quantity and description of the goods, against the invoiced quantity",
            "the shipper and the notify party, against the parties on the invoice",
        ],
        "sources": [
            _src(
                "Shipping and customs documentation supporting the assessment of trade-based "
                "activity, summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REQ-CARGO-INSURANCE-POLICY",
        "title": "Cargo insurance policies",
        "definition": (
            "The insurance policy covering a shipment, showing the insured value and the "
            "insurer. It is requested where the insured value of goods is being compared with "
            "the invoiced value, because a policy is priced against the value of the goods "
            "and is a more independent figure than an invoice."
        ),
        "evidence_to_cite": [
            "the policy, with the insurer, the policy number and the period of cover",
            "the insured value, and the basis on which it was set",
            "the parties to the policy, against the parties to the trade",
        ],
        "sources": [
            _src(
                "Insurance documentation as an independent reference for the value of goods, "
                "summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "moderate",
    },
    {
        "id": "REQ-COUNTERPARTY-BANK-STATEMENTS",
        "title": "Counterparty account statements",
        "definition": (
            "The account statements of a counterparty, obtained with the counterparty's "
            "authority or through a lawful request, covering the period of the transactions "
            "in question. They are requested where the subject's own records show a payment "
            "but do not show what became of it, and they establish the funds' onward "
            "movement, or its absence."
        ),
        "evidence_to_cite": [
            "the statements, with the account holder and the period covered",
            "the transactions in question, cited by their own source id",
            "the authority under which the statements were obtained",
        ],
        "sources": [
            _src(
                "Information sharing with financial institutions, summarised in the FinCrime "
                "regulatory index.",
                _CORNELL_5318,
            )
        ],
        "confidence": "moderate",
        "notes": (
            "The means of obtaining the statements is a legal question, not an analytical "
            "one, and it belongs in the request's provenance rather than in its rationale."
        ),
    },
    {
        "id": "REQ-CUSTOM-DUTY-CLEARANCE",
        "title": "Customs clearance records",
        "definition": (
            "The entry, declaration and clearance documentation for goods entering or "
            "leaving the country, showing the declared description, value, quantity and "
            "origin. They are requested where the value of a trade has to be tested against "
            "the value declared to a customs authority, which is a comparison the customer "
            "does not control."
        ),
        "evidence_to_cite": [
            "the entry and declaration, with the entry number and date",
            "the declared value, description and quantity, against the commercial documents",
            "the ports of entry and exit, against the shipping documents",
        ],
        "sources": [
            _src(
                "Customs documentation in the assessment of trade-based activity, summarised "
                "in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REQ-INVOICE-LEDGER",
        "title": "Sales and purchase invoice ledgers",
        "definition": (
            "The complete invoice ledger for a period, showing every invoice raised or "
            "received, the counterparty, the amount and the date. It is requested where a "
            "sample of transactions has to be tested against the whole population, and it "
            "establishes whether the sampled pattern is the norm or the exception."
        ),
        "evidence_to_cite": [
            "the ledger, with the period it covers and the system it was taken from",
            "the reconciliation of the ledger total to the reported turnover",
            "the sampling method, where a sample was drawn",
        ],
        "sources": [
            _src(
                "Transaction records supporting a pattern assessment, summarised in the FinCrime "
                "regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REQ-PAYROLL-REGISTER",
        "title": "Payroll registers",
        "definition": (
            "The payroll register for the relevant periods, listing the employees, their "
            "status and the amounts paid. It is requested where the outbound payments from "
            "an account are being compared against the workforce the account is said to fund, "
            "and it establishes the scale of the declared activity."
        ),
        "evidence_to_cite": [
            "the register, with the pay periods it covers",
            "the headcount and the total payroll for each period",
            "any discrepancy with the payroll payments in the account",
        ],
        "sources": [
            _src(
                "Payroll records supporting a comparison of declared and observed activity, "
                "summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REQ-BANK-STATEMENTS-12M",
        "title": "Account statements for a twelve-month period",
        "definition": (
            "The statements of the subject account for a full year, so that a pattern can be "
            "separated from an episode. It is requested wherever a single transaction or a "
            "single month would be a weak basis, and it establishes the baseline against "
            "which any deviation is measured."
        ),
        "evidence_to_cite": [
            "the statements, with the account identifiers and the full period",
            "the completeness of the period, and any gaps in the record",
            "the baseline pattern derived, and the method used to derive it",
        ],
        "sources": [
            _src(
                "Account records used to establish a baseline, summarised in the FinCrime "
                "regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REQ-ATM-TRANSACTION-LOG",
        "title": "Automated teller machine transaction logs",
        "definition": (
            "The terminal-level log of cash withdrawals and deposits, showing the terminal, "
            "the location, the time and the amount. It is requested where a dispersion "
            "pattern is being assessed, and it establishes the physical dispersion of cash "
            "movements, which a summary of the account cannot show."
        ),
        "evidence_to_cite": [
            "the terminal logs, with the terminals covered and the period",
            "the terminal location reference used, and how it was resolved",
            "the linkage between the terminal and the account",
        ],
        "sources": [
            _src(
                "Terminal-level records used in the assessment of cash activity, summarised in "
                "the FinCrime regulatory index.",
                _CFR_1010,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REQ-CARD-ACQUIRING-SETTLEMENT",
        "title": "Acquiring and settlement records",
        "definition": (
            "The acquiring bank's records of the card transactions acquired for a merchant, "
            "with the settlement totals and the fees. They are requested where the merchant's "
            "cash intensity is being assessed and the card side of the business is not "
            "visible in the account, and they establish the scale of the card business."
        ),
        "evidence_to_cite": [
            "the acquiring records, with the merchant identifier and the period",
            "the gross and net settlement totals, and the fees applied",
            "the reconciliation to the amounts credited to the account",
        ],
        "sources": [
            _src(
                "Acquiring and settlement records supporting a cash-intensity assessment, "
                "summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "moderate",
    },
    {
        "id": "REQ-CRYPTO-EXCHANGE-KYC",
        "title": "Digital-asset service provider due diligence file",
        "definition": (
            "The customer identification and due diligence file a digital-asset service "
            "provider holds on the customer, together with the screening results and the "
            "source-of-funds record. It is requested where digital-asset activity is part of "
            "the picture, and it establishes what the provider actually verified, which is "
            "usually the only verification that exists."
        ),
        "evidence_to_cite": [
            "the due diligence file, with the date the relationship began",
            "the identity verification performed and its outcome",
            "the screening results, with the list versions and the dates screened",
        ],
        "sources": [
            _src(
                "Money services business customer identification requirements, summarised in "
                "the FinCrime regulatory index.",
                _CFR_1020,
            )
        ],
        "confidence": "moderate",
    },
    {
        "id": "REQ-CRYPTO-WALLET-CHAIN-ANALYSIS",
        "title": "Wallet and on-chain linkage records",
        "definition": (
            "The records linking a fiat account to a digital-asset wallet, and the "
            "transaction history of that wallet. It is requested where the movement of value "
            "has to be followed past the fiat boundary, and it establishes an analytical "
            "inference, which has to be stated as an inference with its basis."
        ),
        "evidence_to_cite": [
            "the linkage evidence, with its type and its strength",
            "the wallet transaction history over the stated period",
            "the counterparty addresses and any attribution applied to them",
        ],
        "sources": [
            _src(
                "Convertible virtual currency guidance, summarised in the FinCrime regulatory "
                "index.",
                _CFR_1020,
            )
        ],
        "confidence": "low",
        "notes": (
            "A wallet attribution is an inference with a stated basis, never an established "
            "fact. The distinction belongs in the finding, not only in the working notes."
        ),
    },
    {
        "id": "REQ-CUSTODY-AGREEMENT",
        "title": "Custody and safekeeping agreements",
        "definition": (
            "The agreement under which a third party holds assets on the customer's behalf, "
            "with the schedule of what is held. It is requested where the source of wealth "
            "depends on the value of assets that the customer does not hold directly, and it "
            "establishes what is held, by whom, and on what terms."
        ),
        "evidence_to_cite": [
            "the agreement, with its date and the parties",
            "the schedule of assets held, and the most recent valuation date",
            "the terms on which the assets may be dealt with",
        ],
        "sources": [
            _src(
                "Ownership and control evidence for source-of-wealth assessment, summarised in "
                "the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "moderate",
    },
    {
        "id": "REQ-PROPERTY-PURCHASE-AGREEMENT",
        "title": "Property purchase agreements",
        "definition": (
            "The signed contract for a property purchase, showing the price, the buyer, the "
            "seller, the deposit and the completion conditions. It is requested where a "
            "property transaction is part of the picture, and it establishes the price "
            "actually agreed and the identity of the parties to it."
        ),
        "evidence_to_cite": [
            "the agreement, with its date and the parties",
            "the price and the deposit structure",
            "the completion date and the conditions attached to it",
        ],
        "sources": [
            _src(
                "Real estate transaction records supporting an assessment of value and "
                "funding, summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REQ-PROPERTY-TITLE-RECORD",
        "title": "Property title records",
        "definition": (
            "The register of title for the property, showing the registered proprietor, the "
            "charges registered and the dates of transfer. It is requested because the "
            "registered proprietor is a different question from the person who paid, and it "
            "establishes the ownership and encumbrance position independently of the parties."
        ),
        "evidence_to_cite": [
            "the register of title, with the date of retrieval",
            "the registered proprietor and the dates of transfer",
            "the registered charges, and the amounts secured",
        ],
        "sources": [
            _src(
                "Independent ownership evidence for real estate assessment, summarised in the "
                "FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REQ-MORTGAGE-APPLICATION",
        "title": "Mortgage application files",
        "definition": (
            "The lender's application file for a mortgage or facility: the applicant's stated "
            "income, assets, liabilities and the property offered as security. It is requested "
            "where a property purchase was funded by borrowing, and it establishes what the "
            "borrower told a third party at the time, which is a different claim from what "
            "they told the institution."
        ),
        "evidence_to_cite": [
            "the application, with the date and the lender",
            "the income, asset and liability declarations, and the supporting documents",
            "the amount advanced and the terms",
        ],
        "sources": [
            _src(
                "Lending records used in the assessment of property funding, summarised in the "
                "FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REQ-LODGING-TAX-RETURNS",
        "title": "Business and personal tax returns",
        "definition": (
            "The filed tax returns for a business or an individual, for the relevant years. "
            "They are requested where the declared income has to be compared with the money "
            "that moved, and they establish the income as it was reported to a tax authority, "
            "which is independent of the customer's own account."
        ),
        "evidence_to_cite": [
            "the returns, with the years they cover and the filing dates",
            "the reported income and the reported assets",
            "any reconciliation between the return and the account activity",
        ],
        "sources": [
            _src(
                "Independent income evidence for customer due diligence, summarised in the "
                "FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REQ-EMPLOYMENT-CONTRACT",
        "title": "Employment contracts",
        "definition": (
            "The contract of employment between the customer and a third party, showing the "
            "role, the remuneration and the term. It is requested where a stated source of "
            "income depends on a role that the customer has not otherwise evidenced, and it "
            "establishes the relationship and its terms."
        ),
        "evidence_to_cite": [
            "the contract, with its date and the parties",
            "the remuneration terms and the commencement date",
            "any variation or termination agreement",
        ],
        "sources": [
            _src(
                "Evidence of a stated source of income, summarised in the FinCrime regulatory "
                "index.",
                _FINCEN,
            )
        ],
        "confidence": "moderate",
    },
    {
        "id": "REQ-VENDOR-INVOICES",
        "title": "Vendor invoices and remittance records",
        "definition": (
            "The invoices raised by a vendor and the corresponding remittance records, "
            "showing what was billed, what was paid and when. They are requested where a "
            "supplier's invoices are being tested against the goods or services actually "
            "delivered, and they establish the billing relationship independently of the payer."
        ),
        "evidence_to_cite": [
            "the invoices, with the vendor and the period",
            "the remittance records, cited by their own source id",
            "the reconciliation between invoiced and paid amounts",
        ],
        "sources": [
            _src(
                "Third-party billing records used in the assessment of trade, summarised in the "
                "FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "moderate",
    },
    {
        "id": "REQ-SHAREHOLDER-REGISTER",
        "title": "Shareholder registers",
        "definition": (
            "The statutory register of members of a company, showing who holds the shares and "
            "since when. It is requested where the ownership of a company customer is in "
            "question, and it establishes the shareholders of record, which is not the same "
            "thing as the beneficial owners."
        ),
        "evidence_to_cite": [
            "the register, with the date of extraction",
            "the shareholders and their holdings, and the dates of acquisition",
            "any transfers during the period, and the consideration recorded",
        ],
        "sources": [
            _src(
                "Ownership evidence for legal entity customers, summarised in the FinCrime "
                "regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REQ-CORPORATE-REGISTRY-EXTRACT",
        "title": "Company registry extract and good standing",
        "definition": (
            "The official register entry for a company, showing its incorporation, its "
            "registered office, its directors and whether it is in good standing, together "
            "with the filings it has made. It is requested where a company customer is being "
            "assessed, and it establishes what the register says about the entity's existence "
            "and status independently of the entity's own account of itself."
        ),
        "evidence_to_cite": [
            "the register extract, with the date of retrieval and the register version",
            "the incorporation details, the registered office and the current directors",
            "the filing history, including any recent change of officers or address",
        ],
        "sources": [
            _src(
                "Entity verification against an official register, summarised in the FinCrime "
                "regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "high",
        "notes": (
            "A company that is not in good standing, or whose registered office is a "
            "serviced address, is a fact about the entity. Neither is a finding about the "
            "people behind it."
        ),
    },
    {
        "id": "REQ-CAPITALIZATION-TABLE",
        "title": "Capitalisation tables",
        "definition": (
            "The company's own record of its owners and the percentages they hold, including "
            "any classes of share with different rights. It is requested alongside a "
            "shareholder register, and it establishes the distribution of ownership and of "
            "control rights, which the register alone does not show."
        ),
        "evidence_to_cite": [
            "the capitalisation table, with the date it was produced",
            "the share classes and the rights attached to each",
            "any inconsistency with the shareholder register",
        ],
        "sources": [
            _src(
                "Ownership and control evidence, summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REQ-SANCTIONS-SCREENING-CONFIRMATION",
        "title": "Sanctions screening records",
        "definition": (
            "The screening results for the customer, the counterparty and the payment, with "
            "the list versions used and the dates the screens were run. It is requested "
            "wherever a transaction involves a party in a higher-risk jurisdiction, and it "
            "establishes what was checked, against which list, and when — which is what "
            "decides whether the check was adequate."
        ),
        "evidence_to_cite": [
            "the screening results, with the list versions and the screening date",
            "any hit, and the disposition of the hit, with the basis",
            "the re-screening date, where the lists have changed since",
        ],
        "sources": [
            _src(
                "Sanctions compliance and reporting obligations, summarised in the FinCrime "
                "regulatory index.",
                _OFAC,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REQ-LETTER-OF-CREDIT",
        "title": "Letters of credit and documentary credits",
        "definition": (
            "The documents for a documentary credit, showing the parties, the amount, the "
            "documents the credit is to be issued against and the terms of the credit. They "
            "are requested where a trade has been financed, and they establish the terms the "
            "parties agreed independently of the invoice."
        ),
        "evidence_to_cite": [
            "the credit, with the issuing and advising banks and the amount",
            "the documents required and those presented",
            "the discrepancies raised, and their disposition",
        ],
        "sources": [
            _src(
                "Trade finance documentation in the assessment of trade-based activity, "
                "summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "moderate",
    },
    {
        "id": "REQ-INSURANCE-POLICY-CASH-VALUE",
        "title": "Insurance policies and their cash value",
        "definition": (
            "The policies held by a customer together with their current cash or surrender "
            "value. They are requested where a customer has said that wealth is held in a "
            "policy, and they establish the value of that holding as an independent party "
            "values it, rather than as the customer describes it."
        ),
        "evidence_to_cite": [
            "the policies, with the insurer and the policy number",
            "the current cash or surrender value, and its valuation date",
            "any loans taken against the policy",
        ],
        "sources": [
            _src(
                "Source-of-wealth evidence, summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "moderate",
    },
]
