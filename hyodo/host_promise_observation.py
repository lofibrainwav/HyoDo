"""Consumer contract for a host-supplied Promise observation (`hyodo.host-promise-observation/v0`).

HyoDo is public and host-neutral. A host that owns Promise state (its own store,
its own authority evidence) may hand HyoDo a *projection* of that state; HyoDo
validates the projection's shape and renders it beside its own evidence. HyoDo
never reads a host's private stores, never treats the projection as authority
or as proof of fulfillment, and never renders what it did not ask for.

Design rules (all fail closed to ``UNOBSERVED`` — an unreadable or invalid
projection is *not* "no promise"):

* **Allowlist, not blocklist.** Only the fields below are read. Anything else —
  including free text such as a commitment, a delegation list, or a receipt id —
  is dropped before rendering and counted in ``dropped_fields`` so the drop is
  visible, never silent. Privacy is minimised at the consumer, not trusted to
  the producer.
* **Authority is always NONE.** A projection that claims anything else is
  rejected: HyoDo does not accept a host's word that it is authoritative.
* **Observed absence is not non-observation.** ``source OBSERVED`` with no
  active Promise is ``NONE``; a missing, unreadable, or inconsistent projection
  is ``UNOBSERVED``. Neither is treated as success.
* **Internal consistency is checked.** A producer cannot report a rail stage as
  ``OBSERVED`` while its own source is ``UNOBSERVED`` or ``NONE``.
* **Supply is limited to three rail stages** (Promise, Contract, Boundaries).
  Action, Artifact, Evidence, and Readback come from HyoDo's own evidence;
  Trust stays a human judgment. A projection cannot fill them.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

HOST_PROMISE_SCHEMA = "hyodo.host-promise-observation/v0"
#: Location HyoDo looks in, relative to the evidence root. The host writes it;
#: HyoDo never reaches into any host-private directory.
HOST_PROMISE_RELATIVE_PATH = Path(".hyodo") / "host-promise-observation.json"

STAGE_STATES = frozenset({"OBSERVED", "NONE", "UNOBSERVED"})
RESOLUTIONS = frozenset({"ACTIVE", "NONE", "AMBIGUOUS", "UNOBSERVED"})
AUTHORITY_STATES = frozenset(
    {"VERIFIED_DIRECT_HUMAN", "NOT_SUFFICIENT", "UNVERIFIED", "UNOBSERVED"}
)
PROMISE_STATUSES = frozenset(
    {"OPEN", "KEPT", "PARTIAL", "BROKEN", "UNOBSERVED", "SUPERSEDED_BY_HUMAN", "TRANSFERRED"}
)
#: The only rail stages a host may supply.
SUPPLIED_STAGES = ("promise", "contract", "boundaries")

MAX_BYTES = 256 * 1024
MAX_PROMISES = 200
MAX_NOTE = 200
_LABEL_RE = re.compile(r"^[A-Za-z0-9._:@-]{1,64}$")
_ID_RE = re.compile(r"^[A-Za-z0-9._-]{3,80}$")
_COUNT_KEYS = ("auto", "ask", "must_not", "completion_conditions")
_TOP_ALLOWED = frozenset(
    {
        "schema",
        "producer",
        "observed_at",
        "authority",
        "source",
        "active_promise",
        "rail",
        "promises",
    }
)


def _unobserved(reason: str) -> dict[str, Any]:
    return {"state": "UNOBSERVED", "reason": reason[:MAX_NOTE]}


def _text(value: Any, limit: int = MAX_NOTE) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = "".join(ch if ch.isprintable() else " " for ch in value).strip()
    return cleaned[:limit] or None


def _dropped(container: dict[str, Any], allowed: frozenset[str] | set[str]) -> int:
    return sum(1 for key in container if key not in allowed)


def _count(value: Any) -> int | None:
    return (
        value
        if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 10_000
        else None
    )


def _delegation_counts(raw: Any, dropped: list[int]) -> dict[str, int] | None:
    """Counts only. A producer that sends the lists themselves has them dropped."""
    if not isinstance(raw, dict):
        return None
    dropped[0] += _dropped(raw, set(_COUNT_KEYS))
    counts = {key: _count(raw.get(key)) for key in _COUNT_KEYS}
    return (
        None
        if any(v is None for v in counts.values())
        else {k: int(v or 0) for k, v in counts.items()}
    )


def _normalise_promise(raw: Any, dropped: list[int]) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    allowed = {"promise_id", "status", "corrupt", "authority_state", "delegation_counts"}
    dropped[0] += _dropped(raw, allowed)
    promise_id = raw.get("promise_id")
    status = raw.get("status")
    if not (isinstance(promise_id, str) and _ID_RE.fullmatch(promise_id)):
        return None
    if status not in PROMISE_STATUSES:
        return None
    corrupt = raw.get("corrupt") is True
    authority_state = raw.get("authority_state")
    if authority_state not in AUTHORITY_STATES:
        return None
    return {
        "promise_id": promise_id,
        "status": status,
        "corrupt": corrupt,
        "authority_state": authority_state,
        "delegation_counts": None
        if corrupt
        else _delegation_counts(raw.get("delegation_counts"), dropped),
    }


def _normalise_rail(raw: Any, dropped: list[int]) -> dict[str, dict[str, Any]] | None:
    if not isinstance(raw, dict):
        return None
    # A host may not supply Action / Artifact / Evidence / Readback / Trust: those keys are dropped, not rendered.
    dropped[0] += _dropped(raw, set(SUPPLIED_STAGES))
    rail: dict[str, dict[str, Any]] = {}
    for stage in SUPPLIED_STAGES:
        entry = raw.get(stage)
        if not isinstance(entry, dict) or entry.get("state") not in STAGE_STATES:
            return None
        dropped[0] += _dropped(entry, {"state", "note"})
        rail[stage] = {"state": entry["state"], "note": _text(entry.get("note"))}
    return rail


def _inconsistent(
    source_state: str, resolution: str, rail: dict[str, dict[str, Any]]
) -> str | None:
    """A producer must not contradict itself. Returns a reason or None."""
    states = {rail[s]["state"] for s in SUPPLIED_STAGES}
    if source_state == "UNOBSERVED" and states != {"UNOBSERVED"}:
        return "source UNOBSERVED but a rail stage claims a state"
    if resolution == "ACTIVE" and states != {"OBSERVED"}:
        return "active promise but rail stages are not all OBSERVED"
    if resolution == "NONE" and states != {"NONE"}:
        return "no active promise but rail stages are not all NONE"
    if resolution in {"AMBIGUOUS", "UNOBSERVED"} and states != {"UNOBSERVED"}:
        return f"{resolution} but rail stages are not all UNOBSERVED"
    return None


def parse_host_promise_observation(raw: Any) -> dict[str, Any]:
    """Validate and minimise a projection. Never raises: invalid input is ``UNOBSERVED`` with a reason.

    The result always carries ``state`` (``OBSERVED`` when a valid projection was read, otherwise
    ``UNOBSERVED``) so a caller cannot mistake a rejection for "no promise".
    """
    if not isinstance(raw, dict):
        return _unobserved("host promise observation is not an object")
    if raw.get("schema") != HOST_PROMISE_SCHEMA:
        return _unobserved("unsupported host promise observation schema")
    dropped = [_dropped(raw, _TOP_ALLOWED)]
    if raw.get("authority") != "NONE":
        return _unobserved("a host promise observation must declare authority NONE")

    producer = raw.get("producer")
    if not isinstance(producer, dict):
        return _unobserved("producer missing")
    dropped[0] += _dropped(producer, {"host", "schema_version"})
    host = producer.get("host")
    if not (isinstance(host, str) and _LABEL_RE.fullmatch(host)):
        return _unobserved("producer host label is not an opaque label")
    version = _text(producer.get("schema_version"), 64)

    source = raw.get("source")
    if not isinstance(source, dict) or source.get("state") not in {"OBSERVED", "UNOBSERVED"}:
        return _unobserved("source state missing")
    dropped[0] += _dropped(source, {"state", "reason", "problem_count"})
    problem_count = _count(source.get("problem_count")) or 0

    active = raw.get("active_promise")
    if not isinstance(active, dict) or active.get("resolution") not in RESOLUTIONS:
        return _unobserved("active_promise resolution missing")
    dropped[0] += _dropped(active, {"resolution", "promise_id"})
    active_id = active.get("promise_id")
    if active_id is not None and not (isinstance(active_id, str) and _ID_RE.fullmatch(active_id)):
        return _unobserved("active promise id is not an opaque id")
    if active["resolution"] == "ACTIVE" and active_id is None:
        return _unobserved("ACTIVE without a promise id")

    rail = _normalise_rail(raw.get("rail"), dropped)
    if rail is None:
        return _unobserved("rail stages missing or invalid")
    contradiction = _inconsistent(source["state"], active["resolution"], rail)
    if contradiction:
        return _unobserved(f"inconsistent projection: {contradiction}")

    raw_promises = raw.get("promises")
    if not isinstance(raw_promises, list) or len(raw_promises) > MAX_PROMISES:
        return _unobserved("promises missing or too many")
    promises = [_normalise_promise(p, dropped) for p in raw_promises]
    if any(p is None for p in promises):
        return _unobserved("a promise entry is malformed")

    return {
        "state": "OBSERVED",
        "schema": HOST_PROMISE_SCHEMA,
        "producer": {"host": host, "schema_version": version},
        "observed_at": _text(raw.get("observed_at"), 40),
        "authority": "NONE",
        "source_state": source["state"],
        "problem_count": problem_count,
        "resolution": active["resolution"],
        "promise_id": active_id,
        "rail": rail,
        "promises": promises,
        "dropped_fields": dropped[0],
    }


def load_host_promise_observation(root: Path | None) -> dict[str, Any] | None:
    """Read ``<root>/.hyodo/host-promise-observation.json``.

    Returns ``None`` when the file does not exist — nothing was supplied, and the
    rail keeps its existing ``UNOBSERVED`` labels. A present-but-unreadable,
    oversized, or invalid file returns an ``UNOBSERVED`` result with a reason;
    it is never converted into an absence.
    """
    if root is None:
        return None
    path = Path(root) / HOST_PROMISE_RELATIVE_PATH
    try:
        stat = path.stat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        return _unobserved(f"host promise observation unreadable: {type(exc).__name__}")
    if not path.is_file() or stat.st_size > MAX_BYTES:
        return _unobserved("host promise observation is not a regular file or too large")
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return _unobserved("host promise observation is not valid JSON")
    return parse_host_promise_observation(parsed)
