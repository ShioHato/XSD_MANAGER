from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Sequence


class Severity(str, Enum):
    ERROR = "ERROR"
    WARNING = "AVISO"
    INFO = "INFO"


@dataclass
class ValidationIssue:
    line: int
    column: int
    message: str
    severity: Severity = Severity.ERROR
    code: Optional[str] = None
    rule: Optional[str] = None

    @property
    def level(self) -> str:
        return self.severity.value


@dataclass
class ValidationRequest:
    xml_path: Path
    xsd_paths: Sequence[Path]
    strict: bool = False


@dataclass
class ValidationMetadata:
    validator: str
    elapsed_ms: float


@dataclass
class ValidationReport:
    ok: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    metadata: Optional[ValidationMetadata] = None

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == Severity.ERROR for issue in self.issues)

