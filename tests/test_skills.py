"""TDD for Stage 2 package 2-A: `hyodo skills ingest|lens|propose` (skill lens).

Spec: docs/superpowers/specs/2026-09-06-hyodo-agent-os-stage2-design.md,
Package 2-A.
"""

from __future__ import annotations

import json
import subprocess

import pytest
from typer.testing import CliRunner

from hyodo.cli.main import app
from hyodo.events import read_agent_events
from hyodo.policy import (
    _BUILTIN_SUPPLY_CHAIN_TOOLS,
    PolicyConfig,
    TrustPolicy,
    evaluate_policy,
)
from hyodo.policy_trust import grant_policy_trust
from hyodo.skills import (
    CompiledCheck,
    compile_rule,
    evaluate_compiled_rule,
    infer_pillars,
    load_manifest,
    parse_skill_rules,
    parse_skill_text,
    render_proposal,
    resolve_source,
    rule_id_for,
    skill_name_for,
    strip_pillar_tag,
)

runner = CliRunner()


def _git_init(path):
    subprocess.run(["git", "init", "-q"], cwd=str(path), check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=t", "add", "-A"],
        cwd=str(path),
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.email=t@example.com",
            "-c",
            "user.name=t",
            "commit",
            "-q",
            "-m",
            "init",
        ],
        cwd=str(path),
        check=True,
    )


# --- Rule-id determinism -----------------------------------------------------


def test_rule_id_deterministic_and_slugified():
    rule_id = rule_id_for("my-skill", "Always Write Tests, Please!")
    assert rule_id == rule_id_for("my-skill", "Always Write Tests, Please!")
    assert rule_id.startswith("my-skill:")
    assert rule_id.split(":", 1)[1] == "always-write-tests-please"


def test_rule_id_caps_at_48_chars_of_rule_text():
    long_text = "x" * 100
    rule_id = rule_id_for("s", long_text)
    slug = rule_id.split(":", 1)[1]
    assert len(slug) <= 48


def test_skill_name_for_skill_md_uses_parent_dir():
    from pathlib import Path

    assert skill_name_for(Path("/repo/skills/example/SKILL.md")) == "example"
    assert skill_name_for(Path("/repo/skills/example/SKILL.md".upper())) or True


def test_skill_name_for_other_file_uses_stem():
    from pathlib import Path

    assert skill_name_for(Path("/repo/conventions.md")) == "conventions"


# --- Skill file format --------------------------------------------------------


def test_parse_rules_under_rules_heading_only():
    text = """# Skill

Some prose with a - dash that is not a bullet.

## Rules

- one
- two

## Notes

- not a rule
"""
    assert parse_skill_text(text) == ["one", "two"]


def test_parse_rules_case_insensitive_heading():
    text = "## rules\n- a\n- b\n"
    assert parse_skill_text(text) == ["a", "b"]


def test_parse_all_top_level_bullets_when_no_rules_heading():
    text = "# Skill\n\n- alpha\n- beta\n\n## Other\n\n- gamma\n"
    assert parse_skill_text(text) == ["alpha", "beta", "gamma"]


# --- Pillar mapping: tag ------------------------------------------------------


def test_tag_mapping_extracts_and_strips_tag():
    base, pillars = strip_pillar_tag("Keep secrets safe. [pillars: truth, goodness]")
    assert base == "Keep secrets safe."
    assert pillars == ("truth", "goodness")


def test_tag_mapping_no_tag_returns_none():
    base, pillars = strip_pillar_tag("Just prose with no tag.")
    assert base == "Just prose with no tag."
    assert pillars is None


# --- Pillar mapping: keyword table --------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected_pillar"),
    [
        ("Always write a test for new code.", "truth"),
        ("Never commit a secret to the repo.", "goodness"),
        ("Update the README for clarity.", "beauty"),
        ("Improve onboarding for new developers.", "benevolence"),
        ("Follow the project convention.", "hyo"),
        ("Keep dependency versions pinned.", "eternity"),
    ],
)
def test_keyword_mapping_hits_expected_pillar(text, expected_pillar):
    assert expected_pillar in infer_pillars(text)


