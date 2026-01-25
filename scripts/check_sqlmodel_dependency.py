"""
sqlmodel 의존성 확인 및 설치 검증 스크립트
Sequential Thinking 기반 문제 해결
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# #region agent log
LOG_PATH = Path("/Users/brnestrm/AFO_Kingdom/.cursor/debug.log")


def log_debug(
    location: str, message: str, data: dict | None = None, hypothesis_id: str = "A"
) -> None:
    """Debug logging to NDJSON file"""
    try:
        log_entry = {
            "id": f"log_{int(datetime.now().timestamp() * 1000)}",
            "timestamp": int(datetime.now().timestamp() * 1000),
            "location": location,
            "message": message,
            "data": data or {},
            "sessionId": "sqlmodel-dependency-check",
            "runId": "check",
            "hypothesisId": hypothesis_id,
        }
        with Path(LOG_PATH).open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Logging failed: {e}", file=sys.stderr)


# #endregion agent log

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "packages" / "afo-core"))


def step1_check_sqlmodel_import() -> None:
    """Step 1: sqlmodel import 시도"""
    # #region agent log
    log_debug(
        "check_sqlmodel_dependency.py:step1_check_sqlmodel_import",
        "Step 1: Attempting sqlmodel import",
        {},
        "STEP1",
    )
    # #endregion agent log

    print("\n🔍 Step 1: sqlmodel import 확인\n")
    print("=" * 60)

    try:
        import sqlmodel

        version = getattr(sqlmodel, "__version__", "unknown")
        print(f"✅ sqlmodel import 성공 (버전: {version})")
        # #region agent log
        log_debug(
            "check_sqlmodel_dependency.py:step1_check_sqlmodel_import",
            "sqlmodel import successful",
            {"version": version},
            "STEP1",
        )
        # #endregion agent log
        return True
    except ImportError as e:
        print(f"❌ sqlmodel import 실패: {e}")
        # #region agent log
        log_debug(
            "check_sqlmodel_dependency.py:step1_check_sqlmodel_import",
            "sqlmodel import failed",
            {"error": str(e)},
            "STEP1",
        )
        # #endregion agent log
        return False


def step2_check_learning_log_import() -> None:
    """Step 2: LearningLog 모델 import 시도"""
    # #region agent log
    log_debug(
        "check_sqlmodel_dependency.py:step2_check_learning_log_import",
        "Step 2: Attempting LearningLog import",
        {},
        "STEP2",
    )
    # #endregion agent log

    print("\n🔍 Step 2: LearningLog 모델 import 확인\n")
    print("=" * 60)

    try:
        from AFO.models.learning_log import LearningLog

        print("✅ LearningLog 모델 import 성공")
        print(f"   모델 필드: {list(LearningLog.model_fields.keys())}")
        # #region agent log
        log_debug(
            "check_sqlmodel_dependency.py:step2_check_learning_log_import",
            "LearningLog import successful",
            {"fields": list(LearningLog.model_fields.keys())},
            "STEP2",
        )
        # #endregion agent log
        return True
    except ImportError as e:
        print(f"❌ LearningLog 모델 import 실패: {e}")
        # #region agent log
        log_debug(
            "check_sqlmodel_dependency.py:step2_check_learning_log_import",
            "LearningLog import failed",
            {"error": str(e)},
            "STEP2",
        )
        # #endregion agent log
        return False


def step3_check_learning_log_router_import() -> None:
    """Step 3: Learning Log Router import 시도"""
    # #region agent log
    log_debug(
        "check_sqlmodel_dependency.py:step3_check_learning_log_router_import",
        "Step 3: Attempting Learning Log Router import",
        {},
        "STEP3",
    )
    # #endregion agent log

    print("\n🔍 Step 3: Learning Log Router import 확인\n")
    print("=" * 60)

    try:
        from AFO.api.routers.learning_log_router import router

        prefix = getattr(router, "prefix", "N/A")
        print("✅ Learning Log Router import 성공")
        print(f"   Prefix: {prefix}")
        # #region agent log
        log_debug(
            "check_sqlmodel_dependency.py:step3_check_learning_log_router_import",
            "Learning Log Router import successful",
            {"prefix": str(prefix)},
            "STEP3",
        )
        # #endregion agent log
        return True
    except ImportError as e:
        print(f"❌ Learning Log Router import 실패: {e}")
        # #region agent log
        log_debug(
            "check_sqlmodel_dependency.py:step3_check_learning_log_router_import",
            "Learning Log Router import failed",
            {"error": str(e)},
            "STEP3",
        )
        # #endregion agent log
        return False


def main() -> None:
    print("\n🏰 sqlmodel 의존성 확인 및 검증\n")

    # Step 1: sqlmodel import 확인
    sqlmodel_available = step1_check_sqlmodel_import()

    # Step 2: LearningLog 모델 import 확인
    learning_log_available = step2_check_learning_log_import() if sqlmodel_available else False

    # Step 3: Learning Log Router import 확인
    router_available = step3_check_learning_log_router_import() if learning_log_available else False

    # 최종 요약
    print("\n" + "=" * 60)
    print("📊 최종 요약")
    print("=" * 60)

    print(f"\n✅ sqlmodel: {'사용 가능' if sqlmodel_available else '❌ 설치 필요'}")
    print(f"✅ LearningLog 모델: {'사용 가능' if learning_log_available else '❌ import 실패'}")
    print(f"✅ Learning Log Router: {'사용 가능' if router_available else '❌ import 실패'}")

    if not sqlmodel_available:
        print("\n💡 해결 방법:")
        print("   1. pyproject.toml에 sqlmodel 의존성 추가")
        print("   2. poetry add sqlmodel 실행")
        print("   3. 이 스크립트를 다시 실행하여 검증")

    # #region agent log
    log_debug(
        "check_sqlmodel_dependency.py:main",
        "Dependency check completed",
        {
            "sqlmodel_available": sqlmodel_available,
            "learning_log_available": learning_log_available,
            "router_available": router_available,
        },
        "MAIN",
    )
    # #endregion agent log


if __name__ == "__main__":
    main()
