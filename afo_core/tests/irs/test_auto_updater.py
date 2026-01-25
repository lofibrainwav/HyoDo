"""
SSOT Auto-Updater 테스트

pytest -v packages/afo-core/tests/irs/test_auto_updater.py
"""

import json
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from AFO.irs.auto_updater import SSOTAutoUpdater, UpdateStatus, UpdateTransaction
from AFO.irs.change_detector import ChangeDetection, ChangeImpact
from AFO.irs.evidence_bundle_extended import EvidenceBundleExtended, TrinityScore
from AFO.irs.irs_config import IRSConfig
from AFO.irs.rollback_manager import RollbackManager


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """임시 디렉토리 fixture"""
    # 기존 data 디렉토리 백업
    data_dir = Path("data")
    backup_dir = tmp_path / "data_backup"
    if data_dir.exists():
        shutil.copytree(data_dir, backup_dir)

    yield tmp_path

    # 테스트 후 정리
    if data_dir.exists():
        shutil.rmtree(data_dir)

    # 백업 복원
    if backup_dir.exists():
        shutil.copytree(backup_dir, data_dir)


@pytest.fixture
def auto_updater(temp_dir: Path) -> SSOTAutoUpdater:
    """Auto-Updater fixture"""
    return SSOTAutoUpdater(min_trinity_score=0.80)


@pytest.fixture
def sample_trinity_score() -> TrinityScore:
    """Sample Trinity Score fixture"""
    return TrinityScore(
        truth=0.95,
        goodness=0.90,
        beauty=0.85,
        serenity=0.88,
        eternity=1.0,
        total=0.90,
        calculated_at="2026-01-18T00:00:00",
    )


@pytest.fixture
def sample_change_detection() -> ChangeDetection:
    """Sample Change Detection fixture"""
    return ChangeDetection(
        change_id="CHG-2026-001",
        document_id="pub17_2025",
        previous_hash="old_hash_123",
        current_hash="abc123def456",
        detected_at="2026-01-18T00:00:00",
        impact=ChangeImpact(
            category="high",
            score=0.7,
            areas=["energy_credit", "ev_credit"],
            description="Tax credit expiration dates updated",
        ),
        document_type="IRS Publication 17",
    )


@pytest.fixture
def sample_content() -> str:
    """Sample IRS document content"""
    return """
    IRS Publication 17 (2025 Edition)

    Section 25D: Energy Credit
    - Credit rate: 30%
    - Expiration: December 31, 2025

    Section 30D: Clean Vehicle Credit
    - Expiration: September 30, 2025

    Section 179: Depreciation
    - Effective date: January 20, 2026
    - Rate: 100% (permanent)

    Section 3134: Employee Retention Credit
    - Retroactive deadline: January 31, 2024

    Section 163: Vehicle Interest Deduction
    - Requirement: Final assembly in United States
    """


