"""Checking a skill package against its contract.

A skill package is a directory with three things in it: a ``SKILL.md`` an
agent reads, a ``fincrime.skill.yaml`` sidecar a machine reads, and (once
the skill is real) a case suite that proves it works. This module checks
that the three agree, and that the policy ids the manifest names exist.

The findings are **skill findings**, not artifact defects. The defect
taxonomy in ``contracts/defect-taxonomy.json`` describes defects in a
*finding document* — a produced artifact. A broken manifest is a different
kind of problem, with a different vocabulary, and mixing the two would
make the taxonomy lie about what the validator enforces.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from fincrime_core.contract.manifest import (
    ManifestFinding,
    SkillManifest,
    check_manifest_consistency,
    parse_skill_manifest,
    validate_skill_manifest,
)
from fincrime_core.eval.cases import validate_case_suite
from fincrime_core.knowledge.model import load_pack, resolve_date
from fincrime_core.policy.set import PolicySet

from fincrime_cli.frontmatter import FrontmatterError, load_skill_md
from fincrime_cli.yamlite import YamlSubsetError, parse

__all__ = [
    "SkillCheckResult",
    "check_skill_package",
    "SKILL_FILENAME",
    "MANIFEST_FILENAME",
    "MAINTENANCE_REQUIRED",
]

SKILL_FILENAME = "SKILL.md"
MANIFEST_FILENAME = "fincrime.skill.yaml"

#: The status a skill is marked with when its knowledge has expired but the
#: skill is allowed to ship. ADR-0006: a released skill is warned, not
#: blocked, but it is disclosed on every surface that lists skills.
MAINTENANCE_REQUIRED = "MAINTENANCE_REQUIRED"

#: A stage heading in the body, for example ``### S3 — Hypothesize``.
_STAGE_HEADING = re.compile(r"^#{2,4}\s*(S\d+)\b", re.MULTILINE)

#: The findings that are part of the shipping gate rather than part of the
#: package being well-formed. A draft skill may fail the gate; a stable one
#: may not.
_GATE_PREFIXES = ("skill-suite", "suite_", "suite-", "case_", "case-")


def _is_gate_finding(code: str) -> bool:
    lowered = code.lower()
    return any(lowered.startswith(prefix) for prefix in _GATE_PREFIXES)


@dataclass(frozen=True, slots=True)
class SkillCheckResult:
    """The outcome of checking one skill package."""

    path: Path
    findings: tuple[ManifestFinding, ...] = ()
    manifest: SkillManifest | None = None
    frontmatter_name: str = ""
    suite_result: Any = None
    detail: dict[str, Any] = field(default_factory=dict)
    maintenance_required: bool = False

    @property
    def valid(self) -> bool:
        return not any(finding.severity == "error" for finding in self.findings)

    @property
    def errors(self) -> tuple[ManifestFinding, ...]:
        return tuple(finding for finding in self.findings if finding.severity == "error")

    @property
    def warnings(self) -> tuple[ManifestFinding, ...]:
        return tuple(finding for finding in self.findings if finding.severity == "warn")

    @property
    def status(self) -> str:
        """The skill's disclosed status: ``MAINTENANCE_REQUIRED`` or ``OK``."""
        return MAINTENANCE_REQUIRED if self.maintenance_required else "OK"


def _finding(code: str, severity: str, message: str) -> ManifestFinding:
    return ManifestFinding(code=code, severity=severity, message=message)


def _stage_ids_in_body(body: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(_STAGE_HEADING.findall(body)))


def _cited_record_ids(manifest: SkillManifest) -> tuple[str, ...]:
    """The record ids the manifest's knowledge block names.

    The block is a mapping of record type to a list of ids. Only the ids the
    manifest itself declares are cited; the rest of the pack is the pack's
    business, not the skill's.
    """
    cited: list[str] = []
    for value in (manifest.knowledge or {}).values():
        if isinstance(value, str):
            cited.append(value)
        elif isinstance(value, Iterable) and not isinstance(value, (str, bytes, Mapping)):
            cited.extend(str(item) for item in value)
    return tuple(dict.fromkeys(cited))


