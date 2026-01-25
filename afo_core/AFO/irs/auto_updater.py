"""
SSOT Auto-Updater - SSOT 자동 업데이트 시스템

孝 (Serenity): 평온 수호/운영 마찰 제거
- SSOT 자동 업데이트 메커니즘
- 파라미터 자동 파싱
- 트랜잭션 기반 안전 업데이트
- 롤백 및 버전 관리
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

if TYPE_CHECKING:
    from .change_detector import ChangeDetection

from .evidence_bundle_extended import (
    ChangeLog,
    EvidenceBundleExtended,
    EvidenceBundleManager,
    TrinityScore,
)
from .hash_utils import HashUtils
from .irs_config import IRSConfig

logger = logging.getLogger(__name__)


class UpdateStatus(Enum):
    """업데이트 상태"""

    PENDING = "pending"  # 대기 중
    VALIDATING = "validating"  # 검증 중
    UPDATING = "updating"  # 업데이트 중
    COMPLETED = "completed"  # 완료
    ROLLED_BACK = "rolled_back"  # 롤백됨
    FAILED = "failed"  # 실패


@dataclass
class UpdateTransaction:
    """업데이트 트랜잭션"""

    transaction_id: str
    bundle_id: str
    document_id: str
    previous_version: str
    new_version: str
    document_type: str = ""  # SSOT 파일명에 사용
    status: UpdateStatus = UpdateStatus.PENDING
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: str | None = None
    error_message: str | None = None
    evidence_bundle: EvidenceBundleExtended | None = None

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "transaction_id": self.transaction_id,
            "bundle_id": self.bundle_id,
            "document_id": self.document_id,
            "document_type": self.document_type,
            "previous_version": self.previous_version,
            "new_version": self.new_version,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "error_message": self.error_message,
            "evidence_bundle": (self.evidence_bundle.to_dict() if self.evidence_bundle else None),
        }


class SSOTAutoUpdater:
    """
    SSOT 자동 업데이트 시스템

    변경 감지 → Trinity Score 검증 → SSOT 업데이트 → 알림
    전체 프로세스를 트랜잭션 기반으로 안전하게 처리
    """

    SSOT_PATH = Path("data/ssot")
    BACKUP_PATH = Path("data/ssot/backups")
    TRANSACTION_LOG = Path("data/transactions/log.json")

    def __init__(
        self,
        config: IRSConfig | None = None,
        min_trinity_score: float = 0.90,
    ):
        self.config = config or IRSConfig()
        self.min_trinity_score = min_trinity_score
        self.hash_utils = HashUtils()
        self.bundle_manager = EvidenceBundleManager()
        self.transactions: dict[str, UpdateTransaction] = {}
        self._init_paths()

    def _init_paths(self) -> None:
        """경로 초기화"""
        self.SSOT_PATH.mkdir(parents=True, exist_ok=True)
        self.BACKUP_PATH.mkdir(parents=True, exist_ok=True)
        self.TRANSACTION_LOG.parent.mkdir(parents=True, exist_ok=True)

    def _load_transactions(self) -> None:
        """트랜잭션 로드"""
        if self.TRANSACTION_LOG.exists():
            with open(self.TRANSACTION_LOG, encoding="utf-8") as f:
                data = json.load(f)
                for txn_data in data:
                    txn = UpdateTransaction(
                        transaction_id=txn_data["transaction_id"],
                        bundle_id=txn_data["bundle_id"],
                        document_id=txn_data["document_id"],
                        previous_version=txn_data["previous_version"],
                        new_version=txn_data["new_version"],
                        status=UpdateStatus(txn_data["status"]),
                        start_time=txn_data["start_time"],
                        end_time=txn_data["end_time"],
                        error_message=txn_data["error_message"],
                    )
                    self.transactions[txn.transaction_id] = txn

    def _save_transactions(self) -> None:
        """트랜잭션 저장"""
        data = [txn.to_dict() for txn in self.transactions.values()]
        with open(self.TRANSACTION_LOG, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _create_backup(self, ssot_file: Path) -> Path:
        """
        SSOT 파일 백업

        Args:
            ssot_file: SSOT 파일 경로

        Returns:
            백업 파일 경로
        """
        # 밀리초 포함하여 동일 초 내 여러 백업 지원
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3]  # YYYYMMDD_HHMMSSmmm
        backup_file = self.BACKUP_PATH / f"{ssot_file.stem}_{timestamp}.json"

        if ssot_file.exists():
            import shutil

            shutil.copy2(ssot_file, backup_file)
            logger.info(f"백업 생성: {backup_file}")

        return backup_file

    def _parse_tax_parameters(self, content: str, document_type: str) -> dict[str, Any]:
        """
        세법 파라미터 자동 파싱

        Args:
            content: 문서 내용
            document_type: 문서 타입

        Returns:
            파싱된 파라미터 딕셔너리
        """
        parameters = {}

        # Publication 17 주요 파라미터
        if "pub17" in document_type.lower() or "publication 17" in document_type.lower():
            # 에너지 크레딧
            if "Energy Credit" in content or "Section 25D" in content:
                parameters["energy_credit"] = self._extract_credit_info(content)

            # 전기차 크레딧
            if "Clean Vehicle" in content or "Section 30D" in content:
                parameters["electric_vehicle_credit"] = self._extract_vehicle_info(content)

            # 감가상각
            if "Depreciation" in content or "Section 179" in content:
                parameters["depreciation"] = self._extract_depreciation_info(content)

            # ERC
            if "Employee Retention Credit" in content or "ERC" in content:
                parameters["erc"] = self._extract_erc_info(content)

            # 자동차 대출 이자
            if "Vehicle Interest" in content or "Section 163" in content:
                parameters["vehicle_interest"] = self._extract_interest_info(content)

        logger.info(f"파라미터 파싱 완료: {len(parameters)}개 파라미터 추출")
        return parameters

    def _extract_credit_info(self, content: str) -> dict[str, str]:
        """에너지 크레딧 정보 추출"""
        info = {}
        if "2034" in content:
            info["extension"] = "2034년까지 연장"
        if "December 31, 2025" in content or "2025-12-31" in content:
            info["expiration"] = "2025년 12월 31일 종료"
        if "30%" in content:
            info["rate"] = "30%"
        return info

    def _extract_vehicle_info(self, content: str) -> dict[str, str]:
        """전기차 크레딧 정보 추출"""
        info = {}
        if "September 30, 2025" in content or "2025-09-30" in content:
            info["expiration"] = "2025년 9월 30일 종료"
        return info

    def _extract_depreciation_info(self, content: str) -> dict[str, str]:
        """감가상각 정보 추출"""
        info = {}
        if "January 20" in content or "2026-01-20" in content:
            info["effective_date"] = "2026년 1월 20일"
        if "100%" in content:
            info["rate"] = "100% 영구화"
        return info

    def _extract_erc_info(self, content: str) -> dict[str, str]:
        """ERC 정보 추출"""
        info = {}
        if "January 31, 2024" in content or "2024-01-31" in content:
            info["deadline"] = "2024년 1월 31일 이후 소급 금지"
        return info

    def _extract_interest_info(self, content: str) -> dict[str, str]:
        """자동차 대출 이자 정보 추출"""
        info = {}
        if "final assembly" in content or "United States" in content:
            info["requirement"] = "미국 최종 조립 신차만 공제 가능"
        return info

    def _calculate_trinity_score(
        self, change: ChangeDetection, parameters: dict[str, Any]
    ) -> TrinityScore:
        """
        Trinity Score 계산

        Args:
            change: 변경 감지 결과
            parameters: 파싱된 파라미터

        Returns:
            Trinity Score
        """
        # 眞 (Truth): 기술적 확실성
        truth_score = 1.0
        if change.impact.category == "critical":
            truth_score = 0.95  # Critical 변경은 약간의 불확실성
        elif not parameters:
            truth_score = 0.5  # 파라미터 파싱 실패

        # 善 (Goodness): 보안/리스크
        goodness_score = 1.0
        if change.impact.category == "critical":
            goodness_score = 0.85  # Critical 변경은 리스크 높음
        elif change.impact.category == "high":
            goodness_score = 0.90

        # 美 (Beauty): 단순함/일관성
        beauty_score = 1.0
        if len(parameters) == 0:
            beauty_score = 0.5  # 파라미터 없음

        # 孝 (Serenity): 평온 수호
        serenity_score = 1.0
        if change.impact.category == "critical":
            serenity_score = 0.8  # 운영 마찰 우려

        # 永 (Eternity): 영속성
        eternity_score = 1.0

        # 가중평균 (眞35% + 善35% + 美20% + 孝8% + 永2%)
        total_score = (
            (truth_score * 0.35)
            + (goodness_score * 0.35)
            + (beauty_score * 0.20)
            + (serenity_score * 0.08)
            + (eternity_score * 0.02)
        )

        return TrinityScore(
            truth=truth_score,
            goodness=goodness_score,
            beauty=beauty_score,
            serenity=serenity_score,
            eternity=eternity_score,
            total=total_score,
            calculated_at=datetime.now().isoformat(),
        )

    def process_update(
        self,
        change: ChangeDetection,
        new_content: str,
    ) -> UpdateTransaction:
        """
        업데이트 처리

        Args:
            change: 변경 감지 결과
            new_content: 새로운 문서 내용

        Returns:
            업데이트 트랜잭션
        """
        # 트랜잭션 생성
        transaction_id = f"txn_{uuid4().hex[:16]}"
        transaction = UpdateTransaction(
            transaction_id=transaction_id,
            bundle_id=str(uuid4()),
            document_id=change.document_id,
            previous_version=change.previous_hash[:16] if change.previous_hash else "N/A",
            new_version=change.current_hash[:16],
            document_type=change.document_type,
            status=UpdateStatus.VALIDATING,
        )

        self.transactions[transaction_id] = transaction

        try:
            # 1. 파라미터 파싱
            parameters = self._parse_tax_parameters(new_content, change.document_type)
            logger.info(f"파라미터 파싱 완료: {len(parameters)}개")

            # 2. Trinity Score 계산
            trinity_score = self._calculate_trinity_score(change, parameters)
            logger.info(
                f"Trinity Score: {trinity_score.total:.2%} "
                f"(眞={trinity_score.truth:.2%}, "
                f"善={trinity_score.goodness:.2%}, "
                f"美={trinity_score.beauty:.2%})"
            )

            # 3. Trinity Score 게이트
            if trinity_score.total < self.min_trinity_score:
                raise ValueError(
                    f"Trinity Score 부족: {trinity_score.total:.2%} < {self.min_trinity_score:.2%}"
                )

            # 4. Evidence Bundle 생성
            transaction.status = UpdateStatus.UPDATING
            change_log = ChangeLog(
                change_id=f"CHG-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                document_id=change.document_id,
                change_type="update",
                previous_hash=change.previous_hash,
                current_hash=change.current_hash,
                timestamp=datetime.now().isoformat(),
                severity=change.impact.category,
                summary=change.impact.description,
                impact_areas=change.impact.areas,
                evidence_bundle_id=transaction.bundle_id,
            )
            bundle = EvidenceBundleExtended(
                bundle_id=transaction.bundle_id,
                timestamp=datetime.now().isoformat(),
                created_at=datetime.now().isoformat(),
                trinity_score=trinity_score.to_dict(),
                change_logs=[change_log],
            )

            # 5. SSOT 업데이트
            ssot_file = self.SSOT_PATH / f"{change.document_type}.json"

            # 백업 생성
            backup_file = self._create_backup(ssot_file)

            # 새로운 SSOT 데이터 생성
            ssot_data = {
                "document_id": change.document_id,
                "document_type": change.document_type,
                "hash": change.current_hash,
                "last_updated": datetime.now().isoformat(),
                "parameters": parameters,
                "backup_file": str(backup_file),
                "transaction_id": transaction_id,
            }

            # SSOT 파일 저장
            with open(ssot_file, "w", encoding="utf-8") as f:
                json.dump(ssot_data, f, indent=2, ensure_ascii=False)

            # 6. Evidence Bundle 저장
            bundle.export_to_json(self.bundle_manager.storage_path / f"{bundle.bundle_id}.json")
            transaction.evidence_bundle = bundle

            # 7. 완료
            transaction.status = UpdateStatus.COMPLETED
            transaction.end_time = datetime.now().isoformat()

            logger.info(f"SSOT 업데이트 완료: {change.document_id}")
            logger.info(f"백업: {backup_file}")
            logger.info(f"Bundle ID: {bundle.bundle_id}")

        except Exception as e:
            transaction.status = UpdateStatus.FAILED
            transaction.end_time = datetime.now().isoformat()
            transaction.error_message = str(e)
            logger.error(f"업데이트 실패: {e}")

        finally:
            # 트랜잭션 저장
            self._save_transactions()

        return transaction

    def rollback(self, transaction_id: str) -> bool:
        """
        업데이트 롤백

        Args:
            transaction_id: 트랜잭션 ID

        Returns:
            롤백 성공 여부
        """
        if transaction_id not in self.transactions:
            logger.error(f"트랜잭션 없음: {transaction_id}")
            return False

        transaction = self.transactions[transaction_id]

        if transaction.status != UpdateStatus.COMPLETED:
            logger.warning(f"완료되지 않은 트랜잭션은 롤백 불가: {transaction_id}")
            return False

        try:
            # SSOT 파일 찾기 (document_type 사용)
            ssot_file = self.SSOT_PATH / f"{transaction.document_type}.json"

            if not ssot_file.exists():
                logger.error(f"SSOT 파일 없음: {ssot_file}")
                return False

            # 백업 파일에서 복원
            backup_pattern = f"{transaction.document_type}_*.json"
            backup_files = sorted(self.BACKUP_PATH.glob(backup_pattern), reverse=True)

            if not backup_files:
                logger.error(f"백업 파일 없음: {backup_pattern}")
                return False

            # 최신 백업 복원
            latest_backup = backup_files[0]
            import shutil

            shutil.copy2(latest_backup, ssot_file)
            logger.info(f"롤백 완료: {latest_backup} → {ssot_file}")

            # 트랜잭션 상태 업데이트
            transaction.status = UpdateStatus.ROLLED_BACK
            transaction.end_time = datetime.now().isoformat()
            self._save_transactions()

            return True

        except Exception as e:
            logger.error(f"롤백 실패: {e}")
            return False

    def get_transaction(self, transaction_id: str) -> UpdateTransaction | None:
        """
        트랜잭션 조회

        Args:
            transaction_id: 트랜잭션 ID

        Returns:
            트랜잭션
        """
        return self.transactions.get(transaction_id)

    def list_transactions(self, status: UpdateStatus | None = None) -> list[UpdateTransaction]:
        """
        트랜잭션 목록 조회

        Args:
            status: 필터링할 상태

        Returns:
            트랜잭션 목록
        """
        transactions = list(self.transactions.values())

        if status:
            transactions = [t for t in transactions if t.status == status]

        # 최신순 정렬
        return sorted(
            transactions,
            key=lambda t: t.start_time,
            reverse=True,  # type: ignore
        )
