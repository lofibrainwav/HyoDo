#!/usr/bin/env python3
"""
TICKET-047: Mem0 통합 테스트 스크립트

이 스크립트는 Mem0 기반 persistence 시스템을 테스트합니다.

기능:
- AFO_MemoryClient 기본 동작 테스트
- Context7MemoryManager 통합 테스트
- 성능 측정 (latency < 100ms 목표)

실행:
    python scripts/ticket047_mem0_integration.py

Trinity Score 목표: 永 1.0 달성
"""

import json
import sys
import time
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_mem0_client() -> None:
    """AFO_MemoryClient 기본 동작 테스트"""
    print("\n" + "=" * 60)
    print("🧪 [Test 1] AFO_MemoryClient 기본 동작 테스트")
    print("=" * 60)

    from memory import AFO_MemoryClient

    # 클라이언트 초기화
    client = AFO_MemoryClient()
    print(f"✅ 클라이언트 초기화 완료 (initialized={client.initialized})")

    # 테스트 사용자 ID
    test_user = "test_user_ticket047"

    # 메모리 추가 테스트
    print("\n📝 메모리 추가 테스트...")
    add_result = client.add_memory(
        content="AFO 왕국의 Mem0 통합이 성공적으로 완료되었습니다. Trinity Score 목표: 永 1.0",
        user_id=test_user,
        metadata={"test": True, "ticket": "TICKET-047"},
        session_id="test_session_001",
    )
    print(f"  - 결과: {add_result['success']}")
    print(f"  - Latency: {add_result['latency_ms']:.2f}ms")

    # 추가 메모리
    client.add_memory(
        content="Context7 지식 베이스와의 통합으로 검색 기능이 강화되었습니다.",
        user_id=test_user,
        metadata={"type": "context7", "ticket": "TICKET-047"},
        session_id="test_session_001",
    )

    client.add_memory(
        content="LangGraph checkpointer를 통한 상태 persistence가 구현되었습니다.",
        user_id=test_user,
        metadata={"type": "langgraph", "ticket": "TICKET-047"},
        session_id="test_session_001",
    )

    # 메모리 검색 테스트
    print("\n🔍 메모리 검색 테스트...")
    search_result = client.search_memory(query="Trinity Score", user_id=test_user, limit=3)
    print(f"  - 결과: {search_result['success']}")
    print(f"  - 검색된 항목: {search_result.get('returned', 0)}개")
    print(f"  - Latency: {search_result['latency_ms']:.2f}ms")

    # 모든 메모리 조회 테스트
    print("\n📋 모든 메모리 조회 테스트...")
    all_memories = client.get_all_memories(user_id=test_user)
    print(f"  - 결과: {all_memories['success']}")
    print(f"  - 총 메모리: {all_memories.get('count', 0)}개")
    print(f"  - Latency: {all_memories['latency_ms']:.2f}ms")

    # 성능 통계
    print("\n📊 성능 통계...")
    stats = client.get_performance_stats()
    print(f"  - Add 호출: {stats['add_calls']}회")
    print(f"  - Search 호출: {stats['search_calls']}회")
    print(f"  - 평균 Latency: {stats['avg_latency_ms']:.2f}ms")
    print(f"  - Trinity Score (永): {stats['trinity_score']['eternity']}")

    return {
        "test": "mem0_client",
        "success": add_result["success"] and search_result["success"],
        "avg_latency_ms": stats["avg_latency_ms"],
        "trinity_score": stats["trinity_score"],
    }


def test_context7_integration() -> None:
    """Context7MemoryManager 통합 테스트"""
    print("\n" + "=" * 60)
    print("🧪 [Test 2] Context7MemoryManager 통합 테스트")
    print("=" * 60)

    from memory import Context7MemoryManager

    # 매니저 초기화
    manager = Context7MemoryManager()
    print("✅ Context7 매니저 초기화 완료")
    print(f"  - 발견된 Context7 문서: {len(manager.context7_docs)}개")

    # 문서 목록 출력
    if manager.context7_docs:
        print("\n📚 Context7 문서 목록:")
        for doc in manager.context7_docs[:5]:
            print(f"  - {doc['filename']}")
    else:
        print("\n⚠️ Context7 문서가 없습니다. (docs/ 폴더 확인 필요)")

    # 메모리화 테스트 (문서가 있는 경우)
    if manager.context7_docs:
        print("\n💾 Context7 문서 메모리화...")
        memorize_result = manager.memorize_context7_docs(user_id="system_ticket047")
        print(f"  - 총 문서: {memorize_result['total_docs']}개")
        print(f"  - 성공: {memorize_result['successful']}개")
        print(f"  - 실패: {memorize_result['failed']}개")
        print(f"  - Latency: {memorize_result['total_latency_ms']:.2f}ms")
    else:
        memorize_result = {"total_docs": 0, "successful": 0, "failed": 0}

    # 검색 테스트
    print("\n🔍 Context7 지식 검색 테스트...")
    search_result = manager.search_context7_knowledge(
        query="Skills Registry", user_id="system_ticket047"
    )
    print(f"  - 결과: {search_result['success']}")
    print(f"  - 검색된 항목: {search_result.get('total_found', 0)}개")
    print(f"  - Latency: {search_result['latency_ms']:.2f}ms")

    # 통계 조회
    print("\n📊 Context7 통계...")
    stats = manager.get_context7_stats(user_id="system_ticket047")
    print(f"  - 총 메모리: {stats.get('total_memories', 0)}개")
    print(f"  - 검색 호출: {stats.get('search_calls', 0)}회")
    print(f"  - 평균 Latency: {stats.get('avg_latency_ms', 0):.2f}ms")

    return {
        "test": "context7_integration",
        "success": search_result["success"],
        "docs_found": len(manager.context7_docs),
        "docs_memorized": memorize_result.get("successful", 0),
    }


