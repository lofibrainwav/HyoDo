"""Contracts for M5-A one-URL remote connector onboarding."""

from __future__ import annotations

import asyncio
import json
from urllib.parse import urlparse

from typer.testing import CliRunner

from hyodo.cli.main import app
from hyodo.connector_contract import MCP_CAPABILITIES, build_connector_contract
from hyodo.pairing import PAIRING_RELATIVE_PATH, create_pairing, revoke_pairing

runner = CliRunner()


def test_connector_contract_is_explicitly_not_live() -> None:
    contract = build_connector_contract()

    assert contract["schema_version"] == "hyodo.connector-contract/v1"
    assert contract["status"] == "CONTRACT_ONLY"
    assert contract["availability"] == "UNOBSERVED"
    assert contract["semantics"]["unobserved_is_green"] is False


def test_connector_contract_uses_one_https_mcp_address() -> None:
    connector = build_connector_contract()["connector"]
    parsed = urlparse(connector["url"])

    assert parsed.scheme == "https"
    assert parsed.netloc == "mcp.hyodo.app"
    assert parsed.path == "/mcp"
    assert connector["auth"] == "oauth2.1"
    assert connector["mcp_spec_target"] == "2026-07-28"


def test_connector_contract_preserves_local_execution_boundary() -> None:
    contract = build_connector_contract()

    assert contract["identity"]["cloud_roles"] == ["identity", "discovery", "routing"]
    assert contract["execution"] == {
        "owner": "local_hyodo_cli",
        "source_code_upload_default": False,
        "arbitrary_shell": False,
        "public_workstation_listener": False,
    }
    assert contract["privacy"]["digest_only_default"] is True
    assert contract["privacy"]["raw_body_requires_operator_consent"] is True


def test_connector_contract_capabilities_match_current_mcp_surface() -> None:
    contract = build_connector_contract()
    names = {item["name"] for item in contract["capabilities"]}

    assert (
        names
        == set(MCP_CAPABILITIES)
        == {
            "get_local_context",
            "hyodo_safe",
            "hyodo_check",
            "hyodo_event_record",
            "hyodo_policy_check",
            "hyodo_agent_rules",
        }
    )


def test_connector_contract_requires_revocation_and_unobserved_disconnect() -> None:
    contract = build_connector_contract()

    assert contract["onboarding"]["revoke_required"] is True
    assert "REVOKED" in contract["onboarding"]["pairing_states"]
    assert contract["semantics"]["missing_or_unreachable_workspace"] == "UNOBSERVED"
    assert contract["semantics"]["policy_signal_is_human_approval"] is False


def test_mcp_contract_json_is_machine_readable_and_honest() -> None:
    result = runner.invoke(app, ["mcp", "contract", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["connector"]["url"] == "https://mcp.hyodo.app/mcp"
    assert payload["status"] == "CONTRACT_ONLY"
    assert payload["availability"] == "UNOBSERVED"


def test_connector_capabilities_match_the_real_server(tmp_path) -> None:
    from hyodo.mcp_server import create_server

    tools = asyncio.run(create_server(tmp_path).list_tools())
    contract_names = {item["name"] for item in build_connector_contract()["capabilities"]}

    assert contract_names == {tool.name for tool in tools}


def test_connector_contract_targets_hardened_oauth_discovery() -> None:
    auth = build_connector_contract()["authorization"]

    assert auth["protected_resource_metadata"] == "rfc9728"
    assert auth["client_registration"] == "cimd_preferred"
    assert auth["issuer_validation"] == "rfc9207"
    assert auth["refresh_tokens_for_persistent_hosts"] is True


# ── M5-B: bridge object reflects measured local pairing state ──────────────


def test_connector_contract_bare_call_stays_pure_and_unpaired() -> None:
    """Calling with no root touches no filesystem and never claims a pairing."""
    contract = build_connector_contract()

    assert contract["status"] == "CONTRACT_ONLY"
    assert contract["availability"] == "UNOBSERVED"
    assert "remote_not_probed" in contract["reasons"]
    assert contract["bridge"] == {
        "pairing": "UNPAIRED",
        "workspace_id": None,
        "root": None,
        "listener": "none",
        "last_seen_at": None,
    }


def test_connector_contract_reports_paired_local_when_measured(tmp_path) -> None:
    record, _token = create_pairing(tmp_path)

    contract = build_connector_contract(tmp_path)

    assert contract["status"] == "PAIRED_LOCAL"
    assert contract["availability"] == "UNOBSERVED"
    assert "remote_not_probed" in contract["reasons"]
    assert contract["bridge"]["pairing"] == "PAIRED"
    assert contract["bridge"]["workspace_id"] == record.workspace_id
    assert contract["bridge"]["listener"] == "loopback"


def test_connector_contract_revoked_pairing_stays_contract_only(tmp_path) -> None:
    create_pairing(tmp_path)
    revoke_pairing(tmp_path)

    contract = build_connector_contract(tmp_path)

    assert contract["bridge"]["pairing"] == "REVOKED"
    assert contract["status"] == "CONTRACT_ONLY"


def test_connector_contract_unpaired_workspace_stays_contract_only(tmp_path) -> None:
    contract = build_connector_contract(tmp_path)

    assert contract["bridge"]["pairing"] == "UNPAIRED"
    assert contract["bridge"]["workspace_id"] is None
    assert contract["status"] == "CONTRACT_ONLY"


def test_connector_contract_corrupt_pairing_file_is_unobserved(tmp_path) -> None:
    path = tmp_path / PAIRING_RELATIVE_PATH
    path.parent.mkdir(parents=True)
    path.write_text("{not json", encoding="utf-8")

    contract = build_connector_contract(tmp_path)

    assert contract["bridge"]["pairing"] == "UNOBSERVED"
    assert contract["status"] == "CONTRACT_ONLY"


def test_mcp_contract_cli_measures_the_given_root(tmp_path) -> None:
    record, _token = create_pairing(tmp_path)

    result = runner.invoke(app, ["mcp", "contract", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] == "PAIRED_LOCAL"
    assert payload["bridge"]["workspace_id"] == record.workspace_id
