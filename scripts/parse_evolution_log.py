#!/usr/bin/env python3
"""
AFO_EVOLUTION_LOG.md 파서 - Phase별 구조화
진화 기록을 Obsidian/Context7 연동 가능한 형태로 변환
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

EVOLUTION_LOG = Path("AFO_EVOLUTION_LOG.md")
OUTPUT_DIR = Path("data/evolution_structured")

# Phase 패턴 정의
PHASE_PATTERN = re.compile(
    r"###?\s*(?:\[SSOT/)?PH(?:ASE)?[-_]?(\d+)(?:-(\d+))?[:/\]]?\s*[:\s]*(.+?)"
    r"(?:\((\d{4}-\d{2}-\d{2})\))?\s*([🔥💎🛡️⚖️🧠🎨🐳🎫🕯️✂️📓📋👁️💾🧪🔧🔄✅📦🧱🚀📊🌊]+)?"
)
SIMPLE_PATTERN = re.compile(
    r"###\s*Phase\s*(\d+)(?:-(\d+))?:\s*(.+?)"
    r"(?:\((\d{4}-\d{2}-\d{2})\))?\s*([🔥💎🛡️⚖️🧠🎨🐳🎫🕯️✂️📓📋👁️💾🧪🔧🔄✅📦🧱🚀📊🌊]+)?"
)
HEADER_PATTERN = re.compile(r"^###?\s*(?:\[SSOT/)?PH|^###\s*Phase")


def _extract_status(content_lines: list[str]) -> str:
    """콘텐츠에서 상태 추출."""
    content = " ".join(content_lines)
    if "SEALED" in content or "봉인" in content:
        return "SEALED"
    if "PARTIAL" in content or "진행 중" in content:
        return "PARTIAL"
    if "완료" in content or "Completed" in content:
        return "COMPLETED"
    return "UNKNOWN"


def _extract_pillars(content_lines: list[str]) -> dict[str, str]:
    """콘텐츠에서 5기둥 점수 추출."""
    pillars: dict[str, str] = {}
    content = "\n".join(content_lines)
    for pillar in ["Truth", "Goodness", "Beauty", "Serenity", "Eternity"]:
        match = re.search(rf"\*\*{pillar}[^:]*:\*\*\s*(.+)", content)
        if match:
            pillars[pillar] = match.group(1).strip()
    return pillars


def _parse_phase_match(
    match: re.Match[str], lines: list[str], start_idx: int
) -> tuple[dict[str, Any], int]:
    """Phase 매치 결과를 파싱하여 Phase 정보와 다음 인덱스 반환."""
    phase_num = match.group(1)
    phase_end = match.group(2) or phase_num
    title = (match.group(3) or "Unknown").strip()
    date = match.group(4)
    emoji = match.group(5) if match.lastindex and match.lastindex >= 5 else ""

    # 다음 Phase까지 내용 수집
    content_lines: list[str] = []
    idx = start_idx + 1
    while idx < len(lines):
        if HEADER_PATTERN.search(lines[idx]):
            break
        content_lines.append(lines[idx])
        idx += 1

    phase_info = {
        "phase": phase_num if phase_num == phase_end else f"{phase_num}-{phase_end}",
        "title": title.replace("**", "").strip(),
        "date": date,
        "emoji": emoji or "",
        "status": _extract_status(content_lines),
        "pillars": _extract_pillars(content_lines),
        "content_preview": " ".join(content_lines[:5])[:300],
    }
    return phase_info, idx


def _deduplicate_phases(phases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """중복 Phase 제거."""
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for p in phases:
        key = f"{p['phase']}_{p['title']}"
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def _generate_summary(phases: list[dict[str, Any]]) -> dict[str, Any]:
    """Phase 목록에서 요약 통계 생성."""
    status_counts: dict[str, int] = {}
    for p in phases:
        status_counts[p["status"]] = status_counts.get(p["status"], 0) + 1

    dates = [p["date"] for p in phases if p["date"]]
    return {
        "total_phases": len(phases),
        "status_distribution": status_counts,
        "date_range": {
            "earliest": min(dates, default=None),
            "latest": max(dates, default=None),
        },
        "phases_with_pillars": len([p for p in phases if p["pillars"]]),
    }


def parse_evolution_log() -> dict[str, Any]:
    """진화 로그 파싱 (메인 함수)."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    content = EVOLUTION_LOG.read_text(encoding="utf-8")
    lines = content.split("\n")

    phases: list[dict[str, Any]] = []
    i = 0
    while i < len(lines):
        match = SIMPLE_PATTERN.search(lines[i]) or PHASE_PATTERN.search(lines[i])
        if match:
            phase_info, i = _parse_phase_match(match, lines, i)
            phases.append(phase_info)
        else:
            i += 1

    unique_phases = _deduplicate_phases(phases)
    summary = _generate_summary(unique_phases)

    # 결과 저장
    result = {
        "parsed_at": datetime.now().isoformat(),
        "total_phases": len(unique_phases),
        "phases": unique_phases,
    }

    (OUTPUT_DIR / "evolution_phases.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (OUTPUT_DIR / "evolution_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # 출력
    print("✅ 진화 로그 파싱 완료!")
    print(f"   - 총 Phase: {len(unique_phases)}개")
    print("\n📊 상태 분포:")
    for status, count in summary["status_distribution"].items():
        print(f"   - {status}: {count}")
    print(f"\n📅 기간: {summary['date_range']['earliest']} ~ {summary['date_range']['latest']}")

    return result


if __name__ == "__main__":
    parse_evolution_log()
