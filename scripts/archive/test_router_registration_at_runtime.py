"""
Test Router Registration at Runtime
실제 서버에서 라우터 등록을 테스트하는 스크립트
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
            "sessionId": "test-router-registration-runtime",
            "runId": "runtime-test",
            "hypothesisId": hypothesis_id,
        }
        with Path(LOG_PATH).open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Logging failed: {e}", file=sys.stderr)


# #endregion agent log


def simulate_router_registration() -> None:
    """api_server.py의 라우터 등록 코드를 시뮬레이션"""
    # #region agent log
    log_debug(
        "test_router_registration_at_runtime.py:simulate_router_registration",
        "Simulating router registration",
        {},
        "A",
    )
    # #endregion agent log

    print("\n🔍 라우터 등록 시뮬레이션\n")
    print("=" * 60)

    # FastAPI app 생성 (실제 등록은 하지 않음)
    from fastapi import FastAPI

    app = FastAPI()

    results = {}

    # 1. Comprehensive Health
    try:
        from AFO.api.routes.comprehensive_health import (
            router as comprehensive_health_router,
        )

        app.include_router(comprehensive_health_router)
        # #region agent log
        log_debug(
            "test_router_registration_at_runtime.py:simulate_router_registration",
            "Comprehensive Health router registered",
            {"prefix": str(comprehensive_health_router.prefix)},
            "A",
        )
        # #endregion agent log
        print(f"✅ Comprehensive Health: 등록 성공 (prefix: {comprehensive_health_router.prefix})")
        results["comprehensive_health"] = True
    except Exception as e:
        # #region agent log
        log_debug(
            "test_router_registration_at_runtime.py:simulate_router_registration",
            "Comprehensive Health router registration failed",
            {"error": str(e)},
            "A",
        )
        # #endregion agent log
        print(f"❌ Comprehensive Health: {e}")
        results["comprehensive_health"] = False

    # 2. Intake
    try:
        from afo_soul_engine.routers.intake import router as intake_router

        app.include_router(intake_router)
        # #region agent log
        log_debug(
            "test_router_registration_at_runtime.py:simulate_router_registration",
            "Intake router registered",
            {"prefix": str(intake_router.prefix)},
            "B",
        )
        # #endregion agent log
        print(f"✅ Intake: 등록 성공 (prefix: {intake_router.prefix})")
        results["intake"] = True
    except Exception as e:
        # #region agent log
        log_debug(
            "test_router_registration_at_runtime.py:simulate_router_registration",
            "Intake router registration failed",
            {"error": str(e)},
            "B",
        )
        # #endregion agent log
        print(f"❌ Intake: {e}")
        results["intake"] = False

    # 3. Family
    try:
        from AFO.api.routers.family import router as family_router

        app.include_router(family_router)
        app.include_router(family_router, prefix="/api")
        # #region agent log
        log_debug(
            "test_router_registration_at_runtime.py:simulate_router_registration",
            "Family router registered",
            {"prefix": str(family_router.prefix)},
            "C",
        )
        # #endregion agent log
        print(f"✅ Family: 등록 성공 (prefix: {family_router.prefix})")
        results["family"] = True
    except Exception as e:
        # #region agent log
        log_debug(
            "test_router_registration_at_runtime.py:simulate_router_registration",
            "Family router registration failed",
            {"error": str(e)},
            "C",
        )
        # #endregion agent log
        print(f"❌ Family: {e}")
        results["family"] = False

    # 등록된 라우트 확인
    print("\n📋 등록된 라우트:")
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            methods = ", ".join(route.methods) if route.methods else "N/A"
            print(f"   {methods:8} {route.path}")

    # #region agent log
    log_debug(
        "test_router_registration_at_runtime.py:simulate_router_registration",
        "Router registration simulation completed",
        {"results": results, "total_routes": len(app.routes)},
        "MAIN",
    )
    # #endregion agent log

    return results, app


def main() -> None:
    print("\n🏰 런타임 라우터 등록 테스트\n")

    results, app = simulate_router_registration()

    print("\n" + "=" * 60)
    print("📊 요약")
    print("=" * 60)
    all_ok = all(results.values())
    if all_ok:
        print("✅ 모든 라우터 등록 성공")
        print(f"   총 라우트 수: {len(app.routes)}")
    else:
        print("❌ 일부 라우터 등록 실패")
        for name, success in results.items():
            status = "✅" if success else "❌"
            print(f"   {status} {name}")


if __name__ == "__main__":
    main()
