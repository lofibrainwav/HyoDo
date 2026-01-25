#!/usr/bin/env python3
"""
log_chunks 분석기 - 캐시를 DNA로 변환
103,739개 에러 로그를 패턴별로 분류하고 임베딩 가능한 형태로 변환
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

LOG_CHUNKS_DIR = Path("log_chunks")
OUTPUT_DIR = Path("data/log_embeddings")

# 에러 패턴 분류
PATTERNS = {
    "module_not_found": r"ModuleNotFoundError|No module named",
    "import_error": r"ImportError|cannot import name",
    "sentry_error": r"Sentry|sentry_sdk",
    "redis_error": r"Redis|redis",
    "postgres_error": r"PostgreSQL|postgres|pg_",
    "playwright_error": r"playwright",
    "port_in_use": r"address already in use|Errno 48",
    "type_error": r"TypeError|type error",
    "attribute_error": r"AttributeError",
    "key_error": r"KeyError",
    "success": r"✅|SUCCESS|successfully|완료",
    "warning": r"⚠️|WARNING|경고",
    "info": r"INFO|정보",
}


def classify_line(line: str) -> str:
    """로그 라인을 패턴별로 분류"""
    for pattern_name, pattern in PATTERNS.items():
        if re.search(pattern, line, re.IGNORECASE):
            return pattern_name
    return "unknown"


def extract_timestamp(line: str) -> str | None:
    """타임스탬프 추출"""
    match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
    return match.group(1) if match else None


def analyze_chunks():
    """모든 청크 분석"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    stats = {
        "total_lines": 0,
        "total_chunks": 0,
        "patterns": defaultdict(int),
        "timeline": defaultdict(list),
        "modules_failed": defaultdict(int),
        "services_status": defaultdict(lambda: {"success": 0, "error": 0}),
    }

    embeddings = []

    for chunk_file in sorted(LOG_CHUNKS_DIR.glob("chunk_*.json")):
        with open(chunk_file) as f:
            chunk = json.load(f)

        chunk_id = chunk["chunk_id"]
        lines = chunk.get("lines", [])
        stats["total_chunks"] += 1

        for line in lines:
            stats["total_lines"] += 1
            pattern = classify_line(line)
            stats["patterns"][pattern] += 1

            # 실패한 모듈 추출
            if pattern == "module_not_found":
                match = re.search(r"No module named ['\"]?([^'\"]+)", line)
                if match:
                    stats["modules_failed"][match.group(1)] += 1

            # 서비스 상태 추적
            if "✅" in line or "successfully" in line.lower():
                service_match = re.search(r"(\w+(?:Service|Engine|Router|Cache))", line)
                if service_match:
                    stats["services_status"][service_match.group(1)]["success"] += 1
            elif "ERROR" in line or "❌" in line:
                service_match = re.search(r"(\w+(?:Service|Engine|Router|Cache))", line)
                if service_match:
                    stats["services_status"][service_match.group(1)]["error"] += 1

            # 임베딩용 데이터 생성
            timestamp = extract_timestamp(line)
            if pattern in ["module_not_found", "import_error", "port_in_use", "sentry_error"]:
                embeddings.append(
                    {
                        "chunk_id": chunk_id,
                        "timestamp": timestamp,
                        "pattern": pattern,
                        "content": line[:500],  # 500자 제한
                        "severity": "error" if pattern != "success" else "info",
                    }
                )

    # 통계 저장
    final_stats = {
        "analyzed_at": datetime.now().isoformat(),
        "total_lines": stats["total_lines"],
        "total_chunks": stats["total_chunks"],
        "pattern_distribution": dict(stats["patterns"]),
        "top_failed_modules": dict(
            sorted(stats["modules_failed"].items(), key=lambda x: -x[1])[:20]
        ),
        "services_status": {k: dict(v) for k, v in stats["services_status"].items()},
    }

    with open(OUTPUT_DIR / "log_analysis_stats.json", "w") as f:
        json.dump(final_stats, f, indent=2, ensure_ascii=False)

    # 임베딩 데이터 저장 (청크 단위)
    chunk_size = 100
    for i in range(0, len(embeddings), chunk_size):
        chunk_embeddings = embeddings[i : i + chunk_size]
        with open(OUTPUT_DIR / f"embeddings_{i // chunk_size:04d}.json", "w") as f:
            json.dump(chunk_embeddings, f, indent=2, ensure_ascii=False)

    print(f"✅ 분석 완료!")
    print(f"   - 총 라인: {stats['total_lines']:,}")
    print(f"   - 총 청크: {stats['total_chunks']:,}")
    print(f"   - 임베딩 데이터: {len(embeddings):,}개")
    print(f"\n📊 패턴 분포:")
    for pattern, count in sorted(stats["patterns"].items(), key=lambda x: -x[1])[:10]:
        print(f"   - {pattern}: {count:,}")

    print(f"\n🔥 자주 실패한 모듈 (Top 10):")
    for module, count in list(stats["modules_failed"].items())[:10]:
        print(f"   - {module}: {count}")

    return final_stats


if __name__ == "__main__":
    analyze_chunks()
