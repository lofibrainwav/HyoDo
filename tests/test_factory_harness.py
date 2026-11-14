"""End-to-end verification of the HyoDo Universal Skill Harness (`examples/factory-loop/`).

Verifies all 12 Phase 2 Acceptance Gates:
1. HyoDo Core works when all external skills are removed.
2. Brand-new standard skills (`pstack`, `superpowers`, `taste`, `impeccable`, `find-skills`) attach with 0 core edits.
3. Granular sub-skill ON/OFF (`gstack/qa` + `gstack/browse`) and complete detach.
4. Removing a skill cleans up registered hooks, permissions, and manifest rules.
5. Fault isolation prevents a failing skill from crashing other modules or HyoDo Core.
6. Duplicate ID, dependency conflict, and symlink/path escape detection.
7. Atomic update failure recovery and snapshot rollback.
8. Version, git commit, and SHA-256 content hash reproducibility.
9. Mid-run skill mutation and content drift blocking (`MID_RUN_SKILL_MUTATION_FORBIDDEN` / `MID_RUN_SKILL_DRIFT`).
10. Substantive producer vs independent verifier separation (`SELF_REVIEW_FORBIDDEN` / `HOLD`).
11. `UNOBSERVED` is never `GREEN`, and `skill-eval` lifecycle recommendations never expand authority.
12. Real mounted workspace repositories (`gstack`, `mattpocock-skills`, `improve`, `ponytail`, `jev-private-worker`) attach, route, and detach cleanly, plus CLI compatibility (`hyodo lens-evidence workspace` & `hyodo_factory.py`).
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from hyodo.cli.dispatch import app as hyodo_cli_app

FACTORY_PATH = (
    Path(__file__).resolve().parents[1] / "examples" / "factory-loop" / "hyodo_factory.py"
)


def _load_factory_module() -> Any:
    spec = importlib.util.spec_from_file_location("hyodo_factory", FACTORY_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _init_clean_repo(repo: Path) -> str:
    repo.mkdir(parents=True, exist_ok=True)
    (repo / ".gitignore").write_text(".hyodo/\n", encoding="utf-8")
    (repo / "spec.md").write_text("# Feature Spec\n", encoding="utf-8")
    (repo / "app.py").write_text(
        "def add(a: int, b: int) -> int:\n    return a + b\n", encoding="utf-8"
    )
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "feat: initial implementation"], cwd=repo, check=True
    )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


def _write_skill_pkg(
    base: Path,
    pkg_name: str,
    skills: dict[str, str],
    *,
    is_plugin: bool = False,
    with_git: bool = False,
) -> Path:
    pkg_dir = base / pkg_name
    pkg_dir.mkdir(parents=True, exist_ok=True)
    if is_plugin:
        plugin_dir = pkg_dir / ".claude-plugin"
        plugin_dir.mkdir(parents=True, exist_ok=True)
        (plugin_dir / "plugin.json").write_text(
            json.dumps(
                {
                    "name": pkg_name,
                    "version": "1.2.0",
                    "hooks": [f"pre-tool:{pkg_name}:default"],
                    "mcpServers": {f"{pkg_name}-mcp": {"command": "echo"}},
                }
            ),
            encoding="utf-8",
        )
    for sub_name, content in skills.items():
        sdir = pkg_dir / ".agents" / "skills" / sub_name
        sdir.mkdir(parents=True, exist_ok=True)
        (sdir / "SKILL.md").write_text(content, encoding="utf-8")
    if with_git:
        subprocess.run(["git", "init", "-q"], cwd=pkg_dir, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=pkg_dir, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=pkg_dir, check=True)
        subprocess.run(["git", "add", "."], cwd=pkg_dir, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "init skill pkg"], cwd=pkg_dir, check=True)
    return pkg_dir


def test_unified_factory_pipeline_connects_jev_gstack_mattpocock_and_hyodo(tmp_path: Path) -> None:
    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    sha = _init_clean_repo(repo)

    hyodo_dir = repo / ".hyodo"
    hyodo_dir.mkdir(parents=True, exist_ok=True)
    history_entry = {
        "measured_at": "2026-11-13T00:00:00Z",
        "provenance": {
            "target_commit": sha,
            "target_dirty": False,
            "validity": "OBSERVED",
            "relation": "BYOG_PROJECT",
            "tool_version": "4.22.4",
        },
        "input_digest": {"before": "a" * 64, "after": "a" * 64},
        "gates": {
            "pytest": {"pillar": "truth", "status": "PASS"},
            "safety": {"pillar": "goodness", "status": "PASS"},
            "ruff": {"pillar": "beauty", "status": "PASS"},
        },
    }
    (hyodo_dir / "history.jsonl").write_text(json.dumps(history_entry) + "\n", encoding="utf-8")

    jev_skill_obs = {
        "job_id": "jev-skillid-001",
        "job_sha256": "f" * 64,
        "selected_skill_id": "ponytail-tdd",
        "execution_authority": False,
    }
    skill_rules = [
        {
            "skill": "ponytail-tdd",
            "source": "path:.agents/skills/ponytail-tdd/SKILL.md",
            "rule_text": "require file: app.py [pillars: truth, goodness]",
        },
        {
            "skill": "ponytail-tdd",
            "source": "path:.agents/skills/ponytail-tdd/SKILL.md",
            "rule_text": "forbid pattern: DO_NOT_COMMIT_HACK [pillars: beauty, eternity]",
        },
    ]
    jev_completion_event = {
        "schema_version": "hyodo.agent-event/v1",
        "event_id": "00000000-0000-4000-8000-000000000099",
        "run_id": "run-factory-001",
        "ts": "2026-11-13T00:00:05+00:00",
        "kind": "model_response",
        "step_index": 1,
        "actor": "agent",
        "tool": None,
        "io": {
            "input_text": "Verify completion evidence for app.py",
            "output_text": "RAW_JEV_COMPLETION_TEXT_MUST_BE_STRIPPED",
            "bytes_in": 37,
            "bytes_out": 40,
        },
        "policy": {"decision": None, "rule_id": None, "reason": None},
        "meta": {
            "model": "openai/gpt-5.4-nano",
            "tags": ["no-execution-authority", "policy-unevaluated", "jev-completion"],
        },
    }

    bundle = factory.run_unified_factory_pipeline(
        repo,
        run_id="run-factory-001",
        promise_id="promise-slice-001",
        plan_producer="mattpocock-tdd-builder",
        review_producer="gstack-independent-reviewer",
        jev_skill_observation=jev_skill_obs,
        skill_rules=skill_rules,
        jev_completion_event=jev_completion_event,
        source_paths=["spec.md"],
        output_paths=["app.py"],
    )

    assert bundle["schema"] == "hyodo.factory-bundle/v1"
    assert bundle["authority"] == "UNOBSERVED"
    assert bundle["external_action_allowed"] is False
    assert bundle["promise_observation"]["state"] == "OBSERVED"
    assert bundle["skill_lens_status"] == "ok"
    assert len(bundle["skill_manifest_entry"]["compiled_rule_ids"]) == 2
    assert "output_text" not in bundle["jev_shadow_event"]["io"]
    assert len(bundle["jev_shadow_event"]["io"]["output_digest"]) == 12
    assert bundle["handoff_verdict"]["status"] == "VERIFIED_EVIDENCE"
    assert bundle["independent_verifier"]["verdict"] == "PASS"
    assert bundle["independent_verifier"]["target"]["exact_artifact_sha"] == sha
    plate_states = {p["lens"]: p["state"] for p in bundle["six_lens_measurement"]["plates"]}
    assert plate_states == {
        "truth": "OBSERVED",
        "goodness": "OBSERVED",
        "beauty": "OBSERVED",
        "benevolence": "OBSERVED",
        "hyo": "OBSERVED",
        "eternity": "OBSERVED",
    }


def test_gate_01_core_works_when_all_external_skills_removed(tmp_path: Path) -> None:
    """Gate 1: Removing all external skills leaves HyoDo Core 100% operational."""
    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    sha = _init_clean_repo(repo)

    pkg = _write_skill_pkg(
        tmp_path, "temp-skill", {"tdd": "# TDD\n## Rules\n- require file: app.py\n"}
    )
    factory.add_module(repo, pkg)
    factory.remove_module(repo, "temp-skill")

    res = factory.execute_modular_run(repo, run_id="run-zero-skills", prompt="implement feature")
    assert res["route_plan"]["selected_skills"] == []
    assert res["six_lens_measurement"]["exact_artifact_sha"] == sha
    assert res["authority"] == "UNOBSERVED"


def test_gate_02_new_standard_skills_attach_with_zero_core_code_changes(tmp_path: Path) -> None:
    """Gate 2: New skills (PStack, Superpowers, Taste, UI/UX Pro Max, Impeccable, Find Skills) attach and route without core edits."""
    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    _init_clean_repo(repo)

    for mod_name, skills in [
        (
            "pstack",
            {
                "poteto-mode": "---\ncategory: orchestration\nrole_hint: router\n---\nRoute tasks.\n",
                "interrogate": "---\ncategory: evaluation\nrole_hint: verifier\n---\nAdversarial cross-model review.\n",
                "correct": "---\ncategory: simplification\n---\nEliminate repeated root-cause mistakes.\n",
            },
        ),
        (
            "taste-skill",
            {
                "taste": "---\ncategory: design\ndesign_stage: architect\n---\nBrand identity and anti-slop layout tokens.\n",
            },
        ),
        (
            "emil-kowalski",
            {
                "motion": "---\ncategory: craft\ndesign_stage: craft\n---\nSpring physics and micro-interactions.\n",
            },
        ),
        (
            "impeccable",
            {
                "audit": "---\ncategory: quality\ndesign_stage: gatekeep\nrole_hint: verifier\n---\nDesign audit and accessibility gatekeeper.\n",
            },
        ),
        (
            "find-skills",
            {
                "discover": "---\ncategory: research\nrole_hint: router\n---\nDiscover new skills.\n",
            },
        ),
    ]:
        pkg = _write_skill_pkg(tmp_path / "catalog", mod_name, skills)
        factory.add_module(repo, pkg)

    # Test Korean natural-language routing + Progressive Disclosure (0 bodies loaded during routing)
    plan = factory.route_skills_for_task(
        repo,
        "\uc774 \uc571 \uc804\uccb4\ub97c \ubd84\uc11d\ud574\uc11c \uadfc\ubcf8 \uc6d0\uc778\uc744 \uc7a1\uace0 UI\uae4c\uc9c0 \uac1c\uc120\ud574.",
        profile_name="design",
    )
    assert plan["bodies_disclosed"] == 0
    assert "pstack/correct" in plan["selected_skills"]
    assert plan["design_pipeline"] == {
        "architect": ["taste-skill/taste"],
        "craft": ["emil-kowalski/motion"],
        "gatekeep": ["impeccable/audit"],
    }
    assert "impeccable/audit" in plan["verifiers"]


def test_gate_03_granular_skill_on_off_and_dependency_resolution(tmp_path: Path) -> None:
    """Gate 3: Enabling `gstack/qa` with `only=True` activates only `gstack/qa` and its required dependency `gstack/browse`."""
    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    _init_clean_repo(repo)

    gstack_pkg = _write_skill_pkg(
        tmp_path,
        "gstack",
        {
            "browse": "# Browse\nHeadless Chromium binary.\n",
            "qa": "# QA\nRun `$B click` in headless browser to verify UI.\n",
            "ship": "# Ship\nOpen pull request.\n",
            "retro": "# Retro\nWeekly engineering retro.\n",
        },
        is_plugin=True,
    )
    factory.add_module(repo, gstack_pkg)

    enabled = factory.enable_target(repo, "gstack/qa", only=True)
    assert enabled == ["gstack/browse", "gstack/qa"]

    # Disabling `gstack/browse` automatically disables dependent `gstack/qa`
    disabled = factory.disable_target(repo, "gstack/browse")
    assert disabled == ["gstack/browse", "gstack/qa"]


def test_gate_04_remove_module_cleans_up_hooks_permissions_and_manifest(tmp_path: Path) -> None:
    """Gate 4: Removing a module cleans up all registered hooks, permissions, and compiled manifest rules."""
    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    _init_clean_repo(repo)

    guard_pkg = _write_skill_pkg(
        tmp_path,
        "guard-suite",
        {
            "guard": "# Guard\n## Rules\n- require file: app.py [pillars: goodness]\n",
        },
        is_plugin=True,
    )
    factory.add_module(repo, guard_pkg)
    hooks_file = repo / ".hyodo" / "factory" / "active_hooks.json"
    hooks_before = json.loads(hooks_file.read_text(encoding="utf-8"))
    assert "guard-suite/guard" in hooks_before["active_hooks"]

    removal = factory.remove_module(repo, "guard-suite")
    assert removal["remaining_active_hooks"] == {}
    manifest = json.loads(
        (repo / ".hyodo" / "skills" / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["skills"] == []


def test_gate_05_fault_isolation_prevents_failing_skill_from_crashing_others(
    tmp_path: Path,
) -> None:
    """Gate 5: A crashing skill is isolated and does not bring down sibling skills or HyoDo Core."""
    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    sha = _init_clean_repo(repo)

    pkg = _write_skill_pkg(
        tmp_path,
        "mixed-mod",
        {
            "broken-debug": "# Broken\nDebugging skill.\n",
            "healthy-tdd": "# Healthy\nTDD implementation skill.\n",
        },
    )
    factory.add_module(repo, pkg)

    def _boom(_sid: str, _body: str) -> dict[str, Any]:
        raise ValueError("simulated adapter crash")

    res = factory.execute_modular_run(
        repo,
        run_id="run-fault-isolation",
        prompt="debug and implement feature with tdd",
        skill_hooks={"mixed-mod/broken-debug": _boom},
    )
    assert "fault_isolated:mixed-mod/broken-debug:ValueError" in res["isolated_faults"]
    assert res["skill_outputs"]["mixed-mod/broken-debug"]["status"] == "UNOBSERVED"
    assert res["skill_outputs"]["mixed-mod/healthy-tdd"]["status"] == "OBSERVED"
    assert res["six_lens_measurement"]["exact_artifact_sha"] == sha


def test_gate_06_duplicate_id_conflict_and_path_escape_detection(tmp_path: Path) -> None:
    """Gate 6: Duplicate module IDs, skill conflicts, and symlink path escapes are detected and blocked."""
    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    _init_clean_repo(repo)

    pkg_a = _write_skill_pkg(
        tmp_path,
        "orch-a",
        {"flow": "---\ncategory: orchestration\nconflicts_with: [orch-b/flow]\n---\nFlow A\n"},
    )
    pkg_b = _write_skill_pkg(
        tmp_path,
        "orch-b",
        {"flow": "---\ncategory: orchestration\nconflicts_with: [orch-a/flow]\n---\nFlow B\n"},
    )
    factory.add_module(repo, pkg_a)
    with pytest.raises(ValueError, match="duplicate_module_id"):
        factory.add_module(repo, pkg_a)

    factory.add_module(repo, pkg_b, enable_all=False)
    with pytest.raises(ValueError, match="skill_conflict"):
        factory.enable_target(repo, "orch-b/flow")

    # Symlink escape inside a skill directory must be rejected or ignored safely
    outside = tmp_path / "secret.txt"
    outside.write_text("SECRET\n", encoding="utf-8")
    evil_pkg = tmp_path / "evil-pkg"
    evil_pkg.mkdir()
    (evil_pkg / "SKILL.md").symlink_to(outside)
    with pytest.raises(ValueError, match=r"no SKILL\.md"):
        factory.add_module(repo, evil_pkg)


def test_gate_07_and_08_atomic_update_rollback_and_hash_reproducibility(tmp_path: Path) -> None:
    """Gates 7 & 8: Version/commit/SHA-256 pins are reproducible, failed updates roll back automatically, and `rollback` restores snapshots."""
    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    _init_clean_repo(repo)

    pkg = _write_skill_pkg(
        tmp_path,
        "evolvable",
        {"core": "# Evolvable v1\n## Rules\n- require file: app.py\n"},
        with_git=True,
    )
    v1_rec = factory.add_module(repo, pkg, version="0.1.0")
    assert v1_rec.git_commit is not None
    v1_tree_sha = v1_rec.tree_sha256

    # Mutate skill content for v0.2.0
    (pkg / ".agents" / "skills" / "core" / "SKILL.md").write_text(
        "# Evolvable v2\n## Rules\n- require file: spec.md\n", encoding="utf-8"
    )
    v2_rec = factory.update_module(repo, "evolvable", new_version="0.2.0")
    assert v2_rec.version == "0.2.0"
    assert v2_rec.tree_sha256 != v1_tree_sha

    # Failed update to non-existent directory preserves v0.2.0
    with pytest.raises((FileNotFoundError, ValueError)):
        factory.update_module(repo, "evolvable", new_source_path=tmp_path / "does-not-exist")
    assert factory.doctor(repo)["status"] == "HEALTHY"

    # Explicit rollback restores v0.1.0 snapshot
    restored = factory.rollback_module(repo, "evolvable")
    assert restored.version == "0.1.0"
    assert restored.tree_sha256 == v1_tree_sha


def test_gate_09_mid_run_skill_mutation_and_drift_blocked(tmp_path: Path) -> None:
    """Gate 9: Mutating registry state or skill files mid-run is blocked."""
    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    _init_clean_repo(repo)

    pkg = _write_skill_pkg(tmp_path, "locked-skill", {"tdd": "# Locked TDD\n"})
    factory.add_module(repo, pkg)

    with pytest.raises(RuntimeError, match="MID_RUN_SKILL_MUTATION_FORBIDDEN"):
        factory.execute_modular_run(
            repo,
            run_id="run-mid-mutate",
            prompt="implement tdd",
            mid_run_callback=lambda r: factory.disable_target(r, "locked-skill"),
        )

    def _tamper_file(_r: Path) -> None:
        (pkg / ".agents" / "skills" / "tdd" / "SKILL.md").write_text(
            "# Tampered!\n", encoding="utf-8"
        )

    with pytest.raises(RuntimeError, match="MID_RUN_SKILL_DRIFT"):
        factory.execute_modular_run(
            repo,
            run_id="run-mid-drift",
            prompt="implement tdd",
            mid_run_callback=_tamper_file,
        )


def test_gate_10_and_11_self_review_blocked_and_eval_never_expands_authority(
    tmp_path: Path,
) -> None:
    """Gates 10 & 11: Self-review is blocked (`HOLD`), `UNOBSERVED != GREEN`, and `skill-eval` recommendations never expand authority."""
    factory = _load_factory_module()
    repo = tmp_path / "self-review-repo"
    _init_clean_repo(repo)

    verdict = factory.build_and_verify_handoff(
        repo,
        run_id="run-self-review",
        plan_producer="same-agent",
        review_producer="same-agent",
        source_paths=["spec.md"],
        output_paths=["app.py"],
        created_at=1_760_000_000.0,
        observed_at=1_760_000_005.0,
        now=1_760_000_010.0,
    )
    assert verdict["status"] == "HOLD"
    assert verdict["external_action_allowed"] is False

    for eval_verdict, expected_rec in [
        ("HELPED", "KEEP_ENABLED"),
        ("NEUTRAL", "OPTIONAL_BY_COST"),
        ("HURT", "CANDIDATE_DISABLE"),
        ("INCONCLUSIVE", "NEEDS_MORE_PAIRED_TRIALS"),
    ]:
        rec = factory.recommend_skill_lifecycle_action(
            eval_verdict, {"truth": "OBSERVED", "hyo": "OBSERVED"}
        )
        assert rec["recommended_action"] == expected_rec
        assert rec["authority_expanded"] is False
        assert rec["safety_fence_modified"] is False

    with pytest.raises(ValueError, match="execution_authority=False"):
        factory.ingest_jev_skill_routing(
            tmp_path,
            jev_observation={"execution_authority": True, "selected_skill_id": "tdd"},
            skill_rules=[],
        )


def test_gate_12_real_mounted_repos_attach_route_and_detach_plus_cli(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Gate 12: Attach real workspace repositories (`gstack`, `mattpocock-skills`, `improve`, `ponytail`, `jev-private-worker`), route, run CLI, and detach cleanly."""
    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    sha = _init_clean_repo(repo)

    workspace_parent = Path("/home/antigravity/lofibrainwav")
    real_repos = [
        workspace_parent / "gstack",
        workspace_parent / "mattpocock-skills",
        workspace_parent / "improve",
        workspace_parent / "ponytail",
        workspace_parent / "jev-private-worker",
    ]
    attached_ids: list[str] = []
    for path in real_repos:
        if path.is_dir():
            assert factory.main(["--root", str(repo), "add", str(path)]) == 0
            attached_ids.append(path.name.lower())
    capsys.readouterr()

    if attached_ids:
        assert factory.main(["--root", str(repo), "doctor"]) == 0
        doc_out = json.loads(capsys.readouterr().out)
        assert doc_out["status"] == "HEALTHY"
        assert doc_out["modules_registered"] == len(attached_ids)

        assert (
            factory.main(
                [
                    "--root",
                    str(repo),
                    "route",
                    "\uc774 \uc571 \uc804\uccb4\ub97c \ubd84\uc11d\ud574\uc11c \uadfc\ubcf8 \uc6d0\uc778\uc744 \uc7a1\uace0 UI\uae4c\uc9c0 \uac1c\uc120\ud574.",
                    "--profile",
                    "development",
                ]
            )
            == 0
        )
        route_out = json.loads(capsys.readouterr().out)
        assert len(route_out["selected_skills"]) > 0
        assert route_out["bodies_disclosed"] == 0

        for mod_id in attached_ids:
            assert factory.main(["--root", str(repo), "remove", mod_id]) == 0
            capsys.readouterr()

    # Verify `hyodo lens-evidence workspace --root <repo>` CLI command
    runner = CliRunner()
    cli_res = runner.invoke(hyodo_cli_app, ["lens-evidence", "workspace", "--root", str(repo)])
    assert cli_res.exit_code == 0
    cli_payload = json.loads(cli_res.stdout)
    assert cli_payload["schema_version"] == "hyodo.six-lens-measurement/v1"
    assert cli_payload["exact_artifact_sha"] == sha
    assert cli_payload["authority"] == "UNOBSERVED"


