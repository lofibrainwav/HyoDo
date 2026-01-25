"""
IRS Real-time Monitor (Facade)
TICKET-070: Monolith Decomposition - Part 2

기존 모놀리식 구조를 packages/afo-core/AFO/irs/monitor/ 패키지로 분할하고
본 파일은 Facade로서 하위 호환성을 유지합니다.
"""

import asyncio

# Facade Imports
from AFO.irs.monitor import IRSRealtimeMonitor

# 글로벌 인스턴스 (Service Layer)
irs_realtime_monitor = IRSRealtimeMonitor()


# 편의 함수들 (Backward Compatibility)
async def start_irs_monitoring():
    """IRS 모니터링 시작"""
    await irs_realtime_monitor.start_monitoring()


async def stop_irs_monitoring():
    """IRS 모니터링 중지"""
    await irs_realtime_monitor.stop_monitoring()


def get_monitoring_stats() -> None:
    """모니터링 통계 조회"""
    return irs_realtime_monitor.get_monitoring_stats()


def get_recent_irs_changes(limit: int = 10) -> None:
    """최근 IRS 변경 조회"""
    return irs_realtime_monitor.get_recent_changes(limit)


def trigger_manual_check() -> None:
    """수동 확인 트리거"""
    irs_realtime_monitor.force_check_now()


if __name__ == "__main__":
    # 테스트 실행
    async def test_irs_monitoring():
        print("📡 Testing IRS Realtime Monitor (Facade)...")

        # 모니터링 시작
        await start_irs_monitoring()
        print("✅ IRS Realtime Monitor started")

        # 잠시 대기 (모니터링 사이클 진행)
        await asyncio.sleep(2)

        # 통계 확인
        stats = get_monitoring_stats()
        print(f"📊 Monitoring stats: {stats}")

        # 최근 변경 확인
        recent_changes = get_recent_irs_changes(5)
        print(f"🔄 Recent changes: {len(recent_changes)} detected")

        # 수동 확인 트리거
        trigger_manual_check()
        print("🔍 Manual check triggered")

        # 추가 대기
        await asyncio.sleep(1)

        # 모니터링 중지
        await stop_irs_monitoring()
        print("✅ IRS Realtime Monitor stopped")

        print("\n✅ IRS Realtime Monitor test completed!")

    asyncio.run(test_irs_monitoring())
