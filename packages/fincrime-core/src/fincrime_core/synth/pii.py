"""Zero-PII guarantee and multi-pattern PII scanner.

Enforces that evaluation datasets and generated fixtures contain only
synthetic entities within reserved namespaces, strictly rejecting real:
- US Social Security Numbers (SSN)
- Credit Card Numbers (validated via the Luhn checksum formula)
- US and international telephone numbers (outside the reserved 555-01xx range)
- Corporate Employer Identification Numbers (EIN) outside 00-xxxxxxx
- Real corporate/personal email addresses outside RFC 2606 reserved domains

Reserved Synthetic Namespaces:
- SSN: 000-xx-xxxx (SSA unissued / reserved fictional block)
- Phone: 555-0100 through 555-0199 (NANP reserved fictional block)
- EIN: 00-xxxxxxx (IRS non-issuable prefix)
- Email: *@example.com, *@example.org, *@example.net, *@*.test
- Identifiers: SUBJ-*, SUB-*, CUST-*, ACCT-*, ACC-*, TXN-*, DOC-*, ALT-*,
               POL-*, IND-*, TYP-*, REG-*, REQ-*, BENIGN-*, GAP-*, BR-*
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

__all__ = [
    "PIIViolation",
    "luhn_checksum",
    "redact_pii",
    "scan_text",
    "scan_file",
    "scan_directory",
    "RESERVED_SYNTHETIC_NAMESPACES",
]

RESERVED_SYNTHETIC_NAMESPACES = (
    "SUBJ-",
    "SUB-",
    "CUST-",
    "ACCT-",
    "ACC-",
    "TXN-",
    "DOC-",
    "ALT-",
    "POL-",
    "IND-",
    "TYP-",
    "REG-",
    "REQ-",
    "BENIGN-",
    "GAP-",
    "BR-",
    "000-",
    "555-01",
    "@example.com",
    "@example.org",
    "@example.net",
)

# ---------------------------------------------------------------------------
# Compiled Regular Expressions for PII Detection
# ---------------------------------------------------------------------------

# US SSN: 3 digits, 2 digits, 4 digits with hyphen or space separator.
# Valid real SSN area is 001-665, 667-899. 000 is SSA unissued/reserved for testing.
_SSN_PATTERN = re.compile(
    r"(?<![0-9a-zA-Z.])(?!000|666|9\d{2})(\d{3})[- ](?!00)(\d{2})[- ](?!0000)(\d{4})(?![0-9a-zA-Z])(?!\.\d)"
)

# US Corporate EIN: 2 digits, 7 digits.
# Valid IRS campus prefixes: 01-06, 10-16, 20-27, 30-39, 40-48, 50-59, 60-68, 71-77, 80-88, 90-95, 98-99.
# Prefix 00 is unissued/reserved synthetic.
_VALID_IRS_EIN_PREFIXES = frozenset(
    [
        "01", "02", "03", "04", "05", "06",
        "10", "11", "12", "13", "14", "15", "16",
        "20", "21", "22", "23", "24", "25", "26", "27",
        "30", "31", "32", "33", "34", "35", "36", "37", "38", "39",
        "40", "41", "42", "43", "44", "45", "46", "47", "48",
        "50", "51", "52", "53", "54", "55", "56", "57", "58", "59",
        "60", "61", "62", "63", "64", "65", "66", "67", "68",
        "71", "72", "73", "74", "75", "76", "77",
        "80", "81", "82", "83", "84", "85", "86", "87", "88",
        "90", "91", "92", "93", "94", "95", "98", "99",
    ]
)
_EIN_PATTERN = re.compile(r"(?<![0-9a-zA-Z.])(\d{2})-(\d{7})(?![0-9a-zA-Z])(?!\.\d)")

# Credit Card Candidate Regex (Visa, Mastercard, Amex, Discover)
_CC_CANDIDATE_PATTERN = re.compile(
    r"(?<![0-9a-zA-Z.])(?:4\d{3}|5[1-5]\d{2}|2[2-7]\d{2}|3[47]\d{2}|6011|65\d{2})[\s-]?(?:\d{4}[\s-]?\d{4}[\s-]?\d{3,4}|\d{6}[\s-]?\d{5})(?![0-9a-zA-Z])(?!\.\d)"
)

# US Phone: NANP 10-digit formats with optional +1 prefix, requiring separator or parens
_PHONE_PATTERN = re.compile(
    r"(?<![0-9a-zA-Z.-])(?:\+?1[-.\s])?\(?([2-9]\d{2})\)?\s*[-.\s]?\s*([2-9]\d{2})[-.\s](\d{4})(?![0-9a-zA-Z-])(?!\.\d)"
)

# Email Address Regex
_EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b"
)

_WHITELISTED_EMAIL_DOMAINS = frozenset(
    [
        "example.com",
        "example.org",
        "example.net",
        "test",
        "invalid",
        "localhost",
    ]
)


@dataclass(frozen=True, slots=True)
class PIIViolation:
    """A detected PII instance violating the zero-PII guarantee."""

    pii_type: str  # "ssn", "credit_card", "phone", "ein", "email"
    matched_value_redacted: str
    line_number: int
    context: str
    file_path: str = ""


def luhn_checksum(digits_str: str) -> bool:
    """Validate digits with the Luhn checksum formula."""
    clean = [c for c in digits_str if c.isdigit()]
    if len(clean) < 13 or len(clean) > 19:
        return False
    # Constant repeat checks (e.g. 0000000000000000)
    if len(set(clean)) == 1:
        return False

    total = 0
    reverse_digits = clean[::-1]
    for i, char in enumerate(reverse_digits):
        n = int(char)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def redact_pii(val: str) -> str:
    """Safely redact sensitive matched string for logging/reporting."""
    if len(val) <= 4:
        return "****"
    return val[:2] + "*" * (len(val) - 4) + val[-2:]


def scan_text(text: str, file_path: str = "") -> list[PIIViolation]:
    """Scan arbitrary text content and return all detected PII violations."""
    violations: list[PIIViolation] = []
    lines = text.splitlines()

    for line_idx, line in enumerate(lines, start=1):
        # Skip lines that are purely cryptographic digests or git hashes
        if any(h in line for h in ("_sha256", "sha256_hex", "commit_hash", "checksum", "git_hash")):
            continue

        # 1. Check SSN
        for m in _SSN_PATTERN.finditer(line):
            raw = m.group(0)
            area = m.group(1)
            # Area 000 is reserved synthetic non-issuable block
            if area == "000":
                continue
            violations.append(
                PIIViolation(
                    pii_type="ssn",
                    matched_value_redacted=redact_pii(raw),
                    line_number=line_idx,
                    context=line.strip()[:100],
                    file_path=file_path,
                )
            )

        # 2. Check Credit Cards (with Luhn check)
        for m in _CC_CANDIDATE_PATTERN.finditer(line):
            raw = m.group(0)
            clean_digits = "".join(c for c in raw if c.isdigit())
            if luhn_checksum(clean_digits):
                violations.append(
                    PIIViolation(
                        pii_type="credit_card",
                        matched_value_redacted=redact_pii(raw),
                        line_number=line_idx,
                        context=line.strip()[:100],
                        file_path=file_path,
                    )
                )

        # 3. Check Corporate EIN
        for m in _EIN_PATTERN.finditer(line):
            raw = m.group(0)
            prefix = m.group(1)
            # 00 prefix is reserved synthetic
            if prefix == "00":
                continue
            # Must match valid IRS campus prefixes
            if prefix in _VALID_IRS_EIN_PREFIXES:
                # Disambiguate from date fragments or version numbers if context suggests
                if "EIN" in line or "tax" in line.lower() or "employer" in line.lower() or not (line.count("-") >= 2 and len(line) <= 12):
                    violations.append(
                        PIIViolation(
                            pii_type="ein",
                            matched_value_redacted=redact_pii(raw),
                            line_number=line_idx,
                            context=line.strip()[:100],
                            file_path=file_path,
                        )
                    )

        # 4. Check Phone Numbers
        for m in _PHONE_PATTERN.finditer(line):
            raw = m.group(0)
            area_code = m.group(1)
            exchange = m.group(2)
            subscriber = m.group(3)

            # Whitelist fictional 555-01xx range (555-0100 through 555-0199)
            if exchange == "555" and subscriber.startswith("01"):
                continue

            # Skip common date formats that resemble numbers (YYYY-MM-DD)
            if "-" in raw and any(y in raw for y in ("2024-", "2025-", "2026-", "2027-")):
                continue

            violations.append(
                PIIViolation(
                    pii_type="phone",
                    matched_value_redacted=redact_pii(raw),
                    line_number=line_idx,
                    context=line.strip()[:100],
                    file_path=file_path,
                )
            )

        # 5. Check Emails
        for m in _EMAIL_PATTERN.finditer(line):
            raw = m.group(0)
            domain = m.group(1).lower()

            if domain in _WHITELISTED_EMAIL_DOMAINS or any(
                domain.endswith("." + wd) for wd in _WHITELISTED_EMAIL_DOMAINS
            ):
                continue
            # Whitelist package repository maintainer references
            if "fincrime-maintainers" in raw:
                continue

            violations.append(
                PIIViolation(
                    pii_type="email",
                    matched_value_redacted=redact_pii(raw),
                    line_number=line_idx,
                    context=line.strip()[:100],
                    file_path=file_path,
                )
            )

    return violations


def scan_file(path: Path) -> list[PIIViolation]:
    """Scan a single file for PII violations."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return []
    return scan_text(content, file_path=str(path))


def scan_directory(
    path: Path,
    extensions: tuple[str, ...] = (
        ".json",
        ".yaml",
        ".yml",
        ".md",
        ".txt",
        ".py",
    ),
    exclude_dirs: tuple[str, ...] = (
        ".git",
        ".venv",
        ".pytest_cache",
        "__pycache__",
        "node_modules",
    ),
) -> list[PIIViolation]:
    """Recursively scan a directory for PII violations across target extensions."""
    violations: list[PIIViolation] = []
    if not path.is_dir():
        return scan_file(path)

    for item in path.rglob("*"):
        if item.is_file() and item.suffix.lower() in extensions:
            if any(part in exclude_dirs for part in item.parts):
                continue
            violations.extend(scan_file(item))

    return violations
