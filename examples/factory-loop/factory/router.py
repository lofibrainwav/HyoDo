"""Phase 2.4 — Natural Language Skill Router, Slot Deduplication & Progressive Disclosure.

Selects active skills from `.hyodo/factory/lock.json` based on natural-language
intent (Korean & English), profile constraints (`minimal`, `development`,
`design`, `research`), and optional zero-authority evaluator recommendations
(e.g. `JEV`), without loading full `SKILL.md` bodies until activation.
Enforces functional slot deduplication so overlapping skills (e.g., multiple
orchestrators or competing design/TDD skills) are never stacked blindly.
"""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib  # type: ignore[no-redef]
from typing import Any

from factory.contracts import ProfileSpec, SkillUnitSpec
from factory.registry import list_enabled_skills, load_registry_state

PROFILES_DIR = Path(__file__).resolve().parents[1] / "profiles"

_INTENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "simplification": (
        "\uadfc\ubcf8 \uc6d0\uc778",
        "\ubd84\uc11d",
        "\uac10\uc0ac",
        "\ubcf5\uc7a1\uc131",
        "\ub9ac\ud329\ud130\ub9c1",
        "\ub2e8\uc21c\ud654",
        "root cause",
        "audit",
        "simplify",
        "yagni",
        "refactor",
        "improve",
        "ponytail",
    ),
    "engineering": (
        "\uad6c\ud604",
        "\uc218\uc815",
        "\ubc84\uadf8",
        "\uc124\uacc4",
        "\ud14c\uc2a4\ud2b8",
        "\uc694\uad6c\uc0ac\ud56d",
        "build",
        "fix",
        "tdd",
        "feature",
        "implement",
        "architect",
        "debug",
    ),
    "design": (
        "ui",
        "ux",
        "\ub514\uc790\uc778",
        "\ub808\uc774\uc544\uc6c3",
        "\ube0c\ub79c\ub4dc",
        "\ud1a0\ud070",
        "\ud314\ub808\ud2b8",
        "design",
        "taste",
        "layout",
        "brand",
        "typography",
        "unslop",
    ),
    "craft": (
        "\uc560\ub2c8\uba54\uc774\uc158",
        "\ubaa8\uc158",
        "\uc778\ud130\ub799\uc158",
        "\ucef4\ud3ec\ub10c\ud2b8",
        "\ud654\uba74",
        "animation",
        "motion",
        "interaction",
        "component",
        "frontend",
    ),
    "quality": (
        "\uac80\uc99d",
        "\ub9ac\ubdf0",
        "\ube0c\ub77c\uc6b0\uc800",
        "\ud488\uc9c8",
        "qa",
        "review",
        "verify",
        "browser",
        "impeccable",
        "gatekeep",
        "\uac1c\uc120",
    ),
    "security": (
        "\ubcf4\uc548",
        "\ucde8\uc57d\uc810",
        "\uad8c\ud55c",
        "\uac00\ub4dc",
        "security",
        "vulnerability",
        "guard",
        "audit",
    ),
    "knowledge": (
        "\uadf8\ub798\ud504",
        "\uad6c\uc870",
        "\uc774\ud574",
        "\uad00\uacc4",
        "graph",
        "graphify",
        "understand",
        "how",
        "why",
    ),
    "research": (
        "\ub9ac\uc11c\uce58",
        "\ud2b8\ub80c\ub4dc",
        "\ubc1c\uad74",
        "\ucc3e\uae30",
        "research",
        "find-skills",
        "discover",
        "trend",
        "last30days",
    ),
    "evaluation": (
        "\ud3c9\uac00",
        "\ubca4\uce58\ub9c8\ud06c",
        "\ube44\uad50",
        "eval",
        "jev",
        "interrogate",
        "benchmark",
    ),
}