def _knowledge_findings(
    manifest: SkillManifest,
    packs_root: str | Path | None,
    as_of: date | None,
    promotion: bool,
) -> tuple[list[ManifestFinding], bool]:
    """The findings for the knowledge pack a skill declares.

    Three rules, from ADR-0006 and from the pack contract:

    * a record the skill **cites** must exist in the pack. A skill that
      depends on a record nobody published depends on nothing;
    * a **cited** record that has expired is a stale dependency. In the
      promotion context it blocks the gate, so a new skill cannot be built on
      expired regulation; in the release context it is disclosed as a warning
      and the skill is marked ``MAINTENANCE_REQUIRED``;
    * a record the skill does **not** cite is the pack's business, not the
      skill's. It is disclosed as a warning in both contexts, so an unrelated
      expired record elsewhere in the pack never blocks an unaffected skill.

    A skill that declares a pack but cites no record in it depends on the
    **whole pack**: any expired record in it is that skill's stale dependency,
    and the promotion block applies. A skill that cites nothing because it
    cites nothing is not the same thing as a skill that cites records.

    Returns the findings and whether the skill needs maintenance.
    """
    findings: list[ManifestFinding] = []
    if not manifest.knowledge_pack or packs_root is None:
        return findings, False

    pack_dir = Path(packs_root) / manifest.knowledge_pack
    if not pack_dir.is_dir():
        findings.append(
            _finding(
                "SKILL-KNOWLEDGE-UNRESOLVED",
                "warn",
                (
                    f"the declared knowledge pack {manifest.knowledge_pack!r} was not found "
                    f"in {packs_root}. Indicator and record existence cannot be verified "
                    "until it is published; disclose the gap."
                ),
            )
        )
        return findings, False

    resolved = resolve_date(as_of)
    if resolved is None:
        return findings, False

    try:
        pack = load_pack(pack_dir)
    except (OSError, ValueError) as exc:
        findings.append(
            _finding(
                "SKILL-KNOWLEDGE-UNREADABLE",
                "warn",
                f"the declared knowledge pack {manifest.knowledge_pack!r} could not be read: {exc}",
            )
        )
        return findings, False

    known_ids = {record.id for record in pack.records}
    cited = set(_cited_record_ids(manifest))

    for record_id in sorted(cited - known_ids):
        findings.append(
            _finding(
                "SKILL-RECORD-UNRESOLVED",
                "error",
                (
                    f"the skill cites record {record_id!r} in pack {pack.id!r}, but the pack "
                    "does not contain this record."
                ),
            )
        )

    # A skill that declares a pack and cites no record in it depends on the
    # whole pack. A skill that cites records depends on those records.
    whole_pack_dependency = not cited

    stale_dependency = False
    expired = sorted(
        (record for record in pack.records if record.is_expired(resolved)),
        key=lambda record: record.id,
    )
    for record in expired:
        if record.id in cited:
            stale_dependency = True
            scope = "cited by the skill"
            severity = "error" if promotion else "warn"
            code = "SKILL-KNOWLEDGE-EXPIRED"
            consequence = (
                "A skill cannot be promoted on expired knowledge: refresh the record, "
                "re-date it, and publish a new pack version."
                if promotion
                else f"The skill is disclosed as {MAINTENANCE_REQUIRED} rather than blocked; "
                "the refresh lands in the next pack version."
            )
        elif whole_pack_dependency:
            stale_dependency = True
            scope = "present in the declared pack, which the skill depends on as a whole"
            severity = "error" if promotion else "warn"
            code = "SKILL-KNOWLEDGE-EXPIRED"
            consequence = (
                "A skill cannot be promoted on expired knowledge: refresh the record, "
                "re-date it, and publish a new pack version."
                if promotion
                else f"The skill is disclosed as {MAINTENANCE_REQUIRED} rather than blocked; "
                "the refresh lands in the next pack version."
            )
        else:
            scope = "present in the declared pack but not cited by the skill"
            severity = "warn"
            code = "SKILL-KNOWLEDGE-UNCITED-EXPIRED"
            consequence = (
                "The skill does not depend on this record, so it does not block the skill; "
                "the pack's own refresh is tracked against the pack."
            )
        findings.append(
            _finding(
                code,
                severity,
                (
                    f"record {record.id} in pack {pack.id} expired on {record.expires_at} "
                    f"and is {scope}. {consequence}"
                ),
            )
        )

    return findings, stale_dependency


