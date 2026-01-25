#!/usr/bin/env python3
"""眞 (Truth) - Dead Code 제거 검증."""

from pathlib import Path


def prove_deadcode_pruning() -> None:
    """
    Dead Code 제거가 올바르게 수행되었는지 검증.

    제거 대상 함수들이 프로덕션 코드에서 실제로 삭제되었는지 확인.
    """
    fabric_path = Path("packages/afo-core/AFO/afo_agent_fabric.py")
    if not fabric_path.exists():
        return

    content = fabric_path.read_text()
    targets = ["chancellor_ping_v2", "chancellor_ping_v3"]

    print("--- 🏛️ Metacognitive Deadcode Proof ---")
    for t in targets:
        if t not in content:
            print(f"✅ Truth: {t} successfully purged from production fabric.")
        else:
            print(f"❌ Truth: {t} still remains in production fabric.")


if __name__ == "__main__":
    prove_deadcode_pruning()
