# Trinity Score: 90.0 (Established by Chancellor)
"""Persona Service 성능 모니터링 및 벤치마크
Phase 5: 성능 최적화 검증
"""

import asyncio
import statistics
import sys
import time
from pathlib import Path
from typing import Any

# 프로젝트 루트를 sys.path에 추가
_AFO_ROOT = Path(__file__).resolve().parent.parent
if str(_AFO_ROOT) not in sys.path:
    sys.path.insert(0, str(_AFO_ROOT))


async def benchmark_persona_switch(iterations: int = 10) -> dict[str, Any]:
    """페르소나 전환 성능 벤치마크"""
    print(f"⚡ [성능 벤치마크] 페르소나 전환 ({iterations}회 반복)\n")

    try:
        from AFO.services.persona_service import persona_service

        persona_types = ["commander", "learner", "jang_yeong_sil", "yi_sun_sin", "shin_saimdang"]
        switch_times: list[float] = []

        for i in range(iterations):
            persona_type = persona_types[i % len(persona_types)]
            start_time = time.perf_counter()

            await persona_service.switch_persona(persona_type)

            end_time = time.perf_counter()
            elapsed_ms = (end_time - start_time) * 1000
            switch_times.append(elapsed_ms)

            if (i + 1) % 5 == 0:
                print(f"   진행: {i + 1}/{iterations}회 완료")

        # 통계 계산
        avg_time = statistics.mean(switch_times)
        median_time = statistics.median(switch_times)
        min_time = min(switch_times)
        max_time = max(switch_times)
        std_dev = statistics.stdev(switch_times) if len(switch_times) > 1 else 0.0

        print("\n📊 [성능 결과]")
        print(f"   평균: {avg_time:.2f}ms")
        print(f"   중앙값: {median_time:.2f}ms")
        print(f"   최소: {min_time:.2f}ms")
        print(f"   최대: {max_time:.2f}ms")
        print(f"   표준편차: {std_dev:.2f}ms")

        return {
            "iterations": iterations,
            "avg_time_ms": avg_time,
            "median_time_ms": median_time,
            "min_time_ms": min_time,
            "max_time_ms": max_time,
            "std_dev_ms": std_dev,
            "all_times": switch_times,
        }

    except Exception as e:
        print(f"❌ 벤치마크 실패: {e}")
        import traceback

        traceback.print_exc()
        return {}


async def benchmark_trinity_score_calculation(iterations: int = 20) -> dict[str, Any]:
    """Trinity Score 계산 성능 벤치마크"""
    print(f"\n⚡ [성능 벤치마크] Trinity Score 계산 ({iterations}회 반복)\n")

    try:
        from AFO.services.persona_service import persona_service

        persona_data = {
            "id": "p007",
            "name": "배움의 길 (眞 Learning)",
            "type": "learner",
            "role": "Learner",
        }

        calculation_times: list[float] = []

        for i in range(iterations):
            start_time = time.perf_counter()

            await persona_service.calculate_trinity_score(
                persona_data=persona_data, context={"iteration": i}
            )

            end_time = time.perf_counter()
            elapsed_ms = (end_time - start_time) * 1000
            calculation_times.append(elapsed_ms)

            if (i + 1) % 10 == 0:
                print(f"   진행: {i + 1}/{iterations}회 완료")

        # 통계 계산
        avg_time = statistics.mean(calculation_times)
        median_time = statistics.median(calculation_times)
        min_time = min(calculation_times)
        max_time = max(calculation_times)
        std_dev = statistics.stdev(calculation_times) if len(calculation_times) > 1 else 0.0

        print("\n📊 [성능 결과]")
        print(f"   평균: {avg_time:.2f}ms")
        print(f"   중앙값: {median_time:.2f}ms")
        print(f"   최소: {min_time:.2f}ms")
        print(f"   최대: {max_time:.2f}ms")
        print(f"   표준편차: {std_dev:.2f}ms")

        return {
            "iterations": iterations,
            "avg_time_ms": avg_time,
            "median_time_ms": median_time,
            "min_time_ms": min_time,
            "max_time_ms": max_time,
            "std_dev_ms": std_dev,
            "all_times": calculation_times,
        }

    except Exception as e:
        print(f"❌ 벤치마크 실패: {e}")
        import traceback

        traceback.print_exc()
        return {}


