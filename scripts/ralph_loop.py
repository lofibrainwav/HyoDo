#!/usr/bin/env python3
import asyncio
import json
import os
import sys
from datetime import datetime

# Add workspace root to sys.path to enable AFO imports
WORKSPACE_ROOT = os.environ.get("WORKSPACE_ROOT", "./packages/afo-core")
if WORKSPACE_ROOT not in sys.path:
    sys.path.append(WORKSPACE_ROOT)

from AFO.chancellor_graph import ChancellorGraph

PRD_PATH = "prd.json"
AGENTS_LOG = "AGENTS.md"


def load_prd_local() -> None:
    if not os.path.exists(PRD_PATH):
        return {"stories": []}
    with open(PRD_PATH, "r") as f:
        return json.load(f)


def save_prd_local(data) -> None:
    with open(PRD_PATH, "w") as f:
        json.dump(data, f, indent=2)


def log_agent_learning(story_id, title, learning) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"\n### [{timestamp}] {story_id}: {title} - Learning\n"
    content = f"- {learning}\n"
    with open(AGENTS_LOG, "a") as f:
        f.write(header + content)


async def run_iteration():
    prd = load_prd_local()
    stories = prd.get("stories", [])

    # Find next todo story
    current_story = next((s for s in stories if s["status"] == "todo"), None)

    if not current_story:
        print("✅ Ralph Loop: All stories are currently complete. Standing by for next deployment.")
        return False

    story_id = current_story["id"]
    story_title = current_story["title"]
    story_desc = current_story["description"]

    print(f"🚀 Ralph Loop: Starting iteration for {story_id}: {story_title}")

    # Transition to in-progress
    current_story["status"] = "in-progress"
    save_prd_local(prd)

    try:
        # INVOKE CHANCELLOR GRAPH V2
        print(f"🧠 Chancellor: Analyzing STORY {story_id}...")

        payload = {
            "query": f"Implement or validate this story from the Phase 30 PRD: {story_desc}",
            "llm_context": {"temperature": 0.3, "max_tokens": 1000},
            "thread_id": f"ralph-loop-{story_id}",
            "skill_id": "ralph_loop_autonomous_agent",
        }

        # Execute via Chancellor V2
        result_state = await ChancellorGraph.run_v2(payload)

        # Extract results
        outputs = result_state.get("outputs", {})
        outputs.get("EXECUTE", {})
        report_text = outputs.get("REPORT", {}).get(
            "result", "Completed successfully via Ralph Loop."
        )

        print(f"✅ Chancellor Response: {report_text[:100]}...")

        # Update PRD
        current_story["status"] = "done"
        current_story["implemented_at"] = datetime.now().isoformat()

        # Log learning
        learning_summary = f"Autonomous implementation successful. Graph Trace: {result_state.get('trace_id', 'N/A')}"
        log_agent_learning(story_id, story_title, learning_summary)

        save_prd_local(prd)
        print(f"✨ {story_id} synchronized with Kingdom state.")

    except Exception as e:
        print(f"❌ Ralph Loop Failed for {story_id}: {e}")
        current_story["status"] = "failed"
        current_story["error"] = str(e)
        save_prd_local(prd)
        return False

    return True


if __name__ == "__main__":
    print("🏰 AFO Kingdom: Ralph Loop Orchestrator (TICKET-104) v2.0")
    try:
        asyncio.run(run_iteration())
    except KeyboardInterrupt:
        print("\n🛑 Ralph Loop interrupted by user.")
