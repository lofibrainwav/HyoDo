"""Privacy-first local friction derivation for HyoDo agent-event traces.

This module intentionally has **no network transport**. It converts local
``hyodo.agent-event/v1`` rows into coarse, allow-listed
``hyodo.friction-contribution/v1`` records that contain no raw prompt/response,
source code, diff, path, secret, event id, run id, actor id, or exact timestamp.

Population evidence produced from this contract is a support signal only. It
must never grant execution authority, override local policy, or override an
evidence gate.
"""

from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hyodo import __version__
from hyodo.events import AGENT_EVENT_SCHEMA_VERSION, read_agent_events

FRICTION_CONTRIBUTION_SCHEMA_VERSION = "hyodo.friction-contribution/v1"
FRICTION_STATE_SCHEMA_VERSION = "hyodo.friction-state/v1"
FRICTION_STATE_RELATIVE_PATH = Path(".hyodo") / "friction-contribution.json"
FRICTION_EXPORT_SCHEMA_VERSION = "hyodo.friction-export/v1"
FRICTION_EXPORT_RELATIVE_PATH = Path(".hyodo") / "friction-export.json"
NETWORK_TRANSPORT = "disabled"

TASK_CLASSES = frozenset(
    {
        "code_change",
        "dependency_update",
        "test",
        "docs",
        "research",
        "data",
        "deployment",
        "external_write",
        "read_only",
        "unknown",
    }
)
RISK_BUCKETS = frozenset({"low", "medium", "high", "unknown"})
ORCHESTRATION_PATTERNS = frozenset({"serial", "multi_actor_serial", "fanout", "unknown"})
COUNT_BUCKETS = frozenset({"0", "1", "2-3", "4-7", "8+"})
EVENT_COUNT_BUCKETS = frozenset({"1-3", "4-7", "8-15", "16-31", "32+"})
PARALLELISM_BUCKETS = frozenset({"1", "2", "3-4", "5+", "unknown"})
WAIT_BUCKETS = frozenset({"none", "0-30s", "30-60s", "1-5m", "5m+", "unresolved", "unobserved"})
EVIDENCE_STATES = frozenset({"complete", "partial", "missing", "unobserved"})
OUTCOMES = frozenset({"pass", "fail", "blocked", "needs_human", "unknown"})
PROVIDER_CLASSES = frozenset({"openai", "anthropic", "google", "xai", "meta", "other", "unknown"})
SOURCE_QUALITIES = frozenset({"complete", "corrupt"})

CONTRIBUTION_FIELDS = frozenset(
    {
        "schema",
        "source_schema",
        "hyodo_version",
        "task_class",
        "risk_bucket",
        "orchestration_pattern",
        "event_count_bucket",
        "parallelism_bucket",
        "retry_bucket",
        "rework_bucket",
        "verification_failure_bucket",
        "human_intervention_bucket",
        "approval_wait_bucket",
        "resource_conflict_bucket",
        "evidence_completeness",
        "outcome",
        "provider_class",
        "source_quality",
    }
)

# JSON Schema is kept as a Python constant so the installed wheel and the CLI
# share one exact contract. ``hyodo friction contract --json`` emits this
# object verbatim.
FRICTION_CONTRIBUTION_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://hyodo.app/schema/friction-contribution-v1.json",
    "title": "HyoDo Friction Contribution v1",
    "type": "object",
    "additionalProperties": False,
    "required": sorted(CONTRIBUTION_FIELDS),
    "properties": {
        "schema": {"const": FRICTION_CONTRIBUTION_SCHEMA_VERSION},
        "source_schema": {"const": AGENT_EVENT_SCHEMA_VERSION},
        "hyodo_version": {
            "type": "string",
            "pattern": r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?$",
        },
        "task_class": {"enum": sorted(TASK_CLASSES)},
        "risk_bucket": {"enum": sorted(RISK_BUCKETS)},
        "orchestration_pattern": {"enum": sorted(ORCHESTRATION_PATTERNS)},
        "event_count_bucket": {"enum": sorted(EVENT_COUNT_BUCKETS)},
        "parallelism_bucket": {"enum": sorted(PARALLELISM_BUCKETS)},
        "retry_bucket": {"enum": sorted(COUNT_BUCKETS)},
        "rework_bucket": {"enum": sorted(COUNT_BUCKETS)},
        "verification_failure_bucket": {"enum": sorted(COUNT_BUCKETS)},
        "human_intervention_bucket": {"enum": sorted(COUNT_BUCKETS)},
        "approval_wait_bucket": {"enum": sorted(WAIT_BUCKETS)},
        "resource_conflict_bucket": {"enum": sorted(COUNT_BUCKETS)},
        "evidence_completeness": {"enum": sorted(EVIDENCE_STATES)},
        "outcome": {"enum": sorted(OUTCOMES)},
        "provider_class": {"enum": sorted(PROVIDER_CLASSES)},
        "source_quality": {"enum": sorted(SOURCE_QUALITIES)},
    },
}


