# Trinity Score: 95.0 (Phase 30 Main Entry Point)
"""Input Server Main Entry Point - Server Launcher"""

import os

import uvicorn

from AFO.config.settings import get_settings

from .core import app


def main() -> None:
    """Main entry point for running the Input Server."""
    # Phase 2-4: settings 사용
    try:
        settings = get_settings()
        port = settings.INPUT_SERVER_PORT
        host = settings.INPUT_SERVER_HOST
    except ImportError:
        port = int(os.getenv("INPUT_SERVER_PORT", "4200"))
        host = os.getenv("INPUT_SERVER_HOST", "127.0.0.1")

    print("=" * 60)
    print("🍽️  AFO Input Server - 胃 (Stomach)")
    print("=" * 60)
    print(f"Port: {port}")
    print(f"Host: {host}")
    print(f"API Wallet URL: {getattr(settings, 'API_WALLET_URL', 'http://localhost:8000')}")
    print("=" * 60)
    print()

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
