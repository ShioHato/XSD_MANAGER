from __future__ import annotations

from abc import ABC, abstractmethod

from ...domain.models import ValidationIssue, ValidationRequest, ValidationReport


class ValidatorError(RuntimeError):
    """Domain-level validation error."""


class BaseValidator(ABC):
    """Interface for all validators."""

    name = "base"

    @abstractmethod
    def supports(self, request: ValidationRequest) -> bool:
        """Return True when this validator can handle the request."""

    @abstractmethod
    def validate(self, request: ValidationRequest) -> ValidationReport:
        """Validate request and return a report."""

    def classify_exception(self, error: Exception) -> list[ValidationIssue]:
        del error
        return []
