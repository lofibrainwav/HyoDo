from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

# Trinity Score: 90.0 (Established by Chancellor)
#!/usr/bin/env python3
"""Friction Calibrator - 병렬 실행 효율 측정 및 자동 튜닝
眞善美孝: Truth, Goodness, Beauty, Serenity

메타인지 기반 튜닝:
- 순차 vs 병렬 시간 측정으로 Friction 계산
- 목표 Friction 이하로 동시성 자동 조정
- 최소/최대 동시성 범위 내에서 안전하게 튜닝
"""


@dataclass
class FrictionStats:
    """Friction 측정 결과"""

    concurrency: int
    sequential_time: float
    parallel_time: float

    @property
    def friction(self) -> float:
        """Friction 계산: (실제 병렬 시간 - 이상적 병렬 시간) / 이상적 병렬 시간

        이상적 병렬 시간 = 순차 시간 / 동시성

        Returns:
            float: Friction 값 (0.0 = 이상적, 높을수록 비효율적)

        """
        if self.concurrency <= 1:
            return 0.0

        ideal_parallel_time = self.sequential_time / float(self.concurrency)

        if ideal_parallel_time <= 0:
            return 0.0

        friction_value = (self.parallel_time - ideal_parallel_time) / ideal_parallel_time
        return max(0.0, friction_value)  # 음수 방지

    @property
    def efficiency(self) -> float:
        """효율성: 이상적 시간 / 실제 시간

        Returns:
            float: 1.0 = 이상적, 낮을수록 비효율적

        """
        if self.parallel_time <= 0:
            return 0.0
        ideal = self.sequential_time / max(1, self.concurrency)
        return ideal / self.parallel_time


class FrictionCalibrator:
    """Friction 기반 동시성 자동 튜닝

    메타인지 로직:
    - 목표 Friction 이하: 동시성 유지 또는 증가
    - 목표 Friction 초과: 동시성 감소 (안전하게 30%)
    - 범위 내에서만 조정 (min/max 리스펙트)
    """

    def __init__(
        self,
        target_friction: float = 0.02,  # 2% 목표 Friction
        min_concurrency: int = 1,
        max_concurrency: int = 64,
        reduction_factor: float = 0.7,  # 30% 감소
    ) -> None:
        self.target_friction = target_friction
        self.min_concurrency = min_concurrency
        self.max_concurrency = max_concurrency
        self.reduction_factor = reduction_factor

    def recommend(self, stats: FrictionStats) -> int:
        """측정 결과 기반 새로운 동시성 추천

        Args:
            stats: Friction 측정 결과

        Returns:
            int: 추천 동시성

        """
        current_friction = stats.friction

        # 眞(진): 목표 Friction 이하 = 효율적
        if current_friction <= self.target_friction:
            # 살짝 증가 고려 (하지만 안전하게 유지)
            return stats.concurrency

        # 善(선): Friction 높음 = 비효율적, 동시성 감소
        new_concurrency = int(stats.concurrency * self.reduction_factor)

        # 범위 내로 클램핑
        if new_concurrency < self.min_concurrency:
            new_concurrency = self.min_concurrency
        if new_concurrency > self.max_concurrency:
            new_concurrency = self.max_concurrency

        return new_concurrency

    def measure_and_recommend(
        self,
        concurrency: int,
        sequential_fn: Callable[[Any], None],
        parallel_fn: Callable[[list[Any], int], None],
        tasks_data: list[Any],
    ) -> tuple[FrictionStats, int]:
        """순차/병렬 실행 측정 + 추천 계산

        Args:
            concurrency: 현재 동시성
            sequential_fn: 순차 실행 함수
            parallel_fn: 병렬 실행 함수
            tasks_data: 작업 데이터

        Returns:
            tuple: (측정 결과, 추천 동시성)

        """
        if not tasks_data:
            return FrictionStats(concurrency, 0.0, 0.0), concurrency

        # 순차 측정
        t0 = time.perf_counter()
        for task in tasks_data:
            sequential_fn(task)
        sequential_time = time.perf_counter() - t0

        # 병렬 측정
        t1 = time.perf_counter()
        parallel_fn(tasks_data, concurrency)
        parallel_time = time.perf_counter() - t1

        # 통계 계산
        stats = FrictionStats(concurrency, sequential_time, parallel_time)
        recommended = self.recommend(stats)

        return stats, recommended


# 글로벌 인스턴스
calibrator = FrictionCalibrator()


def demo_friction() -> None:
    """데모: Friction 측정

    Demonstrates friction measurement between sequential and parallel execution.
    """

    async def mock_task(delay: float) -> None:
        await asyncio.sleep(delay)

    async def sequential_run(tasks: list[float]) -> None:
        for delay in tasks:
            await mock_task(delay)

    async def parallel_run(tasks, concurrency):
        semaphore = asyncio.Semaphore(concurrency)

        async def limited_task(delay):
            async with semaphore:
                await mock_task(delay)

        await asyncio.gather(*[limited_task(delay) for delay in tasks])

    # 테스트 데이터
    tasks = [0.1, 0.05, 0.08, 0.03, 0.12]

    # 측정
    stats, recommended = calibrator.measure_and_recommend(
        concurrency=4,
        sequential_fn=lambda t: asyncio.run(mock_task(t)),
        parallel_fn=lambda tasks, c: asyncio.run(parallel_run(tasks, c)),
        tasks_data=tasks,
    )

    print(f"Friction: {stats.friction:.3f}")
    print(f"Efficiency: {stats.efficiency:.3f}")
    print(f"Recommended concurrency: {recommended}")


if __name__ == "__main__":
    demo_friction()
