import asyncio
import logging
import os
import sys
from pathlib import Path

# Add package root to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
package_root = os.path.abspath(os.path.join(script_dir, "../../"))
if package_root not in sys.path:
    sys.path.append(package_root)

from AFO.rag_engine import rag_engine
from utils.vector_store import get_vector_store

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def verify_rag_renaissance():
    """RAG Renaissance 기능 검증 (眞 - Truth)"""
    # Force absolute path for verification
    kingdom_root = Path(__file__).resolve().parents[3]
    os.environ["LANCEDB_PATH"] = str(kingdom_root / "data/lancedb")

    logger.info("🏰 RAG Renaissance Verification Started...")

    # 1. Vector Store 접속 확인
    logger.info("🔍 Checking LanceDB connection...")
    store = get_vector_store()
    if not store.is_available():
        logger.error("❌ LanceDB is not available. Please check LANCEDB_PATH.")
        return False
    logger.info("✅ LanceDB is available.")

    # 2. RAG Engine 실행 테스트 (Dry Run)
    logger.info("🚀 Running RAG query search...")
    query = "왕국의 삼위일체(Trinity)는 무엇인가?"

    try:
        # 실제 LanceDB 검색 및 LLM 라우팅 테스트
        result = await rag_engine.execute(query)

        logger.info("\n[RAG Execution Result]")
        logger.info(f"Question: {query}")
        logger.info(f"Response: {result['response']}")
        logger.info(f"Confidence: {result['confidence']:.2f}")
        logger.info(f"Sources: {result['sources']}")
        logger.info(f"Enhancement: {result['enhancement']}")

        if result["sources"]:
            logger.info("✅ RAG Success: Retrieved data from LanceDB.")
        else:
            logger.warning("⚠️ RAG Warning: Search results empty (Knowledge base might be empty).")

        return True

    except Exception as e:
        logger.error(f"❌ RAG Execution Failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(verify_rag_renaissance())
    sys.exit(0 if success else 1)
