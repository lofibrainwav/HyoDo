"""
Check Registered Routes in FastAPI Application
실제로 등록된 라우트를 확인하는 스크립트
"""

import json
import sys

# #region agent log
from datetime import datetime
from pathlib import Path

import requests

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
            "sessionId": "check-registered-routes",
            "runId": "check",
            "hypothesisId": hypothesis_id,
        }
        with Path(LOG_PATH).open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Logging failed: {e}", file=sys.stderr)


# #endregion agent log

BASE_URL = "http://localhost:8010"


def check_openapi_schema() -> None:
    """OpenAPI 스키마에서 등록된 라우트 확인"""
    # #region agent log
    log_debug(
        "check_registered_routes.py:check_openapi_schema",
        "Fetching OpenAPI schema",
        {"base_url": BASE_URL},
        "A",
    )
    # #endregion agent log

    try:
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        # #region agent log
        log_debug(
            "check_registered_routes.py:check_openapi_schema",
            "OpenAPI schema response received",
            {
                "status_code": response.status_code,
                "response_size": len(response.content),
            },
            "A",
        )
        # #endregion agent log

        if response.status_code == 200:
            schema = response.json()
            paths = schema.get("paths", {})

            # #region agent log
            log_debug(
                "check_registered_routes.py:check_openapi_schema",
                "OpenAPI schema parsed",
                {"total_paths": len(paths)},
                "A",
            )
            # #endregion agent log

            # 찾고 있는 경로들
            target_paths = [
                "/api/health/comprehensive",
                "/api/intake/health",
                "/api/family/health",
            ]

            print("\n🔍 등록된 라우트 확인\n")
            print("=" * 60)

            found_paths = []
            missing_paths = []

            for target_path in target_paths:
                if target_path in paths:
                    found_paths.append(target_path)
                    methods = list(paths[target_path].keys())
                    print(f"✅ {target_path}")
                    print(f"   Methods: {', '.join(methods)}")
                else:
                    missing_paths.append(target_path)
                    print(f"❌ {target_path} - 등록되지 않음")

            # 비슷한 경로 찾기
            print("\n📋 비슷한 경로들:")
            similar_paths = []
            for path in sorted(paths.keys()):
                if any(
                    keyword in path for keyword in ["health", "intake", "family", "comprehensive"]
                ):
                    similar_paths.append(path)
                    print(f"   - {path}")

            # #region agent log
            log_debug(
                "check_registered_routes.py:check_openapi_schema",
                "Route check completed",
                {
                    "found_paths": found_paths,
                    "missing_paths": missing_paths,
                    "similar_paths": similar_paths,
                },
                "A",
            )
            # #endregion agent log

            return found_paths, missing_paths, similar_paths
        # #region agent log
        log_debug(
            "check_registered_routes.py:check_openapi_schema",
            "OpenAPI schema fetch failed",
            {"status_code": response.status_code},
            "A",
        )
        # #endregion agent log
        print(f"❌ OpenAPI 스키마를 가져올 수 없습니다: {response.status_code}")
        return [], target_paths, []
    except Exception as e:
        # #region agent log
        log_debug(
            "check_registered_routes.py:check_openapi_schema",
            "OpenAPI schema check exception",
            {"error": str(e), "type": type(e).__name__},
            "A",
        )
        # #endregion agent log
        print(f"❌ 오류 발생: {e}")
        return [], target_paths, []


def main() -> None:
    print("\n🏰 FastAPI 등록된 라우트 확인\n")

    found, missing, _similar = check_openapi_schema()

    print("\n" + "=" * 60)
    print("📊 요약")
    print("=" * 60)
    print(f"✅ 찾은 경로: {len(found)}개")
    print(f"❌ 누락된 경로: {len(missing)}개")

    if missing:
        print("\n⚠️  다음 경로들이 등록되지 않았습니다:")
        for path in missing:
            print(f"   - {path}")
        print("\n💡 서버를 재시작했는지 확인하세요.")
        print("   서버 시작 로그에서 다음 메시지를 확인하세요:")
        print("   - '✅ Intake API 라우터 등록 완료'")
        print("   - '✅ Family Hub API 라우터 등록 완료'")
        print("   - '✅ Comprehensive Health Check 라우터 등록 완료'")


if __name__ == "__main__":
    main()
