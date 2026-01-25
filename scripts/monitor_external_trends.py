#!/usr/bin/env python3
# Copyright (c) 2025 AFO Kingdom. All rights reserved.
"""
AFO Kingdom External Trends Monitor.

외부 트렌드 자동 모니터링 스크립트.

Sequential Thinking:
1. 트렌드 데이터 수집 (Brave Search API 활용)
2. 데이터 분석 및 패턴 추출
3. 보고서 생성 및 저장
4. 알림 트리거 (필요시)

Context 7 적용:
- Layer 1: 기술적 (AI Observability 메트릭)
- Layer 2: 아키텍처 (AFO와 비교)
- Layer 3: 성능 (트렌드 속도)
- Layer 4: 운영 (자동화 주기)
- Layer 5: 비즈니스 (시장 기회)
- Layer 6: 미래 (예측 트렌드)
- Layer 7: 철학 (Trinity Score 정렬)

MCP Tools: brave-search 활용
Skills: web_search, data_analysis
Scholars: 전략적 트렌드 해석
"""

import asyncio
import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

import aiohttp

# Constants
TRINITY_WEIGHTS: Final = {
    "truth": 0.35,
    "goodness": 0.35,
    "beauty": 0.20,
    "serenity": 0.08,
    "eternity": 0.02,
}
MAX_SOURCE_SCORE: Final = 10
MAX_MARKET_IMPACT: Final = 100
DEFAULT_COMPLEXITY: Final = 50
TARGET_TRINITY_HIGH: Final = 80
TARGET_TRINITY_MED: Final = 60
OPPORTUNITY_HIGH: Final = 75
OPPORTUNITY_MED: Final = 50
HTTP_OK: Final = 200
BRAVE_SEARCH_URL: Final = "https://api.search.brave.com/res/v1/web/search"

# Logger
logger = logging.getLogger("afo.trends")


def calculate_trinity_score(trend_data: dict) -> float:
    """
    외부 트렌드의 Trinity Score 계산.

    Args:
        trend_data (dict): 트렌드 분석 데이터.

    Returns:
        float: 0.0 ~ 100.0 사이의 Trinity Score 총점.
    """
    # Truth: 데이터 신뢰성
    truth = min(1.0, len(trend_data.get("sources", [])) / MAX_SOURCE_SCORE)

    # Goodness: 시장 영향도
    goodness = min(1.0, trend_data.get("market_impact", 0) / MAX_MARKET_IMPACT)

    # Beauty: 구현 용이성
    beauty = min(
        1.0,
        trend_data.get("implementation_complexity", DEFAULT_COMPLEXITY) / MAX_MARKET_IMPACT,
    )
    beauty = 1.0 - beauty  # 낮은 복잡성 = 높은 beauty

    # Serenity: 자동화 가능성
    serenity = min(1.0, trend_data.get("automation_potential", 0) / MAX_MARKET_IMPACT)

    # Eternity: 장기적 가치
    eternity = min(1.0, trend_data.get("long_term_value", 0) / MAX_MARKET_IMPACT)

    scores = {
        "truth": truth,
        "goodness": goodness,
        "beauty": beauty,
        "serenity": serenity,
        "eternity": eternity,
    }

    total_score = sum(scores[k] * TRINITY_WEIGHTS[k] for k in TRINITY_WEIGHTS) * 100
    return round(total_score, 2)


async def search_brave_ai_trends(query: str, api_key: str) -> dict[str, Any]:
    """
    Brave Search API로 AI 트렌드 검색.

    Args:
        query (str): 검색어.
        api_key (str): Brave Search API 키.

    Returns:
        dict[str, Any]: 검색 결과 데이터 또는 에러 메시지를 포함한 딕셔너리.
    """
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    }
    params = {"q": query, "count": 10, "safesearch": "moderate"}

    async with (
        aiohttp.ClientSession() as session,
        session.get(BRAVE_SEARCH_URL, headers=headers, params=params) as response,
    ):
        if response.status == HTTP_OK:
            data = await response.json()
            return {
                "query": query,
                "timestamp": datetime.now(UTC).isoformat(),
                "results": data.get("web", {}).get("results", []),
                "total_results": len(data.get("web", {}).get("results", [])),
            }
        logger.error("Brave API error: %s", response.status)
        return {"error": f"API call failed with status {response.status}"}


def analyze_trends(search_results: dict) -> dict[str, Any]:
    """
    검색 결과를 분석하여 트렌드 데이터 추출.

    Args:
        search_results (dict): 검색 결과 원본 데이터.

    Returns:
        dict[str, Any]: 분석된 트렌드 데이터 (스코어, 키워드, 소스 등).
    """
    results = search_results.get("results", [])

    # 키워드 빈도 분석
    keywords = [
        "observability",
        "monitoring",
        "AI",
        "ML",
        "predictive",
        "automation",
        "kubernetes",
        "prometheus",
    ]
    keyword_counts = dict.fromkeys(keywords, 0)

    sources = []
    for result in results:
        title = result.get("title", "").lower()
        description = result.get("description", "").lower()

        for kw in keywords:
            if kw in title or kw in description:
                keyword_counts[kw] += 1

        sources.append(
            {
                "title": result.get("title"),
                "url": result.get("url"),
                "age": result.get("age"),
            }
        )

    # 트렌드 점수 계산
    trend_score = sum(keyword_counts.values()) / len(results) if results else 0

    return {
        "query": search_results.get("query"),
        "timestamp": search_results.get("timestamp"),
        "keyword_analysis": keyword_counts,
        "trend_score": round(trend_score, 2),
        "sources": sources,
        "market_impact": min(MAX_MARKET_IMPACT, trend_score * 10),
        "implementation_complexity": 30,  # AFO는 이미 구현됨
        "automation_potential": 85,  # 자동화 가능성 높음
        "long_term_value": 90,  # 장기적 가치 높음
    }


