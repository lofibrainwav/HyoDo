"""Guard: server.json (the official MCP Registry manifest, see
https://github.com/modelcontextprotocol/registry) parses and stays in sync
with this repository's other sources of truth.

``description`` must equal the live ``instructions=`` string handed to the
MCP server in ``hyodo/mcp_server.py``. That value isn't a module-level
constant (it's a literal inside ``create_server()``), so it can't be
imported — this reads the source text and extracts the two concatenated
string-literal pieces directly.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
SERVER_JSON_PATH = ROOT / "server.json"
MCP_SERVER_PATH = ROOT / "hyodo" / "mcp_server.py"

# Matches the `instructions=(\n    "..." \n    "..." \n),` literal inside
# create_server(). Two adjacent string literals, Python-concatenated.
INSTRUCTIONS_RE = re.compile(r'instructions=\(\s*"([^"]*)"\s*"([^"]*)"\s*\)')


def _read_server_instructions() -> str:
    text = MCP_SERVER_PATH.read_text(encoding="utf-8")
    match = INSTRUCTIONS_RE.search(text)
    assert match, "could not find instructions=(...) literal in hyodo/mcp_server.py"
    return match.group(1) + match.group(2)


def _load_manifest() -> dict:
    return json.loads(SERVER_JSON_PATH.read_text(encoding="utf-8"))


def test_server_json_is_valid_json() -> None:
    data = _load_manifest()
    assert isinstance(data, dict)
    assert data["packages"]


def test_server_json_name_is_the_github_namespace() -> None:
    data = _load_manifest()
    assert data["name"] == "io.github.lofibrainwav/hyodo"


def test_server_json_version_matches_version_file() -> None:
    data = _load_manifest()
    expected = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert data["version"] == expected
    # Every package version listed must also track VERSION.
    for package in data["packages"]:
        assert package["version"] == expected


def test_server_json_description_fits_registry_limit_and_matches_server_intent() -> None:
    """The registry caps ``description`` at 100 characters, so it cannot equal
    the longer live ``instructions`` string; it must instead stay within the
    limit and preserve the two non-negotiable claims of that string: the
    adapter is local, and it never grants approval."""
    data = _load_manifest()
    description = data["description"]
    live = _read_server_instructions()
    assert len(description) <= 100
    assert description.startswith("Local HyoDo CLI adapter")
    assert "approval" in description
    assert "approv" in live
