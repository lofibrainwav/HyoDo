"""The M5 remote-connector doc cannot be read as a live ChatGPT / remote MCP path."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
M5_DOC = REPO_ROOT / "docs" / "M5_REMOTE_CONNECTOR_CONTRACT.md"


def test_m5_doc_states_remote_is_contract_only_not_stdio() -> None:
    assert M5_DOC.is_file()
    text = M5_DOC.read_text(encoding="utf-8")
    lowered = text.lower()

    assert "contract-only" in lowered or "UNOBSERVED" in text
    assert "stdio" in lowered

    # Positive live claims we refuse. Negated "not live" is the honest form.
    assert "https://mcp.hyodo.app/mcp is live" not in lowered
    assert "mcp.hyodo.app is live" not in lowered
    assert "remote connector is live" not in lowered
    assert "not live yet" not in lowered


def test_docs_index_points_at_m5_contract() -> None:
    text = (REPO_ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    assert "M5_REMOTE_CONNECTOR_CONTRACT.md" in text