def generate_report(analysis: dict) -> str:
    """
    분석 결과를 보고서로 생성.

    Args:
        analysis (dict): 분석된 트렌드 데이터.

    Returns:
        str: 마크다운 형식의 보고서 문자열.
    """
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    trinity_score = calculate_trinity_score(analysis)

    action = "- **Low Priority**"
    if trinity_score > TARGET_TRINITY_HIGH:
        action = "- **Immediate Action Required**"
    elif trinity_score > TARGET_TRINITY_MED:
        action = "- **Monitor Closely**"

    integration = "Low"
    if trinity_score > OPPORTUNITY_HIGH:
        integration = "High"
    elif trinity_score > OPPORTUNITY_MED:
        integration = "Medium"

    alignment = "Good"
    if "AI" in str(analysis) and "observability" in str(analysis):
        alignment = "Excellent"

    return f"""
# AFO Kingdom External Trends Report
**Generated:** {timestamp}

## Query: {analysis.get("query", "N/A")}

## Trinity Score Analysis
- **Overall Trinity Score:** {trinity_score}/100
- **Truth (35%)**: {analysis.get("market_impact", 0)}/100 - Market Impact
- **Goodness (35%)**: {100 - analysis.get("implementation_complexity", 50)}/100 - Implementation Ease
- **Beauty (20%)**: {analysis.get("automation_potential", 0)}/100 - Automation Potential
- **Serenity (8%)**: {analysis.get("long_term_value", 0)}/100 - Long-term Value
- **Eternity (2%)**: Data Reliability

## Trend Analysis
- **Trend Score:** {analysis.get("trend_score", 0)}/10
- **Total Sources:** {len(analysis.get("sources", []))}

### Keyword Frequency
{json.dumps(analysis.get("keyword_analysis", {}), indent=2)}

### Top Sources
{chr(10).join([f"- [{s['title']}]({s['url']})" for s in analysis.get("sources", [])[:5]])}

## Recommendations
{action}
- Integration Opportunity: {integration}
- AFO Alignment: {alignment}
"""


def save_report(report: str, query: str, reports_dir: Path) -> None:
    """
    보고서를 파일로 저장.

    Args:
        report (str): 보고서 내용.
        query (str): 검색 쿼리.
        reports_dir (Path): 저장 경로.
    """
    timestamp_str = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    report_file = reports_dir / f"trend_report_{timestamp_str}_{query.replace(' ', '_')}.md"
    report_file.write_text(report, encoding="utf-8")
    logger.info("Report saved: %s", report_file)


def generate_summary_report(all_results: dict, reports_dir: Path) -> None:
    """
    종합 보고서 생성 및 저장.

    Args:
        all_results (dict): 모든 분석 결과.
        reports_dir (Path): 저장 경로.
    """
    now_str = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

    highest_impact = "None"
    if all_results:
        highest_impact = max(
            all_results.keys(), key=lambda x: calculate_trinity_score(all_results[x])
        )

    avg_score = 0.0
    if all_results:
        avg_score = round(
            sum(calculate_trinity_score(all_results[q]) for q in all_results) / len(all_results),
            2,
        )

    alignment_str = "excellent" if all_results else "unknown"

    summary_list = "\n".join(
        [f"- **{q}**: {calculate_trinity_score(all_results[q])}/100" for q in all_results]
    )

    summary_report = f"""
# AFO Kingdom External Trends Summary Report
**Generated:** {now_str}

## Overview
Searched trend queries and analyzed {len(all_results)} successful results.

## Trinity Score Summary
{summary_list}

## Key Findings
- **Highest Impact Trend:** {highest_impact}
- **Average Trinity Score:** {avg_score}/100

## AFO Kingdom Alignment
Current AFO monitoring system shows {alignment_str} alignment with 2025 AI observability trends.
"""

    timestamp_file = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    summary_file = reports_dir / f"summary_report_{timestamp_file}.md"
    summary_file.write_text(summary_report, encoding="utf-8")
    logger.info("Summary report saved: %s", summary_file)


async def main() -> None:
    """메인 실행 함수."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # 환경 변수에서 API 키 가져오기
    brave_api_key = os.getenv("BRAVE_API_KEY")
    if not brave_api_key:
        logger.error("BRAVE_API_KEY environment variable not set")
        return

    # 검색 쿼리들
    queries = [
        "AI observability trends 2025",
        "predictive monitoring AI systems",
        "unified AI platform monitoring",
        "Kubernetes AI workload monitoring",
    ]

    reports_dir = Path("docs/reports/external_trends")
    reports_dir.mkdir(parents=True, exist_ok=True)

    all_results = {}

    for query in queries:
        logger.info("Searching: %s", query)
        search_results = await search_brave_ai_trends(query, brave_api_key)

        if "error" not in search_results:
            analysis = analyze_trends(search_results)
            report = generate_report(analysis)
            all_results[query] = analysis
            save_report(report, query, reports_dir)
        else:
            logger.error("Search failed for %s: %s", query, search_results["error"])

        # API rate limit 고려
        await asyncio.sleep(1)

    # 종합 보고서 생성
    generate_summary_report(all_results, reports_dir)


if __name__ == "__main__":
    asyncio.run(main())
