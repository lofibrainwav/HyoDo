from __future__ import annotations

import json
import time
from importlib.util import find_spec
from typing import TYPE_CHECKING, Any, TypedDict, cast

try:
    import autogen
except ImportError:
    autogen = None

try:
    import crewai
except ImportError:
    crewai = None

try:
    import langgraph
    from langgraph.graph import END, StateGraph
except ImportError:
    langgraph = None
    StateGraph = None
    END = None

from fastapi import APIRouter
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from AFO.utils.metrics import sse_open_connections

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

# Optional SSE import
try:
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False


router = APIRouter(prefix="/chancellor", tags=["chancellor"])


class ChancellorRequest(BaseModel):
    input: str
    engine: str | None = None


def _sse(event: str, data_obj: Any) -> bytes:
    return (f"event: {event}\ndata: {json.dumps(data_obj, ensure_ascii=False)}\n\n").encode()


async def _stream_echo(text: str) -> AsyncIterator[bytes]:
    yield _sse("start", {"engine": "echo"})
    for i, ch in enumerate(text):
        yield _sse("token", {"i": i, "t": ch})
    yield _sse("done", {"ok": True})


async def _stream_langgraph(text: str) -> AsyncIterator[bytes]:
    try:
        pass
        yield _sse("info", {"engine": "langgraph", "status": "installed"})
    except Exception:
        yield _sse("info", {"engine": "langgraph", "status": "missing"})
        async for b in _stream_echo(text):
            yield b
        return
    async for b in _stream_echo(text):
        yield b


async def _stream_crewai(text: str) -> AsyncIterator[bytes]:
    try:
        pass
        yield _sse("info", {"engine": "crewai", "status": "installed"})
    except Exception:
        yield _sse("info", {"engine": "crewai", "status": "missing"})
        async for b in _stream_echo(text):
            yield b
        return
    async for b in _stream_echo(text):
        yield b


async def _stream_autogen(text: str) -> AsyncIterator[bytes]:
    try:
        pass
        yield _sse("info", {"engine": "autogen", "status": "installed"})
    except Exception:
        yield _sse("info", {"engine": "autogen", "status": "missing"})
        async for b in _stream_echo(text):
            yield b
        return
    async for b in _stream_echo(text):
        yield b


@router.get("/ping")
async def chancellor_ping():
    """Service Health Check (眞 - Truth Certified)"""
    return {"ok": True, "status": "AFO Kingdom Active"}


# 캐시된 라이브러리 설치 상태 (성능 최적화)
_cached_engine_status: dict[str, bool] | None = None
_cache_timestamp: float = 0
_CACHE_TTL = 300  # 5분 캐시


def _get_cached_engine_status() -> dict[str, bool]:
    """캐시된 엔진 설치 상태 반환 (성능 최적화)"""
    global _cached_engine_status, _cache_timestamp

    current_time = time.time()

    # 캐시가 유효하면 반환
    if _cached_engine_status and (current_time - _cache_timestamp) < _CACHE_TTL:
        return _cached_engine_status.copy()

    # 캐시 만료 또는 없음 - 새로 확인
    installed = {}

    # 빠른 import 시도 (순서 최적화: 가장 가벼운 것부터)
    engines_to_check = [
        ("langgraph", "langgraph"),
        ("crewai", "crewai"),
        ("autogen", "autogen"),  # autogen_agentchat는 fallback으로 확인
    ]

    for engine_name, module_name in engines_to_check:
        try:
            __import__(module_name)
            installed[engine_name] = True
        except ImportError:
            # autogen의 경우 autogen_agentchat도 확인
            if engine_name == "autogen":
                try:
                    __import__("autogen_agentchat")
                    installed[engine_name] = True
                except ImportError:
                    installed[engine_name] = False
            else:
                installed[engine_name] = False

    # 캐시 업데이트
    _cached_engine_status = installed
    _cache_timestamp = current_time

    return installed.copy()


@router.get("/engines")
async def chancellor_engines():
    """Chancellor AI 엔진 설치 상태 확인 (캐시 최적화)

    Trinity Score: 眞 (Truth) - 정확한 라이브러리 상태
    성능 최적화: 5분 캐시 + 빠른 import 순서
    """
    return {"installed": _get_cached_engine_status()}


