"""Core package for XSD Manager validation services."""

from .domain.models import (
    Severity,
    ValidationIssue,
    ValidationMetadata,
    ValidationReport,
    ValidationRequest,
)

__all__ = [
    "Severity",
    "ValidationIssue",
    "ValidationMetadata",
    "ValidationReport",
    "ValidationRequest",
]

