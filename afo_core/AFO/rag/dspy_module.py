from __future__ import annotations

import logging
from typing import Any

try:
    import dspy
except ImportError:  # pragma: no cover
    dspy = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


def _safe_str(v: Any) -> str:
    try:
        return "" if v is None else str(v)
    except Exception:
        return ""


def _doc_line(doc: Any, idx: int) -> str:
    content = _safe_str(getattr(doc, "content", ""))[:1200]
    ctype = _safe_str(getattr(doc, "content_type", "text"))
    meta = getattr(doc, "metadata", {}) or {}
    path = _safe_str(meta.get("path", ""))
    tag = f"[{idx}] type={ctype}"
    if path:
        tag += f" path={path}"
    return f"{tag}\n{content}".strip()


def build_context(engine: Any, question: str, top_k: int = 5) -> str:
    if not engine:
        return ""
    try:
        docs = engine.search(question, top_k=top_k)
        lines = [_doc_line(d, i + 1) for i, d in enumerate(docs)]
        return "\n\n---\n\n".join([ln for ln in lines if ln])
    except Exception as e:
        logger.warning("build_context failed: %s", str(e))
        return ""


if dspy:

    class AfoRagSignature(dspy.Signature):
        question: str = dspy.InputField(desc="User question.")
        context: str = dspy.InputField(desc="Retrieved context.")
        answer: str = dspy.OutputField(
            desc="Answer grounded in the context. If unsure, say you are unsure."
        )

    class AfoRagProgram(dspy.Module):
        def __init__(self, engine: Any = None, top_k: int = 5) -> None:
            super().__init__()
            self._engine = engine
            self._top_k = top_k
            self._gen = dspy.Predict(AfoRagSignature)

        def forward(self, question: str) -> Any:
            ctx = build_context(self._engine, question, top_k=self._top_k)
            return self._gen(question=question, context=ctx)

else:

    class AfoRagProgram:  # pragma: no cover
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError("DSPy is not installed; cannot construct AfoRagProgram.")
