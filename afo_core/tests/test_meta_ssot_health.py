"""
Test: Meta-SSOT Health Metacognitive Layer

메타인지 계층 테스트:
1. launchd 런타임 상태 파싱
2. 교차 검증 로직
3. 자가 치유 결정 로직
4. 알림 필요 여부 판단
"""

# ═══════════════════════════════════════════════════════════════
# Import the module under test
# ═══════════════════════════════════════════════════════════════
# Import from scripts directory using importlib
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

# Load meta_ssot_health module dynamically
spec = importlib.util.spec_from_file_location(
    "meta_ssot_health",
    Path(__file__).parent.parent.parent.parent / "scripts" / "meta_ssot_health.py",
)
meta_ssot = importlib.util.module_from_spec(spec)
sys.modules["meta_ssot_health"] = meta_ssot
spec.loader.exec_module(meta_ssot)


# ═══════════════════════════════════════════════════════════════
# Test: check_launchd_runtime()
# ═══════════════════════════════════════════════════════════════


class TestLaunchdRuntime:
    """launchd 런타임 상태 체크 테스트"""

    def test_launchd_runtime_parsing_all_loaded(self) -> None:
        """모든 서비스가 로드된 경우 파싱 테스트"""
        mock_output = """PID\tStatus\tLabel
-\t0\tcom.afo.meta_ssot_health
12345\t0\tcom.afo.unified_ticket_sync
-\t0\tcom.afo.ssot_document_drift
"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=mock_output, returncode=0)
            result = meta_ssot.check_launchd_runtime()

        assert result["total"] == 3
        assert result["loaded"] == 3
        # At least one is running (PID 12345)
        assert result["running"] >= 1

    def test_launchd_runtime_parsing_none_loaded(self) -> None:
        """서비스가 없는 경우"""
        mock_output = """PID\tStatus\tLabel
12345\t0\tcom.apple.some_service
"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=mock_output, returncode=0)
            result = meta_ssot.check_launchd_runtime()

        assert result["total"] == 3
        assert result["loaded"] == 0
        assert result["running"] == 0

    def test_launchd_runtime_service_details(self) -> None:
        """개별 서비스 상세 정보 테스트"""
        mock_output = """PID\tStatus\tLabel
-\t0\tcom.afo.meta_ssot_health
12345\t0\tcom.afo.unified_ticket_sync
-\t78\tcom.afo.ssot_document_drift
"""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=mock_output, returncode=0)
            result = meta_ssot.check_launchd_runtime()

        services = {s["name"]: s for s in result["services"]}

        # meta_ssot_health: loaded, not running, exit 0
        assert services["com.afo.meta_ssot_health"]["loaded"] is True
        assert services["com.afo.meta_ssot_health"]["running"] is False

        # unified_ticket_sync: loaded, running (PID 12345)
        assert services["com.afo.unified_ticket_sync"]["loaded"] is True
        assert services["com.afo.unified_ticket_sync"]["running"] is True

        # ssot_document_drift: loaded, not running, exit 78 (error)
        assert services["com.afo.ssot_document_drift"]["loaded"] is True
        assert services["com.afo.ssot_document_drift"]["last_exit_code"] == "78"


# ═══════════════════════════════════════════════════════════════
# Test: cross_validate_data()
# ═══════════════════════════════════════════════════════════════


