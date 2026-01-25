#!/usr/bin/env python3
"""
LanceDB 하이브리드 검색 + qwen3-vl 예제 (SSOT)
Docker 0, Ollama 라이브러리 모델만 사용

형님이 제시한 정확한 LanceDB API 사용:
- LanceModel + Vector(dim=...) 패턴
- RRFReranker() 객체 사용
- 임베딩 차원 자동 감지
- Ollama /api/embed + /api/generate 표준 API

사용법:
python scripts/lance_hybrid_qwen3.py ingest /path/to/receipt.jpg
python scripts/lance_hybrid_qwen3.py search "비싼 커피" 50000 스타벅스
"""

import base64
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import lancedb
import requests
from lancedb.pydantic import LanceModel, Vector
from lancedb.rerankers import RRFReranker

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
VISION_MODEL = os.getenv("VISION_MODEL", "qwen3-vl")
EMBED_MODEL = os.getenv("EMBED_MODEL", "embeddinggemma")

LANCEDB_URI = os.getenv("LANCEDB_URI", str(Path.home() / "AFO_Kingdom" / "lancedb_vault"))
LANCEDB_TABLE = os.getenv("LANCEDB_TABLE", "receipts_v1")


def _b64_image(path: Path) -> str:
    """이미지를 base64로 인코딩 (qwen3-vl용)"""
    data = path.read_bytes()
    return base64.b64encode(data).decode("utf-8")


def ollama_generate_with_image(prompt: str, image_path: Path) -> str:
    """qwen3-vl로 이미지 분석 (Ollama /api/generate)"""
    payload = {
        "model": VISION_MODEL,
        "prompt": prompt,
        "images": [_b64_image(image_path)],
        "stream": False,
    }
    r = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload, timeout=300)
    r.raise_for_status()
    j = r.json()
    return j.get("response", "")


def ollama_embed(text: str) -> List[float]:
    """embeddinggemma로 텍스트 임베딩 (Ollama /api/embed)"""
    payload = {
        "model": EMBED_MODEL,
        "input": text,
    }
    r = requests.post(f"{OLLAMA_HOST}/api/embed", json=payload, timeout=120)
    r.raise_for_status()
    j = r.json()
    embs = j.get("embeddings") or []
    if not embs or not isinstance(embs, list) or not embs[0]:
        raise RuntimeError(f"Empty embeddings from Ollama: {j}")
    return embs[0]


def _safe_parse_amount_krw(text: str) -> Optional[float]:
    """영수증 텍스트에서 KRW 금액 파싱 (간단 버전)"""
    m = re.findall(r"([0-9][0-9,]{2,})\s*원", text)
    if not m:
        return None
    raw = m[-1].replace(",", "")
    try:
        return float(raw)
    except:
        return None


def make_receipt_model(dim: int) -> None:
    """LanceDB 스키마 생성 (LanceModel + Vector 패턴)"""

    class Receipt(LanceModel):
        id: str
        text: str
        vector: Vector(dim=dim)
        image_path: str
        source: str
        total_amount: Optional[float]
        created_at: str

    return Receipt


