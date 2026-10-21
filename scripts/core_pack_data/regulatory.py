"""The US regulatory content of the ``core-2026-10`` pack.

Every definition here is **derived and paraphrased**. None of them reproduces
regulatory text, and none of them is legal advice: they state, in summary,
what an obligation requires and where the obligation comes from, so that a
skill can point a reader at the primary source.

Two things follow from that rule, and both are load-bearing:

* a paraphrase does not go stale the way a quotation does — an amendment
  changes the summary, not the summary's words;
* a paraphrase is not a substitute for the source, which is why every record
  carries the citation and the URL and is dated.

The `as_of` date on each record is the date the summary was last checked
against the source, not the date the source was published.
"""

from __future__ import annotations

from typing import Any

_FINCEN = "https://www.fincen.gov/resources/statutes-regulations/guidance"
_CFR_1010 = "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1010"
_CFR_1020 = "https://www.ecfr.gov/current/title-31/subtitle-B/chapter-X/part-1020"
_CORNELL_1956 = "https://www.law.cornell.edu/uscode/text/18/1956"
_CORNELL_1957 = "https://www.law.cornell.edu/uscode/text/18/1957"
_CORNELL_5318 = "https://www.law.cornell.edu/uscode/text/31/5318"
_OFAC = "https://ofac.treasury.gov/"


def _src(citation: str, url: str) -> dict[str, str]:
    return {"citation": citation, "url": url, "retrieved": "2026-10-01"}


