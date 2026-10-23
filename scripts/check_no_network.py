#!/usr/bin/env python3
"""Run the test suite with sockets disabled.

The core must not be able to reach the network, and the golden path must run
in an air-gapped environment. This script installs a socket guard, then runs
pytest in-process, so that any attempt to open a connection fails the run.

Usage::

    python scripts/check_no_network.py [-- pytest args]

Exits non-zero if the suite fails, or if a socket was created.
"""

from __future__ import annotations

import socket
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

for pkg in ("packages/fincrime-core/src", "packages/fincrime-cli/src"):
    pkg_path = str(REPO_ROOT / pkg)
    if pkg_path not in sys.path:
        sys.path.insert(0, pkg_path)

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class NetworkAccessAttempted(RuntimeError):
    """Raised when something under test tries to open a socket."""


class _BlockedSocket(socket.socket):
    """A socket that refuses to be created."""

    def __init__(self, *args, **kwargs):  # noqa: D107
        raise NetworkAccessAttempted(
            "network access is disabled for this run; the core must be air-gap safe"
        )


def install_guard() -> None:
    """Disable outbound socket creation for the current process."""
    socket.socket = _BlockedSocket  # type: ignore[misc,assignment]
    socket.create_connection = _blocked_create_connection  # type: ignore[assignment]

    def _guard(*args, **kwargs):  # noqa: ANN001, ANN002, ANN003
        raise NetworkAccessAttempted(
            "network access is disabled for this run; the core must be air-gap safe"
        )

    socket.getaddrinfo = _guard  # type: ignore[assignment]
    socket.gethostbyname = _guard  # type: ignore[assignment]


def _blocked_create_connection(*args, **kwargs):  # noqa: ANN002, ANN003
    raise NetworkAccessAttempted(
        "network access is disabled for this run; the core must be air-gap safe"
    )


def main(argv: list[str]) -> int:
    install_guard()
    try:
        import pytest
    except ImportError:
        print("pytest is not installed; run `pip install -e packages/fincrime-core[dev]`")
        return 2

    args = list(argv[1:])
    if args and args[0] == "--":
        args = args[1:]
    if not args:
        args = ["packages/fincrime-core/tests", "-q"]
    exit_code = pytest.main(args)
    if exit_code == 0:
        print("\nNetwork-blocked test run OK: the core opened no sockets.")
    return int(exit_code)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
