from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

# Trinity Score: 90.0 (Established by Chancellor)
"""Git Status API
Git 저장소 상태 조회 엔드포인트
"""


router = APIRouter(prefix="/api/git", tags=["Git Status"])

logger = logging.getLogger(__name__)


# Dynamic workspace root calculation - find .git directory by walking up
def _find_git_root() -> Path:
    """Find the git root by walking up the directory tree."""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".git").exists():
            return parent
    # Fallback: try known paths in order
    fallback_paths = [
        Path("/app"),  # Docker container root
        current.parents[4] if len(current.parents) > 4 else None,  # packages/afo-core layout
        current.parents[2] if len(current.parents) > 2 else None,  # AFO layout
    ]
    for p in fallback_paths:
        if p and p.exists():
            return p
    return Path.cwd()


WORKSPACE_ROOT = _find_git_root()


def _run_git_command(cmd: str) -> str:
    """Git 명령어 실행"""
    try:
        result = subprocess.run(
            cmd.split(),
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return ""
    except Exception as e:
        logger.warning(f"Git command failed: {cmd}, error: {e}")
        return ""


@router.get("/status")
async def get_git_status() -> dict[str, Any]:
    """Git 저장소 상태 조회

    Returns:
        - total_commits: 전체 커밋 수
        - today_commits: 오늘 커밋 수
        - head: 현재 HEAD SHA
        - branch: 현재 브랜치
        - synced: 동기화 상태 (uncommitted changes 여부)
        - status: git status 출력
        - recent_commits: 최근 커밋 목록

    """
    try:
        # 기본 Git 정보
        total_commits = _run_git_command("git rev-list --count HEAD")
        head_sha = _run_git_command("git rev-parse --short HEAD")
        branch = _run_git_command("git branch --show-current")
        status_output = _run_git_command("git status --porcelain")

        # 오늘 커밋 수
        try:
            # git log --oneline --since='midnight' 결과를 가져와 Python에서 줄 수 계산
            result = subprocess.run(
                ["git", "log", "--oneline", "--since=midnight"],
                cwd=WORKSPACE_ROOT,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                commits = result.stdout.strip().split("\n")
                today_commits = str(len([c for c in commits if c.strip()]))
            else:
                today_commits = "0"
        except Exception:
            today_commits = "0"

        # 최근 커밋 목록
        recent_commits_output = _run_git_command("git log --oneline -10")
        recent_commits = []
        if recent_commits_output:
            for line in recent_commits_output.split("\n"):
                if line.strip():
                    parts = line.split(" ", 1)
                    if len(parts) == 2:
                        recent_commits.append({"hash": parts[0], "message": parts[1][:50]})

        # 동기화 상태
        synced = not bool(status_output)

        # 추적 중인 파일 수
        tracked_files_output = _run_git_command("git ls-tree -r HEAD --name-only")
        if tracked_files_output:
            tracked_files = str(len([f for f in tracked_files_output.split("\n") if f.strip()]))
        else:
            tracked_files = "0"

        return {
            "status": "success",
            "total_commits": int(total_commits) if total_commits.isdigit() else 0,
            "today_commits": (int(today_commits.strip()) if today_commits.strip().isdigit() else 0),
            "head": head_sha,
            "branch": branch or "unknown",
            "synced": synced,
            "has_changes": not synced,
            "status_output": status_output,
            "tracked_files": (int(tracked_files.strip()) if tracked_files.strip().isdigit() else 0),
            "recent_commits": recent_commits,
        }
    except Exception as e:
        logger.error(f"Git status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get git status: {e}") from e


@router.get("/info")
async def get_git_info() -> dict[str, Any]:
    """Git 저장소 상세 정보 조회

    Returns:
        - remote: 원격 저장소 정보
        - config: Git 설정 정보
        - tags: 태그 목록

    """
    try:
        # 원격 저장소 정보
        remote_url = _run_git_command("git config --get remote.origin.url")

        # 태그 목록
        tags_output = _run_git_command("git tag -Union[l, tail] -10")
        tags = (
            [tag.strip() for tag in tags_output.split("\n") if tag.strip()] if tags_output else []
        )

        # 사용자 정보
        user_name = _run_git_command("git config user.name")
        user_email = _run_git_command("git config user.email")

        return {
            "status": "success",
            "remote": {
                "url": remote_url,
            },
            "user": {
                "name": user_name,
                "email": user_email,
            },
            "tags": tags,
        }
    except Exception as e:
        logger.error(f"Git info check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get git info: {e}") from e
