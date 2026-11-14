"""Phase 2.4 — Natural Language Skill Router, Slot Deduplication & Progressive Disclosure.

Selects active skills from `.hyodo/factory/lock.json` based on natural-language
intent (Korean & English), host-configured Personal Taste rules, preflight
capability-gap / doctor health diagnostics, profile constraints (`minimal`,
`development`, `design`, `research`), and optional zero-authority evaluator
recommendations (e.g. `JEV`), without loading full `SKILL.md` bodies until
activation.
Enforces functional slot deduplication and task-scoped selective activation so
170+ registered skills never need to be enabled globally all at once.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib  # type: ignore[no-redef]
from typing import Any

from factory.contracts import (
    CAPABILITY_STATES,
    GAP_ROOT_CAUSES,
    HOST_TASTE_REL_PATH,
    ProfileSpec,
    SkillUnitSpec,
)
from factory.lifecycle import activate_selected_skills, discover_skills, doctor
from factory.registry import list_enabled_skills, load_registry_state
from hyodo.admission_observation import ADMISSION_OBSERVATIONS_RELATIVE_PATH
from hyodo.connector_contract import build_connector_contract
from hyodo.continuity import measure_continuity
from hyodo.host_promise_observation import load_host_promise_observation
from hyodo.orchestration_observation import read_orchestration_observations
from hyodo.policy_trust import SCOPE_POLICY_ASK, load_policy_trust

PROFILES_DIR = Path(__file__).resolve().parents[1] / "profiles"
TRUST_STATE_REL_PATH = Path(".hyodo") / "factory" / "trust_state.json"

_TASTE_STOP_WORDS = frozenset(
    {
        "the",
        "and",
        "for",
        "with",
        "over",
        "prefer",
        "avoid",
        "forbid",
        "only",
        "when",
        "rule",
        "explicit",
        "host",
        "from",
        "that",
        "this",
        "use",
    }
)

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
        personal_taste_rules=tuple(raw.get("personal_taste_rules", ())),
        inferred_taste_hypotheses=tuple(raw.get("inferred_taste_hypotheses", ())),
        domain_taste_focus=tuple(raw.get("domain_taste_focus", ())),
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


def load_host_taste_config(workspace_root: Path) -> dict[str, Any]:
    """Load optional host-owned Personal Taste state from `.hyodo/factory/host_taste.json`.

    Personal Taste lives exclusively on the host side and is never hardcoded in `hyodo/`.
    """
    path = workspace_root / HOST_TASTE_REL_PATH
    if not path.is_file() or path.is_symlink():
        return {
            "present": False,
            "rules": [],
            "prefer_skills": [],
            "avoid_skills": [],
            "prefer_terms": [],
        }
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {
            "present": False,
            "rules": [],
            "prefer_skills": [],
            "avoid_skills": [],
            "prefer_terms": [],
        }
    if not isinstance(raw, dict):
        return {
            "present": False,
            "rules": [],
            "prefer_skills": [],
            "avoid_skills": [],
            "prefer_terms": [],
        }
    return {
        "present": True,
        "rules": [str(r) for r in raw.get("rules", []) if str(r).strip()],
        "prefer_skills": [str(s) for s in raw.get("prefer_skills", []) if str(s).strip()],
        "avoid_skills": [str(s) for s in raw.get("avoid_skills", []) if str(s).strip()],
        "prefer_terms": [str(t) for t in raw.get("prefer_terms", []) if str(t).strip()],
    }


def _collect_effective_taste(
    workspace_root: Path,
    profile: ProfileSpec | None,
    explicit_taste_feedback: list[str] | None,
) -> dict[str, Any]:
    host_cfg = load_host_taste_config(workspace_root)
    explicit_rules: list[str] = []
    if profile is not None:
        explicit_rules.extend(profile.personal_taste_rules)
    explicit_rules.extend(host_cfg["rules"])
    for skill in host_cfg["prefer_skills"]:
        explicit_rules.append(f"prefer:{skill}")
    for skill in host_cfg["avoid_skills"]:
        explicit_rules.append(f"avoid:{skill}")
    for term in host_cfg["prefer_terms"]:
        explicit_rules.append(f"prefer_term:{term}")
    if explicit_taste_feedback:
        explicit_rules.extend(str(r) for r in explicit_taste_feedback if str(r).strip())

    # Deduplicate while preserving deterministic order
    seen_rules: list[str] = []
    for r in explicit_rules:
        if r not in seen_rules:
            seen_rules.append(r)

    prefer_tokens: list[str] = []
    avoid_tokens: list[str] = []
    boost_keywords: set[str] = set()
    for rule in seen_rules:
        low = rule.strip().lower()
        if low.startswith(("prefer:", "prefer_skill:", "explicit_prefer:")):
            tok = low.split(":", 1)[1].strip()
            if tok and tok not in prefer_tokens:
                prefer_tokens.append(tok)
        elif low.startswith(("prefer_term:",)):
            tok = low.split(":", 1)[1].strip()
            if tok:
                boost_keywords.add(tok)
        elif low.startswith(("avoid:", "avoid_skill:", "forbid:", "explicit_avoid:")):
            tok = low.split(":", 1)[1].strip()
            if tok and tok not in avoid_tokens:
                avoid_tokens.append(tok)
        else:
            _, has_colon, body = low.partition(":")
            phrase = body.strip() if has_colon else low
            if "prefer " in phrase and " over " in phrase:
                preferred_part = phrase.split(" over ", 1)[0].split("prefer ", 1)[1]
                for word in re.findall(r"[a-z0-9_/-]{3,}", preferred_part):
                    if word not in _TASTE_STOP_WORDS:
                        boost_keywords.add(word)
            else:
                for word in re.findall(r"[a-z0-9_/-]{3,}", phrase):
                    if word not in _TASTE_STOP_WORDS:
                        boost_keywords.add(word)

    return {
        "host_taste_file_present": host_cfg["present"],
        "rules": seen_rules,
        "prefer_tokens": prefer_tokens,
        "avoid_tokens": avoid_tokens,
        "boost_keywords": sorted(boost_keywords),
    }


def _unit_matches_taste_token(unit: SkillUnitSpec, token: str) -> bool:
    low = token.lower().strip()
    if not low:
        return False
    return low in (
        unit.skill_id.lower(),
        unit.name.lower(),
        unit.module_id.lower(),
        unit.category.lower(),
    ) or any(low == cap.lower() for cap in unit.capabilities)


def _extract_doctor_diagnostics(
    workspace_root: Path,
    doctor_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rep = doctor_report if doctor_report is not None else doctor(workspace_root)
    degraded_ids: set[str] = set()
    degraded_modules: set[str] = set()
    conflict_ids: set[str] = set()
    silent_zero_ids: set[str] = set()
    silent_zero_details: dict[str, str] = {}

    for prob in rep.get("problems", []):
        if prob.startswith("missing_module_source:"):
            parts = prob.split(":")
            if len(parts) >= 2:
                degraded_modules.add(parts[1])
        elif prob.startswith("active_conflict:"):
            pair = prob.split(":", 1)[1]
            for sid in pair.split("<->"):
                if sid:
                    conflict_ids.add(sid)
        elif prob.startswith(
            (
                "incompatible_python_syntax:",
                "content_hash_drift:",
                "missing_or_symlink_skill_file:",
                "unmet_dependency:",
            )
        ):
            parts = prob.split(":")
            if len(parts) >= 2:
                sid = parts[1].split("->")[0]
                degraded_ids.add(sid)

    for warn in rep.get("warnings", []):
        if warn.startswith("unverified_hook_silent_zero:"):
            parts = warn.split(":")
            if len(parts) >= 2:
                sid = parts[1]
                silent_zero_ids.add(sid)
                if "script_present=" in warn:
                    silent_zero_details[sid] = "HOST_ENV_UNBOUND_SILENT_ZERO_FALLBACK"
                else:
                    silent_zero_details[sid] = "HOOK_SCRIPT_MISSING_SILENT_ZERO"

    return {
        "doctor_report": rep,
        "degraded_ids": degraded_ids,
        "degraded_modules": degraded_modules,
        "conflict_ids": conflict_ids,
        "silent_zero_ids": silent_zero_ids,
        "silent_zero_details": silent_zero_details,
    }


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


def _trust_priority_rank(
    unit: SkillUnitSpec,
    trust_map: dict[str, dict[str, Any]],
) -> int:
    rec = trust_map.get(unit.skill_id)
    if not isinstance(rec, dict):
        return 9
    if rec.get("content_sha256") != unit.content_sha256:
        return 9
    if rec.get("verifier_status") != "PASS":
        return 9
    ranks = {"AUTO_RUN": 0, "TRUSTED": 1, "SHADOW": 2, "MANUAL": 3}
    return ranks.get(str(rec.get("trust_stage", "")), 9)


def _score_candidate(
    unit: SkillUnitSpec,
    prompt_lower: str,
    eval_recs: list[str],
    pref_set: set[str],
    trust_map: dict[str, dict[str, Any]] | None = None,
    taste_info: dict[str, Any] | None = None,
    silent_zero_ids: set[str] | None = None,
) -> tuple[int, int, int, int, int, int, int, str]:
    """Return a deterministic sort key (smaller is higher priority) for candidate ranking."""
    eval_idx = eval_recs.index(unit.skill_id) if unit.skill_id in eval_recs else 999
    taste_prefers = (taste_info or {}).get("prefer_tokens", [])
    taste_prefer_rank = (
        0 if any(_unit_matches_taste_token(unit, tok) for tok in taste_prefers) else 1
    )
    is_pref = 0 if unit.skill_id in pref_set else 1
    explicit_mention = (
        0 if (unit.name.lower() in prompt_lower or unit.module_id.lower() in prompt_lower) else 1
    )
    pinned = (
        unit.skill_id in eval_recs
        or taste_prefer_rank == 0
        or unit.skill_id in pref_set
        or explicit_mention == 0
    )
    silent_zero_rank = 1 if (unit.skill_id in (silent_zero_ids or set()) and not pinned) else 0
    trust_rank = _trust_priority_rank(unit, trust_map or {})
    haystack = f"{unit.name} {unit.description} {' '.join(unit.capabilities)}".lower()
    prompt_words = [w for w in prompt_lower.replace("/", " ").split() if len(w) >= 2]
    kw_hits = sum(1 for w in prompt_words if w in haystack)
    boost_kws = (taste_info or {}).get("boost_keywords", [])
    taste_kw_hits = sum(2 for kw in boost_kws if kw in haystack)
    return (
        eval_idx,
        taste_prefer_rank,
        is_pref,
        explicit_mention,
        silent_zero_rank,
        trust_rank,
        -(kw_hits + taste_kw_hits),
        unit.skill_id,
    )


def route_skills_for_task(
    workspace_root: Path,
    prompt: str,
    *,
    profile_name: str | None = None,
    evaluator_recommendations: list[str] | None = None,
    deduplicate_by_slot: bool = True,
    explicit_taste_feedback: list[str] | None = None,
    include_registered_inactive: bool = False,
    degraded_skill_ids: set[str] | None = None,
    silent_zero_skill_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Select active, non-conflicting skills for *prompt* without disclosing full bodies yet.

    Enforces:
    - Progressive Disclosure (`bodies_disclosed == 0` during routing).
    - Personal Taste causal routing (`taste_applied`: explicit rules/feedback boost or exclude).
    - Preflight `doctor()` health enforcement (`degraded_skipped`).
    - Single orchestrator guard (`orchestrator_collision_avoided`).
    - Functional slot deduplication (`deduplicated_skills`).
    """
    inferred_cats = infer_intent_categories(prompt)
    profile = load_profile(profile_name) if profile_name else None
    allowed_cats = (
        set(inferred_cats) | set(profile.active_categories)
        if profile is not None
        else set(inferred_cats)
    )

    modules = load_registry_state(workspace_root)
    enabled_units = list_enabled_skills(workspace_root)
    enabled_ids = {u.skill_id for u in enabled_units}
    all_units = [
        u
        for m in sorted(modules.values(), key=lambda x: x.module_id)
        for u in sorted(m.skills.values(), key=lambda s: s.skill_id)
    ]
    pool_units = all_units if include_registered_inactive else enabled_units

    trust_map = _load_trust_ledger_map(workspace_root)
    by_id = {u.skill_id: u for u in pool_units}

    if degraded_skill_ids is None or silent_zero_skill_ids is None:
        diag = _extract_doctor_diagnostics(workspace_root)
        eff_degraded = set(diag["degraded_ids"]) | {
            u.skill_id for u in pool_units if u.module_id in diag["degraded_modules"]
        }
        eff_silent_zero = set(diag["silent_zero_ids"])
    else:
        eff_degraded = set(degraded_skill_ids)
        eff_silent_zero = set(silent_zero_skill_ids)

    taste_info = _collect_effective_taste(workspace_root, profile, explicit_taste_feedback)
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
    degraded_skipped: list[str] = []
    taste_excluded: list[str] = []
    taste_preferred_selected: list[str] = []

    def _try_add(unit: SkillUnitSpec, *, is_dependency: bool = False) -> None:
        nonlocal orchestrator_chosen
        if unit.skill_id in selected_ids or unit.skill_id in excl_set:
            return
        if unit.skill_id in eff_degraded:
            degraded_skipped.append(f"degraded_skipped:{unit.skill_id}")
            return
        matched_avoid = [
            tok for tok in taste_info["avoid_tokens"] if _unit_matches_taste_token(unit, tok)
        ]
        if matched_avoid and unit.skill_id not in eval_recs:
            taste_excluded.append(f"taste_excluded:{unit.skill_id}:avoid={matched_avoid[0]}")
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
                if dep_unit.skill_id in eff_degraded:
                    degraded_skipped.append(
                        f"degraded_dependency_blocked:{unit.skill_id}->{dep_unit.skill_id}"
                    )
                    return
                _try_add(dep_unit, is_dependency=True)

        selected.append(unit)
        selected_ids.add(unit.skill_id)
        if any(_unit_matches_taste_token(unit, tok) for tok in taste_info["prefer_tokens"]):
            taste_preferred_selected.append(unit.skill_id)
        if slot not in slot_winners:
            slot_winners[slot] = unit.skill_id

    candidates = [
        u
        for u in pool_units
        if u.category in allowed_cats
        or u.skill_id in pref_set
        or u.skill_id in eval_recs
        or any(_unit_matches_taste_token(u, tok) for tok in taste_info["prefer_tokens"])
    ]
    candidates.sort(
        key=lambda u: _score_candidate(
            u,
            prompt_lower,
            eval_recs,
            pref_set,
            trust_map,
            taste_info=taste_info,
            silent_zero_ids=eff_silent_zero,
        )
    )

    for unit in candidates:
        _try_add(unit)

    selected_ids_ordered = [u.skill_id for u in selected]
    needs_activation = [sid for sid in selected_ids_ordered if sid not in enabled_ids]
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
        "selected_skills": selected_ids_ordered,
        "needs_activation": needs_activation,
        "builders": builders,
        "verifiers": verifiers,
        "evaluators": evaluators,
        "design_pipeline": design_pipeline,
        "slot_winners": slot_winners,
        "conflicts_skipped": conflicts_skipped,
        "degraded_skipped": degraded_skipped,
        "deduplicated_skills": deduplicated_skills,
        "taste_applied": {
            "host_taste_file_present": taste_info["host_taste_file_present"],
            "explicit_rules_count": len(taste_info["rules"]),
            "prefer_tokens": taste_info["prefer_tokens"],
            "avoid_tokens": taste_info["avoid_tokens"],
            "boost_keywords": taste_info["boost_keywords"],
            "taste_preferred_selected": taste_preferred_selected,
            "taste_excluded": taste_excluded,
        },
        "bodies_disclosed": 0,  # Progressive Disclosure: 0 bodies loaded during routing!
        "modules_available": len(modules),
        "total_registered_skills": len(all_units),
        "active_skills_count": len(enabled_units),
    }


