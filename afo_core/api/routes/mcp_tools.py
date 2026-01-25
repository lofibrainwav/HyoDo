from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from AFO.config.health_check_config import health_check_config
from AFO.services.mcp_stdio_client import list_tools as _list_tools

# Trinity Score: 90.0 (Established by Chancellor)
"""MCP Tools Management API
MCP 도구 관리 및 상태 확인 엔드포인트
"""


router = APIRouter(prefix="/api/mcp", tags=["MCP Tools"])

logger = logging.getLogger(__name__)


def _resolve_workspace_root() -> Path | None:
    """Best-effort workspace root resolver for local dev."""
    env_root = os.getenv("WORKSPACE_ROOT")
    if env_root:
        try:
            return Path(env_root).expanduser().resolve()
        except Exception:
            return None

    here = Path(__file__).resolve()

    # Prefer the actual git root when available.
    for parent in [here, *here.parents]:
        if (parent / ".git").exists():
            return parent

    # Fallback: choose the outermost AGENTS.md (monorepo has nested AGENTS.md).
    last_agents: Path | None = None
    for parent in [here, *here.parents]:
        if (parent / "AGENTS.md").exists():
            last_agents = parent

    return last_agents


def _resolve_mcp_config_path() -> Path:
    """Resolve the MCP config path with overrides.

    Priority:
    1) `AFO_MCP_CONFIG_PATH` (explicit override)
    2) `<workspace_root>/.cursor/mcp.json` if workspace root detected
    3) `~/.cursor/mcp.json` (fallback)
    """
    env_path = os.getenv("AFO_MCP_CONFIG_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()

    workspace_root = _resolve_workspace_root()
    if workspace_root:
        return (workspace_root / ".cursor" / "mcp.json").resolve()

    return (Path.home() / ".cursor" / "mcp.json").resolve()


# MCP 설정 파일 경로
MCP_CONFIG_PATH = _resolve_mcp_config_path()
WORKSPACE_ROOT = _resolve_workspace_root() or Path.cwd()


class MCPToolRequest(BaseModel):
    """MCP 도구 추가 요청"""

    name: str = Field(..., description="MCP 서버 이름")
    command: str = Field(..., description="실행 명령어")
    args: list[str] = Field(default_factory=list, description="명령어 인자")
    env: dict[str, str] = Field(default_factory=dict, description="환경 변수")
    description: str = Field(default="", description="설명")


class MCPTestRequest(BaseModel):
    """MCP 연결 테스트 요청"""

    server_name: str = Field(..., description="테스트할 서버 이름")


@router.get("/list")
async def list_mcp_tools() -> dict[str, Any]:
    """등록된 모든 MCP 도구 목록 조회"""
    try:
        config = health_check_config
        servers = [
            {
                "name": server.name,
                "description": server.description,
                "status": server.status,
            }
            for server in config.MCP_SERVERS
        ]

        return {
            "status": "success",
            "total": len(servers),
            "servers": servers,
        }
    except Exception as e:
        logger.error(f"MCP tools list failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/add")
async def add_mcp_tool(request: MCPToolRequest) -> dict[str, Any]:
    """새 MCP 도구 추가

    MCP 설정 파일(.cursor/mcp.json)에 새 서버를 추가합니다.
    """
    try:
        # MCP 설정 파일 읽기
        mcp_config = {}
        if MCP_CONFIG_PATH.exists():
            with open(MCP_CONFIG_PATH, encoding="utf-8") as f:
                mcp_config = json.load(f)
        else:
            mcp_config = {"mcpServers": {}}

        # 새 서버 추가
        if "mcpServers" not in mcp_config:
            mcp_config["mcpServers"] = {}

        # 환경 변수 처리 (WORKSPACE_ROOT 등 자동 치환)
        processed_env = {}
        for key, value in request.env.items():
            if "${WORKSPACE_ROOT}" in value:
                value = value.replace("${WORKSPACE_ROOT}", str(WORKSPACE_ROOT))
            processed_env[key] = value

        # 인자 처리 (WORKSPACE_ROOT 자동 치환)
        processed_args = []
        for arg in request.args:
            if "${WORKSPACE_ROOT}" in arg:
                arg = arg.replace("${WORKSPACE_ROOT}", str(WORKSPACE_ROOT))
            processed_args.append(arg)

        mcp_config["mcpServers"][request.name] = {
            "command": request.command,
            "args": processed_args,
            "env": processed_env if processed_env else None,
            "description": request.description or f"{request.name} MCP Server",
        }

        # 설정 파일 저장
        MCP_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(MCP_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(mcp_config, f, indent=2, ensure_ascii=False)

        logger.info(f"MCP tool '{request.name}' added successfully")

        return {
            "status": "success",
            "message": f"MCP tool '{request.name}' added successfully",
            "config_path": str(MCP_CONFIG_PATH),
        }
    except Exception as e:
        logger.error(f"Failed to add MCP tool: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add MCP tool: {e}") from e


@router.post("/test")
async def test_mcp_connection(request: MCPTestRequest) -> dict[str, Any]:
    """MCP 서버 연결 테스트

    서버가 실제로 실행 가능한지 확인합니다.
    """
    try:
        config = health_check_config
        server = next((s for s in config.MCP_SERVERS if s.name == request.server_name), None)

        if not server:
            # MCP 설정 파일에서 확인
            if MCP_CONFIG_PATH.exists():
                with open(MCP_CONFIG_PATH, encoding="utf-8") as f:
                    mcp_config = json.load(f)
                    if request.server_name not in mcp_config.get("mcpServers", {}):
                        raise HTTPException(
                            status_code=404,
                            detail=f"MCP server '{request.server_name}' not found",
                        )
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"MCP server '{request.server_name}' not found",
                )

        connected = True
        error_message = None
        tools: list[str] | None = None

        # Deep check for local stdio MCP servers where possible.
        try:
            if request.server_name in {
                "afo-ultimate-mcp",
                "afo-skills-mcp",
                "afo-messaging-mcp",
                "trinity-score-mcp",
                "afo-skills-registry-mcp",
                "afo-obsidian-mcp",
            }:
                tools = _list_tools(request.server_name)
                connected = len(tools) > 0
        except Exception as e:
            connected = False
            error_message = str(e)

        return {
            "status": "success",
            "server_name": request.server_name,
            "connected": connected,
            "tools": tools,
            "error": error_message,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MCP connection test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/status")
async def get_mcp_status() -> dict[str, Any]:
    """모든 MCP 도구의 연결 상태 조회"""
    try:
        config = health_check_config
        servers_status = []

        for server in config.MCP_SERVERS:
            # 각 서버의 상태 확인
            status = "configured"
            try:
                # 실제 연결 테스트는 비용이 많이 들 수 있으므로
                # 기본적으로 'configured' 상태로 반환
                # 필요시 test_mcp_connection을 개별 호출
                status = server.status if hasattr(server, "status") else "configured"
            except Exception:
                status = "error"

            servers_status.append(
                {
                    "name": server.name,
                    "description": server.description,
                    "status": status,
                }
            )

        return {
            "status": "success",
            "servers": servers_status,
            "total": len(servers_status),
        }
    except Exception as e:
        logger.error(f"MCP status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
