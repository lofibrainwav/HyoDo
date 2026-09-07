"""M5-D cross-model continuity receipt.

Read-only measurement of one workspace's HyoDo truth stores: the agent-event
ledger, the optional policy file, the MCP access ledger, and the optional
pairing file. It starts no server, reads no client path, and contacts no
network — remote availability is always reported ``UNOBSERVED`` with reason
``remote_not_probed``, exactly like ``hyodo.connector_contract``.

What this module proves is host-independence, not a live ChatGPT/Claude
handshake: two distinct MCP callers against the *same* workspace (the stdio
adapter and the paired loopback HTTP bridge) write into the same four fixed
local files. See ``docs/M5_REMOTE_CONNECTOR_CONTRACT.md``'s M5-D section.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hyodo.access_ledger import ACCESS_LEDGER_PATH
from hyodo.events import AGENT_EVENTS_RELATIVE_PATH, read_agent_events
from hyodo.pairing import PAIRING_RELATIVE_PATH, load_pairing
from hyodo.policy import POLICY_RELATIVE_PATH, try_load_policy

CONTINUITY_SCHEMA_VERSION = "hyodo.continuity/v1"

# The M5-D slice observes at most two local caller shapes: one stdio session
# (no pairing) and one paired loopback/tailscale bridge caller. A third host
# (the remote connector) exists only as a contract today, so 2 is the
# honest ceiling this receipt measures against — not a guess about how many
# hosts a real deployment might eventually pair.
EXPECTED_HOSTS = 2

# The stdio transport never sets a caller_id (see ``mcp_server.create_server``'s
# default parameter and ``run_stdio``, which never passes one). Every stdio
# session's access-ledger rows therefore carry ``caller_id: null`` and are
# indistinguishable from one another by identity alone — they are grouped
# under this one label. A paired HTTP bridge caller always carries its
# pairing's ``workspace_id`` (``mcp_server._create_http_app`` passes it as
# ``caller_id`` whenever ``paired=True``), so those rows group by that id
# instead. These are the only two shapes ``_record_access`` can produce.
STDIO_IDENTITY = "stdio (no pairing)"


def _digest_file(path: Path) -> str | None:
    """Return ``sha256:<hex>`` for *path*, or ``None`` if it does not exist or is unreadable."""
    if not path.exists():
        return None
    try:
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _read_access_entries(root: Path) -> tuple[list[dict[str, Any]] | None, int]:
    """Read the raw access ledger, distinguishing "unreadable" from "corrupt lines".

    Mirrors :func:`hyodo.events.read_agent_events`'s ``(entries, corrupt)``
    contract: ``None`` means the file exists but could not be read (a
    different fact from an empty ledger); a missing file is an honest empty
    list. :func:`hyodo.access_ledger.read_access_log` silently skips
    malformed lines and cannot report this distinction, so this receipt reads
    the file itself rather than reusing it.
    """
    path = root / ACCESS_LEDGER_PATH
    if not path.exists():
        return [], 0
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None, 0
    entries: list[dict[str, Any]] = []
    corrupt = 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            corrupt += 1
            continue
        if isinstance(parsed, dict):
            entries.append(parsed)
        else:
            corrupt += 1
    return entries, corrupt


def _caller_identity(caller_id: str | None) -> str:
    """Classify one access-ledger ``caller_id`` into a distinct observed identity.

    A total, two-branch classification: ``None`` is every stdio session
    (:data:`STDIO_IDENTITY`); any string is a paired bridge caller's
    ``workspace_id``, labeled ``paired:<workspace_id>``. See the module
    docstring and :data:`STDIO_IDENTITY` for how each shape is produced.
    """
    if caller_id is None:
        return STDIO_IDENTITY
    return f"paired:{caller_id}"


@dataclass(frozen=True)
class StoreFact:
    """One measured truth-store file: whether it exists, is readable, and its digest."""

    path: str
    exists: bool
    readable: bool
    digest: str | None
    count: int | None = None
    corrupt_lines: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Return the JSON-serializable form used in the ``hyodo.continuity/v1`` receipt."""
        return {
            "path": self.path,
            "exists": self.exists,
            "readable": self.readable,
            "digest": self.digest,
            "count": self.count,
            "corrupt_lines": self.corrupt_lines,
        }