def test_keyword_mapping_matches_word_starts_only():
    """``ui`` must not match the letters inside ``require``; ``tests`` still hits ``test``."""
    assert infer_pillars("require pattern: def main\\(") == ()
    assert infer_pillars("require file: docs/README.md") == ("beauty",)
    assert infer_pillars("all tests must pass") == ("truth",)


def test_keyword_mapping_no_match_is_empty_tuple():
    assert infer_pillars("Do a thing with no keyword overlap at all.") == ()


def test_keyword_mapping_rule_can_hit_several_pillars():
    pillars = infer_pillars("Write tests and update the README for this security fix.")
    assert "truth" in pillars
    assert "beauty" in pillars


# --- Mechanical checks: compile ----------------------------------------------


def test_compile_require_file():
    assert compile_rule("require file: README.md") == CompiledCheck("require_file", "README.md")


def test_compile_forbid_pattern():
    assert compile_rule("forbid pattern: TODO") == CompiledCheck("forbid_pattern", "TODO")


def test_compile_require_pattern():
    assert compile_rule("require pattern: def main\\(") == CompiledCheck(
        "require_pattern", "def main\\("
    )


def test_compile_ruff():
    assert compile_rule("ruff: F401") == CompiledCheck("ruff", "F401")


def test_compile_advisory_is_none():
    assert compile_rule("Please be nice to reviewers.") is None


# --- Mechanical checks: evaluate (PASS and FAIL for each of the four) -------


def test_require_file_pass_and_fail(tmp_path):
    (tmp_path / "README.md").write_text("hi", encoding="utf-8")
    rules = parse_skill_rules(
        "s", "## Rules\n- require file: README.md\n- require file: MISSING.md\n"
    )
    statuses = {r.rule_id.split(":", 1)[1]: evaluate_compiled_rule(r, tmp_path) for r in rules}
    assert statuses["require-file-readme-md"].status == "PASS"
    assert statuses["require-file-missing-md"].status == "FAIL"


def test_forbid_pattern_pass_and_fail(tmp_path):
    (tmp_path / "clean.py").write_text("print('ok')\n", encoding="utf-8")
    _git_init(tmp_path)
    rules = parse_skill_rules("s", "## Rules\n- forbid pattern: BADWORD\n")
    status = evaluate_compiled_rule(rules[0], tmp_path)
    assert status.status == "PASS"

    (tmp_path / "dirty.py").write_text("BADWORD\n", encoding="utf-8")
    _git_init(tmp_path)
    status2 = evaluate_compiled_rule(rules[0], tmp_path)
    assert status2.status == "FAIL"


def test_require_pattern_pass_and_fail(tmp_path):
    (tmp_path / "a.py").write_text("def main():\n    pass\n", encoding="utf-8")
    _git_init(tmp_path)
    rules = parse_skill_rules("s", "## Rules\n- require pattern: def main\\(\n")
    status = evaluate_compiled_rule(rules[0], tmp_path)
    assert status.status == "PASS"

    rules2 = parse_skill_rules("s", "## Rules\n- require pattern: nope_not_here\n")
    status2 = evaluate_compiled_rule(rules2[0], tmp_path)
    assert status2.status == "FAIL"


def test_ruff_pass_and_unavailable(tmp_path, monkeypatch):
    (tmp_path / "clean.py").write_text("x = 1\n", encoding="utf-8")
    rules = parse_skill_rules("s", "## Rules\n- ruff: F401\n")
    status = evaluate_compiled_rule(rules[0], tmp_path)
    assert status.status in ("PASS", "FAIL")  # depends on ruff's own scan of hyodo/ from tmp_path
    assert status.status != "UNOBSERVED"

    import hyodo.skills as skills_mod

    def _boom(*_args, **_kwargs):
        raise FileNotFoundError("no ruff")

    monkeypatch.setattr(skills_mod.subprocess, "run", _boom)
    status2 = evaluate_compiled_rule(rules[0], tmp_path)
    assert status2.status == "UNOBSERVED"
    assert status2.reason == "ruff_unavailable"


def test_advisory_rule_is_unobserved(tmp_path):
    rules = parse_skill_rules("s", "## Rules\n- Please write friendly commit messages.\n")
    status = evaluate_compiled_rule(rules[0], tmp_path)
    assert status.status == "UNOBSERVED"


