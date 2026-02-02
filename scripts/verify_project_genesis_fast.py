import asyncio
import sys
from datetime import datetime

# Setup Path
sys.path.append("./packages/afo-core")

import pathlib

from AFO.chancellor_graph import historian_node
from langchain_core.messages import HumanMessage


async def verify_genesis_fast():
    print("⚡ Project Genesis: FAST Verification Start")

    # Mock State
    mock_state = {
        "messages": [HumanMessage(content="Test Query: Is the Historian listening?")],
        "analysis_results": {
            "jegalryang": "Truth: The system is functional.",
            "samaui": "Goodness: No risks detected.",
            "juyu": "Beauty: The logs will be elegant.",
        },
        "trinity_score": 0.99,
        "risk_score": 0.01,
        "next_step": "finalize",
    }

    print("\n🚀 Direct Invocation of Historian Node...")
    await historian_node(mock_state)

    print("\n✅ Historian Execution Complete.")

    # Verify Chronicle Creation
    bridge_path = "./docs"
    today = datetime.now().strftime("%Y-%m-%d")
    daily_log = f"{bridge_path}/journals/daily/{today}.md"

    if pathlib.Path(daily_log).exists():
        print(f"\n✅ Daily Log Found: {daily_log}")
        with pathlib.Path(daily_log).open(encoding="utf-8") as f:
            content = f.read()
            if "Council Session Recorded" in content:
                print("   -> 'Council Session Recorded' signature found!")
            else:
                print("   -> ❌ Signature missing in Daily Log.")

        # Clean up for idempotency (optional, but good for check)
        # os.remove(daily_log)
    else:
        print(f"\n❌ Daily Log NOT found at {daily_log}")


if __name__ == "__main__":
    asyncio.run(verify_genesis_fast())
