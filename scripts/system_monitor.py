#!/usr/bin/env python3
"""
AFO 왕국 시스템 모니터링 스크립트
실시간 시스템 상태 모니터링 및 알림
"""

import asyncio
import json
import os
import time
from datetime import datetime

import httpx
import psutil


class SystemMonitor:
    def __init__(self) -> None:
        self.services = {
            "ollama": {"port": 11434, "endpoint": "/api/tags"},
            "api_server": {"port": 8010, "endpoint": "/health"},
            "dashboard": {"port": 3000, "endpoint": "/api/health"},
            "redis": {"port": 6379, "check": self._check_redis},
        }
        self.alerts = []

    def _check_redis(self) -> bool:
        """Redis 연결 상태 확인"""
        try:
            import redis

            r = redis.Redis(host="localhost", port=6379, db=0)
            r.ping()
            return True
        except:
            return False

    async def check_service(self, name: str, config: dict) -> dict:
        """개별 서비스 상태 확인"""
        result = {"name": name, "status": "DOWN", "response_time": None, "error": None}

        if "check" in config:
            # 커스텀 체크 함수 사용
            try:
                result["status"] = "UP" if config["check"]() else "DOWN"
                result["response_time"] = 0.001  # 가상의 빠른 응답 시간
            except Exception as e:
                result["status"] = "ERROR"
                result["error"] = str(e)
        else:
            # HTTP 엔드포인트 체크
            try:
                start_time = time.time()
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(
                        f"http://localhost:{config['port']}{config['endpoint']}"
                    )
                    response_time = time.time() - start_time

                    result["status"] = "UP" if response.status_code < 400 else "DEGRADED"
                    result["response_time"] = round(response_time * 1000, 2)  # ms

            except Exception as e:
                result["status"] = "DOWN"
                result["error"] = str(e)

        return result

    def get_system_stats(self) -> dict:
        """시스템 리소스 통계 수집"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent,
            },
            "disk": {
                "total": psutil.disk_usage("/").total,
                "free": psutil.disk_usage("/").free,
                "percent": psutil.disk_usage("/").percent,
            },
            "processes": len(psutil.pids()),
        }

    async def monitor_once(self) -> dict:
        """단일 모니터링 실행"""
        timestamp = datetime.now().isoformat()

        # 서비스 상태 확인
        service_tasks = [self.check_service(name, config) for name, config in self.services.items()]
        service_results = await asyncio.gather(*service_tasks)

        # 시스템 통계 수집
        system_stats = self.get_system_stats()

        # 결과 정리
        result = {
            "timestamp": timestamp,
            "services": {r["name"]: r for r in service_results},
            "system": system_stats,
            "overall_status": "HEALTHY",
        }

        # 전체 상태 판정
        down_services = [s for s in service_results if s["status"] in ["DOWN", "ERROR"]]
        if down_services:
            result["overall_status"] = "CRITICAL"
        elif any(s["status"] == "DEGRADED" for s in service_results):
            result["overall_status"] = "WARNING"

        return result

    async def continuous_monitor(self, interval: int = 60):
        """지속적 모니터링"""
        print("🚀 AFO 왕국 시스템 모니터링 시작...")
        print(f"📊 모니터링 간격: {interval}초")
        print("-" * 50)

        while True:
            try:
                result = await self.monitor_once()

                # 콘솔 출력
                status_emoji = {"HEALTHY": "✅", "WARNING": "⚠️", "CRITICAL": "🚨"}

                print(
                    f"{status_emoji[result['overall_status']]} [{result['timestamp'][:19]}] {result['overall_status']}"
                )

                for service_name, service_data in result["services"].items():
                    status_icon = "✅" if service_data["status"] == "UP" else "❌"
                    time_info = (
                        f" ({service_data['response_time']}ms)"
                        if service_data["response_time"]
                        else ""
                    )
                    print(f"  {status_icon} {service_name}: {service_data['status']}{time_info}")

                print(
                    f"  📊 CPU: {result['system']['cpu_percent']}%, MEM: {result['system']['memory']['percent']}%"
                )
                print()

                # 로그 파일 저장
                self.save_log(result)

            except Exception as e:
                print(f"❌ 모니터링 오류: {e}")

            await asyncio.sleep(interval)

    def save_log(self, result: dict) -> None:
        """모니터링 결과 로그 저장"""
        os.makedirs("logs", exist_ok=True)
        log_file = f"logs/system_monitor_{datetime.now().strftime('%Y%m%d')}.jsonl"

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")


async def main():
    monitor = SystemMonitor()

    if len(os.sys.argv) > 1 and os.sys.argv[1] == "--once":
        # 단일 실행 모드
        result = await monitor.monitor_once()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # 지속 모니터링 모드
        await monitor.continuous_monitor(interval=60)


if __name__ == "__main__":
    asyncio.run(main())