def measure_continuity(root: Path, *, expected_hosts: int = EXPECTED_HOSTS) -> dict[str, Any]:
    """Measure the M5-D continuity receipt for one workspace. Never raises.

    Reads exactly four fixed-relative-path local stores
    (``.hyodo/agent-events.jsonl``, ``.hyodo/policy.toml``,
    ``.hyodo/mcp-access.jsonl``, ``.hyodo/pairing.json``); starts no server;
    contacts no network. ``status`` is ``READY`` when every present store is
    readable and every line-delimited store is uncorrupted, and
    ``UNOBSERVED`` otherwise — never a probability, and never inferred from
    how many hosts were observed.
    """
    resolved = root.expanduser().resolve()
    reasons: list[str] = []

    # --- agent-event ledger (required path, may not exist yet) ---
    events, events_corrupt = read_agent_events(resolved)
    events_unreadable = events is None
    events_path = resolved / AGENT_EVENTS_RELATIVE_PATH
    agent_events_store = StoreFact(
        path=str(AGENT_EVENTS_RELATIVE_PATH),
        exists=events_path.exists(),
        readable=not events_unreadable,
        digest=_digest_file(events_path),
        count=len(events) if events is not None else None,
        corrupt_lines=events_corrupt,
    )
    if events_unreadable:
        reasons.append("agent_events_unreadable")
    if events_corrupt:
        reasons.append("agent_events_corrupt")

    # --- policy file (optional: absence is not a failure) ---
    policy_path = resolved / POLICY_RELATIVE_PATH
    _policy_config, policy_error = try_load_policy(policy_path)
    policy_unreadable = policy_error == "policy_invalid"
    policy_store = StoreFact(
        path=str(POLICY_RELATIVE_PATH),
        exists=policy_path.exists(),
        readable=not policy_unreadable,
        digest=_digest_file(policy_path),
    )
    if policy_unreadable:
        reasons.append("policy_invalid")

    # --- access ledger (required path, may not exist yet) ---
    access_entries, access_corrupt = _read_access_entries(resolved)
    access_unreadable = access_entries is None
    access_path = resolved / ACCESS_LEDGER_PATH
    access_store = StoreFact(
        path=str(ACCESS_LEDGER_PATH),
        exists=access_path.exists(),
        readable=not access_unreadable,
        digest=_digest_file(access_path),
        count=len(access_entries) if access_entries is not None else None,
        corrupt_lines=access_corrupt,
    )
    if access_unreadable:
        reasons.append("access_ledger_unreadable")
    if access_corrupt:
        reasons.append("access_ledger_corrupt")

    # --- pairing file (optional: absence is not a failure) ---
    pairing_path = resolved / PAIRING_RELATIVE_PATH
    pairing_record = load_pairing(resolved)
    pairing_present_but_invalid = pairing_path.exists() and pairing_record is None
    pairing_store = StoreFact(
        path=str(PAIRING_RELATIVE_PATH),
        exists=pairing_path.exists(),
        readable=not pairing_present_but_invalid,
        digest=_digest_file(pairing_path),
    )
    if pairing_present_but_invalid:
        reasons.append("pairing_invalid")

    # --- distinct caller identities observed in the access ledger ---
    buckets: dict[str, dict[str, Any]] = {}
    for entry in access_entries or []:
        raw_caller = entry.get("caller_id")
        caller_id = raw_caller if isinstance(raw_caller, str) else None
        identity = _caller_identity(caller_id)
        bucket = buckets.setdefault(
            identity,
            {"identity": identity, "caller_id": caller_id, "calls": 0, "tools": set()},
        )
        bucket["calls"] += 1
        tool_name = entry.get("tool_name")
        if isinstance(tool_name, str) and tool_name:
            bucket["tools"].add(tool_name)

    caller_list = [
        {
            "identity": bucket["identity"],
            "caller_id": bucket["caller_id"],
            "calls": bucket["calls"],
            "tools": sorted(bucket["tools"]),
        }
        for bucket in sorted(buckets.values(), key=lambda b: str(b["identity"]))
    ]
    hosts_observed = len(caller_list)

    # --- do different callers' hyodo_event_record calls land in the one ledger? ---
    event_record_calls_per_caller = {
        bucket["identity"]: sum(
            1
            for entry in (access_entries or [])
            if entry.get("tool_name") == "hyodo_event_record"
            and _caller_identity(
                entry.get("caller_id") if isinstance(entry.get("caller_id"), str) else None
            )
            == bucket["identity"]
        )
        for bucket in buckets.values()
    }
    same_ledger = agent_events_store.readable and not events_corrupt

    status = "UNOBSERVED" if reasons else "READY"
    exit_code = 0 if status == "READY" else 2

    return {
        "schema_version": CONTINUITY_SCHEMA_VERSION,
        "status": status,
        "reasons": reasons,
        "root": str(resolved),
        "stores": {
            "agent_events": agent_events_store.to_dict(),
            "policy": policy_store.to_dict(),
            "access_ledger": access_store.to_dict(),
            "pairing": pairing_store.to_dict(),
        },
        "callers": caller_list,
        "hosts": {
            "observed": hosts_observed,
            "expected": expected_hosts,
            "label": f"hosts observed: {hosts_observed}/{expected_hosts} expected",
        },
        "continuity": {
            "same_ledger": same_ledger,
            "agent_events_digest": agent_events_store.digest,
            "event_record_calls_per_caller": event_record_calls_per_caller,
        },
        "remote": {"status": "UNOBSERVED", "reason": "remote_not_probed"},
        "exit_code": exit_code,
    }
