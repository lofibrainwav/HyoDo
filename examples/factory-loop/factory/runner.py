"""Phase 2.3/2.4 — Fault-Isolated Universal Factory Runner & Real Subprocess Executor.

Executes tasks with pluggable skills while enforcing:
1. Core Independence: works even when 0 external skills are installed.
2. Strict separation between metadata registration (`REGISTERED`), instruction
   disclosure (`DISCLOSED_ONLY` -> `gate_verdict: UNOBSERVED`), and real
   subprocess execution (`EXECUTED_PASS` / `EXECUTED_FAIL`).
3. Runtime `PermissionBoundary` enforcement (`subprocess_exec`, `filesystem_write`,
   `network_access`, `execution_authority=False`) with automatic workspace rollback
   if a read-only skill attempts to write or mutate files.
4. Process-level fault isolation (`start_new_session=True`, timeout, clean git env).
5. Substantive Producer != Independent Verifier separation (`SELF_REVIEW_FORBIDDEN`).
6. Real before/after skill impact evaluation via `hyodo.skill_eval.evaluate_skill_case`.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from adapters.agent_skills import disclose_skill_body

from factory.contracts import (
    TRUST_STAGES,
    TRUST_STATE_SCHEMA,
    ModuleRecord,
    SkillUnitSpec,
    recommend_skill_lifecycle_action,
)
from factory.lifecycle import acquire_run_lock, release_run_lock
from factory.registry import load_registry_state
from factory.router import TRUST_STATE_REL_PATH, route_skills_for_task
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
from hyodo.independent_verifier import verify_exact_candidate
from hyodo.nameplate import build_nameplate
from hyodo.orchestration_observation import (
    ORCHESTRATION_OBSERVATION_SCHEMA_VERSION,
    append_orchestration_observation,
)
from hyodo.provenance import clean_git_env
from hyodo.six_lens_runtime import measure_workspace_six_lenses
from hyodo.skill_eval import evaluate_skill_case

_PROTECTED_TOP_DIRS = (".git", ".hyodo", "__pycache__", ".pytest_cache")


def _snapshot_workspace_files(workspace_root: Path) -> dict[str, bytes]:
    """Snapshot all regular files in *workspace_root* outside `.git` and `.hyodo`."""
    snap: dict[str, bytes] = {}
    for path in sorted(workspace_root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        rel = path.relative_to(workspace_root)
        if rel.parts and rel.parts[0] in _PROTECTED_TOP_DIRS:
            continue
        try:
            snap[str(rel)] = path.read_bytes()
        except OSError:
            continue
    return snap


@contextlib.contextmanager
def _readonly_workspace_guard(workspace_root: Path) -> Iterator[None]:
    """Pre-write OS permission enforcement: strip POSIX write bits (`mode & ~0o222`) on workspace files and dirs.

    Prevents standard file creation, modification, or deletion at the OS syscall level (`EACCES` / `PermissionError`)
    while keeping `.hyodo` and `.git` traversable. Original file modes are restored in `finally`.
    """
    saved_modes: list[tuple[Path, int]] = []
    targets: list[Path] = []
    for path in sorted(workspace_root.rglob("*")):
        if path.is_symlink():
            continue
        rel = path.relative_to(workspace_root)
        if rel.parts and rel.parts[0] in _PROTECTED_TOP_DIRS:
            continue
        targets.append(path)
    # Apply to files first, then directories bottom-up, and finally workspace_root
    files = [p for p in targets if p.is_file()]
    dirs = sorted([p for p in targets if p.is_dir()], key=lambda p: len(p.parts), reverse=True)
    ordered = [*files, *dirs, workspace_root]
    try:
        for p in ordered:
            try:
                mode = p.stat().st_mode & 0o777
                saved_modes.append((p, mode))
                p.chmod(mode & ~0o222)
            except OSError:
                continue
        yield
    finally:
        for p, mode in reversed(saved_modes):
            with contextlib.suppress(OSError):
                p.chmod(mode)


def _restore_and_detect_writes(
    workspace_root: Path,
    before: dict[str, bytes],
) -> list[str]:
    """Post-write defense-in-depth: detect any created/modified/deleted files and restore *before* state."""
    after = _snapshot_workspace_files(workspace_root)
    mutated: list[str] = []

    for rel, content in after.items():
        if rel not in before:
            mutated.append(f"created:{rel}")
            with contextlib.suppress(OSError):
                target = workspace_root / rel
                target.chmod(0o644)
                target.unlink()
        elif before[rel] != content:
            mutated.append(f"modified:{rel}")
            with contextlib.suppress(OSError):
                target = workspace_root / rel
                target.chmod(0o644)
                target.write_bytes(before[rel])

    for rel, content in before.items():
        if rel not in after:
            mutated.append(f"deleted:{rel}")
            target = workspace_root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            with contextlib.suppress(OSError):
                target.write_bytes(content)

    return sorted(mutated)


_HYODO_REPO_ROOT = str(Path(__file__).resolve().parents[3])


def _with_pythonpath(env: dict[str, str], workspace_root: Path | None = None) -> dict[str, str]:
    parts = [str(workspace_root)] if workspace_root is not None else []
    parts.append(_HYODO_REPO_ROOT)
    existing = env.get("PYTHONPATH", "")
    if existing:
        parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def _build_isolated_env(unit: SkillUnitSpec, workspace_root: Path | None = None) -> dict[str, str]:
    """Build a scrubbed subprocess environment respecting `unit.boundary`."""
    env = _with_pythonpath(clean_git_env(), workspace_root)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if not unit.boundary.network_access:
        for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy"):
            env.pop(k, None)
        env["HYODO_FACTORY_NETWORK_DISABLED"] = "1"
    env["HYODO_FACTORY_SKILL_ID"] = unit.skill_id
    env["HYODO_FACTORY_ROLE"] = unit.role_hint
    env["HYODO_FACTORY_EXECUTION_AUTHORITY"] = "false"
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
            # Break cycles deterministically by taking the first remaining skill
            ready = [remaining[0]]

        # Separate non-verifier skills from verifier/gatekeep skills if both are ready
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
) -> dict[str, Any]:
    """Run the modular factory loop with real subprocess isolation, permission enforcement, and Progressive Disclosure."""
    acquire_run_lock(workspace_root, run_id)
    t0 = time.monotonic()
    try:
        route_plan = route_skills_for_task(
            workspace_root,
            prompt,
            profile_name=profile_name,
            deduplicate_by_slot=deduplicate_by_slot,
        )
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

        if mid_run_callback is not None:
            mid_run_callback(workspace_root)

        execution_waves = _build_execution_waves(route_plan["selected_skills"], unit_lookup)
        parallel_waves_executed = 0

        for wave in execution_waves:
            # Disclose bodies for all skills in the current wave
            wave_bodies: dict[str, str] = {}
            for skill_id in wave:
                mod, unit = unit_lookup[skill_id]
                body = ""
                if mod.adapter in ("agent-skills", "claude-plugin"):
                    body = disclose_skill_body(mod, skill_id)
                    disclosed_skills.append(skill_id)
                    context_bytes_disclosed += len(body.encode("utf-8"))
                wave_bodies[skill_id] = body

            # Check if this wave has multiple independent read-only subprocess skills that can run in parallel
            can_parallelize = len(wave) > 1 and all(
                (skill_commands or {}).get(sid) is not None
                and unit_lookup[sid][1].boundary.subprocess_exec
                and not unit_lookup[sid][1].boundary.filesystem_write
                for sid in wave
            )

            if can_parallelize:
                parallel_waves_executed += 1
                snap_before = _snapshot_workspace_files(workspace_root)

                def _run_ro_cmd(
                    sid: str,
                ) -> tuple[str, subprocess.CompletedProcess[str] | Exception]:
                    _, u = unit_lookup[sid]
                    cmd_args = (skill_commands or {})[sid]
                    try:
                        proc = subprocess.run(
                            cmd_args,
                            cwd=str(workspace_root),
                            env=_build_isolated_env(u, workspace_root),
                            capture_output=True,
                            text=True,
                            timeout=timeout_s,
                            check=False,
                            start_new_session=True,
                        )
                        return sid, proc
                    except Exception as exc:
                        return sid, exc

                with (
                    _readonly_workspace_guard(workspace_root),
                    ThreadPoolExecutor(max_workers=min(4, len(wave))) as pool,
                ):
                    results = dict(pool.map(_run_ro_cmd, wave))

                illegal_writes = _restore_and_detect_writes(workspace_root, snap_before)
                for skill_id in wave:
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
                        elif proc.returncode != 0 and (
                            "PermissionError" in stderr_text or "Permission denied" in stderr_text
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
                                "stdout": proc.stdout.strip()[:400],
                                "role_hint": unit.role_hint,
                                "content_sha256": unit.content_sha256,
                            }
                continue

            for skill_id in wave:
                mod, unit = unit_lookup[skill_id]
                body = wave_bodies[skill_id]
                try:
                    cmd = (skill_commands or {}).get(skill_id)
                    hook_fn = (skill_hooks or {}).get(skill_id)

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
                            proc = subprocess.run(
                                cmd,
                                cwd=str(workspace_root),
                                env=_build_isolated_env(unit, workspace_root),
                                capture_output=True,
                                text=True,
                                timeout=timeout_s,
                                check=False,
                                start_new_session=True,
                            )
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
                                "stdout": proc.stdout.strip()[:400],
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
                        # Honest distinction: instruction disclosure is NOT execution!
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

        build_receipt: dict[str, Any] = {"state": "UNOBSERVED"}
        if build_cmd is not None:
            b_env = _with_pythonpath(clean_git_env(), workspace_root)
            b_env["HYODO_ACTOR_ID"] = builder_actor
            b_env["HYODO_SESSION_ID"] = builder_session_id
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
                "stdout": b_proc.stdout.strip()[:400],
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
                # Strip proxy/network in independent verifier subprocess
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
                verifier_nameplate = build_nameplate(
                    actor_id=verifier_actor,
                    role="verifier",
                    repo=workspace_root.name,
                    exact_artifact_sha=target_sha,
                    observed_at="2026-11-13T00:00:10Z",
                    runtime={"session_id": verifier_session_id, "host": "hyodo-factory-verifier"},
                )
                attestation = verify_exact_candidate(
                    root=workspace_root,
                    expected_artifact_sha=target_sha,
                    verifier_nameplate=verifier_nameplate,
                    evidence={
                        "verify_exit_code": v_proc.returncode,
                        "verify_stdout_sha256": hashlib.sha256(
                            v_proc.stdout.encode("utf-8")
                        ).hexdigest()[:12],
                    },
                    observed_at="2026-11-13T00:00:10Z",
                )
                verifier_receipt = {
                    "state": "OBSERVED",
                    "status": "PASS"
                    if (v_proc.returncode == 0 and attestation["verdict"] == "PASS")
                    else "FAIL",
                    "exit_code": v_proc.returncode,
                    "actor_id": verifier_actor,
                    "session_id": verifier_session_id,
                    "attestation": attestation,
                }

        duration_ms = int((time.monotonic() - t0) * 1000)

        # Record `hyodo.agent-event/v1` and `hyodo.orchestration-observation/v1` sidecar DAG rows
        orchestration_observations_recorded = 0
        skill_event_ids: dict[str, str] = {}
        wave_event_ids: list[list[str]] = []
        step_idx = 0
        for wave_idx, wave in enumerate(execution_waves):
            is_parallel_wave = len(wave) > 1 and all(
                (skill_commands or {}).get(sid) is not None
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
                    "ts": "2026-11-13T00:00:05Z",
                    "kind": "tool_call",
                    "actor": "agent",
                    "tool": {
                        "name": skill_id,
                        "args_digest": content_digest(prompt),
                        "paths": [],
                    },
                    "policy": unevaluated_policy(),
                }
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
                elif exec_state in ("BLOCKED_BY_PERMISSION", "BLOCKED_BY_OS_READONLY_MODE"):
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
                    "ts": "2026-11-13T00:00:05Z",
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
                    "evidence_refs": [f"sha256:{unit.content_sha256[:12]}"],
                }
                if append_orchestration_observation(workspace_root, obs_payload):
                    orchestration_observations_recorded += 1
            wave_event_ids.append(current_wave_events)

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
                1 for m in modes if m in ("BLOCKED_BY_PERMISSION", "BLOCKED_BY_OS_READONLY_MODE")
            ),
            "skills_rolled_back_post_write": sum(
                1 for m in modes if m == "ROLLED_BACK_ILLEGAL_WRITE"
            ),
            "permission_violations_count": len(permission_violations),
            "isolated_faults_count": len(isolated_faults),
        }
        return {
            "schema": "hyodo.modular-run/v1",
            "run_id": run_id,
            "authority": "UNOBSERVED",
            "external_action_allowed": False,
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
    finally:
        release_run_lock(workspace_root)


def evaluate_skill_impact(
    *,
    skill_id: str,
    baseline_metrics: dict[str, Any],
    treatment_metrics: dict[str, Any],
    case_id: str = "case-01",
    skill_version: str = "0.1.0",
    six_lens_statuses: dict[str, str] | None = None,
    virtue_signals: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Compare before/after task execution metrics via `hyodo.skill_eval.evaluate_skill_case`.

    Evaluates strictly from objective gate/verification observations (subjective `score` floats are ignored):
    - Quality (`passed`, `gates_passed` / `criteria_met`, `tests_failed`, `lint_errors`, `type_errors`, `permission_violations`)
    - Cost (`tokens` / `estimated_tokens`)
    - Time (`duration_ms`)
    - Human intervention count (`human_interventions`)
    - Reproducibility (`output_sha256` == `repeat_output_sha256`)
    """
    from hyodo.skill_eval import SKILL_EVAL_ORACLE

    run_id = f"run-{case_id}"
    execution_id = f"exec-{case_id}"
    attempt_id = f"att-{case_id}"

    # Strip any subjective `score` key before feeding fixture or computing verdicts
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
    evidence_obj = {
        "verifier_attestation": {
            "observed": True,
            "value": "PASS" if treat_passed else "FAIL",
            "freshness": "fresh",
            "producer": "factory-independent-verifier",
            "integrity": "verified",
            "run_id": run_id,
            "execution_id": execution_id,
            "attempt_id": attempt_id,
        }
    }
    effect_readback_obj = {"observed": True, "passed": treat_passed}
    receipt_obj = {"success": treat_passed}
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
    base_gates = int(
        clean_baseline.get(
            "gates_passed", clean_baseline.get("criteria_met", 1 if base_passed else 0)
        )
    )
    treat_gates = int(
        clean_treatment.get(
            "gates_passed", clean_treatment.get("criteria_met", 1 if treat_passed else 0)
        )
    )
    base_failures = (
        int(clean_baseline.get("tests_failed", 0))
        + int(clean_baseline.get("lint_errors", 0))
        + int(clean_baseline.get("type_errors", 0))
        + int(clean_baseline.get("permission_violations", 0))
    )
    treat_failures = (
        int(clean_treatment.get("tests_failed", 0))
        + int(clean_treatment.get("lint_errors", 0))
        + int(clean_treatment.get("type_errors", 0))
        + int(clean_treatment.get("permission_violations", 0))
    )
    base_interventions = int(clean_baseline.get("human_interventions", 0))
    treat_interventions = int(clean_treatment.get("human_interventions", 0))
    base_tokens = int(clean_baseline.get("tokens", clean_baseline.get("estimated_tokens", 0)))
    treat_tokens = int(clean_treatment.get("tokens", clean_treatment.get("estimated_tokens", 0)))

    if eval_verdict.get("status") != "PASS":
        raw_verdict = "INCONCLUSIVE"
    elif (treat_passed and not base_passed) or (
        treat_passed == base_passed
        and (
            treat_gates > base_gates
            or treat_failures < base_failures
            or treat_interventions < base_interventions
        )
    ):
        raw_verdict = "HELPED"
    elif (
        (base_passed and not treat_passed)
        or (treat_gates < base_gates)
        or (treat_failures > base_failures)
    ):
        raw_verdict = "HURT"
    else:
        raw_verdict = "NEUTRAL"

    reproducible = bool(
        clean_treatment.get("output_sha256")
        and clean_treatment.get("output_sha256") == clean_treatment.get("repeat_output_sha256")
    )

    signals = virtue_signals or six_lens_statuses
    lifecycle_rec = recommend_skill_lifecycle_action(raw_verdict, virtue_signals=signals)
    return {
        "schema": "hyodo.factory-skill-impact/v1",
        "skill_id": skill_id,
        "skill_eval_receipt": eval_verdict,
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
            "token_cost_delta": treat_tokens - base_tokens,
            "duration_ms_delta": int(clean_treatment.get("duration_ms", 0))
            - int(clean_baseline.get("duration_ms", 0)),
            "human_interventions_delta": treat_interventions - base_interventions,
            "reproducible": reproducible,
            "subjective_score_ignored": subjective_score_ignored,
        },
        "authority_expanded": False,
    }