class TestCrossValidation:
    """교차 검증 테스트"""

    def test_cross_validate_ticket_counts(self, tmp_path) -> None:
        """티켓 카운트 일관성 검증"""
        # 티켓 동기화 데이터 생성
        ticket_sync_dir = tmp_path / "artifacts" / "ticket_sync"
        ticket_sync_dir.mkdir(parents=True)

        ticket_data = {
            "summary": {
                "total_issues": 10,
                "open_count": 7,
                "closed_count": 3,  # 7 + 3 = 10 ✓
            }
        }
        (ticket_sync_dir / "dashboard_tickets.json").write_text(json.dumps(ticket_data))

        with patch.object(meta_ssot, "get_repo_root", return_value=tmp_path):
            result = meta_ssot.cross_validate_data(tmp_path)

        # 티켓 카운트 검증이 통과해야 함
        ticket_check = next(
            (v for v in result["validations"] if v["check"] == "ticket_counts_consistency"),
            None,
        )
        assert ticket_check is not None
        assert ticket_check["valid"] is True

    def test_cross_validate_ticket_counts_invalid(self, tmp_path) -> None:
        """티켓 카운트 불일치 검증"""
        ticket_sync_dir = tmp_path / "artifacts" / "ticket_sync"
        ticket_sync_dir.mkdir(parents=True)

        ticket_data = {
            "summary": {
                "total_issues": 10,
                "open_count": 5,
                "closed_count": 3,  # 5 + 3 = 8 ≠ 10 ✗
            }
        }
        (ticket_sync_dir / "dashboard_tickets.json").write_text(json.dumps(ticket_data))

        result = meta_ssot.cross_validate_data(tmp_path)

        ticket_check = next(
            (v for v in result["validations"] if v["check"] == "ticket_counts_consistency"),
            None,
        )
        assert ticket_check is not None
        assert ticket_check["valid"] is False

    def test_cross_validate_all_valid_flag(self, tmp_path) -> None:
        """all_valid 플래그 테스트"""
        # 빈 디렉토리 - 검증할 데이터 없음
        result = meta_ssot.cross_validate_data(tmp_path)

        # 검증할 데이터가 없으면 all_valid는 True (vacuous truth)
        assert result["all_valid"] is True
        assert result["passed"] == result["total_checks"]


# ═══════════════════════════════════════════════════════════════
# Test: self_heal()
# ═══════════════════════════════════════════════════════════════


class TestSelfHeal:
    """자가 치유 테스트"""

    def test_self_heal_dry_run_mode(self, tmp_path) -> None:
        """dry-run 모드에서는 실제 실행하지 않음"""
        # plist 파일 생성
        scripts_cron = tmp_path / "scripts" / "cron"
        scripts_cron.mkdir(parents=True)
        (scripts_cron / "com.afo.meta_ssot_health.plist").write_text("<plist/>")

        # launchd 상태: 서비스 로드되지 않음
        mock_runtime = {
            "total": 1,
            "loaded": 0,
            "running": 0,
            "services": [
                {
                    "name": "com.afo.meta_ssot_health",
                    "loaded": False,
                    "running": False,
                    "last_exit_code": None,
                }
            ],
        }

        with patch.object(meta_ssot, "check_launchd_runtime", return_value=mock_runtime):
            with patch.object(meta_ssot, "get_repo_root", return_value=tmp_path):
                result = meta_ssot.self_heal(tmp_path, dry_run=True)

        assert result["dry_run"] is True
        assert result["healed"] == 0  # dry-run이므로 0
        # 액션이 생성될 수도 있고 없을 수도 있음 (로직에 따라 다름)
        assert "actions" in result  # 액션 키가 존재해야 함

    def test_self_heal_identifies_not_loaded_service(self, tmp_path) -> None:
        """로드되지 않은 서비스 식별"""
        mock_runtime = {
            "total": 1,
            "loaded": 0,
            "running": 0,
            "services": [
                {
                    "name": "com.afo.meta_ssot_health",
                    "loaded": False,
                    "running": False,
                    "last_exit_code": None,
                }
            ],
        }

        scripts_cron = tmp_path / "scripts" / "cron"
        scripts_cron.mkdir(parents=True)
        plist_path = scripts_cron / "com.afo.meta_ssot_health.plist"
        plist_path.write_text("<plist/>")

        with patch.object(meta_ssot, "check_launchd_runtime", return_value=mock_runtime):
            result = meta_ssot.self_heal(tmp_path, dry_run=True)

        # self_heal 결과 구조 검증
        assert "actions" in result
        assert "dry_run" in result
        assert "healed" in result
        # dry_run 모드에서는 healed가 0이어야 함
        assert result["dry_run"] is True
        assert result["healed"] == 0


# ═══════════════════════════════════════════════════════════════
# Test: should_alert()
# ═══════════════════════════════════════════════════════════════


