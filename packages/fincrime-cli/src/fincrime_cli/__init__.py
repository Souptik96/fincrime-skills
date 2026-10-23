"""``fincrime`` — the command for authoring, validating, and inspecting skills.

The core engine (``fincrime-core``) validates findings. This package does
everything around it: scaffolding a skill package, validating a skill
package against its contract, loading and exporting a policy set, and
checking a knowledge pack's integrity and staleness.

The CLI is stdlib-only at runtime and reaches the network never. It is a
development and CI tool; it is not part of the trust boundary that ADR-0002
protects.
"""

from __future__ import annotations

__version__ = "1.0.0"

__all__ = ["__version__"]