def _default_env_fingerprint() -> str:
    return f"py{sys.version_info.major}.{sys.version_info.minor}-{sys.platform}"


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


def _write_trust_file(workspace_root: Path, data: dict[str, Any]) -> None:
    path = workspace_root / TRUST_STATE_REL_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def get_skill_trust_state(
    workspace_root: Path,
    skill_id: str,
    *,
    env_fingerprint: str | None = None,
) -> dict[str, Any]:
    """Return the current trust stage (`DISCOVER -> VERIFY -> MANUAL -> SHADOW -> TRUSTED -> AUTO_RUN`) for *skill_id*.

    Automatically demotes back to `VERIFY` if the skill's content hash, version,
    permission boundary, or runtime environment fingerprint has drifted since the
    last verification.
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
            "env_fingerprint": current_env,
        }

    drift_reasons: list[str] = []
    if stored.get("content_sha256") != unit.content_sha256:
        drift_reasons.append("content_sha256_changed")
    if stored.get("version") != mod.version:
        drift_reasons.append("version_changed")
    if stored.get("boundary") != unit.boundary.to_dict():
        drift_reasons.append("permission_boundary_changed")
    if stored.get("env_fingerprint") != current_env:
        drift_reasons.append("environment_fingerprint_changed")

    if drift_reasons:
        prev_stage = str(stored.get("trust_stage", "VERIFY"))
        demoted = {
            **stored,
            "skill_id": skill_id,
            "trust_stage": "VERIFY",
            "drifted": True,
            "demoted_from": prev_stage,
            "demotion_reason": f"DRIFT_DETECTED_REVERIFY_REQUIRED:{','.join(drift_reasons)}",
            "verifier_status": "UNOBSERVED",
            "eval_verdict": "UNOBSERVED",
            "content_sha256": unit.content_sha256,
            "version": mod.version,
            "boundary": unit.boundary.to_dict(),
            "env_fingerprint": current_env,
        }
        skills_map[skill_id] = demoted
        _write_trust_file(workspace_root, trust_doc)
        return demoted

    return {
        **stored,
        "drifted": False,
        "demoted_from": None,
        "demotion_reason": None,
        "registered": True,
    }


def evaluate_and_promote_trust(
    workspace_root: Path,
    *,
    skill_id: str,
    target_stage: str | None = None,
    eval_receipt: dict[str, Any] | None = None,
    verifier_receipt: dict[str, Any] | None = None,
    serenity_gate_approved: bool = False,
    s_score: float | None = None,
    run_id: str = "trust-eval-01",
    source: str = "kingdom.agent-loop.eros-gate",
    env_fingerprint: str | None = None,
) -> dict[str, Any]:
    """Evaluate mandatory evidence gates and advance/demote trust along `DISCOVER -> VERIFY -> MANUAL -> SHADOW -> TRUSTED -> AUTO_RUN`.

    Hard invariants:
    - A high `s_score` NEVER overrides a failed or `UNOBSERVED` verifier or skill-eval gate.
    - `AUTO_RUN` requires `verifier_status == "PASS"`, `eval_verdict == "HELPED"`,
      `reproducible == True`, `0` permission violations, `0` human interventions,
      AND `serenity_gate_approved == True`.
    - Records a validated `hyodo.admission-observation/v1` entry in `.hyodo/admission-observations.jsonl`.
    """
    current_state = get_skill_trust_state(workspace_root, skill_id, env_fingerprint=env_fingerprint)
    if not current_state.get("registered", False):
        raise KeyError(f"cannot promote unregistered skill: {skill_id}")

    modules = load_registry_state(workspace_root)
    mod, unit = next((m, m.skills[skill_id]) for m in modules.values() if skill_id in m.skills)
    current_env = env_fingerprint or _default_env_fingerprint()
    current_stage = str(current_state.get("trust_stage", "VERIFY"))

    v_status = str((verifier_receipt or {}).get("status", "UNOBSERVED"))
    e_verdict = str((eval_receipt or {}).get("verdict", "UNOBSERVED"))
    comp = (eval_receipt or {}).get("comparison", {})
    reproducible = bool(comp.get("reproducible", False))
    failure_delta = int(comp.get("failure_count_delta", 0))
    interventions_delta = int(comp.get("human_interventions_delta", 0))

    mandatory_gates_passed = (
        v_status == "PASS" and e_verdict == "HELPED" and reproducible and failure_delta <= 0
    )
    score_override_blocked = bool(
        s_score is not None and s_score >= 9.0 and not mandatory_gates_passed
    )

    if v_status in ("FAIL", "HOLD", "UNOBSERVED") or e_verdict == "HURT" or failure_delta > 0:
        new_stage = "VERIFY"
        decision = "BLOCK"
        admitted = False
    elif not mandatory_gates_passed:
        # Verifier passed, but impact is NEUTRAL/INCONCLUSIVE or not yet reproducible -> MANUAL only
        new_stage = "MANUAL"
        decision = "ASK_COMMANDER"
        admitted = False
    else:
        # All mandatory verification & impact gates passed (`VERIFIED` + `HELPED` + `reproducible`)
        stage_order = list(TRUST_STAGES)
        cur_idx = stage_order.index(current_stage) if current_stage in stage_order else 1
        if target_stage is not None:
            if target_stage not in stage_order:
                raise ValueError(f"invalid target_stage: {target_stage}")
            desired_idx = stage_order.index(target_stage)
        else:
            desired_idx = min(cur_idx + 1, len(stage_order) - 1)
            # If starting at VERIFY and all gates pass, advance at least to MANUAL
            if desired_idx < stage_order.index("MANUAL"):
                desired_idx = stage_order.index("MANUAL")

        candidate_stage = stage_order[desired_idx]
        if candidate_stage == "AUTO_RUN":
            if serenity_gate_approved and interventions_delta <= 0:
                new_stage = "AUTO_RUN"
                decision = "AUTO_RUN"
                admitted = True
            else:
                new_stage = "TRUSTED"
                decision = "ASK_COMMANDER"
                admitted = False
        else:
            new_stage = candidate_stage
            decision = "ASK_COMMANDER"
            admitted = False

    trust_doc = _read_trust_file(workspace_root)
    record = {
        "skill_id": skill_id,
        "module_id": mod.module_id,
        "trust_stage": new_stage,
        "previous_stage": current_stage,
        "verifier_status": v_status,
        "eval_verdict": e_verdict,
        "reproducible": reproducible,
        "serenity_gate_approved": serenity_gate_approved,
        "score_override_blocked": score_override_blocked,
        "content_sha256": unit.content_sha256,
        "version": mod.version,
        "boundary": unit.boundary.to_dict(),
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
        "ts": "2026-11-13T00:00:15Z",
        "observation_identity": {
            "skill_id": skill_id,
            "trust_stage": new_stage,
            "content_sha256": unit.content_sha256,
            "version": mod.version,
            "score_override_blocked": score_override_blocked,
        },
    }
    admission_obs = append_admission_observation(workspace_root, obs_raw)
    return {
        **record,
        "admission_decision": decision,
        "admitted": admitted,
        "admission_observation": admission_obs,
    }