class TestSSOTAutoUpdater:
    """SSOT Auto-Updater 테스트"""

    def test_init_paths(self, auto_updater: SSOTAutoUpdater) -> None:
        """경로 초기화 테스트"""
        assert auto_updater.SSOT_PATH.exists()
        assert auto_updater.BACKUP_PATH.exists()
        assert auto_updater.TRANSACTION_LOG.parent.exists()

    def test_parse_tax_parameters_energy_credit(
        self, auto_updater: SSOTAutoUpdater, sample_content: str
    ) -> None:
        """에너지 크레딧 파라미터 파싱 테스트"""
        parameters = auto_updater._parse_tax_parameters(sample_content, "IRS Publication 17")

        assert "energy_credit" in parameters
        assert "rate" in parameters["energy_credit"]
        assert parameters["energy_credit"]["rate"] == "30%"

    def test_parse_tax_parameters_vehicle_info(
        self, auto_updater: SSOTAutoUpdater, sample_content: str
    ) -> None:
        """전기차 크레딧 파라미터 파싱 테스트"""
        parameters = auto_updater._parse_tax_parameters(sample_content, "IRS Publication 17")

        assert "electric_vehicle_credit" in parameters
        assert "expiration" in parameters["electric_vehicle_credit"]

    def test_parse_tax_parameters_depreciation(
        self, auto_updater: SSOTAutoUpdater, sample_content: str
    ) -> None:
        """감가상각 파라미터 파싱 테스트"""
        parameters = auto_updater._parse_tax_parameters(sample_content, "IRS Publication 17")

        assert "depreciation" in parameters
        assert "effective_date" in parameters["depreciation"]

    def test_parse_tax_parameters_erc(
        self, auto_updater: SSOTAutoUpdater, sample_content: str
    ) -> None:
        """ERC 파라미터 파싱 테스트"""
        parameters = auto_updater._parse_tax_parameters(sample_content, "IRS Publication 17")

        assert "erc" in parameters
        assert "deadline" in parameters["erc"]

    def test_parse_tax_parameters_interest(
        self, auto_updater: SSOTAutoUpdater, sample_content: str
    ) -> None:
        """자동차 대출 이자 파라미터 파싱 테스트"""
        parameters = auto_updater._parse_tax_parameters(sample_content, "IRS Publication 17")

        assert "vehicle_interest" in parameters
        assert "requirement" in parameters["vehicle_interest"]

    def test_calculate_trinity_score_critical_change(
        self, auto_updater: SSOTAutoUpdater, sample_change_detection: ChangeDetection
    ) -> None:
        """Critical 변경에 대한 Trinity Score 계산 테스트"""
        sample_change_detection.impact = ChangeImpact(
            category="critical",
            score=0.9,
            areas=["energy_credit", "ev_credit"],
            description="Critical tax change",
        )

        trinity_score = auto_updater._calculate_trinity_score(
            sample_change_detection,
            {"energy_credit": {"rate": "30%"}},
        )

        assert trinity_score.truth < 1.0  # Critical 변경
        assert trinity_score.goodness < 1.0  # 리스크 높음
        assert trinity_score.total < 0.95  # 전체 점수 감소

    def test_calculate_trinity_score_high_change(
        self, auto_updater: SSOTAutoUpdater, sample_change_detection: ChangeDetection
    ) -> None:
        """High 변경에 대한 Trinity Score 계산 테스트"""
        sample_change_detection.impact = ChangeImpact(
            category="high",
            score=0.7,
            areas=["energy_credit"],
            description="High impact tax change",
        )

        trinity_score = auto_updater._calculate_trinity_score(
            sample_change_detection,
            {"energy_credit": {"rate": "30%"}},
        )

        assert trinity_score.goodness < 1.0  # 리스크 중간

    def test_process_update_success(
        self,
        auto_updater: SSOTAutoUpdater,
        sample_change_detection: ChangeDetection,
        sample_content: str,
    ) -> None:
        """업데이트 처리 성공 테스트"""
        transaction = auto_updater.process_update(sample_change_detection, sample_content)

        assert transaction.status == UpdateStatus.COMPLETED
        assert transaction.evidence_bundle is not None
        assert transaction.error_message is None
        assert transaction.end_time is not None

    def test_process_update_trinity_gate_failure(
        self,
        auto_updater: SSOTAutoUpdater,
        sample_change_detection: ChangeDetection,
        sample_content: str,
    ) -> None:
        """Trinity Score 게이트 실패 테스트"""
        # 낮은 Trinity Score로 실패 유도
        auto_updater.min_trinity_score = 1.0  # 불가능한 점수

        transaction = auto_updater.process_update(sample_change_detection, sample_content)

        assert transaction.status == UpdateStatus.FAILED
        assert transaction.error_message is not None
        assert "Trinity Score 부족" in transaction.error_message

    def test_create_backup(self, auto_updater: SSOTAutoUpdater, temp_dir: Path) -> None:
        """백업 생성 테스트"""
        # SSOT 파일 생성
        ssot_file = auto_updater.SSOT_PATH / "test_document.json"
        ssot_file.write_text('{"test": "data"}')

        backup_file = auto_updater._create_backup(ssot_file)

        assert backup_file.exists()
        assert backup_file.parent == auto_updater.BACKUP_PATH

    def test_transaction_persistence(
        self,
        auto_updater: SSOTAutoUpdater,
        sample_change_detection: ChangeDetection,
        sample_content: str,
    ) -> None:
        """트랜잭션 영속성 테스트"""
        transaction = auto_updater.process_update(sample_change_detection, sample_content)

        # 트랜잭션 저장 확인
        assert transaction.transaction_id in auto_updater.transactions

        # 로그 파일 확인
        assert auto_updater.TRANSACTION_LOG.exists()

        # 로드된 트랜잭션 확인
        loaded_transaction = auto_updater.get_transaction(transaction.transaction_id)
        assert loaded_transaction is not None
        assert loaded_transaction.status == transaction.status

    def test_list_transactions(
        self,
        auto_updater: SSOTAutoUpdater,
        sample_change_detection: ChangeDetection,
        sample_content: str,
    ) -> None:
        """트랜잭션 목록 조회 테스트"""
        transaction1 = auto_updater.process_update(sample_change_detection, sample_content)
        transaction2 = auto_updater.process_update(sample_change_detection, sample_content)

        transactions = auto_updater.list_transactions()

        assert len(transactions) >= 2
        assert transactions[0].start_time >= transactions[1].start_time  # 최신순 정렬

    def test_list_transactions_filtered(
        self,
        auto_updater: SSOTAutoUpdater,
        sample_change_detection: ChangeDetection,
        sample_content: str,
    ) -> None:
        """필터링된 트랜잭션 목록 조회 테스트"""
        transaction = auto_updater.process_update(sample_change_detection, sample_content)

        completed_transactions = auto_updater.list_transactions(status=UpdateStatus.COMPLETED)

        assert transaction in completed_transactions

    def test_rollback_success(
        self,
        auto_updater: SSOTAutoUpdater,
        sample_change_detection: ChangeDetection,
        sample_content: str,
    ) -> None:
        """롤백 성공 테스트"""
        # 첫 번째 업데이트 (초기 상태 생성)
        first_transaction = auto_updater.process_update(sample_change_detection, sample_content)
        assert first_transaction.status == UpdateStatus.COMPLETED

        # 두 번째 업데이트 (이때 백업 생성됨)
        transaction = auto_updater.process_update(sample_change_detection, sample_content)
        assert transaction.status == UpdateStatus.COMPLETED

        # 롤백 (두 번째 업데이트를 롤백)
        success = auto_updater.rollback(transaction.transaction_id)

        assert success is True

        # 트랜잭션 상태 확인
        rolled_back_transaction = auto_updater.get_transaction(transaction.transaction_id)
        assert rolled_back_transaction is not None
        assert rolled_back_transaction.status == UpdateStatus.ROLLED_BACK

    def test_rollback_nonexistent_transaction(self, auto_updater: SSOTAutoUpdater) -> None:
        """존재하지 않는 트랜잭션 롤백 테스트"""
        success = auto_updater.rollback("nonexistent_txn_id")

        assert success is False

    def test_rollback_incomplete_transaction(
        self,
        auto_updater: SSOTAutoUpdater,
        sample_change_detection: ChangeDetection,
        sample_content: str,
    ) -> None:
        """완료되지 않은 트랜잭션 롤백 테스트"""
        # 트랜잭션 생성 (process_update는 완료 상태로 생성됨)
        transaction = auto_updater.process_update(sample_change_detection, sample_content)

        # 수동으로 상태 변경 (시뮬레이션)
        transaction.status = UpdateStatus.VALIDATING
        auto_updater._save_transactions()

        # 롤백 시도
        success = auto_updater.rollback(transaction.transaction_id)

        assert success is False


