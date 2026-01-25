"""
종합 시스템 점검 스크립트
런타임 증거를 바탕으로 문제점을 체계적으로 파악
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
            "sessionId": "comprehensive-system-check",
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


def check_server_status() -> None:
    """서버 실행 상태 확인"""
    # #region agent log
    log_debug(
        "comprehensive_system_check.py:check_server_status",
        "Starting server status check",
        {},
        "SERVER1",
    )
    # #endregion agent log

    print("\n🔍 1단계: 서버 실행 상태 확인\n")
    print("=" * 60)

    import subprocess

    try:
        result = subprocess.run(
            ["ps", "aux"], capture_output=True, text=True, timeout=5, check=False
        )
        processes = [
            line for line in result.stdout.split("\n") if "uvicorn" in line or "api_server" in line
        ]
        processes = [p for p in processes if "grep" not in p]

        if processes:
            print(f"✅ 서버 프로세스 발견: {len(processes)}개")
            for proc in processes[:3]:
                print(f"   {proc[:80]}")
            # #region agent log
            log_debug(
                "comprehensive_system_check.py:check_server_status",
                "Server processes found",
                {"count": len(processes)},
                "SERVER1",
            )
            # #endregion agent log
            return {"status": "running", "processes": len(processes)}
        print("❌ 서버 프로세스 없음")
        # #region agent log
        log_debug(
            "comprehensive_system_check.py:check_server_status",
            "No server processes found",
            {},
            "SERVER1",
        )
        # #endregion agent log
        return {"status": "not_running", "processes": 0}
    except Exception as e:
        print(f"❌ 서버 상태 확인 실패: {e}")
        return {"status": "error", "error": str(e)}


def check_endpoint_accessibility() -> None:
    """엔드포인트 접근성 확인"""
    # #region agent log
    log_debug(
        "comprehensive_system_check.py:check_endpoint_accessibility",
        "Starting endpoint accessibility check",
        {},
        "ENDPOINT1",
    )
    # #endregion agent log

    print("\n🌐 2단계: 엔드포인트 접근성 확인\n")
    print("=" * 60)

    import requests

    BASE_URL = "http://localhost:8010"
    endpoints = [
        ("기본 Health", "/health", False),
        ("Comprehensive Health", "/api/health/comprehensive", False),
        ("Chancellor Health", "/chancellor/health", False),
        ("Intake Health", "/api/intake/health", False),
        ("Family Health (API)", "/api/family/health", False),
        ("Learning Log Latest", "/api/learning/learning-log/latest", False),
        ("Learning Log Stream", "/api/learning/learning-log/stream", True),
        ("Grok Stream", "/api/grok/stream", True),
    ]

    results = {}
    for name, endpoint, is_streaming in endpoints:
        try:
            timeout = 2 if is_streaming else 5
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=timeout, stream=is_streaming)
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
                f"comprehensive_system_check.py:check_endpoint_accessibility:{name}",
                "Endpoint checked",
                {
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "ok": is_ok,
                },
                "ENDPOINT1",
            )
            # #endregion agent log
        except requests.exceptions.ConnectionError:
            results[name] = {"error": "Connection refused", "endpoint": endpoint}
            print(f"❌ {name}: {endpoint} - 서버 연결 실패")
            # #region agent log
            log_debug(
                f"comprehensive_system_check.py:check_endpoint_accessibility:{name}",
                "Endpoint check failed - connection refused",
                {"endpoint": endpoint},
                "ENDPOINT1",
            )
            # #endregion agent log
        except requests.exceptions.Timeout:
            if is_streaming:
                results[name] = {
                    "status_code": "timeout (expected)",
                    "ok": True,
                    "endpoint": endpoint,
                }
                print(f"✅ {name}: {endpoint} - 타임아웃 (스트리밍, 정상)")
            else:
                results[name] = {"error": "timeout", "endpoint": endpoint}
                print(f"⚠️  {name}: {endpoint} - 타임아웃")
        except Exception as e:
            results[name] = {"error": str(e), "endpoint": endpoint}
            print(f"❌ {name}: {endpoint} - Error: {e}")

    return results


def check_openapi_schema() -> None:
    """OpenAPI 스키마 확인"""
    # #region agent log
    log_debug(
        "comprehensive_system_check.py:check_openapi_schema",
        "Starting OpenAPI schema check",
        {},
        "OPENAPI1",
    )
    # #endregion agent log

    print("\n📋 3단계: OpenAPI 스키마 확인\n")
    print("=" * 60)

    import requests

    BASE_URL = "http://localhost:8010"
    target_paths = [
        "/chancellor/health",
        "/api/learning/learning-log/latest",
        "/api/learning/learning-log/stream",
        "/api/grok/stream",
    ]

    try:
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        if response.status_code == 200:
            schema = response.json()
            paths = schema.get("paths", {})
            found_paths = []
            missing_paths = []

            print(f"총 경로 수: {len(paths)}")

            for target_path in target_paths:
                if target_path in paths:
                    found_paths.append(target_path)
                    methods = list(paths[target_path].keys())
                    print(f"✅ {target_path} - 등록됨 (Methods: {', '.join(methods)})")
                else:
                    missing_paths.append(target_path)
                    print(f"⚠️  {target_path} - 누락")

            # #region agent log
            log_debug(
                "comprehensive_system_check.py:check_openapi_schema",
                "OpenAPI schema checked",
                {
                    "found_paths": found_paths,
                    "missing_paths": missing_paths,
                    "total": len(paths),
                },
                "OPENAPI1",
            )
            # #endregion agent log

            return {
                "found": found_paths,
                "missing": missing_paths,
                "total": len(paths),
            }
        print(f"❌ OpenAPI 스키마 조회 실패: {response.status_code}")
        return {"error": f"HTTP {response.status_code}"}
    except requests.exceptions.ConnectionError:
        print("❌ 서버 연결 실패")
        return {"error": "Connection refused"}
    except Exception as e:
        print(f"❌ OpenAPI 스키마 확인 실패: {e}")
        return {"error": str(e)}


def check_router_registration() -> None:
    """라우터 등록 상태 확인"""
    # #region agent log
    log_debug(
        "comprehensive_system_check.py:check_router_registration",
        "Starting router registration check",
        {},
        "ROUTER1",
    )
    # #endregion agent log

    print("\n🔧 4단계: 라우터 등록 상태 확인\n")
    print("=" * 60)

    try:
        from api_server import app

        routes = [route.path for route in app.routes if hasattr(route, "path")]

        target_paths = [
            "/chancellor/health",
            "/api/learning/learning-log/latest",
            "/api/grok/stream",
        ]

        found = [p for p in target_paths if p in routes]
        missing = [p for p in target_paths if p not in routes]

        print(f"총 등록된 라우트: {len(routes)}개")
        print("\n핵심 경로:")
        for path in found:
            print(f"  ✅ {path}")
        for path in missing:
            print(f"  ❌ {path}")

        # #region agent log
        log_debug(
            "comprehensive_system_check.py:check_router_registration",
            "Router registration checked",
            {"found": found, "missing": missing, "total": len(routes)},
            "ROUTER1",
        )
        # #endregion agent log

        return {"found": found, "missing": missing, "total": len(routes)}
    except Exception as e:
        print(f"❌ 라우터 등록 확인 실패: {e}")
        import traceback

        traceback.print_exc()
        # #region agent log
        log_debug(
            "comprehensive_system_check.py:check_router_registration",
            "Router registration check failed",
            {"error": str(e)},
            "ROUTER1",
        )
        # #endregion agent log
        return {"error": str(e)}


def check_imports() -> None:
    """Import 상태 확인"""
    # #region agent log
    log_debug(
        "comprehensive_system_check.py:check_imports",
        "Starting imports check",
        {},
        "IMPORT1",
    )
    # #endregion agent log

    print("\n📦 5단계: Import 상태 확인\n")
    print("=" * 60)

    results = {}
    routers_to_check = [
        ("learning_log_router", "AFO.api.compat"),
        ("grok_stream_router", "AFO.api.compat"),
        ("chancellor_router", "AFO.api.compat"),
    ]

    for router_name, module_name in routers_to_check:
        try:
            module = __import__(module_name, fromlist=[router_name])
            router = getattr(module, router_name, None)
            if router is None:
                results[router_name] = {"status": "not_found", "module": module_name}
                print(f"❌ {router_name}: 모듈에 없음")
            else:
                prefix = getattr(router, "prefix", "N/A")
                results[router_name] = {
                    "status": "success",
                    "prefix": prefix,
                    "module": module_name,
                }
                print(f"✅ {router_name}: prefix={prefix}")

            # #region agent log
            log_debug(
                f"comprehensive_system_check.py:check_imports:{router_name}",
                "Router import checked",
                results.get(router_name, {}),
                "IMPORT1",
            )
            # #endregion agent log
        except ImportError as e:
            results[router_name] = {"status": "import_error", "error": str(e)}
            print(f"❌ {router_name}: ImportError - {e}")
        except Exception as e:
            results[router_name] = {"status": "error", "error": str(e)}
            print(f"❌ {router_name}: Error - {e}")

    return results


def main() -> None:
    print("\n🏰 AFO 왕국 종합 시스템 점검\n")

    # 1. 서버 상태 확인
    server_status = check_server_status()

    # 2. 엔드포인트 접근성 확인
    endpoint_results = check_endpoint_accessibility()

    # 3. OpenAPI 스키마 확인
    openapi_results = check_openapi_schema()

    # 4. 라우터 등록 상태 확인
    router_results = check_router_registration()

    # 5. Import 상태 확인
    import_results = check_imports()

    # 최종 요약
    print("\n" + "=" * 60)
    print("📊 최종 요약")
    print("=" * 60)

    print(f"\n1. 서버 상태: {server_status.get('status', 'unknown')}")
    if server_status.get("processes", 0) > 0:
        print(f"   - 실행 중인 프로세스: {server_status['processes']}개")

    working = [
        name
        for name, data in endpoint_results.items()
        if data.get("status_code") == 200
        or (data.get("ok") and "timeout" in str(data.get("status_code", "")))
    ]
    not_working = [
        name
        for name, data in endpoint_results.items()
        if data.get("status_code") != 200 and "error" not in data
    ]
    connection_errors = [name for name, data in endpoint_results.items() if "error" in data]

    print("\n2. 엔드포인트 상태:")
    print(f"   - 작동: {len(working)}개")
    print(f"   - 작동 안 함: {len(not_working)}개")
    print(f"   - 연결 실패: {len(connection_errors)}개")

    if isinstance(openapi_results, dict) and "total" in openapi_results:
        found_count = len(openapi_results.get("found", []))
        missing_count = len(openapi_results.get("missing", []))
        print("\n3. OpenAPI 스키마:")
        print(f"   - 총 경로: {openapi_results['total']}개")
        print(f"   - 발견: {found_count}개")
        print(f"   - 누락: {missing_count}개")

    if isinstance(router_results, dict) and "found" in router_results:
        found_count = len(router_results.get("found", []))
        missing_count = len(router_results.get("missing", []))
        print("\n4. 라우터 등록:")
        print(f"   - 총 라우트: {router_results.get('total', 0)}개")
        print(f"   - 발견: {found_count}개")
        print(f"   - 누락: {missing_count}개")

    import_success = sum(1 for r in import_results.values() if r.get("status") == "success")
    print("\n5. Import 상태:")
    print(f"   - 성공: {import_success}/{len(import_results)}개")

    # 문제점 파악
    print("\n" + "=" * 60)
    print("🔍 문제점 분석")
    print("=" * 60)

    issues = []
    if server_status.get("status") != "running":
        issues.append("서버가 실행 중이지 않음")
    if len(connection_errors) > 0:
        issues.append(f"{len(connection_errors)}개 엔드포인트 연결 실패")
    if isinstance(openapi_results, dict) and len(openapi_results.get("missing", [])) > 0:
        issues.append(f"OpenAPI 스키마에 {len(openapi_results['missing'])}개 경로 누락")
    if isinstance(router_results, dict) and len(router_results.get("missing", [])) > 0:
        issues.append(f"라우터 등록에 {len(router_results['missing'])}개 경로 누락")
    if import_success < len(import_results):
        issues.append(f"Import 실패: {len(import_results) - import_success}개")

    if issues:
        print("\n⚠️  발견된 문제점:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    else:
        print("\n✅ 문제점 없음 - 모든 시스템 정상 작동")

    # #region agent log
    log_debug(
        "comprehensive_system_check.py:main",
        "Comprehensive system check completed",
        {
            "server_status": server_status,
            "endpoint_results": endpoint_results,
            "openapi_results": openapi_results,
            "router_results": router_results,
            "import_results": import_results,
            "issues": issues,
        },
        "MAIN",
    )
    # #endregion agent log

    return 0 if len(issues) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