@dataclass(frozen=True)
class FrictionState:
    """Local contribution preparation state.

    ``enabled`` never implies network consent in v1. A future network collector
    must require a new, explicit consent action rather than inheriting this bit.
    """

    enabled: bool
    state: str
    network_consent: bool = False
    consent_scope: str = "local_only_v1"

    def as_dict(self) -> dict[str, Any]:
        """Serialize the local state without adding network authority."""
        return {
            "schema": FRICTION_STATE_SCHEMA_VERSION,
            "enabled": self.enabled,
            "state": self.state,
            "network_consent": self.network_consent,
            "consent_scope": self.consent_scope,
            "network_transport": NETWORK_TRANSPORT,
        }


def _count_bucket(value: int) -> str:
    if value <= 0:
        return "0"
    if value == 1:
        return "1"
    if value <= 3:
        return "2-3"
    if value <= 7:
        return "4-7"
    return "8+"


def _event_count_bucket(value: int) -> str:
    if value <= 3:
        return "1-3"
    if value <= 7:
        return "4-7"
    if value <= 15:
        return "8-15"
    if value <= 31:
        return "16-31"
    return "32+"


def _parallelism_bucket(value: int | None) -> str:
    if value is None:
        return "unknown"
    if value <= 1:
        return "1"
    if value == 2:
        return "2"
    if value <= 4:
        return "3-4"
    return "5+"


