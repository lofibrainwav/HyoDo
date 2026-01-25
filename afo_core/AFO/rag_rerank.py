import asyncio
import os
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class RerankResult:
    ok: bool
    reason: str
    latency_ms: float


def _enabled() -> bool:
    return os.getenv("AFO_RAG_RERANK_ENABLED", "0") == "1"


def _top_k() -> int:
    try:
        return int(os.getenv("AFO_RAG_RERANK_TOP_K", "5"))
    except Exception:
        return 5


def _timeout_ms() -> int:
    try:
        return int(os.getenv("AFO_RAG_RERANK_TIMEOUT_MS", "250"))
    except Exception:
        return 250


def _model_name() -> str:
    return os.getenv("AFO_RAG_RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")


def _doc_text(doc: Any) -> str:
    if isinstance(doc, str):
        return doc
    if isinstance(doc, dict) and "text" in doc:
        return str(doc["text"])
    if hasattr(doc, "page_content"):
        return str(doc.page_content)
    if hasattr(doc, "text"):
        return str(doc.text)
    return str(doc)


async def rerank(query: str, docs: list[Any]) -> tuple[list[Any], RerankResult]:
    if not _enabled():
        return docs[: _top_k()], RerankResult(ok=True, reason="disabled", latency_ms=0.0)

    start = time.time()

    async def _run() -> list[Any]:
        try:
            # Lazy import: enabled 체크 후에만 import (cold start 최적화)
            from sentence_transformers import CrossEncoder
        except Exception:
            return docs[: _top_k()]

        def _predict_sync() -> list[Any]:
            reranker = CrossEncoder(_model_name(), device=os.getenv("AFO_RAG_RERANK_DEVICE", "cpu"))
            pairs = [[query, _doc_text(d)] for d in docs]
            scores = reranker.predict(pairs)
            ranked = [d for _, d in sorted(zip(scores, docs), key=lambda x: x[0], reverse=True)]
            return ranked[: _top_k()]

        return await asyncio.to_thread(_predict_sync)

    try:
        # Timeout 강제: 별도 executor로 감싸서 시간 초과 시 즉시 fail_open
        import concurrent.futures

        def _run_with_timeout() -> list[Any]:
            # 별도 스레드에서 실행하여 timeout 강제
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(asyncio.run, _run())
                try:
                    return future.result(timeout=_timeout_ms() / 1000.0)
                except concurrent.futures.TimeoutError:
                    future.cancel()
                    raise TimeoutError("rerank timeout")

        ranked = await asyncio.to_thread(_run_with_timeout)
        return ranked, RerankResult(ok=True, reason="ok", latency_ms=(time.time() - start) * 1000.0)
    except Exception:
        return docs[: _top_k()], RerankResult(
            ok=False, reason="fail_open", latency_ms=(time.time() - start) * 1000.0
        )