def select_and_activate_for_task(
    workspace_root: Path,
    prompt: str,
    *,
    profile_name: str | None = None,
    evaluator_recommendations: list[str] | None = None,
    explicit_taste_feedback: list[str] | None = None,
    deduplicate_by_slot: bool = True,
    disable_others: bool = True,
) -> dict[str, Any]:
    """Select only task-needed skills across all registered modules (even lazy/dormant ones) and activate them atomically."""
    modules = load_registry_state(workspace_root)
    degraded_ids: set[str] = set()
    # Pre-check disk hash integrity even on dormant modules so tampered dormant skills are never activated
    for mod in modules.values():
        mod_root = Path(mod.source_path)
        if not mod_root.is_dir():
            degraded_ids.update(mod.skills)
            continue
        for sid, unit in mod.skills.items():
            target = mod_root / unit.relative_path
            if target.is_symlink() or not target.is_file():
                degraded_ids.add(sid)
                continue
            try:
                if hashlib.sha256(target.read_bytes()).hexdigest() != unit.content_sha256:
                    degraded_ids.add(sid)
            except OSError:
                degraded_ids.add(sid)

    plan = route_skills_for_task(
        workspace_root,
        prompt,
        profile_name=profile_name,
        evaluator_recommendations=evaluator_recommendations,
        deduplicate_by_slot=deduplicate_by_slot,
        explicit_taste_feedback=explicit_taste_feedback,
        include_registered_inactive=True,
        degraded_skill_ids=degraded_ids,
    )
    activated = activate_selected_skills(
        workspace_root,
        plan["selected_skills"],
        disable_others=disable_others,
    )
    total_skills = sum(len(m.skills) for m in modules.values())
    return {
        "route_plan": plan,
        "activated_skills": activated,
        "active_skills_count": len(activated),
        "dormant_skills_count": max(0, total_skills - len(activated)),
        "total_registered_skills": total_skills,
    }


