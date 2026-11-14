"""Phase 2.3/2.4 — Fault-Isolated Universal Factory Runner & Trust-Enforced Executor.

Executes tasks with pluggable skills while enforcing:
1. Core Independence: works even when 0 external skills are installed.
2. Preflight `analyze_capability_gaps` before routing/execution, skipping
   `DEGRADED` skills and applying host-configured Personal Taste rules.
3. Strict separation between metadata registration (`REGISTERED`), instruction
   disclosure (`DISCLOSED_ONLY` -> `gate_verdict: UNOBSERVED`), and real
   subprocess execution (`EXECUTED_PASS` / `EXECUTED_FAIL`).
4. Full-stream `stdout` hashing and timing-normalized SHA-256 before preview truncation.
5. Runtime `PermissionBoundary` handling: `subprocess_exec` is enforced by a pre-exec
   gate, `filesystem_write=False` is enforced inside the workspace only (POSIX write
   bits plus snapshot rollback; `.git/` and `.hyodo/` outside `.hyodo/factory/` are
   not covered), and `network_access` / `browser_automation` restrictions and the
   `allowed_paths` / `allowed_tools` allowlists are NOT enforced. No skill run may
   change `.hyodo/factory/`. Every
   skill output carries a `boundary_enforcement` report saying which is which, and
   `auto` execution is refused while a restriction the boundary relies on is
   unenforced, unless the host attests that it enforces it itself.
6. Substantive Producer != Independent Verifier separation (`SELF_REVIEW_FORBIDDEN`)
   with genuine `hyodo.independent-verifier/v1` receipt validation in `evaluate_skill_impact`.
7. Single-step trust progression, evidence anti-replay, and host approval receipt
   binding (`workspace_id`, `policy_digest`, `risk_level`, `approved_scope`, the
   whole-module tree digest, the module source path, and the exact command), all
   re-checked at `auto` execution time and confirmed by the host's authority verifier.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from adapters.agent_skills import disclose_skill_body

from factory.contracts import (
    FACTORY_APPROVAL_REQUEST_SCHEMA,
    TRUST_STAGES,
    TRUST_STATE_SCHEMA,
    ModuleRecord,
    PermissionBoundary,
    SkillUnitSpec,
    recommend_skill_lifecycle_action,
    utc_now_iso,
)
from factory.lifecycle import (
    RUN_STATE_DIR_REL,
    acquire_run_lock,
    clear_pending_selective_restore,
    clear_skill_process_groups,
    process_groups_record_rel,
    release_run_lock,
    restore_activation_state,
    save_pending_selective_restore,
    snapshot_activation_state,
    write_skill_process_groups,
)
from factory.registry import (
    FACTORY_DIR_REL,
    compute_module_tree_digest,
    load_registry_state,
    verify_lock_integrity,
)
from factory.router import (
    TRUST_STATE_REL_PATH,
    analyze_capability_gaps,
    route_skills_for_task,
    select_and_activate_for_task,
)
from hyodo.admission_observation import (
    ADMISSION_OBSERVATION_SCHEMA_VERSION,
    append_admission_observation,
)
from hyodo.events import (
    AGENT_EVENT_SCHEMA_VERSION,
    append_agent_event,
    content_digest,
    unevaluated_policy,
    validate_event,
)
from hyodo.host_promise_observation import load_host_promise_observation
from hyodo.independent_verifier import (
    INDEPENDENT_VERIFIER_SCHEMA_VERSION,
    verify_exact_candidate,
)
from hyodo.nameplate import UNOBSERVED, build_nameplate
from hyodo.orchestration_observation import (
    ORCHESTRATION_OBSERVATION_SCHEMA_VERSION,
    append_orchestration_observation,
)
from hyodo.policy_trust import SCOPE_POLICY_ASK, current_policy_digest, load_policy_trust
from hyodo.provenance import clean_git_env
from hyodo.six_lens_runtime import measure_workspace_six_lenses
from hyodo.skill_eval import evaluate_skill_case
from hyodo.user_state import workspace_identity

# Host-owned check that an approval receipt was issued by a real approval
# authority (for example a passkey-signed approval in the host's own system).
# The factory can build an approval *request*, but it can never vouch for who
# approved it.
ApprovalAuthorityVerifier = Callable[[dict[str, Any]], tuple[bool, str | None]]

# Restrictions a `PermissionBoundary` can impose that this runner does not
# fully enforce. A host that enforces one itself (for example by running the
# command in a network-isolated sandbox) names it in `host_enforced_restrictions`;
# that is recorded as `HOST_ATTESTED`, not as something HyoDo observed. Any
# other name is refused: an attestation must name something this report knows.
HOST_ENFORCEABLE_RESTRICTIONS = frozenset(
    {"network_access", "browser_automation", "filesystem_write", "allowed_paths", "allowed_tools"}
)

# Sentinel: the caller does not ask `verify_host_approval_receipt` to compare a
# runtime value (trust promotion has no command or attestation to compare against).
_COMMAND_NOT_CHECKED: Any = object()


def validate_host_enforced_restrictions(names: Any) -> tuple[str, ...]:
    """Return the attested restriction names, sorted; raise on anything unknown.

    Every entry point that accepts an attestation calls this, so a free-text
    claim (for example `"bogus"`) can never count as an enforced restriction.
    """
    if names is None:
        return ()
    if isinstance(names, str) or not isinstance(names, (list, tuple, set, frozenset)):
        raise ValueError("host_enforced_restrictions must be a collection of names")
    unknown = sorted(str(n) for n in names if n not in HOST_ENFORCEABLE_RESTRICTIONS)
    if unknown:
        raise ValueError(f"unknown host_enforced_restrictions: {unknown}")
    return tuple(sorted(set(names)))


def boundary_enforcement_report(
    boundary: PermissionBoundary,
    host_enforced_restrictions: frozenset[str] | set[str] | tuple[str, ...] = (),
) -> dict[str, str]:
    """Say, per restriction, what this runner actually enforces. Never overstates.

    Values: `ENFORCED`, `PARTIAL` (workspace only), `UNENFORCED`,
    `HOST_ATTESTED` (the host says it enforces it; HyoDo did not observe that),
    `NOT_RESTRICTED` (the boundary does not restrict it).
    """
    attested = set(validate_host_enforced_restrictions(host_enforced_restrictions))

    def _state(restricted: bool, own: str, name: str) -> str:
        if not restricted:
            return "NOT_RESTRICTED"
        if own != "ENFORCED" and name in attested:
            return "HOST_ATTESTED"
        return own

    return {
        "execution_authority": "ENFORCED",
        "subprocess_exec": _state(not boundary.subprocess_exec, "ENFORCED", "subprocess_exec"),
        "filesystem_write": _state(not boundary.filesystem_write, "PARTIAL", "filesystem_write"),
        "network_access": _state(not boundary.network_access, "UNENFORCED", "network_access"),
        "browser_automation": _state(
            not boundary.browser_automation, "UNENFORCED", "browser_automation"
        ),
        # Declared path/tool allowlists are not evaluated by the runner at all.
        "allowed_paths": _state(bool(boundary.allowed_paths), "UNENFORCED", "allowed_paths"),
        "allowed_tools": _state(bool(boundary.allowed_tools), "UNENFORCED", "allowed_tools"),
    }


def _restrictions_relying_on_unenforced(
    boundary: PermissionBoundary,
    host_enforced_restrictions: frozenset[str] | set[str] | tuple[str, ...] = (),
) -> list[str]:
    report = boundary_enforcement_report(boundary, host_enforced_restrictions)
    return sorted(k for k, v in report.items() if v in ("UNENFORCED", "PARTIAL"))


def _command_digest(command: list[str] | None) -> str:
    canonical = json.dumps(command, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_command(command: Any) -> tuple[bool, list[str] | None]:
    if command is None:
        return True, None
    if isinstance(command, (list, tuple)) and all(isinstance(a, str) for a in command):
        return True, list(command)
    return False, None


_PROTECTED_TOP_DIRS = (".git", ".hyodo", "__pycache__", ".pytest_cache")

_VOLATILE_TIMING_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"(duration_ms(?:\s*[:=]\s*|\s+))\d+(?:\.\d+)?", re.IGNORECASE),
        r"\g<1><DURATION_MS>",
    ),
    (re.compile(r"\b\d+(?:\.\d+)?\s?ms\b", re.IGNORECASE), "<DURATION_MS>"),
)


def _canonical_receipt_digest(payload: dict[str, Any] | None) -> str | None:
    if not isinstance(payload, dict) or not payload:
        return None
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _stdout_integrity_fields(raw_stdout: str) -> dict[str, Any]:
    """Hash and timing-normalize the full stdout stream prior to 400-char preview truncation."""
    stripped = raw_stdout.strip()
    normalized = raw_stdout
    for pattern, repl in _VOLATILE_TIMING_PATTERNS:
        normalized = pattern.sub(repl, normalized)
    return {
        "stdout": stripped[:400],
        "stdout_bytes": len(raw_stdout.encode("utf-8")),
        "stdout_truncated": len(stripped) > 400,
        "full_stdout_sha256": hashlib.sha256(raw_stdout.encode("utf-8")).hexdigest(),
        "normalized_stdout_sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
    }


WorkspaceSnapshot = dict[str, tuple[bytes, int, int, int]]


def _snapshot_workspace_files(workspace_root: Path) -> WorkspaceSnapshot:
    """Snapshot regular files outside `.git` and `.hyodo`: content, mode, inode, link count."""
    snap: WorkspaceSnapshot = {}
    for path in sorted(workspace_root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        rel = path.relative_to(workspace_root)
        if rel.parts and rel.parts[0] in _PROTECTED_TOP_DIRS:
            continue
        try:
            st = path.lstat()
            snap[str(rel)] = (path.read_bytes(), st.st_mode & 0o777, st.st_ino, st.st_nlink)
        except OSError:
            continue
    return snap


@contextlib.contextmanager
def _readonly_workspace_guard(workspace_root: Path) -> Iterator[None]:
    """Pre-write OS permission enforcement: strip POSIX write bits (`mode & ~0o222`) on workspace files and dirs.

    Modes are put back only on the same inode that was protected: if a skill
    replaced a path (for example with a hard link to a file outside the
    workspace), the replacement is never chmod-ed.
    """
    saved_modes: list[tuple[Path, int, int, int]] = []
    targets: list[Path] = []
    for path in sorted(workspace_root.rglob("*")):
        if path.is_symlink():
            continue
        rel = path.relative_to(workspace_root)
        if rel.parts and rel.parts[0] in _PROTECTED_TOP_DIRS:
            continue
        targets.append(path)
    files = [p for p in targets if p.is_file()]
    dirs = sorted([p for p in targets if p.is_dir()], key=lambda p: len(p.parts), reverse=True)
    ordered = [*files, *dirs, workspace_root]
    try:
        for p in ordered:
            try:
                st = p.lstat()
                mode = st.st_mode & 0o777
                saved_modes.append((p, mode, st.st_dev, st.st_ino))
                p.chmod(mode & ~0o222)
            except OSError:
                continue
        yield
    finally:
        for p, mode, dev, ino in reversed(saved_modes):
            with contextlib.suppress(OSError):
                st = p.lstat()
                if not stat.S_ISLNK(st.st_mode) and (st.st_dev, st.st_ino) == (dev, ino):
                    p.chmod(mode)


def _restore_and_detect_writes(
    workspace_root: Path,
    before: WorkspaceSnapshot,
) -> list[str]:
    """Post-write defense-in-depth: detect created/modified/deleted/replaced files and restore *before* state.

    Restoring never writes or chmods through an existing path: a changed file is
    unlinked and recreated, so a hard link to a file outside the workspace is
    only unlinked. A planted hard link is recorded as `hardlink_planted:<path>`.
    """
    after = _snapshot_workspace_files(workspace_root)
    mutated: list[str] = []

    for rel, (content, _mode, ino, nlink) in after.items():
        target = workspace_root / rel
        if rel not in before:
            mutated.append(f"created:{rel}")
            if nlink > 1:
                mutated.append(f"hardlink_planted:{rel}")
            try:
                target.unlink()
            except OSError as exc:
                mutated.append(f"restore_failed:{rel}:{type(exc).__name__}")
            continue
        old_content, old_mode, old_ino, old_nlink = before[rel]
        if old_content != content or old_ino != ino:
            mutated.append(f"modified:{rel}")
            if nlink > 1 and (old_ino != ino or nlink != old_nlink):
                mutated.append(f"hardlink_planted:{rel}")
            failure = _restore_regular_file(workspace_root, rel, old_content, old_mode)
            if failure is not None:
                mutated.append(f"restore_failed:{rel}:{failure}")

    for rel, (content, mode, _ino, _nlink) in before.items():
        if rel not in after:
            mutated.append(f"deleted:{rel}")
            failure = _restore_regular_file(workspace_root, rel, content, mode)
            if failure is not None:
                mutated.append(f"restore_failed:{rel}:{failure}")

    return sorted(mutated)


def _restore_regular_file(
    workspace_root: Path, rel: str, content: bytes, mode: int = 0o644
) -> str | None:
    """Recreate *rel* as a new regular file without following anything a skill planted.

    Whatever stands at *rel* (file, hard link, symlink) is unlinked and a new
    inode is created with `O_EXCL | O_NOFOLLOW`; a symlink or file standing
    where a directory used to be is removed first. Nothing is ever written or
    chmod-ed through an existing path. Returns `None` on success or a short
    failure reason; it never raises.
    """
    target = workspace_root / rel
    try:
        current = workspace_root
        for part in Path(rel).parts[:-1]:
            current = current / part
            if current.is_symlink() or (current.exists() and not current.is_dir()):
                current.unlink()
            if not current.exists():
                current.mkdir()
        if target.is_symlink() or target.exists():
            target.unlink()
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode)
        try:
            os.write(fd, content)
            os.fchmod(fd, mode)
        finally:
            os.close(fd)
    except OSError as exc:
        return type(exc).__name__
    return None


_SYMLINK_MARK = b"\0symlink\0"


# Harness state no skill run may change: the registry/lock/trust/taste
# directory and the per-run process-group records.
_PROTECTED_STATE_DIRS = (FACTORY_DIR_REL, RUN_STATE_DIR_REL)


def _factory_state_snapshot(workspace_root: Path) -> dict[str, bytes]:
    """Snapshot `.hyodo/factory/` and `.hyodo/factory-run-state/` around a skill run.

    The workspace guard leaves `.hyodo/` alone, so this harness's own state is
    protected separately: no skill run, read-only or not, may change it.
    Symlinks are recorded by their target so a planted link counts as a change.
    """
    snap: dict[str, bytes] = {}
    for rel_root in _PROTECTED_STATE_DIRS:
        root = workspace_root / rel_root
        if root.is_symlink():
            snap[rel_root.as_posix()] = _SYMLINK_MARK + os.readlink(root).encode(
                "utf-8", "surrogateescape"
            )
            continue
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            rel = path.relative_to(workspace_root).as_posix()
            try:
                if path.is_symlink():
                    snap[rel] = _SYMLINK_MARK + os.readlink(path).encode("utf-8", "surrogateescape")
                elif path.is_file():
                    snap[rel] = path.read_bytes()
            except OSError:
                continue
    return snap


def _restore_factory_state(
    workspace_root: Path,
    before: dict[str, bytes],
    harness_written: dict[str, bytes] | None = None,
) -> list[str]:
    """Undo any change a skill run made to protected harness state; return what changed.

    *harness_written* holds what the harness itself wrote during the run (the
    process-group record); those writes are the expected state, not a change.
    Never raises: a path that cannot be restored is reported as `restore_failed`.
    """
    before = {**before, **(harness_written or {})}
    after = _factory_state_snapshot(workspace_root)
    changed: list[str] = []
    for rel, content in after.items():
        target = workspace_root / rel
        if rel not in before:
            changed.append(f"created:{rel}")
            try:
                target.unlink()
            except OSError as exc:
                changed.append(f"restore_failed:{rel}:{type(exc).__name__}")
        elif before[rel] != content:
            changed.append(f"modified:{rel}")
            if before[rel].startswith(_SYMLINK_MARK):
                continue  # a link the host had placed is reported, not re-created
            failure = _restore_regular_file(workspace_root, rel, before[rel])
            if failure is not None:
                changed.append(f"restore_failed:{rel}:{failure}")
    for rel, content in before.items():
        if rel not in after:
            changed.append(f"deleted:{rel}")
            if content.startswith(_SYMLINK_MARK):
                continue  # a link the host had placed is reported, not re-created
            failure = _restore_regular_file(workspace_root, rel, content)
            if failure is not None:
                changed.append(f"restore_failed:{rel}:{failure}")
    return sorted(changed)


def _set_tree_writable(root: Path, writable: bool) -> None:
    paths = [root, *root.rglob("*")]
    for path in sorted(paths, key=lambda p: len(p.parts), reverse=not writable):
        if path.is_symlink():
            continue
        with contextlib.suppress(OSError):
            mode = path.stat().st_mode & 0o777
            path.chmod(mode | 0o200 if writable else mode & ~0o222)


def _snapshot_module_for_exec(
    module_root: Path, approved_tree: str | None
) -> tuple[Path | None, str | None]:
    """Copy the module tree to a private read-only directory and check it against the approval.

    `auto` commands then run with `CLAUDE_PLUGIN_ROOT` / `CLAUDE_SKILL_DIR`
    pointing at this copy, so an edit to the original module after the check
    cannot change what those paths resolve to. Returns `(copy_root, error)`.
    """
    if not approved_tree:
        return None, "approved_module_tree_missing"
    holder = Path(tempfile.mkdtemp(prefix="hyodo-factory-exec-"))
    copy_root = holder / "module"
    try:
        shutil.copytree(
            module_root,
            copy_root,
            symlinks=True,
            ignore=lambda d, names: [".git"] if Path(d) == module_root else [],
        )
    except (OSError, shutil.Error) as exc:
        _discard_exec_snapshot(copy_root)
        return None, f"copy_failed:{type(exc).__name__}"
    digest, _count, err = compute_module_tree_digest(copy_root)
    if digest != approved_tree:
        _discard_exec_snapshot(copy_root)
        return None, f"module_tree_changed_before_exec:{err or 'digest_mismatch'}"
    _set_tree_writable(copy_root, False)
    return copy_root, None


def _discard_exec_snapshot(copy_root: Path) -> None:
    holder = copy_root.parent
    if holder.exists():
        _set_tree_writable(holder, True)
        shutil.rmtree(holder, ignore_errors=True)


def _kill_process_group(pgid: int) -> bool:
    """SIGKILL every process left in the group; True when something was still running."""
    try:
        os.killpg(pgid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        return False
    return True


class SkillTimeoutExpired(subprocess.TimeoutExpired):
    """A skill timed out; its whole process group was then killed."""

    process_group_killed: bool = False


def _run_skill_process(
    cmd: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout: float,
    on_start: Callable[[int], None] | None = None,
) -> tuple[subprocess.CompletedProcess[str], bool]:
    """Run a skill command in its own process group and kill that whole group afterwards.

    A background descendant (`cmd &`) that outlives the skill would otherwise
    keep writing after the post-run checks. Returns `(completed, descendants_killed)`.
    A process that leaves the group (`setsid`) or any other same-user process
    is outside this guarantee.
    """
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    killed = False
    try:
        if on_start is not None:
            on_start(proc.pid)  # the pid is the new session's process-group id
        try:
            out, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            killed = _kill_process_group(proc.pid)
            proc.kill()
            out, err = proc.communicate()
            timeout_exc = SkillTimeoutExpired(cmd, timeout, output=out, stderr=err)
            timeout_exc.process_group_killed = killed
            raise timeout_exc from None
    finally:
        killed = _kill_process_group(proc.pid) or killed
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    return subprocess.CompletedProcess(cmd, proc.returncode, out, err), killed


def _timeout_kill_fields(exc: BaseException) -> dict[str, Any]:
    """What happened to a timed-out skill's process group, as observed."""
    if not isinstance(exc, SkillTimeoutExpired):
        return {}
    # At timeout the group is killed while the skill process itself is still in
    # it, so a successful kill means the skill and any descendants were stopped.
    return {
        "process_group_killed_on_timeout": exc.process_group_killed,
        "descendants_killed_after_exit": exc.process_group_killed,
    }


