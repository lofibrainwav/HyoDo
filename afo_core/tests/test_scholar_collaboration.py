import asyncio
import logging
import os
from AFO.chancellor_graph import ChancellorGraph

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_scholar_collaboration():
    """Test actual parallel collaboration between Heo Jun and Jeong Yak-yong."""
    # Create a mock AGENTS.md in current dir to test hierarchical injection
    with open("AGENTS.md", "w") as f:
        f.write("# Local Project Rules\n- Always use Glassmorphism for Phase 51 tests.")
    
    input_payload = {
        "command": "정교한 Glassmorphism이 적용된 새로운 대시보드 위젯을 리팩토링하고 구현하라. (Refactor and implement a new dashboard widget with sophisticated Glassmorphism)"
    }
    
    logger.info("Starting Phase 51 Parallel Command Test...")
    result = await ChancellorGraph.run_v2(input_payload)
    
    delegate_output = result["outputs"].get("DELEGATE", {})
    logger.info(f"Scholars Involved: {delegate_output.get('scholars_involved')}")
    logger.info(f"Results Summary: {delegate_output.get('results')}")
    
    # Check if results contain mentions of both agents
    results_str = str(delegate_output.get("results", ""))
    if "Heo Jun" in results_str and "Jeong Yak-yong" in results_str:
        logger.info("✅ SUCCESS: Parallel collaboration verified.")
    else:
        logger.warning("⚠️ PARTIAL SUCCESS: Some agents did not respond as expected.")

    # Cleanup mock AGENTS.md
    if os.path.exists("AGENTS.md"):
        os.remove("AGENTS.md")

if __name__ == "__main__":
    asyncio.run(test_scholar_collaboration())
