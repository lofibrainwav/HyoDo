#!/usr/bin/env python3
"""
Phase 038: 깊이 있는 완성도 - 성능 모니터링 시스템
Trinity Score 美(Beauty) +0.3% 달성을 위한 성능 최적화

기능:
- 실시간 성능 메트릭 수집
- 캐시 성능 분석
- API 응답 시간 모니터링
- 데이터베이스 쿼리 최적화 제안
"""

import asyncio
import logging
import tempfile
import time
from datetime import UTC, datetime
from typing import Any

import psutil
import redis

# Logger 정의
logger = logging.getLogger("AFO.PerformanceMonitor")

# 왕국 내부 모듈
try:
    from AFO.config.settings import get_settings
except ImportError:
    logger.warning("AFO modules not found. Using mocks for development.")

    class Settings:
        REDIS_HOST = "localhost"
        REDIS_PORT = 6379
        PROJECT_ROOT = tempfile.gettempdir()
        PERFORMANCE_MONITOR_INTERVAL = 60

    def get_settings() -> None:
        return Settings()

    def calculate_trinity_score() -> None:
        return 85.0


settings = get_settings()


class PerformanceMetrics:
    """성능 메트릭 데이터 클래스"""

    def __init__(self) -> None:
        self.start_time = time.time()
        self.api_response_times: list[float] = []
        self.cache_hit_rates: list[float] = []
        self.database_query_times: list[float] = []
        self.memory_usage: list[float] = []
        self.cpu_usage: list[float] = []

    def record_api_response(self, response_time: float) -> None:
        """API 응답 시간 기록"""
        self.api_response_times.append(response_time)
        # 최근 100개만 유지
        if len(self.api_response_times) > 100:
            self.api_response_times = self.api_response_times[-100:]

    def record_cache_hit_rate(self, hit_rate: float) -> None:
        """캐시 히트율 기록"""
        self.cache_hit_rates.append(hit_rate)
        if len(self.cache_hit_rates) > 50:
            self.cache_hit_rates = self.cache_hit_rates[-50:]

    def get_average_response_time(self) -> float:
        """평균 API 응답 시간 계산"""
        return (
            sum(self.api_response_times) / len(self.api_response_times)
            if self.api_response_times
            else 0.0
        )

    def get_average_cache_hit_rate(self) -> float:
        """평균 캐시 히트율 계산"""
        return (
            sum(self.cache_hit_rates) / len(self.cache_hit_rates) if self.cache_hit_rates else 0.0
        )

    def get_system_metrics(self) -> dict[str, Any]:
        """시스템 메트릭 수집"""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage("/").percent,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {"error": str(e)}


class CacheOptimizer:
    """캐시 최적화 엔진"""

    def __init__(self) -> None:
        try:
            self.redis = redis.Redis(
                host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True
            )
            # 연결 테스트
            self.redis.ping()
            logger.info("✅ Redis 연결 성공")
        except Exception as e:
            logger.warning(f"⚠️ Redis 연결 실패: {e}. 캐시 최적화 비활성화")
            self.redis = None

    def analyze_cache_performance(self) -> dict[str, Any]:
        """캐시 성능 분석"""
        if not self.redis:
            return {"error": "Redis not available"}

        try:
            # Redis INFO 명령으로 캐시 통계 수집
            info = self.redis.info()

            total_keys = info.get("db0", {}).get("keys", 0)
            expired_keys = info.get("expired_keys", 0)
            evicted_keys = info.get("evicted_keys", 0)

            # 캐시 히트율 계산 (예상)
            # 실제 구현에서는 별도 카운터가 필요
            hit_rate = 0.85  # Mock value - 실제로는 별도 메트릭 필요

            return {
                "total_keys": total_keys,
                "expired_keys": expired_keys,
                "evicted_keys": evicted_keys,
                "hit_rate": hit_rate,
                "memory_usage": info.get("used_memory_human", "0"),
                "recommendations": self._generate_cache_recommendations(hit_rate, total_keys),
            }

        except Exception as e:
            logger.error(f"Cache performance analysis failed: {e}")
            return {"error": str(e)}

    def _generate_cache_recommendations(self, hit_rate: float, total_keys: int) -> list[str]:
        """캐시 최적화 추천사항 생성"""
        recommendations = []

        if hit_rate < 0.8:
            recommendations.append("캐시 히트율이 낮음 - TTL 정책 재검토 필요")
        if total_keys > 10000:
            recommendations.append("키 개수가 많음 - 정리 및 최적화 필요")
        if hit_rate > 0.95:
            recommendations.append("캐시 성능 우수 - 현재 최적 상태")

        return recommendations

    def optimize_cache_ttl(self, key_pattern: str, new_ttl: int) -> dict[str, Any]:
        """캐시 TTL 최적화"""
        if not self.redis:
            return {"error": "Redis not available"}

        try:
            # 특정 패턴의 키들을 찾아 TTL 재설정
            keys = self.redis.keys(key_pattern)
            optimized_count = 0

            for key in keys:
                current_ttl = self.redis.ttl(key)
                if current_ttl > 0 and current_ttl > new_ttl:
                    self.redis.expire(key, new_ttl)
                    optimized_count += 1

            return {
                "pattern": key_pattern,
                "keys_found": len(keys),
                "optimized_count": optimized_count,
                "new_ttl": new_ttl,
            }

        except Exception as e:
            logger.error(f"Cache TTL optimization failed: {e}")
            return {"error": str(e)}


