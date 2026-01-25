"""Tax Classification Rules.

문서 내용에 기반한 세금 서류 카테고리 분류 규칙.
"""

from __future__ import annotations

import re


def classify_primary_category(content: str) -> str:
    """문서 내용에서 1차 카테고리를 식별합니다."""
    rules = [
        (r"W-2|Wage and Tax Statement", "Income"),
        (r"1099-MISC|1099-NEC", "Business Income"),
        (r"1040|U.S. Individual Income Tax Return", "Tax Return"),
        (r"Invoice|Receipt", "Expense"),
        (r"Bank Statement", "Financial"),
    ]

    for pattern, category in rules:
        if re.search(pattern, content, re.IGNORECASE):
            return category
    return "Unknown"


def classify_subcategory(content: str, primary: str) -> str:
    """1차 카테고리 내에서 세부 유형을 식별합니다."""
    if primary == "Income":
        if "W-2G" in content:
            return "Gambling Winnings"
        return "Employment"
    elif primary == "Expense":
        if "Meal" in content:
            return "Entertainment"
        if "Travel" in content:
            return "Business Travel"
    return "General"


def has_excluded_patterns(content: str) -> bool:
    """분류에서 제외할 시스템/로그 패턴이 있는지 확인합니다."""
    excluded = [r"DEBUG", r"SYSTEM_LOG", r"IGNORE_THIS"]
    return any(re.search(p, content) for p in excluded)
