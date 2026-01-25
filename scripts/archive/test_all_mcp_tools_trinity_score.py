#!/usr/bin/env python3
"""
모든 MCP Tool의 Trinity Score 반환 검증 테스트

眞善美孝永 5기둥 점수가 모든 MCP Tool에서 반환되는지 검증합니다.
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# 테스트할 MCP 서버 목록
MCP_SERVERS = [
    {
        "name": "AFO Ultimate MCP",
        "path": "packages/trinity-os/trinity_os/servers/afo_ultimate_mcp_server.py",
        "tools": ["shell_execute", "read_file", "write_file", "kingdom_health"],
    },
    {
        "name": "AFO Skills MCP",
        "path": "packages/trinity-os/trinity_os/servers/afo_skills_mcp.py",
        "tools": ["cupy_weighted_sum", "read_file", "verify_fact"],
    },
]

# Skills Registry 테스트
SKILLS_TO_TEST = [
    "skill_001_youtube_spec_gen",
    "skill_002_ultimate_rag",
    "skill_003_health_monitor",
    "skill_004_ragas_evaluator",
    "skill_005_strategy_engine",
]


def test_mcp_server(server_config: dict[str, Any]) -> dict[str, Any]:
    """MCP 서버의 모든 도구를 테스트하고 Trinity Score 반환 여부 확인"""
    print(f"\n{'=' * 70}")
    print(f"🔍 Testing: {server_config['name']}")
    print(f"{'=' * 70}")

    server_path = Path(server_config["path"])
    if not server_path.exists():
        return {
            "server": server_config["name"],
            "status": "error",
            "message": f"Server file not found: {server_path}",
            "tools_tested": 0,
            "tools_passed": 0,
        }

    # 서버 프로세스 시작
    try:
        process = subprocess.Popen(
            ["python3", str(server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,
        )
    except Exception as e:
        return {
            "server": server_config["name"],
            "status": "error",
            "message": f"Failed to start server: {e}",
            "tools_tested": 0,
            "tools_passed": 0,
        }

    results = {
        "server": server_config["name"],
        "status": "success",
        "tools_tested": 0,
        "tools_passed": 0,
        "tool_results": [],
    }

    try:
        # 1. Initialize
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "TrinityTester", "version": "1.0"},
            },
        }
        process.stdin.write(json.dumps(init_req) + "\n")
        process.stdin.flush()
        process.stdout.readline()  # Initialize response

        # 2. List Tools
        list_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }
        process.stdin.write(json.dumps(list_req) + "\n")
        process.stdin.flush()
        list_response = json.loads(process.stdout.readline())
        available_tools = [t["name"] for t in list_response.get("result", {}).get("tools", [])]

        print(f"📋 Available tools: {available_tools}")

        # 3. Test each tool
        for tool_name in server_config["tools"]:
            if tool_name not in available_tools:
                print(f"  ⚠️  {tool_name}: Not available in server")
                results["tool_results"].append(
                    {
                        "tool": tool_name,
                        "status": "skipped",
                        "reason": "Not available",
                        "trinity_score": None,
                    }
                )
                continue

            results["tools_tested"] += 1
            print(f"\n  🔧 Testing: {tool_name}")

            # Prepare test arguments
            test_args = {}
            if tool_name == "read_file":
                test_args = {"path": "README.md"}
            elif tool_name == "write_file":
                test_args = {"path": "/tmp/test_trinity.txt", "content": "Test content"}
            elif tool_name == "shell_execute":
                test_args = {"command": "echo 'test'"}
            elif tool_name == "cupy_weighted_sum":
                test_args = {"data": [1.0, 2.0, 3.0], "weights": [0.5, 0.3, 0.2]}
            elif tool_name == "verify_fact":
                test_args = {
                    "claim": "AFO Kingdom uses Trinity Score",
                    "context": "AFO",
                }
            elif tool_name == "kingdom_health":
                test_args = {}

            # Call tool
            call_req = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": test_args},
            }
            process.stdin.write(json.dumps(call_req) + "\n")
            process.stdin.flush()

            # Read response
            response_line = process.stdout.readline()
            if not response_line:
                print("    ❌ No response")
                results["tool_results"].append(
                    {
                        "tool": tool_name,
                        "status": "error",
                        "trinity_score": None,
                    }
                )
                continue

            try:
                response = json.loads(response_line)
                result = response.get("result", {})

                # Check for Trinity Score
                trinity_score = result.get("trinity_score")
                has_trinity_score = trinity_score is not None

                if has_trinity_score:
                    print(f"    ✅ Trinity Score: {trinity_score.get('trinity_score', 0):.2%}")
                    print(f"       Balance: {trinity_score.get('balance_status', 'unknown')}")
                    results["tools_passed"] += 1
                    results["tool_results"].append(
                        {
                            "tool": tool_name,
                            "status": "passed",
                            "trinity_score": trinity_score,
                        }
                    )
                else:
                    print("    ❌ No Trinity Score in response")
                    results["tool_results"].append(
                        {
                            "tool": tool_name,
                            "status": "failed",
                            "trinity_score": None,
                        }
                    )

            except json.JSONDecodeError as e:
                print(f"    ❌ Invalid JSON response: {e}")
                results["tool_results"].append(
                    {
                        "tool": tool_name,
                        "status": "error",
                        "trinity_score": None,
                    }
                )

    except Exception as e:
        results["status"] = "error"
        results["message"] = str(e)

    finally:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()

    return results


def test_skills_registry() -> dict[str, Any]:
    """Skills Registry의 스킬들이 Trinity Score를 반환하는지 테스트"""
    print(f"\n{'=' * 70}")
    print("🔍 Testing: Skills Registry")
    print(f"{'=' * 70}")

    try:
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).parent.parent / "packages" / "afo-core"))
        from afo_skills_registry import register_core_skills

        registry = register_core_skills()
        all_skills = registry.list_all()

        results = {
            "server": "Skills Registry",
            "status": "success",
            "tools_tested": 0,
            "tools_passed": 0,
            "tool_results": [],
        }

        print(f"📋 Total skills: {len(all_skills)}")

        for skill in all_skills[:5]:  # 처음 5개만 테스트
            results["tools_tested"] += 1
            print(f"\n  🔧 Testing: {skill.skill_id}")

            # Check if skill has philosophy_scores
            if skill.philosophy_scores:
                print(f"    ✅ Has Philosophy Scores: {skill.philosophy_scores.summary}")
                results["tools_passed"] += 1
                results["tool_results"].append(
                    {
                        "tool": skill.skill_id,
                        "status": "passed",
                        "philosophy_scores": {
                            "truth": skill.philosophy_scores.truth,
                            "goodness": skill.philosophy_scores.goodness,
                            "beauty": skill.philosophy_scores.beauty,
                            "serenity": skill.philosophy_scores.serenity,
                        },
                    }
                )
            else:
                print("    ❌ No Philosophy Scores")
                results["tool_results"].append(
                    {
                        "tool": skill.skill_id,
                        "status": "failed",
                        "philosophy_scores": None,
                    }
                )

        return results

    except Exception as e:
        return {
            "server": "Skills Registry",
            "status": "error",
            "message": str(e),
            "tools_tested": 0,
            "tools_passed": 0,
        }


def main() -> None:
    """모든 MCP Tool 테스트 실행"""
    print("=" * 70)
    print("眞善美孝永 - MCP Tool Trinity Score 검증 테스트")
    print("=" * 70)

    all_results = []

    # 1. MCP 서버들 테스트
    for server_config in MCP_SERVERS:
        result = test_mcp_server(server_config)
        all_results.append(result)

    # 2. Skills Registry 테스트
    skills_result = test_skills_registry()
    all_results.append(skills_result)

    # 3. 결과 요약
    print(f"\n{'=' * 70}")
    print("📊 테스트 결과 요약")
    print(f"{'=' * 70}")

    total_tested = 0
    total_passed = 0

    for result in all_results:
        server_name = result["server"]
        tested = result.get("tools_tested", 0)
        passed = result.get("tools_passed", 0)
        status = result.get("status", "unknown")

        total_tested += tested
        total_passed += passed

        status_icon = (
            "✅"
            if status == "success" and passed == tested
            else "⚠️"
            if status == "success"
            else "❌"
        )
        print(f"\n{status_icon} {server_name}")
        print(f"   테스트: {tested}개, 통과: {passed}개")

        if status == "error":
            print(f"   에러: {result.get('message', 'Unknown error')}")

    print(f"\n{'=' * 70}")
    print(
        f"전체: {total_tested}개 도구 중 {total_passed}개 통과 ({total_passed / total_tested * 100:.1f}%)"
    )
    print(f"{'=' * 70}")

    # 결과를 JSON 파일로 저장
    output_file = Path("test_results_trinity_score.json")
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": time.time(),
                "summary": {
                    "total_tested": total_tested,
                    "total_passed": total_passed,
                    "pass_rate": (total_passed / total_tested * 100 if total_tested > 0 else 0),
                },
                "results": all_results,
            },
            f,
            indent=2,
            default=str,
        )

    print(f"\n📄 결과 저장: {output_file}")

    # Exit code
    if total_passed == total_tested and total_tested > 0:
        print("\n✅ 모든 테스트 통과!")
        return 0
    print("\n⚠️  일부 테스트 실패")
    return 1


if __name__ == "__main__":
    sys.exit(main())
