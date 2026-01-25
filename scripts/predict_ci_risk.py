from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class Signal:
    name: str
    score: int
    reason: str


HIGH_RISK_PATH_PREFIXES = (
    "packages/afo-core/",
    "packages/dashboard/",
    "AFO/api/",
    "monitoring/",
    "k8s/",
    "packages/afo-core/k8s/",
    ".github/workflows/",
)

MED_RISK_PATH_PREFIXES = ("scripts/", "docs/")

HIGH_RISK_FILE_KEYWORDS = (
    "llm_router",
    "learning_engine",
    "persona_graph",
    "chancellor",
    "cache",
    "auth",
)

TEST_KEYWORDS = ("test", "pytest", "mypy", "ruff", "lint")


def _run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()


def get_changed_files(diff_base: str) -> list[str]:
    out = _run(["git", "diff", "--name-only", f"{diff_base}...HEAD"])
    return [line for line in out.splitlines() if line.strip()]


def score_changed_files(files: list[str]) -> tuple[int, list[Signal]]:
    signals: list[Signal] = []

    n = len(files)
    if n >= 80:
        signals.append(Signal("large_change_set", 40, f"Changed files={n}"))
    elif n >= 40:
        signals.append(Signal("medium_change_set", 25, f"Changed files={n}"))
    elif n >= 15:
        signals.append(Signal("small_change_set", 12, f"Changed files={n}"))
    elif n >= 1:
        signals.append(Signal("tiny_change_set", 5, f"Changed files={n}"))

    high_hits = []
    med_hits = []
    workflow_touched = False

    for f in files:
        if f.startswith(".github/workflows/"):
            workflow_touched = True

        if any(f.startswith(p) for p in HIGH_RISK_PATH_PREFIXES):
            high_hits.append(f)
        elif any(f.startswith(p) for p in MED_RISK_PATH_PREFIXES):
            med_hits.append(f)

        lower = f.lower()
        if any(k in lower for k in HIGH_RISK_FILE_KEYWORDS):
            signals.append(Signal("core_keyword_touched", 15, f"Keyword hit in {f}"))

        if any(k in lower for k in TEST_KEYWORDS):
            signals.append(
                Signal("tests_or_quality_changed", 6, f"Test/quality tooling touched: {f}")
            )

    if workflow_touched:
        signals.append(Signal("workflow_changed", 18, "GitHub Actions workflows touched"))

    if high_hits:
        signals.append(Signal("high_risk_area", 22, f"High-risk area files={len(high_hits)}"))
    if med_hits and not high_hits:
        signals.append(Signal("medium_risk_area", 10, f"Medium-risk area files={len(med_hits)}"))

    keyword_signals = [s for s in signals if s.name == "core_keyword_touched"]
    if len(keyword_signals) > 3:
        keep = keyword_signals[:3]
        signals = [s for s in signals if s.name != "core_keyword_touched"] + keep

    total = min(sum(s.score for s in signals), 100)
    return total, signals


def main() -> int:
    diff_base = os.environ.get("DIFF_BASE")
    if not diff_base:
        print(json.dumps({"error": "DIFF_BASE env var required"}, ensure_ascii=False))
        return 2

    files = get_changed_files(diff_base)
    score, signals = score_changed_files(files)

    payload = {
        "risk_score": score,
        "changed_files_count": len(files),
        "top_signals": [
            {"name": s.name, "score": s.score, "reason": s.reason} for s in signals[:10]
        ],
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
