"""
Rollback Manager - 롤백 관리 시스템

孝 (Serenity): 평온 수호/운영 마찰 제거
- 롤백 메커니즘
- 버전 관리
- 실패 시 복구 쉬움
"""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

from .auto_updater import SSOTAutoUpdater, UpdateStatus

logger = logging.getLogger(__name__)


class RollbackStatus(Enum):
    """롤백 상태"""

    PENDING = "pending"  # 대기 중
    ROLLING_BACK = "rolling_back"  # 롤백 중
    COMPLETED = "completed"  # 완료
    FAILED = "failed"  # 실피


@dataclass
class RollbackOperation:
    """롤백 작업"""

    rollback_id: str
    transaction_id: str
    status: RollbackStatus = RollbackStatus.PENDING
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: str | None = None
    backup_file: str | None = None
    target_file: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "rollback_id": self.rollback_id,
            "transaction_id": self.transaction_id,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "backup_file": self.backup_file,
            "target_file": self.target_file,
            "error_message": self.error_message,
        }


class RollbackManager:
    """
    롤백 관리자

    업데이트 실패 시 안전한 롤백 메커니즘 제공
    """

    ROLLBACK_LOG = Path("data/rollbacks/log.json")
    MAX_ROLLBACK_VERSIONS = 10  # 최대 롤백 버전 수

    def __init__(self, auto_updater: SSOTAutoUpdater | None = None) -> None:
        self.auto_updater = auto_updater or SSOTAutoUpdater()
        self.rollbacks: dict[str, RollbackOperation] = {}
        self.ROLLBACK_LOG.parent.mkdir(parents=True, exist_ok=True)
        self._load_rollbacks()

    def _load_rollbacks(self) -> None:
        """롤백 로드"""
        if self.ROLLBACK_LOG.exists():
            with open(self.ROLLBACK_LOG, encoding="utf-8") as f:
                data = json.load(f)
                for rollback_data in data:
                    rollback = RollbackOperation(
                        rollback_id=rollback_data["rollback_id"],
                        transaction_id=rollback_data["transaction_id"],
                        status=RollbackStatus(rollback_data["status"]),
                        start_time=rollback_data["start_time"],
                        end_time=rollback_data["end_time"],
                        backup_file=rollback_data["backup_file"],
                        target_file=rollback_data["target_file"],
                        error_message=rollback_data["error_message"],
                    )
                    self.rollbacks[rollback.rollback_id] = rollback

    def _save_rollbacks(self) -> None:
        """롤백 저장"""
        self.ROLLBACK_LOG.parent.mkdir(parents=True, exist_ok=True)
        data = [rb.to_dict() for rb in self.rollbacks.values()]
        with open(self.ROLLBACK_LOG, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _find_backup_file(self, ssot_file: Path) -> Path | None:
        """
        백업 파일 찾기

        Args:
            ssot_file: SSOT 파일 경로

        Returns:
            가장 최근 백업 파일
        """
        backup_pattern = f"{ssot_file.stem}_*.json"
        backup_files = sorted(self.auto_updater.BACKUP_PATH.glob(backup_pattern), reverse=True)

        if backup_files:
            return backup_files[0]

        return None

    def create_rollback_snapshot(self, transaction_id: str, ssot_file: Path) -> str:
        """
        롤백 스냅샷 생성

        Args:
            transaction_id: 트랜잭션 ID
            ssot_file: SSOT 파일 경로

        Returns:
            백업 파일 경로
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        rollback_dir = self.auto_updater.BACKUP_PATH / "snapshots"
        rollback_dir.mkdir(parents=True, exist_ok=True)

        backup_file = rollback_dir / f"{ssot_file.stem}_{timestamp}.json"

        if ssot_file.exists():
            shutil.copy2(ssot_file, backup_file)
            logger.info(f"롤백 스냅샷 생성: {backup_file}")

            return str(backup_file)

        raise FileNotFoundError(f"SSOT 파일 없음: {ssot_file}")

    def rollback_transaction(self, transaction_id: str, force: bool = False) -> RollbackOperation:
        """
        트랜잭션 롤백

        Args:
            transaction_id: 트랜잭션 ID
            force: 강제 롤백

        Returns:
            롤백 작업
        """
        # 롤백 작업 생성
        rollback_id = f"rb_{uuid4().hex[:16]}"
        rollback = RollbackOperation(
            rollback_id=rollback_id,
            transaction_id=transaction_id,
            status=RollbackStatus.ROLLING_BACK,
        )

        self.rollbacks[rollback_id] = rollback

        try:
            # 트랜잭션 확인
            transaction = self.auto_updater.get_transaction(transaction_id)

            if not transaction:
                raise ValueError(f"트랜잭션 없음: {transaction_id}")

            # 강제 롤백이 아니고, 완료되지 않은 트랜잭션은 롤백 불가
            if not force and transaction.status != UpdateStatus.COMPLETED:
                raise ValueError(f"완료되지 않은 트랜잭션은 롤백 불가: {transaction.status.value}")

            # SSOT 파일 경로 (document_type 사용)
            ssot_file = self.auto_updater.SSOT_PATH / f"{transaction.document_type}.json"

            if not ssot_file.exists():
                raise FileNotFoundError(f"SSOT 파일 없음: {ssot_file}")

            # 백업 파일 찾기
            backup_file = self._find_backup_file(ssot_file)

            if not backup_file:
                raise FileNotFoundError("백업 파일 없음")

            rollback.backup_file = str(backup_file)
            rollback.target_file = str(ssot_file)

            # 롤백 수행
            shutil.copy2(backup_file, ssot_file)

            logger.info(f"롤백 완료: {backup_file} → {ssot_file}")

            # 트랜잭션 상태 업데이트
            transaction.status = UpdateStatus.ROLLED_BACK
            transaction.end_time = datetime.now().isoformat()
            self.auto_updater._save_transactions()

            # 롤백 작업 완료
            rollback.status = RollbackStatus.COMPLETED
            rollback.end_time = datetime.now().isoformat()

        except Exception as e:
            rollback.status = RollbackStatus.FAILED
            rollback.end_time = datetime.now().isoformat()
            rollback.error_message = str(e)
            logger.error(f"롤백 실패: {e}")

        finally:
            self._save_rollbacks()

        return rollback

    def rollback_to_version(self, document_id: str, version_timestamp: str) -> RollbackOperation:
        """
        특정 버전으로 롤백

        Args:
            document_id: 문서 ID
            version_timestamp: 버전 타임스탬프

        Returns:
            롤백 작업
        """
        # 롤백 작업 생성
        rollback_id = f"rb_{uuid4().hex[:16]}"
        rollback = RollbackOperation(
            rollback_id=rollback_id,
            transaction_id="MANUAL",
            status=RollbackStatus.ROLLING_BACK,
        )

        self.rollbacks[rollback_id] = rollback

        try:
            # SSOT 파일 경로
            ssot_file = self.auto_updater.SSOT_PATH / f"{document_id}.json"

            if not ssot_file.exists():
                raise FileNotFoundError(f"SSOT 파일 없음: {ssot_file}")

            # 특정 버전 백업 파일 찾기
            backup_pattern = f"{ssot_file.stem}_{version_timestamp}*.json"
            backup_files = list(self.auto_updater.BACKUP_PATH.glob(backup_pattern))

            if not backup_files:
                raise FileNotFoundError(f"버전 {version_timestamp} 백업 파일 없음")

            backup_file = backup_files[0]

            # 현재 상태 스냅샷 생성
            self.create_rollback_snapshot(rollback_id, ssot_file)

            rollback.backup_file = str(backup_file)
            rollback.target_file = str(ssot_file)

            # 롤백 수행
            shutil.copy2(backup_file, ssot_file)

            logger.info(f"버전 롤백 완료: {backup_file} → {ssot_file} (버전: {version_timestamp})")

            rollback.status = RollbackStatus.COMPLETED
            rollback.end_time = datetime.now().isoformat()

        except Exception as e:
            rollback.status = RollbackStatus.FAILED
            rollback.end_time = datetime.now().isoformat()
            rollback.error_message = str(e)
            logger.error(f"버전 롤백 실패: {e}")

        finally:
            self._save_rollbacks()

        return rollback

    def list_rollback_versions(self, document_id: str) -> list[dict[str, Any]]:
        """
        롤백 가능한 버전 목록

        Args:
            document_id: 문서 ID

        Returns:
            버전 목록
        """
        ssot_file = self.auto_updater.SSOT_PATH / f"{document_id}.json"
        backup_pattern = f"{ssot_file.stem}_*.json"
        backup_files = sorted(self.auto_updater.BACKUP_PATH.glob(backup_pattern), reverse=True)

        versions = []
        for backup_file in backup_files:
            # 백업 파일에서 메타데이터 추출
            try:
                with open(backup_file, encoding="utf-8") as f:
                    data = json.load(f)

                # 타임스탬프는 마지막 2개 파트 (YYYYMMDD_HHMMSS)
                parts = backup_file.stem.split("_")
                timestamp = "_".join(parts[-2:]) if len(parts) >= 2 else parts[-1]
                versions.append(
                    {
                        "file": str(backup_file),
                        "timestamp": timestamp,
                        "last_updated": data.get("last_updated", "N/A"),
                        "hash": data.get("hash", "N/A"),
                    }
                )
            except Exception as e:
                logger.warning(f"백업 파일 읽기 실패: {backup_file}, {e}")

        return versions

    def cleanup_old_backups(self, keep_versions: int = 5) -> int:
        """
        오래된 백업 정리

        Args:
            keep_versions: 유지할 최소 버전 수

        Returns:
            삭제된 백업 파일 수
        """
        deleted_count = 0

        # 모든 백업 파일 목록
        all_backups = list(self.auto_updater.BACKUP_PATH.glob("*.json"))

        # 문서별로 그룹화
        backups_by_document: dict[str, list[Path]] = {}
        for backup_file in all_backups:
            # 파일명에서 문서 ID 추출 (pattern: {document_type}_{YYYYMMDD}_{HHMMSS}.json)
            parts = backup_file.stem.split("_")
            if len(parts) >= 3:
                # 마지막 2개 파트(날짜_시간)를 제외한 나머지가 document_type
                document_id = "_".join(parts[:-2])
                if document_id not in backups_by_document:
                    backups_by_document[document_id] = []
                backups_by_document[document_id].append(backup_file)

        # 문서별로 오래된 백업 삭제
        for document_id, backups in backups_by_document.items():
            # 최신순 정렬
            backups.sort(reverse=True)

            # 유지할 버전 제외하고 삭제
            for backup_file in backups[keep_versions:]:
                try:
                    backup_file.unlink()
                    deleted_count += 1
                    logger.info(f"오래된 백업 삭제: {backup_file}")
                except Exception as e:
                    logger.error(f"백업 삭제 실패: {backup_file}, {e}")

        return deleted_count

    def get_rollback(self, rollback_id: str) -> RollbackOperation | None:
        """
        롤백 작업 조회

        Args:
            rollback_id: 롤백 ID

        Returns:
            롤백 작업
        """
        return self.rollbacks.get(rollback_id)

    def list_rollbacks(self, status: RollbackStatus | None = None) -> list[RollbackOperation]:
        """
        롤백 작업 목록

        Args:
            status: 필터링할 상태

        Returns:
            롤백 작업 목록
        """
        rollbacks = list(self.rollbacks.values())

        if status:
            rollbacks = [rb for rb in rollbacks if rb.status == status]

        # 최신순 정렬
        return sorted(
            rollbacks,
            key=lambda rb: rb.start_time,
            reverse=True,  # type: ignore
        )
