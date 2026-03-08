from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from xsd_manager.services.validation.use_case import ValidationUseCase
    from xsd_manager.services.validators.base import ValidatorError
    from xsd_manager.services.validators.xsd_validator import (
        ERROR_KEYS,
        classify_message as _classify_message,
        WARNING_KEYS,
        XsdValidator,
    )
    from xsd_manager.domain.models import ValidationIssue, ValidationRequest
except ModuleNotFoundError:
    from src.xsd_manager.services.validation.use_case import ValidationUseCase
    from src.xsd_manager.services.validators.base import ValidatorError
    from src.xsd_manager.services.validators.xsd_validator import (
        ERROR_KEYS,
        classify_message as _classify_message,
        WARNING_KEYS,
        XsdValidator,
    )
    from src.xsd_manager.domain.models import ValidationIssue, ValidationRequest


def classify_message(message: str) -> str:
    return _classify_message(message).value


def validate(xml_path: str, xsd_path: str) -> list[ValidationIssue]:
    request = ValidationRequest(
        xml_path=Path(xml_path),
        xsd_paths=[Path(xsd_path)],
    )
    use_case = ValidationUseCase(validators=[XsdValidator()])

    try:
        report = use_case.run(request)
    except ValidatorError as exc:
        raise RuntimeError(str(exc)) from exc

    return report.issues


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
    raise SystemExit(main())
