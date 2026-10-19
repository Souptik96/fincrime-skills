"""Provenance primitives: canonical serialisation and content hashing.

The hash of the evidence set and of the prompt is what makes a run reproducible
and falsifiable. It is also the cross-language portability proof for the
contract: a second implementation in another language must reproduce the same
digest, so the canonical form is specified precisely rather than left to a
serialiser's discretion.

Canonical form (contract `fincrime/provenance/1.0.0`):

* UTF-8 encoding.
* Object keys sorted by Unicode code point.
* No insignificant whitespace.
* JSON string escaping per RFC 8259 with the minimal escape set
  (``, `"`, `\\`, and control characters as `` \\u00XX ``; `` \\b ``/`` \\f ``/
  `` \\n ``/`` \\r ``/`` \\t `` used where applicable).
* Numbers serialised via Python's ``repr`` for ``int``, and via ``repr`` for
  ``float`` with integral floats normalised to an integer form so that
  ``1.0`` and ``1`` hash identically.

Any change to this function is a breaking change to the provenance contract and
requires a contract version bump.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

PROVENANCE_CONTRACT_VERSION = "fincrime/provenance/1.0.0"

__all__ = [
    "PROVENANCE_CONTRACT_VERSION",
    "canonical_json",
    "canonical_bytes",
    "sha256_hex",
    "hash_object",
    "hash_evidence_set",
]


def _normalise(value: Any) -> Any:
    """Recursively normalise a value for canonical serialisation.

    Integral floats collapse to ``int`` so that ``1.0`` and ``1`` produce the
    same digest. Non-finite floats are rejected: they have no canonical JSON
    representation and their hash would be meaningless.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError(f"non-finite float is not canonically serialisable: {value!r}")
        if value.is_integer():
            return int(value)
        return value
    if isinstance(value, dict):
        return {key: _normalise(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalise(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    """Serialise ``value`` to the canonical JSON form defined above."""
    normalised = _normalise(value)
    return json.dumps(
        normalised,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def canonical_bytes(value: Any) -> bytes:
    """Return the UTF-8 encoded canonical JSON form of ``value``."""
    return canonical_json(value).encode("utf-8")


def sha256_hex(value: Any) -> str:
    """Return the lowercase hex SHA-256 digest of the canonical form of ``value``."""
    if isinstance(value, (bytes, bytearray)):
        return hashlib.sha256(value).hexdigest()
    if isinstance(value, str):
        return hashlib.sha256(value.encode("utf-8")).hexdigest()
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def hash_object(value: Any) -> str:
    """Alias for :func:`sha256_hex` over a JSON-compatible object."""
    return sha256_hex(value)


def hash_evidence_set(evidence_set: Any) -> str:
    """Return the canonical digest of an evidence set.

    The digest covers the whole closed world an agent was permitted to see, so
    that a reader can establish that an artifact was produced against exactly
    this evidence and not a superset or subset.
    """
    return hash_object(evidence_set)
