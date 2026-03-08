from __future__ import annotations

import time
from pathlib import Path

import lxml.etree as etree

from ...domain.models import (
    Severity,
    ValidationIssue,
    ValidationMetadata,
    ValidationReport,
    ValidationRequest,
)
from .base import BaseValidator, ValidatorError


WARNING_KEYS = (
    "pattern",
    "length",
    "minlength",
    "maxlength",
    "datatype",
    "type",
    "fractiondigits",
    "totaldigits",
    "mininclusive",
    "maxinclusive",
    "minexclusive",
    "maxexclusive",
)

ERROR_KEYS = (
    "missing child element",
    "attribute",
    "is required",
    "not expected",
    "no matching global declaration",
)


def classify_message(message: str) -> Severity:
    text = message.lower()
    for key in ERROR_KEYS:
        if key in text:
            return Severity.ERROR
    for key in WARNING_KEYS:
        if key in text:
            return Severity.WARNING
    return Severity.ERROR


class XsdValidator(BaseValidator):
    name = "xsd"

    def supports(self, request: ValidationRequest) -> bool:
        return bool(request.xml_path and request.xsd_paths)

    def validate(self, request: ValidationRequest) -> ValidationReport:
        start = time.perf_counter()

        if not request.xml_path.exists():
            raise ValidatorError(f"XML no encontrado: {request.xml_path}")
        if not request.xsd_paths:
            raise ValidatorError("Debe indicar al menos un XSD.")

        existing_xsds = [Path(p) for p in request.xsd_paths if Path(p).exists()]
        if not existing_xsds:
            raise ValidatorError("No se encontro ningun XSD valido.")

        try:
            xsd_doc = etree.parse(str(existing_xsds[0]))
            schema = etree.XMLSchema(xsd_doc)
        except (etree.XMLSyntaxError, etree.XMLSchemaParseError) as exc:
            raise ValidatorError(f"No se pudo cargar el XSD: {exc}") from exc

        try:
            xml_doc = etree.parse(str(request.xml_path))
        except etree.XMLSyntaxError as exc:
            raise ValidatorError(f"XML mal formado: {exc}") from exc
        except OSError as exc:
            raise ValidatorError(f"XML mal formateado o inaccesible: {exc}") from exc

        schema.validate(xml_doc)

        issues = []
        for entry in schema.error_log:
            issues.append(
                ValidationIssue(
                    line=entry.line,
                    column=entry.column,
                    message=entry.message,
                    code=entry.type_name,
                    severity=classify_message(entry.message),
                )
            )

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return ValidationReport(
            ok=not issues,
            issues=issues,
            metadata=ValidationMetadata(validator=self.name, elapsed_ms=elapsed_ms),
        )
