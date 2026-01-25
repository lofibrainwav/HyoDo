from __future__ import annotations

import inspect
import sys
from pathlib import Path

# Trinity Score: 90.0 (Established by Chancellor)
"""Path Utilities (眞 - Truth)
경로 계산 유틸리티 - 하드코딩 제거

야전교범 원칙: 가정 금지 - 경로는 항상 동적으로 계산
"""


def get_project_root(start_path: Path | None = None) -> Path:
    """프로젝트 루트 경로를 동적으로 계산

    Args:
        start_path: 시작 경로 (기본값: 현재 파일의 위치)

    Returns:
        프로젝트 루트 Path 객체

    Example:
        >>> root = get_project_root()
        >>> trinity_os_path = root / "packages" / "trinity-os"

    """
    if start_path is None:
        # 호출한 파일의 위치를 기준으로 계산

        frame = inspect.currentframe()
        if frame and frame.f_back:
            caller_file = frame.f_back.f_globals.get("__file__")
            start_path = Path(caller_file).resolve() if caller_file else Path.cwd()
        else:
            start_path = Path.cwd()

    current = Path(start_path).resolve()

    # pyproject.toml 또는 .git 디렉토리를 찾을 때까지 상위로 이동
    # 최대 10단계까지 상위로 이동 (무한 루프 방지)
    max_depth = 10
    depth = 0

    while current != current.parent and depth < max_depth:
        # pyproject.toml 또는 .git이 있으면 프로젝트 루트 후보
        if (current / "pyproject.toml").exists() or (current / ".git").exists():
            # packages 디렉토리가 있으면 그 상위가 프로젝트 루트
            if (current / "packages").exists() and (current / "packages" / "trinity-os").exists():
                return current
            # packages가 없으면 현재가 프로젝트 루트
            if not (current / "packages").exists():
                return current
        current = current.parent
        depth += 1

    # 찾지 못하면 현재 작업 디렉토리에서 다시 시도
    cwd = Path.cwd().resolve()
    if (cwd / "pyproject.toml").exists() or (cwd / ".git").exists():
        return cwd

    # 그래도 찾지 못하면 시작 경로의 5단계 상위 (기존 로직과 호환)
    fallback = Path(start_path).resolve()
    for _ in range(5):
        fallback = fallback.parent
        if (fallback / "packages").exists() and (fallback / "packages" / "trinity-os").exists():
            return fallback

    # 최후의 수단: 현재 작업 디렉토리 반환
    return Path.cwd().resolve()


def get_trinity_os_path(start_path: Path | None = None) -> Path:
    """Trinity OS 패키지 경로를 동적으로 계산

    Args:
        start_path: 시작 경로 (기본값: 현재 파일의 위치)

    Returns:
        Trinity OS 패키지 경로

    """
    project_root = get_project_root(start_path)
    return project_root / "packages" / "trinity-os"


def get_afo_core_path(start_path: Path | None = None) -> Path:
    """AFO Core 패키지 경로를 동적으로 계산

    Args:
        start_path: 시작 경로 (기본값: 현재 파일의 위치)

    Returns:
        AFO Core 패키지 경로

    """
    project_root = get_project_root(start_path)
    return project_root / "packages" / "afo-core"


def add_to_sys_path(path: Path, sys_path_list: list | None = None) -> None:
    """sys.path에 경로 추가 (중복 방지)

    Args:
        path: 추가할 경로
        sys_path_list: sys.path 리스트 (기본값: sys.path)

    """

    if sys_path_list is None:
        sys_path_list = sys.path

    path_str = str(path.resolve())
    if path_str not in sys_path_list:
        sys_path_list.insert(0, path_str)
