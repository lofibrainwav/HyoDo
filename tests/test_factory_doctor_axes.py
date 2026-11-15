"""Factory doctor reports each evidence axis separately.

Integrity is not health, registration is not connection, an old execution is
not evidence for new content, and nothing here is "helped". These tests pin
that separation and the read-only supply-chain check (`verify-upstream`).
"""

from __future__ import annotations

import json
import subprocess
import sys
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
    base: Path, name: str, body: str = "# Probe\n\nRead-only probe skill.\n", *, git: bool = True
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
    assert "host_copy_drift:hosted/probe" in rep["problems"]
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


def test_execution_evidence_is_invalidated_by_new_content(tmp_path: Path) -> None:
    """Gate 11: an execution of old content is not evidence for new content."""
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    mod = _module(tmp_path, "ran")
    rec = factory.add_module(ws, mod)
    old_sha = rec.skills["ran/probe"].content_sha256

    _observe(ws, "ran/probe", old_sha)
    assert factory.doctor(ws)["axes"]["ran"]["skills"]["ran/probe"]["execution"] == "EXECUTED_PASS"

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
    from factory.runner import _write_trust_file

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


def test_verify_upstream_against_a_local_remote(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Gate 5: provenance is checked against the remote, separately from content integrity."""
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    mod = _module(tmp_path, "upstreamed")
    bare = tmp_path / "upstream.git"
    _git(tmp_path, "init", "-q", "--bare", str(bare))
    _git(mod, "remote", "add", "origin", str(bare))
    _git(mod, "push", "-q", "origin", "HEAD:refs/heads/main")
    factory.add_module(ws, mod)

    assert factory.main(["--root", str(ws), "verify-upstream", "upstreamed"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["state"] == "VERIFIED_AT_REF"
    assert out["matching_refs"] == ["refs/heads/main"]

    # A local commit that was never pushed is not a remote ref tip.
    _skill_md(mod).write_text("---\nname: probe\ndescription: local\n---\n", encoding="utf-8")
    _git(mod, "commit", "-q", "-am", "local only")
    factory.update_module(ws, "upstreamed")
    assert factory.main(["--root", str(ws), "verify-upstream", "upstreamed"]) == 2
    assert json.loads(capsys.readouterr().out)["state"] == "COMMIT_NOT_A_REF_TIP"

    copy = _module(tmp_path, "no-remote")
    factory.add_module(ws, copy)
    assert factory.main(["--root", str(ws), "verify-upstream", "no-remote"]) == 2
    assert json.loads(capsys.readouterr().out)["reason"] == "no_recorded_remote"


@pytest.mark.parametrize("hostile", ["--upload-pack=touch {canary}", "ext::sh -c touch {canary}"])
def test_verify_upstream_refuses_option_or_command_remotes(tmp_path: Path, hostile: str) -> None:
    """A module's git config is untrusted: its remote must not become a git option or command."""
    factory = _load_factory_module()
    ws = _workspace(tmp_path)
    canary = tmp_path / "pwned"
    hostile = hostile.format(canary=canary)
    mod = _module(tmp_path, "hostile")
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
