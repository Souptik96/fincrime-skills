"""Locating the canonical contract files.

The contracts in ``contracts/`` are normative and live at the repository root,
outside the installed package, so that adapters, the CLI, and the
documentation all reference one copy.

A wheel install ships the same files inside the package as
``fincrime_core/_contracts`` (see the ``force-include`` setting in
``pyproject.toml``), because a validator that cannot find its own contract
cannot validate anything -- and the validator must be usable in an air-gapped
environment with no repository present.

Resolution order:

1. the packaged copy, ``fincrime_core/_contracts``;
2. the repository checkout, found by walking upward from this module.

When neither is present the caller gets a clear error rather than a silent
fallback to an empty schema.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

__all__ = ["contracts_dir", "repo_root", "packaged_contracts_dir", "ContractsNotFound"]


class ContractsNotFound(FileNotFoundError):
    """Raised when the canonical contract directory cannot be located."""


@lru_cache(maxsize=1)
def packaged_contracts_dir() -> Path | None:
    """Return the contracts shipped inside the package, if present."""
    candidate = Path(__file__).resolve().parent / "_contracts"
    return candidate if candidate.is_dir() else None


@lru_cache(maxsize=1)
def repo_root() -> Path | None:
    """Return the repository root, identified by the presence of ``contracts/``."""
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / "contracts").is_dir():
            return candidate
    return None


@lru_cache(maxsize=1)
def contracts_dir() -> Path:
    """Return the canonical ``contracts/`` directory."""
    packaged = packaged_contracts_dir()
    if packaged is not None:
        return packaged
    root = repo_root()
    if root is not None:
        return root / "contracts"
    raise ContractsNotFound(
        "the canonical contracts directory could not be located; "
        "the package appears to be installed without its contract files"
    )