class PerformanceMonitor:
    """Phase 038 성능 모니터링 코어"""

    def __init__(self) -> None:
        self.metrics = PerformanceMetrics()
        self.cache_optimizer = CacheOptimizer()
        self.monitoring_active = False

    async def start_performance_monitoring(self):
        """성능 모니터링 시작"""
        logger.info("🚀 Starting Phase 038 Performance Monitoring")

        self.monitoring_active = True

        while self.monitoring_active:
            try:
                # 성능 메트릭 수집
                await self._collect_performance_metrics()

                # 캐시 성능 분석
                cache_analysis = self.cache_optimizer.analyze_cache_performance()

                # 최적화 제안 생성
                recommendations = self._generate_performance_recommendations(cache_analysis)

                # 결과 로깅
                self._log_performance_report(cache_analysis, recommendations)

                # 모니터링 간격 대기
                await asyncio.sleep(settings.PERFORMANCE_MONITOR_INTERVAL)

            except Exception as e:
                logger.error(f"💥 Performance monitoring error: {e}")
                await asyncio.sleep(60)  # 에러 시 1분 대기

    async def _collect_performance_metrics(self):
        """성능 메트릭 수집"""
        try:
            # 시스템 메트릭 수집
            system_metrics = self.metrics.get_system_metrics()

            # 메모리에 저장 (실제로는 데이터베이스나 파일에 저장)
            self.metrics.memory_usage.append(system_metrics.get("memory_percent", 0))
            self.metrics.cpu_usage.append(system_metrics.get("cpu_percent", 0))

            # 최근 100개만 유지
            if len(self.metrics.memory_usage) > 100:
                self.metrics.memory_usage = self.metrics.memory_usage[-100:]
            if len(self.metrics.cpu_usage) > 100:
                self.metrics.cpu_usage = self.metrics.cpu_usage[-100:]

        except Exception as e:
            logger.error(f"Failed to collect performance metrics: {e}")

    def _generate_performance_recommendations(self, cache_analysis: dict[str, Any]) -> list[str]:
        """성능 최적화 추천사항 생성"""
        recommendations = []

        # 캐시 성능 기반 추천
        hit_rate = cache_analysis.get("hit_rate", 0)
        if hit_rate < 0.8:
            recommendations.append("캐시 히트율 개선: TTL 정책 조정 또는 캐시 크기 증가")
        elif hit_rate > 0.95:
            recommendations.append("캐시 성능 우수: 현재 최적 상태 유지")

        # 시스템 리소스 기반 추천
        avg_memory = (
            sum(self.metrics.memory_usage[-10:]) / len(self.metrics.memory_usage[-10:])
            if self.metrics.memory_usage
            else 0
        )
        avg_cpu = (
            sum(self.metrics.cpu_usage[-10:]) / len(self.metrics.cpu_usage[-10:])
            if self.metrics.cpu_usage
            else 0
        )

        if avg_memory > 80:
            recommendations.append("메모리 사용률 높음: 메모리 최적화 또는 리소스 확장 고려")
        if avg_cpu > 70:
            recommendations.append("CPU 사용률 높음: 프로세스 최적화 또는 CPU 리소스 확장 고려")

        # API 응답 시간 기반 추천
        avg_response_time = self.metrics.get_average_response_time()
        if avg_response_time > 200:  # 200ms 이상
            recommendations.append("API 응답 시간 개선 필요: 캐싱 강화 또는 쿼리 최적화")

        return recommendations

    def _log_performance_report(
        self, cache_analysis: dict[str, Any], recommendations: list[str]
    ) -> None:
        """성능 보고서 로깅"""
        try:
            report = {
                "timestamp": datetime.now(UTC).isoformat(),
                "cache_analysis": cache_analysis,
                "system_metrics": {
                    "avg_memory_usage": sum(self.metrics.memory_usage[-10:])
                    / len(self.metrics.memory_usage[-10:])
                    if self.metrics.memory_usage
                    else 0,
                    "avg_cpu_usage": sum(self.metrics.cpu_usage[-10:])
                    / len(self.metrics.cpu_usage[-10:])
                    if self.metrics.cpu_usage
                    else 0,
                    "avg_api_response_time": self.metrics.get_average_response_time(),
                    "avg_cache_hit_rate": self.metrics.get_average_cache_hit_rate(),
                },
                "recommendations": recommendations,
            }

            logger.info(
                f"📊 Performance Report: CPU={report['system_metrics']['avg_cpu_usage']:.1f}%, "
                f"Memory={report['system_metrics']['avg_memory_usage']:.1f}%, "
                f"API={report['system_metrics']['avg_api_response_time']:.0f}ms"
            )

            if recommendations:
                logger.info(f"💡 Recommendations: {len(recommendations)}개")
                for rec in recommendations:
                    logger.info(f"   - {rec}")

        except Exception as e:
            logger.error(f"Failed to log performance report: {e}")

    def stop_monitoring(self) -> None:
        """모니터링 중지"""
        logger.info("🛑 Stopping Performance Monitoring")
        self.monitoring_active = False

    def get_performance_report(self) -> dict[str, Any]:
        """현재 성능 보고서 생성"""
        return {
            "cache_analysis": self.cache_optimizer.analyze_cache_performance(),
            "system_metrics": self.metrics.get_system_metrics(),
            "avg_api_response_time": self.metrics.get_average_response_time(),
            "avg_cache_hit_rate": self.metrics.get_average_cache_hit_rate(),
            "generated_at": datetime.now(UTC).isoformat(),
        }


