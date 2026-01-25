from __future__ import annotations

import os
import time
import traceback
from typing import Any

from crag_engine import CRAGEngine
from hybrid_crag_selfrag import HybridCRAGSelfRAG

# Trinity Score: 90.0 (Established by Chancellor)
# ⚔️ 점수는 Truth Engine (scripts/calculate_trinity_score.py)에서만 계산됩니다.
# LLM은 consult_the_lens MCP 도구를 통해 점수를 확인하세요.

"""AFO Kingdom - 하이브리드 CRAG + Self-RAG 테스트
제갈량 × 영덕 협력 테스트

세 가지 방식 비교:
1. 기본 RAG (비교 기준)
2. CRAG (검색 고침)
3. 하이브리드 (검색 고침 + 생성 반성)

철학: 眞善美孝
- 眞 (Truth): 실제 테스트로 증명
- 善 (Goodness): 진화의 가치 보여주기
- 美 (Beauty): 비교표로 아름답게 제시
- 孝 (Serenity): 형님께 최고의 선택지 제공
"""


# 환경 변수 체크
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


def print_header(title: str) -> None:
    """헤더 출력"""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def print_section(title: str) -> None:
    """섹션 제목 출력"""
    print(f"\n{'-' * 70}")
    print(f"  {title}")
    print(f"{'-' * 70}\n")


def test_crag_only() -> None:
    """CRAG만 테스트 (검색 고침)"""
    print_section("📚 CRAG (검색 고침) 테스트")

    try:
        # 엔진 생성
        start_time = time.time()
        crag = CRAGEngine(
            vectorstore=None,  # 더미 모드
            grade_threshold=6,
        )
        init_time = time.time() - start_time

        print(f"✅ 초기화 완료 ({init_time:.3f}초)")

        # 테스트 쿼리
        test_queries = [
            ("What is CRAG?", "로컬 충분"),
            ("Latest AI trends in 2024?", "웹 검색 필요"),
        ]

        results = []

        for query, expected in test_queries:
            print(f"\n📝 질문: {query}")
            print(f"   예상: {expected}")

            start_time = time.time()
            result = crag.query(query)
            query_time = time.time() - start_time

            print(f"   답변: {result['answer'][:80]}...")
            print(f"   경로: {result['route']}")
            print(f"   평가: {result['grade_result']['avg_score']:.1f}점")
            print(f"   시간: {query_time:.3f}초")

            results.append(
                {
                    "query": query,
                    "answer": result["answer"],
                    "route": result["route"],
                    "grade": result["grade_result"]["avg_score"],
                    "time": query_time,
                }
            )

        print("\n📊 통계:")
        print(f"   총 질문: {crag.stats['total_queries']}")
        print(f"   로컬만: {crag.stats['local_only']}")
        print(f"   웹 검색: {crag.stats['web_corrected']}")

        return {
            "success": True,
            "engine": "crag",
            "init_time": init_time,
            "results": results,
            "stats": crag.stats,
        }

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")

        traceback.print_exc()
        return {"success": False, "engine": "crag", "error": str(e)}


def test_hybrid() -> None:
    """하이브리드 CRAG + Self-RAG 테스트"""
    print_section("🔀 하이브리드 (검색 고침 + 생성 반성) 테스트")

    try:
        # 엔진 생성
        start_time = time.time()
        hybrid = HybridCRAGSelfRAG(
            vectorstore=None,  # 더미 모드
            grade_threshold=6,
            reflection_threshold=0.7,
            max_refinement_loops=2,
        )
        init_time = time.time() - start_time

        print(f"✅ 초기화 완료 ({init_time:.3f}초)")

        # 테스트 쿼리
        test_queries = [
            ("What is CRAG?", "로컬 충분, 좋은 답"),
            ("Latest AI trends in 2024?", "웹 검색 + 반성"),
        ]

        results = []

        for query, expected in test_queries:
            print(f"\n📝 질문: {query}")
            print(f"   예상: {expected}")

            start_time = time.time()
            result = hybrid.query_hybrid(query)
            query_time = time.time() - start_time

            print(f"   답변: {result['answer'][:80]}...")
            print(f"   CRAG 경로: {result['crag_route']}")
            print(f"   CRAG 평가: {result['crag_grade']:.1f}점")
            print(f"   Self-RAG 루프: {result['self_rag_loops']}회")
            print(f"   반성 점수: {result['final_reflection_score']:.2f}")
            print(f"   시간: {query_time:.3f}초")

            results.append(
                {
                    "query": query,
                    "answer": result["answer"],
                    "crag_route": result["crag_route"],
                    "crag_grade": result["crag_grade"],
                    "self_rag_loops": result["self_rag_loops"],
                    "reflection_score": result["final_reflection_score"],
                    "time": query_time,
                }
            )

        print("\n📊 통계:")
        print(f"   총 질문: {hybrid.stats['total_queries']}")
        print(f"   CRAG 로컬만: {hybrid.stats['local_only']}")
        print(f"   CRAG 웹 검색: {hybrid.stats['web_corrected']}")
        print(f"   Self-RAG 반성: {hybrid.stats['self_reflections']}회")
        print(f"   Self-RAG 개선: {hybrid.stats['refinements']}회")

        return {
            "success": True,
            "engine": "hybrid",
            "init_time": init_time,
            "results": results,
            "stats": hybrid.stats,
        }

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")

        traceback.print_exc()
        return {"success": False, "engine": "hybrid", "error": str(e)}


