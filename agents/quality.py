"""Quality Agents - Standalone Implementation for HyoDo.

Provides code quality checking agents without external dependencies.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class QualityLevel(Enum):
    """Code quality levels."""

    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    NEEDS_IMPROVEMENT = "needs_improvement"
    CRITICAL = "critical"


@dataclass
class QualityResult:
    """Result of a quality check."""

    level: QualityLevel
    score: float
    issues: list[str]
    suggestions: list[str]


class QualityScoutAgent:
    """Scout agent for initial code quality assessment."""

    name = "QualityScout"
    description = "빠른 코드 품질 스캔"

    async def analyze(self, code: str) -> QualityResult:
        """Analyze code quality."""
        issues: list[str] = []
        suggestions: list[str] = []

        # Basic checks
        lines = code.split("\n")
        if len(lines) > 500:
            issues.append("파일이 500줄을 초과합니다")
            suggestions.append("파일을 더 작은 모듈로 분리하세요")

        # Calculate score
        score = 100.0
        score -= len(issues) * 10

        level = QualityLevel.EXCELLENT
        if score < 90:
            level = QualityLevel.GOOD
        if score < 80:
            level = QualityLevel.ACCEPTABLE
        if score < 70:
            level = QualityLevel.NEEDS_IMPROVEMENT
        if score < 50:
            level = QualityLevel.CRITICAL

        return QualityResult(
            level=level,
            score=max(0, score),
            issues=issues,
            suggestions=suggestions,
        )


class FastRuffAgent:
    """Fast Ruff linting agent."""

    name = "FastRuff"
    description = "빠른 Ruff 린팅"

    async def lint(self, file_path: str) -> dict[str, Any]:
        """Run Ruff linting on a file."""
        import subprocess

        try:
            result = subprocess.run(
                ["ruff", "check", file_path, "--output-format=json"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr,
            }
        except FileNotFoundError:
            return {
                "success": False,
                "output": "",
                "errors": "Ruff not installed",
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "errors": "Timeout",
            }


# Singleton instances
quality_scout_agent = QualityScoutAgent()
fast_ruff_agent = FastRuffAgent()

# Agent list for fast checks
FAST_CHECK_AGENTS = [quality_scout_agent, fast_ruff_agent]

__all__ = [
    "QualityLevel",
    "QualityResult",
    "QualityScoutAgent",
    "FastRuffAgent",
    "quality_scout_agent",
    "fast_ruff_agent",
    "FAST_CHECK_AGENTS",
]
