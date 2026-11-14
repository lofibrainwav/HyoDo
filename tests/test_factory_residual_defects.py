"""Regression tests for factory-harness defects found after #620 (`examples/factory-loop/`).

Each test pins one honest-evidence rule: real timestamps, no zero-gate success,
true taste provenance, host-neutral names, task-scoped activation that leaves
the registry as it was, no claimed enforcement that did not happen, approvals
bound to the whole module tree and the exact command, and recorded module origin.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from test_factory_harness import (
    _host_authority,
    _init_clean_repo,
    _load_factory_module,
    _write_skill,
)

FACTORY_DIR = Path(__file__).resolve().parents[1] / "examples" / "factory-loop"
HOST_ENFORCED = ("network_access", "browser_automation", "filesystem_write")


def _parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _assert_now(value: str, start: datetime, end: datetime) -> None:
    ts = _parse_ts(value)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    assert start - timedelta(seconds=2) <= ts <= end + timedelta(seconds=2), value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _exec_skill_module(
    base: Path, name: str, *, script: str | None = None, extra_frontmatter: str = ""
) -> Path:
    """A module with one engineering skill that may run a subprocess (has a script)."""
    mod_dir = base / name
    sdir = _write_skill(
        mod_dir,
        "tdd",
        "---\nname: tdd\ncategory: engineering\nsubprocess_exec: true\n"
        f"{extra_frontmatter}description: TDD implementation skill\n---\n# TDD\n",
    )
    (sdir / "run.sh").write_text(script or "echo RUN_SH_V1\n", encoding="utf-8")
    return mod_dir


def _forge_auto_run(
    factory: Any, repo: Path, skill_id: str, *, command: list[str] | None, run_id: str
) -> dict[str, Any]:
    """Write an AUTO_RUN trust record carrying a structurally bound approval request.

    Any local process can do this; only the host authority verifier turns it into
    permission, which is exactly what these tests exercise.
    """
    from hyodo.policy_trust import current_policy_digest
    from hyodo.user_state import workspace_identity

    base = factory.get_skill_trust_state(repo, skill_id)
    receipt = factory.issue_host_approval_request(
        repo, skill_id=skill_id, run_id=run_id, approved_by="host-operator", command=command
    )
    skills = {
        skill_id: {
            "skill_id": skill_id,
            "trust_stage": "AUTO_RUN",
            "verifier_status": "PASS",
            "eval_verdict": "HELPED",
            "workspace_id": workspace_identity(repo),
            "policy_digest": current_policy_digest(repo),
            "approved_scope": base["boundary"],
            "approval_receipt": receipt,
            "content_sha256": base["content_sha256"],
            "version": base["version"],
            "boundary": base["boundary"],
            "module_source_path": base["module_source_path"],
            "module_tree_sha256": base["module_tree_sha256"],
            "env_fingerprint": base["env_fingerprint"],
        }
    }
    canonical = json.dumps(skills, sort_keys=True, separators=(",", ":"), default=str)
    trust_path = repo / ".hyodo" / "factory" / "trust_state.json"
    trust_path.parent.mkdir(parents=True, exist_ok=True)
    trust_path.write_text(
        json.dumps(
            {
                "schema": "hyodo.factory-trust-state/v1",
                "skills": skills,
                "ledger_digest": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    return receipt


# 1. Fixed timestamps -------------------------------------------------------


def test_factory_evidence_timestamps_are_real_utc_time(tmp_path: Path) -> None:
    from hyodo.admission_observation import ADMISSION_OBSERVATIONS_RELATIVE_PATH
    from hyodo.orchestration_observation import read_orchestration_observations

    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    _init_clean_repo(repo)
    start = datetime.now(timezone.utc)
    mod = factory.add_module(repo, _exec_skill_module(tmp_path, "clock"), module_id="clock")
    res = factory.execute_modular_run(
        repo,
        run_id="run-clock",
        prompt="implement tdd feature",
        skill_commands={"clock/tdd": [sys.executable, "-c", "print('ok')"]},
        verify_cmd=[sys.executable, "-c", "print('verified')"],
    )
    factory.evaluate_and_promote_trust(repo, skill_id="clock/tdd", run_id="run-clock-trust")
    end = datetime.now(timezone.utc)

    _assert_now(mod.installed_at, start, end)
    _assert_now(mod.origin["recorded_at"], start, end)
    attestation = res["independent_verifier_receipt"]["attestation"]
    _assert_now(attestation["observed_at"], start, end)
    events = _read_jsonl(repo / ".hyodo" / "agent-events.jsonl")
    assert events
    for row in events:
        _assert_now(row["ts"], start, end)
    observations = read_orchestration_observations(repo)
    assert observations
    for row in observations:
        _assert_now(row["ts"], start, end)
    admissions = _read_jsonl(repo / ADMISSION_OBSERVATIONS_RELATIVE_PATH)
    assert admissions
    for row in admissions:
        _assert_now(row["ts"], start, end)
    # A lock row without an install time is unknown, never "now".
    from factory.contracts import ModuleRecord

    legacy = ModuleRecord.from_dict({k: v for k, v in mod.to_dict().items() if k != "installed_at"})
    assert legacy.installed_at == "UNOBSERVED"
    hardcoded = re.compile(r"2026-11-13T00:00:\d\dZ")
    for path in (FACTORY_DIR / "factory").glob("*.py"):
        assert not hardcoded.search(path.read_text(encoding="utf-8")), path.name


# 2. Zero-gate success ------------------------------------------------------


def test_cli_run_exit_code_is_unobserved_without_execution_or_gate(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    _init_clean_repo(repo)
    root = ["--root", str(repo)]
    ok_cmd = f"tdd={sys.executable} -c print(1)"

    # Nothing registered, nothing executed, no verifier: UNOBSERVED, not success.
    assert factory.main([*root, "run", "implement feature", "--run-id", "r-empty"]) == 2
    out = json.loads(capsys.readouterr().out)
    assert out["run_verdict"]["decision"] == "UNOBSERVED"
    assert "no_skill_executed" in out["run_verdict"]["reasons"]

    factory.add_module(repo, _exec_skill_module(tmp_path, "gate"), module_id="gate")
    verify_ok = f"{sys.executable} -c print(2)"
    verify_bad = f'{sys.executable} -c "raise SystemExit(3)"'

    # A skill executed but no independent verifier ran: still UNOBSERVED.
    rc = factory.main(
        [*root, "run", "implement tdd", "--run-id", "r-noverify", "--skill-cmd", f"gate/{ok_cmd}"]
    )
    assert rc == 2
    assert json.loads(capsys.readouterr().out)["run_verdict"]["reasons"] == [
        "independent_verifier_not_run"
    ]

    # A verifier ran but no skill executed (disclosure only): still UNOBSERVED.
    rc = factory.main(
        [*root, "run", "implement tdd", "--run-id", "r-noskill", "--verify-cmd", verify_ok]
    )
    assert rc == 2
    capsys.readouterr()

    # Failure stays 1.
    rc = factory.main(
        [
            *root,
            "run",
            "implement tdd",
            "--run-id",
            "r-fail",
            "--skill-cmd",
            f"gate/{ok_cmd}",
            "--verify-cmd",
            verify_bad,
        ]
    )
    assert rc == 1
    capsys.readouterr()

    # Executed and independently verified: the only 0.
    rc = factory.main(
        [
            *root,
            "run",
            "implement tdd",
            "--run-id",
            "r-pass",
            "--skill-cmd",
            f"gate/{ok_cmd}",
            "--verify-cmd",
            verify_ok,
        ]
    )
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["run_verdict"]["decision"] == "PASS"


# 3. Taste provenance -------------------------------------------------------


def test_profile_rules_are_not_labelled_or_passed_as_host_taste(tmp_path: Path) -> None:
    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    _init_clean_repo(repo)
    factory.add_module(repo, _exec_skill_module(tmp_path, "taste"), module_id="taste")

    # No profile chosen: none is silently picked, so no repo-shipped rule appears.
    auto = factory.analyze_capability_gaps(repo, "implement tdd feature")
    assert auto["profile"] == "auto"
    assert auto["taste_synthesis"]["host_taste_file_present"] is False
    assert auto["taste_synthesis"]["personal_taste"] == []

    # A chosen profile's rules are profile defaults, never HOST_CONFIGURED.
    dev = factory.analyze_capability_gaps(
        repo,
        "implement tdd feature",
        profile_name="development",
        explicit_taste_feedback=["prefer:taste/tdd"],
    )
    items = {i["rule"]: i for i in dev["taste_synthesis"]["personal_taste"]}
    profile_items = [i for i in items.values() if i["source"] == "profile_default:development"]
    assert profile_items
    assert all(i["authority"] == "PROFILE_DEFAULT" for i in profile_items)
    assert items["prefer:taste/tdd"]["authority"] == "HOST_CONFIGURED"
    assert items["prefer:taste/tdd"]["source"] == "explicit_taste_feedback"

    probe = (
        "import json, os; print(json.dumps(json.loads("
        "os.environ.get('HYODO_HOST_PERSONAL_TASTE_JSON', '[]'))))"
    )
    res = factory.execute_modular_run(
        repo,
        run_id="run-taste-provenance",
        prompt="implement tdd feature",
        profile_name="development",
        skill_commands={"taste/tdd": [sys.executable, "-c", probe]},
    )
    out = res["skill_outputs"]["taste/tdd"]
    assert out["execution_state"] == "EXECUTED_PASS"
    assert json.loads(out["stdout"]) == []
    assert res["personal_taste_rules"] == []
    assert res["profile_default_taste_rules"]


# 4. KINGDOM coupling -------------------------------------------------------


def test_factory_harness_is_host_neutral() -> None:
    factory = _load_factory_module()
    coupled = re.compile(r"kingdom|serenity|\beros\b", re.IGNORECASE)
    for path in sorted(FACTORY_DIR.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        assert not coupled.search(text), path.relative_to(FACTORY_DIR)
    from factory.contracts import FACTORY_APPROVAL_REQUEST_SCHEMA

    assert FACTORY_APPROVAL_REQUEST_SCHEMA == "hyodo.factory-approval-request/v1"
    assert not hasattr(factory, "issue_serenity_approval_receipt")
    import inspect

    source_default = (
        inspect.signature(factory.evaluate_and_promote_trust).parameters["source"].default
    )
    assert source_default == "hyodo-factory.trust-ladder"
    # The router docstring no longer states an unverified skill count as fact.
    from factory import router

    assert "170+" not in (router.__doc__ or "")


# 5. Task-scoped selective activation ---------------------------------------


def _enabled_flags(factory: Any, repo: Path) -> dict[str, Any]:
    return {
        mod_id: (mod.enabled, {sid: u.enabled for sid, u in sorted(mod.skills.items())})
        for mod_id, mod in factory.load_registry_state(repo).items()
    }


def test_selective_activation_leaves_persistent_registry_state_unchanged(
    tmp_path: Path,
) -> None:
    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    _init_clean_repo(repo)
    pkg = tmp_path / "scoped"
    _write_skill(pkg, "tdd-one", "---\ncategory: engineering\n---\n# TDD one\nTDD.\n")
    _write_skill(pkg, "office-doc", "---\ncategory: office\n---\n# Office\nDocs.\n")
    _write_skill(pkg, "art", "---\ncategory: creative\n---\n# Art\nArt.\n")
    factory.add_module(repo, pkg, module_id="scoped")
    factory.disable_target(repo, "scoped/art")
    before = _enabled_flags(factory, repo)
    hooks_before = (repo / ".hyodo" / "factory" / "active_hooks.json").read_text()

    res = factory.execute_modular_run(
        repo, run_id="run-scoped", prompt="implement tdd", selective_activation=True
    )
    assert res["selective_activation"]["registry_state_after_run"] == "RESTORED"
    assert "scoped/office-doc" in res["selective_activation"]["restored_skill_flags"]
    assert _enabled_flags(factory, repo) == before
    assert (repo / ".hyodo" / "factory" / "active_hooks.json").read_text() == hooks_before

    # A run that raises still restores the registry.
    def _boom(_root: Path) -> None:
        raise RuntimeError("host aborted the run")

    with pytest.raises(RuntimeError, match="host aborted"):
        factory.execute_modular_run(
            repo,
            run_id="run-scoped-abort",
            prompt="implement tdd",
            selective_activation=True,
            mid_run_callback=_boom,
        )
    assert _enabled_flags(factory, repo) == before


# 6. Unenforced permissions, live contract, wave attribution, asserts --------


def test_unenforced_network_restriction_is_reported_and_refuses_auto(tmp_path: Path) -> None:
    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    _init_clean_repo(repo)
    factory.add_module(
        repo,
        _exec_skill_module(tmp_path, "net", extra_frontmatter="filesystem_write: false\n"),
        module_id="net",
    )
    cmd = [sys.executable, "-c", "print('ran')"]

    manual = factory.execute_modular_run(
        repo, run_id="run-net-manual", prompt="implement tdd", skill_commands={"net/tdd": cmd}
    )
    report = manual["skill_outputs"]["net/tdd"]["boundary_enforcement"]
    assert report["network_access"] == "UNENFORCED"
    assert report["browser_automation"] == "UNENFORCED"
    assert report["filesystem_write"] == "PARTIAL"
    assert report["subprocess_exec"] == "NOT_RESTRICTED"

    _forge_auto_run(factory, repo, "net/tdd", command=cmd, run_id="host-approved")
    host = _host_authority({"host-approved"})
    refused = factory.check_execution_permission(
        repo, "net/tdd", execution_mode="auto", authority_verifier=host, command=cmd
    )
    assert refused["allowed"] is False
    assert refused["reason"].startswith("AUTO_RUN_BLOCKED_UNENFORCED_RESTRICTION:")
    assert "network_access" in refused["reason"]
    allowed = factory.check_execution_permission(
        repo,
        "net/tdd",
        execution_mode="auto",
        authority_verifier=host,
        command=cmd,
        host_enforced_restrictions=HOST_ENFORCED,
    )
    assert allowed["allowed"] is True
    assert allowed["authorized_by"] == "host_authority_verifier"


def test_host_matrix_never_claims_a_verified_live_contract(tmp_path: Path) -> None:
    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    _init_clean_repo(repo)
    matrix = factory.verify_host_integrations(repo)
    assert matrix
    for host, row in matrix.items():
        assert row["verified_live_contract"] is False, host
        assert row["live_contract"] == "UNOBSERVED", host


def test_parallel_wave_write_is_not_blamed_on_every_skill(tmp_path: Path) -> None:
    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    _init_clean_repo(repo)
    mod_dir = tmp_path / "wave"
    for name, desc in (
        ("audit-one", "Parallel simplify yagni audit skill"),
        ("security-two", "Parallel security skill"),
    ):
        sdir = _write_skill(mod_dir, name, f"---\nname: {name}\ndescription: {desc}\n---\n# X\n")
        (sdir / "scripts").mkdir()
        (sdir / "scripts" / "run.py").write_text("print('x')\n", encoding="utf-8")
    factory.add_module(repo, mod_dir, module_id="wave")
    writer = (
        "import os, pathlib; root = pathlib.Path('.').resolve(); os.chmod(root, 0o755); "
        "(root / 'sneaky.txt').write_text('x')"
    )
    res = factory.execute_modular_run(
        repo,
        run_id="run-wave",
        prompt="audit root cause and check security vulnerability",
        skill_commands={
            "wave/audit-one": [sys.executable, "-c", writer],
            "wave/security-two": [sys.executable, "-c", "print('innocent')"],
        },
    )
    assert res["execution_summary"]["parallel_waves_executed"] == 1
    assert not (repo / "sneaky.txt").exists()
    violations = res["permission_violations"]
    assert len(violations) == 1
    assert "attribution=UNOBSERVED" in violations[0]
    assert not any(
        v.endswith(":wave/security-two") or ":wave/security-two:" in v for v in violations
    )
    innocent = res["skill_outputs"]["wave/security-two"]
    assert innocent["write_attribution"] == "UNOBSERVED"
    assert innocent["gate_verdict"] == "UNOBSERVED"
    assert res["run_verdict"]["decision"] == "FAIL"


def test_factory_validation_does_not_use_assert() -> None:
    offenders = []
    for path in sorted(FACTORY_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        offenders += [
            f"{path.relative_to(FACTORY_DIR)}:{n.lineno}"
            for n in ast.walk(tree)
            if isinstance(n, ast.Assert)
        ]
    assert offenders == []


# 7. Approval binds the whole module tree and the exact command --------------


def test_approval_binds_module_tree_source_path_and_command(tmp_path: Path) -> None:
    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    _init_clean_repo(repo)
    mod_dir = _exec_skill_module(tmp_path, "bound")
    factory.add_module(repo, mod_dir, module_id="bound")
    cmd = ["sh", "-c", 'sh "$CLAUDE_SKILL_DIR/run.sh"']
    host = _host_authority({"host-approved"})
    receipt = _forge_auto_run(factory, repo, "bound/tdd", command=cmd, run_id="host-approved")
    assert receipt["command"] == cmd
    assert re.fullmatch(r"[0-9a-f]{64}", receipt["module_tree_sha256"])

    def run(run_id: str, command: list[str]) -> dict[str, Any]:
        return factory.execute_modular_run(
            repo,
            run_id=run_id,
            prompt="implement tdd",
            execution_mode="auto",
            authority_verifier=host,
            host_enforced_restrictions=HOST_ENFORCED,
            skill_commands={"bound/tdd": command},
        )["skill_outputs"]["bound/tdd"]

    ok = run("run-bound-ok", cmd)
    assert ok["execution_state"] == "EXECUTED_PASS"
    assert "RUN_SH_V1" in ok["stdout"]

    # A different host command than the one approved is refused.
    other = run("run-bound-other-cmd", ["sh", "-c", "echo OTHER"])
    assert other["execution_state"] == "BLOCKED_UNVERIFIED_AUTONOMOUS_EXECUTION"
    assert "approval_command_changed" in other["reason"]

    # Editing run.sh (not SKILL.md) after approval blocks the run and demotes trust.
    (mod_dir / "skills" / "tdd" / "run.sh").write_text("echo PWNED\n", encoding="utf-8")
    edited = run("run-bound-edited", cmd)
    assert edited["execution_state"] == "DEGRADED_PREFLIGHT_BLOCKED"
    assert "stdout" not in edited
    state = factory.get_skill_trust_state(repo, "bound/tdd")
    assert state["trust_stage"] == "VERIFY"
    assert "module_tree_changed" in state["demotion_reason"]
    ok_bind, reasons = factory.verify_host_approval_receipt(
        repo,
        receipt,
        skill_id="bound/tdd",
        unit=factory.load_registry_state(repo)["bound"].skills["bound/tdd"],
        content_sha256=receipt["content_sha256"],
        run_id="host-approved",
        command=cmd,
        authority_verifier=host,
    )
    assert ok_bind is False
    assert "approval_module_tree_changed" in reasons


def test_approval_rejects_a_changed_lock_source_path(tmp_path: Path) -> None:
    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    _init_clean_repo(repo)
    mod_dir = _exec_skill_module(tmp_path, "moved")
    factory.add_module(repo, mod_dir, module_id="moved")
    cmd = [sys.executable, "-c", "print('ok')"]
    receipt = _forge_auto_run(factory, repo, "moved/tdd", command=cmd, run_id="host-approved")

    # Same content at another path: the lock now points the skill somewhere else.
    clone = tmp_path / "moved-copy"
    shutil.copytree(mod_dir, clone)
    lock_path = repo / ".hyodo" / "factory" / "lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["modules"]["moved"]["source_path"] = str(clone.resolve())
    lock_path.write_text(json.dumps(lock), encoding="utf-8")

    unit = factory.load_registry_state(repo)["moved"].skills["moved/tdd"]
    ok, reasons = factory.verify_host_approval_receipt(
        repo,
        receipt,
        skill_id="moved/tdd",
        unit=unit,
        content_sha256=receipt["content_sha256"],
        run_id="host-approved",
        command=cmd,
        authority_verifier=_host_authority({"host-approved"}),
    )
    assert ok is False
    assert "approval_module_source_path_changed" in reasons
    assert factory.doctor(repo)["status"] == "DEGRADED"


# 8. Module origin in lock.json + doctor drift ------------------------------


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def test_add_records_module_origin_and_doctor_reports_drift(tmp_path: Path) -> None:
    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    _init_clean_repo(repo)
    mod_dir = _exec_skill_module(tmp_path, "origin-pack")
    _git(mod_dir, "init", "-q")
    _git(mod_dir, "config", "user.email", "test@example.com")
    _git(mod_dir, "config", "user.name", "Test")
    _git(mod_dir, "remote", "add", "origin", "https://user:s3cret@example.com/org/skills.git")
    _git(mod_dir, "add", ".")
    _git(mod_dir, "commit", "-q", "-m", "init")
    head = _git(mod_dir, "rev-parse", "HEAD")

    factory.add_module(repo, mod_dir, module_id="origin-pack")
    lock = json.loads((repo / ".hyodo" / "factory" / "lock.json").read_text(encoding="utf-8"))
    origin = lock["modules"]["origin-pack"]["origin"]
    assert origin["source_path"] == str(mod_dir.resolve())
    assert origin["git_repo"] is True
    assert origin["git_remote_url"] == "https://example.com/org/skills.git"
    assert "s3cret" not in json.dumps(lock)
    assert origin["git_commit"] == head
    assert origin["git_dirty"] is False
    assert re.fullmatch(r"[0-9a-f]{64}", origin["module_tree_sha256"])
    assert origin["module_tree_file_count"] == 2
    healthy = factory.doctor(repo)
    assert healthy["status"] == "HEALTHY"
    assert healthy["module_provenance"]["origin-pack"]["state"] == "UNCHANGED"

    # A non-SKILL.md file changes: lock integrity alone would still call this healthy.
    (mod_dir / "skills" / "tdd" / "run.sh").write_text("echo changed\n", encoding="utf-8")
    drifted = factory.doctor(repo)
    assert drifted["status"] == "DEGRADED"
    assert "module_tree_drift:origin-pack" in drifted["problems"]
    assert drifted["module_provenance"]["origin-pack"]["git_dirty_now"] is True

    _git(mod_dir, "commit", "-q", "-am", "change run.sh")
    moved = factory.doctor(repo)
    assert "module_origin_drift:origin-pack:git_commit" in moved["problems"]

    factory.update_module(repo, "origin-pack")
    assert factory.doctor(repo)["status"] == "HEALTHY"


def test_symlinked_module_tree_is_unbindable(tmp_path: Path) -> None:
    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    _init_clean_repo(repo)
    mod_dir = _exec_skill_module(tmp_path, "linky")
    outside = tmp_path / "outside.sh"
    outside.write_text("echo outside\n", encoding="utf-8")
    (mod_dir / "skills" / "tdd" / "helper.sh").symlink_to(outside)

    rec = factory.add_module(repo, mod_dir, module_id="linky")
    assert rec.origin["module_tree_sha256"] is None
    assert rec.origin["module_tree_error"] == "symlink_refused:skills/tdd/helper.sh"
    assert factory.doctor(repo)["module_provenance"]["linky"]["state"] == "UNBINDABLE"
    with pytest.raises(ValueError, match="module tree unbindable"):
        factory.issue_host_approval_request(
            repo, skill_id="linky/tdd", run_id="r", approved_by="host", command=None
        )


# 9. Tests that would pass with nothing attached ---------------------------


def test_external_repo_tests_skip_instead_of_passing_vacuously(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    harness = (Path(__file__).parent / "test_factory_harness.py").read_text(encoding="utf-8")
    # No private, machine-specific paths: inputs come from an environment variable.
    assert "/home/antigravity" not in harness
    from test_factory_harness import EXTERNAL_SKILLS_ENV, _external_skill_repos

    monkeypatch.delenv(EXTERNAL_SKILLS_ENV, raising=False)
    with pytest.raises(pytest.skip.Exception):
        _external_skill_repos()
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setenv(EXTERNAL_SKILLS_ENV, str(empty))
    with pytest.raises(pytest.skip.Exception):
        _external_skill_repos()