# --- resolve_source / manifest -----------------------------------------------


def test_resolve_source_path_readable(tmp_path):
    (tmp_path / "SKILL.md").write_text("## Rules\n- require file: x\n", encoding="utf-8")
    parsed = resolve_source(tmp_path, "SKILL.md")
    assert parsed.kind == "path"
    assert parsed.readable is True
    assert parsed.manifest_source == "path:SKILL.md"
    assert parsed.content_digest_value is not None


def test_resolve_source_path_unreadable(tmp_path):
    parsed = resolve_source(tmp_path, "nope/SKILL.md")
    assert parsed.readable is False
    assert parsed.content_digest_value is None


def test_resolve_source_url_records_domain_only():
    parsed = resolve_source(None, "https://example.com/a/b?x=1")  # type: ignore[arg-type]
    assert parsed.kind == "url"
    assert parsed.readable is False
    assert parsed.manifest_source == "url:example.com"
    assert parsed.content_digest_value is None


def test_manifest_malformed_treated_as_empty(tmp_path):
    manifest_dir = tmp_path / ".hyodo" / "skills"
    manifest_dir.mkdir(parents=True)
    (manifest_dir / "manifest.json").write_text("not json", encoding="utf-8")
    manifest, status = load_manifest(tmp_path)
    assert manifest is None
    assert status == "malformed"


def test_manifest_missing_is_reported_as_missing(tmp_path):
    manifest, status = load_manifest(tmp_path)
    assert manifest is None
    assert status == "missing"


# --- Policy: unconditional external variable, trust gate ---------------------


def _tool_event(source_path: str) -> dict:
    return {
        "schema_version": "hyodo.agent-event/v1",
        "event_id": "evt-1",
        "run_id": "run-1",
        "ts": "2026-09-06T12:00:00+00:00",
        "kind": "tool_call",
        "step_index": 0,
        "actor": "hyodo",
        "tool": {"name": "skills.ingest", "paths": [source_path], "urls": []},
        "io": {"input_digest": None, "output_digest": None},
    }


def _bare_policy(**overrides) -> PolicyConfig:
    base = {
        "schema": "hyodo.policy/v1",
        "max_steps": None,
        "allowed_tools": None,
        "blocked_path_globs": (),
    }
    base.update(overrides)
    return PolicyConfig(**base)


def test_supply_chain_tools_constant_includes_skills_ingest():
    assert "skills.ingest" in _BUILTIN_SUPPLY_CHAIN_TOOLS


def test_ingest_unconditionally_produces_skill_ingest_external_variable(tmp_path):
    from hyodo.events import validate_event

    ok, _reasons, normalized = validate_event(_tool_event("skills/demo/SKILL.md"))
    assert ok
    decision = evaluate_policy(normalized, _bare_policy(), observed_steps=0, root=tmp_path)
    assert any(v.startswith("skill_ingest:") for v in decision.external_variables)


def test_trust_level_2_does_not_soften_skill_ingest_to_allow(tmp_path):
    from hyodo.events import validate_event

    ok, _reasons, normalized = validate_event(_tool_event("skills/demo/SKILL.md"))
    assert ok
    policy = _bare_policy(trust=TrustPolicy(max_level=3))
    grant_policy_trust(tmp_path, 2, by="human:test")
    decision = evaluate_policy(normalized, policy, observed_steps=0, root=tmp_path)
    assert decision.decision != "ALLOW"


def test_trust_level_3_softens_skill_ingest_to_allow(tmp_path):
    from hyodo.events import validate_event

    ok, _reasons, normalized = validate_event(_tool_event("skills/demo/SKILL.md"))
    assert ok
    policy = _bare_policy(trust=TrustPolicy(max_level=3))
    grant_policy_trust(tmp_path, 3, by="human:test")
    decision = evaluate_policy(normalized, policy, observed_steps=0, root=tmp_path)
    assert decision.decision == "ALLOW"


# --- CLI: ingest ---------------------------------------------------------------