@router.post("/stream")
async def chancellor_stream(req: ChancellorRequest):
    engine = (req.engine or "langgraph").lower()
    if engine == "langgraph":
        gen = _stream_langgraph(req.input)
    elif engine == "crewai":
        gen = _stream_crewai(req.input)
    elif engine == "autogen":
        gen = _stream_autogen(req.input)
    else:
        gen = _stream_echo(req.input)

    if METRICS_AVAILABLE:
        sse_open_connections.inc()

    async def _gen_wrapper():
        try:
            async for item in gen:
                yield item
        finally:
            if METRICS_AVAILABLE:
                sse_open_connections.dec()

    return StreamingResponse(_gen_wrapper(), media_type="text/event-stream")


@router.post("/stream_v2")
async def chancellor_stream_v2(req: ChancellorRequest):
    class _LGState(TypedDict, total=False):
        input: str
        tokens: list[str]

    def _lg_tokenize(state: _LGState) -> _LGState:
        s = state.get("input") or ""
        return {"tokens": list(s)}

    async def _stream_langgraph_real(text: str):
        try:
            pass
        except Exception:
            yield _sse("info", {"engine": "langgraph_real", "status": "missing"})
            async for b in _stream_echo(text):
                yield b
            return

        yield _sse("info", {"engine": "langgraph_real", "status": "installed"})

        g = StateGraph(_LGState)
        g.add_node("tokenize", _lg_tokenize)
        g.set_entry_point("tokenize")
        g.add_edge("tokenize", END)
        compiled = g.compile()

        out = await compiled.ainvoke(cast("Any", {"input": text}))
        tokens = out.get("tokens") or []

        yield _sse("start", {"engine": "langgraph_real"})
        for i, ch in enumerate(tokens):
            yield _sse("token", {"i": i, "t": ch})
        yield _sse("done", {"ok": True})

    engine = (req.engine or "langgraph_real").lower()
    if engine in ("langgraph_real", "langgraph"):
        gen = _stream_langgraph_real(req.input)
    else:
        gen = _stream_echo(req.input)

    if METRICS_AVAILABLE:
        sse_open_connections.inc()

    async def _gen_wrapper():
        try:
            async for item in gen:
                yield item
        finally:
            if METRICS_AVAILABLE:
                sse_open_connections.dec()

    return StreamingResponse(_gen_wrapper(), media_type="text/event-stream")


def _is_installed(mod: str) -> bool:
    return find_spec(mod) is not None


@router.post("/stream_v3")
async def chancellor_stream_v3(req: ChancellorRequest):
    async def _stream_langgraph_real_v3(text: str):
        yield _sse(
            "info",
            {"engine": "langgraph_real", "installed": _is_installed("langgraph")},
        )
        try:
            pass

            class _LGState(TypedDict, total=False):
                input: str
                tokens: list[str]

            def _lg_tokenize(state: _LGState) -> _LGState:
                return {"tokens": list(state.get("input") or "")}

            g = StateGraph(_LGState)
            g.add_node("tokenize", _lg_tokenize)
            g.set_entry_point("tokenize")
            g.add_edge("tokenize", END)
            compiled = g.compile()

            yield _sse("start", {"engine": "langgraph_real"})
            out = await compiled.ainvoke(cast("Any", {"input": text}))
            tokens = out.get("tokens") or []
            for i, ch in enumerate(tokens):
                yield _sse("token", {"i": i, "t": ch})
            yield _sse("done", {"ok": True})
        except Exception as e:
            yield _sse("error", {"engine": "langgraph_real", "error": str(e)})
            async for b in _stream_echo(text):
                yield b

    engine = (req.engine or "langgraph_real").lower()
    installed = {
        "langgraph": _is_installed("langgraph"),
        "crewai": _is_installed("crewai"),
        "autogen": _is_installed("autogen_agentchat") or _is_installed("autogen"),
    }
    yield_headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}

    if engine in ("langgraph_real", "langgraph"):
        gen = _stream_langgraph_real_v3(req.input)
    elif engine == "crewai":

        async def _gen():
            yield _sse("info", {"engine": "crewai", "installed": installed["crewai"]})
            async for b in _stream_echo(req.input):
                yield b

        gen = _gen()
    elif engine == "autogen":

        async def _gen():
            yield _sse("info", {"engine": "autogen", "installed": installed["autogen"]})
            async for b in _stream_echo(req.input):
                yield b

        gen = _gen()
    else:
        gen = _stream_echo(req.input)

    if METRICS_AVAILABLE:
        sse_open_connections.inc()

    async def _gen_wrapper():
        try:
            async for item in gen:
                yield item
        finally:
            if METRICS_AVAILABLE:
                sse_open_connections.dec()

    return StreamingResponse(_gen_wrapper(), media_type="text/event-stream", headers=yield_headers)
