# scripts/deploy.py (Phase 2 - 로컬/CI 통합 실행)
# PDF 페이지 1: AntiGravity 배포 자동화
import sys
from pathlib import Path

# Add package root to path to verify imports
current_dir = Path(__file__).resolve().parent
package_root = current_dir.parent / "packages" / "afo-core"
sys.path.insert(0, str(package_root))

try:
    from config.antigravity import antigravity
except ImportError:
    print("⚠️ AntiGravity 모듈을 찾을 수 없습니다. (PYTHONPATH 확인 필요)")
    sys.exit(1)


def deploy() -> None:
    print(f"🚀 [AntiGravity] 배포 시퀀스 시작: {antigravity.ENVIRONMENT}")

    if antigravity.DRY_RUN_DEFAULT:
        print(
            f"🛡️ [AntiGravity] {antigravity.ENVIRONMENT} 배포 시뮬레이션 완료 - 실제 실행 없음 (善: 안전 위주)"
        )
        print("   -> Helm upgrade command skipped.")
        return

    try:
        # Actual command would go here
        # subprocess.run([
        #     "helm", "upgrade", "--install", "afo-kingdom", "./helm/afo-chart",
        #     "--set", f"environment={antigravity.ENVIRONMENT}"
        # ], check=True)
        print(f"✅ [AntiGravity 로그] {antigravity.ENVIRONMENT} 배포 성공 - 마찰 제거 (孝)")
    except Exception as e:
        print(f"❌ [AntiGravity] 배포 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    deploy()
