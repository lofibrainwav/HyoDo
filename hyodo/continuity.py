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

A host does not have to be an MCP caller to count: a harness wired through
Claude Code hooks (``hyodo connect claude-code``) writes straight to the
agent-event ledger via ``hyodo event record`` and never touches the MCP
access ledger at all. Every distinct ``actor_id`` recorded there — including
one recorded only under ``--shadow`` — is counted as its own observed host,
grouped under identity ``hook:<actor_id>``, alongside whatever the access
ledger observed.
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


def _hook_identity(actor_id: str) -> str:
    """Return the distinct observed identity label for a hook-recorded actor."""
    return f"hook:{actor_id}"


def _hook_hosts(events: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Group agent-events ledger entries into distinct hook-recorded host identities.

    A host wired through Claude Code hooks (or any harness that stamps
    ``actor_id`` on its own recorded events) never appears in the MCP access
    ledger — it writes straight to the agent-event ledger via
    ``hyodo event record``. Every event with ``actor == "agent"`` and a
    non-empty string ``actor_id`` counts as one call from that host; events
    without an ``actor_id`` (older ledgers, or non-hook callers) contribute
    no host. ``shadow`` is derived from each event's ``policy.shadow`` flag:
    ``True`` when every counted event was shadow-stamped, ``False`` when
    none were, ``"mixed"`` when the host has both.
    """
    buckets: dict[str, dict[str, Any]] = {}
    for event in events or []:
        if not isinstance(event, dict) or event.get("actor") != "agent":
            continue
        actor_id = event.get("actor_id")
        if not isinstance(actor_id, str) or not actor_id:
            continue
        identity = _hook_identity(actor_id)
        bucket = buckets.setdefault(
            identity,
            {"identity": identity, "actor_id": actor_id, "calls": 0, "shadow_values": set()},
        )
        bucket["calls"] += 1
        policy = event.get("policy")
        shadow_flag = bool(isinstance(policy, dict) and policy.get("shadow") is True)
        bucket["shadow_values"].add(shadow_flag)

    hosts: list[dict[str, Any]] = []
    for bucket in sorted(buckets.values(), key=lambda b: str(b["identity"])):
        shadow_values: set[bool] = bucket["shadow_values"]
        if len(shadow_values) > 1:
            shadow: bool | str = "mixed"
        else:
            shadow = next(iter(shadow_values), False)
        hosts.append(
            {
                "identity": bucket["identity"],
                "actor_id": bucket["actor_id"],
                "source": "hook",
                "calls": bucket["calls"],
                "shadow": shadow,
            }
        )
    return hosts


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
    contacts no network.

    Integrity and coverage are two different facts, reported separately so
    "nothing is broken" can never be read as "something was observed":

    - ``integrity_status`` is ``READY`` when every *present* store parses,
      and ``CORRUPT`` when any present store is unreadable or corrupt.
      A wholly empty workspace has perfect integrity — there is nothing to
      be corrupt — so an empty root is ``integrity_status: READY``.
    - ``coverage_status`` is ``OBSERVED`` when at least ``expected_hosts``
      distinct hosts were observed — from either the access ledger's
      callers *or* the agent-event ledger's hook-recorded ``actor_id``
      values, or both combined — *and* the agent-event ledger is present
      and readable *and* (the access ledger is present and readable, or at
      least one hook host was observed); ``UNOBSERVED`` when zero hosts
      were observed and none of the four stores exist yet; and ``PARTIAL``
      for everything in between (some signal, but not full coverage).
    - ``status`` (kept for backward compatibility) is ``READY`` only when
      ``integrity_status`` is ``READY`` *and* ``coverage_status`` is
      ``OBSERVED``; otherwise it is ``UNOBSERVED``. An empty workspace is
      therefore ``status: UNOBSERVED`` even though its integrity is
      ``READY`` — "nothing is broken" is not "continuity is connected".

    Exit code 0 means overall ``status`` is ``READY``; exit code 2 means it
    is ``UNOBSERVED``, whether that is because a store is corrupt or because
    coverage was never observed.

    ``reasons`` is the ``status`` driver: any entry means ``UNOBSERVED``.
    Once coverage reaches ``OBSERVED`` through hook-only hosts, the
    store-absence facts (``access_ledger_absent``, ``pairing_absent``,
    ``policy_absent``, ``agent_events_absent``) stop being appended to
    ``reasons`` — a hook-observed root must still be able to reach
    ``READY``. Those same facts are never dropped, though: ``notes`` is a
    separate, always-present list that carries every store-absence fact
    whenever that store is genuinely absent, regardless of
    ``coverage_status``, plus ``hook_only_observation`` when every observed
    host came from the agent-events ledger and none from the MCP access
    ledger. When ``coverage_status`` is not ``OBSERVED``, the same absence
    fact appears in both ``reasons`` and ``notes`` — that duplication is
    intended: ``reasons`` explains the non-``READY`` verdict, ``notes`` is
    the durable "what's actually absent" inventory that never disappears
    just because coverage was satisfied without it.
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

    mcp_caller_list = [
        {
            "identity": bucket["identity"],
            "caller_id": bucket["caller_id"],
            "source": "mcp",
            "calls": bucket["calls"],
            "tools": sorted(bucket["tools"]),
        }
        for bucket in sorted(buckets.values(), key=lambda b: str(b["identity"]))
    ]

    # --- distinct hook-recorded actors observed in the agent-events ledger ---
    hook_caller_list = _hook_hosts(events)

    caller_list = sorted(
        [*mcp_caller_list, *hook_caller_list], key=lambda caller: str(caller["identity"])
    )
    hosts_observed = len(mcp_caller_list) + len(hook_caller_list)
    hosts_by_source = {"mcp": len(mcp_caller_list), "hook": len(hook_caller_list)}

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

    # --- integrity: do the stores that exist parse cleanly? ---
    integrity_status = "CORRUPT" if reasons else "READY"

    # --- coverage: was continuity actually observed, or is nothing here yet? ---
    any_store_present = (
        agent_events_store.exists
        or policy_store.exists
        or access_store.exists
        or pairing_store.exists
    )
    access_ledger_ready = access_store.exists and access_store.readable
    required_stores_ready = (
        agent_events_store.exists
        and agent_events_store.readable
        and (access_ledger_ready or len(hook_caller_list) > 0)
    )
    if hosts_observed >= expected_hosts and required_stores_ready:
        coverage_status = "OBSERVED"
    elif hosts_observed == 0 and not any_store_present:
        coverage_status = "UNOBSERVED"
    else:
        coverage_status = "PARTIAL"

    if hosts_observed == 0:
        reasons.append("hosts_unobserved")
    elif hosts_observed < expected_hosts:
        reasons.append("hosts_partial")

    if coverage_status != "OBSERVED":
        if not agent_events_store.exists:
            reasons.append("agent_events_absent")
        if not access_store.exists:
            reasons.append("access_ledger_absent")
        if not pairing_store.exists:
            reasons.append("pairing_absent")
        if not policy_store.exists:
            reasons.append("policy_absent")

    # --- notes: non-blocking facts, always present regardless of coverage ---
    # `reasons` drives `status` (any entry means UNOBSERVED), so once
    # coverage reaches OBSERVED through hook-only hosts the absence facts
    # above stop being appended there — a hook-observed root must still be
    # able to reach READY. `notes` carries the same store-absence facts
    # unconditionally, so a reader never loses "the access ledger doesn't
    # exist" just because coverage was satisfied without it. When coverage
    # is not OBSERVED, the same fact appears in both `reasons` and `notes`
    # — that duplication is intended: `reasons` explains the non-READY
    # verdict, `notes` is the durable inventory of what's absent.
    notes: list[str] = []
    if not agent_events_store.exists:
        notes.append("agent_events_absent")
    if not access_store.exists:
        notes.append("access_ledger_absent")
    if not pairing_store.exists:
        notes.append("pairing_absent")
    if not policy_store.exists:
        notes.append("policy_absent")
    if hosts_observed > 0 and len(mcp_caller_list) == 0 and len(hook_caller_list) > 0:
        notes.append("hook_only_observation")

    status = (
        "READY" if integrity_status == "READY" and coverage_status == "OBSERVED" else "UNOBSERVED"
    )
    exit_code = 0 if status == "READY" else 2

    return {
        "schema_version": CONTINUITY_SCHEMA_VERSION,
        "status": status,
        "integrity_status": integrity_status,
        "coverage_status": coverage_status,
        "reasons": reasons,
        "notes": notes,
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
            "by_source": hosts_by_source,
        },
        "continuity": {
            "same_ledger": same_ledger,
            "agent_events_digest": agent_events_store.digest,
            "event_record_calls_per_caller": event_record_calls_per_caller,
        },
        "remote": {"status": "UNOBSERVED", "reason": "remote_not_probed"},
        "exit_code": exit_code,
    }
