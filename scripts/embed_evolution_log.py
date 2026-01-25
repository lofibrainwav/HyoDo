#!/usr/bin/env python3
"""
AFO Evolution Log Embedder - 진화 연대기 RAG 임베딩
眞善美孝永 - Context 창 최적화를 위한 벡터화

Usage:
    python scripts/embed_evolution_log.py [--compact]

    --compact: 임베딩 후 원본 파일을 요약만 남기고 압축
"""

import asyncio
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

import lancedb
import pyarrow as pa

KINGDOM_ROOT = Path(__file__).parent.parent
LANCEDB_PATH = KINGDOM_ROOT / "data" / "lancedb"
EVOLUTION_LOG = KINGDOM_ROOT / "AFO_EVOLUTION_LOG.md"
ARCHIVE_DIR = KINGDOM_ROOT / "docs" / "ops" / "evolution_archive"

if str(KINGDOM_ROOT / "packages" / "afo-core") not in sys.path:
    sys.path.insert(0, str(KINGDOM_ROOT / "packages" / "afo-core"))

from utils.embedding import get_ollama_embedding

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def parse_evolution_log(content: str) -> list[dict]:
    """Evolution Log를 Phase/Decision Log 단위로 파싱"""
    chunks = []

    # 1. SSOT Capsules (## [SSOT/PH-XX/...] ...)
    capsule_pattern = r"(## \[SSOT/PH-\d+.*?\].*?)(?=## \[SSOT/PH-|\Z|---\n\n##[^[])"
    capsules = re.findall(capsule_pattern, content, re.DOTALL)
    for cap in capsules:
        cap = cap.strip()
        if len(cap) > 50:
            # Extract phase number
            match = re.search(r"PH-(\d+)", cap)
            phase_num = match.group(1) if match else "0"
            chunks.append(
                {
                    "type": "capsule",
                    "phase": int(phase_num),
                    "content": cap,
                }
            )

    # 2. Phase Details (### Phase XX: ...)
    phase_pattern = r"(### Phase \d+:.*?)(?=### Phase \d+:|\Z|---\n\n##)"
    phases = re.findall(phase_pattern, content, re.DOTALL)
    for ph in phases:
        ph = ph.strip()
        if len(ph) > 100:
            match = re.search(r"Phase (\d+)", ph)
            phase_num = match.group(1) if match else "0"
            chunks.append(
                {
                    "type": "phase_detail",
                    "phase": int(phase_num),
                    "content": ph,
                }
            )

    # 3. Decision Logs (#### YYYY-MM-DD HH:MM:SS Decision Log)
    decision_pattern = (
        r"(#### \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} Decision Log.*?)(?=#### \d{4}-\d{2}-\d{2}|\Z)"
    )
    decisions = re.findall(decision_pattern, content, re.DOTALL)
    for dec in decisions:
        dec = dec.strip()
        if len(dec) > 50:
            # Extract timestamp
            match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", dec)
            timestamp = match.group(1) if match else "unknown"
            chunks.append(
                {
                    "type": "decision_log",
                    "timestamp": timestamp,
                    "content": dec,
                }
            )

    logger.info(
        f"Parsed: {len([c for c in chunks if c['type'] == 'capsule'])} capsules, "
        f"{len([c for c in chunks if c['type'] == 'phase_detail'])} phase details, "
        f"{len([c for c in chunks if c['type'] == 'decision_log'])} decision logs"
    )

    return chunks


async def embed_chunks(chunks: list[dict]) -> list[dict]:
    """청크들을 임베딩"""
    embedded = []
    for i, chunk in enumerate(chunks):
        try:
            embedding = await get_ollama_embedding(chunk["content"][:2000])  # Max 2000 chars
            if embedding and len(embedding) == 768:
                chunk_id = f"evo_{chunk['type']}_{i}"
                if chunk["type"] == "decision_log":
                    chunk_id = f"evo_decision_{chunk.get('timestamp', i)}"
                elif chunk["type"] in ("capsule", "phase_detail"):
                    chunk_id = f"evo_phase_{chunk.get('phase', i)}_{chunk['type']}"

                embedded.append(
                    {
                        "id": chunk_id,
                        "content": chunk["content"],
                        "source": "AFO_EVOLUTION_LOG.md",
                        "chunk_type": chunk["type"],
                        "vector": embedding,
                    }
                )

            if (i + 1) % 10 == 0:
                logger.info(f"Embedded {i + 1}/{len(chunks)} chunks...")

        except Exception as e:
            logger.warning(f"Failed to embed chunk {i}: {e}")

    return embedded


