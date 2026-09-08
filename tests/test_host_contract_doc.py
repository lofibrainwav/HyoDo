"""The host-contract doc exists and names the honesty gaps implementers hit."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HOST_CONTRACT = REPO_ROOT / "docs" / "HOST_CONTRACT.md"
CONNECT_DOC = REPO_ROOT / "docs" / "CONNECT.md"


def test_host_contract_doc_exists_and_names_honesty_gaps() -> None:
    text = HOST_CONTRACT.read_text(encoding="utf-8")
    assert "UNOBSERVED" in text
    assert "allowed_tools" in text
    assert "blocked_path_globs" in text


def test_connect_doc_points_at_host_contract() -> None:
    text = CONNECT_DOC.read_text(encoding="utf-8")
    assert "HOST_CONTRACT.md" in text
