import hashlib
import json
import os
import time
from typing import Any

try:
    import redis
except Exception:
    redis: Any = None

# RAG Cache SSOT Config
RAG_CACHE_CONFIG = {
    "ttl_sec": 3600,  # 기본 TTL (환경변수로 override 가능)
    "prefix": "afo:rag:v1:",
    "version_in_key": True,  # 캐시 키에 버전 정보 포함
}


class _MemTTL:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, str]] = {}

    def get(self, k: str) -> str | None:
        v = self._store.get(k)
        if not v:
            return None
        exp, data = v
        if exp < time.time():
            self._store.pop(k, None)
            return None
        return data

    def setex(self, k: str, ttl: int, data: str) -> None:
        self._store[k] = (time.time() + ttl, data)


_mem = _MemTTL()


def _enabled() -> bool:
    return os.getenv("AFO_RAG_CACHE_ENABLED", "0") == "1"


def _ttl() -> int:
    try:
        return int(os.getenv("AFO_RAG_CACHE_TTL_SEC", "3600"))
    except Exception:
        return 3600


def _prefix() -> str:
    return os.getenv("AFO_RAG_CACHE_PREFIX", "afo:rag:v1:")


def _redis_client() -> None:
    # Use Any cast to avoid MyPy unreachable detection
    r: Any = redis
    if r is None:
        return None
    host = os.getenv("AFO_REDIS_HOST", "localhost")
    port = int(os.getenv("AFO_REDIS_PORT", "6379"))
    db = int(os.getenv("AFO_REDIS_DB", "0"))
    return redis.Redis(host=host, port=port, db=db)


def _key(query: str, extra: dict[str, Any] | None = None) -> str:
    payload: dict[str, Any] = {"q": query}
    if extra:
        payload["x"] = extra
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return _prefix() + hashlib.sha256(raw).hexdigest()


def cache_get(query: str, extra: dict[str, Any] | None = None) -> str | None:
    if not _enabled():
        return None
    k = _key(query, extra)
    try:
        rc = _redis_client()
        if rc is not None:
            v = rc.get(k)
            if v is not None:
                return v.decode("utf-8") if isinstance(v, bytes) else str(v)
            return None
        return _mem.get(k)
    except Exception:
        return None


def cache_set(query: str, answer: str, extra: dict[str, Any] | None = None) -> None:
    if not _enabled():
        return
    k = _key(query, extra)
    ttl = _ttl()
    try:
        rc = _redis_client()
        if rc is not None:
            rc.setex(k, ttl, answer.encode("utf-8"))
            return
        _mem.setex(k, ttl, answer)
    except Exception:
        return