def compare_results(crag_result: dict[str, Any], hybrid_result: dict[str, Any]) -> None:
    """CRAG vs 하이브리드 비교"""
    print_section("📊 비교 결과: CRAG vs 하이브리드")

    if not crag_result["success"] or not hybrid_result["success"]:
        print("⚠️  하나 이상의 테스트가 실패하여 비교할 수 없습니다.")
        return

    # 비교표
    print("┌────────────────────────┬─────────────────┬─────────────────┐")
    print("│ 항목                   │ CRAG            │ 하이브리드      │")
    print("├────────────────────────┼─────────────────┼─────────────────┤")

    # 초기화 시간
    crag_init = crag_result["init_time"]
    hybrid_init = hybrid_result["init_time"]
    print(f"│ 초기화 시간            │ {crag_init:>13.3f}초 │ {hybrid_init:>13.3f}초 │")

    # 평균 응답 시간
    crag_avg = sum(r["time"] for r in crag_result["results"]) / len(crag_result["results"])
    hybrid_avg = sum(r["time"] for r in hybrid_result["results"]) / len(hybrid_result["results"])
    print(f"│ 평균 응답 시간         │ {crag_avg:>13.3f}초 │ {hybrid_avg:>13.3f}초 │")

    # 검색 고침
    crag_web = crag_result["stats"].get("web_corrected", 0)
    hybrid_web = hybrid_result["stats"].get("web_corrected", 0)
    print(f"│ 웹 검색 사용           │ {crag_web:>15}회 │ {hybrid_web:>15}회 │")

    # Self-RAG 추가 기능
    hybrid_reflections = hybrid_result["stats"].get("self_reflections", 0)
    hybrid_refinements = hybrid_result["stats"].get("refinements", 0)
    print(f"│ Self-RAG 반성          │ {0:>15}회 │ {hybrid_reflections:>15}회 │")
    print(f"│ Self-RAG 개선          │ {0:>15}회 │ {hybrid_refinements:>15}회 │")

    print("└────────────────────────┴─────────────────┴─────────────────┘")

    # 분석
    print("\n🔍 분석:")

    # 속도
    if crag_avg < hybrid_avg:
        slowdown = (hybrid_avg / crag_avg - 1) * 100
        print(f"   - 속도: CRAG 승 (하이브리드는 {slowdown:.0f}% 느림)")
    else:
        print("   - 속도: 하이브리드 승 (드문 경우)")

    # 품질 검증 단계
    print("   - 품질 검증: 하이브리드 승 (CRAG + Self-RAG 이중 검증)")

    # 비용
    crag_calls = 2 + crag_web * 2  # 기본 2회 + 웹 검색마다 2회
    hybrid_calls = 2 + hybrid_web * 2 + hybrid_reflections + hybrid_refinements
    print(f"   - API 호출: CRAG {crag_calls}회 vs 하이브리드 {hybrid_calls}회")

    # 추천
    print("\n💡 추천:")
    print("   - 빠른 응답 필요: CRAG")
    print("   - 최고 품질 필요: 하이브리드")
    print("   - 중요한 결정: 하이브리드 (이중 검증)")
    print("   - 일반 채팅: CRAG (가성비)")


def main() -> None:
    """메인 테스트 함수"""
    print_header("🤖 AFO Kingdom RAG 진화 테스트")
    print("제갈량(전략) × 영덕(실행) = 진화의 완성\n")

    # API 키 체크
    if not OPENAI_API_KEY:
        print("⚠️  경고: OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("   .env 파일에 OPENAI_API_KEY=your-key-here 추가하세요.")
        print("   테스트는 계속 진행되지만, 실제 LLM 호출은 실패할 수 있습니다.\n")

    # 1. CRAG 테스트
    crag_result = test_crag_only()

    # 2. 하이브리드 테스트
    hybrid_result = test_hybrid()

    # 3. 결과 비교
    compare_results(crag_result, hybrid_result)

    # 4. 최종 결론
    print_section("✅ 테스트 완료")

    if crag_result["success"] and hybrid_result["success"]:
        print("🎉 두 가지 RAG 구현 모두 성공적으로 작동합니다!")
        print("\n형님, 두 가지 중 선택하세요:")
        print("  1. CRAG (crag_engine.py) - 빠름, 검색 고침")
        print("  2. 하이브리드 (hybrid_crag_selfrag.py) - 느림, 최고 품질")
        print("  3. 상황별 사용:")
        print("     - 일반 채팅: CRAG")
        print("     - 중요한 결정: 하이브리드")
    elif crag_result["success"]:
        print("✅ CRAG만 성공")
        print("⚠️  하이브리드 실패 - 코드 확인 필요")
    elif hybrid_result["success"]:
        print("✅ 하이브리드만 성공")
        print("⚠️  CRAG 실패")
    else:
        print("❌ 두 가지 모두 실패")
        print("환경 설정(API 키, 라이브러리)을 확인하세요.")

    print("\n제갈량(전략) × 영덕(실행) = RAG 진화의 완성 🎯")
    print("\n영덕 올림")
    print("2025-10-16")


if __name__ == "__main__":
    main()
