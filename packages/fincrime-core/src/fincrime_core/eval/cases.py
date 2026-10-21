"""The evaluation case suite: a loader and the mix enforcement it carries.

A case that asserts only "some output" is rejected. The suite is the unit
that holds a skill honest, and a suite of sixty agreeable cases is worth
nothing. Three requirements do the work, and they are the same three
CONTRIBUTING.md states:

* enough cases to be a population rather than an anecdote;
* a mixed population — benign, adversarial, missing-data and contradictory
  cases, so the suite can measure a false-positive rate and not only a
  detection rate;
* negative expectations — cases that assert something the skill must *not*
  do, so a skill that says everything cannot pass.

The thresholds live in the suite manifest rather than in this module, so a
suite can be held to a stricter bar and the bar is visible to whoever writes
the cases.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

from fincrime_core.paths import contracts_dir
from fincrime_core.validate.schema import JsonSchemaValidator

__all__ = [
    "Case",
    "CaseSuite",
    "SuiteFinding",
    "SuiteValidationResult",
    "load_case_schema",
    "load_case_suite_schema",
    "load_case_suite",
    "validate_case_suite",
    "MIXED_CASE_KINDS",
    "DEFAULT_REQUIREMENTS",
]

#: The case kinds that make a suite a population rather than a list of
#: examples. A suite made only of golden cases cannot measure a false
#: positive rate.
MIXED_CASE_KINDS: frozenset[str] = frozenset(
    {"benign", "adversarial", "missing_data", "contradictory"}
)

#: The default thresholds, from CONTRIBUTING.md.
DEFAULT_REQUIREMENTS: Mapping[str, Any] = {
    "min_cases": 60,
    "min_mixed_ratio": 0.4,
    "min_negative_ratio": 0.15,
    "required_kinds": ["golden", "adversarial", "benign"],
    "min_benign_per_typology": True,
}

#: The name of the suite manifest inside a suite directory.
SUITE_FILENAME = "suite.json"


@lru_cache(maxsize=1)
def load_case_schema() -> JsonSchemaValidator:
    """The normative schema for one evaluation case."""
    with (contracts_dir() / "case.schema.json").open("r", encoding="utf-8") as handle:
        return JsonSchemaValidator(json.load(handle))


@lru_cache(maxsize=1)
def load_case_suite_schema() -> JsonSchemaValidator:
    """The normative schema for a case suite manifest."""
    with (contracts_dir() / "case-suite.schema.json").open("r", encoding="utf-8") as handle:
        return JsonSchemaValidator(json.load(handle))


@dataclass(frozen=True, slots=True)
class Case:
    """One evaluation case."""

    case_id: str
    path: str
    kind: str
    suite: str
    version: str
    tags: tuple[str, ...]
    jurisdictions: tuple[str, ...]
    expect: Mapping[str, Any]
    document: Mapping[str, Any] = field(default_factory=dict)

    @property
    def has_negative_expectation(self) -> bool:
        """True when the case asserts something the skill must not do.

        A negative expectation is any of: a forbidden claim class, a
        forbidden indicator, a forbidden string, or an expectation that the
        skill does *not* escalate. A case with none of these asserts only
        what the skill should do, and a skill that does everything passes it.
        """
        expect = self.expect or {}
        if expect.get("forbidden_claim_classes"):
            return True
        if expect.get("forbidden_indicators"):
            return True
        if expect.get("forbidden_strings"):
            return True
        if expect.get("expected_escalation") is False:
            return True
        return False


@dataclass(frozen=True, slots=True)
class CaseSuite:
    """A suite manifest and the cases it lists."""

    suite_id: str
    skill: str
    version: str
    as_of: str
    requirements: Mapping[str, Any]
    cases: tuple[Case, ...]
    typologies: tuple[str, ...] = ()
    description: str = ""

    @property
    def case_count(self) -> int:
        return len(self.cases)

    @property
    def mixed_count(self) -> int:
        return sum(1 for case in self.cases if case.kind in MIXED_CASE_KINDS)

    @property
    def negative_count(self) -> int:
        return sum(1 for case in self.cases if case.has_negative_expectation)

    @property
    def mixed_ratio(self) -> float:
        return self.mixed_count / self.case_count if self.case_count else 0.0

    @property
    def negative_ratio(self) -> float:
        return self.negative_count / self.case_count if self.case_count else 0.0

    def kinds(self) -> tuple[str, ...]:
        return tuple(sorted({case.kind for case in self.cases}))


@dataclass(frozen=True, slots=True)
class SuiteFinding:
    """One problem with a case suite."""

    code: str
    severity: str
    message: str
    case_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "case_id": self.case_id,
        }


@dataclass(frozen=True, slots=True)
class SuiteValidationResult:
    """The outcome of validating a case suite."""

    suite_id: str
    findings: tuple[SuiteFinding, ...] = ()
    suite: CaseSuite | None = None

    @property
    def valid(self) -> bool:
        return not any(finding.severity == "error" for finding in self.findings)

    @property
    def errors(self) -> tuple[SuiteFinding, ...]:
        return tuple(finding for finding in self.findings if finding.severity == "error")

    @property
    def warnings(self) -> tuple[SuiteFinding, ...]:
        return tuple(finding for finding in self.findings if finding.severity == "warn")


def _parse_case(entry: Mapping[str, Any], document: Mapping[str, Any], path: str) -> Case:
    expect = document.get("expect") or {}
    return Case(
        case_id=str(document.get("case_id", entry.get("case_id", ""))),
        path=path,
        kind=str(document.get("kind", "")),
        suite=str(document.get("suite", "")),
        version=str(document.get("version", "")),
        tags=tuple(document.get("tags") or ()),
        jurisdictions=tuple(document.get("jurisdictions") or ()),
        expect=expect if isinstance(expect, Mapping) else {},
        document=document,
    )


def load_case_suite(suite_dir: str | Path) -> tuple[CaseSuite, tuple[SuiteFinding, ...]]:
    """Load a case suite from a directory.

    Returns the suite and the findings raised while loading it. The suite is
    returned even when there are findings, so a caller can report every
    problem in one pass rather than one problem per run.
    """
    root = Path(suite_dir)
    findings: list[SuiteFinding] = []

    manifest_path = root / SUITE_FILENAME
    if not manifest_path.exists():
        return (
            CaseSuite(
                suite_id=root.name,
                skill="",
                version="",
                as_of="",
                requirements=dict(DEFAULT_REQUIREMENTS),
                cases=(),
            ),
            (
                SuiteFinding(
                    code="suite_manifest_missing",
                    severity="error",
                    message=f"case suite manifest not found: {manifest_path}",
                ),
            ),
        )

    try:
        with manifest_path.open("r", encoding="utf-8") as handle:
            manifest = json.load(handle)
    except (OSError, ValueError) as exc:
        return (
            CaseSuite(
                suite_id=root.name,
                skill="",
                version="",
                as_of="",
                requirements=dict(DEFAULT_REQUIREMENTS),
                cases=(),
            ),
            (
                SuiteFinding(
                    code="suite_manifest_unreadable",
                    severity="error",
                    message=f"case suite manifest could not be read: {exc}",
                ),
            ),
        )

    if not isinstance(manifest, Mapping):
        return (
            CaseSuite(
                suite_id=root.name,
                skill="",
                version="",
                as_of="",
                requirements=dict(DEFAULT_REQUIREMENTS),
                cases=(),
            ),
            (
                SuiteFinding(
                    code="suite_manifest_unreadable",
                    severity="error",
                    message="case suite manifest is not a JSON object",
                ),
            ),
        )

    for error in load_case_suite_schema().validate(manifest):
        findings.append(
            SuiteFinding(
                code="suite_manifest_invalid",
                severity="error",
                message=f"manifest: {error.path}: {error.message}",
            )
        )

    requirements = manifest.get("requirements") or dict(DEFAULT_REQUIREMENTS)
    cases: list[Case] = []
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()

    for entry in manifest.get("cases") or ():
        if not isinstance(entry, Mapping):
            findings.append(
                SuiteFinding(
                    code="suite_manifest_invalid",
                    severity="error",
                    message="manifest: every case entry must be an object",
                )
            )
            continue

        case_id = str(entry.get("case_id", ""))
        relative_path = str(entry.get("path", ""))
        if not case_id or not relative_path:
            findings.append(
                SuiteFinding(
                    code="suite_manifest_invalid",
                    severity="error",
                    message="manifest: every case entry needs a case_id and a path",
                )
            )
            continue

        if case_id in seen_ids:
            findings.append(
                SuiteFinding(
                    code="case_duplicate_id",
                    severity="error",
                    message=f"case id {case_id} is listed more than once",
                    case_id=case_id,
                )
            )
            continue
        seen_ids.add(case_id)

        if relative_path in seen_paths:
            findings.append(
                SuiteFinding(
                    code="case_duplicate_path",
                    severity="error",
                    message=f"case file {relative_path} is listed more than once",
                    case_id=case_id,
                )
            )
            continue
        seen_paths.add(relative_path)

        case_path = root / relative_path
        if not case_path.exists():
            findings.append(
                SuiteFinding(
                    code="case_not_found",
                    severity="error",
                    message=f"case file not found: {relative_path}",
                    case_id=case_id,
                )
            )
            continue

        try:
            with case_path.open("r", encoding="utf-8") as handle:
                document = json.load(handle)
        except (OSError, ValueError) as exc:
            findings.append(
                SuiteFinding(
                    code="case_unreadable",
                    severity="error",
                    message=f"{relative_path}: could not be read as JSON: {exc}",
                    case_id=case_id,
                )
            )
            continue

        if not isinstance(document, Mapping):
            findings.append(
                SuiteFinding(
                    code="case_invalid",
                    severity="error",
                    message=f"{relative_path}: a case must be a JSON object",
                    case_id=case_id,
                )
            )
            continue

        for error in load_case_schema().validate(document):
            findings.append(
                SuiteFinding(
                    code="case_invalid",
                    severity="error",
                    message=f"{relative_path}: {error.path}: {error.message}",
                    case_id=case_id,
                )
            )

        document_id = str(document.get("case_id", ""))
        if document_id and document_id != case_id:
            findings.append(
                SuiteFinding(
                    code="case_id_mismatch",
                    severity="error",
                    message=(
                        f"{relative_path} declares case_id {document_id} but the manifest lists it as {case_id}"
                    ),
                    case_id=case_id,
                )
            )

        cases.append(_parse_case(entry, document, relative_path))

    listed = {str(entry.get("case_id", "")) for entry in manifest.get("cases") or () if isinstance(entry, Mapping)}
    for path in sorted(root.rglob("*.json")):
        if path.name == SUITE_FILENAME:
            continue
        relative = path.relative_to(root).as_posix()
        if relative not in seen_paths:
            findings.append(
                SuiteFinding(
                    code="case_unlisted",
                    severity="error",
                    message=(
                        f"{relative} is present in the suite but is not listed in the manifest. "
                        "An unlisted case is a case nobody counts."
                    ),
                )
            )

    suite = CaseSuite(
        suite_id=str(manifest.get("suite_id", root.name)),
        skill=str(manifest.get("skill", "")),
        version=str(manifest.get("version", "")),
        as_of=str(manifest.get("as_of", "")),
        requirements=requirements,
        cases=tuple(cases),
        typologies=tuple(manifest.get("typologies") or ()),
        description=str(manifest.get("description", "")),
    )

    return suite, tuple(findings)


def validate_case_suite(suite_dir: str | Path) -> SuiteValidationResult:
    """Load a case suite and check it against its own requirements.

    The requirement checks are errors: a suite that does not meet the mix it
    declares cannot measure what it claims to measure. The mix itself is
    stated in the suite, so the bar is never a hidden default.
    """
    suite, findings = load_case_suite(suite_dir)
    findings = list(findings)

    requirements = suite.requirements or dict(DEFAULT_REQUIREMENTS)

    min_cases = int(requirements.get("min_cases", DEFAULT_REQUIREMENTS["min_cases"]))
    if suite.case_count < min_cases:
        findings.append(
            SuiteFinding(
                code="suite_case_count_below_minimum",
                severity="error",
                message=f"the suite has {suite.case_count} cases and requires at least {min_cases}",
            )
        )

    min_mixed = float(requirements.get("min_mixed_ratio", DEFAULT_REQUIREMENTS["min_mixed_ratio"]))
    if suite.mixed_ratio < min_mixed:
        findings.append(
            SuiteFinding(
                code="suite_mixed_ratio_below_minimum",
                severity="error",
                message=(
                    f"{suite.mixed_count} of {suite.case_count} cases are benign, adversarial, "
                    f"missing-data or contradictory ({suite.mixed_ratio:.0%}); the suite requires "
                    f"at least {min_mixed:.0%}"
                ),
            )
        )

    min_negative = float(
        requirements.get("min_negative_ratio", DEFAULT_REQUIREMENTS["min_negative_ratio"])
    )
    if suite.negative_ratio < min_negative:
        findings.append(
            SuiteFinding(
                code="suite_negative_ratio_below_minimum",
                severity="error",
                message=(
                    f"{suite.negative_count} of {suite.case_count} cases assert something the skill "
                    f"must not do ({suite.negative_ratio:.0%}); the suite requires at least "
                    f"{min_negative:.0%}"
                ),
            )
        )

    required_kinds = requirements.get("required_kinds") or []
    present = set(suite.kinds())
    for kind in required_kinds:
        if kind not in present:
            findings.append(
                SuiteFinding(
                    code="suite_missing_required_kind",
                    severity="error",
                    message=f"the suite requires at least one {kind} case and has none",
                )
            )

    if requirements.get("min_benign_per_typology") and suite.typologies:
        for typology in suite.typologies:
            covered = any(
                case.kind == "benign" and typology in case.tags for case in suite.cases
            )
            if not covered:
                findings.append(
                    SuiteFinding(
                        code="suite_benign_typology_uncovered",
                        severity="error",
                        message=(
                            f"typology {typology} has no benign case. A typology with no benign "
                            "lookalike is a detector with no false-positive population."
                        ),
                    )
                )

    return SuiteValidationResult(
        suite_id=suite.suite_id,
        findings=tuple(findings),
        suite=suite,
    )
