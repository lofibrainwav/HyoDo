"""
Diagram Validator Models - Data classes for validation results

Contains:
- ValidationSeverity: Issue severity levels
- ValidationIssue: Single validation issue
- ValidationResult: Result of diagram validation
- ValidationSummary: Summary of all validations
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ValidationSeverity(str, Enum):
    """Validation issue severity levels."""

    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class ValidationIssue:
    """Single validation issue."""

    severity: ValidationSeverity
    message: str
    file_path: str | None = None
    element_id: str | None = None
    line_number: int | None = None

    def __str__(self) -> str:
        location = ""
        if self.file_path:
            location += f"{self.file_path}"
        if self.element_id:
            location += f" [element: {self.element_id}]"
        if location:
            location += ": "
        return f"[{self.severity.value}] {location}{self.message}"


@dataclass
class ValidationResult:
    """Result of diagram validation."""

    file_path: Path
    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    schema_valid: bool = True
    semantic_valid: bool = True
    naming_valid: bool = True
    pillar_nodes_found: list[str] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING)


@dataclass
class ValidationSummary:
    """Summary of all validations."""

    total_files: int = 0
    passed_files: int = 0
    failed_files: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    results: list[ValidationResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return self.failed_files == 0
