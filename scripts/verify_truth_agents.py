#!/usr/bin/env python3
"""
🤖 AFO Kingdom Audit Script - Agents (Truth)
"""

import sys
from pathlib import Path

sys.path.append(str(Path.cwd() / "packages/afo-core"))


def audit_agents() -> None:
    # Check for critical agent files existence
    agent_files = [
        "afo_soul_engine/agents/five_pillars_agent.py",
        "strategists/zhuge_liang.py",
        "tigers/guan_yu.py",
        "AFO/julie/ai_agents.py",
    ]

    base_path = Path("packages/afo-core")
    missing = []

    print("🕵️ Auditing Agent Files...")
    for rel_path in agent_files:
        full_path = base_path / rel_path
        if full_path.exists():
            print(f"✅ Found Agent: {rel_path}")
        else:
            print(f"❌ Missing Agent File: {rel_path}")
            missing.append(rel_path)

    # Check for service instantiation (simulation)
    print("\n🕵️ Auditing Agent Instantiation...")
    try:
        from infrastructure.llm.router import LLMRouter

        LLMRouter()
        print("✅ LLMRouter Instantiated (Truth Core)")
    except ImportError as e:
        print(f"❌ Failed to instantiate LLMRouter: {e}")
        missing.append("LLMRouter")
    except Exception as e:
        print(f"⚠️ Instantiation Warning (Environment dependent): {e}")

    return len(missing) == 0


if __name__ == "__main__":
    audit_agents()