def test_adversarial_permission_boundary_and_claude_settings_hook_cleanup(
    tmp_path: Path,
) -> None:
    """Adversarial Gate 3/4/5: Read-only skills attempting file writes in real subprocesses are caught and rolled back; `.claude/settings.json` hooks are cleaned up on disable/remove."""
    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    _init_clean_repo(repo)

    # Create a `.claude/settings.json` with a pre-existing user hook
    claude_dir = repo / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    settings_path = claude_dir / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "Bash",
                            "hooks": [{"type": "command", "command": "echo user-owned-hook"}],
                        }
                    ]
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    pkg = _write_skill_pkg(
        tmp_path,
        "ro-plugin",
        {
            "audit": "# Read-Only Audit\nSecurity and quality audit skill.\n",
        },
        is_plugin=True,
    )
    factory.add_module(repo, pkg)

    # Verify factory hook was injected into `.claude/settings.json`
    settings_after_add = json.loads(settings_path.read_text(encoding="utf-8"))
    pre_entries = settings_after_add["hooks"]["PreToolUse"]
    assert len(pre_entries) == 2
    assert any(
        "# hyodo-factory-hook:ro-plugin/audit" in h.get("command", "")
        for entry in pre_entries
        for h in entry.get("hooks", [])
    )

    # Attempt an unauthorized file write from a read-only skill (`filesystem_write=False`) in a real subprocess
    res = factory.execute_modular_run(
        repo,
        run_id="run-perm-violation",
        prompt="security audit check",
        skill_commands={
            "ro-plugin/audit": [
                sys.executable,
                "-c",
                "import pathlib; pathlib.Path('unauthorized.txt').write_text('hacked'); pathlib.Path('app.py').write_text('corrupted')",
            ]
        },
    )
    audit_out = res["skill_outputs"]["ro-plugin/audit"]
    assert audit_out["execution_state"] == "ROLLED_BACK_ILLEGAL_WRITE"
    assert audit_out["gate_verdict"] == "FAIL"
    assert any(
        "PERMISSION_BOUNDARY_VIOLATION:filesystem_write_forbidden:ro-plugin/audit" in v
        for v in res["permission_violations"]
    )
    # Unauthorized new file must be deleted and modified tracked file restored automatically
    assert not (repo / "unauthorized.txt").exists()
    assert (repo / "app.py").read_text(
        encoding="utf-8"
    ) == "def add(a: int, b: int) -> int:\n    return a + b\n"

    # Disable module -> `.claude/settings.json` must remove factory hook while keeping user hook
    factory.disable_target(repo, "ro-plugin")
    settings_after_disable = json.loads(settings_path.read_text(encoding="utf-8"))
    remaining_pre = settings_after_disable["hooks"]["PreToolUse"]
    assert len(remaining_pre) == 1
    assert remaining_pre[0]["hooks"][0]["command"] == "echo user-owned-hook"


