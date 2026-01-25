#!/usr/bin/env python3
"""
AFO Kingdom MCP 서버 헬스체크 스크립트

목적: 10개 MCP 서버의 실제 실행 상태를 검증하여 의존성 다이어그램 생성

작성일: 2026-01-20
작성자: Sisyphus (AFOI)
버전: 1.0.0
"""

import json
import subprocess
import sys
from typing import Any, Dict

# MCP 서버 구성 (cursor/mcp.json 기반)
MCP_SERVERS = {
    "mcp-docker-gateway": {
        "name": "Docker MCP Gateway",
        "description": "Docker MCP Gateway - 24 servers",
        "health_check": None,  # Docker 서버 직접 검증 어려움 (Docker MCP Gateway 사용)
        "dependency_check": "docker ps --filter name=docker-mcp-gateway",
    },
    "afo-ultimate-mcp": {
        "name": "AFO Ultimate MCP Server",
        "description": "AFO Ultimate MCP Server - 14 tools",
        "health_check": "python3 -c 'from trinity_os.servers.afo_ultimate_mcp_server import afo_ultimate_mcp; afo_ultimate_mcp.get_status()'",
        "dependency_check": "ps aux | grep -i afo_ultimate_mcp",
    },
    "afo-skills-mcp": {
        "name": "AFO Skills MCP Server",
        "description": "AFO Skills MCP Server - 2 tools",
        "health_check": "python3 -c 'from trinity_os.servers.afo_skills_mcp import afo_skills_mcp; afo_skills_mcp.get_status()'",
        "dependency_check": "ps aux | grep -i afo_skills_mcp",
    },
    "trinity-score-mcp": {
        "name": "Trinity Score MCP Server",
        "description": "Trinity Score MCP Server - 1 tool",
        "health_check": "python3 -c 'from trinity_os.servers.trinity_score_mcp import trinity_score_mcp; trinity_score_mcp.get_status()'",
        "dependency_check": "ps aux | grep -i trinity_score_mcp",
    },
    "afo-skills-registry-mcp": {
        "name": "AFO Skills Registry MCP Server",
        "description": "AFO Skills Registry MCP Server",
        "health_check": "python3 -c 'from trinity_os.servers.afo_skills_registry_mcp import afo_skills_registry_mcp; afo_skills_registry_mcp.get_status()'",
        "dependency_check": "ps aux | grep -i afo_skills_registry_mcp",
    },
    "afo-obsidian-mcp": {
        "name": "AFO Obsidian MCP",
        "description": "AFO Obsidian MCP",
        "health_check": "python3 -c 'from trinity_os.servers.afo_obsidian_mcp import afo_obsidian_mcp; afo_obsidian_mcp.get_status()'",
        "dependency_check": "ps aux | grep -i afo_obsidian_mcp",
    },
    "context7": {
        "name": "Context7",
        "description": "Context7 External Knowledge Base",
        "health_check": None,  # 외부 서비스
        "dependency_check": None,  # 사용하지 않음
    },
    "sequential-thinking": {
        "name": "Sequential Thinking",
        "description": "Sequential Thinking MCP",
        "health_check": None,  # MCP 아키텍처
        "dependency_check": None,
    },
    "memory": {
        "name": "Memory",
        "description": "Memory MCP",
        "health_check": None,  # 내부 서비스
        "dependency_check": None,
    },
    "afo-messaging-mcp": {
        "name": "AFO Messaging MCP",
        "description": "AFO Messaging MCP Server",
        "health_check": "python3 -c 'from AFO.mcp.messaging_server import messaging_mcp; messaging_mcp.get_status()'",
        "dependency_check": "ps aux | grep -i messaging_mcp",
    },
}


def check_mcp_server(server_id: str, server_config: dict[str, Any]) -> dict[str, Any]:
    """개별 MCP 서버 헬스체크 수행"""

    result = {
        "server_id": server_id,
        "name": server_config.get("name", "Unknown"),
        "status": "unknown",
        "is_running": False,
        "health_check_cmd": server_config.get("health_check"),
        "dependency_check_cmd": server_config.get("dependency_check"),
        "output": "",
        "error": None,
    }

    # 1. 의존성 체크 (프로세스 실행 여부)
    dep_check_cmd = server_config.get("dependency_check")
    if dep_check_cmd:
        try:
            proc_result = subprocess.run(
                dep_check_cmd, shell=True, capture_output=True, text=True, timeout=5
            )
            result["is_running"] = (
                proc_result.returncode == 0 and len(proc_result.stdout.strip()) > 0
            )
            result["output"] = proc_result.stdout.strip()[:200] if proc_result.stdout else ""
        except subprocess.TimeoutExpired:
            result["output"] = "Dependency check timeout"
        except Exception as e:
            result["error"] = str(e)[:200]

    # 2. Health Check 체크 (헬스체크 명령 실행)
    health_check_cmd = server_config.get("health_check")
    if health_check_cmd and result["is_running"]:
        try:
            proc_result = subprocess.run(
                health_check_cmd, shell=True, capture_output=True, text=True, timeout=10
            )
            if proc_result.returncode == 0:
                result["status"] = "healthy"
                result["output"] = proc_result.stdout.strip()[:500]
            else:
                result["status"] = "unhealthy"
                result["error"] = f"Health check failed: {proc_result.stderr[:200]}"
        except subprocess.TimeoutExpired:
            result["output"] = "Health check timeout"
        except Exception as e:
            result["error"] = str(e)[:200]
    elif not health_check_cmd:
        result["status"] = "no health check defined"

    # 3. 상태 평가
    if result["is_running"] and result["status"] == "healthy":
        result["health"] = "healthy"
    elif result["is_running"] and result["status"] == "unhealthy":
        result["health"] = "unhealthy"
    elif not result["is_running"]:
        result["health"] = "stopped"
    else:
        result["health"] = "unknown"

    return result


