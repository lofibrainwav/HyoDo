from __future__ import annotations

import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import ClassVar

from AFO.config.settings import get_settings

# Trinity Score: 90.0 (Established by Chancellor)
"""
Logging Configuration (眞善美孝永)
AFO 왕국 중앙 로깅 설정

眞 (Truth): 정확한 로그 레벨 및 포맷
善 (Goodness): 안전한 로그 처리 및 개인정보 보호
美 (Beauty): 구조화된 로그 포맷
孝 (Serenity): 개발자 경험 최적화
永 (Eternity): 지속 가능한 로그 관리
"""


class AFOFormatter(logging.Formatter):
    """AFO 왕국 커스텀 로그 포맷터"""

    # 색상 코드 (터미널용)
    COLORS: ClassVar[dict[str, str]] = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def __init__(self, use_colors: bool = True, structured: bool = False) -> None:
        """
        Args:
            use_colors: 터미널 색상 사용 여부
            structured: 구조화된 JSON 포맷 사용 여부
        """
        super().__init__()
        self.use_colors = use_colors and sys.stdout.isatty()
        self.structured = structured

    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드 포맷팅"""
        if self.structured:
            return self._format_structured(record)
        return self._format_text(record)

    def _format_text(self, record: logging.LogRecord) -> str:
        """텍스트 포맷 (기본)"""
        levelname = record.levelname
        color = self.COLORS.get(levelname, "") if self.use_colors else ""
        reset = self.COLORS["RESET"] if self.use_colors else ""

        # 타임스탬프 포맷
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S")

        # 로거 이름 (모듈명)
        logger_name = record.name.split(".")[-1] if "." in record.name else record.name

        # 메시지 포맷
        message = (
            f"{color}[{levelname:8}]{reset} {timestamp} | {logger_name:20} | {record.getMessage()}"
        )

        # 예외 정보 추가
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return message

    def _format_structured(self, record: logging.LogRecord) -> str:
        """구조화된 JSON 포맷"""

        log_data = {
            "timestamp": self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 예외 정보 추가
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 추가 컨텍스트 (extra 필드)
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(
    level: str | int = "INFO",
    log_file: Path | str | None = None,
    use_colors: bool = True,
    structured: bool = False,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> None:
    """
    AFO 왕국 로깅 설정

    Args:
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL 또는 숫자)
        log_file: 로그 파일 경로 (None이면 파일 로깅 안 함)
        use_colors: 터미널 색상 사용 여부
        structured: 구조화된 JSON 포맷 사용 여부
        max_bytes: 로그 파일 최대 크기 (바이트)
        backup_count: 백업 파일 개수
    """
    # 로그 레벨 변환
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 기존 핸들러 제거 (중복 방지)
    root_logger.handlers.clear()

    # 콘솔 핸들러 (항상 추가)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(AFOFormatter(use_colors=use_colors, structured=structured))
    root_logger.addHandler(console_handler)

    # 파일 핸들러 (선택적)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        # 파일은 구조화된 포맷 사용 (검색 용이)
        file_handler.setFormatter(AFOFormatter(use_colors=False, structured=True))
        root_logger.addHandler(file_handler)

    # 로깅 설정 완료 로그
    logging.info(
        f"✅ 로깅 설정 완료: 레벨={logging.getLevelName(level)}, 파일={log_file or '없음'}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    로거 인스턴스 가져오기 (편의 함수)

    Args:
        name: 로거 이름 (보통 __name__)

    Returns:
        Logger 인스턴스
    """
    return logging.getLogger(name)


# 전역 로깅 설정 (선택적)
def configure_from_settings() -> None:
    """설정에서 로깅 구성 로드"""
    try:
        settings = get_settings()

        # 로그 레벨 결정
        if hasattr(settings, "LOG_LEVEL"):
            level = settings.LOG_LEVEL
        elif hasattr(settings, "ENVIRONMENT"):
            level = "DEBUG" if settings.ENVIRONMENT == "dev" else "INFO"
        else:
            level = "INFO"

        # 로그 파일 경로 (선택적)
        log_file = None
        if hasattr(settings, "LOG_FILE"):
            log_file = settings.LOG_FILE
        elif hasattr(settings, "AFO_HOME") and settings.AFO_HOME:
            log_file = Path(settings.AFO_HOME) / "logs" / "afo.log"

        # 로깅 설정 적용
        setup_logging(
            level=level,
            log_file=log_file,
            use_colors=True,
            structured=False,  # 기본은 텍스트 포맷
        )
    except Exception as e:
        # 설정 로드 실패 시 기본 설정 사용
        setup_logging(level="INFO", log_file=None)
        logging.warning(f"설정에서 로깅 구성 로드 실패, 기본 설정 사용: {e}")
