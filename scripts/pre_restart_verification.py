"""
서버 재시작 전 검증 스크립트
현재 상태를 확인하고 재시작 준비
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# #region agent log
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
            "sessionId": "pre-restart-verification",
            "runId": "pre-restart",
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


def verify_code_changes() -> None:
    """코드 변경사항 검증"""
    # #region agent log
    log_debug(
        "pre_restart_verification.py:verify_code_changes",
        "Starting code changes verification",
        {},
        "CODE1",
    )
    # #endregion agent log

    print("\n🔍 코드 변경사항 검증\n")
    print("=" * 60)

    results = {}

    # 1. 라우터 prefix 확인
    try:
        from AFO.api.routers.chancellor_router import router as cr
        from AFO.api.routers.grok_stream import router as gsr
        from AFO.api.routers.learning_log_router import router as llr

        results["chancellor_prefix"] = getattr(cr, "prefix", "")
        results["learning_log_prefix"] = getattr(llr, "prefix", "")
        results["grok_stream_prefix"] = getattr(gsr, "prefix", "")

        print(f"✅ Chancellor Router prefix: {results['chancellor_prefix']}")
        print(f"✅ Learning Log Router prefix: {results['learning_log_prefix']}")
        print(f"✅ Grok Stream Router prefix: {results['grok_stream_prefix']}")

        # #region agent log
        log_debug(
            "pre_restart_verification.py:verify_code_changes",
            "Router prefixes verified",
            results,
            "CODE1",
        )
        # #endregion agent log
    except Exception as e:
        print(f"❌ 라우터 prefix 확인 실패: {e}")
        results["error"] = str(e)
        # #region agent log
        log_debug(
            "pre_restart_verification.py:verify_code_changes",
            "Router prefix verification failed",
            {"error": str(e)},
            "CODE1",
        )
        # #endregion agent log

    # 2. compat.py에서 라우터 로딩 확인
    try:
        from AFO.api.compat import (
            chancellor_router,
            grok_stream_router,
            learning_log_router,
        )

        results["compat_loading"] = {
            "learning_log": learning_log_router is not None,
            "grok_stream": grok_stream_router is not None,
            "chancellor": chancellor_router is not None,
        }

        print("\n✅ compat.py 라우터 로딩:")
        print(
            f"   - learning_log_router: {'✅' if results['compat_loading']['learning_log'] else '❌'}"
        )
        print(
            f"   - grok_stream_router: {'✅' if results['compat_loading']['grok_stream'] else '❌'}"
        )
        print(
            f"   - chancellor_router: {'✅' if results['compat_loading']['chancellor'] else '❌'}"
        )

        # #region agent log
        log_debug(
            "pre_restart_verification.py:verify_code_changes",
            "Compat router loading verified",
            results["compat_loading"],
            "CODE1",
        )
        # #endregion agent log
    except Exception as e:
        print(f"❌ compat.py 라우터 로딩 확인 실패: {e}")
        results["compat_error"] = str(e)

    # 3. 앱 라우트 확인
    try:
        from api_server import app

        routes = [r.path for r in app.routes if hasattr(r, "path")]
        target_paths = [
            "/chancellor/health",
            "/api/learning/learning-log/latest",
            "/api/grok/stream",
        ]

        found = [p for p in target_paths if p in routes]
        results["app_routes"] = {"found": found, "total": len(routes)}

        print(f"\n✅ 앱 라우트: {len(found)}/{len(target_paths)}개 발견 (총 {len(routes)}개)")
        for path in found:
            print(f"   - {path}")

        # #region agent log
        log_debug(
            "pre_restart_verification.py:verify_code_changes",
            "App routes verified",
            results["app_routes"],
            "CODE1",
        )
        # #endregion agent log
    except Exception as e:
        print(f"❌ 앱 라우트 확인 실패: {e}")
        results["app_routes_error"] = str(e)

    return results


def verify_current_endpoints() -> None:
    """현재 엔드포인트 상태 확인"""
    # #region agent log
    log_debug(
        "pre_restart_verification.py:verify_current_endpoints",
        "Starting current endpoints verification",
        {},
        "EP1",
    )
    # #endregion agent log

    print("\n🌐 현재 엔드포인트 상태 확인\n")
    print("=" * 60)

    import requests

    BASE_URL = "http://localhost:8010"
    endpoints = [
        ("Chancellor Health", "/chancellor/health"),
        ("Learning Log Latest", "/api/learning/learning-log/latest"),
        ("Grok Stream", "/api/grok/stream"),
    ]

    results = {}
    for name, endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=3)
            results[name] = {
                "status_code": response.status_code,
                "endpoint": endpoint,
            }
            status = (
                "✅"
                if response.status_code == 200
                else "⚠️"
                if response.status_code == 404
                else "❌"
            )
            print(f"{status} {name}: {endpoint} - {response.status_code}")

            # #region agent log
            log_debug(
                f"pre_restart_verification.py:verify_current_endpoints:{name}",
                "Endpoint checked",
                {"endpoint": endpoint, "status_code": response.status_code},
                "EP1",
            )
            # #endregion agent log
        except requests.exceptions.ConnectionError:
            results[name] = {"error": "Connection refused", "endpoint": endpoint}
            print(f"❌ {name}: {endpoint} - 서버 연결 실패 (서버가 실행 중이지 않음)")
            # #region agent log
            log_debug(
                f"pre_restart_verification.py:verify_current_endpoints:{name}",
                "Endpoint check failed - connection refused",
                {"endpoint": endpoint},
                "EP1",
            )
            # #endregion agent log
        except Exception as e:
            results[name] = {"error": str(e), "endpoint": endpoint}
            print(f"❌ {name}: {endpoint} - Error: {e}")

    return results


def main() -> None:
    print("\n🏰 서버 재시작 전 검증\n")

    # 코드 변경사항 검증
    code_results = verify_code_changes()

    # 현재 엔드포인트 상태 확인
    endpoint_results = verify_current_endpoints()

    # 최종 요약
    print("\n" + "=" * 60)
    print("📊 최종 요약")
    print("=" * 60)

    print("\n✅ 코드 변경사항:")
    if "app_routes" in code_results:
        found_count = len(code_results["app_routes"].get("found", []))
        print(f"   - 앱에 등록된 라우트: {found_count}/3개")

    working = [name for name, data in endpoint_results.items() if data.get("status_code") == 200]
    print(f"\n✅ 현재 작동하는 엔드포인트: {len(working)}개")
    if working:
        for name in working:
            print(f"   - {name}")

    not_working = [
        name
        for name, data in endpoint_results.items()
        if data.get("status_code") != 200 and "error" not in data
    ]
    if not_working:
        print(f"\n⚠️  현재 작동하지 않는 엔드포인트: {len(not_working)}개")
        for name in not_working:
            print(f"   - {name}")

    print("\n💡 다음 단계: 서버 재시작 후 다시 검증하세요.")

    # #region agent log
    log_debug(
        "pre_restart_verification.py:main",
        "Pre-restart verification completed",
        {"code_results": code_results, "endpoint_results": endpoint_results},
        "MAIN",
    )
    # #endregion agent log


if __name__ == "__main__":
    main()