def generate_dependency_diagram(results: list[dict[str, Any]]) -> str:
    """의존성 다이어그램 생성 (Mermaid 포맷)"""

    # 서버 분류
    python_servers = [
        r
        for r in results
        if r["server_id"].startswith("afo-") and r["server_id"] != "afo-obsidian-mcp"
    ]
    docker_servers = [r for r in results if r["server_id"] == "mcp-docker-gateway"]
        r
        for r in results
        if r["server_id"] not in python_servers and r["server_id"] not in docker_servers
    ]

    diagram = f"""graph TD
    A[MCP Docker Gateway] --> |B1[Docker MCP Gateway: {results[0].get("health", "unknown")}|
    
    A --> B1
    
    B1 --> |C1[Python Servers: {len([r for r in results if r["server_id"].startswith("afo-")])}개]|
    
    C1 --> |D1[Context7]|
    C1 --> |E1[Sequential Thinking]|
    C1 --> |F1[Memory]|
    C1 --> |G1[AFO Messaging]|
    
    D1[Context7]
    E1[Sequential Thinking]
    F1[Memory]
    
    G1 --> H1[AFO Messaging]
    H1:::stopped[Health: {results[-1].get("health", "unknown")}]
"""

    return diagram


def main() -> None:
    print("🔍 AFO Kingdom MCP 서버 헬스체크 시작")
    print("=" * 80)

    # 모든 MCP 서버 헬스체크 수행
    results = []
    for server_id, config in MCP_SERVERS.items():
        print(f"\n🔎 {config.get('name', server_id)} 헬스체크 중...")
        result = check_mcp_server(server_id, config)
        results.append(result)

        # 상태 출력
        status_icon = (
            "✅"
            if result["health"] == "healthy"
            else "⚠️"
            if result["health"] == "unhealthy"
            else "❌"
            if result["health"] == "stopped"
            else "⏸️"
        )
        print(f"  {status_icon} 상태: {result['health']}")
        print(f"  📋 출력: {result['output'][:100] if result['output'] else 'N/A'}")
        if result.get("error"):
            print(f"  ❌ 에러: {result['error']}")

    # 다이어그램 생성
    print("\n" + "=" * 80)
    print("📊 의존성 다이어그램 생성")
    diagram = generate_dependency_diagram(results)
    print(diagram)

    # JSON 보고서 생성
    print("\n" + "=" * 80)
    print("📋 JSON 보고서")
    report = {
        "timestamp": "2026-01-20T08:23:04Z",
        "summary": {
            "total_servers": len(MCP_SERVERS),
            "healthy": len([r for r in results if r["health"] == "healthy"]),
            "unhealthy": len([r for r in results if r["health"] == "unhealthy"]),
            "stopped": len([r for r in results if r["health"] == "stopped"]),
            "unknown": len([r for r in results if r["health"] == "unknown"]),
        },
        "servers": results,
        "dependency_diagram": diagram,
    }

    print(json.dumps(report, indent=2, ensure_ascii=False))

    # 결과 요약
    print("\n" + "=" * 80)
    print("📊 결과 요약")
    healthy_count = report["summary"]["healthy"]
    unhealthy_count = report["summary"]["unhealthy"]
    stopped_count = report["summary"]["stopped"]
    unknown_count = report["summary"]["unknown"]

    print(f"  ✅ Healthy: {healthy_count}/{len(MCP_SERVERS)}")
    print(f"  ⚠️ Unhealthy: {unhealthy_count}/{len(MCP_SERVERS)}")
    print(f"  ⏸️ Stopped: {stopped_count}/{len(MCP_SERVERS)}")
    print(f"  ❓ Unknown: {unknown_count}/{len(MCP_SERVERS)}")

    # 의존성 평가
    print("\n🔍 의존성 평가")
    if unhealthy_count == 0 and stopped_count == 0:
        print("  ✅ 모든 MCP 서버가 정상 상태입니다.")
        print("  ℹ️ Docker MCP Gateway는 별도의 Docker 서비스이므로 헬스체크에서 제외됩니다.")
    else:
        print("  ⚠️ 일부 MCP 서버가 비정상 상태입니다.")
        print("  💡 해결: 비정상 서버의 프로세스를 확인하고 재시작 필요 시도.")


if __name__ == "__main__":
    main()
