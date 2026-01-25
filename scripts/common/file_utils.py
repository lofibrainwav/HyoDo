"""
File Utilities Module
파일 및 경로 관련 공통 유틸리티

Usage:
    from scripts.common import get_repo_root, ensure_dir, safe_read_json, safe_write_json

    # Get repository root
    root = get_repo_root()

    # Ensure directory exists
    ensure_dir("artifacts/run")

    # Safe JSON operations
    data = safe_read_json("config.json", default={})
    safe_write_json("output.json", data)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def get_repo_root() -> Path:
    """Get the repository root directory

    Searches for AGENTS.md or .git directory to determine repo root.

    Returns:
        Path to the repository root directory
    """
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "AGENTS.md").exists() or (parent / ".git").exists():
            return parent
    return Path.cwd()


def ensure_dir(path: str | Path) -> Path:
    """디렉토리가 존재하지 않으면 생성

    Args:
        path: 생성할 디렉토리 경로

    Returns:
        생성된 (또는 기존) 디렉토리 Path
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def safe_read_json(
    file_path: str | Path,
    default: Any = None,
    encoding: str = "utf-8",
) -> Any:
    """JSON 파일을 안전하게 읽기

    파일이 없거나 JSON 파싱 실패 시 기본값 반환.

    Args:
        file_path: JSON 파일 경로
        default: 기본값 (파일 없거나 오류 시 반환)
        encoding: 파일 인코딩

    Returns:
        파싱된 JSON 데이터 또는 기본값
    """
    path = Path(file_path)
    if not path.exists():
        logger.debug(f"File not found: {path}")
        return default

    try:
        with path.open(encoding=encoding) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON decode error in {path}: {e}")
        return default
    except OSError as e:
        logger.warning(f"Error reading {path}: {e}")
        return default


def safe_write_json(
    file_path: str | Path,
    data: Any,
    encoding: str = "utf-8",
    indent: int = 2,
    ensure_ascii: bool = False,
) -> bool:
    """JSON 파일을 안전하게 쓰기

    디렉토리가 없으면 자동 생성.

    Args:
        file_path: JSON 파일 경로
        data: 저장할 데이터
        encoding: 파일 인코딩
        indent: JSON 들여쓰기
        ensure_ascii: ASCII 강제 여부

    Returns:
        bool: 쓰기 성공 여부
    """
    path = Path(file_path)

    try:
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding=encoding) as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
        return True
    except (OSError, TypeError) as e:
        logger.error(f"Error writing {path}: {e}")
        return False


def find_files(
    pattern: str,
    root: str | Path | None = None,
    recursive: bool = True,
) -> list[Path]:
    """패턴과 일치하는 파일 찾기

    Args:
        pattern: glob 패턴 (예: "*.py", "**/*.md")
        root: 검색 시작 디렉토리 (기본: repo root)
        recursive: 재귀 검색 여부

    Returns:
        일치하는 파일 경로 리스트
    """
    if root is None:
        root = get_repo_root()
    root = Path(root)

    if recursive and "**" not in pattern:
        pattern = f"**/{pattern}"

    return sorted(root.glob(pattern))