class TestRollbackManager:
    """Rollback Manager 테스트"""

    @pytest.fixture
    def rollback_manager(self, auto_updater: SSOTAutoUpdater) -> RollbackManager:
        """Rollback Manager fixture"""
        return RollbackManager(auto_updater)

    def test_init_paths(self, rollback_manager: RollbackManager) -> None:
        """경로 초기화 테스트"""
        assert rollback_manager.ROLLBACK_LOG.parent.exists()

    def test_create_rollback_snapshot(
        self,
        rollback_manager: RollbackManager,
        auto_updater: SSOTAutoUpdater,
        sample_change_detection: ChangeDetection,
        sample_content: str,
    ) -> None:
        """롤백 스냅샷 생성 테스트"""
        # SSOT 파일 생성
        ssot_file = auto_updater.SSOT_PATH / "test_document.json"
        ssot_file.write_text('{"test": "data"}')

        transaction = auto_updater.process_update(sample_change_detection, sample_content)

        backup_path = rollback_manager.create_rollback_snapshot(
            transaction.transaction_id, ssot_file
        )

        assert Path(backup_path).exists()

    def test_rollback_transaction_success(
        self,
        rollback_manager: RollbackManager,
        auto_updater: SSOTAutoUpdater,
        sample_change_detection: ChangeDetection,
        sample_content: str,
    ) -> None:
        """트랜잭션 롤백 성공 테스트"""
        # 첫 번째 업데이트 (초기 상태 생성)
        auto_updater.process_update(sample_change_detection, sample_content)

        # 두 번째 업데이트 (이때 백업 생성됨)
        transaction = auto_updater.process_update(sample_change_detection, sample_content)

        rollback_op = rollback_manager.rollback_transaction(transaction.transaction_id)

        assert rollback_op.status.name == "COMPLETED"
        assert rollback_op.error_message is None

    def test_rollback_to_version(
        self,
        rollback_manager: RollbackManager,
        auto_updater: SSOTAutoUpdater,
        sample_change_detection: ChangeDetection,
        sample_content: str,
    ) -> None:
        """특정 버전 롤백 테스트"""
        # 첫 번째 업데이트 (초기 상태 생성)
        auto_updater.process_update(sample_change_detection, sample_content)

        # 두 번째 업데이트 (이때 백업 생성됨)
        transaction = auto_updater.process_update(sample_change_detection, sample_content)

        # 버전 목록 조회 (document_type 사용)
        versions = rollback_manager.list_rollback_versions(transaction.document_type)

        assert len(versions) > 0

        # 특정 버전 롤백
        rollback_op = rollback_manager.rollback_to_version(
            transaction.document_type, versions[0]["timestamp"]
        )

        assert rollback_op.status.name == "COMPLETED"

    def test_list_rollback_versions(
        self,
        rollback_manager: RollbackManager,
        auto_updater: SSOTAutoUpdater,
        sample_change_detection: ChangeDetection,
        sample_content: str,
    ) -> None:
        """롤백 버전 목록 조회 테스트"""
        # 첫 번째 업데이트 (초기 상태 생성)
        auto_updater.process_update(sample_change_detection, sample_content)

        # 두 번째 업데이트 (이때 백업 생성됨)
        transaction = auto_updater.process_update(sample_change_detection, sample_content)

        # document_type 사용
        versions = rollback_manager.list_rollback_versions(transaction.document_type)

        assert len(versions) > 0
        assert "timestamp" in versions[0]
        assert "hash" in versions[0]

    @pytest.mark.skip(reason="Flaky in CI environment")
    def test_cleanup_old_backups(
        self,
        rollback_manager: RollbackManager,
        auto_updater: SSOTAutoUpdater,
        sample_change_detection: ChangeDetection,
        sample_content: str,
    ) -> None:
        """오래된 백업 정리 테스트"""
        # 여러 번 업데이트하여 백업 생성
        for _ in range(10):
            auto_updater.process_update(sample_change_detection, sample_content)

        deleted_count = rollback_manager.cleanup_old_backups(keep_versions=5)

        assert deleted_count > 0
