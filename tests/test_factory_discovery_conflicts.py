"""Factory routing intent coverage and same-name skill source conflict reporting.

Two reproduced gaps in `examples/factory-loop/`:

1. `orchestration` is a valid skill category (and drives the single-orchestrator
   guard) but no natural-language intent maps to it, so an orchestration
   request silently falls back to `engineering` and never selects such a skill.
2. `discover_skills` lists same-name skills from different roots without
   saying whether they are the same bytes (an alias) or different bytes (a
   real divergence), so a divergent pair can be mistaken for a harmless copy.

The fixtures here are synthetic; they are not live evidence about any host.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

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


def _write_skill(root: Path, name: str, body: str, *, category: str | None = None) -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    front = f"---\nname: {name}\ndescription: fixture {name}\n"
    if category:
        front += f"category: {category}\n"
    front += "---\n"
    path = skill_dir / "SKILL.md"
    path.write_text(f"{front}# {name}\n{body}\n", encoding="utf-8")
    return path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize(
    "prompt",
    [
        "dispatch parallel workers across worktrees and supervise them via orchestration",
        "coordinate multi-agent worker dispatch with task DAG and settlement",
        "\uc5ec\ub7ec \uc791\uc5c5\uc790\uc5d0\uac8c \ubcd1\ub82c \ub514\uc2a4\ud328\uce58\ud558\uace0 \uc624\ucf00\uc2a4\ud2b8\ub808\uc774\uc158 \uc870\uc728",
    ],
)
def test_orchestration_intent_is_inferred_and_selects_orchestration_skill(
    tmp_path: Path, prompt: str
) -> None:
    factory = _load_factory_module()
    from factory.router import infer_intent_categories

    assert "orchestration" in infer_intent_categories(prompt)

    repo = tmp_path / "workspace"
    repo.mkdir()
    pkg = tmp_path / "pkg"
    _write_skill(pkg, "dispatch-workers", "fixture body", category="orchestration")
    factory.add_module(repo, pkg)

    plan = factory.route_skills_for_task(repo, prompt)
    assert "pkg/dispatch-workers" in plan["selected_skills"]


def test_plain_engineering_prompt_does_not_infer_orchestration() -> None:
    _load_factory_module()
    from factory.router import infer_intent_categories

    cats = infer_intent_categories("fix the failing unit test and implement the feature")
    assert "orchestration" not in cats
    assert "engineering" in cats


def _discover_pair(tmp_path: Path, body_a: str, body_b: str) -> tuple[Any, list[Path], Path, Path]:
    factory = _load_factory_module()
    root_a, root_b = tmp_path / "rootA", tmp_path / "rootB"
    file_a = _write_skill(root_a, "orchestration", body_a)
    file_b = _write_skill(root_b, "orchestration", body_b)
    return factory, [root_a, root_b], file_a, file_b


def test_divergent_same_name_skills_are_reported_with_digests_and_never_resolved(
    tmp_path: Path,
) -> None:
    factory, roots, file_a, file_b = _discover_pair(
        tmp_path, "vendor command guide", "project doctrine"
    )
    found = factory.discover_skills(roots, query="orchestration")
    # No silent bypass: both sources stay visible.
    assert len([e for e in found if e["name"] == "orchestration"]) == 2

    conflicts = factory.find_same_name_skill_conflicts(found)
    assert len(conflicts) == 1
    group = conflicts[0]
    assert group["skill"] == "orchestration"
    assert group["status"] == "DIVERGENT"
    assert {s["sha256"] for s in group["sources"]} == {_sha(file_a), _sha(file_b)}
    assert {s["path"] for s in group["sources"]} == {
        str(file_a.resolve()),
        str(file_b.resolve()),
    }
    # HyoDo reports the divergence; picking a winner belongs to the host.
    assert group["resolution"] == "HOST_DECISION_REQUIRED"
    assert "winner" not in group


def test_same_hash_copies_are_aliases_not_divergence(tmp_path: Path) -> None:
    factory, roots, file_a, file_b = _discover_pair(tmp_path, "same body", "same body")
    assert _sha(file_a) == _sha(file_b)
    conflicts = factory.find_same_name_skill_conflicts(
        factory.discover_skills(roots, query="orchestration")
    )
    assert [c["status"] for c in conflicts] == ["ALIAS"]
    assert conflicts[0]["resolution"] == "HOST_DECISION_REQUIRED"


def test_one_file_seen_through_aggregate_and_child_entry_is_not_a_conflict(
    tmp_path: Path,
) -> None:
    factory = _load_factory_module()
    root = tmp_path / "skills"
    _write_skill(root, "orchestration", "only copy")
    _write_skill(root, "tdd", "other")
    found = factory.discover_skills([root])
    assert factory.find_same_name_skill_conflicts(found) == []


def test_discover_cli_prints_conflicts_next_to_discovered(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    factory, roots, _a, _b = _discover_pair(tmp_path, "one", "two")
    (tmp_path / "ws").mkdir()
    rc = factory.main(
        [
            "--root",
            str(tmp_path / "ws"),
            "discover",
            "--search-root",
            str(roots[0]),
            "--search-root",
            str(roots[1]),
        ]
    )
    assert rc in (0, None)
    payload = json.loads(capsys.readouterr().out)
    assert [c["status"] for c in payload["conflicts"]] == ["DIVERGENT"]
    assert len(payload["discovered"]) >= 2


# --- gaps: a related registered trusted skill must not hide divergent same-name input ---

GAP_PROMPT = "implement the feature with tdd and a careful test plan for the module"


def _trusted_registry(tmp_path: Path) -> tuple[Any, Path, Path]:
    """Register one trusted `tdd` skill (synthetic fixture, not live evidence)."""
    factory = _load_factory_module()
    ws = tmp_path / "ws"
    ws.mkdir()
    pkg = tmp_path / "pkg"
    _write_skill(pkg, "tdd", "registered canonical body", category="engineering")
    factory.add_module(ws, pkg)
    mod = factory.load_registry_state(ws)["pkg"]
    unit = mod.skills["pkg/tdd"]
    trust = {
        "skills": {
            "pkg/tdd": {
                "content_sha256": unit.content_sha256,
                "version": mod.version,
                "boundary": unit.boundary.to_dict(),
                "trust_stage": "TRUSTED",
                "verifier_status": "PASS",
                "eval_verdict": "HELPED",
            }
        }
    }
    (ws / ".hyodo" / "factory").mkdir(parents=True, exist_ok=True)
    (ws / ".hyodo" / "factory" / "trust_state.json").write_text(json.dumps(trust))
    return factory, ws, pkg


def test_trusted_registered_skill_does_not_hide_divergent_external_same_name(
    tmp_path: Path,
) -> None:
    factory, ws, pkg = _trusted_registry(tmp_path)
    ext = tmp_path / "ext"
    ext_file = _write_skill(ext, "tdd", "DIVERGENT external body", category="engineering")

    report = factory.analyze_capability_gaps(ws, GAP_PROMPT, external_search_roots=[ext])

    # Not a false green: the category is no longer plain VERIFIED.
    cat = report["category_assessments"]["engineering"]
    assert cat["state"] == "UNKNOWN"
    assert cat["root_cause"] == "VERIFICATION_MISSING"
    assert cat["source_conflicts"] == ["pkg/tdd"]

    registered_sha = _sha(pkg / "tdd" / "SKILL.md")
    assert len(report["source_conflicts"]) == 1
    conflict = report["source_conflicts"][0]
    assert conflict["skill_id"] == "pkg/tdd"
    assert conflict["status"] == "DIVERGENT"
    assert conflict["registered_sha256"] == registered_sha
    assert conflict["sources"] == [{"path": str(ext_file.resolve()), "sha256": _sha(ext_file)}]
    assert conflict["resolution"] == "HOST_DECISION_REQUIRED"

    # Canonical host precedence: the registered skill is still the routed one,
    # still verified at skill level, and its digest correlates execution receipts.
    assert "pkg/tdd" in report["route_plan"]["selected_skills"]
    item = report["skill_assessments"]["pkg/tdd"]
    assert item["state"] == "VERIFIED"
    assert item["content_sha256"] == registered_sha


def test_same_byte_external_alias_keeps_the_category_verified(tmp_path: Path) -> None:
    factory, ws, _pkg = _trusted_registry(tmp_path)
    ext = tmp_path / "ext"
    _write_skill(ext, "tdd", "registered canonical body", category="engineering")

    report = factory.analyze_capability_gaps(ws, GAP_PROMPT, external_search_roots=[ext])
    assert report["category_assessments"]["engineering"]["state"] == "VERIFIED"
    assert report["source_conflicts"] == []


def test_divergent_same_name_in_an_unrelated_category_is_not_reported(tmp_path: Path) -> None:
    factory, ws, _pkg = _trusted_registry(tmp_path)
    other = tmp_path / "other-pkg"
    _write_skill(other, "palette", "registered design body", category="design")
    factory.add_module(ws, other)
    ext = tmp_path / "ext"
    _write_skill(ext, "palette", "divergent design body", category="design")

    report = factory.analyze_capability_gaps(ws, GAP_PROMPT, external_search_roots=[ext])
    assert "design" not in report["inferred_categories"]
    assert report["source_conflicts"] == []
    assert report["category_assessments"]["engineering"]["state"] == "VERIFIED"


def test_simple_task_fast_path_still_reports_the_divergence(tmp_path: Path) -> None:
    factory, ws, _pkg = _trusted_registry(tmp_path)
    qa_pkg = tmp_path / "qa-pkg"
    _write_skill(qa_pkg, "qa-gate", "registered quality body", category="quality")
    factory.add_module(ws, qa_pkg)
    ext = tmp_path / "ext"
    _write_skill(ext, "tdd", "DIVERGENT external body", category="engineering")

    report = factory.analyze_capability_gaps(ws, "tdd the parser", external_search_roots=[ext])
    assert report["is_simple_task"] is True
    assert report["category_assessments"]["engineering"]["state"] == "UNKNOWN"
    assert [c["skill_id"] for c in report["source_conflicts"]] == ["pkg/tdd"]


def test_gaps_without_search_roots_is_unchanged_and_reports_no_conflicts(
    tmp_path: Path,
) -> None:
    factory, ws, _pkg = _trusted_registry(tmp_path)
    report = factory.analyze_capability_gaps(ws, GAP_PROMPT)
    assert report["category_assessments"]["engineering"]["state"] == "VERIFIED"
    assert report["source_conflicts"] == []


def test_gaps_conflict_check_is_read_only(tmp_path: Path) -> None:
    factory, ws, pkg = _trusted_registry(tmp_path)
    ext = tmp_path / "ext"
    ext_file = _write_skill(ext, "tdd", "DIVERGENT external body", category="engineering")
    before = {p: p.read_bytes() for p in (ext_file, pkg / "tdd" / "SKILL.md")}
    trust_before = (ws / ".hyodo" / "factory" / "trust_state.json").read_bytes()

    factory.analyze_capability_gaps(ws, GAP_PROMPT, external_search_roots=[ext])

    assert {p: p.read_bytes() for p in before} == before
    assert (ws / ".hyodo" / "factory" / "trust_state.json").read_bytes() == trust_before
