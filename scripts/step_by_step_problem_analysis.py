"""
단계별 문제점 분석 스크립트
차근차근 문제를 파악하고 해결
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
            "sessionId": "step-by-step-analysis",
            "runId": "analysis",
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


def step1_check_server_process() -> None:
    """1단계: 서버 프로세스 확인"""
    # #region agent log
    log_debug(
        "step_by_step_problem_analysis.py:step1_check_server_process",
        "Step 1: Checking server process",
        {},
        "STEP1",
    )
    # #endregion agent log

    print("\n" + "=" * 60)
    print("1단계: 서버 프로세스 확인")
    print("=" * 60)

    import subprocess

    try:
        result = subprocess.run(
            ["ps", "aux"], capture_output=True, text=True, timeout=5, check=False
        )
        processes = [
            line
            for line in result.stdout.split("\n")
            if ("uvicorn" in line or "api_server" in line) and "grep" not in line
        ]

        if processes:
            print(f"✅ 서버 프로세스 발견: {len(processes)}개")
            for proc in processes[:2]:
                pid = proc.split()[1] if len(proc.split()) > 1 else "N/A"
                print(f"   PID: {pid}")
            # #region agent log
            log_debug(
                "step_by_step_problem_analysis.py:step1_check_server_process",
                "Server process found",
                {
                    "count": len(processes),
                    "pids": [p.split()[1] for p in processes[:2] if len(p.split()) > 1],
                },
                "STEP1",
            )
            # #endregion agent log
            return {"status": "running", "processes": len(processes)}
        print("❌ 서버 프로세스 없음")
        # #region agent log
        log_debug(
            "step_by_step_problem_analysis.py:step1_check_server_process",
            "No server process found",
            {},
            "STEP1",
        )
        # #endregion agent log
        return {"status": "not_running"}
    except Exception as e:
        print(f"❌ 확인 실패: {e}")
        return {"status": "error", "error": str(e)}


def step2_check_basic_health() -> None:
    """2단계: 기본 Health 엔드포인트 확인"""
    # #region agent log
    log_debug(
        "step_by_step_problem_analysis.py:step2_check_basic_health",
        "Step 2: Checking basic health endpoint",
        {},
        "STEP2",
    )
    # #endregion agent log

    print("\n" + "=" * 60)
    print("2단계: 기본 Health 엔드포인트 확인")
    print("=" * 60)

    import requests

    try:
        response = requests.get("http://localhost:8010/health", timeout=3)
        if response.status_code == 200:
            print(f"✅ /health - {response.status_code} OK")
            # #region agent log
            log_debug(
                "step_by_step_problem_analysis.py:step2_check_basic_health",
                "Health endpoint OK",
                {"status_code": 200},
                "STEP2",
            )
            # #endregion agent log
            return {"status": "ok", "status_code": 200}
        print(f"⚠️  /health - {response.status_code}")
        return {"status": "unexpected", "status_code": response.status_code}
    except requests.exceptions.ConnectionError:
        print("❌ 서버 연결 실패")
        # #region agent log
        log_debug(
            "step_by_step_problem_analysis.py:step2_check_basic_health",
            "Connection refused",
            {},
            "STEP2",
        )
        # #endregion agent log
        return {"status": "connection_refused"}
    except Exception as e:
        print(f"❌ 오류: {e}")
        return {"status": "error", "error": str(e)}


def step3_check_critical_endpoints() -> None:
    """3단계: 핵심 엔드포인트 확인"""
    # #region agent log
    log_debug(
        "step_by_step_problem_analysis.py:step3_check_critical_endpoints",
        "Step 3: Checking critical endpoints",
        {},
        "STEP3",
    )
    # #endregion agent log

    print("\n" + "=" * 60)
    print("3단계: 핵심 엔드포인트 확인")
    print("=" * 60)

    import requests

    endpoints = [
        ("Chancellor Health", "/chancellor/health"),
        ("Learning Log Latest", "/api/learning/learning-log/latest"),
        ("Grok Stream", "/api/grok/stream"),
    ]

    results = {}
    for name, endpoint in endpoints:
        try:
            timeout = 2 if "stream" in endpoint else 3
            response = requests.get(
                f"http://localhost:8010{endpoint}",
                timeout=timeout,
                stream="stream" in endpoint,
            )
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
                f"step_by_step_problem_analysis.py:step3_check_critical_endpoints:{name}",
                "Endpoint checked",
                {
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "ok": is_ok,
                },
                "STEP3",
            )
            # #endregion agent log
        except requests.exceptions.ConnectionError:
            results[name] = {"error": "Connection refused", "endpoint": endpoint}
            print(f"❌ {name}: {endpoint} - 서버 연결 실패")
        except requests.exceptions.Timeout:
            if "stream" in endpoint:
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


def step4_check_router_registration() -> None:
    """4단계: 라우터 등록 상태 확인"""
    # #region agent log
    log_debug(
        "step_by_step_problem_analysis.py:step4_check_router_registration",
        "Step 4: Checking router registration",
        {},
        "STEP4",
    )
    # #endregion agent log

    print("\n" + "=" * 60)
    print("4단계: 라우터 등록 상태 확인")
    print("=" * 60)

    try:
        from api_server import app

        routes = [r.path for r in app.routes if hasattr(r, "path")]
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
            print(f"  ❌ {path} (누락)")

        # #region agent log
        log_debug(
            "step_by_step_problem_analysis.py:step4_check_router_registration",
            "Router registration checked",
            {"found": found, "missing": missing, "total": len(routes)},
            "STEP4",
        )
        # #endregion agent log

        return {"found": found, "missing": missing, "total": len(routes)}
    except Exception as e:
        print(f"❌ 확인 실패: {e}")
        import traceback

        traceback.print_exc()
        # #region agent log
        log_debug(
            "step_by_step_problem_analysis.py:step4_check_router_registration",
            "Router registration check failed",
            {"error": str(e)},
            "STEP4",
        )
        # #endregion agent log
        return {"error": str(e)}


def step5_check_imports() -> None:
    """5단계: Import 상태 확인"""
    # #region agent log
    log_debug(
        "step_by_step_problem_analysis.py:step5_check_imports",
        "Step 5: Checking imports",
        {},
        "STEP5",
    )
    # #endregion agent log

    print("\n" + "=" * 60)
    print("5단계: Import 상태 확인")
    print("=" * 60)

    results = {}
    checks = [
        ("sqlmodel", "sqlmodel"),
        ("LearningLog", "AFO.models.learning_log"),
        ("learning_log_router", "AFO.api.compat"),
        ("grok_stream_router", "AFO.api.compat"),
        ("chancellor_router", "AFO.api.compat"),
    ]

    for name, module_path in checks:
        try:
            if "." in module_path:
                parts = module_path.split(".")
                module = __import__(module_path, fromlist=[parts[-1]])
                obj = getattr(module, parts[-1] if name == parts[-1] else name, None)
            else:
                module = __import__(module_path)
                obj = getattr(module, name, None)

            if obj is None:
                results[name] = {"status": "not_found"}
                print(f"❌ {name}: 모듈에 없음")
            else:
                prefix = getattr(obj, "prefix", None) if hasattr(obj, "prefix") else None
                results[name] = {"status": "success", "prefix": prefix}
                prefix_str = f" (prefix={prefix})" if prefix else ""
                print(f"✅ {name}{prefix_str}")

            # #region agent log
            log_debug(
                f"step_by_step_problem_analysis.py:step5_check_imports:{name}",
                "Import checked",
                results.get(name, {}),
                "STEP5",
            )
            # #endregion agent log
        except ImportError as e:
            results[name] = {"status": "import_error", "error": str(e)}
            print(f"❌ {name}: ImportError - {e}")
        except Exception as e:
            results[name] = {"status": "error", "error": str(e)}
            print(f"❌ {name}: Error - {e}")

    return results


def step6_check_openapi_schema() -> None:
    """6단계: OpenAPI 스키마 확인"""
    # #region agent log
    log_debug(
        "step_by_step_problem_analysis.py:step6_check_openapi_schema",
        "Step 6: Checking OpenAPI schema",
        {},
        "STEP6",
    )
    # #endregion agent log

    print("\n" + "=" * 60)
    print("6단계: OpenAPI 스키마 확인")
    print("=" * 60)

    import requests

    target_paths = [
        "/chancellor/health",
        "/api/learning/learning-log/latest",
        "/api/grok/stream",
    ]

    try:
        response = requests.get("http://localhost:8010/openapi.json", timeout=5)
        if response.status_code == 200:
            schema = response.json()
            paths = schema.get("paths", {})

            print(f"총 경로 수: {len(paths)}")

            found = []
            missing = []
            for target_path in target_paths:
                if target_path in paths:
                    found.append(target_path)
                    methods = list(paths[target_path].keys())
                    print(f"✅ {target_path} - 등록됨 (Methods: {', '.join(methods)})")
                else:
                    missing.append(target_path)
                    print(f"⚠️  {target_path} - 누락")

            # #region agent log
            log_debug(
                "step_by_step_problem_analysis.py:step6_check_openapi_schema",
                "OpenAPI schema checked",
                {"found": found, "missing": missing, "total": len(paths)},
                "STEP6",
            )
            # #endregion agent log

            return {"found": found, "missing": missing, "total": len(paths)}
        print(f"❌ OpenAPI 스키마 조회 실패: {response.status_code}")
        return {"error": f"HTTP {response.status_code}"}
    except requests.exceptions.ConnectionError:
        print("❌ 서버 연결 실패")
        return {"error": "Connection refused"}
    except Exception as e:
        print(f"❌ 확인 실패: {e}")
        return {"error": str(e)}


def main() -> None:
    print("\n🏰 AFO 왕국 단계별 문제점 분석\n")

    # #region agent log
    log_debug(
        "step_by_step_problem_analysis.py:main",
        "Starting step-by-step problem analysis",
        {},
        "MAIN",
    )
    # #endregion agent log

    # 1단계: 서버 프로세스 확인
    server_status = step1_check_server_process()

    # 2단계: 기본 Health 확인
    health_status = step2_check_basic_health()

    # 3단계: 핵심 엔드포인트 확인
    endpoint_results = step3_check_critical_endpoints()

    # 4단계: 라우터 등록 확인
    router_results = step4_check_router_registration()

    # 5단계: Import 확인
    import_results = step5_check_imports()

    # 6단계: OpenAPI 스키마 확인
    openapi_results = step6_check_openapi_schema()

    # 최종 요약 및 문제점 도출
    print("\n" + "=" * 60)
    print("📊 최종 요약 및 문제점 분석")
    print("=" * 60)

    issues = []

    # 서버 상태 문제
    if server_status.get("status") != "running":
        issues.append(
            {
                "level": "CRITICAL",
                "category": "서버 실행",
                "description": "서버가 실행 중이지 않음",
                "step": 1,
            }
        )

    # Health 엔드포인트 문제
    if health_status.get("status") != "ok":
        issues.append(
            {
                "level": "CRITICAL",
                "category": "기본 엔드포인트",
                "description": f"기본 Health 엔드포인트 접근 실패: {health_status.get('status')}",
                "step": 2,
            }
        )

    # 핵심 엔드포인트 문제
    endpoint_errors = [
        name
        for name, data in endpoint_results.items()
        if "error" in data
        or (data.get("status_code") != 200 and "timeout" not in str(data.get("status_code", "")))
    ]
    if endpoint_errors:
        issues.append(
            {
                "level": "HIGH",
                "category": "핵심 엔드포인트",
                "description": f"{len(endpoint_errors)}개 엔드포인트 문제: {', '.join(endpoint_errors)}",
                "step": 3,
            }
        )

    # 라우터 등록 문제
    if isinstance(router_results, dict) and router_results.get("missing"):
        issues.append(
            {
                "level": "HIGH",
                "category": "라우터 등록",
                "description": f"{len(router_results['missing'])}개 경로가 라우터에 등록되지 않음: {router_results['missing']}",
                "step": 4,
            }
        )

    # Import 문제
    import_errors = [
        name for name, data in import_results.items() if data.get("status") != "success"
    ]
    if import_errors:
        issues.append(
            {
                "level": "MEDIUM",
                "category": "Import",
                "description": f"{len(import_errors)}개 Import 실패: {', '.join(import_errors)}",
                "step": 5,
            }
        )

    # OpenAPI 스키마 문제
    if isinstance(openapi_results, dict) and openapi_results.get("missing"):
        issues.append(
            {
                "level": "MEDIUM",
                "category": "OpenAPI 스키마",
                "description": f"{len(openapi_results['missing'])}개 경로가 스키마에 없음: {openapi_results['missing']}",
                "step": 6,
            }
        )

    # 문제점 출력
    if issues:
        print("\n⚠️  발견된 문제점:\n")
        for issue in issues:
            level_icon = (
                "🔴" if issue["level"] == "CRITICAL" else "🟠" if issue["level"] == "HIGH" else "🟡"
            )
            print(f"{level_icon} [{issue['level']}] {issue['category']} (Step {issue['step']})")
            print(f"   {issue['description']}\n")
    else:
        print("\n✅ 문제점 없음 - 모든 시스템 정상 작동")

    # #region agent log
    log_debug(
        "step_by_step_problem_analysis.py:main",
        "Step-by-step analysis completed",
        {
            "server_status": server_status,
            "health_status": health_status,
            "endpoint_results": endpoint_results,
            "router_results": router_results,
            "import_results": import_results,
            "openapi_results": openapi_results,
            "issues": issues,
        },
        "MAIN",
    )
    # #endregion agent log

    return issues


if __name__ == "__main__":
    issues = main()
    sys.exit(0 if len(issues) == 0 else 1)
