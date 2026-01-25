from __future__ import annotations

import os
import time
import traceback
from typing import Any

from crag_engine import CRAGEngine
from crag_langgraph import CRAGLangGraph

# Trinity Score: 90.0 (Established by Chancellor)
# ⚔️ 점수는 Truth Engine (scripts/calculate_trinity_score.py)에서만 계산됩니다.
# LLM은 consult_the_lens MCP 도구를 통해 점수를 확인하세요.

"""AFO Kingdom - CRAG 통합 테스트
제갈량 × 영덕 협력 테스트

두 가지 CRAG 구현을 모두 테스트하고 비교:
1. 클래스 기반 (crag_engine.py) - 영덕
2. LangGraph 기반 (crag_langgraph.py) - 제갈량 + 영덕

철학: 眞善美孝
- 眞 (Truth): 실제 테스트로 증명
- 善 (Goodness): 협력의 가치 보여주기
- 美 (Beauty): 비교표로 아름답게 제시
- 孝 (Serenity): 형님께 명확한 선택지 제공
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


def test_class_based() -> None:
    """클래스 기반 CRAG 테스트 (영덕의 구현)"""
    print_section("🏛️  클래스 기반 CRAG 테스트")

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
            ("Who is the president of USA in 2024?", "웹 검색 필요"),
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
            print(f"   시간: {query_time:.3f}초")

            results.append(
                {
                    "query": query,
                    "answer": result["answer"],
                    "route": result["route"],
                    "time": query_time,
                }
            )

        print("\n📊 통계:")
        print(f"   총 질문: {crag.stats['total_queries']}")
        print(f"   로컬만: {crag.stats['local_only']}")
        print(f"   웹 검색: {crag.stats['web_corrected']}")

        return {
            "success": True,
            "engine": "class_based",
            "init_time": init_time,
            "results": results,
            "stats": crag.stats,
        }

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")

        traceback.print_exc()
        return {"success": False, "engine": "class_based", "error": str(e)}


def test_langgraph_based() -> None:
    """LangGraph 기반 CRAG 테스트 (제갈량 + 영덕의 구현)"""
    print_section("🔀 LangGraph 기반 CRAG 테스트")

    try:
        # 엔진 생성
        start_time = time.time()
        crag = CRAGLangGraph(
            vectorstore=None,  # 더미 모드
            grade_threshold=0.5,
        )
        init_time = time.time() - start_time

        print(f"✅ 초기화 완료 ({init_time:.3f}초)")

        # 테스트 쿼리
        test_queries = [
            ("What is CRAG?", "로컬 충분"),
            ("Who is the president of USA in 2024?", "웹 검색 필요"),
        ]

        results = []

        for query, expected in test_queries:
            print(f"\n📝 질문: {query}")
            print(f"   예상: {expected}")

            start_time = time.time()
            result = crag.query(query)
            query_time = time.time() - start_time

            print(f"   답변: {result['answer'][:80]}...")
            print(f"   웹 검색: {'✅' if result['web_search_used'] else '❌'}")
            print(f"   시간: {query_time:.3f}초")

            results.append(
                {
                    "query": query,
                    "answer": result["answer"],
                    "web_search": result["web_search_used"],
                    "time": query_time,
                }
            )

        print("\n📊 통계:")
        print(f"   총 질문: {crag.stats['total_queries']}")
        print(f"   로컬만: {crag.stats['local_only']}")
        print(f"   웹 검색: {crag.stats['web_searches']}")

        return {
            "success": True,
            "engine": "langgraph_based",
            "init_time": init_time,
            "results": results,
            "stats": crag.stats,
        }

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")

        traceback.print_exc()
        return {"success": False, "engine": "langgraph_based", "error": str(e)}


def compare_results(class_result: dict[str, Any], langgraph_result: dict[str, Any]) -> None:
    """두 결과 비교 및 출력"""
    print_section("📊 비교 결과")

    if not class_result["success"] or not langgraph_result["success"]:
        print("⚠️  하나 이상의 테스트가 실패하여 비교할 수 없습니다.")
        return

    # 비교표
    print("┌─────────────────────┬─────────────────┬─────────────────┐")
    print("│ 항목                │ 클래스 기반     │ LangGraph 기반  │")
    print("├─────────────────────┼─────────────────┼─────────────────┤")

    # 초기화 시간
    class_init = class_result["init_time"]
    lg_init = langgraph_result["init_time"]
    print(f"│ 초기화 시간         │ {class_init:>13.3f}초 │ {lg_init:>13.3f}초 │")

    # 평균 응답 시간
    class_avg = sum(r["time"] for r in class_result["results"]) / len(class_result["results"])
    lg_avg = sum(r["time"] for r in langgraph_result["results"]) / len(langgraph_result["results"])
    print(f"│ 평균 응답 시간      │ {class_avg:>13.3f}초 │ {lg_avg:>13.3f}초 │")

    # 총 질문 수
    class_total = class_result["stats"]["total_queries"]
    lg_total = langgraph_result["stats"]["total_queries"]
    print(f"│ 총 질문 수          │ {class_total:>15}개 │ {lg_total:>15}개 │")

    # 로컬만 사용
    class_local = class_result["stats"]["local_only"]
    lg_local = langgraph_result["stats"]["local_only"]
    print(f"│ 로컬만 사용         │ {class_local:>15}개 │ {lg_local:>15}개 │")

    # 웹 검색 사용
    class_web = class_result["stats"].get("web_corrected", 0)
    lg_web = langgraph_result["stats"].get("web_searches", 0)
    print(f"│ 웹 검색 사용        │ {class_web:>15}개 │ {lg_web:>15}개 │")

    print("└─────────────────────┴─────────────────┴─────────────────┘")

    # 승자 판정
    print("\n🏆 성능 비교:")
    if class_init < lg_init:
        print(f"   - 초기화: 클래스 기반 승 ({class_init:.3f}초 < {lg_init:.3f}초)")
    else:
        print(f"   - 초기화: LangGraph 기반 승 ({lg_init:.3f}초 < {class_init:.3f}초)")

    if class_avg < lg_avg:
        print(f"   - 응답 속도: 클래스 기반 승 ({class_avg:.3f}초 < {lg_avg:.3f}초)")
    else:
        print(f"   - 응답 속도: LangGraph 기반 승 ({lg_avg:.3f}초 < {class_avg:.3f}초)")

    # 추천
    print("\n💡 추천:")
    print("   - API 서버 통합: 클래스 기반 (빠르고 쉬움)")
    print("   - 복잡한 워크플로우: LangGraph 기반 (시각화 가능)")
    print("   - 연구/실험: LangGraph 기반 (그래프로 보고)")
    print("   - 프로덕션: 클래스 기반 (성능 우수)")


def main() -> None:
    """메인 테스트 함수"""
    print_header("🤖 AFO Kingdom CRAG 통합 테스트")

    # API 키 체크
    if not OPENAI_API_KEY:
        print("⚠️  경고: OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("   .env 파일에 OPENAI_API_KEY=your-key-here 추가하세요.")
        print("   테스트는 계속 진행되지만, 실제 LLM 호출은 실패할 수 있습니다.\n")

    # 1. 클래스 기반 테스트
    class_result = test_class_based()

    # 2. LangGraph 기반 테스트
    langgraph_result = test_langgraph_based()

    # 3. 결과 비교
    compare_results(class_result, langgraph_result)

    # 4. 최종 결론
    print_section("✅ 테스트 완료")

    if class_result["success"] and langgraph_result["success"]:
        print("🎉 두 가지 CRAG 구현 모두 성공적으로 작동합니다!")
        print("\n형님, 두 가지 중 선택하세요:")
        print("  1. 클래스 기반 (crag_engine.py) - API 통합 쉬움")
        print("  2. LangGraph 기반 (crag_langgraph.py) - 시각화 가능")
        print("  3. 둘 다 사용 (시나리오별 선택)")
    elif class_result["success"]:
        print("✅ 클래스 기반만 성공")
        print("⚠️  LangGraph 기반 실패 - 라이브러리 설치 필요")
    elif langgraph_result["success"]:
        print("✅ LangGraph 기반만 성공")
        print("⚠️  클래스 기반 실패")
    else:
        print("❌ 두 가지 모두 실패")
        print("환경 설정(API 키, 라이브러리)을 확인하세요.")

    print("\n제갈량(전략) × 영덕(실행) = 협력의 시너지 🤝")
    print("\n영덕 올림")
    print("2025-10-16")


if __name__ == "__main__":
    main()