_HYODO_REPO_ROOT = str(Path(__file__).resolve().parents[3])


def _with_pythonpath(env: dict[str, str], workspace_root: Path | None = None) -> dict[str, str]:
    parts = [str(workspace_root)] if workspace_root is not None else []
    parts.append(_HYODO_REPO_ROOT)
    existing = env.get("PYTHONPATH", "")
    if existing:
        parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def _build_isolated_env(
    unit: SkillUnitSpec,
    workspace_root: Path | None = None,
    *,
    module_source_path: str | None = None,
    active_taste_rules: list[str] | None = None,
) -> dict[str, str]:
    """Build a scrubbed subprocess environment respecting `unit.boundary`, host runtime paths, and active Personal Taste rules."""
    env = _with_pythonpath(clean_git_env(), workspace_root)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if not unit.boundary.network_access:
        # Advisory only: dropping proxy variables and setting a flag does not
        # stop a process from opening sockets. Reported as UNENFORCED.
        for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy"):
            env.pop(k, None)
        env["HYODO_FACTORY_NETWORK_DISABLED"] = "1"
        env["HYODO_FACTORY_NETWORK_ENFORCEMENT"] = "UNENFORCED"
    env["HYODO_FACTORY_SKILL_ID"] = unit.skill_id
    env["HYODO_FACTORY_ROLE"] = unit.role_hint
    env["HYODO_FACTORY_EXECUTION_AUTHORITY"] = "false"
    if module_source_path:
        env["CLAUDE_PLUGIN_ROOT"] = module_source_path
        skill_dir = (Path(module_source_path) / unit.relative_path).parent
        env["CLAUDE_SKILL_DIR"] = str(skill_dir)
    if workspace_root is not None:
        env["CLAUDE_PROJECT_DIR"] = str(workspace_root)
    if active_taste_rules:
        env["HYODO_HOST_PERSONAL_TASTE_JSON"] = json.dumps(list(active_taste_rules))
    return env


def _build_execution_waves(
    selected_skills: list[str],
    unit_lookup: dict[str, tuple[ModuleRecord, SkillUnitSpec]],
) -> list[list[str]]:
    """Group selected skills into topological dependency waves for serial-wave / parallel-intra-wave execution."""
    active_ids = [sid for sid in selected_skills if sid in unit_lookup]
    if not active_ids:
        return []

    remaining = list(active_ids)
    completed: set[str] = set()
    waves: list[list[str]] = []

    while remaining:
        ready: list[str] = []
        for sid in remaining:
            _, unit = unit_lookup[sid]
            deps_in_run = [d for d in unit.dependencies if d in active_ids and d != sid]
            if all(d in completed for d in deps_in_run):
                ready.append(sid)
        if not ready:
            ready = [remaining[0]]

        non_verifiers = [
            sid
            for sid in ready
            if unit_lookup[sid][1].role_hint != "verifier"
            and unit_lookup[sid][1].design_stage != "gatekeep"
        ]
        wave = non_verifiers if non_verifiers else ready
        waves.append(wave)
        for sid in wave:
            completed.add(sid)
            remaining.remove(sid)

    return waves


def _validate_independent_verifier_receipt(
    verifier_receipt: dict[str, Any] | None,
    *,
    builder_actor: str | None = None,
    builder_session_id: str | None = None,
) -> tuple[bool, str | None]:
    """Validate that *verifier_receipt* carries a genuine, non-self-reviewed `hyodo.independent-verifier/v1` attestation."""
    if not isinstance(verifier_receipt, dict) or not verifier_receipt:
        return False, "verifier_receipt_missing"
    status = str(verifier_receipt.get("status", "UNOBSERVED"))
    if status not in ("PASS", "FAIL"):
        return False, f"verifier_status_unobserved_or_hold:{status}"
    attestation = verifier_receipt.get("attestation")
    if not isinstance(attestation, dict):
        return False, "verifier_attestation_missing"
    if attestation.get("schema_version") != INDEPENDENT_VERIFIER_SCHEMA_VERSION:
        return False, "verifier_attestation_schema_invalid"
    att_verdict = str(attestation.get("verdict", "UNOBSERVED"))
    if status == "PASS" and att_verdict != "PASS":
        return False, "verifier_status_attestation_mismatch"

    target = attestation.get("target")
    observed = attestation.get("observed")
    nameplate = attestation.get("verifier_nameplate")
    if (
        not isinstance(target, dict)
        or not isinstance(observed, dict)
        or not isinstance(nameplate, dict)
    ):
        return False, "verifier_attestation_malformed"
    head_sha = observed.get("head_sha")
    exact_sha = target.get("exact_artifact_sha")
    if not head_sha or head_sha == UNOBSERVED or head_sha != exact_sha:
        return False, "verifier_exact_sha_mismatch"
    if nameplate.get("role") != "verifier":
        return False, "verifier_role_invalid"
    v_actor = nameplate.get("actor_id") or verifier_receipt.get("actor_id")
    v_session = nameplate.get("session_id") or verifier_receipt.get("session_id")
    if not v_actor or v_actor == UNOBSERVED or not v_session or v_session == UNOBSERVED:
        return False, "verifier_identity_unobserved"
    if builder_actor and v_actor == builder_actor:
        return False, "SELF_REVIEW_FORBIDDEN:actor_collision"
    if builder_session_id and v_session == builder_session_id:
        return False, "SELF_REVIEW_FORBIDDEN:session_collision"
    return True, None


def _default_env_fingerprint() -> str:
    return f"py{sys.version_info.major}.{sys.version_info.minor}-{sys.platform}"


