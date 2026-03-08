from __future__ import annotations

from typing import Iterable, List

from ...domain.models import ValidationIssue, ValidationRequest, ValidationReport
from ..validators.base import BaseValidator


class ValidationUseCase:
    """Run one or more validators over a validation request."""

    def __init__(self, validators: Iterable[BaseValidator]) -> None:
        self.validators = list(validators)

    def run(self, request: ValidationRequest) -> ValidationReport:
        issues: List[ValidationIssue] = []
        ok = True

        for validator in self.validators:
            if not validator.supports(request):
                continue
            report = validator.validate(request)
            issues.extend(report.issues)
            ok = ok and report.ok

        return ValidationReport(ok=ok, issues=issues)
