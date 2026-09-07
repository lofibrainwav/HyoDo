"""``hyodo connect`` — wire a coding harness to HyoDo's gates.

Dry-run first, ``--write`` to act. This module never re-implements a gate: it
generates harness configuration (Claude Code hooks JSON, a pre-commit repo
entry, a GitHub Actions workflow) that *calls* the ``hyodo`` commands already
shipped elsewhere in this package (``policy check``, ``event record``,
``check``, ``safe``).

Mirrors the ``_detect_X`` pattern already established for gate detection
(``hyodo/gates.py``): one function per target that computes "what would be
written" without writing anything, so dry-run and ``--write`` share one code
path (:func:`plan_target`).

Data lives under ``.hyodo/connect.json`` (schema ``hyodo.connect/v1``): which
targets were written, when, shadow or enforced, and the digest of every file
written — the source of truth :func:`status` reads back to report drift.

Shadow mode (owner decision, 2026-09-06): ``--shadow`` installs the same
Claude Code hooks, but the generated ``PreToolUse`` command carries an extra
``--shadow`` flag. That flag (added to ``hyodo policy check`` and ``hyodo
event record`` in ``hyodo/cli/main.py``) makes the hook record the decision
it *would* have made — stamped ``policy.shadow: true`` — while always exiting
0, so nothing is actually blocked. Leaving shadow mode is a fresh
``hyodo connect claude-code --write`` without ``--shadow``.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypeGuard
from urllib.parse import urlsplit

from hyodo import __version__
from hyodo.events import AGENT_EVENT_SCHEMA_VERSION, content_digest, count_run_events
from hyodo.policy import POLICY_RELATIVE_PATH, POLICY_SCHEMA_ID

CONNECT_SCHEMA_VERSION = "hyodo.connect/v1"
CONNECT_RELATIVE_PATH = Path(".hyodo") / "connect.json"

CLAUDE_SETTINGS_RELATIVE_PATH = Path(".claude") / "settings.json"
PRECOMMIT_CONFIG_RELATIVE_PATH = Path(".pre-commit-config.yaml")
GITHUB_WORKFLOW_RELATIVE_PATH = Path(".github") / "workflows" / "hyodo.yml"

#: Targets this PR actually writes config for (Phase 1-D scope ruling).
WRITABLE_TARGETS = ("claude-code", "pre-commit", "github-actions")
#: Targets whose hook/config contract has not been verified against a live
#: install. ``connect`` never fabricates a config format for these — they are
#: always reported UNOBSERVED, whether detected or explicitly requested.
UNOBSERVED_TARGETS = ("cursor", "codex")
ALL_TARGETS = WRITABLE_TARGETS + UNOBSERVED_TARGETS

HYODO_REPO_URL = "https://github.com/lofibrainwav/HyoDo"
#: Pinned commit for actions/checkout, matching every other workflow this
#: repo ships (see .github/workflows/*.yml) so a drive-by diff review can
#: recognize the same trust boundary immediately.
_CHECKOUT_PIN = "3d3c42e5aac5ba805825da76410c181273ba90b1"  # v7

_PRECOMMIT_MARKER_BEGIN = "  # hyodo:connect:begin"
_PRECOMMIT_MARKER_END = "  # hyodo:connect:end"

#: Command prefixes used both to build the hook command line and to
#: recognize (and safely replace) a HyoDo-owned entry already present in an
#: operator's ``.claude/settings.json`` — never touching hooks HyoDo did not
#: add.
HOOK_PRE_COMMAND_PREFIX = "hyodo policy check --stdin --hook claude-code"
HOOK_POST_COMMAND_PREFIX = "hyodo event record --stdin --hook claude-code"

UNOBSERVED_MESSAGE = (
    "hook/config contract not verified against a live install — UNOBSERVED, nothing written"
)


def _is_str(value: Any) -> TypeGuard[str]:
    return isinstance(value, str) and bool(value.strip())


# --------------------------------------------------------------------------
# Detection
# --------------------------------------------------------------------------


def detect(root: Path) -> dict[str, bool]:
    """Report which harnesses are present in *root* (never writes)."""
    return {
        "claude-code": (root / ".claude").is_dir(),
        "pre-commit": (root / ".pre-commit-config.yaml").is_file(),
        "github-actions": (root / ".github" / "workflows").is_dir(),
    }


# --------------------------------------------------------------------------
# Content builders — one per writable target. Pure functions: given the
# current file content (or None), return the *final* content connect would
# write. The caller diffs current vs. final to decide whether a write is a
# no-op (idempotency).
# --------------------------------------------------------------------------


def _claude_code_hook_command(prefix: str, *, shadow: bool, extra: str = "") -> str:
    command = prefix
    if extra:
        command += f" {extra}"
    if shadow:
        command += " --shadow"
    return command


def _is_owned_hook_entry(entry: Any, owned_prefix: str) -> bool:
    if not isinstance(entry, dict):
        return False
    inner = entry.get("hooks")
    if not isinstance(inner, list):
        return False
    return any(
        isinstance(item, dict)
        and isinstance(item.get("command"), str)
        and item["command"].startswith(owned_prefix)
        for item in inner
    )


def _merge_hook_list(existing: Any, owned_prefix: str, command: str) -> list[Any]:
    entries = list(existing) if isinstance(existing, list) else []
    owned_entry = {"matcher": "*", "hooks": [{"type": "command", "command": command}]}
    for index, entry in enumerate(entries):
        if _is_owned_hook_entry(entry, owned_prefix):
            entries[index] = owned_entry
            return entries
    entries.append(owned_entry)
    return entries


def build_claude_code_settings(existing: dict[str, Any] | None, *, shadow: bool) -> dict[str, Any]:
    """Return the full ``.claude/settings.json`` content, merged key-level.

    Only ``hooks.PreToolUse``/``hooks.PostToolUse`` entries whose command
    HyoDo owns (recognized by prefix) are touched; every other key and every
    other hook entry in the file is passed through unchanged.
    """
    settings: dict[str, Any] = dict(existing) if isinstance(existing, dict) else {}
    existing_hooks = settings.get("hooks")
    hooks: dict[str, Any] = dict(existing_hooks) if isinstance(existing_hooks, dict) else {}
    pre_command = _claude_code_hook_command(
        HOOK_PRE_COMMAND_PREFIX, shadow=shadow, extra="--root ."
    )
    post_command = _claude_code_hook_command(
        HOOK_POST_COMMAND_PREFIX, shadow=shadow, extra="--policy .hyodo/policy.toml"
    )
    hooks["PreToolUse"] = _merge_hook_list(
        hooks.get("PreToolUse"), HOOK_PRE_COMMAND_PREFIX, pre_command
    )
    hooks["PostToolUse"] = _merge_hook_list(
        hooks.get("PostToolUse"), HOOK_POST_COMMAND_PREFIX, post_command
    )
    settings["hooks"] = hooks
    return settings


def _precommit_block() -> str:
    rev = f"v{__version__}"
    return (
        f"{_PRECOMMIT_MARKER_BEGIN}\n"
        f"  - repo: {HYODO_REPO_URL}\n"
        f"    rev: {rev}\n"
        "    hooks:\n"
        "      - id: hyodo-check\n"
        f"{_PRECOMMIT_MARKER_END}\n"
    )


def build_precommit_config(existing_text: str | None) -> str:
    """Return the full ``.pre-commit-config.yaml`` content.

    Merges at the "one HyoDo repo entry" level using marker comments rather
    than a full YAML AST rewrite (PyYAML is a dev-only dependency here, not a
    runtime one) — unrelated repos/hooks in the file are left byte-for-byte
    untouched outside the marked block.
    """
    block = _precommit_block()
    if existing_text is None:
        return f"repos:\n{block}"

    if _PRECOMMIT_MARKER_BEGIN in existing_text and _PRECOMMIT_MARKER_END in existing_text:
        start = existing_text.index(_PRECOMMIT_MARKER_BEGIN)
        end = existing_text.index(_PRECOMMIT_MARKER_END) + len(_PRECOMMIT_MARKER_END)
        # Consume exactly one trailing newline after the end marker, if present,
        # so re-running this doesn't accumulate blank lines.
        if end < len(existing_text) and existing_text[end] == "\n":
            end += 1
        return existing_text[:start] + block + existing_text[end:]

    lines = existing_text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.rstrip("\n") == "repos:":
            return "".join(lines[: index + 1]) + block + "".join(lines[index + 1 :])

    separator = "" if existing_text == "" or existing_text.endswith("\n") else "\n"
    return existing_text + separator + f"repos:\n{block}"


def build_github_actions_workflow() -> str:
    """Return the full ``.github/workflows/hyodo.yml`` content.

    A dedicated new file HyoDo owns outright (not a merge target) — there is
    no pre-existing "hyodo.yml" this could collide with.
    """
    return (
        "name: HyoDo quality gates\n"
        "\n"
        "on:\n"
        "  pull_request:\n"
        "  push:\n"
        "    branches: [main]\n"
        "\n"
        "jobs:\n"
        "  hyodo-check:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        f"      - uses: actions/checkout@{_CHECKOUT_PIN} # v7\n"
        f"      - uses: lofibrainwav/HyoDo/.github/actions/hyodo@v{__version__}\n"
    )


def build_starter_policy() -> str:
    """Return a permissive starter ``.hyodo/policy.toml``.

    Installed by ``hyodo connect claude-code`` only when no policy file is
    already present -- never overwrites an existing one (see
    :func:`plan_target`). Every restriction ships commented out: the
    operator opts in explicitly. ``blocked_path_globs`` is the one
    exception, uncommented, because a starter policy that lets a hook read
    ``.env``/private keys by default undersells "quality gate" -- these are
    the handful of paths almost nobody wants an agent touching.
    """
    return (
        f'schema = "{POLICY_SCHEMA_ID}"\n'
        "\n"
        "# Starter policy installed by `hyodo connect claude-code`.\n"
        "# Permissive by default: nothing else is restricted until you opt in.\n"
        "#\n"
        "# max_steps = 50                     # cap steps per run_id\n"
        '# allowed_tools = ["Read", "Bash"]   # restrict tool calls (unlisted -> DENY)\n'
        "\n"
        "blocked_path_globs = [\n"
        '    ".env",\n'
        '    "*.pem",\n'
        '    "id_rsa*",\n'
        '    ".hyodo/**",\n'
        "]\n"
    )


# --------------------------------------------------------------------------
# Planning — one PlannedFile per file a target touches, dry-run and --write
# share this.
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class PlannedFile:
    """One file ``connect`` would create or modify for a target."""

    path: Path
    content: str
    existed_before: bool
    will_change: bool


@dataclass(frozen=True)
class TargetPlan:
    """The outcome of planning one harness target."""

    name: str
    status: str  # "would_write" | "up_to_date" | "unobserved" | "unknown"
    message: str
    files: tuple[PlannedFile, ...] = field(default_factory=tuple)
    shadow_ignored: bool = False


def _read_text(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _read_json(path: Path) -> dict[str, Any] | None:
    import json

    text = _read_text(path)
    if text is None:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def plan_target(name: str, root: Path, *, shadow: bool) -> TargetPlan:
    """Compute what ``connect`` would do for *name*, writing nothing."""
    if name in UNOBSERVED_TARGETS:
        return TargetPlan(name=name, status="unobserved", message=UNOBSERVED_MESSAGE)
    if name not in WRITABLE_TARGETS:
        return TargetPlan(name=name, status="unknown", message=f"unknown target: {name}")

    import json

    shadow_ignored = False
    extra_files: tuple[PlannedFile, ...] = ()
    if name == "claude-code":
        path = CLAUDE_SETTINGS_RELATIVE_PATH
        existing = _read_json(root / path)
        current_text = _read_text(root / path)
        new_settings = build_claude_code_settings(existing, shadow=shadow)
        content = json.dumps(new_settings, indent=2, sort_keys=True) + "\n"
        # A missing policy.toml is what made shadow mode (and every hook) fail
        # closed with nothing to evaluate against -- bootstrap a permissive
        # starter policy alongside the hooks so a fresh `connect` leaves a
        # working policy in place, never leaving the file absent.
        policy_text = _read_text(root / POLICY_RELATIVE_PATH)
        if policy_text is None:
            extra_files = (
                PlannedFile(
                    path=POLICY_RELATIVE_PATH,
                    content=build_starter_policy(),
                    existed_before=False,
                    will_change=True,
                ),
            )
        elif str(POLICY_RELATIVE_PATH) in _tracked_paths(load_connect_state(root)):
            # HyoDo wrote this policy before (possibly since hand-edited by the
            # operator). Keep tracking it for --status drift, but the content is
            # always exactly what is on disk right now, so this is never a
            # rewrite -- an operator's edits to their own starter policy are
            # never reverted.
            extra_files = (
                PlannedFile(
                    path=POLICY_RELATIVE_PATH,
                    content=policy_text,
                    existed_before=True,
                    will_change=False,
                ),
            )
        # else: a policy.toml already existed that HyoDo never wrote (an
        # operator's own file) -- never overwrite it, and never start tracking
        # it either.
    elif name == "pre-commit":
        path = PRECOMMIT_CONFIG_RELATIVE_PATH
        current_text = _read_text(root / path)
        content = build_precommit_config(current_text)
        shadow_ignored = shadow  # pre-commit always enforces; --shadow is a no-op here.
    else:  # github-actions
        path = GITHUB_WORKFLOW_RELATIVE_PATH
        current_text = _read_text(root / path)
        content = build_github_actions_workflow()
        shadow_ignored = shadow  # CI always enforces; --shadow is a no-op here.

    planned = PlannedFile(
        path=path,
        content=content,
        existed_before=current_text is not None,
        will_change=current_text != content,
    )
    files = (planned, *extra_files)
    status = "would_write" if any(f.will_change for f in files) else "up_to_date"
    messages = [
        (f"{f.path} would be created" if not f.existed_before else f"{f.path} would be updated")
        if f.will_change
        else f"{f.path} already up to date"
        for f in files
    ]
    message = "; ".join(messages)
    return TargetPlan(
        name=name, status=status, message=message, files=files, shadow_ignored=shadow_ignored
    )


# --------------------------------------------------------------------------
# .hyodo/connect.json — the "what did we write" ledger status/drift reads.
# --------------------------------------------------------------------------


def load_connect_state(root: Path) -> dict[str, Any]:
    """Read ``.hyodo/connect.json``, or an empty ``hyodo.connect/v1`` state."""
    empty: dict[str, Any] = {"schema_version": CONNECT_SCHEMA_VERSION, "targets": {}}
    data = _read_json(root / CONNECT_RELATIVE_PATH)
    if data is None or not isinstance(data.get("targets"), dict):
        return empty
    return data


def save_connect_state(root: Path, state: dict[str, Any]) -> None:
    """Write *state* to ``.hyodo/connect.json``, creating the directory if needed."""
    import json

    path = root / CONNECT_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _tracked_paths(state: dict[str, Any]) -> set[str]:
    tracked: set[str] = set()
    for target_state in state.get("targets", {}).values():
        for entry in target_state.get("files", []):
            tracked.add(entry["path"])
    return tracked


def write_target(name: str, root: Path, *, shadow: bool, state: dict[str, Any]) -> TargetPlan:
    """Write *name*'s files (idempotent) and update *state* in place.

    Returns the same shape as :func:`plan_target`; ``state`` is mutated with
    a fresh ``targets[name]`` entry (path, digest, shadow flag, timestamp,
    backup path if one was made).
    """
    plan = plan_target(name, root, shadow=shadow)
    if plan.status in ("unobserved", "unknown"):
        return plan

    tracked = _tracked_paths(state)
    written_files: list[dict[str, Any]] = []
    for planned in plan.files:
        full = root / planned.path
        if planned.will_change:
            backup_rel: str | None = None
            if planned.existed_before and str(planned.path) not in tracked:
                backup_path = full.with_name(full.name + ".bak")
                shutil.copy2(full, backup_path)
                backup_rel = str(planned.path) + ".bak"
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(planned.content, encoding="utf-8")
            written_files.append(
                {
                    "path": str(planned.path),
                    "digest": content_digest(planned.content),
                    "backup": backup_rel,
                }
            )
        else:
            # Idempotent no-op write: keep the existing tracked record for this
            # file (digest unchanged) so --status has something to compare.
            existing_entry = next(
                (
                    entry
                    for target_state in state.get("targets", {}).values()
                    for entry in target_state.get("files", [])
                    if entry["path"] == str(planned.path)
                ),
                None,
            )
            written_files.append(
                existing_entry
                or {
                    "path": str(planned.path),
                    "digest": content_digest(planned.content),
                    "backup": None,
                }
            )

    state.setdefault("targets", {})[name] = {
        "shadow": shadow and not plan.shadow_ignored,
        "written_at": datetime.now(timezone.utc).isoformat(),
        "files": written_files,
    }
    return plan


# --------------------------------------------------------------------------
# --status drift check
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class DriftReport:
    """One file's drift status: whether it still matches what ``connect`` wrote."""

    target: str
    path: str
    status: str  # "ok" | "UNOBSERVED"
    reason: str | None = None