def _parse_ts(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _tags(event: dict[str, Any]) -> set[str]:
    meta = event.get("meta")
    if not isinstance(meta, dict):
        return set()
    raw = meta.get("tags")
    if not isinstance(raw, list):
        return set()
    return {tag.strip().lower() for tag in raw if isinstance(tag, str) and tag.strip()}


def _tool(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("tool")
    return value if isinstance(value, dict) else {}


def _measured_decision(event: dict[str, Any]) -> str | None:
    policy = event.get("policy")
    if not isinstance(policy, dict):
        return None
    # Caller-asserted policy claims are quarantined in events.py. Only a block
    # carrying evaluator provenance is allowed to influence derived metrics.
    evaluated_by = policy.get("evaluated_by")
    decision = policy.get("decision")
    if not isinstance(evaluated_by, str) or not evaluated_by.strip():
        return None
    if decision in {"ALLOW", "DENY", "ASK", "UNOBSERVED"}:
        return str(decision)
    return None


def _task_class(events: list[dict[str, Any]]) -> str:
    for event in events:
        for tag in _tags(event):
            if tag.startswith("task:"):
                candidate = tag.split(":", 1)[1]
                if candidate in TASK_CLASSES and candidate != "unknown":
                    return candidate
    methods = {
        method for event in events if isinstance((method := _tool(event).get("method")), str)
    }
    if methods & {"POST", "PUT", "PATCH", "DELETE"}:
        return "external_write"
    if methods and methods <= {"GET", "HEAD"}:
        return "read_only"
    return "unknown"


def _risk_bucket(events: list[dict[str, Any]]) -> str:
    for event in events:
        for tag in _tags(event):
            if tag in {"risk:low", "risk:medium", "risk:high"}:
                return tag.split(":", 1)[1]

    methods: set[str] = set()
    credential_shaped = False
    for event in events:
        tool = _tool(event)
        method = tool.get("method")
        if isinstance(method, str):
            methods.add(method)
        urls = tool.get("urls")
        if isinstance(urls, list):
            credential_shaped = credential_shaped or any(
                isinstance(entry, dict) and entry.get("credential_shaped") is True for entry in urls
            )
    if credential_shaped or "DELETE" in methods:
        return "high"
    if methods & {"POST", "PUT", "PATCH"}:
        return "medium"
    if methods and methods <= {"GET", "HEAD"}:
        return "low"
    return "unknown"


def _provider_class(events: list[dict[str, Any]]) -> str:
    models: list[str] = []
    for event in events:
        meta = event.get("meta")
        if isinstance(meta, dict) and isinstance(meta.get("model"), str):
            models.append(meta["model"].lower())
    if not models:
        return "unknown"
    joined = " ".join(models)
    if any(token in joined for token in ("gpt", "codex", "o1", "o3", "o4", "openai")):
        return "openai"
    if "claude" in joined or "anthropic" in joined:
        return "anthropic"
    if "gemini" in joined or "google" in joined:
        return "google"
    if "grok" in joined or "xai" in joined:
        return "xai"
    if "llama" in joined or "meta" in joined:
        return "meta"
    return "other"


def _orchestration(events: list[dict[str, Any]]) -> tuple[str, str]:
    actor_ids = {
        actor_id
        for event in events
        if isinstance((actor_id := event.get("actor_id")), str) and actor_id
    }
    by_step: dict[int, set[str]] = {}
    duplicate_step_without_identity = False
    raw_step_counts: dict[int, int] = {}
    for event in events:
        step = event.get("step_index")
        if not isinstance(step, int) or isinstance(step, bool):
            continue
        raw_step_counts[step] = raw_step_counts.get(step, 0) + 1
        actor_id = event.get("actor_id")
        if isinstance(actor_id, str) and actor_id:
            by_step.setdefault(step, set()).add(actor_id)
    for step, count in raw_step_counts.items():
        if count > 1 and len(by_step.get(step, set())) < 2:
            duplicate_step_without_identity = True

    max_parallel = max((len(value) for value in by_step.values()), default=1)
    if max_parallel >= 2:
        return "fanout", _parallelism_bucket(max_parallel)
    if duplicate_step_without_identity:
        return "unknown", "unknown"
    if len(actor_ids) >= 2:
        return "multi_actor_serial", "1"
    return "serial", "1"


def _approval_wait_bucket(events: list[dict[str, Any]]) -> str:
    ask_events = [event for event in events if _measured_decision(event) == "ASK"]
    if not ask_events:
        return "none"

    human_events = [event for event in events if event.get("actor") == "human"]
    waits: list[float] = []
    saw_bad_timestamp = False
    for ask in ask_events:
        ask_ts = _parse_ts(ask.get("ts"))
        if ask_ts is None:
            saw_bad_timestamp = True
            continue
        candidates: list[float] = []
        for human in human_events:
            human_ts = _parse_ts(human.get("ts"))
            if human_ts is None:
                saw_bad_timestamp = True
                continue
            try:
                seconds = (human_ts - ask_ts).total_seconds()
            except TypeError:
                saw_bad_timestamp = True
                continue
            if seconds >= 0:
                candidates.append(seconds)
        if candidates:
            waits.append(min(candidates))
    if len(waits) < len(ask_events):
        return "unobserved" if saw_bad_timestamp else "unresolved"

    worst = max(waits)
    if worst <= 30:
        return "0-30s"
    if worst <= 60:
        return "30-60s"
    if worst <= 300:
        return "1-5m"
    return "5m+"


def _evidence_completeness(events: list[dict[str, Any]]) -> str:
    eligible = [
        event for event in events if event.get("kind") in {"tool_result", "decision", "error"}
    ]
    if not eligible:
        return "unobserved"
    observed = sum(
        1
        for event in eligible
        if isinstance(event.get("evidence_refs"), list) and bool(event.get("evidence_refs"))
    )
    if observed == len(eligible):
        return "complete"
    if observed == 0:
        return "missing"
    return "partial"


def _outcome(events: list[dict[str, Any]]) -> str:
    measured = [decision for event in events if (decision := _measured_decision(event))]
    if measured:
        last = measured[-1]
        if last == "ALLOW":
            return "pass"
        if last == "DENY":
            return "blocked"
        if last in {"ASK", "UNOBSERVED"}:
            return "needs_human"
    if any(event.get("kind") == "error" for event in events):
        return "fail"
    return "unknown"


def _tagged_count(events: list[dict[str, Any]], marker: str) -> int:
    return sum(
        1
        for event in events
        if any(tag == marker or tag.startswith(marker + ":") for tag in _tags(event))
    )


def derive_run_contribution(
    events: list[dict[str, Any]], *, source_quality: str = "complete"
) -> dict[str, Any]:
    """Derive one privacy-transformed contribution from one run's events."""
    ordered = sorted(
        events,
        key=lambda event: (
            event.get("step_index") if isinstance(event.get("step_index"), int) else 2**31,
            event.get("ts") if isinstance(event.get("ts"), str) else "",
        ),
    )
    orchestration_pattern, parallelism_bucket = _orchestration(ordered)
    retry_count = _tagged_count(ordered, "retry")
    rework_count = _tagged_count(ordered, "rework")
    resource_conflicts = _tagged_count(ordered, "resource_conflict")
    verification_failures = sum(
        1
        for event in ordered
        if (
            event.get("kind") == "error"
            and bool(_tags(event) & {"verification", "gate", "verification_failure"})
        )
        or (
            _measured_decision(event) == "DENY"
            and bool(_tags(event) & {"verification", "gate", "verification_failure"})
        )
    )
    human_interventions = sum(1 for event in ordered if event.get("actor") == "human")

    contribution: dict[str, Any] = {
        "schema": FRICTION_CONTRIBUTION_SCHEMA_VERSION,
        "source_schema": AGENT_EVENT_SCHEMA_VERSION,
        "hyodo_version": __version__,
        "task_class": _task_class(ordered),
        "risk_bucket": _risk_bucket(ordered),
        "orchestration_pattern": orchestration_pattern,
        "event_count_bucket": _event_count_bucket(max(1, len(ordered))),
        "parallelism_bucket": parallelism_bucket,
        "retry_bucket": _count_bucket(retry_count),
        "rework_bucket": _count_bucket(rework_count),
        "verification_failure_bucket": _count_bucket(verification_failures),
        "human_intervention_bucket": _count_bucket(human_interventions),
        "approval_wait_bucket": _approval_wait_bucket(ordered),
        "resource_conflict_bucket": _count_bucket(resource_conflicts),
        "evidence_completeness": _evidence_completeness(ordered),
        "outcome": _outcome(ordered),
        "provider_class": _provider_class(ordered),
        "source_quality": source_quality if source_quality in SOURCE_QUALITIES else "corrupt",
    }
    ok, reasons = validate_contribution(contribution)
    if not ok:  # pragma: no cover - internal construction invariant
        raise ValueError("invalid derived contribution: " + ",".join(reasons))
    return contribution


def validate_contribution(payload: Any) -> tuple[bool, list[str]]:
    """Validate the strict allow-listed v1 contribution shape without free text."""
    if not isinstance(payload, dict):
        return False, ["not_an_object"]
    reasons: list[str] = []
    keys = set(payload)
    if keys != CONTRIBUTION_FIELDS:
        for missing in sorted(CONTRIBUTION_FIELDS - keys):
            reasons.append(f"missing_field:{missing}")
        for extra in sorted(keys - CONTRIBUTION_FIELDS):
            reasons.append(f"forbidden_field:{extra}")
    if payload.get("schema") != FRICTION_CONTRIBUTION_SCHEMA_VERSION:
        reasons.append("unsupported_schema")
    if payload.get("source_schema") != AGENT_EVENT_SCHEMA_VERSION:
        reasons.append("unsupported_source_schema")
    version = payload.get("hyodo_version")
    if not isinstance(version, str) or not version:
        reasons.append("invalid_field:hyodo_version")
    enum_checks = {
        "task_class": TASK_CLASSES,
        "risk_bucket": RISK_BUCKETS,
        "orchestration_pattern": ORCHESTRATION_PATTERNS,
        "event_count_bucket": EVENT_COUNT_BUCKETS,
        "parallelism_bucket": PARALLELISM_BUCKETS,
        "retry_bucket": COUNT_BUCKETS,
        "rework_bucket": COUNT_BUCKETS,
        "verification_failure_bucket": COUNT_BUCKETS,
        "human_intervention_bucket": COUNT_BUCKETS,
        "approval_wait_bucket": WAIT_BUCKETS,
        "resource_conflict_bucket": COUNT_BUCKETS,
        "evidence_completeness": EVIDENCE_STATES,
        "outcome": OUTCOMES,
        "provider_class": PROVIDER_CLASSES,
        "source_quality": SOURCE_QUALITIES,
    }
    for field, allowed in enum_checks.items():
        if payload.get(field) not in allowed:
            reasons.append(f"invalid_field:{field}")
    return not reasons, reasons


def derive_contributions(
    root: Path, *, run_id: str | None = None
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Read the local ledger and derive one contribution per observed run.

    ``run_id`` is a local selection filter only; it is never copied into the
    returned contribution.
    """
    events, corrupt_lines = read_agent_events(root)
    if events is None:
        return [], {
            "source": "unreadable",
            "corrupt_lines": 0,
            "runs_observed": 0,
            "network_transport": NETWORK_TRANSPORT,
        }

    groups: dict[str, list[dict[str, Any]]] = {}
    order: list[str] = []
    for event in events:
        event_run_id = event.get("run_id")
        if not isinstance(event_run_id, str) or not event_run_id:
            continue
        if run_id is not None and event_run_id != run_id:
            continue
        if event_run_id not in groups:
            groups[event_run_id] = []
            order.append(event_run_id)
        groups[event_run_id].append(event)

    quality = "corrupt" if corrupt_lines else "complete"
    contributions = [derive_run_contribution(groups[key], source_quality=quality) for key in order]
    return contributions, {
        "source": "observed",
        "corrupt_lines": corrupt_lines,
        "runs_observed": len(contributions),
        "network_transport": NETWORK_TRANSPORT,
    }


def contribution_contract() -> dict[str, Any]:
    """Return an isolated copy of the public v1 JSON Schema contract."""
    return json.loads(json.dumps(FRICTION_CONTRIBUTION_SCHEMA))


def load_friction_state(root: Path) -> FrictionState:
    """Load local state. Missing/malformed state is fail-closed OFF."""
    path = root / FRICTION_STATE_RELATIVE_PATH
    if not path.exists():
        return FrictionState(enabled=False, state="default_off")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return FrictionState(enabled=False, state="unobserved")
    if not isinstance(payload, dict) or payload.get("schema") != FRICTION_STATE_SCHEMA_VERSION:
        return FrictionState(enabled=False, state="unobserved")
    enabled = payload.get("enabled")
    network_consent = payload.get("network_consent")
    consent_scope = payload.get("consent_scope")
    if (
        not isinstance(enabled, bool)
        or network_consent is not False
        or consent_scope != "local_only_v1"
    ):
        return FrictionState(enabled=False, state="unobserved")
    return FrictionState(enabled=enabled, state="enabled" if enabled else "disabled")


def save_friction_state(root: Path, enabled: bool) -> FrictionState:
    """Persist local-only state atomically with owner-only permissions."""
    path = root / FRICTION_STATE_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": FRICTION_STATE_SCHEMA_VERSION,
        "enabled": enabled,
        "network_consent": False,
        "consent_scope": "local_only_v1",
    }
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    if stat.S_IMODE(path.stat().st_mode) != 0o600:
        os.chmod(path, 0o600)
    return FrictionState(enabled=enabled, state="enabled" if enabled else "disabled")


def preview_payload(root: Path, *, run_id: str | None = None) -> dict[str, Any]:
    """Build a local preview receipt. Nothing in this function can transmit data."""
    contributions, observation = derive_contributions(root, run_id=run_id)
    state = load_friction_state(root)
    return {
        "schema": "hyodo.friction-preview/v1",
        "enabled": state.enabled,
        "consent_scope": state.consent_scope,
        "network_consent": False,
        "network_transport": NETWORK_TRANSPORT,
        "nothing_transmitted": True,
        "observation": observation,
        "contributions": contributions,
        "never_export": [
            "prompts",
            "responses",
            "source_code",
            "diffs",
            "file_contents",
            "file_paths",
            "secrets",
            "credentials",
            "emails",
            "raw_command_arguments",
            "raw_event_bodies",
            "event_ids",
            "run_ids",
            "actor_ids",
            "exact_timestamps",
            "persistent_user_ids",
            "persistent_machine_ids",
        ],
        "authority": {
            "may_influence_acl_support": True,
            "may_grant_execution_authority": False,
            "may_override_local_policy": False,
            "may_override_evidence_gate": False,
        },
    }


def friction_export_payload(
    root: Path, *, run_id: str | None = None, exported_at: str | None = None
) -> dict[str, Any]:
    """Build the local export envelope from the exact preview payload.

    ``exported_at`` is envelope metadata only. It is injectable for deterministic
    tests and never carries a run id or any contribution identity.
    """

    preview = preview_payload(root, run_id=run_id)
    return {
        "schema": FRICTION_EXPORT_SCHEMA_VERSION,
        "hyodo_version": __version__,
        "exported_at": exported_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "consent": {
            "enabled": preview["enabled"],
            "network_consent": False,
            "scope": preview["consent_scope"],
        },
        "observation": preview["observation"],
        "contributions": preview["contributions"],
        "never_export": preview["never_export"],
        "authority": preview["authority"],
    }


def write_friction_export(path: Path, payload: dict[str, Any]) -> None:
    """Atomically write one owner-readable local export artifact."""

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    if stat.S_IMODE(path.stat().st_mode) != 0o600:
        os.chmod(path, 0o600)
