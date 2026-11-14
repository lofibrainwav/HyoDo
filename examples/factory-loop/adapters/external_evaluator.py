"""Phase 2.2 — Generic External Evaluator adapter (`external-evaluator`).

Connects zero-authority evaluation engines (such as `jev-private-worker`,
`Cloudflare Security Audit`, or `pstack/interrogate`) to the Factory Harness
and HyoDo Core without coupling HyoDo to any specific evaluator repository.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from factory.contracts import ModuleRecord, PermissionBoundary, SkillUnitSpec

from adapters.agent_skills import (
    _ensure_safe_subpath,
    _git_head_sha,
    detect_repo_license,
    detect_repo_version,
    discover_skill_files,
    parse_skill_unit,
)
from hyodo.events import (
    append_agent_event,
    content_digest,
    strip_full_bodies,
    validate_event,
)
from hyodo.skills import (
    NODE_RETRIEVAL_SCHEMA,
    load_manifest,
    node_manifest_entry,
    node_rules_for,
    save_manifest,
    validate_node_retrieval,
)


def load_external_evaluator_module(
    source_path: Path,
    *,
    module_id: str | None = None,
    version: str | None = None,
) -> ModuleRecord:
    """Discover evaluation lanes/workers or skill specs inside *source_path*."""
    root = source_path.resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"evaluator source must be a directory: {source_path}")
    mod_id = (module_id or root.name).strip().lower().replace(" ", "-")
    resolved_version = version or detect_repo_version(root)
    license_spdx = detect_repo_license(root)

    skills: dict[str, SkillUnitSpec] = {}
    tree_hasher = hashlib.sha256()

    worker_files = sorted(root.glob("*_worker.py"))
    if worker_files:
        for wfile in worker_files:
            if wfile.is_symlink() or not wfile.is_file():
                continue
            rel = _ensure_safe_subpath(root, wfile)
            sha = hashlib.sha256(wfile.read_bytes()).hexdigest()
            lane_name = wfile.stem.replace("_worker", "").replace("_", "-")
            skill_id = f"{mod_id}/{lane_name}"
            role_hint = "router" if "skillid" in lane_name else "observer"
            unit = SkillUnitSpec(
                skill_id=skill_id,
                name=lane_name,
                module_id=mod_id,
                category="evaluation",
                adapter="external-evaluator",
                relative_path=rel,
                content_sha256=sha,
                enabled=True,
                description=f"Zero-authority external evaluator lane ({lane_name})",
                role_hint=role_hint,
                capabilities=("evaluation", lane_name, role_hint),
                executable_scripts=(rel,),
                boundary=PermissionBoundary(
                    filesystem_read=True,
                    filesystem_write=False,
                    subprocess_exec=False,
                    network_access=False,
                    execution_authority=False,
                ),
            )
            skills[skill_id] = unit
            tree_hasher.update(f"{skill_id}:{sha}\n".encode())
    else:
        for sfile in discover_skill_files(root):
            unit = parse_skill_unit(
                root,
                mod_id,
                sfile,
                adapter_name="external-evaluator",
                extra_boundary=PermissionBoundary(
                    filesystem_read=True,
                    filesystem_write=False,
                    subprocess_exec=False,
                    network_access=False,
                    execution_authority=False,
                ),
            )
            skills[unit.skill_id] = unit
            tree_hasher.update(f"{unit.skill_id}:{unit.content_sha256}\n".encode())

    if not skills:
        raise ValueError(f"no evaluator workers or skill files found in {root}")

    return ModuleRecord(
        module_id=mod_id,
        source_path=str(root),
        adapter="external-evaluator",
        version=resolved_version,
        git_commit=_git_head_sha(root),
        tree_sha256=tree_hasher.hexdigest(),
        enabled=True,
        license_spdx=license_spdx,
        skills=skills,
    )


def evaluator_routing_to_hyodo_retrieval(
    workspace_root: Path,
    *,
    evaluator_node: str,
    observation: dict[str, Any],
    candidate_rules: list[dict[str, str]],
    ingested_at: str = "2026-11-13T00:00:00Z",
) -> dict[str, Any]:
    """Convert an external evaluator's routing observation into `hyodo.skill-retrieval/v1`.

    Strips any float probabilities/scores and passes only ordinal `score_rank` (>= 1)
    and content-addressed `rule_digest` values to `validate_node_retrieval`.
    """
    if observation.get("execution_authority") is not False:
        raise ValueError("external evaluator observation must declare execution_authority=False")

    job_sha = str(observation.get("job_sha256") or observation.get("query_digest") or "0" * 12)
    query_digest = job_sha[:12] if len(job_sha) >= 12 else (content_digest(job_sha) or "0" * 12)
    selected_skill = str(observation.get("selected_skill_id") or "unknown")

    retrieved_items: list[dict[str, Any]] = []
    for idx, item in enumerate(candidate_rules, start=1):
        rule_text = item["rule_text"]
        source = item.get("source", f"path:.agents/skills/{selected_skill}/SKILL.md")
        skill_name = item.get("skill", selected_skill)
        retrieved_items.append(
            {
                "skill": skill_name,
                "source": source,
                "rule_text": rule_text,
                "rule_digest": content_digest(rule_text) or "",
                "score_rank": idx,
            }
        )

    payload = {
        "schema": NODE_RETRIEVAL_SCHEMA,
        "node": evaluator_node,
        "query_digest": query_digest,
        "retrieved": retrieved_items,
    }
    retrieval, reasons = validate_node_retrieval(payload)
    if retrieval is None or reasons:
        raise ValueError(f"invalid skill retrieval payload: {reasons}")

    rules = node_rules_for(retrieval)
    entry = node_manifest_entry(retrieval, rules, ingested_at=ingested_at)
    manifest, status = load_manifest(workspace_root)
    existing = list(manifest.get("skills", [])) if manifest and status == "ok" else []
    existing = [row for row in existing if row.get("source") != entry["source"]]
    existing.append(entry)
    save_manifest(workspace_root, existing)
    return entry


def record_evaluator_shadow_receipt(
    workspace_root: Path,
    raw_event: dict[str, Any],
) -> dict[str, Any]:
    """Validate, strip full bodies to 12-hex digests, and append an evaluator receipt to `.hyodo/events.jsonl`."""
    meta = raw_event.get("meta")
    tags = meta.get("tags", []) if isinstance(meta, dict) else []
    if "no-execution-authority" not in tags:
        raise ValueError("evaluator shadow event must carry the 'no-execution-authority' tag")

    ok, reasons, normalized = validate_event(raw_event)
    if not ok or normalized is None:
        raise ValueError(f"evaluator event failed HyoDo validation: {reasons}")

    digest_only = strip_full_bodies(normalized)
    if not append_agent_event(workspace_root, digest_only):
        raise OSError("failed to append evaluator shadow event to .hyodo/events.jsonl")
    return digest_only
