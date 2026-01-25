from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable


FORBIDDEN_PHRASES = [
    "Repairs Complete",
    "완료",
    "completed",
    "implemented",
    "resolved",
    "successfully completed",
    "성공적으로 완료",
]

# Evidence markers. Keep minimal & robust.
EVIDENCE_PATTERNS = [
    r"\bgit\s+commit\b",
    r"\bcommit\s+[0-9a-f]{7,40}\b",
    r"\bdiff\b",
    r"\bfile:\b",
    r"\bline:\b",
    r"\bcommand:\b",
    r"\bpytest\b",
    r"\bmypy\b",
    r"\bruff\b",
    r"\bPASS\b",
    r"\bFAIL\b",
]

# Phrases that indicate analysis-only reporting (allowed)
    "분석",
    "제안",
    "requires verification",
    "need verification",
    "추정",
]


@dataclass(frozen=True)
class Result:
    ok: bool
    reasons: tuple[str, ...]


def _contains_any(text: str, phrases: Iterable[str]) -> list[str]:
    lowered = text.lower()
    return [p for p in phrases if p.lower() in lowered]


def _has_evidence(text: str) -> bool:
    return any(re.search(pat, text, flags=re.IGNORECASE) for pat in EVIDENCE_PATTERNS)


def _is_completion_claim(text: str) -> bool:
    # Treat forbidden phrases as completion claims.
    if _contains_any(text, FORBIDDEN_PHRASES):
        return True
    # Also catch common patterns.
    return bool(re.search(r"\b(done|fixed|shipped|merged)\b", text, flags=re.IGNORECASE))


def validate_report(text: str) -> Result:
    reasons: list[str] = []

    forbidden = _contains_any(text, FORBIDDEN_PHRASES)
    completion_claim = _is_completion_claim(text)

    if forbidden:
        reasons.append(f"Forbidden completion phrase(s): {', '.join(forbidden)}")

    if completion_claim and not _has_evidence(text):
        reasons.append("Completion claim detected but evidence markers are missing.")

    if completion_claim and _has_evidence(text):
        # Still warn if it's only fluffy language with no hard markers
        pass

    ok = len(reasons) == 0
    return Result(ok=ok, reasons=tuple(reasons))


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: python scripts/ssot_report_gate.py '<report text>'")
        return 2

    text = argv[1]
    res = validate_report(text)

    if res.ok:
        print("✅ SSOT Report Gate: PASS")
        return 0

    print("❌ SSOT Report Gate: FAIL")
    for r in res.reasons:
        print(f"- {r}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