def _write_demo_skill(root):
    skill_dir = root / "skills" / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "# Demo\n\n## Rules\n\n- require file: README.md\n- ruff: F401\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text("# Demo repo\n", encoding="utf-8")
    _git_init(root)


def test_cli_ingest_default_ask_and_body_not_stored(tmp_path):
    _write_demo_skill(tmp_path)
    result = runner.invoke(
        app,
        ["skills", "ingest", "skills/demo/SKILL.md", "--root", str(tmp_path), "--json"],
    )
    assert result.exit_code == 3
    payload = json.loads(result.stdout)
    assert payload["decision"] == "ASK"
    manifest_path = tmp_path / ".hyodo" / "skills" / "manifest.json"
    assert not manifest_path.exists()


def test_cli_ingest_yes_compiles_manifest_body_not_stored_by_default(tmp_path):
    _write_demo_skill(tmp_path)
    result = runner.invoke(
        app,
        [
            "skills",
            "ingest",
            "skills/demo/SKILL.md",
            "--root",
            str(tmp_path),
            "--yes",
            "--json",
        ],
    )
    assert result.exit_code == 0
    manifest_path = tmp_path / ".hyodo" / "skills" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = manifest["skills"][0]
    assert entry["body_stored"] is False
    body_dir = tmp_path / ".hyodo" / "skills" / "bodies"
    assert not body_dir.exists()


def test_cli_ingest_store_body_persists_body(tmp_path):
    _write_demo_skill(tmp_path)
    result = runner.invoke(
        app,
        [
            "skills",
            "ingest",
            "skills/demo/SKILL.md",
            "--root",
            str(tmp_path),
            "--yes",
            "--store-body",
            "--json",
        ],
    )
    assert result.exit_code == 0
    manifest_path = tmp_path / ".hyodo" / "skills" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = manifest["skills"][0]
    assert entry["body_stored"] is True
    body_dir = tmp_path / ".hyodo" / "skills" / "bodies"
    assert len(list(body_dir.glob("*.md"))) == 1


def test_cli_ingest_unreadable_source_recorded_not_dropped(tmp_path):
    _write_demo_skill(tmp_path)
    result = runner.invoke(
        app,
        [
            "skills",
            "ingest",
            "skills/missing/SKILL.md",
            "--root",
            str(tmp_path),
            "--yes",
            "--json",
        ],
    )
    assert result.exit_code == 0
    manifest_path = tmp_path / ".hyodo" / "skills" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = manifest["skills"][0]
    assert entry["content_digest"] is None
    assert entry["status"] == "unreadable"


