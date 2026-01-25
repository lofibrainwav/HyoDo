# Copyright (c) 2025 AFO Kingdom
# English ratio detector for AFO Kingdom reports.
#
# This script analyzes markdown files in docs/reports/ to detect
# English-heavy content that should prefer Korean for collaboration.

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

# Constants
MIN_ARGS_REQUIRED = 2
ENGLISH_THRESHOLD = 0.50

ENG_WORD_RE = re.compile(r"\b[a-zA-Z]{3,}\b")
HANGUL_RE = re.compile(r"[가-힣]")
CODE_FENCE_RE = re.compile(r"^\s*```")

# Constants for English ratio detection


def _iter_text_lines(text: str) -> Iterable[str]:
    in_code = False
    for line in text.splitlines():
        if CODE_FENCE_RE.match(line):
            in_code = not in_code
            continue
        if in_code:
            continue
        yield line


def english_heavy_ratio(text: str) -> float:
    lines = [ln.strip() for ln in _iter_text_lines(text)]
    lines = [ln for ln in lines if ln]
    if not lines:
        return 0.0

    eng_only = 0
    for ln in lines:
        has_eng = bool(ENG_WORD_RE.search(ln))
        has_ko = bool(HANGUL_RE.search(ln))
        if has_eng and not has_ko:
            eng_only += 1
    return eng_only / len(lines)


def main() -> int:
    if len(sys.argv) < MIN_ARGS_REQUIRED:
        print("Usage: python scripts/detect_english_ratio.py <file1> [file2 ...]")
        return MIN_ARGS_REQUIRED

    flagged = []
    for arg in sys.argv[1:]:
        p = Path(arg)
        if not p.exists() or not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        ratio = english_heavy_ratio(text)
        if ratio >= ENGLISH_THRESHOLD:
            flagged.append({"file": str(p), "english_ratio": round(ratio, 3)})

    out = {"flagged": flagged, "threshold": ENGLISH_THRESHOLD, "count": len(flagged)}
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
