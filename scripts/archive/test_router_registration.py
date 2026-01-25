"""
Router Registration Test Script
라우터 등록 상태를 확인하는 스크립트
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
            "sessionId": "router-registration-test",
            "runId": "test",
            "hypothesisId": hypothesis_id,
        }
        with Path(LOG_PATH).open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Logging failed: {e}", file=sys.stderr)


# #endregion agent log


def test_comprehensive_health_import() -> None:
    """Comprehensive Health 라우터 import 테스트"""
    # #region agent log
    log_debug(
        "test_router_registration.py:test_comprehensive_health_import",
        "Testing comprehensive health router import",
        {},
        "A",
    )
    # #endregion agent log

    try:
        from AFO.api.routes.comprehensive_health import (
            router as comprehensive_health_router,
        )

        # #region agent log
        log_debug(
            "test_router_registration.py:test_comprehensive_health_import",
            "Comprehensive health router imported successfully",
            {
                "router_prefix": (
                    str(comprehensive_health_router.prefix)
                    if hasattr(comprehensive_health_router, "prefix")
                    else "N/A"
                )
            },
            "A",
        )
        # #endregion agent log
        print("✅ Comprehensive Health 라우터 import 성공")
        print(f"   Prefix: {comprehensive_health_router.prefix}")
        return True, comprehensive_health_router
    except ImportError as e:
        # #region agent log
        log_debug(
            "test_router_registration.py:test_comprehensive_health_import",
            "Comprehensive health router import failed",
            {"error": str(e), "type": type(e).__name__},
            "A",
        )
        # #endregion agent log
        print(f"❌ Comprehensive Health 라우터 import 실패: {e}")
        try:
            from api.routes.comprehensive_health import (
                router as comprehensive_health_router,
            )

            print("✅ Comprehensive Health 라우터 import 성공 (fallback)")
            return True, comprehensive_health_router
        except Exception as e2:
            print(f"❌ Comprehensive Health 라우터 import 실패 (fallback): {e2}")
            return False, None
    except Exception as e:
        # #region agent log
        log_debug(
            "test_router_registration.py:test_comprehensive_health_import",
            "Comprehensive health router import exception",
            {"error": str(e), "type": type(e).__name__},
            "A",
        )
        # #endregion agent log
        print(f"❌ Comprehensive Health 라우터 import 예외: {e}")
        return False, None


def test_intake_import() -> None:
    """Intake 라우터 import 테스트"""
    # #region agent log
    log_debug(
        "test_router_registration.py:test_intake_import",
        "Testing intake router import",
        {},
        "B",
    )
    # #endregion agent log

    try:
        from AFO.afo_soul_engine.routers.intake import router as intake_router

        # #region agent log
        log_debug(
            "test_router_registration.py:test_intake_import",
            "Intake router imported successfully",
            {
                "router_prefix": (
                    str(intake_router.prefix) if hasattr(intake_router, "prefix") else "N/A"
                )
            },
            "B",
        )
        # #endregion agent log
        print("✅ Intake 라우터 import 성공")
        print(f"   Prefix: {intake_router.prefix}")
        return True, intake_router
    except ImportError as e:
        # #region agent log
        log_debug(
            "test_router_registration.py:test_intake_import",
            "Intake router import failed",
            {"error": str(e), "type": type(e).__name__},
            "B",
        )
        # #endregion agent log
        print(f"❌ Intake 라우터 import 실패: {e}")
        try:
            from afo_soul_engine.routers.intake import router as intake_router

            print("✅ Intake 라우터 import 성공 (fallback)")
            return True, intake_router
        except Exception as e2:
            print(f"❌ Intake 라우터 import 실패 (fallback): {e2}")
            return False, None
    except Exception as e:
        # #region agent log
        log_debug(
            "test_router_registration.py:test_intake_import",
            "Intake router import exception",
            {"error": str(e), "type": type(e).__name__},
            "B",
        )
        # #endregion agent log
        print(f"❌ Intake 라우터 import 예외: {e}")
        return False, None


def test_family_import() -> None:
    """Family 라우터 import 테스트"""
    # #region agent log
    log_debug(
        "test_router_registration.py:test_family_import",
        "Testing family router import",
        {},
        "C",
    )
    # #endregion agent log

    try:
        from AFO.api.routers.family import router as family_router

        # #region agent log
        log_debug(
            "test_router_registration.py:test_family_import",
            "Family router imported successfully",
            {
                "router_prefix": (
                    str(family_router.prefix) if hasattr(family_router, "prefix") else "N/A"
                )
            },
            "C",
        )
        # #endregion agent log
        print("✅ Family 라우터 import 성공")
        print(f"   Prefix: {family_router.prefix}")
        return True, family_router
    except ImportError as e:
        # #region agent log
        log_debug(
            "test_router_registration.py:test_family_import",
            "Family router import failed",
            {"error": str(e), "type": type(e).__name__},
            "C",
        )
        # #endregion agent log
        print(f"❌ Family 라우터 import 실패: {e}")
        try:
            from api.routers.family import router as family_router

            print("✅ Family 라우터 import 성공 (fallback)")
            return True, family_router
        except Exception as e2:
            print(f"❌ Family 라우터 import 실패 (fallback): {e2}")
            return False, None
    except Exception as e:
        # #region agent log
        log_debug(
            "test_router_registration.py:test_family_import",
            "Family router import exception",
            {"error": str(e), "type": type(e).__name__},
            "C",
        )
        # #endregion agent log
        print(f"❌ Family 라우터 import 예외: {e}")
        return False, None


def main() -> None:
    print("\n🔍 라우터 등록 상태 테스트\n")
    print("=" * 60)

    results = {}

    # Comprehensive Health 라우터 테스트
    print("\n1. Comprehensive Health 라우터")
    success, router = test_comprehensive_health_import()
    results["comprehensive_health"] = success

    # Intake 라우터 테스트
    print("\n2. Intake 라우터")
    success, router = test_intake_import()
    results["intake"] = success

    # Family 라우터 테스트
    print("\n3. Family 라우터")
    success, _router = test_family_import()
    results["family"] = success

    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    for name, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{name}: {status}")

    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 모든 라우터 import 성공!")
    else:
        print("\n⚠️  일부 라우터 import 실패 - 서버 시작 시 등록되지 않을 수 있습니다.")

    # #region agent log
    log_debug(
        "test_router_registration.py:main",
        "Router registration test completed",
        {"results": results, "all_passed": all_passed},
        "MAIN",
    )
    # #endregion agent log


if __name__ == "__main__":
    main()
