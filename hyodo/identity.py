"""Portable identity for a running HyoDo dashboard.

The identity is an observation receipt, not a control-plane command.  It binds
the target checkout, measuring source, connect state, and agent ledger into one
machine-readable response so consumers cannot silently choose another HyoDo
checkout.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hyodo import __version__
from hyodo.connect import CONNECT_RELATIVE_PATH, check_status
from hyodo.events import AGENT_EVENT_SCHEMA_VERSION, AGENT_EVENTS_RELATIVE_PATH, read_agent_events
from hyodo.provenance import path_digest, resolve_provenance

RUNTIME_IDENTITY_SCHEMA_VERSION = "hyodo.runtime-identity/v1"


def _connect_identity(root: Path) -> dict[str, Any]:
    path = root / CONNECT_RELATIVE_PATH
    if not path.exists():
        return {"state": "ABSENT", "schema_version": None, "targets": []}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {"state": "UNOBSERVED", "schema_version": None, "targets": []}
    if not isinstance(raw, dict):
        return {"state": "UNOBSERVED", "schema_version": None, "targets": []}
    reports = check_status(root)
    return {
        "state": "PRESENT",
        "schema_version": raw.get("schema_version"),
        "targets": [
            {
                "name": item.target,
                "status": item.status,
                "drift": item.status != "ok",
            }
            for item in reports
        ],
    }


def _ledger_identity(root: Path) -> dict[str, Any]:
    path = root / AGENT_EVENTS_RELATIVE_PATH
    if not path.exists():
        return {
            "state": "ABSENT",
            "schema_version": AGENT_EVENT_SCHEMA_VERSION,
            "path_digest": path_digest(path),
            "events": 0,
            "corrupt_lines": 0,
        }
    events, corrupt = read_agent_events(root)
    if events is None:
        return {
            "state": "UNOBSERVED",
            "schema_version": None,
            "path_digest": path_digest(path),
            "events": None,
            "corrupt_lines": None,
        }
    schema = {event.get("schema_version") for event in events}
    schema_value = next(iter(schema)) if len(schema) == 1 else None
    return {
        "state": "OBSERVED",
        "schema_version": schema_value,
        "path_digest": path_digest(path),
        "events": len(events),
        "corrupt_lines": corrupt,
    }


def build_runtime_identity(
    root: Path,
    *,
    endpoint: str = "127.0.0.1:8768",
    http_observed: bool = True,
) -> dict[str, Any]:
    """Return a portable, read-only identity receipt for *root*."""
    target = Path(root).resolve()
    provenance = resolve_provenance(target).to_portable_dict()
    return {
        "schema_version": RUNTIME_IDENTITY_SCHEMA_VERSION,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "service": {
            "name": "hyodo-dashboard",
            "endpoint": endpoint,
            "http_observed": http_observed,
        },
        "target": {
            # This endpoint is loopback-only; the real path is intentionally
            # local detail, while portable consumers should use root_digest.
            "root_realpath": str(target),
            "root_digest": path_digest(target),
            "git_commit": provenance.get("target_commit"),
            "git_dirty": provenance.get("target_dirty"),
        },
        "measurer": {
            "tool_name": provenance.get("tool_name"),
            "tool_version": __version__,
            "source_commit": provenance.get("tool_commit"),
            "source_dirty": provenance.get("tool_dirty"),
            "install_mode": provenance.get("install_mode"),
        },
        "provenance": {
            "schema_version": provenance.get("schema_version"),
            "relation": provenance.get("relation"),
            "validity": provenance.get("validity"),
        },
        "connect": _connect_identity(target),
        "connect_state_path": str(CONNECT_RELATIVE_PATH),
        "ledger_path": str(AGENT_EVENTS_RELATIVE_PATH),
        "ledger": _ledger_identity(target),
        "runtime": {"pid": os.getpid()},
    }
