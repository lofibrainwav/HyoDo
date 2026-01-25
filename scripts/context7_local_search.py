#!/usr/bin/env python3
"""
Context7 로컬 검색기 - AFO Kingdom 지식베이스 검색
외부 Context7 대신 로컬 문서를 검색하는 도구
"""

import json
from pathlib import Path
from typing import Optional

DOCS_PATH = Path("data/context7_local/afo_kingdom_docs.json")


def load_docs() -> dict:
    """문서 로드"""
    if not DOCS_PATH.exists():
        return {}
    with open(DOCS_PATH) as f:
        return json.load(f)


def search(query: str, topic: Optional[str] = None) -> dict:
    """
    AFO Kingdom 지식베이스 검색

    Args:
        query: 검색어
        topic: 특정 토픽 (onboarding, architecture, api, cache_dna, phase_history, mcp_servers, banana_philosophy, quick_start)

    Returns:
        검색 결과
    """
    docs = load_docs()
    if not docs:
        return {"error": "문서를 찾을 수 없습니다"}

    results = []
    query_lower = query.lower()

    topics = docs.get("topics", {})

    # 특정 토픽 검색
    if topic and topic in topics:
        t = topics[topic]
        results.append(
            {
                "topic": topic,
                "title": t["title"],
                "content": t["content"],
                "keywords": t["keywords"],
                "relevance": 1.0,
            }
        )
    else:
        # 전체 검색
        for topic_id, t in topics.items():
            # 키워드 매칭
            keyword_match = any(
                kw.lower() in query_lower or query_lower in kw.lower()
                for kw in t.get("keywords", [])
            )
            # 내용 매칭
            content_match = query_lower in t.get("content", "").lower()
            # 제목 매칭
            title_match = query_lower in t.get("title", "").lower()

            if keyword_match or content_match or title_match:
                relevance = 0.0
                if title_match:
                    relevance += 0.5
                if keyword_match:
                    relevance += 0.3
                if content_match:
                    relevance += 0.2

                results.append(
                    {
                        "topic": topic_id,
                        "title": t["title"],
                        "content": t["content"],
                        "keywords": t["keywords"],
                        "relevance": relevance,
                    }
                )

    # 관련도 순 정렬
    results.sort(key=lambda x: -x["relevance"])

    return {
        "library": docs.get("name", "AFO Kingdom"),
        "version": docs.get("version", "Unknown"),
        "query": query,
        "results": results[:5],  # 상위 5개
        "total": len(results),
        "code_snippets": docs.get("code_snippets", []) if not results else [],
    }


def get_topic(topic: str) -> dict:
    """특정 토픽 가져오기"""
    docs = load_docs()
    topics = docs.get("topics", {})

    if topic in topics:
        return {"success": True, "topic": topic, "data": topics[topic]}

    return {"success": False, "available_topics": list(topics.keys())}


def list_topics() -> list:
    """사용 가능한 토픽 목록"""
    docs = load_docs()
    return list(docs.get("topics", {}).keys())


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("사용법: python context7_local_search.py <검색어>")
        print("\n사용 가능한 토픽:")
        for t in list_topics():
            print(f"  - {t}")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    result = search(query)

    print(f"🔍 검색: '{query}'")
    print(f"📚 라이브러리: {result['library']} ({result['version']})")
    print(f"📊 결과: {result['total']}개\n")

    for r in result["results"]:
        print(f"--- [{r['topic']}] {r['title']} (관련도: {r['relevance']:.1f}) ---")
        print(f"   {r['content'][:200]}...")
        print(f"   키워드: {', '.join(r['keywords'])}\n")