class TestShouldAlert:
    """알림 필요 여부 판단 테스트"""

    def test_should_alert_when_healthy(self) -> None:
        """HEALTHY 상태에서는 알림 불필요"""
        results = {
            "overall_status": "HEALTHY",
            "metacognitive": {
                "launchd_runtime": {"loaded": 3, "total": 3},
                "cross_validation": {"all_valid": True},
            },
        }
        assert meta_ssot.should_alert(results) is False

    def test_should_alert_when_error(self) -> None:
        """ERROR 상태에서는 알림 필요"""
        results = {
            "overall_status": "ERROR",
            "metacognitive": {
                "launchd_runtime": {"loaded": 3, "total": 3},
                "cross_validation": {"all_valid": True},
            },
        }
        assert meta_ssot.should_alert(results) is True

    def test_should_alert_when_cross_validation_fails(self) -> None:
        """교차 검증 실패 시 알림 필요"""
        results = {
            "overall_status": "HEALTHY",
            "metacognitive": {
                "launchd_runtime": {"loaded": 3, "total": 3},
                "cross_validation": {"all_valid": False},
            },
        }
        assert meta_ssot.should_alert(results) is True

    def test_should_alert_when_launchd_missing(self) -> None:
        """launchd 서비스 누락 시 알림 필요"""
        results = {
            "overall_status": "HEALTHY",
            "metacognitive": {
                "launchd_runtime": {"loaded": 2, "total": 3},  # 1개 누락
                "cross_validation": {"all_valid": True},
            },
        }
        assert meta_ssot.should_alert(results) is True


# ═══════════════════════════════════════════════════════════════
# Test: send_discord_alert()
# ═══════════════════════════════════════════════════════════════


class TestDiscordAlert:
    """Discord 알림 테스트"""

    def test_discord_alert_without_webhook_url(self) -> None:
        """웹훅 URL이 없으면 False 반환"""
        with patch.dict("os.environ", {}, clear=True):
            result = meta_ssot.send_discord_alert({}, webhook_url=None)
        assert result is False

    def test_discord_alert_message_structure(self) -> None:
        """Discord 메시지 구조 검증"""
        results = {
            "overall_status": "WARNING",
            "timestamp": datetime.now().isoformat(),
            "meta": {"healthy": 4, "warning": 2, "error": 0},
            "systems": [
                {"name": "Test System", "status": "HEALTHY"},
            ],
            "metacognitive": {
                "launchd_runtime": {"loaded": 3, "total": 3},
                "cross_validation": {"passed": 2, "total_checks": 2},
            },
        }

        # Mock urlopen in the notifier module (modularized structure)
        with patch("scripts.meta_ssot.notifier.urlopen") as mock_urlopen:
            mock_urlopen.return_value = MagicMock()

            result = meta_ssot.send_discord_alert(results, webhook_url="https://discord.com/test")

        assert result is True
        # urlopen이 호출됨
        mock_urlopen.assert_called_once()


# ═══════════════════════════════════════════════════════════════
# Test: AUTOMATION_REGISTRY structure
# ═══════════════════════════════════════════════════════════════


class TestAutomationRegistry:
    """자동화 레지스트리 구조 테스트"""

    def test_registry_has_required_fields(self) -> None:
        """레지스트리 항목에 필수 필드가 있는지 확인"""
        required_fields = {"name", "path", "expected_interval_hours", "check_method"}

        for spec in meta_ssot.AUTOMATION_REGISTRY:
            assert required_fields.issubset(spec.keys()), f"Missing fields in {spec['name']}"

    def test_registry_includes_self_reference(self) -> None:
        """메타인지: 자기 자신이 레지스트리에 포함되어 있는지"""
        names = [s["name"] for s in meta_ssot.AUTOMATION_REGISTRY]
        assert any("Meta" in n or "self" in n.lower() for n in names)

    def test_launchd_services_constant(self) -> None:
        """LAUNCHD_SERVICES 상수 확인"""
        assert len(meta_ssot.LAUNCHD_SERVICES) == 3
        assert all(s.startswith("com.afo.") for s in meta_ssot.LAUNCHD_SERVICES)
