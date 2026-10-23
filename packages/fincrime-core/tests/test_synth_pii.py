"""Tests for zero-PII scanner and guarantee enforcement."""

from __future__ import annotations

import pytest

from fincrime_core.paths import repo_root
from fincrime_core.synth.pii import (
    RESERVED_SYNTHETIC_NAMESPACES,
    luhn_checksum,
    redact_pii,
    scan_directory,
    scan_text,
)


def test_luhn_checksum_calculation() -> None:
    """Luhn formula must validate genuine test card numbers and reject invalid digits."""
    # Well-known Luhn-valid test card numbers
    assert luhn_checksum("4532015112830366") is True
    assert luhn_checksum("4532 0151 1283 0366") is True
    assert luhn_checksum("4532-0151-1283-0366") is True
    # Mutating last check digit fails
    assert luhn_checksum("4532015112830367") is False
    # All identical digits fails
    assert luhn_checksum("0000000000000000") is False


def test_redact_pii_utility() -> None:
    """PII redaction must obscure interior characters while leaving minimal diagnostic boundaries."""
    assert redact_pii("123456789") == "12*****89"
    assert redact_pii("123") == "****"


def test_seeded_ssn_detection() -> None:
    """Scanner must detect real SSNs while accepting synthetic 000-xx-xxxx namespace."""
    # Seeded real SSN violations
    real_ssn_samples = [
        "Customer provided SSN: 219-45-7890 for onboarding.",
        "Taxpayer identification number 458-12-9876 verified.",
        "Social Security: 654 32 1098 on file.",
    ]
    for sample in real_ssn_samples:
        violations = scan_text(sample)
        assert len(violations) >= 1
        assert any(v.pii_type == "ssn" for v in violations)

    # Compliant synthetic SSNs in reserved 000-xx-xxxx namespace
    synthetic_samples = [
        "Synthetic Subject ID SUB-01 SSN 000-12-3456.",
        "Test persona carries synthetic SSN: 000-45-6789.",
        "Reserved testing tax number 000-99-9999.",
    ]
    for sample in synthetic_samples:
        violations = scan_text(sample)
        ssn_violations = [v for v in violations if v.pii_type == "ssn"]
        assert len(ssn_violations) == 0, f"False positive on synthetic SSN: {sample}"


def test_seeded_credit_card_detection() -> None:
    """Scanner must detect Luhn-valid credit card numbers while ignoring random digits/floats."""
    real_cc_samples = [
        "Card payment processed on 4532-0151-1283-0366 via terminal.",
        "Mastercard authorization: 5424 1801 2345 6789 approved.",
        "American Express corporate charge: 3782-822463-10005 settled.",
    ]
    for sample in real_cc_samples:
        violations = scan_text(sample)
        assert len(violations) >= 1
        assert any(v.pii_type == "credit_card" for v in violations)

    # Floats, version numbers, and arbitrary dates must NOT trigger credit card false positives
    clean_numeric_samples = [
        '{"duration_ms": 3.4275997895747423, "latency": 5.4645000491291285}',
        "Release version 1.0.0 built on 2026-10-21T14:30:00Z.",
        "Transaction ID TXN-9841284719284719 with amount 4920.50 USD.",
    ]
    for sample in clean_numeric_samples:
        violations = scan_text(sample)
        cc_violations = [v for v in violations if v.pii_type == "credit_card"]
        assert len(cc_violations) == 0, f"False positive on clean numeric content: {sample}"


def test_seeded_phone_number_detection() -> None:
    """Scanner must detect real phone numbers while accepting reserved 555-01xx range."""
    real_phone_samples = [
        "Primary contact telephone: 415-555-2671 (cellular).",
        "Call received from +1 (212) 867-5309 regarding wire transfer.",
        "Direct branch desk: (312) 987-6543.",
    ]
    for sample in real_phone_samples:
        violations = scan_text(sample)
        assert len(violations) >= 1
        assert any(v.pii_type == "phone" for v in violations)

    # Compliant reserved fictional 555-01xx phone numbers
    fictional_phone_samples = [
        "Synthetic support hotline: 555-0145.",
        "Test persona telephone: (212) 555-0199.",
        "Customer contact on file: +1-415-555-0101.",
    ]
    for sample in fictional_phone_samples:
        violations = scan_text(sample)
        phone_violations = [v for v in violations if v.pii_type == "phone"]
        assert len(phone_violations) == 0, f"False positive on fictional 555-01xx: {sample}"


def test_seeded_corporate_ein_detection() -> None:
    """Scanner must detect real corporate EINs while accepting 00-xxxxxxx."""
    real_ein_samples = [
        "Corporate employer tax ID: 12-3456789.",
        "Entity federal EIN 47-8912345 confirmed with IRS.",
    ]
    for sample in real_ein_samples:
        violations = scan_text(sample)
        assert len(violations) >= 1
        assert any(v.pii_type == "ein" for v in violations)

    # Reserved synthetic EIN
    synthetic_ein_samples = [
        "Synthetic entity tax identifier EIN 00-1234567.",
        "Reserved test corporation EIN: 00-9876543.",
    ]
    for sample in synthetic_ein_samples:
        violations = scan_text(sample)
        ein_violations = [v for v in violations if v.pii_type == "ein"]
        assert len(ein_violations) == 0, f"False positive on synthetic EIN: {sample}"


def test_seeded_email_detection() -> None:
    """Scanner must detect commercial emails while accepting RFC 2606 example domains."""
    real_email_samples = [
        "Send notification to john.doe@chase.com immediately.",
        "Originator email address: analyst@goldmansachs.com.",
        "Personal contact: alert_triage@gmail.com on alert.",
    ]
    for sample in real_email_samples:
        violations = scan_text(sample)
        assert len(violations) >= 1
        assert any(v.pii_type == "email" for v in violations)

    # Compliant synthetic example domains
    synthetic_email_samples = [
        "Investigator contact: analyst@example.com.",
        "System alerts routed to compliance@example.org.",
        "Internal test actor: user123@sub.example.net.",
        "Maintainer tag: @fincrime-maintainers.",
    ]
    for sample in synthetic_email_samples:
        violations = scan_text(sample)
        email_violations = [v for v in violations if v.pii_type == "email"]
        assert len(email_violations) == 0, f"False positive on synthetic email: {sample}"


def test_repository_golden_assets_zero_pii() -> None:
    """All committed skills, knowledge, and examples must contain zero real PII."""
    root = repo_root()
    assert root is not None, "Repo root must be resolvable"

    for target_dir in ("skills", "knowledge", "examples"):
        p = root / target_dir
        if p.exists():
            violations = scan_directory(p)
            assert len(violations) == 0, (
                f"Real PII detected in {target_dir}: "
                f"{[(v.pii_type, v.file_path, v.line_number) for v in violations]}"
            )
