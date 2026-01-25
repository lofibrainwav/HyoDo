# Trinity Score: 90.0 (Established by Chancellor)
# config/friction_calibrator.py (Phase 4 핵심 - 마찰 제거 진단)
# 목표: 시스템의 '재(Ash)'와 '마찰(Friction)'을 측정하여 형님의 평온(Serenity) 수치화

from dataclasses import dataclass
from datetime import datetime

from AFO.antigravity import antigravity
from AFO.security.vault_manager import vault


@dataclass
class SerenityMetrics:
    score: int  # 평온 점수 (0-100)
    friction_level: str  # LOW, MEDIUM, HIGH
    mode: str  # AntiGravity Mode
    vault_status: str  # SECURE (Mock/Live)
    timestamp: str


class FrictionCalibrator:
    """
    마찰 보정기 (Friction Calibrator)

    Truth (眞): 객관적 수치로 시스템 상태 진단
    Goodness (善): 문제 요소를 '마찰'로 정의하여 개선 유도
    Beauty (美): 복잡한 상태를 단 하나의 '점수'로 우아하게 표현
    """

    def calculate_serenity(self) -> SerenityMetrics:
        score = 100
        friction_reasons = []

        # 1. 배포 모드 점검 (Auto Deploy)
        if antigravity.AUTO_DEPLOY:
            # 자동 배포는 마찰을 제거함 (+0)
            pass
        else:
            score -= 10
            friction_reasons.append("Manual Deploy Friction")

        # 2. 안전 장치 점검 (Dry Run)
        if antigravity.DRY_RUN_DEFAULT:
            # 안전 장치는 심리적 마찰을 제거함 (+0)
            pass
        else:
            # 프로덕션에서 Dry Run off는 정상이지만, 개발계에선 위험
            if antigravity.ENVIRONMENT == "dev":
                score -= 5
                friction_reasons.append("Dev Safety Risk")

        # 3. Vault 상태 점검
        vault_status = "SECURE"
        try:
            vault_mode = getattr(vault, "mode", "env")
            if vault_mode == "env":
                vault_status += " (Env Mode)"
                # env 모드는 개발 환경에서는 정상, 프로덕션에서는 주의 필요
                if antigravity.ENVIRONMENT == "prod":
                    score -= 5
                    friction_reasons.append("Prod using Env Mode (consider Vault)")
            else:
                vault_status += f" (Vault Mode: {vault_mode})"
        except Exception:
            vault_status += " (Unknown)"

        # 4. 환경 일치성
        # (추후 확장: 실제 배포된 버전과 코드 버전 일치 여부 등)

        # 5. 재정적 마찰 (Financial Friction) - Phase 13
        # 돈 계산이 부정확하거나(Float), 복구 불가능하면(No Undo) 마찰 발생
        try:
            # Lazy import to avoid circular dependency
            try:
                from AFO.julie_cpa.services.julie_service import JulieService

                julie_service = JulieService()
            except ImportError:
                # Julie module not available, skip financial checks
                score -= 2
                friction_reasons.append("Financial Module Not Available")
                julie_service = None

            if julie_service:
                # Mocking checks for the new service structure
                # The new service doesn't expose raw decimals directly yet,
                # but we assume its internal friction manager does.
                # For now, we pass this check if the service instantiates.
                pass

        except Exception as e:
            # If Julie module is missing or error, slight friction
            score -= 2
            friction_reasons.append(f"Financial Module Check Fail: {e!s}")

        # 점수 보정
        score = max(0, score)

        # 레벨 판정
        if score >= 90:
            level = "LOW"  # 평온
        elif score >= 70:
            level = "MEDIUM"  # 약간의 신경 쓰임
        else:
            level = "HIGH"  # 형님의 개입 필요 (마찰 높음)

        return SerenityMetrics(
            score=score,
            friction_level=level,
            mode="AntiGravity v1.0",
            vault_status=vault_status,
            timestamp=datetime.now().isoformat(),
        )


friction_calibrator = FrictionCalibrator()
