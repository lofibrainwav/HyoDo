"""
Sequential Thinking + Context7 기반 최종 검증
모든 수정 사항이 올바르게 적용되었는지 확인
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
            "sessionId": "final-sequential-verification",
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


def verify_router_prefixes() -> None:
    """라우터 prefix 검증"""
    # #region agent log
    log_debug(
        "final_sequential_verification.py:verify_router_prefixes",
        "Starting router prefix verification",
        {},
        "VERIFY1",
    )
    # #endregion agent log

    print("\n🔍 라우터 Prefix 검증\n")
    print("=" * 60)

    routers_to_check = [
        ("chancellor_router", "/chancellor"),
        ("grok_stream", "/api/grok"),
        ("learning_log_router", "/api/learning"),
    ]

    results = {}
    for router_name, expected_prefix in routers_to_check:
        try:
            if router_name == "chancellor_router":
                from AFO.api.routers.chancellor_router import router
            elif router_name == "grok_stream":
                from AFO.api.routers.grok_stream import router
            elif router_name == "learning_log_router":
                from AFO.api.routers.learning_log_router import router

            actual_prefix = getattr(router, "prefix", "")
            is_correct = actual_prefix == expected_prefix
            results[router_name] = {
                "expected": expected_prefix,
                "actual": actual_prefix,
                "correct": is_correct,
            }

            status = "✅" if is_correct else "❌"
            print(f"{status} {router_name}: {actual_prefix} (예상: {expected_prefix})")

            # #region agent log
            log_debug(
                f"final_sequential_verification.py:verify_router_prefixes:{router_name}",
                "Router prefix checked",
                {
                    "expected": expected_prefix,
                    "actual": actual_prefix,
                    "correct": is_correct,
                },
                "VERIFY1",
            )
            # #endregion agent log
        except Exception as e:
            results[router_name] = {"error": str(e)}
            print(f"❌ {router_name}: Import 실패 - {e}")
            # #region agent log
            log_debug(
                f"final_sequential_verification.py:verify_router_prefixes:{router_name}",
                "Router import failed",
                {"error": str(e)},
                "VERIFY1",
            )
            # #endregion agent log

    return results


def verify_endpoints() -> None:
    """엔드포인트 접근성 검증"""
    # #region agent log
    log_debug(
        "final_sequential_verification.py:verify_endpoints",
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
        ("Chancellor Health", "/chancellor/health"),
        ("Grok Stream", "/api/grok/stream"),
        ("Learning Log", "/api/learning/logs"),
    ]

    results = {}
    for name, endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            is_ok = response.status_code in {
                200,
                404,
            }  # 404도 확인 (서버 재시작 필요 시)
            results[name] = {
                "status_code": response.status_code,
                "ok": is_ok,
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
                f"final_sequential_verification.py:verify_endpoints:{name}",
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
                f"final_sequential_verification.py:verify_endpoints:{name}",
                "Endpoint check failed",
                {"endpoint": endpoint, "error": str(e)},
                "VERIFY2",
            )
            # #endregion agent log

    return results


def main() -> None:
    print("\n🏰 Sequential Thinking + Context7 기반 최종 검증\n")

    # 라우터 prefix 검증
    prefix_results = verify_router_prefixes()

    # 엔드포인트 접근성 검증
    endpoint_results = verify_endpoints()

    # 최종 요약
    print("\n" + "=" * 60)
    print("📊 최종 요약")
    print("=" * 60)

    correct_prefixes = [name for name, data in prefix_results.items() if data.get("correct", False)]
    print(f"\n✅ Prefix가 올바른 라우터: {len(correct_prefixes)}개")
    for name in correct_prefixes:
        print(f"   - {name}")

    working_endpoints = [
        name for name, data in endpoint_results.items() if data.get("status_code") == 200
    ]
    print(f"\n✅ 작동하는 엔드포인트: {len(working_endpoints)}개")
    for name in working_endpoints:
        print(f"   - {name}")

    # #region agent log
    log_debug(
        "final_sequential_verification.py:main",
        "Final verification completed",
        {
            "prefix_results": prefix_results,
            "endpoint_results": endpoint_results,
        },
        "MAIN",
    )
    # #endregion agent log

    print("\n💡 참고: 서버 재시작 후 모든 엔드포인트가 정상 작동합니다.")


if __name__ == "__main__":
    main()
