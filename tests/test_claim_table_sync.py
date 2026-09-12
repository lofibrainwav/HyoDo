"""Keep every public capability claim synchronized with the registry SSOT."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HEADER = "| Capability | Status | Evidence boundary |"
REGISTRY = REPO_ROOT / "docs" / "capabilities.json"


def tracked_markdown() -> list[Path]:
    listing = subprocess.run(
        ["git", "ls-files", "-z", "*.md"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [REPO_ROOT / name for name in listing.stdout.split("\0") if name]


def claim_table(text: str) -> list[str] | None:
    lines = text.splitlines()
    try:
        start = lines.index(HEADER)
    except ValueError:
        return None
    block = [HEADER]
    for line in lines[start + 1 :]:
        if not line.startswith("|"):
            break
        block.append(line)
    return block


def registry_table() -> list[str]:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert payload["schema"] == "hyodo.capabilities/v1"
    rows = payload["public_claim_table"]
    rendered = [HEADER, "| --- | --- | --- |"]
    rendered.extend(
        f"| {capability} | {status} | {evidence} |" for capability, status, evidence in rows
    )
    return rendered


def test_every_copy_of_the_claim_table_matches_the_registry() -> None:
    source = registry_table()
    copies = 0
    mismatched: list[str] = []
    for path in tracked_markdown():
        copy = claim_table(path.read_text(encoding="utf-8"))
        if copy is None:
            continue
        copies += 1
        if copy != source:
            rel = path.relative_to(REPO_ROOT)
            extra = set(copy) - set(source)
            missing = set(source) - set(copy)
            mismatched.append(f"{rel}: +{sorted(extra)} -{sorted(missing)}")

    assert copies >= 2, "expected the public claim table in multiple tracked documents"
    assert not mismatched, "claim table copies disagree with docs/capabilities.json:\n" + "\n".join(
        mismatched
    )


def test_registry_contains_current_state_axes() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    capabilities = payload["capabilities"]
    required = {
        "runtime_identity_v1",
        "graph_v2_multi_parent",
        "codex_canonical_canary",
        "cursor_live_callback",
        "public_remote_mcp",
        "acl_wisdom_routing",
        "ifa_v0",
        "friction_collector_uploader",
    }
    assert required <= set(capabilities)
    for value in capabilities.values():
        assert set(value) == {"public", "current"}


def test_the_table_is_found_by_its_header_not_its_position() -> None:
    text = "intro\n\n" + HEADER + "\n| --- | --- | --- |\n| a | B | c. |\n\nafter\n"
    assert claim_table(text) == [HEADER, "| --- | --- | --- |", "| a | B | c. |"]
    assert claim_table("no table here\n") is None