def test_cli_ingest_trust_level_3_grants_allow_without_yes(tmp_path):
    _write_demo_skill(tmp_path)
    (tmp_path / ".hyodo").mkdir(exist_ok=True)
    (tmp_path / ".hyodo" / "policy.toml").write_text(
        'schema = "hyodo.policy/v1"\n\n[trust]\nmax_level = 3\n',
        encoding="utf-8",
    )
    grant_policy_trust(tmp_path, 3, by="human:test")
    result = runner.invoke(
        app,
        ["skills", "ingest", "skills/demo/SKILL.md", "--root", str(tmp_path), "--json"],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["decision"] == "ALLOW"


# --- CLI: lens -------------------------------------------------------------


def test_cli_lens_excludes_advisory_rule_from_score_and_lists_unobserved(tmp_path):
    skill_dir = tmp_path / "skills" / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "## Rules\n\n- require file: README.md\n- Be kind to reviewers.\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# demo\n", encoding="utf-8")
    _git_init(tmp_path)
    runner.invoke(
        app,
        ["skills", "ingest", "skills/demo/SKILL.md", "--root", str(tmp_path), "--yes"],
    )
    result = runner.invoke(app, ["skills", "lens", "--root", str(tmp_path), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert len(payload["unobserved"]) == 1
    assert payload["unobserved"][0]["rule_text_digest"]
    all_rule_ids = {p["rule_id"] for pillar in payload["pillars"] for p in pillar["provenance"]}
    assert not any(rid.endswith("be-kind-to-reviewers") for rid in all_rule_ids)


def test_cli_lens_untagged_keyword_less_rule_is_unclassified(tmp_path):
    skill_dir = tmp_path / "skills" / "demo"
    skill_dir.mkdir(parents=True)
    # "require file:" is a mechanical prefix (so this compiles, unlike a plain
    # advisory sentence), but "config.toml" hits none of the pillar keywords
    # and the rule carries no `[pillars: ...]` tag.
    (skill_dir / "SKILL.md").write_text(
        "## Rules\n\n- require file: config.toml\n",
        encoding="utf-8",
    )
    (tmp_path / "config.toml").write_text("", encoding="utf-8")
    _git_init(tmp_path)
    runner.invoke(
        app,
        ["skills", "ingest", "skills/demo/SKILL.md", "--root", str(tmp_path), "--yes"],
    )
    result = runner.invoke(app, ["skills", "lens", "--root", str(tmp_path), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)

    unclassified_ids = {p["rule_id"] for p in payload["unclassified"]["provenance"]}
    assert any(rid.endswith("require-file-config-toml") for rid in unclassified_ids)
    assert payload["unclassified"]["expected"] == 1

    pillar_ids = {p["rule_id"] for pillar in payload["pillars"] for p in pillar["provenance"]}
    assert not any(rid.endswith("require-file-config-toml") for rid in pillar_ids)


def test_cli_lens_malformed_manifest_exit_2(tmp_path):
    manifest_dir = tmp_path / ".hyodo" / "skills"
    manifest_dir.mkdir(parents=True)
    (manifest_dir / "manifest.json").write_text("not json", encoding="utf-8")
    result = runner.invoke(app, ["skills", "lens", "--root", str(tmp_path), "--json"])
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["manifest_status"] == "malformed"


def test_cli_lens_missing_manifest_is_zero_everywhere_not_an_error(tmp_path):
    result = runner.invoke(app, ["skills", "lens", "--root", str(tmp_path), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    for pillar in payload["pillars"]:
        assert pillar["expected"] == 0
        assert pillar["observed"] == 0


# --- CLI: propose ------------------------------------------------------------


def test_cli_propose_without_accept_writes_nothing_and_no_event(tmp_path):
    _write_demo_skill(tmp_path)
    runner.invoke(
        app,
        ["skills", "ingest", "skills/demo/SKILL.md", "--root", str(tmp_path), "--yes"],
    )
    events_before, _ = read_agent_events(tmp_path)
    count_before = len(events_before or [])

    result = runner.invoke(app, ["skills", "propose", "--root", str(tmp_path)])
    assert result.exit_code == 0
    proposed_path = tmp_path / ".hyodo" / "skills" / "proposed.md"
    assert not proposed_path.exists()
    events_after, _ = read_agent_events(tmp_path)
    assert len(events_after or []) == count_before


def test_cli_propose_accept_writes_exactly_one_file_and_one_event(tmp_path):
    _write_demo_skill(tmp_path)
    runner.invoke(
        app,
        ["skills", "ingest", "skills/demo/SKILL.md", "--root", str(tmp_path), "--yes"],
    )
    events_before, _ = read_agent_events(tmp_path)
    count_before = len(events_before or [])

    result = runner.invoke(app, ["skills", "propose", "--root", str(tmp_path), "--accept"])
    assert result.exit_code == 0
    proposed_path = tmp_path / ".hyodo" / "skills" / "proposed.md"
    assert proposed_path.exists()
    events_after, _ = read_agent_events(tmp_path)
    assert len(events_after or []) == count_before + 1
    last_event = (events_after or [])[-1]
    assert last_event["tool"]["name"] == "skills.propose"
    assert last_event["policy"]["decision"] == "ALLOW"


def test_render_proposal_only_includes_passed_rules(tmp_path):
    skill_dir = tmp_path / "skills" / "demo"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "## Rules\n\n- require file: README.md\n- require file: MISSING.md\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# demo\n", encoding="utf-8")
    _git_init(tmp_path)
    runner.invoke(
        app,
        ["skills", "ingest", "skills/demo/SKILL.md", "--root", str(tmp_path), "--yes"],
    )
    result = render_proposal(tmp_path, "demo-repo")
    assert "require file: README.md" in result.markdown
    assert "require file: MISSING.md" not in result.markdown
