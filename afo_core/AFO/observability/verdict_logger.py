from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from AFO.observability.verdict_event import VerdictEvent

# Trinity Score: 90.0 (Established by Chancellor)


class RedisLike(Protocol):
    def set(self, name: str, value: str, ex: int | None = None) -> Any: ...
    def publish(self, channel: str, message: str) -> Any: ...


class VerdictLogger:
    def __init__(
        self,
        redis: RedisLike | None,
        *,
        checkpoint_ttl_seconds: int = 60 * 60 * 24 * 7,
        sse_channel: str = "afo:verdicts",  # SSE 스트리밍용 단일 채널
        sse_channel_prefix: str = "sse:chancellor_verdict:",  # 기존 호환성 유지
        checkpoint_prefix: str = "checkpoint:",
    ) -> None:
        self._redis = redis
        self._ttl = checkpoint_ttl_seconds
        self._sse_channel = sse_channel  # SSE 스트리밍용 단일 채널
        self._sse_prefix = sse_channel_prefix  # 기존 호환성 유지
        self._ckpt_prefix = checkpoint_prefix

    def checkpoint_key(self, trace_id: str, graph_node_id: str, step: int) -> str:
        return f"{self._ckpt_prefix}{trace_id}:{graph_node_id}:{step}"

    def sse_channel(self, trace_id: str) -> str:
        return f"{self._sse_prefix}{trace_id}"

    def emit(self, event: VerdictEvent) -> dict[str, Any]:
        payload = event.to_json()
        if self._redis is not None:
            ck = self.checkpoint_key(event.trace_id, event.graph_node_id, event.step)
            self._redis.set(ck, payload, ex=self._ttl)
            # SSE 스트리밍용 단일 채널로 publish (헌법 v1.0 준수)
            self._redis.publish(self._sse_channel, payload)
        return event.to_dict()
