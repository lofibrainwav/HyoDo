from __future__ import annotations

import json
import os
import time
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HealthSnapshot:
    ok: bool
    details: dict[str, Any]


def _http_json(url: str, timeout: float = 2.5) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read().decode("utf-8", errors="ignore")
    try:
        return json.loads(body)
    except Exception:
        return {"raw": body}


def health_snapshot() -> HealthSnapshot:
    """
    표준 라이브러리만 사용하여, 서비스 health endpoint가 있으면 조회합니다.
    (의존성 추가 없이 health 모듈을 '정상 패키지'로 복구하기 위한 최소 구현)
    """
    now = time.time()
    targets = {
        "soul_engine": os.getenv("AFO_SOUL_ENGINE_URL", "http://localhost:8010/health"),
        "wallet_service": os.getenv("AFO_WALLET_URL", "http://localhost:8011/health"),
        "rag_service": os.getenv("AFO_RAG_URL", "http://localhost:8009/health"),
    }

    details: dict[str, Any] = {"ts": now, "targets": targets, "results": {}}
    ok = True

    for name, url in targets.items():
        try:
            details["results"][name] = _http_json(url)
        except Exception as e:
            ok = False
            details["results"][name] = {"error": str(e), "url": url}

    return HealthSnapshot(ok=ok, details=details)
