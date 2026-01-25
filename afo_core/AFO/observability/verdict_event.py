from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, TypedDict

from AFO.constitution.constitution_v1_0 import TRINITY_WEIGHTS

if TYPE_CHECKING:
    from collections.abc import Mapping

# Trinity Score: 90.0 (Established by Chancellor)


# 🔐 SSOT 해시 스탬프: 변경 감지용 (SHA256 12자리)
WEIGHTS_HASH = hashlib.sha256(str(sorted(TRINITY_WEIGHTS.items())).encode()).hexdigest()[:12]


class VerdictFlags(TypedDict):
    dry_run: bool
    residual_doubt: bool


class Decision(str, Enum):
    """Chancellor Graph 판결 결정 (SSOT)

    - AUTO_RUN: Trinity >= 90 AND Risk <= 10 → 자동 실행
    - ASK_COMMANDER: 중간 신뢰도 → 사용자 확인 필요
    - BLOCK: 낮은 신뢰도 → 실행 차단
    """

    AUTO_RUN = "AUTO_RUN"
    ASK_COMMANDER = "ASK_COMMANDER"
    BLOCK = "BLOCK"

    # Legacy alias (하위 호환성)
    ASK = "ASK_COMMANDER"


@dataclass(frozen=True)
class VerdictEvent:
    trace_id: str
    graph_node_id: str
    step: int
    decision: Decision
    rule_id: str
    trinity_score: float
    risk_score: float
    flags: VerdictFlags
    timestamp: str
    extra: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "trace_id": self.trace_id,
            "graph_node_id": self.graph_node_id,
            "step": self.step,
            "decision": self.decision.value
            if isinstance(self.decision, Decision)
            else self.decision,
            "rule_id": self.rule_id,
            "trinity_score": round(float(self.trinity_score), 2),
            "risk_score": float(self.risk_score),
            "flags": dict(self.flags),
            "timestamp": self.timestamp,
            # 🏛️ SSOT 스탬프: weights_version + weights_hash (관찰 고정 모드)
            "weights_version": "constitution/v1.0",
            "weights_hash": WEIGHTS_HASH,
        }
        if self.extra:
            payload["extra"] = dict(self.extra)
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def now_iso() -> str:
        return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
