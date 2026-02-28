import argparse
import sys
from dataclasses import dataclass

import lxml.etree as etree


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


@dataclass
class ValidationIssue:
    level: str
    line: int
    column: int
    message: str


def classify_message(message: str) -> str:
    text = message.lower()

    for key in ERROR_KEYS:
        if key in text:
            return "ERROR"

    for key in WARNING_KEYS:
        if key in text:
            return "AVISO"

    return "ERROR"


def validate(xml_path: str, xsd_path: str) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    try:
        xsd_doc = etree.parse(xsd_path) 
        schema = etree.XMLSchema(xsd_doc) 
    except (etree.XMLSyntaxError, etree.XMLSchemaParseError) as exc: 
        raise RuntimeError(f"No se pudo cargar el XSD: {exc}") from exc

    try:
        xml_doc = etree.parse(xml_path) 
    except etree.XMLSyntaxError as exc: 
        raise RuntimeError(f"XML mal formado: {exc}") from exc

    schema.validate(xml_doc)

    for entry in schema.error_log:
        level = classify_message(entry.message)
        issues.append(
            ValidationIssue(
                level=level,
                line=entry.line,
                column=entry.column,
                message=entry.message,
            )
        )

    return issues


def print_report(issues: list[ValidationIssue]) -> int:
    if not issues:
        print("OK: El XML cumple el XSD sin errores ni avisos.")
        return 0

    errors = [i for i in issues if i.level == "ERROR"]
    warnings = [i for i in issues if i.level == "AVISO"]

    if errors:
        print(f"ERRORES ({len(errors)}):")
        for e in errors:
            print(f"  - Linea {e.line}, Columna {e.column}: {e.message}")

    if warnings:
        print(f"AVISOS ({len(warnings)}):")
        for w in warnings:
            print(f"  - Linea {w.line}, Columna {w.column}: {w.message}")

    return 2 if errors else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida un XML contra un XSD y clasifica incidencias en ERROR/AVISO."
    )
    parser.add_argument("xml", help="Ruta al archivo XML")
    parser.add_argument("xsd", help="Ruta al archivo XSD")
    args = parser.parse_args()

    try:
        issues = validate(args.xml, args.xsd)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 2

    return print_report(issues)


if __name__ == "__main__":
    sys.exit(main())
