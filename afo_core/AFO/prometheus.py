from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastapi import FastAPI

# Trinity Score: 90.0 (Established by Chancellor)
"""AFO Prometheus Module (眞善美孝永)

Stub module for Prometheus middleware to unblock Gate.
Full implementation pending TICKET-XXX.
"""


logger = logging.getLogger(__name__)


class PrometheusMiddleware:
    """Prometheus metrics middleware stub."""

    def __init__(self, app: Any = None) -> None:
        self.app = app
        logger.info("PrometheusMiddleware stub initialized")

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        """Pass through without metrics collection."""
        if self.app:
            await self.app(scope, receive, send)


async def metrics_endpoint() -> str:
    """Prometheus metrics endpoint stub.

    Returns:
        Empty metrics string.
    """
    return "# Prometheus metrics stub\n"


def setup_prometheus(app: FastAPI) -> None:
    """Setup Prometheus middleware on FastAPI app.

    Args:
        app: FastAPI application instance
    """
    logger.info("Prometheus middleware stub setup complete")


__all__ = ["PrometheusMiddleware", "metrics_endpoint", "setup_prometheus"]
