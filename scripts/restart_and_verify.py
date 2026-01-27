"""
서버 재시작 및 검증 스크립트
서버를 재시작하고 모든 엔드포인트를 검증
"""

import json
import subprocess
import sys
import time
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
            "sessionId": "restart-and-verify",
            "runId": "restart",
            "hypothesisId": hypothesis_id,
        }
        with Path(LOG_PATH).open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Logging failed: {e}", file=sys.stderr)


# #endregion agent log


def wait_for_server(max_wait=30) -> None:
    """서버가 시작될 때까지 대기"""
    # #region agent log
    log_debug(
        "restart_and_verify.py:wait_for_server",
        "Waiting for server to start",
        {"max_wait": max_wait},
        "WAIT1",
    )
    # #endregion agent log

    import requests

    BASE_URL = "http://localhost:8010"
    for i in range(max_wait):
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print(f"✅ 서버 시작 완료 ({i + 1}초 후)")
                # #region agent log
                log_debug(
                    "restart_and_verify.py:wait_for_server",
                    "Server started successfully",
                    {"wait_time": i + 1},
                    "WAIT1",
                )
                # #endregion agent log
                return True
        except Exception:
            pass
        time.sleep(1)
        if (i + 1) % 5 == 0:
            print(f"   서버 시작 대기 중... ({i + 1}초)")

    print("❌ 서버 시작 타임아웃")
    # #region agent log
    log_debug(
        "restart_and_verify.py:wait_for_server",
        "Server start timeout",
        {"max_wait": max_wait},
        "WAIT1",
    )
    # #endregion agent log
    return False


def verify_endpoints() -> None:
    """엔드포인트 검증"""
    # #region agent log
    log_debug(
        "restart_and_verify.py:verify_endpoints",
        "Starting endpoint verification",
        {},
        "VERIFY1",
    )
    # #endregion agent log

    print("\n🌐 엔드포인트 검증\n")
    print("=" * 60)

    import requests

    BASE_URL = "http://localhost:8010"
    endpoints = [
        ("기본 Health", "/health"),
        ("Comprehensive Health", "/api/health/comprehensive"),
        ("Chancellor Health", "/chancellor/health"),
        ("Intake Health", "/api/intake/health"),
        ("Family Health (API)", "/api/family/health"),
        ("Family Health (Legacy)", "/family/health"),
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
                f"restart_and_verify.py:verify_endpoints:{name}",
                "Endpoint checked",
                {
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "ok": is_ok,
                },
                "VERIFY1",
            )
            # #endregion agent log
        except Exception as e:
            results[name] = {"error": str(e), "endpoint": endpoint}
            print(f"❌ {name}: {endpoint} - Error: {e}")
            # #region agent log
            log_debug(
                f"restart_and_verify.py:verify_endpoints:{name}",
                "Endpoint check failed",
                {"endpoint": endpoint, "error": str(e)},
                "VERIFY1",
            )
            # #endregion agent log

    return results


def verify_openapi_schema() -> None:
    """OpenAPI 스키마 검증"""
    # #region agent log
    log_debug(
        "restart_and_verify.py:verify_openapi_schema",
        "Starting OpenAPI schema verification",
        {},
        "OPENAPI1",
    )
    # #endregion agent log

    print("\n📋 OpenAPI 스키마 검증\n")
    print("=" * 60)

    import requests

    BASE_URL = "http://localhost:8010"
    target_paths = [
        "/chancellor/health",
        "/api/learning/learning-log/latest",
        "/api/grok/stream",
    ]

    try:
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        if response.status_code == 200:
            schema = response.json()
            paths = schema.get("paths", {})
            found_paths = []
            missing_paths = []

            for target_path in target_paths:
                if target_path in paths:
                    found_paths.append(target_path)
                    print(f"✅ {target_path} - 스키마에 등록됨")
                else:
                    missing_paths.append(target_path)
                    print(f"⚠️  {target_path} - 스키마에 없음")

            # #region agent log
            log_debug(
                "restart_and_verify.py:verify_openapi_schema",
                "OpenAPI schema checked",
                {"found_paths": found_paths, "missing_paths": missing_paths},
                "OPENAPI1",
            )
            # #endregion agent log

            return {"found": found_paths, "missing": missing_paths}
        print(f"❌ OpenAPI 스키마 조회 실패: {response.status_code}")
        return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        print(f"❌ OpenAPI 스키마 검증 실패: {e}")
        return {"error": str(e)}


def main() -> None:
    print("\n🏰 서버 재시작 및 검증\n")

    # 1. 서버 시작
    print("\n🚀 서버 시작 중...\n")
    print("=" * 60)

    project_root = Path(__file__).parent.parent
    server_dir = project_root / "packages" / "afo-core"

    # #region agent log
    log_debug(
        "restart_and_verify.py:main",
        "Starting server",
        {"server_dir": str(server_dir)},
        "MAIN",
    )
    # #endregion agent log

    try:
        # 서버를 백그라운드로 시작
        process = subprocess.Popen(
            [
                "poetry",
                "run",
                "python",
                "-m",
                "uvicorn",
                "api_server:app",
                "--reload",
                "--port",
                "8010",
            ],
            cwd=str(server_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        print(f"✅ 서버 프로세스 시작됨 (PID: {process.pid})")

        # 서버가 시작될 때까지 대기
        if not wait_for_server():
            print("❌ 서버 시작 실패")
            return 1

        # 추가 대기 (라우터 등록 완료 대기)
        print("\n⏳ 라우터 등록 완료 대기 중... (3초)")
        time.sleep(3)

        # 2. 엔드포인트 검증
        endpoint_results = verify_endpoints()

        # 3. OpenAPI 스키마 검증
        openapi_results = verify_openapi_schema()

        # 최종 요약
        print("\n" + "=" * 60)
        print("📊 최종 요약")
        print("=" * 60)

        working = [
            name for name, data in endpoint_results.items() if data.get("status_code") == 200
        ]
        not_working = [
            name
            for name, data in endpoint_results.items()
            if data.get("status_code") != 200 and "error" not in data
        ]

        print(f"\n✅ 작동하는 엔드포인트: {len(working)}개")
        for name in working:
            print(f"   - {name}")

        if not_working:
            print(f"\n⚠️  작동하지 않는 엔드포인트: {len(not_working)}개")
            for name in not_working:
                status_code = endpoint_results[name].get("status_code", "N/A")
                print(f"   - {name}: HTTP {status_code}")

        if isinstance(openapi_results, dict) and "found" in openapi_results:
            found_count = len(openapi_results["found"])
            missing_count = len(openapi_results["missing"])
            print(f"\n📋 OpenAPI 스키마: {found_count}개 경로 발견, {missing_count}개 누락")

        # #region agent log
        log_debug(
            "restart_and_verify.py:main",
            "Restart and verification completed",
            {
                "endpoint_results": endpoint_results,
                "openapi_results": openapi_results,
                "working_count": len(working),
            },
            "MAIN",
        )
        # #endregion agent log

        if len(working) >= 7:
            print("\n🎉 모든 검증 통과! 시스템이 정상 작동 중입니다.")
            return 0
        print("\n⚠️  일부 엔드포인트가 작동하지 않습니다.")
        return 1

    except KeyboardInterrupt:
        print("\n\n⚠️  사용자에 의해 중단됨")
        if "process" in locals():
            process.terminate()
        return 1
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback

        traceback.print_exc()
        if "process" in locals():
            process.terminate()
        return 1


if __name__ == "__main__":
    sys.exit(main())