# CLI 인터페이스
async def main():
    """CLI 진입점"""
    import argparse

    parser = argparse.ArgumentParser(description="Phase 038 - Performance Monitor")
    parser.add_argument("--start", action="store_true", help="지속적 성능 모니터링 시작")
    parser.add_argument("--report", action="store_true", help="현재 성능 보고서 출력")
    parser.add_argument("--optimize-cache", action="store_true", help="캐시 최적화 실행")
    parser.add_argument("--interval", type=int, default=60, help="모니터링 간격 (초)")

    args = parser.parse_args()

    monitor = PerformanceMonitor()

    if args.start:
        try:
            await monitor.start_performance_monitoring()
        except KeyboardInterrupt:
            monitor.stop_monitoring()
            print("\nMonitoring stopped by user")

    elif args.report:
        report = monitor.get_performance_report()
        print("=== Phase 038 Performance Report ===")
        print(f"Cache Hit Rate: {report.get('avg_cache_hit_rate', 0):.1f}%")
        print(f"API Response Time: {report.get('avg_api_response_time', 0):.0f}ms")
        print(f"Generated: {report.get('generated_at', 'N/A')}")

    elif args.optimize_cache:
        optimizer = CacheOptimizer()
        result = optimizer.optimize_cache_ttl("cache:*", 1800)  # 30분 TTL
        print(f"Cache optimization result: {result}")

    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
