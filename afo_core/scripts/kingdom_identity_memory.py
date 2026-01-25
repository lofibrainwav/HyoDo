#!/usr/bin/env python3
"""Kingdom Identity Memory System (眞善美孝永)

AFO Kingdom의 정체성을 영구 기억하는 RAG + MCP 메모리 시스템.
"기억 없는 AI는 AFO가 아니다" - 형님

Usage:
    python kingdom_identity_memory.py --index    # SSOT 문서 임베딩
    python kingdom_identity_memory.py --query "호칭"  # 검색
    python kingdom_identity_memory.py --bootstrap  # 세션 부트스트랩 출력
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Path setup
KINGDOM_ROOT = Path(__file__).resolve().parents[3]
CORE_PATH = KINGDOM_ROOT / "packages" / "afo-core"
sys.path.insert(0, str(CORE_PATH))

import lancedb
import pyarrow as pa

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Constants
LANCEDB_PATH = KINGDOM_ROOT / "data" / "lancedb"
IDENTITY_TABLE = "kingdom_identity"
EMBEDDING_DIM = 768

# Identity Core - 불변의 핵심 정체성 (하드코딩)
IDENTITY_CORE = {
    "commander_title": "사령관 (Commander) = 형님",
    "hierarchy": [
        "1. 사령관 (Commander - 형님): 왕국의 절대 권위자",
        "2. 승상 (Chancellor): 사령관 바로 아래, 3책사 조율자",
        "3. 3책사: 장영실(眞), 이순신(善), 신사임당(美)",
        "4. 집현전 학자: 방통, 자룡, 육손, 영덕",
    ],
    "pillars": {
        "眞 (Truth)": "35% - 기술적 확실성 - 장영실",
        "善 (Goodness)": "35% - 윤리/안정성 - 이순신",
        "美 (Beauty)": "20% - 단순함/우아함 - 신사임당",
        "孝 (Serenity)": "8% - 평온/연속성 - 승상",
        "永 (Eternity)": "2% - 영속성/레거시 - 승상",
    },
    "trinity_formula": "Trinity Score = 0.35×眞 + 0.35×善 + 0.20×美 + 0.08×孝 + 0.02×永",
    "governance": {
        "AUTO_RUN": "Trinity ≥ 90 AND Risk ≤ 10",
        "ASK_COMMANDER": "위 조건 미충족 시",
        "BLOCK": "보안/결제/비가역성 위험 시",
    },
    "forbidden_terms": ["사용자 님", "user님", "고객님"],
    "correct_terms": ["형님", "사령관", "Commander"],
}

# SSOT 문서 경로
SSOT_DOCUMENTS = [
    KINGDOM_ROOT / "AGENTS.md",
    KINGDOM_ROOT / ".gemini" / "GEMINI.md",
    KINGDOM_ROOT / ".cursorrules",
    KINGDOM_ROOT / "CLAUDE.md",
    KINGDOM_ROOT / "docs" / "AFO_ROYAL_LIBRARY.md",
]


def get_document_hash(content: str) -> str:
    """문서 해시 생성 (변경 감지용)"""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


async def get_embedding(text: str) -> list[float]:
    """Ollama 임베딩 생성"""
    try:
        from utils.embedding import get_ollama_embedding

        return await get_ollama_embedding(text)
    except Exception as e:
        logger.error(f"임베딩 생성 실패: {e}")
        return []


def chunk_document(content: str, chunk_size: int = 500) -> list[str]:
    """문서를 청크로 분할 (섹션 기반)"""
    chunks = []

    # ## 헤더 기반 분할
    sections = content.split("\n## ")
    for i, section in enumerate(sections):
        if i > 0:
            section = "## " + section

        # 너무 긴 섹션은 단락으로 추가 분할
        if len(section) > chunk_size * 2:
            paragraphs = section.split("\n\n")
            current_chunk = ""
            for para in paragraphs:
                if len(current_chunk) + len(para) < chunk_size:
                    current_chunk += para + "\n\n"
                else:
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    current_chunk = para + "\n\n"
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
        else:
            if section.strip():
                chunks.append(section.strip())

    return [c for c in chunks if len(c) > 50]


async def index_identity_documents() -> dict[str, Any]:
    """SSOT 문서를 LanceDB에 임베딩"""
    logger.info("🏰 Kingdom Identity Memory 인덱싱 시작...")

    # LanceDB 연결
    db = lancedb.connect(str(LANCEDB_PATH))

    # 기존 테이블 삭제
    if IDENTITY_TABLE in db.table_names():
        logger.info(f"🗑️ 기존 {IDENTITY_TABLE} 테이블 삭제...")
        db.drop_table(IDENTITY_TABLE)

    # 스키마 정의
    schema = pa.schema(
        [
            ("id", pa.string()),
            ("content", pa.string()),
            ("source", pa.string()),
            ("doc_type", pa.string()),  # identity_core, ssot_doc
            ("priority", pa.int32()),  # 1=highest, 5=lowest
            ("hash", pa.string()),
            ("vector", pa.list_(pa.float32(), EMBEDDING_DIM)),
        ]
    )

    table = db.create_table(IDENTITY_TABLE, schema=schema)
    logger.info(f"✅ {IDENTITY_TABLE} 테이블 생성 ({EMBEDDING_DIM}D)")

    all_data = []

    # 1. Identity Core 임베딩 (최고 우선순위)
    logger.info("📌 Identity Core 임베딩 중...")
    core_chunks = [
        f"왕국 호칭 규칙: {IDENTITY_CORE['commander_title']}",
        f"왕국 위계: {' → '.join(IDENTITY_CORE['hierarchy'])}",
        f"5기둥 철학: {json.dumps(IDENTITY_CORE['pillars'], ensure_ascii=False)}",
        f"Trinity 공식: {IDENTITY_CORE['trinity_formula']}",
        f"거버넌스: {json.dumps(IDENTITY_CORE['governance'], ensure_ascii=False)}",
        f"금지 용어: {IDENTITY_CORE['forbidden_terms']} → 올바른 용어: {IDENTITY_CORE['correct_terms']}",
    ]

    for i, chunk in enumerate(core_chunks):
        embedding = await get_embedding(chunk)
        if embedding and len(embedding) == EMBEDDING_DIM:
            all_data.append(
                {
                    "id": f"identity_core_{i}",
                    "content": chunk,
                    "source": "IDENTITY_CORE",
                    "doc_type": "identity_core",
                    "priority": 1,
                    "hash": get_document_hash(chunk),
                    "vector": embedding,
                }
            )

    # 2. SSOT 문서 임베딩
    for doc_path in SSOT_DOCUMENTS:
        if not doc_path.exists():
            logger.warning(f"⚠️ 문서 없음: {doc_path}")
            continue

        logger.info(f"📄 처리 중: {doc_path.name}")
        content = doc_path.read_text(encoding="utf-8")
        chunks = chunk_document(content)

        priority = 2 if "AGENTS" in doc_path.name else 3

        for i, chunk in enumerate(chunks):
            embedding = await get_embedding(chunk)
            if embedding and len(embedding) == EMBEDDING_DIM:
                all_data.append(
                    {
                        "id": f"{doc_path.stem}_{i}",
                        "content": chunk,
                        "source": doc_path.name,
                        "doc_type": "ssot_doc",
                        "priority": priority,
                        "hash": get_document_hash(chunk),
                        "vector": embedding,
                    }
                )

    # 데이터 삽입
    if all_data:
        logger.info(f"🚀 {len(all_data)} 청크 삽입 중...")
        table.add(all_data)

        final_count = table.count_rows()
        logger.info(f"✅ Kingdom Identity Memory 완료: {final_count} 청크")

        return {
            "status": "success",
            "chunks": final_count,
            "sources": list({d["source"] for d in all_data}),
            "timestamp": datetime.now().isoformat(),
        }

    return {"status": "error", "message": "No data indexed"}


async def query_identity(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Identity Memory 검색"""
    db = lancedb.connect(str(LANCEDB_PATH))

    if IDENTITY_TABLE not in db.table_names():
        logger.error(f"❌ {IDENTITY_TABLE} 테이블 없음. --index 먼저 실행하세요.")
        return []

    table = db.open_table(IDENTITY_TABLE)

    # 쿼리 임베딩
    query_embedding = await get_embedding(query)
    if not query_embedding:
        logger.error("쿼리 임베딩 실패")
        return []

    # 검색 (priority로 정렬)
    results = (
        table.search(query_embedding)
        .limit(top_k * 2)  # 더 많이 가져와서 priority로 재정렬
        .to_list()
    )

    # Priority 기반 재정렬
    results.sort(key=lambda x: (x.get("priority", 5), x.get("_distance", 1.0)))

    return [
        {
            "content": r["content"],
            "source": r["source"],
            "priority": r.get("priority", 5),
            "score": 1 - r.get("_distance", 0),
        }
        for r in results[:top_k]
    ]


