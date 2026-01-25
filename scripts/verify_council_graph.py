import asyncio
import logging
import sys
from datetime import UTC, datetime

# Setup path
sys.path.append("packages/afo-core")

from AFO.api.routers import multi_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CouncilVerifier")


async def verify_council():
    logger.info("🏛️ Verifying Council of Minds (TICKET-048)...")

    # 1. Build Graph
    graph = multi_agent.council_graph
    logger.info("✅ Graph Compiled Successfully")

    # 2. Prepare Mock Task
    task_input = {
        "task_id": "verify-001",
        "task": "Should we deploy the new Zero Trust Wallet to production?",
        "context": {"env": "prod", "risk_level": "high"},
        "truth_output": {},
        "goodness_output": {},
        "beauty_output": {},
        "consensus_output": {},
        "trinity_score": 0.0,
        "final_decision": "",
        "errors": [],
        "start_time": datetime.now(UTC).timestamp(),
    }

    # 3. Invoke Graph (Mock Mode should be active via env vars in main)
    # Using AFO_LLM_MOCK_MODE=true for testing
    import os

    os.environ["AFO_LLM_MOCK_MODE"] = "true"

    logger.info("🤖 Invoking Council Graph (Mock Mode)...")
    result = await graph.ainvoke(task_input)

    # 4. Verify Outputs
    truth = result.get("truth_output")
    goodness = result.get("goodness_output")
    beauty = result.get("beauty_output")
    consensus = result.get("consensus_output")
    score = result.get("trinity_score", 0)

    logger.info(f"🦾 Truth: {truth}")
    logger.info(f"🛡️ Goodness: {goodness}")
    logger.info(f"🎭 Beauty: {beauty}")
    logger.info(f"⚖️ Consensus: {consensus}")
    logger.info(f"📊 Trinity Score: {score}")

    if consensus.get("reached"):
        logger.info("✅ SUCCESS: Consensus Reached")
        sys.exit(0)
    else:
        logger.error("❌ FAILURE: No Consensus")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(verify_council())
