#!/usr/bin/env python3
"""善 (Goodness) - JSON 추출 로직 검증."""

import os
import sys
from typing import Any

# Ensure tools/dgm/upstream is in path
sys.path.insert(0, os.path.join(os.getcwd(), "tools/dgm/upstream"))


def test_json_extraction_logic() -> None:
    """JSON 추출 함수의 동작을 테스트 케이스로 검증."""
    try:
        from llm import extract_json_between_markers
    except ImportError as e:
        print(f"Import Error: {e}")
        return

    test_cases: list[tuple[str, dict[str, Any] | None]] = [
        ("No JSON here", None),
        ('```json\n{"key": "value"}\n```', {"key": "value"}),
        ('Random text {"inner": 123} more text', {"inner": 123}),
        ('```json\n{"valid": "json"}\n', {"valid": "json"}),
        ('```json\n{"nested": {"is": "ok"}}\n```', {"nested": {"is": "ok"}}),
    ]

    print("--- 🧠 Metacognitive Logic Proof: JSON Extraction ---")
    pass_count = 0
    for input_text, expected in test_cases:
        actual = extract_json_between_markers(input_text)
        status = "PASSED" if actual == expected else f"FAILED (Got {actual})"
        if actual == expected:
            pass_count += 1
        print(f"Input: {repr(input_text[:30])} | Status: {status}")

    print(f"\nFinal Score: {pass_count}/{len(test_cases)}")


if __name__ == "__main__":
    test_json_extraction_logic()