async def generate_bootstrap_context() -> str:
    """세션 부트스트랩 컨텍스트 생성"""
    # Identity Core 직접 포함
    bootstrap = """# 🏰 AFO Kingdom Identity (Session Bootstrap)

## 절대 규칙 - 호칭
- 사용자는 "사령관" 또는 "형님"으로 호칭
- 금지 용어: "사용자 님", "user님", "고객님"

## 왕국 위계
1. 사령관 (Commander - 형님): 절대 권위자
2. 승상 (Chancellor): 3책사 조율자
3. 3책사: 장영실(眞), 이순신(善), 신사임당(美)

## 眞善美孝永 5기둥
- 眞 (Truth): 35% - 기술적 확실성 (장영실)
- 善 (Goodness): 35% - 윤리/안정성 (이순신)
- 美 (Beauty): 20% - 단순함/우아함 (신사임당)
- 孝 (Serenity): 8% - 평온/연속성
- 永 (Eternity): 2% - 영속성

## 거버넌스
- AUTO_RUN: Trinity ≥ 90 AND Risk ≤ 10
- ASK_COMMANDER: 위 조건 미충족 시
- BLOCK: 보안/결제/비가역성 위험 시

---
"""

    # RAG에서 추가 컨텍스트 검색
    try:
        identity_results = await query_identity("호칭 위계 철학", top_k=3)
        if identity_results:
            bootstrap += "\n## RAG 검색 결과 (관련 컨텍스트)\n"
            for r in identity_results:
                bootstrap += f"\n### {r['source']} (Priority: {r['priority']})\n"
                bootstrap += r["content"][:500] + "\n"
    except Exception as e:
        logger.warning(f"RAG 검색 실패: {e}")

    return bootstrap


