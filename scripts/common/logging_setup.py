"""
Logging Setup Module
표준화된 스크립트 로깅 설정

Usage:
    from scripts.common import setup_script_logging, get_script_logger

    # Setup logging for a script
    setup_script_logging("my_script")

    # Get a logger
    logger = get_script_logger("my_script")
    logger.info("Script started")
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Default log directory
DEFAULT_LOG_DIR = "artifacts/run"


def get_repo_root() -> Path:
    """Get the repository root directory"""
    # Try to find repo root by looking for AGENTS.md or .git
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "AGENTS.md").exists() or (parent / ".git").exists():
            return parent
    return Path.cwd()


def setup_script_logging(
    script_name: str,
    log_dir: str | Path | None = None,
    level: int = logging.INFO,
    console_output: bool = True,
    file_output: bool = True,
) -> logging.Logger:
    """표준화된 스크립트 로깅 설정

    Args:
        script_name: 스크립트 이름 (로그 파일명으로 사용)
        log_dir: 로그 디렉토리 (기본: artifacts/run)
        level: 로그 레벨
        console_output: 콘솔 출력 여부
        file_output: 파일 출력 여부

    Returns:
        설정된 Logger 인스턴스
    """
    # Determine log directory
    if log_dir is None:
        repo_root = get_repo_root()
        log_dir = repo_root / DEFAULT_LOG_DIR
    else:
        log_dir = Path(log_dir)

    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger(script_name)
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Log format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if file_output:
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"{script_name}_{timestamp}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_script_logger(script_name: str) -> logging.Logger:
    """기존 설정된 스크립트 로거 가져오기

    Args:
        script_name: 스크립트 이름

    Returns:
        Logger 인스턴스 (없으면 기본 설정으로 생성)
    """
    logger = logging.getLogger(script_name)
    if not logger.handlers:
        # If no handlers configured, set up with defaults
        return setup_script_logging(script_name)
    return logger


class LogContext:
    """로깅 컨텍스트 매니저

    Usage:
        with LogContext(logger, "Processing files"):
            # ... processing ...
            # Automatically logs start/end with timing
    """

    def __init__(self, logger: logging.Logger, operation: str, **extra: Any) -> None:
        self.logger = logger
        self.operation = operation
        self.extra = extra
        self.start_time: datetime | None = None

    def __enter__(self) -> "LogContext":
        self.start_time = datetime.now()
        extra_str = ", ".join(f"{k}={v}" for k, v in self.extra.items())
        msg = f"Starting: {self.operation}"
        if extra_str:
            msg += f" ({extra_str})"
        self.logger.info(msg)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        elapsed = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        if exc_type is None:
            self.logger.info(f"Completed: {self.operation} ({elapsed:.2f}s)")
        else:
            self.logger.error(f"Failed: {self.operation} ({elapsed:.2f}s) - {exc_val}")
