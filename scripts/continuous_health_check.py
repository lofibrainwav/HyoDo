"""
Continuous Health Check Script with Runtime Logging
眞 (Truth): 실제 런타임 상태 검증
善 (Goodness): 안정적인 모니터링
美 (Beauty): 명확한 상태 보고
孝 (Serenity): 지속적 평온 수호
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

# #region agent log
LOG_PATH = Path("./.cursor/debug.log")
# #endregion agent log

BASE_URL = "http://localhost:8010"

COLORS = {
    "GREEN": "\033[92m",
    "RED": "\033[91m",
    "YELLOW": "\033[93m",
    "BLUE": "\033[94m",
    "RESET": "\033[0m",
    "BOLD": "\033[1m",
}


def log_debug(
    location: str,
    message: str,
    data: dict[str, Any] | None = None,
    hypothesis_id: str = "A",
    run_id: str = "continuous_check",
) -> None:
    """Debug logging to NDJSON file"""
    # #region agent log
    try:
        log_entry = {
            "id": f"log_{int(datetime.now().timestamp() * 1000)}",
            "timestamp": int(datetime.now().timestamp() * 1000),
            "location": location,
            "message": message,
            "data": data or {},
            "sessionId": "continuous-health-check",
            "runId": run_id,
            "hypothesisId": hypothesis_id,
        }
        with Path(LOG_PATH).open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Logging failed: {e}", file=sys.stderr)
    # #endregion agent log


def check_api_server() -> tuple[bool, dict[str, Any]]:
    """API 서버 기본 연결 확인"""
    # #region agent log
    log_debug(
        "continuous_health_check.py:check_api_server",
        "Starting API server check",
        {"base_url": BASE_URL},
        "A",
    )
    # #endregion agent log

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        # #region agent log
        log_debug(
            "continuous_health_check.py:check_api_server",
            "API server response received",
            {
                "status_code": response.status_code,
                "response_size": len(response.content),
            },
            "A",
        )
        # #endregion agent log

        if response.status_code == 200:
            data = response.json()
            # #region agent log
            log_debug(
                "continuous_health_check.py:check_api_server",
                "API server healthy",
                {"response_data": data},
                "A",
            )
            # #endregion agent log
            return True, data
        # #region agent log
        log_debug(
            "continuous_health_check.py:check_api_server",
            "API server unhealthy",
            {"status_code": response.status_code, "response": response.text[:200]},
            "A",
        )
        # #endregion agent log
        return False, {"error": f"Status {response.status_code}"}
    except requests.exceptions.ConnectionError as e:
        # #region agent log
        log_debug(
            "continuous_health_check.py:check_api_server",
            "API server connection failed",
            {"error": str(e)},
            "A",
        )
        # #endregion agent log
        return False, {"error": f"Connection failed: {e}"}
    except Exception as e:
        # #region agent log
        log_debug(
            "continuous_health_check.py:check_api_server",
            "API server check exception",
            {"error": str(e), "type": type(e).__name__},
            "A",
        )
        # #endregion agent log
        return False, {"error": str(e)}


def check_comprehensive_health() -> tuple[bool, dict[str, Any]]:
    """종합 건강 상태 확인"""
    # #region agent log
    log_debug(
        "continuous_health_check.py:check_comprehensive_health",
        "Starting comprehensive health check",
        {"endpoint": f"{BASE_URL}/api/health/comprehensive"},
        "B",
    )
    # #endregion agent log

    try:
        response = requests.get(f"{BASE_URL}/api/health/comprehensive", timeout=30)
        # #region agent log
        log_debug(
            "continuous_health_check.py:check_comprehensive_health",
            "Comprehensive health response received",
            {
                "status_code": response.status_code,
                "response_size": len(response.content),
            },
            "B",
        )
        # #endregion agent log

        if response.status_code == 200:
            data = response.json()
            # #region agent log
            log_debug(
                "continuous_health_check.py:check_comprehensive_health",
                "Comprehensive health data parsed",
                {
                    "status": data.get("status"),
                    "trinity_score": data.get("trinity_score"),
                    "skills_count": len(data.get("skills", {}).get("skills", [])),
                    "scholars_count": data.get("scholars", {}).get("total_scholars", 0),
                    "mcp_tools_count": data.get("mcp_tools", {}).get("total_servers", 0),
                },
                "B",
            )
            # #endregion agent log
            return True, data
        # #region agent log
        log_debug(
            "continuous_health_check.py:check_comprehensive_health",
            "Comprehensive health check failed",
            {"status_code": response.status_code, "response": response.text[:200]},
            "B",
        )
        # #endregion agent log
        return False, {"error": f"Status {response.status_code}"}
    except Exception as e:
        # #region agent log
        log_debug(
            "continuous_health_check.py:check_comprehensive_health",
            "Comprehensive health check exception",
            {"error": str(e), "type": type(e).__name__},
            "B",
        )
        # #endregion agent log
        return False, {"error": str(e)}


def check_lancedb_status() -> tuple[bool, dict[str, Any]]:
    """LanceDB 상태 직접 확인"""
    try:
        # 환경변수 확인
        vector_db = os.getenv("VECTOR_DB", "qdrant")
        if vector_db != "lancedb":
            return False, {"error": f"VECTOR_DB 환경변수가 lancedb가 아님 (현재: {vector_db})"}

        # LanceDB 어댑터 직접 확인
        sys.path.append(str(Path(__file__).parent.parent / "packages" / "afo-core"))
        from utils.vector_store import LanceDBAdapter, get_vector_store

        store = get_vector_store()
        if isinstance(store, LanceDBAdapter):
            is_available = store.is_available()
            if is_available:
                # 데이터베이스 파일 존재 확인
                lancedb_path = os.getenv("LANCEDB_PATH", "./data/lancedb")
                db_file = os.path.join(lancedb_path, "afokingdom_knowledge.lance")
                file_exists = os.path.exists(db_file)

                return True, {
                    "status": "LanceDB Connected",
                    "adapter": "LanceDBAdapter",
                    "database_file": db_file,
                    "file_exists": file_exists,
                }
            else:
                return False, {"error": "LanceDB 어댑터 연결 실패"}
        else:
            return False, {"error": f"잘못된 어댑터 타입: {type(store).__name__}"}

    except Exception as e:
        return False, {"error": f"LanceDB 확인 실패: {str(e)}"}


def check_core_endpoints() -> dict[str, tuple[bool, dict[str, Any]]]:
    """핵심 엔드포인트들 확인"""
    endpoints = [
        ("Chancellor (Brain)", "/chancellor/health"),
        ("Trinity (Soul)", "/api/trinity/health"),
        ("Auth (Heart)", "/api/auth/health"),
        ("Users (Liver)", "/api/users/health"),
        ("Intake (Stomach)", "/api/intake/health"),
        ("Personas (Mask)", "/api/personas/health"),
        ("Family (Spleen)", "/api/family/health"),
    ]

    # Family 라우터는 /family로도 등록되어 있을 수 있으므로 별도로 확인

    results = {}
    # #region agent log
    log_debug(
        "continuous_health_check.py:check_core_endpoints",
        "Starting core endpoints check",
        {"endpoint_count": len(endpoints)},
        "C",
    )
    # #endregion agent log

    for name, path in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{path}", timeout=5)
            # #region agent log
            log_debug(
                f"continuous_health_check.py:check_core_endpoints:{name}",
                "Endpoint response received",
                {"name": name, "path": path, "status_code": response.status_code},
                "C",
            )
            # #endregion agent log

            if response.status_code == 200:
                results[name] = (True, response.json())
            else:
                results[name] = (False, {"error": f"Status {response.status_code}"})
        except Exception as e:
            # #region agent log
            log_debug(
                f"continuous_health_check.py:check_core_endpoints:{name}",
                "Endpoint check failed",
                {"name": name, "path": path, "error": str(e)},
                "C",
            )
            # #endregion agent log
            results[name] = (False, {"error": str(e)})

    # #region agent log
    log_debug(
        "continuous_health_check.py:check_core_endpoints",
        "Core endpoints check completed",
        {
            "total": len(endpoints),
            "healthy": sum(1 for v in results.values() if v[0]),
            "unhealthy": sum(1 for v in results.values() if not v[0]),
        },
        "C",
    )
    # #endregion agent log

    return results


def print_status(component: str, is_healthy: bool, data: dict[str, Any]) -> None:
    """상태 출력"""
    status_icon = "✅" if is_healthy else "❌"
    color = COLORS["GREEN"] if is_healthy else COLORS["RED"]
    print(
        f"{status_icon} {COLORS['BOLD']}[{component}]{COLORS['RESET']} Status: {color}{'HEALTHY' if is_healthy else 'UNHEALTHY'}{COLORS['RESET']}"
    )
    if not is_healthy and "error" in data:
        print(f"   {COLORS['RED']}Error: {data['error']}{COLORS['RESET']}")


def continuous_health_check() -> None:
    """지속적인 건강 상태 검증"""
    print(
        f"\n{COLORS['BOLD']}{COLORS['BLUE']}🏰 AFO Kingdom Continuous Health Check 🏰{COLORS['RESET']}\n"
    )

    # #region agent log
    log_debug(
        "continuous_health_check.py:continuous_health_check",
        "Starting continuous health check session",
        {"timestamp": datetime.now().isoformat()},
        "MAIN",
    )
    # #endregion agent log

    all_healthy = True

    # 1. API 서버 기본 확인
    print(f"{COLORS['BOLD']}1. API Server Basic Check{COLORS['RESET']}")
    api_healthy, api_data = check_api_server()
    print_status("API Server", api_healthy, api_data)
    if not api_healthy:
        all_healthy = False
        print(
            f"   {COLORS['YELLOW']}⚠️  API 서버가 응답하지 않습니다. 서버가 실행 중인지 확인하세요.{COLORS['RESET']}"
        )
        print(
            f"   {COLORS['YELLOW']}   실행 명령: cd AFO && python -m uvicorn api_server:app --reload --port 8010{COLORS['RESET']}\n"
        )
        return

    print()

    # 2. 종합 건강 상태 확인
    print(f"{COLORS['BOLD']}2. Comprehensive Health Check{COLORS['RESET']}")
    comp_healthy, comp_data = check_comprehensive_health()
    if comp_healthy:
        status = comp_data.get("status", "unknown")
        trinity_score = comp_data.get("trinity_score", 0.0)
        skills_count = comp_data.get("skills", {}).get("total_skills", 0)
        scholars_count = comp_data.get("scholars", {}).get("total_scholars", 0)
        mcp_count = comp_data.get("mcp_tools", {}).get("total_servers", 0)

        print_status("Comprehensive Health", comp_healthy, comp_data)
        print(f"   Status: {status}")
        print(f"   Trinity Score: {trinity_score:.2f}")
        print(f"   Skills: {skills_count}개")
        print(f"   Scholars: {scholars_count}명")
        print(f"   MCP Tools: {mcp_count}개")

        # 서비스 상태
        services = comp_data.get("services", {})
        if services:
            print("   Services:")
            for service, healthy in services.items():
                icon = "✅" if healthy else "❌"
                print(f"     {icon} {service}: {'healthy' if healthy else 'unhealthy'}")
    else:
        print_status("Comprehensive Health", comp_healthy, comp_data)
        all_healthy = False

    print()

    # 3. LanceDB 상태 확인
    print(f"{COLORS['BOLD']}3. LanceDB Vector Store Check{COLORS['RESET']}")
    lancedb_healthy, lancedb_data = check_lancedb_status()
    print_status("LanceDB Vector Store", lancedb_healthy, lancedb_data)
    if lancedb_healthy:
        print(f"   Status: {lancedb_data.get('status', 'Unknown')}")
        print(f"   Adapter: {lancedb_data.get('adapter', 'Unknown')}")
        print(f"   Database: {lancedb_data.get('database_file', 'Unknown')}")
        print(f"   File Exists: {lancedb_data.get('file_exists', False)}")
    if not lancedb_healthy:
        all_healthy = False

    print()

    # 4. 핵심 엔드포인트 확인
    print(f"{COLORS['BOLD']}4. Core Endpoints Check{COLORS['RESET']}")
    core_results = check_core_endpoints()
    for name, (healthy, data) in core_results.items():
        print_status(name, healthy, data)
        if not healthy:
            all_healthy = False

    print()

    # 최종 결과
    print("=" * 60)
    if all_healthy:
        print(f"{COLORS['GREEN']}{COLORS['BOLD']}🎉 All Systems Operational! 🎉{COLORS['RESET']}")
    else:
        print(
            f"{COLORS['YELLOW']}{COLORS['BOLD']}⚠️  Some Systems Require Attention! ⚠️{COLORS['RESET']}"
        )
    print("=" * 60)

    # #region agent log
    log_debug(
        "continuous_health_check.py:continuous_health_check",
        "Continuous health check session completed",
        {
            "all_healthy": all_healthy,
            "api_healthy": api_healthy,
            "comprehensive_healthy": comp_healthy,
            "core_endpoints_healthy": all(v[0] for v in core_results.values()),
        },
        "MAIN",
    )
    # #endregion agent log


if __name__ == "__main__":
    continuous_health_check()