@dataclass
class LanceHybridWarden:
    """LanceDB 하이브리드 검색 관리자"""

    db_uri: str = LANCEDB_URI
    table_name: str = LANCEDB_TABLE

    def __post_init__(self) -> None:
        Path(self.db_uri).mkdir(parents=True, exist_ok=True)
        self.db = lancedb.connect(self.db_uri)
        self.table = None

    def _get_or_create_table(self, dim: int) -> None:
        """테이블 생성/로딩 (LanceDB 스키마 적용)"""
        if self.table is not None:
            return self.table

        names = set(self.db.table_names())
        if self.table_name in names:
            self.table = self.db.open_table(self.table_name)
            return self.table

        Receipt = make_receipt_model(dim)
        self.table = self.db.create_table(self.table_name, schema=Receipt, mode="create")

        # FTS 인덱스 (하이브리드용)
        try:
            self.table.create_fts_index("text")
        except Exception as e:
            raise RuntimeError(
                f"FTS 인덱스 생성 실패. 환경에 따라 FTS 의존성이 필요할 수 있습니다.\n원인: {e}"
            )

        return self.table

    def ingest_receipt(self, image_path: str) -> Dict[str, Any]:
        """영수증 이미지 ingest (qwen3-vl + embeddinggemma)"""
        img = Path(image_path).expanduser().resolve()
        if not img.exists():
            raise FileNotFoundError(str(img))

        # 1. qwen3-vl로 OCR + 구조화
        prompt = "영수증에서 가게이름, 날짜, 총액을 최대한 정확히 텍스트로 정리해줘."
        extracted = ollama_generate_with_image(prompt, img)

        # 2. embeddinggemma로 벡터화
        emb = ollama_embed(extracted)
        dim = len(emb)

        # 3. LanceDB 저장
        table = self._get_or_create_table(dim)

        total_amount = _safe_parse_amount_krw(extracted)
        now_iso = datetime.now().isoformat()

        row = {
            "id": f"receipt_{img.stem}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "text": extracted,
            "vector": emb,
            "image_path": str(img),
            "source": "receipt",
            "total_amount": total_amount,
            "created_at": now_iso,
        }
        table.add([row])
        return row

    def hybrid_search(
        self,
        query_text: str,
        k: int = 5,
        min_amount: Optional[float] = None,
        exclude_keywords: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """하이브리드 검색 (LanceDB RRFReranker 적용)"""
        if self.table is None:
            raise RuntimeError(
                "테이블이 아직 없습니다. 먼저 ingest_receipt()로 1건 이상 넣어주세요."
            )

        # 1. 쿼리 벡터화
        qvec = ollama_embed(query_text)

        # 2. 하이브리드 검색 (문서 기준 패턴)
        q = (
            self.table.search(query_type="hybrid")
            .vector(qvec)
            .text(query_text)
            .rerank(RRFReranker())  # RRFReranker 객체 사용
        )

        rows = q.limit(k * 3).to_list()

        # 3. Python 후처리 필터링
        out = []
        for r in rows:
            t = r.get("text") or ""
            amt = r.get("total_amount")

            if min_amount is not None and (amt is None or amt < min_amount):
                continue
            if exclude_keywords:
                if any(kw in t for kw in exclude_keywords):
                    continue

            out.append(
                {
                    "id": r.get("id"),
                    "preview": (t[:120] + "...") if len(t) > 120 else t,
                    "amount": amt,
                    "image_path": r.get("image_path"),
                    "score": r.get("_score") or r.get("_distance"),
                    "created_at": r.get("created_at"),
                }
            )
            if len(out) >= k:
                break

        return out


if __name__ == "__main__":
    import sys

    # CLI 인터페이스
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""

    warden = LanceHybridWarden()

    if cmd == "ingest":
        if len(sys.argv) < 3:
            print("Usage: python scripts/lance_hybrid_qwen3.py ingest /path/to/receipt.jpg")
            sys.exit(1)
        path = sys.argv[2]
        print("🔍 영수증 분석 중...")
        row = warden.ingest_receipt(path)
        print("✅ Ingest 완료:")
        print(json.dumps(row, ensure_ascii=False, indent=2))

    elif cmd == "search":
        if len(sys.argv) < 3:
            print('Usage: python scripts/lance_hybrid_qwen3.py search "비싼 커피" 50000 스타벅스')
            sys.exit(1)
        query = sys.argv[2]
        min_amt = float(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] != "None" else None
        excl = sys.argv[4:] if len(sys.argv) > 4 else None

        print(f"🔍 '{query}' 검색 중...")
        results = warden.hybrid_search(
            query_text=query, k=5, min_amount=min_amt, exclude_keywords=excl
        )
        print("✅ 검색 결과:")
        print(json.dumps(results, ensure_ascii=False, indent=2))

    else:
        print("LanceDB + qwen3-vl 하이브리드 검색 도구")
        print("")
        print("사용법:")
        print("  python scripts/lance_hybrid_qwen3.py ingest /path/to/receipt.jpg")
        print('  python scripts/lance_hybrid_qwen3.py search "비싼 커피" 50000 스타벅스')
        print("")
        print("환경변수:")
        print(f"  OLLAMA_HOST={OLLAMA_HOST}")
        print(f"  VISION_MODEL={VISION_MODEL}")
        print(f"  EMBED_MODEL={EMBED_MODEL}")
        print(f"  LANCEDB_URI={LANCEDB_URI}")
        print(f"  LANCEDB_TABLE={LANCEDB_TABLE}")