def load_profile(profile_name: str, profiles_dir: Path | None = None) -> ProfileSpec:
    """Load a declarative TOML profile (`minimal`, `development`, `design`, `research`)."""
    base = profiles_dir or PROFILES_DIR
    path = base / f"{profile_name}.toml"
    if not path.is_file():
        raise FileNotFoundError(f"unknown profile: {profile_name}")
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    return ProfileSpec(
        name=str(raw.get("name", profile_name)),
        description=str(raw.get("description", "")),
        active_categories=tuple(raw.get("active_categories", ())),
        preferred_skills=tuple(raw.get("preferred_skills", ())),
        excluded_skills=tuple(raw.get("excluded_skills", ())),
        single_orchestrator=bool(raw.get("single_orchestrator", True)),
        require_independent_verifier=bool(raw.get("require_independent_verifier", True)),
    )


def infer_intent_categories(prompt: str) -> list[str]:
    """Infer required Universal Skill Matrix categories from a natural-language request."""
    lowered = prompt.lower()
    matched: list[str] = []
    for category, keywords in _INTENT_KEYWORDS.items():
        if any(kw in lowered for kw in keywords):
            matched.append(category)
    if not matched:
        matched.append("engineering")
    if (
        "design" in matched or "craft" in matched or "engineering" in matched
    ) and "quality" not in matched:
        matched.append("quality")
    return matched


def _functional_slot(unit: SkillUnitSpec) -> str:
    """Return the functional deduplication slot for *unit*."""
    if unit.category == "orchestration":
        return "orchestration"
    if unit.design_stage in ("architect", "craft", "gatekeep"):
        return f"design:{unit.design_stage}"
    if unit.category == "engineering":
        low = f"{unit.name} {unit.description}".lower()
        if any(k in low for k in ("debug", "root-cause", "troubleshoot")):
            return "engineering:debug"
        if any(k in low for k in ("tdd", "test-driven")):
            return "engineering:tdd"
        if any(k in low for k in ("plan", "architect", "prd", "spec", "adr")):
            return "engineering:plan"
        if any(k in low for k in ("brainstorm", "grill", "office-hours", "ideat")):
            return "engineering:ideation"
        return f"engineering:{unit.role_hint}"
    return f"category:{unit.category}:{unit.role_hint}"


def _score_candidate(
    unit: SkillUnitSpec,
    prompt_lower: str,
    eval_recs: list[str],
    pref_set: set[str],
) -> tuple[int, int, int, int, str]:
    """Return a deterministic sort key (smaller is higher priority) for candidate ranking."""
    eval_idx = eval_recs.index(unit.skill_id) if unit.skill_id in eval_recs else 999
    is_pref = 0 if unit.skill_id in pref_set else 1
    explicit_mention = (
        0 if (unit.name.lower() in prompt_lower or unit.module_id.lower() in prompt_lower) else 1
    )
    haystack = f"{unit.name} {unit.description} {' '.join(unit.capabilities)}".lower()
    prompt_words = [w for w in prompt_lower.replace("/", " ").split() if len(w) >= 2]
    kw_hits = sum(1 for w in prompt_words if w in haystack)
    return (eval_idx, is_pref, explicit_mention, -kw_hits, unit.skill_id)


