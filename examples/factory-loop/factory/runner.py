"""Phase 2.3/2.4 — Fault-Isolated Universal Factory Runner & Trust-Enforced Executor.

Executes tasks with pluggable skills while enforcing:
1. Core Independence: works even when 0 external skills are installed.
2. Preflight `analyze_capability_gaps` before routing/execution, skipping
   `DEGRADED` skills and applying host-configured Personal Taste rules.
3. Strict separation between metadata registration (`REGISTERED`), instruction
   disclosure (`DISCLOSED_ONLY` -> `gate_verdict: UNOBSERVED`), and real
   subprocess execution (`EXECUTED_PASS` / `EXECUTED_FAIL`).
4. Full-stream `stdout` hashing and timing-normalized SHA-256 before preview truncation.
5. Runtime `PermissionBoundary` enforcement (`subprocess_exec`, `filesystem_write`,
   `network_access`, `execution_authority=False`) plus `AUTO_RUN` execution permission
   gating before any autonomous execution.
6. Substantive Producer != Independent Verifier separation (`SELF_REVIEW_FORBIDDEN`)
   with genuine `hyodo.independent-verifier/v1` receipt validation in `evaluate_skill_impact`.
7. Single-step trust progression, evidence anti-replay, and EROS/Serenity verified
   approval receipt binding (`workspace_id`, `policy_digest`, `risk_level`, `approved_scope`).
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from adapters.agent_skills import disclose_skill_body

from factory.contracts import (
    SERENITY_RECEIPT_SCHEMA,
    TRUST_STAGES,
    TRUST_STATE_SCHEMA,
    ModuleRecord,
    PermissionBoundary,
    SkillUnitSpec,
    recommend_skill_lifecycle_action,
)
from factory.lifecycle import acquire_run_lock, release_run_lock
from factory.registry import load_registry_state
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

# Host-owned check that a Serenity approval receipt was issued by a real approval
# authority (for example a passkey-signed approval in KINGDOM). The factory can
# build an approval *request*, but it can never vouch for who approved it.
ApprovalAuthorityVerifier = Callable[[dict[str, Any]], tuple[bool, str | None]]

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
    """Pre-write OS permission enforcement: strip POSIX write bits (`mode & ~0o222`) on workspace files and dirs."""
    saved_modes: list[tuple[Path, int]] = []
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
        for k in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy"):
            env.pop(k, None)
        env["HYODO_FACTORY_NETWORK_DISABLED"] = "1"
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


def issue_serenity_approval_receipt(
    workspace_root: Path,
    *,
    skill_id: str,
    run_id: str,
    approved_by: str,
    risk_level: str = "low",
    mandatory_gates_passed: bool = True,
    permission_violations: int = 0,
    reproducible: bool = True,
    require_policy_trust: bool = False,
) -> dict[str, Any]:
    """Build an unsigned Serenity approval *request* bound to workspace, policy digest, skill hash, and run_id.

    The returned dict is not an approval. Every field is asserted by the caller,
    and nothing here proves who approved it. `verify_serenity_approval_receipt`
    accepts it only when the host's `authority_verifier` confirms that a real
    approval authority issued it.
    """
    modules = load_registry_state(workspace_root)
    unit = next((m.skills[skill_id] for m in modules.values() if skill_id in m.skills), None)
    if unit is None:
        raise KeyError(f"cannot issue Serenity receipt for unregistered skill: {skill_id}")
    return {
        "schema": SERENITY_RECEIPT_SCHEMA,
        "approved": True,
        "run_id": run_id,
        "skill_id": skill_id,
        "content_sha256": unit.content_sha256,
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


def verify_serenity_approval_receipt(
    workspace_root: Path,
    serenity_receipt: dict[str, Any] | None,
    *,
    skill_id: str,
    unit: SkillUnitSpec,
    content_sha256: str,
    run_id: str,
    authority_verifier: ApprovalAuthorityVerifier | None = None,
) -> tuple[bool, list[str]]:
    """Fail-closed verification of an EROS/Serenity approval receipt (never trusts a bare boolean).

    Structural binding is checked here; the issuing authority is checked only by the
    host-supplied *authority_verifier*. Without one the receipt is never accepted.
    """
    reasons: list[str] = []
    if not isinstance(serenity_receipt, dict) or not serenity_receipt:
        return False, ["SERENITY_RECEIPT_REQUIRED"]
    if serenity_receipt.get("schema") != SERENITY_RECEIPT_SCHEMA:
        reasons.append("serenity_schema_invalid")
    if serenity_receipt.get("approved") is not True:
        reasons.append("serenity_not_approved")
    if serenity_receipt.get("skill_id") != skill_id:
        reasons.append("serenity_skill_mismatch")
    if serenity_receipt.get("content_sha256") != content_sha256:
        reasons.append("serenity_content_sha_mismatch")
    if serenity_receipt.get("run_id") != run_id:
        reasons.append("serenity_run_id_mismatch")
    if serenity_receipt.get("workspace_id") != workspace_identity(workspace_root):
        reasons.append("serenity_workspace_mismatch")
    if serenity_receipt.get("policy_digest") != current_policy_digest(workspace_root):
        reasons.append("serenity_policy_digest_changed")
    approver = serenity_receipt.get("approved_by")
    if not isinstance(approver, str) or not approver.strip():
        reasons.append("serenity_approver_missing")
    risk = str(serenity_receipt.get("risk_level", "unknown")).lower()
    if risk not in ("low", "medium"):
        reasons.append(f"serenity_risk_blocked:{risk}")
    if serenity_receipt.get("mandatory_gates_passed") is not True:
        reasons.append("serenity_mandatory_gates_unverified")
    violations = serenity_receipt.get("permission_violations", 1)
    if type(violations) is not int:
        reasons.append("serenity_permission_violations_invalid")
    elif violations != 0:
        reasons.append("serenity_permission_violations_nonzero")
    if serenity_receipt.get("reproducible") is not True:
        reasons.append("serenity_reproducibility_false")

    scope_ok, scope_err = _scope_covers_boundary(
        serenity_receipt.get("approved_scope"), unit.boundary
    )
    if not scope_ok and scope_err:
        reasons.append(scope_err)

    if serenity_receipt.get("require_policy_trust") is True:
        pt_state, pt_err = load_policy_trust(workspace_root, scope=SCOPE_POLICY_ASK)
        if pt_state is None or pt_err is not None or pt_state.level < 1:
            reasons.append(f"policy_trust_unverified:{pt_err or 'level_too_low'}")

    host_promise = load_host_promise_observation(workspace_root)
    if host_promise is not None and host_promise.get("state") != "OBSERVED":
        reasons.append("host_promise_projection_invalid")

    if authority_verifier is None:
        reasons.append("SERENITY_ISSUER_UNVERIFIED:no_host_authority_verifier")
    elif not reasons:
        # Only ask the host's approval authority once the structure is bound, so a
        # malformed request never triggers a real approval check.
        try:
            issuer_ok, issuer_err = authority_verifier(dict(serenity_receipt))
        except Exception as exc:  # any verifier failure is fail-closed
            issuer_ok, issuer_err = False, f"verifier_error:{type(exc).__name__}"
        if issuer_ok is not True:
            reasons.append(f"serenity_issuer_rejected:{issuer_err or 'unspecified'}")

    return len(reasons) == 0, reasons


def check_execution_permission(
    workspace_root: Path,
    skill_id: str,
    *,
    execution_mode: str = "manual",
    env_fingerprint: str | None = None,
    authority_verifier: ApprovalAuthorityVerifier | None = None,
) -> dict[str, Any]:
    """Check whether *skill_id* is permitted to execute under *execution_mode* (`manual` | `shadow` | `auto`)."""
    if execution_mode not in ("manual", "shadow", "auto"):
        raise ValueError(f"unsupported execution_mode: {execution_mode}")

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
    unit = next((m.skills[skill_id] for m in modules.values() if skill_id in m.skills), None)
    if unit is None:
        return {
            "allowed": False,
            "execution_mode": execution_mode,
            "reason": f"AUTO_RUN_BLOCKED_MISSING_UNIT:{skill_id}",
            "trust_stage": stage,
        }
    scope_ok, scope_err = _scope_covers_boundary(trust_state.get("approved_scope"), unit.boundary)
    if not scope_ok:
        return {
            "allowed": False,
            "execution_mode": execution_mode,
            "reason": f"AUTO_RUN_BLOCKED_{scope_err}",
            "trust_stage": stage,
        }

    # The trust file is only a cache. Authority is re-checked at execution time
    # against the current skill content and boundary, by the host's verifier.
    stored_receipt = trust_state.get("serenity_receipt")
    approval_ok, approval_reasons = verify_serenity_approval_receipt(
        workspace_root,
        stored_receipt if isinstance(stored_receipt, dict) else None,
        skill_id=skill_id,
        unit=unit,
        content_sha256=unit.content_sha256,
        run_id=str((stored_receipt or {}).get("run_id", ""))
        if isinstance(stored_receipt, dict)
        else "",
        authority_verifier=authority_verifier,
    )
    if not approval_ok:
        return {
            "allowed": False,
            "execution_mode": execution_mode,
            "reason": f"AUTO_RUN_BLOCKED_APPROVAL_UNVERIFIED:{approval_reasons[0]}",
            "trust_stage": stage,
        }

    return {
        "allowed": True,
        "execution_mode": execution_mode,
        "reason": None,
        "trust_stage": stage,
        "verified_content_sha256": unit.content_sha256,
        "verified_boundary": unit.boundary.to_dict(),
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
) -> dict[str, Any]:
    """Run the modular factory loop with preflight gap analysis, trust gating, subprocess isolation, and Progressive Disclosure."""
    if execution_mode not in ("manual", "shadow", "auto"):
        raise ValueError(f"unsupported execution_mode: {execution_mode}")

    selective_result: dict[str, Any] | None = None
    if selective_activation:
        selective_result = select_and_activate_for_task(
            workspace_root,
            prompt,
            profile_name=profile_name,
            explicit_taste_feedback=explicit_taste_feedback,
            deduplicate_by_slot=deduplicate_by_slot,
            disable_others=True,
        )

    acquire_run_lock(workspace_root, run_id)
    t0 = time.monotonic()
    try:
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

        active_taste_rules = [
            item["rule"]
            for item in preflight_gap_report.get("taste_synthesis", {}).get("personal_taste", [])
            if isinstance(item, dict) and item.get("rule")
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

        for wave in execution_waves:
            # First enforce execution_mode (`AUTO_RUN`) trust gate per skill in wave before disclosing/running
            runnable_wave: list[str] = []
            for skill_id in wave:
                perm_check = check_execution_permission(
                    workspace_root,
                    skill_id,
                    execution_mode=execution_mode,
                    env_fingerprint=env_fingerprint,
                    authority_verifier=authority_verifier,
                )
                if perm_check["allowed"] and execution_mode == "auto":
                    # The run executes the unit loaded at run start; it must be the
                    # exact unit whose approval was just verified, or a lock.json
                    # edit between the two reads would widen the boundary.
                    _run_unit = unit_lookup[skill_id][1]
                    if _run_unit.content_sha256 != perm_check.get(
                        "verified_content_sha256"
                    ) or _run_unit.boundary.to_dict() != perm_check.get("verified_boundary"):
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
                snap_before = _snapshot_workspace_files(workspace_root)

                def _run_ro_cmd(
                    sid: str,
                ) -> tuple[str, subprocess.CompletedProcess[str] | Exception]:
                    m_rec, u = unit_lookup[sid]
                    cmd_args = (skill_commands or {})[sid]
                    try:
                        proc = subprocess.run(
                            cmd_args,
                            cwd=str(workspace_root),
                            env=_build_isolated_env(
                                u,
                                workspace_root,
                                module_source_path=m_rec.source_path,
                                active_taste_rules=active_taste_rules,
                            ),
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
                    ThreadPoolExecutor(max_workers=min(4, len(runnable_wave))) as pool,
                ):
                    results = dict(pool.map(_run_ro_cmd, runnable_wave))

                illegal_writes = _restore_and_detect_writes(workspace_root, snap_before)
                for skill_id in runnable_wave:
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
                                **_stdout_integrity_fields(proc.stdout),
                                "role_hint": unit.role_hint,
                                "content_sha256": unit.content_sha256,
                            }
                continue

            for skill_id in runnable_wave:
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
                                env=_build_isolated_env(
                                    unit,
                                    workspace_root,
                                    module_source_path=mod.source_path,
                                    active_taste_rules=active_taste_rules,
                                ),
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
                        "verify_stdout_sha256": v_stdout_meta["full_stdout_sha256"][:12],
                        "full_verify_stdout_sha256": v_stdout_meta["full_stdout_sha256"],
                        "normalized_verify_stdout_sha256": v_stdout_meta[
                            "normalized_stdout_sha256"
                        ],
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
                    **v_stdout_meta,
                    "attestation": attestation,
                }

        duration_ms = int((time.monotonic() - t0) * 1000)

        orchestration_observations_recorded = 0
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
            "skills_rolled_back_post_write": sum(
                1 for m in modes if m == "ROLLED_BACK_ILLEGAL_WRITE"
            ),
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
            "personal_taste_rules": active_taste_rules,
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
        assert isinstance(verifier_receipt, dict)
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
    serenity_receipt: dict[str, Any] | None = None,
    serenity_gate_approved: bool = False,
    builder_actor: str | None = None,
    builder_session_id: str | None = None,
    s_score: float | None = None,
    run_id: str = "trust-eval-01",
    source: str = "kingdom.agent-loop.eros-gate",
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
    - `AUTO_RUN` rejects a bare `serenity_gate_approved=True` boolean without a verified
      `serenity_receipt` bound to `workspace_id`, `policy_digest`, `risk_level`, `approved_scope`,
      `content_sha256`, and `run_id`, and confirmed by the host's *authority_verifier*.
      A receipt built by `issue_serenity_approval_receipt` alone never reaches `AUTO_RUN`.
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

    serenity_verified, serenity_reasons = verify_serenity_approval_receipt(
        workspace_root,
        serenity_receipt,
        skill_id=skill_id,
        unit=unit,
        content_sha256=unit.content_sha256,
        run_id=run_id,
        authority_verifier=authority_verifier,
    )
    bare_boolean_rejected = bool(serenity_gate_approved and not serenity_verified)

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
            if serenity_verified and interventions_delta <= 0:
                new_stage = "AUTO_RUN"
                decision = "AUTO_RUN"
                admitted = True
            else:
                new_stage = "TRUSTED"
                decision = "ASK_COMMANDER"
                admitted = False
                promotion_blocked_reason = (
                    ",".join(serenity_reasons) if serenity_reasons else "SERENITY_RECEIPT_INVALID"
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
        serenity_receipt.get("approved_scope")
        if serenity_verified and isinstance(serenity_receipt, dict)
        else unit.boundary.to_dict()
    )

    record = {
        "skill_id": skill_id,
        "module_id": mod.module_id,
        "trust_stage": new_stage,
        "previous_stage": current_stage,
        "verifier_status": v_status,
        "eval_verdict": e_verdict,
        "reproducible": reproducible,
        "serenity_verified": serenity_verified,
        "serenity_gate_approved": serenity_verified,
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
        "serenity_receipt": serenity_receipt if serenity_verified else None,
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
            "replay_blocked": replay_blocked,
            "stage_skip_blocked": stage_skip_blocked,
            "serenity_verified": serenity_verified,
        },
    }
    admission_obs = append_admission_observation(workspace_root, obs_raw)
    return {
        **record,
        "admission_decision": decision,
        "admitted": admitted,
        "admission_observation": admission_obs,
    }
