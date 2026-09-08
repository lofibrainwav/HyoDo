"""docs/CODEX_HANDOFF_NEXT.md is current-truth notes, not a 4.4.0 rebuild queue."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HANDOFF = REPO_ROOT / "docs" / "CODEX_HANDOFF_NEXT.md"


def test_handoff_is_not_a_stale_440_queue() -> None:
    assert HANDOFF.is_file()
    text = HANDOFF.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "expect 4.4.0" not in lowered
    assert "no mcp/schema/eval/report" not in lowered
    assert "**not implemented**" not in lowered
    assert "start at **m1**" not in lowered
    assert "contract-only" in lowered or "UNOBSERVED" in text
    assert "hyodo mcp stdio" in lowered
    assert "integrity score" in lowered
    assert "demo fixture" in lowered


def test_docs_index_describes_handoff_as_current_notes() -> None:
    index = (REPO_ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    assert "CODEX_HANDOFF_NEXT.md" in index
    assert "4.4.0 rebuild queue" in index or "not a 4.4.0" in index.lower()
