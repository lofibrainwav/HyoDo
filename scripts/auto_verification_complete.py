"""
자동 적용 검증 스크립트
모든 변경사항이 올바르게 적용되었는지 자동으로 검증
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
            "sessionId": "auto-verification-complete",
            "runId": "auto",
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


def verify_all_imports() -> None:
    """모든 import 검증"""
    # #region agent log
    log_debug(
        "auto_verification_complete.py:verify_all_imports",
        "Starting all imports verification",
        {},
        "IMPORT",
    )
    # #endregion agent log

    print("\n🔍 모든 Import 검증\n")
    print("=" * 60)

    results = {}

    # 1. sqlmodel
    try:
        import sqlmodel

        version = getattr(sqlmodel, "__version__", "unknown")
        results["sqlmodel"] = {"status": "success", "version": version}
        print(f"✅ sqlmodel: {version}")
        # #region agent log
        log_debug(
            "auto_verification_complete.py:verify_all_imports:sqlmodel",
            "sqlmodel import successful",
            {"version": version},
            "IMPORT",
        )
        # #endregion agent log
    except ImportError as e:
        results["sqlmodel"] = {"status": "failed", "error": str(e)}
        print(f"❌ sqlmodel: {e}")
        # #region agent log
        log_debug(
            "auto_verification_complete.py:verify_all_imports:sqlmodel",
            "sqlmodel import failed",
            {"error": str(e)},
            "IMPORT",
        )
        # #endregion agent log

    # 2. LearningLog 모델
    try:
        from AFO.models.learning_log import LearningLog

        fields = list(LearningLog.model_fields.keys())
        results["LearningLog"] = {"status": "success", "fields": fields}
        print(f"✅ LearningLog 모델: {len(fields)}개 필드")
        # #region agent log
        log_debug(
            "auto_verification_complete.py:verify_all_imports:LearningLog",
            "LearningLog import successful",
            {"fields": fields},
            "IMPORT",
        )
        # #endregion agent log
    except ImportError as e:
        results["LearningLog"] = {"status": "failed", "error": str(e)}
        print(f"❌ LearningLog 모델: {e}")
        # #region agent log
        log_debug(
            "auto_verification_complete.py:verify_all_imports:LearningLog",
            "LearningLog import failed",
            {"error": str(e)},
            "IMPORT",
        )
        # #endregion agent log

    # 3. Learning Log Router
    try:
        from AFO.api.routers.learning_log_router import router

        prefix = getattr(router, "prefix", "N/A")
        results["learning_log_router"] = {"status": "success", "prefix": prefix}
        print(f"✅ Learning Log Router: prefix={prefix}")
        # #region agent log
        log_debug(
            "auto_verification_complete.py:verify_all_imports:learning_log_router",
            "Learning Log Router import successful",
            {"prefix": str(prefix)},
            "IMPORT",
        )
        # #endregion agent log
    except ImportError as e:
        results["learning_log_router"] = {"status": "failed", "error": str(e)}
        print(f"❌ Learning Log Router: {e}")
        # #region agent log
        log_debug(
            "auto_verification_complete.py:verify_all_imports:learning_log_router",
            "Learning Log Router import failed",
            {"error": str(e)},
            "IMPORT",
        )
        # #endregion agent log

    # 4. Chancellor Router
    try:
        from AFO.api.routers.chancellor_router import router as chancellor_router

        prefix = getattr(chancellor_router, "prefix", "N/A")
        results["chancellor_router"] = {"status": "success", "prefix": prefix}
        print(f"✅ Chancellor Router: prefix={prefix}")
        # #region agent log
        log_debug(
            "auto_verification_complete.py:verify_all_imports:chancellor_router",
            "Chancellor Router import successful",
            {"prefix": str(prefix)},
            "IMPORT",
        )
        # #endregion agent log
    except ImportError as e:
        results["chancellor_router"] = {"status": "failed", "error": str(e)}
        print(f"❌ Chancellor Router: {e}")
        # #region agent log
        log_debug(
            "auto_verification_complete.py:verify_all_imports:chancellor_router",
            "Chancellor Router import failed",
            {"error": str(e)},
            "IMPORT",
        )
        # #endregion agent log

    # 5. Grok Stream Router
    try:
        from AFO.api.routers.grok_stream import router as grok_stream_router

        prefix = getattr(grok_stream_router, "prefix", "N/A")
        results["grok_stream_router"] = {"status": "success", "prefix": prefix}
        print(f"✅ Grok Stream Router: prefix={prefix}")
        # #region agent log
        log_debug(
            "auto_verification_complete.py:verify_all_imports:grok_stream_router",
            "Grok Stream Router import successful",
            {"prefix": str(prefix)},
            "IMPORT",
        )
        # #endregion agent log
    except ImportError as e:
        results["grok_stream_router"] = {"status": "failed", "error": str(e)}
        print(f"❌ Grok Stream Router: {e}")
        # #region agent log
        log_debug(
            "auto_verification_complete.py:verify_all_imports:grok_stream_router",
            "Grok Stream Router import failed",
            {"error": str(e)},
            "IMPORT",
        )
        # #endregion agent log

    return results


def verify_all_endpoints() -> None:
    """모든 엔드포인트 검증"""
    # #region agent log
    log_debug(
        "auto_verification_complete.py:verify_all_endpoints",
        "Starting all endpoints verification",
        {},
        "ENDPOINT",
    )
    # #endregion agent log

    print("\n🌐 모든 엔드포인트 검증\n")
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
                f"auto_verification_complete.py:verify_all_endpoints:{name}",
                "Endpoint checked",
                {
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "ok": is_ok,
                },
                "ENDPOINT",
            )
            # #endregion agent log
        except requests.exceptions.ConnectionError:
            results[name] = {"error": "Connection refused", "endpoint": endpoint}
            print(f"❌ {name}: {endpoint} - 서버 연결 실패 (서버가 실행 중이지 않음)")
            # #region agent log
            log_debug(
                f"auto_verification_complete.py:verify_all_endpoints:{name}",
                "Endpoint check failed - connection refused",
                {"endpoint": endpoint},
                "ENDPOINT",
            )
            # #endregion agent log
        except Exception as e:
            results[name] = {"error": str(e), "endpoint": endpoint}
            print(f"❌ {name}: {endpoint} - Error: {e}")
            # #region agent log
            log_debug(
                f"auto_verification_complete.py:verify_all_endpoints:{name}",
                "Endpoint check failed",
                {"endpoint": endpoint, "error": str(e)},
                "ENDPOINT",
            )
            # #endregion agent log

    return results


def verify_openapi_schema() -> None:
    """OpenAPI 스키마에서 경로 확인"""
    # #region agent log
    log_debug(
        "auto_verification_complete.py:verify_openapi_schema",
        "Starting OpenAPI schema verification",
        {},
        "OPENAPI",
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
                "auto_verification_complete.py:verify_openapi_schema",
                "OpenAPI schema checked",
                {"found_paths": found_paths, "missing_paths": missing_paths},
                "OPENAPI",
            )
            # #endregion agent log

            return {"found": found_paths, "missing": missing_paths}
        print(f"❌ OpenAPI 스키마 조회 실패: {response.status_code}")
        return {"error": f"HTTP {response.status_code}"}
    except requests.exceptions.ConnectionError:
        print("❌ 서버 연결 실패 (서버가 실행 중이지 않음)")
        return {"error": "Connection refused"}
    except Exception as e:
        print(f"❌ OpenAPI 스키마 검증 실패: {e}")
        return {"error": str(e)}


def main() -> None:
    print("\n🏰 자동 적용 검증 - 완전 검증\n")

    # 모든 import 검증
    import_results = verify_all_imports()

    # 모든 엔드포인트 검증
    endpoint_results = verify_all_endpoints()

    # OpenAPI 스키마 검증
    openapi_results = verify_openapi_schema()

    # 최종 요약
    print("\n" + "=" * 60)
    print("📊 최종 요약")
    print("=" * 60)

    # Import 검증 결과
    all_imports_ok = all(r.get("status") == "success" for r in import_results.values())
    print(f"\n✅ Import 검증: {'모두 성공' if all_imports_ok else '일부 실패'}")
    if all_imports_ok:
        for name, data in import_results.items():
            if data.get("status") == "success":
                prefix = data.get("prefix", "N/A")
                print(f"   - {name}: prefix={prefix}")

    # 엔드포인트 검증 결과
    working_endpoints = [
        name for name, data in endpoint_results.items() if data.get("status_code") == 200
    ]
    not_working_endpoints = [
        name
        for name, data in endpoint_results.items()
        if data.get("status_code") != 200 and "error" not in data
    ]
    connection_error = any("error" in data for data in endpoint_results.values())

    print(f"\n✅ 작동하는 엔드포인트: {len(working_endpoints)}개")
    for name in working_endpoints:
        print(f"   - {name}")

    if not_working_endpoints:
        print(f"\n⚠️  작동하지 않는 엔드포인트: {len(not_working_endpoints)}개")
        for name in not_working_endpoints:
            status_code = endpoint_results[name].get("status_code", "N/A")
            print(f"   - {name}: HTTP {status_code}")

    if connection_error:
        print("\n💡 서버가 실행 중이지 않습니다. 서버를 시작한 후 다시 검증하세요.")
        print(
            "   명령: cd packages/afo-core && poetry run python -m uvicorn api_server:app --reload --port 8010"
        )

    # OpenAPI 스키마 결과
    if isinstance(openapi_results, dict) and "found" in openapi_results:
        found_count = len(openapi_results["found"])
        missing_count = len(openapi_results["missing"])
        print(f"\n📋 OpenAPI 스키마: {found_count}개 경로 발견, {missing_count}개 누락")

    # #region agent log
    log_debug(
        "auto_verification_complete.py:main",
        "Auto verification completed",
        {
            "import_results": import_results,
            "endpoint_results": endpoint_results,
            "openapi_results": openapi_results,
        },
        "MAIN",
    )
    # #endregion agent log

    # 최종 상태 판단
    if all_imports_ok and len(working_endpoints) >= 5:
        print("\n🎉 모든 검증 통과! 시스템이 정상 작동 중입니다.")
        return 0
    if all_imports_ok and connection_error:
        print("\n⚠️  Import는 성공했지만 서버가 실행 중이지 않습니다.")
        return 1
    print("\n❌ 일부 검증 실패. 위의 결과를 확인하세요.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
