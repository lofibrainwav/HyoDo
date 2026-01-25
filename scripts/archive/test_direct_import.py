"""
Test Direct Import and Registration
직접 import하고 등록을 테스트하는 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "packages" / "afo-core"))

# #region agent log
import json
from datetime import datetime

LOG_PATH = Path(str(Path(__file__).parent.parent) + "/.cursor/debug.log")


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
            "sessionId": "test-direct-import",
            "runId": "direct-test",
            "hypothesisId": hypothesis_id,
        }
        with Path(LOG_PATH).open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Logging failed: {e}")


# #endregion agent log

print("\n🔍 직접 Import 및 등록 테스트\n")
print("=" * 60)

# 1. Comprehensive Health
# #region agent log
log_debug("test_direct_import.py", "Testing Comprehensive Health import", {}, "A")
# #endregion agent log
try:
    from AFO.api.routes.comprehensive_health import (
        router as comprehensive_health_router,
    )

    # #region agent log
    log_debug(
        "test_direct_import.py",
        "Comprehensive Health router imported",
        {"prefix": str(comprehensive_health_router.prefix)},
        "A",
    )
    # #endregion agent log
    print(f"✅ Comprehensive Health: import 성공 (prefix: {comprehensive_health_router.prefix})")

    # FastAPI app에 등록 테스트
    from fastapi import FastAPI

    test_app = FastAPI()
    test_app.include_router(comprehensive_health_router)
    # #region agent log
    log_debug(
        "test_direct_import.py",
        "Comprehensive Health router registered to test app",
        {"routes_count": len(test_app.routes)},
        "A",
    )
    # #endregion agent log
    print(f"   등록 성공: {len(test_app.routes)}개 라우트")
    for route in test_app.routes:
        if hasattr(route, "path"):
            print(f"     - {route.path}")
except Exception as e:
    # #region agent log
    log_debug(
        "test_direct_import.py",
        "Comprehensive Health import/registration failed",
        {"error": str(e), "type": type(e).__name__},
        "A",
    )
    # #endregion agent log
    print(f"❌ Comprehensive Health: {e}")
    import traceback

    traceback.print_exc()

# 2. Intake
# #region agent log
log_debug("test_direct_import.py", "Testing Intake import", {}, "B")
# #endregion agent log
try:
    from afo_soul_engine.routers.intake import router as intake_router

    # #region agent log
    log_debug(
        "test_direct_import.py",
        "Intake router imported",
        {"prefix": str(intake_router.prefix)},
        "B",
    )
    # #endregion agent log
    print(f"\n✅ Intake: import 성공 (prefix: {intake_router.prefix})")

    # FastAPI app에 등록 테스트
    test_app2 = FastAPI()
    test_app2.include_router(intake_router)
    # #region agent log
    log_debug(
        "test_direct_import.py",
        "Intake router registered to test app",
        {"routes_count": len(test_app2.routes)},
        "B",
    )
    # #endregion agent log
    print(f"   등록 성공: {len(test_app2.routes)}개 라우트")
    for route in test_app2.routes:
        if hasattr(route, "path"):
            print(f"     - {route.path}")
except Exception as e:
    # #region agent log
    log_debug(
        "test_direct_import.py",
        "Intake import/registration failed",
        {"error": str(e), "type": type(e).__name__},
        "B",
    )
    # #endregion agent log
    print(f"\n❌ Intake: {e}")
    import traceback

    traceback.print_exc()

print("\n" + "=" * 60)