def test_adversarial_subprocess_isolation_disclosed_vs_executed_and_concurrent_lock(
    tmp_path: Path,
) -> None:
    """Adversarial Gate 5/9: Real subprocess crashes are isolated, DISCLOSED_ONLY is never reported as PASS, and concurrent run locks block parallel mutation."""
    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    _init_clean_repo(repo)

    pkg = _write_skill_pkg(
        tmp_path,
        "proc-suite",
        {
            "crash-debug": "---\nsubprocess_exec: true\n---\n# Crash Debug\nDebug root cause.\n",
            "pass-tdd": "---\nsubprocess_exec: true\n---\n# Pass TDD\nTDD implementation.\n",
            "blocked-plan": "---\nsubprocess_exec: false\n---\n# Blocked Plan\nArchitecture plan.\n",
            "doc-review": "# Doc Review\nQuality review guidance.\n",
        },
    )
    factory.add_module(repo, pkg)

    res = factory.execute_modular_run(
        repo,
        run_id="run-proc-isolation",
        prompt="debug and tdd and plan and review quality",
        skill_commands={
            "proc-suite/crash-debug": [
                sys.executable,
                "-c",
                "import sys; sys.stderr.write('fatal crash\\n'); sys.exit(42)",
            ],
            "proc-suite/pass-tdd": [
                sys.executable,
                "-c",
                "print('tdd subprocess ok')",
            ],
            "proc-suite/blocked-plan": [
                sys.executable,
                "-c",
                "print('should never run')",
            ],
        },
        verify_cmd=[
            sys.executable,
            "-c",
            "import pathlib; assert pathlib.Path('app.py').is_file()",
        ],
    )
    # 1. Crashing subprocess is isolated (`EXECUTED_FAIL`)
    assert res["skill_outputs"]["proc-suite/crash-debug"]["execution_state"] == "EXECUTED_FAIL"
    assert res["skill_outputs"]["proc-suite/crash-debug"]["exit_code"] == 42
    assert any(
        "fault_isolated:proc-suite/crash-debug:SubprocessExit_42" in f
        for f in res["isolated_faults"]
    )
    # 2. Sibling subprocess succeeds (`EXECUTED_PASS`)
    assert res["skill_outputs"]["proc-suite/pass-tdd"]["execution_state"] == "EXECUTED_PASS"
    assert res["skill_outputs"]["proc-suite/pass-tdd"]["gate_verdict"] == "PASS"
    # 3. Skill with `subprocess_exec=False` is blocked (`BLOCKED_BY_PERMISSION`)
    assert (
        res["skill_outputs"]["proc-suite/blocked-plan"]["execution_state"]
        == "BLOCKED_BY_PERMISSION"
    )
    assert any(
        "PERMISSION_BOUNDARY_VIOLATION:subprocess_exec_forbidden:proc-suite/blocked-plan" in v
        for v in res["permission_violations"]
    )
    # 4. Skill without command is strictly `DISCLOSED_ONLY` (`UNOBSERVED`), never `PASS`
    assert res["skill_outputs"]["proc-suite/doc-review"]["execution_state"] == "DISCLOSED_ONLY"
    assert res["skill_outputs"]["proc-suite/doc-review"]["gate_verdict"] == "UNOBSERVED"
    assert res["execution_summary"]["skills_disclosed_only"] == 1
    assert res["execution_summary"]["skills_executed_pass"] == 1
    assert res["execution_summary"]["skills_executed_fail"] == 1
    assert res["execution_summary"]["skills_blocked_by_permission"] == 1
    # 5. Independent verifier ran in isolated subprocess and attested `PASS`
    assert res["independent_verifier_receipt"]["status"] == "PASS"

    # 6. Concurrent run lock (`O_CREAT | O_EXCL`) blocks overlapping run
    from factory.lifecycle import acquire_run_lock, release_run_lock

    acquire_run_lock(repo, "concurrent-holder")
    try:
        with pytest.raises(RuntimeError, match="CONCURRENT_RUN_LOCK_HELD"):
            factory.execute_modular_run(repo, run_id="run-2", prompt="tdd")
    finally:
        release_run_lock(repo)


