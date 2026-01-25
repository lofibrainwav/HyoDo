#!/usr/bin/env python3
"""
TICKET-059: Phase 36 자율 진화 시스템 시작 스크립트
Council of Minds가 스스로 왕국을 진단하고 티켓을 발행하는 완전 자동화 루프

사용법:
- python start_autonomous_evolution.py --once : 단일 모니터링 실행
- python start_autonomous_evolution.py --continuous : 지속적 모니터링 시작
- python start_autonomous_evolution.py --help : 도움말

기능:
- Cron 기반 주기적 건강 진단 (기본: 1시간)
- Trinity Score 모니터링 및 이상 감지
- Council of Minds 자동 분석
- 자동 티켓 발행 (TICKET-064)
- 모니터링 데이터 영속 저장

철학: "왕국이 잠든 사이에도 책사들이 깨어 있어야 합니다."
"""

import argparse
import asyncio
import logging
import signal
import sys
from pathlib import Path

# AFO 모듈 임포트
try:
    from AFO.config.settings import get_settings

    # 설정 로드 (로깅 설정 전에 필요)
    settings = get_settings()

    # Logging Setup
    log_file = Path(settings.BASE_DIR) / "data" / "monitoring" / "afo_evolution.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(str(log_file))],
    )
    logger = logging.getLogger("autonomous_evolution")

    from AFO.evolution.auto_monitor import AutoMonitor

    logger.info("✅ AFO modules loaded successfully")
except ImportError as e:
    # loguru가 없으면 표준 logging 사용
    import logging as std_logging

    std_logger = std_logging.getLogger("autonomous_evolution")
    std_logger.error(f"❌ Failed to import AFO modules: {e}")
    std_logger.error(
        "💡 Make sure you're running from the correct directory with proper PYTHONPATH"
    )
    sys.exit(1)

# 설정 로드
settings = get_settings()


class AutonomousEvolutionSystem:
    """Phase 36 자율 진화 시스템 메인 클래스"""

    def __init__(self) -> None:
        self.monitor = AutoMonitor()
        self.running = False
        logger.info("🏰 Autonomous Evolution System initialized")
        logger.info(f"📊 Monitoring interval: {settings.AUTO_MONITOR_INTERVAL} seconds")
        logger.info(f"📁 Data directory: {settings.BASE_DIR}/data/monitoring")

    async def run_once(self) -> None:
        """단일 모니터링 사이클 실행"""
        logger.info("🔄 Starting single monitoring cycle...")
        result = await self.monitor.run_monitoring_cycle()

        if result["success"]:
            logger.info("✅ Single cycle completed successfully")
            print(f"📊 Issues detected: {result['issues_count']}")
            print(f"🎫 Tickets generated: {result['tickets_generated']}")
        else:
            logger.error(f"❌ Single cycle failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)

    async def run_continuous(self) -> None:
        """지속적 모니터링 시작"""
        logger.info("🌟 Starting continuous autonomous evolution (Phase 36)")
        logger.info("💡 Press Ctrl+C to stop the system")

        self.running = True

        # 시그널 핸들러 설정
        def signal_handler(_signum, _frame) -> None:
            logger.info("🛑 Shutdown signal received")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            await self.monitor.start_continuous_monitoring()
        except KeyboardInterrupt:
            logger.info("🛑 System stopped by user")
        except Exception as e:
            logger.error(f"💥 Continuous monitoring failed: {e}")
        finally:
            logger.info("🏰 Autonomous Evolution System shutting down")
            self.monitor.stop_monitoring()

    async def show_status(self) -> None:
        """현재 시스템 상태 표시"""
        logger.info("📊 Autonomous Evolution System Status")

        # 모니터링 디렉토리 확인
        monitoring_dir = Path(settings.BASE_DIR) / "data" / "monitoring"
        if monitoring_dir.exists():
            json_files = list(monitoring_dir.glob("*.json"))
            logger.info(f"📁 Monitoring data files: {len(json_files)}")

            if json_files:
                latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
                logger.info(f"📄 Latest monitoring file: {latest_file.name}")
        else:
            logger.warning("⚠️ Monitoring directory not found")

        # 최근 모니터링 결과 표시
        if hasattr(self.monitor, "last_health_check") and self.monitor.last_health_check:
            from datetime import datetime

            last_check_time = datetime.fromtimestamp(self.monitor.last_health_check)
            logger.info(f"⏰ Last health check: {last_check_time}")
        else:
            logger.info("⏰ No health checks performed yet")


def main() -> None:
    """메인 함수"""
    print("🏰 AFO Kingdom - Phase 36 Autonomous Evolution System")
    print("眞善美孝永 - Council of Minds 자율 진화")
    print("=" * 60)

    parser = argparse.ArgumentParser(
        description="Phase 36 - Autonomous Evolution System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  %(prog)s --once                    # 단일 모니터링 실행
  %(prog)s --continuous              # 지속적 모니터링 시작
  %(prog)s --status                  # 시스템 상태 확인
  %(prog)s --continuous --interval 1800  # 30분 간격으로 실행

주의사항:
- --continuous 모드는 백그라운드에서 실행됩니다
- 중지하려면 Ctrl+C를 누르세요
- 모니터링 데이터는 data/monitoring/ 에 저장됩니다
        """,
    )

    parser.add_argument("--once", action="store_true", help="단일 모니터링 사이클 실행")

    parser.add_argument(
        "--continuous", action="store_true", help="지속적 모니터링 시작 (Cron 대체)"
    )

    parser.add_argument("--status", action="store_true", help="현재 시스템 상태 표시")

    parser.add_argument(
        "--interval",
        type=int,
        default=settings.AUTO_MONITOR_INTERVAL,
        help=f"모니터링 간격 (초), 기본값: {settings.AUTO_MONITOR_INTERVAL}",
    )

    args = parser.parse_args()

    # 유효성 검증
    if not any([args.once, args.continuous, args.status]):
        parser.print_help()
        print("\n❌ 실행 모드를 선택해주세요 (--once, --continuous, --status 중 하나)")
        sys.exit(1)

    if sum([args.once, args.continuous, args.status]) > 1:
        print("❌ 하나의 실행 모드만 선택해주세요")
        sys.exit(1)

    # 시스템 초기화
    try:
        system = AutonomousEvolutionSystem()
    except Exception as e:
        logger.error(f"❌ Failed to initialize system: {e}")
        sys.exit(1)

    # 실행
    try:
        if args.once:
            asyncio.run(system.run_once())
            print("✅ Single monitoring cycle completed")

        elif args.continuous:
            print(f"🔄 Starting continuous monitoring (interval: {args.interval}s)")
            print("💡 Press Ctrl+C to stop")
            asyncio.run(system.run_continuous())

        elif args.status:
            asyncio.run(system.show_status())

    except KeyboardInterrupt:
        print("\n🛑 System stopped by user")
    except Exception as e:
        logger.error(f"💥 System execution failed: {e}")
        sys.exit(1)

    print("🏰 Autonomous Evolution System execution completed")


if __name__ == "__main__":
    main()
