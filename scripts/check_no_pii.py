#!/usr/bin/env python3
"""Wrapper invoking scripts/check_pii.py for backwards compatibility with SECURITY.md."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import check_pii  # noqa: E402

if __name__ == "__main__":
    sys.exit(check_pii.main())
