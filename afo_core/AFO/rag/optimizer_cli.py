from __future__ import annotations

import argparse
import inspect
import json
import os
from pathlib import Path
from typing import Any

import dspy

from AFO.config.antigravity import antigravity
from AFO.config.local_dspy import configure_dspy_local_lm, configure_local_dspy
from AFO.evolution.dspy_optimizer import _pick_field, compile_mipro
from AFO.rag.dspy_module import AfoRagProgram
from AFO.rag.multimodal_rag_engine import get_multimodal_engine

try:
    import dspy
except ImportError:
    dspy = None  # type: ignore[assignment]


def _load_jsonl(path: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def _ensure_parent(p: str) -> None:
    Path(p).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def _maybe_configure_lm() -> None:
    """Configure DSPy LM: Ollama (local) first, OpenAI as fallback."""
    if dspy is None:
        raise RuntimeError("DSPy is not installed.")

    # 이미 앱 런타임에서 설정되어 있으면 그대로 사용
    if getattr(dspy.settings, "lm", None):
        return

    # 1순위: 로컬 Ollama 사용 (OpenAI 의존성 제거)
    try:
        configure_dspy_local_lm()
        return
    except Exception as e:
        print(f"[AFO] Local Ollama config failed: {e}")

    # 2순위: OpenAI API (fallback)
    if os.getenv("OPENAI_API_KEY"):
        model = os.getenv("DSPY_OPENAI_MODEL", "gpt-4o-mini")
        lm = dspy.LM(f"openai/{model}")
        dspy.configure(lm=lm)
        print(f"[AFO] Using OpenAI fallback: {model}")
        return

    raise RuntimeError(
        "DSPy LM is not configured. Either:\n"
        "  1. Start Ollama (ollama serve) with a model (deepseek-r1:14b)\n"
        "  2. Set OPENAI_API_KEY environment variable\n"
        "  3. Configure dspy.settings.configure(lm=...) in your runtime."
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", required=True, help="Path to JSONL train set.")
    ap.add_argument("--auto", default="light", choices=["light", "medium", "heavy"])
    ap.add_argument("--out", default="artifacts/dspy/RAG_OPTIMIZED.json", help="Output save path.")
    ap.add_argument("--val-size", type=int, default=20)
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Fail fast (if compile_mipro supports strict).",
    )
    args = ap.parse_args()

    if dspy is None:
        raise RuntimeError("DSPy is not installed.")

    # OLLAMA/Local DSPy 설정 우선
    if not antigravity.DRY_RUN:
        configure_local_dspy()
    else:
        print("[DRY_RUN] Skipping LM configuration.")

    _ensure_parent(args.out)

    rows = _load_jsonl(args.train)

    # Build DSPy Examples
    examples = []
    for r in rows:
        q = _pick_field(r, ["question", "query", "input", "prompt"])
        gt = _pick_field(r, ["ground_truth", "answer", "output", "expected"])
        if not q or not gt:
            continue
        ex = dspy.Example(question=q, ground_truth=gt).with_inputs("question")
        examples.append(ex)

    if not examples:
        raise RuntimeError("No usable examples found in train set.")

    # Lazy import to avoid heavy side effects unless actually running CLI

    # We import get_multimodal_engine from the core module directly as it seems to be in the root of the package source
    # Adjusted import based on inspected file structure: multimodal_rag_engine.py is in packages/afo-core/
    # If the package 'AFO' maps to 'packages/afo-core', then 'AFO.multimodal_rag_engine' works.
    # However, 'multimodal_rag_engine.py' is NOT inside 'AFO/' directory in 'packages/afo-core/'.
    # It is a sibling of 'AFO/'. This suggests 'afo-core' might be a flat layout.
    # BUT 'packages/afo-core/AFO/' exists.
    # If 'multimodal_rag_engine.py' is in root of 'packages/afo-core', and 'pyproject.toml' makes 'packages/afo-core' the package source?
    # Wait, 'packages/afo-core/afo_soul_engine/' is also there. This looks like a diverse collection.
    # The file 'packages/afo-core/multimodal_rag_engine.py' is likely importable as 'multimodal_rag_engine' if 'packages/afo-core' is in PYTHONPATH.
    # BUT 'AFO' package usually implies 'packages/afo-core/AFO'.
    # Let's try importing from 'AFO' first if possible, assuming some path magic, OR assume 'multimodal_rag_engine' is a top level module.
    # Given the previous context, let's look at how other modules import it.
    # The user instruction used: `from AFO.rag.multimodal_rag_engine import get_multimodal_engine` in the sample CLI code.
    # BUT the user also asked to put `dspy_module.py` in `packages/afo-core/AFO/rag/`.
    # And `multimodal_rag_engine.py` is in `packages/afo-core/`.
    # If `packages/afo-core` is added to python path, then `import multimodal_rag_engine` works.
    # If `packages/afo-core` is the root of the installable package `afo-core`, then `multimodal_rag_engine` is a top level module.
    # But `AFO` is also a directory there.
    # Let's assume for now `multimodal_rag_engine` is available at top level or we might need to adjust.
    # Actually, the user's sample code had `from AFO.rag.multimodal_rag_engine`.
    # This implies the user intends to MOVE it? No, user didn't say move.
    # User said "create TICKET-003 files".
    # I will stick to what seems safe: Import relatively or using what I see.
    # If `multimodal_rag_engine.py` is in `packages/afo-core`, and `AFO` is in `packages/afo-core`, they are siblings.
    # If running as `python -m AFO.rag.optimizer_cli`, `sys.path` usually includes the root.
    # If `packages/afo-core` is in python path, then `import multimodal_rag_engine` is correct.
    # I'll use `from multimodal_rag_engine import get_multimodal_engine` inside the CLI, handling the likelihood it's top-level in this dev environment.
    # get_multimodal_engine is already imported at the top of this file

    program = AfoRagProgram(engine=get_multimodal_engine(), top_k=5)

    # Simple val split (tail)
    valset = None
    if len(examples) > args.val_size:
        valset = examples[-args.val_size :]
        trainset = examples[: -args.val_size]
    else:
        trainset = examples

    # Call compile_mipro with signature-aware kwargs
    sig = inspect.signature(compile_mipro)
    kwargs: dict[str, Any] = {
        "program": program,
        "trainset": trainset,
        "valset": valset,
        "auto": args.auto,
        "save_path": args.out,
    }
    if "strict" in sig.parameters:
        kwargs["strict"] = args.strict

    if antigravity.DRY_RUN:
        # compile_mipro 내부에서 DRY_RUN 처리되지만, CLI에서도 한 번 더 명시
        print("[DRY_RUN] optimizer_cli executing in DRY_RUN mode.")

    compile_mipro(**kwargs)
    print(f"[OK] Saved optimized program to: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