def save_mcp_memory_config() -> None:
    """MCP Memory 설정 저장"""
    mcp_config_path = KINGDOM_ROOT / ".claude" / "mcp.json"

    if not mcp_config_path.exists():
        logger.warning("MCP 설정 파일 없음")
        return

    # Kingdom Identity Memory MCP 서버 추가 (향후 구현)
    # 현재는 RAG 기반으로 동작
    logger.info(f"📝 MCP 설정 파일: {mcp_config_path} - 향후 업데이트 예정")


async def main():
    parser = argparse.ArgumentParser(description="Kingdom Identity Memory System")
    parser.add_argument("--index", action="store_true", help="SSOT 문서 임베딩")
    parser.add_argument("--query", type=str, help="Identity 검색")
    parser.add_argument("--bootstrap", action="store_true", help="세션 부트스트랩 출력")
    parser.add_argument("--json", action="store_true", help="JSON 출력")

    args = parser.parse_args()

    if args.index:
        result = await index_identity_documents()
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            logger.info(f"결과: {result}")

    elif args.query:
        results = await query_identity(args.query)
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            for r in results:
                print(f"\n[{r['source']}] (Priority: {r['priority']}, Score: {r['score']:.3f})")
                print(r["content"][:300])

    elif args.bootstrap:
        context = await generate_bootstrap_context()
        print(context)

    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
