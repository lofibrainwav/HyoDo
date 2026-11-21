"""Factory doctor reports each evidence axis separately.

Integrity is not health, registration is not connection, an old execution is
not evidence for new content, and nothing here is "helped". These tests pin
that separation and the read-only supply-chain check (`verify-upstream`).
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from test_factory_harness import _init_clean_repo, _load_factory_module

FACTORY_DIR = Path(__file__).resolve().parents[1] / "examples" / "factory-loop"


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def _module(
    base: Path,
    name: str,
    body: str = "# Probe\n\nRead-only probe skill.\n",
    *,
    git: bool = True,
    remote: str | None = "https://example.com/{name}.git",
) -> Path:
    root = base / name
    skill_dir = root / ".agents" / "skills" / "probe"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: probe\ndescription: probe skill for {name}\n---\n{body}", encoding="utf-8"
    )
    if git:
        _git(root, "init", "-q")
        _git(root, "config", "user.email", "t@example.com")
        _git(root, "config", "user.name", "T")
        _git(root, "add", ".")
        _git(root, "commit", "-q", "-m", "init")
        if remote:
            _git(root, "remote", "add", "origin", remote.format(name=name))
    return root


def _workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    _init_clean_repo(ws)
    return ws


def _skill_md(mod_root: Path) -> Path:
    return mod_root / ".agents" / "skills" / "probe" / "SKILL.md"


def test_plain_copy_is_intact_but_not_healthy(tmp_path: Path) -> None:
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    mod = _module(tmp_path, "copied", git=False)
    factory.add_module(ws, mod)

    rep = factory.doctor(ws)
    axes = rep["axes"]["copied"]
    assert axes["content_integrity"] == "UNCHANGED"
    assert axes["recorded_upstream"] == "NO_GIT_ORIGIN"
    assert rep["problems"] == []
    assert rep["status"] == "UNOBSERVED"
    assert "module_upstream_unrecorded:copied|NO_GIT_ORIGIN" in rep["warnings"]
    assert "content integrity" in rep["status_scope"]


def test_clean_commit_is_healthy_and_other_axes_stay_unobserved(tmp_path: Path) -> None:
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    factory.add_module(ws, _module(tmp_path, "pinned"))

    rep = factory.doctor(ws)
    assert rep["status"] == "HEALTHY"
    skill = rep["axes"]["pinned"]["skills"]["pinned/probe"]
    assert skill["host_connection"] == "UNOBSERVED"
    assert skill["execution"] == "UNOBSERVED"
    assert skill["independent_verification"] == "UNOBSERVED"
    assert skill["helped"] == "UNOBSERVED"
    assert skill["trust_stage"] == "VERIFY"
    assert rep["axes"]["pinned"]["upstream_verified"] == "UNOBSERVED"


def test_host_readback_connected_drifted_absent(tmp_path: Path) -> None:
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    mod = _module(tmp_path, "hosted")
    factory.add_module(ws, mod)

    host = tmp_path / "host-skills"
    (host / "probe").mkdir(parents=True)
    (host / "probe" / "SKILL.md").write_bytes(_skill_md(mod).read_bytes())
    rep = factory.doctor(ws, host_skill_roots=[host])
    assert rep["axes"]["hosted"]["skills"]["hosted/probe"]["host_connection"] == "CONNECTED"
    assert rep["status"] == "HEALTHY"

    # Gate 9: the host serves different content than what was registered.
    (host / "probe" / "SKILL.md").write_text("# tampered host copy\n", encoding="utf-8")
    rep = factory.doctor(ws, host_skill_roots=[host])
    assert rep["axes"]["hosted"]["skills"]["hosted/probe"]["host_connection"] == "DRIFTED"
    assert any(p.startswith("host_copy_drift:hosted/probe|") for p in rep["problems"])
    assert rep["status"] == "DEGRADED"

    empty = tmp_path / "empty-host"
    empty.mkdir()
    rep = factory.doctor(ws, host_skill_roots=[empty])
    assert rep["axes"]["hosted"]["skills"]["hosted/probe"]["host_connection"] == "ABSENT"
    assert "host_copy_absent:hosted/probe" in rep["warnings"]


def _observe(
    ws: Path,
    skill_id: str,
    content_sha: str,
    state: str = "completed",
    unobserved: int = 0,
    ts: str | None = None,
    ledger: bool = True,
    ledger_tool: str | None = None,
) -> None:
    sys.path.insert(0, str(FACTORY_DIR))
    from hyodo.orchestration_observation import (
        ORCHESTRATION_OBSERVATION_SCHEMA_VERSION,
        append_orchestration_observation,
    )

    payload: dict[str, Any] = {
        "schema": ORCHESTRATION_OBSERVATION_SCHEMA_VERSION,
        "observation_id": uuid.uuid4().hex,
        "run_id": "run-" + uuid.uuid4().hex[:8],
        "event_id": uuid.uuid4().hex,
        "ts": ts or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "node_id": skill_id,
        "execution": "serial",
        "depends_on": [],
        "join_policy": None,
        "state": state,
        "attempt": 1,
        "approval_wait_ms": 0,
        "human_interventions": 0,
        "unobserved_claim_count": unobserved,
        "policy_conflict_count": 0,
        "verification_failure_count": 0,
        "evidence_refs": [f"sha256:{content_sha[:12]}"],
    }
    assert append_orchestration_observation(ws, payload)
    if ledger:
        # What the harness runner writes next to each observation.
        from hyodo.events import (
            AGENT_EVENT_SCHEMA_VERSION,
            append_agent_event,
            unevaluated_policy,
            validate_event,
        )

        ok, _reasons, event = validate_event(
            {
                "schema_version": AGENT_EVENT_SCHEMA_VERSION,
                "event_id": payload["event_id"],
                "run_id": payload["run_id"],
                "step_index": 0,
                "ts": payload["ts"],
                "kind": "tool_call",
                "actor": "agent",
                "tool": {"name": ledger_tool or skill_id, "args_digest": None, "paths": []},
                "policy": unevaluated_policy(),
            }
        )
        assert ok
        assert event is not None
        assert append_agent_event(ws, event)


def test_execution_evidence_is_invalidated_by_new_content(tmp_path: Path) -> None:
    """Gate 11: an execution of old content is not evidence for new content."""
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    mod = _module(tmp_path, "ran")
    rec = factory.add_module(ws, mod)
    old_sha = rec.skills["ran/probe"].content_sha256

    _observe(ws, "ran/probe", old_sha)
    ran = factory.doctor(ws)["axes"]["ran"]["skills"]["ran/probe"]
    assert ran["execution"] == "EXECUTED_PASS"
    assert ran["execution_evidence_source"] == "AGENT_LEDGER_CORROBORATED"

    _skill_md(mod).write_text("---\nname: probe\ndescription: v2\n---\n# v2\n", encoding="utf-8")
    _git(mod, "commit", "-q", "-am", "v2")
    factory.update_module(ws, "ran")
    rep = factory.doctor(ws)
    assert rep["axes"]["ran"]["skills"]["ran/probe"]["execution"] == "STALE_CONTENT"
    assert "execution_evidence_stale:ran/probe" in rep["warnings"]


def test_disclosed_only_is_not_executed(tmp_path: Path) -> None:
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    rec = factory.add_module(ws, _module(tmp_path, "shown"))
    _observe(ws, "shown/probe", rec.skills["shown/probe"].content_sha256, unobserved=1)
    rep = factory.doctor(ws)
    assert rep["axes"]["shown"]["skills"]["shown/probe"]["execution"] == "DISCLOSED_ONLY"


def test_trust_record_is_invalidated_without_doctor_writing(tmp_path: Path) -> None:
    """Gate 11 for verification: a record for other content reads INVALIDATED; doctor stays read-only."""
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    mod = _module(tmp_path, "trusted")
    rec = factory.add_module(ws, mod)
    unit = rec.skills["trusted/probe"]

    sys.path.insert(0, str(FACTORY_DIR))
    from factory.registry import compute_module_tree_digest
    from factory.runner import _default_env_fingerprint, _write_trust_file

    tree = compute_module_tree_digest(mod)[0]
    _write_trust_file(
        ws,
        {
            "skills": {
                "trusted/probe": {
                    "skill_id": "trusted/probe",
                    "trust_stage": "SHADOW",
                    "verifier_status": "PASS",
                    "content_sha256": unit.content_sha256,
                    "module_tree_sha256": tree,
                    "version": rec.version,
                    "module_source_path": rec.source_path,
                    "boundary": unit.boundary.to_dict(),
                    "env_fingerprint": _default_env_fingerprint(),
                }
            }
        },
    )
    skill = factory.doctor(ws)["axes"]["trusted"]["skills"]["trusted/probe"]
    assert skill["trust_stage"] == "SHADOW"
    assert skill["independent_verification"] == "PASS"

    trust_file = ws / ".hyodo" / "factory" / "trust_state.json"
    before = trust_file.read_bytes()
    _skill_md(mod).write_text("---\nname: probe\ndescription: changed\n---\n", encoding="utf-8")
    _git(mod, "commit", "-q", "-am", "change")
    factory.update_module(ws, "trusted")
    skill = factory.doctor(ws)["axes"]["trusted"]["skills"]["trusted/probe"]
    assert skill["independent_verification"] == "INVALIDATED"
    assert skill["trust_stage"] == "VERIFY"
    assert skill["trust_stage_before_invalidation"] == "SHADOW"
    assert "content_sha256_changed" in skill["evidence_invalidated_by"]
    assert trust_file.read_bytes() == before


def test_interrupted_write_leaves_registry_view_out_of_sync(tmp_path: Path) -> None:
    """Gate 6: lock.json and its rendered registry.toml must agree, or doctor degrades."""
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    factory.add_module(ws, _module(tmp_path, "viewed"))
    (ws / ".hyodo" / "factory" / "registry.toml").write_text("# stale\n", encoding="utf-8")
    rep = factory.doctor(ws)
    assert "registry_view_out_of_sync:registry.toml" in rep["problems"]
    assert rep["status"] == "DEGRADED"

    # Recovery: any lifecycle write re-renders the view from lock.json.
    factory.disable_target(ws, "viewed")
    factory.enable_target(ws, "viewed")
    assert factory.doctor(ws)["status"] == "HEALTHY"


def test_verify_upstream_states(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Gate 5: provenance is checked against a network remote, separately from integrity."""
    factory = _load_factory_module()
    ws = _workspace(tmp_path)

    # A local bare repository is the module vouching for itself, never VERIFIED.
    mod = _module(tmp_path, "upstreamed", remote=None)
    bare = tmp_path / "upstream.git"
    _git(tmp_path, "init", "-q", "--bare", str(bare))
    _git(mod, "remote", "add", "origin", str(bare))
    _git(mod, "push", "-q", "origin", "HEAD:refs/heads/main")
    factory.add_module(ws, mod)
    assert factory.main(["--root", str(ws), "verify-upstream", "upstreamed"]) == 2
    assert json.loads(capsys.readouterr().out)["state"] == "LOCAL_REMOTE"

    # Network remote: the ls-remote answer decides. Only the subprocess is faked.
    net = _module(tmp_path, "net")
    factory.add_module(ws, net)
    commit = _git(net, "rev-parse", "HEAD")
    sys.path.insert(0, str(FACTORY_DIR))
    import factory.registry as registry

    seen: dict[str, Any] = {}

    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if "ls-remote" not in argv:
            return subprocess.run(argv, **kwargs)
        seen["argv"], seen["env"], seen["cwd"] = argv, kwargs.get("env"), kwargs.get("cwd")
        out = (
            f"{commit}\trefs/tags/v1^{{}}\n0000000000000000000000000000000000000000\trefs/heads/x\n"
        )
        return subprocess.CompletedProcess(argv, 0, out, "")

    monkeypatch.setenv("GIT_ASKPASS", "/bin/echo")
    monkeypatch.setenv("SSH_ASKPASS", "/bin/echo")
    monkeypatch.setattr(registry.subprocess, "run", fake_run)
    assert factory.main(["--root", str(ws), "verify-upstream", "net"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["state"] == "VERIFIED_AT_REF"
    assert out["matching_refs"] == ["refs/tags/v1"]
    # Review M6: no credential prompt or helper, neutral working directory.
    assert "GIT_ASKPASS" not in seen["env"]
    assert "SSH_ASKPASS" not in seen["env"]
    assert seen["env"]["GIT_TERMINAL_PROMPT"] == "0"
    assert "credential.helper=" in seen["argv"]
    assert "protocol.allow=never" in seen["argv"]
    assert seen["argv"][-2] == "--"
    assert seen["cwd"] == tempfile.gettempdir()

    def tip_moved(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        if "ls-remote" not in argv:
            return subprocess.run(argv, **kwargs)
        return subprocess.CompletedProcess(argv, 0, "1" * 40 + "\trefs/heads/main\n", "")

    monkeypatch.setattr(registry.subprocess, "run", tip_moved)
    assert factory.main(["--root", str(ws), "verify-upstream", "net"]) == 2
    assert json.loads(capsys.readouterr().out)["state"] == "COMMIT_NOT_A_REF_TIP"
    monkeypatch.undo()

    copy = _module(tmp_path, "no-remote", remote=None)
    factory.add_module(ws, copy)
    assert factory.main(["--root", str(ws), "verify-upstream", "no-remote"]) == 2
    assert json.loads(capsys.readouterr().out)["reason"] == "no_recorded_remote"


@pytest.mark.parametrize(
    "hostile", ["--upload-pack=touch {canary}", "ext::sh -c touch {canary}", "fd::0,1"]
)
def test_verify_upstream_refuses_option_or_command_remotes(tmp_path: Path, hostile: str) -> None:
    """A module's git config is untrusted: its remote must not become a git option or command."""
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    canary = tmp_path / "pwned"
    hostile = hostile.format(canary=canary)
    mod = _module(tmp_path, "hostile", remote=None)
    # `git remote add` refuses such URLs; a hostile module can still write its config.
    _git(mod, "config", "remote.origin.url", hostile)
    factory.add_module(ws, mod)
    sys.path.insert(0, str(FACTORY_DIR))
    from factory.registry import load_registry_state, verify_module_upstream

    rec = load_registry_state(ws)["hostile"]
    if rec.origin.get("git_remote_url") != hostile:
        pytest.skip("remote URL was normalized when recorded")
    out = verify_module_upstream(rec)
    assert out["state"] == "UNOBSERVED"
    assert out["reason"] == "remote_url_refused"
    assert not canary.exists()


def test_concurrent_adds_are_serialized_without_lost_updates(tmp_path: Path) -> None:
    """Gate 7 (distinct names) and Gate 3 (same name): one writer at a time, no overwrite."""
    ws = _workspace(tmp_path)
    sources = [_module(tmp_path, f"par{i}") for i in range(6)]
    dup_a = _module(tmp_path / "a", "same")
    dup_b = _module(tmp_path / "b", "same")
    cli = [sys.executable, str(FACTORY_DIR / "hyodo_factory.py"), "--root", str(ws), "add"]
    procs = [
        subprocess.Popen([*cli, str(src)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for src in [*sources, dup_a, dup_b]
    ]
    codes = [p.wait(timeout=120) for p in procs]
    for p in procs:
        assert p.stdout is not None
        assert p.stderr is not None
        p.stdout.close()
        p.stderr.close()

    lock = json.loads((ws / ".hyodo" / "factory" / "lock.json").read_text(encoding="utf-8"))
    assert sorted(lock["modules"]) == sorted([*(f"par{i}" for i in range(6)), "same"])
    assert codes[:6] == [0] * 6
    assert sorted(codes[6:]) == [0, 1]
    assert lock["modules"]["same"]["source_path"] in (str(dup_a), str(dup_b))


def test_new_module_needs_no_central_code_and_removal_leaves_nothing(tmp_path: Path) -> None:
    """Gate 1: a module whose name appears nowhere in the harness runs the full lifecycle."""
    factory = _load_factory_module()
    name = "zq-" + uuid.uuid4().hex[:10]
    central = list(FACTORY_DIR.rglob("*.py"))
    assert not any(name in p.read_text(encoding="utf-8", errors="replace") for p in central)

    ws = _workspace(tmp_path)
    mod = _module(tmp_path, name)
    factory.add_module(ws, mod)
    factory.disable_target(ws, name)
    factory.enable_target(ws, f"{name}/probe")
    _skill_md(mod).write_text("---\nname: probe\ndescription: edited\n---\n", encoding="utf-8")
    _git(mod, "commit", "-q", "-am", "edit")
    edited = factory.doctor(ws)
    assert f"module_tree_drift:{name}" in edited["problems"]
    factory.update_module(ws, name)
    assert factory.doctor(ws)["status"] == "HEALTHY"
    factory.rollback_module(ws, name)
    assert factory.doctor(ws)["axes"][name]["content_integrity"] == "DRIFTED"
    factory.update_module(ws, name)
    factory.remove_module(ws, name)
    rep = factory.doctor(ws)
    assert rep["modules_registered"] == 0
    assert rep["axes"] == {}
    manifest = ws / ".hyodo" / "skills" / "manifest.json"
    if manifest.is_file():
        assert name not in manifest.read_text(encoding="utf-8")


def test_missing_disabled_module_is_not_healthy(tmp_path: Path) -> None:
    """Review F2: a module whose source vanished was never checked, enabled or not."""
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    mod = _module(tmp_path, "gone")
    factory.add_module(ws, mod)
    factory.disable_target(ws, "gone")
    import shutil

    shutil.rmtree(mod)
    rep = factory.doctor(ws)
    assert rep["axes"]["gone"]["install"] == "MISSING"
    assert "module_source_missing:gone" in rep["warnings"]
    assert rep["status"] == "UNOBSERVED"


def test_latest_execution_decides_and_tree_changes_invalidate(tmp_path: Path) -> None:
    """Review F3/F4: a later failure wins; a script change after the run makes the run stale."""
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    mod = _module(tmp_path, "seq")
    rec = factory.add_module(ws, mod)
    sha = rec.skills["seq/probe"].content_sha256
    _observe(ws, "seq/probe", sha, ts="2999-01-01T00:00:00Z")
    _observe(ws, "seq/probe", sha, state="failed", ts="2999-01-01T00:00:01Z")
    skill = factory.doctor(ws)["axes"]["seq"]["skills"]["seq/probe"]
    assert skill["execution"] == "EXECUTED_FAILED"

    _observe(ws, "seq/probe", sha, ts="2999-01-01T00:00:02Z")
    assert factory.doctor(ws)["axes"]["seq"]["skills"]["seq/probe"]["execution"] == "EXECUTED_PASS"

    # The SKILL.md digest is unchanged, but a script was added after a past run.
    ws2 = _workspace(tmp_path / "second")
    mod2 = _module(tmp_path / "second", "tree")
    rec2 = factory.add_module(ws2, mod2)
    _observe(ws2, "tree/probe", rec2.skills["tree/probe"].content_sha256, ts="2000-01-01T00:00:00Z")
    (mod2 / "run.sh").write_text("echo hi\n", encoding="utf-8")
    _git(mod2, "add", ".")
    _git(mod2, "commit", "-q", "-m", "script")
    factory.update_module(ws2, "tree")
    assert factory.doctor(ws2)["axes"]["tree"]["skills"]["tree/probe"]["execution"] == (
        "STALE_CONTENT"
    )


def test_stale_evidence_does_not_degrade_gap_analysis(tmp_path: Path) -> None:
    """Review F5: an updated skill with old evidence is not an environment or syntax defect."""
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    mod = _module(tmp_path, "gap")
    rec = factory.add_module(ws, mod)
    _observe(ws, "gap/probe", rec.skills["gap/probe"].content_sha256)
    _skill_md(mod).write_text("---\nname: probe\ndescription: gap v2\n---\n", encoding="utf-8")
    _git(mod, "commit", "-q", "-am", "v2")
    factory.update_module(ws, "gap")
    assert "execution_evidence_stale:gap/probe" in factory.doctor(ws)["warnings"]
    sys.path.insert(0, str(FACTORY_DIR))
    from factory.router import analyze_capability_gaps

    report = json.dumps(analyze_capability_gaps(ws, "probe skill"), default=str)
    assert "ENVIRONMENT_OR_SYNTAX_DEGRADED" not in report


def test_unreadable_inputs_are_unobserved_not_crashes(tmp_path: Path) -> None:
    """Review F6/F7: bad bytes or a bad host root never crash doctor."""
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    factory.add_module(ws, _module(tmp_path, "bad"))
    hd = ws / ".hyodo"
    (hd / "factory" / "trust_state.json").write_bytes(b"\xff\xfe not utf-8")
    (hd / "orchestration-observations.jsonl").write_bytes(b"\xff\xfe\n")
    not_a_dir = tmp_path / "file-root"
    not_a_dir.write_text("x", encoding="utf-8")
    rep = factory.doctor(ws, host_skill_roots=[not_a_dir, tmp_path / "missing-root"])
    skill = rep["axes"]["bad"]["skills"]["bad/probe"]
    assert skill["trust_stage"] == "UNOBSERVED"
    assert skill["execution"] == "UNOBSERVED"
    assert skill["host_connection"] == "UNOBSERVED"
    assert any(w.startswith("host_root_unreadable:") for w in rep["warnings"])
    assert any(w.startswith("trust_state_unverifiable:") for w in rep["warnings"])


def test_frontmatter_name_cannot_leave_the_host_root(tmp_path: Path) -> None:
    """Review F8: only a single path component is looked up under a host root."""
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    root = tmp_path / "rooted"
    root.mkdir()
    (root / "SKILL.md").write_text("---\nname: ../outside\ndescription: x\n---\n", encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "T")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "init")
    factory.add_module(ws, root)
    host = tmp_path / "host" / "skills"
    host.mkdir(parents=True)
    outside = tmp_path / "host" / "outside"
    outside.mkdir()
    (outside / "SKILL.md").write_bytes((root / "SKILL.md").read_bytes())
    rep = factory.doctor(ws, host_skill_roots=[host])
    for skill in rep["axes"]["rooted"]["skills"].values():
        assert skill["host_observations"] == []
        assert skill["host_connection"] == "ABSENT"


def test_crash_between_state_and_view_is_reported_and_recovers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Gate 6: a write that dies after lock.json but before registry.toml is visible, then repaired."""
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    factory.add_module(ws, _module(tmp_path, "crashy"))
    sys.path.insert(0, str(FACTORY_DIR))
    import factory.registry as registry

    real_write = registry._atomic_write_text

    def dying_write(target: Path, content: str) -> None:
        if target.name == "registry.toml":
            raise OSError("simulated crash after lock.json was replaced")
        real_write(target, content)

    monkeypatch.setattr(registry, "_atomic_write_text", dying_write)
    with pytest.raises(OSError, match="simulated crash"):
        factory.disable_target(ws, "crashy")
    monkeypatch.setattr(registry, "_atomic_write_text", real_write)

    lock = json.loads((ws / ".hyodo" / "factory" / "lock.json").read_text(encoding="utf-8"))
    assert lock["modules"]["crashy"]["enabled"] is False
    rep = factory.doctor(ws)
    assert "registry_view_out_of_sync:registry.toml" in rep["problems"]
    assert rep["status"] == "DEGRADED"

    factory.enable_target(ws, "crashy")
    assert factory.doctor(ws)["status"] == "HEALTHY"


def test_sidecar_only_observation_is_an_uncorroborated_claim(tmp_path: Path) -> None:
    """F12: a row no runner event backs (another host, `hyodo observation record`) is not EXECUTED."""
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    rec = factory.add_module(ws, _module(tmp_path, "claimed"))
    sha = rec.skills["claimed/probe"].content_sha256
    _observe(ws, "claimed/probe", sha, ledger=False)
    rep = factory.doctor(ws)
    skill = rep["axes"]["claimed"]["skills"]["claimed/probe"]
    assert skill["execution"] == "UNCORROBORATED_CLAIM"
    assert skill["execution_evidence_source"] == "UNCORROBORATED_OBSERVATION"
    assert "execution_claim_uncorroborated:claimed/probe" in rep["warnings"]

    # An event for another tool with the same ids does not corroborate this skill.
    _observe(ws, "claimed/probe", sha, ledger_tool="other/tool")
    skill = factory.doctor(ws)["axes"]["claimed"]["skills"]["claimed/probe"]
    assert skill["execution"] == "UNCORROBORATED_CLAIM"


def test_runner_executions_are_corroborated_end_to_end(tmp_path: Path) -> None:
    """The real runner writes both records, so its executions read as corroborated."""
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    factory.add_module(ws, _module(tmp_path, "real"))
    result = factory.execute_modular_run(
        ws,
        run_id="corroborate-01",
        prompt="probe skill",
        skill_commands={"real/probe": [sys.executable, "-c", "print('ok')"]},
    )
    assert result["orchestration_observations_recorded"] >= 1
    skill = factory.doctor(ws)["axes"]["real"]["skills"]["real/probe"]
    assert skill["execution_evidence_source"] == "AGENT_LEDGER_CORROBORATED"
    assert skill["execution"] == "EXECUTED_PASS"


def _append_raw_observation(ws: Path, row: dict[str, Any]) -> None:
    path = ws / ".hyodo" / "orchestration-observations.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")


def test_one_ledger_event_cannot_vouch_for_a_replayed_row(tmp_path: Path) -> None:
    """Review H1: reusing a real run's ids for a forged 'completed' row does not flip FAILED to PASS."""
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    factory.add_module(ws, _module(tmp_path, "rp"))
    factory.execute_modular_run(
        ws,
        run_id="replay-01",
        prompt="probe skill",
        skill_commands={"rp/probe": [sys.executable, "-c", "raise SystemExit(3)"]},
    )
    rows = [
        json.loads(line)
        for line in (ws / ".hyodo" / "orchestration-observations.jsonl").read_text().splitlines()
    ]
    real = next(r for r in rows if r["node_id"] == "rp/probe")
    assert factory.doctor(ws)["axes"]["rp"]["skills"]["rp/probe"]["execution"] == "EXECUTED_FAILED"

    forged = {
        **real,
        "observation_id": uuid.uuid4().hex,
        "state": "completed",
        "verification_failure_count": 0,
    }
    _append_raw_observation(ws, forged)
    skill = factory.doctor(ws)["axes"]["rp"]["skills"]["rp/probe"]
    assert skill["execution"] != "EXECUTED_PASS"
    assert skill["execution"] == "UNCORROBORATED_CLAIM"


def test_malformed_rows_and_deep_json_do_not_crash(tmp_path: Path) -> None:
    """Review H2: unhashable ids or deeply nested JSON make an axis UNOBSERVED, never raise."""
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    rec = factory.add_module(ws, _module(tmp_path, "mal"))
    sha = rec.skills["mal/probe"].content_sha256
    _append_raw_observation(
        ws,
        {
            "node_id": "mal/probe",
            "event_id": {"a": 1},
            "run_id": ["x"],
            "ts": "2999-01-01T00:00:00Z",
            "state": "completed",
            "evidence_refs": [f"sha256:{sha[:12]}"],
        },
    )
    rep = factory.doctor(ws)
    assert rep["axes"]["mal"]["skills"]["mal/probe"]["execution"] == "UNCORROBORATED_CLAIM"
    sys.path.insert(0, str(FACTORY_DIR))
    from factory.router import analyze_capability_gaps

    analyze_capability_gaps(ws, "probe skill")

    deep = "[" * 200000
    hd = ws / ".hyodo"
    (hd / "orchestration-observations.jsonl").write_text(deep + "\n", encoding="utf-8")
    (hd / "agent-events.jsonl").write_text(deep + "\n", encoding="utf-8")
    (hd / "factory" / "trust_state.json").write_text(deep, encoding="utf-8")
    skill = factory.doctor(ws)["axes"]["mal"]["skills"]["mal/probe"]
    assert skill["trust_stage"] == "UNOBSERVED"


def test_each_host_root_is_judged_and_shared_names_are_shadowed(tmp_path: Path) -> None:
    """Review M3/M4: a drifted second root is drift; another module's exact copy is SHADOWED."""
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    mod_a = _module(tmp_path, "moda")
    factory.add_module(ws, mod_a)
    good, bad = tmp_path / "good", tmp_path / "bad"
    for root, content in ((good, _skill_md(mod_a).read_bytes()), (bad, b"# tampered\n")):
        (root / "probe").mkdir(parents=True)
        (root / "probe" / "SKILL.md").write_bytes(content)
    rep = factory.doctor(ws, host_skill_roots=[good, bad])
    assert rep["axes"]["moda"]["skills"]["moda/probe"]["host_connection"] == "DRIFTED"
    assert f"host_copy_drift:moda/probe|{bad}" in rep["problems"]
    assert rep["status"] == "DEGRADED"

    factory.add_module(ws, _module(tmp_path, "modb", body="# B\n"))
    rep = factory.doctor(ws, host_skill_roots=[good])
    assert rep["axes"]["moda"]["skills"]["moda/probe"]["host_connection"] == "CONNECTED"
    b_skill = rep["axes"]["modb"]["skills"]["modb/probe"]
    assert b_skill["host_connection"] == "SHADOWED"
    assert b_skill["host_observations"][0]["shadowed_by"] == "moda/probe"
    assert "host_copy_shadowed:modb/probe" in rep["warnings"]
    assert not any(p.startswith("host_copy_drift:modb/") for p in rep["problems"])


def test_recorded_commit_needs_tracked_content_and_a_remote(tmp_path: Path) -> None:
    """Review M5: an ignored module or a local-only commit is not a recorded upstream."""
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    repo = tmp_path / "host-repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "T")
    (repo / ".gitignore").write_text("vendored/\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "init")
    _git(repo, "remote", "add", "origin", "https://example.com/host-repo.git")
    ignored = _module(repo / "vendored", "ign", git=False)
    factory.add_module(ws, ignored)
    local = _module(tmp_path, "localonly", remote=None)
    factory.add_module(ws, local)
    rep = factory.doctor(ws)
    assert rep["axes"]["ign"]["recorded_upstream"] == "NOT_IN_COMMIT"
    assert rep["axes"]["localonly"]["recorded_upstream"] == "LOCAL_COMMIT_ONLY"
    assert rep["status"] == "UNOBSERVED"


def test_doctor_does_not_run_the_modules_fsmonitor(tmp_path: Path) -> None:
    """Review L10: a module's own .git/config hook must not run during doctor."""
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    mod = _module(tmp_path, "hook")
    canary = tmp_path / "fsmonitor-ran"
    script = tmp_path / "fsmon.sh"
    script.write_text(f"#!/bin/sh\ntouch {canary}\n", encoding="utf-8")
    script.chmod(0o755)
    factory.add_module(ws, mod)
    _git(mod, "config", "core.fsmonitor", str(script))
    factory.doctor(ws)
    assert not canary.exists()


def test_trust_axis_sees_environment_and_boundary_drift(tmp_path: Path) -> None:
    """Review M9: doctor applies the runner's drift checks, read-only."""
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    mod = _module(tmp_path, "envd")
    rec = factory.add_module(ws, mod)
    unit = rec.skills["envd/probe"]
    sys.path.insert(0, str(FACTORY_DIR))
    from factory.registry import compute_module_tree_digest
    from factory.runner import _write_trust_file

    _write_trust_file(
        ws,
        {
            "skills": {
                "envd/probe": {
                    "skill_id": "envd/probe",
                    "trust_stage": "AUTO_RUN",
                    "verifier_status": "PASS",
                    "content_sha256": unit.content_sha256,
                    "module_tree_sha256": compute_module_tree_digest(mod)[0],
                    "version": rec.version,
                    "module_source_path": rec.source_path,
                    "boundary": unit.boundary.to_dict(),
                    "env_fingerprint": "some-other-machine",
                }
            }
        },
    )
    skill = factory.doctor(ws)["axes"]["envd"]["skills"]["envd/probe"]
    assert skill["trust_stage"] == "VERIFY"
    assert "environment_fingerprint_changed" in skill["evidence_invalidated_by"]
