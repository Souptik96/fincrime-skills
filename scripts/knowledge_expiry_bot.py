#!/usr/bin/env python3
"""File the knowledge refresh issues the expiry plan calls for.

ADR-0006 makes the expiry bot a recruitment mechanism: for each stale
dependency it opens a labelled issue, addressed to the record's maintainer,
containing the precise refresh diff required.

This script does the filing and nothing else. It does not decide what is
stale — ``fincrime knowledge check`` does, as a pure function of the pack
and the date — and it does not decide what a refresh should say. The plan it
receives already contains the issue title, the body, the labels and the
maintainer.

Idempotency: the issue title is deterministic, so a record that already has
an open issue under that title is skipped. Running the bot twice does not
file two issues for one record.

Usage::

    python scripts/knowledge_expiry_bot.py --packs knowledge/packs --as-of 2026-10-21
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

#: The label every issue raised by the bot carries.
EXPIRY_LABEL = "knowledge/expired"

#: The suffixes that mark a maintainer handle as naming a team rather than a
#: person. GitHub's issue assignee field accepts individual user logins only,
#: so a team handle is notified by mention instead of by assignment.
TEAM_HANDLE_SUFFIXES = ("-maintainers", "-team", "-maintainer", "-owners")


def is_team_handle(handle: str) -> bool:
    """True when the maintainer handle names a team rather than a person."""
    slug = handle.strip().lstrip("@").lower()
    if not slug:
        return False
    if slug in ("team", "maintainers", "owners"):
        return True
    if slug.startswith("team-") or slug.startswith("org-"):
        return True
    return any(slug.endswith(suffix) for suffix in TEAM_HANDLE_SUFFIXES)


def compute_plan(pack_dir: Path, as_of: str) -> list[dict]:
    """Ask the CLI for the refresh plan of one pack."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "fincrime_cli.main",
            "knowledge",
            "check",
            "--pack",
            str(pack_dir),
            "--as-of",
            as_of,
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    text = result.stdout
    start = text.find("{")
    if start < 0:
        return []
    document = json.loads(text[start:])
    return list(document.get("actions", []))


def open_issue_titles() -> set[str]:
    """The titles of the open issues already carrying the expiry label."""
    result = subprocess.run(
        [
            "gh",
            "issue",
            "list",
            "--label",
            EXPIRY_LABEL,
            "--state",
            "open",
            "--limit",
            "500",
            "--json",
            "title",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return {item["title"] for item in json.loads(result.stdout)}


def file_issue(action: dict) -> tuple[bool, str]:
    """File one issue. Returns ``(filed, detail)``.

    A maintainer handle that names a team cannot be an assignee — GitHub
    accepts individual logins there — so the team is mentioned in the body
    instead, and the issue is still filed. If an assignment fails for any
    other reason, the issue is filed again without the assignee: an
    unassigned issue that reaches a maintainer beats an issue that does not
    reach one at all.
    """
    title = action["issue_title"]
    labels = action.get("labels") or [EXPIRY_LABEL]
    body = action["issue_body"]

    maintainer = (action.get("maintainer") or "").strip()
    assignee = ""
    if maintainer.startswith("@") and len(maintainer) > 1:
        if is_team_handle(maintainer):
            body = (
                f"{maintainer} owns this record, so this issue is addressed to the team. "
                "The refresh diff is below.\n\n" + body
            )
        else:
            assignee = maintainer[1:]

    command = [
        "gh",
        "issue",
        "create",
        "--title",
        title,
        "--body",
        body,
    ]
    for label in labels:
        command += ["--label", label]

    if assignee:
        result = subprocess.run(
            command + ["--assignee", assignee], capture_output=True, text=True
        )
        if result.returncode != 0:
            if result.stdout.strip():
                # The issue was created; only the assignment failed. Filing it
                # again would duplicate it.
                return True, result.stdout.strip()
            result = subprocess.run(command, capture_output=True, text=True)
    else:
        result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        return False, result.stderr.strip()
    return True, result.stdout.strip()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--packs",
        default="knowledge/packs",
        help="the directory holding the published packs",
    )
    parser.add_argument(
        "--as-of",
        required=True,
        help="the date to check as of (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the issues that would be filed, and file nothing",
    )
    args = parser.parse_args(argv)

    packs_root = Path(args.packs)
    manifests = sorted(packs_root.glob("*/manifest.json"))
    if not manifests:
        print("No knowledge packs are published yet; nothing to refresh.")
        return 0

    actions: list[dict] = []
    for manifest in manifests:
        actions.extend(compute_plan(manifest.parent, args.as_of))

    if not actions:
        print(f"No stale records as of {args.as_of}.")
        return 0

    if args.dry_run:
        for action in actions:
            print(f"would file: {action['issue_title']}")
        return 0

    existing = open_issue_titles()
    filed = 0
    skipped = 0
    for action in actions:
        title = action["issue_title"]
        if title in existing:
            print(f"skipped (already open): {title}")
            skipped += 1
            continue
        ok, detail = file_issue(action)
        if ok:
            print(f"filed: {title} -> {detail}")
            filed += 1
        else:
            print(f"error: {title}: {detail}", file=sys.stderr)
    print(f"{filed} issue(s) filed, {skipped} skipped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
