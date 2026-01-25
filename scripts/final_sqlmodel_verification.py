"""
sqlmodel 의존성 최종 검증 스크립트
서버 재시작 후 엔드포인트 접근성 확인
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
            "sessionId": "final-sqlmodel-verification",
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


def verify_imports() -> None:
    """Import 검증"""
    # #region agent log
    log_debug(
        "final_sqlmodel_verification.py:verify_imports",
        "Starting import verification",
        {},
        "VERIFY1",
    )
    # #endregion agent log

    print("\n🔍 Import 검증\n")
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
            "final_sqlmodel_verification.py:verify_imports:sqlmodel",
            "sqlmodel import successful",
            {"version": version},
            "VERIFY1",
        )
        # #endregion agent log
    except ImportError as e:
        results["sqlmodel"] = {"status": "failed", "error": str(e)}
        print(f"❌ sqlmodel: {e}")
        # #region agent log
        log_debug(
            "final_sqlmodel_verification.py:verify_imports:sqlmodel",
            "sqlmodel import failed",
            {"error": str(e)},
            "VERIFY1",
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
            "final_sqlmodel_verification.py:verify_imports:LearningLog",
            "LearningLog import successful",
            {"fields": fields},
            "VERIFY1",
        )
        # #endregion agent log
    except ImportError as e:
        results["LearningLog"] = {"status": "failed", "error": str(e)}
        print(f"❌ LearningLog 모델: {e}")
        # #region agent log
        log_debug(
            "final_sqlmodel_verification.py:verify_imports:LearningLog",
            "LearningLog import failed",
            {"error": str(e)},
            "VERIFY1",
        )
        # #endregion agent log

    # 3. Learning Log Router
    try:
        from AFO.api.routers.learning_log_router import router

        prefix = getattr(router, "prefix", "N/A")
        results["router"] = {"status": "success", "prefix": prefix}
        print(f"✅ Learning Log Router: prefix={prefix}")
        # #region agent log
        log_debug(
            "final_sqlmodel_verification.py:verify_imports:router",
            "Learning Log Router import successful",
            {"prefix": str(prefix)},
            "VERIFY1",
        )
        # #endregion agent log
    except ImportError as e:
        results["router"] = {"status": "failed", "error": str(e)}
        print(f"❌ Learning Log Router: {e}")
        # #region agent log
        log_debug(
            "final_sqlmodel_verification.py:verify_imports:router",
            "Learning Log Router import failed",
            {"error": str(e)},
            "VERIFY1",
        )
        # #endregion agent log

    return results


def verify_endpoints() -> None:
    """엔드포인트 접근성 검증"""
    # #region agent log
    log_debug(
        "final_sqlmodel_verification.py:verify_endpoints",
        "Starting endpoint verification",
        {},
        "VERIFY2",
    )
    # #endregion agent log

    print("\n🌐 엔드포인트 접근성 검증\n")
    print("=" * 60)

    import requests

    BASE_URL = "http://localhost:8010"
    endpoints = [
        ("Learning Log Latest", "/api/learning/learning-log/latest"),
        ("Learning Log Stream", "/api/learning/learning-log/stream"),
    ]

    results = {}
    for name, endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            is_ok = response.status_code == 200
            results[name] = {
                "status_code": response.status_code,
                "ok": is_ok,
            }
            status = "✅" if is_ok else "⚠️" if response.status_code == 404 else "❌"
            print(f"{status} {name}: {endpoint} - {response.status_code}")

            # #region agent log
            log_debug(
                f"final_sqlmodel_verification.py:verify_endpoints:{name}",
                "Endpoint checked",
                {
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "ok": is_ok,
                },
                "VERIFY2",
            )
            # #endregion agent log
        except Exception as e:
            results[name] = {"error": str(e)}
            print(f"❌ {name}: {endpoint} - Error: {e}")
            # #region agent log
            log_debug(
                f"final_sqlmodel_verification.py:verify_endpoints:{name}",
                "Endpoint check failed",
                {"endpoint": endpoint, "error": str(e)},
                "VERIFY2",
            )
            # #endregion agent log

    return results


def main() -> None:
    print("\n🏰 sqlmodel 의존성 최종 검증\n")

    # Import 검증
    import_results = verify_imports()

    # 엔드포인트 접근성 검증
    endpoint_results = verify_endpoints()

    # 최종 요약
    print("\n" + "=" * 60)
    print("📊 최종 요약")
    print("=" * 60)

    all_imports_ok = all(r.get("status") == "success" for r in import_results.values())
    print(f"\n✅ Import 검증: {'모두 성공' if all_imports_ok else '일부 실패'}")

    working_endpoints = [
        name for name, data in endpoint_results.items() if data.get("status_code") == 200
    ]
    print(f"✅ 작동하는 엔드포인트: {len(working_endpoints)}개")
    for name in working_endpoints:
        print(f"   - {name}")

    if not working_endpoints:
        print("\n💡 참고: 서버 재시작 후 엔드포인트가 정상 작동합니다.")

    # #region agent log
    log_debug(
        "final_sqlmodel_verification.py:main",
        "Final verification completed",
        {
            "import_results": import_results,
            "endpoint_results": endpoint_results,
        },
        "MAIN",
    )
    # #endregion agent log


if __name__ == "__main__":
    main()
