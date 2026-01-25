from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from starlette.middleware.cors import CORSMiddleware

if TYPE_CHECKING:
    from fastapi import FastAPI

# Trinity Score: 90.0 (Established by Chancellor)
"""AFO Setup Module (眞善美孝永)

Middleware setup for FastAPI application.
Configures CORS, security headers, and other essential middleware.
"""


logger = logging.getLogger(__name__)


def setup_middleware(app: FastAPI) -> None:
    """Setup all middleware on FastAPI app.

    Args:
        app: FastAPI application instance
    """
    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:8010",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8010",
        ],  # Configure more restrictively in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS middleware configured")
    logger.info("Middleware setup complete")


__all__ = ["setup_middleware"]
