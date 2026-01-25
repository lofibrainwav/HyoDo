from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

# Trinity Score: 90.0 (Established by Chancellor)


class RedisDownMode(str, Enum):
    FAIL_OPEN = "FAIL_OPEN"
    FAIL_CLOSED = "FAIL_CLOSED"
    HYBRID = "HYBRID"


def _split_prefixes(raw: str) -> list[str]:
    return [p.strip() for p in raw.split(",") if p.strip()]


@dataclass(frozen=True)
class RedisDownPolicy:
    mode: RedisDownMode
    sensitive_prefixes: tuple[str, ...]
    exempt_prefixes: tuple[str, ...]
    fail_closed_status: int
    warning_header_name: str
    cb_state_header_name: str

    @staticmethod
    def from_env() -> RedisDownPolicy:
        mode_raw = os.getenv("AFO_REDIS_DOWN_POLICY", "HYBRID").strip().upper()
        try:
            mode = RedisDownMode(mode_raw)
        except ValueError:
            mode = RedisDownMode.HYBRID

        sensitive = tuple(
            _split_prefixes(
                os.getenv(
                    "AFO_REDIS_DOWN_SENSITIVE_PREFIXES",
                    "/auth,/billing,/wallet,/admin",
                )
            )
        )
        exempt = tuple(
            _split_prefixes(
                os.getenv(
                    "AFO_REDIS_DOWN_EXEMPT_PREFIXES",
                    "/health,/metrics,/openapi.json,/docs",
                )
            )
        )

        fail_closed_status = int(os.getenv("AFO_REDIS_DOWN_FAIL_CLOSED_STATUS", "503").strip())
        warning_header_name = os.getenv("AFO_REDIS_DOWN_WARNING_HEADER", "X-AFO-Redis-Down").strip()
        cb_state_header_name = os.getenv(
            "AFO_REDIS_CB_STATE_HEADER", "X-AFO-Redis-CB-State"
        ).strip()

        return RedisDownPolicy(
            mode=mode,
            sensitive_prefixes=sensitive,
            exempt_prefixes=exempt,
            fail_closed_status=fail_closed_status,
            warning_header_name=warning_header_name,
            cb_state_header_name=cb_state_header_name,
        )

    def _starts_with_any(self, path: str, prefixes: Iterable[str]) -> bool:
        return any(p and path.startswith(p) for p in prefixes)

    def is_exempt(self, path: str) -> bool:
        return self._starts_with_any(path, self.exempt_prefixes)

    def should_fail_closed(self, path: str) -> bool:
        if self.mode == RedisDownMode.FAIL_CLOSED:
            return True
        if self.mode == RedisDownMode.FAIL_OPEN:
            return False
        return self._starts_with_any(path, self.sensitive_prefixes)