async def benchmark_concurrent_switches(concurrent_tasks: int = 5) -> dict[str, Any]:
    """동시 페르소나 전환 성능 벤치마크"""
    print(f"\n⚡ [성능 벤치마크] 동시 페르소나 전환 ({concurrent_tasks}개 동시 작업)\n")

    try:
        from AFO.services.persona_service import persona_service

        persona_types = ["commander", "learner", "jang_yeong_sil", "yi_sun_sin", "shin_saimdang"]

        async def switch_task(persona_type: str) -> float:
            start_time = time.perf_counter()
            await persona_service.switch_persona(persona_type)
            end_time = time.perf_counter()
            return (end_time - start_time) * 1000

        start_time = time.perf_counter()

        tasks = [
            switch_task(persona_types[i % len(persona_types)]) for i in range(concurrent_tasks)
        ]
        results = await asyncio.gather(*tasks)

        end_time = time.perf_counter()
        total_time = (end_time - start_time) * 1000

        avg_time = statistics.mean(results)
        max_time = max(results)

        print("\n📊 [성능 결과]")
        print(f"   총 소요 시간: {total_time:.2f}ms")
        print(f"   평균 작업 시간: {avg_time:.2f}ms")
        print(f"   최대 작업 시간: {max_time:.2f}ms")
        print(f"   동시성 효율: {(sum(results) / total_time) * 100:.1f}%")

        return {
            "concurrent_tasks": concurrent_tasks,
            "total_time_ms": total_time,
            "avg_task_time_ms": avg_time,
            "max_task_time_ms": max_time,
            "efficiency_percent": (sum(results) / total_time) * 100,
            "all_times": results,
        }

    except Exception as e:
        print(f"❌ 벤치마크 실패: {e}")
        import traceback

        traceback.print_exc()
        return {}


async def main() -> None:
    """메인 벤치마크 실행"""
    print("=" * 60)
    print("🏰 AFO Kingdom - Persona Service 성능 벤치마크")
    print("=" * 60)
    print()

    # 1. 페르소나 전환 벤치마크
    switch_results = await benchmark_persona_switch(iterations=10)

    # 2. Trinity Score 계산 벤치마크
    score_results = await benchmark_trinity_score_calculation(iterations=20)

    # 3. 동시 전환 벤치마크
    concurrent_results = await benchmark_concurrent_switches(concurrent_tasks=5)

    # 최종 요약
    print("\n" + "=" * 60)
    print("📈 [최종 성능 요약]")
    print("=" * 60)

    if switch_results:
        print("\n페르소나 전환:")
        print(f"  평균: {switch_results['avg_time_ms']:.2f}ms")
        if switch_results["avg_time_ms"] < 50:
            print("  ✅ 우수 (50ms 미만)")
        elif switch_results["avg_time_ms"] < 100:
            print("  ⚠️  양호 (100ms 미만)")
        else:
            print("  ❌ 개선 필요 (100ms 이상)")

    if score_results:
        print("\nTrinity Score 계산:")
        print(f"  평균: {score_results['avg_time_ms']:.2f}ms")
        if score_results["avg_time_ms"] < 20:
            print("  ✅ 우수 (20ms 미만)")
        elif score_results["avg_time_ms"] < 50:
            print("  ⚠️  양호 (50ms 미만)")
        else:
            print("  ❌ 개선 필요 (50ms 이상)")

    if concurrent_results:
        print("\n동시 전환:")
        print(f"  효율: {concurrent_results['efficiency_percent']:.1f}%")
        if concurrent_results["efficiency_percent"] > 80:
            print("  ✅ 우수 (80% 이상)")
        elif concurrent_results["efficiency_percent"] > 60:
            print("  ⚠️  양호 (60% 이상)")
        else:
            print("  ❌ 개선 필요 (60% 미만)")

    print("\n" + "=" * 60)
    print("✅ 성능 벤치마크 완료!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
