# Trinity Score: 90.0 (Established by Chancellor)
#!/usr/bin/env python3
"""
Mirror CLI - Command-line interface for Chancellor Mirror

Usage:
    python -m scripts.mirror.cli
    python scripts/mirror/cli.py
"""

import argparse
import asyncio
import logging
import sys

from scripts.mirror.core import ChancellorMirror
from scripts.mirror.models import MirrorConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main(config: MirrorConfig | None = None) -> None:
    """
    메인 함수: 승상의 거울 가동
    """
    print("🏰 AFO 왕국 승상의 거울 가동")
    print("=" * 50)

    # Create mirror
    mirror = ChancellorMirror(config=config)

    try:
        # Start monitoring
        await mirror.monitor_trinity_score()

    except KeyboardInterrupt:
        logger.info("🛑 승상의 거울 중지")

    except Exception as e:
        logger.error(f"❌ 승상의 거울 실행 실패: {e}")
        sys.exit(1)

    finally:
        # Cleanup
        mirror.clear_resolved_alerts()
        active_alerts = mirror.get_active_alerts()

        if active_alerts:
            print(f"\n⚠️  종료 시점 활성 알람: {len(active_alerts)}개")
            for alert in active_alerts:
                print(f"   - {alert.pillar}: {alert.message}")
        else:
            print("\n✅ 모든 알람 해결됨")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="승상의 거울 (Chancellor Mirror) - Trinity Score 모니터링",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Default settings (localhost:8010)
    python -m scripts.mirror.cli

    # Custom API base
    python -m scripts.mirror.cli --api-base http://production:8010

    # Custom alert threshold
    python -m scripts.mirror.cli --threshold 85.0
        """,
    )
    parser.add_argument(
        "--api-base",
        default="http://localhost:8010",
        help="API base URL (default: http://localhost:8010)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=90.0,
        help="Alert threshold (default: 90.0)",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=600,
        help="HTTP polling interval in seconds (default: 600)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args()


def run() -> None:
    """Entry point for CLI"""
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    config = MirrorConfig(
        api_base=args.api_base,
        alert_threshold=args.threshold,
        polling_interval_seconds=args.poll_interval,
    )

    asyncio.run(main(config))


if __name__ == "__main__":
    run()