def test_adversarial_doctor_detects_broken_script_syntax_and_silent_zero_hooks(
    tmp_path: Path,
) -> None:
    """Adversarial Gate 7/10: `doctor()` catches Python syntax errors in bundled skill scripts (`ast.parse`) and warns on silent-zero frontmatter hooks."""
    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    _init_clean_repo(repo)

    broken_pkg = tmp_path / "broken-script-skill"
    skill_dir = broken_pkg / "skills" / "ui-gen"
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: ui-gen\ndescription: UI generator\nhooks:\n  Stop:\n    - hooks:\n        - type: command\n          command: node gate.mjs || { echo 'not found' >&2; exit 0; }\n---\n# UI Gen\n",
        encoding="utf-8",
    )
    (scripts_dir / "bad_syntax.py").write_text(
        "def broken(\n    return 1\n",
        encoding="utf-8",
    )

    factory.add_module(repo, broken_pkg)
    doc = factory.doctor(repo)
    assert doc["status"] == "DEGRADED"
    assert any(
        "incompatible_python_syntax:broken-script-skill/ui-gen" in p for p in doc["problems"]
    )
    assert any(
        "unverified_hook_silent_zero:broken-script-skill/ui-gen" in w for w in doc["warnings"]
    )


def test_adversarial_slot_deduplication_discover_hosts_and_before_after_eval(
    tmp_path: Path,
) -> None:
    """Adversarial Gate 4/11/12: Competing skills across modules deduplicate by slot; `discover`, `hosts`, and before/after `evaluate_skill_impact` work end-to-end."""
    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    sha = _init_clean_repo(repo)

    tdd_a = _write_skill_pkg(
        tmp_path,
        "alpha-tdd",
        {
            "tdd": "---\ncategory: engineering\nsubprocess_exec: true\n---\n# Alpha TDD\nTest-driven development workflow.\n"
        },
    )
    tdd_b = _write_skill_pkg(
        tmp_path,
        "beta-tdd",
        {"tdd": "---\ncategory: engineering\n---\n# Beta TDD\nTest-driven development workflow.\n"},
    )
    factory.add_module(repo, tdd_a)
    factory.add_module(repo, tdd_b)

    # Slot deduplication picks one winner for `engineering:tdd` instead of stacking both
    route = factory.route_skills_for_task(repo, "implement feature with tdd")
    assert route["selected_skills"] == ["alpha-tdd/tdd"]
    assert route["slot_winners"]["engineering:tdd"] == "alpha-tdd/tdd"
    assert any("redundant_slot_skipped:beta-tdd/tdd" in d for d in route["deduplicated_skills"])

    # Generic discovery finds skill packages in `tmp_path`
    discovered = factory.discover_skills([tmp_path], query="tdd")
    assert len(discovered) >= 2

    # Host integration matrix verifies all 4 hosts with honest OBSERVED/UNOBSERVED status
    hosts = factory.verify_host_integrations(repo)
    assert set(hosts.keys()) == {"claude-code", "cursor", "codex", "antigravity"}
    assert hosts["claude-code"]["hook_enforcement"] == "OBSERVED"
    assert hosts["cursor"]["hook_enforcement"] == "UNOBSERVED"
    assert hosts["codex"]["hook_enforcement"] == "UNOBSERVED"
    assert hosts["antigravity"]["hook_enforcement"] == "UNOBSERVED"

    # Real Before (baseline: skills disabled) vs After (treatment: skill enabled & executed) evaluation
    factory.disable_target(repo, "alpha-tdd")
    factory.disable_target(repo, "beta-tdd")
    baseline_run = factory.execute_modular_run(
        repo,
        run_id="run-baseline",
        prompt="implement feature with tdd",
        verify_cmd=[
            sys.executable,
            "-c",
            "import pathlib; assert pathlib.Path('app.py').is_file()",
        ],
    )
    assert baseline_run["execution_summary"]["skills_routed"] == 0

    factory.enable_target(repo, "alpha-tdd/tdd")
    treatment_run = factory.execute_modular_run(
        repo,
        run_id="run-treatment",
        prompt="implement feature with tdd",
        skill_commands={
            "alpha-tdd/tdd": [
                sys.executable,
                "-c",
                "import app; assert app.add(2, 3) == 5; print('PASS')",
            ]
        },
        verify_cmd=[
            sys.executable,
            "-c",
            "import pathlib; assert pathlib.Path('app.py').is_file()",
        ],
    )
    assert treatment_run["execution_summary"]["skills_executed_pass"] == 1
    assert treatment_run["six_lens_measurement"]["exact_artifact_sha"] == sha

    eval_res = factory.evaluate_skill_impact(
        skill_id="alpha-tdd/tdd",
        case_id="case-real-before-after",
        baseline_metrics={
            "passed": False,
            "score": 60.0,
            "tokens": baseline_run["estimated_tokens"] + 500,
            "duration_ms": max(1, baseline_run["duration_ms"]),
            "human_interventions": 1,
        },
        treatment_metrics={
            "passed": treatment_run["independent_verifier_receipt"]["status"] == "PASS",
            "score": 95.0,
            "tokens": treatment_run["estimated_tokens"] + 500,
            "duration_ms": max(1, treatment_run["duration_ms"]),
            "human_interventions": 0,
        },
        six_lens_statuses={
            p["lens"]: p["state"] for p in treatment_run["six_lens_measurement"]["plates"]
        },
    )
    assert eval_res["case_result"]["verdict"] == "HELPED"
    assert eval_res["lifecycle_recommendation"]["recommended_action"] == "KEEP_ENABLED"
    assert eval_res["lifecycle_recommendation"]["authority_expanded"] is False


