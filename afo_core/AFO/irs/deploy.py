"""
Deploy Script - 프로덕션 배포 스크립트

孝 (Serenity): 평온 수호/운영 마찰 제거
- 프로덕션 배포 자동화
- 환경 설정 및 검증
- 롤백 지원
"""

from __future__ import annotations

import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path

from .production_config import IRSProductionConfig

logger = logging.getLogger(__name__)


class DeploymentManager:
    """
    배포 관리자

    프로덕션 환경 배포:
    - 환경 설정 검증
    - 디렉토리 생성
    - 로깅 설정
    - 서비스 시작
    """

    def __init__(self, config: IRSProductionConfig | None = None) -> None:
        self.config = config or IRSProductionConfig.from_env()
        self._setup_logging()

    def _setup_logging(self) -> None:
        """로깅 설정"""
        log_file = Path(self.config.IRS_LOG_FILE)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        import logging.handlers

        # File Handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.config.IRS_LOG_MAX_SIZE_MB * 1024 * 1024,
            backupCount=self.config.IRS_LOG_BACKUP_COUNT,
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        # Logger 설정
        logging.basicConfig(
            level=getattr(logging, self.config.IRS_LOG_LEVEL.upper()),
            handlers=[file_handler, console_handler],
        )

        logger.info("로깅 설정 완료")

    def validate_config(self) -> bool:
        """
        설정 검증

        Returns:
            유효성 여부
        """
        logger.info("설정 검증 시작")

        try:
            self.config.validate()
            logger.info("✅ 설정 검증 통과")
            return True

        except ValueError as e:
            logger.error(f"❌ 설정 검증 실패: {e}")
            return False

    def create_directories(self) -> bool:
        """
        디렉토리 생성

        Returns:
            성공 여부
        """
        logger.info("디렉토리 생성 시작")

        directories = [
            self.config.IRS_SSOT_PATH,
            self.config.IRS_BACKUP_PATH,
            self.config.IRS_EVIDENCE_PATH,
            self.config.IRS_CACHE_DIR,
            self.config.IRS_TRANSACTION_LOG.rpartition("/")[0],
            self.config.IRS_ROLLBACK_LOG.rpartition("/")[0],
            self.config.IRS_ALERTS_FILE.rpartition("/")[0],
            self.config.IRS_SCHEDULER_STATE.rpartition("/")[0],
            Path("data/keys"),
            Path("logs"),
        ]

        for dir_path in directories:
            dir_path = Path(dir_path)
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ 디렉토리 생성: {dir_path}")

        logger.info("✅ 모든 디렉토리 생성 완료")
        return True

    def setup_encryption_key(self) -> bool:
        """
        암호화 키 설정

        Returns:
            성공 여부
        """
        logger.info("암호화 키 설정 시작")

        key_file = Path(self.config.IRS_ENCRYPTION_KEY_FILE)

        if key_file.exists():
            logger.info(f"✅ 암호화 키 이미 존재: {key_file}")
            return True

        try:
            from .encryption_utils import EncryptionUtils

            # 암호화 유틸리티 인스턴스 생성
            encryption_utils = EncryptionUtils()

            # 키 생성
            key = encryption_utils.generate_key()

            # 키 저장
            key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(key_file, "w", encoding="utf-8") as f:
                f.write(key)

            # 파일 권한 설정 (읽기 전용)
            key_file.chmod(0o400)

            logger.info(f"✅ 암호화 키 생성: {key_file}")
            return True

        except Exception as e:
            logger.error(f"❌ 암호화 키 생성 실패: {e}")
            return False

    def run_health_check(self) -> bool:
        """
        Health Check 실행

        Returns:
            성공 여부
        """
        logger.info("Health Check 시작")

        checks = {
            "directories": self._check_directories(),
            "encryption_key": self._check_encryption_key(),
            "cache_dir": self._check_cache_dir(),
        }

        all_passed = all(checks.values())

        if all_passed:
            logger.info("✅ Health Check 통과")
        else:
            logger.error("❌ Health Check 실패")

        return all_passed

    def _check_directories(self) -> bool:
        """디렉토리 체크"""
        directories = [
            self.config.IRS_SSOT_PATH,
            self.config.IRS_BACKUP_PATH,
            self.config.IRS_EVIDENCE_PATH,
            self.config.IRS_CACHE_DIR,
        ]

        for dir_path in directories:
            if not Path(dir_path).exists():
                logger.error(f"❌ 디렉토리 없음: {dir_path}")
                return False

        return True

    def _check_encryption_key(self) -> bool:
        """암호화 키 체크"""
        key_file = Path(self.config.IRS_ENCRYPTION_KEY_FILE)

        if not key_file.exists():
            logger.error(f"❌ 암호화 키 없음: {key_file}")
            return False

        return True

    def _check_cache_dir(self) -> bool:
        """캐시 디렉토리 체크"""
        cache_dir = Path(self.config.IRS_CACHE_DIR)

        if not cache_dir.exists():
            logger.error(f"❌ 캐시 디렉토리 없음: {cache_dir}")
            return False

        return True

    async def start_scheduler(self) -> bool:
        """
        스케줄러 시작

        Returns:
            성공 여부
        """
        logger.info("스케줄러 시작")

        try:
            from .julie_integration import JulieCPAIntegrator
            from .live_crawler import IRSLiveCrawler
            from .notification_template import NotificationManager
            from .scheduler import IRSMonitorScheduler

            # 스케줄러 컴포넌트 초기화
            IRSLiveCrawler()
            auto_updater = None  # Auto-updater는 필요할 때 초기화
            notification_manager = NotificationManager()
            JulieCPAIntegrator(
                auto_updater=auto_updater,
                notification_manager=notification_manager,
            )

            # 스케줄러 초기화
            scheduler = IRSMonitorScheduler()

            # 기본 작업 추가 (간단한 구현)
            scheduler.add_job("irs-monitor-job", interval_hours=24)
            logger.info("✅ 기본 모니터링 작업 추가")

            # 스케줄러 시작
            await scheduler.start()
            logger.info("✅ 스케줄러 시작")

            return True

        except Exception as e:
            logger.error(f"❌ 스케줄러 시작 실패: {e}")
            return False

    async def deploy(self) -> bool:
        """
        배포

        Returns:
            성공 여부
        """
        logger.info("=" * 60)
        logger.info("배포 시작")
        logger.info("=" * 60)

        # 1. 설정 검증
        if not self.validate_config():
            logger.error("❌ 배포 실패: 설정 검증 실패")
            return False

        # 2. 디렉토리 생성
        if not self.create_directories():
            logger.error("❌ 배포 실패: 디렉토리 생성 실패")
            return False

        # 3. 암호화 키 설정
        if not self.setup_encryption_key():
            logger.error("❌ 배포 실패: 암호화 키 설정 실패")
            return False

        # 4. Health Check
        if not self.run_health_check():
            logger.error("❌ 배포 실패: Health Check 실패")
            return False

        # 5. 스케줄러 시작
        if not await self.start_scheduler():
            logger.error("❌ 배포 실패: 스케줄러 시작 실패")
            return False

        logger.info("=" * 60)
        logger.info("✅ 배포 성공")
        logger.info("=" * 60)

        return True

    async def rollback(self) -> bool:
        """
        롤백

        Returns:
            성공 여부
        """
        logger.info("=" * 60)
        logger.info("롤백 시작")
        logger.info("=" * 60)

        try:
            # 스케줄러 정지
            from .scheduler import IRSMonitorScheduler

            scheduler = IRSMonitorScheduler()
            await scheduler.stop()
            logger.info("✅ 스케줄러 정지")

            # 데이터 백업
            backup_dir = Path("data/backup") / datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copytree("data", backup_dir)
            logger.info(f"✅ 데이터 백업: {backup_dir}")

            logger.info("=" * 60)
            logger.info("✅ 롤백 완료")
            logger.info("=" * 60)

            return True

        except Exception as e:
            logger.error(f"❌ 롤백 실패: {e}")
            return False


def main() -> int:
    """
    메인 함수

    Returns:
        종료 코드
    """
    import argparse

    parser = argparse.ArgumentParser(description="IRS Monitor Agent 배포")
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="배포",
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="롤백",
    )
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Health Check",
    )

    args = parser.parse_args()

    # 배포 관리자 초기화
    deploy_manager = DeploymentManager()

    # 명령어 실행
    if args.deploy:
        import asyncio

        success = asyncio.run(deploy_manager.deploy())
    elif args.rollback:
        import asyncio

        success = asyncio.run(deploy_manager.rollback())
    elif args.health_check:
        success = deploy_manager.run_health_check()
    else:
        parser.print_help()
        return 0

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
