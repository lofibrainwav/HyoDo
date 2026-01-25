"""
AFO Scripts Common Module
공통 유틸리티 함수 모음

Modules:
- discord_webhook: Discord 웹훅 알림
- logging_setup: 표준화된 로깅 설정
- file_utils: 파일/경로 유틸리티
"""

from __future__ import annotations

from .discord_webhook import send_discord_alert, send_simple_alert
from .file_utils import ensure_dir, get_repo_root, safe_read_json, safe_write_json
from .logging_setup import get_script_logger, setup_script_logging

__all__ = [
    # Discord
    "send_discord_alert",
    "send_simple_alert",
    # Logging
    "setup_script_logging",
    "get_script_logger",
    # File utils
    "get_repo_root",
    "ensure_dir",
    "safe_read_json",
    "safe_write_json",
]