def check_status(root: Path) -> list[DriftReport]:
    """Compare every file ``connect`` wrote against its recorded digest."""
    state = load_connect_state(root)
    reports: list[DriftReport] = []
    for target_name, target_state in state.get("targets", {}).items():
        for entry in target_state.get("files", []):
            full = root / entry["path"]
            if not full.is_file():
                reports.append(
                    DriftReport(target_name, entry["path"], "UNOBSERVED", "file_missing")
                )
                continue
            try:
                current = full.read_text(encoding="utf-8")
            except OSError:
                reports.append(DriftReport(target_name, entry["path"], "UNOBSERVED", "unreadable"))
                continue
            if content_digest(current) != entry["digest"]:
                reports.append(
                    DriftReport(target_name, entry["path"], "UNOBSERVED", "digest_mismatch")
                )
            else:
                reports.append(DriftReport(target_name, entry["path"], "ok"))
    return reports


# --------------------------------------------------------------------------
# Claude Code hook payload mapping (PreToolUse/PostToolUse -> hyodo.agent-event/v1)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class MappedHookEvent:
    """A Claude Code hook payload, mapped to a raw ``hyodo.agent-event/v1`` dict."""

    raw: dict[str, Any]
    root: Path


def map_claude_code_hook_payload(
    payload: Any, default_root: Path
) -> tuple[MappedHookEvent | None, str | None]:
    """Map one Claude Code ``PreToolUse``/``PostToolUse`` hook JSON payload.

    Field mapping is fixed by the Phase 1-D spec (docs/CONNECT.md mirrors the
    table). Returns ``(None, reason)`` for anything that cannot be honestly
    mapped — callers must treat that as UNOBSERVED, never invent a decision.
    """
    if not isinstance(payload, dict):
        return None, "not_an_object"

    tool_use_id = payload.get("tool_use_id")
    session_id = payload.get("session_id")
    hook_event_name = payload.get("hook_event_name")
    if not _is_str(tool_use_id):
        return None, "missing_field:tool_use_id"
    if not _is_str(session_id):
        return None, "missing_field:session_id"
    if not _is_str(hook_event_name):
        return None, "missing_field:hook_event_name"
    if hook_event_name not in ("PreToolUse", "PostToolUse"):
        return None, "unsupported_hook_event_name"

    kind = "tool_call" if hook_event_name == "PreToolUse" else "tool_result"

    cwd = payload.get("cwd")
    effective_root = Path(cwd) if _is_str(cwd) else default_root
    step_index = count_run_events(effective_root, session_id)
    tags: list[str] = []
    if step_index is None:
        # The ledger could not be observed; zero is a placeholder, and the tag
        # keeps that fact in the record instead of handing out a free zero.
        step_index = 0
        tags.append("step_index:unobserved")

    tool_name = payload.get("tool_name")
    tool_input_raw = payload.get("tool_input")
    tool_input: dict[str, Any] = tool_input_raw if isinstance(tool_input_raw, dict) else {}
    tool: dict[str, Any] = {"name": tool_name if _is_str(tool_name) else None}

    file_path = tool_input.get("file_path")
    if _is_str(file_path):
        tool["paths"] = [file_path]

    url = tool_input.get("url")
    if _is_str(url):
        parsed = urlsplit(url)
        path_and_query = parsed.path + (f"?{parsed.query}" if parsed.query else "")
        tool["urls"] = [{"domain": parsed.netloc, "path": path_and_query or "/"}]

    command = tool_input.get("command")
    if _is_str(command):
        tool["args_digest"] = content_digest(command)

    raw: dict[str, Any] = {
        "schema_version": AGENT_EVENT_SCHEMA_VERSION,
        "event_id": tool_use_id,
        "run_id": session_id,
        # The hook payload carries no timestamp; synthesized at receipt time.
        "ts": datetime.now(timezone.utc).isoformat(),
        "kind": kind,
        "step_index": step_index,
        "actor": "agent",
        # The hook already uses session_id as run_id; actor_id additionally
        # carries the same value so two labelled agents in one run can be
        # told apart downstream (hyodo/graph_view.py build_actor_rows).
        "actor_id": session_id,
        "tool": tool,
    }
    if tags:
        raw["meta"] = {"tags": tags}
    return MappedHookEvent(raw=raw, root=effective_root), None