def _compute_trust_ledger_digest(skills_map: dict[str, Any]) -> str:
    canonical = json.dumps(skills_map, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _read_trust_file(workspace_root: Path) -> dict[str, Any]:
    path = workspace_root / TRUST_STATE_REL_PATH
    if not path.is_file():
        return {"schema": TRUST_STATE_SCHEMA, "skills": {}}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and isinstance(raw.get("skills"), dict):
            return raw
    except (OSError, json.JSONDecodeError):
        pass
    return {"schema": TRUST_STATE_SCHEMA, "skills": {}}


def _verify_trust_file_integrity(workspace_root: Path) -> tuple[bool, str | None]:
    path = workspace_root / TRUST_STATE_REL_PATH
    if not path.is_file():
        return True, None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, "TRUST_STATE_CORRUPT_JSON"
    if not isinstance(raw, dict) or not isinstance(raw.get("skills"), dict):
        return False, "TRUST_STATE_MALFORMED"
    # The digest is unkeyed: it detects corruption and naive edits, not forgery.
    # Forgery resistance for AUTO_RUN comes from re-verifying the stored approval
    # receipt with the host's authority verifier at execution time.
    stored_digest = raw.get("ledger_digest")
    if stored_digest is None:
        return False, "TRUST_STATE_DIGEST_MISSING"
    if stored_digest != _compute_trust_ledger_digest(raw["skills"]):
        return False, "TRUST_STATE_TAMPERED_DIGEST_MISMATCH"
    return True, None


def _write_trust_file(workspace_root: Path, data: dict[str, Any]) -> None:
    path = workspace_root / TRUST_STATE_REL_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    skills = data.get("skills", {})
    out = {
        "schema": TRUST_STATE_SCHEMA,
        "skills": skills,
        "ledger_digest": _compute_trust_ledger_digest(skills),
    }
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _scope_covers_boundary(
    approved_scope: Any, boundary: PermissionBoundary
) -> tuple[bool, str | None]:
    if not isinstance(approved_scope, dict):
        return False, "approved_scope_missing"
    if approved_scope.get("execution_authority") is not False:
        return False, "approved_scope_claimed_execution_authority"
    for cap_flag in ("filesystem_write", "subprocess_exec", "network_access", "browser_automation"):
        if bool(getattr(boundary, cap_flag)) and not bool(approved_scope.get(cap_flag, False)):
            return False, f"scope_exceeded:{cap_flag}"
    allowed_paths = approved_scope.get("allowed_paths")
    if isinstance(allowed_paths, list):
        allowed_set = {str(p) for p in allowed_paths}
        for req_path in boundary.allowed_paths:
            if req_path not in allowed_set:
                return False, f"scope_exceeded:allowed_path:{req_path}"
    return True, None


def _find_module_and_unit(
    modules: dict[str, ModuleRecord], skill_id: str
) -> tuple[ModuleRecord, SkillUnitSpec] | None:
    for mod in modules.values():
        if skill_id in mod.skills:
            return mod, mod.skills[skill_id]
    return None


def issue_host_approval_request(
    workspace_root: Path,
    *,
    skill_id: str,
    run_id: str,
    approved_by: str,
    command: list[str] | None,
    risk_level: str = "low",
    mandatory_gates_passed: bool = True,
    permission_violations: int = 0,
    reproducible: bool = True,
    require_policy_trust: bool = False,
    host_enforced_restrictions: frozenset[str] | set[str] | tuple[str, ...] = (),
) -> dict[str, Any]:
    """Build an unsigned approval *request* for the host's own approval authority.

    It binds the workspace, policy digest, `SKILL.md` hash, run_id, the digest of
    every file in the skill's module tree (symlinks refused), the module source
    path, the exact command the host will run (`None` when no subprocess
    command will run, e.g. disclosure-only or an in-process host hook), and the
    restrictions the host attests it enforces itself, so the approver sees that
    claim and a run with a different claim does not match.

    The returned dict is not an approval. Every field is asserted by the caller,
    and nothing here proves who approved it. `verify_host_approval_receipt`
    accepts it only when the host's `authority_verifier` confirms that a real
    approval authority issued it.
    """
    found = _find_module_and_unit(load_registry_state(workspace_root), skill_id)
    if found is None:
        raise KeyError(f"cannot build an approval request for unregistered skill: {skill_id}")
    mod, unit = found
    ok_cmd, normalized_cmd = _normalize_command(command)
    if not ok_cmd:
        raise ValueError("command must be a list of strings or None")
    tree_digest, _count, tree_error = compute_module_tree_digest(Path(mod.source_path))
    if tree_digest is None:
        raise ValueError(f"cannot bind approval: module tree unbindable ({tree_error})")
    return {
        "schema": FACTORY_APPROVAL_REQUEST_SCHEMA,
        "approved": True,
        "run_id": run_id,
        "skill_id": skill_id,
        "content_sha256": unit.content_sha256,
        "module_source_path": mod.source_path,
        "module_tree_sha256": tree_digest,
        "command": normalized_cmd,
        "command_sha256": _command_digest(normalized_cmd),
        "host_enforced_restrictions": list(
            validate_host_enforced_restrictions(host_enforced_restrictions)
        ),
        "workspace_id": workspace_identity(workspace_root),
        "policy_digest": current_policy_digest(workspace_root),
        "approved_by": approved_by,
        "risk_level": risk_level,
        "mandatory_gates_passed": mandatory_gates_passed,
        "permission_violations": permission_violations,
        "reproducible": reproducible,
        "approved_scope": unit.boundary.to_dict(),
        "require_policy_trust": require_policy_trust,
    }


def verify_host_approval_receipt(
    workspace_root: Path,
    approval_receipt: dict[str, Any] | None,
    *,
    skill_id: str,
    unit: SkillUnitSpec,
    content_sha256: str,
    run_id: str,
    module: ModuleRecord | None = None,
    command: Any = _COMMAND_NOT_CHECKED,
    host_enforced_restrictions: Any = _COMMAND_NOT_CHECKED,
    authority_verifier: ApprovalAuthorityVerifier | None = None,
) -> tuple[bool, list[str]]:
    """Fail-closed verification of a host approval receipt (never trusts a bare boolean).

    Structural binding is checked here, including a fresh recomputation of the
    module tree digest from disk and, when *command* is given, an exact match of
    the command the host is about to run. The issuing authority is checked only
    by the host-supplied *authority_verifier*. Without one the receipt is never
    accepted.
    """
    reasons: list[str] = []
    if not isinstance(approval_receipt, dict) or not approval_receipt:
        return False, ["APPROVAL_RECEIPT_REQUIRED"]
    if approval_receipt.get("schema") != FACTORY_APPROVAL_REQUEST_SCHEMA:
        reasons.append("approval_schema_invalid")
    if approval_receipt.get("approved") is not True:
        reasons.append("approval_not_approved")
    if approval_receipt.get("skill_id") != skill_id:
        reasons.append("approval_skill_mismatch")
    if approval_receipt.get("content_sha256") != content_sha256:
        reasons.append("approval_content_sha_mismatch")
    if approval_receipt.get("run_id") != run_id:
        reasons.append("approval_run_id_mismatch")
    if approval_receipt.get("workspace_id") != workspace_identity(workspace_root):
        reasons.append("approval_workspace_mismatch")
    if approval_receipt.get("policy_digest") != current_policy_digest(workspace_root):
        reasons.append("approval_policy_digest_changed")
    approver = approval_receipt.get("approved_by")
    if not isinstance(approver, str) or not approver.strip():
        reasons.append("approval_approver_missing")
    risk = str(approval_receipt.get("risk_level", "unknown")).lower()
    if risk not in ("low", "medium"):
        reasons.append(f"approval_risk_blocked:{risk}")
    if approval_receipt.get("mandatory_gates_passed") is not True:
        reasons.append("approval_mandatory_gates_unverified")
    violations = approval_receipt.get("permission_violations", 1)
    if type(violations) is not int:
        reasons.append("approval_permission_violations_invalid")
    elif violations != 0:
        reasons.append("approval_permission_violations_nonzero")
    if approval_receipt.get("reproducible") is not True:
        reasons.append("approval_reproducibility_false")

    # Module tree, source path and command binding, recomputed now.
    mod = module
    if mod is None:
        found = _find_module_and_unit(load_registry_state(workspace_root), skill_id)
        mod = found[0] if found is not None else None
    if mod is None:
        reasons.append("approval_module_unregistered")
    else:
        if approval_receipt.get("module_source_path") != mod.source_path:
            reasons.append("approval_module_source_path_changed")
        bound_tree = approval_receipt.get("module_tree_sha256")
        current_tree, _count, tree_error = compute_module_tree_digest(Path(mod.source_path))
        if not isinstance(bound_tree, str) or not bound_tree:
            reasons.append("approval_module_tree_unbound")
        elif current_tree is None:
            reasons.append(f"approval_module_tree_unbindable:{tree_error}")
        elif current_tree != bound_tree:
            reasons.append("approval_module_tree_changed")
    if "command" not in approval_receipt:
        reasons.append("approval_command_unbound")
    else:
        ok_bound, bound_cmd = _normalize_command(approval_receipt.get("command"))
        if not ok_bound or approval_receipt.get("command_sha256") != _command_digest(bound_cmd):
            reasons.append("approval_command_binding_invalid")
        elif command is not _COMMAND_NOT_CHECKED:
            ok_run, run_cmd = _normalize_command(command)
            if not ok_run or run_cmd != bound_cmd:
                reasons.append("approval_command_changed")
    bound_attestation = approval_receipt.get("host_enforced_restrictions")
    try:
        bound_names = validate_host_enforced_restrictions(bound_attestation)
    except ValueError:
        bound_names = None
    if not isinstance(bound_attestation, list) or bound_names is None:
        reasons.append("approval_host_attestation_unbound")
    elif host_enforced_restrictions is not _COMMAND_NOT_CHECKED:
        try:
            runtime_names = validate_host_enforced_restrictions(host_enforced_restrictions)
        except ValueError:
            runtime_names = None
        if runtime_names != bound_names:
            reasons.append("approval_host_attestation_changed")

    scope_ok, scope_err = _scope_covers_boundary(
        approval_receipt.get("approved_scope"), unit.boundary
    )
    if not scope_ok and scope_err:
        reasons.append(scope_err)

    if approval_receipt.get("require_policy_trust") is True:
        pt_state, pt_err = load_policy_trust(workspace_root, scope=SCOPE_POLICY_ASK)
        if pt_state is None or pt_err is not None or pt_state.level < 1:
            reasons.append(f"policy_trust_unverified:{pt_err or 'level_too_low'}")

    host_promise = load_host_promise_observation(workspace_root)
    if host_promise is not None and host_promise.get("state") != "OBSERVED":
        reasons.append("host_promise_projection_invalid")

    if authority_verifier is None:
        reasons.append("APPROVAL_ISSUER_UNVERIFIED:no_host_authority_verifier")
    elif not reasons:
        # Only ask the host's approval authority once the structure is bound, so a
        # malformed request never triggers a real approval check.
        try:
            issuer_ok, issuer_err = authority_verifier(dict(approval_receipt))
        except Exception as exc:  # any verifier failure is fail-closed
            issuer_ok, issuer_err = False, f"verifier_error:{type(exc).__name__}"
        if issuer_ok is not True:
            reasons.append(f"approval_issuer_rejected:{issuer_err or 'unspecified'}")

    return len(reasons) == 0, reasons


def check_execution_permission(
    workspace_root: Path,
    skill_id: str,
    *,
    execution_mode: str = "manual",
    env_fingerprint: str | None = None,
    authority_verifier: ApprovalAuthorityVerifier | None = None,
    command: list[str] | None = None,
    host_enforced_restrictions: frozenset[str] | set[str] | tuple[str, ...] = (),
) -> dict[str, Any]:
    """Check whether *skill_id* is permitted to execute under *execution_mode* (`manual` | `shadow` | `auto`).

    For `auto`, the trust cache (`trust_stage`, `verifier_status`, `eval_verdict`)
    is only a precondition: it can block, never authorize. Permission comes from
    the host's *authority_verifier* accepting a receipt whose bindings (skill
    hash, boundary, module tree digest recomputed from disk, module source path,
    and the exact *command* about to run) all still match. `auto` is also refused
    while the boundary relies on a restriction this runner does not enforce,
    unless the host names it in *host_enforced_restrictions*.
    """
    if execution_mode not in ("manual", "shadow", "auto"):
        raise ValueError(f"unsupported execution_mode: {execution_mode}")
    host_enforced_restrictions = validate_host_enforced_restrictions(host_enforced_restrictions)

    integrity_ok, integrity_err = _verify_trust_file_integrity(workspace_root)
    if execution_mode != "auto":
        return {
            "allowed": True,
            "execution_mode": execution_mode,
            "reason": None if integrity_ok else integrity_err,
            "trust_stage": None,
        }

    if not integrity_ok:
        return {
            "allowed": False,
            "execution_mode": execution_mode,
            "reason": integrity_err or "TRUST_STATE_INTEGRITY_FAILED",
            "trust_stage": "VERIFY",
        }

    trust_state = get_skill_trust_state(workspace_root, skill_id, env_fingerprint=env_fingerprint)
    if not trust_state.get("registered", False):
        return {
            "allowed": False,
            "execution_mode": execution_mode,
            "reason": f"AUTO_RUN_BLOCKED_UNREGISTERED:{skill_id}",
            "trust_stage": trust_state.get("trust_stage", "DISCOVER"),
        }
    if trust_state.get("drifted"):
        return {
            "allowed": False,
            "execution_mode": execution_mode,
            "reason": str(trust_state.get("demotion_reason") or "AUTO_RUN_BLOCKED_DRIFT"),
            "trust_stage": trust_state.get("trust_stage", "VERIFY"),
        }
    stage = str(trust_state.get("trust_stage", "VERIFY"))
    if stage != "AUTO_RUN":
        return {
            "allowed": False,
            "execution_mode": execution_mode,
            "reason": f"AUTO_RUN_BLOCKED_STAGE:{stage}",
            "trust_stage": stage,
        }
    if trust_state.get("verifier_status") != "PASS" or trust_state.get("eval_verdict") != "HELPED":
        return {
            "allowed": False,
            "execution_mode": execution_mode,
            "reason": "AUTO_RUN_BLOCKED_GATES_NOT_PASSED",
            "trust_stage": stage,
        }
    if trust_state.get("workspace_id") != workspace_identity(workspace_root):
        return {
            "allowed": False,
            "execution_mode": execution_mode,
            "reason": "AUTO_RUN_BLOCKED_WORKSPACE_MISMATCH",
            "trust_stage": stage,
        }
    if trust_state.get("policy_digest") != current_policy_digest(workspace_root):
        return {
            "allowed": False,
            "execution_mode": execution_mode,
            "reason": "AUTO_RUN_BLOCKED_POLICY_DIGEST_CHANGED",
            "trust_stage": stage,
        }

    modules = load_registry_state(workspace_root)
    found = _find_module_and_unit(modules, skill_id)
    if found is None:
        return {
            "allowed": False,
            "execution_mode": execution_mode,
            "reason": f"AUTO_RUN_BLOCKED_MISSING_UNIT:{skill_id}",
            "trust_stage": stage,
        }
    mod, unit = found
    scope_ok, scope_err = _scope_covers_boundary(trust_state.get("approved_scope"), unit.boundary)
    if not scope_ok:
        return {
            "allowed": False,
            "execution_mode": execution_mode,
            "reason": f"AUTO_RUN_BLOCKED_{scope_err}",
            "trust_stage": stage,
        }
    unenforced = _restrictions_relying_on_unenforced(unit.boundary, host_enforced_restrictions)
    if unenforced:
        return {
            "allowed": False,
            "execution_mode": execution_mode,
            "reason": f"AUTO_RUN_BLOCKED_UNENFORCED_RESTRICTION:{','.join(unenforced)}",
            "trust_stage": stage,
            "boundary_enforcement": boundary_enforcement_report(
                unit.boundary, host_enforced_restrictions
            ),
        }

    # The trust file is only a cache. Authority is re-checked at execution time
    # against the current skill content, boundary, module tree, source path and
    # command, by the host's verifier.
    stored_receipt = trust_state.get("approval_receipt")
    approval_ok, approval_reasons = verify_host_approval_receipt(
        workspace_root,
        stored_receipt if isinstance(stored_receipt, dict) else None,
        skill_id=skill_id,
        unit=unit,
        module=mod,
        content_sha256=unit.content_sha256,
        run_id=str((stored_receipt or {}).get("run_id", ""))
        if isinstance(stored_receipt, dict)
        else "",
        command=command,
        host_enforced_restrictions=host_enforced_restrictions,
        authority_verifier=authority_verifier,
    )
    if not approval_ok:
        return {
            "allowed": False,
            "execution_mode": execution_mode,
            "reason": f"AUTO_RUN_BLOCKED_APPROVAL_UNVERIFIED:{','.join(approval_reasons)}",
            "trust_stage": stage,
        }

    return {
        "allowed": True,
        "execution_mode": execution_mode,
        "reason": None,
        "trust_stage": stage,
        "authorized_by": "host_authority_verifier",
        "verified_content_sha256": unit.content_sha256,
        "verified_boundary": unit.boundary.to_dict(),
        "verified_module_source_path": mod.source_path,
        "verified_module_tree_sha256": stored_receipt.get("module_tree_sha256")
        if isinstance(stored_receipt, dict)
        else None,
        "verified_command": command,
    }


def execute_modular_run(
    workspace_root: Path,
    *,
    run_id: str,
    prompt: str,
    profile_name: str | None = None,
    skill_hooks: dict[str, Callable[[str, str], dict[str, Any]]] | None = None,
    skill_commands: dict[str, list[str]] | None = None,
    build_cmd: list[str] | None = None,
    verify_cmd: list[str] | None = None,
    builder_actor: str = "factory-builder",
    verifier_actor: str = "factory-independent-verifier",
    builder_session_id: str = "builder-session-01",
    verifier_session_id: str = "verifier-session-02",
    timeout_s: float = 15.0,
    deduplicate_by_slot: bool = True,
    mid_run_callback: Callable[[Path], None] | None = None,
    explicit_taste_feedback: list[str] | None = None,
    external_search_roots: list[Path] | None = None,
    selective_activation: bool = False,
    execution_mode: str = "manual",
    env_fingerprint: str | None = None,
    authority_verifier: ApprovalAuthorityVerifier | None = None,
    host_enforced_restrictions: frozenset[str] | set[str] | tuple[str, ...] = (),
) -> dict[str, Any]:
    """Run the modular factory loop with preflight gap analysis, trust gating, subprocess isolation, and Progressive Disclosure.

    `selective_activation=True` is task-scoped: it enables only the task's
    skills for this run and restores every module's and skill's previous
    `enabled` flag afterwards, even when the run raises.
    """
    if execution_mode not in ("manual", "shadow", "auto"):
        raise ValueError(f"unsupported execution_mode: {execution_mode}")
    host_enforced_restrictions = validate_host_enforced_restrictions(host_enforced_restrictions)

    def _run(selective_result: dict[str, Any] | None) -> dict[str, Any]:
        return _execute_modular_run_locked(
            workspace_root,
            run_id=run_id,
            prompt=prompt,
            profile_name=profile_name,
            skill_hooks=skill_hooks,
            skill_commands=skill_commands,
            build_cmd=build_cmd,
            verify_cmd=verify_cmd,
            builder_actor=builder_actor,
            verifier_actor=verifier_actor,
            builder_session_id=builder_session_id,
            verifier_session_id=verifier_session_id,
            timeout_s=timeout_s,
            deduplicate_by_slot=deduplicate_by_slot,
            mid_run_callback=mid_run_callback,
            explicit_taste_feedback=explicit_taste_feedback,
            external_search_roots=external_search_roots,
            selective_result=selective_result,
            execution_mode=execution_mode,
            env_fingerprint=env_fingerprint,
            authority_verifier=authority_verifier,
            host_enforced_restrictions=host_enforced_restrictions,
        )

    # The run lock is taken before any task-scoped activation and released only
    # after it is restored, so a concurrent run can neither interleave with the
    # activation nor block the restore.
    acquire_run_lock(workspace_root, run_id)
    try:
        if not selective_activation:
            return _run(None)

        prior_activation = snapshot_activation_state(workspace_root)
        # Persisted so a killed run's flags can be restored (`recover-stale-lock`).
        save_pending_selective_restore(workspace_root, run_id, prior_activation)
        try:
            selective_result = select_and_activate_for_task(
                workspace_root,
                prompt,
                profile_name=profile_name,
                explicit_taste_feedback=explicit_taste_feedback,
                deduplicate_by_slot=deduplicate_by_slot,
                disable_others=True,
                owner_run_id=run_id,
            )
            drift = verify_lock_integrity(workspace_root)
            if drift:
                raise RuntimeError(f"MID_RUN_SKILL_DRIFT: {drift}")
            result = _run(selective_result)
        except BaseException as run_exc:
            try:
                restore_activation_state(workspace_root, prior_activation, owner_run_id=run_id)
                clear_pending_selective_restore(workspace_root, run_id)
            except Exception as restore_exc:  # keep the run's own error primary
                add_note = getattr(run_exc, "add_note", None)  # Python 3.11+
                if callable(add_note):
                    add_note(f"selective restore also failed: {restore_exc!r}")
            raise

        # A failing restore must not lose the run's result: report it instead.
        try:
            restored = restore_activation_state(
                workspace_root, prior_activation, owner_run_id=run_id
            )
        except Exception as restore_exc:
            selective_result["registry_state_after_run"] = "RESTORE_FAILED"
            selective_result["restore_error"] = f"{type(restore_exc).__name__}: {restore_exc}"
            verdict = result["run_verdict"]
            result["run_verdict"] = {
                "decision": "FAIL",
                "reasons": [*verdict.get("reasons", []), "selective_restore_failed"],
            }
        else:
            clear_pending_selective_restore(workspace_root, run_id)
            selective_result["registry_state_after_run"] = "RESTORED"
            selective_result["restored_skill_flags"] = restored
        return result
    finally:
        clear_skill_process_groups(workspace_root, run_id)
        release_run_lock(workspace_root)


def _execute_modular_run_locked(
    workspace_root: Path,
    *,
    run_id: str,
    prompt: str,
    profile_name: str | None,
    skill_hooks: dict[str, Callable[[str, str], dict[str, Any]]] | None,
    skill_commands: dict[str, list[str]] | None,
    build_cmd: list[str] | None,
    verify_cmd: list[str] | None,
    builder_actor: str,
    verifier_actor: str,
    builder_session_id: str,
    verifier_session_id: str,
    timeout_s: float,
    deduplicate_by_slot: bool,
    mid_run_callback: Callable[[Path], None] | None,
    explicit_taste_feedback: list[str] | None,
    external_search_roots: list[Path] | None,
    selective_result: dict[str, Any] | None,
    execution_mode: str,
    env_fingerprint: str | None,
    authority_verifier: ApprovalAuthorityVerifier | None,
    host_enforced_restrictions: frozenset[str] | set[str] | tuple[str, ...],
) -> dict[str, Any]:
    t0 = time.monotonic()
    preflight_gap_report = analyze_capability_gaps(
        workspace_root,
        prompt,
        profile_name=profile_name,
        external_search_roots=external_search_roots,
        explicit_taste_feedback=explicit_taste_feedback,
    )
    degraded_ids = {
        sid
        for sid, info in preflight_gap_report["skill_assessments"].items()
        if info.get("state") == "DEGRADED"
    }
    silent_zero_ids = set(preflight_gap_report.get("hook_diagnostics", {}).keys())

    if deduplicate_by_slot:
        route_plan = preflight_gap_report["route_plan"]
    else:
        route_plan = route_skills_for_task(
            workspace_root,
            prompt,
            profile_name=profile_name,
            deduplicate_by_slot=False,
            explicit_taste_feedback=explicit_taste_feedback,
            degraded_skill_ids=degraded_ids,
            silent_zero_skill_ids=silent_zero_ids,
        )

    # Only rules the host itself configured (its taste file or explicit
    # feedback) are handed to subprocesses as host taste; a repo-shipped
    # profile's defaults are reported separately and never relabelled.
    taste_items = [
        item
        for item in preflight_gap_report.get("taste_synthesis", {}).get("personal_taste", [])
        if isinstance(item, dict) and item.get("rule")
    ]
    active_taste_rules = [
        item["rule"] for item in taste_items if item.get("authority") == "HOST_CONFIGURED"
    ]
    profile_default_taste_rules = [
        item["rule"] for item in taste_items if item.get("authority") == "PROFILE_DEFAULT"
    ]

    modules = load_registry_state(workspace_root)
    unit_lookup = {
        sid: (mod, unit)
        for mod in modules.values()
        if mod.enabled
        for sid, unit in mod.skills.items()
        if unit.enabled
    }

    disclosed_skills: list[str] = []
    executed_skills: list[str] = []
    isolated_faults: list[str] = []
    permission_violations: list[str] = []
    skill_outputs: dict[str, Any] = {}
    context_bytes_disclosed = 0

    # Explicitly surface any DEGRADED skill skipped by preflight when a caller tried to invoke it
    for blocked_sid in sorted(degraded_ids):
        if (skill_commands and blocked_sid in skill_commands) or (
            skill_hooks and blocked_sid in skill_hooks
        ):
            isolated_faults.append(f"fault_isolated:{blocked_sid}:DegradedPreflightBlocked")
            skill_outputs[blocked_sid] = {
                "status": "UNOBSERVED",
                "registration_state": "REGISTERED",
                "disclosure_state": "NONE",
                "execution_state": "DEGRADED_PREFLIGHT_BLOCKED",
                "enforcement_mode": "PREFLIGHT_GAP_ANALYZER",
                "gate_verdict": "FAIL",
                "reason": f"DEGRADED_PREFLIGHT_BLOCKED:{blocked_sid}",
            }

    if mid_run_callback is not None:
        mid_run_callback(workspace_root)

    execution_waves = _build_execution_waves(route_plan["selected_skills"], unit_lookup)
    parallel_waves_executed = 0

    # `auto` executions run from a private read-only copy of the module tree that
    # was checked against the approval immediately before the process starts.
    exec_snapshots: dict[str, tuple[Path, str]] = {}
    # Skills whose process group still had members when the skill exited.
    descendants_killed: dict[str, bool] = {}

    # The run's authoritative list of skill process groups lives in memory; the
    # file is rewritten from it, never read back, and each harness write becomes
    # the expected state for the post-run comparison.
    run_groups: list[int] = []
    harness_written: dict[str, bytes] = {}
    run_state_tampering: list[str] = []
    record_rel = process_groups_record_rel(run_id)
    record_lock = threading.Lock()

    def _record_group(pgid: int) -> None:
        with record_lock:
            record_path = workspace_root / record_rel
            expected = harness_written.get(record_rel)
            try:
                current = record_path.read_bytes() if record_path.exists() else None
            except OSError:
                current = None
            if current != expected:
                run_state_tampering.append(record_rel)
            run_groups.append(pgid)
            harness_written[record_rel] = write_skill_process_groups(
                workspace_root, run_id, run_groups
            )

    def _harness_written_now() -> dict[str, bytes]:
        with record_lock:
            return dict(harness_written)

    def _auto_block(skill_id: str, reason: str, body: str) -> None:
        permission_violations.append(
            f"PERMISSION_BOUNDARY_VIOLATION:autonomous_exec_unverified:{skill_id}:{reason}"
        )
        isolated_faults.append(f"fault_isolated:{skill_id}:AutonomousExecBlocked")
        skill_outputs[skill_id] = {
            "status": "UNOBSERVED",
            "registration_state": "REGISTERED",
            "disclosure_state": "DISCLOSED" if body else "NONE",
            "execution_state": "BLOCKED_UNVERIFIED_AUTONOMOUS_EXECUTION",
            "enforcement_mode": "AUTO_RUN_PRE_EXEC_RECHECK",
            "gate_verdict": "FAIL",
            "reason": reason,
        }

    def _auto_pre_exec(skill_id: str) -> str | None:
        """Re-check permission and bindings right before this skill executes.

        Earlier skills in the run may have changed files since the wave started,
        so the wave-level check alone is not enough. Returns a blocking reason or
        `None`; for a command it also takes the read-only execution snapshot.
        """
        if execution_mode != "auto":
            return None
        cmd = (skill_commands or {}).get(skill_id)
        perm = check_execution_permission(
            workspace_root,
            skill_id,
            execution_mode=execution_mode,
            env_fingerprint=env_fingerprint,
            authority_verifier=authority_verifier,
            command=cmd,
            host_enforced_restrictions=host_enforced_restrictions,
        )
        if not perm["allowed"]:
            return str(perm["reason"] or "AUTO_RUN_BLOCKED")
        run_mod, run_unit = unit_lookup[skill_id]
        if (
            run_unit.content_sha256 != perm.get("verified_content_sha256")
            or run_unit.boundary.to_dict() != perm.get("verified_boundary")
            or run_mod.source_path != perm.get("verified_module_source_path")
        ):
            return "AUTO_RUN_BLOCKED_UNIT_CHANGED_SINCE_RUN_START"
        if cmd is not None:
            approved = perm.get("verified_module_tree_sha256")
            copy_root, err = _snapshot_module_for_exec(Path(run_mod.source_path), approved)
            if copy_root is None or not approved:
                return f"AUTO_RUN_BLOCKED_EXEC_SNAPSHOT:{err}"
            exec_snapshots[skill_id] = (copy_root, approved)
        return None

    def _exec_module_root(skill_id: str) -> str:
        snap = exec_snapshots.get(skill_id)
        return str(snap[0]) if snap is not None else unit_lookup[skill_id][0].source_path

    def _post_exec_checks(
        skill_ids: list[str], factory_before: dict[str, bytes], *, parallel: bool
    ) -> None:
        """Roll back `.hyodo/factory/` changes and check the execution snapshots."""
        changes = _restore_factory_state(workspace_root, factory_before, _harness_written_now())
        with record_lock:
            if run_state_tampering:
                changes = sorted({*changes, *(f"modified:{r}" for r in run_state_tampering)})
                run_state_tampering.clear()
        if changes:
            label = f"parallel_wave[{','.join(skill_ids)}]" if parallel else skill_ids[0]
            attribution = ":attribution=UNOBSERVED" if parallel else ""
            violation = (
                f"PERMISSION_BOUNDARY_VIOLATION:factory_state_write_forbidden:{label}"
                f"{attribution}:{','.join(changes)}"
            )
            permission_violations.append(violation)
            isolated_faults.append(f"fault_isolated:{label}:FactoryStateWrite")
            for sid in skill_ids:
                if sid in executed_skills:
                    executed_skills.remove(sid)
                skill_outputs[sid] = {
                    **skill_outputs.get(sid, {}),
                    "status": "UNOBSERVED",
                    "execution_state": "ROLLED_BACK_ILLEGAL_WRITE",
                    "enforcement_mode": "POST_RUN_FACTORY_STATE_ROLLBACK",
                    "gate_verdict": "UNOBSERVED" if parallel else "FAIL",
                    "factory_state_changes": changes,
                    "reason": violation,
                }
                if parallel:
                    skill_outputs[sid]["write_attribution"] = "UNOBSERVED"
        for sid in skill_ids:
            snap = exec_snapshots.pop(sid, None)
            if snap is None:
                continue
            copy_root, approved = snap
            after, _count, _err = compute_module_tree_digest(copy_root)
            _discard_exec_snapshot(copy_root)
            if after != approved:
                violation = f"PERMISSION_BOUNDARY_VIOLATION:module_exec_snapshot_modified:{sid}"
                permission_violations.append(violation)
                isolated_faults.append(f"fault_isolated:{sid}:ModuleSnapshotModified")
                if sid in executed_skills:
                    executed_skills.remove(sid)
                skill_outputs[sid] = {
                    **skill_outputs.get(sid, {}),
                    "status": "UNOBSERVED",
                    "execution_state": "MODULE_SNAPSHOT_MODIFIED_DURING_RUN",
                    "gate_verdict": "FAIL",
                    "reason": violation,
                }
            elif sid in skill_outputs:
                # What is observed: the snapshot was provided (CLAUDE_PLUGIN_ROOT /
                # CLAUDE_SKILL_DIR pointed at it) and was unchanged afterwards. Which
                # files the process actually read is not observed, so the snapshot
                # is never claimed as what ran. A command line that visibly names
                # the original module directory is reported as such; one that
                # reaches it another way (split or computed paths) is not detected.
                original = unit_lookup[sid][0].source_path
                spellings = {original, original.removeprefix("/private")} - {""}
                cmd_text = " ".join((skill_commands or {}).get(sid) or [])
                skill_outputs[sid]["module_snapshot_coverage"] = "UNOBSERVED"
                if any(spelling in cmd_text for spelling in spellings):
                    skill_outputs[sid]["executed_from"] = "ORIGINAL_PATH_REFERENCED"
                else:
                    skill_outputs[sid]["executed_from"] = "MODULE_SNAPSHOT_PROVIDED"
        for sid in skill_ids:
            if descendants_killed.pop(sid, False) and sid in skill_outputs:
                skill_outputs[sid]["descendants_killed_after_exit"] = True

    skill_started_at: dict[str, str] = {}
    try:
        for wave in execution_waves:
            # First enforce execution_mode (`AUTO_RUN`) trust gate per skill in wave before disclosing/running
            runnable_wave: list[str] = []
            wave_ts = utc_now_iso()
            for skill_id in wave:
                skill_started_at[skill_id] = wave_ts
                perm_check = check_execution_permission(
                    workspace_root,
                    skill_id,
                    execution_mode=execution_mode,
                    env_fingerprint=env_fingerprint,
                    authority_verifier=authority_verifier,
                    command=(skill_commands or {}).get(skill_id),
                    host_enforced_restrictions=host_enforced_restrictions,
                )
                if perm_check["allowed"] and execution_mode == "auto":
                    # The run executes the unit loaded at run start; it must be the
                    # exact unit whose approval was just verified, or a lock.json
                    # edit between the two reads would widen the boundary.
                    _run_mod, _run_unit = unit_lookup[skill_id]
                    if (
                        _run_unit.content_sha256 != perm_check.get("verified_content_sha256")
                        or _run_unit.boundary.to_dict() != perm_check.get("verified_boundary")
                        or _run_mod.source_path != perm_check.get("verified_module_source_path")
                    ):
                        perm_check = {
                            **perm_check,
                            "allowed": False,
                            "reason": "AUTO_RUN_BLOCKED_UNIT_CHANGED_SINCE_RUN_START",
                        }
                if not perm_check["allowed"]:
                    reason = str(perm_check["reason"] or "AUTO_RUN_BLOCKED")
                    permission_violations.append(
                        f"PERMISSION_BOUNDARY_VIOLATION:autonomous_exec_unverified:{skill_id}:{reason}"
                    )
                    isolated_faults.append(f"fault_isolated:{skill_id}:AutonomousExecBlocked")
                    skill_outputs[skill_id] = {
                        "status": "UNOBSERVED",
                        "registration_state": "REGISTERED",
                        "disclosure_state": "NONE",
                        "execution_state": "BLOCKED_UNVERIFIED_AUTONOMOUS_EXECUTION",
                        "enforcement_mode": "AUTO_RUN_TRUST_GATE",
                        "gate_verdict": "FAIL",
                        "trust_stage": perm_check.get("trust_stage"),
                        "reason": reason,
                    }
                else:
                    runnable_wave.append(skill_id)

            if not runnable_wave:
                continue

            wave_bodies: dict[str, str] = {}
            for skill_id in runnable_wave:
                mod, unit = unit_lookup[skill_id]
                body = ""
                if mod.adapter in ("agent-skills", "claude-plugin"):
                    body = disclose_skill_body(mod, skill_id)
                    disclosed_skills.append(skill_id)
                    context_bytes_disclosed += len(body.encode("utf-8"))
                wave_bodies[skill_id] = body

            can_parallelize = len(runnable_wave) > 1 and all(
                (skill_commands or {}).get(sid) is not None
                and unit_lookup[sid][1].boundary.subprocess_exec
                and not unit_lookup[sid][1].boundary.filesystem_write
                for sid in runnable_wave
            )

            if can_parallelize:
                parallel_waves_executed += 1
                # Re-check every skill right before the wave starts; each one then runs
                # from its own execution snapshot taken at that check.
                wave_to_run: list[str] = []
                for sid in runnable_wave:
                    blocked_reason = _auto_pre_exec(sid)
                    if blocked_reason is not None:
                        _auto_block(sid, blocked_reason, wave_bodies[sid])
                    else:
                        wave_to_run.append(sid)
                if not wave_to_run:
                    continue
                factory_before = _factory_state_snapshot(workspace_root)
                # Whatever happens below, `.hyodo/factory/` is rolled back and the
                # execution copies are checked and discarded.
                try:
                    snap_before = _snapshot_workspace_files(workspace_root)

                    def _run_ro_cmd(
                        sid: str,
                    ) -> tuple[str, subprocess.CompletedProcess[str] | Exception]:
                        _m_rec, u = unit_lookup[sid]
                        cmd_args = (skill_commands or {})[sid]
                        try:
                            proc, killed = _run_skill_process(
                                cmd_args,
                                cwd=workspace_root,
                                env=_build_isolated_env(
                                    u,
                                    workspace_root,
                                    module_source_path=_exec_module_root(sid),
                                    active_taste_rules=active_taste_rules,
                                ),
                                timeout=timeout_s,
                                on_start=_record_group,
                            )
                            descendants_killed[sid] = killed
                            return sid, proc
                        except Exception as exc:
                            return sid, exc

                    with (
                        _readonly_workspace_guard(workspace_root),
                        ThreadPoolExecutor(max_workers=min(4, len(wave_to_run))) as pool,
                    ):
                        results = dict(pool.map(_run_ro_cmd, wave_to_run))

                    illegal_writes = _restore_and_detect_writes(workspace_root, snap_before)
                    if illegal_writes:
                        # The wave ran concurrently against one snapshot, so which skill
                        # wrote is not observable. Record one wave-level violation and
                        # mark per-skill attribution UNOBSERVED instead of blaming all.
                        wave_label = ",".join(wave_to_run)
                        permission_violations.append(
                            "PERMISSION_BOUNDARY_VIOLATION:filesystem_write_forbidden:"
                            f"parallel_wave[{wave_label}]:attribution=UNOBSERVED:"
                            f"{','.join(illegal_writes)}"
                        )
                        isolated_faults.append(
                            f"fault_isolated:parallel_wave[{wave_label}]:UnattributedWrite"
                        )
                    for skill_id in wave_to_run:
                        _, unit = unit_lookup[skill_id]
                        body = wave_bodies[skill_id]
                        outcome = results[skill_id]
                        if isinstance(outcome, subprocess.TimeoutExpired):
                            isolated_faults.append(f"fault_isolated:{skill_id}:TimeoutExpired")
                            skill_outputs[skill_id] = {
                                "status": "UNOBSERVED",
                                "execution_state": "TIMEOUT",
                                "gate_verdict": "FAIL",
                                "reason": str(outcome),
                                **_timeout_kill_fields(outcome),
                            }
                        elif isinstance(outcome, Exception):
                            isolated_faults.append(
                                f"fault_isolated:{skill_id}:{type(outcome).__name__}"
                            )
                            skill_outputs[skill_id] = {
                                "status": "UNOBSERVED",
                                "execution_state": "EXECUTED_FAIL",
                                "gate_verdict": "FAIL",
                                "reason": str(outcome),
                            }
                        else:
                            proc = outcome
                            stderr_text = proc.stderr.strip()
                            if illegal_writes:
                                skill_outputs[skill_id] = {
                                    "status": "UNOBSERVED",
                                    "registration_state": "REGISTERED",
                                    "disclosure_state": "DISCLOSED" if body else "NONE",
                                    "execution_state": "ROLLED_BACK_ILLEGAL_WRITE",
                                    "enforcement_mode": "POST_WRITE_SNAPSHOT_ROLLBACK",
                                    "gate_verdict": "UNOBSERVED",
                                    "write_attribution": "UNOBSERVED",
                                    "wave_illegal_writes": list(illegal_writes),
                                    "exit_code": proc.returncode,
                                    "reason": "PARALLEL_WAVE_WRITE_ROLLED_BACK:attribution=UNOBSERVED",
                                }
                            elif proc.returncode != 0 and (
                                "PermissionError" in stderr_text
                                or "Permission denied" in stderr_text
                            ):
                                violation = f"PERMISSION_BOUNDARY_VIOLATION:filesystem_write_blocked_pre_write:{skill_id}"
                                permission_violations.append(violation)
                                isolated_faults.append(f"fault_isolated:{skill_id}:PermissionError")
                                skill_outputs[skill_id] = {
                                    "status": "UNOBSERVED",
                                    "registration_state": "REGISTERED",
                                    "disclosure_state": "DISCLOSED" if body else "NONE",
                                    "execution_state": "BLOCKED_BY_OS_READONLY_MODE",
                                    "enforcement_mode": "PRE_WRITE_POSIX_CHMOD",
                                    "gate_verdict": "FAIL",
                                    "exit_code": proc.returncode,
                                    "reason": violation,
                                    "stderr": stderr_text[:400],
                                }
                            elif proc.returncode != 0:
                                isolated_faults.append(
                                    f"fault_isolated:{skill_id}:SubprocessExit_{proc.returncode}"
                                )
                                skill_outputs[skill_id] = {
                                    "status": "UNOBSERVED",
                                    "registration_state": "REGISTERED",
                                    "disclosure_state": "DISCLOSED" if body else "NONE",
                                    "execution_state": "EXECUTED_FAIL",
                                    "gate_verdict": "FAIL",
                                    "exit_code": proc.returncode,
                                    "stderr": stderr_text[:400],
                                }
                            else:
                                executed_skills.append(skill_id)
                                skill_outputs[skill_id] = {
                                    "status": "OBSERVED",
                                    "registration_state": "REGISTERED",
                                    "disclosure_state": "DISCLOSED" if body else "NONE",
                                    "execution_state": "EXECUTED_PASS",
                                    "gate_verdict": "PASS",
                                    "exit_code": 0,
                                    **_stdout_integrity_fields(proc.stdout),
                                    "role_hint": unit.role_hint,
                                    "content_sha256": unit.content_sha256,
                                }
                finally:
                    _post_exec_checks(wave_to_run, factory_before, parallel=True)
                continue

            for skill_id in runnable_wave:
                mod, unit = unit_lookup[skill_id]
                body = wave_bodies[skill_id]
                serial_factory_before: dict[str, bytes] | None = None
                try:
                    cmd = (skill_commands or {}).get(skill_id)
                    hook_fn = (skill_hooks or {}).get(skill_id)

                    if cmd is not None or hook_fn is not None:
                        blocked_reason = (
                            _auto_pre_exec(skill_id)
                            if cmd is None or unit.boundary.subprocess_exec
                            else None
                        )
                        if blocked_reason is not None:
                            _auto_block(skill_id, blocked_reason, body)
                            continue
                        serial_factory_before = _factory_state_snapshot(workspace_root)

                    if cmd is not None:
                        if not unit.boundary.subprocess_exec:
                            violation = f"PERMISSION_BOUNDARY_VIOLATION:subprocess_exec_forbidden:{skill_id}"
                            permission_violations.append(violation)
                            isolated_faults.append(f"fault_isolated:{skill_id}:PermissionError")
                            skill_outputs[skill_id] = {
                                "status": "UNOBSERVED",
                                "registration_state": "REGISTERED",
                                "disclosure_state": "DISCLOSED" if body else "NONE",
                                "execution_state": "BLOCKED_BY_PERMISSION",
                                "enforcement_mode": "PRE_EXEC_POLICY_GATE",
                                "gate_verdict": "FAIL",
                                "reason": violation,
                            }
                            continue

                        snap_before = (
                            _snapshot_workspace_files(workspace_root)
                            if not unit.boundary.filesystem_write
                            else {}
                        )
                        guard_ctx = (
                            _readonly_workspace_guard(workspace_root)
                            if not unit.boundary.filesystem_write
                            else contextlib.nullcontext()
                        )
                        with guard_ctx:
                            proc, killed = _run_skill_process(
                                cmd,
                                cwd=workspace_root,
                                env=_build_isolated_env(
                                    unit,
                                    workspace_root,
                                    module_source_path=_exec_module_root(skill_id),
                                    active_taste_rules=active_taste_rules,
                                ),
                                timeout=timeout_s,
                                on_start=_record_group,
                            )
                            descendants_killed[skill_id] = killed
                        stderr_text = proc.stderr.strip()
                        if not unit.boundary.filesystem_write:
                            illegal_writes = _restore_and_detect_writes(workspace_root, snap_before)
                            if illegal_writes:
                                violation = (
                                    f"PERMISSION_BOUNDARY_VIOLATION:filesystem_write_forbidden:{skill_id}:"
                                    f"{','.join(illegal_writes)}"
                                )
                                permission_violations.append(violation)
                                isolated_faults.append(f"fault_isolated:{skill_id}:PermissionError")
                                skill_outputs[skill_id] = {
                                    "status": "UNOBSERVED",
                                    "registration_state": "REGISTERED",
                                    "disclosure_state": "DISCLOSED" if body else "NONE",
                                    "execution_state": "ROLLED_BACK_ILLEGAL_WRITE",
                                    "enforcement_mode": "POST_WRITE_SNAPSHOT_ROLLBACK",
                                    "gate_verdict": "FAIL",
                                    "reason": violation,
                                }
                                continue
                            if proc.returncode != 0 and (
                                "PermissionError" in stderr_text
                                or "Permission denied" in stderr_text
                            ):
                                violation = f"PERMISSION_BOUNDARY_VIOLATION:filesystem_write_blocked_pre_write:{skill_id}"
                                permission_violations.append(violation)
                                isolated_faults.append(f"fault_isolated:{skill_id}:PermissionError")
                                skill_outputs[skill_id] = {
                                    "status": "UNOBSERVED",
                                    "registration_state": "REGISTERED",
                                    "disclosure_state": "DISCLOSED" if body else "NONE",
                                    "execution_state": "BLOCKED_BY_OS_READONLY_MODE",
                                    "enforcement_mode": "PRE_WRITE_POSIX_CHMOD",
                                    "gate_verdict": "FAIL",
                                    "exit_code": proc.returncode,
                                    "reason": violation,
                                    "stderr": stderr_text[:400],
                                }
                                continue

                        if proc.returncode != 0:
                            isolated_faults.append(
                                f"fault_isolated:{skill_id}:SubprocessExit_{proc.returncode}"
                            )
                            skill_outputs[skill_id] = {
                                "status": "UNOBSERVED",
                                "registration_state": "REGISTERED",
                                "disclosure_state": "DISCLOSED" if body else "NONE",
                                "execution_state": "EXECUTED_FAIL",
                                "gate_verdict": "FAIL",
                                "exit_code": proc.returncode,
                                "stderr": stderr_text[:400],
                            }
                        else:
                            executed_skills.append(skill_id)
                            skill_outputs[skill_id] = {
                                "status": "OBSERVED",
                                "registration_state": "REGISTERED",
                                "disclosure_state": "DISCLOSED" if body else "NONE",
                                "execution_state": "EXECUTED_PASS",
                                "gate_verdict": "PASS",
                                "exit_code": 0,
                                **_stdout_integrity_fields(proc.stdout),
                                "role_hint": unit.role_hint,
                                "content_sha256": unit.content_sha256,
                            }
                    elif hook_fn is not None:
                        snap_before = (
                            _snapshot_workspace_files(workspace_root)
                            if not unit.boundary.filesystem_write
                            else {}
                        )
                        guard_ctx = (
                            _readonly_workspace_guard(workspace_root)
                            if not unit.boundary.filesystem_write
                            else contextlib.nullcontext()
                        )
                        with guard_ctx:
                            hook_res = hook_fn(skill_id, body)
                        if not unit.boundary.filesystem_write:
                            illegal_writes = _restore_and_detect_writes(workspace_root, snap_before)
                            if illegal_writes:
                                violation = (
                                    f"PERMISSION_BOUNDARY_VIOLATION:filesystem_write_forbidden:{skill_id}:"
                                    f"{','.join(illegal_writes)}"
                                )
                                permission_violations.append(violation)
                                isolated_faults.append(f"fault_isolated:{skill_id}:PermissionError")
                                skill_outputs[skill_id] = {
                                    "status": "UNOBSERVED",
                                    "registration_state": "REGISTERED",
                                    "disclosure_state": "DISCLOSED" if body else "NONE",
                                    "execution_state": "ROLLED_BACK_ILLEGAL_WRITE",
                                    "enforcement_mode": "POST_WRITE_SNAPSHOT_ROLLBACK",
                                    "gate_verdict": "FAIL",
                                    "reason": violation,
                                }
                                continue
                        executed_skills.append(skill_id)
                        skill_outputs[skill_id] = {
                            "status": "OBSERVED",
                            "registration_state": "REGISTERED",
                            "disclosure_state": "DISCLOSED" if body else "NONE",
                            "execution_state": "EXECUTED_PASS",
                            "gate_verdict": "PASS",
                            **hook_res,
                        }
                    else:
                        skill_outputs[skill_id] = {
                            "status": "OBSERVED",
                            "registration_state": "REGISTERED",
                            "disclosure_state": "DISCLOSED" if body else "REGISTERED_ONLY",
                            "execution_state": "DISCLOSED_ONLY",
                            "gate_verdict": "UNOBSERVED",
                            "role_hint": unit.role_hint,
                            "content_sha256": unit.content_sha256,
                        }
                except subprocess.TimeoutExpired as exc:
                    isolated_faults.append(f"fault_isolated:{skill_id}:TimeoutExpired")
                    skill_outputs[skill_id] = {
                        "status": "UNOBSERVED",
                        "execution_state": "TIMEOUT",
                        "gate_verdict": "FAIL",
                        "reason": str(exc),
                        **_timeout_kill_fields(exc),
                    }
                except PermissionError as exc:
                    violation = f"PERMISSION_BOUNDARY_VIOLATION:filesystem_write_blocked_pre_write:{skill_id}"
                    permission_violations.append(violation)
                    isolated_faults.append(f"fault_isolated:{skill_id}:PermissionError")
                    skill_outputs[skill_id] = {
                        "status": "UNOBSERVED",
                        "registration_state": "REGISTERED",
                        "disclosure_state": "DISCLOSED" if body else "NONE",
                        "execution_state": "BLOCKED_BY_OS_READONLY_MODE",
                        "enforcement_mode": "PRE_WRITE_POSIX_CHMOD",
                        "gate_verdict": "FAIL",
                        "reason": str(exc),
                    }
                except RuntimeError as exc:
                    if "MID_RUN_SKILL_DRIFT" in str(exc):
                        raise
                    isolated_faults.append(f"fault_isolated:{skill_id}:{type(exc).__name__}")
                    skill_outputs[skill_id] = {
                        "status": "UNOBSERVED",
                        "execution_state": "EXECUTED_FAIL",
                        "gate_verdict": "FAIL",
                        "reason": str(exc),
                    }
                except Exception as exc:
                    isolated_faults.append(f"fault_isolated:{skill_id}:{type(exc).__name__}")
                    skill_outputs[skill_id] = {
                        "status": "UNOBSERVED",
                        "execution_state": "EXECUTED_FAIL",
                        "gate_verdict": "FAIL",
                        "reason": str(exc),
                    }
                finally:
                    if serial_factory_before is not None:
                        _post_exec_checks([skill_id], serial_factory_before, parallel=False)
    finally:
        # Never leak an execution copy, whatever ended the wave loop.
        for leftover_root, _approved in list(exec_snapshots.values()):
            _discard_exec_snapshot(leftover_root)
        exec_snapshots.clear()

    build_receipt: dict[str, Any] = {"state": "UNOBSERVED"}
    if build_cmd is not None:
        b_env = _with_pythonpath(clean_git_env(), workspace_root)
        b_env["HYODO_ACTOR_ID"] = builder_actor
        b_env["HYODO_SESSION_ID"] = builder_session_id
        if active_taste_rules:
            b_env["HYODO_HOST_PERSONAL_TASTE_JSON"] = json.dumps(active_taste_rules)
        b_proc = subprocess.run(
            build_cmd,
            cwd=str(workspace_root),
            env=b_env,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
            start_new_session=True,
        )
        build_receipt = {
            "state": "OBSERVED",
            "actor_id": builder_actor,
            "session_id": builder_session_id,
            "pid": os.getpid(),
            "exit_code": b_proc.returncode,
            "status": "PASS" if b_proc.returncode == 0 else "FAIL",
            **_stdout_integrity_fields(b_proc.stdout),
        }

    six_lenses = measure_workspace_six_lenses(workspace_root)
    exact_sha = six_lenses["exact_artifact_sha"]
    target_sha = exact_sha if exact_sha != "UNOBSERVED" else "0" * 40

    verifier_receipt: dict[str, Any] = {"state": "UNOBSERVED"}
    if verify_cmd is not None:
        if builder_actor == verifier_actor or builder_session_id == verifier_session_id:
            verifier_receipt = {
                "state": "HOLD",
                "status": "HOLD",
                "reason": "SELF_REVIEW_FORBIDDEN: builder and independent verifier must not share actor_id or session_id",
            }
        else:
            v_env = _with_pythonpath(clean_git_env(), workspace_root)
            v_env["HYODO_ACTOR_ID"] = verifier_actor
            v_env["HYODO_SESSION_ID"] = verifier_session_id
            for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
                v_env.pop(k, None)
            v_proc = subprocess.run(
                verify_cmd,
                cwd=str(workspace_root),
                env=v_env,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
                start_new_session=True,
            )
            v_stdout_meta = _stdout_integrity_fields(v_proc.stdout)
            verified_at = utc_now_iso()
            verifier_nameplate = build_nameplate(
                actor_id=verifier_actor,
                role="verifier",
                repo=workspace_root.name,
                exact_artifact_sha=target_sha,
                observed_at=verified_at,
                runtime={"session_id": verifier_session_id, "host": "hyodo-factory-verifier"},
            )
            attestation = verify_exact_candidate(
                root=workspace_root,
                expected_artifact_sha=target_sha,
                verifier_nameplate=verifier_nameplate,
                evidence={
                    "verify_exit_code": v_proc.returncode,
                    "verify_stdout_sha256": v_stdout_meta["full_stdout_sha256"][:12],
                    "full_verify_stdout_sha256": v_stdout_meta["full_stdout_sha256"],
                    "normalized_verify_stdout_sha256": v_stdout_meta["normalized_stdout_sha256"],
                },
                observed_at=verified_at,
            )
            verifier_receipt = {
                "state": "OBSERVED",
                "status": "PASS"
                if (v_proc.returncode == 0 and attestation["verdict"] == "PASS")
                else "FAIL",
                "exit_code": v_proc.returncode,
                "actor_id": verifier_actor,
                "session_id": verifier_session_id,
                **v_stdout_meta,
                "attestation": attestation,
            }

    duration_ms = int((time.monotonic() - t0) * 1000)

    orchestration_observations_recorded = 0
    attested_tags = [f"host_attested:{name}" for name in host_enforced_restrictions]
    skill_event_ids: dict[str, str] = {}
    wave_event_ids: list[list[str]] = []
    step_idx = 0
    for wave_idx, wave in enumerate(execution_waves):
        is_parallel_wave = len(wave) > 1 and all(
            (skill_commands or {}).get(sid) is not None
            and sid in unit_lookup
            and unit_lookup[sid][1].boundary.subprocess_exec
            and not unit_lookup[sid][1].boundary.filesystem_write
            for sid in wave
        )
        exec_mode = "parallel" if is_parallel_wave else "serial"
        current_wave_events: list[str] = []
        for skill_id in wave:
            _, unit = unit_lookup[skill_id]
            safe_sid = skill_id.replace("/", "-").replace("_", "-")
            ev_id = f"evt-{run_id}-w{wave_idx}-{safe_sid}"
            obs_id = f"obs-{run_id}-w{wave_idx}-{safe_sid}"
            skill_event_ids[skill_id] = ev_id
            current_wave_events.append(ev_id)

            raw_ev = {
                "schema_version": AGENT_EVENT_SCHEMA_VERSION,
                "event_id": ev_id,
                "run_id": run_id,
                "step_index": step_idx,
                "ts": skill_started_at.get(skill_id) or utc_now_iso(),
                "kind": "tool_call",
                "actor": "agent",
                "tool": {
                    "name": skill_id,
                    "args_digest": content_digest(prompt),
                    "paths": [],
                },
                "policy": unevaluated_policy(),
            }
            if attested_tags:
                # The host's enforcement claim travels with the evidence it shaped.
                raw_ev["meta"] = {"tags": list(attested_tags)}
            ok_ev, _, norm_ev = validate_event(raw_ev)
            if ok_ev and norm_ev is not None:
                append_agent_event(workspace_root, norm_ev)
            step_idx += 1

            dep_event_ids = sorted(
                {
                    skill_event_ids[d]
                    for d in unit.dependencies
                    if d in skill_event_ids and skill_event_ids[d] != ev_id
                }
            )
            if not dep_event_ids and wave_idx > 0:
                dep_event_ids = sorted(set(wave_event_ids[wave_idx - 1]))

            out = skill_outputs.get(skill_id, {})
            exec_state = str(out.get("execution_state", "DISCLOSED_ONLY"))
            if exec_state in ("EXECUTED_PASS", "DISCLOSED_ONLY"):
                node_state = "completed"
            elif exec_state in (
                "BLOCKED_BY_PERMISSION",
                "BLOCKED_BY_OS_READONLY_MODE",
                "BLOCKED_UNVERIFIED_AUTONOMOUS_EXECUTION",
                "DEGRADED_PREFLIGHT_BLOCKED",
            ):
                node_state = "blocked"
            elif exec_state == "ROLLED_BACK_ILLEGAL_WRITE":
                node_state = "rolled_back"
            else:
                node_state = "failed"

            obs_payload: dict[str, Any] = {
                "schema": ORCHESTRATION_OBSERVATION_SCHEMA_VERSION,
                "observation_id": obs_id,
                "run_id": run_id,
                "event_id": ev_id,
                "ts": skill_started_at.get(skill_id) or utc_now_iso(),
                "node_id": skill_id,
                "execution": exec_mode,
                "depends_on": dep_event_ids,
                "join_policy": "all" if len(dep_event_ids) >= 2 else None,
                "state": node_state,
                "attempt": 1,
                "approval_wait_ms": 0,
                "human_interventions": 0,
                "unobserved_claim_count": 1 if exec_state == "DISCLOSED_ONLY" else 0,
                "policy_conflict_count": 1 if node_state in ("blocked", "rolled_back") else 0,
                "verification_failure_count": 1 if out.get("gate_verdict") == "FAIL" else 0,
                "evidence_refs": [f"sha256:{unit.content_sha256[:12]}", *attested_tags],
            }
            if append_orchestration_observation(workspace_root, obs_payload):
                orchestration_observations_recorded += 1
        wave_event_ids.append(current_wave_events)

    for skill_id, out in skill_outputs.items():
        if skill_id in unit_lookup and isinstance(out, dict):
            out["boundary_enforcement"] = boundary_enforcement_report(
                unit_lookup[skill_id][1].boundary, host_enforced_restrictions
            )

    run_verdict = _compute_run_verdict(
        routed_skills=list(route_plan["selected_skills"]),
        skill_outputs=skill_outputs,
        executed_skills=executed_skills,
        isolated_faults=isolated_faults,
        permission_violations=permission_violations,
        build_receipt=build_receipt,
        verifier_receipt=verifier_receipt,
    )

    modes = [str(v.get("execution_state", "")) for v in skill_outputs.values()]
    execution_summary = {
        "skills_routed": len(route_plan["selected_skills"]),
        "execution_waves_count": len(execution_waves),
        "parallel_waves_executed": parallel_waves_executed,
        "orchestration_observations_recorded": orchestration_observations_recorded,
        "skills_disclosed_only": sum(1 for m in modes if m == "DISCLOSED_ONLY"),
        "skills_executed_pass": sum(1 for m in modes if m == "EXECUTED_PASS"),
        "skills_executed_fail": sum(1 for m in modes if m == "EXECUTED_FAIL"),
        "skills_blocked_by_permission": sum(
            1
            for m in modes
            if m
            in (
                "BLOCKED_BY_PERMISSION",
                "BLOCKED_BY_OS_READONLY_MODE",
                "BLOCKED_UNVERIFIED_AUTONOMOUS_EXECUTION",
            )
        ),
        "skills_blocked_by_preflight_gap": sum(
            1 for m in modes if m == "DEGRADED_PREFLIGHT_BLOCKED"
        ),
        "skills_rolled_back_post_write": sum(1 for m in modes if m == "ROLLED_BACK_ILLEGAL_WRITE"),
        "permission_violations_count": len(permission_violations),
        "isolated_faults_count": len(isolated_faults),
    }
    return {
        "schema": "hyodo.modular-run/v1",
        "run_id": run_id,
        "execution_mode": execution_mode,
        "authority": "UNOBSERVED",
        "external_action_allowed": False,
        "preflight_gap_report": preflight_gap_report,
        "selective_activation": selective_result,
        "run_verdict": run_verdict,
        "personal_taste_rules": active_taste_rules,
        "profile_default_taste_rules": profile_default_taste_rules,
        "route_plan": route_plan,
        "execution_waves": execution_waves,
        "orchestration_observations_recorded": orchestration_observations_recorded,
        "disclosed_skills": disclosed_skills,
        "executed_skills": executed_skills,
        "execution_summary": execution_summary,
        "context_bytes_disclosed": context_bytes_disclosed,
        "estimated_tokens": context_bytes_disclosed // 4,
        "duration_ms": duration_ms,
        "skill_outputs": skill_outputs,
        "isolated_faults": isolated_faults,
        "permission_violations": permission_violations,
        "build_receipt": build_receipt,
        "independent_verifier_receipt": verifier_receipt,
        "six_lens_measurement": six_lenses,
    }


def _compute_run_verdict(
    *,
    routed_skills: list[str],
    skill_outputs: dict[str, Any],
    executed_skills: list[str],
    isolated_faults: list[str],
    permission_violations: list[str],
    build_receipt: dict[str, Any],
    verifier_receipt: dict[str, Any],
) -> dict[str, Any]:
    """Summarize a run as `PASS`, `FAIL` or `UNOBSERVED`. A zero-gate run is never `PASS`.

    `PASS` needs every routed skill to have actually executed and passed (at
    least one) AND an independent verifier that ran and passed. A routed skill
    that was only disclosed, or never ran, makes the run `UNOBSERVED`.
    """
    failures: list[str] = []
    if isolated_faults:
        failures.append("isolated_faults")
    if permission_violations:
        failures.append("permission_violations")
    if build_receipt.get("state") == "OBSERVED" and build_receipt.get("status") != "PASS":
        failures.append("build_failed")
    if verifier_receipt.get("status") in ("FAIL", "HOLD"):
        failures.append(f"independent_verifier_{str(verifier_receipt['status']).lower()}")
    if failures:
        return {"decision": "FAIL", "reasons": failures}
    unobserved: list[str] = []
    if not executed_skills:
        unobserved.append("no_skill_executed")
    for sid in routed_skills:
        out = skill_outputs.get(sid)
        if not isinstance(out, dict) or out.get("execution_state") != "EXECUTED_PASS":
            unobserved.append(f"routed_skill_not_executed:{sid}")
    if verifier_receipt.get("state") != "OBSERVED" or verifier_receipt.get("status") != "PASS":
        unobserved.append("independent_verifier_not_run")
    if unobserved:
        return {"decision": "UNOBSERVED", "reasons": unobserved}
    return {"decision": "PASS", "reasons": []}


def evaluate_skill_impact(
    *,
    skill_id: str,
    baseline_metrics: dict[str, Any],
    treatment_metrics: dict[str, Any],
    verifier_receipt: dict[str, Any] | None = None,
    builder_actor: str | None = None,
    builder_session_id: str | None = None,
    case_id: str = "case-01",
    skill_version: str = "0.1.0",
    six_lens_statuses: dict[str, str] | None = None,
    virtue_signals: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Compare before/after task execution metrics via `hyodo.skill_eval.evaluate_skill_case`.

    Requires an authentic, non-self-reviewed `hyodo.independent-verifier/v1` receipt
    (`verifier_receipt`); never fabricates a passing attestation when missing or invalid.
    Evaluates strictly from deliverable quality + Taste conformance + cost + duration +
    human intervention reduction + reproducibility (never skill count or `score` floats).
    """
    from hyodo.skill_eval import SKILL_EVAL_ORACLE

    run_id = f"run-{case_id}"
    execution_id = f"exec-{case_id}"
    attempt_id = f"att-{case_id}"

    clean_baseline = {k: v for k, v in baseline_metrics.items() if k != "score"}
    clean_treatment = {k: v for k, v in treatment_metrics.items() if k != "score"}
    subjective_score_ignored = ("score" in baseline_metrics) or ("score" in treatment_metrics)

    case_obj = {
        "eval_id": case_id,
        "skill_id": skill_id,
        "skill_version": skill_version,
        "scenario": f"paired before/after evaluation for {skill_id}",
        "oracle": SKILL_EVAL_ORACLE,
        "input_fixture": {"baseline": clean_baseline},
        "expected_behavior": {"owner": "host-harness"},
        "forbidden_behavior": ["authority_expansion"],
        "required_evidence": ["verifier_attestation"],
        "critical_invariants": ["execution_authority_false"],
    }

    treat_passed = bool(clean_treatment.get("passed", False))
    verifier_ok, verifier_err = _validate_independent_verifier_receipt(
        verifier_receipt,
        builder_actor=builder_actor,
        builder_session_id=builder_session_id,
    )
    if verifier_receipt is None:
        att_evidence: dict[str, Any] = {
            "observed": False,
            "state": "UNOBSERVED",
            "reason": verifier_err,
        }
    elif not verifier_ok:
        att_evidence = {
            "observed": True,
            "value": str((verifier_receipt or {}).get("status", "HOLD")),
            "freshness": "fresh",
            "producer": str((verifier_receipt or {}).get("actor_id", "unverified")),
            "integrity": "tampered",
            "run_id": run_id,
            "execution_id": execution_id,
            "attempt_id": attempt_id,
            "reason": verifier_err,
        }
    else:
        # A real check, not `assert`: it must survive `python -O`.
        if not isinstance(verifier_receipt, dict):
            raise TypeError("validated verifier_receipt must be a dict")
        v_status = str(verifier_receipt.get("status", "FAIL"))
        att_evidence = {
            "observed": True,
            "value": v_status,
            "freshness": "fresh",
            "producer": str(verifier_receipt.get("actor_id", "factory-independent-verifier")),
            "integrity": "verified",
            "run_id": run_id,
            "execution_id": execution_id,
            "attempt_id": attempt_id,
        }

    execution_obj = {
        "observed": True,
        "eval_id": case_id,
        "skill_id": skill_id,
        "skill_version": skill_version,
        "run_id": run_id,
        "execution_id": execution_id,
        "attempt_id": attempt_id,
        "owner": "host-harness",
        "inferred_owner_from_label": False,
    }
    evidence_obj = {"verifier_attestation": att_evidence}
    effect_readback_obj = {"observed": verifier_ok, "passed": treat_passed and verifier_ok}
    receipt_obj = {"success": treat_passed and verifier_ok}
    authority_obj = {"execution_authority": False, "hyo_do_granted_execution": False}

    eval_verdict = evaluate_skill_case(
        case=case_obj,
        execution=execution_obj,
        evidence=evidence_obj,
        effect_readback=effect_readback_obj,
        receipt=receipt_obj,
        authority=authority_obj,
    )

    base_passed = bool(clean_baseline.get("passed", False))
    base_taste_checks = int(clean_baseline.get("taste_checks_passed", 0))
    treat_taste_checks = int(clean_treatment.get("taste_checks_passed", 0))
    base_taste_violations = int(clean_baseline.get("taste_violations", 0))
    treat_taste_violations = int(clean_treatment.get("taste_violations", 0))

    base_gates = int(
        clean_baseline.get(
            "gates_passed",
            clean_baseline.get(
                "criteria_met",
                int(clean_baseline.get("tests_passed", 1 if base_passed else 0))
                + base_taste_checks,
            ),
        )
    )
    treat_gates = int(
        clean_treatment.get(
            "gates_passed",
            clean_treatment.get(
                "criteria_met",
                int(clean_treatment.get("tests_passed", 1 if treat_passed else 0))
                + treat_taste_checks,
            ),
        )
    )
    base_failures = (
        int(clean_baseline.get("tests_failed", 0))
        + int(clean_baseline.get("lint_errors", 0))
        + int(clean_baseline.get("type_errors", 0))
        + int(clean_baseline.get("permission_violations", 0))
        + base_taste_violations
    )
    treat_failures = (
        int(clean_treatment.get("tests_failed", 0))
        + int(clean_treatment.get("lint_errors", 0))
        + int(clean_treatment.get("type_errors", 0))
        + int(clean_treatment.get("permission_violations", 0))
        + treat_taste_violations
    )
    base_interventions = int(clean_baseline.get("human_interventions", 0))
    treat_interventions = int(clean_treatment.get("human_interventions", 0))
    base_tokens = int(clean_baseline.get("tokens", clean_baseline.get("estimated_tokens", 0)))
    treat_tokens = int(clean_treatment.get("tokens", clean_treatment.get("estimated_tokens", 0)))

    verifier_passed = bool(verifier_ok and (verifier_receipt or {}).get("status") == "PASS")
    if eval_verdict.get("status") != "PASS" or not verifier_passed:
        raw_verdict = "INCONCLUSIVE"
    elif (
        (base_passed and not treat_passed)
        or (treat_gates < base_gates)
        or (treat_failures > base_failures)
        or (treat_taste_violations > base_taste_violations)
    ):
        raw_verdict = "HURT"
    elif treat_taste_violations > 0:
        raw_verdict = "NEUTRAL"
    elif (treat_passed and not base_passed) or (
        treat_passed == base_passed
        and (
            treat_gates > base_gates
            or treat_failures < base_failures
            or treat_taste_checks > base_taste_checks
            or treat_interventions < base_interventions
        )
    ):
        raw_verdict = "HELPED"
    else:
        raw_verdict = "NEUTRAL"

    reproducible = bool(
        clean_treatment.get("output_sha256")
        and clean_treatment.get("output_sha256") == clean_treatment.get("repeat_output_sha256")
    )

    signals = virtue_signals or six_lens_statuses
    lifecycle_rec = recommend_skill_lifecycle_action(raw_verdict, virtue_signals=signals)
    result = {
        "schema": "hyodo.factory-skill-impact/v1",
        "skill_id": skill_id,
        "case_id": case_id,
        "skill_eval_receipt": eval_verdict,
        "verifier_validation": {
            "valid": verifier_ok,
            "reason": verifier_err,
            "verifier_receipt_sha256": _canonical_receipt_digest(verifier_receipt),
        },
        "case_result": {
            "case_id": case_id,
            "verdict": raw_verdict,
            "gate_status": eval_verdict.get("status"),
        },
        "verdict": raw_verdict,
        "lifecycle_recommendation": lifecycle_rec,
        "comparison": {
            "gates_passed_delta": treat_gates - base_gates,
            "failure_count_delta": treat_failures - base_failures,
            "taste_checks_passed_delta": treat_taste_checks - base_taste_checks,
            "taste_violations_delta": treat_taste_violations - base_taste_violations,
            "taste_conformance_passed": treat_taste_violations == 0,
            "token_cost_delta": treat_tokens - base_tokens,
            "duration_ms_delta": int(clean_treatment.get("duration_ms", 0))
            - int(clean_baseline.get("duration_ms", 0)),
            "human_interventions_delta": treat_interventions - base_interventions,
            "reproducible": reproducible,
            "subjective_score_ignored": subjective_score_ignored,
        },
        "authority_expanded": False,
    }
    result["eval_receipt_sha256"] = _canonical_receipt_digest(result)
    return result


def get_skill_trust_state(
    workspace_root: Path,
    skill_id: str,
    *,
    env_fingerprint: str | None = None,
) -> dict[str, Any]:
    """Return the current trust stage (`DISCOVER -> VERIFY -> MANUAL -> SHADOW -> TRUSTED -> AUTO_RUN`) for *skill_id*.

    Automatically demotes back to `VERIFY` if content hash, version, permission
    boundary, or runtime environment fingerprint has drifted since verification.
    """
    current_env = env_fingerprint or _default_env_fingerprint()
    modules = load_registry_state(workspace_root)
    found: tuple[ModuleRecord, SkillUnitSpec] | None = None
    for mod in modules.values():
        if skill_id in mod.skills:
            found = (mod, mod.skills[skill_id])
            break

    if found is None:
        return {
            "skill_id": skill_id,
            "trust_stage": "DISCOVER",
            "drifted": False,
            "demoted_from": None,
            "demotion_reason": None,
            "registered": False,
        }

    mod, unit = found
    current_tree, _tree_count, _tree_error = compute_module_tree_digest(Path(mod.source_path))
    trust_doc = _read_trust_file(workspace_root)
    skills_map: dict[str, Any] = trust_doc["skills"]
    stored = skills_map.get(skill_id)
    if not isinstance(stored, dict):
        return {
            "skill_id": skill_id,
            "trust_stage": "VERIFY",
            "drifted": False,
            "demoted_from": None,
            "demotion_reason": None,
            "registered": True,
            "content_sha256": unit.content_sha256,
            "version": mod.version,
            "boundary": unit.boundary.to_dict(),
            "module_source_path": mod.source_path,
            "module_tree_sha256": current_tree,
            "env_fingerprint": current_env,
        }

    drift_reasons: list[str] = []
    if stored.get("content_sha256") != unit.content_sha256:
        drift_reasons.append("content_sha256_changed")
    if stored.get("version") != mod.version:
        drift_reasons.append("version_changed")
    if stored.get("boundary") != unit.boundary.to_dict():
        drift_reasons.append("permission_boundary_changed")
    # Any file in the module (scripts, references, run.sh) counts, not only SKILL.md.
    if current_tree is None or stored.get("module_tree_sha256") != current_tree:
        drift_reasons.append("module_tree_changed")
    if stored.get("module_source_path") != mod.source_path:
        drift_reasons.append("module_source_path_changed")
    if stored.get("env_fingerprint") != current_env:
        drift_reasons.append("environment_fingerprint_changed")

    if drift_reasons:
        prev_stage = str(stored.get("trust_stage", "VERIFY"))
        demoted = {
            **stored,
            "skill_id": skill_id,
            "trust_stage": "VERIFY",
            "drifted": True,
            "registered": True,
            "demoted_from": prev_stage,
            "demotion_reason": f"DRIFT_DETECTED_REVERIFY_REQUIRED:{','.join(drift_reasons)}",
            "verifier_status": "UNOBSERVED",
            "eval_verdict": "UNOBSERVED",
            "approval_verified": False,
            "approval_receipt": None,
            "content_sha256": unit.content_sha256,
            "version": mod.version,
            "boundary": unit.boundary.to_dict(),
            "module_source_path": mod.source_path,
            "module_tree_sha256": current_tree,
            "env_fingerprint": current_env,
        }
        skills_map[skill_id] = demoted
        _write_trust_file(workspace_root, trust_doc)
        return demoted

    # No new drift now; an earlier demotion stays visible until re-promotion
    # rewrites the record.
    return {
        **stored,
        "drifted": False,
        "demoted_from": stored.get("demoted_from"),
        "demotion_reason": stored.get("demotion_reason"),
        "registered": True,
    }


def evaluate_and_promote_trust(
    workspace_root: Path,
    *,
    skill_id: str,
    target_stage: str | None = None,
    eval_receipt: dict[str, Any] | None = None,
    verifier_receipt: dict[str, Any] | None = None,
    approval_receipt: dict[str, Any] | None = None,
    approved_flag: bool = False,
    builder_actor: str | None = None,
    builder_session_id: str | None = None,
    s_score: float | None = None,
    run_id: str = "trust-eval-01",
    source: str = "hyodo-factory.trust-ladder",
    env_fingerprint: str | None = None,
    authority_verifier: ApprovalAuthorityVerifier | None = None,
) -> dict[str, Any]:
    """Evaluate mandatory evidence gates and advance/demote trust along `DISCOVER -> VERIFY -> MANUAL -> SHADOW -> TRUSTED -> AUTO_RUN`.

    Hard invariants:
    - Single-step progression only: `target_stage` cannot skip intermediate stages.
    - Evidence anti-replay: each step requires a fresh `run_id`, fresh `eval_receipt`,
      and fresh `verifier_receipt`; reusing prior evidence is blocked.
    - Genuine `hyodo.independent-verifier/v1` receipt required (never accepts bare mocks).
    - A high `s_score` NEVER overrides failed or `UNOBSERVED` mandatory gates.
    - `AUTO_RUN` rejects a bare `approved_flag=True` boolean without a verified
      `approval_receipt` bound to `workspace_id`, `policy_digest`, `risk_level`, `approved_scope`,
      `content_sha256`, `run_id`, the module tree digest, the module source path and the
      command, and confirmed by the host's *authority_verifier*.
      A request built by `issue_host_approval_request` alone never reaches `AUTO_RUN`.
    """
    current_state = get_skill_trust_state(workspace_root, skill_id, env_fingerprint=env_fingerprint)
    if not current_state.get("registered", False):
        raise KeyError(f"cannot promote unregistered skill: {skill_id}")

    modules = load_registry_state(workspace_root)
    mod, unit = next((m, m.skills[skill_id]) for m in modules.values() if skill_id in m.skills)
    current_env = env_fingerprint or _default_env_fingerprint()
    current_stage = str(current_state.get("trust_stage", "VERIFY"))

    trust_doc = _read_trust_file(workspace_root)
    prior_rec = trust_doc["skills"].get(skill_id, {})
    consumed_run_ids = list(prior_rec.get("consumed_run_ids", []))
    consumed_eval_digests = list(prior_rec.get("consumed_eval_digests", []))
    consumed_verifier_digests = list(prior_rec.get("consumed_verifier_digests", []))

    eval_digest = _canonical_receipt_digest(eval_receipt)
    verifier_digest = _canonical_receipt_digest(verifier_receipt)

    verifier_ok, verifier_err = _validate_independent_verifier_receipt(
        verifier_receipt,
        builder_actor=builder_actor,
        builder_session_id=builder_session_id,
    )
    v_status = (
        str((verifier_receipt or {}).get("status", "UNOBSERVED")) if verifier_ok else "UNOBSERVED"
    )
    if isinstance(verifier_receipt, dict) and verifier_receipt.get("status") in ("FAIL", "HOLD"):
        v_status = str(verifier_receipt["status"])

    e_verdict = str((eval_receipt or {}).get("verdict", "UNOBSERVED"))
    eval_gate_status = str(
        (eval_receipt or {}).get("skill_eval_receipt", {}).get("status", "UNOBSERVED")
    )
    comp = (eval_receipt or {}).get("comparison", {})
    reproducible = bool(comp.get("reproducible", False))
    failure_delta = int(comp.get("failure_count_delta", 0))
    interventions_delta = int(comp.get("human_interventions_delta", 0))
    taste_conformance_ok = bool(comp.get("taste_conformance_passed", True))

    replay_blocked = bool(
        run_id in consumed_run_ids
        or (eval_digest is not None and eval_digest in consumed_eval_digests)
        or (verifier_digest is not None and verifier_digest in consumed_verifier_digests)
    )

    stage_order = list(TRUST_STAGES)
    cur_idx = stage_order.index(current_stage) if current_stage in stage_order else 1
    if cur_idx < 1:
        cur_idx = 1

    stage_skip_blocked = False
    if target_stage is not None:
        if target_stage not in stage_order:
            raise ValueError(f"invalid target_stage: {target_stage}")
        desired_idx = stage_order.index(target_stage)
        if desired_idx > cur_idx + 1:
            stage_skip_blocked = True
    else:
        desired_idx = min(cur_idx + 1, len(stage_order) - 1)
        if desired_idx < stage_order.index("MANUAL"):
            desired_idx = stage_order.index("MANUAL")

    mandatory_gates_passed = (
        verifier_ok
        and v_status == "PASS"
        and e_verdict == "HELPED"
        and eval_gate_status == "PASS"
        and reproducible
        and failure_delta <= 0
        and taste_conformance_ok
    )
    score_override_blocked = bool(
        s_score is not None and s_score >= 9.0 and not mandatory_gates_passed
    )

    approval_verified, approval_reasons = verify_host_approval_receipt(
        workspace_root,
        approval_receipt,
        skill_id=skill_id,
        unit=unit,
        module=mod,
        content_sha256=unit.content_sha256,
        run_id=run_id,
        authority_verifier=authority_verifier,
    )
    bare_boolean_rejected = bool(approved_flag and not approval_verified)

    promotion_blocked_reason: str | None = None
    if replay_blocked:
        new_stage = current_stage
        decision = "BLOCK"
        admitted = False
        promotion_blocked_reason = "DUPLICATE_EVIDENCE_REPLAY"
    elif stage_skip_blocked:
        new_stage = current_stage
        decision = "BLOCK"
        admitted = False
        promotion_blocked_reason = f"STAGE_SKIP_FORBIDDEN:{current_stage}->{target_stage}"
    elif (
        v_status in ("FAIL", "HOLD", "UNOBSERVED")
        or e_verdict == "HURT"
        or failure_delta > 0
        or not taste_conformance_ok
    ):
        new_stage = "VERIFY"
        decision = "BLOCK"
        admitted = False
        promotion_blocked_reason = verifier_err or "MANDATORY_GATE_FAILED_OR_UNOBSERVED"
    elif not mandatory_gates_passed:
        new_stage = "MANUAL" if cur_idx < stage_order.index("MANUAL") else current_stage
        decision = "ASK_COMMANDER"
        admitted = False
        promotion_blocked_reason = "IMPACT_NOT_HELPED_OR_NOT_REPRODUCIBLE"
    else:
        candidate_stage = stage_order[desired_idx]
        if candidate_stage == "AUTO_RUN":
            if approval_verified and interventions_delta <= 0:
                new_stage = "AUTO_RUN"
                decision = "AUTO_RUN"
                admitted = True
            else:
                new_stage = "TRUSTED"
                decision = "ASK_COMMANDER"
                admitted = False
                promotion_blocked_reason = (
                    ",".join(approval_reasons) if approval_reasons else "APPROVAL_RECEIPT_INVALID"
                )
        else:
            new_stage = candidate_stage
            decision = "ASK_COMMANDER"
            admitted = False

    if (
        not replay_blocked
        and not stage_skip_blocked
        and verifier_ok
        and eval_digest
        and verifier_digest
    ):
        consumed_run_ids.append(run_id)
        consumed_eval_digests.append(eval_digest)
        consumed_verifier_digests.append(verifier_digest)

    approved_scope = (
        approval_receipt.get("approved_scope")
        if approval_verified and isinstance(approval_receipt, dict)
        else unit.boundary.to_dict()
    )
    current_tree, _tree_count, _tree_error = compute_module_tree_digest(Path(mod.source_path))

    record = {
        "skill_id": skill_id,
        "module_id": mod.module_id,
        "trust_stage": new_stage,
        "previous_stage": current_stage,
        "verifier_status": v_status,
        "eval_verdict": e_verdict,
        "reproducible": reproducible,
        "approval_verified": approval_verified,
        "bare_boolean_rejected": bare_boolean_rejected,
        "replay_blocked": replay_blocked,
        "stage_skip_blocked": stage_skip_blocked,
        "score_override_blocked": score_override_blocked,
        "promotion_blocked_reason": promotion_blocked_reason,
        "evidence_steps_count": len(consumed_run_ids),
        "consumed_run_ids": consumed_run_ids,
        "consumed_eval_digests": consumed_eval_digests,
        "consumed_verifier_digests": consumed_verifier_digests,
        "workspace_id": workspace_identity(workspace_root),
        "policy_digest": current_policy_digest(workspace_root),
        "approved_scope": approved_scope,
        "approval_receipt": approval_receipt if approval_verified else None,
        "content_sha256": unit.content_sha256,
        "version": mod.version,
        "boundary": unit.boundary.to_dict(),
        "module_source_path": mod.source_path,
        "module_tree_sha256": current_tree,
        "env_fingerprint": current_env,
    }
    trust_doc["skills"][skill_id] = record
    _write_trust_file(workspace_root, trust_doc)

    safe_sid = skill_id.replace("/", "-").replace("_", "-")
    obs_raw = {
        "schema": ADMISSION_OBSERVATION_SCHEMA_VERSION,
        "observation_id": f"adm-obs-{run_id}-{safe_sid}-{new_stage.lower()}",
        "decision_id": f"adm-dec-{run_id}-{safe_sid}-{new_stage.lower()}",
        "run_id": run_id,
        "decision": decision,
        "s_score": s_score,
        "observed": v_status != "UNOBSERVED",
        "admitted": admitted,
        "execution_attempted": False,
        "execution_observed": False,
        "source": source,
        "ts": utc_now_iso(),
        "observation_identity": {
            "skill_id": skill_id,
            "trust_stage": new_stage,
            "content_sha256": unit.content_sha256,
            "version": mod.version,
            "score_override_blocked": score_override_blocked,
            "replay_blocked": replay_blocked,
            "stage_skip_blocked": stage_skip_blocked,
            "approval_verified": approval_verified,
        },
    }

    admission_obs = append_admission_observation(workspace_root, obs_raw)
    return {
        **record,
        "admission_decision": decision,
        "admitted": admitted,
        "admission_observation": admission_obs,
    }