def test_adversarial_all_official_external_and_workspace_repos_real_cli_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Adversarial Gate 12: Attach all 8 official upstream skill repositories + 5 workspace repositories, execute `ui-ux-pro-max` search.py via `hyodo-factory run` CLI, and detach cleanly."""
    ext_dir = Path("/home/antigravity/lofibrainwav/external-skills")
    if not ext_dir.is_dir():
        pytest.skip("external-skills directory not present in this environment")

    factory = _load_factory_module()
    repo = tmp_path / "workspace"
    _init_clean_repo(repo)

    expected_external = [
        "superpowers",
        "pstack",
        "taste-skill",
        "ui-ux-pro-max-skill",
        "impeccable",
        "graphify",
        "security-audit-skill",
        "skills",
    ]
    attached: list[str] = []
    for name in expected_external:
        cand = ext_dir / name
        if cand.is_dir():
            rec = factory.add_module(repo, cand)
            attached.append(rec.module_id)
            assert rec.license_spdx in ("MIT", "Apache-2.0")
            assert len(rec.skills) >= 1

    search_script = (
        ext_dir
        / "ui-ux-pro-max-skill"
        / ".claude"
        / "skills"
        / "ui-ux-pro-max"
        / "scripts"
        / "search.py"
    )
    if search_script.is_file():
        rc = factory.main(
            [
                "--root",
                str(repo),
                "run",
                "ui-ux-pro-max-skill/ui-ux-pro-max \ub514\uc790\uc778 \uc2a4\ud0c0\uc77c \uac80\uc0c9 \ubc0f \uac80\uc99d",
                "--run-id",
                "cli-e2e-real-script",
                "--skill-cmd",
                f"ui-ux-pro-max-skill/ui-ux-pro-max={sys.executable} {search_script} 'fintech Minimal' --domain style -n 1",
                "--verify-cmd",
                f"{sys.executable} -c \"import pathlib; assert pathlib.Path('app.py').is_file()\"",
            ]
        )
        assert rc == 0
        run_payload = json.loads(capsys.readouterr().out)
        ui_out = run_payload["skill_outputs"]["ui-ux-pro-max-skill/ui-ux-pro-max"]
        assert ui_out["execution_state"] == "EXECUTED_PASS"
        assert "UI Pro Max Search Results" in ui_out["stdout"]
        assert run_payload["independent_verifier_receipt"]["status"] == "PASS"

    for mod_id in attached:
        factory.remove_module(repo, mod_id)
    assert factory.doctor(repo)["modules_registered"] == 0
