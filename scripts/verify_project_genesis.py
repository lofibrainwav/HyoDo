import asyncio
import os
import sys
from datetime import datetime

# Setup Path
sys.path.append("./packages/afo-core")

import pathlib

from langchain_core.messages import HumanMessage

from AFO.chancellor_graph import chancellor_graph


async def verify_genesis():
    print("📜 Project Genesis: Verification Start")

    # 1. Simulate Commander's Query
    query = "Explain the difference between Truth and Goodness in our Kingdom."
    print(f"👑 Commander Query: {query}")

    initial_state = {
        "messages": [HumanMessage(content=query)],
        "trinity_score": 0.85,  # Force ASK_COMMANDER path usually, but here we just want to reach Historian
        "risk_score": 0.1,
        "steps_taken": 0,
    }

    print("\n🚀 Running Chancellor Graph...")

    # Run the graph
    inputs = initial_state

    async for output in chancellor_graph.astream(
        inputs, config={"configurable": {"thread_id": "genesis_test"}}
    ):
        for key in output:
            print(f" -> Node Finished: {key}")
            if key == "historian":
                pass

    print("\n✅ Graph Execution Complete.")

    # 2. Verify Chronicle Creation
    # Look for the daily log or chronicle file
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
                print(f"Sample content:\n{content[:200]}")
    else:
        print(f"\n❌ Daily Log NOT found at {daily_log}")

    # Check for specific Chronicle file (timestamp based, hard to predict exact filename, but we check directory)
    chronicles_dir = f"{bridge_path}/journals/chronicles"
    if pathlib.Path(chronicles_dir).exists():
        files = os.listdir(chronicles_dir)
        if files:
            print(f"✅ Chronicles found: {len(files)} files in {chronicles_dir}")
            print(f"   Latest: {files[-1]}")
        else:
            print("⚠️ Chronicles directory exists but is empty.")
    else:
        # Directory might not exist if first run and mkdir is handled by bridge but maybe not recursively for parent?
        # Bridge code uses `parent.mkdir(parents=True)`, so it should exist if `write_note` succeeded.
        print(f"❌ Chronicles directory {chronicles_dir} does not exist.")


if __name__ == "__main__":
    asyncio.run(verify_genesis())
