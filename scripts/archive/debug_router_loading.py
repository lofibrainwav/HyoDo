"""
라우터 로딩 디버깅 스크립트
compat.py에서 라우터가 제대로 로드되는지 확인
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# #region agent log
LOG_PATH = Path(str(Path(__file__).parent.parent) + "/.cursor/debug.log")


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
            "sessionId": "debug-router-loading",
            "runId": "debug",
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


def test_router_loading() -> None:
    """라우터 로딩 테스트"""
    # #region agent log
    log_debug(
        "debug_router_loading.py:test_router_loading",
        "Starting router loading test",
        {},
        "LOAD1",
    )
    # #endregion agent log

    print("\n🔍 라우터 로딩 테스트\n")
    print("=" * 60)

    routers_to_test = [
        ("learning_log_router", "/api/learning"),
        ("grok_stream_router", "/api/grok"),
        ("chancellor_router", "/chancellor"),
    ]

    results = {}
    for router_name, expected_prefix in routers_to_test:
        try:
            from AFO.api.compat import (
                chancellor_router,
                grok_stream_router,
                learning_log_router,
            )

            if router_name == "learning_log_router":
                router = learning_log_router
            elif router_name == "grok_stream_router":
                router = grok_stream_router
            elif router_name == "chancellor_router":
                router = chancellor_router

            if router is None:
                results[router_name] = {"status": "failed", "error": "Router is None"}
                print(f"❌ {router_name}: None")
                # #region agent log
                log_debug(
                    f"debug_router_loading.py:test_router_loading:{router_name}",
                    "Router is None",
                    {},
                    "LOAD1",
                )
                # #endregion agent log
            else:
                prefix = getattr(router, "prefix", "N/A")
                is_correct = prefix == expected_prefix
                results[router_name] = {
                    "status": "success" if is_correct else "wrong_prefix",
                    "prefix": prefix,
                    "expected": expected_prefix,
                }
                status = "✅" if is_correct else "⚠️"
                print(f"{status} {router_name}: prefix={prefix} (예상: {expected_prefix})")
                # #region agent log
                log_debug(
                    f"debug_router_loading.py:test_router_loading:{router_name}",
                    "Router loaded",
                    {
                        "prefix": str(prefix),
                        "expected": expected_prefix,
                        "correct": is_correct,
                    },
                    "LOAD1",
                )
                # #endregion agent log
        except ImportError as e:
            results[router_name] = {"status": "failed", "error": str(e)}
            print(f"❌ {router_name}: ImportError - {e}")
            # #region agent log
            log_debug(
                f"debug_router_loading.py:test_router_loading:{router_name}",
                "Router import failed",
                {"error": str(e)},
                "LOAD1",
            )
            # #endregion agent log
        except Exception as e:
            results[router_name] = {"status": "failed", "error": str(e)}
            print(f"❌ {router_name}: Error - {e}")
            # #region agent log
            log_debug(
                f"debug_router_loading.py:test_router_loading:{router_name}",
                "Router loading failed",
                {"error": str(e)},
                "LOAD1",
            )
            # #endregion agent log

    return results


def test_router_registration() -> None:
    """라우터 등록 테스트"""
    # #region agent log
    log_debug(
        "debug_router_loading.py:test_router_registration",
        "Starting router registration test",
        {},
        "REG1",
    )
    # #endregion agent log

    print("\n🔍 라우터 등록 테스트\n")
    print("=" * 60)

    from fastapi import FastAPI

    test_app = FastAPI()

    try:
        from AFO.api.routers import setup_routers

        setup_routers(test_app)

        # 등록된 라우트 확인
        routes = [route.path for route in test_app.routes if hasattr(route, "path")]

        target_paths = [
            "/chancellor/health",
            "/api/learning/learning-log/latest",
            "/api/grok/stream",
        ]

        print("\n등록된 경로 확인:")
        found_paths = []
        missing_paths = []
        for target_path in target_paths:
            # 경로가 정확히 일치하거나 포함되는지 확인
            found = any(target_path in route or route == target_path for route in routes)
            if found:
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
                    if any(part in route for part in missing.split("/") if part):
                        print(f"   {route}")
                        break

        # #region agent log
        log_debug(
            "debug_router_loading.py:test_router_registration",
            "Router registration test completed",
            {
                "found_paths": found_paths,
                "missing_paths": missing_paths,
                "total_routes": len(routes),
            },
            "REG1",
        )
        # #endregion agent log

        return {
            "found": found_paths,
            "missing": missing_paths,
            "total_routes": len(routes),
        }
    except Exception as e:
        print(f"❌ 라우터 등록 테스트 실패: {e}")
        import traceback

        traceback.print_exc()
        # #region agent log
        log_debug(
            "debug_router_loading.py:test_router_registration",
            "Router registration test failed",
            {"error": str(e)},
            "REG1",
        )
        # #endregion agent log
        return {"error": str(e)}


def main() -> None:
    print("\n🏰 라우터 로딩 및 등록 디버깅\n")

    # 라우터 로딩 테스트
    loading_results = test_router_loading()

    # 라우터 등록 테스트
    registration_results = test_router_registration()

    # 최종 요약
    print("\n" + "=" * 60)
    print("📊 최종 요약")
    print("=" * 60)

    all_loaded = all(r.get("status") == "success" for r in loading_results.values())
    print(f"\n✅ 라우터 로딩: {'모두 성공' if all_loaded else '일부 실패'}")

    if isinstance(registration_results, dict) and "found" in registration_results:
        found_count = len(registration_results["found"])
        missing_count = len(registration_results["missing"])
        print(f"✅ 라우터 등록: {found_count}개 경로 발견, {missing_count}개 누락")

    # #region agent log
    log_debug(
        "debug_router_loading.py:main",
        "Debugging completed",
        {
            "loading_results": loading_results,
            "registration_results": registration_results,
        },
        "MAIN",
    )
    # #endregion agent log


if __name__ == "__main__":
    main()
