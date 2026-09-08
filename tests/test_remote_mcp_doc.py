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
    assert "until m5-b serves" not in lowered
    assert "intends to serve" not in lowered


def test_docs_index_points_at_m5_contract() -> None:
    text = (REPO_ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    assert "M5_REMOTE_CONNECTOR_CONTRACT.md" in text


def test_mcp_contract_cli_source_does_not_say_live_yet() -> None:
    text = (REPO_ROOT / "hyodo" / "cli" / "main.py").read_text(encoding="utf-8")
    assert "not claimed live yet" not in text
    assert "not live yet" not in text.lower()


def test_mcp_design_doc_status_says_remote_is_contract_only() -> None:
    text = (REPO_ROOT / "docs" / "HYODO_MCP_CONNECTOR_DESIGN.md").read_text(encoding="utf-8")
    lowered = text.lower()
    assert "contract-only" in lowered
    assert "UNOBSERVED" in text
    assert "start at **M1**" not in text
    assert "local status" in lowered or "are shipped" in lowered


def test_connector_contract_module_does_not_imply_imminent_remote() -> None:
    text = (REPO_ROOT / "hyodo" / "connector_contract.py").read_text(encoding="utf-8")
    lowered = text.lower()
    assert "intends to serve" not in lowered
    assert "until a later phase" not in lowered
    assert "UNOBSERVED" in text
