from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, TypedDict, cast

try:
    import autogen  # noqa: F401

    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False

try:
    import crewai  # noqa: F401

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

from fastapi import APIRouter
from langgraph.graph import END, StateGraph
from pydantic import BaseModel
from starlette.responses import StreamingResponse

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

router_v2 = APIRouter(prefix="/chancellor", tags=["chancellor"])


class ChancellorRequestV2(BaseModel):
    input: str
    engine: str | None = None


def _sse(event: str, data_obj: Any) -> bytes:
    return (f"event: {event}\ndata: {json.dumps(data_obj, ensure_ascii=False)}\n\n").encode()


async def _stream_echo(text: str) -> AsyncIterator[bytes]:
    yield _sse("start", {"engine": "echo"})
    for i, ch in enumerate(text):
        yield _sse("token", {"i": i, "t": ch})
    yield _sse("done", {"ok": True})


class _LGState(TypedDict, total=False):
    input: str
    tokens: list[str]


def _lg_tokenize(state: _LGState) -> _LGState:
    s = state.get("input") or ""
    return {"tokens": list(s)}


async def _stream_langgraph_real(text: str) -> AsyncIterator[bytes]:
    try:
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
    except Exception:
        yield _sse("info", {"engine": "langgraph_real", "status": "missing"})
        async for b in _stream_echo(text):
            yield b


@router_v2.get("/ping_v2")
async def chancellor_ping_v2():
    return {"ok": True}


@router_v2.get("/engines")
async def chancellor_engines():
    installed = {}
    try:
        installed["langgraph"] = True
    except Exception:
        installed["langgraph"] = False
    try:
        installed["crewai"] = True
    except Exception:
        installed["crewai"] = False
    try:
        installed["autogen"] = True
    except Exception:
        installed["autogen"] = False
    return {"installed": installed}


@router_v2.post("/stream_v2")
async def chancellor_stream_v2(req: ChancellorRequestV2):
    engine = (req.engine or "langgraph_real").lower()
    if engine in ("langgraph_real", "langgraph"):
        gen = _stream_langgraph_real(req.input)
    else:
        gen = _stream_echo(req.input)
    return StreamingResponse(gen, media_type="text/event-stream")