def route_skills_for_task(
    workspace_root: Path,
    prompt: str,
    *,
    profile_name: str | None = None,
    evaluator_recommendations: list[str] | None = None,
    deduplicate_by_slot: bool = True,
) -> dict[str, Any]:
    """Select active, non-conflicting skills for *prompt* without disclosing full bodies yet.

    Enforces:
    - Progressive Disclosure (`bodies_disclosed == 0` during routing).
    - Single orchestrator guard (`orchestrator_collision_avoided`).
    - Functional slot deduplication (`deduplicated_skills`) so identical-role
      skills from multiple repositories are not stacked simultaneously unless
      explicitly requested or required as a dependency.
    """
    inferred_cats = infer_intent_categories(prompt)
    profile = load_profile(profile_name) if profile_name else None
    allowed_cats = (
        set(inferred_cats) | set(profile.active_categories)
        if profile is not None
        else set(inferred_cats)
    )

    enabled_units = list_enabled_skills(workspace_root)
    modules = load_registry_state(workspace_root)
    by_id = {u.skill_id: u for u in enabled_units}

    eval_recs = list(evaluator_recommendations or [])
    pref_set = set(profile.preferred_skills) if profile else set()
    excl_set = set(profile.excluded_skills) if profile else set()
    prompt_lower = prompt.lower()

    selected: list[SkillUnitSpec] = []
    selected_ids: set[str] = set()
    orchestrator_chosen: str | None = None
    slot_winners: dict[str, str] = {}
    conflicts_skipped: list[str] = []
    deduplicated_skills: list[str] = []

    def _try_add(unit: SkillUnitSpec, *, is_dependency: bool = False) -> None:
        nonlocal orchestrator_chosen
        if unit.skill_id in selected_ids or unit.skill_id in excl_set:
            return
        if (
            not is_dependency
            and unit.disable_model_invocation
            and unit.skill_id not in eval_recs
            and unit.skill_id not in pref_set
            and unit.name.lower() not in prompt_lower
        ):
            deduplicated_skills.append(f"model_invocation_disabled:{unit.skill_id}")
            return
        if (profile is None or profile.single_orchestrator) and unit.category == "orchestration":
            if orchestrator_chosen is not None and orchestrator_chosen != unit.module_id:
                conflicts_skipped.append(f"orchestrator_collision_avoided:{unit.skill_id}")
                return
            orchestrator_chosen = unit.module_id
        for active_id in selected_ids:
            active_u = by_id.get(active_id)
            if active_u and (
                active_id in unit.conflicts_with or unit.skill_id in active_u.conflicts_with
            ):
                conflicts_skipped.append(f"conflict_avoided:{unit.skill_id}<->{active_id}")
                return

        slot = _functional_slot(unit)
        explicitly_pinned = (
            is_dependency
            or unit.skill_id in eval_recs
            or unit.skill_id in pref_set
            or unit.skill_id.lower() in prompt_lower
        )
        if deduplicate_by_slot and not explicitly_pinned and slot in slot_winners:
            winner = slot_winners[slot]
            deduplicated_skills.append(
                f"redundant_slot_skipped:{unit.skill_id}(slot={slot},winner={winner})"
            )
            return

        for dep_id in unit.dependencies:
            dep_unit = by_id.get(dep_id)
            if dep_unit is not None and dep_id not in selected_ids:
                _try_add(dep_unit, is_dependency=True)

        selected.append(unit)
        selected_ids.add(unit.skill_id)
        if slot not in slot_winners:
            slot_winners[slot] = unit.skill_id

    candidates = [
        u
        for u in enabled_units
        if u.category in allowed_cats or u.skill_id in pref_set or u.skill_id in eval_recs
    ]
    candidates.sort(key=lambda u: _score_candidate(u, prompt_lower, eval_recs, pref_set))

    for unit in candidates:
        _try_add(unit)

    builders = [u.skill_id for u in selected if u.role_hint in ("builder", "router")]
    verifiers = [u.skill_id for u in selected if u.role_hint == "verifier"]
    evaluators = [
        u.skill_id for u in selected if u.role_hint == "observer" or u.category == "evaluation"
    ]
    design_pipeline = {
        stage: [u.skill_id for u in selected if u.design_stage == stage]
        for stage in ("architect", "craft", "gatekeep")
    }

    return {
        "prompt": prompt,
        "profile": profile.name if profile else "auto",
        "inferred_categories": inferred_cats,
        "selected_skills": [u.skill_id for u in selected],
        "builders": builders,
        "verifiers": verifiers,
        "evaluators": evaluators,
        "design_pipeline": design_pipeline,
        "slot_winners": slot_winners,
        "conflicts_skipped": conflicts_skipped,
        "deduplicated_skills": deduplicated_skills,
        "bodies_disclosed": 0,  # Progressive Disclosure: 0 bodies loaded during routing!
        "modules_available": len(modules),
    }
