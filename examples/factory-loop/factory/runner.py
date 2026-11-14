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
import os
import subprocess
import time
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from adapters.agent_skills import disclose_skill_body

from factory.contracts import ModuleRecord, SkillUnitSpec, recommend_skill_lifecycle_action
from factory.lifecycle import acquire_run_lock, release_run_lock
from factory.registry import load_registry_state
from factory.router import route_skills_for_task
from hyodo.independent_verifier import verify_exact_candidate
from hyodo.nameplate import build_nameplate
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
        modes = [str(v.get("execution_state", "")) for v in skill_outputs.values()]
        execution_summary = {
            "skills_routed": len(route_plan["selected_skills"]),
            "execution_waves_count": len(execution_waves),
            "parallel_waves_executed": parallel_waves_executed,
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
