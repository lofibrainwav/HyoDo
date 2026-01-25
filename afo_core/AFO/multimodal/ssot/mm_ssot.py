from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

from AFO.ssot_chain import current_env_hash as _ceh

CHAIN_PATH = Path("artifacts/mipro_runs/ssot_chain.jsonl")
MM_BOOT_PATH = Path("artifacts/mipro_runs/mm_boot_ssot.jsonl")


def _append_jsonl(path: Path, entry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _fallback_env_hash() -> str:
    keys = [
        "AFO_DRY_RUN",
        "AFO_DRY_RUN_DEFAULT",
        "AFO_ANTIGRAVITY_EXECUTION_ENABLED",
        "OLLAMA_HOST",
        "OLLAMA_BASE_URL",
    ]
    payload = {k: os.getenv(k, "") for k in keys}
    s = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def current_env_hash() -> str:
    try:
        return _ceh()
    except Exception:
        return _fallback_env_hash()


def record_mm_boot_ssot(envelope: dict[str, Any]) -> None:
    entry = {
        "ts": time.time(),
        "status": "mm_boot",
        "pid": os.getpid(),
        "ppid": os.getppid(),
        "env_hash": current_env_hash(),
        "trace_id": envelope.get("trace_id"),
        "has_images": bool(envelope.get("image_paths") or []),
        "input_hash": envelope.get("input_hash"),
    }
    _append_jsonl(MM_BOOT_PATH, entry)


def record_mm_router_decision_ssot(
    *,
    trace_id: str | None,
    input_hash: str,
    has_images: bool,
    chosen_path: str,
    reason: str,
) -> None:
    entry = {
        "ts": time.time(),
        "status": "mm_router_decision",
        "env_hash": current_env_hash(),
        "trace_id": trace_id,
        "input_hash": input_hash,
        "has_images": has_images,
        "chosen_path": chosen_path,
        "reason": reason,
        "error": None,
    }
    _append_jsonl(CHAIN_PATH, entry)
