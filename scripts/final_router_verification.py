"""
최종 라우터 검증 스크립트
서버 재시작 후 모든 라우터가 올바르게 등록되었는지 확인
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
            "sessionId": "final-router-verification",
            "runId": "final",
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


def verify_app_routes() -> None:
    """앱에 등록된 라우트 확인"""
    # #region agent log
    log_debug(
        "final_router_verification.py:verify_app_routes",
        "Starting app routes verification",
        {},
        "APP1",
    )
    # #endregion agent log

    print("\n🔍 앱에 등록된 라우트 확인\n")
    print("=" * 60)

    try:
        from api_server import app

        routes = [route.path for route in app.routes if hasattr(route, "path")]

        target_paths = [
            "/chancellor/health",
            "/api/learning/learning-log/latest",
            "/api/grok/stream",
        ]

        print(f"총 등록된 라우트: {len(routes)}개\n")

        found_paths = []
        missing_paths = []
        for target_path in target_paths:
            if target_path in routes:
                found_paths.append(target_path)
                print(f"✅ {target_path}")
            else:
                missing_paths.append(target_path)
                print(f"❌ {target_path}")

        # 비슷한 경로 찾기
        if missing_paths:
            print("\n비슷한 경로:")
            for route in sorted(routes):
                for missing in missing_paths:
                    if any(
                        part in route
                        for part in missing.split("/")
                        if part and part not in {"api", "chancellor", "learning", "grok"}
                    ):
                        print(f"   {route}")
                        break

        # #region agent log
        log_debug(
            "final_router_verification.py:verify_app_routes",
            "App routes verification completed",
            {
                "found_paths": found_paths,
                "missing_paths": missing_paths,
                "total_routes": len(routes),
            },
            "APP1",
        )
        # #endregion agent log

        return {"found": found_paths, "missing": missing_paths, "total": len(routes)}
    except Exception as e:
        print(f"❌ 앱 라우트 확인 실패: {e}")
        import traceback

        traceback.print_exc()
        # #region agent log
        log_debug(
            "final_router_verification.py:verify_app_routes",
            "App routes verification failed",
            {"error": str(e)},
            "APP1",
        )
        # #endregion agent log
        return {"error": str(e)}


def verify_endpoints() -> None:
    """엔드포인트 접근성 검증"""
    # #region agent log
    log_debug(
        "final_router_verification.py:verify_endpoints",
        "Starting endpoint verification",
        {},
        "EP1",
    )
    # #endregion agent log

    print("\n🌐 엔드포인트 접근성 검증\n")
    print("=" * 60)

    import requests

    BASE_URL = "http://localhost:8010"
    endpoints = [
        ("Chancellor Health", "/chancellor/health"),
        ("Learning Log Latest", "/api/learning/learning-log/latest"),
        ("Learning Log Stream", "/api/learning/learning-log/stream"),
        ("Grok Stream", "/api/grok/stream"),
    ]

    results = {}
    for name, endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            is_ok = response.status_code == 200
            results[name] = {
                "status_code": response.status_code,
                "ok": is_ok,
                "endpoint": endpoint,
            }
            status = "✅" if is_ok else "⚠️" if response.status_code == 404 else "❌"
            print(f"{status} {name}: {endpoint} - {response.status_code}")

            # #region agent log
            log_debug(
                f"final_router_verification.py:verify_endpoints:{name}",
                "Endpoint checked",
                {
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "ok": is_ok,
                },
                "EP1",
            )
            # #endregion agent log
        except requests.exceptions.ConnectionError:
            results[name] = {"error": "Connection refused", "endpoint": endpoint}
            print(f"❌ {name}: {endpoint} - 서버 연결 실패")
            # #region agent log
            log_debug(
                f"final_router_verification.py:verify_endpoints:{name}",
                "Endpoint check failed - connection refused",
                {"endpoint": endpoint},
                "EP1",
            )
            # #endregion agent log
        except Exception as e:
            results[name] = {"error": str(e), "endpoint": endpoint}
            print(f"❌ {name}: {endpoint} - Error: {e}")
            # #region agent log
            log_debug(
                f"final_router_verification.py:verify_endpoints:{name}",
                "Endpoint check failed",
                {"endpoint": endpoint, "error": str(e)},
                "EP1",
            )
            # #endregion agent log

    return results


def main() -> None:
    print("\n🏰 최종 라우터 검증\n")

    # 앱 라우트 확인
    app_results = verify_app_routes()

    # 엔드포인트 접근성 검증
    endpoint_results = verify_endpoints()

    # 최종 요약
    print("\n" + "=" * 60)
    print("📊 최종 요약")
    print("=" * 60)

    if isinstance(app_results, dict) and "found" in app_results:
        found_count = len(app_results["found"])
        missing_count = len(app_results["missing"])
        print(f"\n✅ 앱 라우트: {found_count}개 발견, {missing_count}개 누락")
        if app_results["found"]:
            print("   발견된 경로:")
            for path in app_results["found"]:
                print(f"     - {path}")
        if app_results["missing"]:
            print("   누락된 경로:")
            for path in app_results["missing"]:
                print(f"     - {path}")

    working_endpoints = [
        name for name, data in endpoint_results.items() if data.get("status_code") == 200
    ]
    print(f"\n✅ 작동하는 엔드포인트: {len(working_endpoints)}개")
    for name in working_endpoints:
        print(f"   - {name}")

    not_working = [
        name
        for name, data in endpoint_results.items()
        if data.get("status_code") != 200 and "error" not in data
    ]
    if not_working:
        print(f"\n⚠️  작동하지 않는 엔드포인트: {len(not_working)}개")
        for name in not_working:
            status_code = endpoint_results[name].get("status_code", "N/A")
            print(f"   - {name}: HTTP {status_code}")

    # #region agent log
    log_debug(
        "final_router_verification.py:main",
        "Final verification completed",
        {"app_results": app_results, "endpoint_results": endpoint_results},
        "MAIN",
    )
    # #endregion agent log

    if len(working_endpoints) >= 4:
        print("\n🎉 모든 검증 통과! 시스템이 정상 작동 중입니다.")
        return 0
    print("\n⚠️  일부 엔드포인트가 작동하지 않습니다. 서버를 재시작했는지 확인하세요.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