def _load_trust_ledger_map(workspace_root: Path) -> dict[str, dict[str, Any]]:
    path = workspace_root / TRUST_STATE_REL_PATH
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    skills = raw.get("skills", {})
    return skills if isinstance(skills, dict) else {}


def analyze_capability_gaps(
    workspace_root: Path,
    prompt: str,
    *,
    profile_name: str | None = None,
    external_search_roots: list[Path] | None = None,
    explicit_taste_feedback: list[str] | None = None,
    inferred_taste_hypotheses: list[str] | None = None,
) -> dict[str, Any]:
    """Compare task requirements against verified capabilities (`知己 -> 知彼 -> 差異`).

    Classifies skills and required categories into the 6 canonical states
    (`VERIFIED`, `UNVERIFIED`, `MISSING`, `DEGRADED`, `REDUNDANT`, `UNKNOWN`)
    with explicit root-cause attribution (`NONE`, `CAPABILITY_MISSING`,
    `WIRING_DISCONNECTED`, `VERIFICATION_MISSING`,
    `ENVIRONMENT_OR_SYNTAX_DEGRADED`, `DUPLICATE_SLOT`), while separating
    task-scoped wiring gaps from intentionally dormant out-of-scope skills.
    """
    inferred_cats = infer_intent_categories(prompt)
    profile = load_profile(profile_name) if profile_name else load_profile("development")
    modules = load_registry_state(workspace_root)
    doctor_report = doctor(workspace_root)
    diag = _extract_doctor_diagnostics(workspace_root, doctor_report=doctor_report)
    doctor_issues = list(doctor_report.get("problems", [])) + list(
        doctor_report.get("warnings", [])
    )
    route_plan = route_skills_for_task(
        workspace_root,
        prompt,
        profile_name=profile_name,
        explicit_taste_feedback=explicit_taste_feedback,
        degraded_skill_ids=diag["degraded_ids"],
        silent_zero_skill_ids=diag["silent_zero_ids"],
    )
    selective_preview = route_skills_for_task(
        workspace_root,
        prompt,
        profile_name=profile_name,
        explicit_taste_feedback=explicit_taste_feedback,
        include_registered_inactive=True,
        degraded_skill_ids=diag["degraded_ids"],
        silent_zero_skill_ids=diag["silent_zero_ids"],
    )
    trust_map = _load_trust_ledger_map(workspace_root)

    # Check if simple task fast-path applies (avoid unnecessary metacognitive overhead)
    word_count = len(prompt.strip().split())
    enabled_cats = {
        unit.category
        for mod in modules.values()
        if mod.enabled
        for unit in mod.skills.values()
        if unit.enabled
    }
    missing_cats_initial = [c for c in inferred_cats if c not in enabled_cats]
    is_simple_task = word_count <= 6 and len(inferred_cats) <= 2 and not missing_cats_initial
    metacognition_mode = "FAST_PATH_SIMPLE_TASK" if is_simple_task else "FULL_METACOGNITIVE_LOOP"

    dedup_entries = list(route_plan.get("deduplicated_skills", []))
    conflict_entries = list(route_plan.get("conflicts_skipped", []))
    task_scope_cats = set(inferred_cats)

    skill_assessments: dict[str, dict[str, Any]] = {}
    dormant_out_of_scope_count = 0
    for mod_id, mod in sorted(modules.items()):
        for skill_id, unit in sorted(mod.skills.items()):
            in_task_scope = (
                unit.category in task_scope_cats or skill_id in route_plan["selected_skills"]
            )
            has_doctor_issue = (
                any(
                    f":{skill_id}" in issue
                    or f":{mod_id}:" in issue
                    or issue.endswith(f":{mod_id}")
                    for issue in doctor_issues
                )
                or skill_id in diag["degraded_ids"]
                or mod_id in diag["degraded_modules"]
            )
            is_redundant_slot = any(
                f"redundant_slot_skipped:{skill_id}(" in entry for entry in dedup_entries
            ) or any(f":{skill_id}" in entry for entry in conflict_entries)
            t_rec = trust_map.get(skill_id)
            drift_detected = False
            if isinstance(t_rec, dict) and (
                t_rec.get("content_sha256") != unit.content_sha256
                or t_rec.get("version") != mod.version
                or t_rec.get("boundary") != unit.boundary.to_dict()
            ):
                drift_detected = True

            dormant_out_of_scope = False
            if has_doctor_issue:
                state = "DEGRADED"
                root_cause = "ENVIRONMENT_OR_SYNTAX_DEGRADED"
                trust_stage = "VERIFY"
            elif not mod.enabled or not unit.enabled:
                if in_task_scope:
                    state = "UNVERIFIED"
                    root_cause = "WIRING_DISCONNECTED"
                    trust_stage = "DISCOVER"
                else:
                    dormant_out_of_scope = True
                    dormant_out_of_scope_count += 1
                    state = "UNVERIFIED"
                    root_cause = "NONE"
                    trust_stage = "DISCOVER"
            elif is_redundant_slot:
                state = "REDUNDANT"
                root_cause = "DUPLICATE_SLOT"
                trust_stage = (
                    str(t_rec.get("trust_stage", "VERIFY"))
                    if isinstance(t_rec, dict) and not drift_detected
                    else "VERIFY"
                )
            elif isinstance(t_rec, dict) and not drift_detected:
                trust_stage = str(t_rec.get("trust_stage", "VERIFY"))
                v_status = str(t_rec.get("verifier_status", "UNOBSERVED"))
                e_verdict = str(t_rec.get("eval_verdict", "UNOBSERVED"))
                if v_status == "UNKNOWN" or e_verdict == "INCONCLUSIVE":
                    state = "UNKNOWN"
                    root_cause = "VERIFICATION_MISSING"
                elif v_status == "PASS" and trust_stage in (
                    "MANUAL",
                    "SHADOW",
                    "TRUSTED",
                    "AUTO_RUN",
                ):
                    state = "VERIFIED"
                    root_cause = "NONE"
                else:
                    state = "UNVERIFIED"
                    root_cause = "VERIFICATION_MISSING"
            else:
                state = "UNVERIFIED"
                root_cause = "VERIFICATION_MISSING"
                trust_stage = "VERIFY"

            assert state in CAPABILITY_STATES
            assert root_cause in GAP_ROOT_CAUSES
            item: dict[str, Any] = {
                "skill_id": skill_id,
                "module_id": mod_id,
                "category": unit.category,
                "in_task_scope": in_task_scope,
                "dormant_out_of_scope": dormant_out_of_scope,
                "state": state,
                "root_cause": root_cause,
                "trust_stage": trust_stage,
                "drift_detected": drift_detected,
                "selected_for_task": skill_id in route_plan["selected_skills"],
            }
            if skill_id in diag["silent_zero_details"]:
                item["hook_root_cause"] = diag["silent_zero_details"][skill_id]
            skill_assessments[skill_id] = item

    category_assessments: dict[str, dict[str, Any]] = {}
    external_candidates: dict[str, list[dict[str, Any]]] = {}
    for cat in inferred_cats:
        cat_skills = [info for info in skill_assessments.values() if info["category"] == cat]
        if not cat_skills:
            c_state = "MISSING"
            c_cause = "CAPABILITY_MISSING"
            if external_search_roots and not is_simple_task:
                found = discover_skills(external_search_roots, query=cat)
                if not found:
                    cat_kws = _INTENT_KEYWORDS.get(cat, (cat,))
                    found = [
                        item
                        for item in discover_skills(external_search_roots)
                        if any(
                            kw
                            in f"{item.get('name', '')} {' '.join(item.get('sample_skills', []))}".lower()
                            for kw in cat_kws
                        )
                    ]
                external_candidates[cat] = found

        elif all(s["state"] == "DEGRADED" for s in cat_skills):
            c_state = "DEGRADED"
            c_cause = "ENVIRONMENT_OR_SYNTAX_DEGRADED"
        elif all(s["root_cause"] == "WIRING_DISCONNECTED" for s in cat_skills):
            c_state = "UNVERIFIED"
            c_cause = "WIRING_DISCONNECTED"
        elif any(s["state"] == "VERIFIED" for s in cat_skills):
            c_state = "VERIFIED"
            c_cause = "NONE"
        elif any(s["state"] == "UNKNOWN" for s in cat_skills):
            c_state = "UNKNOWN"
            c_cause = "VERIFICATION_MISSING"
        else:
            c_state = "UNVERIFIED"
            c_cause = "VERIFICATION_MISSING"

        category_assessments[cat] = {
            "category": cat,
            "state": c_state,
            "root_cause": c_cause,
            "registered_skills": [s["skill_id"] for s in cat_skills],
            "external_candidates_count": len(external_candidates.get(cat, [])),
        }

    # System Awareness (Bridge M5-B + Cross-host continuity + PolicyTrust + HostPromise + Sidecars)
    connector = build_connector_contract(workspace_root)
    continuity = measure_continuity(workspace_root)
    policy_trust_state, policy_trust_err = load_policy_trust(workspace_root, scope=SCOPE_POLICY_ASK)
    host_promise = load_host_promise_observation(workspace_root)
    orch_rows = read_orchestration_observations(workspace_root)
    adm_path = workspace_root / ADMISSION_OBSERVATIONS_RELATIVE_PATH
    adm_count = 0
    if adm_path.is_file():
        with adm_path.open("r", encoding="utf-8") as handle:
            adm_count = sum(1 for line in handle if line.strip())

    wiring_gaps: list[str] = []
    if len(orch_rows) == 0:
        wiring_gaps.append("orchestration_sidecar_unobserved")
    if adm_count == 0:
        wiring_gaps.append("admission_ledger_unobserved")
    for sid, info in skill_assessments.items():
        if info["root_cause"] == "WIRING_DISCONNECTED":
            wiring_gaps.append(f"skill_disabled:{sid}")

    # Taste x Metacognition synthesis
    taste_info = _collect_effective_taste(workspace_root, profile, explicit_taste_feedback)
    hypotheses = list(profile.inferred_taste_hypotheses) + list(inferred_taste_hypotheses or [])
    taste_synthesis = {
        "personal_taste": [
            {
                "rule": rule,
                "source": "explicit_user_rule_or_feedback",
                "hypothesis": False,
                "authority": "HOST_CONFIGURED",
            }
            for rule in taste_info["rules"]
        ],
        "professional_taste": {
            "domain_focus": list(profile.domain_taste_focus),
            "active_taste_skills": [
                sid
                for sid in route_plan["selected_skills"]
                if skill_assessments.get(sid, {}).get("category")
                in ("design", "craft", "simplification", "engineering", "quality")
            ],
            "design_pipeline": route_plan["design_pipeline"],
            "source": "external_professional_skill",
            "hypothesis": False,
        },
        "inferred_hypotheses": [
            {
                "preference": hyp,
                "source": "ai_inferred_preference",
                "hypothesis": True,
                "authority": "UNOBSERVED",
                "must_yield_to_explicit_feedback": True,
                "overridden_by_explicit": any(
                    tok in hyp.lower()
                    for tok in (*taste_info["prefer_tokens"], *taste_info["avoid_tokens"])
                ),
            }
            for hyp in hypotheses
        ],
        "taste_applied_to_routing": route_plan["taste_applied"],
        "hardcoded_in_hyodo_core": False,
    }

    state_counts = {
        st: sum(1 for info in skill_assessments.values() if info["state"] == st)
        for st in CAPABILITY_STATES
    }
    task_scoped_state_counts = {
        st: sum(
            1
            for info in skill_assessments.values()
            if info["in_task_scope"] and not info["dormant_out_of_scope"] and info["state"] == st
        )
        for st in CAPABILITY_STATES
    }

    return {
        "schema": "hyodo.capability-gap-report/v1",
        "prompt": prompt,
        "profile": profile.name,
        "metacognition_mode": metacognition_mode,
        "is_simple_task": is_simple_task,
        "inferred_categories": inferred_cats,
        "state_counts": state_counts,
        "task_scoped_state_counts": task_scoped_state_counts,
        "dormant_out_of_scope_count": dormant_out_of_scope_count,
        "active_skills_count": route_plan["active_skills_count"],
        "total_registered_skills": route_plan["total_registered_skills"],
        "category_assessments": category_assessments,
        "skill_assessments": skill_assessments,
        "hook_diagnostics": diag["silent_zero_details"],
        "external_candidates": external_candidates,
        "taste_synthesis": taste_synthesis,
        "system_awareness": {
            "connector_overall_status": connector.get("overall_status", "UNOBSERVED"),
            "connector_summary": connector.get("summary", {}),
            "continuity_status": continuity.get("status", "UNOBSERVED"),
            "continuity_value": continuity.get("value"),
            "policy_trust_status": "GRANTED"
            if policy_trust_state is not None
            else (policy_trust_err or "UNOBSERVED"),
            "host_promise_status": (host_promise or {}).get("state", "NONE_SUPPLIED"),
            "orchestration_observations_count": len(orch_rows),
            "admission_observations_count": adm_count,
            "wiring_gaps": wiring_gaps,
        },
        "route_plan": route_plan,
        "selective_route_preview": selective_preview["selected_skills"],
    }