async def index_to_lancedb(embedded_chunks: list[dict]) -> bool:
    """LanceDB에 인덱싱"""
    collection_name = "evolution_log"

    db = lancedb.connect(str(LANCEDB_PATH))

    # Drop existing
    if collection_name in db.table_names():
        logger.info(f"Dropping existing {collection_name}...")
        db.drop_table(collection_name)

    # Create schema
    schema = pa.schema(
        [
            ("id", pa.string()),
            ("content", pa.string()),
            ("source", pa.string()),
            ("chunk_type", pa.string()),
            ("vector", pa.list_(pa.float32(), 768)),
        ]
    )

    table = db.create_table(collection_name, schema=schema)
    logger.info(f"Created table: {collection_name}")

    # Insert
    if embedded_chunks:
        table.add(embedded_chunks)
        final_count = table.count_rows()
        logger.info(f"Indexed {final_count} chunks to LanceDB")
        return final_count > 0

    return False


def compact_evolution_log() -> None:
    """원본 파일을 요약만 남기고 압축"""
    content = EVOLUTION_LOG.read_text(encoding="utf-8")

    # Archive the full file first
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archive_name = f"evolution_log_{datetime.now().strftime('%Y%m')}.md"
    archive_path = ARCHIVE_DIR / archive_name

    if not archive_path.exists():
        archive_path.write_text(content, encoding="utf-8")
        logger.info(f"Archived to: {archive_path}")
    else:
        logger.info(f"Archive already exists: {archive_path}")

    # Extract only the header and SSOT capsules (top ~100 lines)
    lines = content.split("\n")

    # Find where detailed phases start (### Phase)
    cutoff = len(lines)
    for i, line in enumerate(lines):
        if line.startswith("### Phase") or line.startswith("#### "):
            cutoff = i
            break

    # Keep header + capsules + add RAG notice
    compact_content = "\n".join(lines[:cutoff])
    compact_content += f"""

---

## RAG 아카이브 안내

상세 Phase 기록 및 Decision Log는 **LanceDB RAG**로 이관되었습니다.

- **컬렉션**: `evolution_log`
- **쿼리 예시**: "Phase 47 Network Hardening", "Decision Log 2026-01"
- **아카이브 경로**: `docs/ops/evolution_archive/`
- **이관 일시**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

> *"역사를 잊지 않되, 가볍게 운반한다."* — AFO 왕국

"""

    # Backup then write
    backup_path = EVOLUTION_LOG.with_suffix(".md.bak")
    EVOLUTION_LOG.rename(backup_path)
    EVOLUTION_LOG.write_text(compact_content, encoding="utf-8")

    new_lines = len(compact_content.split("\n"))
    logger.info(f"Compacted: {len(lines)} → {new_lines} lines")
    logger.info(f"Backup saved: {backup_path}")


async def main():
    """메인 실행"""
    compact_mode = "--compact" in sys.argv

    logger.info("=" * 60)
    logger.info("AFO Evolution Log Embedder")
    logger.info("=" * 60)

    # 1. Read & Parse
    if not EVOLUTION_LOG.exists():
        logger.error(f"File not found: {EVOLUTION_LOG}")
        return False

    content = EVOLUTION_LOG.read_text(encoding="utf-8")
    logger.info(f"Read {len(content)} bytes from {EVOLUTION_LOG.name}")

    chunks = parse_evolution_log(content)
    if not chunks:
        logger.error("No chunks parsed!")
        return False

    # 2. Embed
    logger.info("Starting embedding...")
    embedded = await embed_chunks(chunks)
    if not embedded:
        logger.error("No chunks embedded!")
        return False

    # 3. Index
    success = await index_to_lancedb(embedded)
    if not success:
        logger.error("Indexing failed!")
        return False

    logger.info("Embedding complete!")

    # 4. Compact (if requested)
    if compact_mode:
        logger.info("Compacting original file...")
        compact_evolution_log()
        logger.info("Compaction complete!")
    else:
        logger.info("Tip: Run with --compact to reduce file size after embedding")

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