REGULATORY: list[dict[str, Any]] = [
    {
        "id": "REG-BSA-AML-PROGRAM",
        "title": "Anti-money-laundering programme obligations for covered financial institutions",
        "definition": (
            "The obligation on a covered financial institution to maintain a written, "
            "board-approved anti-money-laundering programme that is appropriate to the size "
            "and complexity of the institution. The programme is expected to contain a risk "
            "assessment, effective internal controls, a designated compliance officer, "
            "training, and independent testing, and to be revised when the institution's "
            "risks change. This record summarises the requirement; it is not the text of the "
            "rule."
        ),
        "evidence_to_cite": [
            "the institution's written anti-money-laundering programme and its approval date",
            "the risk assessment the programme rests on, and its most recent review",
            "the testing or independent review that the programme has been through",
        ],
        "sources": [
            _src(
                "Anti-money-laundering programme requirements for banks (31 CFR 1020.210) and for "
                "money services businesses (31 CFR 1020.220), summarised in the FinCrime "
                "regulatory index.",
                _CFR_1020,
            )
        ],
        "confidence": "high",
        "notes": (
            "A programme that exists but has not been revised since the institution's business "
            "or risk changed does not satisfy the requirement in substance."
        ),
    },
    {
        "id": "REG-CTR-1010-311",
        "title": "Currency transaction reporting",
        "definition": (
            "The requirement to file a report on currency transactions exceeding the "
            "applicable threshold, in cash or in monetary instruments, conducted by one person "
            "in one business day. Transactions by a person are aggregated across branches, "
            "accounts and automated teller machines for the day, and a report covers the whole "
            "of the person's activity rather than each individual transaction. A set of "
            "exceptions exists for transactions between financial institutions, and for "
            "certain listed businesses. This record summarises the obligation."
        ),
        "evidence_to_cite": [
            "the filed report, its identifier and the period it covers",
            "the aggregated transaction records for the person for the business day",
            "the aggregation applied, and any exception relied on",
        ],
        "sources": [
            _src(
                "Currency transaction reporting requirements and the aggregation rule "
                "(31 CFR 1010.311, 1010.313 and 1020.315), summarised in the FinCrime "
                "regulatory index.",
                _CFR_1010,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REG-SAR-1020-320",
        "title": "Suspicious activity reporting",
        "definition": (
            "The requirement to file a report on transactions conducted, or attempted, that "
            "are suspicious by the institution's judgement, subject to a stated reporting "
            "threshold. For covered institutions the threshold is set by reference to the "
            "amount involved and to whether the transaction has an apparent lawful purpose, and "
            "a continuing-activity rule requires a further report while the activity "
            "continues. This record summarises the obligation; the thresholds and the "
            "applicable rules are set out in the source."
        ),
        "evidence_to_cite": [
            "the filed report, its identifier and the period it covers",
            "the transaction records the report was based on",
            "the basis for the suspicion, as recorded at the time",
        ],
        "sources": [
            _src(
                "Suspicious activity reporting requirements for banks (31 CFR 1020.320), "
                "summarised in the FinCrime regulatory index.",
                _CFR_1020,
            )
        ],
        "confidence": "high",
        "notes": (
            "The decision to report is a judgement the institution makes and documents, not a "
            "computation. The record of that judgement is what has to be evidenced."
        ),
    },
    {
        "id": "REG-SAR-FILING-DEADLINE",
        "title": "Filing deadlines for suspicious activity reports",
        "definition": (
            "The rule that a suspicious activity report is filed within a set number of "
            "calendar days from the initial detection of the activity that gave rise to the "
            "suspicion, with a shorter period where no earlier report has been filed for the "
            "subject, and an extension available only where the delay is explained by "
            "circumstances outside the institution's control. A continuing-activity report is "
            "due on its own cycle while the activity continues. The periods themselves are "
            "stated in the source and change; this record summarises the structure."
        ),
        "evidence_to_cite": [
            "the initial detection date, and how it was established",
            "the filing date of the report, and any justification for a delay",
            "the basis for the continued-activity cycle used, where one applies",
        ],
        "sources": [
            _src(
                "Suspicious activity reporting filing deadlines, including the continuing-activity "
                "rule (31 CFR 1020.320), summarised in the FinCrime regulatory index.",
                _CFR_1020,
            )
        ],
        "confidence": "high",
        "notes": (
            "The deadline runs from detection, not from the transaction. A record of the "
            "detection date is the single most important thing to keep."
        ),
    },
    {
        "id": "REG-CDD-1010-230",
        "title": "Customer due diligence and risk-based procedures",
        "definition": (
            "The requirement to establish and verify a customer's identity, to understand the "
            "nature and purpose of the relationship, to develop a risk profile, and to apply "
            "enhanced procedures where the profile warrants them. The obligation is risk-based: "
            "the depth of the procedures follows the risk, and the institution is expected to "
            "revisit the profile when circumstances change rather than at a fixed interval. "
            "This record summarises the requirement."
        ),
        "evidence_to_cite": [
            "the customer due diligence file and the date each element was collected",
            "the risk rating assigned and the basis for it",
            "the enhanced procedures applied, and the trigger that required them",
        ],
        "sources": [
            _src(
                "Customer due diligence requirements for banks (31 CFR 1020.210 and 1020.220) and "
                "the customer due diligence rule (31 CFR 1010.230), summarised in the FinCrime "
                "regulatory index.",
                _CFR_1010,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REG-BENEFICIAL-OWNERSHIP-RULE",
        "title": "Beneficial ownership identification and reporting",
        "definition": (
            "The requirement, for a covered financial institution, to identify and verify the "
            "natural persons who ultimately own or control a legal entity customer, to the "
            "threshold stated in the rule, and to obtain and maintain a certification from the "
            "customer. A customer that has certified the information for a previous "
            "verification is not required to collect it again, and a customer with more owners "
            "than the rule permits may be exempted from certification. This record summarises "
            "the requirement."
        ),
        "evidence_to_cite": [
            "the ownership and control evidence for the entity customer",
            "the certification obtained, with its date",
            "any reliance on a previous certification, and the basis for it",
        ],
        "sources": [
            _src(
                "Beneficial ownership identification and certification requirements "
                "(31 CFR 1010.230), summarised in the FinCrime regulatory index.",
                _CFR_1010,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REG-CIP-1010-220",
        "title": "Customer identification programme",
        "definition": (
            "The requirement to maintain a written programme for identifying and verifying "
            "the identity of a customer, and the person acting on the customer's behalf, before "
            "the account is opened. The programme must state the identifying information that "
            "will be collected, the documents that will be accepted, how the information will "
            "be compared, and the records that will be kept, and it must provide for "
            "non-discrimination in its application. This record summarises the requirement."
        ),
        "evidence_to_cite": [
            "the institution's customer identification programme, and its approval date",
            "the identifying information collected for the customer in question",
            "the documents relied on and the comparison performed",
        ],
        "sources": [
            _src(
                "Customer identification programme requirements (31 CFR 1020.220 and 1010.230), "
                "summarised in the FinCrime regulatory index.",
                _FINCEN,
            )
        ],
        "confidence": "high",
        "notes": (
            "The non-discrimination requirement is part of the rule, not an addition to it: a "
            "programme that cannot be applied to every customer is not a compliant programme."
        ),
    },
    {
        "id": "REG-TRAVEL-RULE-1010-410E",
        "title": "Information accompanying funds transfers",
        "definition": (
            "The requirement that specified information travel with a funds transfer: for a "
            "payment in currency or monetary instruments, the originator's name, account number "
            "and address, or the identifying information the rule prescribes where a payment "
            "is made through an intermediary. The receiving institution is expected to have the "
            "information and to be able to produce it, and the information travels with the "
            "funds rather than being supplied separately. This record summarises the "
            "requirement."
        ),
        "evidence_to_cite": [
            "the payment or wire message, and the information it carried",
            "the receiving institution's response to a request for the information",
            "the procedure applied where the information was incomplete or absent",
        ],
        "sources": [
            _src(
                "Funds transfer information requirements (31 CFR 1010.410), summarised in the "
                "FinCrime regulatory index.",
                _CFR_1010,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REG-TRANSFER-1010-410F",
        "title": "Currency transfers and the reporting that follows them",
        "definition": (
            "The requirement to report a currency transfer, by a financial institution or a "
            "money services business, of currency or monetary instruments exceeding the "
            "applicable threshold, whether or not the funds physically travel in reportable "
            "form, and the requirement to collect the information the transfer rule prescribes "
            "from the person making the transfer. This record summarises the obligation."
        ),
        "evidence_to_cite": [
            "the transfer records, and whether the funds travelled in reportable form",
            "the information collected from the person making the transfer",
            "the report filed, where one was required",
        ],
        "sources": [
            _src(
                "Currency transfer reporting and information requirements (31 CFR 1010.410), "
                "summarised in the FinCrime regulatory index.",
                _CFR_1010,
            )
        ],
        "confidence": "moderate",
        "notes": (
            "Whether a report is required turns on the form of the funds, which is why the "
            "record has to say what physically travelled and not only what was booked."
        ),
    },
    {
        "id": "REG-STRUCTURING-1010-100",
        "title": "Prohibition on avoiding a reporting requirement",
        "definition": (
            "The prohibition on breaking up or structuring a transaction, or a series of "
            "transactions, so as to avoid a reporting or recordkeeping requirement that would "
            "have applied to the transaction as a whole. The prohibition applies to the "
            "purpose, so the pattern of conduct and the surrounding facts matter, and not only "
            "the amounts. Conduct by a person associated with a financial institution, but not "
            "by the institution itself, is covered by a separate provision. This record "
            "summarises the prohibition."
        ),
        "evidence_to_cite": [
            "the individual transactions, each cited by its own source id",
            "the reportable transaction they would have formed, if it had been made in one",
            "the facts relied on to establish purpose, and their source",
        ],
        "sources": [
            _src(
                "Definitions governing the avoidance of reporting requirements (31 CFR 1010.100), "
                "summarised in the FinCrime regulatory index.",
                _CFR_1010,
            )
        ],
        "confidence": "high",
        "notes": (
            "The prohibition is about purpose, which is why a pattern of small transactions "
            "is not by itself a violation, and why the surrounding facts have to be evidenced."
        ),
    },
    {
        "id": "REG-RECORD-RETENTION-1010-430",
        "title": "Recordkeeping and retention periods",
        "definition": (
            "The requirement to create and retain the records that support a report, and to "
            "keep them for the period the rule specifies, generally five years from the date "
            "of the report. The records that must be kept are those a reasonable person would "
            "expect to be needed to demonstrate that the report was made and that the "
            "institution complied with the underlying obligations. This record summarises the "
            "requirement."
        ),
        "evidence_to_cite": [
            "the retained record, and the date it was created",
            "the retention period applied, and the date the record will be destroyed",
            "the report the record supports, where there is one",
        ],
        "sources": [
            _src(
                "Recordkeeping and retention requirements (31 CFR 1010.430), summarised in the "
                "FinCrime regulatory index.",
                _CFR_1010,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REG-OFAC-REPORTING-501-603",
        "title": "Reporting blocked and rejected transactions",
        "definition": (
            "The requirement to report property that has been blocked because it is believed to "
            "be owned or controlled by a designated party, and property that has been rejected "
            "because a party with whom it would be transacted is designated. The reports are "
            "made to the sanctions authority, and the periods for making them are set out in "
            "the rule and differ between blocking and rejection. This record summarises the "
            "requirement."
        ),
        "evidence_to_cite": [
            "the blocked or rejected property record, and the date of the decision",
            "the report made, and the date it was made",
            "the screening result and the date the designation was checked against",
        ],
        "sources": [
            _src(
                "Reporting of blocked and rejected transactions, and the associated time limits "
                "(31 CFR 501.603 and 501.604), summarised in the FinCrime regulatory index.",
                _OFAC,
            )
        ],
        "confidence": "high",
        "notes": (
            "Designation status is checked against the date of the transaction, not against "
            "today's list: a party designated after the payment does not make the payment "
            "reportable, and a party delisted today was still designated then."
        ),
    },
    {
        "id": "REG-OFAC-TERRORIST-ASSETS-501-601",
        "title": "Blocking property of designated persons",
        "definition": (
            "The requirement to block, and to hold blocked, property in which a designated "
            "person has an interest, and to report it. A financial institution is expected to "
            "screen its customers and its counterparties against the designations in force, "
            "to re-screen as the lists change, and to hold rather than return property that "
            "has been blocked. This record summarises the requirement."
        ),
        "evidence_to_cite": [
            "the screening result, the list version used and the date of the screen",
            "the property blocked, and the date of the block",
            "the report made to the sanctions authority",
        ],
        "sources": [
            _src(
                "Blocking of property owned or controlled by designated persons "
                "(31 CFR 501.601 and 501.603), summarised in the FinCrime regulatory index.",
                _OFAC,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REG-PATRIOT-314A",
        "title": "Mandatory sharing of information with law enforcement",
        "definition": (
            "The provision that permits a financial institution to share information with a "
            "law-enforcement agency about a suspected violation of a law the institution is "
            "subject to, including a suspicion of money laundering and of structuring. The "
            "information is shared through the appropriate agency rather than directly, the "
            "disclosure may not be made to the customer, and the institution may not disclose "
            "the fact that it has made the disclosure. This record summarises the provision."
        ),
        "evidence_to_cite": [
            "the request received, its date and the agency that made it",
            "the information disclosed, and the date of the disclosure",
            "the prohibition on disclosing the disclosure to the customer, and how it was met",
        ],
        "sources": [
            _src(
                "Voluntary sharing of information with law enforcement (31 USC 5318, "
                "subsections (l) and (m)), summarised in the FinCrime regulatory index.",
                _CORNELL_5318,
            )
        ],
        "confidence": "high",
        "notes": (
            "The provision is a permission, not an obligation to report. The duty to file a "
            "report comes from the reporting rules themselves, and the two are frequently "
            "confused."
        ),
    },
    {
        "id": "REG-PATRIOT-314B",
        "title": "Voluntary sharing of information between financial institutions",
        "definition": (
            "The provision that permits a financial institution to share information with "
            "another financial institution about a suspected violation of a law the "
            "institution is subject to, on a safe harbour, subject to conditions including "
            "that the sharing is for the purpose of investigating or preventing the violation, "
            "that the information is shared confidentially, and that the sharing is documented. "
            "This record summarises the provision."
        ),
        "evidence_to_cite": [
            "the request received, and the basis on which the institution answered it",
            "the record of the sharing, and the confidentiality undertaking given",
            "the purpose the sharing was for",
        ],
        "sources": [
            _src(
                "Voluntary sharing between financial institutions (31 USC 5318, subsection (m)), "
                "summarised in the FinCrime regulatory index.",
                _CORNELL_5318,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REG-MLA-1956-1957",
        "title": "Money laundering and conspiracy offences",
        "definition": (
            "The federal offences of conducting a financial transaction with the intention of "
            "concealing the nature, source or location of the value, of disguising the "
            "proceeds as other property, of engaging in a transaction to conceal the "
            "beneficial owner of the value, and of transporting or transferring value knowing "
            "that it is the proceeds of criminal activity. The offences are framed around "
            "conduct and intention, which is why an indicator of a pattern is evidence of a "
            "pattern and not a finding of the offence. This record summarises the offences."
        ),
        "evidence_to_cite": [
            "the transaction records relied on, each cited by its own source id",
            "the facts relied on to establish the intent or knowledge alleged",
            "the source of the value, and the evidence for it",
        ],
        "sources": [
            _src(
                "Money laundering offences and the prohibition on laundering the proceeds of "
                "specified activity (18 USC 1956 and 18 USC 1957), summarised in the FinCrime "
                "regulatory index.",
                _CORNELL_1956,
            )
        ],
        "confidence": "high",
        "notes": (
            "This record describes the offences for context. A skill must not reach a "
            "conclusion about them: the prohibition on a criminality conclusion is a control "
            "in the skill, not a matter of emphasis."
        ),
    },
    {
        "id": "REG-MONEY-SERVICES-REGISTRATION",
        "title": "Registration of money services businesses",
        "definition": (
            "The requirement that a person who conducts a money services business — such as "
            "dealing in foreign currency, issuing or redeeming stored-value instruments, or "
            "transmitting money — register with the financial crimes authority, and that a "
            "registered business maintain an anti-money-laundering programme of its own. A "
            "fintech or payments business may be a money services business without calling "
            "itself one, and the classification drives which obligations apply."
        ),
        "evidence_to_cite": [
            "the registration record, and the registration identifier",
            "the activities the business conducts, and the classification applied to each",
            "the anti-money-laundering programme, where the business is a registrant",
        ],
        "sources": [
            _src(
                "Money services business registration and programme requirements "
                "(31 CFR 1020.380 and 1020.220), summarised in the FinCrime regulatory index.",
                _CFR_1020,
            )
        ],
        "confidence": "high",
    },
    {
        "id": "REG-FOREIGN-CURRENCY-REPORT-1010-370",
        "title": "Reports of foreign currency and monetary instrument transactions",
        "definition": (
            "The requirement to report transactions in foreign currency and monetary "
            "instruments exceeding the stated threshold, conducted by one person in one "
            "business day, and to keep the supporting records. The report is a separate "
            "obligation from currency transaction reporting and is not satisfied by it."
        ),
        "evidence_to_cite": [
            "the report filed, its identifier and the period it covers",
            "the foreign currency and monetary instrument records for the period",
            "the aggregation applied across the person's accounts and locations",
        ],
        "sources": [
            _src(
                "Reporting of foreign currency and monetary instrument transactions "
                "(31 CFR 1010.370), summarised in the FinCrime regulatory index.",
                _CFR_1010,
            )
        ],
        "confidence": "moderate",
    },
    {
        "id": "REG-SAR-CONFIDENTIALITY-1020-320D",
        "title": "Confidentiality of suspicious activity reports",
        "definition": (
            "The rule that the existence of a suspicious activity report, and the information "
            "it contains, may not be disclosed to a customer, a suspect or the wider "
            "organisation except in the limited ways the rule allows, and the safe harbour "
            "for a person who voluntarily discloses information from a report to a law "
            "enforcement agency. The confidentiality rule is a reason a report is not "
            "explained to a customer, and it is not a licence to mislead one about an "
            "unrelated matter."
        ),
        "evidence_to_cite": [
            "the report identifier, and the basis on which its existence was disclosed to anyone",
            "the disclosure itself, where one was made, and to whom",
            "the rationale given to the customer for the account's treatment",
        ],
        "sources": [
            _src(
                "Confidentiality of suspicious activity reports and the related safe harbour "
                "(31 CFR 1020.320), summarised in the FinCrime regulatory index.",
                _CFR_1020,
            )
        ],
        "confidence": "high",
        "notes": (
            "This record is the one most often misused. The rule restricts what may be said "
            "about the report; it does not authorise any other misstatement to the customer."
        ),
    },
    {
        "id": "REG-FINCEN-CIVIL-PENALTY",
        "title": "Civil penalty authority for reporting and programme failures",
        "definition": (
            "The authority to impose a civil monetary penalty for a violation of a reporting, "
            "recordkeeping or anti-money-laundering programme requirement, and the separate "
            "authority to impose penalties on a financial institution for a programme failure, "
            "which are assessed against a set of factors including the size of the institution, "
            "the duration of the failure and whether it was self-reported. The existence of "
            "the penalty authority is why a control failure is a supervisory matter and not "
            "only an operational one. This record summarises the authority."
        ),
        "evidence_to_cite": [
            "the control that failed, and the period the failure covered",
            "the self-assessment and remediation steps taken, with their dates",
            "the regulatory correspondence, where there is any",
        ],
        "sources": [
            _src(
                "Civil monetary penalty provisions for violations of the reporting, "
                "recordkeeping and programme requirements (31 CFR 1010.810 and 1020.810), "
                "summarised in the FinCrime regulatory index.",
                _CFR_1010,
            )
        ],
        "confidence": "moderate",
    },
]
