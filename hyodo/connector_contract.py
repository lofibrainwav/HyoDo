"""Public contract for HyoDo M5 remote-connector onboarding.

This module describes the connector that M5 intends to serve. It does not
claim that the remote endpoint is live. Runtime availability stays explicitly
UNOBSERVED until a later phase provides and probes the service.
"""

from __future__ import annotations

from typing import Any

CONNECTOR_SCHEMA_VERSION = "hyodo.connector-contract/v1"
REMOTE_CONNECTOR_URL = "https://mcp.hyodo.app/mcp"
OAUTH_RESOURCE_METADATA_URL = "https://mcp.hyodo.app/.well-known/oauth-protected-resource"
ONBOARDING_URL = "https://hyodo.app/connect"

MCP_CAPABILITIES = (
    "get_local_context",
    "hyodo_safe",
    "hyodo_check",
    "hyodo_event_record",
    "hyodo_policy_check",
    "hyodo_agent_rules",
)
PAIRING_STATES = (
    "UNPAIRED",
    "PAIRING",
    "PAIRED",
    "REVOKED",
    "UNOBSERVED",
)


def build_connector_contract() -> dict[str, Any]:
    """Return the machine-readable M5-A connector contract.

    ``CONTRACT_ONLY`` and ``UNOBSERVED`` are intentional. They prevent this
    declaration from being mistaken for a deployed remote MCP service.
    """
    return {
        "schema_version": CONNECTOR_SCHEMA_VERSION,
        "status": "CONTRACT_ONLY",
        "availability": "UNOBSERVED",
        "connector": {
            "url": REMOTE_CONNECTOR_URL,
            "transport": "streamable-http",
            "auth": "oauth2.1",
            "protected_resource_metadata": OAUTH_RESOURCE_METADATA_URL,
            "mcp_spec_target": "2026-07-28",
        },
        "onboarding": {
            "url": ONBOARDING_URL,
            "flow": ["authenticate", "pair_workspace", "discover_tools", "use"],
            "pairing_states": list(PAIRING_STATES),
            "revoke_required": True,
        },
        "identity": {
            "cloud_roles": ["identity", "discovery", "routing"],
            "workspace_identity": "paired_local_workspace",
            "device_identity_required": True,
        },
        "authorization": {
            "protected_resource_metadata": "rfc9728",
            "authorization_server_discovery": ["rfc8414", "openid-connect"],
            "client_registration": "cimd_preferred",
            "issuer_validation": "rfc9207",
            "refresh_tokens_for_persistent_hosts": True,
        },
        "execution": {
            "owner": "local_hyodo_cli",
            "source_code_upload_default": False,
            "arbitrary_shell": False,
            "public_workstation_listener": False,
        },
        "privacy": {
            "digest_only_default": True,
            "raw_body_requires_operator_consent": True,
        },
        "semantics": {
            "missing_or_unreachable_workspace": "UNOBSERVED",
            "policy_signal_is_human_approval": False,
            "unobserved_is_green": False,
        },
        "capabilities": [{"name": name, "owner": "hyodo_cli"} for name in MCP_CAPABILITIES],
    }
