"""Expected defect recall and false defect rate scorers.

- expected_defect_recall (gate: >= 0.90): Recall rate when evaluating intentionally
  defective artifacts or cases with discriminating negative assertions.
- false_defect_rate (gate: <= 0.05): Defect rate reported when evaluating
  compliant golden artifacts (must be zero false defects on reference golden corpus).
"""

from __future__ import annotations

from typing import Any, Mapping

from fincrime_core.eval.cases import Case
from fincrime_core.eval.scorers.base import ScoreResult, Scorer
from fincrime_core.validate.validator import ValidationResult

__all__ = ["ExpectedDefectRecallScorer", "FalseDefectRateScorer"]


class ExpectedDefectRecallScorer(Scorer):
    """Scores recall rate on expected defects and negative case expectations."""

    metric_name = "expected_defect_recall"
    default_gate_target = 0.90
    gate_type = "min"

    def score(
        self,
        candidate: dict[str, Any],
        case: Case,
        manifest: Mapping[str, Any] | None = None,
        validation_result: ValidationResult | None = None,
        gate_target: float | None = None,
        **kwargs: Any,
    ) -> ScoreResult:
        target = gate_target if gate_target is not None else self.default_gate_target

        # Check if the case or provider declared expected defects
        expected_defects: list[str] = []
        for tag in case.tags:
            if tag.startswith("mutation:"):
                expected_defects.append(tag.split(":", 1)[1])
            elif tag.startswith("expected_defect:"):
                expected_defects.append(tag.split(":", 1)[1])

        # If the case does not test a defect or mutation, recall is vacuously 1.0
        if not expected_defects and not kwargs.get("expected_defect"):
            return ScoreResult(
                metric=self.metric_name,
                score=1.0,
                passed=True,
                gate_target=target,
                gate_type=self.gate_type,
                details={"status": "no_expected_defects"},
            )

        declared_expected = list(expected_defects)
        if kwargs.get("expected_defect"):
            declared_expected.append(str(kwargs["expected_defect"]))

        # Check if validation result or compliance checks caught the defect
        defects = validation_result.defects if validation_result is not None else []
        schema_errors = (
            validation_result.schema_errors if validation_result is not None else []
        )

        detected_codes = {d.code for d in defects} | {d.rule_id for d in defects if d.rule_id}
        if schema_errors:
            detected_codes.add("schema_error")

        recalled = 0
        missed: list[str] = []
        for exp in declared_expected:
            # Map common mutation names to defect codes/rules
            matched = False
            if exp in detected_codes:
                matched = True
            elif exp == "missing_benign_hypothesis" and (
                "missing_benign_reading" in detected_codes or "R-3b" in detected_codes
            ):
                matched = True
            elif exp == "ungrounded_recommendation" and (
                "recommendation_without_basis" in detected_codes or "R-10" in detected_codes
            ):
                matched = True
            elif exp == "culpability_assertion" and (
                "unsupported_claim" in detected_codes or "R-6" in detected_codes
            ):
                matched = True
            elif exp == "uncited_indicator" and (
                "unsupported_claim" in detected_codes or "R-2" in detected_codes
            ):
                matched = True
            elif exp == "unanchored_timeline" and (
                "unsupported_claim" in detected_codes or "R-1b" in detected_codes
            ):
                matched = True
            elif exp == "schema_error" and (schema_errors or "schema_error" in detected_codes):
                matched = True
            elif exp == "prohibited_claim" and defects:
                matched = True

            if matched:
                recalled += 1
            else:
                missed.append(exp)

        score = recalled / len(declared_expected) if declared_expected else 1.0
        passed = self.is_passing(score, target)

        return ScoreResult(
            metric=self.metric_name,
            score=score,
            passed=passed,
            gate_target=target,
            gate_type=self.gate_type,
            details={
                "expected": declared_expected,
                "recalled_count": recalled,
                "missed": missed,
                "detected_codes": sorted(detected_codes),
            },
        )


class FalseDefectRateScorer(Scorer):
    """Scores rate of unwarranted defects flagged on compliant golden artifacts."""

    metric_name = "false_defect_rate"
    default_gate_target = 0.05
    gate_type = "max"

    def score(
        self,
        candidate: dict[str, Any],
        case: Case,
        manifest: Mapping[str, Any] | None = None,
        validation_result: ValidationResult | None = None,
        gate_target: float | None = None,
        **kwargs: Any,
    ) -> ScoreResult:
        target = gate_target if gate_target is not None else self.default_gate_target

        # Only golden / compliant reference cases can trigger false defects.
        # Defective or mutated test cases are meant to produce defects.
        is_golden = case.kind == "golden" and not any(
            t.startswith("mutation:") or t.startswith("expected_defect:") for t in case.tags
        )

        if not is_golden:
            return ScoreResult(
                metric=self.metric_name,
                score=0.0,
                passed=True,
                gate_target=target,
                gate_type=self.gate_type,
                details={"status": "not_golden_case"},
            )

        defects = validation_result.defects if validation_result is not None else []
        schema_errors = (
            validation_result.schema_errors if validation_result is not None else []
        )

        false_defects = len(defects) + len(schema_errors)
        # For a single case, 0 false defects -> score 0.0, any false defect -> score 1.0
        score = 1.0 if false_defects > 0 else 0.0
        passed = self.is_passing(score, target)

        return ScoreResult(
            metric=self.metric_name,
            score=score,
            passed=passed,
            gate_target=target,
            gate_type=self.gate_type,
            details={
                "false_defect_count": false_defects,
                "defects": [d.to_dict() for d in defects],
                "schema_errors": [
                    {"path": e.path, "message": e.message} for e in schema_errors
                ],
            },
        )
