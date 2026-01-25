from __future__ import annotations

from typing import Any

from afo_soul_engine.routers.auth import *  # noqa: F403 # type: ignore


class _Missing:
    def __init__(self, name: str) -> None:
        self._name = name

    def __call__(self, *a: Any, **k: Any) -> Any:
        raise NotImplementedError(f"browser_auth stub: {self._name}")

    def __getattr__(self, attr: str) -> Any:
        raise NotImplementedError(f"browser_auth stub: {self._name}.{attr}")


try:
    pass  # Placeholder
except Exception:
    pass


def __getattr__(name: str) -> Any:
    return _Missing(name)
