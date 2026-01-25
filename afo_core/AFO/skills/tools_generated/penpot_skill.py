from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class ToolSkillResult:
    tool_id: str
    pillar: str
    status: str
    score: int
    evidence: str


def run(repo_root: Path) -> dict:
    # Auto-generated evidence candidates
    candidates = [repo_root / "artifacts/penpot-health.json"]

    # Find first existing evidence
    hit = next((p for p in candidates if p.exists()), None)

    if hit and hit.stat().st_size > 0:
        # Resolve relative path for cleaner output if possible
        try:
            rel = str(hit.relative_to(repo_root))
        except ValueError:
            rel = str(hit)

        return asdict(ToolSkillResult("penpot", "beauty", "healthy", 90, rel))

    # Fail Loud if no evidence
    return asdict(ToolSkillResult("penpot", "beauty", "unhealthy", 10, "missing"))
