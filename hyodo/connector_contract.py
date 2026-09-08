"""Public contract for HyoDo M5 remote-connector onboarding.

This module emits the connector declaration. It does not claim the remote
endpoint is live. Runtime availability stays UNOBSERVED because this code
never probes DNS, OAuth, or routing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hyodo.pairing import load_pairing, pairing_state

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


def _measure_bridge(root: Path | None) -> dict[str, Any]:
    """Measure the M5-B local bridge state for *root*, or report it unmeasured.

    ``root=None`` is the pure-default case (no workspace was named): the
    bridge is reported as ``UNPAIRED`` without touching the filesystem, so
    :func:`build_connector_contract` stays a pure function when called with
    no arguments. Passing a real *root* is the only way to observe a local
    pairing; remote availability is never probed here.
    """
    if root is None:
        return {
            "pairing": "UNPAIRED",
            "workspace_id": None,
            "root": None,
            "listener": "none",
            "last_seen_at": None,
        }
    state = pairing_state(root)
    record = load_pairing(root)
    return {
        "pairing": state.value,
        "workspace_id": record.workspace_id if record is not None else None,
        "root": record.root if record is not None else None,
        # A local socket probe would risk a false positive from an unrelated
        # process on the same port, and the pairing record does not persist
        # which listener it was created for. Reporting "loopback" exactly
        # when paired keeps this deterministic and matches the only bridge
        # transport M5-B measures end to end; tailscale is never claimed
        # without a dedicated live probe.
        "listener": "loopback" if state.value == "PAIRED" else "none",
        "last_seen_at": record.last_seen_at if record is not None else None,
    }


def build_connector_contract(root: Path | None = None) -> dict[str, Any]:
    """Return the machine-readable M5 connector contract.

    ``CONTRACT_ONLY`` and ``UNOBSERVED`` remote availability are intentional.
    They prevent this declaration from being mistaken for a deployed remote
    MCP service. Passing *root* additionally measures the M5-B local bridge
    (pairing lifecycle) for that workspace; ``status`` becomes
    ``PAIRED_LOCAL`` only when that local pairing is ``PAIRED`` — remote
    ``availability`` stays ``UNOBSERVED`` either way, because this call never
    probes DNS, OAuth, or routing.
    """
    bridge = _measure_bridge(root)
    status = "PAIRED_LOCAL" if bridge["pairing"] == "PAIRED" else "CONTRACT_ONLY"
    return {
        "schema_version": CONNECTOR_SCHEMA_VERSION,
        "status": status,
        "availability": "UNOBSERVED",
        "reasons": ["remote_not_probed"],
        "bridge": bridge,
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
