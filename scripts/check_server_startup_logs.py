"""
Check Server Startup Logs
서버 시작 시 라우터 등록 메시지를 확인하는 스크립트
"""

# #region agent log
import json
import sys
from datetime import datetime
from pathlib import Path

LOG_PATH = Path("./.cursor/debug.log")


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
            "sessionId": "check-server-startup",
            "runId": "startup-check",
            "hypothesisId": hypothesis_id,
        }
        with Path(LOG_PATH).open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Logging failed: {e}", file=sys.stderr)


# #endregion agent log


def test_router_imports() -> None:
    """라우터 import 테스트"""
    # #region agent log
    log_debug(
        "check_server_startup_logs.py:test_router_imports",
        "Testing router imports",
        {},
        "A",
    )
    # #endregion agent log

    print("\n🔍 라우터 Import 테스트\n")
    print("=" * 60)

    results = {}

    # 1. Comprehensive Health
    try:
        import sys
        from pathlib import Path

        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root / "packages" / "afo-core"))

        from AFO.api.routes.comprehensive_health import router as comp_router

        # #region agent log
        log_debug(
            "check_server_startup_logs.py:test_router_imports",
            "Comprehensive Health router imported",
            {"prefix": str(comp_router.prefix)},
            "A",
        )
        # #endregion agent log
        print(f"✅ Comprehensive Health: {comp_router.prefix}")
        results["comprehensive_health"] = True
    except Exception as e:
        # #region agent log
        log_debug(
            "check_server_startup_logs.py:test_router_imports",
            "Comprehensive Health router import failed",
            {"error": str(e)},
            "A",
        )
        # #endregion agent log
        print(f"❌ Comprehensive Health: {e}")
        results["comprehensive_health"] = False

    # 2. Intake
    try:
        from afo_soul_engine.routers.intake import router as intake_router

        # #region agent log
        log_debug(
            "check_server_startup_logs.py:test_router_imports",
            "Intake router imported",
            {"prefix": str(intake_router.prefix)},
            "B",
        )
        # #endregion agent log
        print(f"✅ Intake: {intake_router.prefix}")
        results["intake"] = True
    except Exception as e:
        # #region agent log
        log_debug(
            "check_server_startup_logs.py:test_router_imports",
            "Intake router import failed",
            {"error": str(e)},
            "B",
        )
        # #endregion agent log
        print(f"❌ Intake: {e}")
        results["intake"] = False

    # 3. Family
    try:
        from AFO.api.routers.family import router as family_router

        # #region agent log
        log_debug(
            "check_server_startup_logs.py:test_router_imports",
            "Family router imported",
            {"prefix": str(family_router.prefix)},
            "C",
        )
        # #endregion agent log
        print(f"✅ Family: {family_router.prefix}")
        results["family"] = True
    except Exception as e:
        # #region agent log
        log_debug(
            "check_server_startup_logs.py:test_router_imports",
            "Family router import failed",
            {"error": str(e)},
            "C",
        )
        # #endregion agent log
        print(f"❌ Family: {e}")
        results["family"] = False

    print("\n" + "=" * 60)
    return results


def check_api_server_code() -> None:
    """api_server.py에서 라우터 등록 코드 확인"""
    # #region agent log
    log_debug(
        "check_server_startup_logs.py:check_api_server_code",
        "Checking api_server.py for router registration code",
        {},
        "D",
    )
    # #endregion agent log

    print("\n📋 api_server.py 라우터 등록 코드 확인\n")
    print("=" * 60)

    api_server_path = Path(__file__).parent.parent / "packages" / "afo-core" / "api_server.py"

    if not api_server_path.exists():
        print(f"❌ api_server.py를 찾을 수 없습니다: {api_server_path}")
        return

    content = api_server_path.read_text(encoding="utf-8")

    checks = [
        ("Comprehensive Health", "comprehensive_health"),
        ("Intake", "intake_router"),
        ("Family", "family_router"),
    ]

    for name, keyword in checks:
        if keyword in content:
            # 등록 코드가 있는지 확인
            if "app.include_router" in content and keyword in content:
                print(f"✅ {name}: 등록 코드 발견")
            else:
                print(f"⚠️  {name}: 키워드는 있지만 등록 코드 없음")
        else:
            print(f"❌ {name}: 키워드 없음")

    # #region agent log
    log_debug(
        "check_server_startup_logs.py:check_api_server_code",
        "Code check completed",
        {},
        "D",
    )
    # #endregion agent log


def main() -> None:
    print("\n🏰 서버 시작 로그 확인\n")

    # 1. 라우터 import 테스트
    import_results = test_router_imports()

    # 2. api_server.py 코드 확인
    check_api_server_code()

    # 3. 요약
    print("\n" + "=" * 60)
    print("📊 요약")
    print("=" * 60)
    all_ok = all(import_results.values())
    if all_ok:
        print("✅ 모든 라우터 import 성공")
        print("\n💡 서버를 재시작하면 라우터가 등록될 것입니다.")
    else:
        print("❌ 일부 라우터 import 실패")
        print("\n⚠️  서버 시작 시 라우터 등록이 실패할 수 있습니다.")

    # #region agent log
    log_debug(
        "check_server_startup_logs.py:main",
        "Server startup check completed",
        {"import_results": import_results, "all_ok": all_ok},
        "MAIN",
    )
    # #endregion agent log


if __name__ == "__main__":
    main()
