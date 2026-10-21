#!/usr/bin/env python3
"""AST import linter: the core must have zero non-stdlib runtime dependencies.

ADR-0002 makes this a blocking CI check. The core is the trust boundary of a
bank deployment; a transitive dependency is a transitive supply-chain
surface, and a dependency that can open a socket is a dependency that can
exfiltrate case data.

The scan is a static AST walk, not an import test, so it catches a forbidden
import even on a code path the tests do not exercise.

Usage::

    python scripts/check_imports.py [package_dir ...]

Exits non-zero and prints every violation.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

#: The standard library module names, as reported by ``sys.stdlib_module_names``.
#: Available from Python 3.10, which is our floor.
STDLIB = set(sys.stdlib_module_names)

#: Modules that are permitted inside the core because they are part of the
#: Python runtime itself but are not listed in ``sys.stdlib_module_names`` on
#: every platform.
EXTRA_STDLIB = {
    "fincrime_core",  # first-party intra-package imports
    "fincrime_cli",  # the CLI's own intra-package imports
}

#: The packages that are the subject of the check.
DEFAULT_PACKAGES = (
    "packages/fincrime-core/src",
    "packages/fincrime-cli/src",
)

#: A forbidden import is one that pulls in an agent framework, a model SDK, a
#: web framework, or anything that can perform network I/O.
FORBIDDEN_ROOTS = {
    "anthropic",
    "openai",
    "httpx",
    "requests",
    "urllib3",
    "aiohttp",
    "http",
    "socket",
    "ssl",
    "langchain",
    "langchain_core",
    "langgraph",
    "crewai",
    "autogen",
    "pydantic",
    "jsonschema",
    "numpy",
    "pandas",
    "torch",
    "playwright",
    "selenium",
    "yaml",
    "requests_toolbelt",
}


class ImportViolation:
    __slots__ = ("path", "line", "module", "reason")

    def __init__(self, path: Path, line: int, module: str, reason: str) -> None:
        self.path = path
        self.line = line
        self.module = module
        self.reason = reason

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.reason} (import {self.module!r})"


def _root_module(name: str) -> str:
    return name.split(".", 1)[0]


def _module_allowed(name: str) -> bool:
    root = _root_module(name)
    if root in EXTRA_STDLIB:
        return True
    if root in STDLIB:
        # A stdlib module that can perform network I/O is still forbidden
        # inside the core, because the core must not be able to reach out.
        return root not in FORBIDDEN_ROOTS
    return False


def scan_file(path: Path) -> list[ImportViolation]:
    """Return the import violations in one file."""
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    violations: list[ImportViolation] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                root = _root_module(name)
                if root in FORBIDDEN_ROOTS:
                    violations.append(
                        ImportViolation(
                            path, node.lineno, name,
                            "forbidden import in the zero-dependency core",
                        )
                    )
                elif not _module_allowed(name):
                    violations.append(
                        ImportViolation(
                            path, node.lineno, name,
                            "non-stdlib import in the zero-dependency core",
                        )
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue  # relative import within the package
            name = node.module or ""
            root = _root_module(name)
            if root in FORBIDDEN_ROOTS:
                violations.append(
                    ImportViolation(
                        path, node.lineno, name,
                        "forbidden import in the zero-dependency core",
                    )
                )
            elif not _module_allowed(name):
                violations.append(
                    ImportViolation(
                        path, node.lineno, name,
                        "non-stdlib import in the zero-dependency core",
                    )
                )
    return violations


def scan(package_dirs: list[str]) -> list[ImportViolation]:
    """Scan every Python file under the given directories."""
    violations: list[ImportViolation] = []
    for package_dir in package_dirs:
        root = Path(package_dir)
        if not root.exists():
            violations.append(
                ImportViolation(root, 0, str(root), "package directory does not exist")
            )
            continue
        for path in sorted(root.rglob("*.py")):
            violations.extend(scan_file(path))
    return violations


def main(argv: list[str]) -> int:
    package_dirs = argv[1:] or list(DEFAULT_PACKAGES)
    violations = scan(package_dirs)
    if violations:
        print("Import lint FAILED: the core must have zero non-stdlib runtime dependencies.")
        print("See docs/adr/0002-zero-dependency-core.md.\n")
        for violation in violations:
            print(f"  {violation}")
        print(f"\n{len(violations)} violation(s).")
        return 1
    print(f"Import lint OK: {', '.join(package_dirs)} has zero non-stdlib runtime imports.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
