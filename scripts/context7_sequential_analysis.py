"""
Context7 + Sequential Thinking 기반 종합 문제 분석
Context7 지식 베이스를 활용한 체계적 문제 파악
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
            "sessionId": "context7-sequential-analysis",
            "runId": "context7",
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


def sequential_thinking_analysis() -> None:
    """Sequential Thinking 기반 단계별 분석"""
    # #region agent log
    log_debug(
        "context7_sequential_analysis.py:sequential_thinking_analysis",
        "Starting sequential thinking analysis",
        {},
        "SEQ1",
    )
    # #endregion agent log

    print("\n🔍 Sequential Thinking: 단계별 문제 분석\n")
    print("=" * 60)

    steps = [
        {
            "step": 1,
            "title": "현재 상태 파악",
            "action": "실행 중인 서비스 및 엔드포인트 확인",
        },
        {
            "step": 2,
            "title": "라우터 등록 상태 확인",
            "action": "모든 라우터가 정상 등록되었는지 확인",
        },
        {
            "step": 3,
            "title": "의존성 및 설정 확인",
            "action": "필수 의존성과 설정이 정상인지 확인",
        },
        {
            "step": 4,
            "title": "잠재적 문제점 식별",
            "action": "Context7 지식 베이스를 활용한 문제점 탐색",
        },
    ]

    for step in steps:
        print(f"\nStep {step['step']}: {step['title']}")
        print(f"   작업: {step['action']}")

    return steps


def context7_analysis() -> None:
    """Context7 지식 베이스 기반 분석"""
    # #region agent log
    log_debug(
        "context7_sequential_analysis.py:context7_analysis",
        "Starting Context7 analysis",
        {},
        "CTX1",
    )
    # #endregion agent log

    print("\n📚 Context7: 지식 베이스 기반 분석\n")
    print("=" * 60)

    # Context7 지식 베이스 키 목록 (문서에서 확인)
    knowledge_keys = [
        "AFO_ARCHITECTURE",
        "TRINITY_PHILOSOPHY",
        "SIXXON_BODY",
        "MCP_PROTOCOL",
        "API_ENDPOINTS",
        "SKILLS_REGISTRY",
        "DEPLOYMENT",
        "CONFIGURATION",
        "TROUBLESHOOTING",
        "DOCUMENTATION",
    ]

    print("\n📋 Context7 지식 베이스 키:")
    for key in knowledge_keys:
        print(f"   - {key}")

    # #region agent log
    log_debug(
        "context7_sequential_analysis.py:context7_analysis",
        "Context7 knowledge keys listed",
        {"keys": knowledge_keys},
        "CTX1",
    )
    # #endregion agent log

    return knowledge_keys


def check_system_health() -> None:
    """시스템 건강 상태 확인"""
    # #region agent log
    log_debug(
        "context7_sequential_analysis.py:check_system_health",
        "Checking system health",
        {},
        "HEALTH1",
    )
    # #endregion agent log

    print("\n🏥 시스템 건강 상태 확인\n")
    print("=" * 60)

    import requests

    BASE_URL = "http://localhost:8010"
    health_checks = [
        ("기본 Health", "/health"),
        ("Comprehensive Health", "/api/health/comprehensive"),
        ("Chancellor Health", "/chancellor/health"),
        ("Intake Health", "/api/intake/health"),
        ("Family Health (API)", "/api/family/health"),
    ]

    results = {}
    for name, endpoint in health_checks:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            is_ok = response.status_code == 200
            results[name] = is_ok
            status = "✅" if is_ok else "❌"
            print(f"{status} {name}: {endpoint} - {response.status_code}")
            # #region agent log
            log_debug(
                f"context7_sequential_analysis.py:check_system_health:{name}",
                "Health check result",
                {
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "ok": is_ok,
                },
                "HEALTH1",
            )
            # #endregion agent log
        except Exception as e:
            results[name] = False
            print(f"❌ {name}: {endpoint} - Error: {e}")
            # #region agent log
            log_debug(
                f"context7_sequential_analysis.py:check_system_health:{name}",
                "Health check failed",
                {"endpoint": endpoint, "error": str(e)},
                "HEALTH1",
            )
            # #endregion agent log

    return results


def identify_potential_issues() -> None:
    """잠재적 문제점 식별"""
    # #region agent log
    log_debug(
        "context7_sequential_analysis.py:identify_potential_issues",
        "Identifying potential issues",
        {},
        "ISSUE1",
    )
    # #endregion agent log

    print("\n🔎 잠재적 문제점 식별\n")
    print("=" * 60)

    issues = []

    # 1. 라우터 prefix 일관성 확인
    print("\n1. 라우터 Prefix 일관성 확인")
    router_files = list((project_root / "packages" / "afo-core" / "api" / "routers").glob("*.py"))
    prefix_issues = []
    
    # Known routers that are mounted centrally (false positives)
    CENTRAL_MOUNTED_ROUTERS = {
        "intake", "matrix", "finance_root", "skills", "thoughts", "got", 
        "rag_query", "modal_data", "n8n", "debugging", "trinity", "multi_agent"
    }
    
    for router_file in router_files:
        try:
            content = router_file.read_text(encoding="utf-8")
            if "APIRouter" in content:
                # prefix 확인
                if 'prefix="/api/' in content or 'prefix="/' in content:
                    # prefix가 있는 경우
                    pass
                elif (
                    "APIRouter(" in content
                    and "prefix" not in content.split("APIRouter(")[1].split(")")[0]
                ):
                    # prefix가 없는 경우
                    router_name = router_file.stem
                    if router_name not in {"__init__", "health", "root"} and router_name not in CENTRAL_MOUNTED_ROUTERS:
                        prefix_issues.append(router_name)
        except Exception:
            pass

    if prefix_issues:
        print(f"   ⚠️  Prefix가 없는 라우터: {prefix_issues}")
        issues.append({"type": "missing_prefix", "routers": prefix_issues})
    else:
        print("   ✅ 모든 라우터에 prefix 설정됨")

    # 2. 등록 코드 확인
    print("\n2. 라우터 등록 코드 확인")
    api_server_path = project_root / "packages" / "afo-core" / "api_server.py"
    if api_server_path.exists():
        content = api_server_path.read_text(encoding="utf-8")
        router_registrations = content.count("app.include_router")
        print(f"   ✅ 라우터 등록 코드: {router_registrations}개 발견")

    # 3. Import 에러 가능성 확인
    print("\n3. Import 에러 가능성 확인")
    try:
        from AFO.api.routers.chancellor_router import router as cr

        print(f"   ✅ Chancellor 라우터 import 성공 (prefix: {getattr(cr, 'prefix', 'N/A')})")
    except Exception as e:
        print(f"   ❌ Chancellor 라우터 import 실패: {e}")
        issues.append({"type": "import_error", "router": "chancellor", "error": str(e)})

    # #region agent log
    log_debug(
        "context7_sequential_analysis.py:identify_potential_issues",
        "Potential issues identified",
        {"issues": issues},
        "ISSUE1",
    )
    # #endregion agent log

    return issues


def main() -> None:
    print("\n🏰 Context7 + Sequential Thinking 기반 종합 문제 분석\n")

    # Sequential Thinking 분석
    steps = sequential_thinking_analysis()

    # Context7 분석
    knowledge_keys = context7_analysis()

    # 시스템 건강 상태 확인
    health_results = check_system_health()

    # 잠재적 문제점 식별
    issues = identify_potential_issues()

    # 최종 요약
    print("\n" + "=" * 60)
    print("📊 최종 요약")
    print("=" * 60)

    working = [name for name, ok in health_results.items() if ok]
    not_working = [name for name, ok in health_results.items() if not ok]

    print(f"\n✅ 작동하는 엔드포인트: {len(working)}개")
    for name in working:
        print(f"   - {name}")

    if not_working:
        print(f"\n❌ 작동하지 않는 엔드포인트: {len(not_working)}개")
        for name in not_working:
            print(f"   - {name}")

    if issues:
        print(f"\n⚠️  발견된 문제점: {len(issues)}개")
        for issue in issues:
            print(f"   - {issue['type']}: {issue}")

    # #region agent log
    log_debug(
        "context7_sequential_analysis.py:main",
        "Comprehensive analysis completed",
        {
            "steps": len(steps),
            "knowledge_keys": len(knowledge_keys),
            "health_results": health_results,
            "issues": issues,
        },
        "MAIN",
    )
    # #endregion agent log


if __name__ == "__main__":
    main()
