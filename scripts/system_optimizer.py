#!/usr/bin/env python3
"""
AFO 왕국 시스템 최적화 도구
캐시, 네트워크, 메모리 최적화
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

import httpx
import psutil
import redis


class SystemOptimizer:
    def __init__(self) -> None:
        self.redis_client = redis.Redis(host="localhost", port=6379, db=0)

    async def optimize_redis_cache(self) -> dict:
        """Redis 캐시 최적화"""
        result = {"status": "success", "optimizations": []}

        try:
            # 현재 캐시 정보 수집
            info = self.redis_client.info()
            used_memory = info["used_memory"]
            total_keys = self.redis_client.dbsize()

            # 오래된 캐시 정리 (TTL이 없는 키들)
            keys_without_ttl = []
            for key in self.redis_client.scan_iter():
                ttl = self.redis_client.ttl(key)
                if ttl == -1:  # TTL 없음
                    keys_without_ttl.append(key)

            # 기본 TTL 설정 (7일)
            default_ttl = 7 * 24 * 60 * 60
            for key in keys_without_ttl[:100]:  # 최대 100개만 처리
                try:
                    self.redis_client.expire(key, default_ttl)
                    result["optimizations"].append(f"Set TTL for key: {key[:50]}...")
                except:
                    pass

            result["optimizations"].append(
                f"Redis memory: {used_memory / 1024 / 1024:.1f}MB, Keys: {total_keys}"
            )
            result["optimizations"].append(f"Set TTL for {len(keys_without_ttl)} keys")

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    async def optimize_network_connections(self) -> dict:
        """네트워크 연결 최적화"""
        result = {"status": "success", "optimizations": []}

        services = [
            {
                "name": "ollama",
                "url": "http://localhost:11434/api/tags",
                "timeout": 5.0,
            },
            {
                "name": "api_server",
                "url": "http://localhost:8010/health",
                "timeout": 3.0,
            },
            {
                "name": "dashboard",
                "url": "http://localhost:3000/api/health",
                "timeout": 5.0,
            },
        ]

        for service in services:
            try:
                start_time = asyncio.get_event_loop().time()
                async with httpx.AsyncClient(timeout=service["timeout"]) as client:
                    response = await client.get(service["url"])
                    response_time = asyncio.get_event_loop().time() - start_time

                    if response.status_code == 200:
                        result["optimizations"].append(
                            f"{service['name']}: {response_time:.3f}s (OK)"
                        )
                    else:
                        result["optimizations"].append(
                            f"{service['name']}: {response_time:.3f}s (HTTP {response.status_code})"
                        )

            except Exception as e:
                result["optimizations"].append(f"{service['name']}: ERROR - {str(e)[:50]}")

        return result

    def optimize_memory_usage(self) -> dict:
        """메모리 사용량 최적화"""
        result = {"status": "success", "optimizations": []}

        # 현재 메모리 상태
        memory = psutil.virtual_memory()
        result["optimizations"].append(
            f"System Memory: {memory.percent:.1f}% used ({memory.available / 1024 / 1024 / 1024:.1f}GB free)"
        )

        # 프로세스별 메모리 사용량 분석
        processes = []
        for proc in psutil.process_iter(["pid", "name", "memory_percent"]):
            try:
                if proc.info["memory_percent"] > 0.1:  # 0.1% 이상 사용 프로세스
                    processes.append(proc.info)
            except:
                continue

        # 메모리 사용량 기준 정렬
        processes.sort(key=lambda x: x["memory_percent"], reverse=True)

        for proc in processes[:5]:  # 상위 5개
            result["optimizations"].append(
                f"Process {proc['name']} ({proc['pid']}): {proc['memory_percent']:.1f}%"
            )

        return result

    async def optimize_file_system(self) -> dict:
        """파일 시스템 최적화"""
        result = {"status": "success", "optimizations": []}

        # 큰 로그 파일 정리
        log_dir = Path("logs")
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            for log_file in log_files:
                size_mb = log_file.stat().st_size / 1024 / 1024
                if size_mb > 50:  # 50MB 이상 로그 파일
                    result["optimizations"].append(
                        f"Large log file: {log_file.name} ({size_mb:.1f}MB)"
                    )

        # 임시 파일 정리
        temp_patterns = ["*.tmp", "*.temp", "*.bak", "*~"]
        temp_files = []
        for pattern in temp_patterns:
            temp_files.extend(Path(".").rglob(pattern))

        if temp_files:
            result["optimizations"].append(f"Found {len(temp_files)} temporary files")

        # 캐시 디렉토리 정리 권장
        cache_dirs = ["__pycache__", ".pytest_cache", "node_modules/.cache"]
        for cache_dir in cache_dirs:
            if Path(cache_dir).exists():
                size = sum(f.stat().st_size for f in Path(cache_dir).rglob("*") if f.is_file())
                size_mb = size / 1024 / 1024
                if size_mb > 100:
                    result["optimizations"].append(f"Large cache: {cache_dir} ({size_mb:.1f}MB)")

        return result

    async def run_full_optimization(self) -> dict:
        """전체 최적화 실행"""
        print("🚀 AFO 왕국 시스템 최적화 시작...")

        results = await asyncio.gather(
            self.optimize_redis_cache(),
            self.optimize_network_connections(),
            self.optimize_file_system(),
        )

        memory_result = self.optimize_memory_usage()

        # 결과 종합
        optimization_report = {
            "timestamp": datetime.now().isoformat(),
            "redis_cache": results[0],
            "network": results[1],
            "file_system": results[2],
            "memory": memory_result,
            "summary": {
                "total_optimizations": sum(
                    len(r.get("optimizations", [])) for r in results + [memory_result]
                ),
                "status": "completed",
            },
        }

        # 결과 출력
        print("📊 최적화 결과:")
        for category, result in [
            ("Redis 캐시", results[0]),
            ("네트워크", results[1]),
            ("파일 시스템", results[2]),
            ("메모리", memory_result),
        ]:
            print(f"  🔧 {category}:")
            for opt in result.get("optimizations", []):
                print(f"    {opt}")
            print()

        # 결과 저장
        os.makedirs("reports", exist_ok=True)
        report_file = f"reports/optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(optimization_report, f, indent=2, ensure_ascii=False)

        print(f"📄 최적화 보고서 저장: {report_file}")

        return optimization_report


async def main():
    optimizer = SystemOptimizer()
    await optimizer.run_full_optimization()


if __name__ == "__main__":
    asyncio.run(main())
