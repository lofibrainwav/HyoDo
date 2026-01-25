import os
from typing import Any, cast

import httpx
from mcp.server.fastmcp import FastMCP

AFO_API_BASE_URL = os.environ.get("AFO_API_BASE_URL", "http://127.0.0.1:8010").rstrip("/")
HTTP_TIMEOUT_S = float(os.environ.get("AFO_MCP_HTTP_TIMEOUT_S", "15"))

mcp = FastMCP("AFO Skills MCP")


def _client() -> httpx.Client:
    return httpx.Client(base_url=AFO_API_BASE_URL, timeout=HTTP_TIMEOUT_S)


@mcp.tool()
def afo_api_health() -> dict[str, Any]:
    with _client() as c:
        r = c.get("/api/skills/health")
        r.raise_for_status()
        return cast("dict[str, Any]", r.json())


@mcp.tool()
def skills_list(
    category: str | None = None, q: str | None = None, limit: int = 100
) -> dict[str, Any]:
    if limit < 1 or limit > 500:
        raise ValueError("limit must be 1..500")
    params: dict[str, str | int] = {"limit": limit}
    if category:
        params["category"] = category
    if q:
        params["q"] = q
    with _client() as c:
        r = c.get("/api/skills/list", params=params)
        r.raise_for_status()
        return cast("dict[str, Any]", r.json())


@mcp.tool()
def skills_detail(skill_id: str) -> dict[str, Any]:
    if not skill_id:
        raise ValueError("skill_id is required")
    with _client() as c:
        r = c.get(f"/api/skills/detail/{skill_id}")
        r.raise_for_status()
        return cast("dict[str, Any]", r.json())


@mcp.tool()
def skills_execute(
    skill_id: str, inputs: dict | None = None, dry_run: bool = True
) -> dict[str, Any]:
    if not skill_id:
        raise ValueError("skill_id is required")
    payload = {"skill_id": skill_id, "inputs": inputs or {}, "dry_run": bool(dry_run)}
    with _client() as c:
        r = c.post("/api/skills/execute", json=payload)
        r.raise_for_status()
        return cast("dict[str, Any]", r.json())


@mcp.tool()
def genui_generate(
    prompt: str, template: str = "react_component", dry_run: bool = True
) -> dict[str, Any]:
    if not prompt or len(prompt) > 8000:
        raise ValueError("prompt is required (<= 8000 chars)")
    payload = {"prompt": prompt, "template": template, "dry_run": bool(dry_run)}
    with _client() as c:
        r = c.post("/api/genui/generate", json=payload)
        r.raise_for_status()
        return cast("dict[str, Any]", r.json())


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