def check_skill_package(
    path: str | Path,
    policy_set: PolicySet | None = None,
    packs_root: str | Path | None = None,
    as_of: date | None = None,
    promotion: bool = False,
) -> SkillCheckResult:
    """Check a skill package and return every problem found.

    ``policy_set`` is the set the manifest's policy ids are resolved
    against. ``packs_root`` is the directory holding knowledge packs; a
    declared pack that cannot be resolved is a disclosure, not a failure,
    because the skill may legitimately be authored ahead of the pack.

    ``promotion`` selects the enforcement context of ADR-0006: in it, an
    expired record the skill depends on is a hard error; without it, the same
    record is a warning and the skill is marked ``MAINTENANCE_REQUIRED``.
    An expired record the skill does not depend on is disclosed in both
    contexts and blocks neither. ``as_of`` is the date the expiry is judged
    against; without it no freshness claim is made.
    """
    root = Path(path)
    findings: list[ManifestFinding] = []
    maintenance_required = False

    skill_path = root / SKILL_FILENAME
    manifest_path = root / MANIFEST_FILENAME

    frontmatter_name = ""
    body = ""
    if not skill_path.exists():
        findings.append(
            _finding(
                "SKILL-FRONTMATTER-MISSING",
                "error",
                f"{SKILL_FILENAME} not found in {root}",
            )
        )
    else:
        try:
            frontmatter = load_skill_md(skill_path)
        except (FrontmatterError, OSError) as exc:
            findings.append(
                _finding("SKILL-FRONTMATTER-INVALID", "error", str(exc))
            )
        else:
            body = frontmatter.body
            frontmatter_name = frontmatter.name
            if not frontmatter_name:
                findings.append(
                    _finding(
                        "SKILL-FRONTMATTER-INVALID",
                        "error",
                        "the frontmatter has no 'name'",
                    )
                )
            elif frontmatter_name != root.name:
                findings.append(
                    _finding(
                        "SKILL-NAME-MISMATCH",
                        "error",
                        (
                            f"the frontmatter names {frontmatter_name!r} but the package "
                            f"directory is {root.name!r}. A host loads the skill by directory name, "
                            "so the two must be the same."
                        ),
                    )
                )
            if not frontmatter.description.strip():
                findings.append(
                    _finding(
                        "SKILL-DESCRIPTION-MISSING",
                        "error",
                        "the frontmatter has no description. A host decides whether to load a "
                        "skill from its description alone.",
                    )
                )

    manifest: SkillManifest | None = None
    if not manifest_path.exists():
        findings.append(
            _finding(
                "SKILL-MANIFEST-MISSING",
                "error",
                f"{MANIFEST_FILENAME} not found in {root}",
            )
        )
    else:
        try:
            with manifest_path.open("r", encoding="utf-8") as handle:
                document = parse(handle.read())
        except (YamlSubsetError, OSError) as exc:
            findings.append(
                _finding("SKILL-MANIFEST-UNPARSEABLE", "error", str(exc))
            )
        else:
            if not isinstance(document, dict):
                findings.append(
                    _finding(
                        "SKILL-MANIFEST-UNPARSEABLE",
                        "error",
                        "the sidecar is not a mapping",
                    )
                )
            else:
                schema_errors = validate_skill_manifest(document)
                for error in schema_errors:
                    findings.append(
                        _finding(
                            "SKILL-MANIFEST-INVALID",
                            "error",
                            f"{error.path}: {error.message}",
                        )
                    )
                if not schema_errors:
                    manifest = parse_skill_manifest(document)
                    for finding in check_manifest_consistency(manifest):
                        findings.append(finding)

    if manifest is not None:
        if policy_set is not None:
            known = set(policy_set.policy_ids())
            for policy_id in manifest.policy_ids() + manifest.guard_ids():
                if policy_id not in known:
                    findings.append(
                        _finding(
                            "SKILL-POLICY-UNRESOLVED",
                            "error",
                            (
                                f"policy {policy_id!r} is not defined by the policy set "
                                f"{policy_set.id!r}. A skill may not depend on a control that "
                                "nobody can point at."
                            ),
                        )
                    )

        body_stages = _stage_ids_in_body(body)
        manifest_stages = tuple(
            str(stage.get("stage", "")) for stage in manifest.stages
        )
        if body_stages and body_stages != manifest_stages:
            findings.append(
                _finding(
                    "SKILL-STAGE-MISMATCH",
                    "error",
                    (
                        f"the body documents stages {list(body_stages)} but the sidecar declares "
                        f"{list(manifest_stages)}. An agent reads the body; a host reads the sidecar."
                    ),
                )
            )

        knowledge_findings, maintenance_required = _knowledge_findings(
            manifest, packs_root, as_of, promotion
        )
        findings.extend(knowledge_findings)

    suite_result = None
    if manifest is not None and manifest.evaluation_suite:
        suite_dir = root / manifest.evaluation_suite
        if not suite_dir.is_dir():
            findings.append(
                _finding(
                    "SKILL-SUITE-MISSING",
                    "error",
                    (
                        f"the manifest names the evaluation suite {manifest.evaluation_suite!r} "
                        f"but {suite_dir} does not exist. A skill without a suite has no gate."
                    ),
                )
            )
        else:
            suite_result = validate_case_suite(suite_dir)
            for suite_finding in suite_result.findings:
                findings.append(
                    _finding(
                        suite_finding.code,
                        suite_finding.severity,
                        suite_finding.message,
                    )
                )

    if manifest is not None and manifest.status != "stable":
        # A draft skill is allowed to be incomplete. The gate applies when the
        # skill claims to be shippable.
        for index, finding in enumerate(findings):
            if _is_gate_finding(finding.code) and finding.severity == "error":
                message = finding.message.rstrip()
                if not message.endswith((".", "!", "?")):
                    message += "."
                findings[index] = ManifestFinding(
                    code=finding.code,
                    severity="warn",
                    message=(
                        message
                        + " The skill is a draft, so this is disclosed rather than enforced."
                    ),
                )

    return SkillCheckResult(
        path=root,
        findings=tuple(findings),
        manifest=manifest,
        frontmatter_name=frontmatter_name,
        suite_result=suite_result,
        maintenance_required=maintenance_required,
    )