def test_performance() -> None:
    """성능 테스트 (latency < 100ms 목표)"""
    print("\n" + "=" * 60)
    print("🧪 [Test 3] 성능 테스트 (목표: latency < 100ms)")
    print("=" * 60)

    from memory import get_memory_client

    client = get_memory_client()
    test_user = "perf_test_user"
    latencies = []

    # 10회 반복 테스트
    print("\n⏱️ 10회 반복 latency 측정...")
    for i in range(10):
        start = time.time()
        client.add_memory(
            content=f"Performance test iteration {i}",
            user_id=test_user,
            metadata={"iteration": i},
        )
        latency = (time.time() - start) * 1000
        latencies.append(latency)

    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)
    min_latency = min(latencies)

    print(f"  - 평균 Latency: {avg_latency:.2f}ms")
    print(f"  - 최소 Latency: {min_latency:.2f}ms")
    print(f"  - 최대 Latency: {max_latency:.2f}ms")

    # 목표 달성 여부
    target_met = avg_latency < 100
    if target_met:
        print(f"\n✅ 성능 목표 달성! (avg {avg_latency:.2f}ms < 100ms)")
    else:
        print(f"\n⚠️ 성능 목표 미달 (avg {avg_latency:.2f}ms >= 100ms)")

    return {
        "test": "performance",
        "success": target_met,
        "avg_latency_ms": avg_latency,
        "min_latency_ms": min_latency,
        "max_latency_ms": max_latency,
    }


def main() -> None:
    """메인 실행 함수"""
    print("=" * 60)
    print("🏰 TICKET-047: Mem0 통합 테스트")
    print("   AFO 왕국 Persistence 시스템")
    print("=" * 60)
    print(f"📅 실행 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    results = []

    # 테스트 실행
    try:
        results.append(test_mem0_client())
    except Exception as e:
        print(f"\n❌ Mem0 Client 테스트 실패: {e}")
        results.append({"test": "mem0_client", "success": False, "error": str(e)})

    try:
        results.append(test_context7_integration())
    except Exception as e:
        print(f"\n❌ Context7 통합 테스트 실패: {e}")
        results.append({"test": "context7_integration", "success": False, "error": str(e)})

    try:
        results.append(test_performance())
    except Exception as e:
        print(f"\n❌ 성능 테스트 실패: {e}")
        results.append({"test": "performance", "success": False, "error": str(e)})

    # 최종 결과 요약
    print("\n" + "=" * 60)
    print("📊 TICKET-047 테스트 결과 요약")
    print("=" * 60)

    all_success = all(r.get("success", False) for r in results)

    for result in results:
        status = "✅" if result.get("success") else "❌"
        print(f"{status} {result['test']}: {'PASS' if result.get('success') else 'FAIL'}")

    # Trinity Score 계산
    trinity_score = {
        "truth": 0.9 if all_success else 0.7,
        "goodness": 0.95 if all_success else 0.8,
        "beauty": 0.9,
        "serenity": 1.0,
        "eternity": 1.0 if all_success else 0.8,
    }

    print("\n🎯 Trinity Score:")
    for pillar, score in trinity_score.items():
        print(f"  - {pillar}: {score}")

    # SSOT 결과 출력
    ssot_result = {
        "ticket": "TICKET-047",
        "phase": "Phase 1 - Mem0 통합",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "tests": results,
        "all_passed": all_success,
        "trinity_score": trinity_score,
        "decision": "AUTO_RUN APPROVED" if all_success else "ASK_COMMANDER",
    }

    print("\n📋 SSOT 결과:")
    print(json.dumps(ssot_result, indent=2, ensure_ascii=False))

    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
