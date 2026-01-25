import asyncio
import logging
import os
import sys
from pathlib import Path

import lancedb
import pyarrow as pa

# Force absolute path
# Standardized relative root
KINGDOM_ROOT = str(Path(__file__).resolve().parents[3])
LANCEDB_ABS_PATH = os.path.join(KINGDOM_ROOT, "data/lancedb")

if os.path.join(KINGDOM_ROOT, "packages/afo-core") not in sys.path:
    sys.path.append(os.path.join(KINGDOM_ROOT, "packages/afo-core"))

from utils.embedding import get_ollama_embedding

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def reindex_kingdom_direct():
    """왕국 지식 베이스 직접 재인덱싱 (眞 - Direct LanceDB)"""
    logger.info(f"🏰 Starting Direct Kingdom Re-indexing to: {LANCEDB_ABS_PATH}")

    collection_name = "afokingdom_knowledge"

    # 1. Connect and Drop
    db = lancedb.connect(LANCEDB_ABS_PATH)
    if collection_name in db.table_names():
        logger.info(f"🗑️ Deleting existing {collection_name}...")
        db.drop_table(collection_name)

    # 2. Create Table with Schema
    schema = pa.schema(
        [
            ("id", pa.string()),
            ("content", pa.string()),
            ("source", pa.string()),
            ("vector", pa.list_(pa.float32(), 768)),
        ]
    )
    table = db.create_table(collection_name, schema=schema)
    logger.info(f"✅ Created fresh table: {collection_name} (768D)")

    # 3. 문서 로드
    docs_dir = Path(KINGDOM_ROOT) / "packages/afo-core/docs"
    targets = list(docs_dir.glob("*.md")) + list((docs_dir / "afo").glob("*.md"))

    if not targets:
        logger.error("❌ No documents found to index.")
        return False

    all_data = []
    for doc_path in targets:
        try:
            with open(doc_path, encoding="utf-8") as f:
                content = f.read()

            # Simple chunking
            paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 50]

            for i, p in enumerate(paragraphs):
                embedding = await get_ollama_embedding(p)
                if not embedding or len(embedding) != 768:
                    continue

                all_data.append(
                    {
                        "id": f"{doc_path.name}_{i}",
                        "content": p,
                        "vector": embedding,
                        "source": doc_path.name,
                    }
                )

            logger.info(f"⏳ Prepared: {doc_path.name} ({len(paragraphs)} chunks)")
        except Exception as e:
            logger.error(f"❌ Failed to process {doc_path.name}: {e}")

    # 4. Final Insert
    if all_data:
        logger.info(f"🚀 Inserting {len(all_data)} chunks...")
        table.add(all_data)

        # 5. Verify
        final_count = table.count_rows()
        logger.info(f"📊 Final count verified: {final_count}")
        if final_count > 0:
            logger.info("✅ SUCCESS: Kingdom knowledge is now grounded in LanceDB (768D).")
        else:
            logger.error("❌ FAILURE: Row count is still 0.")
            return False

    return True


if __name__ == "__main__":
    success = asyncio.run(reindex_kingdom_direct())
    sys.exit(0 if success else 1)
